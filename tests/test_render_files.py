"""What reaches disk, and how (S11-render-once, R3: a file arrives finished or not at all; the PNG).

Counts come from the stand-in's log. Failures are made by the marker the fixture offers: a slice whose name
carries it makes every diagram whose source names that slice refuse to draw.
"""
from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from render_fixture import FAIL_MARKER, IS_WINDOWS, MODEL_DIR, RenderCase, write_model

NAMES = [f"Do thing {i}" for i in range(1, 17)]


@unittest.skipIf(IS_WINDOWS, "the stand-in's .bin/mmdc is a shebang script")
class FinishedFilesTest(RenderCase):
    def svgs(self, repo: Path) -> dict[str, bytes]:
        root = repo / MODEL_DIR
        return {str(path.relative_to(root)): path.read_bytes() for path in sorted(root.rglob("*.svg"))}

    def leftovers(self, repo: Path) -> list[str]:
        return [str(path) for path in (repo / MODEL_DIR).rglob(".tmp-*")]

    def test_e8_a_failed_draw_leaves_the_earlier_file_names_the_diagram_and_exits_non_zero(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, NAMES[:3])
            self.model_log(repo)
            before = self.svgs(repo)
            write_model(repo, [NAMES[0], f"Do {FAIL_MARKER}", NAMES[2]])
            done = self.run_model(repo)
            self.assertNotEqual(done.returncode, 0)
            self.assertIn("slices/S2.svg", done.stderr, "the diagram that failed is named")
            self.assertEqual(self.svgs(repo), before, "the earlier files' bytes stand")
            self.assertEqual(self.leftovers(repo), [])
            tracked = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=repo,
                                     text=True, capture_output=True).stdout
            self.assertNotIn(".tmp-", tracked)

    def test_e8_no_further_draw_starts_after_a_failure_and_the_session_is_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, [f"Do {FAIL_MARKER}", *NAMES[1:16]])
            done = self.run_model(repo, CI="true")  # a CI run draws all 25, in windows of four
            self.assertNotEqual(done.returncode, 0)
            log = self.model_log_of(repo)
            self.assertEqual(log.draws, 4, "the window that failed finished; no other was started")
            self.assertEqual((log.sessions, log.closes), (1, 1))
            self.assertEqual(self.leftovers(repo), [])
            drawn = self.svgs(repo)
            self.assertTrue(all(b"em-renderer-sha256" in drawn[f"segments/model-{n}.svg"] for n in (2, 3)),
                            "draws already in flight when one failed finish and are written as any other")
            self.assertNotIn("model.svg", drawn)
            self.assertNotIn("segments/model-1.svg", drawn)
            self.assertFalse(any(name.startswith("slices/") for name in drawn), "no later window was started")

    def test_e9_png_is_drawn_on_every_run_that_asks_in_the_session_the_svgs_use_and_never_left(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, 2)
            png = repo / MODEL_DIR / "model.png"
            first = self.model_log(repo, PNG="1")
            self.assertEqual((first.sessions, first.png_draws, first.draws), (1, 1, 5 + 0))
            self.assertTrue(png.read_bytes().startswith(b"\x89PNG"))
            png.write_bytes(b"stale")
            second = self.model_log(repo, PNG="1")
            self.assertEqual((second.sessions, second.png_draws, second.draws), (1, 1, 1), "only the PNG is drawn")
            self.assertTrue(png.read_bytes().startswith(b"\x89PNG"))

    def test_e9_without_the_request_an_existing_png_is_left_as_it_is(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, 2)
            self.model_log(repo)
            png = repo / MODEL_DIR / "model.png"
            self.assertFalse(png.exists())
            png.write_bytes(b"made by a person")
            log = self.model_log(repo)
            self.assertEqual((log.sessions, log.png_draws), (0, 0))
            self.assertEqual(png.read_bytes(), b"made by a person")


if __name__ == "__main__":
    unittest.main()
