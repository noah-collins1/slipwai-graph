"""S08 T027 (AC-S08-1): under make's dry-run flags (`-n`, `-q`, `-t`, read from `MAKEFLAGS`) the run prints its plan.

The recipe names `$(MAKE)`, so make runs it even under `-n`; the script is what has to start nothing. The runner here is
a tripwire written in the test tree: it fails on a wired backend's `run` or `sweep`, and the fake make logs every call.
Only a refusal, which starts no tool, is let through to the script's own.
"""
from __future__ import annotations

import contextlib
import io
import os
from typing import Any

from mutation_scope_fixture import HEALTH, SLICE, ScopeCase
from stamp_fixture import git
from test_mutation_borders import calls, clean_environment, loaded

YAML = "apps/billing/.gremlins.yaml"
TWO_GO = ("go:apps/service", "go:apps/billing")
FLAGS = ("n", "q", "t", "nk")


class Tripwire:
    """Records any tool the script starts for a wired backend; a refusal starts none and is the script's."""

    def __init__(self, module: Any) -> None:
        self.started: list[tuple[str, str]] = []
        self.real = module.Tools()

    def run(self, backend: str, path: str, files: list[str]) -> Any:
        if backend in ("go", "java-spring"):
            self.started.append(("run", path))
        return self.real.run(backend, path, files)

    def sweep(self, backend: str, path: str) -> Any:
        if backend in ("go", "java-spring"):
            self.started.append(("sweep", path))
        return self.real.sweep(backend, path)


class DryRunTest(ScopeCase):
    def under(self, flags: str, *services: str) -> tuple[int, list[str], Tripwire]:
        self.fit_recipe(services)
        module = loaded(self.repo / "scripts/mutation-scope.py")
        runner = Tripwire(module)
        saved, here = dict(os.environ), os.getcwd()
        os.environ.clear()
        os.environ.update(clean_environment(MAKEFLAGS=flags))
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

    def nothing_started(self, runner: Tripwire, lines: list[str]) -> None:
        self.assertEqual((runner.started, calls(self.log)), ([], []), "\n".join(lines))

    def test_a_scoped_run_prints_the_scope_and_starts_no_tool(self) -> None:
        self.write(HEALTH, "package health\n// edited\n")
        for flags in FLAGS:
            with self.subTest(flags=flags):
                status, lines, runner = self.under(flags, "go:apps/service")
                self.assertTrue(lines[0].startswith(f"mutation: dry run (make was run with -{flags})"), lines)
                self.assertIn("mutation: scope apps/service — health/health.go", lines)
                self.assertEqual((status, lines[-1]), (0, "mutation: 1 scoped, 0 swept, 0 skipped, 0 refused; planned"))
                self.nothing_started(runner, lines)

    def test_a_per_service_sweep_prints_the_sweep_and_starts_no_tool(self) -> None:
        git(self.repo, "checkout", "-q", "main")
        self.write(YAML, "unleash: {}\n")
        self.commit("base")
        git(self.repo, "checkout", "-q", "-B", SLICE)
        self.write(YAML, "unleash:\n  integration: true\n")
        self.write("apps/service/health/more.go")
        status, lines, runner = self.under("n", *TWO_GO)
        self.assertIn(f"mutation: sweep apps/billing — `{YAML}` changed", lines)
        self.assertIn("mutation: scope apps/service — health/more.go", lines)
        self.assertEqual((status, lines[-1]), (0, "mutation: 1 scoped, 1 swept, 0 skipped, 0 refused; planned"))
        self.nothing_started(runner, lines)

    def test_a_whole_sweep_prints_the_reason_and_runs_no_make(self) -> None:
        self.write("scripts/mutation-scope.py", (self.repo / "scripts/mutation-scope.py").read_text(
            encoding="utf-8") + "\n# probe\n")
        status, lines, runner = self.under("n", "go:apps/service")
        self.assertEqual(lines[0], "mutation: dry run (make was run with -n) — the plan below starts no tool")
        self.assertIn("mutation: the sweep runs — `scripts/mutation-scope.py` changed", lines)
        self.assertEqual(status, 0)
        self.nothing_started(runner, lines)

    def test_a_refusal_is_the_plan_and_the_dry_run_exits_0(self) -> None:
        paths = {"typescript": "apps/service/src/x.ts", "python": "apps/service/src/pkg/x.py",
                 "java-quarkus": "apps/service/src/main/java/com/x/Foo.java"}
        for backend, path in paths.items():
            for flags in ("n", "q", "t"):
                with self.subTest(backend=backend, flags=flags):
                    self.write(path)
                    status, lines, runner = self.under(flags, f"{backend}:apps/service")
                    self.assertEqual(lines[0], f"mutation: dry run (make was run with -{flags}) — "
                                     "the plan below starts no tool")
                    self.assertTrue(any(line.startswith("mutation: refuse apps/service — ") for line in lines), lines)
                    closing = "mutation: 0 scoped, 0 swept, 0 skipped, 1 refused; dry run — would fail: apps/service"
                    self.assertEqual((status, lines[-1]), (0, closing))
                    self.nothing_started(runner, lines)

    def test_an_adopted_layout_prints_the_recorded_command_and_runs_no_make(self) -> None:
        project = self.repo / "project.json"
        project.write_text(project.read_text(encoding="utf-8").rstrip().removesuffix("}")
                           + ', "layout": {"delivery": "delivery"}}', encoding="utf-8")
        status, lines, runner = self.under("n", "go:apps/service")
        self.assertEqual(lines[0], "mutation: dry run (make was run with -n) — the plan below starts no tool")
        self.assertIn("mutation: this layout has no mutation scope — the recorded command runs", lines)
        self.assertEqual(status, 0)
        self.nothing_started(runner, lines)
