"""What `slipwai migrate` does with the `verify` job's checkout, and the workflow `project_files()` omits.

A project made before this slice has the bare step `- uses: actions/checkout@v6` in its `verify` job. The key
arrives by the same three-way merge as any other change to a factory-owned file: where the step is as
generated it merges silently, where the project wrote a `with:` of its own the two disagree and the file
conflicts, so neither side is lost without the project seeing it. The `ux-gates` extension writes its own
sharded job into `verify.yml`; that job's checkout fetches history too.
"""
from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

from support import FactoryTestCase, commit_all
from test_design_extensions import FAKE_NODE, FAKE_NPX, FAKE_SPECIFY
from test_migrate import migrate
from test_replay import git, newer_factory

from slipwai.scaffold import NO_MAINTENANCE

VERIFY = ".github/workflows/verify.yml"
STEP = "      - uses: actions/checkout@v6\n"
WITH_KEY = STEP + "        with:\n          fetch-depth: 0\n"


def verify_job(workflow: str) -> str:
    """The `verify` job's text: from its two-space key to the next job's."""
    after = workflow.split("\n  verify:\n", 1)[1]
    return after.split("\n  integration", 1)[0] if "\n  integration" in after else after


def made_before_the_slice(repo: Path) -> str:
    """Put the `verify` job's checkout back to the bare step, as the factory's own commit: the root commit is
    amended, so it is the base the next migration measures against, as a project made before this slice has it."""
    path = repo / VERIFY
    text = path.read_text()
    assert text.count(WITH_KEY) == 1, "the generated verify job's checkout carries the key"
    path.write_text(text.replace(WITH_KEY, STEP))
    subprocess.run(["git", "add", VERIFY], cwd=repo, check=True)
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@local", *NO_MAINTENANCE,
                    "commit", "-q", "--amend", "--no-edit"], cwd=repo, check=True)
    assert git(repo, "rev-list", "--count", "HEAD").stdout.strip() == "1", "the project has the one commit"
    return path.read_text()


class CiFetchMigrateTest(FactoryTestCase):
    def test_hold_a_project_made_before_the_slice_gains_the_key_when_it_migrates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "product", "event-modelling", "typescript")
            bare = made_before_the_slice(repo)
            self.assertNotIn("fetch-depth", bare)
            factory = newer_factory(Path(directory), "\n## A section a newer factory added\n")

            result = migrate(repo, factory)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(git(repo, "status", "--porcelain").stdout, "")
            merged = (repo / VERIFY).read_text()
            self.assertIn(WITH_KEY, verify_job(merged), "the key arrives on the verify job's checkout")
            self.assertEqual(merged.count("fetch-depth"), 1, "and only there")

    def test_hold_a_project_that_wrote_its_own_with_meets_the_key_as_a_conflict_and_loses_neither_side(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "product", "event-modelling", "typescript")
            made_before_the_slice(repo)
            own = repo / VERIFY
            own.write_text(own.read_text().replace(STEP, STEP + "        with:\n          submodules: true\n", 1))
            commit_all(repo, "The project fetches its submodules")
            head = git(repo, "rev-parse", "HEAD").stdout.strip()
            factory = newer_factory(Path(directory), "\n## A section a newer factory added\n")

            result = migrate(repo, factory)

            # `migrate` stops with the merge in progress and names the file, as for any both-changed hunk.
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("stopped at 1 conflict(s)", result.stdout)
            self.assertIn(f"\n  {VERIFY}\n", result.stdout)
            self.assertEqual(git(repo, "diff", "--name-only", "--diff-filter=U").stdout.split(), [VERIFY])
            self.assertTrue((repo / ".git/MERGE_HEAD").is_file())
            conflicted = (repo / VERIFY).read_text()
            self.assertIn("<<<<<<<", conflicted)
            self.assertIn(">>>>>>>", conflicted)
            self.assertIn("submodules: true", conflicted, "the project's line is still there")
            self.assertIn("fetch-depth: 0", conflicted, "and so is the factory's")
            git(repo, "merge", "--abort")
            self.assertEqual(git(repo, "rev-parse", "HEAD").stdout.strip(), head)
            self.assertNotIn("fetch-depth", (repo / VERIFY).read_text(), "an abort gives the project's own back")

    def test_hold_the_ux_gates_job_checks_out_with_full_history(self) -> None:
        """The extension writes its job after generation, so `project_files()` never returns it."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "scaled", frontend="react-vite")
            fake_bin = Path(directory) / "fake-bin"
            fake_bin.mkdir()
            for name, body in (("npx", FAKE_NPX), ("node", FAKE_NODE), ("specify", FAKE_SPECIFY)):
                (fake_bin / name).write_text(body)
                (fake_bin / name).chmod(0o755)
            environment = os.environ | {"PATH": f"{fake_bin}:{os.environ['PATH']}", "NPX_LOG": f"{directory}/n",
                                        "NODE_LOG": f"{directory}/node-calls", "FAKE_BROWSER": "chrome"}
            subprocess.run(["./init", "--integration", "codex", "--extension", "ux-gates"], cwd=repo, check=True,
                           env=environment, capture_output=True)

            workflow = (repo / VERIFY).read_text()

            job = workflow.split("\n  ux-gates:\n", 1)[1]
            first_step = job.split("      - uses: actions/setup-node", 1)[0]
            self.assertIn(WITH_KEY, first_step, "the ux-gates job's checkout, as written, fetches history")
