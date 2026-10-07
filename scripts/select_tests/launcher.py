"""Whether a node runs the launcher or the command module (S43 T002b, D187 rule 3).

Every form that starts `slipwai` is a route to every option of every axis unless `argv` reads it: a path to the
launcher (`"./slipwai"`, `ROOT / "slipwai"`), the launcher on `PATH`, `python -m slipwai`, an import of `slipwai.cli`,
and a command given as a string (`shlex.split("./slipwai generate ...")`, `run("./slipwai ...", shell=True)`, the
constant parts of an f-string). A string that is a docstring or a bare expression statement is prose, not a command.
"""
from __future__ import annotations

import ast
import sys
from collections.abc import Callable

sys.dont_write_bytecode = True

LAUNCHER = "slipwai"
COMMAND_MODULE = "slipwai.cli"


def is_path(word: str) -> bool:
    parts = word.split("/")
    return len(parts) > 1 and parts[-1] == LAUNCHER and parts[0] in (".", "..", "")


def is_module(word: str) -> bool:
    return word == LAUNCHER or word.startswith(LAUNCHER + ".")


def dash_m(words: list[str]) -> bool:
    return any(a == "-m" and is_module(b) for a, b in zip(words, words[1:], strict=False))


def string_names(value: str) -> bool:
    words = value.split()
    return any(is_path(word) for word in words) or dash_m(words)


def detector(tree: ast.AST) -> Callable[[ast.AST], bool]:
    """`names_launcher` for the nodes of `tree`, which knows which strings are bare statements (prose)."""
    prose = {id(node.value) for node in ast.walk(tree) if isinstance(node, ast.Expr)}

    def names_launcher(node: ast.AST) -> bool:
        if isinstance(node, ast.Constant):
            return isinstance(node.value, str) and id(node) not in prose and string_names(node.value)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            return isinstance(node.right, ast.Constant) and node.right.value == LAUNCHER
        if isinstance(node, ast.List):  # `["slipwai", "generate", ...]`, `["python3", "-m", "slipwai", ...]`
            values = [e.value if isinstance(e, ast.Constant) else None for e in node.elts]
            return values[:1] == [LAUNCHER] or any(
                a == "-m" and isinstance(b, str) and is_module(b) for a, b in zip(values, values[1:], strict=False))
        if isinstance(node, ast.Import):
            return any(alias.name == COMMAND_MODULE or alias.name.startswith(COMMAND_MODULE + ".")
                       for alias in node.names)
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            return node.level == 0 and (module == COMMAND_MODULE or module.startswith(COMMAND_MODULE + ".")
                                        or (module == LAUNCHER and any(alias.name == "cli" for alias in node.names)))
        return False

    return names_launcher
