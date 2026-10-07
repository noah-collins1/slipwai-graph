# Tasks: S26-reversibility-line — every decision says how hard it would be to take back

**Input**: [plan.md](plan.md) (*The example map* R1–R10 is what the tasks cut on; *Structure Decision*; *Tests*;
*Pin*), [data-model.md](data-model.md), [research.md](research.md), [quickstart.md](quickstart.md); acceptance criteria
AC-S26-1 … AC-S26-16 in `specs/001-faster-slipwai/spec.md` under `### S26-reversibility-line`; D174–D178 in
`specs/001-faster-slipwai/decisions.md`.

**Branch**: `slice/S26-reversibility-line` (worktree `../slipwai-graph-S26-reversibility-line`). No push. One commit
per task.

**Delegation**: one delegate per task, each its own RED-GREEN-REFACTOR increment (constitution V): write the rule's
examples, see them fail for the right reason, make them pass, refactor. A task's "Files" line is its manifest: the only
files that delegate may write. Nobody but the host writes `tasks.md`. Tasks are tagged `[US1]` (the verb and its
facts), `[US2]` (the gate), `[US3]` (the writers and the briefs), `[US4]` (a project made before). The slice has no
screen: `## Design review` reads `No screen in this slice`. AC-S26-16's last clause is the demo
([quickstart.md](quickstart.md)), not a task.

**Default is sequential**, in the order below. Phase 5 names the only tasks whose manifests are disjoint and which
may run alongside each other; the host dispatches them concurrently only if it chooses to.

**Cuts from the map.** R6 and R9 would each have an empty GREEN as their own task (R6's version dispatch is what R4
needs to name `rules 9` unknown; R9 leaves `measures.py` unchanged and proves a reader against output the verb
already writes), and R5's e1 is a guard over the loader R4 adds. So R6 is folded into T004 (R4), R9 into T003 (R2,
the task after which the verb's output is final) and R5's e1 into T004; every example stays, in the task that
produces the behaviour it guards. No task instructs a test that passes the moment it is written without saying so and
naming the behaviour it guards.

## Constraints

Constraints that hold for every task's GREEN, stated once:

- **Size.** Every file under `tests/`, `src/` and `scripts/` stays at or under 350 lines (`make check-structure`);
  each new test module ≤ 350; `src/slipwai/project/cruise.py` is at 341, so T008's change there is two lines in place
  and nothing grows beyond 350. A task that would overrun asks the host to name a new module rather than growing one.
  `assets/toolkit/scripts/reversibility.py` (new) targets ≤ 350.
- **Repository rules.** No edit under `delivery/`, to `VERSION` (stays `1.6.0.dev0`), `catalog.json`,
  `decisions.md`, `spec.md`, `story-split.md`, the register (`slices/README.md`), `project.json`, the root `Makefile`,
  `assets/toolkit/scripts/agents/measures.py` (AC-S26-13), nor to any record under `specs/` but this slice's folder.
  No manifest names S07's files (`assets/toolkit/scripts/verify_scoped/`, `check-ux-gates.py`) or S43's (`tests/`
  `TEST_SELECTION` declarations and helper moves).
- **Encoding.** Every `open` and `read_text` names `encoding="utf-8"`.
- **Bytecode.** Tests set `sys.dont_write_bytecode = True` before loading any toolkit script; scripts under `assets/`
  run as `python3 -B`; no `__pycache__/` is left under `assets/`.
- **Tests.** Fakes live in the test tree (a copied `reversibility.py` with a version 2 is a file written there); never
  `unittest.mock` or any mocking framework. Examples enter through the verb or the gate as `python3 -B` subprocesses
  against a scratch project (`tests/reversibility_fixture.py`), or through `slipwai generate`/`replay`/`migrate`.
- **Commits by path.** `git add <exact paths of the task's manifest>`, never `git add -A`. `make lint typecheck
  check-structure` before each commit, `$?` tested, never chained after a pipe.
- **Test runs.** `make test TESTS="<only the modules the task touches or reads>"`, never the whole suite. Whenever
  `assets/toolkit/` changes, also `make test TESTS="test_toolkit test_utf8_io test_changelog test_assets_bytecode"`.
