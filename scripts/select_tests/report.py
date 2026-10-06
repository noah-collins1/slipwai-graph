"""The lines the selector prints: each one built here, so a word that is not the selector's own is printed one way."""
from __future__ import annotations

import unicodedata

LIMIT = 200


class Full(Exception):
    """A reason the whole suite runs: its one line, already worded, and where a replay established what it was
    compared with, that base (a full replay still says what it was measured against)."""

    def __init__(self, line: str, against: str = "") -> None:
        super().__init__(line)
        self.line = line
        self.against = against


def printable(value: object, limit: int = LIMIT, quote: bool = True) -> str:
    """A word that is not ours (a branch, a path, a ref, git's own words) with every control character dropped and,
    where `quote`, a backtick made an apostrophe, so it forges no line and ends no span early. Words the scoped gate
    already made printable keep their own backticks (`quote=False`)."""
    kept = []
    for char in str(value):
        category = unicodedata.category(char)
        if category[0] == "C" or category in ("Zl", "Zp"):
            continue
        kept.append("'" if quote and char == "`" else char)
    return "".join(kept)[:limit]


def full_line(reason: str) -> str:
    return f"full: {reason}"


def off_line(reason: str) -> str:
    return f"selection off: {reason}"


def skipped_line(module: str, reason: str) -> str:
    return f"skipped {module}: {reason}"


def narrowed_line(module: str, backends: tuple[str, ...], left_out: tuple[str, ...]) -> str:
    only = ("backend " if len(backends) == 1 else "backends ") + ", ".join(backends)
    return f"narrowed {module}: {only} only ({', '.join(left_out)} unaffected)"


def summary_line(selected: int, total: int, against: str) -> str:
    return f"selected {selected} of {total} modules against {against}"
