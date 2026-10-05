"""T048 (adversary A1 · AC-S06-2, -5): a path is changed when its raw bytes or mode differ from the base's blob.

`check-slice-scope.changed_files` asks `git diff`, which applies git's filters: CRLF under `text=auto eol=lf`, a mode
bit under `core.fileMode=false`, a clean filter, `ident`, `working-tree-encoding`. The stamp reads raw bytes, so a
difference they hide made the scoped run skip a check `make verify` fails. Each example makes `git diff <base>` say
nothing and shows the check still runs. The filters are set in `.git/info/attributes` and the repository's config, so
no tracked file differs.
"""
from __future__ import annotations

import subprocess
import sys

from scoped_fixture import FULL, SLICE, ShapeCase
from stamp_fixture import git

sys.dont_write_bytecode = True

DRY: dict[str, str | None] = {"STANDIN_DRY": "1"}
APP = "apps/web/src/App.tsx"
NOTE = "apps/web/src/note.txt"


class ChangedTest(ShapeCase):
    shape = "model-typescript-web"

    def attributes(self, text: str) -> None:
        (self.repo / ".git" / "info").mkdir(exist_ok=True)
        (self.repo / ".git" / "info" / "attributes").write_text(text, encoding="utf-8")

    def config(self, key: str, value: str) -> None:
        git(self.repo, "config", key, value)

    def new_base(self, path: str, content: bytes) -> None:
        """`path` committed on `main` as it is, and the slice cut again from there, its baseline taken."""
        git(self.repo, "checkout", "-q", "main")
        (self.repo / path).write_bytes(content)
        git(self.repo, "add", path)
        git(self.repo, "commit", "-q", "-m", "a file for the example")
        git(self.repo, "checkout", "-q", "-B", SLICE)
        self.write_baseline()

    def assert_hidden(self) -> None:
        """The example's premise: git, filters applied, sees no difference from the base."""
        quiet = subprocess.run(["git", "diff", "--quiet", "main"], cwd=self.repo, check=False)
        self.assertEqual(quiet.returncode, 0, "git itself sees the difference: " + git(self.repo, "diff", "main"))
        self.assertEqual(git(self.repo, "ls-files", "--others", "--exclude-standard").strip(), "")

    def assert_runs(self, unit: str = "lint-web") -> None:
        self.assert_hidden()
        run = self.scoped(DRY)
        ran, skipped = self.decided(run)
        full = any(line.startswith(FULL) for line in self.scoped_lines(run))
        self.assertTrue(unit in ran or full, f"{unit} was skipped though a byte differs: " + run.stdout + run.stderr)
        self.assertNotIn(unit, skipped)

    def test_e1_crlf_under_text_auto_eol_lf_is_changed(self) -> None:
        self.attributes("* text=auto eol=lf\n")
        old = (self.repo / APP).read_bytes()
        (self.repo / APP).write_bytes(old.replace(b"\n", b"\r\n"))
        self.assert_runs()

    def test_e1_crlf_under_core_autocrlf_is_changed(self) -> None:
        self.config("core.autocrlf", "true")
        old = (self.repo / APP).read_bytes()
        (self.repo / APP).write_bytes(old.replace(b"\n", b"\r\n"))
        self.assert_runs()

    def test_e1_a_mode_bit_under_core_filemode_false_is_changed(self) -> None:
        self.config("core.fileMode", "false")
        (self.repo / APP).chmod(0o755)
        self.assert_runs()

    def test_e1_a_scripts_verify_mode_is_the_full_gate(self) -> None:
        self.config("core.fileMode", "false")
        (self.repo / "scripts" / "verify").chmod(0o644)
        self.assert_hidden()
        run = self.scoped(DRY)
        self.assertTrue(any(line.startswith(FULL) for line in self.scoped_lines(run)), run.stdout + run.stderr)

    def test_e1_what_a_clean_filter_normalises_away_is_changed(self) -> None:
        self.attributes("*.tsx filter=strip\n")
        self.config("filter.strip.clean", "sed -e 's/[ ]*$//'")
        self.config("filter.strip.smudge", "cat")
        (self.repo / APP).write_bytes((self.repo / APP).read_bytes().replace(b"\n", b"   \n", 1))
        self.assert_runs()

    def test_e1_an_expanded_ident_keyword_is_changed(self) -> None:
        self.new_base("apps/web/src/id.ts", b"// $Id$\nexport const id = 1\n")
        self.attributes("*.ts ident\n")
        (self.repo / "apps/web/src/id.ts").write_bytes(b"// $Id: 0123456789abcdef $\nexport const id = 1\n")
        self.assert_runs()

    def test_e1_a_working_tree_encoding_is_changed(self) -> None:
        self.new_base(NOTE, b"hello\n")
        self.attributes("*.txt working-tree-encoding=UTF-16\n")  # a checkout writes the little-endian form
        (self.repo / NOTE).write_bytes(b"\xfe\xff" + "hello\n".encode("utf-16-be"))
        self.assert_runs()

    def test_e1_a_link_that_points_elsewhere_is_changed(self) -> None:
        self.new_base(NOTE, b"hello\n")
        (self.repo / NOTE).unlink()
        (self.repo / NOTE).symlink_to("elsewhere")
        run = self.scoped(DRY)
        ran, skipped = self.decided(run)
        self.assertNotIn("lint-web", skipped, run.stdout)

    def test_e2_an_untouched_tree_under_every_filter_skips_as_before(self) -> None:
        self.attributes("* text=auto eol=lf\n*.tsx filter=strip\n")
        self.config("filter.strip.clean", "sed -e 's/[ ]*$//'")
        self.config("core.fileMode", "false")
        self.config("core.autocrlf", "input")
        run = self.scoped(DRY)
        ran, skipped = self.decided(run)
        self.assertNotIn("lint-web", ran, run.stdout + run.stderr)
        self.assertIn("lint-web", skipped, run.stdout + run.stderr)

    def test_e2_a_file_as_a_checkout_writes_it_under_eol_crlf_is_not_changed(self) -> None:
        """Raw bytes differ from the blob's, but they are the bytes git itself writes there: not an edit."""
        self.attributes("*.tsx text eol=crlf\n")
        (self.repo / APP).write_bytes((self.repo / APP).read_bytes().replace(b"\n", b"\r\n"))
        self.assert_hidden()
        ran, skipped = self.decided(self.scoped(DRY))
        self.assertIn("lint-web", skipped)
        self.assertNotIn("lint-web", ran)
