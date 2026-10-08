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
from slipwai.project.mutation import mutation_notes
from slipwai.services import App

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
    "standard-python": "7bf0566e0936365cf1a1d316a95860f292f26a246ba813cfae6c86e9070f032e",
    "model-typescript-web": "ca06fb369e785a134705fcd8850a5dd5cbb28686b08650647fb7d40ea5da74b1",
    "model-typescript-web-cloud": "0eec6cfa921951453690d97633299cc67fd80ccc78b94ec66a50095af81c171f",
    "model-python-sqlite": "18d0ea697a9dc13ff77b664908d6d3cbc034034a57d0a512489b05ffe7b9522e",
    "model-go-azure": "49c93cf01e241187020cc2bdfcdc377032c1b4b3926979308baf4df3719e29fe",
    "standard-quarkus": "74efc08991dfe6e26f8a1d08c92058adb4874763026935514074f51059ff3491",
    "standard-spring-web": "f08f581ddf2ee0fdfb8ed5ae2fe7c3446a009b182f0740604f55ab780a0e0c6e",
    "two-python": "908424d5321b705609d09dc13864b792b100e2df893c42675bda21aaae6a79b1",
    "go-web": "3fa01ecf6acac061b0cfe50f1e09d18aa0679c616c8abd90c140a443b127d643",
    "java-go": "917cf20ca83c1a8230030d0406a0d611137fad7225945df7e2d1b260b33c5c53",
    "java-python-web": "755789dbfd2144bd0e9243344099bc430cb97683b31abb96ce1ee6a36a60df4e",
    "two-go": "9c1b692182bce8e0af9e571a44c4b2e0b528efaa399c61933db9b4da81f94b3b",
    "integration": "250a60dab88765bc71a06e25c411d76f3e22f01b2afa8b8048d8903e02f2bb45",
    "integration-billing": "2701a30c39286b3020d4098b6030d45b0f0a1c663ba0f7d22216c9f2aee31736",
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

    def test_t029_every_backends_note_is_its_own_block_and_stays_within_120_columns_for_two_services(self) -> None:
        def services(*backends: str) -> list[App]:
            return [App(name, f"apps/{name}", "service", backend.partition("-")[0],
                        {"spring": "spring-boot", "quarkus": "quarkus"}.get(backend.partition("-")[2]), 3000)
                    for backend in backends for name in ("service", "billing")]

        backends = ("go", "java-spring", "java-quarkus", "typescript", "python")
        for backend in backends:
            with self.subTest(backend=backend):
                note = mutation_notes(services(backend))
                self.assertEqual([line for line in note.splitlines() if len(line) > 120], [])
        together = mutation_notes(services(*backends)).splitlines()
        self.assertEqual([line for line in together if len(line) > 120], [])
        starts = [i for i, line in enumerate(together) if line.startswith(("# Wired up", "# Not wired"))]
        self.assertEqual(len(starts), len(backends))
        for start in starts[1:]:
            self.assertEqual(together[start - 1], "#", "each note is its own block, one comment line from the last")
            self.assertNotEqual(together[start - 2], "#")
        for name in ("two-python", "java-python-web"):  # the generated Makefile carries the same text
            with self.subTest(project=name):
                above = (self.project(name) / "Makefile").read_text(encoding="utf-8").split("\nmutation:")[0]
                comments = [line for line in above.splitlines()[::-1] if line.startswith("#")]
                self.assertTrue(comments)
                self.assertEqual([line for line in comments if len(line) > 120], [])

if __name__ == "__main__":
    unittest.main()
