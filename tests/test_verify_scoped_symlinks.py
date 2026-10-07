"""T021 (A1, closes T013): an input read through a link gives its check no recorded inputs, for every row of the record.

A declared input that is a link, that has a link among its directories below the project root, or (a directory) that
holds a link leading outside the check's own inputs makes the check read a file no row names: a change there skips a
check `make verify` fails. Such a check keeps no recorded inputs — it runs on every scoped run and claims nothing — with
a reason that names the link. The working tree and the base are both read: a link the branch replaced is still one.

The record is the project's own (`verify-scoped.py record`); the selection is `choose` over it, as
`test_verify_scoped_flips` takes it.
"""
from __future__ import annotations

import importlib
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

from stamp_fixture import git
from test_verify_scoped_flips import integrate
from test_verify_scoped_record import RecordCase, loaded

from slipwai.assets import ROOT

sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "assets" / "toolkit" / "scripts"))

CONSTITUTION = ".specify/memory/constitution.md"
MOVED = "docs/event-model/constitution.md"  # under `check-model`'s own inputs, so a change there is claimed
UNCHANGED = "none of its inputs changed"


def link(project: Path, path: str, target: str) -> None:
    """`path` made a link to `target`, written as a link's text is (relative to the link's own directory)."""
    where = project / path
    if where.is_dir() and not where.is_symlink():
        shutil.rmtree(where)
    elif where.exists() or where.is_symlink():
        where.unlink()
    where.parent.mkdir(parents=True, exist_ok=True)
    os.symlink(target, where)


def commit(project: Path, message: str) -> None:
    git(project, "add", "-A")
    git(project, "-c", "user.name=t", "-c", "user.email=t@local", "-c", "maintenance.auto=false",
        "commit", "-qm", message)


def selection(record: dict[str, Any], changed: list[str]) -> dict[str, tuple[bool, str]]:
    choose = importlib.import_module("verify_scoped.choose")
    data = importlib.import_module("verify_scoped.record").Database({}, {}, {})
    return {item.unit: (item.runs, item.reason) for item in choose.choose(record, data, changed)}


class LinkCase(RecordCase):
    def assert_linked(self, check: dict[str, Any], named: str) -> None:
        self.assertEqual((check["inputs"], check["claims"]), (None, False), check)
        self.assertIn(f"`{named}`", check["always"], check)
        self.assertIn("link", check["always"], check)

    def constitution_behind_a_link(self) -> Path:
        project = self.project("model-typescript-web")
        (project / MOVED).write_text("# A constitution\n", encoding="utf-8")  # `./init` writes one; none is generated
        link(project, CONSTITUTION, "../../" + MOVED)
        return project


class InsideTest(LinkCase):
    def test_a_constitution_moved_behind_a_link_inside_the_project_runs_its_readers(self) -> None:
        project = self.constitution_behind_a_link()
        record = loaded(project)
        for name in ("check-constitution", "check-speckit"):
            self.assert_linked(record["checks"][name], CONSTITUTION)
        chosen = selection(record, [MOVED])
        for name in ("check-constitution", "check-speckit"):
            self.assertTrue(chosen[name][0], (name, chosen[name]))
            self.assertIn(CONSTITUTION, chosen[name][1])
        self.assertEqual(chosen["check-model"], (True, f"{MOVED} changed"))

    def test_a_linked_directory_of_an_input_is_a_link_for_every_check_that_reads_under_it(self) -> None:
        project = self.project("model-typescript-web")
        shutil.move(str(project / "docs" / "event-model"), str(project / "model-elsewhere"))
        link(project, "docs/event-model", "../model-elsewhere")
        record = loaded(project)
        for name in ("check-model", "check-drawio", "check-decisions", "check-benchmark"):
            self.assert_linked(record["checks"][name], "docs/event-model")

    def test_a_link_under_an_input_directory_that_leads_outside_the_checks_inputs_is_a_link(self) -> None:
        project = self.project("model-typescript-web")
        (project / "docs/event-model/skill.md").write_text("# a skill\n", encoding="utf-8")
        link(project, "skills/linked/SKILL.md", "../../docs/event-model/skill.md")
        record = loaded(project)
        self.assert_linked(record["checks"]["check-agents"], "skills/linked/SKILL.md")
        self.assertTrue(selection(record, ["docs/event-model/skill.md"])["check-agents"][0])

    def test_a_link_under_an_input_directory_that_stays_inside_the_checks_inputs_is_no_link(self) -> None:
        project = self.project("model-typescript-web")
        first = sorted(path.parent.name for path in (project / "skills").glob("*/SKILL.md"))[0]
        link(project, "skills/again", first)
        check = loaded(project)["checks"]["check-agents"]
        self.assertIsNotNone(check["inputs"], check)
        self.assertIn("skills/", check["inputs"]["files"])


class OutsideTest(LinkCase):
    def test_a_skills_projection_linked_outside_the_project_runs_check_agents(self) -> None:
        project = self.project("model-typescript-web")
        integrate(project, "claude")
        outside = Path(tempfile.mkdtemp(prefix="outside-", dir=self.parent)) / "skills"
        shutil.move(str(project / ".claude" / "skills"), str(outside))
        link(project, ".claude/skills", str(outside))
        record = loaded(project)
        self.assert_linked(record["checks"]["check-agents"], ".claude/skills")
        self.assertTrue(selection(record, [])["check-agents"][0])


class BaseTest(LinkCase):
    def test_a_link_only_at_the_base_is_still_a_link(self) -> None:
        project = self.constitution_behind_a_link()
        git(project, "checkout", "-q", "main")
        commit(project, "the constitution behind a link")
        git(project, "checkout", "-q", "-B", "slice/S1")
        (project / CONSTITUTION).unlink()
        shutil.copyfile(project / MOVED, project / CONSTITUTION)
        self.assertFalse((project / CONSTITUTION).is_symlink())
        record = loaded(project)
        for name in ("check-constitution", "check-speckit"):
            self.assert_linked(record["checks"][name], CONSTITUTION)
            self.assertIn("base", record["checks"][name]["always"])

    def test_a_tree_with_no_link_keeps_every_rows_inputs(self) -> None:
        record = loaded(self.project("model-typescript-web"))
        self.assertFalse([name for name, check in record["checks"].items() if "link" in (check["always"] or "")])
        self.assertEqual(selection(record, [MOVED])["check-constitution"], (False, UNCHANGED))
