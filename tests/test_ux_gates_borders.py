"""R8 e3 (AC-S07-11): where `check-ux-gates` cannot trust a slice's base it renders every preview, and says why in one
line — the first border that holds, in the order the scoped gate asks them — and what it opens on a slice branch.

Each example is a copy of `test_ux_gates_default`'s project, put in the state the border is about. What rendered is
read from `node`'s log, the line from what the script printed.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys

from test_ux_gates_default import EVERY, STYLES, GatesCase, commit_all, git, scoped_line
from test_verify_scoped_held import WRAPPER, findings_of
from test_verify_scoped_record import loaded

sys.dont_write_bytecode = True

EVERY_LINE = "check-ux-gates: every preview in scope — "


class BordersCase(GatesCase):
    def said_every(self, why: str, **env: str) -> str:
        """The script rendered every preview, and its one line began with `why`; the output."""
        said, previews, _ = self.gate(**env)
        self.assertEqual(previews, EVERY, said)
        lines = [line for line in said.splitlines() if line.startswith(EVERY_LINE)]
        self.assertEqual(len(lines), 1, said)
        self.assertTrue(lines[0].startswith(EVERY_LINE + why), lines[0])
        self.assertNotIn("previews scoped", said)
        return said

    def sliced(self) -> None:
        self.branch()
        self.edit(f"{STYLES}/linked.css")


class BorderTest(BordersCase):
    def test_e3_a_branch_that_is_no_slice_renders_every_preview(self) -> None:
        self.branch("feature/x")
        self.edit(f"{STYLES}/linked.css")
        self.said_every("`feature/x` is not a slice/<id> branch")

    def test_e3_a_detached_head_renders_every_preview(self) -> None:
        git(self.repo, "checkout", "-q", "--detach")
        self.said_every("HEAD is detached")

    def test_e3_an_unborn_head_renders_every_preview(self) -> None:
        git(self.repo, "checkout", "-q", "--orphan", "slice/S1")
        self.said_every("HEAD names no commit")

    def test_e3_a_ci_marker_renders_every_preview_and_names_it(self) -> None:
        self.sliced()
        self.said_every("CI is set, so this is a CI run", CI="1")
        self.said_every("GITHUB_ACTIONS is set, so this is a CI run", GITHUB_ACTIONS="true")

    def test_e3_a_checkout_with_no_main_has_no_usable_base(self) -> None:
        self.sliced()
        git(self.repo, "branch", "-D", "main")
        self.said_every("no usable base: slice/S1 has no `main` to compare with")

    def test_e3_a_trunk_that_cannot_be_told_renders_every_preview(self) -> None:
        self.sliced()
        record = json.loads((self.repo / "project.json").read_text(encoding="utf-8"))
        record["ci"] = {"branch": "slice/S9"}
        (self.repo / "project.json").write_text(json.dumps(record), encoding="utf-8")
        self.said_every("the trunk cannot be told — ")

    def test_e3_an_index_the_stamp_will_not_vouch_for_renders_every_preview(self) -> None:
        self.sliced()
        git(self.repo, "update-index", "--skip-worktree", f"{STYLES}/deep.css")
        self.said_every(f"{STYLES}/deep.css is marked skip-worktree, so git does not look at it")

    def test_e3_a_remote_with_no_origin_trunk_renders_every_preview(self) -> None:
        self.sliced()
        git(self.repo, "remote", "add", "origin", str(self.scratch / "nowhere.git"))
        self.said_every("there is a remote but no `origin/main` to say which of `main`'s commits were pushed")

    def test_e3_a_project_that_is_not_the_top_of_its_repository_renders_every_preview(self) -> None:
        outer = self.scratch / "outer"
        shutil.copytree(self.repo, outer / "project", ignore=shutil.ignore_patterns(".git"))
        subprocess.run(["git", "init", "-q", "-b", "main", str(outer)], check=True, timeout=60)
        commit_all(outer, "the project, below the top")
        git(outer, "checkout", "-q", "-b", "slice/S1")
        self.repo = outer / "project"
        self.edit(f"{STYLES}/linked.css")
        self.said_every("the project is not the repository's top")

    def test_e3_a_checkout_the_scripts_cannot_read_renders_every_preview_and_says_so(self) -> None:
        self.sliced()
        (self.repo / "scripts/verify-stamp.py").write_text("def broken(:\n", encoding="utf-8")
        self.said_every("the slice's base could not be read (")

    def test_e3_only_the_first_border_that_holds_is_said(self) -> None:
        self.branch("feature/x")
        self.said_every("CI is set, so this is a CI run", CI="1")

    def test_a_forced_gate_and_make_state_are_not_borders_here(self) -> None:
        self.sliced()
        said, previews, _ = self.gate(VERIFY_FORCE="1", MAKEFLAGS="n")
        self.assertEqual(previews, {"linked.html"}, said)
        self.assertIn("previews scoped to what changed since", said)


class MakeTargetTest(BordersCase):
    """T018 (D192, AC-S07-9): `make check-ux-gates`, the generated Makefile's target, scopes on a slice branch too."""

    def make_target(self, **env: str) -> str:
        installed = self.repo / "node_modules/.package-lock.json"  # newer than the manifests: no `npm ci` to run
        installed.parent.mkdir(exist_ok=True)
        installed.touch()
        done = subprocess.run(["make", "--no-print-directory", "check-ux-gates"], cwd=self.repo, text=True,
                              capture_output=True, env=self.environment(**env), timeout=300)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        return done.stdout

    def test_make_check_ux_gates_on_a_slice_branch_prints_the_default_scope_line(self) -> None:
        self.branch()
        short = git(self.repo, "rev-parse", "--short", "main").strip()
        self.edit(f"{STYLES}/linked.css")
        said = self.make_target()
        self.assertIn(scoped_line("slice/S1", short), said.splitlines(), said)
        self.assertEqual(sorted(self.opened()), ["linked.html"], said)

    def test_make_check_ux_gates_on_the_trunk_renders_every_preview(self) -> None:
        said = self.make_target()
        self.assertNotIn("previews scoped", said)
        self.assertEqual(self.opened(), EVERY, said)

    def opened(self) -> set[str]:
        calls = self.log.read_text(encoding="utf-8").splitlines() if self.log.exists() else []
        return {line.split("apps/web/screens/", 1)[1].split(" --dark")[0] for line in calls
                if "apps/web/screens/" in line and ".html" in line}


