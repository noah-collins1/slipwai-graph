#!/usr/bin/env python3
"""`make mutation` and `make mutation-full` for a Python service: mutmut, held to what its own `.meta` files say.

    python3 scripts/mutmut-mutation.py <service> [<service> ...] [--file <path within the service> ...]

Without `--file` the whole of the service's `[tool.mutmut]` `source_paths` is mutated; `--file`, repeatable, hands over
only those files, and is taken with one service only. With several services each is run fully in turn, from a fresh
`mutants/` and under its own lock; one that fails never stops the next, and the run ends on one summary line naming each
failed service (D223). The verdict is read from the `mutants/<file>.meta` files mutmut writes, never from mutmut's exit status
(D212).

The configuration is read here, by the subset of `[tool.mutmut]` the factory writes (`targets`), so a `--file` is held
against what mutmut would mutate (`matched`) and a path mutmut would misread is refused (`refused`): `mutmut run` takes
mutant names as `fnmatch` patterns, so a `*`, `?` or `[` in a path is a pattern and not the file.

Exit status (with several services, the first non-zero in service order): 0 when every mutant is killed (or has no test reaching it, which is counted), 1 when a mutant fails the
run or a sweep finds nothing to mutate, 2 when the run could not start (a refused path, an unreadable table, a host,
`uv`, lock or mutmut version that does not fit, a `mutants/` that could not be removed).
"""
from __future__ import annotations

import io
import json
import os
import re
import shutil
import subprocess
import sys
import tokenize
from pathlib import Path
from collections import Counter
from typing import IO, Any, Callable

USAGE = "mutation: usage: mutmut-mutation.py <service> [<service> ...] [--file <path within the service> ...]"
# The one mutmut this script was written against: it calls functions mutmut does not document as public (R3), so another
# version is refused, and a change of the pin sweeps (T008).
PINNED = "3.8.0"
VERSION_CODE = "import importlib.metadata as m; print(m.version('mutmut'))"
# Held by a run for its whole length, beside the environment it runs in; the kernel releases it when the run dies.
LOCK = ".venv/mutmut-run.lock"
# What `mutmut run` does before it collects stats, and nothing after (R3): copy `src/` and the files its tests need into
# `mutants/`, then plant every mutant and write `mutants/<file>.meta` for each file. There is no generate-only command,
# and `mutmut run <names>` asserts on an empty selection, so the names a scoped run hands over are read from these files
# first, and an empty file is decided here and never by that assertion. The calls are mutmut 3.8.0's, not documented as
# public: this is why an environment holding another mutmut is refused (T004) and a change of the pin sweeps (T008).
GENERATE = """\
import os
from mutmut.__main__ import create_mutants, store_lines_covered_by_tests
from mutmut.mutation.trampoline import set_mutant_under_test
from mutmut.utils.file_utils import copy_also_copy_files, copy_src_dir, setup_source_paths
set_mutant_under_test("mutant_generation")
os.makedirs("mutants", exist_ok=True)
copy_src_dir()
copy_also_copy_files()
setup_source_paths()
store_lines_covered_by_tests()
create_mutants(os.cpu_count() or 4)
"""
# mutmut 3.8.0's own table of exit codes (`stats.py`, `status_by_exit_code`), as the verdict reads it (D212): a status is
# (what it is called, what it is called in the count, what it means for the run). A code not named here is not in the
# table mutmut was read against, and fails, by the `.get` default and not by a branch.
PASS, COUNTED, FAIL = "passes", "counted", "fails"
STATUS: dict[Any, tuple[str, str, str]] = {
    1: ("killed", "killed", PASS), 3: ("killed", "killed", PASS),
    5: ("no tests", "no tests", COUNTED), 33: ("no tests", "no tests", COUNTED),
    0: ("survived", "survived", FAIL),
    **{code: ("timeout", "timed out", FAIL) for code in (36, 24, -24, 152, 255)},
    35: ("suspicious", "suspicious", FAIL),
    **{code: ("segfault", "segfault", FAIL) for code in (-11, -9)},
    None: ("not checked", "not checked", FAIL),
    2: ("check was interrupted by user", "interrupted", FAIL),
    34: ("skipped", "skipped", FAIL),
    37: ("caught by type check", "caught by type check", FAIL),
}
# `# pragma: no mutate block|start|end` silences the mutants of the lines it covers, and a silenced mutant is never
# generated, so no status records it. Only the bare form is the per-mutant comment D212 excuses.
SILENCING_WORDS = ("block", "start", "end")
MUTMUT_STACK_DEPTH = -1  # `max_stack_depth`'s default: any other value hides survivors a test reaches as "no tests"
# What `uv sync --locked` says of a lock that is missing or out of date, in both of uv's wordings (0.12.21): the rest of
# its refusals are not a lock disagreement.
LOCKED_REFUSED = "`--locked` was provided"
EXITED = "(its exit status and the output above are mutmut's, never the verdict; the .meta files are)"
# What `fnmatch` reads as syntax: the characters that make a path a pattern over mutant names, not a name.
OPENERS = "*?["
# The packages whose version decides which mutants exist: mutmut, and libcst with everything libcst resolves to (D222).
ROOT_PACKAGE = "mutmut"
PARSER_PACKAGE = "libcst"


