"""S41 T028 (D219, D212 items 1 and 6): an `Ignored` mutant passes only where the line above it is a
`// Stryker disable next-line <mutator>: <reason>` comment naming its mutator with a reason.

Stryker 10.0.0 gives the same `Ignored` status to a next-line, a block and a file-wide comment (and the same
`statusReason` to the last two when they give a reason), and a different one only to `excludedMutations`: research R10.
The wrapper reads the source line above the mutant, from the report's `source` where it holds one, else from the file.
"""
from __future__ import annotations

import sys
import unittest

from test_stryker_verdict import REPORT, SERVICE, VerdictCase, mutant, report

sys.dont_write_bytecode = True
TEST_SELECTION = {"reads": ["assets/languages/typescript/scripts/stryker-mutation.py"]}
CODE = 'export const a = "x";'
EXCLUDED = 'Ignored because of excluded mutation "StringLiteral"'


def ignored(reason: str, line: int = 2, name: str = "StringLiteral") -> dict:
    return {**mutant("Ignored", line, 5, name), "statusReason": reason}


class IgnoredTest(VerdictCase):
    def judge(self, source: list[str], one: dict, **plan: object) -> tuple[int, list[str]]:
        (self.tree / SERVICE / "src/a.ts").write_text("\n".join(source) + "\n", encoding="utf-8")
        return self.run_wrapper({"report": report(src__a_ts=[mutant("Killed"), one]), **plan}, "--file", "src/a.ts")

    def failing(self, source: list[str], one: dict, why: str) -> None:
        code, lines = self.judge(source, one)
        self.assertEqual(code, 1, lines)
        self.assertIn(f'mutation: Ignored {SERVICE}/src/a.ts:{one["location"]["start"]["line"]}:5 '
                      f'{one["mutatorName"]} → "" — not excused: {why} (report {REPORT})', lines)
        self.assertTrue(lines[-1].endswith(f"1 ignored without a next-line comment; failed — report {REPORT}"), lines)

    def test_e1_a_next_line_comment_naming_the_mutator_with_a_reason_passes(self) -> None:
        for comment, reason in (("// Stryker disable next-line StringLiteral: a label only", "a label only"),
                                ("  // Stryker disable next-line stringliteral,ConditionalExpression : equivalent",
                                 "equivalent"),
                                ("//Stryker disable next-line ConditionalExpression, StringLiteral: a reason: with a "
                                 "colon", "a reason: with a colon")):
            with self.subTest(comment=comment):
                code, lines = self.judge([comment, CODE], ignored(reason))
                self.assertEqual(code, 0, lines)
                self.assertEqual(lines[-1], "mutation: 2 mutants: 1 killed, 1 ignored, 0 not covered (reported, never "
                                            f"failed); passed — report {REPORT}")

    def test_e2_a_next_line_comment_without_a_reason_fails(self) -> None:
        for comment in ("// Stryker disable next-line StringLiteral", "// Stryker disable next-line StringLiteral:",
                        "// Stryker disable next-line StringLiteral:   "):
            with self.subTest(comment=comment):
                self.failing([comment, CODE], ignored("Ignored using a comment"),
                             "the next-line comment gives no reason")

    def test_e3_a_block_or_file_wide_disable_fails_whatever_its_reason(self) -> None:
        why = "the line above it is not a `// Stryker disable next-line StringLiteral: <reason>` comment"
        self.failing(["// Stryker disable StringLiteral: a block", CODE, CODE.replace("a", "b")],
                     ignored("a block", line=3), why)
        self.failing(["// Stryker disable StringLiteral: the whole file", "", CODE],
                     ignored("the whole file", line=3), why)
        self.failing(["// Stryker disable StringLiteral: the whole file", CODE], ignored("the whole file"), why)

    def test_e4_excluded_mutations_fails_and_says_so(self) -> None:
        self.failing([CODE, CODE.replace("a", "b")], ignored(EXCLUDED),
                     "the config's mutator.excludedMutations ignored it, which is not a per-mutant comment")
        self.failing(["", "// Stryker disable next-line StringLiteral: a reason", CODE], ignored(EXCLUDED, line=3),
                     "the config's mutator.excludedMutations ignored it, which is not a per-mutant comment")

    def test_e5_a_comment_for_another_mutator_or_for_all_fails(self) -> None:
        for comment in ("// Stryker disable next-line ConditionalExpression: a reason",
                        "// Stryker disable next-line all: a reason",
                        "// Stryker restore next-line StringLiteral: a reason",
                        "/* Stryker disable next-line StringLiteral: a reason */"):
            with self.subTest(comment=comment):
                self.failing([comment, CODE], ignored("a reason"),
                             "the line above it is not a `// Stryker disable next-line StringLiteral: <reason>` comment"
                             if "restore" in comment or comment.startswith("/*") else
                             "the next-line comment does not name StringLiteral")

    def test_e6_the_first_line_and_a_source_that_cannot_be_read_fail_closed(self) -> None:
        self.failing([CODE], ignored("a reason", line=1),
                     "the line above it is not a `// Stryker disable next-line StringLiteral: <reason>` comment")
        (self.tree / SERVICE / "src/a.ts").unlink()
        code, lines = self.run_wrapper({"report": report(src__a_ts=[mutant("Killed"), ignored("r")])},
                                       "--file", "src/a.ts")
        self.assertEqual(code, 1, lines)

    def test_e7_the_source_the_report_carries_is_read_before_the_file(self) -> None:
        the_report = report(src__a_ts=[mutant("Killed"), ignored("a reason")])
        the_report["files"]["src/a.ts"]["source"] = "// Stryker disable next-line StringLiteral: a reason\n" + CODE
        (self.tree / SERVICE / "src/a.ts").write_text(CODE + "\n" + CODE, encoding="utf-8")
        code, lines = self.run_wrapper({"report": the_report}, "--file", "src/a.ts")
        self.assertEqual(code, 0, lines)


    def test_e8_lines_are_split_where_stryker_counts_them_not_where_python_does(self) -> None:
        """T039 (A5): a form feed is no line break to Stryker, so it must be none here; the comment above the mutant
        is the one without a reason, not the one Python's `splitlines` would put there."""
        self.failing(["// a page break here:\f next",
                      "// Stryker disable next-line StringLiteral: a reason that excuses nothing",
                      "// Stryker disable next-line StringLiteral", 'export const greeting = "hello";'],
                     ignored("Ignored using a comment", line=4), "the next-line comment gives no reason")
        for separator in ("\r\n", "\r", "\u2028", "\u2029"):
            with self.subTest(separator=repr(separator)):
                (self.tree / SERVICE / "src/a.ts").write_text(
                    separator.join(["// Stryker disable next-line StringLiteral: a reason", CODE]), encoding="utf-8")
                code, lines = self.run_wrapper({"report": report(src__a_ts=[mutant("Killed"), ignored("a reason")])},
                                               "--file", "src/a.ts")
                self.assertEqual(code, 0, lines)

    def test_e9_the_excuse_is_the_comment_that_gave_strykers_reason_not_a_block_comment_beside_it(self) -> None:
        """T039 (A6): a block disable ignored the mutant (Stryker's reason is the default one); a next-line comment
        that is really template text, one line above it, must not pass it."""
        source = ["// Stryker disable StringLiteral",
                  "// Stryker disable next-line StringLiteral: the outer template is a fixture",
                  "export const help = `",
                  "// Stryker disable next-line StringLiteral: this line is template text, not a comment",
                  '${"secret"}`;']
        self.failing(source, ignored("Ignored using a comment", line=5),
                     "Stryker's reason for ignoring it (`Ignored using a comment`) is not the next-line comment's "
                     "(`this line is template text, not a comment`), so another directive ignored it")
        code, lines = self.judge(source, ignored("this line is template text, not a comment", line=5))
        self.assertEqual(code, 0, lines)
        code, lines = self.judge(["// Stryker disable next-line StringLiteral: a reason", CODE], ignored(""))
        self.assertEqual(code, 1, "a report that gives no reason at all is not the comment's")

    def test_e10_the_nearest_directive_above_the_line_is_read_past_blank_and_comment_only_lines(self) -> None:
        """T039 (A8): Stryker attaches the comment to the next node, past any blank or comment-only line."""
        directive = "// Stryker disable next-line StringLiteral: a reason"
        for between in ([""], ["// a note", ""], ["", "/* another", " * note */", ""]):
            with self.subTest(between=between):
                code, lines = self.judge([directive, *between, CODE], ignored("a reason", line=len(between) + 2))
                self.assertEqual(code, 0, lines)
        self.failing([directive, "doThing();", "", CODE], ignored("a reason", line=4),
                     "the line above it is not a `// Stryker disable next-line StringLiteral: <reason>` comment")
        self.failing([directive, "// Stryker restore next-line StringLiteral: no", CODE], ignored("a reason", line=3),
                     "the line above it is not a `// Stryker disable next-line StringLiteral: <reason>` comment")


if __name__ == "__main__":
    unittest.main()
