"""The change set is the scoped gate's (S38 R3, AC-S38-5, -10): its own functions, loaded as they ship, plus what git
ignores. A change set that cannot be established runs every module.

The set is read from a probe of `select_tests.base.change_set`; the D153 and `Span` words are taken from the scoped
gate's own functions, run by a probe in the same repository, never re-typed here.
"""
from __future__ import annotations

import json
import shutil
import stat
import sys
from pathlib import Path

from select_fixture import SelectCase, git

sys.dont_write_bytecode = True

ALL = ["test_a", "test_b", "test_c"]
GO = "assets/languages/go/main.go"
SCRIPTS = "assets/toolkit/scripts/"
CHANGES = ("from select_tests import base\n"
           "root = __import__('pathlib').Path('.').resolve()\n"
           "found = base.change_set(root, base.establish(root, {env}))\n"
           "print(json.dumps({{'paths': found.paths, 'line': found.line}}))\n")
D153 = ("import importlib.util\n"
        "from select_tests import base\n"
        "root = __import__('pathlib').Path('.').resolve()\n"
        "scoped = base.load_scoped(root)\n"
        "start = base.trunk_base(root, scoped).commit\n"
        "span = scoped.changes.unpushed(scoped.scope, start)\n"
        "class Choice(__import__('typing').NamedTuple):\n"
        "    runs: bool\n"
        "    reason: str\n"
        "words = scoped.changes.unpushed_words([Choice(True, {path!r} + ' changed')], set(), span, scoped.scope)\n"
        "print(json.dumps({{'reason': words[0].reason, 'failure': span.failure, 'note': span.note}}))\n")
FAKE_GIT = ("#!/bin/sh\nfor a in \"$@\"; do\n"
            "  if [ \"$a\" = diff ]; then echo 'fatal: fake git cannot diff' >&2; exit 128; fi\n"
            "done\nexec {git} \"$@\"\n")


class ChangesCase(SelectCase):
    def exclude(self, *patterns: str) -> None:
        """Ignore `patterns` in this clone only, so no tracked file changes."""
        info = self.repo / ".git" / "info"
        info.mkdir(exist_ok=True)
        (info / "exclude").write_text("\n".join(patterns) + "\n", encoding="utf-8")

    def changes(self, **env: str) -> dict[str, object]:
        done = self.probe(CHANGES.format(env=repr(env)))
        self.assertEqual(done.returncode, 0, done.stderr)
        found: dict[str, object] = json.loads(done.stdout)
        return found

    def first_line(self, **env: str) -> str:
        done = self.selector(**env)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertEqual(self.modules_run(), ALL)
        lines = done.stdout.splitlines()
        return lines[0] if lines else ""

    def slice_branch(self) -> None:
        self.branch("slice/x")

    def give_the_trunk_an_unpushed_commit(self, path: str) -> None:
        scratch = self.repo.parent
        git(scratch, "init", "-q", "--bare", "origin.git")
        git(self.repo, "remote", "add", "origin", str(scratch / "origin.git"))
        git(self.repo, "push", "-q", "origin", "main")
        git(self.repo, "fetch", "-q", "origin")
        self.write(path, "unpushed\n")
        self.commit("not pushed")
        self.slice_branch()


class TestWhatTheGateCounts(ChangesCase):
    def test_an_untracked_new_file_is_a_change(self) -> None:
        self.slice_branch()
        self.write(GO, "package main\n")
        self.assertEqual(self.changes(SINCE="main")["paths"], [GO])
        self.assertTrue(self.first_line(SINCE="main").startswith("compared with `main` at "))

    def test_a_deleted_file_is_a_change(self) -> None:
        self.write(GO, "package main\n")
        self.commit("go on the trunk")
        self.slice_branch()
        (self.repo / GO).unlink()
        self.assertEqual(self.changes(SINCE="main")["paths"], [GO])

    def test_a_cache_under_the_tests_is_no_change(self) -> None:
        self.slice_branch()
        self.exclude("*.pyo")
        self.write(GO, "package main\n")
        self.write("tests/__pycache__/x.pyc", "x")
        self.write("tests/x.pyo", "x")
        self.write("assets/toolkit/__pycache__/y.cpython-314.pyc", "y")
        self.assertEqual(self.changes(SINCE="main")["paths"], [GO])
        self.assertTrue(self.first_line(SINCE="main").startswith("compared with `main` at "))

    def test_the_trunk_clause_of_an_unpushed_range_is_in_the_first_line(self) -> None:
        self.give_the_trunk_an_unpushed_commit("README.md")
        found = self.changes()
        self.assertEqual(found["paths"], ["README.md"])
        note = self.probe(D153.format(path="README.md"))
        self.assertEqual(note.returncode, 0, note.stderr)
        self.assertTrue(str(found["line"]).endswith("; " + json.loads(note.stdout)["note"]), found["line"])


