"""R8 e9 and R9 (AC-S07-1's end-to-end half, AC-S07-11's last sentence): the scoped gate on a generated project with a
service and a web app, through `make verify-scoped` on a slice branch with a baseline.

A service's source change leaves the four method-file checks and `check-ux-gates` skipped, each named; a web app's
source change runs `check-ux-gates`. And what a stamp or a baseline records of `UX_GATES_SINCE` tells the default
(unset) from `all`, so a stamp is not reused across the two meanings and a scoped run after a baseline taken without it
selects `check-ux-gates`. The key is proved with the stamp script's own functions; a green `make verify` run end to end
adds nothing to it, since the key is what reuse compares.
"""
from __future__ import annotations

import json
import subprocess
import sys

from scoped_fixture import ShapeCase
from stamp_fixture import git

sys.dont_write_bytecode = True

DRY: dict[str, str | None] = {"STANDIN_DRY": "1"}
FOUR = ("check-agents", "check-speckit", "check-extensions", "check-constitution")
UX = "check-ux-gates"
SERVICE = "apps/service/src/extra.ts"
WEB = "apps/web/src/extra.ts"
TABLE = "scripts/verify_scoped/table.py"
VARIABLE = '"UX_GATES_SINCE", '
# What the stamp script says of the variable, in the project: the key's parts and the baseline's digest, under `env`.
_KEY = """
import importlib.util, json, sys
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location("stamp", "scripts/verify-stamp.py")
stamp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stamp)
parts = stamp.key_parts({})
print(json.dumps({"key": parts[0]["key"], "variables": parts[1]["variables"],
                  "digest": stamp.variable_digests()["UX_GATES_SINCE"]}))
"""


class ScopedSelectionTest(ShapeCase):
    shape = "model-typescript-web"

    def decide(self, env: dict[str, str | None] | None = None) -> tuple[dict[str, str], dict[str, str]]:
        return self.decided(self.scoped(env={**DRY, **(env or {})}))

    def test_e9_a_service_source_change_skips_the_four_and_check_ux_gates_each_named(self) -> None:
        self.edit(SERVICE, "export const extra = 1;\n")
        ran, skipped = self.decide()
        for name in (*FOUR, UX):
            self.assertIn(name, skipped, (ran, skipped))
            self.assertNotIn(name, ran)

    def test_e9_a_web_app_source_change_runs_check_ux_gates_naming_the_file(self) -> None:
        self.edit(WEB, "export const extra = 1;\n")
        ran, skipped = self.decide()
        self.assertEqual(ran.get(UX), WEB + " changed", (ran, skipped))
        self.assertNotIn(UX, skipped)

    def test_r9_all_after_a_baseline_taken_without_it_selects_check_ux_gates(self) -> None:
        self.edit(SERVICE, "export const extra = 1;\n")
        ran, skipped = self.decide({"UX_GATES_SINCE": "all"})
        self.assertIn(UX, ran, (ran, skipped))
        self.assertIn("UX_GATES_SINCE", ran[UX])
        self.assertIn(UX, self.decide()[1], "unset, as the baseline was taken, it is skipped")

    def test_r9_a_baseline_taken_under_all_selects_it_for_the_default(self) -> None:
        self.write_baseline({"UX_GATES_SINCE": "all"})
        self.edit(SERVICE, "export const extra = 1;\n")
        ran, _ = self.decide()
        self.assertIn(UX, ran)
        self.assertIn("UX_GATES_SINCE", ran[UX])

    def test_r9_teeth_a_row_without_the_variable_leaves_check_ux_gates_skipped_under_all(self) -> None:
        git(self.repo, "checkout", "-q", "main")
        table = self.repo / TABLE
        text = table.read_text(encoding="utf-8")
        self.assertIn(VARIABLE, text)
        table.write_text(text.replace(VARIABLE, "", 1), encoding="utf-8")
        git(self.repo, "add", TABLE)
        git(self.repo, "-c", "user.name=t", "-c", "user.email=t@local", "-c", "maintenance.auto=false", "commit", "-qm",
            "the variable is not read")
        git(self.repo, "checkout", "-q", "-B", "slice/S1")
        self.write_baseline()
        self.edit(SERVICE, "export const extra = 1;\n")
        ran, skipped = self.decide({"UX_GATES_SINCE": "all"})
        self.assertIn(UX, skipped, (ran, skipped))


class StampTest(ShapeCase):
    shape = "model-typescript-web"

    def key(self, env: dict[str, str | None]) -> dict[str, str]:
        done = subprocess.run([sys.executable, "-B", "-c", _KEY], cwd=self.repo, env=self.environment(env), text=True,
                              capture_output=True, timeout=60)
        self.assertEqual(done.returncode, 0, done.stderr)
        found: dict[str, str] = json.loads(done.stdout)
        return found

    def test_r9_a_stamp_taken_with_the_default_is_not_reused_under_all(self) -> None:
        default, everything = self.key({}), self.key({"UX_GATES_SINCE": "all"})
        self.assertNotEqual(default["key"], everything["key"])
        self.assertNotEqual(default["variables"], everything["variables"])

    def test_r9_the_baselines_digest_for_the_variable_differs_between_the_two_runs(self) -> None:
        self.assertNotEqual(self.key({})["digest"], self.key({"UX_GATES_SINCE": "all"})["digest"])
        self.assertEqual(self.key({})["digest"], self.key({})["digest"])

    def test_r9_the_key_follows_where_the_trunk_stands_so_a_stamp_never_outlives_its_base(self) -> None:
        before = self.key({})["key"]
        git(self.repo, "checkout", "-q", "main")
        self.edit("README.md", "\nan edit\n")
        git(self.repo, "-c", "user.name=t", "-c", "user.email=t@local", "-c", "maintenance.auto=false", "commit",
            "-qam", "main moves")
        git(self.repo, "checkout", "-q", "slice/S1")
        self.assertNotEqual(self.key({})["key"], before)
