# Porchlight — Agentic Community Meal-Delivery Coordination

**Version:** 2.0 Hackathon MVP  
**Status:** Build baseline  
**Primary track:** Good Neighbor Agent  
**Primary users:** Delivery coordinator and volunteer  
**Primary beneficiary:** Meal recipient / community member

## 1. Product vision

Porchlight is a calm, mobile-first delivery companion and operations assistant for community meal-delivery programs. The volunteer interface stays simple and human. An AI operations agent works mostly behind the scenes to coordinate route coverage, execute approved response protocols, reconcile delivery outcomes, and surface only the issues that require a human decision.

**Product promise:** Technology handles the coordination work around the delivery so volunteers can focus on the person at the door.

## 2. Problem

Community meal-delivery programs rely on coordinators and volunteers to manage frequent operational exceptions: last-minute cancellations, route gaps, delayed starts, no-answer situations, unresolved stops, and end-of-shift reconciliation. Much of this work is manual and time-sensitive. A missed handoff or unresolved delivery can affect a vulnerable recipient, while excessive alerts can overwhelm coordinators.

## 3. Goals

1. Reduce coordinator effort spent on routine route exceptions.
2. Make the volunteer experience linear, low-friction, and safe.
3. Ensure every scheduled stop reaches an explicit outcome.
4. Execute organization-defined escalation protocols consistently.
5. Interrupt a human only when policy requires approval, acknowledgement, or judgment.
6. Demonstrate genuine agent behavior: observe an event, reason over allowed choices, use tools, track state, and continue until the workflow is resolved or requires a human.

## 4. Non-goals for the MVP

- Medical diagnosis, triage, or clinical advice.
- Autonomous emergency decision-making.
- Full nonprofit CRM, fundraising, kitchen inventory, payroll, or donor management.
- Continuous volunteer location surveillance.
- Production SMS, telephony, GIS optimization, or identity management unless time permits.
- Replacing coordinator authority or local operating procedures.

## 5. Users and roles

### Coordinator
Needs a concise view of route health, unresolved exceptions, volunteer coverage, and agent actions. Can approve or acknowledge escalations and override assignments.

### Volunteer
Needs a clear route, one stop at a time, recipient-specific delivery instructions, and fast outcome reporting with minimal typing.

### Recipient
Does not need an account in the MVP. The recipient is the beneficiary whose delivery and welfare-related exceptions must not be lost in operational noise.

## 6. Core agent workflows

### Workflow A — Pre-route coverage

**Trigger:** An assigned volunteer declines, cancels, or fails to confirm by the configured cutoff.

**Agent actions:**
1. Read the affected route and required time window.
2. Find eligible backup volunteers based on availability and route constraints.
3. Contact candidates in policy-defined order.
4. Record responses.
5. Reassign the route after an eligible volunteer accepts.
6. Notify the original coordinator that coverage has been restored.
7. If no replacement is found by the escalation threshold, create a human-required issue.

**Human boundary:** The agent may assign only from the approved eligible list. Any rule exception requires coordinator approval.

### Workflow B — Delivery exception / no answer

**Trigger:** Volunteer records `No Answer`, `Needs Follow-up`, or another defined delivery exception.

**Agent actions:**
1. Capture the stop, volunteer, timestamp, and structured reason.
2. Present the organization-approved checklist/protocol to the volunteer.
3. Record protocol steps completed.
4. Notify the appropriate coordinator/contact according to deterministic policy.
5. Track acknowledgement/resolution.
6. Keep the route exception open until a permitted resolution is recorded.

**Human boundary:** The agent does not infer a medical condition or create a medical response. Emergency actions and escalation thresholds come from explicit organizational policy.

### Workflow C — End-of-shift reconciliation

**Trigger:** Volunteer finishes the final stop or attempts to end the route.

**Agent actions:**
1. Reconcile every scheduled recipient against a recorded outcome.
2. Identify missing or unresolved outcomes.
3. Prevent a clean close when policy-required issues remain open.
4. Generate a concise coordinator summary.
5. Close the route only when every stop is accounted for and required escalations are acknowledged.

## 7. Experience principles

- **Human first:** AI stays mostly invisible when work is proceeding normally.
- **One task at a time:** Volunteer screens avoid dense dashboards and chat-style interaction.
- **Exception, not notification, design:** Coordinator sees what needs action, plus a compact audit trail of work resolved automatically.
- **Calm language:** No alarmist copy unless the configured protocol explicitly requires urgency.
- **Explicit outcomes:** Every stop ends in a structured status.
- **Explainability:** Agent actions show what happened and why a human is—or is not—needed.

## 8. Existing Stitch screens to retain

### Volunteer
- Login / Start Shift
- Route Overview
- Navigation Mode
- Recipient Care Card
- Wellness Check
- Emergency / Issue Modal
- Shift Summary

### Coordinator
- Admin Dashboard Overview
- Volunteer Management
- Route Planning & Dispatch
- Route Planning Heatmap (defer advanced optimization)

## 9. Required screen updates

### Coordinator dashboard
Add **Agent Activity / Needs Attention** with two visual states:

**Resolved automatically**
- Route coverage restored
- Volunteer confirmation received
- Delay acknowledged and within policy
- Route reconciled successfully

**Human action required**
- Replacement not found
- No-answer protocol awaiting acknowledgement
- Rule exception requiring approval
- Unresolved delivery at end of route

Each item must show:
- severity/status
- short title
- one-line reason
- timestamp
- route/recipient reference
- agent action already taken
- next required human action, if any

