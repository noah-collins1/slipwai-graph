#!/usr/bin/env python3
"""`make mutation` and `make mutation-full` for a TypeScript service: Stryker, held to what its own report says.

    python3 scripts/stryker-mutation.py <service> [--file <path within the service> ...]

Without `--file` the whole of the service's `stryker.config.json` `mutate` list is mutated; `--file`, repeatable, hands
over only those files. The verdict is read from `<service>/reports/mutation/mutation.json`, never from Stryker's exit
status (D212): `Killed` passes, `Ignored` passes only where a `// Stryker disable next-line <mutator>: <reason>`
comment on the line above excuses it (D219), `NoCoverage` is counted and reported, and every other status, a status
nobody has heard of included, fails; a run that leaves no readable report fails whatever Stryker exited.

The list of files Stryker mutates is the service's `mutate` patterns, and `--mutate` replaces that list rather than
narrowing it (Stryker mutates a file the config excludes if it is handed one), so a `--file` is first held against the
list here, by the subset of minimatch the factory writes: literal segments, `*` within a segment, `**` as a whole
segment, a leading `!` and a leading `./`. A pattern outside that subset is `Unreadable`, and the caller decides, never
this reader by guessing.
"""
from __future__ import annotations

import contextlib
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from collections import Counter
from collections.abc import Iterator
from pathlib import Path

CONFIG = "stryker.config.json"
# What minimatch 10 (the version Stryker 10 reads) or `--mutate`'s own reading treats as syntax inside a path, in one
# table: (text, in a path that is handed to `--mutate`, in a `mutate` pattern this reader evaluates). A path holding a
# `path` entry is refused, never mutated under a different scope (D215 d); a pattern holding a `pattern` entry is
# `Unreadable`. `,` splits `--mutate`'s list and `*` is the one wildcard this reader evaluates, so each is one-sided;
# `(`, `)`, `]`, `}`, `+` and `@` alone are literal text to minimatch, so a path may hold them, while a pattern with
# one is left to the caller (the sweep) rather than guessed at.
SYNTAX = (
    (",", True, False), ("*", True, False), ("?", True, True), ("{", True, True), ("[", True, True),
    ("!", True, True), ("\\", True, True), ("+(", True, True), ("@(", True, True),
    ("]", False, True), ("}", False, True), ("(", False, True), (")", False, True), ("+", False, True),
    ("@", False, True),
)
# A trailing `:<line>` or `:<start>-<end>` that `--mutate` reads as a line range, in a path or a pattern alike.
RANGE = re.compile(r":\d+(-\d+)?$")
STRYKER = "@stryker-mutator/"
# The package that parses and plants the mutants; what it resolves in a lock decides which mutants exist (D222).
INSTRUMENTER = f"{STRYKER}instrumenter"
REPORT = "reports/mutation/mutation.json"
SANDBOX = ".stryker-tmp"
# Stryker's incremental mode keeps results here by default; `incremental: true` would let a run reuse them (T036).
INCREMENTAL = "reports/stryker-incremental.json"
# The verdict of each status, in one place: anything not named here fails, so a status Stryker adds later fails closed.
PASS = ("Killed", "Ignored")  # an `Ignored` one is then held to `unexcused`
COUNTED = ("NoCoverage",)
# The version the factory pins both packages at (ADR 0009); this names it in the one line that says Stryker is missing.
PINNED = "10.0.0"
PACKAGES = ("core", "vitest-runner")
# An `Ignored` mutant whose source does not excuse it is counted under this name (D219), which is not a Stryker status.
UNEXCUSED = "Unexcused"
# A static `Survived` mutant under which fewer tests completed than the dry run ran is counted under this name (D217): its
# suite did not run to completion, so Stryker's "survived" is not a verdict (research R11). Not a Stryker status either.
INCOMPLETE = "Incomplete"
# What D219 reads above an `Ignored` mutant: Stryker's own `next-line` directive, written with `//`, and the `restore` that
# undoes one (its regex, `^\s?Stryker (disable|restore)(?: (next-line))? ([a-zA-Z, ]+)(?::(.+)?)?`, on the comment's text).
NEXT_LINE = re.compile(r"\s*//\s?Stryker (disable|restore) next-line ([a-zA-Z, ]+)(?::(.*))?")
# Where Babel (so Stryker) counts a line: not at a form feed, a vertical tab or U+0085, which `str.splitlines` splits at.
LINE_BREAK = re.compile(r"\r\n?|[\n\u2028\u2029]")
COMMENT_ONLY = re.compile(r"\s*(?://|/\*|\*)")
FAILED_AS = {UNEXCUSED: "ignored without a next-line comment", INCOMPLETE: "survived with the suite incomplete",
             "Survived": "survived", "Timeout": "timed out", "RuntimeError": "runtime error",
             "CompileError": "compile error", "Pending": "pending"}


class Unreadable(ValueError):
    """Something this reader does not claim to read; the message says what, and the caller says so and stops."""


def say(text: str) -> None:
    """A line of this script's own, flushed: Stryker writes to the same pipe from another process. A character the
    stdout's encoding has no code for (cp1252 has no arrow) prints as `?`, never as a traceback."""
    encoding = sys.stdout.encoding or "utf-8"
    print(text.encode(encoding, "replace").decode(encoding), flush=True)


