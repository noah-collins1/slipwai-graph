"""The eight helpers under `tests/` say what they read, or stay undeclared for a stated reason (S38 T012, AC-S38-8).

Read over the real tree by the selector's own scan, in a `python3 -B` probe, so a declaration is held to the same
reading the selector gives it. A helper's declaration is a completeness claim; the claims below are what a reading of
each helper proves, and the three that are not declared are held undeclared so a later declaration is a decision.
"""
from __future__ import annotations

import json
import subprocess
import sys
import unittest

from slipwai.assets import ROOT

sys.dont_write_bytecode = True

PROBE = """
import json, sys
sys.path.insert(0, 'scripts')
from pathlib import Path
from select_tests import declarations
root = Path('.').resolve()
tree = declarations.scan(root)
out = {"held": declarations.held(root), "helpers": {}}
for name in sys.argv[1:]:
    own = tree.sources[name].declaration
    out["helpers"][name] = None if own is None else {
        "generates": own.generates, "every": own.every,
        "axes": {axis: sorted(options) for axis, options in own.axes.items()}, "reads": sorted(own.reads)}
    out["helpers"][name + ":effective"] = tree.effective(name)[1]
print(json.dumps(out))
"""
HELPERS = ("support", "scoped_fixture", "stamp_fixture", "mutation_scope_fixture", "gate_audit", "parallel_gate",
           "render_fixture", "forge_checkout")
NOTHING = {"generates": False, "every": False, "axes": {}, "reads": []}


def claim(axes: dict[str, list[str]], reads: list[str]) -> dict[str, object]:
    return {"generates": True, "every": False, "axes": axes, "reads": reads}


class TestTheHelpersSayWhatTheyRead(unittest.TestCase):
    helpers: dict[str, object]
    held: list[str]

    @classmethod
    def setUpClass(cls) -> None:
        done = subprocess.run(["python3", "-B", "-c", PROBE, *HELPERS], cwd=ROOT, text=True, capture_output=True,
                              timeout=180)
        assert done.returncode == 0, done.stderr
        found = json.loads(done.stdout)
        cls.helpers, cls.held = found["helpers"], found["held"]

    def test_support_reads_the_launcher_and_generates_only_what_its_callers_name(self) -> None:
        # `generate` runs `./slipwai` with the caller's arguments: the callers declare what they pass, and a
        # declaration of its own would widen every importer to every configuration
        self.assertEqual(self.helpers["support"], {**NOTHING, "reads": ["slipwai"]})

    def test_the_render_fixture_names_the_one_project_it_generates_and_reads_the_launcher_through_support(self) -> None:
        # it generates the default project through `./slipwai` with arguments the selector can read, so the claim is
        # those three axes; `support` carries the launcher read, which the join keeps
        self.assertEqual(self.helpers["render_fixture"],
                         {"generates": True, "every": False, "axes": {"backend": ["typescript"],
                          "profile": ["event-modelling"], "frontend": ["none"]}, "reads": []})

    def test_the_stamp_fixture_stays_undeclared_because_it_loads_a_script_with_importlib(self) -> None:
        # it runs the launcher too, and `importlib` loads a generated project's script: a reach D164 rule 4 holds to
        # `reads`, which cannot name a file in a project not yet generated
        self.assertIsNone(self.helpers["stamp_fixture"])

    def test_the_helpers_that_open_nothing_of_the_repository_declare_nothing_read(self) -> None:
        # both work in directories their callers hand them: git on an origin, a gate script of a generated project
        self.assertEqual(self.helpers["forge_checkout"], NOTHING)
        self.assertEqual(self.helpers["gate_audit"], NOTHING)

    def test_a_helper_that_imports_a_test_module_or_is_at_the_size_budget_stays_undeclared(self) -> None:
        # scoped_fixture and mutation_scope_fixture import test modules (`test_scoped_targets`,
        # `test_mutation_borders`) that declare nothing, and scoped_fixture loads `verify_scoped.rules` by
        # `importlib.import_module` from `assets/toolkit/scripts`; parallel_gate is at the 350-line budget
        for name in ("scoped_fixture", "mutation_scope_fixture", "parallel_gate"):
            self.assertIsNone(self.helpers[name], name)

    def test_a_declared_scoped_fixture_would_name_what_it_loads_by_name(self) -> None:
        declared = self.helpers["scoped_fixture"]
        if declared is not None:
            assert isinstance(declared, dict)
            self.assertIn("assets/toolkit/scripts", declared["reads"])

    def test_no_declaration_among_them_is_void(self) -> None:
        mine = [line for line in self.held if any(f"tests/{name}.py" in line for name in HELPERS)]
        self.assertEqual(mine, [])
        for name in ("support", "render_fixture", "forge_checkout", "gate_audit"):
            self.assertEqual(self.helpers[f"{name}:effective"], "", name)


if __name__ == "__main__":
    unittest.main()
