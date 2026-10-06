"""S08 T005 (rule 4 · AC-S02): the Go runner: one changed file mutates that file only, the other service starts nothing.

The script is the project's own copy, called in this process with its default runner; the tool behind it is the fake
`go` of `test_go_mutation_file` first on `PATH` (real `git`, real `go-mutation.py`), so a Gremlins start is a log line.
"""
from __future__ import annotations

import contextlib
import io
import os
import re
import tempfile
from pathlib import Path

from mutation_scope_fixture import HEALTH, ScopeCase
from stamp_fixture import git
from test_go_mutation_file import FakeTools
from test_mutation_borders import clean_environment, loaded

TWO = ("go:apps/service", "go:apps/billing")


NOTHING = ("mutation: no mutant to run — "
           "every changed production file is outside the tools' targets")
SKIPPED = "mutation: skip {} — no changed production file within the tool's targets"


class GoScopeTest(ScopeCase):
    def run_default(self, *services: str) -> tuple[int, list[str], FakeTools]:
        """The script with its own runners, `go` faked, in the project: status, the lines it said, the tools' log."""
        tools = FakeTools(Path(tempfile.mkdtemp(dir=self.parent)), git=False)
        self.fit_recipe(services or TWO)
        module = loaded(self.repo / "scripts/mutation-scope.py")
        arguments = ["--make", str(self.make), "--makefile", "Makefile", *(services or TWO)]
        saved, here = dict(os.environ), os.getcwd()
        wanted = {**clean_environment(), **tools.environment()}
        os.environ.clear()
        os.environ.update(wanted)
        os.chdir(self.repo)
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out):
                status = module.main(arguments)
        finally:
            os.chdir(here)
            os.environ.clear()
            os.environ.update(saved)
        return status, out.getvalue().splitlines(), tools

    @staticmethod
    def service_lines(lines: list[str], path: str) -> list[str]:
        """The per-service lines that name `path`: every service is named once."""
        return [line for line in lines if re.match(rf"mutation: (scope|skip|sweep|refuse) {path} —", line)]

    def test_e4_one_changed_file_starts_gremlins_once_and_only_for_its_service(self) -> None:
        git(self.repo, "checkout", "-q", "main")
        self.write("apps/service/domain/other.go")
        self.commit()
        git(self.repo, "checkout", "-q", "-B", "slice/S1")
        (self.repo / HEALTH).write_text("package health\n// edited\n", encoding="utf-8")
        status, lines, tools = self.run_default()
        self.assertEqual(status, 0, "\n".join(lines))
        (run,) = tools.runs()
        excluded = [run[i + 1] for i, word in enumerate(run) if word == "--exclude-files"]
        self.assertNotIn(r"^health/health\.go$", excluded)
        self.assertIn(r"^domain/other\.go$", excluded)
        self.assertIn("mutation: scope apps/service — health/health.go", lines)
        self.assertIn("mutation: skip apps/billing — no changed production file", lines)
        self.assertEqual(lines[-1], "mutation: 1 scoped, 0 swept, 1 skipped, 0 refused; passed")

    def test_e5_a_file_the_yaml_excludes_is_named_and_no_tool_starts(self) -> None:
        git(self.repo, "checkout", "-q", "main")
        self.write("apps/service/cmd/serve/main.go", "package main\n")
        self.commit()
        git(self.repo, "checkout", "-q", "-B", "slice/S1")
        self.write("apps/service/cmd/serve/main.go", "package main\n// edited\n")
        status, lines, tools = self.run_default()
        self.assertEqual(status, 0, "\n".join(lines))
        self.assertIn("mutation: not mutated apps/service/cmd/serve/main.go — outside Gremlins' configured targets",
                      lines)
        self.assertEqual(lines[0], NOTHING)
        self.assertEqual(self.service_lines(lines, "apps/service"), [
            SKIPPED.format("apps/service")])
        self.assertEqual(lines[-1], "mutation: 0 scoped, 0 swept, 2 skipped, 0 refused; passed")
        self.assertEqual(tools.runs(), [])

    def test_t025_the_scope_line_names_the_files_gremlins_takes_and_the_others_are_not_mutated_lines(self) -> None:
        self.write("apps/service/cmd/migrate/main.go", "package main\n// edited\n")
        self.write(HEALTH, "package health\n// edited\n")
        status, lines, _ = self.run_default()
        self.assertEqual(status, 0, "\n".join(lines))
        self.assertEqual(self.service_lines(lines, "apps/service"), ["mutation: scope apps/service — health/health.go"])
        self.assertIn("mutation: not mutated apps/service/cmd/migrate/main.go — outside Gremlins' configured targets",
                      lines)

    def test_e4_the_tools_failure_is_the_services_failure(self) -> None:
        self.fit_recipe(TWO)
        (self.repo / HEALTH).write_text("package health\n// edited\n", encoding="utf-8")
        tools = FakeTools(Path(tempfile.mkdtemp(dir=self.parent)), git=False)
        fake = tools.bin / "go"
        fake.write_text(fake.read_text(encoding="utf-8") + "sys.exit(1)\n", encoding="utf-8")
        module = loaded(self.repo / "scripts/mutation-scope.py")
        saved, here = dict(os.environ), os.getcwd()
        wanted = {**clean_environment(), **tools.environment()}
        os.environ.clear()
        os.environ.update(wanted)
        os.chdir(self.repo)
        try:
            with contextlib.redirect_stdout(io.StringIO()) as out:
                status = module.main(["--make", str(self.make), "--makefile", "Makefile", *TWO])
        finally:
            os.chdir(here)
            os.environ.clear()
            os.environ.update(saved)
        self.assertNotEqual(status, 0, out.getvalue())
        self.assertTrue(out.getvalue().splitlines()[-1].endswith("; failed: apps/service"), out.getvalue())
