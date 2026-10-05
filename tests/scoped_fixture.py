"""What the `test_verify_scoped_*` modules share: the stamp fixture's project on a slice branch, and readers over a run.

Not a test module. A project is the stamp fixture's (generated once per process, copied per test), with the stand-in
`uv`, `make`, `git` and `python3` first on `PATH` that log each call to `$STANDIN_LOG`, on `slice/S1` cut from the
`main` it began on. Evidence is the log and the files a run leaves, never a clock and never a line the run printed
about itself.
"""
from __future__ import annotations

import atexit
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from stamp_fixture import PYVENV_CFG, StampTestCase, git, write_stand_ins
from support import FactoryTestCase, commit_all
from test_scoped_targets import build

from slipwai.assets import ROOT

sys.dont_write_bytecode = True

SLICE = "slice/S1"
LINE = "verify-scoped: "
FULL = LINE + "the full gate runs, as `make verify` — "


# What a green full run on a slice branch leaves beside the stamp, without the run: the baseline, written by
# `verify-stamp.py`'s own functions from what the project's recipe hands the stamp, with the tools the environment
# answers. Run in the project, as the interpreter that runs the tests (the stand-in `python3` is for the gate's calls).
_BASELINE = """
import importlib.util, sys
sys.dont_write_bytecode = True
sys.path.insert(0, "scripts")
from verify_scoped import record
spec = importlib.util.spec_from_file_location("stamp", "scripts/verify-stamp.py")
stamp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stamp)
found = record.database("make", "Makefile").variables["VERIFY_STAMP"]
stamp.write_baseline(stamp.machine_tools(stamp.Options(["--make", "make", *found.split()])))
"""


