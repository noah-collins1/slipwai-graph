"""The file column of the scoped table held against the scripts (research R-8, R-9): a path literal a check script
names that lies under none of the check's recorded inputs fails here, and the table is widened.

Moved out of `test_verify_scoped_record.py`, which had no room left for the four checks' rows. `covered` stays there:
`test_verify_scoped_walks.py` imports it from it.
"""
from __future__ import annotations

import ast
import importlib
import os
import re
import sys
from pathlib import Path

from test_scoped_targets import SHAPES as SHAPE_TABLE
from test_verify_scoped_record import GATES, RecordCase, covered, loaded, record

from slipwai.assets import ROOT

sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "assets" / "toolkit" / "scripts"))

PATH_LIKE = re.compile(r"^[\w./-]+$")
SCRIPT = re.compile(r"scripts/[\w./-]+\.py")
# Read by a check and handled outside the table: a changed one runs the full gate (R5), or it is the gate's own.
ROOT_OWN = ("project.json", "Makefile", "GNUmakefile", "makefile", "scripts", ".git")
# A literal that names a path-looking thing a check does not read as an input of the project: the reason is the value.
NOT_AN_INPUT = {
    ".": "the project's own directory, as a working directory",
    "init": "a subcommand of a tool a check launches, not a path",
    ".claude/projects": "under the user's home (`Path.home()`), where the benchmark reads session transcripts",
    "agents": "a key of a benchmark.json stage, not a path",
    # The four method-file checks (R-1, R-9): what their scripts name that `--check` never reads.
    ".claude/settings.json": "a control path of `agents/cruise.py` (`CONTROL_PATHS`), read by `run` and its guard",
    ".github/workflows": "a control path of `agents/cruise.py` (`CONTROL_PATHS`), read by `run` and its guard",
    ".specify/cruise-inbox.jsonl": "`agents/cruise.py`'s run file, read and written by `run`/`watch`/`tell`",
    ".specify/cruise-last-response.txt": "`agents/cruise.py`'s run file, written by `run`",
    ".specify/cruise-run.log": "`agents/cruise.py`'s run file, written by `run`",
    ".specify/cruise-stream.jsonl": "`agents/cruise.py`'s run file, written by `run`",
    ".specify/cruise-told.jsonl": "`agents/cruise.py`'s run file, written by `tell`",
    ".specify/cruise-watch.cursor": "`agents/cruise.py`'s run file, written by `watch`",
    ".specify/cruise.pid": "`agents/cruise.py`'s run file; `--check` only runs `load()` of `.specify/cruise.json`",
    ".specify/cruise.stop": "`agents/cruise.py`'s run file; `--check` only runs `load()` of `.specify/cruise.json`",
    "docs/event-model/model.yaml": "read by `agents/benchmark.py` and `measures.py` (imported by `cruise.py`), whose "
                                   "`check` is a gate of its own (`check-benchmark`), not of the four `--check`s",
    ".specify/integration.json": "`extensions/guidance.installed_harnesses`, called by `write_project_mcp` on the "
                                 "write paths of an extension's `init.py`; `extensions/project.py --check` never does",
    "agents/registry.json": "`scripts/agents/registry.json` beside the script (its first segment is the root's own "
                            "`agents/`): a gate script, so the full gate already",
}
# The same, as a pattern: one literal for each of a family of paths.
NOT_AN_INPUT_PATTERN = {
    r"skills/[\w-]+/SKILL\.md": "`check-constitution.py`'s `practice` pointers, tested for existence by "
                                  "`present_practice` for `--requirements` only (a printed hint); `--check` opens none",
}


def reads_of(path: Path, project: Path) -> set[str]:
    """Every string literal of a Python file that names something at the project's root: it reads as a path, and its
    first segment is an entry of the project's own directory (so `origin/main` and `slices/README.md` are not one)."""
    found = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and PATH_LIKE.match(node.value):
            literal = node.value.removeprefix("./")
            first = literal.split("/")[0]
            if first and first not in ROOT_OWN and (project / first).exists():
                found.add(literal)
    return found


def explained(read: str) -> bool:
    return read in NOT_AN_INPUT or any(re.fullmatch(pattern, read) for pattern in NOT_AN_INPUT_PATTERN)


def modules_of(project: Path, entry: Path) -> set[Path]:
    """The script and every file of `scripts/` it imports or names, however far: what the check reads through."""
    scripts = project / "scripts"
    seen: set[Path] = set()
    pending = [entry]
    while pending:
        path = pending.pop()
        if path in seen or not path.is_file():
            continue
        seen.add(path)
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            named: list[str] = []
            if isinstance(node, ast.Import):
                named = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                base = "." * node.level + (node.module or "")
                named = [base, *(f"{base}.{alias.name}" for alias in node.names)] if node.module else \
                    [f"{base}{alias.name}" for alias in node.names]
            elif isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value.endswith(".py"):
                named = [node.value]
            for name in named:
                pending.extend(candidates(name, path.parent, scripts))
    return seen


def candidates(name: str, here: Path, scripts: Path) -> list[Path]:
    if name.endswith(".py"):
        return [directory / name for directory in (here, scripts)]
    dots = len(name) - len(name.lstrip("."))
    parts = name.lstrip(".").split(".")
    roots = [here.parents[dots - 1] if dots > 1 else here] if dots else [here, scripts]
    found = []
    for root in roots:
        found += [root.joinpath(*parts).with_suffix(".py"), root.joinpath(*parts, "__init__.py")]
    return found


class TableHeldTest(RecordCase):
    """The file column against the scripts: a check's script, and what it imports, names no project path the check's
    recorded inputs leave out. A check with no recorded inputs is held to nothing."""

    SHAPES = tuple(SHAPE_TABLE)  # every shape the factory generates for the scoped gate, a cloud one among them

    def findings(self) -> list[str]:
        records = importlib.import_module("verify_scoped.record")  # the script's own reading of the make database
        findings = []
        fired: set[str] = set()
        for shape in self.SHAPES:
            project = self.project(shape)
            if record(project).returncode != 0:  # a shape whose record is refused (`integration`) has no table to hold
                continue
            data = loaded(project)
            was = os.getcwd()
            os.chdir(project)
            try:
                recipes = records.database("make", "Makefile").recipes
            finally:
                os.chdir(was)
            for name, check in data["checks"].items():
                if check["inputs"] is None or name.split("-")[0] in GATES:
                    continue
                entries = [found for line in recipes.get(name, []) for found in re.findall(SCRIPT, line)]
                reads: set[str] = set()
                for entry in entries:
                    for module in modules_of(project, project / entry):
                        reads |= reads_of(module, project)
                files = check["inputs"]["files"]
                findings += [f"{shape}: {name} reads {read}, under none of {files}" for read in sorted(reads)
                             if not covered(read, files) and not explained(read)]
                fired.update(read for read in reads if not covered(read, files))
        stale = sorted(set(NOT_AN_INPUT) - fired)
        findings += [f"{pattern} is explained, and no check reads it any more" for pattern in NOT_AN_INPUT_PATTERN
                     if not any(re.fullmatch(pattern, read) for read in fired)]
        findings += [f"{read} is explained, and no check reads it any more" for read in stale]
        return findings

    def test_e4_every_path_a_check_script_reads_lies_under_one_of_its_recorded_inputs(self) -> None:
        self.assertEqual(self.findings(), [])
