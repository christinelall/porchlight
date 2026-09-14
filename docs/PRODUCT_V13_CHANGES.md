# Porchlight v1.3 — Non-integration product polish

This release intentionally avoids adding new external dependencies. It strengthens the app using the existing local data, Strands tools and role surfaces.

## Coordinator
- Needs Attention now includes timing, escalation owner, route impact and recommended next action.
- Route workspaces include a visual stop sequence and next-stop navigation link.
- Recently handled events are rewritten as concise operational stories rather than low-level logs.

## Volunteer
- Compact route sequence shows progress and the current stop.
- Exception forms use protocol-specific factual-note prompts.
- Volunteers see what will happen after submission: record-and-continue vs human review.

## Administration
- Agent Evaluation stores workflow/tool/postcondition evidence without exposing hidden model reasoning.
- Scenario Lab creates deterministic starting states for repeatable demonstrations.
- Protocol editor supports title, severity, escalation target, note prompt, acknowledgement, step reordering/deletion and live preview.

## Reliability / evaluation
- Agent runs record duration, tools, errors and application postconditions.
- Coverage demos can explicitly show decline → continued reasoning → acceptance, or all-decline → human escalation.
- Test suite expanded to 13 tests.
