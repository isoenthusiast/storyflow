"use strict";
const stages = [
  "idea",
  "research",
  "drafting",
  "review",
  "ready",
  "scheduled",
  "published",
];
const labels = {
  idea: "Ideas",
  research: "Research",
  drafting: "Drafting",
  review: "Review",
  ready: "Ready",
  scheduled: "Scheduled",
  published: "Published",
};
const prompts = {
  idea: "A question, an observation, a little spark.",
  research: "Follow the curiosity. Gather your sources.",
  drafting: "Give the thought some room to grow.",
  review: "Read it with fresh eyes.",
  ready: "A finished draft, ready for the next step.",
  scheduled: "Confirmed with your publisher.",
  published: "Stories you have put into the world.",
};
const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];
let ideas = [],
  current = null,
  dirty = false,
  archived = false,
  view = "board",
  saving = false,
  refreshing = false,
  workflow = [];
const form = $("#editForm");
const esc = (value) =>
  String(value ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const words = (s) => (s.trim().match(/\S+/g) || []).length;
const stamp = (s) =>
  new Date(s).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
function notify(message) {
  $("#toast").textContent = message;
  $("#toast").hidden = false;
  clearTimeout(notify.timer);
  notify.timer = setTimeout(() => ($("#toast").hidden = true), 4000);
}
async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-StoryFlow": "desk",
      ...options.headers,
    },
  });
  const data = await response.json();
  if (!response.ok)
    throw new Error(data.error || "Could not save. Please try again.");
  return data;
}
async function refresh() {
  if (refreshing) return;
  refreshing = true;
  try {
    ideas = await api("/api/ideas");
    $("#loadError").hidden = true;
    render();
    $(".connection").textContent =
      "● Synced " +
      new Date().toLocaleTimeString(undefined, {
        hour: "2-digit",
        minute: "2-digit",
      });
    const latest = current && ideas.find((x) => x.id === current.id);
    if (latest && latest.version > current.version && !saving) {
      if (dirty) {
        $("#saveState").textContent =
          "A newer version was saved in chat or another tab. Your edits are kept here; copy them before reopening.";
      } else {
        current = latest;
        fillEditor(latest);
        loadActivity(latest.id);
      }
    }
  } catch (e) {
    $(".connection").textContent = "● Connection interrupted";
    $("#loadError").textContent =
      "Could not sync the desk. Your unsaved edits are kept. " + e.message;
    $("#loadError").hidden = false;
  } finally {
    refreshing = false;
  }
}
function card(item) {
  return `<button class="card" data-id="${item.id}"><span class="tag">${esc(item.format)}</span><h3>${esc(item.title)}</h3><p>${esc((item.conversation || item.angle || item.notes || "Open this idea to find the angle.").slice(0, 130))}</p>${item.next_action ? `<p class="next-action"><strong>Next</strong> ${esc(item.next_action.slice(0, 140))}</p>` : ""}<div class="card-foot"><span>${view === "list" ? esc(labels[item.stage]) : words(item.draft) + " words"}</span><span>${item.target_date ? "Target " + esc(item.target_date) : "Updated " + esc(new Date(item.updated_at).toLocaleDateString(undefined, { day: "numeric", month: "short" }))}</span></div></button>`;
}
function render() {
  const query = $("#search").value.toLowerCase();
  const stage = $("#stageFilter").value;
  const filtered = ideas.filter(
    (x) =>
      x.archived === archived &&
      (!stage || x.stage === stage) &&
      [
        x.title,
        x.angle,
        x.draft,
        x.notes,
        x.sources,
        x.audience,
        x.conversation,
        x.decisions,
        x.questions,
        x.next_action,
      ]
        .join(" ")
        .toLowerCase()
        .includes(query),
  );
  $("#total").textContent = ideas.filter((x) => !x.archived).length;
  $("#summary").textContent =
    `${filtered.length} ${filtered.length === 1 ? "story" : "stories"} · ${filtered.reduce((n, x) => n + words(x.draft), 0).toLocaleString()} words`;
  $("#viewTitle").textContent = archived
    ? "Ideas on the shelf"
    : "Your writing pipeline";
  $("#board").classList.toggle("list-mode", view === "list");
  if (!filtered.length && (archived || query || stage || view === "list")) {
    $("#board").innerHTML =
      '<div class="empty-board"><h3>' +
      (query || stage
        ? "No matching ideas"
        : archived
          ? "Room for a second thought"
          : "Your next story starts with a thought") +
      "</h3><p>" +
      (query || stage
        ? "Try another phrase or stage."
        : archived
          ? "Archived ideas stay here, ready whenever you are."
          : "Use the capture bar above. A working title is enough.") +
      "</p></div>";
    return;
  }
  $("#board").innerHTML =
    view === "list"
      ? filtered.map(card).join("")
      : (stage ? [stage] : stages)
          .map(
            (s) =>
              `<section class="column"><div class="column-head"><span class="dot"></span>${labels[s]}<span>${filtered.filter((x) => x.stage === s).length}</span></div>${
                filtered
                  .filter((x) => x.stage === s)
                  .map(card)
                  .join("") || `<div class="empty-column">${prompts[s]}</div>`
              }${s === "idea" && !archived ? '<button class="add-column" data-add="true">＋ Capture a thought</button>' : ""}</section>`,
          )
          .join("");
}
function tab(name) {
  $$("[data-panel]").forEach((x) => (x.hidden = x.dataset.panel !== name));
  $$("[data-tab]").forEach((x) => {
    x.setAttribute("aria-selected", x.dataset.tab === name);
    x.tabIndex = x.dataset.tab === name ? 0 : -1;
  });
}
function handoffState() {
  const link = $("#handoff");
  link.href = current ? `/api/ideas/${current.id}/handoff` : "#";
  link.setAttribute("aria-disabled", !current || dirty ? "true" : "false");
}
function fillEditor(item) {
  for (const [key, value] of Object.entries(item)) {
    if (form.elements.namedItem(key))
      form.elements.namedItem(key).value = value;
  }
  $$(".checks input").forEach(
    (x) => (x.checked = item.checks.includes(x.value)),
  );
  $("#archiveButton").textContent = item.archived
    ? "Restore idea"
    : "Archive idea";
  $("#saveState").textContent = "Saved · " + stamp(item.updated_at);
  $("#wordCount").textContent = words(item.draft) + " words";
  handoffState();
  stageGuide();
}
function openEditor(item) {
  current = item;
  dirty = false;
  form.reset();
  fillEditor(item);
  $("#history").replaceChildren();
  tab("conversation");
  loadActivity(item.id);
  $("#editor").showModal();
  $("#title").focus();
}
function stageGuide() {
  const step = workflow.find((x) => x.stage === $("#stage").value);
  $("#stageGuide").textContent = step ? "Next transition: " + step.move : "";
}
async function loadActivity(id) {
  try {
    const events = await api("/api/ideas/" + id + "/activity");
    if (!current || current.id !== id) return;
    $("#activity").innerHTML = events.length
      ? events
          .map(
            (e) =>
              `<article class="activity-entry"><div><strong>${e.source === "chat" ? "From our chat" : "Desk update"}</strong><small>${esc(stamp(e.at))}</small></div><p>${esc(e.note)}</p>${e.from_stage !== e.to_stage ? `<span class="stage-change">${esc(e.from_stage ? labels[e.from_stage] : "New idea")} → ${esc(labels[e.to_stage])}</span>` : ""}</article>`,
          )
          .join("")
      : '<p class="hint">New updates will appear here. Older versions remain in saved history.</p>';
  } catch (e) {
    if (current && current.id === id)
      $("#activity").textContent =
        "Could not load activity. Reopen this idea to retry.";
  }
}

