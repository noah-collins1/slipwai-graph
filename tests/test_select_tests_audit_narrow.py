"""The reads-only audit covers what the run selected (S43 T003, D187 rule 4, AC-S43-13).

A selected run hands the modules it runs to the processes it starts as `SELECTED_TEST_MODULES`, and a full run hands
none (and removes one it was given). The audit narrows to the declared reads-only modules in it, and covers every
module its listing names where nothing, or nothing readable, was handed over. Three planted undeclared reads, each in
a changed place, are selected, audited and named.
"""
from __future__ import annotations

import ast
import sys
import tempfile
from pathlib import Path

from select_fixture import SelectCase
from select_fixture_declare import GO, DeclarationCase
from test_select_tests_real_audit import SCRATCH, SELECTED, audited, to_audit

sys.dont_write_bytecode = True

LOG = ("import os\nimport unittest\n\n\nclass Case(unittest.TestCase):\n    def test_it(self):\n"
       "        with open(os.environ['STANDIN_LOG'], 'a', encoding='utf-8') as log:\n"
       "            log.write('handed\\t{name}\\t' + repr(os.environ.get('SELECTED_TEST_MODULES')) + '\\n')\n")
DECLARED = "assets/toolkit/scripts/mutation-scope.py"  # a real file, which the planted module declares it reads
UNDECLARED = "scripts/publish-to-gitea.py"  # a real file, which it does not
HELPER = ('TEST_SELECTION = {{}}\nfrom pathlib import Path\n\n\ndef peek(path: str) -> None:\n    try:\n'
          '        Path(path).read_text()\n'
          '    except OSError:\n        pass\n\n\ndef extra() -> None:\n{body}')
PROBE = ('TEST_SELECTION = {{"reads": ["' + DECLARED + '"]}}\nimport os\nimport unittest\n\nfrom probe_helper import '
         'extra, peek\n\n\nclass Case(unittest.TestCase):\n    def test_it(self) -> None:\n'
         '        peek("' + DECLARED + '")\n{read}'
         '        if "STANDIN_LOG" in os.environ:\n'
         '            with open(os.environ["STANDIN_LOG"], "a", encoding="utf-8") as log:\n'
         '                log.write("handed\\t" + repr(os.environ.get("SELECTED_TEST_MODULES")) + "\\n")\n'
         '        extra()\n')
READ = f'        peek("{UNDECLARED}")\n'
NOTHING = "    pass\n"
EXTRA = f'    peek("{UNDECLARED}")\n'


class TestTheSelectorHandsDownWhatItRuns(DeclarationCase):
    GO_ONLY = '{"configurations": {"backend": ["go"]}}'
    SKIPPED = '{"reads": ["README.md"]}'

    def handed(self) -> dict[str, str | None]:
        found: dict[str, str | None] = {}
        for line in self.ran():
            if line.startswith("handed\t"):
                _, name, value = line.split("\t")
                found[name] = ast.literal_eval(value)
        return found

    def stand_ins(self, *paths: str) -> None:
        """`test_matrix` narrows to go, `test_other` is undeclared, `test_idle` reads a file."""
        self.write("README.md", "read\n")
        for name, selection in (("test_matrix", self.GO_ONLY), ("test_other", ""), ("test_idle", self.SKIPPED)):
            self.write(f"tests/{name}.py", (f"TEST_SELECTION = {selection}\n" if selection else "")
                       + LOG.format(name=name))
        self.slice_changing(*paths)

    def test_a_selected_run_hands_the_union_of_both_batches_to_each_module(self) -> None:
        self.stand_ins(GO)
        done = self.selector(SELECTED_TEST_MODULES="test_outside")
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertIn("narrowed test_matrix", done.stdout)
        self.assertIn("skipped test_idle", done.stdout)
        both = "test_matrix,test_other"
        self.assertEqual(self.handed(), {"test_matrix": both, "test_other": both})

    def test_a_full_run_hands_nothing_and_drops_one_it_inherited(self) -> None:
        self.stand_ins(GO)
        done = self.selector(FULL="1", SELECTED_TEST_MODULES="test_matrix")
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertEqual(self.handed(), dict.fromkeys(("test_matrix", "test_other", "test_idle")))

    def test_a_run_that_selects_nothing_still_drops_an_inherited_value(self) -> None:
        self.stand_ins("Makefile")  # a row that runs everything
        done = self.selector(SELECTED_TEST_MODULES="test_matrix")
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertEqual(set(self.handed().values()), {None})


