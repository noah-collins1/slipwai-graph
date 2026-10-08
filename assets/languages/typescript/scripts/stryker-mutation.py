#!/usr/bin/env python3
"""`make mutation` and `make mutation-full` for a TypeScript service: Stryker, held to what its own report says.

    python3 scripts/stryker-mutation.py <service> [--file <path within the service> ...]

Without `--file` the whole of the service's `stryker.config.json` `mutate` list is mutated; `--file`, repeatable, hands
over only those files. The verdict is read from `<service>/reports/mutation/mutation.json`, never from Stryker's exit
status. Until the run itself is built out every run that reaches it is refused, the same refusal `make mutation-full`
printed before Stryker was wired, so that it can only fail and never pass.

The list of files Stryker mutates is the service's `mutate` patterns, and `--mutate` replaces that list rather than
narrowing it (Stryker mutates a file the config excludes if it is handed one), so a `--file` is first held against the
list here, by the subset of minimatch the factory writes: literal segments, `*` within a segment, `**` as a whole
segment, a leading `!` and a leading `./`. A pattern outside that subset is `Unreadable`, and the caller decides, never
this reader by guessing.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

CONFIG = "stryker.config.json"
# Characters a segment may not hold: each is minimatch syntax this reader does not evaluate.
SYNTAX = "?[]{}()+@\\!"
RANGE = re.compile(r":\d+(-\d+)?$")
STRYKER = "@stryker-mutator/"


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
        bad = next((char for char in SYNTAX if char in part), None)
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
        # The shortest key is the hoisted one; a nested copy of the same package never overrules it.
        for path in sorted(entries if isinstance(entries, dict) else {}, key=len):
            name = path.rsplit("node_modules/", 1)[-1]
            if name.startswith(STRYKER) and "node_modules/" in path and isinstance(entries[path], dict):
                found.setdefault(name, str(entries[path].get("version")))
        return found
    for table in ("dependencies", "devDependencies"):
        for name, version in (document.get(table) if isinstance(document.get(table), dict) else {}).items():
            if name.startswith(STRYKER):
                found[name] = str(version)
    return found


def versions(manifest_text: str | None = None, lock_text: str | None = None) -> dict[str, str]:
    """`{package: version}` for every `@stryker-mutator/*` entry of a manifest, a lock, or both (the lock's resolved
    version wins). What the scope script compares between the base and the working tree (D215 b)."""
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


def run(service: str, files: list[str]) -> int:
    say("mutation: Stryker is not wired by this script yet; a run that cannot be judged is not a pass.")
    return 2


def main(arguments: list[str]) -> int:
    parsed = parse(arguments)
    if parsed is None:
        say("mutation: usage: stryker-mutation.py <service> [--file <path within the service> ...]")
        return 2
    service, given = parsed
    try:
        patterns = targets(Path(service))
    except Unreadable as why:
        say(f"mutation: {service}/{CONFIG}: {why}")
        return 2
    kept = []
    for file in given:
        if matched(patterns, file):
            kept.append(file)
        else:
            say(f"mutation: not mutated {service}/{file} — outside Stryker's configured targets")
    if given and not kept:
        say(f"mutation: nothing under {service} that was given is a file Stryker would mutate; no mutant to run")
        return 0
    return run(service, kept)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
