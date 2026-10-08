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
import shutil
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
    mutate, each it will not with the reason, where its configuration cannot be read the words of that, and where a
    changed path would be misread by the tool the words of the refusal (which starts no tool)."""

    keep: list[str]
    left: list[tuple[str, str]]
    unreadable: str | None = None
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
BORDERS = ("ci", "head", "trunk", "slice_branch", "base", "told", "index")
NO_SCOPE = "this layout has no mutation scope — the recorded command runs"
NO_SERVICE = "no generated service to scope"
EMPTY_SINCE = "SINCE is set and empty"
INCLUDES = "`{makefile}` includes another makefile, which the factory cannot read, so it cannot vouch for what runs"
MAKEFILES_SET = "`MAKEFILES` is set, so makefiles the factory cannot read run beside `{makefile}`"
NOT_FACTORY = "`mutation-full`'s recipe is not the one the factory wrote, so it runs as written"


def browser_apps() -> list[str]:
    """The paths `project.json` records for a browser app (`kind: web`): nothing here mutates a file in one."""
    try:
        with open("project.json", encoding="utf-8") as handle:
            records = json.load(handle).get("deployables")
    except (OSError, ValueError, AttributeError):
        return []
    records = list(records.values()) if isinstance(records, dict) else records if isinstance(records, list) else []
    return sorted(record["path"].rstrip("/") for record in records
                  if isinstance(record, dict) and record.get("kind") == "web" and isinstance(record.get("path"), str))


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
    """The commit `SINCE` names, as git resolves it (`:/<message>`, a tag, a hash, a branch), or a refusal naming it: the ref
    is resolved first and `^{commit}` is applied to the hash it gave, since `:/<message>^{commit}` is a different message."""
    named = scope.git("rev-parse", "--verify", "--end-of-options", ref)
    found = scope.git("rev-parse", "--verify", "--end-of-options", named.strip() + "^{commit}") if named else None
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
                    # a file the unpushed commits removed is not in the base's tree, and is deleted whatever else happened
                    here = path[len(prefix):]
                    gone = scope.git("cat-file", "-e", f"{base.commit}:./{here}") is None
                    found.setdefault(here, "D" if gone else "M")
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


def prerequisites(rule: list[str]) -> list[str]:
    """The prerequisites on a rule's target line: the words after the colon, before a comment or a recipe after `;`."""
    if not rule:
        return []
    return rule[0].partition(":")[2].split("#")[0].split(";")[0].split()


def mutation_rule(text: str) -> list[str]:
    """The `mutation` and `mutation-full` rules of a Makefile as written: the latter holds the tool's invocation."""
    return rule_of(text, "mutation") + rule_of(text, "mutation-full")


def factory_recipe(services: list[tuple[str, str]]) -> list[str]:
    """The recipe lines of `mutation-full` as the factory writes them for these services: each backend's own line with its
    path, in service order, each distinct line once as the factory merges them, except that every Python service shares
    the one line, at the place of the first. The Go and Spring lines are the
    ones this script's own runs are held equal to; a placeholder's is its setup message."""
    lines: list[str] = []
    python = " ".join(path for backend, path in services if backend == "python")  # one line for all of them (D223)
    for backend, path in services:
        if backend == "go":
            line = f"python3 scripts/go-mutation.py {path} $(if $(SINCE),--since $(SINCE))"
        elif backend == "typescript":
            line = f"python3 scripts/stryker-mutation.py {path}"
        elif backend == "java-spring":
            line = f"cd {path} && " + " ".join(PIT)
        elif backend == "python":
            line = f"python3 scripts/mutmut-mutation.py {python}"
        else:
            line = f"@echo '{PLACEHOLDERS[backend]}'; exit 2"
        if line not in lines:
            lines.append(line)
    return lines


def shape(element: Any) -> Any:
    """An element as comparable structure: tags, attributes, text and children, never comments or layout."""
    return (local(element.tag), tuple(sorted(element.attrib.items())), (element.text or "").strip(),
            tuple(shape(child) for child in element))


