"""R6 (AC-S03-32, D83 item 1): the key covers every file under the project, whatever makes git ignore it, except a
closed exempt list, each entry with one of three reasons and its named exceptions.

The two reproductions of the adversary's A1 run through `make verify` with the stand-ins: a scratch test that git
ignores through a committed pattern and does not compile, and a module ignored through `.git/info/exclude` that breaks
`check-imports`. The rest holds the list itself, in both directions, in this process through the function `reuse` calls.
"""
from __future__ import annotations

import subprocess

from stamp_fixture import KeyTestCase, StampTestCase, commit_all, exclude, load_script, probe_path

SCRATCH = "apps/service/tests/scratch_broken.py"
MODULE = "apps/service/src/fixture/domain/bad.py"


class IgnoredFilesThroughMakeTest(StampTestCase):
    def stamped(self) -> None:
        self.assertEqual(self.run_gate().returncode, 0)
        self.assertIsNotNone(self.stamp_path())
        self.forget_log()

    def assert_full_gate_fails(self, path: str, content: str) -> None:
        target = self.repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        self.assertEqual(subprocess.run(["git", "check-ignore", "-q", path], cwd=self.repo, check=False).returncode, 0,
                         "the premise: git ignores it")
        run = self.run_gate()
        self.assertTrue(self.checks(), "no check started: the stamp was reused for a tree the gate fails")
        self.assertNotEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertIsNone(self.stamp_path(), "a failing tree left a stamp")
        forced = self.run_gate({"VERIFY_FORCE": "1"})
        self.assertNotEqual(forced.returncode, 0, "the forced run passes, so the premise is wrong")

    def test_an_ignored_scratch_test_that_does_not_compile_runs_the_full_gate(self) -> None:
        """A1: a committed pattern ignores it, `compileall` walks the tests, and the plain run used to reuse."""
        with (self.repo / ".gitignore").open("a", encoding="utf-8") as handle:
            handle.write("scratch_*.py\n")
        commit_all(self.repo, "ignore scratch files")
        self.stamped()
        self.assert_full_gate_fails(SCRATCH, "def (:\n")

    def test_a_module_ignored_through_the_exclude_file_that_breaks_check_imports_runs_the_full_gate(self) -> None:
        """A1: `.git/info/exclude` is no commit's; `check-imports` walks the source tree and finds the import."""
        exclude(self.repo, MODULE)
        self.stamped()
        self.assert_full_gate_fails(MODULE, "from fixture.adapters.store import x\n")

    def test_an_ignored_directory_that_is_itself_a_repository_is_a_run_that_records_nothing(self) -> None:
        """AC-S03-12 for an ignored directory nobody listed: the key cannot vouch for it, one line says so."""
        exclude(self.repo, "vendor/")
        (self.repo / "vendor" / "lib").mkdir(parents=True)
        subprocess.run(["git", "init", "-q", str(self.repo / "vendor" / "lib")], check=True)
        (self.repo / "vendor" / "lib" / "a.txt").write_text("a\n", encoding="utf-8")
        run = self.run_gate()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertTrue(self.checks())
        lines = [line for line in self.reuse_lines(run) if "repository" in line]
        self.assertEqual(len(lines), 1, run.stdout)
        self.assertIn("vendor/lib", lines[0])
        self.assertIsNone(self.stamp_path())


class ExemptListTest(KeyTestCase):
    def exempt(self) -> tuple[tuple[str, str, tuple[str, ...]], ...]:
        entries = tuple(load_script(self.repo).EXEMPT)
        self.assertTrue(entries, "the exempt list is empty: every cache would move the key")
        return entries

    def moves(self, path: str, content: bytes = b"one") -> bool:
        """Whether an ignored file at `path` moves the key: absent, created and changed in turn, then removed."""
        exclude(self.repo, path)
        absent = self.key()
        target = self.repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        created = self.key()
        target.write_bytes(content + b"two")
        changed = self.key()
        target.unlink()
        self.assertEqual(self.key(), absent, "absence is a value, and the same one")
        return len({absent, created, changed}) == 3

    def test_every_entry_has_one_of_the_three_reasons_and_matches_its_own_probe(self) -> None:
        script = load_script(self.repo)
        self.assertEqual(sorted(script.REASONS), ["cache", "rebuilt", "record"])
        for entry, reason, exceptions in self.exempt():
            with self.subTest(entry=entry):
                self.assertIn(reason, script.REASONS)
                self.assertTrue(script.REASONS[reason].strip(), "a reason is words")
                found = script.exempt_entry(probe_path(entry))
                self.assertIsNotNone(found)
                assert found is not None
                self.assertEqual(found[0], entry)
                for exception in exceptions:
                    directory = probe_path(entry).rsplit("/", 1)[0]
                    self.assertIsNone(script.exempt_entry(directory + "/" + exception), f"{exception} stays in the key")

    def test_a_file_an_entry_exempts_does_not_move_the_key_at_the_top_and_at_depth(self) -> None:
        for entry, _, _ in self.exempt():
            for under in ("", "apps/service/"):
                with self.subTest(entry=entry, under=under):
                    path = probe_path(entry, under)
                    if under and "/" in entry.strip("/").rstrip("/"):
                        continue  # an entry with a path in it is anchored at the project's directory
                    self.assertFalse(self.moves(path), f"{path} is exempt and moved the key")

    def test_an_exception_an_entry_names_stays_in_the_key(self) -> None:
        named = [(entry, exception) for entry, _, exceptions in self.exempt() for exception in exceptions]
        self.assertTrue(named)
        for entry, exception in named:
            with self.subTest(entry=entry, exception=exception):
                directory = probe_path(entry).rsplit("/", 1)[0]
                self.assertTrue(self.moves(directory + "/" + exception))

    def test_the_named_exceptions_are_the_ones_the_criterion_names(self) -> None:
        by_entry = {entry: exceptions for entry, _, exceptions in self.exempt()}
        self.assertEqual(sorted(by_entry[".codegraph/"]), ["codegraph.db", "codegraph.db-wal"])
        self.assertEqual(by_entry["node_modules/"], (".package-lock.json",))
        self.assertIn(".venv/", by_entry)

    def test_an_ignored_path_nobody_listed_is_hashed_whole(self) -> None:
        """A1: a scratch file, a directory of notes, a file under a hidden directory — each moves the key."""
        for path in ("scratch_one.py", "notes/draft.md", ".idea/workspace.xml", "apps/service/tests/scratch_x.py",
                     ".claude/skills/x/SKILL.md", "tools/ux-gates/README.md", ".env", ".delivery-tools/yaml.py",
                     "specs/001-x/plan.md"):
            with self.subTest(path=path):
                self.assertTrue(self.moves(path))
