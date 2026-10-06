"""S08 T002 (rule 1 · AC-S08-11, AC-S08-13): two targets, `mutation` one script line and `mutation-full` today's recipe.

Projects are generated once per class in the shapes the rule names; the make database is read with
`make -npq -f Makefile .DEFAULT`, which runs nothing. The script's delegation is proved with a fake `--make` written
into the temp directory that logs its arguments.
"""
from __future__ import annotations

import importlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from scoped_fixture import LINE as SCOPED
from scoped_fixture import ShapeCase
from stamp_fixture import CI_MARKERS, GIT_STATE, MAKE_STATE
from support import FactoryTestCase
from test_layout import DELIVERY
from test_mutation_borders import loaded
from test_scoped_targets import build, database
from test_verify_stamp_pinned import gate_prerequisites

from slipwai.assets import ROOT
from slipwai.catalog import family_of, framework_of
from slipwai.project.native_commands import STEP, commands_of, merged
from slipwai.scaffold import write_project
from slipwai.selection import Selection
from slipwai.services import App, default_apps

sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "assets" / "toolkit" / "scripts"))

SCRIPT = ROOT / "assets/toolkit/scripts/mutation-scope.py"
LINE = '@python3 scripts/mutation-scope.py --make "$(MAKE)" --makefile "$(firstword $(MAKEFILE_LIST))"'
# shape -> the `<backend>:<path>` words, one per service in service order
SERVICES = {
    "go-web": ["go:apps/service"],
    "two-go": ["go:apps/service", "go:apps/second"],
    "standard-spring-web": ["java-spring:apps/service"],
    "model-typescript-web": ["typescript:apps/service"],
    "standard-python": ["python:apps/service"],
    "standard-quarkus": ["java-quarkus:apps/service"],
}
PORTS = {"typescript": 3000}


def clean_environment() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if k not in CI_MARKERS + MAKE_STATE + GIT_STATE + ("SINCE",)}


def recipe_of(makefile: str, target: str) -> list[str]:
    """The recipe lines (tab removed) of the first rule for `target`."""
    lines = makefile.splitlines()
    starts = [i for i, line in enumerate(lines) if re.match(rf"^{re.escape(target)}:(?!=)", line)]
    if not starts:
        return []
    start = starts[0]
    found = []
    for line in lines[start + 1:]:
        if not line.startswith("\t"):
            break
        found.append(line[1:])
    return found


def full_recipe(words: list[str]) -> list[str]:
    """What `mutation` held before this slice: each service's own recipe, merged — built here from the factory's
    per-backend table, not copied from the new code."""
    apps = []
    for word in words:
        backend, path = word.split(":")
        apps.append(App(path.split("/")[-1], path, "service", family_of(backend), framework_of(backend), 3000))
    return steps_of(merged(commands_of(apps, apps))["mutation"])


def steps_of(recipe: str) -> list[str]:
    return recipe.split(STEP)


def fake_make(directory: Path, status: int) -> tuple[Path, Path]:
    """An executable that logs its arguments one per line, `--` between calls, and exits with `status`."""
    log = directory / "make.log"
    program = directory / "fake-make"
    program.write_text(f'#!/bin/sh\nprintf \'%s\\n\' "$@" >> "{log}"\necho -- >> "{log}"\nexit {status}\n',
                       encoding="utf-8")
    program.chmod(program.stat().st_mode | stat.S_IXUSR)
    return program, log


