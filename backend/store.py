from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any
import itertools
import json
import os
import sqlite3

_counter = itertools.count(1)
ROOT = Path(__file__).resolve().parents[1]
DB_PATH = Path(os.getenv("PORCHLIGHT_DB_PATH", ROOT / "data" / "porchlight.db"))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def today_iso() -> str:
    return datetime.now().date().isoformat()


def offset_iso(minutes: int = 0) -> str:
    return (datetime.now(timezone.utc) + timedelta(minutes=minutes)).isoformat(timespec="seconds")


def build_base_state() -> dict[str, Any]:
    return {
        "organization": {
            "name": "Porchlight Community Delivery",
            "coordinator_name": "Maya",
            "coordinator_phone": "+1 345 555 0100",
            "timezone": "America/Cayman",
            "emergency_note": "If there is immediate danger, contact local emergency services and the site coordinator.",
        },
        "integrations": {
            "messaging": {"provider": "Demo SMS adapter", "status": "simulation"},
            "maps": {"provider": "External map deep links", "status": "enabled"},
            "agent": {"provider": "Strands Agents", "status": "enabled"},
        },
        "users": {
            "coordinator": {"id": "u1", "name": "Maya", "role": "coordinator"},
            "admin": {"id": "u2", "name": "Jordan", "role": "admin"},
        },
        "volunteers": {
            "v1": {"id": "v1", "name": "Sarah", "active": True, "available": True, "phone": "••• 0142", "eligible_routes": ["r3"], "backup_priority": 99, "reliability": 96, "demo_response": "decline"},
            "v2": {"id": "v2", "name": "Marcus", "active": True, "available": True, "phone": "••• 8321", "eligible_routes": ["r3", "r4"], "backup_priority": 1, "reliability": 98, "demo_response": "accept"},
            "v3": {"id": "v3", "name": "Elena", "active": True, "available": True, "phone": "••• 2774", "eligible_routes": ["r3"], "backup_priority": 2, "reliability": 93, "demo_response": "decline"},
            "v4": {"id": "v4", "name": "Devon", "active": True, "available": True, "phone": "••• 4408", "eligible_routes": ["r1"], "backup_priority": 1, "reliability": 97},
            "v5": {"id": "v5", "name": "Leah", "active": True, "available": True, "phone": "••• 6510", "eligible_routes": ["r2"], "backup_priority": 1, "reliability": 95},
            "v6": {"id": "v6", "name": "Andre", "active": True, "available": True, "phone": "••• 1992", "eligible_routes": ["r5"], "backup_priority": 99, "reliability": 91, "demo_response": "decline"},
            "v8": {"id": "v8", "name": "Camila", "active": True, "available": True, "phone": "••• 8830", "eligible_routes": ["r5"], "backup_priority": 1, "reliability": 96, "demo_response": "decline"},
            "v9": {"id": "v9", "name": "Noah", "active": True, "available": True, "phone": "••• 5528", "eligible_routes": ["r5"], "backup_priority": 2, "reliability": 94, "demo_response": "accept"},
            "v7": {"id": "v7", "name": "Priya", "active": True, "available": True, "phone": "••• 7382", "eligible_routes": ["r4"], "backup_priority": 1, "reliability": 97},
        },
        "routes": {
            "r1": {"id": "r1", "name": "West Bay", "scheduled_date": today_iso(), "start_time": "09:30", "volunteer_id": "v4", "status": "in_progress", "stop_ids": ["r1s1", "r1s2", "r1s3", "r1s4"], "started_at": now_iso(), "estimated_finish": "11:20"},
            "r2": {"id": "r2", "name": "Bodden Town", "scheduled_date": today_iso(), "start_time": "09:45", "volunteer_id": "v5", "status": "complete", "stop_ids": ["r2s1", "r2s2", "r2s3"], "started_at": now_iso(), "estimated_finish": "11:05"},
            "r3": {"id": "r3", "name": "George Town", "scheduled_date": today_iso(), "start_time": "10:00", "volunteer_id": "v1", "status": "confirmed", "stop_ids": ["s1", "s2", "s3", "s4", "s5"], "started_at": None, "estimated_finish": "12:10"},
            "r4": {"id": "r4", "name": "Prospect", "scheduled_date": today_iso(), "start_time": "10:15", "volunteer_id": "v7", "status": "scheduled", "stop_ids": ["r4s1", "r4s2", "r4s3"], "started_at": None, "estimated_finish": "11:40"},
            "r5": {"id": "r5", "name": "East End", "scheduled_date": today_iso(), "start_time": "10:00", "volunteer_id": "v6", "status": "at_risk", "stop_ids": ["r5s1", "r5s2", "r5s3", "r5s4"], "started_at": None, "estimated_finish": "12:30", "risk_note": "Volunteer has not started route.", "overdue_minutes": 23, "last_contact_at": None, "last_contact_status": "No response yet"},
        },
        "stops": {
            "r1s1": {"id":"r1s1","route_id":"r1","sequence":1,"recipient":"Nora K.","address":"12 Birch Walk","delivery_notes":"Ring bell.","outcome":"delivered","outcome_note":""},
            "r1s2": {"id":"r1s2","route_id":"r1","sequence":2,"recipient":"Peter M.","address":"4 Seaview Close","delivery_notes":"Side gate.","outcome":"delivered","outcome_note":""},
            "r1s3": {"id":"r1s3","route_id":"r1","sequence":3,"recipient":"Joan R.","address":"31 Harbour View","delivery_notes":"Knock twice.","outcome":None,"outcome_note":""},
            "r1s4": {"id":"r1s4","route_id":"r1","sequence":4,"recipient":"Calvin D.","address":"8 North West Point","delivery_notes":"Call on arrival.","outcome":None,"outcome_note":""},
            "r2s1": {"id":"r2s1","route_id":"r2","sequence":1,"recipient":"Iris P.","address":"15 Gun Square","delivery_notes":"","outcome":"delivered","outcome_note":""},
            "r2s2": {"id":"r2s2","route_id":"r2","sequence":2,"recipient":"Sam W.","address":"22 Belford Dr","delivery_notes":"","outcome":"delivered","outcome_note":""},
            "r2s3": {"id":"r2s3","route_id":"r2","sequence":3,"recipient":"Etta G.","address":"7 Lookout Rd","delivery_notes":"","outcome":"delivered","outcome_note":""},
            "s1": {"id":"s1","route_id":"r3","sequence":1,"recipient":"Arthur B.","address":"18 Palm Way","delivery_notes":"Knock twice.","conversation_starter":"Ask how his tomato plants are doing.","diet":"Low sodium","meal_items":"1 hot meal · 1 juice","accessibility":"Uses a cane","outcome":None,"outcome_note":""},
            "s2": {"id":"s2","route_id":"r3","sequence":2,"recipient":"Lena J.","address":"27 Garden Road","delivery_notes":"Use side entrance.","conversation_starter":"She enjoys hearing about local birds.","diet":"Regular","meal_items":"1 hot meal · 1 milk","accessibility":"","outcome":None,"outcome_note":""},
            "s3": {"id":"s3","route_id":"r3","sequence":3,"recipient":"Mary S.","address":"402 Maple Avenue","delivery_notes":"Knock loudly. Please wait briefly after the second knock.","conversation_starter":"Ask about her grandson, Timmy, who just started soccer.","diet":"Regular · no added salt","meal_items":"1 hot meal · 1 milk","accessibility":"Hard of hearing","outcome":None,"outcome_note":""},
            "s4": {"id":"s4","route_id":"r3","sequence":4,"recipient":"George T.","address":"8 Harbour Lane","delivery_notes":"Ring bell once.","conversation_starter":"He follows local cricket.","diet":"Diabetic-friendly","meal_items":"1 hot meal · 1 fruit","accessibility":"","outcome":None,"outcome_note":""},
            "s5": {"id":"s5","route_id":"r3","sequence":5,"recipient":"Anita R.","address":"51 Schoolhouse Road","delivery_notes":"Meal bag on table by door after handoff.","conversation_starter":"Ask about her orchids.","diet":"Vegetarian","meal_items":"1 hot meal · 1 milk","accessibility":"","outcome":None,"outcome_note":""},
            "r4s1": {"id":"r4s1","route_id":"r4","sequence":1,"recipient":"Mina F.","address":"19 Prospect Point","delivery_notes":"","outcome":None,"outcome_note":""},
            "r4s2": {"id":"r4s2","route_id":"r4","sequence":2,"recipient":"Henry C.","address":"61 Marina Dr","delivery_notes":"","outcome":None,"outcome_note":""},
            "r4s3": {"id":"r4s3","route_id":"r4","sequence":3,"recipient":"Olive N.","address":"9 Patrick Ave","delivery_notes":"","outcome":None,"outcome_note":""},
            "r5s1": {"id":"r5s1","route_id":"r5","sequence":1,"recipient":"Mabel H.","address":"6 Sea View","delivery_notes":"","outcome":None,"outcome_note":""},
            "r5s2": {"id":"r5s2","route_id":"r5","sequence":2,"recipient":"Roy L.","address":"11 Austin Conolly","delivery_notes":"","outcome":None,"outcome_note":""},
            "r5s3": {"id":"r5s3","route_id":"r5","sequence":3,"recipient":"Celia J.","address":"3 Farm Rd","delivery_notes":"","outcome":None,"outcome_note":""},
            "r5s4": {"id":"r5s4","route_id":"r5","sequence":4,"recipient":"Owen A.","address":"28 Queens Hwy","delivery_notes":"","outcome":None,"outcome_note":""},
        },
        "protocols": {
            "no_answer": {"exception_type":"no_answer","title":"No answer","ordered_steps":["Knock or ring again and wait briefly.","Check the delivery notes for an approved alternate contact method.","Do not leave the meal unless program instructions explicitly allow it.","Record factual observations and notify the site coordinator."],"escalation_target":"Site Coordinator","severity":"medium","requires_acknowledgement":True,"note_prompt":"Describe only what you observed. Avoid diagnoses or assumptions."},
            "welfare_concern": {"exception_type":"welfare_concern","title":"Welfare concern","ordered_steps":["Do not diagnose or enter the home unless authorized.","Record only factual observations.","Contact the site coordinator immediately.","Follow the organization emergency policy if instructed by a human coordinator."],"escalation_target":"Site Coordinator","severity":"high","requires_acknowledgement":True,"note_prompt":"Describe only what you observed. Avoid diagnoses or assumptions."},
            "could_not_access": {"exception_type":"could_not_access","title":"Could not access property","ordered_steps":["Re-check delivery/access notes.","Try the approved contact method if listed.","Do not enter restricted areas.","Record the access problem."],"escalation_target":"Site Coordinator","severity":"low","requires_acknowledgement":False,"note_prompt":"Briefly record the factual delivery outcome."},
            "recipient_declined": {"exception_type":"recipient_declined","title":"Recipient declined delivery","ordered_steps":["Confirm that the recipient is declining today’s delivery.","Do not pressure the recipient or leave the meal unless program instructions allow it.","Record the factual outcome."],"escalation_target":"Site Coordinator","severity":"low","requires_acknowledgement":False,"note_prompt":"Briefly record the factual delivery outcome."},
            "meal_issue": {"exception_type":"meal_issue","title":"Meal issue","ordered_steps":["Do not substitute or alter the meal unless authorized.","Record the problem with the meal or packaging.","Notify the site coordinator for follow-up."],"escalation_target":"Site Coordinator","severity":"medium","requires_acknowledgement":True,"note_prompt":"Describe only what you observed. Avoid diagnoses or assumptions."},
            "other": {"exception_type":"other","title":"Other delivery problem","ordered_steps":["Record only factual observations.","Do not improvise a safety or care response.","Notify the site coordinator if the issue prevents a normal delivery."],"escalation_target":"Site Coordinator","severity":"medium","requires_acknowledgement":True,"note_prompt":"Describe only what you observed. Avoid diagnoses or assumptions."},
        },
        "backup_outreach": {},
        "communications": [],
        "protocol_completions": {},
        "issues": [],
        "agent_runs": [],
        "demo": {"scenario": "baseline", "label": "Sample delivery day"},
        "activity": [
            {"id":"seed-a1","timestamp":offset_iso(-18),"route_id":"r2","event_type":"route_reconciled","message":"Bodden Town reconciled automatically: all 3 scheduled stops were accounted for.","status":"resolved","human_action_required":False,"actor":"system"},
            {"id":"seed-a2","timestamp":offset_iso(-37),"route_id":"r3","event_type":"route_confirmed","message":"Sarah confirmed the George Town route for 10:00 AM.","status":"resolved","human_action_required":False,"actor":"system"},
            {"id":"seed-a3","timestamp":offset_iso(-29),"route_id":"r4","event_type":"routine_confirmation","message":"Porchlight logged Priya's confirmation for the Prospect route; no coordinator action needed.","status":"resolved","human_action_required":False,"actor":"system"}
        ],
        "audit": [],
    }

