"""S42 T005, T006 (rules 5 and 3 · AC-S42-3, -4 fresh `mutants/`, -5, -6): what `mutmut-mutation.py` generates and runs,
and the verdict it reads from the `.meta` files.

The wrapper is run as a subprocess in a temporary project with a fake `uv` first on `PATH`, written here. The fake logs
every call (`argv`, `cwd`); answers the version question `3.8.0`; for `run … python -c` (mutmut's generation) refuses to
run on a `mutants/` left from an earlier run and writes the `.meta` files the example hands it (`FAKE_META`); and for
`run … mutmut run` writes the results the example hands it (`FAKE_RESULTS`) into those files and exits as told. Nothing
here starts mutmut: the one real run of the slice is T012's.
"""
from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

from slipwai.assets import LANGUAGE_ROOT

sys.dont_write_bytecode = True
SCRIPT = LANGUAGE_ROOT / "python" / "scripts/mutmut-mutation.py"
TEST_SELECTION = {"reads": ["assets/languages/python/scripts/mutmut-mutation.py"]}
TABLE = """[tool.mutmut]
source_paths = ["src"]
pytest_add_cli_args_test_selection = ["tests", "--ignore=tests/integration"]
pytest_add_cli_args = ["-p", "no:xdist"]
"""
FAKE_UV = f"""#!{sys.executable}
import json, os, sys
args = sys.argv[1:]
with open(os.environ["FAKE_LOG"], "a", encoding="utf-8") as log:
    log.write(json.dumps({{"argv": args, "cwd": os.getcwd()}}) + "\\n")


def write(files):
    for name, keys in files.items():
        path = os.path.join("mutants", name + ".meta")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump({{"exit_code_by_key": keys}}, handle)


if args[0] == "sync":
    sys.exit(0)
if "importlib.metadata" in args[-1]:
    print("3.8.0")
    sys.exit(0)
if args[4] == "python":
    if os.path.exists("mutants"):
        open(os.environ["FAKE_LOG"] + ".stale", "w").write("mutants/ was still there")
        sys.exit(97)
    write(json.loads(os.environ.get("FAKE_META", "{{}}")))
    print("src/some/file.py")
    sys.exit(0)
write(json.loads(os.environ.get("FAKE_RESULTS", "{{}}")))
print("fake mutmut output")
sys.exit(int(os.environ.get("FAKE_MUTMUT_EXIT", "0")))
"""
EXITED = "(its exit status and the output above are mutmut's, never the verdict; the .meta files are)"


def lines_of(done: subprocess.CompletedProcess[str]) -> list[str]:
    return [line for line in (done.stdout + done.stderr).strip().splitlines() if line.startswith("mutation: ")]


