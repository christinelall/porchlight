from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .agent import RUNTIME, run_agent_async, verify_coverage_postcondition
from .store import STATE, add_activity, persist_state, recompute_route, reset_state, route_summary
from .tools import (
    find_backup_volunteers,
    contact_backup,
    assign_volunteer,
    record_delivery_outcome,
    create_protocol_issue,
    create_coverage_gap_issue,
    reconcile_route,
)

app = FastAPI(title="Porchlight", version="1.0.0")
ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
app.mount("/static", StaticFiles(directory=FRONTEND), name="static")


class OutcomePayload(BaseModel):
    outcome: str
    note: str = ""
    protocol_completed: bool = False


class UnavailablePayload(BaseModel):
    reason: str = "Volunteer is no longer available for this shift."


class StartPayload(BaseModel):
    volunteer_id: str | None = None


class AssignPayload(BaseModel):
    volunteer_id: str
    reason: str = "Coordinator reassignment"


class ProtocolPayload(BaseModel):
    ordered_steps: list[str] = Field(min_length=1)
    severity: str = "medium"
    escalation_target: str = "Site Coordinator"
    requires_acknowledgement: bool = True


@app.get("/")
def root():
    return RedirectResponse("/coordinator")


@app.get("/coordinator")
def coordinator_page():
    return FileResponse(FRONTEND / "coordinator.html")


@app.get("/volunteer")
def volunteer_page():
    return FileResponse(FRONTEND / "volunteer.html")


@app.get("/admin")
def admin_page():
    return FileResponse(FRONTEND / "admin.html")


@app.get("/api/health")
def health():
    return {"ok": True, "app": "Porchlight", "version": "1.0.0", "strands": RUNTIME.as_dict()}


def _public_state() -> dict:
    route_summaries = {rid: route_summary(rid) for rid in STATE["routes"]}
    open_issues = [i for i in STATE["issues"] if i["status"] == "open"]
    routes = list(STATE["routes"].values())
    stats = {
        "routes_total": len(routes),
        "routes_active": sum(r["status"] in {"in_progress", "confirmed"} for r in routes),
        "routes_complete": sum(r["status"] == "complete" for r in routes),
        "routes_at_risk": sum(r["status"] in {"at_risk", "uncovered", "needs_review"} for r in routes),
        "open_issues": len(open_issues),
        "meals_scheduled": sum(len(r["stop_ids"]) for r in routes),
        "delivered": sum(1 for s in STATE["stops"].values() if s.get("outcome") == "delivered"),
    }
    return {"strands": RUNTIME.as_dict(), "stats": stats, "route_summaries": route_summaries, **STATE}


@app.get("/api/state")
def state():
    return _public_state()


@app.get("/api/routes/{route_id}")
def get_route(route_id: str):
    route = STATE["routes"].get(route_id)
    if not route:
        raise HTTPException(404, "Route not found")
    return {
        "route": route,
        "summary": route_summary(route_id),
        "volunteer": STATE["volunteers"].get(route.get("volunteer_id")),
        "stops": [STATE["stops"][sid] for sid in route["stop_ids"]],
        "issues": [i for i in STATE["issues"] if i["route_id"] == route_id],
        "communications": [c for c in STATE["communications"] if c["route_id"] == route_id],
    }


