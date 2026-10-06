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
import re
import subprocess
import sys
import unicodedata
from pathlib import Path
from xml.etree import ElementTree
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
    unreadable: str | None = None


class Plan(NamedTuple):
    """What a wired service's tool would take of the changed files, decided before any tool starts: the files it will
    mutate, each it will not with the reason, and, where its configuration cannot be read, the words of that."""

    keep: list[str]
    left: list[tuple[str, str]]
    unreadable: str | None = None


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
BORDERS = ("ci", "head", "trunk", "slice_branch", "base", "told", "index")
NO_SCOPE = "this layout has no mutation scope — the recorded command runs"
NO_SERVICE = "no generated service to scope"
EMPTY_SINCE = "SINCE is set and empty"
NOT_FACTORY = "`mutation-full`'s recipe is not the one the factory wrote, so it runs as written"


def say(text: str) -> None:
    """The only place a `mutation:` line is spelled."""
    print(LINE + text, flush=True)


def unreadable(error: BaseException) -> str:
    return "the checkout could not be read (" + str(error).replace("\n", " ")[:120] + ")"


def load(filename: str) -> Any:
    """A script beside this one, loaded and never copied: the borders and the trunk are `verify-scoped.py`'s own, the
    Go exclusions are `go-mutation.py`'s."""
    spec = importlib.util.spec_from_file_location("mutation_scope_" + filename.replace("-", "_"),
                                                  os.path.join(HERE, filename))
    if spec is None or spec.loader is None:
        raise ImportError("cannot load " + filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def scoped_gate() -> Any:
    return load("verify-scoped.py")


def scoped_gate_changes() -> Any:
    """`verify-scoped.py`'s own `changes` module, whose `unpushed` is D153's rule: reached through it, never copied."""
    return scoped_gate().changes


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


def dry_flags() -> str:
    """The make flags that start nothing (`-n`, `-q`, `-t`) this run was made with, as verify-scoped's `idle` border reads
    them: the stamp's own `make_flags` and `IDLE_FLAGS`. Empty where the run is a real one."""
    stamp = load("verify-stamp.py")
    flags = str(stamp.make_flags())
    return flags if any(letter in flags for letter in stamp.IDLE_FLAGS) else ""


def full(make: str, makefile: str, clear_since: bool = False, dry: bool = False) -> int:
    """The sweep: `make mutation-full`, its status the run's. close_fds=False keeps a jobserver's descriptors. Under a
    set `SINCE` the sub-make gets `SINCE=` on its command line, which beats the environment and `MAKEFLAGS`, so Go's
    `$(if $(SINCE),--since $(SINCE))` cannot scope a run that is announced as the sweep."""
    if dry:
        say("`make mutation-full` would run here; it starts nothing under a dry run")
        return 0
    command = [make, "--no-print-directory", "-f", makefile, "mutation-full", *(["SINCE="] if clear_since else [])]
    return subprocess.run(command, close_fds=False, check=False).returncode


class Sweep(Exception):
    """The whole run is the sweep, for the reason this carries. `keeps_since` is true only where the recipe that runs is the
    project's own (D154): the sweep then hands `SINCE` on, and every other cause clears it."""

    def __init__(self, reason: str, keeps_since: bool = False) -> None:
        super().__init__(reason)
        self.keeps_since = keeps_since


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


def project_changes(scope: Any, base: str) -> dict[str, str]:
    """Every path that differs from `base` with its status, each relative to the project's root, which is where every
    other path this script compares starts. `changed_files` is not used: it gives tracked paths from the top of the
    repository and untracked ones from the project, and a project inside a subdirectory would match neither rule."""
    changes: dict[str, str] = {}
    fields = scope.git_must("diff", "--name-status", "-z", "--no-renames", "--relative", base).split("\0")
    for status, path in zip(fields[0::2], fields[1::2]):
        if path:
            changes[path] = status[:1]
    for path in scope.git_must("ls-files", "-z", "--others", "--exclude-standard").split("\0"):
        if path:
            changes[path] = "A"
    return changes


def change_set(env: Mapping[str, str]) -> tuple[str, dict[str, str], Any, str]:
    """What the run is compared with, in words, the paths that differ from it with their status, the module that read
    them and the commit they differ from. The borders are asked unless `SINCE` names a commit, which scopes on any
    checkout; a checkout that cannot be read is a sweep."""
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
            span = scoped_gate_changes().unpushed(scope, base.commit)  # D153: the trunk's commits nobody's push gated
            if span.failure is not None:
                raise Sweep(span.failure)
            found = project_changes(scope, base.commit)
            prefix = (scope.git("rev-parse", "--show-prefix") or "").strip()
            for path in sorted(span.paths):  # from the top of the repository; the changes here start at the project
                if path.startswith(prefix) and path[len(prefix):]:
                    found.setdefault(path[len(prefix):], "M")
            clause = f"; {span.note}" if span.paths else ""
            return f"`{shown(str(base.named))}` at {short}{clause}", found, scope, base.commit
        commit = resolved(where.scope, since)
        return f"`{shown(since)}`", project_changes(where.scope, commit), where.scope, commit
    except (Sweep, Refused):
        raise
    except Exception as error:
        raise Sweep(unreadable(error)) from error


def rule_of(text: str, target: str) -> list[str]:
    """One rule of a Makefile as written: its target line and the recipe lines under it."""
    found: list[str] = []
    following = False
    for line in text.splitlines():
        if re.match(re.escape(target) + r":(?!=)", line):
            following = True
            found.append(line)
        elif following and line.startswith("\t"):
            found.append(line)
        else:
            following = False
    return found


def mutation_rule(text: str) -> list[str]:
    """The `mutation` and `mutation-full` rules of a Makefile as written: the latter holds the tool's invocation."""
    return rule_of(text, "mutation") + rule_of(text, "mutation-full")


def factory_recipe(services: list[tuple[str, str]]) -> list[str]:
    """The recipe lines of `mutation-full` as the factory writes them for these services: each backend's own line with its
    path, in service order, each distinct line once as the factory merges them. The Go and Spring lines are the ones
    this script's own runs are held equal to; a placeholder's is its setup message."""
    lines: list[str] = []
    for backend, path in services:
        if backend == "go":
            line = f"python3 scripts/go-mutation.py {path} $(if $(SINCE),--since $(SINCE))"
        elif backend == "java-spring":
            line = f"cd {path} && " + " ".join(PIT)
        elif backend == "python":
            line = ("@command -v mutmut >/dev/null 2>&1 || { echo '" + PLACEHOLDERS[backend] +
                    "' >&2; exit 2; }; mutmut run")
        else:
            line = f"@echo '{PLACEHOLDERS[backend]}'; exit 2"
        if line not in lines:
            lines.append(line)
    return lines


def shape(element: Any) -> Any:
    """An element as comparable structure: tags, attributes, text and children, never comments or layout."""
    return (local(element.tag), tuple(sorted(element.attrib.items())), (element.text or "").strip(),
            tuple(shape(child) for child in element))


def pitest_block(text: str | None) -> Any:
    """The `pitest-maven` plugin of a pom as structure; None where there is no pom or no such plugin. Text that does not
    parse raises, because a side that cannot be read cannot be called equal."""
    if text is None:
        return None
    for plugin in (el for el in ElementTree.fromstring(text).iter() if local(el.tag) == "plugin"):
        if any(local(child.tag) == "artifactId" and (child.text or "").strip() == "pitest-maven" for child in plugin):
            return shape(plugin)
    return None


def read(path: str) -> str | None:
    try:
        with open(path, encoding="utf-8") as handle:
            return handle.read()
    except OSError:
        return None


def pom_changed(tool: Any, commit: str, path: str) -> bool:
    """Whether a pom's `pitest-maven` plugin differs from the base's as parsed structure; a side that cannot be parsed does.
    A pom the base does not have belongs to a service that is new, whose every file is in the scope already."""
    then = tool.git("show", f"{commit}:./{path}")
    if then is None:
        return False
    try:
        return bool(pitest_block(then) != pitest_block(read(path)))
    except Exception:
        return True


def sweep_causes(changes: dict[str, str], services: list[tuple[str, str]], tool: Any, commit: str,
                 makefile: str) -> tuple[list[str], dict[str, list[str]]]:
    """The changed files no scope can be trusted across, in the order of data-model's table: those that sweep the whole
    run (the `mutation` rule's text, this script), and per service those that sweep it (Go's script and yaml, a Spring
    pom whose `pitest-maven` block differs)."""
    here = os.path.relpath(os.path.abspath(__file__))
    backend_script = os.path.join(os.path.dirname(here), "go-mutation.py")
    rule = os.path.normpath(makefile)
    whole: list[str] = []
    per: dict[str, list[str]] = {}
    for path in sorted(changes):
        if path == rule and mutation_rule(tool.git("show", f"{commit}:./{path}") or "") != mutation_rule(read(path) or ""):
            whole.insert(0, path)
        elif path == here:
            whole.append(path)
        for backend, root in services:
            wired = (backend == "go" and path in (backend_script, f"{root}/.gremlins.yaml")) or (
                backend == "java-spring" and path == f"{root}/pom.xml" and pom_changed(tool, commit, path))
            if wired:
                per.setdefault(root, []).append(path)
    return whole, per


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


def go_plan(path: str, files: list[str]) -> Plan:
    """The files Gremlins will take within the given ones: the exclusions `.gremlins.yaml` carries are `go-mutation.py`'s
    to read. A configuration it refuses to read plans every file, and the run then fails with its words."""
    tool = load("go-mutation.py")
    try:
        keep = tool.mutable(set(files), tool.excluded(Path(path) / tool.CONFIG))
    except SystemExit:
        return Plan(list(files), [])
    return Plan(sorted(keep), [(name, "outside Gremlins' configured targets") for name in files if name not in keep])


def go(path: str, files: list[str]) -> Result:
    """Gremlins over the given files only; a file the exclusions take is named and left out, so a run with nothing left
    starts no tool."""
    tool = load("go-mutation.py")
    try:
        tool.excluded(Path(path) / tool.CONFIG)
    except SystemExit as stop:  # a configuration go-mutation.py refuses to read is a failed run, with its words
        print(stop.code, file=sys.stderr)
        return Result(2, [], [])
    plan = go_plan(path, files)
    if not plan.keep:
        return Result(0, [], plan.left)
    command = [sys.executable, os.path.join(HERE, "go-mutation.py"), path]
    command += [word for name in plan.keep for word in ("--file", name)]
    return Result(subprocess.run(command, close_fds=False, check=False).returncode, plan.keep, plan.left)


# The setup message of each placeholder backend: the line `make mutation-full` prints for it, held equal to the factory's by a test.
PLACEHOLDERS = {
    "typescript": "Configure the repository-selected Stryker mutator, then run its checked-in configuration.",
    "python": "install and configure mutmut for the selected production packages",
    "java-quarkus": "Configure PIT for the domain packages only — see the note above this target — then run it.",
}
WIRED = ("go", "java-spring")
# D149: the scoped run refuses a Python service whether or not mutmut is installed; only the sweep runs the tool today.
PYTHON_REFUSED = ("a Python service is refused until a later slipwai release wires mutmut, whether or not mutmut is "
                  "installed; `make mutation-full` runs mutmut today where it is installed")


class Unreadable(Exception):
    """A pattern or a file this script cannot read as the tool reads it: the service's run is then the sweep."""


# What PIT's `Glob` escapes or turns into a regex operator, character by character; `*` and `**.` are split off first.
GLOB = {"?": ".", ".": r"\.", "$": r"\$", "+": r"\+", "\\": r"\\", "(": r"\(", ")": r"\)", "[": r"\[", "]": r"\]"}


def pit_regex(pattern: str) -> re.Pattern[str]:
    """A `targetClasses`/`excludedClasses` pattern as PIT's `Glob` reads it (pitest 1.25.9): matched whole; `*` any run of
    characters including `.`, `?` one character, `$` and `.` literal, `**.` zero or more packages, a leading `~` a raw
    regular expression. A `${property}` is Maven's to expand and not this script's to guess."""
    if "${" in pattern:
        raise Unreadable(f"the pattern `{shown(pattern)}` names a property")
    try:
        if pattern.startswith("~"):
            return re.compile(pattern[1:])
        words = {"**.": r"(?:.*\.)*", "*": ".*"}
        return re.compile("".join(words.get(word) or "".join(GLOB.get(char, char) for char in word)
                                  for word in re.split(r"(\*\*\.|\*)", pattern)))
    except re.error as error:
        raise Unreadable(f"the pattern `{shown(pattern)}` cannot be read ({error})") from error


def pit_matches(pattern: str, name: str) -> bool:
    return pit_regex(pattern).fullmatch(name) is not None


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def pit_targets(pom: str) -> tuple[list[str], list[str]]:
    """The `targetClasses` and `excludedClasses` of the `pitest-maven` plugin in a pom, read and never written."""
    try:
        tree = ElementTree.parse(pom)
    except (OSError, ElementTree.ParseError) as error:
        raise Unreadable(f"the pom cannot be read ({str(error)[:80]})") from error
    for plugin in (el for el in tree.iter() if local(el.tag) == "plugin"):
        if any(local(child.tag) == "artifactId" and (child.text or "").strip() == "pitest-maven" for child in plugin):
            settings = next((child for child in plugin if local(child.tag) == "configuration"), None)
            lists = {local(child.tag): [(param.text or "").strip() for param in child]
                     for child in (settings if settings is not None else [])}
            if not lists.get("targetClasses"):
                raise Unreadable("the pitest-maven plugin names no targetClasses")
            return lists["targetClasses"], lists.get("excludedClasses", [])
    raise Unreadable("the pom has no pitest-maven plugin")


def class_name(path: str) -> str:
    """`src/main/java/com/x/Foo.java` as `com.x.Foo`."""
    return path.removeprefix("src/main/java/").removesuffix(".java").replace("/", ".")


def stream(argv: list[str], cwd: str) -> tuple[int, str]:
    """A command run in `cwd`, its output echoed as it comes and returned whole."""
    seen: list[str] = []
    with subprocess.Popen(argv, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                          errors="replace", close_fds=False) as process:
        for line in process.stdout or []:
            print(line, end="", flush=True)
            seen.append(line)
    return process.returncode, "".join(seen)


PIT = ["./mvnw", "-B", "-q", "test-compile", "org.pitest:pitest-maven:mutationCoverage"]
NO_MUTATIONS = "No mutations found"


def spring_plan(path: str, files: list[str]) -> Plan:
    """The classes PIT will take within the changed ones, by the pom's own `targetClasses`/`excludedClasses`."""
    pom = f"{path}/pom.xml"
    try:
        targets, excluded = pit_targets(pom)
        keep = [name for name in files if any(pit_matches(t, class_name(name)) for t in targets)
                and not any(pit_matches(x, class_name(name)) for x in excluded)]
    except Unreadable as why:
        return Plan([], [], f"{pom}: {why}")
    return Plan(keep, [(name, "outside PIT's configured targets") for name in files if name not in keep])


def spring(path: str, files: list[str], execute: Any) -> Result:
    """PIT over the changed classes only — `-DtargetClasses=Foo,Foo$*` on the sweep's own command, the pom untouched —
    within the pom's targets. A class outside them is named and left out, and a run with nothing left starts no Maven."""
    plan = spring_plan(path, files)
    if plan.unreadable is not None:
        return Result(0, [], [], None, plan.unreadable)
    if not plan.keep:
        return Result(0, [], plan.left)
    classes = [class_name(name) for name in plan.keep]
    status, text = execute([*PIT, "-DtargetClasses=" + ",".join(c for name in classes for c in (name, name + "$*"))], path)
    if status != 0 and NO_MUTATIONS in text:  # PIT's own failure for a scope with nothing to mutate, which is no failure
        say(f"no mutant to run in {path} — PIT found no code to mutate in {', '.join(classes)}; no report was written")
        status = 0
    return Result(status, plan.keep, plan.left)


def refusal(backend: str, path: str, files: list[str]) -> Result:
    """A backend with no tool wired up: the placeholder's own setup message, then what the scope would have mutated."""
    named = ", ".join(shown(f"{path}/{name}") for name in files)
    if backend not in PLACEHOLDERS:
        return Result(2, [], [], f"no runner for {backend}")
    said = PLACEHOLDERS[backend].rstrip(".")
    return Result(2, [], [], f"{said}; the scope will apply once a tool is wired; it would mutate: {named}"
                  + (" (" + PYTHON_REFUSED + ")" if backend == "python" else ""))


class Tools:
    """The runner of the wired backends. Any other backend refuses until its tool is wired, so the target can fail but
    never pass for it."""

    def __init__(self, execute: Any = None) -> None:
        self.execute = execute or stream

    def plan(self, backend: str, path: str, files: list[str]) -> Plan:
        """What the tool will take of `files`, before anything runs; a backend with no tool takes them all."""
        if backend == "go":
            return go_plan(path, files)
        if backend == "java-spring":
            return spring_plan(path, files)
        return Plan(list(files), [])

    def run(self, backend: str, path: str, files: list[str]) -> Result:
        if backend == "go":
            return go(path, files)
        if backend == "java-spring":
            return spring(path, files, self.execute)
        return refusal(backend, path, files)

    def sweep(self, backend: str, path: str) -> Result:
        """The service's whole run, as `make mutation-full` would: no scope."""
        if backend == "go":
            command = [sys.executable, os.path.join(HERE, "go-mutation.py"), path]
            return Result(subprocess.run(command, close_fds=False, check=False).returncode, [], [])
        if backend == "java-spring":
            return Result(self.execute(PIT, path)[0], [], [])
        return refusal(backend, path, [])


def said(paths: list[str]) -> str:
    return ", ".join(f"`{shown(path)}` changed" for path in paths)


def scope(services: list[tuple[str, str]], words: str, changes: dict[str, str], runner: Runner,
          causes: dict[str, list[str]], dry: bool = False) -> int:
    """The scoped run: what changed, classified, what each tool will take of it decided for every service, then the first
    line, each service once in service order, and the closing line. A service in `causes` is swept and its production
    files are not additionally scoped; so is one whose configuration cannot be read. Under `dry` no wired tool is asked: the
    plan is printed and each service reads as having run clean; a refusal, which starts none, is the runner's."""
    handled = {path for found in causes.values() for path in found}
    shared: list[str] = []
    deleted: list[str] = []
    tests: list[str] = []
    production: dict[str, list[str]] = {}
    for path in sorted(set(changes) - handled):
        kind, root, inside = classify(path, changes[path], services)
        if kind == "shared":
            shared.append(path)
        elif kind == "deleted":
            deleted.append(path)
        elif kind == "test":
            tests.append(path)
        elif kind == "production" and root not in causes:
            production.setdefault(root, []).append(inside)
    plans: dict[str, Plan] = {}
    for backend, root in services:  # a runner with no plan takes every file, and says what it left out when it runs
        if root in production:
            plans[root] = getattr(runner, "plan", lambda *_: Plan(production[root], []))(backend, root, production[root])
    unread = {root: plan.unreadable for root, plan in plans.items() if plan.unreadable is not None}
    named = sorted(f"{root}/{inside}" for root, plan in plans.items() if root not in unread for inside in plan.keep)
    outside = any(plan.left for plan in plans.values())
    if named:
        say(f"scoped to {len(named)} changed file(s) since {words}: {', '.join(shown(name) for name in named)}")
    elif causes or unread:
        say(SWEEPS.format(reason=", ".join([*([said(sorted(handled))] if handled else []), *map(str, unread.values())])))
    elif tests:
        say(f"no mutant to run — only tests changed: {', '.join(shown(name) for name in tests)}; "
            "`make mutation-full` is the run that measures them")
    elif outside:
        say("no mutant to run — every changed production file is outside the tools' targets")
    else:
        say("no mutant to run — no production file changed")
    for path in shared:
        say(f"not mutated {shown(path)} — not mutated by this target")
    for path in deleted:
        say(f"not mutated {shown(path)} — deleted, no mutants")
    counts = {"scoped": 0, "swept": 0, "skipped": 0, "refused": 0}
    failed: list[str] = []
    status = 0
    for backend, root in services:
        plan = plans.get(root)
        if root in causes:
            say(f"sweep {root} — {said(causes[root])}")
            result, kind = (Result(0, [], []) if dry and backend in WIRED else runner.sweep(backend, root)), "swept"
        elif root in unread:
            say(f"sweep {root} — {unread[root]}")
            result, kind = (Result(0, [], []) if dry and backend in WIRED else runner.sweep(backend, root)), "swept"
        elif plan is None:
            say(f"skip {root} — no changed production file")
            counts["skipped"] += 1
            continue
        elif not plan.keep and plan.left:
            say(f"skip {root} — no changed production file within the tool's targets")
            for name, why in plan.left:
                say(f"not mutated {shown(root + '/' + name)} — {why}")
            counts["skipped"] += 1
            continue
        else:
            if backend in WIRED:
                say(f"scope {root} — {', '.join(shown(name) for name in production[root])}")
            result = (Result(0, list(production[root]), []) if dry and backend in WIRED
                      else runner.run(backend, root, production[root]))
            kind = "scoped"
        for name, why in result.skipped:
            say(f"not mutated {shown(root + '/' + name)} — {why}")
        if result.refusal is not None:
            say(f"refuse {root} — {result.refusal}")
            kind = "refused"
        elif kind == "scoped" and not result.files:
            kind = "skipped"
        counts[kind] += 1
        if result.status != 0:
            failed.append(root)
            status = status or result.status
    ended = ("planned" if dry else "passed") if not failed else "failed: " + ", ".join(failed)
    if dry and failed:  # a dry run reports what would happen and does not fail, as `make -n` on a refusing recipe exits 0
        ended, status = "dry run — would fail: " + ", ".join(failed), 0
    say(f"{counts['scoped']} scoped, {counts['swept']} swept, {counts['skipped']} skipped, {counts['refused']} refused; {ended}")
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
    flags = dry_flags()
    dry = bool(flags)
    if dry:
        say(f"dry run (make was run with -{flags}) — the plan below starts no tool")
    if delivery_moved():
        say(NO_SCOPE)
        return full(make, makefile, dry=dry)
    try:
        if not services:
            raise Sweep(NO_SERVICE)
        words, changes, tool, commit = change_set(os.environ)
        whole, causes = sweep_causes(changes, services, tool, commit, makefile)
        if whole:
            raise Sweep(said(whole))
        if [line[1:] for line in rule_of(read(makefile) or "", "mutation-full")[1:]] != factory_recipe(services):
            handed = os.environ.get("SINCE")
            raise Sweep(NOT_FACTORY + (f", with `SINCE={shown(handed)}`" if handed else ""), keeps_since=True)
    except Sweep as why:
        say(SWEEPS.format(reason=why))
        return full(make, makefile, bool(os.environ.get("SINCE")) and not why.keeps_since, dry)
    except Refused as why:
        say(str(why))
        return 2
    return scope(services, words, changes, runner or Tools(), causes, dry)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
