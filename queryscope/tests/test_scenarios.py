import json
import unittest
from pathlib import Path

from queryscope import estimate

CASES = Path(__file__).resolve().parents[1] / "fixtures"


class ScenarioTests(unittest.TestCase):
    def test_contract_cases(self):
        count = 0
        for file in sorted(CASES.glob("*.jsonl")):
            for line in file.read_text(encoding="utf-8").splitlines():
                case = json.loads(line)
                count += 1
                with self.subTest(case=case["id"]):
                    actual = estimate(case['input'])
                    self.assertEqual(actual, case["expected"])
        self.assertGreater(count, 0)
