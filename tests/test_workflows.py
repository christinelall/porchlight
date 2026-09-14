from __future__ import annotations

import unittest

from backend.store import STATE, reset_state, route_summary
from backend.tools import (
    find_backup_volunteers,
    contact_backup,
    assign_volunteer,
    record_delivery_outcome,
    create_protocol_issue,
    reconcile_route,
)


class PorchlightWorkflowTests(unittest.TestCase):
    def setUp(self):
        reset_state()

    def test_backup_cannot_be_assigned_without_acceptance(self):
        result = assign_volunteer("r3", "v2")
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], "acceptance_not_verified")

    def test_coverage_flow_requires_contact_then_acceptance(self):
        STATE["volunteers"]["v1"]["available"] = False
        STATE["routes"]["r3"]["status"] = "uncovered"
        candidates = find_backup_volunteers("r3")["candidates"]
        self.assertEqual(candidates[0]["id"], "v2")
        response = contact_backup("v2", "r3")
        self.assertEqual(response["response"], "accept")
        assignment = assign_volunteer("r3", "v2")
        self.assertTrue(assignment["ok"])
        self.assertEqual(STATE["routes"]["r3"]["volunteer_id"], "v2")
        self.assertEqual(STATE["routes"]["r3"]["status"], "confirmed")
        self.assertEqual(STATE["communications"][0]["status"], "accept")

    def test_no_answer_issue_requires_human_protocol_completion(self):
        record_delivery_outcome("r3", "s3", "no_answer", "No response after approved attempts.")
        issue = create_protocol_issue("r3", "s3", "no_answer")
        self.assertFalse(issue["ok"])
        self.assertEqual(issue["error"], "human_protocol_completion_not_verified")

        STATE["protocol_completions"]["r3:s3:no_answer"] = True
        issue = create_protocol_issue("r3", "s3", "no_answer")
        self.assertTrue(issue["ok"])
        self.assertEqual(issue["issue"]["severity"], "medium")

    def test_reconcile_blocks_open_issue_then_closes_after_ack(self):
        for sid in ["s1", "s2", "s3", "s4", "s5"]:
            outcome = "no_answer" if sid == "s3" else "delivered"
            record_delivery_outcome("r3", sid, outcome)
        STATE["protocol_completions"]["r3:s3:no_answer"] = True
        issue = create_protocol_issue("r3", "s3", "no_answer")["issue"]
        blocked = reconcile_route("r3")
        self.assertFalse(blocked["clean"])
        issue["status"] = "acknowledged"
        clean = reconcile_route("r3")
        self.assertTrue(clean["clean"])
        self.assertEqual(STATE["routes"]["r3"]["status"], "complete")

    def test_route_summary_tracks_real_progress(self):
        record_delivery_outcome("r3", "s1", "delivered")
        record_delivery_outcome("r3", "s2", "delivered")
        summary = route_summary("r3")
        self.assertEqual(summary["delivered"], 2)
        self.assertEqual(summary["pending"], 3)
        self.assertEqual(summary["percent"], 40)

    def test_reset_restores_sarah_availability(self):
        STATE["volunteers"]["v1"]["available"] = False
        reset_state()
        self.assertTrue(STATE["volunteers"]["v1"]["available"])
        self.assertEqual(STATE["routes"]["r3"]["volunteer_id"], "v1")


if __name__ == "__main__":
    unittest.main()

