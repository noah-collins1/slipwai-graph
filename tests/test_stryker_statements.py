"""S41 T037 (A2, A3 · AC-S41-3, T026, T033): a file is inert only where every statement of it is.

The wrapper's reader of a given file that Stryker found no mutant in cuts it into statements the way TypeScript does
(a `;`, or a newline where the next token cannot continue the statement), and a statement is inert only as a whole:
`import … ⏎ if (…)` is two statements, one inert and one code. Ambient declarations and enums without initialisers plant
nothing, which Stryker 10.0.0's report confirms (A3). What is not classified is code.
"""
from __future__ import annotations

import sys
import unittest
from typing import Any

from test_stryker_verdict import REPORT, SERVICE, VerdictCase

sys.dont_write_bytecode = True
TEST_SELECTION = {"reads": ["assets/languages/typescript/scripts/stryker-mutation.py",
                            "assets/toolkit/scripts/check-styles.py"]}
EMPTY: dict[str, Any] = {"files": {}}
NONE_TO_RUN = ("mutation: no mutant to run — src/a.ts: Stryker found no mutant in it (declarations and comments only: "
               "types, imports, plain constants)")
# A2: a statement that begins like a declaration and is followed, with no `;`, by code on the next line. Stryker planted
# mutants in every one of these.
CODE_AFTER_A_DECLARATION = (
    'import { health } from "./health"\nconsole.log(health().status === "ok" ? "up" : "down")\n',
    'export interface P { x: number }\nif (process.env.X === "1") { run() }\n',
    'type A = string\nawait start({ host: "0.0.0.0" })\n',
    'export type { A } from "./a"\nregister("x")\n',
    'import type { A } from "./a"\n// a comment between\nregister("x")\n',
    'export interface P { x: number } if (go) { run() }\n',
    'declare const A: string; \nrun()\n',
)
# A3: ambient declarations and an enum without initialisers, which Stryker plants nothing in.
INERT_STATEMENTS = (
    "declare const BUILD_ID: string;\ndeclare function track(e: string): void;\nexport {};\n",
    "export enum Kind { A, B }\n", "enum Kind {\n  A,\n  B,\n}\n", "export const enum Kind { A }\n", "enum Kind {}\n",
    "declare let a: number\ndeclare var b: string\n", "declare class C { x: number; m(): void }\n",
    "export declare function f(a: string): void\n", "declare namespace N { const a: string }\n",
    "declare module 'x' { export function f(): void }\n", "declare global { interface Window { a: string } }\n",
    "import { a } from './a'\nexport interface P { x: a }\ntype T = string\n",
    "export type A =\n  | 'a'\n  | 'b'\n",
)
# Anything the reader cannot classify as a whole stays code: an initialiser in an ambient or enum member, a body.
STILL_CODE = (
    "export enum Kind { A = 'a' }\n", "export enum Kind { A = 1 }\n", "declare const A = 'x';\n",
    "declare namespace N { const a = 'x' }\n",
    "export const enum Kind { A, B = A }\n", "interface P { x: number }\nrun()\n",
    "declare module 'x' {} run()\n", "enum K { A }; run()\n",
)


class StatementsTest(VerdictCase):
    def judge(self, text: str) -> tuple[int, list[str]]:
        (self.tree / SERVICE / "src/a.ts").write_text(text, encoding="utf-8")
        return self.run_wrapper({"report": EMPTY}, "--file", "src/a.ts")

    def test_e1_a_declaration_followed_by_code_on_the_next_line_is_two_statements_and_the_file_holds_code(self) -> None:
        for text in CODE_AFTER_A_DECLARATION:
            with self.subTest(text=text):
                code, lines = self.judge(text)
                self.assertEqual(code, 1, lines)
                self.assertEqual(lines[-1], f"mutation: Stryker found no mutant in {SERVICE}/src/a.ts, which holds "
                                            f"code it could mutate; that is not a pass (report {REPORT})")

    def test_e2_ambient_declarations_and_enums_without_initialisers_plant_nothing(self) -> None:
        for text in INERT_STATEMENTS:
            with self.subTest(text=text):
                code, lines = self.judge(text)
                self.assertEqual((code, lines[-1]), (0, NONE_TO_RUN), lines)

    def test_e3_what_the_reader_cannot_classify_as_a_whole_fails_closed(self) -> None:
        for text in STILL_CODE:
            with self.subTest(text=text):
                code, lines = self.judge(text)
                self.assertEqual(code, 1, lines)
                self.assertIn("which holds code it could mutate", lines[-1])


if __name__ == "__main__":
    unittest.main()
