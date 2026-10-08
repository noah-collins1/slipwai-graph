"""mutmut for a generated Python service: the wrapper's path and the one recipe line.

The mutation tool of the Python backend is mutmut, pinned exactly in each service's dev group (ADR 0010), configured by
the `[tool.mutmut]` table of the service's `pyproject.toml` and run through `scripts/mutmut-mutation.py`, which decides
the verdict from the `.meta` files mutmut writes and not from mutmut's exit status. This module is the factory's half:
where the wrapper lands in a project and the one line the Makefile runs. The wrapper itself is an asset,
`assets/languages/python/scripts/mutmut-mutation.py`.
"""
from __future__ import annotations

from ..assets import LANGUAGE_ROOT
from ..backends import APP
from ..services import App

# Where the wrapper lands in a project (once, however many Python services there are) and the asset it is read from.
SCRIPT_PATH = "scripts/mutmut-mutation.py"
SCRIPT_ASSET = LANGUAGE_ROOT / "python" / "scripts" / "mutmut-mutation.py"
# The `mutation-full` line of a Python service, with the service's path as the token every native command carries.
FULL_COMMAND = f"python3 {SCRIPT_PATH} {APP}"


def mutmut_files(services: list[App]) -> dict[str, str]:
    """What mutmut adds beside the services: the wrapper, once, at its path from the project root."""
    return {SCRIPT_PATH: SCRIPT_ASSET.read_text(encoding="utf-8")} if services else {}
