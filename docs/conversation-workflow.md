# From a conversation to a story

You supply the ideas, experience, and editorial decisions. Your assistant helps
develop the writing. StoryFlow keeps a record that you can return to later.

| Stage | What you do | What the record keeps |
| --- | --- | --- |
| Idea | Share an observation or question | Working title, possible angle, uncertainties |
| Research | Explore the reader and check claims | Sources, evidence, agreed direction |
| Drafting | Turn the material into a complete draft | Article text and unresolved issues |
| Review | React to the draft and refine it | Feedback, revised text, checks |
| Ready | Decide when and where to share it | Reviewed draft, publication next action |
| Scheduled | Confirm a schedule in your publishing service | Actual link, date, time, timezone |
| Published | Verify the live article | Public link, outcome, optional audio status |

You can revisit earlier steps. A personal reflection may skip research; a post
published immediately skips scheduling. A published post stays Published while
later edits are tracked as revision work.

## Connect an agent

Use an agent with tools that can reach this computer and make local HTTP
requests. Give it this repository's AGENTS.md and the API reference. A phone
browser opening the desk does not give a separate chat access to the computer.
Do not put credentials in chat records or expose the desk to work around this.

Example instruction:

> Use StoryFlow at http://127.0.0.1:8799 as the record for our writing. Before
> editing an idea, read its current version. Save our summary, decisions, open
> questions, next action, and draft as we work. Preserve my sources and previous
> work. Read back changes. Do not publish anything without my instruction.

For each meaningful exchange, the agent:

1. Reads `/api/ideas` and matches the existing idea by ID and context.
2. Performs the authorized research or writing, keeping uncertainties explicit.
3. Updates only affected fields using the latest `version`, `update_source:
   "chat"`, and a short `activity_note`.
4. On a conflict, rereads and reconciles. On success, reads back the saved record.
5. Explains the outcome and next action. The board shows the saved changes.

Source labels in the activity timeline are self-reported, not identity proof.
No polling of chats, unattended agent, or automatic publishing is installed.

## Without a connected agent

Use the same fields manually. Download a Markdown handoff to provide context
to a writing assistant. Review its suggestions before saving them. This path
works without any direct connection between the chat and your desk.
