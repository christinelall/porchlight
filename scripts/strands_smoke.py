"""Run one real Strands coverage workflow and fail loudly if tools did not change state."""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Make the repository root importable even when this file is launched as a script.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Must be set before backend modules import configuration.
os.environ["PORCHLIGHT_USE_STRANDS"] = "1"

from backend.agent import RUNTIME, run_agent, verify_coverage_postcondition  # noqa: E402
from backend.store import STATE, add_activity, reset_state  # noqa: E402


def main() -> None:
    if not RUNTIME.installed:
        raise SystemExit("Strands is not installed. Run: pip install -r requirements.txt")

    reset_state()
    route = STATE["routes"]["r3"]
    STATE["volunteers"][route["volunteer_id"]]["available"] = False
    route["status"] = "uncovered"
    add_activity("r3", "volunteer_cancelled", "Sarah cancelled Route 3.", "attention", actor="human_event")

    print(f"Using provider: {RUNTIME.provider}")
    print(f"Using model: {RUNTIME.model_id}")
    result = run_agent(
        "Sarah has cancelled route r3. Restore coverage within policy using tools.",
        workflow="smoke-test coverage",
        toolset="coverage",
    )
    ok, resolution = verify_coverage_postcondition("r3")
    print("Agent result:", result)
    print("Postcondition:", ok, resolution)
    print("Assigned volunteer:", STATE["routes"]["r3"]["volunteer_id"])
    print("Recent activity:")
    for item in reversed(STATE["activity"][:8]):
        print(f" - [{item['actor']}] {item['event_type']}: {item['message']}")
    if not ok:
        raise SystemExit("FAIL: Strands finished without a valid operational resolution")
    print("PASS: real Strands workflow reached a valid operational resolution")


if __name__ == "__main__":
    main()