class ScopedCase(StampTestCase):
    """The stamp fixture's project, checked out on `slice/S1` with `main` behind it."""

    def setUp(self) -> None:
        super().setUp()
        git(self.repo, "checkout", "-q", "main")
        git(self.repo, "checkout", "-q", "-b", SLICE)

    def checkout(self, *args: str) -> None:
        git(self.repo, "checkout", "-q", *args)

    def write_baseline(self, env: dict[str, str | None] | None = None) -> None:
        """The baseline a green `make verify` would leave on this branch, taken under `env`; the log is cleared."""
        subprocess.run([sys.executable, "-B", "-c", _BASELINE], cwd=self.repo, env=self.environment(env), check=True,
                       capture_output=True, timeout=60)
        self.forget_log()

    def baseline_file(self) -> Path:
        (found,) = sorted((self.repo / ".git" / "slipwai").glob("verify-baseline-*.json"))
        return found

    def scoped(
        self, env: dict[str, str | None] | None = None, args: list[str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        """`make verify-scoped` as a person types it, in the project."""
        return subprocess.run(
            ["make", "verify-scoped", *(args or [])], cwd=self.repo, env=self.environment(env), text=True,
            capture_output=True, timeout=180,
        )

    def scoped_lines(self, run: subprocess.CompletedProcess[str]) -> list[str]:
        """The lines `verify-scoped` said, in order."""
        return [line for line in run.stdout.splitlines() if line.startswith(LINE)]

    def verify_calls(self) -> list[str]:
        """The `make` calls the stand-in saw whose goal is `verify`: the full gate was asked for, however it ended."""
        calls = []
        for line in self.log.read_text(encoding="utf-8").splitlines() if self.log.exists() else []:
            tool, _, arguments = line.partition("\t")
            if tool == "make" and arguments.split()[-1:] == ["verify"]:
                calls.append(arguments)
        return calls


# What a project whose tools are not on this machine needs: `npm` and `node` that log the call, and a `make` whose
# call that names the chosen units can be told to print what it would run, so a Go, a Java or a Python shape's
# selection is read without those toolchains.
_NPM = """#!/bin/sh
printf 'npm\\t%s\\n' "$*" >> "$STANDIN_LOG"
[ "$1" = --version ] && echo "${STANDIN_NPM_VERSION:-10.9.0}"
case "$1" in ci|install) mkdir -p node_modules; : > node_modules/.package-lock.json;; esac
exit 0
"""
_NODE = """#!/bin/sh
printf 'node\\t%s\\n' "$*" >> "$STANDIN_LOG"
[ "$1" = --version ] && [ -n "$STANDIN_NODE_FAIL" ] && exit 1
[ "$1" = --version ] && echo "${STANDIN_NODE_VERSION:-v22.1.0}"
exit 0
"""
_MAKE = """#!/bin/bash
printf '%s\\t%s\\n' "make" "$*" >> "$STANDIN_LOG"
case " $* " in *" VERIFY_ORDER=1 "*) [ -n "$STANDIN_DRY" ] && exec -a make "{real}" -n "$@";; esac
exec -a make "{real}" "$@"
"""
_shapes: dict[str, Path] = {}
EVENTS = "events"  # not a shape of `test_scoped_targets`: an event-modelling project with a second service beside it


def events_project(parent: Path) -> Path:
    """An event-modelling project with a `service` and a `billing` service, committed on `main`."""
    project = FactoryTestCase().generate(parent, "ledger", "event-modelling", "python", "none", http="fastapi",
                                         event_store="sqlite")
    subprocess.run([str(ROOT / "slipwai"), "add-service", "billing", "--language", "python"], cwd=project, check=True,
                   capture_output=True, timeout=120)
    commit_all(project, "billing")
    return project


def shape_template(shape: str) -> Path:
    """One generated project of a shape `test_scoped_targets` names, made once per process and never run in."""
    if shape not in _shapes:
        parent = Path(tempfile.mkdtemp(prefix="scoped-shape-"))
        atexit.register(shutil.rmtree, parent, ignore_errors=True)
        project = events_project(parent) if shape == EVENTS else build(parent, shape, FactoryTestCase())
        for key, value in (("user.name", "t"), ("user.email", "t@local"), ("commit.gpgsign", "false")):
            git(project, "config", key, value)
        if git(project, "status", "--porcelain").strip():  # `add-service` leaves what it wrote uncommitted
            commit_all(project, "the shape")
        _shapes[shape] = project
    return _shapes[shape]


class ShapeCase(ScopedCase):
    """A generated project of `shape`, on `slice/S1` cut from its `main`, with the stand-ins first on `PATH`: the stamp
    fixture's `uv`, `git` and `python3`, and `npm`, `node` and `make` as above. `STANDIN_DRY` makes the call that names
    the chosen units print and run nothing."""

    shape = "model-typescript-web"

    def setUp(self) -> None:
        unittest.TestCase.setUp(self)
        scratch = Path(tempfile.mkdtemp(prefix="scoped-case-"))
        self.addCleanup(shutil.rmtree, scratch, ignore_errors=True)
        self.repo = scratch / "project"
        shutil.copytree(shape_template(self.shape), self.repo, symlinks=True)
        self.bin = scratch / "bin"
        write_stand_ins(self.bin)
        for name, text in (("npm", _NPM), ("node", _NODE),
                           ("make", _MAKE.replace("{real}", shutil.which("make") or "make"))):
            (self.bin / name).write_text(text, encoding="utf-8")
            (self.bin / name).chmod(0o755)
        self.log = scratch / "standin.log"
        self.checkout("-b", SLICE)
        for pyproject in sorted(self.repo.glob("apps/*/pyproject.toml")):  # what `uv sync` leaves
            config = pyproject.parent / ".venv" / "pyvenv.cfg"
            config.parent.mkdir(exist_ok=True)
            config.write_text(PYVENV_CFG, encoding="utf-8")
        self.write_baseline()  # as a green run on this branch, on this machine, left it

    def edit(self, path: str, text: str = "\n# an edit\n") -> None:
        """Make `path` differ from the base, as a person editing it would, uncommitted."""
        target = self.repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        old = target.read_text(encoding="utf-8") if target.exists() else ""
        target.write_text(old + text, encoding="utf-8")

    def reset(self) -> None:
        """Back to the base: every edit made so far, committed or not, is undone."""
        git(self.repo, "checkout", "-q", "--", ".")
        git(self.repo, "clean", "-fdq")
        self.forget_log()

    def lines(self, run: subprocess.CompletedProcess[str]) -> list[str]:
        """The unit lines a run said, as `run  <unit> — <reason>` and `skip <unit> — <reason>`."""
        said = [line.removeprefix(LINE) for line in self.scoped_lines(run)]
        return [line for line in said if line.startswith(("run ", "skip"))]

    def decided(self, run: subprocess.CompletedProcess[str]) -> tuple[dict[str, str], dict[str, str]]:
        """The units a run said it would run, and those it skipped, each with its reason."""
        ran: dict[str, str] = {}
        skipped: dict[str, str] = {}
        for line in self.lines(run):
            verb, _, rest = line.partition(" ")
            unit, _, reason = rest.strip().partition(" — ")
            (ran if verb == "run" else skipped)[unit] = reason
        return ran, skipped

    def called(self) -> list[list[str]]:
        """The goals of the one `make` call that names the chosen units: every `make` call of the log that carries
        `VERIFY_ORDER=1`, each as its goals."""
        calls = []
        for line in self.log.read_text(encoding="utf-8").splitlines() if self.log.exists() else []:
            tool, _, arguments = line.partition("\t")
            words = arguments.split()
            if tool == "make" and "VERIFY_ORDER=1" in words:
                calls.append([word for word in words if not word.startswith("-") and word != "VERIFY_ORDER=1"
                              and word != "Makefile"])
        return calls
