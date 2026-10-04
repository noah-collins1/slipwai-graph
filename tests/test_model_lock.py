"""R7 (AC-S04-45, -46): the factory ships the model tooling's lock, and a project with the event profile tracks it.

No network and no `npm`: the lock is read as data. How it was made — by npm, against the registry, from the
manifest alone — is a fact of the commit that added it; what is held here is what a reader can check of it.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
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


class WhatTheTextsSayTest(unittest.TestCase):
    def test_e16_neither_the_readme_nor_the_manifest_says_the_gate_runs_npm_install_or_that_make_model_installs(
        self,
    ) -> None:
        """AC-S04-79 (D96, G13): both say the tooling installs from its committed lock."""
        repo = shape("db")
        readme = " ".join((repo / "docs/event-model/README.md").read_text(encoding="utf-8").split())
        description = read(repo / MANIFEST)["description"]
        for text in (readme, description):
            self.assertNotIn("Installed by `make model`", text)
            self.assertNotIn("on first run", text)
            self.assertNotIn("installs the renderer", text)
        self.assertIn("installs `scripts/event-model`'s three dependencies from its committed lock", readme)
        self.assertIn("only when a manifest is newer than what is installed", readme)
        self.assertIn("Installed from its committed lock", description)


class DescriptionLeavesTheLockTest(unittest.TestCase):
    def test_e17_npm_ci_accepts_the_shipped_lock_and_a_regenerated_lock_is_the_shipped_one(self) -> None:
        """AC-S04-79: the description is not in the lock, so changing it changes nothing npm checks (real npm)."""
        for tool in ("npm", "node"):
            if shutil.which(tool) is None:
                self.skipTest(f"{tool} is not installed here")
        repo = shape("db")
        with tempfile.TemporaryDirectory(prefix="model-lock-") as directory:
            work = Path(directory)
            for name in ("package.json", "package-lock.json"):
                shutil.copy(repo / "scripts/event-model" / name, work / name)
            ping = subprocess.run(["npm", "ping", "--registry", "https://registry.npmjs.org/"], capture_output=True,
                                  timeout=60)
            if ping.returncode != 0:
                self.skipTest("the npm registry cannot be reached from here")
            shipped = (work / "package-lock.json").read_bytes()
            quiet = ["--no-audit", "--no-fund", "--loglevel=error"]
            done = subprocess.run(["npm", "ci", *quiet], cwd=work, text=True, capture_output=True, timeout=180)
            self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
            self.assertEqual((work / "package-lock.json").read_bytes(), shipped)
            (work / "package-lock.json").unlink()
            shutil.rmtree(work / "node_modules")
            done = subprocess.run(["npm", "install", "--package-lock-only", *quiet], cwd=work, text=True,
                                  capture_output=True, timeout=180)
            self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
            self.assertEqual((work / "package-lock.json").read_bytes(), shipped)
            self.assertNotIn("description", read(work / "package-lock.json")["packages"][""])


if __name__ == "__main__":
    unittest.main()
