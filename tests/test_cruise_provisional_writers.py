"""What the factory writes about provisional decisions (S27): the `decide` setting's five values and its sentence.

The four places a person reads the setting from are compared with one another and with the script that enforces it.
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
import tempfile
from types import ModuleType

from support import FactoryTestCase
from test_cruise_runner import cruise
from test_drive_adoption import adopted, wrapped

from slipwai.assets import ROOT, TOOLKIT_ROOT
from slipwai.project.cruise import CONFIG, SETTINGS
from slipwai.project.cruise_provisional import DECIDE_CONTROLS, DECIDE_VALUES
from slipwai.project.cruise_record import DECISION_ENTRY

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


def flat(text: str) -> str:
    return " ".join(text.split())


class BriefsTest(FactoryTestCase):
    """R12: the command, the skipper's brief, the owner brief and the stop table say what provisional means."""

    def test_e1_the_command_names_the_three_verbs_the_trailer_and_who_may(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "command", "standard", "python")
            command = flat((repo / "commands/cruise.md").read_text(encoding="utf-8"))
            settings = flat((repo / "commands/cruise-settings.md").read_text(encoding="utf-8"))
        self.assertIn('"take easy decisions provisionally" is `decide=provisional-shadow` first', settings)
        for words in ("python3 scripts/provisional.py status", "python3 scripts/provisional.py audit",
                      "python3 scripts/agents/cruise.py mode", "Decision: D<n>", "`told: accept`", "no bosun",
                      "Only the skipper takes an always-ask item provisionally", "`Decided by: human`",
                      "`overridden by D<m>`", "question about a gate, a check or CI is never provisional",
                      "`cruise: parked: ratify D<n>`", "`--set decide=…` refuses inside an iteration"):
            self.assertIn(words, command)
        self.assertLess(command.index("python3 scripts/agents/cruise.py mode"), command.index("## The watch seat"))
        audit = command.index("## When the ready set is empty")
        self.assertLess(audit, command.index("provisional.py audit"))
        self.assertLess(command.index("provisional.py audit"), command.index("## The iteration contract"))

    def test_e2_the_skipper_names_the_verb_the_owner_line_the_gate_exception_and_decided(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "skipper", "standard", "python")
            skipper = flat((repo / "agents/drive-skipper.md").read_text(encoding="utf-8"))
        for words in ("python3 scripts/provisional.py status --decide <value> --ask approval", "Score its tier first",
                      "quote in **Why** the owner-brief line the item falls under",
                      "A question about a gate, a check or CI is never provisional", "your `status` is `decided`",
                      "trailer `Decision: D<n>`", "decide as under `recommended-first`"):
            self.assertIn(words, skipper)

    def test_e3_the_owner_brief_shows_the_entry_lines_and_the_always_ask_sentence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "owner", "standard", "python")
            brief = (repo / ".specify/product-owner.md").read_text(encoding="utf-8")
        self.assertIn(DECISION_ENTRY, brief)
        for words in ("provisional · ratify by", "- **Revert:**", "Provisional (shadow"):
            self.assertIn(words, DECISION_ENTRY)
        lines = DECISION_ENTRY.splitlines()
        self.assertTrue(lines[-2].startswith("- **Status:**") and lines[-1].startswith("- **Revert:**"))
        self.assertTrue(lines[-3].startswith("- **Written to:**") and lines[-4].startswith("- **Provisional ("))
        self.assertIn("Under `decide: provisional` an easy or guarded item here may be taken provisionally and is "
                      "listed for ratification (`commands/cruise.md` says how).", flat(brief))

    def test_e4_the_approval_row_names_the_exception_in_the_table_and_the_page(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "stops", "standard", "python")
            command = (repo / "commands/cruise.md").read_text(encoding="utf-8")
        for text in (command, (ROOT / "docs/cruise.md").read_text(encoding="utf-8")):
            line = next(line for line in text.splitlines() if "a person's approval |" in line and "genuinely" in line
                        or line.startswith("| 12 |"))
            self.assertIn("decide: provisional", line)
            self.assertIn("no bosun and no ⛔", line)

    def test_e5_an_adopted_repository_carries_the_same_text_with_the_delivery_path(self) -> None:
        files = adopted([wrapped("shop", ".")])
        command = flat(files["delivery/commands/cruise.md"])
        for verb in ("python3 delivery/scripts/provisional.py status", "python3 delivery/scripts/provisional.py audit",
                     "python3 delivery/scripts/agents/cruise.py mode"):
            self.assertIn(verb, command)
        self.assertIn("python3 delivery/scripts/provisional.py status --decide <value>",
                      flat(files["delivery/agents/drive-skipper.md"]))

    def test_e6_the_command_writer_stays_within_its_cap(self) -> None:
        lines = (ROOT / "src/slipwai/project/cruise.py").read_text(encoding="utf-8").count("\n")
        self.assertLessEqual(lines, 350)


