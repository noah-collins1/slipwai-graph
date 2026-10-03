"""A log that is not what the runner left is read whole again, and answers what a whole read always answered
(D58; AC-S02-24 to -29, -32, -33).

The runner remembers the log only while the file reads exactly as it was after the runner's own append, and checks
that again before it appends. These examples change the log during an iteration — cut, deleted, replaced, edited in
place, appended to by another hand, half-written — from inside the fake harness, and read the numbers and the
`bookkeeping.log_bytes` counts back from the log. The last three are holds, green before the slice.
"""
from __future__ import annotations

import json
import subprocess
import tempfile
import threading
import time
from pathlib import Path

from support import FactoryTestCase
from test_cruise_runner import cruise, enable, fake_harness, logged, outside_a_run
from test_runner_log import seed

from slipwai.project.cruise import LOG

EDIT = """
import sys
with open(sys.argv[1], "r+b") as handle:
    data = bytearray(handle.read())
    data[data.index(b"0000000000000002") + 15] = ord("9")
    handle.seek(0)
    handle.write(bytes(data))
"""
HAND = '{"iteration": 99, "last_line": "cruise: continue", "fingerprint": "00000000000000ff"}'


def changing(directory: str, how: str) -> dict[str, str]:
    """A fake harness whose first iteration changes the log by `how` and whose later ones do nothing to it."""
    (Path(directory) / "edit.py").write_text(EDIT)
    log = "specs/cruise-log.jsonl"
    change = {
        "cut": f'head -n 3 {log} > "$d/cut"; cat "$d/cut" > {log}',
        "delete": f"rm {log}",
        "replace": f'cp {log} "$d/copy"; mv "$d/copy" {log}',
        "edit": f'python3 "$d/edit.py" {log}',
        "append": f"printf '%s\\n' '{HAND}' >> {log}",
        "half": f"printf '{{\"iteration\": 9, \"la' >> {log}",
    }[how]
    return fake_harness(Path(directory), f"""d=$(dirname "$0")
mkdir -p specs && touch "specs/progress-$n"
if [ "$n" -eq 1 ]; then {change}; fi
echo "cruise: continue\"""")


