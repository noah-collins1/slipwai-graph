"""Every page that owns a stop with delegates says when each block is appended, and what a skipper's block names."""
from __future__ import annotations

import re
import subprocess
import tempfile

from support import FactoryTestCase
from test_agent_types import REGISTRY, projected
from test_result_contract_briefs import ADOPTED, SECTION, brief, command
from test_stage_models import installed

from slipwai.assets import ROOT
from slipwai.layout import AT_ROOT
from slipwai.project.agents import types


def flat(text: str) -> str:
    return " ".join(text.split())


class SkipperAnswerTest(FactoryTestCase):
    def test_the_cruise_text_puts_the_skippers_own_number_in_change_summary_never_in_decisions(self) -> None:
        for layout in (AT_ROOT, ADOPTED):
            text = flat(command("cruise", layout))
            with self.subTest(layout=layout.delivery):
                self.assertNotIn("the entry's `D<n>` in `decisions`", text)
                self.assertIn("own `D<n>` goes in the block's `change_summary` and never in `decisions`", text)
                self.assertIn("which lists only the standing entries the work relied on", text)

    def test_an_unavailable_answer_is_an_entry_in_the_protocol_and_in_the_skipper_brief(self) -> None:
        for layout in (AT_ROOT, ADOPTED):
            cruise = flat(command("cruise", layout))
            skipper = flat(brief("drive-skipper", layout))
            with self.subTest(layout=layout.delivery):
                self.assertIn("An `unavailable` answer is an entry too, appended at `Status: standing`", cruise)
                self.assertIn("a person overrides it as they override any entry", cruise)
                self.assertIn("An `unavailable` answer is still the entry", skipper)
                self.assertIn("Your own `D<n>` goes in `change_summary` and never in `decisions`", skipper)
                self.assertNotIn("`unavailable: <what a person must provide>`", skipper)


def section(text: str, heading: str) -> str:
    return text.split(heading, 1)[1].split("\n## ", 1)[0]


class StopsTest(FactoryTestCase):
    def test_the_adversary_page_appends_each_block_before_it_ends_the_benchmark_entry(self) -> None:
        for event in (False, True):
            for layout in (AT_ROOT, ADOPTED):
                where = f"{layout.delivery}/" if layout.moved else ""
                text = flat(command("adversary", layout, event))
                with self.subTest(event=event, layout=layout.delivery):
                    verb = f"python3 {where}scripts/check-decisions.py --hand-back specs/<feature>/slices/<id> "
                    self.assertIn(verb + "drive-adversary adversary", text)
                    self.assertIn(f"({where}docs/result-contract.md)", text)
                    self.assertLess(text.index(verb), text.rindex("end the `adversary` benchmark entry"))
                    self.assertIn("one continuation", text)

    def test_the_completion_audit_is_the_backstop_for_every_slices_record(self) -> None:
        for layout in (AT_ROOT, ADOPTED):
            where = f"{layout.delivery}/" if layout.moved else ""
            text = flat(section(command("cruise", layout), "## When the ready set is empty: the completion audit"))
            with self.subTest(layout=layout.delivery):
                self.assertIn("each audit `drive-gaps` delegate also runs "
                              f"`python3 {where}scripts/check-decisions.py --hand-backs` over every slice", text)
                self.assertIn("a delegated stage with neither a passing block nor a `Missing:` line is an audit "
                              "finding", text)
                self.assertIn(f"python3 {where}scripts/check-decisions.py --hand-back specs/<feature> drive-gaps audit",
                              text)
                self.assertLess(text.index("--hand-back specs/<feature> drive-gaps audit"),
                                text.index("Only an audit with nothing left to build ends with `cruise: done`"))

    def test_every_page_that_owns_a_stop_with_delegates_appends_before_it_closes_the_stage(self) -> None:
        for layout in (AT_ROOT, ADOPTED):
            pages = {
                "drive": section(command("drive", layout), "## What every delegate hands back"),
                "cruise": command("cruise", layout),
                "adversary": command("adversary", layout),
                "audit": section(command("cruise", layout), "## When the ready set is empty: the completion audit"),
            }
            for name, text in pages.items():
                with self.subTest(layout=layout.delivery, page=name):
                    self.assertIn("--hand-back ", text)
                    self.assertRegex(flat(text), r"before (it|you) (close|end)s? the|before the stage's benchmark "
                                                 r"entry closes|before ending the|before you end the|before the audit")

    def test_a_continuation_after_the_entry_closed_is_recorded_with_started(self) -> None:
        for layout in (AT_ROOT, ADOPTED):
            text = flat(section(command("drive", layout), "## What every delegate hands back"))
            with self.subTest(layout=layout.delivery):
                self.assertIn("A continuation recorded after the stage's benchmark entry has closed passes "
                              "`--started <instant>` to either verb, the instant the `--hand-backs` line names", text)
                self.assertIn("on time, the verb finds the open entry itself", text)


