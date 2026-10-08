"""S42 T046 (B2): `rule_of` finds a `mutation-full` or `mutation` rule however make spells it.

The recipe check and the rule-changed sweep read the rule through `rule_of`, which every backend shares. A rule spelled
with whitespace before the colon, or on a line of several targets, or a second rule for the target, is a rule make runs,
so it is not the recipe the factory wrote. Go's project, as `test_mutation_recipe` cuts it, behind S08's `FakeRunner`
seam through the script's own `Recording`.
"""
from __future__ import annotations

import sys

from stamp_fixture import git
from test_mutation_borders import loaded
from test_mutation_recipe import GO_FILE, NOT_FACTORY, RecipeBase
from test_mutation_sweeps import TWO_GO

sys.dont_write_bytecode = True
SPELLINGS = {
    "whitespace before the colon": "mutation-full :\n\t@echo override\n",
    "a tab before the colon": "mutation-full\t:\n\t@echo override\n",
    "several targets on one line": "other mutation-full: ## also\n\t@echo override\n",
    "a second rule for the target": "mutation-full:\n\t@echo again\n",
    "a double-colon rule": "mutation-full::\n\t@echo again\n",
}


class SpellingTest(RecipeBase):
    def append_on_main(self, rule: str) -> None:
        git(self.repo, "checkout", "-q", "main")
        makefile = self.repo / "Makefile"
        makefile.write_text(makefile.read_text(encoding="utf-8") + "\n" + rule, encoding="utf-8")
        self.commit("base")
        git(self.repo, "checkout", "-q", "-B", "slice/S1")

    def test_b2_a_rule_spelled_another_way_is_not_the_factorys_recipe(self) -> None:
        origin = git(self.repo, "rev-parse", "main").strip()
        for name, rule in SPELLINGS.items():
            with self.subTest(spelling=name):
                git(self.repo, "checkout", "-q", "-f", "slice/S1")
                git(self.repo, "branch", "-q", "-f", "main", origin)
                git(self.repo, "checkout", "-q", "-B", "slice/S1", "main")
                git(self.repo, "checkout", "-q", "--", ".")
                self.on_main(TWO_GO)
                self.append_on_main(rule)
                (self.repo / GO_FILE).unlink(missing_ok=True)
                self.log.unlink(missing_ok=True)
                self.write(GO_FILE)
                status, lines, recording = self.run_recording(*TWO_GO)
                self.assertEqual(lines[0], NOT_FACTORY, lines)
                self.swept_whole(status, lines, recording)

    def test_b2_a_changed_rule_spelled_another_way_sweeps_the_whole_run(self) -> None:
        self.on_main(TWO_GO)
        self.append_on_main("mutation-full :\n\t@echo before\n")
        makefile = self.repo / "Makefile"
        makefile.write_text(makefile.read_text(encoding="utf-8").replace("echo before", "echo after"), encoding="utf-8")
        self.write(GO_FILE)
        status, lines, recording = self.run_recording(*TWO_GO)
        self.assertIn("Makefile", lines[0], lines)
        self.swept_whole(status, lines, recording)

    def test_b2_hold_the_factorys_own_rule_and_look_alikes_are_not_found_as_others(self) -> None:
        module = loaded(self.repo / "scripts/mutation-scope.py")
        text = ("MUTATION_FULL := 1\nX ::= mutation-full: a\n.PHONY: mutation-full\nmutation-full-x:\n\t@a\n"
                "mutation-fullish: mutation-full\n\t@b\n"
                "mutation-full: ## Run\n\t@real\n\t@more\nafter:\n\t@c\n")
        self.assertEqual(module.rule_of(text, "mutation-full"), ["mutation-full: ## Run", "\t@real", "\t@more"])
        self.assertEqual(module.rule_of(text, "mutation"), [])
        self.assertEqual(module.rule_of("a mutation-full : x\n\t@r\n", "mutation-full"), ["a mutation-full : x", "\t@r"])
