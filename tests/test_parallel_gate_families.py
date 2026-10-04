"""R5 (AC-S04-15, -17, -42, -43): every backend family holds the rule that a parallel gate is the serial gate's verdict.

Java's three Maven checks write one service's `target/`, and Go's first `go` command resolves the workspace and writes
`go.work.sum` on a fresh clone, so under `-j` the gate orders them: with a Java service `typecheck` waits for `lint` and
`test` for `typecheck`; with a Go service `lint` and `test` wait for `typecheck`; both families take the Java chain.
The order is the gate's own (`VERIFY_ORDER`, which only its sub-make is given), so a target typed alone starts
nothing it did not. The native tools are stand-ins that log each call and, between its `start` and its `end`, wait
for another native call to be in flight; evidence is that log, never a clock. A hold is named so, with its teeth in
its docstring.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys

from parallel_gate import (
    ParallelGateTestCase,
    barrier_events,
    native_calls,
    native_overlapped,
    shape,
    write_native,
    write_stand_ins,
)
from stamp_fixture import PYVENV_CFG
from test_verify_stamp_scan import gate_targets, makefile_rules

sys.dont_write_bytecode = True

JAVA_SHAPES = ("quarkus", "spring", "java-py", "java-go")
GO_SHAPES = ("go", "go-web", "java-go")
INSTALLERS = ("go mod download", "npm ci", "dependency:", "go get", "install")
# What each check runs in each family, as the Makefile spells it: a target typed alone starts only its own.
JAVA = {"lint": "checkstyle", "typecheck": "test-compile", "test": "-q test"}
GO = {"lint": "go vet", "typecheck": "-run '^$$'", "test": "coverprofile"}
MARKER = "node_modules/.package-lock.json"


def kind_of(arguments: str) -> str:
    """Which gate check a `./mvnw` call belongs to, read from its goals."""
    return next((kind for kind, word in JAVA.items() if word in arguments), "test")


class FamiliesTestCase(ParallelGateTestCase):
    """A project of the named shape, its native tools stand-ins, run serially and under `-j`."""

    def use(self, name: str) -> None:
        """Replace the project with a fresh copy of shape `name`, `./mvnw`, `go` and `gofmt` written as stand-ins."""
        shutil.rmtree(self.repo)
        shutil.copytree(shape(name), self.repo, symlinks=True)
        for wrapper in self.repo.glob("apps/*/mvnw"):
            write_native(wrapper, "mvnw")
        if "go" in name:
            write_native(self.bin / "go", "go")
            write_native(self.bin / "gofmt", "gofmt")
        write_stand_ins(self.bin)
        (self.bin / "npm").write_text("#!/bin/sh\nmkdir -p node_modules\n", encoding="utf-8")  # the marker's `touch`
        for manifest in sorted(self.repo.glob("apps/*/pyproject.toml")):
            (manifest.parent / ".venv").mkdir(exist_ok=True)
            (manifest.parent / ".venv" / "pyvenv.cfg").write_text(PYVENV_CFG, encoding="utf-8")

    def gate(self, *flags: str) -> subprocess.CompletedProcess[str]:
        """`make [flags] verify`, run whatever the stamp says, with a fresh log."""
        self.forget_log()
        return self.make(*flags, "verify", env={"VERIFY_FORCE": "1"})

    def started(self) -> list[str]:
        """Every native call that started, as `<tool> <arguments>`, in the order they did."""
        return [arguments for event, arguments in native_calls(self.log) if event == "start"]

    def assert_same_verdict(self, name: str) -> None:
        """The parallel run passes as the serial one did, and starts the commands it started."""
        serial = self.gate()
        self.assert_passed(serial)
        serial_started = self.started()
        parallel = self.gate("-j")
        self.assert_passed(parallel)
        self.assertEqual(sorted(self.started()), sorted(serial_started), name)
        self.assertEqual(parallel.stdout.splitlines()[-1], serial.stdout.splitlines()[-1])
        self.assertIn("verify: all gates passed", parallel.stdout)


class JavaChainTest(FamiliesTestCase):
    def test_maven_checks_do_not_overlap_under_j(self) -> None:
        """e1: no two Maven runs overlap, they run lint, typecheck, test, and the verdict is the serial run's."""
        for name in JAVA_SHAPES:
            with self.subTest(shape=name):
                self.use(name)
                self.assert_same_verdict(name)  # leaves the parallel run's log
                self.assertFalse(native_overlapped(self.log), self.log.read_text(encoding="utf-8"))
                self.assertNotIn("met", barrier_events(self.log))
                maven = [kind_of(a) for a in self.started() if a.startswith("mvnw")]
                self.assertEqual(maven, ["lint", "typecheck", "test"])

    def test_the_serial_gate_ran_the_same_chain(self) -> None:
        """The serial run's order, for the comparison above: lint, typecheck, test, one at a time."""
        self.use("quarkus")
        self.assert_passed(self.gate())
        self.assertFalse(native_overlapped(self.log))
        self.assertEqual([kind_of(a) for a in self.started() if a.startswith("mvnw")], ["lint", "typecheck", "test"])