class RunnerLogStaleTest(FactoryTestCase):
    def two_iterations_after(self, how: str, seeded: int = 3) -> tuple[list[dict], int]:
        """Run two iterations, the first of which changes the log by `how`; the entries in the file afterwards,
        and the file's size."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, f"stale-{how}", "standard", "python")
            enable(repo, max_iterations="2")
            seed(repo, seeded)
            ended = cruise(repo, "run", "--no-park", env=changing(directory, how))
            self.assertEqual(ended.returncode, 0, ended.stdout + ended.stderr)
            return logged(repo), (repo / LOG).stat().st_size

    @staticmethod
    def counts(entries: list[dict]) -> list[int | None]:
        return [entry.get("bookkeeping", {}).get("log_bytes") for entry in entries]

    def whole_read(self, entries: list[dict], size: int) -> None:
        """The last entry's `log_bytes` is the whole file as it stood before that entry was appended."""
        last_line = len(json.dumps(entries[-1], ensure_ascii=False)) + 1
        self.assertEqual(self.counts(entries)[-1], size - last_line)

    def test_a_log_cut_during_an_iteration_is_appended_to_and_the_next_is_numbered_from_what_is_left(self) -> None:
        """AC-S02-24: ten entries, cut to three while iteration 11 runs: its entry is appended as today, the next
        iteration is numbered 5, and that entry's `log_bytes` is the size of the file it re-read — the three left
        and the one appended."""
        entries, _ = self.two_iterations_after("cut", seeded=10)
        self.assertEqual([entry["iteration"] for entry in entries], [1, 2, 3, 11, 5])
        reread = sum(len(json.dumps(entry, ensure_ascii=False)) + 1 for entry in entries[:4])
        first = self.counts(entries)[3]
        self.assertEqual(self.counts(entries)[3:], [first, reread])
        self.assertGreater(first or 0, 0, "the seeded log was read once at the start")

    def test_a_log_deleted_during_an_iteration_is_recreated_holding_that_one_entry(self) -> None:
        """AC-S02-25: deleted while iteration 4 runs; recreated holding that entry; the next is numbered 2 and
        reads that one-entry file whole."""
        entries, size = self.two_iterations_after("delete")
        self.assertEqual([entry["iteration"] for entry in entries], [4, 2])
        self.whole_read(entries, size)  # the file it re-read at the next iteration is the one entry

    def test_a_log_replaced_by_a_new_file_of_the_same_bytes_is_read_whole_at_the_next_iteration(self) -> None:
        """AC-S02-26: the number is what it would have been (3 + 1 + 1), and the entry's `log_bytes` is the whole
        file's size at that moment."""
        entries, size = self.two_iterations_after("replace")
        self.assertEqual([entry["iteration"] for entry in entries], [1, 2, 3, 4, 5])
        self.whole_read(entries, size)

    def test_a_log_edited_in_place_to_the_same_length_is_read_whole_at_the_next_iteration(self) -> None:
        """AC-S02-27: the count is the entries plus one, and `log_bytes` the file's size before the new entry."""
        entries, size = self.two_iterations_after("edit")
        self.assertEqual([entry["iteration"] for entry in entries], [1, 2, 3, 4, 5])
        self.assertEqual(entries[2]["fingerprint"], "0000000000000003")
        self.assertEqual(entries[1]["fingerprint"][:15] + "9", entries[1]["fingerprint"], "the edit landed")
        self.whole_read(entries, size)

    def test_an_entry_another_hand_appended_is_counted_and_the_log_is_read_whole(self) -> None:
        """AC-S02-28: three seeded and one by hand; iteration 1 is numbered 4 and the next counts the hand's entry
        as well, 6."""
        entries, size = self.two_iterations_after("append")
        self.assertEqual([entry["iteration"] for entry in entries], [1, 2, 3, 99, 4, 6])
        self.whole_read(entries, size)

    def test_hold_a_log_whose_last_line_is_not_a_whole_entry_ends_the_run_and_nothing_is_appended(self) -> None:
        """AC-S02-29 (hold), at the start: the run ends on the parse error as it does today."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "half-start", "standard", "python")
            enable(repo, max_iterations="2")
            seed(repo, 3)
            with (repo / LOG).open("a", encoding="utf-8") as handle:
                handle.write('{"iteration": 4, "la')
            before = (repo / LOG).read_bytes()
            ended = cruise(repo, "run", "--no-park", env=changing(directory, "append"))
            self.assertNotEqual(ended.returncode, 0)
            self.assertIn("line 1 column", ended.stderr)  # the parse error, as `main()` prints it
            self.assertEqual((repo / LOG).read_bytes(), before, "nothing was appended")
            self.assertFalse((Path(directory) / "calls").exists(), "no iteration was run")

    def test_hold_a_log_half_written_during_an_iteration_ends_the_run_at_the_next_read(self) -> None:
        """AC-S02-29 (hold), after a change: the entry is appended as today, the next read fails the same way,
        and no second iteration runs or is appended."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "half-later", "standard", "python")
            enable(repo, max_iterations="2")
            seed(repo, 3)
            ended = cruise(repo, "run", "--no-park", env=changing(directory, "half"))
            self.assertNotEqual(ended.returncode, 0)
            self.assertIn("line 1 column", ended.stderr)  # the parse error, as `main()` prints it
            self.assertEqual((Path(directory) / "calls").read_text().strip(), "1", "one iteration ran")
            self.assertEqual(len((repo / LOG).read_text().splitlines()), 4, "the half line and the entry share a line")

    def test_hold_status_where_tell_and_resume_print_what_they_printed_over_a_log_of_fifty(self) -> None:
        """AC-S02-32 (hold): the verbs that read the log whole once per invocation are untouched; their output over
        a log of fifty entries was captured from the script before the slice."""
        said = {"status": ("cruise: no runner is running here\n"
                           "cruise: 50 iteration(s) logged; the last ended 2026-10-03T10:50:30Z with "
                           "`cruise: continue`\n"),
                "where": "", "resume": "",
                "tell hello": ("cruise: queued; no runner is running here — the first iteration of the next run "
                               "carries it (`/cruise` starts one)\n")}
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "verbs", "standard", "python")
            enable(repo)
            (repo / LOG).parent.mkdir(exist_ok=True)
            (repo / LOG).write_text("".join(json.dumps({
                "iteration": n, "started": f"2026-10-0{1 + n % 3}T10:{n:02d}:00Z",
                "ended": f"2026-10-0{1 + n % 3}T10:{n:02d}:30Z", "harness": "claude", "last_line": "cruise: continue",
                "fingerprint": f"{n:016x}"}) + "\n" for n in range(1, 51)), encoding="utf-8")
            for verb, output in said.items():
                done = cruise(repo, *verb.split())
                self.assertEqual((done.returncode, done.stdout), (0, output), verb)

    def test_hold_the_stuck_window_is_what_it_was_when_the_log_is_cut_short_during_a_park(self) -> None:
        """AC-S02-33 (hold): two idle iterations park the run (`stuck_after` 2); while it waits the log is emptied
        and a message resumes it. The window lives in the process, so the very next idle iteration parks again."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "window", "standard", "python")
            enable(repo, stuck_after="2", unblock="park")
            env = fake_harness(Path(directory), """if [ "$n" -ge 3 ]; then touch .specify/cruise.stop; fi
echo "cruise: continue\"""")
            runner = subprocess.Popen(["python3", "scripts/agents/cruise.py", "run"], cwd=repo, text=True,
                                      stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                      env=outside_a_run(env))
            lines: list[str] = []
            reader = threading.Thread(target=lambda: lines.extend(runner.stdout or []), daemon=True)
            reader.start()
            try:
                deadline = time.monotonic() + 60
                while not any("cruise: waiting" in line for line in lines) and time.monotonic() < deadline:
                    time.sleep(0.05)
                (repo / LOG).write_text("")
                cruise(repo, "tell", "go on")
                runner.wait(timeout=60)
            finally:
                if runner.poll() is None:
                    runner.terminate()
                    runner.wait()
            reader.join(timeout=5)
        text = "".join(lines)
        self.assertEqual(text.count("cruise: parked — no progress since iteration"), 2, text)
        self.assertIn("cruise: parked — no progress since iteration 1", text)
        self.assertIn("cruise: a person's message; resuming", text)
