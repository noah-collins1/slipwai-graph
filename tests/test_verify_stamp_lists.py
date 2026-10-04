"""R6 (AC-S03-7, -9), the closed lists: a check script that reads what git ignores, or a variable, that is on neither
list fails here.

The scan is a reading of the generated project's `scripts/check-*.py` — every string that names a path git ignores
there, and every upper-case name inside a function that reads the environment — against the script's own lists, which
are imported and never copied. What a check mentions and does not read as an input is an exemption, with its reason.
"""
from __future__ import annotations

import ast
import fnmatch
import re
from pathlib import Path

from stamp_fixture import CI_MARKERS, StampTestCase, load_script

from slipwai.project.gitignore import projection_artifacts

# Mentioned by a check and not an input: the reason is the entry's value.
EXEMPT_PATHS = {
    ".codegraph/gate-memory.json": "the code-index check's memo of itself, rewritten by every pass",
    "__pycache__": "a directory name walked past by the architecture scans, never read",
    ".venv": "a directory name walked past by the architecture scans, never read",
    ".codegraph/": "a presence check on the directory, whose index is the listed input",
    ".codegraph": "a presence check on the directory, whose index is the listed input",
}
EXEMPT_NAMES = {
    "HEAD": "a git revision",
    "SKIPPED": "a word the gate prints",
    "DS_REQUIRE_BROWSER": "set in the kit's child environment, never read from this one",
}
PATH_LIKE = re.compile(r"^[\w./*-]+$")
NAME_LIKE = re.compile(r"^[A-Z][A-Z0-9_]{2,}$")


def ignored_patterns(gitignore: str) -> list[str]:
    return [line.strip().lstrip("/") for line in gitignore.splitlines()
            if line.strip() and not line.startswith(("#", "!"))]


def names_ignored_path(literal: str, patterns: list[str]) -> bool:
    """Whether a string that looks like a path is one git's ignore patterns take, or sits under a directory they do."""
    parts = literal.strip("/").split("/")
    prefixes = ["/".join(parts[: index + 1]) for index in range(len(parts))]
    for pattern in patterns:
        bare = pattern.rstrip("/")
        if "/" in bare:
            if any(fnmatch.fnmatch(prefix, bare) for prefix in prefixes):
                return True
        elif any(fnmatch.fnmatch(part, bare) for part in parts):
            return True
    return False


def on_the_list(literal: str, entries: tuple[str, ...]) -> bool:
    """Whether a path is one of the list's entries, or inside one, or is a directory above one."""
    path = literal.strip("/")
    for entry in entries:
        bare = entry.rstrip("/")
        if fnmatch.fnmatch(path, bare) or path.startswith(bare + "/") or bare.startswith(path + "/"):
            return True
    return False


def uses_environment(node: ast.AST) -> bool:
    return any(
        isinstance(item, ast.Attribute) and item.attr in ("environ", "getenv")
        and isinstance(item.value, ast.Name) and item.value.id == "os"
        for item in ast.walk(node)
    )


def read_directly(node: ast.AST) -> str | None:
    """The literal name in `os.environ.get("X")`, `os.environ["X"]` or `os.getenv("X")`, where it is spelled out."""
    if isinstance(node, ast.Call) and node.args and isinstance(node.args[0], ast.Constant):
        called = node.func
        if isinstance(called, ast.Attribute) and called.attr in ("get", "getenv") and uses_environment(called):
            return str(node.args[0].value)
    if isinstance(node, ast.Subscript) and uses_environment(node.value) and isinstance(node.slice, ast.Constant):
        return str(node.slice.value)
    return None


