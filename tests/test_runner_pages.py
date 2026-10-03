"""The pages that said only the gate narrows say the runner's check does as well, and the slice's one fragment says
what it changed (S02, R12; AC-S02-46, -69; D56, D57, D58, D59, D60, D61).

The pages are read as the project reads them: the docstring of `agents/code_index.py`, the codegraph extension's
`init.py` (its docstring and the block it writes into `AGENTS.md`), the text `docs.py` writes into a project's
verification page, and the factory's own `docs/cruise.md` and `docs/verification.md`.
"""
from __future__ import annotations

from pathlib import Path

from support import FactoryTestCase

ROOT = Path(__file__).resolve().parents[1]
PAGES = ("assets/toolkit/scripts/agents/code_index.py", "assets/toolkit/scripts/extensions/codegraph/init.py",
         "src/slipwai/project/docs.py", "docs/cruise.md", "docs/verification.md")
FRAGMENT = ROOT / "changelog.d/runner-bookkeeping.md"


def said(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


class WhatThePagesSayOfTheRunnersCheckTest(FactoryTestCase):
    def test_e46_each_page_says_the_runners_check_narrows_as_well_as_the_gate(self) -> None:
        for name in PAGES:
            with self.subTest(name):
                text = said(ROOT / name)
                for words in ("runner's check before an iteration", "only what changed since the last whole comparison",
                              "cannot see", "gate-memory.json"):
                    self.assertTrue(words in text, f"{name} does not say: {words}")

    def test_the_codegraph_extension_says_it_where_it_writes_the_block_as_well_as_in_its_docstring(self) -> None:
        text = said(ROOT / "assets/toolkit/scripts/extensions/codegraph/init.py")
        self.assertEqual(text.count("The runner's check before an iteration narrows the same way"), 2)


class WhatTheFragmentSaysTest(FactoryTestCase):
    def fragment(self) -> str:
        if not FRAGMENT.is_file():
            self.skipTest("released: `make release` assembled the fragment into CHANGELOG.md and deleted it")
        return said(FRAGMENT)

    def test_e69_hold_the_fragment_claims_minor_on_its_first_line(self) -> None:
        self.fragment()
        self.assertEqual(FRAGMENT.read_text(encoding="utf-8").splitlines()[0], "MINOR")

    def test_the_fragment_names_what_the_slice_changed_and_what_each_part_cannot_see(self) -> None:
        text = self.fragment()
        for part in (
            "`bookkeeping`", "`log_bytes`", "`stream_bytes`",
            "its value for a given tree is not the one earlier code gave",
            # D57 and D56: the residuals, in their own words
            "a file under `specs/` whose bytes changed while its size, modification time, change time and identity "
            "all read as before",
            "a control whose bytes were changed while its size, modification time, change time and identity all "
            "read as before",
            # AC-S02-46's three sentences
            "compares only what changed since the last whole comparison",
            "holds for it too",
            "Deleting that file makes the next comparison whole",
            # D60 and D61
            "`- **Scope:** <slice ids, comma-separated> | global`", "check-decisions.py --scope <slice-id>",
            "**Catch-up.**", "`slipwai migrate` merges the new entry shape beside what the project wrote there",
        ):
            with self.subTest(part):
                self.assertTrue(part in text, f"the fragment does not say: {part}")
