"""A scratch project for S27's tests: `project.json`, the three toolkit scripts beside it, a README and one log.

The verb and the gate run as `python3 -B` subprocesses, the way a generated project holds them.
"""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from reversibility_fixture import EASY
from reversibility_fixture import scratch as reversibility_scratch

NAMES = ("check-decisions.py", "reversibility.py", "provisional.py")
WHEN = "2026-10-07T21:17:49Z"


def rev_line(tiers: str = "easy", **changes: str) -> str:
    """A whole `Reversibility:` line over the easy facts with `changes` applied; `""` drops a key."""
    merged = {**EASY, **changes}
    written = " ".join(f"{key}={value}" for key, value in merged.items() if value != "")
    return f"- **Reversibility:** {tiers} · rules 1 · {written}"


EASY_LINE = rev_line()
GUARDED_LINE = rev_line("guarded", rollback_complexity="hours")
HARD_LINE = rev_line("hard", ci_workflow="yes", migrate_file="yes", behind_flag="no-code")  # the D54 fixture
FLAG_LINE = rev_line("guarded", flag_default="yes")  # guarded by F2 alone


def scratch(directory: str, log: str = "") -> Path:
    """A project holding the three scripts as `assets/toolkit/scripts/` has them, and a committed list."""
    return reversibility_scratch(directory, log, names=NAMES, listed=("scripts/check-decisions.py",))


def run(repo: Path, script: str, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["python3", "-B", f"scripts/{script}.py", *arguments], cwd=repo, text=True,
                          capture_output=True, encoding="utf-8")


def status(decide: str, ask: str = "approval", line: str | None = None, when: str = WHEN, number: str = "D12",
           ) -> subprocess.CompletedProcess[str]:
    """`provisional.py status` in a fresh scratch project; `line` (a whole `Reversibility:` line) is optional."""
    arguments = ["status", "--decide", decide, "--ask", ask, "--when", when, "--number", number]
    if line is not None:
        arguments += ["--reversibility", line]
    return raw(*arguments)


def raw(*arguments: str) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as directory:
        return run(scratch(directory), "provisional", *arguments)


def audit(log: str | dict[str, str] | None, *arguments: str) -> subprocess.CompletedProcess[str]:
    """`provisional.py audit` over a project whose `specs/f/decisions.md` holds `log` (None: no log; a dict: one log
    per feature name)."""
    with tempfile.TemporaryDirectory() as directory:
        repo = scratch(directory)
        (repo / "specs/f/decisions.md").unlink()
        if isinstance(log, str):
            log = {"f": log}
        for feature, text in (log or {}).items():
            (repo / "specs" / feature).mkdir(parents=True, exist_ok=True)
            (repo / "specs" / feature / "decisions.md").write_text("# Decisions\n\n" + text, encoding="utf-8")
        return run(repo, "provisional", "audit", *arguments)


def gate(log: str, *arguments: str, names: tuple[str, ...] = NAMES) -> subprocess.CompletedProcess[str]:
    """`check-decisions.py` over a project whose `specs/f/decisions.md` holds `log`; `names` are the scripts beside."""
    with tempfile.TemporaryDirectory() as directory:
        repo = reversibility_scratch(directory, log, names=names, listed=("scripts/check-decisions.py",))
        return run(repo, "check-decisions", *arguments)


def entry(number: int, status_line: str = "standing", revert: str | None = None, reversibility: str | None = None,
          mode: str | None = None, scope: str = "S1") -> str:
    """One decision entry. `status_line` is the text after `Status:`; `revert` the text after `Revert:` (None for
    none; `"own"` for the entry's own); `reversibility` a whole line, after `Confidence`; `mode` a whole mode line,
    after it, before `Written to`."""
    own = f"commits carrying Decision: D{number}"
    after = "" if revert is None else f"- **Revert:** {own if revert == 'own' else revert}\n"
    before = "".join(f"{text}\n" for text in (reversibility, mode) if text is not None)
    return (f"## D{number} — Question {number}\n"
            "- **Stage:** plan · **Slice:** S1 · **When:** 2026-10-07T21:17:49Z · **Iteration:** 1\n"
            f"- **Scope:** {scope}\n- **Question:** what is {number}?\n- **Options:** a · b\n- **Decision:** a\n"
            "- **Why:** because\n- **Decided by:** drive-skipper (opus)\n"
            f"- **Confidence:** high · **Would reverse if:** never\n{before}"
            f"- **Written to:** `README.md`\n- **Status:** {status_line}\n{after}")
