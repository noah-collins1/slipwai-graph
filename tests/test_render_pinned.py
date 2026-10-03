"""What `make model` leaves on disk, pinned before the renderer is changed (S11-render-once, T001).

Every test here is a HOLD: green against today's `render.ts` and still green after the slice, unedited. The
renderer is the stand-in of `render_fixture`, so no browser starts. Not pinned, because the slice changes it on
purpose: how many renderer processes or sessions a run opens, that every diagram is redrawn on every run, the
closing line's words, and the wholesale deletion of `slices/` and `segments/`.
"""
from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

from render_fixture import (
    IS_WINDOWS,
    MODEL_DIR,
    install_stand_in,
    make_model,
    read_log,
    write_model,
)
from support import FactoryTestCase

HASH = re.compile(r"em-source-sha256: ([0-9a-f]{64})")


@unittest.skipIf(IS_WINDOWS, "the stand-in's .bin/mmdc is a shebang script")
class RenderPinnedTest(FactoryTestCase):
    def project(self, directory: str, slices: int | list[str]) -> Path:
        repo = self.generate(directory, "render-pin")
        install_stand_in(repo)
        write_model(repo, slices)
        return repo

    def run_model(self, repo: Path) -> None:
        done = make_model(repo, Path(repo.parent) / "renderer.log")
        self.assertEqual(done.returncode, 0, done.stderr + done.stdout)

    def artifacts(self, repo: Path) -> set[str]:
        root = repo / MODEL_DIR
        return {str(path.relative_to(root)) for path in root.rglob("*") if path.is_file()}

    def assert_every_svg_stamped_from_its_mmd(self, repo: Path) -> int:
        root = repo / MODEL_DIR
        svgs = sorted(root.rglob("*.svg"))
        for svg in svgs:
            mmd = svg.with_suffix(".mmd")
            self.assertTrue(mmd.exists(), f"{svg.name} has no .mmd beside it")
            expected = HASH.search(mmd.read_text())
            assert expected is not None, f"{mmd.name} carries no stamp"
            first = svg.read_text().split("\n", 1)[0]
            self.assertEqual(first, f"<!-- em-source-sha256: {expected.group(1)} -->", svg.name)
            self.assertTrue(svg.read_text().rstrip().endswith("</svg>"), svg.name)
        return len(svgs)

    def test_hold_a_mmd_sits_beside_every_svg_stamped_with_its_hash_and_the_page_exists(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, 16)
            self.run_model(repo)
            root = repo / MODEL_DIR
            self.assertEqual(self.assert_every_svg_stamped_from_its_mmd(repo), 1 + 8 + 16)
            self.assertEqual(len(list((root / "slices").glob("*.svg"))), 16)
            self.assertEqual(len(list((root / "segments").glob("*.svg"))), 8)
            self.assertTrue((root / "model.svg").exists())
            page = root / "model.html"
            self.assertTrue(page.exists())
            self.assertIn("</svg>", page.read_text())
            # The stand-in did draw: the log is how this suite knows, and what it says is not pinned.
            self.assertGreater(read_log(Path(directory) / "renderer.log").draws, 0)

    def test_hold_a_slice_the_model_no_longer_has_leaves_nothing_behind(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, 16)
            self.run_model(repo)
            root = repo / MODEL_DIR
            self.assertTrue((root / "slices/S16.svg").exists())

            write_model(repo, 15)
            self.run_model(repo)
            self.assertFalse((root / "slices/S16.svg").exists())
            self.assertFalse((root / "slices/S16.mmd").exists())
            self.assertEqual(self.assert_every_svg_stamped_from_its_mmd(repo), 1 + 8 + 15)

            # A model that shrank to three slices leaves exactly what a clean run on three slices leaves:
            # no slice file and no segment file the model no longer produces.
            write_model(repo, 3)
            self.run_model(repo)
            shrunk = self.artifacts(repo)
            self.assertEqual({n for n in shrunk if n.startswith("slices/")},
                             {f"slices/S{i}.{ext}" for i in (1, 2, 3) for ext in ("mmd", "svg")})
            for stale in ("slices", "segments"):
                for path in (root / stale).iterdir():
                    path.unlink()
            self.run_model(repo)
            self.assertEqual(self.artifacts(repo), shrunk)
            self.assertEqual(self.assert_every_svg_stamped_from_its_mmd(repo), len(
                [n for n in shrunk if n.endswith(".svg")]))

    def test_hold_an_empty_model_removes_every_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, 4)
            self.run_model(repo)
            root = repo / MODEL_DIR
            for kept in ("model.mmd", "model.svg", "model.html", "slices/S1.svg"):
                self.assertTrue((root / kept).exists(), kept)

            write_model(repo, 0)
            self.run_model(repo)
            for gone in ("model.mmd", "model.svg", "model.png", "model.html"):
                self.assertFalse((root / gone).exists(), gone)
            self.assertFalse((root / "slices").exists())
            self.assertFalse((root / "segments").exists())
            self.assertEqual(self.artifacts(repo) & {"model.yaml"}, {"model.yaml"})


if __name__ == "__main__":
    unittest.main()
