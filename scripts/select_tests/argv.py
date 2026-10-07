"""A literal `./slipwai generate` argv, read as the axes it generates (S43 T001, D187 rules 1-3).

`read` answers one `ast.List`: the axes of the project the argv generates, or None where the list is not an argv this
rule reads, and stays a route to every option of every axis. Only a fully literal argv handed straight to `subprocess`
is read: `ROOT / "slipwai"` (or `str(...)` of it), the literal `generate`, then string-literal flags and values, bar the
project name (computed only right after `generate`) and the value of `--output`, which select nothing. The CLI's own
defaults are not the seam's, so an omitted axis flag is every option.
"""
from __future__ import annotations

import ast
import functools
import json
import sys
from collections.abc import Mapping
from pathlib import Path

sys.dont_write_bytecode = True

LAUNCHER = "slipwai"
SUBCOMMAND = "generate"
# the flags that answer an axis a declaration can name
AXIS_FLAGS = {"--backend": "backend", "--profile": "profile", "--frontend": "frontend", "--target": "target"}
AXES = frozenset(AXIS_FLAGS.values())


@functools.lru_cache(maxsize=8)
def catalog_flags(root: Path) -> frozenset[str]:
    """`--<key>` for each key of the catalog's `axes` object: flags that take a literal and answer no declared axis."""
    try:
        axes = json.loads((root / "catalog.json").read_text(encoding="utf-8")).get("axes", {})
    except (OSError, ValueError, AttributeError):
        return frozenset()
    return frozenset(f"--{key}" for key in axes) if isinstance(axes, dict) else frozenset()


def literal(node: ast.expr) -> str | None:
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def launcher(node: ast.expr) -> ast.expr | None:
    """The `ROOT / "slipwai"` chain itself, which may be wrapped in `str(...)`; None for anything else."""
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "str" \
            and len(node.args) == 1 and not node.keywords:
        node = node.args[0]
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div) and isinstance(node.left, ast.Name) \
            and node.left.id == "ROOT" and literal(node.right) == LAUNCHER:
        return node
    return None


RUNNERS = frozenset({"run", "Popen", "call", "check_call", "check_output"})


def whole(node: ast.List, parent: ast.AST | None) -> bool:
    """Whether the list is the whole argv as written: the first argument of a `subprocess` call, and nothing else. A
    list anywhere else (joined, bound to a name, returned, held in another container, handed to a helper) may be
    changed before it runs, so it is not read (D187 rule 3)."""
    return isinstance(parent, ast.Call) and bool(parent.args) and parent.args[0] is node \
        and isinstance(parent.func, ast.Attribute) and parent.func.attr in RUNNERS \
        and isinstance(parent.func.value, ast.Name) and parent.func.value.id == "subprocess"


def read(node: ast.AST, root: Path | None,
         parent: ast.AST | None = None) -> tuple[Mapping[str, frozenset[str] | None], ast.expr] | None:
    """The axes a literal launcher argv generates, with the launcher node inside it; None where it is not read."""
    if not isinstance(node, ast.List) or len(node.elts) < 2 or any(isinstance(e, ast.Starred) for e in node.elts):
        return None
    if not whole(node, parent):
        return None
    chain = launcher(node.elts[0])
    if chain is None or literal(node.elts[1]) != SUBCOMMAND:
        return None
    known = catalog_flags(root) if root is not None else frozenset()
    given: dict[str, str] = {}
    seen: set[str] = set()
    positional = 0
    rest = node.elts[2:]
    index = 0
    while index < len(rest):
        flag = literal(rest[index])
        if flag is None or not flag.startswith("--"):
            if flag is None and index != 0:
                return None  # a computed name is read only right after `generate`: later, it may be a flag
            positional += 1  # the project's name, selecting nothing
            index += 1
            continue
        if flag in seen:
            return None
        seen.add(flag)
        if flag == "--skip-checks":
            index += 1
            continue
        if flag not in AXIS_FLAGS and flag not in known and flag != "--output":
            return None
        if index + 1 >= len(rest):
            return None
        value = literal(rest[index + 1])
        if flag != "--output" and value is None:
            return None
        if flag in AXIS_FLAGS and value is not None:
            given[AXIS_FLAGS[flag]] = value
        index += 2
    if positional > 1:
        return None
    return {axis: (frozenset({given[axis]}) if axis in given else None) for axis in sorted(AXES)}, chain
