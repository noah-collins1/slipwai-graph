"""T036 (R4, R5 · AC-S06-2, -5; D127 items 2, 4, 7, D140 point 8): a rule make applies that no prerequisite names.

A pattern rule, a suffix rule, a match-anything rule, `.DEFAULT`, a special target, a `vpath` and a `.PHONY` line are
all rules make applies to a name `verify` reaches without any prerequisite saying so. No list of them was ever
complete (four passes found the next one each time), so the `Makefile` text is held instead (D140): each is a text
the factory did not write and is the full gate, with the `Makefile` words, before make reads it. A project's pattern
rule that matches nothing `verify` reaches, and its `.PHONY` line for a target of its own, are the full gate too
(e5 reversed).
"""
from __future__ import annotations

import sys
from collections.abc import Callable

from scoped_fixture import FULL, MAKEFILE_WORDS
from stamp_fixture import git
from test_verify_scoped_sum import RuleCase

sys.dont_write_bytecode = True

# the constructs of the pass-4 probe, each appended to the trunk's `Makefile`
CONSTRUCTS = {
    ".ONESHELL": ".ONESHELL:\n", ".POSIX": ".POSIX:\n", ".SECONDEXPANSION": ".SECONDEXPANSION:\n",
    ".DELETE_ON_ERROR": ".DELETE_ON_ERROR:\n", ".NOTPARALLEL": ".NOTPARALLEL:\n",
    ".SUFFIXES and a suffix rule": ".SUFFIXES: .x .y\n.x.y:\n\t@exit 1\n", ".IGNORE": ".IGNORE:\n",
    ".SILENT": ".SILENT:\n", ".DEFAULT": ".DEFAULT:\n\t@echo default\n",
    ".PRECIOUS": ".PRECIOUS: node_modules/.package-lock.json\n",
    ".INTERMEDIATE": ".INTERMEDIATE: node_modules/.package-lock.json\n", ".SECONDARY": ".SECONDARY:\n",
    ".NOTINTERMEDIATE": ".NOTINTERMEDIATE:\n", ".LOW_RESOLUTION_TIME": ".LOW_RESOLUTION_TIME: x\n",
    "a match-anything rule": "%:: FORCE\n\t@echo any\n\nFORCE:\n", "vpath": "vpath %.mjs tools\n",
    "a .PHONY line naming a reached target": ".PHONY: check-drawio\n",
    "a -include": "-include extra.mk\n",
}
# e1: an implicit rule on a reached file that has no recipe, which `make verify` fails and the scoped run never saw
PATTERN = "scripts/event-model/%.json: FORCE\n\t@! grep -rq FORBIDDEN apps/web/src\n\nFORCE:\n"
# e5 (reversed): neither matches a name `verify` reaches
UNMATCHED = "deploy/%.yaml: deploy/%.yaml.in\n\tcp $< $@\n"
OWN_PHONY = ".PHONY: deploy\ndeploy:\n\t@echo deploy\n"


class ImplicitRuleTest(RuleCase):
    first: str | None = None  # the trunk commit the examples of one test start from

    def assert_makefile_reason(self, text: str, fails: bool = False) -> None:
        run = self.scoped()
        self.assertEqual(self.scoped_lines(run)[0], FULL + MAKEFILE_WORDS, f"{text!r}\n{run.stdout}")
        self.assertEqual(self.lines(run), [], "a unit line was said beside the full gate")
        self.assertEqual(len(self.verify_calls()), 1, "`make verify` was not run exactly once")
        if fails:
            self.assertNotEqual(run.returncode, 0, run.stdout)

    def test_e1_a_project_pattern_rule_on_a_reached_file_is_the_full_gate_and_the_gate_fails(self) -> None:
        """The reproduction: `check-drawio` waits for `scripts/event-model/package.json`; it fails the full gate."""
        self.trunk(lambda text: text + "\n" + PATTERN)
        self.edit("apps/web/src/App.tsx", "\n// FORBIDDEN\n")
        self.assert_makefile_reason(PATTERN, fails=True)

    def test_e2_a_match_anything_rule_and_a_default_recipe_are_each_the_full_gate(self) -> None:
        for name in ("a match-anything rule", ".DEFAULT"):
            with self.subTest(name):
                self.each(name, CONSTRUCTS[name])

    def test_e3_each_special_target_the_factory_did_not_write_is_the_full_gate(self) -> None:
        for name, text in CONSTRUCTS.items():
            if name not in ("a match-anything rule", ".DEFAULT", "vpath", "a .PHONY line naming a reached target"):
                with self.subTest(name):
                    self.each(name, text)

    def test_e4_a_vpath_and_a_phony_line_for_a_reached_target_are_the_full_gate(self) -> None:
        for name in ("vpath", "a .PHONY line naming a reached target"):
            with self.subTest(name):
                self.each(name, CONSTRUCTS[name])

    def test_e5_an_unmatched_pattern_rule_and_a_phony_line_of_its_own_are_the_full_gate_too(self) -> None:
        for what, text in (("an unmatched pattern rule", UNMATCHED), ("a project's own target", OWN_PHONY)):
            with self.subTest(what):
                self.each(what, text)

    def each(self, name: str, text: str) -> None:
        """The factory's `Makefile` with `text` appended on the trunk, a branch cut from it, and a web edit."""
        self.restore_trunk(lambda old: old + "\n" + text)
        self.edit("apps/web/src/App.tsx", "\n// harmless\n")
        self.assert_makefile_reason(name)

    def restore_trunk(self, edit: Callable[[str], str]) -> None:
        """What the trunk held first, edited: one example after another does not stack their texts."""
        self.reset()
        git(self.repo, "checkout", "-q", "main")
        if self.first is None:
            self.first = git(self.repo, "rev-parse", "HEAD").strip()
        else:
            git(self.repo, "checkout", "-q", self.first, "--", "Makefile")
        self.trunk(edit)
