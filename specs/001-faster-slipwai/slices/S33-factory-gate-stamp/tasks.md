# Tasks: S33-factory-gate-stamp — the factory's own gate returns at once on a tree it already passed

**Input**: [plan.md](plan.md) (*The example map* R1–R5 is what the tasks cut on; *Pin*; *Structure Decision*),
[research.md](research.md) (R-1 to R-3), [data-model.md](data-model.md), [quickstart.md](quickstart.md); acceptance
criteria AC-S33-1 … AC-S33-10 in `specs/001-faster-slipwai/spec.md` under `### S33-factory-gate-stamp`; decisions D91,
D99, D100, D101 in `specs/001-faster-slipwai/decisions.md`. A method slice with no screen and no event model of its
own, so **no white box, no mockup task and no styling task**; the one story is **US1**, *a developer's second
`make verify` on an unchanged tree returns at once, and a slice of the suite or a CI run is never mistaken for it*.

**Branch**: `adopt-method` (D12). No `slice/` branch, no push, no claim. One commit per task, **in the scratch
worktree** (below) until T006 exports the result.

## The root `Makefile` is a control (D99, D101) — where the work happens

The cruise guard refuses an iteration an edit to the root `Makefile`. Every implementation task (T001–T005)
therefore runs in a **scratch worktree**, `/home/noahc/math/slipwai-graph-s33`, branch `s33-patch`, made off the tip
of `adopt-method` (`git worktree add -b s33-patch /home/noahc/math/slipwai-graph-s33 adopt-method`; the host makes it
before T001 and a delegate does not alter any other branch). Each task commits **by path** there. T006 exports the
result as `specs/001-faster-slipwai/slices/S33-factory-gate-stamp/s33.patch` and checks it applies to `adopt-method`;
T007 is a person's. Nothing in this slice edits the root `Makefile` on `adopt-method`.

**Files for the slice** (a manifest for every task below): the root `Makefile` (in the worktree) and the new
`tests/test_factory_gate_stamp.py` (under 350 lines, within 120 columns). **Not edited, by any task:**
`assets/toolkit/scripts/verify-stamp.py` and `check-slice-scope.py` (run where they ship, R-1; AC-S33-8),
`.github/workflows/verify.yml`, anything under `src/`, `assets/`, `delivery/`, `VERSION`, `changelog.d/` (no bump: the
root `Makefile` and `tests/` reach no user), and no second copy of the script.

## Constraints that hold for every task

- **Tests.** Standard library only; a fake is an executable or script written in the test tree implementing the
  tool's real command line — **never `unittest.mock`** or any mocking framework (`AGENTS.md`, *Delivery method*).
  The tests copy the root `Makefile`, `assets/toolkit/scripts/verify-stamp.py` and `check-slice-scope.py` into a
  temporary git repository whose `project.json` records `ci.branch` `main`, on a branch other than `main`, with
  `scripts/verify`-style stand-ins for the four checks (lint, typecheck, check-structure, the suite) that append to a
  log. Evidence is the stand-ins' log, never a printed line alone. Every `read_text`/`open` names `encoding="utf-8"`.
- **Environment of a run.** The environment has `CI`, `GITHUB_ACTIONS`, `GITLAB_CI` removed unless the example sets
  one, and `MAKEFLAGS`, `MFLAGS`, `MAKELEVEL`, `MAKEOVERRIDES`, `MAKEFILES`, `GIT_DIR`, `GIT_WORK_TREE`,
  `GIT_INDEX_FILE` removed, so the factory's own `make test` does not leak into the make under test
  (`tests/stamp_fixture.py` holds the tuples `CI_MARKERS`, `MAKE_STATE`, `GIT_STATE`; import, never re-list).
- **No wall-clock assertion**; every `subprocess.run` of `make` carries `timeout=180`.
- **RED is seen** for its stated reason before the Makefile is touched. A **hold** is written as a hold and **seen to
  have teeth** before it is committed (AC-S33-10): change the Makefile, observe the failure, restore with
  `git checkout -- Makefile` only for a change you made and have not committed over; confirm `git status` shows only
  the task's own files. A hold whose teeth cannot be shown is reported as such, not claimed.
