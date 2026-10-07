"""T002 (R2 · AC-S07-3; D172 limit i): a path an integration manifest lists is an input of `check-speckit`; a
manifest or preset that cannot be trusted makes it a check with no recorded inputs, which runs on every scoped run.

The record is the project's own (`verify-scoped.py record`, as `test_verify_scoped_record` runs it); the one end-to-end
run goes through `make verify-scoped` on a slice branch with a baseline.
"""
from __future__ import annotations

import importlib
import importlib.util
import json
import os
import sys
import unittest
from pathlib import Path
from typing import Any

from scoped_fixture import ShapeCase
from stamp_fixture import git
from test_verify_scoped_record import RecordCase, loaded

from slipwai.assets import ROOT

sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "assets" / "toolkit" / "scripts"))

NO_INPUTS = "no recorded inputs"
DRY: dict[str, str | None] = {"STANDIN_DRY": "1"}
COMMON = ".specify/scripts/bash/common.sh"
MANIFEST = ".specify/integrations/claude.manifest.json"
PRESET = ".specify/presets/x/preset.yml"
STATE = ".specify/integration.json"


def manifest(*keys: str) -> str:
    return json.dumps({"integration": "claude", "files": {key: "0" * 64 for key in keys}})


def commit_on_main(repo: Path, files: dict[str, str]) -> None:
    """Write `files` (forcing past `.gitignore`), commit them on `main`, and branch `slice/S1` from there."""
    git(repo, "checkout", "-q", "main")
    for path, text in files.items():
        (repo / path).parent.mkdir(parents=True, exist_ok=True)
        (repo / path).write_text(text, encoding="utf-8")
        git(repo, "add", "-f", path)
    git(repo, "-c", "user.name=t", "-c", "user.email=t@local", "-c", "maintenance.auto=false", "commit", "-qm", "files")
    git(repo, "checkout", "-q", "-B", "slice/S1")


def state(*installed: str, default: str | None = None) -> str:
    chosen: dict[str, Any] = {"installed_integrations": list(installed)}
    if default:
        chosen["default_integration"] = default
    return json.dumps(chosen)


def entry(project: Path, name: str = "check-speckit") -> dict[str, Any]:
    found: dict[str, Any] = loaded(project)["checks"][name]
    return found


class DerivedCase(RecordCase):
    SHAPE = "standard-python"

    def project_with(self, files: dict[str, str]) -> Path:
        project = self.project(self.SHAPE)
        commit_on_main(project, files)
        return project

    def assert_no_inputs(self, check: dict[str, Any]) -> None:
        self.assertEqual((check["inputs"], check["claims"], check["always"]), (None, False, NO_INPUTS), check)


