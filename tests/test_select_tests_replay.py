"""A dry run replays a range of commits (S38 R8 second half, AC-S38-15): `--dry-run --replay <base>..<tip>` takes the
change set from that range of commits instead of the working tree and the branch rules, and selects over the current
tree's declarations. Nothing is run.
"""
from __future__ import annotations

import sys

from select_fixture import git
from select_fixture_declare import GO, DeclarationCase

sys.dont_write_bytecode = True

TOOLKIT = "assets/toolkit/scripts/x.py"


class ReplayCase(DeclarationCase):
    def history(self) -> tuple[str, str, str]:
        """Declared modules on the trunk, then a go path (commit one), then a toolkit path (commit two)."""
        self.declare(test_a='{"configurations": {"backend": ["go"]}}',
                     test_b='{"configurations": {"backend": ["python"]}}', test_c="", test_d='{"reads": ["README.md"]}')
        self.write("README.md", "read\n")
        start = self.commit("declarations")
        self.write(GO, "package main\n")
        one = self.commit("go")
        self.write(TOOLKIT, "x = 1\n")
        two = self.commit("toolkit")
        return start, one, two

    def replay(self, span: str, **env: str) -> list[str]:
        done = self.selector_merged("--dry-run", "--replay", span, **env)
        self.assertEqual(done.returncode, 0, done.stdout)
        self.assertEqual(self.ran(), [], "a dry run runs nothing")
        return done.stdout.splitlines()

    def short(self, commit: str) -> str:
        return git(self.repo, "rev-parse", "--short", commit).strip()


class TestAReplayedRange(ReplayCase):
    def test_a_go_commit_and_then_a_toolkit_commit_select_what_both_paths_reach(self) -> None:
        start, _, two = self.history()
        lines = self.replay(f"{start}..{two}")
        short = self.short(start)
        # the toolkit script reaches every configuration, so `test_b` (python) runs and nothing is narrowed
        self.assertEqual(lines, [f"compared with `{start}` at {short}, replaying `{start}..{two}`",
                                 "skipped test_d: reads no configuration",
                                 f"selected 3 of 4 modules against `{start}` at {short}"])

    def test_the_first_commit_alone_is_a_go_change_only(self) -> None:
        start, one, _ = self.history()
        lines = self.replay(f"{start}..{one}")
        left_out = "(java-quarkus, java-spring, python, typescript unaffected)"
        self.assertEqual(lines[1:-1], ["skipped test_b: reads no go configuration",
                                       "skipped test_d: reads no go configuration",
                                       f"narrowed test_a: backend go only {left_out}"])
        self.assertEqual(lines[-1], f"selected 2 of 4 modules against `{start}` at {self.short(start)}")

    def test_the_branch_rules_do_not_apply_and_the_working_tree_is_not_the_change(self) -> None:
        start, one, _ = self.history()
        self.write("docs/untracked.md", "not in the range\n")
        lines = self.replay(f"{start}..{one}")
        self.assertFalse([line for line in lines if line.startswith("full:")], lines)

    def test_it_selects_over_the_current_trees_declarations(self) -> None:
        start, one, _ = self.history()
        self.write("tests/test_b.py", "TEST_SELECTION = {'configurations': {'backend': ['go']}}\n"
                   + (self.repo / "tests/test_b.py").read_text(encoding="utf-8").split("\n", 1)[1])
        lines = self.replay(f"{start}..{one}")
        self.assertNotIn("skipped test_b: reads no go configuration", lines)

    def test_a_range_that_touches_the_catalog_prints_the_full_line(self) -> None:
        start, _, _ = self.history()
        self.write("catalog.json", (self.repo / "catalog.json").read_text(encoding="utf-8") + "\n")
        tip = self.commit("catalog")
        self.assertEqual(self.replay(f"{start}..{tip}"),
                         ["full: `catalog.json` changed — the catalog: its effect cannot be established"])

    def test_a_range_that_cannot_be_read_says_so_and_exits_zero(self) -> None:
        self.history()
        for span in ("nonexistent..main", "main", "main...main", "..main", "main.."):
            with self.subTest(span=span):
                lines = self.replay(span)
                self.assertEqual(len(lines), 1, lines)
                self.assertTrue(lines[0].startswith("full: the change set cannot be established — "), lines)

    def test_the_environment_that_makes_a_run_whole_still_does(self) -> None:
        start, one, _ = self.history()
        self.assertEqual(self.replay(f"{start}..{one}", FULL="1"), ["full: FULL=1 given"])

    def test_it_needs_a_dry_run(self) -> None:
        start, one, _ = self.history()
        done = self.selector_merged("--replay", f"{start}..{one}")
        self.assertEqual(done.returncode, 2)
        self.assertEqual(self.ran(), [])