def segments(pattern: object) -> tuple[bool, list[str]]:
    """A `mutate` pattern as (negated, segments), or `Unreadable` naming it. The one reader of pattern syntax, so what
    is readable and what matches cannot drift."""
    if not isinstance(pattern, str):
        raise Unreadable(f"the pattern `{pattern}` is not a string")
    negated = pattern.startswith("!")
    body = pattern[1:] if negated else pattern
    if body.startswith("./"):
        body = body[2:]
    if RANGE.search(body):
        raise Unreadable(f"the pattern `{pattern}` ends in a line range, which this reader does not evaluate")
    if not body or body.startswith(("/", "#")) or body.endswith("/"):
        raise Unreadable(f"the pattern `{pattern}` is empty, absolute, a comment or ends in `/`")
    parts = body.split("/")
    for part in parts:
        bad = next((text for text, _, in_pattern in SYNTAX if in_pattern and text in part), None)
        if bad is not None:
            raise Unreadable(f"the pattern `{pattern}` uses `{bad}`, which this reader does not evaluate")
        if part in ("", ".", "..") or ("**" in part and part != "**"):
            raise Unreadable(f"the pattern `{pattern}` has a segment (`{part}`) this reader does not evaluate")
    return negated, parts


def segment_matches(pattern: str, part: str) -> bool:
    """One path segment against one pattern segment; `*` never takes a leading `.` the pattern did not write."""
    if part.startswith(".") and not pattern.startswith("."):
        return False
    if "*" not in pattern:
        return pattern == part
    return re.fullmatch("[^/]*".join(re.escape(piece) for piece in pattern.split("*")), part) is not None


def path_matches(pattern: list[str], parts: list[str]) -> bool:
    if not pattern:
        return not parts
    head, rest = pattern[0], pattern[1:]
    if head != "**":
        return bool(parts) and segment_matches(head, parts[0]) and path_matches(rest, parts[1:])
    for skip in range(len(parts) + 1):
        if skip and parts[skip - 1].startswith("."):
            return False
        if path_matches(rest, parts[skip:]):
            return True
    return False


def matched(patterns: list[object], file: str) -> bool:
    """Whether Stryker would mutate `file` (a POSIX path within the service): the patterns in order, a positive one
    marks what it matches and a `!` one clears it."""
    parts = file[2:].split("/") if file.startswith("./") else file.split("/")
    marked = False
    for negated, pattern in map(segments, patterns):
        if path_matches(pattern, parts):
            marked = not negated
    return marked


def targets(service: Path) -> list[str]:
    """The service's `mutate` list, every pattern checked readable, or `Unreadable` saying why not."""
    config = service / CONFIG
    if not config.is_file():
        raise Unreadable(f"no {CONFIG}")
    try:
        patterns = json.loads(config.read_text(encoding="utf-8")).get("mutate")
    except (ValueError, AttributeError) as why:
        raise Unreadable(f"is not a JSON object ({why})") from why
    if not isinstance(patterns, list) or not patterns:
        raise Unreadable("`mutate` is missing or is not a non-empty list of patterns")
    for pattern in patterns:
        segments(pattern)
    return patterns


def refused(service: str, file: str) -> str | None:
    """The words refusing a path within the service that Stryker's `--mutate` would misread, or None (D215 d)."""
    found = next((text for text, in_path, _ in SYNTAX if in_path and text in file), None) \
        or (RANGE.search(file) or [None])[0]
    if found is None:
        return None
    return (f"`{service}/{file}` holds `{found}`, which Stryker's --mutate reads as pattern syntax; rename it, or run "
            "`make mutation-full`")


def directory_refused(service: str) -> str | None:
    """The words refusing a service whose absolute path holds pattern syntax, or None. Stryker builds every `--mutate`
    and config pattern from the absolute path (`config/file-matcher.js`), so such a checkout matches none of its own
    files and the report is `files: {}` over files it never tried (D212)."""
    absolute = (Path.cwd() / service).resolve().as_posix()
    found = next((text for text, in_path, _ in SYNTAX if in_path and text in absolute), None)
    if found is None:
        return None
    return (f"{service} is at {absolute}, whose path holds `{found}`; Stryker reads it as pattern syntax, so no file "
            "would match. Run from a checkout whose path holds none")


def resolved(table: dict, roots: list[str]) -> list[str]:
    """The lock paths of everything `roots` need, transitively, found as npm finds a dependency: in the package's own
    `node_modules`, then in each parent's up to the lock's top. A dependency the lock does not hold is skipped."""
    seen: list[str] = []
    pending = [path for path in roots if isinstance(table.get(path), dict)]
    while pending:
        path = pending.pop()
        if path in seen:
            continue
        seen.append(path)
        needs = {**(table[path].get("optionalDependencies") or {}), **(table[path].get("dependencies") or {})}
        for name in needs if isinstance(needs, dict) else ():
            where = path
            while True:
                candidate = f"{where}/node_modules/{name}" if where else f"node_modules/{name}"
                if isinstance(table.get(candidate), dict):
                    pending.append(candidate)
                    break
                if "node_modules/" not in where:
                    break
                where = where.rsplit("/node_modules/", 1)[0] if "/node_modules/" in where else ""
    return seen