- **Scratch** only under `/home/noahc/math/.cruise27/`, literal paths, cleared when done.
- **Fragment.** `changelog.d/reversibility-line.md` (first line `MINOR`) is created by T002, the first task that
  changes a user-visible file; later tasks do not touch it until T009 completes it.
- **Pin.** T001's modules run green before T002 and again after T009; a refusal or output they assert is changed only
  in the increment that changes it, and only that line.

## Phase 1: Pin (before any change)

- [x] T001 [US2] **Pin — what already holds** (plan *Pin*; D65). Factory code needs no separate pin file: its tests
  are the pin. Run and report, green and unchanged, before any edit: `make test TESTS="test_decisions_gate_differential
  test_decisions_scope_gate test_decisions_scope test_hand_backs_coverage test_cruise_scope_writers test_cruise_record
  test_cruise test_replay test_adopt test_benchmark_feature test_toolkit test_utf8_io test_changelog
  test_assets_bytecode"` (drop any name `ls tests/` does not show and say which). Note the line count of
  `tests/test_decisions_gate_differential.py` (112) and `assets/toolkit/scripts/check-decisions.py` (699). No file is
  written, no commit.
  Files: none.

## Phase 2: US1 — the verb (sequential)

R1 and R2 both write `reversibility.py` and the score test, so they run in order. T002 also writes the shared fixture
(no separate setup task).

