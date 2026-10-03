# Tasks: S00-run-path — prove the run path and establish a green gate

**Input**: [plan.md](plan.md) (*Phases of work* is the order kept here), [research.md](research.md) R1–R9,
[data-model.md](data-model.md), [quickstart.md](quickstart.md); acceptance criteria AC-S00-1 … AC-S00-7 in
`specs/001-faster-slipwai/spec.md` under `### S00-run-path` (no `examples.md`: a method slice with no screen and
no event model). Decisions D11, D12, D13 in `specs/001-faster-slipwai/decisions.md`.

**Branch**: `adopt-method` on top of `5460bf9` (D12). No `slice/` branch, no push, no claim.

**Delegation** (`.specify/drive.json`: `delegate: story`, `cycle: rule`): these tasks carry no user-story tag,
so they are delegated **per rule**, one delegate per task, each its own commit. There is one rule in this
slice (T001); T002 and T003 are records of a run, not rules.

**Constraints that hold for every task** (plan.md *Constraints*, AC-S00-7): nothing under `assets/`,
`src/slipwai/`, `catalog.json`, the CLI, `VERSION` or `changelog.d/` changes; nothing under `delivery/scripts/`,
`tools/`, the `Makefile`, CI or hook settings changes; no test is quarantined, skipped or moved;
`make ratchet-tighten` is never run; `cruise.py` is not edited (the fix is in the tests, R2).

## Format: `[ID] [P?] Description` — each task is one increment, one commit

No `[P]` appears: see *Parallel opportunities*.

---

## Phase 1: Implementation stage

### T001 — The test child environment no longer inherits the runner's marks (AC-S00-3, AC-S00-4)

- [x] **Done** — `e12ca58` (drive-implement · model: sonnet · delegated, fresh context · rule/rule · split=0) and
  `030ad00` (host: two lines wrapped after `make verify` went red at lint, E501). RED observed before the change
  as assertion failures: the new example
  `test_a_test_child_never_inherits_the_marks_of_a_run_the_test_is_itself_running_under` failed because the child
  took the driven path (*started this session as iteration 2*) instead of printing `UNREAD`; the six tests of
  R2 red with the marks present (1 error, 5 failures, one shared refusal). GREEN: helper `outside_a_run()` in
  `tests/test_cruise_runner.py`, five sites routed through it; 44 cruise tests green with the marks and without.

**Rule:** a test that spawns `scripts/agents/cruise.py`, or drives it in-process, never lets the child see
`CRUISE_RUNNER` or `CRUISE_ITERATION` unless the test sets them itself (data-model.md, *Test child
environment*; research.md R2, R3). This is **one rule, one increment**: the five sites in R3 are one rule and
each, taken alone, would be a proof over behaviour another site already produced, so they are not cut into
tasks and the test is not scheduled apart from the change.

**RED** (observe before any production edit; with `CRUISE_RUNNER=1 CRUISE_ITERATION=2` in the parent):
- Add one new example to `tests/test_cruise_runner.py` asserting that `cruise(repo, "loop")`, run while the
  parent environment carries both marks, prints the *nobody is reading* line (the constant `UNREAD`, already
  imported by `tests/test_cruise_stop_hook.py`). It fails today with the iteration refusal (*this session is
  iteration 2 of a run already under way*).
- Run the existing `test_cruise*` modules with the marks set and observe the six red tests of R2 red for the
  same stated reason: one error in `test_cruise_start`, and failures in `test_cruise_index`,
  `test_cruise_start`, `test_cruise_watch` (two) and `test_cruise_where`
  (`CRUISE_RUNNER=1 CRUISE_ITERATION=2 make test TESTS="…"`, command in quickstart.md, AC-S00-3).

**GREEN** — every site, in one change (R3):
1. `tests/test_cruise_runner.py` — add the helper, e.g. `outside_a_run(env: dict | None = None) -> dict[str, str]`
   (parent environment without the two marks, plus the overrides applied last); `cruise()` (lines 43–45) calls it.
2. `tests/test_cruise_stop_hook.py` — `hook()` (lines 28–31) calls the shared helper instead of its own copy.
3. `tests/test_cruise_tell.py` — the `run` `Popen` (lines 146–148) takes its `env` from the helper.
4. `tests/test_cruise_watch.py` — the `watch --minutes 1` run (lines 166–167) takes its `env` from the helper.
5. `tests/test_cruise_start.py` — the two in-process calls (lines 282 and 292) become
   `mock.patch.dict(module.os.environ, outside_a_run(env), clear=True)`; arguments change, no mocking
   framework is added.

