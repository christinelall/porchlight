from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .config import GEMINI_API_KEY, MODEL_ID, MODEL_PROVIDER, USE_STRANDS
from .store import STATE, add_activity, start_agent_run, finish_agent_run
from .tools import (
    get_route,
    find_backup_volunteers,
    contact_backup,
    assign_volunteer,
    get_protocol,
    record_delivery_outcome,
    create_protocol_issue,
    create_coverage_gap_issue,
    reconcile_route,
)

try:
    from strands import Agent
    STRANDS_INSTALLED = True
except ImportError:
    Agent = None  # type: ignore
    STRANDS_INSTALLED = False


SYSTEM_PROMPT = """
You are the Porchlight operations agent for a community meal-delivery program.

Your purpose is to handle routine logistics so coordinators and volunteers can focus on people.
You must act only through the provided tools and stay strictly inside configured policy.

NON-NEGOTIABLE RULES
- Never diagnose a recipient or infer a medical condition, consciousness, safety, or welfare state.
- Never invent volunteers, acceptance, deliveries, acknowledgements, outreach, or route facts.
- Tool results are authoritative. If a tool rejects an action, do not work around it.
- Do not expose hidden reasoning. Give only a short operational result after tool use.
- Human care/safety decisions remain with the program coordinator and configured protocol.

COVERAGE WORKFLOW
When an assigned volunteer cancels:
1. Inspect the affected route.
2. Find approved backups.
3. Contact candidates in returned policy order until one accepts.
4. Assign only a volunteer whose acceptance is verified by the tool.
5. If all candidates decline/fail, create a coverage-gap issue.
6. Stop when coverage is restored or human action is required.

NO-ANSWER WORKFLOW
When the app says the volunteer has completed the approved no-answer protocol:
1. Retrieve the configured no_answer protocol.
2. Record outcome no_answer with the factual note provided by the app.
3. Create the policy-driven protocol issue.
4. Do not invent additional wellness or emergency action.

RECONCILIATION WORKFLOW
When asked to close/reconcile a route, call reconcile_route. A route is not cleanly complete
while any scheduled stop lacks an outcome or any issue remains open.
""".strip()

COVERAGE_TOOLS = [
    get_route,
    find_backup_volunteers,
    contact_backup,
    assign_volunteer,
    create_coverage_gap_issue,
]

NO_ANSWER_TOOLS = [
    get_protocol,
    record_delivery_outcome,
    create_protocol_issue,
]

RECONCILE_TOOLS = [reconcile_route]

TOOLSETS = {
    "coverage": COVERAGE_TOOLS,
    "no_answer": NO_ANSWER_TOOLS,
    "reconcile": RECONCILE_TOOLS,
    "all": COVERAGE_TOOLS + NO_ANSWER_TOOLS + RECONCILE_TOOLS,
}


@dataclass(frozen=True)
class AgentRuntimeStatus:
    requested: bool
    installed: bool
    enabled: bool
    provider: str
    model_id: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "requested": self.requested,
            "installed": self.installed,
            "enabled": self.enabled,
            "provider": self.provider,
            "model_id": self.model_id,
            "mode": "strands" if self.enabled else "fallback",
        }


RUNTIME = AgentRuntimeStatus(
    requested=USE_STRANDS,
    installed=STRANDS_INSTALLED,
    enabled=USE_STRANDS and STRANDS_INSTALLED,
    provider=MODEL_PROVIDER,
    model_id=MODEL_ID,
)


def build_model() -> Any:
    """Create the configured Strands model provider without changing Porchlight tools/workflows."""
    if MODEL_PROVIDER == "gemini":
        if not GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY is not set")
        try:
            from strands.models.gemini import GeminiModel
        except ImportError as exc:
            raise RuntimeError(
                "Gemini support is not installed. Run: pip install 'strands-agents[gemini]'"
            ) from exc
        return GeminiModel(
            client_args={"api_key": GEMINI_API_KEY},
            model_id=MODEL_ID,
            params={"temperature": 0.0, "max_output_tokens": 1024},
        )

    if MODEL_PROVIDER == "bedrock":
        # A model-id string tells Strands to use its Bedrock provider.
        return MODEL_ID

    raise RuntimeError(f"Unsupported PORCHLIGHT_MODEL_PROVIDER: {MODEL_PROVIDER}")