class Unreadable(Exception):
    """A configuration this script cannot read; the message is what is wrong, without the file it is in."""


def parse(arguments: list[str]) -> tuple[list[str], list[str]] | None:
    """The services and the files handed over with `--file`, or None where the arguments are not that shape. Files go
    with one service only: which of several they belong to is not said."""
    services = []
    rest = list(arguments)
    while rest and not rest[0].startswith("-"):
        services.append(os.path.normpath(rest.pop(0)))
    files: list[str] = []
    while rest:
        if rest[0] != "--file" or len(rest) < 2:
            return None
        files.append(rest[1])
        rest = rest[2:]
    if not services or (files and len(services) > 1):
        return None
    return services, [os.path.normpath(file) for file in files]


def read_toml(text: str) -> dict[str, Any]:
    """TOML text as data; `tomllib` is imported here so that loading the script on Python 3.10 never fails."""
    try:
        import tomllib
    except ImportError:
        raise Unreadable("no tomllib: Python 3.11 or newer reads [tool.mutmut]") from None
    try:
        return tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        raise Unreadable(f"is not valid TOML ({error})") from None


def opener(path: str) -> str | None:
    """The first character of a path that `fnmatch` reads as syntax, if it holds one."""
    return next((char for char in path if char in OPENERS), None)


def source_root(value: Any) -> str | None:
    """A `source_paths` entry as the one directory it names, or None where it is not the canonical form: a relative POSIX
    directory of literal segments, with no `.`, `..` or empty segment, no pattern syntax, no backslash and no `.py` file,
    with or without a trailing slash. mutmut reads an entry as `Path(entry)` and walks it, so any other spelling names
    files that a prefix of the entry as written would not place; the reader takes the subset it can place."""
    if not isinstance(value, str) or "\\" in value or opener(value):
        return None
    parts = value.removesuffix("/").split("/")
    if any(part in ("", ".", "..") for part in parts) or parts[-1].endswith(".py"):
        return None
    return "/".join(parts)


def check_paths(values: Any, name: str) -> list[str]:
    """`source_paths` as a non-empty list of canonical relative directories (`source_root`), else Unreadable."""
    if not isinstance(values, list) or not values:
        raise Unreadable(f"{name} must be a non-empty list of paths, not {values!r}")
    for value in values:
        if source_root(value) is None:
            raise Unreadable(f"{name} holds {value!r}, which is not a relative directory of literal segments under the "
                             "service")
    return values


