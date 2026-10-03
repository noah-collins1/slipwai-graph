"""An entry of `git status` that carries a second path is one entry (S23, T011; brownfield adoption, experimental).

`git status --porcelain=v1 -z` prints a rename or a copy as `XY to NUL from NUL`, and `R` or `C` may stand in
either column: `R ` is staged, ` R` is a rename in the working tree that `git add -N` made visible, and `C` is
what `status.renames=copies` prints for a copy whose source was edited (read from `git help status`; the shapes
below are asserted against what git prints here, so a git that spells one differently fails the example and not
the sweep). `changed()` is called directly because only its return value shows which paths it took for changes: a
CLI run shows only the paths it writes, and the origin of a rename is a path nothing here writes.

The project is `ab/` and holds `ab/ab/x.md`, so that the origin read as an entry of its own with its first three
characters cut off (`ab/` -- the cut of a status letter pair and a space) is a file that exists, `ab/x.md`, which
nobody changed.
"""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from support import FactoryTestCase
from test_replay import git

from slipwai.uncommitted import changed

BODY = "a line of body\n" * 30

def prepared(parent: Path, copies: bool) -> Path:
    top = parent / "repo"
    for relative in ("ab/ab/x.md", "ab/y.md", "other/c.md"):
        path = top / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"{relative}\n{BODY}")
    git(top, "init", "-q", "-b", "main")
    if copies:
        git(top, "config", "status.renames", "copies")
    git(top, "add", "-A")
    git(top, "-c", "user.name=t", "-c", "user.email=t@local", "commit", "-q", "-m", "theirs")
    return top


def move(top: Path, source: str, to: str, copy: bool, staged: bool) -> None:
    (top / to).parent.mkdir(parents=True, exist_ok=True)
    text = (top / source).read_text()
    if copy:
        (top / source).write_text(text + "edited, so that git sees what was copied\n")
        (top / to).write_text(text)
    else:
        (top / source).rename(top / to)
    git(top, "add", "-A" if staged else "-N", *([] if staged else [to]))


class StatusEntriesWithASecondPathTest(FactoryTestCase):
    def check(
        self, source: str, to: str, *, copy: bool, staged: bool, shape: dict[str, str], expected: dict[str, list[str]]
    ) -> None:
        """`shape` is the `XY` git prints for the moved file, `expected` the whole answer, each by where the project
        is (`""` the top, `"ab"`); a shape of `""` is a copy git does not print as one there."""
        for at, answer in expected.items():
            with self.subTest(at=at or "top"), tempfile.TemporaryDirectory() as directory:
                top = prepared(Path(directory), copy)
                move(top, source, to, copy, staged)
                root = top / at if at else top
                printed = subprocess.run(
                    ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all", "--", "."],
                    cwd=root, capture_output=True, text=True, check=True,
                ).stdout
                codes = [e[:2] for e in printed.split("\0") if len(e) > 3 and e[2] == " "]
                if shape[at]:
                    self.assertIn(shape[at], codes, f"git printed {printed!r}")
                else:
                    self.assertFalse([c for c in codes if "C" in c], f"git printed {printed!r}")
                self.assertEqual(sorted(changed(root) or []), answer, f"git printed {printed!r}")

    # Renames. Inside the project; outside it into it; out of it. Staged (`R `) and in the working tree (` R`).
    def test_a_staged_rename_inside_the_project_is_the_new_path_only(self) -> None:
        self.check("ab/ab/x.md", "ab/moved.md", copy=False, staged=True, shape={"": "R ", "ab": "R "},
                   expected={"": ["ab/moved.md"], "ab": ["moved.md"]})

    def test_a_rename_in_the_working_tree_inside_the_project_is_the_new_path_only(self) -> None:
        self.check("ab/ab/x.md", "ab/moved.md", copy=False, staged=False, shape={"": " R", "ab": " R"},
                   expected={"": ["ab/moved.md"], "ab": ["moved.md"]})

    def test_a_staged_rename_from_outside_in_is_the_new_path_only(self) -> None:
        self.check("other/c.md", "ab/moved.md", copy=False, staged=True, shape={"": "R ", "ab": "A "},
                   expected={"": ["ab/moved.md"], "ab": ["moved.md"]})

    def test_a_rename_in_the_working_tree_from_outside_in_is_the_new_path_only(self) -> None:
        self.check("other/c.md", "ab/moved.md", copy=False, staged=False, shape={"": " R", "ab": " A"},
                   expected={"": ["ab/moved.md"], "ab": ["moved.md"]})

    def test_a_staged_rename_from_inside_out_is_the_new_path_at_the_top_and_the_deletion_below(self) -> None:
        self.check("ab/ab/x.md", "other/moved.md", copy=False, staged=True, shape={"": "R ", "ab": "D "},
                   expected={"": ["other/moved.md"], "ab": ["ab/x.md"]})

    def test_a_working_tree_rename_from_inside_out_is_the_new_path_at_the_top_and_the_deletion_below(self) -> None:
        self.check("ab/ab/x.md", "other/moved.md", copy=False, staged=False, shape={"": " R", "ab": " D"},
                   expected={"": ["other/moved.md"], "ab": ["ab/x.md"]})

    # Copies: git prints `C` only for `status.renames=copies`, and only where the source is edited as well.
    def test_a_staged_copy_inside_the_project_is_the_new_path_and_the_edited_source(self) -> None:
        self.check("ab/ab/x.md", "ab/moved.md", copy=True, staged=True, shape={"": "C ", "ab": "C "},
                   expected={"": ["ab/ab/x.md", "ab/moved.md"], "ab": ["ab/x.md", "moved.md"]})

    def test_a_copy_in_the_working_tree_inside_the_project_is_the_new_path_and_the_edited_source(self) -> None:
        self.check("ab/ab/x.md", "ab/moved.md", copy=True, staged=False, shape={"": " C", "ab": " C"},
                   expected={"": ["ab/ab/x.md", "ab/moved.md"], "ab": ["ab/x.md", "moved.md"]})

    def test_a_staged_copy_from_outside_in_is_the_new_path_and_the_source_only_at_the_top(self) -> None:
        self.check("other/c.md", "ab/moved.md", copy=True, staged=True, shape={"": "C ", "ab": "A "},
                   expected={"": ["ab/moved.md", "other/c.md"], "ab": ["moved.md"]})

    def test_a_copy_in_the_working_tree_from_outside_in_is_the_new_path_and_the_source_only_at_the_top(self) -> None:
        self.check("other/c.md", "ab/moved.md", copy=True, staged=False, shape={"": " C", "ab": " A"},
                   expected={"": ["ab/moved.md", "other/c.md"], "ab": ["moved.md"]})

    def test_a_staged_copy_from_inside_out_is_the_edited_source_in_the_project(self) -> None:
        self.check("ab/ab/x.md", "other/moved.md", copy=True, staged=True, shape={"": "C ", "ab": ""},
                   expected={"": ["ab/ab/x.md", "other/moved.md"], "ab": ["ab/x.md"]})

    def test_a_copy_in_the_working_tree_from_inside_out_is_the_edited_source_in_the_project(self) -> None:
        self.check("ab/ab/x.md", "other/moved.md", copy=True, staged=False, shape={"": " C", "ab": ""},
                   expected={"": ["ab/ab/x.md", "other/moved.md"], "ab": ["ab/x.md"]})
