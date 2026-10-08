"""S42 T027, T030 (gaps 6): every line `mutmut-mutation.py` prints has its fixed text in the table below.

The table is the factory's own contract for what the wrapper may say, held here and not in a slice's record under
`specs/`, so that archiving or moving a slice cannot fail the factory's suite. `<…>` is what a run fills in and `[…]`
what a line may or may not carry; a line that runs on is indented, and the table is read with its white space squashed.
A string the wrapper speaks that the table lacks is a line nobody has fixed.
"""
from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path

from slipwai.assets import LANGUAGE_ROOT

sys.dont_write_bytecode = True
SCRIPT = LANGUAGE_ROOT / "python" / "scripts/mutmut-mutation.py"
# `slipwai` reads `check-styles.py` on import (as `test_stryker_closure` does)
TEST_SELECTION = {"reads": ["assets/languages/python/scripts/mutmut-mutation.py",
                            "assets/toolkit/scripts/check-styles.py", "tests"]}
TABLE = """\
mutation: usage: mutmut-mutation.py <service> [<service> ...] [--file <path within the service> ...]
mutation: <s> swept, <r> refused; passed
mutation: <s> swept, <r> refused; failed: <service>, <service>
mutation: mutmut needs os.fork, which this host does not have; run it under WSL
mutation: uv is not on PATH; install it to run mutmut (see scripts/verify)
mutation: <service>/uv.lock does not agree with <service>/pyproject.toml; run uv lock --project <service>, then this
    again
mutation: uv sync --locked failed for <service> (exit <n>)[: <uv's last stderr line that is not a hint>]
mutation: mutmut <found or is not> installed in <service>'s environment[ (<the probe's last stderr line>)]; this
    wrapper runs mutmut 3.8.0: add mutmut==3.8.0 to the dev group of <service>/pyproject.toml and run uv lock
    --project <service> (slipwai migrate brings the wrapper for a newer pin)
mutation: <mutmut or libcst> is imported from <directory>, not from <service>'s environment; a package on PYTHONPATH
    ahead of the environment's is refused: remove it from PYTHONPATH
mutation: <service>/pyproject.toml: no [tool.mutmut] table
mutation: <PYTEST_* variable> is not passed to mutmut (it would change how every mutant's tests run); [tool.mutmut]
    pytest_add_cli_args is where this service adds pytest options
mutation: not mutated <service>/<file> — outside mutmut's configured targets
mutation: not mutated <service>/<file> — excluded by [tool.mutmut] source_paths (not under <roots>) | only_mutate (no
    pattern matches) | do_not_mutate "<pattern>"
mutation: nothing under <service> that was given is a file mutmut would mutate; no mutant to run
mutation: no mutant to run — <files>: mutmut found no function to mutate in it | them
mutation: scoped to <n> given file(s): <files> — <m> mutant(s)
mutation: mutmut exited <code> (its exit status and the output above are mutmut's, never the verdict; the .meta files
    are)
mutation: <service>/<file>:<line> holds "# pragma: no mutate <block|start|end>", which silences mutants nobody looked
    at; only a bare "# pragma: no mutate" on the line excuses one
mutation: <service>/pyproject.toml <setting> is <value found, or missing>, not <value held, or absent>, which narrows what
    the tests reach without anyone looking at it
mutation: <service>/pyproject.toml sets do_not_mutate_patterns, which silences every line a pattern matches without
    anyone looking at its mutants; only a bare "# pragma: no mutate" on the line excuses one
mutation: <service>/pyproject.toml sets mutate_only_covered_lines, which leaves out the mutants of every line coverage
    excludes without anyone looking at them
mutation: <service>/pyproject.toml sets max_stack_depth, which turns the survivors a test reaches through deeper calls
    into mutants no test reaches without anyone looking at them
mutation: <status> <service> <mutant name> (mutmut show <mutant name> in <service>; report <service>/mutants/)
mutation: mutmut found nothing to mutate in <service>; a pass on nothing is not a pass[, <n> file(s) excluded by
    [tool.mutmut]]
mutation: <n> mutants: <k> killed, <u> no tests (reported, never failed)[, <s> survived, …]; passed | failed — report
    <service>/mutants/[, <n> file(s) excluded by [tool.mutmut]]
mutation: another mutmut run of <service> holds <service>/.venv/mutmut-run.lock; wait for it, then run this again
mutation: mutmut could not generate mutants for <service> (exit <n>)[: <its last stderr line>]
mutation: <service>/mutants/ could not be removed; delete it, then run this again
mutation: <service>/<file>: mutmut's generation left an exit code on <n> mutant(s) before any test ran (a committed
    .meta file copied into mutants/?), so the verdict cannot be trusted
mutation: <service>/<file>: mutmut left no readable .meta, so nothing can be said of it
mutation: <service>/<file> cannot be read as UTF-8, so its pragmas cannot be checked
mutation: <service>/<file> cannot be read as Python, so its pragmas cannot be checked
mutation: `<service>/<file>` holds `<char>`, which mutmut reads as a pattern over mutant names; rename it, or run
    `make mutation-full`
mutation: <service>/pyproject.toml: <what is wrong>, which is one of:
    no tomllib: Python 3.11 or newer reads [tool.mutmut]
    is not valid TOML (<error>)
    cannot be read (<error>)
    source_paths must be a non-empty list of paths, not <value>
    source_paths holds <value>, which is not a relative directory of literal segments under the service
    only_mutate must be a list of strings, not <value>   (likewise do_not_mutate)
is not a uv lock: it has no [[package]] entries
unknown (exit <code>)
"""


def spoken() -> set[str]:
    """The fixed pieces of every string the wrapper prints or raises: f-string parts and the arguments of `say`, `note`
    and `Unreadable`."""
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    said = [n for n in ast.walk(tree) if isinstance(n, ast.JoinedStr)
            or isinstance(n, ast.Call) and getattr(n.func, "id", "") in ("say", "note", "Unreadable")]
    return {c.value.strip() for n in said for c in ast.walk(n) if isinstance(c, ast.Constant)
            and isinstance(c.value, str)} - {""}


class LinesTest(unittest.TestCase):
    def test_t027_every_line_the_wrapper_prints_has_its_fixed_text_in_the_table(self) -> None:
        table = " ".join(TABLE.split())
        self.assertEqual([piece for piece in sorted(spoken()) if piece not in table], [])

    def test_t030_no_mutmut_test_reads_a_slice_s_record_under_specs(self) -> None:
        needle = "specs" + "/0"  # built in parts, so that this file does not hold what it looks for
        holding = [path.name for path in sorted(Path(__file__).parent.glob("test_mutmut_*.py"))
                   if needle in path.read_text(encoding="utf-8")]
        self.assertEqual(holding, [])


if __name__ == "__main__":
    unittest.main()
