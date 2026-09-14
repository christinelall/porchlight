# Porchlight v1 — product interface changes

This build replaces the hackathon/demo console with role-based product surfaces.

## Removed from normal users
- “Simulate Sarah cancelling”
- “Reset demo”
- “Complete remaining stops”
- “Reconcile route”
- “Strands live” / model information
- raw Strands tool labels in coordinator operations UI

## Coordinator
- multi-route today dashboard
- route health/progress/status
- Needs Attention queue
- at-risk routes
- recently handled timeline
- route detail drawer
- volunteer communication history
- real “Volunteer unavailable” operational action
- coordinator manual reassignment/override

## Volunteer
- mobile route home
- shift start lifecycle
- ordered stops and current/next stop
- recipient care card
- meal, diet, accessibility, access notes, conversation starter
- structured delivery outcomes
- fixed organization protocols
- factual notes
- automatic progress/reconciliation

## Administration
- volunteer roster and route eligibility
- protocol view
- Strands/model diagnostics
- separate audit trail

## Platform
- SQLite-backed persistent state
- communication status model
- automatic route recomputation
- broader structured exception taxonomy
- production-shaped endpoints with backwards-compatible smoke-test endpoints
