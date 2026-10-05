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

- [x] **Rule R1.** Creates `tests/test_factory_gate_stamp.py` with its fixture (the temporary repository, the
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

- [x] **Rule R2.** Follows T001 (same two files). The script's own `standing()` and `VERIFY_FORCE` carry this
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

- [x] **Rule R3.** Follows T002.

**RED** (fails today: `verify` calls the script regardless):
- e1 a pass, then `make verify TESTS=x` (and, separately, `SKIP=x`) → the checks run as before with the named
  tests, and the **stamp file is untouched** (same bytes and mtime), the script never called (its stand-in-wrapped
  copy logs no call); a pass followed by `TESTS` then a plain `make verify` still reuses the earlier stamp.
- e2 with no stamp yet, `make verify TESTS=x` → no stamp written; the next plain `make verify` is a full run.

**GREEN** — root `Makefile`: when `TESTS` or `SKIP` is set, `verify` is `verify-checks` straight (`ifneq`/`$(if)`; no
construct newer than GNU Make 3.81). The script is not called, so nothing reads, writes or removes a stamp (D100).

**Verify:** as T001. **Files:** `Makefile`, `tests/test_factory_gate_stamp.py`.

### T004 — [US1] The tools the suite looks for are in the key (R4 · AC-S33-6)

- [x] **Rule R4.** Follows T003.

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

- [x] **Rule R5.** Follows T004. A **hold task**: the rule guards what T001–T004 left alone, so no RED is expected
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

- [x] **Host task; no story.** In the worktree, `git diff adopt-method...s33-patch -- Makefile
  tests/test_factory_gate_stamp.py > /home/noahc/math/slipwai-graph/specs/001-faster-slipwai/slices/S33-factory-gate-stamp/s33.patch`
  (the patch names only those two paths). Then from `/home/noahc/math/slipwai-graph` on `adopt-method`:
  `git apply --check specs/001-faster-slipwai/slices/S33-factory-gate-stamp/s33.patch` exits 0, **and nothing is
  applied**. Commit the patch alone (it is not a control). The worktree's own gate has run green before export
  (`make lint typecheck check-structure`, `make test TESTS=test_factory_gate_stamp`).

**Files:** `specs/001-faster-slipwai/slices/S33-factory-gate-stamp/s33.patch` (new).

### T007 — BLOCKED: a person applies `s33.patch` (⛔)

- [x] *(Applied by the owner at `cab6cda`, with the follow-ups `e3bc084` and `e997a5f`; iteration 16 re-enters at T008.)* **Not a delegate's task and not the host's: the root `Makefile` is a control (D99, D101).** A person runs the
  three commands in plan.md's *Summary* (`git apply …/s33.patch`; `make lint typecheck check-structure && make test
  TESTS=test_factory_gate_stamp`; the commit by path). Until then the slice is blocked and the run takes `S05-xdist`;
  the iteration after it lands re-enters at **T008**. No task below starts before this one is ticked.

---

## Phase 2: Gates and closing (host; after T007)

### T008 — Converge (host task)

- [x] *(Two passes, iteration 16: pass 1 not converged — T015 CRITICAL, T016 HIGH, T017 MEDIUM; pass 2 converged — T018, T019 MEDIUM, T020 LOW; all six built into `s33-2.patch`.)* `drive-converge` over the applied diff against the constitution; the verdict goes under `## Convergence`;
  any finding it appends becomes a task under *Phase 4*, in the order found.

### T009 — After-converge gaps pass (host task)

- [x] *(Iteration 18, over `2a8c10c`: seven gaps — T022–T025, D119, D120, and the quickstart's records.)* `drive-gaps` traces AC-S33-1 … -10 over the applied tree; findings are decisions or tasks under *Phase 4*.

### T010 — Demo (host task)

- [ ] *(After T026 is applied. First check the quickstart's precondition — no worktree inside the checkout, a clean `git status`, nothing writing the tree — and record that it held (D120); a fresh checkout's first run changes the cache list, so measure the run after the one that wrote it.)* The demo from [quickstart.md](quickstart.md) run by `drive-hand`: the factory's own `make verify` twice on an
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

## Phase 4: Converge findings (pass 1)

The root `Makefile` is still a control (D99, D101). A task below that changes it goes the way T001–T007 did: a
scratch worktree, an exported patch, then a person applies it. A task that changes only `tests/` does not.

### T015 — CRITICAL: an environment variable that narrows the suite is neither keyed nor a bypass (Principle I; owner priority 5)

- [x] *(In `s33-2.patch`; applied by the owner at `d92f908`, D113.)* `tests/support.py:31` reads `FACTORY_BACKENDS` and cuts the matrix down (`FACTORY_BACKENDS=python` → 1 backend
  out of 5). `.github/workflows/verify.yml:57` calls it, beside `TESTS`/`SKIP`, *how a slice is named*. The key
  holds only the script's `VARIABLES` (`verify-stamp.py:115`). Root `Makefile:46` bypasses the stamp for `TESTS` and
  `SKIP` and nothing else. **Evidence:** `key_parts()` over this tree gives `646104d6449f41a4` both with and without
  `FACTORY_BACKENDS=python` (and with `IMAGE_REGISTRY=x/`). In a scratch fixture built from
  `GateCase`, `FACTORY_BACKENDS=python make verify` after a pass printed the reuse line and started no check. Turn
  that round and you have the false green: `FACTORY_BACKENDS=python make verify` records a stamp, and a later plain
  `make verify` reuses it, so four backends' generated gates never run locally. That is a check removed to make the
  loop faster (constitution I, line 33), and it is a false green, which priority 5 rules out. **Close the class, not
  the instance:** (a) root `Makefile` (a person, by patch): every variable that narrows or redirects what the suite
  runs bypasses the stamp the way `TESTS`/`SKIP` do, starting with `FACTORY_BACKENDS` in the `ifneq` at line 46.
  (b) `tests/test_factory_gate_stamp.py`: one example that collects every name `tests/*.py` reads from the
  environment (`os.environ.get(...)`, `os.environ[...]`, `getenv(...)`) and fails on a name missing from a table
  in the test. The table says *bypasses* (each such name gets an example: the checks run straight, the stamp's
  bytes and mtime are unchanged, and the fixture's `gate()` strips it) or *does not change what the suite runs*,
  with the reason (`PATH`, and the variables a test sets for its own child: `STANDIN_LOG`, `FAKE_CODEGRAPH_LOG`…).
  `IMAGE_REGISTRY` and `PACK_FLAGS` (`tests/test_images.py:118`, `tests/test_launcher.py:54`) are decided in that
  table, not left out of it. Show the example's teeth by deleting `FACTORY_BACKENDS` from the bypass.

### T016 — HIGH: tools whose presence changes what the suite runs are missing from `VERIFY_TOOLS` (AC-S33-6's class)

- [x] *(In `s33-2.patch`; applied by the owner at `d92f908`, D113.)* `VERIFY_TOOLS` (`Makefile:42`) is a list someone wrote by hand. The suite looks for more than it holds:
  `ko` (`tests/test_images.py:61,179` skip the Go image without it); `mvn` (`tests/test_wrappers.py:103` asserts
  only when `mvn` is absent); the Docker Compose plugin (`tests/test_postgres.py:208-211` skips without
  `docker compose version`, and `docker --version` stays the same when the plugin is installed). Install `ko`
  after a pass and the next `make verify` reuses the stamp over an image test that never ran. **Close the class:**
  (a) `tests/test_factory_gate_stamp.py`: one example that collects every tool name the suite probes, from the
  `shutil.which("<name>")` literals, the `NEEDS`-style maps and the `for tool in (...)` loops in `tests/*.py`, and
  fails on a name that is neither in `VERIFY_TOOLS` (read from the Makefile, as `listed()` does) nor on a written
  exemption list with its reason. Seed the list with `sh` (D100) and the names that only build a stand-in `PATH`
  (`dirname`). Its teeth: drop `ko` from the list. (b) root `Makefile` (a person, by patch): `ko` and `mvn` join
  `VERIFY_TOOLS`. (c) The Compose plugin cannot be a `--tool`, because the script asks `<tool> --version` and
  nothing else. That is a product question for the host: key it some other way, or name it in the spec's *Not keyed,
  and said so* sentence beside the npm registry. The delegate does not choose. **Decided (D112): keyed through `.factory-work/verify-probes`, written by the
  root recipe from `docker compose version` (or `absent`) before `token`; the probed-tools table records it as *keyed
  through the probe file*.**

### T017 — MEDIUM: clauses of AC-S33-6 and the root recipe's make-flag paths have no example (AC-S33-10)

- [x] *(In `s33-2.patch`; applied by the owner at `d92f908`, D113.)* `tests/test_factory_gate_stamp.py` has no example of a listed tool **leaving** `PATH`. Its "one missing, still
  written and reused" example (`:226`) holds only on a machine where some listed tool really is missing. Nothing
  runs the root recipe under `-i`, `-n`, `-q` or `-k`, although its exit handling (`Makefile:49`, the
  `rc -eq 1` silence) is its own and not the generated one. In a scratch `GateCase` probe each one already behaves:
  a tool leaving gives a full run; `-i` with a failing check exits 0, writes no stamp and the next run is full; `-n`
  starts no check and leaves the stamp's bytes alone; `-q` exits 1 and says nothing; `-k` with a failing check exits
  2, names the failure and writes no stamp. So these are holds. Write each one as a hold and show its teeth. For
  "missing", build the `PATH` so at least one listed tool is certainly absent instead of depending on the host.
  Tests only. No Makefile change.

### Converge pass 2: what pass 1's fix (`s33-fix`, `s33-2.patch`) still owes

Pass 2 found no CRITICAL or HIGH. T015's bypass, T016's `ko`/`mvn`/probe file and T017's holds close what they name.
The three tasks below are what is left. None of them re-opens the loop.

### T018 — MEDIUM: AC-S33-12 e3 keys the probe file as an untracked file, never through `tree_records`/`EXEMPT`

- [x] *(In `s33-2.patch`; applied by the owner at `d92f908`, D113.)* `GateCase` writes the fixture's `.gitignore` as `__pycache__/` only (`tests/test_factory_gate_stamp.py:59`). So in
  the fixture `.factory-work/verify-probes` is untracked and *not* ignored. `covered_files` lists it, and it is keyed
  as a file. The real tree takes a different route: `.gitignore:4` ignores it, and it reaches the key only through
  `tree_records` and `exempt_entry` (`assets/toolkit/scripts/verify-stamp.py:334`, `:57`). That route is the one D112
  rests on, and it is D112's own *would reverse if*. **Evidence:** with `(".factory-work/", CACHE, ())` added to
  `EXEMPT`, `test_the_plugin_arriving_puts_the_next_run_in_full_and_the_run_after_reuses` still passes (restored).
  The real tree is correct today. In a `/tmp` clone of `s33-fix`, `git check-ignore` names `.gitignore:4`, and
  `key_parts()`'s `ignored` digest moves from `122e0a182a1e` (`absent`) to `d9a3de6e3723` (a Compose version line)
  and stays put after a `touch` of a different mtime. So the behaviour holds and only its guard is missing.
  **Do:** in `tests/` only, make the example run the real route. Either the fixture's `.gitignore` gains
  `.factory-work/` for this example, or a second example asserts that the root `.gitignore` ignores the path and
  that `exempt_entry(".factory-work/verify-probes")` is `None`. Show the teeth with the same `EXEMPT` mutation.

### T019 — MEDIUM: the two scanners see only literal forms, and one live probe gets past them

- [x] *(In `s33-2.patch`; applied by the owner at `d92f908`, D113.)* `reads()` and `probed()` (`tests/test_factory_gate_stamp_inputs.py:62`, `:113`) do catch a new
  `os.environ.get("X")`, `os.environ.get("X", d)`, `shutil.which("y")` and a `NEEDS` map entry. Each was proven
  with a throwaway `tests/test_zz_mut.py` that made e1 fail, then removed. They pass over the following forms, and
  e1 stays green with each one added: `"X" in os.environ`; `os.environ.setdefault("X", …)`; `os.environ.get(NAME)`
  where `NAME` is a constant; `shutil.which(TOOL)` where `TOOL` is a constant; `subprocess.run(["y", "--version"])`
  as a probe for any tool but `docker compose`; `os.access(dir / "y", os.X_OK)`. The tree already has one live case
  of the last form. `tests/test_extensions.py:209-212` skips its test when `codegraph` or `npx` shares a
  directory with `sh`. Neither name is in `VERIFY_TOOLS`, in `EXEMPT_TOOLS` or in `probed()`. Here `npx` is
  `/usr/bin/npx`, so the test always skips on this machine. The false-green direction needs `npx` to leave `sh`'s
  directory while `npm --version` (keyed) answers the same. That is rare, which is why this is MEDIUM. **Do:**
  in `tests/` only, either extend both scanners to these forms or make them fail on any non-literal argument
  to a getter or `which`/`os.access`. Then put `codegraph` and `npx` in the tools table, keyed or with a reason.
  Show the teeth with one added line per form.

### T020 — LOW: the probe file is written under `make -n` and `make -q`

- [x] *(In `s33-2.patch`; applied by the owner at `d92f908`, D113.)* The stamped branch is one recipe line that contains `$(MAKE)`, so GNU make runs it under `-n` and `-q`. In a
  `/tmp` clone, `make -n verify` (exit 0) and `make -q verify` (exit 1) each wrote `.factory-work/verify-probes`
  where there was none. The bypass branch wrote nothing. What gets written is the probe's true answer, to an ignored
  file, and the stamp is untouched (T017's `-n` hold). So no stamp can go wrong. The problem is that a dry run writes a
  file. **Do:** say so in the `Makefile` comment above `VERIFY_STAMP_SCRIPT` (a person, by patch), or accept it in
  the convergence note. No test is owed.

### T021 — The converge probe left bytecode in the toolkit (the owner's note, D118)

- [x] *(Iteration 18: `tests/test_assets_bytecode.py`; `tests/test_mutation.py`.)* The factory gate went red after
  `d92f908` for one reason: `assets/toolkit/scripts/__pycache__/verify-stamp.cpython-314.pyc`, which `test_toolkit`
  reads as text and fails on. It was written at 00:27:31Z in iteration 16 by T008's first converge pass. To read the
  key, that pass typed a `python3 -c` that loaded `assets/toolkit/scripts/verify-stamp.py` through
  `importlib.util.spec_from_file_location` with bytecode writing on. No test in the suite did it; the owner deleted the
  file. **Done:** `tests/test_assets_bytecode.py` holds three things. The toolkit tree has no `__pycache__` or `.pyc`,
  and the failure says what made one and what to do. Every test module that loads a script and names an asset tree
  in its code turns `sys.dont_write_bytecode` on. And the scan flags the probe as it was typed, and passes it with the
  switch on. Teeth shown: a `.pyc` planted under `assets/toolkit/scripts/__pycache__/` fails the first, and the
  pre-fix `tests/test_mutation.py` fails the second. That module was the one other loader in the class: it left
  `assets/languages/go/scripts/__pycache__/` on every run, and it now turns the switch on around its load. A probe
  that imports a script under `assets/` by hand runs as `python3 -B`; every brief this run writes for a delegate
  that may probe says so. `tests/` only, so it reaches no user and raises no number.

## Phase 4: After-converge gaps (T009, iteration 18)

`drive-gaps` traced AC-S33-1 … -12 over `2a8c10c`. Every criterion is met except AC-S33-10, which is the demo's
measurement (T010). Its HIGH (caches under `assets/` are exempt from the key but read by the suite) and one MEDIUM
(an agent worktree under `.claude/worktrees/` stops every stamp) are product questions, D119 and D120. The rest
change `tests/` only and are below, in the order found.

### T022 — MEDIUM: a `FACTORY_BACKENDS` that names no backend takes the stamped path over an empty matrix

- [x] *(Iteration 18, `f35f981`.)* `FACTORY_BACKENDS=" "` (or `","`) is empty to make's `$(strip …)`, so `Makefile:51` does not bypass; but
  `tests/support.py:31-38` reads it as a value and `backends_under_test()` returns `[]`. The matrix,
  `test_flag_gate` and `test_line_widths` then pass over zero backends, a stamp is recorded, and a later plain run
  reuses it. **Do (`tests/` only):** `backends_under_test()` raises when the value is set and names no backend,
  as its docstring already says a silently empty slice is an error; an example in
  `tests/test_factory_gate_stamp_inputs.py`, observed failing first.

### T023 — LOW: what the inputs scan cannot see — `TMPDIR`, and what `src/slipwai` reads inside the suite

- [x] *(Iteration 18, `d69f345`.)* `tests/test_uncommitted_places.py:142,180` skip when the temporary directory sits inside a git repository, so
  `TMPDIR` decides whether two tests run, and the table does not hold it. `src/slipwai` reads `GITEA_OWNER`,
  `GITEA_PAGES_URL` and `GITEA_TOKEN` in the suite's own process, and the scan reads only `tests/*.py`. **Do
  (`tests/` only):** make the two tests independent of where `TMPDIR` is (recommended: `GIT_CEILING_DIRECTORIES`
  in the probe's and the child's environment, so git cannot see above the copy, and the skip goes); extend the scan
  to `src/slipwai/**/*.py` and decide each name it finds in the tables, with its reason.

### T024 — LOW: `go` and `gh` are named by AC-S33-6 and held by nothing

- [x] *(Iteration 18, `f326372`.)* `listed()` asserts only `tofu` and `node`; `tests/test_factory_gate_stamp_inputs.py:131` asserts `ko`, `mvn`,
  `pack`, `java`, `docker`. Dropping `go` from `VERIFY_TOOLS` leaves every test green. **Do (`tests/` only):**
  assert AC-S33-6's whole list, with `ko` and `mvn`, is a subset of `listed()`; teeth shown by dropping `go`.

### T025 — LOW: `npx`'s directory decides a skip, and the key holds only its version

- [x] *(Iteration 18, `d26bb55`.)* `tests/test_extensions.py:209-212` skips according to whether `npx` shares a directory with `sh` (T019's
  leftover). **Do (`tests/` only):** write its reason into the tables in
  `tests/test_factory_gate_stamp_inputs.py` (a decided entry), or make the test hide `npx` without depending on
  its directory; whichever, the scan must know of it.

### T026 — HIGH (D119): interpreter caches under `assets/` are exempt from the key, and the suite fails on them — BLOCKED on a person (⛔)

- [ ] *(Built in iteration 18 as `s33-3.patch` — branch `s33-patch-3`, `aa46146`; `git apply --check` clean against `adopt-method`; RED observed (the run after the plant reused), teeth shown; the probe line writes a line unique to the run where `sort` is missing, held by its own example, and the AC-S33-6 hold's stand-in PATH carries `find` and `sort`, both decided in the tools table. ⛔ until a person applies it.)* `verify-stamp.py`'s `EXEMPT` skips `__pycache__/` and `*.pyc` at the factory root too, while `test_toolkit`
  reads the toolkit and profile overlays as text and `test_assets_bytecode` fails on a toolkit cache: in a /tmp clone
  `key_parts()` was the same before and after planting `assets/toolkit/scripts/__pycache__/verify-stamp.cpython-314.pyc`,
  so D118's incident over a stamped tree would have printed the reuse line. **Do (AC-S33-13):** in the stamped branch
  only, the root `Makefile`'s probe line appends `find assets \( -name __pycache__ -o -name '*.pyc' -o -name '*.pyo' \)
  2>/dev/null | LC_ALL=C sort` to `.factory-work/verify-probes`, after the Compose answer; the script is unchanged.
  `tests/test_factory_gate_stamp.py` gains the example on `GateCase` — after a pass, a planted `.pyc` under the
  fixture's `assets/toolkit/scripts/__pycache__/` makes the next run full and the one after it a reuse — observed
  failing first, teeth shown by taking the `find` out. Built in a scratch worktree, exported as `s33-3.patch`,
  `git apply --check`ed against `adopt-method`; **a person applies it** (D99, D101, D113).

### T027 — The quickstart's precondition and the general question (D120)

- [x] *(Iteration 18.)* `quickstart.md` states the precondition before step 1 and names all three patches, `CI=1`
  and `FACTORY_BACKENDS`; `story-split.md` carries a Parking Lot line on a harness's worktree directory and the stamp,
  after `S32-verify-stamp-split`; `cruise-carry.md`'s lesson gains no `isolation: worktree` delegate while S33's
  measurement or demo is pending. No code.

## Convergence

**Verdict (T008, iteration 16): converged at the bound of two passes** — `drive-converge` · model: host (claude-opus-5-5) · delegated, fresh context, twice.

Pass 1, over `cab6cda~1..e997a5f`, was not converged. It found one CRITICAL and one HIGH, both places where a stamp
could stand over a run that skipped work (owner priority 5). `FACTORY_BACKENDS` narrows the suite and was neither
keyed nor a bypass (T015, reproduced by the host: `tests/support.py:31`). `ko`, `mvn` and the Compose plugin change
what the suite runs and were unkeyed (T016; D112 keys Compose through `.factory-work/verify-probes`). Pass 2, over the
scratch branch that fixed them, converged: each class closed with its teeth shown, and what was left (T018, T019
MEDIUM; T020 LOW) was built before the patch went to a person rather than left for a third round. Principles the diff
touches: **I** (line 33, a memoised gate is additive) — `Makefile` bypass line and `VERIFY_TOOLS` in `s33-2.patch`,
held by `tests/test_factory_gate_stamp_inputs.py` and `tests/test_factory_gate_stamp_scan.py`; the trunk and CI never
read a stamp (`assets/toolkit/scripts/verify-stamp.py`, unchanged); **V** — every example observed failing, or a
hold shown to have teeth; **VIII** — no bump, the root `Makefile` and `tests/` reach no user. **The slice is ⛔ on a
person again (D113)**: `s33-2.patch` changes the root `Makefile`, a control. T009 onwards run on the tree it
produces. *(The owner applied it at `d92f908`; T021, the owner's note on a converge probe's bytecode, followed in
iteration 18.)*

## Differences from plan.md

Written for the host to correct the plan; none changes a requirement or a decision.

1. **R2 is expected to be mostly holds.** `standing()` and `VERIFY_FORCE` live in the script, which `verify` calls
   after T001, so R2's examples may pass the moment they are written. T002 therefore observes each first and
   writes each as a hold with its teeth shown, per S04's precedent for holds; it is not a task that instructs a test
   to pass unseen. If every example holds, the host may fold T002 into T001 at no cost.
2. **R5 is one hold task**, as the plan's map allows; its `make help` line may be R1's GREEN or a RED of its own.
3. **T006 and T007 are tasks, not notes.** The plan says the patch is applied by hand; here its export and
   `git apply --check` are the host's task and the application is a blocked task, so the run's order is visible.
