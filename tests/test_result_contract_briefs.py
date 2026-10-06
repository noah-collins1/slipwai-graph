"""Every delegate's brief ends its hand-back with the result-contract block; the drive ladder says who records it."""
from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
import tempfile

from support import FactoryTestCase
from test_agent_types import projected
from test_stage_models import installed

from slipwai.assets import TOOLKIT_ROOT
from slipwai.layout import AT_ROOT, Layout
from slipwai.project import result_contract
from slipwai.project.agents import agent_file, types
from slipwai.project.commands import command_files
from slipwai.project.docs_index import docs_index

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

    def test_each_type_says_the_helpers_it_starts_get_no_block_and_report_inside_its_own(self) -> None:
        for layout in (AT_ROOT, ADOPTED):
            for agent in types():
                with self.subTest(layout=layout.delivery, agent=agent.name):
                    paragraph = " ".join(handed_back(brief(agent.name, layout)).split())
                    self.assertIn("Helpers you start (Explore, general-purpose, a fan-out group) get no block and "
                                  "no entry of their own", paragraph)
                    self.assertIn("what they did is reported in your own block", paragraph)

    def test_the_implement_brief_fan_out_text_says_the_groups_report_inside_the_one_block(self) -> None:
        for layout in (AT_ROOT, ADOPTED):
            text = " ".join(brief("drive-implement", layout).split())
            with self.subTest(layout=layout.delivery):
                fan = text.split("**You may fan your own increment out**", 1)[1].split("Return what you finished", 1)[0]
                self.assertIn("get no `result-contract` block and no entry of their own", fan)
                self.assertIn("one block", fan)

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


def command(name: str, layout: Layout, event: bool = False) -> str:
    """One generated command as a project at `layout` carries it."""
    files = layout.relocate(command_files(event, [], "none", layout, None))
    return files[layout.place(f"commands/{name}.md")]


class LadderTest(FactoryTestCase):
    def test_the_drive_ladder_says_who_appends_each_block_and_what_a_missing_one_costs(self) -> None:
        for event in (False, True):
            for layout in (AT_ROOT, ADOPTED):
                where = f"{layout.delivery}/" if layout.moved else ""
                text = command("drive", layout, event)
                with self.subTest(event=event, layout=layout.delivery):
                    heading = "## What every delegate hands back"
                    self.assertEqual(text.count(heading), 1)
                    self.assertLess(text.index("## Who runs each stage"), text.index(heading))
                    self.assertLess(text.index(heading), text.index("## What each stage costs"))
                    section = text.split(heading, 1)[1].split("\n## ", 1)[0]
                    check = f"python3 {where}scripts/check-decisions.py"
                    for words in (
                        f"{check} --hand-back <dir> <type> <stage>",
                        f"{check} --hand-back-missing <dir> <type> <stage> <reason>",
                        f"{check} --hand-backs specs/<feature>/slices/<id>", "`specs/<feature>/slices/<id>`",
                        "`specs/<feature>`", "`ready-set`", "before it closes the stage's benchmark entry",
                        "one continuation", "`refused: <the first line of the delegate's words>`", "`malformed: <field>`",
                        "`no continuation`", "`stopped: <reason>`", "never re-run", "never writes a block",
                        "A stage run in this context has no delegate, so it has no entry",
                        "Before the hand, at the demo stop", "at the adversary stop",
                        "never re-opens converge",
                    ):
                        self.assertIn(words, section)
                    if layout.moved:
                        self.assertNotRegex(section, r"(?<![\w/])(scripts|docs)/")

    def test_the_convergence_rung_and_the_converge_brief_read_the_record_by_stage(self) -> None:
        for layout in (AT_ROOT, ADOPTED):
            where = f"{layout.delivery}/" if layout.moved else ""
            drive = command("drive", layout)
            rung = drive.split("**Convergence**", 1)[1].split("**Demo**", 1)[0]
            converge = brief("drive-converge", layout)
            with self.subTest(layout=layout.delivery):
                lines = [each for each in rung.splitlines() if "--hand-backs" in each]
                self.assertTrue(lines and all(each.startswith("   ") for each in lines), lines)
                self.assertIn(f"{where}scripts/check-decisions.py --hand-backs", rung)
                for text in (rung, converge):
                    self.assertIn("`--hand-backs`", text.replace("check-decisions.py --hand-backs", "`--hand-backs`"))
                    self.assertIn("without a passing `result-contract` block is a finding", text)
                    self.assertIn("naming the stage and the delegate type", text)
                    self.assertIn("`MEDIUM`", text.split("--hand-backs", 1)[1])
                self.assertLess(converge.index("Account for every level"), converge.index("--hand-backs"))
                self.assertLess(converge.index("--hand-backs"), converge.index("Where you prove a finding"))

    def test_the_cruise_command_records_every_skipper_hand_and_bosun_dispatch_the_same_way(self) -> None:
        for layout in (AT_ROOT, ADOPTED):
            where = f"{layout.delivery}/" if layout.moved else ""
            text = command("cruise", layout)
            with self.subTest(layout=layout.delivery):
                self.assertEqual(text.count("Every skipper, hand and bosun dispatch is recorded the same way"), 1)
                sentence = text.split("Every skipper, hand and bosun dispatch is recorded the same way", 1)[1]
                sentence = sentence.split("\n\n", 1)[0]
                for words in (
                    f"({where}docs/result-contract.md)", "`specs/<feature>/decisions.md`", "drive-skipper",
                    f"{where}scripts/check-decisions.py --hand-back <dir>", "What every delegate hands back",
                ):
                    self.assertIn(words, sentence)


    def test_every_reader_of_the_delegation_says_what_owes_a_block_and_which_word_is_the_stage(self) -> None:
        owes = "owes a block only when a typed `drive-*` delegate that belongs to the stage ran"
        stage = "`<stage>` is the name of the stage's open benchmark entry"
        for layout in (AT_ROOT, ADOPTED):
            with self.subTest(layout=layout.delivery):
                section = command("drive", layout).split("## What every delegate hands back", 1)[1]
                section = section.split("\n## ", 1)[0]
                rung = command("drive", layout).split("**Convergence**", 1)[1].split("**Demo**", 1)[0]
                for text in (section, " ".join(rung.split()), " ".join(brief("drive-converge", layout).split())):
                    self.assertIn(owes, " ".join(text.split()))
                self.assertIn("untyped helpers", section)
                self.assertIn(stage, section)
                self.assertIn("open benchmark entry", " ".join(command("cruise", layout).split()))
                self.assertIn("open benchmark entry", " ".join(brief("drive-slice", layout).split()))


