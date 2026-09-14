from __future__ import annotations

try:
    from strands import tool
except ImportError:
    # Development/demo fallback: normal Python calls still work without the SDK.
    def tool(func=None, **_kwargs):
        if func is None:
            return lambda f: f
        return func

from .store import STATE, add_activity, create_issue


@tool
def get_route(route_id: str) -> dict:
    """Get a delivery route and its current assignment/status.

    Args:
        route_id: Route identifier such as r3.
    """
    route = STATE["routes"].get(route_id)
    if not route:
        return {"ok": False, "error": "route_not_found"}
    volunteer = STATE["volunteers"].get(route.get("volunteer_id"))
    return {"ok": True, "route": route, "assigned_volunteer": volunteer}


@tool
def find_backup_volunteers(route_id: str) -> dict:
    """Find approved active and available backup volunteers for a route in policy order.

    Args:
        route_id: Route that needs replacement coverage.
    """
    route = STATE["routes"].get(route_id)
    if not route:
        return {"ok": False, "error": "route_not_found", "candidates": []}
    current = route.get("volunteer_id")
    candidates = [
        {
            "id": v["id"],
            "name": v["name"],
            "priority": v.get("backup_priority", 100),
        }
        for v in STATE["volunteers"].values()
        if v["id"] != current
        and v["active"]
        and v["available"]
        and route_id in v["eligible_routes"]
    ]
    candidates.sort(key=lambda item: (item["priority"], item["name"]))
    add_activity(
        route_id,
        "backup_search",
        f"Found {len(candidates)} approved backup candidate(s).",
        "info",
        actor="strands_tool",
    )
    return {"ok": True, "candidates": candidates}


@tool
def contact_backup(volunteer_id: str, route_id: str) -> dict:
    """Contact an approved backup volunteer and record their response.

    For this hackathon demo the outbound communication is simulated, while the agent
    genuinely decides which candidate to contact and how to proceed.

    Args:
        volunteer_id: Approved volunteer identifier returned by find_backup_volunteers.
        route_id: Route needing coverage.
    """
    volunteer = STATE["volunteers"].get(volunteer_id)
    route = STATE["routes"].get(route_id)
    if not volunteer or not route:
        return {"ok": False, "error": "not_found"}
    if not volunteer["active"] or not volunteer["available"] or route_id not in volunteer["eligible_routes"]:
        return {"ok": False, "error": "volunteer_not_eligible"}

    response = volunteer.get("demo_response", "decline")
    STATE["backup_outreach"][f"{route_id}:{volunteer_id}"] = response
    add_activity(
        route_id,
        "backup_contacted",
        f"Contacted {volunteer['name']} for backup coverage — response: {response}.",
        "info",
        actor="strands_tool",
    )
    return {"ok": True, "volunteer_id": volunteer_id, "response": response}


@tool
def assign_volunteer(route_id: str, volunteer_id: str) -> dict:
    """Assign a backup volunteer only after that volunteer has explicitly accepted.

    Args:
        route_id: Route requiring coverage.
        volunteer_id: Volunteer who accepted the backup request.
    """
    route = STATE["routes"].get(route_id)
    volunteer = STATE["volunteers"].get(volunteer_id)
    if not route or not volunteer:
        return {"ok": False, "error": "not_found"}
    if not volunteer["active"] or not volunteer["available"] or route_id not in volunteer["eligible_routes"]:
        return {"ok": False, "error": "volunteer_not_eligible"}
    if STATE["backup_outreach"].get(f"{route_id}:{volunteer_id}") != "accept":
        return {"ok": False, "error": "acceptance_not_verified"}

    route["volunteer_id"] = volunteer_id
    route["status"] = "covered"
    add_activity(
        route_id,
        "coverage_restored",
        f"Route coverage restored: {volunteer['name']} accepted and was assigned.",
        "resolved",
        actor="strands_tool",
    )
    return {"ok": True, "route_id": route_id, "volunteer_id": volunteer_id, "volunteer_name": volunteer["name"]}


@tool
def get_protocol(exception_type: str) -> dict:
    """Return the organization-defined deterministic protocol for a delivery exception.

    Args:
        exception_type: Configured exception type, for example no_answer.
    """
    protocol = STATE["protocols"].get(exception_type)
    if not protocol:
        return {"ok": False, "error": "protocol_not_found"}
    return {"ok": True, "protocol": protocol}


