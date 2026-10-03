"""The paths a controls signature covers are as fresh as the signature (D56; AC-S02-1, -2, -7, T015).

A harness's registry row may project a hook file, and that file is a control: an iteration that edits it has made
a gate pass by changing what runs it. Which files are hook files is read from `registry.json`, so a row an
iteration gains, or a person keeps, changes which paths a signature walks. The set is derived again whenever the
hash of the registry is not the one it was derived from, and that hash comes from the same record as every other
control's, so a registry no one touches is not opened for content on a later signature (AC-S02-1).
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import time
from pathlib import Path

from support import FactoryTestCase
from test_cruise_runner import enable, fake_harness, logged, outside_a_run
from test_runner_controls import probe

from slipwai.project.cruise import LOG

REGISTRY = "scripts/agents/registry.json"
HOOK = ".newharness/hooks.json"
# Gives the `claude` row a projected hook file: what a registry change an iteration makes looks like.
GAIN = f"""
import json
from pathlib import Path
path = Path("{REGISTRY}")
table = json.loads(path.read_text(encoding="utf-8"))
for row in table["harnesses"]:
    if row["key"] == "claude":
        row["hooks"]["projection"] = {{"where": "{HOOK}"}}
path.write_text(json.dumps(table, indent=2) + "\\n", encoding="utf-8")
Path("{HOOK}").parent.mkdir(exist_ok=True)
Path("{HOOK}").write_text('{{"hooks": {{}}}}\\n', encoding="utf-8")
"""


class RunnerControlsPathsTest(FactoryTestCase):
    def test_a_hook_file_a_registry_row_gains_is_held_from_the_next_signature_on(self) -> None:
        """T015, the probe seam: the signature taken after the registry gained a hook row covers that file, and a
        later edit to it changes the signature."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "gains", "standard", "python")
            seen = probe(repo, f"""
cruise.CONTROL_RECORD.clock = later()
before = cruise.controls_signature()
exec({GAIN!r})
gained = cruise.controls_signature()
with open("{HOOK}", "a", encoding="utf-8") as handle: handle.write("# edited by an iteration\\n")
edited = cruise.controls_signature()
result = {{"changed": cruise.controls_changed(before, gained), "then": cruise.controls_changed(gained, edited)}}""")
        self.assertEqual(seen["changed"], [f"{HOOK} (added)", f"{REGISTRY} (modified)"])
        self.assertEqual(seen["then"], [f"{HOOK} (modified)"])

    def test_a_registry_change_is_read_once_and_a_registry_no_one_touches_is_not_opened_again(self) -> None:
        """AC-S02-1 with T015: the path set follows the registry's hash from the record, so the changed registry
        and the hook file it names are each opened once, and the signatures after that open nothing."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "rereads", "standard", "python")
            seen = probe(repo, f"""
cruise.CONTROL_RECORD.clock = later()
cruise.controls_signature(); opened()
exec({GAIN!r}); opened()
cruise.controls_signature(); changed = opened()
cruise.controls_signature(); settled = opened()
cruise.controls_signature(); settled_again = opened()
result = {{"changed": sorted(set(changed)), "settled": settled, "again": settled_again}}""")
        self.assertEqual(seen["changed"], [HOOK, REGISTRY])
        self.assertEqual((seen["settled"], seen["again"]), ([], []))

    def test_an_iteration_that_gains_a_hook_row_is_told_so_and_a_later_edit_of_that_file_parks_the_run(self) -> None:
        """T015, through the runner: iteration 1 gives a row a hook file and the run parks naming both changes; a
        person keeps it and resumes; iteration 2 edits the file and the run parks naming it `(modified)`."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "gained", "standard", "python")
            enable(repo)
            (Path(directory) / "gain.py").write_text(GAIN, encoding="utf-8")
            env = fake_harness(Path(directory), f"""mkdir -p specs && touch "specs/progress-$n"
case "$n" in
  1) {sys.executable} {directory}/gain.py; echo "cruise: continue";;
  *) echo "# edited" >> {HOOK}; touch .specify/cruise.stop; echo "cruise: continue";;
esac""")
            runner = subprocess.Popen(["python3", "scripts/agents/cruise.py", "run"], cwd=repo, text=True,
                                      stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                      env=outside_a_run(env))
            try:
                deadline = time.monotonic() + 60
                while not (repo / LOG).is_file() and time.monotonic() < deadline:
                    time.sleep(0.05)
                time.sleep(0.5)  # the entry is written after the iteration's after-signature: the run is parked
                (repo / "specs/answer.md").write_text("kept on purpose\n", encoding="utf-8")
                output, _ = runner.communicate(timeout=60)
            finally:
                if runner.poll() is None:
                    runner.terminate()
                    runner.communicate()
            self.assertEqual(runner.returncode, 0, output)
            entries = logged(repo)
            self.assertEqual(len(entries), 2, output)
            self.assertEqual(entries[0]["controls_changed"], [f"{HOOK} (added)", f"{REGISTRY} (modified)"])
            self.assertEqual(entries[1]["controls_changed"], [f"{HOOK} (modified)"])
