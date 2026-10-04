"""The gate `slipwai adopt` writes fetches history, on both forges (S24 R2, AC-S24-2 and AC-S24-3).

A pull request's checkout of one commit gives `check-slice-scope` nothing to compare with, so the `verify` job of
the Actions file and `verify-delivery` of the GitLab job ask the forge for full history. The `smoke` job and
`smoke-delivery` are not the gate and keep the forge's default; no `rules:` is added, since when the job runs is
the repository's own configuration's to say. Every repository here is adopted through the command line.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from support import FactoryTestCase
from test_adopt import repository, slipwai
from test_ci_fetch_generated import checks_named, verify_chain
from test_replay import git

ACTIONS = ".github/workflows/verify-delivery.yml"
GITLAB = "delivery/ci/verify-delivery.gitlab-ci.yml"
FILES = {
    "package.json": json.dumps({"name": "shop", "scripts": {"test": "node --test", "start": "node app.js"}}),
    "app.js": "console.log('listening');\n",
    "smoke.js": "console.log('shop answers');\n",
    "test/a.test.js": 'require("node:test")("a", () => {});\n',
}
FULL_HISTORY = (
    "      # Full history: `check-slice-scope` and `check-migrations`, and `check-flags` where the project has one,\n"
    "      # compare this change with the trunk, and a checkout of one commit gives them nothing to compare with.\n"
    "      - uses: actions/checkout@v6\n        with:\n          fetch-depth: 0\n"
)
GIT_DEPTH = (
    "  stage: test\n  variables:\n    # Full history: the gate's checks compare this change with the trunk.\n"
    '    GIT_DEPTH: "0"\n'
)


def adopted(parent: Path, name: str, forge: str, smoke: bool) -> Path:
    """The application is named by its directory: each case gets a directory of its own, the repository is `shop`."""
    repo = repository(parent / name, "shop", FILES)
    arguments = ["adopt", "--yes", "--forge", forge]
    if smoke:
        arguments += ["--command", "shop:smoke=node smoke.js"]
    result = slipwai(repo, *arguments)
    assert result.returncode == 0, result.stderr
    return repo


def job(text: str, name: str) -> str:
    """The text of one top-level job of a workflow, from its `  name:` line to the next job's."""
    start = text.index(f"\n  {name}:\n") + 1
    following = text.find("\n  smoke:\n", start + 1)
    return text[start:] if following == -1 else text[start:following + 1]


def gitlab_job_text(text: str, name: str) -> str:
    start = text.index(f"\n{name}:\n") + 1
    following = text.find("\nsmoke-delivery:\n", start + 1)
    return text[start:] if following == -1 else text[start:following + 1]


class AdoptedGateFetchesHistory(FactoryTestCase):
    def test_the_github_verify_job_carries_full_history_and_the_smoke_job_does_not(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            text = (adopted(Path(directory), "a", "github", smoke=True) / ACTIONS).read_text()
        self.assertIn(FULL_HISTORY, job(text, "verify"))
        smoke = job(text, "smoke")
        # A hold, green before the change: the smoke job is not the gate, and keeps the forge's default depth.
        self.assertIn("      - uses: actions/checkout@v6\n", smoke)
        self.assertNotIn("fetch-depth", smoke)
        self.assertEqual(text.count("fetch-depth"), 1)

    def test_the_gitlab_gate_job_carries_git_depth_and_the_smoke_job_and_rules_are_untouched(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            text = (adopted(Path(directory), "a", "gitlab", smoke=True) / GITLAB).read_text()
        self.assertIn(GIT_DEPTH, gitlab_job_text(text, "verify-delivery"))
        smoke = text[text.index("\nsmoke-delivery:\n"):]
        # Holds, green before the change.
        self.assertNotIn("variables:", smoke)
        self.assertNotIn("GIT_DEPTH", smoke)
        self.assertNotIn("rules:", text)
        self.assertEqual(text.count("GIT_DEPTH"), 1)

    def test_every_forge_with_and_without_a_smoke_command_fetches_history_once_in_the_gate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            for forge, path in (("github", ACTIONS), ("gitea", ACTIONS), ("gitlab", GITLAB)):
                for smoke in (False, True):
                    with self.subTest(forge=forge, smoke=smoke):
                        repo = adopted(Path(directory), f"{forge}-{smoke}", forge, smoke)
                        text = (repo / path).read_text()
                        if path == ACTIONS:
                            self.assertIn(FULL_HISTORY, job(text, "verify"))
                            self.assertEqual(text.count("fetch-depth"), 1)
                        else:
                            self.assertIn(GIT_DEPTH, gitlab_job_text(text, "verify-delivery"))
                            self.assertEqual(text.count("GIT_DEPTH"), 1)
                            self.assertNotIn("rules:", text)

    def test_every_check_the_comment_names_without_a_clause_is_in_the_verify_chain_beside_it(self) -> None:
        """T013: an adopted repository has no `check-flags`, so the comment names it only where the project has one."""
        with tempfile.TemporaryDirectory() as directory:
            for forge in ("github", "gitea"):
                with self.subTest(forge=forge):
                    repo = adopted(Path(directory), forge, forge, smoke=False)
                    named = checks_named((repo / ACTIONS).read_text())
                    chain = verify_chain((repo / "delivery/Makefile").read_text())
                    self.assertIn("check-slice-scope", named)
                    self.assertTrue(named <= chain, named - chain)
            self.assertNotIn("check-flags", verify_chain((repo / "delivery/Makefile").read_text()))

    def test_a_refresh_writes_the_file_adopt_first_wrote(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            for forge, path in (("github", ACTIONS), ("gitlab", GITLAB)):
                with self.subTest(forge=forge):
                    repo = adopted(Path(directory), forge, forge, smoke=True)
                    first = (repo / path).read_text()
                    (repo / path).write_text("stale\n")
                    git(repo, "add", "-A")
                    git(repo, "-c", "user.name=t", "-c", "user.email=t@local", "commit", "-q", "-m", "stale")
                    refreshed = slipwai(repo, "adopt", "--refresh")
                    self.assertEqual(refreshed.returncode, 0, refreshed.stderr)
                    self.assertEqual((repo / path).read_text(), first)


class AdoptedReportSaysWhatACiOfYourOwnNeeds(FactoryTestCase):
    """T017 (D86): where `adopt` writes no CI, the report says the job needs the trunk's branch to compare with."""

    def test_the_ci_line_for_other_and_for_none_ends_on_a_full_clone_with_the_trunks_branch_fetched(self) -> None:
        tail = "on a full clone with the trunk's branch fetched."
        with tempfile.TemporaryDirectory() as directory:
            for forge in ("other", "none"):
                with self.subTest(forge=forge):
                    repo = repository(Path(directory) / forge, "shop", FILES)
                    result = slipwai(repo, "adopt", "--yes", "--forge", forge)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    line = next(row for row in result.stdout.splitlines() if row.startswith("CI:"))
                    self.assertIn("`make -f delivery/Makefile verify` " + tail, line)
                    self.assertTrue(line.endswith(tail), line)
