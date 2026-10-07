"""The backend readers say which backends they generate, or stay undeclared for a stated reason (S38 T013, AC-S38-8/9).

Read over the real tree by the selector's own scan, with `choose` fed paths directly, so no git is involved. Each
declaration is a completeness claim: the seven declared modules generate through `./slipwai generate` and read no file
of the repository by path; the five that stay undeclared are held undeclared, so a later declaration is a decision.
"""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from typing import Any

from slipwai.assets import ROOT

sys.dont_write_bytecode = True

DECLARED = ("test_matrix", "test_images", "test_postgres", "test_readiness", "test_line_widths",
            "test_no_mocking_frameworks", "test_stale_references")
UNDECLARED = ("test_monorepos", "test_flag_gate", "test_factory_repository", "test_factory_gate_stamp_inputs")
PATHS = {"go": "assets/languages/go/scripts/go-mutation.py",
         "frontend": "assets/frontends/react-vite/app-route-client/Home.tsx",
         "standard": "assets/profiles/standard/docs/speckit-preset.md", "docs": "docs/maintaining.md"}
PROBE = """
import json, sys
sys.dont_write_bytecode = True
sys.path.insert(0, 'scripts')
from pathlib import Path
from select_tests import choose, declarations
root = Path('.').resolve()
catalog = json.loads((root / 'catalog.json').read_text(encoding='utf-8'))
tree = declarations.scan(root, catalog)
modules = sys.argv[2:]
out = {"held": declarations.held(root), "own": {}, "ran": {}, "narrowed": {}, "backends": {}}
for name in modules:
    own = tree.sources[name].declaration
    out["own"][name] = None if own is None else {
        "every": own.every, "axes": {a: sorted(o) for a, o in own.axes.items()}, "reads": sorted(own.reads)}
for key, path in json.loads(sys.argv[1]).items():
    selection = choose.select(tree, [path], catalog)
    out["ran"][key] = sorted(v.module for v in selection.verdicts if v.module in modules and v.runs)
    out["narrowed"][key] = sorted(v.module for v in selection.narrowed() if v.module in modules)
    out["backends"][key] = list(selection.backends)
print(json.dumps(out))
"""
BACKENDS = ["go", "java-quarkus", "java-spring", "python", "typescript"]
BOTH = ["event-modelling", "standard"]


def claim(frontends: list[str], profiles: list[str]) -> dict[str, object]:
    return {"every": False, "reads": [], "axes": {"backend": BACKENDS, "command": ["generate"],
                                                  "frontend": frontends, "profile": sorted(profiles)}}


class TestTheBackendReadersSayWhatTheyGenerate(unittest.TestCase):
    found: dict[str, Any]

    @classmethod
    def setUpClass(cls) -> None:
        done = subprocess.run(["python3", "-B", "-c", PROBE, json.dumps(PATHS), *DECLARED, *UNDECLARED], cwd=ROOT,
                              text=True, capture_output=True, timeout=180)
        assert done.returncode == 0, done.stderr
        cls.found = json.loads(done.stdout)

    def test_each_declared_module_names_every_backend_and_the_frontends_and_profiles_it_passes(self) -> None:
        both, none = ["none", "react-vite"], ["none"]
        expected = {"test_matrix": claim(both, BOTH), "test_images": claim(none, ["event-modelling"]),
                    "test_postgres": claim(none, ["event-modelling"]), "test_readiness": claim(none, BOTH),
                    "test_line_widths": claim(both, BOTH), "test_no_mocking_frameworks": claim(both, BOTH),
                    "test_stale_references": claim(both, BOTH)}
        for name, want in expected.items():
            with self.subTest(module=name):
                self.assertEqual(self.found["own"][name], want)

    def test_the_modules_that_read_the_repository_or_load_undeclared_tests_stay_undeclared(self) -> None:
        # monorepos imports `test_verify_stamp_pinned` and reads its own sources; flag_gate is at the 350-line budget
        # and opens `assets/languages`; factory_repository reads `src`, `assets`, the workflows and the Makefile;
        # factory_gate_stamp_inputs copies scripts of `assets/toolkit` that load others by path, and imports the
        # undeclared `test_factory_gate_stamp_scan` (`test_factory_gate_stamp` is declared reads-only by S43 T007)
        for name in UNDECLARED:
            self.assertIsNone(self.found["own"][name], name)

    def test_no_declaration_among_them_is_void(self) -> None:
        held = self.found["held"]
        mine = [line for line in held if any(f"tests/{name}.py" in line for name in DECLARED)]
        self.assertEqual(mine, [])

    def test_a_go_path_runs_every_declared_module_narrowed_to_go(self) -> None:
        self.assertEqual(self.found["backends"]["go"], ["go"])
        self.assertEqual(self.found["ran"]["go"], sorted(DECLARED + UNDECLARED))
        self.assertEqual(self.found["narrowed"]["go"], sorted(DECLARED))

    def test_a_frontend_path_skips_the_modules_that_generate_no_browser_app(self) -> None:
        ran = self.found["ran"]["frontend"]
        for name in ("test_images", "test_postgres", "test_readiness"):
            self.assertNotIn(name, ran)
        for name in ("test_matrix", "test_line_widths", "test_no_mocking_frameworks", "test_stale_references"):
            self.assertIn(name, ran)

    def test_a_standard_profile_path_skips_the_modules_that_generate_only_event_modelling(self) -> None:
        ran = self.found["ran"]["standard"]
        for name in ("test_images", "test_postgres"):
            self.assertNotIn(name, ran)
        self.assertIn("test_matrix", ran)

    def test_a_page_of_the_docs_runs_none_of_the_declared_modules(self) -> None:
        self.assertEqual([m for m in self.found["ran"]["docs"] if m in DECLARED], [])


if __name__ == "__main__":
    unittest.main()
