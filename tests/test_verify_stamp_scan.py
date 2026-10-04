"""R6 (AC-S03-9, -32), T017: the closed-list test scans every script the gate runs, in every shape of project.

The subject is derived from the generated `Makefile`, not from a file-name pattern: the targets `verify-checks` (or
`verify`, where a project has no stamp) depends on, transitively and through `$(MAKE)`; every `scripts/…` file their
recipes launch; and whatever a launched script imports or names as a `*.py` file under `scripts/`. A script added to a
recipe — or a sibling a script loads — is scanned the day it exists. What the scan cannot read is named below with the
reason it holds nothing, so a new one fails the test; and every ignore line a project can get is, in both directions,
either left out of the key by an exempt entry with its reason or in the key — a file at it moves the key.
"""
from __future__ import annotations

import ast
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from types import ModuleType

from stamp_fixture import CI_MARKERS, exclude, key_of, load_script, probe_path, template
from support import FactoryTestCase
from test_verify_stamp_lists import READ, ignored_patterns, unlisted

# Shapes that add a prerequisite or an ignore line: (name, profile, backend, frontend, axes).
SHAPES = (
    ("standard-python", "standard", "python", "none", {"http": "none"}),
    ("model-typescript-web", "event-modelling", "typescript", "react-vite", {"http": "fastify"}),
    ("model-typescript-web-cloud", "event-modelling", "typescript", "react-vite", {"http": "fastify", "target": "aws"}),
    ("model-python-sqlite", "event-modelling", "python", "none", {"http": "fastapi", "event_store": "sqlite"}),
    ("model-go-azure", "event-modelling", "go", "none", {"http": "net-http", "target": "azure"}),
    ("standard-quarkus", "standard", "java-quarkus", "none", {"http": "quarkus-rest"}),
    ("standard-spring-web", "standard", "java-spring", "react-vite", {"http": "spring-web"}),
)
# Launched by a recipe the gate runs and not Python: the reason it holds no read of an ignored path or a variable.
NOT_SCANNED = {
    "scripts/event-model/render-drawio.ts": "`check-drawio`: reads docs/event-model/model.yaml and compares the"
    " committed model.drawio, both tracked, and the model tooling whose installed manifest is on the list",
    "scripts/verify": "the shell runner of `lint`, `typecheck` and `test` per backend: it launches the project's"
    " own tools and syncs `.venv` from the lock on every run, and reads no path a gate script names; the variables"
    " it and the Maven wrapper read are named in `test_verify_stamp_launches`, each deciding which tool is asked or"
    " configuring one",
}
# Launched by a recipe the gate runs, and not an input: the stamp is the thing that reads the lists.
THE_STAMP = "scripts/verify-stamp.py"
# Where a probe for an entry that matches at any depth is put: the places the factory's ignore lines are anchored.
PLACES = ("", "apps/service/", "apps/web/", "packages/x/", "infra/stack/")
# Exempt entries no generated ignore line has: the caches a gate's own tools write, which the factory does not list.
NOT_GENERATED = {
    ".mypy_cache/": "`mypy` in `typecheck`",
    ".coverage": "`coverage` beside `pytest`",
    "*.tsbuildinfo": "`tsc` incremental builds",
}


def _reads(script: str, *literals: str) -> dict[str, str]:
    return {READ.format(label=script, literal=literal): "" for literal in literals}


def _variables(script: str, *names: str) -> dict[str, str]:
    return {f"{script}: reads the variable {name}, which is on neither list": "" for name in names}


def _because(reason: str, findings: dict[str, str]) -> dict[str, str]:
    return {finding: reason for finding in findings}


