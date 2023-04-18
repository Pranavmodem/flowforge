import json
import unittest
from pathlib import Path

from governance import deletion_plan, findings

CASES = Path(__file__).resolve().parents[1] / "fixtures"


class ScenarioTests(unittest.TestCase):
    def test_contract_cases(self):
        count = 0
        for file in sorted(CASES.glob("*.jsonl")):
            for line in file.read_text(encoding="utf-8").splitlines():
                case = json.loads(line)
                count += 1
                with self.subTest(case=case["id"]):
                    actual = (findings if case['mode'] == 'drift' else deletion_plan)(**case['input'])
                    self.assertEqual(actual, case["expected"])
        self.assertGreater(count, 0)
