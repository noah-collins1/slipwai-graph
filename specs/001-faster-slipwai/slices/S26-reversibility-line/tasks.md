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

### Pass 1 — 2026-10-07, `drive-converge` — **converged** (no open CRITICAL or HIGH)

Read against `.specify/memory/constitution.md`, AC-S26-1..17 (AC-S26-15 as amended and AC-S26-17 from `adopt-method`
at `bfd3ff5`), D174–D178, D183–D185, ADR 0007 (Proposed) and this plan (Q5 taken as option (b)), over
`git diff 063c187..b6f8c68` outside `specs/`. Evidence: probes in a scratch project under `.cruise27/`, mutations
restored by path, and `make test TESTS="test_reversibility_score test_reversibility_gate test_reversibility_versions
test_reversibility_writers test_decisions_gate_differential test_decisions_scope_gate test_toolkit test_utf8_io
test_changelog test_assets_bytecode test_cruise test_cruise_record test_cruise_scope_writers"` (116 tests, OK) and
`test_reversibility_migrate` (OK) after the fixes; `make lint typecheck check-structure` 0 before each commit.

**Constitution, principle by principle the diff touches.**
- I (owns its files): `.slipwai/propagated` and `scripts/reversibility.py` reach a project only through `generate` and
  `migrate` (`src/slipwai/scaffold.py` `project_files`, `files[PROPAGATED] = propagated_file(files)`, so `replay`
  regenerates it); the catch-up is `changelog.d/reversibility-line.md:9`. The fragment's line 1 is `MINOR`; `VERSION`
  untouched. *Scoped gate additive*: holds — the merge root and CI run the full gate — but see O1.
- VIII (a persisted shape is a contract): the line names `rules <n>`; `RULES` in `reversibility.py` keeps every
  version and `test_reversibility_versions` e2 freezes version 1 by digest; `measures.py` and `SPELLING` unchanged
  (e3). The gate refuses unknown keys only on a label this release defines (D176, D65; versions e2 states the one
  moved log shape).
- VII (auditability): one finding per fault naming `<file>:<line>: D<n>` and the field (`line_findings`,
  `rule_findings`); the verb names the rules that fired on stderr.
- XIV and the ADR rule: ADR 0007 stays `Proposed`; the plan's product questions went to the host (D183–D185, Q5).
- *Persisted data records facts true on any machine*: the list is committed project-relative paths (not ignored in
  `gitignore.py`, which ignores only `.slipwai/catch-up.md`); `.delivery-tools/written.json` is never read.
- No money, time zone, identity or personal data is touched.

**Findings by level** (severity; fixed or open):

Domain — the rule table matches data-model.md (H1–H7, R1, R2, F1, F2, D1, D2, U1); fail-closed for a missing or
unaccepted fact and an unreadable scope; `size`/`urgency` refused, never scored, by both verb and gate; version 1
frozen. No finding.

Use case
- **F7 LOW, fixed `9e666a1`** — a full stop after the `(same shape as D<a>, D<b>)` parenthesis made the gate say
  "cites fewer than two"; now read (`ProposedRuleTest` e5b).
