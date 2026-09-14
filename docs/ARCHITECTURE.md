# Porchlight Architecture — v1.3

```text
Coordinator UI          Volunteer PWA          Admin / Evaluation UI
     |                        |                         |
     +--------------------- FastAPI -------------------+
                               |
                         Product services
       routes / stops / issues / protocols / settings / scenarios
            communications / timeline / audit / agent runs
                               |
                          SQLite state
                               |
                   bounded operational events
                               |
                          Strands Agent
                    /          |           \
          coverage tools   exception tools   reconciliation
                    \          |           /
                     policy-enforcing tools
                               |
                       verified postconditions
```

## Product boundary

AI stays behind the product. Coordinators and volunteers see route status, delivery outcomes, communications, protocols and human-review tasks — not prompts, hidden reasoning, model names, or raw tool traces.

The administrator surface owns diagnostics, scenario preparation, protocol configuration, audit history and **agent evaluation evidence**.

## Agent boundary

Each bounded workflow receives only the tools needed for that task:

- **Coverage:** route lookup, approved backup search, outreach, verified assignment, escalation.
- **No answer:** protocol lookup, structured outcome recording, policy issue creation.
- **Reconciliation:** route reconciliation only.

Tools validate preconditions. A model cannot bypass a rejected assignment, fabricate a delivery, or resolve human-required review.

## Evaluation boundary

Porchlight records **operational evidence**, not hidden chain-of-thought:

- workflow + route;
- model/provider;
- timestamps/duration;
- tool calls and tool-level success/blocking;
- final workflow status;
- application postcondition and verification status.

This lets judges/admins distinguish a plausible text response from a workflow that actually changed application state correctly.

## Scenario boundary

The Scenario Lab only prepares deterministic starting state. It does not fake an agent success. A loaded scenario must still be continued through the normal product UI and, when enabled, live Strands orchestration.

This makes failure/recovery demos repeatable:

- first backup declines, second accepts;
- all backups decline and human coverage review is created;
- no-answer protocol produces a human welfare handoff.

## Safety boundary

Program-defined protocols are application configuration, not LLM-generated guidance. Welfare/safeguarding decisions remain human-owned. A route cannot close while a scheduled stop is unaccounted for or a required review remains open.

## Field/offline boundary

The volunteer surface is installable as a lightweight PWA. Last-synced route details remain viewable through intermittent connectivity. Outcome writes require an online connection so Porchlight never pretends a safety-sensitive report was submitted when it was not.

## Non-integration route visualization

Coordinator route workspaces and volunteer route homes use a local stop-sequence schematic to communicate route order and outcomes without depending on a routing API. Individual stops retain optional external navigation deep links.

## Integration seams

1. **Model provider** — Strands provider configuration; Gemini is the tested provider.
2. **Communications provider** — deterministic adapter today; replaceable with SMS/WhatsApp/email.
3. **Maps** — local sequence visualization + external deep links today; routing/ETA provider later.
4. **Persistence** — SQLite state document today; normalized encrypted schema later.
5. **Identity** — role-shaped surfaces exist; server-enforced auth can be added for a real pilot.
