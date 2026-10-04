"""R8 (AC-S04-56 to -63, -21, -64 to -66): the slice reaches a project that exists, and the words are true.

A project "made before the slice" is this checkout's project with the model tooling's lock taken out of its one
commit (the root commit is amended, so it is the base `migrate` measures from), as `test_ci_fetch_migrate` puts a
workflow back. The three cases of the lock are each followed as the fragment's catch-up words them: no lock, an
untracked one, one the project committed. The page and the fragment are read; the CI workflow and the ladder's
commands are held to `make verify`.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from support import FactoryTestCase, commit_all
from test_migrate import migrate
from test_replay import git, newer_factory

from slipwai.assets import ROOT
from slipwai.catch_up import OWED
from slipwai.layout import Layout
from slipwai.project.gate import FAILED
from slipwai.scaffold import NO_MAINTENANCE, project_files
from slipwai.selection import Selection
from slipwai.services import default_apps

LOCK = "scripts/event-model/package-lock.json"
FRAGMENT = ROOT / "changelog.d/parallel-gate.md"
SHIPPED = (ROOT / "assets/toolkit" / LOCK).read_bytes()
LANGUAGES = ("typescript", "python", "go")
CHANGE = "\n## A section a newer factory added\n"


def made_before_the_slice(repo: Path) -> None:
    """The project as an earlier factory made it: no lock under `scripts/event-model/`, in the root commit."""
    git(repo, "rm", "-q", LOCK)
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@local", *NO_MAINTENANCE,
                    "commit", "-q", "--amend", "--no-edit"], cwd=repo, check=True)
    assert git(repo, "rev-list", "--count", "HEAD").stdout.strip() == "1"
    assert not (repo / LOCK).exists()


def catch_up() -> str:
    found = OWED.search(FRAGMENT.read_text(encoding="utf-8"))
    assert found is not None, "the fragment has a Catch-up paragraph"
    return " ".join(found.group(1).split())


def squashed(text: str) -> str:
    return " ".join(text.split())


class AProjectMadeBeforeTheSliceMigratesTest(FactoryTestCase):
    def old_project(self, directory: str, language: str) -> tuple[Path, Path]:
        repo = self.generate(directory, f"old-{language}", "event-modelling", language)
        made_before_the_slice(repo)
        return repo, newer_factory(Path(directory) / language, CHANGE)

    def test_a_clean_project_gains_the_lock_and_is_asked_nothing_else(self) -> None:
        """e1. Hold-like: the shipped tree has the lock, so the removed one comes back through the merge."""
        for language in LANGUAGES:
            with self.subTest(language), tempfile.TemporaryDirectory() as directory:
                repo, factory = self.old_project(directory, language)
                result = migrate(repo, factory)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertTrue((repo / LOCK).is_file(), "the merge brought the lock back")
                self.assertEqual((repo / LOCK).read_bytes(), SHIPPED)
                self.assertEqual(git(repo, "status", "--porcelain").stdout, "")
                self.assertNotIn("conflict", result.stdout)
                self.assertEqual(git(repo, "ls-files", LOCK).stdout.strip(), LOCK, "the lock is tracked")

    def test_its_check_drawio_passes_on_the_lock_the_merge_brought(self) -> None:
        """e1, with the real npm, as `test_drawio_canvas` runs it; where there is none the example cannot run."""
        if shutil.which("npm") is None:
            self.skipTest("npm is not installed here; check-drawio installs the model tooling from the lock")
        with tempfile.TemporaryDirectory() as directory:
            repo, factory = self.old_project(directory, "typescript")
            self.assertEqual(migrate(repo, factory).returncode, 0)
            run = subprocess.run(["make", "check-drawio"], cwd=repo, text=True, capture_output=True, timeout=180)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertEqual(git(repo, "status", "--porcelain").stdout, "", "the install wrote nothing to the tree")

    def test_hold_an_untracked_lock_is_refused_as_any_uncommitted_change_is_and_left_as_it_was(self) -> None:
        """e2. A hold on `migrate.py`'s refusal; deleting the file, as the catch-up says, is the way through."""
        for language in LANGUAGES:
            with self.subTest(language), tempfile.TemporaryDirectory() as directory:
                repo, factory = self.old_project(directory, language)
                (repo / LOCK).write_text('{"from": "an earlier gate run"}\n', encoding="utf-8")
                before = git(repo, "rev-parse", "HEAD").stdout

                refused = migrate(repo, factory)

                self.assertNotEqual(refused.returncode, 0)
                self.assertIn("uncommitted changes", refused.stderr)
                self.assertEqual((repo / LOCK).read_text(encoding="utf-8"), '{"from": "an earlier gate run"}\n')
                self.assertEqual(git(repo, "rev-parse", "HEAD").stdout, before)
                self.assertFalse((repo / ".git/MERGE_HEAD").exists())
                (repo / LOCK).unlink()
                self.assertEqual(migrate(repo, factory).returncode, 0)
                self.assertEqual((repo / LOCK).read_bytes(), SHIPPED)

    def test_hold_a_lock_the_project_committed_stops_the_merge_on_that_file_and_the_catch_up_gets_through(self) -> None:
        """e3. Hold: both sides added the file, so git stops on it. The catch-up's own commands finish the merge."""
        for language in LANGUAGES:
            with self.subTest(language), tempfile.TemporaryDirectory() as directory:
                repo, factory = self.old_project(directory, language)
                (repo / LOCK).write_text('{"lockfileVersion": 3, "own": true}\n', encoding="utf-8")
                commit_all(repo, "The project's own lock")
                own = git(repo, "rev-parse", "HEAD").stdout.strip()

                result = migrate(repo, factory)

                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn(f"\n  {LOCK}\n", result.stdout)
                self.assertEqual(git(repo, "diff", "--name-only", "--diff-filter=U").stdout.split(), [LOCK])
                self.assertTrue((repo / ".git/MERGE_HEAD").is_file())
                git(repo, "checkout", "--theirs", LOCK)
                git(repo, "add", LOCK)
                git(repo, "-c", "user.name=t", "-c", "user.email=t@local", "commit", "-q", "--no-edit")
                self.assertEqual((repo / LOCK).read_bytes(), SHIPPED)
                self.assertEqual(git(repo, "status", "--porcelain").stdout, "")
                self.assertEqual(git(repo, "rev-parse", "HEAD^1").stdout.strip(), own)

    def test_hold_a_committed_lock_equal_to_the_shipped_one_raises_no_conflict(self) -> None:
        """e3's teeth: with the two locks equal the merge does not stop."""
        with tempfile.TemporaryDirectory() as directory:
            repo, factory = self.old_project(directory, "typescript")
            (repo / LOCK).write_bytes(SHIPPED)
            commit_all(repo, "The project's own lock, the same")
            self.assertEqual(migrate(repo, factory).returncode, 0)


