"""An interpreter cache under `assets/` reaches the modules that read `assets` (S38 T026, AC-S38-10, -16).

A cache never makes the run whole and no configuration claims it, but a module whose `reads` name the directory it sits
in is reached: `test_assets_bytecode` exists to fail on exactly this file.
"""
from __future__ import annotations

import sys

from select_fixture_declare import DeclarationCase

sys.dont_write_bytecode = True

CACHE = "assets/toolkit/scripts/__pycache__/verify-stamp.cpython-312.pyc"
READER = '{"reads": ["assets"]}'
GENERATOR = '{"configurations": {"backend": ["go"]}}'


class TestACacheUnderAssets(DeclarationCase):
    def dry_run(self, *paths: str) -> list[str]:
        self.declare(test_reader=READER, test_generator=GENERATOR, test_other='{"reads": ["src"]}')
        self.slice_changing()
        for path in paths:
            self.write(path, "cache\n")
        done = self.selector("--dry-run", SINCE="HEAD")
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        return done.stdout.splitlines()

    def test_it_selects_the_module_that_reads_assets_and_the_run_stays_scoped(self) -> None:
        lines = self.dry_run(CACHE)
        self.assertTrue(lines[0].startswith("compared with `HEAD` at "), lines[0])
        self.assertNotIn("full:", "\n".join(lines))
        self.assertIn("skipped test_generator: reads none of the changed files", lines)
        self.assertIn("skipped test_other: reads none of the changed files", lines)
        self.assertFalse([line for line in lines if line.startswith("skipped test_reader")], lines)

    def test_the_run_runs_the_module_that_reads_assets(self) -> None:
        self.declare(test_reader=READER)
        self.slice_changing()
        self.write(CACHE, "cache\n")
        done = self.selector(SINCE="HEAD")
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertEqual(self.modules_run(), ["test_reader"])

    def test_a_cache_outside_assets_reaches_nothing(self) -> None:
        lines = self.dry_run("tests/__pycache__/x.pyc")
        self.assertIn("skipped test_reader: reads none of the changed files", lines)

    def test_a_cache_alone_does_not_hide_a_real_change(self) -> None:
        self.declare(test_reader=READER, test_generator=GENERATOR)
        self.slice_changing("assets/languages/go/main.go")
        self.write(CACHE, "cache\n")
        done = self.selector("--dry-run", SINCE="HEAD")
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertNotIn("skipped test_generator", done.stdout)
