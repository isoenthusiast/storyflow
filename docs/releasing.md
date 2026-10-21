# Preparing v0.1.0

Release only from reviewed, committed source. The original personal workspace
must remain private; never copy its database, history, profile, or attachments.

1. Run Python tests, JS syntax validation, browser smoke test, and `git diff --check`.
2. Confirm CI is green on Linux, macOS, and Windows.
3. Start a clean source checkout using only the README. Load the demo; create,
   edit, reload, archive, and restore an idea. Verify backup recovery separately.
4. Review every tracked file and the complete new Git history for personal data
   and secrets. Confirm no production settings, media, or runtime data are tracked.
5. Check README links, MIT license, VERSION, and release notes. Have another
   author try the quickstart when possible; record whether this has been done.
6. Update CHANGELOG from release candidate to the release date. Tag `v0.1.0`
   only after review and explicit release approval. Create a GitHub release
   from that tag, describing limitations and linking the quickstart.

GitHub's source ZIP/tarball are sufficient for v0.1; no compiled installer,
container registry, paid service, or production deployment is required.