class TheFragmentIsTrueAndStandsAloneTest(FactoryTestCase):
    def test_it_claims_minor_on_its_first_line(self) -> None:
        self.assertEqual(FRAGMENT.read_text(encoding="utf-8").splitlines()[0], "MINOR")

    def test_the_catch_up_names_the_three_cases_and_what_each_does(self) -> None:
        text = catch_up()
        for needed in (
            LOCK,
            "slipwai migrate",
            "no lock",
            "untracked",
            "delete that file, then run `slipwai migrate`",
            "committed a lock of its own",
            f"git checkout --theirs {LOCK}",
            "npm install --package-lock-only",
            "scripts/event-model",
        ):
            self.assertIn(needed, text)

    def test_the_catch_up_stands_alone_and_says_what_an_edited_manifest_and_an_adopted_gate_now_need(self) -> None:
        text = catch_up()
        self.assertTrue(text.startswith("The model tooling's lockfile"), "it names its subject first")
        self.assertIn("model tooling", text)
        self.assertIn("lock that agrees with it", text)
        self.assertIn("package.json", text)
        self.assertRegex(text, r"experimental")
        self.assertIn("adopted", text)
        self.assertIn("serially whatever `-j` says", text)
        self.assertIn("`make -f delivery/Makefile -j verify`", text)
        self.assertIn("keeps `-j` for its own targets", text)
        self.assertIn("`make -j verify` typed at such a root is not promised", text)
        self.assertNotIn("above", text, "a paragraph copied into a note cannot point at the body above it")
        self.assertEqual(len(OWED.findall(FRAGMENT.read_text(encoding="utf-8"))), 1, "one paragraph")

    def test_the_body_says_make_install_installs_the_model_tooling_and_that_the_catch_up_asks_nothing_more_for_it(
        self,
    ) -> None:
        body = squashed(OWED.sub("", FRAGMENT.read_text(encoding="utf-8")))
        self.assertIn("make install", body)
        self.assertIn("also installs the model tooling from its committed lock", body)
        self.assertNotIn("First draft", body)
        self.assertNotIn("when that part lands", body)

    def test_the_body_says_which_toolchains_ran_and_leaves_out_the_measurement_the_demo_writes(self) -> None:
        body = squashed(OWED.sub("", FRAGMENT.read_text(encoding="utf-8")))
        for family in ("Go", "TypeScript", "Java (Quarkus)", "Python", "Spring", "GNU Make 3.81"):
            self.assertIn(family, body)
        self.assertNotRegex(body, r"\d+(\.\d+)? ?s\b", "no measured number: the host writes them after the demo")


