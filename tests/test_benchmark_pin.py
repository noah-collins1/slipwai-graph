"""S39 pins what `make benchmark` printed before it (AC-S39-8, D65): the records a project already has must read
the same after `migrate`, except where S39 renames a column on purpose.

`benchmark.py` as it stood at `525399b` — the commit S39 was cut from — and the working copy's run over one tree:
every record committed at `8072724`. Every cell of every column both tables carry is equal (a renamed column is
compared under its new name), every key the old `--json` carried still holds its value, and `check-benchmark` is
byte for byte the same. Transcripts are kept out (an empty `HOME`) and the tree is no git repository, so nothing a
machine happens to hold can make the two disagree.
"""
from __future__ import annotations

import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

from slipwai.assets import ROOT

sys.dont_write_bytecode = True

BEFORE = "525399b"  # benchmark.py as it stood before S39
RECORDS = "8072724"  # the records as committed when S39's criteria were written
SCRIPTS = ("assets/toolkit/scripts/agents", "assets/toolkit/scripts/hand_backs.py")
# Columns S39 renames, old name → new name: compared under the new name, values unchanged.
RENAMED: dict[str, str] = {"wall": "stage time", "rework": "re-entered"}
# `--json` keys S39 renames, old → new.
RENAMED_KEYS: dict[str, str] = {"rework": "reentered"}


def archive(commit: str, *paths: str) -> tarfile.TarFile:
    data = subprocess.run(["git", "archive", "--format=tar", commit, *paths], cwd=ROOT, capture_output=True,
                          check=True).stdout
    return tarfile.open(fileobj=io.BytesIO(data))


def project(where: Path, scripts: tarfile.TarFile | None) -> Path:
    """A scratch project: `project.json`, the toolkit's `scripts/` (from `scripts`, or the working copy), and the
    `specs/` tree as committed at RECORDS."""
    where.mkdir(parents=True)
    (where / "project.json").write_text("{}\n", encoding="utf-8")
    staging = where / ".staging"
    if scripts is None:
        shutil.copytree(ROOT / SCRIPTS[0], staging / SCRIPTS[0], ignore=shutil.ignore_patterns("__pycache__"))
        (staging / SCRIPTS[1]).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / SCRIPTS[1], staging / SCRIPTS[1])
    else:
        scripts.extractall(staging, filter="data")
    shutil.move(str(staging / "assets/toolkit/scripts"), where / "scripts")
    shutil.rmtree(staging)
    archive(RECORDS, "specs").extractall(where, filter="data")
    return where


def run(repo: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    env = {key: value for key, value in os.environ.items() if not key.startswith(("CLAUDE", "CODEX"))}
    env["HOME"] = str(repo / ".home")
    (repo / ".home").mkdir(exist_ok=True)
    return subprocess.run(["python3", "-B", str(repo / "scripts/agents/benchmark.py"), *arguments], cwd=repo,
                          env=env, text=True, capture_output=True, timeout=300)


def columns(header: str) -> list[tuple[str, int]]:
    """Each column's name and where it starts: names are left-justified and joined by two spaces (a name may hold
    one space, `stage time`)."""
    found: list[tuple[str, int]] = []
    position = 0
    for name in re.split(r" {2,}", header.strip()):
        start = header.index(name, position)
        found.append((name, start))
        position = start + len(name)
    return found


def table(output: str, rows: int) -> dict[str, dict[str, str]]:
    """The slice table's cells, by the row's slice and the column's name."""
    lines = output.splitlines()
    head = next(index for index, line in enumerate(lines) if line.lstrip().startswith("slice "))
    spans = columns(lines[head])
    cells: dict[str, dict[str, str]] = {}
    for line in lines[head + 1:head + 1 + rows]:
        row = {}
        for index, (name, start) in enumerate(spans):
            end = spans[index + 1][1] if index + 1 < len(spans) else None
            row[name] = line[start:end].strip()
        cells[row["slice"]] = row
    return cells


class BenchmarkPinTest(unittest.TestCase):
    scratch: tempfile.TemporaryDirectory[str]
    before: Path
    after: Path

    @classmethod
    def setUpClass(cls) -> None:
        cls.scratch = tempfile.TemporaryDirectory()
        base = Path(cls.scratch.name)
        cls.before = project(base / "before", archive(BEFORE, *SCRIPTS))
        cls.after = project(base / "after", None)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.scratch.cleanup()

    def test_e1_every_column_s39_does_not_rename_holds_its_values(self) -> None:
        records = json.loads(run(self.before, "--json").stdout)
        before, after = run(self.before), run(self.after)
        self.assertEqual(0, after.returncode, after.stderr)
        self.assertNotIn("Traceback", after.stderr)
        old, new = table(before.stdout, len(records)), table(after.stdout, len(records))
        self.assertEqual(sorted(old), sorted(new))
        for slice_, row in old.items():
            for name, value in row.items():
                with self.subTest(slice=slice_, column=name):
                    self.assertIn(RENAMED.get(name, name), new[slice_])
                    self.assertEqual(value, new[slice_][RENAMED.get(name, name)])

    def test_e1_every_key_the_old_json_carried_holds_its_value(self) -> None:
        old = json.loads(run(self.before, "--json").stdout)
        new = json.loads(run(self.after, "--json").stdout)
        self.assertEqual([record["path"] for record in old], [record["path"] for record in new])
        for was, now in zip(old, new, strict=True):
            for key, value in was.items():
                with self.subTest(record=was["path"], key=key):
                    self.assertEqual(value, now[RENAMED_KEYS.get(key, key)])

    def test_e2_check_benchmark_is_byte_for_byte_the_same(self) -> None:
        before, after = run(self.before, "check"), run(self.after, "check")
        self.assertEqual((before.returncode, before.stdout, before.stderr),
                         (after.returncode, after.stdout, after.stderr))


if __name__ == "__main__":
    unittest.main()
