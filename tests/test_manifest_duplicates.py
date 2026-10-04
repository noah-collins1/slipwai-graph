"""D107 (T023): a key written twice in `project.json` is refused by every command that reads it, before anything is
written or committed — B1, where `add-service`, `describe-service` and `adopt --refresh` kept the last copy and turned
a person's `false` into the generated `true`."""
from __future__ import annotations

import os
import re
import subprocess
import tempfile
from pathlib import Path

from support import FactoryTestCase, commit_all
from test_add_service import add_service
from test_candidates import adopted
from test_describe_service import describe

from slipwai.assets import ROOT
from slipwai.errors import GenerationError
from slipwai.manifest import keys_written_twice, parse_manifest

KEY = "parallelSafe"
ENVIRONMENT = {name: value for name, value in os.environ.items() if name not in ("CI", "GITHUB_ACTIONS", "GITLAB_CI")}


def head(repo: Path) -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, text=True, capture_output=True).stdout.strip()


def after_name(repo: Path, line: str) -> None:
    """Write `line` right after the `"name"` line of the project's `project.json`, and commit it."""
    path = repo / "project.json"
    text = path.read_text(encoding="utf-8")
    path.write_text(re.sub(r'(\n  "name": [^\n]*\n)', lambda found: found.group(1) + line + "\n", text, count=1),
                    encoding="utf-8")
    commit_all(repo, "a key written by hand")


def b1_file(repo: Path) -> None:
    """The reproduced file: the person's `false` after `"name"`, the generated `true` after `"target"`."""
    after_name(repo, f'  "{KEY}": false,')
    path = repo / "project.json"
    text = path.read_text(encoding="utf-8")
    if text.count(f'"{KEY}"') < 2:  # an adopted project records no mark of its own: add the generated copy
        path.write_text(re.sub(r'(\n  "target": [^\n]*\n)', lambda found: found.group(1) + f'  "{KEY}": true,\n', text,
                               count=1), encoding="utf-8")
        commit_all(repo, "the generated copy")
        text = path.read_text(encoding="utf-8")
    assert text.count(f'"{KEY}"') == 2, text


def gate_reads_serial(repo: Path) -> bool:
    """The generated gate's own reader of the mark, run on this project: serial where the key is written twice."""
    script = (repo / "scripts/verify").read_text(encoding="utf-8")
    reader = re.search(r"python3 -I -c '(import json,sys; once=.*?)' >/dev/null", script)
    assert reader, "the generated gate no longer carries the reader this test runs"
    return subprocess.run(["python3", "-I", "-c", reader.group(1)], cwd=repo).returncode != 0


class Untouched:
    """What a refused command leaves: the file byte for byte, no new commit, nothing in the tree."""

    def __init__(self, test: FactoryTestCase, repo: Path) -> None:
        self.test, self.repo = test, repo
        self.text = (repo / "project.json").read_bytes()
        self.commit = head(repo)

    def check(self, result: subprocess.CompletedProcess, key: str = KEY) -> None:
        self.test.assertNotEqual(result.returncode, 0, result.stdout)
        # The CLI's own error path ends in one `error:` line, after whatever usage the parser printed.
        errors = [line for line in result.stderr.splitlines() if ": error: " in line]
        self.test.assertEqual(len(errors), 1, result.stderr)
        message = errors[0]
        self.test.assertIn(f'project.json has "{key}" twice', message)
        self.test.assertIn("keep one copy", message)
        self.test.assertEqual((self.repo / "project.json").read_bytes(), self.text)
        self.test.assertEqual(head(self.repo), self.commit)
        status = subprocess.run(["git", "status", "--porcelain"], cwd=self.repo, text=True, capture_output=True)
        self.test.assertEqual(status.stdout, "")


class TheReaderRefusesAKeyWrittenTwice(FactoryTestCase):
    def test_at_any_depth_and_names_the_path(self) -> None:
        self.assertEqual(keys_written_twice('{"a": 1, "b": {"c": 1, "c": 2}, "d": [{"e": 1, "e": 2}], "a": 3}'),
                         ["a", "b.c", "d.0.e"])
        self.assertEqual(keys_written_twice('{"a": {"b": 1}, "c": {"b": 1}}'), [])
        with self.assertRaisesRegex(GenerationError, r'project.json has "b.c" twice; keep one copy'):
            parse_manifest('{"b": {"c": 1, "c": 2}}')


class AddServiceDescribeAndRefreshRefuseTheB1File(FactoryTestCase):
    def test_add_service_refuses_and_changes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "shop", "event-modelling", "python")
            b1_file(repo)
            untouched = Untouched(self, repo)

            untouched.check(add_service(repo, "billing", "--language", "go"))

            self.assertTrue(gate_reads_serial(repo))
            self.assertFalse((repo / "apps/billing").exists())

    def test_describe_service_refuses_and_changes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "shop", "event-modelling", "python")
            b1_file(repo)
            untouched = Untouched(self, repo)

            untouched.check(describe(repo, "service", "--purpose", "Keeps the ledger."))

            self.assertTrue(gate_reads_serial(repo))

    def test_adopt_refresh_refuses_and_changes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = adopted(Path(directory))
            b1_file(repo)
            untouched = Untouched(self, repo)

            result = subprocess.run([str(ROOT / "slipwai"), "adopt", "--refresh"], cwd=repo, text=True,
                                    capture_output=True, stdin=subprocess.DEVNULL, env=ENVIRONMENT)

            untouched.check(result)
            self.assertNotIn("refreshed", result.stdout)


class EveryKeyAtEveryDepthIsCovered(FactoryTestCase):
    def test_a_duplicate_inside_a_deployable_is_refused_the_same_way(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "shop", "event-modelling", "python")
            path = repo / "project.json"
            text = path.read_text(encoding="utf-8")
            path.write_text(text.replace('"port": 3000,', '"port": 3000,\n      "port": 3001,', 1), encoding="utf-8")
            commit_all(repo, "a port twice")

            Untouched(self, repo).check(add_service(repo, "billing"), "deployables.service.port")

    def test_ci_branch_written_twice_is_refused_through_add_service(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "shop", "event-modelling", "python")
            after_name(repo, '  "ci": {"branch": "main", "forge": "none", "branch": "trunk"},')

            Untouched(self, repo).check(add_service(repo, "billing"), "ci.branch")
