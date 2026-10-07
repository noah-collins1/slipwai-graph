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

- [x] **T001 — R1 literal launcher argv; AC-S43-12 (readable half), AC-S43-14 (both halves).**
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
- [x] **T002 — R2 every unreadable form stays every axis and is held; AC-S43-12 (second half), D187 rule 5.**
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
- [x] **T003 [P] — R4 the audit covers what the run selected; AC-S43-13.**
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

- [x] **T004 — R5 e1–e2 scaffold; AC-S43-2, AC-S43-3.**
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

- [x] **T005 — group 1 codegraph/health** (≈ 277 s; AC-S43-1, -2, -3, -9, -11).
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
- [x] **T006 — group 2 render** (≈ 160 s).
  - **Manifest:** `tests/render_fixture.py` (339; `"every"` narrowed to what `RenderCase.project` generates — typescript,
    event-modelling, none — and the one-element `["slipwai"]` list dropped from its own `reads`, `support`'s carrying it into
    the join); `tests/test_render_current.py`, `test_render_files_report.py`, `test_render_files.py`, `test_render_links.py`,
    `test_render_failures.py`, `test_render_once.py`, `test_render_browser.py`, `test_render_pinned.py`,
    `test_render_docs.py`; `tests/test_select_tests_real_s43.py`. Any helper the modules import beyond `render_fixture` is
    moved the T005 way into a named new file the executor adds to this manifest before writing it.
  - **Done when:** `held()` clean; a Go path skips the render modules, a typescript or event-modelling path selects them.
  - **Run:** the nine `test_render_*` modules, `test_select_tests_real_s43`, `test_select_tests_real_declared`.
- [x] **T007 — group 3 `test_factory_gate_stamp`** (46.4 s).
  - **Manifest:** `tests/test_factory_gate_stamp.py` (297; `self.repo / ".git" / "slipwai"` -> `self.repo / ".git/slipwai"`,
    same path and no `/ "slipwai"` route; the `ROOT / name` copies named in `reads`); `tests/test_select_tests_real_s43.py`.
    If its join still reaches `stamp_fixture.git`, create `tests/git_helpers.py` here (own `TEST_SELECTION`; `stamp_fixture.git`
    and `test_replay.git` moved there, the old names re-exported) and add `tests/stamp_fixture.py` (318) and
    `tests/test_replay.py` to this manifest; otherwise T008 creates it.
  - **Done when:** `held()` clean; the module skipped on a Go change.
  - **Run:** `make test TESTS="test_factory_gate_stamp test_select_tests_real_s43 test_select_tests_real_declared"` plus every
    module that imports a moved name (stamp, replay).
- [x] **T008 — group 4 mutation** (`test_mutation_scope_real_spring` 31.7 s and what shares the cut).
  - **Manifest:** `tests/test_mutation_scope_real_spring.py` (69); `tests/test_mutation_borders.py` (226;
    `clean_environment` moves out, re-exported); new `tests/mutation_env.py` (own `TEST_SELECTION`); `tests/git_helpers.py`
    (create here if T007 did not), `tests/stamp_fixture.py`, `tests/test_replay.py` (the `git` moves, re-exported);
    `tests/test_select_tests_real_s43.py`.
  - **Done when:** `held()` clean; the moved names import from both paths.
  - **Run:** `make test TESTS="test_mutation_scope_real_spring test_mutation_borders test_select_tests_real_s43 test_select_tests_real_declared"` plus the modules importing a moved name.

## Phase 4 — down the table

- [x] **T009 — the next declarable modules, one sub-task per group, ≥ 5 s first, stopping when the next is not declarable.**
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

- [x] **T010 — AC-S43-7 undeclared list, AC-S43-9 same test ids, AC-S43-10 note.**
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

## Implementation record

