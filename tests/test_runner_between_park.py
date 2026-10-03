"""A control changed while the run was parked is named, not parked on again (D64; AC-S02-72 to -75, -77, -78).

A park is the time the page gives a person to edit a control, so the run does not park a second time on what changed
during one. The next entry carries `controls_changed_between` and the feed one `cruise:` line. Where no control
changed, and on a runner process's first iteration, nothing is said. The runs are bounded by a timeout and
`max_iterations`.
"""
from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path

from support import FactoryTestCase
from test_cruise_runner import enable, fake_harness, logged
from test_runner_between import GATE, PARK, Resumable, arm, gapped, ran

NAMED = f"cruise: {GATE} (modified) changed while the run was parked; iteration 2 starts against them"


class RunnerBetweenParkTest(FactoryTestCase):
    def parked_between(self, directory: str, name: str) -> tuple[Path, Resumable, str]:
        """A run parked on a gate changed in the gap after iteration 1, waiting for a person; and the gate's text."""
        repo, env = gapped(self, directory, name)
        enable(repo)
        arming = arm(directory, repo, f"echo '# edited' >> {repo / GATE}")
        harness = fake_harness(Path(directory), f'''case "$n" in
  1) {arming}
     echo "cruise: continue";;
  *) echo "cruise: done";;
esac''')
        original = (repo / GATE).read_text(encoding="utf-8")
        runner = Resumable(repo, directory, {**env, **harness})
        runner.wait_for("cruise: waiting;")
        return repo, runner, original

    def test_e72_a_change_kept_on_purpose_is_named_on_the_next_entry_and_in_the_feed_once(self) -> None:
        """AC-S02-72: the person keeps the change and resumes with a message; the number was not consumed."""
        with tempfile.TemporaryDirectory() as directory:
            repo, runner, _ = self.parked_between(directory, "named-kept")
            try:
                runner.tell("kept on purpose")
                runner.wait_for("cruise: done")
            finally:
                output = runner.end()
            self.assertEqual(output.count(PARK), 1)
            self.assertEqual(output.splitlines().count(NAMED), 1, output)
            entries = logged(repo)
            self.assertEqual([entry["iteration"] for entry in entries], [1, 2])
            self.assertEqual(entries[1]["controls_changed_between"], [f"{GATE} (modified)"])
            self.assertNotIn("controls_changed", entries[1])
            self.assertEqual(entries[1]["told"], ["kept on purpose"])

    def test_e73_a_change_reverted_during_the_park_leaves_neither_field_and_no_line(self) -> None:
        """AC-S02-73: the net difference at the iteration's start is nothing."""
        with tempfile.TemporaryDirectory() as directory:
            repo, runner, original = self.parked_between(directory, "named-reverted")
            try:
                (repo / GATE).write_text(original, encoding="utf-8")
                runner.tell("reverted")
                runner.wait_for("cruise: done")
            finally:
                output = runner.end()
            entry = logged(repo)[1]
            self.assertEqual(entry["iteration"], 2)
            self.assertTrue("controls_changed" not in entry and "controls_changed_between" not in entry, entry)
            self.assertNotIn("changed while the run was parked", output)

    def test_e74_a_control_changed_during_any_park_is_named_and_a_later_change_still_parks(self) -> None:
        """AC-S02-74: iteration 1 parks for a decision; the person edits a gate and resumes; iteration 2 is named
        the change and runs; iteration 3 edits the same gate and parks naming it as its own."""
        with tempfile.TemporaryDirectory() as directory:
            repo, env = gapped(self, directory, "named-other-park")
            enable(repo)
            harness = fake_harness(Path(directory), f'''case "$n" in
  1) echo "cruise: parked: a person must decide";;
  2) echo "cruise: continue";;
  *) echo '# again' >> {GATE}; echo "cruise: continue";;
esac''')
            runner = Resumable(repo, directory, {**env, **harness})
            try:
                runner.wait_for("cruise: waiting;")
                (repo / GATE).write_text((repo / GATE).read_text(encoding="utf-8") + "# kept\n", encoding="utf-8")
                runner.tell("here you are")
                runner.wait_for(f"cruise: parked — iteration 3 changed a gate or a control of the run — {GATE}")
                (repo / ".specify/cruise.stop").write_text("", encoding="utf-8")
            finally:
                output = runner.end()
            self.assertEqual(output.splitlines().count(NAMED), 1, output)
            entries = logged(repo)
            self.assertEqual([entry.get("controls_changed_between") for entry in entries],
                             [None, [f"{GATE} (modified)"], None])
            self.assertEqual([entry.get("controls_changed") for entry in entries], [None, None, [f"{GATE} (modified)"]])

    def test_e75_hold_a_change_that_parked_its_own_iteration_and_was_kept_is_not_named_again(self) -> None:
        """AC-S02-75 (hold): the kept after-signature is the next before-signature, so nothing differs."""
        with tempfile.TemporaryDirectory() as directory:
            repo, env = gapped(self, directory, "named-not-twice")
            enable(repo)
            harness = fake_harness(Path(directory), f'''case "$n" in
  1) echo '# the iteration changed it' >> {GATE}; echo "cruise: continue";;
  *) echo "cruise: done";;
esac''')
            runner = Resumable(repo, directory, {**env, **harness})
            try:
                runner.wait_for("cruise: waiting;")
                runner.tell("keep it")
                runner.wait_for("cruise: done")
            finally:
                output = runner.end()
            entries = logged(repo)
            self.assertEqual(entries[0]["controls_changed"], [f"{GATE} (modified)"])
            self.assertEqual(entries[1]["told"], ["keep it"])
            self.assertTrue("controls_changed" not in entries[1] and "controls_changed_between" not in entries[1])
            self.assertNotIn("changed while the run was parked", output)

    def test_e77_hold_no_change_between_two_iterations_says_nothing_and_writes_no_field(self) -> None:
        """AC-S02-77 (hold)."""
        with tempfile.TemporaryDirectory() as directory:
            repo, env = gapped(self, directory, "named-nothing")
            enable(repo, max_iterations="3")
            harness = fake_harness(Path(directory), 'echo "cruise: continue"')
            ended = ran(repo, "run", "--no-park", env={**env, **harness})
            self.assertEqual(ended.returncode, 0, ended.stdout + ended.stderr)
            self.assertNotIn("changed while the run was parked", ended.stdout)
            self.assertNotIn("changed between iterations", ended.stdout)
            self.assertTrue(all("controls_changed_between" not in entry for entry in logged(repo)))

    def test_e78_hold_a_runner_processs_first_iteration_compares_nothing_with_an_earlier_process(self) -> None:
        """AC-S02-78 (hold): a gate changed between two runner processes is not seen by the runner at all."""
        with tempfile.TemporaryDirectory() as directory:
            repo, env = gapped(self, directory, "named-first")
            enable(repo, max_iterations="1")
            harness = fake_harness(Path(directory), 'echo "cruise: continue"')
            first = ran(repo, "run", "--no-park", env={**env, **harness})
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            (repo / GATE).write_text((repo / GATE).read_text(encoding="utf-8") + "# between processes\n",
                                     encoding="utf-8")
            second = ran(repo, "run", "--no-park", env={**env, **harness})
            self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
            entry = logged(repo)[-1]
            self.assertEqual(entry["iteration"], 2)
            self.assertTrue("controls_changed" not in entry and "controls_changed_between" not in entry)

    def test_the_generated_command_says_a_control_is_also_compared_between_iterations(self) -> None:
        """The cruise command's *Blocked* paragraph says what D64 decided, in the words a person reads."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "said-between", "standard", "python")
            command = (repo / "commands/cruise.md").read_text()
            self.assertIn("It compares them between iterations too: a control changed after one iteration\nended and "
                          "before the next began, with no park between, parks the run before the next starts; one "
                          "changed while\nthe run was parked is named on the next entry (`controls_changed_between`) "
                          "and in the feed, and does not park it\nagain.", command)

    def test_watch_reads_the_between_park_as_a_park_and_the_naming_line_as_nothing_it_returns_on(self) -> None:
        """`watch`'s `boundary()` against the two new lines: the park returns the seat, the naming does not."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "watch-between", "standard", "python")
            sys.dont_write_bytecode = True  # no __pycache__/ beside the toolkit's scripts (AC-S02-45)
            sys.path.insert(0, str(repo / "scripts/agents"))
            try:
                specification = importlib.util.spec_from_file_location("cruise_read", repo / "scripts/agents/cruise.py")
                assert specification is not None and specification.loader is not None
                module = importlib.util.module_from_spec(specification)
                specification.loader.exec_module(module)
            finally:
                sys.path.remove(str(repo / "scripts/agents"))
            self.assertEqual(module.boundary(PARK), ("parked", PARK.removeprefix("cruise: parked — ")))
            self.assertIsNone(module.boundary(NAMED))