function closeEditor() {
  if (saving) return;
  if (dirty && !confirm("Discard your unsaved changes?")) return;
  $("#editor").close();
  current = null;
  dirty = false;
}
function payload() {
  return {
    ...Object.fromEntries(new FormData(form)),
    checks: $$(".checks input:checked").map((x) => x.value),
    archived: current.archived,
    version: current.version,
    update_source: "desk",
  };
}
async function save(event) {
  event.preventDefault();
  if (saving || !form.reportValidity()) return;
  saving = true;
  form.inert = true;
  $("#saveButton").disabled = true;
  $("#saveState").textContent = "Saving…";
  try {
    current = await api("/api/ideas/" + current.id, {
      method: "PUT",
      body: JSON.stringify(payload()),
    });
    dirty = false;
    $("#saveState").textContent = "Saved · " + stamp(current.updated_at);
    handoffState();
    stageGuide();
    loadActivity(current.id);
    await refresh();
    notify("Your story is saved.");
  } catch (e) {
    $("#saveState").textContent = e.message;
    notify(e.message);
  } finally {
    saving = false;
    form.inert = false;
    $("#saveButton").disabled = false;
  }
}
$("#capture").addEventListener("submit", async (event) => {
  event.preventDefault();
  const input = $("#quickTitle");
  const button = $("#capture button");
  button.disabled = true;
  try {
    const item = await api("/api/ideas", {
      method: "POST",
      body: JSON.stringify({ title: input.value, stage: "idea" }),
    });
    input.value = "";
    archived = false;
    $("#activeView").classList.add("active");
    $("#archiveView").classList.remove("active");
    await refresh();
    openEditor(item);
    notify("Idea captured.");
  } catch (e) {
    notify(e.message);
  } finally {
    button.disabled = false;
  }
});
$("#board").addEventListener("click", (event) => {
  const item = event.target.closest("[data-id]");
  if (item) openEditor(ideas.find((x) => x.id === item.dataset.id));
  if (event.target.closest("[data-add]")) $("#quickTitle").focus();
});
form.addEventListener("input", () => {
  dirty = true;
  $("#saveState").textContent = "Unsaved changes";
  $("#wordCount").textContent = words($("#draft").value) + " words";
  handoffState();
});
form.addEventListener("submit", save);
$("#closeEditor").onclick = closeEditor;
$("#editor").addEventListener("cancel", (event) => {
  event.preventDefault();
  closeEditor();
});
window.addEventListener("beforeunload", (event) => {
  if (dirty) {
    event.preventDefault();
    event.returnValue = "";
  }
});
$$("[data-tab]").forEach((button) => {
  button.onclick = () => tab(button.dataset.tab);
  button.onkeydown = (event) => {
    if (!["ArrowRight", "ArrowLeft"].includes(event.key)) return;
    event.preventDefault();
    const tabs = $$("[data-tab]");
    const next =
      tabs[
        (tabs.indexOf(button) +
          (event.key === "ArrowRight" ? 1 : tabs.length - 1)) %
          tabs.length
      ];
    tab(next.dataset.tab);
    next.focus();
  };
});
$("#archiveButton").onclick = async () => {
  if (saving) return;
  if (dirty) {
    notify("Save your changes before archiving or restoring.");
    return;
  }
  try {
    current = await api("/api/ideas/" + current.id, {
      method: "PUT",
      body: JSON.stringify({
        ...current,
        archived: !current.archived,
        update_source: "desk",
        activity_note: current.archived ? "Idea restored" : "Idea archived",
      }),
    });
    $("#editor").close();
    await refresh();
    notify(
      current.archived
        ? "Idea archived. You can restore it anytime."
        : "Idea restored.",
    );
    current = null;
  } catch (e) {
    notify(e.message);
  }
};
$("#historyButton").onclick = async () => {
  try {
    const history = await api("/api/ideas/" + current.id + "/history");
    $("#history").innerHTML = history.length
      ? history
          .map(
            (x) =>
              `<details class="history-entry"><summary>Version ${x.version} · ${esc(stamp(x.updated_at))}</summary><pre>${esc([x.title, "Stage: " + x.stage, "Angle: " + x.angle, "Reader: " + x.audience, "Experience: " + x.experience, "Sources: " + x.sources, "Notes: " + x.notes, "Conversation: " + (x.conversation || ""), "Decisions: " + (x.decisions || ""), "Questions: " + (x.questions || ""), "Next: " + (x.next_action || ""), "Draft:", x.draft].join("\n\n"))}</pre></details>`,
          )
          .join("")
      : '<p class="hint">Previous versions appear after your first edit.</p>';
  } catch (e) {
    notify(e.message);
  }
};
$("#activeView").onclick = () => {
  archived = false;
  $("#activeView").classList.add("active");
  $("#archiveView").classList.remove("active");
  render();
};
$("#archiveView").onclick = () => {
  archived = true;
  $("#archiveView").classList.add("active");
  $("#activeView").classList.remove("active");
  render();
};
$("#search").oninput = render;
$("#stageFilter").onchange = render;
for (const v of ["board", "list"])
  $("#" + v + "View").onclick = () => {
    view = v;
    for (const w of ["board", "list"]) {
      $("#" + w + "View").classList.toggle("selected", w === v);
      $("#" + w + "View").setAttribute("aria-pressed", w === v);
    }
    render();
  };