class PorchlightProductHardeningTests(unittest.TestCase):
    def setUp(self):
        reset_state()

    def test_route_lifecycle_is_separate_from_attention_overlay(self):
        summary = route_summary("r5")
        self.assertEqual(summary["lifecycle"], "confirmed")
        self.assertEqual(summary["attention"], "at_risk")

    def test_meal_issue_requires_protocol_completion_and_human_review(self):
        from backend.store import persist_state
        from backend.tools import create_protocol_issue

        protocol = STATE["protocols"]["meal_issue"]
        self.assertTrue(protocol["requires_acknowledgement"])
        record_delivery_outcome("r3", "s1", "meal_issue", "Meal bag was torn on arrival.")
        blocked = create_protocol_issue("r3", "s1", "meal_issue")
        self.assertFalse(blocked["ok"])
        STATE["protocol_completions"]["r3:s1:meal_issue"] = True
        persist_state()
        issue = create_protocol_issue("r3", "s1", "meal_issue")
        self.assertTrue(issue["ok"])
        self.assertEqual(issue["issue"]["severity"], "medium")

    def test_low_risk_access_protocol_can_finish_without_open_issue(self):
        STATE["protocol_completions"]["r3:s1:could_not_access"] = True
        record_delivery_outcome("r3", "s1", "could_not_access", "Gate was locked; no approved access route available.")
        summary = route_summary("r3")
        self.assertEqual(summary["exceptions"], 1)
        self.assertEqual(summary["open_issues"], 0)

class PorchlightV13Tests(unittest.TestCase):
    def setUp(self):
        reset_state()

    def test_backup_retry_scenario_decline_then_accept(self):
        from backend.store import apply_demo_scenario
        apply_demo_scenario("backup_retry")
        STATE["volunteers"]["v6"]["available"] = False
        STATE["routes"]["r5"]["status"] = "uncovered"
        candidates = find_backup_volunteers("r5")["candidates"]
        self.assertEqual([x["id"] for x in candidates[:2]], ["v8", "v9"])
        self.assertEqual(contact_backup("v8", "r5")["response"], "decline")
        self.assertEqual(contact_backup("v9", "r5")["response"], "accept")
        self.assertTrue(assign_volunteer("r5", "v9")["ok"])
        self.assertEqual(STATE["routes"]["r5"]["volunteer_id"], "v9")

    def test_coverage_gap_scenario_all_decline(self):
        from backend.store import apply_demo_scenario
        from backend.tools import create_coverage_gap_issue
        apply_demo_scenario("coverage_gap")
        STATE["volunteers"]["v6"]["available"] = False
        STATE["routes"]["r5"]["status"] = "uncovered"
        candidates = find_backup_volunteers("r5")["candidates"]
        responses = [contact_backup(x["id"], "r5")["response"] for x in candidates]
        self.assertTrue(responses)
        self.assertTrue(all(x == "decline" for x in responses))
        issue = create_coverage_gap_issue("r5")
        self.assertTrue(issue["ok"])
        self.assertEqual(issue["issue"]["severity"], "high")

    def test_agent_run_telemetry_tracks_tool_evidence(self):
        from backend.store import start_agent_run, record_agent_tool, finish_agent_run, update_agent_postcondition, agent_metrics
        run = start_agent_run("r3", "restore route coverage", "test", "test-model", "coverage")
        record_agent_tool("r3", "find_backup_volunteers", "Found 2 approved backups")
        record_agent_tool("r3", "contact_backup", "Marcus accepted")
        finish_agent_run(run["id"], "succeeded", result_summary="Coverage restored")
        update_agent_postcondition("r3", "restore route coverage", "coverage_restored", True)
        latest = STATE["agent_runs"][0]
        self.assertEqual(len(latest["tool_events"]), 2)
        self.assertTrue(latest["postcondition_verified"])
        metrics = agent_metrics()
        self.assertEqual(metrics["workflows_total"], 1)
        self.assertEqual(metrics["tool_calls"], 2)
        self.assertEqual(metrics["verified_postconditions"], 1)

    def test_no_answer_scenario_places_mary_next(self):
        from backend.store import apply_demo_scenario, route_summary
        apply_demo_scenario("no_answer")
        self.assertEqual(STATE["stops"]["s1"]["outcome"], "delivered")
        self.assertEqual(STATE["stops"]["s2"]["outcome"], "delivered")
        self.assertIsNone(STATE["stops"]["s3"]["outcome"])
        self.assertEqual(route_summary("r3")["percent"], 40)