def stryker_in(text: str, key: str) -> dict[str, str]:
    """The `@stryker-mutator/*` versions in a manifest's dependency tables or a lock's `packages`, or `Unreadable`."""
    try:
        document = json.loads(text)
    except ValueError as why:
        raise Unreadable(f"is not JSON ({why})") from why
    if not isinstance(document, dict):
        raise Unreadable("is not a JSON object")
    found: dict[str, str] = {}
    if key == "packages":
        entries = document.get("packages")
        # Keyed by the lock's own path: every copy of a package, hoisted or nested, is its own entry, so any copy moving
        # is a change (D215 b). Collapsing them to one version per name would hide a nested copy moving.
        table = entries if isinstance(entries, dict) else {}
        for path, entry in table.items():
            if "node_modules/" in path and path.rsplit("node_modules/", 1)[-1].startswith(STRYKER) \
                    and isinstance(entry, dict):
                found[path] = str(entry.get("version"))
        # And whatever the instrumenter resolves, which decides which mutants exist (D222): its parser and its regex mutator
        # move through ranges while every `@stryker-mutator/*` version stands.
        for path in resolved(table, [path for path in table if path.endswith(f"node_modules/{INSTRUMENTER}")]):
            found[path] = str(table[path].get("version"))
        return found
    for table in ("dependencies", "devDependencies"):
        for name, version in (document.get(table) if isinstance(document.get(table), dict) else {}).items():
            if name.startswith(STRYKER):
                found[name] = str(version)
    return found


def versions(manifest_text: str | None = None, lock_text: str | None = None) -> dict[str, str]:
    """`{key: version}` for every `@stryker-mutator/*` entry of a manifest (keyed by package name), a lock (keyed by the
    lock path of each copy), or both. What the scope script compares between the base and the working tree (D215 b)."""
    found = stryker_in(manifest_text, "manifest") if manifest_text is not None else {}
    if lock_text is not None:
        found.update(stryker_in(lock_text, "packages"))
    return found


def parse(arguments: list[str]) -> tuple[str, list[str]] | None:
    """The service and the `--file` values, or None where the arguments are not `<service> [--file <path> ...]`."""
    if not arguments or arguments[0].startswith("-"):
        return None
    service, files, rest = arguments[0].rstrip("/") or arguments[0], [], arguments[1:]
    while rest:
        if rest[0] != "--file" or len(rest) < 2:
            return None
        files.append(rest[1])
        rest = rest[2:]
    return service, files


def service_relative(service: Path, file: str) -> str:
    """A `--file` as the path within the service that it names. The scope script hands over service-relative paths, and a
    person running this by hand may type one relative to the project root or the current directory, or an absolute one;
    all read as the file they name (A10). A path that names nothing under the service stays as it was, so the list check
    says it is outside Stryker's targets."""
    where = service.resolve()
    if not os.path.isabs(file) and (service / file).exists():
        return file
    if os.path.isabs(file):
        with contextlib.suppress(ValueError):
            return Path(file).resolve().relative_to(where).as_posix()
        return file
    for base in (Path.cwd(), project_root(service)):
        with contextlib.suppress(ValueError):
            return (base / file).resolve().relative_to(where).as_posix()
    return file


def stale(root: Path, service: Path) -> bool:
    """Whether `npm ci` has to run: the install marker is missing or older than a manifest or lock that feeds it.

    The same rule the Makefile's `node_modules/.package-lock.json: package.json package-lock.json` target and the
    family verify script (`if [ ! -d node_modules ]; then npm ci; fi`) apply, so a change to one is read against the
    others: install from the committed lock when the lock is newer than what was installed, otherwise leave it.
    """
    marker = root / "node_modules" / ".package-lock.json"
    if not marker.is_file():
        return True
    inputs = (root / "package.json", root / "package-lock.json", service / "package.json", service / "package-lock.json")
    return any(path.is_file() and path.stat().st_mtime > marker.stat().st_mtime for path in inputs)


def stryker_present(root: Path, service: Path) -> bool:
    """Whether both Stryker packages and the `stryker` binary `npm exec` starts are installed, looked for from the
    service up to the project root."""
    here, top, found = service.resolve(), root.resolve(), set()
    while True:
        found |= {name for name in PACKAGES if (here / "node_modules" / "@stryker-mutator" / name / "package.json").is_file()}
        found |= {"bin" for name in ("stryker", "stryker.cmd") if (here / "node_modules" / ".bin" / name).exists()}
        if here == top or here.parent == here:
            return found == {*PACKAGES, "bin"}
        here = here.parent


def project_root(service: Path) -> Path:
    """The directory the project's npm workspace is rooted at, found from the service rather than assumed to be the
    current directory: the nearest ancestor whose `package.json` declares `workspaces`, else the nearest ancestor above
    the service that holds a `package-lock.json`, else the current directory."""
    here = service.resolve()
    for ancestor in (here, *here.parents):
        try:
            if '"workspaces"' in (ancestor / "package.json").read_text(encoding="utf-8"):
                return ancestor
        except OSError:
            continue
    for ancestor in here.parents:
        if (ancestor / "package-lock.json").is_file():
            return ancestor
    return Path.cwd()


def locks(root: Path) -> Path:
    """Where this script's locks live: under the project, in a directory git ignores and `check-imports` does not read,
    so that every shell on the checkout finds them (not `TMPDIR`, which differs between shells) and `npm ci` does not
    remove them (as it would under `node_modules`)."""
    return root / SANDBOX


