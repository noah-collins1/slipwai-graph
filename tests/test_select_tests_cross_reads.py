"""A directory is read by more than its name suggests (S38 R5 second half, research R-5, AC-S38-8).

The three cross-reads research R-5 found are held in a fixture; the scan holds the map to the generator the run
executes: every reference in `src/slipwai/` to an asset root names a directory the map attributes to the
configuration that holds it, or the test fails naming the reference. `src/slipwai/` never changes in a selected run (a
change there is full), so what the scan reads is what a selected run's generator reads.
"""
from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
from typing import NamedTuple

from select_fixture import SelectCase
from select_fixture_declare import DeclarationCase

from slipwai.assets import ROOT

sys.dont_write_bytecode = True

SRC = ROOT / "src" / "slipwai"
CLAIMS = ("import sys\nfrom pathlib import Path\nfrom select_tests import rules\n"
          "catalog = rules.load_catalog(Path('.').resolve())\n"
          "found = {}\n"
          "for path in json.load(sys.stdin):\n"
          "    claim = rules.claim(path, catalog)\n"
          "    found[path] = None if claim is None else [claim.full, claim.every, sorted(claim.configs)]\n"
          "print(json.dumps(found))\n")
# What each source file serves, where it serves one configuration: the `(axis, option)` pairs a change to an asset it
# reads has to reach. A file not named here reads assets every configuration shares, or is the pruner's.
SERVES = {
    "project/languages/go.py": {("backend", "go")},
    "project/languages/python.py": {("backend", "python")},
    "project/languages/typescript.py": {("backend", "typescript")},
    "project/mutmut.py": {("backend", "python")},
    "project/stryker.py": {("backend", "typescript")},
    "project/languages/java_quarkus.py": {("backend", "java-quarkus")},
    "project/languages/java_spring.py": {("backend", "java-spring")},
    "project/frontend.py": {("frontend", "react-vite")},
    "project/biome.py": {("backend", "typescript"), ("frontend", "react-vite")},
    "wrappers.py": {("command", "adopt")},
    "platform.py": {("command", "adopt")},
    "scaffold.py": {("command", "adopt")},
    "project/strangle_command.py": {("command", "adopt")},
    # `speakers_of` gives a project with no service of the factory's the TypeScript speaker, and `snippet` reads its
    # `examples/` through the f-string below
    "examples.py": {("command", "adopt")},
}
ASSET_STRING = re.compile(r"assets/(languages|backing-services|frontends|profiles|targets|toolkit|adoption)/([\w.-]+)")


class TestTheCrossReads(DeclarationCase):
    def test_the_biome_files_reach_the_browser_app_too(self) -> None:
        self.declare(test_a='{"configurations": {"frontend": ["react-vite"]}}',
                     test_b='{"configurations": {"backend": ["python"], "frontend": ["none"]}}',
                     test_c='{"configurations": {"backend": ["go"], "frontend": ["none"]}}')
        self.commit("declarations")
        for number, path in enumerate(("assets/languages/typescript/biome/biome.jsonc",
                                       "assets/languages/typescript/app/package.json")):
            with self.subTest(path=path):
                self.branch("main")
                self.branch(f"slice/{number}")
                self.write(path, "{}\n")
                ran, skipped = self.selected()
                self.assertEqual(ran, ["test_a"])
                self.assertEqual(skipped, ["skipped test_b: reads no typescript, react-vite configuration",
                                           "skipped test_c: reads no typescript, react-vite configuration"])

    def test_the_browser_apps_manifest_reaches_the_typescript_backend_that_pins_biome_from_it(self) -> None:
        self.declare(test_a='{"configurations": {"backend": ["typescript"], "frontend": ["none"]}}',
                     test_b='{"configurations": {"backend": ["go"], "frontend": ["none"]}}')
        self.slice_changing("assets/frontends/react-vite/app/package.json")
        self.assertEqual(self.selected()[0], ["test_a"])

    def test_the_java_build_reaches_adoption_which_wraps_it(self) -> None:
        self.declare(test_a='{"configurations": {"command": ["adopt"]}}',
                     test_b='{"configurations": {"command": ["generate"], "backend": ["go"]}}',
                     test_c='{"configurations": {"backend": ["java-spring"]}}')
        self.slice_changing("assets/languages/java/build/pom.xml")
        ran, skipped = self.selected()
        self.assertEqual(ran, ["test_a", "test_c"])
        self.assertEqual(skipped, ["skipped test_b: reads no java-quarkus, java-spring, adopt configuration"])

    def test_the_typescript_examples_reach_adoption_which_falls_back_to_them(self) -> None:
        self.declare(test_a='{"configurations": {"command": ["adopt"]}}',
                     test_b='{"configurations": {"command": ["generate"], "backend": ["go"]}}')
        self.slice_changing("assets/languages/typescript/examples/tdd/x.md")
        self.assertEqual(self.selected()[0], ["test_a"])