**Must keep (AC-S00-4):** `tests/test_cruise_start.py:174`
(`test_a_typed_cruise_starts_the_runner_detached_and_a_person_stops_it_from_anywhere`) still passes by setting
the two variables itself; overrides win because they are applied last. Do not weaken it.

**REFACTOR:** only if the five call sites leave a duplicate; the helper is the one place the two names appear.

**Verify:** `CRUISE_RUNNER=1 CRUISE_ITERATION=2 make test TESTS="<the eleven test_cruise modules in quickstart.md>"`
is green, then the same with both variables unset is green. Commit.

**Files:** `tests/test_cruise_runner.py`, `tests/test_cruise_stop_hook.py`, `tests/test_cruise_tell.py`,
`tests/test_cruise_watch.py`, `tests/test_cruise_start.py`.

### T002 — Record the run path in `delivery/survey/running.md` (AC-S00-1, AC-S00-2)

- [x] **Done** — `fdb9956` (host). `./slipwai --version` → `slipwai 1.5.2.dev0`, exit 0, on Python 3.14.4;
  `grep -c "Not yet proven" delivery/survey/running.md` → 0.

**No test, deliberately.** This is a record of a run, not behaviour: there is no code whose RED could precede
it, and a test written for it would pass the moment it was written. The proof is the run itself and the grep
in quickstart.md.

- Run `./slipwai --version` and `python3 --version`; the first must exit 0 and print `slipwai ` followed by the
  contents of `VERSION` (AC-S00-1: name `VERSION`, not the literal).
- Replace the `## . (python)` section's *Not yet proven* with the fields of data-model.md, *Run-path record*:
  command `./slipwai --version`; the exact line it printed; the interpreter from `python3 --version` (floor
  `>=3.11`); no port, seed or backing service; cannot run on: *not tested* (recorded as such, never guessed);
  proved by cruise iteration 2, date of the run.
- Check: `grep -c "Not yet proven" delivery/survey/running.md` prints `0`. Commit.

**Files:** `delivery/survey/running.md`.

### T003 — Both gates with the marks set; record `delivery/baseline.json` (AC-S00-5)

- [x] **Done** — host, at commit `030ad00`, environment `CRUISE_RUNNER=1 CRUISE_ITERATION=2`. First attempt at
  `fdb9956` went red at lint (E501 ×2 from T001) → `030ad00` → rerun. Evidence under `## Convergence`.
  **No `delivery/baseline.json` was written and none is committed:** `delivery/scripts/ratchet.py` lines 205–212
  record nothing when the command exits 0 and no entry exists — a clean first run leaves no file — so lint,
  typecheck and test were all clean, and "no `test` quarantine" holds with no file at all.

**No test, deliberately.** The gates are the check; this task runs them and commits what the first delivery-gate
run records. **Order is fixed after T001 and T002** (research.md R4): a red `test` with no baseline stops the
ratchet and records nothing, so the test fix lands first.

1. `CRUISE_RUNNER=1 CRUISE_ITERATION=2 make verify` — exit 0.
2. `CRUISE_RUNNER=1 CRUISE_ITERATION=2 make -f delivery/Makefile verify` — exit 0. This is the first run of the
   ratchet here: `lint` and `typecheck` record their findings as they are (not fixed in this slice), `test`
   records `{"exit": 0, "findings": []}`.
3. Read the ratchet lines: `test` is green and not `QUARANTINED`; `delivery/baseline.json` holds no `test`
   quarantine. Do not run `make ratchet-tighten`.
4. Record the unittest `Ran N tests … OK (skipped=K)` line from each gate run, and compare its `skipped=` with
   the line of the pre-slice baseline run in `/tmp/full-tests-baseline.log` (its summary line was not yet
   written when this file was derived; read it from the log, R9). `K` must be no higher than the baseline's.
   Write the comparison, both commands, the commit they ran on and the environment under `## Convergence`
   (data-model.md, *Gate evidence*).
5. Commit `delivery/baseline.json`.

A red gate here is not repaired in the gate: stop and report.

