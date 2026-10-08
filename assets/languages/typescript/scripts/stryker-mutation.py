#!/usr/bin/env python3
"""`make mutation` and `make mutation-full` for a TypeScript service: Stryker, held to what its own report says.

    python3 scripts/stryker-mutation.py <service> [--file <path within the service> ...]

Without `--file` the whole of the service's `stryker.config.json` `mutate` list is mutated; `--file`, repeatable, hands
over only those files. The verdict is read from `<service>/reports/mutation/mutation.json`, never from Stryker's exit
status (D212): `Killed` and `Ignored` pass, `NoCoverage` is counted and reported, and every other status, a status
nobody has heard of included, fails; a run that leaves no readable report fails whatever Stryker exited.

The list of files Stryker mutates is the service's `mutate` patterns, and `--mutate` replaces that list rather than
narrowing it (Stryker mutates a file the config excludes if it is handed one), so a `--file` is first held against the
list here, by the subset of minimatch the factory writes: literal segments, `*` within a segment, `**` as a whole
segment, a leading `!` and a leading `./`. A pattern outside that subset is `Unreadable`, and the caller decides, never
this reader by guessing.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from collections import Counter
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
REPORT = "reports/mutation/mutation.json"
SANDBOX = ".stryker-tmp"
# The verdict of each status, in one place: anything not named here fails, so a status Stryker adds later fails closed.
PASS = ("Killed", "Ignored")
COUNTED = ("NoCoverage",)
# The version the factory pins both packages at (ADR 0009); this names it in the one line that says Stryker is missing.
PINNED = "10.0.0"
PACKAGES = ("core", "vitest-runner")
FAILED_AS = {"Survived": "survived", "Timeout": "timed out", "RuntimeError": "runtime error",
             "CompileError": "compile error", "Pending": "pending"}


class Unreadable(ValueError):
    """Something this reader does not claim to read; the message says what, and the caller says so and stops."""


def say(text: str) -> None:
    """A line of this script's own, flushed: Stryker writes to the same pipe from another process."""
    print(text, flush=True)


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
        for path, entry in (entries if isinstance(entries, dict) else {}).items():
            if "node_modules/" in path and path.rsplit("node_modules/", 1)[-1].startswith(STRYKER) \
                    and isinstance(entry, dict):
                found[path] = str(entry.get("version"))
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
    """Whether both Stryker packages are installed, looked for from the service up to the project root."""
    here, top, found = service.resolve(), root.resolve(), set()
    while True:
        found |= {name for name in PACKAGES if (here / "node_modules" / "@stryker-mutator" / name / "package.json").is_file()}
        if here == top or here.parent == here:
            return found == set(PACKAGES)
        here = here.parent


def installed(job: Job) -> int | None:
    """Exit 2 with one line where Stryker cannot be started, None where it can. Installs from the committed lock and
    never fetches: `npm ci` takes exactly the lock, and `npm exec --no` refuses to download what is not installed."""
    service, root = job.service, Path.cwd()
    if shutil.which("npm") is None:
        wanted = root / ".nvmrc"
        node = wanted.read_text(encoding="utf-8").strip() if wanted.is_file() else ""
        say(f"mutation: npm is not on PATH; install Node{' ' + node if node else ''} to run Stryker")
        return 2
    if stale(root, Path(service)):
        say("mutation: installing from the committed lock (npm ci)")
        done = subprocess.run(["npm", "ci"], cwd=root)
        if done.returncode != 0:
            say(f"mutation: npm ci failed (exit {done.returncode}); fix the install, then run this again")
            return 2
        marker = root / "node_modules" / ".package-lock.json"
        marker.parent.mkdir(exist_ok=True)
        marker.touch()
    if not stryker_present(root, Path(service)):
        say(f"mutation: Stryker is not installed in this project: add @stryker-mutator/core and @stryker-mutator/vitest-runner "
            f"{PINNED} to {service}/package.json's devDependencies and run npm install")
        return 2
    return None


