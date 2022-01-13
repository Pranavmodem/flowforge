import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from dataforge import LEDGER, sync

CASES = Path(__file__).parent.parent / "fixtures"


def write_inputs(root, inputs):
    for filename, value in inputs.items():
        path = root / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")


class TransferScenarioTests(unittest.TestCase):
    def test_transfer_contract(self):
        count = 0
        for file in sorted(CASES.glob("*.jsonl")):
            for line in file.read_text(encoding="utf-8").splitlines():
                case = json.loads(line)
                count += 1
                with self.subTest(case=case["id"]), tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    source, target = root / "source", root / "output"
                    write_inputs(source, case["source"])
                    write_inputs(target, case["preexisting"])
                    report = sync(source, target, case["tenants"], dry_run=True)
                    for name, counts in case["expected"].items():
                        if counts is None:
                            self.assertEqual(report[name]["status"], "failed")
                        else:
                            self.assertEqual(report[name]["copied"], 0)
                            self.assertEqual(
                                (report[name]["planned"], report[name]["unchanged"]),
                                tuple(counts),
                            )
                    observed = {
                        path.relative_to(target).as_posix(): path.read_text(encoding="utf-8")
                        for path in target.rglob("*") if path.is_file()
                    }
                    self.assertEqual(observed, case["preexisting"])

                    report = sync(source, target, case["tenants"])
                    again = sync(source, target, case["tenants"])
                    for name, counts in case["expected"].items():
                        if counts is None:
                            self.assertEqual(report[name]["status"], "failed")
                            self.assertFalse((target / name / LEDGER).exists())
                            continue
                        self.assertEqual(report[name]["copied"], counts[0])
                        self.assertEqual(again[name]["copied"], 0)
                        inventory = json.loads((target / name / LEDGER).read_text(encoding="utf-8"))
                        expected = {}
                        for filename, content in case["source"].items():
                            tenant, relative = filename.split("/", 1)
                            if tenant == name:
                                self.assertEqual((target / filename).read_text(encoding="utf-8"), content)
                                expected[relative] = hashlib.sha256(content.encode("utf-8")).hexdigest()
                        self.assertEqual(inventory, expected)
        self.assertGreater(count, 0)

    def test_rejects_linked_destination_without_writing_to_its_target(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, target, outside = root / "source", root / "output", root / "outside"
            write_inputs(source, {"alpha/input.csv": "new"})
            target.mkdir()
            outside.mkdir()
            (target / "alpha").symlink_to(outside, target_is_directory=True)
            self.assertEqual(sync(source, target, ["alpha"])["alpha"]["status"], "failed")
            self.assertEqual(list(outside.iterdir()), [])

    def test_rerun_repairs_output_and_updates_ledger(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, target = root / "source", root / "output"
            write_inputs(source, {"alpha/input.csv": "old", "alpha/removed.csv": "history"})
            self.assertEqual(sync(source, target, ["alpha"])["alpha"]["copied"], 2)
            write_inputs(source, {"alpha/input.csv": "new"})
            (source / "alpha" / "removed.csv").unlink()
            (target / "alpha" / "input.csv").write_text("corrupt", encoding="utf-8")
            self.assertEqual(sync(source, target, ["alpha"])["alpha"]["copied"], 1)
            self.assertEqual(sync(source, target, ["alpha"])["alpha"]["copied"], 0)
            self.assertEqual((target / "alpha" / "input.csv").read_text(encoding="utf-8"), "new")
            self.assertTrue((target / "alpha" / "removed.csv").is_file())
            ledger = json.loads((target / "alpha" / LEDGER).read_text(encoding="utf-8"))
            self.assertEqual(set(ledger), {"input.csv"})
