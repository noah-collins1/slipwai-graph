"""T001 (R1, R4, R5 · AC-S07-2, -5, -6, -7, -10): the four method-file checks have rows, so a change to what they read
runs them and nothing else does.

Generated projects are the scoped fixture's: a `slice/S1` branch cut from `main`, a baseline, and the project's own
`verify-scoped.py` run as the person would. `check-agents` reads `.specify/` and `AGENTS.md`; `check-speckit` the
integrations and presets; `check-extensions` the extensions file, `AGENTS.md` and each web app's directory;
`check-constitution` `specs/` and the constitution's files. A row naming nothing is no recorded input.
"""
from __future__ import annotations

import shutil
import subprocess
import sys

from scoped_fixture import LINE, ShapeCase
from stamp_fixture import git
from test_verify_scoped_record import INPUT_KEYS, SCHEMA, UNIT_KEYS, RecordCase, loaded

sys.dont_write_bytecode = True

DRY: dict[str, str | None] = {"STANDIN_DRY": "1"}
FOUR = ("check-agents", "check-speckit", "check-extensions", "check-constitution")
NO_INPUTS = "no recorded inputs"
TEMPLATE = ".specify/presets/x/templates/constitution-template.md"


class FourRecordTest(RecordCase):
    def test_r1_e1_the_four_have_input_objects(self) -> None:
        data = loaded(self.project("model-typescript-web"))
        self.assertEqual(data["schema"], SCHEMA)
        for name in FOUR:
            check = data["checks"][name]
            self.assertEqual(set(check), UNIT_KEYS, name)
            self.assertIsNotNone(check["inputs"], name)
            self.assertEqual(set(check["inputs"]), INPUT_KEYS, name)
            self.assertEqual((check["claims"], check["always"], check["inputs"]["variables"]), (True, None, []), name)
        files = {name: data["checks"][name]["inputs"]["files"] for name in FOUR}
        self.assertIn(".specify/drive.json", files["check-agents"])
        self.assertIn("AGENTS.md", files["check-agents"])
        self.assertIn(".specify/presets/", files["check-speckit"])
        self.assertIn("apps/web/", files["check-extensions"])
        self.assertIn("specs/", files["check-constitution"])

    def test_r5_e1_a_row_with_no_files_and_no_reason_has_no_recorded_inputs(self) -> None:
        project = self.project("model-typescript-web")
        makefile = project / "Makefile"
        makefile.write_text(makefile.read_text(encoding="utf-8")
                            + "\nverify-checks: check-licences\ncheck-licences:\n\t@true\n", encoding="utf-8")
        table = project / "scripts" / "verify_scoped" / "table.py"
        table.write_text(table.read_text(encoding="utf-8") + '\nCHECKS["check-licences"] = Row()\n', encoding="utf-8")
        added = loaded(project)["checks"]["check-licences"]
        self.assertEqual((added["inputs"], added["claims"], added["always"]), (None, False, NO_INPUTS))

    def test_t009_e1_check_decisions_records_the_reversibility_list_among_its_files(self) -> None:
        files = loaded(self.project("model-typescript-web"))["checks"]["check-decisions"]["inputs"]["files"]
        self.assertIn(".slipwai/propagated", files)


