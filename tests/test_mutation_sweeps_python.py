"""S42 T008 (rule 7 · AC-S42-7): what sweeps a Python service, with real `git` and the base holding the old files.

The tool is `test_mutation_scope_python`'s recording `Runner`, which says whether a service was asked for a scope or a
sweep. A change no scope can be trusted across names its file and sweeps the service; a change that cannot be told
apart from a harmless one sweeps too, and a harmless one does not.
"""
from __future__ import annotations

import sys

from stamp_fixture import git
from test_mutation_borders import clean_environment
from test_mutation_scope_python import GO_AND, HEALTH, SOURCE, TWO, PythonCase

sys.dont_write_bytecode = True
MANIFEST_PATH = "apps/service/pyproject.toml"
LOCK_PATH = "apps/service/uv.lock"
TABLE = '[tool.mutmut]\nsource_paths = ["src"]\n'
HEAD = '[project]\nname = "x"\nversion = "0.1.0"\n\n[dependency-groups]\n'
MANIFEST = HEAD + 'dev = ["mutmut==3.8.0", "ruff==0.16.3"]\n\n' + TABLE
BASE = {"mutmut": ["3.8.0"], "libcst": ["1.9.0"], "pyyaml": ["6.0.2"], "pytest": ["9.1.1"], "coverage": ["7.0"],
        "textual": ["1.0"]}
DEPENDS = {"mutmut": ["libcst", "pytest", "coverage", "textual"], "libcst": ["pyyaml"]}


def lock(**moved: list[str]) -> str:
    """A uv lock with mutmut and the closure of libcst among others: `moved` sets the versions of the named packages."""
    versions = {**BASE, **moved}
    out = "version = 1\n"
    for name, found in versions.items():
        for version in found:
            wanted = ", ".join(f'{{ name = "{item}" }}' for item in DEPENDS.get(name, []))
            out += f'\n[[package]]\nname = "{name}"\nversion = "{version}"\ndependencies = [{wanted}]\n'
    return out


