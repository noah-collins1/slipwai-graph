"""S08 T008 (rule 7 · AC-S08-8): what sweeps — configuration, the scripts, and the rule's own text.

Real `git`, with the base commit holding the old pom and Makefile; the tool is a recording `Runner` written here
that says whether it was asked for a scope or for a sweep. A change that no scope can be trusted across names its
file and sweeps the service, or the whole run, and a change that cannot be told apart from a harmless one sweeps too.
"""
from __future__ import annotations

import contextlib
import io
import os
from typing import Any

from mutation_scope_fixture import SLICE, ScopeCase
from stamp_fixture import git
from test_mutation_borders import FULL, calls, clean_environment, loaded
from test_mutation_scope_spring import POM, params

YAML = "apps/billing/.gremlins.yaml"
TWO_GO = ("go:apps/service", "go:apps/billing")
SPRING = "java-spring:apps/spring"
PIT = POM.format(targets=params("com.example.x.*"), excluded="")
OTHER = "<plugin><artifactId>other</artifactId></plugin>"


class Recording:
    """Which services were asked for a scope, which for a sweep."""

    def __init__(self, module: Any) -> None:
        self.result = module.Result
        self.scoped: list[tuple[str, list[str]]] = []
        self.swept: list[str] = []

    def run(self, backend: str, path: str, files: list[str]) -> Any:
        self.scoped.append((path, list(files)))
        return self.result(0, list(files), [])

    def sweep(self, backend: str, path: str) -> Any:
        self.swept.append(path)
        return self.result(0, [], [])


