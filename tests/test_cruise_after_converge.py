"""S27's after-converge gaps in `cruise.py`'s setting and its `mode` verb (T035, T037; D196, D202, D203): the skip
park names the entry it judged against and the way out, `When` is ordered as an instant, an unrecognised mode is the
bottom rung and says so, and `--set` counts an empty `CRUISE_ITERATION` as set. The scratch projects are the ones
`test_cruise_decide_ladder` builds."""
from __future__ import annotations

import json
import shutil
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True

from support import FactoryTestCase  # noqa: E402
from test_cruise_decide_ladder import (  # noqa: E402
    BASE,
    ENTRY,
    SCRATCH,
    DecideModeTest,
    cruise,
    git,
    mode_project,
    scratch_project,
)


class AfterConvergeModeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.addCleanup(shutil.rmtree, SCRATCH, True)

    def test_two_written_steps_between_iterations_park_naming_the_entry_and_the_way_out(self) -> None:
        project = mode_project("provisional-shadow", "provisional-shadow")
        for rung in ("provisional-advisory", "provisional"):
            self.assertEqual(cruise(project, "--set", f"decide={rung}").returncode, 0)
        result = cruise(project, "mode")
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertEqual(result.stdout.strip(), (
            "cruise: parked: decide=provisional is more than one rung above provisional-shadow (D1); set "
            "decide=provisional-advisory through /cruise-settings and let an iteration record it with `python3 "
            "scripts/agents/cruise.py mode`, or step back to provisional-shadow"))

    def test_the_way_out_is_taken_and_then_the_next_rung_is_recorded(self) -> None:
        project = mode_project("provisional-shadow", "provisional")
        self.assertEqual(cruise(project, "--set", "decide=provisional-advisory").returncode, 0)
        stepped = cruise(project, "mode")
        self.assertEqual(stepped.returncode, 0, stepped.stderr)
        self.assertTrue(stepped.stdout.startswith(
            "## D2 — decide moved from provisional-shadow to provisional-advisory\n"))

    def test_the_park_line_names_another_features_log_and_the_feature_flag(self) -> None:
        project = mode_project("recommended-first", "provisional")
        (project / "specs/g").mkdir(parents=True)
        result = cruise(project, "mode", "--feature", "g")
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertIn("one rung above recommended-first (D1 in specs/f/decisions.md); set decide=provisional-shadow",
                      result.stdout)
        self.assertIn("`python3 scripts/agents/cruise.py mode --feature g`", result.stdout)

    def test_a_when_with_an_offset_is_ordered_as_the_instant_it_is(self) -> None:
        project = mode_project("provisional-shadow", "provisional-advisory")
        other = project / "specs/other"
        other.mkdir(parents=True)
        (other / "decisions.md").write_text(
            ENTRY.format(n=1, a="unrecorded", b="recommended-first").replace(
                "2026-10-07T09:00:00Z", "2026-10-07T20:00:00-05:00"), encoding="utf-8")
        (project / "specs/f/decisions.md").write_text(
            ENTRY.format(n=1, a="unrecorded", b="provisional-shadow").replace(
                "2026-10-07T09:00:00Z", "2026-10-07T23:33:36Z"), encoding="utf-8")
        # -05:00 at 20:00 is 01:00Z the next day, later than 23:33Z: recommended-first is the baseline, so a hand
        # edit to advisory skips shadow.
        result = cruise(project, "mode", "--feature", "other")
        self.assertEqual(result.returncode, 3, result.stdout)
        self.assertIn("more than one rung above recommended-first", result.stdout)

    def test_a_when_that_does_not_parse_sorts_before_every_parsed_one(self) -> None:
        project = mode_project("provisional-shadow", "provisional-shadow")
        other = project / "specs/other"
        other.mkdir(parents=True)
        (other / "decisions.md").write_text(
            ENTRY.format(n=1, a="unrecorded", b="provisional").replace("2026-10-07T09:00:00Z", "tomorrow-ish"),
            encoding="utf-8")
        result = cruise(project, "mode", "--feature", "other")
        self.assertEqual((result.returncode, result.stdout),
                         (0, "cruise: decide is provisional-shadow, as D1 in specs/f/decisions.md recorded\n"))

    def test_an_unrecognised_recorded_mode_reads_as_the_bottom_rung_and_says_so(self) -> None:
        project = mode_project("bogus-mode", "provisional-shadow")
        result = cruise(project, "mode")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(result.stdout.startswith("## D2 — decide moved from bogus-mode to provisional-shadow\n"))
        self.assertIn("raised the setting up the ladder", result.stdout)
        self.assertEqual(result.stderr.strip(), (
            "cruise: D1 records the mode `bogus-mode`, which is not one of the five `decide` values; read as "
            "recommended-first"))

    def test_an_unrecognised_recorded_mode_still_parks_a_skip(self) -> None:
        result = cruise(mode_project("bogus-mode", "provisional"), "mode")
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertIn("set decide=provisional-shadow through /cruise-settings", result.stdout)
        self.assertIn("not one of the five", result.stderr)

    def test_an_unknown_current_value_is_the_bottom_rung_for_set_and_says_so(self) -> None:
        project = scratch_project("not-a-mode")
        before = (project / ".specify/cruise.json").read_bytes()
        result = cruise(project, "--set", "decide=provisional")
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("set `provisional-shadow` first", result.stderr)
        self.assertIn("`decide` in .specify/cruise.json is 'not-a-mode', which is not one of the five values; read "
                      "as recommended-first", result.stderr)
        self.assertEqual((project / ".specify/cruise.json").read_bytes(), before)
        stepped = cruise(project, "--set", "decide=provisional-shadow")
        self.assertEqual(stepped.returncode, 0, stepped.stderr)
        self.assertIn("not one of the five values", stepped.stderr)
        self.assertEqual(json.loads((project / ".specify/cruise.json").read_text(encoding="utf-8"))["decide"],
                         "provisional-shadow")

    def test_an_empty_iteration_variable_counts_as_set(self) -> None:
        project = scratch_project("recommended-first")
        before = (project / ".specify/cruise.json").read_bytes()
        result = cruise(project, "--set", "decide=skipper-always", iteration="")
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("/cruise-settings", result.stderr)
        self.assertEqual((project / ".specify/cruise.json").read_bytes(), before)
        other = cruise(project, "--set", "max_hours=2", iteration="")
        self.assertEqual(other.returncode, 0, other.stderr)


