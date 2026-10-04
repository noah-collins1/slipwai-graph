"""What a run writes and says (S11-render-once, R5: text files only where they differ; the closing line).

Counts come from the stand-in's log; the closing line is the specification of the report and is asserted
verbatim. No test waits: a rewrite is seen in the run's own `wrote` lines and in the file's modification time, and
no example skips for a clock (the two runs it compares are whole `make model` runs apart).
"""
from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from render_fixture import (
    EVENT_MODEL,
    IS_WINDOWS,
    LOG_VARIABLE,
    MODEL_DIR,
    WINDOWS_SKIP,
    RenderCase,
    mtimes,
    read_log,
    rename_frame,
    render_env,
    write_model,
    wrote,
)

OPEN = "Open docs/event-model/model.html to browse it."
FIRST = f"model: 16 slices, 25 of 25 diagrams drawn, 0 unchanged. {OPEN}"
EDIT = f"model: 16 slices, 3 of 25 diagrams drawn, 22 unchanged. {OPEN}"
NOTHING = f"model: 16 slices, 0 of 25 diagrams drawn, 25 unchanged; no browser started. {OPEN}"


@unittest.skipIf(IS_WINDOWS, WINDOWS_SKIP)
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

    def test_e13_a_run_that_drew_only_the_png_says_the_png_was_drawn(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, 16)
            self.closing(repo)
            self.assertEqual(self.closing(repo, PNG="1"),
                             f"model: 16 slices, 0 of 25 diagrams drawn, 25 unchanged; the PNG was drawn. {OPEN}")
            self.assertEqual(self.model_log_of(repo).png_draws, 1)

    def test_e25_the_closing_line_in_each_case_of_drawn_none_ci_and_png_alone_and_together(self) -> None:
        ci = "; everything was drawn because a CI marker is set"
        png = "; the PNG was drawn"
        cases = [
            ("edit", {}, f"3 of 25 diagrams drawn, 22 unchanged. {OPEN}"),
            ("edit and png", {"PNG": "1"}, f"3 of 25 diagrams drawn, 22 unchanged{png}. {OPEN}"),
            ("nothing", {}, f"0 of 25 diagrams drawn, 25 unchanged; no browser started. {OPEN}"),
            ("png", {"PNG": "1"}, f"0 of 25 diagrams drawn, 25 unchanged{png}. {OPEN}"),
            ("ci", {"CI": "true"}, f"25 of 25 diagrams drawn, 0 unchanged{ci}. {OPEN}"),
            ("ci and png", {"CI": "true", "PNG": "1"}, f"25 of 25 diagrams drawn, 0 unchanged{ci}{png}. {OPEN}"),
            ("png set to something else", {"PNG": "0"}, f"0 of 25 diagrams drawn, 25 unchanged; no browser started. "
                                                        f"{OPEN}"),
        ]
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, 16)
            self.closing(repo)
            for name, env, tail in cases:
                with self.subTest(case=name):
                    if name.startswith("edit"):
                        rename_frame(repo, "Do7" if name == "edit" else "Do7b", "Do7b" if name == "edit" else "Do7c")
                    elif name == "nothing":
                        self.closing(repo)
                    self.assertEqual(self.closing(repo, **env), f"model: 16 slices, {tail}")

    def test_e19_under_a_ci_marker_the_closing_line_says_one_clause_why_everything_was_drawn(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, 1)
            self.closing(repo)
            for marker in ("CI", "GITHUB_ACTIONS", "GITLAB_CI"):
                with self.subTest(marker=marker):
                    self.assertEqual(
                        self.closing(repo, **{marker: "true"}),
                        f"model: 1 slice, 3 of 3 diagrams drawn, 0 unchanged; everything was drawn because a CI "
                        f"marker is set. {OPEN}")
            self.assertEqual(self.closing(repo, CI=""),
                             f"model: 1 slice, 0 of 3 diagrams drawn, 3 unchanged; no browser started. {OPEN}",
                             "a marker that is empty is none")

    def test_e13_a_one_slice_model_agrees_its_nouns_with_their_counts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, 1)
            self.assertEqual(self.closing(repo), f"model: 1 slice, 3 of 3 diagrams drawn, 0 unchanged. {OPEN}")
            self.assertEqual(self.closing(repo),
                             f"model: 1 slice, 0 of 3 diagrams drawn, 3 unchanged; no browser started. {OPEN}")

    def test_e9_the_png_flag_asks_for_the_raster_copy_as_the_variable_does(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, 1)
            log = self.model_log(repo)  # the project's own run, which installs the TypeScript runner
            self.assertEqual(log.png_draws, 0)
            png = repo / MODEL_DIR / "model.png"
            self.assertFalse(png.exists())
            done = subprocess.run(
                ["node", str(repo / EVENT_MODEL / "node_modules/tsx/dist/cli.mjs"),
                 str(repo / EVENT_MODEL / "render.ts"), "--png"],
                cwd=repo, text=True, capture_output=True,
                env=render_env(**{LOG_VARIABLE: str(repo.parent / "flag.log")}),
            )
            self.assertEqual(done.returncode, 0, done.stderr)
            self.assertTrue(png.read_bytes().startswith(b"\x89PNG"))
            self.assertEqual(self.read_flag_log(repo).png_draws, 1)

    def read_flag_log(self, repo: Path):
        return read_log(repo.parent / "flag.log")

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
            first = self.run_model(repo)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertGreaterEqual(len(wrote(first)), 25 * 2 + 1, "every diagram's two files and the page")
            before = mtimes(repo)
            second = self.run_model(repo)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(wrote(second), [])
            # The two runs are whole `make model` runs apart, far longer than any file clock's tick: a rewrite would
            # show here, and `wrote(second) == []` above needs no clock at all.
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
