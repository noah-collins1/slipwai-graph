# Implementation Plan: S04-parallel-gate — the gate's independent checks run at once and each toolchain syncs once

**Branch**: `adopt-method` (D12 — no `slice/` branch, no claim, no push) | **Date**: 2026-10-04 |
**Spec**: [spec.md](../../spec.md), *Slice acceptance criteria* → `### S04-parallel-gate` (AC-S04-1 … AC-S04-63)

**Input**: the slice's row in [story-split.md](../../story-split.md) and its criteria in `spec.md`; decisions
D12, D74, D78, D81, D83, D88, D89, D90, D91, D92 in [decisions.md](../../decisions.md); the Parking Lot lines *What
`S04-parallel-gate` inherits from the stamp* and *Seen at S04's gaps stage*. Written by cruise iteration 13 (host,
strong model). The optional `before_plan` hook (`/characterise`) is taken as the ladder's Pin stage, after tasks.

## Summary

A generated project's `make verify` runs its checks one after another, and `make -j verify` runs them together
only by luck: three `uv sync` runs land on one `.venv` at the same moment, three Maven runs on one `target/`, and
`check-python` is no longer first. This slice orders every writer ahead of what reads it by a prerequisite — the
one thing every GNU Make since 3.81 honours ([research.md](research.md) R-1) — so `make -j verify` gives the serial
run's verdicts in about half the time (R-6), syncs each Python service once per `make` run instead of three times,
and says where to look when it fails. The model tooling gets a committed lockfile and installs through one file
target, so `check-drawio` stops reinstalling on every gate and stops leaving an untracked lock behind. An adopted
repository's gate, whose commands nobody here can call read-only, is declared serial. Plain `make verify`, CI and
the ladder's text type what they typed (D89). MINOR: one new generated file, the lockfile (D91); `VERSION` stays
`1.6.0.dev0`.

## The example map (rules the tasks cut on)

*Serial*, *a full run* and *a stand-in* are as the criteria define them. *The Python project* is a generated
project with one Python service, the event profile, FastAPI and Postgres unless the example says otherwise.

