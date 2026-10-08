#!/usr/bin/env python3
"""Enforce the repository's inward dependency rule — and the seam between bounded contexts inside one
service — without assuming one language."""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path


def project_root(script: Path, depth: int) -> Path:
    """The repository root: the nearest directory above this script holding `project.json`.

    This script's own tree is `<root>/scripts` in a generated project and `<root>/<layout.delivery>/scripts`
    where the method was installed beside an existing codebase (`project.json`'s `layout.delivery`), so how
    far below the root it sits is not something to count; `depth` is only the fallback for a tree with no
    manifest at all.
    """
    for candidate in script.parents:
        if (candidate / "project.json").is_file():
            return candidate
    return script.parents[depth]


ROOT = project_root(Path(__file__).resolve(), 1)
MANIFEST = ROOT / "project.json"
SOURCE_SUFFIXES = {".go", ".java", ".py", ".ts", ".tsx"}
IMPORT_LINE = re.compile(r"^\s*(?:from\s+|import\s+|require\s*\(|use\s+)", re.MULTILINE)
OUTER_LAYER = re.compile(r"(?:^|[/._-])(adapter|adapters|infrastructure|delivery)(?:[/._-]|$)", re.IGNORECASE)
# The application layer owns its ports; adapters implement them and are injected, and composition is the
# only place the two meet. So it may not name either, on top of what the domain may not name.
OUTER_LAYER_FROM_APPLICATION = re.compile(
    r"(?:^|[/._-])(adapter|adapters|composition|infrastructure|delivery)(?:[/._-]|$)", re.IGNORECASE
)


PRUNED = {".venv", "node_modules", "__pycache__", ".git", ".stryker-tmp"}
listings: dict[Path, list[Path]] = {}
members: dict[Path, frozenset[Path]] = {}
entries_read = 0
_recorded: tuple[set[str], set[str]] | None = None


def relative(path: Path) -> str | None:
    """`path` below the root, as POSIX, or None where it is not below it."""
    try:
        return Path(os.path.normpath(path)).relative_to(os.path.normpath(ROOT)).as_posix()
    except ValueError:
        return None


def recorded() -> tuple[set[str], set[str]]:
    """What `project.json` says about where deployables are: every recorded `path`, and the paths recorded as Java
    (`language` the string `java`), each as `x` whether recorded as `x`, `x/` or `./x`. A record that is not there,
    is unreadable, is not an object, or whose `path` or `language` is not a string says nothing."""
    global _recorded
    if _recorded is None:
        paths: set[str] = set()
        java: set[str] = set()
        try:
            records = manifest().get("deployables", {}) if isinstance(manifest(), dict) else {}
        except (OSError, ValueError):
            records = {}
        for record in records.values() if isinstance(records, dict) else []:
            if isinstance(record, dict) and isinstance(record.get("path"), str):
                path = os.path.normpath(record["path"])
                if path != ".":
                    paths.add(Path(path).as_posix())
                if record.get("language") == "java":
                    java.add(Path(path).as_posix())
        _recorded = (paths, java)
    return _recorded


def skipped(directory: Path, name: str) -> bool:
    """Is the directory `name` inside `directory` one nobody reads: an installed package, a cache, git's own, or
    Maven's `target` at the root of a Java deployable `project.json` records, beside that deployable's `pom.xml`.
    The record decides, never a file the tree holds: elsewhere `target` is a source directory. A directory that is a
    recorded deployable's path, or on the way to one, is read whatever it is called."""
    parent = relative(directory)
    if parent is None:
        return name in PRUNED
    here = name if parent == "." else f"{parent}/{name}"
    paths, java = recorded()
    if any(path == here or path.startswith(f"{here}/") for path in paths):
        return False
    return name in PRUNED or (name == "target" and parent in java and (directory / "pom.xml").is_file())


def listing(top: Path) -> list[Path]:
    """Every path under `top`, files and directories, in `Path` order — listed once, links not followed.

    The count of names every listing returned is what the pass line reports: a measurement, not a limit.
    """
    global entries_read
    if top not in listings:
        found: list[Path] = []
        for current, directories, files in os.walk(top):
            entries_read += len(directories) + len(files)
            directory = Path(current)
            directories[:] = [name for name in directories if not skipped(directory, name)]
            found.extend(directory / name for name in directories + files)
        listings[top] = sorted(found)
        members[top] = frozenset(found)
    return listings[top]