- [x] T002 [US1] **R1 — the verb scores declared facts** (AC-S26-1, -2, -3, -4, -5, -6, -7, -14 for the verb's half).
  `assets/toolkit/scripts/reversibility.py`: `FACTS` (the closed list, order and accepted values of data-model.md),
  `RULES = {1: …}`, `score()`, `main()` — `--scope`, `--written-to`, `--raise`, `key=value`…; stdout the whole
  `- **Reversibility:** …` line, stderr one line naming the rules that fired, exit 2 with one stderr line and empty
  stdout on a stray key, a repeated key, a non-`key=value` argument or a lowering `--raise`. `tests/reversibility_fixture.py`
  (scratch project: `project.json` with or without `origin`, the two scripts copied from `assets/toolkit/scripts/`,
  `README.md`, `specs/f/decisions.md`; `score(...)` and `gate(...)` subprocess helpers; an entry builder). Also
  `changelog.d/reversibility-line.md`: first line `MINOR`, a stub **Catch-up.** paragraph (completed in T009).
  RED→GREEN: e1 AC-S26-1's facts, `--scope S26-reversibility-line`: `easy` · e2 each of the seven hard facts `yes`
  alone: `hard`, seven tests · e3 `rollback_complexity` `days`, `needs-migration`: `hard`; `hours`: `guarded`;
  `trivial`: `easy` · e4 `behind_flag=no`: `guarded`; `no-code`: `easy` · e5 `flag_default=yes`: `guarded` · e6 scope
  of two ids: `guarded`; `global`: `hard`; an unreadable scope: `hard` · e7 `schema` omitted: `hard`, the line carries
  `schema=missing`; `rollback_complexity=weeks`: `hard`, the line carries it · e8 plus `size=large`, and plus
  `urgency=high`: exit 2, stderr names the key, stdout empty · e9 the D54 fixture (`ci_workflow=yes migrate_file=yes
  behind_flag=no-code`, `Written to` two records, no commits): `hard` · e10 `--raise hard` from `easy`: `easy →
  guarded → hard`; `--raise guarded` from `hard`: exit 2. Pin: T001's modules stay green. Run the toolkit module set.
  Files: `assets/toolkit/scripts/reversibility.py`, `tests/reversibility_fixture.py`,
  `tests/test_reversibility_score.py`, `changelog.d/reversibility-line.md`.

- [x] T003 [US1] **R2 — the committed list raises `migrate_file`; and R9 — S39's reader reads the verb's lines**
  (AC-S26-8, -7, -13). `reversibility.py`: `propagated(root)` (`<delivery>/.written` where `project.json`'s `origin`
  is `adopted`, `.written` at the root where `layout.delivery` is `.`, else `.slipwai/propagated`), and the raise in
  `score()`. RED→GREEN for R2: e1 generated, `--written-to "\`scripts/check-decisions.py\`"`, list names it,
  `migrate_file=no`: line carries `migrate_file=yes`, `hard`, stderr says so · e2 adopted (`origin: adopted`,
  `layout.delivery: delivery`), `delivery/.written` names the path: the same · e3 a `Written to` of `specs/f/spec.md`
  only: `migrate_file=no` stands · e4 no list: `migrate_file=no-list`, `hard` · e5 a declared `yes` with no path on
  the list: `yes`, never lowered. R9, folded here because the verb's output is final after this task, is a guard over
  `measures.decision_entries` / `decision_health` read by path with bytecode off (`measures.py` unchanged): e1 twenty
  entries carrying verb output, four of them `--raise hard`: tiers and escalation share as computed (20 %) · e2 `easy
  → guarded` is not an escalation to hard · e3 `git diff 063c187 -- assets/toolkit/scripts/agents/measures.py` is
  empty. R9's examples pass the moment they are written; keep them as the guard and say so in the report. Pin: T001
  stays green. Run the toolkit module set.
  Files: `assets/toolkit/scripts/reversibility.py`, `tests/reversibility_fixture.py`,
  `tests/test_reversibility_score.py`, `tests/test_reversibility_versions.py`.

## Phase 3: US2 — the gate (sequential)

R4–R7 write `check-decisions.py` and `reversibility.py`, so they run in order, after Phase 2.

- [x] T004 [US2] **R4 — the gate holds the line; with R6 — old lines under newer rules; and R5's e1 — old logs get the
  earlier answer** (AC-S26-9, -10, -11, -14; FR-051 last sentence; D65). `reversibility.py`: `parse_line()`,
  `check_log()` (findings and notes for one parsed log, given the gate's own `scope_tokens` and `STATUS`; re-derives the
  first tier under the version the line names; R2's list check as a refusal); `check-decisions.py`: the module
  docstring, `sibling(name)` shared with `hand_backs_module()`, and `gate()` loading `reversibility.py` by path with
  bytecode off only for a log whose text carries a `- **Reversibility:**` or `- **Proposed rule:**` label.
  RED→GREEN for R4: e1 a well-formed `easy` line on an AC-S26-1 entry: exit 0 · e2 `Reversibility: medium …`: refused,
  names D1 and `Reversibility` · e3 `easy → hard`: refused as a skipped step; `hard → guarded`: refused as lowering ·
  e4 `rules 9`: refused · e5 `size=large` on the line: refused naming `size` · e6 two lines: refused · e7 `easy` with
  `ci_workflow=yes`: refused, names `ci_workflow` · e8 `hard` with `schema=maybe`: accepted · e9 `migrate_file=no` with
  a `Written to` on the list: refused naming `migrate_file` · e10 `easy → guarded → hard` whose first tier is right:
  accepted. R6: e1 a fake in the test tree (`reversibility.py` copied with a version 2 that makes `behind_flag=no`
  `hard`): a log with a version-1 `guarded` line for it passes, a version-2 line saying `guarded` for the same facts is
  refused · e2 the digest of version 1's tier over every fact vector of the closed value sets and the three dependants
  classes equals the one written in the test (a guard: it passes when written; it freezes the shipped version). R5 e1
  (a guard over the loader): every case of `test_decisions_gate_differential` plus this repository's own log, through a
  scratch project that also holds `reversibility.py`, equal to the released checker at `596740f`. Pin: T001 stays green.
  Run the toolkit module set.
  Files: `assets/toolkit/scripts/reversibility.py`, `assets/toolkit/scripts/check-decisions.py`,
  `tests/reversibility_fixture.py`, `tests/test_reversibility_gate.py`, `tests/test_reversibility_versions.py`,
  `tests/test_decisions_gate_differential.py`.

- [x] T005 [US2] **R7 — a proposed rule cites two entries of the feature** (AC-S26-15 gate half, as amended by D185). `reversibility.py`
  `check_log()` reads a `- **Proposed rule:** … (same shape as D<a>, D<b>)` line: at least two distinct ids other than
  its own entry's, each the heading of an entry in the same log (its `Status` is not read — D185); one finding naming the
  entry and `Proposed rule` otherwise; an entry without the line never refused. RED→GREEN: e1 D3 citing D1, D2 standing:
  exit 0 · e2 citing D1 only: refused · e3 citing D1, D9 (absent): refused naming D9 · e4 citing D1, D2 with D2
  `overridden by D3`: **accepted** (D185, D65) · e5 citing D3 and D1 from D3: refused (its own id does not count) · e6 no entry
  has the line: nothing new. Run the toolkit module set.
  Files: `assets/toolkit/scripts/reversibility.py`, `tests/test_reversibility_gate.py`.

- [x] T006 [US2] **R5 (remainder) — a missing line is a note** (AC-S26-10; D176). `check_log()` and `gate()` print, for
  each entry without the line that comes after one with it, one `check-decisions: note: <file>:<line>: D<n> has no
  \`Reversibility:\` line after an entry that has one; score it with python3 scripts/reversibility.py`, exit unchanged;
  entries before the first line get none. RED→GREEN: e3 D1 with the line, D2 without: exit 0, one note naming D2 and the
  verb · e4 D1 without, D2 with: no note. e2 (a log holding `- **Reversibility:** whatever`: the released checker
  passed it, the gate now refuses it, the only log shape whose answer moves, D65's carve-out, stated in the test) passes
  once T004 stands: write it here with the carve-out comment as a guard beside e3, which is the RED. Run the toolkit
  module set.
  Files: `assets/toolkit/scripts/reversibility.py`, `assets/toolkit/scripts/check-decisions.py`,
  `tests/test_reversibility_versions.py`.

## Phase 4: US3 and US4 — the writers, and a project made before

- [x] T007 [US3] **R3 — `generate` writes the list, `migrate` carries it** (AC-S26-8, AC-S26-17; D175, D183). `src/slipwai/assets.py`:
  `PROPAGATED = ".slipwai/propagated"` beside `NOTES`; `src/slipwai/project/propagated.py` (new):
  `propagated_file(files)`; `src/slipwai/scaffold.py`: where no adoption is given, the list is added after
  `layout.relocate` and before the adoption cut, so `replay` regenerates it. RED→GREEN: e1 a generated project, both
  profiles: the list exists, names `scripts/check-decisions.py`, `scripts/reversibility.py`, `commands/cruise.md`,
  `.specify/product-owner.md`, `Makefile`, and names no path under `apps/`, `docs/`, nor `README.md` · e2 `slipwai
  replay` of it reproduces the list byte for byte · e3 an adopted repository: no `.slipwai/propagated`, `.written` as
  before · e4 the path `reversibility.py` reads equals `assets.PROPAGATED`. Pin: `test_replay`, `test_adopt` stay green.
  Run `make test TESTS="test_reversibility_writers test_replay test_adopt"`.
  Files: `src/slipwai/assets.py`, `src/slipwai/project/propagated.py`, `src/slipwai/scaffold.py`,
  `tests/test_reversibility_writers.py`.

- [x] T008 [US3] **R8 — the shape and the briefs write it** (AC-S26-12, -14, -15). `src/slipwai/project/cruise_record.py`:
  `DECISION_ENTRY` gains `- **Reversibility:** <tier> · rules <n> · <facts> — from python3 scripts/reversibility.py`
  after `Confidence` and `- **Proposed rule:** …` as an optional line, and `REVERSIBILITY_RULE` (run the verb for every
  entry the session writes; add the feature's entry headings — each `D<n>` with its heading, Stage and Scope — to every
  skipper brief); `cruise_agents.py` `SCORE_VERB` and the skipper's brief (run the verb with the declared facts;
  escalate one tier at a time with `--raise`, writing each step; never lower a computed tier; never leave a question in
  a diff or a note instead of escalating; after three standing entries of the feature decided by the same reason add the
  `Proposed rule:` line citing the earlier ids, decide the question anyway, never edit the owner brief; out-of-scope
  headings are evidence for the count, never binding); `cruise.py` interpolates `REVERSIBILITY_RULE` after the entry's
  shape, in place (two lines, file stays at or under 350); `decisions.py` one sentence in *What the record looks like*
  naming the verb. Paths are re-pointed to `delivery/scripts/reversibility.py` in an adopted project by the existing
  rewriting. The existing assertions on `DECISION_ENTRY` or the skipper's brief in `tests/test_cruise_record.py` and
  `tests/test_cruise.py` are updated, only those lines. RED→GREEN: e1 a generated project: `commands/cruise.md` and
  `.specify/product-owner.md` hold `DECISION_ENTRY` with both lines · e2 `agents/drive-skipper.md` names the verb,
  `--raise`, `one tier at a time`, `never lowers`, `Proposed rule:`, `never edits` the owner brief · e3 the cruise
  command tells the host to run the verb and to add the headings list · e4 an adopted repository: the same text with
  `delivery/scripts/reversibility.py`. Pin: `test_cruise_scope_writers`, `test_cruise_record`, `test_cruise`,
  `test_hand_backs_coverage` stay green.
  Files: `src/slipwai/project/cruise_record.py`, `src/slipwai/project/cruise_agents.py`,
  `src/slipwai/project/cruise.py`, `src/slipwai/project/decisions.py`, `tests/test_reversibility_writers.py`,
  `tests/test_cruise_record.py`, `tests/test_cruise.py`.

- [x] T009 [US4] **R10 — a project made before** (AC-S26-16; D65). `tests/test_reversibility_migrate.py` takes the
  factory at `063c187` with `git archive` (as `test_benchmark_elapsed_migrate.old_factory` does) into a scratch dir,
  generates a project there, writes a decisions log (no line), runs this checkout's `slipwai migrate`; and completes
  `changelog.d/reversibility-line.md`: its one **Catch-up.** paragraph stands alone and names the line, the verb, the
  committed list, the note for a missing line, and that the owner brief keeps the old shape until edited by hand.
  RED→GREEN: e2 the fragment's words (a test reads the first line `MINOR` and the one paragraph; this is the RED) · e1
  the migration: `scripts/reversibility.py` and `.slipwai/propagated` arrive, `make check-decisions` passes as before,
  `.specify/product-owner.md` is unchanged, an entry appended with the verb's line passes (e1 passes once T002–T008
  stand: keep it as the guard, say so). Finally run T001's modules once more and `make test TESTS="test_reversibility_score
  test_reversibility_gate test_reversibility_versions test_reversibility_writers test_reversibility_migrate
  test_toolkit test_utf8_io test_changelog test_assets_bytecode"`.
  Files: `tests/test_reversibility_migrate.py`, `changelog.d/reversibility-line.md`.

## Phase 5: Parallel opportunities

The default is the order above, one delegate at a time. Disjoint manifests allow exactly one concurrent split:

- **T007 and T008 may run alongside T004 → T005 → T006** (the gate chain). Neither side names a file the other
  writes: the gate chain owns `assets/toolkit/scripts/reversibility.py`, `check-decisions.py`, `reversibility_fixture.py`,
  `test_reversibility_gate.py`, `test_reversibility_versions.py` and `test_decisions_gate_differential.py`; T007–T008 own
  `src/slipwai/`, `test_reversibility_writers.py` and the two cruise test modules. T007 needs T003 done first (its e4
  reads `reversibility.py`'s list path); T008 follows T007 (both write `test_reversibility_writers.py`). Mark: **[P]**
  across the two chains only, never inside one.
- **Not parallel**: T002 → T003 → T004 → T005 → T006 (one module, one gate, one fixture); T007 → T008 (one test module);
  T009 after everything (it reads all of it and completes the fragment T002 created). T001 first.
- A delegate for either side runs only its own manifest's tests; the host runs the toolkit module set after the
  chains rejoin.

## Design review

No screen in this slice.

## Convergence