@app.post("/api/routes/{route_id}/volunteer-unavailable")
async def volunteer_unavailable(route_id: str, payload: UnavailablePayload):
    route = STATE["routes"].get(route_id)
    if not route:
        raise HTTPException(404, "Route not found")
    old = STATE["volunteers"].get(route.get("volunteer_id"))
    if not old:
        raise HTTPException(409, "Route has no assigned volunteer")
    old["available"] = False
    route["status"] = "uncovered"
    persist_state()
    add_activity(route_id, "volunteer_unavailable", f"{old['name']} reported they cannot cover {route['name']}. {payload.reason}", "attention", actor="human_event")

    if RUNTIME.enabled:
        try:
            result = await run_agent_async(
                f"{old['name']} is unavailable for route {route_id}. Restore coverage within policy using tools.",
                workflow="restore route coverage",
                route_id=route_id,
                toolset="coverage",
            )
        except Exception as exc:
            raise HTTPException(502, f"Porchlight could not complete backup coordination: {exc}") from exc
        valid, resolution = verify_coverage_postcondition(route_id)
        if not valid:
            raise HTTPException(500, f"Agent finished without a valid coverage outcome: {resolution}")
        return {"ok": True, "mode": "strands", "resolution": resolution, "agent_result": result}

    candidates = find_backup_volunteers(route_id)
    for candidate in candidates.get("candidates", []):
        response = contact_backup(candidate["id"], route_id)
        if response.get("response") == "accept":
            assignment = assign_volunteer(route_id, candidate["id"])
            return {"ok": True, "mode": "fallback", "assignment": assignment}
    return {"ok": True, "mode": "fallback", "issue": create_coverage_gap_issue(route_id)}


@app.post("/api/routes/{route_id}/assign")
def manual_assign(route_id: str, payload: AssignPayload):
    route = STATE["routes"].get(route_id)
    volunteer = STATE["volunteers"].get(payload.volunteer_id)
    if not route or not volunteer:
        raise HTTPException(404, "Route or volunteer not found")
    if not volunteer.get("active") or route_id not in volunteer.get("eligible_routes", []):
        raise HTTPException(409, "Volunteer is not approved for this route")
    old = STATE["volunteers"].get(route.get("volunteer_id"))
    route["volunteer_id"] = volunteer["id"]
    route["status"] = "confirmed"
    persist_state()
    add_activity(route_id, "coordinator_reassignment", f"Maya reassigned {route['name']} from {old.get('name','Unassigned') if old else 'Unassigned'} to {volunteer['name']}. {payload.reason}", "resolved", actor="human_event")
    return {"ok": True, "route": route, "volunteer": volunteer}


@app.post("/api/routes/{route_id}/start")
def start_route(route_id: str, payload: StartPayload):
    route = STATE["routes"].get(route_id)
    if not route:
        raise HTTPException(404, "Route not found")
    assigned = route.get("volunteer_id")
    if payload.volunteer_id and assigned != payload.volunteer_id:
        raise HTTPException(403, "This route is assigned to another volunteer")
    if route["status"] in {"uncovered", "needs_review"}:
        raise HTTPException(409, "Route cannot start while coverage or review is unresolved")
    if not route.get("started_at"):
        from .store import now_iso
        route["started_at"] = now_iso()
    route["status"] = "in_progress"
    persist_state()
    volunteer = STATE["volunteers"].get(assigned, {})
    add_activity(route_id, "route_started", f"{volunteer.get('name', 'Volunteer')} started {route['name']}.", "info", actor="human_event")
    return {"ok": True, "route": route}


