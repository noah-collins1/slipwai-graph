"""R11 (AC-S39-2, -5): the commands name each `drive-slice` delegate and bracket the full gate as the slice's `gate`
stage. R12 (AC-S39-12) joins this module: what a project made before the slice gets, and the fragment that says so."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from support import FactoryTestCase
from test_benchmark import bench, clean

sys.dont_write_bytecode = True

SLICE = "specs/shop/slices/S1"


class TheLadderNamesTheSliceAndBracketsTheGateTest(FactoryTestCase):
    def test_e1_both_commands_say_a_drive_slice_delegate_is_described_by_its_slice(self) -> None:
        for profile in ("event-modelling", "standard"):
            with self.subTest(profile=profile), tempfile.TemporaryDirectory() as directory:
                repo = self.generate(directory, "named", profile, "typescript")
                drive = (repo / "commands/drive.md").read_text(encoding="utf-8")
                cruise = (repo / "commands/cruise.md").read_text(encoding="utf-8")
                for text in (drive, cruise):
                    self.assertIn("`drive-slice <id>`", text)
                    self.assertIn("the slice's whole id", " ".join(text.split()))
                self.assertIn("charge a delegate's requests to its slice", " ".join(drive.split()))

    def test_e2_what_each_stage_costs_names_the_gate_and_its_bracket(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "gated", "event-modelling", "typescript")
            drive = (repo / "commands/drive.md").read_text(encoding="utf-8")
            section = drive.split("## What each stage costs")[1].split("## Once inside the slice")[0]
            section = " ".join(section.split())
            self.assertIn("python3 scripts/agents/benchmark.py start specs/<feature>/slices/<id> gate", section)
            self.assertIn("python3 scripts/agents/benchmark.py end specs/<feature>/slices/<id> gate", section)
            self.assertIn("| `gate` |", section)
            self.assertIn("elapsed", section)

    def test_e3_a_gate_entry_is_recorded_and_sorted_after_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "sorted", "event-modelling", "typescript")
            (repo / SLICE).mkdir(parents=True)
            env = clean(HOME=str(Path(directory) / "home"))
            for stage in ("gate", "skipper", "mutation"):  # out of order: what is read back is the ladder's
                self.assertEqual(bench(repo, "start", SLICE, stage, env=env).returncode, 0)
                ended = bench(repo, "end", SLICE, stage, env=env)
                self.assertEqual(ended.returncode, 0, ended.stderr)
            overview = bench(repo, "overview", "shop", env=env)
            self.assertEqual(overview.returncode, 0, overview.stderr)
            page = (repo / "specs/shop/benchmark.md").read_text(encoding="utf-8")
            self.assertLess(page.index("| mutation | "), page.index("| gate | "))
            self.assertLess(page.index("| gate | "), page.index("| skipper | "))
            script = (repo / "scripts/agents/benchmark.py").read_text(encoding="utf-8")
            self.assertIn('"mutation", "gate", "skipper"', " ".join(script.split()))
