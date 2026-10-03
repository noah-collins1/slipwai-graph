#!/usr/bin/env python3
"""Fail when the code index this project carries no longer describes the code that is here.

A code index is only worth asking while it is current, and a stale one does not say so: asked
which functions call a symbol it never read, it answers *none* — the same answer it gives when
nothing calls it, and exactly the failure an index is bought to avoid in a text search.

CodeGraph keeps `.codegraph/codegraph.db` up to date by watching the tree, but the watcher lives
in a daemon, and that daemon only runs while a CodeGraph client is attached to it — an MCP
client, or a `codegraph` command. It shuts down on an idle timeout once the last one goes away.
So a checkout opened somewhere that has the database and not the tooling — a container, a
sandbox, a CI runner, a machine where the CLI was never installed — keeps a file that looks like
an index, answers every question without complaint, and has not been written to since the last
client was attached. Nothing else in this repository would notice.

This does. It compares what the index holds with what version control tracks, and reports the two
ways an index goes wrong: a file it has never seen, and a file whose content changed after it was
read. The comparison is by SHA-256 — `files.content_hash` is the digest of the file's bytes —
rather than by modification time, because a checkout, a rebase or a `touch` moves an mtime
without changing a line, and a gate that cries stale over those is a gate that gets ignored. The
timestamp is still reported: `files.indexed_at` is the last moment anything was indexed, which is
the last moment a client was attached, and that is the number that says *why* it is behind.

Two more things make it worth running before it judges. A database that does not pass SQLite's
integrity check is never a pass: CodeGraph's own `status` and `sync` report a malformed index as
up to date, and only a query finds out. Where the pinned CLI is reachable
(`scripts/agents/code_index.py`), a corrupt database is moved aside and rebuilt, and an index
behind the tree is synced, before it is compared — the database is derived from the source and
ignored by Git — so the gate fails only where the index cannot be made sound and current: the
tooling absent, or the rebuild or sync not taking, which is the state it exists to report.
`CODEGRAPH_GATE_NO_SYNC=1` compares without repairing anything.

All of that is the whole run, and it is what the trunk, every other branch, a detached `HEAD` and CI do. On a
`slice/<id>` branch in a developer's checkout, outside CI, the gate compares only what changed since its last whole
comparison and leaves the integrity check to the trunk and CI: a developer waits on this gate three times a slice,
and what a passing whole run vouched for has not moved. It keeps that record in `.codegraph/gate-memory.json`,
written only by a pass and only where Git ignores `.codegraph/`, and deleting that file makes the next run whole.
The runner's check before an iteration, `health()` in `scripts/agents/code_index.py`, reads and renews the same
record through this script's own functions (outside CI, on any branch); this gate's own output is unchanged by it.
Wherever the record cannot be used or cannot be kept, the run is the whole run and the pass line says why, in one
clause. Which files moved is never taken from Git alone: the record holds how each looked when it was hashed.

No `.codegraph/` is not a failure: the code index is an optional extension (`./init --extension
codegraph`), and a project that never adopted one has nothing to keep fresh. Standard library
only, like every gate script here.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
import re
import sqlite3
import stat
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path, PurePath
from typing import Any


def project_root(script: Path, depth: int) -> Path:
    """The repository root: the nearest directory above this script holding `project.json`.

    This script's own tree is `<root>/scripts` in a generated project and `<root>/<layout.delivery>/scripts`
    where the method was installed beside an existing codebase (`project.json`'s `layout.delivery`), so how
    far below the root it sits is not something to count; `depth` is only the fallback for a tree with no
    manifest at all.
    """
    for candidate in script.parents:
        if (candidate / "project.json").is_file():
            return candidate
    return script.parents[depth]


ROOT = project_root(Path(__file__).resolve(), 1)
INDEX = ROOT / ".codegraph/codegraph.db"
# What the last whole comparison vouched for, so that a run on a `slice/<id>` branch need hash only what moved.
MEMORY = ROOT / ".codegraph/gate-memory.json"
SLICE_BRANCH = re.compile(r"^slice/[A-Za-z0-9][A-Za-z0-9._-]*$")
CI_MARKERS = ("CI", "GITHUB_ACTIONS", "GITLAB_CI")
# How many offending paths to name before summarising the rest: enough to recognise the shape of
# what is missing, short enough that the gate's output stays readable.
LISTED = 8
RESTORE = """This is not a rebuild you forgot to run. CodeGraph keeps itself current only while a
client is attached: the watcher lives in a daemon that starts with an MCP client or a
`codegraph` command and shuts down on its idle timeout. A checkout opened where that
tooling is absent — a container, a sandbox, a CI runner, a machine where the CLI was
never installed — keeps this database and never writes to it again.

Attaching a client once catches the backlog up on its own. From a terminal, in this
directory: `scripts/codegraph sync`, which runs the pinned CLI through `npx` or an
installed `codegraph`. From an agent session: configure the CodeGraph MCP server for this
project. To put the tooling back for good, install it and re-adopt the extension, which
is also what re-points the agent at the index:

  curl -fsSL https://raw.githubusercontent.com/colbymchenry/codegraph/main/install.sh | sh
  ./init --extension codegraph

Until one of those has run, treat this index as absent rather than empty: it answers
about the code it last read, and says nothing about the rest."""


def tracked() -> list[str] | None:
    """Every tracked path, or None where git cannot answer: an export, a tarball, no git at all."""
    try:
        completed = subprocess.run(
            ["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return [path for path in completed.stdout.decode("utf-8", "replace").split("\0") if path]


def rows_of(source: str) -> list[tuple[str, str, float]]:
    with sqlite3.connect(source, uri=True) as connection:
        return connection.execute("SELECT path, content_hash, indexed_at FROM files").fetchall()


def indexed() -> dict[str, tuple[str, float]] | None:
    """Each indexed path with its content digest and the moment it was indexed, or None where
    this database does not carry the table this check reads.

    CodeGraph owns that schema, and a version of it that renamed a column is its business rather
    than a reason to fail somebody's build — so an unreadable shape is reported and skipped, not
    failed. The read-only URI is the first attempt rather than the only one: a database left in
    WAL mode may need to create its shared-memory file before anything can be read, which
    read-only cannot do, and stopping there would be silence in the one state this reports.
    """
    try:
        rows = rows_of(f"{INDEX.as_uri()}?mode=ro")
    except sqlite3.Error:
        try:
            rows = rows_of(INDEX.as_uri())
        except sqlite3.Error:
            return None
    return {str(path): (str(digest), float(at or 0)) for path, digest, at in rows}


HASHED = [0]  # how many files this run read to compare, said on a narrowed pass line
START = time.time()  # the moment this run began: what a file's times are measured against, were it to vouch for it
# What each file looked like as it was opened to be hashed: size, modification time and change time in nanoseconds,
# and its inode. The memory keeps these, because git's own comparison normalises some changes away (D49).
STATS: dict[str, list[int]] = {}
SAFELY = 2.0  # seconds a file's times must be older than the run that vouched for it, where the filesystem's own
# timestamp granularity is not known


def key(path: PurePath) -> str:
    """The spelling of a file under the project that the index, git and the memory share."""
    return path.relative_to(ROOT).as_posix()


def digest(path: Path) -> str:
    HASHED[0] += 1
    sha = hashlib.sha256()
    with path.open("rb") as handle:
        seen = os.fstat(handle.fileno())  # the file as opened, before its bytes are read
        STATS[key(path)] = [seen.st_size, seen.st_mtime_ns, seen.st_ctime_ns, seen.st_ino]
        for block in iter(lambda: handle.read(1 << 20), b""):
            sha.update(block)
    return sha.hexdigest()


def moment(milliseconds: float) -> str:
    """A timestamp from the index, which records epoch milliseconds."""
    if not milliseconds:
        return "never"
    return datetime.fromtimestamp(milliseconds / 1000).strftime("%Y-%m-%d %H:%M:%S")


def listing(label: str, paths: list[str]) -> list[str]:
    lines = [f"  {len(paths)} tracked file(s) {label}:"]
    lines += [f"    - {path}" for path in sorted(paths)[:LISTED]]
    if len(paths) > LISTED:
        lines.append(f"    ... and {len(paths) - LISTED} more")
    return lines


def drift(only: set[str] | None = None, rows: dict[str, tuple[str, float]] | None = None,
          ) -> tuple[dict[str, tuple[str, float]], list[str], list[str]] | None:
    """What the index holds, and the tracked files it has never seen or read before they changed; None where
    there is no index, no `files` table to read, or no checkout to compare it with. `only` narrows the judgement to
    those paths to be *hashed*; a tracked file the index holds no row for is judged either way. With none, every
    tracked file is hashed, which is what `behind()` asks. `rows` is a read the caller already made and built its
    `only` from: it is the one read this comparison judges and returns, never a second one."""
    if not INDEX.is_file():
        return None
    if rows is None:
        rows = indexed()
    paths = tracked()
    if rows is None or paths is None:
        return None
    STATS.clear()
    # Which files belong in the index is CodeGraph's decision, not this script's: it parses the
    # languages it supports and ignores the rest. Taking the set of suffixes it has actually
    # indexed here as the answer keeps this check from inventing a language table of its own — and
    # from reporting every committed PNG as a hole in the graph.
    suffixes = {Path(path).suffix for path in rows} - {""}
    last = max((at for _, at in rows.values()), default=0.0)
    missing, changed = [], []
    for path in paths:
        if Path(path).suffix not in suffixes:
            continue
        absolute = ROOT / path
        if not absolute.is_file():
            continue
        row = rows.get(path)
        # Narrowing is of the hashing: a file with a row and no reason to be hashed is the memory's to vouch for.
        # One with no row costs a stat, not a hash, and is judged as the whole run judges it, whatever git reports.
        if row is not None and only is not None and path not in only:
            continue
        if row is None:
            # A file the index has never seen is a hole only where it appeared *after* the index last ran.
            # Matching the suffix is not enough: CodeGraph declines files of a language it indexes — a
            # vendored `bootstrap.min.js` beside a `src/app.js` it read — and which ones is its decision,
            # not this script's. Reported anyway, a real repository's vendored bundles failed a gate that
            # `codegraph sync` said was already up to date, and the two tools called each other wrong. The
            # index records milliseconds and the filesystem seconds.
            if last and absolute.stat().st_mtime * 1000 <= last:
                continue
            missing.append(path)
        elif row[0] and digest(absolute) != row[0]:
            changed.append(path)
    return rows, missing, changed


def code_index():
    """`scripts/agents/code_index.py`, loaded: the pinned route, the integrity check, the sync — without writing a
    `__pycache__/` into the project beside it."""
    sys.dont_write_bytecode = True
    specification = importlib.util.spec_from_file_location(
        "code_index", Path(__file__).resolve().parent / "agents/code_index.py")
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module




def git_output(*arguments: str) -> bytes | None:
    """What git printed for these arguments in the project, or None where it could not answer."""
    try:
        done = subprocess.run(["git", *arguments], cwd=ROOT, capture_output=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        return None
    return done.stdout


def paths_of(output: bytes | None) -> list[str] | None:
    return None if output is None else [path for path in output.decode("utf-8", "replace").split("\0") if path]


def narrowable() -> bool:
    """A developer's checkout of a `slice/<id>` branch: the one place the gate compares only what changed. The
    trunk, any other branch, a detached `HEAD` and a run under any CI marker are compared whole, as ever."""
    if any(os.environ.get(marker) for marker in CI_MARKERS):
        return False
    branch = git_output("symbolic-ref", "--short", "-q", "HEAD")
    return branch is not None and SLICE_BRANCH.match(branch.decode("utf-8", "replace").strip()) is not None


def gate_key() -> str | None:
    """A digest of this script and of the one it loads: a changed gate does not trust an older gate's memory."""
    try:
        parts = [(Path(__file__).resolve().parent / name).read_bytes()
                 for name in ("check-codegraph.py", "agents/code_index.py")]
    except OSError:
        return None
    return "-".join(hashlib.sha256(part).hexdigest() for part in parts)


def unreported() -> set[str] | None:
    """The paths git has been told not to report (`assume-unchanged`, `skip-worktree`), or None where it cannot say."""
    listed = git_output("ls-files", "-v", "-z")
    if listed is None:
        return None
    # `-v` tags a path `h` (assume-unchanged) or `S`/`s` (skip-worktree) in front of its name.
    return {entry[2:] for entry in listed.decode("utf-8", "replace").split("\0")
            if entry[:1] and (entry[0].islower() or entry[0] in "Ss")}


def files_of(rows: dict[str, tuple[str, float]], kept: dict[str, Any] | None) -> dict[str, list[float]]:
    """What the memory records of each file: the stat taken as it was hashed this run and the moment this run began;
    for a file this run did not hash, what the memory recorded of it before (a narrowed run, which stat-checked it)."""
    found = {path: [*seen, START] for path, seen in STATS.items()}
    return {path: record for path, record in {**(kept or {}), **found}.items() if path in rows}


def ignored() -> bool:
    """Whether git ignores the memory file: only then may it be written, since a record `git status` reported would
    be a change nobody made."""
    return git_output("check-ignore", "-q", "--", str(MEMORY)) is not None


def remember(rows: dict[str, tuple[str, float]], whole: float | None = None,
             kept: dict[str, Any] | None = None) -> None:
    """Record what this passing run vouched for. Never fatal: a gate that cannot take notes is merely slower."""
    # Written only where git ignores it: a record `git status` reported would be a change nobody made.
    if any(os.environ.get(marker) for marker in CI_MARKERS) or not ignored():
        return
    key, head = gate_key(), git_output("rev-parse", "HEAD")
    dirty = paths_of(git_output("diff", "--name-only", "--no-renames", "-z", "--relative", "HEAD", "--"))
    silenced = unreported()
    if key is None or head is None or dirty is None or silenced is None:
        return
    dirty = sorted({*dirty, *silenced})  # what the flag keeps out of `git diff` is dirty all the same
    try:
        record = {"key": key, "commit": head.decode().strip(), "dirty": dirty,
                  "rows": {path: found[0] for path, found in rows.items()}, "database": database_of(),
                  "files": files_of(rows, kept), "whole": time.time() if whole is None else whole}
        write(json.dumps(record))
    except OSError:
        pass


LEFTOVER = ".gate-memory-"  # the front of the name of every temporary file this gate creates, `.tmp` its end
STALE = 600  # seconds after which a temporary file of the gate's own is a run's leftover, not a run in progress


def write(text: str) -> None:
    """Replace the record with `text`, through a file this gate creates itself.

    Never through a name that is already there: the temporary file is made exclusively, under a name of its own, in
    `.codegraph/`, which git ignores; a link, a FIFO or a tracked file somebody left at any other name is not
    touched, and the record is replaced only where it is absent or a regular file. Anything else is a record that
    cannot be kept here. The temporary file does not outlive the run, whichever way it ends."""
    for old in MEMORY.parent.glob(f"{LEFTOVER}*.tmp"):  # left by a run killed between the write and the rename
        try:
            seen = old.lstat()
            if stat.S_ISREG(seen.st_mode) and time.time() - seen.st_mtime > STALE:
                old.unlink()
        except OSError:
            pass
    descriptor, name = tempfile.mkstemp(prefix=LEFTOVER, suffix=".tmp", dir=MEMORY.parent)
    beside = Path(name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(text)
        try:
            kept = stat.S_ISREG(MEMORY.lstat().st_mode)
        except FileNotFoundError:
            kept = True
        if kept and git_output("check-ignore", "-q", "--", str(beside)) is not None:
            os.replace(beside, MEMORY)
    finally:
        beside.unlink(missing_ok=True)


# Why a run on a slice branch compared everything: said once, in one clause, on the pass line.
NO_RECORD = "no earlier whole comparison is recorded"
UNKEPT = "the record cannot be kept here: git does not ignore `.codegraph/`"
NOT_A_FILE = "the record cannot be kept here: what is at its path is not a regular file"
UNREADABLE = "the record of the last whole comparison could not be read"
SCRIPTS = "the gate's scripts changed since"
COMMIT_GONE = "the commit it was taken at is gone"
OTHER_DATABASE = "the index database is not the one it was compared against"
INDEX_UNREADABLE = "the index could not be read"
GIT_SILENT = "git could not say what changed"
SHAPE = {"key": str, "commit": str, "dirty": list, "rows": dict, "database": list, "files": dict, "whole": (int, float)}


def number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def readable(record: dict[str, Any]) -> bool:
    """Whether every field is of the depth the run uses it at: a record can be the right shape and hold nonsense."""
    try:
        moment_of(float(record["whole"]))
        return (number(record["whole"]) and all(isinstance(path, str) for path in record["dirty"])
                and all(isinstance(path, str) and isinstance(digest_, str) for path, digest_ in record["rows"].items())
                and len(record["database"]) == 2 and all(type(part) is int for part in record["database"])
                and all(isinstance(path, str) and isinstance(seen, list) and len(seen) == 5
                        and all(number(part) for part in seen) and all(type(part) is int for part in seen[:4])
                        for path, seen in record["files"].items()))
    except (ArithmeticError, OSError, ValueError):
        return False


def remembered() -> dict[str, Any] | str:
    """The memory of the last whole comparison, or the reason it cannot be used."""
    try:
        regular = stat.S_ISREG(MEMORY.lstat().st_mode)
    except FileNotFoundError:
        return NO_RECORD if ignored() else UNKEPT
    except OSError:
        return UNREADABLE
    if not regular:
        return NOT_A_FILE
    try:
        record = json.loads(MEMORY.read_text(encoding="utf-8"))
    except (OSError, ValueError, RecursionError, MemoryError):
        return UNREADABLE
    if not isinstance(record, dict) or any(not isinstance(record.get(name), kind) for name, kind in SHAPE.items()):
        return UNREADABLE
    if not readable(record):
        return UNREADABLE
    if record["key"] != gate_key():
        return SCRIPTS
    commit = record["commit"]
    if not re.fullmatch(r"[0-9a-f]{40,64}", commit) or git_output("cat-file", "-e", f"{commit}^{{commit}}") is None:
        return COMMIT_GONE
    if database_of() != record["database"]:
        return OTHER_DATABASE
    return record


def candidates_of(record: dict[str, Any], rows: dict[str, tuple[str, float]]) -> set[str] | None:
    """The tracked paths a narrowed run must hash, or None where git cannot say what changed.

    What the memory cannot vouch for: whatever git reports against the commit it was taken at (committed, staged,
    unstaged, new, renamed); whatever was dirty when it was taken, since a revert is not in a diff against a commit;
    whatever git was told not to report; and every path whose row is not what was vouched for, by content."""
    changed = paths_of(git_output("diff", "--name-only", "--no-renames", "-z", "--relative", str(record["commit"]),
                                  "--"))
    silenced = unreported()
    if changed is None or silenced is None:
        return None
    vouched = record["rows"]
    moved = {path for path in rows.keys() | vouched.keys() if (rows[path][0] if path in rows else None) != vouched.get(path)}
    return {*changed, *record["dirty"], *silenced, *moved, *unvouched(record["files"], rows)}


def unvouched(files: dict[str, Any], rows: dict[str, tuple[str, float]]) -> set[str]:
    """The indexed paths whose bytes the memory cannot vouch for from the file itself: no record of how it looked when
    it was last hashed and found equal, a file that does not look so now, or one whose times are not safely older
    than the run that vouched for it (written while that run went on, and so possibly after it read it)."""
    answer = set()
    for path in rows:
        recorded = files.get(path)
        try:
            now = (ROOT / path).stat()
        except OSError:
            now = None
        if (recorded is None or now is None
                or recorded[:4] != [now.st_size, now.st_mtime_ns, now.st_ctime_ns, now.st_ino]
                or max(now.st_mtime_ns, now.st_ctime_ns) + SAFELY * 1e9 > recorded[4] * 1e9):
            answer.add(path)
    return answer


def database_of() -> list[int] | None:
    """Which file the index is: another one, or a rebuilt one, is never one the memory vouched for."""
    try:
        stat = INDEX.stat()
    except OSError:
        return None
    return [stat.st_dev, stat.st_ino]


def moment_of(seconds: float) -> str:
    return moment(seconds * 1000)


MOVING = "the index changed while it was being read"


def read_once(record: dict[str, Any]) -> tuple[dict[str, tuple[str, float]], set[str]] | str:
    """One read of the index's rows and the candidates built from that read, or the reason there is none. The rows
    are read again after the candidates are: a read that differs is one something wrote to while git was asked, so it
    is made again, and an index that will not hold still is not narrowed."""
    for _ in range(3):
        rows = indexed()
        if rows is None:
            return INDEX_UNREADABLE
        candidates = candidates_of(record, rows)
        if candidates is None:
            return GIT_SILENT
        if indexed() == rows:
            return rows, candidates
    return MOVING


def narrowed(tooling: Any, record: dict[str, Any]) -> int | str:
    """The comparison of a `slice/<id>` branch: only the candidates are hashed. A reason where it cannot be made."""
    read = read_once(record)
    if isinstance(read, str):
        return read
    rows, candidates = read
    repairing = os.environ.get("CODEGRAPH_GATE_NO_SYNC") != "1" and tooling.route() is not None
    HASHED[0] = 0
    found = drift(candidates, rows)
    assert found is not None
    synced = ""
    if (found[1] or found[2]) and repairing:
        done, said = tooling.cli("sync", ".")
        synced = (f"synced {len(found[1]) + len(found[2])} file(s) first; " if done
                  else f"`codegraph sync` did not take ({said}); ")
        read = read_once(record)
        if isinstance(read, str):
            return read
        rows, candidates = read
        HASHED[0] = 0
        found = drift(candidates, rows)
        assert found is not None
    return conclude(found, synced, f"hashed {HASHED[0]} of {len(found[0])} file(s), only what changed since the "
                    f"last whole comparison ({moment_of(float(record['whole']))}); the integrity check was not "
                    "run here: it runs on the trunk, on any other branch and in CI", float(record["whole"]), kept=record["files"])


def conclude(found: tuple[dict[str, tuple[str, float]], list[str], list[str]], synced: str, said: str,
             whole: float | None = None, clause: str = "", kept: dict[str, Any] | None = None) -> int:
    """The verdict on a comparison, and the memory a pass leaves behind."""
    rows, missing, changed = found
    paths = tracked() or []
    last = max((at for _, at in rows.values()), default=0.0)
    # An index holding nothing describes nothing, and cannot say which files it should hold — the
    # suffixes above come from what it has read. In a checkout with tracked files that is the same
    # failure as a missing one, reported rather than passed for want of anything to compare.
    if not rows and paths:
        print("check-codegraph: the code index holds no files at all — it was emptied, or "
              "nothing ever finished indexing\n", file=sys.stderr)
        print(RESTORE, file=sys.stderr)
        return 1
    if not missing and not changed:
        print(f"check-codegraph: {synced}index current — {said or f'{len(rows)} file(s), indexed {moment(last)}'}{clause}")
        remember(rows, whole, kept)
        return 0
    report = [f"check-codegraph: {synced}the code index no longer describes this working tree",
              f"  last indexed: {moment(last)}"]
    if missing:
        report += listing("the index has never seen", missing)
    if changed:
        report += listing("changed since they were indexed", changed)
    print("\n".join([*report, "", RESTORE]), file=sys.stderr)
    return 1


def whole(tooling: Any, why: str | None = None) -> int:
    """Every tracked file compared, the integrity check run and a corrupt index repaired: today's gate. On a slice
    branch that could have compared less, `why` is said after the pass line."""
    try:
        problem = tooling.damage()
    except tooling.Unopened as error:
        print(f"check-codegraph: .codegraph/codegraph.db could not be opened to be checked ({error}). That is "
              "this environment's SQLite or the directory's permissions, not damage, so the database was left "
              "alone; `codegraph status` says whether the index itself is current", file=sys.stderr)
        return 1
    repairing = os.environ.get("CODEGRAPH_GATE_NO_SYNC") != "1" and tooling.route() is not None
    repaired = ""
    if problem is not None and repairing:
        # Derived from the source and ignored by Git: a corrupt database loses nothing by being rebuilt, so the
        # gate rebuilds it and judges what that leaves, rather than failing every `make verify` until a person does.
        said = tooling.health()
        problem = None if said.get("state") != "failed" else f"{problem}; the rebuild failed too: {said['detail']}"
        repaired = f"rebuilt a corrupt database first ({said.get('seconds', 0)}s); "
    if problem is not None:
        print(f"check-codegraph: .codegraph/codegraph.db fails SQLite's integrity check ({problem}). "
              "CodeGraph's own `status` and `sync` do not notice this; its queries fail. The database is "
              "derived from the source and ignored by Git, so nothing is lost by rebuilding it: "
              "`python3 scripts/agents/code_index.py health` moves it aside and rebuilds it (a /cruise "
              "runner does that before every iteration)", file=sys.stderr)
        return 1
    if indexed() is None:
        print("check-codegraph: .codegraph/codegraph.db does not carry the `files` table this "
              "check reads; CodeGraph's schema may have moved on — skipped")
        return 0
    if tracked() is None:
        print("check-codegraph: not a checkout — nothing to compare the index against; skipped")
        return 0
    found = drift()
    assert found is not None
    synced = repaired
    if (found[1] or found[2]) and repairing:
        done, said = tooling.cli("sync", ".")
        synced += (f"synced {len(found[1]) + len(found[2])} file(s) first; " if done
                  else f"`codegraph sync` did not take ({said}); ")
        found = drift()
        assert found is not None
    return conclude(found, synced, "", clause=f" (compared everything: {why})" if why else "")


def main() -> int:
    if not INDEX.is_file():
        print("check-codegraph: no .codegraph/ — this project carries no code index; nothing to "
              "check")
        return 0
    tooling = code_index()
    why = None
    if narrowable():
        try:
            record = remembered()
            done = narrowed(tooling, record) if isinstance(record, dict) else record
        except Exception:  # noqa: BLE001 — whatever the memory held, reading it or using it, it is the whole run
            done = UNREADABLE
        if isinstance(done, int):
            return done
        why = done
    return whole(tooling, why)


if __name__ == "__main__":
    raise SystemExit(main())
