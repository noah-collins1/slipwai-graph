"""The runner reads a control's content once while its size, times and identity stand (D56; AC-S02-1, -5, -9 to -11).

`controls_signature()` is what the runner compares before and after an iteration to see whether the iteration
edited a gate. It is still a comparison of content; what changes is that a file whose stat facts read as recorded,
and were recorded safely long after they were written, is not opened again. These tests load the runner's script
in a child process under the interpreter's audit hook and count what a call opened — never a timing — and put the
clock the record reads at a point ten seconds on, so that a file written a moment ago is older than the record's
two-second margin without the test sleeping.
"""
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from support import FactoryTestCase

PROBE = '''
import importlib.util, json, os, sys, time, types
sys.dont_write_bytecode = True
seen, armed = [], [False]
def hook(event, arguments):
    if armed[0] and event == "open" and arguments and isinstance(arguments[0], (str, bytes, os.PathLike)):
        seen.append(os.path.abspath(os.fsdecode(arguments[0])))
sys.addaudithook(hook)
specification = importlib.util.spec_from_file_location("cruise_probed", "scripts/agents/cruise.py")
cruise = importlib.util.module_from_spec(specification)
sys.modules["cruise_probed"] = cruise
specification.loader.exec_module(cruise)
ROOT = str(cruise.ROOT)
def opened(under=""):
    """Every file inside the project opened since the last call, as the project spells it, once per open."""
    found = sorted(os.path.relpath(path, ROOT) for path in seen if path.startswith(ROOT + os.sep))
    del seen[:]
    return [path for path in found if path.startswith(under)]
def later(seconds=10):
    return lambda: time.time_ns() + seconds * 10**9
armed[0] = True
exec(sys.argv[1])
print(json.dumps(result))
'''
GATE = "scripts/check-ux-gates.py"


def probe(repo: Path, snippet: str) -> dict:
    """Run `snippet` in a child with the runner's script loaded as `cruise`; it sets `result`, which comes back."""
    done = subprocess.run(["python3", "-c", PROBE, snippet], cwd=repo, text=True, capture_output=True)
    assert done.returncode == 0, done.stderr
    return json.loads(done.stdout.splitlines()[-1])


class RunnerControlsTest(FactoryTestCase):
    def test_a_later_signature_over_controls_no_one_touched_opens_no_control_and_equals_the_first(self) -> None:
        """AC-S02-1: the second and every later signature of the process opens nothing for content."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "once", "standard", "python")
            seen = probe(repo, """
cruise.CONTROL_RECORD.clock = later()
first = cruise.controls_signature(); first_reads = opened()
later_signatures = [cruise.controls_signature() for _ in range(5)]
result = {"first_reads": sorted(set(first_reads)), "files": sorted(first), "later_reads": opened(),
          "equal": all(each == first for each in later_signatures)}""")
        self.assertGreater(len(seen["files"]), 10, "the signature covers the gates, the Makefile and the hook files")
        self.assertEqual(seen["first_reads"], seen["files"], "the first signature opens every control")
        self.assertEqual(seen["later_reads"], [])
        self.assertTrue(seen["equal"])

    def test_a_touched_or_same_bytes_file_is_read_once_and_not_again_while_it_stays_unchanged(self) -> None:
        """AC-S02-5, the reads: touching a gate (or rewriting it with the bytes it has) moves its times, so the
        next signature opens that file alone, finds the same hash, and the one after opens nothing."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "touched", "standard", "python")
            seen = probe(repo, f"""
cruise.CONTROL_RECORD.clock = later()
first = cruise.controls_signature(); opened()
os.utime("{GATE}")
after_touch = cruise.controls_signature(); touch_reads = opened()
settled = cruise.controls_signature(); settled_reads = opened()
with open("{GATE}", "rb") as handle: same = handle.read()
with open("{GATE}", "wb") as handle: handle.write(same)
opened()
after_rewrite = cruise.controls_signature(); rewrite_reads = opened()
settled_again = cruise.controls_signature(); settled_again_reads = opened()
result = {{"touch_reads": touch_reads, "settled_reads": settled_reads, "rewrite_reads": rewrite_reads,
          "settled_again_reads": settled_again_reads,
          "same": first == after_touch == settled == after_rewrite == settled_again}}""")
        self.assertEqual(seen["touch_reads"], [GATE])
        self.assertEqual(seen["settled_reads"], [])
        self.assertEqual(seen["rewrite_reads"], [GATE])
        self.assertEqual(seen["settled_again_reads"], [])
        self.assertTrue(seen["same"], "the same bytes are the same signature, whatever the times say")

    def test_a_file_modified_within_two_seconds_of_the_moment_it_was_hashed_is_read_again(self) -> None:
        """AC-S02-9: the record is taken as of ten seconds on; the gate's modification time is then set one second
        short of that moment, so it is not safely older than the hashing — it is read at every signature, and the
        files that are safely old are not."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "window", "standard", "python")
            seen = probe(repo, f"""