class ManifestPathsTest(DerivedCase):
    def test_e1_a_manifests_files_are_inputs_of_check_speckit(self) -> None:
        check = entry(self.project_with({MANIFEST: manifest(COMMON, ".specify/templates/")}))
        self.assertIn(COMMON, check["inputs"]["files"])
        self.assertEqual(check["inputs"]["files"], sorted(set(check["inputs"]["files"])))
        self.assertIn(".specify/presets/", check["inputs"]["files"])

    def test_e2_a_path_only_the_bases_manifest_lists_is_still_an_input(self) -> None:
        project = self.project_with({MANIFEST: manifest(COMMON)})
        (project / MANIFEST).unlink()
        self.assertIn(COMMON, entry(project)["inputs"]["files"])

    def test_absent_manifests_add_nothing(self) -> None:
        check = entry(self.project(self.SHAPE))
        self.assertNotIn(COMMON, check["inputs"]["files"])
        self.assertEqual((check["claims"], check["always"]), (True, None))

    def test_e3_a_manifest_that_is_not_json_is_no_recorded_inputs(self) -> None:
        self.assert_no_inputs(entry(self.project_with({MANIFEST: "{"})))

    def test_e3_a_manifest_that_is_not_an_object_or_has_no_files_map_is_no_recorded_inputs(self) -> None:
        for text in ("[]", "{}", '{"files": []}', '{"files": "x"}', '{"files": null}'):
            with self.subTest(text=text):
                self.assert_no_inputs(entry(self.project_with({MANIFEST: text})))

    def test_e4_a_path_outside_the_project_is_no_recorded_inputs(self) -> None:
        for key in ("../outside", "/etc/x", "~/x", "", "a\\b", ".specify/../../x"):
            with self.subTest(key=key):
                self.assert_no_inputs(entry(self.project_with({MANIFEST: manifest(COMMON, key)})))

    def test_e4_a_bad_manifest_in_the_base_alone_is_no_recorded_inputs(self) -> None:
        project = self.project_with({MANIFEST: "{"})
        (project / MANIFEST).write_text(manifest(COMMON), encoding="utf-8")
        self.assert_no_inputs(entry(project))

    def test_e5_a_preset_declaring_a_file_outside_is_no_recorded_inputs(self) -> None:
        for declared in ("../../x", "/etc/x", "a\\b"):
            with self.subTest(declared=declared):
                text = f'id: x\nprovides:\n  templates:\n    - file: "{declared}"\n'
                self.assert_no_inputs(entry(self.project_with({PRESET: text})))

    @unittest.skipIf(os.geteuid() == 0, "root reads a file whatever its mode")
    def test_e5_an_unreadable_preset_is_no_recorded_inputs(self) -> None:
        project = self.project(self.SHAPE)
        (project / PRESET).parent.mkdir(parents=True)
        (project / PRESET).write_text("id: x\n", encoding="utf-8")
        (project / PRESET).chmod(0)
        self.addCleanup((project / PRESET).chmod, 0o644)
        self.assert_no_inputs(entry(project))

    def test_a_preset_declaring_a_file_inside_keeps_its_inputs(self) -> None:
        text = 'id: x\nprovides:\n  templates:\n    - file: "templates/a.md"\n'
        check = entry(self.project_with({PRESET: text}))
        self.assertEqual((check["claims"], check["always"]), (True, None))
        self.assertIsNotNone(check["inputs"])

    def test_the_other_three_are_left_alone(self) -> None:
        project = self.project_with({MANIFEST: "{"})
        for name in ("check-agents", "check-extensions", "check-constitution"):
            self.assertIsNotNone(entry(project, name)["inputs"], name)

    def test_a_preset_registry_naming_a_preset_outside_the_presets_is_no_recorded_inputs(self) -> None:
        """`check-speckit` reads `<name>/preset.yml` and what it declares for each name `.registry` lists, so a name
        that climbs out of `.specify/presets/` makes it read where no input of its says (D172 limit i)."""
        registry = ".specify/presets/.registry"
        for name in ("../../specs/p", "/etc", "~x"):
            with self.subTest(name=name):
                self.assert_no_inputs(entry(self.project_with({registry: json.dumps({"presets": {name: {}}})})))
        kept = entry(self.project_with({registry: json.dumps({"presets": {"x": {"enabled": True}}})}))
        self.assertEqual((kept["claims"], kept["always"]), (True, None))

    def test_the_preset_pattern_is_check_speckits(self) -> None:
        methods = importlib.import_module("verify_scoped.methods")
        path = ROOT / "assets" / "toolkit" / "scripts" / "check-speckit.py"
        spec = importlib.util.spec_from_file_location("check_speckit_text", path)
        assert spec is not None and spec.loader is not None
        speckit = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(speckit)
        self.assertEqual((methods.PRESET_FILE_ENTRY.pattern, methods.PRESET_FILE_ENTRY.flags),
                         (speckit.PRESET_FILE_ENTRY.pattern, speckit.PRESET_FILE_ENTRY.flags))


