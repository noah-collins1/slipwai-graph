# Research: S02-runner-bookkeeping

Each statement cites what it was read from; one with no citation reads *assumed*.

1. **How a toolkit script reaches a project, and what lists it.** *Assumed, to verify before the first cycle of
   story 1:* the generator copies `assets/toolkit/scripts/agents/` whole and records each file in the project's
   `.written`; a test may enumerate the toolkit's files. The delegate reads `src/slipwai/` for where `code_index.py`
   is named beside `cruise.py` and follows that precedent for `bookkeeping.py`; if a new file cannot ride that
   precedent, the record goes into `cruise.py` itself and the plan's structure is amended, not the generator.
2. **The runner imports a sibling.** `cruise.py` already imports `code_index` from its own directory (the call
   `code_index.health()` in `drive()`, `assets/toolkit/scripts/agents/cruise.py`), so a second sibling import is
   the existing shape.
3. **What moves a file's change time.** A same-size rewrite in place with the modification time restored moved
   the change time and kept the inode; a replace by rename moved both (D56's probe under `/tmp/d56`, Linux, tmpfs,
   Python 3.14). An unprivileged process cannot set a change time (D56, same probe). Windows: Python's
   `st_ctime_ns` is the creation time and `st_ino` may be 0 — *assumed* from D56's statement, not run; R1 hashes
   everything there, R2 uses what is reported.
4. **The log has one writer.** `record()` is the only appender of `specs/cruise-log.jsonl`; the callers of
   `entries()` are at lines 813, 1088, 1197, 1227, 1228, 1620 and 1669 of `cruise.py` and only those in `drive()`
   are per-iteration (D58, read; confirmed by the host's `grep -n 'entries()'`).
5. **The gate's memory functions.** `remembered()`, `candidates_of()`, `unvouched()`, `read_once()`, `narrowed()`,
   `remember()` and `whole()` in `assets/toolkit/scripts/check-codegraph.py` (lines 299–533); `drift(only, rows)`
   already takes a narrowed set (line 182). The memory's key carries the hash of `agents/code_index.py`
   (S01's [data-model](../S01-gate-walks/data-model.md)), so this slice's own edit makes the first comparison whole.
6. **An older checker ignores an unknown label.** `entries()` in `check-decisions.py` keeps every `- **Label:**`
   line and `check_decisions()` reads only `DECISION_FIELDS` (lines 76–137, read by the host); e63 runs it.
7. **The id shape.** `done_slices()` in `check-decisions.py` (line 174) reads a slice id; D17 and D19 fix how a
   bare prefix meets a slugged id.

**Decisions**: none open. D56–D60 answer every question the gaps review raised.
