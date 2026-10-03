"""An iteration's `index_use` is read from the byte its marker was written at (S02, R11; AC-S02-30, -31; D58).

The runner writes `# iteration <n> <time>` into the raw stream before the harness starts, and holds the byte it wrote
it at and the line itself. The entry's `index_use` is read from that byte on when the bytes there are that line and the
path is still the file the runner wrote through; otherwise the whole stream is read, as it always was. The count of
bytes read goes in the entry as `bookkeeping.stream_bytes` — a count, never a timing — and is what these tests read.
"""
from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path
from types import ModuleType

from support import FactoryTestCase
from test_cruise_index import DONE, MCP_CALL, bare_path, index
from test_cruise_runner import cruise, enable, fake_harness, logged
from test_runner_log import seed

from slipwai.project.cruise_record import RUNNER_STREAM

OTHER_CALL = MCP_CALL.replace("post_entry", "something_else")


def section(number: int, *calls: str) -> str:
    return "".join([f"# iteration {number} 2026-10-03T10:00:00Z\n", *(call + "\n" for call in calls),
                    DONE.replace("{last}", "continue") + "\n"])


def history(count: int) -> str:
    """A stream already holding `count` iterations, each of which asked the index once."""
    return "".join(section(n, MCP_CALL) for n in range(1, count + 1))


def code_index_of(repo: Path) -> ModuleType:
    sys.dont_write_bytecode = True  # no __pycache__/ beside the toolkit's scripts (AC-S02-45)
    sys.path.insert(0, str(repo / "scripts/agents"))
    try:
        specification = importlib.util.spec_from_file_location("code_index_read", repo / "scripts/agents/code_index.py")
        assert specification is not None and specification.loader is not None
        module = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(module)
    finally:
        sys.path.remove(str(repo / "scripts/agents"))
    return module


