"""The `--scope` verb's edges: which feature it reads, and that it only reads (D60, AC-S02-55 and -56)."""
from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from test_decisions_scope import SLICE, entry, printed, run, scratch

TEST_SELECTION: dict[str, object] = {
    "reads": ["assets/toolkit/scripts/check-decisions.py", "assets/toolkit/scripts/check-styles.py"],
}


def tree_digest(root: Path) -> str:
    """Every path, byte and modification time under `root`: a created, changed or touched file changes it."""
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        digest.update(path.relative_to(root).as_posix().encode())
        if path.is_file():
            digest.update(path.read_bytes())
            digest.update(str(path.stat().st_mtime_ns).encode())
    return digest.hexdigest()


class DecisionsScopeEdgesTest(unittest.TestCase):
    def test_e55_two_features_need_feature_named_and_one_feature_does_not(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = scratch(directory, entry(1, SLICE), entry(1, "global"), names=("alpha", "beta"))
            refused = run(repo, "--scope", SLICE)
            self.assertNotEqual(0, refused.returncode)
            self.assertEqual("", refused.stdout)
            lines = refused.stderr.strip().splitlines()
            self.assertEqual(1, len(lines), refused.stderr)
            self.assertIn("alpha", lines[0])
            self.assertIn("beta", lines[0])
            self.assertIn("--feature", lines[0])
            chosen = run(repo, "--scope", SLICE, "--feature", "beta")
            self.assertEqual(0, chosen.returncode, chosen.stderr)
            self.assertEqual(["D1"], printed(chosen))
        with tempfile.TemporaryDirectory() as directory:
            only = run(scratch(directory, entry(1, SLICE)), "--scope", SLICE)
            self.assertEqual(0, only.returncode, only.stderr)
            self.assertEqual(["D1"], printed(only))

    def test_e56_no_run_creates_or_changes_a_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = scratch(directory, entry(1, SLICE) + "\n" + entry(2, status="overridden by D3"),
                           entry(1, "global"), names=("alpha", "beta"))
            before = tree_digest(repo)
            for args in (["--scope", SLICE], ["--scope", SLICE, "--feature", "alpha"], ["--scope"], ["--feature", "x"]):
                run(repo, *args)
                self.assertEqual(before, tree_digest(repo), args)


if __name__ == "__main__":
    unittest.main()