class OwnershipSentencesTest(FactoryTestCase):
    def test_the_stage_sentence_names_ready_set_as_the_one_stage_with_no_benchmark_entry(self) -> None:
        for layout in (AT_ROOT, ADOPTED):
            with self.subTest(layout=layout.delivery):
                drive = flat(section(command("drive", layout), "## What every delegate hands back"))
                self.assertIn("`ready-set` is the one stage with no benchmark entry", drive)
                slice_brief = flat(brief("drive-slice", layout))
                self.assertIn("`ready-set` is the one stage with no benchmark entry", slice_brief)

    def test_the_fragment_counts_a_stage_when_a_typed_delegate_that_belongs_to_it_ran(self) -> None:
        text = flat((ROOT / "changelog.d/result-contract.md").read_text(encoding="utf-8"))
        self.assertIn("how many stages a typed delegate that belongs to them ran handed back a block", text)
        self.assertNotIn("how many delegated stages", text)

    def test_the_fragment_carries_the_started_argument_the_catch_up_cut_off_and_the_skipper_correction(self) -> None:
        text = (ROOT / "changelog.d/result-contract.md").read_text(encoding="utf-8")
        self.assertEqual(text.splitlines()[0], "MINOR")
        lead, catch_up = flat(text).split("**Catch-up.**")
        for words in ("`--started <instant>`", "the instant the `--hand-backs` line names",
                      "a continuation that arrives after its stage's entry closed", "`unavailable` answer",
                      "`change_summary`", "a PATCH-level correction"):
            self.assertIn(words, lead)
        self.assertIn("Stages that ended before `hand_backs.py` first reached the project's history owe no block, "
                      "and `--hand-backs` and `make benchmark` say so instead of counting them", catch_up)

    def test_the_two_links_in_every_brief_are_root_relative_the_same_way(self) -> None:
        """Both name a project-root path, spelled out in the link text; neither is relative to `agents/`."""
        for layout in (AT_ROOT, ADOPTED):
            where = f"{layout.delivery}/" if layout.moved else ""
            for agent in types():
                with self.subTest(layout=layout.delivery, agent=agent.name):
                    links = re.findall(r"\[([^\]]*)\]\(([^)]*)\)", brief(agent.name, layout))
                    for page in ("result-contract.md", "delegated-agent-safety.md"):
                        self.assertIn((f"{where}docs/{page}", f"{where}docs/{page}"), links)


class EveryHarnessProjectionTest(FactoryTestCase):
    def test_every_harness_with_an_agent_file_row_carries_the_paragraph(self) -> None:
        keys = [each["key"] for each in REGISTRY if each["agentFile"]]
        self.assertEqual(sorted(keys), ["claude", "codex", "copilot", "cursor-agent", "gemini", "opencode"])
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "projected", "standard", "python")
            installed(repo, *keys)
            subprocess.run(["python3", "-B", "scripts/agents/project.py"], cwd=repo, check=True, capture_output=True)
            for key in keys:
                for agent in types():
                    text = projected(repo, key, agent.name)
                    with self.subTest(harness=key, agent=agent.name):
                        self.assertIn(SECTION.removeprefix("## "), text)
                        self.assertIn(f"`delegate` is `{agent.name}`", text)
                        self.assertIn("(docs/result-contract.md)", text)