MODES = ("provisional-shadow", "provisional-advisory", "provisional")


def sentences(text: str) -> list[str]:
    return re.split(r"(?<=[.:])\s+(?=[A-Z*])", flat(text))


class ModesAreSeparateTest(FactoryTestCase):
    """T016: each `decide` value has its own sentence, and shadow and advisory take nothing."""

    command = ""
    skipper = ""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        directory = tempfile.TemporaryDirectory()
        cls.addClassCleanup(directory.cleanup)
        repo = cls().generate(directory.name, "modes", "standard", "python")
        cls.command = flat((repo / "commands/cruise.md").read_text(encoding="utf-8"))
        cls.skipper = flat((repo / "agents/drive-skipper.md").read_text(encoding="utf-8"))

    def test_t016_the_command_has_one_sentence_per_value(self) -> None:
        for words in ("Under `decide: provisional-shadow` an always-ask item is not taken: it stays `unavailable`, "
                      "the skipper's `status` is `unavailable`, and the entry only gains the "
                      "`Provisional (shadow):` line",
                      "Under `decide: provisional-advisory` an always-ask item is not taken either: it stays "
                      "`unavailable`, the skipper's `status` is `unavailable`, and the entry only gains the "
                      "`Provisional (advisory):` line",
                      "Under `decide: provisional`, and only there, the skipper takes an easy or guarded approval "
                      "provisionally, as `Status: provisional · ratify by <date>` with a `Revert:` line"):
            self.assertIn(words, self.command)

    def test_t016_the_skipper_has_one_sentence_per_value(self) -> None:
        for words in ("Under `decide: provisional-shadow` an always-ask item is not taken: it stays `unavailable`, "
                      "your `status` is `unavailable`, and the entry only gains the `Provisional (shadow):` line",
                      "Under `decide: provisional-advisory` an always-ask item is not taken either: it stays "
                      "`unavailable`, your `status` is `unavailable`, and the entry only gains the "
                      "`Provisional (advisory):` line",
                      "Under `decide: provisional`, and only there, you take an easy or guarded approval "
                      "provisionally, and your `status` is `decided`"):
            self.assertIn(words, self.skipper)

    def test_t016_no_sentence_grants_taking_under_shadow_or_advisory(self) -> None:
        for text in (self.command, self.skipper):
            for sentence in sentences(text):
                if "provisional-shadow" in sentence or "provisional-advisory" in sentence:
                    self.assertNotIn("Under `decide: provisional-shadow`, `provisional-advisory` or", sentence)
                    self.assertNotRegex(sentence, r"\b(takes|take) an always-ask item provisionally")
                    self.assertNotIn("`status` is `decided`", sentence)
                    self.assertNotIn("`status` stays `decided`", sentence)

    def test_t016_an_enforced_decision_is_not_a_block_only_under_provisional(self) -> None:
        self.assertNotIn("An enforced provisional decision is not a block: your `status` is `decided`", self.skipper)
        self.assertNotIn("no ⛔, the skipper's `status` stays `decided`", self.command)
        self.assertIn("An enforced provisional decision, which only `decide: provisional` makes, is not a block: "
                      "no bosun, no ⛔", self.command)

    def test_t016_the_unavailable_paragraph_names_the_exception(self) -> None:
        self.assertIn("it is never decided, whatever `decide` says, except an approval under `decide: provisional`",
                      self.command)
        self.assertNotIn("whatever `decide` says. It is still an entry", self.command)