class GoChainTest(FamiliesTestCase):
    def test_typecheck_ends_before_the_others_start_under_j(self) -> None:
        """e2: Go's first `go` command, `typecheck`'s, ends before any other native call of the gate starts."""
        for name in GO_SHAPES:
            with self.subTest(shape=name):
                self.use(name)
                self.assert_same_verdict(name)
                calls = native_calls(self.log)
                first = next(i for i, (e, a) in enumerate(calls) if e == "end" and a.startswith("go test -run"))
                if name != "java-go":  # the Java chain covers Go: its own ordering is e1's
                    self.assertEqual(sum(1 for e, a in calls[:first] if e == "start"), 1, calls[: first + 1])
                later = [a for e, a in calls[first + 1 :] if e == "start"]
                self.assertGreater(len(later), 0)
                self.assertFalse(any(a.startswith("go test -run") for a in later))

    def test_both_families_take_the_java_chain(self) -> None:
        """A project with a Java and a Go service: no two native calls overlap at all."""
        self.use("java-go")
        self.assert_passed(self.gate("-j"))
        self.assertFalse(native_overlapped(self.log), self.log.read_text(encoding="utf-8"))
        self.assertEqual([kind_of(a) for a in self.started() if a.startswith("mvnw")], ["lint", "typecheck", "test"])


class StandaloneTest(FamiliesTestCase):
    def test_a_target_typed_alone_starts_only_its_own_commands(self) -> None:
        """e3, a hold: `make test` starts no `lint` command and `make lint` no `typecheck`, in every family; read from
        `make -n`, never run. Teeth: take away `ifdef VERIFY_ORDER` so the chain applies standalone."""
        for name in ("quarkus", "spring", "go", "go-web", "java-go"):
            families = [table for table, own in ((JAVA, name != "go" and name != "go-web"), (GO, "go" in name)) if own]
            with self.subTest(shape=name):
                self.use(name)
                for target in JAVA:
                    out = subprocess.run(["make", "-n", target], cwd=self.repo, env=self.environment(), text=True,
                                         capture_output=True, timeout=180).stdout
                    for table in families:
                        for other, word in table.items():
                            self.assertEqual(word.replace("$$", "$") in out, other == target, (name, target, out))


class InstallFreeTest(FamiliesTestCase):
    def test_gate_targets_reach_npm_ci_only_through_the_file_target(self) -> None:
        """e4, a hold (AC-S04-42): of the gate's targets only the file target runs `npm ci`, and every one that runs
        npm has it as a prerequisite. Teeth: put an `npm ci` in the `lint` recipe."""
        for name in ("ts", "spring", "go-web", "java-py"):
            with self.subTest(shape=name):
                rules = makefile_rules((shape(name) / "Makefile").read_text(encoding="utf-8"))
                gate = gate_targets(rules)
                self.assertEqual([t for t in gate if any("npm ci" in line for line in rules[t][1])], [MARKER])
                for target in gate - {MARKER}:
                    if any(re.search(r"\bnpm\b", line) for line in rules[target][1]):
                        self.assertIn(MARKER, reaches(rules, target), target)

    def test_native_checks_carry_no_install_step(self) -> None:
        """e5, a hold (AC-S04-43): Go's and Java's `lint`, `typecheck` and `test` recipes install nothing. Teeth: add
        `go mod download` to a recipe."""
        for name in ("quarkus", "spring", "go", "go-web", "java-go"):
            with self.subTest(shape=name):
                rules = makefile_rules((shape(name) / "Makefile").read_text(encoding="utf-8"))
                for target in ("lint", "typecheck", "test"):
                    for line in rules[target][1]:
                        if re.search(r"\bnpm\b", line):
                            continue  # the browser app's own commands: `npm --workspace … run …`, never an install
                        self.assertFalse([w for w in INSTALLERS if w in line], (name, target, line))


def reaches(rules: dict[str, tuple[set[str], list[str]]], target: str) -> set[str]:
    """Every target `target` names as a prerequisite, directly or through another."""
    seen: set[str] = set()
    todo = [target]
    while todo:
        for needed in rules.get(todo.pop(), (set(), []))[0]:
            if needed not in seen:
                seen.add(needed)
                todo.append(needed)
    return seen

