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

- [x] **Stand-alone pin; green on today's `Makefile`, no production change.** Creates `tests/select_fixture.py`
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

- [x] **Rule R1.** Follows T001. Data-model *full* rows 1–7, in order. Creates the entry `scripts/select-tests.py`
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

- [x] **Rule R2.** Follows T002. Data-model *The base*, rows 8–9 and the `SINCE` clauses of row 3's precedence.
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

- [x] **Rule R3.** Follows T003. `changes.changed` + `changes.unpushed`, loaded as they ship (research R-1); the
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

- [x] **Rule R4.** Follows T004. The **full** rows of data-model *The path rules*. Creates `scripts/select_tests/rules.py`
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

- [x] **Rule R5, first half.** Follows T005. `TEST_SELECTION` read by `ast.literal_eval` (never an import); the
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

- [x] **Rule R5, second half.** Follows T006. The cross-read rows of research R-5 in `rules.py`:
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

- [x] **Rule R6.** Follows T007. The module, helper and `reads` rows for `tests/`. Edits `rules.py`, `choose.py` and
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

- [x] **Rule R7.** Follows T008. Data-model *Narrowing*: two `unittest` processes, the narrowed with
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

- [x] **Rule R8, first half.** Follows T009. Data-model *What a run prints*. Edits `report.py` and the entry; creates
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

- [x] **Rule R8, second half.** Follows T010. `--dry-run --replay <base>..<tip>`: the change set from that range
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

- [x] **Declaration task.** Follows T011 (the selector is complete). A module whose closure holds an undeclared
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

- [x] **Declaration task.** Follows T012. Adds `TEST_SELECTION` to each module below **where a reading proves what it
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

- [x] **Declaration task.** Follows T012. Declares the modules that run a real toolchain for one backend, **where a
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

