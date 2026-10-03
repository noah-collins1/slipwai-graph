"""The refusal wherever the project sits (S23, R4; brownfield adoption, experimental).

Depth, a name git would quote, and a symbolic link change nothing: each placement repeats the three checks of
`tests/test_uncommitted_subdirectory.py` -- a person's edit refused by the project's own name for it, what a run
leaves recorded as the project spells it, an edit under `other/` refusing nothing. The prefix comes from git, so
no placement needs code of its own.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from support import FactoryTestCase
from test_adopt import repository, slipwai
from test_adopt_next import in_terminal
from test_candidates import MONOREPO, adopted
from test_replay import git
from test_uncommitted_subdirectory import PAGE


def placed(parent: Path, at: str) -> tuple[Path, Path]:
    """`test_uncommitted_subdirectory.placed`, with the project named (`--name shop`): a directory name like
    `dé pt` is not one a project can be called, and the placement is what is under test, not the name.
    The candidate is `shop` throughout."""
    files = {f"{at}/{name}": text for name, text in MONOREPO.items()}
    top = repository(parent, "shop", {**files, "other/note.txt": "x\n"})
    output = in_terminal(top / at, "adopt", "--no-init", "--name", "shop")
    assert (top / at / "project.json").is_file(), output
    assert git(top, "status", "--porcelain").stdout == "", "the adoption is committed"
    return top, top / at


class PlacementChecks(FactoryTestCase):
    def check(self, top: Path, project: Path, candidate: str, prefix: str) -> None:
        """The three checks, run in `project` (which may be a link to the project's real directory)."""
        page = project / PAGE
        page.write_text(page.read_text() + "\nA note of mine.\n")
        result = slipwai(project, "adopt", "--refresh")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn(f"`{PAGE}`", result.stderr)
        self.assertNotIn(prefix, result.stderr, "named as the project spells it, nothing of its place in the name")
        self.assertIn("A note of mine.", page.read_text(), "and nothing was written over it")
        git(top, "checkout", "--", prefix + PAGE)
        (top / "other/note.txt").write_text("mine\n")
        result = slipwai(project, "adopt", "--confirm", candidate)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((top / "other/note.txt").read_text(), "mine\n", "an edit under other/ refused nothing")
        keys = json.loads((project / ".delivery-tools/written.json").read_text())
        self.assertIn(PAGE, keys, "the run recorded what it left")
        for key in keys:
            self.assertTrue((project / key).exists(), key)
            self.assertFalse(key.startswith((prefix, "/", "./")), f"{key}: spelled relative to the project")

    def in_place(self, at: str, candidate: str) -> None:
        with tempfile.TemporaryDirectory() as directory:
            top, project = placed(Path(directory), at=at)
            self.check(top, project, candidate, f"{at}/")

    def test_a_project_in_a_nested_directory_is_refused_and_recorded_as_it_spells_its_files(self) -> None:
        self.in_place("a/b", "shop")

    def test_a_project_in_a_directory_git_would_quote_is_refused_and_recorded_as_it_spells_its_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            try:
                (Path(directory) / "dé pt").mkdir()
            except OSError as error:
                self.skipTest(f"this filesystem cannot make a non-ASCII directory name: {error}")
        self.in_place("dé pt", "shop")

    def link_to(self, real: Path, link: Path) -> Path:
        try:
            link.symlink_to(real, target_is_directory=True)
        except (OSError, NotImplementedError) as error:
            self.skipTest(f"this platform cannot make a symbolic link: {error}")
        return link

    def test_commands_run_in_a_link_to_the_project_outside_the_repository_are_refused_and_recorded_alike(self) -> None:
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as elsewhere:
            top, project = placed(Path(directory), "sub")
            self.check(top, self.link_to(project, Path(elsewhere) / "shortcut"), "shop", "sub/")

    def test_commands_run_in_a_link_to_the_project_inside_the_repository_are_refused_and_recorded_alike(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            top, project = placed(Path(directory), "sub")
            self.check(top, self.link_to(project, top / "other" / "shortcut"), "shop", "sub/")


class WhereNothingChanges(FactoryTestCase):
    """Holds (S23, R6; AC-S23-7, -8): green before the slice's production change and after, none a RED."""

    def test_hold_at_the_top_of_the_repository_the_recorded_keys_are_spelled_as_before(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = adopted(Path(directory))
            self.assertEqual(git(repo, "status", "--porcelain").stdout, "", "the adoption is committed")
            result = slipwai(repo, "adopt", "--confirm", "shop")
            self.assertEqual(result.returncode, 0, result.stderr)
            keys = json.loads((repo / ".delivery-tools/written.json").read_text())
            # The set the pre-slice text wrote (observed): these exact spellings, so `./project.json`, an absolute
            # path or a top-relative prefix would each miss one.
            self.assertTrue({"project.json", "delivery/.written", "delivery/Makefile", PAGE} <= set(keys), keys)
            for key in keys:
                self.assertTrue((repo / key).exists(), key)
                self.assertFalse(key.startswith(("./", "/")), f"{key}: neither dotted nor absolute")
                self.assertEqual(key, Path(key).as_posix())

    def test_hold_a_project_copied_to_a_directory_in_no_repository_is_refreshed_and_records_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as elsewhere:
            repo = adopted(Path(directory))
            copy = Path(elsewhere) / "shop"
            shutil.copytree(repo, copy, ignore=shutil.ignore_patterns(".git"))
            probe = subprocess.run(["git", "rev-parse"], cwd=copy, capture_output=True)
            if probe.returncode == 0:
                self.skipTest("the temporary directory sits inside a git repository on this machine")
            (copy / PAGE).write_text((copy / PAGE).read_text() + "\nA note of mine.\n")
            result = slipwai(copy, "adopt", "--refresh")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertNotIn("Traceback", result.stderr)
            self.assertNotIn("uncommitted", result.stderr, "nothing is refused where git cannot answer")
            self.assertFalse((copy / ".delivery-tools/written.json").exists(), "nothing to record without git")
