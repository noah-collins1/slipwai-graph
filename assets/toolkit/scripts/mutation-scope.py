#!/usr/bin/env python3
"""`make mutation`: the mutation run priced per change where a tool is wired, and the sweep wherever it is not told.

`--make <make> --makefile <file> <backend>:<path> …` is what the target's recipe calls, one word per generated service
in service order. This script runs `make mutation-full` (the recipe `make mutation` was before it was scoped) with its
status; the rules that scope a run on a slice branch are added to it one at a time and none changes the recipe line.

Nothing here writes a file of the project's: the script sets `sys.dont_write_bytecode` before it loads anything.
"""
from __future__ import annotations

import subprocess
import sys
from typing import Protocol

sys.dont_write_bytecode = True  # an untracked file under scripts/ would make every later scoped run the full gate

LINE = "mutation: "
BACKENDS = ("go", "java-spring", "java-quarkus", "typescript", "python")
USAGE = LINE + "usage: mutation-scope.py --make <make> --makefile <file> <backend>:<path> …"


class Runner(Protocol):
    """What runs one service's tool; a test's fake stands in for it, and the default is the real tool."""

    def run(self, backend: str, path: str, files: list[str]) -> int: ...


def services_of(words: list[str]) -> list[tuple[str, str]] | None:
    """Each `<backend>:<path>` word as a pair, or None where one names no backend this script knows."""
    found = []
    for word in words:
        backend, _, path = word.partition(":")
        if backend not in BACKENDS or not path:
            return None
        found.append((backend, path))
    return found


def full(make: str, makefile: str) -> int:
    """The sweep: `make mutation-full`, its status the run's. close_fds=False keeps a jobserver's descriptors."""
    command = [make, "--no-print-directory", "-f", makefile, "mutation-full"]
    return subprocess.run(command, close_fds=False, check=False).returncode


def main(argv: list[str]) -> int:
    options: dict[str, str] = {}
    rest = list(argv)
    while rest[:1] in (["--make"], ["--makefile"]) and len(rest) >= 2:
        options[rest[0]] = rest[1]
        rest = rest[2:]
    services = services_of(rest)
    if services is None or set(options) != {"--make", "--makefile"}:
        print(USAGE, file=sys.stderr)
        return 2
    return full(options["--make"], options["--makefile"])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
