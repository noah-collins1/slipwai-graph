"""R11, R10 (AC-S03-36, D83 items 6 and 11): what git and the files say is taken exactly.

Git's answer for a path loses exactly one trailing line feed and nothing else, so a git directory or a project
directory whose name begins or ends in whitespace has a stamp of its own, inside its own git directory. An empty
directory at the note's path is removed as itself and a full one is named; a file where the factory's directory should
be is named as that file. A stamp whose instant is not exactly the shape the reuse line prints is no stamp, and git's
reason on a line is its first non-empty line, escaped.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from stamp_fixture import StampTestCase, commit_all, git

MULTI_LINE_GIT = (
    "#!/bin/sh\nprintf '\\n\\nfatal: first line \\033[31mred\\nhint: second\\nhint: third\\n' >&2\nexit 128\n"
)
FORGED = "verify: forged line"


class WhitespaceNamesTest(StampTestCase):
    def test_a_git_directory_whose_name_ends_in_whitespace_has_its_stamp_inside_it(self) -> None:
        """B3: `strip()` took the space off the name, and the stamp went to a sibling directory outside the git dir."""
        gitdir = self.repo.parent / "gitdir "
        subprocess.run(["git", "init", "-q", "--separate-git-dir", str(gitdir)], cwd=self.repo, check=True)
        self.assertTrue((self.repo / ".git").is_file())
        run = self.run_gate()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertEqual(len(list((gitdir / "slipwai").glob("verify-stamp-*.json"))), 1)
        self.assertFalse((self.repo.parent / "gitdir").exists(), "the stamp went to a directory outside the git dir")
        self.forget_log()
        self.run_gate()
        self.assertEqual(self.checks(), [], "the stamp written inside it is the one read")

    def test_projects_named_alike_but_for_leading_whitespace_have_stamps_of_their_own(self) -> None:
        """B4: the prefix was stripped, so ` p/` and `p/` named one file."""
        top = self.repo.parent / "mono"
        top.mkdir()
        for name in ("p", " p"):
            shutil.copytree(self.repo, top / name, symlinks=True, ignore=shutil.ignore_patterns(".git"))
        subprocess.run(["git", "init", "-q", "-b", "main", str(top)], check=True)
        for key, value in (("user.name", "t"), ("user.email", "t@local"), ("commit.gpgsign", "false")):
            git(top, "config", key, value)
        commit_all(top, "two projects")
        git(top, "checkout", "-q", "-b", "topic")
        for name in ("p", " p"):
            done = subprocess.run(["make", "verify"], cwd=top / name, env=self.environment(), text=True,
                                  capture_output=True, timeout=120)
            self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertEqual(len(list((top / ".git" / "slipwai").glob("verify-stamp-*.json"))), 2)


class FilesWhereTheFactoryWritesTest(StampTestCase):
    def moved(self) -> None:
        (self.repo / "moved.txt").write_text("moved\n", encoding="utf-8")

    def stamped(self) -> Path:
        self.assertEqual(self.run_gate().returncode, 0)
        path = self.stamp_path()
        assert path is not None
        self.forget_log()
        return path

    def test_an_empty_directory_at_the_notes_path_is_removed_as_itself_and_the_pass_is_recorded(self) -> None:
        """B5: it stopped every later run recording, and the line named nothing to delete."""
        note = self.stamped().with_suffix(".pending")
        note.mkdir()
        self.moved()
        run = self.run_gate()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertEqual(self.reuse_lines(run), [], run.stdout)
        self.assertFalse(note.exists(), "the note was left behind")
        self.assertTrue(self.stamp()["passed"])
        self.forget_log()
        self.run_gate()
        self.assertEqual(self.checks(), [], "the pass was recorded, so the tree is reused")

    def test_a_directory_with_something_in_it_at_the_notes_path_is_named_as_the_directory_to_delete(self) -> None:
        note = self.stamped().with_suffix(".pending")
        note.mkdir()
        (note / "keep").write_text("", encoding="utf-8")
        self.moved()
        run = self.run_gate()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        lines = self.reuse_lines(run)
        self.assertEqual(len(lines), 1, run.stdout)
        self.assertIn(note.name, lines[0])
        self.assertIn("delete that directory", lines[0])
        self.assertTrue((note / "keep").exists(), "a directory with something in it is not emptied")
        self.assertTrue(self.checks())

    def test_a_file_where_the_factorys_directory_should_be_is_named_as_that_file(self) -> None:
        """B5: the line named the stamp inside it, which does not exist."""
        directory = self.repo / ".git" / "slipwai"
        directory.mkdir()
        directory.rmdir()
        directory.write_text("in the way\n", encoding="utf-8")
        run = self.run_gate()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        lines = self.reuse_lines(run)
        self.assertEqual(len(lines), 1, run.stdout)
        self.assertIn(str(directory), lines[0])
        self.assertIn("delete that file", lines[0])
        self.assertNotIn("verify-stamp-", lines[0])
        self.assertEqual(directory.read_text(encoding="utf-8"), "in the way\n")


class InstantTest(StampTestCase):
    def plant_with(self, passed: object) -> None:
        self.plant_stamp()
        path = self.stamp_path()
        assert path is not None
        stamp = json.loads(path.read_text(encoding="utf-8"))
        stamp["passed"] = passed
        path.write_text(json.dumps(stamp, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def test_a_stamp_whose_instant_is_not_the_printed_shape_is_no_stamp_and_prints_nothing_of_it(self) -> None:
        """B6: a hand-made stamp printed arbitrary lines."""
        for passed in (f"2026-01-01T00:00:00Z\n{FORGED}", "2026-01-01T00:00:00Z\n", " 2026-01-01T00:00:00Z",
                       "2026-01-01 00:00:00Z", "2026-01-01T00:00:00", "2026-01-01T00:00:00+00:00",
                       "２026-01-01T00:00:00Z", "2026-01-01T00:00:00.5Z", 20260101, None, ["2026-01-01T00:00:00Z"]):
            with self.subTest(passed=passed):
                self.plant_with(passed)
                self.forget_log()
                run = self.run_gate()
                self.assertTrue(self.checks(), "a stamp with an instant of another shape was reused")
                self.assertNotIn("forged", run.stdout)
                self.assertNotIn("did not run", run.stdout)

    def test_a_stamp_of_the_printed_shape_is_reused_and_its_instant_shown(self) -> None:
        """A hold: the shape `record` writes."""
        self.plant_with("2031-12-31T23:59:59Z")
        self.forget_log()
        run = self.run_gate()
        self.assertEqual(self.checks(), [])
        self.assertIn("2031-12-31T23:59:59Z", run.stdout)


class GitsReasonTest(StampTestCase):
    def refuse(self) -> None:
        refusing = self.bin / "git"
        refusing.write_text(MULTI_LINE_GIT, encoding="utf-8")
        refusing.chmod(0o755)

    def assert_one_line(self) -> None:
        run = self.run_gate()
        lines = self.reuse_lines(run)
        self.assertEqual(len(lines), 1, run.stdout)
        self.assertIn("fatal: first line", lines[0])
        self.assertNotIn("hint", run.stdout, "git's second and third lines are printed")
        self.assertIn("\\x1b", lines[0], "a control character in git's words is escaped")
        self.assertNotIn("\x1b", run.stdout)

    def test_git_failing_with_several_lines_is_one_line_with_its_first_non_empty_line_escaped(self) -> None:
        """C6: it was four lines."""
        self.refuse()
        self.assert_one_line()

    def test_the_same_on_the_trunk(self) -> None:
        git(self.repo, "checkout", "-q", "main")
        self.refuse()
        self.assert_one_line()
