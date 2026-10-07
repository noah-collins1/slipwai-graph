"""The existence of an ignored projection directory reaches the scoped gate (T016, gaps finding 1).

`check-agents` (`agents/project.py`'s `unprojected`) and `check-speckit` (`unprojected_directory`) decide what they hold
by whether a git-ignored projection directory exists, and the baseline's ignored digest records files and links, never a
directory. So `mkdir .claude/skills` after a baseline flips `check-agents` without a changed path or a digest change.
A projection directory with no file under it, at any depth, therefore runs the full gate, naming it; one with a file
is the digest's, and does not.
"""
from __future__ import annotations

import json
import subprocess
import sys

from scoped_fixture import ShapeCase
from stamp_fixture import git

sys.dont_write_bytecode = True

DRY: dict[str, str | None] = {"STANDIN_DRY": "1"}
LINE = "verify-scoped: "
WHY = "an ignored projection directory with no files, whose existence the baseline cannot see"


def said(directory: str) -> str:
    return f"{LINE}dependency knowledge was incomplete for {directory} — {WHY}"


class ProjectionDirectoryTest(ShapeCase):
    shape = "model-typescript-web"

    def setUp(self) -> None:
        super().setUp()
        (self.repo / ".specify").mkdir(exist_ok=True)
        (self.repo / ".specify/integration.json").write_text(
            json.dumps({"installed_integrations": ["claude"], "default_integration": "claude"}), encoding="utf-8")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "claude recorded")
        git(self.repo, "branch", "-f", "main", "HEAD")

    def check_agents(self) -> int:
        return subprocess.run([sys.executable, "-B", "scripts/agents/project.py", "--check"], cwd=self.repo,
                              capture_output=True, timeout=60).returncode

    def hollow(self, *directories: str, baseline: bool = True,
               filled: str | None = None) -> subprocess.CompletedProcess[str]:
        """`directories` made after (or, `baseline=False`, before) a baseline; `filled` gets a file first."""
        def make() -> None:
            for directory in directories:
                (self.repo / directory).mkdir(parents=True, exist_ok=True)
            if filled:
                (self.repo / filled).write_text("x\n", encoding="utf-8")
        if not baseline:
            make()
        self.write_baseline()
        if baseline:
            make()
        return self.scoped(env=DRY)

    def test_e1_an_empty_skills_directory_after_the_baseline_runs_the_full_gate_naming_it(self) -> None:
        self.assertEqual(self.check_agents(), 0)
        run = self.hollow(".claude/skills")
        self.assertEqual(self.check_agents(), 1, "the premise: the directory alone flips the check")
        self.assertIn(said(".claude/skills/"), self.scoped_lines(run))
        self.assertTrue(self.verify_calls(), run.stdout)
        self.assertNotIn("check-agents", self.decided(run)[1])

    def test_e2_an_installed_integrations_agents_directory_is_one_too(self) -> None:
        run = self.hollow(".claude/agents")
        self.assertIn(said(".claude/agents/"), self.scoped_lines(run))
        self.assertTrue(self.verify_calls(), run.stdout)

    def test_e3_a_directory_holding_only_empty_directories_has_no_file_under_it(self) -> None:
        run = self.hollow(".claude/commands/nested/deeper")
        self.assertIn(said(".claude/commands/"), self.scoped_lines(run))

    def test_e4_check_speckit_reads_registry_directories_of_harnesses_not_installed_too(self) -> None:
        run = self.hollow(".bob/skills")
        self.assertIn(said(".bob/skills/"), self.scoped_lines(run))
        self.assertTrue(self.verify_calls(), run.stdout)

    def test_e5_a_directory_with_a_file_is_not_this_rules_the_digest_covers_it(self) -> None:
        self.edit("apps/service/src/extra.ts", "export const extra = 1;\n")
        run = self.hollow(".claude/skills", baseline=False, filled=".claude/skills/x.md")
        self.assertEqual([line for line in self.scoped_lines(run) if "projection directory" in line], [])
        self.assertIn("check-agents", self.decided(run)[1], run.stdout)

    def test_e6_only_the_empty_one_is_named_beside_a_directory_that_holds_a_file(self) -> None:
        run = self.hollow(".claude/skills", ".bob/skills", baseline=False, filled=".claude/skills/x.md")
        self.assertEqual([line for line in self.scoped_lines(run) if "projection directory" in line],
                         [said(".bob/skills/")])
