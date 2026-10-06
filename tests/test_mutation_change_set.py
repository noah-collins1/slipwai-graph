"""S08 T004 (rule 3 · AC-S08-7, -9, -10, -12): what changed, and how it is classified.

Real `git` in a generated project on `slice/S1`; the tool is a fake `Runner`; the declared services alone decide what
is a production file, so a Python or TypeScript service is declared on the Go project's tree.
"""
from __future__ import annotations

import subprocess

from mutation_scope_fixture import HEALTH, ScopeCase
from stamp_fixture import git
from test_mutation_borders import clean_environment
from test_mutation_sweeps import Recorded

TWO = ("go:apps/service", "go:apps/billing")


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


class UnlistedTest(Recorded):
    """T042 (A4, A8): a file git does not list as changed is a sweep cause; `SINCE` is resolved as git does."""

    def exclude(self, pattern: str) -> None:
        with (self.repo / ".git/info/exclude").open("a", encoding="utf-8") as handle:
            handle.write(pattern + "\n")

    def swept(self, *words: str) -> tuple[list[str], list[str], int]:
        status, lines, recording = self.run_recording(*(words or TWO))
        return recording.swept, lines, status

    def test_a4_an_ignored_production_file_under_a_service_sweeps_that_service(self) -> None:
        self.exclude("apps/service/health/ignored_gen.go")
        self.write("apps/service/health/ignored_gen.go")
        swept, lines, status = self.swept()
        said = "`apps/service/health/ignored_gen.go` is a path git ignores, so whether it changed cannot be told"
        self.assertEqual((swept, status), (["apps/service"], 0), lines)
        self.assertEqual(lines[0], f"mutation: the sweep runs — {said}", lines)
        self.assertIn(f"mutation: sweep apps/service — {said}", lines)
        self.assertNotIn("mutation: no mutant to run — no production file changed", lines)

    def test_a4_an_ignored_directory_of_sources_and_a_nested_repository_sweep_that_service(self) -> None:
        for name, make in (("an ignored directory", self.ignored_directory), ("a nested repository", self.nested)):
            with self.subTest(case=name):
                self.setUp()
                path = make()
                swept, lines, _ = self.swept()
                self.assertEqual(swept, ["apps/service"], lines)
                self.assertTrue(lines[0].startswith(f"mutation: the sweep runs — `{path}` is a "), lines)

    def ignored_directory(self) -> str:
        self.exclude("apps/service/gen/")
        self.write("apps/service/gen/x.go")
        return "apps/service/gen/"

    def nested(self) -> str:
        (self.repo / "apps/service/inner").mkdir()
        self.write("apps/service/inner/x.go")
        subprocess.run(["git", "init", "-q"], cwd=self.repo / "apps/service/inner", check=True, timeout=60)
        return "apps/service/inner/"

    def test_a4_hold_ignored_files_that_are_not_sources_or_are_dependencies_stay_scoped(self) -> None:
        for pattern, path in (("*.log", "apps/service/run.log"), ("vendor/", "apps/service/vendor/x/x.go"),
                              ("gremlins.json", "apps/service/gremlins.json")):
            with self.subTest(path=path):
                self.setUp()
                self.exclude(pattern)
                self.write(path)
                self.write("apps/billing/b.go")
                swept, lines, _ = self.swept()
                self.assertEqual(swept, [], lines)
                self.assertTrue(lines[0].startswith("mutation: scoped to 1 changed file(s)"), lines)

    def test_a8_since_resolves_as_git_resolves_it(self) -> None:
        git(self.repo, "checkout", "-q", "main")
        self.write("apps/service/config/marked.go")
        self.commit("marker commit")
        self.write("apps/service/config/later.go")
        self.commit("later")
        for ref in (":/marker commit", ":/marker"):
            with self.subTest(ref=ref):
                ran = self.run_in_process(env=clean_environment(SINCE=ref))
                self.assertEqual(ran.status, 0, ran.out)
                self.assertEqual(ran.first, f"mutation: scoped to 1 changed file(s) since `{ref}`: "
                                 "apps/service/config/later.go", ran.out)
        ran = self.run_in_process(env=clean_environment(SINCE=":/no commit says this"))
        self.assertEqual((ran.status, ran.runner.seen), (2, []))
        self.assertIn("names no commit", ran.first)


class StatesTest(ScopeCase):
    """T031 (G6): states that worked and had no example."""

    def base(self) -> str:
        """`main` with a marker commit and a later one that adds `config/later.go`; the slice is cut at the later one."""
        git(self.repo, "checkout", "-q", "main")
        self.write("apps/service/config/marked.go")
        self.commit("marker")
        marked = self.git_out("rev-parse", "HEAD")
        self.write("apps/service/config/later.go")
        self.commit("later")
        git(self.repo, "checkout", "-q", "-B", "slice/S1")
        return marked

    def test_a_unicode_path_with_a_space_is_scoped_as_named(self) -> None:
        name = "apps/service/health/café ünï.go"
        self.write(name)
        ran = self.run_in_process()
        self.assertEqual(ran.runner.seen, [("apps/service", ["health/café ünï.go"])], ran.out)
        self.assertTrue(ran.first.endswith(f": {name}"), ran.first)

    def test_a_since_as_a_tag_a_ref_name_a_full_or_short_hash_or_detached_with_ci_names_the_same_commit(self) -> None:
        marked = self.base()
        git(self.repo, "tag", "-a", "-m", "marker", "v-marker", marked)
        git(self.repo, "tag", "plain", marked)
        forms = ("v-marker", "refs/tags/v-marker", "plain", marked, marked[:8])
        for ref in forms:
            for extra in ({}, {"CI": "1"}):
                with self.subTest(ref=ref[:20], ci=bool(extra)):
                    ran = self.run_in_process(env=clean_environment(SINCE=ref, **extra))
                    self.assertEqual(ran.status, 0, ran.out)
                    self.assertEqual(ran.first, f"mutation: scoped to 1 changed file(s) since `{ref}`: "
                                     "apps/service/config/later.go", ran.out)
        git(self.repo, "checkout", "-q", "--detach")
        ran = self.run_in_process(env=clean_environment(SINCE="v-marker", CI="1"))
        self.assertEqual(ran.runner.seen, [("apps/service", ["config/later.go"])], ran.out)

    def test_a_a_rename_across_services_is_deleted_in_the_one_and_scoped_in_the_other(self) -> None:
        (self.repo / "apps/billing").mkdir(exist_ok=True)
        git(self.repo, "mv", HEALTH, "apps/billing/health.go")
        ran = self.run_in_process("go:apps/service", "go:apps/billing")
        self.assertIn(f"mutation: not mutated {HEALTH} — deleted, no mutants", ran.lines)
        self.assertEqual(ran.runner.seen, [("apps/billing", ["health.go"])], ran.out)
        self.assertIn("mutation: skip apps/service — no changed production file", ran.lines)
