"""D208 (adversary B1, B2, B5, B8): the runner never takes more `decide` than a person gave it. Any raise it sees —
inside an iteration, between two, while parked, behind a file that was broken — parks the run until a `told:`
message, and only that releases it; `--set` outside an iteration queues the confirmation itself; `tell` is refused
inside an iteration; a step back never parks. The runner is run for real in a scratch project against a fake harness
that parks, so the test's own edits to the settings stand in for what a process left behind by an iteration does
after it ends. Every run is bounded by `max_iterations` and a deadline, and killed by the pid the test started.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.dont_write_bytecode = True

from support import FactoryTestCase  # noqa: E402
from test_cruise_runner import cruise, enable, fake_harness, outside_a_run  # noqa: E402

from slipwai.project.cruise_record import INBOX  # noqa: E402

CONFIG = ".specify/cruise.json"
PARKS = 'mkdir -p specs && touch "specs/progress-$n"\necho "cruise: parked: S1 needs a person\'s answer"'
HELD = "only a message"


def edit_decide(repo: Path, value: str) -> None:
    """What a hand edit, or a process an iteration left behind, does to the file."""
    path = repo / CONFIG
    table = json.loads(path.read_text(encoding="utf-8"))
    table["decide"] = value
    path.write_text(json.dumps(table, indent=2) + "\n", encoding="utf-8")


class Running:
    """A runner started in `repo` with its output in a file; stopped by its own pid, never by pattern."""

    def __init__(self, repo: Path, env: dict[str, str], out: Path) -> None:
        self.repo, self.out = repo, out
        self.handle = out.open("w", encoding="utf-8")
        self.process = subprocess.Popen(["python3", "-B", "scripts/agents/cruise.py", "run"], cwd=repo, text=True,
                                        stdout=self.handle, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                        env=outside_a_run(env))

    def text(self) -> str:
        return self.out.read_text(encoding="utf-8")

    def wait_for(self, words: str, times: int = 1) -> None:
        deadline = time.monotonic() + 30
        while self.text().count(words) < times:
            if time.monotonic() > deadline:
                raise AssertionError(f"the runner never said {words!r} ({times}x):\n{self.text()}")
            time.sleep(0.05)

    def stop(self) -> None:
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
        self.handle.close()


class DecideRaisedTest(FactoryTestCase):
    def run_parked(self, name: str, decide: str | None = None):
        """A project whose run parks on every iteration, started and waiting for the first park."""
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        repo = self.generate(directory.name, name, "standard", "python")
        enable(repo, max_iterations="3")
        if decide:
            self.assertEqual(cruise(repo, "--set", f"decide={decide}").returncode, 0)
        running = Running(repo, fake_harness(Path(directory.name), PARKS), Path(directory.name) / "out.log")
        self.addCleanup(running.stop)
        running.wait_for("cruise: waiting;")
        return repo, running, Path(directory.name)

    def calls(self, directory: Path) -> int:
        return int((directory / "calls").read_text())

    def test_a_raise_between_iterations_parks_the_run_and_only_a_told_message_releases_it(self) -> None:
        repo, running, directory = self.run_parked("between")
        edit_decide(repo, "provisional-shadow")  # a person's hand edit, or a process an iteration left behind
        (repo / "specs/touched").write_text("a change under specs/ resumes an ordinary park")
        running.wait_for("cruise: parked — `decide` was raised from recommended-first to provisional-shadow outside an "
                         "iteration", 1)
        running.wait_for("cruise: waiting;", 2)
        self.assertIn("a person who raised it on purpose resumes the run with a `told:` message (/cruise-tell)",
                      running.text())
        self.assertIn(HELD, running.text().split("provisional-shadow outside")[1])
        (repo / "specs/touched-again").write_text("still no person's word")
        time.sleep(1.0)
        self.assertEqual(self.calls(directory), 1, "a change in the tree released a park on a raise")
        self.assertTrue(cruise(repo, "tell", "yes, I raised decide").returncode == 0)
        running.wait_for("cruise: a person's message; resuming")
        running.wait_for("cruise: iteration 2 started")
        running.wait_for("cruise: waiting;", 3)  # iteration 2 ran and parked, so its prompt is written
        self.assertIn("told: yes, I raised decide", (directory / "prompts").read_text(encoding="utf-8"))

    def test_a_raise_behind_a_broken_file_is_seen_when_the_file_is_mended(self) -> None:
        repo, running, directory = self.run_parked("broken")
        good = (repo / CONFIG).read_text(encoding="utf-8")
        (repo / CONFIG).write_text('{"enabled": true, "decide": "nobody"}\n', encoding="utf-8")
        (repo / "specs/one").write_text("x")
        running.wait_for("cruise: waiting;", 2)  # iteration 2 ran under the last good settings and parked
        self.assertNotIn("was raised", running.text())
        (repo / CONFIG).write_text(good.replace("recommended-first", "provisional"), encoding="utf-8")
        (repo / "specs/two").write_text("x")
        running.wait_for("`decide` was raised from recommended-first to provisional outside an iteration")
        time.sleep(0.5)
        self.assertEqual(self.calls(directory), 2, "the mended raise started an iteration")

    def test_a_person_raising_decide_through_set_queues_its_confirmation_and_the_run_is_not_parked(self) -> None:
        repo, running, directory = self.run_parked("confirmed")
        raised = cruise(repo, "--set", "decide=provisional-shadow")
        self.assertEqual(raised.returncode, 0, raised.stderr)
        queued = [json.loads(line) for line in (repo / INBOX).read_text(encoding="utf-8").splitlines()]
        self.assertEqual([each.get("decide") for each in queued], ["provisional-shadow"])
        running.wait_for("cruise: iteration 2 started")
        self.assertNotIn("was raised", running.text())

    def test_a_step_back_never_parks_and_queues_nothing(self) -> None:
        repo, running, directory = self.run_parked("back", decide="provisional-shadow")
        stepped = cruise(repo, "--set", "decide=recommended-first")
        self.assertEqual(stepped.returncode, 0, stepped.stderr)
        self.assertFalse((repo / INBOX).exists())
        (repo / "specs/touched").write_text("x")
        running.wait_for("cruise: iteration 2 started")
        self.assertNotIn("was raised", running.text())

    def test_tell_is_refused_inside_an_iteration_even_with_an_empty_mark(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "refused", "standard", "python")
            enable(repo)
            for mark in ("3", ""):
                refused = cruise(repo, "tell", "yes", env={"CRUISE_ITERATION": mark})
                self.assertEqual(refused.returncode, 1, refused.stdout)
                self.assertIn("`tell` is a person's", refused.stderr)
                self.assertFalse((repo / INBOX).exists())
