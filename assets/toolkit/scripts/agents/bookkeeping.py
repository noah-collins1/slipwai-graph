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
import json
import os
import stat
import time
from pathlib import Path
from typing import Any, Callable, TextIO

Facts = tuple[Any, ...]
# A file written less than this long before it was read may be written again within the clock's granularity
# without a fact moving, so it is not vouched for until it is older than this at the moment it was read.
MARGIN_NS = 2_000_000_000
# What the log's facts are while there is no log: the runner has looked, and found nothing to read.
ABSENT: Facts = ()


class NotRegular(OSError):
    """A path the runner reads or appends to as its own holds something that is not a regular file."""


def not_regular(path: Path, mode: int) -> NotRegular:
    kind = {stat.S_IFIFO: "a FIFO", stat.S_IFDIR: "a directory", stat.S_IFCHR: "a character device",
            stat.S_IFBLK: "a block device", stat.S_IFSOCK: "a socket"}.get(stat.S_IFMT(mode), "not a file")
    return NotRegular(f"{path} is {kind}, not a regular file; the runner reads and appends to it as its own and "
                      "will not wait on it")


def append_regular(path: Path) -> TextIO:
    """`path` opened for appending, only where it is a regular file: the open never waits for a reader of a FIFO, and
    what is not a regular file raises `NotRegular` instead (D63)."""
    flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT | getattr(os, "O_NONBLOCK", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError:
        try:
            mode = os.stat(path).st_mode
        except OSError:
            raise  # not a matter of what the path holds
        if not stat.S_ISREG(mode):
            raise not_regular(path, mode) from None
        raise
    mode = os.fstat(descriptor).st_mode
    if not stat.S_ISREG(mode):
        os.close(descriptor)
        raise not_regular(path, mode)
    return os.fdopen(descriptor, "a", encoding="utf-8", newline="\n")


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

    def __init__(self, strict: bool, report: Callable[[Any], Any] | None = None) -> None:
        self.strict = strict
        # Every stat result passes through `report`, so a test can hand the record a platform that says less.
        self.report = report or (lambda status: status)
        # The moment a file is hashed, as the margin reads it; a test sets this to be past the margin without waiting.
        self.clock: Callable[[], int] = time.time_ns
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


class Log:
    """The runner's log as the runner left it (D58): the entries it read, and the file's facts after its own append.

    The runner is the log's only writer, so while the file reads exactly as it was left, the only entry not yet
    counted is the one the runner appended itself and no byte need be read. Any difference — a size, a time, an
    identity, a file gone — and everything remembered is forgotten and the whole file is read again, which is what
    the answer always was. Another hand's appended entry is not tailed: a stat cannot show that the earlier bytes
    stand. `read_bytes` is what has been read since it was last taken."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.items: list[dict[str, Any]] | None = None
        self.facts: Facts | None = None
        self.read_bytes = 0

    def stands(self) -> bool:
        """Whether the file reads, now, exactly as it did after the runner's last append or read."""
        if self.items is None or self.facts is None:
            return False
        if self.facts == ABSENT:
            return not self.path.is_file()
        try:
            return facts_of(os.stat(self.path), False) == self.facts
        except OSError:
            return False

    def entries(self) -> list[dict[str, Any]]:
        """Every entry in the log: the remembered ones where the file stands, otherwise a whole read. A line that
        does not parse raises as it always did, and leaves nothing remembered."""
        if self.stands() and self.items is not None:
            return self.items
        self.items = self.facts = None
        try:
            mode = os.stat(self.path).st_mode
        except OSError:
            mode = None
        if mode is not None and not stat.S_ISREG(mode):
            raise not_regular(self.path, mode)
        if not self.path.is_file():
            self.items, self.facts = [], ABSENT
            return self.items
        with open(self.path, "rb") as handle:
            status = os.fstat(handle.fileno())
            data = handle.read()
        self.read_bytes += len(data)
        items = [json.loads(line) for line in data.decode("utf-8").splitlines() if line.strip()]
        self.items, self.facts = items, facts_of(status, False)
        return items

    def append(self, entry: dict[str, Any]) -> None:
        """Append one entry. The facts are checked first: a log that is not as it was left is forgotten, and this
        entry is appended to whatever the file now is."""
        intact = self.stands()
        if not intact:
            self.items = self.facts = None
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with append_regular(self.path) as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
            handle.flush()
            status = os.fstat(handle.fileno())
        if intact and self.items is not None:
            self.items.append(entry)
            self.facts = facts_of(status, False)

    def take(self) -> int:
        """The bytes read since the last call."""
        taken, self.read_bytes = self.read_bytes, 0
        return taken