STATE: dict[str, Any] = {}


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS app_state (id INTEGER PRIMARY KEY CHECK(id=1), payload TEXT NOT NULL, updated_at TEXT NOT NULL)")
    return conn


def persist_state() -> None:
    payload = json.dumps(STATE, separators=(",", ":"), ensure_ascii=False)
    with _conn() as conn:
        conn.execute(
            "INSERT INTO app_state(id,payload,updated_at) VALUES(1,?,?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload, updated_at=excluded.updated_at",
            (payload, now_iso()),
        )


def load_state() -> None:
    with _conn() as conn:
        row = conn.execute("SELECT payload FROM app_state WHERE id=1").fetchone()
    STATE.clear()
    if row:
        try:
            STATE.update(json.loads(row[0]))
            base = build_base_state()
            # Lightweight forward migration for product-shaped demo data. Existing
            # operational outcomes are preserved; only newly introduced fields/records
            # are added when missing.
            for bucket in ("users", "volunteers", "routes", "stops", "protocols"):
                STATE.setdefault(bucket, {})
                for key, value in base[bucket].items():
                    if key not in STATE[bucket]:
                        STATE[bucket][key] = deepcopy(value)
                    elif isinstance(value, dict) and isinstance(STATE[bucket][key], dict):
                        for field, default in value.items():
                            STATE[bucket][key].setdefault(field, deepcopy(default))
            for bucket in ("communications", "issues", "activity", "audit", "agent_runs"):
                STATE.setdefault(bucket, deepcopy(base[bucket]))
            STATE.setdefault("demo", deepcopy(base["demo"]))
            for bucket in ("organization", "integrations"):
                STATE.setdefault(bucket, {})
                for key, value in base[bucket].items():
                    if key not in STATE[bucket]:
                        STATE[bucket][key] = deepcopy(value)
                    elif isinstance(value, dict) and isinstance(STATE[bucket][key], dict):
                        for field, default in value.items():
                            STATE[bucket][key].setdefault(field, deepcopy(default))
            STATE.setdefault("backup_outreach", {})
            STATE.setdefault("protocol_completions", {})
            persist_state()
            return
        except Exception:
            pass
    STATE.update(build_base_state())
    persist_state()


