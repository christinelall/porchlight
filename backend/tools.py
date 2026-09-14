from __future__ import annotations

try:
    from strands import tool
except ImportError:
    def tool(func=None, **_kwargs):
        if func is None:
            return lambda f: f
        return func

from .store import STATE, add_activity, create_issue, now_iso, persist_state, recompute_route


@tool
def get_route(route_id: str) -> dict:
    """Get a delivery route and its current assignment/status."""
    route = STATE["routes"].get(route_id)
    if not route:
        return {"ok": False, "error": "route_not_found"}
    volunteer = STATE["volunteers"].get(route.get("volunteer_id"))
    return {"ok": True, "route": route, "assigned_volunteer": volunteer}


@tool
def find_backup_volunteers(route_id: str) -> dict:
    """Find approved active and available backup volunteers for a route in policy order."""
    route = STATE["routes"].get(route_id)
    if not route:
        return {"ok": False, "error": "route_not_found", "candidates": []}
    current = route.get("volunteer_id")
    candidates = [
        {"id": v["id"], "name": v["name"], "priority": v.get("backup_priority", 100), "reliability": v.get("reliability")}
        for v in STATE["volunteers"].values()
        if v["id"] != current and v["active"] and v["available"] and route_id in v["eligible_routes"]
    ]
    candidates.sort(key=lambda item: (item["priority"], item["name"]))
    add_activity(route_id, "backup_search", f"Porchlight found {len(candidates)} approved backup volunteer(s).", "info", actor="strands_tool")
    return {"ok": True, "candidates": candidates}


@tool
def contact_backup(volunteer_id: str, route_id: str) -> dict:
    """Contact an approved backup volunteer and record their response."""
    volunteer = STATE["volunteers"].get(volunteer_id)
    route = STATE["routes"].get(route_id)
    if not volunteer or not route:
        return {"ok": False, "error": "not_found"}
    if not volunteer["active"] or not volunteer["available"] or route_id not in volunteer["eligible_routes"]:
        return {"ok": False, "error": "volunteer_not_eligible"}
    response = volunteer.get("demo_response", "decline")
    STATE["backup_outreach"][f"{route_id}:{volunteer_id}"] = response
    comm = {"id": f"c{len(STATE['communications'])+1}", "route_id": route_id, "volunteer_id": volunteer_id, "volunteer_name": volunteer["name"], "channel": "SMS", "status": response, "sent_at": now_iso(), "responded_at": now_iso(), "message": f"Can you cover {route['name']} at {route['start_time']} today?"}
    STATE["communications"].insert(0, comm)
    persist_state()
    add_activity(route_id, "backup_contacted", f"{volunteer['name']} was contacted for backup coverage and {('accepted' if response == 'accept' else 'declined')}.", "info", actor="strands_tool")
    return {"ok": True, "volunteer_id": volunteer_id, "response": response}


@tool
def assign_volunteer(route_id: str, volunteer_id: str) -> dict:
    """Assign a backup volunteer only after that volunteer has explicitly accepted."""
    route = STATE["routes"].get(route_id)
    volunteer = STATE["volunteers"].get(volunteer_id)
    if not route or not volunteer:
        return {"ok": False, "error": "not_found"}
    if STATE["backup_outreach"].get(f"{route_id}:{volunteer_id}") != "accept":
        return {"ok": False, "error": "acceptance_not_verified"}
    route["volunteer_id"] = volunteer_id
    route["status"] = "confirmed"
    persist_state()
    add_activity(route_id, "coverage_restored", f"Coverage restored. {volunteer['name']} accepted {route['name']}; no coordinator action is needed.", "resolved", actor="strands_tool")
    return {"ok": True, "route_id": route_id, "volunteer_id": volunteer_id, "volunteer_name": volunteer["name"]}


@tool
def get_protocol(exception_type: str) -> dict:
    """Return the organization-defined deterministic protocol for a delivery exception."""
    protocol = STATE["protocols"].get(exception_type)
    return {"ok": bool(protocol), "protocol": protocol, **({} if protocol else {"error": "protocol_not_found"})}


@tool
def record_delivery_outcome(route_id: str, stop_id: str, outcome: str, note: str = "") -> dict:
    """Record a structured delivery outcome without diagnosing or inferring recipient health."""
    stop = STATE["stops"].get(stop_id)
    if not stop or stop["route_id"] != route_id:
        return {"ok": False, "error": "stop_not_found"}
    allowed = {"delivered", "no_answer", "recipient_declined", "could_not_access", "meal_issue", "welfare_concern", "other"}
    if outcome not in allowed:
        return {"ok": False, "error": "invalid_outcome", "allowed": sorted(allowed)}
    stop["outcome"] = outcome
    stop["outcome_note"] = note
    persist_state()
    add_activity(route_id, "delivery_outcome", f"{stop['recipient']}: {outcome.replace('_', ' ')} recorded.", "info", actor="strands_tool")
    recompute_route(route_id)
    return {"ok": True, "stop": stop}


@tool
def create_protocol_issue(route_id: str, stop_id: str, exception_type: str) -> dict:
    """Create a coordinator issue using configured policy after a human completed the protocol."""
    stop = STATE["stops"].get(stop_id)
    protocol = STATE["protocols"].get(exception_type)
    if not stop or stop.get("route_id") != route_id:
        return {"ok": False, "error": "stop_not_found"}
    if not protocol:
        return {"ok": False, "error": "protocol_not_found"}
    if not STATE["protocol_completions"].get(f"{route_id}:{stop_id}:{exception_type}"):
        return {"ok": False, "error": "human_protocol_completion_not_verified"}
    if stop.get("outcome") != exception_type:
        return {"ok": False, "error": "matching_outcome_not_recorded"}
    reason = f"{stop['recipient']} — {protocol['title'].lower()}. Approved volunteer protocol completed; {protocol['escalation_target']} review required."
    issue = create_issue(route_id, stop_id, f"{exception_type}_follow_up", protocol.get("severity", "medium"), reason)
    add_activity(route_id, "human_review_required", reason, "attention", True, actor="strands_tool")
    recompute_route(route_id)
    return {"ok": True, "issue": issue, "requires_acknowledgement": protocol.get("requires_acknowledgement", True)}


@tool
def create_coverage_gap_issue(route_id: str) -> dict:
    """Create a human-required issue when approved backup outreach cannot restore coverage."""
    route = STATE["routes"].get(route_id)
    if not route:
        return {"ok": False, "error": "route_not_found"}
    issue = create_issue(route_id, None, "coverage_gap", "high", f"{route['name']} remains uncovered after approved backup outreach. Coordinator action required.")
    route["status"] = "needs_review"
    persist_state()
    add_activity(route_id, "coverage_gap", issue["reason"], "attention", True, actor="strands_tool")
    return {"ok": True, "issue": issue}


@tool
def reconcile_route(route_id: str) -> dict:
    """Reconcile every scheduled stop and determine whether a route can be cleanly closed."""
    route = STATE["routes"].get(route_id)
    if not route:
        return {"ok": False, "error": "route_not_found"}
    summary = recompute_route(route_id)
    clean = summary["pending"] == 0 and summary["open_issues"] == 0
    if clean:
        add_activity(route_id, "route_reconciled", f"{route['name']} reconciled automatically: {summary['total']} stops accounted for, {summary['exceptions']} exception(s), no open issues.", "resolved", actor="strands_tool")
    return {"ok": True, "clean": clean, "summary": summary}
