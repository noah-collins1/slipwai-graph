"""What every `test_select_tests_*` module that declares stand-in modules shares: declarations written into a slice.

Not a test module. `declare` writes stand-ins that start with `TEST_SELECTION = <literal>`, `slice_changing`
commits them on the trunk and changes paths on a slice branch cut from it, and `selected` runs the selector and
reads what ran.
"""
from __future__ import annotations

import json
import sys

from select_fixture import STAND_IN, SelectCase

sys.dont_write_bytecode = True

TEST_SELECTION: dict[str, object] = {}

GO = "assets/languages/go/main.go"
HELD = ("from select_tests import declarations\n"
        "print(json.dumps(declarations.held(__import__('pathlib').Path('.').resolve())))\n")


def declared(name: str, selection: str) -> str:
    """A stand-in module whose source starts with `TEST_SELECTION = <selection>`."""
    return f"TEST_SELECTION = {selection}\n" + STAND_IN.format(name=name)


class DeclarationCase(SelectCase):
    modules = ()

    def declare(self, **selections: str) -> None:
        for name, selection in selections.items():
            self.write(f"tests/{name}.py", declared(name, selection) if selection else STAND_IN.format(name=name))

    def slice_changing(self, *paths: str) -> None:
        """Commit the declarations on the trunk, then change `paths` on a slice branch cut from it."""
        self.commit("declarations")
        self.branch("slice/x")
        for path in paths:
            self.write(path, "changed\n")

    def selected(self, **env: str) -> tuple[list[str], list[str]]:
        """The modules that ran, and the `skipped` lines the run printed."""
        done = self.selector(**env)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        return self.modules_run(), [line for line in done.stdout.splitlines() if line.startswith("skipped ")]

    def held(self) -> list[str]:
        done = self.probe(HELD)
        self.assertEqual(done.returncode, 0, done.stderr)
        found: list[str] = json.loads(done.stdout)
        return found
