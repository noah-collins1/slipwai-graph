# Implementation Plan: S38-factory-test-selection — the factory's own `make test` on a slice branch runs the modules a change can reach, and names the rest

**Branch**: `slice/S38-factory-test-selection` (local, cut from `adopt-method` at `8072724`; no push) | **Date**: 2026-10-06 |
**Spec**: [spec.md](../../spec.md), *Slice acceptance criteria* → `### S38-factory-test-selection` (AC-S38-1 … AC-S38-17),
FR-048, SC-016

**Input**: the slice's row and graph row in [story-split.md](../../story-split.md); D156, D157, D158 and the entries they
cite (D117, D119, D125, D128–D132, D138 item 4, D153) in [decisions.md](../../decisions.md); the pre-planning gaps
report (iteration 24, `drive-gaps`); `.specify/product-owner.md`. Written by cruise iteration 24 (`drive-slice`, host
model, in the slice's worktree). Research: [research.md](research.md); shapes: [data-model.md](data-model.md); the
demo's steps: [quickstart.md](quickstart.md).

## Summary

Every slice here pays the factory's whole suite — about forty minutes — whatever it changed. This slice gives the
root `make test` a selector, `scripts/select-tests.py`: on a `slice/<id>` branch it measures the change against the
trunk, or against the tree `SINCE=<ref>` names (D156), maps each changed path to the starter configurations and files
it can reach, and runs only the test modules whose declaration reaches one of them, plus every module that declares
nothing. It narrows `FACTORY_BACKENDS` for the modules only a backend's assets selected. Every module it leaves out is
named with one reason, before the tests start. Wherever the effect cannot be established — the catalog, the pruner,
the generator, the gate's own files, an ignored file, a path no rule claims — and wherever the full suite is the rule
— the trunk, `adopt-method`, any other branch, a detached `HEAD`, CI, `RATCHET_TIGHTEN`, `FULL=1` — it runs every
module and says why in one line. `make verify` always runs every module and keeps S33's stamp; `TESTS`, `SKIP` and
`FACTORY_BACKENDS` turn selection off and run exactly what they ask (D158).

Selection only (G12): no parallelism, no change to how a test runs. The selector reuses the scoped gate's change
functions by loading `check-slice-scope.py` and `verify_scoped/changes.py` where they ship, unchanged (research R-1).
**No bump**: nothing under `assets/`, `src/slipwai/` or `catalog.json` changes; `VERSION` and `changelog.d/` stay as
they are (AC-S38-17, R-8).

**The root `Makefile` is a control the cruise guard refuses an iteration to edit (AC-S38-14, as S33's D99/D101).** Its
change — the `test` recipe calls the selector, `verify` passes `FULL=1` to `verify-checks`, and the comments say so — is
prepared in a scratch clone under `/tmp/s38/` and exported as [`s38.patch`](s38.patch), which a person reads and
applies on this branch:

```sh
git apply specs/001-faster-slipwai/slices/S38-factory-test-selection/s38.patch
make lint typecheck check-structure && make test TESTS="test_select_tests_makefile test_select_tests_make"
git commit -m "S38: the factory's make test selects on a slice branch; make verify stays whole (applied by hand; no bump — reaches no user)" -- Makefile
```

Until it is applied, the tests that need it fail with a line naming the patch, and the demo cannot run.

## The example map

| Rule | Criteria | What it says | Examples |
|---|---|---|---|
| **R1** only a slice branch selects | AC-S38-1, -4 (c), -7, -13 | Data-model *full* rows 1–7, in order | e1 on `main`, `adopt-method`, `feature/x`, a detached `HEAD`: every module, one line naming the case · e2 `CI=1` (and `GITHUB_ACTIONS`, `GITLAB_CI`) on `slice/x`, with `SINCE` too: the CI line · e3 `RATCHET_TIGHTEN=1`: full, line names it · e4 `FULL=1`: full · e5 `FACTORY_BACKENDS=go`: selection off, run as asked · e6 `GIT_DIR` set: full, named |
| **R2** the base is the trunk, or what `SINCE` names | AC-S38-2, -3, -4 (b) | Data-model *The base*; rows 8–10 | e1 slice cut from `main`, one go path, `origin/main` level: the trunk line, one path selects · e2 slice cut from `adopt-method`, `SINCE=adopt-method`: the SINCE line, tree comparison, not merge-base · e3 `SINCE=nonexistent`, `SINCE=<unrelated root>`: full, *could not be resolved — why* |
| **R3** the change set is the scoped gate's | AC-S38-5, -10 (ignored) | `changes.changed` + `unpushed`; ignored files | e1 untracked new file under `assets/languages/go/`: go modules run · e2 a deleted one: same · e3 unpushed `main` commit touching `catalog.json`: full, D153's words · e4 an ignored non-cache file under `src/`: full · e5 a `__pycache__` under `tests/`: no effect |
| **R4** what cannot be established runs everything | AC-S38-4 (a), -8 (b), -10, -14 (b) | Data-model *path rules*, the **full** rows | e1 `Makefile` and `catalog.json` changed: full, first path and its rule named · e2 each listed path, one at a time · e3 `assets/newthing/x`: *no rule claims it* · e4 a top-level file no row claims: full |
| **R5** a module reads what it declares; an undeclared one always runs | AC-S38-8 | `TEST_SELECTION`; the configuration rows; R-5's cross-reads | e1 one go path: go declarers, *every* declarers and undeclared run; the rest skipped *reads no go configuration* · e2 `assets/languages/typescript/biome/x`: react-vite declarers run too · e3 a declaration naming a missing option or path fails its test · e4 a declared module importing an undeclared helper: undeclared |
| **R6** the test tree selects by its own imports | AC-S38-10 (fixture), -11 | Module, helper and `reads` rows for `tests/` | e1 `tests/test_x.py` edited: `test_x` runs, every other declared module skipped · e2 `tests/scoped_fixture.py` edited: exactly its importers, transitively · e3 a deleted test module: no error, not listed · e4 a `tests/fixtures/…` file: its readers |
| **R7** a backend's change narrows the matrix | AC-S38-9 | Data-model *Narrowing* | e1 one go path: `test_matrix` runs with `FACTORY_BACKENDS=go`, the line names the four left out · e2 go path plus a toolkit path: `test_matrix` not narrowed |
| **R8** every skip is named, and a dry run shows it | AC-S38-12, -15 (replay) | Data-model *What a run prints* | e1 a selected run: each skipped module once, one reason, before the tests; summary line before and last · e2 `--dry-run`: the same lines, nothing runs · e3 `--dry-run --replay A..B`: the range's paths, current declarations |
| **R9** the root `Makefile`, by patch | AC-S38-6, -13, -14 | `test` → selector unless `TESTS`; `verify` → `verify-checks FULL=1`; bypass list unchanged | e1 the recipes and the bypass list equal the held text; unpatched: the failure names `s38.patch` · e2 `make verify` on a slice branch with a one-backend change: every module, stamp recorded · e3 `make verify TESTS=x`: no stamp touched · e4 `make test SKIP=test_matrix`: all but it, *selection off: SKIP given* |
| **R10** selection only, and proven sound | AC-S38-15, -16, -17 | Demo (host); scope held by diff | e1 the four replays printed · e2 go-asset and toolkit-script faults: the selected run fails every module the full run fails · e3 `git diff --stat 8072724 -- assets src/slipwai catalog.json` empty |

## Technical Context

**Language/Version**: Python ≥3.10, standard library only (`ast`, `importlib.util`, `subprocess`); GNU Make (the
recipe uses nothing newer than 3.81). **Where the code goes**: `scripts/select-tests.py` (the entry: arguments, the
order of *full* rows, running `unittest`) and a package `scripts/select_tests/` (`base.py` — the base and the change
set, loading the scoped gate's scripts; `rules.py` — the path rules and R-5's cross-reads, from `catalog.json`;
`declarations.py` — `TEST_SELECTION` by `ast`, the import graph; `choose.py` — selection and narrowing; `report.py`
— the lines). `scripts/` has no line budget, but no file there should outgrow 350 lines either. **Testing**:
`unittest`, new modules `tests/test_select_tests_*.py`, each ≤350 lines. They build temporary git repositories holding
the selector, `assets/toolkit/scripts/check-slice-scope.py` and `verify_scoped/` copied in (as S33's tests copy the
stamp), a `project.json` recording `ci.branch` `main`, a small `catalog.json`, and stand-in `tests/test_*.py` modules
that append their name and `FACTORY_BACKENDS` to a log — fakes in the test tree, never `unittest.mock`. Evidence is
the log, never a printed line alone. Every module that loads a script sets `sys.dont_write_bytecode`; every
`subprocess.run` carries a timeout; no wall-clock assertion. The real tree's declarations, the path map's cross-reads
and the Makefile text are held by tests over the repository itself. **Performance**: selection costs under a second
(R-1); the demo reports elapsed time against a same-commit full run, without a threshold (D157).

## Constitution Check

- **I — a scoped gate is additive.** The merge root (`adopt-method` here, the trunk in general) and CI run every
  module: R1 rows 3, 6 and 7; `make verify` passes `FULL=1` (R-3), so the stamped gate never judges a selected run.
- **Owner priority 5 — no false green.** Every doubt broadens: an undeclared module runs; an unclaimed path, an
  ignored file, an unresolvable base, unloadable scripts, a repository-locating `GIT_*` variable each run everything.
  The soundness check (AC-S38-16) is the pass condition, not the timing (D157).
- **XIV / one scenario per commit**: each RED-GREEN-REFACTOR increment is committed by path; `make lint typecheck
  check-structure` before every commit.
- **Testing without mocks**: fakes written in the test tree (`AGENTS.md`, *Delivery method*).
- No new dependency. No change to a shipped file.

## Structure Decision

This repository only: `scripts/select-tests.py`, `scripts/select_tests/`, new `tests/test_select_tests_*.py` and,
where a module is declared, one `TEST_SELECTION` assignment added to it (helpers included); `docs/maintaining.md`
(*Verify it*: what `make test` does on a slice branch, `SINCE` — its default, the trunk, and one sentence on when to set
it (D156) — `FULL=1` and the dry run); the root `Makefile` by `s38.patch`. **Not edited**: anything under `assets/`,
`src/`, `delivery/`, `.github/`, `tools/`; `scripts/verify`; `catalog.json`; `VERSION`; `changelog.d/`; the decision
log, `spec.md`, `story-split.md`.

**Which modules are declared in this slice.** The backend readers of research R-4 that narrow by `FACTORY_BACKENDS`
(where a reading proves what they generate), the real-toolchain mutation modules (`go`, `java-spring`), and the
modules that generate nothing and load a toolkit script by path, with the helpers they import (`support`,
`stamp_fixture`, `scoped_fixture` and the rest as needed). Each declaration is a claim a reading proves; any module
where it does not stays undeclared and always runs. The list each task declares is its manifest. More declarations
are later work, and each is safe to add alone.

## Pin

The factory's tests are the pin. Before the selector exists, `tests/test_select_tests_pin.py` holds what `make test`
and `make verify` do today, through the real root `Makefile` copied into a fixture repository: `TESTS=a b` runs exactly
those modules with `PYTHONPATH=src:tests`; `SKIP=a` runs every other; on `main` and on `adopt-method` every module runs
through `discover`; `make verify` runs every module. Green now, and green unchanged after the patch: on every branch
but a slice branch the patched `make test` runs what it ran before. `test_factory_gate_stamp*` stays green over the
patched `Makefile` (the stamp, its bypass list and `verify-checks` unchanged in behaviour).

## Where the Makefile work happens

The selector, its tests and the declarations are written and committed in this worktree. The `Makefile` change is
made in a scratch clone, `/tmp/s38/clone` (`git clone --quiet /home/noahc/math/slipwai-graph-S38-factory-test-selection
/tmp/s38/clone`, refreshed with `git -C /tmp/s38/clone pull --quiet` before the patch task), never in a worktree the
cruise guard watches; `git -C /tmp/s38/clone diff -- Makefile > …/s38.patch` exports it, and it is checked by applying
it to a second scratch copy at this branch's tip and running the tests that need it there. The tests that drive the
real `Makefile` (`test_select_tests_make`, `test_select_tests_makefile`) find the unpatched text and fail with
`the root Makefile is not yet patched — apply specs/001-faster-slipwai/slices/S38-factory-test-selection/s38.patch`.

## Open questions

None. D156–D158 settle the base, the demo and the twelve gaps; the plan's own choices — the axis rule (an unnamed axis
admits every option), two `unittest` processes for narrowing, an ignored file's presence as its change, the
`GIT_*` list — are recorded in [research.md](research.md) and [data-model.md](data-model.md) and fail closed.
