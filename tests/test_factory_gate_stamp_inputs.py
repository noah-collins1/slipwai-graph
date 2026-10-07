"""What the suite reads from the environment and probes on `PATH` is accounted for by the root gate's stamp (S33).

Two class-closing tables, each checked against the tests as they are written: a name a test starts reading, or a tool a
test starts looking for, that is in neither the table nor the gate's own lists fails here, so the stamp cannot go on
reusing a pass over a suite the new input changes. The examples run the root `Makefile` in `GateCase`'s throwaway repo.
"""
from __future__ import annotations

import importlib.util
import os
import re
import shutil
import subprocess
import sys
from functools import partial

from support import backends_under_test
from test_factory_gate_stamp import BYPASS, FULL, GateCase
from test_factory_gate_stamp_scan import probed, reads, unreadable

from slipwai.assets import ROOT

sys.dont_write_bytecode = True

# Every name `tests/*.py` reads from the environment. A name that narrows or redirects what the suite runs
# BYPASSES the stamp (the checks run straight, nothing is read or written), with a value that shows it. The rest
# change nothing the suite runs, with the reason.
BYPASSES = {"TESTS": "test_x", "SKIP": "test_nothing", "FACTORY_BACKENDS": "python"}
UNCHANGING = {
    "PATH": "the tools a run finds are keyed by `--version` answers, and a stand-in PATH is built by the test",
    "SLIPWAI_NO_INSTALL": "`support.py` sets it for its own process; it stops an installer, not a test",
    "SLIPWAI_INDEX": "a registry URL `test_upgrade.py` hands its own child and clears around it; asserted the same",
    "S02_TEST_CI": "a test sets it for its own child, with a CI marker the test itself names",
    "UV_INDEX_SLIPWAI_USERNAME": "a test sets it for its own child; the same tests run with or without it",
    "UV_INDEX_SLIPWAI_PASSWORD": "a test sets it for its own child; the same tests run with or without it",
    "GITHUB_REF_NAME": "only labels the image tag a test builds; every assertion is the same under any label",
    "IMAGE_REGISTRY": "names where the pack image test pushes, a throwaway local one otherwise; the test runs "
                      "and asserts the same, and a wrong registry fails it, never passes it",
    "PACK_FLAGS": "extra flags for the pack build the test runs anyway; the same assertions, and a bad flag fails "
                  "the build",
    "GITEA_OWNER": "`event_model_page_url` reads it; its one test sets it and clears it around the call, and no "
                   "other test asserts the address it makes",
    "GITEA_PAGES_URL": "the same call and the same test, which sets it and clears it around the call",
    "GITEA_TOKEN": "`preflight` reads it, and every `generate` the suite runs passes `--skip-checks`; the one test "
                   "that names it asserts a refusal's wording, not whether one happens",
    "GIT_CEILING_DIRECTORIES": "`test_uncommitted_places.py` sets it for its own process and restores it; it makes "
                               "git blind to what sits above the temporary directory, so the tests behave the same",
    "GITEA_PRIVATE": "`scripts/publish-to-gitea.py` reads it; the one test that runs it passes `--list`, which exits "
                     "before the value is used, and the suite is green with a bad one",
    "GITEA_URL": "the same script's `--url` default; `--list` never contacts a forge, and the suite is green with any",
    "GITEA_USERNAME": "`tag-release.py` hands it to its own child's push; no test pushes, and the suite is green "
                      "with any",
    "PYPI_TOKEN": "`publish-wheel.py` reads it in `main`; `test_versions.py` loads the module for its pure functions "
                  "only, and the suite is green with any",
    **{name: "read by `scripts/gitea-pages.py` at load, which the suite pins out of the process (T030): "
             "`test_gitea_pages_environment.py` runs its tests with an odd value for each"
       for name in ("GITEA_REPOS_DIR", "GITEA_PAGES_ROOT", "GITEA_PAGES_HOST", "GITEA_PAGES_PORT",
                    "GITEA_PAGES_BRANCH", "GITEA_PAGES_POLL_SECONDS")},
    **{name: "what the fake `go` of `test_go_mutation_signal.py` prints and writes; the test sets both around its "
             "own call and restores the environment, so a value from outside never reaches an assertion"
       for name in ("FAKE_SAY", "FAKE_REPORT")},
    "SELECTED_TEST_MODULES": "narrows the reads-only audit, but never under the gate: `make verify` runs `test` "
                             "with `FULL=1`, and the selector removes it from every run it starts and sets it only on "
                             "a selected one (`test_select_tests_audit_narrow`: a full run drops an inherited value); "
                             "the one path that keeps it, `TESTS=`/`SKIP=`, is a bypass already (D187 rule 4, S43)",
    "TMPDIR": "where `tempfile` makes directories; no test's outcome turns on it since T023 (git is given "
              "`GIT_CEILING_DIRECTORIES` where it could see above one)",
}