def pitest_plugins(root: Any) -> list[Any]:
    """Every `pitest-maven` plugin element of a pom, wherever it sits: `plugins`, `pluginManagement`, a profile."""
    return [plugin for plugin in root.iter() if local(plugin.tag) == "plugin" and any(
        local(child.tag) == "artifactId" and (child.text or "").strip() == "pitest-maven" for child in plugin)]


def pom_properties(root: Any) -> dict[str, list[str]]:
    """The values of every `<properties>` entry of a pom, a name once per place it is set."""
    found: dict[str, list[str]] = {}
    for properties in (el for el in root.iter() if local(el.tag) == "properties"):
        for child in properties:
            found.setdefault(local(child.tag), []).append((child.text or "").strip())
    return found


def pitest_block(text: str | None) -> Any:
    """PIT's configuration in a pom as structure: every `pitest-maven` element and the properties they read through
    `${…}`, transitively; None where there is no pom or no such plugin. Text that does not parse raises, because a side
    that cannot be read cannot be called equal."""
    if text is None:
        return None
    root = ElementTree.fromstring(text)
    plugins = pitest_plugins(root)
    if not plugins:
        return None
    blocks = tuple(shape(plugin) for plugin in plugins)
    values, wanted, seen = pom_properties(root), re.findall(r"\$\{([^}]+)\}", repr(blocks)), set()
    while wanted:
        name = wanted.pop()
        if name not in seen:
            seen.add(name)
            wanted += re.findall(r"\$\{([^}]+)\}", " ".join(values.get(name, [])))
    return blocks, tuple(sorted((name, tuple(values.get(name, []))) for name in seen))


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


IGNORED = "`{path}` is a path git ignores, so whether it changed cannot be told"
NESTED = "`{path}` is a nested repository, so the files in it cannot be told apart"
# Directories of dependencies and build output, which no sweep of a service mutates and a scope never names.
DEPENDENCIES = ("vendor", "node_modules", "target", "build", "dist", ".venv", "venv", "__pycache__", ".gradle")
PRODUCTION_ROOT = {"go": "", "java-spring": "src/main/java/", "typescript": "src/", "python": "src/"}  # where a wired service's sources live
OTHER_JVM = (".kt", ".groovy", ".scala")


def other_jvm(path: str, root: str) -> bool:
    """A source under the service's `src/main/` in a JVM language other than Java: its classes cannot be read from it, so
    the service sweeps and it is never counted as no production file."""
    return path.startswith(f"{root}/src/main/") and path.endswith(OTHER_JVM)


INCLUDE = re.compile(r"^ *(?:-include|include|sinclude)(?=[ \t])", re.MULTILINE)
DEFAULT_MAKEFILES = ("GNUmakefile", "makefile", "Makefile")


def own_makefile(makefile: str) -> str:
    """The Makefile make runs: the one handed here, unless that is a file `MAKEFILES` names, which make lists first and
    which is not the project's own; then the first of the names make looks for."""
    named = [os.path.normpath(word) for word in os.environ.get("MAKEFILES", "").split()]
    if os.path.normpath(makefile) not in named:
        return makefile
    return next((name for name in DEFAULT_MAKEFILES if os.path.exists(name)), "Makefile")


def unlisted(changes: dict[str, str], services: list[tuple[str, str]], tool: Any) -> list[tuple[Unlisted, str]]:
    """The paths under a wired service's production sources that git does not list as changed, whatever they hold: files and
    directories it ignores, and a nested repository (listed once as `dir/`). Each is a sweep of that service, since a sweep
    mutates what a scope cannot name. Dependency and build-output directories are left out."""
    wired = [(backend, root) for backend, root in services if backend in PRODUCTION_ROOT]
    if not wired:
        return []
    listing = tool.git("ls-files", "-z", "--others", "--ignored", "--exclude-standard", "--directory", "--",
                       *sorted({root for _, root in wired}))
    if listing is None:
        raise Sweep(unreadable(RuntimeError("git cannot list the ignored files")))
    found: list[tuple[Unlisted, str]] = []
    for path in [*(name for name in listing.split("\0") if name), *(name for name in changes if name.endswith("/"))]:
        owners = [(backend, root) for backend, root in wired if path.startswith(root + "/")]
        if not owners:
            continue
        backend, root = max(owners, key=lambda owner: len(owner[1]))
        inside = path[len(root) + 1:]
        if any(part in DEPENDENCIES for part in inside.split("/")):
            continue
        if path.endswith("/"):
            reads = any(inside.startswith(prefix) or prefix.startswith(inside) for prefix in production_roots(backend, root))
        else:
            reads = kind_of(backend, root, inside) == "production"
        if reads:
            nested = path in changes
            found.append((Unlisted(path, (NESTED if nested else IGNORED).format(path=shown(path))), root))
    return found


