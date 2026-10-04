#!/usr/bin/env python3
"""Say whether this tree already passed the gate, and record that it did: `reuse` and `record`.

`make verify` asks `reuse` first. It exits 0 only after printing the one line that says the full gate did not run
because this tree already passed it; any other answer — no stamp, a stamp for another key, anything this script cannot
read — exits non-zero, and the recipe runs every check. After the checks passed, `record` writes the stamp: a JSON
file under the git directory, never in the working tree, holding the key the tree had when the checks began. Nothing
here can fail the gate: `reuse` exits 0 only after printing its line, and `record` always exits 0.

The key is one SHA-256 over named parts, each a digest of its own so the stamp can show them apart. It starts the
way a tree is judged — every file git tracks and every file it does not ignore, by raw bytes, executable bit and a
link's target, read from the working tree through no filter, and the index's entries — and the parts a later rule
adds are named where they join.

Starts on any `python3`: nothing here is newer than the syntax the gate's `check-python` message is printed from,
and an interpreter older than 3.10 answers "no stamp" before it reads anything.
"""
from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
import sys
import time

# The stamp's fields: the key a later run compares, the three parts it is made of, the instant of the pass, and
# the result, which is only ever a pass.
FIELDS = ("key", "tree", "scripts", "tools", "passed", "result")
EMPTY = hashlib.sha256(b"").hexdigest()
REUSE_LINE = (
    "verify: the full gate did not run; this tree already passed it at {passed} (key {abbreviated}); "
    "VERIFY_FORCE=1 runs it anyway"
)


class CannotTell(Exception):
    """The key cannot be built; the full gate runs."""


def git(*args: str) -> bytes:
    try:
        done = subprocess.run(["git", *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    except OSError as error:
        raise CannotTell("git: " + str(error))
    if done.returncode != 0:
        raise CannotTell("git " + " ".join(args) + ": " + done.stderr.decode("utf-8", "replace").strip())
    return done.stdout


def digest(parts: list[bytes]) -> str:
    """One SHA-256 over length-prefixed parts, so no two lists of parts make the same digest."""
    whole = hashlib.sha256()
    for part in parts:
        whole.update(str(len(part)).encode("ascii") + b":" + part)
    return whole.hexdigest()


def covered_files() -> list[bytes]:
    """Every file the gate judges: tracked, and untracked where git does not ignore it, under this directory."""
    listed = git("ls-files", "-z", "--cached", "--others", "--exclude-standard")
    return sorted(set(path for path in listed.split(b"\0") if path))


def file_record(path: bytes) -> bytes:
    """One covered file as the key sees it, whatever it is: a regular file by its executable bit and the SHA-256 of
    its raw bytes, a link by its target as written and never followed, a file that is not there as missing. Read with
    `lstat` and `open`, through none of git's filters and none of its stat shortcuts."""
    try:
        status = os.lstat(path)
    except FileNotFoundError:
        return path + b"\0missing"
    if stat.S_ISLNK(status.st_mode):
        return path + b"\0link\0" + os.readlink(path)
    if not stat.S_ISREG(status.st_mode):
        raise CannotTell(os.fsdecode(path) + " is neither a file nor a link")
    with open(path, "rb") as handle:
        content = hashlib.sha256(handle.read()).hexdigest().encode("ascii")
    return path + b"\0" + (b"exec" if status.st_mode & stat.S_IXUSR else b"file") + b"\0" + content


def index_entries() -> bytes:
    """The index's entries — mode, blob id, stage, name — as `ls-files --stage` lists them, which reads the index
    and never writes it."""
    return git("ls-files", "-z", "--stage")


def tree_digest() -> str:
    return digest([index_entries()] + [file_record(path) for path in covered_files()])


def build_key() -> dict[str, object]:
    """The parts and the key they make. `scripts` and `tools` join the key when their rules are written."""
    tree = tree_digest()
    scripts = EMPTY
    tools: dict[str, str] = {}
    key = digest([tree.encode("ascii"), scripts.encode("ascii"), json.dumps(tools, sort_keys=True).encode("utf-8")])
    return {"key": key, "tree": tree, "scripts": scripts, "tools": tools}


def stamp_directory() -> str:
    return os.path.join(git("rev-parse", "--absolute-git-dir").decode("utf-8").strip(), "slipwai")


def project_name() -> str:
    """Which project of the repository this is: a digest of where it sits, so the file holds no path."""
    prefix = git("rev-parse", "--show-prefix").decode("utf-8").strip()
    return hashlib.sha256(prefix.encode("utf-8")).hexdigest()[:16]


def stamp_path() -> str:
    return os.path.join(stamp_directory(), "verify-stamp-" + project_name() + ".json")


def pending_path() -> str:
    return os.path.join(stamp_directory(), "verify-stamp-" + project_name() + ".pending")


def read_stamp(path: str) -> dict[str, object] | None:
    """The stamp, or None where there is none, it cannot be parsed, or it lacks a field."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            stamp = json.load(handle)
    except (OSError, ValueError):
        return None
    if not isinstance(stamp, dict) or any(field not in stamp for field in FIELDS) or stamp["result"] != "pass":
        return None
    return stamp


def write_file(path: str, text: str) -> None:
    """A finished file or none: written beside its name, then renamed onto it."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    temporary = path + "." + str(os.getpid()) + ".tmp"
    with open(temporary, "w", encoding="utf-8") as handle:
        handle.write(text)
    os.replace(temporary, path)


def reuse() -> int:
    key = build_key()
    stamp = read_stamp(stamp_path())
    if stamp is not None and stamp["key"] == key["key"]:
        print(REUSE_LINE.format(passed=stamp["passed"], abbreviated=str(key["key"])[:12]))
        return 0
    write_file(pending_path(), str(key["key"]))
    return 1


def record() -> int:
    with open(pending_path(), "r", encoding="utf-8") as handle:
        pending = handle.read()
    key = build_key()
    if key["key"] != pending:
        return 0
    passed = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    stamp = dict(key, passed=passed, result="pass")
    write_file(stamp_path(), json.dumps(stamp, indent=2, sort_keys=True) + "\n")
    os.remove(pending_path())
    return 0


def main(argv: list[str]) -> int:
    verb = argv[0] if argv else ""
    try:
        if sys.version_info < (3, 10):
            return 0 if verb == "record" else 1
        if verb == "reuse":
            return reuse()
        if verb == "record":
            return record()
    except Exception:
        pass
    return 0 if verb == "record" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
