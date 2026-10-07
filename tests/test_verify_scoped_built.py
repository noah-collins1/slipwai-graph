"""T030 (D194): an exempt directory a walking check reads gives that check no recorded inputs.

`check-imports` and `check-migrations` read every directory but D45's four and a recorded Java root's `target` (D52),
so a directory the verify stamp exempts (`dist/`, `coverage/`, `target/`, `.build/`, …: the stamp's own
`exempt_entry`) that holds a file one of them reads is read by it and compared by nothing the scoped gate has. Where
one exists in the working tree under a declared input of either check, the check keeps no recorded inputs, with the
directory named. What the gate's own runs leave there (a web app's built `.js`, a coverage report) is read by neither,
and changes nothing.
"""
from __future__ import annotations

import subprocess
import sys

from scoped_fixture import ShapeCase
from stamp_fixture import git

sys.dont_write_bytecode = True

DRY: dict[str, str | None] = {"STANDIN_DRY": "1"}
LEAK = "apps/web/dist/domain/leak.ts"  # the shape ignores a web app's `dist/`
FRAMEWORK = 'import Fastify from "fastify";\n'
MIGRATION = "apps/service/coverage/migrations/0001_init.sql"
UNCHANGED = "none of its inputs changed"


class BuiltTest(ShapeCase):
    def check(self, name: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, "-B", f"scripts/{name}.py"], cwd=self.repo, text=True,
                              capture_output=True, timeout=120)

    def test_a_file_check_imports_flags_inside_an_ignored_dist_runs_check_imports(self) -> None:
        self.edit(LEAK, FRAMEWORK)
        self.assertIn("!!", git(self.repo, "status", "--porcelain", "--ignored", "--", LEAK), "dist/ is not ignored")
        self.assertNotEqual(self.check("check-imports").returncode, 0, "the check does not read the file")
        ran, skipped = self.decided(self.scoped(DRY))
        self.assertIn("check-imports", ran, skipped.get("check-imports"))
        self.assertIn("`apps/web/dist/`", ran["check-imports"])
        self.assertIn("exempt", ran["check-imports"])

    def test_a_migration_inside_an_exempt_directory_runs_check_migrations(self) -> None:
        self.edit(MIGRATION, "create table t (id int);\n")
        ran, _ = self.decided(self.scoped(DRY))
        self.assertIn("`apps/service/coverage/`", ran.get("check-migrations", ""), ran)

    def test_what_a_build_leaves_that_neither_check_reads_still_skips_them(self) -> None:
        for path in ("apps/web/dist/assets/index.js", "apps/web/dist/index.html", "apps/web/coverage/index.html",
                     "apps/service/node_modules/x/domain/y.ts", ".build/probe.ts"):
            self.edit(path, "moved\n")
        _, skipped = self.decided(self.scoped(DRY))
        self.assertEqual((skipped.get("check-imports"), skipped.get("check-migrations")), (UNCHANGED, UNCHANGED))

    def test_a_tree_with_no_exempt_directory_skips_them(self) -> None:
        _, skipped = self.decided(self.scoped(DRY))
        self.assertEqual((skipped.get("check-imports"), skipped.get("check-migrations")), (UNCHANGED, UNCHANGED))
