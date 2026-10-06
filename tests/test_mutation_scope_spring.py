"""S08 T006 (rule 5 · AC-S08-3, -4): the Spring runner — PIT narrowed to the changed classes within the pom's targets.

The tool is a fake `execute` written here, recording the argv and the directory it would run in and returning a status
and the text PIT would print; the pom is read from a real file in the project. Nothing is started.
"""
from __future__ import annotations

import contextlib
import hashlib
import io
import os
import re

from mutation_scope_fixture import ScopeCase
from stamp_fixture import git
from test_mutation_borders import calls, clean_environment, loaded

PACKAGE = "com/example/x"
POM = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <build><plugins>
    <plugin>
      <groupId>org.pitest</groupId>
      <artifactId>pitest-maven</artifactId>
      <configuration>
        <targetClasses>{targets}</targetClasses>
        <targetTests><param>com.example.x.*Test</param></targetTests>
        <excludedTestClasses><param>com.example.x.*IT</param></excludedTestClasses>
        <excludedClasses>{excluded}</excludedClasses>
        <failWhenNoMutations>true</failWhenNoMutations>
      </configuration>
    </plugin>
  </plugins></build>
</project>
"""
NO_MUTATIONS = "[ERROR] failed: No mutations found. This probably means there is an issue with the supplied classpath"
SWEEP = ["./mvnw", "-B", "-q", "test-compile", "org.pitest:pitest-maven:mutationCoverage"]


def params(*names: str) -> str:
    return "".join(f"<param>{name}</param>" for name in names)


NOTHING = ("mutation: no mutant to run — "
           "every changed production file is outside the tools' targets")
SKIPPED = "mutation: skip {} — no changed production file within the tool's targets"


class FakeExecute:
    """The `execute` seam: `(argv, cwd) -> (status, text)`, recorded."""

    def __init__(self, status: int = 0, text: str = "") -> None:
        self.status, self.text = status, text
        self.seen: list[tuple[list[str], str]] = []

    def __call__(self, argv: list[str], cwd: str) -> tuple[int, str]:
        self.seen.append((list(argv), cwd))
        return self.status, self.text


class SpringCase(ScopeCase):
    def pom(self, targets: tuple[str, ...] = ("com.example.x.health.*",), excluded: tuple[str, ...] = ()) -> None:
        self.write("apps/spring/pom.xml", POM.format(targets=params(*targets), excluded=params(*excluded)))

    def java(self, *names: str) -> None:
        for name in names:
            where, _, last = name.rpartition("/")
            package = ".".join(["com.example.x", *([where.replace("/", ".")] if where else [])])
            self.write(f"apps/spring/src/main/java/{PACKAGE}/{name}.java",
                       f"package {package};\n\npublic class {last} {{}}\n")

    def run_spring(self, execute: FakeExecute, *services: str) -> tuple[int, list[str]]:
        """The script with the Spring runner over `execute`, in this process and the project."""
        module = loaded(self.repo / "scripts/mutation-scope.py")
        words = services or ("java-spring:apps/spring",)
        self.fit_recipe(words)
        arguments = ["--make", str(self.make), "--makefile", "Makefile", *words]
        wanted, saved, here = clean_environment(), dict(os.environ), os.getcwd()
        os.environ.clear()
        os.environ.update(wanted)
        os.chdir(self.repo)
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out):
                status = module.main(arguments, module.Tools(execute))
        finally:
            os.chdir(here)
            os.environ.clear()
            os.environ.update(saved)
        return status, out.getvalue().splitlines()


class SpringRunnerTest(SpringCase):
    def test_e1_a_changed_class_inside_the_targets_is_foo_and_foo_dollar_star_never_foo_star(self) -> None:
        self.pom(("com.example.x.*",))
        self.java("health/HealthStatus")
        execute = FakeExecute()
        status, lines = self.run_spring(execute)
        self.assertEqual(status, 0, "\n".join(lines))
        self.assertEqual(execute.seen, [
            ([*SWEEP, "-DtargetClasses=com.example.x.health.HealthStatus,com.example.x.health.HealthStatus$*"],
             "apps/spring")])
        self.assertIn("mutation: scope apps/spring — src/main/java/com/example/x/health/HealthStatus.java", lines)

    def test_e2_two_classes_are_one_comma_separated_value_and_non_classes_are_not_production(self) -> None:
        self.pom(("com.example.x.*",))
        self.java("a/Foo", "a/Bar", "a/package-info", "module-info")
        execute = FakeExecute()
        self.run_spring(execute)
        self.assertEqual(len(execute.seen), 1)
        self.assertEqual(execute.seen[0][0][-1], "-DtargetClasses=com.example.x.a.Bar,com.example.x.a.Bar$*,"
                                   "com.example.x.a.Foo,com.example.x.a.Foo$*")

    def test_e3_a_class_outside_the_targets_or_inside_the_excluded_ones_is_named_and_maven_is_not_started(self) -> None:
        self.pom(("com.example.x.health.*",), ("com.example.x.health.Wiring*",))
        self.java("other/Outside", "health/WiringConfig")
        execute = FakeExecute()
        status, lines = self.run_spring(execute)
        self.assertEqual((status, execute.seen), (0, []))
        for name in ("other/Outside", "health/WiringConfig"):
            self.assertIn(f"mutation: not mutated apps/spring/src/main/java/{PACKAGE}/{name}.java"
                          " — outside PIT's configured targets", lines)
        self.assertEqual(lines[0], NOTHING)
        self.assertEqual([line for line in lines if " apps/spring —" in line and not line.startswith(
            "mutation: not mutated")], [SKIPPED.format("apps/spring")])

    def test_t025_the_scope_line_names_the_classes_pit_takes_and_the_others_are_not_mutated_lines(self) -> None:
        self.pom(("com.example.x.health.*",))
        self.java("health/HealthStatus", "other/Outside")
        _, lines = self.run_spring(FakeExecute())
        kept, left = f"src/main/java/{PACKAGE}/health/HealthStatus.java", f"src/main/java/{PACKAGE}/other/Outside.java"
        self.assertIn(f"mutation: scope apps/spring — {kept}", lines)
        self.assertIn(f"mutation: not mutated apps/spring/{left} — outside PIT's configured targets", lines)
        self.assertFalse([line for line in lines if line.startswith("mutation: scope ") and "Outside" in line], lines)

    def test_t030_a_deleted_service_whose_makefile_was_not_regenerated_fails_by_name_and_starts_nothing(self) -> None:
        git(self.repo, "checkout", "-q", "main")
        self.pom(("com.example.x.*",))
        self.java("health/HealthStatus")
        self.commit("the service")
        git(self.repo, "checkout", "-q", "-B", "slice/S1")
        git(self.repo, "rm", "-rq", "apps/spring")
        execute = FakeExecute()
        status, lines = self.run_spring(execute)
        self.assertEqual((status, execute.seen), (2, []), "\n".join(lines))
        self.assertIn("mutation: refuse apps/spring — the service directory `apps/spring` does not exist; "
                      "the Makefile still names it, so regenerate it or restore the service", lines)
        self.assertEqual(lines[-1], "mutation: 0 scoped, 0 swept, 0 skipped, 1 refused; failed: apps/spring")

    def test_t031_a_renamed_java_class_is_deleted_at_the_old_name_and_targeted_at_its_new_fqn(self) -> None:
        git(self.repo, "checkout", "-q", "main")
        self.pom(("com.example.x.*",))
        self.java("health/OldName")
        self.commit("the class")
        git(self.repo, "checkout", "-q", "-B", "slice/S1")
        git(self.repo, "mv", f"apps/spring/src/main/java/{PACKAGE}/health/OldName.java",
            f"apps/spring/src/main/java/{PACKAGE}/health/NewName.java")
        (self.repo / f"apps/spring/src/main/java/{PACKAGE}/health/NewName.java").write_text(
            "package com.example.x.health;\n\npublic class NewName {}\n", encoding="utf-8")
        execute = FakeExecute()
        status, lines = self.run_spring(execute)
        self.assertEqual(status, 0, "\n".join(lines))
        self.assertEqual(execute.seen, [([*SWEEP, "-DtargetClasses=com.example.x.health.NewName,"
                                          "com.example.x.health.NewName$*"], "apps/spring")])
        self.assertIn(f"mutation: not mutated apps/spring/src/main/java/{PACKAGE}/health/OldName.java"
                      " — deleted, no mutants", lines)

    def test_e4_an_unreadable_pom_or_pattern_is_reported_as_unreadable_naming_the_file(self) -> None:
        self.java("health/HealthStatus")
        for text in ("<project><unclosed>", POM.format(targets=params("${pkg}.*"), excluded=""),
                     POM.format(targets=params("~("), excluded="")):
            with self.subTest(pom=text[:40]):
                self.write("apps/spring/pom.xml", text)
                module = loaded(self.repo / "scripts/mutation-scope.py")
                here = os.getcwd()
                os.chdir(self.repo)
                try:
                    result = module.Tools(FakeExecute()).run(
                        "java-spring", "apps/spring", [f"src/main/java/{PACKAGE}/health/HealthStatus.java"])
                finally:
                    os.chdir(here)
                self.assertIn("apps/spring/pom.xml", result.unreadable or "")

    def test_t020_an_unreadable_pom_is_the_sweep_named_once_and_opens_the_run_so(self) -> None:
        self.java("health/HealthStatus")
        self.write("apps/spring/pom.xml", "<project><unclosed>")
        execute = FakeExecute()
        status, lines = self.run_spring(execute)
        self.assertTrue(lines[0].startswith("mutation: the sweep runs — apps/spring/pom.xml: "), lines)
        named = [line for line in lines if re.match(r"mutation: (scope|skip|sweep|refuse) apps/spring —", line)]
        self.assertEqual(len(named), 1, lines)
        self.assertTrue(named[0].startswith("mutation: sweep apps/spring — apps/spring/pom.xml: "), named)
        self.assertEqual(lines[-1], "mutation: 0 scoped, 1 swept, 0 skipped, 0 refused; passed")
        self.assertEqual(execute.seen, [(SWEEP, "apps/spring")])
        self.assertEqual(status, 0)

    def test_t020_hold_pit_finding_nothing_keeps_the_scope_line_first_and_the_service_named_once(self) -> None:
        self.pom(("com.example.x.*",))
        self.java("health/EventVisitor")
        _, lines = self.run_spring(FakeExecute(1, NO_MUTATIONS))
        self.assertTrue(lines[0].startswith("mutation: scoped to 1 changed file(s) since "), lines)
        named = [line for line in lines if re.match(r"mutation: (scope|skip|sweep|refuse) apps/spring —", line)]
        self.assertEqual(len(named), 1, lines)
        self.assertEqual(lines[-1], "mutation: 1 scoped, 0 swept, 0 skipped, 0 refused; passed")

    def test_e5_pits_no_mutations_text_on_a_scoped_run_is_the_no_mutant_line(self) -> None:
        self.pom(("com.example.x.*",))
        self.java("health/EventVisitor")
        status, lines = self.run_spring(FakeExecute(1, NO_MUTATIONS))
        self.assertEqual(status, 0, "\n".join(lines))
        self.assertIn("mutation: no mutant to run in apps/spring — PIT found no code to mutate in "
                      "com.example.x.health.EventVisitor; no report was written", lines)

    def test_e5_any_other_failure_is_the_services_failure(self) -> None:
        self.pom(("com.example.x.*",))
        self.java("health/HealthStatus")
        status, lines = self.run_spring(FakeExecute(1, "[ERROR] test failures"))
        self.assertEqual(status, 1)
        self.assertEqual(lines[-1], "mutation: 1 scoped, 0 swept, 0 skipped, 0 refused; failed: apps/spring")

    def test_e5_failwhennomutations_is_never_passed(self) -> None:
        """HOLD (teeth: pass the flag and see this fail)."""
        self.pom(("com.example.x.*",))
        self.java("health/HealthStatus")
        execute = FakeExecute()
        self.run_spring(execute)
        self.assertFalse([word for argv, _ in execute.seen for word in argv if "failWhenNoMutations" in word])

    def test_e6_hold_the_pom_is_read_and_never_written(self) -> None:
        self.pom(("com.example.x.*",))
        self.java("health/HealthStatus")
        pom = self.repo / "apps/spring/pom.xml"
        before = hashlib.sha256(pom.read_bytes()).hexdigest()
        names = sorted(path.name for path in (self.repo / "apps/spring").rglob("*"))
        self.run_spring(FakeExecute())
        self.assertEqual(hashlib.sha256(pom.read_bytes()).hexdigest(), before)
        self.assertEqual(sorted(path.name for path in (self.repo / "apps/spring").rglob("*")), names)
        self.assertEqual(calls(self.log), [])
