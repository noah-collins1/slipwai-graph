"""S08 T007 (rule 6 · AC-S08-5, -6): placeholders refuse with their setup message and name what they would mutate.

TypeScript, Python and `java-quarkus` have no tool wired (D137, recorded as a stub): a service of one with a
changed production file refuses and fails the run after every service has run; an untouched one is skipped; a wired
service beside it still runs. The wired side is a fake `Runner` written here, the placeholders are the script's own.
"""
from __future__ import annotations

import contextlib
import io
import os
import re
import subprocess
import tempfile
from typing import Any

from mutation_scope_fixture import FakeRunner, ScopeCase
from test_mutation_borders import clean_environment, loaded

from slipwai.project.native_commands import service_commands

SETUP = "the scope will apply once a tool is wired; it would mutate: "
ECHO = re.compile(r"echo '([^']+)'")
PYTHON_ENDING = ("a Python service is refused until a later slipwai release wires mutmut, whether or not mutmut is "
                 "installed; `make mutation-full` runs mutmut today where it is installed")
FILES = {
    "typescript": "apps/service/src/x.ts",
    "python": "apps/service/src/pkg/x.py",
    "java-quarkus": "apps/service/src/main/java/com/x/Foo.java",
}


class Mixed:
    """The wired side is a fake, the placeholders are the script's own `Tools`."""

    def __init__(self, module: Any, **arguments: Any) -> None:
        self.wired = FakeRunner(module, **arguments)
        self.real = module.Tools()

    def run(self, backend: str, path: str, files: list[str]) -> Any:
        return (self.wired if backend == "go" else self.real).run(backend, path, files)