@tool
def record_delivery_outcome(route_id: str, stop_id: str, outcome: str, note: str = "") -> dict:
    """Record a structured delivery outcome without diagnosing or inferring recipient health.

    Args:
        route_id: Route identifier.
        stop_id: Stop identifier on the route.
        outcome: One of delivered, no_answer, needs_follow_up, emergency.
        note: Optional factual volunteer note.
    """
    stop = STATE["stops"].get(stop_id)
    if not stop or stop["route_id"] != route_id:
        return {"ok": False, "error": "stop_not_found"}
    allowed = {"delivered", "no_answer", "needs_follow_up", "emergency"}
    if outcome not in allowed:
        return {"ok": False, "error": "invalid_outcome", "allowed": sorted(allowed)}

    stop["outcome"] = outcome
    stop["outcome_note"] = note
    add_activity(
        route_id,
        "delivery_outcome",
        f"{stop['recipient']}: recorded outcome '{outcome}'.",
        "info",
        actor="strands_tool",
    )
    return {"ok": True, "stop": stop}


@tool
def create_protocol_issue(route_id: str, stop_id: str, exception_type: str) -> dict:
    """Create a coordinator issue using configured policy after the human completed the protocol.

    The tool, not the model, determines severity, wording, acknowledgement requirement,
    and escalation target from policy.

    Args:
        route_id: Route identifier.
        stop_id: Stop requiring follow-up.
        exception_type: Configured exception type such as no_answer.
    """
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

    reason = (
        f"{stop['recipient']} — {exception_type.replace('_', ' ')}. "
        f"Approved volunteer protocol completed; {protocol['escalation_target']} acknowledgement required."
    )
    issue = create_issue(
        route_id,
        stop_id,
        f"{exception_type}_follow_up",
        protocol.get("severity", "medium"),
        reason,
    )
    add_activity(
        route_id,
        "human_review_required",
        reason,
        "attention",
        True,
        actor="strands_tool",
    )
    return {"ok": True, "issue": issue, "requires_acknowledgement": protocol.get("requires_acknowledgement", True)}


@tool
def create_coverage_gap_issue(route_id: str) -> dict:
    """Create a human-required issue when approved backup outreach cannot restore coverage.

    Args:
        route_id: Uncovered route identifier.
    """
    route = STATE["routes"].get(route_id)
    if not route:
        return {"ok": False, "error": "route_not_found"}
    issue = create_issue(
        route_id,
        None,
        "coverage_gap",
        "high",
        f"{route['name']} remains uncovered after approved backup outreach. Coordinator action required.",
    )
    route["status"] = "attention"
    add_activity(
        route_id,
        "coverage_gap",
        issue["reason"],
        "attention",
        True,
        actor="strands_tool",
    )
    return {"ok": True, "issue": issue}


@tool
def reconcile_route(route_id: str) -> dict:
    """Reconcile every scheduled stop and determine whether a route can be cleanly closed.

    Args:
        route_id: Route identifier to reconcile.
    """
    route = STATE["routes"].get(route_id)
    if not route:
        return {"ok": False, "error": "route_not_found"}
    stops = [STATE["stops"][sid] for sid in route["stop_ids"]]
    missing = [s["id"] for s in stops if not s.get("outcome")]
    open_issues = [i["id"] for i in STATE["issues"] if i["route_id"] == route_id and i["status"] == "open"]
    clean = not missing and not open_issues
    summary = {
        "scheduled": len(stops),
        "delivered": sum(s.get("outcome") == "delivered" for s in stops),
        "exceptions": sum(s.get("outcome") not in (None, "delivered") for s in stops),
        "missing": len(missing),
        "open_issues": len(open_issues),
    }
    if clean:
        route["status"] = "complete"
        add_activity(
            route_id,
            "route_reconciled",
            f"Route reconciled: {summary['scheduled']} stops accounted for, {summary['exceptions']} exception(s), no open issues.",
            "resolved",
            actor="strands_tool",
        )
    else:
        route["status"] = "attention"
        add_activity(
            route_id,
            "route_not_reconciled",
            f"Route cannot close yet: {len(missing)} missing outcome(s), {len(open_issues)} open issue(s).",
            "attention",
            True,
            actor="strands_tool",
        )
    return {
        "ok": True,
        "clean": clean,
        "summary": summary,
        "missing_stop_ids": missing,
        "open_issue_ids": open_issues,
    }
