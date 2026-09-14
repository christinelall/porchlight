from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .agent import RUNTIME, run_agent_async, verify_coverage_postcondition
from .store import STATE, add_activity, now_iso, persist_state, recompute_route, reset_state, route_summary, agent_metrics, update_agent_postcondition, apply_demo_scenario
from .tools import (
    find_backup_volunteers,
    contact_backup,
    assign_volunteer,
    record_delivery_outcome,
    create_protocol_issue,
    create_coverage_gap_issue,
    reconcile_route,
)

app = FastAPI(title="Porchlight", version="1.3.0")
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
    title: str | None = None
    ordered_steps: list[str] = Field(min_length=1)
    severity: str = "medium"
    escalation_target: str = "Site Coordinator"
    requires_acknowledgement: bool = True
    note_prompt: str | None = None


class VolunteerAdminPayload(BaseModel):
    active: bool | None = None
    available: bool | None = None
    eligible_routes: list[str] | None = None
    backup_priority: int | None = Field(default=None, ge=1, le=999)


class OrganizationPayload(BaseModel):
    coordinator_name: str | None = None
    coordinator_phone: str | None = None
    emergency_note: str | None = None


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


@app.get("/service-worker.js")
def service_worker():
    return FileResponse(FRONTEND / "service-worker.js", media_type="application/javascript")


@app.get("/volunteers")
def volunteers_page():
    return FileResponse(FRONTEND / "volunteers.html")


@app.get("/api/health")
def health():
    return {"ok": True, "app": "Porchlight", "version": "1.3.0", "strands": RUNTIME.as_dict()}


def _public_state() -> dict:
    route_summaries = {rid: route_summary(rid) for rid in STATE["routes"]}
    open_issues = [i for i in STATE["issues"] if i["status"] == "open"]
    routes = list(STATE["routes"].values())
    issue_routes = {i["route_id"] for i in open_issues}
    route_risks_without_issue = sum(
        route_summaries[r["id"]]["attention"] in {"at_risk", "uncovered"} and r["id"] not in issue_routes
        for r in routes
    )
    stats = {
        "routes_total": len(routes),
        "routes_active": sum(s["lifecycle"] in {"confirmed", "in_progress"} for s in route_summaries.values()),
        "routes_complete": sum(s["lifecycle"] == "complete" for s in route_summaries.values()),
        "routes_at_risk": route_risks_without_issue,
        "open_issues": len(open_issues),
        "attention_items": len(open_issues) + route_risks_without_issue,
        "meals_scheduled": sum(len(r["stop_ids"]) for r in routes),
        "delivered": sum(1 for s in STATE["stops"].values() if s.get("outcome") == "delivered"),
    }
    return {"strands": RUNTIME.as_dict(), "stats": stats, "route_summaries": route_summaries, "agent_metrics": agent_metrics(), **STATE}


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
    route["risk_note"] = f"{old['name']} is unavailable; coverage needs to be restored."
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
        update_agent_postcondition(route_id, "restore route coverage", resolution, valid)
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