# What a script the gate runs mentions and the gate does not read, or reads and the key cannot hold, each finding with
# its reason: the sweep of T017. A finding that no longer fires fails the test, so the table never outlives its cause.
CRUISE = "scripts/agents/cruise.py"
EXPLAINED = {
    **_because("`/cruise`'s run state, read by `cruise.py run`, `watch`, `status` and `stop`; the gate runs `--check`, "
               "which reads `.specify/cruise.json`, tracked", _reads(
                   CRUISE, ".specify/cruise-inbox.jsonl", ".specify/cruise-last-response.txt",
                   ".specify/cruise-run.log", ".specify/cruise-stream.jsonl", ".specify/cruise-told.jsonl",
                   ".specify/cruise-watch.cursor", ".specify/cruise.pid", ".specify/cruise.stop",
                   "specs/cruise-checkpoint.md")),
    **_because("how `/cruise` starts and paces a harness, read by `run` and `watch`, not by `--check`",
               _variables(CRUISE, "CRUISE_HARNESS_COMMAND", "CRUISE_HARNESS_STREAM", "CRUISE_POLL_SECONDS",
                          "CRUISE_WATCH_TICK")),
    **_because("which session is recording; read by `benchmark.py start` and `end`, never by `check`",
               _variables("scripts/agents/benchmark.py", "CLAUDE_CODE_SESSION_ID", "CODEX_HOME", "CODEX_THREAD_ID")),
    **_because("where the CodeGraph binary is looked for: `PATH` and a user-level tool configuration, D73's residual",
               _variables("scripts/agents/code_index.py", "FNM_DIR", "NVM_DIR", "PATH", "VOLTA_HOME")),
    **_because("set in a child's environment to stop an update check, never read from this one",
               _variables("scripts/agents/code_index.py", "CODEGRAPH_NO_UPDATE_CHECK")
               | _variables("scripts/extensions/codegraph/init.py", "CODEGRAPH_NO_UPDATE_CHECK")),
    **_because("a directory name in the set of directories the flag scan walks past, never read",
               _reads("scripts/check-flags.py", ".build")),
    **_because("written by the `go test` on the line before it in the same recipe, on every run",
               _reads("scripts/go-coverage.py", "coverage.out")),
    **_because("the installer `./init` runs, which `extensions/guidance.py` names; no gate recipe runs it",
               _variables("scripts/install-tools.py", "LOCALAPPDATA", "PATH", "SLIPWAI_HOST_SYSTEM")),
}
RULE = re.compile(r"^([^\s:=#$][^:=]*?):(?!=)(.*)$")
LAUNCHED = re.compile(r"(?:^|[\s\"'=(])((?:[\w./-]*/)?scripts/[\w./-]+)")
NAMED_FILE = re.compile(r"^[\w-]+\.py$")


def makefile_rules(text: str) -> dict[str, tuple[set[str], list[str]]]:
    """Each target's prerequisites and recipe lines, a target named twice merged, `\\` continuations joined."""
    rules: dict[str, tuple[set[str], list[str]]] = {}
    current: list[str] = []
    for line in re.sub(r"\\\n\s*", " ", text).splitlines():
        if line.startswith("\t"):
            for target in current:
                rules[target][1].append(line.strip())
            continue
        found = RULE.match(line.split("##")[0].rstrip()) if not line.startswith("#") else None
        if not found or found.group(1).startswith("."):
            current = []
            continue
        current = found.group(1).split()
        for target in current:
            needs = rules.setdefault(target, (set(), []))[0]
            needs.update(word for word in found.group(2).split() if "$(" not in word)
    return rules


def gate_targets(rules: dict[str, tuple[set[str], list[str]]]) -> set[str]:
    """`verify-checks` (`verify` where a project has no stamp) and all it reaches, by prerequisite or `$(MAKE)`."""
    seen: set[str] = set()
    todo = ["verify-checks" if "verify-checks" in rules else "verify"]
    while todo:
        target = todo.pop()
        if target in seen or target not in rules:
            continue
        seen.add(target)
        todo.extend(rules[target][0])
        for line in rules[target][1]:
            if "$(MAKE)" in line:
                todo.extend(word for word in line.split() if word in rules)
    return seen


