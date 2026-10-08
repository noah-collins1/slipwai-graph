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
# What uv 0.12.21 prints on a real mismatch (a manifest the lock does not agree with), read from a run, and the offline
# failure of a sync with an empty cache: the first is the only one of the two that is a lock disagreement.
LOCKED = ("error: The lockfile at `uv.lock` needs to be updated, but `--locked` was provided.\n\n"
          "hint: To update the lockfile, run `uv lock`.\n")
NO_LOCK = ("error: Unable to find lockfile at `uv.lock`, but `--locked` was provided. To create a lockfile, run `uv "
           "lock` or `uv sync` without the flag.\n")
OFFLINE = ("error: Failed to download `mypy==2.3.1`\n  cause: Network connectivity is disabled, but the requested "
           "data wasn't found in the cache for: `https://files.pythonhosted.org/mypy.whl`\n\n"
           "hint: `mypy` (v2.3.1) was included because `demo-service:dev` (v0.1.0) depends on `mypy`\n")
FAKE_UV = f"""#!{sys.executable}
import json, os, sys
args = sys.argv[1:]
names = ("PYTEST_ADDOPTS", "PYTHONPATH", "VIRTUAL_ENV")
with open(os.environ["FAKE_LOG"], "a", encoding="utf-8") as log:
    log.write(json.dumps({{"argv": args, "cwd": os.getcwd(), "env": {{k: os.environ.get(k) for k in names}}}}) + "\\n")
if args[0] == "sync":
    if os.environ.get("FAKE_WAIT"):
        open(os.environ["FAKE_WAIT"], encoding="utf-8").read()
    sys.stderr.write(os.environ.get("FAKE_SYNC_STDERR", {LOCKED!r}))
    sys.exit(int(os.environ.get("FAKE_SYNC_EXIT", "0")))
if args[:2] == ["run", "--no-sync"] and "importlib.metadata" in args[-1]:
    version = os.environ.get("FAKE_VERSION", "3.8.0")
    if version == "absent":
        sys.stderr.write(os.environ.get("FAKE_PROBE_STDERR", ""))
        sys.exit(1)
    print(version)
    sys.exit(0)
sys.stderr.write(os.environ.get("FAKE_GENERATE_STDERR", ""))
sys.exit(97)
"""
NO_FORK = "import os; del os.fork"
HOST = "mutation: mutmut needs os.fork, which this host does not have; run it under WSL"
NO_UV = "mutation: uv is not on PATH; install it to run mutmut (see scripts/verify)"
# Where a run that passes every check ends in this module: the fake `uv` answers nothing but the version and the sync,
# so mutmut's generation, the first thing after the checks, fails (T005's examples are `test_mutmut_verdict`'s).
PASSED = "mutation: mutmut could not generate mutants for apps/service (exit 97)"


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
        self.assertEqual(lines_of(done), [PASSED])

    def test_e4_the_version_is_read_in_the_service_s_environment_without_syncing_again(self) -> None:
        self.run_wrapper("apps/service")
        argv = [call["argv"] for call in self.calls()]
        self.assertEqual(argv[:1], [["sync", "--project", "apps/service", "--locked", "--quiet"]])
        read = argv[1][:5] if len(argv) > 1 else []
        self.assertEqual(argv[2][:3] if len(argv) > 2 else [], ["run", "--no-sync", "--project"], "then generation")
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
        self.assertEqual(lines_of(third), [PASSED])

    def test_e6_two_services_run_at_once_because_the_lock_is_per_service(self) -> None:
        for path in ("apps/service", "apps/other"):
            shutil.rmtree(self.tree / path, ignore_errors=True)
            self.make_service(path, environment=True)
        waits = {"apps/service": self.fifo("a"), "apps/other": self.fifo("b")}
        running = [self.start(path, extra={"FAKE_WAIT": wait}) for path, wait in waits.items()]
        self.wait_for_calls(2)
        for wait in waits.values():
            self.release(wait)
        for path, process in zip(waits, running, strict=True):
            out, _ = process.communicate(timeout=30)
            self.assertEqual(out.strip().splitlines(), [PASSED.replace("apps/service", path)])


