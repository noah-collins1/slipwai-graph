# Implementation Plan: S43-test-declarations — a change that reaches one starter stops paying the whole factory suite

**Branch**: `slice/S43-test-declarations` (local, cut from `adopt-method` at `063c187`; no push) | **Date**: 2026-10-07 |
**Spec**: [spec.md](../../spec.md) → `### S43-test-declarations` (AC-S43-1 … AC-S43-11), FR-048, SC-016

**Input**: the slice's split and graph rows in [story-split.md](../../story-split.md); D169 (the owner's), D179–D182 and
S38's D156–D158, D164, D165 in [decisions.md](../../decisions.md); the gaps report
(`/home/noahc/math/.cruise27/gaps-S43.md`); the measured run, [runtime-table.md](runtime-table.md) (AC-S43-1, committed
`3a9c808`). Research: [research.md](research.md).

## Status: BLOCKED at plan — D179's *would reverse if* holds

**AC-S43-1 is done** (`3a9c808`): 373 modules at `063c187`, 3448 s wall on the reference machine, the per-test sums
3415.6 s (99.1% of it). The one error in the run was environmental and is named in the table (the host's word).

**The table shows D179 (b) cannot meet AC-S43-6.** [research.md](research.md) R-2 to R-5: on a one-Go-file change, at
least ≈ 2329 s of modules keep running whatever (b) does — 569 s the siblings' modules this slice must leave undeclared,
580 s whose own source runs the launcher or `refuse(`, and 1180 s that generate nothing themselves but either import a
fixture that generates a literal configuration through `./slipwai` (`stamp_fixture`, `parallel_gate`,
`scoped_fixture`, `render_fixture`) or would become reads-only declarations the audit re-runs (D181). (b) can save at
most ≈ 480 s beyond what S38's selector already saves; the gap to 900 s is 2548 s. D179 says that, in this case, "(b)
could not then meet acceptance, and the launcher rule would have to be decided first, as its own decision" (condition 4),
and the brief says to return the question rather than change a rule. Nothing has been declared or moved.

## Open questions (for the host; a person's where marked)

1. **The launcher rule (D179 option (c), D164 rule 3).** May the selector resolve a *literal* `./slipwai generate` argv
   per axis — `--backend python --profile standard` is the python and standard configurations, not every one — as it
   already resolves `FactoryTestCase.generate`'s literal arguments? That is the only change the table shows reaching the
   1060 s of fixture importers and most of the 580 s of own-route modules; `add-service`, `migrate`, `adopt` and
   `replay` argv would need their own reading (or stay every). It is a selector rule change, which D169 allows only
   when a declaration cannot be expressed — and here one cannot: a fixture that generates python through the launcher
   has no declaration that skips it on a go change. D164 put rule 3 in after a reproduced false skip, so the decision
   has to say how a literal argv is held (e.g. resolved like a `generate(` call: a computed part is every option).
2. **The audit (D181's *would reverse if*).** The table shows the reads-only modules are not cheap once the launcher
   routes are gone: up to 1180 s would be declared reads-only and re-run by `test_select_tests_real_audit` on every
   run. Does the audit narrow to the reads-only modules a change reaches (it would still run each declared module
   whenever that module runs, and every one on a full run)?
3. **The sibling-claimed modules (569 s).** S07 and S26 claim `test_verify_scoped_*`, the ux-gates and
   check-decisions tests and `test_result_contract_briefs`; undeclared, they run on every change. Is AC-S43-6 measured
   only after those merge and a follow-up declares them, or with them running?
4. **The target (D182, a person's word).** If (1) is not taken, no reading of D179 (b) reaches 900 s: the bound is about
   2540 s selected on a go change (estimated; ≈ 3020 s today, also estimated from the table). Relax the 15 minutes, or take (1) and (2)?

**Recommendation from the numbers, not a decision:** take (1) and (2) together as one named decision for this slice,
measure after (b) and those, and keep (3) as an explicit exclusion of the 569 s from AC-S43-6's run until S07/S26 merge
— or, if (1) is refused, put (4) to a person now, since (b) alone repeats demo 2's outcome by about 500 s.

## What the slice would do once unblocked (outline only — no tasks written)

- **Order:** the table's, top-down among the declarable: the own-generating B′ modules and class D first
  (`test_mutation_stamp_untouched` 34.6, `test_mutation_scope_real_spring` 31.7, `test_confirm` 23.3,
  `test_parallel_gate_carry` 16.9, `test_verify_stamp_scan` 16.7, `test_verify_stamp_ships` 15.7, `test_render_once`
  13.1, `test_parallel_gate_output` 12.8, `test_gate_walks_pom` 10.0, …), then class C's backend loops.
- **Helper files (D179 (b)):** `tests/git_helpers.py` (`git` from `test_replay` and `stamp_fixture`, `newer_factory`),
  `tests/launchers.py` (`slipwai`, `migrate`, `add_service`, `replay` wrappers), each declaring its own
  `TEST_SELECTION` and added to a `real_*` list; the old names re-exported from `test_replay`, `test_adopt`,
  `test_migrate`, `test_add_service` and `stamp_fixture` so S07's and S26's branches still merge cleanly (host's word,
  iteration 27). Every new file under 350 lines.
- **Loops (AC-S43-10):** only `.github/workflows/verify.yml`'s `matrix` jobs set `FACTORY_BACKENDS` and they run only
  `test_matrix test_images`; every other module runs in `checks` (or a job with no `FACTORY_BACKENDS`), where
  `backends_under_test()` returns every backend — so switching a module outside those two leaves CI's (module, backend)
  pairs the same by construction.
- **Pin (stage 3):** factory code needs no pin; its tests are the pin. AC-S43-9 (same test ids) is the slice's check.
- **Modules both this slice and a sibling might touch:** `test_verify_scoped_*` (S07; they import `scoped_fixture`,
  `test_scoped_targets`, `test_verify_stamp_scan`, `stamp_fixture`), `test_decisions_*` and `test_hand_backs_record`
  (S26 via `test_decisions_scope`), `test_result_contract_briefs`/`_stops` (S26), `test_ux_gates_scale`
  (S07, imports `test_design_extensions`). This slice would edit none of them; a helper they import keeps its old name.

## Technical Context

Python 3.14, `unittest`; the selector under `scripts/select_tests/` (unchanged, D179 condition 3); `tests/` only.
No bump, no fragment: nothing under `tests/` or `scripts/select_tests/` is in the wheel (`pyproject.toml` force-includes
`assets`, `catalog.json`, `VERSION`, `CHANGELOG.md`, `changelog.d`).

## Constitution Check

Not reached: the slice stops before design on a question its artifacts do not settle. Nothing was written outside
this slice's folder.