def check_patterns(values: Any, name: str) -> list[str]:
    if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
        raise Unreadable(f"{name} must be a list of strings, not {values!r}")
    return values


def targets(service: str | Path) -> dict[str, Any]:
    """The service's `[tool.mutmut]` table, with `source_paths` (or, only where it is empty, the deprecated
    `paths_to_mutate`), `only_mutate` and `do_not_mutate` checked and defaulted."""
    path = Path(service) / "pyproject.toml"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise Unreadable(f"cannot be read ({error.strerror or error})") from None
    table = read_toml(text).get("tool", {}).get("mutmut")
    if not isinstance(table, dict):
        raise Unreadable("no [tool.mutmut] table")
    config = dict(table)
    config["source_paths"] = check_paths(table.get("source_paths") or table.get("paths_to_mutate"), "source_paths")
    for name in ("only_mutate", "do_not_mutate"):
        config[name] = check_patterns(table.get(name, []), name)
    return config


def matched(config: dict[str, Any], file: str) -> bool:
    """Whether mutmut 3.8.0 would mutate this file (a path within the service): a `.py` under `source_paths` that
    `should_mutate` takes, `fnmatch` applied to the path exactly as its `configuration.py` applies it."""
    from fnmatch import fnmatch

    roots = [source_root(root) for root in config["source_paths"]]
    if not file.endswith(".py") or not any(root and file.startswith(root + "/") for root in roots):
        return False
    included = not config["only_mutate"] or any(fnmatch(file, pattern) for pattern in config["only_mutate"])
    return included and not any(fnmatch(file, pattern) for pattern in config["do_not_mutate"])


def refused(service: str, file: str) -> str | None:
    """The words refusing a path `mutmut run` would read as a pattern over mutant names, or None."""
    char = opener(file)
    if char is None:
        return None
    return (f"`{service}/{file}` holds `{char}`, which mutmut reads as a pattern over mutant names; rename it, or run "
            "`make mutation-full`")


def requirement_name(requirement: str) -> str:
    found = re.match(r"\s*([A-Za-z0-9][A-Za-z0-9._-]*)", requirement)
    return re.sub(r"[-_.]+", "-", found.group(1)).lower() if found else ""


def manifest_versions(text: str) -> dict[str, Any]:
    document = read_toml(text)
    groups = [*document.get("dependency-groups", {}).values(), document.get("project", {}).get("dependencies", []),
              *document.get("project", {}).get("optional-dependencies", {}).values()]
    return {"tool.mutmut": document.get("tool", {}).get("mutmut"),
            "requirement": [item for group in groups for item in group
                            if isinstance(item, str) and requirement_name(item) == ROOT_PACKAGE]}


def closure(packages: list[dict[str, Any]], root: str) -> set[str]:
    """`root` and every package it resolves to, by the lock's own `dependencies`, whichever marker selects them."""
    wanted: dict[str, list[str]] = {}
    for package in packages:
        wanted.setdefault(package["name"], []).extend(item["name"] for item in package.get("dependencies", []))
    found, todo = set(), [root]
    while todo:
        name = todo.pop()
        if name not in found:
            found.add(name)
            todo.extend(wanted.get(name, []))
    return found


def lock_versions(text: str) -> dict[str, list[str]]:
    packages = read_toml(text).get("package")
    if not isinstance(packages, list):
        raise Unreadable("is not a uv lock: it has no [[package]] entries")
    names = {ROOT_PACKAGE} | closure(packages, PARSER_PACKAGE)
    found: dict[str, list[str]] = {}
    for package in packages:
        if package["name"] in names:
            found.setdefault(package["name"], []).append(package["version"])
    return found


def versions(pyproject_text: str | None = None, lock_text: str | None = None) -> dict[str, Any]:
    """What a change to the manifest or the lock sweeps on (R6): from the manifest its `[tool.mutmut]` table and every
    mutmut requirement as written, from the lock the versions of mutmut and of the closure of libcst, by name."""
    found: dict[str, Any] = {}
    if pyproject_text is not None:
        found.update(manifest_versions(pyproject_text))
    if lock_text is not None:
        found.update(lock_versions(lock_text))
    return found


