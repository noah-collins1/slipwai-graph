"""The two scanners behind S33's class-closing tables: what `tests/*.py` read from the
environment, and look for on `PATH`.

A scanner that only sees literal forms goes green past a form it cannot read, so these fail the other way: every form
handled below is read, and any site whose name cannot be resolved to literal strings (a parameter, a computed value)
is returned as an `unreadable` entry, which the table test must account for by file and expression, with a reason.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

sys.dont_write_bytecode = True

TESTS_DIR = Path(__file__).resolve().parent
ENVIRONS = ("os.environ", "environ")
ENV_GETTERS = tuple(f"{o}.{m}" for o in ENVIRONS for m in ("get", "setdefault", "pop")) + ("os.getenv", "getenv")
WHICH = ("shutil.which", "which", "_on_path")
SPAWNS = ("run", "Popen", "call", "check_call", "check_output")


class Names:
    """Resolves an expression to the literal strings it can be, or None. A name is what the nearest enclosing `for` or
    comprehension over literals makes it, else what its one assignment in the file makes it; a parameter, a name bound
    twice or anything computed is None."""

    def __init__(self, tree: ast.AST) -> None:
        self.parents = {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
        self.assigned: dict[str, list[ast.AST]] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                self.assigned.setdefault(node.targets[0].id, []).append(node.value)

    def literals(self, node: ast.AST) -> set[str] | None:
        if isinstance(node, ast.Constant):
            return {node.value} if isinstance(node.value, str) else None
        if isinstance(node, ast.Tuple | ast.List):
            return self.each(node)
        if isinstance(node, ast.Name):
            loop = self.loop(node)
            if loop is not None:
                return self.each(loop)
            values = self.assigned.get(node.id, [])
            return self.literals(values[0]) if len(values) == 1 else None
        return None

    def each(self, node: ast.AST) -> set[str] | None:
        """The strings an iterable of literals holds."""
        if isinstance(node, ast.Name):
            values = self.assigned.get(node.id, [])
            return self.each(values[0]) if len(values) == 1 else None
        if not isinstance(node, ast.Tuple | ast.List):
            return None
        parts = [self.literals(e) for e in node.elts]
        return None if any(p is None for p in parts) else set().union(*parts)  # type: ignore[arg-type]

    def loop(self, name: ast.Name) -> ast.AST | None:
        """The iterable of the nearest enclosing `for` or comprehension that binds `name`, if there is one."""
        child: ast.AST = name
        while child in self.parents:
            parent = self.parents[child]
            binders = parent.generators if isinstance(parent, ast.ListComp | ast.SetComp | ast.GeneratorExp
                                                      | ast.DictComp) else [parent]
            for binder in binders:
                if isinstance(binder, ast.For | ast.comprehension) and isinstance(binder.target, ast.Name) \
                        and binder.target.id == name.id and child is not binder.iter:
                    return binder.iter
            child = parent
        return None


def sites(directory: Path) -> tuple[set[str], set[str], list[str]]:
    """The environment names read, the tools looked for, and each site whose name cannot be read as `file: code`."""
    env: set[str] = set()
    tools: set[str] = set()
    unreadable: list[str] = []
    for path in sorted(directory.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names = Names(tree)

        def take(into: set[str], node: ast.AST, whole: ast.AST, file: str = path.name, names: Names = names) -> None:
            found = names.literals(node)
            if found is None:
                unreadable.append(f"{file}: {ast.unparse(whole)}")
            else:
                into.update(found)

        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and node.args:
                function, first = ast.unparse(node.func), node.args[0]
                if function in ENV_GETTERS:
                    take(env, first, node)
                elif function in WHICH:
                    take(tools, first, node)
                elif function == "bare_path":
                    for argument in node.args[1:]:
                        take(tools, argument, node)
                elif function == "os.access" and len(node.args) > 1 and ast.unparse(node.args[1]) == "os.X_OK":
                    named = first.right if isinstance(first, ast.BinOp) and isinstance(first.op, ast.Div) else first
                    take(tools, named, node)
                elif function.split(".")[-1] in SPAWNS and isinstance(first, ast.List | ast.Tuple):
                    words = names.literals(first) or {str(e.value) for e in first.elts if isinstance(e, ast.Constant)}
                    if words >= {"docker", "compose"}:
                        tools.add("docker compose")
                    elif "--version" in words and isinstance(first.elts[0], ast.Constant):
                        tools.add(str(first.elts[0].value))
            elif isinstance(node, ast.Subscript) and ast.unparse(node.value) in ENVIRONS:
                take(env, node.slice, node)
            elif isinstance(node, ast.Compare) and any(ast.unparse(c) in ENVIRONS for c in node.comparators):
                take(env, node.left, node)
            elif isinstance(node, ast.Assign) and ast.unparse(node.targets[0]) == "NEEDS" and isinstance(
                    node.value, ast.Dict):
                for value in node.value.values:
                    take(tools, value, node)
    return env, {t for t in tools if "/" not in t and "." not in t}, unreadable


def reads(directory: Path = TESTS_DIR) -> set[str]:
    """Every name some `tests/*.py` reads from `os.environ` or `getenv`, or sets there for itself."""
    return sites(directory)[0]


def probed(directory: Path = TESTS_DIR) -> set[str]:
    """Every tool some `tests/*.py` looks for: `which`, `os.access(... / tool, os.X_OK)`, a `--version` probe, `NEEDS`,
    a stand-in `PATH` built from named tools, `docker compose` run as a probe."""
    return sites(directory)[1]


def unreadable(directory: Path = TESTS_DIR) -> list[str]:
    return sites(directory)[2]