# Every tool a test looks for, other than the gate's own `VERIFY_TOOLS`: a test skips, or asserts, on whether one is
# there, so a tool that can appear belongs in the key. These do not change what runs, with the reason; `make` is keyed
# by the recipe itself, and `docker compose` through the probe file the recipe writes (D112).
EXEMPT_TOOLS = {
    "sh": "always there, and the key's own runner needs it (D100); `--version` is not asked of it",
    "chmod": "coreutils a stand-in PATH is built from; asserted present, never a reason to skip",
    "dirname": "coreutils a stand-in PATH is built from; asserted present, never a reason to skip",
    "cat": "coreutils a stand-in PATH is built from; asserted present, never a reason to skip",
    "mkdir": "coreutils a stand-in PATH is built from; asserted present, never a reason to skip",
    "touch": "coreutils a stand-in PATH is built from; asserted present, never a reason to skip",
    "rm": "coreutils a stand-in PATH is built from; asserted present, never a reason to skip",
    "mv": "coreutils a stand-in PATH is built from; asserted present, never a reason to skip",
    "mkfifo": "coreutils a stand-in PATH is built from; asserted present, never a reason to skip",
    "echo": "coreutils a stand-in PATH is built from; asserted present, never a reason to skip",
    "sleep": "coreutils a stand-in PATH is built from; asserted present, never a reason to skip",
    "find": "lists the caches under `assets/` into the probe file (D119); a stand-in PATH carries it, never a skip",
    "sort": "orders that list; where it is missing the probe line is unique to the run, so nothing is reused",
    "init": "the generated repository's own `init` script, asserted executable: a file its test lands, not a tool",
    "make": "keyed by the recipe itself: `--tool make --make \"$(MAKE)\"`, under the name it was run as",
}
PROBE_FILE = ".factory-work/verify-probes"
KEYED_THROUGH_THE_PROBE_FILE = {"docker compose"}


