"""R9 (AC-S03-35, D83 item 4): a note is bound to the run that wrote it.

Two runs of the gate in one worktree share one note under the git directory. The run token the recipe hands both of a
run's halves is what lets `record` tell its own run's note from another's, and a hand-typed `record` from either. The
interleaving is the adversary's (B1): run A's checks are in flight on a passing tree, an edit that fails the gate, run
B started on it, then A finishes. A is held by a stand-in `uv` that waits for a file, never by a clock, and every child
is bounded by a watchdog.
"""
from __future__ import annotations

import os
import re
import signal
import subprocess
import threading
from pathlib import Path

from stamp_fixture import StampTestCase

HELD = "held (stand-in)"
NOT_RECORDED = "not recorded"
TOKEN = re.compile(r"--token (\S+)")


class TwoRunsTest(StampTestCase):
    def start(self, env: dict[str, str | None]) -> subprocess.Popen[str]:
        child = subprocess.Popen(
            ["make", "verify"], cwd=self.repo, env=self.environment(env), text=True, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, start_new_session=True,
        )
        watchdog = threading.Timer(150, os.killpg, (child.pid, signal.SIGKILL))  # a bound, not a wait
        watchdog.start()
        self.addCleanup(watchdog.cancel)
        self.addCleanup(self.reap, child)
        return child

    def reap(self, child: subprocess.Popen[str]) -> None:
        if child.poll() is None:
            os.killpg(child.pid, signal.SIGKILL)
            child.wait()
        if child.stdout is not None:
            child.stdout.close()

    def read_until(self, child: subprocess.Popen[str], text: str) -> list[str]:
        """The run's lines up to the one that holds `text`: a blocking read, ended by the watchdog."""
        assert child.stdout is not None
        seen = []
        for line in child.stdout:
            seen.append(line)
            if text in line:
                return seen
        self.fail(f"the run never printed {text!r}: {''.join(seen)[-400:]}")

    def finish(self, child: subprocess.Popen[str]) -> str:
        assert child.stdout is not None
        output = child.stdout.read()
        child.wait()
        return output

    def edit_tree(self) -> None:
        (self.repo / "README.md").write_text("an edit that fails lint\n", encoding="utf-8")

    def notes(self) -> list[Path]:
        return sorted((self.repo / ".git" / "slipwai").glob("*.pending"))

    def test_run_b_failing_on_an_edited_tree_leaves_no_stamp_when_run_a_finishes(self) -> None:
        """B1: A passes on the tree it began with; the tree is edited, B starts on it and fails; A's `record`
        used to find B's note, whose key is the edited tree's, and write a stamp for a tree that fails."""
        release = self.repo.parent / "release"
        first = self.start({"STANDIN_HOLD": str(release)})
        self.read_until(first, HELD)
        self.edit_tree()
        second = self.run_gate({"STANDIN_UV_FAIL": "1"})
        self.assertNotEqual(second.returncode, 0, "the edited tree fails: that is the premise")
        release.write_text("", encoding="utf-8")
        output = self.finish(first)
        self.assertEqual(first.returncode, 0, output)
        self.assertIsNone(self.stamp_path(), "a stamp stands for an edited tree that fails the gate")
        lines = [line for line in output.splitlines() if NOT_RECORDED in line]
        self.assertEqual(len(lines), 1, output)
        self.assertIn("another run of the gate", lines[0])

    def test_run_b_interrupted_on_an_edited_tree_leaves_no_stamp_when_run_a_finishes(self) -> None:
        """B1: B is killed while its checks run; its note is what stands, and A may not take it for its own."""
        release = self.repo.parent / "release"
        first = self.start({"STANDIN_HOLD": str(release)})
        self.read_until(first, HELD)
        self.edit_tree()
        second = self.start({"STANDIN_UV_HANG": "1"})
        self.read_until(second, "waiting (stand-in)")
        os.killpg(second.pid, signal.SIGKILL)
        second.wait()
        release.write_text("", encoding="utf-8")
        output = self.finish(first)
        self.assertEqual(first.returncode, 0, output)
        self.assertIsNone(self.stamp_path())
        self.assertEqual(len([line for line in output.splitlines() if NOT_RECORDED in line]), 1, output)

    def test_a_run_that_is_alone_records_as_it_did(self) -> None:
        """A hold: one run, one token, the stamp written, and the note removed."""
        run = self.run_gate()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertIsNotNone(self.stamp_path())
        self.assertEqual(self.notes(), [])
        self.assertEqual([line for line in run.stdout.splitlines() if NOT_RECORDED in line], [])

    def test_record_typed_by_hand_after_a_failed_run_writes_nothing_and_says_so(self) -> None:
        """B2: the failed run's note holds the key of a tree that failed; a `record` with no token is no run's."""
        run = self.run_gate({"STANDIN_UV_FAIL": "1"})
        self.assertNotEqual(run.returncode, 0)
        self.assertEqual(len(self.notes()), 1, "the premise: a failed run leaves its note")
        typed = subprocess.run(["python3", "scripts/verify-stamp.py", "record"], cwd=self.repo,
                               env=self.environment(), text=True, capture_output=True, timeout=60)
        self.assertEqual(typed.returncode, 0)
        self.assertIsNone(self.stamp_path(), "a hand-typed record stamped a tree that failed")
        lines = typed.stdout.splitlines()
        self.assertEqual(len(lines), 1, typed.stdout)
        self.assertIn(NOT_RECORDED, lines[0])
        self.assertIn("not a run of the gate", lines[0])

    def test_record_with_another_runs_token_writes_nothing_and_says_so(self) -> None:
        self.run_gate({"STANDIN_UV_FAIL": "1"})
        typed = subprocess.run(["python3", "scripts/verify-stamp.py", "record", "--token", "0" * 32],
                               cwd=self.repo, env=self.environment(), text=True, capture_output=True, timeout=60)
        self.assertIsNone(self.stamp_path())
        self.assertEqual(len(typed.stdout.splitlines()), 1, typed.stdout)
        self.assertIn("another run of the gate", typed.stdout)

    def test_the_recipe_hands_both_halves_one_token_and_each_run_has_its_own(self) -> None:
        """The token is a random value, not a process id, a host or a path; the note holds it and only it."""
        tokens = []
        for _ in range(2):
            self.forget_log()
            self.run_gate({"VERIFY_FORCE": "1"})
            lines = [line for line in self.log.read_text(encoding="utf-8").splitlines() if "verify-stamp.py" in line]
            found = [TOKEN.search(line) for line in lines if " reuse " in line or " record " in line]
            self.assertEqual(len(found), 2, lines)
            given = [match.group(1) for match in found if match]
            self.assertEqual(len(set(given)), 1, f"the two halves were given different tokens: {given}")
            tokens.append(given[0])
        self.assertEqual(len(set(tokens)), 2, "two runs share a token")
        for token in tokens:
            self.assertRegex(token, r"^[0-9a-f]{32}$")

    def test_the_note_holds_the_token_and_no_process_id_host_or_path(self) -> None:
        release = self.repo.parent / "release"
        first = self.start({"STANDIN_HOLD": str(release)})
        self.read_until(first, HELD)
        notes = self.notes()
        self.assertEqual(len(notes), 1)
        text = notes[0].read_text(encoding="utf-8")
        release.write_text("", encoding="utf-8")
        self.finish(first)
        for forbidden in (str(first.pid), str(self.repo), os.uname().nodename):
            self.assertNotIn(forbidden, text)
        self.assertRegex(text, r'"token": "[0-9a-f]{32}"')