class Job:
    """One run: the service, the files handed over, the environment mutmut and `uv` get, and the lock once held."""

    def __init__(self, service: str, files: list[str]) -> None:
        self.service = service
        self.files = files
        self.env: dict[str, str] = {}
        self.lock: IO[str] | None = None
        self.config: dict[str, Any] = {}
        self.judged: list[str] = []  # the files whose `.meta` is the verdict: the given ones, or every one in a sweep
        self.names: list[str] = []  # the mutant names a scoped run hands mutmut: every key of the given files


def note(line: str) -> None:
    """One `mutation: ` line; every line this script prints is spelled here."""
    print(f"mutation: {line}")


def say(line: str) -> int:
    """A `mutation: ` line, and the exit status that ends a run on it."""
    note(line)
    return 2


def check_refusal(job: Job) -> int | None:
    for file in job.files:
        refusal = refused(job.service, file)
        if refusal:
            return say(refusal)
    return None


def check_table(job: Job) -> int | None:
    try:
        job.config = targets(job.service)
    except Unreadable as error:
        return say(f"{job.service}/pyproject.toml: {error}")
    return None


def check_host(job: Job) -> int | None:
    if sys.platform == "win32" or not hasattr(os, "fork"):
        return say("mutmut needs os.fork, which this host does not have; run it under WSL")
    return None


def check_uv(job: Job) -> int | None:
    if shutil.which("uv", path=os.environ.get("PATH", "")) is None:
        return say("uv is not on PATH; install it to run mutmut (see scripts/verify)")
    return None


def check_environment(job: Job) -> int | None:
    """What mutmut and `uv` are handed: this environment without `PYTEST_ADDOPTS`, which would change how every mutant's
    tests run (`[tool.mutmut] pytest_add_cli_args` is where a service adds pytest options)."""
    job.env = {name: value for name, value in os.environ.items() if name != "PYTEST_ADDOPTS"}
    if "PYTEST_ADDOPTS" in os.environ:
        say("PYTEST_ADDOPTS is not passed to mutmut (it would change how every mutant's tests run); [tool.mutmut] "
            "pytest_add_cli_args is where this service adds pytest options")
    return None


def take_lock(job: Job, environment_only: bool = False) -> int | None:
    """One run of a service at a time: an exclusive, non-blocking lock beside its environment. Before the sync where
    the environment is already there; after it where it is not, because `uv sync` refuses a `.venv` that holds
    nothing but this file."""
    import fcntl

    path = Path(job.service) / LOCK
    if job.lock is not None or (environment_only and not (path.parent / "pyvenv.cfg").is_file()):
        return None
    path.parent.mkdir(exist_ok=True)
    handle = open(path, "a", encoding="utf-8", newline="\n")
    try:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        handle.close()
        return say(f"another mutmut run of {job.service} holds {path.as_posix()}; wait for it, then run this again")
    job.lock = handle
    return None


def take_lock_if_there(job: Job) -> int | None:
    return take_lock(job, environment_only=True)


def uv(job: Job, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["uv", *arguments], env=job.env, text=True, capture_output=True)


def last_line(done: subprocess.CompletedProcess[str]) -> str:
    """The last line a failed tool said, from what it wrote to stderr (to stdout where that is empty), leaving out the
    `hint:` lines that follow the error itself; empty where it said nothing."""
    for text in (done.stderr, done.stdout):
        lines = [line.strip() for line in (text or "").splitlines() if line.strip()]
        lines = [line for line in lines if not line.startswith("hint:")] or lines
        if lines:
            return lines[-1]
    return ""


