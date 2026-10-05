"""What the `mutation-scope.py` suites share beyond the borders': a generated Go project cut per example, the project's
own copy of the script run in this process behind a fake `Runner`, and the fake. Not a test module."""
from __future__ import annotations

import contextlib
import io
import os
import re
import shutil
import subprocess
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


def with_recipe(text: str, lines: list[str]) -> str:
    """The Makefile with `mutation-full`'s recipe lines replaced, its target line and everything else as it was."""
    return re.sub(r"(?m)^(mutation-full:[^\n]*\n)(?:\t[^\n]*\n)+", lambda found: found.group(1) + "".join(
        "\t" + line + "\n" for line in lines), text, count=1)


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

    def git_out(self, *args: str, env: dict[str, str] | None = None, stdin: str | None = None) -> str:
        done = subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@local", "-c", "maintenance.auto=false",
                               *args], cwd=self.repo, check=True, text=True, capture_output=True, input=stdin,
                              env=env, timeout=60)
        return done.stdout.strip()

    def fit_recipe(self, words: tuple[str, ...]) -> None:
        """Make the project's `mutation-full` recipe the one the factory writes for `words`, in the base: on `main`, and
        merged into the slice branch, so the change is nobody's change and the scoped examples stay scoped."""
        from test_mutation_targets import full_recipe  # the factory's own table, built there

        old = self.git_out("show", "main:Makefile")
        new = with_recipe(old + "\n", full_recipe(list(words)))[:-1]
        if new == old:
            return
        if self.git_out("rev-parse", "--abbrev-ref", "HEAD") == "main":
            (self.repo / "Makefile").write_text(new, encoding="utf-8")
            self.git_out("commit", "-q", "-m", "fit the recipe", "--", "Makefile")
            return
        index = {**os.environ, "GIT_INDEX_FILE": str(self.repo / ".git/fit-index")}
        self.git_out("read-tree", "main", env=index)
        blob = self.git_out("hash-object", "-w", "--stdin", stdin=new)
        self.git_out("update-index", "--cacheinfo", f"100644,{blob},Makefile", env=index)
        tree = self.git_out("write-tree", env=index)
        commit = self.git_out("commit-tree", tree, "-p", "main", "-m", "fit the recipe")
        (self.repo / ".git/fit-index").unlink()
        self.git_out("update-ref", "refs/heads/main", commit)
        self.git_out("merge", "-q", "--no-edit", "main")

    def commit(self, message: str = "change") -> None:
        git(self.repo, "add", "-A")
        git(self.repo, "-c", "user.name=t", "-c", "user.email=t@local", "-c", "maintenance.auto=false",
            "commit", "-q", "-m", message)

    def run_in_process(self, *services: str, env: dict[str, str] | None = None,
                       runner_args: dict[str, Any] | None = None) -> Ran:
        """The project's copy of the script, loaded and called here with its fake runner, under `env`."""
        words = services or ("go:apps/service",)
        self.fit_recipe(words)
        module = loaded(self.repo / "scripts/mutation-scope.py")
        runner = FakeRunner(module, **(runner_args or {}))
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
