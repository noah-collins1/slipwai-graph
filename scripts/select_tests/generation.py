"""What a declared module's source does to generate a project, read statically (S38 T038, D164).

A declaration is a claim; this is the part of the claim the source can be held to. Every `generate(` call in a module
or in a helper it imports is bound to `FactoryTestCase.generate`'s signature (read by `ast` from `tests/support.py`)
and resolved per axis: a literal, or a loop over a literal sequence, to its values; anything else to *every option of
the axis*, so that a doubt fits only a declaration that leaves the axis unnamed or names it whole. A route to a
generated project the signature does not describe (`refuse(`, the launcher, `slipwai.cli`) is every option of every
axis. A module that generates and reaches into the repository in-process (`ROOT`, `__file__`, `.load(`, `importlib`,
`runpy`, `exec`, `sys.path`) is held to `reads` naming the target; so is one that hands on a string literal naming an
existing top-level path of the repository (`Path("AGENTS.md")`: the tests run at its root). The problem found voids
the declaration.
"""
from __future__ import annotations

import ast
import functools
import subprocess
import sys
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import NamedTuple

sys.dont_write_bytecode = True

SEAM_CLASS = "FactoryTestCase"
SEAM_METHOD = "generate"
# the parameter of `generate` (or the keyword its `**axes` takes) that answers a declaration's axis
AXIS_OF = {"profile": "profile", "language": "backend", "backend": "backend", "frontend": "frontend",
           "target": "target"}
LOADERS_THAT_ARE_NOT = ("json", "tomllib", "tomli", "yaml", "pickle", "marshal")
MODULES_THAT_REACH = ("importlib", "runpy")


class Signature(NamedTuple):
    """`generate`'s parameters after `self`, each with its literal default, and whether it takes `**axes`."""

    parameters: tuple[tuple[str, str | None], ...]
    keywords: bool


class Call(NamedTuple):
    line: int
    axes: Mapping[str, frozenset[str] | None]  # None: computed, so every option of the axis


class Reach(NamedTuple):
    line: int
    what: str
    literal: str | None  # the path the reach names, where it names one by a literal


class Facts(NamedTuple):
    calls: tuple[Call, ...] = ()
    routes: tuple[tuple[int, str], ...] = ()
    reaches: tuple[Reach, ...] = ()


@functools.lru_cache(maxsize=8)
def signature(root: Path) -> Signature | None:
    """`FactoryTestCase.generate`'s signature as `tests/support.py` writes it; None where it cannot be read."""
    try:
        module = ast.parse((root / "tests" / "support.py").read_text(encoding="utf-8"))
    except (OSError, SyntaxError, ValueError, RecursionError):
        return None
    for node in ast.walk(module):
        if isinstance(node, ast.ClassDef) and node.name == SEAM_CLASS:
            for method in node.body:
                if isinstance(method, ast.FunctionDef) and method.name == SEAM_METHOD:
                    args = method.args
                    plain = [*args.posonlyargs, *args.args][1:]
                    defaults: list[ast.expr | None] = [None] * (len(plain) - len(args.defaults)) + list(args.defaults)
                    return Signature(tuple((arg.arg, str(d.value) if isinstance(d, ast.Constant)
                                            and isinstance(d.value, str) else None)
                                           for arg, d in zip(plain, defaults, strict=True)), args.kwarg is not None)
    return None


def defines_seam(module: ast.Module) -> bool:
    return any(isinstance(node, ast.ClassDef) and node.name == SEAM_CLASS for node in module.body)


def parents_of(module: ast.Module) -> dict[int, ast.AST]:
    return {id(child): node for node in ast.walk(module) for child in ast.iter_child_nodes(node)}


def sequence(node: ast.expr) -> list[ast.expr] | None:
    return list(node.elts) if isinstance(node, ast.Tuple | ast.List) else None


def from_loop(name: str, target: ast.expr, iterator: ast.expr) -> frozenset[str] | None:
    """The values `name` takes in `for target in iterator` where the iterator is a literal sequence."""
    rows = sequence(iterator)
    if rows is None:
        return None
    if isinstance(target, ast.Name):
        found = [row.value for row in rows if isinstance(row, ast.Constant) and isinstance(row.value, str)]
        return frozenset(found) if target.id == name and len(found) == len(rows) else None
    if isinstance(target, ast.Tuple):
        for index, part in enumerate(target.elts):
            if isinstance(part, ast.Name) and part.id == name:
                cells = [sequence(row) for row in rows]
                values = [cell[index] for cell in cells if cell is not None and len(cell) > index]
                if len(values) == len(rows) and all(isinstance(v, ast.Constant) and isinstance(v.value, str)
                                                    for v in values):
                    return frozenset(str(v.value) for v in values if isinstance(v, ast.Constant))
    return None