- **Guards added, `9e666a1`** — nothing held "a log with neither label never loads the module" (removing the guard
  passed every test with the module present) nor the verb's copies of the gate's `scope_tokens`/`paths_of`. Now
  `test_reversibility_versions` e5 (a fake `reversibility.py` that exits on load; shown to fail with the guard
  mutated out) and `test_the_verb_reads_scope_and_written_to_as_the_gate_does` (shown to fail with `one_id` mutated
  out of the verb's copy).
- **O2 LOW, open, no change** — the verb accepts no `--written-to`; with a listed path in the entry's `Written to` it
  prints `migrate_file=no` and the gate refuses it. The gate is right (under-declaration caught); both briefs pass
  `--written-to`.
- **O3 LOW, open, no change** — a log with the labels but no `reversibility.py` beside the gate gets a note and
  passes; by design and tested (`test_a_log_with_a_line_and_no_sibling_module_is_noted_not_refused`).

Adapter
- **F5 LOW, fixed `9e666a1`** — a committed list that is not UTF-8 made the gate print a traceback (its rule is one
  line, never a traceback) and the verb a codec message; an unreadable list is now no list, failing closed as a
  missing one does (`test_a_list_that_is_not_utf8_is_no_list_said_in_one_finding`).
- **F6 LOW, fixed `9e666a1`** — the missing-line note named `python3 scripts/reversibility.py` in an adopted layout,
  where `layout.repoint` leaves `scripts/` content alone and the verb is `delivery/scripts/reversibility.py`; the gate
  now passes the path it loaded (versions e6).
- **O1 MEDIUM, open, outside this slice's files** — `assets/toolkit/scripts/verify_scoped/table.py`'s
  `check-decisions` row names `specs/` and `docs/event-model/model.yaml`, but the gate now also reads
  `.slipwai/propagated` (generated) and `<delivery>/.written` (adopted). A change to the list alone lets a scoped run
  skip `check-decisions` although its answer can change (a `Written to` path newly listed refuses `migrate_file=no`).
  `tests/test_verify_scoped_record.py` e4 cannot see it: its scan follows imports, not `sibling()`'s load by path.
  The full gate still runs at the merge root and in CI, so principle I's additive MUST holds. The table is S07's
  file: widen the row with `.slipwai/propagated` and the delivery `.written` (and teach the scan `sibling()` loads),
  in S07 or a follow-up the host assigns.
- Encoding and bytecode: every `read_text` names UTF-8; `sibling()` sets `dont_write_bytecode`; `test_utf8_io` and
  `test_assets_bytecode` pass.

Published contract
- **F1 MEDIUM, fixed `9e666a1`** — the verb printed a line the gate refused: a fact value holding whitespace
  (`schema="a b"`, a tab, a newline) was written as given, and the gate split the facts there (`has 'b', which is not
  key=value`). The whole class is whitespace in a value; the verb now refuses it as usage, exit 2. No other value the
  verb accepts splits the line (`·`, arrows and tier words were already refused).
- **F2 MEDIUM, fixed `054150e`** — `DECISION_ENTRY`'s line ended `— from python3 scripts/reversibility.py`; a writer
  filling the placeholders keeps it and the gate refuses (`has '—'`). One constant, so every copy (generated and
  adopted `commands/cruise.md`, `.specify/product-owner.md`) is fixed: `<facts, as … prints the line>`.
- **F3 MEDIUM, fixed `054150e`** — the `Proposed rule:` template line carried no optional marker; filled as shown it
  is refused (`cites fewer than two`) while AC-S26-15 says lacking it is never refused. Now `<optional: …>`.
- **F4 MEDIUM, fixed `054150e`** — the standalone Catch-up said `migrate` brings `scripts/reversibility.py` and
  `.slipwai/propagated`, false for an adopted repository; it now says, labelled experimental, that the script lands
  under the delivery directory and the verb reads the `.written` already there.
- **F8 LOW, fixed `9e666a1`, `054150e`** — `REVERSIBILITY_RULE` had a 161-character line in the generated command;
  the skipper paragraph broke mid-sentence; `reversibility.py` docstring lines at 135 and 124. Rewrapped; no line the
  slice adds is over 120 but `DECISION_ENTRY`'s field lines, which cannot wrap.
- **O4 LOW, open, the host's** — Q5: AC-S26-16's "keeps the old entry shape until edited by hand" and the owner-brief
  page's "`slipwai migrate` never rewrites it" (`decisions.py`, predates the slice) disagree with what `migrate` does;
  the Catch-up states the tree's behaviour.
- **O5 LOW, open, predates the slice** — `DECISION_ENTRY`'s `Scope:` line carries the same kind of trailing annotation
  (`— a feature-level or doubtful decision is \`global\``) that the gate refuses if kept.
- `SPELLING` unchanged; lines the verb writes, chains included, are read by `decision_health` as computed (versions
  R9 tests). A hand-written line with a tier word inside a fact value can only be accepted at `hard`, which the
  escalation share does not count, so S39's reader is not misled.

**Budgets.** `reversibility.py` 318 lines; every new test module and `src/` file is under 350.
`assets/toolkit/scripts/check-decisions.py` was 699 at the base and is 728 (outside `check-structure`'s scope, and the
reason the rules live in a module beside it); LOW, no change.

**Tasks appended:** none that re-open the loop. O1 (MEDIUM) is for the host to assign to S07's table.

### After-converge tasks (from `/home/noahc/math/.cruise27/gaps-after-S26.md`, the host's gaps pass)

Each one starts with a failing test and closes the whole class, not only the instance. Two groups of tasks run in parallel. **A** is the toolkit chain (T010–T015), which owns `assets/toolkit/scripts/reversibility.py`, `check-decisions.py` and the `tests/test_reversibility_{score,gate,versions}.py` and fixture files. **B** is T016 and T017. T016 owns `src/slipwai/project/{cruise_agents,cruise_record,decisions}.py` and `tests/test_reversibility_writers.py`; T017 owns `tests/test_reversibility_migrate.py`. Inside each group the tasks are sequential, one commit each.

- [x] T010 **M1 MEDIUM — the facts belong to a rules version** (AC-S26-11, FR-051). The parser and rule U1 read the fact list of the version the line names, and `HARD_FACTS` belongs to its version too. A test adds a fact in a v2 (the fake is written in the test tree) and shows that every v1 line still passes, and that a v1 line carrying the new fact is refused as an unknown key.
- [x] T011 **M2 MEDIUM — `Written to` paths are normalised before the list is consulted** (AC-S26-8). The verb and the gate share one normaliser, which handles `./`, a directory (a match if any listed file is under it) and a backslash path. Tests cover each case in both the verb and the gate.
- [x] T012 **M3 MEDIUM — the verb writes UTF-8** (AC-S26-14). `main` sets stdout and stderr to UTF-8 at its start, as `check-slice-scope.py` does. A test runs the verb under `PYTHONIOENCODING=cp1252` with a `--raise` chain, and also with `ascii`.
- [x] T013 **M4 MEDIUM — fenced code blocks are not the line** (AC-S26-10, D65). When the gate finds the `Reversibility:` and `Proposed rule:` labels, it skips lines inside a fence, both for the decision to load the module and for the labels the module reads. Tests: an entry that quotes the line in a fence and has no real line passes, the same as the released checker. An entry with a fenced quote and one real line is not "more than one".
- [x] T014 **L1 LOW — text after the citation is allowed** (AC-S26-15). The gate refuses only fewer than two ids or an id that is no entry.
- [x] T015 **L2 LOW — cited ids are earlier entries** (AC-S26-15 "earlier"; D185 dropped only *standing*). A cited id that is not lower than the entry's own number is refused, naming it.
- [x] T016 **L3 LOW and D189 LOW — the briefs show quoted flags; the owner-brief template says what migrate does.** The skipper brief and the host's `REVERSIBILITY_RULE` show the verb with its flags quoted, e.g. `--scope 'S1, S2' --written-to 'a, b'`, and the host text names the flags. In `decisions.py`, the template sentence *`slipwai migrate` never rewrites it* changes to say that `migrate` merges the factory's changes and never overwrites the project's own edits. The fragment's catch-up is unchanged in substance.
- [x] T017 **AC-S26-16's test gap — a migrated project's own checks.** `test_reversibility_migrate` (or a new module) runs the checks of `make verify` that read the new files on a project migrated from `063c187`: at least `lint`, `check-structure` and `check-decisions`. It runs the full `make verify` if the starter allows it in a minute or two.

L4 (the generated list leaves out CI workflows) is the host's sentence in ADR 0007, not a task here.

After-converge result (cruise iteration 27): T010 `b5c4972`, T011 `791372e`, T012 `11cbcf3`, T013 `4922aec`, T014
`51d0519`, T015 `09fc839`, T016 `6f8b247`, T017 `46ff82b`. Each began with a RED that failed on an assertion against
the unchanged code. T017 is the exception: it guards behaviour that already stood, so it passed when written, and its
teeth were shown in a scratch project. The touched modules plus the toolkit set (192 tests, 1 skipped) pass, and so
do `make lint typecheck check-structure`. No fix grew larger than its finding, so no second converge pass was run.
`reversibility.py` is at 340 of 350 lines. Rules are versioned by convention: a future `rules_vN` reads its own
`FACT_LISTS[N]` for U1, and the test fake does exactly that. Still open: O1, the scoped-gate inputs, which belong to
S07's table; and L4, a sentence in ADR 0007, which is the host's.
