"""What the `mutation-scope.py` suites share beyond the borders': a generated Go project cut per example, the project's
own copy of the script run in this process behind a fake `Runner`, and the fake. Not a test module."""
from __future__ import annotations

import contextlib
import io
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

from stamp_fixture import git
from support import FactoryTestCase
from test_mutation_borders import calls, clean_environment, fake_make, loaded

sys.dont_write_bytecode = True
SLICE = "slice/S1"
HEALTH = "apps/service/health/health.go"


class FakeRunner:
    """The script's `Runner` seam in the test tree: records `(path, files)` per call, returns a set status, and reports
    every file it was given as mutated unless `mutable` says which of them the tool would take."""

    def __init__(self, module: Any, statuses: dict[str, int] | None = None, mutable: dict[str, list[str]] | None = None,
                 refusals: dict[str, str] | None = None) -> None:
        self.result = module.Result
        self.statuses = statuses or {}
        self.mutable = mutable
        self.refusals = refusals or {}
        self.seen: list[tuple[str, list[str]]] = []

    def run(self, backend: str, path: str, files: list[str]) -> Any:
        self.seen.append((path, list(files)))
        kept = files if self.mutable is None else self.mutable.get(path, [])
        gone = [(name, "outside the tool's targets") for name in files if name not in kept]
        return self.result(self.statuses.get(path, 0), list(kept), gone, self.refusals.get(path))


class Ran:
    """What one in-process run of the script left: status, stdout and the fake runner's calls."""

    def __init__(self, status: int, out: str, runner: FakeRunner, make_calls: list[list[str]]) -> None:
        self.status, self.out, self.runner, self.make_calls = status, out, runner, make_calls
        self.lines = out.splitlines()
        self.first = self.lines[0] if self.lines else ""
        self.last = self.lines[-1] if self.lines else ""


class ScopeCase(FactoryTestCase):
    """A generated Go project (cut per example) with the script's own copy run in this process."""

    longMessage = False
    template: Path | None = None
    parent: Path

    @classmethod
    def setUpClass(cls) -> None:
        cls.parent = Path(tempfile.mkdtemp(prefix="mutation-scope-"))
        cls.addClassCleanup(shutil.rmtree, cls.parent, ignore_errors=True)
        cls.template = cls().generate(cls.parent, "scoped", "standard", "go", http="none")

    def setUp(self) -> None:
        assert self.template is not None
        self.repo = Path(tempfile.mkdtemp(dir=self.parent)) / "project"
        shutil.copytree(self.template, self.repo, symlinks=True)
        self.tools = Path(tempfile.mkdtemp(dir=self.parent))
        self.make, self.log = fake_make(self.tools)
        git(self.repo, "checkout", "-q", "-b", SLICE)

    def write(self, path: str, text: str = "package x\n") -> None:
        target = self.repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")

    def commit(self, message: str = "change") -> None:
        git(self.repo, "add", "-A")
        git(self.repo, "-c", "user.name=t", "-c", "user.email=t@local", "-c", "maintenance.auto=false",
            "commit", "-q", "-m", message)

    def run_in_process(self, *services: str, env: dict[str, str] | None = None,
                       runner_args: dict[str, Any] | None = None) -> Ran:
        """The project's copy of the script, loaded and called here with its fake runner, under `env`."""
        module = loaded(self.repo / "scripts/mutation-scope.py")
        runner = FakeRunner(module, **(runner_args or {}))
        words = services or ("go:apps/service",)
        arguments = ["--make", str(self.make), "--makefile", "Makefile", *words]
        wanted = clean_environment() if env is None else env
        saved, here = dict(os.environ), os.getcwd()
        os.environ.clear()
        os.environ.update(wanted)
        os.chdir(self.repo)
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out):
                status = module.main(arguments, runner)
        finally:
            os.chdir(here)
            os.environ.clear()
            os.environ.update(saved)
        return Ran(status, out.getvalue(), runner, calls(self.log))
