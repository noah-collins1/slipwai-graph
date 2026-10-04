"""An adopted repository's gate is serial (S04-parallel-gate R6; AC-S04-24 to -27; experimental, as `AGENTS.md` says).

Its `verify` is not the stamped gate, and its three ratchet runs read and write one `baseline.json`, so its Makefile
carries a bare `.NOTPARALLEL:` and `make -j verify` runs as `make verify` does. A generated project's does not.
Recorded `lint`, `typecheck` and `test` are stand-ins that log `start` and `end` and, between them, wait a bounded
while for another stand-in's start and log `met` or `alone`: the evidence is that log, never a clock.
"""
from __future__ import annotations

import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

from parallel_gate import gate_environment, log_lines, run_make
from support import FactoryTestCase
from test_adopt import repository, slipwai
from test_candidates import adopted
from test_layout import DELIVERY

from slipwai.scaffold import project_files, write_project
from slipwai.selection import Selection
from slipwai.services import default_apps

sys.dont_write_bytecode = True
DIRECTIVE = re.compile(r"^# [^\n]+\n\.NOTPARALLEL:\n", re.M)
CHECKS = ("lint", "typecheck", "test")
# Starts, waits (bounded: `STANDIN_TICKS` fiftieths of a second) for another stand-in to start or to be in flight,
# says which, ends. `lint` and `typecheck` are red with one finding named for each, so the ratchet has a baseline to
# record; a red `test` would be refused, not recorded, until a person quarantines it.
STAND_IN = """#!/bin/sh
log() { printf '%s\\t%s\\n' "$1" "$2" >> "$STANDIN_LOG"; }
starts() { grep -c '^start' "$STANDIN_LOG"; }
in_flight() { echo $(($(starts) - $(grep -c '^end' "$STANDIN_LOG"))); }
log start "$1"
first=$(starts); n=0; seen=alone
while [ "$n" -lt "${STANDIN_TICKS:-0}" ]; do
  if [ "$(in_flight)" -ge 2 ] || [ "$(starts)" -gt "$first" ]; then seen=met; break; fi
  sleep 0.05; n=$((n + 1))
done
log "$seen" "$1"
[ "$1" = test ] && { log end "$1"; exit 0; }
echo "src/$1.js:1:1: no-$1: $1 found something"
log end "$1"
exit 1
"""
SCRIPTS = {name: f"sh standin.sh {name}" for name in CHECKS}
FILES = {
    "package.json": json.dumps({"name": "shop", "private": True, "scripts": SCRIPTS}),
    "standin.sh": STAND_IN,
    "src/lint.js": "\n", "src/typecheck.js": "\n", "src/test.js": "\n",
}


def confirmed(parent: Path, name: str = "shop") -> Path:
    """An adopted repository whose `lint`, `typecheck` and `test` are the stand-ins, with `shop` confirmed."""
    repo = repository(parent, name, FILES)
    result = slipwai(repo, "adopt", "--yes")
    assert result.returncode == 0, result.stderr
    return repo


def serial_comment(makefile: str) -> bool:
    return bool(DIRECTIVE.search(makefile)) and makefile.count(".NOTPARALLEL") == 1


