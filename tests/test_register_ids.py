"""A slice's id is the register's whole first cell (`S00-run-path`), not the `S00` its head spells.

`check-decisions.py` reads a feature's register at `specs/<feature>/slices/README.md`, and held every done slice to
a row in the adversary log. Read as the bare prefix, a slice with a slug was named wrongly and its row looked for
under the wrong heading. A row headed with the whole id or with the bare prefix both satisfy it (decisions D17, D19).
"""
from __future__ import annotations

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
