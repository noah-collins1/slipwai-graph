"""What reaches disk, and how (S11-render-once, R3: a file arrives finished or not at all; the PNG).

Counts come from the stand-in's log. Failures are made by the marker the fixture offers: a slice whose name
carries it makes every diagram whose source names that slice refuse to draw.
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from render_fixture import (
    EVENT_MODEL,
    FAIL_MARKER,
    IS_WINDOWS,
    MODEL_DIR,
    WINDOWS_SKIP,
    RenderCase,
    render_env,
    sha256_of,
    write_model,
    wrote,
)

NAMES = [f"Do thing {i}" for i in range(1, 17)]


PROBE_NAME = """import { temporaryPath } from './render-plan.ts';
console.log(JSON.stringify([temporaryPath('slice', 'docs/event-model/slices/S1.svg'), process.pid]));
"""


@unittest.skipIf(IS_WINDOWS, WINDOWS_SKIP)
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

    def test_e11_what_the_model_no_longer_produces_is_removed_by_name_and_nothing_it_still_does_is_touched(
        self,
    ) -> None:
        # Held on arrival: removal by name landed with T003, since a wholesale deletion cannot leave a current SVG.
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, NAMES[:3])
            self.model_log(repo)
            root = repo / MODEL_DIR
            names = ("slices/S1.svg", "slices/S2.svg")
            kept = {name: (root / name).read_bytes() for name in names}
            marks = {name: (root / name).stat().st_mtime_ns for name in names}
            (root / "slices/gone").mkdir()
            (root / "slices/gone/inner.svg").write_text("x")
            (root / "segments/stray-dir").mkdir()
            (root / "slices/.tmp-slice-S9.svg").write_text("<svg")
            (root / "segments/model-9.svg").write_text("old")
            (root / "slices/S9.mmd").write_text("old")
            write_model(repo, NAMES[:2])  # S3 is no longer produced: its SVG and source must go
            log = self.model_log(repo)
            self.assertEqual(sorted(p.name for p in (root / "slices").iterdir()),
                             ["S1.mmd", "S1.svg", "S2.mmd", "S2.svg"])
            self.assertEqual(sorted(p.name for p in (root / "segments").iterdir()), ["model-1.mmd", "model-1.svg"])
            self.assertEqual({n: (root / n).read_bytes() for n in names}, kept)
            self.assertEqual({n: (root / n).stat().st_mtime_ns for n in names}, marks)
            for name in ("slices/S1.mmd", "slices/S2.mmd"):
                self.assertNotIn(sha256_of(root / name), log.drawn_sources, "a current slice is not drawn again")

    def test_e18_a_temporary_is_named_for_the_process_that_writes_it_so_two_runs_never_share_one(self) -> None:
        # The name is read through a probe importing the naming `writeFinished` uses: a draw cannot be held mid-write.
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, 1)
            self.model_log(repo)  # the project's own run, which installs the TypeScript runner the probe needs
            script = repo / EVENT_MODEL / "probe-name.mts"
            script.write_text(PROBE_NAME)
            done = subprocess.run(
                ["node", str(repo / EVENT_MODEL / "node_modules/tsx/dist/cli.mjs"), str(script)],
                cwd=repo, text=True, capture_output=True, env=render_env())
            self.assertEqual(done.returncode, 0, done.stderr)
            path, pid = json.loads(done.stdout)
            self.assertEqual(Path(path).name, f".tmp-slice-{pid}-S1.svg")
            self.assertEqual(Path(path).parent.name, "slices")

    def test_e18_hold_a_leftover_temporary_of_any_process_is_removed_before_drawing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, 2)
            self.model_log(repo)
            root = repo / MODEL_DIR
            leftovers = [root / "slices/.tmp-slice-4242-S1.svg", root / "slices/.tmp-global-1-model.png",
                         root / "slices/.tmp-slice-S9.svg"]
            for leftover in leftovers:
                leftover.write_text("<svg")
            self.model_log(repo)
            self.assertEqual(self.leftovers(repo), [])

    def test_e11_an_empty_model_after_a_run_that_left_files_removes_every_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, 2)
            self.model_log(repo, PNG="1")
            (repo / MODEL_DIR / "slices/.tmp-slice-S9.svg").write_text("<svg")
            write_model(repo, [])
            log = self.model_log(repo)
            self.assertEqual(log.sessions, 0)
            root = repo / MODEL_DIR
            for name in ("model.mmd", "model.svg", "model.png", "model.html", "slices", "segments"):
                self.assertFalse((root / name).exists(), name)

    def test_e8_hold_a_redrawn_svg_and_png_arrive_as_new_files_never_written_in_place(self) -> None:
        # A hold on the rename: a write to the final name keeps the inode,
        # a rename of a finished file does not.
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, 1)
            self.model_log(repo, PNG="1")
            root = repo / MODEL_DIR
            names = ("slices/S1.svg", "model.png")
            before = {name: (root / name).stat().st_ino for name in names}
            svg = root / "slices/S1.svg"
            svg.write_text(svg.read_text().rstrip()[: -len("</svg>")])  # torn, so it is drawn again
            svg.chmod(0o444)
            self.model_log(repo, PNG="1")
            self.assertEqual(svg.read_text().rstrip()[-6:], "</svg>")
            for name in names:
                self.assertNotEqual((root / name).stat().st_ino, before[name], f"{name} was written in place")

    @unittest.skipIf(not hasattr(os, "getuid") or os.getuid() == 0, "a directory the process cannot write into is only "
                     "one for a user other than root")
    def test_e8_a_rename_that_cannot_happen_fails_the_run_keeps_the_earlier_file_and_closes_the_session(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, 1)
            self.model_log(repo)
            segments = repo / MODEL_DIR / "segments"
            torn = segments / "model-1.svg"
            torn.write_text(torn.read_text().rstrip()[: -len("</svg>")])  # to be drawn again, into a closed directory
            before = torn.read_bytes()
            segments.chmod(0o555)
            try:
                done = self.run_model(repo)
                log = self.model_log_of(repo)
                leftovers = self.leftovers(repo)
                kept = torn.read_bytes()
            finally:
                segments.chmod(0o755)
            self.assertNotEqual(done.returncode, 0)
            self.assertEqual(kept, before, "the earlier file's bytes stand")
            self.assertEqual(leftovers, [], "the temporary is removed")
            self.assertEqual((log.sessions, log.closes), (1, 1))

    def test_e12_every_text_output_is_written_only_where_it_differs(self) -> None:
        # The sweep of T009: each write the scripts make under docs/event-model/ is named by a line of the first run
        # and by none of the second, which is what makes write-if-different (the .mmd, the page, the README block).
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, 2)
            first = self.run_model(repo)
            self.assertEqual(first.returncode, 0, first.stderr)
            paths = wrote(first)
            for expected in ("docs/event-model/model.mmd", "docs/event-model/slices/S1.mmd",
                             "docs/event-model/segments/model-1.mmd", "docs/event-model/model.html",
                             "README.md (event-model block)"):
                self.assertIn(expected, paths)
            second = self.run_model(repo)
            self.assertEqual(wrote(second), [])


if __name__ == "__main__":
    unittest.main()
