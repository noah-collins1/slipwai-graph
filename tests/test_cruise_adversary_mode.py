"""D208, D209 (adversary B3, B6, B7, B8): `mode` ignores a mode entry dated after now, and with several features and no
`--feature` prints the entry (numbered against every log, naming none) and exits 0; a second `"decide"` key in the
settings file is refused by `--check` and by `--set`; `guard` refuses a hard link to the settings file. Each runs the
toolkit's script as a subprocess in a scratch project, the way test_cruise_decide_ladder does."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True

from test_cruise_decide_ladder import BASE, ENTRY, SCRATCH, cruise, mode_project  # noqa: E402


class AdversaryModeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.addCleanup(shutil.rmtree, SCRATCH, True)

    def advance(self, project: Path, value: str) -> None:
        (project / ".specify/cruise.json").write_text(json.dumps({**BASE, "decide": value}) + "\n", encoding="utf-8")

    def test_a_mode_entry_dated_after_now_is_not_the_baseline(self) -> None:
        project = mode_project("provisional-shadow", "provisional-shadow")
        future = ENTRY.format(n=2, a="provisional-shadow", b="provisional").replace("2026-10-07T09:00:00Z",
                                                                                      "2999-01-01T00:00:00Z")
        log = project / "specs/f/decisions.md"
        log.write_text(log.read_text(encoding="utf-8") + "\n" + future, encoding="utf-8")
        self.advance(project, "provisional-advisory")
        result = cruise(project, "mode", "--feature", "f")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(result.stdout.startswith("## D3 — decide moved from provisional-shadow to "
                                                 "provisional-advisory\n"), result.stdout)
        self.assertIn("D2 in specs/f/decisions.md is dated after now (2999-01-01T00:00:00Z)", result.stderr)

    def test_a_future_mode_entry_does_not_let_a_hand_edit_skip_a_rung(self) -> None:
        project = mode_project("recommended-first", "provisional")
        future = ENTRY.format(n=2, a="recommended-first", b="provisional").replace("2026-10-07T09:00:00Z",
                                                                                     "2999-01-01T00:00:00Z")
        log = project / "specs/f/decisions.md"
        log.write_text(log.read_text(encoding="utf-8") + "\n" + future, encoding="utf-8")
        result = cruise(project, "mode", "--feature", "f")
        self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
        self.assertIn("cruise: parked: decide=provisional is more than one rung above recommended-first (D1)",
                      result.stdout)

    def test_several_features_and_no_feature_prints_the_entry_numbered_against_every_log_and_exits_0(self) -> None:
        project = mode_project("provisional-shadow", "provisional-shadow")
        (project / "specs/g").mkdir()
        (project / "specs/g/decisions.md").write_text(ENTRY.format(n=5, a="x", b="y").replace(
            "decide moved from x to y", "some other question"), encoding="utf-8")
        self.advance(project, "provisional-advisory")
        result = cruise(project, "mode")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(result.stdout.startswith("## D6 — decide moved from provisional-shadow to "
                                                 "provisional-advisory\n"), result.stdout)
        self.assertEqual(result.stderr, "")

    def test_a_second_decide_key_is_refused_by_check_and_by_set(self) -> None:
        project = mode_project(None, "recommended-first")
        path = project / ".specify/cruise.json"
        text = path.read_text(encoding="utf-8").replace('"decide": "recommended-first"',
                                                       '"decide": "recommended-first",\n  "decide": "provisional"')
        path.write_text(text, encoding="utf-8")
        for arguments in (("--check",), ("--set", "enabled=true"), ("mode",)):
            refused = cruise(project, *arguments)
            self.assertEqual(refused.returncode, 1, (arguments, refused.stdout))
            self.assertIn("names `decide` more than once", refused.stderr)
        self.assertEqual(path.read_text(encoding="utf-8"), text, "--set wrote through a file it could not read")

    def test_guard_refuses_a_hard_link_to_the_settings_file(self) -> None:
        project = mode_project(None, "recommended-first")
        os.link(project / ".specify/cruise.json", project / "elsewhere.json")
        event = json.dumps({"hook_event_name": "PreToolUse", "tool_name": "Write", "cwd": str(project),
                            "tool_input": {"file_path": "elsewhere.json", "content": "x"}})
        environment = {k: v for k, v in os.environ.items() if not k.startswith("CRUISE_")}
        refused = subprocess.run([sys.executable, "-B", "scripts/agents/cruise.py", "guard"], cwd=project, text=True,
                                 input=event, capture_output=True, env={**environment, "CRUISE_RUNNER": "1"})
        self.assertEqual(refused.returncode, 2, refused.stdout + refused.stderr)
        self.assertIn("`.specify/cruise.json` is the run's own setting", refused.stderr)
