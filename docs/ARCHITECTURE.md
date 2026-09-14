# Porchlight Architecture

```text
Coordinator UI      Volunteer UI       Admin UI
     |                   |                |
     +---------------- FastAPI -----------+
                         |
                   Product services
         routes / stops / issues / protocols
             communications / audit
                         |
                    SQLite state
                         |
            bounded operational events
                         |
                  Strands Agent
                  /     |      \
        coverage tools  |   reconciliation
                        |
               exception tools
                        |
          policy-enforcing functions
```

## Design boundary

The model is not granted broad database or shell access. Each workflow receives a narrow Strands toolset.

- **Coverage:** route lookup, approved backup search, outreach, verified assignment, escalation.
- **No answer:** protocol lookup, structured outcome recording, policy issue creation.
- **Reconciliation:** route reconciliation only.

Tools validate preconditions. Tool results are authoritative.

## UI boundary

Coordinator and volunteer screens show operational language only. Model/provider/tool diagnostics live on the administrator surface. This keeps Porchlight useful even if the underlying model provider changes.

## Current integration seams

The repository deliberately leaves three replaceable adapters:

1. **Model provider** — Strands model configuration.
2. **Communications provider** — currently simulated; production SMS/WhatsApp/email later.
3. **Persistence** — SQLite state document today; normalized production data model later.
