# Porchlight v1.3 Demo Guide

The Scenario Lab lives under `/admin#scenarios`. Loading a scenario only prepares sample state; it does not fabricate an agent result.

## 1. Backup retry — show real agency

1. Load **Backup retry**.
2. Open `/coordinator`.
3. Open **East End**.
4. Choose **Mark unavailable & find replacement**.
5. With Strands enabled, Porchlight should:
   - find Camila and Noah as approved backups;
   - contact Camila first and receive a decline;
   - continue instead of stopping;
   - contact Noah and receive an acceptance;
   - assign Noah only after acceptance is verified.
6. Return to `/admin#evaluation` to inspect the workflow/tool evidence and verified postcondition.

## 2. Coverage gap — show safe failure

1. Load **Coverage gap**.
2. Open East End and mark Andre unavailable.
3. Both approved backups decline.
4. Porchlight must **not invent coverage**. It creates a high-priority human coverage issue instead.

## 3. No-answer handoff — show the human welfare boundary

1. Load **No-answer handoff**.
2. Open `/volunteer?route=r3`.
3. Mary S. is the next pending stop.
4. Choose **Problem / no answer**.
5. Complete the configured checklist and enter a factual note.
6. Submit the outcome.
7. Open `/coordinator` and review the Needs Attention item.
8. The coordinator sees the factual note + exact human-approved protocol and owns the decision.

## 4. Sample delivery day — show the product

Use this for a general walkthrough of routes, volunteers, recipient care cards, route visualization, protocol editing, and human-readable Recently handled stories.
