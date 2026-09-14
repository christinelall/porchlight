# Porchlight

**Helping make sure no neighbor is missed.**

A Good Neighbor agent demo for community meal-delivery coordination.

The volunteer UI stays calm and task-focused while a Strands-powered operations agent handles routine coordination behind the scenes and surfaces only exceptions that require a human.

## What works in this build

- Coordinator dashboard with route status, stop outcomes, agent activity, and human-required issues.
- Seeded volunteer cancellation scenario.
- Automatic backup-volunteer search/contact/reassignment.
- Volunteer no-answer flow with explicit deterministic protocol.
- Coordinator acknowledgement workflow.
- End-of-route reconciliation.
- Real Strands agent orchestration with custom tools when live mode is enabled.
- Tool-enforced acceptance and policy boundaries so the model cannot invent assignments or welfare actions.
- Deterministic fallback mode for UI development only; the submission demo should use live Strands mode.
- Visible Strands/tool activity markers and postcondition checks so a model response cannot masquerade as completed work.

## Run locally

Python 3.10+ is required.

```bash
python -m venv .venv
source .venv/bin/activate       # macOS/Linux
# .venv\\Scripts\\Activate.ps1 # Windows PowerShell
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

Open `http://127.0.0.1:8000`.

## Demo sequence

1. On **Coordinator**, click **Simulate Sarah cancelling**.
2. Watch the activity stream show backup outreach and reassignment to Marcus.
3. Switch to **Volunteer**.
4. Click **Problem / No Answer** for Mary S.
5. Review the fixed no-answer protocol and click **Protocol completed — notify coordinator**.
6. Switch to **Coordinator** and acknowledge the open issue.
7. Switch to **Volunteer**, click **Complete remaining normal stops**.
8. Return to **Coordinator** and click **Reconcile route**.

## Enable Strands

The app is intentionally usable before model access is configured. To run orchestration through the Strands Agent:

1. Configure AWS credentials with Amazon Bedrock inference permission.
2. The default model is `global.amazon.nova-2-lite-v1:0` (override with `PORCHLIGHT_MODEL_ID`).
3. Set:

```bash
export PORCHLIGHT_USE_STRANDS=1
```

4. Restart the server.

Verify `/api/health` reports `"enabled": true`, then run the real agent smoke test:

```bash
PORCHLIGHT_USE_STRANDS=1 python scripts/strands_smoke.py
```

The smoke test fails unless Strands genuinely reaches a valid operational postcondition.

Strands Python package: `strands-agents`.

Official docs:
- https://strandsagents.com/docs/user-guide/quickstart/python/
- https://strandsagents.com/docs/user-guide/concepts/tools/custom-tools/

## Safety boundary

The agent coordinates logistics. It does **not** diagnose recipients or invent emergency responses. No-answer/emergency handling is constrained by program-defined protocols and human acknowledgement rules.

## Project structure

```text
porchlight/
├── backend/
│   ├── agent.py
│   ├── main.py
│   ├── store.py
│   └── tools.py
├── docs/
│   └── PRD.md
├── frontend/
│   ├── app.js
│   └── index.html
├── .env.example
├── README.md
└── requirements.txt
```

## Architecture

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) and [`docs/architecture.svg`](docs/architecture.svg).

The important boundary is: **Strands chooses and sequences actions; tools and program policy authorize them.**

## Tests

```bash
python -m unittest discover -s tests -v
```

The tests cover backup acceptance enforcement, no-answer human-protocol enforcement, route reconciliation, and repeatable reset behavior.

## Pre-existing work disclosure

The original meal-delivery product concept and Stitch UX mockups predate the hackathon. The submitted Porchlight application, backend, Strands integration, custom tools, autonomous workflows, safety boundaries, and hackathon demo implementation were built during the hackathon submission period.

## License

MIT — see [`LICENSE`](LICENSE).


## Reliability note

Porchlight exposes only workflow-relevant tools to each Strands invocation (least privilege). Coverage workflows also verify a tool-backed postcondition after the agent returns and allow one bounded Strands retry if the first attempt stops without actually resolving the route. This keeps the demo agentic while preventing a plausible text-only answer from being treated as operational success.


### FastAPI / Gemini event-loop note
The live web endpoints invoke Strands with `await agent.invoke_async(...)` so Gemini runs on FastAPI's long-lived asyncio loop. The CLI smoke test can continue using the synchronous Strands bridge. `google-genai>=2.11.0` is required because newer releases include event-loop mismatch fixes.
