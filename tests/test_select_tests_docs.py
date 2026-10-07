"""`docs/maintaining.md` says what `make test` does on a slice branch (S38, D156 point 6).

The page is read as text. Each term a maintainer needs is held on its own, so a missing one fails by name.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "docs" / "maintaining.md"


def verify_section() -> str:
    text = PAGE.read_text(encoding="utf-8")
    match = re.search(r"^## Verify it\n(.*?)(?=^## )", text, re.S | re.M)
    assert match, "docs/maintaining.md has no `## Verify it` section"
    return match.group(1)


def flat(text: str) -> str:
    return re.sub(r"\s+", " ", text)


class MaintainingPageSaysWhatMakeTestDoes(unittest.TestCase):
    def setUp(self) -> None:
        self.section = verify_section()
        self.prose = flat(self.section)

    def assertSays(self, term: str) -> None:
        self.assertTrue(term in self.prose, f"*Verify it* in docs/maintaining.md does not say `{term}`")

    def assertSaysLike(self, pattern: str) -> None:
        self.assertIsNotNone(re.search(pattern, self.prose), f"*Verify it* does not say anything like /{pattern}/")

    def test_names_the_selector(self) -> None:
        self.assertSays("select-tests.py")

    def test_names_since(self) -> None:
        self.assertSays("SINCE")

    def test_since_defaults_to_the_trunk(self) -> None:
        self.assertSaysLike(r"(?i)defaults? to the trunk|the trunk by default|the trunk\b.*default")

    def test_says_when_to_set_since(self) -> None:
        self.assertSaysLike(r"(?i)cut from a branch other than the trunk")
        self.assertSaysLike(r"(?i)tip passed the full suite")

    def test_names_full(self) -> None:
        self.assertSays("FULL=1")

    def test_names_dry_run_and_replay(self) -> None:
        self.assertSays("--dry-run")
        self.assertSays("--replay")

    def test_says_how_a_module_declares(self) -> None:
        self.assertSays("TEST_SELECTION")

    def test_says_every_skip_is_named(self) -> None:
        self.assertSaysLike(r"(?i)names every (module it )?skips?|every skip|every one it skips")

    def test_says_selection_is_for_slice_branches_only(self) -> None:
        self.assertSaysLike(r"slice/<id>")
        self.assertSaysLike(r"(?i)\bCI\b")

    def test_names_what_turns_selection_off(self) -> None:
        for name in ("TESTS", "SKIP", "FACTORY_BACKENDS"):
            self.assertSays(name)
        self.assertSaysLike(r"(?i)turns? selection off")

    def test_says_verify_stays_whole(self) -> None:
        self.assertSaysLike(r"(?i)`make verify` (always )?runs every module")

    def test_no_longer_says_the_patch_is_pending(self) -> None:
        self.assertNotIn("s38.patch", self.prose)
        self.assertIsNone(re.search(r"(?i)until .*patch.* applied", self.prose))

    def test_says_what_make_test_does_on_a_slice_branch(self) -> None:
        self.assertSaysLike(r"`make test` (on a slice branch )?prints .*selected N of M modules.* runs only")


if __name__ == "__main__":
    unittest.main()
