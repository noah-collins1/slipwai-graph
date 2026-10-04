"""A root Makefile that includes the delivery one keeps its own `-j` (S04-parallel-gate D95; AC-S04-67 to -70).

The bare `.NOTPARALLEL:` the delivery Makefile carries holds only a run started on that file. A repository's own
targets, beside the include, run under `-j` as they did before adoption; `ratchet-tighten` is held from every door,
since its sub-make starts on the delivery Makefile. Concurrency is shown by a barrier and a log, never a clock: each
target logs `start`, waits (bounded) for the other to be in flight, and logs `met` or `alone`, then `end`.
"""
from __future__ import annotations

import re
import shutil
import sys
import tempfile
from pathlib import Path

from parallel_gate import gate_environment, log_lines, run_make
from support import FactoryTestCase
from test_parallel_gate_adopted import CHECKS, confirmed

sys.dont_write_bytecode = True
HELD = "make -f delivery/Makefile -j verify"
# `own.sh NAME OTHER LOG`: logs start, waits for OTHER (a name in the same log) to be in flight, logs met or alone, end.
OWN = """#!/bin/sh
log() { printf '%s\\t%s\\n' "$1" "$2" >> "$OWN_LOG"; }
in_flight() { [ "$(grep -c "^start.$1\\$" "$OWN_LOG")" -gt "$(grep -c "^end.$1\\$" "$OWN_LOG")" ]; }
log start "$1"; n=0; seen=alone
while [ "$n" -lt 100 ]; do
  if in_flight "$2"; then seen=met; break; fi
  sleep 0.05; n=$((n + 1))
done
log "$seen" "$1"
# Having met the other, stay in flight until it has decided too, so the one that decides last still sees this one.
n=0
decided() { grep -qE "^(met|alone).$1\\$" "$OWN_LOG"; }
while [ "$seen" = met ] && [ "$n" -lt 100 ] && ! decided "$2"; do sleep 0.05; n=$((n + 1)); done
log end "$1"
"""
# `beside.sh NAME`: the same, but waits for one of the recorded stand-ins (in `STANDIN_LOG`) to be in flight.
BESIDE = """#!/bin/sh
log() { printf '%s\\t%s\\n' "$1" "$2" >> "$OWN_LOG"; }
flying() { [ "$(grep -c '^start' "$STANDIN_LOG" 2>/dev/null)" -gt "$(grep -c '^end' "$STANDIN_LOG" 2>/dev/null)" ]; }
log start "$1"; n=0; seen=alone
while [ "$n" -lt 100 ]; do
  if flying; then seen=met; break; fi
  sleep 0.05; n=$((n + 1))
done
log "$seen" "$1"; log end "$1"
"""
OWN_TARGETS = """
own-a:
\t@sh own.sh a b
own-b:
\t@sh own.sh b a
own-c:
\t@sh beside.sh c
"""


class IncludingRootTest(FactoryTestCase):
    def setUp(self) -> None:
        sys.dont_write_bytecode = True
        scratch = Path(tempfile.mkdtemp(prefix="parallel-gate-include-"))
        self.addCleanup(shutil.rmtree, scratch, ignore_errors=True)
        self.scratch = scratch
        (scratch / "bin").mkdir()
        self.repo = confirmed(scratch)
        (self.repo / "own.sh").write_text(OWN)
        (self.repo / "beside.sh").write_text(BESIDE)
        root = self.repo / "Makefile"
        self.assertIn("-include delivery/Makefile", root.read_text())
        root.write_text(root.read_text() + OWN_TARGETS)

    def make(self, repo: Path, name: str, *args: str):
        env = gate_environment(self.scratch / "bin", self.scratch / f"{name}.standin",
                               {"STANDIN_TICKS": "40", "RATCHET_TIGHTEN": None,
                                "OWN_LOG": str(self.scratch / f"{name}.own")})
        done = run_make(repo, env, *args)
        self.assertEqual(done.returncode, 0, done.stdout[-3000:] + done.stderr[-3000:])
        return log_lines(self.scratch / f"{name}.own"), log_lines(self.scratch / f"{name}.standin")

    def assert_serial(self, events: list[tuple[str, str]]) -> None:
        self.assertEqual([a for e, a in events if e == "alone"], list(CHECKS), events)
        self.assertEqual([(e, a) for e, a in events if e in ("start", "end")],
                         [(e, c) for c in CHECKS for e in ("start", "end")], events)

    def test_the_roots_own_targets_overlap_under_j_with_the_include_and_without_it(self) -> None:
        """AC-S04-67: both meet each other, and with the include line taken out the log is the same."""
        included, _ = self.make(self.repo, "included", "-j", "own-a", "own-b")
        self.assertEqual(sorted((e, a) for e, a in included if e == "met"), [("met", "a"), ("met", "b")], included)
        root = self.repo / "Makefile"
        root.write_text(re.sub(r"^-include .*\n", "", root.read_text(), flags=re.M))
        self.assertNotIn("-include", root.read_text())
        without, _ = self.make(self.repo, "without", "-j", "own-a", "own-b")
        self.assertEqual(sorted((e, a) for e, a in without if e == "met"), [("met", "a"), ("met", "b")], without)

    def test_ratchet_tighten_at_the_root_runs_its_three_one_after_another(self) -> None:
        """AC-S04-68: the sub-make starts on the delivery Makefile, so it is held from this door."""
        _, standins = self.make(self.repo, "tighten", "-j", "ratchet-tighten")
        self.assert_serial(standins)

    def test_an_own_target_beside_ratchet_tighten_is_not_made_to_wait_for_its_three(self) -> None:
        """AC-S04-69: the own target sees a stand-in in flight; the three still do not overlap each other."""
        own, standins = self.make(self.repo, "beside", "-j", "own-c", "ratchet-tighten")
        self.assertIn(("met", "c"), own, own)
        self.assert_serial(standins)


class WordsAreRightTest(FactoryTestCase):
    def test_what_adopt_writes_never_says_whatever_j_says_without_naming_the_held_command(self) -> None:
        """AC-S04-70: the step on the adoption page and the root Makefile block say what the include does."""
        with tempfile.TemporaryDirectory() as directory:
            repo = confirmed(Path(directory))
            seen = {}
            for path in repo.rglob("*"):
                if ".git" in path.parts or "node_modules" in path.parts or not path.is_file():
                    continue
                try:
                    seen[path.relative_to(repo).as_posix()] = path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    continue
            for name, text in seen.items():
                if re.search(r"whatever\s+`-j`\s+says", text):
                    self.assertIn(HELD, text, name)
            block = seen["Makefile"]
            self.assertIn("leaves your own `-j` alone", block)
            self.assertIn(HELD, block)
            page = next(text for name, text in seen.items() if name.endswith("docs/adoption.md"))
            self.assertIn("leaves your own `-j` alone", page)
            self.assertIn(HELD, page)
