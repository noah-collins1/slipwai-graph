"""T024 of S05-xdist (D108): the plugin loads with autoload off, the page's words on a root module and
`-p no:xdist`, a project with no Python reads a conditional, and a non-finite mark is refused.

Real `uv` and the pinned pytest-xdist for the first rule (skipped, with its reason, where `uv` is absent).
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from support import FactoryTestCase, commit_all
from test_describe_service import describe
from test_migrate import migrate
from test_replay import newer_factory

from slipwai.project.parallel_tests import FLAGS, MARK, NO_PYTHON

sys.dont_write_bytecode = True

CI_NAMES = ("CI", "GITHUB_ACTIONS", "GITLAB_CI")
AUTOLOAD = "PYTEST_DISABLE_PLUGIN_AUTOLOAD"
NO_PYTHON_SENTENCE = (
    "Where `project.json` carries `\"parallelSafe\": true`, a Python service's tests run across cores; "
    "it changes nothing until a Python service is added.\n"
)


def squashed(text: str) -> str:
    return " ".join(text.split())


@unittest.skipUnless(shutil.which("uv"), "uv is not on the PATH, so the plugin cannot be run for real")
class ThePluginLoadsWhateverTheAutoloadSetting(FactoryTestCase):
    def verify(self, repo: Path, autoload_off: bool) -> subprocess.CompletedProcess:
        env = {name: value for name, value in os.environ.items() if name not in (*CI_NAMES, AUTOLOAD)}
        if autoload_off:
            env[AUTOLOAD] = "1"
        return subprocess.run(["./scripts/verify", "--test-only"], cwd=repo, env=env, text=True,
                              capture_output=True, timeout=600)

    def test_workers_start_with_autoload_off_and_no_double_registration_with_it_on(self) -> None:
        with tempfile.TemporaryDirectory() as parent:
            repo = self.generate(parent, "shop", "event-modelling", "python")
            for off in (True, False):
                with self.subTest(autoload_off=off):
                    run = self.verify(repo, off)
                    output = run.stdout + run.stderr
                    self.assertEqual(run.returncode, 0, output)
                    self.assertIn("created:", output)
                    self.assertNotIn("already registered", output)

    def test_the_script_and_the_page_carry_the_same_flags(self) -> None:
        with tempfile.TemporaryDirectory() as parent:
            repo = self.generate(parent, "shop", "event-modelling", "python")
            script = (repo / "scripts/verify").read_text(encoding="utf-8")
            self.assertIn(f'parallel="{FLAGS}"', script)
            self.assertIn(f"`{FLAGS}`", MARK)
            self.assertIn("-p xdist", FLAGS)


class ThePageNamesTheTwoWaysToFailAndTheConditional(unittest.TestCase):
    def test_a_root_module_named_like_a_standard_library_one_crashes_every_worker(self) -> None:
        page = squashed(MARK)
        self.assertIn("module at the project's root is named like a standard-library one (a `json.py`, say)", page)
        self.assertIn("*maximum crashed workers reached*", page)
        self.assertRegex(page, r"rename it or set the mark `false`")

    def test_the_plugin_sentence_names_p_no_xdist_in_addopts_as_the_same_case(self) -> None:
        page = squashed(MARK)
        self.assertIn("a service that removed it fails on an argument error", page)
        self.assertIn("`-p no:xdist` in `PYTEST_ADDOPTS`", page)

    def test_a_project_with_no_python_reads_a_conditional(self) -> None:
        self.assertEqual(NO_PYTHON, NO_PYTHON_SENTENCE)


class ANonFiniteMarkIsRefused(FactoryTestCase):
    def project(self, directory: str, written: str) -> tuple[Path, bytes]:
        repo = self.generate(directory, "shop", "event-modelling", "python")
        path = repo / "project.json"
        text = path.read_text(encoding="utf-8")
        self.assertIn('"parallelSafe": true', text)
        path.write_text(text.replace('"parallelSafe": true', f'"parallelSafe": {written}'), encoding="utf-8")
        commit_all(repo, "a mark that is not a boolean")
        return repo, path.read_bytes()

    def assertRefused(self, run: subprocess.CompletedProcess, written: str) -> None:
        text = run.stdout + run.stderr
        self.assertNotEqual(run.returncode, 0, text)
        lines = [line for line in text.splitlines() if "parallelSafe" in line]
        self.assertEqual(len(lines), 1, text)
        self.assertIn("project.json", lines[0])
        self.assertIn(written, lines[0])
        self.assertRegex(lines[0], r"`true` or `false`|true or false")

    def test_describe_service_refuses_and_writes_nothing(self) -> None:
        for written in ("1e400", "NaN", "-1e400", "Infinity"):
            with self.subTest(written=written), tempfile.TemporaryDirectory() as directory:
                repo, before = self.project(directory, written)
                self.assertRefused(describe(repo, "service", "--purpose", "x"), written)
                self.assertEqual((repo / "project.json").read_bytes(), before)

    def test_migrate_refuses_and_writes_nothing(self) -> None:
        for written in ("1e400", "NaN"):
            with self.subTest(written=written), tempfile.TemporaryDirectory() as directory:
                repo, before = self.project(directory, written)
                factory = newer_factory(Path(directory), "\n## A section a newer factory added\n")
                self.assertRefused(migrate(repo, factory), written)
                self.assertEqual((repo / "project.json").read_bytes(), before)
                status = subprocess.run(["git", "status", "--porcelain"], cwd=repo, text=True, capture_output=True)
                self.assertEqual(status.stdout, "")