def next_id(prefix: str) -> str:
    return f"{prefix}{int(datetime.now(timezone.utc).timestamp()*1000)}{next(_counter)}"


def add_audit(action: str, detail: str, actor: str = "system", route_id: str | None = None) -> dict:
    item = {"id": next_id("au"), "timestamp": now_iso(), "action": action, "detail": detail, "actor": actor, "route_id": route_id}
    STATE.setdefault("audit", []).insert(0, item)
    STATE["audit"] = STATE["audit"][:250]
    persist_state()
    return item


def add_activity(route_id: str, event_type: str, message: str, status: str = "resolved", human_action_required: bool = False, actor: str = "system") -> dict:
    item = {"id": next_id("a"), "timestamp": now_iso(), "route_id": route_id, "event_type": event_type, "message": message, "status": status, "human_action_required": human_action_required, "actor": actor}
    STATE["activity"].insert(0, item)
    STATE["activity"] = STATE["activity"][:200]
    add_audit(event_type, message, actor=actor, route_id=route_id)
    return item


def create_issue(route_id: str, stop_id: str | None, issue_type: str, severity: str, reason: str) -> dict:
    existing = next((i for i in STATE["issues"] if i["route_id"] == route_id and i.get("stop_id") == stop_id and i["type"] == issue_type and i["status"] == "open"), None)
    if existing:
        return existing
    issue = {"id": next_id("i"), "route_id": route_id, "stop_id": stop_id, "type": issue_type, "severity": severity, "reason": reason, "status": "open", "created_at": now_iso(), "acknowledged_by": None}
    STATE["issues"].insert(0, issue)
    persist_state()
    return issue


