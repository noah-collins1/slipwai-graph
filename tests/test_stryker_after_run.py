"""S41 T010 (rule 8 · AC-S41-9, -10): after a TypeScript run the stamp, the scoped gate and the placeholders hold.

A fake `npm` (`test_stryker_verdict`'s, which also answers the version question the stamp asks) writes the report;
`make`, the scripts and the stamp are the project's own. The scoped-gate examples run in the stamp fixture's project
(`ShapeCase`), the placeholder and border examples in projects the factory generates here.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from scoped_fixture import ShapeCase
from stamp_fixture import CI_MARKERS, GIT_STATE, MAKE_STATE, git
from support import FactoryTestCase, commit_all
from test_stryker_verdict import FAKE_NPM, mutant, report

from slipwai.assets import ROOT

sys.dont_write_bytecode = True

VERSIONED = '#!/bin/sh\n[ "$1" = --version ] && { echo 10.9.0; exit 0; }\nexec "$(dirname "$0")/npm-fake" "$@"\n'


def fake_npm(directory: Path) -> None:
    """`npm` in `directory`: the verdict suite's fake, which also answers the version question the stamp asks."""
    for name, text in (("npm-fake", FAKE_NPM), ("npm", VERSIONED)):
        (directory / name).write_text(text, encoding="utf-8")
        (directory / name).chmod(0o755)


PASSING: dict[str, Any] = {"report": report(src__health_ts=[mutant("Killed")])}
FAILING: dict[str, Any] = {"report": report(src__health_ts=[mutant("Survived")])}
DRY: dict[str, str | None] = {"STANDIN_DRY": "1"}
IGNORED = "import sys, json, importlib.util\nsys.dont_write_bytecode = True\n" + (
    "spec = importlib.util.spec_from_file_location('s', 'scripts/verify-stamp.py')\n"
    "stamp = importlib.util.module_from_spec(spec); spec.loader.exec_module(stamp)\n"
    "print(json.dumps(stamp.key_parts({})[1]['ignored']))\n")


class AfterARunTest(ShapeCase):
    """Rule 8: the leavings of a run are the stamp's exempt rows and no reach; the project is the stamp-fixture one."""

    shape = "model-typescript-web"

    def setUp(self) -> None:
        super().setUp()
        fake_npm(self.bin)
        for package in ("core", "vitest-runner"):  # installed, and the marker newer than every manifest
            (self.repo / "node_modules/@stryker-mutator" / package).mkdir(parents=True, exist_ok=True)
            (self.repo / "node_modules/@stryker-mutator" / package / "package.json").write_text("{}", encoding="utf-8")
        marker = self.repo / "node_modules/.package-lock.json"
        marker.write_text("{}", encoding="utf-8")
        os.utime(marker, (time.time() + 500, time.time() + 500))
        self.write_baseline()
        self.edit("apps/service/src/health.ts")
        self.plan = self.bin.parent / "plan.json"

    def make(self, target: str, plan: dict[str, Any]) -> subprocess.CompletedProcess[str]:
        self.plan.write_text(json.dumps(plan), encoding="utf-8")
        env = self.environment({"FAKE_LOG": str(self.bin.parent / "npm.log"), "FAKE_PLAN": str(self.plan)})
        return subprocess.run(["make", target], cwd=self.repo, env=env, text=True, capture_output=True, timeout=180)

    def state(self) -> tuple[tuple[dict[str, str], dict[str, str]], str, set[str]]:
        digest = subprocess.run([sys.executable, "-B", "-c", IGNORED], cwd=self.repo, env=self.environment(), text=True,
                                capture_output=True, check=True, timeout=60).stdout
        status = git(self.repo, "status", "--porcelain", "--ignored")
        return self.decided(self.scoped(DRY)), digest, set(status.splitlines())

    def test_e1_a_passing_and_a_failing_run_of_either_target_leave_the_stamp_and_the_scoped_gate_alone(self) -> None:
        """Teeth: remove one of the two `EXEMPT` rows in `verify-stamp.py` and see it fail."""
        before = self.state()
        for plan, status in ((PASSING, 0), (FAILING, 2)):  # make's own status for a recipe that failed
            for target in ("mutation", "mutation-full"):
                done = self.make(target, plan)
                self.assertEqual(done.returncode, status, f"{target}: {done.stdout}{done.stderr}")
        after = self.state()
        self.assertEqual(after[:2], before[:2], "a run moved what the scoped gate or the stamp compares")
        left = after[2] - before[2]
        self.assertTrue(left, "the runs left nothing to ignore")
        self.assertTrue(all(line.startswith("!! ") and ("/reports/" in line or ".stryker-tmp/" in line)
                            for line in left), left)

    def test_e2_a_sandbox_left_behind_is_no_reach_unless_its_link_leaves_the_deployable(self) -> None:
        """Teeth: the last example, a link out of the deployable, is a reach."""
        base = self.state()[0]
        self.assertTrue(base[0], "the baseline selects nothing: the examples below would hold with no teeth")
        sandbox = self.repo / "apps/service/.stryker-tmp/sandbox-x"
        (sandbox / "node_modules/.vite").mkdir(parents=True)
        (sandbox / "node_modules/.vite/deps.json").write_text("{}", encoding="utf-8")
        self.assertEqual(self.state()[0], base, "a real node_modules with no link read as a reach")
        shutil.rmtree(sandbox / "node_modules")
        (self.repo / "apps/service/node_modules").mkdir()
        os.symlink("../../node_modules", sandbox / "node_modules")  # back inside the service
        self.assertEqual(self.state()[0], base, "a link back inside the service read as a reach")
        (sandbox / "node_modules").unlink()
        os.symlink("../../../../node_modules", sandbox / "node_modules")  # out of the deployable
        self.assertNotEqual(self.state()[0], base)


