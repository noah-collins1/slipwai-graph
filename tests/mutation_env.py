"""The environment the mutation suites run `make` and the scope script in: the machine's, less CI, make and git state.

Not a test module, and it generates nothing: `test_mutation_borders` re-exports `clean_environment` so every importer
keeps its name, and the one that runs a real Spring build imports it from here so its declaration need not drag in a
module that generates Go projects and loads their scripts with `importlib`.
"""
from __future__ import annotations

import os

from stamp_names import CI_MARKERS, GIT_STATE, MAKE_STATE

TEST_SELECTION: dict[str, object] = {}


def clean_environment(**extra: str) -> dict[str, str]:
    """The machine's environment without CI, make or git state (and `SINCE`), then what the example sets."""
    kept = {k: v for k, v in os.environ.items() if k not in CI_MARKERS + MAKE_STATE + GIT_STATE + ("SINCE",)}
    return {**kept, **extra}
