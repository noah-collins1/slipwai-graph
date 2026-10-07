"""T026 (R4, R7 · AC-S06-5, -8, -9; D125): every part of the stamp's key is compared by the selection.

The stamp's key holds every file git ignores under the project, but for the closed list `EXEMPT` leaves out, because
a check reads some: `.env` (Vite and Vitest load it), `node_modules/.package-lock.json`, the UX kit under
`tools/ux-gates/`, a test file `.git/info/exclude` hides. The selection reads changed paths, which never name an ignored
file, so the baseline holds the key's `ignored` digest and a scoped run that finds the tree's different is the full
gate.
"""
from __future__ import annotations

import importlib
import json
import subprocess
import sys

from scoped_fixture import FULL, LINE, ShapeCase
from stamp_fixture import git

from slipwai.assets import ROOT

sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "assets" / "toolkit" / "scripts"))

DRY: dict[str, str | None] = {"STANDIN_DRY": "1"}
DIFFERS = FULL + "a file git ignores differs from the baseline"
HINT = LINE + ("you may have edited one, or a check written one; `git status --ignored` shows it, and the next run "
               "records")
NO_BASELINE = LINE + "no usable baseline (it cannot be read) — every check that reads a tool or a variable runs"
# Each part of the key and what the selection compares it by: the changed paths (`check-slice-scope.changed_files`),
# the gate's own files (D117 rule 4, `choose.unknown`), the base and the branch (the borders), or the baseline.
BY_PATHS = {"files": "changed_files", "index": "changed_files"}
BY_GATE_SCRIPTS = {"scripts": "choose.unknown"}
BY_THE_BASE = {"history": "the base and branch borders"}
READ = """
import importlib.util, json, sys
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location("stamp", "scripts/verify-stamp.py")
stamp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stamp)
key, parts = stamp.key_parts({})
print(json.dumps(sorted((set(key) - {"key", "tree"}) | set(parts))))
"""


class IgnoredTest(ShapeCase):
    shape = "model-typescript-web"

    def assert_full(self, run: subprocess.CompletedProcess[str]) -> None:
        self.assertEqual(self.scoped_lines(run), [DIFFERS, HINT], run.stdout + run.stderr)
        self.assertEqual(len(self.verify_calls()), 1, "`make verify` was not run exactly once")
        self.assertEqual(self.called(), [["verify-checks"]], "a selection was made as well as the full gate")

    def test_e1_an_env_file_and_the_installed_manifest_make_the_run_the_full_gate(self) -> None:
        self.edit("apps/web/.env", "VITE_API=http://elsewhere\n")
        self.edit("node_modules/.package-lock.json", '{"changed": true}\n')
        self.assertEqual(git(self.repo, "status", "--porcelain").strip(), "", "a file git does not ignore changed")
        self.assert_full(self.scoped(DRY))

    def test_e1_each_of_the_named_ignored_files_alone_is_enough(self) -> None:
        for path in ("apps/web/.env", "tools/ux-gates/probe.js", "skills/ui-ux-pro-max/probe.md",
                     "node_modules/.package-lock.json"):
            with self.subTest(path=path):
                self.edit(path, "moved\n")
                self.assertIn("!!", git(self.repo, "status", "--porcelain", "--ignored", "--", path))
                self.assert_full(self.scoped(DRY))
                (self.repo / path).unlink()
                self.forget_log()

    def test_e1_a_test_file_the_exclude_list_hides_is_one_too(self) -> None:
        with (self.repo / ".git" / "info" / "exclude").open("a", encoding="utf-8") as handle:
            handle.write("apps/web/src/hidden.test.ts\n")
        self.edit("apps/web/src/hidden.test.ts", "test('x', () => {});\n")
        self.assert_full(self.scoped(DRY))

    def test_e2_hold_an_ignored_file_the_stamp_leaves_out_selects_nothing(self) -> None:
        """HOLD (teeth: compare another digest than the stamp's, and each is the full gate): `dist/`, `coverage/`, a
        cache under `node_modules/` and `.build/` are written by the gate itself and read by no check."""
        for path in ("apps/web/dist/probe.js", "apps/web/coverage/probe.json", "node_modules/.cache/probe",
                     ".build/probe"):
            self.edit(path, "moved\n")
            self.assertIn("!!", git(self.repo, "status", "--porcelain", "--ignored", "--", path), path)
        run = self.scoped(DRY)
        said = self.scoped_lines(run)
        self.assertFalse([line for line in said if line.startswith(FULL)], said)
        ran, skipped = self.decided(run)
        self.assertTrue({"lint-web", "typecheck-web", "test-service", "check-styles"} <= set(skipped), (ran, skipped))
        self.assertEqual(self.verify_calls(), [])

    def test_e4_a_baseline_without_the_ignored_part_is_not_one(self) -> None:
        path = self.baseline_file()
        kept = {key: value for key, value in json.loads(path.read_text(encoding="utf-8")).items() if key != "ignored"}
        path.write_text(json.dumps(kept), encoding="utf-8")
        self.assertEqual(self.scoped_lines(self.scoped(DRY)), [NO_BASELINE, FULL + "every check was chosen"])
        self.assertEqual(len(self.verify_calls()), 1)

    def test_e3_every_part_of_the_key_is_compared_by_something(self) -> None:
        done = subprocess.run([sys.executable, "-B", "-c", READ], cwd=self.repo, check=True, capture_output=True,
                              text=True, timeout=120)
        parts = set(json.loads(done.stdout))
        choose = importlib.import_module("verify_scoped.choose")
        by_the_baseline = set(choose.Drift._fields)
        mapped = [set(BY_PATHS), set(BY_GATE_SCRIPTS), set(BY_THE_BASE), by_the_baseline]
        self.assertEqual(parts, {"files", "scripts", "index", "history", "ignored", "variables", "tools"})
        self.assertEqual(set().union(*mapped), parts, "a part of the key is compared by nothing")
        self.assertEqual(sum(len(each) for each in mapped), len(parts), "a part is mapped twice")
