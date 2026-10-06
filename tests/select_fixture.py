"""The temporary repository every `test_select_tests_*` module drives the real root `Makefile` in.

Not a test module. The repository holds the root `Makefile` as it is, the scripts the stamp and the selector load
(copied where they exist), a `project.json` recording `ci.branch` `main`, and stand-in `tests/test_*.py` modules that
append their name, `PYTHONPATH` and `FACTORY_BACKENDS` to a log. What ran is read from that log, never from a printed
line (AC-S38-1). Later tasks extend it with declarations, a small `catalog.json` and slice branches.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from stamp_fixture import CI_MARKERS, GIT_STATE, MAKE_STATE

from slipwai.assets import ROOT

sys.dont_write_bytecode = True

SCRIPTS = "assets/toolkit/scripts/"
# What the selector and the stamp load; a path that does not exist yet (the selector, before T002) is skipped.
COPIED = ("Makefile", "scripts/select-tests.py", "scripts/select_tests", SCRIPTS + "check-slice-scope.py",
          SCRIPTS + "verify-stamp.py", SCRIPTS + "verify_scoped")
# What a run is told by the person, not by the machine: removed from the child unless an example sets it.
NARROWING = ("RATCHET_TIGHTEN", "FULL", "SINCE", "TESTS", "SKIP", "FACTORY_BACKENDS", "VERIFY_FORCE")
# The variables the recipe's stamp bypass tests, in the order the `Makefile` writes them (T001's recording).
BYPASS = ("TESTS", "SKIP", "FACTORY_BACKENDS")
STAND_IN = ("import os\nimport unittest\n\n\nclass Case(unittest.TestCase):\n    def test_it(self):\n"
            "        with open(os.environ['STANDIN_LOG'], 'a', encoding='utf-8') as log:\n"
            "            log.write('module\\t{name}\\tPYTHONPATH=' + os.environ.get('PYTHONPATH', '')\n"
            "                      + '\\tFACTORY_BACKENDS=' + os.environ.get('FACTORY_BACKENDS', '') + '\\n')\n")
LINT = "#!/bin/sh\necho \"verify $*\" >> \"$STANDIN_LOG\"\nexit 0\n"
STRUCTURE = ("import os\nwith open(os.environ['STANDIN_LOG'], 'a', encoding='utf-8') as log:\n"
             "    log.write('check-structure\\n')\n")


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, check=True, text=True, capture_output=True).stdout


def bypass_list(makefile: Path) -> tuple[str, ...]:
    """The variables the `verify` recipe's `ifneq` tests, read from the text of that `Makefile`."""
    found = re.search(r"^ifneq \(\$\(strip ((?:\$\([A-Z_]+\))+)\),\)$", makefile.read_text(encoding="utf-8"), re.M)
    if found is None:
        raise AssertionError("the verify recipe's bypass test was not found in the Makefile")
    return tuple(re.findall(r"\$\(([A-Z_]+)\)", found.group(1)))


class SelectCase(unittest.TestCase):
    """A repository on `main` holding the given stand-in modules; `branch()` moves it."""

    modules: tuple[str, ...] = ("test_a", "test_b", "test_c")
    repo: Path
    log: Path

    def setUp(self) -> None:
        scratch = Path(tempfile.mkdtemp(prefix="select-"))
        self.addCleanup(shutil.rmtree, scratch, ignore_errors=True)
        self.repo, self.log = scratch / "repo", scratch / "standin.log"
        self.repo.mkdir()
        for name in COPIED:
            source = ROOT / name
            if not source.exists():
                continue
            (self.repo / name).parent.mkdir(parents=True, exist_ok=True)
            if source.is_dir():
                shutil.copytree(source, self.repo / name, ignore=shutil.ignore_patterns("__pycache__"))
            else:
                shutil.copy(source, self.repo / name)
        for module in self.modules:
            self.write(f"tests/{module}.py", STAND_IN.format(name=module))
        self.write("scripts/verify", LINT)
        (self.repo / "scripts/verify").chmod(0o755)
        self.write("scripts/check-structure.py", STRUCTURE)
        self.write("src/mod.py", "X = 1\n")
        self.write(".gitignore", "__pycache__/\n.factory-work/\n")
        self.write("project.json", '{"ci": {"branch": "main"}}\n')
        git(self.repo, "init", "-q", "-b", "main")
        for key, value in (("user.name", "t"), ("user.email", "t@local"), ("commit.gpgsign", "false")):
            git(self.repo, "config", key, value)
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "trunk")
        self.log.write_text("", encoding="utf-8")

    def write(self, name: str, text: str) -> None:
        (self.repo / name).parent.mkdir(parents=True, exist_ok=True)
        (self.repo / name).write_text(text, encoding="utf-8")

    def branch(self, name: str) -> None:
        """Move to `name`, made from where the repository is if it does not exist."""
        exists = subprocess.run(["git", "rev-parse", "-q", "--verify", f"refs/heads/{name}"], cwd=self.repo,
                                capture_output=True).returncode == 0
        git(self.repo, "checkout", "-q", *(() if exists else ("-b",)), name)

    def make(self, *args: str, **env: str) -> subprocess.CompletedProcess[str]:
        """`make <args>` as a person types it, with nothing of the outer run's state in the child."""
        names = CI_MARKERS + MAKE_STATE + GIT_STATE + NARROWING
        full = {k: v for k, v in os.environ.items() if k not in names and not k.startswith("GIT_")}
        full.update(STANDIN_LOG=str(self.log), PYTHONDONTWRITEBYTECODE="1", **env)
        return subprocess.run(["make", *args], cwd=self.repo, env=full, text=True, capture_output=True, timeout=180)

    def ran(self) -> list[str]:
        """What has run since the last call, from the log: each stand-in module as `(name, PYTHONPATH)` strings."""
        lines = self.log.read_text(encoding="utf-8").splitlines()
        self.log.write_text("", encoding="utf-8")
        return lines

    def modules_run(self) -> list[str]:
        """The stand-in modules that ran since the last call, sorted."""
        return sorted(line.split("\t")[1] for line in self.ran() if line.startswith("module\t"))

    def pythonpaths(self) -> set[str]:
        """The `PYTHONPATH` each stand-in module saw, since the last call (the log is read once)."""
        return {line.split("\t")[2] for line in self.ran() if line.startswith("module\t")}
