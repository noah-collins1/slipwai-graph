"""S42 T017 (converge pass 1 · D212 items 1, 4, 6; D219's reason; plan.md *Applied, not decided* 2 and 5; AC-S42-5, -6):
what silences mutants, as mutmut 3.8.0 reads it, fails the run, and is decided in `plan`, before any *no mutant to run*
or *found nothing* exit.

The reader is mutmut's `_parse_pragma_token` (`mutmut/mutation/pragma_handling.py`): a comment holding `# pragma:` and
`no mutate` takes the tail after `no mutate`, strips `: `, reads the first word before a comma. Only comments are read.
The fake `uv` and the harness are `test_mutmut_verdict`'s.
"""
from __future__ import annotations

import subprocess
import sys
from typing import Any

from test_mutmut_verdict import KEY, TABLE, Case, lines_of

sys.dont_write_bytecode = True
# `test_mutmut_verdict` imports `slipwai`, which reads this script on import (as `test_stryker_closure` does)
TEST_SELECTION = {"reads": ["assets/languages/python/scripts/mutmut-mutation.py",
                            "assets/toolkit/scripts/check-styles.py"]}
FILE = "apps/service/src/pkg/a.py"
BODY = "def f():\n    return 1\n"


def holds(word: str, line: int) -> str:
    return (f'mutation: {FILE}:{line} holds "# pragma: no mutate {word}", which silences mutants nobody looked at; '
            'only a bare "# pragma: no mutate" on the line excuses one')


class SilencedCase(Case):
    def source(self, text: str, setting: str = "") -> None:
        (self.service / "src/pkg").mkdir(parents=True, exist_ok=True)
        (self.service / "src/pkg/a.py").write_text(text, encoding="utf-8")
        (self.service / "pyproject.toml").write_text(TABLE.replace("[tool.mutmut]\n", "[tool.mutmut]\n" + setting),
                                                     encoding="utf-8")

    def scoped(self, keys: dict[str, Any] | None = None, *arguments: str) -> subprocess.CompletedProcess[str]:
        keys = {KEY: None} if keys is None else keys
        return self.run_wrapper("apps/service", *(arguments or ("--file", "src/pkg/a.py")),
                                meta={"src/pkg/a.py": keys}, results={"src/pkg/a.py": {key: 1 for key in keys}})


SPELLINGS = (
    ("# pragma: no mutate: block", "block"), ("# pragma: no mutate:block", "block"),
    ("# pragma:no mutate block", "block"),
    ("# pragma: no cover, no mutate block", "block"), ("# pragma: no mutate block, a reason", "block"),
    ("# pragma: no mutate start", "start"), ("# pragma: no mutate: start", "start"),
    ("# pragma: no mutate:start", "start"), ("# pragma: no mutate end", "end"), ("# pragma: no mutate: end", "end"),
    ("# pragma: no mutate:end", "end"), ("# pragma: no cover, no mutate end", "end"),
)
NOT_A_PRAGMA_TO_MUTMUT = (
    "# pragma: no mutate", "# pragma: no mutate, a reason", "# pragma: no mutate: a reason",
    "# pragma: no mutate blocked",
    "#pragma: no mutate block", "#  pragma: no mutate block", "# pragma: nomutate block", "# no mutate block",
    "# pragma: no cover",
)


class SpellingTest(SilencedCase):
    def test_e1_every_spelling_mutmut_reads_as_block_start_or_end_fails_the_run_with_its_line(self) -> None:
        for comment, word in SPELLINGS:
            for where, text in (("own line", f"x = 1\n{comment}\n{BODY}"), ("trailing", f"x = 1\ny = 2  {comment}\n")):
                with self.subTest(comment=comment, where=where):
                    self.source(text)
                    done = self.scoped()
                    self.assertEqual(done.returncode, 1)
                    self.assertIn(holds(word, 2), lines_of(done))

    def test_e1_hold_what_mutmut_reads_as_bare_or_not_at_all_is_not_flagged(self) -> None:
        """HOLD (teeth: flag every `no mutate` comment, or read `#pragma` as one, and see it fail)."""
        for comment in NOT_A_PRAGMA_TO_MUTMUT:
            with self.subTest(comment=comment):
                self.source(f"x = 1  {comment}\n{BODY}")
                self.assertEqual(self.scoped().returncode, 0)

    def test_e1_hold_the_same_text_in_a_string_is_not_a_comment(self) -> None:
        """HOLD (teeth: read lines and not comment tokens, and see it fail)."""
        self.source('s = "# pragma: no mutate block"\nt = """\n# pragma: no mutate start\n"""\n' + BODY)
        self.assertEqual(self.scoped().returncode, 0)

    def test_e1_a_file_python_cannot_tokenize_fails_closed(self) -> None:
        self.source("x = (1,\n")
        done = self.scoped()
        self.assertEqual(done.returncode, 1)
        self.assertIn(f"mutation: {FILE} cannot be read as Python, so its pragmas cannot be checked",
                      lines_of(done))