- T001 `a142fdd` (+ `0bd4d13`), T002 `bfefce8`, T002b `5eadc4e` (concatenation, string commands and `python -m slipwai` held; `names_launcher` moved to `scripts/select_tests/launcher.py`), T003 `5cf11c4`, T004 `db2953b`, T005 `b38dd0e`, T006 `0dfdad0`, T007 `623903f` (+ `a9f9364`), T008 `34c9874`, T009 `68005f4`, T010 `80529eb`; rebased onto `adopt-method` `0000e5b` after S26 merged (D188), no conflict.
- T009 stopped at `test_slice_scope_base`, `test_slice_scope_forge_nobase` and `test_benchmark_brackets` (their closures reach `test_adopt`'s launcher route); S26's modules were not declared (≈ 9 s).
- Estimated Go-change selection at the tip (`undeclared.md`): 342 of 383 modules, ≈ 2734 s of the table before `test_matrix`/`test_images` narrow to go; AC-S43-6 is expected to miss 900 s (plan *Status*).

## Convergence

### Converge pass 1 (drive-converge, 2026-10-07) — verdict: converged, with two MEDIUM and three LOW owed

Read against AC-S43-1…14 (the branch's `spec.md` carries the amended AC-S43-6/-11 and AC-S43-12…14), D164, D169,
D179–D182, D187, D188, the plan, research, data-model, quickstart, runtime table, `undeclared.md`, and the
constitution. One HIGH found and fixed in `98f1025`; nothing CRITICAL or HIGH is left open.

**By level**

- **Domain: the argv rule (`scripts/select_tests/argv.py`, `launcher.py`, the hook in `generation.py`).** The rule was
  fail-open (the HIGH below), and is now fail-closed for every form tried. The tries: `--flag=value`, a repeated flag,
  `--language`/`--framework`/`--service-name`, a second positional, `os.fspath(...)`, `shlex`, `shell=True`, f-string
  commands, `sys.executable -m slipwai`, `sh -c`, and `env=`/`cwd=` (`ROOT` in `cwd` is a reach; the launcher
  prepends `$root/src`, so `PYTHONPATH` cannot redirect it). Every one is held. D164 rules 1, 2 and 4 are unchanged:
  `generation.py`'s `bind`, `resolve` and `problem` are byte-identical to `adopt-method`, and `declarations.py` only moved
  `names_launcher` out. `launcher.py`'s string and `-m` detection gives the same verdict as the old `names_launcher`
  on every node of the real `tests/`: 95 detections each, none different. So it adds no false route and loses no
  real one. The real tree's 15 readable argvs are all the first argument of `subprocess.run(...)`, and the fix leaves
  every one read.
- **Use case: the audit narrowing (`scripts/select-tests.py:80-82`, `to_audit`).** On a selected run, both batches
  are handed `running`. Every module selected for its own change, a closure helper's change or a `reads` match is
  therefore audited. `test_select_tests_audit_narrow` plants all three cases. `run_full` removes an inherited
  `SELECTED_TEST_MODULES`, so a full run, CI and the merge root audit everything. The one gap is the `TESTS=`/`SKIP=`
  route (MEDIUM, T011).
- **Adapter: the declarations.** `held()` on the tip is `[]` (`test_select_tests_real_s43`,
  `test_select_tests_real_declared` and `test_select_tests_real_helpers` pass). The six reads-only modules this slice
  declared all ran clean under the audit hook in 92 s: `test_factory_gate_stamp` and
  `test_select_tests_{make,makefile,paths,go_app,declarations}`. The moved helpers (`gate_rules`, `stamp_names`,
  `stamp_case`, `mutation_env`) are re-exported, and `test_select_tests_real_s43` asserts that each is the same object
  by both paths. Some `reads` entries name generated-project or redundant paths, such as `"scripts"`, `"README.md"`
  and `"src/slipwai"` (`src/` already runs everything, AC-S43-5). These over-claim, which only over-selects and never
  skips. The `.git" / "slipwai"` → `.git/slipwai` rewrites and `["src/slipwai", "slipwai"]` keep the same paths, and
  exist to avoid a false launcher route (LOW, T013).
- **Screen:** none in this slice.
- **Published contract.** `make check-structure` passes, and no file is over 350 lines. No `unittest.mock` line was
  added. Nothing under `assets/`, `src/`, `catalog.json`, `VERSION` or `changelog.d/` changed, so there is no bump.
  S07's and S26's modules are untouched (`git diff adopt-method --stat`). The AC-S43-9 test ids have one rename
  (MEDIUM, T012). The AC-S43-6/-8 records make the host's demo possible (quickstart step 6). The expected miss is
  stated in two places, in different but compatible units: the plan *Status* gives ≈ 2250 s, and `undeclared.md`
  gives 2734 s with `test_matrix`/`test_images` counted whole and S07's 564 s on a line of its own.

**Constitution**

- **I (a scoped gate MUST be additive).** A false skip is a scoped gate removing a check without saying so. Before
  `98f1025`, fourteen literal-argv shapes did exactly that. The rule now reads only the first argument of
  `subprocess.<run|Popen|call|check_call|check_output>` (`argv.py` `whole`), and the merge root and CI still audit and
  run everything (`select-tests.py` `run_unittest` pops the variable, and `run_full` hands none).
- **I (VERSION and fragments).** No user-visible tree changed, so neither a bump nor a fragment is owed.
- **V (RED before GREEN; tests in the same commit).** `98f1025` carries the 14 new forms and the fix together. All 14
  were seen failing (`held()` returned `[]` for each, and the copy was skipped on a Go change) before `argv.py` and
  `launcher.py` changed. T002's own guard nature is flagged in this file.
- **V (behaviour, not structure).** Every selector test asserts what the selector selects and holds, through its own
  process.
- **X (deterministic).** `argv.catalog_flags` caches per process only, and reads the tree being selected.
- **Repository rule (no mocking framework).** Satisfied.
- **II, IV, VI, VII, VIII, IX:** nothing in the slice touches money, time, identity, a write path or an external
  boundary.

**Found and fixed**

- [x] **HIGH — fixed in `98f1025`: the literal-argv reader and the launcher detector failed open (D187 rules 1 and 3).**
  `argv.read` read any launcher list whose parent was not `+`, `*`, `+=`, `=` or `:`, so the deny-list missed every
  other way a list can be changed before it runs. The fourteen forms below each read as `--backend python` while
  generating go, so a copy declaring python was skipped on a Go change. Evidence: the new `FORMS` entries in
  `tests/test_select_tests_argv_forms.py` failed with 14 failures before the fix and pass after it (45/45), together
  with `test_select_tests_{argv,generation,declarations,real_s43,real_declared,real_helpers,real_backends}`.
  - **A list that is changed before it runs:**
    - returned from a function;
    - held in a dict or a tuple;
    - an element of a list of argvs;
    - bound by `:=`;
    - inside a conditional expression;
    - a lambda's result;
    - a default argument;
    - a comprehension's iterable;
    - handed to a helper that extends it.
  - **A computed element after the flags.** A computed or f-string element after the flags was counted as "the
    name", but at run time it can be `--backend=go`, which argparse's last-wins applies.
  - **Tuples.** `("python3", "-m", "slipwai", …)` and `("slipwai", "generate", …)` were never routes. A bare
    `"slipwai"` is only a path reach, and `support`'s `reads: ["slipwai"]` satisfies that in every importer.
  - **The fix:**
    - a list is read only as the first argument of a `subprocess` runner;
    - a computed name is read only right after `generate`, where last-wins makes it harmless;
    - `launcher.py` treats a tuple like a list.

**Owed**

- [ ] **T011 MEDIUM (partly done in `2d257a2`; the `TESTS=`/`SKIP=` recipe is still owed, see pass 2) — `make test TESTS=…`/`SKIP=…` keeps an inherited `SELECTED_TEST_MODULES` (R4 e3, D187 rule 4).**
  - **The problem:** those recipes run `python3 -m unittest` straight from the person's environment, so a value left
    exported in a shell narrows a run that has no change set.
  - **Evidence:** `SELECTED_TEST_MODULES=<six names> make test TESTS=test_select_tests_real_audit` audited 6 modules,
    not every one `LISTING` names.
  - **Same class:** `to_audit` treats a handoff that names modules but matches none (for example, separated by spaces
    instead of commas) as "audit nothing", not as the broken handoff its docstring says falls back to the full audit.
  - **The fix is one of:**
    - the `test` recipe's `TESTS`/`SKIP` branch unsets the variable (`env -u SELECTED_TEST_MODULES`); or
    - `select-tests.py` hands a marker beside the list, and `to_audit` honours the list only when the marker is
      present.

    In either case, a chosen name that is not a `tests/test_*.py` module falls back to the full audit. Add an
    `audit_narrow` case for each.
- [ ] **T012 MEDIUM — AC-S43-9's letter is not met; the host's word is needed.**
  - **The facts:** `undeclared.md` records honestly that one base test id was renamed away:
    `test_select_tests_real_helpers…test_the_render_fixture_runs_the_launcher_so_it_declares_every_configuration`
    became `…names_the_one_project_it_generates_and_reads_the_launcher_through_support`. Its assertion changed
    because T006 narrowed `render_fixture`, so no coverage was lost. Even so, the criterion says "none renamed away",
    and quickstart step 4 says the two lists "are equal". Whether any test is newly skipped is deferred to the
    AC-S43-8 full run.
  - **What is needed:** either the host accepts the rename as a selector-test assertion change (and the quickstart
    says "equal but for the one recorded rename"), or the old id is kept.
- [ ] **T013 LOW — the launcher detector over-matches.**
  - **The over-matches:** any `<expr> / "slipwai"`, and any list or tuple whose first element is `"slipwai"`, is a
    route. That includes a `TEST_SELECTION` `reads` list and `self.repo / ".git" / "slipwai"`.
  - **The cost:** fail-closed, so it only over-selects. But it forced the `.git/slipwai` rewrites in four files and the
    order of `stamp_case`'s `["src/slipwai", "slipwai"]`, and it silently voids a planted declaration whose `reads`
    starts with `"slipwai"` (seen in this pass).
  - **The fix:** narrow the `Div` branch to `ROOT / "slipwai"`, and skip the `TEST_SELECTION` assignment's own value.
- [x] **T014 LOW — the records drift.** Done: the counts in `2d257a2`, the *Implementation record* in converge pass 2.
  - The *Implementation record* above cites the pre-rebase commits for T001–T007 (`139f1e8`, `315a153`, `8e6c5f7`,
    `fe98a42`, `11186e5`, `8ce6f9e`, `885960b`, `7bf69f5`, `3ea65da`), which no branch contains. On this branch they
    are T001 `a142fdd` (+ `0bd4d13`), T002 `bfefce8`, T002b `5eadc4e`, T003 `5cf11c4`, T004 `db2953b`, T005
    `b38dd0e`, T006 `0dfdad0` and T007 `623903f`.
  - `undeclared.md`'s AC-S43-9 counts (3319 ids at the tip, `_argv_forms` 22) predate `98f1025`, which adds 14 ids
    (`_argv_forms` 36).
- [ ] **T015 LOW — the in-process routes D164 rule 3 never named stay unrouted. This predates the slice.**
  - **The routes:** `__import__("slipwai.cli")`, and imports of other command modules (`slipwai.cli_add`, the
    generator's own functions).
  - **The status:** none of them is on the real tree, and D187 did not ask for them. Record them for the next selector
    slice; do not widen this one.

### Converge pass 2 (drive-converge, 2026-10-07, the last) — verdict: converged; nothing CRITICAL or HIGH open

Read again against AC-S43-1…14, D187, D188 and the constitution, at the tip `2d257a2`. `98f1025` and `2d257a2` hold.
No form tried reads one configuration while generating another. Nothing was changed in code by this pass.

**The argv rule: forms tried against the new `argv.read`.** Each form was put through `generation.facts` with the real
`launcher.detector` and the real `catalog.json`. A route means every option of every axis; a read means the literal axes.

- **Kept as a route (correct):**
  - `subprocess.run(args=[…])`;
  - `run([…], **kw)` (a bare `run`);
  - `from subprocess import run as r; r([…])`;
  - `import subprocess as sp; sp.run([…])`;
  - `os.execv(ROOT / "slipwai", […])`, which is two routes;
  - `asyncio.create_subprocess_exec(*[…])`;
  - an abbreviated flag (`--back`);
  - a `--` separator.
- **Read, and what it generates is what it says:**
  - `subprocess.Popen([…]).communicate()`;
  - `env=` and `cwd=`. The launcher puts `$root/src` first on `PYTHONPATH`, and `generate` reads no environment.
- **Read narrow, but runs no project:** `subprocess.run([…], shell=True)`. With a list, POSIX runs
  `sh -c <launcher> generate …`, so the launcher starts with no verb and `parser.error`s.
- **Read narrow, but the program is not the one written (LOW, T017):** `executable=…`, `Popen([…], -1, other)` and
  `subprocess.run([…], **kw)`. None of these is on the tree (`grep executable= tests/` finds nothing). A
  different program would have to accept `generate <name> --backend …` to generate anything at all.
- **A computed name at index 0, set at run time to a flag such as `--backend=go` or `--language=java`.** It leaves
  `args.name` empty, and the literal argv cannot hold a second positional, so `generate` raises "project name is
  required" (`src/slipwai/cli.py:247`). An injected axis flag is also overridden by any later literal one.
- **A computed `--output` value.** argparse classes `-x` and `--backend=go` as options, so `--output` fails with
  "expected one argument".

**By level**

- **Domain (D187 rules 1–3).** The cases above, plus the slice's modules:
  - Passing: `test_select_tests_argv`, `_argv_forms` (36), `_audit_narrow`, `_real_s43`, `_real_declared`,
    `_real_helpers`, `_real_backends`, `_declarations` and `_generation`, 120 tests in 46 s.
  - Not pinned by a test: the forms the host named, listed above (T017).
- **Use case (D187 rule 4, AC-S43-13).**
  - `to_audit` now falls back to the full audit in these cases: an empty handoff, a malformed one (a name that is not
    an identifier), or one without `test_select_tests_real_audit`. `test_select_tests_audit_narrow` pins each.
  - A value that names the audit and an identifier that is not a module is still honoured. So is any well-formed
    value left in a person's shell, through `make test TESTS=…`.
  - Evidence: `SELECTED_TEST_MODULES=test_select_tests_real_audit,test_pit_globs make test TESTS=test_select_tests_real_audit`
    audited one module and ran 6 tests in 4.1 s.
  - Still owed as T011's remainder.
  - A full run, CI and the merge root are unaffected: `run_unittest` pops the variable and `run_full` hands none.
- **Adapter (the declarations).** As pass 1 found. `held()` on the tip is `[]`.
- **Screen:** none in this slice.
- **Published contract.**
  - `make lint typecheck check-structure` passes (583 files typed; 154 modules, no upward imports).
  - No changed `.py` file is over 350 lines.
  - No `unittest.mock`, `MagicMock` or `patch(` was added.
  - Nothing under `assets/`, `src/`, `catalog.json`, `VERSION` or `changelog.d/` changed, so no bump or fragment is
    owed.
  - No S07 or S26 module was touched.
  - AC-S43-9: 3271 ids at the base and 3333 at the tip. That is 63 added (9 + 36 + 11 + 6 + 1, each re-counted by the
    loader) and one renamed (T012).
  - The branch is 3 records-only commits behind `adopt-method`, sharing no file with them. AC-S43-6 is measured
    after the rebase D188 names.
- **Not proven by the diff:**
  - AC-S43-6 (under 900 s; the plan expects a miss, which is a `behaviour` demo and a person's word, D182);
  - AC-S43-8 (the faulted full run);
  - the "none newly skipped" half of AC-S43-9.

  All three are the host's demo measurements.

**Constitution**

- **I (a scoped gate MUST be additive).** No form reads narrow and generates another configuration. The
  `executable=`/`**kw` family is fail-open only in principle, with no instance on the tree (T017, LOW). The
  remaining narrowing of the `TESTS=` audit needs a hand-set variable, and CI and the merge root audit everything
  (T011, MEDIUM).
- **I (VERSION and fragments).** Neither is owed.
- **V (RED before GREEN).** `2d257a2` carries its cases together with the fallback.
- **X (deterministic).** Unchanged from pass 1.
- **Repository rule (no mocking framework).** Holds.
- **II, IV, VI–IX:** not touched.

**Final owed list**

- [ ] **T011 MEDIUM — the remainder: the `TESTS=`/`SKIP=` recipe still honours an inherited `SELECTED_TEST_MODULES`.**
  - **What is left:** the `Makefile` `test` recipe (line 35) runs `python3 -m unittest` with the person's
    environment, and `to_audit` accepts any identifier, not only a `tests/test_*.py` module.
  - **Fix:**
    - `env -u SELECTED_TEST_MODULES` in that branch of the recipe;
    - `to_audit` falls back where a chosen name is not a module in `tests/`;
    - one `audit_narrow` case for each.
- [ ] **T012 MEDIUM — a question for the host, not decided here.** Does AC-S43-9's "none renamed away" accept the one
  selector-test id renamed because its old name became false (`test_select_tests_real_helpers…runs_the_launcher_so_it_declares_every_configuration`
  → `…names_the_one_project_it_generates_and_reads_the_launcher_through_support`)? If it does, quickstart step 4
  reads "equal but for the one recorded rename". If it does not, the old id is kept.
- [ ] **T013 LOW — the launcher detector over-matches** (as pass 1 found).
- [ ] **T015 LOW — the in-process routes D164 rule 3 never named** (as pass 1 found; predates the slice).
- [ ] **T016 LOW — pin the forms pass 2 tried as `FORMS` cases in `test_select_tests_argv_forms`.**
  - **The forms:** `subprocess.run(args=[…])`, an aliased `run`, `sp.run`, `os.execv`,
    `asyncio.create_subprocess_exec(*[…])`, and a bare `run([…], **kw)`.
  - **Why:** each holds today, but none is pinned, so a later loosening of `argv.whole` would pass the suite.
- [ ] **T017 LOW — `argv.whole` reads a list whose call can swap the program.**
  - **The forms:** a `subprocess` runner given `executable=`, a third positional to `Popen`, or `**kw`.
  - **Fix:** read only when every keyword is one of `check`, `capture_output`, `text`, `stdout`, `stderr`, `input`,
    `timeout`, `cwd`, `env` or `encoding`, and there is one positional and no `**`.
  - **Status:** no instance is on the tree.
- [x] **T014 LOW** — done (counts in `2d257a2`; the *Implementation record* corrected in this pass).
