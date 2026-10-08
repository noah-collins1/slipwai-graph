"""S42 Phase 4 (T036, T037, T039, T042, T043; the adversary's findings A1, A2, A4, A7, B3): what `mutmut-mutation.py`
holds against a run that is not what it seems, reproduced through the wrapper's boundary.

The harness is `test_mutmut_verdict`'s: the wrapper runs as a subprocess against a fake `uv` first on `PATH`. The
fake is that module's, read for the changes these examples need: an orphaned child of `mutmut run`, the `PYTEST_*`
environment each call is handed, and the probe's report on where mutmut was imported from. Undeclared, as
`test_mutmut_migrate` is: it reads the fragment and the generated starter's table.
"""
from __future__ import annotations

import os
import signal
import stat
import subprocess
import sys
import unittest
from typing import Any

from test_mutmut_config import loaded
from test_mutmut_verdict import FAKE_UV, KEY, SCRIPT, Case, lines_of

sys.dont_write_bytecode = True

LOG_ENV = ('json.dumps({"argv": args, "cwd": os.getcwd()})',
           'json.dumps({"argv": args, "cwd": os.getcwd(), "env": {k: v for k, v in os.environ.items() '
           'if k.startswith("PYTEST_")}})')

ORPHAN = ('write(json.loads(os.environ.get("FAKE_RESULTS", "{}")))',
          '''if os.environ.get("FAKE_ORPHAN"):
    child = os.fork()
    if child == 0:
        os.setsid()
        null = os.open(os.devnull, os.O_RDWR)
        for descriptor in (0, 1, 2):
            os.dup2(null, descriptor)
        import time
        time.sleep(60)
        os._exit(0)
    open(os.environ["FAKE_ORPHAN"], "w").write(str(child))
write(json.loads(os.environ.get("FAKE_RESULTS", "{}")))''')

PROBE = ('    print("3.8.0")\n',
         '    print("3.8.0")\n    if os.environ.get("FAKE_SHADOW"):\n'
         '        print("shadowed " + os.environ["FAKE_SHADOW"])\n')


def fake_uv() -> str:
    text = FAKE_UV
    for old, new in (LOG_ENV, ORPHAN, PROBE):
        assert old in text, "test_mutmut_verdict's fake uv no longer reads as this expects"
        text = text.replace(old, new)
    return text


class PhaseCase(Case):
    def setUp(self) -> None:
        super().setUp()
        (self.bin / "uv").write_text(fake_uv(), encoding="utf-8")
        (self.bin / "uv").chmod(0o755 | stat.S_IXUSR)

    def run_with(self, *arguments: str, extra: dict[str, str] | None = None,
                 **keywords: Any) -> subprocess.CompletedProcess[str]:
        """`run_wrapper` with more variables in the wrapper's environment."""
        saved = dict(os.environ)
        os.environ.update(extra or {})
        try:
            return self.run_wrapper(*arguments, **keywords)
        finally:
            os.environ.clear()
            os.environ.update(saved)


class OrphanTest(PhaseCase):
    """T036 (A1): a `mutmut run` child that outlives the wrapper keeps the lock."""

    def test_a1_a_run_that_leaves_a_child_alive_keeps_its_service_locked_and_the_next_run_is_refused(self) -> None:
        pidfile = self.root / "orphan.pid"
        first = self.run_with("apps/service", "--file", "src/pkg/a.py", extra={"FAKE_ORPHAN": str(pidfile)},
                              meta={"src/pkg/a.py": {KEY: None}}, results={"src/pkg/a.py": {KEY: 1}})
        orphan = int(pidfile.read_text(encoding="utf-8"))
        self.addCleanup(self.kill, orphan)
        self.assertEqual(first.returncode, 0)
        second = self.run_wrapper("apps/service", "--file", "src/pkg/a.py", meta={"src/pkg/a.py": {KEY: None}},
                                  results={"src/pkg/a.py": {KEY: 1}})
        self.assertEqual(second.returncode, 2)
        self.assertEqual(lines_of(second), ["mutation: another mutmut run of apps/service holds "
                                            "apps/service/.venv/mutmut-run.lock; wait for it, then run this again"])
        self.kill(orphan)
        third = self.run_wrapper("apps/service", "--file", "src/pkg/a.py", meta={"src/pkg/a.py": {KEY: None}},
                                 results={"src/pkg/a.py": {KEY: 1}})
        self.assertEqual(third.returncode, 0, "the lock is free once the child is gone")

    @staticmethod
    def kill(pid: int) -> None:
        try:
            os.kill(pid, signal.SIGKILL)
            os.waitpid(pid, 0)
        except (ProcessLookupError, ChildProcessError):
            pass
        for _ in range(100):
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                return
            import time
            time.sleep(0.05)


