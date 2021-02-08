import json
import unittest
from pathlib import Path

from flowforge import preview, seal

CASES = Path(__file__).parent.parent / "fixtures"


class WorkflowScenarioTests(unittest.TestCase):
    def test_workflow_contract(self):
        count = 0
        for file in sorted(CASES.glob("*.jsonl")):
            for line in file.read_text(encoding="utf-8").splitlines():
                case = json.loads(line)
                count += 1
                with self.subTest(case=case["id"]):
                    spec = {"tasks": case["tasks"]}
                    if "error" in case:
                        with self.assertRaisesRegex(ValueError, case["error"]):
                            preview(seal(spec), case["failures"])
                        continue

                    actual = preview(seal(spec), case["failures"])
                    positions = {name: index for index, name in enumerate(actual["order"])}
                    self.assertEqual(set(positions), set(case["expected"]))
                    self.assertEqual(actual["status"], case["expected"])
                    for task in case["tasks"]:
                        for dependency in task["needs"]:
                            self.assertLess(positions[dependency], positions[task["name"]])
                    flipped = {
                        "tasks": [
                            {"name": task["name"], "needs": task["needs"][::-1]}
                            for task in case["tasks"][::-1]
                        ]
                    }
                    self.assertEqual(actual, preview(seal(flipped), case["failures"]))
        self.assertGreater(count, 0)
