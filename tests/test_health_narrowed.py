"""`health()` before an iteration: the sync count, the gate's output and the tree are today's (S02, R7), and it
hashes only what changed (R4).

The project is the indexed one of `test_code_index_health`, driven through `Project` of `test_codegraph_narrowed`;
`health()` is run as `python3 scripts/agents/code_index.py health`, which prints `code-index: <state> — <detail>`.
`HoldsTest` is R7 and every example in it is a hold: green before `health()` narrows, and it must stay green.
`NarrowedHealthTest` is R4, the change itself.
"""
from __future__ import annotations

import json
import re
import subprocess
import tempfile

from gate_audit import WRAPPER, Audited
from support import FactoryTestCase
from test_codegraph_narrowed import CI_MARKERS, CURRENT, OWN, Project
from test_cruise_index import bare_path

# Generates nothing itself: the projects come from `Project`, imported from the modules above.
TEST_SELECTION: dict[str, object] = {}

HEALTH = "scripts/agents/code_index.py"
# What `health()` says of a narrowed comparison: how many of how many, that only what changed was compared, and since
# when; the moment is the gate's own (`2026-10-03 12:00:00`).
NARROWED = (r"hashed {hashed} of (\d+) file\(s\), only what changed since the last whole comparison "
            r"\(\d{{4}}-\d\d-\d\d \d\d:\d\d:\d\d\)")
SAID = re.compile(r"^code-index: (\w+) — (.*)\n$", re.DOTALL)


class Health:
    """One run of the runner's check, and what it opened."""

    def __init__(self, project: Project, **extra: str | None) -> None:
        self.project = project
        self.read(subprocess.run(["python3", HEALTH, "health"], cwd=project.repo, env=project.env(**extra),
                                 text=True, capture_output=True))

    def read(self, done: subprocess.CompletedProcess[str]) -> None:
        self.result = done
        said = SAID.match(done.stdout)
        self.state, self.detail = (said.group(1), said.group(2)) if said else ("", done.stdout)

    @classmethod
    def audited(cls, project: Project, **extra: str | None) -> tuple[Health, list[str]]:
        """`health` run under the audit hook of `gate_audit`: its wrapper, with the verb on the command line, and
        every path the run opened as the project spells it."""
        record = project.repo.parent / "audit-health.json"
        wrapper = WRAPPER.replace("sys.argv = [script]", "sys.argv = [script, 'health']")
        done = subprocess.run(["python3", "-c", wrapper, HEALTH, str(record)], cwd=project.repo, text=True,
                              capture_output=True, env=project.env(**extra))
        events = json.loads(record.read_text())
        record.unlink()
        root = project.repo.resolve()
        health = cls.__new__(cls)
        health.project = project
        health.read(done)
        return health, [Audited.within(root, path) for event, path in events if event == "open"]

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


class NarrowedHealthTest(FactoryTestCase):
    """R4: `health()` hashes what changed since the last whole comparison, on any branch outside CI."""

    def prepared(self, directory: str) -> Project:
        project = Project(self, directory)
        project.whole()
        self.assertTrue(project.memory.is_file())
        return project

    def test_e34_nothing_changed_hashes_nothing_on_every_kind_of_branch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self.prepared(directory)
            for where in ("main", "slice/S1", "feature/x", "detached"):
                project.git("checkout", "-q", *(["--detach"] if where == "detached" else ["-B", where]))
                done = Health(project)
                self.assertEqual(done.state, "current", f"{where}: {done.detail}")
                self.assertRegex(done.detail, NARROWED.format(hashed=0), where)

    def test_e35_one_changed_file_is_hashed_alone_and_synced_once(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self.prepared(directory)
            project.in_place()
            edited = project.edit()
            project.log.unlink(missing_ok=True)
            done, opened = Health.audited(project)
            self.assertEqual(done.state, "synced", done.detail)
            self.assertEqual(done.calls(), ["sync ."])
            self.assertEqual(set(project.rows()) & set(opened) - OWN, {edited})
            self.assertIn("1 tracked file(s) were ahead of the index; synced it", done.detail)

    def test_e35_a_sync_that_does_not_take_is_failed_as_today(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self.prepared(directory)
            project.in_place()
            project.edit()
            done = Health(project, FAKE_SYNC_FAILS="1")
            self.assertEqual(done.state, "failed", done.detail)
            self.assertIn("1 tracked file(s) ahead of the index, and `codegraph sync` failed", done.detail)

    def test_e41_a_touch_costs_one_hash(self) -> None:
        """AC-S02-41's first run; the second, which hashes 0, needs the memory renewed (T008, `test_health_memory`)."""
        with tempfile.TemporaryDirectory() as directory:
            project = self.prepared(directory)
            path = project.repo / project.source()
            project.settle()
            path.touch()
            project.settle()
            first, opened = Health.audited(project)
            self.assertEqual(first.state, "current", first.detail)
            self.assertRegex(first.detail, NARROWED.format(hashed=1))
            self.assertIn(project.source(), opened)

    def test_e42_an_unchanged_tree_costs_the_fiftieth_iteration_what_the_second_did(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self.prepared(directory)
            project.settle()
            for iteration in range(2, 52):
                if iteration in (2, 50):
                    done, opened = Health.audited(project)
                    self.assertEqual(set(project.rows()) & set(opened) - OWN, set(), f"iteration {iteration}")
                else:
                    done = Health(project)
                self.assertEqual(done.state, "current", f"iteration {iteration}: {done.detail}")
                self.assertRegex(done.detail, NARROWED.format(hashed=0), f"iteration {iteration}")