def resolve(expression: ast.expr, parents: Mapping[int, ast.AST], module: ast.Module) -> frozenset[str] | None:
    """The values an argument takes, or None where they cannot be told."""
    if isinstance(expression, ast.Constant):
        return frozenset({expression.value}) if isinstance(expression.value, str) else None
    if isinstance(expression, ast.IfExp):
        one, other = resolve(expression.body, parents, module), resolve(expression.orelse, parents, module)
        return None if one is None or other is None else one | other
    if not isinstance(expression, ast.Name):
        return None
    node: ast.AST | None = parents.get(id(expression))
    while node is not None:
        loops = [(node.target, node.iter)] if isinstance(node, ast.For) else (
            [(g.target, g.iter) for g in node.generators]
            if isinstance(node, ast.ListComp | ast.SetComp | ast.GeneratorExp | ast.DictComp) else [])
        for target, iterator in loops:
            if (found := from_loop(expression.id, target, iterator)) is not None:
                return found
        node = parents.get(id(node))
    assigned = [n for n in ast.walk(module) if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == expression.id for t in n.targets)]
    if len(assigned) == 1 and isinstance(assigned[0].value, ast.Constant) and isinstance(assigned[0].value.value, str):
        return frozenset({assigned[0].value.value})
    return None


def bind(call: ast.Call, shape: Signature | None, parents: Mapping[int, ast.AST],
         module: ast.Module) -> Mapping[str, frozenset[str] | None]:
    """Each axis a call answers, by position and by keyword, with the signature's default for one it omits."""
    axes: dict[str, frozenset[str] | None] = {axis: None for axis in set(AXIS_OF.values())}
    if shape is None or any(isinstance(arg, ast.Starred) for arg in call.args) or any(
            kw.arg is None for kw in call.keywords):
        return axes
    given: dict[str, ast.expr] = {}
    for (name, _), arg in zip(shape.parameters, call.args, strict=False):
        given[name] = arg
    for keyword in call.keywords:
        if keyword.arg is not None:
            given[keyword.arg] = keyword.value
    for name, default in shape.parameters:
        if name in AXIS_OF:
            axes[AXIS_OF[name]] = (resolve(given[name], parents, module) if name in given
                                   else (None if default is None else frozenset({default})))
    for name, value in given.items():
        if name in AXIS_OF and name not in dict(shape.parameters):
            axes[AXIS_OF[name]] = resolve(value, parents, module)
    return axes


def called(node: ast.Call) -> str:
    function = node.func
    return function.attr if isinstance(function, ast.Attribute) else getattr(function, "id", "")


def literal_after(node: ast.AST, parents: Mapping[int, ast.AST]) -> str | None:
    """The literal path a `ROOT / "a" / "b"` chain names, or None where a part is not a literal."""
    parts: list[str] = []
    while isinstance(parent := parents.get(id(node)), ast.BinOp) and isinstance(parent.op, ast.Div) \
            and parent.left is node:
        if not (isinstance(parent.right, ast.Constant) and isinstance(parent.right.value, str)):
            return "/".join(parts).strip("/") or None
        parts.append(parent.right.value)
        node = parent
    return "/".join(parts).strip("/") or None


def names_a_path(value: str, root: Path | None) -> bool:
    """Whether a string literal names an existing top-level path of the repository, or a path under one: the tests run
    at the root, so `Path("AGENTS.md")` and `["python3", "scripts/x.py"]` reach it with no `ROOT` (T053)."""
    if root is None or not value or value.startswith("/") or any(c in value for c in "\n\0") or len(value) > 200:
        return False
    if {*value.split("/")} & {"..", ".", ""}:
        return False
    seen = paths_git_sees(root)
    return value in seen if seen is not None else (root / value).exists()