@app.post("/api/routes/{route_id}/contact-assigned")
def contact_assigned(route_id: str):
    route = STATE["routes"].get(route_id)
    if not route:
        raise HTTPException(404, "Route not found")
    volunteer = STATE["volunteers"].get(route.get("volunteer_id"))
    if not volunteer:
        raise HTTPException(409, "Route has no assigned volunteer")
    message = f"Hi {volunteer['name']}, Porchlight here. Your {route['name']} route was scheduled for {route['start_time']}. Please confirm whether you are able to start or contact the coordinator."
    comm = {
        "id": f"c{len(STATE['communications'])+1}",
        "route_id": route_id,
        "volunteer_id": volunteer["id"],
        "volunteer_name": volunteer["name"],
        "channel": "SMS",
        "status": "sent",
        "sent_at": now_iso(),
        "responded_at": None,
        "message": message,
    }
    STATE["communications"].insert(0, comm)
    route["last_contact_at"] = comm["sent_at"]
    route["last_contact_status"] = "Reminder sent · awaiting response"
    persist_state()
    add_activity(route_id, "volunteer_reminder_sent", f"Porchlight sent {volunteer['name']} a route-start reminder; awaiting response.", "info", actor="system")
    return {"ok": True, "communication": comm}


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
    route["risk_note"] = None
    route["overdue_minutes"] = 0
    route["last_contact_status"] = f"Coordinator assigned {volunteer['name']}"
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

    if payload.outcome != "delivered" and len(payload.note.strip()) < 3:
        raise HTTPException(422, "Add a short factual note describing what you observed")

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
            created = any(i["route_id"] == route_id and i.get("stop_id") == stop_id and i["status"] == "open" for i in STATE["issues"])
            update_agent_postcondition(route_id, "handle no-answer exception", "human_review_created" if created else "missing_human_review", created)
            return {"ok": True, "mode": "strands", "agent_result": result}
        result = record_delivery_outcome(route_id, stop_id, "no_answer", payload.note)
        issue = create_protocol_issue(route_id, stop_id, "no_answer")
        recompute_route(route_id)
        return {"ok": True, "mode": "fallback", "result": result, "issue": issue}

    # Structured exceptions remain deterministic. The volunteer reports facts; Porchlight
    # follows the configured protocol and escalates only when organization policy requires it.
    allowed = {"recipient_declined", "could_not_access", "meal_issue", "welfare_concern", "other"}
    if payload.outcome not in allowed:
        raise HTTPException(400, "Unsupported outcome")
    protocol = STATE["protocols"].get(payload.outcome)
    if protocol and not payload.protocol_completed:
        raise HTTPException(409, f"Complete the approved {protocol['title'].lower()} protocol before submitting")
    if protocol:
        STATE["protocol_completions"][f"{route_id}:{stop_id}:{payload.outcome}"] = True
        persist_state()
        add_activity(route_id, "protocol_completed", f"Volunteer completed the approved {protocol['title'].lower()} protocol for {stop['recipient']}.", "info", actor="human_event")
    result = record_delivery_outcome(route_id, stop_id, payload.outcome, payload.note)
    issue = None
    if protocol and protocol.get("requires_acknowledgement"):
        issue_result = create_protocol_issue(route_id, stop_id, payload.outcome)
        issue = issue_result.get("issue") if issue_result.get("ok") else None
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
    updates = payload.model_dump(exclude_none=True)
    if updates.get("severity") not in {"low", "medium", "high"}:
        raise HTTPException(400, "Severity must be low, medium, or high")
    if "title" in updates and not updates["title"].strip():
        raise HTTPException(400, "Protocol title cannot be blank")
    protocol.update(updates)
    persist_state()
    add_activity("r3", "protocol_updated", f"Administrator updated the {exception_type.replace('_',' ')} protocol.", "info", actor="admin")
    return {"ok": True, "protocol": protocol}


@app.put("/api/admin/volunteers/{volunteer_id}")
def update_volunteer(volunteer_id: str, payload: VolunteerAdminPayload):
    volunteer = STATE["volunteers"].get(volunteer_id)
    if not volunteer:
        raise HTTPException(404, "Volunteer not found")
    updates = payload.model_dump(exclude_none=True)
    if "eligible_routes" in updates:
        unknown = [rid for rid in updates["eligible_routes"] if rid not in STATE["routes"]]
        if unknown:
            raise HTTPException(400, f"Unknown routes: {', '.join(unknown)}")
    volunteer.update(updates)
    persist_state()
    add_activity("r3", "volunteer_profile_updated", f"Administrator updated {volunteer['name']}'s operational profile.", "info", actor="admin")
    return {"ok": True, "volunteer": volunteer}


@app.put("/api/admin/organization")
def update_organization(payload: OrganizationPayload):
    STATE.setdefault("organization", {}).update(payload.model_dump(exclude_none=True))
    persist_state()
    add_activity("r3", "organization_settings_updated", "Administrator updated Porchlight organization settings.", "info", actor="admin")
    return {"ok": True, "organization": STATE["organization"]}


@app.post("/api/admin/scenarios/{scenario_name}")
def load_demo_scenario(scenario_name: str):
    try:
        demo = apply_demo_scenario(scenario_name)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    return {"ok": True, "demo": demo}


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
        summary = route_summary("r3")
        verified = summary["pending"] == 0 and summary["open_issues"] == 0
        update_agent_postcondition("r3", "reconcile route", "route_clean" if verified else "route_still_open", verified)
        return {"ok": True, "mode": "strands", "agent_result": result}
    return {"ok": True, "mode": "fallback", "result": reconcile_route("r3")}