def versions_moved(script: str, tool: Any, commit: str, path: str, field: str) -> bool:
    """Whether the versions a wrapper reads from a file (`field` names the argument of its `versions`: `manifest_text` and
    `lock_text` for Stryker's, `pyproject_text` and `lock_text` for mutmut's) differ from the base's (D215 b); a side that
    cannot be parsed does. A file the base does not have belongs to a service that is new, whose every file is in the
    scope already."""
    then = tool.git("show", f"{commit}:./{path}")
    if then is None:
        return False
    now = read(path)
    wrapper = load(script)
    try:
        return bool(now is None or wrapper.versions(**{field: then}) != wrapper.versions(**{field: now}))
    except wrapper.Unreadable:
        return True


def python_moved(root: str, path: str, script: str, tool: Any, commit: str) -> bool:
    """Whether a changed path sweeps a Python service: the wrapper, or the service's manifest or lock where what mutmut
    reads of it moved (its `[tool.mutmut]` table, its requirement, the lock's mutmut and libcst closure)."""
    field = {f"{root}/pyproject.toml": "pyproject_text", f"{root}/uv.lock": "lock_text"}.get(path)
    return path == script or (field is not None and versions_moved("mutmut-mutation.py", tool, commit, path, field))


def sweep_causes(changes: dict[str, str], services: list[tuple[str, str]], tool: Any, commit: str,
                 makefile: str) -> tuple[list[str], dict[str, list[str]]]:
    """The changed files no scope can be trusted across, in the order of data-model's table: those that sweep the whole
    run (the `mutation` rule's text, this script), and per service those that sweep it (Go's script and yaml, a Spring
    pom whose `pitest-maven` block differs)."""
    here = os.path.relpath(os.path.abspath(__file__))
    backend_script = os.path.join(os.path.dirname(here), "go-mutation.py")
    wrapper_script = os.path.join(os.path.dirname(here), "stryker-mutation.py")
    python_script = os.path.join(os.path.dirname(here), "mutmut-mutation.py")
    lock = "package-lock.json"
    lock_moved = lock in changes and any(backend == "typescript" for backend, _ in services) and versions_moved(
        "stryker-mutation.py", tool, commit, lock, "lock_text")
    rule = os.path.relpath(os.path.abspath(makefile))  # project-relative, whatever form `--makefile` takes (make's own)
    whole: list[str] = []
    per: dict[str, list[str]] = {}
    for path in sorted(changes):
        if path == rule and mutation_rule(tool.git("show", f"{commit}:./{path}") or "") != mutation_rule(read(path) or ""):
            whole.insert(0, path)
        elif path == here:
            whole.append(path)
        for backend, root in services:
            wired = (backend == "go" and path in (backend_script, f"{root}/.gremlins.yaml")) or (
                backend == "java-spring" and (path == f"{root}/pom.xml" and pom_changed(tool, commit, path)
                                              or other_jvm(path, root))) or (
                backend == "typescript" and (path in (wrapper_script, f"{root}/stryker.config.json")
                                             or (path == lock and lock_moved)
                                             or (path == f"{root}/package.json"
                                                 and versions_moved("stryker-mutation.py", tool, commit, path,
                                                                    "manifest_text")))) or (
                backend == "python" and python_moved(root, path, python_script, tool, commit))
            if wired:
                per.setdefault(root, []).append(path)
    for path, root in unlisted(changes, services, tool):
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


