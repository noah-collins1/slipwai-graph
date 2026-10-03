"""What a run writes and says (S11-render-once, R5: text files only where they differ; the closing line).

Counts come from the stand-in's log; the closing line is the specification of the report and is asserted
verbatim. No test waits: a rewrite is seen by the file's own modification time, and where the platform's clock is
too coarse to show one the example skips, saying so.
"""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from render_fixture import IS_WINDOWS, MODEL_DIR, RenderCase, mtimes, rename_frame, write_model, wrote

OPEN = "Open docs/event-model/model.html to browse it."
FIRST = f"model: 16 slices, 25 of 25 diagrams drawn, 0 unchanged. {OPEN}"
EDIT = f"model: 16 slices, 3 of 25 diagrams drawn, 22 unchanged. {OPEN}"
NOTHING = f"model: 16 slices, 0 of 25 diagrams drawn, 25 unchanged; no browser started. {OPEN}"


def clock_is_fine(directory: Path) -> bool:
    """Whether two writes in a row show different modification times here."""
    probe = directory / "clock-probe"
    probe.write_text("a")
    first = probe.stat().st_mtime_ns
    probe.write_text("b")
    return probe.stat().st_mtime_ns != first


@unittest.skipIf(IS_WINDOWS, "the stand-in's .bin/mmdc is a shebang script")
class ReportTest(RenderCase):
    def closing(self, repo: Path, **env: str) -> str:
        done = self.run_model(repo, **env)
        self.assertEqual(done.returncode, 0, done.stderr + done.stdout)
        return next(line for line in done.stdout.splitlines() if line.startswith("model: "))

    def test_e13_the_closing_line_says_what_the_run_did_on_a_first_run_an_edit_and_nothing_changed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, 16)
            self.assertEqual(self.closing(repo), FIRST)
            self.assertEqual((self.model_log_of(repo).sessions, self.model_log_of(repo).draws), (1, 25))
            rename_frame(repo, "Do7", "Do7b")
            self.assertEqual(self.closing(repo), EDIT)
            self.assertEqual((self.model_log_of(repo).sessions, self.model_log_of(repo).draws), (1, 3))
            self.assertEqual(self.closing(repo), NOTHING)
            self.assertEqual((self.model_log_of(repo).sessions, self.model_log_of(repo).draws), (0, 0))

    def test_e13_a_run_that_drew_only_the_png_opened_a_browser(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, 16)
            self.closing(repo)
            png = f"model: 16 slices, 0 of 25 diagrams drawn, 25 unchanged. {OPEN}"
            self.assertEqual(self.closing(repo, PNG="1"), png)

    def test_e13_the_empty_model_message_is_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, 2)
            self.model_log(repo)
            write_model(repo, [])
            done = self.run_model(repo)
            self.assertEqual(done.returncode, 0, done.stderr)
            self.assertIn("docs/event-model/model.yaml has no slices yet — nothing to render.", done.stdout)
            self.assertIn("Model your first workflow with the `event-modeling` skill, then run this again.",
                          done.stdout)

    def test_e12_a_second_run_on_an_unchanged_tree_writes_nothing_and_says_nothing_was_written(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, 16)
            if not clock_is_fine(Path(directory)):
                self.skipTest("the platform's file time is too coarse to show a rewrite")
            first = self.run_model(repo)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertGreaterEqual(len(wrote(first)), 25 * 2 + 1, "every diagram's two files and the page")
            before = mtimes(repo)
            second = self.run_model(repo)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(wrote(second), [])
            self.assertEqual(mtimes(repo), before, "no file moved")

    def test_e12_an_edit_writes_exactly_the_files_whose_bytes_differ(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, 16)
            self.model_log(repo)
            rename_frame(repo, "Do7", "Do7b")
            done = self.run_model(repo)
            names = sorted(path.rsplit("event-model/", 1)[-1] for path in wrote(done))
            segments = [name for name in names if name.startswith("segments/")]
            self.assertEqual(len(segments), 2, names)
            self.assertEqual([name for name in names if name not in segments],
                             ["model.html", "model.mmd", "model.svg", "slices/S7.mmd", "slices/S7.svg"])
            self.assertEqual(len(wrote(done)), 7, "one line per file written, none for a file left")

    def test_e12_the_page_is_rebuilt_from_the_svgs_on_disk(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, 2)
            self.model_log(repo)
            page = repo / MODEL_DIR / "model.html"
            svg = repo / MODEL_DIR / "slices/S1.svg"
            svg.write_text(svg.read_text().replace("<desc>", "<desc>EDITED-ON-DISK-"))
            os.utime(svg)  # still a current SVG, so it is left and the page carries what is on disk
            self.model_log(repo)
            self.assertIn("EDITED-ON-DISK-", page.read_text())


if __name__ == "__main__":
    unittest.main()
