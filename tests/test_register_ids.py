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


MODEL = "slices:\n  - id: place-order\n    status: implemented\n    spec: specs/f/spec.md\n"


def model_slice(repo: Path, head: str | None) -> None:
    """A slice the model alone names, `place-order`: no letters-then-digits head, so no bare prefix to fall back on."""
    (repo / "docs/event-model").mkdir(parents=True, exist_ok=True)
    (repo / "docs/event-model/model.yaml").write_text(MODEL)
    (repo / "specs/f/slices/place-order").mkdir(parents=True, exist_ok=True)
    (repo / "specs/f/slices/README.md").unlink(missing_ok=True)
    log = repo / "specs/f/adversary-log.md"
    log.unlink(missing_ok=True)
    if head is not None:
        log.write_text(LOG.format(head=head))


class IdWithoutAPrefixTest(FactoryTestCase):
    """An id from the model with no letters-then-digits head has no prefix and is looked up whole (D19)."""

    def test_check_benchmark_warns_of_the_missing_record_and_exits_clean(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "noprefixb", "standard", "python")
            model_slice(repo, None)
            found = warnings(repo)
            self.assertIn("specs/f/slices/place-order is done but has no benchmark.json", "\n".join(found))
            (repo / "specs/f/slices/place-order/benchmark.json").write_text(
                json.dumps({"slice": "place-order", "stages": [], "shape": {}}))
            self.assertEqual([line for line in warnings(repo) if "place-order" in line], [])

    def test_check_decisions_names_the_whole_id_without_a_row_and_passes_with_it(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "noprefixd", "standard", "python")
            model_slice(repo, None)
            refused = gate(repo)
            self.assertEqual(refused.returncode, 1, refused.stderr)
            self.assertIn("no row for place-order, which is done", refused.stderr)
            self.assertNotIn("Traceback", refused.stderr)
            model_slice(repo, "place-order")
            self.assertEqual(gate(repo).returncode, 0, gate(repo).stderr)

    def test_the_baseline_writes_a_row_headed_with_the_whole_id(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "noprefixbase", "standard", "python")
            model_slice(repo, None)
            result = subprocess.run(["python3", "scripts/check-decisions.py", "--adversary-baseline"], cwd=repo,
                                    text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("## place-order · predates the adversary gate",
                          (repo / "specs/f/adversary-log.md").read_text())


class BaselineBesideABareRowTest(FactoryTestCase):
    def test_the_baseline_writes_no_row_for_a_slice_already_recorded_under_its_bare_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "baserow", "standard", "python")
            self.assertEqual(register(repo, "S00-run-path", "S00").returncode, 0)
            before = (repo / "specs/f/adversary-log.md").read_text()
            result = subprocess.run(["python3", "scripts/check-decisions.py", "--adversary-baseline"], cwd=repo,
                                    text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("nothing to baseline", result.stdout)
            self.assertEqual((repo / "specs/f/adversary-log.md").read_text(), before)
