"""What `check-ux-gates` renders when `UX_GATES_SINCE` is not set: the previews a slice branch's changes can move.

On a slice branch outside CI the base is the scoped gate's own: `check-slice-scope.py`'s `merge_base`, found through
`verify-stamp.py`, both loaded from beside this package and never copied, and the changed paths are
`changes.changed` with the paths of the trunk's commits the forge does not carry yet (`changes.unpushed`, D153). So the
two cannot come to different answers about a branch. Wherever that base cannot be had or trusted — a CI run, the trunk,
a branch that is no `slice/<id>`, a repository this script cannot read — every preview renders, and one line says why.

The borders are asked in a fixed order, the first that holds is the only one said, and their words are
`verify-scoped.py`'s where it has them. `VERIFY_FORCE` and `make -n` are not borders here: neither is about what a
preview renders.
"""
from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any, NamedTuple

from . import changes
from .record import printable

sys.dont_write_bytecode = True

SCRIPTS = Path(__file__).resolve().parent.parent
LINE = "check-ux-gates: "
EVERY = LINE + "every preview in scope — "
SCOPED = (LINE + "{branch} — previews scoped to what changed since {short} (the commit on `{trunk}` this branch is "
          "built on){note}; UX_GATES_SINCE=all renders every preview")


class Scope(NamedTuple):
    """The paths a slice branch changed, or None where every preview renders; and the one line that says which."""

    changed: set[str] | None
    line: str
    branch: str = ""


def load(filename: str) -> Any:
    """A script beside the package, loaded under a name of its own and never copied."""
    spec = importlib.util.spec_from_file_location("ux_gates_for_" + filename.removesuffix(".py").replace("-", "_"),
                                                  SCRIPTS / filename)
    if spec is None or spec.loader is None:
        raise ImportError("cannot load " + filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def no_base(branch: str, said: str) -> str:
    """Why a slice branch has no base, said once: `check-slice-scope`'s own line names the branch already."""
    words = said.removeprefix("check-slice-scope: ")
    return f"no usable base: {words}" if words else f"{branch} has no usable base"


def every(why: str) -> Scope:
    return Scope(None, EVERY + why)


def asked(root: Path, *arguments: str) -> bytes:
    """What a `-q` question of git answers at the project root, as `verify-stamp.py`'s `git_or_nothing` reads it (git
    saying no without a reason is nothing), but never asked of the directory the script was run from."""
    done = subprocess.run(["git", *arguments], cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if done.returncode == 1 and not done.stderr:
        return b""
    if done.returncode != 0:
        raise RuntimeError("git " + " ".join(arguments) + ": " + done.stderr.decode("utf-8", "replace").strip())
    return done.stdout


def not_vouched(stamp: Any, top: str) -> str | None:
    """`verify-stamp.py`'s `not_vouched`, asked of the top the project root's git names, not the current directory's."""
    try:
        return stamp.index_problem(top)  # type: ignore[no-any-return]
    except stamp.CannotTell as error:
        return str(error)


def reason(stamp: Any, scope: Any, root: Path, ref: str, has_commit: bool) -> str | None:
    """Why every preview renders, from the first border that holds; None where none does."""
    for marker in stamp.CI_MARKERS:
        if os.environ.get(marker):
            return f"{marker} is set, so this is a CI run"
    branch = ref.removeprefix("refs/heads/")
    if not ref.startswith("refs/heads/"):
        return "HEAD is detached"
    if not has_commit:
        return "HEAD names no commit"
    named = str(scope.merge_base().named)
    if branch == named:
        return f"this is the trunk (`{printable(named)}`)"
    if not scope.SLICE_BRANCH.match(branch):
        return f"`{printable(branch)}` is not a slice/<id> branch"
    if scope.merge_base().commit is None:
        return no_base(branch, scope.check(branch)[3])
    problem = stamp.trunk_problem()[1]
    if problem is not None:
        return f"the trunk cannot be told — {problem}"
    top = os.path.realpath(str(scope.git_must("rev-parse", "--show-toplevel")).removesuffix("\n"))
    unvouched = not_vouched(stamp, top)  # an index git does not look at: a change to it would never be seen
    if unvouched is not None:
        return unvouched
    if top != os.path.realpath(root):
        return "the project is not the repository's top, and the changed paths are the top's"
    return None


def changed_among(scope: Any, base: str, among: Iterable[str] | None) -> set[str]:
    """`changes.changed`, with the raw reading of a file's bytes made only of the paths in `among`: git's own answer is
    the whole tree's and costs nothing, but comparing the bytes on disk with the base's opens every tracked file, and a
    preview's scope depends on the previews, the stylesheets they link and the files that move every preview alone.
    `among` of None is every path, which is `changes.changed`."""
    if among is None:
        return set(changes.changed(scope, base))
    found = set(scope.changed_files(base))
    top = str(scope.git_must("rev-parse", "--show-toplevel")).removesuffix("\n")
    held = changes.tree(scope, base)
    for path in set(among) - found:
        if path in held and changes.raw_differs(scope, base, held[path], path, os.path.join(top, path)):
            found.add(path)
    return found


def ask(root: Path, among: Iterable[str] | None) -> Scope:
    stamp = load("verify-stamp.py")
    scope = stamp.trunk_module()
    ref = asked(root, "symbolic-ref", "-q", "HEAD").removesuffix(b"\n").decode("utf-8", "surrogateescape")
    has_commit = bool(asked(root, "rev-parse", "-q", "--verify", "HEAD"))
    why = reason(stamp, scope, Path(root), ref, has_commit)
    if why is not None:
        return every(why)
    branch = ref.removeprefix("refs/heads/")
    base = scope.merge_base().commit
    span = changes.unpushed(scope, base)
    if span.failure is not None:
        return every(span.failure)
    found = changed_among(scope, base, among) | set(span.paths)
    short = (scope.git("rev-parse", "--short", base) or str(base)[:7]).strip()
    note = f"; {span.note}" if span.note else ""
    trunk = printable(str(scope.merge_base().named))
    return Scope(found, SCOPED.format(branch=printable(branch), short=short, trunk=trunk, note=note), branch)


def default(root: Path, among: Iterable[str] | None = None) -> Scope:
    """The scope the default gives in `root`: what changed since the slice's base, or every preview and why. `among` is
    the paths whose bytes can move a preview, which are the ones read raw (see `changed_among`)."""
    try:
        return ask(root, among)
    except Exception as error:  # a checkout this script cannot read is one it cannot scope
        return every(f"the slice's base could not be read ({printable(error, 120, False)})")
