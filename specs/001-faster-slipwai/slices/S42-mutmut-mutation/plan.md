# Implementation Plan: S42-mutmut-mutation — a Python slice's mutation run is real and proportional to its change

**Branch**: `slice/S42-mutmut-mutation` | **Date**: 2026-10-08 | **Spec**: `specs/001-faster-slipwai/spec.md`,
`### S42-mutmut-mutation` (AC-S42-1..13), FR-008 as D137 amends it

**Status**: unblocked (cruise iteration 30): D223 answers Q1, D224 Q2, D225 *Handed back* 1, D226 the six readings
below. Tasks T031 onward carry the answers; the demo (T016) follows the next converge pass.

**Input**: the slice's criteria; D137, D138, D139, D149, D150 (S08's, cited); D212, D216 (this slice's), D214 (S42 is
planned on S41's merged tip, `b9f16ef`); D215 (d), D218, D219, D222 (S41's, whose *reasons* this plan applies to mutmut —
*Applied, not decided* below); research.md R1–R9; ADR 0010 (Proposed). Precedent: S41-stryker-mutation's plan, wrapper
and tests, read, not re-derived.

## Summary

Every generated Python service gets `mutmut==3.8.0` in its `dev` group and a `[tool.mutmut]` table in its
`pyproject.toml` (source `src`, the default suite without `tests/integration`, `-p no:xdist`); the four committed Python
locks are regenerated. One wrapper per project, `scripts/mutmut-mutation.py`, syncs the service from its committed lock,
refuses a host without `os.fork` and an environment without mutmut 3.8.0 (exit 2), starts every run from a fresh
`mutants/`, runs mutmut's own generation step, reads which mutants each scoped file holds from the `.meta` files that
step wrote (an empty one is *no mutant to run*, never mutmut's assertion), hands `mutmut run` exactly those names, and
decides the verdict from the `.meta` results by D212's rule. `make mutation-full` runs the wrapper once per Python
service; `make mutation` (S08's `mutation-scope.py`) treats Python as wired: it intersects the changed files with
`[tool.mutmut]` in Python before any tool starts, and sweeps a service whose `[tool.mutmut]`, mutmut pin, mutmut/libcst
lock entries or wrapper changed, or that it cannot read (no `tomllib`). `apps/*/mutants/` is ignored by git, exempt in
the verify stamp and pruned by `check-imports`; the words — the Makefile note, the mutation command, the skill, the
obligations page, the requirements row — say Python is wired, and only `java-quarkus` is left a placeholder.

## Technical Context

**Language/Version**: Python 3.11+ (the factory; the wrapper and the scope script it writes, stdlib only, reading TOML
with `tomllib` where it exists and sweeping where it does not); the generated service's Python ≥ 3.11
(`requires-python`), uv as its toolchain.

**Primary Dependencies**: new in every generated Python service: `mutmut==3.8.0` (dev group, exact) and its closure
(13 packages, R1) — ADR 0010. Nothing new in the factory itself.

**Storage**: none. The wrapper reads `<service>/mutants/**/*.py.meta` that the run wrote; `mutants/` is deleted before
the next run.

**Testing**: `unittest` under the factory's runner. The wrapper is tested in-process (loaded with
`sys.dont_write_bytecode`) and as a subprocess against fakes written in the test tree — a fake `uv` executable first on a
temporary `PATH` that records its arguments and working directory and, for `run … python -c`, writes the `.meta` files a
test hands it, and for `run … mutmut run`, writes the results the test hands it; the scope script behind S08's
`FakeRunner` seam. One real mutmut run on a generated starter, gated like `test_mutation_scope_real_typescript.py`
(`backends_under_test()` names `python`, `uv` on `PATH`) and skipped otherwise. No `unittest.mock`.

**Target Platform**: Linux and macOS developer machines (WSL on Windows); CI unchanged (no gate runs `make mutation`).

**Project Type**: CLI factory (`slipwai`) generating repositories.

**Performance Goals**: a slice that changed one production module mutates that module's mutants only (US2 scenario
6); the demo measures it against `mutation-full` (AC-S42-13; R8's reference: 14 mutants in 1.1 + 1.6 s against 992 in
9.8 s on one service).

