"""R7 (AC-S04-77, -78; D96, G9): the install's marker is a file only the recipe writes, with real `npm`.

A lock regenerated from an edited manifest makes npm rewrite its own hidden lockfile without installing, so a rule
keyed on that file would skip over a stale tree; the recipe's own marker is written only after `npm ci` succeeds and
npm's `ci` removes it with the tree. The tests need npm, node and the registry and skip, with the reason, without them.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile

from test_model_install import MARKER, PREFIX, SKIP, ModelCase

sys.dont_write_bytecode = True

MANIFEST = f"{PREFIX}/package.json"


class RegenerateCase(ModelCase):
    def setUp(self) -> None:
        super().setUp()
        for tool in ("npm", "node"):
            if shutil.which(tool) is None:
                self.skipTest(f"{tool} is not installed here")
        for tool in ("npm", "node"):
            (self.bin / tool).unlink()
        ping = subprocess.run(["npm", "ping", "--registry", "https://registry.npmjs.org/"], capture_output=True,
                              timeout=60)
        if ping.returncode != 0:
            self.skipTest("the npm registry cannot be reached from here")

    def installed_version(self, package: str) -> str:
        path = self.repo / PREFIX / "node_modules" / package / "package.json"
        return str(json.loads(path.read_text(encoding="utf-8"))["version"])

    def installs(self, done: subprocess.CompletedProcess[str]) -> list[str]:
        return [line for line in done.stdout.splitlines() if line.startswith(f"npm --prefix {PREFIX} ci")]


class RegenerateTest(RegenerateCase):
    def test_e14_a_lock_regenerated_on_an_installed_tree_is_installed_from_and_then_matches(self) -> None:
        """AC-S04-77: `npm install --package-lock-only` installs nothing, so the next gate must, once."""
        self.assert_passed(self.make("check-drawio"))
        manifest = self.repo / MANIFEST
        manifest.write_text(manifest.read_text(encoding="utf-8").replace('"yaml": "2.9.0"', '"yaml": "2.8.0"'),
                            encoding="utf-8")
        self.assertEqual(self.installed_version("yaml"), "2.9.0")
        self.assert_passed(self.run_in("npm", "--prefix", PREFIX, "install", "--package-lock-only", "--no-audit",
                                       "--no-fund", "--loglevel=error"))
        self.assertEqual(self.installed_version("yaml"), "2.9.0")
        first = self.make("check-drawio")
        self.assert_passed(first)
        self.assertEqual(len(self.installs(first)), 1, first.stdout)
        self.assertEqual(self.installed_version("yaml"), "2.8.0")
        self.assertNotIn(SKIP, first.stdout.splitlines())
        second = self.make("check-drawio")
        self.assert_passed(second)
        self.assertEqual(self.installs(second), [], second.stdout)
        self.assertEqual(second.stdout.splitlines().count(SKIP), 1, second.stdout)


class InterruptedTest(RegenerateCase):
    def test_e15_an_install_that_does_not_complete_leaves_no_marker_and_the_next_gate_installs(self) -> None:
        """AC-S04-78: `npm ci` empties the tree first; with no cache and no network it fails, and nothing vouches."""
        self.assert_passed(self.make("check-drawio"))
        marker = self.repo / MARKER
        self.assertTrue(marker.exists())
        lock = self.repo / PREFIX / "package-lock.json"
        later = marker.stat().st_mtime + 10
        os.utime(lock, (later, later))
        with tempfile.TemporaryDirectory(prefix="npm-empty-cache-") as cache:
            failed = self.make("check-drawio", env={"npm_config_offline": "true", "npm_config_cache": cache})
        self.assertNotEqual(failed.returncode, 0, failed.stdout + failed.stderr)
        self.assertEqual(len(self.installs(failed)), 1, failed.stdout)
        self.assertFalse(marker.exists())
        again = self.make("check-drawio")
        self.assert_passed(again)
        self.assertEqual(len(self.installs(again)), 1, again.stdout)
        self.assertNotIn(SKIP, again.stdout.splitlines())
