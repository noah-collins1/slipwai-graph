"""T043 (G1 · AC-S06-2, -3, -5; D148): a deployable that reads outside its own path is the full gate.

A compiler, a type checker or a package manager reaches another deployable's files in three ways: a path, another
deployable's package or module identity, a link. `reach.py` reads those three over every file git lists under each
deployable, and any reach is the full gate with words that name the file; where it cannot tell, the full gate runs
too. The factory's own shapes reach nothing and keep every saving.
"""
from __future__ import annotations

import atexit
import importlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import scoped_fixture
from scoped_fixture import FULL, ShapeCase, shape_template
from stamp_fixture import git
from support import commit_all
from test_verify_scoped_record import RecordCase

from slipwai.assets import ROOT

sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "assets" / "toolkit" / "scripts"))

ENDING = ("and the scoped gate scopes only a deployable that reads nothing outside its own path; share code through "
          "a package under `packages/` or a published contract to scope again")
TS_TWO, JAVA_TWO = "ts-two", "java-two"
SERVICE = "apps/service"


def register(name: str, template: str, service: str, language: str) -> None:
    """A shape of its own: `template` with `add-service <service> --language <language>`, committed."""
    parent = Path(tempfile.mkdtemp(prefix="scoped-reach-"))
    atexit.register(shutil.rmtree, parent, ignore_errors=True)
    project = parent / "project"
    shutil.copytree(shape_template(template), project, symlinks=True)
    subprocess.run([str(ROOT / "slipwai"), "add-service", service, "--language", language], cwd=project, check=True,
                   capture_output=True, timeout=180)
    commit_all(project, "the second service")
    scoped_fixture._shapes[name] = project


def setUpModule() -> None:
    register(TS_TWO, "model-typescript-web", "billing", "typescript")
    register(JAVA_TWO, "standard-quarkus", "second", "java")


class TwoCase(ShapeCase):
    """Examples over two deployables: a file of the first is put on the trunk, the branch is cut from it again, and
    a file of the second changes on the branch, which is what the selection must not skip."""

    longMessage = False

    def trunk(self, files: dict[str, str], links: dict[str, str] | None = None) -> None:
        git(self.repo, "checkout", "-q", "main")
        for path, text in files.items():
            (self.repo / path).parent.mkdir(parents=True, exist_ok=True)
            (self.repo / path).write_text(text, encoding="utf-8")
        for path, target in (links or {}).items():
            os.symlink(target, self.repo / path)
        git(self.repo, "add", "-A")
        git(self.repo, "-c", "user.name=t", "-c", "user.email=t@local", "commit", "-qm", "the first reads the second")
        git(self.repo, "checkout", "-q", "-B", "slice/S1")
        self.write_baseline()

    def read(self, path: str) -> str:
        return (self.repo / path).read_text(encoding="utf-8")

    def reached(self, run: subprocess.CompletedProcess[str], cause: str) -> None:
        self.assertEqual(self.scoped_lines(run)[0], FULL + cause, run.stdout)
        self.assertEqual(len(self.verify_calls()), 1, "`make verify` was not run exactly once")
        self.assertEqual(self.lines(run), [], "a unit line was said beside the full gate")

    def path_cause(self, file: str, target: str, owner: str = SERVICE) -> str:
        return f"`{file}` reaches `{target}`, outside its deployable `{owner}`, {ENDING}"

    def name_cause(self, file: str, name: str, deployable: str, owner: str = SERVICE) -> str:
        return (f"`{file}` names `{name}`, the package of the deployable `{deployable}`, outside its deployable "
                f"`{owner}`, {ENDING}")

    def stays_scoped(self, run: subprocess.CompletedProcess[str]) -> None:
        self.assertEqual(self.verify_calls(), [], run.stdout)
        self.assertNotIn("reaches", run.stdout)
        self.assertNotIn("cannot be established", run.stdout)



