"""R10 (AC-S06-13, AC-S06-6's table half): `verify-scoped.py record` prints what the gate is as JSON.

The record is derived on every call from the make database, `project.json`, the tree and the model, and written
nowhere. Projects are generated once per class; the script is the one the project ships, run as `python3 -B` in it.
The factory's table of what each check reads is held against the check scripts themselves (research R-8): a path
literal a check script names that lies under none of the check's recorded inputs fails here, and the table is widened.
"""
from __future__ import annotations

import ast
import importlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from stamp_fixture import CI_MARKERS, GIT_STATE, MAKE_STATE, git
from support import FactoryTestCase, commit_all
from test_scoped_targets import SHAPES as SHAPE_TABLE
from test_scoped_targets import build

from slipwai.assets import ROOT

sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "assets" / "toolkit" / "scripts"))

SCHEMA = 1
UNIT_KEYS = {"gate", "components", "inputs", "claims", "always", "targets"}
INPUT_KEYS = {"files", "tools", "variables"}
GATES = ("lint", "typecheck", "test")
EVENT_MODEL = "docs/event-model/model.yaml"
PATH_LIKE = re.compile(r"^[\w./-]+$")
SCRIPT = re.compile(r"scripts/[\w./-]+\.py")
# Read by a check and handled outside the table: a changed one runs the full gate (R5), or it is the gate's own.
ROOT_OWN = ("project.json", "Makefile", "GNUmakefile", "makefile", "scripts", ".git")
# A literal that names a path-looking thing a check does not read as an input of the project: the reason is the value.
NOT_AN_INPUT = {
    ".": "the project's own directory, as a working directory",
    "init": "a subcommand of a tool a check launches, not a path",
    ".claude/projects": "under the user's home (`Path.home()`), where the benchmark reads session transcripts",
}


def environment() -> dict[str, str]:
    return {key: value for key, value in os.environ.items() if key not in CI_MARKERS + MAKE_STATE + GIT_STATE}


def record(project: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["python3", "-B", "scripts/verify-scoped.py", "record", *arguments], cwd=project,
                          env=environment(), text=True, capture_output=True, timeout=120)


def loaded(project: Path) -> dict[str, Any]:
    before = git(project, "status", "--porcelain", "--ignored")
    done = record(project)
    assert done.returncode == 0, done.stderr
    assert git(project, "status", "--porcelain", "--ignored") == before, "the record left a file in the project"
    return json.loads(done.stdout)


class RecordCase(FactoryTestCase):
    longMessage = False
    parent: Path
    projects: dict[str, Path]

    @classmethod
    def setUpClass(cls) -> None:
        cls.parent = Path(tempfile.mkdtemp(prefix="scoped-record-"))
        cls.addClassCleanup(shutil.rmtree, cls.parent, ignore_errors=True)
        cls.projects = {}

    def project(self, name: str) -> Path:
        """A shape's project, built once and handed over as a fresh copy: a test may edit what it is given."""
        if name not in self.projects:
            self.projects[name] = build(self.parent, name, self)
        copy = Path(tempfile.mkdtemp(prefix="copy-", dir=self.parent)) / "project"
        shutil.copytree(self.projects[name], copy, symlinks=True)
        return copy


