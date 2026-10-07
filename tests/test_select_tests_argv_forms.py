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

from test_select_tests_argv import GO, ArgvCase

sys.dont_write_bytecode = True

L = 'ROOT / "slipwai"'
NARROW = '"--profile", "standard", "--frontend", "none"'
PY = f'[{L}, "generate", "n", "--backend", "python", {NARROW}]'  # a literal argv a form below then changes
# the stamp-style claim with the launcher read `support` hands every importer on the real tree (not first: a list that
# starts with "slipwai" is the launcher on `PATH`)
STAMPED = ('{"configurations": {"backend": ["python"], "profile": ["standard"], "frontend": ["none"]}, '
           '"reads": ["README.md", "slipwai"]}')

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
    "python_dash_m_slipwai": (f'["python3", "-m", "slipwai", "generate", "n", "--backend", "python", {NARROW}]', ""),
    "a_concatenation": (f'[{L}, "generate", "n", "--backend", "python", {NARROW}] + flags', ""),
    "a_concatenation_onto_a_literal_argv": (f'flags + [{L}, "generate", "n", "--backend", "python", {NARROW}]', ""),
    "shlex_split": ('run(shlex.split("./slipwai generate n --backend python"))', "from subprocess import run\n"),
    "a_shell_string": ('run("./slipwai generate n --backend python", shell=True)', "from subprocess import run\n"),
    # converge pass 1: a literal argv that is not the one a `subprocess` call is handed, then changed to generate go
    "a_returned_list_extended": ('shape() + ["--backend", "go"]', f"def shape():\n    return {PY}\n"),
    "a_list_in_a_dict_extended": ('SHAPES["p"] + ["--backend", "go"]', f'SHAPES = {{"p": {PY}}}\n'),
    "a_list_in_a_tuple_extended": ('SHAPES[0] + ["--backend", "go"]', f"SHAPES = ({PY},)\n"),
    "a_list_of_argvs_extended": (f'[a + ["--backend", "go"] for a in [{PY}]][0]', ""),
    "a_walrus_bound_list_extended": (f'(cmd := {PY}) + ["--backend", "go"]', ""),
    "a_conditional_extended": (f'({PY} if fast else {PY}) + ["--backend", "go"]', ""),
    "a_lambda_result_extended": ('make() + ["--backend", "go"]', f"make = lambda: {PY}\n"),
    "a_default_argument_extended": ("shape()", f'def shape(a={PY}):\n    return a + ["--backend", "go"]\n'),
    "a_comprehension_element_extended": (f'[x for x in {PY}] + ["--backend", "go"]', ""),
    "a_helper_that_extends": (f"go({PY})", 'def go(a):\n    return a + ["--backend", "go"]\n'),
    "a_computed_element_after_the_flags": (f'[{L}, "generate", "--backend", "python", {NARROW}, extra]', ""),
    "an_f_string_after_the_flags": (f'[{L}, "generate", "--backend", "python", {NARROW}, f"--backend={{b}}"]', ""),
    # after-converge A1: a project generated inside a `python -c` code string, which no node of the module imports
    "a_code_string_importing_the_cli": (
        '[sys.executable, "-c", "from slipwai.cli import main\\nmain(sys.argv[1:])", "generate", "p", '
        '"--backend", "go"]', ""),
    "a_code_string_importing_the_cli_plainly": (
        '[sys.executable, "-c", "import slipwai.cli", "generate", "p", "--backend", "go"]', ""),
    "a_code_string_running_the_module_with_runpy": (
        '[sys.executable, "-c", "import runpy; runpy.run_module(\'slipwai\', run_name=\'__main__\')", '
        '"generate", "p", "--backend", "go"]', ""),
    "a_code_string_running_the_cli_module_with_runpy": (
        '[sys.executable, "-c", \'import runpy\\nrunpy.run_module("slipwai.cli")\', "generate", "p", '
        '"--backend", "go"]', ""),
    # after-converge A2: a literal argv whose call can still change the program it runs is not the argv it reads
    "a_list_with_shell_true": (f"{PY}, shell=True", ""),
    "a_list_with_a_computed_shell": (f"{PY}, shell=SHELL", ""),
    "a_list_with_an_executable": (f'{PY}, executable="/bin/true"', ""),
    "a_list_with_double_star_keywords": (f"{PY}, **KW", ""),
    "a_list_with_a_second_positional": (f"{PY}, 4096", ""),
    "a_list_with_an_unlisted_keyword": (f"{PY}, preexec_fn=hook", ""),
    # after-converge A4: forms converge pass 2 tried, each of them a route
    "a_keyword_args_list": (f"args={PY}", ""),
    "run_imported_under_an_alias": (f"r({PY})", "from subprocess import run as r\n"),
    "subprocess_imported_under_an_alias": (f"sp.run({PY})", "import subprocess as sp\n"),
    "os_execv_with_a_launcher_path": (
        f'os.execv(ROOT / "slipwai", [{L}, "generate", "n", "--backend", "python", {NARROW}])', ""),
    "an_asyncio_exec_with_a_starred_list": (
        f'asyncio.create_subprocess_exec(*[{L}, "generate", "n", "--backend", "python", {NARROW}])', ""),
    "an_abbreviated_backend_flag": (f'[{L}, "generate", "n", "--back", "python", {NARROW}]', ""),
    "a_double_dash_separator": (f'[{L}, "generate", "n", "--", "--backend", "python", {NARROW}]', ""),
    "python_dash_m_slipwai_as_a_tuple": (
        f'("python3", "-m", "slipwai", "generate", "n", "--backend", "python", {NARROW})', ""),
    "the_launcher_on_path_as_a_tuple": (f'("slipwai", "generate", "n", "--backend", "python", {NARROW})', ""),
}


class ArgvForms(ArgvCase):
    """One test per form (below): the planted copy is void, so it is held and selected on a Go change."""

    def planted(self, expression: str, head: str) -> None:
        self.write("slipwai", "#!/bin/sh\n")
        self.write("README.md", "read\n")
        self.module(STAMPED, f"argv = lambda: subprocess.run({expression})", head)


def case(expression: str, head: str) -> Callable[[ArgvForms], None]:
    def test(self: ArgvForms) -> None:
        self.planted(expression, head)
        found = self.voided()
        self.assertIn("every option", found)
        self.assertTrue(self.runs_on(GO), found)

    return test


for form, (expression, head) in FORMS.items():
    setattr(ArgvForms, f"test_{form}_is_every_axis_held_and_selected_on_a_go_change", case(expression, head))


if __name__ == "__main__":
    unittest.main()