class ForgedMetaTest(PhaseCase):
    """T037 (A2): after the wrapper's own generation every code is null; only sources under `source_paths` are read."""

    FORGED = ("mutation: apps/service/src/pkg/a.py: mutmut's generation left an exit code on 1 mutant(s) before any "
              "test ran (a committed .meta file copied into mutants/?), so the verdict cannot be trusted")

    def test_a2_a_scoped_key_that_already_has_a_code_fails_the_run_naming_the_file(self) -> None:
        done = self.run_wrapper("apps/service", "--file", "src/pkg/a.py", meta={"src/pkg/a.py": {KEY: 1}},
                                results={"src/pkg/a.py": {KEY: 1}})
        self.assertEqual(done.returncode, 1)
        self.assertIn(self.FORGED, lines_of(done))
        self.assertEqual(self.started_mutmut(), [])

    def test_a2_a_sweep_of_a_forged_file_fails_the_same_way(self) -> None:
        done = self.run_wrapper("apps/service", meta={"src/pkg/a.py": {KEY: 1}}, results={"src/pkg/a.py": {KEY: 1}})
        self.assertEqual(done.returncode, 1)
        self.assertIn(self.FORGED, lines_of(done))

    def test_a2_a_meta_beside_a_test_or_outside_the_source_roots_is_never_a_verdict(self) -> None:
        meta = {"src/pkg/a.py": {KEY: None}, "tests/test_a.py": {"t.x_f__mutmut_1": 1},
                "scripts/b.py": {"b.x_f__mutmut_1": 0}, "src/pkg/readme.txt": {"r.x_f__mutmut_1": 0}}
        done = self.run_wrapper("apps/service", meta=meta, results={"src/pkg/a.py": {KEY: 1}})
        self.assertEqual(done.returncode, 0, lines_of(done))
        self.assertEqual(lines_of(done)[-1].split(" \u2014 ")[0], "mutation: 1 mutants: 1 killed, 0 no tests "
                                                                 "(reported, never failed); passed")

    def test_a2_a_ghost_meta_outside_the_roots_does_not_make_an_empty_sweep_pass(self) -> None:
        done = self.run_wrapper("apps/service", meta={"src/pkg/types.py": {}, "tests/ghost.py": {"g.x_f__mutmut_1": 1}})
        self.assertEqual(done.returncode, 1)
        self.assertEqual(lines_of(done)[-1], "mutation: mutmut found nothing to mutate in apps/service; a pass on "
                                             "nothing is not a pass")

    def test_a2_a_file_handed_over_that_the_table_does_not_take_is_not_run_on_a_copied_meta(self) -> None:
        done = self.run_wrapper("apps/service", "--file", "tests/test_a.py", meta={"tests/test_a.py": {KEY: None}},
                                results={"tests/test_a.py": {KEY: 0}})
        self.assertEqual(done.returncode, 0)
        self.assertEqual(self.started_mutmut(), [])


class ShadowedPackageTest(PhaseCase):
    """T039 (A4): the mutmut and libcst the run imports are the environment's, not a copy ahead of it."""

    def test_a4_a_package_found_ahead_of_the_environments_exits_2_naming_where_it_was_found(self) -> None:
        for name in ("mutmut", "libcst"):
            with self.subTest(package=name):
                done = self.run_with("apps/service", extra={"FAKE_SHADOW": f"{name} /elsewhere/{name}"},
                                     meta={"src/pkg/a.py": {KEY: None}}, results={"src/pkg/a.py": {KEY: 1}})
                self.assertEqual(done.returncode, 2)
                self.assertEqual(lines_of(done), [
                    f"mutation: {name} is imported from /elsewhere/{name}, not from apps/service's environment; a "
                    "package on PYTHONPATH ahead of the environment's is refused: remove it from PYTHONPATH"])
                self.assertEqual(self.started_mutmut(), [])

    def test_a4_hold_the_probe_asks_where_the_packages_are_imported_from(self) -> None:
        """HOLD (teeth: drop the location check from the probe and see it fail)."""
        module = loaded(SCRIPT)
        for needle in ("find_spec", "locate_file", "'mutmut'", "'libcst'"):
            self.assertIn(needle, module.VERSION_CODE)


SELECTION = '["tests", "--ignore=tests/integration"]'

CLI_ARGS = '["-p", "no:xdist"]'


def narrowed(selection: str | None = SELECTION, cli_args: str | None = CLI_ARGS, extra: str = "") -> str:
    lines = ["[tool.mutmut]", 'source_paths = ["src"]']
    if selection is not None:
        lines.append(f"pytest_add_cli_args_test_selection = {selection}")
    if cli_args is not None:
        lines.append(f"pytest_add_cli_args = {cli_args}")
    return "\n".join(lines) + "\n" + extra


def narrowing(setting: str, found: str, held: str) -> str:
    return (f"mutation: apps/service/pyproject.toml {setting} is {found}, not {held}, which narrows what the tests "
            "reach without anyone looking at it")


