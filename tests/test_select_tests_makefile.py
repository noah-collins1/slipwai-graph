"""The patched root `Makefile` holds the text the selector needs (S38 R9, AC-S38-6, -13, -14).

Text only: the recipes of `test` and `verify` are held line for line (the S33/D140 lesson: text nobody compared is where
a defect hid), and the stamp's bypass list is held unchanged. On the unpatched tree each test fails with the line that
names the patch. Behaviour through the real `Makefile` is `test_select_tests_make`.
"""
from __future__ import annotations

import sys
import unittest

from select_fixture import BYPASS, bypass_list

from slipwai.assets import ROOT

sys.dont_write_bytecode = True

PATCH = "specs/001-faster-slipwai/slices/S38-factory-test-selection/s38.patch"
UNPATCHED = f"the root Makefile is not yet patched \u2014 apply {PATCH}"
MAKEFILE = ROOT / "Makefile"

# `test` calls the selector unless TESTS or SKIP is given (SKIP fills TESTS in, so its origin is the file), and then
# says so; a SKIP that names every module leaves TESTS empty, so it says so and runs no module rather than the selector.
TEST_RECIPE = [
    "\t$(if $(strip $(TESTS)$(SKIP)),echo 'selection off: $(if $(filter file,$(origin TESTS)),SKIP,TESTS) given'"
    "$(if $(strip $(TESTS)),; PYTHONPATH=src:tests python3 -m unittest -v $(TESTS)),"
    "PYTHONPATH=src python3 -B scripts/select-tests.py)",
]
# `verify-checks` is whole however it is reached: a target-specific, overriding, exported FULL its prerequisites get.
FULL_RULE = [
    "# Run directly or through `verify`, the gate is whole: `override` holds against FULL on the command line, in "
    "MAKEFLAGS and",
    "# under `make -e`, `export` hands it to the `test` prerequisite's recipe, which the selector reads.",
    "verify-checks: override export FULL := 1",
]
BYPASS_TEST = "ifneq ($(strip $(TESTS)$(SKIP)$(FACTORY_BACKENDS)),)"
CHECKS = '"$(MAKE)" --no-print-directory -f "$(firstword $(MAKEFILE_LIST))" verify-checks FULL=1'
ELSE_BEFORE = (
    "\t@if [ -L .factory-work ] || { [ -e .factory-work ] && [ ! -d .factory-work ]; }; then echo 'verify:"
    ' .factory-work is a symbolic link or not a directory; the stamp cannot key what is behind it - make '
    "it a plain directory' >&2; exit 2; fi; { mkdir -p .factory-work && { docker compose version 2>/dev/n"
    'ull || echo absent; { command -v sort >/dev/null && list=$$(find assets \\( -name __pycache__ -o -nam'
    'e \'*.pyc\' -o -name \'*.pyo\' \\) 2>/dev/null) && printf \'%s\\n\' "$$list" | LC_ALL=C sort; } || echo "cac'
    'hes: not listed, run $$$$"; } > .factory-work/verify-probes; } || { echo \'verify: .factory-work/veri'
    "fy-probes could not be written, so the stamp would key a stale answer; the gate stops' >&2; exit 2; "
    '}; run=$$(python3 $(VERIFY_STAMP_SCRIPT) token); python3 $(VERIFY_STAMP_SCRIPT) reuse --token "$$run'
    '" $(VERIFY_STAMP) || { "$(MAKE)" --no-print-directory -f "$(firstword $(MAKEFILE_LIST))"'
)
ELSE_AFTER = (
    'python3 $(VERIFY_STAMP_SCRIPT) record --token "$$run" $(VERIFY_STAMP); } || { rc=$$?; [ "$$rc" -eq 1'
    ' ] || echo \'verify: the gate did not pass; each failed check is named above\'; exit "$$rc"; }'
)

# The stamped branch is today's line with `FULL=1` after its one `verify-checks`.
VERIFY_RECIPE = [BYPASS_TEST, "\t@" + CHECKS, "else", ELSE_BEFORE + " verify-checks FULL=1 && " + ELSE_AFTER, "endif"]


def lines() -> list[str]:
    return MAKEFILE.read_text(encoding="utf-8").split("\n")


def recipe(target: str) -> list[str]:
    """The lines after `<target>:` up to the blank line that ends its recipe."""
    text = lines()
    start = next(i for i, line in enumerate(text) if line.startswith(f"{target}:"))
    end = next(i for i in range(start + 1, len(text)) if text[i] == "")
    return text[start + 1:end]


class TestTheMakefileHoldsThePatchedText(unittest.TestCase):
    def patched(self) -> None:
        if "select-tests.py" not in MAKEFILE.read_text(encoding="utf-8"):
            self.fail(UNPATCHED)

    def test_the_root_makefile_is_patched(self) -> None:
        self.patched()

    def test_the_test_recipe_calls_the_selector_unless_tests_is_given(self) -> None:  # e1
        self.patched()
        self.assertEqual(recipe("test"), TEST_RECIPE)

    def test_both_branches_of_verify_pass_full_to_verify_checks(self) -> None:  # e1
        self.patched()
        self.assertEqual(recipe("verify"), VERIFY_RECIPE)
        self.assertEqual(sum("verify-checks FULL=1" in line for line in lines()), 2)

    def test_verify_checks_and_the_variables_the_suite_is_narrowed_by_are_unchanged(self) -> None:  # e1
        self.patched()
        text = lines()
        self.assertIn("verify-checks: lint typecheck check-structure test", text)
        at = text.index(FULL_RULE[0])
        self.assertEqual(text[at:at + 4], [*FULL_RULE, "verify-checks: lint typecheck check-structure test"])
        self.assertEqual(text[at - 1], ".PHONY: verify-checks")
        self.assertIn("TESTS ?= $(if $(SKIP),$(filter-out $(SKIP),$(ALL_TESTS)),)", text)

    def test_the_stamp_bypass_list_is_the_recorded_one_and_since_is_not_on_it(self) -> None:  # e1
        self.patched()
        self.assertEqual(bypass_list(MAKEFILE), BYPASS)
        self.assertIn(BYPASS_TEST, lines())
        self.assertNotIn("SINCE", BYPASS_TEST)


if __name__ == "__main__":
    unittest.main()
