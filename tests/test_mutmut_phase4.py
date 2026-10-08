"""S42 Phase 4 (T036-T044, the adversary's findings A1-A7, B3, B5; D227, D228): what `mutmut-mutation.py` holds against
a run that is not what it seems, reproduced through the wrapper's boundary.

The harness is `test_mutmut_verdict`'s: the wrapper runs as a subprocess against a fake `uv` first on `PATH`. The fake is
that module's, read for the changes these examples need (an orphaned child of `mutmut run`, files already in `mutants/`
when generation ends, the `PYTEST_*` environment, the probe's report on where mutmut was imported from).
"""
from __future__ import annotations

import json
import os
import signal
import stat
import subprocess
import sys
import unittest
from pathlib import Path
from typing import Any

from test_mutmut_verdict import FAKE_UV, KEY, TABLE, Case, lines_of

sys.dont_write_bytecode = True
# `test_mutmut_verdict` imports `slipwai`, which reads this script on import (as `test_stryker_closure` does)
TEST_SELECTION = {"reads": ["assets/languages/python/scripts/mutmut-mutation.py",
                            "assets/toolkit/scripts/check-styles.py"]}

LOG_ENV = ('json.dumps({"argv": args, "cwd": os.getcwd()})',
           'json.dumps({"argv": args, "cwd": os.getcwd(), "env": {k: v for k, v in os.environ.items() '
           'if k.startswith("PYTEST_")}})')
ORPHAN = ('write(json.loads(os.environ.get("FAKE_RESULTS", "{}")))',
          '''if os.environ.get("FAKE_ORPHAN"):
    child = os.fork()
    if child == 0:
        os.setsid()
        null = os.open(os.devnull, os.O_RDWR)
        for descriptor in (0, 1, 2):
            os.dup2(null, descriptor)
        import time
        time.sleep(60)
        os._exit(0)
    open(os.environ["FAKE_ORPHAN"], "w").write(str(child))
write(json.loads(os.environ.get("FAKE_RESULTS", "{}")))''')


def fake_uv() -> str:
    text = FAKE_UV
    for old, new in (LOG_ENV, ORPHAN):
        assert old in text, "test_mutmut_verdict's fake uv no longer reads as this expects"
        text = text.replace(old, new)
    return text


class PhaseCase(Case):
    def setUp(self) -> None:
        super().setUp()
        (self.bin / "uv").write_text(fake_uv(), encoding="utf-8")
        (self.bin / "uv").chmod(0o755 | stat.S_IXUSR)

    def run_with(self, *arguments: str, extra: dict[str, str] | None = None,
                 **keywords: Any) -> subprocess.CompletedProcess[str]:
        """`run_wrapper` with more variables in the wrapper's environment."""
        saved = dict(os.environ)
        os.environ.update(extra or {})
        try:
            return self.run_wrapper(*arguments, **keywords)
        finally:
            os.environ.clear()
            os.environ.update(saved)


class OrphanTest(PhaseCase):
    """T036 (A1): a `mutmut run` child that outlives the wrapper keeps the lock."""

    def test_a1_a_run_that_leaves_a_child_alive_keeps_its_service_locked_and_the_next_run_is_refused(self) -> None:
        pidfile = self.root / "orphan.pid"
        first = self.run_with("apps/service", "--file", "src/pkg/a.py", extra={"FAKE_ORPHAN": str(pidfile)},
                              meta={"src/pkg/a.py": {KEY: None}}, results={"src/pkg/a.py": {KEY: 1}})
        orphan = int(pidfile.read_text(encoding="utf-8"))
        self.addCleanup(self.kill, orphan)
        self.assertEqual(first.returncode, 0)
        second = self.run_wrapper("apps/service", "--file", "src/pkg/a.py", meta={"src/pkg/a.py": {KEY: None}},
                                  results={"src/pkg/a.py": {KEY: 1}})
        self.assertEqual(second.returncode, 2)
        self.assertEqual(lines_of(second), ["mutation: another mutmut run of apps/service holds "
                                            "apps/service/.venv/mutmut-run.lock; wait for it, then run this again"])
        self.kill(orphan)
        third = self.run_wrapper("apps/service", "--file", "src/pkg/a.py", meta={"src/pkg/a.py": {KEY: None}},
                                 results={"src/pkg/a.py": {KEY: 1}})
        self.assertEqual(third.returncode, 0, "the lock is free once the child is gone")

    @staticmethod
    def kill(pid: int) -> None:
        try:
            os.kill(pid, signal.SIGKILL)
            os.waitpid(pid, 0)
        except (ProcessLookupError, ChildProcessError):
            pass
        for _ in range(100):
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                return
            import time
            time.sleep(0.05)


class ForgedMetaTest(PhaseCase):
    """T037 (A2): after the wrapper's own generation every code is null, and only sources under `source_paths` are read."""

    FORGED = ("mutation: apps/service/src/pkg/a.py: mutmut's generation left an exit code on 1 mutant(s) before any "
              "test ran (a committed .meta file copied into mutants/?), so the verdict cannot be trusted")

    def test_a2_a_scoped_key_that_already_has_a_code_fails_the_run_naming_the_file(self) -> None:
        done = self.run_wrapper("apps/service", "--file", "src/pkg/a.py", meta={"src/pkg/a.py": {KEY: 1}},
                                results={"src/pkg/a.py": {KEY: 1}})
        self.assertEqual(done.returncode, 1)
        self.assertIn(self.FORGED, lines_of(done))
        self.assertEqual(self.started_mutmut(), [])

    def test_a2_a_sweep_of_a_forged_file_fails_the_same_way(self) -> None:
        done = self.run_wrapper("apps/service", meta={"src/pkg/a.py": {KEY: 1}}, results={"src/pkg/a.py": {KEY: 1}})
        self.assertEqual(done.returncode, 1)
        self.assertIn(self.FORGED, lines_of(done))

    def test_a2_a_meta_beside_a_test_or_outside_the_source_roots_is_never_a_verdict(self) -> None:
        meta = {"src/pkg/a.py": {KEY: None}, "tests/test_a.py": {"t.x_f__mutmut_1": 1},
                "scripts/b.py": {"b.x_f__mutmut_1": 0}, "src/pkg/readme.txt": {"r.x_f__mutmut_1": 0}}
        done = self.run_wrapper("apps/service", meta=meta, results={"src/pkg/a.py": {KEY: 1}})
        self.assertEqual(done.returncode, 0, lines_of(done))
        self.assertEqual(lines_of(done)[-1].split(" \u2014 ")[0], "mutation: 1 mutants: 1 killed, 0 no tests "
                                                                 "(reported, never failed); passed")

    def test_a2_a_ghost_meta_outside_the_roots_does_not_make_an_empty_sweep_pass(self) -> None:
        done = self.run_wrapper("apps/service", meta={"src/pkg/types.py": {}, "tests/ghost.py": {"g.x_f__mutmut_1": 1}})
        self.assertEqual(done.returncode, 1)
        self.assertEqual(lines_of(done)[-1], "mutation: mutmut found nothing to mutate in apps/service; a pass on "
                                             "nothing is not a pass")

    def test_a2_a_file_handed_over_that_the_table_does_not_take_is_not_run_on_a_copied_meta(self) -> None:
        done = self.run_wrapper("apps/service", "--file", "tests/test_a.py", meta={"tests/test_a.py": {KEY: None}},
                                results={"tests/test_a.py": {KEY: 0}})
        self.assertEqual(done.returncode, 0)
        self.assertEqual(self.started_mutmut(), [])


if __name__ == "__main__":
    unittest.main()
