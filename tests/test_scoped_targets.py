"""R3 (AC-S06-2, -4, -14): a component is a deployable with targets of its own.

The generated `Makefile` gains, after everything it had, `lint-<name>`, `typecheck-<name>` and `test-<name>` for every
service and browser app, built from that deployable's own recipe lines; a line naming no deployable's path is a family
target `<check>_<family>` the family's units name as a prerequisite. The make database is read with
`make -npq -f Makefile .DEFAULT` (exit 2, nothing run). Projects are generated once per class, in every shape the
verify stamp's scan and the matrix cover plus the two-service and name-collision ones.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from stamp_fixture import CI_MARKERS, GIT_STATE, MAKE_STATE
from support import FactoryTestCase, commit_all
from test_parallel_gate_families import reaches
from test_parallel_gate_reads import OWN_CODE, READS_NOTHING
from test_verify_stamp_scan import SHAPES as SCAN_SHAPES
from test_verify_stamp_scan import makefile_rules

from slipwai.assets import ROOT

sys.dont_write_bytecode = True

CHECKS = ("lint", "typecheck", "test")
SECTION = "\n# Scoped gate"  # where the new section begins in a generated Makefile
# name -> (profile, backend, frontend, axes, services added by `add-service <name> --language <language>`)
Shape = tuple[str, str, str, dict[str, str], tuple[tuple[str, str], ...]]
SHAPES: dict[str, Shape] = {shape[0]: (*shape[1:4], shape[4], ()) for shape in SCAN_SHAPES}
SHAPES["two-python"] = ("standard", "python", "none", {"http": "none"}, (("billing", "python"),))
SHAPES["go-web"] = ("standard", "go", "react-vite", {"http": "none"}, ())
SHAPES["java-go"] = ("standard", "java-quarkus", "none", {"http": "none"}, (("second", "go"),))
SHAPES["java-python-web"] = ("standard", "java-quarkus", "react-vite", {"http": "none"}, (("second", "python"),))
SHAPES["two-go"] = ("standard", "go", "none", {"http": "none"}, (("second", "go"),))
SHAPES["integration"] = ("standard", "python", "none", {"http": "none"}, (("integration", "python"),))
SHAPES["integration-billing"] = (
    "standard", "python", "none", {"http": "none"}, (("billing", "python"), ("integration-billing", "python")),
)
# sha256 of each shape's Makefile before this slice's section, from the commit that came before it (R3 e5). A gate
# that changes on purpose regenerates these; this slice adds text after everything and moves nothing before it.
PRE_SLICE: dict[str, str] = {
    "standard-python": "e0f55e165135548b364d5e4ec116c25a36b519ac4efba9acd874d25df849b5af",
    "model-typescript-web": "c99e5d3a271431f461346b9fce46b4c5949b3eb409b3f087f845898e1ce930c3",
    "model-typescript-web-cloud": "7702568c040e1c40c2d5b6b3251501ae35ddce81808f2511ba182ca5ec9f0691",
    "model-python-sqlite": "5339b0746b90b0fbe6f4e548ff686bd80c3f7fe05c1c397ddb6f23e4629ab9e9",
    "model-go-azure": "9f9e907561bd7983722157d8c2361af4ba8a6d2653f478b213a5277fea7eddd9",
    "standard-quarkus": "74efc08991dfe6e26f8a1d08c92058adb4874763026935514074f51059ff3491",
    "standard-spring-web": "a8a880dca931f39ad02d5e07ff4611b5cf793d272da8ab2007069adfbcb5d01a",
    "two-python": "891f03f6cd52134e02978dcbf02270a38bd598db500898cbcce833f6528cf80d",
    "go-web": "5cba1d7a2e3c050e9d37c8dd8f1276613f08e28635dd4a2d41c6ca50888458ef",
    "java-go": "e1db44ee0c6305f24b11f331de2acc99f442c2908233a300cc5f77a5f8bdfb0f",
    "java-python-web": "8553c378a95f5d6e8dd1c94ad9f1526550218ff36a07a88c38a712dd69320ab7",
    "two-go": "939186aed2f2577a2ff5ce201c95ae449874cbe1a351df43e92e96823ade6167",
    "integration": "57f25e77524ad4ae759e7e51cce6cfa3db6a71e46bc8457d7d9d0512ac2b514f",
    "integration-billing": "f1fa7aa3244e6efb6531340bfcb5ec875d42595777c2739e5ac21f3bf416e01b",
}


def build(parent: Path, name: str, case: FactoryTestCase) -> Path:
    profile, backend, frontend, axes, added = SHAPES[name]
    # A project name of its own: the cloud targets refuse their own brand as a word of one.
    project = case.generate(parent, f"shape{list(SHAPES).index(name)}", profile, backend, frontend, **axes)
    for service, language in added:
        dirty = subprocess.run(["git", "status", "--porcelain"], cwd=project, text=True, capture_output=True,
                               timeout=60)
        if dirty.stdout.strip():  # `add-service` refuses a tree with uncommitted work, so the one before is committed
            commit_all(project, "before " + service)
        subprocess.run([str(ROOT / "slipwai"), "add-service", service, "--language", language], cwd=project,
                       check=True, capture_output=True, timeout=120)
    return project


def database(project: Path) -> dict[str, tuple[list[str], list[str]]]:
    """Each target's prerequisites (order-only ones included) and recipe lines, from make's database."""
    env = {k: v for k, v in __import__("os").environ.items() if k not in CI_MARKERS + MAKE_STATE + GIT_STATE}
    done = subprocess.run(["make", "-npq", "-f", "Makefile", ".DEFAULT"], cwd=project, env=env, text=True,
                          capture_output=True, timeout=60)
    assert done.returncode == 2 and "No rule to make target" in done.stderr, done.stderr
    rules: dict[str, tuple[list[str], list[str]]] = {}
    current: str | None = None
    for line in done.stdout.splitlines():
        if line.startswith("\t"):
            if current is not None:
                rules[current][1].append(line[1:])
            continue
        if line.startswith("#"):  # the database's own notes, among them the one that heads each recipe
            continue
        found = re.match(r"^([^\s#=:][^:=]*):(?!=)\s*(.*)$", line)
        current = None
        if found and ":=" not in line and "=" not in found.group(1):
            current = found.group(1)
            needs = rules.setdefault(current, ([], []))[0]
            needs.extend(word for word in found.group(2).replace("|", " ").split() if word not in needs)
    return rules


class ScopedTargetsTest(FactoryTestCase):
    longMessage = False  # a failure names the target, never the make database

    parent: Path
    projects: dict[str, Path]
    databases: dict[str, dict[str, tuple[list[str], list[str]]]]

    @classmethod
    def setUpClass(cls) -> None:
        cls.parent = Path(tempfile.mkdtemp(prefix="scoped-targets-"))
        cls.addClassCleanup(shutil.rmtree, cls.parent, ignore_errors=True)
        cls.projects = {}
        cls.databases = {}

    def project(self, name: str) -> Path:
        if name not in self.projects:
            self.projects[name] = build(self.parent, name, self)
            self.databases[name] = database(self.projects[name])
        return self.projects[name]

    def rules(self, name: str) -> dict[str, tuple[list[str], list[str]]]:
        self.project(name)
        return self.databases[name]

    def test_e1_a_typescript_service_and_web_app_have_six_units_and_no_family_target(self) -> None:
        rules = self.rules("model-typescript-web")
        for check in CHECKS:
            for name in ("service", "web"):
                unit = f"{check}-{name}"
                self.assertTrue(unit in rules, f"no target {unit}")
                words = "test" if check == "test" else f"run {check}"
                self.assertEqual(rules[unit][1], [f"npm --workspace apps/{name} {words}"])
            self.assertEqual([t for t in rules if t.startswith(f"{check}_")], [], "a family target with no shared line")
            merged = rules[check][1]
            self.assertEqual([rules[f"{check}-{n}"][1][0] for n in ("service", "web")], merged)

    def test_e2_two_python_services_share_one_family_line(self) -> None:
        rules = self.rules("two-python")
        self.assertEqual(rules["lint_python"][1], ["./scripts/verify --lint-only --synced"])
        for unit in ("lint-service", "lint-billing"):
            self.assertTrue("lint_python" in rules[unit][0], unit)
            self.assertEqual(rules[unit][1], [], f"{unit} has a recipe of its own")
            self.assertTrue({"sync", "check-python"} <= set(rules[unit][0]), rules[unit][0])
        self.assertIn("sync", rules["lint_python"][0])

    def makefile_text(self, name: str) -> str:
        return (self.project(name) / "Makefile").read_text(encoding="utf-8")

    def ordering_of(self, name: str) -> list[str]:
        """The lines the section holds under `VERIFY_ORDER`, between its conditional and the `endif`."""
        section = self.makefile_text(name).split(SECTION)[-1]
        self.assertIn("ifeq ($(origin VERIFY_ORDER),command line)", section)
        return section.split("ifeq ($(origin VERIFY_ORDER),command line)\n")[1].split("endif")[0].splitlines()

    def test_e3_go_and_java_units_and_their_order(self) -> None:
        go = self.rules("model-go-azure")
        self.assertEqual(go["lint_go"][1], [line for line in go["lint"][1] if "gofmt" in line])
        self.assertEqual(len(go["test_go"][1]), 1)
        self.assertIn("covdata", go["test_go"][1][0])
        self.assertTrue("lint_go" in go["lint-service"][0] and "test_go" in go["test-service"][0])
        # VERIFY_ORDER, as `gate_order` has it: Go's typecheck and test wait for its lint; Java's three run in a chain.
        self.assertEqual(self.ordering_of("model-go-azure"), ["typecheck-service test-service: lint-service"])
        self.assertEqual(self.ordering_of("standard-quarkus"),
                         ["typecheck-service: lint-service", "test-service: typecheck-service"])
        self.rules("standard-spring-web")
        self.assertEqual(self.ordering_of("standard-spring-web"),
                         ["typecheck-service: lint-service", "test-service: typecheck-service"])
        npm = self.rules("model-typescript-web")
        for unit in ("lint-service", "typecheck-web", "test-web"):
            self.assertTrue("build-packages" in npm[unit][0] and "check-python" in npm[unit][0], unit)

    def test_e4_the_units_and_families_of_every_shape_are_the_gates_recipe_lines(self) -> None:
        for name in SHAPES:
            with self.subTest(shape=name):
                rules = self.rules(name)
                for check in CHECKS:
                    gate = rules[check][1]
                    owners = sorted(t for t in rules if t.startswith((f"{check}-", f"{check}_")) and t not in (
                        "test-integration", "test_integration") and not t.startswith("test-integration-"))
                    lines = [line for t in owners for line in rules[t][1]]
                    self.assertEqual(sorted(lines), sorted(gate), (name, check, owners))
                    for target in owners:  # each target's own lines keep the gate's order
                        positions = [gate.index(line) for line in rules[target][1]]
                        self.assertEqual(positions, sorted(positions), (name, target))

    def test_e5_hold_the_text_before_the_section_is_what_the_gate_was(self) -> None:
        """HOLD (teeth: change one byte of `verify-checks`' line and a pin fails): nothing before the suffix moves."""
        for name in SHAPES:
            with self.subTest(shape=name):
                text = (self.project(name) / "Makefile").read_text(encoding="utf-8")
                before = text.split(SECTION)[0]
                self.assertEqual(hashlib.sha256(before.encode("utf-8")).hexdigest(), PRE_SLICE[name])
                for rule in ("verify:", "verify-checks:", "ci:"):
                    self.assertIn(f"\n{rule}", before)

    def test_e6_hold_a_deployable_named_integration_gets_no_units(self) -> None:
        """HOLD (teeth: emit `test-integration`, and a unit is found): the existing recipes are untouched."""
        for name in ("integration", "integration-billing"):
            with self.subTest(shape=name):
                rules = self.rules(name)
                deployable = "integration" if name == "integration" else "integration-billing"
                self.assertTrue("lint-service" in rules, "the other deployables still have units")
                for check in ("lint", "typecheck"):
                    self.assertNotIn(f"{check}-{deployable}", rules)
                # `test-integration` and `test-integration-<service>` are the existing targets, and stay what they were.
                self.assertEqual(rules["test-integration"][1], [])
                self.assertFalse({"check-python", "sync"} & set(rules["test-integration"][0]))
                if name == "integration-billing":
                    self.assertTrue("test-billing" in rules, "the real service `billing` has its own")
                    self.assertEqual(rules["test-integration-billing"][0], ["sync"])
                done = subprocess.run(["make", "-n", "-f", "Makefile", "test-integration"], cwd=self.project(name),
                                      text=True, capture_output=True, timeout=60)
                self.assertNotIn("overriding recipe", done.stderr)

    def test_e7_every_unit_and_family_target_is_classified_and_none_is_in_help(self) -> None:
        for name in SHAPES:
            with self.subTest(shape=name):
                project = self.project(name)
                text = (project / "Makefile").read_text(encoding="utf-8")
                rules = makefile_rules(re.sub(r"^# backing-service:.*\n", "", text, flags=re.M))
                self.assertIn(SECTION, (project / "Makefile").read_text(encoding="utf-8"), "no scoped section")
                section = (project / "Makefile").read_text(encoding="utf-8").split(SECTION)[1]
                targets = sorted({t for t in re.findall(r"^((?:lint|typecheck|test)[-_][a-z0-9_-]+):", section, re.M)})
                self.assertTrue(targets, name)
                for target in targets:
                    recipe = " ".join(rules[target][1])
                    if OWN_CODE.search(recipe):
                        self.assertIn("build-packages", reaches(rules, target), target)
                    else:
                        self.assertIn(re.split(r"[-_]", target)[0], READS_NOTHING, target)
                helped = subprocess.run(["make", "help"], cwd=project, text=True, capture_output=True,
                                        timeout=60).stdout
                for target in targets:
                    self.assertNotRegex(helped, rf"^\s+{re.escape(target)}\s", target)


if __name__ == "__main__":
    unittest.main()
