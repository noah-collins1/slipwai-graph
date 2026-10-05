"""T049 (adversary B1, B2, B8 · AC-S06-9, -10; D146): the stamp and the baseline are written only when make read the
project's own root `Makefile`, under the factory's shell.

`-f <other>` and `MAKEFILES=<file>` run a sub-make over a makefile the factory did not write, a `GNUmakefile` or a
`makefile` is read in place of `Makefile`, and `.SHELLFLAGS` in the environment reaches every recipe. None of these is
in `MAKEFLAGS`, so D146's one predicate (`makeflags_problem` in `verify-stamp.py`) also asks for them: `make verify`
writes neither stamp nor baseline and says why in one line, and the scoped run is the full gate through
`make verify` on the project's `Makefile`, whatever makefile the scoped target itself was read from.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from scoped_fixture import FULL
from stamp_fixture import load_script
from test_verify_scoped_baseline import BaselineTest
from test_verify_scoped_sum import RuleCase

sys.dont_write_bytecode = True

OTHER = "other.mk"
FORMS = (["-f", OTHER], [f"--file={OTHER}"], ["--makefile", OTHER], [f"-f{OTHER}"], ["-k", f"-f{OTHER}"],
         ["-kf", OTHER], ["-f", "Makefile", "-f", OTHER], ["-f", "./" + OTHER])


# What `MAKEFILES` reads before the `Makefile`: a `verify-checks` that passes, which the `Makefile`'s own rule then
# overrides, and which a sub-make over this file alone would run in its place.
STAND_IN = "verify-checks:\n\t@true\n"


IGNORED = "\n".join((OTHER, "extra.mk", "GNUmakefile", "makefile")) + "\n"


def copy_aside(repo: Path) -> None:
    """`other.mk`, the text of the `Makefile`, git ignoring it so that it is not a file the slice reaches with."""
    shutil.copy(repo / "Makefile", repo / OTHER)
    (repo / "extra.mk").write_text(STAND_IN, encoding="utf-8")
    exclude = repo / ".git" / "info" / "exclude"
    exclude.parent.mkdir(exist_ok=True)
    exclude.write_text((exclude.read_text(encoding="utf-8") if exclude.exists() else "") + IGNORED,
                       encoding="utf-8")


class PredicateTest(BaselineTest):
    def problem(self, environ: dict[str, str]) -> str | None:
        return load_script(self.repo).makeflags_problem(environ)

    def test_e1_makefiles_in_the_environment_is_named(self) -> None:
        found = self.problem({"MAKEFILES": "extra.mk"})
        self.assertIn("`MAKEFILES`", found or "")

    def test_e1_an_empty_makefiles_adds_nothing(self) -> None:
        self.assertIsNone(self.problem({"MAKEFILES": ""}))

    def test_e2_shellflags_in_the_environment_is_named_with_or_without_a_value(self) -> None:
        for value in ("-ec", "", "-c"):
            with self.subTest(value=value):
                self.assertIn("`.SHELLFLAGS`", self.problem({".SHELLFLAGS": value}) or "")

    def test_e2_shell_in_the_environment_is_not_what_make_runs_recipes_under(self) -> None:
        """The `Makefile` says `SHELL := /bin/bash`, which an environment `SHELL` never overrides (without `-e`)."""
        self.assertIsNone(self.problem({"SHELL": "/bin/true"}))


class StampDeclinesTest(BaselineTest):
    def gate(self, args: list[str], env: dict[str, str | None] | None = None) -> subprocess.CompletedProcess[str]:
        done = subprocess.run(["make", *args, "verify"], cwd=self.repo, env=self.environment(env), text=True,
                              capture_output=True, timeout=180)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        return done

    def copies(self) -> None:
        copy_aside(self.repo)

    def declined(self, run: subprocess.CompletedProcess[str], word: str) -> None:
        self.assertEqual(self.stamp_files(), [])
        self.assertIsNone(self.baseline_path())
        said = [line for line in run.stdout.splitlines() if "was not recorded" in line]
        self.assertEqual(len(said), 1, run.stdout)
        self.assertIn(word, said[0])

    def stamp_files(self) -> list[Path]:
        return sorted((self.repo / ".git" / "slipwai").glob("verify-stamp-*.json"))

    def test_e1_a_makefile_named_with_f_in_any_spelling_writes_no_stamp_and_no_baseline(self) -> None:
        self.copies()
        for form in FORMS:
            with self.subTest(form=form):
                self.declined(self.gate(form), OTHER)

    def test_e1_makefiles_writes_no_stamp_and_no_baseline(self) -> None:
        copy_aside(self.repo)
        self.declined(self.gate([], {"MAKEFILES": "extra.mk"}), "MAKEFILES")

    def test_e1_a_gnumakefile_or_makefile_that_make_reads_instead_writes_no_stamp_and_no_baseline(self) -> None:
        self.copies()
        for name in ("GNUmakefile", "makefile"):
            with self.subTest(name=name):
                (self.repo / name).write_text("include Makefile\n", encoding="utf-8")
                self.declined(self.gate([]), name)
                (self.repo / name).unlink()

    def test_e2_shellflags_from_the_environment_writes_no_stamp_and_no_baseline(self) -> None:
        self.declined(self.gate([], {".SHELLFLAGS": "-ec"}), ".SHELLFLAGS")

    def test_e3_the_projects_own_makefile_named_or_not_still_writes_both(self) -> None:
        cases: list[tuple[list[str], dict[str, str | None] | None]] = [
            ([], None), (["-f", "Makefile"], None), (["-f", "./Makefile"], None),
            (["--file", str(self.repo / "Makefile")], None), (["-k"], None),
            ([], {"SHELL": "/bin/sh"}), ([], {"MAKEFILES": ""})]
        for args, env in cases:
            with self.subTest(args=args, env=env):
                for stale in (self.stamp_files() + [self.baseline_path() or self.repo / "none"]):
                    stale.unlink(missing_ok=True)
                self.move_tree()
                run = self.gate(args, env)
                self.assertEqual(len(self.stamp_files()), 1, run.stdout)
                self.assertIsNotNone(self.baseline_path())
                self.assertNotIn("was not recorded", run.stdout)


class ScopedFallbackTest(RuleCase):
    def setUp(self) -> None:
        super().setUp()
        copy_aside(self.repo)  # before the baseline it is compared with, as a file git ignores is part of it
        self.trunk(change=lambda _repo: None)
        self.forbidden()

    def scoped_over(
        self, args: list[str], env: dict[str, str | None] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["make", *args, "verify-scoped"], cwd=self.repo, env=self.environment(env), text=True,
                              capture_output=True, timeout=180)

    def the_full_gate_on_the_projects_makefile(self, run: subprocess.CompletedProcess[str], word: str) -> None:
        first = self.scoped_lines(run)[0]
        self.assertTrue(first.startswith(FULL), first)
        self.assertIn(word, first)
        calls = self.verify_calls()
        self.assertEqual(len(calls), 1, run.stdout)
        self.assertIn("-f Makefile ", calls[0] + " ")
        self.assertNotIn(OTHER, calls[0])
        self.assertNotIn("No rule", run.stdout + run.stderr)
        self.assertEqual(self.lines(run), [])

    def test_b8_makefiles_runs_make_verify_on_the_makefile_not_on_the_added_file(self) -> None:
        run = self.scoped_over([], {"MAKEFILES": "extra.mk"})
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.the_full_gate_on_the_projects_makefile(run, "MAKEFILES")

    def test_b1_f_other_is_the_full_gate_through_the_projects_makefile(self) -> None:
        run = self.scoped_over(["-f", OTHER])
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.the_full_gate_on_the_projects_makefile(run, "")
        self.assertNotIn("run  ", run.stdout)

    def test_b1_f_other_with_the_projects_text_is_still_the_full_gate(self) -> None:
        """`other.mk` is a copy of the text the factory wrote, so the text border passes; make's own `-f` does not."""
        run = self.scoped_over(["-f", OTHER])
        self.assertIn(OTHER, self.scoped_lines(run)[0])

    def test_b2_shellflags_in_the_environment_is_the_full_gate(self) -> None:
        run = self.scoped_over([], {".SHELLFLAGS": "-ec"})
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.the_full_gate_on_the_projects_makefile(run, ".SHELLFLAGS")

    def test_b8_a_gnumakefile_runs_make_verify_on_the_makefile(self) -> None:
        (self.repo / "GNUmakefile").write_text("include Makefile\n", encoding="utf-8")
        run = self.scoped_over([])
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.the_full_gate_on_the_projects_makefile(run, "GNUmakefile")