class RecordTest(RecordCase):
    def test_e1_a_typescript_service_and_web_app_record(self) -> None:
        project = self.project("model-typescript-web")
        text = record(project).stdout
        data = json.loads(text)
        self.assertEqual(text, json.dumps(data, indent=2, sort_keys=True) + "\n")
        self.assertEqual(data["schema"], SCHEMA)
        self.assertEqual(data["deployables"]["service"], {"kind": "service", "path": "apps/service",
                                                          "family": "typescript"})
        self.assertEqual(data["deployables"]["web"], {"kind": "web", "path": "apps/web", "family": "typescript",
                                                      "api": "service"})
        checks = data["checks"]
        for gate in GATES:
            for name in ("service", "web"):
                unit = checks[f"{gate}-{name}"]
                self.assertEqual(set(unit), UNIT_KEYS)
                self.assertEqual((unit["gate"], unit["components"], unit["targets"]),
                                 (gate, [name], [f"{gate}-{name}"]))
                self.assertEqual(set(unit["inputs"]), INPUT_KEYS)
                self.assertTrue(unit["claims"])
                self.assertIsNone(unit["always"])
        web = checks["lint-web"]["inputs"]
        self.assertEqual(web["files"], sorted(web["files"]))
        self.assertIn("apps/web/", web["files"])
        self.assertEqual(web["tools"], ["make", "node", "npm", "python3"])
        self.assertEqual(checks["check-agents"]["inputs"], None)
        self.assertEqual(checks["check-agents"]["always"], "no recorded inputs")
        by_id = {contract["id"]: contract for contract in data["contracts"]}
        self.assertEqual(by_id["openapi:service"], {"id": "openapi:service", "kind": "openapi", "owner": "service",
                                                    "paths": ["apps/service/"], "consumers": ["web"]})
        self.assertEqual(by_id["package:api-client"]["consumers"], ["service", "web"])
        self.assertEqual(by_id["package:api-client"]["paths"], ["packages/api-client/"])
        self.assertIn("check-openapi", checks)
        self.assertIn("apps/service/", checks["check-openapi"]["inputs"]["files"])

    def test_e1_two_python_services_and_a_go_one(self) -> None:
        data = loaded(self.project("two-python"))
        self.assertEqual(sorted(unit for unit in data["checks"] if unit[:4] in ("lint", "type", "test")),
                         sorted(f"{gate}-{name}" for gate in GATES for name in ("service", "billing")))
        python = data["checks"]["test-billing"]["inputs"]
        self.assertEqual(python["files"], ["apps/billing/"])
        self.assertEqual(python["tools"], ["interpreter apps/billing/.venv", "make", "python3", "uv"])
        self.assertEqual(data["contracts"], [])
        go = loaded(self.project("model-go-azure"))
        self.assertEqual(go["checks"]["lint-service"]["inputs"]["tools"], ["go", "make", "python3"])
        self.assertIn("go.work", go["checks"]["test-service"]["inputs"]["files"])
        java = loaded(self.project("java-go"))
        self.assertEqual(java["deployables"]["service"]["family"], "java")
        self.assertEqual(java["checks"]["typecheck-service"]["inputs"]["tools"], ["java", "make", "python3"])

    def test_e1_the_tools_a_record_names_are_tools_the_baseline_asks_for(self) -> None:
        """T047 (G7): a tool the stamp never asks of the machine cannot drift against the baseline, so the record must
        not name it. `VERIFY_STAMP` is the list: a `--tool` each, and an `--environment` for each interpreter."""
        buildable = [name for name in SHAPE_TABLE if not name.startswith("integration")]  # their record is not built
        for shape in buildable:
            with self.subTest(shape=shape):
                project = self.project(shape)
                text = (project / "Makefile").read_text(encoding="utf-8")
                words = re.search(r"^VERIFY_STAMP := (.*)$", text, re.M).group(1).split()  # type: ignore[union-attr]
                asked = {words[i + 1] for i, word in enumerate(words) if word == "--tool"}
                asked |= {"interpreter " + words[i + 1] for i, word in enumerate(words) if word == "--environment"}
                for unit, check in loaded(project)["checks"].items():
                    named = set((check["inputs"] or {}).get("tools", []))
                    self.assertEqual(named - asked, set(), unit)

    def test_e5_the_tables_own_claims(self) -> None:
        checks = loaded(self.project("model-typescript-web-cloud"))["checks"]
        for name in ("check-slice-scope", "check-codegraph"):
            self.assertFalse(checks[name]["claims"], name)
            self.assertTrue(checks[name]["always"], name)
        self.assertTrue(checks["check-python"]["always"])
        self.assertFalse(checks["check-python"]["claims"])
        for name in ("check-agents", "check-speckit", "check-extensions", "check-constitution"):
            self.assertEqual((checks[name]["inputs"], checks[name]["claims"], checks[name]["always"]),
                             (None, False, "no recorded inputs"), name)
        for name in ("check-flags", "check-deploy-role", "check-model", "check-ux-gates"):
            self.assertTrue(checks[name]["claims"], name)
            self.assertIsNone(checks[name]["always"], name)
        self.assertEqual(checks["check-ux-gates"]["inputs"]["variables"],
                         ["SLIPWAI_NO_INSTALL", "UX_GATES_REQUIRE", "UX_GATES_SHARD", "UX_GATES_SINCE"])

    def test_e5_a_check_the_project_added_has_no_recorded_inputs(self) -> None:
        project = self.project("model-typescript-web")
        makefile = project / "Makefile"
        makefile.write_text(makefile.read_text(encoding="utf-8")
                            + "\nverify-checks: check-licences\ncheck-licences:\n\t@true\n", encoding="utf-8")
        added = loaded(project)["checks"]["check-licences"]
        self.assertEqual((added["inputs"], added["claims"], added["always"]), (None, False, "no recorded inputs"))