$("#profileButton").onclick = async () => {
  try {
    const profile = await api("/api/profile");
    $("#profileText").textContent = profile.text;
    $("#profileDialog").showModal();
  } catch (e) {
    notify(e.message);
  }
};
$("#closeProfile").onclick = () => $("#profileDialog").close();
for (const s of stages) {
  $("#stage").add(new Option(labels[s], s));
  $("#stageFilter").add(new Option(labels[s], s));
}
$("#today").textContent = new Date()
  .toLocaleDateString(undefined, {
    day: "numeric",
    month: "long",
    year: "numeric",
  })
  .toUpperCase();
refresh();

$("#stage").addEventListener("change", stageGuide);
$("#workflowButton").onclick = async () => {
  try {
    workflow = await api("/api/workflow");
    $("#workflowSteps").innerHTML = workflow
      .map(
        (s, i) =>
          `<section class="workflow-step"><span class="step-number">${i + 1}</span><div><h3>${esc(s.label)}</h3><p>${esc(s.conversation)}</p><p><strong>Saved here:</strong> ${esc(s.record)}</p><p class="hint"><strong>Moves forward:</strong> ${esc(s.move)}</p></div></section>`,
      )
      .join("");
    $("#workflowDialog").showModal();
  } catch (e) {
    notify(e.message);
  }
};
$("#closeWorkflow").onclick = () => $("#workflowDialog").close();
api("/api/workflow")
  .then((data) => {
    workflow = data;
    if (current) stageGuide();
  })
  .catch(() => {});
setInterval(() => {
  if (!document.hidden && !saving) refresh();
}, 5000);
document.addEventListener("visibilitychange", () => {
  if (!document.hidden && !saving) refresh();
});
