"""A path no row claims never reaches `choose.select` silently: it stops selection with one full line (S43, after D188).

`scripts/select-tests.py` turns every path `rules.broadening` names into a full run before it calls `choose.select`, so
a real `make test` never hands it an unclaimed path (a bare directory, a top-level name no row knows). A direct caller
can: the S26 check in `test_select_tests_real_s43` handed it `specs`, a declared read that is a directory, and
the selector died on a `KeyError` inside `reach`. A crash is neither a selection nor a full run, so the doubt is said
the way the selector says every other one — `Full` with its one line — and a caller that runs the suite runs all of it.
Read over the real tree, with `choose` fed paths directly, so no git is involved.
"""
from __future__ import annotations

import sys
import unittest
from collections.abc import Mapping
from typing import Any

from slipwai.assets import ROOT

sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "scripts"))

from select_tests import choose, declarations, rules  # noqa: E402
from select_tests.report import Full  # noqa: E402


class TestAnUnclaimedPathStopsSelectionWithOneLine(unittest.TestCase):
    tree: declarations.Tree
    catalog: Mapping[str, Any]

    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = rules.load_catalog(ROOT)
        cls.tree = declarations.scan(ROOT, cls.catalog)

    def test_a_directory_no_row_claims_is_a_full_line_naming_it(self) -> None:
        for path in ("specs", "assets", "assets/newthing", "no-such-top-level-name"):
            with self.subTest(path), self.assertRaises(Full) as raised:
                choose.select(self.tree, [path], self.catalog)
            self.assertTrue(raised.exception.line.startswith("full: "), raised.exception.line)
            self.assertIn(f"`{path}`", raised.exception.line)
            self.assertIn(rules.UNCLAIMED, raised.exception.line)
            self.assertNotIn("\n", raised.exception.line)

    def test_one_unclaimed_path_beside_claimed_ones_still_stops_it(self) -> None:
        with self.assertRaises(Full):
            choose.select(self.tree, ["assets/languages/go/Makefile", "specs"], self.catalog)

    def test_claimed_paths_select_as_before(self) -> None:
        chosen = choose.select(self.tree, ["assets/languages/go/Makefile", "docs/maintaining.md"], self.catalog)
        self.assertTrue(chosen.verdicts)
        self.assertEqual(chosen.backends, ("go",))


if __name__ == "__main__":
    unittest.main()