class PathTest(TwoCase):
    shape = TS_TWO

    def test_e8_g1_a_relative_import_of_the_other_deployables_source_is_the_full_gate(self) -> None:
        self.trunk({f"{SERVICE}/src/uses-billing.ts": 'import { rate } from "../../billing/src/rate.js";\nrate;\n'})
        self.edit("apps/billing/src/rate.ts", "export const rate = 'a string';\n")
        self.reached(self.scoped(), self.path_cause(f"{SERVICE}/src/uses-billing.ts", "apps/billing/src/rate.js"))

    def test_e8_a_backslash_path_is_a_reach_too(self) -> None:
        self.trunk({f"{SERVICE}/src/win.ts": 'const p = "..\\\\..\\\\billing\\\\src";\n'})
        self.edit("apps/billing/src/rate.ts", "x\n")
        self.reached(self.scoped(), self.path_cause(f"{SERVICE}/src/win.ts", "apps/billing/src"))

    def test_e8_a_tsconfig_that_extends_a_root_file_is_the_full_gate(self) -> None:
        self.trunk({f"{SERVICE}/tsconfig.extra.json": '{ "extends": "../../tsconfig.base.json" }\n'})
        self.edit("apps/billing/src/rate.ts", "x\n")
        self.reached(self.scoped(), self.path_cause(f"{SERVICE}/tsconfig.extra.json", "tsconfig.base.json"))

    def test_e8_a_config_is_read_against_the_deployables_root_as_well_as_its_own_directory(self) -> None:
        self.trunk({f"{SERVICE}/sub/tsconfig.json": '{ "extends": "../shared.json" }\n'})
        self.edit("apps/billing/src/rate.ts", "x\n")
        self.reached(self.scoped(), self.path_cause(f"{SERVICE}/sub/tsconfig.json", "apps/shared.json"))

    def test_e8_a_path_that_names_the_other_deployable_from_the_root_is_the_full_gate(self) -> None:
        self.trunk({f"{SERVICE}/scripts.json": '{ "read": "apps/billing/src" }\n'})
        self.edit("apps/billing/src/rate.ts", "x\n")
        self.reached(self.scoped(), self.path_cause(f"{SERVICE}/scripts.json", "apps/billing"))

    def test_e8_a_symlink_that_leaves_the_deployable_is_the_full_gate(self) -> None:
        self.trunk({}, {f"{SERVICE}/src/billing-src": "../../billing/src"})
        self.edit("apps/billing/src/rate.ts", "x\n")
        self.reached(self.scoped(), self.path_cause(f"{SERVICE}/src/billing-src", "apps/billing/src"))

    def test_e8_an_ignored_symlink_that_leaves_the_deployable_is_the_full_gate(self) -> None:
        """T051 (A3): the link is read whether or not git ignores it; a change through it must not be skipped."""
        self.trunk({".gitignore": f"{SERVICE}/src/svc\n"}, {f"{SERVICE}/src/svc": "../../billing/src"})
        self.assertEqual(git(self.repo, "check-ignore", f"{SERVICE}/src/svc").strip(), f"{SERVICE}/src/svc")
        self.edit("apps/billing/src/rate.ts", "x\n")
        self.reached(self.scoped(), self.path_cause(f"{SERVICE}/src/svc", "apps/billing/src"))

    def test_e8_an_ignored_symlink_inside_the_deployable_or_out_of_the_repository_is_no_reach(self) -> None:
        self.trunk({".gitignore": f"{SERVICE}/src/own\n{SERVICE}/src/away\n"},
                   {f"{SERVICE}/src/own": "main.ts", f"{SERVICE}/src/away": "/usr"})
        self.edit("apps/billing/src/rate.ts", "x\n")
        self.stays_scoped(self.scoped())

    def test_e8_an_untracked_file_is_scanned_as_a_tracked_one_is(self) -> None:
        self.write_baseline()
        self.edit(f"{SERVICE}/src/new.ts", 'import "../../billing/src/rate.js";\n')
        self.reached(self.scoped(), self.path_cause(f"{SERVICE}/src/new.ts", "apps/billing/src/rate.js"))

    def test_e8_a_path_above_the_repository_root_cannot_be_established(self) -> None:
        self.trunk({f"{SERVICE}/src/up.ts": 'import "../../../../../elsewhere.js";\n'})
        self.edit("apps/billing/src/rate.ts", "x\n")
        run = self.scoped()
        self.assertEqual(self.scoped_lines(run)[0], FULL + f"what `{SERVICE}` reads outside its path cannot be "
                         f"established: `{SERVICE}/src/up.ts` climbs above the repository root", run.stdout)

    def test_e8_a_file_that_cannot_be_opened_cannot_be_established(self) -> None:
        self.trunk({f"{SERVICE}/src/sealed.ts": "x\n"})
        (self.repo / f"{SERVICE}/src/sealed.ts").chmod(0)
        self.addCleanup((self.repo / f"{SERVICE}/src/sealed.ts").chmod, 0o644)
        if os.access(self.repo / f"{SERVICE}/src/sealed.ts", os.R_OK):
            return  # a user who reads a file of mode 0 (root) has no unreadable file to make here
        self.edit("apps/billing/src/rate.ts", "x\n")
        run = self.scoped()
        self.assertTrue(self.scoped_lines(run)[0].startswith(
            FULL + f"what `{SERVICE}` reads outside its path cannot be established: "), run.stdout)

    def test_e8_the_deployables_own_row_files_and_a_package_it_consumes_are_not_a_reach(self) -> None:
        self.trunk({f"{SERVICE}/own.json": '{ "a": "../../package.json", "b": "../../packages/api-client/x" }\n'})
        self.edit(f"{SERVICE}/src/main.ts", "\n// an edit\n")
        self.stays_scoped(self.scoped())

    def test_e8_two_deployables_that_read_nothing_of_each_other_keep_every_saving(self) -> None:
        self.edit("apps/billing/src/main.ts", "\n// an edit\n")
        run = self.scoped()
        self.stays_scoped(run)
        self.assertIn("skip typecheck-service", run.stdout)


