"""What the factory writes about provisional decisions (S27): the `decide` setting's five values and its sentence.

The four places a person reads the setting from are compared with one another and with the script that enforces it.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from types import ModuleType

from support import FactoryTestCase
from test_cruise_runner import cruise

from slipwai.assets import ROOT, TOOLKIT_ROOT
from slipwai.project.cruise import CONFIG, SETTINGS
from slipwai.project.cruise_provisional import DECIDE_CONTROLS, DECIDE_VALUES

FIVE = ("recommended-first", "skipper-always", "provisional-shadow", "provisional-advisory", "provisional")
SENTENCE = ("Change it to `provisional-shadow` when always-ask questions are stalling slices and you want to see "
            "which ones would have been taken provisionally before letting any be; move on to "
            "`provisional-advisory`, then `provisional`, once the shadow lines read right.")


def load(relative: str, name: str) -> ModuleType:
    """A toolkit script loaded without leaving bytecode in the factory's assets."""
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location(name, TOOLKIT_ROOT / relative)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def row(text: str) -> str:
    """The `decide` row of a settings table, as one line."""
    return next(line for line in text.splitlines() if line.startswith("| `decide` |"))


def listed(line: str) -> tuple[str, ...]:
    return tuple(part.strip(" `") for part in line.replace("\\|", ",").split("|")[2].split(","))


class DecideSettingTest(FactoryTestCase):
    def test_the_four_sources_list_the_same_five_values_in_order_and_provisional_accepts_them(self) -> None:
        """e1."""
        script = load("scripts/agents/cruise.py", "cruise_under_test")
        provisional = load("scripts/provisional.py", "provisional_under_test")
        server = next(values for key, values, *_ in SETTINGS if key == "decide")
        self.assertEqual(server, FIVE)
        self.assertEqual(DECIDE_VALUES, FIVE)
        self.assertEqual(script.CHOICES["decide"], FIVE)
        self.assertEqual(provisional.DECIDE, FIVE)
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "five", "standard", "python")
            command = row((repo / "commands/cruise-settings.md").read_text())
        page = row((ROOT / "docs/cruise.md").read_text())
        self.assertEqual(listed(command), FIVE)
        self.assertEqual(listed(page), FIVE)

    def test_a_generated_project_still_defaults_to_recommended_first(self) -> None:
        """e2."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "default", "standard", "python")
            self.assertEqual(json.loads((repo / CONFIG).read_text())["decide"], "recommended-first")
            self.assertIn("| `\"recommended-first\"` |",
                          row((repo / "commands/cruise-settings.md").read_text()))

    def test_the_one_sentence_is_in_the_controls_the_settings_command_and_the_page(self) -> None:
        """e3."""
        script = load("scripts/agents/cruise.py", "cruise_sentence_under_test")
        self.assertIn(SENTENCE, DECIDE_CONTROLS)
        self.assertIn(SENTENCE, script.CONTROLS["decide"])
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "sentence", "standard", "python")
            self.assertIn(SENTENCE, row((repo / "commands/cruise-settings.md").read_text()))
        self.assertIn(SENTENCE, row((ROOT / "docs/cruise.md").read_text()))

    def test_setting_decide_to_nonsense_names_the_five(self) -> None:
        """e4."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "nope", "standard", "python")
            refused = cruise(repo, "--set", "decide=nope")
            self.assertEqual(refused.returncode, 1)
            self.assertIn(", ".join(FIVE) + ", not 'nope'", refused.stderr)
            self.assertEqual(json.loads((repo / CONFIG).read_text())["decide"], "recommended-first")
