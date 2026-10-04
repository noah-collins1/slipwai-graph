"""One sync per `make` run, by every way into a Python mode (R1, AC-S04-34 to -40, -14): `ci`, `migrate`, `dev`,
`install`, the spellings published outside the Makefile, the environment, and a project with no `.venv`.

A **hold** is true today and must stay true; each says so in its docstring and was seen to have teeth.
"""
from __future__ import annotations

import sys
import unittest

from parallel_gate import (
    ParallelGateTestCase,
    log_lines,
    overlapped,
    run_lines,
    sync_ended_before_any_run,
    sync_lines,
    synced_projects,
    syncs_precede_runs,
)

from slipwai.catalog import CATALOG, axis_default
from slipwai.project.native_commands import service_commands
from slipwai.scaffold import project_files
from slipwai.selection import resolve_selection
from slipwai.services import App, add_service, default_apps

sys.dont_write_bytecode = True

# Where a spelling that skips the sync may sit: the Makefile's own recipes, and the script that reads it.
MAY_CARRY = ("Makefile",)


class WaysIntoAModeTest(ParallelGateTestCase):
    SHAPE = "db"

    def test_e7_make_ci_syncs_once(self) -> None:
        """AC-S04-34: `make ci` with its database targets leaves one sync line."""
        self.assert_passed(self.make("ci"))
        self.assertEqual(synced_projects(self.log), ["apps/service"], sync_lines(self.log))

    def test_e8_make_migrate_syncs_once_before_the_migration(self) -> None:
        """AC-S04-35: one sync, and it precedes the `uv run` of `migrations/apply.py`."""
        self.assert_passed(self.make("migrate"))
        self.assertEqual(synced_projects(self.log), ["apps/service"], sync_lines(self.log))
        self.assertTrue(any("migrations/apply.py" in a for a in run_lines(self.log)), run_lines(self.log))
        self.assertTrue(syncs_precede_runs(self.log))

    def test_e10_install_and_test_in_one_command_sync_once(self) -> None:
        """AC-S04-37: `make install test` is one make process, so one sync."""
        self.assert_passed(self.make("install", "test"))
        self.assertEqual(synced_projects(self.log), ["apps/service"], sync_lines(self.log))

    def test_e13_no_environment_variable_makes_a_mode_skip_the_sync(self) -> None:
        """HOLD (AC-S04-40): with the non-syncing argument absent, any variable set to any value, the script still
        syncs first."""
        names = ("CI", "UV_NO_SYNC", "UV_FROZEN", "UV_OFFLINE", "VERIFY_FORCE", "VERIFY_SYNCED", "SYNCED", "SKIP_SYNC",
                 "NO_SYNC", "VERIFY_SKIP_SYNC", "MAKELEVEL", "A_NEW_SWITCH", "X7Q", "synced")
        for value in ("1", "true", "--synced", "yes", ""):
            with self.subTest(value=value):
                self.forget_log()
                self.assert_passed(self.run_in("./scripts/verify", "--test-only", env=dict.fromkeys(names, value)))
                self.assertEqual(synced_projects(self.log), ["apps/service"], sync_lines(self.log))
                self.assertTrue(syncs_precede_runs(self.log))


class DevTest(ParallelGateTestCase):
    SHAPE = "api"
    VENV = False

    def test_e9_make_dev_syncs_once_before_the_service_starts(self) -> None:
        """HOLD (AC-S04-36): the recipe's own `--install-only` line is today's one sync, and it precedes the run."""
        self.assert_passed(self.make("dev"))
        self.assertEqual(synced_projects(self.log), ["apps/service"], sync_lines(self.log))
        self.assertTrue(any(".main" in a for a in run_lines(self.log)), run_lines(self.log))
        self.assertTrue(syncs_precede_runs(self.log))

    def test_e16_without_a_venv_two_targets_under_j_wait_for_one_sync(self) -> None:
        """AC-S04-14: `make -j check-openapi lint` with no `.venv`: both pass, and the sync ended before either started;
        a second concurrent sync would have been held beside the first and logged `met`."""
        self.assertFalse((self.repo / "apps/service/.venv").exists())
        self.assert_passed(self.make("-j", "check-openapi", "lint", env={"STANDIN_SYNC_HOLD": "1"}))
        self.assertFalse(overlapped(self.log), log_lines(self.log))
        self.assertEqual(len(sync_lines(self.log)), 1, sync_lines(self.log))
        self.assertTrue(sync_ended_before_any_run(self.log), log_lines(self.log))


def apps_of(backend: str, http: str, frontend: bool, services: int) -> list[App]:
    """A project of this backend and transport answer, with a browser app or not, and this many services."""
    answers = resolve_selection({"http": http}, "event-modelling", backend, "none")
    apps = default_apps(backend, "react-vite" if frontend else "none", answers)
    for extra in range(services - 1):
        apps = add_service(apps, f"more{extra}", backend, answers)
    return apps


class NothingPublishedSaysTheNonSyncingSpellingTest(ParallelGateTestCase):
    SHAPE = "plain"

    def test_e12_only_the_makefile_and_the_scripts_say_it(self) -> None:
        """HOLD (AC-S04-39): across every backend, with a transport and without, with a browser app and without, and
        with several services, the CI workflow, the pages and `service_commands()` never name `--synced`."""
        said: list[str] = []
        for backend in CATALOG["backends"]:
            for http in dict.fromkeys(("none", axis_default("http", backend, "none"))):
                for frontend in (False, True):
                    for services in (1, 2):
                        apps = apps_of(backend, http, frontend, services)
                        files = project_files("sweep", "event-modelling", "none", apps)
                        for path, text in files.items():
                            if "--synced" in text and path not in MAY_CARRY and not path.startswith("scripts/verify"):
                                said.append(f"{backend} {http} {frontend} {services}: {path}")
                for command in service_commands(backend, "apps/service").values():
                    if "--synced" in command:
                        said.append(f"{backend}: service_commands {command!r}")
        self.assertEqual(sorted(set(said)), [])


if __name__ == "__main__":
    unittest.main()
