"""S08 T006 (rule 5 · AC-S08-3): the one real Spring run — PIT mutates the changed class only, on the pinned plugin.

Gated by `backends_under_test()` naming `java-spring`, a JDK on `PATH` and the project's `mvnw` running. It holds
research R1's finding — the `-DtargetClasses` user property wins over the pom's configured list — against the
plugin version the starter pins, so a new pin that stops honouring it fails here.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from stamp_fixture import git
from support import FactoryTestCase, backends_under_test
from test_mutation_borders import clean_environment


def pit_report(project: Path) -> str:
    """The text of the newest `mutations.xml` PIT wrote under the service."""
    reports = (project / "apps/service/target/pit-reports").rglob("mutations.xml")
    found = sorted(reports, key=lambda p: p.stat().st_mtime)
    return found[-1].read_text(encoding="utf-8") if found else ""


def classes_of(report: str) -> tuple[set[str], int]:
    return set(re.findall(r"<mutatedClass>([^<]+)</mutatedClass>", report)), report.count("<mutation ")


def spring_project(case: FactoryTestCase, directory: str) -> Path | None:
    """A Spring starter on `slice/S1` with `HealthStatus` edited; None where the machine cannot run it."""
    if "java-spring" not in backends_under_test() or shutil.which("java") is None:
        return None
    repo = case.generate(directory, "scoped-spring", "event-modelling", "java-spring", "none")
    if not (repo / "apps/service/mvnw").is_file():
        return None
    git(repo, "checkout", "-q", "-b", "slice/S1")
    edited = next((repo / "apps/service/src/main/java").rglob("HealthStatus.java"))
    edited.write_text("// edited\n" + edited.read_text(encoding="utf-8"), encoding="utf-8")
    return repo


class RealSpringTest(FactoryTestCase):
    def test_e7_make_mutation_mutates_the_changed_class_only_and_fewer_mutants_than_the_sweep(self) -> None:
        with tempfile.TemporaryDirectory(prefix="real-spring-", dir="/tmp") as directory:
            repo = spring_project(self, directory)
            if repo is None:
                self.skipTest("the Spring slice of the matrix, with a JDK and a runnable mvnw")
            done = subprocess.run(["make", "mutation"], cwd=repo, env=clean_environment(), text=True,
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=600)
            self.assertEqual(done.returncode, 0, done.stdout[-3000:])
            lines = done.stdout.splitlines()
            self.assertRegex(lines[0], r"^mutation: scoped to 1 changed file\(s\) since `main` at [0-9a-f]+: "
                                       r"apps/service/src/main/java/com/example/\w+/health/HealthStatus\.java$")
            self.assertEqual(lines[-1], "mutation: 1 scoped, 0 swept, 0 skipped, 0 refused; passed")
            scoped_classes, scoped_count = classes_of(pit_report(repo))
            self.assertEqual({name.rsplit(".", 1)[-1] for name in scoped_classes}, {"HealthStatus"}, scoped_classes)
            full = subprocess.run(["make", "mutation-full"], cwd=repo, env=clean_environment(), text=True,
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=600)
            self.assertEqual(full.returncode, 0, full.stdout[-3000:])
            swept_classes, swept_count = classes_of(pit_report(repo))
            self.assertGreater(len(swept_classes), 1)
            self.assertLess(scoped_count, swept_count)
