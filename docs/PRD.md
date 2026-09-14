# Porchlight — Product Requirements

**Version:** 3.0 Product Build  
**Status:** Working product-shaped prototype  
**Primary users:** Delivery coordinator, volunteer, program administrator  
**Primary beneficiary:** Meal recipient / community member

## 1. Vision

Porchlight is a calm, human-first operations platform for community meal-delivery programs. Volunteers should spend their attention on the person at the door, not on administrative software. Coordinators should see the handful of situations that need judgment, not every low-level event. An AI operations agent works in the background to resolve routine logistics within program-defined policy.

**Promise:** Porchlight handles coordination around the delivery so people can focus on people.

## 2. Product principles

1. **AI is infrastructure, not the interface.** Normal users should not need to know which model or tool executed a workflow.
2. **Exception-first coordination.** Coordinator home prioritizes what needs action now; routine agent work moves to a quiet timeline.
3. **One stop at a time.** Volunteer UI is mobile-first, legible, and task-focused.
4. **Structured facts over free-form inference.** Delivery outcomes are explicit; factual notes never become medical diagnoses.
5. **Human welfare boundary.** Logistics can be autonomous. Welfare, safeguarding, and emergency judgment remains human/policy controlled.
6. **Auditable by design.** Agent/tool details are available to administrators without cluttering operational UX.
7. **Every stop accounted for.** A route cannot quietly disappear into “complete” while a delivery or required review is unresolved.

## 3. Roles

### Coordinator
Needs a concise picture of route health, volunteer coverage, delivery progress, late starts, and unresolved exceptions. Can review/acknowledge issues and manage operational exceptions.

### Volunteer
Needs route assignment, clear stop order, navigation-ready address, delivery/access notes, recipient-specific context, and fast structured outcome reporting.

### Administrator
Manages volunteers, protocol configuration, technical diagnostics, audit trails, and future program settings.

### Recipient
Does not require an account in the first product version. Recipient information is limited to what is operationally necessary for a safe, respectful delivery.

## 4. Core experiences

### 4.1 Coordinator Home
Must immediately answer:
- Are today’s routes covered?
- Which routes have started / completed?
- Is anything at risk of being late?
- Which recipient/route issues require a person?

Components:
- summary cards;
- routes list with progress and status;
- Needs Attention queue;
- “Recently handled by Porchlight” timeline;
- route detail panel with stops and communication history.

### 4.2 Volunteer Route
Lifecycle:
`Assigned → Confirmed → Started → Delivering → Complete`

Volunteer sees:
- route/start time/estimated finish;
- progress (`x of y accounted for`);
- ordered stops;
- current/next stop;
- recipient care card;
- structured outcome choices.

### 4.3 Recipient Care Card
Contains only delivery-relevant context:
- display name;
- address;
- access/delivery instructions;
- accessibility note when operationally useful;
- meal/diet information;
- optional conversation starter.

### 4.4 Exception Flow
Structured outcomes:
- Delivered
- No Answer
- Recipient Declined
- Could Not Access Property
- Meal Issue
- Welfare Concern
- Other

If an organization-defined protocol exists, show its fixed steps and require volunteer completion before submission. AI must not invent protocol content.

### 4.5 Administration
Separate from operational screens:
- volunteer roster / eligibility / availability;
- protocols;
- Strands/model diagnostics;
- audit trail.

## 5. Agent workflows

### A. Coverage recovery
Trigger: assigned volunteer becomes unavailable or fails a future confirmation cutoff.

Strands may:
1. inspect route;
2. find approved eligible backups;
3. contact in policy order;
4. react to decline/accept responses;
5. assign only after tool-verified acceptance;
6. escalate if coverage cannot be restored.

### B. No-answer processing
Trigger: volunteer records `No Answer` after completing the organization-approved protocol.

Strands may:
1. load configured policy;
2. record factual outcome/note;
3. create policy-defined coordinator issue;
4. stop.

It may not infer illness, injury, consciousness, neglect, or safety.

### C. Background reconciliation
After each outcome or human acknowledgement, Porchlight recalculates route state. A route is complete only when every stop has a structured outcome and no required issue remains open.

## 6. Communications

Product model supports outbound communications with:
- target volunteer;
- channel;
- message;
- sent time;
- response status;
- response time.

Current repository uses a deterministic simulated adapter. Production replaces this with SMS/WhatsApp/email without changing Strands’ decision boundary.

## 7. Persistence

Current build persists application state to SQLite. State includes routes, stops, volunteers, communications, issues, outcomes, protocols, operational timeline, and audit history.

Production should migrate from the single state document to normalized relational tables with migrations, encryption, access control, backups, and retention policy.

## 8. Safety requirements

1. No diagnosis, clinical triage, or medical inference.
2. No autonomous emergency decision-making.
3. Program protocols are configuration, not LLM-generated instructions.
4. Reassignment requires real/verified volunteer acceptance.
5. Recipient outcome cannot be invented by an agent.
6. Human-required items stay open until explicitly acknowledged/resolved.
7. Agent actions are auditable.
8. Production pilot requires privacy, safeguarding, authentication, retention, and local program review.

## 9. Product statuses

### Route
- `scheduled`
- `confirmed`
- `uncovered`
- `at_risk`
- `in_progress`
- `needs_review`
- `complete`

### Communication
- `queued`
- `sent`
- `accept`
- `decline`
- `timed_out`
- `failed`

### Issue
- `open`
- `acknowledged`
- future: `resolved`, `escalated`

## 10. Product acceptance criteria

- Coordinator and volunteer experiences are separate pages with role-appropriate actions.
- Everyday views never expose “Strands live”, model names, raw tool calls, or demo/reset buttons.
- Coordinator sees multiple routes and a human-only attention queue.
- Volunteer can start a route, progress through stops, and record structured outcomes.
- No-answer displays the configured protocol before submission.
- Agent-restored coverage appears as a human-readable operational outcome and communication history.
- Admin can see technical diagnostics and audit detail.
- State survives server restart.
- Route progress/reconciliation updates without a manual “reconcile” button.
- Workflow tests enforce acceptance/policy boundaries.

## 11. Next production milestones

1. Authentication and real role-based authorization.
2. Twilio/WhatsApp or chosen communication connector.
3. Maps/navigation and route optimization.
4. Program onboarding/configuration for routes, volunteers, recipients, meals and protocols.
5. Normalized encrypted database schema + migrations.
6. Notifications/background workers and scheduled volunteer confirmations.
7. Safeguarding/privacy/retention review for pilot jurisdiction.
8. Observability and agent evaluation suite.