def build_agent(toolset: str = "all") -> Any:
    if not STRANDS_INSTALLED or Agent is None:
        raise RuntimeError("Strands is not installed. Run: pip install -r requirements.txt")
    tools = TOOLSETS.get(toolset)
    if tools is None:
        raise RuntimeError(f"Unknown Porchlight toolset: {toolset}")
    return Agent(
        model=build_model(),
        system_prompt=SYSTEM_PROMPT,
        tools=tools,
        name="Porchlight Operations Agent",
        description="Coordinates community meal-delivery logistics within human-defined policy.",
        callback_handler=None,
        trace_attributes={"app.name": "porchlight", "app.track": "good-neighbor", "app.toolset": toolset},
    )


def run_agent(prompt: str, workflow: str, route_id: str = "r3", toolset: str = "all") -> str:
    """Run a fresh Strands agent for one bounded workflow with auditable telemetry."""
    if not RUNTIME.enabled:
        raise RuntimeError("Strands live mode is not enabled")

    run = start_agent_run(route_id, workflow, RUNTIME.provider, RUNTIME.model_id, toolset)
    add_activity(route_id, "strands_started", f"Porchlight started workflow: {workflow}.", "info", actor="strands")
    try:
        result = build_agent(toolset=toolset)(prompt)
        finish_agent_run(run["id"], "succeeded", result_summary=str(result))
        add_activity(route_id, "strands_completed", f"Porchlight completed workflow: {workflow}.", "resolved", actor="strands")
        return str(result)
    except Exception as exc:
        finish_agent_run(run["id"], "failed", error=f"{type(exc).__name__}: {exc}")
        add_activity(route_id, "strands_error", f"Porchlight workflow failed: {type(exc).__name__}: {exc}", "attention", True, actor="strands")
        raise


async def run_agent_async(prompt: str, workflow: str, route_id: str = "r3", toolset: str = "all") -> str:
    """Run Strands on FastAPI's long-lived asyncio loop with auditable telemetry."""
    if not RUNTIME.enabled:
        raise RuntimeError("Strands live mode is not enabled")

    run = start_agent_run(route_id, workflow, RUNTIME.provider, RUNTIME.model_id, toolset)
    add_activity(route_id, "strands_started", f"Porchlight started workflow: {workflow}.", "info", actor="strands")
    try:
        agent = build_agent(toolset=toolset)
        result = await agent.invoke_async(prompt)
        finish_agent_run(run["id"], "succeeded", result_summary=str(result))
        add_activity(route_id, "strands_completed", f"Porchlight completed workflow: {workflow}.", "resolved", actor="strands")
        return str(result)
    except Exception as exc:
        finish_agent_run(run["id"], "failed", error=f"{type(exc).__name__}: {exc}")
        add_activity(route_id, "strands_error", f"Porchlight workflow failed: {type(exc).__name__}: {exc}", "attention", True, actor="strands")
        raise

def verify_coverage_postcondition(route_id: str = "r3") -> tuple[bool, str]:
    route = STATE["routes"].get(route_id)
    if not route:
        return False, "route_not_found"
    volunteer_id = route.get("volunteer_id")
    if route.get("status") in {"confirmed", "covered"} and volunteer_id != "v1":
        accepted = STATE["backup_outreach"].get(f"{route_id}:{volunteer_id}") == "accept"
        if accepted:
            return True, "coverage_restored"
    has_issue = any(
        issue["route_id"] == route_id and issue["type"] == "coverage_gap" and issue["status"] == "open"
        for issue in STATE["issues"]
    )
    if has_issue:
        return True, "human_escalation_created"
    return False, "agent_finished_without_valid_resolution"
