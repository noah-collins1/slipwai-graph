"""S41 T040 (A7, B2, A10 · D212 item 5): one install at a time, whoever starts it, and a lock that cannot strand a run.

The wrapper's `npm ci` and the Makefile's install target (`python3 scripts/stryker-mutation.py --install npm ci`, which
takes the same lock and runs the same command) are held to one lock file, `.stryker-tmp/install.lock` at the project
root, naming its holder's pid; it is broken when that process is gone, and the line that waits and the one that gives up
name it. The wrapper finds the project root from the service, and reads a root-relative or absolute `--file` as the
service-relative path it names. The fake `npm` is `test_stryker_verdict`'s: `ci` sleeps `ci_sleep` seconds.
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import signal
import subprocess
import sys
import time
import unittest
from pathlib import Path

from test_stryker_list import SCRIPT, loaded
from test_stryker_verdict import SERVICE, VerdictCase, mutant, report

sys.dont_write_bytecode = True
TEST_SELECTION = {"reads": ["assets/languages/typescript/scripts/stryker-mutation.py"]}
OK = {"report": report(src__health_ts=[mutant("Killed")])}


class Fresh(VerdictCase):
    installed = False

    def start(self, plan: dict, *arguments: str, cwd: str | None = None) -> subprocess.Popen[str]:
        self.plan.write_text(json.dumps(plan), encoding="utf-8")
        env = {**os.environ, "PATH": f"{self.bin}{os.pathsep}{os.environ['PATH']}", "FAKE_LOG": str(self.log),
               "FAKE_PLAN": str(self.plan)}
        for marker in ("CI", "GITHUB_ACTIONS", "GITLAB_CI"):
            env.pop(marker, None)
        one = subprocess.Popen([sys.executable, "-B", str(SCRIPT), *arguments], cwd=cwd or self.tree, env=env,
                               text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, start_new_session=True)
        self.addCleanup(self.stop, one)
        return one

    @staticmethod
    def stop(one: subprocess.Popen[str]) -> None:
        with contextlib.suppress(OSError):
            os.killpg(one.pid, signal.SIGKILL)  # the wrapper and a fake `npm` it left running

    def installing(self) -> None:
        deadline = time.time() + 20
        while not any(call["argv"] == ["ci"] for call in self.calls()):
            self.assertLess(time.time(), deadline, "the install never started")
            time.sleep(0.05)

    @property
    def lock(self) -> Path:
        return self.tree / ".stryker-tmp" / "install.lock"

    def installs(self) -> list[str]:
        return [call["argv"][0] for call in self.calls() if call["argv"][0] in ("ci", "ci-done")]


class InstallLockTest(Fresh):
    def test_e1_a_run_killed_during_the_install_leaves_a_lock_the_next_run_breaks(self) -> None:
        """A7: the lock named its holder, the holder is gone, so the next run does not wait for a half-hour."""
        first = self.start({"ci_sleep": 30}, SERVICE, "--file", "src/health.ts")
        self.installing()
        self.assertEqual(self.lock.read_text(encoding="utf-8").split()[0], str(first.pid))
        os.kill(first.pid, signal.SIGTERM)
        first.wait(timeout=30)  # not `communicate`: the fake `npm` it left running still holds the pipe
        self.assertTrue(self.lock.exists(), "a killed run is expected to leave its lock")
        begun = time.time()
        code, lines = self.run_wrapper(OK, "--file", "src/health.ts")
        self.assertEqual(code, 0, lines)
        self.assertLess(time.time() - begun, 20, lines)

    def test_e2_a_run_that_waits_names_the_lock_and_its_holder_and_a_finished_install_is_not_repeated(self) -> None:
        first = self.start({**OK, "ci_sleep": 3}, SERVICE, "--file", "src/health.ts")
        self.installing()
        code, lines = self.run_wrapper(OK, "--file", "src/health.ts")
        out, _ = first.communicate(timeout=60)
        self.assertEqual((first.returncode, code), (0, 0), (out, lines))
        self.assertIn(f"mutation: another run of the install of this project is running (pid {first.pid}, "
                      f"{self.lock}); waiting for it", lines)
        self.assertEqual(self.installs(), ["ci", "ci-done"], "the second run installed again")

    def test_e3_a_run_that_cannot_get_the_lock_says_which_lock_and_whose(self) -> None:
        module = loaded(SCRIPT)
        module.LOCK_WAIT = 0.4
        self.lock.parent.mkdir(parents=True)
        self.lock.write_text(f"{os.getpid()}\n", encoding="utf-8")
        said = io.StringIO()
        with contextlib.redirect_stdout(said), module.file_lock(self.lock, "the install of this project") as held:
            pass
        self.assertFalse(held)
        self.assertIn(f"(pid {os.getpid()}, {self.lock}) did not finish", said.getvalue())

    def test_e4_the_makefiles_install_takes_the_same_lock_and_runs_npm_ci_once_beside_a_run(self) -> None:
        """B2: `make -j2 mutation-full build-packages` ran two `npm ci` in one root; both now go through the lock."""
        make = self.start({**OK, "ci_sleep": 2}, "--install", "npm", "ci")
        self.installing()
        code, lines = self.run_wrapper(OK, "--file", "src/health.ts")
        out, _ = make.communicate(timeout=60)
        self.assertEqual((make.returncode, code), (0, 0), (out, lines))
        self.assertEqual(self.installs(), ["ci", "ci-done"], "two installs overlapped or repeated")
        self.assertTrue((self.tree / "node_modules/.package-lock.json").is_file())

    def test_e5_the_install_mode_runs_nothing_but_npm_ci(self) -> None:
        for arguments in (["--install"], ["--install", "npm", "install"], ["--install", "npm", "ci", "x"]):
            with self.subTest(arguments=arguments):
                one = self.start(OK, *arguments)
                out, _ = one.communicate(timeout=30)
                self.assertEqual(one.returncode, 2, out)
                self.assertEqual(self.calls(), [])


class RootTest(Fresh):
    def test_e6_a_run_from_inside_the_service_installs_at_the_project_root(self) -> None:
        """A10: `cd apps/service && …stryker-mutation.py . --file src/health.ts` ran `npm ci` in `apps/service`."""
        (self.tree / "package.json").write_text('{"workspaces": ["apps/*"]}', encoding="utf-8")
        one = self.start(OK, ".", "--file", "src/health.ts", cwd=str(self.tree / SERVICE))
        out, _ = one.communicate(timeout=60)
        self.assertEqual(one.returncode, 0, out)
        installs = [call for call in self.calls() if call["argv"] == ["ci"]]
        self.assertEqual([call["cwd"] for call in installs], [str(self.tree.resolve())], out)
        self.assertTrue((self.tree / "node_modules/.package-lock.json").is_file())
        self.assertFalse((self.tree / SERVICE / "node_modules").exists())
        self.assertEqual(self.execs()[0]["cwd"], str((self.tree / SERVICE).resolve()))

    def test_e7_a_root_relative_or_absolute_file_is_the_service_relative_path_it_names(self) -> None:
        (self.tree / SERVICE / "src/health.ts").write_text("export const a = 'x';\n", encoding="utf-8")
        for given in (f"{SERVICE}/src/health.ts", str(self.tree / SERVICE / "src/health.ts"), "src/health.ts",
                      f"{SERVICE}/src/gone.ts"):
            with self.subTest(given=given):
                self.log.unlink(missing_ok=True)
                code, lines = self.run_wrapper(OK, "--file", given)
                scoped = [call["argv"][-1] for call in self.execs()]
                wanted = "src/gone.ts" if given.endswith("gone.ts") else "src/health.ts"
                self.assertEqual(scoped, [wanted], lines)
                self.assertIn(f"mutation: scoped to 1 given file(s): {wanted}", lines)


if __name__ == "__main__":
    unittest.main()
