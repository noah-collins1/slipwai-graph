"""`check-decisions.py --scope <slice-id>`: the standing decisions in scope for one slice (D60, AC-S02-47 to -54).

The verb reads the entries the gate already parses and prints those a slice's later decisions must agree with:
the ones that name the slice, the ones that are `global`, and the ones with no readable `Scope:` line, which are
carried as global because a filter that could hide a binding decision is the wrong one. Run in a scratch project
with the script copied beside a `project.json`, the way a generated project holds it.
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from slipwai.assets import ROOT

SCRIPT = ROOT / "assets/toolkit/scripts/check-decisions.py"
SLICE = "S02-runner-bookkeeping"


def entry(number: int, scope: str | None = None, status: str = "standing", stage_slice: str = "S1") -> str:
    """One decision entry in the shape `commands/cruise.md` shows; `scope=None` writes no `Scope:` line."""
    line = "" if scope is None else f"- **Scope:** {scope}\n"
    return (f"## D{number} — Question {number}\n"
            f"- **Stage:** plan · **Slice:** {stage_slice} · **When:** 2026-10-03T00:00Z · **Iteration:** 1\n{line}"
            f"- **Question:** what is {number}?\n- **Options:** a · b\n- **Decision:** a\n- **Why:** because\n"
            "- **Decided by:** drive-bosun\n- **Confidence:** high · **Would reverse if:** never\n"
            f"- **Written to:** `README.md`\n- **Status:** {status}\n")


def scratch(directory: str, *logs: str, script: Path = SCRIPT, names: tuple[str, ...] = ("f",)) -> Path:
    """A project holding the script and one `decisions.md` per name in `names` (each the text in `logs`)."""
    repo = Path(directory)
    (repo / "scripts").mkdir()
    shutil.copy(script, repo / "scripts/check-decisions.py")
    (repo / "project.json").write_text("{}\n", encoding="utf-8")
    (repo / "README.md").write_text("# scratch\n", encoding="utf-8")
    for name, text in zip(names, logs, strict=False):
        (repo / "specs" / name).mkdir(parents=True)
        (repo / "specs" / name / "decisions.md").write_text("# Decisions\n\n" + text, encoding="utf-8")
    return repo


def run(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["python3", "scripts/check-decisions.py", *args], cwd=repo, text=True, capture_output=True)


def printed(result: subprocess.CompletedProcess[str]) -> list[str]:
    """The numbers of the entries the verb printed, in the order printed."""
    return [line.split(" ")[1] for line in result.stdout.splitlines() if line.startswith("## D")]


class DecisionsScopeTest(unittest.TestCase):
    def verb(self, log: str, ident: str = SLICE) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as directory:
            return run(scratch(directory, log), "--scope", ident)

    def test_e47_a_hundred_entries_yield_the_fourteen_in_scope_or_global_verbatim_in_order(self) -> None:
        mine = [n for n in range(1, 101) if n % 10 == 0 and n <= 40]
        wanted = [n for n in range(1, 101) if n % 10 == 1 and n <= 100][:10]
        log = "\n".join(
            entry(n, SLICE if n in mine else "global" if n in wanted else "S11-render-once") for n in range(1, 101))
        result = self.verb(log)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual([f"D{n}" for n in sorted(mine + wanted)], printed(result))
        for n in mine + wanted:
            self.assertIn(entry(n, SLICE if n in mine else "global"), result.stdout)

    def test_e48_a_comma_separated_scope_is_printed_for_either_id_and_not_for_another(self) -> None:
        log = entry(1, f"{SLICE}, S14-result-contract")
        self.assertEqual(["D1"], printed(self.verb(log, SLICE)))
        self.assertEqual(["D1"], printed(self.verb(log, "S14-result-contract")))
        other = self.verb(log, "S11-render-once")
        self.assertEqual(0, other.returncode)
        self.assertEqual([], printed(other))

    def test_e49_a_bare_id_meets_a_slugged_one_on_its_head_and_s1_does_not_meet_s12(self) -> None:  # -81 amends -49
        log = entry(1, "S02") + "\n" + entry(2, "S12-model-sidecar")
        self.assertEqual(["D1"], printed(self.verb(log, SLICE)))
        self.assertEqual([], printed(self.verb(log, "S1")))
        self.assertEqual(["D2"], printed(self.verb(log, "S12")))

    def test_e50_an_entry_with_no_scope_line_is_printed_and_counted_as_carried_for_want_of_a_line(self) -> None:
        result = self.verb(entry(1) + "\n" + entry(2, "S11-render-once"))
        self.assertEqual(["D1"], printed(result))
        self.assertIn("1 carried as global for want of a line", result.stdout.splitlines()[-1])

    def test_e51_an_empty_or_unreadable_scope_is_printed_as_global(self) -> None:
        log = "\n".join([entry(1, ""), entry(2, "the runner"), entry(3, "global, S11-render-once")])
        result = self.verb(log)
        self.assertEqual(["D1", "D2", "D3"], printed(result))
        self.assertEqual(0, result.returncode)

    def test_e52_an_overridden_entry_is_not_printed_and_the_closing_line_names_what_overrode_it(self) -> None:
        log = "\n".join([entry(1, SLICE, "overridden by D9"), entry(2, SLICE, "overridden by human 2026-10-04"),
                         entry(3, SLICE)])
        result = self.verb(log)
        self.assertEqual(["D3"], printed(result))
        closing = result.stdout.splitlines()[-1]
        self.assertIn("D1 (overridden by D9)", closing)
        self.assertIn("D2 (overridden by human 2026-10-04)", closing)

    def test_e53_the_last_line_counts_carried_of_all_split_by_how_each_was_placed(self) -> None:
        log = "\n".join([entry(1, SLICE), entry(2, "global"), entry(3), entry(4, "S11-render-once"),
                         entry(5, "S11-render-once"), entry(6, SLICE, "overridden by D7")])
        closing = self.verb(log).stdout.splitlines()[-1]
        self.assertTrue(closing.startswith("check-decisions: "), closing)
        self.assertIn(f"carried 3 of 6 entries for {SLICE}", closing)
        self.assertIn("1 in scope, 1 global, 1 carried as global for want of a line", closing)
        self.assertIn("2 left out as out of scope", closing)

    def test_e54_a_slice_no_entry_names_gets_the_global_and_unscoped_entries_and_exit_zero(self) -> None:
        log = "\n".join([entry(1, "S11-render-once"), entry(2, "global"), entry(3)])
        result = self.verb(log, "S99-nothing-names-me")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(["D2", "D3"], printed(result))


if __name__ == "__main__":
    unittest.main()
