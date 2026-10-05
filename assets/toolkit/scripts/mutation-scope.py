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
import unicodedata
from typing import Any, Mapping, NamedTuple, Protocol

sys.dont_write_bytecode = True  # an untracked file under scripts/ would make every later scoped run the full gate

HERE = os.path.dirname(os.path.abspath(__file__))
LINE = "mutation: "
SWEEPS = "the sweep runs — {reason}"
BACKENDS = ("go", "java-spring", "java-quarkus", "typescript", "python")
USAGE = LINE + "usage: mutation-scope.py --make <make> --makefile <file> <backend>:<path> …"


class Result(NamedTuple):
    """What one service's tool run came to: its exit status, the files (relative to the service) it mutated, each file it
    would not mutate with the reason, and, where there is no tool to run, the words of the refusal."""

    status: int
    files: list[str]
    skipped: list[tuple[str, str]]
    refusal: str | None = None


class Runner(Protocol):
    """What runs one service's tool; a test's fake stands in for it, and the default is the real tool."""

    def run(self, backend: str, path: str, files: list[str]) -> Result: ...


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


class Sweep(Exception):
    """The whole run is the sweep, for the reason this carries."""


class Refused(Exception):
    """The run cannot start, for the reason this carries: status 2, nothing run."""


def shown(text: str) -> str:
    """A name the gate did not choose, as it may be printed: control and line-separating characters dropped and a
    backtick made an apostrophe, so it can forge no line and end no span early."""
    return "".join("'" if char == "`" else char for char in text
                   if unicodedata.category(char)[0] != "C" and unicodedata.category(char) not in ("Zl", "Zp"))


def resolved(scope: Any, ref: str) -> str:
    """The commit `SINCE` names, or a refusal naming it."""
    found = scope.git("rev-parse", "--verify", "--end-of-options", ref + "^{commit}")
    if not found or not found.strip():
        raise Refused(f"SINCE `{shown(ref)}` names no commit")
    return str(found.strip())


def change_set(env: Mapping[str, str]) -> tuple[str, dict[str, str]]:
    """What the run is compared with, in words, and the paths that differ from it with their status. The borders are
    asked unless `SINCE` names a commit, which scopes on any checkout; a checkout that cannot be read is a sweep."""
    since = env.get("SINCE")
    if since == "":
        raise Sweep(EMPTY_SINCE)
    try:
        where = ground()
        if since is None:
            found = sweep_reason(env, where)
            if found is not None:
                raise Sweep(found)
            scope = where.scope
            base = scope.merge_base()
            short = (scope.git("rev-parse", "--short", base.commit) or str(base.commit)[:7]).strip()
            return f"`{shown(str(base.named))}` at {short}", dict(scope.changed_files(base.commit))
        return f"`{shown(since)}`", dict(where.scope.changed_files(resolved(where.scope, since)))
    except (Sweep, Refused):
        raise
    except Exception as error:
        raise Sweep(unreadable(error)) from error


def go_kind(path: str) -> str:
    return ("test" if path.endswith("_test.go") else "production") if path.endswith(".go") else "other"


def java_kind(path: str) -> str:
    if path.startswith("src/test/"):
        return "test"
    named = path.rsplit("/", 1)[-1]
    on = path.startswith("src/main/java/") and path.endswith(".java")
    return "production" if on and named not in ("package-info.java", "module-info.java") else "other"


def typescript_kind(path: str) -> str:
    named = path.rsplit("/", 1)[-1]
    if path.startswith("tests/") or ".test." in named or ".spec." in named:
        return "test"
    scripted = named.endswith((".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".mts", ".cts"))
    return "production" if path.startswith("src/") and scripted and not named.endswith(".d.ts") else "other"


def python_kind(path: str) -> str:
    if path.startswith("tests/"):
        return "test"
    return "production" if path.startswith("src/") and path.endswith(".py") else "other"


# Production, test or other for a path within a service, per backend: one table, so `classify` asks one place.
KINDS = {"go": go_kind, "java-spring": java_kind, "java-quarkus": java_kind, "typescript": typescript_kind,
         "python": python_kind}


def classify(path: str, status: str, services: list[tuple[str, str]]) -> tuple[str, str, str]:
    """`(class, service path, path within the service)` for one changed path: shared, deleted, test, production or other."""
    if path.startswith("packages/"):
        return "shared", "", path
    owners = [(backend, root) for backend, root in services if path.startswith(root + "/")]
    if not owners:
        return "other", "", path
    backend, root = max(owners, key=lambda owner: len(owner[1]))
    inside = path[len(root) + 1:]
    kind = KINDS[backend](inside)
    return ("deleted" if status == "D" and kind == "production" else kind), root, inside


class Unwired:
    """The runner until a tool is wired for a backend: it refuses, so the target can fail but never pass."""

    def run(self, backend: str, path: str, files: list[str]) -> Result:
        return Result(2, [], [], f"no runner for {backend}")


def scope(services: list[tuple[str, str]], words: str, changes: dict[str, str], runner: Runner) -> int:
    """The scoped run: what changed, classified, then each service once in service order, then the closing line."""
    shared: list[str] = []
    deleted: list[str] = []
    tests: list[str] = []
    production: dict[str, list[str]] = {}
    for path in sorted(changes):
        kind, root, inside = classify(path, changes[path], services)
        if kind == "shared":
            shared.append(path)
        elif kind == "deleted":
            deleted.append(path)
        elif kind == "test":
            tests.append(path)
        elif kind == "production":
            production.setdefault(root, []).append(inside)
    named = sorted(f"{root}/{inside}" for root, found in production.items() for inside in found)
    if named:
        say(f"scoped to {len(named)} changed file(s) since {words}: {', '.join(shown(name) for name in named)}")
    elif tests:
        say(f"no mutant to run — only tests changed: {', '.join(shown(name) for name in tests)}; "
            "`make mutation-full` is the run that measures them")
    else:
        say("no mutant to run — no production file changed")
    for path in shared:
        say(f"not mutated {shown(path)} — not mutated by this target")
    for path in deleted:
        say(f"not mutated {shown(path)} — deleted, no mutants")
    counts = {"scoped": 0, "skipped": 0, "refused": 0}
    failed: list[str] = []
    status = 0
    for backend, root in services:
        files = production.get(root, [])
        if not files:
            say(f"skip {root} — no changed production file")
            counts["skipped"] += 1
            continue
        say(f"scope {root} — {', '.join(shown(name) for name in files)}")
        result = runner.run(backend, root, files)
        for name, why in result.skipped:
            say(f"not mutated {shown(root + '/' + name)} — {why}")
        if result.refusal is not None:
            say(f"refuse {root} — {result.refusal}")
            counts["refused"] += 1
        else:
            counts["scoped" if result.files else "skipped"] += 1
        if result.status != 0:
            failed.append(root)
            status = status or result.status
    if named and not counts["scoped"] and not failed:
        say("no mutant to run — every changed production file is outside the tools' targets")
    ended = "passed" if not failed else "failed: " + ", ".join(failed)
    say(f"{counts['scoped']} scoped, 0 swept, {counts['skipped']} skipped, {counts['refused']} refused; {ended}")
    return status


def main(argv: list[str], runner: Runner | None = None) -> int:
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
    try:
        if not services:
            raise Sweep(NO_SERVICE)
        words, changes = change_set(os.environ)
    except Sweep as why:
        say(SWEEPS.format(reason=why))
        return full(make, makefile)
    except Refused as why:
        say(str(why))
        return 2
    return scope(services, words, changes, runner or Unwired())


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