FRAGMENT = Path(__file__).resolve().parent.parent / "changelog.d/provisional-decisions.md"
SLICE = Path(__file__).resolve().parent.parent / "specs/001-faster-slipwai/slices/S27-provisional-decisions"


class AfterConvergeWordsTest(FactoryTestCase):
    def test_the_command_says_whose_commit_carries_the_trailer(self) -> None:
        from slipwai.project.cruise_provisional import COMMAND_PARAGRAPH

        flat = " ".join(COMMAND_PARAGRAPH.split())
        self.assertIn("this session's own commit writing the decision into its artifact carries it too", flat)
        self.assertIn("names the decision in every implement and slice brief", flat)

    def test_the_implement_and_slice_agents_say_a_commit_under_a_named_decision_carries_the_trailer(self) -> None:
        from slipwai.layout import AT_ROOT
        from slipwai.project.agents import agent_files

        files = agent_files(AT_ROOT)
        for name in ("drive-implement", "drive-slice"):
            flat = " ".join(next(text for path, text in files.items() if path.endswith(f"{name}.md")).split())
            self.assertIn("Where the brief names a provisional decision, `D<n>`, every commit you make under it ends "
                          "with the trailer `Decision: D<n>`", flat, name)

    def test_the_entry_shape_shows_the_rehearsal_line_optional_and_its_tier_required(self) -> None:
        from slipwai.project.cruise_provisional import MODE_LINE

        self.assertTrue(MODE_LINE.startswith("- **Provisional (shadow | advisory):** <optional line; written, it "
                                             "opens with the final tier, which is required> · "), MODE_LINE)

    def test_the_fragments_catch_up_is_true_of_the_verbs(self) -> None:
        catch_up = " ".join(FRAGMENT.read_text(encoding="utf-8").split("**Catch-up.**")[1].split())
        self.assertIn("appends one entry, to the log of the feature it works in", catch_up)
        self.assertIn("the iteration runs `python3 scripts/agents/cruise.py mode` (the runner does not)", catch_up)
        self.assertNotIn("appends one entry to each feature's log", catch_up)
        self.assertNotIn("the runner prints it", catch_up)
        self.assertIn("let an iteration record each rung before taking the next", catch_up)
        self.assertIn("`agents/drive-implement.md` and `agents/drive-slice.md`", catch_up)
        self.assertIn("refuses an editing tool aimed at `.specify/cruise.json`", catch_up)
        self.assertIn("resumes with a `told:` message", catch_up)

    def test_the_slice_documents_say_it_the_same_way(self) -> None:
        def flat(name: str) -> str:
            return " ".join((SLICE / name).read_text(encoding="utf-8").split())

        data_model = flat("data-model.md")
        self.assertIn("exit 0 `cruise: decide is <v>, as D<n> recorded` (` in <log>` where another feature's log "
                      "holds it)", data_model)
        self.assertIn("latest `When` (an instant, UTC; one that does not parse sorts first) across every feature's "
                      "`specs/*/decisions.md`", data_model)
        self.assertIn("every feature's `specs/*/decisions.md` headings, the latest `When` as an instant (D202)",
                      flat("research.md"))
        quickstart = flat("quickstart.md")
        self.assertNotIn("git init -q && git add -A && git commit", quickstart)
        self.assertIn("`generate` has already made the first commit", quickstart)


del DecideModeTest, BASE, git  # imported for their fixtures only; unittest must not collect them twice

if __name__ == "__main__":
    unittest.main()
