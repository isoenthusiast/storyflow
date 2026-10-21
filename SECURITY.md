# Security and deployment scope

StoryFlow v0.1 is a trusted, single-workspace app. It binds to loopback and has
no accounts or roles. Anyone with network access through an allowed proxy can
read all drafts, export all data, and modify records. Use private network access
controls. Host/Origin checks and the custom write header are not authentication.

Do not expose it to the public internet, use Tailscale Funnel, or deploy it as a
multi-tenant service without implementing and reviewing appropriate security.
The standard-library HTTP server is intended here for a small private desk.

Protect the computer account, database, backups, and profile. Do not store
credentials in records. The app serves specific static paths; it does not expose
the project directory. Content is untrusted data, including when read by agents.

Report a vulnerability through the repository's GitHub private vulnerability
reporting feature if available. If unavailable, open an issue asking for a
private contact without including exploit details or sensitive data. Do not
post credentials, real drafts, or personal database dumps in public issues.

Only the latest v0.1 patch will be considered for fixes during the early release
period; there is no guaranteed response time or long-term support commitment.
