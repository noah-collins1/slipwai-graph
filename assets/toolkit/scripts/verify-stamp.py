#!/usr/bin/env python3
"""Say whether this tree already passed the gate, and record that it did: `reuse` and `record`.

`make verify` asks `reuse` first. It exits 0 only after printing the one line that says the full gate did not run
because this tree already passed it; any other answer — no stamp, a stamp for another key, anything this script cannot
read — exits non-zero, and the recipe runs every check. After the checks passed, `record` writes the stamp: a JSON
file under the git directory, never in the working tree, holding the key the tree had when the checks began. Nothing
here can fail the gate: `reuse` exits 0 only after printing its line, and `record` always exits 0.

The key is one SHA-256 over named parts, each a digest of its own so the stamp can show them apart. It starts the
way a tree is judged — every file git tracks and every file it does not ignore, for the whole repository, and every
file under the project's directory that git ignores except a closed exempt list, by raw bytes, executable bit and a
link's target, read from the working tree through no filter, and the index's entries — where the checkout stands
in its repository: `HEAD`, every ref git lists, the shallow boundary and the repository's configuration — and, as a
part of its own, the `Makefile` and the scripts the gate runs from. The parts a later rule adds are named where they
join.

Starts on any `python3`: nothing here is newer than the syntax the gate's `check-python` message is printed from,
and an interpreter older than 3.10 answers "no stamp" before it reads anything.
"""
from __future__ import annotations

import fnmatch
import hashlib
import importlib.util
import json
import os
import re
import secrets
import stat
import subprocess
import sys
import tempfile
import time
from collections.abc import Mapping
from typing import Any

# What is persisted under the git directory is a closed set of fields — the stamp's own, and the note's: the key, the
# tools' lines, or `NOTHING` as a marker that the run records nothing. Free text, and so a path, is printed, not stored.
# The stamp's fields: the key a later run compares, the three parts it is made of, the instant of the pass, and
# the result, which is only ever a pass.
FIELDS = ("key", "tree", "scripts", "tools", "passed", "result")
# The two closed lists. What the key leaves out of the files under the project that git ignores, each entry with the
# reason it is left out; and the variables a check reads that can change its answer, by value (unset is not empty).
# Everything else under the project's directory is in the key by its bytes, whatever makes git ignore it — a committed
# pattern, `.git/info/exclude`, a user's excludes file — and an ignored directory nobody listed is hashed whole. A
# test fails when a check script reads a path under an entry outside its exceptions. An entry is a name that matches
# at any depth (`__pycache__/` a directory, `*.pyc` a file) or, with a `/` inside it, a path from the project's
# directory; a `*` is one level of names. Its exceptions are paths inside the directory it matches that stay in the key.
REBUILT = "rebuilt"
CACHE = "cache"
RECORD = "record"
REASONS = {
    REBUILT: "the gate's own recipe rebuilds it from a committed lock or source on every run",
    CACHE: "a cache or an output a tool writes, which no check reads as an input",
    RECORD: "a record the gate or the runner writes about itself",
}
EXEMPT: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    # `uv sync --locked` runs before every phase; the interpreter's version is in the tools
    (".venv/", REBUILT, ()),
    # `build-packages`, a prerequisite of lint, typecheck and test, rebuilds the packages' output and the typed client
    ("dist/", REBUILT, ()),
    ("packages/api-client/src/schema.ts", REBUILT, ()),
    # the recipe's `go test` writes it just before `go-coverage.py` reads it; Maven's output is rebuilt by every
    # compile and test the recipe runs, and the flattened pom by every build
    ("coverage.out", REBUILT, ()),
    ("target/", REBUILT, ()),
    (".flattened-pom.xml", REBUILT, ()),
    # bytecode and the tools' caches: nothing a source does not say
    ("__pycache__/", CACHE, ()),
    ("*.pyc", CACHE, ()),
    (".pytest_cache/", CACHE, ()),
    (".ruff_cache/", CACHE, ()),
    (".mypy_cache/", CACHE, ()),
    (".coverage", CACHE, ()),
    ("*.tsbuildinfo", CACHE, ()),
    ("coverage/", CACHE, ()),
    # what npm installs, which the recipe installs only when the lock is newer: the manifest npm wrote of what is
    # installed stays in the key, and `check-model` reads nothing else of it
    ("node_modules/", CACHE, (".package-lock.json",)),
    # written by `make build`, `make mutation` and `make deploy`, which the gate does not run
    (".build/", CACHE, ()),
    ("apps/*/requirements.txt", CACHE, ()),
    ("gremlins.json", CACHE, ()),
    # Stryker's sandbox (`make mutation` removes it, and a killed run leaves it) and the report a TypeScript service writes
    (".stryker-tmp/", CACHE, ()),
    ("apps/*/reports/mutation/", CACHE, ()),
    # mutmut's copy of a Python service's `src/` and `tests/`, its `.meta` files and `mutmut-stats.json`, which
    # `make mutation` removes and writes again on every run
    ("apps/*/mutants/", CACHE, ()),
    (".terraform/", CACHE, ()),
    ("*.tfplan", CACHE, ()),
    ("terraform.tfstate.backup", CACHE, ()),
    # the data a service writes at run time, the Spec Kit installer's tooling, and what `make model` renders (the gate
    # reads `model.yaml` and the committed `model.drawio`)
    ("*.sqlite3", CACHE, ()),
    ("*.sqlite3-wal", CACHE, ()),
    ("*.sqlite3-shm", CACHE, ()),
    (".specify-tools/", CACHE, ()),
    ("scripts/event-model/.mermaid-cli/", CACHE, ()),
    ("docs/event-model/model.mmd", CACHE, ()),
    ("docs/event-model/model.svg", CACHE, ()),
    ("docs/event-model/model.png", CACHE, ()),
    ("docs/event-model/model.html", CACHE, ()),
    ("docs/event-model/slices/", CACHE, ()),
    ("docs/event-model/segments/", CACHE, ()),
    # the code index's own files, of which `check-codegraph` reads the database and the write-ahead file beside it and
    # writes `gate-memory.json`, its memo of itself, on every pass
    (".codegraph/", RECORD, ("codegraph.db", "codegraph.db-wal")),
    # what a factory command leaves for a person, and the state of `/cruise`, which only its runner reads
    (".slipwai/catch-up.md", RECORD, ()),
    ("specs/cruise-checkpoint.md", RECORD, ()),
    (".specify/cruise.stop", RECORD, ()),
    (".specify/cruise.pid", RECORD, ()),
    (".specify/cruise-run.log", RECORD, ()),
    (".specify/cruise-stream.jsonl", RECORD, ()),
    (".specify/cruise-watch.cursor", RECORD, ()),
    (".specify/cruise-last-response.txt", RECORD, ()),
    (".specify/cruise-inbox.jsonl", RECORD, ()),
    (".specify/cruise-told.jsonl", RECORD, ()),
)
VARIABLES: tuple[str, ...] = (
    "UX_GATES_REQUIRE", "UX_GATES_SINCE", "UX_GATES_SHARD", "CODEGRAPH_GATE_NO_SYNC", "SLIPWAI_NO_INSTALL",
    "GITHUB_HEAD_REF", "CI_COMMIT_REF_NAME",
    # `check-slice-scope`'s pull-request target, and the harness the extensions' projections are compared for
    "GITHUB_BASE_REF", "CI_MERGE_REQUEST_TARGET_BRANCH_NAME", "SLIPWAI_INTEGRATION",
)
# Read by a check and not in the key: how many run at once is not what they say.
UNKEYED_VARIABLES = ("UX_GATES_JOBS",)
RATCHET_VARIABLE = "RATCHET_TIGHTEN"
# A run is a CI run when any of these is non-empty — `CI=false` included, the way `check-codegraph` and
# `check-slice-scope` read them (D32).
CI_MARKERS = ("CI", "GITHUB_ACTIONS", "GITLAB_CI")
SLICE_SCOPE = "check-slice-scope.py"