def alive(pid: int) -> bool:
    """Whether a process of this id exists. Where it cannot be asked (Windows has no signal 0: `os.kill` would end the
    process), it is taken to exist, and the lock's age decides instead."""
    if sys.platform == "win32":
        return True
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except OSError:
        return True
    return True


def holder_of(lock: Path) -> int | None:
    """The pid a lock records, or None where it is unreadable."""
    try:
        return int(lock.read_text(encoding="utf-8").split()[0])
    except (OSError, ValueError, IndexError):
        return None


def broken(lock: Path) -> bool:
    """Whether the lock's holder is gone: its pid is not a live process, or on Windows the lock is older than `LOCK_STALE`."""
    holder = holder_of(lock)
    if sys.platform == "win32":
        try:
            return time.time() - lock.stat().st_mtime > LOCK_STALE
        except OSError:
            return True
    return holder is not None and not alive(holder)


@contextlib.contextmanager
def file_lock(lock: Path, what: str) -> Iterator[bool]:
    """Exclusive use of `what`, kept as `lock`: a file naming its holder's pid, created whole and hard-linked into place
    (so it is never seen empty), and broken where that pid is no process. Yields False where it was not got within
    `LOCK_WAIT` seconds. The lock and its holder are named in the line that says this run is waiting and in the one that
    says it gave up."""
    lock.parent.mkdir(parents=True, exist_ok=True)
    mine = lock.with_name(f"{lock.name}.{os.getpid()}")
    mine.write_text(f"{os.getpid()}\n", encoding="utf-8", newline="\n")
    deadline, told = time.time() + LOCK_WAIT, False
    try:
        while True:
            try:
                os.link(mine, lock)
                break
            except FileExistsError:
                if broken(lock):
                    lock.unlink(missing_ok=True)
                    continue
                if time.time() > deadline:
                    say(f"mutation: another run of {what} (pid {holder_of(lock)}, {lock}) did not finish; "
                        "if no such process is running, remove the lock, then run this again")
                    yield False
                    return
                if not told:
                    say(f"mutation: another run of {what} is running (pid {holder_of(lock)}, {lock}); waiting for it")
                    told = True
                time.sleep(0.2)
        try:
            yield True
        finally:
            lock.unlink(missing_ok=True)
    finally:
        mine.unlink(missing_ok=True)


LOCK_STALE = 1800  # seconds after which a lock is broken where its holder's pid cannot be asked (Windows)
LOCK_WAIT = 900  # seconds a run waits for a lock whose holder is alive


def install(root: Path, service: Path, quiet: bool = False) -> int | None:
    """`npm ci` at the root under the project's install lock, where the marker still says it is due once the lock is held
    (another run, or the Makefile's install target, may have installed meanwhile); exit 2 with one line where it fails,
    None otherwise. `quiet` is the Makefile's call, which says nothing of its own."""
    with file_lock(locks(root) / "install.lock", "the install of this project") as held:
        if not held:
            return 2
        if not stale(root, service):
            return None
        if not quiet:
            say("mutation: installing from the committed lock (npm ci)")
        done = subprocess.run(["npm", "ci"], cwd=root)
        if done.returncode != 0:
            say(f"mutation: npm ci failed (exit {done.returncode}); fix the install, then run this again")
            return 2
        marker = root / "node_modules" / ".package-lock.json"
        marker.parent.mkdir(exist_ok=True)
        marker.touch()
    return None


def installed(job: Job) -> int | None:
    """Exit 2 with one line where Stryker cannot be started, None where it can. Installs from the committed lock and
    never fetches: `npm ci` takes exactly the lock, and `npm exec --no` refuses to download what is not installed."""
    service = job.service
    root = project_root(Path(service))
    if shutil.which("npm") is None:
        wanted = root / ".nvmrc"
        node = wanted.read_text(encoding="utf-8").strip() if wanted.is_file() else ""
        say(f"mutation: npm is not on PATH; install Node{' ' + node if node else ''} to run Stryker")
        return 2
    if stale(root, Path(service)):
        failed = install(root, Path(service))
        if failed is not None:
            return failed
    if not stryker_present(root, Path(service)):
        say(f"mutation: Stryker is not installed in this project: add @stryker-mutator/core and @stryker-mutator/vitest-runner "
            f"{PINNED} to {service}/package.json's devDependencies and run npm install")
        return 2
    return None


class Job:
    """One invocation: the service, and the files handed over (narrowed by the list check to those Stryker would take)."""

    def __init__(self, service: str, given: list[str]) -> None:
        self.service, self.given = service, given


def incremental_files(service: Path) -> list[Path]:
    """Where Stryker's incremental mode keeps an earlier run's results: its default file, and the one the config's
    `incrementalFile` names where that stays inside the service (a path that leaves it is not this script's to delete)."""
    found = [service / INCREMENTAL]
    try:
        named = json.loads((service / CONFIG).read_text(encoding="utf-8")).get("incrementalFile")
    except (OSError, ValueError, AttributeError):
        named = None
    if isinstance(named, str) and named:
        here = (service / named).resolve()
        if here.is_relative_to(service.resolve()) and here != service.resolve():
            found.append(here)
    return found