def under(directory: Path) -> list[Path]:
    """Every path under `directory`: filtered from a listing already taken only where that listing holds the
    directory as one of its own entries, spelled as it is spelled here, and not a link — then its files are
    exactly those the directory's own listing would give. Anything else (a `..` or a link in the spelling, a
    directory that is itself a link, one the listing pruned) is listed on its own, pruned and counted."""
    for top, paths in listings.items():
        if top in directory.parents and directory in members[top] and not directory.is_symlink():
            return [path for path in paths if directory in path.parents]
    return listing(directory)


_manifest: dict | Exception | None = None


def manifest() -> dict:
    """`project.json` read once per run — an empty record where there is none. A record that cannot be read
    raises, as it always has, and keeps raising the same error without being opened again."""
    global _manifest
    if _manifest is None:
        try:
            _manifest = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.is_file() else {}
        except (OSError, ValueError) as error:
            _manifest = error
    if isinstance(_manifest, Exception):
        raise _manifest
    return _manifest


def deployables(kind: str) -> list[dict]:
    """Every application record of one kind, from `project.json` — the one list this repository keeps.

    The hexagonal rules below need no list: they apply inside every directory under `apps/` and `packages/`
    whatever it is called — bar the six nobody reads: `.venv`, `node_modules`, `__pycache__`, `.git`, a mutation run's `.stryker-tmp` and the `target`
    at the root of a Java deployable `project.json` records, beside its `pom.xml`, which are never descended — and
    never a directory that is a recorded deployable's path or on the way to one. The frontend rule has to know which directories are *services* and which are
    *browser apps*, because it forbids each of the latter to import from any of the former; the context rule
    has to know which bounded contexts each service says it holds.
    """
    records = manifest().get("deployables", {})
    return [
        record
        for record in records.values()
        if isinstance(record, dict) and record.get("kind") == kind and isinstance(record.get("path"), str)
    ]


def app_paths(kind: str) -> list[str]:
    return [record["path"] for record in deployables(kind) if record.get("generated") is not False]


def unruled() -> list[str]:
    """The applications that existed before the method did (`"generated": false`) and do not declare the
    hexagonal layout — code the rules below were not written for, and pass over — whatever they are recorded
    as: a service, a library, a tool, a test suite, or an application whose role nobody has established."""
    records = manifest().get("deployables", {}).values()
    return [
        record["path"] for record in records
        if isinstance(record, dict) and isinstance(record.get("path"), str)
        and record.get("generated") is False and record.get("layout") != "hexagonal" and record["path"] != "."
    ]


def ruled(path: Path) -> bool:
    relative = path.relative_to(ROOT).as_posix()
    return not any(relative == skipped or relative.startswith(f"{skipped}/") for skipped in unruled())


def context_holders() -> dict[str, list[str]]:
    """Each service holding more than one bounded context, by path — the only ones the context rule is about.

    A service with one context (named or not) has no seam inside it. A service that lists several is the
    modular monolith this repository starts as: one deployable, several models, each under `src/<context>/`,
    and the list in the manifest is what says the boundary is meant rather than a directory that happens to
    share a name.
    """
    return {
        record["path"]: record["contexts"]
        for record in deployables("service")
        if (record.get("generated") is not False or record.get("layout") == "hexagonal")
        and isinstance(record.get("contexts"), list) and len(record["contexts"]) > 1
        and all(isinstance(name, str) for name in record["contexts"])
    }


def reaches_into(line: str, other: str, published: str) -> bool:
    """Does this import line name another context's insides — anything of it but its `published` module?

    Language-neutral in the way `OUTER_LAYER` is: the context is a path or package segment, so it is looked
    for between separators (`../billing/domain`, `app.billing.domain`, `com.acme.billing.domain`), never
    inside a word. Names that are not segments — `import { billing } from …` — are somebody's identifier.
    """
    for match in re.finditer(rf"(?:^|[\s/.'\"]){re.escape(other)}(?=[/.'\"]|\s+import\s|$)", line):
        rest = line[match.end():]
        if re.match(rf"(?:[/.]|\s+import\s+){re.escape(published)}(?:[/.\s;,'\"]|$)", rest):
            continue
        return True
    return False


def backend_implementation() -> re.Pattern[str]:
    """A frontend import that reaches into a service — by path from the root, or relatively from `apps/web`."""
    alternatives = []
    for path in app_paths("service"):
        alternatives.append(re.escape(path))
        alternatives.append(rf"(?:\.\./)+{re.escape(Path(path).name)}")
    return re.compile(rf"(?:{'|'.join(alternatives)})(?:/|['\"])" if alternatives else r"(?!)")

