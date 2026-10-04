"""R2 of S05-xdist: the project's `parallelSafe` mark reaches the gate's pytest, read each time the gate runs.

A generated Python project, `./scripts/verify <mode>` run from its root with a stand-in `uv` first on `PATH`;
the evidence is the stand-in's log of the `pytest` lines, never a printed line and never a clock.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

from parallel_gate import gate_environment, run_lines, shape, write_stand_ins
from stamp_fixture import PYVENV_CFG

sys.dont_write_bytecode = True

FLAGS = "-n auto --maxprocesses 4"
# The stock stand-in exits 0 for everything; this wrapper lets a test make pytest exit with a chosen
# status (5: nothing selected).
WRAPPER = """#!/bin/sh
case " $* " in
  *" pytest "*)
    if [ -n "${STANDIN_PYTEST_EXIT:-}" ]; then
      printf 'start\\t%s\\n' "$*" >> "$STANDIN_LOG"
      printf 'end\\t%s\\n' "$*" >> "$STANDIN_LOG"
      exit "$STANDIN_PYTEST_EXIT"
    fi ;;
esac
exec "$(dirname "$0")/uv-stock" "$@"
"""


class MarkReachesPytest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="xdist-gate-"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.bin = self.root / "bin"
        self.log = self.root / "log"
        self.repo = self.root / "project"

    def project(self, name: str = "plain") -> None:
        shutil.copytree(shape(name), self.repo, symlinks=True)
        self.original = (self.repo / "project.json").read_text(encoding="utf-8")
        write_stand_ins(self.bin)
        (self.bin / "uv").rename(self.bin / "uv-stock")
        (self.bin / "uv").write_text(WRAPPER, encoding="utf-8")
        (self.bin / "uv").chmod(0o755)
        for manifest in sorted(self.repo.glob("apps/*/pyproject.toml")):
            (manifest.parent / ".venv").mkdir(exist_ok=True)
            (manifest.parent / ".venv" / "pyvenv.cfg").write_text(PYVENV_CFG, encoding="utf-8")

    def mark(self, value: object = ..., raw: str | None = None) -> None:
        """Write `parallelSafe` (`...` removes it), or the file's raw text, or (raw="") delete the file."""
        path = self.repo / "project.json"
        if raw is not None:
            if raw == "":
                path.unlink()
            else:
                path.write_text(raw, encoding="utf-8")
            return
        document = json.loads(self.original)
        document.pop("parallelSafe", None)
        if value is not ...:
            document["parallelSafe"] = value
        path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")

    def verify(self, *mode: str, pytest_exit: str | None = None) -> subprocess.CompletedProcess[str]:
        self.log.write_text("", encoding="utf-8")
        env = gate_environment(self.bin, self.log, {"STANDIN_PYTEST_EXIT": pytest_exit})
        return subprocess.run(
            ["./scripts/verify", *mode], cwd=self.repo, env=env, text=True, capture_output=True, timeout=120
        )

    def pytest_lines(self, *mode: str, **keywords: str | None) -> list[str]:
        result = self.verify(*mode, **keywords)
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = [line for line in run_lines(self.log) if " pytest " in f" {line} "]
        self.assertTrue(lines, f"no pytest ran in {mode}")
        return lines

    def without_flags(self, line: str) -> str:
        return " ".join(line.replace(FLAGS, "").split())

    def test_true_puts_the_flags_on_every_mode_that_takes_them(self):
        self.project()
        for mode in ("--test-only", "--adversarial-only", "all"):
            with self.subTest(mode=mode):
                for line in self.pytest_lines(*([mode] if mode != "all" else [])):
                    self.assertIn(f"pytest {FLAGS} ", line)

    def test_each_of_two_services_carries_the_flags(self):
        self.project("two")
        lines = self.pytest_lines("--test-only")
        self.assertEqual(len(lines), 2)
        for line in lines:
            self.assertIn(FLAGS, line)
        self.assertEqual(len({line.split("--project ")[1].split()[0] for line in lines}), 2)

    def test_anything_but_the_json_true_is_the_serial_line_and_nothing_else_changes(self):
        self.project()
        self.mark(...)
        serial = self.pytest_lines("--test-only")
        self.assertNotIn("-n ", " ".join(serial))
        self.mark(True)
        parallel = self.pytest_lines("--test-only")
        self.assertEqual([self.without_flags(line) for line in parallel], serial)
        cases: dict[str, dict[str, Any]] = {
            "false": {"value": False}, "yes": {"value": "yes"}, "one": {"value": 1}, "string true": {"value": "true"},
            "null": {"value": None}, "not json": {"raw": "{not json"}, "absent": {"raw": ""},
            "a list": {"raw": "[true]"}, "empty": {"raw": " "},
        }
        for name, how in cases.items():
            with self.subTest(case=name):
                self.mark(True)
                self.mark(**how)
                self.assertEqual(self.pytest_lines("--test-only"), serial)

    def test_an_edit_takes_effect_on_the_next_run_with_nothing_regenerated(self):
        self.project()
        self.mark(False)
        self.assertNotIn(FLAGS, " ".join(self.pytest_lines("--test-only")))
        self.mark(True)
        self.assertIn(FLAGS, " ".join(self.pytest_lines("--test-only")))
        self.mark(False)
        self.assertNotIn(FLAGS, " ".join(self.pytest_lines("--test-only")))

    def test_the_integration_run_is_never_parallel(self):
        self.project("db")
        self.mark(True)
        lines = self.pytest_lines("--integration-only")
        self.assertNotIn("-n ", " ".join(lines))
        self.assertIn("tests/integration", lines[0])

    def test_adversarial_run_with_nothing_selected_still_exits_zero_and_carries_the_flags(self):
        self.project()
        self.mark(True)
        lines = self.pytest_lines("--adversarial-only", pytest_exit="5")
        self.assertIn(FLAGS, lines[0])
        self.assertIn("-k adversarial", lines[0])

    def test_a_failing_pytest_still_fails_the_gate(self):
        self.project()
        self.mark(True)
        self.assertEqual(self.verify("--test-only", pytest_exit="1").returncode, 1)
