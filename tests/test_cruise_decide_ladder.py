"""`decide` is a ladder of five modes (S27 R9): `--set` moves up one rung at a time, anything may step down, and
an iteration never sets it. The script runs as a subprocess in a scratch project holding `scripts/agents/` copied
from the toolkit, the way a generated project holds it."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True

TOOLKIT = Path(__file__).resolve().parent.parent / "assets/toolkit"
SCRATCH = Path("/tmp/s27-chainB/projects")
BASE = {"enabled": False, "decide": "recommended-first", "release": "flagged", "constitution": "ratify",
        "hand": "browser", "unblock": "bosun", "stuck_after": 3, "max_iterations": None, "max_hours": None,
        "poll_minutes": 10, "model": None}
LADDER = ("recommended-first", "provisional-shadow", "provisional-advisory", "provisional")


def scratch_project(decide: str) -> Path:
    SCRATCH.mkdir(parents=True, exist_ok=True)
    project = Path(tempfile.mkdtemp(dir=SCRATCH))
    shutil.copytree(TOOLKIT / "scripts/agents", project / "scripts/agents",
                    ignore=shutil.ignore_patterns("__pycache__"))
    (project / ".specify").mkdir()
    (project / ".specify/cruise.json").write_text(json.dumps({**BASE, "decide": decide}, indent=2) + "\n",
                                                  encoding="utf-8")
    return project


def cruise(project: Path, *arguments: str, iteration: str | None = None) -> subprocess.CompletedProcess[str]:
    environment = {k: v for k, v in os.environ.items() if not k.startswith("CRUISE_")}
    if iteration is not None:
        environment["CRUISE_ITERATION"] = iteration
    return subprocess.run([sys.executable, "-B", "scripts/agents/cruise.py", *arguments], cwd=project, text=True,
                          capture_output=True, stdin=subprocess.DEVNULL, env=environment)


class DecideLadderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.addCleanup(shutil.rmtree, SCRATCH, True)

    def config(self, project: Path) -> Path:
        return project / ".specify/cruise.json"

    def refused(self, start: str, target: str, next_rung: str) -> None:
        project = scratch_project(start)
        before = self.config(project).read_bytes()
        result = cruise(project, "--set", f"decide={target}")
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn(f"`decide` moves one mode at a time: set `{next_rung}` first", result.stderr)
        self.assertEqual(self.config(project).read_bytes(), before, "a refusal wrote the file")

    def test_a_jump_from_the_default_to_provisional_is_refused_naming_the_next_rung(self) -> None:
        self.refused("recommended-first", "provisional", "provisional-shadow")

    def test_a_jump_from_the_default_to_advisory_is_refused_naming_shadow(self) -> None:
        self.refused("recommended-first", "provisional-advisory", "provisional-shadow")

    def test_a_jump_from_shadow_to_provisional_is_refused_naming_advisory(self) -> None:
        self.refused("provisional-shadow", "provisional", "provisional-advisory")

    def test_the_ladder_is_climbed_one_written_rung_at_a_time(self) -> None:
        project = scratch_project("recommended-first")
        for rung in LADDER[1:]:
            result = cruise(project, "--set", f"decide={rung}")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(self.config(project).read_text(encoding="utf-8"))["decide"], rung)

    def test_any_step_down_is_written(self) -> None:
        for target in ("recommended-first", "provisional-shadow"):
            project = scratch_project("provisional")
            result = cruise(project, "--set", f"decide={target}")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(self.config(project).read_text(encoding="utf-8"))["decide"], target)

    def test_the_two_zero_rung_values_move_into_shadow_and_between_each_other(self) -> None:
        project = scratch_project("skipper-always")
        self.assertEqual(cruise(project, "--set", "decide=provisional-shadow").returncode, 0)
        project = scratch_project("skipper-always")
        self.assertEqual(cruise(project, "--set", "decide=recommended-first").returncode, 0)
        project = scratch_project("recommended-first")
        self.assertEqual(cruise(project, "--set", "decide=skipper-always").returncode, 0)

    def test_an_iteration_never_sets_decide_but_other_keys_still_write(self) -> None:
        project = scratch_project("provisional")
        before = self.config(project).read_bytes()
        result = cruise(project, "--set", "decide=recommended-first", iteration="4")
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("/cruise-settings", result.stderr)
        self.assertEqual(len(result.stderr.strip().splitlines()), 1)
        self.assertEqual(self.config(project).read_bytes(), before)
        other = cruise(project, "--set", "max_hours=2", iteration="4")
        self.assertEqual(other.returncode, 0, other.stderr)
        self.assertEqual(json.loads(self.config(project).read_text(encoding="utf-8"))["max_hours"], 2)

    def test_a_hand_edited_file_holding_provisional_passes_check(self) -> None:
        project = scratch_project("provisional")
        result = cruise(project, "--check")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("well-formed", result.stdout)


if __name__ == "__main__":
    unittest.main()
