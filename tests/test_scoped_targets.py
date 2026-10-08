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
    "standard-python": "075e4cf86fe457bec23136cd4ad98eb1afb6f6816b159fbf759df1f38ce59bab",
    "model-typescript-web": "984e9a38b969f4362834e5288e14ea7b6fb352e9980531fbd799c7071aa4661d",
    "model-typescript-web-cloud": "ac36b4ebcdf92e5cfc0b452e89f4abe9297c61d3a5f10aef031c4fd64bdcb00c",
    "model-python-sqlite": "d5bbe35548f548034281963a541f878775f5dfb7f03a2d764b2529041a20cd9a",
    "model-go-azure": "4e1460b376ec99d6df9dbb610d9e9cbf36303cd96f146c9108dd926a92b8e71f",
    "standard-quarkus": "74efc08991dfe6e26f8a1d08c92058adb4874763026935514074f51059ff3491",
    "standard-spring-web": "f08f581ddf2ee0fdfb8ed5ae2fe7c3446a009b182f0740604f55ab780a0e0c6e",
    "two-python": "d8a52b16ad8ec70ac6d94641b0a61730f2372fb325a8a263ae57f324c549e231",
    "go-web": "247491616ca93133108871785fd8863c27c2ca410058b2fa415c8749b7afe52a",
    "java-go": "1e4574d4f9cb761120d338e0b17c3f227b475f6f2c2b8aa134e852ab823773b5",
    "java-python-web": "abbe32f027235ce81d6e9114048b35b49faa0ae0be0b7ac8d7cc883a73c77fca",
    "two-go": "6fbf55df732ad2b631de9f105cd7d9a713123dfece1681f6d335b86d7271dcd7",
    "integration": "f0aea1276b2a5aa5fc2d21b743bb07903735d36fcdca5d3010d77335d4ede4a9",
    "integration-billing": "5a5f4a72c21c4e81b1ff9aa2fcab602b43f4e52fa365a9de931dc7e421276c80",
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
