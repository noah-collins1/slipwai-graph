"""T017 (AC-S07-8): `check-constitution` reads `skills/*/SKILL.md`, and that never changes its exit status.

`present_practice` tests each skill a requirement points at for existence, inside `findings()`, and only for a
requirement whose signals are not all present: a requirement already reported as a failure. So deleting the skills turns
`; see skills/…/SKILL.md` into nothing in the failure text and leaves the verdict where it was, for a constitution that
fails and for one that passes. That is why `skills/` is not on the row (`NOT_AN_INPUT_PATTERN_FOR`'s reason says so).
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from test_verify_scoped_flips import DRAFT, put, run
from test_verify_scoped_record import RecordCase

sys.dont_write_bytecode = True

SEE = re.compile(r"; see skills/[^\n]*")
CONSTITUTION = ".specify/memory/constitution.md"


class PracticeTest(RecordCase):
    def check(self, project: Path) -> subprocess.CompletedProcess[str]:
        return run(project, "python3", "-B", "scripts/check-constitution.py")

    def without_skills(self, project: Path) -> None:
        skills = sorted((project / "skills").glob("*/SKILL.md"))
        self.assertTrue(skills)
        for skill in skills:
            skill.unlink()

    def test_deleting_the_skills_changes_only_the_failure_text_of_a_failing_constitution(self) -> None:
        project = self.project("model-typescript-web")
        put(project, CONSTITUTION, DRAFT)
        before = self.check(project)
        self.assertEqual(before.returncode, 1, before.stdout + before.stderr)
        self.assertRegex(before.stderr, SEE)
        self.without_skills(project)
        after = self.check(project)
        self.assertEqual(after.returncode, before.returncode, after.stdout + after.stderr)
        self.assertNotRegex(after.stderr, SEE)
        self.assertEqual(after.stderr, SEE.sub("", before.stderr), "more than the pointers changed")

    def test_deleting_the_skills_leaves_a_passing_constitution_passing_with_the_same_words(self) -> None:
        project = self.project("model-typescript-web")
        asked = run(project, "python3", "-B", "scripts/check-constitution.py", "--requirements")
        self.assertEqual(asked.returncode, 0, asked.stderr)
        put(project, CONSTITUTION, asked.stdout)
        before = self.check(project)
        self.assertEqual(before.returncode, 0, before.stdout + before.stderr)
        self.without_skills(project)
        after = self.check(project)
        self.assertEqual((after.returncode, after.stdout, after.stderr), (0, before.stdout, before.stderr))
