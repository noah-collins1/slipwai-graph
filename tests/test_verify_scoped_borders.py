"""R1 (AC-S06-1, -14): `make verify-scoped` is the full gate wherever it cannot read the branch.

Every border prints one line, `verify-scoped: the full gate runs, as `make verify` — <reason>`, and then runs
`make verify` and exits with its status. The borders are asked in a fixed order and the first that holds is the only
one said. Until later rules select by what changed, a slice branch with a usable base is the full gate too, so the
target is never wrong in between. What ran is read from the stand-ins' log; a stamp is neither read nor written
outside a slice branch.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scoped_fixture import FULL, SLICE, ScopedCase, ShapeCase
from stamp_fixture import CI_MARKERS, CLOSING, git
from support import FactoryTestCase
from test_scoped_targets import SHAPES, build
from test_verify_stamp_scan import makefile_rules

sys.dont_write_bytecode = True


class BordersTest(ScopedCase):
    def assert_full_gate(self, run: subprocess.CompletedProcess[str], reason: str) -> None:
        """One line, the reason in it, and then `make verify` ran: its closing line is the run's last."""
        lines = self.scoped_lines(run)
        self.assertEqual(lines, [FULL + reason], run.stdout + run.stderr)
        self.assertEqual(run.stdout.splitlines()[0], lines[0], "the line is not the first said")
        self.assertEqual(len(self.verify_calls()), 1, "`make verify` was not run exactly once")
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertTrue(run.stdout.endswith(f"\n{CLOSING}\n"), run.stdout[-200:])

    def test_e1_on_the_trunk_the_line_names_it_and_make_verify_runs_without_a_stamp(self) -> None:
        self.checkout("main")
        run = self.scoped()
        self.assert_full_gate(run, "this is the trunk (`main`)")
        self.assertIsNone(self.stamp_path(), "a stamp was written on the trunk")

    def test_e2_on_another_branch_the_line_names_the_branch(self) -> None:
        self.checkout("-b", "feature/x")
        self.assert_full_gate(self.scoped(), "`feature/x` is not a slice/<id> branch")

    def test_e3_a_ci_marker_names_it(self) -> None:
        for marker in CI_MARKERS:
            with self.subTest(marker=marker):
                self.forget_log()
                self.assert_full_gate(self.scoped({marker: "1"}), f"{marker} is set, so this is a CI run")

    def test_e4_no_trunk_ref_carries_check_slice_scopes_reason(self) -> None:
        git(self.repo, "branch", "-D", "main")
        run = self.scoped()
        (line,) = self.scoped_lines(run)
        self.assertTrue(line.startswith(FULL + f"no usable base: {SLICE} has no "), line)
        self.assertIn("has no `main` to compare with", line)
        self.assertEqual(len(self.verify_calls()), 1)

    def test_e5_verify_force_runs_a_forced_gate(self) -> None:
        run = self.scoped({"VERIFY_FORCE": "1"})
        self.assertEqual(self.scoped_lines(run), [FULL + "VERIFY_FORCE=1"])
        self.assertIn("verify: the full gate runs, forced by VERIFY_FORCE=1", run.stdout)
        self.assertEqual(len(self.verify_calls()), 1)

    def test_e6_a_detached_head_and_an_unborn_one(self) -> None:
        self.checkout("--detach")
        self.assertEqual(self.scoped_lines(self.scoped()), [FULL + "HEAD is detached"])
        self.checkout("--orphan", "fresh")
        self.forget_log()
        self.assertEqual(self.scoped_lines(self.scoped()), [FULL + "HEAD names no commit"])
        self.assertEqual(len(self.verify_calls()), 1)

    def test_e7_make_flags_that_start_no_check_are_named(self) -> None:
        for flag in ("n", "t", "q"):
            with self.subTest(flag=flag):
                self.forget_log()
                run = self.scoped(args=[f"-{flag}"])
                self.assertEqual(self.scoped_lines(run), [FULL + f"make was run with -{flag}"], run.stdout + run.stderr)
                self.assertEqual(len(self.verify_calls()), 1)

    def test_e8_a_trunk_the_gate_cannot_tell_says_verify_stamps_words(self) -> None:
        record = self.repo / "project.json"
        data = json.loads(record.read_text(encoding="utf-8"))
        data["ci"] = {"branch": "nonsense"}
        record.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        run = self.scoped()
        (line,) = self.scoped_lines(run)
        self.assertTrue(line.startswith(FULL + "the trunk cannot be told — "), line)
        self.assertIn("project.json records ci.branch as `nonsense`", line)
        self.assertEqual(len(self.verify_calls()), 1)

    def test_e8_the_order_is_fixed_and_a_case_where_two_hold_prints_the_first_only(self) -> None:
        self.checkout("-b", "feature/y")
        run = self.scoped({"VERIFY_FORCE": "1", "CI": "1"}, ["-n"])
        self.assertEqual(self.scoped_lines(run), [FULL + "make was run with -n"], run.stdout)
        self.forget_log()
        run = self.scoped({"VERIFY_FORCE": "1", "CI": "1"})
        self.assertEqual(self.scoped_lines(run), [FULL + "CI is set, so this is a CI run"])
        self.forget_log()
        run = self.scoped({"VERIFY_FORCE": "1"})
        self.assertEqual(self.scoped_lines(run), [FULL + "VERIFY_FORCE=1"])
        self.forget_log()
        self.checkout("--detach")
        run = self.scoped()
        self.assertEqual(self.scoped_lines(run), [FULL + "HEAD is detached"])

    def test_e9_a_failing_check_is_make_verifys_status(self) -> None:
        self.checkout("main")
        scoped = self.scoped({"STANDIN_UV_FAIL": "1"})
        direct = self.run_gate({"STANDIN_UV_FAIL": "1"})
        self.assertNotEqual(direct.returncode, 0, direct.stdout)
        self.assertEqual(scoped.returncode, direct.returncode, scoped.stdout + scoped.stderr)
        self.assertEqual(self.scoped_lines(scoped), [FULL + "this is the trunk (`main`)"])
        self.assertIn("verify: the gate did not pass", scoped.stdout)

    def test_e11_the_script_ships_without_a_service_path_and_importing_it_writes_no_bytecode(self) -> None:
        scripts = self.repo / "scripts"
        files = [scripts / "verify-scoped.py", *sorted((scripts / "verify_scoped").rglob("*.py"))]
        self.assertTrue(all(path.is_file() for path in files), files)
        for path in files:
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("apps/service", text, path.name)
            self.assertNotIn("apps/web", text, path.name)
        probe = ("import importlib.util, sys; spec = importlib.util.spec_from_file_location('m', sys.argv[1]);"
                 " module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)")
        done = subprocess.run([sys.executable, "-B", "-c", probe, str(scripts / "verify-scoped.py")], cwd=self.repo,
                              capture_output=True, text=True, timeout=60)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(git(self.repo, "status", "--porcelain"), "", "importing the script left a file")
        self.assertEqual(list(Path(self.repo).rglob("__pycache__")), [])