def referenced(script: Path, root: Path) -> set[Path]:
    """The `.py` files under `root` that `script` imports by their name, or names in a string as a file."""
    names = {path.stem: path for path in root.rglob("*.py")}
    found: set[Path] = set()
    for node in ast.walk(ast.parse(script.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            modules = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            modules = [node.module]
        else:
            modules = []
        found.update(names[module.split(".")[0]] for module in modules if module.split(".")[0] in names)
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and NAMED_FILE.match(node.value):
            found.update(path for path in root.rglob(node.value))
    found.discard(script)
    return {path for path in found if path.name != Path(THE_STAMP).name}


def gate_scripts(project: Path) -> tuple[list[Path], set[str]]:
    """Every Python script a prerequisite of the gate runs or imports, and the other files its recipes launch."""
    rules = makefile_rules((project / "Makefile").read_text(encoding="utf-8"))
    launched = {
        match.group(1).lstrip("./")
        for target in gate_targets(rules) for line in rules[target][1] for match in LAUNCHED.finditer(line)
    }
    launched = {relative for relative in launched if relative != THE_STAMP and (project / relative).is_file()}
    python = {project / relative for relative in launched if relative.endswith(".py")}
    root = project / "scripts"
    todo = list(python)
    while todo:
        for path in referenced(todo.pop(), root):
            if path not in python:
                python.add(path)
                todo.append(path)
    return sorted(python), {relative for relative in launched if not relative.endswith(".py")}


_projects: dict[str, Path] = {}


class GateScriptsTest(FactoryTestCase):
    def project(self, shape: tuple[str, str, str, str, dict[str, str]]) -> Path:
        _, profile, backend, frontend, axes = shape
        name = f"gate{SHAPES.index(shape)}"
        if name not in _projects:
            directory = tempfile.mkdtemp(prefix="stamp-scan-")
            self.addClassCleanup(shutil.rmtree, directory, ignore_errors=True)
            self.addClassCleanup(_projects.pop, name, None)
            _projects[name] = self.generate(directory, name, profile, backend, frontend, **axes)
        return _projects[name]

    def lists(self) -> tuple[ModuleType, set[str]]:
        script = load_script(template())
        return script, set(script.VARIABLES) | set(script.UNKEYED_VARIABLES) | set(CI_MARKERS)

    def raw(self, project: Path, scripts: list[Path]) -> list[str]:
        script, variables = self.lists()
        return unlisted(scripts, project, script, variables)

    def findings(self, project: Path, scripts: list[Path]) -> list[str]:
        return [found for found in self.raw(project, scripts) if found not in EXPLAINED]

    def test_every_script_the_gate_runs_reads_nothing_the_lists_lack_in_every_shape(self) -> None:
        """The sweep: each shape's derived scripts against both lists; a launched non-Python file is named."""
        fired: set[str] = set()
        for shape in SHAPES:
            with self.subTest(shape=shape[0]):
                project = self.project(shape)
                scripts, others = gate_scripts(project)
                fired.update(self.raw(project, scripts))
                self.assertGreater(len(scripts), 10, "the derivation found almost nothing")
                self.assertEqual(sorted(others - set(NOT_SCANNED)), [], "a launched file the scan cannot read, unnamed")
                self.assertEqual(self.findings(project, scripts), [])
        self.assertEqual(sorted(set(EXPLAINED) - fired), [], "a reason for a read no script makes any more")

    def test_the_scan_reaches_what_the_gate_runs_beyond_the_check_scripts(self) -> None:
        """The derivation holds the scripts the evidence names: recipe-launched, imported, and loaded by file name."""
        project = self.project(SHAPES[1])
        names = {path.relative_to(project).as_posix() for path in gate_scripts(project)[0]}
        for expected in ("scripts/event-model/check.py", "scripts/check-styles.py",
                         "scripts/extensions/project.py", "scripts/agents/project.py", "scripts/agents/code_index.py",
                         "scripts/test_benchmark.py", "scripts/extensions/uipro/init.py", "scripts/agents/models.py"):
            self.assertIn(expected, names)
        self.assertNotIn(THE_STAMP, names)
        cloud = self.project(SHAPES[2])
        aws = {path.relative_to(cloud).as_posix() for path in gate_scripts(cloud)[0]}
        self.assertIn("scripts/check-flags.py", aws)
        self.assertIn("scripts/check-deploy-role.py", aws)

    def test_a_read_planted_in_each_script_the_gate_runs_fails_the_scan(self) -> None:
        """T017 (b): an environment read and a read of an ignored path off the lists, appended to each derived script of
        each shape, are both found there and nowhere else."""
        planted = '\nimport os\nos.environ.get("A_NEW_SWITCH")\nopen(".specify-tools/state.json")\n'
        for shape in SHAPES:
            project = self.project(shape)
            scripts, _ = gate_scripts(project)
            for path in scripts:
                label = path.relative_to(project).as_posix()
                with self.subTest(shape=shape[0], script=label):
                    original = path.read_text(encoding="utf-8")
                    path.write_text(original + planted, encoding="utf-8")
                    try:
                        found = self.findings(project, [path])
                    finally:
                        path.write_text(original, encoding="utf-8")
                    self.assertEqual(found, [
                        READ.format(label=label, literal=".specify-tools/state.json"),
                        f"{label}: reads the variable A_NEW_SWITCH, which is on neither list",
                    ])

    def test_a_script_added_to_a_recipe_the_gate_runs_is_scanned(self) -> None:
        """Derived, not named: a new check, wired in by one line, and the module it imports."""
        project = self.project(SHAPES[0])
        makefile = project / "Makefile"
        original = makefile.read_text(encoding="utf-8")
        (project / "scripts" / "check-new-thing.py").write_text("import helper_for_it\n", encoding="utf-8")
        (project / "scripts" / "helper_for_it.py").write_text("x = 1\n", encoding="utf-8")
        makefile.write_text(original + "\nverify-checks: check-new-thing\ncheck-new-thing:\n"
                            "\tpython3 scripts/check-new-thing.py\n", encoding="utf-8")
        try:
            names = {path.name for path in gate_scripts(project)[0]}
        finally:
            makefile.write_text(original, encoding="utf-8")
            (project / "scripts" / "check-new-thing.py").unlink()
            (project / "scripts" / "helper_for_it.py").unlink()
        self.assertLessEqual({"check-new-thing.py", "helper_for_it.py"}, names)

    def generated_lines(self) -> list[str]:
        """The lines of each shape's `.gitignore`, and the extensions' (which every project carries)."""
        seen: set[str] = set()
        for shape in SHAPES:
            seen.update(ignored_patterns((self.project(shape) / ".gitignore").read_text(encoding="utf-8")))
        return sorted(seen)

    def moves_the_key(self, probe: str) -> bool:
        """Whether an ignored file at `probe` moves the key of a copy of the fixture project."""
        scratch = Path(tempfile.mkdtemp(prefix="stamp-line-"))
        self.addCleanup(shutil.rmtree, scratch, ignore_errors=True)
        repo = scratch / "project"
        shutil.copytree(template(), repo, symlinks=True)
        exclude(repo, probe)
        before = key_of(repo)
        (repo / probe).parent.mkdir(parents=True, exist_ok=True)
        (repo / probe).write_text("one\n", encoding="utf-8")
        return key_of(repo) != before

    def test_every_ignore_line_a_project_can_get_is_left_out_with_a_reason_or_is_in_the_key(self) -> None:
        """AC-S03-32, direction one: a line's own path is either under an exempt entry, which has one of the three
        reasons, or a file there moves the key."""
        script, _ = self.lists()
        lines = self.generated_lines()
        self.assertGreater(len(lines), 40)
        for line in lines:
            with self.subTest(line=line):
                probe = probe_path(line)
                entry = script.exempt_entry(probe)
                if entry is not None:
                    self.assertIn(entry[1], script.REASONS, f"{line}: {entry[0]} has no reason")
                    self.assertFalse(self.moves_the_key(probe), f"{probe} is exempt by {entry[0]} and moved the key")
                else:
                    self.assertTrue(self.moves_the_key(probe), f"{probe} is covered and did not move the key")

    def test_every_exempt_entry_is_an_ignore_line_a_project_gets_or_names_why_not(self) -> None:
        """AC-S03-32, direction two: nothing is left out of the key that no project's ignore lines mention, unless
        the table above names the tool that writes it; and that table holds no entry the list lost."""
        script, _ = self.lists()
        scratch = Path(tempfile.mkdtemp(prefix="stamp-lines-"))
        self.addCleanup(shutil.rmtree, scratch, ignore_errors=True)
        subprocess.run(["git", "init", "-q", str(scratch)], check=True)
        (scratch / ".gitignore").write_text("".join(line + "\n" for line in self.generated_lines()), encoding="utf-8")
        unmatched = set()
        for entry, _, _ in script.EXEMPT:
            probes = [probe_path(entry, under) for under in PLACES]
            ignored = [subprocess.run(["git", "check-ignore", "-q", "--", probe], cwd=scratch, check=False)
                       .returncode == 0 for probe in probes]
            if not any(ignored):
                unmatched.add(entry)
        self.assertEqual(sorted(unmatched), sorted(NOT_GENERATED))