class IdentityTest(TwoCase):
    shape = TS_TWO

    def billing(self) -> str:
        return str(json.loads(self.read("apps/billing/package.json"))["name"])

    def test_e8_a_bare_workspace_import_with_no_dependency_declared_is_the_full_gate(self) -> None:
        name = self.billing()
        self.trunk({f"{SERVICE}/src/bare.ts": f'import {{ rate }} from "{name}";\nrate;\n'})
        self.edit("apps/billing/src/rate.ts", "x\n")
        self.reached(self.scoped(), self.name_cause(f"{SERVICE}/src/bare.ts", name, "billing"))

    def test_e8_a_rename_on_the_branch_still_finds_the_old_name_in_the_other_deployables_source(self) -> None:
        name = self.billing()
        self.trunk({f"{SERVICE}/src/bare.ts": f'import {{ rate }} from "{name}";\nrate;\n'})
        path = self.repo / "apps/billing/package.json"
        path.write_text(path.read_text(encoding="utf-8").replace(f'"{name}"', '"renamed-billing"', 1), encoding="utf-8")
        self.reached(self.scoped(), self.name_cause(f"{SERVICE}/src/bare.ts", name, "billing"))

    def test_e8_a_longer_word_that_holds_the_name_is_not_the_name(self) -> None:
        name = self.billing()
        self.trunk({f"{SERVICE}/src/other.ts": f'const a = "{name}-extra"; const b = "x{name}";\n'})
        self.edit("apps/billing/src/rate.ts", "x\n")
        self.stays_scoped(self.scoped())


class GoTest(TwoCase):
    shape = "two-go"

    def test_e8_a_go_import_of_the_other_modules_path_under_go_work_is_the_full_gate(self) -> None:
        module = re.search(r"^module (\S+)", self.read("apps/second/go.mod"), re.M)
        assert module is not None
        self.trunk({"apps/service/uses.go": f'package main\n\nimport _ "{module.group(1)}/pkg"\n'})
        self.edit("apps/second/pkg/x.go", "package pkg\n")
        self.reached(self.scoped(), self.name_cause("apps/service/uses.go", module.group(1), "second"))


