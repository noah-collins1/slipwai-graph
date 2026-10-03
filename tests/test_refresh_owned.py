"""A refresh leaves the four files the project owns where it has them (S21; brownfield adoption, experimental).

`.specify/cruise.json`, `product-owner.md`, `models.json` and `drive.json` are seeded by the factory and then
changed by the project. A refresh wrote each back to the factory's default; it now writes one only where it is
absent. The holds beside the examples guard what must not change with it: a missing one is still written, the
pages the record drives still follow it, and `.written` still lists all four.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from support import FactoryTestCase
from test_adopt import slipwai
from test_candidates import adopted, commit, record
from test_replay import git

CRUISE, OWNER = ".specify/cruise.json", ".specify/product-owner.md"
MODELS, DRIVE = ".specify/models.json", ".specify/drive.json"
FOUR = (CRUISE, OWNER, MODELS, DRIVE)


def settings(repo: Path, name: str) -> str:
    """The project's own version of a seeded file, written and committed: not the factory's default."""
    path = repo / name
    if name.endswith(".json"):
        path.write_text(json.dumps({**json.loads(path.read_text()), "mine": 10}, indent=2, ensure_ascii=False) + "\n")
    else:
        path.write_text(path.read_text() + "\n## Taste\n\nSmall, boring, mine.\n")
    commit(repo)
    return path.read_text()


class RefreshKeepsOwnedTest(FactoryTestCase):
    def kept(self, repo: Path, *step: str) -> None:
        """Run `step` and check every committed edit stands: same bytes, not in `git status`, not counted."""
        before = {name: (repo / name).read_text() for name in FOUR}
        result = slipwai(repo, "adopt", *step)
        self.assertEqual(result.returncode, 0, result.stderr)
        for name in FOUR:
            self.assertEqual((repo / name).read_text(), before[name], f"{name} bytes")
            self.assertNotIn(name, git(repo, "status", "--porcelain").stdout, f"{name} in git status")
            self.assertNotIn(f"`{name}`", result.stdout, f"{name} reported")

    def one(self, name: str) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = adopted(Path(directory))
            settings(repo, name)
            self.kept(repo, "--refresh")

    def test_a_committed_cruise_json_is_left_as_it_is(self) -> None:
        self.one(CRUISE)

    def test_a_filled_in_owner_brief_is_left_as_it_is(self) -> None:
        self.one(OWNER)

    def test_a_models_json_that_is_not_the_default_is_left_as_it_is(self) -> None:
        self.one(MODELS)

    def test_a_drive_json_that_is_not_the_default_is_left_as_it_is(self) -> None:
        self.one(DRIVE)

    def test_a_confirm_leaves_all_four_as_they_are(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = adopted(Path(directory))
            for name in FOUR:
                settings(repo, name)
            self.kept(repo, "--confirm", "shop")

    def test_a_refresh_counts_none_of_the_four_among_the_files_it_rewrote(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = adopted(Path(directory))
            for name in FOUR:
                settings(repo, name)
            self.assertIn("\n0 file(s) rewritten", slipwai(repo, "adopt", "--refresh").stdout)


class HeldTest(FactoryTestCase):
    """Today's behaviour, green on arrival and green after: the edit must not skip more than the four present."""

    def missing(self, name: str) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = adopted(Path(directory))
            default = (repo / name).read_text()
            (repo / name).unlink()
            commit(repo)
            result = slipwai(repo, "adopt", "--refresh")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((repo / name).read_text(), default)
            self.assertIn(name, git(repo, "status", "--porcelain").stdout)

    def test_a_missing_cruise_json_is_written_with_the_default(self) -> None:
        self.missing(CRUISE)

    def test_a_missing_owner_brief_is_written_with_the_default(self) -> None:
        self.missing(OWNER)

    def test_a_row_moved_by_hand_reaches_the_convergence_page(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = adopted(Path(directory))
            page = repo / "delivery/docs/convergence.md"
            document = record(repo)
            document["convergence"][0] = {**document["convergence"][0], "provenance": "confirmed",
                                          "planned": "moved by hand, S21"}
            (repo / "project.json").write_text(json.dumps(document, indent=2) + "\n")
            self.assertEqual(slipwai(repo, "adopt", "--refresh").returncode, 0)
            self.assertIn("moved by hand, S21", page.read_text())

    def test_written_lists_the_four_and_the_report_names_no_owned_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = adopted(Path(directory))
            for name in FOUR:
                settings(repo, name)
            result = slipwai(repo, "adopt", "--refresh")
            listed = (repo / "delivery/.written").read_text().split()
            for name in FOUR:
                self.assertIn(name, listed)
            self.assertNotIn("owned:", result.stdout)


class UncommittedTest(FactoryTestCase):
    """The refusal protects what a run writes; it no longer lists the four a refresh leaves where they are (R3)."""

    def test_an_uncommitted_edit_to_a_seeded_file_is_not_refused_and_stands(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = adopted(Path(directory))
            path = repo / CRUISE
            path.write_text(json.dumps({**json.loads(path.read_text()), "mine": 10}, indent=2) + "\n")
            edited = path.read_text()
            result = slipwai(repo, "adopt", "--refresh")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(path.read_text(), edited)

    def test_an_uncommitted_hand_edit_to_the_convergence_page_is_still_refused_by_name(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = adopted(Path(directory))
            self.assertEqual(slipwai(repo, "adopt", "--confirm", "shop").returncode, 0)
            page = repo / "delivery/docs/convergence.md"
            page.write_text(page.read_text() + "\nA note of mine.\n")
            refused = slipwai(repo, "adopt", "--refresh")
            self.assertEqual(refused.returncode, 2)
            self.assertIn("`delivery/docs/convergence.md`", refused.stderr)

    def test_an_uncommitted_deletion_of_a_seeded_file_is_still_refused_by_name(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = adopted(Path(directory))
            self.assertEqual(slipwai(repo, "adopt", "--confirm", "shop").returncode, 0)
            (repo / CRUISE).unlink()
            refused = slipwai(repo, "adopt", "--refresh")
            self.assertEqual(refused.returncode, 2)
            self.assertIn(f"`{CRUISE}`", refused.stderr)
            self.assertFalse((repo / CRUISE).exists(), "and nothing was written")