@functools.cache
def paths_git_sees(root: Path) -> frozenset[str] | None:
    """Every path git tracks or would add under `root`, with every directory above one; None where git cannot say. What
    git ignores (`build/`, where `make starters` ran) is on disk in one checkout and not another, so it holds no
    declaration and voids none."""
    try:
        done = subprocess.run(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=root,
                              capture_output=True, timeout=60, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if done.returncode != 0:
        return None
    seen: set[str] = set()
    for path in done.stdout.decode("utf-8", "surrogateescape").split("\0"):
        parts = path.split("/")
        seen.update("/".join(parts[:end]) for end in range(1, len(parts) + 1) if path)
    return frozenset(seen)


def anchored_elsewhere(node: ast.AST, parents: Mapping[int, ast.AST]) -> bool:
    """A literal that is not a path handed to something: the operand of a comparison, an index, a key, or what a
    `base / "name"` is joined to a base other than the repository (`ROOT` reports its own chain)."""
    parent = parents.get(id(node))
    if isinstance(parent, ast.Compare | ast.Subscript) or (isinstance(parent, ast.Dict) and node in parent.keys):
        return True
    if isinstance(parent, ast.BinOp) and isinstance(parent.op, ast.Div) and parent.right is node:
        return True
    return in_root_chain(node, parents)


def in_root_chain(node: ast.AST, parents: Mapping[int, ast.AST]) -> bool:
    """Whether a node is a part of a `ROOT / "a" / "b"` chain, which `ROOT` reports with its literal."""
    while isinstance(parent := parents.get(id(node)), ast.BinOp) and isinstance(parent.op, ast.Div):
        node = parent
    while isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        node = node.left
    return isinstance(node, ast.Name) and node.id == "ROOT"


def facts(module: ast.Module, shape: Signature | None, trusted: bool, launcher: Callable[[ast.AST], bool],
          root: Path | None = None) -> Facts:
    """Every call, route and reach in the file. The file that defines the seam is trusted with its own launcher and
    `ROOT`: it is what the calls are bound to."""
    parents = parents_of(module)
    calls: list[Call] = []
    routes: list[tuple[int, str]] = []
    reaches: list[Reach] = []
    for node in ast.walk(module):
        line = getattr(node, "lineno", 0)
        if isinstance(node, ast.Call):
            name = called(node)
            if name == SEAM_METHOD:
                calls.append(Call(line, bind(node, shape, parents, module)))
            if name == "refuse" and not trusted:
                routes.append((line, "refuse("))
            if name == "exec" and not trusted:
                reaches.append(Reach(line, "exec(", None))
            if name == "load" and isinstance(node.func, ast.Attribute) and not trusted and not (
                    isinstance(node.func.value, ast.Name) and node.func.value.id in LOADERS_THAT_ARE_NOT):
                first = node.args[0] if node.args else None
                reaches.append(Reach(line, ".load(", str(first.value) if isinstance(first, ast.Constant)
                                     and isinstance(first.value, str) else None))
        if trusted:
            continue
        if launcher(node):
            routes.append((line, "the launcher or `slipwai.cli`"))
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and names_a_path(node.value, root) \
                and not anchored_elsewhere(node, parents):
            reaches.append(Reach(line, "the path literal", node.value))
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            parent = parents.get(id(node))
            if node.id == "ROOT" and not (isinstance(parent, ast.BinOp) and isinstance(parent.op, ast.Div)
                                          and parent.left is node and isinstance(parent.right, ast.Constant)
                                          and parent.right.value == "slipwai"):
                reaches.append(Reach(line, "ROOT", literal_after(node, parents)))
            elif node.id == "__file__":
                reaches.append(Reach(line, "__file__", None))
            elif node.id in MODULES_THAT_REACH:
                reaches.append(Reach(line, node.id, None))
        elif isinstance(node, ast.Attribute) and node.attr == "path" and isinstance(node.value, ast.Name) \
                and node.value.id == "sys":
            reaches.append(Reach(line, "sys.path", None))
        elif (isinstance(node, ast.Import) and any(a.name.split(".")[0] in MODULES_THAT_REACH for a in node.names)) or (
                isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] in MODULES_THAT_REACH):
            reaches.append(Reach(line, "importlib or runpy", None))
    return Facts(tuple(calls), tuple(routes), tuple(reaches))


def names(entry: str, reads: frozenset[str], by_name: bool = False) -> bool:
    """Whether a `reads` entry names the literal path, as the path or the directory above it; a bare-name `.load(` is
    also held by the entry that ends in the name, as the selector matches a path and not a suffix (T054)."""
    return any(entry == read or entry.startswith(read + "/") or (by_name and read.endswith("/" + entry))
               for read in reads)


def problem(member: str, found: Facts, axes: Mapping[str, frozenset[str]], every: bool, reads: frozenset[str],
            options: Callable[[str], frozenset[str]]) -> str:
    """Why a file's source is not what the declaration it runs under says, or empty."""
    where = f"`tests/{member}.py`"
    for line, route in found.routes:
        if not every:
            return (f"{where} line {line} generates through {route}, which is every option of every axis, "
                    'and the declaration is not "every"')
    for call in found.calls:
        if every:
            break
        for axis, declared in sorted(axes.items()):
            values = call.axes.get(axis, None) if axis in call.axes else None
            if axis == "command":
                if "generate" not in declared:
                    return f"{where} line {call.line} calls generate, which the declared commands lack"
                continue
            if axis not in call.axes:
                continue
            if values is None:
                if not options(axis) <= declared:
                    return (f"{where} line {call.line} passes a computed {axis}, which is every option, "
                            f"and the declaration narrows it to {', '.join(sorted(declared))}")
            elif not values <= declared:
                lacking = ", ".join(sorted(values - declared))
                return f"{where} line {call.line} generates the {axis} {lacking}, which its declaration lacks"
    for reach in found.reaches:
        if reach.literal is None or not names(reach.literal, reads,
                                              reach.what == ".load(" and "/" not in reach.literal):
            said = f" `{reach.literal}`" if reach.literal else ""
            return (f"{where} line {reach.line} reaches the repository in-process ({reach.what}{said}) and `reads` "
                    "does not name it")
    return ""
