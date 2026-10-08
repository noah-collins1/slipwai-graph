"""S42 (US2): what a generated Python service is given for mutmut, and what the project's gates keep of it.

T010 (rule 9 · AC-S42-11 placeholder half): the words — the Makefile note, command text, skill and pages.

T002 (rule 1 · AC-S42-1, -4 recipe, -9 first clause, -11 `mutation-full` carries no `SINCE`): the exact dev pin, the
`[tool.mutmut]` table per service, the wrapper once per project, the `mutation-full` line, the ignore line and the
committed locks that agree with the manifest. Projects are generated once per class; nothing is run except `make -npq`,
the wrapper with no arguments and (where `uv` is on PATH) `uv lock --check`.
"""
from __future__ import annotations

import ast
import hashlib
import importlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

from stamp_fixture import GIT_STATE, git
from support import FactoryTestCase, commit_all
from test_mutation_targets import LINE, recipe_of
from test_stryker_generated import BEFORE, GATES_PAGE, SKILL_WITHOUT_THE_PASSAGE, clean_environment

from slipwai.assets import ROOT
from slipwai.layout import Layout
from slipwai.project.languages.python import python_pyproject
from slipwai.project.mutation import UNWIRED, mutation_command, mutation_notes
from slipwai.project.mutmut import FULL_COMMAND, SCRIPT_PATH
from slipwai.scaffold import write_project
from slipwai.selection import Selection
from slipwai.services import App, default_apps

sys.dont_write_bytecode = True

PIN = "mutmut==3.8.0"
TABLE = {
    "source_paths": ["src"],
    "pytest_add_cli_args_test_selection": ["tests", "--ignore=tests/integration"],
    "pytest_add_cli_args": ["-p", "no:xdist"],
}
LOCKS = ROOT / "assets/languages/python/locks"
CLOSURE = ("mutmut", "libcst", "textual", "coverage", "setproctitle", "click")
SKILL = ROOT / "assets/toolkit/skills/mutation-testing/SKILL.md"
NOTE_FACTS = ("mutmut 3.8.0", "`scripts/mutmut-mutation.py`", "`apps/orders/pyproject.toml`", "`apps/orders/mutants/`",
              "`.meta`", "decides the verdict itself", "never from mutmut's exit status", "`uv sync --locked`",
              "bare `# pragma: no mutate`", "named in the commit",
              "`# pragma: no mutate block`, `start` and `end`, and `do_not_mutate_patterns`, "
              "`mutate_only_covered_lines` and `max_stack_depth`", "fails the run",
              "default Python starter's `make mutation-full` reports survivors the day it is generated",
              "its own starter tests leave them", "minimal starter", "is green", "`tests/integration`", "`-p no:xdist`",
              "scopes itself on a `slice/<id>` branch", "`make mutation SINCE=<the commit before the merge>`")


def service(name: str, backend: str) -> App:
    language, _, framework = backend.partition("-")
    return App(name, f"apps/{name}", "service", language, {"spring": "spring-boot", "quarkus": "quarkus"}.get(
        framework), 3000)


def flat(text: str) -> str:
    return " ".join(line.removeprefix("# ").removeprefix("#").strip() for line in text.splitlines())


def add_service(project: Path, name: str, language: str) -> None:
    if git(project, "status", "--short").strip():  # `add-service` refuses a tree with uncommitted work
        commit_all(project, "base")
    subprocess.run([str(ROOT / "slipwai"), "add-service", name, "--language", language], cwd=project, check=True,
                   capture_output=True, timeout=120)


