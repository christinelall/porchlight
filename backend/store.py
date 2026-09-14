from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any
import itertools

_counter = itertools.count(1)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


BASE_STATE: dict[str, Any] = {
    "volunteers": {
        "v1": {
            "id": "v1", "name": "Sarah", "active": True, "available": True,
            "eligible_routes": ["r3"], "backup_priority": 99,
        },
        "v2": {
            "id": "v2", "name": "Marcus", "active": True, "available": True,
            "eligible_routes": ["r3"], "backup_priority": 1, "demo_response": "accept",
        },
        "v3": {
            "id": "v3", "name": "Elena", "active": True, "available": True,
            "eligible_routes": ["r3"], "backup_priority": 2, "demo_response": "decline",
        },
    },
    "routes": {
        "r3": {
            "id": "r3",
            "name": "Route 3 — George Town",
            "scheduled_date": "Demo Day",
            "start_time": "10:00",
            "volunteer_id": "v1",
            "status": "scheduled",
            "stop_ids": ["s1", "s2", "s3", "s4", "s5"],
        }
    },
    "stops": {
        "s1": {"id": "s1", "route_id": "r3", "sequence": 1, "recipient": "Arthur B.", "address": "18 Palm Way", "delivery_notes": "Knock twice.", "outcome": "delivered", "outcome_note": ""},
        "s2": {"id": "s2", "route_id": "r3", "sequence": 2, "recipient": "Lena J.", "address": "27 Garden Road", "delivery_notes": "Use side entrance.", "outcome": "delivered", "outcome_note": ""},
        "s3": {"id": "s3", "route_id": "r3", "sequence": 3, "recipient": "Mary S.", "address": "402 Maple Avenue", "delivery_notes": "Hard of hearing. Knock loudly.", "outcome": None, "outcome_note": ""},
        "s4": {"id": "s4", "route_id": "r3", "sequence": 4, "recipient": "George T.", "address": "8 Harbour Lane", "delivery_notes": "Ring bell once.", "outcome": None, "outcome_note": ""},
        "s5": {"id": "s5", "route_id": "r3", "sequence": 5, "recipient": "Anita R.", "address": "51 Schoolhouse Road", "delivery_notes": "Meal bag on table by door after handoff.", "outcome": None, "outcome_note": ""},
    },
    "protocols": {
        "no_answer": {
            "exception_type": "no_answer",
            "ordered_steps": [
                "Knock or ring again and wait briefly.",
                "Check the delivery notes for an approved alternate contact method.",
                "Do not leave the meal unless the program instructions explicitly allow it.",
                "Record the outcome and notify the site coordinator.",
            ],
            "escalation_target": "Site Coordinator",
            "severity": "medium",
            "requires_acknowledgement": True,
        }
    },
    # Tool-enforced proof that outreach occurred and the volunteer accepted.
    "backup_outreach": {},
    # Human completion is recorded by the app before Strands may escalate the exception.
    "protocol_completions": {},
    "issues": [],
    "activity": [],
}

STATE: dict[str, Any] = {}


def next_id(prefix: str) -> str:
    return f"{prefix}{next(_counter)}"


def add_activity(
    route_id: str,
    event_type: str,
    message: str,
    status: str = "resolved",
    human_action_required: bool = False,
    actor: str = "system",
) -> dict:
    item = {
        "id": next_id("a"),
        "timestamp": now_iso(),
        "route_id": route_id,
        "event_type": event_type,
        "message": message,
        "status": status,
        "human_action_required": human_action_required,
        "actor": actor,
    }
    STATE["activity"].insert(0, item)
    return item


def create_issue(route_id: str, stop_id: str | None, issue_type: str, severity: str, reason: str) -> dict:
    # Idempotency: the same unresolved issue is returned rather than duplicated.
    existing = next(
        (
            issue for issue in STATE["issues"]
            if issue["route_id"] == route_id
            and issue.get("stop_id") == stop_id
            and issue["type"] == issue_type
            and issue["status"] == "open"
        ),
        None,
    )
    if existing:
        return existing

    issue = {
        "id": next_id("i"),
        "route_id": route_id,
        "stop_id": stop_id,
        "type": issue_type,
        "severity": severity,
        "reason": reason,
        "status": "open",
        "created_at": now_iso(),
        "acknowledged_by": None,
    }
    STATE["issues"].insert(0, issue)
    return issue


def reset_state() -> None:
    STATE.clear()
    STATE.update(deepcopy(BASE_STATE))
    add_activity("r3", "ready", "Route 3 is ready for today's demo.", "info", actor="system")


reset_state()
