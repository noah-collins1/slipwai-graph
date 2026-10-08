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
import unittest
from pathlib import Path
from typing import Any

from test_scoped_targets import SHAPES as SHAPE_TABLE
from test_scoped_targets import database
from test_verify_scoped_record import GATES, RecordCase, covered, loaded, record

from slipwai.assets import ROOT

sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "assets" / "toolkit" / "scripts"))

PATH_LIKE = re.compile(r"^[\w./-]+$")
SCRIPT = re.compile(r"scripts/[\w./-]+\.py")
# What `verify_scoped/methods.py` derives inputs from, as a file name a script names whole (`"registry.json"`).
DERIVED = re.compile(r"^[\w./*-]*(?:registry\.json|\.manifest\.json)$")
# A claiming check outside the four whose closure names one of them, and does not read what it derives from it.
DERIVED_NOT_READ = {
    "check-benchmark": "`agents/benchmark.py` names `registry.json` for `cursor()`, the transcript cursor of its "
                       "`start` and `end`; `check` never calls it, and the file is under `scripts/`, the full gate",
}
FOUR = ("check-agents", "check-speckit", "check-extensions", "check-constitution")
# Read by a check and handled outside the table: a changed one runs the full gate (R5), or it is the gate's own.
ROOT_OWN = ("project.json", "Makefile", "GNUmakefile", "makefile", "scripts", ".git")


def for_checks(checks: tuple[str, ...], literal: str, reason: str) -> dict[tuple[str, str], str]:
    """One exemption for each check it was written for: a check not named is not excused by it."""
    return {(check, literal): reason for check in checks}


