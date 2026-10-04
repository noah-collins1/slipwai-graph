"""R6 (AC-S03-7, -8, -9): the key is what a check reads that git ignores, and the variables that change an answer.

The lists are read from the script, never copied here; what this module holds is that each entry moves the key
(changed, created and removed in turn), that each variable's three states are three keys, that the installed
environments are where each backend's recipe says they are, and that a run that tightens the ratchet neither reads
nor writes a stamp. One entry runs through the real `make verify`; the rest build the key in this process, which is
the function `reuse` calls.
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from stamp_fixture import CLOSING, KeyTestCase, StampTestCase, load_script, template
from support import FactoryTestCase

# What the criteria name, held as a floor: a list that dropped one fails here, and a list longer than this is fine.
NAMED_ENTRIES = (".codegraph/codegraph.db", ".codegraph/codegraph.db-wal", "tools/ux-gates/", "skills/ui-ux-pro-max/",
                 ".env")
NAMED_VARIABLES = ("UX_GATES_REQUIRE", "UX_GATES_SINCE", "UX_GATES_SHARD", "CODEGRAPH_GATE_NO_SYNC",
                   "SLIPWAI_NO_INSTALL", "GITHUB_HEAD_REF", "CI_COMMIT_REF_NAME")


def concrete(entry: str) -> str:
    """A path an entry names: a glob's star becomes one feature's directory."""
    return entry.replace("*", "001")


class IgnoredInputsTest(KeyTestCase):
    def test_the_lists_hold_what_the_criteria_name(self) -> None:
        """e7, e9: a floor, so that the loops below are never over nothing."""
        script = load_script(self.repo)
        for entry in NAMED_ENTRIES:
            self.assertIn(entry, script.IGNORED_INPUTS)
        for name in NAMED_VARIABLES:
            self.assertIn(name, script.VARIABLES)
        self.assertNotIn("UX_GATES_JOBS", script.VARIABLES)
        self.assertIn("UX_GATES_JOBS", script.UNKEYED_VARIABLES)
        self.assertNotIn(".codegraph/gate-memory.json", script.IGNORED_INPUTS)

    def ignore(self, target: Path) -> None:
        """Hold the premise: the path is one git ignores here — a project that needs `.env` ignores it, and this one
        does not need it, so the line a project with a transport has is added."""
        relative = str(target.relative_to(self.repo))
        if subprocess.run(["git", "check-ignore", "-q", relative], cwd=self.repo, check=False).returncode != 0:
            with (self.repo / ".gitignore").open("a", encoding="utf-8") as handle:
                handle.write(relative + "\n")
        done = subprocess.run(["git", "check-ignore", "-q", relative], cwd=self.repo, check=False)
        self.assertEqual(done.returncode, 0, f"{relative} is not ignored, so it is not this list's")

    def test_each_ignored_input_moves_the_key_changed_created_and_removed(self) -> None:
        """e7: one example per entry, absence a value: absent, created, changed, removed, and absent's key again."""
        script = load_script(self.repo)
        self.assertTrue(script.IGNORED_INPUTS)
        for entry in script.IGNORED_INPUTS:
            with self.subTest(entry=entry):
                path = self.repo / concrete(entry)
                target = path / "probe.txt" if entry.endswith("/") else path
                self.ignore(target)
                absent = self.key()
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(b"one")
                created = self.key()
                target.write_bytes(b"two")
                changed = self.key()
                target.unlink()
                removed = self.key()
                self.assertEqual(len({absent, created, changed}), 3, "an entry's bytes did not move the key")
                self.assertEqual(removed, absent, "absence is a value, and the same one")
                if entry.endswith("/") and path.is_dir() and not any(path.iterdir()):
                    path.rmdir()

    def test_a_link_inside_an_ignored_directory_is_read_by_its_target_and_not_followed(self) -> None:
        """e7: the slot a Spec Kit command writes through is a link; what it points at is not this list's to read."""
        outside = self.repo.parent / "outside"
        outside.mkdir()
        (outside / "file.txt").write_text("one", encoding="utf-8")
        kit = self.repo / "tools/ux-gates"
        kit.mkdir(parents=True)
        try:
            (kit / "link").symlink_to(outside)
        except (OSError, NotImplementedError):
            self.skipTest("this platform cannot make a symbolic link")
        before = self.key()
        (outside / "file.txt").write_text("two", encoding="utf-8")
        self.assertEqual(self.key(), before, "the key followed a link out of the ignored directory")
        (kit / "link").unlink()
        (kit / "link").symlink_to(self.repo.parent)
        self.assertNotEqual(self.key(), before, "a link retargeted did not move the key")

    def test_an_ignored_input_runs_the_gate_through_make(self) -> None:
        """e7: the installed UX-gates kit through the real gate — the full gate runs and a new stamp is written."""
        self.assertEqual(self.run_gate().returncode, 0)
        before = self.stamp()["key"]
        self.forget_log()
        kit = self.repo / "tools/ux-gates/README.md"
        kit.parent.mkdir(parents=True)
        kit.write_text("a kit\n", encoding="utf-8")
        self.assertEqual(subprocess.run(["git", "check-ignore", "-q", "tools/ux-gates/README.md"], cwd=self.repo,
                                        check=False).returncode, 0)
        run = self.run_gate()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertTrue(self.checks(), "no check started: the ignored file was not in the key")
        self.assertNotEqual(self.stamp()["key"], before)

    def test_the_canonical_slots_are_in_the_list(self) -> None:
        """e7, the sweep: `check-slice-scope` reads the five ignored slots at a feature root (a regular file there
        fails it), so they are inputs the criterion did not name."""
        script = load_script(self.repo)
        for slot in ("plan.md", "research.md", "data-model.md", "quickstart.md", "tasks.md"):
            self.assertIn(f"specs/*/{slot}", script.IGNORED_INPUTS)