# Every site whose name the scanners cannot read as literals, `file: code`, with the reason it is not a gap: the name is
# a parameter whose callers' literals are read at their own call, or the path is a file the test's repository holds.
UNREADABLE = {
    "stamp_fixture.py: os.environ.get(name)": "`variable()` sets one name for one block and restores it; it is the "
                                              "generated gate's own input, held in-process, not what the suite runs",
    "stamp_fixture.py: os.environ.pop(name, None)": "the same helper, restoring",
    "stamp_fixture.py: os.environ[name]": "the same helper, setting",
    "test_cruise_index.py: shutil.which(tool)": "`bare_path`'s parameter: its callers' tools are read as arguments",
    "test_wrappers.py: shutil.which(tool)": "`_on_path`'s parameter: every caller's tool is read as its argument",
    "test_images.py: shutil.which(NEEDS[tool])": "`NEEDS`' values, read where the map is assigned",
    "src/slipwai/preflight.py: shutil.which(probe[0])": "`preflight` is skipped by every `generate` the suite runs "
                                                        "(`--skip-checks`); its tools are `targets.TOOLS`, keyed",
    "src/slipwai/preflight.py: shutil.which(tool)": "the same: a parameter of the skipped `preflight`, read from "
                                                    "`targets.TOOLS`, whose names are listed tools",
    "src/slipwai/preflight.py: os.environ.get(variable)": "the same: the target's region variable, which only the "
                                                         "skipped `preflight` reads",
    "src/slipwai/upgrade.py: os.environ.get(f'{stem}_USERNAME')": "`UV_INDEX_SLIPWAI_USERNAME`, decided above; the "
                                                                 "stem is the one index name `test_upgrade.py` uses",
    "src/slipwai/upgrade.py: os.environ.get(f'{stem}_PASSWORD')": "`UV_INDEX_SLIPWAI_PASSWORD`, decided above",
    "src/slipwai/wrappers.py: shutil.which(tool)": "the tools a recorded command runs; `test_wrappers.py` names them "
                                                   "as literals at its own call, and every one is listed or exempt",
    "scripts/test-adoption.py: shutil.which(tool)": "`verify`'s parameter in a script only `make test-adoption` runs; "
                                                    "the suite never runs it",
    "test_gitea_pages.py: os.environ.pop(name, None)": "`load_daemon` restoring the names its caller handed it",
    "test_gitea_pages.py: os.environ[name]": "`load_daemon` taking its `GITEA_*` names out of the environment for "
                                             "the load, so the shell's value never reaches the script (T030)",
    "test_monorepos.py: os.access(landed, os.X_OK)": "a file the generated repository holds, not a tool",
    "test_parallel_slices.py: os.access(gate, os.X_OK)": "a file the generated repository holds, not a tool",
}


class TestEveryVariableTheSuiteReadsIsAccountedFor(GateCase):
    def test_a_site_the_scanners_cannot_read_is_listed_with_its_reason(self) -> None:  # AC-S33-11 e1
        self.assertEqual(sorted(set(unreadable()) - set(UNREADABLE)), [], "a name the scanner cannot resolve")
        self.assertEqual(sorted(set(UNREADABLE) - set(unreadable())), [], "an entry nothing needs any more")

    def test_a_name_the_tests_read_is_a_bypass_or_has_its_reason_for_not_being_one(self) -> None:  # AC-S33-11 e1
        self.assertEqual(sorted(reads() - set(BYPASSES) - set(UNCHANGING)), [])
        self.assertEqual(set(BYPASSES), set(BYPASS), "the fixture strips exactly the bypasses")
        self.assertFalse(set(BYPASSES) & set(UNCHANGING))

    def test_each_bypass_runs_the_checks_straight_and_leaves_the_stamp_alone(self) -> None:  # AC-S33-11 e2
        self.passes()
        before = self.stamps()
        self.assertTrue(before)
        for name, value in BYPASSES.items():
            # in the environment, then on make's command line
            for how, run in (("environment", partial(self.gate, **{name: value})),
                             ("command line", partial(self.gate, f"{name}={value}"))):
                with self.subTest(name, how=how):
                    done = run()
                    self.assertEqual(done.returncode, 0, done.stderr)
                    self.assertEqual((self.ran(), self.stamps()), (FULL, before))
        done = self.gate()
        self.assertEqual((done.returncode, self.ran()), (0, []))

    def test_a_bypass_writes_no_stamp_and_the_next_plain_run_is_full(self) -> None:  # AC-S33-11 e3
        for name, value in BYPASSES.items():
            with self.subTest(name):
                self.assertEqual(self.gate(**{name: value}).returncode, 0)
                self.assertEqual((self.ran(), self.stamps()), (FULL, {}))
                self.passes()
                self.gate()
                self.ran()
                shutil.rmtree(self.repo / ".git" / "slipwai")