class BeforeTheEmptyExitsTest(SilencedCase):
    def test_e2_a_scoped_file_wholly_inside_start_and_end_fails_and_never_says_no_mutant_to_run(self) -> None:
        self.source("# pragma: no mutate start\n" + BODY + "# pragma: no mutate end\n")
        done = self.scoped({})
        self.assertEqual(done.returncode, 1)
        self.assertIn(holds("start", 1), lines_of(done))
        self.assertIn(holds("end", 4), lines_of(done))
        self.assertFalse(any("no mutant to run" in line for line in lines_of(done)))
        self.assertEqual(self.started_mutmut(), [])

    def test_e2_a_table_with_do_not_mutate_patterns_fails_a_scoped_file_it_emptied(self) -> None:
        self.source(BODY, 'do_not_mutate_patterns = ["return"]\n')
        done = self.scoped({})
        self.assertEqual(done.returncode, 1)
        self.assertIn("mutation: apps/service/pyproject.toml sets do_not_mutate_patterns", " ".join(lines_of(done)))
        self.assertFalse(any("no mutant to run" in line for line in lines_of(done)))
        self.assertEqual(self.started_mutmut(), [])

    def test_e2_the_table_is_read_before_the_nothing_under_exit_too(self) -> None:
        self.source(BODY, 'do_not_mutate_patterns = ["return"]\n')
        done = self.run_wrapper("apps/service", "--file", "src/pkg/a.py")
        self.assertEqual(done.returncode, 1)
        self.assertFalse(any("nothing under" in line for line in lines_of(done)))

    def test_e2_a_sweep_whose_every_file_is_silenced_names_the_pragma_beside_found_nothing(self) -> None:
        self.source("# pragma: no mutate start\n" + BODY + "# pragma: no mutate end\n")
        done = self.run_wrapper("apps/service", meta={"src/pkg/a.py": {}})
        self.assertEqual(done.returncode, 1)
        shown = lines_of(done)
        self.assertIn(holds("start", 1), shown)
        self.assertEqual(shown[-1], "mutation: mutmut found nothing to mutate in apps/service; a pass on nothing is "
                                    "not a pass")

    def test_e2_hold_a_function_less_file_is_still_no_mutant_to_run(self) -> None:
        """HOLD (teeth: fail every empty `.meta` and see it fail)."""
        self.source("X = 1  # pragma: no mutate\n")
        done = self.scoped({})
        self.assertEqual(done.returncode, 0)
        self.assertEqual(lines_of(done), ["mutation: no mutant to run — src/pkg/a.py: mutmut found no function "
                                          "to mutate in it"])

    def test_e2_a_given_file_outside_the_targets_has_no_meta_and_is_not_read(self) -> None:
        self.source("x = 1  # pragma: no mutate block\n")
        done = self.run_wrapper("apps/service", "--file", "src/pkg/a.py", meta={})
        self.assertEqual(done.returncode, 0)


class OnlyCoveredLinesTest(SilencedCase):
    LINE = ("mutation: apps/service/pyproject.toml sets mutate_only_covered_lines, which leaves out the mutants of "
            "every line coverage excludes without anyone looking at them")

    def test_e3_a_table_setting_it_fails_in_plan_with_one_line_naming_it(self) -> None:
        for keys in ({KEY: None}, {}):
            with self.subTest(keys=keys):
                self.source(BODY, "mutate_only_covered_lines = true\n")
                done = self.scoped(keys)
                self.assertEqual(done.returncode, 1)
                self.assertEqual([line for line in lines_of(done) if "mutate_only_covered_lines" in line], [self.LINE])
                self.assertEqual(self.started_mutmut(), [])

    def test_e3_a_sweep_fails_too_and_so_does_a_file_outside_the_targets(self) -> None:
        self.source(BODY, "mutate_only_covered_lines = true\n")
        done = self.run_wrapper("apps/service", meta={"src/pkg/a.py": {KEY: None}})
        self.assertEqual((done.returncode, self.started_mutmut()), (1, []))
        self.assertIn(self.LINE, lines_of(done))
        done = self.run_wrapper("apps/service", "--file", "src/pkg/a.py", meta={})
        self.assertEqual(done.returncode, 1)

    def test_e3_hold_false_or_absent_is_not_flagged(self) -> None:
        """HOLD (teeth: flag the key's presence and see it fail)."""
        self.source(BODY, "mutate_only_covered_lines = false\n")
        self.assertEqual(self.scoped().returncode, 0)


if __name__ == "__main__":
    import unittest

    unittest.main()
