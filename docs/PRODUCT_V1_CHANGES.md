# Porchlight product evolution

## v1 — product surfaces

Replaced the hackathon/demo console with separate coordinator, volunteer, and administrator experiences. Removed demo triggers, reset/reconcile controls, “Strands live” labels, and raw tool names from normal operations.

## v1.1 — coordinator operations

- Multi-route operations dashboard and coordinator volunteer roster.
- Formal route workspace with timing, progress, communications, stop outcomes, reminders, backup coordination, and manual override.
- Needs Attention context for late/unstarted routes.
- Human-readable Recently handled by Porchlight timeline.
- Forward-compatible persisted state migration.

## v1.2 — product hardening

- Formal route lifecycle separated from attention overlays.
- Human-review drawer: factual volunteer note + exact approved protocol before acknowledgement.
- Volunteer field flow adds navigation deep links, coordinator contact, step-by-step protocol completion, required factual exception notes, and stronger welfare-boundary language.
- Installable PWA shell with last-synced route cache; offline writes are blocked rather than silently queued.
- Editable administrator settings for volunteer eligibility/availability, organization contact, and exception protocols.
- Additional policy-backed outcomes: recipient declined, meal issue, and generic delivery problem.
- Automatic route reconciliation when every stop is accounted for and no required human review remains.
- Unique Needs Attention metric avoids double-counting a route and its open issue.
- Expanded tests for lifecycle overlays and protocol-driven exceptions.