def said(done: subprocess.CompletedProcess[str]) -> str:
    """` (exit n): <the tool's last line>` for a line about a tool that failed."""
    line = last_line(done)
    return f" (exit {done.returncode})" + (f": {line}" if line else "")


def ensure_synced(job: Job) -> int | None:
    """The environment from the committed lock and nothing else, as `scripts/verify` builds it. A lock that disagrees is
    what `uv sync --locked` says it is; any other failure (no network, a manifest it cannot parse) is said as `uv` said
    it, because a person told to relock a lock that is fine loses an afternoon."""
    done = uv(job, "sync", "--project", job.service, "--locked", "--quiet")
    if done.returncode == 0:
        return None
    if LOCKED_REFUSED in done.stderr:
        return say(f"{job.service}/uv.lock does not agree with {job.service}/pyproject.toml; run uv lock --project "
                   f"{job.service}, then this again")
    return say(f"uv sync --locked failed for {job.service}{said(done)}")


def check_mutmut_version(job: Job) -> int | None:
    done = uv(job, "run", "--no-sync", "--project", job.service, "python", "-c", VERSION_CODE)
    found = done.stdout.strip() if done.returncode == 0 else ""
    if found == PINNED:
        return None
    why = f" ({last_line(done)})" if done.returncode != 0 and last_line(done) else ""
    return say(f"mutmut {found or 'is not'} installed in {job.service}'s environment{why}; this wrapper runs mutmut "
               f"{PINNED}: add mutmut=={PINNED} to the dev group of {job.service}/pyproject.toml and run uv lock --project "
               f"{job.service} (slipwai migrate brings the wrapper for a newer pin)")


def meta_path(service: str, file: str) -> Path:
    """Where mutmut writes what it knows of one source file (a path within the service)."""
    return Path(service) / "mutants" / f"{file}.meta"


def codes_of(service: str, file: str) -> dict[str, Any] | None:
    """What mutmut recorded for each mutant of a file (its exit code, or null), in its own order; None where it wrote no
    readable `.meta` for it."""
    try:
        codes = json.loads(meta_path(service, file).read_text(encoding="utf-8")).get("exit_code_by_key")
    except (OSError, ValueError, AttributeError):
        return None
    return codes if isinstance(codes, dict) else None


def keys_of(service: str, file: str) -> list[str] | None:
    """The mutant names mutmut generated for a file, in its own order; None where it wrote no `.meta` for it."""
    codes = codes_of(service, file)
    return None if codes is None else list(codes)


def clean(job: Job) -> int | None:
    """Every run starts from nothing: mutmut keeps results between runs and lets them stand, and the directory is the
    report of the run that wrote it, not of the one before. What the delete could not remove is not read: mutmut's
    `copy_src_dir` skips every target that already exists, so a stale copy would stand as this run's."""
    left = Path(job.service) / "mutants"
    shutil.rmtree(left, ignore_errors=True)
    if left.exists() or left.is_symlink():
        return say(f"{job.service}/mutants/ could not be removed; delete it, then run this again")
    return None


def in_service(job: Job, *arguments: str, capture: bool) -> subprocess.CompletedProcess[str]:
    """`uv run --no-sync` in the service's own environment, from its directory, where mutmut reads its configuration."""
    project = str(Path(job.service).resolve())
    return subprocess.run(["uv", "run", "--no-sync", "--project", project, *arguments], cwd=job.service, env=job.env,
                          text=True, capture_output=capture)


def generate(job: Job) -> int | None:
    done = in_service(job, "python", "-c", GENERATE, capture=True)
    if done.returncode != 0:
        if (done.stdout + done.stderr).strip():
            print((done.stdout + done.stderr).strip()[-2000:])
        return say(f"mutmut could not generate mutants for {job.service}{said(done)}")
    return None