def route_lifecycle(route: dict[str, Any]) -> str:
    """Return the normal route lifecycle independently of exception/attention state."""
    if route.get("status") == "complete":
        return "complete"
    if route.get("started_at"):
        return "in_progress"
    if route.get("volunteer_id") and route.get("status") != "scheduled":
        return "confirmed"
    return "scheduled"


def route_attention(route: dict[str, Any], open_issues: int = 0) -> str | None:
    if open_issues or route.get("status") == "needs_review":
        return "needs_review"
    if route.get("status") in {"at_risk", "uncovered"}:
        return route.get("status")
    return None


def route_summary(route_id: str) -> dict[str, Any]:
    route = STATE["routes"][route_id]
    stops = [STATE["stops"][sid] for sid in route["stop_ids"]]
    delivered = sum(s.get("outcome") == "delivered" for s in stops)
    exceptions = sum(bool(s.get("outcome")) and s.get("outcome") != "delivered" for s in stops)
    pending = sum(not s.get("outcome") for s in stops)
    open_issues = [i for i in STATE["issues"] if i["route_id"] == route_id and i["status"] == "open"]
    return {
        "total": len(stops),
        "delivered": delivered,
        "exceptions": exceptions,
        "pending": pending,
        "open_issues": len(open_issues),
        "percent": round((delivered + exceptions) / len(stops) * 100) if stops else 0,
        "lifecycle": route_lifecycle(route),
        "attention": route_attention(route, len(open_issues)),
    }


