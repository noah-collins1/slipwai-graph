"""D203: the run never moves `decide` itself. `guard` refuses an editing tool aimed at `.specify/cruise.json` in a
runner's session, and the runner compares `decide` before and after each iteration and parks when it moved inside
one; a person's change between iterations is not a move inside one, and goes on being recorded by `mode`."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True

from support import FactoryTestCase  # noqa: E402
from test_cruise_guard import edit  # noqa: E402
from test_cruise_runner import cruise, enable, fake_harness, logged  # noqa: E402
from test_cruise_stop_hook import hook  # noqa: E402


def decide_of(repo: Path) -> str:
    return json.loads((repo / ".specify/cruise.json").read_text(encoding="utf-8"))["decide"]


class DecideGuardTest(FactoryTestCase):
    def test_guard_refuses_an_edit_to_the_settings_file_in_a_runners_session_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "guarded", "standard", "python")
            enable(repo)
            for spelled in (".specify/cruise.json", str(repo / ".specify/cruise.json"),
                            str(repo / ".specify/../.specify/cruise.json")):
                refused = edit(repo, spelled)
                self.assertEqual(refused.returncode, 2, (spelled, refused.stderr))
                self.assertIn("`.specify/cruise.json` is the run's own setting", refused.stderr)
                self.assertIn("/cruise-settings", refused.stderr)
                self.assertEqual(refused.stdout, "")
            for path in (".specify/product-owner.md", ".specify/cruise.json.bak", "specs/cruise.json"):
                allowed = edit(repo, str(repo / path))
                self.assertEqual((allowed.returncode, allowed.stdout, allowed.stderr), (0, "", ""), path)
            typed = edit(repo, str(repo / ".specify/cruise.json"), env={})
            self.assertEqual((typed.returncode, typed.stdout, typed.stderr), (0, "", ""))
            notebook = hook(repo, "guard", {"tool_name": "NotebookEdit", "cwd": str(repo),
                                            "tool_input": {"notebook_path": ".specify/cruise.json"}},
                            {"CRUISE_RUNNER": "1", "CRUISE_ITERATION": "3"})
            self.assertEqual(notebook.returncode, 2, notebook.stderr)


class DecideMovedInsideAnIterationTest(FactoryTestCase):
    def test_the_runner_parks_an_iteration_that_moved_decide_whatever_its_last_line_said(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "moved", "standard", "python")
            enable(repo, max_iterations="3")  # a runner that fails to park ends here, not never
            env = fake_harness(Path(directory), """mkdir -p specs && touch "specs/progress-$n"
sed -i 's/"recommended-first"/"provisional-shadow"/' .specify/cruise.json
echo "cruise: continue\"""")
            parked = cruise(repo, "run", "--no-park", env=env)
            self.assertEqual(parked.returncode, 3, parked.stdout + parked.stderr)
            self.assertIn("cruise: parked — iteration 1 moved `decide` from recommended-first to "
                          "provisional-shadow — an iteration never sets it; a person who changed it on purpose "
                          "resumes the run with a `told:` message (/cruise-tell)", parked.stdout)
            self.assertEqual(len(logged(repo)), 1, "the run did not go on to a second iteration")
            self.assertEqual(logged(repo)[-1]["decide_moved"], ["recommended-first", "provisional-shadow"])

    def test_an_iteration_that_leaves_decide_alone_is_not_parked_for_it(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "still", "standard", "python")
            enable(repo)
            env = fake_harness(Path(directory), """mkdir -p specs && touch "specs/progress-$n"
sed -i 's/"max_hours": null/"max_hours": 9/' .specify/cruise.json
if [ "$n" -ge 2 ]; then echo "cruise: done"; else echo "cruise: continue"; fi""")
            result = cruise(repo, "run", "--no-park", env=env)
            self.assertNotIn("moved `decide`", result.stdout)
            self.assertNotIn("decide_moved", json.dumps(logged(repo)))
            self.assertEqual(decide_of(repo), "recommended-first")

    def test_a_broken_file_moves_nothing_but_the_same_iteration_mending_it_to_another_value_does(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "mended", "standard", "python")
            enable(repo, max_iterations="4")
            env = fake_harness(Path(directory), """mkdir -p specs && touch "specs/progress-$n"
here="$(dirname "$0")"
if [ "$n" -eq 1 ]; then
  cp .specify/cruise.json "$here/good.json"
  echo '{"enabled": true, "decide": "nobody"}' > .specify/cruise.json
fi
if [ "$n" -eq 2 ]; then sed 's/"recommended-first"/"provisional-shadow"/' "$here/good.json" > .specify/cruise.json; fi
echo "cruise: continue\"""")
            parked = cruise(repo, "run", "--no-park", env=env)
            self.assertEqual(parked.returncode, 3, parked.stdout + parked.stderr)
            self.assertNotIn("iteration 1 moved `decide`", parked.stdout)
            self.assertIn("iteration 2 moved `decide` from recommended-first to provisional-shadow", parked.stdout)