class Case(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="mutmut-verdict-"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        (self.bin / "uv").write_text(FAKE_UV, encoding="utf-8")
        (self.bin / "uv").chmod(0o755 | stat.S_IXUSR)
        self.log = self.root / "uv.log"
        self.tree = self.root / "tree"
        self.tree.mkdir()
        self.service = self.make_service("apps/service")

    def make_service(self, path: str, table: str = TABLE) -> Path:
        directory = self.tree / path
        directory.mkdir(parents=True)
        (directory / "pyproject.toml").write_text(table, encoding="utf-8")
        return directory

    def run_wrapper(self, *arguments: str, meta: dict[str, Any] | None = None, results: dict[str, Any] | None = None,
                    mutmut_exit: int = 0) -> subprocess.CompletedProcess[str]:
        env = {k: v for k, v in os.environ.items() if k not in ("CI", "GITHUB_ACTIONS", "GITLAB_CI", "PYTEST_ADDOPTS")}
        env.update({"PATH": f"{self.bin}{os.pathsep}{env['PATH']}", "FAKE_LOG": str(self.log),
                    "FAKE_META": json.dumps(meta or {}), "FAKE_RESULTS": json.dumps(results or {}),
                    "FAKE_MUTMUT_EXIT": str(mutmut_exit)})
        return subprocess.run([sys.executable, "-B", str(SCRIPT), *arguments], cwd=self.tree, env=env, text=True,
                              capture_output=True, timeout=60)

    def calls(self) -> list[dict[str, Any]]:
        if not self.log.exists():
            return []
        return [json.loads(line) for line in self.log.read_text(encoding="utf-8").splitlines()]

    def commands(self) -> list[list[str]]:
        """Each call's argv from its subcommand on, without the project path (an absolute one the wrapper chooses)."""
        shown = []
        for call in self.calls():
            argv = call["argv"]
            if argv[0] == "run" and "--project" in argv:
                at = argv.index("--project")
                argv = [*argv[:at], *argv[at + 2:]]
            shown.append(argv)
        return shown

    def started_mutmut(self) -> list[dict[str, Any]]:
        return [call for call in self.calls() if call["argv"][0] == "run" and call["argv"][4:5] == ["mutmut"]]

    def the_mutmut_call(self) -> dict[str, Any]:
        started = self.started_mutmut()
        self.assertEqual(len(started), 1, "mutmut run is started once")
        return started[0] if started else {"argv": [], "cwd": ""}


class GenerateThenRunTest(Case):
    def test_e1_a_scoped_run_generates_then_hands_mutmut_exactly_the_keys_of_the_given_file(self) -> None:
        keys = {"pkg.x_f__mutmut_1": None, "pkg.x_f__mutmut_2": None, "pkg.x_g__mutmut_1": None}
        done = self.run_wrapper("apps/service", "--file", "src/pkg/a.py", meta={"src/pkg/a.py": keys})
        lines = lines_of(done)
        self.assertEqual(lines[0], "mutation: scoped to 1 given file(s): src/pkg/a.py — 3 mutant(s)")
        self.assertIn(f"mutation: mutmut exited 0 {EXITED}", lines)
        shown = self.commands()
        self.assertEqual([argv[0] for argv in shown], ["sync", "run", "run", "run"])
        self.assertEqual(shown[2][:4], ["run", "--no-sync", "python", "-c"])
        self.assertEqual(shown[3], ["run", "--no-sync", "mutmut", "run", "--", "pkg.x_f__mutmut_1",
                                    "pkg.x_f__mutmut_2", "pkg.x_g__mutmut_1"])
        for call in self.calls()[2:]:
            self.assertEqual(call["cwd"], str(self.service))

    def test_e2_the_clean_slate_is_gone_before_generation_and_present_after(self) -> None:
        (self.service / "mutants").mkdir()
        (self.service / "mutants" / "old.meta").write_text('{"exit_code_by_key": {"x": 0}}', encoding="utf-8")
        (self.service / "mutants" / "mutmut-stats.json").write_text("{}", encoding="utf-8")
        self.run_wrapper("apps/service", "--file", "src/pkg/a.py", meta={"src/pkg/a.py": {"pkg.x_f__mutmut_1": None}})
        self.assertFalse(Path(str(self.log) + ".stale").exists(), "the fake met a mutants/ left from an earlier run")
        self.assertFalse((self.service / "mutants" / "old.meta").exists())
        self.assertFalse((self.service / "mutants" / "mutmut-stats.json").exists())
        self.assertTrue((self.service / "mutants" / "src/pkg/a.py.meta").is_file(), "the new report is kept")

    def test_e2_a_run_that_writes_no_meta_does_not_read_the_old_one(self) -> None:
        (self.service / "mutants" / "src/pkg").mkdir(parents=True)
        (self.service / "mutants" / "src/pkg/a.py.meta").write_text('{"exit_code_by_key": {"pkg.x_f__mutmut_1": 0}}',
                                                                    encoding="utf-8")
        done = self.run_wrapper("apps/service", "--file", "src/pkg/a.py")
        self.assertEqual(lines_of(done)[0], "mutation: not mutated apps/service/src/pkg/a.py — outside mutmut's "
                                            "configured targets")
        self.assertEqual(self.started_mutmut(), [])


class NoMutantToRunTest(Case):
    def test_e3_a_file_with_no_function_to_mutate_is_no_mutant_to_run_and_mutmut_never_starts(self) -> None:
        done = self.run_wrapper("apps/service", "--file", "src/pkg/types.py",
                                meta={"src/pkg/types.py": {}})
        self.assertEqual(done.returncode, 0)
        self.assertEqual(lines_of(done), ["mutation: no mutant to run — src/pkg/types.py: mutmut found no "
                                          "function to mutate in it"])
        self.assertEqual(self.started_mutmut(), [])

    def test_e3_two_such_files_read_in_them(self) -> None:
        done = self.run_wrapper("apps/service", "--file", "src/pkg/a.py", "--file", "src/pkg/b.py",
                                meta={"src/pkg/a.py": {}, "src/pkg/b.py": {}})
        self.assertEqual(done.returncode, 0)
        self.assertEqual(lines_of(done), ["mutation: no mutant to run — src/pkg/a.py, src/pkg/b.py: mutmut found "
                                          "no function to mutate in them"])
        self.assertEqual(self.started_mutmut(), [])

    def test_e3_an_empty_file_beside_one_holding_keys_runs_the_keys_only(self) -> None:
        self.run_wrapper("apps/service", "--file", "src/pkg/types.py", "--file", "src/pkg/a.py",
                         meta={"src/pkg/types.py": {}, "src/pkg/a.py": {"pkg.x_f__mutmut_1": None}})
        call = self.the_mutmut_call()
        self.assertEqual(call["argv"][-2:], ["--", "pkg.x_f__mutmut_1"])

    def test_e4_a_file_with_no_meta_is_named_and_nothing_left_is_exit_zero(self) -> None:
        done = self.run_wrapper("apps/service", "--file", "src/pkg/a.py",
                                meta={"src/pkg/b.py": {"pkg.x_f__mutmut_1": 1}})
        self.assertEqual(done.returncode, 0)
        self.assertEqual(lines_of(done), [
            "mutation: not mutated apps/service/src/pkg/a.py — outside mutmut's configured targets",
            "mutation: nothing under apps/service that was given is a file mutmut would mutate; no mutant to run"])
        self.assertEqual(self.started_mutmut(), [])

    def test_e4_an_unmatched_file_beside_a_matched_one_runs_the_matched_one_and_names_the_other(self) -> None:
        done = self.run_wrapper("apps/service", "--file", "src/pkg/a.py", "--file", "scripts/x.py",
                                meta={"src/pkg/a.py": {"pkg.x_f__mutmut_1": None}})
        lines = lines_of(done)
        self.assertEqual(lines[0], "mutation: not mutated apps/service/scripts/x.py — outside mutmut's "
                                   "configured targets")
        self.assertEqual(lines[1], "mutation: scoped to 1 given file(s): src/pkg/a.py — 1 mutant(s)")
        call = self.the_mutmut_call()
        self.assertEqual(call["argv"][-2:], ["--", "pkg.x_f__mutmut_1"])


class NamesAndShapesTest(Case):
    def test_e5_a_package_init_runs_that_file_s_keys_only_never_a_pattern_or_a_submodule(self) -> None:
        self.run_wrapper("apps/service", "--file", "src/pkg/__init__.py",
                         meta={"src/pkg/__init__.py": {"pkg.x_health__mutmut_1": None},
                               "src/pkg/sub.py": {"pkg.sub.x_f__mutmut_1": None}})
        call = self.the_mutmut_call()
        self.assertEqual(call["argv"][-2:], ["--", "pkg.x_health__mutmut_1"])
        self.assertNotIn("pkg.*", call["argv"])

    def test_e6_a_sweep_starts_mutmut_with_no_names_after_a_fresh_generation(self) -> None:
        (self.service / "mutants").mkdir()
        (self.service / "mutants" / "old.meta").write_text("{}", encoding="utf-8")
        self.run_wrapper("apps/service", meta={"src/pkg/a.py": {"pkg.x_f__mutmut_1": None}})
        self.assertFalse(Path(str(self.log) + ".stale").exists())
        call = self.the_mutmut_call()
        self.assertEqual(call["argv"][-2:], ["mutmut", "run"])
        self.assertNotIn("--", call["argv"])
        self.assertEqual(call["cwd"], str(self.service))

    def test_e7_each_service_runs_from_its_own_directory_with_its_own_table(self) -> None:
        second = self.make_service("apps/second", TABLE.replace('["src"]', '["lib"]'))
        self.run_wrapper("apps/service", "--file", "src/pkg/a.py", meta={"src/pkg/a.py": {"pkg.x_f__mutmut_1": None}})
        self.run_wrapper("apps/second", "--file", "lib/b.py", meta={"lib/b.py": {"b.x_g__mutmut_1": None}})
        self.assertEqual([call["cwd"] for call in self.started_mutmut()], [str(self.service), str(second)])
        self.assertTrue((second / "mutants" / "lib/b.py.meta").is_file())
        self.assertFalse((self.service / "mutants" / "lib").exists(), "one run does not touch another's mutants/")

    def test_e8_hold_dot_slash_and_trailing_slash_forms_are_the_same_file_and_service(self) -> None:
        """HOLD (teeth: drop the normalisation and see it fail for `./src/pkg/a.py`)."""
        meta = {"src/pkg/a.py": {"pkg.x_f__mutmut_1": None}}
        for service, file in (("apps/service/", "./src/pkg/a.py"), ("./apps/service", "src//pkg/a.py")):
            with self.subTest(service=service, file=file):
                self.log.unlink(missing_ok=True)
                done = self.run_wrapper(service, "--file", file, meta=meta)
                self.assertEqual(lines_of(done)[0], "mutation: scoped to 1 given file(s): src/pkg/a.py — 1 mutant(s)")
                call = self.the_mutmut_call()
                self.assertEqual(call["argv"][-2:], ["--", "pkg.x_f__mutmut_1"])


if __name__ == "__main__":
    unittest.main()
