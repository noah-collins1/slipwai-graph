"""R7, the writing half (AC-S06-9): a full green run on a slice branch leaves the baseline; any full run removes it.

`verify-stamp.py record` writes `verify-baseline-<project>.json` beside the stamp, only where it writes the stamp and
only on a `slice/<id>` branch: the branch, the tools the run asked at its start, a SHA-256 of each variable's
record — never a value — and the key's `ignored` digest (D125), no name of a file. `begin_full_run` and the ratchet
path of `reuse` remove it. What is read is the file; what ran is the stand-ins' log. The stamp's own fields are
untouched (e8), and `test_verify_stamp_*` keep holding that.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from scoped_fixture import ScopedCase
from stamp_fixture import SERVICE, load_script

sys.dont_write_bytecode = True


class BaselineTest(ScopedCase):
    def baseline_path(self) -> Path | None:
        found = sorted((self.repo / ".git" / "slipwai").glob("verify-baseline-*.json"))
        return found[0] if found else None

    def baseline(self) -> dict[str, object]:
        path = self.baseline_path()
        self.assertIsNotNone(path, "no baseline under .git/slipwai")
        assert path is not None
        return json.loads(path.read_text(encoding="utf-8"))

    def green(self, env: dict[str, str | None] | None = None) -> None:
        run = self.run_gate(env)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)

    def move_tree(self) -> None:
        (self.repo / SERVICE / "moved.txt").write_text("moved\n", encoding="utf-8")

    def digests(self, env: dict[str, str | None]) -> dict[str, str]:
        """What `variable_record` says of each name in `VARIABLES` under `env`, hashed here, never read from a file."""
        module = load_script(self.repo)
        was, here = dict(os.environ), Path.cwd()
        os.environ.clear()
        os.environ.update(self.environment(env))
        try:
            return {name: hashlib.sha256(module.variable_record(name)).hexdigest() for name in module.VARIABLES}
        finally:
            os.environ.clear()
            os.environ.update(was)
            os.chdir(here)

    def ignored_digest(self, tools: dict[str, str]) -> str:
        """The stamp key's `ignored` part, as `key_parts` computes it for the tree as it stands."""
        code = ("import importlib.util, sys\nsys.dont_write_bytecode = True\n"
                "spec = importlib.util.spec_from_file_location('stamp', 'scripts/verify-stamp.py')\n"
                "stamp = importlib.util.module_from_spec(spec)\nspec.loader.exec_module(stamp)\n"
                f"print(stamp.key_parts({tools!r})[1]['ignored'])")
        done = subprocess.run([sys.executable, "-B", "-c", code], cwd=self.repo, env=self.environment(None),
                              check=True, capture_output=True, text=True, timeout=120)
        return done.stdout.strip()

    def test_e1_a_green_run_on_a_slice_branch_writes_the_branch_the_tools_and_digests(self) -> None:
        env: dict[str, str | None] = {
            "UX_GATES_SINCE": "", "SLIPWAI_NO_INSTALL": "secret-value-1", "UX_GATES_REQUIRE": None,
        }
        self.green(env)
        written = self.baseline()
        self.assertEqual(set(written), {"branch", "tools", "variables", "ignored"})
        self.assertEqual(written["branch"], "slice/S1")
        self.assertEqual(written["tools"], self.stamp()["tools"])
        self.assertEqual(written["variables"], self.digests(env))
        self.assertEqual(written["ignored"], self.ignored_digest(written["tools"]))  # type: ignore[arg-type]
        self.assertRegex(str(written["ignored"]), r"^[0-9a-f]{64}$", "the ignored part is one digest, no name")
        text = self.baseline_path().read_text(encoding="utf-8")  # type: ignore[union-attr]
        self.assertNotIn("secret-value-1", text, "a value is in the baseline")

    def test_e1_unset_and_empty_are_told_apart(self) -> None:
        self.green({"UX_GATES_SINCE": None})
        unset = self.baseline()["variables"]["UX_GATES_SINCE"]  # type: ignore[index]
        self.move_tree()
        self.green({"UX_GATES_SINCE": ""})
        empty = self.baseline()["variables"]["UX_GATES_SINCE"]  # type: ignore[index]
        self.assertNotEqual(unset, empty)

    def test_e2_a_failing_run_leaves_none(self) -> None:
        run = self.run_gate({"STANDIN_UV_FAIL": "1"})
        self.assertNotEqual(run.returncode, 0, run.stdout)
        self.assertIsNone(self.baseline_path())

    def test_e2_a_failing_run_removes_the_one_a_green_run_left(self) -> None:
        self.green()
        self.assertIsNotNone(self.baseline_path())
        self.move_tree()
        run = self.run_gate({"STANDIN_UV_FAIL": "1"})
        self.assertNotEqual(run.returncode, 0, run.stdout)
        self.assertIsNone(self.baseline_path(), "a baseline stood through a run whose check failed")

    def test_e3_a_run_that_does_not_vouch_for_the_gate_writes_none(self) -> None:
        runs: list[tuple[str, dict[str, str | None] | None, list[str] | None]] = [
            ("-i", None, ["-i"]), ("-n", None, ["-n"]), ("-t", None, ["-t"]), ("-q", None, ["-q"]),
            ("RATCHET_TIGHTEN", {"RATCHET_TIGHTEN": "1"}, None),
        ]
        for name, env, args in runs:
            with self.subTest(run=name):
                self.run_gate(env, args)
                self.assertIsNone(self.baseline_path(), f"a run under {name} left a baseline")

    def test_e3_a_full_run_that_begins_under_i_or_the_ratchet_removes_the_one_that_stood(self) -> None:
        runs: list[tuple[str, dict[str, str | None] | None, list[str] | None]] = [
            ("-i", None, ["-i"]), ("RATCHET_TIGHTEN", {"RATCHET_TIGHTEN": "1"}, None),
        ]
        for name, env, args in runs:
            with self.subTest(run=name):
                self.green({"VERIFY_FORCE": "1"})
                self.assertIsNotNone(self.baseline_path())
                self.run_gate(env, args)
                self.assertIsNone(self.baseline_path(), f"a baseline stood through a run under {name}")

    def test_e3_a_run_that_starts_no_check_touches_the_one_that_stood(self) -> None:
        self.green()
        stood = self.baseline_path().read_bytes()  # type: ignore[union-attr]
        for flag in ("-n", "-t", "-q"):
            with self.subTest(flag=flag):
                self.run_gate(None, [flag])
                self.assertEqual(self.baseline_path().read_bytes(), stood)  # type: ignore[union-attr]

    def test_e4_the_ratchet_path_of_reuse_removes_it(self) -> None:
        self.green()
        self.run_gate({"RATCHET_TIGHTEN": "1"})
        self.assertIsNone(self.baseline_path())

    def test_e5_off_a_slice_branch_none_is_written(self) -> None:
        self.checkout("-b", "feature/x")
        self.green()
        self.assertIsNotNone(self.stamp_path(), "the gate passed and recorded: the baseline is what is absent")
        self.assertIsNone(self.baseline_path(), "a baseline was written on feature/x")
        self.checkout("main")
        self.run_gate()
        self.assertIsNone(self.baseline_path(), "a baseline was written on the trunk")
        self.checkout("--detach")
        self.run_gate()
        self.assertIsNone(self.baseline_path(), "a baseline was written on a detached HEAD")

    def test_e5_a_ci_run_on_a_slice_branch_writes_none(self) -> None:
        self.run_gate({"CI": "1"})
        self.assertIsNone(self.baseline_path())

    def test_e6_a_baseline_is_written_only_when_the_stamp_is(self) -> None:
        """The key moves during the run (a check writes a file): no stamp, so no baseline."""
        edited = self.repo / SERVICE / "edited-by-a-check.txt"
        run = self.run_gate({"STANDIN_EDIT": str(edited)})
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertIsNone(self.stamp_path(), "the key moved and a stamp was written")
        self.assertIsNone(self.baseline_path(), "a baseline was written where no stamp was")

    def test_e7_hold_a_scoped_run_never_writes_one(self) -> None:
        """HOLD over `verify-scoped.py` as it stands (teeth: make the script write one itself after the full gate).

        Where the gate under the scoped target fails it leaves none, and the script adds none of its own; on the trunk
        and off a slice branch a scoped run leaves none either."""
        run = self.scoped({"STANDIN_UV_FAIL": "1"})
        self.assertNotEqual(run.returncode, 0, run.stdout)
        self.assertIsNone(self.baseline_path(), "a scoped run left a baseline after a failing gate")
        self.checkout("main")
        self.scoped()
        self.assertIsNone(self.baseline_path(), "a scoped run left a baseline on the trunk")

    def test_e8_the_stamp_and_the_note_are_what_they_were(self) -> None:
        self.green()
        stamp = self.stamp()
        self.assertEqual(set(stamp), set(load_script(self.repo).FIELDS), "the stamp's fields moved")
        left = [path.name for path in (self.repo / ".git" / "slipwai").iterdir() if path.suffix == ".pending"]
        self.assertEqual(left, [], "the note outlived a passing run")
        self.assertEqual(self.baseline()["tools"], stamp["tools"])
        again = subprocess.run(["git", "status", "--porcelain"], cwd=self.repo, text=True, capture_output=True,
                               timeout=60).stdout
        self.assertEqual(again, "", "the baseline is written into the working tree")
