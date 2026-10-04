"""R7 (AC-S04-45, -46): the factory ships the model tooling's lock, and a project with the event profile tracks it.

No network and no `npm`: the lock is read as data. How it was made — by npm, against the registry, from the
manifest alone — is a fact of the commit that added it; what is held here is what a reader can check of it.
"""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from parallel_gate import shape

sys.dont_write_bytecode = True

LOCK = "scripts/event-model/package-lock.json"
MANIFEST = "scripts/event-model/package.json"


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class ModelLockTest(unittest.TestCase):
    def test_e1_an_event_profile_project_tracks_a_lock_that_names_the_manifests_pins(self) -> None:
        """AC-S04-45: the lock is a tracked file, and its root entry is exactly the manifest's two groups."""
        repo = shape("db")
        tracked = subprocess.run(["git", "ls-files", LOCK], cwd=repo, text=True, capture_output=True, check=True)
        self.assertEqual(tracked.stdout.strip(), LOCK)
        manifest, lock = read(repo / MANIFEST), read(repo / LOCK)
        root = lock["packages"][""]
        self.assertEqual(root["dependencies"], manifest["dependencies"])
        self.assertEqual(root["devDependencies"], manifest["devDependencies"])
        self.assertEqual(set(root) - {"name", "dependencies", "devDependencies"}, set())

    def test_e1_a_standard_profile_project_has_no_lock(self) -> None:
        """AC-S04-45: the `scripts/event-model/` rule excludes the standard profile, so its lock goes too."""
        self.assertFalse((shape("plain") / LOCK).exists())

    def test_e2_the_shipped_lock_is_version_3_from_the_public_registry_for_every_esbuild_platform(self) -> None:
        """AC-S04-46: lockfileVersion 3; every `resolved` from registry.npmjs.org; esbuild's own platforms all in."""
        lock = read(shape("db") / LOCK)
        self.assertEqual(lock["lockfileVersion"], 3)
        packages = lock["packages"]
        for name, entry in packages.items():
            if name:
                self.assertTrue(entry["resolved"].startswith("https://registry.npmjs.org/"), name)
        platforms = packages["node_modules/esbuild"]["optionalDependencies"]
        self.assertGreaterEqual(len(platforms), 20)
        for platform in platforms:
            self.assertIn(f"node_modules/{platform}", packages, platform)


if __name__ == "__main__":
    unittest.main()
