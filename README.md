# Porchlight v1.3

**Helping make sure no neighbor is missed.**

Porchlight is a human-first operations platform for community meal-delivery programs. Volunteers get a simple field experience; coordinators see only the situations that need judgment; Porchlight handles routine coordination behind the scenes with bounded Strands workflows and organization-defined policy.

This release focuses on the parts that make the product more convincing **without adding external integrations**: richer operational context, better route visualization, deterministic QA/demo scenarios, editable protocol previews, and an evidence-first agent evaluation surface.

## What changed in v1.3

- **Richer Needs Attention:** timing, last-contact context, escalation owner, route impact, and recommended next action.
- **Route sequence visualization:** a local schematic makes stop order and outcome state obvious without requiring a maps API.
- **Recently handled stories:** coordinator-facing cards summarize what Porchlight resolved instead of exposing raw tool activity.
- **Scenario Lab:** deterministic starting states for backup retry, all-backups-decline, no-answer handoff, and a normal sample day.
- **Agent Evaluation:** workflow runs, tool evidence, duration, verified postconditions, human handoffs, decline recovery, and code-enforced guardrails.
- **Protocol editor 2.0:** edit title, severity, escalation owner, volunteer note prompt, acknowledgement policy, step order, deletion, and live volunteer preview.
- **Cleaner demo data:** realistic seeded timeline events and intentional state transitions.
- **No extra integrations required:** communications remain behind the deterministic adapter and maps remain optional deep links.

## Product surfaces

### Coordinator — `/coordinator`
- Today-at-a-glance route health and delivery progress.
- Formal route lifecycle (`Scheduled → Confirmed → In Progress → Complete`) with separate attention overlays (`At Risk`, `Uncovered`, `Needs Review`).
- **Needs Attention** queue with severity, age, timing, escalation owner, route impact, and next action.
- Human-readable **Recently handled by Porchlight** stories.
- Full route workspace: assigned volunteer, timing, stop outcomes, local route schematic, communications, manual override, reminder, backup coordination, and next-stop navigation.
- Recipient exception review drawer showing the volunteer’s factual note and the exact approved protocol before acknowledgement.
- Dedicated coordinator volunteer roster at `/volunteers`.

### Volunteer — `/volunteer`
- Mobile-first route home and one-stop-at-a-time delivery flow.
- Route start, progress, current/next stop, estimated finish, and compact route sequence.
- Recipient care card with address, delivery notes, meal/diet information, accessibility notes, and optional conversation starter.
- One-tap external navigation link for each stop.
- Structured outcomes: Delivered, No Answer, Recipient Declined, Could Not Access, Meal Issue, Welfare Concern, Other.
- Step-by-step human-approved protocol checklist before exception submission.
- Protocol-specific factual-note prompts plus a clear **What happens next** explanation.
- Coordinator call action for sensitive exceptions.
- PWA shell + last-synced route cache so route instructions remain viewable when connectivity drops. Writes are deliberately blocked offline rather than silently queued.

### Administration — `/admin`
- Strands/model diagnostics kept out of everyday operations.
- **Agent Evaluation** with workflow history, tool evidence and postcondition verification.
- **Scenario Lab** for deterministic product/agent demonstrations.
- Editable organization contact/emergency guidance.
- Integration status cards.
- Volunteer availability, activation, approved route eligibility, and backup priority editing.
- Full exception-protocol editor with live preview and step reordering/deletion.
- Separate audit trail for operational, human, admin, and agent actions.

## Agent behavior

Porchlight uses **Strands Agents** for bounded operational workflows:

1. **Coverage recovery** — find approved backups, contact in policy order, continue after declines, assign only after verified acceptance, escalate when no approved backup accepts.
2. **No-answer handling** — only after the volunteer completes the configured protocol, record the factual outcome and create the policy-defined human review item.
3. **Reconciliation** — verify every scheduled stop is accounted for and required human review is cleared.

The key boundary remains:

> **Strands chooses and sequences permitted actions. Program tools and human-approved policy authorize them.**

The model cannot invent a volunteer acceptance, delivery result, acknowledgement, emergency response, or medical/welfare conclusion.

