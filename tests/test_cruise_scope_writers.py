"""The writers of a decision's `Scope:` line (S02, D60): the entry's shape, the two briefs, the command.

Each example reads a generated project's files, because those are what a run reads; the verb the texts point at
(`check-decisions.py --scope`) is another test's, and none of these runs it. An owner brief an earlier factory
seeded is the project's (D24): the one hold here is that `migrate` leaves it as it stood.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from support import FactoryTestCase, commit_all
from test_drive_adoption import adopted, wrapped
from test_migrate import migrate
from test_replay import git, newer_factory

from slipwai.project.cruise_agents import DECISIONS, OWNER_BRIEF

SHAPE = "- **Scope:** <slice ids, comma-separated> | global"
VERB = "python3 scripts/check-decisions.py --scope <slice-id>"


def lines_after(text: str, marker: str) -> list[str]:
    return text.split(marker, 1)[1].splitlines()


class ScopeWritersTest(FactoryTestCase):
    def test_the_entry_shape_shows_the_scope_line_after_the_stage_line_in_the_command_and_the_brief(self) -> None:
        """e64: both places a person or a run reads the shape from."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "shape", "standard", "python")
            for text in ((repo / "commands/cruise.md").read_text(), (repo / OWNER_BRIEF).read_text()):
                after = lines_after(text, "- **Stage:** <stage> · **Slice:** <id>")
                self.assertTrue(after[1].startswith(SHAPE), after[1])
                self.assertIn("`global`", after[1])
                self.assertIn("feature-level or doubtful", after[1])
        entry = adopted([wrapped("shop", ".")])["delivery/commands/cruise.md"]
        self.assertIn(SHAPE, entry)

    def test_the_skipper_reads_the_standing_entries_for_its_slice_through_the_verb(self) -> None:
        """e65: the verb for a slice, the whole log where the brief names none, and the line on the entry back."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "skipper", "standard", "python")
            skipper = (repo / "agents/drive-skipper.md").read_text()
            flat = " ".join(skipper.split())
            self.assertIn(f"`{VERB}`", flat)
            self.assertIn(f"every standing entry in `{DECISIONS}` where the brief names no slice", flat)
            self.assertIn("with its `Scope:` line", flat)

    def test_the_bosun_reads_through_the_verb_and_every_entry_it_writes_carries_a_scope_line(self) -> None:
        """e66."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "bosun", "standard", "python")
            bosun = (repo / "agents/drive-bosun.md").read_text()
            flat = " ".join(bosun.split())
            self.assertIn(f"`{VERB}`", flat)
            self.assertIn(f"every standing entry in `{DECISIONS}` where the brief names no slice", flat)
            self.assertIn("every entry you write carries a `Scope:` line", flat)

    def test_the_command_points_at_the_verb_for_a_slice_and_keeps_every_entry_for_a_feature_one(self) -> None:
        """e67: the iteration-start text and *Deciding*."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "command", "standard", "python")
            cruise = (repo / "commands/cruise.md").read_text()
            start = cruise.split("this is an iteration:")[1].split("Where `.codegraph/`")[0]
            deciding = cruise.split("## Deciding: the skipper protocol")[1].split("The entry's shape")[0]
            for part in (start, deciding):
                flat = " ".join(part.split())
                self.assertIn(f"`{VERB}`", flat)
                self.assertIn("every standing entry", flat)
                self.assertIn("feature-level", flat)

    def test_hold_migrate_leaves_an_owner_brief_an_earlier_factory_seeded_as_it_stood(self) -> None:
        """e68, a hold (D24): the brief is the project's. Teeth: let the seeding rewrite an existing brief and the
        bytes below change."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "seeded", "standard", "python")
            brief = repo / OWNER_BRIEF
            earlier = "".join(line for line in brief.read_text().splitlines(True) if "**Scope:**" not in line)
            earlier += "\n## Taste\n\nSmall, boring, mine.\n"
            brief.write_text(earlier)
            commit_all(repo, "An owner brief an earlier factory seeded")
            factory = newer_factory(Path(directory), "\n## Added\n")

            result = migrate(repo, factory)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(brief.read_text(), earlier)
            self.assertEqual(git(repo, "status", "--porcelain").stdout, "")
