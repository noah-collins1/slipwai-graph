# Implementation Plan: S43-test-declarations — a change that reaches one starter stops paying the whole factory suite

**Branch**: `slice/S43-test-declarations` (local, cut from `adopt-method` at `063c187`; no push; not rebased — D188 rebases
it onto `adopt-method` only after S26 merges, and the host does that) | **Date**: 2026-10-07 |
**Spec**: `### S43-test-declarations` as amended on `adopt-method` at `89ca20c` (AC-S43-1 … AC-S43-14; AC-S43-6 and
AC-S43-11 amended, AC-S43-12 … 14 new), FR-048, SC-016

**Input**: D169, D179–D182, **D187** (the literal-argv rule and the narrowed audit), **D188** (AC-S43-6 is measured on the
merged tree), S38's D156–D158, D164, D165; the measured table [runtime-table.md](runtime-table.md) (AC-S43-1, `3a9c808`);
[research.md](research.md). The decisions and the amended criteria live on `adopt-method` (`89ca20c`), read from there
and not merged into this branch (host's word).

## Summary

The selector learns one thing (D187 rule 1–3): a **fully literal** `[str(ROOT / "slipwai"), "generate", …]` argv is read as
the equivalent `generate(` call, so a fixture that generates python through the launcher no longer counts as every
configuration. The reads-only audit narrows to the declared reads-only modules a run selects (D187 rule 4), the full
audit staying wherever no selected set is handed over. Then, in the table's order, the heavy modules and the helpers they
import are declared, after the borrowed non-generating helpers move into declared helper files (D179 (b)) so the join no
longer drags in `test_adopt`'s, `test_candidates`'s or `parallel_gate`'s launcher routes. Selection only: no test's
behaviour changes, and a full run has the same test ids (AC-S43-9). **No bump**: `scripts/select_tests/` and `tests/`
are not in the wheel.

## Status and the estimate the host should see now

**Expected outcome of AC-S43-6: a miss.** The per-name probe (`/tmp/s43w/ideal.py`: the scratch selector with the
argv rule, every module declared as narrowly as the names it actually uses allow, the `".git" / "slipwai"` false route
rewritten) still runs ≈ 2641 s of the 3448 s on a Go change; less the non-go share of `test_matrix` and `test_images`
(already narrowed by S38, ≈ 380 s), ≈ **2250 s**, before any of this slice's work is measured. What keeps it there:
the siblings' modules (570.7 s, of which S26's are declarable only after its merge, D188), `test_adopt.slipwai`'s
`./slipwai adopt` route and `test_add_service`'s `add-service` (≈ 500 s; D187 rule 3 keeps them every axis),
`stamp_fixture.load_script`'s `importlib` in generating closures (≈ 250 s; D164 rule 4 voids them), and the modules
that generate go or a computed backend (≈ 650 s). D187 rule 7 says to measure after the work and leave a miss to D182
(a person's word); this plan does that, and says it now so the question can be put early.

## The example map

| Rule | Criteria | Examples |
|---|---|---|
| **R1** a fully literal launcher `generate` argv resolves per axis | AC-S43-12, -14, -11 | e1 `[str(ROOT / "slipwai"), "generate", "fixture", "--profile", "standard", "--backend", "python", "--frontend", "none", "--http", "none", "--output", str(parent), "--skip-checks"]` is backend {python}, profile {standard}, frontend {none}, target every · e2 `ROOT / "slipwai"` without `str(…)` reads the same · e3 omitted `--backend` → every backend · e4 `--target aws` → target {aws}; `--event-store`/`--http`/`--auth`/`--users` (the catalog's `axes`) select nothing the declaration names · e5 the name and `--output`'s value may be computed |
| **R2** every unreadable form stays every axis and is held | AC-S43-12 | planted copies, each selected on a one-Go-file change and named by `held()`: a computed `--backend`; `*SHAPES[name]`; `[…] + flags`; a list variable; `shlex.split(…)`; `shell=True` string; an unmapped flag (`--language`, `--service-name`, `--no-init`, `--backend=go`); `add-service`, `migrate`, `adopt`, `replay`; `["slipwai", "generate", …]` on `PATH`; `python -m slipwai`; `refuse(` |
| **R3** a literal value the declaration omits voids it | AC-S43-14, -4 | e1 a copy of the stamp-style fixture declaring backend {typescript} with a literal `--backend python`: void, runs, `held()` names it · e2 one real `assets/languages/python/` path selects every importer of a literal-python fixture, the expectation from `generation.facts` |
| **R4** the audit covers what the run selected | AC-S43-13 | e1 a selected run hands the selected set to the modules it starts; the audit covers the declared reads-only modules in it · e2 a planted undeclared read is audited and fails when the change is the module itself, a helper in its closure, or a file its `reads` names · e3 no set handed over (full run, `TESTS=`, CI, the merge root): every module `LISTING` names |
| **R5** declarations, in the table's order, checked | AC-S43-1, -2, -3, -7 | e1 each newly declared module and helper is in a `real_*` list and `held()` names none · e2 for each (axis, option) any declaration names, one real path that pair claims selects every module whose facts generate that option or whose reads match · e3 the undeclared list, each with the selector's reason |
| **R6** restructuring changes nothing a test does | AC-S43-9, -10 | e1 the full run's test ids at the slice's tip equal those at `063c187` · e2 a moved helper keeps its old import path (a re-export) so S07's and S26's branches merge · e3 a loop switched to `backends_under_test()` runs outside the `matrix` jobs, so CI's (module, backend) pairs are unchanged |

## Technical Context

**Language/Version**: Python 3.14, `unittest`. **Primary Dependencies**: none new. **Storage**: none.
**Testing**: `make test TESTS="…"` on the modules a change touches only (the machine is shared with S07 and S26; no full
run, no `make verify`). **Project Type**: the factory's own test tree and its selector. **Constraints**: every file under
`tests/`, `scripts/` held to 350 lines (`scripts/check-structure.py`); the selector's rules change only as D187 says,
D164 rules 1, 2 and 4 unchanged (AC-S43-11); no `unittest.mock` in new code.

## Constitution Check

- **Additive gates (a scoped gate MUST be additive):** the full run, CI and the merge root keep the full audit and the
  full suite; the argv rule fails closed on every form it cannot read (R2). Pass.
- **Fakes, not mocking frameworks:** the planted copies and scratch trees are files written by the test. Pass.
- **Size and structure:** new logic goes in new files (below), no file over 350. Pass.
- **Versioning:** nothing user-visible; no bump, no fragment (AGENTS.md table: `tests/` and `scripts/select_tests/` do not
  ship). Pass.

## Structure decision

New files:

- `scripts/select_tests/argv.py` — reads one `ast.List` as a literal launcher `generate` argv and returns its axes, or
  None. `generation.facts` (312 lines) calls it: a list it reads becomes a `Call`, and the launcher node inside it is not
  also reported as a route. Every other route stays. The axis flags are `--backend` (→ backend), `--profile`,
  `--frontend`, `--target`, and the catalog's `axes` keys read from `catalog.json` by the caller (they select nothing a
  declaration names); `--output` (one value) and `--skip-checks` select nothing; anything else is None.
- `tests/test_select_tests_argv.py` (and `_argv_forms.py` if one file would pass 350) — R1–R3 against scratch trees.
- `tests/test_select_tests_audit_narrow.py` — R4.
- `tests/test_select_tests_real_s43.py` — the slice's `real_*` list (`DECLARED`, `HELPERS_S43`) with R5 e1–e2; imported by
  `test_select_tests_real_declared.py` beside the existing lists.
- Helper files for D179 (b), each declaring its own `TEST_SELECTION`: named in the tasks per group (e.g.
  `tests/gate_rules.py` for `test_verify_stamp_pinned.gate_prerequisites`/`gate_rule`, `tests/git_helpers.py` for
  `stamp_fixture.git` and `test_replay.git`, `tests/mutation_env.py` for `test_mutation_borders.clean_environment`); the
  old module re-exports each moved name.
- `specs/001-faster-slipwai/slices/S43-test-declarations/undeclared.md` — AC-S43-7's list, written from `declarations.scan`
  at the slice's tip.

Edited: `scripts/select_tests/generation.py` (the hook only), `scripts/select-tests.py` (hands the selected set to the
modules it starts, in an environment variable `SELECTED_TEST_MODULES`, and removes it for a full run),
`tests/test_select_tests_real_audit.py` (`LISTING` filters by the variable where set), the declared modules and helpers.

## Order of the declarations (the table's, among what can be declared)

Groups, each one task, each ending with `held()` clean for what it declared and the group's modules run:

1. **codegraph/health** — `test_codegraph_memory` 60.2, `test_health_memory` 58.0, `test_health_memory_states` 53.2,
   `test_codegraph_races` 38.8, `test_health_narrowed` 36.0, `test_codegraph_narrowed` 30.6, plus their helpers
   `test_code_index_health`, `test_cruise_index`, `test_cruise_runner` (≈ 277 s). Cut: `test_cruise_runner` imports
   `test_verify_stamp_pinned.gate_prerequisites`, whose file imports `test_candidates` → `test_adopt` (launcher). Move
   `gate_prerequisites`/`gate_rule`/`gate_target_name` to `tests/gate_rules.py`.
2. **render** — `test_render_current` 46.2, `_files_report` 23.4, `_files` 19.5, `_links` 18.5, `_failures` 16.0, `_once`
   13.1, `_browser` 8.4, `_pinned`, `_docs` (≈ 160 s). `render_fixture` narrows from `"every"` to what
   `RenderCase.project` generates (`self.generate(directory, name)`: typescript, event-modelling, none), and drops the
   `["slipwai"]` list from its own `reads` — a one-element list whose first element is `"slipwai"` is the launcher on
   `PATH` to the selector (D164 rule 3); `support`'s `reads` already carries it into the join.
3. **`test_factory_gate_stamp`** 46.4 — `self.repo / ".git" / "slipwai"` is read as the launcher by path (a `/ "slipwai"`
   chain); written `self.repo / ".git/slipwai"` it is the same path and no route. Its `ROOT / name` copies are named in
   `reads`.
4. **mutation** — `test_mutation_scope_real_spring` 31.7 (and what else shares the cut): move `stamp_fixture.git` and
   `test_mutation_borders.clean_environment` to helper files.
5. **Then down the table** while each next module is declarable, ≥ 5 s first; the rest stays undeclared and goes on
   AC-S43-7's list with the selector's reason. S26's modules wait for the host's rebase (D188 item 2); S07's are left.

## Modules this slice and a sibling may both touch

S07: `test_verify_scoped_*`, `test_verify_scoped_table_held` (new), the ux-gates tests — they import `scoped_fixture`,
`test_scoped_targets`, `test_verify_stamp_scan`, `stamp_fixture`. S26: `test_decisions_*`, `test_hand_backs_record`,
`test_result_contract_briefs`/`_stops`, the check-decisions and cruise-brief tests. This slice edits none of them. A
helper they import that moves (`stamp_fixture.git`, anything from `test_verify_stamp_pinned`) keeps its old name by a
re-export, so their branches merge cleanly.

## Pin (stage 3)

Factory code needs no pin: its tests are the pin. Behaviour is held by AC-S43-9 (same test ids at tip and base,
quickstart step 4) and by running each touched module before and after its move.

## Open questions

None open. The four questions of the blocked plan were answered by D187 (1, 2) and D188 (3); (4) stays with D182 and is
expected to be asked after the measurement (above).
