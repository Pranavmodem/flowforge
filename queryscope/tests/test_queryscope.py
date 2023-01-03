import json
import unittest
from pathlib import Path

from queryscope import estimate

EXAMPLE = Path(__file__).parents[1] / "examples" / "workload.json"


class WorkloadTests(unittest.TestCase):
    def setUp(self):
        self.spec = json.loads(EXAMPLE.read_text())

    def test_models_retry_cost_and_freshness(self):
        report = estimate(self.spec)
        self.assertEqual(report["sql_cost"], "378.00")
        self.assertEqual(report["cluster_cost"], "324.00")
        self.assertEqual(report["lower_cost"], "cluster")
        self.assertTrue(report["within_freshness_budget"])

    def test_partition_pruning_and_latency_change_decisions(self):
        self.spec.update(scan_tib=0.25, cadence_minutes=20)
        report = estimate(self.spec)
        self.assertEqual(report["lower_cost"], "sql")
        self.assertFalse(report["within_freshness_budget"])

    def test_rejects_impossible_fraction(self):
        self.spec["retry_fraction"] = 1.1
        with self.assertRaisesRegex(ValueError, "retry fractions"):
            estimate(self.spec)
