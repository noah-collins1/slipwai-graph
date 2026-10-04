"""R1 (AC-S03-1, -18, -19): a pass is recorded and reused, saying so in one line.

Every "no check ran" here is read from the stand-ins' log (`stamp_fixture.checks_started`), never from what the
run printed: a line on the screen says what the script chose to say, the log says what started.
"""
from __future__ import annotations

import json
import re

from stamp_fixture import CLOSING, INSTANT, StampTestCase

FIELDS = ("key", "tree", "scripts", "tools", "passed", "result")


class ReuseTest(StampTestCase):
    def test_the_second_run_prints_one_line_of_its_own_and_starts_no_check(self) -> None:
        """e1: nothing changed between two runs; the second says so, in one line carrying the five facts."""
        first = self.run_gate()
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        self.assertTrue(self.checks(), "the first run started no check at all")
        self.forget_log()
        second = self.run_gate()
        self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
        self.assertEqual(self.checks(), [], "a check started on a tree that already passed")
        lines = [line for line in second.stdout.splitlines() if line.strip()]
        self.assertEqual(len(lines), 1, second.stdout)
        line = lines[0]
        stamp = self.stamp()
        self.assertTrue(line.startswith("verify: "), line)
        self.assertIn("did not run", line)
        self.assertIn("already passed", line)
        self.assertEqual(INSTANT.findall(line), [stamp["passed"]], line)
        abbreviated = re.findall(r"\b[0-9a-f]{7,}\b", line)
        self.assertEqual(len(abbreviated), 1, line)
        self.assertTrue(str(stamp["key"]).startswith(abbreviated[0]), line)
        self.assertIn("VERIFY_FORCE=1", line)

    def test_the_closing_line_is_the_full_runs_alone(self) -> None:
        """A full passing run ends with the closing line, byte for byte, and says nothing of a stamp; a reuse never
        prints it."""
        first = self.run_gate()
        self.assertTrue(first.stdout.endswith(f"\n\n{CLOSING}\n"), first.stdout[-200:])
        self.assertEqual(self.reuse_lines(first), [])
        second = self.run_gate()
        self.assertNotIn("all gates passed", second.stdout)
        self.assertEqual(second.stderr, "")

    def test_the_stamp_is_plain_text_with_its_fields(self) -> None:
        """e18: the five fields of the entity, and the key they make, readable by a person."""
        self.run_gate()
        path = self.stamp_path()
        self.assertIsNotNone(path, "a passing run wrote no stamp")
        assert path is not None
        text = path.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("{\n"), text)
        stamp = json.loads(text)
        self.assertEqual(sorted(stamp), sorted(FIELDS))
        self.assertEqual(stamp["result"], "pass")
        self.assertRegex(str(stamp["passed"]), INSTANT)
        for part in ("key", "tree", "scripts"):
            self.assertRegex(str(stamp[part]), r"^[0-9a-f]{64}$", part)
        self.assertIsInstance(stamp["tools"], dict)

    def test_a_stamp_missing_a_field_or_cut_short_is_no_stamp(self) -> None:
        """e18: one field removed, or the file cut short, and the full gate runs and writes a whole stamp."""
        self.run_gate()
        path = self.stamp_path()
        self.assertIsNotNone(path, "a passing run wrote no stamp")
        assert path is not None
        whole = path.read_text(encoding="utf-8")
        damaged = {f"without {field}": json.dumps({k: v for k, v in json.loads(whole).items() if k != field})
                   for field in FIELDS}
        damaged["cut short"] = whole[: len(whole) // 2]
        damaged["empty"] = ""
        for name, text in damaged.items():
            with self.subTest(name):
                path.write_text(text, encoding="utf-8")
                self.forget_log()
                run = self.run_gate()
                self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
                self.assertTrue(self.checks(), "no check started: the damaged stamp was reused")
                self.assertEqual(self.reuse_lines(run), [])
                self.assertTrue(run.stdout.endswith(f"{CLOSING}\n"))
                self.assertEqual(sorted(self.stamp()), sorted(FIELDS))

    def test_the_evidence_is_the_log_and_not_what_the_run_printed(self) -> None:
        """e19: with a run's output thrown away, the log still says a check started on a full run and none on a
        reuse; and the reader takes a log, not an output."""
        self.run_gate()
        full = self.checks()
        self.assertTrue(any(line.startswith("uv\tsync") for line in full), full)
        self.assertTrue(any("scripts/check-imports.py" in line for line in full), full)
        self.forget_log()
        self.run_gate()
        self.assertEqual(self.checks(), [])
