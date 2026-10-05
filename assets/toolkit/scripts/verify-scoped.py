#!/usr/bin/env python3
"""`make verify-scoped`: the checks whose inputs changed on a slice branch, and the full gate wherever it cannot tell.

`run --make <make> --makefile <file>` is what the target's recipe calls. It asks a fixed list of borders, in order,
and the first that holds prints one line, `verify-scoped: the full gate runs, as `make verify` — <reason>`, and runs
`make verify` with its status: the stamp's reuse and record are that target's, not this script's. The borders are the
places this script cannot read the branch: a make that starts no check, a CI run, a forced run, a `HEAD` that names no
branch or no commit, the trunk itself, a branch that is no `slice/<id>`, a branch with no usable base, a trunk the gate
cannot tell. A scoped selection is built on top of them, in later rules; until then a slice branch with a usable base is
the full gate as well, so the target is never wrong in between.

Nothing here writes the stamp or any file. `verify-stamp.py` and `check-slice-scope.py` beside this script are loaded,
never copied, so the trunk, the base and the stamp's own words are the ones the gate uses.
"""
from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from typing import Any, Callable

sys.dont_write_bytecode = True  # an untracked file under scripts/ would make every later scoped run the full gate

HERE = os.path.dirname(os.path.abspath(__file__))
LINE = "verify-scoped: "
FULL = LINE + "the full gate runs, as `make verify` — {reason}"
NOT_BUILT = "every check is chosen until the selection is built"


def load(name: str, filename: str) -> Any:
    """A script beside this one, loaded and never copied."""
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, filename))
    if spec is None or spec.loader is None:
        raise ImportError("cannot load " + filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Ground:
    """What the borders ask about: the stamp's and the slice scope's own modules, and where `HEAD` stands."""

    def __init__(self) -> None:
        self.stamp = load("verify_stamp_for_the_scope", "verify-stamp.py")
        self.scope = self.stamp.trunk_module()
        ref = self.stamp.git_or_nothing("symbolic-ref", "-q", "HEAD").removesuffix(b"\n")
        self.ref = ref.decode("utf-8", "surrogateescape")
        self.has_commit = bool(self.stamp.git_or_nothing("rev-parse", "-q", "--verify", "HEAD"))
        self.branch = self.ref.removeprefix("refs/heads/")


Border = Callable[[Ground], "str | None"]


def idle(ground: Ground) -> str | None:
    flags = ground.stamp.make_flags()
    return f"make was run with -{flags}" if any(letter in flags for letter in ground.stamp.IDLE_FLAGS) else None


def ci(ground: Ground) -> str | None:
    for marker in ground.stamp.CI_MARKERS:
        if os.environ.get(marker):
            return f"{marker} is set, so this is a CI run"
    return None


def forced(ground: Ground) -> str | None:
    return ground.stamp.forced_reason(None)


def head(ground: Ground) -> str | None:
    if not ground.ref.startswith("refs/heads/"):
        return "HEAD is detached"
    return None if ground.has_commit else "HEAD names no commit"


def trunk(ground: Ground) -> str | None:
    named = str(ground.scope.merge_base().named)
    return f"this is the trunk (`{ground.scope.printable(named)}`)" if ground.branch == named else None


def slice_branch(ground: Ground) -> str | None:
    if ground.scope.SLICE_BRANCH.match(ground.branch):
        return None
    return f"`{ground.scope.printable(ground.branch)}` is not a slice/<id> branch"


def base(ground: Ground) -> str | None:
    if ground.scope.merge_base().commit is not None:
        return None
    words = ground.scope.check(ground.branch)[3].removeprefix("check-slice-scope: ")
    return f"{ground.branch} has no usable base — {words}"


def told(ground: Ground) -> str | None:
    problem = ground.stamp.trunk_problem()[1]
    return None if problem is None else f"the trunk cannot be told — {problem}"


# In the order they are asked: a case where two hold prints the first only.
BORDERS: tuple[Border, ...] = (idle, ci, forced, head, trunk, slice_branch, base, told)


def reason() -> str:
    """Why the full gate runs, from the first border that holds; and where none does, that nothing is selected yet."""
    try:
        ground = Ground()
        for border in BORDERS:
            found = border(ground)
            if found is not None:
                return found
    except Exception as error:  # a checkout this script cannot read is one it cannot scope
        return "the checkout could not be read (" + str(error).replace("\n", " ")[:120] + ")"
    return NOT_BUILT


def run(make: str, makefile: str) -> int:
    print(FULL.format(reason=reason()), flush=True)
    # close_fds=False keeps the jobserver's descriptors for the sub-make, so `make -j verify-scoped` still runs at once
    command = [make, "--no-print-directory", "-f", makefile, "verify"]
    return subprocess.run(command, close_fds=False, check=False).returncode


def main(argv: list[str]) -> int:
    options = dict(zip(argv[1::2], argv[2::2], strict=False))
    if argv[:1] != ["run"] or len(argv) % 2 == 0 or not set(options) <= {"--make", "--makefile"}:
        print("usage: verify-scoped.py run [--make <make>] [--makefile <file>]", file=sys.stderr)
        return 2
    return run(options.get("--make", "make"), options.get("--makefile", "Makefile"))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
