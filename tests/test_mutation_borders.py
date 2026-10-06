"""S08 T003 (rule 2 · AC-S08-1, AC-S08-15): the checkouts that sweep say so, then sweep.

Real `git` in a generated Go project, copied per example, on `main` or on `slice/S1`; `--make` is a fake executable
that logs its arguments, so the evidence is the line the script printed, the calls the fake saw and the status.
"""
from __future__ import annotations

import importlib.util
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from stamp_fixture import CI_MARKERS, GIT_STATE, MAKE_STATE, git
from support import FactoryTestCase
from test_parallel_gate_adopted import confirmed

from slipwai.assets import ROOT

sys.dont_write_bytecode = True
SLICE = "slice/S1"
SWEEPS = "mutation: the sweep runs — "
FULL = ["--no-print-directory", "-f", "Makefile", "mutation-full"]


def clean_environment(**extra: str) -> dict[str, str]:
    """The machine's environment without CI, make or git state (and `SINCE`), then what the example sets."""
    kept = {k: v for k, v in os.environ.items() if k not in CI_MARKERS + MAKE_STATE + GIT_STATE + ("SINCE",)}
    return {**kept, **extra}


def fake_make(directory: Path, status: int = 0) -> tuple[Path, Path]:
    """An executable that logs its arguments one per line, `--` after each call, and exits with `status`."""
    log = directory / "make.log"
    program = directory / "fake-make"
    program.write_text(f'#!/bin/sh\nprintf \'%s\\n\' "$@" >> "{log}"\necho -- >> "{log}"\nexit {status}\n',
                       encoding="utf-8")
    program.chmod(program.stat().st_mode | stat.S_IXUSR)
    return program, log


def calls(log: Path) -> list[list[str]]:
    """Each call the fake make logged, as its argument list."""
    if not log.exists():
        return []
    found: list[list[str]] = [[]]
    for line in log.read_text(encoding="utf-8").splitlines():
        found.append([]) if line == "--" else found[-1].append(line)
    return found[:-1]


