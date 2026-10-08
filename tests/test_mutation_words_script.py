"""S08 T004 (rule 3 · AC-S08-12): the words the script prints, first line, per-service lines and last line.

The same words for every backend: the fake `Runner` stands in for the tool and the services are declared on the command
line, so a Python, a TypeScript and a mixed project are the Go project's tree with other files in it.
"""
from __future__ import annotations

import itertools
import re
from types import SimpleNamespace
from typing import Any

import mutation_scope_fixture
from mutation_scope_fixture import HEALTH, FakeRunner, ScopeCase
from stamp_fixture import git
from test_mutation_borders import clean_environment

FIRST = re.compile(r"^mutation: scoped to (\d+) changed file\(s\) since `main` at ([0-9a-f]{7,}): (.+)$")


class PlanningRunner(FakeRunner):
    """The fake with the tool's other half: what it would take is decided before the run, as the real tools' is."""

    def plan(self, backend: str, path: str, files: list[str]) -> Any:
        kept = files if self.mutable is None else self.mutable.get(path, [])
        return SimpleNamespace(keep=list(kept), unreadable=None, refusal=None,  # the shape of the script's `Plan`
                               left=[(name, "outside the tool's targets") for name in files if name not in kept])


class WordsTest(ScopeCase):
    def two_services(self) -> None:
        self.write("apps/service/health/health.go", "package health\n// edited\n")

    def test_e1_one_changed_file_in_one_of_two_services(self) -> None:
        self.two_services()
        ran = self.run_in_process("go:apps/service", "go:apps/billing")
        match = FIRST.match(ran.first)
        self.assertTrue(match, ran.out)
        self.assertEqual(match.group(1) if match else "", "1")
        self.assertTrue((match.group(3) if match else "") == HEALTH, ran.out)
        self.assertEqual(ran.lines[1:], [
            "mutation: scope apps/service — health/health.go",
            "mutation: skip apps/billing — no changed production file",
            "mutation: 1 scoped, 0 swept, 1 skipped, 0 refused; passed",
        ])
        self.assertEqual(ran.runner.seen, [("apps/service", ["health/health.go"])])

    def test_e6_one_failing_service_fails_the_run_after_both_ran(self) -> None:
        self.write("apps/service/health/health.go", "package health\n// edited\n")
        self.write("apps/billing/b.go")
        ran = self.run_in_process("go:apps/service", "go:apps/billing", runner_args={"statuses": {"apps/service": 1}})
        self.assertEqual(ran.status, 1)
        self.assertEqual([path for path, _ in ran.runner.seen], ["apps/service", "apps/billing"])
        self.assertEqual(ran.last,
                         "mutation: 2 scoped, 0 swept, 0 skipped, 0 refused; failed: apps/service")

    def test_e6_the_status_is_the_first_non_zero_in_service_order(self) -> None:
        self.write("apps/service/a.go")
        self.write("apps/billing/b.go")
        ran = self.run_in_process("go:apps/service", "go:apps/billing",
                                  runner_args={"statuses": {"apps/service": 3, "apps/billing": 1}})
        self.assertEqual(ran.status, 3)
        self.assertTrue(ran.last.endswith("; failed: apps/service, apps/billing"), ran.last)

    def test_e6_no_file_the_tool_will_mutate_says_so(self) -> None:
        self.write("apps/service/a.go")
        self.addCleanup(setattr, mutation_scope_fixture, "FakeRunner", FakeRunner)
        setattr(mutation_scope_fixture, "FakeRunner", PlanningRunner)  # noqa: B010 -- the run site reads this name
        ran = self.run_in_process(runner_args={"mutable": {}})
        self.assertIn("mutation: not mutated apps/service/a.go — outside the tool's targets", ran.lines)
        every = "mutation: no mutant to run — every changed production file is outside the tools' targets"
        self.assertEqual(ran.first, every)
        self.assertEqual(ran.status, 0)
        self.assertEqual(ran.last, "mutation: 0 scoped, 0 swept, 1 skipped, 0 refused; passed")

    def test_e7_the_words_are_the_same_for_every_backend(self) -> None:
        shapes = {
            "python": (["python:apps/service"], "apps/service/src/pkg/mod.py"),
            "typescript": (["typescript:apps/service"], "apps/service/src/app.ts"),
            "go-go": (["go:apps/service", "go:apps/billing"], "apps/billing/b.go"),
            "mixed": (["go:apps/service", "python:apps/worker"], "apps/worker/src/w.py"),
        }
        for name, (services, path) in shapes.items():
            with self.subTest(shape=name):
                self.write(path, "x = 1\n")
                ran = self.run_in_process(*services)
                self.assertTrue(FIRST.match(ran.first), ran.out)
                self.assertTrue(all(line.startswith("mutation: ") for line in ran.lines), ran.out)
                self.assertRegex(ran.last, r"^mutation: \d+ scoped, \d+ swept, \d+ skipped, \d+ refused; passed$")
                self.assertEqual(len(ran.runner.seen), 1)
                self.commit()


