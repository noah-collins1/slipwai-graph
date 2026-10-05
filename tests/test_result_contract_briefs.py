"""Every delegate's brief ends its hand-back with the result-contract block; the drive ladder says who records it."""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile

from support import FactoryTestCase
from test_agent_types import projected
from test_stage_models import installed

from slipwai.assets import TOOLKIT_ROOT
from slipwai.layout import AT_ROOT, Layout
from slipwai.project.agents import agent_file, types

ADOPTED = Layout(delivery="delivery")
SECTION = "## What you hand back"
SLICE_RECORD = "specs/<feature>/slices/<id>/hand-backs.md"


def hand_backs():
    """The script's own tables, read by path with bytecode off so no `__pycache__` is left under `assets/`."""
    kept, sys.dont_write_bytecode = sys.dont_write_bytecode, True
    try:
        spec = importlib.util.spec_from_file_location("hand_backs_under_test", TOOLKIT_ROOT / "scripts/hand_backs.py")
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.dont_write_bytecode = kept


def brief(name: str, layout: Layout) -> str:
    """One agent file as a project at `layout` carries it: assembled, then placed and re-pointed."""
    agent = next(each for each in types() if each.name == name)
    path = f"agents/{name}.md"
    return next(iter(layout.relocate({path: agent_file(agent, layout)}).values()))


def handed_back(text: str) -> str:
    """The shared paragraph, from its heading to the next one."""
    return text.split(SECTION, 1)[1].split("\n## ", 1)[0]


class BriefsTest(FactoryTestCase):
    def test_each_type_ends_with_the_block_pointing_at_its_page_and_spelling_its_own_statuses(self) -> None:
        statuses = hand_backs().STATUSES
        self.assertEqual(sorted(each.name for each in types()), sorted(statuses))
        for layout, page in ((AT_ROOT, "docs/result-contract.md"), (ADOPTED, "delivery/docs/result-contract.md")):
            for agent in types():
                with self.subTest(layout=layout.delivery, agent=agent.name):
                    text = brief(agent.name, layout)
                    self.assertIn(SECTION, text)
                    paragraph = handed_back(text)
                    self.assertIn("one fenced block whose info string is exactly `result-contract`", paragraph)
                    self.assertIn(f"({page})", paragraph)
                    bare = r"(?<![\w/])docs/result-contract\.md" if layout.moved else r"delivery/"
                    self.assertNotRegex(paragraph, bare)
                    self.assertIn(f"`delegate` is `{agent.name}`", paragraph)
                    own = statuses[agent.name]
                    for status in own:
                        self.assertIn(f"`{status}`", paragraph)
                    elsewhere = {each for kind in statuses.values() for each in kind} - set(own)
                    self.assertEqual([each for each in elsewhere if f"`{each}`" in paragraph], [])
                    self.assertLess(text.index(SECTION), text.index("## What holds for every delegate here"))

    def test_the_claude_codex_and_gemini_projections_carry_the_paragraph(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "projected", "standard", "python")
            installed(repo, "claude", "codex", "gemini")
            subprocess.run(["python3", "-B", "scripts/agents/project.py"], cwd=repo, check=True, capture_output=True)
            for key in ("claude", "codex", "gemini"):
                for agent in types():
                    text = projected(repo, key, agent.name)
                    with self.subTest(harness=key, agent=agent.name):
                        self.assertIn(SECTION, text)
                        self.assertIn(f"`delegate` is `{agent.name}`", text)
                        self.assertIn("(docs/result-contract.md)", text)

    def test_the_bosun_and_hands_return_words_are_their_blocks_status(self) -> None:
        for layout in (AT_ROOT, ADOPTED):
            bosun = brief("drive-bosun", layout)
            hand = brief("drive-hand", layout)
            skipper = brief("drive-skipper", layout)
            with self.subTest(layout=layout.delivery):
                self.assertIn("`status` is `unblocked`, `catastrophic` or `cannot`", bosun)
                self.assertNotRegex(bosun, r"Return `unblocked:|answer `catastrophic:|is `cannot: ")
                self.assertIn("`accepted`, `behaviour` and `implementation` are the `status` of your", hand)
                self.assertNotIn("Return the verdict, the examples", hand)
                self.assertIn("the entry first, then any ADR, then the `result-contract` block last", skipper)
                self.assertNotIn("`unavailable: <what a person must provide>`", skipper)
                self.assertNotIn("Return the gaps and nothing else", brief("drive-gaps", layout))

    def test_the_slice_delegate_records_its_sub_delegates_and_hands_its_own_block_to_the_feature(self) -> None:
        for layout in (AT_ROOT, ADOPTED):
            text = brief("drive-slice", layout)
            with self.subTest(layout=layout.delivery):
                self.assertIn(SLICE_RECORD, text)
                where = f"{layout.delivery}/" if layout.moved else ""
                self.assertIn(f"{where}scripts/check-decisions.py --hand-back", text)
                self.assertIn("`specs/<feature>/hand-backs.md`, stage `ready-set`", text)
        for agent in types():
            if agent.name != "drive-slice":
                self.assertNotIn(SLICE_RECORD, brief(agent.name, AT_ROOT), agent.name)
