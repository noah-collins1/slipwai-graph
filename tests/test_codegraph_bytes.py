"""What a narrowed `check-codegraph` run cannot know from git alone (S01-gate-walks, T016 and T017).

The constitution's MUST: a narrowed run never reports *current* where the whole run would not. These examples are the
states git does not report faithfully: a path git was told not to report at the moment the memory vouched, and a file
whose bytes changed in a way git's comparison normalises away. Helpers are those of `test_codegraph_narrowed`.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from support import FactoryTestCase
from test_codegraph_memory import whole_line
from test_codegraph_narrowed import Project, narrowed_line

NO_SYNC = {"CODEGRAPH_GATE_NO_SYNC": "1"}
FLAGS = (("--assume-unchanged", "--no-assume-unchanged"), ("--skip-worktree", "--no-skip-worktree"))


class WhatGitWasNotReportingWhenTheMemoryVouchedTest(FactoryTestCase):
    """T017: a path flagged at the write is hashed afterwards, whichever run wrote the memory."""

    def reverted_after_the_flag_is_cleared(self, project: Project, path: str, clear: str) -> None:
        project.git("update-index", clear, path)
        project.git("checkout", "--", path)
        failed = project.run(**NO_SYNC)
        self.assertEqual(failed.returncode, 1, failed.stdout)
        self.assertIn(f"- {path}", failed.stderr)
        project.git("checkout", "-q", "main")
        self.assertEqual(project.run(**NO_SYNC).returncode, 1, "the whole run says the same")

    def test_flagged_and_edited_before_a_whole_pass_wrote_the_memory(self) -> None:
        for flag, clear in FLAGS:
            with self.subTest(flag), tempfile.TemporaryDirectory() as directory:
                project = Project(self, directory)
                path = project.source()
                project.git("update-index", flag, path)
                project.edit(path)
                project.resync()
                project.whole()
                project.slice()
                self.reverted_after_the_flag_is_cleared(project, path, clear)

    def test_flagged_and_edited_before_a_narrowed_pass_renewed_the_memory(self) -> None:
        for flag, clear in FLAGS:
            with self.subTest(flag), tempfile.TemporaryDirectory() as directory:
                project = Project(self, directory)
                project.whole()
                project.slice()
                path = project.source()
                project.git("update-index", flag, path)
                project.edit(path)
                project.resync()
                passed = project.run(**NO_SYNC)
                self.assertEqual(passed.returncode, 0, passed.stderr)
                self.assertIn("hashed 1 of", passed.stdout)
                self.reverted_after_the_flag_is_cleared(project, path, clear)


def line_endings(project: Project, path: str, ending: bytes) -> None:
    target = project.repo / path
    target.write_bytes(target.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", ending))


class WhatGitsComparisonNormalisesAwayTest(FactoryTestCase):
    """T016: the bytes on disk are what the index's row is of, whatever `* text=auto eol=lf` says of them."""

    def same_as_the_whole_run(self, project: Project, path: str) -> None:
        failed = project.run(**NO_SYNC)
        self.assertEqual(failed.returncode, 1, failed.stdout)
        self.assertIn(f"- {path}", failed.stderr)
        project.git("checkout", "-q", "main")
        whole = project.run(**NO_SYNC)
        self.assertEqual((failed.returncode, failed.stderr), (whole.returncode, whole.stderr))

    def test_crlf_before_git_add(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Project(self, directory)
            project.whole()
            project.slice()
            path = project.source()
            line_endings(project, path, b"\r\n")
            self.assertEqual(project.git("diff", "--name-only", "HEAD"), "", "git's comparison does not name it")
            self.same_as_the_whole_run(project, path)

    def test_crlf_after_git_add(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Project(self, directory)
            project.whole()
            project.slice()
            path = project.source()
            line_endings(project, path, b"\r\n")
            project.git("add", path)
            self.assertEqual(project.git("status", "--porcelain"), "", "after the add not even status names it")
            self.same_as_the_whole_run(project, path)

    def test_the_mirror_crlf_when_the_memory_was_written_and_lf_after(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Project(self, directory)
            path = project.source()
            line_endings(project, path, b"\r\n")
            project.resync()  # the index row is of the CRLF bytes, and the whole comparison passes on them
            project.whole()
            project.slice()
            line_endings(project, path, b"\n")
            self.same_as_the_whole_run(project, path)

    def test_a_same_size_rewrite_in_place_with_its_modification_time_restored(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Project(self, directory)
            project.git("config", "core.trustctime", "false")  # the filesystems and tools where git cannot see it
            project.git("config", "core.checkStat", "minimal")
            project.git("update-index", "--refresh")
            project.whole()
            project.slice()
            path = project.source()
            target = project.repo / path
            before = target.stat()
            data = target.read_bytes()
            target.write_bytes(data.replace(data[:1], b"#" if data[:1] != b"#" else b"!", 1))
            self.assertEqual(target.stat().st_size, before.st_size)
            os.utime(target, ns=(before.st_atime_ns, before.st_mtime_ns))
            self.assertEqual(project.git("status", "--porcelain"), "", "git cannot see it either")
            self.same_as_the_whole_run(project, path)

    def test_a_touch_is_hashed_once_and_then_not_again(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Project(self, directory)
            project.whole()
            project.slice()
            os.utime(project.repo / project.source())
            project.settle()
            first = project.run()
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertRegex(first.stdout, narrowed_line(1))
            self.assertRegex(project.run().stdout, narrowed_line(0))

    def test_a_memory_written_before_the_files_were_recorded_is_the_whole_run(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Project(self, directory)
            project.whole()
            project.slice()
            record = json.loads(project.memory.read_text())
            record.pop("files", None)
            project.memory.write_text(json.dumps(record))
            run = project.run()
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertRegex(run.stdout, whole_line("the record of the last whole comparison could not be read"))

    def test_a_file_modified_within_two_seconds_of_the_run_that_vouched_for_it_is_hashed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Project(self, directory)
            project.settle()
            path = project.source()
            os.utime(project.repo / path)  # the whole run starts moments after this
            project.whole(settled=False)
            project.slice()
            audited = project.audited()
            self.assertEqual(audited.result.returncode, 0, audited.result.stderr)
            self.assertRegex(audited.result.stdout, narrowed_line(1))
            self.assertIn(path, audited.opened)


class ATrackedFileTheIndexHoldsNoRowForTest(FactoryTestCase):
    """T021: narrowing narrows the hashing, never the never-seen judgement; the whole run's own test decides it."""

    def same_as_the_whole_run(self, project: Project, path: str) -> None:
        failed = project.run(**NO_SYNC)
        self.assertEqual(failed.returncode, 1, failed.stdout)
        self.assertIn("never seen", failed.stderr)
        self.assertIn(f"- {path}", failed.stderr)
        whole = project.run(CI="1", **NO_SYNC)  # a CI marker: the same tree, compared whole
        self.assertEqual((failed.returncode, failed.stderr), (whole.returncode, whole.stderr))

    def declined(self, project: Project) -> Path:
        """A tracked `.py` file the index declined: committed, no row, older than the index's last `indexed_at`."""
        target = project.repo / "declined.py"
        target.write_text("x = 1\n")
        project.commit("a file the index declined")
        os.utime(target, (0, 0))
        return target

    def test_a_declined_file_touched_after_a_whole_pass_is_judged_as_the_whole_run_judges_it(self) -> None:
        for how in ("touch", "crlf"):
            with self.subTest(how), tempfile.TemporaryDirectory() as directory:
                project = Project(self, directory)
                target = self.declined(project)
                project.whole()
                project.slice()
                if how == "touch":
                    os.utime(target)
                else:
                    target.write_bytes(b"x = 1\r\n")
                self.assertEqual(project.git("diff", "--name-only", "HEAD"), "", "git does not name it")
                self.same_as_the_whole_run(project, "declined.py")

    def test_hold_a_declined_file_left_alone_stays_current(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Project(self, directory)
            self.declined(project)
            project.whole()
            project.slice()
            passed = project.run(**NO_SYNC)
            self.assertEqual(passed.returncode, 0, passed.stderr)
            self.assertRegex(passed.stdout, narrowed_line(0))

    def test_hold_a_file_newly_tracked_after_the_memory_is_judged_however_git_reports_it(self) -> None:
        """Hold: the run is the whole run's, committed, staged, or intent-to-add. Its teeth are git's report."""
        for how in ("commit", "add", "add -N"):
            with self.subTest(how), tempfile.TemporaryDirectory() as directory:
                project = Project(self, directory)
                project.whole()
                project.slice()
                (project.repo / "brand_new.py").write_text("y = 2\n")
                if how == "commit":
                    project.commit("a new file")
                else:
                    project.git("add", *how.split()[1:], "brand_new.py")
                self.same_as_the_whole_run(project, "brand_new.py")