def recompute_route(route_id: str) -> dict:
    route = STATE["routes"][route_id]
    previous_status = route.get("status")
    summary = route_summary(route_id)
    if summary["pending"] == 0 and summary["open_issues"] == 0:
        route["status"] = "complete"
    elif summary["open_issues"] > 0:
        route["status"] = "needs_review"
    elif route.get("started_at"):
        route["status"] = "in_progress"
    elif route["status"] not in {"uncovered", "at_risk"}:
        route["status"] = "confirmed"
    persist_state()
    if route["status"] == "complete" and previous_status != "complete":
        add_activity(
            route_id,
            "route_reconciled",
            f"{route['name']} reconciled automatically: every scheduled stop has an outcome and no human review remains open.",
            "resolved",
            actor="system",
        )
    return summary


def start_agent_run(route_id: str, workflow: str, provider: str, model_id: str, toolset: str) -> dict:
    run = {
        "id": next_id("ar"), "route_id": route_id, "workflow": workflow, "provider": provider,
        "model_id": model_id, "toolset": toolset, "status": "running", "started_at": now_iso(),
        "finished_at": None, "duration_ms": None, "tool_events": [], "postcondition": None,
        "postcondition_verified": None, "result_summary": None, "error": None,
    }
    STATE.setdefault("agent_runs", []).insert(0, run)
    STATE["agent_runs"] = STATE["agent_runs"][:100]
    persist_state()
    return run


def record_agent_tool(route_id: str, tool_name: str, detail: str, ok: bool = True) -> None:
    run = next((x for x in STATE.get("agent_runs", []) if x.get("route_id") == route_id and x.get("status") == "running"), None)
    if not run:
        return
    run.setdefault("tool_events", []).append({"timestamp": now_iso(), "tool": tool_name, "detail": detail, "ok": bool(ok)})
    persist_state()


def finish_agent_run(run_id: str, status: str, result_summary: str | None = None, error: str | None = None) -> None:
    run = next((x for x in STATE.get("agent_runs", []) if x.get("id") == run_id), None)
    if not run:
        return
    run["status"] = status
    run["finished_at"] = now_iso()
    try:
        started = datetime.fromisoformat(run["started_at"])
        finished = datetime.fromisoformat(run["finished_at"])
        run["duration_ms"] = max(0, int((finished - started).total_seconds() * 1000))
    except Exception:
        run["duration_ms"] = None
    run["result_summary"] = (result_summary or "")[:500] or None
    run["error"] = (error or "")[:800] or None
    persist_state()


