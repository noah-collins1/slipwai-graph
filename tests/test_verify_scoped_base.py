"""T050 (adversary A2 · D153): a skip relies only on a commit `origin/<trunk>` carries.

`check-slice-scope.merge_base()` takes the newer of the merge-bases with local `main` and `origin/main`, so commits
on a local `main` that nobody gated, merged into the slice, became the base, and the gate never checked what they
broke. The files they changed count as changed, as the slice's own do; where that range cannot be established the
full gate runs; with no remote at all the local trunk is the base, as D117 had it.
"""
from __future__ import annotations

import subprocess
import sys

from scoped_fixture import FULL, LINE, SLICE, ShapeCase
from stamp_fixture import git

sys.dont_write_bytecode = True

DRY: dict[str, str | None] = {"STANDIN_DRY": "1"}
BREAKS: dict[str, str | None] = {"STANDIN_NPM_FAIL": "apps/web run lint"}
EXTRA = "apps/web/src/extra.ts"
FETCH = "git fetch origin refs/heads/main:refs/remotes/origin/main"
NO_REF = ("there is a remote but no `origin/main` to say which of `main`'s commits were pushed; run `" + FETCH
          + "` to scope again")


class BaseTest(ShapeCase):
    shape = "model-typescript-web"

    def remote(self, name: str = "origin", push: bool = True) -> None:
        """A remote the project has: a bare repository beside it, with `main` pushed to it unless `push` is off."""
        bare = self.repo.parent / "remote.git"
        subprocess.run(["git", "init", "-q", "--bare", str(bare)], check=True, capture_output=True)
        git(self.repo, "remote", "add", name, str(bare))
        if push:
            git(self.repo, "push", "-q", name, "main")

    def on_main(self, *changes: tuple[str, str | None]) -> None:
        """One commit on the local `main` for each (path, text) — a text of None removes the path — then merged into
        the slice, which is what makes the local trunk the base. The baseline is taken again on the merged branch."""
        git(self.repo, "checkout", "-q", "main")
        for path, text in changes:
            if text is None:
                git(self.repo, "rm", "-q", path)
            else:
                (self.repo / path).parent.mkdir(parents=True, exist_ok=True)
                (self.repo / path).write_text(text, encoding="utf-8")
                git(self.repo, "add", path)
            git(self.repo, "commit", "-q", "-m", "a commit nobody pushed")
        git(self.repo, "checkout", "-q", SLICE)
        git(self.repo, "merge", "-q", "--no-edit", "main")
        self.write_baseline()

    def short(self, ref: str) -> str:
        return git(self.repo, "rev-parse", "--short", ref).strip()

    def said(self, ref: str = "main") -> str:
        return (f"`main` at {self.short(ref)} has 1 commits `origin/main` at {self.short('origin/main')} does not, "
                "and every file they changed counts as changed")

    def test_e1_a_file_on_an_unpushed_trunk_commit_selects_its_check_with_the_words_and_the_run_fails(self) -> None:
        self.remote()
        self.on_main((EXTRA, "export const unused = 1\n"))
        run = self.scoped(BREAKS)
        ran, _ = self.decided(run)
        origin = self.short("origin/main")
        self.assertEqual(ran.get("lint-web"),
                         f"{EXTRA} changed on `main` since `origin/main` at {origin}, which nobody's push has gated",
                         run.stdout + run.stderr)
        self.assertNotEqual(run.returncode, 0, run.stdout)
        self.assertIn("compared with `main` at ", self.scoped_lines(run)[-1])
        self.assertIn("; " + self.said(), self.scoped_lines(run)[-1])

    def test_e2_a_remote_with_no_origin_main_is_the_full_gate_and_names_the_fetch(self) -> None:
        self.remote(push=False)
        self.on_main((EXTRA, "export const unused = 1\n"))
        run = self.scoped(DRY)
        self.assertEqual(self.scoped_lines(run), [FULL + NO_REF], run.stdout + run.stderr)
        self.assertEqual(len(self.verify_calls()), 1)

    def test_e2_a_remote_under_another_name_is_the_same_and_prints_no_fetch(self) -> None:
        self.remote("upstream", push=False)
        self.on_main((EXTRA, "export const unused = 1\n"))
        run = self.scoped(DRY)
        said = "there is a remote but no `origin/main` to say which of `main`'s commits were pushed"
        self.assertEqual(self.scoped_lines(run), [FULL + said], run.stdout + run.stderr)

    def test_e3_with_no_remote_the_local_trunk_is_the_base_and_a_merged_file_is_not_added(self) -> None:
        self.on_main((EXTRA, "export const unused = 1\n"))
        run = self.scoped(DRY)
        ran, skipped = self.decided(run)
        self.assertIn("lint-web", skipped, run.stdout + run.stderr)
        self.assertNotIn("lint-web", ran)
        self.assertNotIn("does not, and every file", run.stdout)

    def test_e4_with_origin_main_level_with_local_main_nothing_is_added(self) -> None:
        self.remote()
        self.on_main((EXTRA, "export const unused = 1\n"))
        git(self.repo, "push", "-q", "origin", "main")
        run = self.scoped(DRY)
        ran, skipped = self.decided(run)
        self.assertIn("lint-web", skipped, run.stdout + run.stderr)
        self.assertNotIn("does not, and every file", run.stdout)

    def test_e4_with_origin_main_ahead_of_local_main_nothing_is_added(self) -> None:
        self.remote()
        self.on_main((EXTRA, "export const unused = 1\n"))
        git(self.repo, "push", "-q", "origin", "main")
        git(self.repo, "checkout", "-q", "main")
        git(self.repo, "commit", "-q", "--allow-empty", "-m", "ahead")
        git(self.repo, "push", "-q", "origin", "main")
        git(self.repo, "reset", "-q", "--hard", "HEAD~1")
        git(self.repo, "checkout", "-q", SLICE)
        run = self.scoped(DRY)
        ran, skipped = self.decided(run)
        self.assertIn("lint-web", skipped, run.stdout + run.stderr)
        self.assertNotIn("does not, and every file", run.stdout)

    def test_e5_an_unpushed_project_json_is_the_full_gate_through_the_gate_files_rule(self) -> None:
        self.remote()
        self.on_main(("project.json", (self.repo / "project.json").read_text(encoding="utf-8") + "\n"))
        run = self.scoped(DRY)
        lines = self.scoped_lines(run)
        self.assertTrue(lines[0].startswith(LINE + "dependency knowledge was incomplete for project.json"), lines)
        self.assertTrue(any(line.startswith(FULL) for line in lines), lines)

    def test_e6_a_file_added_then_reverted_within_the_unpushed_range_still_selects_its_check(self) -> None:
        self.remote()
        self.on_main((EXTRA, "export const unused = 1\n"), (EXTRA, None))
        self.assertFalse((self.repo / EXTRA).exists())
        ran, _ = self.decided(self.scoped(DRY))
        self.assertIn("lint-web", ran)
        self.assertIn("changed on `main` since `origin/main`", ran["lint-web"])

    def test_e7_a_failed_diff_is_the_full_gate_naming_why(self) -> None:
        self.remote()
        self.on_main((EXTRA, "export const unused = 1\n"))
        # a remote-tracking ref whose history shares nothing with the branch: no merge-base, so no range
        empty = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"  # the empty tree
        orphan = git(self.repo, "commit-tree", empty, "-m", "orphan").strip()
        git(self.repo, "update-ref", "refs/remotes/origin/main", orphan)
        run = self.scoped(DRY)
        first = self.scoped_lines(run)[0]
        self.assertTrue(first.startswith(FULL), run.stdout + run.stderr)
        self.assertIn("has commits `origin/main` does not, and what they changed cannot be established: ", first)
