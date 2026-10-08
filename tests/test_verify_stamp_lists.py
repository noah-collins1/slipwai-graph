"""R6 (AC-S03-9, -32), the closed lists: a check script that reads a path the exempt list leaves out of the key, or a
variable on neither list, fails here.

The scan is a reading of a generated project's check scripts — every string that names a path under an exempt entry
(outside its exceptions), and every upper-case name inside a function that reads the environment — against the
script's own lists, which are imported and never copied. What a check mentions and does not read as an input is an
exemption, with its reason.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path
from types import ModuleType

from stamp_fixture import CI_MARKERS, StampTestCase, load_script

from slipwai.project.gitignore import projection_artifacts

# Mentioned by a check and not an input: the reason is the entry's value.
EXEMPT_PATHS = {
    ".codegraph/gate-memory.json": "the code-index check's memo of itself, rewritten by every pass",
    "__pycache__": "a directory name walked past by the architecture scans, never read",
    ".venv": "a directory name walked past by the architecture scans, never read",
    ".stryker-tmp": "a directory name walked past by the architecture scans, never read",
    ".codegraph/": "a presence check on the directory, whose index is the listed input",
    ".codegraph": "a presence check on the directory, whose index is the listed input",
}
EXEMPT_NAMES = {
    "HEAD": "a git revision",
    "SKIPPED": "a word the gate prints",
    "DS_REQUIRE_BROWSER": "set in the kit's child environment, never read from this one",
}
READ = "{label}: reads {literal}, which an exempt entry leaves out of the key"
PATH_LIKE = re.compile(r"^[\w./*-]+$")
NAME_LIKE = re.compile(r"^[A-Z][A-Z0-9_]{2,}$")


def ignored_patterns(gitignore: str) -> list[str]:
    return [line.strip().lstrip("/") for line in gitignore.splitlines()
            if line.strip() and not line.startswith(("#", "!"))]


def left_out(script: ModuleType, literal: str) -> bool:
    """Whether the exempt list leaves the path (or a directory of that name) out of the key."""
    return script.exempt_entry(literal) is not None or script.exempt_entry(literal.rstrip("/") + "/") is not None


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


def unlisted(paths: list[Path], root: Path, script: ModuleType, variables: set[str]) -> list[str]:
    """Every path one of `paths` names that the exempt list leaves out of the key and every variable it reads that the
    lists do not hold; each finding is led by the script's path under `root`."""
    findings = []
    for path in sorted(paths):
        label = path.relative_to(root).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                literal = node.value
                looks_like_a_path = PATH_LIKE.match(literal) and ("/" in literal or "." in literal)
                if looks_like_a_path and literal not in EXEMPT_PATHS and left_out(script, literal):
                    findings.append(READ.format(label=label, literal=literal))
        for node in ast.walk(tree):
            name = read_directly(node)
            if name is not None and name not in variables and name not in EXEMPT_NAMES:
                findings.append(f"{label}: reads the variable {name}, which is on neither list")
        for function in [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
            if not uses_environment(function):
                continue
            for node in ast.walk(function):
                if not (isinstance(node, ast.Constant) and isinstance(node.value, str)):
                    continue
                name = node.value
                if NAME_LIKE.match(name) and name not in variables and name not in EXEMPT_NAMES:
                    findings.append(f"{label}: reads the variable {name}, which is on neither list")
    return sorted(set(findings))


class ClosedListsTest(StampTestCase):
    def findings(self) -> list[str]:
        script = load_script(self.repo)
        variables = set(script.VARIABLES) | set(script.UNKEYED_VARIABLES) | set(CI_MARKERS)
        checks = sorted((self.repo / "scripts").glob("check-*.py"))
        return unlisted(checks, self.repo, script, variables)

    def plant(self, source: str) -> None:
        (self.repo / "scripts" / "check-planted.py").write_text(source, encoding="utf-8")

    def test_the_checks_a_generated_project_has_read_nothing_the_lists_lack(self) -> None:
        """e7, e9, the sweep: every `check-*.py` of the fixture, against both lists."""
        self.assertEqual(self.findings(), [])

    def test_a_planted_check_that_reads_under_an_exempt_entry_fails_it(self) -> None:
        """AC-S03-32: `.pytest_cache/` is left out of the key, so a check that reads it as an input is a hole."""
        self.plant('from pathlib import Path\nPath(".pytest_cache/v/cache/lastfailed").read_text()\n')
        self.assertEqual(self.findings(), [READ.format(label="scripts/check-planted.py",
                                                       literal=".pytest_cache/v/cache/lastfailed")])

    def test_a_planted_check_that_reads_a_variable_off_the_lists_fails_it(self) -> None:
        """e9: by `os.environ.get` and by the loop `check-slice-scope` reads its variables in."""
        self.plant('import os\nos.environ.get("A_NEW_SWITCH")\n')
        self.assertEqual(self.findings(),
                         ["scripts/check-planted.py: reads the variable A_NEW_SWITCH, which is on neither list"])
        self.plant('import os\n\ndef name():\n    for variable in ("ANOTHER_SWITCH", "UX_GATES_REQUIRE"):\n'
                   '        if os.environ.get(variable):\n            return variable\n')
        self.assertEqual(self.findings(),
                         ["scripts/check-planted.py: reads the variable ANOTHER_SWITCH, which is on neither list"])

    def test_a_planted_check_that_reads_what_the_key_covers_passes_it(self) -> None:
        """e7, e9: a path nothing exempts, an exception an entry names, a listed variable, the unkeyed one, a marker."""
        self.plant('import os\nfrom pathlib import Path\nPath(".env").read_text()\nPath("tools/ux-gates/x.md")\n'
                   'Path(".claude/skills/x")\nPath(".codegraph/codegraph.db")\nPath("node_modules/.package-lock.json")\n'
                   'os.environ.get("UX_GATES_SHARD")\nos.environ.get("UX_GATES_JOBS")\nos.environ.get("CI")\n')
        self.assertEqual(self.findings(), [])

    def test_the_harness_directories_the_generator_ignores_are_in_the_key(self) -> None:
        """AC-S03-32: the registry's projection directories, as `gitignore.py` writes them, are no exempt entry's."""
        script = load_script(self.repo)
        generated = {line.strip() for line in projection_artifacts().splitlines() if line.strip()}
        self.assertTrue(generated)
        for directory in sorted(generated):
            with self.subTest(directory=directory):
                self.assertIsNone(script.exempt_entry(directory.rstrip("/") + "/skill/file.md"))