class TestTheAuditNarrowsToWhatWasSelected(SelectCase):
    declared = {"test_one": ["a"], "test_two": ["b"], "test_three": []}

    def test_without_the_variable_every_declared_module_is_audited(self) -> None:
        self.assertEqual(to_audit(self.declared, {}), self.declared)

    def test_an_empty_or_unreadable_handoff_falls_back_to_every_module(self) -> None:
        for value in ("", " ", ",", " , "):
            with self.subTest(value):
                self.assertEqual(to_audit(self.declared, {SELECTED: value}), self.declared)

    def test_a_named_set_audits_the_declared_modules_in_it_only(self) -> None:
        self.assertEqual(to_audit(self.declared, {SELECTED: "test_two,test_other,test_three"}),
                         {"test_two": ["b"], "test_three": []})

    def test_the_real_listing_is_whole_when_nothing_is_handed(self) -> None:
        from test_select_tests_real_audit import reads_only
        listing = reads_only()
        self.assertEqual(to_audit(listing, {}).keys(), listing.keys())
        self.assertGreaterEqual(len(listing), 8)


class TestAPlantedUndeclaredReadIsSelectedAndAudited(DeclarationCase):
    modules = ()

    def plant(self, *, module: str = "", helper: str = NOTHING) -> None:
        self.write("tests/test_probe.py", PROBE.format(read=module))
        self.write("tests/probe_helper.py", HELPER.format(body=helper))
        self.write(DECLARED, "read\n")
        self.commit("trunk")
        self.branch("slice/x")

    def audit(self, expected: list[str]) -> None:
        """The module the selector ran is the one in the handed set, and the audit of it names the read."""
        self.log.write_text("", encoding="utf-8")
        done = self.selector()
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertNotIn("skipped test_probe", done.stdout)
        handed = [line.split("\t")[1] for line in self.ran() if line.startswith("handed\t")]
        self.assertEqual(handed, [repr("test_probe")])
        chosen = to_audit({"test_probe": [DECLARED], "test_unselected": []}, {SELECTED: "test_probe"})
        self.assertEqual(list(chosen), ["test_probe"])
        SCRATCH.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=SCRATCH) as directory:
            for name in ("test_probe.py", "probe_helper.py"):
                (Path(directory) / name).write_text((self.repo / "tests" / name).read_text(encoding="utf-8"),
                                                    encoding="utf-8")
            found = audited("test_probe", chosen["test_probe"], Path(directory))
        self.assertTrue(found["ok"], found)
        self.assertEqual(found["uncovered"], expected)

    def test_a_change_elsewhere_skips_the_module_so_it_is_not_audited(self) -> None:
        self.plant(module=READ)
        self.write("docs/note.md", "changed\n")
        done = self.selector()
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertIn("skipped test_probe", done.stdout)

    def test_a_read_in_the_changed_module_itself(self) -> None:
        self.plant()
        self.write("tests/test_probe.py", PROBE.format(read=READ))
        self.audit([UNDECLARED])

    def test_a_read_in_a_helper_of_its_closure(self) -> None:
        self.plant()
        self.write("tests/probe_helper.py", HELPER.format(body=EXTRA))
        self.audit([UNDECLARED])

    def test_a_read_in_a_module_whose_declared_file_changed(self) -> None:
        self.plant(module=READ)
        self.write(DECLARED, "changed\n")
        self.audit([UNDECLARED])
