"""A scratch project for S26's tests: `project.json`, the two toolkit scripts beside it, a README and one log.

The verb and the gate run as `python3 -B` subprocesses, the way a generated project holds them.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from slipwai.assets import ROOT

SCRIPTS = ROOT / "assets/toolkit/scripts"
EASY = {"contract": "no", "schema": "no", "auth": "no", "customer_visible": "no", "export": "no",
        "ci_workflow": "no", "migrate_file": "no", "behind_flag": "yes", "flag_default": "no",
        "rollback_complexity": "trivial"}


def scratch(directory: str, log: str = "", origin: str | None = None, names: tuple[str, ...] = (
        "check-decisions.py", "reversibility.py")) -> Path:
    """A project with the scripts copied from `assets/toolkit/scripts/`; `origin` goes into `project.json` if given."""
    repo = Path(directory)
    (repo / "scripts").mkdir()
    for name in names:
        shutil.copy(SCRIPTS / name, repo / "scripts" / name)
    document = {} if origin is None else {"origin": origin}
    (repo / "project.json").write_text(json.dumps(document) + "\n", encoding="utf-8")
    (repo / "README.md").write_text("# scratch\n", encoding="utf-8")
    (repo / "specs/f").mkdir(parents=True)
    (repo / "specs/f/decisions.md").write_text("# Decisions\n\n" + log, encoding="utf-8")
    return repo


def facts(**changes: str) -> list[str]:
    """`key=value` arguments: the easy facts with `changes` applied; a value of `None`-like `""` drops the key."""
    merged = {**EASY, **changes}
    return [f"{key}={value}" for key, value in merged.items() if value != ""]


def score(repo: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["python3", "-B", "scripts/reversibility.py", *arguments], cwd=repo, text=True,
                          capture_output=True)


def gate(repo: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["python3", "-B", "scripts/check-decisions.py", *arguments], cwd=repo, text=True,
                          capture_output=True)


def entry(number: int, line: str | None = None, scope: str = "S1", written: str = "`README.md`") -> str:
    """One decision entry; `line` is a whole `Reversibility:` line (or None for none), after `Confidence`."""
    extra = "" if line is None else line + "\n"
    return (f"## D{number} — Question {number}\n"
            "- **Stage:** plan · **Slice:** S1 · **When:** 2026-10-03T00:00Z · **Iteration:** 1\n"
            f"- **Scope:** {scope}\n- **Question:** what is {number}?\n- **Options:** a · b\n- **Decision:** a\n"
            "- **Why:** because\n- **Decided by:** drive-bosun\n"
            f"- **Confidence:** high · **Would reverse if:** never\n{extra}"
            f"- **Written to:** {written}\n- **Status:** standing\n")