def sweep(job: Job) -> int | None:
    """A sweep judges every file mutmut wrote a `.meta` for, and reads the silencing of every one of them first. With
    no mutant in any of them there is nothing to run, and a pass on nothing is not a pass."""
    root = Path(job.service) / "mutants"
    job.judged = sorted(path.relative_to(root).as_posix()[: -len(".meta")] for path in root.rglob("*.meta"))
    failed = refuse_silenced(job)
    if not any(keys_of(job.service, file) for file in job.judged):
        note(f"mutmut found nothing to mutate in {job.service}; a pass on nothing is not a pass")
        return 1
    return 1 if failed else None


def plan(job: Job) -> int | None:
    """What a scoped run hands mutmut: the keys of the given files that have any. A file with no `.meta` is outside what
    mutmut mutates; one whose `.meta` is empty holds no function to mutate. Neither starts mutmut. What silences
    mutants is decided before any of those exits, over every given file that has a `.meta`."""
    if not job.files:
        return sweep(job)
    keyed: dict[str, list[str]] = {}
    for file in job.files:
        keys = keys_of(job.service, file)
        if keys is None:
            note(f"not mutated {job.service}/{file} \u2014 outside mutmut's configured targets")
        else:
            keyed[file] = keys
    job.judged = list(keyed)
    failed = refuse_silenced(job)
    if failed:
        return 1
    if not keyed:
        note(f"nothing under {job.service} that was given is a file mutmut would mutate; no mutant to run")
        return 0
    held = [file for file, keys in keyed.items() if keys]
    if not held:
        note(f"no mutant to run \u2014 {', '.join(keyed)}: mutmut found no function to mutate in "
             f"{'it' if len(keyed) == 1 else 'them'}")
        return 0
    job.names = [key for file in held for key in keyed[file]]
    note(f"scoped to {len(held)} given file(s): {', '.join(held)} \u2014 {len(job.names)} mutant(s)")
    return None


def run_mutmut(job: Job) -> int | None:
    """`mutmut run`, for the names of a scoped run after `--` and for none in a sweep. Its output is for whoever is
    watching; its exit status is printed and is never the verdict."""
    names = ["--", *job.names] if job.files else []
    done = in_service(job, "mutmut", "run", *names, capture=False)
    note(f"mutmut exited {done.returncode} {EXITED}")
    return None


def pragma_word(comment: str) -> str | None:
    """What mutmut 3.8.0's `_parse_pragma_token` makes of one comment, for the three words that silence more than a line:
    a comment holding `# pragma:` and `no mutate` takes the tail after the first `no mutate`, strips `: ` from its
    start, and reads the first word before a comma."""
    if "# pragma:" not in comment or "no mutate" not in comment:
        return None
    words = comment.partition("no mutate")[-1].strip().lstrip(": ").split(",", 1)[0].split()
    return words[0] if words and words[0] in SILENCING_WORDS else None


def pragmas(text: str) -> list[tuple[int, str]]:
    """The (line, word) of every comment in a source text that mutmut reads as a block, start or end pragma; strings
    that hold the same text are not comments. Raises SyntaxError where the text cannot be tokenized."""
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except (tokenize.TokenError, SyntaxError) as error:
        raise SyntaxError(str(error)) from None
    return [(token.start[0], word) for token in tokens if token.type == tokenize.COMMENT
            and (word := pragma_word(token.string))]


def silenced_by_file(service: str, file: str) -> list[str]:
    try:
        text = (Path(service) / file).read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return [f"{service}/{file} cannot be read as UTF-8, so its pragmas cannot be checked"]
    except OSError:
        return []
    try:
        found = pragmas(text)
    except SyntaxError:
        return [f"{service}/{file} cannot be read as Python, so its pragmas cannot be checked"]
    return [f"{service}/{file}:{number} holds \"# pragma: no mutate {word}\", which silences mutants nobody looked at; "
            "only a bare \"# pragma: no mutate\" on the line excuses one" for number, word in found]


