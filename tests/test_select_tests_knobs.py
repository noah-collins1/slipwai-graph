"""`SINCE` and `FULL` in any form never reach a module (S38 T051, adversary A2).

make records a command-line assignment in `MAKEFLAGS` as it was given — `SINCE:=main`, `SINCE::=main`, a value with a
space written `a\\ b` — and a test that builds a project and runs `make mutation` there reads it as its own. Every
assignment form is stripped whole, other variables are left whole, and the helper that spawns a generated project's
commands holds neither knob where the Makefile bypasses the selector (`TESTS`, `SKIP`).
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from select_fixture import SelectCase

from slipwai.assets import ROOT

sys.dont_write_bytecode = True

PROBE = ("import os\nimport unittest\n\n\nclass Case(unittest.TestCase):\n    def test_it(self):\n"
         "        with open(os.environ['STANDIN_LOG'], 'a', encoding='utf-8') as log:\n"
         "            log.write('flags\\t' + repr((os.environ.get('MAKEFLAGS'), os.environ.get('MFLAGS'))) + '\\n')\n")
FORMS = ("=", ":=", "::=", ":::=", "+=", "?=", "!=")
CASES = {  # MAKEFLAGS as make would write it -> what a module may see
    "-j4 -- SINCE=HEAD": "-j4",
    "-- FULL=1": None,
    "-- SINCE=a\\ b": None,
    "-- SINCE=a\\ b KEEP=x\\ y": "-- KEEP=x\\ y",
    "-- KEEP=x\\ y SINCE=a\\ \\ b FULL=1 OTHER=2": "-- KEEP=x\\ y OTHER=2",
    "-- SINCE=1 SINCEX=2 MYFULL=3": "-- SINCEX=2 MYFULL=3",
    **{f"-- SINCE{form}HEAD KEEP=1": "-- KEEP=1" for form in FORMS},
    **{f"-- FULL{form}1 KEEP=1": "-- KEEP=1" for form in FORMS},
}


class TestEveryFormOfAKnobIsStripped(SelectCase):
    def seen(self) -> tuple[str | None, str | None]:
        lines = [line for line in self.ran() if line.startswith("flags\t")]
        self.assertEqual(len(lines), 1, lines)
        found: tuple[str | None, str | None] = eval(lines[0].split("\t", 1)[1])  # noqa: S307 - our own repr
        return found

    def test_a_module_sees_no_knob_in_any_form_and_no_variable_split(self) -> None:
        self.write("tests/test_probe.py", PROBE)
        self.commit("probe")
        self.branch("slice/x")
        self.write("docs/note.md", "changed\n")
        for flags, kept in CASES.items():
            with self.subTest(flags):
                done = self.selector(SINCE="HEAD", MAKEFLAGS=flags)
                self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
                self.assertEqual(self.seen()[0], kept)


class TestAHelperRunningAGeneratedProjectHoldsNoKnob(SelectCase):
    """Where the Makefile bypasses the selector (`make test TESTS=… SINCE=…`) the modules still get make's exports; the
    tests' own helper is the last place the knobs can be removed before a generated project's commands start."""

    def test_the_suite_helper_clears_the_knobs_from_the_environment_and_the_flags(self) -> None:
        code = ("import os, support\nprint(repr([os.environ.get(n) for n in "
                "('SINCE', 'FULL', 'MAKEFLAGS', 'MFLAGS', 'KEPT')]))\n")
        env = dict(self.environment(), SINCE="HEAD", FULL="1", KEPT="yes", MAKEFLAGS="-j2 -- SINCE:=a\\ b FULL=1 K=1",
                   MFLAGS="-j2 -- SINCE=HEAD", PYTHONPATH=f"{ROOT / 'src'}:{ROOT / 'tests'}")
        done = subprocess.run(["python3", "-B", "-c", code], cwd=Path(os.devnull).parent, env=env, text=True,
                              capture_output=True, timeout=180)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(done.stdout.strip(), repr([None, None, "-j2 -- K=1", "-j2", "yes"]))
