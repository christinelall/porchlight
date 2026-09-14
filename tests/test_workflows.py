from __future__ import annotations

import unittest

from backend.store import STATE, reset_state
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
        for sid in ["s3", "s4", "s5"]:
            outcome = "no_answer" if sid == "s3" else "delivered"
            record_delivery_outcome("r3", sid, outcome)
        STATE["protocol_completions"]["r3:s3:no_answer"] = True
        issue = create_protocol_issue("r3", "s3", "no_answer")["issue"]
        blocked = reconcile_route("r3")
        self.assertFalse(blocked["clean"])
        issue["status"] = "acknowledged"
        clean = reconcile_route("r3")
        self.assertTrue(clean["clean"])

    def test_reset_restores_sarah_availability(self):
        STATE["volunteers"]["v1"]["available"] = False
        reset_state()
        self.assertTrue(STATE["volunteers"]["v1"]["available"])
        self.assertEqual(STATE["routes"]["r3"]["volunteer_id"], "v1")


if __name__ == "__main__":
    unittest.main()
