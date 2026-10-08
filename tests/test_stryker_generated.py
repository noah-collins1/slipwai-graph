"""S41 (US2): what a generated TypeScript service is given for Stryker, and what the project's gates keep of it.

T002 (rule 1 · AC-S41-2 part, -11, -13 part): the two exact devDependencies, `stryker.config.json` per service, the
wrapper once per project, the `mutation-full` line, the ignore lines and the committed locks that agree with the
manifest. Projects are generated once per class; nothing is run except `make -npq`, the wrapper with no arguments and
(gated) `npm audit`.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from stamp_fixture import CI_MARKERS, GIT_STATE, MAKE_STATE, git
from support import FactoryTestCase, commit_all
from test_mutation_targets import go_and_typescript, recipe_of

from slipwai.assets import ROOT
from slipwai.project.stryker import FULL_COMMAND, SCRIPT_PATH
from slipwai.scaffold import write_project
from slipwai.selection import Selection
from slipwai.services import default_apps

sys.dont_write_bytecode = True

EXACT = "10.0.0"
PACKAGES = ("@stryker-mutator/core", "@stryker-mutator/vitest-runner")
MUTATE = ["src/**/*.ts", "!src/main.ts", "!src/openapi.ts"]
POSTGRES = "!src/adapters/driven/event-store-postgres/**"


def clean_environment() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if k not in CI_MARKERS + MAKE_STATE + GIT_STATE + ("SINCE",)}


class StrykerGeneratedTest(FactoryTestCase):
    parent: Path
    projects: dict[str, Path]

    @classmethod
    def setUpClass(cls) -> None:
        cls.parent = Path(tempfile.mkdtemp(prefix="stryker-generated-"))
        cls.addClassCleanup(shutil.rmtree, cls.parent, ignore_errors=True)
        cls.projects = {}

    def project(self, name: str) -> Path:
        if name not in self.projects:
            if name == "go-ts":
                self.projects[name] = go_and_typescript(self.parent, self)
            elif name == "two-ts":
                made = self.generate(self.parent, name, "standard", "typescript", "none", http="none")
                dirty = subprocess.run(["git", "status", "--porcelain"], cwd=made, text=True, capture_output=True,
                                       timeout=60)
                if dirty.stdout.strip():  # `add-service` refuses a tree with uncommitted work
                    commit_all(made, "base")
                subprocess.run([str(ROOT / "slipwai"), "add-service", "second", "--language", "typescript"], cwd=made,
                               check=True, capture_output=True, timeout=120)
                self.projects[name] = made
            elif name == "go":
                self.projects[name] = self.generate(self.parent, name, "standard", "go", "none", http="none")
            elif name == "memory":
                self.projects[name] = self.generate(self.parent, name, "event-modelling", "typescript", "none",
                                                    event_store="memory")
            else:
                self.projects[name] = self.generate(self.parent, name, "event-modelling", "typescript", "none",
                                                    event_store="postgres")
        return self.projects[name]

    def services(self, name: str) -> list[str]:
        return [f"apps/{p.name}" for p in sorted((self.project(name) / "apps").iterdir())
                if (p / "package.json").is_file()]

    def test_e1_both_packages_are_exact_devdependencies_of_every_typescript_service(self) -> None:
        for name in ("postgres", "go-ts", "two-ts"):
            for service in self.services(name):
                with self.subTest(project=name, service=service):
                    manifest = json.loads((self.project(name) / service / "package.json").read_text(encoding="utf-8"))
                    for package in PACKAGES:
                        self.assertEqual(manifest["devDependencies"].get(package), EXACT)

    def test_e2_each_service_has_its_own_config_with_the_list_the_decision_fixes(self) -> None:
        for name, postgres in (("postgres", True), ("memory", False)):
            config = json.loads((self.project(name) / "apps/service/stryker.config.json").read_text(encoding="utf-8"))
            with self.subTest(project=name):
                self.assertEqual(config["testRunner"], "vitest")
                self.assertIs(config["vitest"]["related"], False)
                self.assertEqual(config["vitest"]["configFile"], "vitest.config.ts")
                self.assertEqual(config["mutate"], [*MUTATE, *([POSTGRES] if postgres else [])])
                self.assertEqual(sorted(config["reporters"]), ["clear-text", "html", "json"])
                self.assertIs(config["incremental"], False)
                self.assertEqual(config["cleanTempDir"], "always")
                self.assertIsNone(config["thresholds"]["break"])
                self.assertFalse((self.project(name) / "apps/service" / config["tsconfigFile"]).exists())
                for key in ("vitest", "mutate", "thresholds", "tsconfigFile"):
                    self.assertIsInstance(config[f"{key}_comment"], str)
        for service in ("apps/service", "apps/second"):
            self.assertTrue((self.project("two-ts") / service / "stryker.config.json").is_file(), service)
            beside_go = (self.project("go-ts") / service / "stryker.config.json").is_file()
            self.assertEqual(beside_go, service == "apps/second")

    def test_e3_the_wrapper_is_one_executable_script_per_typescript_project(self) -> None:
        for name in ("postgres", "two-ts", "go-ts"):
            script = self.project(name) / SCRIPT_PATH
            with self.subTest(project=name):
                self.assertTrue(script.is_file())
                self.assertTrue(os.access(script, os.X_OK))
                text = script.read_text(encoding="utf-8")
                self.assertNotIn("apps/service", text)
                self.assertNotIn("apps/web", text)
        self.assertFalse((self.project("go") / SCRIPT_PATH).exists())
        script = self.project("postgres") / SCRIPT_PATH
        for arguments in ([], ["apps/service", "--bogus"]):
            done = subprocess.run([sys.executable, "-B", str(script), *arguments], cwd=self.project("postgres"),
                                  text=True, capture_output=True, timeout=60)
            self.assertEqual(done.returncode, 2, arguments)
            self.assertEqual(len((done.stdout + done.stderr).strip().splitlines()), 1, arguments)
        self.assertEqual(list(self.project("postgres").rglob("__pycache__")), [])

    def test_e3_in_an_adopted_layout_the_wrapper_lands_under_the_delivery_scripts(self) -> None:
        with tempfile.TemporaryDirectory(prefix="stryker-layout-") as directory:
            repo = Path(directory) / "wrapped"
            from slipwai.layout import Layout
            write_project(repo, "wrapped", "event-modelling", "none",
                          default_apps("typescript", "none", Selection({"http": "fastify"})), layout=Layout("delivery"))
            self.assertTrue(os.access(repo / "delivery" / SCRIPT_PATH, os.X_OK))
            self.assertFalse((repo / SCRIPT_PATH).exists())

    def test_e4_mutation_full_is_the_wrapper_per_service_and_the_gates_are_untouched(self) -> None:
        self.assertEqual(recipe_of(self.project("postgres").joinpath("Makefile").read_text(encoding="utf-8"),
                                   "mutation-full"), [FULL_COMMAND.replace("__APP__", "apps/service")])
        two = recipe_of((self.project("two-ts") / "Makefile").read_text(encoding="utf-8"), "mutation-full")
        self.assertEqual(two, [FULL_COMMAND.replace("__APP__", f"apps/{n}") for n in ("service", "second")])
        mixed = recipe_of((self.project("go-ts") / "Makefile").read_text(encoding="utf-8"), "mutation-full")
        self.assertIn(FULL_COMMAND.replace("__APP__", "apps/second"), mixed)

    def test_e4_hold_no_gate_reaches_the_mutation_targets(self) -> None:
        """HOLD (teeth: add `mutation-full` as a prerequisite of `verify-checks`): the gates' rules name neither."""
        for name in ("postgres", "go-ts"):
            text = (self.project(name) / "Makefile").read_text(encoding="utf-8")
            for rule in ("verify", "verify-checks", "ci"):
                line = re.search(rf"(?m)^{rule}:(.*)$", text)
                self.assertIsNotNone(line, rule)
                self.assertNotIn("mutation", line.group(1) if line else "", f"{name}: {rule}")

    def test_e5_the_ignore_lines_are_a_typescript_project_s_and_git_ignores_what_a_run_leaves(self) -> None:
        for name in ("postgres", "go-ts"):
            project = self.project(name)
            if git(project, "status", "--short").strip():
                commit_all(project, "as generated")
            ignored = (project / ".gitignore").read_text(encoding="utf-8").splitlines()
            self.assertIn(".stryker-tmp/", ignored)
            self.assertIn("apps/*/reports/mutation/", ignored)
            for path in ("apps/service/reports/mutation/mutation.json", "apps/service/.stryker-tmp/sandbox-x/a.ts"):
                (project / path).parent.mkdir(parents=True, exist_ok=True)
                (project / path).write_text("{}", encoding="utf-8")
            self.assertEqual(git(project, "status", "--short").strip(), "", f"{name}: a run's leavings show in git")
        ignored = (self.project("go") / ".gitignore").read_text(encoding="utf-8").splitlines()
        self.assertNotIn(".stryker-tmp/", ignored)
        self.assertNotIn("apps/*/reports/mutation/", ignored)

    def test_e6_hold_every_committed_typescript_lock_agrees_with_the_manifest_the_factory_writes(self) -> None:
        """HOLD (teeth: restore one lock from git and see it fail): the root record of each lock names both."""
        locks = [*(ROOT / "assets/languages/typescript/locks").glob("package-lock*.json"),
                 *(ROOT / "assets/frontends/react-vite/locks").glob("typescript-backend*.json")]
        self.assertEqual(len(locks), 12)
        for lock in locks:
            with self.subTest(lock=lock.name):
                packages = json.loads(lock.read_text(encoding="utf-8"))["packages"]
                declared = packages.get("apps/service", packages[""]).get("devDependencies", {})
                for package in PACKAGES:
                    self.assertEqual(declared.get(package), EXACT)
                    self.assertEqual(packages[f"node_modules/{package}"]["version"], EXACT)

    @unittest.skipUnless(shutil.which("npm") and os.environ.get("FACTORY_BACKENDS", "").find("typescript") >= 0,
                         "heavy: needs npm, the network and FACTORY_BACKENDS=typescript")
    def test_e7_audit_stays_green_over_the_new_tree(self) -> None:
        project = self.project("memory")
        for command in (["npm", "ci"], ["npm", "audit", "--audit-level=critical"]):
            done = subprocess.run(command, cwd=project, env=clean_environment(), text=True, capture_output=True,
                                  timeout=600)
            self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
