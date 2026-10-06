"""The lines the selector prints: each one built here, so a word that is not the selector's own is printed one way."""
from __future__ import annotations

import unicodedata

LIMIT = 200


class Full(Exception):
    """A reason the whole suite runs: its one line, already worded."""

    def __init__(self, line: str) -> None:
        super().__init__(line)
        self.line = line


def printable(value: object, limit: int = LIMIT) -> str:
    """A word that is not ours (a branch, a path, a ref, git's own words) with every control character dropped and a
    backtick made an apostrophe, so it forges no line and ends no span early."""
    kept = []
    for char in str(value):
        category = unicodedata.category(char)
        if category[0] == "C" or category in ("Zl", "Zp"):
            continue
        kept.append("'" if char == "`" else char)
    return "".join(kept)[:limit]


def full_line(reason: str) -> str:
    return f"full: {reason}"


def off_line(reason: str) -> str:
    return f"selection off: {reason}"