- **Before each commit**, in the worktree: `make lint typecheck check-structure`. **Quick test of an increment**:
  `make test TESTS=test_factory_gate_stamp`.
- **Commit by path** (`git commit -m … -- Makefile tests/test_factory_gate_stamp.py`; the new test file
  `git add`ed by its exact path first); never `git add -A`, never `git commit -a`. Commit messages say the change
  reaches no user (no bump) — the root `Makefile` and `tests/` are not user-visible trees.
- **The pin** (plan *Pin*): the first `make verify` on a tree that has not passed runs the same four checks in the
  same order, now through the new `verify-checks` target. R1 e2 compares the log.

## Format: `[ID] [P?] [Story] Description` — each task is one increment, one commit

`[P]` marks a task whose files are disjoint from its siblings'. **None is marked here**: see *Parallel opportunities*.

---

## Phase 1: Implementation stage (scratch worktree `s33-patch`)

### T001 — [US1] A tree that passed is not judged again off the trunk (R1 · AC-S33-1, -2, -7)

- [ ] **Rule R1.** Creates `tests/test_factory_gate_stamp.py` with its fixture (the temporary repository, the
  copied files, the stand-in checks, the environment builder, the log reader) **only as far as R1 needs it**.

**RED** (each fails today because `verify` has no stamp and no `verify-checks` target):
- e1 `make verify` passes, then runs again unchanged → the second run's log shows **no check started**, one line says
  the tree already passed and when, exit 0 *(AC-S33-1)*.
- e2 after a pass, a tracked file changes (then, separately, an untracked non-ignored file, the `Makefile`, a file
  under `scripts/`) → a full run, the four checks in **the order they ran before**, compared with the log of the
  first run *(AC-S33-2; the pin)*.
- e3 a check fails (stand-in exits 1) → `make verify` exits non-zero, names the failure, **no stamp written**, and
  the next run is a full run *(AC-S33-7)*.

**GREEN** — root `Makefile`: the four checks move, in their order, under a new `verify-checks` target; `verify`
becomes `reuse` ‖ (`verify-checks` && `record`) calling `assets/toolkit/scripts/verify-stamp.py` where it ships, with
`--make "$(MAKE)"` and the trunk found through the script's own `standing()`. Nothing else in the file moves.

**REFACTOR:** the recipe's quoting and the one place the script's path is spelled; none otherwise expected.

**Verify:** `make test TESTS=test_factory_gate_stamp` green in the worktree, then `make lint typecheck check-structure`.
Commit by path.

**Files:** `Makefile`, `tests/test_factory_gate_stamp.py` (new).

### T002 — [US1] The trunk, CI and force always run in full (R2 · AC-S33-3, -4)

- [ ] **Rule R2.** Follows T001 (same two files). The script's own `standing()` and `VERIFY_FORCE` carry this
  rule, so **each example is observed first**: it is a RED with its GREEN named in the report if it fails, and
  otherwise a **hold written as one and seen to have teeth** (teeth: stop `verify` calling the script, or drop the
  environment pass-through) — the report says which, and no example is claimed that was neither.

