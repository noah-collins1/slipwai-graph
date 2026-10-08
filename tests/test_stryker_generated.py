"""S41 (US2): what a generated TypeScript service is given for Stryker, and what the project's gates keep of it.

T002 (rule 1 · AC-S41-2 part, -11, -13 part): the two exact devDependencies, `stryker.config.json` per service, the
wrapper once per project, the `mutation-full` line, the ignore lines and the committed locks that agree with the
manifest. Projects are generated once per class; nothing is run except `make -npq`, the wrapper with no arguments and
(gated) `npm audit`.
"""
from __future__ import annotations

import hashlib
import importlib.util
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
from slipwai.project.mutation import UNWIRED, mutation_command, mutation_notes
from slipwai.project.stryker import FULL_COMMAND, SCRIPT_PATH
from slipwai.scaffold import write_project
from slipwai.selection import Selection
from slipwai.services import App, default_apps

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
                self.assertTrue(Path(script).stat().st_mode & 0o100)
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
            self.assertTrue(Path(repo / "delivery" / SCRIPT_PATH).stat().st_mode & 0o100)
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

    def test_e6_the_generated_makefile_carries_the_note_and_its_rules_and_help_are_unchanged(self) -> None:
        """Teeth: add a global variable to the note and `rules.json` no longer equals the text."""
        project = self.project("postgres")
        text = (project / "Makefile").read_text(encoding="utf-8")
        self.assertIn(mutation_notes([service("service", "typescript")]), text)
        sys.path.insert(0, str(ROOT / "assets" / "toolkit" / "scripts"))
        rules = importlib.import_module("verify_scoped.rules")
        held = json.loads((project / "scripts/verify_scoped/rules.json").read_text(encoding="utf-8"))
        self.assertEqual(rules.from_text(text), held)
        helped = subprocess.run(["make", "-s", "help"], cwd=project, env=clean_environment(), text=True,
                                capture_output=True, timeout=60).stdout
        self.assertRegex(helped, r"(?m)^  mutation-full +\S")

    @unittest.skipUnless(shutil.which("npm") and os.environ.get("FACTORY_BACKENDS", "").find("typescript") >= 0,
                         "heavy: needs npm, the network and FACTORY_BACKENDS=typescript")
    def test_e7_audit_stays_green_over_the_new_tree(self) -> None:
        project = self.project("memory")
        for command in (["npm", "ci"], ["npm", "audit", "--audit-level=critical"]):
            done = subprocess.run(command, cwd=project, env=clean_environment(), text=True, capture_output=True,
                                  timeout=600)
            self.assertEqual(done.returncode, 0, done.stdout + done.stderr)


