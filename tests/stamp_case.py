"""The fixture project every `test_verify_stamp_*` module runs the real gate against, and the case that copies it.

Not a test module. The project is one the factory generates — standard profile, Python backend, no transport, no
frontend — on a branch that is not the trunk, copied per test from one generation. The stand-ins are executables
written by `stamp_names` and put first on `PATH`. Every check script of the project is the real one, so the full gate
passes in about half a second with no network, and what ran is read from the stand-ins' log, never from what the run
printed (AC-S03-19). `plant_stamp`, which loads the project's script with `importlib`, stays in `stamp_fixture`.
"""
from __future__ import annotations

import atexit
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from stamp_names import (
    BRANCH,
    CI_MARKERS,
    CLOSING,
    GIT_STATE,
    MAKE_STATE,
    PYVENV_CFG,
    REUSE_PREFIX,
    SERVICE,
    checks_started,
    git,
    write_stand_ins,
)

from slipwai.assets import ROOT
from slipwai.project.gate import FAILED

# `template()` generates one project, standard profile on the Python backend with no frontend, through the launcher
# (read per axis from its literal argv, D187), and `StampTestCase` copies it per test. `reads` names the launcher and
# the package it runs; the list does not start with `"slipwai"`, which the selector would read as a launcher route.
TEST_SELECTION: dict[str, object] = {
    "configurations": {"backend": ["python"], "profile": ["standard"], "frontend": ["none"]},
    "reads": ["src/slipwai", "slipwai"],
}

sys.dont_write_bytecode = True

_template: Path | None = None


def template() -> Path:
    """The fixture project, generated once per process and never run in: tests copy it."""
    global _template
    if _template is None:
        parent = Path(tempfile.mkdtemp(prefix="stamp-fixture-"))
        atexit.register(shutil.rmtree, parent, ignore_errors=True)
        subprocess.run(
            [str(ROOT / "slipwai"), "generate", "fixture", "--profile", "standard", "--backend", "python",
             "--frontend", "none", "--http", "none", "--output", str(parent), "--skip-checks"],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        repo = parent / "fixture"
        git(repo, "checkout", "-q", "-b", BRANCH)
        for key, value in (("user.name", "t"), ("user.email", "t@local"), ("commit.gpgsign", "false")):
            git(repo, "config", key, value)
        (repo / SERVICE / ".venv").mkdir(parents=True, exist_ok=True)
        (repo / SERVICE / ".venv" / "pyvenv.cfg").write_text(PYVENV_CFG, encoding="utf-8")
        _template = repo
    return _template



class StampTestCase(unittest.TestCase):
    """One fixture project per test, a stand-in directory first on `PATH`, and `run_gate`."""

    repo: Path
    log: Path

    def setUp(self) -> None:
        sys.dont_write_bytecode = True
        scratch = Path(tempfile.mkdtemp(prefix="stamp-test-"))
        self.addCleanup(shutil.rmtree, scratch, ignore_errors=True)
        self.repo = scratch / "project"
        shutil.copytree(template(), self.repo, symlinks=True)
        self.bin = scratch / "bin"
        write_stand_ins(self.bin)
        self.log = scratch / "standin.log"

    def environment(self, extra: dict[str, str | None] | None = None) -> dict[str, str]:
        """The environment of a run: the stand-ins first on `PATH`, the three CI markers removed unless the
        example sets one, and `extra` on top (a `None` removes a name)."""
        env = {key: value for key, value in os.environ.items() if key not in CI_MARKERS + MAKE_STATE + GIT_STATE}
        env["PATH"] = f"{self.bin}{os.pathsep}{env.get('PATH', '')}"
        env["STANDIN_LOG"] = str(self.log)
        for key, value in (extra or {}).items():
            if value is None:
                env.pop(key, None)
            else:
                env[key] = value
        return env

    def run_gate(
        self, env: dict[str, str | None] | None = None, args: list[str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        """`make verify` as a developer types it, in the project, with the log kept between runs."""
        return subprocess.run(
            ["make", "verify", *(args or [])], cwd=self.repo, env=self.environment(env), text=True,
            capture_output=True, timeout=180,
        )

    def forget_log(self) -> None:
        self.log.write_text("", encoding="utf-8")

    def checks(self) -> list[str]:
        return checks_started(self.log)

    def stamp_path(self) -> Path | None:
        """The project's stamp, under the git directory; None where there is none."""
        found = sorted((self.repo / ".git/slipwai").glob("verify-stamp-*.json"))
        return found[0] if found else None

    def stamp(self) -> dict[str, object]:
        path = self.stamp_path()
        self.assertIsNotNone(path, "no stamp under .git/slipwai")
        assert path is not None
        return json.loads(path.read_text(encoding="utf-8"))

    def reuse_lines(self, run: subprocess.CompletedProcess[str]) -> list[str]:
        """The stamp's lines of a run: those beginning `verify:` other than the gate's two closing lines, a pass's
        and, since S04, a failed run's (AC-S04-9)."""
        closing = (CLOSING, FAILED)
        return [line for line in run.stdout.splitlines() if line.startswith(REUSE_PREFIX) and line not in closing]

