"""`health()` before an iteration: the sync count, the gate's output and the tree are today's (S02, R7).

The project is the indexed one of `test_code_index_health`, driven through `Project` of `test_codegraph_narrowed`;
`health()` is run as `python3 scripts/agents/code_index.py health`, which prints `code-index: <state> — <detail>`.
`HoldsTest` is R7 and every example in it is a hold: green before `health()` narrows, and it must stay green.
"""
from __future__ import annotations

import re
import subprocess
import tempfile

from support import FactoryTestCase
from test_codegraph_narrowed import CI_MARKERS, CURRENT, Project
from test_cruise_index import bare_path

HEALTH = "scripts/agents/code_index.py"
SAID = re.compile(r"^code-index: (\w+) — (.*)\n$", re.DOTALL)

class Health:
    """One run of the runner's check, and what it opened."""

    def __init__(self, project: Project, **extra: str | None) -> None:
        self.project = project
        self.result = subprocess.run(["python3", HEALTH, "health"], cwd=project.repo, env=project.env(**extra),
                                     text=True, capture_output=True)
        said = SAID.match(self.result.stdout)
        self.state, self.detail = (said.group(1), said.group(2)) if said else ("", self.result.stdout)

    def syncs(self) -> int:
        return sum(1 for call in self.calls() if call.split()[:1] == ["sync"])

    def calls(self) -> list[str]:
        return self.project.log.read_text().splitlines() if self.project.log.exists() else []


class HoldsTest(FactoryTestCase):
    """R7: every example is a hold, green today."""

    def test_hold_e43_one_iteration_syncs_at_most_once_and_only_where_files_are_behind(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Project(self, directory)
            project.whole()
            project.log.unlink(missing_ok=True)

            current = Health(project)
            self.assertEqual((current.state, current.syncs(), current.calls()), ("current", 0, []), current.detail)

            project.edit()
            behind = Health(project)
            self.assertEqual((behind.state, behind.syncs()), ("synced", 1), behind.detail)
            self.assertEqual(behind.calls(), ["sync ."], "once, and nothing else")
            project.log.unlink()

            project.database.unlink()
            built = Health(project)
            self.assertEqual((built.state, built.syncs(), built.calls()), ("built", 0, ["init -y ."]), built.detail)
            project.log.unlink()

            project.database.write_bytes(b"garbage " * 1000)
            rebuilt = Health(project)
            self.assertEqual((rebuilt.state, rebuilt.syncs(), rebuilt.calls()), ("rebuilt", 0, ["init -y ."]),
                             rebuilt.detail)
            project.log.unlink()

            project.edit()
            unreachable = Health(project, PATH=str(bare_path(project.repo.parent)), HOME=str(project.repo.parent),
                                 NVM_DIR="", VOLTA_HOME="", FNM_DIR="")
            self.assertEqual((unreachable.state, unreachable.calls()), ("unreachable", []), unreachable.detail)

    def test_hold_e44_the_gate_off_a_slice_branch_and_in_ci_prints_todays_line_and_exit_code(self) -> None:
        """The gate's own examples are `test_codegraph_narrowed` and `test_codegraph_bytes`, which pass with no edit;
        this is the same output seen after `health()` has run beside it, the corrupt-database rebuild included."""
        with tempfile.TemporaryDirectory() as directory:
            project = Project(self, directory)
            today = project.whole()
            self.assertRegex(today.stdout, CURRENT)
            Health(project)
            project.git("checkout", "-q", "-b", "feature/x")
            self.assertEqual(project.run().stdout, today.stdout)
            project.git("checkout", "-q", "--detach")
            self.assertEqual(project.run().stdout, today.stdout)
            project.slice()
            for marker in CI_MARKERS:
                done = project.run(**{marker: "true"})
                self.assertEqual((done.returncode, done.stdout), (0, today.stdout), marker)
            project.git("checkout", "-q", "main")
            project.database.write_bytes(b"garbage " * 1000)
            rebuilt = project.run()
            self.assertEqual(rebuilt.returncode, 0, rebuilt.stderr)
            self.assertRegex(rebuilt.stdout, r"^check-codegraph: rebuilt a corrupt database first \([\d.]+s\); "
                             r"index current — \d+ file\(s\), indexed ")
            self.assertNotIn("hashed", rebuilt.stdout)

    def test_hold_e45_health_leaves_nothing_for_git_status_and_no_bytecode_beside_the_scripts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Project(self, directory)
            project.whole()
            def committed_edit() -> None:
                project.edit()
                project.commit()

            for disturb in (lambda: None, committed_edit,
                            lambda: project.database.write_bytes(b"garbage " * 1000), project.database.unlink):
                disturb()
                done = Health(project)
                self.assertNotEqual(done.state, "", done.result.stderr)
                self.assertEqual(project.git("status", "--porcelain"), "", done.state)
                self.assertEqual(list(project.repo.rglob("__pycache__")), [], done.state)

    def test_hold_health_runs_the_integrity_check_on_every_call(self) -> None:
        """D59: narrowed or not, a corrupt database is found by `health()` and not left to a later query."""
        with tempfile.TemporaryDirectory() as directory:
            project = Project(self, directory)
            project.whole()
            Health(project)
            project.database.write_bytes(b"garbage " * 1000)
            done = Health(project)
            self.assertEqual(done.state, "rebuilt", done.detail)
            self.assertIn("failed its integrity check", done.detail)
