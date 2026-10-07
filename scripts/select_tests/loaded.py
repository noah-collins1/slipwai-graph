"""The asset paths `src/slipwai/` reads, found by scanning its source (S38 T037, AC-S38-10, AC-S38-16).

A module that imports `slipwai` runs the generator's import-time reads (`assets.py` loads a toolkit script by path)
and every read of a function it calls in process (the agent registry). The declaration cannot say which, so each
such module is taken to read every asset path the source names in full, a file or a directory. The paths are read,
not listed: a new read in `src/slipwai/` is a new entry.
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True

ASSETS = "assets/"
STRING = re.compile(r"assets/(?:languages|backing-services|frontends|profiles|targets|toolkit|adoption)/[\w./-]+")


def roots_of(module: ast.Module) -> dict[str, str]:
    """The names `assets.py` gives to an asset directory: `TOOLKIT_ROOT = ROOT / "assets/toolkit"`."""
    found: dict[str, str] = {}
    for statement in module.body:
        if not (isinstance(statement, ast.Assign) and len(statement.targets) == 1):
            continue
        name, value = statement.targets[0], statement.value
        if (isinstance(name, ast.Name) and name.id != "ROOT" and isinstance(value, ast.BinOp)
                and isinstance(value.op, ast.Div) and isinstance(value.left, ast.Name) and value.left.id == "ROOT"
                and isinstance(value.right, ast.Constant) and str(value.right.value).startswith(ASSETS)):
            found[name.id] = str(value.right.value)
    return found


def chain(node: ast.BinOp) -> tuple[ast.expr, list[ast.expr]]:
    """`a / b / c` as its head and the parts that follow."""
    parts: list[ast.expr] = []
    walker: ast.expr = node
    while isinstance(walker, ast.BinOp) and isinstance(walker.op, ast.Div):
        parts.append(walker.right)
        walker = walker.left
    return walker, parts[::-1]


def known(parts: list[ast.expr]) -> str:
    """The path the parts name, or none where any part is computed at run time: a tree walked by what is chosen at run
    time is the generating configuration's, which a rule already claims, and not a read a module makes in process."""
    kept: list[str] = []
    for part in parts:
        if not (isinstance(part, ast.Constant) and isinstance(part.value, str)):
            return ""
        kept.append(part.value)
    return "/".join(piece.strip("/") for piece in kept if piece.strip("/"))


def paths_in(module: ast.Module, roots: dict[str, str]) -> set[str]:
    found: set[str] = set()
    inner = {id(node.left) for node in ast.walk(module)
             if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div)}
    documented = {id(node.body[0].value) for node in ast.walk(module)
                  if isinstance(node, ast.Module | ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef)
                  and node.body and isinstance(node.body[0], ast.Expr)}
    for node in ast.walk(module):
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div) and id(node) not in inner:
            head, parts = chain(node)
            if isinstance(head, ast.Name) and head.id in roots:
                path = f"{roots[head.id]}/{known(parts)}"
            elif isinstance(head, ast.Name) and head.id == "ROOT":
                path = known(parts)
            else:
                continue
            path = path.strip("/")
            if path.startswith(ASSETS) and path.count("/") > 1:
                found.add(path)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in documented:
            found.update(match.rstrip("/.") for match in STRING.findall(node.value))
    return found


def scan(root: Path) -> frozenset[str]:
    """Every asset path read by `src/slipwai/` under `root`; none where there is no such package. A file that cannot be
    read stands for the whole of `assets/` (the doubt broadens)."""
    source = root / "src" / "slipwai"
    if not source.is_dir():
        return frozenset()
    files = sorted(source.rglob("*.py"))
    try:
        roots = roots_of(ast.parse((source / "assets.py").read_text(encoding="utf-8")))
    except (OSError, SyntaxError, ValueError):
        return frozenset({ASSETS})
    found: set[str] = set()
    for file in files:
        try:
            found |= paths_in(ast.parse(file.read_text(encoding="utf-8"), filename=str(file)), roots)
        except (OSError, SyntaxError, ValueError, RecursionError):
            return frozenset({ASSETS})
    return frozenset(found)
