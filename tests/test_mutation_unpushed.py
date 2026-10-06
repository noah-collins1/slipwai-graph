"""S08 T035(c) (D153): a trunk commit the forge's trunk does not carry counts as changed for `make mutation` too.

Real `git` with a real bare remote in a temp directory, on the generated Go project's `slice/S1`; the tool is a fake
`Runner`. The rule is S06's, `verify_scoped.changes.unpushed`, reached through the loaded `verify-scoped` module.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

from mutation_scope_fixture import HEALTH, SLICE, ScopeCase
from stamp_fixture import git
from test_mutation_borders import FULL, clean_environment, loaded

SWEEPS = "mutation: the sweep runs — "


class UnpushedTrunkTest(ScopeCase):
    def remote(self, push: bool) -> Path:
        """A bare remote named `origin`; `main` is pushed to it where `push` says so."""
        self.fit_recipe(("go:apps/service",))  # the base the examples share, so only the file below is anyone's change
        bare = self.repo.parent / "origin.git"
        subprocess.run(["git", "init", "-q", "--bare", str(bare)], check=True, capture_output=True, timeout=60)
        git(self.repo, "remote", "add", "origin", str(bare))
        if push:
            git(self.repo, "push", "-q", "origin", "main")
            git(self.repo, "fetch", "-q", "origin")
        return bare

    def trunk_commit(self) -> None:
        """A commit on local `main` changing a production file; `slice/S1` is cut after it and changes nothing."""
        git(self.repo, "checkout", "-q", "main")
        (self.repo / HEALTH).write_text("package health\n// edited on main\n", encoding="utf-8")
        self.commit("main, unpushed")
        git(self.repo, "checkout", "-q", "-B", SLICE)

    def test_e1_a_file_changed_on_an_unpushed_trunk_commit_is_scoped(self) -> None:
        self.remote(push=True)
        self.trunk_commit()
        ran = self.run_in_process()
        self.assertEqual(ran.runner.seen, [("apps/service", ["health/health.go"])], ran.out)
        self.assertEqual(ran.make_calls, [])
        self.assertIn("has 1 commits `origin/main`", ran.first)
        self.assertEqual(ran.status, 0, ran.out)

    def test_e2_a_remote_with_no_origin_trunk_is_the_sweep_with_s06s_words(self) -> None:
        self.remote(push=False)
        self.trunk_commit()
        module = loaded(self.repo / "scripts/mutation-scope.py")
        os.chdir(self.repo)
        self.addCleanup(os.chdir, Path(__file__).parent)
        where = module.ground()
        said = module.scoped_gate().changes.unpushed(where.scope, where.scope.merge_base().commit).failure
        self.assertIn("there is a remote but no `origin/main`", str(said))
        ran = self.run_in_process()
        self.assertEqual(ran.first, SWEEPS + str(said), ran.out)
        self.assertEqual((ran.make_calls, ran.runner.seen), ([FULL], []))

    def test_e3_with_no_remote_the_local_trunk_is_the_base_as_it_was(self) -> None:
        self.fit_recipe(("go:apps/service",))
        self.trunk_commit()
        ran = self.run_in_process()
        self.assertEqual(ran.first, "mutation: no mutant to run — no production file changed", ran.out)
        self.assertEqual((ran.make_calls, ran.runner.seen), ([], []))

    def test_e4_an_explicit_since_stays_a_diff_from_that_ref(self) -> None:
        self.remote(push=False)  # the remote that would be the sweep without SINCE
        self.trunk_commit()
        ran = self.run_in_process(env=clean_environment(SINCE="main"))
        self.assertEqual(ran.first, "mutation: no mutant to run — no production file changed", ran.out)
        self.assertEqual((ran.make_calls, ran.runner.seen), ([], []))

    def test_a6_a_file_an_unpushed_trunk_commit_deleted_is_named_deleted_and_is_not_scoped(self) -> None:
        self.remote(push=True)
        git(self.repo, "checkout", "-q", "main")
        git(self.repo, "rm", "-q", HEALTH)
        self.commit("main deletes, unpushed")
        git(self.repo, "checkout", "-q", "-B", SLICE)
        ran = self.run_in_process()
        self.assertIn(f"mutation: not mutated {HEALTH} — deleted, no mutants", ran.lines)
        self.assertEqual((ran.runner.seen, ran.make_calls, ran.status), ([], [], 0), ran.out)

    def test_a6_the_old_path_of_an_unpushed_rename_is_deleted_and_the_new_one_scoped(self) -> None:
        self.remote(push=True)
        git(self.repo, "checkout", "-q", "main")
        git(self.repo, "mv", HEALTH, "apps/service/health/status.go")
        self.commit("main renames, unpushed")
        git(self.repo, "checkout", "-q", "-B", SLICE)
        ran = self.run_in_process()
        self.assertIn(f"mutation: not mutated {HEALTH} — deleted, no mutants", ran.lines)
        self.assertEqual(ran.runner.seen, [("apps/service", ["health/status.go"])], ran.out)

    def test_a6_a_file_added_then_deleted_in_unpushed_commits_is_a_change_not_a_deletion_of_a_known_file(self) -> None:
        self.remote(push=True)
        git(self.repo, "checkout", "-q", "main")
        self.write("apps/service/health/flash.go")
        self.commit("main adds")
        git(self.repo, "rm", "-q", "apps/service/health/flash.go")
        self.commit("main removes it again")
        git(self.repo, "checkout", "-q", "-B", SLICE)
        ran = self.run_in_process()
        self.assertEqual((ran.runner.seen, ran.status), ([], 0), ran.out)