@app.post("/api/routes/{route_id}/stops/{stop_id}/outcome")
async def record_outcome(route_id: str, stop_id: str, payload: OutcomePayload):
    stop = STATE["stops"].get(stop_id)
    if not stop or stop["route_id"] != route_id:
        raise HTTPException(404, "Stop not found")

    if payload.outcome == "delivered":
        result = record_delivery_outcome(route_id, stop_id, "delivered", payload.note)
        recompute_route(route_id)
        return {"ok": True, "result": result}

    if payload.outcome == "no_answer":
        if not payload.protocol_completed:
            raise HTTPException(409, "Complete the approved no-answer protocol before submitting")
        STATE["protocol_completions"][f"{route_id}:{stop_id}:no_answer"] = True
        persist_state()
        add_activity(route_id, "protocol_completed", f"Volunteer completed the approved no-answer protocol for {stop['recipient']}.", "info", actor="human_event")
        if RUNTIME.enabled:
            try:
                result = await run_agent_async(
                    f"Stop {stop_id} on route {route_id}: No Answer. The volunteer completed the approved protocol. Factual note: {payload.note!r}. Record and escalate using configured policy tools.",
                    workflow="handle no-answer exception",
                    route_id=route_id,
                    toolset="no_answer",
                )
            except Exception as exc:
                raise HTTPException(502, f"Porchlight could not process the exception: {exc}") from exc
            recompute_route(route_id)
            return {"ok": True, "mode": "strands", "agent_result": result}
        result = record_delivery_outcome(route_id, stop_id, "no_answer", payload.note)
        issue = create_protocol_issue(route_id, stop_id, "no_answer")
        recompute_route(route_id)
        return {"ok": True, "mode": "fallback", "result": result, "issue": issue}

    # Structured non-medical exceptions remain deterministic. The volunteer reports facts;
    # Porchlight records them and escalates only when organization policy requires it.
    allowed = {"recipient_declined", "could_not_access", "meal_issue", "welfare_concern", "other"}
    if payload.outcome not in allowed:
        raise HTTPException(400, "Unsupported outcome")
    result = record_delivery_outcome(route_id, stop_id, payload.outcome, payload.note)
    issue = None
    if payload.outcome in {"welfare_concern", "meal_issue"}:
        severity = "high" if payload.outcome == "welfare_concern" else "medium"
        from .store import create_issue
        issue = create_issue(route_id, stop_id, f"{payload.outcome}_follow_up", severity, f"{stop['recipient']} — {payload.outcome.replace('_',' ')} reported. Coordinator review required.")
        add_activity(route_id, "human_review_required", issue["reason"], "attention", True, actor="system")
    recompute_route(route_id)
    return {"ok": True, "result": result, "issue": issue}


@app.post("/api/issues/{issue_id}/acknowledge")
def acknowledge(issue_id: str):
    issue = next((i for i in STATE["issues"] if i["id"] == issue_id), None)
    if not issue:
        raise HTTPException(404, "Issue not found")
    if issue["status"] != "acknowledged":
        issue["status"] = "acknowledged"
        issue["acknowledged_by"] = STATE["users"]["coordinator"]["name"]
        persist_state()
        add_activity(issue["route_id"], "issue_acknowledged", f"{STATE['users']['coordinator']['name']} acknowledged the {issue['type'].replace('_',' ')} item.", "resolved", actor="human_event")
        summary = recompute_route(issue["route_id"])
        if summary["pending"] == 0 and summary["open_issues"] == 0:
            reconcile_route(issue["route_id"])
    return {"ok": True, "issue": issue}


@app.put("/api/admin/protocols/{exception_type}")
def update_protocol(exception_type: str, payload: ProtocolPayload):
    if exception_type not in STATE["protocols"]:
        raise HTTPException(404, "Protocol not found")
    protocol = STATE["protocols"][exception_type]
    protocol.update(payload.model_dump())
    persist_state()
    add_activity("r3", "protocol_updated", f"Administrator updated the {exception_type.replace('_',' ')} protocol.", "info", actor="admin")
    return {"ok": True, "protocol": protocol}


# Developer-only reset kept off production-facing pages.
@app.post("/api/dev/reset")
def reset_dev_state():
    reset_state()
    return {"ok": True}


# Backwards-compatible endpoints for smoke tests / earlier builds.
@app.post("/api/demo/reset")
def reset_demo():
    return reset_dev_state()


@app.post("/api/demo/cancellation")
async def demo_cancellation():
    return await volunteer_unavailable("r3", UnavailablePayload(reason="Development scenario."))


@app.post("/api/demo/reconcile")
async def demo_reconcile():
    if RUNTIME.enabled:
        result = await run_agent_async("Reconcile route r3 now using the reconcile_route tool.", workflow="reconcile route", route_id="r3", toolset="reconcile")
        return {"ok": True, "mode": "strands", "agent_result": result}
    return {"ok": True, "mode": "fallback", "result": reconcile_route("r3")}
