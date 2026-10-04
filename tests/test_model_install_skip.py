"""R7 (AC-S04-48, -49, -51, -52, -55): a matching tree is not reinstalled, and a fresh one installs once.

Swept over the four model targets and the Python, Go and TypeScript starters where an example is about every
project with the event profile. Evidence is the log a stand-in `npm` and `node` append to, never a printed line —
except for the skip line, which is the thing under test.
"""
from __future__ import annotations

import itertools
import os
import sys

from parallel_gate import log_lines, run_make
from test_model_install import CI, MARKER, SKIP, TARGETS, ModelCase

sys.dont_write_bytecode = True

LANGUAGES = ("python", "go", "typescript")
MANIFESTS = ("scripts/event-model/package.json", "scripts/event-model/package-lock.json")


class SkipCase(ModelCase):
    def installed(self) -> None:
        """A tree an earlier gate installed: run the first target once, then forget what that logged."""
        self.assert_passed(self.make("check-drawio"))
        self.forget_log()

    def touch_ahead(self, path: str) -> None:
        marker = self.repo / MARKER
        later = marker.stat().st_mtime + 10
        os.utime(self.repo / path, (later, later))


class SkipTest(SkipCase):
    def test_e4_an_installed_tree_newer_than_both_manifests_is_not_reinstalled_and_check_drawio_says_so(self) -> None:
        """AC-S04-48 and -55, over every starter."""
        for language in LANGUAGES:
            with self.subTest(language=language):
                self.LANGUAGE = language
                self.setUp()
                self.installed()
                done = self.make("check-drawio")
                self.assert_passed(done)
                self.assertEqual(self.npm_calls(), [])
                self.assertEqual(done.stdout.splitlines().count(SKIP), 1, done.stdout)

    def test_e5_touching_either_manifest_installs_again_and_says_no_skip_line(self) -> None:
        """AC-S04-49, over every starter, both manifests and all four targets."""
        for language, manifest, target in itertools.product(LANGUAGES, MANIFESTS, TARGETS):
            with self.subTest(language=language, manifest=manifest, target=target):
                self.LANGUAGE = language
                self.setUp()
                self.installed()
                self.touch_ahead(manifest)
                done = self.make(target)
                self.assert_passed(done)
                self.assertEqual(self.npm_calls(), [CI])
                self.assertNotIn("not reinstalled", done.stdout)

    def test_e7_the_other_three_targets_install_nothing_on_a_matching_tree_and_say_nothing(self) -> None:
        """AC-S04-51, over every starter."""
        for language in LANGUAGES:
            for target in TARGETS[1:]:
                with self.subTest(language=language, target=target):
                    self.LANGUAGE = language
                    self.setUp()
                    self.installed()
                    done = self.make(target)
                    self.assert_passed(done)
                    self.assertEqual(self.npm_calls(), [])
                    self.assertNotIn("not reinstalled", done.stdout)

    def test_e7_every_target_installs_on_a_fresh_clone_with_one_ci_and_no_skip_line(self) -> None:
        """AC-S04-47, -51: the install is the same one whichever target is first."""
        for target in TARGETS:
            with self.subTest(target=target):
                self.setUp()
                done = self.make(target)
                self.assert_passed(done)
                self.assertEqual(self.npm_calls(), [CI])
                self.assertNotIn("not reinstalled", done.stdout)


class MarkerDatedTest(SkipCase):
    def test_e12_the_marker_is_newer_than_both_manifests_after_an_install_that_wrote_it_old(self) -> None:
        """D91 part 2: the recipe dates the marker itself, so the next run sees a tree that matches."""
        self.assert_passed(self.make("check-drawio", env={"STANDIN_NPM_STALE": "1"}))
        marker = (self.repo / MARKER).stat().st_mtime
        for manifest in MANIFESTS:
            self.assertGreaterEqual(marker, (self.repo / manifest).stat().st_mtime, manifest)
        self.forget_log()
        self.assert_passed(self.make("check-drawio", env={"STANDIN_NPM_STALE": "1"}))
        self.assertEqual(self.npm_calls(), [])


class ParallelTest(SkipCase):
    def test_e8_two_targets_in_parallel_on_a_fresh_clone_install_once_before_either_starts(self) -> None:
        """AC-S04-52: the stand-in `npm` holds, bounded, for a second call or a `node`; `met` would show either."""
        env = self.environment({"STANDIN_NPM_HOLD": "1"})
        done = run_make(self.repo, env, "-j", "check-drawio", "model-drawio-test")
        self.assert_passed(done)
        self.assertEqual(self.npm_calls(), [CI])
        self.assertEqual(self.events("npm-met"), [])
        names = [event for event, _ in log_lines(self.log)]
        self.assertEqual(names.count("node-start"), 2, names)
        self.assertLess(names.index("npm-end"), names.index("node-start"))
        self.assertNotIn("not reinstalled", done.stdout)

    def test_e8_the_skip_line_is_said_under_j_once_the_tree_is_installed(self) -> None:
        """AC-S04-55: the line is decided inside the one make invocation, parallel or not."""
        self.installed()
        done = run_make(self.repo, self.environment(), "-j", "check-drawio", "model-drawio-test")
        self.assert_passed(done)
        self.assertEqual(self.npm_calls(), [])
        self.assertEqual(done.stdout.splitlines().count(SKIP), 1, done.stdout)
