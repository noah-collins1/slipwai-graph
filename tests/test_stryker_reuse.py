"""S41 T036 (A1 · D212 item 7, AC-S41-4): a green never rests on results an earlier run left.

`incremental: true` in a service's `stryker.config.json` makes Stryker reuse the kills of an earlier run
(`reports/stryker-incremental.json`), so a test helper gutted since still passes. The wrapper closes every route by
which an earlier run's result reaches this one: `--force` (Stryker's own "run all mutants even if an incremental file
exists") on every run, and the file removed with the report, wherever the config says it is.
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

from test_stryker_verdict import SERVICE, VerdictCase, mutant, report

sys.dont_write_bytecode = True
TEST_SELECTION = {"reads": ["assets/languages/typescript/scripts/stryker-mutation.py",
                            "assets/toolkit/scripts/check-styles.py"]}
KILLED = {"report": report(src__calc_ts=[mutant("Killed")])}


class ReuseTest(VerdictCase):
    def service(self, *parts: str) -> Path:
        return self.tree.joinpath(SERVICE, *parts)

    def configure(self, **options: object) -> None:
        config = json.loads(self.service("stryker.config.json").read_text(encoding="utf-8"))
        self.service("stryker.config.json").write_text(json.dumps({**config, **options}), encoding="utf-8")

    def leave(self, *parts: str) -> Path:
        left = self.service(*parts)
        left.parent.mkdir(parents=True, exist_ok=True)
        left.write_text('{"files": {}}', encoding="utf-8")
        return left

    def test_e1_every_run_forces_all_mutants_so_nothing_is_reused(self) -> None:
        self.configure(incremental=True)
        for files in (("--file", "src/calc.ts"), ()):
            with self.subTest(files=files):
                self.log.unlink(missing_ok=True)
                code, lines = self.run_wrapper(KILLED, *files)
                self.assertEqual(code, 0, lines)
                self.assertIn("--force", self.execs()[0]["argv"])

    def test_e2_the_incremental_file_goes_with_the_report(self) -> None:
        self.configure(incremental=True)
        left = self.leave("reports", "stryker-incremental.json")
        self.run_wrapper({**KILLED, "expect_clean": True}, "--file", "src/calc.ts")
        self.assertFalse(left.exists(), "the earlier run's incremental file is still there")
        self.assertFalse(Path(str(self.log) + ".dirty").exists(), "Stryker found the earlier run's incremental file")

    def test_e3_an_incremental_file_the_config_names_goes_too_and_one_outside_the_service_stays(self) -> None:
        self.configure(incremental=True, incrementalFile="reports/elsewhere/last.json")
        named = self.leave("reports", "elsewhere", "last.json")
        outside = self.tree / "outside.json"
        outside.write_text("{}", encoding="utf-8")
        self.run_wrapper(KILLED, "--file", "src/calc.ts")
        self.assertFalse(named.exists())
        self.configure(incrementalFile="../../outside.json")
        self.run_wrapper(KILLED, "--file", "src/calc.ts")
        self.assertTrue(outside.exists(), "a path outside the service is not the wrapper's to delete")


if __name__ == "__main__":
    unittest.main()