class FirstLineTest(ScopeCase):
    """T022 (data-model *The words*): the first line is the outcome, whatever changed beside the files no tool takes."""

    SHAPES = {
        "go": ("go:apps/service", "apps/service/{}", ["a.go", "a_test.go", "gone.go"]),
        "spring": ("java-spring:apps/spring", "apps/spring/src/{}", ["main/java/x/A.java", "test/java/x/ATest.java",
                                                                       "main/java/x/Gone.java"]),
    }
    ONLY_TESTS = "mutation: no mutant to run — only tests changed: "
    NONE = "mutation: no mutant to run — no production file changed"
    OUTSIDE = "mutation: no mutant to run — every changed production file is outside the tools' targets"

    def base(self) -> None:
        """The files a combination deletes exist at the base: committed on `main`, the slice cut again from it."""
        git(self.repo, "checkout", "-q", "main")
        for _, template, (_, _, gone) in self.SHAPES.values():
            self.write(template.format(gone))
        self.commit("base")
        git(self.repo, "checkout", "-q", "-B", "slice/S1")

    def combination(self, backend: str, kinds: tuple[str, ...], outside: bool) -> Any:
        word, template, (production, test, gone) = self.SHAPES[backend]
        git(self.repo, "reset", "-q", "--hard", "HEAD")
        git(self.repo, "clean", "-fdq")
        if "tests" in kinds:
            self.write(template.format(test))
        if "packages" in kinds:
            self.write("packages/shared/a.txt", "x\n")
        if "deleted" in kinds:
            (self.repo / template.format(gone)).unlink()
        if outside:
            self.write(template.format(production))
        self.addCleanup(setattr, mutation_scope_fixture, "FakeRunner", FakeRunner)
        setattr(mutation_scope_fixture, "FakeRunner", PlanningRunner)  # noqa: B010 -- the run site reads this name
        return self.run_in_process(word, runner_args={"mutable": {}})

    def test_t022_the_first_line_is_the_outcome_in_every_combination_beside_files_no_tool_takes(self) -> None:
        self.base()
        kinds = [c for n in (1, 2, 3) for c in itertools.combinations(("tests", "packages", "deleted"), n)]
        for backend in self.SHAPES:
            for combo in kinds:
                for outside in (True, False):
                    with self.subTest(backend=backend, kinds=combo, outside=outside):
                        ran = self.combination(backend, combo, outside)
                        if outside:
                            self.assertEqual(ran.first, self.OUTSIDE, ran.out)
                        elif combo == ("tests",):
                            self.assertTrue(ran.first.startswith(self.ONLY_TESTS), ran.out)
                        else:
                            self.assertEqual(ran.first, self.NONE, ran.out)
                        self.assertEqual(ran.status, 0)
                        if "packages" in combo:
                            self.assertIn("mutation: not mutated packages/shared/a.txt — not mutated by this target",
                                          ran.lines)


class EarlierReportTest(ScopeCase):
    """T044 (B7): a Go service the run starts no tool for keeps no earlier report that reads as this run's."""

    REPORT = "apps/service/gremlins.json"

    def plant(self) -> None:
        self.write(self.REPORT, '{"mutants_killed": 0}\n')

    def test_t044_a_service_with_nothing_to_mutate_loses_the_report_of_an_earlier_run(self) -> None:
        self.plant()
        self.write("apps/service/health/extra_test.go")
        ran = self.run_in_process("go:apps/service", "go:apps/billing")
        self.assertIn("mutation: skip apps/service — no changed production file", ran.lines)
        self.assertFalse((self.repo / self.REPORT).exists(), ran.out)

    def test_t044_a_service_whose_changed_files_the_tool_leaves_out_loses_it_too(self) -> None:
        self.plant()
        self.write("apps/service/cmd/x.go")
        self.addCleanup(setattr, mutation_scope_fixture, "FakeRunner", FakeRunner)
        setattr(mutation_scope_fixture, "FakeRunner", PlanningRunner)  # noqa: B010 -- the run site reads this name
        ran = self.run_in_process("go:apps/service", runner_args={"mutable": {}})
        self.assertIn("mutation: skip apps/service — no changed production file within the tool's targets", ran.lines)
        self.assertFalse((self.repo / self.REPORT).exists(), ran.out)

    def test_t044_hold_a_service_the_tool_runs_for_keeps_its_report_for_the_tool_to_replace(self) -> None:
        self.plant()
        self.write(HEALTH, "package health\n// edited\n")
        ran = self.run_in_process("go:apps/service")
        self.assertIn("mutation: scope apps/service — health/health.go", ran.lines)
        self.assertTrue((self.repo / self.REPORT).exists(), ran.out)

    def test_t044_hold_a_dry_run_removes_nothing(self) -> None:
        self.plant()
        self.write("apps/service/health/extra_test.go")
        ran = self.run_in_process("go:apps/service", env=clean_environment(MAKEFLAGS="n"))
        self.assertIn("mutation: skip apps/service — no changed production file", ran.lines)
        self.assertTrue((self.repo / self.REPORT).exists(), ran.out)
