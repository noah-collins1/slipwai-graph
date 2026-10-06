"""R11 (AC-S39-2, -5): the commands name each `drive-slice` delegate and bracket the full gate as the slice's `gate`
stage. R12 (AC-S39-12) joins this module: what a project made before the slice gets, and the fragment that says so."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from support import FactoryTestCase
from test_benchmark import bench, clean
from test_migrate import migrate
from test_replay import git, newer_factory

from slipwai.assets import ROOT

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


BEFORE = "525399b"  # the commit S39 was cut from: the last factory whose benchmark knew neither elapsed nor waiting
FRAGMENT = ROOT / "changelog.d/benchmark-elapsed.md"


def squashed(text: str) -> str:
    return " ".join(text.split())


def catch_up_paragraphs(text: str) -> list[str]:
    return [block for block in text.split("\n\n") if block.startswith("**Catch-up.**")]


def old_factory(directory: str) -> Path:
    old = Path(directory) / "factory-before"
    old.mkdir()
    archive = subprocess.run(["git", "archive", BEFORE], cwd=ROOT, capture_output=True, check=True, timeout=120).stdout
    subprocess.run(["tar", "-x", "-C", str(old)], input=archive, check=True, timeout=120)
    return old


def old_entry(stage: str, started: str, ended: str, seconds: int, **signals: object) -> dict:
    """An entry in the shape the factory at `BEFORE` wrote: no moments, no attribution, a usage that read nothing."""
    return {"stage": stage, "started": started, "ended": ended, "seconds": seconds, "signals": signals,
            "usage": {"source": None, "reason": "no harness installed"}, "ran": [], "agents": None, "delegated": False}


def own_records(repo: Path) -> None:
    """What a project wrote before S39: a slice record with ended entries, and the register row that calls it done."""
    slice_ = repo / "specs/shop/slices/S1"
    slice_.mkdir(parents=True)
    record = {"feature": "shop", "slice": "S1", "from": "0" * 40,
              "stages": [old_entry("implement", "2026-10-01T09:00:00Z", "2026-10-01T09:10:00Z", 600, verify_failures=1),
                         old_entry("mutation", "2026-10-01T09:10:00Z", "2026-10-01T09:12:00Z", 120,
                                   mutation_score="90%")]}
    (slice_ / "benchmark.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    (repo / "specs/shop/slices/README.md").write_text(
        "# Slices\n\n| Slice | Date | Demo |\n|---|---|---|\n| `S1` | 2026-10-01 | x |\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "-c", "user.name=t", "-c", "user.email=t@local", "commit", "-q", "-m", "records")


def make(repo: Path, target: str) -> subprocess.CompletedProcess:
    return subprocess.run(["make", target], cwd=repo, env=clean(HOME=str(repo / ".home-none")), text=True,
                          capture_output=True, timeout=120)


class AProjectMadeBeforeReadsItsOldRecordsAfterMigrateTest(FactoryTestCase):
    def test_e1_migrate_brings_the_modules_and_make_benchmark_reads_the_old_records(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            old = old_factory(directory)
            subprocess.run([str(old / "slipwai"), "generate", "product", "--profile", "event-modelling", "--backend",
                            "typescript", "--frontend", "none", "--output", directory, "--skip-checks"],
                           check=True, capture_output=True, timeout=300)
            repo = Path(directory) / "product"
            for name in ("measures.py", "attribution.py"):
                self.assertFalse((repo / "scripts/agents" / name).exists(), f"{name}: the factory as it was had none")
            (repo / ".specify").mkdir(exist_ok=True)
            (repo / ".specify/integration.json").write_text(json.dumps({"installed_integrations": ["claude"]}))
            own_records(repo)
            before = make(repo, "check-benchmark")
            self.assertEqual(before.returncode, 0, before.stdout + before.stderr)
            factory = newer_factory(Path(directory), "\n## A section a newer factory added\n")
            shutil.copytree(ROOT / "changelog.d", factory / "changelog.d")

            result = migrate(repo, factory)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            for name in ("measures.py", "attribution.py"):
                self.assertTrue((repo / "scripts/agents" / name).is_file(), f"{name} arrives with migrate")
            shown = make(repo, "benchmark")
            self.assertEqual(shown.returncode, 0, shown.stdout + shown.stderr)
            self.assertIn("stage time", shown.stdout)
            self.assertIn("unattributed", shown.stdout, "the waiting table, by cause")
            after = make(repo, "check-benchmark")
            self.assertEqual(after.returncode, 0, after.stdout + after.stderr)
            self.assertEqual(after.stdout, before.stdout, "check-benchmark prints nothing it did not print before")
            self.assertEqual(after.stderr, before.stderr)


class TheFragmentIsMinorAndItsCatchUpStandsAloneTest(FactoryTestCase):
    def setUp(self) -> None:
        self.text = FRAGMENT.read_text(encoding="utf-8")
        paragraphs = catch_up_paragraphs(self.text)
        self.assertEqual(len(paragraphs), 1, "exactly one paragraph begins **Catch-up.**")
        self.note = squashed(paragraphs[0])

    def test_e2_the_shape_is_the_level_a_blank_line_and_a_bold_one_sentence_lead(self) -> None:
        lines = self.text.splitlines()
        self.assertEqual(lines[0], "MINOR")
        self.assertEqual(lines[1], "")
        lead = self.text.split("\n\n")[1]
        self.assertTrue(lead.startswith("**") and "make benchmark" in lead)

    def test_e2_the_catch_up_names_the_renames_the_json_key_the_modules_and_the_gate(self) -> None:
        for words in ("`wall` → `stage time`", "`rework` column → `re-entered`", "{seconds, tokens}", "`reentered`",
                      "`scripts/agents/measures.py`", "`scripts/agents/attribution.py`", "`gate`",
                      "`drive-slice <id>`", "no record is rewritten",
                      "nothing"):
            self.assertIn(words, self.note)

    def test_e2_the_catch_up_stands_alone(self) -> None:
        for reference in ("T0", "AC-S39", "D159", "above", "the page", "R12"):
            self.assertNotIn(reference, self.note)