class IndexBorderTest(ShapeCase):
    """T044 (G2 · AC-S06-1, -5): an index the stamp will not vouch for is the full gate, in the stamp's own words. Git
    does not look at such an entry, so a change to it would be skipped and `passed` said of a tree no check read."""

    def full(self, reason: str) -> None:
        run = self.scoped()
        self.assertEqual(self.scoped_lines(run), [FULL + reason], run.stdout + run.stderr)
        self.assertEqual(len(self.verify_calls()), 1)
        self.assertEqual(self.lines(run), [])

    def changed(self) -> str:
        path = "apps/service/src/main.ts"
        self.edit(path, "\n// a change git is told not to look at\n")
        return path

    def test_e12_an_entry_marked_assume_unchanged_is_the_full_gate(self) -> None:
        path = self.changed()
        git(self.repo, "update-index", "--assume-unchanged", path)
        self.full(f"{path} is marked assume-unchanged, so git does not look at it")

    def test_e12_an_entry_marked_skip_worktree_is_the_full_gate(self) -> None:
        path = self.changed()
        git(self.repo, "update-index", "--skip-worktree", path)
        self.full(f"{path} is marked skip-worktree, so git does not look at it")

    def test_e12_a_sparse_checkout_is_the_full_gate(self) -> None:
        self.changed()
        git(self.repo, "sparse-checkout", "set", "--no-cone", "/*", "!/apps/web/")
        run = self.scoped()
        (line,) = self.scoped_lines(run)
        self.assertRegex(line, r"^verify-scoped: the full gate runs, as `make verify` — apps/web/\S+ is marked "
                               r"skip-worktree, so git does not look at it$")
        self.assertEqual(len(self.verify_calls()), 1)

    def test_e12_a_submodule_is_the_full_gate(self) -> None:
        self.changed()
        git(self.repo, "update-index", "--add", "--cacheinfo", "160000," + git(self.repo, "rev-parse", "HEAD").strip()
            + ",vendor/lib")
        self.full("vendor/lib is a submodule (an index entry of mode 160000)")

    def test_e12_an_index_the_stamp_would_vouch_for_stays_scoped(self) -> None:
        self.changed()
        run = self.scoped()
        self.assertEqual(self.verify_calls(), [], run.stdout)


class SuffixHoldsTest(unittest.TestCase):
    def test_e10_hold_the_suffix_defines_no_gate_rule_in_any_shape(self) -> None:
        """HOLD (teeth: a `verify:` rule in the suffix fails it): `verify`, `verify-checks` and `ci` are the gate's."""
        case = FactoryTestCase()
        parent = Path(tempfile.mkdtemp(prefix="scoped-borders-"))
        self.addCleanup(shutil.rmtree, parent, ignore_errors=True)
        for name in SHAPES:
            with self.subTest(shape=name):
                text = (build(parent, name, case) / "Makefile").read_text(encoding="utf-8")
                section = text.split("\n# Scoped gate")[1]
                self.assertIn("verify-scoped", section, "no verify-scoped rule")
                defined = set(makefile_rules(section))
                self.assertFalse(defined & {"verify", "verify-checks", "ci"}, defined)


if __name__ == "__main__":
    unittest.main()