class PackagesTest(RecordCase):
    def contracts(self, project: Path) -> set[str]:
        return {str(contract["id"]) for contract in loaded(project)["contracts"]}

    def test_e3_a_directory_without_a_package_json_is_not_an_npm_contract(self) -> None:
        project = self.project("model-typescript-web")
        (project / "packages" / "shared-go").mkdir()
        (project / "packages" / "shared-go" / "x.go").write_text("package shared\n", encoding="utf-8")
        self.assertNotIn("package:shared-go", self.contracts(project))
        self.assertIn("package:api-client", self.contracts(project))

    def test_e3_a_package_json_added_in_the_working_tree_counts(self) -> None:
        project = self.project("model-typescript-web")
        (project / "packages" / "extra").mkdir()
        (project / "packages" / "extra" / "package.json").write_text("{}\n", encoding="utf-8")
        self.assertIn("package:extra", self.contracts(project))

    def test_e3_a_package_the_base_had_counts_after_the_working_tree_loses_it(self) -> None:
        project = self.project("model-typescript-web")
        git(project, "checkout", "-q", "-b", "slice/S1")
        (project / "packages" / "api-client" / "package.json").unlink()
        self.assertIn("package:api-client", self.contracts(project))


class CannotBuildTest(RecordCase):
    def assert_refused(self, done: subprocess.CompletedProcess[str], words: str) -> None:
        self.assertEqual(done.stdout, "")
        self.assertEqual(done.returncode, 1, done.stderr)
        self.assertEqual(len(done.stderr.splitlines()), 1, done.stderr)
        self.assertIn(words, done.stderr)

    def test_e2_a_makefile_with_no_verify_checks(self) -> None:
        project = self.project("model-typescript-web")
        (project / "bare.mk").write_text("all:\n\t@true\n", encoding="utf-8")
        self.assert_refused(record(project, "--makefile", "bare.mk"), "no `verify-checks`")

    def test_e2_a_deployable_whose_units_are_missing(self) -> None:
        self.assert_refused(record(self.project("integration")), "the make database has no `lint-integration`")

    def test_e2_a_project_json_it_cannot_read(self) -> None:
        project = self.project("model-typescript-web")
        (project / "project.json").write_text("{", encoding="utf-8")
        self.assert_refused(record(project), "project.json")


class EventsTest(RecordCase):
    """An event edge needs the model, at the base and in the working tree, and two services that can carry it."""

    MODEL = ("slices:\n  - id: Bill\n    service: {producer}\n    frames:\n      - {{type: evt, name: Billed}}\n"
             "  - id: Ship\n    service: {reader}\n    reads: [Billed]\n")

    def project(self, name: str = "") -> Path:
        if "events" not in self.projects:
            made = self.generate(self.parent, "ledger", "event-modelling", "python", "none", http="fastapi",
                                 event_store="sqlite")
            subprocess.run([str(ROOT / "slipwai"), "add-service", "billing", "--language", "python"], cwd=made,
                           check=True, capture_output=True, timeout=120)
            commit_all(made, "billing")
            self.projects["events"] = made
        copy = Path(tempfile.mkdtemp(prefix="copy-", dir=self.parent)) / "project"
        shutil.copytree(self.projects["events"], copy, symlinks=True)
        return copy

    def test_e1_an_event_edge_is_a_contract_with_its_consumers(self) -> None:
        project = self.project()
        (project / EVENT_MODEL).write_text(self.MODEL.format(producer="billing", reader="service"), encoding="utf-8")
        (contract,) = [item for item in loaded(project)["contracts"] if item["kind"] == "event"]
        self.assertEqual(contract, {"id": "event:Billed", "kind": "event", "event": "Billed", "owner": "billing",
                                    "paths": ["apps/billing/"], "consumers": ["service"]})

    def test_e2_a_model_it_cannot_read_where_an_event_edge_is_needed(self) -> None:
        project = self.project()
        (project / EVENT_MODEL).write_text("slices: [unclosed\n", encoding="utf-8")
        done = record(project)
        self.assertEqual((done.stdout, done.returncode, len(done.stderr.splitlines())), ("", 1, 1), done.stderr)
        self.assertIn("the model cannot be read", done.stderr)


