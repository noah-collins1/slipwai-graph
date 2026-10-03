"""The page, the docs and the fragment say what `make model` does, and doing what they say holds (S11-render-once, R6).

A sentence is tested by following it, on the fixture, with the stand-in renderer: the counts come from its log.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from render_fixture import IS_WINDOWS, MODEL_DIR, WINDOWS_SKIP, RenderCase

from slipwai.assets import ROOT, VERSION

README = ROOT / "assets/toolkit/docs/event-model/README.md"
PAGE = ROOT / "docs/event-model.md"
FRAGMENT = ROOT / "changelog.d/render-once.md"


def flat(path: Path) -> str:
    """The file's prose with line breaks folded into spaces, so a sentence is found wherever it wraps."""
    return re.sub(r"\s+", " ", path.read_text())


class SaysItTest(unittest.TestCase):
    def test_e10_the_shipped_readme_says_how_to_force_a_redraw_and_that_there_is_no_setting_or_flag(self) -> None:
        text = flat(README)
        self.assertIn("there is no setting and no flag: delete a diagram, or `segments/` and `slices/`", text)
        self.assertIn("the installed mermaid-cli, Mermaid and Puppeteer versions", text)
        self.assertIn("a browser upgraded behind an `executablePath` that config names is not noticed, and deleting "
                      "`segments/` and `slices/` is the remedy", text)

    def test_e10_the_event_model_page_no_longer_says_a_browser_per_diagram(self) -> None:
        text = flat(PAGE)
        self.assertNotRegex(text, r"(?i)browser (per|for each|for every) diagram")
        self.assertIn("draws through one browser", text)
        self.assertIn("delete a diagram, or `segments/` and `slices/`", text)

    def test_e17_the_fragment_claims_patch_and_says_both_catch_up_things(self) -> None:
        text = FRAGMENT.read_text()
        self.assertEqual(text.splitlines()[0], "PATCH")
        prose = flat(FRAGMENT)
        self.assertIn("the installed mermaid-cli, Mermaid and Puppeteer versions", prose)
        self.assertIn("Nothing is asked of a repository already generated.", prose)
        self.assertIn("its first `make model` redraws every diagram once, and since the output is ignored nothing "
                      "committed changes", prose)
        self.assertIn("removed the ignore lines and commits its diagrams sees the second comment line in each SVG",
                      prose)

    def test_e17_the_version_stays_and_the_changelog_arithmetic_holds(self) -> None:
        # a hold: VERSION is `1.6.0.dev0` and the fragments' highest level is what it carries
        self.assertEqual(VERSION, "1.6.0.dev0")
        done = subprocess.run([sys.executable, "-m", "unittest", "test_changelog"], cwd=ROOT, text=True,
                              capture_output=True, env={**os.environ, "PYTHONPATH": f"{ROOT / 'src'}:{ROOT / 'tests'}",
                                                        "PYTHONDONTWRITEBYTECODE": "1"})
        self.assertEqual(done.returncode, 0, done.stderr)


@unittest.skipIf(IS_WINDOWS, WINDOWS_SKIP)
class FollowedTest(RenderCase):
    def test_e10_deleting_a_diagram_redraws_it_alone_and_deleting_the_two_directories_redraws_what_they_held(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, 3)
            root = repo / MODEL_DIR
            self.assertEqual(self.model_log(repo).draws, 6, "the timeline, two segments, three slices")
            self.assertEqual(self.model_log(repo).draws, 0)
            (root / "slices/S2.svg").unlink()
            log = self.model_log(repo)
            self.assertEqual((log.sessions, log.draws), (1, 1), "the deleted diagram, alone")
            self.assertTrue((root / "slices/S2.svg").exists())
            shutil.rmtree(root / "segments")
            shutil.rmtree(root / "slices")
            log = self.model_log(repo)
            self.assertEqual((log.sessions, log.draws), (1, 5), "two segments and three slices; the timeline stands")

    def test_e17_after_migrate_the_first_run_redraws_every_diagram_once_and_adds_the_second_comment_line(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, 3)
            self.model_log(repo)
            svgs = sorted((repo / MODEL_DIR).rglob("*.svg"))
            for svg in svgs:  # what an earlier factory drew: the source stamp, no renderer line
                svg.write_text(re.sub(r"<!-- em-renderer-sha256: [0-9a-f]{64} -->\n", "", svg.read_text(), count=1))
            self.assertEqual(self.model_log(repo).draws, len(svgs), "every diagram, once")
            self.assertEqual(self.model_log(repo).draws, 0, "and then left")
            for svg in svgs:
                lines = svg.read_text().splitlines()
                self.assertTrue(lines[0].startswith("<!-- em-source-sha256: "), svg.name)
                self.assertTrue(lines[1].startswith("<!-- em-renderer-sha256: "), svg.name)


if __name__ == "__main__":
    unittest.main()
