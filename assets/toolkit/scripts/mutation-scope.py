"""`make mutation`: the mutation run priced per change where a tool is wired, and the sweep wherever it is not told.

`--make <make> --makefile <file> <backend>:<path> …` is what the target's recipe calls, one word per generated service
in service order. The checkouts this script cannot scope are the borders `verify-scoped.py` asks, loaded from it and
never copied: on any of them it prints one line, `mutation: the sweep runs — <reason>`, and runs `make mutation-full`
(the recipe `make mutation` was before it was scoped) with its status. An adopted layout, which has no scope, says so
and runs the same recorded command. The rules that scope a run on a slice branch are added to it one at a time and
none changes the recipe line.

Nothing here writes a file of the project's: the script sets `sys.dont_write_bytecode` before it loads anything.
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from typing import Any, Mapping, Protocol

sys.dont_write_bytecode = True  # an untracked file under scripts/ would make every later scoped run the full gate

HERE = os.path.dirname(os.path.abspath(__file__))
LINE = "mutation: "
SWEEPS = "the sweep runs — {reason}"
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


# The borders of `verify-scoped.py` this script asks, in the order it asks them. `idle` and `forced` are the stamp's.
BORDERS = ("ci", "head", "trunk", "slice_branch", "base", "told")
NO_SCOPE = "this layout has no mutation scope — the recorded command runs"
NO_SERVICE = "no generated service to scope"
EMPTY_SINCE = "SINCE is set and empty"


def say(text: str) -> None:
    """The only place a `mutation:` line is spelled."""
    print(LINE + text, flush=True)


def unreadable(error: BaseException) -> str:
    return "the checkout could not be read (" + str(error).replace("\n", " ")[:120] + ")"


def scoped_gate() -> Any:
    """`verify-scoped.py` beside this script, loaded and never copied: the borders and the trunk are the gate's own."""
    spec = importlib.util.spec_from_file_location("verify_scoped_for_the_mutation_scope", os.path.join(HERE, "verify-scoped.py"))
    if spec is None or spec.loader is None:
        raise ImportError("cannot load verify-scoped.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def ground() -> Any:
    """Where `HEAD` stands, as `verify-scoped.py` reads it."""
    return scoped_gate().Ground()


def sweep_reason(env: Mapping[str, str], where: Any) -> str | None:
    """Why the whole run sweeps, from the first border that holds; None where none does. A border that cannot be asked
    is a checkout this script cannot scope, which is a sweep and not a crash."""
    if env.get("SINCE") == "":
        return EMPTY_SINCE
    try:
        gate = scoped_gate()
        for name in BORDERS:
            found = getattr(gate, name)(where)
            if found is not None:
                return str(found)
    except Exception as error:
        return unreadable(error)
    return None


def delivery_moved() -> bool:
    """Whether `project.json` records `layout.delivery` somewhere other than the root: an adopted layout (experimental)."""
    try:
        with open("project.json", encoding="utf-8") as handle:
            layout = json.load(handle).get("layout")
    except (OSError, ValueError, AttributeError):
        return False
    return isinstance(layout, dict) and layout.get("delivery", ".") != "."


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
    make, makefile = options["--make"], options["--makefile"]
    if delivery_moved():
        say(NO_SCOPE)
        return full(make, makefile)
    found = NO_SERVICE if not rest else None
    if found is None:
        try:
            where = None if os.environ.get("SINCE") == "" else ground()
        except Exception as error:
            where, found = None, unreadable(error)
        found = found or sweep_reason(os.environ, where)
    if found is not None:
        say(SWEEPS.format(reason=found))
    return full(make, makefile)  # past the borders the run is still the sweep, until the scope is built on top of them


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
