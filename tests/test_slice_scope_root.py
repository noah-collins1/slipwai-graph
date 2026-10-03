"""A deployable at `.` is the fallback owner of every path no other deployable claims.

An adopted repository records its one application at `.`, and `check-slice-scope` once read that as owning
nothing, so a slice's own tests were refused as *outside every deployable*. These tests run the gate in a real
temporary repository laid out as an adoption leaves one (the delivery material under `delivery/`), on a
`slice/S1` branch, with the deployables the manifest records.
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from support import NO_MAINTENANCE, commit_all
from test_adopt import repository, slipwai

from slipwai.assets import ROOT
from slipwai.delivery_facts import CI_FORGES

SCRIPTS = ROOT / "assets/toolkit/scripts"
OUTSIDE = "outside every deployable"
MODEL = """\
schemaVersion: 1
slices:
  - id: S1
    name: Place an order
    pattern: state-change
    status: planned
    actor: Customer
    service: shop
    frames: []
"""


def load_checker(path: Path, name: str):
    """The checker as a module, from whichever copy `path` names, with no `__pycache__` left beside it."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.dont_write_bytecode = True
    spec.loader.exec_module(module)
    return module


def git(repo: Path, *arguments: str) -> None:
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@local", *NO_MAINTENANCE, *arguments],
                   cwd=repo, capture_output=True, check=True)


