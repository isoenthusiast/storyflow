# Local API

Base URL: `http://127.0.0.1:8799`. Writes use `Content-Type: application/json`
and `X-StoryFlow: desk`. The header guards against unwanted cross-origin writes;
it is **not authentication**. Host and Origin checks are additional protections.

| Request | Result |
| --- | --- |
| GET /api/ideas | All records including archived ones |
| POST /api/ideas | Create a record; `title` required |
| PUT /api/ideas/ID | Update specified fields; current `version` required |
| GET /api/ideas/ID/history | Prior versions, newest first |
| GET /api/ideas/ID/activity | Saved events, newest first |
| GET /api/ideas/ID/handoff | Markdown brief and draft |
| GET /api/export | JSON export of ideas, revisions, activity |
| GET /api/profile | Configured editorial profile as text |
| GET /api/workflow | Stage descriptions and transition guidance |

```sh
curl http://127.0.0.1:8799/api/ideas \
  -H 'Content-Type: application/json' -H 'X-StoryFlow: desk' \
  -d '{"title":"An idea to explore","conversation":"We are choosing an angle.","update_source":"chat","activity_note":"Captured the idea."}'
```

Use the returned `id` and `version` for the next update:

```json
{
  "version": 1,
  "stage": "research",
  "decisions": "Write for beginners.",
  "questions": "Which example is clearest?",
  "next_action": "Check the main claim.",
  "update_source": "chat",
  "activity_note": "Agreed on the reader; beginning research."
}
```

Fields: `title`, `stage`, `angle`, `audience`, `experience`, `sources`, `draft`,
`notes`, `format`, `target_date` (YYYY-MM-DD), `wordpress_url`, `narration`,
`checks`, `archived`, `conversation`, `decisions`, `questions`, `next_action`,
`chat_reference`. Text is stored as text, not rendered HTML.

`checks` is a list of `voice`, `facts`, `structure`, `disclosure`; `archived`
is boolean. Omitted fields retain their previous value. Titles are 1–250
characters. The body limit is 2 MB. `update_source` accepts `desk` or `chat`;
`activity_note` is at most 4,000 characters. Neither is trusted identity data.

HTTP 400 means invalid input; 403 means host/origin/header rejection; 404 means
missing record/route; 409 means stale version. Re-read and reconcile a conflict.
Revisions, events, and the updated idea commit in one transaction.

`wordpress_url` accepts any HTTP(S) publisher link. Stage changes only record
what the caller says happened. Validate real-world publication separately.
JSON export is not an import format supported by the app; see the SQLite
backup/restore tool for full recovery.
