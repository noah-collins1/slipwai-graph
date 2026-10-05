"""R6, R7 (AC-S03-38, -39): the recipe runs from where it was started, and `ci` is the checks' own target.

Each example is a reproduction an adversary pass found, run against a generated project with the fixture's stand-ins:
a make reached through a directory whose name holds a space, `make -f build.mk verify` in a project with no file named
`Makefile`, and `ci` reached by a route the goals do not show (a prerequisite of another target, `MAKECMDGOALS`
overridden). What ran is read from the stand-ins' log, and the stamp from its bytes, never from a printed line.
"""
from __future__ import annotations

import re
import subprocess
import tempfile

from stamp_fixture import StampTestCase, write_spaced_make
from support import FactoryTestCase
from test_add_service import add_service

from slipwai.catalog import CATALOG

PIP_AUDIT = "#!/bin/sh\nprintf 'pip-audit\\t%s\\n' \"$*\" >> \"$STANDIN_LOG\"\nexit 0\n"


class RecipeRunsFromWhereItStartedTest(StampTestCase):
    def test_a_make_whose_path_holds_a_space_runs_the_gate_records_and_reuses(self) -> None:
        make = write_spaced_make(self.bin.parent)
        env = self.environment()
        first = subprocess.run([str(make), "verify"], cwd=self.repo, env=env, text=True, capture_output=True,
                               timeout=180)
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        self.assertTrue(self.checks(), "no check started through a make whose path holds a space")
        self.assertIsNotNone(self.stamp_path(), "the pass was not recorded")
        self.forget_log()
        again = subprocess.run([str(make), "verify"], cwd=self.repo, env=env, text=True, capture_output=True,
                               timeout=180)
        self.assertEqual(again.returncode, 0, again.stdout + again.stderr)
        self.assertEqual(self.checks(), [], "the second run did not reuse")
        self.assertIn("did not run", again.stdout)

    def test_make_dash_f_a_file_not_named_makefile_runs_the_gate_and_records_nothing(self) -> None:
        """T049 (adversary B1): the gate still runs from the file make was given, but a stamp is for the project's own
        `Makefile` alone, so none is written and the next run runs the checks again."""
        (self.repo / "Makefile").rename(self.repo / "build.mk")
        first = self.run_gate(args=["-f", "build.mk"])
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        self.assertTrue(self.checks(), "no check started")
        self.assertIsNone(self.stamp_path(), "a pass under a makefile that is not the project's was recorded")
        self.assertIn("was not recorded", first.stdout)
        self.forget_log()
        again = self.run_gate(args=["-f", "build.mk"])
        self.assertEqual(again.returncode, 0, again.stdout + again.stderr)
        self.assertTrue(self.checks(), "the second run reused a stamp that was never written")


class CiIsTheChecksOwnTargetTest(StampTestCase):
    def ran(self, *arguments: str) -> tuple[subprocess.CompletedProcess[str], bytes]:
        """`make <arguments>` on a tree with a stamp that a run allowed to read would reuse; the run and the stamp's
        bytes afterwards."""
        audit = self.bin / "pip-audit"
        audit.write_text(PIP_AUDIT, encoding="utf-8")
        audit.chmod(0o755)
        with (self.repo / "Makefile").open("a", encoding="utf-8") as handle:
            handle.write("\nrelease: ci\n\t@echo released\n")
        planted = self.plant_stamp()
        self.forget_log()
        run = subprocess.run(["make", *arguments], cwd=self.repo, env=self.environment(), text=True,
                             capture_output=True, timeout=180)
        path = self.stamp_path()
        self.assertEqual(path.read_bytes() if path else None, planted, "the stamp moved")
        return run, planted

    def assert_every_check_and_no_stamp_line(self, run: subprocess.CompletedProcess[str]) -> None:
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertTrue(self.checks(), "no check started: " + run.stdout[-300:])
        self.assertEqual(self.reuse_lines(run), [], "a stamp line was printed")

    def test_ci_as_a_prerequisite_of_another_target_runs_every_check_and_touches_no_stamp(self) -> None:
        run, _ = self.ran("release")
        self.assert_every_check_and_no_stamp_line(run)

    def test_ci_with_the_goals_overridden_runs_every_check_and_touches_no_stamp(self) -> None:
        run, _ = self.ran("ci", "MAKECMDGOALS=verify")
        self.assert_every_check_and_no_stamp_line(run)

    def test_ci_runs_the_audit_and_the_integration_tests_and_a_failing_check_leaves_the_stamp(self) -> None:
        run, planted = self.ran("ci")
        self.assert_every_check_and_no_stamp_line(run)
        self.assertIn("pip-audit\t", self.log.read_text(encoding="utf-8"))
        self.assertIn("test-integration:", run.stdout)
        self.forget_log()
        failed = subprocess.run(["make", "ci"], cwd=self.repo, env=self.environment({"STANDIN_UV_FAIL": "1"}),
                                text=True, capture_output=True, timeout=180)
        self.assertNotEqual(failed.returncode, 0)
        path = self.stamp_path()
        self.assertIsNotNone(path, "a failing ci removed the stamp")
        assert path is not None
        self.assertEqual(path.read_bytes(), planted)


class EveryStampedShapeTakesTheRecipeTest(FactoryTestCase):
    def assert_recipe(self, makefile: str) -> None:
        ci = re.search(r"^ci:\s*(.*?)(?: ##.*)?$", makefile, re.M)
        assert ci is not None
        self.assertEqual(ci.group(1).split()[0], "verify-checks", ci.group(0))
        self.assertNotIn("verify", [word for word in ci.group(1).split() if word != "verify-checks"])
        recipe = re.search(r"^verify:.*\n((?:\t.*\n)+)", makefile, re.M)
        assert recipe is not None
        self.assertIn('"$(MAKE)" $(VERIFY_GROUP) --no-print-directory -f "$(firstword $(MAKEFILE_LIST))" verify-checks',
                      recipe.group(1))
        self.assertNotIn("--goals", recipe.group(1))
        self.assertNotIn("MAKECMDGOALS", recipe.group(1))

    def test_ci_waits_on_the_checks_and_the_recipe_quotes_its_make_for_every_shape(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            for backend in CATALOG["backends"]:
                for http in (None, "none"):
                    with self.subTest(backend=backend, http=http):
                        axes = {} if http is None else {"http": http}
                        repo = self.generate(directory, f"{backend}-{http or 'with'}", "standard", backend, **axes)
                        self.assert_recipe((repo / "Makefile").read_text())
            with self.subTest("a browser app"):
                repo = self.generate(directory, "web", "standard", "python", "react-vite", http="none")
                self.assert_recipe((repo / "Makefile").read_text())
            with self.subTest("several services"):
                repo = self.generate(directory, "grown", "standard", "python", http="none")
                self.assertEqual(add_service(repo, "payments").returncode, 0)
                self.assert_recipe((repo / "Makefile").read_text())
