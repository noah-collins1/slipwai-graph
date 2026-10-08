"""S41 T003, T006 (rules 2 and 7 · AC-S41-3, -6 half, -7): the list `stryker-mutation.py` reads, and what it refuses.

The wrapper is loaded as a module (bytecode off) for `matched`, `targets` and `versions`, and run as a subprocess in a
temporary project with a fake `npm` first on `PATH`, written here, that fails the example if it is ever called: every
example of this module is decided before Stryker would start.
"""
from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

from test_mutation_borders import loaded

from slipwai.assets import LANGUAGE_ROOT

sys.dont_write_bytecode = True
SCRIPT = LANGUAGE_ROOT / "typescript" / "scripts/stryker-mutation.py"
TEST_SELECTION = {"reads": ["assets/languages/typescript/scripts/stryker-mutation.py"]}
LIST = ["src/**/*.ts", "!src/main.ts", "!src/openapi.ts"]
POSTGRES = "!src/adapters/driven/event-store-postgres/**"
FAKE_NPM = """#!/bin/sh
echo "npm $*" >> "$FAKE_LOG"
exit 99
"""
PACKAGES = ("@stryker-mutator/core", "@stryker-mutator/vitest-runner")


def project(directory: Path, service: str = "apps/service", patterns: list[Any] | None = None) -> Path:
    """A project root holding one service with a `stryker.config.json` (the list, unless `patterns` says otherwise)."""
    (directory / service / "src").mkdir(parents=True)
    (directory / service / "stryker.config.json").write_text(json.dumps({"mutate": patterns or LIST}), encoding="utf-8")
    return directory


