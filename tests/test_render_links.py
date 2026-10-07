"""A run never removes, reads or writes through a link (S11-render-once, T020/T021; AC-S11-21, -22).

Every victim a test plants lives inside that test's own temporary directory, beside the project and never in it,
except the one example whose point is a link to the project's own root: that project is the test's too. Each
example asserts the victim's bytes stand. What is removed is said, one `removed <path>` line each.
"""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from render_fixture import IS_WINDOWS, MODEL_DIR, WINDOWS_SKIP, RenderCase, make_model_within

# Generates nothing itself: the project comes from `RenderCase.project`, whose declaration the join carries.
TEST_SELECTION: dict[str, object] = {}

NAMES = [f"Do thing {i}" for i in range(1, 4)]


def removed(stdout: str) -> list[str]:
    """The paths of the `removed <path>` lines a run printed, in order."""
    return [line.strip().split("removed ", 1)[1] for line in stdout.splitlines() if line.strip().startswith("removed ")]


def plant_victim(parent: Path, name: str) -> dict[Path, bytes]:
    """A directory of files, a hidden one and a nested one, inside `parent`; their bytes by path."""
    root = parent / name
    (root / "sub").mkdir(parents=True)
    contents = {root / "notes.txt": b"notes", root / ".hidden": b"hidden", root / "sub" / "deep.txt": b"deep"}
    for path, data in contents.items():
        path.write_bytes(data)
    return contents


def stands(test: unittest.TestCase, victim: dict[Path, bytes]) -> None:
    for path, data in victim.items():
        test.assertEqual(path.read_bytes() if path.is_file() else None, data, f"{path} must stand")


