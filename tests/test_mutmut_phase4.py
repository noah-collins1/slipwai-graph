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


if __name__ == "__main__":
    unittest.main()