**RED / hold:**
- e1 after a pass, `make verify VERIFY_FORCE=1` → every check runs, one line says the run was forced *(AC-S33-3)*.
- e2 `CI=1` (and `GITHUB_ACTIONS`, `GITLAB_CI`, each) after a pass → full run, **no stamp read, written or
  removed** (the stamp file's bytes and mtime unchanged, or absent where none existed) *(AC-S33-4)*.
- e3 on the trunk (`main` checked out) → the same: full, no stamp written, none removed *(AC-S33-4)*.

**GREEN** — only what an observed RED demands in `Makefile`; if none, the commit holds the tests alone and the report
names the reason (the script already answers).

**Verify:** as T001. **Files:** `Makefile` (only if a RED demands), `tests/test_factory_gate_stamp.py`.

### T003 — [US1] A slice of the suite is not the gate (R3 · AC-S33-5)

- [ ] **Rule R3.** Follows T002.

**RED** (fails today: `verify` calls the script regardless):
- e1 a pass, then `make verify TESTS=x` (and, separately, `SKIP=x`) → the checks run as before with the named
  tests, and the **stamp file is untouched** (same bytes and mtime), the script never called (its stand-in-wrapped
  copy logs no call); a pass followed by `TESTS` then a plain `make verify` still reuses the earlier stamp.
- e2 with no stamp yet, `make verify TESTS=x` → no stamp written; the next plain `make verify` is a full run.

**GREEN** — root `Makefile`: when `TESTS` or `SKIP` is set, `verify` is `verify-checks` straight (`ifneq`/`$(if)`; no
construct newer than GNU Make 3.81). The script is not called, so nothing reads, writes or removes a stamp (D100).

**Verify:** as T001. **Files:** `Makefile`, `tests/test_factory_gate_stamp.py`.

### T004 — [US1] The tools the suite looks for are in the key (R4 · AC-S33-6)

- [ ] **Rule R4.** Follows T003.

**RED** (fails today: no `--tool` is passed, so a tool appearing changes nothing):
- e1 after a pass, a stand-in `tofu` is put on `PATH` → the next `make verify` is a full run; the pass after that is
  reused.
- e2 after a pass, a stand-in `node` answering another version → full run.
- e3 a tool on the list **missing** from `PATH` (none of the stand-ins present) → the stamp is still written and the
  next run reuses it; `make` changing its version (`--make "$(MAKE)"` answering another one, by a stand-in make
  wrapper) → full run.

**GREEN** — root `Makefile`: `--tool` for each of `python3 git uv node npm go java docker pack tofu gh` that is found
on `PATH` (`$(foreach)`, `$(if)`, `$(shell)`; a missing one is left out, `ask()` cannot ask it, D100; `sh` is not asked)
and `--make "$(MAKE)"`. The list is written once.

**REFACTOR:** the tool list is one variable; the test reads its names from the same words, not a second list.

**Verify:** as T001. **Files:** `Makefile`, `tests/test_factory_gate_stamp.py`.

### T005 — [US1] Nothing else moves (R5 · AC-S33-8, -9) — hold

- [ ] **Rule R5.** Follows T004. A **hold task**: the rule guards what T001–T004 left alone, so no RED is expected
  and each example is **written as a hold and seen to have teeth**; the commit may touch `Makefile` only for the one
  `make help` line if the earlier tasks left it unsaid.
- e1 `make help` lists `verify` with a line saying a tree that already passed is not judged again *(fails today
  if the line is not yet written — then it is a RED with its GREEN, the `## ` help comment on `verify`; teeth by
  deleting it)*.
- e2 no second copy of `verify-stamp.py` or `check-slice-scope.py` exists in the tree, and the `Makefile` names the
  script only at `assets/toolkit/scripts/` *(teeth: copy the script into `scripts/` and see it fail)*.
- e3 the other targets (`lint`, `typecheck`, `check-structure`, `test`) read from `make -n` run exactly the commands
  they ran before, and `.github/workflows/verify.yml` is byte-identical to `adopt-method`'s *(teeth: edit a target;
  AC-S33-9)*.

**Verify:** as T001, then `git diff adopt-method -- . ':!Makefile' ':!tests/test_factory_gate_stamp.py'` is empty
(AC-S33-8: nothing a generated project receives changes). **Files:** `Makefile` (the help line only, if needed),
`tests/test_factory_gate_stamp.py`.

### T006 — Export the patch and prove it applies (host task)

- [ ] **Host task; no story.** In the worktree, `git diff adopt-method...s33-patch -- Makefile
  tests/test_factory_gate_stamp.py > /home/noahc/math/slipwai-graph/specs/001-faster-slipwai/slices/S33-factory-gate-stamp/s33.patch`
  (the patch names only those two paths). Then from `/home/noahc/math/slipwai-graph` on `adopt-method`:
  `git apply --check specs/001-faster-slipwai/slices/S33-factory-gate-stamp/s33.patch` exits 0, **and nothing is
  applied**. Commit the patch alone (it is not a control). The worktree's own gate has run green before export
  (`make lint typecheck check-structure`, `make test TESTS=test_factory_gate_stamp`).

**Files:** `specs/001-faster-slipwai/slices/S33-factory-gate-stamp/s33.patch` (new).

### T007 — BLOCKED: a person applies `s33.patch` (⛔)

