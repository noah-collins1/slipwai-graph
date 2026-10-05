"""R11 of S06-scoped-gate: the ladder, the settings, the templates and the briefs say the scoped gate.

The scoped gate runs immediately before a slice's first push; the full gate runs at the merge root and in CI (D123).
No text the ladder writes types the job flag (D124).
"""
from __future__ import annotations

import re
import unittest

from slipwai.layout import AT_ROOT, Layout
from slipwai.scaffold import project_files
from slipwai.services import App

PRINCIPLE_V = (
    "The branch's scoped gate MUST be green immediately before that first implementation push: it runs every check "
    "that reads a file changed since the trunk commit the branch is built on, or a tool, a variable or an ignored "
    "file that differs from the branch's last green full gate, and it is the full gate wherever it cannot tell; a "
    "check it skips is taken as passing because the trunk passed it. The full gate MUST be green at the merge root "
    "and in CI before anything lands on trunk."
)
PLANNING = (
    "After demo acceptance, immediately before the first implementation push, widen to the affected suites, "
    "verify static analysis, run the repository's scoped gate where it has one and its full gate otherwise, "
    "then run the end-of-phase mutation gate once where required and present its final report (or the reviewed "
    "alternate-evidence record and `N/A` rationale). The full gate runs at the merge root and in CI."
)
IMPLEMENT = (
    "do not push, and do not widen to affected suites, static analysis or `{make} verify-scoped`. Those checks "
    "belong immediately before the first implementation push, which happens after demo acceptance; the full "
    "`{make} verify` runs at the merge root."
)
CONVERGE = (
    "Do not run `{make} verify-scoped` or `{make} verify`: the scoped gate runs after demo acceptance, "
    "immediately before the implementation is pushed, and the full gate at the merge root."
)


def flat(text: str) -> str:
    return " ".join(text.split())


def generated(profile: str, layout: Layout) -> dict[str, str]:
    apps = [App("shop", "apps/shop", "service", "python", None, 0)]
    return project_files("shop", profile, "none", apps, layout)


def find(files: dict[str, str], suffix: str) -> str:
    (name,) = [name for name in files if name.endswith(suffix)]
    return files[name]


class ScopedLadderTest(unittest.TestCase):
    def each(self) -> list[tuple[str, Layout, dict[str, str]]]:
        return [
            (profile, layout, generated(profile, layout))
            for profile in ("standard", "event-modelling")
            for layout in (AT_ROOT, Layout("delivery"))
        ]

    def test_drive_ladder_starts_and_pushes_scoped_and_keeps_the_full_gate_at_phase_four(self) -> None:
        for _, _, files in self.each():
            drive = flat(find(files, "commands/drive.md"))
            self.assertIn("Start the slice from a green `make verify-scoped`.", drive)
            self.assertIn("runs `codegraph sync`, then `make verify-scoped`, then the first push", drive)
            self.assertNotIn("start from a green `make verify`", drive.lower())
            self.assertIn("then `make verify`", drive)  # Phase 4 on main

    def test_concurrent_slices_gate_before_the_push_is_scoped(self) -> None:
        for _, layout, files in self.each():
            drive = flat(find(files, "commands/drive.md"))
            if "Demo on the slice branch" not in drive:
                continue
            self.assertIn(f"`{layout.make} verify-scoped` green, then push the slice's commits", drive)
            self.assertIn(f"`{layout.make} verify`, marking the slice done", drive)

    def test_settings_allow_the_scoped_gate_beside_the_full_one(self) -> None:
        files = generated("standard", AT_ROOT)
        settings = find(files, ".claude/settings.json")
        self.assertIn('"Bash(make verify)"', settings)
        self.assertIn('"Bash(make verify-scoped)"', settings)

    def test_constitution_templates_carry_the_scoped_principle(self) -> None:
        for _, _, files in self.each():
            text = flat(find(files, "constitution-template.md"))
            self.assertIn(PRINCIPLE_V, text)
            self.assertNotIn("The whole suite MUST be green immediately before that first implementation push", text)
            self.assertIn("immediately before that first implementation push", text)

    def test_planning_skill_and_briefs_say_the_scoped_gate(self) -> None:
        for _, layout, files in self.each():
            planning = flat(find(files, "skills/planning/SKILL.md"))
            self.assertIn(PLANNING, planning)
            self.assertIn("After demo acceptance", planning)
            implement = flat(find(files, "agents/drive-implement.md"))
            self.assertIn(IMPLEMENT.format(make=layout.make), implement)
            converge = flat(find(files, "agents/drive-converge.md"))
            self.assertIn(CONVERGE.format(make=layout.make), converge)

    def test_no_ladder_line_types_the_job_flag(self) -> None:
        for _, _, files in self.each():
            for name, text in files.items():
                if not re.search(r"(commands|agents)/[^/]+\.md$|settings\.json$", name):
                    continue
                self.assertNotRegex(text, r"make -j|(?<![\w-])-j(?![\w-])", name)


if __name__ == "__main__":
    unittest.main()
