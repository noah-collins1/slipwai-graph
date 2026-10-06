"""S08 T039 (class · AC-S08-2, adversary B2): `go-mutation.py` reads `.gremlins.yaml`'s `exclude-files` as YAML does.

The forms the factory's own file (`assets/languages/go/app/.gremlins.yaml`) could be edited into in a plain way: a
comment after a quoted item in either quote style, after the key, after the section; an empty list; a comment
line between items. A form the reader cannot read exits loudly, which the caller's scoped run takes as the sweep
and never as a wrong pattern: a pattern Gremlins would not have read is a trusted exclusion that is not one.
"""
from __future__ import annotations

import contextlib
import io
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from test_go_mutation_file import loaded

from slipwai.assets import LANGUAGE_ROOT

sys.dont_write_bytecode = True
FACTORY = LANGUAGE_ROOT / "go" / "app/.gremlins.yaml"


def document(*lines: str, head: str = "unleash:", key: str = "  exclude-files:") -> str:
    return "\n".join([head, "  integration: true", key, *(f"    {line}" for line in lines),
                      "  threshold:", "    efficacy: 99.99", ""])


class YamlTest(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = Path(tempfile.mkdtemp(prefix="go-yaml-", dir="/tmp"))
        self.addCleanup(shutil.rmtree, self.directory, ignore_errors=True)
        self.wrapper = loaded()

    def read(self, text: str) -> list[str]:
        config = self.directory / ".gremlins.yaml"
        config.write_text(text, encoding="utf-8")
        return self.wrapper.excluded(config)

    def refused(self, text: str) -> None:
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            self.read(text)

    def test_e1_hold_the_factorys_own_file_reads_as_it_says(self) -> None:
        self.assertEqual(self.wrapper.excluded(FACTORY), ["cmd/.*", "eventstorecontract/.*"])

    def test_e2_a_trailing_comment_after_a_quoted_item_is_not_part_of_it(self) -> None:
        items = ['- "x/.*" # why', "- 'y/.*'  # why", "- bare/.* # why", "- 'it''s.go'\t# q", r'- "a\\b" # e',
                 '- "q\\"uote" # e', '- "has # inside" # why', "- 'has # inside'"]
        self.assertEqual(self.read(document(*items)),
                         ["x/.*", "y/.*", "bare/.*", "it's.go", "a\\b", 'q"uote', "has # inside", "has # inside"])

    def test_e3_a_comment_after_a_key_or_the_section_changes_nothing(self) -> None:
        self.assertEqual(self.read(document('- "x/.*"', head="unleash: # why", key="  exclude-files: # why")), ["x/.*"])
        self.assertEqual(self.read(document('- "x/.*"', key="  exclude-files:   #")), ["x/.*"])
        self.assertEqual(self.read(document('- "x/.*"', "# between", '  # indented', "- 'y'")), ["x/.*", "y"])
        self.assertEqual(self.read(document('- "x/.*"', head='"unleash":', key="  'exclude-files':")), ["x/.*"])

    def test_e4_an_empty_list_is_empty_however_it_is_written(self) -> None:
        for key in ("  exclude-files: []", "  exclude-files: [ ]  # none", "  exclude-files: # none",
                    "  exclude-files: ~", "  exclude-files: null # none"):
            with self.subTest(key):
                self.assertEqual(self.read(document(key=key)), [])

    def test_e5_a_form_it_cannot_read_is_refused_never_read_wrong(self) -> None:
        for lines, key in (
            (['- "x/.*"#glued'], "  exclude-files:"),       # `#` with no space before it is not a comment: a YAML error
            (['- "x/.*" junk'], "  exclude-files:"),
            (['- "unclosed'], "  exclude-files:"),
            ([r'- "a\.go"'], "  exclude-files:"),          # an invalid escape: Gremlins itself refuses the file
            (["- {a: b}"], "  exclude-files:"),
            (["- &anchor x/.*"], "  exclude-files:"),
            (["-"], "  exclude-files:"),
            (["- # nothing"], "  exclude-files:"),
            ([], '  exclude-files: ["cmd/.*"]'),
            ([], "  exclude-files: [] x"),
            ([], "  exclude-files: bare"),
        ):
            with self.subTest(lines=lines, key=key):
                self.refused(document(*lines, key=key))


if __name__ == "__main__":
    unittest.main()
