"""S42 T004 (rule 4 · AC-S42-10): what `mutmut-mutation.py` checks before it starts mutmut, and the order it checks in.

The wrapper is run as a subprocess in a temporary project with a fake `uv` first on `PATH`, written here, that logs
every call as one JSON line (`argv`, `cwd`, and the environment variables the examples read) and answers as the example
says: the exit status of `sync`, the version `python -c` prints, a FIFO `sync` waits on. Every `subprocess` here is
under a timeout and every process an example starts is ended by the example.
"""
from __future__ import annotations

import json
import os
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
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
names = ("PYTEST_ADDOPTS", "PYTHONPATH", "VIRTUAL_ENV")
with open(os.environ["FAKE_LOG"], "a", encoding="utf-8") as log:
    log.write(json.dumps({{"argv": args, "cwd": os.getcwd(), "env": {{k: os.environ.get(k) for k in names}}}}) + "\\n")
if args[0] == "sync":
    if os.environ.get("FAKE_WAIT"):
        open(os.environ["FAKE_WAIT"], encoding="utf-8").read()
    sys.stderr.write("fake uv: the lock is out of date\\n")
    sys.exit(int(os.environ.get("FAKE_SYNC_EXIT", "0")))
if args[:2] == ["run", "--no-sync"] and "python" in args:
    version = os.environ.get("FAKE_VERSION", "3.8.0")
    if version == "absent":
        sys.exit(1)
    print(version)
    sys.exit(0)