**Constraints**: owner priority 1 — `verify`, `verify-checks`, `ci` and the CI workflow unchanged; the `mutation` line
unchanged (only `mutation-full`'s Python recipe line changes, which `factory_recipe` mirrors); no Makefile variable
added; `SINCE` reaches no Python line (D216); `src/` and `tests/` files ≤ 350 lines and 120 columns; anything under
`assets/` opens files with `encoding="utf-8"`, runs as `python3 -B` in probes and leaves no `__pycache__`; path literals
a toolkit check loads written as segments.

**Scale/Scope**: one backend (Python), any number of Python services beside any others.

## Constitution Check

| Principle | How this slice meets it | Where |
|---|---|---|
| I — owns its files; passes its own gate | the table and the wrapper are the project's from generation; `migrate` brings them, the regenerated `rules.json` and the ignore lines to older projects; `make verify` is untouched and still passes (the matrix's Python rows, now syncing mutmut); the scope script reads `pyproject.toml` and never writes it | rules 1, 10 |
| I — `VERSION` and fragment | `changelog.d/mutmut-mutation.md`, MINOR, with a **Catch-up.** for the `uv.lock` conflict, a leftover `mutants/` or `.mutmut-cache`, and exit 2 until the lock is redone (AC-S42-12); `VERSION` stays `1.6.0.dev0` (S41's MINOR already carries it) | rule 10 |
| II — idempotency, retry safety | every run deletes `mutants/` first (D212 item 7); one run of a service at a time (`flock`); a second run never reads the first's results | rules 4, 5 |
| III — simplicity | one wrapper, as Go's and TypeScript's; TOML read by stdlib; the reader takes the subset the factory writes and calls the rest unreadable rather than guessing; no new factory dependency | research R2, R3 |
| V — GWT, one rule per increment | rules 1–11 below, each its own RED-GREEN-REFACTOR, entered through the wrapper's and the scope script's `main` | Rules |
| VI — contract-bounded integration | mutmut's `.meta` read field by field (`exit_code_by_key`), its exit codes mapped by a table copied from 3.8.0's `stats.py`; an unknown code fails closed; the version is checked before the generation step runs | research R3, R4 |
| VIII — versioning | the new dependency is pinned exactly; a change to the pin or to libcst's lock entries sweeps (R6); the bump is MINOR | rules 6, 10 |
| IX — supply chain | installed only from the committed lock (`uv sync --locked`); `pip-audit` over the new tree names nothing mutmut brought (R1) | rule 4 |
| XIII (target) — fast feedback | the point of the slice | quickstart |
| XIV — stop on a decision | the starter's own survivors and the readings of S41's decisions applied here are handed back below, with options | *Handed back* |
| ADR rule (*Development Workflow*) | a new dependency in every Python project: ADR 0010, `Proposed` | `delivery/docs/adr/0010-mutmut-for-python-mutation.md` |
| Stubs recorded | `java-quarkus` stays a placeholder that refuses (AC-S42-11) — an unchanged stub, recorded in S08 | rule 6 |

No violation; nothing in *Complexity Tracking*.

## Rules (the map the tasks are cut from — all `[US2]`, User Story 2 scenario 6)

1. **What a Python service is given** (AC-S42-1, -9 first clause, -4's recipe). `BASE_DEVELOPMENT` gains
   `mutmut==3.8.0`; the template `pyproject.toml` gains the `[tool.mutmut]` table of data-model, each line commented;
   the four `uv*.lock` are regenerated by `scripts/regenerate-locks.py` and `--check` passes; `uv sync --locked` accepts
   each starter; `scripts/mutmut-mutation.py` is written once per project with a Python service, executable
   (`BACKEND_EXECUTABLES["python"]`); `mutation-full`'s Python line is `python3 scripts/mutmut-mutation.py <path>`, one
   per service, with no `SINCE`; `apps/*/mutants/` is ignored; `factory_recipe` writes the same line in the same commit.
2. **The configuration the wrapper reads** (R2, data-model *targets*, *matched*, *refused*, *versions*).
   `targets(service)`, `matched(config, file)`, `refused(service, file)` and `versions(pyproject_text, lock_text)` as
   data-model fixes them; no `tomllib` is `Unreadable`.
3. **The verdict** (D212, AC-S42-5, R4). From `mutants/<file>.meta` for the given files (all, swept): killed passes;
   no tests counted on the last line; every other code — survived, timeout, suspicious, segfault, not checked,
   interrupted, skipped, caught by type check, unknown — fails, one line per mutant naming the service, the mutant and
   its status; a sweep with no mutant fails; mutmut's exit status is printed, never the verdict; a `block`, `start` or
   `end` pragma in a judged file, or a non-empty `do_not_mutate_patterns`, fails in one line (*Applied, not decided* 2).
4. **Setup and environment** (AC-S42-10, R7). No `os.fork` → exit 2 naming WSL; no `uv` → exit 2; `uv sync --project
   <svc> --locked --quiet` refused → exit 2 naming `uv lock --project <svc>`; mutmut absent or not 3.8.0 in the
   environment → exit 2 with one line; no `[tool.mutmut]` → exit 2; `PYTEST_ADDOPTS` is removed from mutmut's
   environment and named; an exclusive `flock` on `<svc>/.venv/mutmut-run.lock` holds the run.
5. **Generate, then run** (AC-S42-2's mechanism, AC-S42-6, R3, R5). `mutants/` deleted before; mutmut's generation step
   run in the service's environment; a given file with no `.meta` is *outside mutmut's configured targets*; every given
   file's `exit_code_by_key` empty → *no mutant to run*, exit 0, `mutmut run` never started; otherwise `mutmut run --
   <every key of the given files>`, from the service directory; a changed `pkg/__init__.py` runs that file's keys only.
6. **Python is wired in the scope script** (AC-S42-2, -3, -8, -11, D138 items 1 and 5). `WIRED` and `PRODUCTION_ROOT`
   gain Python, `PLACEHOLDERS` and `PYTHON_REFUSED` lose it; `Tools.plan/run/sweep` hand Python to the wrapper as
   TypeScript's are handed to `stryker-mutation.py`; a file `[tool.mutmut]` leaves out is named *outside mutmut's
   configured targets* and mutmut does not start; a refused path refuses its service (exit 2, no tool); a skipped Python
   service keeps no earlier `mutants/` (`drop_report`); two Python services, and Go beside Python, run only the changed
   one and name the other skipped; D138's test-only, deleted and outside-config lines hold with exit 0; `java-quarkus`
   still refuses; `SINCE` and D117's borders hold for Python; `make mutation-full SINCE=<ref>` sweeps Python whole.
7. **What sweeps a Python service** (AC-S42-7, R6). Its `[tool.mutmut]` or mutmut requirement changed (parsed); its
   `uv.lock`'s mutmut or libcst-closure versions changed; the wrapper changed (every Python service); a side that cannot
   be parsed, or no `tomllib`; a configuration `targets()` cannot read; an ignored file under `src/`. Each line names the
   file.
8. **The stamp, `check-imports` and the scoped gate** (AC-S42-9). After a passing and a failing Python run the stamp's
   ignored digest and `git status` are unchanged and `verify-scoped` is not broadened: `apps/*/mutants/` is an `EXEMPT`
   row; `check-imports` prunes `mutants` at the root of a Python deployable `project.json` records, beside its
   `pyproject.toml`, and nowhere else (a package of that name under `src/` is still read).
9. **The words** (the criteria's *wired* half; AC-S42-11's placeholder half). A Python note above the target (what
   runs, the `.meta` report, where the verdict is decided, the escape for an equivalent mutant, that the default
   starter's sweep reports its own survivors and the minimal one is green, why `tests/integration` is left out and why
   `-p no:xdist`); `mutation_command` names the Python report and `UNWIRED` names only Quarkus; the mutation-testing
   skill says a generated Python service is already wired; `docs/backend-obligations.md` and `docs/requirements.md`;
   S41's fragment stops saying Python has no tool (both fragments land in one release); ADR 0010.
10. **Catch-up** (AC-S42-12). `slipwai migrate` on a project made before brings the recipe, the wrapper, the ignore
    lines and the regenerated `rules.json`, and the dev pin and `[tool.mutmut]` where the service's files merge; the
    fragment names the `uv.lock` conflict and `uv lock --project apps/<svc>`, says a leftover `mutants/` or
    `.mutmut-cache` may be deleted, and says `make mutation` exits 2 until the lock is redone.
11. **One real run** (AC-S42-1, -2, -4, -5 end to end). On a generated Python starter on `slice/S1`: one changed module
    whose tests kill its mutants scopes to it and passes; a weakened test fails naming the survivor; a types-only module
    is *no mutant to run*; the sweep mutates every file under `src/`.

AC-S42-13 is the demo's (quickstart), after the converged verdict.

## Project Structure

### Documentation (this slice)

```text
specs/001-faster-slipwai/slices/S42-mutmut-mutation/
├── plan.md  research.md  data-model.md  quickstart.md  tasks.md  benchmark.json
delivery/docs/adr/0010-mutmut-for-python-mutation.md
```

### Source Code

```text
assets/languages/python/scripts/mutmut-mutation.py      # new: the wrapper — config, refusal, setup, generate, run, verdict
assets/languages/python/app/pyproject.toml              # the [tool.mutmut] table
assets/languages/python/locks/uv*.lock (4)              # regenerated
src/slipwai/project/mutmut.py                           # new: the script path, the recipe line, the note, mutmut_files
src/slipwai/project/languages/python.py                 # BASE_DEVELOPMENT; one call site (the script)
src/slipwai/project/native_commands.py                  # the Python `mutation-full` line
src/slipwai/project/mutation.py                         # MUTATION_NOTES, NAMED_FILES, UNWIRED, the report line
src/slipwai/project/gitignore.py  src/slipwai/backends.py  # the ignore line; the script's executable bit
assets/toolkit/scripts/mutation-scope.py                # tables and dispatch only: WIRED, PLACEHOLDERS, PYTHON_REFUSED,
                                                        # PRODUCTION_ROOT, REPORTS, factory_recipe, sweep causes, Tools
assets/toolkit/scripts/verify-stamp.py                  # one EXEMPT row
assets/toolkit/scripts/check-imports.py                 # `mutants` at a Python deployable's root
assets/toolkit/skills/mutation-testing/SKILL.md  docs/backend-obligations.md  docs/requirements.md
changelog.d/mutmut-mutation.md  changelog.d/stryker-mutation.md (Python's clause only)
tests/test_mutmut_config.py           # new: rule 2
tests/test_mutmut_verdict.py          # new: rules 3, 5 (through a fake uv)
tests/test_mutmut_setup.py            # new: rule 4
tests/test_mutation_scope_python.py   # new: rule 6
tests/test_mutation_sweeps_python.py  # new: rule 7
tests/test_mutmut_generated.py        # new: rules 1, 8, 9's generated half
tests/test_mutmut_migrate.py          # new: rule 10
tests/test_mutation_scope_real_python.py  # new, heavy: rule 11
tests/test_mutation_placeholders.py, tests/test_mutation_words*.py, tests/test_mutation.py, tests/test_mutation_dry_run.py,
tests/test_select_tests_real_*.py, tests/test_select_tests_cross_reads.py, tests/test_scoped_targets.py  # re-pinned
```

**Structure Decision**: the one deployable `slipwai-graph` (kind `tool`, D3); one vocabulary — the factory's generated
toolkit — so one context. Code that lands in generated projects goes under `assets/` and `src/slipwai/project/` (owner
priority 3). mutmut's logic lives in a wrapper of its own under the Python backend's assets,
`assets/languages/python/scripts/mutmut-mutation.py`, as `go-mutation.py` is Go's and `stryker-mutation.py` is
TypeScript's; `mutation-scope.py` gains table rows and dispatch only, and loads the wrapper (never copies it) for the
configuration, the refusal and the version reader. The factory side's new text goes in a new module,
`src/slipwai/project/mutmut.py`, because `native_commands.py` (321), `mutation.py` (291) and `backends.py` (332) are near
the 350-line budget. Shared surfaces stay S06's and S14's: `rules.py`, `scoped_targets.py`, `verify_scoped/*` are read,
never edited. No `.codegraph/` in this repository: callers were found by text search (`grep -rn`), and the tasks name
them.

**Pin**: this is the factory's own code, held by its own tests — the S08 and S41 mutation suites
(`tests/test_mutation_*.py`, `tests/test_stryker_*.py`), `tests/test_matrix.py`, `tests/test_backend_obligations.py`,
`tests/test_verify_scoped_*`, the lock checks. No code here predates the method (`delivery/commands/drive.md` stage 7).

**Nothing outside the slice's scope is needed**: no change to the root `Makefile`, `delivery/scripts/`, `tools/`, CI or
harness settings.

## Applied, not decided — confirmed by D226 (standing decisions' reasons read onto mutmut, all six as built)

Each is a reading of a standing decision onto the second tool, not a new choice; each is one table or one branch to
change if the host reads it otherwise, and none blocks the slice.

1. **D222 → libcst** (D226 item 1). D216 sweeps a service on a mutmut pin change; D222's reason (*a new parser changes which mutants
   exist*) sweeps it on a move of `libcst`'s lock entries too (R6). pytest, coverage and textual are not in the set.
2. **D219 → block pragmas** (D226 item 2). D212 item 1 names mutmut's `# pragma: no mutate` as the escape; mutmut 3.8.0 also reads
   `block`, `start` … `end` and `do_not_mutate_patterns`, which silence mutants nobody looked at — D219's reason for
   failing Stryker's block comments and `excludedMutations`. The wrapper fails them (R4). mutmut's bare pragma takes no
   reason, so none is required (D212 item 1 names it as written).
3. **D215 (d) / D218 → `*`, `?`, `[` in a scoped path** (D226 item 3). `mutmut run` reads names through `fnmatch`; a module path
   holding one would widen the scope, so it is refused (data-model *refused*).
4. **D215 (a) → the exact version** (D226 item 4). A run never fetches, and the wrapper refuses (exit 2) an environment whose mutmut
   is not 3.8.0, because its generation step is 3.8.0's (R3). A project that raises the pin before the factory does gets
   that line until `slipwai migrate` brings a newer wrapper. Renovate will propose such a raise; a grouping or hold rule
   is `renovate.py`'s, not this slice's.

5. **D219 → `mutate_only_covered_lines`** (D226 item 5) (converge pass 1's question). mutmut 3.8.0 with `mutate_only_covered_lines = true`
   generates no mutant for a line coverage excludes (`# pragma: no cover`, `exclude_lines`), covered or not — a setting that
   silences mutants nobody looked at, D219's class. The wrapper fails a run whose table sets it, beside
   `do_not_mutate_patterns` (T017). The alternatives the pass named: allow it (a table change already sweeps), or exit 2 at
   setup.

6. **D219 → `max_stack_depth`** (D226 item 6) (converge pass 2, T022). A table that sets it turns survivors a test reaches through
   deeper calls into *no tests* (`33`, counted, never failed) — reproduced against 3.8.0. The same reading as item 5: the
   wrapper fails a run whose table sets it. Alternative named: allow it (but the sweep reads the same `33`s and is green).

## Answered (product questions from the after-converge gaps review — D223, D224)

The slice converged at pass 2 (`tasks.md`, *Convergence*); the after-converge gaps review then found one HIGH and one
MEDIUM that each turn on a decision this slice may not take. The demo (AC-S42-13) cannot be recorded as the quickstart
writes it until **Q1** is answered.

**Q1 — What does `make mutation-full` do when an earlier service fails?** **Answered by D223: (c)** — one combined Python
`mutation-full` line, the wrapper running each service fully and failing at the end, `--file` refused with more than one
service, AC-S42-4 amended in place; (a) across backends is `S47-mutation-full-runs-every-service`; (b) refused. (gaps finding 1, HIGH; AC-S42-4, -13.) The
recipe is one line per service and make stops at the first failing line. The default Python starter is red the day it is
generated (R9), so on the two-service demo `apps/service` fails and `apps/billing` is never mutated; `make mutation` on the
trunk delegates to the same recipe. Go and TypeScript recipes have the same shape today; their default starters are not
always red.
- (a) Every service runs and the run fails at the end — a recipe change for every backend, mirrored in `factory_recipe`.
  Conflicts with AC-S42-11 (*`mutation-full` unchanged for every other backend*) unless that criterion is amended.
- (b) Keep make's stop-on-error; the note, the quickstart and the demo say `make -k mutation-full`, and the scope script
  passes `-k` when it delegates the sweep (a change to S08's `full()` for every backend).
- (c) Python only: the Python services share one recipe line, `python3 scripts/mutmut-mutation.py apps/service apps/billing`,
  the wrapper running each in turn and failing at the end — AC-S42-4's "one line per service" then reads as output lines,
  and Go or TypeScript failing first still stops it.
- **Recommended: (c)** — it meets AC-S42-4 for Python inside this slice without touching another backend's recipe
  (AC-S42-11), and leaves (a) for every backend as its own MINOR slice. The gaps reviewer recommended (b) now and (a) later;
  (b) changes S08's sweep for every backend inside S42.

**Q2 — What does `add-service --backend python` do in a project an older factory last wrote?** **Answered by D224: (a)**
now — one Catch-up sentence, AC-S42-12's added clause, no code — and (b) as `S46-add-service-older-project`, warning
only; (c) refused. (gaps finding 4, MEDIUM;
AC-S42-2, -9, -12.) It writes the wrapper, the recipe line and the ignore line but not the newer `mutation-scope.py` or
`verify-stamp.py` (it writes only files that differ between the two renders), so every scoped run sweeps ("`mutation-full`'s
recipe is not the one the factory wrote") and the stamp cannot reuse after a run. TypeScript (S41) has the same exposure.
- (a) The Catch-up says to run `slipwai migrate` before adding a Python service.
- (b) `add-service` refuses or warns when `project.json`'s `generator` is older than the running factory — a factory-wide
  follow-on slice.
- (c) `add-service` also refreshes the toolkit scripts.
- **Recommended: (a) in this slice** (one Catch-up sentence, with T025), **and (b) as a follow-on** across backends.

## Handed back (not blocking)

Recorded for the host; neither changes a criterion this slice implements or a decision it relies on, and either
answer only adds work. The slice proceeds under the criteria as written.

1. **The default Python starter's `make mutation-full` is red on day one** — **answered by D225: (a)**, D217 applied:
   the note and the fragment say so, the fragment names `S45-python-starter-kills-mutants` as the fix, no pragma is added,
   and the demo hand-replays a sample of survivors (D221's lesson) (research R9: 114 survivors in nine files —
   the memory stores, the HTTP app, the event port, logging, the projections and their lifespan, settings, tracing —
   none read as equivalent; the minimal `standard`/`http none`/`memory` starter is green). This is D217's shape on the
   TypeScript side.
   - (a) Ship as the criteria say, and say it: the note and the fragment state that the default starter's sweep reports
     its own weak tests, and a follow-on slice — *the Python starter's own tests kill every mutant* — strengthens them
     (test-only changes to the Python starter's test assets under `assets/backing-services/python/` and
     `assets/languages/python/`).
     **Recommended**, as D217 (a): it keeps S42 the size D128 wants and the verdict honest (priority 5). The note and the
     fragment are written to (a) without promising a follow-on; the host adds the promise with the slice.
   - (b) Widen S42 to kill or suppress every starter survivor before it ships — roughly 114 mutants; triples the slice.
   - (c) Narrow `[tool.mutmut]` to the files that are green today — refused, as D217 refused it for TypeScript.
2. **S41's fragment** says *Python and `java-quarkus` still have no tool wired*; both fragments land in the same
   release, so rule 9 narrows that clause to `java-quarkus` (pinned words in `tests/test_stryker_migrate.py` permitting).
   Named here because the file is S41's.

## Open questions

None that block. Recorded residuals: `type_check_command` set by a project turns its type-caught mutants (`37`) into
failures, since D212 passes only killed (no project the factory makes sets it); a project with no test reaching any
mutant makes mutmut stop before testing (`run_stats_collection`, exit 1, every key `null`), which the wrapper fails as
*not checked*, never as *no tests* — a red run, never a green over nothing; mutmut uses every core
(`os.cpu_count()`), multiplied by concurrent Phase 4 worktrees, unchanged, as Stryker's (S41 G19).

## Complexity Tracking

Nothing to justify.