def clean(service: Path) -> None:
    """Every run starts from nothing: an earlier report must not be able to pass a run that wrote none, an earlier
    sandbox is not this run's, and an earlier run's incremental file is no result of this one (T036; `--force` is the
    other half, `run` passes it)."""
    shutil.rmtree(service / "reports" / "mutation", ignore_errors=True)
    shutil.rmtree(service / SANDBOX, ignore_errors=True)
    for left in incremental_files(service):
        left.unlink(missing_ok=True)


def read_report(path: Path) -> dict[str, dict] | None:
    """The report's `files`, or None where there is no readable report."""
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    files = document.get("files") if isinstance(document, dict) else None
    return files if isinstance(files, dict) else None


def dry_run_tests(path: Path) -> int | None:
    """How many tests the dry run found, from the report's `testFiles`; None where the report does not say."""
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
        listed = document["testFiles"]
        return sum(len(entry["tests"]) for entry in listed.values())
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return None


def test_owners(path: Path) -> dict[str, str]:
    """The test file each of the report's dry-run tests is in, by test id; empty where the report does not say."""
    try:
        listed = json.loads(path.read_text(encoding="utf-8"))["testFiles"]
        return {str(test["id"]): name for name, entry in listed.items() for test in entry["tests"]}
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return {}


def ignores_static(service: Path) -> bool:
    """Whether the service's config sets `ignoreStatic`, under which Stryker runs a static mutant under the tests that
    cover it and not under the whole suite (A9)."""
    try:
        return json.loads((service / CONFIG).read_text(encoding="utf-8")).get("ignoreStatic") is True
    except (OSError, ValueError, AttributeError):
        return False


def incomplete(one: dict, dry_run: int | None, covering_only: bool = False,
               owners: dict[str, str] | None = None) -> str | None:
    """Why a `Survived` mutant is not a survivor (D217, research R11), or None. Stryker 10.0.0's Vitest runner skips the
    tests of a file whose `beforeAll` throws and reads a run with no failed test as `Survived`; the report keeps only
    `testsCompleted`. A static mutant is one every test runs under, so it must complete the dry run's count, or with
    `ignoreStatic` (`covering_only`) the tests that cover it; a mutant that is not static runs only its covering tests,
    and is never compared."""
    done = one.get("testsCompleted")
    if one.get("status") != "Survived" or one.get("static") is not True:
        return None
    covering = one.get("coveredBy")
    # The test files the report places the mutant's covering tests in: where the tests went missing is not recorded, so
    # these are the files to look in, named only where the report says.
    files = sorted({(owners or {}).get(str(test)) for test in covering if (owners or {}).get(str(test))}) \
        if isinstance(covering, list) else []
    where = f"; the tests that cover it are in {', '.join(files)}" if files else ""
    remedy = (" — make the setup that failed fail inside a test (a hook inside a `describe`), and the mutant counts as "
              "killed")
    if covering_only:
        if not isinstance(covering, list) or not isinstance(done, int) or isinstance(done, bool) or done >= len(covering):
            return None
        return (f"Stryker says it survived, but the suite ran {done} of the {len(covering)} tests that cover it "
                f"(a hook or a file failed, so that is not a survivor and not a pass{where}){remedy}")
    if dry_run is None or not isinstance(done, int) or isinstance(done, bool) or done >= dry_run:
        return None
    return (f"Stryker says it survived, but the suite ran {done} of the dry run's {dry_run} tests under it "
            f"(a hook or a file failed, so that is not a survivor and not a pass{where}){remedy}")


def judged(files: dict[str, dict], given: list[str]) -> list[tuple[str, dict]]:
    """The mutants the verdict is about: those of the given files, or of every file in the report when none were given."""
    wanted = [name[2:] if name.startswith("./") else name for name in given]
    return [(name, one) for name in sorted(files) if not wanted or name in wanted
            for one in (files[name].get("mutants") or []) if isinstance(one, dict)]


# What starts a statement after a newline, so a file written without semicolons is still cut where it ends.
STATEMENT = re.compile(r"\s*(?:export|import|const|let|var|function|class|interface|type|declare|enum|async|abstract|"
                       r"namespace)\s")
# Where TypeScript's automatic semicolon insertion ends a statement at a newline: the text before ends an operand (a name,
# a number, a string, a closing bracket) and the next token begins one (a name, a number, a string) and is not a word that
# continues an expression. Anything else continues the statement, and a statement read too long is classified as code.
OPERAND_END = re.compile(r"[\w$)\]}'\"`>]")
OPERAND_START = re.compile(r"[\w$'\"]")
CONTINUES = re.compile(r"(?:as|satisfies|in|of|instanceof|extends|implements|is|keyof)\b")
# The statements that plant nothing: type declarations and imports (by how they begin), re-exports (whole), ambient
# declarations (`declare` of a value, a function, a class, a namespace; none holds an initialiser, which is checked) and an
# enum whose members have no initialiser. `interface` and `declare` blocks must also end where their braces do (T037).
DECLARED = re.compile(r"(?:export\s+)?(?:declare\s+)?(?:interface|type)\s+[A-Za-z_$]|import\s+(?:type\s+)?[\w{*\"']|"
                      r"export\s+type\b")
INTERFACE = re.compile(r"(?:export\s+)?(?:declare\s+)?interface\b")
AMBIENT = re.compile(r"(?:export\s+)?declare\s+(?:const|let|var|function|(?:abstract\s+)?class|namespace|module|global|"
                     r"(?:const\s+)?enum)\b")
