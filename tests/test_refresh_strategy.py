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
from test_adopt import OWN, node_repository, repository, slipwai
from test_candidates import commit, record
from test_platform import POM

PIPELINE = "a pipeline that deploys on a passing `verify`"
SUITE = "a green suite in the gate"
ROLES = "every application's role recorded"
PAGE = "delivery/docs/change-strategy.md"
PLATFORM = "the platform in support — "
SEAM = "a seam requests enter through"
PINNED = "`/characterise` pinning each seam"
WHY = "split it so teams can move"
DERIVED = ("recommended", "because", "decided", "finished", "programme")
UNKNOWN = "the path to production is `unknown`"


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

    def test_a_row_a_person_overrode_above_the_rung_is_not_named_a_prerequisite(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = adopted(Path(directory))
            document = record(repo)
            for row in document["convergence"]:
                if row["axis"] == "safety-net":
                    row.update(rung="tests-pass", provenance="overridden")
            (repo / "project.json").write_text(json.dumps(document, indent=2) + "\n")
            commit(repo)
            refresh(repo)
            self.assertEqual(leads(repo, SUITE), (False, False))

    def test_a_safety_net_recorded_at_none_keeps_its_entry_and_names_none(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = adopted(Path(directory))
            recorded(repo, "safety-net", "none")
            refresh(repo)
            self.assertEqual(leads(repo, "the safety net is `none`"), (True, True))
            self.assertEqual(leads(repo, "the safety net is `tests-exist`"), (False, False))

    def test_a_path_to_production_recorded_at_manual_keeps_its_entry_and_names_manual(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = adopted(Path(directory))
            self.assertEqual(leads(repo, UNKNOWN), (True, True))
            recorded(repo, "path-to-production", "manual")
            refresh(repo)
            self.assertEqual(leads(repo, "the path to production is `manual`"), (True, True))
            self.assertEqual(leads(repo, UNKNOWN), (False, False))

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
            self.assertEqual({k: v for k, v in second.items() if k != "before"},
                             {k: v for k, v in first.items() if k != "before"}, "every key but `before`")
            commit(repo)
            settled = (repo / "project.json").read_text(), (repo / PAGE).read_text()
            refresh(repo)
            self.assertEqual(((repo / "project.json").read_text(), (repo / PAGE).read_text()), settled)


def released(parent: Path, path: str) -> Path:
    """`node_repository` adopted with `--release <path>`: the row and the `release` record are a person's answer."""
    repo = node_repository(parent)
    result = slipwai(repo, "adopt", "--yes", "--no-init", "--release", path)
    assert result.returncode == 0, result.stderr
    return repo


def release_path(repo: Path, path: str) -> None:
    """A person edits `release.path` in `project.json` and commits."""
    document = record(repo)
    document["release"]["path"] = path
    (repo / "project.json").write_text(json.dumps(document, indent=2) + "\n")
    commit(repo)


def path_row(repo: Path) -> dict:
    return next(r for r in record(repo)["convergence"] if r["axis"] == "path-to-production")


def refreshed_out(repo: Path) -> str:
    result = slipwai(repo, "adopt", "--refresh")
    assert result.returncode == 0, result.stderr
    return result.stdout


def maven(parent: Path, why: str | None) -> Path:
    """A Maven service on Spring 3.2.8 and JUnit 3, past end of life, adopted (with `why` when there is one): the
    tree reads Safety net `tests-exist`, so `before` carries the platform, the delivery rungs and, for a trigger
    that names a capability, the strangler fig's own two entries."""
    repo = repository(parent, "shop", {**OWN, "pom.xml": POM, "src/main/java/App.java": "class App {}\n"})
    result = slipwai(repo, "adopt", "--yes", "--no-init", *(["--why", why] if why else []))
    assert result.returncode == 0, result.stderr
    return repo


class PersonLowersReleasePathTest(FactoryTestCase):
    """AC-S21-12 (D28): a person's Path to production row above what a `release` record they answered allows follows
    that record down at a refresh; every other row of theirs stands."""

    def lowered(self, rung: str, adopted_at: str = "pipeline") -> tuple[Path, str]:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        repo = released(Path(directory.name), adopted_at)
        self.assertEqual((path_row(repo)["rung"], path_row(repo)["provenance"]), (adopted_at, "overridden"))
        release_path(repo, rung)
        return repo, refreshed_out(repo)

    def test_a_release_path_lowered_below_the_row_moves_the_row_and_names_the_prerequisite(self) -> None:
        repo, out = self.lowered("manual")
        row = path_row(repo)
        self.assertEqual((row["rung"], row["provenance"]), ("manual", "overridden"))
        self.assertIn("convergence: path-to-production refreshed from `pipeline` to `manual`", out)
        self.assertIn("release.path", out)
        self.assertEqual(leads(repo, "the path to production is `manual`"), (True, True))
        self.assertEqual(leads(repo, PIPELINE), (True, True), "the pipeline is a prerequisite again")
        self.assertIn("manual", (repo / "delivery/docs/convergence.md").read_text())

    def test_the_sweep_every_lower_rung_the_record_can_name_under_every_rung_above_it(self) -> None:
        for above in ("pipeline", "one-path", "pipeline-decides"):
            for below in ("unknown", "manual", "scripted"):
                with self.subTest(row=above, release=below):
                    directory = tempfile.TemporaryDirectory()
                    self.addCleanup(directory.cleanup)
                    repo = released(Path(directory.name), "pipeline")
                    document = record(repo)
                    for r in document["convergence"]:
                        if r["axis"] == "path-to-production":
                            r.update(rung=above, planned="S9-next")
                    document["release"]["path"] = below
                    (repo / "project.json").write_text(json.dumps(document, indent=2) + "\n")
                    commit(repo)
                    out = refreshed_out(repo)
                    row = path_row(repo)
                    self.assertEqual((row["rung"], row["provenance"], row["planned"]), (below, "overridden", "S9-next"))
                    self.assertIn(f"refreshed from `{above}` to `{below}`", out)
                    self.assertEqual(leads(repo, f"the path to production is `{below}`"), (True, True))
                    commit(repo)
                    settled = (repo / "project.json").read_text()
                    self.assertNotIn("path-to-production refreshed", refreshed_out(repo))
                    self.assertEqual((repo / "project.json").read_text(), settled)

    def test_a_row_at_or_below_the_record_stands_and_its_entry_is_still_named(self) -> None:
        """A hold: adopted `--release manual`, later `release.path: pipeline`."""
        repo, out = self.lowered("pipeline", "manual")
        self.assertEqual((path_row(repo)["rung"], path_row(repo)["provenance"]), ("manual", "overridden"))
        self.assertNotIn("path-to-production refreshed", out)
        self.assertEqual(leads(repo, "the path to production is `manual`"), (True, True))

    def test_a_row_at_one_path_over_release_path_pipeline_stands_with_no_entry(self) -> None:
        """A hold: `release.path` cannot spell `one-path`."""
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        repo = released(Path(directory.name), "pipeline")
        recorded(repo, "path-to-production", "one-path")
        out = refreshed_out(repo)
        self.assertEqual(path_row(repo)["rung"], "one-path")
        self.assertNotIn("path-to-production refreshed", out)
        self.assertEqual(leads(repo, "the path to production is"), (False, False))

    def test_a_row_over_a_detected_release_record_stands(self) -> None:
        """A hold: a `release` record nobody answered is not a person's newer word."""
        with tempfile.TemporaryDirectory() as directory:
            repo = adopted(Path(directory))
            recorded(repo, "path-to-production", "pipeline")
            out = refreshed_out(repo)
            self.assertEqual(path_row(repo)["rung"], "pipeline")
            self.assertNotIn("path-to-production refreshed", out)


class RefreshBeforeIsAssembledWholeTest(FactoryTestCase):
    """`with_reconciled()` hands `before_of()` the rows, the strategy and the products; each is held through a
    refresh by an example whose `before` and page would differ were that argument wrong. Holds, green on arrival."""

    def refreshed(self, why: str | None) -> tuple[list[str], list[str], str]:
        """`before` as adopted, as refreshed after a person recorded the safety net, and the page after that."""
        with tempfile.TemporaryDirectory() as directory:
            repo = maven(Path(directory), why)
            first = record(repo)["strategy"]["before"]
            recorded(repo, "safety-net", "tests-pass")
            refresh(repo)
            return first, record(repo)["strategy"]["before"], (repo / PAGE).read_text()

    def test_the_strategy_a_refresh_reads_the_entries_of_is_the_one_the_record_recommends(self) -> None:
        first, after, page = self.refreshed(WHY)
        self.assertTrue(any(SEAM in line for line in first) and any(PINNED in line for line in first), first)
        self.assertEqual(after, [line for line in first if SUITE not in line])
        for line in after:
            self.assertIn(line, page)
        self.assertIn(SEAM, page)
        self.assertIn(PINNED, page)

    def test_the_platform_a_refresh_names_in_before_is_the_products_the_record_carries(self) -> None:
        first, after, page = self.refreshed(None)
        platform = [line for line in first if line.startswith(PLATFORM)]
        self.assertGreaterEqual(len(platform), 3, first)
        self.assertEqual([line for line in after if line.startswith(PLATFORM)], platform)
        self.assertEqual(after, [line for line in first if SUITE not in line])
        for line in platform:
            self.assertIn(line, page)

    def test_the_rows_a_refresh_reads_are_the_reconciled_ones_whatever_the_strategy_and_platform(self) -> None:
        first, after, page = self.refreshed(WHY)
        self.assertTrue(any(SUITE in line for line in first), "the tree's reading names it before")
        self.assertFalse(any(SUITE in line for line in after))
        self.assertNotIn(SUITE, page)
