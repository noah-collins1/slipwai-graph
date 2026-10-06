"""The base is the trunk, or what `SINCE` names (S38 R2, AC-S38-2, -3, -4): the first line says which, and a base that
cannot be established runs every module.

The line is read from the output, the commit compared with from a probe of `select_tests.base`.
"""
from __future__ import annotations

import json
import sys

from select_fixture import SelectCase, git

sys.dont_write_bytecode = True

ALL = ["test_a", "test_b", "test_c"]
GO = "assets/languages/go/main.go"
PROBE = ("from select_tests import base, report\\n"
         "try:\\n"
         "    found = base.establish(__import__('pathlib').Path('.').resolve(), {env})\\n"
         "    print(json.dumps({{'commit': found.commit, 'line': found.line, 'name': found.name}}))\\n"
         "except report.Full as full:\\n"
         "    print(json.dumps({{'full': full.line}}))\\n")


class BaseCase(SelectCase):
    def short(self, commit: str) -> str:
        return git(self.repo, "rev-parse", "--short", commit).strip()

    def first_line(self, **env: str) -> str:
        done = self.selector(**env)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertEqual(self.modules_run(), ALL)
        lines = done.stdout.splitlines()
        return lines[0] if lines else ""

    def established(self, **env: str) -> dict[str, str]:
        done = self.probe(PROBE.replace("\\n", "\n").format(env=repr(env)))
        self.assertEqual(done.returncode, 0, done.stderr)
        found: dict[str, str] = json.loads(done.stdout)
        return found

    def slice_from(self, parent: str) -> str:
        """A slice branch cut from `parent` holding one go path; the commit it was cut from."""
        self.branch(parent)
        cut = git(self.repo, "rev-parse", "HEAD").strip()
        self.branch("slice/x")
        self.write(GO, "package main\n")
        self.commit("go")
        return cut


class TestTheTrunk(BaseCase):
    def test_a_slice_cut_from_main_is_compared_with_the_trunk(self) -> None:
        cut = self.slice_from("main")
        line = self.first_line()
        self.assertEqual(line, f"compared with `main` at {self.short(cut)} (the trunk)")

    def test_the_trunk_base_is_the_merge_base_commit(self) -> None:
        cut = self.slice_from("main")
        found = self.established()
        self.assertEqual(found["commit"], cut)
        self.assertEqual(found["name"], "main")

    def test_a_trunk_that_cannot_be_told_runs_every_module(self) -> None:
        self.slice_from("main")
        git(self.repo, "branch", "-m", "main", "elsewhere")
        self.write("project.json", '{"ci": {"branch": "develop"}}\n')
        line = self.first_line()
        self.assertEqual(line, "full: the trunk cannot be told — `ci.branch` names `develop`, which has no branch here")

    def test_a_trunk_that_cannot_be_told_and_names_nothing_still_says_so(self) -> None:
        self.slice_from("main")
        git(self.repo, "branch", "-m", "main", "elsewhere")
        self.assertTrue(self.first_line().startswith("full: the trunk cannot be told — "))


class TestSince(BaseCase):
    def test_since_is_compared_as_a_tree_and_the_line_says_whose_word_it_is(self) -> None:
        self.branch("adopt-method")
        self.write("assets/languages/java/x.txt", "adopted\n")
        adopted = self.commit("adopt")
        self.branch("slice/x")
        self.write(GO, "package main\n")
        self.commit("go")
        line = self.first_line(SINCE="adopt-method")
        self.assertEqual(line, f"compared with `adopt-method` at {self.short(adopted)}, named by SINCE — taken as "
                               "passing on the word of whoever named it")
        # a merge-base would be `main`'s commit, and the adoption would be part of the change
        self.assertEqual(self.established(SINCE="adopt-method")["commit"], adopted)
        self.assertNotEqual(self.established()["commit"], adopted)

    def test_since_names_what_a_branch_has_moved_on_from(self) -> None:
        self.slice_from("main")
        self.branch("main")
        self.write("README.md", "moved\n")
        moved = self.commit("main moved")
        self.branch("slice/x")
        self.assertEqual(self.established(SINCE="main")["commit"], moved)

    def test_a_ref_that_names_no_commit_runs_every_module(self) -> None:
        self.slice_from("main")
        line = self.first_line(SINCE="nonexistent")
        self.assertEqual(line, "full: SINCE=nonexistent could not be resolved — it names no commit")

    def test_a_ref_that_looks_like_an_option_is_not_a_ref(self) -> None:
        self.slice_from("main")
        line = self.first_line(SINCE="--all")
        self.assertEqual(line, "full: SINCE=--all could not be resolved — it names no commit")

    def test_a_ref_with_no_history_in_common_runs_every_module(self) -> None:
        self.slice_from("main")
        git(self.repo, "checkout", "-q", "--orphan", "unrelated")
        git(self.repo, "rm", "-rfq", ".")
        self.commit("another root")
        self.branch("slice/x")
        line = self.first_line(SINCE="unrelated")
        self.assertEqual(line, "full: SINCE=unrelated could not be resolved — it shares no history with HEAD")

    def test_since_never_turns_selection_on_where_the_branch_says_full(self) -> None:
        self.branch("adopt-method")
        self.assertEqual(self.first_line(SINCE="main"), "full: not a slice branch (`adopt-method`)")
        self.branch("slice/x")
        self.assertEqual(self.first_line(SINCE="main", CI="1"), "full: CI is set — a CI run is the full gate")