## Agent evaluation and guardrails

Porchlight stores operational evidence, not hidden model reasoning. Each live bounded workflow can record:

- workflow name and route;
- model/provider;
- start/end time and duration;
- tool calls and their outcomes;
- final workflow status;
- application-level postcondition and whether it was verified.

The administrator view also surfaces four code-enforced controls:

- backup assignment requires verified acceptance;
- welfare/no-answer decisions remain human-owned;
- open issues or unaccounted stops block clean route closure;
- safety-sensitive outcomes require factual evidence rather than diagnosis.

## Scenario Lab

The admin Scenario Lab resets local sample data into one of four deterministic starting states:

- **Sample delivery day** — general product walkthrough.
- **Backup retry** — first approved East End backup declines; the second accepts.
- **Coverage gap** — every approved East End backup declines, requiring a human handoff.
- **No-answer handoff** — George Town is already in progress and Mary is the next pending stop.

The scenario loader never pretends an agent action occurred. It only prepares the starting state; users continue through the normal coordinator/volunteer product flows.

## Automatic reconciliation

There is no user-facing “reconcile route” control. After outcomes and acknowledgements, Porchlight recomputes the route automatically. A route becomes complete only when every stop has an explicit outcome and no required review remains open.

## Persistence

Operational state is persisted to SQLite at `data/porchlight.db`. Routes, stops, volunteers, communications, outcomes, issues, protocol configuration, agent runs, timeline events, and audit history survive server restarts.

## Run locally

Python 3.12 recommended:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
uvicorn backend.main:app --reload
```

Open:

- Coordinator: `http://127.0.0.1:8000/coordinator`
- Volunteer roster: `http://127.0.0.1:8000/volunteers`
- Volunteer: `http://127.0.0.1:8000/volunteer`
- Administration / Evaluation / Scenario Lab: `http://127.0.0.1:8000/admin`

## Enable real Strands orchestration

Gemini is the currently tested model provider:

```bash
export GEMINI_API_KEY='...'
export PORCHLIGHT_USE_STRANDS=1
export PORCHLIGHT_MODEL_PROVIDER=gemini
export PORCHLIGHT_MODEL_ID=gemini-3.6-flash
uvicorn backend.main:app --reload
```

Do not commit API keys. A Bedrock provider path remains available for AWS accounts with model access.

Direct agent smoke test:

```bash
PORCHLIGHT_USE_STRANDS=1 \
PORCHLIGHT_MODEL_PROVIDER=gemini \
PORCHLIGHT_MODEL_ID=gemini-3.6-flash \
python scripts/strands_smoke.py
```

## Tests

```bash
python -m pytest -q
```

Current suite: **13 tests** covering verified assignment, decline/retry, all-decline coverage gaps, protocol gates, human review, lifecycle/attention separation, route reconciliation, demo-scenario setup, and agent telemetry/postcondition evidence.

## Current integration boundaries

Deliberately *not* expanded in this release:

- outbound messaging still uses the deterministic communications adapter;
- route navigation uses external deep links rather than a routing API;
- authentication/role enforcement is not a hackathon priority;
- data remains a versionable SQLite state document rather than a production encrypted relational schema;
- scheduled background jobs are still future work.

Those are integration/deployment concerns. v1.3 concentrates on making the product behavior, safety boundary, demoability and agent evidence stronger first.

## Project structure

```text
porchlight/
├── backend/
│   ├── agent.py
│   ├── config.py
│   ├── main.py
│   ├── store.py
│   └── tools.py
├── frontend/
│   ├── coordinator.html / coordinator.js
│   ├── volunteer.html / volunteer.js
│   ├── volunteers.html / volunteers.js
│   ├── admin.html / admin.js
│   ├── shared.js
│   ├── manifest.webmanifest
│   ├── service-worker.js
│   └── styles.css
├── docs/
├── tests/
└── scripts/
```

## Design origin

The original community meal-delivery concept and Stitch UX explorations predate the agent implementation. Porchlight preserves the warmth, mobile focus, and person-at-the-door philosophy of those screens while treating AI as background operations infrastructure rather than the interface itself.

## License

MIT — see `LICENSE`.
