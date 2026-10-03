"""One browser per run, opened on the first diagram to draw (S11-render-once, R1 and R2's session half).

Every count is read from the stand-in's log (`render_fixture`), never from what the run printed.
"""
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from render_fixture import (
    IS_WINDOWS,
    MODEL_DIR,
    RenderCase,
    install_stand_in,
    mmd_hashes,
    write_model,
)


@unittest.skipIf(IS_WINDOWS, "the stand-in's .bin/mmdc is a shebang script")
class OneSessionTest(RenderCase):
    def test_e1_a_first_run_opens_one_session_and_draws_every_diagram_through_it(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, 16)
            log = self.model_log(repo)
            self.assertEqual(log.sessions, 1)
            self.assertEqual(log.draws, 1 + 8 + 16)
            self.assertEqual(log.closes, 1, "the session is closed")
            self.assertEqual(sorted(log.drawn_sources), sorted(mmd_hashes(repo).values()))

    def test_e4_a_fresh_checkout_and_a_ci_run_each_open_one_session(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, 16)
            self.model_log(repo)
            shutil.rmtree(repo / MODEL_DIR / "slices")
            shutil.rmtree(repo / MODEL_DIR / "segments")
            for name in ("model.svg", "model.mmd", "model.html"):
                (repo / MODEL_DIR / name).unlink()
            fresh = self.model_log(repo)
            self.assertEqual((fresh.sessions, fresh.draws), (1, 25))
            ci = self.model_log(repo, CI="true")
            self.assertEqual((ci.sessions, ci.draws, ci.closes), (1, 25, 1))

    def test_e4_a_one_slice_model_draws_its_three_diagrams_in_one_session(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, 1)
            log = self.model_log(repo)
            self.assertEqual((log.sessions, log.draws, log.closes), (1, 3, 1))

    def test_e16_the_session_is_launched_with_the_config_files_contents_at_the_width_of_today(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, 2)
            config = Path(directory) / "puppeteer.json"
            config.write_text(json.dumps({"args": ["--no-sandbox", "--stand-in-marker"]}))
            log = self.model_log(repo, MERMAID_PUPPETEER_CONFIG=str(config))
            self.assertEqual(log.launch_options, [{"headless": "shell", "args": ["--no-sandbox", "--stand-in-marker"]}])
            draws = [e for e in log.entries if e["event"] == "draw"]
            self.assertEqual({e["width"] for e in draws}, {2400})
            self.assertEqual({e["background"] for e in draws}, {"white"})

    def test_e16_hold_the_swimlane_patch_has_run_before_the_browser_is_launched(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "patch-order")
            install_stand_in(repo, unpatched=True)
            write_model(repo, 2)
            log = self.model_log(repo)
            self.assertGreaterEqual(log.sessions, 1)
            self.assertEqual([e["chunk_fixed"] for e in log.entries if e["event"] == "session"],
                             [True] * log.sessions)


if __name__ == "__main__":
    unittest.main()
