import unittest

from governance import deletion_plan, findings


class GovernanceTests(unittest.TestCase):
    def test_routes_owned_and_ambiguous_changes(self):
        result = findings(
            {"a": ["read"]}, {"a": ["read", "write"], "b": []},
            {"a": ["team"], "b": ["east", "west"]},
        )
        self.assertEqual([row["route"] for row in result], ["team", "manual-triage"])
        self.assertEqual(result[0]["new_roles"], ["write"])

    def test_missing_location_keeps_request_incomplete(self):
        result = deletion_plan(["events"], ["events", "archive"], {"events": "verified"})
        self.assertFalse(result["complete"])
        self.assertEqual(result["missing_locations"], ["archive"])
        self.assertEqual(result["actions"], [])

    def test_unverified_targets_have_stable_actions(self):
        result = deletion_plan(["a", "b"], ["a", "b"], {"b": "acknowledged"})
        self.assertEqual(result["actions"], [{"target": "a", "action": "queue"}, {"target": "b", "action": "verify"}])
        self.assertTrue(deletion_plan(["a"], ["a"], {"a": "verified"})["complete"])

    def test_unknown_ledger_target_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid ledger"):
            deletion_plan(["a"], ["a"], {"b": "verified"})