class TestABackendSliceThatNamesNoBackendIsAnError(GateCase):
    def test_a_value_that_is_blank_or_only_commas_is_refused_not_an_empty_matrix(self) -> None:  # T022
        """make's `$(strip ...)` sees these as empty, so the stamped path runs; the suite must not pass over nothing."""
        kept = os.environ.get("FACTORY_BACKENDS")
        try:
            for value in (" ", ",", " , "):
                with self.subTest(value=value):
                    os.environ["FACTORY_BACKENDS"] = value
                    with self.assertRaises(ValueError):
                        backends_under_test()
            os.environ["FACTORY_BACKENDS"] = "python"
            self.assertEqual(backends_under_test(), ["python"])
        finally:
            if kept is None:
                os.environ.pop("FACTORY_BACKENDS", None)
            else:
                os.environ["FACTORY_BACKENDS"] = kept


class TestEveryToolTheSuiteLooksForIsAccountedFor(GateCase):
    def listed(self) -> list[str]:
        words = re.search(r"^VERIFY_TOOLS\s*:?=(.*)$", (self.repo / "Makefile").read_text(encoding="utf-8"), re.M)
        self.assertIsNotNone(words)
        return words.group(1).split() if words else []

    def test_a_tool_the_tests_look_for_is_keyed_exempt_with_its_reason_or_keyed_through_the_probe_file(self) -> None:
        accounted = set(self.listed()) | set(EXEMPT_TOOLS) | KEYED_THROUGH_THE_PROBE_FILE  # AC-S33-12 e1
        self.assertEqual(sorted(probed() - accounted), [])
        text = (self.repo / "Makefile").read_text(encoding="utf-8")
        self.assertIn(PROBE_FILE, text)
        self.assertIn("docker compose version", text)

    def test_the_tools_whose_absence_skips_an_image_or_wrapper_test_are_listed(self) -> None:  # AC-S33-12 e2
        self.assertTrue({"ko", "mvn", "pack", "java", "docker"} <= set(self.listed()))

    def test_every_tool_acceptance_criterion_6_names_is_listed_with_ko_and_mvn(self) -> None:  # AC-S33-6 hold
        named = {"python3", "git", "uv", "node", "npm", "go", "java", "docker", "pack", "tofu", "gh", "ko", "mvn"}
        self.assertEqual(sorted(named - set(self.listed())), [])

    def test_the_plugin_arriving_puts_the_next_run_in_full_and_the_run_after_reuses(self) -> None:  # AC-S33-12 e3
        """A stand-in `docker` answers `--version` the same throughout and fails `compose version` until it is told."""
        docker = self.bin / "docker"
        docker.write_text('#!/bin/sh\ncase "$1" in\n  --version) echo "Docker version 27.0 (stand-in)" ;;\n'
                          '  compose) [ -f "$0.compose" ] && cat "$0.compose" || exit 1 ;;\nesac\n', encoding="utf-8")
        docker.chmod(0o755)
        with (self.repo / ".gitignore").open("a", encoding="utf-8") as ignores:
            ignores.write(".factory-work/\n")  # as the real `.gitignore` does
        self.passes()
        self.assertEqual(self.gate().returncode, 0)
        self.assertEqual(self.ran(), [])
        (self.bin / "docker.compose").write_text("Docker Compose version v2.29.0\n", encoding="utf-8")
        self.passes()
        self.assertEqual(self.gate().returncode, 0)
        self.assertEqual(self.ran(), [])

    def test_the_real_tree_ignores_the_probe_file_and_the_key_does_not_exempt_it(self) -> None:  # AC-S33-12 e3
        ignored = subprocess.run(["git", "check-ignore", PROBE_FILE], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(ignored.returncode, 0, "the real `.gitignore` ignores the probe file")
        spec = importlib.util.spec_from_file_location("verify_stamp", ROOT / "assets/toolkit/scripts/verify-stamp.py")
        assert spec is not None and spec.loader is not None
        stamp = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(stamp)
        self.assertIsNone(stamp.exempt_entry(PROBE_FILE), "an ignored file, but one the key reads by its bytes")

    def test_a_slice_of_the_suite_writes_no_probe_file(self) -> None:  # AC-S33-12 e4
        self.assertEqual(self.gate("TESTS=test_x").returncode, 0)
        self.assertFalse((self.repo / PROBE_FILE).exists())


class TestCachesThatCannotBeListedAreNeverReused(GateCase):
    def test_a_path_without_sort_never_reuses(self) -> None:  # AC-S33-13 hold (D119)
        """Where the caches under `assets/` cannot be listed, the probe line is unique to the run: no reuse."""
        bare = self.bin.parent / "bare"
        bare.mkdir()
        for name in ("make", "git", "python3", "sh", "mkdir", "echo", "find"):
            (bare / name).symlink_to(shutil.which(name) or name)
        for _ in range(2):
            done = self.gate(path=str(bare))
            self.assertEqual((done.returncode, self.ran()), (0, FULL), done.stdout + done.stderr)


class TestAListedToolLeavingPutsTheNextRunInFull(GateCase):
    def test_a_stand_in_tool_removed_from_a_path_that_holds_none_other_is_a_full_run(self) -> None:  # AC-S33-6 hold
        """The `PATH` is built here so `tofu` is certainly absent after, whatever the host has installed."""
        bare = self.bin.parent / "bare"
        bare.mkdir()
        for name in ("make", "git", "python3", "sh", "mkdir", "echo", "find", "sort"):
            (bare / name).symlink_to(shutil.which(name) or name)
        path = str(bare)
        tofu = self.bin / "tofu"
        tofu.write_text('#!/bin/sh\necho "OpenTofu v1.8.0"\n', encoding="utf-8")
        tofu.chmod(0o755)
        done = self.gate(path=path)
        self.assertEqual((done.returncode, self.ran()), (0, FULL), done.stdout + done.stderr)
        self.assertEqual((self.gate(path=path).returncode, self.ran()), (0, []))
        tofu.unlink()
        self.assertIsNone(shutil.which("tofu", path=f"{self.bin}{os.pathsep}{path}"))
        done = self.gate(path=path)
        self.assertEqual((done.returncode, self.ran()), (0, FULL), done.stdout)
        self.assertNotIn("not found", done.stderr, "the probe line is silent where there is no `docker`")
        self.assertEqual((self.gate(path=path).returncode, self.ran()), (0, []))


class TestTheRootRecipeUnderMakesOwnFlags(GateCase):
    """The recipe's exit handling is its own, not the generated one's: each flag below is a hold (AC-S33-10)."""

    def test_i_with_a_failing_check_exits_0_writes_no_stamp_and_the_next_run_is_full(self) -> None:
        done = self.gate("-i", STANDIN_FAIL="test")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(self.ran(), FULL)
        self.assertEqual([n for n in self.stamps() if n.endswith(".json")], [])
        self.passes()

    def test_n_starts_no_check_and_leaves_every_stamp_byte_alone(self) -> None:
        self.passes()
        before = self.stamps()
        self.append("src/mod.py")
        for tree in ("changed", "unchanged"):
            with self.subTest(tree):
                self.assertEqual(self.gate("-n").returncode, 0)
                self.assertEqual((self.ran(), self.stamps()), ([], before))
                if tree == "changed":
                    (self.repo / "src/mod.py").write_text("X = 1\n", encoding="utf-8")

    def test_q_exits_1_and_says_nothing_on_a_tree_that_needs_the_checks(self) -> None:
        for tree in ("fresh", "changed"):
            with self.subTest(tree):
                before = self.stamps()
                done = self.gate("-q")
                self.assertEqual((done.returncode, done.stdout, done.stderr, self.ran()), (1, "", "", []))
                self.assertEqual(self.stamps(), before)
                if tree == "fresh":
                    self.passes()
                    self.append("src/mod.py")

    def test_k_with_a_failing_check_exits_2_names_the_failure_and_writes_no_stamp(self) -> None:
        done = self.gate("-k", STANDIN_FAIL="check-structure")
        self.assertEqual(done.returncode, 2, done.stderr)
        self.assertIn("did not pass", done.stdout + done.stderr)
        self.assertIn("check-structure", done.stdout + done.stderr)
        self.assertEqual([n for n in self.stamps() if n.endswith(".json")], [])
        self.ran()
        self.passes()
