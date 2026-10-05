"""The probe file the root gate keys is written or the run stops (S33, D122: A1 and A5)."""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from test_factory_gate_stamp import GateCase

sys.dont_write_bytecode = True

PROBES = ".factory-work/verify-probes"
CACHE = "assets/toolkit/scripts/__pycache__/x.pyc"


class TestTheProbeFileIsWrittenOrTheRunStops(GateCase):
    def test_a_probe_file_that_cannot_be_written_never_lets_a_stale_key_reuse(self) -> None:  # A1 a
        self.passes()
        probes = self.repo / PROBES
        probes.chmod(0o444)
        self.addCleanup(probes.chmod, 0o644)
        if os.access(probes, os.W_OK):
            self.skipTest("running as a user for whom chmod does not stop a write")
        (self.repo / CACHE).parent.mkdir(parents=True, exist_ok=True)
        (self.repo / CACHE).write_bytes(b"")
        done = self.gate()
        self.assertNotEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertNotIn("already passed it at", done.stdout)
        self.assertEqual(self.ran(), [])
        self.assertIn("verify-probes", done.stderr)

    def test_a_symlinked_work_directory_is_refused_and_no_stamp_is_written(self) -> None:  # A1 b
        self.passes()
        before = self.stamps()
        elsewhere = Path(tempfile.mkdtemp(prefix="factory-gate-elsewhere-"))
        self.addCleanup(shutil.rmtree, elsewhere, ignore_errors=True)
        shutil.rmtree(self.repo / ".factory-work")
        (self.repo / ".factory-work").symlink_to(elsewhere)
        done = self.gate()
        self.assertNotEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertIn(".factory-work is a symbolic link", done.stderr)
        self.assertEqual((self.ran(), self.stamps()), ([], before))
        self.assertEqual(list(elsewhere.iterdir()), [])

    def test_a_work_path_that_is_a_file_is_refused(self) -> None:  # A1 b, the other half
        (self.repo / ".factory-work").write_text("x", encoding="utf-8")
        done = self.gate()
        self.assertNotEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertIn(".factory-work is a symbolic link or not a directory", done.stderr)
        self.assertEqual(self.ran(), [])


class TestAFailedCacheListingIsUniqueToTheRun(GateCase):
    def test_a_directory_find_cannot_read_leaves_the_run_unique_line(self) -> None:  # A5
        hidden = self.repo / "assets/hidden"
        hidden.mkdir(parents=True)
        hidden.chmod(0o000)
        self.addCleanup(hidden.chmod, 0o755)
        if os.access(hidden, os.R_OK):
            self.skipTest("running as a user for whom chmod 000 does not hide a directory")
        self.gate()
        self.assertIn("caches: not listed, run ", (self.repo / PROBES).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
