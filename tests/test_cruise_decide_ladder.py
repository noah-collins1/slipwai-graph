"""`decide` is a ladder of five modes (S27 R9): `--set` moves up one rung at a time, anything may step down, and
an iteration never sets it; `cruise.py mode` (R10) records a person's move in the feature's log, or parks on a hand
edit that skipped a rung. The script runs as a subprocess in a scratch project holding `scripts/agents/` copied
from the toolkit, the way a generated project holds it; the mode verb's scratch is also a git repository."""
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

    def test_several_assignments_in_one_call_are_judged_against_the_value_the_file_held(self) -> None:
        project = scratch_project("recommended-first")
        before = self.config(project).read_bytes()
        result = cruise(project, "--set", "decide=provisional-shadow", "decide=provisional-advisory",
                        "decide=provisional")
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("set `provisional-shadow` first", result.stderr)
        self.assertEqual(self.config(project).read_bytes(), before, "a refusal wrote the file")
        self.assertEqual(result.stdout, "")

    def test_one_step_stated_twice_in_one_call_is_still_one_step(self) -> None:
        project = scratch_project("recommended-first")
        result = cruise(project, "--set", "decide=provisional-shadow", "decide=provisional-shadow")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(self.config(project).read_text(encoding="utf-8"))["decide"],
                         "provisional-shadow")

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


ENTRY = """## D{n} — decide moved from {a} to {b}
- **Stage:** iteration start · **Slice:** none · **When:** 2026-10-07T09:00:00Z · **Iteration:** 1
- **Scope:** global
- **Question:** which `decide` mode does this run work under?
- **Options:** recommended-first · skipper-always · provisional-shadow · provisional-advisory · provisional
- **Decision:** {b}, as a person set it in `.specify/cruise.json` (commit abc1234)
- **Why:** a person changed the setting through /cruise-settings; the run records the move and never sets it (D62)
- **Decided by:** human
- **Confidence:** high · **Would reverse if:** a person sets `decide` again
- **Written to:** `.specify/cruise.json`
- **Status:** standing
"""
FACTS = ("contract=no", "schema=no", "auth=no", "customer_visible=no", "export=no", "ci_workflow=no",
         "migrate_file=no", "behind_flag=no-code", "flag_default=no", "rollback_complexity=trivial")


def git(project: Path, *arguments: str) -> str:
    done = subprocess.run(["git", *arguments], cwd=project, text=True, capture_output=True, encoding="utf-8")
    assert done.returncode == 0, done.stderr
    return done.stdout.strip()


def mode_project(recorded: str | None, decide: str, commit: bool = True) -> Path:
    """A git repository holding the runner, the gate, `.specify/cruise.json` at `decide` (committed unless told
    otherwise) and `specs/f/decisions.md` whose only entry, D1, moved `decide` to `recorded` (no log when None)."""
    project = scratch_project(decide)
    (project / "scripts").mkdir(exist_ok=True)
    for name in ("check-decisions.py", "reversibility.py"):
        shutil.copy(TOOLKIT / "scripts" / name, project / "scripts" / name)
    if recorded is not None:
        (project / "specs/f").mkdir(parents=True)
        (project / "specs/f/decisions.md").write_text(ENTRY.format(n=1, a="unrecorded", b=recorded), encoding="utf-8")
    git(project, "init", "-q")
    git(project, "config", "user.name", "Test")
    git(project, "config", "user.email", "test@example.invalid")
    if commit:
        git(project, "add", "-A")
        git(project, "commit", "-q", "-m", "scratch")
    return project


class DecideModeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.addCleanup(shutil.rmtree, SCRATCH, True)

    def test_a_setting_that_matches_the_last_mode_entry_is_said_and_nothing_printed_to_append(self) -> None:
        project = mode_project("provisional-shadow", "provisional-shadow")
        result = cruise(project, "mode")
        self.assertEqual((result.returncode, result.stdout),
                         (0, "cruise: decide is provisional-shadow, as D1 recorded\n"))

    def test_a_person_step_up_prints_the_entry_citing_the_commit_and_it_passes_the_gate(self) -> None:
        project = mode_project("provisional-shadow", "provisional-shadow")
        (project / ".specify/cruise.json").write_text(json.dumps({**BASE, "decide": "provisional-advisory"}) + "\n",
                                                      encoding="utf-8")
        git(project, "commit", "-q", "-am", "advisory")
        result = cruise(project, "mode", iteration="5")
        self.assertEqual(result.returncode, 0, result.stderr)
        entry = result.stdout
        self.assertTrue(entry.startswith("## D2 — decide moved from provisional-shadow to provisional-advisory\n"))
        self.assertIn(f"(commit {git(project, 'log', '-1', '--format=%h', '--', '.specify/cruise.json')})", entry)
        self.assertIn("**Iteration:** 5", entry)
        self.assertIn("- **Decided by:** human", entry)
        scored = subprocess.run([sys.executable, "-B", "scripts/reversibility.py", "--scope", "global", *FACTS],
                                cwd=project, text=True, capture_output=True, encoding="utf-8")
        line = scored.stdout.strip()
        self.assertTrue(line.startswith("- **Reversibility:**"), scored.stderr)
        log = project / "specs/f/decisions.md"
        scored_entry = entry.replace("- **Written to:**", line + "\n- **Written to:**")
        log.write_text(log.read_text(encoding="utf-8") + "\n" + scored_entry, encoding="utf-8")
        gate = subprocess.run([sys.executable, "-B", "scripts/check-decisions.py"], cwd=project, text=True,
                              capture_output=True, encoding="utf-8")
        self.assertEqual(gate.returncode, 0, gate.stdout + gate.stderr)

    def test_a_change_not_yet_committed_is_cited_as_uncommitted(self) -> None:
        project = mode_project("provisional-shadow", "provisional-shadow")
        (project / ".specify/cruise.json").write_text(json.dumps({**BASE, "decide": "provisional-advisory"}) + "\n",
                                                      encoding="utf-8")
        result = cruise(project, "mode")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(result.stdout, r"\(uncommitted at \d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ\)")

    def test_the_first_entry_moves_from_unrecorded(self) -> None:
        project = mode_project(None, "recommended-first")
        result = cruise(project, "mode")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(result.stdout.startswith("## D1 — decide moved from unrecorded to recommended-first\n"))
        decision, why = (self.line(result.stdout, name) for name in ("Decision", "Why"))
        self.assertIn("recorded as found", decision)
        self.assertIn("no earlier mode entry", decision)
        self.assertRegex(decision, r"\((commit [0-9a-f]+|uncommitted at [^)]+)\)")
        self.assertIn("records the mode as found", why)
        self.assertIn("no earlier mode entry", why)
        for text in (decision, why):
            self.assertNotIn("a person", text)
            self.assertNotIn("changed", text)

    @staticmethod
    def line(entry: str, name: str) -> str:
        return next(row for row in entry.splitlines() if row.startswith(f"- **{name}:**"))

    def test_each_case_the_mode_prints_gets_a_why_true_of_that_case(self) -> None:
        for recorded, decide, word in (("provisional-shadow", "provisional-advisory", "raised"),
                                       ("provisional", "recommended-first", "back down"),
                                       ("recommended-first", "skipper-always", "sideways")):
            project = mode_project(recorded, decide)
            why = self.line(cruise(project, "mode").stdout, "Why")
            self.assertIn("a person", why)
            self.assertIn(word, why)
            for other in {"raised", "back down", "sideways"} - {word}:
                self.assertNotIn(other, why)

    def test_a_feature_naming_no_directory_under_specs_is_exit_2_naming_it(self) -> None:
        project = mode_project("provisional-shadow", "provisional-shadow")
        result = cruise(project, "mode", "--feature", "nope")
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertEqual(result.stderr.strip().splitlines(), ["cruise: no specs/nope/ directory to name a feature"])
        self.assertEqual(result.stdout, "")

    def test_a_named_feature_with_no_log_yet_still_prints_its_first_entry(self) -> None:
        project = mode_project(None, "recommended-first")
        (project / "specs/g").mkdir(parents=True)
        result = cruise(project, "mode", "--feature", "g")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(result.stdout.startswith("## D1 — decide moved from unrecorded to recommended-first\n"))

    def test_a_hand_edit_that_skips_a_rung_parks_with_nothing_to_append(self) -> None:
        project = mode_project("recommended-first", "provisional")
        result = cruise(project, "mode")
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertEqual(result.stdout.strip(), "cruise: parked: decide=provisional skips provisional-shadow; "
                                                "set it through /cruise-settings")

    def test_a_step_back_is_an_entry(self) -> None:
        project = mode_project("provisional", "recommended-first")
        result = cruise(project, "mode")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(result.stdout.startswith("## D2 — decide moved from provisional to recommended-first\n"))


    def second_feature(self, project: Path, recorded: str | None, when: str = "2026-10-07T09:00:00Z") -> Path:
        log = project / "specs/b/decisions.md"
        log.parent.mkdir(parents=True)
        if recorded is not None:
            log.write_text(ENTRY.format(n=1, a="unrecorded", b=recorded).replace("2026-10-07T09:00:00Z", when),
                           encoding="utf-8")
        return log

    def test_a_first_reading_two_rungs_up_with_no_mode_entry_anywhere_parks(self) -> None:
        for decide, step in (("provisional-advisory", "provisional-shadow"), ("provisional", "provisional-shadow")):
            project = mode_project(None, decide)
            result = cruise(project, "mode")
            self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
            self.assertIn(f"skips {step}", result.stdout)

    def test_a_first_reading_at_shadow_or_below_is_recorded_as_found(self) -> None:
        for decide in ("recommended-first", "provisional-shadow"):
            result = cruise(mode_project(None, decide), "mode")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(result.stdout.startswith(f"## D1 — decide moved from unrecorded to {decide}\n"))
            self.assertIn("- **Decided by:** human", result.stdout)

    def test_another_features_mode_entry_is_the_baseline_and_the_equal_line_names_its_log(self) -> None:
        project = mode_project("provisional", "provisional")
        self.second_feature(project, None)
        result = cruise(project, "mode", "--feature", "b")
        self.assertEqual((result.returncode, result.stdout),
                         (0, "cruise: decide is provisional, as D1 in specs/f/decisions.md recorded\n"))

    def test_another_features_mode_entry_makes_a_step_back_an_entry_from_that_mode(self) -> None:
        project = mode_project("provisional", "recommended-first")
        self.second_feature(project, None)
        result = cruise(project, "mode", "--feature", "b")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(result.stdout.startswith("## D1 — decide moved from provisional to recommended-first\n"))

    def test_the_latest_when_across_logs_wins_not_the_log_order(self) -> None:
        project = mode_project("provisional-shadow", "provisional-advisory")
        self.second_feature(project, "recommended-first", when="2026-10-06T09:00:00Z")
        result = cruise(project, "mode", "--feature", "b")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(result.stdout.startswith(
            "## D2 — decide moved from provisional-shadow to provisional-advisory\n"))


if __name__ == "__main__":
    unittest.main()