| Rule | Criteria | What it says | Examples |
|---|---|---|---|
| **R1** one sync per `make` run | AC-S04-28 to -41, -44, -14 | The sync is one target; every target that runs a Python mode names it; the recipes pass the script `--synced`; a mode reached any other way syncs first | e1 `make verify`, one service → one sync line · e2 `make -j verify` → one per service, each before the first run line · e3 two services → two · e4 `make lint test` → one · e5 `make lint` alone, and `typecheck`, `test` → one, first · e6 `./scripts/verify --lint-only` typed directly (and `--typecheck-only`, `--test-only`, none) → one, first · e7 `make ci` → one · e8 `make migrate` → one, before the migration · e9 `make dev` → one, before the service · e10 `make install test` → one · e11 a `uv` whose `sync` fails → non-zero, no run line, with and without `-j` · e12 the generated CI workflow, `service_commands()` and the pages never say `--synced` · e13 no environment variable makes `--test-only` skip the sync · e14 `make verify` prints nothing new but make's echo of the sync recipe, once · e15 `make verify lint` → at most two per service · e16 no `.venv`, `make -j check-openapi lint` → the sync ends before either starts |
| **R2** `check-python` is first, both ways | AC-S04-13, -1, -18 | It is a prerequisite of the sync and of every check that runs `python3` | e1 a `python3` older than 3.10, `make verify` → its line, no sync line, no other check started, non-zero · e2 the same under `-j` · e3 a serial full run starts the checks in the order they had, no two at once · e4 `make -j verify` leaves every byte under `.specify/` as it was |
| **R3** a parallel run is the serial run's verdict | AC-S04-2 to -9, -19, -20 | Same checks, exit zero exactly when serial is, the closing line last on a pass; a failed run names its failures and ends on the gate's own line; one stamp for both | e1 the set of commands started under `-j` equals serial's · e2 exit 0, last line `verify: all gates passed` · e3 two checks running at the same moment (a barrier between two stand-ins, no clock) · e4 one check fails under `-j` → non-zero, no closing line, no stamp · e5 two fail → each on a `***` line with its target's name · e6 a failed run, serial and `-j` → the gate's last line begins `verify:` and points at the `***` lines · e7 a pass under `-j` is reused by `make verify` · e8 a pass under `make verify` is reused by `make -j verify` |
| **R4** each check's output stays together where the make can | AC-S04-10 to -12, -16 | `--output-sync=target` to the sub-make, behind a test of `.FEATURES`; nothing else newer than 3.81; no `.WAIT`, no `.NOTPARALLEL` with a prerequisite | e1 4.4.1, `-j`, two checks printing three lines each a moment apart → each check's three lines contiguous · e2 the recipe names the option only inside `$(if $(filter output-sync,$(.FEATURES)),…)` · e3 a serial run with the feature: a check's first line is seen before its last is written · e4 every starter's Makefile: no `.WAIT`, no `.NOTPARALLEL` with a prerequisite |
| **R5** every backend family holds the rule | AC-S04-15, -17, -42, -43, -5 | Under the gate, Java's three Maven checks run one after another and Go's `typecheck` runs before its `lint` and `test`; standalone targets are as they were; TypeScript and the install-free modes are pinned | e1 a Java project, `-j`, a stand-in `./mvnw` → no two overlap, verdict equals serial · e2 a Go project, `-j`, a stand-in `go` → `typecheck`'s commands end before `lint`'s or `test`'s start · e3 `make test` alone on a Java project starts no `lint` command · e4 a TypeScript Makefile: every gate target reaches `npm ci` only through the file target · e5 Go's and Java's `lint`, `typecheck`, `test` carry no install step · e6 with the real toolchain, one starter per family, fresh: `make -j verify` passes with its serial run's checks |
| **R6** an adopted repository's gate is serial | AC-S04-24 to -27 | A bare `.NOTPARALLEL:` where `stamped()` answers no, and nowhere else | e1 an adopted repository's Makefile carries the line · e2 a generated project's carries none · e3 recorded `lint`, `typecheck`, `test` as stand-ins, `make -j verify` → none overlap, serial order · e4 no baseline, `make -j verify` → `baseline.json` equals a serial first run's |
| **R7** the model tooling installs from a committed lock, once, and says when it did not | AC-S04-45 to -55 | The factory ships `scripts/event-model/package-lock.json`; one file target runs `npm ci`; the four model targets name it; `check-drawio` says the skip line | e1 a new event-profile project tracks the lock; its root entry equals the manifest's pins · e2 the shipped lock: version 3, every `resolved` from `registry.npmjs.org`, a package for each esbuild platform · e3 fresh clone, `make check-drawio` → `npm ci`, `git status --porcelain` empty · e4 installed and newer → no npm command, the skip line · e5 either manifest touched → `npm ci` again, no skip line · e6 manifest and lock disagree → non-zero with npm's refusal, no tracked file changed · e7 `make model-drawio-test` (and `model`, `model-drawio`) on a matching tree → no install, no skip line · e8 `make -j check-drawio model-drawio-test`, fresh → one `npm ci`, ended before either starts · e9 the Makefile spells `npm` for `scripts/event-model` in one recipe, `npm ci` · e10 fresh clone on a branch, first `make verify` passes → recorded; the next prints the reuse line |
| **R8** it reaches a project that exists, and the words are true | AC-S04-56 to -63, -21 to -23 | `migrate`'s three cases; one MINOR fragment whose catch-up stands alone; the page; CI and the ladder unchanged; the stamp's script untouched | e1 a project made at the commit before this slice, clean → `migrate` adds the lock, `make check-drawio` passes · e2 the same with an untracked lock → refused, the file as it was · e3 the same with its own committed lock → the merge stops naming that file · e4 the fragment: first line `MINOR`, the catch-up paragraph alone says the three cases, the edited-manifest sentence and the adopted line under the experimental label · e5 the page says the six things of AC-S04-61 · e6 the generated CI workflow and the ladder's commands still type `make verify` · e7 S04's diff does not name `assets/toolkit/scripts/verify-stamp.py` |

