"""What the factory writes so the reversibility verb can tell a method file from the project's own.

`generate` writes `.slipwai/propagated` (D175, D183): the method's categories and the list, nothing of the
project's. `replay` regenerates it, an adopted repository has none (its `.written` is the list), and the verb
reads the very path the factory wrote.
"""
from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path
from types import ModuleType

from support import FactoryTestCase
from test_drive_adoption import adopted, wrapped
from test_replay import replay, tree

from slipwai.assets import PROPAGATED, ROOT, VERSION

MUST_NAME = (
    "scripts/check-decisions.py", "scripts/reversibility.py", "commands/cruise.md", ".specify/product-owner.md",
    "Makefile", PROPAGATED,
)


def verb() -> ModuleType:
    """`scripts/reversibility.py` loaded without leaving bytecode in the factory's assets."""
    sys.dont_write_bytecode = True
    path = ROOT / "assets/toolkit/scripts/reversibility.py"
    spec = importlib.util.spec_from_file_location("reversibility_under_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class PropagatedListTest(FactoryTestCase):
    def test_a_generated_project_lists_the_method_and_nothing_of_its_own(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            for profile in ("standard", "event-modelling"):
                repo = self.generate(directory, f"p-{profile}", profile, "typescript")
                lines = (repo / PROPAGATED).read_text(encoding="utf-8").splitlines()
                self.assertEqual(lines, sorted(set(lines)))
                for path in MUST_NAME:
                    self.assertIn(path, lines)
                for path in lines:
                    self.assertTrue((repo / path).is_file(), path)
                    self.assertFalse(path.startswith(("apps/", "docs/")) or path == "README.md", path)

    def test_replay_regenerates_the_list_byte_for_byte(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "twin", "standard", "typescript")
            self.assertEqual(replay(repo).returncode, 0)
            twin = Path(directory) / f"twin-at-{VERSION}"
            self.assertEqual(tree(twin)[PROPAGATED], tree(repo)[PROPAGATED])

    def test_an_adopted_repository_has_no_list_and_its_written_is_unchanged(self) -> None:
        files = adopted([wrapped("shop", "shop")])
        self.assertNotIn(PROPAGATED, files)
        listed = files["delivery/.written"].splitlines()
        self.assertFalse([path for path in listed if "propagated" in path])
        self.assertEqual(listed, sorted(files))

    def test_the_verb_reads_the_path_the_factory_writes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "reads", "standard", "typescript")
            listed = verb().propagated(repo)
            self.assertEqual(listed, set((repo / PROPAGATED).read_text(encoding="utf-8").splitlines()))
            self.assertIn(PROPAGATED, listed)


LINE = "- **Reversibility:** <tier> · rules <n> · <facts, as python3 scripts/reversibility.py prints the line>"
RULE_LINE = ("- **Proposed rule:** <optional: one owner-brief sentence, where three entries share a reason> "
             "(same shape as D<a>, D<b>)")


def flat(text: str) -> str:
    return " ".join(text.split())


class LineWritersTest(FactoryTestCase):
    def test_e1_the_entry_shape_shows_both_lines_in_the_command_and_the_owner_brief(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "shape", "standard", "python")
            for text in ((repo / "commands/cruise.md").read_text(encoding="utf-8"),
                         (repo / ".specify/product-owner.md").read_text(encoding="utf-8")):
                lines = text.split("- **Confidence:**", 1)[1].splitlines()
                self.assertEqual(lines[1], LINE)
                self.assertEqual(lines[2], RULE_LINE)
                self.assertTrue(lines[3].startswith("- **Written to:**"), lines[3])

    def test_e2_the_skipper_brief_names_the_verb_the_escalation_and_the_proposal(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "skipper", "standard", "python")
            skipper = flat((repo / "agents/drive-skipper.md").read_text(encoding="utf-8"))
            for words in ("python3 scripts/reversibility.py", "--raise", "one tier at a time", "never lowers",
                          "Proposed rule:", "never edits", "evidence for the count, never binding"):
                self.assertIn(words, skipper)

    def test_e3_the_command_tells_the_host_to_run_the_verb_and_add_the_headings(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "command", "standard", "python")
            cruise = flat((repo / "commands/cruise.md").read_text(encoding="utf-8"))
            self.assertIn("runs `python3 scripts/reversibility.py` for every entry it writes", cruise)
            self.assertIn("with that entry's facts, `Scope:` and `Written to`", cruise)
            self.assertIn("each `D<n>` with its heading, Stage and Scope", cruise)
            self.assertIn("to every skipper brief", cruise)

    def test_e4_an_adopted_repository_carries_the_same_text_with_the_delivery_path(self) -> None:
        files = adopted([wrapped("shop", ".")])
        verb = "python3 delivery/scripts/reversibility.py"
        self.assertIn(LINE.replace("python3 scripts/reversibility.py", verb),
                      files["delivery/commands/cruise.md"])
        self.assertIn(f"runs `{verb}` for every entry it writes", flat(files["delivery/commands/cruise.md"]))
        self.assertIn(verb, flat(files["delivery/agents/drive-skipper.md"]))
