# tasks — S43-test-declarations

Feature 001-faster-slipwai. Plan: [plan.md](plan.md) (example map R1–R6, *Structure decision*, *Order of the declarations*).
Criteria: AC-S43-1 … AC-S43-14 as amended on `adopt-method` at `89ca20c`; decisions D187, D188, D179, D164 (read from that
commit, not merged into this branch).

**Rules for every task**

- One RED-GREEN-REFACTOR cycle, one commit, committed **by path** (only the files in the task's manifest), after
  `make lint typecheck check-structure` passes. No bump, no changelog fragment (`tests/` and `scripts/select_tests/` ship to nobody).
- Run only the modules the task names: `make test TESTS="<modules>"`. The machine is shared; never the full suite, never `make verify`.
- No `unittest.mock`; planted copies and scratch trees are files the test writes. No file over 350 lines
  (`make check-structure`); where a declaration would push one over, the move that shrinks it comes first in that task.
- Never touch `tests/test_verify_scoped_*`, the ux-gates tests, `tests/test_decisions_*`, `tests/test_hand_backs_record.py`,
  `tests/test_result_contract_briefs.py`, `tests/test_result_contract_stops.py` (S07 / S26, D188). A helper they import that
  moves keeps its old name by a re-export in the old file.
- A moved helper: the new file carries its own `TEST_SELECTION`, the old file re-exports the name (R6 e2), and a test in
  `tests/test_select_tests_real_s43.py` imports it from both paths and asserts they are the same object.
- Selection only: no test's behaviour changes (AC-S43-9).

## Phase 1 — the selector learns one rule (D187)

- [ ] **T001 — R1 literal launcher argv; AC-S43-12 (readable half), AC-S43-14 (both halves).**
  - **Manifest:** new `scripts/select_tests/argv.py`; `scripts/select_tests/generation.py` (312 lines; the hook only, stays
    under 350); new `tests/test_select_tests_argv.py`.
  - **RED:** against scratch trees, e1 `[str(ROOT / "slipwai"), "generate", "fixture", "--profile", "standard", "--backend",
    "python", "--frontend", "none", "--http", "none", "--output", str(parent), "--skip-checks"]` resolves to backend
    {python}, profile {standard}, frontend {none}, target every, so a one-Go-file change skips a module declaring exactly that
    and a `assets/languages/python/` path selects it; e2 `ROOT / "slipwai"` without `str(...)` reads the same; e3 omitted
    `--backend` is every backend; e4 `--target aws` is target {aws}, `--event-store/--http/--auth/--users` (the catalog's
    `axes`) select nothing the declaration names; e5 a computed name or `--output` value still reads. AC-S43-14 second half
    (real tree): one real `assets/languages/python/` path selects every importer of a literal-python fixture, the expected set
    derived from `generation.facts` over the real tests, not typed. Fails first because the launcher node is a route that
    counts as every configuration.
  - **GREEN:** `argv.py` reads one `ast.List` as `{backend, profile, frontend, target} -> frozenset | None` per
    [data-model.md](data-model.md) (axis flags read from `catalog.json` by the caller); in `generation.facts()` a read list
    becomes a `Call` at the list's line and the launcher node inside it is not also reported as a route; every other route stays.
  - **REFACTOR:** `argv.py` has one entry point; `generation.py` ≤ 350.
  - **Done when:** the module passes; D164 rules 1, 2 and 4 behave as before (`test_select_tests_generation` still passes).
  - **Run:** `make test TESTS="test_select_tests_argv test_select_tests_generation test_select_tests_declarations"`.
- [ ] **T002 — R2 every unreadable form stays every axis and is held; AC-S43-12 (second half), D187 rule 5.**
  - **Manifest:** new `tests/test_select_tests_argv_forms.py` (split from `test_select_tests_argv.py` territory; own file).
  - **Test:** a planted copy of a fixture module per form, each selected on a one-Go-file change set and named by
    `declarations.held()`: computed `--backend`; `*SHAPES[name]`; `[...] + flags`; a list variable; `shlex.split(...)`;
    `shell=True` string; unmapped flags (`--language`, `--service-name`, `--no-init`, `--backend=go`); literal `add-service`,
    `migrate`, `adopt`, `replay`; `["slipwai", "generate", ...]` on `PATH`; `python -m slipwai`; `refuse(`; plus R3 e1 (a copy
    declaring backend {typescript} with a literal `--backend python` is void, runs, and `held()` names it).
  - **RED (D187 rule 5, each case written to fail before the rule exists):** run each case once against a throwaway,
    uncommitted permissive reader in `argv.py` (treat any list starting with the launcher as readable) and see every form
    fail; then restore T001's reader and see them pass. The literal-python real-tree case is T001's, which is what makes it
    fail-then-pass; T002 is the fault-planting guard around it. **Flag to the host:** under today's rules these cases already
    pass (unreadable is already every axis), so T002 is a guard with no honest empty-GREEN-free cycle of its own; if the
    drive-implement refuses that, fold it into T001 (one commit, both files).
  - **GREEN:** nothing in production changes; the case set is the deliverable.
  - **Done when:** every form selects the copy on the Go change and is held; the permissive-reader trial fails each.
  - **Run:** `make test TESTS="test_select_tests_argv_forms test_select_tests_argv"`.
- [ ] **T003 [P] — R4 the audit covers what the run selected; AC-S43-13.**
  - **Manifest:** `scripts/select-tests.py` (190); `tests/test_select_tests_real_audit.py` (185); new
    `tests/test_select_tests_audit_narrow.py`.
  - **Parallel with T001/T002:** the files are disjoint from theirs (it touches neither `generation.py`, `argv.py` nor
    their tests); it waits for neither.
  - **RED:** (e1) a selected run hands `SELECTED_TEST_MODULES` (comma-separated module names) to every module it starts, both
    batches; the audit's `LISTING` covers only the declared reads-only modules in it; (e2) three planted undeclared reads,
    each audited and failing: in the changed module itself, in a helper of its closure, in a file its `reads` names; (e3) no
    variable set (full run, `TESTS=`, CI, merge root): `LISTING` is every module it names, and a full run removes the variable
    from the environment it passes down.
  - **GREEN:** `select-tests.py` sets the variable on a selected run and deletes it on a full run; `LISTING` filters when it is set.
  - **Done when:** the three planted-read cases and the full-run case pass.
  - **Run:** `make test TESTS="test_select_tests_audit_narrow test_select_tests_real_audit test_select_tests_full test_select_tests_narrow"`.

## Phase 2 — the slice's own `real_*` list

- [ ] **T004 — R5 e1–e2 scaffold; AC-S43-2, AC-S43-3.**
  - **Manifest:** new `tests/test_select_tests_real_s43.py` (`DECLARED`, `HELPERS_S43`, both empty at first);
    `tests/test_select_tests_real_declared.py` (49 lines; unions the new lists beside the existing ones).
  - **RED:** AC-S43-2 `declarations.held()` on the real tree names none of the listed modules or helpers; AC-S43-3 for each
    (axis, option) any listed declaration names, one real path that pair claims selects every module whose `generation.facts`
    generate that option or whose `reads` match (expectation derived, not typed). Fails first because the module and the union
    do not exist; with empty lists the checks are vacuous by design and every later task makes them bite.
  - **GREEN:** the module and the wiring.
  - **Done when:** `test_select_tests_real_declared`'s pinned-set test passes with the new union.
  - **Run:** `make test TESTS="test_select_tests_real_s43 test_select_tests_real_declared"`.

## Phase 3 — the declarations, in the table's order

Sequential: every one edits `tests/test_select_tests_real_s43.py`. Each task is: (1) RED — add the group's names to `DECLARED`
/ `HELPERS_S43` (and the moved-helper old-and-new import test) so the pinned-set and AC-S43-3 checks fail; (2) GREEN — move
borrowed helpers to a declared file with a re-export, declare the group; (3) `held()` clean; (4) run the group's modules plus
`test_select_tests_real_s43 test_select_tests_real_declared` and, for each moved module, the modules that import it by the old
name. Find importers with `delivery/scripts/codegraph callers <name>` before moving. If a module a task declares sits near 350
lines, any move that shrinks it comes first.

- [ ] **T005 — group 1 codegraph/health** (≈ 277 s; AC-S43-1, -2, -3, -9, -11).
  - **Manifest:** new `tests/gate_rules.py` (`gate_target_name`, `gate_prerequisites`, `gate_rule`, own `TEST_SELECTION`);
    `tests/test_verify_stamp_pinned.py` (148; removes the three defs, re-exports them); `tests/test_cruise_runner.py` (336;
    imports from `gate_rules`, declares, stays ≤ 350); `tests/test_cruise_index.py` (192); `tests/test_code_index_health.py`
    (337; declares, stays ≤ 350); `tests/test_codegraph_memory.py`, `tests/test_health_memory.py`,
    `tests/test_health_memory_states.py`, `tests/test_codegraph_races.py`, `tests/test_health_narrowed.py`,
    `tests/test_codegraph_narrowed.py`; `tests/test_select_tests_real_s43.py`.
  - **Why the move:** `test_cruise_runner` imports `test_verify_stamp_pinned.gate_prerequisites`, whose file imports
    `test_candidates` -> `test_adopt` (launcher routes), which the join drags into every closure.
  - **Done when:** `held()` names none of the nine; `gate_prerequisites` is the same object by both import paths; a Go path
    skips the six heavy modules.
  - **Run:** `make test TESTS="test_codegraph_memory test_health_memory test_health_memory_states test_codegraph_races test_health_narrowed test_codegraph_narrowed test_cruise_runner test_cruise_index test_code_index_health test_verify_stamp_pinned test_select_tests_real_s43 test_select_tests_real_declared"`.
- [ ] **T006 — group 2 render** (≈ 160 s).
  - **Manifest:** `tests/render_fixture.py` (339; `"every"` narrowed to what `RenderCase.project` generates — typescript,
    event-modelling, none — and the one-element `["slipwai"]` list dropped from its own `reads`, `support`'s carrying it into
    the join); `tests/test_render_current.py`, `test_render_files_report.py`, `test_render_files.py`, `test_render_links.py`,
    `test_render_failures.py`, `test_render_once.py`, `test_render_browser.py`, `test_render_pinned.py`,
    `test_render_docs.py`; `tests/test_select_tests_real_s43.py`. Any helper the modules import beyond `render_fixture` is
    moved the T005 way into a named new file the executor adds to this manifest before writing it.
  - **Done when:** `held()` clean; a Go path skips the render modules, a typescript or event-modelling path selects them.
  - **Run:** the nine `test_render_*` modules, `test_select_tests_real_s43`, `test_select_tests_real_declared`.
- [ ] **T007 — group 3 `test_factory_gate_stamp`** (46.4 s).
  - **Manifest:** `tests/test_factory_gate_stamp.py` (297; `self.repo / ".git" / "slipwai"` -> `self.repo / ".git/slipwai"`,
    same path and no `/ "slipwai"` route; the `ROOT / name` copies named in `reads`); `tests/test_select_tests_real_s43.py`.
    If its join still reaches `stamp_fixture.git`, create `tests/git_helpers.py` here (own `TEST_SELECTION`; `stamp_fixture.git`
    and `test_replay.git` moved there, the old names re-exported) and add `tests/stamp_fixture.py` (318) and
    `tests/test_replay.py` to this manifest; otherwise T008 creates it.
  - **Done when:** `held()` clean; the module skipped on a Go change.
  - **Run:** `make test TESTS="test_factory_gate_stamp test_select_tests_real_s43 test_select_tests_real_declared"` plus every
    module that imports a moved name (stamp, replay).
- [ ] **T008 — group 4 mutation** (`test_mutation_scope_real_spring` 31.7 s and what shares the cut).
  - **Manifest:** `tests/test_mutation_scope_real_spring.py` (69); `tests/test_mutation_borders.py` (226;
    `clean_environment` moves out, re-exported); new `tests/mutation_env.py` (own `TEST_SELECTION`); `tests/git_helpers.py`
    (create here if T007 did not), `tests/stamp_fixture.py`, `tests/test_replay.py` (the `git` moves, re-exported);
    `tests/test_select_tests_real_s43.py`.
  - **Done when:** `held()` clean; the moved names import from both paths.
  - **Run:** `make test TESTS="test_mutation_scope_real_spring test_mutation_borders test_select_tests_real_s43 test_select_tests_real_declared"` plus the modules importing a moved name.

## Phase 4 — down the table

- [ ] **T009 — the next declarable modules, one sub-task per group, ≥ 5 s first, stopping when the next is not declarable.**
  Same cycle as Phase 3. Candidates in the table's order after the groups above, skipping S07 / S26 claims (D188):
  `test_codegraph_bytes` (46.6 s; joins group 1), `test_refresh_owned` (37.0), `test_mutation_stamp_untouched` (34.6),
  `test_factory_gate_stamp_inputs` (29.3) and `_scan`, `test_refresh_strategy` (21.2), `test_uncommitted_subdirectory`
  (29.8), `test_model_install_first` (29.7), `test_xdist_carry` (29.2), the `test_verify_stamp_*` family (35.1 s and down).
  Each sub-task (T009a, T009b, …) starts by asking the selector why the module is undeclarable now
  (`scripts/select-tests.py --dry-run`, `declarations.scan`); a sub-task is written only when the reason is a borrowed helper
  that can move (D179 (b)) or a `reads` that can be stated. The `stamp_fixture.load_script` `importlib` closure voids a
  generating declaration (D164 rule 4); a module whose reach cannot be stated stays undeclared, goes on T010's list with the
  selector's reason, and ends the descent at that row. S26's modules wait for the host's rebase (D188 item 2): out of scope here.
  - **Manifest per sub-task:** the module(s), the helper file(s) it moves, `tests/test_select_tests_real_s43.py`; the
    executor writes the exact list into a sub-task line of this file's report back, not into this file.
  - **Run:** the sub-task's modules plus `test_select_tests_real_s43 test_select_tests_real_declared`.

## Phase 5 — the records

- [ ] **T010 — AC-S43-7 undeclared list, AC-S43-9 same test ids, AC-S43-10 note.**
  - **Manifest:** new `specs/001-faster-slipwai/slices/S43-test-declarations/undeclared.md` only (records; no test).
  - **Steps:** (1) AC-S43-7: one row per `test_*` module `tree.effective` leaves None at the slice's tip, with the selector's
    own reason, from `declarations.scan` (quickstart step 5); the list equals the scan. (2) AC-S43-9 (quickstart step 4): list
    test ids at the tip and at `063c187` (`git archive 063c187 tests src | tar -x -C <scratch>`; discovery walks the suite
    without running it), the two sorted lists equal; record the counts. (3) AC-S43-10: state whether any `CATALOG["backends"]`
    loop was switched to `backends_under_test()`; only the matrix jobs set `FACTORY_BACKENDS`, and they run
    `test_matrix test_images` only, which this slice does not switch outside S38's narrowing, so CI's (module, backend)
    pairs are unchanged; a switched loop that cannot be shown so keeps its loop. (4) Quickstart step 2: `held()` prints `[]`.
  - **Done when:** the file holds the three records and the scan matches. The AC-S43-6 measurement and AC-S43-8 are the host's
    demo (D188), not a task.
  - **Run:** `make test TESTS="test_select_tests_real_s43 test_select_tests_real_declared test_select_tests_real_audit"`.

## Design review

No screen in this slice.

## Parallel opportunities

- **May run together:** T003 alongside T001 or T002 (files disjoint: `select-tests.py`, `test_select_tests_real_audit.py`,
  `test_select_tests_audit_narrow.py` against `argv.py`, `generation.py`, `test_select_tests_argv*.py`). Nothing else.
- **May not:** T001 -> T002 (same behaviour under test; T002's RED trial needs T001's `argv.py`). T004 after T001–T003
  (its checks read the selector as changed). T005 … T009 are strictly sequential: each edits
  `tests/test_select_tests_real_s43.py`, and T007/T008 share `tests/git_helpers.py`, `stamp_fixture.py` and `test_replay.py`.
  T010 last. `[P]` marks only T003.

## Contradictions and notes for the host

- T002 under today's rules is mostly a guard (unreadable forms already select every axis); see its flag.
- Line budget: `test_cruise_runner` 336, `test_code_index_health` 337, `render_fixture` 339, `stamp_fixture` 318 leave
  little room; T005/T006/T007/T008 each name the move that shrinks them first.

## Convergence
