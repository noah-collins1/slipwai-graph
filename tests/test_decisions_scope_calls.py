"""The calls `check-decisions.py` answers, and the log it cannot read (D63, AC-S02-84 to -86; adversary C4, C5, C6, C9).

A call the script did not understand is usage and exit 2, never a green run of something else; a block the verb
cannot place under a heading it can read is printed and counted, and the verb then says the log does not pass; a log
that is not UTF-8 is one line naming it. With no argument, and with `--adversary-baseline`, the script does what it did.
"""
from __future__ import annotations

import subprocess
import tempfile
import unittest

from test_decisions_scope import SCRIPT, SLICE, entry, printed, run, scratch
from test_decisions_scope_gate import released_checker

TEST_SELECTION: dict[str, object] = {
    "reads": ["assets/toolkit/scripts/check-decisions.py", "assets/toolkit/scripts/check-styles.py"],
}


def text(log: str) -> bytes:
    return ("# Decisions\n\n" + log).encode("utf-8")


USAGE = "usage: check-decisions.py [--scope <slice-id> [--feature <name>] | --adversary-baseline | --help]\n"


class UnderstoodCallsTest(unittest.TestCase):
    def usage(self, *args: str) -> None:
        # a log the gate would refuse, so a gate run in the verb's place shows as a different stderr
        with tempfile.TemporaryDirectory() as directory:
            result = run(scratch(directory, entry(1, "the runner")), *args)
        self.assertEqual(2, result.returncode, (args, result.stdout, result.stderr))
        self.assertEqual("", result.stdout, args)
        self.assertEqual(USAGE, result.stderr, args)

    def test_e84_a_scope_value_that_is_not_id_shaped_is_usage_and_exit_two(self) -> None:
        for value in ("", "s02", "s02-runner-bookkeeping", f"{SLICE} ", f" {SLICE}", f"slices/{SLICE}", "--feature",
                      "S02,S03", "S02\n", "*", "S", "02", "S02-", "S０２"):
            self.usage("--scope", value)

    def test_e84_an_argument_the_script_does_not_know_is_usage_and_exit_two(self) -> None:
        for args in (["--scope=S02"], ["-scope", "S02"], ["S02"], ["--bogus"], ["--scope"], ["--feature", "f"],
                     ["--scope", "S02", "--feature"], ["--scope", "S02", "--scope", "S03"],
                     ["--scope", "S02", "--feature", "f", "extra"], ["--scope", "S02", "--bogus", "x"],
                     ["--adversary-baseline", "--scope", "S02"], ["--adversary-baseline", "x"], ["--help", "x"],
                     ["--scope", "S02", "--feature", "--scope"], ["-h"], [""]):
            self.usage(*args)

    def test_e84_help_prints_the_usage_and_exits_zero(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = run(scratch(directory, entry(1, "the runner")), "--help")
        self.assertEqual((0, USAGE, ""), (result.returncode, result.stdout, result.stderr))

    def test_e84_a_well_formed_call_in_either_order_still_runs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = scratch(directory, entry(1, SLICE))
            for args in (["--scope", SLICE], ["--scope", "S2", "--feature", "f"], ["--feature", "f", "--scope", "S02"]):
                result = run(repo, *args)
                self.assertEqual((0, ["D1"]), (result.returncode, printed(result)), (args, result.stderr))

    def test_e84_hold_no_argument_and_the_baseline_answer_as_the_released_checker_did(self) -> None:
        with tempfile.TemporaryDirectory() as other:
            released = released_checker(other)
            for args in ([], ["--adversary-baseline"]):
                seen = []
                for script in (released, SCRIPT):
                    with tempfile.TemporaryDirectory() as directory:
                        repo = scratch(directory, entry(1) + "\n" + entry(2), script=script)
                        (repo / "specs/f/slices").mkdir()
                        (repo / "specs/f/slices/README.md").write_text("| S1-a | done |\n", encoding="utf-8")
                        result = run(repo, *args)
                        log = repo / "specs/f/adversary-log.md"
                        written = log.read_text(encoding="utf-8") if log.exists() else None
                        seen.append((result.returncode, result.stdout, result.stderr, written))
                self.assertEqual(seen[0], seen[1], args)


class ABlockTheVerbCannotReadTest(unittest.TestCase):
    def verb(self, log: bytes) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as directory:
            repo = scratch(directory, "")
            (repo / "specs/f/decisions.md").write_bytes(log)
            return run(repo, "--scope", SLICE)

    def check(self, result: subprocess.CompletedProcess[str], block: str, carried: int, of: int) -> None:
        self.assertEqual(1, result.returncode, result.stdout)
        self.assertIn(block, result.stdout)
        closing = result.stdout.splitlines()[-1]
        self.assertIn(f"carried {carried} of {of} entries for {SLICE}", closing)
        self.assertIn("1 carried for want of a heading it can read", closing)
        headings = [line for line in result.stdout.splitlines() if line.lstrip("\ufeff").startswith("## ")]
        self.assertEqual(carried, len(headings), result.stdout)
        lines = result.stderr.strip().splitlines()
        self.assertEqual(1, len(lines), result.stderr)
        self.assertIn("does not pass check-decisions", lines[0])

    def test_e85_a_heading_written_with_a_hyphen_after_an_out_of_scope_entry_is_printed_and_counted(self) -> None:
        bad = entry(2, SLICE).replace("## D2 — ", "## D2 - ")
        result = self.verb(text(entry(1, "S05-other") + "\n" + bad + "\n" + entry(3, "global")))
        self.check(result, bad.strip(), carried=2, of=3)

    def test_e85_an_overridden_out_of_scope_entry_under_a_bad_heading_is_not_hidden_in_the_one_before(self) -> None:
        bad = entry(2, "S05-other", status="overridden by D3").replace("## D2 — ", "## D2: ")
        result = self.verb(text(entry(1, "global") + "\n" + bad + "\n" + entry(3, "global")))
        self.check(result, bad.strip(), carried=3, of=3)
        self.assertEqual(1, result.stdout.count("## D1 — "))

    def test_e85_a_byte_order_mark_before_the_first_entry_is_read_past_and_the_entry_printed_and_counted(self) -> None:
        result = self.verb(b"\xef\xbb\xbf" + (entry(1, SLICE) + "\n" + entry(2, "S05-other")).encode("utf-8"))
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(["D1"], printed(result))
        self.assertIn(f"carried 1 of 2 entries for {SLICE}: 1 in scope", result.stdout.splitlines()[-1])
        self.assertEqual("", result.stderr)

    def test_e85_the_gate_refuses_a_log_with_such_a_block_too(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = scratch(directory, entry(1, "global") + "\n" + entry(2, "global").replace("## D2 — ", "## D2 - "))
            gate = run(repo)
        self.assertEqual(1, gate.returncode)
        self.assertIn("a heading that is not `## D<n> — <question>`", gate.stderr)


class ALogThatIsNotUtf8Test(unittest.TestCase):
    def one_line(self, result: subprocess.CompletedProcess[str], name: str) -> None:
        self.assertEqual(1, result.returncode, result.stdout)
        lines = result.stderr.strip().splitlines()
        self.assertEqual(1, len(lines), result.stderr)
        self.assertIn(name, lines[0])
        self.assertIn("not UTF-8", lines[0])
        self.assertNotIn("Traceback", result.stderr)

    def test_e86_a_decisions_log_that_is_not_utf_8_is_one_line_for_the_gate_and_for_the_verb(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = scratch(directory, entry(1, SLICE).replace("because", "café"))
            path = repo / "specs/f/decisions.md"
            path.write_bytes(path.read_bytes().replace("é".encode(), b"\xe9"))
            self.one_line(run(repo), "specs/f/decisions.md")
            self.one_line(run(repo, "--scope", SLICE), "specs/f/decisions.md")

    def test_e86_a_demo_log_that_is_not_utf_8_is_one_line_for_the_gate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = scratch(directory, entry(1, "global"))
            log = (repo / "specs/f/slices/S1/demo-log.md")
            log.parent.mkdir(parents=True)
            log.write_bytes(b"# Demos\n\n\xff\xfe\n")
            self.one_line(run(repo), "specs/f/slices/S1/demo-log.md")


if __name__ == "__main__":
    unittest.main()