class SweepsTest(ScopeCase):
    makefile_arg = "Makefile"  # what the recipe's `$(firstword $(MAKEFILE_LIST))` is, which T041's examples vary

    def on_main(self, *names: str, text: str = "package x\n") -> None:
        """Files that exist at the base: committed on `main`, then the slice branch is cut again from it."""
        git(self.repo, "checkout", "-q", "main")
        for name in names:
            self.write(name, text)
        self.commit("base")
        git(self.repo, "checkout", "-q", "-B", SLICE)

    def run_recording(self, *services: str, env: dict[str, str] | None = None) -> tuple[int, list[str], Recording]:
        self.fit_recipe(services)
        module = loaded(self.repo / "scripts/mutation-scope.py")
        recording = Recording(module)
        wanted, saved, here = (clean_environment() if env is None else env), dict(os.environ), os.getcwd()
        os.environ.clear()
        os.environ.update(wanted)
        os.chdir(self.repo)
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out):
                status = module.main(["--make", str(self.make), "--makefile", self.makefile_arg, *services], recording)
        finally:
            os.chdir(here)
            os.environ.clear()
            os.environ.update(saved)
        return status, out.getvalue().splitlines(), recording

    def test_e1_a_changed_added_or_deleted_gremlins_yaml_sweeps_that_service_only(self) -> None:
        self.on_main(YAML, text="unleash: {}\n")
        self.write("apps/service/health/more.go")
        for change in ("edit", "delete", "add"):
            with self.subTest(change=change):
                if change == "edit":
                    self.write(YAML, "unleash:\n  integration: true\n")
                elif change == "delete":
                    (self.repo / YAML).unlink()
                else:
                    git(self.repo, "checkout", "-q", "--", YAML)
                    git(self.repo, "rm", "-q", "-f", "--cached", YAML)
                status, lines, recording = self.run_recording(*TWO_GO)
                self.assertIn(f"mutation: sweep apps/billing — `{YAML}` changed", lines)
                self.assertEqual(recording.swept, ["apps/billing"])
                self.assertEqual(recording.scoped, [("apps/service", ["health/more.go"])])
                self.assertEqual(status, 0)
                self.assertEqual(lines[-1], "mutation: 1 scoped, 1 swept, 0 skipped, 0 refused; passed")

    def test_e2_the_pitest_block_changing_as_parsed_structure_sweeps_and_nothing_else_does(self) -> None:
        self.on_main("apps/spring/pom.xml", text=PIT)
        self.write("apps/spring/src/main/java/com/example/x/A.java", "package com.example.x;\nclass A {}\n")
        cases = {
            "the pitest block's targets": (PIT.replace("com.example.x.*", "com.example.y.*"), True),
            "another plugin or dependency": (PIT.replace("</plugins>", f"{OTHER}</plugins>")
                                             .replace("<build>", "<dependencies/><build>"), False),
            "a comment and whitespace in the block": (PIT.replace("<configuration>", "<configuration>\n <!-- c -->\n"),
                                                      False),
            "the plugin among the others": (PIT.replace("<plugins>", f"<plugins>{OTHER}"), False),
            "a pom that does not parse": ("<project><oops>", True),
        }
        for name, (text, sweeps) in cases.items():
            with self.subTest(change=name):
                self.write("apps/spring/pom.xml", text)
                status, lines, recording = self.run_recording(SPRING)
                self.assertEqual(recording.swept, ["apps/spring"] if sweeps else [], lines)
                self.assertEqual(sweeps, "mutation: sweep apps/spring — `apps/spring/pom.xml` changed" in lines, lines)
                self.assertEqual(status, 0)

    def test_e2_a_pom_that_did_not_parse_at_the_base_sweeps_when_it_changes(self) -> None:
        self.on_main("apps/spring/pom.xml", text="<project><oops>")
        self.write("apps/spring/pom.xml", PIT)
        _, lines, recording = self.run_recording(SPRING)
        self.assertEqual(recording.swept, ["apps/spring"], lines)

    def test_e3_go_mutation_py_sweeps_every_go_service_and_not_a_spring_one(self) -> None:
        self.edit("scripts/go-mutation.py")
        self.write("apps/spring/src/main/java/com/example/x/A.java", "package com.example.x;\nclass A {}\n")
        self.write("apps/spring/pom.xml", PIT)
        self.commit("unrelated")
        git(self.repo, "checkout", "-q", "main")
        git(self.repo, "checkout", "-q", SLICE)
        status, lines, recording = self.run_recording(*TWO_GO, SPRING)
        self.assertEqual(sorted(recording.swept), ["apps/billing", "apps/service"])
        self.assertIn("mutation: sweep apps/service — `scripts/go-mutation.py` changed", lines)
        self.assertEqual([path for path, _ in recording.scoped], ["apps/spring"])
        self.assertEqual(status, 0)

    def test_e3_the_scope_script_or_the_mutation_rule_text_sweeps_the_whole_run(self) -> None:
        for name, edit in (("script", self.edit_script), ("rule", self.edit_rule)):
            with self.subTest(change=name):
                git(self.repo, "checkout", "-q", "-B", SLICE, "main")
                git(self.repo, "checkout", "-q", "--", ".")
                edit()
                status, lines, recording = self.run_recording(*TWO_GO)
                file = "scripts/mutation-scope.py" if name == "script" else "Makefile"
                self.assertEqual(lines[0], f"mutation: the sweep runs — `{file}` changed", lines)
                self.assertEqual((recording.scoped, recording.swept), ([], []))
                self.assertEqual(len(calls(self.log)), 1)
                self.log.unlink()

    def edit(self, name: str) -> None:
        path = self.repo / name
        path.write_text(path.read_text(encoding="utf-8") + "\n# e\n", encoding="utf-8")

    def edit_script(self) -> None:
        self.edit("scripts/mutation-scope.py")

    def edit_rule(self) -> None:
        path = self.repo / "Makefile"
        path.write_text(path.read_text(encoding="utf-8").replace("mutation: ##", "mutation: ## (changed)", 1),
                        encoding="utf-8")

    def test_e3_a_change_elsewhere_in_the_makefile_does_not_sweep(self) -> None:
        self.fit_recipe(TWO_GO)
        path = self.repo / "Makefile"
        path.write_text(path.read_text(encoding="utf-8") + "\nelsewhere:\n\t@true\n", encoding="utf-8")
        self.write("apps/service/health/more.go")
        status, lines, recording = self.run_recording(*TWO_GO)
        self.assertEqual(recording.swept, [])
        self.assertTrue(lines[0].startswith("mutation: scoped to 1 changed file(s)"), lines)
        self.assertEqual(calls(self.log), [])

    def test_e4_two_causes_in_one_service_sweep_it_once_naming_each_and_scope_nothing_there(self) -> None:
        self.on_main(YAML, text="unleash: {}\n")
        self.write(YAML, "unleash:\n  integration: true\n")
        self.write("apps/billing/b.go")
        self.edit("scripts/go-mutation.py")
        _, lines, recording = self.run_recording(*TWO_GO)
        self.assertIn(f"mutation: sweep apps/billing — `{YAML}` changed, `scripts/go-mutation.py` changed", lines)
        self.assertEqual(recording.swept.count("apps/billing"), 1)
        self.assertNotIn("apps/billing", [path for path, _ in recording.scoped])

    def test_e5_hold_a_since_run_sweeps_on_the_same_triggers(self) -> None:
        git(self.repo, "checkout", "-q", "main")
        self.fit_recipe(TWO_GO)
        self.write(YAML, "unleash: {}\n")
        self.commit("yaml")
        status, lines, recording = self.run_recording(*TWO_GO, env=clean_environment(SINCE="HEAD~1"))
        self.assertIn(f"mutation: sweep apps/billing — `{YAML}` changed", lines)
        self.assertEqual(recording.swept, ["apps/billing"])

    def test_t019_a_whole_run_sweep_under_since_clears_since_for_the_sub_make(self) -> None:
        """Go's `$(if $(SINCE),--since …)` would scope a sweep: the command line `SINCE=` beats the environment and
        `MAKEFLAGS` alike, from either source of the variable."""
        self.fit_recipe(TWO_GO)
        for name, edit in (("script", self.edit_script), ("rule", self.edit_rule)):
            for source, extra in (("environment", {}), ("make's command line", {"MAKEFLAGS": "-- SINCE=main"})):
                with self.subTest(change=name, since=source):
                    git(self.repo, "checkout", "-q", "-B", SLICE, "main")
                    git(self.repo, "checkout", "-q", "--", ".")
                    edit()
                    status, lines, recording = self.run_recording(*TWO_GO, env=clean_environment(SINCE="main", **extra))
                    self.assertTrue(lines[0].startswith("mutation: the sweep runs — "), lines)
                    self.assertEqual(calls(self.log), [[*FULL, "SINCE="]], lines)
                    self.assertEqual((recording.scoped, recording.swept, status), ([], [], 0))
                    self.log.unlink()

    def test_t019_hold_an_adopted_layout_under_since_keeps_the_recorded_command_as_it_is(self) -> None:
        project = self.repo / "project.json"
        project.write_text(project.read_text(encoding="utf-8").rstrip().removesuffix("}")
                           + ', "layout": {"delivery": "delivery"}}', encoding="utf-8")
        _, lines, _ = self.run_recording(*TWO_GO, env=clean_environment(SINCE="main"))
        self.assertEqual(lines[0], "mutation: this layout has no mutation scope — the recorded command runs")
        self.assertEqual(calls(self.log), [FULL])
