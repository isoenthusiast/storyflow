# Contributing

Start with an issue describing the author-facing problem and a small proposed
change. Useful contributions include clearer onboarding, accessibility fixes,
portable tests, and optional integration examples. There is no support SLA.

Use Python 3.11+ and an isolated test database. Runtime code uses only Python's
standard library. Never commit real drafts, exports, account settings, or keys.

```sh
python3 -m unittest discover -s tests -v
node --check webapp/app.js
git diff --check
```

For the browser smoke test (development only):

```sh
npm ci
npx playwright install chromium
npm run test:browser
npm run format:check
```

On Linux, Playwright may also need system browser libraries; CI installs them
with `npx playwright install --with-deps chromium`. The test starts and stops
its own server and uses a temporary database. It never connects to a live desk.

In a pull request, describe the problem, resulting behavior, verification, and
any data migration impact. Include meaningful regression coverage for data
handling changes. Contributions are provided under the project's MIT license.