class TestWhatCannotBeEstablished(ChangesCase):
    def test_an_unpushed_commit_that_touches_the_catalog_runs_every_module_in_d153s_words(self) -> None:
        self.give_the_trunk_an_unpushed_commit("catalog.json")
        words = self.probe(D153.format(path="catalog.json"))
        self.assertEqual(words.returncode, 0, words.stderr)
        reason = json.loads(words.stdout)["reason"]
        self.assertIn("nobody's push has gated", reason)
        self.assertTrue(self.first_line().startswith(f"full: {reason}"))

    def test_an_unpushed_range_that_cannot_be_walked_is_the_spans_own_failure(self) -> None:
        self.slice_branch()
        git(self.repo, "remote", "add", "origin", str(self.repo.parent / "nowhere.git"))
        failure = json.loads(self.probe(D153.format(path="x")).stdout)["failure"]
        self.assertIn("there is a remote but no `origin/main`", failure)
        self.assertEqual(self.first_line(), f"full: {failure}")

    def test_an_ignored_file_under_src_cannot_be_told_from_no_change(self) -> None:
        self.slice_branch()
        self.exclude("*.dat")
        self.write("src/data.dat", "x")
        self.write(GO, "package main\n")
        self.assertEqual(self.first_line(SINCE="main"),
                         "full: `src/data.dat` is a file git ignores — what it changes cannot be established")

    def test_an_ignored_file_outside_the_trees_the_suite_reads_is_no_change(self) -> None:
        self.slice_branch()
        self.exclude("*.dat")
        self.write("docs/data.dat", "x")
        self.write(GO, "package main\n")
        self.assertTrue(self.first_line(SINCE="main").startswith("compared with `main` at "))

    def test_scoped_gate_scripts_that_are_missing_run_every_module(self) -> None:
        self.slice_branch()
        (self.repo / SCRIPTS / "check-slice-scope.py").unlink()
        line = self.first_line(SINCE="main")
        self.assertTrue(line.startswith("full: the change set cannot be established — "), line)
        self.assertNotIn("\n", line)

    def test_a_package_that_will_not_load_runs_every_module(self) -> None:
        self.slice_branch()
        shutil.rmtree(self.repo / SCRIPTS / "verify_scoped")
        self.assertTrue(self.first_line(SINCE="main").startswith("full: the change set cannot be established — "))

    def test_git_failing_runs_every_module_and_says_what_git_said(self) -> None:
        self.slice_branch()
        bin_dir = self.repo.parent / "bin"
        bin_dir.mkdir()
        fake = bin_dir / "git"
        fake.write_text(FAKE_GIT.format(git=shutil.which("git")), encoding="utf-8")
        fake.chmod(fake.stat().st_mode | stat.S_IXUSR)
        path = f"{bin_dir}:{Path('/usr/bin')}:/bin"
        line = self.first_line(SINCE="main", PATH=path)
        self.assertEqual(line, "full: the change set cannot be established — fatal: fake git cannot diff")


class TestARootMakefileGitDoesNotSee(ChangesCase):
    """Make reads these three names whatever git says of them: any raw difference from the base is whole (T028)."""

    def whole(self, name: str) -> None:
        line = self.first_line(SINCE="HEAD")
        self.assertEqual(line, f"full: `{name}` changed — the root Makefile: its effect cannot be established")

    def test_a_makefile_edited_under_assume_unchanged_is_a_change(self) -> None:
        self.slice_branch()
        git(self.repo, "update-index", "--assume-unchanged", "Makefile")
        self.write("Makefile", (self.repo / "Makefile").read_text(encoding="utf-8") + "# edited\n")
        self.whole("Makefile")

    def test_a_makefile_edited_under_skip_worktree_is_a_change(self) -> None:
        self.slice_branch()
        git(self.repo, "update-index", "--skip-worktree", "Makefile")
        self.write("Makefile", (self.repo / "Makefile").read_text(encoding="utf-8") + "# edited\n")
        self.whole("Makefile")

    def test_an_ignored_gnumakefile_is_a_change(self) -> None:
        self.slice_branch()
        self.exclude("GNUmakefile")
        self.write("GNUmakefile", "include Makefile\n")
        self.whole("GNUmakefile")

    def test_an_ignored_lowercase_makefile_is_a_change(self) -> None:
        self.slice_branch()
        self.exclude("makefile")
        self.write("makefile", "include Makefile\n")
        self.whole("makefile")

    def test_a_makefile_that_lost_its_executable_bit_is_a_change(self) -> None:
        self.slice_branch()
        git(self.repo, "update-index", "--assume-unchanged", "Makefile")
        (self.repo / "Makefile").chmod(0o755)
        self.whole("Makefile")

    def test_an_untouched_makefile_is_no_change(self) -> None:
        self.slice_branch()
        self.write(GO, "package main\n")
        self.assertTrue(self.first_line(SINCE="HEAD").startswith("compared with `HEAD` at "))
