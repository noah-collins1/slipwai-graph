"""A scratch project for the result-contract gate: the toolkit scripts copied beside a `project.json`, a record
under `specs/f/slices/S1/`, a valid block, and the checker run as `python3 -B` the way a project runs it."""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from slipwai.assets import ROOT

SCRIPTS = ROOT / "assets/toolkit/scripts"
HEADING = "## 2026-10-05T17:00:00Z — drive-gaps — gaps"
RECORD = "specs/f/slices/S1/hand-backs.md"


def valid() -> dict[str, Any]:
    """The page's example block: every one of the thirteen fields, each of its type."""
    return {"contract": 1, "delegate": "drive-gaps", "scope": "S14-result-contract converge pass 1",
            "status": "gaps", "contracts_changed": [], "invariants_checked": ["AC-S14-16 bytes"],
            "tests": ["make test TESTS=test_x: 12 passed"], "decisions": ["D134"], "assumptions": [],
            "unresolved": [], "change_summary": "Read the diff; two gaps.", "files_changed": [],
            "difficulty_observed": {"score": 2, "reason": "one module, clear criteria"}}


def fence(block: dict[str, Any] | str) -> str:
    body = block if isinstance(block, str) else json.dumps(block)
    return f"```result-contract\n{body}\n```\n"


def entry(block: dict[str, Any] | str | None = None, heading: str = HEADING) -> str:
    return f"{heading}\n\n{fence(valid() if block is None else block)}\n"


def decision(number: int) -> str:
    """One decision entry the gate passes, in the shape `commands/cruise.md` shows."""
    return (f"## D{number} — Question {number}\n"
            "- **Stage:** plan · **Slice:** S1 · **When:** 2026-10-03T00:00Z · **Iteration:** 1\n"
            f"- **Question:** what is {number}?\n- **Options:** a · b\n- **Decision:** a\n- **Why:** because\n"
            "- **Decided by:** drive-bosun\n- **Confidence:** high · **Would reverse if:** never\n"
            "- **Written to:** `README.md`\n- **Status:** standing\n\n")


def scratch(directory: str, record: str | None = None, decisions: int = 134, path: str = RECORD) -> Path:
    """A project with the two toolkit scripts, a `decisions.md` holding D1..D<decisions> and one record."""
    repo = Path(directory)
    (repo / "scripts").mkdir()
    for name in ("check-decisions.py", "hand_backs.py"):
        shutil.copy(SCRIPTS / name, repo / "scripts" / name)
    (repo / "project.json").write_text("{}\n", encoding="utf-8")
    (repo / "README.md").write_text("# scratch\n", encoding="utf-8")
    (repo / "specs/f/slices/S1").mkdir(parents=True)
    if decisions:
        (repo / "specs/f/decisions.md").write_text(
            "# Decisions\n\n" + "".join(decision(n) for n in range(1, decisions + 1)), encoding="utf-8")
    if record is not None:
        (repo / path).write_text(record, encoding="utf-8")
    return repo


def run(repo: Path, *args: str, stdin: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["python3", "-B", "scripts/check-decisions.py", *args], cwd=repo, text=True,
                          capture_output=True, input=stdin)


def gate(record: str, decisions: int = 134, path: str = RECORD) -> subprocess.CompletedProcess[str]:
    """The checker's no-argument run over a project holding just this record."""
    with tempfile.TemporaryDirectory() as directory:
        return run(scratch(directory, record, decisions, path))


def findings(result: subprocess.CompletedProcess[str]) -> list[str]:
    """The finding lines on stderr, indentation removed."""
    return [line.strip() for line in result.stderr.splitlines() if line.startswith("  ")]