class OpensTest(BordersCase):
    """What the script opens, lists and stats on a slice branch lies under its recorded inputs, `project.json`,
    `scripts/` or git's own directory (research R-6): the audit wrapper is `test_verify_scoped_held`'s."""

    def run_audited(self) -> list[list[str]]:
        wrapper, shim, log = self.scratch / "wrapper.py", self.scratch / "bin" / "python3", self.scratch / "audit.log"
        shim.parent.mkdir()
        wrapper.write_text(WRAPPER, encoding="utf-8")
        shim.write_text(f'#!/bin/sh\nexec {sys.executable} -B {wrapper} "$@"\n', encoding="utf-8")
        shim.chmod(0o755)
        env = self.environment(AUDIT_LOG=str(log))
        env["PATH"] = f"{shim.parent}{os.pathsep}{env['PATH']}"
        done = subprocess.run(["python3", "scripts/check-ux-gates.py"], cwd=self.repo, env=env, text=True,
                              capture_output=True, timeout=300)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertIn("previews scoped to what changed since", done.stdout)
        return [event for each in log.read_text(encoding="utf-8").splitlines() for event in json.loads(each)]

    def test_a_slice_branch_opens_only_what_its_row_or_the_full_gate_names(self) -> None:
        self.sliced()
        files = loaded(self.repo)["checks"]["check-ux-gates"]["inputs"]["files"]
        events = self.run_audited()
        self.assertTrue(any(path.startswith("apps/web/") for _, path in events), "the previews were read")
        self.assertEqual(findings_of(self.repo, events, files), [])

    def sliced(self) -> None:
        super().sliced()
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "a stylesheet")
        self.edit(f"{STYLES}/deep.css")
