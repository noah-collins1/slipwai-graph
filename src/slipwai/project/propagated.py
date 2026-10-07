"""The list of paths `migrate` carries into a generated project, which `scripts/reversibility.py` reads.

A generated project has no `.written` (that is an adopted repository's list of what the factory wrote into a tree
that is mostly not its own), so the same fact is written here: one project-relative path per line, sorted, the
method's own categories and the list itself. Application code, documentation and anything an extension projects
are the project's own to change and are not named (D183).
"""
from __future__ import annotations

from ..assets import PROPAGATED

# Directories whose every file is the method's, and the root files that are.
METHOD_DIRECTORIES = ("scripts", "skills", "commands", "agents", ".specify")
METHOD_FILES = ("Makefile", "init")


def propagated_file(files: dict[str, str]) -> str:
    """The list's text for the assembled `files`: sorted, one path per line, the list itself among them."""
    paths = {
        path for path in files
        if path in METHOD_FILES or any(path.startswith(f"{root}/") for root in METHOD_DIRECTORIES)
    }
    return "".join(f"{path}\n" for path in sorted({*paths, PROPAGATED}))
