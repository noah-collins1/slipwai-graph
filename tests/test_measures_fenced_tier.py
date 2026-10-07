"""T023 (finding B2): `measures.py` reads an entry's tier from the same lines the gate checks, so a `Reversibility:`
line inside a fenced code block (``` or ~~~) is not the entry's tier. Loaded by path with bytecode off."""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "assets/toolkit/scripts/agents/measures.py"


def measures() -> Any:
    spec = importlib.util.spec_from_file_location("measures_fenced_tier", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def tiers(text: str) -> list[Any]:
    return [found["tier"] for found in measures().decision_entries(text)]


class FencedTier(unittest.TestCase):
    def test_a_fenced_easy_line_is_not_the_tier_beside_a_real_hard_line(self) -> None:
        for fence in ("```", "~~~"):
            with self.subTest(fence=fence):
                text = (f"## D1 — a choice\n\nAn example:\n\n{fence}\n- **Reversibility:** easy\n{fence}\n\n"
                        "- **Reversibility:** hard — a published contract\n")
                self.assertEqual(tiers(text), ["hard"])

    def test_an_entry_holding_only_a_fenced_line_has_no_tier(self) -> None:
        for fence in ("```", "~~~"):
            with self.subTest(fence=fence):
                text = f"## D1 — a choice\n\n{fence}\n- **Reversibility:** easy\n{fence}\n"
                self.assertEqual(tiers(text), [None])

    def test_an_unclosed_fence_hides_the_rest_and_a_longer_fence_closes_only_on_its_own(self) -> None:
        text = ("## D1 — a\n\n````\n```\n- **Reversibility:** easy\n````\n- **Reversibility:** guarded\n\n"
                "## D2 — b\n\n```\n- **Reversibility:** hard\n")
        self.assertEqual(tiers(text), ["guarded", None])

    def test_an_unfenced_line_is_still_read(self) -> None:
        self.assertEqual(tiers("## D1 — a\n\n- **Reversibility:** easy\n"), ["easy"])


if __name__ == "__main__":
    unittest.main()