**Files:** `delivery/baseline.json` (new), `specs/001-faster-slipwai/slices/S00-run-path/tasks.md`
(the evidence under `## Convergence`).

---

## Phase 2: Convergence stage — run only AFTER the converge verdict and the after-converge gaps pass, BEFORE the demo

> **Do not start these in the implementation stage.** They move the map and bring principle V into force;
> they are written by the Convergence stage (`delivery/commands/drive.md`, stage 9: *hold the map to what the
> slice did … a rung this slice reached flips its row*), once the converge verdict is in and `/gaps` has traced
> the promise — and before the demo, so the hand can check AC-S00-6. (Corrected by the host: the plan's step 4
> and the first draft of this heading said *after acceptance*; the ladder's stage order is converge → gaps → map
> → demo.) Both gates must already be green with exit 0 (T003) — the transition
> `tests-exist → tests-pass` is made only after both gate-evidence rows exist (data-model.md). Neither task has
> a test; each is a record, and the check named is the tree's own (`check-convergence`, `check-constitution`).

### T004 — Move the Safety net row and bring principle V into force (AC-S00-6; D11, R5, R6)

One commit:
- `project.json`, `convergence[]`, axis `safety-net`: rung `tests-pass`, provenance `confirmed`, `planned`
  null, target unchanged (`mutation-measured`), `evidence` naming the two commands, the commit they were green
  on, and *established by cruise iteration 2; no person has read the gate*.
- `.specify/memory/constitution.md`: principle V's preamble and `<!-- journey: … at tests-exist -->` marker
  come out, its quoted text becomes the principle, the two *what holds here* bullets fold into the first
  paragraph as history; principle XIII's marker moves to `at tests-pass` and its *stands at* sentence follows.
  No new principle is written (R6).

**Files:** `project.json`, `.specify/memory/constitution.md`.

### T005 — Redraw the page and check the tree agrees (AC-S00-6; R5)

- On a clean tree (`git status --porcelain` empty; it refuses otherwise): `./slipwai adopt --refresh`.
- Read its report (Refreshed / Disagrees / Not wrapped) before committing. A *Disagrees* line on the Safety
  net row means D11's reading was wrong: stop, the row goes back (D11, *Would reverse if*). Read every file it
  rewrote; none may be a control the runner watches (`delivery/scripts/`, `tools/`, `Makefile`, CI, hooks).
- Commit what it regenerated (expected: `delivery/docs/convergence.md` and the other files R5 lists).
- `make -f delivery/Makefile check-convergence` and `make -f delivery/Makefile check-constitution` green;
  `grep -n "Safety net" delivery/docs/convergence.md` shows `tests-pass` … `confirmed`.
- `make ratchet-tighten` is **not** run.

**Files:** `delivery/docs/convergence.md`, and whatever else `./slipwai adopt --refresh` regenerates
(`delivery/commands/ground.md`, `delivery/commands/strangle.md`, `delivery/docs/change-strategy.md`,
`delivery/survey/structure.md`, and `project.json` where a `detected` fact moved — the generated pages are never
edited by hand; `project.json`'s row is T004's deliberate edit, which `AGENTS.md` permits).

---

## Phase 3: Final check

### T006 — Nothing user-visible changed (AC-S00-7)

Run `git diff --stat 5460bf9..HEAD -- assets src/slipwai catalog.json VERSION changelog.d`: the output is
empty. Run it as the last task, after T005 (and once at the end of the implementation stage, which it passes
without T004 and T005). A non-empty diff is a defect to report, not to repair here. No file is written.

**Files:** none.

---

## Dependencies & Execution Order

T001 → T002 → T003 → (converge verdict, gaps pass) → T004 → T005 → (demo) → T006. T003 needs T001 (R4: the ratchet's
first run needs a green `test`) and T002 only by plan order. T004 needs T003's gate evidence; T005 needs T004
committed (a clean tree) and needs the row already moved.

## Parallel opportunities

None; no task is marked `[P]`. The tasks are sequential by the plan's order and by data: T001 edits five test
files and every later task runs the suite T001 repairs; T002's file is disjoint from T001's but T003 reads both
and the plan fixes the order (one commit per increment on one branch, `adopt-method`); T003 writes
`delivery/baseline.json` and the `## Convergence` evidence; T004 and T005 write `project.json` and
`delivery/docs/convergence.md`, and T005 refuses an unclean tree, so it cannot run beside T004 or anything
else that dirties the checkout. The gates in T003 and T005 read the whole tree, so any concurrent edit would
change what they measure. One delegate at a time.

