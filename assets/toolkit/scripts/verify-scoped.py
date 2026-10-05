#!/usr/bin/env python3
"""`make verify-scoped`: the checks whose inputs changed on a slice branch, and the full gate wherever it cannot tell.

`run --make <make> --makefile <file>` is what the target's recipe calls. It asks a fixed list of borders, in order,
and the first that holds prints one line, `verify-scoped: the full gate runs, as `make verify` — <reason>`, and runs
`make verify` with its status: the stamp's reuse and record are that target's, not this script's. The borders are the
places this script cannot read the branch: a make that starts no check, a CI run, a forced run, a `HEAD` that names no
branch or no commit, the trunk itself, a branch that is no `slice/<id>`, a branch with no usable base, a trunk the gate
cannot tell. A scoped selection is built on top of them, in later rules; until then a slice branch with a usable base is
the full gate as well, so the target is never wrong in between.

Nothing here writes the stamp or a file of this script's own; the one write beside it is the model loader's, which may
install `yaml` into `.delivery-tools` where `check-model` would. `verify-stamp.py` and `check-slice-scope.py` beside this script are loaded,
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
from verify_scoped import rules  # noqa: E402

LINE = "verify-scoped: "
FULL = LINE + "the full gate runs, as `make verify` — {reason}"
INCOMPLETE = "dependency knowledge was incomplete"
EVERY = "every check was chosen"
IGNORED = "a file git ignores differs from the baseline"


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


def compared(ground: Ground, make: str, data: records.Database) -> tuple[choose.Drift | None, str]:
    """How the machine stands against the baseline a green full run left: the drift, or None with why there is no
    baseline to compare with. The tools are asked once, as the stamp asks them, and nothing is written."""
    stamp = ground.stamp
    try:
        path = stamp.baseline_path()
        found, why = choose.baseline_of(stamp.read_own(path), ground.branch, os.path.lexists(path))
    except stamp.CannotTell:
        return None, "it cannot be read"
    if found is None:
        return None, why
    named = data.variables.get("VERIFY_STAMP")
    if named is None:
        return None, "the gate does not name the tools the stamp asks"
    try:
        tools = stamp.machine_tools(stamp.Options(["--make", make, *named.split()]))
        ignored = stamp.key_parts(tools)[1]["ignored"]  # the stamp's own digest of the files git ignores, never a copy
    except (stamp.CannotTell, OSError, subprocess.SubprocessError) as error:
        return None, words(error)
    return choose.drift(found, tools, stamp.variable_digests(), ignored), ""


def full_gate(make: str, makefile: str, *goals: str) -> int:
    # close_fds=False keeps the jobserver's descriptors for the sub-make, so `make -j verify-scoped` still runs at once
    command = [make, "--no-print-directory", "-f", makefile, *goals]
    return subprocess.run(command, close_fds=False, check=False).returncode


def broaden(make: str, makefile: str, reason: str, notes: list[str] | None = None, then: str | None = None) -> int:
    """The full gate, `make verify`, with its status: what is said first (one line each), then why it runs, then, where
    there is one, a line of advice."""
    for note in notes or []:
        print(LINE + note, flush=True)
    print(FULL.format(reason=reason), flush=True)
    if then is not None:
        print(LINE + then, flush=True)
    return full_gate(make, makefile, "verify")


def incomplete(make: str, makefile: str, why: str) -> int:
    return broaden(make, makefile, INCOMPLETE, [f"{INCOMPLETE} — {why}"])


def words(error: BaseException) -> str:
    return str(error).replace("\n", " ")[:160]


def run(make: str, makefile: str) -> int:
    try:
        ground = Ground()
    except Exception as error:  # a checkout this script cannot read is one it cannot scope
        return broaden(make, makefile, "the checkout could not be read (" + words(error) + ")")
    found = reason(ground)
    if found is not None:
        return broaden(make, makefile, found)
    try:  # the text of the Makefile before any read of it: a project's own is never parsed by a scoped run (D140)
        foreign = rules.text_problem(makefile, os.path.join(str(ground.scope.ROOT), records.RULES_FILE), os.environ)
    except Exception as error:  # text this script cannot compare is text it cannot scope
        return broaden(make, makefile, "the Makefile's text could not be compared (" + words(error) + ")")
    if foreign is not None:
        return broaden(make, makefile, foreign)
    conditions = ground.stamp.makeflags_problem()  # text or conditions make was handed (D146): the stamp's one predicate
    if conditions is not None:
        return broaden(make, makefile, conditions + "; " + rules.ADVICE)
    try:
        data: records.Database | None = records.database(make, makefile)
    except records.RecordError:
        data = None
    reused = standing(ground, make, data)
    if reused is not None:
        print(reused, flush=True)
        return 0
    try:
        base = records.base_of(ground.scope)
        if data is None:
            data = records.database(make, makefile)  # the same words the record gives, where it cannot be read
        record = records.build(make, makefile, ground.scope, data, base)
        changed = sorted(ground.scope.changed_files(base))
    except records.FullGate as error:  # matching text that make reads differently: knowledge this script does not have
        return incomplete(make, makefile, str(error).replace("\n", " "))
    except records.ObligationError as error:  # a person's declaration is named on a line of its own
        return broaden(make, makefile, INCOMPLETE, [str(error).replace("\n", " ")])
    except records.RecordError as error:
        return incomplete(make, makefile, str(error).replace("\n", " "))
    except Exception as error:  # what cannot be read is knowledge this script does not have
        return incomplete(make, makefile, words(error))
    gate = ground.stamp.is_gate_script
    notes = [f"{INCOMPLETE} for {ground.scope.printable(path)} — {why}" for path, why in choose.unknown(
        record, changed, lambda path: bool(gate(path.encode("utf-8", "surrogateescape"))))]
    if notes:
        return broaden(make, makefile, INCOMPLETE, notes)
    drifted, why = compared(ground, make, data)
    if drifted is None:  # with no baseline every reader runs, and every check reads `make`
        note = f"no usable baseline ({why}) — every check that reads a tool or a variable runs"
        return broaden(make, makefile, EVERY, [note])
    if drifted.ignored:  # a check reads a file git ignores, and no changed path names one: as the stamp's key has it (D125)
        return broaden(make, makefile, IGNORED, then=ground.stamp.WRITTEN_IGNORED.removeprefix(" — "))
    choices = choose.choose(record, data, changed, drifted)
    if all(choice.runs for choice in choices):
        return broaden(make, makefile, EVERY)
    for choice in choices:
        print(LINE + (f"run  {choice.unit} — " if choice.runs else f"skip {choice.unit} — ") + choice.reason,
              flush=True)
    targets = list(dict.fromkeys(  # a whole gate's units all name the gate, once
        target for choice in choices if choice.runs for target in record["checks"][choice.unit]["targets"]))
    status = 0
    if targets:
        # the gate's own output grouping, where this make has it; close_fds=False hands the sub-make the jobserver
        group = data.variables.get("VERIFY_GROUP", "").split()
        command = [make, *group, "--no-print-directory", "-f", makefile, *targets, "VERIFY_ORDER=1"]
        status = subprocess.run(command, close_fds=False, check=False).returncode
    ran = sum(choice.runs for choice in choices)
    print(LINE + closing(ground.scope, base, ran, len(choices) - ran, status == 0), flush=True)
    return status


def closing(scope: Any, base: str | None, ran: int, skipped: int, passed: bool) -> str:
    """The last line: what was run and skipped, what it was compared with, and how it ended."""
    named = scope.printable(str(scope.merge_base().named))
    short = ((scope.git("rev-parse", "--short", base) if base else None) or str(base)[:7]).strip()
    ended = "passed" if passed else ("the scoped gate did not pass — each failed check is named above on a line "
                                     "carrying ***")
    return f"{ran} run, {skipped} skipped, compared with `{named}` at {short}; {ended}"


def record(make: str, makefile: str) -> int:
    """Print the record; where it cannot be built, one line on stderr, nothing on stdout, and status 1."""
    try:
        scope = load("verify_stamp_for_the_scope", "verify-stamp.py").trunk_module()
        try:
            built = records.build(make, makefile, scope)
        except records.FullGate as error:  # the record is still what it is, with each charged difference marked
            built = error.built
        text = records.render(built)
    except records.RecordError as error:
        print(LINE + "the record cannot be built — " + str(error).replace("\n", " "), file=sys.stderr)
        return 1
    except Exception as error:  # a checkout this script cannot read is one it cannot record
        print(LINE + "the record cannot be built — " + words(error), file=sys.stderr)
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