# sha256 of what the other backends' notes and the gates page said before this slice: not this rule's to change.
BEFORE = {"go": "db4dabb3917fb51911370261d9328bda8137d8b165bd111f64385d7dbc46d76f",
          "java-spring": "ccfe2452d786d21eb47acc8d17d02a0d9ca8103932c3cd2f0ebba5273d657fcf",
          "java-quarkus": "74fde152fd96f87e4597fb976e8827555cba9631feccb67bd7196c4776bd283a",
          "python": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"}
GATES_PAGE = "53dad482d8dc5e54762bdcb6edf5045e520235cd201f8e38089034be900e1660"
SKILL = ROOT / "assets/toolkit/skills/mutation-testing/SKILL.md"
HAND_WIRED = ("- If no Stryker setup exists in a JS/TS project, recommend adding it before doing manual mutation "
              "analysis.\n")
SKILL_WITHOUT_THE_PASSAGE = "9bb3f69cec19d36de3b9b6a6750fee371830b096ffc9bc6e66111997f8e51c1e"


def service(name: str, backend: str) -> App:
    language, _, framework = backend.partition("-")
    return App(name, f"apps/{name}", "service", language, {"spring": "spring-boot", "quarkus": "quarkus"}.get(
        framework), 3000)


def flat(text: str) -> str:
    return " ".join(line.removeprefix("# ").removeprefix("#").strip() for line in text.splitlines())


class WordsTest(unittest.TestCase):
    def test_e1_the_typescript_note_carries_the_six_facts_and_the_other_notes_are_what_they_were(self) -> None:
        note = flat(mutation_notes([service("orders", "typescript")]))
        for fact in ("Stryker", "`scripts/stryker-mutation.py`", "`apps/orders/reports/mutation/mutation.json`",
                     "decides the verdict", "// Stryker disable next-line <mutator>: <reason>", "named in the commit",
                     "`related`", "`tsconfigFile`"):
            self.assertIn(fact, note)
        self.assertNotIn("__APP__", note)
        for backend, digest in BEFORE.items():
            self.assertEqual(hashlib.sha256(mutation_notes([service("orders", backend)]).encode()).hexdigest(), digest,
                             backend)

    def test_e1_note_and_fragment_say_the_default_starter_is_red_and_what_alone_excuses_a_mutant(self) -> None:
        """D217 item 1 and D219: held in the note a project reads and in the entry its maintainer reads."""
        note = flat(mutation_notes([service("orders", "typescript")]))
        fragment = " ".join((ROOT / "changelog.d/stryker-mutation.md").read_text(encoding="utf-8").split())
        for text in (note, fragment):
            for sentence in ("default TypeScript starter's `make mutation-full` fails the day it is generated",
                             "its own starter tests leave survivors",
                             "a slice that edits one of those files meets that file's survivors in its scoped "
                             "`make mutation`",
                             "minimal starter is green",
                             "fix is planned",
                             "`Incomplete`",
                             "Only a `// Stryker disable next-line <mutator>: <reason>` comment excuses a mutant",
                             "`excludedMutations` in the config and block or file-wide disable comments do not"):
                self.assertIn(sentence, text)

    def test_e2_the_command_text_names_the_wrapper_and_the_report_and_only_the_stubs_are_unwired(self) -> None:
        for backends in (["typescript"], ["go", "typescript"]):
            text = flat(mutation_command(backends))
            for words in ("scripts/stryker-mutation.py", "reports/mutation/mutation.json",
                          "make mutation SINCE=<review-base>", "CI and the trunk get the sweep"):
                self.assertIn(words, text)
            self.assertNotIn("refuses until a tool is wired", text)
        for backends in (["python"], ["java-quarkus"]):
            self.assertIn("refuses until a tool is wired", flat(mutation_command(backends)))
        self.assertIn("Python and Quarkus", UNWIRED)
        self.assertNotIn("TypeScript", UNWIRED)

    def test_e3_the_skill_says_a_generated_service_is_wired_and_is_otherwise_what_it_was(self) -> None:
        """HOLD for every other line (teeth: edit another line and the digest moves)."""
        text = SKILL.read_text(encoding="utf-8")
        self.assertNotIn(HAND_WIRED, text)
        for words in ("already wired", "stryker.config.json", "scripts/stryker-mutation.py",
                      "reports/mutation/mutation.json", "no `.mjs`", "no `mutation:diff`", "no threshold"):
            self.assertIn(words, text)
        rest = "".join(line for line in text.splitlines(keepends=True) if "already wired" not in line)
        self.assertEqual(hashlib.sha256(rest.encode()).hexdigest(), SKILL_WITHOUT_THE_PASSAGE)

    def test_e4_the_pages_say_stryker_is_wired_and_the_gates_page_and_the_adr_are_as_they_were(self) -> None:
        for page in ("docs/backend-obligations.md", "docs/requirements.md"):
            text = flat((ROOT / page).read_text(encoding="utf-8"))
            self.assertIn("scripts/stryker-mutation.py", text, page)
            self.assertNotIn("TypeScript** and **Python** exit 2", text, page)
            self.assertNotIn("no tool wired (TypeScript, Python", text, page)
        gates = hashlib.sha256((ROOT / "docs/verification.md").read_bytes()).hexdigest()
        self.assertEqual(gates, GATES_PAGE)
        adr = (ROOT / "delivery/docs/adr/0009-stryker-for-typescript-mutation.md").read_text(encoding="utf-8")
        self.assertIn("## Status\n\nProposed\n", adr)
        decision = " ".join(adr.split())
        self.assertIn("`@stryker-mutator/core` 10.0.0 and `@stryker-mutator/vitest-runner` 10.0.0", decision)

    def test_e5_the_provisional_gate_reads_stryker_config_as_gate_configuration(self) -> None:
        spec = importlib.util.spec_from_file_location("provisional_under_test",
                                                      ROOT / "assets/toolkit/scripts/provisional.py")
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        for name in ("stryker.config.json", "stryker.config.mjs", "stryker.config.js", "biome.jsonc", "go.mod"):
            self.assertIsNotNone(module.GATE_CONFIGURATION.fullmatch(name), name)
        for name in ("stryker.config.json.bak", "mystryker.config.json", "stryker.json"):
            self.assertIsNone(module.GATE_CONFIGURATION.fullmatch(name), name)
