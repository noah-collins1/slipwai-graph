"""`strategy.before` follows the map as a refresh leaves it (S21 R5; brownfield adoption, experimental).

The record's `before` named a prerequisite from the tree's reading even where a person had recorded the row above
it. It now reads the rows after reconciliation, so the strategy page and the map never disagree. The holds guard
what must not move with it: a row left at the tree's rung keeps its entry, and nothing but `before` changes.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from support import FactoryTestCase
from test_adopt import node_repository, slipwai
from test_candidates import commit, record

PIPELINE = "a pipeline that deploys on a passing `verify`"
SUITE = "a green suite in the gate"
ROLES = "every application's role recorded"
PAGE = "delivery/docs/change-strategy.md"
DERIVED = ("recommended", "because", "decided", "finished", "programme")


def adopted(parent: Path) -> Path:
    """A Node service whose tree reads Safety net `tests-exist`, Path to production `unknown`, Structure `as-found`."""
    repo = node_repository(parent)
    result = slipwai(repo, "adopt", "--yes", "--no-init")
    assert result.returncode == 0, result.stderr
    return repo


def recorded(repo: Path, axis: str, rung: str) -> None:
    """A person's answer, committed: the row carries `rung` as `confirmed`."""
    document = json.loads((repo / "project.json").read_text())
    for row in document["convergence"]:
        if row["axis"] == axis:
            row.update(rung=rung, provenance="confirmed")
    (repo / "project.json").write_text(json.dumps(document, indent=2) + "\n")
    commit(repo)


def refresh(repo: Path) -> None:
    result = slipwai(repo, "adopt", "--refresh")
    assert result.returncode == 0, result.stderr


def leads(repo: Path, entry: str) -> tuple[bool, bool]:
    """Whether `project.json` `strategy.before` and the strategy page each carry `entry`."""
    return (any(entry in line for line in record(repo)["strategy"]["before"]),
            entry in (repo / PAGE).read_text())


class RefreshStrategyTest(FactoryTestCase):
    def gone(self, axis: str, rung: str, entry: str) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = adopted(Path(directory))
            self.assertEqual(leads(repo, entry), (True, True), "the tree's reading names it before")
            recorded(repo, axis, rung)
            refresh(repo)
            self.assertEqual(leads(repo, entry), (False, False))

    def test_a_safety_net_a_person_recorded_at_tests_pass_is_not_named_a_prerequisite(self) -> None:
        self.gone("safety-net", "tests-pass", SUITE)

    def test_a_path_to_production_recorded_above_scripted_is_not_named_a_prerequisite(self) -> None:
        self.gone("path-to-production", "pipeline", PIPELINE)

    def test_a_structure_recorded_above_as_found_is_not_named_a_prerequisite(self) -> None:
        self.gone("structure", "named", ROLES)

    def test_a_row_left_at_the_rung_the_tree_reads_keeps_its_entry(self) -> None:
        """A hold: today's behaviour, green before the change."""
        with tempfile.TemporaryDirectory() as directory:
            repo = adopted(Path(directory))
            recorded(repo, "safety-net", "tests-exist")
            refresh(repo)
            for entry in (SUITE, PIPELINE, ROLES):
                self.assertEqual(leads(repo, entry), (True, True), entry)

    def test_only_before_changes_and_a_second_refresh_leaves_the_record_still(self) -> None:
        """A hold: the other fields are derived as today, and the record is still between surveys."""
        with tempfile.TemporaryDirectory() as directory:
            repo = adopted(Path(directory))
            first = record(repo)["strategy"]
            recorded(repo, "safety-net", "tests-pass")
            refresh(repo)
            second = record(repo)["strategy"]
            for key in DERIVED:
                self.assertEqual(second[key], first[key], key)
            commit(repo)
            settled = (repo / "project.json").read_text(), (repo / PAGE).read_text()
            refresh(repo)
            self.assertEqual(((repo / "project.json").read_text(), (repo / PAGE).read_text()), settled)
