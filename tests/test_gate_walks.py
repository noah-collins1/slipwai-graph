"""The two walking gates read each directory once and say how much they read (S01-gate-walks, rule R1).

`check-imports` and `check-migrations` end their pass line with `(N directory entries read)`: the sum of the names
every directory listing returned. The count is a measurement, not a limit.
"""
from __future__ import annotations

import os
import re
import subprocess
import tempfile
from pathlib import Path

from support import FactoryTestCase

from slipwai.assets import TOOLKIT_ROOT

IMPORTS_LINE = "check-imports: inward dependency rule holds"
MIGRATIONS_LINE = (
    "check-migrations: every migration is additive, or a marked contraction of an earlier one; "
    "Go migrate images embed their .sql files"
)
GATES = {"scripts/check-imports.py": IMPORTS_LINE, "scripts/check-migrations.py": MIGRATIONS_LINE}


def run_gate(repo: Path, script: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["python3", script], cwd=repo, text=True, capture_output=True)


def entries(repo: Path) -> int:
    """The test's own enumeration of `apps/` and `packages/`: every name every directory in them holds."""
    total = 0
    for top in ("apps", "packages"):
        for _, directories, files in os.walk(repo / top):
            total += len(directories) + len(files)
    return total


def reported(result: subprocess.CompletedProcess[str], line: str) -> int:
    """The count on a pass line that is `line`, one line, nothing on stderr."""
    pattern = re.compile(rf"^{re.escape(line)} \((\d+) directory entries read\)\n$")
    found = pattern.match(result.stdout)
    assert found is not None, f"stdout is not `{line} (N directory entries read)`: {result.stdout!r}"
    assert result.returncode == 0 and result.stderr == "", (result.returncode, result.stderr)
    return int(found.group(1))


class GateWalkListingTest(FactoryTestCase):
    def skeleton(self, directory: str) -> Path:
        return self.generate(directory, "walks", "event-modelling", "python")

    def test_the_import_gate_lists_each_directory_once_and_says_how_many_entries(self) -> None:
        """R1e1."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.skeleton(directory)
            count = reported(run_gate(repo, "scripts/check-imports.py"), IMPORTS_LINE)
            self.assertEqual(count, entries(repo))
            self.assertLessEqual(count, 100)

    def test_the_migration_gate_keeps_its_sentence_and_says_how_many_entries(self) -> None:
        """R1e2."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.skeleton(directory)
            self.assertEqual(reported(run_gate(repo, "scripts/check-migrations.py"), MIGRATIONS_LINE), entries(repo))

    def test_a_bigger_project_is_not_refused_for_its_size(self) -> None:
        """R1e3: 150 more files, the count passes 100, still one line and nothing on stderr."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.skeleton(directory)
            extra = repo / "apps/service/src/extra"
            extra.mkdir(parents=True)
            for number in range(150):
                (extra / f"empty_{number}.py").write_text("")
            for script, line in GATES.items():
                with self.subTest(script=script):
                    count = reported(run_gate(repo, script), line)
                    self.assertGreater(count, 100)
                    self.assertEqual(count, entries(repo))

    def test_a_project_with_no_source_reads_nothing(self) -> None:
        """R1e4: only `project.json` and `scripts/`."""
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "bare"
            (repo / "scripts").mkdir(parents=True)
            (repo / "project.json").write_text("{}\n")
            for script, line in GATES.items():
                with self.subTest(script=script):
                    (repo / script).write_text((TOOLKIT_ROOT / script).read_text())
                    self.assertEqual(reported(run_gate(repo, script), line), 0)

    def test_a_link_to_a_directory_is_one_entry_and_is_not_followed(self) -> None:
        """R1e5: the link counts once; what it points at is not read."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.skeleton(directory)
            before = {script: reported(run_gate(repo, script), line) for script, line in GATES.items()}
            outside = Path(directory) / "outside"
            (outside / "domain").mkdir(parents=True)
            (outside / "domain/bad.py").write_text("from ..adapters.store import save\n")
            (outside / "migrations").mkdir()
            (outside / "migrations/0001_drop.sql").write_text("DROP TABLE events;\n")
            try:
                (repo / "apps/service/linked").symlink_to(outside, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("this platform cannot make a symbolic link")
            for script, line in GATES.items():
                with self.subTest(script=script):
                    self.assertEqual(reported(run_gate(repo, script), line), before[script] + 1)
