"""S07 T022 (adversary A2, A3): the agent projection reads nothing the verify stamp leaves out of its key.

`make verify-scoped` decides whether `check-agents` runs from what changed, and an ignored file the stamp's exempt list
names (`__pycache__/`, `*.pyc`, `node_modules/`, `dist/`, `target/`, `coverage/` …) is not a change to it. A skill's
own script run on the branch writes a `.pyc` beside it; the projection walked `skills/` whole and read it, so the scoped
gate skipped a check that `make verify` then failed. The list is the stamp's own, read from `verify-stamp.py`: a probe
is made for every entry of it that matches at any depth, so an entry added there is held here the day it exists. A file
the projection does read and cannot decode is one line naming it, never a traceback.
"""
from __future__ import annotations

import ast
import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType

from support import FactoryTestCase
from test_verify_scoped_held import recipes_of
from test_verify_scoped_record import GATES, RecordCase, loaded, record
from test_verify_scoped_table_held import BASE_MODULES, entries_of, modules_of

from slipwai.assets import ROOT

sys.dont_write_bytecode = True

SKILL = "skills/acceptance-review"
PROJECTED = ".claude/skills/acceptance-review"


def stamp_script() -> ModuleType:
    """The stamp as the factory ships it, for its `EXEMPT` list."""
    spec = importlib.util.spec_from_file_location("stamp_under_test", ROOT / "assets/toolkit/scripts/verify-stamp.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def probes() -> list[str]:
    """One file per entry of the stamp's list that matches at any depth, placed inside a skill: under the directory
    the entry names, or named by the pattern the entry is. An entry's exceptions are left where they are."""
    found = []
    for pattern, _, _ in stamp_script().EXEMPT:
        name = pattern.rstrip("/")
        if "/" in name:
            continue  # anchored at the project's own directory, so never under `skills/`
        found.append(f"{SKILL}/scripts/{name.replace('*', 'probe')}/probe.md" if pattern.endswith("/")
                     else f"{SKILL}/scripts/{name.replace('*', 'probe')}")
    return found


class ProjectionCase(FactoryTestCase):
    parent: Path
    built: Path

    @classmethod
    def setUpClass(cls) -> None:
        cls.parent = Path(tempfile.mkdtemp(prefix="projection-exempt-"))
        cls.addClassCleanup(shutil.rmtree, cls.parent, ignore_errors=True)
        cls.built = cls("run").generate(cls.parent, "projected", "standard", "python", "none", http="none")
        subprocess.run(["git", "init", "-q"], cwd=cls.built, check=True)
        cls.project_into(cls.built)

    @staticmethod
    def project_into(repo: Path, *flags: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["python3", "-B", "scripts/agents/project.py", *flags, "claude"], cwd=repo, text=True,
                              capture_output=True, timeout=120)

    def repo(self) -> Path:
        copy = Path(tempfile.mkdtemp(prefix="copy-", dir=self.parent)) / "project"
        shutil.copytree(self.built, copy, symlinks=True)
        return copy

    def write(self, repo: Path, relative: str, data: bytes) -> None:
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)


class ExemptTest(ProjectionCase):
    def test_a2_a_pyc_a_skills_own_script_wrote_is_not_read_by_check_agents(self) -> None:
        repo = self.repo()
        self.assertEqual(self.project_into(repo, "--check").returncode, 0, "the fixture's projection is current")
        # What `python3 skills/<x>/scripts/tool.py` leaves where a sibling module is imported: bytes, not text.
        self.write(repo, f"{SKILL}/scripts/__pycache__/tool.cpython-312.pyc", b"\xcb\r\r\n\x00\x00\x00\x00\xe3\xff")
        checked = self.project_into(repo, "--check")
        self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
        self.assertIn("projected files match", checked.stdout)

    def test_a2_every_entry_of_the_stamps_list_that_can_sit_in_a_skill_is_left_out(self) -> None:
        repo = self.repo()
        made = probes()
        self.assertTrue({f"{SKILL}/scripts/__pycache__/probe.md", f"{SKILL}/scripts/probe.pyc",
                         f"{SKILL}/scripts/node_modules/probe.md", f"{SKILL}/scripts/dist/probe.md",
                         f"{SKILL}/scripts/target/probe.md", f"{SKILL}/scripts/coverage/probe.md"} <= set(made), made)
        for relative in made:
            self.write(repo, relative, b"# text a projection would copy\n")
        checked = self.project_into(repo, "--check")
        self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
        self.assertEqual(self.project_into(repo).returncode, 0)
        written = [relative for relative in made if (repo / relative.replace(SKILL, PROJECTED, 1)).exists()]
        self.assertEqual(written, [], "the projection copied a path the stamp leaves out of its key")

    def test_a2_a_file_beside_them_that_the_list_does_not_name_is_still_projected(self) -> None:
        repo = self.repo()
        self.write(repo, f"{SKILL}/scripts/build/notes.md", b"# not on the list\n")
        checked = self.project_into(repo, "--check")
        self.assertEqual(checked.returncode, 1)
        self.assertIn(f"{PROJECTED}/scripts/build/notes.md: missing", checked.stderr)

    def test_a3_a_file_it_must_read_that_is_not_utf8_is_one_line_naming_it(self) -> None:
        repo = self.repo()
        self.write(repo, f"{SKILL}/table.txt", b"caf\xe9\n")
        for flags in (("--check",), ()):
            done = self.project_into(repo, *flags)
            self.assertEqual(done.returncode, 1, flags)
            self.assertNotIn("Traceback", done.stderr)
            self.assertEqual(len(done.stderr.strip().splitlines()), 1, done.stderr)
            self.assertIn(f"{SKILL}/table.txt", done.stderr)
            self.assertIn("UTF-8", done.stderr)