class Job:
    """One invocation: the service, and the files handed over (narrowed by the list check to those Stryker would take)."""

    def __init__(self, service: str, given: list[str]) -> None:
        self.service, self.given = service, given


def clean(service: Path) -> None:
    """Every run starts from nothing: an earlier report must not be able to pass a run that wrote none, and an earlier
    sandbox is not this run's."""
    shutil.rmtree(service / "reports" / "mutation", ignore_errors=True)
    shutil.rmtree(service / SANDBOX, ignore_errors=True)


def read_report(path: Path) -> dict[str, dict] | None:
    """The report's `files`, or None where there is no readable report."""
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    files = document.get("files") if isinstance(document, dict) else None
    return files if isinstance(files, dict) else None


def judged(files: dict[str, dict], given: list[str]) -> list[tuple[str, dict]]:
    """The mutants the verdict is about: those of the given files, or of every file in the report when none were given."""
    wanted = [name[2:] if name.startswith("./") else name for name in given]
    return [(name, one) for name in sorted(files) if not wanted or name in wanted
            for one in (files[name].get("mutants") or []) if isinstance(one, dict)]


def failure_line(service: str, name: str, one: dict, report: str) -> str:
    start = (one.get("location") or {}).get("start") or {}
    replacement = " ".join(str(one.get("replacement", "")).split())
    return (f"mutation: {one.get('status')} {service}/{name}:{start.get('line')}:{start.get('column')} "
            f"{one.get('mutatorName')} → {replacement} (report {report})")


def last_line(counts: Counter, failed: bool, report: str) -> str:
    total = sum(counts.values())
    text = (f"mutation: {total} mutants: {counts['Killed']} killed, {counts['Ignored']} ignored, "
            f"{counts['NoCoverage']} not covered (reported, never failed)")
    for status, count in sorted(counts.items(), key=lambda item: (item[0] not in FAILED_AS, item[0])):
        if status not in PASS + COUNTED:
            text += f", {count} {FAILED_AS.get(status, status)}"
    return f"{text}; {'failed' if failed else 'passed'} — report {report}"


def verdict(service: str, given: list[str], report: str, files: dict[str, dict]) -> int:
    mutants = judged(files, given)
    if not mutants:
        if given:
            say(f"mutation: no mutant to run — {', '.join(given)}: Stryker found no mutant in them (types or comments only)")
            return 0
        say(f"mutation: Stryker found nothing to mutate in {service}; a pass on nothing is not a pass")
        return 1
    failing = [(name, one) for name, one in mutants if one.get("status") not in PASS + COUNTED]
    for name, one in failing:
        say(failure_line(service, name, one, report))
    say(last_line(Counter(str(one.get("status")) for _, one in mutants), bool(failing), report))
    return 1 if failing else 0


def run(job: Job) -> int:
    """Stryker over the given files (or the config's whole list), judged by the report it wrote."""
    service, given = job.service, job.given
    directory = Path(service)
    clean(directory)
    command = ["npm", "exec", "--no", "--", "stryker", "run"]
    if given:
        say(f"mutation: scoped to {len(given)} given file(s): {', '.join(given)}")
        command += ["--mutate", ",".join(given)]
    code = subprocess.run(command, cwd=directory).returncode
    say(f"mutation: Stryker exited {code} (its exit status is printed, never the verdict; the report is)")
    report = f"{service}/{REPORT}"
    files = read_report(directory / REPORT)
    shutil.rmtree(directory / SANDBOX, ignore_errors=True)
    if files is None:
        say(f"mutation: Stryker exited {code} and left no readable report at {report}; that is not a pass")
        return 1
    return verdict(service, given, report, files)


def refusal(job: Job) -> int | None:
    """A path `--mutate` would misread refuses the whole invocation: never a narrower or wider scope."""
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
    parsed = parse(arguments)
    if parsed is None:
        say("mutation: usage: stryker-mutation.py <service> [--file <path within the service> ...]")
        return 2
    job = Job(*parsed)
    for check in CHECKS:
        status = check(job)
        if status is not None:
            return status
    return 2  # unreachable: `run` returns a status


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