## Design review

No screen in this slice

## Converge pass 1 — appended tasks

Verdict: **converged** for the implementation stage (T001–T003); no `CRITICAL` or `HIGH`. Evidence under
*Converge pass 1 — evidence* below. These tasks are what the slice still owes before it is called done; none
re-opens the loop.

### T007 — The convergence commit carries the slice's intent (constitution XIV) · **MEDIUM**

The three commits `e12ca58`, `fdb9956`, `030ad00` carry no intent artifact: `specs/001-faster-slipwai/spec.md`
(AC-S00-1 … 7), `decisions.md` (D11–D13), `story-split.md` and the whole of
`specs/001-faster-slipwai/slices/S00-run-path/` are uncommitted in the working tree (`git status` at this pass).
XIV is in force: *every change MUST carry its intent as versioned artifacts delivered in the same commit as the
code*. The ladder's convergence commit (T004) is the commit that can still satisfy it for this slice: it MUST
add `specs/001-faster-slipwai/` (spec, decisions, story-split, the slice directory) alongside `project.json`
and the constitution, and the register row's *Merged as* MUST name a range that includes it. Not `HIGH`
because the artifacts exist and the ladder has a commit scheduled that can carry them; `HIGH` if T004 lands
without them.

**Files:** none new — the T004 commit's contents.

### T008 — `running.md` names a test count that T001 already moved · **LOW**

`delivery/survey/running.md:25–26` says *exercised by the test suite (`make test`, 829 tests)*. The suite has
830 tests since `e12ca58` (tasks.md, *Gate evidence*). The record is true of `5460bf9`, which its first line
names, but the count will drift with every slice and a run-path record is not where the suite's size lives.
Drop the number or pin it in words to the commit (*829 at `5460bf9`*). Data-model's *Run-path record* names
no such field, so AC-S00-2 is unaffected either way.

**Files:** `delivery/survey/running.md`.

### T009 — The new example restores `os.environ` by hand · **LOW**

`tests/test_cruise_runner.py:78–91` sets the two marks with `os.environ.update(marks)` and restores them in a
`try/finally` of its own. `mock.patch.dict(os.environ, marks)` is already how this tree does exactly that
(`tests/test_cruise_start.py:282`, `tests/test_event_model.py:70`), and it restores on every exit path without
the eight lines. A REFACTOR-step leftover, not a behaviour defect: the test is green and discriminates (see
evidence). Fold it when the file is next touched; do not open a cycle for it.

**Files:** `tests/test_cruise_runner.py`.

### Converge pass 1 — evidence

- **AC-S00-3 (marks set):** `CRUISE_RUNNER=1 CRUISE_ITERATION=2 make test TESTS="<the eleven modules>"` at
  `030ad00` → `Ran 44 tests in 32.687s` · `OK`, exit 0 (`/tmp/converge-s00-marks.log`).
- **Marks unset:** `env -u CRUISE_RUNNER -u CRUISE_ITERATION make test TESTS="…"` → `Ran 44 tests in 32.630s` ·
  `OK`, exit 0 (`/tmp/converge-s00-nomarks.log`).
