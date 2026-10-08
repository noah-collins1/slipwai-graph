"""S41 T026 (D212, AC-S41-1, -3, -4): a scoped run never passes on a report that does not show the files it was given.

Split from `test_stryker_verdict`, whose fixtures it uses: the wrapper runs as a subprocess in a temporary project
with a fake `npm` that writes the report an example's plan hands it.
"""
from __future__ import annotations

import sys
import unittest
from typing import Any

from test_stryker_verdict import REPORT, SERVICE, VerdictCase, mutant, report

from slipwai.assets import ROOT

sys.dont_write_bytecode = True
TEST_SELECTION = {"reads": ["assets/languages/typescript/scripts/stryker-mutation.py"]}
EMPTY: dict[str, Any] = {"files": {}}
NONE_TO_RUN = "mutation: no mutant to run — src/a.ts: Stryker found no mutant in them (types or comments only)"


class ReportNamesTest(VerdictCase):
    def write(self, name: str, text: str) -> None:
        (self.tree / SERVICE / name).write_text(text, encoding="utf-8")

    def test_e1_a_report_that_names_a_file_outside_the_given_list_fails_naming_it(self) -> None:
        self.write("src/a.ts", "export const a = 'x';\n")
        for the_report in (report(src__other_ts=[mutant("Killed")]),
                           report(src__a_ts=[mutant("Killed")], src__other_ts=[mutant("Killed")])):
            with self.subTest(report=sorted(the_report["files"])):
                code, lines = self.run_wrapper({"report": the_report}, "--file", "src/a.ts")
                self.assertEqual(code, 1, lines)
                self.assertIn(f"mutation: the report names {SERVICE}/src/other.ts, which was not given; a scoped run "
                              f"is judged on the files it was given, so that is not a pass (report {REPORT})", lines)

    def test_e2_files_empty_is_the_zero_only_for_a_given_file_that_holds_nothing_to_plant(self) -> None:
        for text in ("", "// only a comment\n/* and another\n   over two lines */\n",
                     "export interface A { b: string; c(): void }\n",
                     "import type { X } from './x.js';\nimport { Y } from './y.js';\nexport type Z = X | 'a;b';\n",
                     "export type { X } from './x.js';\nexport * from './y.js';\nexport { Y };\n",
                     "type A = { a: string }\nexport type B = A\ninterface C {\n  d: number\n}\n"):
            with self.subTest(text=text):
                self.write("src/a.ts", text)
                code, lines = self.run_wrapper({"report": EMPTY}, "--file", "src/a.ts")
                self.assertEqual((code, lines[-1]), (0, NONE_TO_RUN), lines)

    def test_e3_files_empty_over_a_given_file_that_holds_code_fails_naming_it(self) -> None:
        for text in ("export const x = 'one';\n", "export function f() { return 1 }\n", "export enum E { A = 1 }\n",
                     "type A = { a: string }\nexport const x = [1]\n", "export type A = string;\nconst y = 'z';\n",
                     "import('./x.js');\n", "class K {}\n"):
            with self.subTest(text=text):
                self.write("src/a.ts", text)
                code, lines = self.run_wrapper({"report": EMPTY}, "--file", "src/a.ts")
                self.assertEqual(code, 1, lines)
                self.assertEqual(lines[-1], f"mutation: Stryker found no mutant in {SERVICE}/src/a.ts, which holds "
                                            f"code it could mutate; that is not a pass (report {REPORT})")

    def test_e4_a_given_file_that_is_not_a_file_fails_and_one_of_two_with_no_mutant_is_named(self) -> None:
        code, lines = self.run_wrapper({"report": EMPTY}, "--file", "src/a.ts")
        self.assertEqual(code, 1, lines)
        self.assertEqual(lines[-1], f"mutation: {SERVICE}/src/a.ts is not a file; that is not a pass (report {REPORT})")
        self.write("src/a.ts", "export interface A {}\n")
        self.write("src/b.ts", "export const b = 'x';\n")
        code, lines = self.run_wrapper({"report": report(src__a_ts=[])}, "--file", "src/a.ts", "--file", "src/b.ts")
        self.assertEqual(code, 1, lines)
        self.assertIn(f"mutation: Stryker found no mutant in {SERVICE}/src/b.ts, which holds code it could mutate; "
                      f"that is not a pass (report {REPORT})", lines)


# What Stryker 10.0.0's mutators read (research R12, probed with its instrumenter): a string or template literal, a
# boolean or `!`, a unary `-`, a non-empty array or object, an arrow or function body, a regex with a pattern, an
# operator, a call on a string method. A numeric literal, `null`, `undefined`, a name or a member path: none.
INERT = ("export const A = 0;", "export const A: number = 0;", "export const A = 10n;", "export const A = 0xff;",
         "export const A = 1_000;", "export const A = 1.5e3;", "const A = 0;", "let A = 0;", "var A = 0;",
         "export const A = null;", "export const A = undefined;", "export const A = B;", "export const A = B.c.d;",
         "export const A = 0 as const;", "export const A: Readonly<number> = 0;", "export const A = 0\n",
         "export const A = 0;\nexport const B = 1;\nexport type C = typeof A;\n")
CODE = ("export const A = -1;", "export const A = 'x';", "export const A = `x`;", "export const A = true;",
        "export const A = false;", "export const A = [1];", "export const A = {b: 1};", "export const A = !B;",
        "export const A = B + 1;", "export const A = f();", "export const A = () => 0;", "export const A = 0, B = 1;",
        "export const A = 0 + 1;", "export const A = B ? 0 : 1;", "export const A = (0);", "export const A = B?.c;",
        "export const A = 0;\nexport const B = 'x';", "export default 0;", "export const A = true as const;")


class NothingToMutateTest(VerdictCase):
    def write(self, name: str, text: str) -> None:
        (self.tree / SERVICE / name).write_text(text, encoding="utf-8")

    def test_e7_a_declaration_no_stryker_10_mutator_reads_is_no_mutant_to_run(self) -> None:
        for text in INERT:
            with self.subTest(text=text):
                self.write("src/a.ts", text)
                code, lines = self.run_wrapper({"report": EMPTY}, "--file", "src/a.ts")
                self.assertEqual((code, lines[-1]), (0, NONE_TO_RUN), lines)

    def test_e8_the_starters_own_read_models_port_with_a_comment_edited_is_no_mutant_to_run(self) -> None:
        text = (ROOT / "assets/backing-services/typescript/read-models.ts").read_text(encoding="utf-8")
        self.assertIn("export const FROM_THE_BEGINNING = 0;", text)
        self.write("src/a.ts", text.replace("Where a projection that has never run starts.", "Where one starts."))
        code, lines = self.run_wrapper({"report": EMPTY}, "--file", "src/a.ts")
        self.assertEqual((code, lines[-1]), (0, NONE_TO_RUN), lines)

    def test_e9_a_construct_a_mutator_reads_or_the_scanner_cannot_classify_still_fails_closed(self) -> None:
        for text in CODE:
            with self.subTest(text=text):
                self.write("src/a.ts", text)
                code, lines = self.run_wrapper({"report": EMPTY}, "--file", "src/a.ts")
                self.assertEqual(code, 1, lines)
                self.assertIn("which holds code it could mutate; that is not a pass", lines[-1])


if __name__ == "__main__":
    unittest.main()