class RunnerStreamTest(FactoryTestCase):
    def run_51st(self, name: str, stream: str, behaviour: str,
                 extra: dict[str, str] | None = None) -> tuple[Path, dict]:
        """Iteration 51 of a run whose log holds 50 entries and whose stream holds `stream`; returns the repo and
        the entry the runner wrote. The harness does `behaviour` after it prints its own line."""
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        here = Path(directory.name)
        repo = self.generate(directory.name, name, "standard", "python")
        enable(repo, max_iterations="1")
        index(repo)
        seed(repo, 50)
        (repo / RUNNER_STREAM).parent.mkdir(parents=True, exist_ok=True)
        (repo / RUNNER_STREAM).write_text(stream, encoding="utf-8")
        for path, text in (extra or {}).items():
            (here / path).write_text(text, encoding="utf-8")
        env = {**fake_harness(here, behaviour), "CRUISE_HARNESS_STREAM": "claude",
               "PATH": str(bare_path(here, "cat", "mkdir", "touch", "rm", "mv", "dirname"))}
        ended = cruise(repo, "run", "--no-park", env=env)
        self.assertEqual(ended.returncode, 0, ended.stdout + ended.stderr)
        entry = logged(repo)[-1]
        self.assertEqual(entry["iteration"], 51)
        return repo, entry

    def test_e30_a_stream_of_fifty_iterations_is_read_from_this_iterations_marker(self) -> None:
        """AC-S02-30: `index_use` is what the whole read gives; `stream_bytes` is the section, not the history."""
        calls = [OTHER_CALL, OTHER_CALL]
        lines = "".join(call + "\n" for call in calls)
        before = history(50)
        repo, entry = self.run_51st("stream-fifty", before, "cat $(dirname $0)/mine.jsonl",
                                    {"mine.jsonl": lines + DONE.replace("{last}", "continue") + "\n"})
        raw = (repo / RUNNER_STREAM).read_bytes()
        section_bytes = len(raw) - raw.index(b"# iteration 51 ")
        whole = code_index_of(repo).delegate_use(repo / RUNNER_STREAM, 51)[51]
        self.assertEqual(entry["index_use"], whole)
        self.assertEqual(sum(agent["queries"] for agent in entry["index_use"]), 2)
        stream_bytes = entry["bookkeeping"]["stream_bytes"]
        self.assertGreater(stream_bytes, 0)
        self.assertLessEqual(stream_bytes, section_bytes)
        self.assertLess(section_bytes, len(before.encode("utf-8")) // 10)

    def test_e30_the_bytes_read_do_not_depend_on_how_long_the_history_was(self) -> None:
        """SC-006 held as a count: the same iteration over 5 and over 50 iterations of history reads the same."""
        mine = {"mine.jsonl": OTHER_CALL + "\n" + DONE.replace("{last}", "continue") + "\n"}
        counts = [self.run_51st(f"history-{n}", history(n), "cat $(dirname $0)/mine.jsonl", mine)[1]
                  for n in (5, 50)]
        self.assertEqual(counts[0]["bookkeeping"]["stream_bytes"], counts[1]["bookkeeping"]["stream_bytes"])

    def test_e31_a_stream_cut_short_to_a_marker_elsewhere_is_read_whole(self) -> None:
        """AC-S02-31: the harness truncates the stream and writes a marker of its own at byte 0 — not where the
        runner wrote its marker. `index_use` is the whole read's, `stream_bytes` the size of what was read."""
        cut = "printf '%s\\n' \"# iteration 51 2026-10-03T11:00:00Z\" > .specify/cruise-stream.jsonl"
        repo, entry = self.run_51st("stream-cut", history(50), f"{cut}\ncat $(dirname $0)/mine.jsonl",
                                    {"mine.jsonl": OTHER_CALL + "\n" + DONE.replace("{last}", "continue") + "\n"})
        stream = repo / RUNNER_STREAM
        self.assertTrue(stream.read_bytes().startswith(b"# iteration 51 2026-10-03T11:00:00Z\n"))
        self.assertEqual(entry["index_use"], code_index_of(repo).delegate_use(stream, 51)[51])
        self.assertEqual(entry["bookkeeping"]["stream_bytes"], stream.stat().st_size)

    def test_e31_a_stream_replaced_during_the_iteration_is_read_whole(self) -> None:
        """AC-S02-31: another file moved into the path, with a marker for this iteration at another byte."""
        replacement = "# padding\n" * 7 + section(51, OTHER_CALL, OTHER_CALL, OTHER_CALL)
        move = "mv $(dirname $0)/new.jsonl .specify/cruise-stream.jsonl"
        repo, entry = self.run_51st("stream-replaced", history(50), move, {"new.jsonl": replacement})
        stream = repo / RUNNER_STREAM
        self.assertEqual(stream.read_text(encoding="utf-8"), replacement)
        self.assertEqual(sum(agent["queries"] for agent in entry["index_use"]), 3)
        self.assertEqual(entry["index_use"], code_index_of(repo).delegate_use(stream, 51)[51])
        self.assertEqual(entry["bookkeeping"]["stream_bytes"], len(replacement.encode("utf-8")))

    def test_e31_a_deleted_stream_gives_no_index_use(self) -> None:
        """AC-S02-31: nothing to read, nothing read."""
        repo, entry = self.run_51st("stream-gone", history(50), "rm .specify/cruise-stream.jsonl")
        self.assertFalse((repo / RUNNER_STREAM).exists())
        self.assertNotIn("index_use", entry)
        self.assertEqual(entry["bookkeeping"]["stream_bytes"], 0)

    def test_a_run_with_no_stream_kept_carries_no_stream_bytes(self) -> None:
        """Where the harness keeps no stream the field is absent, as the data model says."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "no-stream", "standard", "python")
            enable(repo, harness="gemini", max_iterations="1")  # a harness whose headless row names no stream
            ended = cruise(repo, "run", "--no-park", env=fake_harness(Path(directory), "echo 'cruise: continue'"))
            self.assertEqual(ended.returncode, 0, ended.stdout + ended.stderr)
            self.assertEqual(set(logged(repo)[-1]["bookkeeping"]), {"log_bytes"})
