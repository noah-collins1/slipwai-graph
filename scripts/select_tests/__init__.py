"""The factory's test selector: which `tests/test_*.py` modules a change on a slice branch can reach.

`select-tests.py` is the entry. Each module here has one job: `report` words every line, `base` says what the change
is measured against and what changed, `rules` says what a path can reach, `declarations` reads what a module says it
reads, `choose` joins them. This file spells the one order in which the cases that make a run whole are checked.
"""
from __future__ import annotations

import subprocess
from collections.abc import Mapping
from pathlib import Path

from .report import Full, full_line, off_line, printable

CI_MARKERS = ("CI", "GITHUB_ACTIONS", "GITLAB_CI")
# Research R-7: what makes git describe another tree than the one the tests read.
LOCATING = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
            "GIT_COMMON_DIR", "GIT_NAMESPACE", "GIT_CONFIG_PARAMETERS", "GIT_CONFIG_COUNT")
SLICE_PREFIX = "slice/"
GIT_TIMEOUT = 60


def environment_rows(env: Mapping[str, str]) -> Full | None:
    """Rows 1-5 of data-model *Where a run is full*: what the person or the machine said. Selection is *off* for the
    first (the run is exactly what was asked) and *full* for the rest; both are `Full`, and the line says which."""
    if env.get("FACTORY_BACKENDS"):
        return Full(off_line("FACTORY_BACKENDS given"))
    if env.get("FULL"):
        return Full(full_line(f"FULL={printable(env['FULL'])} given"))
    for name in CI_MARKERS:
        if env.get(name):
            return Full(full_line(f"{name} is set — a CI run is the full gate"))
    if env.get("RATCHET_TIGHTEN"):
        return Full(full_line("RATCHET_TIGHTEN is set — a tightened baseline must not lose the findings of modules "
                              "that did not run"))
    for name in LOCATING:
        if name in env:
            return Full(full_line(f"{name} is set — the change set would describe another tree"))
    return None


def git_out(root: Path, *args: str) -> tuple[int, str]:
    """git's status and stdout in `root`; a git that cannot run at all is status 127."""
    try:
        done = subprocess.run(["git", *args], cwd=root, text=True, errors="surrogateescape", capture_output=True,
                              timeout=GIT_TIMEOUT, check=False)
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        return 127, str(error)
    return done.returncode, done.stdout


def branch_rows(root: Path) -> str:
    """Rows 6 and 7: the branch `HEAD` is on, which must be `slice/<id>`. Returns it, or raises the line."""
    status, out = git_out(root, "symbolic-ref", "-q", "HEAD")
    if status == 1:
        raise Full(full_line("HEAD is not on a branch"))
    if status:
        raise Full(full_line(f"the change set cannot be established — git could not read HEAD: {printable(out)}"))
    name = out.strip().removeprefix("refs/heads/")
    if git_out(root, "rev-parse", "--verify", "-q", "HEAD")[0]:
        raise Full(full_line("HEAD is not on a branch"))
    identifier = name.removeprefix(SLICE_PREFIX)
    if not name.startswith(SLICE_PREFIX) or not identifier or "/" in identifier or identifier.startswith("-"):
        raise Full(full_line(f"not a slice branch (`{printable(name)}`)"))
    return name


def full_rows(env: Mapping[str, str], root: Path, *, branch: bool = True) -> Full | None:
    """The cases that make a run whole, in the order the data model lists them; the first that holds is the line. A
    replay of a range of commits has no branch to ask about, so `branch=False` leaves rows 6 and 7 out."""
    found = environment_rows(env)
    if found is not None or not branch:
        return found
    try:
        branch_rows(root)
    except Full as full:
        return full
    return None
