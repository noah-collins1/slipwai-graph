"""R10 (AC-S03-12, -13): where the key cannot be built, the gate runs, the stamp is removed and none is written.

Each example plants a stamp that a run able to tell would reuse (`plant_stamp`, where the key can be built), so a run
that starts every check and leaves no stamp behind is one that said it could not tell. One line comes first, before
any check; the exit code is the gate's own, read from `make verify-checks` run the same way.
"""
from __future__ import annotations

import shutil
import subprocess
import sys

from stamp_fixture import StampTestCase, git

REFUSING_GIT = "#!/bin/sh\necho 'fatal: stand-in refusal' >&2\nexit 128\n"


class CannotTellTest(StampTestCase):
    def gates_exit(self, env: dict[str, str | None] | None = None) -> int:
        """What the gate alone exits with, here: `make verify-checks`, which no stamp can touch."""
        done = subprocess.run(["make", "verify-checks"], cwd=self.repo, env=self.environment(env), text=True,
                              capture_output=True, timeout=180)
        self.forget_log()
        return done.returncode

    def assert_cannot_tell(
        self, naming: list[str], env: dict[str, str | None] | None = None, stands: bytes | None = None,
    ) -> None:
        """One line first, naming each of `naming`; every check ran; the exit is the gate's; no stamp is left — or,
        where git cannot even say where one would be (`stands`), the planted one is neither read nor touched."""
        expected = self.gates_exit(env)
        run = self.run_gate(env)
        self.assertEqual(run.returncode, expected, run.stdout + run.stderr)
        lines = self.reuse_lines(run)
        self.assertEqual(len(lines), 1, run.stdout)
        self.assertEqual(run.stdout.splitlines()[0], lines[0], "the line is not before the first check")
        for word in naming:
            self.assertIn(word, lines[0])
        self.assertNotIn("did not run", lines[0])
        self.assertTrue(self.checks(), "the gate did not run")
        path = self.stamp_path()
        if stands is None:
            self.assertIsNone(path, "a stamp stood, or was written, where the key could not be built")
        else:
            assert path is not None
            self.assertEqual(path.read_bytes(), stands)

    def unreadable(self, name: str) -> None:
        """`name` is there, a stamp stands for the tree with it, and then nothing may read it."""
        path = self.repo / name
        path.write_text("secret\n", encoding="utf-8")
        self.plant_stamp()
        path.chmod(0o000)
        self.addCleanup(path.chmod, 0o644)
        try:
            path.read_bytes()
        except OSError:
            return
        self.skipTest("this account can read a file with no permissions")

    def test_a_file_marked_assume_unchanged(self) -> None:
        """e12: git is told not to look at it, so the index cannot vouch for it."""
        git(self.repo, "update-index", "--assume-unchanged", "README.md")
        self.plant_stamp()
        self.assert_cannot_tell(["assume-unchanged", "README.md"])

    def test_a_file_marked_skip_worktree(self) -> None:
        """e12: the same, with git's other way of not looking."""
        git(self.repo, "update-index", "--skip-worktree", "README.md")
        self.plant_stamp()
        self.assert_cannot_tell(["skip-worktree", "README.md"])

    def test_a_submodule_entry(self) -> None:
        """e12: an index entry of mode 160000 stands for a repository the key does not read."""
        head = git(self.repo, "rev-parse", "HEAD").strip()
        git(self.repo, "update-index", "--add", "--cacheinfo", f"160000,{head},vendor/sub")
        self.plant_stamp()
        self.assert_cannot_tell(["submodule", "vendor/sub"])

    def test_an_untracked_directory_that_is_itself_a_repository(self) -> None:
        """e12 (research item 2, read here): `git ls-files --others` lists it as one entry ending in `/`, and its
        files are not read, so the key cannot vouch for it."""
        self.plant_stamp()
        inner = self.repo / "vendored"
        inner.mkdir()
        git(inner, "init", "-q", ".")
        (inner / "a.txt").write_text("a\n", encoding="utf-8")
        self.assert_cannot_tell(["vendored/", "repository"])

    def test_a_git_that_fails_carries_its_reason(self) -> None:
        """e13: a `git` first on `PATH` that refuses; its words are on the line."""
        planted = self.plant_stamp()
        refusing = self.bin / "git"
        refusing.write_text(REFUSING_GIT, encoding="utf-8")
        refusing.chmod(0o755)
        self.assert_cannot_tell(["git", "stand-in refusal"], stands=planted)

    def test_a_directory_that_is_no_repository_carries_gits_reason(self) -> None:
        """e13: the gate runs in a copy with no `.git`, and the line has git's own words."""
        shutil.rmtree(self.repo / ".git")
        self.assert_cannot_tell(["not a git repository"])

    def test_no_git_on_path_is_a_line_and_a_run_for_the_recipe_to_carry_on_from(self) -> None:
        """e13: `reuse` where no `git` can be found exits non-zero, with one line, and writes nothing. (The gate's
        own checks need git too, so this one is held at the script, and the examples above run the gate.)"""
        empty = self.bin.parent / "nothing-on-path"
        empty.mkdir()
        done = subprocess.run(
            [sys.executable, "scripts/verify-stamp.py", "reuse", "--make", "make"], cwd=self.repo, text=True,
            env={"PATH": str(empty), "HOME": str(self.bin.parent)}, capture_output=True, timeout=60)
        self.assertEqual(done.returncode, 1, done.stdout + done.stderr)
        self.assertEqual(len(done.stdout.splitlines()), 1, done.stdout)
        self.assertIn("git", done.stdout)
        self.assertIsNone(self.stamp_path())
        self.assertEqual(done.stderr, "")

    def test_an_unreadable_covered_file_is_named(self) -> None:
        """e13: a file git would list and the key cannot read."""
        self.unreadable("notes.txt")
        self.assert_cannot_tell(["notes.txt"])

    def test_an_unreadable_ignored_input_is_named(self) -> None:
        """e13: the same for a file on the ignored-inputs list, which is read by its bytes as well."""
        self.unreadable(".env")
        self.assert_cannot_tell([".env"])

    def test_a_stamp_that_stood_is_removed_where_the_key_cannot_be_built(self) -> None:
        """e12: a stamp planted for the tree as it was is gone after a run that could not tell, not left to be
        believed once the checkout is in order again."""
        git(self.repo, "update-index", "--skip-worktree", "README.md")
        planted = self.plant_stamp()
        self.assertTrue(planted)
        self.run_gate()
        self.assertIsNone(self.stamp_path())
        git(self.repo, "update-index", "--no-skip-worktree", "README.md")
        self.forget_log()
        run = self.run_gate()
        self.assertTrue(self.checks(), run.stdout)