# Which third-party packages domain code may name, per language. Import *direction* is language-neutral,
# but "which bare specifier is a framework" is not: it depends on the ecosystem's own vocabulary. New
# languages add a row here and put the rest of their lint material under `assets/languages/<language>/`
# rather than threading ecosystem detail through the generic rules above.
# `allowed` may be None, which means "judge by the banned prefixes alone". Both shapes are needed, and
# which one fits is a property of the ecosystem rather than a preference. TypeScript's imports are a small
# set of bare specifiers, so an allowlist is short and exact. Java's are the whole JDK: `java.util`,
# `java.time` and `java.math` are the language, not a framework, so listing what a Decider may name would
# mean listing the standard library and would still be wrong the next time it grows. There, the honest rule
# is the list of prefixes that mean infrastructure.
DOMAIN_PACKAGE_POLICY: dict[str, dict[str, object]] = {
    # A schema library is not a framework, and domain event shapes are validated schema-first.
    ".ts": {"allowed": frozenset({"zod"}), "banned_prefixes": ("node:",), "banned": "a Node built-in"},
    ".tsx": {"allowed": frozenset({"zod"}), "banned_prefixes": ("node:",), "banned": "a Node built-in"},
    # Every prefix here is a framework, a container, a transport or a driver — the things a Decider must
    # stay free of so it can be tested without any of them. `jakarta.` and `javax.` cover CDI, JAX-RS,
    # Bean Validation, JPA and `javax.sql`, which is where a domain object starts needing a DataSource.
    # `java.sql.` is banned for the same reason while the rest of `java.*` is not: it is a driver API that
    # happens to ship with the JDK.
    ".java": {
        "allowed": None,
        "banned_prefixes": (
            "io.quarkus.",
            "io.smallrye.",
            "jakarta.",
            "javax.",
            "java.sql.",
            "org.eclipse.microprofile.",
            "org.flywaydb.",
            "org.hibernate.",
            "com.fasterxml.jackson.",
            "org.springframework.",
        ),
        # What the banned list actually is here, said accurately: `jakarta.inject` is a framework rather
        # than a built-in, and a message that called it one would send the reader looking in the JDK.
        "banned": "a framework or driver package",
    },
}
# `import x from 'y'`, `export … from 'y'`, bare `import 'y'`, `import('y')`, and `require('y')`. Matched
# against the whole file rather than line by line, because a multi-line import list is still one import.
SPECIFIER_PATTERNS = (
    re.compile(r"(?:^|\n)\s*(?:import|export)[\s\S]*?from\s*['\"]([^'\"]+)['\"]"),
    re.compile(r"(?:^|\n)\s*import\s*['\"]([^'\"]+)['\"]"),
    re.compile(r"\bimport\s*\(\s*['\"]([^'\"]+)['\"]\s*\)"),
    re.compile(r"\brequire\s*\(\s*['\"]([^'\"]+)['\"]\s*\)"),
)


# Test code is not the layer it tests. A Decider's spec lives in `tests/domain/` — the level
# `adversarial-testing` and `event-modeling-to-code.md` send it to — or beside the Decider, as Go's
# `_test.go` must, and either way it names the test runner and the fakes the layer itself may not.
TEST_DIRECTORIES = {"test", "tests", "__tests__"}
TEST_FILE = re.compile(r"(?:_test\.(?:go|py)|\.(?:test|spec)\.tsx?|Tests?\.java)$|^test_\w*\.py$")


def is_test(path: Path) -> bool:
    return bool(TEST_DIRECTORIES.intersection(path.parts)) or bool(TEST_FILE.search(path.name))


def source_files(layer: str) -> list[Path]:
    """Every source file under a `layer/` directory at any depth, in any deployable or package.

    One service holds `src/domain/`; the same service holds `src/<context>/domain/` once it has more than
    one bounded context. Both are the same layer. A test of the layer is not in it (`is_test`).
    """
    found: list[Path] = []
    for source_root in (ROOT / "apps", ROOT / "packages"):
        if not source_root.exists():
            continue
        for path in listing(source_root):
            relative = path.relative_to(source_root)
            if (
                path.is_file() and path.suffix in SOURCE_SUFFIXES and layer in relative.parts
                and not is_test(relative) and ruled(path)
            ):
                found.append(path)
    return found


# `import a.b.C;` and `import static a.b.C.member;`, with a trailing `.*` dropped so a wildcard import
# reports the package it names. Java has no quoted specifier, so the patterns above find nothing in it.
JAVA_IMPORT = re.compile(r"(?m)^\s*import\s+(?:static\s+)?([\w.]+?)(?:\.\*)?\s*;")