def loaded(script: Path) -> Any:
    """The project's own copy of the script, as a module: it finds the root and the trunk by where it sits."""
    spec = importlib.util.spec_from_file_location("mutation_scope_under_test", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    was, sys.dont_write_bytecode = sys.dont_write_bytecode, True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = was
    return module


class BordersTest(FactoryTestCase):
    """A generated single-service Go project, copied per example, on `main`; the fake make is beside it."""

    longMessage = False
    template: Path | None = None
    parent: Path

    @classmethod
    def setUpClass(cls) -> None:
        cls.parent = Path(tempfile.mkdtemp(prefix="mutation-borders-"))
        cls.addClassCleanup(shutil.rmtree, cls.parent, ignore_errors=True)
        cls.template = cls().generate(cls.parent, "scoped", "standard", "go", http="none")

    def setUp(self) -> None:
        assert self.template is not None
        self.repo = Path(tempfile.mkdtemp(dir=self.parent)) / "project"
        shutil.copytree(self.template, self.repo, symlinks=True)
        self.tools = Path(tempfile.mkdtemp(dir=self.parent))
        self.make, self.log = fake_make(self.tools)

    def run_script(self, *services: str, env: dict[str, str] | None = None, status: int | None = None,
                   cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
        """The script as the recipe calls it, with the fake make; the project's one service by default."""
        if status is not None:
            self.make, self.log = fake_make(self.tools, status)
        words = services if services else ("go:apps/service",)
        before = git(self.repo, "status", "--porcelain", "--ignored") if (self.repo / ".git").exists() else ""
        done = subprocess.run(
            ["python3", "-B", "scripts/mutation-scope.py", "--make", str(self.make), "--makefile", "Makefile", *words],
            cwd=cwd or self.repo, env=env if env is not None else clean_environment(), text=True,
            capture_output=True, timeout=120)
        if (self.repo / ".git").exists():
            self.assertEqual(git(self.repo, "status", "--porcelain", "--ignored"), before, "a byte moved")
        return done

    def sweeps(self, done: subprocess.CompletedProcess[str], reason: str, status: int = 0) -> None:
        self.assertEqual(done.stdout.splitlines()[:1], [SWEEPS + reason], done.stdout + done.stderr)
        self.assertEqual(calls(self.log), [FULL])
        self.assertEqual(done.returncode, status, done.stderr)

    def test_e1_the_trunk_says_so_and_sweeps_with_the_makes_status(self) -> None:
        self.sweeps(self.run_script(status=5), "this is the trunk (`main`)", 5)

    def test_e2_a_branch_that_is_not_a_slice(self) -> None:
        git(self.repo, "checkout", "-q", "-b", "feature/x")
        self.sweeps(self.run_script(), "`feature/x` is not a slice/<id> branch")

    def test_e3_a_detached_head(self) -> None:
        git(self.repo, "checkout", "-q", "--detach")
        self.sweeps(self.run_script(), "HEAD is detached")

    def test_e4_each_ci_marker(self) -> None:
        git(self.repo, "checkout", "-q", "-b", SLICE)
        for marker in CI_MARKERS:
            with self.subTest(marker=marker):
                self.log.unlink(missing_ok=True)
                self.sweeps(self.run_script(env=clean_environment(**{marker: "1"})),
                            f"{marker} is set, so this is a CI run")

    def test_e5_a_slice_branch_with_no_trunk_has_no_usable_base(self) -> None:
        git(self.repo, "checkout", "-q", "-b", SLICE)
        git(self.repo, "branch", "-q", "-D", "main")
        done = self.run_script()
        first = (done.stdout.splitlines() or [""])[0]
        self.assertTrue(first.startswith(SWEEPS + f"{SLICE} has no usable base"), first + done.stderr)
        self.assertEqual(calls(self.log), [FULL])

    def test_e6_a_directory_git_cannot_read_still_sweeps(self) -> None:
        shutil.rmtree(self.repo / ".git")
        done = self.run_script()
        self.assertTrue(done.stdout.startswith(SWEEPS), done.stdout + done.stderr)
        self.assertEqual(calls(self.log), [FULL])
        self.assertEqual(done.returncode, 0)

    def test_e7_an_empty_since_is_the_sweep(self) -> None:
        git(self.repo, "checkout", "-q", "-b", SLICE)
        self.sweeps(self.run_script(env=clean_environment(SINCE="")), "SINCE is set and empty")

    def test_e7_where_two_hold_the_first_only_is_printed(self) -> None:
        done = self.run_script(env=clean_environment(CI="1"))  # on `main`: the CI border comes before the trunk's
        self.assertEqual(done.stdout.count("mutation: "), 1, done.stdout)
        self.sweeps(done, "CI is set, so this is a CI run")

    def test_e8_a_border_that_raises_is_a_sweep_not_a_crash(self) -> None:
        class Unreadable:
            def __getattr__(self, name: str) -> Any:
                raise OSError("no such thing")

        reason = loaded(self.repo / "scripts/mutation-scope.py").sweep_reason(clean_environment(), Unreadable())
        self.assertTrue(str(reason).startswith("the checkout could not be read ("), reason)

    def test_e8_a_slice_branch_with_a_base_is_not_a_sweep(self) -> None:
        git(self.repo, "checkout", "-q", "-b", SLICE)
        os.chdir(self.repo)
        self.addCleanup(os.chdir, ROOT)
        module = loaded(self.repo / "scripts/mutation-scope.py")
        self.assertIsNone(module.sweep_reason(clean_environment(), module.ground()))

    def test_e9_an_adopted_layout_runs_the_recorded_command_without_a_scope(self) -> None:
        repo = confirmed(self.parent)
        done = subprocess.run(["make", "-f", "delivery/Makefile", "mutation"], cwd=repo, env=clean_environment(),
                              text=True, capture_output=True, timeout=120)
        first = (done.stdout.splitlines() or [""])[0]
        self.assertEqual(first, "mutation: this layout has no mutation scope — the recorded command runs",
                         done.stdout + done.stderr)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)

    def test_e9_an_adopted_layout_sweeps_through_the_makefile_it_was_given(self) -> None:
        (self.repo / "project.json").write_text(
            (self.repo / "project.json").read_text(encoding="utf-8").rstrip().removesuffix("}")
            + ', "layout": {"delivery": "delivery"}}', encoding="utf-8")
        done = self.run_script()
        self.assertEqual(done.stdout.splitlines()[:1],
                         ["mutation: this layout has no mutation scope — the recorded command runs"])
        self.assertEqual(calls(self.log), [FULL])

    def test_e11_no_generated_service_is_the_sweep(self) -> None:
        git(self.repo, "checkout", "-q", "-b", SLICE)
        command = ["python3", "-B", "scripts/mutation-scope.py", "--make", str(self.make), "--makefile", "Makefile"]
        zero = subprocess.run(command, cwd=self.repo, env=clean_environment(), text=True, capture_output=True,
                              timeout=120)
        self.assertEqual(zero.stdout.splitlines()[:1], [SWEEPS + "no generated service to scope"], zero.stderr)

    def test_e12_an_index_the_stamp_will_not_vouch_for_is_the_sweep_with_that_borders_words(self) -> None:
        """T035(b), S06 T044's `index`: an assume-unchanged production file hides its edit from git, so the run was
        *no mutant to run*; now it sweeps and says why."""
        git(self.repo, "checkout", "-q", "-b", SLICE)
        source = next((self.repo / "apps/service").rglob("*.go"))
        relative = str(source.relative_to(self.repo))
        git(self.repo, "update-index", "--assume-unchanged", relative)
        source.write_text(source.read_text(encoding="utf-8") + "\n// an edit\n", encoding="utf-8")
        os.chdir(self.repo)
        self.addCleanup(os.chdir, ROOT)
        module = loaded(self.repo / "scripts/mutation-scope.py")
        words = module.scoped_gate().index(module.ground())
        self.assertIn("assume-unchanged", str(words))
        self.sweeps(self.run_script(), str(words))

    def test_e10_every_border_leaves_the_project_as_it_was(self) -> None:
        """HOLD: `run_script` compares `git status --porcelain --ignored` before and after each run; here the
        borders of e1 to e7 run in one project in turn."""
        for arguments in (["main"], ["feature/y"], ["slice/S2"]):
            git(self.repo, "checkout", "-q", "-B", arguments[0])
            self.run_script()
            self.run_script(env=clean_environment(CI="1"))
            self.run_script(env=clean_environment(SINCE=""))
        self.assertFalse((self.repo / "scripts/__pycache__").exists())
