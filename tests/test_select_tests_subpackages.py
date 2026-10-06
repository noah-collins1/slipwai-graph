"""A `tests/` sub-package already on the base is a module the selector cannot name, so the run is whole (T033,
AC-S38-12, -16): `unittest discover -s tests` imports it, and a selected run that left it out of its verdicts and its
total would answer differently from the full run on one commit.
"""
from __future__ import annotations

import sys

from select_fixture import STAND_IN, SelectCase, git

sys.dont_write_bytecode = True

ALL = ["test_a", "test_b", "test_c"]
NAMELESS = "a test module the selector cannot name"
BROADENS = "its effect cannot be established"


class SubPackageCase(SelectCase):
    def on_base(self, *files: str) -> None:
        for path in files:
            self.write(path, STAND_IN.format(name=path.rsplit("/", 1)[-1].removesuffix(".py"))
                       if "/test" in path else "")
        self.commit("a sub-package on the trunk")

    def go_change(self) -> None:
        git(self.repo, "reset", "-q", "--hard")
        self.branch("slice/x")
        self.write("assets/languages/go/x.go", "package x\n")

    def first_line(self) -> str:
        done = self.selector("--dry-run")
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        return done.stdout.splitlines()[0]


class TestASubPackageOnTheBase(SubPackageCase):
    def test_a_go_change_beside_it_is_a_full_run_that_names_the_module(self) -> None:
        self.on_base("tests/sub/__init__.py", "tests/sub/test_nested.py")
        self.go_change()
        self.assertEqual(self.first_line(), f"full: `tests/sub/test_nested.py` is {NAMELESS} — {BROADENS}")

    def test_the_real_run_runs_the_module_and_every_other(self) -> None:
        self.on_base("tests/sub/__init__.py", "tests/sub/test_nested.py")
        self.go_change()
        done = self.selector()
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertEqual(self.modules_run(), sorted([*ALL, "test_nested"]))

    def test_a_package_two_deep_is_found_through_its_chain(self) -> None:
        self.on_base("tests/sub/__init__.py", "tests/sub/deep/__init__.py", "tests/sub/deep/test_x.py")
        self.go_change()
        self.assertEqual(self.first_line(), f"full: `tests/sub/deep/test_x.py` is {NAMELESS} — {BROADENS}")

    def test_a_package_with_no_test_module_keeps_the_selection(self) -> None:
        self.on_base("tests/sub/__init__.py", "tests/sub/helper.py")
        self.go_change()
        self.assertTrue(self.first_line().startswith("compared with `main` at "))

    def test_a_directory_with_no_init_is_not_one_discover_enters(self) -> None:
        self.on_base("tests/data/test_x.py", "tests/sub/__init__.py", "tests/sub/deep/test_y.py")
        self.go_change()
        self.assertTrue(self.first_line().startswith("compared with `main` at "))


class TestASubPackageAddedOnTheBranch(SubPackageCase):
    def test_it_is_still_a_full_run(self) -> None:
        self.go_change()
        self.write("tests/sub/__init__.py", "")
        self.write("tests/sub/test_nested.py", "")
        self.assertIn(NAMELESS, self.first_line())