# A recursive walk: `Path.rglob`, `os.walk`, `Path.walk`, or a `glob` whose pattern holds `**`.
WALKS = ("rglob", "walk")
# What a walk consults to leave out what the stamp leaves out: the stamp's own matcher, called directly or through a
# function of the same module that calls it.
MATCHER = "exempt_entry"
SHAPES = ("standard-python", "model-typescript-web-cloud", "model-go-azure", "standard-spring-web")
# A walk in a module the check loads that the check's own recipe line never reaches, with the line that stops short.
OFF_THE_CHECK_PATH = {
    "check-agents: agents/cruise.py controls_signature()": "taken around an iteration of `cruise.py run`, never by "
                                                           "`--check`",
    "check-agents: agents/cruise.py fingerprint()": "the progress fingerprint of `cruise.py run`, never taken by "
                                                    "`--check`",
}
# Walks found by this test that T029 did not close, because closing them is a product decision: each is handed back
# with the decision it would override. An entry that stops firing fails.
D52 = ("D45 closes the pruned names at four and D52 reads every `target` but a recorded Java root's, so a slice cannot "
       "hide its own source by naming a directory; pruning the stamp's names (`dist/`, `coverage/`, `target/` …) is "
       "that switch, and asking git whether a path is ignored is D52's rejected option (d)")
HANDED_BACK = {
    "check-imports: check-imports.py listing()": D52,
    "check-migrations: check-migrations.py listing()": D52,
}


def is_walk(node: ast.AST) -> bool:
    """A call that descends: a walk, or a `glob` whose pattern, written where it is called, holds `**`."""
    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
        return False
    if node.func.attr in WALKS:
        return True
    return node.func.attr == "glob" and any(isinstance(argument, ast.Constant) and "**" in str(argument.value)
                                            for argument in node.args[:1])


def named(node: ast.AST) -> set[str]:
    return {sub.id if isinstance(sub, ast.Name) else sub.attr for sub in ast.walk(node)
            if isinstance(sub, (ast.Name, ast.Attribute))}


def unscoped_walks(path: Path) -> set[str]:
    """Each function of a script that walks a tree recursively and never consults the stamp's matcher, by name."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    functions = [node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    consulting = {MATCHER}
    while True:
        more = {function.name for function in functions if named(function) & consulting} - consulting
        if not more:
            break
        consulting |= more
    found = set()
    for function in functions:
        inner = {id(sub) for nested in ast.walk(function) if nested is not function
                 and isinstance(nested, (ast.FunctionDef, ast.AsyncFunctionDef)) for sub in ast.walk(nested)}
        if any(is_walk(sub) and id(sub) not in inner for sub in ast.walk(function)) \
                and function.name not in consulting:
            found.add(function.name)
    return found


class WalksHeldTest(RecordCase):
    """Every recursive walk a check makes, where the scoped gate may skip that check, is held to the stamp's list."""

    def test_every_recursive_walk_of_a_scoped_check_consults_the_stamps_list(self) -> None:
        found: set[str] = set()
        for shape in SHAPES:
            project = self.project(shape)
            if record(project).returncode != 0:
                continue
            recipes = recipes_of(project)
            for name, check in loaded(project)["checks"].items():
                if check["inputs"] is None or not check["claims"] or check["always"] or name.split("-")[0] in GATES:
                    continue
                for entry in entries_of(recipes.get(name, [])):
                    for module in modules_of(project, project / entry, exempt=BASE_MODULES.get(name)):
                        where = module.relative_to(project / "scripts").as_posix()
                        found |= {f"{name}: {where} {function}()" for function in unscoped_walks(module)}
        self.maxDiff = None
        self.assertEqual(sorted(found), sorted(OFF_THE_CHECK_PATH | HANDED_BACK))


if __name__ == "__main__":
    unittest.main()
