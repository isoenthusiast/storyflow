import assert from "node:assert/strict";
import { spawn, spawnSync } from "node:child_process";
import { once } from "node:events";
import { mkdtemp, rm, mkdir } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const root = fileURLToPath(new URL("../", import.meta.url));
const directory = await mkdtemp(join(tmpdir(), "storyflow-browser-"));
const python =
  process.env.PYTHON || (process.platform === "win32" ? "python" : "python3");
const database = join(directory, "demo.sqlite3");
const seed = spawnSync(python, ["tools/demo.py", "--db", database], {
  cwd: root,
  encoding: "utf8",
});
assert.equal(seed.status, 0, seed.stderr);
const server = spawn(
  python,
  ["webapp/server.py", "--port", "0", "--db", database],
  { cwd: root },
);
let browser;
try {
  const url = await new Promise((accept, reject) => {
    let output = "";
    const timeout = setTimeout(
      () => reject(new Error("Server startup timeout")),
      15000,
    );
    server.stdout.on("data", (chunk) => {
      output += chunk;
      const match = output.match(/http:\/\/127\.0\.0\.1:\d+/);
      if (match) {
        clearTimeout(timeout);
        accept(match[0]);
      }
    });
    server.once("error", (error) => {
      clearTimeout(timeout);
      reject(error);
    });
    server.once("exit", (code) => {
      clearTimeout(timeout);
      reject(new Error(`Server exited: ${code}`));
    });
  });
  browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({
    viewport: { width: 1440, height: 1000 },
  });
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto(url);
  await page.locator(".card").first().waitFor();
  await page.locator("#quickTitle").fill("Example: Make space for curiosity");
  await page.locator("#capture button").click();
  await page.locator("#editor[open]").waitFor();
  await page.locator('[data-tab="draft"]').click();
  await page
    .locator("#draft")
    .fill("A fictional draft for browser verification.");
  await page.locator("#stage").selectOption("review");
  const save = page.waitForResponse(
    (r) => r.request().method() === "PUT" && r.url().includes("/api/ideas/"),
  );
  await page.locator("#saveButton").click();
  assert.equal((await save).status(), 200);
  await page.waitForFunction(() => !document.querySelector("#editForm").inert);
  await page.locator("#closeEditor").click();
  await page.reload();
  await page
    .getByRole("button", { name: /Example: Make space for curiosity/ })
    .click();
  assert.equal(
    await page.locator("#draft").inputValue(),
    "A fictional draft for browser verification.",
  );
  await page.locator('[data-tab="review"]').click();
  await page.locator("#historyButton").click();
  await page.locator(".history-entry").first().waitFor();
  const download = page.waitForEvent("download");
  await page.locator("#handoff").click();
  assert.match((await download).suggestedFilename(), /^storyflow-.*\.md$/);
  await page.locator("#archiveButton").click();
  await page.locator("#editor").waitFor({ state: "hidden" });
  await page.locator("#archiveView").click();
  await page
    .getByRole("button", { name: /Example: Make space for curiosity/ })
    .click();
  await page.locator("#archiveButton").click();
  await page.locator("#editor").waitFor({ state: "hidden" });
  await page.locator("#activeView").click();
  await page
    .getByRole("button", { name: /Example: Make space for curiosity/ })
    .waitFor();
  // A second API client acts as a connected agent; the board must refresh it.
  const response = await fetch(`${url}/api/ideas`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-StoryFlow": "desk" },
    body: JSON.stringify({
      title: "Example: A question worth exploring",
      update_source: "chat",
      conversation: "A hypothetical writing conversation.",
      next_action: "Choose a reader.",
    }),
  });
  assert.equal(response.status, 201);
  await page
    .getByRole("button", { name: /Example: A question worth exploring/ })
    .waitFor({ timeout: 10000 });
  const screenshots = resolve(
    process.env.SCREENSHOT_DIR || join(root, "runs", "browser"),
  );
  await mkdir(screenshots, { recursive: true });
  await page.screenshot({
    path: join(screenshots, "desktop.png"),
    fullPage: true,
  });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.locator("#listView").click();
  assert.equal(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
    true,
  );
  await page
    .getByRole("button", { name: /Example: A question worth exploring/ })
    .click();
  await page.locator("#editor[open]").waitFor();
  await page.screenshot({
    path: join(screenshots, "mobile.png"),
    fullPage: true,
  });
  assert.deepEqual(errors, []);
  console.log(
    "Browser smoke passed: create, save, reload, history, handoff, archive/restore, agent refresh, mobile.",
  );
} finally {
  if (browser) await browser.close();
  if (server.exitCode === null) {
    server.kill();
    await once(server, "exit");
  }
  await rm(directory, { recursive: true, force: true });
}
