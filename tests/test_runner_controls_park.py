"""A run parks on a control that changed in content, whatever the record of its stat facts says (D56; AC-S02-2 to -8).

The record that lets the runner skip re-reading a control must never become a time-based signature. Every example
here but the last is a hold, green before the record existed: the runner is run for real against a fake harness
whose iterations edit the gates in the ways the record could be fooled by, and the log is read back. A hold is
shown to have teeth by making the record reuse a hash on size and modification time alone.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from support import FactoryTestCase
from test_cruise_runner import cruise, enable, fake_harness, logged, outside_a_run

from slipwai.project.cruise import LOG

GATE = "scripts/check-ux-gates.py"
# What an iteration does to a gate, written once beside the fake harness: it is a script of its own because the
# edits that matter are the ones that put a stat fact back.
MUTATE = """
import os, sys
from pathlib import Path
how, name = sys.argv[1], Path(sys.argv[2])
status = name.stat()
data = bytearray(name.read_bytes())
if how == "append":
    name.write_bytes(bytes(data) + b"# treat a crash as skipped\\n")
elif how == "in-place":
    data[0] = (data[0] + 1) % 256
    name.write_bytes(bytes(data))
    os.utime(name, ns=(status.st_atime_ns, status.st_mtime_ns))
elif how == "rename":
    data[0] = (data[0] + 1) % 256
    other = name.with_name(name.name + ".new")
    other.write_bytes(bytes(data))
    os.utime(other, ns=(status.st_atime_ns, status.st_mtime_ns))
    os.replace(other, name)
elif how == "touch":
    os.utime(name)
elif how == "same-bytes":
    name.write_bytes(bytes(data))
elif how == "unreadable":
    name.chmod(0)
"""


def mutating(directory: str, behaviour: str) -> dict[str, str]:
    """A fake harness whose iterations run `behaviour`, a shell fragment that may call `mutate <how> <path>`."""
    (Path(directory) / "mutate.py").write_text(MUTATE)
    return fake_harness(Path(directory), f"""mkdir -p specs && touch "specs/progress-$n"
mutate() {{ {sys.executable} {directory}/mutate.py "$@"; }}
{behaviour}""")


class RunnerControlsParkTest(FactoryTestCase):
    def parks_naming(self, how: str) -> None:
        """Hold: an iteration that edits a gate by `how` parks the run naming it `(modified)` on its log entry."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, f"parks-{how}", "standard", "python")
            enable(repo, max_iterations="3")  # a run that failed to park ends here, instead of going on for ever
            env = mutating(directory, f"""if [ "$n" -eq 1 ]; then mutate {how} {GATE}; fi
echo "cruise: continue\"""")
            parked = cruise(repo, "run", "--no-park", env=env)
            self.assertEqual(parked.returncode, 3, parked.stdout + parked.stderr)
            self.assertIn(f"cruise: parked — iteration 1 changed a gate or a control of the run — {GATE} (modified)",
                          parked.stdout)
            self.assertEqual(logged(repo)[-1]["controls_changed"], [f"{GATE} (modified)"])

    def test_hold_a_line_appended_to_a_gate_parks_the_run(self) -> None:
        """AC-S02-2 (hold)."""
        self.parks_naming("append")

    def test_hold_a_gate_rewritten_in_place_at_its_size_with_its_time_restored_parks_the_run(self) -> None:
        """AC-S02-3 (hold): same size, modification time put back — the change time is what shows it."""
        self.parks_naming("in-place")

    def test_hold_a_gate_replaced_by_rename_with_a_same_size_file_of_the_old_time_parks_the_run(self) -> None:
        """AC-S02-4 (hold): the identity of the file is what shows it."""
        self.parks_naming("rename")

    def test_hold_an_iteration_that_only_touches_a_gate_or_rewrites_its_bytes_does_not_park_for_it(self) -> None:
        """AC-S02-5 (hold, the park half): the reads half is in `test_runner_controls`."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "touches", "standard", "python")
            enable(repo)
            env = mutating(directory, f"""case "$n" in
  1) mutate touch {GATE}; echo "cruise: continue";;
  2) mutate same-bytes {GATE}; echo "cruise: continue";;
  *) echo "cruise: done";;