class PlaceholderTest(ScopeCase):
    def run_mixed(self, *services: str, **arguments: Any) -> tuple[int, list[str], Mixed]:
        self.fit_recipe(services)
        module = loaded(self.repo / "scripts/mutation-scope.py")
        runner = Mixed(module, **arguments)
        wanted, saved, here = clean_environment(), dict(os.environ), os.getcwd()
        os.environ.clear()
        os.environ.update(wanted)
        os.chdir(self.repo)
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out):
                status = module.main(["--make", str(self.make), "--makefile", "Makefile", *services], runner)
        finally:
            os.chdir(here)
            os.environ.clear()
            os.environ.update(saved)
        return status, out.getvalue().splitlines(), runner

    def test_e1_e2_a_changed_file_refuses_with_the_setup_message_the_clause_and_the_file(self) -> None:
        for backend, path in FILES.items():
            with self.subTest(backend=backend):
                self.write(path)
                status, lines, _ = self.run_mixed(f"{backend}:apps/service")
                message = PLACEHOLDER_MESSAGES[backend].rstrip(".")
                ending = " (" + PYTHON_ENDING + ")" if backend == "python" else ""
                self.assertIn(f"mutation: refuse apps/service — {message}; {SETUP}{path}{ending}", lines)
                self.assertEqual(status, 2)
                self.assertEqual(lines[-1], "mutation: 0 scoped, 0 swept, 0 skipped, 1 refused; failed: apps/service")
                self.assertFalse([line for line in lines if line.startswith("mutation: scope ")], lines)
                self.commit()

    def test_t020_only_placeholders_changed_keeps_the_scope_line_first_and_each_service_named_once(self) -> None:
        self.write(FILES["typescript"])
        self.write(FILES["python"].replace("apps/service", "apps/other"))
        _, lines, _ = self.run_mixed("typescript:apps/service", "python:apps/other", "java-quarkus:apps/third")
        self.assertTrue(lines[0].startswith("mutation: scoped to 2 changed file(s) since "), lines)
        for path, word in (("apps/service", "refuse"), ("apps/other", "refuse"), ("apps/third", "skip")):
            named = [line for line in lines if re.match(rf"mutation: (scope|skip|sweep|refuse) {path} —", line)]
            self.assertEqual(len(named), 1, lines)
            self.assertTrue(named[0].startswith(f"mutation: {word} {path} — "), named)
        self.assertEqual(lines[-1],
                         "mutation: 0 scoped, 0 swept, 1 skipped, 2 refused; failed: apps/service, apps/other")

    def test_e1_the_scripts_table_is_the_text_the_sweep_echoes_today(self) -> None:
        """HOLD (teeth: change a string in the script's table): one source of the setup sentence per placeholder."""
        module = loaded(self.repo / "scripts/mutation-scope.py")
        self.assertEqual(set(module.PLACEHOLDERS), set(FILES))
        for backend in FILES:
            recipe = service_commands(backend, "apps/service")["mutation"]
            said = ECHO.findall(recipe)
            self.assertEqual(module.PLACEHOLDERS[backend], said[0], backend)

    def test_d149_a_python_refusal_says_until_which_slice_and_what_the_sweep_runs_today(self) -> None:
        self.write(FILES["python"])
        _, lines, _ = self.run_mixed("python:apps/service")
        refusal = next(line for line in lines if line.startswith("mutation: refuse apps/service — "))
        self.assertIn(f"{PLACEHOLDER_MESSAGES['python'].rstrip('.')}; {SETUP}{FILES['python']}", refusal)
        for words in ("until a later slipwai release wires mutmut", "whether or not mutmut is installed",
                      "`make mutation-full` runs mutmut today where it is installed"):
            self.assertIn(words, refusal)

    def test_d149_hold_the_other_refusals_do_not_name_mutmut(self) -> None:
        for backend in ("typescript", "java-quarkus"):
            self.write(FILES[backend])
            _, lines, _ = self.run_mixed(f"{backend}:apps/service")
            self.assertNotIn("mutmut", " ".join(lines).lower().replace("mutation:", ""), backend)

    def test_e3_a_placeholder_first_no_longer_stops_a_wired_service(self) -> None:
        self.write("apps/billing/b.go")
        status, lines, runner = self.run_mixed("typescript:apps/service", "go:apps/billing")
        self.assertIn("mutation: skip apps/service — no changed production file", lines)
        self.assertEqual(runner.wired.seen, [("apps/billing", ["b.go"])])
        self.assertEqual(status, 0, "\n".join(lines))
        self.assertEqual(lines[-1], "mutation: 1 scoped, 0 swept, 1 skipped, 0 refused; passed")

    def test_e3_both_changed_the_wired_service_still_runs_and_the_run_fails_with_2(self) -> None:
        self.write("apps/billing/b.go")
        self.write(FILES["typescript"])
        status, lines, runner = self.run_mixed("typescript:apps/service", "go:apps/billing")
        self.assertEqual(runner.wired.seen, [("apps/billing", ["b.go"])])
        self.assertEqual(status, 2)
        self.assertEqual(lines[-1], "mutation: 1 scoped, 0 swept, 0 skipped, 1 refused; failed: apps/service")

    def test_e3_the_first_non_zero_in_service_order_is_the_status(self) -> None:
        self.write("apps/billing/b.go")
        self.write(FILES["python"])
        status, _, _ = self.run_mixed("go:apps/billing", "python:apps/service", statuses={"apps/billing": 1})
        self.assertEqual(status, 1)

    def test_e4_only_a_test_file_changed_is_no_mutant_to_run_not_a_refusal(self) -> None:
        self.write("apps/service/src/x.test.ts")
        self.write("apps/other/tests/test_y.py")
        status, lines, _ = self.run_mixed("typescript:apps/service", "python:apps/other")
        self.assertTrue(lines[0].startswith("mutation: no mutant to run — only tests changed: "), lines)
        self.assertEqual(status, 0)

    def test_e4_an_untouched_placeholder_is_skipped_and_the_run_passes(self) -> None:
        self.write("README.md", "x\n")
        status, lines, _ = self.run_mixed("python:apps/service")
        self.assertEqual((status, lines[-1]), (0, "mutation: 0 scoped, 0 swept, 1 skipped, 0 refused; passed"))

    def test_e5_production_and_test_files_per_backend(self) -> None:
        module = loaded(self.repo / "scripts/mutation-scope.py")
        table = {
            "typescript": {"src/a.ts": "production", "src/a.tsx": "production", "src/a.d.ts": "other",
                           "src/a.test.ts": "test", "src/a.spec.ts": "test", "tests/a.ts": "test",
                           "README.md": "other"},
            "python": {"src/pkg/a.py": "production", "tests/test_a.py": "test", "src/pkg/a.txt": "other"},
            "java-quarkus": {"src/main/java/com/x/A.java": "production",
                             "src/main/java/com/x/package-info.java": "other",
                             "src/main/java/module-info.java": "other",
                             "src/test/java/com/x/ATest.java": "test", "pom.xml": "other"},
            "java-spring": {"src/main/java/com/x/A.java": "production", "src/test/java/com/x/ATest.java": "test"},
            "go": {"a/b.go": "production", "a/b_test.go": "test", "go.mod": "other"},
        }
        for backend, files in table.items():
            for name, kind in files.items():
                with self.subTest(backend=backend, file=name):
                    found, _, inside = module.classify(f"apps/service/{name}", "M", [(backend, "apps/service")])
                    self.assertEqual((found, inside), (kind, name))

    def test_e6_hold_the_sweep_of_a_typescript_project_is_still_its_setup_message(self) -> None:
        """HOLD (teeth: change a placeholder string in `native_commands`): `make mutation-full`, run for real."""
        with tempfile.TemporaryDirectory(prefix="placeholder-", dir="/tmp") as directory:
            repo = self.generate(directory, "placeholder", "standard", "typescript", "none", http="none")
            done = subprocess.run(["make", "mutation-full"], cwd=repo, env=clean_environment(), text=True,
                                  capture_output=True, timeout=120)
            self.assertEqual(done.returncode, 2, done.stdout + done.stderr)
            self.assertIn(PLACEHOLDER_MESSAGES["typescript"], done.stdout)


PLACEHOLDER_MESSAGES = {
    "typescript": "Configure the repository-selected Stryker mutator, then run its checked-in configuration.",
    "python": "install and configure mutmut for the selected production packages",
    "java-quarkus": "Configure PIT for the domain packages only — see the note above this target — then run it.",
}
