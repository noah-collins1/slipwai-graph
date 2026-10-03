"""The runner never blocks on a path of its own that is not a regular file, and names a changed control first (D63;
AC-S02-80; adversary A1, A3, B1).

The raw stream and the log are the runner's own paths. An iteration that leaves a FIFO (or a directory) there used to
hang the runner in `open()` before it compared the controls or wrote its entry, so an iteration that had edited a gate
could stop the run from ever saying so. Every run here is bounded by a timeout, so a runner that blocks fails an
assertion, and by `max_iterations`.
"""
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from support import FactoryTestCase
from test_cruise_index import bare_path, index
from test_cruise_runner import enable, fake_harness, logged, outside_a_run

GATE = "scripts/check-ux-gates.py"
STREAM = ".specify/cruise-stream.jsonl"
LOG = "specs/cruise-log.jsonl"
TIMEOUT = 15
EDIT = f"echo '# edited' >> {GATE}"
LEFT = {"fifo": "mkfifo {path}", "directory": "mkdir {path}"}


class RunnerNonRegularTest(FactoryTestCase):
    def run_runner(self, repo: Path, directory: str, behaviour: str, *arguments: str,
                   iterations: str = "2") -> subprocess.CompletedProcess:
        """The runner against a fake harness that does `behaviour`, bounded; a runner that blocks fails here."""
        enable(repo, max_iterations=iterations)
        index(repo)
        bare_path(Path(directory), "cat", "mkdir", "touch", "rm", "mkfifo", "dirname")
        env = {**fake_harness(Path(directory), behaviour), "CRUISE_HARNESS_STREAM": "claude",
               "PATH": str(Path(directory) / "bare")}
        try:
            return subprocess.run(["python3", "scripts/agents/cruise.py", "run", *arguments], cwd=repo, text=True,
                                  capture_output=True, stdin=subprocess.DEVNULL, env=outside_a_run(env),
                                  timeout=TIMEOUT)
        except subprocess.TimeoutExpired as error:
            said = (error.stdout or b"").decode(errors="replace")
            self.fail(f"the runner blocked for {TIMEOUT}s on a path that is not a regular file: {said}")

    def leaves(self, what: str, path: str) -> str:
        return f"mkdir -p specs .specify; rm -rf {path}; " + LEFT[what].format(path=path)

    def project(self, directory: str, name: str) -> Path:
        return self.generate(directory, name, "standard", "python")

    def test_e80_a_fifo_left_at_the_stream_with_a_gate_edited_parks_naming_the_gate(self) -> None:
        """AC-S02-80, A1: the controls are compared and named before the stream is read."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, "fifo-stream-gate")
            ended = self.run_runner(repo, directory, f'{EDIT}\n{self.leaves("fifo", STREAM)}\necho "cruise: continue"',
                                    "--no-park")
            self.assertEqual(ended.returncode, 3, ended.stdout + ended.stderr)
            self.assertIn(f"cruise: parked — iteration 1 changed a gate or a control of the run — {GATE} (modified)",
                          ended.stdout)
            entry = logged(repo)[-1]
            self.assertEqual(entry["controls_changed"], [f"{GATE} (modified)"])
            self.assertNotIn("index_use", entry)

    def test_e80_a_stream_that_is_not_a_regular_file_gives_no_index_use_and_the_run_goes_on(self) -> None:
        """AC-S02-80: a FIFO or a directory at the stream is read as nothing and appended to by nothing, in the
        iteration that left it and in the next."""
        for what in LEFT:
            with self.subTest(what), tempfile.TemporaryDirectory() as directory:
                repo = self.project(directory, f"{what}-stream")
                ended = self.run_runner(repo, directory, f'''if [ "$n" -eq 1 ]; then {self.leaves(what, STREAM)}; fi
echo "cruise: continue"''', "--no-park")
                self.assertEqual(ended.returncode, 0, ended.stdout + ended.stderr)
                entries = logged(repo)
                self.assertEqual([entry["iteration"] for entry in entries], [1, 2])
                self.assertTrue(all("index_use" not in entry for entry in entries), entries)
                self.assertEqual(entries[0]["bookkeeping"]["stream_bytes"], 0)

    def test_e80_status_does_not_block_on_a_fifo_at_the_stream(self) -> None:
        """AC-S02-80, B1: `status` reads the stream for the account of the index, and the path is not a file."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, "fifo-status")
            enable(repo)
            index(repo)
            (repo / "specs").mkdir(exist_ok=True)
            logged_once = {"iteration": 1, "started": "2026-10-03T00:00:00Z", "ended": "2026-10-03T00:01:00Z",
                           "last_line": "cruise: done", "fingerprint": "0000000000000000"}
            (repo / LOG).write_text(json.dumps(logged_once) + "\n", encoding="utf-8")
            subprocess.run(["mkfifo", str(repo / STREAM)], check=True)
            try:
                said = subprocess.run(["python3", "scripts/agents/cruise.py", "status"], cwd=repo, text=True,
                                      capture_output=True, stdin=subprocess.DEVNULL, env=outside_a_run(),
                                      timeout=TIMEOUT)
            except subprocess.TimeoutExpired:
                self.fail("`status` blocked on a FIFO at the stream")
            self.assertEqual(said.returncode, 0, said.stdout + said.stderr)

    def test_e80_a_fifo_left_at_the_log_with_a_gate_edited_parks_naming_the_gate(self) -> None:
        """AC-S02-80, A3: the entry cannot be written, and the run says which gate changed before it says that."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, "fifo-log-gate")
            ended = self.run_runner(repo, directory, f'{EDIT}\n{self.leaves("fifo", LOG)}\necho "cruise: continue"',
                                    "--no-park")
            self.assertEqual(ended.returncode, 3, ended.stdout + ended.stderr)
            self.assertIn(f"cruise: parked — iteration 1 changed a gate or a control of the run — {GATE} (modified)",
                          ended.stdout)

    def test_e80_a_log_that_is_not_a_regular_file_ends_the_run_with_one_line_naming_it(self) -> None:
        """AC-S02-80, A3: a FIFO or a directory at the log; the runner never blocks and never prints a traceback."""
        for what in LEFT:
            with self.subTest(what), tempfile.TemporaryDirectory() as directory:
                repo = self.project(directory, f"{what}-log")
                ended = self.run_runner(repo, directory, f'{self.leaves(what, LOG)}\necho "cruise: continue"',
                                        "--no-park")
                self.assertEqual(ended.returncode, 1, ended.stdout + ended.stderr)
                self.assertEqual(len(ended.stderr.strip().splitlines()), 1, ended.stderr)
                self.assertIn(LOG, ended.stderr)
                self.assertIn("not a regular file", ended.stderr)
                self.assertNotIn("Traceback", ended.stderr)
