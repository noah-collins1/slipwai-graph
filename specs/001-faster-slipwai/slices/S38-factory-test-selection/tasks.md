# Tasks: S38-factory-test-selection — the factory's own `make test` on a slice branch runs the modules a change can reach, and names the rest

**Input**: [plan.md](plan.md) (*The example map* R1–R10 is what the tasks cut on; *Pin*; *Structure Decision*; *Which
modules are declared*; *Where the Makefile work happens*), [research.md](research.md) (R-1 … R-8),
[data-model.md](data-model.md), [quickstart.md](quickstart.md); acceptance criteria AC-S38-1 … AC-S38-17 in
`specs/001-faster-slipwai/spec.md` under `### S38-factory-test-selection`; decisions D156, D157, D158 in
`specs/001-faster-slipwai/decisions.md`. A method slice for this repository only, with no screen and no event model of
its own, so **no white box, no mockup task and no styling task**.

**Stories** (what a host delegates by):

- **US1** — *a maintainer on a `slice/<id>` branch runs `make test` and gets the modules the change can reach, every
  skip named, and the whole suite wherever the effect cannot be established*: the selector (R1–R8).
- **US2** — *a module says what it reads, so the selector has something to narrow by*: the declarations and the page
  that documents them (R5's real-tree half; D156 point 6).
- **US3** — *`make test` calls the selector and `make verify` stays whole and stamped*: the root `Makefile`, by patch
  (R9).

**Branch**: `slice/S38-factory-test-selection` (local, cut from `adopt-method` at `8072724`; no push). One commit per
task, in `/home/noahc/math/slipwai-graph-S38-factory-test-selection`, **except** T018, which works in a scratch clone and
commits only `s38.patch` here. Every `make` and `git` command a delegate runs in this worktree carries
`SINCE=adopt-method` where it is a `make test`/`verify` without `TESTS=`; the quick runs below use `TESTS=`.

## The root `Makefile` is a control (AC-S38-14, as S33's D99/D101) — where the work happens

The cruise guard refuses an iteration an edit to the root `Makefile`. T001–T017 never touch it. T017 writes the tests
that hold the patched text (they fail on the unpatched tree with a line naming the patch). T018 makes the change in the
scratch clone `/tmp/s38/clone` and exports `slices/S38-factory-test-selection/s38.patch`. **T019 is a person's.** The
demo (T023) cannot run before it.

**Files for the slice**: `scripts/select-tests.py`, `scripts/select_tests/{__init__,base,rules,declarations,choose,report}.py`
(new), `tests/select_fixture.py` (new, the shared fixture), new `tests/test_select_tests_*.py`, one `TEST_SELECTION`
assignment in each module a declaration task names, `docs/maintaining.md` (*Verify it*), `s38.patch`. **Not edited, by
any task:** anything under `assets/`, `src/`, `delivery/`, `.github/`, `tools/`; `scripts/verify`; `catalog.json`;
`VERSION`; `changelog.d/`; the root `Makefile` (T018 changes it only inside the scratch clone, T019 applies it by
hand); `spec.md`, `decisions.md`, `story-split.md`. No bump (AC-S38-17): nothing under `assets/`, `src/slipwai/` or
`catalog.json` changes.

## Constraints that hold for every task

- **Tests.** Standard library only; a fake is a class, function or script written in the test tree implementing the
  real interface — **never `unittest.mock`** or any mocking framework (`AGENTS.md`, *Delivery method*). The tests
  build temporary git repositories holding the selector, `assets/toolkit/scripts/check-slice-scope.py` and
  `verify_scoped/` copied in, a `project.json` recording `ci.branch` `main`, a small `catalog.json`, and stand-in
  `tests/test_*.py` modules that append their name and `FACTORY_BACKENDS` to a log (`tests/select_fixture.py`, created
  in T001, extended by later tasks; split it where it nears 350 lines). Evidence is the log, never a printed line alone.
- **Size and width.** Every new `tests/test_select_tests_*.py` is **≤ 350 lines** and within 120 columns; so is
  `tests/select_fixture.py`, and no file under `scripts/select_tests/` outgrows 350 lines either. Split a module by
  rule rather than exceed.
- **Bytecode and encoding.** `sys.dont_write_bytecode = True` before the first import or load in **every** test that
  loads a script; every probe is `python3 -B`; `encoding="utf-8"` on every `open` and `read_text`.
- **Environment of a run.** The fixture's environment removes `CI`, `GITHUB_ACTIONS`, `GITLAB_CI`, `RATCHET_TIGHTEN`,
  `FULL`, `SINCE`, `TESTS`, `SKIP`, `FACTORY_BACKENDS`, `MAKEFLAGS`, `MFLAGS`, `MAKELEVEL`, `MAKEOVERRIDES`,
  `MAKEFILES` and every repository-locating `GIT_*` variable of research R-7 unless the example sets one
  (`tests/stamp_fixture.py` holds `CI_MARKERS`, `MAKE_STATE`, `GIT_STATE`; import, never re-list).
- **No wall-clock assertion**; every `subprocess.run` carries a timeout (`timeout=180`; the real-tree tests of
  T012–T015 need none — they call functions).
- **RED is seen** for its stated reason before the production code is touched. A **hold** (an example that passes
  because an earlier task produced the behaviour) is not written as its own task: it rides with the task that
  produces the behaviour and is seen to have teeth — change the production file, watch the test fail, restore with
  `git checkout -- <exact path>` only for a change you made and have not committed over; `git status` then shows only
  the task's own files. A hold whose teeth cannot be shown is reported, not claimed.
- **Before each commit**, in the worktree: `make lint typecheck check-structure`. **Quick test of an increment**:
  `make test TESTS="test_select_tests_<module> …"` — `TESTS` turns selection off, so it runs exactly those. Never the
  whole suite (the host runs it, T024); never `make verify` in a delegate.
- **Commit by path** (`git add <exact new paths>`, then `git commit -m … -- <the task's files>`); never `git add -A`,
  never `git commit -a`. Messages say the change reaches no user (no bump) — `scripts/`, `tests/`, `docs/` and the
  root `Makefile` are not user-visible trees.
- **Scratch only under `/tmp/s38/`.** Nothing is written beside the checkout; nothing is read from or written to
  `/home/noahc/math/slipwai-graph`.
- **Every doubt broadens.** A path no rule claims, an ignored file, an unreadable declaration, an unloadable script,
  an unresolvable base: the selector runs every module and says why (owner priority 5, Principle I).

## Format: `[ID] [P?] [Story] Description` — each task is one increment, one commit

`[P]` marks a task whose files are disjoint from its siblings' (see *Parallel opportunities*).

---

## Phase 1: Implementation stage (worktree `slice/S38-factory-test-selection`)

### T001 — [US1] Pin: what `make test` and `make verify` do today (plan *Pin*)

- [ ] **Stand-alone pin; green on today's `Makefile`, no production change.** Creates `tests/select_fixture.py`
  (the temporary repository on a branch, the copied root `Makefile`, the stand-in modules and log, the environment
  builder) only as far as the pin needs, and `tests/test_select_tests_pin.py`, driving the **real** root `Makefile`
  copied into the fixture.

**Hold (green now; teeth shown by editing the `Makefile`'s `test` recipe and watching each fail):**
- `TESTS="a b"` runs exactly those two modules, with `PYTHONPATH=src:tests`; `SKIP=a` runs every other module.
- On `main` and on `adopt-method` every module runs through `discover`.
- `make verify` runs every module (the stand-ins log it) and records the stamp.
- The text of the `Makefile`'s stamp bypass list is read and kept for T017's comparison.

**Verify:** `make test TESTS=test_select_tests_pin` green, then `make lint typecheck check-structure`. This module and
`test_factory_gate_stamp*` stay green after T019.

**Files:** `tests/select_fixture.py` (new), `tests/test_select_tests_pin.py` (new).

### T002 — [US1] Only a slice branch selects (R1 · AC-S38-1, -7, -13)

- [ ] **Rule R1.** Follows T001. Data-model *full* rows 1–7, in order. Creates the entry `scripts/select-tests.py`
  (arguments, the order of the *full* rows, running today's full command), `scripts/select_tests/__init__.py` and
  `report.py` (the line), and `tests/test_select_tests_full.py`.

**RED** (each fails: there is no selector):
- e1 on `main`, `adopt-method`, `feature/x` and a detached `HEAD`: every stand-in runs, one line names the case
  (`full: not a slice branch (…)`, `full: HEAD is not on a branch`).
- e2 `CI=1`, then `GITHUB_ACTIONS`, then `GITLAB_CI`, each on `slice/x` and once with `SINCE` too: every module, the
  CI line naming the variable.
- e3 `RATCHET_TIGHTEN=1`: every module, the line names it. e4 `FULL=1`: every module, `full: FULL=1 given`.
- e5 `FACTORY_BACKENDS=go`: `selection off: FACTORY_BACKENDS given`; the stand-ins run as asked.
- e6 each `GIT_*` variable of R-7 set (one test, the tuple walked): every module, the variable named.

**GREEN:** the entry and `report.py` produce each line and run `PYTHONPATH=src python3 -m unittest discover -s tests`
as today's full command does.

**REFACTOR:** the one place the *full* rows' order is spelled.

**Verify:** `make test TESTS="test_select_tests_pin test_select_tests_full"`, then lint/typecheck/structure. Commit by path.

**Files:** `scripts/select-tests.py`, `scripts/select_tests/__init__.py`, `scripts/select_tests/report.py` (new);
`tests/test_select_tests_full.py` (new); `tests/select_fixture.py` (extended).

### T003 — [US1] The base is the trunk, or what `SINCE` names (R2 · AC-S38-2, -3, -4 (b), (c))

- [ ] **Rule R2.** Follows T002. Data-model *The base*, rows 8–9 and the `SINCE` clauses of row 3's precedence.
  Creates `scripts/select_tests/base.py` (the base: loads `check-slice-scope.py`'s `merge_base()` as it ships,
  `SINCE` as `<ref>^{commit}` compared as a tree, D138 item 4, with the shared-history check) and
  `tests/test_select_tests_base.py`.

**RED:**
- e1 a slice cut from `main`, one `assets/languages/go/` path, `origin/main` level: the first line reads ``compared
  with `main` at <short> (the trunk)`` and the selection reflects that one path only (observed through the log).
- e2 a slice cut from `adopt-method`, `SINCE=adopt-method`, one go path: the SINCE line (``named by SINCE — taken as
  passing on the word of whoever named it``); a **tree** comparison — a fixture where merge-base and tree differ.
- e3 `SINCE=nonexistent` and `SINCE=<unrelated root>`: every module, `full: SINCE=<ref> could not be resolved — <why>`;
  `SINCE=main` on `adopt-method`, and on `slice/x` with `CI=1`: the *not a slice branch* / CI reason, not the base.
- e4 the trunk cannot be told (`project.json` absent or no such branch): `full: the trunk cannot be told — …`.

**GREEN:** `base.py` and its wiring in the entry.

**REFACTOR:** none expected.

**Verify:** `make test TESTS="test_select_tests_full test_select_tests_base"`, lint/typecheck/structure. Commit by path.

**Files:** `scripts/select_tests/base.py` (new), `scripts/select-tests.py`; `tests/test_select_tests_base.py` (new).

### T004 — [US1] The change set is the scoped gate's (R3 · AC-S38-5, -10 (ignored files))

- [ ] **Rule R3.** Follows T003. `changes.changed` + `changes.unpushed`, loaded as they ship (research R-1); the
  ignored files (R-6); data-model *full* rows 10, 11, 13. Edits `base.py` (the change set) and creates
  `tests/test_select_tests_changes.py`.

**RED:**
- e1 an untracked new file under `assets/languages/go/` with `SINCE`: a go-reading stand-in is the changed set's
  consequence (the log shows the changed paths reach the chooser — a stub chooser run order is not needed: assert
  the printed changed-path line and, after T006, the log; until then assert the path is in the set the entry reports).
- e2 a deleted tracked file under the same directory: the same.
- e3 no `SINCE`, an unpushed `main` commit touching `catalog.json`: every module, the line names that path in D153's
  words (taken from `verify_scoped.changes`' own wording, not re-typed).
- e4 an ignored non-cache file under `src/`: `full: … is a file git ignores — what it changes cannot be established`.
- e5 a `__pycache__/x.pyc` under `tests/` (and `*.pyo`): no effect, selection stays.
- e6 the scoped-gate scripts removed from the fixture, or git failing: `full: the change set cannot be established — …`;
  the unpushed range failing: `full: <Span.failure>`.

**GREEN:** the change set in `base.py`; the ignored scan; the broadened lines.

**REFACTOR:** the exemption list of caches shared with nothing (D119's three suffixes named once).

**Verify:** `make test TESTS="test_select_tests_base test_select_tests_changes"`, lint/typecheck/structure. Commit by path.

**Files:** `scripts/select_tests/base.py`, `scripts/select-tests.py`; `tests/test_select_tests_changes.py` (new).

### T005 — [US1] What cannot be established runs everything (R4 · AC-S38-4 (a), -8 (b), -10, -14 (b))

- [ ] **Rule R4.** Follows T004. The **full** rows of data-model *The path rules*. Creates `scripts/select_tests/rules.py`
  (the first row that claims a path, with its rule's words) and `tests/test_select_tests_paths.py`.

**RED:**
- e1 `Makefile` and `catalog.json` both changed: every module; the line names the **first** such path and its rule
  (``full: `Makefile` changed — the root Makefile: its effect cannot be established``).
- e2 each listed full path, one at a time (the table walked: `catalog.json`, `assets/backing-services/prune.py`, a
  file under `src/`, `Makefile`, `scripts/verify`, `requirements-dev.txt`, `pyproject.toml`, `VERSION`, `project.json`,
  `slipwai`, `.gitignore`, `.gitattributes`, the selector's two paths, its tests): every module, its own rule named.
- e3 `assets/newthing/x` and `assets/backing-services/unknown/x` under no catalog row: ``no rule claims it``.
- e4 a top-level file no row claims: every module, the same words.

**GREEN:** `rules.py` and the *full* row 12 in the entry.

**REFACTOR:** the table as data, one place; each row's words beside it.

**Verify:** `make test TESTS="test_select_tests_changes test_select_tests_paths"`, lint/typecheck/structure. Commit by path.

**Files:** `scripts/select_tests/rules.py` (new), `scripts/select-tests.py`; `tests/test_select_tests_paths.py` (new).

### T006 — [US1] A module reads what it declares; an undeclared one always runs (R5 e1, e3, e4 · AC-S38-8)

- [ ] **Rule R5, first half.** Follows T005. `TEST_SELECTION` read by `ast.literal_eval` (never an import); the
  path-to-configuration map taken from `catalog.json` (`backends` with each one's `family`, `frontends`, `profiles`,
  `targets`) and the `assets/` rows of the table; the selection and its reasons. Creates
  `scripts/select_tests/declarations.py` and `choose.py`, and `tests/test_select_tests_declarations.py`.

**RED (stand-in modules carry declarations; the log is the evidence):**
- e1 one go path: go declarers, *every* declarers and undeclared modules run; the rest skipped, reason *reads no go
  configuration*; an axis the declaration does not name admits every option.
- e3 a declaration naming a missing option, a missing `reads` path, a non-literal, or a wrong shape: the selector
  treats the module as undeclared (it runs), and **a held-declarations check** (a function in `declarations.py`
  the test calls on the fixture) names it. The same check run over the **real tree** is in this module and is
  green (no declaration exists yet): it is the hold T012–T015 rely on.
- e4 a declared module importing an undeclared helper in `tests/`: the module is undeclared (it runs); the
  held-declarations check reports the voided declaration by name.

**GREEN:** `declarations.py` (reading, validation, effective declaration through the import closure of `ast`
`import` and `from … import` inside `tests/`), `choose.py` (reasons in order: *undeclared*, `reads`, configuration)
and their wiring: the selected modules run as `PYTHONPATH=src:tests python3 -m unittest <modules>`.

**REFACTOR:** one reason order, spelled once.

**Verify:** `make test TESTS="test_select_tests_paths test_select_tests_declarations"`, lint/typecheck/structure.
Commit by path.

**Files:** `scripts/select_tests/declarations.py`, `scripts/select_tests/choose.py` (new), `scripts/select-tests.py`,
`scripts/select_tests/rules.py`; `tests/test_select_tests_declarations.py` (new).

### T007 — [US1] A directory is read by more than its name suggests (R5 e2, R-5 · AC-S38-8)

- [ ] **Rule R5, second half.** Follows T006. The cross-read rows of research R-5 in `rules.py`:
  `assets/languages/typescript/biome/**` and `typescript/app/package.json` also reach `frontend` `react-vite`;
  `assets/languages/java/build/**` also reaches `command` `adopt`; and each row of `FLAG_READERS[backend].tree` that
  a reading of `src/slipwai/project/flags.py` confirms. Creates `tests/test_select_tests_cross_reads.py`.

**RED:**
- e2 `assets/languages/typescript/biome/x` in a fixture: react-vite declarers run too; `java/build/x`: adopt declarers.
- **the scan** (a hold over the real `src/slipwai/`, with teeth shown): every reference to an asset root
  (`LANGUAGE_ROOT`, `FRONTEND_ROOT` and the other roots `slipwai.assets` exports, and literal `assets/<tree>/` strings),
  found by `ast` and text, names a directory `rules.py` attributes to the configuration that holds it, or the test
  fails naming the reference; the same for `assets/backing-services/<x>/` against `prune.py`'s `LANGUAGES` and
  `OWNED_FILES`. If the scan finds a reading the map lacks beyond the three in R-5, add its row and report it.

**GREEN:** the cross-read rows in `rules.py`. (The scan is not its own task: it guards behaviour this task
produces, so it is folded here.)

**REFACTOR:** none expected.

**Verify:** `make test TESTS="test_select_tests_declarations test_select_tests_cross_reads"`, lint/typecheck/structure.
Commit by path.

**Files:** `scripts/select_tests/rules.py`; `tests/test_select_tests_cross_reads.py` (new).

### T008 — [US1] The test tree selects by its own imports (R6 · AC-S38-10 (fixture), -11)

- [ ] **Rule R6.** Follows T007. The module, helper and `reads` rows for `tests/`. Edits `rules.py`, `choose.py` and
  `declarations.py` (the import graph, transitive); creates `tests/test_select_tests_imports.py`.

**RED:**
- e1 `tests/test_x.py` edited: `test_x` runs, every other **declared** module is skipped (reason *reads none of the
  changed files*); undeclared modules still run.
- e2 `tests/scoped_fixture.py`-style helper edited: exactly its importers, directly or through another helper, run.
- e3 a deleted test module: the run does not fail on the missing name and it is not listed.
- e4 a `tests/fixtures/…` file: the modules whose `reads` name it (or a directory containing it).

**GREEN:** the rows and the import graph in the chooser.

**REFACTOR:** the graph built once per run.

**Verify:** `make test TESTS="test_select_tests_declarations test_select_tests_imports"`, lint/typecheck/structure.
Commit by path.

**Files:** `scripts/select_tests/rules.py`, `scripts/select_tests/choose.py`, `scripts/select_tests/declarations.py`;
`tests/test_select_tests_imports.py` (new).

### T009 — [US1] A backend's change narrows the matrix (R7 · AC-S38-9)

- [ ] **Rule R7.** Follows T008. Data-model *Narrowing*: two `unittest` processes, the narrowed with
  `FACTORY_BACKENDS=<B>`, the rest with it unset, the run failing when either fails. Edits `choose.py`,
  `select-tests.py`; creates `tests/test_select_tests_narrow.py`.

**RED:**
- e1 one go path: the stand-in `test_matrix` (declared as reading backends) runs with `FACTORY_BACKENDS=go` and a
  stand-in that does not narrow runs with it unset (the log names both); the line names the four left out,
  taken from the fixture's `catalog.json`; exit non-zero when either process fails.
- e2 a go path plus a toolkit path: `test_matrix` is **not** narrowed. A module selected for one non-backend reason is
  not narrowed either.

**GREEN:** narrowing in `choose.py` and the two-process run in the entry.

**REFACTOR:** the run's command line spelled once for the full and the narrowed run.

**Verify:** `make test TESTS="test_select_tests_imports test_select_tests_narrow"`, lint/typecheck/structure. Commit by path.

**Files:** `scripts/select_tests/choose.py`, `scripts/select-tests.py`; `tests/test_select_tests_narrow.py` (new).

### T010 — [US1] Every skip is named, and a dry run shows it (R8 e1, e2 · AC-S38-12)

- [ ] **Rule R8, first half.** Follows T009. Data-model *What a run prints*. Edits `report.py` and the entry; creates
  `tests/test_select_tests_report.py`.

**RED:**
- e1 a selected run prints the base line, then each skipped module **once** with one reason, the `narrowed` lines,
  the summary (`selected <n> of <total> modules against …`) **before** the tests start and again **last**.
- e2 `--dry-run` prints the same lines up to the summary, nothing runs (the log stays empty), exit 0.

**GREEN:** the lines, in that order, and `--dry-run`.

**REFACTOR:** none expected.

**Verify:** `make test TESTS="test_select_tests_narrow test_select_tests_report"`, lint/typecheck/structure. Commit by path.

**Files:** `scripts/select_tests/report.py`, `scripts/select-tests.py`; `tests/test_select_tests_report.py` (new).

### T011 — [US1] A dry run replays a range of commits (R8 e3 · AC-S38-15 (replay))

- [ ] **Rule R8, second half.** Follows T010. `--dry-run --replay <base>..<tip>`: the change set from that range
  instead of the working tree and the branch rules, selection over the **current** tree's declarations. Edits
  `base.py` and the entry; creates `tests/test_select_tests_replay.py` (a fixture repository with a range of commits).

**RED:** e3 a two-commit range (a go path, then a toolkit path): the replay prints that range's paths' selection;
a range touching `catalog.json` prints the full line; a bad range prints `full: … cannot be established` and exits 0;
nothing is run and the branch rules (not a slice branch) do not apply.

**GREEN:** the replay change set.

**REFACTOR:** none expected.

**Verify:** `make test TESTS="test_select_tests_report test_select_tests_replay"`, lint/typecheck/structure. Commit by path.

**Files:** `scripts/select_tests/base.py`, `scripts/select-tests.py`; `tests/test_select_tests_replay.py` (new).

### T012 — [US2] The helpers say what they read (R5 · AC-S38-8; plan *Which modules are declared*)

- [ ] **Declaration task.** Follows T011 (the selector is complete). A module whose closure holds an undeclared
  helper is undeclared (T006 e4), so the helpers come first. Adds one `TEST_SELECTION` assignment to each helper of
  the manifest **where a reading proves it**; any helper whose reading does not prove it **stays undeclared** and
  is named, with the reason, in the report (its importers then always run). Creates `tests/test_select_tests_real_helpers.py`.

**Manifest (the only files this task edits besides its test):** `tests/support.py`, `tests/scoped_fixture.py`,
`tests/stamp_fixture.py`, `tests/mutation_scope_fixture.py`, `tests/gate_audit.py`, `tests/parallel_gate.py`,
`tests/render_fixture.py`, `tests/forge_checkout.py`.

**RED:** over the **real tree**, the test asserts for each helper that it is declared with exactly the claim its
reading supports (`reads` for every path it opens or loads by path, `configurations` for what it generates — or
absent), that the declaration passes the held-declarations check (T006), and that `scoped_fixture`'s
`importlib.import_module` loads are named in its `reads` or the helper stays undeclared (research R-4).

**GREEN:** the assignments (and only they).

**REFACTOR:** none.

**Verify:** `make test TESTS="test_select_tests_declarations test_select_tests_real_helpers"` and every module that
imports an edited helper still imports (`python3 -B -c "import ast…"` over each, or the quick run of one importer).
Commit by path.

**Files:** the eight helpers above; `tests/test_select_tests_real_helpers.py` (new).

### T013 — [P] [US2] The backend readers say which backends they generate (R5 · AC-S38-8, -9)

- [ ] **Declaration task.** Follows T012. Adds `TEST_SELECTION` to each module below **where a reading proves what it
  generates and reads**; a module where it does not (including the four research R-4 says only name the variable) **stays
  undeclared** and is named with the reason. A module that narrows by `backends_under_test()` or `FACTORY_BACKENDS`
  declares its backend axis as the full set the catalog lists, so the narrowing of T009 has a subject. Creates
  `tests/test_select_tests_real_backends.py`.

**Manifest:** `tests/test_matrix.py`, `tests/test_images.py`, `tests/test_monorepos.py`, `tests/test_postgres.py`,
`tests/test_readiness.py`, `tests/test_flag_gate.py`, `tests/test_line_widths.py`,
`tests/test_no_mocking_frameworks.py`, `tests/test_stale_references.py`, `tests/test_factory_repository.py`,
`tests/test_factory_gate_stamp.py`, `tests/test_factory_gate_stamp_inputs.py`.

**RED:** over the real tree, `choose` with one go path (a function call, not a git run) skips each declared module
that provably reads no go configuration, runs `test_matrix` narrowed to `go`, and no declared module is voided (T006's check).

**GREEN:** the assignments only.

**REFACTOR:** none.

**Verify:** `make test TESTS="test_select_tests_declarations test_select_tests_real_backends"` and a quick run of two
of the edited modules. Commit by path.

**Files:** the manifest above; `tests/test_select_tests_real_backends.py` (new).

### T014 — [P] [US2] The real-toolchain mutation modules say which backend they run (R5 · AC-S38-8)

- [ ] **Declaration task.** Follows T012. Declares the modules that run a real toolchain for one backend, **where a
  reading proves it**; any other stays undeclared. Creates `tests/test_select_tests_real_mutation.py`.

**Manifest:** `tests/test_mutation_scope_real_go.py` (`backend: ["go"]`), `tests/test_mutation_scope_real_spring.py`
(`backend: ["java-spring"]`), `tests/test_mutation_stamp_untouched.py`.

**RED:** over the real tree, a go-only change selects the first and skips the second with *reads no go configuration*
inverted accordingly: a java-spring path selects the second; a typescript path selects neither.

**GREEN:** the assignments only.

**REFACTOR:** none.

**Verify:** `make test TESTS="test_select_tests_declarations test_select_tests_real_mutation"`. Commit by path.

**Files:** the three modules above; `tests/test_select_tests_real_mutation.py` (new).

### T015 — [P] [US2] Modules that generate nothing and load a toolkit script by path say what they load (R5 · AC-S38-8, -16)

- [ ] **Declaration task.** Follows T012. These are the tests no import scan can follow (research R-4: 29 modules call
  `spec_from_file_location`, ten more use `importlib.import_module`/`__import__`). For each module of the manifest, a
  reading decides: declare `reads` for **every** script, directory or fixture it loads or opens by path (and no
  `configurations` where it generates no project), or **leave it undeclared** and name why. A module that also
  generates a project, or whose loads the reading cannot enumerate, stays undeclared. Creates
  `tests/test_select_tests_real_loaders.py`.

**Manifest (candidates; the report says which were declared and which left):** `tests/test_aws_flags.py`,
`tests/test_aws_forge.py`, `tests/test_assets_bytecode.py`, `tests/test_mutation.py`, `tests/test_deploy_role.py`,
`tests/test_codegraph_bytes.py`, `tests/test_runner_controls.py`, `tests/test_design_stage.py`,
`tests/test_mutation_borders.py`, `tests/test_cruise_start.py`, `tests/test_go_mutation_file.py`,
`tests/test_migration_script.py`, `tests/test_gitea_pages.py`, `tests/test_pit_globs.py`, `tests/test_health_said.py`,
`tests/test_release.py`, `tests/test_mutation_targets.py`, `tests/test_runner_stream.py`,
`tests/test_skill_capabilities.py`, `tests/test_slice_scope_root.py`, `tests/test_runner_between_park.py`,
`tests/test_ux_gates_scale.py`, `tests/test_shared_packages.py`, `tests/test_verify_scoped_baseline.py`,
`tests/test_verify_scoped_borders.py`, `tests/test_verify_scoped_ignored.py`, `tests/test_versions.py`.

**RED:** over the real tree, for each declared module the test asserts (i) its `reads` paths exist (T006's check),
(ii) a change to **each** path it reads selects it, by calling `choose`, and (iii) for the soundness class of AC-S38-16:
a change to one script under `assets/toolkit/scripts/` that a declared module loads selects that module.

**GREEN:** the assignments only.

**REFACTOR:** none.

**Verify:** `make test TESTS="test_select_tests_declarations test_select_tests_real_loaders"` and a quick run of three
of the edited modules. Commit by path.

**Files:** the declared subset of the manifest; `tests/test_select_tests_real_loaders.py` (new).

### T016 — [P] [US2] `docs/maintaining.md` says what `make test` does on a slice branch (D156 point 6)

- [ ] **Docs.** Follows T011 (the flags are final). Edits *Verify it* in `docs/maintaining.md`: what `make test`
  does on a `slice/<id>` branch (selects; names every skip; full elsewhere and under CI); `SINCE` — its default, the trunk,
  and **one sentence** on when to set it (when your branch was cut from a branch other than the trunk, and that
  branch's tip passed the full suite); `FULL=1`; `TESTS`/`SKIP`/`FACTORY_BACKENDS` turn selection off; `make verify`
  always runs every module; `--dry-run` and `--replay`; how a module declares `TEST_SELECTION`. Creates
  `tests/test_select_tests_docs.py`.

**RED:** the test reads the page (`encoding="utf-8"`) and fails on each missing term: `select-tests.py`, `SINCE`,
the trunk default and the *when to set it* sentence, `FULL=1`, `--dry-run`, `TEST_SELECTION`, and that `make verify`
stays whole.

**GREEN:** the prose, within the page's own width and style (`make lint` and `test_line_widths` still pass).

**REFACTOR:** none.

**Verify:** `make test TESTS="test_select_tests_docs test_line_widths"` (the latter if it covers docs), then
lint/typecheck/structure. Commit by path.

**Files:** `docs/maintaining.md`; `tests/test_select_tests_docs.py` (new).

### T017 — [P] [US3] The tests that hold the patched `Makefile` (R9 · AC-S38-6, -13, -14)

- [ ] **Rule R9, tests.** Follows T011 (the selector exists); disjoint from T012–T016. Creates the two modules that
  drive the **real** root `Makefile` copied into the fixture. **They fail on the unpatched tree, by design, with
  the line `the root Makefile is not yet patched — apply
  specs/001-faster-slipwai/slices/S38-factory-test-selection/s38.patch`** (AC-S38-14), asserted by a first test that
  detects the patched text and otherwise fails with exactly that message; the rest are skipped-by-failure, not skipped.
  Committed as they are; T018 turns them green. Never run them in a full suite before T019.

`tests/test_select_tests_makefile.py` (text): e1 the `test` recipe calls the selector unless `TESTS` is given; the
`verify` recipe passes `FULL=1` to `verify-checks`; the stamp **bypass list equals the one T001 recorded**
(unchanged: `SINCE` is not on it); the recipes equal the held text.

`tests/test_select_tests_make.py` (behaviour): e2 `make verify` on a slice branch with a one-backend change: every
stand-in runs, the stamp is recorded as S33 records it, and `SINCE=…` on `make verify` does not narrow it;
e3 `make verify TESTS=x`: no stamp read, written or removed; e4 `make test SKIP=test_matrix`: every module but it,
line `selection off: SKIP given` (likewise `TESTS`); `make test FULL=1`: every module; any change to the root `Makefile`
on a slice branch makes `make test` run every module (AC-S38-14).

**Verify (unpatched):** `make test TESTS="test_select_tests_makefile test_select_tests_make"` **fails**, each failure
the patch line; `make lint typecheck check-structure` passes. Commit by path.

**Files:** `tests/test_select_tests_makefile.py` (new), `tests/test_select_tests_make.py` (new);
`tests/select_fixture.py` (extended only if T011's fixture lacks a stamp helper — then keep it ≤ 350 lines).

### T018 — [US3] Make the `Makefile` change in the scratch clone and export `s38.patch` (R9 · AC-S38-6, -13, -14)

- [ ] **Rule R9, GREEN.** Follows T017 and every other task through T017 (the clone is taken at the worktree's tip).
  In `/tmp/s38/clone`: `git clone --quiet /home/noahc/math/slipwai-graph-S38-factory-test-selection /tmp/s38/clone`
  (or `git -C /tmp/s38/clone pull --quiet` if it exists), then edit the clone's root `Makefile` only: the `test`
  recipe calls `python3 -B scripts/select-tests.py` unless `TESTS` is given (then it runs as today and prints
  `selection off: TESTS given`; `SKIP` likewise); `verify` passes `FULL=1` to its `verify-checks` call (research R-3);
  the stamp bypass list is **unchanged**; comments in the file say so. In the clone, `make test
  TESTS="test_select_tests_makefile test_select_tests_make test_select_tests_pin"` and `TESTS=test_factory_gate_stamp*`
  go green, then `make lint typecheck check-structure`.

**Export and check (the GREEN of the tests in T017):**
1. `git -C /tmp/s38/clone diff -- Makefile > specs/001-faster-slipwai/slices/S38-factory-test-selection/s38.patch`
   (names only `Makefile`).
2. A second scratch copy at this branch's tip: `git clone --quiet <worktree> /tmp/s38/check`; `git -C /tmp/s38/check
   apply --check …/s38.patch` then `apply`; run there `make test TESTS="test_select_tests_makefile
   test_select_tests_make test_select_tests_pin test_factory_gate_stamp test_factory_gate_stamp_inputs
   test_factory_gate_stamp_scan"` green, and `python3 -B scripts/select-tests.py --dry-run` on a throwaway
   `slice/` branch there. Nothing is applied in the worktree itself.
3. Teeth: in `/tmp/s38/check`, revert one recipe line and watch the held-text test fail; restore.

**Files:** `specs/001-faster-slipwai/slices/S38-factory-test-selection/s38.patch` (new, committed alone by path; it is
not a control). The clone and the check copy are scratch under `/tmp/s38/` and are not committed.

### T019 — BLOCKED: a person applies `s38.patch` (⛔)

- [ ] **Not a delegate's task and not the host's: the root `Makefile` is a control (AC-S38-14).** A person runs the
  three commands in plan.md's *Summary* (`git apply …/s38.patch`; `make lint typecheck check-structure && make test
  TESTS="test_select_tests_makefile test_select_tests_make"`; the commit by path with the message there). Until then
  the slice is blocked at the demo: T020–T022 run on a patched scratch copy, T023–T025 wait for this one.

---

## Phase 2: Gates and closing (host)

**T020–T022 do not wait for T019.** They judge the branch with `s38.patch` applied in a scratch copy
(`/tmp/s38/check`, a fresh clone of the worktree's tip with the patch applied and not committed), so the slice reaches a
converged verdict while the patch waits for a person. A fix to the root `Makefile` they find is a new patch
(`s38-2.patch`). T023 and T024 wait for T019.

### T020 — Converge, pass 1 (host task)

- [ ] `drive-converge` over the slice's diff with `s38.patch` applied in `/tmp/s38/check`, against the constitution. **Brief it with the whole class**, not an
  instance (S06 and S33 each needed five passes to find it): *anything make or the environment can change about which
  modules run* — every variable (command line, environment, `MAKEFLAGS`, `-e`, `MAKEOVERRIDES`, `SINCE` from the
  environment), every `GIT_*` and git configuration that moves the change set, a path git ignores, a path no rule
  claims, a module that loads by path, `__import__` or `importlib` without declaring it, a helper that voids a
  declaration, a deleted file, a rename, a submodule, a symlink, a case-folded name, `make -n`/`-q`, and
  `make verify` reached through the ratchet. The verdict goes under `## Convergence`; each finding becomes a task
  under *Phase 4*, in the order found.

### T021 — Converge, pass 2 (host task)

- [ ] A second `drive-converge` pass over what pass 1's fixes changed, same class. A change to the root `Makefile`
  is a new patch (`s38-2.patch`) a person applies again.

### T022 — After-converge gaps pass (host task)

- [ ] `drive-gaps` traces AC-S38-1 … -17 over the applied tree. Includes AC-S38-17's check:
  `git diff --stat 8072724 -- assets src/slipwai catalog.json` is empty, `VERSION` and `changelog.d/` unchanged. Findings
  are decisions or tasks under *Phase 4*.

### T023 — Demo (host task; AC-S38-15, -16; D157; the quickstart)

- [ ] After T019, with no CI variable set, no worktree inside the checkout and a clean `git status`. Runs the
  quickstart's four replays (S06, S08, S33, S14), the two timed cases with `SINCE`, then the soundness check with a
  fault in the go asset and in a toolkit script a declared module loads by path, and says which part belongs to S39.
  Records machine, commit and times in `demo-log.md`. A full selection is recorded as printed; no minimum saving.

### T024 — The full gate (host task)

- [ ] `make verify` at the worktree's root (a full run on a slice branch by design), green; then
  `make -f delivery/Makefile verify`, green.

### T025 — Register row and benchmark (host task)

- [ ] The slice's row and `benchmark.json` closed; after-acceptance commits ride in this slice's own pull request.

---

## Parallel opportunities

| Task | Writes | Reads another task's file |
|---|---|---|
| T001 | `tests/select_fixture.py`, `tests/test_select_tests_pin.py` | none |
| T002 | `scripts/select-tests.py`, `scripts/select_tests/{__init__,report}.py`, `tests/test_select_tests_full.py`, fixture | T001's fixture |
| T003–T011 | `scripts/select-tests.py`, `scripts/select_tests/*.py`, one new `tests/test_select_tests_*.py` each, the fixture | the previous task's selector files |
| T012 | the eight helpers, `tests/test_select_tests_real_helpers.py` | the selector |
| T013 | its twelve modules, `tests/test_select_tests_real_backends.py` | the selector; T012's helpers (not written) |
| T014 | its three modules, `tests/test_select_tests_real_mutation.py` | same |
| T015 | its declared modules, `tests/test_select_tests_real_loaders.py` | same |
| T016 | `docs/maintaining.md`, `tests/test_select_tests_docs.py` | none of the selector's files |
| T017 | `tests/test_select_tests_makefile.py`, `tests/test_select_tests_make.py` | the selector, the fixture |
| T018 | `s38.patch`; the scratch clone | T017's tests, the selector |

**T001–T011 run one after another, by one `drive-implement` delegate (`delegate: story`, US1).** They all write
`scripts/select-tests.py` or `scripts/select_tests/*` and extend `tests/select_fixture.py`; `[P]` is on none of them.

**May run together once T011 is committed: T013, T014, T015, T016 and T017** (`[P]`; their files are pairwise
disjoint, and none edits the selector or a helper). **T012 must finish first** for T013–T015 (they declare modules that
import its helpers, and a module whose closure holds an undeclared helper is undeclared); T016 and T017 need not wait for
it, so T012, T016 and T017 may also run together (T012 is not marked `[P]` only because it gates T013–T015, not because
its files overlap). The worktree has one index: commits are by path and may need a retry when two land at once.

**May not run together:** T018 after T017 (it exports the tests' text) and after the declaration tasks' commits are
in, so the clone's tip is final — start it when no sibling is mid-commit. T019 is a person's. T020–T022 run alone, in order, on the patched scratch copy, without
waiting for T019; T023–T025 run after T019; T023 never beside T024.

## Design review

No screen in this slice

## Convergence

*(To be written by T020 and T021.)*

## Differences from plan.md

Written for the host; none changes a requirement or a decision.

1. **Three stories, not one.** The plan names none; the tasks tag US1 (the selector), US2 (declarations and the page)
   and US3 (the Makefile) so a host delegates per story. Merge them if one delegate is preferred; no task changes.
2. **R5 is two tasks and R8 is two**, and R1–R4 carry the selector's skeleton, so no task writes a test that passes at
   once. R-5's src-scan is folded into T007 (the cross-read rows it guards), not scheduled alone.
3. **R9's tests (T017) are committed red** with the patch line as their failure (AC-S38-14), then turned green by
   T018 in the scratch clone and T019. The worktree's full suite fails on those two modules until T019.
4. **The declaration modules are candidate lists** (T013, T015): the plan says a module stays undeclared where a
   reading does not prove the declaration, so the final lists are what each task's report names.
5. **R10 is the host's** (T022, T023): e3 is a diff, e1 and e2 are the demo; no implementation task.