class SweepsPythonTest(PythonCase):
    def setUp(self) -> None:
        super().setUp()
        self.on_main(MANIFEST_PATH, "apps/second/pyproject.toml", text=MANIFEST)
        self.on_main(LOCK_PATH, "apps/second/uv.lock", text=lock())

    def edit(self, name: str) -> None:
        path = self.repo / name
        path.write_text(path.read_text(encoding="utf-8") + "\n# e\n", encoding="utf-8")

    def swept(self, *services: str, env: dict[str, str] | None = None) -> tuple[list[str], list[str], list[str]]:
        """(the services swept, the files scoped by `service/file`, the lines) of one run."""
        status, lines, recording = self.run_planned(*services, env=env)
        self.assertEqual(status, 0, lines)
        return recording.swept, [f"{path}/{name}" for path, names in recording.scoped for name in names], lines

    def test_e1_a_changed_mutmut_table_sweeps_that_service_only(self) -> None:
        self.write("apps/second/src/pkg/b.py", SOURCE)
        for name, content in (("a key added", MANIFEST + "pytest_add_cli_args = ['-x']\n"),
                              ("source_paths altered", MANIFEST.replace('["src"]', '["src", "lib"]')),
                              ("the table removed", HEAD + 'dev = ["mutmut==3.8.0", "ruff==0.16.3"]\n')):
            with self.subTest(change=name):
                self.write(MANIFEST_PATH, content)
                swept, scoped, lines = self.swept(*TWO)
                self.assertEqual(swept, ["apps/service"], lines)
                self.assertIn(f"mutation: sweep apps/service — `{MANIFEST_PATH}` changed", lines)
                self.assertEqual(scoped, ["apps/second/src/pkg/b.py"])

    def test_e1_a_table_added_sweeps_and_a_go_service_beside_is_not_swept(self) -> None:
        self.on_main("apps/second/pyproject.toml", text=HEAD + 'dev = ["mutmut==3.8.0"]\n')
        self.write("apps/second/pyproject.toml", HEAD + 'dev = ["mutmut==3.8.0"]\n\n' + TABLE)
        self.write("apps/service/domain/x.go", "package domain\n")
        swept, scoped, lines = self.swept(*GO_AND)
        self.assertEqual((swept, scoped), (["apps/second"], ["apps/service/domain/x.go"]), lines)
        self.assertIn("mutation: sweep apps/second — `apps/second/pyproject.toml` changed", lines)

    def test_e2_the_wrapper_changing_sweeps_every_python_service_and_no_other(self) -> None:
        self.edit("scripts/mutmut-mutation.py")
        swept, _, lines = self.swept(*TWO)
        self.assertEqual(sorted(swept), ["apps/second", "apps/service"], lines)
        self.assertIn("mutation: sweep apps/service — `scripts/mutmut-mutation.py` changed", lines)
        swept, _, _ = self.swept("go:apps/service", "python:apps/second", "typescript:apps/third")
        self.assertEqual(swept, ["apps/second"])

    def test_e2_hold_the_go_or_typescript_wrapper_changing_sweeps_no_python_service(self) -> None:
        for name in ("scripts/go-mutation.py", "scripts/stryker-mutation.py"):
            with self.subTest(wrapper=name):
                self.write(name, "x = 1\n")
                swept, _, lines = self.swept(*TWO)
                self.assertEqual(swept, [], lines)

    def test_e3_the_mutmut_pin_moving_sweeps_that_service_only(self) -> None:
        self.write(MANIFEST_PATH, MANIFEST.replace("mutmut==3.8.0", "mutmut==3.8.1"))
        swept, _, lines = self.swept(*TWO)
        self.assertEqual(swept, ["apps/service"], lines)
        self.assertIn(f"mutation: sweep apps/service — `{MANIFEST_PATH}` changed", lines)

    def test_e3_hold_nothing_that_is_not_the_table_or_the_pin_sweeps(self) -> None:
        """HOLD (teeth: compare the raw text of the manifest and see the first three sweep)."""
        self.write(HEALTH, SOURCE)
        for name, content in (("another dependency", MANIFEST.replace("ruff==0.16.3", "ruff==0.17.0")),
                              ("key order and whitespace", HEAD + 'dev = [ "ruff==0.16.3",   "mutmut==3.8.0" ]\n\n'
                               + '[tool.mutmut]\n\nsource_paths   =   ["src"]\n'),
                              ("a comment", "# a note\n" + MANIFEST.replace(TABLE, "# the table\n" + TABLE)),
                              ("the project version", MANIFEST.replace('"0.1.0"', '"0.2.0"'))):
            with self.subTest(change=name):
                self.write(MANIFEST_PATH, content)
                swept, scoped, lines = self.swept(*TWO)
                self.assertEqual((swept, scoped), ([], ["apps/service/src/pkg/health.py"]), lines)

    def test_e3_a_manifest_that_does_not_parse_on_either_side_sweeps_naming_the_file(self) -> None:
        self.write(MANIFEST_PATH, "[not toml")
        swept, _, lines = self.swept(*TWO)
        self.assertEqual(swept, ["apps/service"])
        self.assertIn(f"mutation: sweep apps/service — `{MANIFEST_PATH}` changed", lines)
        self.on_main(MANIFEST_PATH, text="[not toml")
        self.write(MANIFEST_PATH, MANIFEST)
        swept, _, _ = self.swept(*TWO)
        self.assertEqual(swept, ["apps/service"])

    def test_e3_a_manifest_with_no_tomllib_sweeps_when_it_changes(self) -> None:
        self.write(MANIFEST_PATH, "# a note\n" + MANIFEST)  # a comment alone moves nothing where the file can be read
        saved = sys.modules.get("tomllib")
        sys.modules["tomllib"] = None  # type: ignore[assignment]
        try:
            swept, _, lines = self.swept(*TWO)
        finally:
            if saved is None:
                del sys.modules["tomllib"]
            else:
                sys.modules["tomllib"] = saved
        self.assertEqual(swept, ["apps/service"], lines)

    def test_e4_the_lock_moving_mutmut_or_the_libcst_closure_sweeps_that_service_only(self) -> None:
        for name, content, sweeps in (
                ("mutmut", lock(mutmut=["3.8.1"]), True), ("libcst", lock(libcst=["1.9.1"]), True),
                ("pyyaml, in libcst's closure", lock(pyyaml=["6.0.3"]), True),
                ("a second copy of libcst", lock(libcst=["1.9.0", "1.8.0"]), True),
                ("a lock that does not parse", "version = [", True),
                ("pytest", lock(pytest=["9.2.0"]), False), ("coverage", lock(coverage=["7.1"]), False),
                ("textual", lock(textual=["2.0"]), False)):
            with self.subTest(change=name):
                self.write(LOCK_PATH, content)
                swept, _, lines = self.swept(*TWO)
                self.assertEqual(swept, ["apps/service"] if sweeps else [], lines)
                self.assertEqual(sweeps, f"mutation: sweep apps/service — `{LOCK_PATH}` changed" in lines, lines)

    def test_e5_a_table_the_script_cannot_read_sweeps_naming_the_manifest_changed_or_not(self) -> None:
        for content in ('[tool.mutmut]\nsource_paths = ["s*"]\n', '[project]\nname = "x"\n'):
            with self.subTest(table=content):
                self.on_main(MANIFEST_PATH, text=content)
                self.write(HEALTH, SOURCE)  # the manifest is unchanged since the base
                swept, scoped, lines = self.swept(*TWO)
                self.assertEqual((swept, scoped), (["apps/service"], []), lines)
                self.assertTrue([line for line in lines if line.startswith("mutation: sweep apps/service — ")
                                 and MANIFEST_PATH in line], lines)
                self.reset()

    def test_e6_hold_an_ignored_file_under_src_sweeps_that_service(self) -> None:
        """HOLD (teeth: take Python out of `PRODUCTION_ROOT` and see it fail)."""
        ignores = (self.repo / ".gitignore").read_text(encoding="utf-8")
        self.on_main(".gitignore", text=ignores + "apps/service/src/pkg/gen/\n")
        self.write("apps/service/src/pkg/gen/x.py", SOURCE)
        swept, _, lines = self.swept(*TWO)
        self.assertEqual(swept, ["apps/service"], lines)
        self.assertTrue([line for line in lines if "apps/service/src/pkg/gen" in line and "ignores" in line], lines)

    def test_e7_two_causes_in_one_service_sweep_it_once_naming_the_manifest(self) -> None:
        self.write(MANIFEST_PATH, MANIFEST.replace("mutmut==3.8.0", "mutmut==3.8.1"))
        self.write(HEALTH, SOURCE)
        swept, scoped, lines = self.swept(*TWO)
        self.assertEqual((swept, scoped), (["apps/service"], []), lines)
        sweeps = [line for line in lines if line.startswith("mutation: sweep apps/service — ")]
        self.assertEqual(len(sweeps), 1, lines)
        self.assertIn(f"`{MANIFEST_PATH}` changed", sweeps[0])

    def test_e7_since_sweeps_on_the_same_triggers(self) -> None:
        self.fit_recipe(TWO)
        self.write(MANIFEST_PATH, MANIFEST.replace("mutmut==3.8.0", "mutmut==3.8.1"))
        self.commit("pin")
        swept, _, lines = self.swept(*TWO, env={**clean_environment(), "SINCE": "HEAD~1"})
        self.assertEqual(swept, ["apps/service"], lines)

    def reset(self) -> None:
        super().reset()
        git(self.repo, "checkout", "-q", "-B", "slice/S1", "main")