class SliceScopeRootTest(unittest.TestCase):
    def repo(self, deployables: dict, model: bool = False, written: str | None = None,
             registry: bool | str = False, **project: object) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        repo = Path(directory.name)
        git(repo, "init", "-q", "-b", "main")
        (repo / "project.json").write_text(json.dumps({"deployables": deployables, **project}))
        (repo / "delivery/scripts/event-model").mkdir(parents=True)
        shutil.copy(SCRIPTS / "check-slice-scope.py", repo / "delivery/scripts")
        shutil.copy(SCRIPTS / "event-model/check.py", repo / "delivery/scripts/event-model")
        if written is not None:
            (repo / "delivery/.written").write_text(written)
        if registry is True:
            (repo / "delivery/scripts/agents").mkdir()
            shutil.copy(SCRIPTS / "agents/registry.json", repo / "delivery/scripts/agents")
        elif isinstance(registry, str):
            (repo / "delivery/scripts/agents").mkdir()
            (repo / "delivery/scripts/agents/registry.json").write_text(registry)
        if model:
            (repo / "delivery/docs/event-model").mkdir(parents=True)
            (repo / "delivery/docs/event-model/model.yaml").write_text(MODEL)
        commit_all(repo, "base")
        git(repo, "checkout", "-q", "-b", "slice/S1")
        return repo

    def verdict(self, repo: Path, path: str) -> subprocess.CompletedProcess:
        target = repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        before = target.read_bytes() if target.exists() else None
        target.write_text("x\n")
        try:
            return subprocess.run(
                ["python3", "delivery/scripts/check-slice-scope.py"], cwd=repo, text=True, capture_output=True,
                env={**os.environ, "GITHUB_HEAD_REF": "", "CI_COMMIT_REF_NAME": ""},
            )
        finally:
            if before is None:
                target.unlink()
            else:
                target.write_bytes(before)

    def green(self, repo: Path, *paths: str) -> None:
        for path in paths:
            result = self.verdict(repo, path)
            self.assertEqual(result.returncode, 0, f"{path}: {result.stderr}")
            self.assertIn("touches only what one slice may", result.stdout, path)

    def refused(self, repo: Path, *paths: str) -> None:
        for path in paths:
            result = self.verdict(repo, path)
            self.assertNotEqual(result.returncode, 0, f"{path} was let through")
            self.assertIn(OUTSIDE, result.stderr, path)
            self.assertIn("the host's", result.stderr, path)

    def root(self, path: str = ".") -> dict:
        return {"shop": {"kind": "service", "path": path}}

    def test_the_root_deployable_owns_what_nobody_else_claims(self) -> None:
        """R1 e1-e3: the application's own tests, a sibling directory, root tooling and manifests are the slice's."""
        repo = self.repo(self.root())
        self.green(repo, "tests/test_x.py")
        self.green(repo, "worker/x.py", "scripts/x.py", "docs/x.md")
        self.green(repo, "requirements.txt", "pyproject.toml")

    def test_the_root_may_be_written_with_a_trailing_slash(self) -> None:
        """R1 e4: `./` answers as `.` does."""
        self.green(self.repo(self.root("./")), "tests/test_x.py", "worker/x.py")

    def test_an_empty_path_owns_nothing(self) -> None:
        """R1 e5: a deployable with `path: ""` is no fallback; its file stays outside every deployable."""
        result = self.verdict(self.repo(self.root("")), "tests/test_x.py")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(OUTSIDE, result.stderr)

    def test_a_subdirectory_service_still_owns_its_own_files(self) -> None:
        """R3 e1: the fallback does not outrank `apps/api`, and another service's code is not this slice's."""
        repo = self.repo({**self.root(), "api": {"kind": "service", "path": "apps/api"}}, model=True)
        result = self.verdict(repo, "apps/api/x.py")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("service `api` is not slice `S1`'s", result.stderr)

    def test_the_root_service_still_owns_the_rest_beside_a_subdirectory_one(self) -> None:
        """R3 e2: the same branch, a file the root service owns, is green."""
        repo = self.repo({**self.root(), "api": {"kind": "service", "path": "apps/api"}}, model=True)
        self.green(repo, "tests/test_x.py")

    def test_the_host_surface_at_the_root_is_refused(self) -> None:
        """R2 e1: the root Makefile, the manifest, the run's settings, CI and the harness guidance are the host's."""
        self.refused(self.repo(self.root()), "Makefile", "project.json", ".specify/x.json",
                     ".github/workflows/x.yml", "AGENTS.md", ".claude/settings.json")

    def test_the_delivery_directory_is_refused(self) -> None:
        """R2 e2: the gate, the skills, the commands and the baseline sit in the delivery directory."""
        self.refused(self.repo(self.root()), "delivery/scripts/x.py", "delivery/skills/x/SKILL.md",
                     "delivery/commands/x.md", "delivery/Makefile", "delivery/baseline.json")

    def test_the_docs_keep_their_own_answer(self) -> None:
        """R2 e3, held: the docs are refused as they were, by the docs clause."""
        result = self.verdict(self.repo(self.root()), "delivery/docs/x.md")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("the docs are the host's", result.stderr)

    def test_the_slice_writes_two_survey_pages_and_no_other(self) -> None:
        """R2 e4: `pinned.md` and `running.md` are the ladder's to write; `survey.md` stays the host's."""
        repo = self.repo(self.root())
        self.green(repo, "delivery/survey/pinned.md", "delivery/survey/running.md")
        self.refused(repo, "delivery/survey/survey.md")

    def test_a_path_the_factory_wrote_is_refused(self) -> None:
        """R2 e5: a line of `.written` is the host's, though no fixed name says so."""
        repo = self.repo(self.root(), written="lib/generated.py\n")
        self.refused(repo, "lib/generated.py")
        self.green(repo, "lib/own.py")

    def test_taking_a_file_over_does_not_open_the_gate_workflow(self) -> None:
        """R2 e6: `.written` with the gate's line deleted still refuses the gate workflow."""
        repo = self.repo(self.root(), written="lib/generated.py\n")
        self.refused(repo, ".github/workflows/verify-delivery.yml")

    def test_no_written_file_leaves_the_fixed_list(self) -> None:
        """R2 e7, held: with no `.written` the fixed list refuses and the rest is the slice's."""
        repo = self.repo(self.root())
        self.assertFalse((repo / "delivery/.written").exists())
        self.refused(repo, "Makefile")
        self.green(repo, "lib/own.py")

    def test_the_recorded_gate_is_the_hosts_wherever_it_sits(self) -> None:
        """R2 e8: `ci.gate` naming a file outside the fixed CI names is refused."""
        repo = self.repo(self.root(), ci={"gate": "ci/gate.yml"})
        self.refused(repo, "ci/gate.yml")
        self.green(repo, "ci/other.yml")

    def test_every_spelling_of_a_recorded_path_answers_alike(self) -> None:
        """T007 (AC-S20-7, -8): `./apps/api` is `apps/api`; `ci.gate` spelled `./ci/gate.yml` is `ci/gate.yml`."""
        for spelling in ("apps/api", "apps/api/", "./apps/api", "./apps/api/", ".//apps/api"):
            with self.subTest(path=spelling):
                repo = self.repo({**self.root(), "api": {"kind": "service", "path": spelling}}, model=True)
                result = self.verdict(repo, "apps/api/x.py")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("service `api` is not slice `S1`'s", result.stderr)
                self.green(repo, "tests/test_x.py")
        for spelling in (".", "./", "./."):
            with self.subTest(root=spelling):
                self.green(self.repo(self.root(spelling)), "tests/test_x.py")
        for gate in ("ci/gate.yml", "./ci/gate.yml", "ci/gate.yml/"):
            with self.subTest(gate=gate):
                repo = self.repo(self.root(), ci={"gate": gate})
                self.refused(repo, "ci/gate.yml")
                self.green(repo, "ci/other.yml")

    HARNESS_PATHS = (".mcp.json", "opencode.json", "GEMINI.md", ".agents/skills/x/SKILL.md", ".kiro/settings/mcp.json")
    FLOOR = ("Makefile", ".github/workflows/x.yml", "AGENTS.md", ".claude/settings.json")

    def test_every_path_a_harness_row_names_is_the_hosts(self) -> None:
        """T008 (AC-S20-14): the registry beside the checker names the harness files; each is refused."""
        self.refused(self.repo(self.root(), registry=True), *self.HARNESS_PATHS, ".cursor/hooks.json",
                     ".github/copilot-instructions.md", ".junie/AGENTS.md")

    def test_a_registry_that_is_gone_unreadable_or_malformed_adds_nothing(self) -> None:
        """T008 (AC-S20-14): D18's names are still refused, the five pass, and there is never a traceback."""
        for label, registry in (("absent", False), ("not json", "{nope"), ("a list", "[1, 2]"),
                                ("harnesses a string", '{"harnesses": "x"}'), ("empty", "")):
            with self.subTest(registry=label):
                repo = self.repo(self.root(), registry=registry)
                self.refused(repo, *self.FLOOR)
                self.green(repo, *self.HARNESS_PATHS)
        unreadable = self.repo(self.root())
        (unreadable / "delivery/scripts/agents/registry.json").mkdir(parents=True)  # not readable as a file
        self.refused(unreadable, *self.FLOOR)
        self.green(unreadable, *self.HARNESS_PATHS)

    def test_a_malformed_row_adds_nothing_and_does_not_hide_the_others(self) -> None:
        """T008 (AC-S20-14, D20): a row of the wrong shape adds nothing; a well-formed row beside it still does."""
        rows = [
            "x", {"contextFile": 5, "skillsDir": ".zz/skills"}, {"agentFile": "oops", "commandsDir": ".yy/commands"},
            {"hooks": {"projection": []}, "contextFile": "WRONG.md"},
            {"contextFile": "GOOD.md", "skillsDir": "~/home/skills", "commandsDir": "/abs/commands",
             "agentFile": {"dir": ".good/agents"}, "hooks": {"projection": {"where": ".goodhooks/h.json"}},
             "projectMcp": {"file": ".good/nested/mcp.json"}},
        ]
        repo = self.repo(self.root(), registry=json.dumps({"harnesses": rows}))
        self.refused(repo, "GOOD.md", ".good/agents/a.md", ".goodhooks/h.json", ".good/nested/mcp.json")
        self.green(repo, ".zz/x", ".yy/x", "WRONG.md", "home/skills/x", "abs/commands/x")

    def test_the_registry_is_read_once_not_per_path(self) -> None:
        """T008: the harness names are read once for the run; replacing the file mid-run changes nothing."""
        repo = self.repo(self.root(), registry=True)
        checker = load_checker(repo / "delivery/scripts/check-slice-scope.py", "slice_scope_read_once")
        scope = checker.Scope("S1", "HEAD")
        self.assertTrue(scope.host_surface(".mcp.json"))
        (repo / "delivery/scripts/agents/registry.json").write_text("{nope")
        self.assertTrue(scope.host_surface("GEMINI.md"))

    def test_the_other_ci_systems_and_makefile_spellings_are_the_hosts(self) -> None:
        """T008 (AC-S20-15): what `adopt` recognises as CI, and `GNUmakefile` / `makefile`, are refused."""
        self.refused(self.repo(self.root(), registry=True), "Jenkinsfile", "azure-pipelines.yml",
                     "bitbucket-pipelines.yml", ".circleci/config.yml", ".woodpecker.yml", ".drone.yml",
                     ".travis.yml", "GNUmakefile", "makefile")

    def test_the_checker_names_every_ci_system_adopt_recognises(self) -> None:
        """T008 (AC-S20-15): a forge `adopt` learns later and the checker does not is a red test, not a hole."""
        checker = load_checker(SCRIPTS / "check-slice-scope.py", "slice_scope_names")
        for key in CI_FORGES:
            with self.subTest(ci=key):
                self.assertTrue(key in checker.HOST_FILES or key.split("/")[0] in checker.HOST_DIRECTORIES, key)

    def test_git_hooks_and_the_ignore_file_are_the_repositorys_own(self) -> None:
        """T008 (AC-S20-16), held: green on arrival, and still green once the registry and CI names are read."""
        self.green(self.repo(self.root(), registry=True), ".gitignore", ".githooks/pre-commit",
                   ".pre-commit-config.yaml", ".husky/pre-commit")

    FIXED_HOST_NAMES = (
        "project.json", "Makefile", "GNUmakefile", "makefile", "AGENTS.md", "CLAUDE.md", ".gitlab-ci.yml",
        "Jenkinsfile", "azure-pipelines.yml", "bitbucket-pipelines.yml", ".woodpecker.yml", ".drone.yml",
        ".travis.yml", ".specify/x.json", ".github/workflows/x.yml", ".gitea/workflows/x.yml",
        ".forgejo/workflows/x.yml", ".gitlab/x.yml", ".circleci/config.yml", ".claude/settings.json",
        ".codex/config.toml", ".cursor/rules/x.mdc", ".gemini/settings.json", ".opencode/x.json",
    )

    def test_every_fixed_host_name_is_refused_with_no_registry(self) -> None:
        """T006 (AC-S20-2, D20), held: every name the checker fixes, one at a time, listed here and not read from
        the checker, so deleting one from its constants turns this red. There is no registry beside the checker."""
        repo = self.repo(self.root())
        for path in self.FIXED_HOST_NAMES:
            with self.subTest(path=path):
                self.refused(repo, path)

    def test_a_deployable_with_no_path_key_owns_nothing(self) -> None:
        """T006 (AC-S20-8), held: a record with the key missing, as with `""`, is no fallback owner."""
        for record in ({"kind": "service"}, {"kind": "service", "path": None}, {"kind": "service", "path": 7}):
            with self.subTest(record=record):
                self.refused(self.repo({"shop": record}), "tests/test_x.py")

    def test_the_host_surface_is_refused_under_the_slash_spelling_too(self) -> None:
        """T006 (AC-S20-2, -8), held: with the root recorded `./`, the host's names are as refused as at `.`."""
        self.refused(self.repo(self.root("./")), "Makefile", "project.json", ".specify/x.json", "AGENTS.md",
                     ".github/workflows/x.yml", "delivery/scripts/x.py")

    def test_a_real_adoption_at_the_root(self) -> None:
        """AC-S20-1, -2 on a tree `slipwai adopt` made: tests are the slice's, the Makefile and a written path not."""
        with tempfile.TemporaryDirectory() as directory:
            repo = repository(Path(directory), "shop", {
                "package.json": json.dumps({"name": "shop", "scripts": {"lint": "x", "test": "y"}}),
                "src/index.js": "1\n", "test/a.test.js": "2\n", "Makefile": "all:\n\t@true\n",
            })
            self.assertEqual(slipwai(repo, "adopt", "--yes").returncode, 0)
            self.assertEqual(json.loads((repo / "project.json").read_text())["deployables"]["shop"]["path"], ".")
            written = [line for line in (repo / "delivery/.written").read_text().splitlines() if line]
            self.assertEqual(subprocess.run(["git", "status", "--porcelain"], cwd=repo, text=True,
                                            capture_output=True).stdout, "")  # adopt committed it, on main
            git(repo, "checkout", "-q", "-b", "slice/S1")
            self.green(repo, "tests/test_x.py", "test/a.test.js", "src/index.js")
            self.refused(repo, "Makefile", written[0], written[-1], ".github/workflows/verify-delivery.yml")


if __name__ == "__main__":
    unittest.main()
