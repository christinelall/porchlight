from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .agent import RUNTIME, run_agent_async, verify_coverage_postcondition
from .store import STATE, add_activity, reset_state
from .tools import (
    find_backup_volunteers,
    contact_backup,
    assign_volunteer,
    record_delivery_outcome,
    create_protocol_issue,
    create_coverage_gap_issue,
    reconcile_route,
)

app = FastAPI(title="Porchlight", version="0.3.0")
ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
app.mount("/static", StaticFiles(directory=FRONTEND), name="static")


class NoAnswerPayload(BaseModel):
    note: str = "Volunteer completed the approved no-answer checklist."


@app.get("/")
def index():
    return FileResponse(FRONTEND / "index.html")


@app.get("/api/health")
def health():
    return {"ok": True, "app": "Porchlight", "strands": RUNTIME.as_dict()}


@app.get("/api/state")
def state():
    return {"strands": RUNTIME.as_dict(), **STATE}


@app.post("/api/demo/reset")
def reset_demo():
    reset_state()
    return {"ok": True}


@app.post("/api/demo/cancellation")
async def cancellation():
    route = STATE["routes"]["r3"]
    old = STATE["volunteers"][route["volunteer_id"]]
    old["available"] = False
    route["status"] = "uncovered"
    add_activity("r3", "volunteer_cancelled", f"{old['name']} cancelled Route 3.", "attention", actor="human_event")

    if RUNTIME.enabled:
        # Keep the live prompt intentionally short. This exact task shape is also used by
        # scripts/strands_smoke.py and has been verified to drive real tool use.
        base_prompt = "Sarah has cancelled route r3. Restore coverage within policy using tools."
        last_result = ""
        resolution = "agent_finished_without_valid_resolution"
        for attempt in range(1, 3):
            prompt = base_prompt
            if attempt > 1:
                prompt += (
                    " A prior agent attempt stopped without satisfying the operational postcondition. "
                    "Inspect the current route state and continue using tools until a valid outcome is actually recorded."
                )
                add_activity(
                    "r3",
                    "strands_retry",
                    "Strands is retrying the coverage workflow because the first attempt did not change state to a valid resolution.",
                    "info",
                    actor="system",
                )
            try:
                last_result = await run_agent_async(
                    prompt,
                    workflow=f"restore route coverage (attempt {attempt})",
                    toolset="coverage",
                )
            except Exception as exc:
                raise HTTPException(502, f"Live Strands workflow failed: {exc}") from exc

            valid, resolution = verify_coverage_postcondition("r3")
            if valid:
                return {
                    "ok": True,
                    "mode": "strands",
                    "resolution": resolution,
                    "agent_result": last_result,
                    "attempts": attempt,
                }

        raise HTTPException(500, f"Strands returned without a valid operational resolution after 2 attempts: {resolution}")

    # Explicit development fallback. It is never represented as Strands.
    candidates = find_backup_volunteers("r3")
    for candidate in candidates.get("candidates", []):
        response = contact_backup(candidate["id"], "r3")
        if response.get("response") == "accept":
            assignment = assign_volunteer("r3", candidate["id"])
            return {"ok": True, "mode": "fallback", "assignment": assignment}
    issue = create_coverage_gap_issue("r3")
    return {"ok": True, "mode": "fallback", "resolution": "human_escalation_created", "issue": issue}


@app.post("/api/demo/no-answer")
async def no_answer(payload: NoAnswerPayload):
    # This flag represents the human pressing "Protocol completed" in the volunteer UI.
    STATE["protocol_completions"]["r3:s3:no_answer"] = True
    add_activity(
        "r3",
        "protocol_completed",
        "Volunteer confirmed completion of the approved no-answer checklist for Mary S.",
        "info",
        actor="human_event",
    )

    if RUNTIME.enabled:
        try:
            result = await run_agent_async(
                "The volunteer at stop s3 on route r3 selected No Answer and has completed the approved no-answer protocol. "
                f"Their factual note is: {payload.note!r}. Use the configured policy tools to record and escalate this event.",
                workflow="handle no-answer exception",
                toolset="no_answer",
            )
        except Exception as exc:
            raise HTTPException(502, f"Live Strands workflow failed: {exc}") from exc

        stop = STATE["stops"]["s3"]
        issue = next((i for i in STATE["issues"] if i.get("stop_id") == "s3" and i["status"] == "open"), None)
        if stop.get("outcome") != "no_answer" or not issue:
            raise HTTPException(500, "Strands returned without recording the no-answer outcome and policy issue")
        return {"ok": True, "mode": "strands", "agent_result": result}

    outcome = record_delivery_outcome("r3", "s3", "no_answer", payload.note)
    issue = create_protocol_issue("r3", "s3", "no_answer")
    return {"ok": True, "mode": "fallback", "outcome": outcome, "issue": issue}


@app.post("/api/issues/{issue_id}/acknowledge")
def acknowledge(issue_id: str):
    issue = next((i for i in STATE["issues"] if i["id"] == issue_id), None)
    if not issue:
        raise HTTPException(404, "Issue not found")
    if issue["status"] == "acknowledged":
        return {"ok": True, "issue": issue}
    issue["status"] = "acknowledged"
    issue["acknowledged_by"] = "Demo Coordinator"
    add_activity(
        issue["route_id"],
        "issue_acknowledged",
        f"Coordinator acknowledged {issue['type'].replace('_', ' ')}.",
        "resolved",
        actor="human_event",
    )
    return {"ok": True, "issue": issue}


@app.post("/api/demo/complete-rest")
def complete_rest():
    for sid in ["s4", "s5"]:
        if not STATE["stops"][sid]["outcome"]:
            record_delivery_outcome("r3", sid, "delivered", "Demo delivery completed.")
    return {"ok": True}


@app.post("/api/demo/reconcile")
async def reconcile():
    if RUNTIME.enabled:
        try:
            result = await run_agent_async(
                "Reconcile route r3 now using the reconcile_route tool. Do not claim completion unless the tool says clean=true.",
                workflow="reconcile route",
                toolset="reconcile",
            )
        except Exception as exc:
            raise HTTPException(502, f"Live Strands workflow failed: {exc}") from exc
        return {"ok": True, "mode": "strands", "agent_result": result}
    return {"ok": True, "mode": "fallback", "result": reconcile_route("r3")}
