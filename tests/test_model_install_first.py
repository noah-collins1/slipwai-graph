"""R7 (AC-S04-54, -64; D93): what the first passing gate of a fresh clone records, with real `npm` and `node`.

After `make install` the first `make verify` runs no npm for the model tooling and is recorded; with nothing installed
the first pass installs, is not recorded and says the stamp's line, the second is a full run that is recorded, and the
third reuses it. The Python environment exists in both, as a developer's does: what differs is the model tooling.
Skipped, with its reason, where `npm`, `node` or the registry is absent.
"""
from __future__ import annotations

import shutil
import subprocess
import sys

from stamp_fixture import BRANCH, CLOSING, REUSE_PREFIX, git
from test_model_install import PREFIX, ModelCase

sys.dont_write_bytecode = True

NOT_RECORDED = "this pass was not recorded — a file git ignores changed while the checks ran"


class FirstGateTest(ModelCase):
    VENV = True

    def setUp(self) -> None:
        super().setUp()
        for tool in ("npm", "node"):
            if shutil.which(tool) is None:
                self.skipTest(f"{tool} is not installed here")
        for tool in ("npm", "node"):
            (self.bin / tool).unlink()
        ping = subprocess.run(["npm", "ping", "--registry", "https://registry.npmjs.org/"], capture_output=True,
                              timeout=60)
        if ping.returncode != 0:
            self.skipTest("the npm registry cannot be reached from here")

    def reused(self, done: subprocess.CompletedProcess[str]) -> list[str]:
        return [line for line in done.stdout.splitlines() if line.startswith(REUSE_PREFIX) and line != CLOSING
                and "did not run" in line]

    def installs(self, done: subprocess.CompletedProcess[str]) -> list[str]:
        return [line for line in done.stdout.splitlines() if line.startswith(f"npm --prefix {PREFIX} ci")]

    def test_e10_after_make_install_the_first_gate_installs_nothing_and_is_recorded(self) -> None:
        """AC-S04-54."""
        self.assert_passed(self.make("install"))
        first = self.make("verify")
        self.assert_passed(first)
        self.assertEqual(self.installs(first), [], first.stdout)
        self.assertNotIn(NOT_RECORDED, first.stdout)
        second = self.make("verify")
        self.assert_passed(second)
        self.assertEqual(len(self.reused(second)), 1, second.stdout)

    def test_e13_with_nothing_installed_the_first_pass_is_unrecorded_the_second_is_and_the_third_reuses(self) -> None:
        """AC-S04-64: the stamp's rule stands — a pass during which a covered input moved is not recorded."""
        first = self.make("verify")
        self.assert_passed(first)
        self.assertEqual(len(self.installs(first)), 1, first.stdout)
        self.assertIn(NOT_RECORDED, first.stdout)
        second = self.make("verify")
        self.assert_passed(second)
        self.assertEqual(self.installs(second), [], second.stdout)
        self.assertEqual(self.reused(second), [], "the second run reused a pass that was never recorded")
        self.assertNotIn(NOT_RECORDED, second.stdout)
        third = self.make("verify")
        self.assert_passed(third)
        self.assertEqual(len(self.reused(third)), 1, third.stdout)


class TypeScriptFirstGateTest(FirstGateTest):
    """AC-S04-54 and -64 hold on a TypeScript project too (D96, G17): every example above, with its toolchain real.

    A hold: the behaviour was there, so none of these is red for its own reason first. Its teeth were shown once by
    replacing the recipe's `@touch` of the marker in `model_targets.py` with `@true`, which failed both examples here
    and in the Python class, and restoring the file.
    """

    LANGUAGE = "typescript"
    VENV = False

    def setUp(self) -> None:
        super().setUp()
        # The starter is on the trunk, where no pass is recorded; a developer's branch is where these examples live.
        git(self.repo, "checkout", "-q", "-b", BRANCH)
        for key, value in (("user.name", "t"), ("user.email", "t@local"), ("commit.gpgsign", "false")):
            git(self.repo, "config", key, value)
