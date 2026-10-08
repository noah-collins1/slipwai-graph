#!/usr/bin/env python3
"""`make mutation` and `make mutation-full` for a Python service: mutmut, held to what its own `.meta` files say.

    python3 scripts/mutmut-mutation.py <service> [--file <path within the service> ...]

Without `--file` the whole of the service's `[tool.mutmut]` `source_paths` is mutated; `--file`, repeatable, hands over
only those files. The verdict is read from the `mutants/<file>.meta` files mutmut writes, never from mutmut's exit status
(D212). This is the skeleton: it reads its arguments and refuses to run, which can only fail, never pass.
"""
from __future__ import annotations

import sys

USAGE = "mutation: usage: mutmut-mutation.py <service> [--file <path within the service> ...]"
NOT_WIRED = "mutation: mutmut is not wired by this script yet; nothing was run"


def parse(arguments: list[str]) -> tuple[str, list[str]] | None:
    """The service and the files handed over with `--file`, or None where the arguments are not that shape."""
    if not arguments or arguments[0].startswith("-"):
        return None
    files: list[str] = []
    rest = arguments[1:]
    while rest:
        if rest[0] != "--file" or len(rest) < 2:
            return None
        files.append(rest[1])
        rest = rest[2:]
    return arguments[0], files


def main(arguments: list[str]) -> int:
    if parse(arguments) is None:
        print(USAGE)
        return 2
    print(NOT_WIRED)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
