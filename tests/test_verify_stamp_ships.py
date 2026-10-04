"""What ships: every project the factory generates, wrapped applications aside, takes the stamped `verify`.

R12 (AC-S03-29): the gate is the gate it was — the prerequisites of `verify-checks` are the ones `verify` had, in the
same order, with the same closing line, for every backend the catalog offers, with a transport and without, with a
browser app, and with several services (one gate, one `--environment` per Python service); `./init --http none` cuts
the transport's line and leaves no `check-openapi`. The starter matrix's own gates are the host's full gate; here the
Makefile each starter gets is held against what the gate ran before.

R13 (AC-S03-25, -30, -31): the page a generated project has about its gate says what the stamp does, and every
sentence of it is followed as written on the fixture project with the stand-in tools; the fragment claims MINOR and
asks nothing of an existing project; and a project generated before the stamp is brought it by `slipwai migrate`.
"""
from __future__ import annotations

import re
import subprocess
import tempfile

from stamp_fixture import CLOSING as PASSED
from stamp_fixture import StampTestCase, git
from support import FactoryTestCase
from test_add_service import add_service
from test_migrate import migrate
from test_replay import newer_factory
from test_verify_stamp_pinned import CLOSING, STANDARD, gate_prerequisites, gate_rule

from slipwai.assets import ROOT
from slipwai.catalog import CATALOG

TOOLS = {
    "typescript": ["make", "git", "python3", "node", "npm"],
    "python": ["make", "git", "python3", "uv"],
    "go": ["make", "git", "python3", "go"],
    "java-quarkus": ["make", "git", "python3", "java"],
    "java-spring": ["make", "git", "python3", "java"],
}


UNSEEN = ("the clock", "the network", "user-level tool configuration", "`PATH`", "a variable no gate script names")
SEES_NOT = (
    "A stamp cannot see what a project's own tests or tools read from outside the repository: the clock, the network, "
    "user-level tool configuration, `PATH`, or a variable no gate script names."
)
REUSED_AS_GREEN = (
    "A gate that would now fail for one of those alone is reused as green until a file, a ref or a listed input moves "
    "or `VERIFY_FORCE` is given."
)
CAUGHT_IN_CI = "CI and the trunk, which never read a stamp, are where it is caught."


def stamp_variable(makefile: str) -> list[str]:
    match = re.search(r"^VERIFY_STAMP := (.*)$", makefile, re.M)
    assert match, "no VERIFY_STAMP in the Makefile"
    return match.group(1).split()


def tools_asked(makefile: str) -> list[str]:
    words = stamp_variable(makefile)
    return [words[i + 1] for i, word in enumerate(words) if word == "--tool"]


def environments_asked(makefile: str) -> list[str]:
    words = stamp_variable(makefile)
    return [words[i + 1] for i, word in enumerate(words) if word == "--environment"]


