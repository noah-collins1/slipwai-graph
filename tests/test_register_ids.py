"""A slice's id is the register's whole first cell (`S00-run-path`), not the `S00` its head spells.

`check-decisions.py` reads a feature's register at `specs/<feature>/slices/README.md`, and held every done slice to
a row in the adversary log. Read as the bare prefix, a slice with a slug was named wrongly and its row looked for
under the wrong heading. `check-benchmark` looks for the slice's record the same way: at `slices/<whole id>/`,
then at `slices/<prefix>/`. A row headed with the whole id or with the bare prefix both satisfy it (decisions D17, D19).
"""
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from support import FactoryTestCase

LOG = "# Adversary log\n\n## {head} · abc1234 · 2026-09-22\n\n| Trigger | Status | Evidence |\n|---|---|---|\n" \
      "| new endpoint | not present | prior row |\n\nSpawned:\nOmitted: none\nFindings: none\n"


def gate(repo: Path) -> subprocess.CompletedProcess:
    return subprocess.run(["python3", "scripts/check-decisions.py"], cwd=repo, text=True, capture_output=True)


def register(repo: Path, ident: str, head: str | None) -> subprocess.CompletedProcess:
    feature = repo / "specs/f"
    (feature / "slices").mkdir(parents=True, exist_ok=True)
    (feature / "slices/README.md").write_text(f"| Slice | Accepted |\n|---|---|\n| `{ident}` | 2026-09-22 |\n")
    log = feature / "adversary-log.md"
    if head is None:
        log.unlink(missing_ok=True)
    else:
        log.write_text(LOG.format(head=head))
    return gate(repo)


class RegisterIdsTest(FactoryTestCase):
    def test_a_row_headed_with_the_whole_id_satisfies_the_gate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "whole", "standard", "python")
            result = register(repo, "S00-run-path", "S00-run-path")
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_a_row_headed_with_the_bare_prefix_still_satisfies_the_gate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "bare", "standard", "python")
            result = register(repo, "S00-run-path", "S00")
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_a_missing_row_is_a_finding_that_names_the_whole_id(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "missing", "standard", "python")
            result = register(repo, "S00-run-path", None)
            self.assertEqual(result.returncode, 1)
            self.assertIn("no row for S00-run-path, which is done", result.stderr)
            result = register(repo, "S00-run-path", "S01-other")
            self.assertEqual(result.returncode, 1)
            self.assertIn("no row for S00-run-path, which is done", result.stderr)

    def test_a_register_id_without_a_slug_reads_as_before_and_header_rows_are_no_ids(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "plain", "standard", "python")
            self.assertEqual(register(repo, "S1", "S1").returncode, 0)
            refused = register(repo, "S1", None)
            self.assertEqual(refused.returncode, 1)
            self.assertIn("no row for S1, which is done", refused.stderr)
            self.assertNotIn("Slice", refused.stderr)
            self.assertNotIn("---", refused.stderr)


def warnings(repo: Path) -> list[str]:
    result = subprocess.run(["python3", "scripts/agents/benchmark.py", "check"], cwd=repo, text=True,
                            capture_output=True)
    assert result.returncode == 0, result.stderr
    return [line for line in result.stderr.splitlines() if "slices/" in line]


def record_for(repo: Path, ident: str, folder: str | None) -> list[str]:
    """Register `ident` as done, leave a closed record under `slices/<folder>/` (none when None), and run the check."""
    slices = repo / "specs/f/slices"
    slices.mkdir(parents=True, exist_ok=True)
    (slices / "README.md").write_text(f"| Slice | Accepted |\n|---|---|\n| `{ident}` | 2026-09-22 |\n")
    if folder:
        (slices / folder).mkdir(parents=True, exist_ok=True)
        (slices / folder / "benchmark.json").write_text(json.dumps({"slice": folder, "stages": [], "shape": {}}))
    return warnings(repo)


class RecordLookupTest(FactoryTestCase):
    def test_a_record_under_the_whole_id_is_found(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "recwhole", "standard", "python")
            self.assertEqual(record_for(repo, "S00-run-path", "S00-run-path"), [])

    def test_a_record_under_the_bare_prefix_is_still_found(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "recbare", "standard", "python")
            self.assertEqual(record_for(repo, "S00-run-path", "S00"), [])

    def test_no_record_is_one_warning_naming_the_whole_id(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "recnone", "standard", "python")
            found = record_for(repo, "S00-run-path", None)
            self.assertEqual(len([line for line in found if "is done but has no" in line]), 1, found)
            self.assertIn("specs/f/slices/S00-run-path is done but has no benchmark.json", found[0])

    def test_a_register_id_without_a_slug_is_held_as_before(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "recplain", "standard", "python")
            self.assertEqual(record_for(repo, "S1", "S1"), [])
            (repo / "specs/f/slices/S1/benchmark.json").unlink()
            self.assertIn("specs/f/slices/S1 is done but has no benchmark.json", record_for(repo, "S1", None)[0])