- [x] **Declaration task.** Follows T012. These are the tests no import scan can follow (research R-4: 29 modules call
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

- [x] **Docs.** Follows T011 (the flags are final). Edits *Verify it* in `docs/maintaining.md`: what `make test`
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

- [x] **Rule R9, tests.** Follows T011 (the selector exists); disjoint from T012–T016. Creates the two modules that
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

- [x] **Rule R9, GREEN.** Follows T017 and every other task through T017 (the clone is taken at the worktree's tip).
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

### T019 — a person applies `s38.patch` (done at `75150f9`)

- [x] *(Done by a person at `75150f9`, 2026-10-06, told to cruise iteration 24: the plan's checks passed — lint, typecheck, check-structure; `test_select_tests_makefile` and `test_select_tests_make`, 22 tests OK.)* **Not a delegate's task and not the host's: the root `Makefile` is a control (AC-S38-14).** A person runs the
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

- [x] `drive-converge` over the slice's diff with `s38.patch` applied in `/tmp/s38/check`, against the constitution. **Brief it with the whole class**, not an
  instance (S06 and S33 each needed five passes to find it): *anything make or the environment can change about which
  modules run* — every variable (command line, environment, `MAKEFLAGS`, `-e`, `MAKEOVERRIDES`, `SINCE` from the
  environment), every `GIT_*` and git configuration that moves the change set, a path git ignores, a path no rule
  claims, a module that loads by path, `__import__` or `importlib` without declaring it, a helper that voids a
  declaration, a deleted file, a rename, a submodule, a symlink, a case-folded name, `make -n`/`-q`, and
  `make verify` reached through the ratchet. The verdict goes under `## Convergence`; each finding becomes a task
  under *Phase 4*, in the order found.

### T021 — Converge, pass 2 (host task)

- [x] A second `drive-converge` pass over what pass 1's fixes changed, same class. A change to the root `Makefile`
  is a new patch (`s38-2.patch`) a person applies again.

### T022 — After-converge gaps pass (host task)

- [x] *(Done at `c4ae355`, iteration 24: five findings, T037–T041.)* `drive-gaps` traces AC-S38-1 … -17 over the applied tree. Includes AC-S38-17's check:
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

## Phase 4: Convergence fixes

Found by T020 (converge pass 1), in the order found; the grade is in each title. T026 and T027 re-open the loop; the
rest may ship after it. T031 and T032 change the root `Makefile`, so they are a new patch (`s38-2.patch`) a person
applies, as T019 is. Each RED is written first and observed failing for its own reason.

### T026 — HIGH: an interpreter cache under `assets/` reaches the modules that read `assets` (AC-S38-10, -16)

- [x] `base.ignored_files` drops every cache (`is_cache`, `scripts/select_tests/base.py:171-181`), so a cache never enters
  the change set. AC-S38-10 exempts caches from making the run **full**; it does not exempt them from reaching a
  module that reads them. `test_assets_bytecode` declares `reads: ["assets", "tests"]` and exists to fail on exactly
  this. Reproduced in a patched scratch copy: an ignored `assets/toolkit/scripts/__pycache__/verify-stamp.cpython-312.pyc`
  and `SINCE=HEAD … select-tests.py --dry-run` print `skipped test_assets_bytecode: reads none of the changed files`;
  `make test TESTS=test_assets_bytecode` on the same tree fails (1 failure). Full run red, selected run green.
  **Fix:** a cache under `assets/` joins the change set for `reads` matching only — it still never makes the run full
  and is claimed by no configuration.
  **RED:** in the fixture, a slice branch with `SINCE` at its tip and one ignored `assets/<x>/__pycache__/y.pyc`: the
  dry run selects the module declaring `reads: ["assets"]` with reason ``reads `assets` ``, the first line is the
  base line (not `full:`), and a module declaring only a configuration is still skipped.
  **Files:** `scripts/select_tests/base.py`, `scripts/select-tests.py` (only if `plan` is where the paths join),
  `tests/test_select_tests_changes.py` (or a new `tests/test_select_tests_caches.py`).

### T027 — HIGH: a test module in a `tests/` sub-package is neither run nor counted (AC-S38-12, -16)

- [x] The scan reads `tests/*.py` only (`scripts/select_tests/declarations.py:205`), and `rules.claim` sends any path
  under a `tests/` subdirectory to *the files its readers name*. `unittest discover -s tests`, the full run, imports
  `test*.py` from every sub-package. Reproduced: `tests/sub/__init__.py` plus a failing `tests/sub/test_nested.py`,
  `SINCE=HEAD` dry run prints `selected 322 of 336` and names `test_nested` nowhere (only `test_assets_bytecode` is
  pulled in, by its `reads`); `discover -s tests -p test_nested.py` fails. The total under-counts what the full run
  holds and the module is never skipped by name (AC-S38-12).
  **Fix:** a `.py` path under a `tests/` subdirectory that `discover` would import — every directory from `tests/` to
  it holds an `__init__.py`, the file matches `test*.py`, or the path is an `__init__.py` — makes the run full with the
  rule's words (e.g. *a test module the selector cannot name*). `tests/fixtures/…` (no `__init__.py` chain) keeps its
  row.
  **RED:** in the fixture, a slice branch with `tests/sub/__init__.py` and `tests/sub/test_nested.py` added: the dry
  run's line is `full: \`tests/sub/test_nested.py\` changed — …`; a `.py` under `tests/fixtures/x/` with no
  `__init__.py` chain still selects.
  **Files:** `scripts/select_tests/rules.py`, `tests/test_select_tests_paths.py`.

### T028 — MEDIUM: a root makefile git does not see changed leaves the run selected (AC-S38-14)

- [x] `verify_scoped.changes.changed` compares every base blob raw **except** `Makefile`, `GNUmakefile` and
  `makefile` (`assets/toolkit/scripts/verify_scoped/changes.py:98`), which D140 hands to the scoped gate's text border;
  the selector loads `changed` and has no such border, and `ignored_files` looks only under `assets/`, `src/` and
  `tests/`. Reproduced: `git update-index --assume-unchanged Makefile`, a comment appended, `SINCE=HEAD` dry run prints
  `selected 321 of 336`; likewise an untracked `GNUmakefile` (`include Makefile`) ignored through `.git/info/exclude`,
  which make reads **before** `Makefile`. AC-S38-14: *any* change to the root `Makefile` makes the run full.
  **Fix:** the selector compares the three root makefile names itself, raw against the base (bytes, mode, presence,
  ignored or not), and any difference is the root Makefile's full row.
  **RED:** in the fixture, (a) `Makefile` edited under `--assume-unchanged`, (b) an ignored `GNUmakefile` created, (c)
  `Makefile` edited under `--skip-worktree`: each dry run's line is `full: \`<name>\` changed — the root Makefile: …`.
  **Files:** `scripts/select_tests/base.py` (or `scripts/select-tests.py`'s `plan`), `tests/test_select_tests_changes.py`.

### T029 — MEDIUM: the scoped gate's scripts that compute the change set are not a full row (priority 5)

- [x] The selector's verdict is computed by `assets/toolkit/scripts/check-slice-scope.py` and
  `assets/toolkit/scripts/verify_scoped/` (`base.load_scoped`, `scripts/select_tests/base.py:51`), but a change to them
  is claimed as *the toolkit* (every configuration), not as the selector (`rules.py:60`). A change to that code can
  hide itself. Reproduced: `changes.changed` edited to drop paths under `verify_scoped/` from its return; `SINCE=HEAD`
  dry run prints `skipped test_matrix: reads none of the changed files` and `selected 321 of 336` — the edit is not in
  the change set it computed. **Fix:** both are rows of *the selector* (full), with their own words.
  **RED:** a one-line change to `assets/toolkit/scripts/verify_scoped/changes.py`, and separately to
  `check-slice-scope.py`: the line is `full: … — the selector's change-set scripts: its effect cannot be established`.
  **Files:** `scripts/select_tests/rules.py`, `tests/test_select_tests_paths.py`.

### T030 — MEDIUM: nothing holds a new declaration complete (AC-S38-8, -16)

- [x] The fifteen declarations here were spot-checked and hold (see *Convergence*), but the `real_*` tests pin only the
  modules they list: a later `TEST_SELECTION` added to a module that is not on any list is held only for existence
  (`held()`, `declarations.py:217`). `support.generate` is reachable from every importer while `support` declares no
  configuration, so a reads-only declaration on a module that calls `self.generate(…)` under-claims and nothing fails.
  **Fix:** (a) a test pins the set of modules and helpers carrying `TEST_SELECTION` to the union of the `real_*`
  lists, so a new declaration must edit a selector test (which is itself full and reviewed); and (b) `held()` reports a
  declared module whose closure calls `generate(`/`refuse(` or runs `slipwai` and declares no `configurations`.
  **RED:** in the fixture, a module declaring `{"reads": []}` that imports `support` and calls `self.generate(…)`:
  `held()` names it; and against the real tree, the pinned set equals the scanned set.
  **Files:** `scripts/select_tests/declarations.py`, `tests/test_select_tests_declarations.py`,
  `tests/test_select_tests_real_helpers.py` (or a new `tests/test_select_tests_real_declared.py`).

### T031 — LOW: `make verify-checks` run directly selects, then says `verify: all gates passed` (AC-S38-6, G3)

- [x] Only `verify` passes `FULL=1` (patched `Makefile:58,60`); `verify-checks` (`Makefile:64`) reaches `test` with
  selection on, on a slice branch, and ends `verify: all gates passed`. Shown by `make -n verify-checks` in the patched
  scratch copy: the `test` line is `PYTHONPATH=src python3 -B scripts/select-tests.py`.
  **Fix (in `s38.patch`, regenerated — it is not yet applied, so the person applies one patch, not two):** `verify-checks` runs every module (a target-specific `FULL := 1` exported to its
  prerequisites, or the message names a selected run). **RED:** `make verify-checks` on a slice branch with a
  one-backend change runs every stand-in.
  **Files:** `specs/001-faster-slipwai/slices/S38-factory-test-selection/s38.patch` (regenerated), `tests/test_select_tests_make.py`,
  `tests/test_select_tests_makefile.py`.

### T032 — LOW: `SKIP` naming every module turns selection on (AC-S38-13)

- [x] `TESTS ?= $(if $(SKIP),$(filter-out …),)` (`Makefile:32`) is empty when `SKIP` names every module, so the `test`
  recipe calls the selector. `make -n test SKIP="<all 336>"` prints `PYTHONPATH=src python3 -B scripts/select-tests.py`
  where AC-S38-13 says `SKIP` turns selection off (the unpatched recipe ran every module here).
  **Fix (in the regenerated `s38.patch`):** the recipe branches on `$(TESTS)$(SKIP)`, prints `selection off: SKIP given` and runs no
  module. **RED:** `make test SKIP="<every module>"` prints that line and does not call the selector.
  **Files:** `specs/001-faster-slipwai/slices/S38-factory-test-selection/s38.patch` (shared with T031),
  `tests/test_select_tests_make.py`.

Found by T021 (converge pass 2), in the order of their grade. T033 re-opens the loop; T034–T036 may ship after it.
T034 and T035 change the root `Makefile`: `s38.patch` is still unapplied, so they regenerate it (one patch for the
person, as T031/T032 did); were it applied first, they are `s38-2.patch`.

### T033 — HIGH: a `tests/` sub-package already on the base is never run, never named, never counted (AC-S38-12, -16; VIII)

- [x] T027 makes the run full only while a sub-package file is in the change set. Once the sub-package is on the base,
  the scan still reads `tests/*.py` only (`scripts/select_tests/declarations.py:223`, `scan`), so every later
  selected run leaves its modules out of the verdicts, the skipped lines and the total, while `unittest discover -s
  tests`, the full run, imports them. Reproduced in a patched scratch clone: `tests/sub/__init__.py` plus
  `tests/sub/test_nested.py` (fails when `assets/languages/go/README.probe` holds `FAULT`) committed, then that go
  file committed; `SINCE=HEAD~1 select-tests.py --dry-run` prints `selected 331 of 338` and names `test_nested`
  nowhere; `discover -s tests -p test_nested.py` on the same tree is `FAILED (failures=1)`. Full run red, selected run
  green, and the module is never skipped by name. **Fix:** a selected run is possible only where the scan holds every
  module `discover` would load. Where any directory under `tests/` reachable through an `__init__.py` chain holds a
  `test*.py`, the run is full and the line names it (*a test module the selector cannot name*). Alternatively, the scan
  takes those modules as undeclared, always run, by their dotted names. Choosing between the two is the implementer's
  call; both broaden. **RED:** in the fixture, a slice branch whose *base* holds `tests/sub/__init__.py` and a stand-in
  `tests/sub/test_nested.py`, with a go-asset change since the base: the dry run either is full with that line, or
  lists `sub.test_nested` as run and counts it in the total; the log of a real run holds `test_nested`.
  **Files:** `scripts/select_tests/declarations.py` and/or `scripts/select_tests/rules.py`, `scripts/select-tests.py`
  (only if the full row is raised in `plan`), `tests/test_select_tests_paths.py` (or a new
  `tests/test_select_tests_subpackages.py`), `tests/select_fixture.py` (only if a stand-in in a sub-directory needs it).

### T034 — MEDIUM: `TESTS` given empty beside `SKIP` runs no module and passes — `make verify` included (AC-S38-6, -13; I)

- [x] The patched `test` recipe branches on `$(strip $(TESTS)$(SKIP))` and words the line by `$(origin TESTS)`.
  An explicitly empty `TESTS` (command line, or exported empty in the environment, so `?=` does not assign) with
  any `SKIP` echoes `selection off: TESTS given` and runs nothing. Reproduced in the patched scratch clone:
  `make test TESTS= SKIP=test_matrix` → `selection off: TESTS given`, no unittest, `rc=0`; `TESTS= make test
  SKIP=test_matrix` the same; `make verify-checks TESTS= SKIP=test_matrix` ends `verify: all gates passed` with no
  test run, and `make -n verify TESTS= SKIP=test_matrix` shows that path (stamp bypassed, `verify-checks FULL=1`,
  then the echo alone). The unpatched recipe (`8072724:Makefile:32`) ran `discover -s tests` for an empty `TESTS`, and
  AC-S38-13 gives `SKIP=test_matrix` *every module but `test_matrix`*. **Fix (in the regenerated `s38.patch`):** an
  empty `TESTS` is not given. The branch and the word test `$(strip $(TESTS))` before `origin`, so `TESTS= SKIP=x`
  runs every module but `x` and says `SKIP given`. T032's all-modules `SKIP` keeps running none. **RED:** `make test
  TESTS= SKIP=<one stand-in>` in the fixture runs every other stand-in (the log, not the line) and prints `selection
  off: SKIP given`; the same with `TESTS` exported empty.
  **Files:** `specs/001-faster-slipwai/slices/S38-factory-test-selection/s38.patch` (regenerated),
  `tests/test_select_tests_make.py`, `tests/test_select_tests_makefile.py`.

### T035 — LOW: `make test verify-checks` runs `test` once, selected, then says `verify: all gates passed` (AC-S38-6, G3)

- [x] T031's `verify-checks: override export FULL := 1` reaches `test` only when `verify-checks` is what makes it.
  Named first as a goal, `test` is made once without `FULL`, and `verify-checks` finds it done. Reproduced in the
  patched scratch clone with a stub selector that prints `FULL`: `make test verify-checks -o lint -o typecheck -o
  check-structure` → `STUB FULL=None`, then `verify: all gates passed` (`make verify-checks`, `… FULL=`, `-e
  verify-checks` each print `FULL='1'`). **Fix (in the regenerated `s38.patch`):** `verify-checks`' recipe ends with
  its words only where the run was whole, e.g. it calls `test` itself through `$(MAKE) … test FULL=1` rather than as
  a prerequisite, or it refuses alongside a `test` goal (`$(filter test,$(MAKECMDGOALS))`). **RED:** `make test
  verify-checks` on a slice branch with a one-backend change runs every stand-in by the log, or exits non-zero
  without the `all gates passed` line.
  **Files:** `specs/001-faster-slipwai/slices/S38-factory-test-selection/s38.patch` (shared with T034),
  `tests/test_select_tests_make.py`, `tests/test_select_tests_makefile.py`.

### T036 — LOW: `held()`'s under-claim check sees one route to a generated project of four (AC-S38-8)

- [x] T030 (b) flags a reads-only declaration only for a `generate(`/`refuse(` call in the closure, or the literal
  `./slipwai` in the module's *own* file (`declarations.py:126`, `under_claims` at `:235`). `stamp_fixture` reaches
  the launcher as `str(ROOT / "slipwai")`. Reproduced with `declarations.held()` over a scratch tree whose modules
  all declare `{"reads": []}`: `subprocess.run([str(ROOT / "slipwai"), "generate", …])`, a helper `gen_helper.py`
  running `["./slipwai", "generate", …]`, and `from slipwai.cli import main; main(["generate", …])` are not named;
  only `self.generate("x")` is. T030 (a)'s pin, an equality run on every selected run (the selector's tests are
  undeclared), still makes a new declaration edit a reviewed selector test, so this is LOW. **Fix:** the launcher
  test reads the closure, not the module alone, and matches the name `slipwai` as a path's last part
  (`"./slipwai"`, `ROOT / "slipwai"`) or a `slipwai.cli` import. Alternatively, the docstring and data model say
  `held()` names the direct call only and the pin is the guard. **RED:** in the fixture, each of the three modules
  above is named by `held()`.
  **Files:** `scripts/select_tests/declarations.py`, `tests/test_select_tests_declarations.py`.

---

### After-converge gaps (T022, 2026-10-06, iteration 24, `drive-gaps` over `c4ae355`) — before the demo

AC-S38-1, -2, -4…-7, -9…-14, -17 held; -3 and -8 partly; -15 not yet run; **-16 not held** (reproduced). T037 and T038
land before the demo (T023); T039–T041 too, since the demo follows the quickstart.

- [ ] **T037 — HIGH · Asset files the generator reads on import reach every module that imports `slipwai` (gaps 1; AC-S38-10, -16).** `src/slipwai/assets.py` loads `assets/toolkit/scripts/check-styles.py` by path on import, and generator functions a module calls in process read `assets/toolkit/scripts/agents/registry.json` (`src/slipwai/project/gitignore.py`); a toolkit change selects only generating modules and those whose `reads` name the file, so seven reads-only modules importing `slipwai` are skipped while each errors on the faulted tree (reproduced: `check-styles.py` broken, `selected 332 of 339`, the seven raise `SyntaxError`). **RED** (`tests/test_select_tests_real_loaders.py`): a change to `check-styles.py`, to `agents/registry.json`, and to every other asset `src/slipwai` reads at import or from a function a declared module calls in process, runs every module that imports `slipwai` (or the run is full), with the reason. **GREEN — the class:** a rule like the pruner's row for every asset path `src/slipwai/` reads, found by scanning `src/slipwai/` for asset paths (literal and joined), not by a typed list; a module importing `slipwai` is taken to read them. **Files:** `scripts/select_tests/rules.py`, `scripts/select_tests/declarations.py`, `tests/test_select_tests_real_loaders.py`.
- [ ] **T038 — HIGH · A declared module is held to what it reads, not to a typed list (gaps 2; AC-S38-8, -16) — the generating modules decided by D164.** **RED** (a new `tests/test_select_tests_real_audit.py`): each reads-only declared module runs under an audit hook (`sys.addaudithook`, `open` events), and the test fails on any opened path outside `src/` and `tests/` that neither its `reads` nor a run-everything row covers — teeth: the gaps pass's `self.module.load("verify-stamp.py")` added to `test_pit_globs` fails it; for the modules that generate projects, see D164. **GREEN:** the declarations it flags are fixed. **Files:** a new `tests/test_select_tests_real_audit.py`, `tests/support.py` only as D164 allows, the declarations it flags.
- [ ] **T039 — MEDIUM · The demo's replays are runnable as written, and a full replay prints its count and base (gaps 3; AC-S38-15) — D165 (D157 standing).** `quickstart.md` names the four ranges: S06 `51c6de4..45ebedb` and S33 by its register row's *Merged as* range (they landed on `adopt-method`'s main line, no merge commit), S08 `3138416^1..3138416`, S14 `37cdf3f^1..37cdf3f` (merged since the plan); the quickstart's `SINCE=adopt-method` example is read on a tree whose `Makefile` matches its base. **RED/GREEN** (`tests/test_select_tests_replay.py`, `scripts/select-tests.py`): a replay that runs everything also prints `selected N of N against <base>`. **Files:** `quickstart.md`, `scripts/select-tests.py`, `tests/test_select_tests_replay.py`.
- [ ] **T040 — LOW · The docs say the patch is applied (gaps 4).** Delete *Until `s38.patch` is applied …* from `docs/maintaining.md` and `test_says_the_patch_is_not_yet_applied` (`tests/test_select_tests_docs.py`), which holds it there; say instead what `make test` does on a slice branch. **Files:** `docs/maintaining.md`, `tests/test_select_tests_docs.py`.
- [ ] **T041 — LOW · `adopt`'s fallback to the TypeScript examples is a cross-read (gaps 5).** `src/slipwai/toolkit.py` falls back to `assets/languages/typescript/examples/`; `CROSS_READS` gains `(command, adopt)` for them and the scan reads the f-string path in `src/slipwai/examples.py`. **Files:** `scripts/select_tests/rules.py`, `tests/test_select_tests_cross_reads.py`.

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

### Pass 1 (T020, cruise iteration 24) — **not converged**: 2 HIGH, 3 MEDIUM, 2 LOW

Judged on `git diff 8072724..HEAD` (tip `1151dcd`) with `s38.patch` applied and committed in a scratch clone
(`/tmp/s38/converge1`, probes in a second clone). There is no `.codegraph/` in this tree; text search and running code
answered. The slice's own tests (`test_select_tests_*`, 19 modules, plus `test_factory_gate_stamp`) pass on the patched
copy: 169 tests, OK.

**Findings** (tasks under *Phase 4*):

| Task | Grade | One-line reproduction |
|---|---|---|
| T026 | HIGH | ignored `assets/toolkit/scripts/__pycache__/x.pyc`, `SINCE=HEAD` dry run → `skipped test_assets_bytecode`; that module fails on the same tree |
| T027 | HIGH | `tests/sub/__init__.py` + failing `tests/sub/test_nested.py` → `selected 322 of 336`, the module never named; `discover` fails it |
| T028 | MEDIUM | `Makefile` edited under `--assume-unchanged`, or an ignored `GNUmakefile` → `selected 321 of 336`, not full |
| T029 | MEDIUM | `verify_scoped/changes.py` edited to drop its own path → `skipped test_matrix`, `selected 321 of 336` |
| T030 | MEDIUM | a reads-only declaration on a module that calls `support.generate` is held by nothing |
| T031 | LOW | `make -n verify-checks` → the `test` line calls the selector; the run ends `verify: all gates passed` |
| T032 | LOW | `make -n test SKIP="<every module>"` → the selector runs, not `selection off` |

No finding is a product question: none changes what a criterion or decision says (T026 keeps AC-S38-10's exemption
from *full*; T029 widens a full row, which priority 5 asks for).

**Constitution, principle by principle the diff touches:**

- *I, a scoped gate MUST be additive* — satisfied: CI markers make every run full
  (`scripts/select_tests/__init__.py:15`, `environment_rows` at `:23`); only `slice/<id>` selects (`branch_rows`,
  `:52-63`), so `adopt-method` and `main` stay full; `make verify` passes `FULL=1` on both of its `verify-checks` calls
  (patched `Makefile:58` and `:60`), and `FULL=1` holds against `FULL=`/`FULL=0` on the command line, `make -e` and
  `MAKEFLAGS` (scratch make probe). No check is removed: the diff touches nothing under `assets/`, `src/slipwai/` or
  `catalog.json`.
- *I, `VERSION` and a fragment for every user-visible change* — satisfied: `git diff --stat 8072724..HEAD -- assets
  src/slipwai catalog.json VERSION changelog.d` is empty (AC-S38-17); no bump is owed.
- *VIII, deterministic: same inputs, same verdict* — **not met** by T026 and T027: on one commit the full run fails
  and the selected run passes.
- *AGENTS, no mocking framework* — satisfied: no `unittest.mock`, `MagicMock` or `mock` in `tests/select_fixture*.py`
  or `tests/test_select_tests_*.py`.
- Money, time, identity, idempotency, persisted schema: not touched (a test-runner script).

**Each level:**

- **Domain** (`rules`, `declarations`, `choose`): proven — the generator opens and lists only assets its claim admits,
  across 45 configurations (five backends × both frontends × both profiles at target `none`; × both frontends at
  `aws` and `azure` under `event-modelling`; `existing` with postgres and keycloak), measured with an audit hook. Nothing at
  the root is opened besides `VERSION` and `catalog.json`. `CROSS_READS` is complete for generation. Narrowing is
  sound: a go asset narrows seven modules to `go`, and a cross-read path added beside it runs them whole. The fifteen
  declared modules' `reads` and `configurations` match what each opens and passes to `generate` (spot-checked:
  `test_matrix`, `test_images`, `test_postgres`, `test_readiness`, `test_line_widths`, `test_stale_references`,
  `test_no_mocking_frameworks`, `test_mutation`, `test_go_mutation_file`, `test_pit_globs`, `test_release`,
  `test_versions`, `test_gitea_pages`, `test_migration_script`, `test_assets_bytecode`). Not proven: caches (T026),
  sub-packages (T027), self-hiding change-set code (T029), future declarations (T030).
- **Use case** (`select-tests.py`): proven — what it prints is what it runs (skips named, narrowed named, summary
  first and last); both processes run and either failing fails the run; `--replay` only with `--dry-run`; `SINCE`
  unresolved, empty, or naming a non-commit goes full or falls back to the trunk as D156 says. Not proven: the
  total under-counts a sub-package (T027).
- **Delivery adapter** (the patched root `Makefile`): proven — `TESTS`/`SKIP`/`FACTORY_BACKENDS` turn selection off and
  bypass the stamp; `SINCE` reaches the ratchet's `make test` through the environment; `RATCHET_TIGHTEN` is full;
  the ratchet refuses to record a red suite without `RATCHET_TIGHTEN`, so a selected run cannot write a quarantine.
  Not proven: hidden makefile edits (T028), `verify-checks` run directly (T031), `SKIP` naming every module (T032).
- **Screen:** none (the selector's lines are its interface; `report.printable` strips control characters from every
  word not its own).
- **Published contract** (`make test`/`make verify` and `docs/maintaining.md`): held by `test_select_tests_docs` and
  the two Makefile modules, green on the patched copy.

Checked and clean: the trunk and `SINCE` base, deletion, rename (`--no-renames`), untracked and ignored files under the
three trees, `--skip-worktree`/`--assume-unchanged` and filters on every file but the makefiles (raw comparison),
`GIT_*` locating variables, CI markers, `FULL` empty, no tracked symlink or submodule, `make -n`/`-q`.

### Pass 2 (T021, cruise iteration 24) — **not converged**: 1 HIGH, 1 MEDIUM, 2 LOW

Judged on `git diff 8072724..HEAD` (tip `ef4318f`), weighted to pass 1's fixes (`1151dcd..HEAD`, T026–T032), with
`s38.patch` applied in `/tmp/s38/converge2`. Probes ran in a second clone with the patch committed (`/tmp/s38/probe`),
since an uncommitted `Makefile` makes every dry run full. There is no `.codegraph/` in this tree; text search and
running code answered. On the patched copy, `make test TESTS="<the 20 test_select_tests_* modules, test_factory_gate_stamp,
test_factory_gate_stamp_probes>"` ran 212 tests, OK.

**Findings** (tasks under *Phase 4*):

| Task | Grade | One-line reproduction |
|---|---|---|
| T033 | HIGH | `tests/sub/{__init__,test_nested}.py` on the base, a go asset changed since → `selected 331 of 338`, `test_nested` never named; `discover` fails it |
| T034 | MEDIUM | `make test TESTS= SKIP=test_matrix` → `selection off: TESTS given`, no module, rc 0; `make verify-checks` the same, ending `verify: all gates passed` |
| T035 | LOW | `make test verify-checks` → the selector sees `FULL` unset, then `verify: all gates passed` |
| T036 | LOW | `held()` names no reads-only module that generates through `ROOT / "slipwai"`, a helper's `./slipwai`, or `slipwai.cli.main` |

No finding changes what a criterion or decision says. T033 extends T027's full row to the base, which priority 5 asks
for. T034 restores what AC-S38-13 already says `SKIP` does. **One question for the host (not a finding):** T032 made
`SKIP` naming every module run none, with `make verify SKIP=<all>` then ending `verify: all gates passed`. The
unpatched recipe ran the whole suite there. That matches the words of AC-S38-13, and pass 1 recorded it as the fix,
but it is a green gate with no test run. If the owner wants priority 5 to govern it, T032's fix should broaden instead.

**What pass 1's fixes hold (checked again, by probe):**

- **T026:** a cache only adds a `reads` match (`choose.select`, after `reach`), so it can neither narrow nor claim a
  configuration. A non-ignored `.pyo` would enter the change set as an untracked toolkit file and broaden. Caches under
  `src/`/`tests/` are D119's exemption, and no declared module reads a cache there (`test_assets_bytecode` reads
  `tests/*.py` as text, `TESTS.glob("*.py")`). `find assets -name __pycache__` in the worktree: empty.
- **T027:** `rules.discoverable` sends `tests/sub/test_a.py`, `tests/sub/__init__.py` and a vanished chain to the full
  row, and `tests/fixtures/x/test_y.py` and `tests/fixtures/adopt/python-worker/tests/test_worker.py` (no
  `__init__.py` chain) to *the files its readers name*. Python 3.14's `discover` imports no namespace package. The
  only `load_tests` (`test_xdist_ci`) is undeclared and always runs. Not held: a sub-package once it is on the base
  (T033).
- **T028:** `base.makefile_changes` compares the three names raw, by `lstat`, so a symlink, a deletion, a mode change
  or an ignored new `GNUmakefile` differs. GNU make reads no case variant on Linux, and the root `Makefile` includes
  nothing.
- **T029:** both change-set scripts are full rows. `verify_scoped/*` imports only its own package and the stdlib, and
  `check-slice-scope.merge_base`/`changed_files` read only `project.json` (full) and git. `GITHUB_BASE_REF` and
  `CI_MERGE_REQUEST_TARGET_BRANCH_NAME` can only move the base back (`older_of`).
- **T030:** the pin (`test_select_tests_real_declared`) is an equality and runs on every selected run. `held()` is
  narrower than its words (T036).
- **T031/T032:** `make verify-checks` with `FULL=`, `-e`, `FULL=0` in the environment, and `MAKEFLAGS=FULL=` each hand
  the selector `FULL='1'` (stub selector). `make verify TESTS=' '` takes the stamped path and runs whole. Not held: a
  `test` goal ahead of `verify-checks` (T035), and an empty `TESTS` beside `SKIP` (T034).

**Constitution, principle by principle the diff touches:**

- *I, a scoped gate MUST be additive:* `make verify` is whole on its stamped path (patched `Makefile:58`, `:60`),
  and `verify-checks` is whole under every variable route tried (`override export FULL := 1`). **Not met** where
  `TESTS` is empty beside `SKIP`: the gate ends `all gates passed` with no test (T034). CI markers make every run full
  (`scripts/select_tests/__init__.py:15`, `:23`).
- *I, `VERSION` and a fragment for every user-visible change:* satisfied. `git diff --stat 8072724..HEAD -- assets
  src/slipwai catalog.json VERSION changelog.d` is empty (AC-S38-17), so no bump is owed.
- *VIII, deterministic: the same inputs give the same verdict:* **not met** by T033, where on one commit the full run
  fails and the selected run passes.
- *AGENTS, no mocking framework:* satisfied. The new tests (`test_select_tests_caches`, `_real_declared`, and the
  additions to `_changes`, `_paths`, `_declarations`, `_make`, `_makefile`) use the fixture's stand-ins, with no
  `unittest.mock`.
- Money, time, identity, idempotency and persisted schema are not touched (a test-runner script).

**Each level:**

- **Domain** (`rules`, `declarations`, `choose`): proven — the path rows (full rows, sub-package files, the change-set
  scripts) by `rules.claim` over edge paths. Caches match `reads` only. Not proven: a sub-package on the base (T033),
  and `held()`'s routes (T036).
- **Use case** (`select-tests.py`): proven — what is printed is what runs, for the top-level modules. A cache never
  makes the run full. An ignored non-cache file under the three trees is full under every pathspec-modifying `GIT_*`
  variable (`GIT_GLOB_`, `NOGLOB_`, `ICASE_`, `LITERAL_PATHSPECS`). Not proven: the total omits a sub-package's modules
  (T033).
- **Delivery adapter** (the patched root `Makefile`): proven — `FULL` reaches the selector from `verify-checks` under
  every variable route. `TESTS`/`SKIP` from the command line or environment word the line correctly when non-empty.
  `make -f delivery/Makefile verify` reaches the root `make test` through the ratchet, as AC-S38-3 says it may. Not
  proven: T034, T035.
- **Screen:** none.
- **Published contract** (`make test`/`make verify`, `docs/maintaining.md`): green on the patched copy. T034 changes
  what an empty `TESTS` means against the contract `8072724` published.

Checked and clean, beyond pass 1's list: an ignored file outside `assets/`, `src/` and `tests/` (e.g.
`scripts/select_tests/zz_probe.py` under `.git/info/exclude`) is not listed. AC-S38-10 scopes ignored files to those
three trees, and an unimported file is inert, so this is recorded as scope, not a finding. `make test TESTS=' '` or
`SKIP=' '` selects, the default and not a narrowing the person asked for. When `TESTS` and `SKIP` are both given,
`TESTS` wins, as it did before the patch. Scratch removed: `/tmp/s38/converge2`, `/tmp/s38/probe`, `/tmp/s38/held`
and two logs.

### After pass 2 (host, cruise iteration 24) — the findings fixed; the verdict this slice stops at

Pass 2's four findings are fixed and each is held by the RED its task named: T033 `afdd6e2` (a sub-package anywhere in
the tree makes the run full, named), T036 `17ab354` (the under-claim check reads the closure for the launcher by path
and `slipwai.cli`), T034/T035 `563bdf8` + `f699166` (`s38.patch` regenerated: an empty `TESTS` reads as unset, a `SKIP`
naming every module says no module runs — R-9, the host's answer to pass 2's question — and `verify-checks` makes
`test` itself with `FULL=1`, whole in any goal order). The data model says each. On a fresh clone of the tip with
`s38.patch` applied, every `test_select_tests_*` module, `test_select_tests_pin` and the four `test_factory_gate_stamp*`
modules: 223 tests, OK (122.7 s). A dry run there on a throwaway `slice/x` with one go-asset line changed and `SINCE`
its parent: the SINCE line, 5 modules skipped with their reasons, the seven backend readers narrowed to `go`,
`selected 334 of 339`; without `SINCE`, `full: \`.gitignore\` changed — the ignore rules: …` (the trunk's diff).
`git diff --stat 8072724..HEAD -- assets src/slipwai catalog.json VERSION changelog.d` is empty (AC-S38-17).

**Verdict: converged on the patched tree, with no CRITICAL or HIGH open — two passes as briefed, the second's
findings fixed and held by their tests, not judged again by a third pass.** Blocked at T019: until a person applies
`s38.patch`, the 22 tests of `test_select_tests_make` and `test_select_tests_makefile` fail on this branch with the
line naming the patch (AC-S38-14), and the demo (T023) cannot run. Noted, not a finding: `verify-checks` now runs
`test` after lint, typecheck and check-structure rather than beside them under `make -j`.

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
