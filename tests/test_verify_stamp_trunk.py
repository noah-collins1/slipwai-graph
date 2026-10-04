"""R7 (AC-S03-37, D83 items 7, 8 and 11): a run that cannot tell which branch is the trunk does not stamp, and says what
to fix.

The questions are asked in this order: a CI marker; a `HEAD` that names no commit or is a symbolic ref outside
`refs/heads` (both silent); whether the trunk can be told (the one line); and only then whether this is the trunk
(silent). Each example plants a stamp valid for the tree as it stands, so a run that read it, wrote one or removed it is
seen, and reads what the run printed and left under the git directory.
"""
from __future__ import annotations

import json
import shutil
import subprocess

from stamp_fixture import StampTestCase, git

NEVER_WRITTEN = "a run that cannot tell which branch is the trunk left a note for a stamp to be written"


class TrunkTestCase(StampTestCase):
    def record(self, value: object = ..., ci: object = ...) -> None:
        """`project.json`'s `ci.branch` set to `value` (left out where it is `...`), or `ci` itself set to `ci`."""
        path = self.repo / "project.json"
        document = json.loads(path.read_text(encoding="utf-8"))
        if ci is not ...:
            document["ci"] = ci
        elif value is not ...:
            document.setdefault("ci", {})["branch"] = value
        path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")

    def notes(self) -> list[str]:
        directory = self.repo / ".git" / "slipwai"
        return sorted(path.name for path in directory.glob("*.pending")) if directory.is_dir() else []

    def run_leaving(
        self, env: dict[str, str | None] | None = None, plant: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        """The gate as typed, with a stamp planted for the tree as it stands: after it the stamp stands byte for byte
        (it was neither read, removed nor written), every check ran, and no note is left."""
        planted = self.plant_stamp() if plant else None
        self.forget_log()
        run = self.run_gate(env)
        self.assertTrue(self.checks(), "no check started: the stamp was read")
        if planted is not None:
            path = self.stamp_path()
            assert path is not None
            self.assertEqual(path.read_bytes(), planted, "the stamp was replaced or removed")
        self.assertEqual(self.notes(), [], NEVER_WRITTEN)
        return run

    def assert_cannot_tell(self, env: dict[str, str | None] | None = None) -> str:
        """One line before the first check, which names what to fix; the stamp untouched."""
        run = self.run_leaving(env)
        lines = self.reuse_lines(run)
        self.assertEqual(len(lines), 1, run.stdout)
        self.assertEqual(run.stdout.splitlines()[0], lines[0], "the line is not before the first check")
        self.assertIn("cannot tell which branch is the trunk", lines[0])
        self.assertIn("ci.branch", lines[0])
        self.assertIn("fetch the trunk", lines[0])
        self.assertNotIn("did not run", lines[0])
        return lines[0]

    def assert_silent(self, env: dict[str, str | None] | None = None) -> None:
        run = self.run_leaving(env)
        self.assertEqual(self.reuse_lines(run), [], run.stdout)

    def assert_reads(self) -> None:
        planted = self.plant_stamp()
        self.forget_log()
        run = self.run_gate()
        self.assertEqual(self.checks(), [], run.stdout)
        self.assertEqual(len(self.reuse_lines(run)), 1, run.stdout)
        path = self.stamp_path()
        assert path is not None
        self.assertEqual(path.read_bytes(), planted)

    def fresh_repository(self, branch: str) -> None:
        """The project in a repository of its own with no commit yet, `HEAD` naming `branch`."""
        shutil.rmtree(self.repo / ".git")
        subprocess.run(["git", "init", "-q", "-b", branch], cwd=self.repo, check=True)
        for key, value in (("user.name", "t"), ("user.email", "t@local"), ("commit.gpgsign", "false")):
            git(self.repo, "config", key, value)


class CannotTellTest(TrunkTestCase):
    def test_a_trunk_named_develop_with_no_main_or_master_and_nothing_recorded_cannot_be_told(self) -> None:
        """C1, D83 item 7(b): the name the trunk resolves to (`main`) has no ref."""
        git(self.repo, "branch", "-m", "main", "develop")
        self.assert_cannot_tell()

    def test_the_same_run_on_the_trunk_is_told_too(self) -> None:
        """The order: cannot tell comes before the trunk, so a branch that is in fact the trunk says it as well."""
        git(self.repo, "branch", "-m", "main", "develop")
        git(self.repo, "checkout", "-q", "develop")
        self.assert_cannot_tell()

    def test_each_ci_branch_the_gate_cannot_use_is_told(self) -> None:
        """C4: not a string, not a branch name, a slice branch, another case, a branch this checkout has no ref for."""
        for value in (5, ["main"], "", "has space", "~tilde", "slice/S01-x", "Main", "no-such-branch",
                      "refs/heads/no-such-branch"):
            with self.subTest(value=value):
                self.record(value)
                self.assert_cannot_tell()

    def test_a_ci_that_is_not_an_object_is_told(self) -> None:
        self.record(ci="main")
        self.assert_cannot_tell()

    def test_a_recorded_branch_with_no_ref_where_main_has_one_is_told(self) -> None:
        """The trunk the gate resolves (`main`) is not the name recorded, whatever the reason."""
        self.record("develop")
        line = self.assert_cannot_tell()
        self.assertIn("develop", line)

    def test_a_project_json_that_is_missing_is_told(self) -> None:
        (self.repo / "project.json").unlink()
        line = self.assert_cannot_tell()
        self.assertIn("project.json", line)

    def test_a_project_json_that_is_not_an_object_or_not_json_is_told(self) -> None:
        for text in ("[]\n", '"main"\n', "7\n", "null\n", "{ not json\n", ""):
            with self.subTest(text=text):
                (self.repo / "project.json").write_text(text, encoding="utf-8")
                self.assertIn("project.json", self.assert_cannot_tell())


class SilentTest(TrunkTestCase):
    def test_an_unborn_master_reads_writes_and_says_nothing(self) -> None:
        """C1, D83 item 7(a): a `HEAD` that names no commit has no stamp, and nothing is said."""
        self.fresh_repository("master")
        run = self.run_gate()
        self.assertEqual(self.reuse_lines(run), [], run.stdout)
        self.assertTrue(self.checks())
        self.assertFalse((self.repo / ".git" / "slipwai").exists(), "a run before the first commit wrote under .git")

    def test_a_head_that_is_a_symbolic_ref_outside_refs_heads_reads_and_writes_nothing_and_says_nothing(self) -> None:
        """C5, D83 item 11: `refs/remotes/origin/topic` is no branch, so it is not taken for one that is not trunk."""
        git(self.repo, "update-ref", "refs/remotes/origin/topic", "HEAD")
        git(self.repo, "symbolic-ref", "HEAD", "refs/remotes/origin/topic")
        self.assert_silent()

    def test_the_order_a_ci_marker_comes_before_cannot_tell(self) -> None:
        (self.repo / "project.json").unlink()
        self.assert_silent({"CI": "1"})

    def test_the_order_a_detached_head_comes_before_cannot_tell(self) -> None:
        (self.repo / "project.json").unlink()
        git(self.repo, "checkout", "-q", "--detach")
        self.assert_silent()

    def test_the_order_an_unborn_head_comes_before_cannot_tell(self) -> None:
        self.fresh_repository("master")
        (self.repo / "project.json").write_text("[]\n", encoding="utf-8")
        run = self.run_gate()
        self.assertEqual(self.reuse_lines(run), [], run.stdout)
        self.assertFalse((self.repo / ".git" / "slipwai").exists())

    def test_the_order_a_non_branch_head_comes_before_cannot_tell(self) -> None:
        self.record("no-such-branch")
        git(self.repo, "update-ref", "refs/remotes/origin/topic", "HEAD")
        git(self.repo, "symbolic-ref", "HEAD", "refs/remotes/origin/topic")
        self.assert_silent()


class StampsStillTest(TrunkTestCase):
    """Holds: where the trunk can be told, nothing changes (D81 stands)."""

    def test_a_ci_branch_that_is_not_recorded_with_main_present_stamps(self) -> None:
        self.assert_reads()

    def test_a_ci_branch_that_is_null_is_not_recorded(self) -> None:
        self.record(None)
        self.assert_reads()

    def test_a_recorded_branch_spelled_with_refs_heads_that_has_a_ref_stamps(self) -> None:
        self.record("refs/heads/main")
        self.assert_reads()

    def test_a_trunk_named_develop_beside_a_stale_main_is_a_branch_like_any_other(self) -> None:
        """D81: `main` has a ref, so the trunk is told as `main`, and `develop` reads a stamp."""
        git(self.repo, "checkout", "-q", "-b", "develop")
        self.assert_reads()
