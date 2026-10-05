"""S08 T004 (rule 3 · AC-S08-7, -9, -10, -12): what changed, and how it is classified.

Real `git` in a generated project on `slice/S1`; the tool is a fake `Runner`; the declared services alone decide what
is a production file, so a Python or TypeScript service is declared on the Go project's tree.
"""
from __future__ import annotations

from mutation_scope_fixture import HEALTH, ScopeCase
from stamp_fixture import git
from test_mutation_borders import clean_environment


class ChangeSetTest(ScopeCase):
    def test_e2_staged_unstaged_untracked_and_committed_files_are_all_in_the_set(self) -> None:
        self.write("apps/service/config/committed.go")
        self.commit()
        self.write("apps/service/config/staged.go")
        git(self.repo, "add", "apps/service/config/staged.go")
        (self.repo / "apps/service/health/health.go").write_text("package health\n// edited\n", encoding="utf-8")
        self.write("apps/service/config/untracked.go")
        ran = self.run_in_process()
        self.assertEqual(ran.runner.seen, [("apps/service", [
            "config/committed.go", "config/staged.go", "config/untracked.go", "health/health.go"])])
        self.assertEqual(ran.make_calls, [])

    def test_e3_only_tests_changed(self) -> None:
        self.write("apps/service/health/extra_test.go")
        ran = self.run_in_process()
        self.assertEqual(ran.first, "mutation: no mutant to run — only tests changed: "
                         "apps/service/health/extra_test.go; `make mutation-full` is the run that measures them")
        self.assertEqual((ran.status, ran.runner.seen, ran.make_calls), (0, [], []))

    def test_e3_only_non_source_files_changed(self) -> None:
        self.write("apps/service/README.md", "x\n")
        self.write("apps/service/go.mod", "module x\n")
        ran = self.run_in_process()
        self.assertEqual(ran.first, "mutation: no mutant to run — no production file changed")
        self.assertEqual((ran.status, ran.runner.seen, ran.make_calls), (0, [], []))

    def test_e3_only_a_deletion_is_named_and_nothing_runs(self) -> None:
        (self.repo / HEALTH).unlink()
        ran = self.run_in_process()
        self.assertIn(f"mutation: not mutated {HEALTH} — deleted, no mutants", ran.lines)
        self.assertEqual(ran.first, "mutation: no mutant to run — no production file changed")
        self.assertEqual((ran.status, ran.runner.seen, ran.make_calls), (0, [], []))

    def test_e4_a_shared_package_is_named_and_not_run(self) -> None:
        self.write("packages/greeting/greeting.go")
        ran = self.run_in_process()
        self.assertIn("mutation: not mutated packages/greeting/greeting.go — not mutated by this target", ran.lines)
        self.assertEqual((ran.status, ran.runner.seen), (0, []))

    def test_e4_a_renamed_file_is_deleted_at_the_old_path_and_scoped_at_the_new(self) -> None:
        git(self.repo, "mv", HEALTH, "apps/service/health/status.go")
        ran = self.run_in_process()
        self.assertIn(f"mutation: not mutated {HEALTH} — deleted, no mutants", ran.lines)
        self.assertEqual(ran.runner.seen, [("apps/service", ["health/status.go"])])

    def test_e5_since_scopes_on_any_checkout_ci_included(self) -> None:
        git(self.repo, "checkout", "-q", "main")
        self.write("apps/service/config/new.go")
        self.commit()
        for env in (clean_environment(SINCE="HEAD~1"), clean_environment(SINCE="HEAD~1", CI="1")):
            with self.subTest(ci="CI" in env):
                ran = self.run_in_process(env=env)
                self.assertTrue(ran.first.startswith("mutation: scoped to 1 changed file(s) since `HEAD~1`: "), ran.out)
                self.assertEqual(ran.runner.seen[-1], ("apps/service", ["config/new.go"]))
        self.assertEqual(self.run_in_process(env=clean_environment(SINCE="HEAD~1")).make_calls, [])

    def test_e5_since_includes_the_working_tree_and_untracked_files(self) -> None:
        (self.repo / HEALTH).write_text("package health\n// edited\n", encoding="utf-8")
        self.write("apps/service/config/untracked.go")
        ran = self.run_in_process(env=clean_environment(SINCE="main"))
        self.assertEqual(ran.runner.seen, [("apps/service", ["config/untracked.go", "health/health.go"])])

    def test_e5_an_unresolvable_since_fails_naming_it_and_runs_nothing(self) -> None:
        for ref in ("nope", "--upload-pack=x", "a`b"):
            with self.subTest(ref=ref):
                ran = self.run_in_process(env=clean_environment(SINCE=ref))
                self.assertEqual(ran.status, 2, ran.out)
                self.assertEqual(len(ran.lines), 1, ran.out)
                self.assertIn(ref.replace("`", "'"), ran.first)
                self.assertEqual((ran.runner.seen, ran.make_calls), ([], []))

    def test_e8_hold_a_slice_branch_with_no_change_is_no_production_file_not_a_sweep(self) -> None:
        """HOLD (teeth: make the empty set sweep)."""
        ran = self.run_in_process()
        self.assertEqual(ran.first, "mutation: no mutant to run — no production file changed")
        self.assertEqual((ran.status, ran.runner.seen, ran.make_calls), (0, [], []))