def references() -> list[tuple[str, int, str, str, str]]:
    """Every reference to an asset root in `src/slipwai/`: file, line, the asset tree, what is known of the path under
    it (up to the first part computed at run time) and `dynamic` where something computed follows."""
    roots: dict[str, str] = {}
    found: list[tuple[str, int, str, str, str]] = []
    for statement in ast.parse((SRC / "assets.py").read_text(encoding="utf-8")).body:
        value = statement.value if isinstance(statement, ast.Assign) else None
        if isinstance(value, ast.BinOp) and isinstance(value.right, ast.Constant):
            name = statement.targets[0].id if isinstance(statement.targets[0], ast.Name) else ""  # type: ignore[attr-defined]
            if name.endswith("_ROOT") and name != "ROOT":
                roots[name] = str(value.right.value).removeprefix("assets/")
    for file in sorted(SRC.rglob("*.py")):
        shown = file.relative_to(SRC).as_posix()
        aliases = dict(roots)
        for node in ast.walk(ast.parse(file.read_text(encoding="utf-8"))):
            if not (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div)):
                continue
            operands = []
            walker: ast.expr = node
            while isinstance(walker, ast.BinOp) and isinstance(walker.op, ast.Div):
                operands.append(walker.right)
                walker = walker.left
            operands.append(walker)
            operands.reverse()
            head = operands[0]
            if isinstance(head, ast.Name) and head.id in aliases and not isinstance(node.left, ast.BinOp):
                tree, rest = aliases[head.id], operands[1:]
            elif (isinstance(head, ast.Name) and head.id == "ROOT" and len(operands) > 1
                  and isinstance(operands[1], ast.Constant) and str(operands[1].value).startswith("assets/")):
                tree, rest = str(operands[1].value).removeprefix("assets/"), operands[2:]
            else:
                continue
            known, dynamic = [], ""
            for part in rest:
                if isinstance(part, ast.Constant) and isinstance(part.value, str):
                    known.append(part.value)
                    continue
                if isinstance(part, ast.JoinedStr) and part.values and isinstance(part.values[0], ast.Constant):
                    known.append(str(part.values[0].value))
                dynamic = "yes"
                break
            found.append((shown, node.lineno, tree, "/".join(known), dynamic))
        found.extend(fstring_references(shown, ast.parse(file.read_text(encoding="utf-8"))))
    return found


def fstring_references(shown: str, module: ast.Module) -> list[tuple[str, int, str, str, str]]:
    """A path written as `f"assets/languages/{owner}/{name}"`, where `name` is a variable the file gives an f-string
    that opens with a directory (`f"examples/..."`): read for the owner the TypeScript fallback names, the one a
    project with no service of the factory's is given (`speakers_of`)."""
    openings = {target.id: str(node.value.values[0].value).rstrip("/")
                for node in ast.walk(module) if isinstance(node, ast.Assign) and isinstance(node.value, ast.JoinedStr)
                and node.value.values and isinstance(node.value.values[0], ast.Constant)
                for target in node.targets if isinstance(target, ast.Name)}
    found: list[tuple[str, int, str, str, str]] = []
    for node in ast.walk(module):
        if not (isinstance(node, ast.JoinedStr) and len(node.values) == 4 and isinstance(node.values[0], ast.Constant)
                and str(node.values[0].value) == "assets/languages/"):
            continue
        tail = node.values[3]
        if isinstance(tail, ast.FormattedValue) and isinstance(tail.value, ast.Name) and tail.value.id in openings:
            found.append((shown, node.lineno, "languages", f"typescript/{openings[tail.value.id]}", "yes"))
    return found


def synthetic(tree: str, known: str) -> str:
    """A path the reference reaches: the file it names, or a file inside the directory it names."""
    if "." in known.rsplit("/", 1)[-1]:
        return f"assets/{tree}/{known}"
    return f"assets/{tree}/{known.rstrip('/')}/x"


class Seen(NamedTuple):
    """What the map says of a path: whether it is full, reaches every configuration, or the pairs it names."""

    full: bool
    every: bool
    configs: frozenset[tuple[str, str]]


