# Implementation Plan: S33-factory-gate-stamp — the factory's own gate returns at once on a tree it already passed

**Branch**: `adopt-method` (D12 — no `slice/` branch, no claim, no push) | **Date**: 2026-10-04 |
**Spec**: [spec.md](../../spec.md), *Slice acceptance criteria* → `### S33-factory-gate-stamp` (AC-S33-1 … AC-S33-10)

**Input**: the slice's row and graph row in [story-split.md](../../story-split.md); decisions D91, D99, D100 and
D101 in [decisions.md](../../decisions.md). Written by cruise iteration 14 (host, strong model).

## Summary

The factory's `make verify` runs lint, typecheck, check-structure and the whole suite every time — about forty
minutes here — and a cruise slice pays it several times on trees that have not changed in between. This slice puts
the verify stamp S03 gave every generated project in front of the factory's own gate: `verify` asks
`assets/toolkit/scripts/verify-stamp.py reuse` first and runs the four checks, through a new `verify-checks`
target, only where the key moved; `record` writes the stamp after they pass. The script runs where it ships,
unchanged (R-1), so `S32` is not owed (D91). `TESTS` and `SKIP` bypass the stamp (D100); the key asks the machine
for each tool the suite looks for that is on `PATH` (D100). No bump: the root `Makefile` and `tests/` reach no
user, and nothing a generated project receives changes.

**The root `Makefile` is a control the cruise guard refuses an iteration to edit (D99, D101).** The change is
therefore prepared, and checked, as one patch — [`s33.patch`](s33.patch), the `Makefile`'s lines and the test
module that holds them — which a person reads and applies:

```sh
git apply specs/001-faster-slipwai/slices/S33-factory-gate-stamp/s33.patch
make lint typecheck check-structure && make test TESTS=test_factory_gate_stamp
git commit -m "S33: the factory's gate asks the verify stamp first (applied by hand; no bump — reaches no user)" -- Makefile tests/test_factory_gate_stamp.py
```

Until it is applied the slice is blocked (⛔), and the run takes `S05-xdist`. The iteration after it lands
re-enters at convergence.

**Applied by the owner at `cab6cda`. Converge (iteration 16) found what it let through, and the fix is a second
patch, [`s33-2.patch`](s33-2.patch), over the tree as it stands after `e997a5f` (D113):**

```sh
git apply specs/001-faster-slipwai/slices/S33-factory-gate-stamp/s33-2.patch
make lint typecheck check-structure && make test TESTS="test_factory_gate_stamp test_factory_gate_stamp_inputs test_factory_gate_stamp_scan test_factory_repository test_extensions"
git add tests/test_factory_gate_stamp_inputs.py tests/test_factory_gate_stamp_scan.py
git commit -m "S33: the stamp's bypass and key close what converge found (applied by hand; no bump — reaches no user)" -- Makefile tests/test_factory_gate_stamp.py tests/test_factory_gate_stamp_inputs.py tests/test_factory_gate_stamp_scan.py
```

Until it is applied the slice is ⛔ again, and the run takes `S06-scoped-gate`; the iteration after it lands
re-enters at T009 (after-converge gaps).

## The example map

| Rule | Criteria | What it says | Examples |
|---|---|---|---|
| **R1** a tree that passed is not judged again off the trunk | AC-S33-1, -2, -7 | `verify` = `reuse` ‖ (`verify-checks` && `record`) | e1 pass, run again: no check starts, one line, exit 0 · e2 a tracked file changes: full run · e3 a check fails: non-zero, no stamp, next run full |
| **R2** the trunk, CI and force always run in full | AC-S33-3, -4 | The script's own `standing()` and `VERIFY_FORCE` | e1 `VERIFY_FORCE=1`: every check, the forced line · e2 `CI=1`: full, no stamp written · e3 on `main`: full, no stamp written |
| **R3** a slice of the suite is not the gate | AC-S33-5 | `TESTS` or `SKIP` set: `verify-checks` straight, the script never called | e1 a pass then `make verify TESTS=x`: checks run, the stamp file is untouched |
| **R4** the tools the suite looks for are in the key | AC-S33-6 | `--tool` for each of the list found on `PATH`; `--make "$(MAKE)"` | e1 a stand-in `tofu` put on `PATH` after a pass: full run · e2 a stand-in `node` answering another version: full run |
| **R5** nothing else moves | AC-S33-8, -9 | The script unchanged and not copied; other targets and CI unchanged; `make help` line | e1 `make help` shows the verify line · e2 no second copy of the script in the tree |

## Technical Context

**Language/Version**: GNU Make (4.4.1 here; the recipe uses nothing newer than 3.81 — `$(foreach)`, `$(if)`,
`$(shell)`, `ifneq`), Python ≥3.10 for the script and the tests. **Testing**: `unittest`, in
`tests/test_factory_gate_stamp.py` (new; under 350 lines). The tests copy the root `Makefile`, the script and
`check-slice-scope.py` beside it into a temporary git repository with a `project.json` recording `ci.branch`
`main`, and replace `./scripts/verify`, `scripts/check-structure.py` and `python3 -m unittest` targets' work with
stand-ins that append to a log — fakes in the test tree, no mocking framework (`AGENTS.md`, *Delivery method*).
**Performance**: the key over this tree took 0.6 s (spec, S33's gaps note); the demo measures the second
`make verify`. **Constraints**: the script is run in place (R-1); `sh` is not asked (D100).

## Constitution Check

The factory's own `make verify` stays the gate CI runs — CI sets a marker and never reads a stamp (owner brief,
first priority: the merge root and CI run the full gate). A stamp is keyed on the whole tree, the gate's scripts,
the tools and the history (S03's key), so it cannot vouch for a tree it did not judge (fifth priority). No new
dependency.

## Structure Decision

This repository only: the root `Makefile` (a control — by the patch) and `tests/test_factory_gate_stamp.py`. No
file under `assets/` or `src/` changes; no service, no bounded context.

## Pin

No code that was here changes behaviour on a tree that has not passed: the first `make verify` runs the four checks
it ran before, in the same order, through `verify-checks`. The tests hold that ordering (R1 e2 compares the log).