class PathsLeavingTheServiceTest(PhaseCase):
    """T042 (A7): a `--file` or an `also_copy` entry outside the service is refused or made relative."""

    def test_a7_an_absolute_path_inside_the_service_is_taken_as_the_file_relative_to_it(self) -> None:
        done = self.run_wrapper("apps/service", "--file", str(self.service / "src/pkg/a.py"),
                                meta={"src/pkg/a.py": {KEY: None}}, results={"src/pkg/a.py": {KEY: 1}})
        self.assertEqual(done.returncode, 0)
        self.assertEqual(lines_of(done)[0], "mutation: scoped to 1 given file(s): src/pkg/a.py \u2014 1 mutant(s)")

    def test_a7_a_path_that_is_not_within_the_service_exits_2_before_anything_starts(self) -> None:
        for given in (str(self.root / "elsewhere/a.py"), "../x.py", "src/../../x.py",
                      str(self.tree / "apps/other/a.py")):
            with self.subTest(file=given):
                done = self.run_wrapper("apps/service", "--file", given)
                self.assertEqual(done.returncode, 2)
                self.assertEqual(lines_of(done), [f"mutation: `{os.path.normpath(given)}` is not a path within "
                                                  "apps/service; give it relative to the service, without `..`"])
                self.assertEqual(self.calls(), [])

    def test_a7_an_also_copy_entry_that_leaves_mutants_exits_2_naming_it(self) -> None:
        for entry in ("../x", "/etc/passwd", "a/../../x", ".."):
            with self.subTest(entry=entry):
                (self.service / "pyproject.toml").write_text(narrowed(extra=f'also_copy = ["data", "{entry}"]\n'),
                                                             encoding="utf-8")
                done = self.run_wrapper("apps/service")
                self.assertEqual(done.returncode, 2)
                self.assertEqual(lines_of(done), [f'mutation: apps/service/pyproject.toml also_copy holds "{entry}", '
                                                  "which leaves apps/service/mutants/; keep it to paths within the "
                                                  "service"])
                self.assertEqual(self.calls(), [])

    def test_a7_hold_also_copy_entries_within_the_service_are_not_refused(self) -> None:
        (self.service / "pyproject.toml").write_text(narrowed(extra='also_copy = ["data", "a/b.json", "./c"]\n'),
                                                     encoding="utf-8")
        done = self.run_wrapper("apps/service", meta={"src/pkg/a.py": {KEY: None}}, results={"src/pkg/a.py": {KEY: 1}})
        self.assertEqual(done.returncode, 0, lines_of(done))


LOCK = """version = 1
[[package]]
name = "mutmut"
version = "3.8.0"
source = { registry = "https://pypi.org/simple" }
dependencies = [{ name = "libcst" }]
sdist = { url = "https://x/mutmut.tar.gz", hash = "sha256:aaa" }
wheels = [{ url = "https://x/mutmut.whl", hash = "sha256:bbb" }]
[[package]]
name = "libcst"
version = "1.9.0"
source = { registry = "https://pypi.org/simple" }
wheels = [{ url = "https://x/libcst-a.whl", hash = "sha256:ccc" },
          { url = "https://x/libcst-b.whl", hash = "sha256:ddd" }]
[[package]]
name = "pytest"
version = "9.1.1"
source = { registry = "https://pypi.org/simple" }
"""


class LockEntryTest(unittest.TestCase):
    """T043 (B3): the sweep reads each closure entry's source and hashes as well as its version."""

    def setUp(self) -> None:
        self.module = loaded(SCRIPT)

    def moved(self, old: str, new: str) -> bool:
        return bool(self.module.versions(None, LOCK) != self.module.versions(None, LOCK.replace(old, new)))

    def test_b3_the_same_version_with_other_hashes_or_another_source_is_a_move(self) -> None:
        for old, new in (("sha256:bbb", "sha256:eee"), ("sha256:aaa", "sha256:eee"), ("sha256:ddd", "sha256:eee"),
                         ('registry = "https://pypi.org/simple" }\ndependencies', 'registry = "https://evil/simple" }'
                          "\ndependencies"),
                         ('name = "libcst"\nversion = "1.9.0"\nsource = { registry = "https://pypi.org/simple" }',
                          'name = "libcst"\nversion = "1.9.0"\nsource = { git = "https://x/libcst" }')):
            with self.subTest(old=old, new=new):
                self.assertTrue(self.moved(old, new))

    def test_b3_hold_a_lock_that_did_not_change_and_a_package_outside_the_closure_is_not_a_move(self) -> None:
        """HOLD (teeth: include pytest in the closure and see it fail)."""
        self.assertEqual(self.module.versions(None, LOCK), self.module.versions(None, LOCK))
        self.assertFalse(self.moved('name = "pytest"\nversion = "9.1.1"', 'name = "pytest"\nversion = "9.1.1"\n'
                                    'wheels = [{ url = "u", hash = "sha256:zzz" }]'))
        self.assertFalse(self.moved("hash = \"sha256:bbb\"", "hash = \"sha256:bbb\""))

    def test_b3_a_bare_version_is_still_the_version_alone(self) -> None:
        found = self.module.versions(None, 'version = 1\n[[package]]\nname = "mutmut"\nversion = "3.8.0"\n')
        self.assertEqual(found, {"mutmut": ["3.8.0"]})


if __name__ == "__main__":
    unittest.main()