# How long a version question may take, and the one argument that is not `--version` for the tools that spell it
# otherwise (`java -version` answers on standard error, which the answer is read from too).
ASK_TIMEOUT = 5
# What of a tool's answer is stored: the words that are version-shaped — digits and dots, with at most a short suffix
# (`2.43.0`, `v20.11.0`, `1.0-rc1`) — and nothing else. A path, a host name, a user name and a process id are words of
# the tool's own, and the stamp is shared state a person may copy: it holds none (the constitution's persisted data).
VERSION_WORD = re.compile(r"v?[0-9]+(?:\.[0-9]+)+(?:[-+_]?[A-Za-z]{1,6}[0-9]{0,3})?")
SHOWN_WORDS = 4
VERSION_ARGUMENTS = {"go": "version", "java": "-version"}
CANNOT_LINE = "verify: the full gate runs and this run records nothing — {reason}"
# The instant of a pass exactly as `record` writes it and the reuse line prints it: UTC, to the second.
INSTANT = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z")
NOTHING = "nothing"
FORCE_VARIABLE = "VERIFY_FORCE"
FORCED_LINE = "verify: the full gate runs, forced by {reason}"
NOT_RECORDED_LINE = "verify: this pass was not recorded — {reason}"
# make's flags under which no check starts: nothing is read, written or removed. `-i` is not among them: it starts
# every check and lets one fail, so it is `declined` for the stamp but removes the one that stood.
IDLE_FLAGS = "ntq"
DECLINING_FLAGS = IDLE_FLAGS + "i"
REUSE_LINE = (
    "verify: the full gate did not run; this tree already passed it at {passed} (key {abbreviated}); "
    "VERIFY_FORCE=1 runs it anyway"
)


class CannotTell(Exception):
    """The key cannot be built; the full gate runs."""


class CannotAsk(CannotTell):
    """A part of the key that is read from the machine cannot be: the full gate runs, one line says why, and the run
    records nothing."""


class Options:
    """What the recipe hands the script: the command `make` was run as, each tool to ask the version of, and each
    Python environment whose interpreter is read from where `uv sync` wrote it."""

    def __init__(self, argv: list[str]) -> None:
        self.make = "make"
        self.token = ""
        self.tools: list[str] = []
        self.environments: list[str] = []
        pairs = {"--make": "make", "--tool": "tools", "--environment": "environments",
                 "--token": "token"}
        for flag, value in zip(argv, argv[1:]):
            name = pairs.get(flag)
            if name == "make":
                self.make = value or "make"
            elif name == "token":
                self.token = value
            elif name is not None:
                getattr(self, name).append(value)


def reason_of(stderr: bytes) -> str:
    """Git's reason on a line: the first of its lines that is not empty, with control characters escaped, so that a
    reason of several lines is one line and a word of git's cannot forge another."""
    for line in stderr.decode("utf-8", "replace").splitlines():
        if line.strip():
            return shown(line)
    return ""


