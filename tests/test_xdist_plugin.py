"""R3 of S05-xdist: the plugin is pinned in every Python service, locked, and only the gate turns it on.

Generation alone for the shape, `uv lock --check` for whether the committed lock agrees with the manifest
(skipped, with its reason, where `uv` is not on the PATH).
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
import tomllib
import unittest

from support import FactoryTestCase

from slipwai.assets import ROOT

LOCKS = ROOT / "assets/languages/python/locks"
TEMPLATE = ROOT / "assets/languages/python/app/pyproject.toml"
PLUGIN = "pytest-xdist==3.8.0"
# The four selections the locks are built for: (name, event store, http, lock file).
SELECTIONS = (
    ("plain", "memory", "none", "uv.lock"),
    ("fastapi", "memory", "fastapi", "uv-fastapi.lock"),
    ("postgres", "postgres", "none", "uv-postgres.lock"),
    ("fastapi-postgres", "postgres", "fastapi", "uv-fastapi-postgres.lock"),
)


def locked_versions(text: str) -> dict[str, str]:
    return {package["name"]: package["version"] for package in tomllib.loads(text)["package"]}


class PluginIsPinned(FactoryTestCase):
    def test_every_selections_dev_list_carries_the_plugin(self) -> None:
        for name, store, http, _ in SELECTIONS:
            with self.subTest(selection=name), tempfile.TemporaryDirectory() as parent:
                repo = self.generate(
                    parent, "shop", "event-modelling", "python", "none", event_store=store, http=http, auth="none"
                )
                document = tomllib.loads((repo / "apps/service/pyproject.toml").read_text(encoding="utf-8"))
                self.assertIn(PLUGIN, document["dependency-groups"]["dev"])
                self.assertNotIn(PLUGIN, document["project"]["dependencies"])

    def test_every_committed_lock_names_the_plugin_and_execnet(self) -> None:
        for name, _, _, lock in SELECTIONS:
            with self.subTest(lock=lock):
                versions = locked_versions((LOCKS / lock).read_text(encoding="utf-8"))
                self.assertEqual(versions.get("pytest-xdist"), "3.8.0", name)
                self.assertIn("execnet", versions, name)

    @unittest.skipUnless(shutil.which("uv"), "uv is not on the PATH, so a lock cannot be checked against its manifest")
    def test_uv_accepts_every_committed_lock_for_its_manifest(self) -> None:
        for name, store, http, _ in SELECTIONS:
            with self.subTest(selection=name), tempfile.TemporaryDirectory() as parent:
                repo = self.generate(
                    parent, "shop", "event-modelling", "python", "none", event_store=store, http=http, auth="none"
                )
                result = subprocess.run(
                    ["uv", "lock", "--check", "--project", str(repo / "apps/service")],
                    capture_output=True, text=True, timeout=300,
                )
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_hold_the_template_addopts_has_no_parallel_flag_and_is_what_it_was(self) -> None:
        """A hold: a person's own `pytest` stays serial, so the template's `addopts` never names `-n`."""
        for source in (TEMPLATE,):
            options = tomllib.loads(source.read_text(encoding="utf-8"))["tool"]["pytest"]["ini_options"]
            self.assertEqual(options["addopts"], "--strict-config --strict-markers")
        with tempfile.TemporaryDirectory() as parent:
            repo = self.generate(parent, "shop", "standard", "python", "none")
            generated = tomllib.loads((repo / "apps/service/pyproject.toml").read_text(encoding="utf-8"))
            self.assertEqual(generated["tool"]["pytest"]["ini_options"]["addopts"], "--strict-config --strict-markers")
