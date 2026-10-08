"""R6 (AC-S03-8, -9, -32): the key holds the ignored files a check can read, and the variables that change an answer.

The exempt list is read from the script, never copied here (`test_verify_stamp_ignored` holds it entry by entry); what
this module holds is the files an exempt list must not take out — a link, the tools the gate installs beside the
checkout, the slots a Spec Kit command writes through — that each variable's three states are three keys, that the
installed environments are where each backend's recipe says they are, and that a run that tightens the ratchet neither
reads nor writes a stamp. One example runs through the real `make verify`; the rest build the key in this process,
which is the function `reuse` calls.
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from stamp_fixture import CLOSING, KeyTestCase, StampTestCase, load_script, template
from support import FactoryTestCase

NAMED_VARIABLES = ("UX_GATES_REQUIRE", "UX_GATES_SINCE", "UX_GATES_SHARD", "CODEGRAPH_GATE_NO_SYNC",
                   "SLIPWAI_NO_INSTALL", "GITHUB_HEAD_REF", "CI_COMMIT_REF_NAME")


class IgnoredInputsTest(KeyTestCase):
    def test_the_variable_lists_hold_what_the_criteria_name(self) -> None:
        """e9: a floor, so that the loops below are never over nothing."""
        script = load_script(self.repo)
        for name in NAMED_VARIABLES:
            self.assertIn(name, script.VARIABLES)
        self.assertNotIn("UX_GATES_JOBS", script.VARIABLES)
        self.assertIn("UX_GATES_JOBS", script.UNKEYED_VARIABLES)

    def test_the_inputs_the_criteria_name_are_in_the_key_and_the_codegraph_memo_is_not(self) -> None:
        """AC-S03-32: what D73's list named stays covered, by being no exempt entry's; the memo is a record."""
        script = load_script(self.repo)
        for path in (".codegraph/codegraph.db", ".codegraph/codegraph.db-wal", "tools/ux-gates/README.md",
                     "skills/ui-ux-pro-max/SKILL.md", ".env", ".delivery-tools/yaml.py", "specs/001-x/plan.md",
                     ".claude/skills/a/SKILL.md", "node_modules/.package-lock.json"):
            with self.subTest(path=path):
                self.assertIsNone(script.exempt_entry(path))
        self.assertIsNotNone(script.exempt_entry(".codegraph/gate-memory.json"))

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

    def test_a_tool_the_gate_installs_beside_the_checkout_moves_the_key_changed_created_and_removed(self) -> None:
        """e7, T017: `check-model` puts `.delivery-tools/` first on `sys.path` and imports `yaml` from it; the gate
        installs there only on an `ImportError`, so what is installed is an input — a `yaml.py` that fails the check."""
        self.assertIsNone(load_script(self.repo).exempt_entry(".delivery-tools/yaml.py"))
        tool = self.repo / ".delivery-tools" / "yaml.py"
        self.assertEqual(subprocess.run(["git", "check-ignore", "-q", ".delivery-tools/yaml.py"], cwd=self.repo,
                                        check=False).returncode, 0, "the generated project does not ignore it")
        absent = self.key()
        tool.parent.mkdir()
        tool.write_text("raise ImportError\n", encoding="utf-8")
        created = self.key()
        tool.write_text("def safe_load(text): return {}\n", encoding="utf-8")
        changed = self.key()
        tool.unlink()
        self.assertEqual(len({absent, created, changed}), 3, "a change under .delivery-tools/ did not move the key")
        self.assertEqual(self.key(), absent, "absence is a value, and the same one")

    def test_a_tool_installed_beside_the_checkout_runs_the_gate_through_make(self) -> None:
        """e7, T017: the stamp is not reused for a tree whose `.delivery-tools/` changed."""
        self.assertEqual(self.run_gate().returncode, 0)
        self.forget_log()
        tool = self.repo / ".delivery-tools" / "yaml.py"
        tool.parent.mkdir()
        tool.write_text("raise ImportError\n", encoding="utf-8")
        run = self.run_gate()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertTrue(self.checks(), "no check started: a reused stamp stood for a changed tool")

    def test_the_canonical_slots_move_the_key(self) -> None:
        """e7, the sweep: `check-slice-scope` reads the five ignored slots at a feature root (a regular file there
        fails it), so they are inputs the criterion did not name."""
        for slot in ("plan.md", "research.md", "data-model.md", "quickstart.md", "tasks.md"):
            with self.subTest(slot=slot):
                path = self.repo / "specs" / "001-x" / slot
                path.parent.mkdir(parents=True, exist_ok=True)
                before = self.key()
                path.write_text("a regular file\n", encoding="utf-8")
                self.assertNotEqual(self.key(), before)
                path.unlink()


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

    def exempt(self, path: str) -> tuple[str, str, tuple[str, ...]] | None:
        return load_script(template()).exempt_entry(path)

    def test_python_syncs_from_the_lock_on_every_run(self) -> None:
        """e8: `uv sync --locked` before each phase; the environment is outside the key, its interpreter in it."""
        text = (self.project("python") / "scripts/verify").read_text(encoding="utf-8")
        self.assertIn('uv sync --project "$app" --locked --quiet', text)
        entry = self.exempt("apps/service/.venv/pyvenv.cfg")
        assert entry is not None
        self.assertEqual((entry[0], entry[1]), (".venv/", "rebuilt"))

    def test_typescript_installs_only_when_the_lock_is_newer_so_its_manifest_is_in_the_key(self) -> None:
        """e8: `node_modules/.package-lock.json` is a file target — `npm ci` runs when `package.json` or the lock is
        newer than it, not on every run — so what is installed is an input, by the manifest npm wrote."""
        makefile = (self.project("typescript") / "Makefile").read_text(encoding="utf-8")
        # The recipe is `npm ci` bare, or through the Stryker wrapper (S41 T040) where a TypeScript service is present;
        # either way it is the file target keyed by the manifest and the lock.
        target = "node_modules/.package-lock.json: package.json package-lock.json\n\t"
        runs = ("npm ci", "python3 scripts/stryker-mutation.py --install npm ci")
        self.assertTrue(any(target + run + "\n" in makefile for run in runs), makefile)
        self.assertIsNone(self.exempt("node_modules/.package-lock.json"))
        self.assertIsNotNone(self.exempt("node_modules/left-pad/index.js"))

    def test_the_model_tooling_installs_from_its_lock_and_its_manifest_is_in_the_key(self) -> None:
        """e8: `npm --prefix scripts/event-model ci` — from the committed lock; a satisfied tree is left as it is."""
        makefile = (self.project("python", "event-modelling") / "Makefile").read_text(encoding="utf-8")
        self.assertIn("npm --prefix scripts/event-model ci", makefile)
        self.assertNotIn("npm --prefix scripts/event-model install", makefile)
        self.assertIsNone(self.exempt("scripts/event-model/node_modules/.package-lock.json"))
        self.assertIsNotNone(self.exempt("scripts/event-model/node_modules/yaml/index.js"))

    def test_go_and_java_install_nothing_into_the_checkout(self) -> None:
        """e8: modules and wrapper distributions live in the user's cache, outside the checkout, and what the build
        writes beside the code (`target/`, coverage files) is rebuilt by the recipe, not installed — so what is left out
        of the key for them has the reason `rebuilt`, and no backend directory is left out whole."""
        for backend in ("go", "java-quarkus", "java-spring"):
            with self.subTest(backend=backend):
                project = self.project(backend)
                ignored = (project / ".gitignore").read_text(encoding="utf-8")
                self.assertNotIn("vendor/", ignored)
                self.assertNotIn("node_modules/", ignored)
        for path in ("target/classes/A.class", "coverage.out", ".flattened-pom.xml"):
            entry = self.exempt(path)
            assert entry is not None
            self.assertEqual(entry[1], "rebuilt", path)
        for path in ("apps/service/vendor/x.go", "vendor/x.go", "apps/service/src/Main.java"):
            self.assertIsNone(self.exempt(path), path)
