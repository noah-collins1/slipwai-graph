#!/usr/bin/env python3
"""`make mutation` and `make mutation-full` for a TypeScript service: Stryker, held to what its own report says.

    python3 scripts/stryker-mutation.py <service> [--file <path within the service> ...]

Without `--file` the whole of the service's `stryker.config.json` `mutate` list is mutated; `--file`, repeatable, hands
over only those files. The verdict is read from `<service>/reports/mutation/mutation.json`, never from Stryker's exit
status. This is a skeleton: it parses its arguments and refuses every run, the same refusal `make mutation-full` printed
before Stryker was wired, so that it can only fail and never pass until it is built out.
"""
from __future__ import annotations

import sys


def say(text: str) -> None:
    """A line of this script's own, flushed: Stryker writes to the same pipe from another process."""
    print(text, flush=True)


def parse(arguments: list[str]) -> tuple[str, list[str]] | None:
    """The service and the `--file` values, or None where the arguments are not `<service> [--file <path> ...]`."""
    if not arguments or arguments[0].startswith("-"):
        return None
    service, files, rest = arguments[0], [], arguments[1:]
    while rest:
        if rest[0] != "--file" or len(rest) < 2:
            return None
        files.append(rest[1])
        rest = rest[2:]
    return service, files


def main(arguments: list[str]) -> int:
    parsed = parse(arguments)
    if parsed is None:
        say("mutation: usage: stryker-mutation.py <service> [--file <path within the service> ...]")
        return 2
    say("mutation: Stryker is not wired by this script yet; a run that cannot be judged is not a pass.")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
