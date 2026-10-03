# Implementation Plan: S02-runner-bookkeeping — cruising at iteration 50 costs what iteration 1 did

**Branch**: `adopt-method` (D12 — no `slice/` branch, no claim, no push) | **Date**: 2026-10-03 |
**Spec**: [spec.md](../../spec.md), *Slice acceptance criteria* → `### S02-runner-bookkeeping` (AC-S02-1 … AC-S02-69)

**Input**: the slice's row in [story-split.md](../../story-split.md) and its criteria in `spec.md`; decisions
D7, D9, D12, D39, D46, D49, D50, D56, D57, D58, D59, D60 in [decisions.md](../../decisions.md). Written by cruise
iteration 9 (host, strong model). The optional `before_plan` hook (`/characterise`) is taken as the ladder's Pin
stage, after tasks.

## Summary

Before and after every iteration the runner re-does work whose answer it already has: it hashes every control
file twice, reads every file under `specs/` to fingerprint the tree (and again on every poll of a park), parses
the whole log up to twice, reads the whole raw stream to find one iteration's lines, and has the code index hash
every tracked file. After this slice the runner process remembers what it read — content hashes beside each
file's size, times and identity (D56, D57), the log as it left it (D58), the byte it wrote the stream's marker at
(D58) — and `health()` compares through the gate's own memory (D59). What is compared is unchanged: controls and
the fingerprint are still content, the iteration number is still the count of entries, the gate on the trunk and
in CI is untouched. Separately, a decision entry may carry a `Scope:` line, `check-decisions.py --scope <id>`
prints the standing entries a slice's question needs, and the generated command and briefs write and read it
(D60). A MINOR: `VERSION` to `1.6.0.dev0`, one fragment.

## The example map (rules the tasks cut on)

Each example is the criterion of the same number in `spec.md` — **e*n* is AC-S02-*n*** — read there, not restated
here. The **runner** in every example is `assets/toolkit/scripts/agents/cruise.py` run as a generated project runs
it, against the fake harness `tests/test_cruise_runner.py` already drives (`CRUISE_HARNESS_COMMAND`); the
**indexed project** is `indexed()` from `tests/test_code_index_health.py` with its fake `codegraph` CLI.

### User story 1 — what the runner remembers (`agents/cruise.py`, new `agents/bookkeeping.py`) `[US1]`

| Rule | Criteria | What it says | Examples |
|---|---|---|---|
| **R1** a control's content is read once while its size, times and identity stand; the comparison is still content | AC-S02-1 … -11 | The record is the runner process's, all four facts or nothing, two seconds' margin, a fresh stat for every before and after | e1 e5 e9 e10 e11 (the reads) · e2 e3 e4 e7 e8 (the park: e2, e7, e8 hold today and are written as holds; e3 and e4 are holds that the record must not break) · e6 (a person's edit during a park is not charged to the next iteration — holds today) |
| **R2** the fingerprint is path and content, each file read once while its record stands | AC-S02-12 … -21 | Per-file SHA-256 in the digest, so the value changes once; D49's record, as many facts as the platform reports | e12 e13 e14 e17 (the reads) · e15 e16 (changes are seen) · e18 e19 (commit and status still count; two processes agree — `tests/test_cruise_runner.py`'s *no progress since iteration 2* stays green) · e20 (a log carrying older values is read) · e21 (files opened on call 50 equal call 2: a count) |
| **R3** the log is read whole once per process, and again only when it is not what the runner left | AC-S02-22 … -29, -32, -33 | `bookkeeping.log_bytes` on each entry says what was read; the number stays the count plus one; the facts are checked again before the append | e22 e23 (0 bytes on a later iteration, whatever the history) · e24 e25 e26 e27 e28 (cut, deleted, replaced, edited in place, appended by another hand → one whole read) · e29 (a line that does not parse ends the run as today — a hold) · e32 (`status`, `where`, `tell`, `resume` print what they printed — holds) · e33 (the stuck window is not re-seeded — a hold) |

### User story 2 — the index before an iteration (`agents/code_index.py`, `check-codegraph.py`) `[US2]`

| Rule | Criteria | What it says | Examples |
|---|---|---|---|
| **R4** `health()` hashes what changed since the last whole comparison, on any branch outside CI | AC-S02-34, -35, -41, -42 | The gate's own candidates and memory; `detail` says how many of how many | e34 (0 hashed on `main`, `slice/S1`, `feature/x`, detached) · e35 (one changed file: hashed 1, one sync, `synced`) · e41 (a `touch` costs one hash once) · e42 (opens no tracked file on an unchanged tree) |
| **R5** what the memory cannot vouch for is the whole comparison, said in one clause | AC-S02-36, -37, -39 | Every drift state of S01 answers as `health()` without a memory does; a rebuilt database is compared whole | e36 (one example per state: AC-S01-13, -14, -15, -16, -17, -18, -23, -24, and the no-row state) · e37 (each reason, its clause) · e39 (corrupt → moved aside, rebuilt, whole) |
| **R6** the memory is written by a `health()` that ends current, and never in CI | AC-S02-38, -40 | Through the gate's writer; `failed`, `unreachable`, unopened → as it was | e38 (each CI marker: whole, memory bytes and times unchanged) · e40 (current and synced write what a passing gate would; the failures write nothing) |
| **R7** the gate, the sync count and the tree are today's | AC-S02-43, -44, -45 | At most one `sync`, before the iteration; `make check-codegraph` byte for byte; nothing left for `git status` | e43 (fake CLI counts its `sync` calls — a hold) · e44 (`tests/test_codegraph_*.py`, `tests/test_code_index*.py` pass with no edit) · e45 |

