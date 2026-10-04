"""R1 of S05-xdist: a project `generate` makes is marked `"parallelSafe": true`, whatever its backend.

The mark is the project's own word about whether its tests may share a machine's cores; the gate reads it
at run time (`test_xdist_gate.py`) and `migrate` carries it (`test_xdist_carry.py`).
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from support import FactoryTestCase

from slipwai.catalog import CATALOG


class NewProjectIsMarked(FactoryTestCase):
    def mark_of(self, parent: str, backend: str) -> object:
        repo = self.generate(parent, "shop", language=backend)
        document = json.loads((repo / "project.json").read_text(encoding="utf-8"))
        self.assertIn("parallelSafe", document, f"a {backend} project carries no mark")
        return document["parallelSafe"]

    def test_a_python_project_is_marked_true(self):
        with tempfile.TemporaryDirectory() as parent:
            self.assertIs(self.mark_of(parent, "python"), True)

    def test_a_typescript_project_is_marked_true_too(self):
        with tempfile.TemporaryDirectory() as parent:
            self.assertIs(self.mark_of(parent, "typescript"), True)

    def test_every_backend_the_catalog_offers_is_marked_true(self):
        for backend in CATALOG["backends"]:
            with self.subTest(backend=backend), tempfile.TemporaryDirectory() as parent:
                self.assertIs(self.mark_of(parent, backend), True)

    def test_the_mark_sits_at_the_top_level_beside_target_and_profile(self):
        with tempfile.TemporaryDirectory() as parent:
            repo: Path = self.generate(parent, "shop", language="python")
            keys = list(json.loads((repo / "project.json").read_text(encoding="utf-8")))
            self.assertIn("parallelSafe", keys)
            self.assertLess(abs(keys.index("parallelSafe") - keys.index("target")), 3)