esac""")
            done = cruise(repo, "run", "--no-park", env=env)
            self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
            self.assertEqual(["controls_changed" in entry for entry in logged(repo)], [False, False, False])

    def test_hold_a_control_a_person_edits_while_the_run_is_parked_is_not_charged_to_the_next_iteration(self) -> None:
        """AC-S02-6 (hold): iteration 1 parks the run for a person; once its entry is written the person edits a gate
        and writes under `specs/`, which resumes it. Iteration 2 reports no change; iteration 3, which edits the same
        gate, parks naming it."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "person", "standard", "python")
            enable(repo)
            env = mutating(directory, f"""case "$n" in
  1) echo "cruise: parked: a person must decide";;
  2) echo "cruise: continue";;
  *) mutate append {GATE}; touch .specify/cruise.stop; echo "cruise: continue";;
esac""")
            runner = subprocess.Popen(["python3", "scripts/agents/cruise.py", "run"], cwd=repo, text=True,
                                      stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                      env=outside_a_run(env))
            try:
                # The entry is written after the iteration's after-signature: the run is parked, and a person acts.
                deadline = time.monotonic() + 60
                while not (repo / LOG).is_file() and time.monotonic() < deadline:
                    time.sleep(0.05)
                time.sleep(0.5)
                (repo / GATE).write_text((repo / GATE).read_text() + "# kept on purpose\n")
                (repo / "specs/answer.md").write_text("here you are\n")
                output, _ = runner.communicate(timeout=60)
            finally:
                if runner.poll() is None:
                    runner.terminate()
                    runner.communicate()
            ended = subprocess.CompletedProcess(runner.args, runner.returncode, output, "")
            self.assertEqual(ended.returncode, 0, ended.stdout + ended.stderr)
            self.assertIn("cruise: something changed; resuming", ended.stdout)
            entries = logged(repo)
            self.assertEqual(len(entries), 3, ended.stdout)
            self.assertEqual([entry.get("controls_changed") for entry in entries], [None, None, [f"{GATE} (modified)"]])
            self.assertIn(f"cruise: parked — iteration 3 changed a gate or a control of the run — {GATE} (modified)",
                          ended.stdout)

    def test_hold_a_deleted_control_and_a_script_added_beside_the_gates_are_changes_and_an_install_is_not(self) -> None:
        """AC-S02-7 (hold)."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "deleted", "standard", "python")
            enable(repo, max_iterations="3")
            env = mutating(directory, f"""mkdir -p tools/ux-gates && touch "tools/ux-gates/installed-$n"
if [ "$n" -eq 1 ]; then rm {GATE}; printf 'raise SystemExit(0)\\n' > scripts/check-nothing.py; fi
echo "cruise: continue\"""")
            parked = cruise(repo, "run", "--no-park", env=env)
            self.assertEqual(parked.returncode, 3, parked.stdout + parked.stderr)
            changed = ["scripts/check-nothing.py (added)", f"{GATE} (deleted)"]
            self.assertEqual(logged(repo)[-1]["controls_changed"], sorted(changed))

    def test_hold_a_control_unreadable_after_the_iteration_is_reported_deleted_as_it_is_today(self) -> None:
        """AC-S02-8 (hold): a file that cannot be opened is absent from the signature, so it compares as deleted;
        no hash recorded for it is reused. Skipped where the process can read a file whatever its mode (root)."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "unreadable", "standard", "python")
            probe = Path(directory) / "probe"
            probe.write_text("x")
            probe.chmod(0)
            if os.access(probe, os.R_OK):
                self.skipTest("this process reads a file whatever its mode, so none is unreadable here")
            enable(repo, max_iterations="3")
            env = mutating(directory, f"""if [ "$n" -eq 1 ]; then mutate unreadable {GATE}; fi
echo "cruise: continue\"""")
            parked = cruise(repo, "run", "--no-park", env=env)
            self.assertEqual(parked.returncode, 3, parked.stdout + parked.stderr)
            self.assertEqual(logged(repo)[-1]["controls_changed"], [f"{GATE} (deleted)"])
