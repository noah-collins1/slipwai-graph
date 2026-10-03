"""What the /cruise runner remembers between two looks at the same file.

The runner is one process for a whole run, and before and after every iteration it asks the same questions of
the same files: what do the controls say, what does `specs/` say. A file's bytes are read once, and the answer is
kept beside the facts the file reported when it was read — its size, its modification time, its change time and
its identity. A later look stats the file afresh and opens it only where a fact differs from what was recorded.
The comparison the runner makes is still one of content; the record only spares re-reading a file that nothing
can have changed. It lives in the process and is never written (D56, D57).
"""
from __future__ import annotations

import hashlib
import os
import time
from pathlib import Path
from typing import Any, Callable

Facts = tuple[Any, ...]
# A file written less than this long before it was read may be written again within the clock's granularity
# without a fact moving, so it is not vouched for until it is older than this at the moment it was read.
MARGIN_NS = 2_000_000_000


def facts_of(status: Any, strict: bool) -> Facts | None:
    """The facts a stat result reports, or None where it reports too few to vouch for a file.

    Size and modification time are always needed. A change time (which Windows reports as the creation time, so
    it is not read there) and an identity (an inode of 0 is no identity) are needed too where `strict`; where
    not, the record rests on as many as the platform reports (D49). Absent facts hold their place as None."""
    size = getattr(status, "st_size", None)
    modified = getattr(status, "st_mtime_ns", None)
    changed = getattr(status, "st_ctime_ns", None) if os.name != "nt" else None
    inode = getattr(status, "st_ino", 0) or 0
    identity = (getattr(status, "st_dev", 0), inode) if inode else None
    if size is None or modified is None:
        return None
    if strict and (changed is None or identity is None):
        return None
    return (size, modified, changed, identity)


class Record:
    """Path -> SHA-256 of its bytes, kept while the facts the file reported when it was read still stand."""

    def __init__(self, strict: bool, report: Callable[[Any], Any] | None = None,
                 clock: Callable[[], int] | None = None) -> None:
        self.strict = strict
        # Every stat result passes through `report`, so a test can hand the record a platform that says less.
        self.report = report or (lambda status: status)
        self.clock = clock or time.time_ns
        self.held: dict[str, tuple[Facts, str]] = {}

    def digest(self, path: Path) -> str:
        """The SHA-256 of the file's bytes: from the record where the file reports what it did when it was read,
        otherwise by reading it. Raises OSError where the file cannot be statted or read, and records nothing."""
        key = str(path)
        facts = facts_of(self.report(os.stat(path)), self.strict)
        held = self.held.get(key)
        if facts is not None and held is not None and held[0] == facts:
            return held[1]
        self.held.pop(key, None)
        began = self.clock()
        with open(path, "rb") as handle:
            # The facts are the file's as it was opened, before its bytes are read.
            facts = facts_of(self.report(os.fstat(handle.fileno())), self.strict)
            digest = hashlib.sha256(handle.read()).hexdigest()
        if facts is not None and max(facts[1], facts[2] or 0) <= began - MARGIN_NS:
            self.held[key] = (facts, digest)
        return digest

    def retain(self, keep: set[str]) -> None:
        """Drop the record of every file not in `keep`: a file no longer in the tree is not remembered."""
        self.held = {key: value for key, value in self.held.items() if key in keep}

    def __len__(self) -> int:
        return len(self.held)
