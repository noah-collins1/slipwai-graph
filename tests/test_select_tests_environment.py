"""What the selector leaves out of the environment it hands the tests (S38 T042, demo 1's finding).

`make test SINCE=<ref>` is exported by make into the recipe and into `MAKEFLAGS`; a test that builds a project and runs
`make mutation` there would read the factory's `SINCE` as its own. The process the selector starts holds neither
`SINCE` nor `FULL`, in either place, and still holds what the tests do read.
"""
from __future__ import annotations

import sys

from select_fixture import SelectCase

sys.dont_write_bytecode = True

NAMES = ("SINCE", "FULL", "MAKEFLAGS", "MFLAGS", "KEPT")
PROBE = ("import os\nimport unittest\n\n\nclass Case(unittest.TestCase):\n    def test_it(self):\n"
         "        with open(os.environ['STANDIN_LOG'], 'a', encoding='utf-8') as log:\n"
         "            log.write('env\\t' + repr({n: os.environ.get(n) for n in " + repr(NAMES) + "}) + '\\n')\n")


class TestTheTestProcessHoldsNoSelectionKnob(SelectCase):
    def seen(self) -> dict[str, str | None]:
        lines = [line for line in self.ran() if line.startswith("env\t")]
        self.assertEqual(len(lines), 1, lines)
        return eval(lines[0].split("\t", 1)[1])  # noqa: S307 - the repr this test's own probe wrote

    def selected_run(self) -> None:
        self.write("tests/test_probe.py", PROBE)
        self.commit("probe")
        self.branch("slice/x")
        self.write("docs/note.md", "changed\n")

    def test_a_selected_run_sees_neither_since_nor_full_in_the_environment_or_the_flags(self) -> None:
        self.selected_run()
        done = self.make("test", "SINCE=HEAD", KEPT="yes", MAKEFLAGS="SINCE=HEAD -- SINCE=HEAD", MFLAGS="-- SINCE=HEAD")
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        seen = self.seen()
        self.assertEqual({name: seen[name] for name in NAMES if name != "KEPT"}, dict.fromkeys(NAMES[:4]), seen)
        self.assertEqual(seen["KEPT"], "yes")

    def test_a_full_run_sees_neither_either(self) -> None:
        self.selected_run()
        done = self.selector(SINCE="HEAD", FULL="1", MAKEFLAGS=" SINCE=HEAD FULL=1 -- SINCE=HEAD FULL=1")
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        seen = self.seen()
        self.assertEqual({name: seen[name] for name in NAMES[:4]}, dict.fromkeys(NAMES[:4]), seen)

    def test_make_flags_that_are_not_the_selection_stay(self) -> None:
        self.selected_run()
        done = self.selector(SINCE="HEAD", MAKEFLAGS="-j4 SINCE=HEAD -- SINCE=HEAD KEEP=1", MFLAGS="-j4")
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        seen = self.seen()
        self.assertEqual(seen["MAKEFLAGS"], "-j4 -- KEEP=1")
        self.assertEqual(seen["MFLAGS"], "-j4")