class IntegrationPathsTest(DerivedCase):
    def files(self, installed: dict[str, str]) -> list[str]:
        found: list[str] = entry(self.project_with(installed), "check-agents")["inputs"]["files"]
        return found

    def test_e1_an_installed_integrations_directories_and_context_file_are_inputs(self) -> None:
        files = self.files({STATE: state("claude")})
        for path in ("CLAUDE.md", ".claude/skills/", ".claude/commands/", ".claude/agents/"):
            self.assertIn(path, files)
        self.assertEqual(files, sorted(set(files)))

    def test_e2_a_hooks_file_is_an_input(self) -> None:
        self.assertIn(".cursor/hooks.json", self.files({STATE: state("cursor-agent")}))

    def test_the_default_integration_is_read_where_none_is_listed(self) -> None:
        files = self.files({STATE: json.dumps({"default_integration": "claude"})})
        self.assertIn("CLAUDE.md", files)

    def test_an_installed_list_wins_over_the_default(self) -> None:
        files = self.files({STATE: state("cursor-agent", default="claude")})
        self.assertIn(".cursor/hooks.json", files)
        self.assertNotIn("CLAUDE.md", files)

    def test_an_integration_only_the_base_installs_is_still_read(self) -> None:
        project = self.project_with({STATE: state("claude")})
        (project / STATE).unlink()
        self.assertIn("CLAUDE.md", entry(project, "check-agents")["inputs"]["files"])

    def test_a_row_naming_a_path_outside_in_the_base_alone_is_no_recorded_inputs(self) -> None:
        project = self.project_with({STATE: state("hermes")})
        (project / STATE).write_text(state("claude"), encoding="utf-8")
        self.assert_no_inputs(entry(project, "check-agents"))

    def test_an_unknown_key_adds_nothing(self) -> None:
        plain = entry(self.project(self.SHAPE), "check-agents")["inputs"]["files"]
        self.assertEqual(self.files({STATE: state("nonesuch")}), plain)

    def test_e3_an_integration_file_that_does_not_parse_or_names_none_is_no_recorded_inputs(self) -> None:
        for text in ("{", "[]", "{}", '{"installed_integrations": []}', '{"default_integration": 3}'):
            with self.subTest(text=text):
                self.assert_no_inputs(entry(self.project_with({STATE: text}), "check-agents"))

    def test_e4_a_row_naming_a_path_outside_the_project_is_no_recorded_inputs(self) -> None:
        self.assert_no_inputs(entry(self.project_with({STATE: state("claude", "hermes")}), "check-agents"))

    def test_e4_an_unreadable_registry_is_no_recorded_inputs(self) -> None:
        for text in ("{", "[]", '{"harnesses": 1}'):
            with self.subTest(text=text):
                project = self.project_with({STATE: state("claude")})
                (project / "scripts" / "agents" / "registry.json").write_text(text, encoding="utf-8")
                self.assert_no_inputs(entry(project, "check-agents"))

    def test_the_other_checks_are_left_alone(self) -> None:
        project = self.project_with({STATE: "{"})
        for name in ("check-speckit", "check-extensions", "check-constitution"):
            self.assertIsNotNone(entry(project, name)["inputs"], name)


class ListedFileRunsTest(ShapeCase):
    shape = "standard-python"

    def test_e1_a_listed_file_that_changed_runs_check_speckit_naming_it(self) -> None:
        commit_on_main(self.repo, {MANIFEST: manifest(COMMON), COMMON: "#!/bin/sh\n"})
        self.write_baseline()
        self.edit(COMMON, "\n# an edit\n")
        ran, skipped = self.decided(self.scoped(env=DRY))
        self.assertEqual(ran.get("check-speckit"), COMMON + " changed", (ran, skipped))
        self.assertIn("check-agents", skipped)

    def runs_check_agents_naming(self, installed: str, path: str) -> None:
        commit_on_main(self.repo, {STATE: state(installed), path: "# context\n"})
        self.write_baseline()
        self.edit(path, "\nan edit\n")
        ran, skipped = self.decided(self.scoped(env=DRY))
        self.assertEqual(ran.get("check-agents"), path + " changed", (ran, skipped))
        self.assertIn("check-speckit", skipped)

    def test_e1_a_changed_context_file_runs_check_agents_naming_it(self) -> None:
        self.runs_check_agents_naming("claude", "CLAUDE.md")

    def test_e2_a_changed_hooks_file_runs_check_agents_naming_it(self) -> None:
        self.runs_check_agents_naming("cursor-agent", ".cursor/hooks.json")


if __name__ == "__main__":
    unittest.main()