class VariablesTest(KeyTestCase):
    def test_each_variable_set_empty_and_unset_is_three_keys(self) -> None:
        """e9: unset is not empty, and neither is a value."""
        script = load_script(self.repo)
        self.assertTrue(script.VARIABLES)
        for name in script.VARIABLES:
            with self.subTest(variable=name):
                with self.variable(name, None):
                    unset = self.key()
                with self.variable(name, ""):
                    empty = self.key()
                with self.variable(name, "1"):
                    value = self.key()
                with self.variable(name, "2"):
                    another = self.key()
                self.assertEqual(len({unset, empty, value, another}), 4)

    def test_the_jobs_variable_changes_nothing(self) -> None:
        """e9: `UX_GATES_JOBS` is how many run at once, not what they say."""
        with self.variable("UX_GATES_JOBS", None):
            unset = self.key()
        with self.variable("UX_GATES_JOBS", "8"):
            self.assertEqual(self.key(), unset)

    def test_a_variable_runs_the_gate_through_make_and_the_jobs_one_does_not(self) -> None:
        """e9: the gate as typed — `UX_GATES_REQUIRE=1` is a full run, `UX_GATES_JOBS=4` a reuse."""
        self.assertEqual(self.run_gate().returncode, 0)
        self.forget_log()
        self.run_gate({"UX_GATES_JOBS": "4"})
        self.assertEqual(self.checks(), [], "UX_GATES_JOBS moved the key")
        run = self.run_gate({"UX_GATES_REQUIRE": "1"})
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertTrue(self.checks(), "no check started: the variable was not in the key")


