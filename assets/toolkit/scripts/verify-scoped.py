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
sys.path.insert(0, HERE)

from verify_scoped import choose  # noqa: E402
from verify_scoped import record as records  # noqa: E402

LINE = "verify-scoped: "
FULL = LINE + "the full gate runs, as `make verify` — {reason}"
EVERY = LINE + "every check runs, as no selection is built yet; the stamp is left as it is"


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


def reason(ground: Ground) -> str | None:
    """Why the full gate runs, from the first border that holds; None where none does."""
    try:
        for border in BORDERS:
            found = border(ground)
            if found is not None:
                return found
    except Exception as error:  # a checkout this script cannot read is one it cannot scope
        return "the checkout could not be read (" + str(error).replace("\n", " ")[:120] + ")"
    return None


def standing(ground: Ground, make: str, data: records.Database | None) -> str | None:
    """verify-stamp's reuse line where its stamp stands for this tree and this machine; nothing is written or removed.
    The key is built with the tools and environments the project's own `verify` recipe hands the stamp script, which
    the make database holds as `VERIFY_STAMP`."""
    stamp = ground.stamp
    try:
        found = data.variables.get("VERIFY_STAMP") if data is not None else None
        usable, cannot = stamp.standing()
        if found is None or cannot is not None or not usable or stamp.ratcheting() or stamp.declined():
            return None
        if stamp.index_problem(stamp.top_level()) is not None:
            return None
        key = stamp.build_key(stamp.machine_tools(stamp.Options(["--make", make, *found.split()])))
    except (stamp.CannotTell, ValueError, OSError, subprocess.SubprocessError):
        return None
    held = stamp.read_stamp(stamp.stamp_path())
    if held is None or held["key"] != key["key"]:
        return None
    return str(stamp.REUSE_LINE.format(passed=held["passed"], abbreviated=str(key["key"])[:12]))


def full_gate(make: str, makefile: str, *goals: str) -> int:
    # close_fds=False keeps the jobserver's descriptors for the sub-make, so `make -j verify-scoped` still runs at once
    command = [make, "--no-print-directory", "-f", makefile, *goals]
    return subprocess.run(command, close_fds=False, check=False).returncode


def selected(
    ground: Ground, make: str, makefile: str, data: records.Database,
) -> tuple[list[choose.Choice], dict[str, Any]]:
    """What the change since the base chooses, in the record's order, and the record it was chosen from."""
    base = records.base_of(ground.scope)
    record = records.build(make, makefile, ground.scope, data, base)
    return choose.choose(record, data, sorted(ground.scope.changed_files(base))), record


def run(make: str, makefile: str) -> int:
    try:
        ground = Ground()
    except Exception as error:  # a checkout this script cannot read is one it cannot scope
        words = "the checkout could not be read (" + str(error).replace("\n", " ")[:120] + ")"
        print(FULL.format(reason=words), flush=True)
        return full_gate(make, makefile, "verify")
    found = reason(ground)
    if found is not None:
        print(FULL.format(reason=found), flush=True)
        return full_gate(make, makefile, "verify")
    try:
        data: records.Database | None = records.database(make, makefile)
    except records.RecordError:
        data = None
    reused = standing(ground, make, data)
    if reused is not None:
        print(reused, flush=True)
        return 0
    try:
        assert data is not None
        choices, record = selected(ground, make, makefile, data)
    except Exception:  # until the borders of an unreadable record are drawn, every check runs
        print(EVERY, flush=True)
        return full_gate(make, makefile, "verify-checks", "VERIFY_ORDER=1")
    for choice in choices:
        print(LINE + (f"run  {choice.unit} — " if choice.runs else f"skip {choice.unit} — ") + choice.reason,
              flush=True)
    targets = [target for choice in choices if choice.runs for target in record["checks"][choice.unit]["targets"]]
    if not targets:
        return 0
    command = [make, *targets, "VERIFY_ORDER=1", "--no-print-directory", "-f", makefile]
    return subprocess.run(command, close_fds=False, check=False).returncode


def record(make: str, makefile: str) -> int:
    """Print the record; where it cannot be built, one line on stderr, nothing on stdout, and status 1."""
    try:
        scope = load("verify_stamp_for_the_scope", "verify-stamp.py").trunk_module()
        text = records.render(records.build(make, makefile, scope))
    except records.RecordError as error:
        print(LINE + "the record cannot be built — " + str(error).replace("\n", " "), file=sys.stderr)
        return 1
    except Exception as error:  # a checkout this script cannot read is one it cannot record
        print(LINE + "the record cannot be built — " + str(error).replace("\n", " ")[:160], file=sys.stderr)
        return 1
    sys.stdout.write(text)
    return 0


VERBS = {"run": run, "record": record}


def main(argv: list[str]) -> int:
    options = dict(zip(argv[1::2], argv[2::2], strict=False))
    if argv[:1] not in (["run"], ["record"]) or len(argv) % 2 == 0 or not set(options) <= {"--make", "--makefile"}:
        print("usage: verify-scoped.py run|record [--make <make>] [--makefile <file>]", file=sys.stderr)
        return 2
    return VERBS[argv[0]](options.get("--make", "make"), options.get("--makefile", "Makefile"))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
