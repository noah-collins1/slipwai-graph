#!/usr/bin/env python3
"""Say whether this tree already passed the gate, and record that it did: `reuse` and `record`.

`make verify` asks `reuse` first. It exits 0 only after printing the one line that says the full gate did not run
because this tree already passed it; any other answer — no stamp, a stamp for another key, anything this script cannot
read — exits non-zero, and the recipe runs every check. After the checks passed, `record` writes the stamp: a JSON
file under the git directory, never in the working tree, holding the key the tree had when the checks began. Nothing
here can fail the gate: `reuse` exits 0 only after printing its line, and `record` always exits 0.

The key is one SHA-256 over named parts, each a digest of its own so the stamp can show them apart. It starts the
way a tree is judged — every file git tracks and every file it does not ignore, by raw bytes, executable bit and a
link's target, read from the working tree through no filter, and the index's entries — where the checkout stands
in its repository: `HEAD`, every branch and remote ref, the shallow boundary — and, as a part of its own, the
`Makefile` and the scripts the gate runs from. The parts a later rule adds are named where they join.

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
import tempfile
import time

# The stamp's fields: the key a later run compares, the three parts it is made of, the instant of the pass, and
# the result, which is only ever a pass.
FIELDS = ("key", "tree", "scripts", "tools", "passed", "result")
# How long a version question may take, and the one argument that is not `--version` for the tools that spell it
# otherwise (`java -version` answers on standard error, which the answer is read from too).
ASK_TIMEOUT = 5
VERSION_ARGUMENTS = {"go": "version", "java": "-version"}
CANNOT_LINE = "verify: the full gate runs and this run records nothing — {reason}"
NOTHING = "nothing"
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
        self.tools: list[str] = []
        self.environments: list[str] = []
        pairs = {"--make": "make", "--tool": "tools", "--environment": "environments"}
        for flag, value in zip(argv, argv[1:]):
            name = pairs.get(flag)
            if name == "make":
                self.make = value or "make"
            elif name is not None:
                getattr(self, name).append(value)


def git(*args: str) -> bytes:
    try:
        done = subprocess.run(["git", *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    except OSError as error:
        raise CannotTell("git: " + str(error))
    if done.returncode != 0:
        raise CannotTell("git " + " ".join(args) + ": " + done.stderr.decode("utf-8", "replace").strip())
    return done.stdout


def git_or_nothing(*args: str) -> bytes:
    """What a `-q` question of git answers, or nothing where git says no without a reason: a detached `HEAD` has no
    branch and an unborn branch no commit, and neither is a failure."""
    try:
        done = subprocess.run(["git", *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    except OSError as error:
        raise CannotTell("git: " + str(error))
    if done.returncode == 1 and not done.stderr:
        return b""
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


def history_digest() -> str:
    """Where the checkout stands in its repository: the branch `HEAD` names (nothing where it is detached) and the
    commit it names (nothing on an unborn branch), every ref under `refs/heads` and `refs/remotes`, and the shallow
    boundary — the bytes of the file git names for it, or their absence."""
    refs = git("for-each-ref", "--format=%(objectname) %(refname)", "refs/heads", "refs/remotes")
    shallow = git("rev-parse", "--git-path", "shallow").decode("utf-8").strip()
    boundary = b"absent"
    if os.path.exists(shallow):
        with open(shallow, "rb") as handle:
            boundary = b"present\0" + handle.read()
    return digest([
        git_or_nothing("symbolic-ref", "-q", "HEAD"), git_or_nothing("rev-parse", "-q", "--verify", "HEAD"), refs,
        boundary,
    ])


def ask(tool: str, command: str) -> str:
    """The first non-empty line `command` prints when asked its version, whole. Launched once, with no standard input,
    its output read from a file so that nothing it leaves running can hold this script."""
    argument = VERSION_ARGUMENTS.get(tool, "--version")
    with tempfile.TemporaryFile() as output:
        try:
            child = subprocess.Popen(
                [command, argument], stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT,
            )
        except FileNotFoundError:
            raise CannotAsk(tool + " is not on PATH")
        except OSError as error:
            raise CannotAsk(tool + " cannot be started (" + str(error) + ")")
        try:
            code = child.wait(timeout=ASK_TIMEOUT)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait()
            raise CannotAsk(tool + " did not answer within " + str(ASK_TIMEOUT) + " seconds when asked its version")
        output.seek(0)
        text = output.read().decode("utf-8", "replace")
    if code != 0:
        raise CannotAsk(tool + " exited " + str(code) + " when asked its version")
    for line in text.splitlines():
        if line.strip():
            return line.strip()
    raise CannotAsk(tool + " printed nothing when asked its version")


def interpreter(environment: str) -> str:
    """The Python an environment was made with, as `pyvenv.cfg` records it, read without launching anything."""
    path = os.path.join(environment, "pyvenv.cfg")
    try:
        with open(path, "r", encoding="utf-8") as handle:
            lines = handle.read().splitlines()
    except OSError as error:
        raise CannotAsk("cannot read " + path + " (" + (error.strerror or str(error)) + ")")
    for line in lines:
        name, _, value = line.partition("=")
        if name.strip() == "version_info" and value.strip():
            return value.strip()
    raise CannotAsk(path + " does not record the interpreter's version_info")


def machine_tools(options: Options) -> dict[str, str]:
    """Every tool the machine supplies that the key holds, by the line it reported, and each environment's interpreter.
    The recipe names them; this script holds no list of its own."""
    tools = {}
    for tool in options.tools:
        tools[tool] = ask(tool, options.make if tool == "make" else tool)
    for environment in options.environments:
        tools["interpreter " + environment] = interpreter(environment)
    return tools


def is_gate_script(path: bytes) -> bool:
    """The `Makefile` and everything covered under `scripts/`, at any depth: what the gate runs from."""
    return path == b"Makefile" or path.startswith(b"scripts/")


def build_key(tools: dict[str, str]) -> dict[str, object]:
    """The parts and the key they make. Each part is a digest of its own, so the stamp shows them apart: `tree` is
    every covered file, the index and the history; `scripts` is the covered files the gate runs from, which `tree`
    holds as well. Each covered file is read once. `tools` is what the machine reported, asked once per run."""
    records = [(path, file_record(path)) for path in covered_files()]
    tree = digest([history_digest().encode("ascii"), index_entries()] + [record for _, record in records])
    scripts = digest([record for path, record in records if is_gate_script(path)])
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


def reuse(options: Options) -> int:
    try:
        tools = machine_tools(options)
    except CannotAsk as reason:
        print(CANNOT_LINE.format(reason=reason))
        write_file(pending_path(), json.dumps({NOTHING: str(reason)}) + "\n")
        return 1
    key = build_key(tools)
    stamp = read_stamp(stamp_path())
    if stamp is not None and stamp["key"] == key["key"]:
        print(REUSE_LINE.format(passed=stamp["passed"], abbreviated=str(key["key"])[:12]))
        return 0
    write_file(pending_path(), json.dumps({"key": key["key"], "tools": tools}) + "\n")
    return 1


def record(options: Options) -> int:
    """After the last check: the stamp, if the key is the one the run began with. The tools are the ones the run began
    with too — they are asked once — and the note that says this run records nothing records nothing."""
    with open(pending_path(), "r", encoding="utf-8") as handle:
        pending = json.load(handle)
    if NOTHING in pending:
        return 0
    key = build_key(pending["tools"])
    if key["key"] != pending["key"]:
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
            return reuse(Options(argv[1:]))
        if verb == "record":
            return record(Options(argv[1:]))
    except Exception:
        pass
    return 0 if verb == "record" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