sys.exit(97)
"""
NO_FORK = "import os; del os.fork"
HOST = "mutation: mutmut needs os.fork, which this host does not have; run it under WSL"
NO_UV = "mutation: uv is not on PATH; install it to run mutmut (see scripts/verify)"
SKELETON = "mutation: mutmut is not wired by this script yet; nothing was run"


def lines_of(done: subprocess.CompletedProcess[str]) -> list[str]:
    return (done.stdout + done.stderr).strip().splitlines()


class Case(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="mutmut-setup-"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        (self.bin / "uv").write_text(FAKE_UV, encoding="utf-8")
        (self.bin / "uv").chmod(0o755 | stat.S_IXUSR)
        self.log = self.root / "uv.log"
        self.tree = self.root / "tree"
        self.tree.mkdir()
        self.service = self.make_service("apps/service")

    def make_service(self, path: str, environment: bool = False) -> Path:
        directory = self.tree / path
        directory.mkdir(parents=True)
        (directory / "pyproject.toml").write_text(TABLE, encoding="utf-8")
        if environment:  # what `uv sync` leaves: a virtual environment the lock can live in
            (directory / ".venv").mkdir()
            (directory / ".venv" / "pyvenv.cfg").write_text("home = /usr/bin\n", encoding="utf-8")
        return directory

    def environment(self, extra: dict[str, str] | None = None, path: str | None = None) -> dict[str, str]:
        env = {k: v for k, v in os.environ.items() if k not in ("CI", "GITHUB_ACTIONS", "GITLAB_CI", "PYTEST_ADDOPTS")}
        env.update({"PATH": path if path is not None else f"{self.bin}{os.pathsep}{env['PATH']}",
                    "FAKE_LOG": str(self.log), **(extra or {})})
        return env

    def command(self, arguments: tuple[str, ...], prelude: str) -> list[str]:
        if not prelude:
            return [sys.executable, "-B", str(SCRIPT), *arguments]
        code = (f"{prelude}\nimport runpy, sys\nsys.argv = [{str(SCRIPT)!r}, *{list(arguments)!r}]\n"
                f"runpy.run_path({str(SCRIPT)!r}, run_name='__main__')")
        return [sys.executable, "-B", "-c", code]

    def run_wrapper(self, *arguments: str, extra: dict[str, str] | None = None, prelude: str = "",
                    path: str | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(self.command(arguments, prelude), cwd=self.tree, env=self.environment(extra, path),
                              text=True, capture_output=True, timeout=60)

    def calls(self) -> list[dict[str, Any]]:
        if not self.log.exists():
            return []
        return [json.loads(line) for line in self.log.read_text(encoding="utf-8").splitlines()]

    def wait_for_calls(self, count: int) -> None:
        deadline = time.monotonic() + 10
        while len(self.calls()) < count:
            self.assertLess(time.monotonic(), deadline, "the fake uv was not reached")
            time.sleep(0.05)

    def start(self, *arguments: str, extra: dict[str, str]) -> subprocess.Popen[str]:
        process = subprocess.Popen(self.command(arguments, ""), cwd=self.tree, env=self.environment(extra),
                                   text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.addCleanup(self.end, process)
        return process

    @staticmethod
    def end(process: subprocess.Popen[str]) -> None:
        if process.poll() is None:
            process.kill()
        process.communicate(timeout=30)

    def fifo(self, name: str) -> str:
        path = self.root / name
        os.mkfifo(path)
        return str(path)

    @staticmethod
    def release(fifo: str) -> None:
        with open(fifo, "w", encoding="utf-8"):
            pass


class OrderedChecksTest(Case):
    def test_e1_no_fork_is_the_wsl_line_and_nothing_starts_or_is_created(self) -> None:
        done = self.run_wrapper("apps/service", prelude=NO_FORK)
        self.assertEqual((done.returncode, lines_of(done)), (2, [HOST]))
        self.assertEqual(self.calls(), [])
        self.assertFalse((self.service / ".venv").exists())
        self.assertFalse((self.service / "mutants").exists())

    def test_e2_no_uv_is_the_uv_line(self) -> None:
        empty = self.root / "empty"
        empty.mkdir()
        done = self.run_wrapper("apps/service", path=str(empty))
        self.assertEqual((done.returncode, lines_of(done)), (2, [NO_UV]))

    def test_e3_a_lock_that_disagrees_is_the_uv_lock_line_and_mutmut_never_starts(self) -> None:
        line = ("mutation: apps/service/uv.lock does not agree with apps/service/pyproject.toml; run uv lock --project "
                "apps/service, then this again")
        for arguments in (("apps/service",), ("apps/service", "--file", "src/pkg/a.py")):
            with self.subTest(arguments=arguments):
                self.log.unlink(missing_ok=True)
                done = self.run_wrapper(*arguments, extra={"FAKE_SYNC_EXIT": "1"})
                self.assertEqual((done.returncode, lines_of(done)), (2, [line]))
                self.assertEqual([(call["argv"], call["cwd"]) for call in self.calls()],
                                 [(["sync", "--project", "apps/service", "--locked", "--quiet"], str(self.tree))])

    def test_e4_the_environment_s_mutmut_must_be_3_8_0(self) -> None:
        tail = ("'s environment; this wrapper runs mutmut 3.8.0: add mutmut==3.8.0 to the dev group of "
                "apps/service/pyproject.toml and run uv lock --project apps/service (slipwai migrate brings the "
                "wrapper for a newer pin)")
        for version, found in (("absent", "is not"), ("3.7.0", "3.7.0"), ("3.8.1", "3.8.1")):
            with self.subTest(version=version):
                done = self.run_wrapper("apps/service", extra={"FAKE_VERSION": version})
                self.assertEqual((done.returncode, lines_of(done)),
                                 (2, [f"mutation: mutmut {found} installed in apps/service" + tail]))
        done = self.run_wrapper("apps/service", extra={"FAKE_VERSION": "3.8.0"})
        self.assertEqual(lines_of(done), [SKELETON])

    def test_e4_the_version_is_read_in_the_service_s_environment_without_syncing_again(self) -> None:
        self.run_wrapper("apps/service")
        argv = [call["argv"] for call in self.calls()]
        self.assertEqual(len(argv), 2)
        self.assertEqual(argv[:1], [["sync", "--project", "apps/service", "--locked", "--quiet"]])
        read = argv[1][:5] if len(argv) > 1 else []
        self.assertEqual(read, ["run", "--no-sync", "--project", "apps/service", "python"])


class EnvironmentTest(Case):
    def test_e5_pytest_addopts_is_removed_from_every_call_and_named_once(self) -> None:
        done = self.run_wrapper("apps/service", extra={"PYTEST_ADDOPTS": "-n 2"})
        said = [line for line in lines_of(done) if "PYTEST_ADDOPTS" in line]
        self.assertEqual(said, ["mutation: PYTEST_ADDOPTS is not passed to mutmut (it would change how every mutant's "
                                "tests run); [tool.mutmut] pytest_add_cli_args is where this service adds pytest "
                                "options"])
        self.assertGreaterEqual(len(self.calls()), 2)
        for call in self.calls():
            self.assertIsNone(call["env"]["PYTEST_ADDOPTS"])
        self.log.unlink()
        self.assertEqual([line for line in lines_of(self.run_wrapper("apps/service")) if "PYTEST_ADDOPTS" in line], [])

    def test_e5_hold_every_other_variable_is_passed_through(self) -> None:
        """HOLD (teeth: hand `uv` an empty environment and see it fail)."""
        self.run_wrapper("apps/service", extra={"PYTHONPATH": "/some/path", "VIRTUAL_ENV": "/some/venv"})
        self.assertTrue(self.calls())
        for call in self.calls():
            self.assertEqual((call["env"]["PYTHONPATH"], call["env"]["VIRTUAL_ENV"]), ("/some/path", "/some/venv"))


class OneRunAtATimeTest(Case):
    def test_e6_a_second_run_of_one_service_is_refused_before_it_syncs_and_the_kernel_frees_the_lock(self) -> None:
        shutil.rmtree(self.service)
        self.make_service("apps/service", environment=True)
        wait = self.fifo("first")
        first = self.start("apps/service", extra={"FAKE_WAIT": wait})
        self.wait_for_calls(1)
        second = self.run_wrapper("apps/service")
        self.assertEqual(second.returncode, 2)
        self.assertEqual(len(lines_of(second)), 1)
        self.assertIn("apps/service/.venv/mutmut-run.lock", lines_of(second)[0])
        self.assertEqual(len(self.calls()), 1, "the refused run never reached uv sync")
        first.send_signal(signal.SIGKILL)
        first.communicate(timeout=30)
        self.release(wait)
        third = self.run_wrapper("apps/service")
        self.assertEqual(lines_of(third), [SKELETON])

    def test_e6_two_services_run_at_once_because_the_lock_is_per_service(self) -> None:
        for path in ("apps/service", "apps/other"):
            shutil.rmtree(self.tree / path, ignore_errors=True)
            self.make_service(path, environment=True)
        waits = {"apps/service": self.fifo("a"), "apps/other": self.fifo("b")}
        running = [self.start(path, extra={"FAKE_WAIT": wait}) for path, wait in waits.items()]
        self.wait_for_calls(2)
        for wait in waits.values():
            self.release(wait)
        for process in running:
            out, _ = process.communicate(timeout=30)
            self.assertEqual(out.strip().splitlines(), [SKELETON])


class NothingIsFetchedTest(Case):
    def test_e7_hold_uv_is_only_asked_to_sync_locked_or_to_run_without_syncing(self) -> None:
        """HOLD (teeth: drop `--no-sync` from one call and see it fail)."""
        for extra in ({}, {"FAKE_VERSION": "3.7.0"}):
            self.log.unlink(missing_ok=True)
            self.run_wrapper("apps/service", extra=extra)
            self.assertTrue(self.calls())
            for call in self.calls():
                argv = call["argv"]
                self.assertTrue((argv[0] == "sync" and "--locked" in argv) or argv[:2] == ["run", "--no-sync"], argv)

    def test_e7_hold_setup_writes_nothing_under_the_service_but_the_lock(self) -> None:
        before = sorted(path.relative_to(self.service) for path in self.service.rglob("*"))
        self.run_wrapper("apps/service")
        after = sorted(path.relative_to(self.service) for path in self.service.rglob("*"))
        self.assertEqual([path for path in after if path not in before],
                         [Path(".venv"), Path(".venv/mutmut-run.lock")])


if __name__ == "__main__":
    unittest.main()