def reads_of(path: Path, project: Path) -> set[str]:
    """Every string literal of a Python file that names something at the project's root: it reads as a path, and its
    first segment is an entry of the project's own directory (so `origin/main` and `slices/README.md` are not one)."""
    found = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and PATH_LIKE.match(node.value):
            literal = node.value.removeprefix("./")
            first = literal.split("/")[0]
            if first and first not in ROOT_OWN and (project / first).exists():
                found.add(literal)
    return found


def covered(literal: str, files: list[str]) -> bool:
    """An entry at or above the literal. A directory the script walks is covered by the directory, never by one
    entry somewhere under it: that reads less than the script does."""
    return any(entry == "./" or literal.rstrip("/") == entry.rstrip("/") or (entry.endswith("/")
               and literal.startswith(entry)) for entry in files)


def modules_of(project: Path, entry: Path) -> set[Path]:
    """The script and every file of `scripts/` it imports or names, however far: what the check reads through."""
    scripts = project / "scripts"
    seen: set[Path] = set()
    pending = [entry]
    while pending:
        path = pending.pop()
        if path in seen or not path.is_file():
            continue
        seen.add(path)
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            named: list[str] = []
            if isinstance(node, ast.Import):
                named = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                base = "." * node.level + (node.module or "")
                named = [base, *(f"{base}.{alias.name}" for alias in node.names)] if node.module else \
                    [f"{base}{alias.name}" for alias in node.names]
            elif isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value.endswith(".py"):
                named = [node.value]
            for name in named:
                pending.extend(candidates(name, path.parent, scripts))
    return seen


def candidates(name: str, here: Path, scripts: Path) -> list[Path]:
    if name.endswith(".py"):
        return [directory / name for directory in (here, scripts)]
    dots = len(name) - len(name.lstrip("."))
    parts = name.lstrip(".").split(".")
    roots = [here.parents[dots - 1] if dots > 1 else here] if dots else [here, scripts]
    found = []
    for root in roots:
        found += [root.joinpath(*parts).with_suffix(".py"), root.joinpath(*parts, "__init__.py")]
    return found


class TableHeldTest(RecordCase):
    """The file column against the scripts: a check's script, and what it imports, names no project path the check's
    recorded inputs leave out. A check with no recorded inputs is held to nothing."""

    SHAPES = tuple(SHAPE_TABLE)  # every shape the factory generates for the scoped gate, a cloud one among them

    def findings(self) -> list[str]:
        records = importlib.import_module("verify_scoped.record")  # the script's own reading of the make database

        findings = []
        fired: set[str] = set()
        for shape in self.SHAPES:
            project = self.project(shape)
            if record(project).returncode != 0:  # a shape whose record is refused (`integration`) has no table to hold
                continue
            data = loaded(project)
            was = os.getcwd()
            os.chdir(project)
            try:
                recipes = records.database("make", "Makefile").recipes
            finally:
                os.chdir(was)
            for name, check in data["checks"].items():
                if check["inputs"] is None or name.split("-")[0] in GATES:
                    continue
                entries = [found for line in recipes.get(name, []) for found in re.findall(SCRIPT, line)]
                reads: set[str] = set()
                for entry in entries:
                    for module in modules_of(project, project / entry):
                        reads |= reads_of(module, project)
                files = check["inputs"]["files"]
                findings += [f"{shape}: {name} reads {read}, under none of {files}" for read in sorted(reads)
                             if not covered(read, files) and read not in NOT_AN_INPUT]
                fired.update(read for read in reads if not covered(read, files))
        stale = sorted(set(NOT_AN_INPUT) - fired)
        findings += [f"{read} is explained, and no check reads it any more" for read in stale]
        return findings

    def test_e4_every_path_a_check_script_reads_lies_under_one_of_its_recorded_inputs(self) -> None:
        self.assertEqual(self.findings(), [])
