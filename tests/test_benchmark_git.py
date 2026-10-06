"""T045 (A3, A4, A5): what git holds or lacks cannot stop the report, and reading it never reaches the network."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from elapsed_fixture import (
    FEATURE,
    bench,
    clean,
    commit,
    entry,
    git,
    graph,
    project,
    record,
    register,
    stamp,
    summaries,
    write,
)

sys.dont_write_bytecode = True

SPLIT = f"specs/{FEATURE}/story-split.md"
REGISTER = f"specs/{FEATURE}/slices/README.md"


class GitTest(unittest.TestCase):
    def setUp(self) -> None:
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.repo = repo = project(Path(self.scratch.name))
        write(repo, SPLIT, graph([("S1", [])]))
        path = record(repo, "S1", entry("implement", stamp(3, "09:00:00"), stamp(3, "10:00:00")))
        commit(repo, stamp(2), "split", SPLIT, path)
        write(repo, REGISTER, register(["S1"]))
        commit(repo, stamp(4), "S1 done", REGISTER)

    def test_e1_a_past_copy_that_is_not_utf8_does_not_stop_the_report(self) -> None:
        repo = project(Path(self.scratch.name), "q")
        (repo / SPLIT).parent.mkdir(parents=True)
        (repo / SPLIT).write_bytes(b"# Story split\ncaf\xe9\n")
        commit(repo, stamp(1, "12:00:00"), "latin-1", SPLIT)
        write(repo, SPLIT, graph([("S1", [])]))
        path = record(repo, "S1", entry("implement", stamp(3, "09:00:00"), stamp(3, "10:00:00")))
        commit(repo, stamp(2), "valid", SPLIT, path)
        write(repo, REGISTER, register(["S1"]))
        commit(repo, stamp(4), "S1 done", REGISTER)
        self.assertEqual(stamp(2), summaries(repo)["S1"]["moments"]["ready"])
        for arguments in ((), ("overview", FEATURE)):
            done = bench(repo, *arguments)
            self.assertEqual((0, ""), (done.returncode, done.stderr), arguments)

    def test_e2_with_no_git_on_the_path_every_figure_git_answers_reads_unknown(self) -> None:
        done = subprocess.run([sys.executable, "-B", str(self.repo / "scripts/agents/benchmark.py"), "--json"],
                              cwd=self.repo, env={**clean(self.repo / ".home"), "PATH": "/nonexistent"}, text=True,
                              capture_output=True, timeout=120)
        self.assertEqual((0, ""), (done.returncode, done.stderr))
        item = next(item for item in json.loads(done.stdout) if item["slice"] == "S1")
        for key in ("ready", "accepted"):
            self.assertIn("git not found", item["moments"][key]["unknown"])
        self.assertIn("git not found", item["elapsed"]["unknown"])

    def test_e3_a_partial_clone_reads_unknown_and_fetches_nothing(self) -> None:
        source, clone = self.repo, Path(self.scratch.name) / "clone"
        git(source, "config", "uploadpack.allowFilter", "true")
        git(Path(self.scratch.name), "clone", "-q", "--filter=blob:none", f"file://{source}", str(clone))
        (clone / ".home").mkdir()
        shutil.copytree(source / "scripts", clone / "scripts")
        before = git(clone, "count-objects", "-v")
        found = summaries(clone)["S1"]
        self.assertIn("partial clone", found["elapsed"]["unknown"])
        self.assertEqual(before, git(clone, "count-objects", "-v"))


if __name__ == "__main__":
    unittest.main()
