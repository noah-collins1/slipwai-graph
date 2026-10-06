"""What cannot be established runs everything (S38 R4, AC-S38-4 (a), -8 (b), -10, -14 (b)): the *full* rows of the path
rules, each named with its rule, and a path no rule claims.

A slice branch is cut from `main` with nothing else changed, so the path under test is the whole change set.
"""
from __future__ import annotations

import sys

from select_fixture import SelectCase, git

sys.dont_write_bytecode = True

ALL = ["test_a", "test_b", "test_c"]
BROADENS = "its effect cannot be established"
# Data-model *The path rules*, first row: every path that is full, with the rule that names it.
FULL = {
    "catalog.json": "the catalog",
    "assets/backing-services/prune.py": "the pruner",
    "src/mod.py": "the generator",
    "Makefile": "the root Makefile",
    "scripts/verify": "the verify script",
    "requirements-dev.txt": "the pinned development tooling",
    "pyproject.toml": "the package definition",
    "VERSION": "the version",
    "project.json": "the project record",
    "slipwai": "the command's launcher",
    ".gitignore": "the ignore rules",
    ".gitattributes": "the attribute rules",
    "scripts/select-tests.py": "the selector",
    "scripts/select_tests/__init__.py": "the selector",
    "tests/test_select_tests_x.py": "the selector's own tests",
    "tests/select_fixture.py": "the selector's own tests",
}
# Rows that claim a path with an effect of its own: none of them makes the run whole.
CLAIMED = ("assets/languages/go/x.go", "assets/languages/java/build/pom.xml", "assets/frontends/react-vite/x",
           "assets/profiles/standard/x", "assets/targets/aws/x", "assets/toolkit/scripts/x.py", "assets/adoption/x",
           "assets/backing-services/keycloak/x", "assets/backing-services/docker-compose.yml",
           "assets/backing-services/go/x.go", "docs/x.md", "specs/x.md", "delivery/x.md", ".github/x.yml",
           "changelog.d/x.md", "coordination-lean/x.md", "scripts/other.py", "README.md", "AGENTS.md",
           "tests/test_a.py", "tests/support.py", "tests/fixtures/x.txt")


class PathCase(SelectCase):
    def line_for(self, *paths: str) -> str:
        """The first line of a selector run on a fresh slice branch that changed exactly `paths`."""
        git(self.repo, "reset", "-q", "--hard")
        git(self.repo, "clean", "-fdq")
        self.branch("slice/x")
        for path in paths:
            target = self.repo / path
            self.write(path, (target.read_text(encoding="utf-8") if target.is_file() else "") + "\n# changed\n")
        done = self.selector()
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertEqual(self.modules_run(), ALL)
        lines = done.stdout.splitlines()
        return lines[0] if lines else ""


class TestTheFullRows(PathCase):
    def test_the_first_changed_path_that_broadens_is_named_with_its_rule(self) -> None:
        self.assertEqual(self.line_for("catalog.json", "Makefile"),
                         f"full: `Makefile` changed — the root Makefile: {BROADENS}")

    def test_every_listed_path_runs_every_module_and_names_its_own_rule(self) -> None:
        for path, rule in FULL.items():
            with self.subTest(path=path):
                self.assertEqual(self.line_for(path), f"full: `{path}` changed — {rule}: {BROADENS}")

    def test_a_path_under_a_rule_of_its_own_does_not_make_the_run_whole(self) -> None:
        for path in CLAIMED:
            with self.subTest(path=path):
                self.assertTrue(self.line_for(path).startswith("compared with `main` at "))


class TestAPathNoRuleClaims(PathCase):
    def test_a_new_directory_under_assets_is_not_claimed(self) -> None:
        for path in ("assets/newthing/x", "assets/backing-services/unknown/x", "assets/README.md",
                     "assets/frontends/unknown/x", "assets/languages/unknown/x"):
            with self.subTest(path=path):
                self.assertEqual(self.line_for(path), f"full: `{path}` changed — no rule claims it")

    def test_a_top_level_file_no_row_claims_is_not_claimed(self) -> None:
        self.assertEqual(self.line_for("notes.txt"), "full: `notes.txt` changed — no rule claims it")
        self.assertEqual(self.line_for("tools/x.py"), "full: `tools/x.py` changed — no rule claims it")

    def test_a_claimed_path_after_an_unclaimed_one_does_not_hide_it(self) -> None:
        self.assertEqual(self.line_for("README.md", "notes.txt"), "full: `notes.txt` changed — no rule claims it")


class TestACatalogThatCannotBeRead(PathCase):
    def test_an_unreadable_catalog_that_did_not_change_cannot_say_what_a_path_reaches(self) -> None:
        self.write("catalog.json", "{not json")
        self.commit("a broken catalog on the trunk")
        self.assertTrue(self.line_for("assets/languages/go/x.go").startswith(
            "full: the change set cannot be established — catalog.json cannot be read: "))
