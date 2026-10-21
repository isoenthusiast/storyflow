# Operation and recovery

## Start and stop

Run `python3 webapp/server.py` from the source directory. Use `py -3` on Windows.
Keep the process running while using the app; Ctrl+C stops it. No service,
background agent, or boot-time task is installed automatically.

Flags: `--port` (8799), `--db` (state/editorial-desk.sqlite3 beside the source),
`--profile` (editorial-profile.md), and `--public-host` (optional exact proxy
hostname, including port when non-default). `STORYFLOW_PUBLIC_HOST` can supply
the latter. The network bind stays 127.0.0.1.

## Private phone access

Prerequisite: Tailscale installed and signed in on both devices, with access
rules allowing only your intended readers/editors. Use your own device hostname.
Stop a previous local StoryFlow server before running this example:

```sh
python3 webapp/server.py --public-host your-device.your-tailnet.ts.net:8464
```

In another terminal, configure a free port in Tailscale Serve:

```sh
tailscale serve --bg --https=8464 http://127.0.0.1:8799
```

Open `https://your-device.your-tailnet.ts.net:8464/` on the connected phone.
Choose a different port if another service already uses 8464; adjust both
commands. This is Serve, not Funnel. Keep the host awake and the Python process
running. Check `tailscale serve status` when diagnosing access. Disable only
this mapping with `tailscale serve --https=8464 off`.

Official reference: https://tailscale.com/kb/1312/serve

## Backup

The SQLite database contains ideas, revisions, and activity. Use SQLite's backup
API while the app runs; copying just the database file can miss WAL updates.

```sh
python3 tools/backup.py backup --source state/editorial-desk.sqlite3 --output backups/desk-001.sqlite3
```

Every output must be a new filename. The tool refuses overwrites, checks the
schema's core tables and SQLite integrity, and creates a consistent copy. Keep
backups outside the machine as appropriate; no cloud backup is configured.
Back up your custom editorial profile separately. Restrict access to both.

## Restore and verify

Restore into a **new** path, preserving your original files:

```sh
python3 tools/backup.py restore --source backups/desk-001.sqlite3 --output state/recovered.sqlite3
python3 webapp/server.py --port 8800 --db state/recovered.sqlite3
```

Open http://127.0.0.1:8800 and check the latest draft, saved versions, and activity.
After checking, stop both processes before using the restored database as your
normal desk. Do not restore over a database a running server is using.

The browser's Download desk backup link produces JSON for portability and
inspection. v0.1 has no JSON importer. Use the SQLite backup tool when you need
a directly restorable backup. Neither backups nor exports are encrypted.