class MethodFilesTest(ShapeCase):
    shape = "model-typescript-web"

    def decide(self) -> tuple[dict[str, str], dict[str, str]]:
        return self.decided(self.scoped(env=DRY))

    def assert_only(self, ran: dict[str, str], skipped: dict[str, str], runs: tuple[str, ...]) -> None:
        for name in FOUR:
            if name in runs:
                self.assertIn(name, ran, (ran, skipped))
                self.assertNotIn(name, skipped)
            else:
                self.assertIn(name, skipped, (ran, skipped))
                self.assertNotIn(name, ran)

    def test_r1_e2_drive_json_alone_runs_check_agents_naming_it(self) -> None:
        self.edit(".specify/drive.json", "\n")
        ran, skipped = self.decide()
        self.assertEqual(ran.get("check-agents"), ".specify/drive.json changed")
        self.assert_only(ran, skipped, ("check-agents",))

    def test_r1_e3_agents_md_alone_runs_check_agents_and_check_extensions(self) -> None:
        self.edit("AGENTS.md", "\nan edit\n")
        ran, skipped = self.decide()
        self.assertEqual(ran.get("check-agents"), "AGENTS.md changed")
        self.assert_only(ran, skipped, ("check-agents", "check-extensions"))

    def test_r1_e4_a_preset_template_runs_check_speckit_and_check_constitution(self) -> None:
        self.edit(TEMPLATE, "# a template\n")
        ran, skipped = self.decide()
        self.assertEqual(ran.get("check-speckit"), TEMPLATE + " changed")
        self.assert_only(ran, skipped, ("check-speckit", "check-constitution"))

    def constitute(self) -> None:
        """`main` holds the template as the constitution (and as the template it was installed from); the branch is cut
        from it, with a baseline: nobody has drafted anything, so no spec is yet a reason to fail."""
        git(self.repo, "checkout", "-q", "main")
        template = "# [PROJECT_NAME] Constitution\n\n## Principle 1\n[PRINCIPLE_1_NAME]\n"
        for path in (".specify/memory/constitution.md", ".specify/templates/constitution-template.md"):
            (self.repo / path).parent.mkdir(parents=True, exist_ok=True)
            (self.repo / path).write_text(template, encoding="utf-8")
        git(self.repo, "add", "-f", ".specify")
        git(self.repo, "commit", "-qm", "the template constitution")
        git(self.repo, "checkout", "-q", "-B", "slice/S1")
        self.write_baseline()

    def test_r1_e5_a_spec_over_the_template_constitution_runs_check_constitution_and_it_fails(self) -> None:
        self.constitute()
        self.edit("specs/001-x/spec.md", "# a spec\n")
        made = self.make("check-constitution")
        self.assertNotEqual(made.returncode, 0, made.stdout + made.stderr)
        run = self.scoped(env=DRY)
        ran, skipped = self.decided(run)
        self.assertEqual(ran.get("check-constitution"), "specs/001-x/spec.md changed", (ran, skipped))
        self.assert_only(ran, skipped, ("check-constitution",))
        real = self.scoped()
        self.assertNotEqual(real.returncode, 0, real.stdout + real.stderr)
        self.assertIn("is still the template", real.stderr)

    def make(self, target: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["make", target], cwd=self.repo, env=self.environment(), text=True,
                              capture_output=True, timeout=120)

    def test_r4_e1_a_web_app_deleted_with_project_json_unchanged_runs_check_extensions(self) -> None:
        shutil.rmtree(self.repo / "apps" / "web")
        ran, skipped = self.decide()
        self.assertRegex(ran.get("check-extensions", ""), r"^apps/web/.* changed$", (ran, skipped))
        self.assertNotIn("check-extensions", skipped)

    def test_r4_e2_a_services_source_skips_check_extensions_and_apps_claim_nothing_for_it(self) -> None:
        self.edit("apps/service/src/main.ts", "\n// an edit\n")
        ran, skipped = self.decide()
        self.assertIn("check-extensions", skipped, (ran, skipped))
        self.assertNotIn("check-extensions", ran)

    def test_r5_e2_an_unreadable_declared_file_is_a_changed_path(self) -> None:
        """The baseline cannot be read against it either, so what runs is the full gate, which holds `check-agents`,
        and the line says which file: never a skip of a check that reads what nobody could read."""
        drive = self.repo / ".specify" / "drive.json"
        drive.unlink()
        drive.mkdir()  # a directory in the file's place: no uid can read it, root included
        run = self.scoped(env=DRY)
        self.assertIn(LINE + "no usable baseline (.specify/drive.json is neither a file nor a link) — every check "
                      "that reads a tool or a variable runs", self.scoped_lines(run))
        self.assertEqual(len(self.verify_calls()), 1)
        self.assertEqual(self.decided(run), ({}, {}))

    def test_t009_e2_the_reversibility_list_alone_runs_check_decisions_naming_it(self) -> None:
        self.edit(".slipwai/propagated", "\n")
        run = self.scoped(env=DRY)
        ran, skipped = self.decided(run)
        self.assertEqual(ran.get("check-decisions"), ".slipwai/propagated changed", (ran, skipped, run.stdout))
        self.assertEqual(len(self.verify_calls()), 0)