def silenced(job: Job) -> list[str]:
    """One line for each way a judged file or the table silences mutants without anyone looking at them: decided in
    `plan`, before any exit that finds nothing to run, so that the two cannot disagree about what silences."""
    found = []
    if job.config.get("do_not_mutate_patterns"):
        found.append(f"{job.service}/pyproject.toml sets do_not_mutate_patterns, which silences every line a pattern "
                     "matches without anyone looking at its mutants; only a bare \"# pragma: no mutate\" on the "
                     "line excuses one")
    if job.config.get("mutate_only_covered_lines"):
        found.append(f"{job.service}/pyproject.toml sets mutate_only_covered_lines, which leaves out the mutants of "
                     "every line coverage excludes without anyone looking at them")
    if job.config.get("max_stack_depth", MUTMUT_STACK_DEPTH) != MUTMUT_STACK_DEPTH:
        found.append(f"{job.service}/pyproject.toml sets max_stack_depth, which turns the survivors a test reaches "
                     "through deeper calls into mutants no test reaches without anyone looking at them")
    for file in job.judged:
        found.extend(silenced_by_file(job.service, file))
    return found


def refuse_silenced(job: Job) -> list[str]:
    found = silenced(job)
    for line in found:
        note(line)
    return found


def judge(job: Job) -> int | None:
    """The verdict, from the `.meta` files and by D212's rule: killed passes, no tests is counted, and every other code,
    `null` and a code nobody has heard of included, fails."""
    failed: list[str] = []
    counts: Counter[str] = Counter()
    total = 0
    for file in job.judged:
        codes = codes_of(job.service, file)
        if codes is None:
            failed.append(f"{job.service}/{file}: mutmut left no readable .meta, so nothing can be said of it")
            note(failed[-1])
            continue
        for key, code in codes.items():
            total += 1
            name, counted, kind = STATUS.get(code, (f"unknown (exit {code})", f"unknown (exit {code})", FAIL))
            counts[counted] += 1
            if kind == FAIL:
                failed.append(key)
                note(f"{name} {job.service} {key} (mutmut show {key} in {job.service}; report {job.service}/mutants/)")
    order = ["killed", "no tests"] + [name for _, name, kind in STATUS.values() if kind == FAIL]
    parts = [f"{counts['killed']} killed", f"{counts['no tests']} no tests (reported, never failed)"]
    parts += [f"{counts[name]} {name}" for name in dict.fromkeys(order[2:] + sorted(set(counts) - set(order)))
              if counts[name]]
    note(f"{total} mutants: {', '.join(parts)}; {'failed' if failed else 'passed'} \u2014 report {job.service}/mutants/")
    return 1 if failed else 0


# The order the rules fix, read in one place: what starts nothing first, then the host, `uv`, the run's own lock, the
# environment, and the version in it.
CHECKS: tuple[Callable[[Job], int | None], ...] = (
    check_refusal, check_table, check_host, check_uv, check_environment, take_lock_if_there, ensure_synced, take_lock,
    check_mutmut_version, clean, generate, plan, run_mutmut, judge,
)


def run_service(service: str, files: list[str]) -> int:
    """One service's turn: every step from its refusals to its verdict, and the lock let go at the end of it."""
    job = Job(service, files)
    try:
        for check in CHECKS:
            status = check(job)
            if status is not None:
                return status
    finally:
        if job.lock is not None:
            job.lock.close()
    return 2  # unreachable: the last check returns a status


def main(arguments: list[str]) -> int:
    parsed = parse(arguments)
    if parsed is None:
        print(USAGE)
        return 2
    services, files = parsed
    if len(services) == 1:
        return run_service(services[0], files)
    statuses = {service: run_service(service, files) for service in dict.fromkeys(services)}
    failed = [service for service, status in statuses.items() if status]
    note(f"{len(statuses)} swept; {'failed: ' + ', '.join(failed) if failed else 'passed'}")
    return next((status for status in statuses.values() if status), 0)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