R1, R2, R3 (the failed run's line), R4, R5, R6 and R7 change production code, each its own RED-GREEN-REFACTOR cycle
with its examples red first for the stated reason. R3e1, e2, e7 and e8, R5e4 and e5, R8e2, e3 and e6 hold today or
by the rules before them: each is still **seen** to have teeth — the assertion inverted or the fixture broken,
observed failing, restored, the tree clean afterwards — before it is committed. AC-S04-22 and -23 are the demo's.

## Technical Context

**Language/Version**: Python ≥ 3.11 (`pyproject.toml`); the generated Makefile is GNU Make, 3.81 upwards.
**Primary Dependencies**: none added to the factory. The shipped lock adds no dependency to a project: the same
three pins `scripts/event-model/package.json` already carries (R-4).
**Storage**: none.
**Testing**: `unittest` via `make test`. The rules are driven through a generated project's own `make`, with
stand-ins on `PATH` written in the test tree (`uv`, `npm`, `go`, `./mvnw`, `python3` where R2 needs an old one):
each appends a line to a log when it starts and when it ends and exits as the test says. Concurrency is shown by a
barrier — one stand-in waits, bounded, for the other's start line — never by a clock. The helpers S03 left
(`StampTestCase` and what `tests/test_verify_stamp_recipe.py` and `tests/test_verify_stamp_launches.py` import)
generate the project and run its gate; one new helper module, `tests/parallel_gate.py`, holds the stand-ins and
the log's readers. No mocking framework.
**Target Platform**: wherever `slipwai` runs; the generated gate on Linux, macOS and, under Git Bash, Windows —
which the matrix tests hold before release (Edge Cases) and this slice does not run.
**Project Type**: CLI tool, the factory — deployable `slipwai-graph`, kind `tool`, path `.`.
**Performance Goals**: AC-S04-22 — on AC-S03-20's project, warm, the median of three `VERIFY_FORCE=1 make -j
verify` is lower than the serial median; measured at the demo, written into the quickstart and the fragment.
**Constraints**: nothing newer than GNU Make 3.81 documents except output grouping behind its feature test; the
stamp's script is not edited by a byte (D91, D92 — if a task finds it must be, the slice stops and
`S32-verify-stamp-split` lands first); nothing under `delivery/scripts/`, `tools/`, the `Makefile`, this
repository's own CI or hook settings changes (this repository's `delivery/Makefile` takes the adopted line by
`slipwai migrate`, a person's — D9); every file under `src/` and `tests/` stays within `make check-structure`'s
350 lines (`makefile.py` is at 328, `docs.py` 329, `native_commands.py` 308: what this slice adds lives in
`gate.py` and one new module); every `read_text`/`open` names `encoding="utf-8"`.
**Scale/Scope**: five generator modules and one new one, one shell script's first lines, one shipped lockfile, one
page paragraph, one fragment; one test helper and about nine new test files; S03's two suites that pin the order
and the recipe.

## Constitution Check

*GATE: evaluated against `.specify/memory/constitution.md` before research; re-checked after design.*

| Principle | Touched? | How this slice satisfies it |
|---|---|---|
| I. A generated project owns its files and passes its own gate (NON-NEGOTIABLE) | Yes | No check is removed, weakened or reordered out of the gate: the same prerequisites hang on `verify-checks`, and CI and the trunk type `make verify` as before (AC-S04-21). A memoised or parallel run is additive: the stamp is never read in CI (D74), and a pass under `-j` is the serial verdict by R1–R5. A project's files change only through `slipwai migrate`, and the fragment's catch-up says the three lockfile cases (AC-S04-56 to -60). Every starter `make starters` materialises passes its own gate (AC-S04-63). |
| III. Simplicity | Yes | Prerequisites, one argument, one file target in the root's own pattern, one bare directive. No new script, no setting, no content comparison (D91). |
| V. Acceptance-driven development | Yes | Each rule a cycle through a generated project's own `make`; holds written as holds and seen to have teeth. |
| VIII. Versioning and breaking changes | Yes | MINOR, said in the fragment's first line and the commit (a new generated file, D91); the adopted line under the experimental label. |
| XI. Dependencies are locked | Yes | The model tooling's transitive packages stop floating: a committed lock, `npm ci` (D91). |
| XIV. Agent-generated change meets the same bar (NON-NEGOTIABLE) | Yes | Increment commits with the quickest relevant tests green; both full gates on the final tip; the hand runs the demo as the actor. |
| II, IV, VI, VII, IX, X, XII, XIII, XV | No | No domain code, contract, telemetry, secret or type changes. |

**Gate result:** no violation; *Complexity Tracking* stays empty. **Post-design re-check:** unchanged.

## Project Structure

```text
src/slipwai/project/parallel_gate.py           # new — R1, R2, R5: the sync target, the prerequisite lines, the gate-only order, `--synced` on a recipe; R8: the page's paragraph
src/slipwai/project/gate.py                    # R3, R4: `STAMPED` — the grouping option, `VERIFY_ORDER=1`, the failed run's line
src/slipwai/project/makefile.py                # R1, R2, R5: calls into `parallel_gate`; `install_step()`; `dev_targets()`
src/slipwai/project/native_commands.py         # R1 only if `--synced` cannot be applied from `makefile.py` (see Design)
src/slipwai/project/languages/python.py        # R1: `verify_script()` — the second argument
src/slipwai/backends.py                        # R1: `dev_command()`'s Python line loses its written-out sync
src/slipwai/project/integration.py             # R1: `test-integration` and its per-service targets name the sync
src/slipwai/project/openapi.py                 # R1: `openapi` and `check-openapi` name the sync where a Python service exports
src/slipwai/project/adopted_targets.py         # R6: `gate_target()` — the bare `.NOTPARALLEL:`
src/slipwai/project/model_targets.py           # R7: the file target, the four targets, the skip line
assets/toolkit/scripts/event-model/package-lock.json   # R7: new — made by npm (R-4)
src/slipwai/project/docs.py                    # R8: the gate's page takes the paragraph from `parallel_gate`
changelog.d/parallel-gate.md                   # R8: new — MINOR
tests/parallel_gate.py                         # new helper — the stand-ins, the log, the barrier
tests/test_parallel_gate_sync.py               # new — R1 e1–e7, e10, e11, e14, e15
tests/test_parallel_gate_sync_ways.py          # new — R1 e8, e9, e12, e13, e16
tests/test_parallel_gate_first.py              # new — R2
tests/test_parallel_gate_run.py                # new — R3
tests/test_parallel_gate_output.py             # new — R4
tests/test_parallel_gate_families.py           # new — R5
tests/test_parallel_gate_adopted.py            # new — R6
tests/test_model_install.py                    # new — R7 e3–e10
tests/test_model_lock.py                       # new — R7 e1, e2
tests/test_parallel_gate_carry.py              # new — R8
tests/test_verify_stamp_pinned.py              # AC-S04-63: the pinned order, amended for the sync phase
tests/test_verify_stamp_recipe.py              # AC-S04-63: the recipe's text, amended
```

**Structure Decision**: one deployable, `slipwai-graph` (kind `tool`, path `.`, purpose confirmed); one bounded
context (the factory; D3). The decided strategy is `leave-it` (`delivery/docs/adr/0002-change-strategy.md`, at
`Proposed`; D5): no new home. The code changed existed before the method did, so the Pin stage applies.
`native_commands()` is called only from `makefile()`; `makefile()` from `src/slipwai/scaffold.py` and the adoption
path; `model_targets()` from `makefile()` (found by text search — this tree has no `.codegraph/`). Any test that
pins the whole text of a generated Makefile, a recipe or `scripts/verify`, and any helper under `tests/` that
rebuilds an old Makefile by regex, is found by search before the change and named in the task.

## Design

Names the tasks may keep or better, saying so: the target `sync`, the argument `--synced`, the variable
`VERIFY_ORDER`, the module `parallel_gate`.

**R1 — the sync.** Where a project has a Python service, the Makefile gains

```make
.PHONY: sync
sync: check-python ## Build each Python service's environment from its committed lock, once per make run
	./scripts/verify --install-only
```

(the family's own script where the project has several: `verify_path()`). Every target whose recipe runs a mode of
that script, or `uv run --no-sync`, names `sync` as a prerequisite: `lint`, `typecheck`, `test`, `format`,
`adversarial`, `install`, `test-integration` and its per-service targets, `migrate` and its per-service targets,
`dev` and its per-service targets, `openapi` and `check-openapi`. For the targets that live inside a backing
service's marked region (`migrate`, `dev`) the prerequisite goes **on the target line inside the region**, as
`install_step()` already does for npm — a prerequisite line left outside would define a pruned target with no recipe
(`migrate_targets()`'s docstring says why). Their recipes lose the written-out `--install-only` line, and
`install`'s recipe loses its Python line. In the Makefile's recipes — and in `INTEGRATION_TEST`'s default, which is
a recipe's text — each call of a mode becomes `./scripts/verify --<mode> --synced`. `service_commands()` keeps the
syncing spelling, since it is what everything outside the Makefile reads (AC-S04-39): the rewrite is a function in
`parallel_gate` applied by `makefile()` to the merged recipes of a project with a Python service.

In `verify_script()` the sync loop is skipped only when the second argument is exactly `--synced`:

```sh
mode="${1:-all}"
if [ "${2:-}" != --synced ]; then
  for app in $apps; do … uv sync --project "$app" --locked --quiet; done
fi
```

No environment variable is read. With no argument, or one, the script is today's.

**R2 — `check-python` first.** One line after the gate's rule: every prerequisite of the gate but `check-python`
itself names `check-python` (`sync` does too, above). In a serial run nothing moves: it is first in the list
already. The root's `npm ci` file target and the model tooling's are not checks and do not name it — a file target
that depended on a phony one would reinstall on every run — so under `-j` with an old `python3` an install may
start; no sync and no check does (AC-S04-13 as written).

**R3, R4 — the recipe.** `STAMPED` in `gate.py` becomes, in substance,

```make
VERIFY_GROUP := $(if $(filter output-sync,$(.FEATURES)),--output-sync=target)
verify: ## …
	@run=$$(…token); …reuse… || { "$(MAKE)" $(VERIFY_GROUP) --no-print-directory -f "$(firstword $(MAKEFILE_LIST))" verify-checks VERIFY_ORDER=1 && …record…; } || { echo 'verify: the gate did not pass; each failed check is named above on a line carrying ***'; exit 1; }
```

`reuse`'s exit 0 still ends the recipe at once; `record` always exits 0, so the last group runs only when the
checks failed. The exact sentence is the task's to settle against AC-S04-9 and the page. `ci` still hangs on
`verify-checks` and gets neither the grouping nor the order variable: `make -j ci` is not promised (D88).

**R5 — the families.** Inside `ifdef VERIFY_ORDER` … `endif` (GNU Make 3.81 has both), so only the gate's own
sub-make sees it and `make test` typed alone is what it was: with a Java service, `typecheck: lint` and `test:
typecheck`; otherwise, with a Go service, `lint test: typecheck` — Go's `typecheck` is the first `go` command to
resolve the workspace and write `go.work.sum` on a fresh clone (R-6), and one writer goes first. A project with
both takes the Java chain, which covers Go. Python and TypeScript need neither: after the sync and the root's
install their three checks write only their own caches (D88, R4 of that entry). The cost is said in the fragment:
under `-j` a Java gate's three native checks still run one after another, beside the gate's other checks.

**R6 — the adopted gate.** `gate_target()` returns its text with a line `.NOTPARALLEL:` and one comment above it
wherever it does not return the stamped gate — the refusal included, so the rule is *not stamped, serial*.
`ratchet-tighten`'s sub-make reads the same Makefile and is serial with it.

**R7 — the model tooling.** `MODEL_TARGETS` becomes one file target in the root's pattern and four targets that
name it:

```make
scripts/event-model/node_modules/.package-lock.json: scripts/event-model/package.json scripts/event-model/package-lock.json
	npm ci --prefix scripts/event-model --no-audit --no-fund --loglevel=error
	@touch scripts/event-model/node_modules/.package-lock.json
	$(eval MODEL_INSTALLED := yes)
check-drawio: scripts/event-model/node_modules/.package-lock.json ## …
	@$(if $(MODEL_INSTALLED),true,echo 'check-drawio: scripts/event-model/package-lock.json is not newer than the installed model tooling; not reinstalled')
	node … render-drawio.ts --check
```

(R-3 for the variable; R-4 for `npm ci --prefix`). `model`, `model-drawio` and `model-drawio-test` take the
prerequisite and lose their install line. The module's comment that the install is *repeated per recipe rather than
shared through a prerequisite* is rewritten. How a moved layout spells the paths is whatever it does for the
existing recipes; the task reads it before changing them. The lock is made by `npm install --package-lock-only` in
a directory holding only the shipped manifest (R-4) and committed as `assets/toolkit/scripts/event-model/package-lock.json`;
a factory test holds its root entry to the manifest's pins with no network. Whatever lists the toolkit's files
(the pruner, a manifest test, `delivery/.written`'s writer) is found by running the suite after adding it.

**R8 — the words.** The gate's page (`STAMP_PAGE`'s neighbour in `docs.py`) gains one paragraph from
`parallel_gate`, saying the six things of AC-S04-61. The fragment `changelog.d/parallel-gate.md` opens `MINOR` and
its **Catch-up.** is one paragraph that stands alone in the note `migrate` writes (iteration 12's lesson), followed
by migrating a project made at the commit before the slice.

## Pin

`delivery/survey/running.md` records the run path proven (S00) and `project.json` records `smoke`. Behaviours this
slice changes, each in `delivery/survey/pinned.md` before implementation: what a generated project's `make verify`
runs, in order, with its closing line, and the `verify` rule of an adopted repository byte for byte (both pinned
already, the 2026-10-04 rows from S03 — named, not re-pinned; their suites are the ones AC-S04-63 amends); what
each mode of the Python `scripts/verify` runs first, and the recipes of `install`, `migrate` and `dev` on a Python
project; and the four model targets' recipes — each pinned by `/characterise`, one at a time, where no test holds
it now.

## Branch and integration

As D12: increments land on `adopt-method`, one slice at a time, no `slice/` branch, nothing pushed. The demo runs
this checkout's `./slipwai` to generate projects under a temporary directory and runs their own gates with the real
toolchains ([quickstart.md](quickstart.md)).

**Not run, and said so on the board:** GNU Make 3.81 and 4.3 (none on this machine; `.FEATURES`, `$(eval)`,
`ifdef` and prerequisites are read from make's NEWS, R-1 to R-3); Windows under Git Bash and macOS; `npm ci` from
the shipped lock on any platform but this one. **Run with the real toolchain here:** the Python, Go, TypeScript
and Java (Quarkus) starters (R-6, and again at the demo); the Spring starter is read.

## Deliberate stubs

None.

## Complexity Tracking

Empty.

## What changed after this plan was written

The plan above is as the plan stage left it, with the skip line's words brought up to date. Where the slice ended
elsewhere, the decisions say why and `tasks.md` says what landed: the model tooling's marker is a file of the recipe's own,
`scripts/event-model/node_modules/.installed`, and `install` names it (D93, D96); the install is spelled `npm --prefix
scripts/event-model ci`; the gate-only order is read only from make's command line (`$(origin VERIFY_ORDER)`), and Go's is
`typecheck test: lint` (D96); the two install markers wait for `check-python` by an order-only prerequisite inside that
guard, and `check-ux-gates` and a TypeScript `check-openapi` wait for `build-packages` (D96); the adopted directive sits
inside `ifeq ($(words $(MAKEFILE_LIST)),1)` (D95); `VERIFY_GROUP` is defined with `override` and the skip line says what
make compared (D97).
