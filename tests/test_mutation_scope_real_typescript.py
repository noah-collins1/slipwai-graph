"""S41 T013 (rule 11 · AC-S41-1, -2, -4 end to end): the one real Stryker run — heavy, S43's list.

The minimal starter (`--profile standard --http none`, so no transport, no store and nothing red on day one) on a slice
branch with one file changed, run through the project's own `make mutation` and `make mutation-full`, with the real
`npm ci` and the real Stryker 10.0.0 under Vitest 4.1.11 and TypeScript 7.0.2. It is the one place the fake `npm` of
`test_stryker_verdict` and the recording runner of `test_mutation_scope_typescript` are checked against the tool.

Gated as `tests/test_mutation_scope_real_go.py` is, by `backends_under_test()` and the tool on `PATH` (here `npm`, and
the network `npm ci` needs), and only where `FACTORY_BACKENDS` is set: a run of the whole matrix on a laptop does not
start a sweep nobody asked for. Skipped, not failed, without it.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any

from stamp_fixture import git, key_of
from support import FactoryTestCase, backends_under_test, commit_all
from test_mutation_borders import clean_environment

REPORT = "apps/service/reports/mutation/mutation.json"
HEALTH = "apps/service/src/health.ts"
HEALTH_TEST = "apps/service/tests/health.test.ts"
EXTRA = "export function double(n: number): number {\n  return n * 2;\n}\n"
EXTRA_TEST = ("import { expect, it } from 'vitest';\n\nimport { double } from '../src/extra.js';\n\n"
              "it('doubles', () => {\n  expect(double(3)).toBe(6);\n});\n")
LISTED = {"src/health.ts", "src/extra.ts"}
EXCLUDED = ("src/main.ts", "src/openapi.ts")


def enabled() -> bool:
    chosen = bool(os.environ.get("FACTORY_BACKENDS")) and "typescript" in backends_under_test()
    return chosen and shutil.which("npm") is not None


class RealTypeScriptTest(FactoryTestCase):
    repo: Path
    key: str
    counts: dict[str, int]

    @classmethod
    def setUpClass(cls) -> None:
        if not enabled():
            raise unittest.SkipTest("heavy: the TypeScript slice of the matrix (FACTORY_BACKENDS), npm and a network")
        parent = Path(tempfile.mkdtemp(prefix="real-ts-", dir="/tmp"))
        cls.addClassCleanup(shutil.rmtree, parent, ignore_errors=True)
        cls.repo = cls().generate(parent, "real", "standard", "typescript", "none", http="none")
        for name, text in (("extra.ts", EXTRA), ("main.ts", "export const main = (): number => 1;\n"),
                           ("openapi.ts", "export const openapi = (): number => 2;\n")):
            (cls.repo / "apps/service/src" / name).write_text(text, encoding="utf-8")
        (cls.repo / "apps/service/tests/extra.test.ts").write_text(EXTRA_TEST, encoding="utf-8")
        commit_all(cls.repo, "a second tested file, and two entry points the list leaves out")
        git(cls.repo, "checkout", "-q", "-b", "slice/S1")
        cls.counts = {}

    def make(self, target: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["make", target], cwd=self.repo, env=clean_environment(), text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=900)

    def report(self) -> dict[str, Any]:
        return json.loads((self.repo / REPORT).read_text(encoding="utf-8"))

    def mutants(self) -> int:
        return sum(len(entry["mutants"]) for entry in self.report()["files"].values())

    def test_e1_a_changed_file_with_a_killing_test_is_scoped_to_that_file_and_passes(self) -> None:
        with (self.repo / HEALTH).open("a", encoding="utf-8") as handle:
            handle.write("// touched\n")
        done = self.make("mutation")
        self.assertEqual(done.returncode, 0, done.stdout[-4000:])
        lines = done.stdout.splitlines()
        self.assertRegex(lines[0], r"^mutation: scoped to 1 changed file\(s\) since `main` at [0-9a-f]+: "
                         + re.escape(HEALTH))
        self.assertEqual(lines[-1], "mutation: 1 scoped, 0 swept, 0 skipped, 0 refused; passed")
        self.assertEqual(set(self.report()["files"]), {"src/health.ts"})
        type(self).counts["scoped"] = self.mutants()
        git(self.repo, "checkout", "-q", "--", HEALTH)
        type(self).key = key_of(self.repo)  # the stamp's key with a scoped run's report in a clean tree

    def test_e2_a_weakened_test_fails_naming_the_survivor_and_replaces_the_report(self) -> None:
        before = hashlib.sha256((self.repo / REPORT).read_bytes()).hexdigest()
        test = self.repo / HEALTH_TEST
        text = test.read_text(encoding="utf-8")
        test.write_text(text.replace("expect(health()).toEqual({ status: 'ok' });", "expect(health()).toBeDefined();"),
                        encoding="utf-8")
        with (self.repo / HEALTH).open("a", encoding="utf-8") as handle:
            handle.write("// touched\n")
        try:
            done = self.make("mutation")
        finally:
            git(self.repo, "checkout", "-q", "--", HEALTH_TEST, HEALTH)
        self.assertNotEqual(done.returncode, 0, done.stdout[-4000:])
        self.assertRegex(done.stdout, r"mutation: Survived apps/service/src/health\.ts:\d+:\d+ \S+ → .* "
                                      r"\(report apps/service/reports/mutation/mutation\.json\)")
        self.assertNotEqual(hashlib.sha256((self.repo / REPORT).read_bytes()).hexdigest(), before)
        self.assertIn("Survived", {m["status"] for m in self.report()["files"]["src/health.ts"]["mutants"]})

    def test_e3_the_sweep_mutates_the_config_s_list_and_nothing_it_excludes(self) -> None:
        done = self.make("mutation-full")
        self.assertEqual(done.returncode, 0, done.stdout[-4000:])
        self.assertEqual(set(self.report()["files"]), LISTED)
        for name in EXCLUDED:
            self.assertNotIn(name, self.report()["files"])
        self.assertGreater(self.mutants(), self.counts["scoped"], "the sweep is not larger than the scoped run")

    def test_e4_afterwards_git_is_clean_and_the_stamp_s_key_is_what_it_was(self) -> None:
        self.assertEqual(git(self.repo, "status", "--short").strip(), "")
        self.assertEqual(key_of(self.repo), type(self).key, "a run moved what the stamp compares, so the scoped gate")