def git(*args: str) -> bytes:
    try:
        done = subprocess.run(["git", *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    except FileNotFoundError:
        raise CannotTell("git is not on PATH")
    except OSError as error:
        raise CannotTell("git cannot be started (" + shown(str(error)) + ")")
    if done.returncode != 0:
        raise CannotTell("git " + " ".join(args) + ": " + reason_of(done.stderr))
    return done.stdout


def git_or_nothing(*args: str) -> bytes:
    """What a `-q` question of git answers, or nothing where git says no without a reason: a detached `HEAD` has no
    branch and an unborn branch no commit, and neither is a failure."""
    try:
        done = subprocess.run(["git", *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    except FileNotFoundError:
        raise CannotTell("git is not on PATH")
    except OSError as error:
        raise CannotTell("git cannot be started (" + shown(str(error)) + ")")
    if done.returncode == 1 and not done.stderr:
        return b""
    if done.returncode != 0:
        raise CannotTell("git " + " ".join(args) + ": " + reason_of(done.stderr))
    return done.stdout


def digest(parts: list[bytes]) -> str:
    """One SHA-256 over length-prefixed parts, so no two lists of parts make the same digest."""
    whole = hashlib.sha256()
    for part in parts:
        whole.update(str(len(part)).encode("ascii") + b":" + part)
    return whole.hexdigest()


def shown(path: bytes | str) -> str:
    """A path as a line may carry it: control characters escaped, so a name cannot forge a line."""
    text = os.fsdecode(path)
    return "".join(char if char.isprintable() else char.encode("unicode_escape").decode("ascii") for char in text)


def top_level() -> str:
    """The repository's work tree, where git is asked about the whole of it."""
    return os.fsdecode(git("rev-parse", "--show-toplevel").removesuffix(b"\n"))


def project_prefix() -> bytes:
    """Where this project sits in its repository, from the top, as git writes it: empty at the top, else ending in `/`."""
    return git("rev-parse", "--show-prefix").removesuffix(b"\n")


def covered_files(top: str) -> list[bytes]:
    """Every file the gate judges that git lists, from the top of the whole repository: tracked, and untracked where git
    does not ignore it. An untracked directory that is itself a repository is listed as one entry ending in `/`, and
    the files in it are not listed: the key cannot vouch for them."""
    listed = git("-C", top, "ls-files", "-z", "--cached", "--others", "--exclude-standard")
    paths = sorted(set(path for path in listed.split(b"\0") if path))
    for path in paths:
        if path.endswith(b"/"):
            raise CannotTell(shown(path) + " is an untracked directory that is itself a repository")
    return paths


def index_problem(top: str) -> str | None:
    """Why the index cannot vouch for the working tree, or None: an entry marked `assume-unchanged` (git does not look
    at it) or `skip-worktree`, or a submodule (an entry of mode 160000, a repository the key does not read). `ls-files
    -v` tags an `assume-unchanged` entry with a lower-case letter and a `skip-worktree` one with `S`; both it and
    `--stage` read the index and never write it."""
    marks = [(record[:1].decode("ascii", "replace"), record[2:]) for record in
             git("-C", top, "ls-files", "-v", "-z").split(b"\0") if record]
    for tag, path in marks:
        if tag.islower():
            return shown(path) + " is marked assume-unchanged, so git does not look at it"
    for tag, path in marks:
        if tag == "S":
            return shown(path) + " is marked skip-worktree, so git does not look at it"
    for record in index_entries(top).split(b"\0"):
        if record.startswith(b"160000 "):
            return shown(record.partition(b"\t")[2]) + " is a submodule (an index entry of mode 160000)"
    return None


def not_vouched() -> str | None:
    """Why the stamp will not vouch for this tree: `index_problem` of the repository's top level, or why that cannot be
    asked. The one predicate `reuse` and the scoped gate's border both take, so the two cannot come to different
    answers about an index."""
    try:
        return index_problem(top_level())
    except CannotTell as reason:
        return str(reason)


def file_record(path: bytes, top: str) -> bytes:
    """One covered file as the key sees it, whatever it is: a regular file by its executable bit and the SHA-256 of
    its raw bytes, a link by its target as written and never followed, a file that is not there as missing. `path` is
    from the top of the repository, which is where it is read from, with `lstat` and `open`, through none of git's
    filters and none of its stat shortcuts."""
    place = os.path.join(os.fsencode(top), path)
    try:
        status = os.lstat(place)
        if stat.S_ISLNK(status.st_mode):
            return path + b"\0link\0" + os.readlink(place)
        if not stat.S_ISREG(status.st_mode):
            raise CannotTell(shown(path) + " is neither a file nor a link")
        with open(place, "rb") as handle:
            content = hashlib.sha256(handle.read()).hexdigest().encode("ascii")
    except FileNotFoundError:
        return path + b"\0missing"
    except OSError as error:
        raise CannotTell("cannot read " + shown(path) + " (" + (error.strerror or str(error)) + ")")
    return path + b"\0" + (b"exec" if status.st_mode & stat.S_IXUSR else b"file") + b"\0" + content


def directory_match(segments: list[str], names: list[str], directories: int) -> int | None:
    """Where an entry's directory names end in a path whose first `directories` names are directories: after the first
    directory that matches a lone name (at any depth), or after the leading names where there are several (from the
    project's directory); None where they do not."""
    if len(names) == 1:
        for index in range(directories):
            if fnmatch.fnmatchcase(segments[index], names[0]):
                return index + 1
        return None
    if len(names) <= directories and all(fnmatch.fnmatchcase(seg, name) for seg, name in zip(segments, names)):
        return len(names)
    return None


def exempt_entry(relative: str) -> tuple[str, str, tuple[str, ...]] | None:
    """The `EXEMPT` entry that leaves the path out of the key, or None where it stays in: `relative` is from the
    project's directory with `/` between names, and ends in `/` where it is a directory. A path that is one of an
    entry's exceptions, or inside one, is not left out by that entry."""
    segments = relative.rstrip("/").split("/")
    is_directory = relative.endswith("/")
    for entry in EXEMPT:
        pattern, _, exceptions = entry
        names = pattern.rstrip("/").split("/")
        if pattern.endswith("/"):
            end = directory_match(segments, names, len(segments) if is_directory else len(segments) - 1)
            inside = segments[end:] if end is not None else []
            if end is None or any(inside[: len(kept.split("/"))] == kept.split("/") for kept in exceptions):
                continue
            return entry
        tail = segments[-1:] if len(names) == 1 else segments
        if not is_directory and len(tail) == len(names) and all(
                fnmatch.fnmatchcase(seg, name) for seg, name in zip(tail, names)):
            return entry
    return None


def tree_records(path: str, top: str, prefix: bytes, listed: set[bytes]) -> list[bytes]:
    """Every file and link under `path` (a name from the project's directory) that git does not list, by its record,
    pruned where the exempt list says; nothing is followed, so a link is its target. A directory that is itself a
    repository, outside the list, is a part of the key that cannot be read."""
    project = os.path.join(top, os.fsdecode(prefix))
    here = os.path.join(project, path) if path else project
    try:
        names = sorted(os.listdir(here))
    except OSError as error:
        raise CannotTell("cannot read " + shown(here) + " (" + (error.strerror or str(error)) + ")")
    records: list[bytes] = []
    for name in names:
        relative = path + "/" + name if path else name
        if not path and name == ".git":
            continue
        place = os.path.join(project, relative)
        from_top = prefix + os.fsencode(relative)
        if os.path.islink(place) or not os.path.isdir(place):
            if from_top not in listed and exempt_entry(relative) is None:
                records.append(file_record(from_top, top))
            continue
        entry = exempt_entry(relative + "/")
        if entry is not None:
            for exception in entry[2]:
                kept = from_top + b"/" + os.fsencode(exception)
                if os.path.lexists(os.path.join(place, exception)) and kept not in listed:
                    records.append(file_record(kept, top))
            continue
        if os.path.lexists(os.path.join(place, ".git")):
            raise CannotTell(shown(relative) + "/ is an ignored directory that is itself a repository")
        records.extend(tree_records(relative, top, prefix, listed))
    return records


def variable_record(name: str) -> bytes:
    """A variable by its value, with unset told from empty."""
    value = os.environ.get(name)
    return name.encode("utf-8") + (b"\0unset" if value is None else b"\0set\0" + os.fsencode(value))


def index_entries(top: str) -> bytes:
    """The index's entries — mode, blob id, stage, name — as `ls-files --stage` lists them for the whole repository,
    which reads the index and never writes it."""
    return git("-C", top, "ls-files", "-z", "--stage")


def file_bytes(path: str) -> bytes:
    """What a file git names holds, or its absence, which is a value of its own."""
    if os.path.exists(path):
        with open(path, "rb") as handle:
            return b"present\0" + handle.read()
    return b"absent"


def history_digest() -> str:
    """Where the checkout stands in its repository, and how git is told to read it: the branch `HEAD` names (nothing
    where it is detached) and the commit it names (nothing on an unborn branch), every ref git lists with what it names
    — branches, remote-tracking refs, tags, replace refs, notes, the stash — the shallow boundary, and the bytes of
    the repository's configuration file and the worktree's. Each is the bytes of the file git names for it, or their
    absence."""
    refs = git("for-each-ref", "--format=%(objectname) %(refname)")
    named = [git("rev-parse", "--git-path", name).decode("utf-8", "surrogateescape").removesuffix("\n")
             for name in ("shallow", "config", "config.worktree")]
    return digest([
        git_or_nothing("symbolic-ref", "-q", "HEAD"), git_or_nothing("rev-parse", "-q", "--verify", "HEAD"), refs,
        *[file_bytes(path) for path in named],
    ])


def java_command() -> str:
    """The JVM the Maven wrapper runs: `JAVA_HOME`'s where that variable is non-empty (the wrapper's own choice, the AIX
    layout first), else the `java` on `PATH`. The variable's value is a path to a directory and is never in the key or
    the stamp: what is keyed is the answer the JVM gives."""
    home = os.environ.get("JAVA_HOME", "")
    if not home:
        return "java"
    aix = os.path.join(home, "jre", "sh", "java")
    return aix if os.access(aix, os.X_OK) else os.path.join(home, "bin", "java")


def stored_answer(printed: list[bytes]) -> str:
    """What the stamp stores of a tool's answer: the version-shaped words, as the tool printed them on either stream
    (the first few, each once), then the digest of the whole answer; the digest alone where there is no such word. The
    key holds the digest, so nothing narrowed here narrows what moves it (D80)."""
    words: list[str] = []
    for stream in printed:
        for word in stream.decode("utf-8", "replace").split():
            word = word.strip("\"'()[]<>;:")
            if VERSION_WORD.fullmatch(word) and word not in words:
                words.append(word)
    return " ".join(words[:SHOWN_WORDS] + ["[answer " + digest(printed)[:16] + "]"])


def ask(tool: str, command: str) -> str:
    """What the key holds of a tool: the digest of everything it printed when asked its version, on both streams, so a
    notice ahead of the version cannot hide a changed one (D80), behind the version-shaped words a person is shown
    (`stored_answer`); no other word of the answer is kept. Launched once, with no standard input, its output read from
    files so that nothing it leaves running can hold this script."""
    argument = VERSION_ARGUMENTS.get(tool, "--version")
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        try:
            child = subprocess.Popen([command, argument], stdin=subprocess.DEVNULL, stdout=out, stderr=err)
        except FileNotFoundError:
            raise CannotAsk(tool + (" is not where JAVA_HOME names it" if tool == "java" and command != tool
                                    else " is not on PATH"))
        except OSError as error:
            raise CannotAsk(tool + " cannot be started (" + shown(str(error)) + ")")
        try:
            code = child.wait(timeout=ASK_TIMEOUT)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait()
            raise CannotAsk(tool + " did not answer within " + str(ASK_TIMEOUT) + " seconds when asked its version")
        out.seek(0)
        err.seek(0)
        printed = [out.read(), err.read()]
    if code != 0:
        raise CannotAsk(tool + " exited " + str(code) + " when asked its version")
    if any(line.strip() for stream in printed for line in stream.decode("utf-8", "replace").splitlines()):
        return stored_answer(printed)
    raise CannotAsk(tool + " printed nothing when asked its version")


def interpreter(environment: str) -> str:
    """The Python an environment was made with, as `pyvenv.cfg` records it, read without launching anything."""
    path = os.path.join(environment, "pyvenv.cfg")
    try:
        with open(path, "r", encoding="utf-8") as handle:
            lines = handle.read().splitlines()
    except OSError as error:
        raise CannotAsk("cannot read " + shown(path) + " (" + (error.strerror or str(error)) + ")")
    for line in lines:
        name, _, value = line.partition("=")
        if name.strip() == "version_info" and value.strip():
            return value.strip()
    raise CannotAsk(shown(path) + " does not record the interpreter's version_info")


def machine_tools(options: Options) -> dict[str, str]:
    """Every tool the machine supplies that the key holds, by the line it reported, and each environment's interpreter.
    The recipe names them; this script holds no list of its own."""
    tools = {}
    for tool in options.tools:
        tools[tool] = ask(tool, options.make if tool == "make" else java_command() if tool == "java" else tool)
    for environment in options.environments:
        tools["interpreter " + environment] = interpreter(environment)
    return tools


def is_gate_script(path: bytes) -> bool:
    """The `Makefile` and everything covered under `scripts/`, at any depth: what the gate runs from. `path` is from the
    project's directory."""
    return path == b"Makefile" or path.startswith(b"scripts/")


def key_parts(tools: dict[str, str]) -> tuple[dict[str, object], dict[str, str]]:
    """The key and the digests it is made of, so a run can say which part moved. Each part of the stamp is a digest of
    its own, so the stamp shows them apart: `tree` is every file git lists for the whole repository, every file under
    the project's directory that git ignores except what the exempt list leaves out, the index, the history and the
    variables; `scripts` is the covered files the gate runs from, which `tree` holds as well. Each file is read once.
    `tools` is what the machine reported, asked once per run. The second value is what `reuse` keeps for `record`:
    digests of the parts, never a name of a file."""
    top, prefix = top_level(), project_prefix()
    listed = covered_files(top)
    records = [(path, file_record(path, top)) for path in listed]
    ignored = digest(tree_records("", top, prefix, set(listed)))
    variables = digest([variable_record(name) for name in VARIABLES])
    index, history = index_entries(top), history_digest()
    parts = {
        "history": history, "index": digest([index]), "ignored": ignored, "variables": variables,
        "files": digest([record for _, record in records]),
        "scripts": digest([record for path, record in records
                           if path.startswith(prefix) and is_gate_script(path[len(prefix):])]),
    }
    tree = digest(
        [history.encode("ascii"), index, ignored.encode("ascii"), variables.encode("ascii")]
        + [record for _, record in records])
    key = digest([
        tree.encode("ascii"), parts["scripts"].encode("ascii"), json.dumps(tools, sort_keys=True).encode("utf-8")])
    return {"key": key, "tree": tree, "scripts": parts["scripts"], "tools": tools}, parts


def build_key(tools: dict[str, str]) -> dict[str, object]:
    return key_parts(tools)[0]


def stamp_directory() -> str:
    """Under the git directory, whose name is git's answer with exactly one line feed taken off and nothing else: a name
    that ends or begins in whitespace is its own."""
    return os.path.join(os.fsdecode(git("rev-parse", "--absolute-git-dir").removesuffix(b"\n")), "slipwai")


def project_name() -> str:
    """Which project of the repository this is: a digest of where it sits, so the file holds no path."""
    return hashlib.sha256(project_prefix()).hexdigest()[:16]


def stamp_path() -> str:
    return os.path.join(stamp_directory(), "verify-stamp-" + project_name() + ".json")


def pending_path() -> str:
    return os.path.join(stamp_directory(), "verify-stamp-" + project_name() + ".pending")


def baseline_path() -> str:
    """What a scoped run compares the machine with: beside the stamp, under the same project's name."""
    return os.path.join(stamp_directory(), "verify-baseline-" + project_name() + ".json")


def read_own(path: str) -> str | None:
    """The text of one of this script's own files, or None where it is not there or is anything but a regular file in
    a real directory: a link is never followed, a directory or a FIFO is never opened (a FIFO would wait for a writer),
    and a link where the directory should be is no directory. Read through a descriptor opened without following."""
    try:
        if os.path.islink(os.path.dirname(path)) or not stat.S_ISREG(os.lstat(path).st_mode):
            return None
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
    except OSError:
        return None
    with os.fdopen(descriptor, "r", encoding="utf-8") as handle:
        try:
            return handle.read() if stat.S_ISREG(os.fstat(handle.fileno()).st_mode) else None
        except (OSError, ValueError):
            return None


def read_stamp(path: str) -> dict[str, object] | None:
    """The stamp, or None where there is none, it cannot be parsed, or it lacks a field."""
    text = read_own(path)
    if text is None:
        return None
    try:
        stamp = json.loads(text)
    except ValueError:
        return None
    if not isinstance(stamp, dict) or any(field not in stamp for field in FIELDS) or stamp["result"] != "pass":
        return None
    passed = stamp["passed"]
    if not isinstance(passed, str) or not INSTANT.fullmatch(passed):
        return None  # a stamp is shown by its instant, so an instant that is not the shape `record` writes is no stamp
    return stamp


def ensure_directory(directory: str) -> None:
    """The factory's own directory under the git directory, a real one: a link in its place is removed as itself (what
    it points to is left alone) and a directory made; anything else that stands there makes `makedirs` fail."""
    if os.path.islink(directory):
        os.remove(directory)
    os.makedirs(directory, exist_ok=True)


def write_file(path: str, text: str) -> None:
    """A finished file or none: written to a file of its own beside its name, made new (never an existing path, so a
    link cannot be written through), then renamed onto it — which replaces a link as itself and never follows it."""
    directory = os.path.dirname(path)
    ensure_directory(directory)
    descriptor, temporary = tempfile.mkstemp(dir=directory, prefix=os.path.basename(path) + ".", suffix=".tmp")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.replace(temporary, path)
    except BaseException:
        try:
            os.remove(temporary)
        except OSError:
            pass
        raise


def trunk_module() -> Any:
    """`check-slice-scope.py` beside this script, loaded, never copied: the one definition of the trunk, so the two cannot
    come to different answers."""
    spec = importlib.util.spec_from_file_location(
        "check_slice_scope_for_the_stamp", os.path.join(os.path.dirname(os.path.abspath(__file__)), SLICE_SCOPE))
    if spec is None or spec.loader is None:
        raise CannotTell("cannot load " + SLICE_SCOPE)
    module = importlib.util.module_from_spec(spec)
    was, sys.dont_write_bytecode = sys.dont_write_bytecode, True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = was
    return module


TRUNK_FIX = "record `ci.branch` in project.json, or fetch the trunk"


def trunk_problem() -> tuple[str, str | None]:
    """The trunk's name, and why this run cannot tell which branch is the trunk, or None where it can: `project.json` is missing, unreadable or
    not an object; it records a `ci.branch` that is not the trunk the gate resolves (not a string, not a branch name, a
    slice branch, another case, no branch here, whatever the reason); or the name the trunk resolves to has no ref. The
    trunk is resolved by `merge_base` of `check-slice-scope.py` in `Base.named` and never in `Base.trunk`, which is the
    name a pull request's target may have taken (a usable `ci.branch` that has a ref, else `main` where it has one,
    else `master`). A `ci.branch` simply not recorded, with `main` or `master` present, is no problem (D81)."""
    module = trunk_module()
    record = module.read_json(module.ROOT / "project.json")
    if not isinstance(record, dict):
        return "", "project.json is missing, unreadable or not a JSON object; " + TRUNK_FIX
    ci = record.get("ci")
    value = ci.get("branch") if isinstance(ci, dict) else None
    named = str(module.merge_base().named)
    if ci is not None and not isinstance(ci, dict):
        return named, "project.json records ci as something other than an object; " + TRUNK_FIX
    if value is not None and module.usable(value) != named:
        what = "`" + shown(value)[:80] + "`" if isinstance(value, str) else "something that is not a string"
        return named, ("project.json records ci.branch as " + what + ", which is not the trunk the gate resolves (`"
                       + shown(named)[:80] + "`); " + TRUNK_FIX)
    if not module.bases_of(named)[0]:
        return named, "no branch named `" + shown(named)[:80] + "` has a ref here; " + TRUNK_FIX
    return named, None


def standing() -> tuple[bool, str | None]:
    """Whether a stamp may be used at all on this run, and the one line to say first where it cannot be told. The
    questions are asked in this order: a CI marker; a `HEAD` that names no commit or is a symbolic ref outside
    `refs/heads` or is detached (all silent); whether the trunk can be told (the line); and then whether this is the
    trunk (silent). Where a stamp may not be used a run reads nothing, writes nothing, removes nothing — it is the gate
    as it was, with the line where there is one. Asked by both verbs, so a `record` that follows a run that could not
    read writes nothing either."""
    if any(os.environ.get(marker) for marker in CI_MARKERS):
        return False, None
    # the full ref name, never `--short`: git shortens `refs/heads/main` to `heads/main` once a tag `main` exists
    ref = git_or_nothing("symbolic-ref", "-q", "HEAD").removesuffix(b"\n").decode("utf-8", "surrogateescape")
    if not ref.startswith("refs/heads/") or not git_or_nothing("rev-parse", "-q", "--verify", "HEAD"):
        return False, None
    named, problem = trunk_problem()
    if problem is not None:
        return False, problem
    return ref != "refs/heads/" + named, None


def eligible() -> bool:
    """Whether a stamp may be used on this run: `standing`'s answer, with no line."""
    return standing() == (True, None)


def forced_reason(options: Options) -> str | None:
    """Why this run is forced, or None: `VERIFY_FORCE` set to anything but empty or `0`, whether it came on make's
    command line (which make exports to the recipe) or in the environment. `make ci` is not read here: it depends on the
    checks' own target and never reaches this script. The value is
    printed with its control characters escaped and cut short, so it cannot forge a line."""
    value = os.environ.get(FORCE_VARIABLE)
    if value not in (None, "", "0"):
        return FORCE_VARIABLE + "=" + str(value).encode("unicode_escape").decode("ascii")[:80]
    return None


def make_flags() -> str:
    """The single-letter flags make was run with, which it hands a recipe as the first word of `MAKEFLAGS` — the word
    only where it is made of letters (`i`, `ik`; a leading space, `-j4` or `--no-print-directory` is none)."""
    words = os.environ.get("MAKEFLAGS", "").split()
    return words[0] if words and words[0].isalpha() else ""


# What make hands every recipe in `MAKEFLAGS` (and reads from `GNUMAKEFLAGS`) that adds no text and no condition the
# factory did not write (D146): the letters that change no recipe (`k`, `s`, `w`, and the idle ones, which the borders
# take themselves), a job count, the load limit (D152), the jobserver's words, `--no-print-directory` and an
# output-sync word. Nothing else.
QUIET_LETTERS = frozenset("kswntqi")
QUIET_WORD = re.compile(r"-[kswntqi]+|-j[0-9]*|--jobserver-(?:auth|fifo|fds)=\S*|--no-print-directory|-O[a-z]*"
                        r"|--output-sync(?:=[a-z]+)?|-l[0-9.]*|--(?:load-average|max-load)(?:=[0-9.]+)?")
FORCING = re.compile(r"VERIFY_FORCE=\S*")  # the one command-line variable allowed, by name and any value (D147)
NOT_THE_FACTORYS = "make was run with `{word}`, which can add text or conditions the factory did not write"


def quoted(word: str) -> str:
    """A word from the command line or the environment as a line may carry it: control characters escaped, cut short, and
    no backtick, so that it cannot forge a line or close the span it is printed in."""
    return word.encode("unicode_escape").decode("ascii")[:80].replace("`", "\\x60")


# What no `MAKEFLAGS` says (D146, adversary B1, B2, B8): which makefile make read, and the variables recipes run under.
# `-f <file>` is on make's command line only; `MAKEFILES`, a `GNUmakefile` or a `makefile` is a makefile the factory did not
# write; `.SHELLFLAGS` in the environment changes how every recipe runs (`SHELL` in the environment does not: the
# `Makefile` sets it, and an environment variable never overrides that without `-e`, which `MAKEFLAGS` carries).
SHELLS = frozenset({"sh", "bash", "dash", "zsh", "ksh", "ash"})
MAKES = frozenset({"make", "gmake", "remake"})
ARGUMENT_LETTERS = frozenset("CEIfoW")  # make's short options that take an argument; `j`, `l` and `O` take it only attached
WITH_ARGUMENT = frozenset({"directory", "include-dir", "old-file", "assume-old", "what-if", "new-file", "assume-new",
                           "eval"})


def makefiles_named(argv: list[str]) -> list[str]:
    """The files make's own command line names with `-f`, `--file` or `--makefile`, in every spelling it takes."""
    named: list[str] = []
    index = 1
    while index < len(argv):
        word = argv[index]
        index += 1
        if word == "--":
            break
        if word.startswith("--"):
            option, _, value = word[2:].partition("=")
            if option in ("file", "makefile", *WITH_ARGUMENT) and not value and index < len(argv):
                value = argv[index]
                index += 1
            if option in ("file", "makefile"):
                named.append(value)
        elif word.startswith("-") and len(word) > 1:
            for position, letter in enumerate(word[1:], 1):
                if letter in "jlO":
                    break
                if letter in ARGUMENT_LETTERS:
                    value = word[position + 1:]
                    if not value and index < len(argv):
                        value = argv[index]
                        index += 1
                    if letter == "f":
                        named.append(value)
                    break
    return named


def process_of(pid: int) -> tuple[int, list[str]] | None:
    """The parent and the command line of a process, from `/proc` where there is one, else from `ps`; None where neither
    can say."""
    try:
        with open(f"/proc/{pid}/stat", encoding="utf-8", errors="replace") as handle:
            parent = int(handle.read().rpartition(")")[2].split()[1])
        with open(f"/proc/{pid}/cmdline", "rb") as raw:
            return parent, [os.fsdecode(word) for word in raw.read().split(b"\0") if word]
    except (OSError, ValueError, IndexError):
        pass
    try:
        done = subprocess.run(["ps", "-o", "ppid=", "-o", "args=", "-p", str(pid)], capture_output=True, text=True,
                              check=False, timeout=10)
        words = done.stdout.split()
        return (int(words[0]), words[1:]) if done.returncode == 0 and len(words) > 1 else None
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def making_command() -> list[str] | None:
    """The command line of the make whose recipe is running this process, reached through the shells between them; [] where
    no make runs it (a person at a prompt, a test runner), None where it cannot be read and a make is running it."""
    pid = os.getppid()
    for _ in range(32):
        found = process_of(pid)
        if found is None:
            return None if "MAKELEVEL" in os.environ else []
        parent, argv = found
        name = os.path.basename(argv[0]).lstrip("-") if argv else ""
        if name in MAKES:
            return argv
        if name not in SHELLS or parent <= 1:
            return []
        pid = parent
    return []


def makefile_problem(environ: Mapping[str, str], cwd: str | None) -> str | None:
    """Why make did not read exactly the project's root `Makefile` under the factory's shell: `MAKEFILES` or `.SHELLFLAGS`
    in the environment; and, where `cwd` is the directory the recipe runs in, a `GNUmakefile` or `makefile` there, or a
    make whose command line names a file other than `Makefile`."""
    if environ.get("MAKEFILES"):
        return "make was run with `MAKEFILES`, which adds makefiles the factory did not write"
    if ".SHELLFLAGS" in environ:
        return "make was run with `.SHELLFLAGS` in the environment, which changes how every recipe runs"
    if cwd is None:
        return None
    try:
        entries = sorted(os.listdir(cwd))
    except OSError:
        entries = []
    for name in entries:
        if name != "Makefile" and name.casefold() in ("gnumakefile", "makefile"):
            return f"make reads `{quoted(name)}`, not the `Makefile` the factory wrote"
    command = making_command()
    if command is None:
        return "make's command line could not be read, so which makefile it read is not known"
    root = os.path.realpath(os.path.join(cwd, "Makefile"))
    for name in makefiles_named(command):
        if os.path.realpath(os.path.join(cwd, name)) != root:
            return f"make read `{quoted(name)}`, not the project's `Makefile`"
    return None


def makeflags_problem(environ: Mapping[str, str] | None = None) -> str | None:
    """Why this run's `MAKEFLAGS` or `GNUMAKEFLAGS` can add text or conditions the factory did not write — `--eval`, `-I`,
    `-e`, `-r`, `-R`, `-B`, `-W`, `-o`, `-L`, `--trace`, `--shuffle`, anything after `--` — naming the first word that is
    not allowed, else why make did not read exactly the project's `Makefile` under the factory's shell
    (`makefile_problem`), else None. Defined here once: `verify-scoped.py` asks it for the full gate, and `declined` for
    the stamp. The word is printed with its control characters escaped and cut short, so it cannot forge a line. Given an
    environment, only that is read; without one, the process, the directory and the make that runs it are read too."""
    real = environ is None
    environ = os.environ if environ is None else environ
    for name in ("MAKEFLAGS", "GNUMAKEFLAGS"):
        words = environ.get(name, "").split()
        for index, word in enumerate(words):
            if word == "--" and all(FORCING.fullmatch(after) for after in words[index + 1:]):
                break  # only `VERIFY_FORCE=<value>` follows (D147): the documented forced run
            if QUIET_WORD.fullmatch(word) or (index == 0 and word.isalpha() and set(word) <= QUIET_LETTERS):
                continue
            return NOT_THE_FACTORYS.format(word=quoted(word))
    return makefile_problem(environ, os.getcwd() if real else None)


def ratcheting() -> bool:
    """Whether this run makes the gate write the tree it judges (`RATCHET_TIGHTEN`): it reads no stamp, writes none and
    removes none (D80), so a stamp that stood stands."""
    return bool(os.environ.get(RATCHET_VARIABLE))


def declined() -> bool:
    """Whether this run writes no stamp for what it is, whoever it is run by: a ratchet run touches nothing (D80); under
    `-n`, `-t` or `-q` the checks do not run; under `-i` a check that fails still lets the run go on and the sub-make
    exit 0, so `reuse` removes the stamp that stood, and this run records nothing."""
    return ratcheting() or any(letter in make_flags() for letter in DECLINING_FLAGS) or (
        makeflags_problem() is not None)


def idle() -> bool:
    """Whether this run starts no check (`-n`, `-t`, `-q`), so that it touches nothing."""
    return any(letter in make_flags() for letter in IDLE_FLAGS)


def remove_own(path: str) -> str | None:
    """One of this script's own files, gone before the first check starts, so that after a run that failed or was
    killed there is none. Whatever stands at its path is removed as itself: a regular file, a link (never what it
    points to) or a FIFO by unlinking, an empty directory by `rmdir`; a directory with something in it is not emptied,
    it is named. A file where the factory's directory should be is named as that file. None where it is gone or was
    never there; else why it could not be, naming what to delete."""
    directory = os.path.dirname(path)
    if os.path.islink(directory):
        return None  # what is behind a link is not ours to remove; `write_file` replaces the link itself
    if os.path.lexists(directory) and not os.path.isdir(directory):
        return "cannot use " + shown(directory) + " (it is a file, not a directory); delete that file"
    kind = "file"
    try:
        if stat.S_ISDIR(os.lstat(path).st_mode):
            kind = "directory"
            os.rmdir(path)
        else:
            os.remove(path)
    except FileNotFoundError:
        return None
    except OSError as error:
        return "cannot remove " + shown(path) + " (" + (error.strerror or str(error)) + "); delete that " + kind
    return None


def variable_digests() -> dict[str, str]:
    """The SHA-256 of each keyed variable's record, never a value: unset is told from empty by the record itself."""
    return {name: hashlib.sha256(variable_record(name)).hexdigest() for name in VARIABLES}


def write_baseline(tools: dict[str, str], ignored: str) -> None:
    """Beside a stamp just written, where the branch is a `slice/<id>`: the branch, the tools the run asked at its start,
    the variables' digests and the key's `ignored` part (`key_parts`' own digest of the files git ignores, no name of
    one), for a scoped run to compare with. Nothing is written on any other branch."""
    ref = git_or_nothing("symbolic-ref", "-q", "HEAD").removesuffix(b"\n").decode("utf-8", "surrogateescape")
    branch = ref.removeprefix("refs/heads/")
    if not trunk_module().SLICE_BRANCH.match(branch):
        return
    baseline = {"branch": branch, "tools": tools, "variables": variable_digests(), "ignored": ignored}
    write_file(baseline_path(), json.dumps(baseline, indent=2, sort_keys=True) + "\n")


def forget_baseline() -> str | None:
    """The baseline, gone: a run that may change what it was taken of leaves none. None where it is gone, or git cannot
    say where it would be."""
    try:
        return remove_own(baseline_path())
    except CannotTell:
        return None


def remove_stamp() -> str | None:
    """The stamp, gone before the first check starts (`remove_own`)."""
    return remove_own(stamp_path())


def begin_full_run(note: dict[str, object], token: str, forced: str | None = None, cannot: str | None = None) -> int:
    """Every full run of a stamp that may be used starts here: the stamp is removed, one line is said where there is
    something to act on, and the note of what the run began with — and the run's token, which only this run's `record` holds — is left for
    `record`. The line is the first of: the
    key cannot be built (`cannot`, the run records nothing), the stamp cannot be removed (it names the file to delete,
    and the run records nothing), the run was forced. Exits non-zero, so the recipe runs every check."""
    try:
        reason = next(filter(None, (remove_stamp(), remove_own(pending_path()), remove_own(baseline_path()))), None)
    except CannotTell:
        reason = None  # git cannot say where a stamp would be, so there is none to remove and none to write
    if cannot is None and reason is not None:
        cannot = reason
    if cannot is not None:
        print(CANNOT_LINE.format(reason=cannot))
        note = {NOTHING: True}  # a marker, never the reason: that is printed, and a path in it is this machine's
    elif forced is not None:
        print(FORCED_LINE.format(reason=forced))
    try:
        write_file(pending_path(), json.dumps(dict(note, token=token)) + "\n")
    except (OSError, CannotTell):
        pass  # `record` finds no note and says why it records nothing
    return 1


def reuse(options: Options) -> int:
    try:
        if idle():
            return 1
        usable, cannot = standing()
        if cannot is not None:
            print(CANNOT_LINE.format(reason="cannot tell which branch is the trunk: " + cannot))
            return 1  # it reads, writes and removes nothing: a stamp that stood stands
        if not usable:
            return 1
        if ratcheting():
            forget_baseline()  # what it writes is what the baseline was not taken of
            return 1  # a ratchet run reads, writes and removes nothing (D80): a stamp that stood is for a key that passed
        if declined():
            # `-i`: the checks run and may fail with the run still exiting 0, so no stamp may stand to be reused
            # afterwards; text or conditions the factory did not write (D146): no stamp may vouch for a tree they
            # judged. Either way this run records nothing (`record` declines it too)
            conditions = makeflags_problem()
            if conditions is not None:
                print(NOT_RECORDED_LINE.format(reason=conditions))
            return begin_full_run({NOTHING: True}, options.token)
        problem = not_vouched()
        if problem is not None:
            raise CannotTell(problem)
        key, parts = key_parts(machine_tools(options))
    except CannotTell as reason:
        return begin_full_run({}, options.token, cannot=str(reason))
    forced = forced_reason(options)
    if forced is None:
        stamp = read_stamp(stamp_path())
        if stamp is not None and stamp["key"] == key["key"]:
            print(REUSE_LINE.format(passed=stamp["passed"], abbreviated=str(key["key"])[:12]))
            return 0
    return begin_full_run({"key": key["key"], "tools": key["tools"], "parts": parts}, options.token, forced)


def not_recorded(reason: str) -> int:
    """A pass that was not recorded, and why: one line, and the gate's own exit code stands."""
    print(NOT_RECORDED_LINE.format(reason=reason))
    return 0


# The parts of the key a pass can find moved, in the order they are told, and how a person is told each.
PARTS = (
    ("scripts", "the Makefile or a script under scripts/"), ("files", "a file"), ("index", "the index"),
    ("history", "a branch or the history"), ("ignored", "a file git ignores"), ("variables", "a variable a check reads"),
)
WRITTEN = " — a check may have written one; `git status` shows it, and the next run records"
WRITTEN_IGNORED = " — a check may have written one; `git status --ignored` shows it, and the next run records"


def moved(before: object, after: dict[str, str]) -> str:
    """Which part of the key moved while the checks ran, from the digests `reuse` kept: what is said, and, where it is
    the files, that a check may have written one, that `git status` shows it and that the next run records."""
    kept = before if isinstance(before, dict) else {}
    names = [name for name, _ in PARTS if kept.get(name) != after[name]]
    if "scripts" in names and "files" in names:
        names.remove("files")  # the gate's scripts are among the files: one part, named once
    said = ", ".join(words for name, words in PARTS if name in names)
    if not said:
        return "the key changed while the checks ran"
    advice = WRITTEN_IGNORED if "ignored" in names else WRITTEN if {"files", "scripts"} & set(names) else ""
    return said + " changed while the checks ran" + advice


def why_no_note() -> str | None:
    """Why `reuse` left no note of the key, found by trying to leave one; None where a stamp that could not be removed
    stands (`reuse` named it already) and where nothing says why."""
    path = pending_path()
    directory = os.path.dirname(path)
    if os.path.lexists(stamp_path()) or (os.path.lexists(directory) and not os.path.isdir(directory)) or (
            os.path.isdir(path) and not os.path.islink(path)):
        return None  # a stamp or a note that could not be removed, or a file where the directory goes: `reuse` named it
    try:
        ensure_directory(os.path.dirname(path))
        with tempfile.TemporaryFile(dir=os.path.dirname(path)):
            pass
    except OSError as error:
        return "cannot write " + shown(os.path.dirname(path)) + " (" + (error.strerror or str(error)) + ")"
    return "the key from before the checks was not kept"


def new_token() -> int:
    """A random value for one run of the gate, which the recipe hands that run's two halves: never a process id, a host
    or a path."""
    print(secrets.token_hex(16))
    return 0


def record(options: Options) -> int:
    """After the last check: the stamp, if the note is this run's and the key is the one the run began with. The tools
    are the ones the run began with too — they are asked once — and the note that says this run records nothing records
    nothing. A pass that cannot be recorded — the tree moved while the checks ran, another run of the gate started here
    after this one, this was no run of the gate, or the stamp cannot be written — says so in one line."""
    if declined() or not eligible():
        return 0
    if not options.token:
        return not_recorded("this was not a run of the gate: no run token was given")
    try:
        text = read_own(pending_path())
        if text is None:
            raise ValueError("no note")
        pending = json.loads(text)
        if pending.get("token") != options.token:
            return not_recorded("another run of the gate started here after this one began, so only that run may record")
        if NOTHING in pending:
            return 0
        pending["key"], pending["tools"]
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        reason = why_no_note()
        return 0 if reason is None else not_recorded(reason)
    try:
        key, parts = key_parts(pending["tools"])
    except CannotTell as reason:
        return not_recorded(str(reason))
    if key["key"] != pending["key"]:
        return not_recorded(moved(pending.get("parts"), parts))
    passed = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    stamp = dict(key, passed=passed, result="pass")
    try:
        write_file(stamp_path(), json.dumps(stamp, indent=2, sort_keys=True) + "\n")
    except OSError as error:
        return not_recorded("cannot write " + shown(stamp_path()) + " (" + (error.strerror or str(error)) + ")")
    try:
        write_baseline(key["tools"], parts["ignored"])  # type: ignore[arg-type]
    except (OSError, CannotTell):
        pass  # the stamp stands; a scoped run finds no baseline and runs the full gate
    try:
        os.remove(pending_path())
    except OSError:
        pass  # a note left behind is overwritten by the next run
    return 0


def remove_after_failure() -> None:
    """`reuse` failed in a way nobody foresaw and the recipe runs every check: a stamp that stood is removed where this
    run could have used one, and where even that cannot be told, nothing is."""
    try:
        if not idle() and eligible():
            remove_stamp()
    except Exception:
        pass


def main(argv: list[str]) -> int:
    verb = argv[0] if argv else ""
    try:
        if sys.version_info < (3, 10):
            return 0 if verb == "record" else 1
        if verb == "reuse":
            return reuse(Options(argv[1:]))
        if verb == "record":
            return record(Options(argv[1:]))
        if verb == "token":
            return new_token()
    except Exception:
        if verb == "reuse":
            remove_after_failure()
    return 0 if verb == "record" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
