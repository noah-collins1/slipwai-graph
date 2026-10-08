"""S27's after-converge audit gaps (T029, T033; D207, AC-S27-22): the audit reads `Status` as the gate does, and reads
every feature's log, with or without `--feature`."""
from __future__ import annotations

import sys
import unittest

from provisional_fixture import EASY_LINE, audit, entry, gate

sys.dont_write_bytecode = True

PROVISIONAL = "provisional · ratify by 2026-10-14"


def waiting(number: int = 1, status: str = PROVISIONAL) -> str:
    return entry(number, status, revert="own", reversibility=EASY_LINE)


class AuditReadsStatusAsTheGateDoesTest(unittest.TestCase):
    def test_t029_e1_a_status_label_with_a_space_before_the_colon_is_the_gates_status_and_the_audits(self) -> None:
        """Beside a real `ratified` entry the gate takes the near-miss label as the `Status` it reads; so does the
        audit (alone, the gate refuses such an entry, and the audit stays with it)."""
        near = waiting(2).replace("**Status:**", "**Status :**")
        log = entry(1, "ratified 2026-10-09", reversibility=EASY_LINE) + near
        self.assertEqual(0, gate(log).returncode, "the gate reads D2 as a provisional entry and finds it sound")
        result = audit(log)
        self.assertEqual((3, "cruise: parked: ratify D2 in specs/f/decisions.md\n"), (result.returncode, result.stdout))

    def test_t029_e2_a_status_that_only_starts_with_the_word_is_not_provisional_to_either(self) -> None:
        log = waiting(status="provisionally maybe")
        self.assertEqual(1, gate(log).returncode)
        self.assertEqual(0, audit(log).returncode)

    def test_t029_e3_only_the_first_status_of_an_entry_counts(self) -> None:
        twice = entry(1, "standing") + "- **Status:** " + PROVISIONAL + "\n"
        self.assertEqual(0, audit(twice).returncode)
        first = waiting() + "- **Status:** standing\n"
        self.assertEqual(3, audit(first).returncode)


class AuditReadsEveryFeaturesLogTest(unittest.TestCase):
    """T033 (D207, AC-S27-22)."""

    def logs(self) -> dict[str, str]:
        return {"alpha": entry(1) + waiting(2), "beta": waiting(1, "provisional · ratify by 2026-10-14")}

    def test_t033_e1_with_or_without_a_feature_the_lowest_numbered_entry_is_named_with_its_feature(self) -> None:
        for arguments in ((), ("--feature", "alpha"), ("--feature", "beta")):
            result = audit(self.logs(), *arguments)
            self.assertEqual((3, "cruise: parked: ratify D1 in specs/beta/decisions.md\n"),
                             (result.returncode, result.stdout), (arguments, result.stderr))

    def test_t033_e2_a_tie_on_the_number_goes_to_the_first_feature_by_name(self) -> None:
        result = audit({"beta": waiting(1), "alpha": waiting(1)})
        self.assertEqual("cruise: parked: ratify D1 in specs/alpha/decisions.md\n", result.stdout)

    def test_t033_e3_the_feature_chosen_may_be_clean_and_another_still_parks_the_run(self) -> None:
        result = audit({"alpha": entry(1), "beta": waiting(3)}, "--feature", "alpha")
        self.assertEqual((3, "cruise: parked: ratify D3 in specs/beta/decisions.md\n"),
                         (result.returncode, result.stdout))

    def test_t033_e4_every_log_ratified_is_exit_zero_naming_the_logs_read(self) -> None:
        result = audit({"alpha": entry(1), "beta": entry(1, "ratified 2026-10-09")})
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("specs/alpha/decisions.md", result.stdout)
        self.assertIn("specs/beta/decisions.md", result.stdout)

    def test_t033_e5_a_feature_naming_no_directory_stays_exit_two(self) -> None:
        for arguments in (("--feature", "nope"), ("--feature", "")):
            result = audit(self.logs(), *arguments)
            self.assertEqual((2, ""), (result.returncode, result.stdout), arguments)
            self.assertEqual(1, len(result.stderr.strip().splitlines()), result.stderr)