def claims(paths: list[str]) -> dict[str, Seen | None]:
    code = "import json\nsys = __import__('sys')\nsys.path.insert(0, 'scripts')\n" + CLAIMS
    done = subprocess.run(["python3", "-B", "-c", code], cwd=ROOT, input=json.dumps(paths), text=True,
                          capture_output=True, timeout=180)
    assert done.returncode == 0, done.stderr
    said: dict[str, list[object] | None] = json.loads(done.stdout)
    return {path: None if row is None else Seen(bool(row[0]), bool(row[1]), frozenset(
        (pair[0], pair[1]) for pair in row[2]))  # type: ignore[attr-defined]
        for path, row in said.items()}


class TestTheScan(SelectCase):
    modules = ()

    def test_every_reference_to_an_asset_root_names_a_directory_the_map_attributes_to_its_holder(self) -> None:
        found = references()
        self.assertGreater(len(found), 40, "the scan found the references it should")
        checked = [(shown, line, synthetic(tree, known)) for shown, line, tree, known, _ in found if known]
        mapped = claims([path for _, _, path in checked])
        wrong = []
        for shown, line, path in checked:
            found_claim = mapped[path]
            serves = SERVES.get(shown)
            if found_claim is None:
                wrong.append(f"src/slipwai/{shown}:{line} reads `{path}`, which no rule claims")
            elif found_claim.full or found_claim.every:
                continue
            elif serves is None:
                wrong.append(f"src/slipwai/{shown}:{line} reads `{path}`, which only {sorted(found_claim.configs)} "
                             "reach — name the configuration this file serves in SERVES")
            elif not serves <= found_claim.configs:
                wrong.append(f"src/slipwai/{shown}:{line} reads `{path}`, which {sorted(found_claim.configs)} reach; "
                             f"{sorted(serves)} read it")
        self.assertEqual(wrong, [])

    def test_every_flag_reader_tree_is_the_backends_own_or_its_familys(self) -> None:
        table = next(node for node in ast.parse((SRC / "project/flags.py").read_text(encoding="utf-8")).body
                     if isinstance(node, ast.AnnAssign) and getattr(node.target, "id", "") == "FLAG_READERS")
        assert isinstance(table.value, ast.Dict)
        trees = {ast.literal_eval(key): next(kw.value for kw in value.keywords if kw.arg == "tree")  # type: ignore[attr-defined]
                 for key, value in zip(table.value.keys, table.value.values, strict=True) if key is not None}
        paths = {backend: f"assets/languages/{ast.literal_eval(tree)}/x" for backend, tree in trees.items()}
        mapped = claims(list(paths.values()))
        self.assertEqual(len(paths), 5)
        for backend, path in paths.items():
            with self.subTest(backend=backend):
                found_claim = mapped[path]
                assert found_claim is not None
                self.assertIn(("backend", backend), found_claim.configs)

    def test_every_backing_service_directory_is_claimed_and_the_pruners_languages_are_backends(self) -> None:
        entries = (ROOT / "assets/backing-services").iterdir()
        listed = sorted(path.name for path in entries if path.name != "__pycache__")
        paths = [f"assets/backing-services/{name}" + ("" if "." in name else "/x") for name in listed]
        mapped = claims(paths)
        self.assertEqual([path for path in paths if mapped[path] is None], [])
        prune = ast.parse((ROOT / "assets/backing-services/prune.py").read_text(encoding="utf-8"))
        languages = next(ast.literal_eval(node.value) for node in prune.body
                         if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "LANGUAGES")
        owned = claims([f"assets/backing-services/{name}/x" for name in languages])
        for name in languages:
            with self.subTest(language=name):
                found_claim = owned[f"assets/backing-services/{name}/x"]
                assert found_claim is not None
                self.assertTrue(found_claim.configs, "a language the pruner knows is a backend or a family of backends")

    def test_a_literal_asset_path_in_the_generator_is_claimed(self) -> None:
        paths: dict[str, str] = {}
        for file in sorted(SRC.rglob("*.py")):
            module = ast.parse(file.read_text(encoding="utf-8"))
            documented = {id(node.body[0].value) for node in ast.walk(module)
                          if isinstance(node, ast.Module | ast.FunctionDef | ast.ClassDef) and node.body
                          and isinstance(node.body[0], ast.Expr)}
            for node in ast.walk(module):
                if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in documented:
                    for tree, name in ASSET_STRING.findall(node.value):
                        paths[f"assets/{tree}/{name}" + ("" if "." in name else "/x")] = f"{file.relative_to(ROOT)}"
        mapped = claims(list(paths))
        self.assertEqual({where: path for path, where in paths.items() if mapped[path] is None}, {})