class PlaceholdersAfterTest(FactoryTestCase):
    """Rule 8: Python and Quarkus still refuse; a TypeScript service beside them runs; the borders and `SINCE` hold."""

    parent: Path
    projects: dict[str, Path]

    @classmethod
    def setUpClass(cls) -> None:
        cls.parent = Path(tempfile.mkdtemp(prefix="stryker-after-"))
        cls.addClassCleanup(shutil.rmtree, cls.parent, ignore_errors=True)
        cls.projects = {}

    def project(self, name: str) -> Path:
        """A generated project on `slice/S1` with a production file changed in each service."""
        if name in self.projects:
            return self.projects[name]
        language = {"quarkus": "java-quarkus"}.get(name, "typescript")
        made = self.generate(self.parent, name, "standard", language, "none", http="none")
        if name == "mixed":
            subprocess.run([str(ROOT / "slipwai"), "add-service", "billing", "--language", "python"], cwd=made,
                           check=True, capture_output=True, timeout=120)
            commit_all(made, "billing")
        git(made, "checkout", "-q", "-b", "slice/S1")
        edits = {"quarkus": ["apps/service/src/main/java/com/x/Foo.java"], "mixed": [
            "apps/service/src/health.ts", "apps/billing/src/billing/extra.py"]}
        for path in edits.get(name, ["apps/service/src/health.ts"]):
            (made / path).parent.mkdir(parents=True, exist_ok=True)
            with (made / path).open("a", encoding="utf-8") as handle:
                handle.write("\n// an edit\n")
        self.projects[name] = made
        return made

    def make(self, name: str, *words: str, **env: str) -> subprocess.CompletedProcess[str]:
        directory = Path(tempfile.mkdtemp(dir=self.parent))
        fake_npm(directory)
        (directory / "plan.json").write_text(json.dumps(PASSING), encoding="utf-8")
        self.addCleanup(shutil.rmtree, directory, ignore_errors=True)
        wanted = {k: v for k, v in os.environ.items() if k not in CI_MARKERS + MAKE_STATE + GIT_STATE + ("SINCE",)}
        wanted.update({"PATH": f"{directory}{os.pathsep}{wanted['PATH']}", "FAKE_LOG": str(directory / "npm.log"),
                       "FAKE_PLAN": str(directory / "plan.json"), **env})
        done = subprocess.run(["make", *words], cwd=self.project(name), env=wanted, text=True, capture_output=True,
                              timeout=180)
        self.log = directory / "npm.log"
        return done

    def started(self) -> list[list[str]]:
        calls = [json.loads(line)["argv"] for line in self.log.read_text(encoding="utf-8").splitlines()]
        return [argv for argv in calls if argv[:1] == ["exec"]]

    def test_e3_quarkus_and_python_still_refuse_with_their_setup_messages_and_a_typescript_service_runs(self) -> None:
        """HOLD (teeth: change a placeholder string in `native_commands` and see it fail)."""
        done = self.make("quarkus", "mutation")
        self.assertEqual(done.returncode, 2, done.stdout)
        self.assertIn("Configure PIT for the domain packages only", done.stdout)
        done = self.make("mixed", "mutation")
        self.assertEqual(done.returncode, 2, done.stdout)
        self.assertIn("mutation: scope apps/service — src/health.ts", done.stdout)
        self.assertIn("mutation: refuse apps/billing — install and configure mutmut", done.stdout)
        self.assertEqual(self.started(), [["exec", "--no", "--", "stryker", "run", "--mutate", "src/health.ts"]])

    def test_e4_hold_the_borders_and_since_decide_scoped_or_swept_for_typescript(self) -> None:
        git(self.project("ts"), "checkout", "-q", "slice/S1")
        scoped = [["exec", "--no", "--", "stryker", "run", "--mutate", "src/health.ts"]]
        swept = [["exec", "--no", "--", "stryker", "run"]]
        for name, expected, words, env in (
                ("slice", scoped, ["mutation"], {}), ("CI", swept, ["mutation"], {"CI": "true"}),
                ("empty SINCE", swept, ["mutation"], {"SINCE": ""}), ("SINCE in CI", scoped, ["mutation"],
                                                                      {"SINCE": "main", "CI": "true"}),
                ("mutation-full", swept, ["mutation-full", "SINCE=main"], {})):
            with self.subTest(case=name):
                done = self.make("ts", *words, **env)
                self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
                self.assertEqual(self.started(), expected, done.stdout)
        for how in (["checkout", "-q", "main"], ["checkout", "-q", "--detach", "slice/S1"]):
            git(self.project("ts"), *how)
            with self.subTest(border=how[-1]):
                done = self.make("ts", "mutation")
                self.assertEqual((done.returncode, self.started()), (0, swept), done.stdout)