ENUM = re.compile(r"(?:export\s+)?(?:declare\s+)?(?:const\s+)?enum\s+[A-Za-z_$][\w$]*\s*\{\s*"
                  r"(?:[A-Za-z_$][\w$]*\s*(?:,\s*[A-Za-z_$][\w$]*\s*)*,?\s*)?\}")
REEXPORT = re.compile(r"export\s*(?:\*(?:\s+as\s+\w+)?|\{[^}]*\})\s*(?:from\s+['\"][^'\"]*['\"])?")
# A declaration whose initialiser no Stryker 10.0.0 mutator reads (research R12): a numeric literal (decimal, separators,
# exponent, hex, octal, binary, bigint), `null`, `undefined` or a plain name or member path, with an optional plain type
# and `as const`. The mutators read strings, templates, booleans, `!`, a unary sign, arrays, objects, arrows, function
# bodies, regexes, operators and some method calls; a name is not a boolean. Anything else is not matched, so it is code.
NUMBER = r"(?:0[xX][\da-fA-F_]+|0[oO][0-7_]+|0[bB][01_]+|(?:\d[\d_]*\.?[\d_]*|\.\d[\d_]*)(?:[eE][+-]?\d[\d_]*)?)n?"
NAME = r"(?!(?:true|false)\b)[A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*"
INERT = re.compile(rf"(?:export\s+)?(?:const|let|var)\s+[A-Za-z_$][\w$]*(?:\s*:\s*[\w$.<>\[\]| ]+?)?\s*=\s*"
                   rf"(?:{NUMBER}|null|undefined|{NAME})(?:\s+as\s+const)?")


def code_after(text: str, i: int) -> str:
    """The text from the first character at or after `i` that is neither blank nor in a comment."""
    while i < len(text):
        if text[i].isspace():
            i += 1
        elif text.startswith("//", i):
            i = text.find("\n", i) if "\n" in text[i:] else len(text)
        elif text.startswith("/*", i):
            i = text.find("*/", i + 2) + 2 if "*/" in text[i + 2:] else len(text)
        else:
            break
    return text[i:i + 12]


def ends_here(before: str, after: str) -> bool:
    """Whether a newline between `before` and `after` ends a statement (automatic semicolon insertion)."""
    return bool(before) and OPERAND_END.match(before[-1]) is not None and OPERAND_START.match(after) is not None \
        and CONTINUES.match(after) is None


def statements(text: str) -> list[str]:
    """The top-level statements of a TypeScript file, comments dropped and strings kept whole: cut at a `;` outside any
    bracket, or at a newline outside any bracket where the next token cannot continue the statement or a
    statement-starting keyword follows."""
    found, buf, depth, quote, i = [], [], 0, None, 0
    while i < len(text):
        char = text[i]
        if quote:
            buf.append(text[i:i + 2] if char == "\\" else char)
            i += 2 if char == "\\" else 1
            quote = None if char == quote else quote
            continue
        if text.startswith("//", i):
            i = text.find("\n", i) if "\n" in text[i:] else len(text)
            continue
        if text.startswith("/*", i):
            i = text.find("*/", i + 2) + 2 if "*/" in text[i + 2:] else len(text)
            buf.append(" ")
            continue
        depth += (char in "{([") - (char in "})]")
        quote = char if char in "'\"`" else None
        if (char == ";" and depth <= 0) or (char == "\n" and depth <= 0 and (
                STATEMENT.match(text, i + 1) or ends_here("".join(buf).rstrip(), code_after(text, i + 1)))):
            found.append("".join(buf).strip())
            buf = []
        else:
            buf.append(char)
        i += 1
    return [*found, "".join(buf).strip()]


def closed(statement: str) -> bool:
    """Whether the statement ends where its first brace group does (or has none): nothing follows its closing brace."""
    depth, quote, seen, i = 0, None, False, 0
    while i < len(statement):
        char = statement[i]
        if quote:
            i += 2 if char == "\\" else 1
            quote = None if char == quote else quote
            continue
        if char in "'\"`":
            quote = char
        elif char in "{([":
            depth, seen = depth + 1, seen or char == "{"
        elif char in "})]":
            depth -= 1
            if depth == 0 and seen and statement[i + 1:].strip():
                return False
        i += 1
    return True


def inert(statement: str) -> bool:
    """Whether the whole of one statement plants nothing: a declaration that is entirely so, never one that merely begins
    like it."""
    if REEXPORT.fullmatch(statement) or INERT.fullmatch(statement) or ENUM.fullmatch(statement):
        return True
    if DECLARED.match(statement):
        return INTERFACE.match(statement) is None or closed(statement)
    return AMBIENT.match(statement) is not None and "=" not in statement.replace("=>", "") and closed(statement)


