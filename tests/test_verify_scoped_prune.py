"""T035 (R5, R13 · AC-S06-5, -18): a prune the project ran is not a Makefile the project wrote.

`scripts/verify_scoped/rules.json` holds what the factory wrote for the `Makefile`. Every code path that writes the
`Makefile` of a stamped project leaves the two matching, when they matched before: `generate`, `add-service`,
`replay` (which `migrate` merges), `prune` itself, and the `./init` step that runs it
(`scripts/backing-services.py`). A `Makefile` the project had already edited is left differing, so the scoped gate
still charges the edit. Matching is read the way the gate reads it: the make database of the project's own
`Makefile` against the file.
"""
from __future__ import annotations

import importlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from support import FactoryTestCase
from test_replay import git, replay

from slipwai.assets import ROOT

sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "assets" / "toolkit" / "scripts"))

RULES = "scripts/verify_scoped/rules.json"
PRUNE = ("python3", "-B", "scripts/backing-services.py")
BOTH = ("--event-store", "memory", "--http", "none", "--auth", "none")
FULL = {"event_store": "postgres", "http": "fastify", "auth": "keycloak"}


def held(project: Path) -> dict[str, Any]:
    return json.loads((project / RULES).read_text(encoding="utf-8"))


def read(project: Path) -> dict[str, Any]:
    """What the gate reads from the project's own `Makefile`: the make database in the form `rules.json` is in."""
    rules = importlib.import_module("verify_scoped.rules")
    records = importlib.import_module("verify_scoped.record")
    data = records.database("make", str(project / "Makefile"))
    names = json.loads((project / "project.json").read_text(encoding="utf-8"))["deployables"]
    units = [f"{gate}-{name}" for gate in ("lint", "typecheck", "test") for name in names
             if f"{gate}-{name}" in data.needs and not name.startswith("integration")]
    return rules.from_database(data, units)


def prune(project: Path, *flags: str) -> None:
    done = subprocess.run([*PRUNE, *flags], cwd=project, text=True, capture_output=True, timeout=120)
    assert done.returncode == 0, done.stdout + done.stderr


class PruneKeepsTheRecordTest(FactoryTestCase):
    longMessage = False
    parent: Path
    base: Path

    @classmethod
    def setUpClass(cls) -> None:
        cls.parent = Path(tempfile.mkdtemp(prefix="scoped-prune-"))
        cls.addClassCleanup(shutil.rmtree, cls.parent, ignore_errors=True)
        cls.base = FactoryTestCase.generate(cls, cls.parent, "kept", "event-modelling", "typescript", **FULL)  # type: ignore[arg-type]

    def fresh(self) -> Path:
        copy = Path(tempfile.mkdtemp(prefix="copy-", dir=self.parent)) / "project"
        shutil.copytree(self.base, copy, symlinks=True)
        return copy

    def assertMatches(self, project: Path, why: str = "") -> None:
        self.assertEqual(held(project), read(project), why or "rules.json is not what the Makefile makes")

    def test_e1_the_starter_that_keeps_postgres_and_fastify_matches_to_begin_with(self) -> None:
        self.assertIn("CI_DATABASE :=", (self.base / "Makefile").read_text(encoding="utf-8"))
        self.assertMatches(self.base)

    def test_e1_init_event_store_memory_leaves_rules_json_matching(self) -> None:
        project = self.fresh()
        prune(project, "--event-store", "memory")
        self.assertNotIn("CI_DATABASE :=", (project / "Makefile").read_text(encoding="utf-8"))
        self.assertMatches(project)

    def test_e2_init_http_none_leaves_rules_json_matching(self) -> None:
        project = self.fresh()
        prune(project, "--http", "none", "--auth", "none")
        self.assertNotIn("verify-checks: check-openapi", (project / "Makefile").read_text(encoding="utf-8"))
        self.assertMatches(project)

    def test_e1_the_function_prune_gives_the_same(self) -> None:
        project = self.fresh()
        pruner = importlib.import_module("slipwai.assets").PRUNER
        pruner.prune(project, {"keycloak", "fastify"}, log=lambda _message: None)
        self.assertMatches(project)

    def test_e3_a_makefile_the_project_edited_before_the_prune_still_differs_after(self) -> None:
        project = self.fresh()
        makefile = project / "Makefile"
        makefile.write_text(makefile.read_text(encoding="utf-8").replace("CI_DATABASE", "CI_DATABASE_MINE", 1),
                            encoding="utf-8")
        before = (project / RULES).read_bytes()
        prune(project, "--event-store", "memory")
        self.assertEqual((project / RULES).read_bytes(), before)
        self.assertNotEqual(held(project), read(project))

    def test_e4_a_missing_rules_file_stays_missing(self) -> None:
        project = self.fresh()
        (project / RULES).unlink()
        prune(project, "--event-store", "memory")
        self.assertFalse((project / RULES).exists())

    def test_e5_the_rewrite_is_by_rename_and_leaves_nothing_beside_it(self) -> None:
        project = self.fresh()
        before = {path.name for path in (project / RULES).parent.iterdir()}
        prune(project, "--event-store", "memory")
        self.assertEqual({path.name for path in (project / RULES).parent.iterdir()}, before)
        self.assertEqual(held(project)["schema"], 1)

    def test_e6_add_service_after_a_prune_leaves_rules_json_matching(self) -> None:
        project = self.fresh()
        prune(project, *BOTH)
        commit_all_changes(project, "pruned")
        done = subprocess.run([str(ROOT / "slipwai"), "add-service", "billing", "--language", "python"],
                              cwd=project, text=True, capture_output=True, timeout=300)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertMatches(project)
        self.assertNotIn("CI_DATABASE :=", (project / "Makefile").read_text(encoding="utf-8"))

    def test_e6_add_service_to_the_full_starter_leaves_rules_json_matching(self) -> None:
        project = self.fresh()
        done = subprocess.run([str(ROOT / "slipwai"), "add-service", "billing", "--language", "python"],
                              cwd=project, text=True, capture_output=True, timeout=300)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertMatches(project)

    def test_e7_replay_of_a_pruned_project_matches(self) -> None:
        project = self.fresh()
        prune(project, *BOTH)
        commit_all_changes(project, "pruned")
        offered = self.parent / f"offered-{project.parent.name}"
        done = replay(project, ROOT, "--into", str(offered))
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertNotIn("CI_DATABASE :=", (offered / "Makefile").read_text(encoding="utf-8"))
        self.assertMatches(offered)


def commit_all_changes(project: Path, message: str) -> None:
    git(project, "add", "-A")
    git(project, "-c", "user.name=t", "-c", "user.email=t@local", "commit", "-q", "--allow-empty", "-m", message)