class EveryStarterTakesTheStampedGateTest(FactoryTestCase):
    def assert_stamped_gate(self, makefile: str, expected: list[str]) -> None:
        self.assertEqual(len(re.findall(r"^verify:", makefile, re.M)), 1, "one rule named verify")
        self.assertEqual(len(re.findall(r"^verify-checks:(?!.*check-openapi)", makefile, re.M)), 1)
        self.assertIn("verify-stamp.py reuse", makefile)
        self.assertEqual(gate_prerequisites(makefile), expected)
        self.assertTrue(gate_rule(makefile).endswith(CLOSING), gate_rule(makefile))

    def test_every_backend_the_catalog_offers_keeps_its_prerequisites_with_and_without_a_transport(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            for backend in CATALOG["backends"]:
                for http in (None, "none"):
                    with self.subTest(backend=backend, http=http):
                        axes = {} if http is None else {"http": http}
                        repo = self.generate(directory, f"{backend}-{http or 'with'}", "standard", backend, **axes)
                        makefile = (repo / "Makefile").read_text()
                        # Only the backends that can write a document out of the app itself have a line to cut.
                        transport = http is None and backend in ("typescript", "python")
                        self.assert_stamped_gate(makefile, STANDARD + (["check-openapi"] if transport else []))
                        if transport:
                            self.assertRegex(
                                makefile,
                                r"# backing-service:[a-z-]+:begin\nverify-checks: check-openapi\n"
                                r"# backing-service:[a-z-]+:end\n",
                            )
                        else:
                            self.assertNotRegex(makefile, r"(?m)^verify(-checks)?: check-openapi")
                        self.assertEqual(tools_asked(makefile), TOOLS[backend])
                        expected_environments = ["apps/service/.venv"] if backend == "python" else []
                        self.assertEqual(environments_asked(makefile), expected_environments)

    def test_a_project_with_a_browser_app_asks_the_machine_for_node_and_keeps_its_style_gate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "web", "standard", "python", "react-vite", http="none")
            makefile = (repo / "Makefile").read_text()
            self.assert_stamped_gate(makefile, STANDARD + ["check-styles"])
            self.assertEqual(tools_asked(makefile), ["make", "git", "python3", "uv", "node", "npm"])

    def test_init_answering_the_transport_with_none_leaves_no_document_check_anywhere(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "cut", "event-modelling", "typescript", http="fastify")
            self.assertIn("check-openapi", (repo / "Makefile").read_text())
            subprocess.run(["python3", "scripts/backing-services.py", "--http", "none"], cwd=repo, check=True,
                           stdout=subprocess.DEVNULL)
            makefile = (repo / "Makefile").read_text()
            self.assertNotIn("check-openapi", gate_prerequisites(makefile))
            self.assertNotRegex(makefile, r"(?m)^verify(-checks)?: check-openapi")
            self.assertIn("verify-stamp.py reuse", makefile)
            self.assertTrue(gate_rule(makefile).endswith(CLOSING))

    def test_several_services_are_one_gate_with_one_environment_each(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            for flags, environments, tools in (
                ((), ["apps/service/.venv", "apps/payments/.venv"], TOOLS["python"]),
                (("--language", "go"), ["apps/service/.venv"], TOOLS["python"] + ["go"]),
            ):
                with self.subTest(added=flags):
                    repo = self.generate(directory, f"grown{len(flags)}", "standard", "python", http="none")
                    result = add_service(repo, "payments", *flags)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    makefile = (repo / "Makefile").read_text()
                    self.assert_stamped_gate(makefile, STANDARD)
                    self.assertEqual(environments_asked(makefile), environments)
                    self.assertEqual(tools_asked(makefile), tools)


FORCING = "`make verify VERIFY_FORCE=1`"


class ThePageSaysWhatTheStampDoesTest(StampTestCase):
    """e25: the page's sentences, followed as written."""

    def page(self) -> str:
        return " ".join((self.repo / "docs/gates.md").read_text(encoding="utf-8").split())

    def test_the_page_names_the_variable_its_default_and_the_one_sentence_that_runs_the_gate_anyway(self) -> None:
        page = self.page()
        self.assertIn("A tree that already passed `make verify` is not judged again", page)
        self.assertIn("`VERIFY_FORCE` is unset by default", page)
        self.assertIn(f"To run the gate anyway, run {FORCING}", page)
        self.assertIn("anything but empty or `0` forces it, on the command line or in the environment", page)

    def test_following_the_page_the_second_run_says_so_and_the_forced_run_runs_every_check(self) -> None:
        self.assertEqual(self.run_gate().returncode, 0)
        self.assertTrue(self.checks(), "the first run is a full one")
        stamp = self.stamp_path()
        self.assertIsNotNone(stamp)
        # "nothing of it in the working tree": git status sees nothing, ignored files included
        self.assertNotIn("slipwai", git(self.repo, "status", "--porcelain", "--ignored"))
        self.forget_log()
        again = self.run_gate()
        self.assertEqual(self.checks(), [], "the second run on the same tree starts no check")
        self.assertIn("this tree already passed it", again.stdout)
        self.assertIn("VERIFY_FORCE=1 runs it anyway", again.stdout)
        self.assertNotIn(PASSED, again.stdout)
        self.forget_log()
        forced = self.run_gate(args=["VERIFY_FORCE=1"])
        self.assertTrue(self.checks(), "the page's sentence runs every check")
        self.assertIn(PASSED, forced.stdout)

    def test_the_page_names_what_a_stamp_cannot_see_and_where_it_is_never_used(self) -> None:
        page = self.page()
        never_read = (
            "The trunk and CI (`CI`, `GITHUB_ACTIONS` or `GITLAB_CI` set) always run the full gate and neither "
            "read nor write a stamp, and `make ci` always runs it."
        )
        for sentence in (SEES_NOT, REUSED_AS_GREEN, CAUGHT_IN_CI, never_read):
            self.assertIn(sentence, page)

    def test_the_fragment_says_the_same_list_and_the_consequence_in_its_own_words(self) -> None:
        fragment = " ".join((ROOT / "changelog.d/verify-stamp.md").read_text(encoding="utf-8").split())
        for thing in UNSEEN:
            self.assertIn(thing, fragment)
        self.assertIn("is reused as green until a file, a ref or a listed input moves or `VERIFY_FORCE` is given",
                      fragment)
        self.assertIn("CI and the trunk", fragment)
        self.assertNotIn("a tool a recipe fetches", fragment)

    def test_the_tutorial_says_the_same_in_its_own_words(self) -> None:
        tutorial = " ".join((ROOT / "docs/learn-generate.md").read_text(encoding="utf-8").split())
        self.assertIn("`make verify VERIFY_FORCE=1` runs the gate anyway", tutorial)
        self.assertIn("verify: the full gate did not run; this tree already passed it …", tutorial)
        self.assertIn("The trunk, CI and `make ci` always run the full gate", tutorial)
        run = self.run_gate()
        self.assertEqual(run.returncode, 0)
        self.assertIn("verify: the full gate did not run; this tree already passed it", self.run_gate().stdout)

    def test_following_the_page_ci_and_make_ci_run_the_full_gate_on_a_tree_that_passed(self) -> None:
        self.assertEqual(self.run_gate().returncode, 0)
        self.forget_log()
        self.run_gate({"CI": "true"})
        self.assertTrue(self.checks(), "CI ran no check on a tree that passed")
        self.forget_log()
        run = subprocess.run(["make", "ci"], cwd=self.repo, env=self.environment(), text=True,
                             capture_output=True, timeout=180)
        self.assertTrue(self.checks(), f"make ci started no check: {run.stdout[-300:]}")

    def test_following_the_page_the_trunk_runs_the_full_gate_every_time_and_leaves_no_stamp(self) -> None:
        git(self.repo, "checkout", "-q", "main")
        for _ in range(2):
            self.forget_log()
            self.assertEqual(self.run_gate().returncode, 0)
            self.assertTrue(self.checks(), "the trunk ran no check")
        self.assertIsNone(self.stamp_path())


class TheFragmentTest(FactoryTestCase):
    """e31: the fragment's level, its catch-up sentence, and the number `main` carries."""

    def test_the_fragment_claims_minor_and_asks_nothing_of_an_existing_project(self) -> None:
        raw = (ROOT / "changelog.d/verify-stamp.md").read_text(encoding="utf-8")
        text = " ".join(raw.split())
        self.assertEqual(raw.splitlines()[0], "MINOR")
        self.assertIn("**Catch-up.** Nothing is asked of a repository already generated", text)
        self.assertIn("`slipwai migrate` brings the new `Makefile` and `scripts/verify-stamp.py`", text)
        self.assertIn("the first `make verify` runs in full", text)
        self.assertIn("`.gitignore` is not touched", text)
        # a hold: the arithmetic `test_changelog` checks, seen here as the number the claim is made against
        self.assertEqual((ROOT / "VERSION").read_text(encoding="utf-8").strip(), "1.6.0.dev0")


class AMigratedProjectIsBroughtTheStampTest(StampTestCase):
    """e30: a project generated before the stamp, migrated, has the new `Makefile` and script, the same `.gitignore`,
    and a first run that is full and writes a stamp."""

    def make_it_old(self) -> str:
        """The fixture as the factory made it before the stamp: the old `verify` rule, no script. Amended into the
        scaffold commit, which stays the factory's, so it is the base `migrate` measures from."""
        makefile = (self.repo / "Makefile").read_text(encoding="utf-8")
        rule = re.search(r"^VERIFY_STAMP := .*?^verify-checks: ([^\n]*)\n", makefile, re.M | re.S)
        assert rule is not None
        old = f"verify: {rule.group(1)} ## Full deterministic pre-commit gate\n"
        (self.repo / "Makefile").write_text(makefile.replace(rule.group(0), old), encoding="utf-8")
        (self.repo / "scripts/verify-stamp.py").unlink()
        git(self.repo, "add", "-A")
        git(self.repo, "-c", "maintenance.auto=false", "commit", "-q", "--amend", "--no-edit")
        return (self.repo / ".gitignore").read_text(encoding="utf-8")

    def test_migrate_brings_the_makefile_and_the_script_and_the_first_run_is_full(self) -> None:
        ignore = self.make_it_old()
        self.assertNotIn("verify-checks", (self.repo / "Makefile").read_text(encoding="utf-8"))
        factory = newer_factory(self.repo.parent, "\n## A section a newer factory added\n")
        result = migrate(self.repo, factory)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((self.repo / "scripts/verify-stamp.py").is_file())
        self.assertIn("verify-stamp.py reuse", (self.repo / "Makefile").read_text(encoding="utf-8"))
        self.assertEqual((self.repo / ".gitignore").read_text(encoding="utf-8"), ignore)
        self.assertIsNone(self.stamp_path(), "nothing was passed yet")
        run = self.run_gate()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertTrue(self.checks(), "the first run after a migration is full")
        self.assertIn(PASSED, run.stdout)
        self.assertEqual(self.stamp()["result"], "pass")