class CleanSlateTest(Case):
    def test_e8_a_mutants_directory_the_delete_could_not_remove_is_exit_2_and_generation_never_starts(self) -> None:
        if os.geteuid() == 0:
            self.skipTest("root can remove what a read-only directory holds")
        stale = self.service / "mutants" / "sub"
        stale.mkdir(parents=True)
        (stale / "old.py.meta").write_text('{"exit_code_by_key": {"x": 0}}', encoding="utf-8")
        stale.chmod(0o555)
        self.addCleanup(stale.chmod, 0o755)
        done = self.run_wrapper("apps/service", "--file", "src/pkg/a.py")
        self.assertEqual(done.returncode, 2, lines_of(done))
        self.assertEqual(lines_of(done)[-1], "mutation: apps/service/mutants/ could not be removed; delete it, then "
                                             "run this again")
        self.assertEqual([call["argv"][0] for call in self.calls()], ["sync", "run"], "setup only, no generation")
        self.assertTrue((stale / "old.py.meta").exists(), "the stale report is left for its owner, never read")


class ToolFailureTest(Case):
    """Every subprocess the wrapper judges by exit status says what the tool said where it fails (D212 item 5)."""

    SYNC = "mutation: uv sync --locked failed for apps/service (exit {code}){said}"

    def test_e9_a_sync_that_fails_for_another_reason_says_uv_s_last_error_line_and_is_no_lock_line(self) -> None:
        for stderr, code, said in (
                (OFFLINE, 1, ": cause: Network connectivity is disabled, but the requested data wasn't found in the "
                             "cache for: `https://files.pythonhosted.org/mypy.whl`"),
                ("error: Project directory `apps/nope` does not exist\n", 2,
                 ": error: Project directory `apps/nope` does not exist"),
                ("", 1, "")):
            with self.subTest(stderr=stderr[:30]):
                self.log.unlink(missing_ok=True)
                done = self.run_wrapper("apps/service", extra={"FAKE_SYNC_EXIT": str(code), "FAKE_SYNC_STDERR": stderr})
                self.assertEqual((done.returncode, lines_of(done)), (2, [self.SYNC.format(code=code, said=said)]))
                self.assertEqual([call["argv"][0] for call in self.calls()], ["sync"], "mutmut never started")

    def test_e9_hold_both_messages_uv_prints_for_a_lock_that_disagrees_keep_the_lock_line(self) -> None:
        """HOLD (teeth: report uv's last line for every failure and see it fail)."""
        for stderr in (LOCKED, NO_LOCK):
            with self.subTest(stderr=stderr[:40]):
                done = self.run_wrapper("apps/service", extra={"FAKE_SYNC_EXIT": "1", "FAKE_SYNC_STDERR": stderr})
                self.assertEqual((done.returncode, lines_of(done)), (2, [
                    "mutation: apps/service/uv.lock does not agree with apps/service/pyproject.toml; run uv lock "
                    "--project apps/service, then this again"]))

    def test_e9_a_version_probe_that_fails_says_what_it_said_beside_the_mutmut_line(self) -> None:
        said = "importlib.metadata.PackageNotFoundError: No package metadata was found for mutmut"
        done = self.run_wrapper("apps/service", extra={
            "FAKE_VERSION": "absent", "FAKE_PROBE_STDERR": f"Traceback (most recent call last):\n{said}\n"})
        self.assertEqual(done.returncode, 2)
        self.assertTrue(lines_of(done)[0].startswith(
            f"mutation: mutmut is not installed in apps/service's environment ({said}); this wrapper runs mutmut "
            "3.8.0: "), lines_of(done))

    def test_e9_a_generation_that_fails_says_the_last_line_it_printed(self) -> None:
        stderr = "Traceback\nImportError: no mutmut here\n"
        done = self.run_wrapper("apps/service", extra={"FAKE_GENERATE_STDERR": stderr})
        self.assertEqual(done.returncode, 2)
        self.assertEqual(lines_of(done)[-1], "mutation: mutmut could not generate mutants for apps/service (exit 97): "
                                             "ImportError: no mutmut here")


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