def specifiers_with_lines(text: str, suffix: str) -> list[tuple[int, str]]:
    patterns = (JAVA_IMPORT,) if suffix == ".java" else SPECIFIER_PATTERNS
    found: list[tuple[int, str]] = []
    for pattern in patterns:
        for match in pattern.finditer(text):
            found.append((text.count("\n", 0, match.start(1)) + 1, match.group(1)))
    return sorted(set(found))


def package_name(specifier: str) -> str:
    parts = specifier.split("/")
    return "/".join(parts[:2]) if specifier.startswith("@") else parts[0]


def main() -> int:
    violations: list[str] = []

    # 1. Domain code may not name an outer layer, in any language.
    for path in source_files("domain"):
        for number, line in enumerate(path.read_text(errors="replace", encoding="utf-8").splitlines(), start=1):
            if IMPORT_LINE.match(line) and OUTER_LAYER.search(line):
                violations.append(f"{path.relative_to(ROOT)}:{number}: domain imports an outer layer: {line.strip()}")

    # 2. Domain code may not reach for a framework or a runtime built-in either — being provider-free is
    #    what lets a Decider be tested without a provider.
    for path in source_files("domain"):
        policy = DOMAIN_PACKAGE_POLICY.get(path.suffix)
        if policy is None:
            continue
        allowed: frozenset[str] | None = policy["allowed"]  # type: ignore[assignment]
        banned_prefixes: tuple[str, ...] = policy["banned_prefixes"]  # type: ignore[assignment]
        banned_label = policy["banned"]
        for number, specifier in specifiers_with_lines(path.read_text(errors="replace", encoding="utf-8"), path.suffix):
            if specifier.startswith(".") or specifier.startswith("/"):
                continue
            relative = f"{path.relative_to(ROOT)}:{number}"
            if specifier.startswith(banned_prefixes):
                violations.append(
                    f"{relative}: domain imports {banned_label}: {specifier} — the domain is provider-free"
                )
            elif allowed is not None and package_name(specifier) not in allowed:
                allowed_list = ", ".join(sorted(allowed))
                violations.append(
                    f"{relative}: domain imports '{specifier}' — only {allowed_list} may be imported here"
                )

    # 3. Application code may not name an adapter or the composition root, in any language.
    for path in source_files("application"):
        for number, line in enumerate(path.read_text(errors="replace", encoding="utf-8").splitlines(), start=1):
            if IMPORT_LINE.match(line) and OUTER_LAYER_FROM_APPLICATION.search(line):
                violations.append(
                    f"{path.relative_to(ROOT)}:{number}: application imports an outer layer: {line.strip()}"
                )

    # 4. Every browser app consumes published contracts, never backend implementation — from any service.
    implementation = backend_implementation()
    for web in (ROOT / relative for relative in app_paths("web")):
        if not web.is_dir():
            continue
        for path in under(web):
            if not path.is_file() or path.suffix not in {".ts", ".tsx"}:
                continue
            for number, line in enumerate(path.read_text(errors="replace", encoding="utf-8").splitlines(), start=1):
                if IMPORT_LINE.match(line) and implementation.search(line):
                    violations.append(
                        f"{path.relative_to(ROOT)}:{number}: frontend imports backend implementation: {line.strip()}"
                    )

    # 5. Inside a service that holds more than one bounded context, a context reaches another only through
    #    that context's `public` module (`api` in Java, which cannot name a package `public`) — what a
    #    context publishes is its contract, and the rest of it is its own. This is what makes the modular
    #    monolith modular, and what makes moving a context into a service of its own a move rather than a
    #    rewrite: nothing outside it depends on anything but the module it chose to publish. Composition
    #    code that lives in no context is where the contexts meet, and is not checked.
    for service_path, contexts in context_holders().items():
        service = ROOT / service_path
        for path in under(service) if service.is_dir() else []:
            if not path.is_file() or path.suffix not in SOURCE_SUFFIXES:
                continue
            directories = path.relative_to(service).parts[:-1]
            own = next((context for context in contexts if context in directories), None)
            if own is None:
                continue
            published = "api" if path.suffix == ".java" else "public"
            for number, line in enumerate(path.read_text(errors="replace", encoding="utf-8").splitlines(), start=1):
                if not IMPORT_LINE.match(line):
                    continue
                for other in contexts:
                    if other != own and reaches_into(line, other, published):
                        violations.append(
                            f"{path.relative_to(ROOT)}:{number}: {own} reaches into {other}: {line.strip()} — "
                            f"a context crosses into another only through its {other}/{published} module, "
                            "or by reading the events it publishes"
                        )

    if violations:
        print("\n".join(sorted(set(violations))), file=sys.stderr)
        return 1
    print(f"check-imports: inward dependency rule holds ({entries_read} directory entries read)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
