"""The fixture project and the stand-in tools every `test_verify_stamp_*` module runs the real gate against.

Not a test module. The project is one the factory generates — standard profile, Python backend, no transport, no
frontend — on a branch that is not the trunk, copied per test from one generation. The stand-ins are executables
written here and put first on `PATH`: `uv`, which is the one tool whose work the gate cannot do offline, and `make`,
`git` and `python3`, which log the call and hand it to the real one. Every check script of the project is the real
one, so the full gate passes in about half a second with no network, and what ran is read from the stand-ins' log,
never from what the run printed (AC-S03-19).
"""
from __future__ import annotations

import contextlib
import importlib.util
import json
import os
import re
import sys
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType

import stamp_case
from stamp_case import template  # noqa: F401
from stamp_names import (  # noqa: F401
    BRANCH,
    CI_MARKERS,
    CLOSING,
    GIT_STATE,
    INSTANT,
    MAKE_STATE,
    PYVENV_CFG,
    REUSE_PREFIX,
    SERVICE,
    checks_started,
    commit_all,
    exclude,
    git,
    probe_path,
    write_spaced_make,
    write_stand_ins,
)

# Undeclared: `load_script` loads a generated project's script with `importlib`, which the scan reads as a reach into
# the repository that `reads` cannot name (D164 rule 4), and `plant_stamp` and `KeyTestCase` need it. The names, the
# stand-ins and the generation moved to `stamp_names` and `stamp_case` (declared) and are re-exported here; a module
# that needs only those imports them from there, and a module that imports this one always runs.

sys.dont_write_bytecode = True


class StampTestCase(stamp_case.StampTestCase):
    """The fixture's case, with `plant_stamp`, which builds the project's key through its own script."""

    def plant_stamp(self) -> bytes:
        """A stamp that is valid for the tree, the branch and the machine as they stand now, written as a pass would
        write it, and its bytes: what a run that may read it would reuse, so a run that does not is seen not to."""
        module = load_script(self.repo)
        makefile = (self.repo / "Makefile").read_text(encoding="utf-8")
        arguments = re.search(r"^VERIFY_STAMP := (.*)$", makefile, re.M)
        assert arguments is not None
        options = module.Options(["--make", "make", *arguments.group(1).split()])
        was, here, env = dict(os.environ), Path.cwd(), self.environment()
        os.environ.clear()
        os.environ.update(env)
        os.chdir(self.repo)
        try:
            stamp = dict(module.build_key(module.machine_tools(options)), passed="2026-01-01T00:00:00Z", result="pass")
            module.write_file(module.stamp_path(), json.dumps(stamp, indent=2, sort_keys=True) + "\n")
            return Path(module.stamp_path()).read_bytes()
        finally:
            os.chdir(here)
            os.environ.clear()
            os.environ.update(was)


def key_of(repo: Path) -> str:
    """The key of `repo` as `reuse` would build it with no tool to ask, in this process, in that directory."""
    module = load_script(repo)
    was = Path.cwd()
    os.chdir(repo)
    try:
        return str(module.build_key({})["key"])
    finally:
        os.chdir(was)




def load_script(repo: Path) -> ModuleType:
    """The project's own `scripts/verify-stamp.py`, loaded as a module so a test can read its lists and build its
    key without a gate run. Nothing is written beside it."""
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("verify_stamp_under_test", repo / "scripts" / "verify-stamp.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class KeyTestCase(StampTestCase):
    """Examples that hold the key itself: it is built in this process, in the project's directory, for the tree and
    the environment as they stand — the same function a `reuse` run calls, with no tool to ask."""

    @contextlib.contextmanager
    def in_project(self) -> Iterator[None]:
        was = Path.cwd()
        os.chdir(self.repo)
        try:
            yield
        finally:
            os.chdir(was)

    def key(self) -> str:
        module = load_script(self.repo)
        with self.in_project():
            return str(module.build_key({})["key"])

    @contextlib.contextmanager
    def variable(self, name: str, value: str | None) -> Iterator[None]:
        """`name` set to `value` (unset for None) for the length of the block, as it was afterwards."""
        was = os.environ.get(name)
        if value is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = value
        try:
            yield
        finally:
            if was is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = was