- [ ] **Not a delegate's task and not the host's: the root `Makefile` is a control (D99, D101).** A person runs the
  three commands in plan.md's *Summary* (`git apply …/s33.patch`; `make lint typecheck check-structure && make test
  TESTS=test_factory_gate_stamp`; the commit by path). Until then the slice is blocked and the run takes `S05-xdist`;
  the iteration after it lands re-enters at **T008**. No task below starts before this one is ticked.

---

## Phase 2: Gates and closing (host; after T007)

### T008 — Converge (host task)

- [ ] `drive-converge` over the applied diff against the constitution; the verdict goes under `## Convergence`;
  any finding it appends becomes a task under *Phase 4*, in the order found.

### T009 — After-converge gaps pass (host task)

- [ ] `drive-gaps` traces AC-S33-1 … -10 over the applied tree; findings are decisions or tasks under *Phase 4*.

### T010 — Demo (host task)

- [ ] The demo from [quickstart.md](quickstart.md) run by `drive-hand`: the factory's own `make verify` twice on an
  unchanged tree on `adopt-method`, the second **measured** (AC-S33-10; the first took about forty minutes, the second
  must return at once with the reuse line), plus `VERIFY_FORCE=1`, `CI=1` and `TESTS=…` as the actor would type them.
  The measurement is written into the quickstart by the host.

### T011 — Adversary pass (host task)

- [ ] Per the trigger table in `/drive`: this slice's seam is the key and the stamp (a tool changing under it, an
  interrupted run, two `make verify` at once on one stamp). If the table says run, `drive-adversary` attacks it and each
  confirmed finding is a regression test appended as a task; if it says skip, the row says why. Not before T010.

### T012 — Mutation (host task)

- [ ] **N/A**: this repository records no mutation command (`project.json`), as for the slices before it; said in the
  register row, not pretended.

### T013 — The full gate (host task)

- [ ] `make verify` at the root on the tree after T007 — now itself through the stamp, so the **first run is a full
  run** (the tree is new) — green; then `make -f delivery/Makefile verify`, green. A forced run
  (`VERIFY_FORCE=1 make verify`) is the one that stands as the proof if a stamp could have been reused.

### T014 — Register row and benchmark (host task)

- [ ] The slice's row in the register and `benchmark.json` closed, after-acceptance commits riding in this slice's
  own pull request (`AGENTS.md`: one PR per slice).

---

## Parallel opportunities

| Task | Writes | Imports another task's file |
|---|---|---|
| T001 | `Makefile`, `tests/test_factory_gate_stamp.py` (new) | none |
| T002 | `Makefile` (only if a RED demands), `tests/test_factory_gate_stamp.py` | the fixture T001 wrote |
| T003 | `Makefile`, `tests/test_factory_gate_stamp.py` | same |
| T004 | `Makefile`, `tests/test_factory_gate_stamp.py` | same |
| T005 | `Makefile` (help line only, if needed), `tests/test_factory_gate_stamp.py` | same |
| T006 | `s33.patch` | — |

**May run together: nothing.** All five rules write the same two files — one `Makefile` and one test module — so
`[P]` is on no task, and two delegates would be two agents writing one file. T001 to T005 run **one after another in
the one scratch worktree**, one commit each, by a single `drive-implement` delegate (`delegate: story`). T006 follows
T005 (it exports the sum of the five commits). T007 is a person's. T008–T014 run alone, in order, after T007; T010
runs on the tree T007 produced, never beside T013.

## Design review

No screen in this slice

## Convergence

*(to be written by T008)*

## Differences from plan.md

Written for the host to correct the plan; none changes a requirement or a decision.

1. **R2 is expected to be mostly holds.** `standing()` and `VERIFY_FORCE` live in the script, which `verify` calls
   after T001, so R2's examples may pass the moment they are written. T002 therefore observes each first and
   writes each as a hold with its teeth shown, per S04's precedent for holds; it is not a task that instructs a test
   to pass unseen. If every example holds, the host may fold T002 into T001 at no cost.
2. **R5 is one hold task**, as the plan's map allows; its `make help` line may be R1's GREEN or a RED of its own.
3. **T006 and T007 are tasks, not notes.** The plan says the patch is applied by hand; here its export and
   `git apply --check` are the host's task and the application is a blocked task, so the run's order is visible.