class RatchetTest(StampTestCase):
    def slipwai_directory(self) -> list[str]:
        directory = self.repo / ".git" / "slipwai"
        return sorted(path.name for path in directory.iterdir()) if directory.is_dir() else []

    def test_a_run_that_tightens_the_ratchet_reads_no_stamp(self) -> None:
        """e9: the stamp's bytes stand, every check runs, and nothing is said but what the gate says."""
        self.assertEqual(self.run_gate().returncode, 0)
        path = self.stamp_path()
        assert path is not None
        before = path.read_bytes()
        self.forget_log()
        run = self.run_gate({"RATCHET_TIGHTEN": "1"})
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertTrue(self.checks(), "a stamp was read by a run that tightens the ratchet")
        self.assertEqual(self.reuse_lines(run), [])
        self.assertTrue(run.stdout.endswith(f"{CLOSING}\n"))
        self.assertEqual(path.read_bytes(), before)

    def test_a_run_that_tightens_the_ratchet_writes_no_stamp(self) -> None:
        """e9: with none standing, none is made, and no note is left."""
        run = self.run_gate({"RATCHET_TIGHTEN": "1"})
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertTrue(self.checks())
        self.assertEqual(self.slipwai_directory(), [])
        self.assertEqual(self.reuse_lines(run), [])


class InstalledEnvironmentsTest(FactoryTestCase):
    """e8, AC-S03-8: the plan's table per backend, read from what each backend generates. An installed environment is
    outside the key only where the gate's own recipe rebuilds it from a committed lock on every run."""

    def project(self, backend: str, profile: str = "standard") -> Path:
        directory = tempfile.mkdtemp(prefix="stamp-env-")
        self.addCleanup(shutil.rmtree, directory, ignore_errors=True)
        return self.generate(directory, "env", profile, backend, http="none")

    def listed(self) -> tuple[str, ...]:
        script = load_script(template())
        return tuple(script.IGNORED_INPUTS)

    def test_python_syncs_from_the_lock_on_every_run(self) -> None:
        """e8: `uv sync --locked` before each phase; the environment is outside the key, its interpreter in it."""
        text = (self.project("python") / "scripts/verify").read_text(encoding="utf-8")
        self.assertIn('uv sync --project "$app" --locked --quiet', text)
        self.assertEqual([entry for entry in self.listed() if ".venv" in entry], [])

    def test_typescript_installs_only_when_the_lock_is_newer_so_its_manifest_is_in_the_key(self) -> None:
        """e8: `node_modules/.package-lock.json` is a file target — `npm ci` runs when `package.json` or the lock is
        newer than it, not on every run — so what is installed is an input, by the manifest npm wrote."""
        makefile = (self.project("typescript") / "Makefile").read_text(encoding="utf-8")
        self.assertIn("node_modules/.package-lock.json: package.json package-lock.json\n\tnpm ci\n", makefile)
        self.assertIn("node_modules/.package-lock.json", self.listed())

    def test_the_model_tooling_installs_without_the_lock_so_its_manifest_is_in_the_key(self) -> None:
        """e8: `npm --prefix scripts/event-model install` — no `ci`, and a satisfied tree is left as it is."""
        makefile = (self.project("python", "event-modelling") / "Makefile").read_text(encoding="utf-8")
        self.assertIn("npm --prefix scripts/event-model install", makefile)
        self.assertNotIn("npm --prefix scripts/event-model ci", makefile)
        self.assertIn("scripts/event-model/node_modules/.package-lock.json", self.listed())

    def test_go_and_java_install_nothing_into_the_checkout(self) -> None:
        """e8: modules and wrapper distributions live in the user's cache, outside the checkout, and what the build
        writes beside the code (`target/`, coverage files) is rebuilt by the recipe, not installed — so no backend
        directory is on the list."""
        for backend in ("go", "java-quarkus", "java-spring"):
            with self.subTest(backend=backend):
                project = self.project(backend)
                ignored = (project / ".gitignore").read_text(encoding="utf-8")
                self.assertNotIn("vendor/", ignored)
                self.assertNotIn("node_modules/", ignored)
        self.assertEqual([entry for entry in self.listed() if entry.startswith(("target", "vendor", "apps/"))], [])