### User story 3 — the `Scope:` line in the checker (`check-decisions.py`) `[US3]`

| Rule | Criteria | What it says | Examples |
|---|---|---|---|
| **R8** `--scope <id>` prints the standing entries in scope, global, or without a line | AC-S02-47 … -56 | Verbatim, in number order, a closing line of counts; never drops what it cannot place; writes nothing | e47 … e56 |
| **R9** the gate accepts absence and refuses a malformed line | AC-S02-57 … -63 | Empty, or neither `global` alone nor id-shaped tokens → exit 1 naming the entry; a missing line after a present one → a `note:` | e57 (this repository's log as it stands, copied as a fixture — a hold) · e58 … e62 · e63 (the checker at `HEAD` before the slice, taken with `git show`, passes a log carrying the line — a hold) |

### User story 4 — the writers (`src/slipwai/project/`) `[US4]`

| Rule | Criteria | What it says | Examples |
|---|---|---|---|
| **R10** the entry's shape, both briefs and the command write and read the line | AC-S02-64 … -68 | `DECISION_ENTRY`, the skipper's and the bosun's briefs, the command's iteration-start and *Deciding* text; an owner brief already seeded is left alone | e64 … e68, each read from a generated project's files |

### User story 5 — the stream, and the release `[US5]` (after US1 and US2: it touches both their files)

| Rule | Criteria | What it says | Examples |
|---|---|---|---|
| **R11** an iteration's `index_use` is read from the byte its marker was written at | AC-S02-30, -31 | `bookkeeping.stream_bytes`; the marker at the offset is the check; otherwise today's whole read | e30 · e31 |
| **R12** the release says what it is | AC-S02-46, -69 | `VERSION` `1.6.0.dev0`; one `MINOR` fragment with the catch-up paragraph and the three residual sentences; the pages that say only the gate narrows say the runner does too | e69 (`tests/test_changelog.py` green) · e46 |

Holds are written as holds, saying so. Every other example is **seen** failing for its stated reason before the
production file is touched.

## Technical Context

**Language/Version**: the scripts run on the project's `python3` (the skeleton pins 3.13); standard library only.
The factory's own code and tests: Python ≥ 3.11 (`pyproject.toml`).
**Primary Dependencies**: none added. `git`, as today.
**Storage**: none new on disk. The records of R1–R3 and R11 live in the runner's process (D56, D57, D58). The
gate's `.codegraph/gate-memory.json` gains a second writer, `health()`, through the gate's own function (D59).
`specs/cruise-log.jsonl` entries gain an optional `bookkeeping` object (D58).
**Testing**: `unittest` via `make test`. The runner is run as a subprocess against the fake harness and its log
read back; what a call opened is observed with the audit-hook wrapper `tests/gate_audit.py` (S01's, `open`
events), not a mocking framework and not a timing. A function of the runner is called in a `python3 -c` child
with `sys.dont_write_bytecode` set, as `tests/test_cruise_guard.py` loads it. The fake `codegraph` CLI is the one
in `tests/test_code_index_health.py`.
**Target Platform**: Linux, macOS, Git Bash. e10 (no change time or identity) is exercised by handing the record
a stat result without them; an example that needs a symbolic link or `os.utime` in nanoseconds skips, saying why,
where the platform cannot.
**Project Type**: CLI tool, the factory — deployable `slipwai-graph`, kind `tool`, path `.`.
**Performance Goals**: SC-006 — held as counts: bytes read from the log and the stream, and files opened by the
fingerprint, the signature and `health()`, do not depend on how many iterations came before.
**Constraints**: nothing under this repository's `delivery/scripts/`, `tools/`, the `Makefile`, CI or hook
settings changes, and no file `delivery/.written` lists (D9); every file under `src/` and `tests/` stays within
350 lines (`src/slipwai/project/cruise.py` is at 331 and `tests/test_cruise.py` at 350: new text goes through
`cruise_record.py` and `cruise_agents.py`, new tests in new files); every `open`/`read_text` in a toolkit script
names `encoding="utf-8"`; no setting, no flag but `--scope` and `--feature` on `check-decisions.py`.
**Scale/Scope**: four scripts under `assets/toolkit/scripts/` and one new sibling module; three modules under
`src/slipwai/project/`; about nine new test files; one fragment; four pages of words.

## Constitution Check

*GATE: evaluated against `.specify/memory/constitution.md` before research; re-checked after design.*

| Principle | Touched? | How this slice satisfies it |
|---|---|---|
| I. A generated project owns its files and passes its own gate (NON-NEGOTIABLE) | Yes | *A scoped or memoised gate MUST be additive … no check is removed anywhere*: `check-codegraph`'s `main()` and `narrowable()` are not edited and its trunk and CI runs are byte for byte today's (R7, e44); the runner's comparison of controls stays one of content (R1); `check-decisions` refuses nothing a log written before this release contains (R9, e57). Every starter still passes its own gate (the matrix tests). An owner brief already seeded is not rewritten (e68). `VERSION` is raised once, in the commit that adds the line, with its fragment (R12). |
| III. Simplicity | Yes | One record class for R1 and R2 (path → hash beside its stat), in one new module beside the runner; no file on disk, no setting. The filter is a verb of the script that already parses entries. |
| V. Acceptance-driven development | Yes | Each rule a RED-GREEN-REFACTOR cycle at the script's command line or the runner's log; holds are written as holds. |
| VIII. Versioning and breaking changes | Yes | MINOR: an optional line and an optional object, both ignored by readers already released (e63; D58 on the log's readers). The fingerprint's field keeps its name and shape. |
| XIV. Agent-generated change meets the same bar (NON-NEGOTIABLE) | Yes | Increment commits with the quickest relevant tests green; both full gates on the final tip; the hand runs the demo as the actor. |
| II, IV, VI, VII, IX, X, XI, XII, XIII, XV | No | No retry path, domain code, contract, telemetry, secret, pipeline or type changes. |

**Gate result:** no violation; *Complexity Tracking* stays empty. **Post-design re-check:** unchanged.

## Project Structure

```text
assets/toolkit/scripts/agents/bookkeeping.py   # new — R1–R3: the stat-vouched hash record, the log as the runner left it
assets/toolkit/scripts/agents/cruise.py        # R1–R3, R11: controls_signature(), fingerprint(), entries()/record(), iterate(), drive()
assets/toolkit/scripts/agents/code_index.py    # R4–R7: health(), behind(); R11: delegate_use() from an offset
assets/toolkit/scripts/check-codegraph.py      # R4–R6: only what health() needs made callable; main() and narrowable() untouched
assets/toolkit/scripts/check-decisions.py      # R8, R9
src/slipwai/project/cruise_record.py           # R10: DECISION_ENTRY
src/slipwai/project/cruise_agents.py           # R10: the skipper's and the bosun's briefs
src/slipwai/project/cruise.py                  # R10: the two sentences (331 lines today; no net growth past 350)
tests/test_runner_controls.py                  # new — R1
tests/test_runner_fingerprint.py               # new — R2
tests/test_runner_log.py                       # new — R3
tests/test_runner_stream.py                    # new — R11
tests/test_health_narrowed.py                  # new — R4, R7
tests/test_health_memory.py                    # new — R5, R6
tests/test_decisions_scope.py                  # new — R8
tests/test_decisions_scope_gate.py             # new — R9
tests/test_cruise_scope_writers.py             # new — R10
changelog.d/runner-bookkeeping.md              # R12
VERSION                                        # R12: 1.6.0.dev0
docs/cruise.md, src/slipwai/project/docs.py, assets/toolkit/scripts/extensions/codegraph/init.py  # R12: e46's pages
```

**Structure Decision**: one deployable, `slipwai-graph` (kind `tool`, path `.`, purpose confirmed); one bounded
context — the factory. The strategy on the map is `leave-it` at `Proposed` (D5): the code lands where the code
it changes already is. `bookkeeping.py` is a new file a generated project receives; [research.md](research.md)
item 1 is how the toolkit's files reach a project and what lists them, to be read before the first cycle.

## What this slice changes in code that was here (for the Pin stage)

1. The runner parks on a changed control and names it (`tests/test_cruise_guard.py`).
2. The stuck detector: equal fingerprints across iterations and across two runner processes park the run
   (`tests/test_cruise_runner.py`, *no progress since iteration 2*).
3. The iteration number is the count of the log's entries plus one, across runner processes.
4. `health()`'s states and `detail` (`tests/test_code_index_health.py`, `tests/test_cruise_index.py`).
5. `check-decisions`' verdict on a log whose entries carry no `Scope:` (`tests/test_cruise_record.py`).
6. The generated command's and briefs' words about reading the log (`tests/test_cruise.py`).

## Delegation

Stories 1 to 4 share no file and run as four concurrent `drive-implement` delegates in this checkout, each
committing by path; story 5 follows 1 and 2. The first commit of story 4 that adds the line to `DECISION_ENTRY`
carries `VERSION` and the fragment's first form (AGENTS.md: the number is raised in the commit that makes the
change); story 5 completes the fragment.

## Complexity Tracking

None.
