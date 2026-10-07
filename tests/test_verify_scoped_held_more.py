"""T012 (AC-S07-8; D172 limit ii): the audit over the branches a starter with Claude alone never takes.

`test_verify_scoped_held` audits every starter shape with Claude installed and one manifest. Here a web starter elects
the `ux-gates` extension (so `check-extensions` reads each extension's `ready()` and `installed_block`), installs
`cursor-agent` and `gemini` beside Claude (a `copy` context file and a hooks projection each, so `check-agents` reads
`copy_context_blocks` and `hook_file`) and carries one preset with a `.registry` (so `check-speckit` reads
`preset_findings`). Every path each of the four touches lies under its recorded inputs, by the same rule as there.
"""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from test_verify_scoped_held import FOUR, HeldCase, findings_of, reported
from test_verify_scoped_record import environment

sys.dont_write_bytecode = True

SHAPE = "model-typescript-web"
HARNESSES = ["claude", "cursor-agent", "gemini"]
COPIES = {".cursor/rules/specify-rules.mdc": "# rules\n", "GEMINI.md": "# gemini\n"}
PRESETS = ".specify/presets"
PRESET_FILE = "templates/a.md"
ELECT = (
    "import runpy, sys; sys.path.insert(0, 'scripts/extensions'); "
    "runpy.run_path('scripts/extensions/ux-gates/init.py')['project_guidance']()"
)


class WideCase(HeldCase):
    SHAPES = (SHAPE,)

    def install(self, project: Path) -> None:
        """Claude, cursor-agent and gemini installed and projected, an extension elected, a preset registered."""
        for name, text in COPIES.items():
            (project / name).parent.mkdir(parents=True, exist_ok=True)
            (project / name).write_text(text, encoding="utf-8")
        super().install(project)
        (project / ".specify" / "integration.json").write_text(
            json.dumps({"installed_integrations": HARNESSES, "default_integration": "claude"}), encoding="utf-8")
        for step in (["python3", "-B", "-c", ELECT], ["python3", "-B", "scripts/agents/project.py"]):
            done = subprocess.run(step, cwd=project, env=environment(), text=True, capture_output=True, timeout=120)
            assert done.returncode == 0, done.stdout + done.stderr
        preset = project / PRESETS / "p"
        (preset / "templates").mkdir(parents=True)
        (preset / PRESET_FILE).write_text("# a\n", encoding="utf-8")
        (preset / "preset.yml").write_text(f'id: p\nprovides:\n  templates:\n    - file: "{PRESET_FILE}"\n',
                                           encoding="utf-8")
        (project / PRESETS / ".registry").write_text(json.dumps({"presets": {"p": {"enabled": True}}}),
                                                     encoding="utf-8")


class WideAuditTest(WideCase):
    maxDiff = None

    def test_the_shape_takes_the_branches(self) -> None:
        """Each branch the starters never reach is read by its check, or the audit holds nothing there."""
        project, events, _ = self.audit(SHAPE)
        agents = {path for _, path in events["check-agents"]}
        speckit = {path for _, path in events["check-speckit"]}
        extensions = {path for _, path in events["check-extensions"]}
        self.assertTrue({".cursor/hooks.json", ".gemini/settings.json"} <= agents, sorted(agents)[:40])
        self.assertTrue({".cursor/rules/specify-rules.mdc", "GEMINI.md"} <= agents, sorted(agents)[:40])
        self.assertIn(f"{PRESETS}/.registry", speckit)
        self.assertIn(f"{PRESETS}/p/preset.yml", speckit)
        self.assertTrue({".slipwai/extensions.json", "AGENTS.md"} <= extensions, sorted(extensions))
        self.assertIn("apps/web", " ".join(sorted(extensions)))
        self.assertTrue((project / ".slipwai" / "extensions.json").is_file())

    def test_every_path_a_check_touches_lies_under_its_recorded_inputs(self) -> None:
        project, events, files = self.audit(SHAPE)
        findings = [f"{name} touched {path}, under none of its inputs" for name in FOUR
                    for path in findings_of(project, events[name], files[name],
                                            reported(project) if name == "check-agents" else None)]
        self.assertEqual(findings, [])

    def test_teeth_dropping_the_presets_directory_from_the_row_names_the_registry(self) -> None:
        project, events, files = self.audit(SHAPE)
        narrowed = [path for path in files["check-speckit"] if not path.startswith(PRESETS)]
        self.assertNotEqual(narrowed, files["check-speckit"], "the row names no presets path to drop")
        self.assertEqual(findings_of(project, events["check-speckit"], files["check-speckit"]), [])
        found = findings_of(project, events["check-speckit"], narrowed)
        self.assertIn(f"{PRESETS}/.registry", found)


if __name__ == "__main__":
    unittest.main()