class AdoptedMakefileTest(FactoryTestCase):
    def test_a_wrapped_application_carries_the_bare_directive_and_one_comment(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = adopted(Path(directory))
            self.assertEqual(slipwai(repo, "adopt", "--confirm", "shop").returncode, 0)
            self.assertTrue(serial_comment((repo / "delivery/Makefile").read_text()))

    def test_the_refusal_carries_it_too(self) -> None:
        """Nothing confirmed is not stamped either: the rule is `not stamped, so serial`."""
        with tempfile.TemporaryDirectory() as directory:
            makefile = (adopted(Path(directory)) / "delivery/Makefile").read_text()
            self.assertIn("verify: ## Refuses until", makefile)
            self.assertTrue(serial_comment(makefile))

    def test_a_moved_layout_with_a_generated_service_beside_it_carries_it(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "wrapped"
            apps = default_apps("python", "none", Selection({"http": "none"}))
            write_project(repo, "wrapped", "standard", "none", apps, layout=DELIVERY)
            self.assertTrue(serial_comment((repo / "delivery/Makefile").read_text()))

    def test_a_generated_project_carries_none_whatever_its_backends(self) -> None:
        """Hold: `stamped()` answers yes for every generated project, so none carries the line
        (teeth: emit it always)."""
        for backend, frontend, http in (("python", "none", "none"), ("python", "react-vite", "fastapi"),
                                        ("typescript", "none", "fastify"), ("typescript", "react-vite", "none")):
            with self.subTest(backend=backend, frontend=frontend, http=http):
                apps = default_apps(backend, frontend, Selection({"http": http}))
                makefile = project_files("held", "event-modelling", "none", apps)["Makefile"]
                self.assertNotIn(".NOTPARALLEL", makefile)


class AdoptedRunTest(FactoryTestCase):
    def setUp(self) -> None:
        sys.dont_write_bytecode = True
        scratch = Path(tempfile.mkdtemp(prefix="parallel-gate-adopted-"))
        self.addCleanup(shutil.rmtree, scratch, ignore_errors=True)
        self.scratch = scratch
        self.repo = confirmed(scratch)
        (scratch / "bin").mkdir()

    def make(self, repo: Path, log: Path, ticks: int, *args: str):
        env = gate_environment(self.scratch / "bin", log, {"STANDIN_TICKS": str(ticks), "RATCHET_TIGHTEN": None})
        return run_make(repo, env, "-f", "delivery/Makefile", *args)

    def assert_serial(self, log: Path) -> None:
        """No stand-in met another, and each ended before the next started, in the gate's order."""
        events = log_lines(log)
        self.assertEqual([a for e, a in events if e == "alone"], list(CHECKS), events)
        self.assertNotIn("met", [e for e, _ in events], events)
        self.assertEqual([(e, a) for e, a in events if e in ("start", "end")],
                         [(e, c) for c in CHECKS for e in ("start", "end")], events)

    def test_recorded_checks_do_not_overlap_under_j(self) -> None:
        log = self.scratch / "e3.log"
        done = self.make(self.repo, log, 40, "-j", "verify")
        self.assertEqual(done.returncode, 0, done.stdout[-3000:] + done.stderr[-3000:])
        self.assert_serial(log)

    def test_ratchet_tighten_runs_its_three_targets_one_after_another(self) -> None:
        """`ratchet-tighten`'s sub-make reads the same Makefile, so `-j` does not make its three targets overlap."""
        log = self.scratch / "tighten.log"
        done = self.make(self.repo, log, 40, "-j", "ratchet-tighten")
        self.assertEqual(done.returncode, 0, done.stdout[-3000:] + done.stderr[-3000:])
        self.assert_serial(log)

    def test_a_first_run_under_j_records_the_baseline_a_serial_one_does(self) -> None:
        serial_repo = self.scratch / "serial"
        shutil.copytree(self.repo, serial_repo, symlinks=True)
        serial = self.make(serial_repo, self.scratch / "serial.log", 0, "verify")
        self.assertEqual(serial.returncode, 0, serial.stdout[-3000:] + serial.stderr[-3000:])
        parallel = self.make(self.repo, self.scratch / "parallel.log", 40, "-j", "verify")
        self.assertEqual(parallel.returncode, 0, parallel.stdout[-3000:] + parallel.stderr[-3000:])
        recorded = json.loads((self.repo / "delivery/baseline.json").read_text(encoding="utf-8"))
        self.assertEqual(sorted(recorded["shop"]), ["lint", "typecheck"])
        self.assertEqual(recorded, json.loads((serial_repo / "delivery/baseline.json").read_text(encoding="utf-8")))
