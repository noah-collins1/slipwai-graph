"""R7 (AC-S03-21, -22, -24): where a stamp is never read, never written and never removed, and where it is.

A stamp planted for the tree as it stands (`plant_stamp`) would be reused by a run that may read it, so a run that
runs every check and leaves the planted bytes alone is one that did not read it, did not write and did not remove.
What such a run prints is what `make verify-checks` prints: the gate as it was, with none of the script's lines.
"""
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from stamp_fixture import StampTestCase, git
from support import FactoryTestCase
from test_candidates import adopted, slipwai


class WhereTest(StampTestCase):
    def checks_output(self, env: dict[str, str | None] | None = None) -> subprocess.CompletedProcess[str]:
        """The gate as it was before the stamp: the checks and the closing line, from `verify-checks`."""
        done = subprocess.run(["make", "verify-checks"], cwd=self.repo, env=self.environment(env), text=True,
                              capture_output=True, timeout=180)
        self.forget_log()
        return done

    def pending(self) -> list[Path]:
        return sorted((self.repo / ".git" / "slipwai").glob("*.pending"))

    def assert_untouched(self, env: dict[str, str | None] | None = None) -> None:
        """A planted stamp stands byte for byte, every check ran, and the run said what the gate says today."""
        planted = self.plant_stamp()
        path = self.stamp_path()
        assert path is not None
        expected = self.checks_output(env)
        run = self.run_gate(env)
        self.assertEqual(run.returncode, expected.returncode, run.stdout + run.stderr)
        self.assertTrue(self.checks(), "no check started: the stamp was read")
        self.assertEqual(self.reuse_lines(run), [])
        self.assertEqual(run.stdout, expected.stdout)
        self.assertEqual(path.read_bytes(), planted, "the stamp was written, replaced or removed")
        self.assertEqual(self.pending(), [], "a run that may not read a stamp left a note for one to be written")

    def assert_reads(self) -> None:
        planted = self.plant_stamp()
        self.forget_log()
        run = self.run_gate()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertEqual(self.checks(), [], "a check started on a tree whose stamp could be read")
        self.assertEqual(len(self.reuse_lines(run)), 1, run.stdout)
        path = self.stamp_path()
        assert path is not None
        self.assertEqual(path.read_bytes(), planted)

    def test_each_ci_marker_reads_and_writes_no_stamp_and_any_non_empty_value_is_one(self) -> None:
        """e21: `CI`, `GITHUB_ACTIONS`, `GITLAB_CI`; `CI=false` is a marker too."""
        for marker, value in (("CI", "true"), ("CI", "false"), ("GITHUB_ACTIONS", "true"), ("GITLAB_CI", "true")):
            with self.subTest(f"{marker}={value}"):
                self.assert_untouched({marker: value})

    def test_an_empty_marker_is_not_one(self) -> None:
        """e22's border: a marker that is set and empty is no CI run, as `check-codegraph` reads it."""
        self.plant_stamp()
        self.forget_log()
        run = self.run_gate({"CI": ""})
        self.assertEqual(self.checks(), [], run.stdout)
        self.assertEqual(len(self.reuse_lines(run)), 1, run.stdout)

    def test_the_trunk_reads_and_writes_no_stamp(self) -> None:
        """e21: `main`, the trunk where `project.json` records none and `main` has a ref."""
        git(self.repo, "checkout", "-q", "main")
        self.assert_untouched()

    def test_master_is_the_trunk_where_there_is_no_main(self) -> None:
        """e21 (D33): with no `main` ref, `master` is the trunk."""
        git(self.repo, "branch", "-m", "main", "master")
        git(self.repo, "checkout", "-q", "master")
        self.assert_untouched()

    def test_master_beside_a_main_is_not_the_trunk(self) -> None:
        """e22 (D33): `main` has a ref, so a `master` made beside it is a branch like any other and reads a stamp."""
        git(self.repo, "checkout", "-q", "-b", "master")
        self.assert_reads()

    def test_the_recorded_trunk_is_the_trunk_and_main_is_then_a_branch(self) -> None:
        """e21, e22 (D30): `ci.branch` in `project.json`, where it has a ref, is the trunk."""
        record = self.repo / "project.json"
        document = json.loads(record.read_text(encoding="utf-8"))
        document.setdefault("ci", {})["branch"] = "develop"
        record.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
        git(self.repo, "checkout", "-q", "-b", "develop")
        self.assert_untouched()
        git(self.repo, "checkout", "-q", "main")
        self.assert_reads()

    def test_a_detached_head_reads_and_writes_no_stamp(self) -> None:
        """e21: no branch is checked out."""
        git(self.repo, "checkout", "-q", "--detach")
        self.assert_untouched()

    def test_every_other_branch_reads_the_stamp(self) -> None:
        """e22: `slice/<id>`, a topic branch and this run's `adopt-method`."""
        for name in ("slice/S01-x", "fix/y", "adopt-method"):
            with self.subTest(name):
                git(self.repo, "checkout", "-q", "-b", name)
                self.assert_reads()


class WrappedTest(FactoryTestCase):
    def test_the_gate_of_a_wrapped_application_has_no_stamp_step(self) -> None:
        """e24: the generated rule neither reads nor writes a stamp, and the refusal stands in unchanged. (The rule's
        own text is pinned byte for byte in `test_verify_stamp_pinned`.)"""
        with tempfile.TemporaryDirectory() as directory:
            repo = adopted(Path(directory))
            refusing = (repo / "delivery/Makefile").read_text(encoding="utf-8")
            self.assertNotIn("verify-stamp", refusing)
            self.assertEqual(slipwai(repo, "adopt", "--confirm", "shop").returncode, 0)
            gate = (repo / "delivery/Makefile").read_text(encoding="utf-8")
            self.assertNotIn("verify-stamp", gate)
            self.assertNotIn("VERIFY_STAMP", gate)
