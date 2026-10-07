"""T024 (B4): every git question `verify_scoped/since.py` asks is asked at the project root, not where it was run.

Run from inside another repository, the default scope read that repository's branch: a `slice/X` checked out there
scoped a run of the project's trunk, and a trunk there rendered every preview of the project's slice. The project is
`test_ux_gates_default`'s, and `check-ux-gates` is run by its path from a directory of an unrelated repository.
"""
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

from test_ux_gates_default import EVERY, SCREENS_DIR, STYLES, GatesCase, commit_all, git, scoped_line

sys.dont_write_bytecode = True


class ElsewhereTest(GatesCase):
    def elsewhere(self, branch: str) -> Path:
        """An unrelated repository with one commit, on `branch`, and a directory inside it to run from."""
        other = self.scratch / "other"
        (other / "deep").mkdir(parents=True)
        git(other, "init", "-q", "-b", "main")
        (other / "deep" / "file.txt").write_text("x\n", encoding="utf-8")
        commit_all(other, "unrelated")
        if branch != "main":
            git(other, "checkout", "-q", "-b", branch)
        return other / "deep"

    def run_from(self, where: Path) -> tuple[str, set[str]]:
        self.log.unlink(missing_ok=True)
        done = subprocess.run(["python3", "-B", str(self.repo / "scripts" / "check-ux-gates.py")], cwd=where,
                              text=True, capture_output=True, env=self.environment(), timeout=300)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        calls = self.log.read_text(encoding="utf-8").splitlines() if self.log.exists() else []
        previews = {line.split(f"{SCREENS_DIR}/", 1)[1].split(" --dark")[0] for line in calls
                    if f"{SCREENS_DIR}/" in line and ".html" in line}
        return done.stdout, previews

    def test_a_slice_branch_elsewhere_does_not_scope_the_projects_trunk(self) -> None:
        self.edit(f"{STYLES}/linked.css")
        said, previews = self.run_from(self.elsewhere("slice/X"))
        self.assertIn("check-ux-gates: every preview in scope — this is the trunk (`main`)\n", said)
        self.assertNotIn("previews scoped", said)
        self.assertEqual(previews, EVERY)

    def test_the_trunk_elsewhere_does_not_unscope_the_projects_slice(self) -> None:
        self.branch()
        short = git(self.repo, "rev-parse", "--short", "main").strip()
        self.edit(f"{STYLES}/linked.css")
        said, previews = self.run_from(self.elsewhere("main"))
        self.assertIn(scoped_line("slice/S1", short), said)
        self.assertEqual(previews, {"linked.html"})


if __name__ == "__main__":
    unittest.main()
