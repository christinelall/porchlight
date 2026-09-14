# Porchlight Architecture

Porchlight deliberately separates **agent reasoning** from **policy enforcement**. Strands chooses and sequences operational tools; tools validate eligibility, acceptance, human protocol completion, and route-close conditions.

```mermaid
flowchart LR
    C[Coordinator Web UI] --> API[FastAPI Backend]
    V[Volunteer Mobile UI] --> API

    API -->|bounded workflow event| S[Strands Operations Agent]
    S --> M[Amazon Bedrock\nNova 2 Lite]

    S --> T1[get_route]
    S --> T2[find_backup_volunteers]
    S --> T3[contact_backup]
    S --> T4[assign_volunteer]
    S --> T5[get_protocol]
    S --> T6[record_delivery_outcome]
    S --> T7[create_protocol_issue]
    S --> T8[reconcile_route]

    T1 --> D[(MVP State Store)]
    T2 --> D
    T3 --> D
    T4 --> D
    T5 --> P[Deterministic Program Policy]
    T6 --> D
    T7 --> P
    T7 --> D
    T8 --> D

    D --> A[Auditable Agent Activity]
    A --> C
    D --> V

    H[Human safety boundary] -. protocol completion / acknowledgement .-> API
```

## Safety boundary

- Strands may decide **which permitted logistics tool to use next**.
- `assign_volunteer` refuses assignment unless an eligible volunteer was contacted and accepted.
- `create_protocol_issue` refuses escalation unless the volunteer explicitly confirmed the configured protocol was completed.
- Severity, escalation target, and no-answer language come from deterministic program policy, not the model.
- `reconcile_route` refuses clean closure while outcomes or required acknowledgements are unresolved.
- No medical diagnosis or welfare inference is delegated to the model.

## Hackathon data

All recipient, volunteer, address, and route data in the demo is synthetic. Backup communications are simulated so judges can replay the workflow consistently; the orchestration and tool selection are performed by Strands in live mode.
