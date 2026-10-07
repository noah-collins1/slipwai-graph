"""Inputs read through a link (T021, closing T013 for every row of the record).

A check reads what a link leads to, and the record names the link's own path: a change where the link leads is charged
to whatever claims that place, or to nothing (a projection linked outside the project), and the check that reads it
is skipped while `make verify` fails. So a check keeps no recorded inputs — it runs on every scoped run and claims
nothing — where one of its file inputs is a link, has a link among its directories below the project root, or is a
directory holding a link that leads anywhere but under the check's own inputs. Each is read in the working tree and
at the base (`git ls-tree`, mode 120000), so a link the branch replaced is still one. The reason names the link.

Under `apps/`, `packages/` and a deployable's own directory, what git ignores is the tools' own (`node_modules/.bin`,
a `.venv`'s interpreter), as `reach.py` holds it, and is not read for links; a link there that git lists is.
"""
from __future__ import annotations

import os
import posixpath
import sys
from pathlib import Path, PurePosixPath
from typing import Any

sys.dont_write_bytecode = True

from .reach import shown  # noqa: E402

EVERYTHING = "./"
SHARED = ("apps/", "packages/")  # `choose.SHARED`: what units build, whose ignored files are the tools' own
LINK_MODE = "120000"


class Tree:
    """The links the working tree and the base hold, as far as the inputs reach."""

    def __init__(self, root: Path, scope: Any, base: str | None) -> None:
        self.root = root
        self.real = root.resolve()
        self.scope = scope
        self.base = base
        self.at_base: dict[str, str] | None = None  # link path -> blob, read once where a base is asked

    def based(self) -> dict[str, str]:
        if self.at_base is None:
            self.at_base = {}
            # Paths relative to the project root, as `git` answers there: a link above the root is not one of its inputs.
            listed = self.scope.git("ls-tree", "-r", "-z", self.base) if self.base else ""
            if listed is None:
                raise LookupError("the base's tree cannot be listed")
            for item in listed.split("\0"):
                head, _, path = item.partition("\t")
                if head.split(" ")[0] == LINK_MODE:
                    self.at_base[path] = head.split(" ")[2]
        return self.at_base

    def on_the_way(self, entry: str) -> str | None:
        """The input itself or a directory of it below the root that is a link here or at the base: words, or None."""
        parts = PurePosixPath(entry.rstrip("/")).parts
        prefixes = ["/".join(parts[:end]) for end in range(1, len(parts) + 1)]
        here = next((path for path in prefixes if os.path.islink(self.root / path)), None)
        if here is not None:
            return said(here, False)
        there = next((path for path in prefixes if path in self.based()), None)
        return None if there is None else said(there, True)

    def listed(self, directories: list[str], ignored: list[str]) -> list[str]:
        """Every path git lists under `directories` (tracked, or untracked and not ignored: one listing of the tree,
        as `reach.listed` takes it) and, under `ignored`, what it ignores too: the working tree's candidates for a
        link. A directory under another of the list is asked once, through the outer one."""
        found: list[str] = []
        outer = [entry for entry in ignored if not any(entry != other and entry.startswith(other) for other in ignored)]
        for flags, where in ((("--cached", "--others", "--exclude-standard"), []),
                             (("--others", "--ignored", "--exclude-standard"), outer)):
            if flags[1] == "--ignored" and not where:
                continue
            out = self.scope.git("ls-files", "-z", *flags, *(["--", *where] if where else []))
            if out is None:
                raise LookupError("git cannot list the tree")
            found.extend(item for item in out.split("\0") if item and any(under(item, entry) for entry in directories))
        return found

    def leads_to(self, link: str) -> str | None:
        """Where a working-tree link leads, relative to the root; None where it leaves the project or cannot be told."""
        try:
            target = (self.root / link).resolve()
            return target.relative_to(self.real).as_posix()
        except (OSError, RuntimeError, ValueError):
            return None

    def led_to_at_base(self, link: str) -> str | None:
        text = self.scope.git("cat-file", "blob", self.based()[link])
        if text is None or text.startswith("/"):
            return None
        landed = posixpath.normpath(posixpath.join(posixpath.dirname(link), text))
        parts = PurePosixPath(landed).parts
        if landed in (".", "..") or landed.startswith("../") or any(
                "/".join(parts[:end]) in self.based() for end in range(1, len(parts) + 1)):
            return None  # out of the project, or on through another link: what it reads cannot be told
        return landed


def said(link: str, at_base: bool) -> str:
    where = " at the base" if at_base else ""
    return f"it reads through the link `{shown(link).replace('`', chr(39))}`{where}, which no recorded input follows"


def under(path: str, entry: str) -> bool:
    return entry == EVERYTHING or path == entry.rstrip("/") or (entry.endswith("/") and path.startswith(entry))


def beneath(tree: Tree, files: list[str], links: list[str], at_base: bool) -> str | None:
    """The first link under one of the check's directory inputs that leads anywhere but under its own inputs."""
    directories = [entry for entry in files if entry.endswith("/") and entry != EVERYTHING]
    for link in links:
        if any(under(link, entry) for entry in directories):
            landed = tree.led_to_at_base(link) if at_base else tree.leads_to(link)
            if landed is None or not any(under(landed, entry) for entry in files if entry != EVERYTHING):
                return said(link, at_base)
    return None


def with_links(checks: dict[str, Any], root: Path, scope: Any, base: str | None,
               deployables: dict[str, dict[str, Any]] | None = None) -> None:
    """Every check that reads an input through a link keeps no recorded inputs, with the link named as its reason."""
    held = {name: entry for name, entry in checks.items() if entry["inputs"] is not None and not entry["always"]}
    entries = sorted({path for entry in held.values() for path in entry["inputs"]["files"] if path != EVERYTHING})
    tree = Tree(root, scope, base)
    try:
        linked = {entry: words for entry in entries if (words := tree.on_the_way(entry)) is not None}
        directories = [entry for entry in entries if entry.endswith("/") and entry not in linked]
        own = tuple(SHARED) + tuple(str(item["path"]).rstrip("/") + "/" for item in (deployables or {}).values())
        here = [path for path in tree.listed(directories, [entry for entry in directories if not entry.startswith(own)])
                if os.path.islink(root / path)]
        there = sorted(tree.based())
    except LookupError as error:
        for entry in held.values():
            entry.update(inputs=None, claims=False, always=f"its inputs cannot be read for links: {error}")
        return
    for entry in held.values():
        files = entry["inputs"]["files"]
        reason = next((linked[path] for path in files if path in linked), None) \
            or beneath(tree, files, sorted(set(here)), False) or beneath(tree, files, there, True)
        if reason is not None:
            entry.update(inputs=None, claims=False, always=reason)
