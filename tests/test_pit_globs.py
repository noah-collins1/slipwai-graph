"""S08 T006 (rule 5 · AC-S08-3, AC-S08-4): PIT's pattern language as the scope script reads it.

The expected answers are research R2's: `org.pitest.util.Glob` in pitest 1.25.9, disassembled, and runs against the
Spring starter — the whole name (anchored), `*` any run of characters including `.`, `?` one character, `$` and `.`
literal, a leading `~` a raw regular expression, `**.` zero or more packages.
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from typing import Any

from slipwai.assets import ROOT

sys.dont_write_bytecode = True
SCRIPT = ROOT / "assets/toolkit/scripts/mutation-scope.py"


def loaded() -> Any:
    specification = importlib.util.spec_from_file_location("mutation_scope_globs", SCRIPT)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    was, sys.dont_write_bytecode = sys.dont_write_bytecode, True
    try:
        specification.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = was
    return module


class GlobTest(unittest.TestCase):
    def setUp(self) -> None:
        self.module = loaded()

    def holds(self, pattern: str, matching: list[str], other: list[str]) -> None:
        for name in matching:
            self.assertTrue(self.module.pit_matches(pattern, name), f"{pattern} should match {name}")
        for name in other:
            self.assertFalse(self.module.pit_matches(pattern, name), f"{pattern} should not match {name}")

    def test_a_bare_name_is_exact_and_never_a_prefix(self) -> None:
        self.holds("com.x.events.Tag", ["com.x.events.Tag"], ["com.x.events.TagQuery", "x.com.x.events.Tag"])

    def test_star_is_any_run_of_characters_including_dots(self) -> None:
        self.holds("com.x.*", ["com.x.Foo", "com.x.sub.Foo", "com.x.Foo$Bar"], ["com.xy.Foo", "org.com.x.Foo"])
        self.holds("com.x.*Test", ["com.x.FooTest", "com.x.a.b.BarTest"], ["com.x.FooTests"])

    def test_question_mark_is_one_character(self) -> None:
        self.holds("com.x.Fo?", ["com.x.Foo", "com.x.Fox"], ["com.x.Fo", "com.x.Fooo"])

    def test_dollar_and_dot_are_literal(self) -> None:
        self.holds("com.x.Foo$*", ["com.x.Foo$Bar", "com.x.Foo$Bar$Baz"], ["com.x.FooBar", "com.x.Foo"])
        self.holds("com.x.Foo", ["com.x.Foo"], ["com_x.Foo", "comax.Foo"])

    def test_double_star_dot_is_zero_or_more_packages(self) -> None:
        self.holds("**.Foo", ["Foo", "a.Foo", "a.b.Foo"], ["a.FooBar", "a.Bar"])
        self.holds("com.**.Foo", ["com.Foo", "com.a.Foo", "com.a.b.Foo"], ["org.a.Foo"])

    def test_a_leading_tilde_is_a_raw_regular_expression(self) -> None:
        self.holds(r"~com\.x\.(A|B)", ["com.x.A", "com.x.B"], ["com.x.AB", "com.x.C"])

    def test_a_pattern_python_cannot_read_is_unreadable(self) -> None:
        for pattern in ("~(", "~[a-", "~*x"):
            with self.subTest(pattern=pattern), self.assertRaises(self.module.Unreadable):
                self.module.pit_matches(pattern, "com.x.A")
        for pattern in ("${package}.*", "com.${x}.Foo"):
            with self.subTest(pattern=pattern), self.assertRaises(self.module.Unreadable):
                self.module.pit_matches(pattern, "com.x.A")


if __name__ == "__main__":
    unittest.main()