class TheGatesPageIsTrueTest(FactoryTestCase):
    def pages(self) -> tuple[str, str]:
        apps = default_apps("typescript", "none", Selection({"http": "fastify"}))
        root = project_files("same", "event-modelling", "none", apps, Layout("."))["docs/gates.md"]
        moved = project_files("same", "event-modelling", "none", apps, Layout("delivery"))["delivery/docs/gates.md"]
        return squashed(root), squashed(moved)

    def test_a_stamped_projects_page_says_what_parallel_gives_and_does_not_promise(self) -> None:
        page, _ = self.pages()
        for said in (
            "`make -j verify` runs the gate's checks at once, from GNU Make 3.81 on",
            "use it when you wait on the gate locally",
            "Each check's output appears when that check finishes",
            "on a make older than 4.0 lines may interleave",
            "the order of the lines is not promised",
            "`verify` as the only goal",
            "`make -j ci` is not promised",
            "An adopted repository's gate runs serially whatever `-j` says when make is started on its Makefile, "
            "`make -f delivery/Makefile -j verify`",
            "keeps `-j` for its own targets, and `make -j verify` typed there is not promised",
            "A recorded command that itself calls `make` is that application's own",
        ):
            self.assertIn(said, page)

    def test_the_sentence_a_failed_run_ends_on_is_the_codes_own_and_the_page_quotes_it(self) -> None:
        page, _ = self.pages()
        self.assertIn(FAILED, page)

    def test_it_says_in_one_sentence_what_an_install_during_the_run_does_to_the_record(self) -> None:
        page, _ = self.pages()
        self.assertIn("A passing run that installed dependencies as it went is not recorded, the next run on the "
                      "unchanged tree is, and `make install` beforehand makes the first one count.", page)

    def test_hold_a_moved_layouts_page_claims_nothing_of_parallel_because_its_gate_is_serial(self) -> None:
        _, moved = self.pages()
        for word in ("-j", "interleave", "installed dependencies as it went"):
            self.assertNotIn(word, moved)

    def test_hold_the_ci_workflow_and_the_ladders_commands_type_make_verify_and_never_a_job_count(self) -> None:
        jobs = re.compile(r"\bmake\b[^\n`]*\s(?:-j\d*|--jobs)\b")
        for backend in ("typescript", "python", "go", "java-quarkus", "java-spring"):
            apps = default_apps(backend, "none", Selection({"http": "fastify"} if backend == "typescript" else {}))
            files = project_files("same", "event-modelling", "none", apps, Layout("."))
            workflow = files[".github/workflows/verify.yml"]
            self.assertIn("      - run: make verify\n", workflow, backend)
            for path, text in files.items():
                if path.startswith((".github/", "commands/", "agents/", "skills/", ".claude/")):
                    self.assertIsNone(jobs.search(text), f"{backend}: {path} types a job count")