def unlisted(scripts: Path, gitignore: str, entries: tuple[str, ...], variables: set[str]) -> list[str]:
    """Every ignored path a check names and every variable a check reads that the lists do not hold."""
    patterns = ignored_patterns(gitignore)
    findings = []
    for path in sorted(scripts.glob("check-*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                literal = node.value
                looks_like_a_path = PATH_LIKE.match(literal) and ("/" in literal or "." in literal)
                unlisted_path = literal not in EXEMPT_PATHS and not on_the_list(literal, entries)
                if looks_like_a_path and unlisted_path and names_ignored_path(literal, patterns):
                    findings.append(f"{path.name}: reads the ignored path {literal}, which is not on the list")
        for node in ast.walk(tree):
            name = read_directly(node)
            if name is not None and name not in variables and name not in EXEMPT_NAMES:
                findings.append(f"{path.name}: reads the variable {name}, which is on neither list")
        for function in [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
            if not uses_environment(function):
                continue
            for node in ast.walk(function):
                if not (isinstance(node, ast.Constant) and isinstance(node.value, str)):
                    continue
                name = node.value
                if NAME_LIKE.match(name) and name not in variables and name not in EXEMPT_NAMES:
                    findings.append(f"{path.name}: reads the variable {name}, which is on neither list")
    return sorted(set(findings))


class ClosedListsTest(StampTestCase):
    def findings(self) -> list[str]:
        script = load_script(self.repo)
        variables = set(script.VARIABLES) | set(script.UNKEYED_VARIABLES) | set(CI_MARKERS)
        gitignore = (self.repo / ".gitignore").read_text(encoding="utf-8")
        return unlisted(self.repo / "scripts", gitignore, tuple(script.IGNORED_INPUTS), variables)

    def plant(self, source: str) -> None:
        (self.repo / "scripts" / "check-planted.py").write_text(source, encoding="utf-8")

    def test_the_checks_a_generated_project_has_read_nothing_the_lists_lack(self) -> None:
        """e7, e9, the sweep: every `check-*.py` of the fixture, against both lists."""
        self.assertEqual(self.findings(), [])

    def test_a_planted_check_that_reads_an_ignored_path_off_the_list_fails_it(self) -> None:
        """e7: `.pytest_cache/` is ignored and is no input the list holds."""
        self.plant('from pathlib import Path\nPath(".pytest_cache/v/cache/lastfailed").read_text()\n')
        self.assertEqual(self.findings(), ["check-planted.py: reads the ignored path .pytest_cache/v/cache/lastfailed, "
                                           "which is not on the list"])

    def test_a_planted_check_that_reads_a_variable_off_the_lists_fails_it(self) -> None:
        """e9: by `os.environ.get` and by the loop `check-slice-scope` reads its variables in."""
        self.plant('import os\nos.environ.get("A_NEW_SWITCH")\n')
        self.assertEqual(self.findings(),
                         ["check-planted.py: reads the variable A_NEW_SWITCH, which is on neither list"])
        self.plant('import os\n\ndef name():\n    for variable in ("ANOTHER_SWITCH", "UX_GATES_REQUIRE"):\n'
                   '        if os.environ.get(variable):\n            return variable\n')
        self.assertEqual(self.findings(),
                         ["check-planted.py: reads the variable ANOTHER_SWITCH, which is on neither list"])

    def test_a_planted_check_that_reads_what_the_lists_hold_passes_it(self) -> None:
        """e7, e9: a listed path, a listed variable, the unkeyed one, a CI marker."""
        self.plant('import os\nfrom pathlib import Path\nPath(".env").read_text()\nPath("tools/ux-gates/x.md")\n'
                   'Path(".claude/skills/x")\nos.environ.get("UX_GATES_SHARD")\nos.environ.get("UX_GATES_JOBS")\n'
                   'os.environ.get("CI")\n')
        self.assertEqual(self.findings(), [])

    def test_the_harness_directories_on_the_list_are_the_ones_the_generator_ignores(self) -> None:
        """e7: the registry's projection directories, as `gitignore.py` writes them, are all on the list."""
        script = load_script(self.repo)
        generated = {line.strip() for line in projection_artifacts().splitlines() if line.strip()}
        self.assertTrue(generated)
        self.assertEqual(generated - set(script.IGNORED_INPUTS), set())
