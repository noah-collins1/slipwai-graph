"""S41 T007, T009 (rules 5 and 7 · AC-S41-1, -2, -3, -7, -8): `make mutation` for a TypeScript service.

The project is the Go one `mutation_scope_fixture` cuts, with the wrapper and a `stryker.config.json` per TypeScript
service committed on `main` (the base), so a change on `slice/S1` is the change under test. The tool is a recording
`Runner` written here that plans with the script's own `Tools` (the config and the wrapper's list are real) and runs
nothing: the real wrapper behind a fake `npm` is `test_stryker_verdict`'s, the real Stryker is
`test_mutation_scope_real_typescript`'s.
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import sys
from typing import Any

from stamp_fixture import git
from test_mutation_borders import clean_environment, loaded
from test_mutation_sweeps import Recorded, Recording

from slipwai.assets import LANGUAGE_ROOT

sys.dont_write_bytecode = True
WRAPPER = LANGUAGE_ROOT / "typescript" / "scripts/stryker-mutation.py"
LIST = ["src/**/*.ts", "!src/main.ts", "!src/openapi.ts"]
HEALTH = "apps/service/src/health.ts"
OUTSIDE = "outside Stryker's configured targets"
TWO = ("typescript:apps/service", "typescript:apps/second")
GO_AND = ("go:apps/service", "typescript:apps/second")


class Planned(Recording):
    """The recording `Runner` with the script's own plan for TypeScript: what the config's list takes is real."""

    def __init__(self, module: Any) -> None:
        super().__init__(module)
        self.tools = module.Tools()

    def plan(self, backend: str, path: str, files: list[str]) -> Any:
        return self.tools.plan(backend, path, files)

    def run(self, backend: str, path: str, files: list[str]) -> Any:
        """As `Tools.run` does: only what the plan keeps is handed over, and what it leaves out is named."""
        plan = self.plan(backend, path, files)
        self.scoped.append((path, plan.keep))
        return self.result(0, plan.keep, plan.left)


class TypeScriptCase(Recorded):
    """`apps/service` and `apps/second` are TypeScript services at the base: a config each, the wrapper too."""

    def setUp(self) -> None:
        super().setUp()
        self.on_main("scripts/stryker-mutation.py", text=WRAPPER.read_text(encoding="utf-8"))
        self.on_main("apps/service/stryker.config.json", "apps/second/stryker.config.json",
                     text=json.dumps({"mutate": LIST}))
        self.on_main(".gitignore", text=(self.repo / ".gitignore").read_text(encoding="utf-8") + "reports/mutation/\n")

    def reset(self) -> None:
        """Back to the base: no change from an earlier example of the same test."""
        git(self.repo, "checkout", "-q", "--", ".")
        git(self.repo, "clean", "-qfd", "apps", "packages", "docs")

    def run_planned(self, *services: str, env: dict[str, str] | None = None) -> tuple[int, list[str], Planned]:
        self.fit_recipe(services)
        module = loaded(self.repo / "scripts/mutation-scope.py")
        recording = Planned(module)
        wanted, saved, here = (clean_environment() if env is None else env), dict(os.environ), os.getcwd()
        os.environ.clear()
        os.environ.update(wanted)
        os.chdir(self.repo)
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out):
                status = module.main(["--make", str(self.make), "--makefile", "Makefile", *services], recording)
        finally:
            os.chdir(here)
            os.environ.clear()
            os.environ.update(saved)
        return status, out.getvalue().splitlines(), recording


class ScopeTest(TypeScriptCase):
    def test_e1_one_changed_file_is_scoped_to_that_file_in_that_service(self) -> None:
        self.write(HEALTH, "export const health = 1;\n")
        status, lines, recording = self.run_planned("typescript:apps/service")
        self.assertEqual(status, 0, lines)
        self.assertTrue(lines[0].startswith("mutation: scoped to 1 changed file(s) since `main` at "), lines)
        self.assertTrue(lines[0].endswith(f": {HEALTH}"), lines[0])
        self.assertIn("mutation: scope apps/service — src/health.ts", lines)
        self.assertEqual(lines[-1], "mutation: 1 scoped, 0 swept, 0 skipped, 0 refused; passed")
        self.assertEqual(recording.scoped, [("apps/service", ["src/health.ts"])])

    def test_e2_the_other_service_starts_no_tool_and_keeps_no_earlier_report(self) -> None:
        for services, other in ((TWO, "apps/second"), (GO_AND, "apps/second")):
            with self.subTest(services=services):
                self.reset()
                earlier = self.repo / other / "reports/mutation/mutation.json"
                earlier.parent.mkdir(parents=True, exist_ok=True)
                earlier.write_text("{}", encoding="utf-8")
                self.write(HEALTH if services == TWO else "apps/service/domain/x.go", "export const a = 1;\n")
                status, lines, recording = self.run_planned(*services)
                self.assertEqual(status, 0, lines)
                self.assertIn(f"mutation: skip {other} — no changed production file", lines)
                self.assertEqual([path for path, _ in recording.scoped], ["apps/service"])
                self.assertFalse(earlier.exists(), "an earlier run's report is left to read as this run's")
        self.reset()
        gremlins = self.repo / "apps/service/gremlins.json"
        gremlins.write_text("{}", encoding="utf-8")
        self.write("apps/second/src/b.ts", "export const b = 1;\n")
        _, lines, recording = self.run_planned(*GO_AND)
        self.assertEqual(recording.scoped, [("apps/second", ["src/b.ts"])])
        self.assertIn("mutation: skip apps/service — no changed production file", lines)
        self.assertFalse(gremlins.exists())

    def test_e3_a_file_outside_the_list_is_named_and_starts_nothing(self) -> None:
        for name in ("main", "openapi"):
            with self.subTest(file=name):
                self.write(f"apps/service/src/{name}.ts", "export const a = 1;\n")
                status, lines, recording = self.run_planned("typescript:apps/service")
                self.assertEqual(status, 0, lines)
                self.assertIn(f"mutation: not mutated apps/service/src/{name}.ts — {OUTSIDE}", lines)
                self.assertEqual(lines[0], "mutation: no mutant to run — every changed production file is outside "
                                           "the tools' targets")
                self.assertEqual(recording.scoped, [])
                self.reset()
        self.write(HEALTH, "export const a = 1;\n")
        self.write("apps/service/src/main.ts", "export const m = 1;\n")
        status, lines, recording = self.run_planned("typescript:apps/service")
        self.assertEqual(recording.scoped, [("apps/service", ["src/health.ts"])])
        self.assertIn(f"mutation: not mutated apps/service/src/main.ts — {OUTSIDE}", lines)
        self.assertEqual(status, 0)

    def test_e4_a_browser_app_file_is_named_and_no_service_runs_for_it(self) -> None:
        project = json.loads((self.repo / "project.json").read_text(encoding="utf-8"))
        project["deployables"]["web"] = {"kind": "web", "path": "apps/web", "language": "typescript"}
        self.on_main("project.json", text=json.dumps(project))
        self.write("apps/web/src/App.tsx", "export const App = 1;\n")
        self.write("packages/shared/x.ts", "export const x = 1;\n")
        status, lines, recording = self.run_planned("typescript:apps/service")
        self.assertEqual(status, 0, lines)
        self.assertIn("mutation: not mutated apps/web/src/App.tsx — browser app, not mutated by this target", lines)
        self.assertIn("mutation: not mutated packages/shared/x.ts — not mutated by this target", lines)
        self.assertEqual(recording.scoped, [])
        self.assertEqual(lines[-1], "mutation: 0 scoped, 0 swept, 1 skipped, 0 refused; passed")

    def test_e4_t034_a_browser_only_change_does_not_open_with_no_production_file_changed(self) -> None:
        """T034 (demo 1): `App.tsx` is production code; the first line must not contradict the second."""
        project = json.loads((self.repo / "project.json").read_text(encoding="utf-8"))
        project["deployables"]["web"] = {"kind": "web", "path": "apps/web", "language": "typescript"}
        self.on_main("project.json", text=json.dumps(project))
        self.write("apps/web/src/App.tsx", "export const App = 1;\n")
        status, lines, recording = self.run_planned("typescript:apps/service")
        self.assertEqual((status, recording.scoped), (0, []), lines)
        self.assertEqual(lines[0], "mutation: no mutant to run — no service production file changed")
        self.assertIn("mutation: not mutated apps/web/src/App.tsx — browser app, not mutated by this target", lines[1])

    def test_e4_a_changed_test_beside_a_changed_browser_file_is_not_only_tests_changed(self) -> None:
        """T024: the browser file is a source file that changed, so the closing words are not the tests-only ones."""
        project = json.loads((self.repo / "project.json").read_text(encoding="utf-8"))
        project["deployables"]["web"] = {"kind": "web", "path": "apps/web", "language": "typescript"}
        self.on_main("project.json", text=json.dumps(project))
        self.write("apps/service/src/health.test.ts", "export const t = 1;\n")
        self.write("apps/web/src/App.tsx", "export const App = 1;\n")
        status, lines, recording = self.run_planned("typescript:apps/service")
        self.assertEqual((status, recording.scoped), (0, []), lines)
        self.assertEqual(lines[0], "mutation: no mutant to run — no service production file changed")
        self.assertIn("mutation: not mutated apps/web/src/App.tsx — browser app, not mutated by this target", lines)

    def test_e4_hold_a_path_under_no_deployable_is_whatever_it_was(self) -> None:
        self.write("docs/notes.md", "x\n")
        status, lines, _ = self.run_planned("typescript:apps/service")
        self.assertEqual((status, lines[0]), (0, "mutation: no mutant to run — no production file changed"))
        self.assertFalse([line for line in lines if "browser app" in line])

    def test_e5_a_list_the_script_cannot_read_is_that_service_s_sweep(self) -> None:
        self.on_main("apps/service/stryker.config.json", text=json.dumps({"mutate": ["src/**/*.{ts,tsx}"]}))
        self.write(HEALTH, "export const a = 1;\n")
        status, lines, recording = self.run_planned("typescript:apps/service")
        self.assertEqual(status, 0, lines)
        sweep = next(line for line in lines if line.startswith("mutation: sweep apps/service — "))
        self.assertIn("apps/service/stryker.config.json", sweep)
        self.assertEqual((recording.swept, recording.scoped), (["apps/service"], []))

    def test_e6_hold_the_borders_since_and_an_empty_change_set_behave_as_for_go(self) -> None:
        """HOLD (teeth: make the empty change set sweep and see the last example fail)."""
        self.fit_recipe(("typescript:apps/service",))
        self.write(HEALTH, "export const a = 1;\n")
        self.commit("health")
        since = {**clean_environment(), "SINCE": "HEAD~1"}
        _, lines, recording = self.run_planned("typescript:apps/service", env=since)
        self.assertEqual(recording.scoped, [("apps/service", ["src/health.ts"])], lines)
        git(self.repo, "checkout", "-q", "main")
        _, lines, _ = self.run_planned("typescript:apps/service")
        self.assertTrue(any(line.startswith("mutation: the sweep runs — ") for line in lines), lines)
        git(self.repo, "checkout", "-q", "-B", "slice/S2", "main")
        status, lines, recording = self.run_planned("typescript:apps/service")
        self.assertEqual((status, lines[0], recording.scoped, recording.swept),
                         (0, "mutation: no mutant to run — no production file changed", [], []))


def words(file: str, char: str) -> str:
    return (f"`apps/service/{file}` holds `{char}`, which Stryker's --mutate reads as pattern syntax; "
            "rename it, or run `make mutation-full`")


class RefusalTest(TypeScriptCase):
    """Rule 7, scope half (D215 d): a changed path `--mutate` would misread refuses its service, and starts no tool."""

    def test_e1_a_comma_in_a_changed_path_refuses_the_service_and_runs_and_sweeps_nothing(self) -> None:
        self.write("apps/service/src/a,b.ts", "export const a = 1;\n")
        status, lines, recording = self.run_planned("typescript:apps/service")
        self.assertEqual(status, 2, lines)
        self.assertIn("mutation: refuse apps/service — " + words("src/a,b.ts", ","), lines)
        self.assertEqual(lines[-1], "mutation: 0 scoped, 0 swept, 0 skipped, 1 refused; failed: apps/service")
        self.assertEqual((recording.scoped, recording.swept), ([], []))

    def test_e2_every_misread_shape_is_refused(self) -> None:
        for file, char in (("a,b.ts", ","), ("a*.ts", "*"), ("a?.ts", "?"), ("{a}.ts", "{"), ("[a].ts", "["),
                           ("!a.ts", "!"), ("a+(b).ts", "+("), ("a@(b).ts", "@("), ("a\\b.ts", "\\")):
            with self.subTest(file=file):
                self.write(f"apps/service/src/{file}", "export const a = 1;\n")
                status, lines, recording = self.run_planned("typescript:apps/service")
                self.assertEqual(status, 2, lines)
                self.assertIn("mutation: refuse apps/service — " + words(f"src/{file}", char), lines)
                self.assertEqual((recording.scoped, recording.swept), ([], []))
                self.reset()

    def test_e2_a_trailing_line_number_never_reaches_the_service_as_a_production_file(self) -> None:
        """`src/a.ts:12` ends in no TypeScript extension, so it is no production file and is never handed to
        Stryker: the wrapper's refusal of that shape (`test_stryker_list`) is for a `--file` given by hand."""
        self.write("apps/service/src/a.ts:12", "export const a = 1;\n")
        status, lines, recording = self.run_planned("typescript:apps/service")
        self.assertEqual((status, recording.scoped, recording.swept), (0, [], []), lines)
        self.assertFalse([line for line in lines if "refuse " in line], lines)

    def test_e3_a_refused_file_refuses_the_whole_service_and_another_service_still_runs(self) -> None:
        self.write("apps/service/src/a,b.ts", "export const a = 1;\n")
        self.write(HEALTH, "export const h = 1;\n")
        self.write("apps/second/src/b.ts", "export const b = 1;\n")
        status, lines, recording = self.run_planned(*TWO)
        self.assertEqual(status, 2, lines)
        self.assertEqual(recording.scoped, [("apps/second", ["src/b.ts"])])
        self.assertEqual(lines[-1], "mutation: 1 scoped, 0 swept, 0 skipped, 1 refused; failed: apps/service")

    def test_e4_the_refusal_is_louder_than_outside_targets_and_only_typescript_production(self) -> None:
        self.write("apps/service/src/main,x.ts", "export const m = 1;\n")
        _, lines, _ = self.run_planned("typescript:apps/service")
        self.assertIn("mutation: refuse apps/service — " + words("src/main,x.ts", ","), lines)
        self.assertFalse([line for line in lines if OUTSIDE in line], lines)
        self.reset()
        self.write("apps/service/src/a,b.test.ts", "export const t = 1;\n")
        self.write("apps/service/domain/a,b.go", "package domain\n")
        status, lines, recording = self.run_planned(*GO_AND)
        self.assertEqual(status, 0, lines)
        self.assertFalse([line for line in lines if "refuse " in line], lines)
        self.assertEqual(recording.scoped, [("apps/service", ["domain/a,b.go"])])

    def test_e5_a_dry_run_says_would_fail_and_leaves_the_earlier_report(self) -> None:
        earlier = self.repo / "apps/service/reports/mutation/mutation.json"
        earlier.parent.mkdir(parents=True)
        earlier.write_text("{}", encoding="utf-8")
        self.write("apps/service/src/a,b.ts", "export const a = 1;\n")
        status, lines, recording = self.run_planned("typescript:apps/service", env=clean_environment(MAKEFLAGS="n"))
        self.assertEqual(status, 0, lines)
        self.assertEqual(lines[-1], "mutation: 0 scoped, 0 swept, 0 skipped, 1 refused; "
                                    "dry run — would fail: apps/service")
        self.assertEqual((recording.scoped, recording.swept), ([], []))
        self.assertTrue(earlier.exists(), "the run did not happen, so the earlier report is not this run's to remove")
