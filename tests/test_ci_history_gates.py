"""With the history a forge's pull-request checkout now carries, the other two history gates answer as on a full
clone (S24, R5; AC-S24-8; D54).

D54's skipper ran the shipped `check-migrations.py` and both targets' `check-flags.py` by hand in scratch
repositories: at depth 1 with no trunk ref both exit 0, with every branch fetched both exit 1 on an expand and its
contract together and on a flag seeded `on`, and on a push to the trunk both exit 0 at either depth. These tests are
that run, kept. Every one is a hold: the slice changes no line of the three scripts. Each runs a script's command
line, with the forges' variables removed unless a test sets them, on a checkout built with git itself
(`tests/forge_checkout.py` for the pull request).
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from forge_checkout import pull_request_checkout, run

from slipwai.assets import ROOT

TOOLKIT = ROOT / "assets/toolkit/scripts"
FLAG_SCRIPTS = {path.parents[1].name: path
                for path in sorted((ROOT / "assets/targets").glob("*/scripts/check-flags.py"))}
GITHUB = {"CI": "true", "GITHUB_ACTIONS": "true", "GITHUB_HEAD_REF": "feature/x", "GITHUB_BASE_REF": "main"}
GITLAB = {"GITLAB_CI": "true", "CI_COMMIT_REF_NAME": "feature/x", "CI_MERGE_REQUEST_TARGET_BRANCH_NAME": "main"}
FORGES = {"github": GITHUB, "gitlab": GITLAB}
FORGE_VARIABLES = ("CI", "GITHUB_ACTIONS", "GITLAB_CI", "GITHUB_HEAD_REF", "GITHUB_BASE_REF",
                   "CI_COMMIT_REF_NAME", "CI_MERGE_REQUEST_TARGET_BRANCH_NAME")
MANIFEST = '{"deployables": {"service": {"kind": "service", "path": "apps/service"}}}\n'
EXPAND = "ALTER TABLE orders ADD COLUMN status text;\n"
CONTRACT = "-- contract: 202610010900_orders_add_status\nALTER TABLE orders DROP COLUMN legacy;\n"
READER = "def handle(environment):\n    return flag_enabled('checkout-v2', environment)\n"
TESTS = ("def test_on():\n    assert handle({'FLAG_CHECKOUT_V2': 'on'})\n\n"
         "def test_off():\n    assert not handle({})\n")
SEED = 'flags = {{\n  service = {{\n    checkout-v2 = "{}"\n  }}\n}}\n'


def write(repo: Path, relative: str, text: str) -> None:
    (repo / relative).parent.mkdir(parents=True, exist_ok=True)
    (repo / relative).write_text(text, encoding="utf-8")


def commit(repo: Path, message: str, *paths: str) -> None:
    run(repo, "add", "--", *paths)
    run(repo, "commit", "-q", "-m", message)


def environment(extra: dict[str, str]) -> dict[str, str]:
    """This process's environment with every forge variable removed, then `extra` set."""
    return {**{k: v for k, v in os.environ.items() if k not in FORGE_VARIABLES}, **extra}