def holds_code(path: Path) -> bool:
    """Whether the file could hold a mutant: any top-level statement that is not a type declaration, an import, a
    re-export or a declaration of a value no mutator reads (T033). A file this cannot read counts as holding code, so the answer fails closed."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, ValueError):
        return True
    return any(statement and not inert(statement) for statement in statements(text))


def directives_above(lines: list[str], line: int) -> list[re.Match[str]]:
    """The `// Stryker disable|restore next-line` comments that lead the code on 1-based `line`, in source order: Stryker
    attaches a comment to the next node, so the blank and comment-only lines between a directive and its code do not
    separate them (A8), and the first line of code above ends the search."""
    found: list[re.Match[str]] = []
    for text in reversed(lines[:line - 1]):
        if not text.strip():
            continue
        match = NEXT_LINE.fullmatch(text.rstrip())
        if match is not None:
            found.insert(0, match)
        elif COMMENT_ONLY.match(text) is None:
            break
    return found


def unexcused(service: str, name: str, entry: dict, one: dict) -> str | None:
    """Why an `Ignored` mutant does not pass (D219), or None where a `// Stryker disable next-line <mutator>: <reason>`
    comment above it names its mutator with a reason and is what ignored it. Stryker 10.0.0 marks a next-line, a block and
    a file-wide comment alike `Ignored`, and gives the comment's reason (or `Ignored using a comment`) as `statusReason`,
    so the source decides which comment, and the `statusReason` must be that comment's reason, or a block comment
    ignored it (A6); only `excludedMutations` is told apart by its reason (research R10)."""
    if str(one.get("statusReason") or "").startswith("Ignored because of excluded mutation"):
        return "the config's mutator.excludedMutations ignored it, which is not a per-mutant comment"
    source = entry.get("source")
    if not isinstance(source, str):
        try:
            source = (Path(service) / name).read_text(encoding="utf-8")
        except (OSError, ValueError):
            source = ""
    lines = LINE_BREAK.split(source)
    mutator = str(one.get("mutatorName"))
    line = ((one.get("location") or {}).get("start") or {}).get("line")
    directives = directives_above(lines, line) if isinstance(line, int) and 2 <= line <= len(lines) + 1 else []
    # Stryker's rules chain from the nearest: the first that names the mutator, or `all`, is the one that applies.
    def names(found: re.Match[str]) -> list[str]:
        return [word.strip().lower() for word in found[2].split(",")]

    applying = next((found for found in reversed(directives) if {mutator.lower(), "all"} & set(names(found))), None)
    if applying is None and directives:
        return f"the next-line comment does not name {mutator}"
    if applying is None or applying[1] == "restore":
        return f"the line above it is not a `// Stryker disable next-line {mutator}: <reason>` comment"
    if mutator.lower() not in names(applying):
        return f"the next-line comment does not name {mutator}"
    reason = (applying[3] or "").strip()
    if not reason:
        return "the next-line comment gives no reason"
    given = str(one.get("statusReason") or "").strip()
    if given != reason:
        return (f"Stryker's reason for ignoring it (`{given}`) is not the next-line comment's (`{reason}`), so another "
                "directive ignored it")
    return None


def failure_line(service: str, name: str, one: dict, report: str, why: str | None = None,
                 unfinished: str | None = None) -> str:
    start = (one.get("location") or {}).get("start") or {}
    replacement = " ".join(str(one.get("replacement", "")).split())
    excuse = f" — not excused: {why}" if why else f" — {unfinished}" if unfinished else ""
    return (f"mutation: {INCOMPLETE if unfinished else one.get('status')} {service}/{name}:{start.get('line')}:{start.get('column')} "
            f"{one.get('mutatorName')} → {replacement}{excuse} (report {report})")


def last_line(counts: Counter, failed: bool, report: str) -> str:
    total = sum(counts.values())
    text = (f"mutation: {total} mutants: {counts['Killed']} killed, {counts['Ignored']} ignored, "
            f"{counts['NoCoverage']} not covered (reported, never failed)")
    for status, count in sorted(counts.items(), key=lambda item: (item[0] not in FAILED_AS, item[0])):
        if status not in PASS + COUNTED:
            text += f", {count} {FAILED_AS.get(status, status)}"
    return f"{text}; {'failed' if failed else 'passed'} — report {report}"


def unseen(service: str, given: list[str], report: str, files: dict[str, dict]) -> list[str]:
    """What a scoped report fails to show of the files it was given (T026): a file it names that was not given, and a
    given file with no mutant in it that is not a file, or holds code Stryker could have planted a mutant in."""
    wanted = [name[2:] if name.startswith("./") else name for name in given]
    lines = [f"mutation: the report names {service}/{name}, which was not given; a scoped run is judged on the files "
             f"it was given, so that is not a pass (report {report})" for name in sorted(files) if name not in wanted]
    for name in wanted:
        entry = files.get(name)
        if isinstance(entry, dict) and entry.get("mutants"):
            continue
        path = Path(service) / name
        if not path.is_file():
            lines.append(f"mutation: {service}/{name} is not a file; that is not a pass (report {report})")
        elif holds_code(path):
            lines.append(f"mutation: Stryker found no mutant in {service}/{name}, which holds code it could mutate; "
                         f"that is not a pass (report {report})")
    return lines


def verdict(service: str, given: list[str], report: str, files: dict[str, dict], dry_run: int | None = None,
            covering_only: bool = False, owners: dict[str, str] | None = None) -> int:
    mutants = judged(files, given)
    problems = unseen(service, given, report, files) if given else []
    for line in problems:
        say(line)
    if not mutants:
        if given and not problems:
            say(f"mutation: no mutant to run — {', '.join(given)}: Stryker found no mutant in "
                f"{'it' if len(given) == 1 else 'them'} (declarations and comments only: types, imports, plain constants)")
            return 0
        if given:
            return 1
        say(f"mutation: Stryker found nothing to mutate in {service}; a pass on nothing is not a pass")
        return 1
    why = {(name, id(one)): unexcused(service, name, files[name], one) for name, one in mutants
           if one.get("status") == "Ignored"}
    short = {(name, id(one)): incomplete(one, dry_run, covering_only, owners) for name, one in mutants}
    failing = [(name, one) for name, one in mutants
               if one.get("status") not in PASS + COUNTED or why.get((name, id(one)))]
    for name, one in failing:
        say(failure_line(service, name, one, report, why.get((name, id(one))), short[(name, id(one))]))
    counts = Counter(UNEXCUSED if why.get((name, id(one))) else INCOMPLETE if short[(name, id(one))]
                     else str(one.get("status")) for name, one in mutants)
    say(last_line(counts, bool(failing or problems), report))
    return 1 if failing or problems else 0


def run(job: Job) -> int:
    """Stryker over the given files (or the config's whole list), judged by the report it wrote, alone in its service:
    a second run waits, so neither removes the report the other is about to read (T038)."""
    name = hashlib.sha1(str(Path(job.service).resolve()).encode()).hexdigest()[:16]
    with file_lock(locks(project_root(Path(job.service))) / f"run-{name}.lock", f"the mutation of {job.service}") as held:
        return judge(job) if held else 2


def judge(job: Job) -> int:
    service, given = job.service, job.given
    directory = Path(service)
    clean(directory)
    if (directory / REPORT).exists():
        say(f"mutation: the previous report {service}/{REPORT} could not be removed; remove it, then run this again")
        return 2
    # `--force` runs every mutant even where `incremental` is on and an incremental file exists: a green never rests on
    # the results of an earlier run (T036, D212 item 7).
    # The config is named: Stryker 10 reads `stryker.conf.json`, `.js`, `.mjs`, `.cjs` and `stryker.config.js|mjs|cjs`
    # before `stryker.config.json` where none is, and the scope script reads only the last (T042, D213).
    command = ["npm", "exec", "--no", "--", "stryker", "run", CONFIG, "--force"]
    if given:
        say(f"mutation: scoped to {len(given)} given file(s): {', '.join(given)}")
        command += ["--mutate", ",".join(given)]
    code = subprocess.run(command, cwd=directory).returncode
    say(f"mutation: Stryker exited {code} (its exit status and the output above it are Stryker's, never the verdict; the report is)")
    report = f"{service}/{REPORT}"
    files = read_report(directory / REPORT)
    shutil.rmtree(directory / SANDBOX, ignore_errors=True)
    if files is None:
        say(f"mutation: Stryker exited {code} and left no readable report at {report}; that is not a pass")
        return 1
    return verdict(service, given, report, files, dry_run_tests(directory / REPORT), ignores_static(directory),
                   test_owners(directory / REPORT))


def refusal(job: Job) -> int | None:
    """A path `--mutate` would misread refuses the whole invocation: never a narrower or wider scope. So does a
    service directory whose own path Stryker would misread, whatever is given."""
    where = directory_refused(job.service)
    if where is not None:
        say(f"mutation: {where}")
        return 2
    for file in job.given:
        words = refused(job.service, file)
        if words is not None:
            say(f"mutation: {words}")
            return 2
    return None


def listed(job: Job) -> int | None:
    """Hold the files against the config's list: name what Stryker would not take, and stop where none is left. The
    sweep reads no pattern — Stryker evaluates its own list, and a list this reader cannot is exactly when the scope
    script sweeps (D213 item 3) — but it needs the config, without which Stryker would mutate its defaults."""
    if not job.given:
        if (Path(job.service) / CONFIG).is_file():
            return None
        say(f"mutation: {job.service}/{CONFIG}: no {CONFIG}")
        return 2
    try:
        patterns = targets(Path(job.service))
    except Unreadable as why:
        say(f"mutation: {job.service}/{CONFIG}: {why}")
        return 2
    kept = []
    for file in job.given:
        if matched(patterns, file):
            kept.append(file)
        else:
            say(f"mutation: not mutated {job.service}/{file} — outside Stryker's configured targets")
    if job.given and not kept:
        say(f"mutation: nothing under {job.service} that was given is a file Stryker would mutate; no mutant to run")
        return 0
    job.given = kept
    return None


# The order the rules fix, read in one place: each returns an exit status to stop with, or None to go on. A refusal
# comes before everything (nothing is looked up or deleted for a run that will not happen), `run` always ends it.
CHECKS = (refusal, listed, installed, run)


def main(arguments: list[str]) -> int:
    if arguments[:1] == ["--install"]:
        # The Makefile's install target: the same lock, the same `npm ci`, run only where the marker says it is due.
        if arguments != ["--install", "npm", "ci"]:
            say("mutation: usage: stryker-mutation.py --install npm ci")
            return 2
        return install(Path.cwd(), Path.cwd(), quiet=True) or 0
    parsed = parse(arguments)
    if parsed is None:
        say("mutation: usage: stryker-mutation.py <service> [--file <path within the service> ...]")
        return 2
    job = Job(parsed[0], [service_relative(Path(parsed[0]), file) for file in parsed[1]])
    for check in CHECKS:
        status = check(job)
        if status is not None:
            return status
    return 2  # unreachable: `run` returns a status


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