def update_agent_postcondition(route_id: str, workflow: str, postcondition: str, verified: bool) -> None:
    run = next((x for x in STATE.get("agent_runs", []) if x.get("route_id") == route_id and x.get("workflow") == workflow), None)
    if not run:
        return
    run["postcondition"] = postcondition
    run["postcondition_verified"] = bool(verified)
    persist_state()


def agent_metrics() -> dict[str, Any]:
    runs = STATE.get("agent_runs", [])
    completed = [r for r in runs if r.get("status") == "succeeded"]
    failed = [r for r in runs if r.get("status") == "failed"]
    tool_calls = sum(len(r.get("tool_events", [])) for r in runs)
    verified = sum(r.get("postcondition_verified") is True for r in runs)
    handoffs = sum(1 for a in STATE.get("activity", []) if a.get("human_action_required") and a.get("actor") in {"strands_tool", "strands"})
    declines = sum(1 for r in runs for t in r.get("tool_events", []) if t.get("tool") == "contact_backup" and "declined" in t.get("detail", "").lower())
    return {
        "workflows_total": len(runs), "workflows_succeeded": len(completed), "workflows_failed": len(failed),
        "success_rate": round(len(completed) / len(runs) * 100) if runs else 0, "tool_calls": tool_calls,
        "verified_postconditions": verified, "human_handoffs": handoffs, "backup_declines_handled": declines,
        "avg_tools_per_workflow": round(tool_calls / len(runs), 1) if runs else 0,
    }


def apply_demo_scenario(name: str) -> dict:
    reset_state()
    if name == "baseline":
        STATE["demo"] = {"scenario": "baseline", "label": "Sample delivery day"}
    elif name == "backup_retry":
        r = STATE["routes"]["r5"]
        r.update({"status": "at_risk", "risk_note": "Andre reported a vehicle problem and may not be able to start.", "overdue_minutes": 18, "last_contact_status": "Awaiting coordinator confirmation"})
        STATE["volunteers"]["v6"]["available"] = True
        STATE["volunteers"]["v8"]["demo_response"] = "decline"
        STATE["volunteers"]["v9"]["demo_response"] = "accept"
        STATE["demo"] = {"scenario": "backup_retry", "label": "Backup retry: first backup declines"}
        add_activity("r5", "route_at_risk", "Andre reported a vehicle problem; East End needs a coverage decision.", "attention", True, actor="human_event")
    elif name == "coverage_gap":
        r = STATE["routes"]["r5"]
        r.update({"status": "at_risk", "risk_note": "Andre cannot cover the route; available backups may also be constrained.", "overdue_minutes": 25, "last_contact_status": "Coverage unresolved"})
        STATE["volunteers"]["v6"]["available"] = True
        STATE["volunteers"]["v8"]["demo_response"] = "decline"
        STATE["volunteers"]["v9"]["demo_response"] = "decline"
        STATE["demo"] = {"scenario": "coverage_gap", "label": "Coverage gap: all approved backups decline"}
        add_activity("r5", "route_at_risk", "East End is at risk and may require a coordinator handoff.", "attention", True, actor="human_event")
    elif name == "no_answer":
        r = STATE["routes"]["r3"]
        r["status"] = "in_progress"
        r["started_at"] = offset_iso(-24)
        STATE["stops"]["s1"].update({"outcome": "delivered", "outcome_note": "Meal handed to recipient."})
        STATE["stops"]["s2"].update({"outcome": "delivered", "outcome_note": "Meal handed to recipient."})
        STATE["demo"] = {"scenario": "no_answer", "label": "No-answer safety handoff"}
        add_activity("r3", "route_started", "Sarah started George Town; Mary S. is the next pending stop.", "info", actor="human_event")
    else:
        raise ValueError(f"Unknown demo scenario: {name}")
    persist_state()
    return STATE["demo"]


def reset_state() -> None:
    STATE.clear()
    STATE.update(deepcopy(build_base_state()))
    add_activity("r3", "route_confirmed", "Sarah confirmed the George Town route for 10:00 AM.", "info", actor="human_event")
    add_activity("r2", "route_complete", "Bodden Town route completed with all stops accounted for.", "resolved", actor="system")
    persist_state()


load_state()