PAGE = TOOLKIT_ROOT / "docs/result-contract.md"


def rows(section: str) -> list[list[str]]:
    """The cells of each table row under the page's `## <section>` heading, header and rule lines left out."""
    body = PAGE.read_text(encoding="utf-8").split(f"\n## {section}", 1)[-1].split("\n## ", 1)[0]
    table = [line for line in body.splitlines() if line.startswith("| `")]
    return [[cell.strip() for cell in line.strip().strip("|").split("|")] for line in table]


class PageTest(FactoryTestCase):
    def test_the_pages_field_table_is_the_scripts_thirteen_fields_in_order(self) -> None:
        fields = hand_backs().FIELDS
        self.assertEqual(len(fields), 13)
        self.assertEqual([(cell[0].strip("`"), cell[1]) for cell in rows("The fields")], list(fields))
        self.assertTrue(all(cell[2] for cell in rows("The fields")), "every field carries its rule")

    def test_the_pages_status_table_and_the_factorys_copy_are_the_scripts_statuses(self) -> None:
        statuses = hand_backs().STATUSES
        page = {cell[0].strip("`"): tuple(re.findall(r"`([a-z-]+)`", cell[1])) for cell in rows("Status, per type")}
        self.assertEqual(page, statuses)
        self.assertEqual(result_contract.STATUSES, statuses)

    def test_the_page_names_the_heading_the_missing_forms_and_the_three_verbs(self) -> None:
        text = PAGE.read_text(encoding="utf-8")
        for words in (
            "## <UTC time> — drive-<name> — <stage>", "- **Missing:** <reason>", "`refused: <the delegate's words>`",
            "`malformed: <field>`", "`no continuation`", "`stopped: <reason>`", "specs/<feature>/hand-backs.md",
            "scripts/check-decisions.py --hand-back <dir> <type> <stage>",
            "scripts/check-decisions.py --hand-back-missing <dir> <type> <stage> <reason>",
            "scripts/check-decisions.py --hand-backs <slice-dir>", "```result-contract",
        ):
            self.assertIn(words, text)

    def test_the_page_says_helpers_get_no_block_of_their_own(self) -> None:
        record = PAGE.read_text(encoding="utf-8").split("\n## The record", 1)[1].split("\n## The verbs", 1)[0]
        text = " ".join(record.split())
        for words in ("Helpers a delegate starts", "get no block and no entry of their own",
                      "reported in the delegate's own block"):
            self.assertIn(words, text)

    def test_the_page_says_what_owes_a_block_and_what_the_finding_line_names(self) -> None:
        text = " ".join(PAGE.read_text(encoding="utf-8").split())
        for words in ("owes a block only when a typed `drive-*` delegate that belongs to the stage ran",
                      "untyped helpers", "`drive-slice`", "the stage and the type(s)", "a finding for converge",
                      "the name of the stage's open benchmark entry"):
            self.assertIn(words, text)

    def test_the_docs_index_lists_the_page_under_a_heading_of_its_own_kind(self) -> None:
        index = docs_index({"docs/result-contract.md": PAGE.read_text(encoding="utf-8")})
        self.assertNotIn("## Also here", index)
        self.assertIn("- [`result-contract.md`](result-contract.md) — ", index)
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "indexed", "standard", "python")
            listed = (repo / "docs/README.md").read_text(encoding="utf-8")
            self.assertIn("[`result-contract.md`](result-contract.md) — ", listed)
            self.assertNotIn("## Also here", listed)