class MutmutGeneratedTest(FactoryTestCase):
    parent: Path
    projects: dict[str, Path]

    @classmethod
    def setUpClass(cls) -> None:
        cls.parent = Path(tempfile.mkdtemp(prefix="mutmut-generated-"))
        cls.addClassCleanup(shutil.rmtree, cls.parent, ignore_errors=True)
        cls.projects = {}

    def project(self, name: str) -> Path:
        if name not in self.projects:
            if name == "mini":
                made = self.generate(self.parent, name, "standard", "python", "none", http="none",
                                     event_store="memory")
            elif name == "two-py":
                made = self.generate(self.parent, name, "standard", "python", "none", http="none")
                add_service(made, "second", "python")
            elif name == "go-py":
                made = self.generate(self.parent, name, "standard", "go", "none", http="none")
                add_service(made, "second", "python")
            elif name == "go":
                made = self.generate(self.parent, name, "standard", "go", "none", http="none")
            elif name == "ts":
                made = self.generate(self.parent, name, "standard", "typescript", "none", http="none")
            else:
                made = self.generate(self.parent, name, "event-modelling", "python", "none")
            self.projects[name] = made
        return self.projects[name]

    def makefile(self, name: str) -> str:
        return (self.project(name) / "Makefile").read_text(encoding="utf-8")

    def test_e1_the_pin_is_exact_in_the_dev_group_of_every_python_service(self) -> None:
        for name, services in (("default", ["service"]), ("mini", ["service"]), ("two-py", ["service", "second"]),
                               ("go-py", ["second"])):
            for service in services:
                with self.subTest(project=name, service=service):
                    manifest = tomllib.loads((self.project(name) / f"apps/{service}/pyproject.toml").read_text(
                        encoding="utf-8"))
                    dev = manifest["dependency-groups"]["dev"]
                    self.assertEqual(dev.count(PIN), 1)
                    self.assertEqual(dev, sorted(dev))
                    self.assertEqual([pin for pin in dev if pin.startswith("mutmut")], [PIN])

    def test_e2_every_service_has_the_table_and_a_comment_above_each_key(self) -> None:
        for name, service in (("default", "service"), ("mini", "service"), ("two-py", "second"),
                              ("go-py", "second")):
            with self.subTest(project=name, service=service):
                text = (self.project(name) / f"apps/{service}/pyproject.toml").read_text(encoding="utf-8")
                self.assertEqual(tomllib.loads(text)["tool"].get("mutmut"), TABLE)
                lines = text.splitlines()
                for key in TABLE:
                    at = next((i for i, line in enumerate(lines) if line.startswith(f"{key} = ")), 0)
                    self.assertTrue(at and lines[at - 1].startswith("# "), f"{key}: no comment above it")

    def test_e3_the_wrapper_is_one_executable_script_per_python_project(self) -> None:
        for name in ("default", "two-py", "go-py"):
            script = self.project(name) / SCRIPT_PATH
            with self.subTest(project=name):
                self.assertTrue(script.is_file())
                self.assertTrue(os.access(script, os.X_OK))
                text = script.read_text(encoding="utf-8")
                self.assertNotIn("apps/service", text)
                self.assertNotIn("apps/web", text)
        for name in ("go", "ts"):
            self.assertFalse((self.project(name) / SCRIPT_PATH).exists(), name)
        script = self.project("default") / SCRIPT_PATH
        for arguments in ([], ["apps/service", "--bogus"]):
            done = subprocess.run([sys.executable, "-B", str(script), *arguments], cwd=self.project("default"),
                                  text=True, capture_output=True, timeout=60)
            self.assertEqual(done.returncode, 2, arguments)
            lines = (done.stdout + done.stderr).strip().splitlines()
            self.assertEqual(len(lines), 1, arguments)
            self.assertTrue(lines[0].startswith("mutation: "), arguments)
        self.assertEqual(list(self.project("default").rglob("__pycache__")), [])

    def test_e3_in_an_adopted_layout_the_wrapper_lands_under_the_delivery_scripts(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mutmut-layout-") as directory:
            repo = Path(directory) / "wrapped"
            write_project(repo, "wrapped", "event-modelling", "none", default_apps("python", "none", Selection({})),
                          layout=Layout("delivery"))
            self.assertTrue(os.access(repo / "delivery" / SCRIPT_PATH, os.X_OK))
            self.assertFalse((repo / SCRIPT_PATH).exists())

    def test_e4_mutation_full_is_the_wrapper_per_service_with_no_since_and_no_guard(self) -> None:
        one = recipe_of(self.makefile("default"), "mutation-full")
        self.assertEqual(one, ["python3 scripts/mutmut-mutation.py apps/service"])
        self.assertEqual(FULL_COMMAND.replace("__APP__", "apps/service"), one[0])
        two = recipe_of(self.makefile("two-py"), "mutation-full")
        self.assertEqual(two, [FULL_COMMAND.replace("__APP__", f"apps/{n}") for n in ("service", "second")])
        mixed = recipe_of(self.makefile("go-py"), "mutation-full")
        self.assertEqual(mixed, ["python3 scripts/go-mutation.py apps/service $(if $(SINCE),--since $(SINCE))",
                                 FULL_COMMAND.replace("__APP__", "apps/second")])
        for line in (*one, *two):
            for word in ("SINCE", "$(if", "@command -v"):
                self.assertNotIn(word, line)

    def test_e4_the_scoped_target_is_what_it_was(self) -> None:
        for name, words in (("default", "python:apps/service"), ("two-py", "python:apps/service python:apps/second")):
            self.assertEqual(recipe_of(self.makefile(name), "mutation"), [f"{LINE} {words}"], name)

    def test_e4_hold_no_gate_reaches_the_mutation_targets(self) -> None:
        """HOLD (teeth: add `mutation-full` as a prerequisite of `verify-checks`): the gates' rules name neither."""
        for name in ("default", "go-py"):
            for rule in ("verify", "verify-checks", "ci"):
                line = re.search(rf"(?m)^{rule}:(.*)$", self.makefile(name))
                self.assertIsNotNone(line, rule)
                self.assertNotIn("mutation", line.group(1) if line else "", f"{name}: {rule}")

    def test_e5_the_ignore_line_leads_the_python_block_and_git_ignores_what_a_run_leaves(self) -> None:
        project = self.project("default")
        if git(project, "status", "--short").strip():
            commit_all(project, "as generated")
        ignored = (project / ".gitignore").read_text(encoding="utf-8").splitlines()
        self.assertIn("apps/*/mutants/", ignored)
        self.assertEqual(ignored[ignored.index("apps/*/mutants/") + 1], "__pycache__/")
        leaving = project / "apps/service/mutants/src/x.py.meta"
        leaving.parent.mkdir(parents=True)
        leaving.write_text("{}", encoding="utf-8")
        self.assertEqual(git(project, "status", "--short").strip(), "", "a run's leavings show in git")
        for name in ("go", "ts"):
            self.assertNotIn("apps/*/mutants/", (self.project(name) / ".gitignore").read_text(encoding="utf-8"))

    @unittest.skipUnless(shutil.which("uv"), "uv is not on PATH")
    def test_e6_hold_every_committed_lock_agrees_with_its_manifest_and_names_mutmut_and_its_closure(self) -> None:
        """HOLD (teeth: restore one lock from git and see it fail): `uv lock --check` accepts each combination."""
        template = (ROOT / "assets/languages/python/app/pyproject.toml").read_text(encoding="utf-8")
        for axes, lock in (({}, "uv.lock"), ({"event-store": "postgres"}, "uv-postgres.lock"),
                           ({"http": "fastapi"}, "uv-fastapi.lock"),
                           ({"http": "fastapi", "event-store": "postgres"}, "uv-fastapi-postgres.lock")):
            with self.subTest(lock=lock), tempfile.TemporaryDirectory(prefix="mutmut-lock-") as directory:
                staging = Path(directory)
                (staging / "pyproject.toml").write_text(python_pyproject(template, Selection(axes)), encoding="utf-8")
                text = (LOCKS / lock).read_text(encoding="utf-8")
                (staging / "uv.lock").write_text(text, encoding="utf-8")
                env = {k: v for k, v in os.environ.items() if k not in GIT_STATE}
                done = subprocess.run(["uv", "lock", "--check", "--project", str(staging)], env=env, text=True,
                                      capture_output=True, timeout=300)
                self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
                packages = {entry["name"] for entry in tomllib.loads(text)["package"]}
                for name in CLOSURE:
                    self.assertIn(name, packages)


class MutmutWordsTest(unittest.TestCase):
    def test_t010_e1_python_has_a_note_with_the_facts_and_the_others_are_what_they_were(self) -> None:
        note = flat(mutation_notes([service("orders", "python")]))
        for fact in NOTE_FACTS:
            self.assertIn(fact, note)
        self.assertNotIn("__APP__", note)
        self.assertNotIn("follow-on", note)
        self.assertNotIn("is planned", note)
        both = flat(mutation_notes([service("a", "python"), service("b", "python")]))
        self.assertIn("`apps/a/mutants/` and `apps/b/mutants/`", both)
        for backend, digest in BEFORE.items():
            if backend != "python":
                self.assertEqual(hashlib.sha256(mutation_notes([service("orders", backend)]).encode()).hexdigest(),
                                 digest, backend)
        self.assertNotIn("mutmut", mutation_notes([service("orders", "typescript")]))

    def test_t010_e2_the_command_text_names_the_wrapper_and_the_report_and_only_quarkus_is_unwired(self) -> None:
        for backends in (["python"], ["go", "python"]):
            text = flat(mutation_command(backends))
            for words in ("mutmut", "scripts/mutmut-mutation.py", "mutants/", "make mutation SINCE=<review-base>",
                          "CI and the trunk get the sweep"):
                self.assertIn(words, text)
            self.assertNotIn("refuses until a tool is wired", text)
        self.assertIn("refuses until a tool is wired", flat(mutation_command(["java-quarkus"])))
        self.assertIn("refuses until a tool is wired", flat(mutation_command(["python", "java-quarkus"])))
        self.assertIn("Quarkus", UNWIRED)
        self.assertNotIn("Python", UNWIRED)

    def test_t010_e3_the_skill_says_a_generated_python_service_is_wired_and_is_otherwise_what_it_was(self) -> None:
        """HOLD for every other line (teeth: edit another line and the digest moves)."""
        text = SKILL.read_text(encoding="utf-8")
        self.assertNotIn("hand-wire mutmut", text)
        lines = [line for line in text.splitlines(keepends=True) if "Python service this factory generated" in line]
        self.assertEqual(len(lines), 1)
        for words in ("already wired", "[tool.mutmut]", "scripts/mutmut-mutation.py", "mutants/", "`.meta`"):
            self.assertIn(words, lines[0])
        rest = "".join(line for line in text.splitlines(keepends=True) if "already wired" not in line)
        self.assertEqual(hashlib.sha256(rest.encode()).hexdigest(), SKILL_WITHOUT_THE_PASSAGE)

    def test_t010_e4_the_pages_say_mutmut_is_wired_and_the_gates_page_and_the_adr_are_as_they_were(self) -> None:
        for page in ("docs/backend-obligations.md", "docs/requirements.md"):
            text = flat((ROOT / page).read_text(encoding="utf-8"))
            self.assertIn("mutmut 3.8.0", text, page)
            self.assertIn("scripts/mutmut-mutation.py", text, page)
            self.assertNotIn("**Python** exits 2", text, page)
            self.assertNotIn("asking for `mutmut` on the PATH", text, page)
            self.assertNotIn("(Python, `java-quarkus`)", text, page)
        self.assertIn("only four backends have one wired up", flat((ROOT / "docs/requirements.md").read_text(
            encoding="utf-8")))
        self.assertEqual(hashlib.sha256((ROOT / "docs/verification.md").read_bytes()).hexdigest(), GATES_PAGE)
        adr = (ROOT / "delivery/docs/adr/0010-mutmut-for-python-mutation.md").read_text(encoding="utf-8")
        self.assertIn("## Status\n\nProposed\n", adr)
        self.assertIn("`mutmut==3.8.0`", " ".join(adr.split()))

    def test_t010_e5_stryker_s_fragment_names_java_quarkus_alone_as_a_recorded_stub(self) -> None:
        text = (ROOT / "changelog.d/stryker-mutation.md").read_text(encoding="utf-8")
        self.assertEqual(text.splitlines()[0], "MINOR")
        paragraphs = [block for block in text.split("\n\n") if block.startswith("**Catch-up.**")]
        self.assertEqual(len(paragraphs), 1)
        for where, words in (("body", " ".join(text.split("\n\n")[1].split())), ("catch-up", " ".join(
                paragraphs[0].split()))):
            with self.subTest(where=where):
                self.assertIn("`java-quarkus`", words)
                self.assertNotIn("Python and `java-quarkus`", words)
        stub = " ".join(paragraphs[0].split())
        self.assertIn("`java-quarkus` stays a recorded stub", stub)
        self.assertNotIn("Python and `java-quarkus` stay", stub)


class MutmutNoteGeneratedTest(FactoryTestCase):
    def test_t010_e6_the_generated_makefile_carries_the_note_and_its_rules_and_help_are_unchanged(self) -> None:
        """Teeth: add a global variable to the note and `rules.json` no longer equals the text."""
        with tempfile.TemporaryDirectory(prefix="mutmut-note-") as directory:
            project = self.generate(Path(directory), "noted", "standard", "python", "none", http="none",
                                    event_store="memory")
            text = (project / "Makefile").read_text(encoding="utf-8")
            self.assertIn(mutation_notes([service("service", "python")]), text)
            for line in mutation_notes([service("service", "python")]).splitlines():
                self.assertTrue(line.startswith("#"), f"the note is comments only, never a variable: {line!r}")
            sys.path.insert(0, str(ROOT / "assets" / "toolkit" / "scripts"))
            rules = importlib.import_module("verify_scoped.rules")
            held = json.loads((project / "scripts/verify_scoped/rules.json").read_text(encoding="utf-8"))
            self.assertEqual(rules.from_text(text), held)
            self.assertIsNone(rules.text_problem(str(project / "Makefile"), str(
                project / "scripts/verify_scoped/rules.json"), {}))
            helped = subprocess.run(["make", "-s", "help"], cwd=project, env=clean_environment(), text=True,
                                    capture_output=True, timeout=60).stdout
            self.assertRegex(helped, r"(?m)^  mutation-full +\S")


class WordsOfShippedFilesTest(unittest.TestCase):
    """T021 (Constitution I, the words level): a file a project carries says what the code does now."""

    TRANSIENT = ("skeleton", "refuses to run", "until t0", "not wired by this script yet", "can only fail")

    def test_t021_the_wrapper_s_docstring_carries_no_word_of_the_task_that_wrote_its_first_half(self) -> None:
        text = (ROOT / "assets/languages/python/scripts/mutmut-mutation.py").read_text(encoding="utf-8")
        words = (ast.get_docstring(ast.parse(text)) or "").lower()
        self.assertIn("mutmut", words)
        for word in self.TRANSIENT:
            with self.subTest(word=word):
                self.assertNotIn(word, words)

    def test_t021_check_imports_names_every_directory_it_walks_past_in_the_docstring_that_lists_them(self) -> None:
        tree = ast.parse((ROOT / "assets/toolkit/scripts/check-imports.py").read_text(encoding="utf-8"))
        values = {target.id: ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign)
                  for target in node.targets if isinstance(target, ast.Name) and target.id in ("PRUNED", "OUTPUT")}
        names = sorted({*values["PRUNED"], *(output for output, _ in values["OUTPUT"].values())})
        docstring = next(" ".join((ast.get_docstring(node) or "").split()) for node in tree.body
                         if isinstance(node, ast.FunctionDef) and node.name == "deployables")
        for name in names:
            with self.subTest(name=name):
                self.assertIn(f"`{name}`", docstring)
        count = {5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine"}[len(names)]
        self.assertIn(f"the {count} nobody reads", docstring)


if __name__ == "__main__":
    unittest.main()
