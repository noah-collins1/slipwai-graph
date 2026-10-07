"""Every argv form the literal rule cannot read stays every axis, so a narrow declaration is void and held (S43 T002).

D187 rule 3, AC-S43-12: a planted copy of a fixture module declares `backend: python` and generates through one form.
On a one-Go-file change set the module is selected, and `declarations.held()` names it. These are the guard around the
reader in `scripts/select_tests/argv.py`: a reader that took any list starting with the launcher would read the forms
below it as the literal axes it can see, and the copy would be skipped. The routes the reader never sees (`refuse(`, the
launcher on `PATH`) stay what `generation.py` already made them. Stand-in modules in a temporary repository.
"""
from __future__ import annotations

import sys
import unittest
from collections.abc import Callable

from test_select_tests_argv import GO, STAMPED, ArgvCase

sys.dont_write_bytecode = True

L = 'ROOT / "slipwai"'
NARROW = '"--profile", "standard", "--frontend", "none"'

# name -> (the expression the planted module holds, the import head it needs)
FORMS: dict[str, tuple[str, str]] = {
    "a_computed_backend_value": (f'[{L}, "generate", "n", "--backend", pick(), {NARROW}]', ""),
    "a_starred_element": (f'[{L}, "generate", "n", *SHAPES[name], {NARROW}]', ""),
    "a_starred_backend_flag": (f'[{L}, "generate", "n", "--backend", "python", {NARROW}, *EXTRA]', ""),
    "a_list_variable_given_to_run": (
        "run(cmd)", "from subprocess import run\ncmd = [ROOT / 'slipwai', 'generate']\n"),
    "an_unmapped_language_flag": (f'[{L}, "generate", "n", "--language", "python", {NARROW}]', ""),
    "an_unmapped_service_name_flag": (
        f'[{L}, "generate", "n", "--service-name", "x", "--backend", "python", {NARROW}]', ""),
    "an_unmapped_no_init_flag": (f'[{L}, "generate", "n", "--no-init", "--backend", "python", {NARROW}]', ""),
    "an_equals_form_flag": (f'[{L}, "generate", "n", "--backend=go", {NARROW}]', ""),
    "a_repeated_flag": (f'[{L}, "generate", "n", "--backend", "python", "--backend", "python", {NARROW}]', ""),
    "a_literal_add_service": (f'[{L}, "add-service", "n", "--backend", "python", {NARROW}]', ""),
    "a_literal_migrate": (f'[{L}, "migrate", "n", "--backend", "python", {NARROW}]', ""),
    "a_literal_adopt": (f'[{L}, "adopt", "n", "--backend", "python", {NARROW}]', ""),
    "a_literal_replay": (f'[{L}, "replay", "n", "--backend", "python", {NARROW}]', ""),
    "a_computed_subcommand": (f'[{L}, verb, "n", "--backend", "python", {NARROW}]', ""),
    "the_launcher_on_path": (f'["slipwai", "generate", "n", "--backend", "python", {NARROW}]', ""),
    "the_cli_module_imported": ('main(["generate", "n", "--backend", "python"])', "from slipwai.cli import main\n"),
    "refuse": ('self.refuse("d", "n", backend="python")', ""),
}


# forms D187 rule 3 names that today's rules do NOT hold (T002 findings): `argv.read` reads the literal list inside a
# `+` (so it is a Call with its literal axes and the appended flags are unseen), a command given as a string is no
# launcher route, and `python3 -m slipwai` is none either. Each is expected to
# fail; when the selector holds one, the unexpected success says to move it up.
HOLES: dict[str, tuple[str, str]] = {
    "python_dash_m_slipwai": (f'["python3", "-m", "slipwai", "generate", "n", "--backend", "python", {NARROW}]', ""),
    "a_concatenation": (f'[{L}, "generate", "n", "--backend", "python", {NARROW}] + flags', ""),
    "a_concatenation_onto_a_literal_argv": (f'flags + [{L}, "generate", "n", "--backend", "python", {NARROW}]', ""),
    "shlex_split": ('run(shlex.split("./slipwai generate n --backend python"))', "from subprocess import run\n"),
    "a_shell_string": ('run("./slipwai generate n --backend python", shell=True)', "from subprocess import run\n"),
}


class ArgvForms(ArgvCase):
    """One test per form (below): the planted copy is void, so it is held and selected on a Go change."""

    def planted(self, expression: str, head: str) -> None:
        self.module(STAMPED, f"argv = lambda: {expression}", head)


def case(expression: str, head: str) -> Callable[[ArgvForms], None]:
    def test(self: ArgvForms) -> None:
        self.planted(expression, head)
        found = self.voided()
        self.assertIn("every option", found)
        self.assertTrue(self.runs_on(GO), found)

    return test


for form, (expression, head) in FORMS.items():
    setattr(ArgvForms, f"test_{form}_is_every_axis_held_and_selected_on_a_go_change", case(expression, head))
for form, (expression, head) in HOLES.items():
    setattr(ArgvForms, f"test_known_hole_{form}_is_not_yet_held", unittest.expectedFailure(case(expression, head)))


if __name__ == "__main__":
    unittest.main()
