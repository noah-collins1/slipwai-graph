# Tasks: S02-runner-bookkeeping — cruising at iteration 50 costs what iteration 1 did

**Input**: [plan.md](plan.md) (*The example map* R1–R12 is what the tasks cut on; *Technical Context*; *Project
Structure*), [research.md](research.md), [data-model.md](data-model.md), [quickstart.md](quickstart.md); acceptance
criteria AC-S02-1 … AC-S02-69 in `specs/001-faster-slipwai/spec.md` under `### S02-runner-bookkeeping` (example e*n*
is criterion AC-S02-*n*); decisions D7, D9, D12, D39, D46, D49, D50, D56, D57, D58, D59, D60 in
`specs/001-faster-slipwai/decisions.md`. No `examples.md`: a method slice with no screen and no event model.

**Branch**: `adopt-method` (D12). No `slice/` branch, no push, no claim. One commit per task.

**Delegation**: one delegate per implementation task, each its own RED-GREEN-REFACTOR increment and its own commit.
The "Files" line of a task is its manifest: the only files that delegate may write. Nobody but the host writes
`tasks.md`.

**User stories** (from the plan's example map): **US1** what the runner remembers, `agents/cruise.py` and the new
`agents/bookkeeping.py` (R1–R3); **US2** the index before an iteration, `agents/code_index.py` and
`check-codegraph.py` (R4–R7); **US3** the `Scope:` line in `check-decisions.py` (R8, R9); **US4** the writers under
`src/slipwai/project/` (R10); **US5** the stream and the release (R11, R12).

## Constraints

Constraints that hold for every task, stated once:

- **Not edited, ever, by any task here:** anything under this repository's `delivery/`, `tools/`, the `Makefile`,
  `.github/`, or hook settings (D9); nothing under `release/`; no file `delivery/.written` lists.
- **Encoding.** Every `open` and `read_text` in a toolkit script names `encoding="utf-8"`.
- **Tests.** Fakes written in the test tree (the harness `tests/test_cruise_runner.py` drives through
  `CRUISE_HARNESS_COMMAND`; `indexed()` and its fake `codegraph` CLI in `tests/test_code_index_health.py`) and the
  audit-hook wrapper `tests/gate_audit.py` (S01's) for what a call opened. Never a mocking framework. Never a
  wall-clock assertion: SC-006 is held as counts (bytes read, files opened), not times (AC-S02-21, D58). A test that
  loads a toolkit script as a module sets `sys.dont_write_bytecode` first (as `tests/test_cruise_guard.py` does), so
  no `__pycache__/` appears beside the scripts (AC-S02-45). Where a platform cannot make a link or set a time, the
  example skips, saying why.
- **Size.** Every file under `src/` and `tests/` stays within 350 lines (`make check-structure`).
  `src/slipwai/project/cruise.py` is at 331 and `tests/test_cruise.py` at 350: new text goes through
  `cruise_record.py` and `cruise_agents.py`, new tests in new files. A task whose examples will not fit one test file
  names a second.
- **Commits are by path.** `git add <exact path>` for the files in the task's manifest, never `git add -A`: the branch
  is one and other stories' half-done files may be in the tree. `make lint typecheck check-structure` before each commit.
- **Shared helper.** `tests/gate_audit.py` is S01's and is edited by no task here; a delegate who finds it wanting
  stops and reports.
- **RED is seen** for its stated reason before the production file is touched. A **hold** (the plan says which) is
  written as a hold, saying so in the test's name or comment, and is observed passing; it is not a RED. A hold is shown
  to have teeth by changing the production file in the working tree, seeing the test fail, and restoring with
  `git checkout -- <exact path>`; `git status` then shows only the task's own files.
- **Versioning** (`AGENTS.md`). The first commit that adds the `Scope:` line to `DECISION_ENTRY` (T011) carries `VERSION`
  `1.6.0.dev0` and `changelog.d/runner-bookkeeping.md` in its first form, first line `MINOR`; its message names the
  level and the reason (something a project can newly be given, every existing answer meaning what it meant). T013
  completes the fragment. Every other commit that changes `assets/` or `src/` says `Level MINOR; VERSION already
  1.6.0.dev0` once T011 is in, and before it `VERSION is raised in T011's commit, the first that adds the line`; a
  commit that changes only `tests/` says it reaches no user.
- **Quickest test per task:** `make test TESTS="<modules>"`, the modules each task names.

## Format: `[ID] [P?] [Story] Description` — each task is one increment, one commit

`[P]` marks a task whose files are disjoint from every task of *another* story that may run at the same time; it says
nothing about tasks inside one story, which share files and run in order. See *Parallel opportunities*.

---

## Phase 1: Setup

### T001 — Verify how a new toolkit file reaches a project (research item 1; gates T002 only)

- [x] **Read, no commit, no rule.** `research.md` item 1 was *assumed*. Read against `src/slipwai/toolkit.py`,
  `src/slipwai/assets.py` and `src/slipwai/scaffold.py` on 2026-10-03:
  **Answer.** `toolkit_files_from_assets` walks `asset_files(TOOLKIT_ROOT)` whole, and `toolkit_treatment(path, …)`
  answers `copied` for any path that is not a skill excluded by capability or a profile-excluded event-model document;
  `scripts/agents/` is neither, so a new `assets/toolkit/scripts/agents/bookkeeping.py` is copied beside `cruise.py`
  and `code_index.py` with no list to extend and no edit under `src/slipwai/`. `.written` is the set of files the
  generator wrote, so the file is in it by construction. `src/slipwai/project/agent_settings.py` and `rules.py` name
  `agents/code_index.py` for reasons of their own (the index's wiring), not as a registry of the directory. The
  toolkit's self-containment test reads every file under `assets/toolkit/` as text, which is why a test that loads a
  script sets `sys.dont_write_bytecode`. So the plan's structure stands: `bookkeeping.py` is a new sibling file, and
  `cruise.py` imports it as it imports `code_index` (research item 2).
  **What the T002 delegate does first:** confirm in one command that a generated project holds the file once the
  module exists (`./slipwai generate` into a scratch directory, `ls scripts/agents/`); if it does not, stop and report
  — the fallback in research item 1 (the record goes into `cruise.py`, the plan amended) is the host's to choose.

**Files:** none.

---

## Phase 2: User Story 1 — what the runner remembers [US1]

`agents/cruise.py` and the new `agents/bookkeeping.py`. T002, T003 and T004 all edit both: they run in order. Needs T001.
Disjoint from every task of US2, US3 and US4. T002 and T003 share the record class (path → hash beside its stat), T004
the log's record; the three write to separate test modules.

### T002 — [P] [US1] A control's content is read once while its size, times and identity stand (R1 · AC-S02-1 … -11)

- [x] *(6ef64b6)* **Rule R1.** New `assets/toolkit/scripts/agents/bookkeeping.py` holding the stat-vouched hash record (all four
  facts — size, modification time, change time, identity — or the file is hashed every time; two seconds' margin; the
  record is the process's, never written); `controls_signature()` in `cruise.py` asks it. The comparison is still
  content (D56). Test modules `tests/test_runner_controls.py` (new; the reads and the two-second and no-change-time
  cases) and `tests/test_runner_controls_park.py` (new; the park and the holds).

**RED** (each seen failing for its stated reason before the scripts are touched; observed under the audit hook, as counts):
- e1 a run whose controls no one touches, the second and every later `controls_signature()` of the process → no control
  opened for content and the value equals the first. Fails today: every control is opened on every call.
- e5 an iteration that only touches a gate, or rewrites it with the same bytes → no park for it, and that file's content
  is read once and not again while it stays unchanged. Fails today: read every time (the no-park half is a hold).
- e9 a control modified within two seconds of the moment it was hashed → read again at the next signature. Fails today
  only in that nothing yet distinguishes the window; seen failing against the record before the window is coded
  (write the test against the record with the window absent, then add it).
- e10 a platform reporting no change time or no file identity (the record handed a stat result without them) → every
  control read at every signature. Fails today? Today every control is read anyway, so the *refusal to reuse* is
  seen failing only once the record exists: the test first hands the record a full stat result (reuse allowed, written
  and observed once the record is coded), then one without (read) — it is written with the record, the reuse half RED.
- e11 a new runner process over a tree whose controls changed while none was alive → every control hashed on its first
  iteration, nothing from an earlier process consulted. Fails today only for the *consulted* half; the record is
  process-local (nothing on disk), observed by two child processes.

**Holds** (green today, written as holds, observed passing, teeth shown):
- e2 an iteration appends a line to a gate script → the run parks naming `<path> (modified)` with `controls_changed` on
  the log entry. e3 rewritten in place at the same size, modification time restored → parks `(modified)`. e4 replaced
  by rename with a same-size file carrying the old modification time → parks `(modified)`. These guard the record from
  becoming a time-based signature; teeth: make the record reuse on size and modification time alone.
- e7 an iteration deletes a control and adds a script beside the gates → `(deleted)` and `(added)`; a file added under
  `tools/` is not a change. e8 a control unreadable after an iteration and read before → `(deleted)`, no hash reused
  for it.
- e6 a run parked between iterations, a person edits a control, the run resumes → the next entry carries no
  `controls_changed` for that file, and a later iteration changing it still parks naming it.

**GREEN** — `bookkeeping.py`: the record class and the two-second rule; `controls_signature()` reads a file's stat
fresh for every before and after (never a cached stat), reuses a recorded hash only where all four facts read as
recorded and the file's times are two seconds older than the hashing, and otherwise hashes and records. `cruise.py`
imports the sibling the way it imports `code_index`. The signature's value for any tree is unchanged.

**REFACTOR:** one record class, no second copy; T003 uses it for `specs/` and must need only a different set of facts.

**Verify:** `make test TESTS="test_runner_controls test_runner_controls_park test_cruise_guard test_cruise_runner"`, then
`make lint typecheck check-structure`. Commit (level line as in *Constraints*).

**Files:** `assets/toolkit/scripts/agents/bookkeeping.py` (new), `assets/toolkit/scripts/agents/cruise.py`,
`tests/test_runner_controls.py` (new), `tests/test_runner_controls_park.py` (new).

### T003 — [P] [US1] The fingerprint is path and content, each file read once while its record stands (R2 · AC-S02-12 … -21)

- [x] *(043239e, 05aef6d)* **Rule R2.** `fingerprint()` in `cruise.py` digests path and per-file SHA-256 of every file under `specs/` but the
  log and the checkpoint, through the T002 record with as many facts as the platform reports (D57); the value changes
  once, the field keeps its name and 16 hex characters. Needs T002 (the record). Test module
  `tests/test_runner_fingerprint.py` (new).

**RED:**
- e12 a `specs/` tree last written more than the granularity window ago, fingerprinted once in the process → a second
  `fingerprint()` opens no file under `specs/` and returns the same value. Fails today: every file is opened again.
- e13 the first call → each file under `specs/` but the log and the checkpoint opened exactly once. Fails today: counted
  against the new digest's one read per file (today's reads are of the same files, so seen failing against the second
  call, e12; e13 is seen failing on the log and checkpoint exclusion only if today reads them — assert both halves).
- e14 one file touched or rewritten with the same bytes → the next call opens that file alone and returns the same
  value, the call after opens none. Fails today: all files each call.
- e17 a file written within the granularity window of its read, nothing changed → read again, same value. Fails today
  only as the *record-absent* path; seen failing as the window is coded.
- e21 files opened on call 50 equal those opened on call 2 (a count, no timing). Fails today: every call opens every
  file, so the two equal each other *and* the first; the test asserts the count on call 50 is zero for an unchanged tree.
- e15 a file rewritten in place with different bytes of the same size → a different value; and with its modification
  time restored, on a platform that reports a change time (skip, saying why, where it does not). Fails today only on
  the restored-time half if today's value ignores content; observed, and written as a hold if it already differs.
- e16 a file added, removed, or renamed with bytes unchanged → a different value, and a removed file's record is no
  longer held (asserted on the record's size).
- e20 a log carrying fingerprints written by the earlier code → read without error; the run parks as stuck only after
  `stuck_after` values of its own are equal. Fails today? Observed; a hold where it passes.

**Holds:**
- e18 two runner processes, same tree, commit and status → equal fingerprints (`tests/test_cruise_runner.py`'s *no
  progress since iteration 2* stays green, run with no edit). e19 a new commit, or a change outside `specs/` altering
  `git status`, with `specs/` unchanged → the value differs and no file under `specs/` is opened.

**GREEN** — `fingerprint()` hashes each file's bytes once per record, includes path and hash in the digest, keeps commit
and status exactly as they are, drops a removed file's record; reuse under the same two-second margin as T002.

**REFACTOR:** no second walk; the digest takes the record's answer, nothing more.

**Verify:** `make test TESTS="test_runner_fingerprint test_runner_controls test_cruise_runner test_cruise_guard"`, then
`make lint typecheck check-structure`. Commit.

**Files:** `assets/toolkit/scripts/agents/bookkeeping.py`, `assets/toolkit/scripts/agents/cruise.py`,
`tests/test_runner_fingerprint.py` (new).

### T004 — [P] [US1] The log is read whole once per process, and again only when it is not what the runner left (R3 · AC-S02-22 … -29, -32, -33)

- [x] *(a151f5c)* **Rule R3.** `entries()`/`record()` in `cruise.py` and the loop in `drive()`; the log as left (entry count; the
  file's size, times and identity after the runner's own append) held in the process and checked again before the
  append; `bookkeeping.log_bytes` on each entry; the iteration number stays the count of entries plus one (D58). Needs
  T003 (same files). Test modules `tests/test_runner_log.py` (new; the counts) and `tests/test_runner_log_stale.py`
  (new; the changed-log cases and holds).

**RED:**
- e22 a log of 50 entries, a fake harness, one runner process, two iterations → entries numbered 51 and 52; entry 51's
  `bookkeeping.log_bytes` is the seeded log's size counted once, entry 52's is 0. Fails today: no `bookkeeping` object.
- e23 the same over a log of 1 entry → the second entry's `log_bytes` is 0, as over 50 entries. Fails today: same.
- e24 an iteration cut the log to its first 3 entries → the entry is appended as today; the next iteration is numbered
  from the entries then in the file; that next entry's `log_bytes` is the size of the file re-read. Fails today: no
  `log_bytes` (the numbering half is a hold).
- e25 a log deleted during an iteration → recreated holding that one entry, the next iteration numbered 2. Fails today
  for `log_bytes` only; the numbering is a hold.
- e26 replaced by a new file with the same bytes → the number is what it would have been and `log_bytes` is the whole
  file's size. e27 one entry edited in place to the same length → read whole (`log_bytes` is its size), number the
  count plus one. e28 another hand appended one entry → its number counts it, `log_bytes` the whole size. Each fails
  today for the missing field; each asserts the *whole read* by its value, not a timing.

**Holds:**
- e29 a log whose last line is not a whole entry, at start or at the next read after a change → the run ends as today,
  nothing appended. e32 a log of 50 entries → `status`, `where`, `tell`, `resume` each print what they printed (output
  captured from the `HEAD` script into a fixture before the change, or the existing assertions run with no edit). e33
  a run whose fingerprint has not moved for `stuck_after` iterations, the log cut short during a park → the stuck
  window is what it was.

**GREEN** — `bookkeeping.py` gains the log record: forgotten on any difference between the file's present facts and the
recorded ones, the whole log then read once and re-recorded after the append; `drive()` asks it per iteration; callers
of `entries()` outside the per-iteration path (`status`, `where`, `tell`, `resume`) are unchanged. `log_bytes` is
written on the entry the runner appends; an unparseable line ends the run as it does today.

**REFACTOR:** one place that answers "what is in the log now", so the append and the next read share it.

**Verify:** `make test TESTS="test_runner_log test_runner_log_stale test_runner_controls test_runner_fingerprint test_cruise_runner test_cruise_guard"`, then `make lint typecheck check-structure`. Commit.

**Files:** `assets/toolkit/scripts/agents/bookkeeping.py`, `assets/toolkit/scripts/agents/cruise.py`,
`tests/test_runner_log.py` (new), `tests/test_runner_log_stale.py` (new).

---

## Phase 3: User Story 2 — the index before an iteration [US2]

`agents/code_index.py` and `check-codegraph.py`. T005 → T006 → T007 → T008, in order (the same two scripts, and
T005–T006, T007–T008 each share a test file). Needs T001 for nothing; disjoint from every US1, US3 and US4 task. In every
example the indexed project is `indexed()` from `tests/test_code_index_health.py`; *a whole comparison* is one run of
the gate or of `health()` that compared everything.

### T005 — [P] [US2] The gate, the sync count and the tree are today's (R7 · AC-S02-43, -44, -45) — pinned first

- [x] *(33facda)* **Rule R7 — every example is a hold: green today, written as holds, saying so, observed passing.** Numbered
  after R4–R6 in the plan, scheduled first here: it pins what the narrowing must not break, and so is committed before
  any production change in this story (as S01's T008 was). Test module `tests/test_health_narrowed.py` (new; R4's
  examples join it at T006).

**Tests (all holds):**
- e43 the fake `codegraph` CLI counting its `sync` calls: for each state of the index (current, behind, missing,
  corrupt, unreachable) readying one iteration invokes `sync` at most once, before the iteration, only where files are
  found behind; `current` means none; built or rebuilt means `init` and no `sync`.
- e44 `tests/test_codegraph_*.py` and `tests/test_code_index*.py` pass with no edit (run, and `git diff` shows none of
  them touched); the trunk, a non-`slice/<id>` branch, a detached `HEAD` and each CI marker print today's
  `make check-codegraph` bytes and exit code, a corrupt database it has `health()` rebuild included (a captured
  fixture of today's output).
- e45 after any `health()` run `git status --porcelain` is empty and no `__pycache__/` sits beside the toolkit's scripts.

**GREEN:** none. **Teeth:** in the working tree make `health()` call `sync` twice; see e43 fail; restore with
`git checkout -- assets/toolkit/scripts/agents/code_index.py`.

**Verify:** `make test TESTS="test_health_narrowed test_codegraph_narrowed test_codegraph_memory test_code_index_health test_code_index_open test_code_index test_cruise_index"`, then `make lint typecheck check-structure`. Commit (tests only: reaches no user).

**Files:** `tests/test_health_narrowed.py` (new).

### T006 — [P] [US2] `health()` hashes what changed since the last whole comparison, on any branch outside CI (R4 · AC-S02-34, -35, -41, -42)

- [x] *(6eba6d0 (e41's second half — the next run hashes 0 — landed with T008, where health() writes the memory))* **Rule R4.** `health()` in `code_index.py` compares through the gate's own candidates and memory
  (`remembered()`, `candidates_of()`, `unvouched()`, `read_once()`, `narrowed()` in `check-codegraph.py`, research item
  5; `drift(only, rows)` already takes a narrowed set); only what those need made callable is changed in the gate
  script, and `main()` and `narrowable()` are not edited. `detail` says in one line how many files of how many were
  hashed, that only what changed was compared, and since when. Needs T005. Test file `tests/test_health_narrowed.py`.

**RED** (each fails today because `health()` hashes every tracked file and `detail` says nothing of the count):
- e34 index current, usable memory, nothing changed → on `main`, `slice/S1`, `feature/x` and a detached `HEAD`:
  `current`, 0 files hashed, `detail` carries `hashed 0 of N`, the narrowed clause and the moment.
- e35 one tracked indexed file changed that the index has not read → exactly that file hashed, one `sync`, compared
  again, `synced`; where the sync does not take it, `failed` as today.
- e41 a `touch`, checkout or rebase moving a file's times without a byte → the first `health()` hashes it once and
  reports `current`, the second hashes 0.
- e42 an unchanged tree across iterations → readying iteration 50 hashes as many files as readying iteration 2 (zero)
  and, under the audit hook, opens no tracked file for content.

**GREEN** — `health()` reads the memory, computes the candidates, hashes only those, and names the count in `detail`;
`check-codegraph.py` gets only the small edits that make the memory's functions callable from `code_index.py` (the
module is already loaded there for `drift()`); no memory write yet (T008).

**REFACTOR:** one call path for "what to hash", shared by the gate's narrowed run and `health()`.

**Verify:** `make test TESTS="test_health_narrowed test_codegraph_narrowed test_codegraph_memory test_codegraph_bytes test_code_index_health test_code_index_open test_cruise_index"`, then `make lint typecheck check-structure`. Commit.

**Files:** `assets/toolkit/scripts/agents/code_index.py`, `assets/toolkit/scripts/check-codegraph.py`,
`tests/test_health_narrowed.py`.

### T007 — [P] [US2] What the memory cannot vouch for is the whole comparison, said in one clause (R5 · AC-S02-36, -37, -39)

- [x] *(5622e7d (e36 holds sixteen states; AC-S01-24's is added by T012's delegate))* **Rule R5.** Every drift state of S01 answers as `health()` without a memory does; each reason the memory cannot
  be used is one clause in `detail`; a rebuilt database is compared whole. Needs T006. Test modules
  `tests/test_health_memory.py` (new; e37, e39) and `tests/test_health_memory_states.py` (new; the per-state table of e36).

**RED:**
- e36 one example per state — AC-S01-13, -14, -15, -16, -17, -18, -23, -24 and the no-row state of -21 — each: its
  state under a narrowed `health()` equals the state with the memory deleted, on the same tree and index. Fails today
  for any state where T006's narrowed path answers differently; observed state by state, and a state that already
  agrees is written as a hold with the reason.
- e37 a memory `health()` cannot use, one example per reason (none, unreadable, commit gone, scripts changed, another
  database identity, git unable to say what changed) → every tracked file hashed, today's state, `detail` carries one
  clause naming the reason. Fails today: no clause.
- e39 a corrupt database with a usable memory present → moved aside, rebuilt as today, then every tracked file hashed.

**GREEN** — the reasons returned by the gate's own function become `detail`'s one clause; any unusable-memory route and
any rebuilt database run the whole comparison; no new judgement of a file's state is written here.

**REFACTOR:** the clause wording lives in the gate script's table, not copied.

**Verify:** `make test TESTS="test_health_memory test_health_memory_states test_health_narrowed test_codegraph_memory test_code_index_health"`, then `make lint typecheck check-structure`. Commit.

**Files:** `assets/toolkit/scripts/agents/code_index.py`, `assets/toolkit/scripts/check-codegraph.py`,
`tests/test_health_memory.py` (new), `tests/test_health_memory_states.py` (new).

### T008 — [P] [US2] The memory is written by a `health()` that ends current, and never in CI (R6 · AC-S02-38, -40)

- [x] *(822e47f)* **Rule R6.** Through the gate's writer (`remember()`, D59); `failed`, `unreachable`, unopened → as it was. Needs
  T007 (same test file and scripts). Test file `tests/test_health_memory.py`.

**RED:**
- e38 each CI marker (`CI`, `GITHUB_ACTIONS`, `GITLAB_CI`) set → `health()` compares everything and `gate-memory.json`'s
  bytes and times are unchanged afterwards. Fails today only if T006's path reads a memory under CI; observed, a hold
  where it already compares everything and writes nothing.
- e40 `health()` ending `current`, or `synced` with the second comparison clean → the memory holds what a passing gate
  run on the same tree writes (byte-compared with a gate run's). Fails today: `health()` writes nothing. Ending
  `failed`, `unreachable`, the database not openable, or no answer from the comparison → memory bytes as before.

**GREEN** — `health()` calls the gate's writer at the two ending states, outside CI only, and in no other.

**REFACTOR:** none expected.

**Verify:** `make test TESTS="test_health_memory test_health_memory_states test_health_narrowed test_codegraph_narrowed test_codegraph_memory test_codegraph_races test_code_index_health test_code_index_open test_code_index test_cruise_index"`, then `make lint typecheck check-structure`. Commit.

**Files:** `assets/toolkit/scripts/agents/code_index.py`, `tests/test_health_memory.py`.

---

## Phase 4: User Story 3 — the `Scope:` line in the checker [US3]

`check-decisions.py` only. T009 → T010 (the same script). Disjoint from US1, US2, US4.

### T009 — [P] [US3] `--scope <id>` prints the standing entries in scope, global, or without a line (R8 · AC-S02-47 … -56)

- [x] *(13b6b03)* **Rule R8.** A verb of the script that already parses entries: `--scope <id>` and `--feature`; verbatim, number
  order, a closing line of counts; never drops what it cannot place; writes nothing (D60). Test modules
  `tests/test_decisions_scope.py` (new; e47–e54) and `tests/test_decisions_scope_edges.py` (new; e55, e56).

**RED** (each fails today: the option does not exist, exit 2):
- e47 100 standing entries, 4 naming `S02-runner-bookkeeping`, 10 `Scope: global`, 86 others → exactly those 14, verbatim,
  in number order, exit 0. e48 `S02-runner-bookkeeping, S14-result-contract` → printed for either id, not for
  `S11-render-once`. e49 `Scope: S02` printed for `S02-runner-bookkeeping`; with `S1` neither it nor `S12-model-sidecar`.
- e50 an entry with no `Scope:` printed for any slice, counted as carried for want of a line. e51 empty or unreadable
  value → printed as global. e52 `Status` `overridden by D<m>` or `overridden by human <date>` → not printed, the
  closing line names it by number with what overrode it. e53 the last line says how many entries carried of how many,
  split in scope, global, carried for want of a line, and left out as out of scope. e54 a slice id no entry names →
  the global and unscoped standing entries, exit 0.
- e55 two features' `decisions.md` and no `--feature` → non-zero, one line naming the features to choose from; one
  feature → `--feature` not needed. e56 any run → no file in the tree created or changed (tree digest before and after).

**GREEN** — the option, the id matching D17/D19 describe (a bare prefix meets a slugged id; `S1` does not meet
`S12-…`), the output as above. `check_decisions()`'s verdict is not touched (T010).

**REFACTOR:** the entry parser is the one in the script; the filter reads its output.

**Verify:** `make test TESTS="test_decisions_scope test_decisions_scope_edges test_cruise_record"`, then `make lint typecheck check-structure`. Commit.

**Files:** `assets/toolkit/scripts/check-decisions.py`, `tests/test_decisions_scope.py` (new),
`tests/test_decisions_scope_edges.py` (new).

### T010 — [P] [US3] The gate accepts absence and refuses a malformed line (R9 · AC-S02-57 … -63)

- [x] *(1716e4c, bf660de — the gate code landed in 13b6b03 with T009, so e59, e60 and e62 were seen red by disabling it afterwards, not before it existed)* **Rule R9.** `check_decisions()` validates the `Scope:` value when present; absence is never a failure; one
  `note:` where an entry lacks it after one that has it. Needs T009 (same script). Test file
  `tests/test_decisions_scope_gate.py` (new).

**RED:**
- e59 `- **Scope:**` with no value → exit 1, one line naming the entry and saying the value is `global` or slice ids.
  e60 `Scope: global, S02-runner-bookkeeping` or `Scope: the runner` → exit 1, the same kind of line. e62 an entry with
  no `Scope:` after one that has it → exit 0 and one `note:` naming it and saying it is carried as global. Each fails
  today: the label is read by nothing, so exit 0 and no note.

**Holds:**
- e57 this repository's own D1–D60 log, copied as a fixture → exit code and output are what they were before the change
  (the output captured from `HEAD` before editing). e58 `Scope: global`, or ids bare or in backticks, after the Stage
  line → passes. e61 an id no slice in the split has → passes. e63 the checker at `HEAD` before the slice (taken with
  `git show HEAD:assets/toolkit/scripts/check-decisions.py` into a temporary file in the test) passes a log carrying
  well-formed `Scope:` lines.

**GREEN** — in `check-decisions.py`, a value is `global` alone or id-shaped tokens separated by commas; anything else
or empty fails with the entry's number; the `note:` is printed to stdout, exit unchanged.

**REFACTOR:** none expected.

**Verify:** `make test TESTS="test_decisions_scope_gate test_decisions_scope test_cruise_record"`, then `make lint typecheck check-structure`. Commit.

**Files:** `assets/toolkit/scripts/check-decisions.py`, `tests/test_decisions_scope_gate.py` (new).

---

## Phase 5: User Story 4 — the writers [US4]

### T011 — [P] [US4] The entry's shape, both briefs and the command write and read the line (R10 · AC-S02-64 … -68)

- [x] *(9b57a82 (VERSION 1.6.0.dev0 and the fragment's first form in the same commit))* **Rule R10.** `DECISION_ENTRY` in `cruise_record.py`, the skipper's and bosun's briefs in `cruise_agents.py`, the
  command's iteration-start and *Deciding* text in `src/slipwai/project/cruise.py` (331 lines: no net growth past 350);
  an owner brief already seeded is left alone. **This task's first commit that adds the line carries `VERSION` →
  `1.6.0.dev0` and `changelog.d/runner-bookkeeping.md` in its first form** (first line `MINOR`; what T011 changes for a
  project and the catch-up sentence: a seeded owner brief is unchanged and the line may be added by hand, D24). Test
  file `tests/test_cruise_scope_writers.py` (new); each example read from a generated project's files.

**RED** (each fails today: no `Scope:` anywhere in the generated text):
- e64 a generated or adopted project: the cruise command's entry shape shows `- **Scope:** <slice ids, comma-separated> |
  global` directly after the Stage line, with the rule that a feature-level or doubtful decision is `global`; a newly
  seeded owner brief says so too.
- e65 the generated `drive-skipper` brief tells the delegate to read the standing entries for the brief's slice through
  the verb (the whole log where the brief names no slice) and to return its entry with a `Scope:` line.
- e66 the generated `drive-bosun` brief says the same of reading, and that every entry it writes carries a `Scope:` line.
- e67 the cruise command's iteration-start and *Deciding* text point at the verb for a slice's question and keep *every
  standing entry* for a feature-level one.

**Hold:**
- e68 a project whose owner brief an earlier factory seeded: `slipwai migrate` leaves that file unchanged (D24).
  Teeth: make the seeding rewrite an existing brief; see the test fail; restore.

**GREEN** — the entry shape and the three texts, written through `cruise_record.py` and `cruise_agents.py` so
`src/slipwai/project/cruise.py` does not grow past 350; the existing tests that hold these sentences
(`tests/test_cruise.py`, at 350 lines; `tests/test_cruise_record.py`) are edited only if a held sentence changes, and then
with no net growth past 350. `VERSION` → `1.6.0.dev0` and the fragment's first form in the commit.

**REFACTOR:** the sentence about the verb is written once and used by the skipper's and the bosun's briefs.

**Verify:** `make test TESTS="test_cruise_scope_writers test_cruise test_cruise_record test_changelog test_add_commands"`, then `make lint typecheck check-structure`. Commit; the message names the level (MINOR) and the reason.

**Files:** `src/slipwai/project/cruise_record.py`, `src/slipwai/project/cruise_agents.py`,
`src/slipwai/project/cruise.py`, `tests/test_cruise_scope_writers.py` (new), `VERSION`,
`changelog.d/runner-bookkeeping.md` (new), and any existing test that holds a sentence changed (named in the report).

---

## Phase 6: User Story 5 — the stream, and the release [US5]

Needs US1 and US2 done: T012 edits `cruise.py` and `code_index.py`; T013 names what all five did.

### T012 — [US5] An iteration's `index_use` is read from the byte its marker was written at (R11 · AC-S02-30, -31)

- [x] *(dc7b9c2)* **Rule R11.** `delegate_use()` in `code_index.py` reads from an offset; `iterate()`/`drive()` in `cruise.py` hold the
  byte offset and the exact marker line written for the iteration (the stream's marker, data-model); the marker found
  at the offset is the check; otherwise today's whole read (D58). Needs T004 and T008. Test module
  `tests/test_runner_stream.py` (new).

**RED:**
- e30 a stream already holding 50 iterations and an index in use, iteration 51's entry written → `index_use` equals what
  `delegate_use(STREAM, 51)` returns over the whole file, and `bookkeeping.stream_bytes` is no more than the bytes from
  this iteration's marker to the end of the file. Fails today: no `stream_bytes`; the whole stream is read.
- e31 a stream replaced or cut short during the iteration so the marker is not at the recorded byte → `index_use` is
  what today's whole read gives and `stream_bytes` is the size of what was read; a deleted stream gives no `index_use`.
  Fails today: no `stream_bytes` (the value of `index_use` is a hold).

**GREEN** — the offset taken when the marker is written, checked by comparing the bytes at it to the marker line; on
any mismatch the whole read; `stream_bytes` absent where no stream is kept.

**REFACTOR:** `delegate_use()` has one reader, with the offset defaulting to zero.

**Verify:** `make test TESTS="test_runner_stream test_runner_log test_cruise_runner test_cruise_index test_code_index_health"`, then `make lint typecheck check-structure`. Commit.

**Files:** `assets/toolkit/scripts/agents/cruise.py`, `assets/toolkit/scripts/agents/code_index.py`,
`tests/test_runner_stream.py` (new).

### T013 — [US5] The release says what it is (R12 · AC-S02-46, -69)

- [x] *(918a04e — e46's RED was reconstructed against the pages at HEAD, the pages having been edited before the test; `docs/verification.md` joined the pages; AC-S01-24's row for e36 is 1b4b7b5, tests only)* **Rule R12.** Completes `changelog.d/runner-bookkeeping.md` and corrects the pages. Needs T012 and T011 (all
  stories done).

**RED** — e46: a test (in `tests/test_runner_stream.py`'s sibling is not allowed to grow; add it to
`tests/test_cruise_scope_writers.py` only if under 350 lines, else a new `tests/test_runner_pages.py`) asserts that the
docstring of `agents/code_index.py`, `scripts/extensions/codegraph/init.py`, the text in `src/slipwai/project/docs.py`
and `docs/cruise.md` each say the runner narrows its check as well as the gate. Fails today: they say only the gate
narrows.

**Hold** — e69: `VERSION` reads `1.6.0.dev0`; the fragment's first line is `MINOR`; `make test TESTS="test_changelog"` is
green; `git diff` over the slice shows no change under `delivery/`, `tools/`, `.github/`, the `Makefile` or hook settings,
and no file `delivery/.written` lists.

**GREEN** — the fragment, with: the catch-up paragraph (T011's, kept); the optional `bookkeeping` object on a log entry
(D58); the fingerprint's one-off change of value and what it cannot see (D57); what the controls' record cannot see
(D56); and AC-S02-46's three sentences — the runner's check compares only what changed since the last whole comparison,
D49's sentence on what a narrowed comparison cannot see holds for it too, deleting `.codegraph/gate-memory.json` makes
the next comparison whole. The four pages reworded.

**REFACTOR:** none.

**Verify:** `make test TESTS="test_changelog test_runner_pages test_codegraph_said"`, then `make lint typecheck check-structure`. Commit (MINOR, `VERSION` already raised by T011).

**Files:** `changelog.d/runner-bookkeeping.md`, `docs/cruise.md`, `src/slipwai/project/docs.py`,
`assets/toolkit/scripts/extensions/codegraph/init.py`, `assets/toolkit/scripts/agents/code_index.py` (docstring only),
`tests/test_runner_pages.py` (new), and any test holding those words (named in the report).

---

## Phase 7: Gates (host)

### T014 — Both full gates on the final tip (host task)

- [x] *(both green at `4dda695`, after T015–T019: `demo/gates-4dda695.txt`)* **Host task — not delegated.** Run `make verify` and `make -f delivery/Makefile verify` on the tree after T013; both
  green (Principle XIV). Confirm `VERSION` is `1.6.0.dev0` and the slice's diff touches nothing under `delivery/`, `tools/`,
  `.github/`, the `Makefile` or hook settings; no file over 350 lines. Then the demo from [quickstart.md](quickstart.md).

---

## Parallel opportunities

- **US1, US2, US3 and US4 may run concurrently** (four delegates at most). They share no file:

  | Story | Writes |
  |---|---|
  | US1 (T002–T004) | `agents/bookkeeping.py`, `agents/cruise.py`, `tests/test_runner_controls.py`, `test_runner_controls_park.py`, `test_runner_fingerprint.py`, `test_runner_log.py`, `test_runner_log_stale.py` |
  | US2 (T005–T008) | `agents/code_index.py`, `check-codegraph.py`, `tests/test_health_narrowed.py`, `test_health_memory.py`, `test_health_memory_states.py` |
  | US3 (T009–T010) | `check-decisions.py`, `tests/test_decisions_scope.py`, `test_decisions_scope_edges.py`, `test_decisions_scope_gate.py` |
  | US4 (T011) | `src/slipwai/project/cruise_record.py`, `cruise_agents.py`, `cruise.py`, `tests/test_cruise_scope_writers.py`, `VERSION`, `changelog.d/runner-bookkeeping.md` |

  Conditions: each delegate commits only the exact paths of its manifest (`git add <path>`); each runs
  `make lint typecheck check-structure` knowing another story's half-done file may be in the tree; the `[P]` is
  *against the other stories*. `VERSION` and the fragment belong to T011 (and T013 later), so no other concurrent
  delegate edits them. If that is not acceptable, give each story its own worktree.
- **Not parallel inside a story.** T002–T004 all write `bookkeeping.py` and `cruise.py`; T005–T008 all write
  `code_index.py`'s or `check-codegraph.py`'s neighbours and share `test_health_narrowed.py` (T005, T006) and
  `test_health_memory.py` (T007, T008); T009 and T010 both edit `check-decisions.py`. Two delegates would write one file.
  They run one at a time, in order.
- **T001 first** (it gates only T002, the first cycle of US1); the other stories do not wait for it.
- **US5 follows US1 and US2.** T012 edits `cruise.py` (US1's) and `code_index.py` (US2's); T013 follows T011 and T012 and
  names everything. T012 may run while US3 and US4 still run, since it touches neither's files; T013 touches
  `code_index.py`'s docstring and so waits for T012.
- **Host tasks:** T014; the host writes `tasks.md` and nothing else here.
- Most delegates at once: four.

## Design review

No screen in this slice

## Phase 4: Convergence, pass 1 (appended by `drive-converge` at `f849ef7`; the slice's code tip is `1b4b7b5`)

Grades: `CRITICAL` and `HIGH` re-open the loop; `MEDIUM` and `LOW` are what the slice may ship without. Each GREEN
names the class it closes, not the one instance.

### T015 — [HIGH] The controls' path set is as fresh as the signature: a hook file a registry row gains is held (D56 · AC-S02-2, -7)

- [x] *(7b481a6)* **Found.** `control_paths()` (`assets/toolkit/scripts/agents/cruise.py:523`–`536`) reads `registry.json` once per
  runner process and keeps the hook files in `_HOOK_FILES`. Before the slice it read the registry on every signature. D56
  says the later signature *walks the same paths* and that `controls_changed()` *answers byte for byte as today*; this is
  the one place the slice traded a control's reach for a read (constitution I, *no check is removed anywhere to make the
  loop faster*).
- **Evidence** (scratch, `/tmp/s02-converge/repro/test_repro.py`, a generated `standard`/`python` project, the runner's
  module loaded as `tests/test_runner_controls.py` loads it): a registry row is given
  `hooks.projection.where: .newharness/hooks.json` and the file is written. The comparison answers
  `["scripts/agents/registry.json (modified)"]` — the run still parks, but before the slice it also named
  `.newharness/hooks.json (added)`. After a person keeps the change and the run goes on, the next iteration rewrites
  `.newharness/hooks.json`: the comparison answers `[]`. With `_HOOK_FILES` reset, so the registry is read again, the same
  edit answers `[".newharness/hooks.json (modified)"]`. The guard held that file for the rest of the run before the slice,
  and does not now, until a new runner process.
- **RED.** An example at the probe seam and one through the runner: a registry row gains a hook file in one iteration
  (or during a park); a later iteration of the same process edits that file; the run parks naming it `(modified)`, and
  the iteration that added it is reported with `(added)` beside the registry's `(modified)`. Red today.
- **GREEN — the class:** every input that decides *which* paths a signature covers is read as freshly as the signature
  itself, with AC-S02-1 kept (no control opened for content while its record stands) — e.g. the hook files are derived
  again whenever the record's hash of `registry.json` is not the one they were derived from. No path set is fixed for
  the life of the process.

### T016 — [HIGH] A hold on a memo runs with the memo engaged: the park holds prove nothing about the record (D56 · AC-S02-2, -3, -4, -6, -8)

- [x] *(924e19b — identity alone is not shown red: a rename also moves the change time)* **Found.** Every example in `tests/test_runner_controls_park.py` generates a project and runs the runner at once,
  so each gate was written less than two seconds before it is hashed and the record (`bookkeeping.py:70`) holds nothing
  for it: every signature in those runs hashes every file. The holds pass whatever the record's rule is. The module's
  docstring says *a hold is shown to have teeth by making the record reuse a hash on size and modification time alone*;
  that is not what happens.
- **Evidence** (mutations in a clone under `/tmp/s02-converge/A`, the checkout untouched):
  (1) `Record.digest` reuses any held hash whatever the file's facts say — all of `test_runner_controls_park` passes
  (AC-S02-2, -3, -4, -6, -7, -8 holds green); `test_runner_controls` fails only its two *reads* examples.
  (2) `Record.digest` compares size and modification time only (`held[0][:2] == facts[:2]`) — `test_runner_controls` and
  `test_runner_controls_park` pass whole, 20 tests; the only red in the suite is the fingerprint's
  `test_hold_a_same_size_rewrite_with_different_bytes_changes_the_value_even_with_its_time_restored`, which shares the
  class. So AC-S02-3 and AC-S02-4, the two criteria D56 exists for, are held for the controls by no test of the controls,
  and nothing would go red if the strict record alone were weakened.
  (3) An unreadable file answered from its held hash — the AC-S02-8 hold stays green, for the same reason.
- **RED.** The same holds with the changed gate vouched for by the record at the before-signature of the iteration that
  changes it (the gate older than the margin when that signature is taken: a first iteration that outlasts the margin
  and a second that edits, or the equivalent at the probe seam with the record's clock moved as
  `test_runner_controls.py` already does), each seen red under mutation (2), and AC-S02-8 under (3). The wait is real
  where the runner is run for real — D50's T023 let such waits stand; it is not a seam or a setting.
- **GREEN — the class:** every *hold* written against a record, memory or offset in this slice is run in a state where
  that record vouches for the file under test, and is seen to fail when the record's rule is weakened; the docstring
  says what was actually seen. Sweep the slice's other holds for the same shape (the log's and the fingerprint's were
  seen red here: see the verdict).

### T017 — [MEDIUM] The fragment names CI as what sees a narrowed comparison's blind spot; D59 says it is not the catch (AC-S02-46)

- [x] *(1c01ecc)* **Found.** `changelog.d/runner-bookkeeping.md:9` lists *`make verify` on the trunk or any branch not named
  `slice/<id>`, CI, or any check after `.codegraph/gate-memory.json` is deleted* as the next whole comparison. D59:
  *CI normally has no index, so it is not the catch* — `.codegraph/` is ignored by git, and with no index the gate says
  so and passes (`docs/verification.md`).
- **GREEN — the class:** a published sentence that tells a person what catches a residual names only what does, in the
  state a generated project is actually in; here, CI is named only *where CI has an index*, or dropped. By reading; no
  code involved.

### T018 — [LOW] The AC-S01-24 row of e36 discriminates nothing of its own (lead d; AC-S02-36)

- [x] *(0a790c2 — the row rides on AC-S01-23's and says so)* **Found, by reading and not by mutation.** `tests/test_health_memory_states.py:162` gives the *not safely older*
  state the same `after` step as the AC-S01-23 row above it (`same_size_with_its_time_restored`), which moves the
  change time, so the file is a candidate with or without the two-second rule and the row passes either way.
- **GREEN — the class:** a row in a state table is either seen red with the rule it names removed, or says in its name
  which other row's mechanism it rides on.

### T019 — [LOW] Constructor arguments nothing passes (lead b; constitution III)

- [x] *(b5f15bc)* **Found.** `Record(clock=…)` (`bookkeeping.py:48`) and `Log(report=…)` (`bookkeeping.py:91`) are passed by nothing in
  the tree: the tests assign `CONTROL_RECORD.clock` / `SPECS_RECORD.clock` as attributes, and only `Record(report=…)` is
  constructed with an argument (`tests/test_runner_controls.py:129`). Neither is reachable by an iteration — the three
  instances (`cruise.py:463`, `:498`, `:541`) are built with no argument, and no environment variable or file feeds them
  — so this is surplus, not a hole.
- **GREEN — the class:** a parameter exists because a caller passes it; drop the two, or have the tests construct
  through them.

## Phase 4: Convergence, pass 2 (written by `drive-converge` at `4dda695`; to be copied under the pass-1 tasks)

Grades as in pass 1: `CRITICAL` and `HIGH` re-open the loop, and past the bound only a `CRITICAL` does. Neither task
below is either.

### T020 — [LOW] The stream's identity is a second witness no example isolates (D58 · AC-S02-31)

- [x] *(closed by T025, 4cd0398)* **Found, by mutation.** `stream_use()` (`assets/toolkit/scripts/agents/cruise.py:796`–`813`) reads from the marker's
  byte only where the bytes there are the marker line *and* the path is still the file written through. With the
  identity clause removed (`if found == marker.encode("utf-8"):`) all six examples of `tests/test_runner_stream.py`
  pass; with the marker clause removed and the identity kept, only *cut short* goes red, so *replaced* is held by
  the marker alone. The same shape pass 1's T016 note records for the control record's identity.
- **GREEN — the class:** a clause in a guard is either seen red when removed, or the docstring beside it says which
  other clause it rides behind and that no example isolates it; here, an example where another file is moved into the
  path with the same marker line at the same byte, or one sentence in `stream_use()`'s docstring and the module
  docstring of `test_runner_stream.py`. The answer is the same either way (the last marker for the iteration wins in a
  whole read too), which is why this is `LOW`.

### T021 — [LOW] `health()`'s three `except Exception` arms are run by no example (D59 · AC-S02-37, -40; constitution III, V)

- [x] *(closed by T025, 4cd0398)* **Found, by mutation.** In `assets/toolkit/scripts/agents/code_index.py`: `compare()`'s arm (`:245`), `memory_of()`'s
  (`:258`) and `renew()`'s (`:273`). Each narrowed to an exception nothing raises (`except ZeroDivisionError:`), and
  `compare()`'s made to answer *current* (`return Compared(([], [], []), 0, None)`): `test_health_memory`,
  `test_health_memory_states` and `test_health_narrowed` pass whole all four times (20 tests each). The gate's own
  functions already turn every failure the examples provoke into a reason (`remembered()`,
  `check-codegraph.py:386`–`411`) or swallow it (`remember()`, `:318`), so the arms are a second line nothing reaches.
  Each fails toward the whole comparison or toward not writing the memory, so nothing unsafe hides behind them; what
  is unproved is only that they do what their comments say.
- **GREEN — the class:** an `except` arm that changes what a comparison answers is run by an example or is not there:
  a fake `tooling` written in the test tree (a class with the gate's functions, one of which raises — `compare()`,
  `memory_of()` and `renew()` take it as an argument, so no mocking framework is involved) showing *compared
  everything: the record … could not be read*, and a `renew()` that raises leaving `health()`'s answer as it was;
  or the arms are dropped where the gate's own handling is the whole of it.

### T022 — [LOW] An entry with two `Scope:` lines passes the gate, and the verb reads the first (the hand's note 2 at the demo · D60)

- [x] *(closed by T026, d368f3a)* The hand wrote `Scope: S11-render-once` followed by `Scope: global` in one entry: `check-decisions` passed and
  `--scope S02` left the entry out. D60 says the first line is the one read and that the filter never drops what it
  cannot place; an entry that says two things is one it cannot place. **GREEN closes the class:** an entry whose scope
  the checker cannot read as one statement — a second `Scope:` line among them — is refused by the gate naming it, and
  carried as global by the verb. Taken in Phase 4 with the adversary's findings, through a failing test.

## Phase 4: After acceptance — the adversary's findings (appended by the host; D63, D64; the row `## S02 ·` in `adversary-log.md`)

Each is a failing test first, then the smallest change; each GREEN closes its class. Constraints as at the top.

### T023 — [HIGH] A control changed between two iterations parks the run; across a park it is named (adversary A2 · D64 · AC-S02-70 … -79)

- [x] *(cc4c3ee)* `drive()` in `assets/toolkit/scripts/agents/cruise.py` keeps the last after-signature and whether `park()` has
  returned since, and compares it with the next before-signature through `controls_changed()`: no park between → the
  run parks before the iteration starts (no entry, the number not consumed, a message already taken rides on); a park
  between → one `cruise:` line in the feed and `controls_changed_between` on the entry. D64 says what parks, what is
  named, `--no-park`, `tools/`, and the note for the implementer (the *started* line and `deliver()` come before
  `controls_before` today; `watch`'s `boundary()` against the new line). The generated command's *Blocked* paragraph
  says it, at its source under `src/slipwai/project/`; the fragment gains D64's sentences. Reproduction to turn into
  the first test: `/tmp/s02-adv-A/probes2.sh` with `escaped.py`.

### T024 — [HIGH] The runner never blocks on a path of its own that is not a regular file, and names a changed control first (adversary A1, B1, A3 · D63 · AC-S02-80)

- [x] *(a6ac3ce)* `stream_use()` and the log's reader and appender (`cruise.py`, `bookkeeping.py`), `delegate_use_read()`
  (`code_index.py`). Reproductions: `/tmp/s02-adv-A/probes5.sh` (`gate-and-stream-fifo`, `gate-and-log-fifo`),
  `/tmp/s02-adv-B/p11.sh`. Every test that could hang runs its child under a timeout, so a failure is an assertion.

### T025 — [LOW] `health()` says what it did and writes what a gate would; guard clauses are seen red or gone (adversary B2, B3; T020, T021 · AC-S02-87, -88)

- [x] *(4cd0398)* `code_index.py` (`Compared.said()`, `renew()`, the three `except` arms), `cruise.py` (`stream_use()`'s identity
  clause). Reproductions: `/tmp/s02-adv-B/p14.sh`, `p1.sh` (P3, P6).

### T026 — [HIGH] A `Scope:` the checker cannot read as one statement is refused by the gate and carried by the verb; ids meet on their head (adversary C1, C2, C3, C7, C8; T022 · D63 · AC-S02-81 … -83)

- [x] *(d368f3a — the Status and byte-order-mark refusals it built are withdrawn by D65, T028)* `assets/toolkit/scripts/check-decisions.py` (`meets()`, `SLICE_ID`, `scope_tokens`, `scope_finding`, the entry
  parser's line splitting). Reproduction: `python3 /tmp/s02-adv-C/repro.py`, blocks C1 to C3, C7, C8.

### T027 — [MEDIUM] The verb never answers a call it did not understand with a green run, never drops a block, never ends on a traceback (adversary C4, C5, C6, C9 · D63 · AC-S02-84 … -86)

- [x] *(5c58152)* `check-decisions.py` (argument handling, the verb's printing and closing line, the read). Reproduction:
  `repro.py`, blocks C4 to C6, C9.

### T028 — [MEDIUM] The gate refuses nothing a log written before this release can contain (D65 · AC-S02-57, -83, -85)

- [x] *(2bd37b8; the gate reads a byte-order mark as the earlier checker did, only the verb reads past it — D65 as settled)* `check-decisions.py`: a second `Status:` line is a `note:`, not a finding; a byte-order mark at the start of the
  file is read past by the gate and the verb; a differential example holds the gate's exit code and findings to the
  checker at `596740f` over a set of logs with no `Scope:` line. The fragment gains the sentences T026 and T027 handed
  back, as D65 leaves them.

*(T022 is closed by T026; T020 and T021 by T025.)*

## Convergence

**Pass 1 — NOT CONVERGED: two `HIGH` (T015, T016), one `MEDIUM` (T017), two `LOW` (T018, T019). Incomplete — the budget
ended before every criterion was traced; what was not done is listed last.** Judged at `f849ef7` over
`git diff 596740f..HEAD -- assets src docs tests VERSION changelog.d`. The slice's fifteen targeted suites ran green
through `make test TESTS=…` (97 tests, 1 skipped). No file of the checkout was mutated: every mutation ran in a clone
under `/tmp/s02-converge/`.

### Constitution, principle by principle

- **I (owns its files, passes its own gate; a memoised gate is additive).** *Version and fragment:* `VERSION:1` reads
  `1.6.0.dev0`; `changelog.d/runner-bookkeeping.md:1` claims `MINOR`; `tests.test_changelog` green. *Nothing of the
  project's overwritten:* `git diff 596740f..HEAD -- delivery` is empty (D9). *The gate is not narrowed:*
  `check-codegraph.py` gains two docstring lines and no code; `health()` neither reads nor writes the memory under a CI
  marker (`code_index.py:254`, `:266`), seen red when the first is removed (`test_e38…`, three examples).
  **Unmet in one reach:** the controls comparison lost a path it held (`cruise.py:523`–`536`; T015).
- **III (simplicity, the rung).** The record lives in the process and is never written (`bookkeeping.py:8`; D56–D58), one
  class serves both records (`cruise.py:463` `strict=False` per D57, `:541` `strict=True` per D56), `health()` uses the
  gate's own functions and memory rather than a second cache (`code_index.py:229`–`274`). Surplus: T019.
- **V (acceptance at the use case).** The runner is driven as a subprocess against a fake harness and the log read back
  (`tests/test_runner_controls_park.py:66`, `tests/test_runner_log.py`, `test_runner_log_stale.py`); fakes are written
  in the test tree, no mocking framework. **Unmet for AC-S02-3, -4, -6, -8 as proof:** T016.
- **VII (observability).** What the bookkeeping did is said where a person reads it: `bookkeeping.log_bytes` and
  `stream_bytes` on the entry (`cruise.py:1329`–`1331`), and `health()`'s one-line account (`code_index.py:219`–`226`).
- **VIII (a persisted schema is additive; readers tolerate).** The entry's `bookkeeping` object is optional and nothing
  reads it back (`cruise.py:1329`); the memory file is written only through the gate's own writer
  (`code_index.py:270`–`272`); a `Scope:` line is accepted absent and refused only when present and malformed
  (`check-decisions.py:129`, `:178`), and the filter carries what it cannot place as global (`check-decisions.py:317`).
- **XIII (target, not in force).** No test asserts a wall-clock ratio (AC-S02-21, D58). T016's RED needs a real wait
  past the two-second margin where the runner runs for real; D50's T023 is the precedent.
- **XIV (the same bar).** The diff edits no specification, criterion or constitution; both full gates are the host's
  T014 and were not run here.
- **II, IV (target), VI, IX–XII, XV:** not touched by this diff. The log has one writer; its append re-checks the
  file's facts first (`bookkeeping.py:129`–`131`), seen red when that check is removed (five examples of
  `test_runner_log_stale`).

### Level by level

1. **Logic.** *Proved:* the two records are built with the rule their decisions give (lead g); the margin and the
   all-four rule read as D56 writes them (`bookkeeping.py:27`–`42`, `:70`); the check before the append and the whole
   read on any difference (lead h) are held by tests seen red; a tolerant parse of the log is caught by both AC-S02-29
   examples (lead f, e29); a signature that moves on a touch is caught by the AC-S02-5 park half (lead f, e5); `health()`
   in CI is caught (lead i). `--scope`: equal-or-bare-prefix matching, the first `Scope` line read, overridden entries
   named, the counts — run by hand on a seven-entry log, all as D60 says; e59, e60 and e62 go red with the gate's code
   disabled (lead c: discriminating). `stream_bytes` is 0 for a deleted stream or no index, which is what was read (lead
   e: not a finding). *Not proved:* T015, T016. e7 guards code the slice did not alter, and no mutation of the slice's
   diff reaches it. The `except Exception` paths of `compare()` and `memory_of()` (`code_index.py:245`, `:258`) and
   `stream_use()` were read, not mutated.
2. **Use case.** One iteration end to end is exercised by the subprocess suites, green. `health()` before it: one
   `sync` at most and only where files are behind (`code_index.py:329`–`330`), a rebuilt database compared whole
   (`:346`), the memory renewed only on `current`/`synced` (`:350`). Read and suite-green; not re-derived by mutation.
3. **Delivery adapter.** `check-decisions.py --scope`: entries and the closing line on stdout, exit 0; several
   `decisions.md` or none, one line on stderr, exit 1; a malformed command line, usage on stderr, exit 2; no file
   written, no `__pycache__/` (run in a scratch generation). The log entry: `bookkeeping` as above.
4. **Screen.** None in this slice.
5. **Published contract.** In a scratch generation: `commands/cruise.md`, `agents/drive-skipper.md` and
   `agents/drive-bosun.md` carry the verb and the `Scope:` line; the entry shape is in `commands/cruise.md`,
   `.specify/product-owner.md` and the checker's docstring; the verb runs as the pages say. The fragment's sentences on
   the log, the stream, `bookkeeping`, the fingerprint, the controls and `Scope:` match the code; one does not (T017),
   and it does not yet say what T015 found. No toolkit `open`/`read_text` added by the diff lacks `encoding="utf-8"` or
   binary mode (lead j).

### Not finished

- A criterion-by-criterion trace of all 69: AC-S02-18 to -20, -32, -33, -42 to -44 and -68 were taken on the green
  suites and not individually followed to an assertion.
- An **adopted** layout was not generated: that `scripts/check-decisions.py` in the briefs becomes
  `delivery/scripts/…` rests on reading `Layout.relocate` (`src/slipwai/layout.py:90`), not on a run.
- T018 was read, not mutated; the stream's offset (T012) and `health()`'s exception paths were not mutated.
- This file now has two `## Phase 4` headings (User Story 3's, and the one above, which the brief named).

### Pass 2

**Pass 2 — CONVERGED: no `CRITICAL`, no `HIGH`, no `MEDIUM`; two `LOW` (T020, T021), which the slice may ship
without. T015 and T016 are closed as classes; T017, T018 and T019 are closed. Complete for what the brief named;
what was not re-done is listed last.** Judged at `4dda695` (`adopt-method`), in clones under `/tmp/s02-converge2/`
(removed); nothing in the checkout was written, run or mutated. Every mutation was restored with
`git checkout -- <path>` and the clone's `git status` read empty after each batch.

**Nothing found is a `CRITICAL`.** No route was found by which an iteration changes a gate unseen on an ordinary
filesystem with no clock moved: see T015 and T016 below.

#### What pass 1 found, re-run at this tip

- **T015 — closed as a class.** `control_paths()` (`cruise.py:527`–`541`) takes the registry's hash through
  `CONTROL_RECORD.digest(REGISTRY)` on every call and derives the hook files again whenever it is not the hash they
  came from; `controls_signature()` (`:548`–`571`) uses that same hash as the registry's entry, so the path set and the
  signature are of one reading. The registry is the only input that decides which paths are covered — the rest are
  constants (`CONTROL_PATHS` `:147`, `SKIPPED_DIRECTORIES` `:150`). Reproduced in a generated `standard`/`python`
  project, the runner loaded as `tests/test_runner_controls.py` loads it, **on the real clock**, the project settled
  2.2 s so the record vouched for the registry (`registry_held_at_before: true`):
  (a) a row gains a hook file → `[".newharness/hooks.json (added)", "scripts/agents/registry.json (modified)"]`;
  (b) the registry rewritten again at once, inside the margin, at the same size with its modification time restored
  (both checked equal), naming another file → `[".newharness/hooks.json (deleted)", ".oldharness/hooks.json (added)",
  "scripts/agents/registry.json (modified)"]`, and an edit of that file → `[".oldharness/hooks.json (modified)"]`;
  (c) a new process, the registry held, rewritten at the same size with its modification time restored → the registry
  `(modified)`, the new file `(added)`, the old `(deleted)`, and its edit `(modified)`. Only the change time cannot be
  put back, which is the fragment's stated residual (a clock set back). `guard()` (`:589`) runs in a process of its
  own per edit, with an empty record, so it hashes the registry and derives the paths afresh: a new process listed
  the gained file among `control_paths()`. A deleted registry raises `FileNotFoundError` from the signature, as it did
  at `596740f`, where `registry()` was read on every call — loud, and unchanged by the slice.
  AC-S02-1 is kept: `test_a_registry_change_is_read_once_and_a_registry_no_one_touches_is_not_opened_again` green.
  The three examples of `tests/test_runner_controls_paths.py` are red against `7b481a6^`'s `cruise.py` (3 of 3) and
  green at the tip.
- **T016 — closed as a class.** `Record.digest` (`bookkeeping.py:56`–`72`) weakened in the clone, the park, controls
  and paths suites run each time (15 tests, green unmutated):
  reuse any held hash → 5 park holds red (append, in-place, rename, the person's edit, unreadable), 9 red in all;
  size and modification time only → 3 park holds red (in-place, rename, unreadable);
  no change time → 2 park holds red (in-place, unreadable).
  These are the counts `924e19b` and the module docstring claim. Pass 1 saw 0, 0 and 0 park holds red. The identity
  alone is not isolated, and the docstring says so (`tests/test_runner_controls_park.py`, *Not shown red*).
- **T017 — closed.** `changelog.d/runner-bookkeeping.md:9` now names CI only *where CI has a code index*, and says why.
- **T018 — closed.** The row's name (`RECENT_ROW`, `tests/test_health_memory_states.py:166`) says what it rides on.
- **T019 — closed.** `Record.__init__` takes `strict` and `report` (`bookkeeping.py:48`), `Log.__init__` the path
  (`:91`); the three instances are `cruise.py:463`, `:498`, `:545`; the one `report=` caller is
  `tests/test_runner_controls.py:129`.

#### What pass 1 did not finish

- **AC-S02-18** — `tests/test_runner_fingerprint.py:143`: two probe processes over one tree, values asserted equal.
- **AC-S02-19** — `:152`: a stray file outside `specs/`, then an empty commit; both move the value and
  `opened("specs")` is `[]` both times.
- **AC-S02-20** — `:172`: a log carrying two earlier-code fingerprints; exit 3, *no progress since iteration 3*, entries
  1–4.
- **AC-S02-32** — `tests/test_runner_log_stale.py:142`: `status`, `where`, `resume`, `tell hello` over fifty entries,
  exit code and stdout equal to text captured before the slice. (`where` and `resume` print nothing in that state, so
  for those two the hold is the exit code and the silence.)
- **AC-S02-33** — `:163`: the log emptied during a park; *parked — no progress* twice, the first naming iteration 1.
- **AC-S02-42** — `tests/test_health_narrowed.py:203`: fifty `health()` runs, each `current` and `hashed 0 of N`; at
  iterations 2 and 50 no tracked file is among the files opened.
- **AC-S02-43** — `:68`: `current` → no call; behind → exactly `["sync ."]`; no database → `["init -y ."]`; garbage →
  `rebuilt`, `["init -y ."]`; no route → no call.
- **AC-S02-44** — `:99`: the gate's stdout on `feature/x`, detached and under each CI marker equals today's, after
  `health()` has run beside it; the corrupt-database rebuild line asserted, with no `hashed`.
- **AC-S02-68** — `tests/test_cruise_scope_writers.py:73`: a brief seeded without the line and then edited is
  byte-equal after `migrate`, `git status` empty; the *add it by hand* half is the fragment's **Catch-up** paragraph
  (`changelog.d/runner-bookkeeping.md`, last paragraph), by reading.
- **The stream offset (AC-S02-30, -31), by mutation** of `stream_use()`: no verification at all → both *cut short* and
  *replaced* red; never the offset → both e30 examples red; identity only → *cut short* red; marker only → all green
  (T020). `delegate_use_read()` (`code_index.py:572`) seeks to the offset it is given and reports `len(data)`; the
  e30 assertions on `stream_bytes` are what hold it.
- **`health()`'s exception arms, by mutation:** none is reached by an example (T021).
- **An adopted layout, by a run:** `slipwai adopt --yes --no-init` in a scratch repository. `delivery/commands/cruise.md`
  (`:35`, `:115`), `delivery/agents/drive-skipper.md:17` and `delivery/agents/drive-bosun.md:17` say
  `python3 delivery/scripts/check-decisions.py --scope <slice-id>`; that command, run there over an empty
  `decisions.md`, printed the closing line and exited 0. The runner loaded from `delivery/scripts/agents/cruise.py`
  signs 31 files, `delivery/scripts/agents/registry.json` among them, and reports it `(modified)` when edited.

#### Constitution, principle by principle (what changed since pass 1)

- **I (owns its files, passes its own gate; a memoised gate is additive).** Pass 1's one unmet reach is met: the
  controls comparison covers every path the registry names at the moment of the signature (`cruise.py:534`–`541`,
  `:565`–`566`), and no check was removed to make the loop faster. `VERSION:1` is `1.6.0.dev0`;
  `changelog.d/runner-bookkeeping.md:1` claims `MINOR`; since pass 1 the user-visible trees changed in
  `bookkeeping.py`, `cruise.py` and the fragment only, each commit saying its level.
- **III (simplicity, the rung).** T019's surplus is gone (`bookkeeping.py:48`, `:91`). The fix for T015 added no second
  cache: one tuple beside the record it is keyed on (`cruise.py:524`). Remaining surplus: T021's arms.
- **V (acceptance at the use case).** Met for AC-S02-2, -3, -4, -6, -8 as proof: the holds run with the record vouching
  for the file and go red under each weakening (above). Fakes are written in the test tree (`fake_harness`, the
  `mutate.py` script); no mocking framework. Unproved: T020, T021.
- **VII (observability).** Unchanged: `bookkeeping.log_bytes` and `stream_bytes` on the entry (`cruise.py:1335`–`1337`),
  `health()`'s one-line account (`code_index.py:219`–`226`).
- **VIII (a persisted schema is additive; readers tolerate).** Unchanged since pass 1; `_HOOKS` and both records live
  in the process and are never written.
- **XIII (target, not in force).** The park suite now has one real wait of 2.2 s for the module and one more in the
  person's example (`tests/test_runner_controls_park.py`, `SETTLED`); no assertion reads a clock. The three health
  suites took about 145 s together in the clone, as before the fixes.
- **XIV (the same bar).** No specification, criterion or constitution edited by `7b481a6..b5f15bc`; the full gates are
  the host's and were not run here.
- **II, IV (target), VI, IX–XII, XV:** not touched by this diff.

#### Level by level

1. **Logic.** *Proved:* the path set is as fresh as the signature (T015, by run and by its three examples seen red on
   the earlier code); the record's rule is held by the park holds (T016, three weakenings); the offset is taken only
   where the marker is at its byte and is what bounds `stream_bytes`. *Not proved:* the stream's identity clause
   (T020); the three `except` arms (T021).
2. **Use case.** One iteration through the runner as a subprocess: park on a gained hook file and on its later edit
   (`test_runner_controls_paths.py`, third example), park on each fooling edit with the record engaged. `health()`
   before it: sync at most once, traced to `test_health_narrowed.py:68`.
3. **Delivery adapter.** `check-decisions.py --scope` run in an adopted layout from its relocated path: stdout, exit 0.
   The log entry's `bookkeeping` unchanged.
4. **Screen.** None in this slice.
5. **Published contract.** The fragment's sentence on CI is corrected (T017); the adopted layout's briefs and command
   page carry the relocated verb path, seen in a run rather than read off `Layout.relocate`.

#### Not re-done in this pass

- The criteria pass 1 traced were not traced again; of the 69, this pass followed the nine pass 1 left, and
  AC-S02-1 to -8, -30 and -31 by run or mutation.
- Of the slice's fifteen targeted suites, seven were run here (`test_runner_controls`, `_park`, `_paths`,
  `test_runner_stream`, `test_health_memory`, `_states`, `test_health_narrowed`), all green unmutated; the other
  eight rest on pass 1's run and on the host's gates.
- The generated (non-adopted) pages were not regenerated; pass 1 read them.