@unittest.skipIf(IS_WINDOWS, WINDOWS_SKIP)
class LinksTest(RenderCase):
    def linked(self, repo: Path, name: str, target: str | Path) -> Path:
        link = repo / MODEL_DIR / name
        link.parent.mkdir(parents=True, exist_ok=True)
        try:
            link.symlink_to(target)
        except OSError as error:
            self.skipTest(f"this platform cannot make a symbolic link: {error}")
        return link

    def test_e21_a_link_at_slices_or_segments_is_removed_as_itself_and_what_it_names_stands(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, NAMES)
            self.model_log(repo)
            slices_victim = plant_victim(Path(directory), "victim-slices")
            segments_victim = plant_victim(Path(directory), "victim-segments")
            for name in ("slices", "segments"):
                for entry in (repo / MODEL_DIR / name).iterdir():
                    entry.unlink()
                (repo / MODEL_DIR / name).rmdir()
            self.linked(repo, "slices", Path(directory) / "victim-slices")
            self.linked(repo, "segments", Path(directory) / "victim-segments")
            done = self.run_model(repo)
            self.assertEqual(done.returncode, 0, done.stderr + done.stdout)
            stands(self, slices_victim)
            stands(self, segments_victim)
            for name in ("slices", "segments"):
                self.assertTrue((repo / MODEL_DIR / name).is_dir() and not (repo / MODEL_DIR / name).is_symlink())
            self.assertEqual(sorted(p.name for p in (repo / MODEL_DIR / "slices").iterdir()),
                             ["S1.mmd", "S1.svg", "S2.mmd", "S2.svg", "S3.mmd", "S3.svg"])
            self.assertEqual(sorted(removed(done.stdout)), ["docs/event-model/segments", "docs/event-model/slices"])
            self.assertEqual(removed(self.run_model(repo).stdout), [], "an unchanged tree removes and says nothing")

    def test_e21_a_link_at_slices_to_the_projects_own_root_removes_the_link_and_nothing_it_names(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, NAMES)
            self.model_log(repo)
            marks = {p: p.read_bytes() for p in (repo / "Makefile", repo / MODEL_DIR / "model.yaml")}
            slices = repo / MODEL_DIR / "slices"
            for entry in slices.iterdir():
                entry.unlink()
            slices.rmdir()
            self.linked(repo, "slices", "../..")
            done = self.run_model(repo)
            self.assertEqual(done.returncode, 0, done.stderr + done.stdout)
            self.assertTrue((repo / ".git").is_dir(), "the repository's own history stands")
            self.assertEqual({p: p.read_bytes() for p in marks}, marks)
            self.assertTrue((repo / "apps").exists() and not slices.is_symlink())

    def test_e21_a_dangling_link_or_a_file_at_slices_or_segments_is_removed_and_a_directory_made(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, NAMES)
            self.model_log(repo)
            root = repo / MODEL_DIR
            for name in ("slices", "segments"):
                for entry in (root / name).iterdir():
                    entry.unlink()
                (root / name).rmdir()
            self.linked(repo, "slices", Path(directory) / "nowhere")
            (root / "segments").write_text("a file where a directory goes")
            done = self.run_model(repo)
            self.assertEqual(done.returncode, 0, done.stderr + done.stdout)
            self.assertTrue((root / "slices" / "S1.svg").is_file() and (root / "segments" / "model-1.svg").is_file())
            self.assertEqual(sorted(removed(done.stdout)), ["docs/event-model/segments", "docs/event-model/slices"])

    def test_e21_an_entry_at_a_name_the_model_produces_that_is_not_a_file_is_removed_then_drawn_or_written(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, NAMES)
            self.model_log(repo)
            root = repo / MODEL_DIR
            victim = plant_victim(Path(directory), "victim-names")
            outside = Path(directory) / "victim-file"
            outside.write_bytes(b"not mermaid")
            (root / "slices/S1.svg").unlink()
            (root / "slices/S1.svg").mkdir()
            (root / "slices/S1.svg/inner").write_bytes(b"inner")
            (root / "slices/S1.mmd").unlink()
            self.linked(repo, "slices/S1.mmd", Path(directory) / "victim-names")
            (root / "slices/S2.mmd").unlink()
            self.linked(repo, "slices/S2.mmd", outside)
            (root / "slices/S2.svg").unlink()
            self.linked(repo, "slices/S2.svg", outside)
            (root / "model.html").unlink()
            self.linked(repo, "model.html", outside)
            (root / "model.svg").unlink()
            (root / "model.svg").mkdir()
            (root / "segments/model-1.svg").unlink()
            os.mkfifo(root / "segments/model-1.svg")
            done = self.run_model(repo, PNG="1")
            self.assertEqual(done.returncode, 0, done.stderr + done.stdout)
            stands(self, victim)
            self.assertEqual(outside.read_bytes(), b"not mermaid", "nothing was written through a link")
            for name in ("slices/S1.svg", "slices/S1.mmd", "slices/S2.mmd", "slices/S2.svg", "model.html",
                         "model.svg", "segments/model-1.svg"):
                self.assertTrue((root / name).is_file() and not (root / name).is_symlink(), name)
            self.assertTrue((root / "slices/S1.svg").read_text().rstrip().endswith("</svg>"))
            self.assertEqual(sorted(removed(done.stdout)), sorted(f"docs/event-model/{n}" for n in (
                "slices/S1.svg", "slices/S1.mmd", "slices/S2.mmd", "slices/S2.svg", "model.html", "model.svg",
                "segments/model-1.svg")))

    def test_e21_a_link_at_the_png_is_replaced_when_it_is_asked_for_and_what_it_names_stands(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, NAMES[:1])
            self.model_log(repo)
            outside = Path(directory) / "victim-png"
            outside.write_bytes(b"a person's")
            self.linked(repo, "model.png", outside)
            self.assertEqual(self.run_model(repo).returncode, 0)
            self.assertTrue((repo / MODEL_DIR / "model.png").is_symlink(), "not asked for: left as it is")
            done = self.run_model(repo, PNG="1")
            self.assertEqual(done.returncode, 0, done.stderr)
            self.assertEqual(outside.read_bytes(), b"a person's")
            self.assertTrue((repo / MODEL_DIR / "model.png").read_bytes().startswith(b"\x89PNG"))
            self.assertEqual(removed(done.stdout), ["docs/event-model/model.png"])

    def test_e21_a_link_where_the_empty_model_clears_is_removed_as_itself(self) -> None:
        from render_fixture import write_model

        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, NAMES[:1])
            self.model_log(repo)
            victim = plant_victim(Path(directory), "victim-empty")
            slices = repo / MODEL_DIR / "slices"
            for entry in slices.iterdir():
                entry.unlink()
            slices.rmdir()
            self.linked(repo, "slices", Path(directory) / "victim-empty")
            write_model(repo, [])
            done = self.run_model(repo)
            self.assertEqual(done.returncode, 0, done.stderr)
            stands(self, victim)
            self.assertFalse(slices.exists() or slices.is_symlink())

    def test_e21_a_real_directory_the_model_does_not_produce_is_removed_without_following_the_link_inside_it(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, NAMES[:1])
            self.model_log(repo)
            victim = plant_victim(Path(directory), "victim-inner")
            (repo / MODEL_DIR / "slices/stray").mkdir()
            self.linked(repo, "slices/stray/inner", Path(directory) / "victim-inner")
            done = self.run_model(repo)
            self.assertEqual(done.returncode, 0, done.stderr)
            stands(self, victim)
            self.assertEqual(removed(done.stdout), ["docs/event-model/slices/stray"])

    def test_e21_a_leftover_temporary_is_removed_and_said(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, NAMES[:1])
            self.model_log(repo)
            (repo / MODEL_DIR / "slices/.tmp-4242-0").write_text("<svg")
            done = self.run_model(repo)
            self.assertEqual(removed(done.stdout), ["docs/event-model/slices/.tmp-4242-0"])

    def test_e21_a_fifo_at_an_svg_name_does_not_hang_the_run(self) -> None:
        if not hasattr(os, "mkfifo"):
            self.skipTest("this platform has no FIFOs")
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, NAMES[:1])
            self.model_log(repo)
            fifo = repo / MODEL_DIR / "slices/S1.svg"
            fifo.unlink()
            os.mkfifo(fifo)
            done = make_model_within(repo, 90, repo.parent / "renderer.log")
            self.assertIsNotNone(done, "the run hung on a FIFO")
            assert done is not None
            self.assertEqual(done.returncode, 0, done.stderr + done.stdout)
            self.assertTrue(fifo.is_file())

    def test_e22_a_slice_id_as_long_as_a_file_name_allows_is_drawn(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, 1)
            model = repo / MODEL_DIR / "model.yaml"
            long_id = "S" + "a" * 245
            model.write_text(model.read_text().replace("id: S1\n", f"id: {long_id}\n"))
            done = self.run_model(repo)
            self.assertEqual(done.returncode, 0, done.stderr + done.stdout)
            self.assertTrue((repo / MODEL_DIR / "slices" / f"{long_id}.svg").is_file())
            self.assertEqual(list((repo / MODEL_DIR).rglob(".tmp-*")), [])


if __name__ == "__main__":
    unittest.main()