class Case(unittest.TestCase):
    def setUp(self) -> None:
        self.module = loaded(SCRIPT)
        self.root = Path(tempfile.mkdtemp(prefix="stryker-list-"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        (self.bin / "npm").write_text(FAKE_NPM, encoding="utf-8")
        (self.bin / "npm").chmod(0o755 | stat.S_IXUSR)
        self.log = self.root / "npm.log"
        self.tree = self.root / "tree"
        self.tree.mkdir()

    def run_wrapper(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        env = {**os.environ, "PATH": f"{self.bin}{os.pathsep}{os.environ['PATH']}", "FAKE_LOG": str(self.log)}
        for marker in ("CI", "GITHUB_ACTIONS", "GITLAB_CI"):
            env.pop(marker, None)
        return subprocess.run([sys.executable, "-B", str(SCRIPT), *arguments], cwd=self.tree, env=env, text=True,
                              capture_output=True, timeout=60)

    def assertNpmNeverCalled(self) -> None:
        self.assertFalse(self.log.exists(), self.log.read_text(encoding="utf-8") if self.log.exists() else "")


class MatchedTest(Case):
    def test_e1_the_generated_list_matches_what_it_names_and_nothing_else(self) -> None:
        for patterns in (LIST, [*LIST, POSTGRES]):
            for name in ("src/app.ts", "src/a/b/c.ts", "src/health.ts"):
                with self.subTest(patterns=len(patterns), file=name):
                    self.assertTrue(self.module.matched(patterns, name))
            for name in ("src/main.ts", "src/openapi.ts", "tests/app.test.ts", "src/a.js", "src/.hidden/x.ts",
                         "src/.x.ts"):
                with self.subTest(patterns=len(patterns), file=name):
                    self.assertFalse(self.module.matched(patterns, name))
        adapter = "src/adapters/driven/event-store-postgres/store.ts"
        self.assertTrue(self.module.matched(LIST, adapter))
        self.assertFalse(self.module.matched([*LIST, POSTGRES], adapter))

    def test_e1_a_later_positive_pattern_marks_again_what_an_earlier_negation_cleared(self) -> None:
        self.assertTrue(self.module.matched(["src/**/*.ts", "!src/main.ts", "src/main.ts"], "src/main.ts"))
        self.assertTrue(self.module.matched(["!src/main.ts", "src/**/*.ts"], "src/main.ts"))

    def test_e1_a_leading_dot_slash_and_a_literal_dot_segment_are_read(self) -> None:
        self.assertTrue(self.module.matched(["./src/**/*.ts"], "src/app.ts"))
        self.assertTrue(self.module.matched(["src/.gen/*.ts"], "src/.gen/x.ts"))
        self.assertFalse(self.module.matched(["src/*/x.ts"], "src/.gen/x.ts"))

    def test_e2_each_construct_outside_the_subset_is_unreadable_and_names_the_pattern(self) -> None:
        for pattern in ("src/?.ts", "src/[a].ts", "src/{a,b}.ts", "src/(a).ts", "src/a+.ts", "src/@a.ts", "src\\a.ts",
                        "src/a**.ts", "../x.ts", "/abs/x.ts", "src/a.ts:3-9", "src/a.ts:3", "!!src/a.ts", "src//a.ts"):
            with self.subTest(pattern=pattern), self.assertRaises(self.module.Unreadable) as raised:
                self.module.matched(["src/**/*.ts", pattern], "src/a.ts")
            self.assertIn(pattern, str(raised.exception))
        with self.assertRaises(self.module.Unreadable) as raised:
            self.module.matched([3], "src/a.ts")
        self.assertIn("3", str(raised.exception))

    def test_e2_a_config_that_cannot_be_read_says_why(self) -> None:
        service = self.tree / "apps/service"
        service.mkdir(parents=True)
        with self.assertRaises(self.module.Unreadable) as raised:
            self.module.targets(service)
        self.assertEqual(str(raised.exception), "no stryker.config.json")
        config = service / "stryker.config.json"
        for text in ("{", "[]", "{}", '{"mutate": []}', '{"mutate": "src/**/*.ts"}', '{"mutate": ["src/**/*.ts", 4]}'):
            config.write_text(text, encoding="utf-8")
            with self.subTest(text=text), self.assertRaises(self.module.Unreadable):
                self.module.targets(service)
        config.write_text(json.dumps({"mutate": LIST}), encoding="utf-8")
        self.assertEqual(self.module.targets(service), LIST)

    def test_e3_versions_reads_a_manifest_and_a_lock(self) -> None:
        manifest = json.dumps({"devDependencies": {"@stryker-mutator/core": "10.0.0", "vitest": "4.1.11",
                                                   "@stryker-mutator/vitest-runner": "10.0.0"}})
        self.assertEqual(self.module.versions(manifest_text=manifest),
                         {"@stryker-mutator/core": "10.0.0", "@stryker-mutator/vitest-runner": "10.0.0"})
        self.assertEqual(self.module.versions(manifest_text="{}"), {})
        lock = json.dumps({"packages": {
            "": {"name": "x"},
            "node_modules/@stryker-mutator/core": {"version": "10.0.0"},
            "apps/service/node_modules/@stryker-mutator/core": {"version": "10.0.0"},
            "node_modules/@stryker-mutator/vitest-runner": {"version": "10.0.1"},
            "node_modules/vitest": {"version": "4.1.11"}}})
        self.assertEqual(self.module.versions(lock_text=lock),
                         {"@stryker-mutator/core": "10.0.0", "@stryker-mutator/vitest-runner": "10.0.1"})
        for text in ("not json", "[1]", '"s"'):
            with self.subTest(text=text), self.assertRaises(self.module.Unreadable):
                self.module.versions(manifest_text=text)
            with self.subTest(lock=text), self.assertRaises(self.module.Unreadable):
                self.module.versions(lock_text=text)


class MainTest(Case):
    def test_e4_a_file_the_list_does_not_match_is_named_and_with_none_left_nothing_runs(self) -> None:
        project(self.tree)
        done = self.run_wrapper("apps/service", "--file", "src/main.ts")
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertEqual(done.stdout.splitlines(), [
            "mutation: not mutated apps/service/src/main.ts — outside Stryker's configured targets",
            "mutation: nothing under apps/service that was given is a file Stryker would mutate; no mutant to run"])
        self.assertNpmNeverCalled()
        self.assertEqual(sorted(p.name for p in (self.tree / "apps/service").iterdir()), ["src", "stryker.config.json"])

    def test_e4_a_matched_file_reaches_the_run_and_the_unmatched_one_is_named_first(self) -> None:
        project(self.tree)
        for name in ("package.json", "node_modules/.package-lock.json", *(
                f"node_modules/@stryker-mutator/{package}/package.json" for package in ("core", "vitest-runner"))):
            (self.tree / name).parent.mkdir(parents=True, exist_ok=True)
            (self.tree / name).write_text("{}", encoding="utf-8")  # installed, so the run is reached
        done = self.run_wrapper("apps/service", "--file", "src/main.ts", "--file", "src/health.ts")
        self.assertEqual(done.returncode, 1, done.stdout)  # the fake `npm` wrote no report: not a pass (T004 judges it)
        self.assertEqual(done.stdout.splitlines()[0],
                         "mutation: not mutated apps/service/src/main.ts — outside Stryker's configured targets")
        self.assertIn("exec --no -- stryker run --mutate src/health.ts", self.log.read_text(encoding="utf-8"))

    def test_e4_an_unreadable_config_is_one_line_and_exit_2(self) -> None:
        project(self.tree, patterns=["src/**/*.{ts,tsx}"])
        done = self.run_wrapper("apps/service", "--file", "src/a.ts")
        self.assertEqual(done.returncode, 2)
        lines = (done.stdout + done.stderr).strip().splitlines()
        self.assertEqual(len(lines), 1, lines)
        self.assertTrue(lines[0].startswith("mutation: apps/service/stryker.config.json: "), lines)
        self.assertIn("src/**/*.{ts,tsx}", lines[0])
        self.assertNpmNeverCalled()

    def test_e4_the_sweep_runs_stryker_over_a_list_this_reader_cannot_evaluate(self) -> None:
        """D213 item 3: a list the scope script cannot read is the service's *sweep* — Stryker reads its own globs, so
        the whole-list run must start, not refuse. Only a missing config stops it (Stryker would mutate its defaults)."""
        project(self.tree, patterns=["src/**/*.{ts,tsx}"])
        for name in ("package.json", "node_modules/.package-lock.json", *(
                f"node_modules/@stryker-mutator/{package}/package.json" for package in ("core", "vitest-runner"))):
            (self.tree / name).parent.mkdir(parents=True, exist_ok=True)
            (self.tree / name).write_text("{}", encoding="utf-8")
        done = self.run_wrapper("apps/service")
        self.assertIn("npm exec --no -- stryker run\n", self.log.read_text(encoding="utf-8"), done.stdout)
        (self.tree / "apps/service/stryker.config.json").unlink()
        self.log.unlink()
        done = self.run_wrapper("apps/service")
        self.assertEqual(done.returncode, 2, done.stdout)
        self.assertEqual(done.stdout.splitlines(), ["mutation: apps/service/stryker.config.json: no stryker.config.json"])
        self.assertNpmNeverCalled()

    def test_e5_hold_a_nested_service_and_a_trailing_slash_answer_alike(self) -> None:
        """HOLD (teeth: compare the argument with a trailing `/` as written and see the line name `apps/billing//`)."""
        project(self.tree, "apps/billing")
        for argument in ("apps/billing", "apps/billing/"):
            with self.subTest(argument=argument):
                done = self.run_wrapper(argument, "--file", "src/main.ts")
                self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
                self.assertEqual(done.stdout.splitlines()[0], "mutation: not mutated apps/billing/src/main.ts — "
                                 "outside Stryker's configured targets")
        self.assertNpmNeverCalled()


class RefusalTest(Case):
    """Rule 7, wrapper half (D215 d): a path `--mutate` would misread refuses the whole run, before anything is done."""

    def words(self, file: str, char: str) -> str:
        return (f"`apps/service/{file}` holds `{char}`, which Stryker's --mutate reads as pattern syntax; "
                "rename it, or run `make mutation-full`")

    def test_e1_each_character_and_a_trailing_line_number_is_refused_in_the_data_model_words(self) -> None:
        for file, char in (("src/a,b.ts", ","), ("src/a*.ts", "*"), ("src/a?.ts", "?"), ("src/{a}.ts", "{"),
                           ("src/[a].ts", "["), ("src/!a.ts", "!"), ("src/a.ts:12", ":12"), ("src/a.ts:3", ":3")):
            with self.subTest(file=file):
                self.assertEqual(self.module.refused("apps/service", file), self.words(file, char))
        for file in ("src/a.ts:x", "src/a.ts:", "src/a:1.ts", "src/health.ts", "src/a b.ts", "src/$a.ts", "src/é.ts",
                     "src/#a.ts"):
            with self.subTest(file=file):
                self.assertIsNone(self.module.refused("apps/service", file))

    def test_e2_one_refused_file_refuses_the_whole_run_before_npm_the_config_or_anything_is_touched(self) -> None:
        project(self.tree)
        old = self.tree / "apps/service/reports/mutation/mutation.json"
        old.parent.mkdir(parents=True)
        old.write_text("{}", encoding="utf-8")
        done = self.run_wrapper("apps/service", "--file", "src/health.ts", "--file", "src/a,b.ts")
        self.assertEqual(done.returncode, 2)
        self.assertEqual(done.stdout.splitlines(), ["mutation: " + self.words("src/a,b.ts", ",")])
        self.assertNpmNeverCalled()
        self.assertEqual(old.read_text(encoding="utf-8"), "{}")
        self.assertFalse((self.tree / "apps/service/.stryker-tmp").exists())

    def test_e3_the_refusal_is_louder_than_outside_the_targets(self) -> None:
        project(self.tree)
        for files in (("src/main,x.ts",), ("src/main.ts", "src/a?.ts")):
            with self.subTest(files=files):
                done = self.run_wrapper("apps/service", *(part for file in files for part in ("--file", file)))
                self.assertEqual(done.returncode, 2, done.stdout)
                self.assertEqual(len(done.stdout.splitlines()), 1, done.stdout)
        self.assertNpmNeverCalled()

    def test_e4_hold_a_space_a_dollar_a_unicode_letter_and_a_hash_reach_the_run(self) -> None:
        """HOLD (teeth: refuse every non-alphanumeric character and see it fail)."""
        project(self.tree)
        for name in ("src/a b.ts", "src/$a.ts", "src/é.ts", "src/#a.ts"):
            with self.subTest(file=name):
                done = self.run_wrapper("apps/service", "--file", name)
                self.assertNotIn("holds", done.stdout)
                self.assertTrue(self.log.exists(), "the run was not reached")
                self.log.unlink()


if __name__ == "__main__":
    unittest.main()
