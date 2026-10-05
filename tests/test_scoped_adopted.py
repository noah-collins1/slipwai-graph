"""R12 (AC-S06-16; experimental, as `AGENTS.md` says): an adopted repository runs its gate, saying it has no record.

Where the gate is not the stamped one (`gate.stamped()` false: a wrapped application, a moved layout) there is no
baseline and no stamp to compare with, so `make -f delivery/Makefile verify-scoped` says so and runs
`$(MAKE) -f delivery/Makefile verify` with its status. The adopted `verify` rule's bytes, its `GATE` and `SERIAL`, are
what they were.
"""
from __future__ import annotations

import re
import shutil
import sys
import tempfile
from pathlib import Path

from parallel_gate import gate_environment, log_lines, run_make
from support import FactoryTestCase
from test_adopt import slipwai
from test_candidates import adopted
from test_layout import DELIVERY
from test_parallel_gate_adopted import CHECKS, confirmed, serial_comment

from slipwai.project.adopted_targets import GATE
from slipwai.scaffold import project_files, write_project
from slipwai.selection import Selection
from slipwai.services import default_apps

sys.dont_write_bytecode = True
SAYS = "this layout has no verification-dependency record yet"


class AdoptedScopedTest(FactoryTestCase):
    def setUp(self) -> None:
        sys.dont_write_bytecode = True
        scratch = Path(tempfile.mkdtemp(prefix="scoped-adopted-"))
        self.addCleanup(shutil.rmtree, scratch, ignore_errors=True)
        self.scratch = scratch
        self.repo = confirmed(scratch)
        (scratch / "bin").mkdir()

    def make(self, repo: Path, log: Path, *args: str):
        env = gate_environment(self.scratch / "bin", log, {"STANDIN_TICKS": "0", "RATCHET_TIGHTEN": None})
        return run_make(repo, env, "-f", "delivery/Makefile", *args)

    def copy(self, name: str) -> Path:
        repo = self.scratch / name
        shutil.copytree(self.repo, repo, symlinks=True)
        return repo

    def test_e1_it_says_it_has_no_record_and_then_the_full_gate_runs(self) -> None:
        """A wrapped application in a moved layout: the line first, then the gate's own output and exit status."""
        scoped = self.make(self.copy("scoped"), self.scratch / "scoped.log", "verify-scoped")
        plain = self.make(self.copy("plain"), self.scratch / "plain.log", "verify")
        self.assertEqual(scoped.returncode, 0, scoped.stdout[-3000:] + scoped.stderr[-3000:])
        lines = scoped.stdout.splitlines()
        self.assertTrue(lines[0].startswith("verify-scoped: ") and SAYS in lines[0], lines[:2])
        self.assertEqual("\n".join(lines[1:]) + "\n", plain.stdout, "what followed is not the full gate's output")
        started = [e for e, _ in log_lines(self.scratch / "scoped.log") if e == "start"]
        self.assertEqual(started, ["start"] * len(CHECKS))

    def test_e1_the_gates_failure_is_the_targets(self) -> None:
        for name in ("failing-scoped", "failing-plain"):
            standin = self.copy(name) / "standin.sh"
            passing = '[ "$1" = test ] && { log end "$1"; exit 0; }'
            failing = passing.replace("exit 0", "exit 3")
            standin.write_text(standin.read_text(encoding="utf-8").replace(passing, failing), encoding="utf-8")
        scoped = self.make(self.scratch / "failing-scoped", self.scratch / "f1.log", "verify-scoped")
        plain = self.make(self.scratch / "failing-plain", self.scratch / "f2.log", "verify")
        self.assertNotEqual(plain.returncode, 0, "the fixture's gate did not fail")
        self.assertEqual(scoped.returncode, plain.returncode, scoped.stdout[-2000:] + scoped.stderr[-2000:])
        self.assertIn(SAYS, scoped.stdout)

    def test_e1_a_moved_layout_with_a_generated_service_and_a_wrapped_one_in_the_root_reach_it(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "moved"
            apps = default_apps("python", "none", Selection({"http": "none"}))
            write_project(repo, "moved", "standard", "none", apps, layout=DELIVERY)
            makefile = (repo / "delivery/Makefile").read_text(encoding="utf-8")
            self.assertIn(SAYS, makefile)
            self.assertNotIn("verify-scoped.py", makefile)
            wrapped = adopted(Path(directory))
            self.assertEqual(slipwai(wrapped, "adopt", "--confirm", "shop").returncode, 0)
            self.assertIn(SAYS, (wrapped / "delivery/Makefile").read_text(encoding="utf-8"))

    def test_e1_a_generated_project_does_not_say_it(self) -> None:
        """The stamped gate keeps the script's target, not the adopted one (hold: teeth, say it always)."""
        apps = default_apps("python", "none", Selection({"http": "none"}))
        makefile = project_files("held", "standard", "none", apps)["Makefile"]
        self.assertNotIn(SAYS, makefile)
        self.assertIn("verify-scoped.py", makefile)

    def test_e2_the_serial_directive_stays_and_follows_the_rule_convention(self) -> None:
        makefile = (self.repo / "delivery/Makefile").read_text(encoding="utf-8")
        self.assertTrue(serial_comment(makefile), "the one `.NOTPARALLEL:` is gone or doubled")
        rules = re.findall(r"^verify-scoped:.*\n((?:\t.*\n)+)", makefile, re.M)
        self.assertEqual(len(rules), 1)
        self.assertEqual(len(rules[0].splitlines()), 1, "the target is more than one recipe line")
        self.assertIn("$(MAKE) -f delivery/Makefile --no-print-directory verify", rules[0])
        self.assertIn(".PHONY: verify-scoped", makefile)

    def test_e2_the_target_is_serial_under_j(self) -> None:
        log = self.scratch / "j.log"
        env = gate_environment(self.scratch / "bin", log, {"STANDIN_TICKS": "40", "RATCHET_TIGHTEN": None})
        done = run_make(self.repo, env, "-f", "delivery/Makefile", "-j", "verify-scoped")
        self.assertEqual(done.returncode, 0, done.stdout[-3000:] + done.stderr[-3000:])
        events = log_lines(log)
        self.assertEqual([a for e, a in events if e == "alone"], list(CHECKS), events)

    def test_e3_hold_the_adopted_verify_rule_is_what_it_was(self) -> None:
        """HOLD: the adopted `verify` rule is `GATE` over the gate's dependencies, byte for byte (teeth: edit one)."""
        makefile = (self.repo / "delivery/Makefile").read_text(encoding="utf-8")
        found = re.search(
            r"^verify: (.*?) ## Full deterministic pre-commit gate\n\t@echo\n\t@echo 'verify: all gates passed'$",
            makefile, re.M)
        self.assertIsNotNone(found, "the adopted verify rule is not GATE")
        assert found is not None
        self.assertIn(GATE.format(dependencies=found.group(1)), makefile)
        self.assertEqual(makefile.count("\nverify:"), 1)