class PythonTest(TwoCase):
    shape = "two-python"

    def name(self) -> str:
        found = re.search(r'^name = "([^"]+)"', self.read("apps/billing/pyproject.toml"), re.M)
        assert found is not None
        return found.group(1)

    def test_e8_a_uv_path_dependency_is_the_full_gate(self) -> None:
        self.trunk({"apps/service/pyproject.toml": self.read("apps/service/pyproject.toml")
                    + '\n[tool.uv.sources]\nbilling = { path = "../billing" }\n'})
        self.edit("apps/billing/src/x.py", "x = 1\n")
        self.reached(self.scoped(), self.path_cause("apps/service/pyproject.toml", "apps/billing"))

    def test_e8_a_uv_workspace_dependency_by_name_is_the_full_gate_however_the_name_is_spelled(self) -> None:
        name = self.name()
        spelled = name.replace("-", "_").upper()
        self.trunk({"apps/service/pyproject.toml": self.read("apps/service/pyproject.toml")
                    + f"\n[tool.uv.sources]\n{spelled} = {{ workspace = true }}\n"})
        self.edit("apps/billing/src/x.py", "x = 1\n")
        self.reached(self.scoped(), self.name_cause("apps/service/pyproject.toml", spelled, "billing"))


class JavaTest(TwoCase):
    shape = JAVA_TWO

    def test_e8_a_maven_dependency_on_the_other_deployables_artifact_id_is_the_full_gate(self) -> None:
        found = re.search(r"<artifactId>([^<$]+-second)</artifactId>", self.read("apps/second/pom.xml"))
        assert found is not None
        pom = self.read("apps/service/pom.xml")
        added = pom.replace("<dependencies>", f"<dependencies>\n    <dependency><artifactId>{found.group(1)}"
                            "</artifactId></dependency>", 1)
        self.trunk({"apps/service/pom.xml": added})
        self.edit("apps/second/src/main/java/X.java", "class X {}\n")
        self.reached(self.scoped(), self.name_cause("apps/service/pom.xml", found.group(1), "second"))


class FactoryShapesTest(RecordCase):
    """The hold, as in D140 point 4: every shape the factory makes, and a service with a second service, reads nothing
    outside its own deployable, so the saving stays."""

    def test_e8_hold_no_shape_has_a_reach(self) -> None:
        from test_scoped_targets import SHAPES  # noqa: PLC0415

        record, reach = (importlib.import_module(f"verify_scoped.{name}") for name in ("record", "reach"))
        shapes: dict[str, Path] = {name: self.project(name) for name in SHAPES}
        shapes[TS_TWO], shapes[JAVA_TWO] = (scoped_fixture._shapes[name] for name in (TS_TWO, JAVA_TWO))
        for name, project in shapes.items():
            with self.subTest(shape=name):
                packages = sorted(path.parent.name for path in (project / "packages").glob("*/package.json"))
                found = reach.find(project, record.deployables_of(project), packages, "HEAD")
                self.assertIsNone(found)

    def test_e8_the_reader_finds_a_reach_in_a_tree_with_one_deployable(self) -> None:
        """It runs whatever the number of deployables: a lone service whose test reads the model has the same hole."""
        record, reach = (importlib.import_module(f"verify_scoped.{name}") for name in ("record", "reach"))
        project = self.project("model-typescript-web")
        reads = 'import "../../../docs/event-model/model.yaml";\n'
        (project / "apps/service/src/m.ts").write_text(reads, encoding="utf-8")
        self.addCleanup((project / "apps/service/src/m.ts").unlink)
        found = reach.find(project, record.deployables_of(project), [], None)
        self.assertEqual(found, f"`{SERVICE}/src/m.ts` reaches `docs/event-model/model.yaml`, outside its deployable "
                                f"`{SERVICE}`, {ENDING}")