class CiHistoryGatesTest(unittest.TestCase):
    def origin(self, target: str) -> Path:
        """A project on `main` carrying the shipped gates, the flag's reader and tests."""
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.scratch = Path(directory.name)
        repo = self.scratch / "origin"
        repo.mkdir()
        run(repo, "init", "-q", "-b", "main")
        for name, source in (("check-migrations.py", TOOLKIT / "check-migrations.py"),
                             ("check-flags.py", FLAG_SCRIPTS[target]),
                             ("check-slice-scope.py", TOOLKIT / "check-slice-scope.py")):
            (repo / "scripts").mkdir(exist_ok=True)
            shutil.copy(source, repo / "scripts" / name)
        (repo / "scripts/event-model").mkdir()
        shutil.copy(TOOLKIT / "event-model/check.py", repo / "scripts/event-model")
        write(repo, "project.json", MANIFEST)
        write(repo, "apps/service/handler.py", READER)
        write(repo, "apps/service/tests/test_handler.py", TESTS)
        write(repo, "infra/service/flags.auto.tfvars", "flags = {\n}\n")
        commit(repo, "base", ".")
        return repo

    def pull_request(self, target: str, depth: int | None) -> Path:
        """The pull-request checkout of `feature/x`; the expand is new in it, being committed in the same branch."""
        origin = self.origin(target)
        run(origin, "checkout", "-q", "-b", "feature/x")
        write(origin, "apps/service/migrations/202610010900_orders_add_status.sql", EXPAND)
        write(origin, "apps/service/migrations/202610011000_orders_drop_legacy.sql", CONTRACT)
        write(origin, "infra/service/flags.auto.tfvars", SEED.format("on"))
        commit(origin, "expand, contract and a flag seeded on", "apps/service", "infra")
        run(origin, "checkout", "-q", "main")
        return pull_request_checkout(origin, "feature/x", self.scratch, depth=depth)

    def trunk(self, target: str, depth: int | None) -> Path:
        """The same commits pushed to `main`: a clone of the trunk, whole or at depth 1."""
        origin = self.origin(target)
        write(origin, "apps/service/migrations/202610010900_orders_add_status.sql", EXPAND)
        commit(origin, "the expand", "apps/service")
        write(origin, "apps/service/migrations/202610011000_orders_drop_legacy.sql", CONTRACT)
        write(origin, "infra/service/flags.auto.tfvars", SEED.format("on"))
        commit(origin, "the contract and a flag seeded on", "apps/service", "infra")
        clone = self.scratch / "trunk"
        shallow = ["--depth", "1"] if depth else []
        run(self.scratch, "clone", "-q", *shallow, f"file://{origin}", str(clone))
        return clone

    def gate(self, clone: Path, script: str, forge: dict[str, str]) -> subprocess.CompletedProcess:
        return subprocess.run(["python3", f"scripts/{script}"], cwd=clone, text=True, capture_output=True,
                              env=environment(forge))

    def holds(self, clone: Path, forge: dict[str, str], *, refused: bool) -> None:
        """Both gates on `clone`: refused with their reason, or exit 0."""
        for script, reason in (("check-migrations.py", "is new in this same change"),
                               ("check-flags.py", 'new in this change and seeded "on"')):
            result = self.gate(clone, script, forge)
            if refused:
                self.assertEqual(result.returncode, 1, f"{script}: {result.stdout}{result.stderr}")
                self.assertIn(reason, result.stderr, script)
            else:
                self.assertEqual(result.returncode, 0, f"{script}: {result.stdout}{result.stderr}")

    def test_hold_there_is_a_flag_script_per_target(self) -> None:
        """The sweep's list: aws and azure each ship one, and each is covered below."""
        self.assertEqual(sorted(FLAG_SCRIPTS), ["aws", "azure"])

    def test_hold_a_pull_request_with_history_is_refused_by_both_gates(self) -> None:
        """e1 (check-migrations) and e2 (check-flags), the full-history checkout, per target and per forge."""
        for target in FLAG_SCRIPTS:
            clone = self.pull_request(target, None)
            for forge, variables in FORGES.items():
                with self.subTest(target=target, forge=forge):
                    self.holds(clone, variables, refused=True)

    def test_hold_a_pull_request_at_depth_one_is_not_refused(self) -> None:
        """e1 and e2: with no trunk ref the gates have no base and say nothing (why the verify job fetches it all)."""
        for target in FLAG_SCRIPTS:
            clone = self.pull_request(target, 1)
            self.assertEqual(run(clone, "for-each-ref", "refs/remotes"), "")
            for forge, variables in FORGES.items():
                with self.subTest(target=target, forge=forge):
                    self.holds(clone, variables, refused=False)

    def test_hold_the_same_commits_on_the_trunk_pass_at_either_depth(self) -> None:
        """e3: on `main` itself nothing committed counts as new, whole clone or depth 1, both forges."""
        for target in FLAG_SCRIPTS:
            for depth in (None, 1):
                clone = self.trunk(target, depth)
                for forge, variables in FORGES.items():
                    with self.subTest(target=target, depth=depth, forge=forge):
                        self.holds(clone, variables, refused=False)

    def test_hold_slice_scope_has_nothing_to_hold_on_a_feature_branch(self) -> None:
        """e4: the pull-request checkout from `feature/x` is not a `slice/<id>` branch: said so, exit 0."""
        clone = self.pull_request("aws", None)
        for forge, variables in FORGES.items():
            with self.subTest(forge=forge):
                result = self.gate(clone, "check-slice-scope.py", variables)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("nothing to hold", result.stdout)


if __name__ == "__main__":
    unittest.main()
