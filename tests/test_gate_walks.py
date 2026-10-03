"""The two walking gates read each directory once and say how much they read (S01-gate-walks, rule R1).

`check-imports` and `check-migrations` end their pass line with `(N directory entries read)`: the sum of the names
every directory listing returned. The count is a measurement, not a limit.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

from gate_audit import Audited
from support import FactoryTestCase

from slipwai.assets import TOOLKIT_ROOT

IMPORTS_LINE = "check-imports: inward dependency rule holds"
MIGRATIONS_LINE = (
    "check-migrations: every migration is additive, or a marked contraction of an earlier one; "
    "Go migrate images embed their .sql files"
)
PRUNED = (".venv", "node_modules", "__pycache__", ".git")
GATES = {"scripts/check-imports.py": IMPORTS_LINE, "scripts/check-migrations.py": MIGRATIONS_LINE}


def run_gate(repo: Path, script: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["python3", script], cwd=repo, text=True, capture_output=True)


def entries(repo: Path) -> int:
    """The test's own enumeration of `apps/` and `packages/`: every name every directory in them holds, the
    four directories nobody reads counted as names and not entered."""
    total = 0
    for top in ("apps", "packages"):
        for _, directories, files in os.walk(repo / top):
            total += len(directories) + len(files)
            directories[:] = [name for name in directories if name not in PRUNED]
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


class GateWalkPrunedTest(FactoryTestCase):
    """R2: `.venv`, `node_modules`, `__pycache__` and `.git` are never descended, at any depth, in any walk."""

    def plant(self, repo: Path, under: str) -> None:
        base = repo / under
        (base / ".venv/lib/pkg/domain").mkdir(parents=True)
        (base / ".venv/lib/pkg/domain/bad.py").write_text("from ..adapters.store import save\n")
        (base / "node_modules/pkg/migrations").mkdir(parents=True)
        (base / "node_modules/pkg/migrations/0001_drop.sql").write_text("DROP TABLE events;\n")
        (base / "__pycache__").mkdir()
        (base / "__pycache__/x.py").write_text("x = 1\n")
        (base / ".git/hooks").mkdir(parents=True)
        (base / ".git/hooks/x").write_text("")

    def test_the_four_names_are_not_read_where_they_are_planted(self) -> None:
        """R2e1 and R2e2: beside the source and two directories deeper, both gates pass, the count follows."""
        for under in ("apps/service", "apps/service/src/a/b"):
            with self.subTest(under=under), tempfile.TemporaryDirectory() as directory:
                repo = self.generate(directory, "pruned", "event-modelling", "python")
                skeleton = entries(repo)
                self.plant(repo, under)
                for script, line in GATES.items():
                    count = reported(run_gate(repo, script), line)
                    self.assertEqual(count, entries(repo))
                    self.assertGreaterEqual(count, skeleton + 4)

    def test_a_pruned_directory_in_a_web_app_hides_nothing_from_rule_4(self) -> None:
        """R2e3."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "pruned-web", "event-modelling", "python", frontend="react-vite")
            vendored = repo / "apps/web/node_modules/pkg/src"
            vendored.mkdir(parents=True)
            (vendored / "x.ts").write_text("import { y } from '../../../../service/src/domain/thing';\n")
            reported(run_gate(repo, "scripts/check-imports.py"), IMPORTS_LINE)

    def test_no_pruned_directory_is_listed(self) -> None:
        """R2e4: under the audit hook, no listing of any path inside one of the four."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "pruned-audit", "event-modelling", "python")
            self.plant(repo, "apps/service/src/a/b")
            for script in GATES:
                with self.subTest(script=script):
                    audited = Audited(repo, script)
                    self.assertEqual(audited.result.returncode, 0, audited.result.stderr)
                    self.assertTrue(any(path.startswith("apps/service/src/a/b") for path in audited.listed))
                    inside = [path for path in audited.listed if set(path.split("/")) & set(PRUNED)]
                    self.assertEqual(inside, [])


class GateWalkManifestTest(FactoryTestCase):
    """R5: `project.json` is opened at most once per run."""

    def test_the_import_gate_opens_the_manifest_once(self) -> None:
        """R5e1: a web app and a two-context service, so every rule that asks the manifest runs."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "once", "event-modelling", "python", frontend="react-vite")
            manifest = json.loads((repo / "project.json").read_text())
            manifest["deployables"]["service"]["contexts"] = ["orders", "billing"]
            (repo / "project.json").write_text(json.dumps(manifest, indent=2) + "\n")
            audited = Audited(repo, "scripts/check-imports.py")
            self.assertEqual(audited.result.returncode, 0, audited.result.stderr)
            self.assertEqual(audited.opened.count("project.json"), 1)

    def test_the_migration_gate_opens_the_manifest_once(self) -> None:
        """R5e2, moved by D52 (AC-S01-8): it reads none before the slice, and now reads once, for which deployables
        are Java."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "once", "event-modelling", "python")
            audited = Audited(repo, "scripts/check-migrations.py")
            self.assertEqual(audited.result.returncode, 0, audited.result.stderr)
            self.assertEqual(audited.opened.count("project.json"), 1)

    def test_hold_without_a_manifest_both_gates_still_pass(self) -> None:
        """R5e3, a hold: the rules that need the manifest find no applications."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "none", "event-modelling", "python", frontend="react-vite")
            (repo / "project.json").unlink()
            for script, line in GATES.items():
                with self.subTest(script=script):
                    reported(run_gate(repo, script), line)