- **The helper has teeth (T001's RED claim re-observed):** `outside_a_run` mutated to
  `return {**os.environ, **(env or {})}` (the pre-slice shape), marks set, `test_cruise_runner test_cruise_start
  test_cruise_index test_cruise_watch test_cruise_where` → `Ran 20 tests` · `FAILED (failures=6, errors=1)`:
  the new example `test_a_test_child_never_inherits_the_marks_of_a_run_the_test_is_itself_running_under` red,
  plus exactly the six R2 named (`test_cruise_start` ×2 incl. the error, `test_cruise_index`,
  `test_cruise_watch` ×2, `test_cruise_where`), the refusal *iteration 2 of a run already under way* in the
  log five times (`/tmp/converge-s00-mutant.log`). File restored with `git checkout -- tests/test_cruise_runner.py`;
  `git diff --quiet -- tests/` clean.
- **AC-S00-4:** `tests/test_cruise_start.py:174` passes the marks itself (`env={**env, "CRUISE_RUNNER": "1",
  "CRUISE_ITERATION": "5"}`) and is green in both runs above; under the mutant it is red — the refusal it
  proves is still the script's and still reachable only when a test asks for it.
- **Spawn-site sweep:** `grep -n "os.environ" tests/*.py` and `grep -n "scripts/agents/cruise.py" tests/*.py`:
  every site that hands `scripts/agents/cruise.py` an environment goes through `outside_a_run` —
  `test_cruise_runner.py:53`, `test_cruise_stop_hook.py:28`, `test_cruise_tell.py:145`,
  `test_cruise_watch.py:165`, and the in-process `test_cruise_start.py:282, 292` (`clear=True`). The remaining
  hits are docstrings, hook-config strings, Makefile-text assertions, and fake-harness shell lines that run
  *inside* a child `cruise()` already cleaned. No site missed.
- **AC-S00-2:** `delivery/survey/running.md:12–26` carries every *Run-path record* field: command (:15),
  printed line + exit (:17), interpreter + floor (:19, CI `3.11` confirmed at
  `.github/workflows/verify-delivery.yml:18,29`), port/seed/service none (:22), cannot-run-on *not tested* (:23),
  proved-by + date (:12). `grep -c "Not yet proven"` → 0. `make -f delivery/Makefile smoke` runs the same line
  (`delivery/Makefile:98–99`).
- **AC-S00-1:** `./slipwai --version` → `slipwai 1.5.2.dev0`, exit 0; `VERSION` reads `1.5.2.dev0`.
- **AC-S00-7:** `git diff --stat 5460bf9..HEAD -- assets src/slipwai catalog.json VERSION changelog.d` → empty.
- **Not run here, by the brief:** `make verify`, `make -f delivery/Makefile verify` (green at `030ad00`, table
  below). T004–T006 are the Convergence stage's and the final check's, not gaps.

## Convergence

### Gate evidence (T003, implementation stage)

| Gate | Commit | Environment | Exit | Suite summary | Ratchet |
|---|---|---|---|---|---|
| `make verify` | `030ad00` | `CRUISE_RUNNER=1 CRUISE_ITERATION=2` | 0 | `Ran 830 tests in 1033.794s` · `OK (skipped=9)` | n/a (root gate) |
| `make -f delivery/Makefile verify` | `030ad00` | `CRUISE_RUNNER=1 CRUISE_ITERATION=2` | 0 | `Ran 830 tests in 1033.990s` · `OK (skipped=9)` | lint, typecheck, test all exit 0 with no prior entry → nothing recorded, no `delivery/baseline.json`; not quarantined |

Pre-slice baseline (marks cleared, `5460bf9`): `Ran 829 tests in 1033.671s` · `OK (skipped=9)`. The 830th test
is T001's example; `skipped=` is unchanged at 9 (AC-S00-5). Logs: `/tmp/gate1.log`, `/tmp/gate2.log`
(03:08–03:25Z and 03:25–03:42Z, 2026-10-03). The delivery gate's own lines: `check-slice-scope: on
`adopt-method`, not a `slice/<id>` branch — nothing to hold`; `check-constitution: 15 required principle(s)
covered, 8 of them as targets held to the convergence map`; `check-decisions: 13 decision(s) …`;
`check-benchmark` warned once about the open `implement` entry (closed after this write). One red gate during
the stage: `verify_failures=1`.

### Converge verdict — pass 1 of 2, 2026-10-03T03:50Z, commit `030ad00`

`drive-converge · model: host (claude-fable-5-1) · delegated, fresh context` · budget 15 min, completed within it.

**Converged** for the implementation stage (T001–T003). No CRITICAL or HIGH finding; the loop is not re-opened,
and the slice goes to its demo with the appended MEDIUM and LOW tasks (T007–T009, above) carried as Phase 4 /
convergence-commit work, as the ladder's bound says.

Per principle in force, with the file and line that satisfies it:
- **I** — the diff touches six files, none under `Makefile`, `delivery/Makefile`, `delivery/scripts/`, CI or
  hooks (`git diff --stat 5460bf9..HEAD`); the fix is the tests' child environment,
  `tests/test_cruise_runner.py:43–49`, not the gate; `VERSION:1` unchanged; no fragment owed (AC-S00-7 empty).
- **III** — one helper, `tests/test_cruise_runner.py:46–49`, copying `hook()`'s precedent; the only new import is
  `UNREAD` from the tree's own module (line 20).
- **IX / Additional Constraints** — `delivery/survey/running.md:12–26` carries no credential, path, hostname or pid;
  the runtime line names the interpreter the run used beside the `>=3.11` floor.
- **XIV** — gates ran at `030ad00`; the three commits carry no intent artifact yet → **T007 (MEDIUM)**: the
  convergence commit (T004) adds `specs/001-faster-slipwai/`. HIGH if it lands without them.
- **V, X, XIII** — targets, not in force; the diff nonetheless did what V asks (RED observed, one rule, one
  increment). **II, IV, VI, VII, VIII, XI, XII, XV** — not touched.

Per level: **domain** not touched (`src/slipwai/` diff empty); **use case** — `cruise.py start`'s refusal inside
an iteration unchanged and still proven by `tests/test_cruise_start.py:174`, which passes the marks itself and
goes red under the mutant (AC-S00-4); **delivery adapter (CLI)** — `./slipwai --version` → `slipwai 1.5.2.dev0`
exit 0 (AC-S00-1); all five spawn/in-process sites route through `outside_a_run`, and a sweep of `os.environ` and
`scripts/agents/cruise.py` over `tests/` found no site missed; **screen** — none; **published contract** — not
touched.

Evidence: marks set, eleven modules `Ran 44 tests · OK`; marks unset `Ran 44 tests · OK`; the helper mutated to
`{**os.environ, **(env or {})}` with marks set → `FAILED (failures=6, errors=1)` — the new example red plus
exactly the six of R2 — then restored with `git checkout -- tests/test_cruise_runner.py`; `git status` identical
before and after except the appended tasks. AC-S00-2's fields all present; CI's 3.11 confirmed at
`.github/workflows/verify-delivery.yml:18,29`. Logs: `/tmp/converge-s00-marks.log`,
`/tmp/converge-s00-nomarks.log`, `/tmp/converge-s00-mutant.log`.

Map: held at T004/T005 below (the Safety net row reaches `tests-pass`; the Constitution row is `/survey`'s to
re-read from the ratified file).

### After-converge gaps pass — 2026-10-03T03:59Z, commit `030ad00`

`drive-gaps · model: host (claude-fable-5-1) · delegated, fresh context` · read-only · budget 10 min, within it.
Verdict **satisfies** for AC-S00-1 … 5 and 7 (AC-S00-6 scheduled at T004/T005). Pinned by: AC-S00-1
`tests/test_cli.py:17` `test_version_flag` (an existing test the artifacts had not named — now cited in
`quickstart.md`); AC-S00-2 `delivery/survey/running.md:12–26`, every field; AC-S00-3 the five routed sites and
the new example, 44 cruise tests green under the marks, 830 in the gate; AC-S00-4 `tests/test_cruise_start.py:174`
against the refusal at `assets/toolkit/scripts/agents/cruise.py:1320–1321`; AC-S00-5 the recorded gate runs;
AC-S00-7 the empty diff. Five findings, traced (`gaps=5`), all paper and closed by the host before the demo:
1. **Artifacts promised a `delivery/baseline.json` and a ratchet line that a clean first run never writes**
   (`ratchet.py:204–212`): `quickstart.md`, `data-model.md`, `plan.md` and T003's steps corrected to say a silent
   green run is the clean case.
2. **When T004/T005 run** contradicted between the Phase 2 heading (before the demo) and `tasks.md`'s
   dependency line / `plan.md` step 4 (after acceptance): both now say converge → gaps → map → demo; and
   `project.json` is T004's deliberate edit, not a never-by-hand file.
3. **Product question — the quarantine guard on `tests-pass` is latent** while no baseline file exists
   (`check-convergence.py:98`): decided as **D14** — the row rests on the recorded gate evidence; noted in
   `data-model.md` and `plan.md`.
4. **Observation (low)** — two routed sites (`test_cruise_tell.py:147`, `test_cruise_stop_hook.py:29`) are held by
   the converge pass's static sweep, not by a test that would go red on regression, because `cruise.py run` does
   not refuse under the marks. No structural test opened; recorded.
5. `plan.md` *Scale/Scope* said 4 test files; five. Corrected.