# A literal that names a path-looking thing one check does not read as an input of the project, by (check, literal): the
# reason is the value. A literal the other checks' rows would still have to cover is never excused for them, and an
# entry its check no longer fires is stale.
NOT_AN_INPUT_FOR = {
    **for_checks(("check-agents", "check-benchmark", "check-decisions", "check-deploy-role", "check-extensions",
                  "check-imports", "check-migrations", "check-model", "check-styles", "check-ux-gates"), ".",
                 "the project's own directory, as a working directory"),
    **for_checks(("check-agents", "check-ux-gates"), "init", "a subcommand of a tool a check launches, not a path"),
    **for_checks(("check-agents", "check-benchmark"), ".claude/projects",
                 "under the user's home (`Path.home()`), where the benchmark reads session transcripts"),
    ("check-decisions", "agents"): "a key of a benchmark.json stage, not a path",
    # The four method-file checks (R-1, R-9): what their scripts name that `--check` never reads.
    ("check-agents", ".claude/settings.json"): "a control path of `agents/cruise.py` (`CONTROL_PATHS`), read by `run` "
                                              "and its guard",
    ("check-agents", ".github/workflows"): "a control path of `agents/cruise.py` (`CONTROL_PATHS`), read by `run` and "
                                          "its guard",
    ("check-agents", ".specify/cruise-inbox.jsonl"): "`agents/cruise.py`'s run file, read and written by "
                                                    "`run`/`watch`/`tell`",
    ("check-agents", ".specify/cruise-last-response.txt"): "`agents/cruise.py`'s run file, written by `run`",
    ("check-agents", ".specify/cruise-run.log"): "`agents/cruise.py`'s run file, written by `run`",
    ("check-agents", ".specify/cruise-stream.jsonl"): "`agents/cruise.py`'s run file, written by `run`",
    ("check-agents", ".specify/cruise-told.jsonl"): "`agents/cruise.py`'s run file, written by `tell`",
    ("check-agents", ".specify/cruise-watch.cursor"): "`agents/cruise.py`'s run file, written by `watch`",
    ("check-agents", ".specify/cruise.pid"): "`agents/cruise.py`'s run file; `--check` only runs `load()` of "
                                            "`.specify/cruise.json`",
    ("check-agents", ".specify/cruise.stop"): "`agents/cruise.py`'s run file; `--check` only runs `load()` of "
                                             "`.specify/cruise.json`",
    ("check-agents", "docs/event-model/model.yaml"): "read by `agents/benchmark.py` and `measures.py` (imported by "
                                                    "`cruise.py`), whose `check` is a gate of its own "
                                                    "(`check-benchmark`), not of the four `--check`s",
    ("check-extensions", ".specify/integration.json"): "`extensions/guidance.installed_harnesses`, called by "
                                                      "`write_project_mcp` on the write paths of an extension's "
                                                      "`init.py`; `extensions/project.py --check` never does",
    **for_checks(("check-extensions", "check-speckit"), "agents/registry.json",
                 "`scripts/agents/registry.json` beside the script (its first segment is the root's own `agents/`): "
                 "a gate script, so the full gate already"),
    ("check-decisions", ".slipwai"): "`reversibility.py` joins it to `propagated`, which the row names whole "
                                     "(`.slipwai/propagated`); the directory is never read as a path of its own",
    ("check-decisions", ".."): "`reversibility.py`'s `inside` refuses a path whose first segment is `..`; compared, "
                               "never opened",
    # `"provisional"` is a `decide` value in `agents/cruise.py`'s `CONTROLS`, which the scan takes for a sibling script
    # named without its suffix and so walks `provisional.py` and the `reversibility.py` it loads; `cruise.py` never
    # loads either (`--check` reads `.specify/cruise.json` alone), so the two literals are `check-decisions`' above.
    ("check-agents", ".slipwai"): "reached only through `provisional.py`, which `cruise.py` names as a `decide` value "
                                  "(a string, not a module it loads)",
    ("check-agents", ".."): "reached only through `provisional.py` -> `reversibility.py`'s `inside`, which `cruise.py` "
                            "names as a `decide` value (a string, not a module it loads)",
    # S27 T027 (D204): `provisional.py`'s closed list names CI workflow directories and control paths by their segments,
    # to compare with a decision's `Written to`; `check-decisions` loads it, and `check-agents` reaches it as above.
    **for_checks(("check-agents", "check-decisions"), ".github",
                 "a segment of `provisional.py`'s closed list (`CI_DIRECTORIES`), compared with `Written to`, never "
                 "opened"),
    **for_checks(("check-agents", "check-decisions"), ".claude",
                 "a segment of `provisional.py`'s closed list (a control path), compared with `Written to`, never "
                 "opened"),
    # S27 T041 (D209): the verb `status` of `provisional.py` reads `.specify/cruise.json` (its `decide`), named as the
    # segments `CONFIG_PARTS`; only the verb opens it, never `check-decisions` (which loads the module for its gate
    # functions) and never `check-agents` (which reaches the module as above).
    **for_checks(("check-agents", "check-decisions"), ".specify",
                 "a segment of `provisional.py`'s `CONFIG_PARTS`, opened by its `status` verb alone, never by a check"),
    ("check-agents", ".slipwai/extensions.json"): "`agents/code_index.py`'s `adopted()`, which `cruise.py` imports "
                                                  "and calls on `health`/`run` paths; `cruise.py --check` never does",
}
# The same, as a pattern: one literal for each of a family of paths, by (check, pattern).
NOT_AN_INPUT_PATTERN_FOR = {
    ("check-constitution", r"skills/[\w-]+/SKILL\.md"): "`check-constitution.py`'s `practice` pointers, tested for "
                                  "existence by `present_practice` inside `findings()` for a requirement already "
                                  "reported as failing: a missing skill changes the failure text (`; see skills/…`) "
                                  "and never the exit status (`test_verify_scoped_flips_practice`)",
}
# Modules a check loads only to find the slice's base and the paths changed since it, by check (`check-ux-gates`'s
# default, research R-6): not walked for the check that loads them, since the stamp's cruise files, the model and the
# registry they name are the full gate's or another check's. Each is a file name, or a directory under `scripts/`; the
# reason is the value. A module its check no longer reaches is stale, as `NOT_AN_INPUT_FOR` is when no check fires it.
BASE_MODULES = {
    "check-agents": {
        "verify-stamp.py": "loaded by `agents/project.py` for `exempt_entry`, so the projection reads nothing the "
                           "stamp leaves out of its key (S07 T022); nothing the stamp names is read by the check",
    },
    "check-benchmark": {
        "verify-stamp.py": "loaded by `agents/benchmark.py` for `exempt_entry` (S07 T029), and reached as "
                           "`check-agents` reaches it; nothing the stamp names is read by the check",
    },
    **{name: {"verify-stamp.py": "loaded for `exempt_entry`, so the check walks nothing the stamp leaves out of its "
                                 "key (S07 T029); nothing the stamp names is read by the check"}
       for name in ("check-styles", "check-flags", "check-deploy-role")},
    "check-ux-gates": {
        "verify-stamp.py": "loaded for `trunk_module()` and the questions the scoped gate's borders ask: CI markers, "
                           "`HEAD`, the index and the trunk; nothing it names is read by the check that loads it",
        "check-slice-scope.py": "the one definition of the trunk and the base (`merge_base`, `changed_files`); the "
                                "check that loads it reads none of what it reads",
        "verify_scoped": "`changes.changed` and `changes.unpushed` give the changed paths and `since.py` the borders; "
                         "the package's own tables and rules are the scoped gate's, not the loading check's inputs",
    },
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


def entries_of(lines: list[str]) -> list[str]:
    """The check scripts a recipe's lines run: every one, as `check-agents`' chained line runs three."""
    return [found for line in lines for found in re.findall(SCRIPT, line)]


def closure_literals(project: Path, name: str, recipes: dict[str, list[str]]) -> set[str]:
    """Every string a check's scripts, and what they import or name, hold."""
    found: set[str] = set()
    for entry in entries_of(recipes.get(name, [])):
        for module in modules_of(project, project / entry, exempt=BASE_MODULES.get(name)):
            found.update(node.value for node in ast.walk(ast.parse(module.read_text(encoding="utf-8")))
                         if isinstance(node, ast.Constant) and isinstance(node.value, str))
    return found


def derived_readers(project: Path, data: dict[str, Any], recipes: dict[str, list[str]]) -> list[str]:
    """The claiming checks outside the four whose scripts name a manifest or the registry (D172 limit ii): what those
    name is derived into the four's inputs only, so a fifth that reads them would be skipped when they change."""
    found = []
    for name, check in sorted(data["checks"].items()):
        if name in FOUR or name.split("-")[0] in GATES or check["inputs"] is None or not check["claims"] \
                or check["always"] or name in DERIVED_NOT_READ:
            continue
        found += [f"{name} reads {literal}" for literal in sorted(closure_literals(project, name, recipes))
                  if DERIVED.match(literal)]
    return found


def explained(read: str, name: str) -> bool:
    return (name, read) in NOT_AN_INPUT_FOR \
        or any(check == name and re.fullmatch(pattern, read) for check, pattern in NOT_AN_INPUT_PATTERN_FOR)


def base_module(path: Path) -> str:
    """What a file is called in `BASE_MODULES`: its name, or `verify_scoped` for a file of that package."""
    return "verify_scoped" if path.parent.name == "verify_scoped" else path.name


def modules_of(project: Path, entry: Path, skipped: set[str] | None = None,
               exempt: dict[str, str] | None = None) -> set[Path]:
    """The script and every file of `scripts/` it imports or names, however far: what the check reads through, but for
    the modules `exempt` names (`BASE_MODULES` of the check walked), which are not walked; `skipped` collects the ones
    the walk met."""
    scripts = project / "scripts"
    exempt = exempt or {}
    seen: set[Path] = set()
    pending = [entry]
    while pending:
        path = pending.pop()
        if path in seen or not path.is_file():
            continue
        loaded_for_the_base = base_module(path)
        if path != entry and loaded_for_the_base in exempt:
            if skipped is not None:
                skipped.add(loaded_for_the_base)
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
            elif isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value.isidentifier():
                named = [f"{node.value}.py"]  # a sibling named without its suffix (`check-decisions`' `sibling()`)
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
        fired_for: set[tuple[str, str]] = set()
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
                entries = entries_of(recipes.get(name, []))
                reads: set[str] = set()
                for entry in entries:
                    for module in modules_of(project, project / entry, exempt=BASE_MODULES.get(name)):
                        reads |= reads_of(module, project)
                files = check["inputs"]["files"]
                findings += [f"{shape}: {name} reads {read}, under none of {files}" for read in sorted(reads)
                             if not covered(read, files) and not explained(read, name)]
                fired_for.update((name, read) for read in reads if not covered(read, files))
        findings += [f"{name} is explained for {pattern}, and no longer reads it" for name, pattern in
                     sorted(NOT_AN_INPUT_PATTERN_FOR) if not any(
                         check == name and re.fullmatch(pattern, read) for check, read in fired_for)]
        findings += [f"{name} is explained for {read}, and no longer reads it" for name, read in
                     sorted(set(NOT_AN_INPUT_FOR) - fired_for)]
        return findings

    def test_e4_every_path_a_check_script_reads_lies_under_one_of_its_recorded_inputs(self) -> None:
        self.assertEqual(self.findings(), [])

    def test_e4_no_claiming_check_outside_the_four_reads_the_registry_or_a_manifest(self) -> None:
        findings = []
        named: set[str] = set()
        for shape in self.SHAPES:
            project = self.project(shape)
            if record(project).returncode != 0:
                continue
            data = loaded(project)
            recipes = {name: lines for name, (_, lines) in database(project).items()}
            findings += [f"{shape}: {line}" for line in derived_readers(project, data, recipes)]
            named.update(name for name in DERIVED_NOT_READ if name in recipes
                         and any(DERIVED.match(literal) for literal in closure_literals(project, name, recipes)))
        findings += [f"{name} is allowed to name a derived file, and no longer does"
                     for name in sorted(set(DERIVED_NOT_READ) - named)]
        self.assertEqual(findings, [])


class ExemptionsAreScopedTest(unittest.TestCase):
    """T019 (finding 6): an exemption excuses a literal for the check it was written for, and for no other."""

    def test_a_literal_is_excused_for_its_check_and_not_for_another_that_names_it(self) -> None:
        self.assertTrue(explained("init", "check-agents"))
        self.assertFalse(explained("init", "check-model"))
        self.assertTrue(explained(".github/workflows", "check-agents"))
        self.assertFalse(explained(".github/workflows", "check-speckit"))
        self.assertFalse(explained(".specify/integration.json", "check-agents"))
        self.assertTrue(explained(".specify/integration.json", "check-extensions"))

    def test_a_pattern_is_excused_for_its_check_only(self) -> None:
        self.assertTrue(explained("skills/tdd/SKILL.md", "check-constitution"))
        self.assertFalse(explained("skills/tdd/SKILL.md", "check-agents"))

    def test_no_check_is_excused_by_a_literal_alone(self) -> None:
        self.assertFalse(explained("init", ""))


class BaseModulesTest(RecordCase):
    """The named list is load-bearing and not stale (research R-6)."""

    def walk(self, name: str, exempt: dict[str, str] | None) -> tuple[set[str], set[str]]:
        """What a check's walk reached, as `BASE_MODULES` names a file, and the base modules it met and did not walk."""
        project = self.project("model-typescript-web-cloud")  # a shape with every check that loads a base module
        recipes = {key: lines for key, (_, lines) in database(project).items()}
        reached: set[str] = set()
        skipped: set[str] = set()
        for entry in entries_of(recipes[name]):
            reached |= {base_module(path) for path in modules_of(project, project / entry, skipped, exempt)}
        return reached, skipped

    def test_a_check_with_base_modules_meets_them_and_walks_none_of_them(self) -> None:
        for name, modules in BASE_MODULES.items():
            reached, skipped = self.walk(name, modules)
            self.assertTrue(skipped, f"{name} loads no base module")
            self.assertEqual(reached & set(modules), set(), f"{name} walks one of {sorted(modules)}")

    def test_every_base_module_is_reached_by_the_walk_that_does_not_exempt_it(self) -> None:
        """Without the list the walk reaches each one: each entry is load-bearing, and one no check loads is stale."""
        for name, modules in BASE_MODULES.items():
            reached, skipped = self.walk(name, None)
            self.assertEqual(skipped, set())
            self.assertEqual(set(modules) - reached, set(), f"{name}: a base module it no longer loads is stale")
