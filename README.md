# Porchlight

**Helping make sure no neighbor is missed.**

Porchlight is an agent-powered operations companion for community meal-delivery programs. It keeps volunteer delivery work simple, handles routine coordination behind the scenes, and surfaces only the situations that need a human decision.

This repository is the **v1 product-shaped build** evolved from the original hackathon proof of concept. The Strands workflows remain real; the interface is now organized around actual coordinator, volunteer, and administrator jobs rather than demo controls.

## Product surfaces

### Coordinator — `/coordinator`
- Today-at-a-glance route health rather than an AI console.
- **Needs Attention** queue containing only human-required items.
- Live route progress, volunteer assignment, estimated finish, and exception counts.
- Route detail drawer with stops and volunteer communication status.
- Human-readable **Recently handled by Porchlight** timeline.
- Coverage recovery can be initiated from a real operational action (`Volunteer unavailable`), not a “simulate” button.

### Volunteer — `/volunteer`
- Mobile-first route home with shift lifecycle and progress.
- One stop at a time, with delivery/access notes, meal details, accessibility information, and optional conversation starter.
- Structured outcomes: Delivered, No Answer, Recipient Declined, Could Not Access, Meal Issue, Welfare Concern, Other.
- Protocol steps shown only when the organization has configured one.
- Factual-note language intentionally avoids diagnosis or inference.
- Route reconciliation happens in the background as outcomes and coordinator acknowledgements arrive.

### Administration — `/admin`
- Volunteer availability, eligibility, contact status, and reliability.
- Organization-defined exception protocols.
- Separate technical/audit trail, including Strands diagnostics, kept out of everyday coordinator UX.

## Agent behavior

Porchlight uses **Strands Agents** for bounded operational workflows:

1. **Route coverage recovery** — find approved backups, contact in policy order, assign only after verified acceptance, escalate if no approved candidate accepts.
2. **No-answer handling** — after a volunteer completes the configured human protocol, record the outcome and create the policy-defined coordinator issue.
3. **Reconciliation** — ensure every scheduled stop has an explicit outcome and required human issues are cleared before the route is considered complete.

The key boundary is:

> **Strands chooses and sequences permitted actions. Program tools and human-approved policy authorize them.**

The model cannot invent a volunteer acceptance, delivery result, acknowledgement, or medical/welfare conclusion.

## Persistence

Operational state is persisted to SQLite at `data/porchlight.db` so routes, outcomes, communications, issues, and audit history survive browser refreshes and server restarts.

For this iteration, the database stores the application state as a versionable JSON document inside SQLite. A production deployment can normalize these entities without changing the UI/API contracts.

## Run locally

Python 3.10+ (3.12 recommended):

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
uvicorn backend.main:app --reload
```

Then open:

- Coordinator: `http://127.0.0.1:8000/coordinator`
- Volunteer: `http://127.0.0.1:8000/volunteer`
- Administration: `http://127.0.0.1:8000/admin`

## Enable real Strands orchestration

Gemini is the currently tested model provider for Strands:

```bash
export GEMINI_API_KEY='...'
export PORCHLIGHT_USE_STRANDS=1
export PORCHLIGHT_MODEL_PROVIDER=gemini
export PORCHLIGHT_MODEL_ID=gemini-3.6-flash
uvicorn backend.main:app --reload
```

Do not commit API keys. The app also retains a Bedrock provider path for accounts with Bedrock model access.

Run the direct agent smoke test:

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

Current workflow tests cover:
- acceptance required before reassignment;
- approved backup search/contact/assignment;
- persisted communication status;
- no-answer protocol completion gate;
- reconciliation blocked by open human issues;
- progress calculation and reset behavior.

## Developer reset

There is intentionally **no reset/demo control in the production-facing interface**. During local development only:

```bash
curl -X POST http://127.0.0.1:8000/api/dev/reset
```

## What is still an integration boundary

This is now product-shaped but not yet a production deployment. Before a live community program pilot, add:

- real authentication / role-based authorization;
- an SMS/WhatsApp provider behind the existing communications abstraction;
- mapping/navigation provider and route optimization;
- encrypted recipient data and formal retention/privacy controls;
- organization-specific emergency and safeguarding procedures;
- monitoring, backups, migrations, and operational support.

Backup outreach is deliberately simulated in this repository; **Strands genuinely decides and sequences the workflow, while the outbound communication adapter remains the next production integration.**

## Project structure

```text
porchlight/
├── backend/
│   ├── agent.py          # Strands configuration + bounded toolsets
│   ├── config.py
│   ├── main.py           # FastAPI product API
│   ├── store.py          # seeded state + SQLite persistence
│   └── tools.py          # policy-enforcing Strands tools
├── frontend/
│   ├── coordinator.html / coordinator.js
│   ├── volunteer.html / volunteer.js
│   ├── admin.html / admin.js
│   ├── shared.js
│   └── styles.css
├── docs/
│   ├── PRD.md
│   └── ARCHITECTURE.md
├── tests/
└── scripts/
```

## Design origin

The original community meal-delivery concept and Stitch UX explorations predate the agent implementation. Porchlight keeps the warmth, mobile focus, and person-at-the-door philosophy of those screens while treating AI as background operations infrastructure rather than the interface itself.

## License

MIT — see `LICENSE`.