cruise.CONTROL_RECORD.clock = later()
cruise.controls_signature(); opened()
near = time.time_ns() + 9 * 10**9
os.utime("{GATE}", ns=(near, near))
cruise.controls_signature(); first = opened()
cruise.controls_signature(); second = opened()
cruise.controls_signature(); third = opened()
result = {{"first": first, "second": second, "third": third}}""")
        self.assertEqual((seen["first"], seen["second"], seen["third"]), ([GATE], [GATE], [GATE]))

    def test_a_platform_that_reports_no_change_time_or_no_identity_has_every_control_read_every_time(self) -> None:
        """AC-S02-10: handed a stat result with all four facts, the record reuses a hash; handed one without a
        change time, or with an inode of 0, it reuses nothing and every control is read at every signature."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "platform", "standard", "python")
            seen = probe(repo, """
def stripped(**gone):
    def report(status):
        facts = {"st_size": status.st_size, "st_mtime_ns": status.st_mtime_ns, "st_ctime_ns": status.st_ctime_ns,
                 "st_ino": status.st_ino, "st_dev": status.st_dev}
        for name, value in gone.items():
            if value is None: del facts[name]
            else: facts[name] = value
        return types.SimpleNamespace(**facts)
    return report
result = {}
for name, report in (("full", None), ("no change time", stripped(st_ctime_ns=None)),
                     ("no identity", stripped(st_ino=0))):
    cruise.CONTROL_RECORD = cruise.bookkeeping.Record(strict=True, report=report) if report else \\
        cruise.bookkeeping.Record(strict=True)
    cruise.CONTROL_RECORD.clock = later()
    files = len(cruise.controls_signature()); opened()
    cruise.controls_signature(); again = opened()
    cruise.controls_signature(); and_again = opened()
    result[name] = {"files": files, "again": len(again), "and_again": len(and_again)}""")
        full = seen["full"]
        self.assertEqual((full["again"], full["and_again"]), (0, 0), "with all four facts the hash is reused")
        for name in ("no change time", "no identity"):
            files = seen[name]["files"]
            self.assertEqual((seen[name]["again"], seen[name]["and_again"]), (files, files), name)

    def test_hold_a_new_runner_process_hashes_every_control_and_consults_nothing_from_an_earlier_one(self) -> None:
        """AC-S02-11, a hold: today every signature reads everything, and the record is the process's and never
        written, so the first signature of a second process over a tree that changed while no runner was alive
        opens every control and sees the change."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "process", "standard", "python")
            snippet = """
cruise.CONTROL_RECORD.clock = later()
signature = cruise.controls_signature()
result = {"signature": signature, "reads": opened()}"""
            first = probe(repo, snippet)
            (repo / GATE).write_text((repo / GATE).read_text() + "# changed while no runner was alive\n")
            second = probe(repo, snippet)
        self.assertEqual(sorted(second["signature"]), sorted(first["signature"]))
        self.assertEqual(sorted(set(second["reads"])), sorted(second["signature"]), "every control was opened")
        self.assertNotEqual(second["signature"][GATE], first["signature"][GATE])
        self.assertEqual({path for path in second["signature"] if second["signature"][path]
                          != first["signature"][path]}, {GATE})
