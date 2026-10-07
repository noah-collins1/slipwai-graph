"""The scripts the selector itself runs are judged by their bytes, not by themselves (S38 T050, adversary A1).

`changes.changed` and `check-slice-scope.py` report what changed; a regression committed in them beside a test edit
would hide both. The selector compares each file it runs with the base's bytes, independently of those scripts, and a
difference is a full run whose one line names the file.
"""
from __future__ import annotations

import sys

from select_fixture import SelectCase, git

sys.dont_write_bytecode = True

SCRIPTS = "assets/toolkit/scripts/"
CHANGES = SCRIPTS + "verify_scoped/changes.py"
ALL = ["test_a", "test_b", "test_c"]
BLIND = "\n\ndef changed(scope, base):  # a regression: nothing ever changed\n    return []\n"


class TestTheSelectorsOwnScriptsAreJudgedByTheirBytes(SelectCase):
    def narrowed_run(self) -> list[str]:
        self.write("tests/test_a.py", self.read("tests/test_a.py") + "\n# edit\n")
        self.commit("edit a test")
        done = self.selector()
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        return done.stdout.splitlines()

    def short(self) -> str:
        return git(self.repo, "rev-parse", "--short", "main").strip()

    def read(self, name: str) -> str:
        return (self.repo / name).read_text(encoding="utf-8")

    def test_an_untouched_selector_narrows(self) -> None:
        self.branch("slice/x")
        self.assertEqual(self.narrowed_run()[0], "compared with `main` at " + self.short() + " (the trunk)")

    def test_a_regression_in_changes_changed_beside_a_test_edit_does_not_narrow(self) -> None:
        self.branch("slice/x")
        self.write(CHANGES, self.read(CHANGES) + BLIND)
        lines = self.narrowed_run()
        self.assertEqual(self.modules_run(), ALL)
        self.assertTrue(lines[0].startswith(f"full: `{CHANGES}` "), lines)

    def test_each_file_the_selector_runs_is_compared(self) -> None:
        for name in (SCRIPTS + "check-slice-scope.py", "scripts/select-tests.py", "scripts/select_tests/choose.py",
                     SCRIPTS + "verify_scoped/__init__.py"):
            with self.subTest(name):
                self.branch("slice/x")
                self.write(name, self.read(name) + "\n# changed\n")
                lines = self.narrowed_run()
                self.assertEqual(self.modules_run(), ALL)
                self.assertIn(f"`{name}`", lines[0])
                git(self.repo, "checkout", "-q", "main")
                git(self.repo, "branch", "-q", "-D", "slice/x")
                git(self.repo, "checkout", "-q", "--", ".")

    def test_a_file_added_beside_them_is_a_difference_too(self) -> None:
        self.branch("slice/x")
        self.write("scripts/select_tests/extra.py", "X = 1\n")
        lines = self.narrowed_run()
        self.assertEqual(self.modules_run(), ALL)
        self.assertIn("`scripts/select_tests/extra.py`", lines[0])

    def test_an_uncommitted_edit_is_a_difference(self) -> None:
        self.branch("slice/x")
        self.write("tests/test_a.py", self.read("tests/test_a.py") + "\n# edit\n")
        self.write(CHANGES, self.read(CHANGES) + BLIND)
        done = self.selector()
        self.assertEqual(self.modules_run(), ALL)
        self.assertIn(f"`{CHANGES}`", done.stdout.splitlines()[0])