def sourced(backend: str | None, inside: str) -> bool:
    """Whether a path `typescript_kind` calls a test is a script under `src/` that Stryker's list may still take (B3)."""
    named = inside.rsplit("/", 1)[-1]
    return (backend == "typescript" and inside.startswith("src/") and not named.endswith(".d.ts")
            and named.endswith((".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".mts", ".cts")))


# Stryker 10's `findConfigFile` would take these; the wrapper runs `stryker.config.json` by name, so they are never read (D213).
UNREAD_CONFIGS = tuple(f"stryker.{stem}.{extension}" for stem, extension in (
    ("conf", "json"), ("conf", "js"), ("conf", "mjs"), ("conf", "cjs"), ("config", "js"), ("config", "mjs"), ("config", "cjs")))


def unread_configs(root: str) -> list[str]:
    """The Stryker config files beside a TypeScript service's own that nothing reads, in the order Stryker would try them."""
    return [name for name in UNREAD_CONFIGS if os.path.isfile(os.path.join(root, name))]


def python_roots(service: str) -> list[str]:
    """The directories (each with its trailing slash) a Python service's `[tool.mutmut]` `source_paths` name, read as the
    wrapper reads them; `[""]`, every directory, where the table cannot be read, so that the service sweeps."""
    try:
        wrapper = load("mutmut-mutation.py")
        return [wrapper.source_root(entry) + "/" for entry in wrapper.targets(Path(service))["source_paths"]]
    except Exception:  # the wrapper's Unreadable, a wrapper or tomllib that is not there: the table is not read
        return [""]


def python_kind(path: str, service: str = "") -> str:
    if path.startswith("tests/"):
        return "test"
    return "production" if path.endswith(".py") and any(
        path.startswith(root) for root in ["src/", *python_roots(service)]) else "other"


def production_roots(backend: str, service: str) -> list[str]:
    """Where a wired service's sources live, as prefixes within it: a Python service's are its own `source_paths`."""
    return ["src/", *python_roots(service)] if backend == "python" else [PRODUCTION_ROOT[backend]]


def kind_of(backend: str, service: str, inside: str) -> str:
    """Production, test or other for a path within a service."""
    return python_kind(inside, service) if backend == "python" else KINDS[backend](inside)


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
    kind = kind_of(backend, root, inside)
    return ("deleted" if status == "D" and kind == "production" else kind), root, inside


def go_plan(path: str, files: list[str]) -> Plan:
    """The files Gremlins will take within the given ones: the exclusions `.gremlins.yaml` carries are `go-mutation.py`'s
    to read. A configuration it refuses to read plans every file, and the run then fails with its words."""
    tool = load("go-mutation.py")
    try:
        keep = tool.mutable(set(files), tool.excluded(Path(path) / tool.CONFIG))
    except SystemExit:
        return Plan(list(files), [])
    except re.error as error:  # a pattern Go's regexp accepts and Python's `re` cannot compile: not read, so the sweep
        return Plan([], [], f"{path}/{tool.CONFIG}: the pattern `{shown(str(error.pattern))}` cannot be read "
                            f"({str(error.msg)[:80]})")
    return planned(files, keep, "Gremlins'")


def planned(files: list[str], keep: Any, tool: str) -> Plan:
    """The files a tool takes of the given ones, sorted, and each it leaves out with the reason: the step Go's and
    TypeScript's plans share, both of them intersections with the tool's own list."""
    return Plan(sorted(keep), [(name, f"outside {tool} configured targets") for name in files if name not in keep])


# The wired backends whose tool a wrapper script owns: the wrapper, the words naming its list, and the file that list is in.
WRAPPERS = {"typescript": ("stryker-mutation.py", "Stryker's", "stryker.config.json"),
            "python": ("mutmut-mutation.py", "mutmut's", "pyproject.toml")}


def wrapper_plan(backend: str, path: str, files: list[str]) -> Plan:
    """The files a wrapper's tool will take within the given ones, by the service's own list as the wrapper reads it: the
    wrapper is loaded and never copied. A list it cannot read plans nothing and says why, and the service then sweeps."""
    script, whose, config = WRAPPERS[backend]
    tool = load(script)
    for name in files:  # a misread pattern is the louder fact: it refuses the service, before the list is even asked
        words = tool.refused(path, shown(name))
        if words is not None:
            return Plan([], [], None, words)
    try:
        patterns = tool.targets(Path(path))
        keep = {name for name in files if tool.matched(patterns, name)}
    except tool.Unreadable as why:
        return Plan([], [], f"{path}/{config}: {why}")
    return planned(files, keep, whose)


def wrapper_run(backend: str, path: str, files: list[str]) -> Result:
    """The tool over the given files only, through its wrapper; a file outside the list is named and left out, so a run
    with nothing left starts no tool."""
    plan = wrapper_plan(backend, path, files)
    if plan.unreadable is not None:
        return Result(0, [], [], None, plan.unreadable)
    if not plan.keep:
        return Result(0, [], plan.left)
    command = [sys.executable, os.path.join(HERE, WRAPPERS[backend][0]), path]
    command += [word for name in plan.keep for word in ("--file", name)]
    return Result(subprocess.run(command, close_fds=False, check=False).returncode, plan.keep, plan.left)


def wrapper_sweep(backend: str, path: str) -> Result:
    command = [sys.executable, os.path.join(HERE, WRAPPERS[backend][0]), path]
    return Result(subprocess.run(command, close_fds=False, check=False).returncode, [], [])


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
    if plan.unreadable is not None:
        return Result(0, [], [], None, plan.unreadable)
    if not plan.keep:
        return Result(0, [], plan.left)
    command = [sys.executable, os.path.join(HERE, "go-mutation.py"), path]
    command += [word for name in plan.keep for word in ("--file", name)]
    return Result(subprocess.run(command, close_fds=False, check=False).returncode, plan.keep, plan.left)


# The setup message of each placeholder backend: the line `make mutation-full` prints for it, held equal to the factory's by a test.
PLACEHOLDERS = {
    "java-quarkus": "Configure PIT for the domain packages only — see the note above this target — then run it.",
}
WIRED = ("go", "java-spring", "typescript", "python")


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
    plugins = pitest_plugins(tree.getroot())
    if len(plugins) > 1:  # which one Maven reads depends on profiles and management, which this script does not resolve
        raise Unreadable("the pom has more than one pitest-maven plugin")
    for plugin in plugins:
        settings = next((child for child in plugin if local(child.tag) == "configuration"), None)
        lists = {local(child.tag): [(param.text or "").strip() for param in child]
                 for child in (settings if settings is not None else [])}
        if not lists.get("targetClasses"):
            raise Unreadable("the pitest-maven plugin names no targetClasses")
        return lists["targetClasses"], lists.get("excludedClasses", [])
    raise Unreadable("the pom has no pitest-maven plugin")


class Undeclared(Unreadable):
    """A Java file whose package and top-level types this script cannot read with certainty: its words name the file."""


TYPE = re.compile(r"(?<![\w$.])(?:class|interface|enum|record)\s+([^\W\d][\w$]*)")
PACKAGE = re.compile(r"(?<![\w$.])package\s+([^\W\d][\w$]*(?:\s*\.\s*[^\W\d][\w$]*)*)\s*;")
ARGUMENTS = re.compile(r"\([^()]*\)")


def declared(path: str, source: str) -> list[str]:
    """The fully qualified name of every top-level type a Java source declares, from its own `package` line, never from its
    path. Comments, strings, character and text-block literals are blanked first and only braces at depth zero are read; a
    source that does not balance, or declares no type, is not read with certainty and raises `Undeclared` naming `path`."""
    blanked: list[str] = []
    depth = 0
    index = 0
    while index < len(source):
        two, char = source[index:index + 2], source[index]
        if two == "//":
            end = source.find("\n", index)
            index = len(source) if end < 0 else end
        elif two == "/*":
            end = source.find("*/", index + 2)
            if end < 0:
                raise Undeclared(f"{path}: a comment is never closed")
            index = end + 2
            blanked.append(" ")
        elif source.startswith('"""', index) or char in "\"'":
            quote = '"""' if source.startswith('"""', index) else char
            index += len(quote)
            while source[index:index + len(quote)] != quote:
                if index >= len(source) or (len(quote) == 1 and source[index] == "\n"):
                    raise Undeclared(f"{path}: a literal is never closed")
                index += 2 if source[index] == "\\" else 1
            index += len(quote)
            blanked.append(" ")
        else:
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth < 0:
                    raise Undeclared(f"{path}: braces do not balance")
            blanked.append(char if depth == 0 or char in "{}" else " ")
            index += 1
    if depth != 0:
        raise Undeclared(f"{path}: braces do not balance")
    text = "".join(blanked)
    while ARGUMENTS.search(text):  # an annotation's arguments hold `Foo.class` and the like, never a declaration
        text = ARGUMENTS.sub(" ", text)
    package = PACKAGE.search(text)
    prefix = "".join(package.group(1).split()) + "." if package else ""
    names = [prefix + found.group(1) for found in TYPE.finditer(text)]
    if not names:
        raise Undeclared(f"{path}: no type declaration could be read")
    return names


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


def taken(name: str, targets: list[str], excluded: list[str]) -> bool:
    """Whether PIT will mutate the top-level class `name` or a class nested in it, by its own rule: a name is matched whole,
    so an exclusion of `Foo` leaves `Foo$Bar` in. `$0` stands for a nested name, which `Foo$*` and `Foo*` and `x.*` read the same."""
    return any(any(pit_matches(t, each) for t in targets) and not any(pit_matches(x, each) for x in excluded)
               for each in (name, name + "$0"))


def spring_classes(path: str, files: list[str]) -> dict[str, list[str]]:
    """Each changed file with the top-level classes PIT will take in it, decided class by class within the pom's
    `targetClasses` and `excludedClasses`; a file none of whose classes qualify maps to an empty list."""
    targets, excluded = pit_targets(f"{path}/pom.xml")
    found: dict[str, list[str]] = {}
    for name in files:
        where = f"{path}/{name}"
        try:
            with open(where, encoding="utf-8") as handle:
                names = declared(where, handle.read())
        except (OSError, UnicodeDecodeError) as error:
            raise Undeclared(f"{where}: the file cannot be read ({str(error)[:60]})") from error
        found[name] = [each for each in names if taken(each, targets, excluded)]
    return found


def spring_plan(path: str, files: list[str]) -> Plan:
    """The classes PIT will take within the changed files, by the declared classes of each against the pom's own
    `targetClasses`/`excludedClasses`."""
    pom = f"{path}/pom.xml"
    try:
        found = spring_classes(path, files)
    except Undeclared as why:
        return Plan([], [], str(why))
    except Unreadable as why:
        return Plan([], [], f"{pom}: {why}")
    keep = [name for name in files if found[name]]
    return Plan(keep, [(name, "outside PIT's configured targets") for name in files if name not in keep])


def spring(path: str, files: list[str], execute: Any) -> Result:
    """PIT over the changed classes only — `-DtargetClasses=Foo,Foo$*` on the sweep's own command, the pom untouched —
    within the pom's targets. A file with no class inside them is named and left out, and a run with nothing left starts no
    Maven."""
    plan = spring_plan(path, files)
    if plan.unreadable is not None:
        return Result(0, [], [], None, plan.unreadable)
    if not plan.keep:
        return Result(0, [], plan.left)
    found = spring_classes(path, plan.keep)
    classes = [each for name in plan.keep for each in found[name]]
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
    return Result(2, [], [], f"{said}; the scope will apply once a tool is wired; it would mutate: {named}")


def gone(path: str) -> str | None:
    """The words of the refusal for a service whose directory is not there (a Makefile that still names a deleted service)."""
    if os.path.isdir(path):
        return None
    return (f"the service directory `{shown(path)}` does not exist; the Makefile still names it, so regenerate it or "
            "restore the service")


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
        if backend in WRAPPERS:
            return wrapper_plan(backend, path, files)
        return Plan(list(files), [])

    def gone(self, backend: str, path: str) -> str | None:
        """The refusal's words where this runner would start a tool for a service whose directory is not there."""
        return gone(path) if backend in WIRED else None

    def run(self, backend: str, path: str, files: list[str]) -> Result:
        if (why := self.gone(backend, path)) is not None:
            return Result(2, [], [], why)
        if backend == "go":
            return go(path, files)
        if backend == "java-spring":
            return spring(path, files, self.execute)
        if backend in WRAPPERS:
            return wrapper_run(backend, path, files)
        return refusal(backend, path, files)

    def sweep(self, backend: str, path: str) -> Result:
        """The service's whole run, as `make mutation-full` would: no scope."""
        if (why := self.gone(backend, path)) is not None:
            return Result(2, [], [], why)
        if backend == "go":
            command = [sys.executable, os.path.join(HERE, "go-mutation.py"), path]
            return Result(subprocess.run(command, close_fds=False, check=False).returncode, [], [])
        if backend == "java-spring":
            return Result(self.execute(PIT, path)[0], [], [])
        if backend in WRAPPERS:
            return wrapper_sweep(backend, path)
        return refusal(backend, path, [])


REPORTS = {"go": "gremlins.json", "typescript": os.path.join("reports", "mutation"), "python": "mutants"}  # where a run leaves its report


def drop_report(backend: str, root: str, dry: bool) -> None:
    """A service this run starts no tool for keeps no earlier run's report, which would read as this run's. The report
    is a tool's output, replaced by the next run that starts one; nothing is removed under a dry run."""
    report = os.path.join(root, REPORTS.get(backend, ""))
    if backend not in REPORTS or dry or not os.path.exists(report):
        return
    try:
        shutil.rmtree(report) if os.path.isdir(report) else os.remove(report)
    except OSError as error:
        say(f"{shown(report)} is an earlier run's report and could not be removed ({str(error)[:60]})")


class Unlisted(str):
    """A path git cannot say changed — one it ignores, or one in a nested repository — with the words that say so."""

    words: str

    def __new__(cls, path: str, words: str) -> "Unlisted":
        found = super().__new__(cls, path)
        found.words = words
        return found


def said(paths: list[str]) -> str:
    return ", ".join(path.words if isinstance(path, Unlisted) else f"`{shown(path)}` changed" for path in paths)


def scope(services: list[tuple[str, str]], words: str, changes: dict[str, str], runner: Runner,
          causes: dict[str, list[str]], dry: bool = False) -> int:
    """The scoped run: what changed, classified, what each tool will take of it decided for every service, then the first
    line, each service once in service order, and the closing line. A service in `causes` is swept and its production
    files are not additionally scoped; so is one whose configuration cannot be read. Under `dry` no wired tool is asked: the
    plan is printed and each service reads as having run clean; a refusal, which starts none, is the runner's."""
    handled = {path for found in causes.values() for path in found}
    shared: list[str] = []
    browser: list[str] = []
    deleted: list[str] = []
    tests: list[str] = []
    production: dict[str, list[str]] = {}
    named_tests: dict[str, list[tuple[str, str]]] = {}
    apps = browser_apps()
    for path in sorted(set(changes) - handled):
        if any(path.startswith(app + "/") for app in apps):
            browser.append(path)
            continue
        kind, root, inside = classify(path, changes[path], services)
        if kind == "shared":
            shared.append(path)
        elif kind == "deleted":
            deleted.append(path)
        elif kind == "test":
            owner = next((backend for backend, found in services if found == root), None)
            if sourced(owner, inside):  # B3: production if the service's own list takes it, asked below
                named_tests.setdefault(root, []).append((path, inside))
            else:
                tests.append(path)
        elif kind == "production" and root not in causes:
            production.setdefault(root, []).append(inside)
    for root, candidates in named_tests.items():
        ask = getattr(runner, "plan", None)
        asked = ask("typescript", root, [inside for _, inside in candidates]) if ask else None
        if asked is not None and root not in causes and (asked.keep or asked.refusal or asked.unreadable):
            production.setdefault(root, []).extend(inside for _, inside in candidates)
        else:
            tests.extend(path for path, _ in candidates)
    plans: dict[str, Plan] = {}
    for backend, root in services:  # a runner with no plan takes every file, and says what it left out when it runs
        if root in production:
            plans[root] = getattr(runner, "plan", lambda *_: Plan(production[root], []))(backend, root, production[root])
    unread = {root: plan.unreadable for root, plan in plans.items() if plan.unreadable is not None}
    named = sorted(f"{root}/{inside}" for root, plan in plans.items() if root not in unread
                   for inside in (production[root] if plan.refusal else plan.keep))
    missing_of = getattr(runner, "gone", lambda *_: None)  # a runner with no `gone` has no tool to start
    absent = [root for backend, root in services
              if (root in causes or root in unread) and missing_of(backend, root) is not None]  # B5: refused below, not swept
    swept_paths = sorted(path for root, found in causes.items() if root not in absent for path in found)
    reasons = [unread[root] for root in unread if root not in absent]
    named = sorted(f"{root}/{inside}" for root, plan in plans.items() if root not in unread
                   for inside in (production[root] if plan.refusal else plan.keep))
    outside = any(plan.left for plan in plans.values())
    if named:
        say(f"scoped to {len(named)} changed file(s) since {words}: {', '.join(shown(name) for name in named)}")
    elif swept_paths or reasons:
        say(SWEEPS.format(reason=", ".join([*([said(swept_paths)] if swept_paths else []), *map(str, reasons)])))
    elif absent:  # the sweep the cause asks for cannot start: the first line names the refusal the service gets below
        say(f"refusing {', '.join(absent)} — its directory does not exist, so nothing is swept")
    elif outside:  # a production file a tool leaves out changed, whatever else did: it is named `not mutated` below
        say("no mutant to run — every changed production file is outside the tools' targets")
    elif tests and not shared and not browser and not deleted:  # tests the only source files that changed (T022)
        say(f"no mutant to run — only tests changed: {', '.join(shown(name) for name in tests)}; "
            "`make mutation-full` is the run that measures them")
    elif browser:  # a browser app's file is production code, only not a service's: the lines below name it (T034)
        say("no mutant to run — no service production file changed")
    else:
        say("no mutant to run — no production file changed")
    for path in shared:
        say(f"not mutated {shown(path)} — not mutated by this target")
    for path in browser:
        say(f"not mutated {shown(path)} — browser app, not mutated by this target")
    for path in deleted:
        say(f"not mutated {shown(path)} — deleted, no mutants")
    counts = {"scoped": 0, "swept": 0, "skipped": 0, "refused": 0}
    failed: list[str] = []
    status = 0
    for backend, root in services:
        plan = plans.get(root)
        if backend == "typescript" and (unrun := unread_configs(root)):
            say(f"note {root} — {', '.join(unrun)} not read — `make mutation` runs `stryker.config.json`")
        runs = root in causes or root in unread or (plan is not None and bool(plan.keep))
        missing = missing_of(backend, root)
        if runs and missing is not None:  # no tool starts for a service that is not there
            why = missing
            say(f"refuse {root} — {why}")
            counts["refused"] += 1
            failed.append(root)
            status = status or 2
            continue
        if root in causes:
            say(f"sweep {root} — {said(causes[root])}")
            result, kind = (Result(0, [], []) if dry and backend in WIRED else runner.sweep(backend, root)), "swept"
        elif root in unread:
            say(f"sweep {root} — {unread[root]}")
            result, kind = (Result(0, [], []) if dry and backend in WIRED else runner.sweep(backend, root)), "swept"
        elif plan is None:
            say(f"skip {root} — no changed production file")
            drop_report(backend, root, dry)
            counts["skipped"] += 1
            continue
        elif plan.refusal is not None:  # a refusal starts no tool, and the shared tail below counts and fails it
            result, kind = Result(2, [], [], plan.refusal), "scoped"
        elif not plan.keep and plan.left:
            say(f"skip {root} — no changed production file within the tool's targets")
            for name, why in plan.left:
                say(f"not mutated {shown(root + '/' + name)} — {why}")
            drop_report(backend, root, dry)
            counts["skipped"] += 1
            continue
        else:
            if backend in WIRED:
                say(f"scope {root} — {', '.join(shown(name) for name in plan.keep)}")
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
    make, makefile = options["--make"], own_makefile(options["--makefile"])
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
        if os.environ.get("MAKEFILES"):  # makefiles make reads beside the project's own, whose rules this script cannot see
            raise Sweep(MAKEFILES_SET.format(makefile=shown(os.path.relpath(makefile))))
        if INCLUDE.search(read(makefile) or ""):
            raise Sweep(INCLUDES.format(makefile=shown(os.path.relpath(makefile))))
        written = rule_of(read(makefile) or "", "mutation-full")
        if [line[1:] for line in written[1:]] != factory_recipe(services) or prerequisites(written):
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