### Volunteer issue flow
Retain the current large-button issue screen. After selection, show only the configured protocol steps and the next required action. Do not expose free-form AI reasoning.

### Shift summary
Add:
- scheduled stops
- completed deliveries
- exceptions
- unresolved issues
- route closure state

## 10. Functional requirements

### FR-1 Route assignment
Coordinator can create/view a route and assign a volunteer.

### FR-2 Confirmation
The system records volunteer confirmation or cancellation.

### FR-3 Replacement search
The agent can retrieve eligible backups and attempt permitted reassignment.

### FR-4 Agent audit trail
Every tool action is logged with event type, timestamp, route, target, result, and whether human action is required.

### FR-5 Delivery outcome
Volunteer can record Delivered, No Answer, Needs Follow-up, or Emergency/Protocol-defined issue.

### FR-6 Protocol execution
For each exception type, the system loads a configured deterministic protocol.

### FR-7 Human escalation
The agent can create an issue requiring acknowledgement or approval but cannot bypass policy boundaries.

### FR-8 Route reconciliation
All scheduled stops must have an outcome before a route is considered reconciled.

### FR-9 Coordinator override
Coordinator can override an assignment or resolve/escalate an issue, with the action recorded.

### FR-10 Demo mode
The hackathon build includes seeded data and deterministic simulated communications so the complete workflow can be demonstrated without live SMS or phone integrations.

## 11. Agent tools

The Strands agent receives narrowly-scoped tools rather than broad system access:

- `get_route(route_id)`
- `find_backup_volunteers(route_id)`
- `contact_backup(volunteer_id, route_id)`
- `assign_volunteer(route_id, volunteer_id)`
- `record_delivery_outcome(route_id, stop_id, outcome, note)`
- `get_protocol(exception_type)`
- `create_coordinator_issue(route_id, stop_id, severity, reason)`
- `acknowledge_issue(issue_id, coordinator_id)`
- `reconcile_route(route_id)`
- `log_agent_activity(...)`

Tools enforce authorization and validation. The model never receives unrestricted database or shell access.

## 12. Safety requirements

1. No diagnosis or health inference from volunteer notes.
2. Emergency call behavior is deterministic and explicitly configured, not model-selected.
3. Recipient details shown to the volunteer are limited to delivery-relevant information.
4. Agent actions are auditable.
5. Agent may not invent a substitute volunteer, recipient status, delivery result, or acknowledgement.
6. Human-required events remain visibly open until acknowledged.
7. Production deployment would require privacy review, authentication, access control, retention policy, and local program approval.

## 13. MVP data model

### Volunteer
`id, name, active, available, eligible_routes[], phone_or_demo_channel`

### Route
`id, name, scheduled_date, start_time, volunteer_id, status, stop_ids[]`

### Stop
`id, route_id, sequence, recipient_display_name, address, delivery_notes, outcome, outcome_note`

### Protocol
`exception_type, ordered_steps[], escalation_target, requires_acknowledgement`

### Issue
`id, route_id, stop_id?, type, severity, status, created_at, acknowledged_by?`

### AgentActivity
`id, timestamp, route_id, event_type, message, status, human_action_required`

## 14. Hackathon demo scenario

1. Dashboard shows Route 3 assigned to Sarah and all routes healthy.
2. Sarah cancels.
3. Agent receives the event, finds eligible backups, contacts Marcus, receives a simulated acceptance, reassigns Route 3, and records “No action needed.”
4. Marcus starts Route 3 and completes initial deliveries.
5. At Mary S., Marcus selects **Problem / No Answer**.
6. App shows the approved no-answer protocol; Marcus records completion.
7. Agent logs the exception and creates a coordinator acknowledgement item because policy requires human review.
8. Coordinator acknowledges the item.
9. Marcus completes the route.
10. Agent reconciles all stops and generates the final route summary.

## 15. Acceptance criteria for the demo build

- A user can switch between Coordinator and Volunteer demo views.
- Triggering a seeded volunteer cancellation produces visible agent activity and an updated route assignment.
- Recording `No Answer` opens the configured protocol and creates a coordinator issue after completion.
- Coordinator can acknowledge the issue.
- Route reconciliation correctly distinguishes fully resolved from unresolved routes.
- Every automated action is visible in an audit/activity stream.
- The system remains usable in demo mode even if a foundation-model call is unavailable.
- When Strands is enabled, orchestration runs through a Strands Agent using custom tools rather than hard-coded UI-only transitions.

## 16. Technical architecture

**Frontend:** Lightweight responsive HTML/CSS/JavaScript, preserving the Stitch visual language.  
**Backend:** Python + FastAPI.  
**Agent:** Strands Agents SDK, one operations agent with custom tools.  
**State for MVP:** In-memory seeded store; persistence can be added after the core demo works.  
**Model:** Amazon Bedrock by default when AWS credentials are configured.  
**Communications for MVP:** Simulated inbox/response tool to make the workflow deterministic in a public demo.

## 17. Post-MVP opportunities

- SMS/email integrations
- program-specific configurable protocol editor
- volunteer availability/preferences
- route optimization / maps
- secure authentication and role-based access
- analytics on unresolved exceptions and coverage gaps
- accessibility / voice-assisted volunteer flow
- offline-friendly mobile PWA
- multi-program tenancy

## 18. Naming

Use **Porchlight** consistently. Treat `Community Focus` and `Community Connect` only as historical prototype names; neither should appear in the submitted product UI.