class MutationTargetsTest(FactoryTestCase):
    longMessage = False
    parent: Path
    projects: dict[str, Path]
    databases: dict[str, Any]

    @classmethod
    def setUpClass(cls) -> None:
        cls.parent = Path(tempfile.mkdtemp(prefix="mutation-targets-"))
        cls.addClassCleanup(shutil.rmtree, cls.parent, ignore_errors=True)
        cls.projects = {}
        cls.databases = {}

    def project(self, name: str) -> Path:
        if name not in self.projects:
            self.projects[name] = build(self.parent, name, self)
            self.databases[name] = database(self.projects[name])
        return self.projects[name]

    def text(self, name: str) -> str:
        return (self.project(name) / "Makefile").read_text(encoding="utf-8")

    def test_e1_mutation_is_one_script_line_with_a_word_per_service_in_service_order(self) -> None:
        for name, words in SERVICES.items():
            with self.subTest(shape=name):
                self.assertEqual(recipe_of(self.text(name), "mutation"), [f"{LINE} {' '.join(words)}"])

    def test_e2_mutation_full_is_the_recipe_mutation_was_and_is_listed(self) -> None:
        for name, words in SERVICES.items():
            with self.subTest(shape=name):
                text = self.text(name)
                self.assertEqual(recipe_of(text, "mutation-full"), full_recipe(words))
                self.assertRegex(text, r"(?m)^mutation-full: ## \S.*$")
                self.assertRegex(text, r"(?m)^\.PHONY: mutation-full\nmutation-full: ")
                helped = subprocess.run(["make", "-s", "help"], cwd=self.project(name), env=clean_environment(),
                                        text=True, capture_output=True, timeout=60).stdout
                self.assertRegex(helped, r"(?m)^  mutation-full +\S")

    def test_e2_the_scripts_reconstruction_of_the_recipe_is_the_generated_one_for_every_shape(self) -> None:
        """T018 (D138 item 3): what the script compares `mutation-full` with is what the factory wrote there. Teeth:
        change the Go or Spring line in `native_commands.py` and this fails."""
        module = loaded(SCRIPT)
        for name, words in SERVICES.items():
            with self.subTest(shape=name):
                services = [tuple(word.split(":", 1)) for word in words]
                self.assertEqual(module.factory_recipe(services), recipe_of(self.text(name), "mutation-full"))

    def test_e3_hold_neither_target_is_reachable_from_the_gate_or_the_ci_rule(self) -> None:
        """HOLD (teeth: add `mutation` as a prerequisite of `verify-checks`): the gate's rules do not reach either."""
        for name in SERVICES:
            with self.subTest(shape=name):
                text = self.text(name)
                rules = self.databases.get(name) or database(self.project(name))
                reached: set[str] = set()
                todo = ["verify", "verify-checks", "ci"]
                while todo:
                    target = todo.pop()
                    needs, recipe = rules.get(target, ([], []))
                    named = [w for line in recipe if "$(MAKE)" in line for w in line.split()]
                    for word in [*needs, *named]:
                        if word in rules and word not in reached:
                            reached.add(word)
                            todo.append(word)
                self.assertFalse({"mutation", "mutation-full"} & reached, name)
                self.assertFalse({"mutation", "mutation-full"} & set(gate_prerequisites(text)), name)
                self.assertTrue((self.project(name) / ".github/workflows").is_dir())
                for workflow in (self.project(name) / ".github/workflows").glob("*"):
                    self.assertNotIn("mutation", workflow.read_text(encoding="utf-8"), workflow.name)

    def hold(self, project: Path) -> tuple[Any, str, str | None, str | None]:
        """S06's own hold (D140) over this project's Makefile: the rules module, the Makefile text, `text_problem` and
        `difference`, each read as the scoped run reads them."""
        sys.path.insert(0, str(ROOT / "assets/toolkit/scripts"))
        rules = importlib.import_module("verify_scoped.rules")
        records = importlib.import_module("verify_scoped.record")
        makefile = project / "Makefile"
        data = records.database("make", str(makefile))
        names = json.loads((project / "project.json").read_text(encoding="utf-8"))["deployables"]
        flat = [f"{gate}-{n}" for gate in ("lint", "typecheck", "test") for n in names
                if f"{gate}-{n}" in data.needs and not n.startswith("integration")]
        path = str(project / "scripts/verify_scoped/rules.json")
        problem = rules.text_problem(str(makefile), path, {})
        found = rules.difference(rules.load(path), data, flat, rules.project_exports(data, str(project)))
        return rules, makefile.read_text(encoding="utf-8"), problem, found

    def test_e4_hold_the_scoped_gates_text_hold_reads_the_new_makefile_without_a_difference(self) -> None:
        """HOLD (teeth: the next example): `rules.json`'s digest is the Makefile text's, and the hold finds nothing."""
        for name in SERVICES:
            with self.subTest(shape=name):
                project = self.project(name)
                rules, text, problem, found = self.hold(project)
                held = json.loads((project / "scripts/verify_scoped/rules.json").read_text("utf-8"))
                self.assertEqual(held["makefile"], rules.text_digest(text))
                self.assertIsNone(problem)
                self.assertIsNone(found)
                for target in ("mutation", "mutation-full"):
                    self.assertNotIn(target, held["rules"])

    def test_e4_teeth_a_global_variable_every_rule_reads_is_a_text_the_hold_says_is_not_the_factorys(self) -> None:
        copy = Path(tempfile.mkdtemp(dir=self.parent)) / "project"
        shutil.copytree(self.project("go-web"), copy, symlinks=True)
        makefile = copy / "Makefile"
        makefile.write_text(makefile.read_text(encoding="utf-8") + "\nSHELL := /bin/sh\n", encoding="utf-8")
        _, _, problem, _ = self.hold(copy)
        self.assertIn("not the text the factory wrote", problem or "")

    def test_e5_the_script_delegates_to_mutation_full_and_passes_the_status_through(self) -> None:
        for status in (0, 7):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as directory:
                program, log = fake_make(Path(directory), status)
                done = subprocess.run(
                    ["python3", "-B", str(SCRIPT), "--make", str(program), "--makefile", "Makefile.x",
                     "go:apps/service", "go:apps/billing"],
                    cwd=directory, env=clean_environment(), text=True, capture_output=True, timeout=60)
                self.assertEqual(done.returncode, status, done.stdout + done.stderr)
                called = log.read_text(encoding="utf-8").splitlines() if log.exists() else []
                self.assertEqual(called, ["--no-print-directory", "-f", "Makefile.x", "mutation-full", "--"])

    def test_e5_an_unknown_backend_or_a_malformed_word_is_a_usage_error_of_one_line(self) -> None:
        for arguments in (["cobol:apps/service"], ["go"], ["go:"]):
            with self.subTest(arguments=arguments), tempfile.TemporaryDirectory() as directory:
                program, log = fake_make(Path(directory), 0)
                done = subprocess.run(
                    ["python3", "-B", str(SCRIPT), "--make", str(program), "--makefile", "Makefile", *arguments],
                    cwd=directory, env=clean_environment(), text=True, capture_output=True, timeout=60)
                self.assertEqual(done.returncode, 2, done.stdout + done.stderr)
                self.assertEqual(len(done.stderr.strip().splitlines()), 1, done.stderr)
                self.assertFalse(log.exists(), "make was called")

    def test_e5_zero_services_is_still_the_sweep(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            program, log = fake_make(Path(directory), 0)
            done = subprocess.run(["python3", "-B", str(SCRIPT), "--make", str(program), "--makefile", "Makefile"],
                                  cwd=directory, env=clean_environment(), text=True, capture_output=True, timeout=60)
            self.assertEqual(done.returncode, 0, done.stderr)
            self.assertIn("mutation-full", log.read_text(encoding="utf-8"))

    def test_e6_the_script_ships_names_no_service_path_and_leaves_no_bytecode(self) -> None:
        shipped = self.project("go-web") / "scripts/mutation-scope.py"
        self.assertEqual(shipped.read_text(encoding="utf-8"), SCRIPT.read_text(encoding="utf-8"))
        for literal in ("apps/service", "apps/web"):
            self.assertNotIn(literal, SCRIPT.read_text(encoding="utf-8"))
        before = set(SCRIPT.parent.rglob("__pycache__"))
        probe = ("import importlib.util, sys; s = importlib.util.spec_from_file_location('m', sys.argv[1]); "
                 "m = importlib.util.module_from_spec(s); s.loader.exec_module(m)")
        done = subprocess.run(["python3", "-B", "-c", probe, str(SCRIPT)], text=True, capture_output=True, timeout=60)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(set(SCRIPT.parent.rglob("__pycache__")), before)

    def test_e6_an_adopted_layout_ships_it_in_its_delivery_scripts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "moved"
            apps = default_apps("go", "none", Selection({"http": "none"}))
            write_project(repo, "moved", "standard", "none", apps, layout=DELIVERY)
            self.assertTrue((repo / "delivery/scripts/mutation-scope.py").is_file())
            makefile = (repo / "delivery/Makefile").read_text(encoding="utf-8")
            self.assertIn("python3 delivery/scripts/mutation-scope.py", makefile)


class TheScopedGateStillScopesAProjectWithTheNewTargetsTest(ShapeCase):
    shape = "go-web"

    def test_e4_hold_a_one_file_source_change_on_a_slice_branch_is_not_the_full_gate(self) -> None:
        """AC-S08-13 end to end: the generated Go project, on `slice/S1`, one production file changed. `make
        verify-scoped` (its checks printed, not run: `STANDIN_DRY`) never says the full gate runs."""
        self.edit("apps/service/main.go", "\n// an edit\n")
        run = self.scoped({"STANDIN_DRY": "1"})
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertTrue(self.scoped_lines(run), run.stdout)
        self.assertNotIn("the full gate runs", run.stdout + run.stderr)
        ran = [line for line in self.scoped_lines(run) if line.startswith(SCOPED + "run  lint-service")]
        self.assertTrue(ran, run.stdout)
