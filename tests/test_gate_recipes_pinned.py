"""What a Python project's gate recipes run first, pinned before S04-parallel-gate changes how they sync.

The slice makes each toolchain sync once per `make` run and the model targets install through a lockfile. What it
keeps, and what these tests hold, is the order: a sync of every service precedes the first `uv run` in every mode of
`scripts/verify`, `make install`, `make migrate` and `make dev` sync before the command they exist for, and the four
model targets install with npm and then run tsx's entry with the script and arguments they run today. How many syncs,
and whether the install is `install` or `ci`, is deliberately not pinned. Evidence is a stand-in's log, never output.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from stamp_fixture import CI_MARKERS, GIT_STATE, MAKE_STATE
from support import FactoryTestCase
from test_add_service import add_service

sys.dont_write_bytecode = True

STAND_IN = "#!/bin/sh\nprintf '%s\\t%s\\n' \"$(basename \"$0\")\" \"$*\" >> \"$STANDIN_LOG\"\nexit 0\n"
# npm's stand-in also writes the marker a real install leaves at the end, in the directory `--prefix` names.
NPM = STAND_IN.replace(
    "exit 0\n",
    'dir=.\nwhile [ $# -gt 0 ]; do [ "$1" = --prefix ] && dir=$2; shift; done\n'
    'mkdir -p "$dir/node_modules"\n: > "$dir/node_modules/.package-lock.json"\nexit 0\n')
APPS = ("apps/service", "apps/second")
MODES = (
    "--install-only", "--lint-only", "--typecheck-only", "--test-only", "--migrate", "--integration-only",
    "--adversarial-only", "",
)
TSX = "scripts/event-model/node_modules/tsx/dist/cli.mjs"
MODEL_TARGETS = {
    "model": f"{TSX} scripts/event-model/render.ts",
    "model-drawio": f"{TSX} scripts/event-model/render-drawio.ts",
    "check-drawio": f"{TSX} scripts/event-model/render-drawio.ts --check",
    "model-drawio-test": f"{TSX} --test scripts/event-model/board-plan.test.ts scripts/event-model/drawio.test.ts",
}


def calls(log: Path, tool: str) -> list[str]:
    """The arguments of every call a stand-in logged for `tool`, in order."""
    found = []
    for line in log.read_text(encoding="utf-8").splitlines() if log.exists() else []:
        name, _, arguments = line.partition("\t")
        if name == tool:
            found.append(arguments)
    return found


class GateRecipesPinnedTest(FactoryTestCase):
    template: Path

    @classmethod
    def setUpClass(cls) -> None:
        parent = Path(tempfile.mkdtemp(prefix="gate-recipes-"))
        cls.addClassCleanup(shutil.rmtree, parent, ignore_errors=True)
        cls.template = FactoryTestCase.generate(
            cls(), parent, "pinned", "event-modelling", "python", http="fastapi", event_store="postgres")
        done = add_service(cls.template, "second", "--language", "python")
        if done.returncode != 0:
            raise RuntimeError(done.stdout + done.stderr)

    def setUp(self) -> None:
        scratch = Path(tempfile.mkdtemp(prefix="gate-recipes-run-"))
        self.addCleanup(shutil.rmtree, scratch, ignore_errors=True)
        self.repo = scratch / "project"
        shutil.copytree(self.template, self.repo, symlinks=True)
        self.log = scratch / "standin.log"
        bin_dir = scratch / "bin"
        bin_dir.mkdir()
        for name in ("uv", "npm", "node"):
            (bin_dir / name).write_text(NPM if name == "npm" else STAND_IN, encoding="utf-8")
            (bin_dir / name).chmod(0o755)
        drop = CI_MARKERS + MAKE_STATE + GIT_STATE
        self.env = {key: value for key, value in os.environ.items() if key not in drop}
        self.env["PATH"] = f"{bin_dir}{os.pathsep}{self.env.get('PATH', '')}"
        self.env["STANDIN_LOG"] = str(self.log)

    def run_command(self, *command: str) -> None:
        done = subprocess.run(command, cwd=self.repo, env=self.env, text=True, capture_output=True, timeout=180)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)

    def assert_synced_before_first_run(self, first_run: str | None = None, every: bool = False) -> None:
        """A sync precedes the first `run` naming `first_run` (any, if None); with `every`, no sync follows it."""
        lines = calls(self.log, "uv")
        syncs = [i for i, arguments in enumerate(lines) if arguments.split()[:1] == ["sync"]]
        runs = [i for i, arguments in enumerate(lines)
                if arguments.split()[:1] == ["run"] and (first_run is None or first_run in arguments)]
        self.assertTrue(syncs, f"no sync was run: {lines}")
        if runs:
            self.assertLess(max(syncs) if every else min(syncs), runs[0], f"no sync before the first run: {lines}")
        elif first_run is not None:
            self.fail(f"the command {first_run!r} never ran: {lines}")

    def test_every_mode_of_the_verify_script_syncs_every_service_before_its_first_run(self) -> None:
        """Seam: `./scripts/verify <mode>` with a stand-in `uv`; each service named in a `--project` sync."""
        for mode in MODES:
            with self.subTest(mode=mode or "none"):
                self.log.write_text("", encoding="utf-8")
                self.run_command("./scripts/verify", *([mode] if mode else []))
                self.assert_synced_before_first_run(every=True)
                synced = " ".join(a for a in calls(self.log, "uv") if a.startswith("sync"))
                for app in APPS:
                    self.assertIn(f"--project {app}", synced, f"{app} was not synced in mode {mode or 'none'}")

    def test_make_install_syncs(self) -> None:
        """Seam: `make install` on a Python project; a sync is run, and nothing is run before it."""
        self.run_command("make", "install")
        self.assert_synced_before_first_run()

    def test_make_migrate_syncs_before_it_applies_the_migrations(self) -> None:
        """Seam: `make migrate` with Postgres; a sync precedes the `uv run` of `migrations/apply.py`."""
        self.run_command("make", "migrate")
        self.assert_synced_before_first_run("migrations/apply.py")

    def test_make_dev_syncs_before_it_starts_the_service(self) -> None:
        """Seam: `make dev` with a transport; a sync precedes the `uv run` of the service's `main` module."""
        self.run_command("make", "dev")
        self.assert_synced_before_first_run(".main")

    def test_each_model_target_installs_with_npm_then_runs_tsx_with_its_script(self) -> None:
        """Seam: the four model targets with stand-in `npm` and `node`; install first, then tsx's entry, unchanged."""
        for target, expected in MODEL_TARGETS.items():
            with self.subTest(target=target):
                self.log.write_text("", encoding="utf-8")
                # each target from a tree where the tooling is not installed, as a fresh clone's is
                shutil.rmtree(self.repo / "scripts/event-model/node_modules", ignore_errors=True)
                self.run_command("make", target)
                order = [line.split("\t")[0] for line in self.log.read_text(encoding="utf-8").splitlines()]
                self.assertEqual(order[0], "npm", order)
                self.assertEqual(order[-1], "node", order)
                self.assertEqual(order.count("node"), 1, order)
                npm = calls(self.log, "npm")[0].split()
                self.assertEqual(npm[:2], ["--prefix", "scripts/event-model"])
                self.assertIn(npm[2], ("install", "ci"))
                self.assertEqual(calls(self.log, "node"), [expected])


if __name__ == "__main__":
    unittest.main()
