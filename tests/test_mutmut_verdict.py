"""S42 T005, T006 (rules 5 and 3 · AC-S42-3, -4 fresh `mutants/`, -5, -6): what `mutmut-mutation.py` generates and runs,
and the verdict it reads from the `.meta` files.

The wrapper runs as a subprocess against a fake `uv` first on `PATH`, written here: it logs every call, answers the
version `3.8.0`, refuses to generate over a `mutants/` left from an earlier run and writes the `.meta` files the example
hands it (`FAKE_META`), then writes the results it hands it (`FAKE_RESULTS`) when `mutmut run` is called and exits as
told. Nothing here starts mutmut: the one real run of the slice is T012's.
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
        self.assertEqual(lines[0], "mutation: not mutated apps/service/scripts/x.py — excluded by "
                                   "[tool.mutmut] source_paths (not under src)")
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


KEY = "pkg.x_f__mutmut_1"
REPORT = "report apps/service/mutants/"
PASSED = "mutation: {} mutants: {} killed, {} no tests (reported, never failed); passed \u2014 " + REPORT
STATUSES = {0: "survived", 36: "timeout", 24: "timeout", -24: "timeout", 152: "timeout", 255: "timeout",
            35: "suspicious", -11: "segfault", -9: "segfault", None: "not checked", 2: "check was interrupted by user",
            34: "skipped", 37: "caught by type check", 99: "unknown (exit 99)", -1: "unknown (exit -1)"}


class VerdictTest(Case):
    def verdict(self, codes: dict[str, Any], **keywords: Any) -> subprocess.CompletedProcess[str]:
        meta = {"src/pkg/a.py": {key: None for key in codes}}
        return self.run_wrapper("apps/service", "--file", "src/pkg/a.py", meta=meta,
                                results={"src/pkg/a.py": codes}, **keywords)

    def test_e1_every_key_killed_passes_in_the_last_line_the_data_model_fixes(self) -> None:
        done = self.verdict({KEY: 1, "pkg.x_f__mutmut_2": 3, "pkg.x_g__mutmut_1": 1})
        self.assertEqual((done.returncode, lines_of(done)[-1]), (0, PASSED.format(3, 3, 0)))

    def test_e2_each_code_of_the_table_fails_by_name_and_no_tests_is_counted_never_failed(self) -> None:
        for code, status in STATUSES.items():
            with self.subTest(code=code):
                done = self.verdict({KEY: code})
                self.assertEqual(done.returncode, 1)
                self.assertIn(f"mutation: {status} apps/service {KEY} (mutmut show {KEY} in apps/service; {REPORT})",
                              lines_of(done))
                self.assertTrue(lines_of(done)[-1].endswith(f"; failed \u2014 {REPORT}"))
        for code in (5, 33):
            done = self.verdict({KEY: code, "pkg.x_f__mutmut_2": 1})
            self.assertEqual((done.returncode, lines_of(done)[-1]), (0, PASSED.format(2, 1, 1)))
        done = self.verdict({KEY: 0, "pkg.x_f__mutmut_2": 36, "pkg.x_f__mutmut_3": 5})
        self.assertEqual(lines_of(done)[-1], "mutation: 3 mutants: 0 killed, 1 no tests (reported, never failed), "
                                             f"1 survived, 1 timed out; failed \u2014 {REPORT}")

    def test_e3_mutmut_s_exit_status_is_printed_and_never_decides(self) -> None:
        self.assertEqual(self.verdict({KEY: 0}, mutmut_exit=0).returncode, 1)
        self.assertEqual(self.verdict({KEY: 1}, mutmut_exit=1).returncode, 0)
        done = self.verdict({KEY: None}, mutmut_exit=1)
        self.assertEqual(done.returncode, 1)
        self.assertTrue(any(line.startswith("mutation: not checked ") for line in lines_of(done)))
        self.assertFalse(any(line.startswith("mutation: no tests ") for line in lines_of(done)))

    def test_e4_a_sweep_of_nothing_is_not_a_pass(self) -> None:
        done = self.run_wrapper("apps/service", meta={"src/pkg/types.py": {}})
        self.assertEqual((done.returncode, lines_of(done)[-1]), (1, "mutation: mutmut found nothing to mutate in "
                                                                    "apps/service; a pass on nothing is not a pass"))

    def test_e5_scoped_means_scoped_and_a_sweep_judges_every_file(self) -> None:
        meta = {"src/pkg/a.py": {KEY: None}, "src/pkg/b.py": {"pkg.y_h__mutmut_1": None}}
        results = {"src/pkg/a.py": {KEY: 1}, "src/pkg/b.py": {"pkg.y_h__mutmut_1": 0}}
        done = self.run_wrapper("apps/service", "--file", "src/pkg/a.py", meta=meta, results=results)
        self.assertEqual(done.returncode, 0)
        done = self.run_wrapper("apps/service", meta=meta, results=results)
        self.assertEqual(done.returncode, 1)
        self.assertIn(f"mutation: survived apps/service pkg.y_h__mutmut_1 (mutmut show pkg.y_h__mutmut_1 in "
                      f"apps/service; {REPORT})", lines_of(done))

    def source(self, text: str | bytes, setting: str = "", name: str = "a") -> None:
        """A source file under `src/pkg/` and, where `setting` is given, a line in the service's `[tool.mutmut]`."""
        (self.service / "src/pkg").mkdir(parents=True, exist_ok=True)
        (self.service / f"src/pkg/{name}.py").write_bytes(text if isinstance(text, bytes) else text.encode())
        (self.service / "pyproject.toml").write_text(TABLE.replace("[tool.mutmut]\n", "[tool.mutmut]\n" + setting),
                                                     encoding="utf-8")

    def test_e6_a_block_start_or_end_pragma_fails_the_run_and_a_bare_one_does_not(self) -> None:
        for word in ("block", "start", "end"):
            with self.subTest(word=word):
                self.source("x = 1\n" * 11 + f"y = 2  # pragma: no mutate {word}\n")
                done = self.verdict({KEY: 1})
                self.assertEqual(done.returncode, 1)
                self.assertIn(f'mutation: apps/service/src/pkg/a.py:12 holds "# pragma: no mutate {word}", which '
                              'silences mutants nobody looked at; only a bare "# pragma: no mutate" on the line '
                              "excuses one", lines_of(done))

    def test_e6_hold_a_bare_pragma_or_another_comment_is_not_flagged(self) -> None:
        """HOLD (teeth: flag every `pragma` and see it fail)."""
        self.source("a = 1  # pragma: no mutate\nb = 2  # pragma: no mutate -- a reason\nc = 3  # no mutate\n"
                    "d = 4  # pragma: no cover\n")
        self.assertEqual(self.verdict({KEY: 1}).returncode, 0)

    def test_e6_an_undecodable_file_fails_closed(self) -> None:
        self.source(b"x = '\xff'\n")
        done = self.verdict({KEY: 1})
        self.assertEqual(done.returncode, 1)
        self.assertIn("mutation: apps/service/src/pkg/a.py cannot be read as UTF-8, so its pragmas cannot be checked",
                      lines_of(done))

    def test_e6_a_non_empty_do_not_mutate_patterns_fails_and_an_empty_one_does_not(self) -> None:
        for setting, failed in (('do_not_mutate_patterns = ["x"]\n', True), ("do_not_mutate_patterns = []\n", False)):
            with self.subTest(setting=setting):
                self.source("x = 1\n", setting)
                done = self.verdict({KEY: 1})
                self.assertEqual(done.returncode, int(failed))
                self.assertEqual(any("apps/service/pyproject.toml sets do_not_mutate_patterns" in line
                                     for line in lines_of(done)), failed)

    def test_e6_a_pragma_in_a_file_that_is_not_judged_is_not_read(self) -> None:
        self.source("x = 1  # pragma: no mutate block\n", name="b")
        self.assertEqual(self.verdict({KEY: 1}).returncode, 0)

    def test_e7_hold_only_mutants_and_the_lock_are_written_and_mutmut_gets_only_the_names(self) -> None:
        """HOLD (teeth: add a flag to the argv and see it fail)."""
        self.source("x = 1\n")
        before = {path: path.read_bytes() for path in self.service.rglob("*") if path.is_file()}
        self.verdict({KEY: 1})
        after = {path: path.read_bytes() for path in self.service.rglob("*") if path.is_file()
                 and "mutants" not in path.parts and path.name != "mutmut-run.lock"}
        self.assertEqual(after, before)
        self.assertEqual(self.the_mutmut_call()["argv"][4:], ["mutmut", "run", "--", KEY])


if __name__ == "__main__":
    unittest.main()
