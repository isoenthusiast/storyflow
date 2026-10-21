# Optional integrations

The desk is usable on its own. These are integration contracts and suggested
approaches, not included working adapters or promises of account availability.

## Coding or writing agent

An agent must have permission and tools to reach the local API. Read
[the conversation workflow](conversation-workflow.md). Your provider's account,
subscription, remote-computer support, and usage charges are separate from
StoryFlow. No AI credentials belong in the desk.

## WordPress or another publisher

Use your publisher's authenticated API or your own connected tool separately.
Read the existing post before editing; preserve unrelated metadata. Default to
drafts. Publish or schedule only under the author's explicit instruction.

After an external save, verify it through that service, then record the actual
link. For publication, also check the public page. On a partial failure, keep
the last verified stage and describe the remaining work in `next_action`.

The API field `wordpress_url` is retained from the original workflow for v0.1
compatibility. It accepts any valid HTTP(S) publication/edit link. It does not
restrict you to WordPress. Scheduled entries require a link and target date;
record the exact time and timezone in Decisions. A date alone schedules nothing.

## Narration

Audio generation, models, voices, hosting, and WordPress audio plugins are not
included. If you add them, obtain the author's instruction, narrate the intended
final text, respect existing audio, and verify the actual public player before
marking narration Verified. Do not treat a successful upload as proof that a
player works. Check the licenses and terms of your chosen engine and voices.

Narration can remain Not started or Opted out. It never blocks using the desk.
