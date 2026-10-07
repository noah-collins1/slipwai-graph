# Tasks: S27-provisional-decisions — a decision that is easy to take back no longer stops a slice

**Input**: [plan.md](plan.md) (*The example map* R1–R13 is what the tasks cut on; *Structure Decision*; *Pin*; *Plan
decisions* P1–P6), [data-model.md](data-model.md), [research.md](research.md), [quickstart.md](quickstart.md);
acceptance criteria AC-S27-1 … AC-S27-17 in `specs/001-faster-slipwai/spec.md` under `### S27-provisional-decisions`;
D195–D201 (with D54, D62, D65, D132, D174–D178, D183–D185) in `specs/001-faster-slipwai/decisions.md`; ADR 0008 stays
`Proposed`.

**Branch**: `slice/S27-provisional-decisions` (worktree `../slipwai-graph-S27-provisional-decisions`). No push. One
commit per task.

**Delegation**: `.specify/drive.json` `delegate=story`, `cycle=rule`: the story's rules are handed to `drive-implement`
delegates by disjoint manifest (chain A, chain B, then Phase 4), each task its own RED-GREEN-REFACTOR increment (constitution V): write the rule's examples, see them fail for the right reason, make them pass,
refactor. A task's "Files" line is its manifest: the only files that delegate may write. Nobody but the host writes
`tasks.md`. Every implementation task is tagged `[US8]` (User Story 8). The slice has no screen: `## Design review`
reads `No screen in this slice`. The demo ([quickstart.md](quickstart.md)) is the host's `drive-hand` stage, not a task.

**Default is sequential**, in the order below. Phase 5 names the only tasks whose manifests are disjoint.

**Cuts from the map.** R6 (old logs get the earlier answer) is a guard over the loader that R3 adds, so it would have
an empty GREEN as its own task; it is folded into T004 (R3), which adds the loader, and every R6 example stays in
that task. R13's e1 (the migration) passes once T002–T013 stand; it is kept as the guard beside e2, the fragment's words,
which is the RED. No other task instructs a test that passes the moment it is written without saying so and naming
the behaviour it guards.

## Constraints

Constraints that hold for every task's GREEN, stated once:

- **Size.** Every file under `tests/` and `src/` stays at or under 350 lines (`make check-structure`); each new test
  module and `assets/toolkit/scripts/provisional.py` (new) targets ≤ 350. `src/slipwai/project/cruise.py` is at 341:
  its change is the `decide` row replaced by one line plus at most nine interpolation lines, never past 350.
  `tests/test_cruise.py` is at 350: **never add to it**. All new text goes in `src/slipwai/project/cruise_provisional.py`.
  A task that would overrun asks the host to name a new module rather than growing one.
- **Repository rules.** No edit under `delivery/` in this checkout, to `VERSION` (stays `1.6.0.dev0`), `catalog.json`,
  `decisions.md`, `spec.md`, `story-split.md`, the register (`slices/README.md`), `project.json`, the root `Makefile`,
  `assets/toolkit/scripts/reversibility.py`, `assets/toolkit/scripts/agents/measures.py`, `src/slipwai/project/seeded.py`,
  nor any record under `specs/` but this slice's folder.
- **Encoding.** Every `open` and `read_text` names `encoding="utf-8"`.
- **Bytecode.** Toolkit scripts under `assets/` run in tests as `python3 -B` subprocesses; tests set
  `sys.dont_write_bytecode = True` before loading any toolkit script by path; no `.pyc` / `__pycache__/` is left under
  `assets/` (`test_assets_bytecode`).
- **Tests.** Fakes live in the test tree; never `unittest.mock` or any mocking framework. Examples enter through the
  verb (`provisional.py status|audit`, `cruise.py --set|mode`), the gate (`check-decisions.py`) as subprocesses
  against a scratch project (`tests/provisional_fixture.py`), or through `slipwai generate`/`replay`/`migrate`.
- **Commits by path.** `git add <new paths>` then `git commit -m … -- <exact paths of the task's manifest>`, never `git add -A`. `make lint typecheck
  check-structure` before each commit, `$?` tested, never chained after a pipe.
- **Test runs.** `make test TESTS="<only the modules the task touches or reads>"`, never the whole suite. Whenever
  `assets/toolkit/` changes, also `make test TESTS="test_toolkit test_utf8_io test_changelog test_assets_bytecode"`
  (the *toolkit module set*).
- **Scratch** only under `/tmp/s27-<task>/` (a 16G tmpfs shared with full gates), literal paths, cleared when done.
- **Fragment.** `changelog.d/provisional-decisions.md` (first line `MINOR`) is created by T002, the first task that
  changes a user-visible file; later tasks do not touch it until T014 completes it.
- **Pin.** T001's modules run green before T002 and again at T015; a refusal or output they assert is changed only in
  the increment that changes it, and only that line.

## Phase 1: Pin (before any change)

- [x] T001 [US8] **Pin — what already holds** (plan *Pin*; D65). Run and report, green and unchanged, before any edit:
  `make test SINCE=adopt-method TESTS="<every test_verify_scoped_* module> test_verify_stamp_scan test_toolkit
  test_utf8_io test_changelog test_assets_bytecode <every test_decisions_*, test_reversibility_* and test_cruise*
  module>"` (take the names from `ls tests/`; drop none silently). Note the line counts of `src/slipwai/project/cruise.py`
  (341), `tests/test_cruise.py` (350), `tests/test_decisions_gate_differential.py` (134) and
  `assets/toolkit/scripts/check-decisions.py`. No file is written, no commit.
  Files: none.

## Phase 2: US8 — the verb, the gate's reading of the new forms, the audit (chain A, sequential)

R1–R8 (less R6's separate task) write `provisional.py`, `check-decisions.py` and the shared fixture, so they run in
order.

- [x] T002 [US8] **R1 — the verb's table** (AC-S27-1, -2, -3, -4, -5, -6; D195, D199, D201; P1).
  `assets/toolkit/scripts/provisional.py` (new): `DECIDE` (the five values in order), `ASKS`, `HELD_FACTS`,
  `ratify_by()`, `status_lines()`, `main()` with `status` (`--decide --ask --when --number [--reversibility]`);
  loads `reversibility.py` beside it by path, bytecode off, only in `main`, for `parse_line`. Exit 2 and one stderr line
  naming the option, stdout empty, on a bad `decide`, `--ask`, `--when` (first ten characters no ISO date), `--number`,
  an unparseable line, or an option missing/repeated. `tests/provisional_fixture.py` (new: scratch project with
  `project.json`, the three scripts copied from `assets/toolkit/scripts/` as they exist, `README.md`,
  `specs/f/decisions.md`; `status(...)`, `audit(...)`, `gate(...)` subprocess helpers; an entry builder with `Status`,
  `Revert`, `Reversibility` and mode lines). Also `changelog.d/provisional-decisions.md`: first line `MINOR`, a stub
  **Catch-up.** paragraph (completed in T014).
  RED→GREEN: e1 guarded fixture, `provisional`, `approval`, `When: 2026-10-07T21:17:49Z`, D12: `Status: provisional ·
  ratify by 2026-10-14`, `Revert: commits carrying Decision: D12` · e2 the same with the `easy` line · e3 `When:
  2026-12-28T00:00Z`: `ratify by 2027-01-04` · e4 the D54 fixture's (`hard`) line: `unavailable: a person's approval`
  · e5 the flag fixture: unavailable, stderr names `flag_default=yes` · e6 each of `recommended-first`,
  `skipper-always`, `provisional-shadow`, `provisional-advisory` with the easy, guarded and hard lines: unavailable (12
  cases; mode lines are T003's, so assert only the `unavailable` and `Status: standing` lines) · e7 no `--reversibility`
  under `provisional`: unavailable, stderr says hard · e8 `easy → guarded → hard`: unavailable (the last step governs)
  · e9 `--ask no` under each of the five values: `Status: standing` only · e10 `--ask fact`, `must`, `release` under
  `provisional` with the easy line: `unavailable: <reason>`, never provisional · e11 `--decide sometimes`, `--ask
  maybe`, `--when yesterday`, `--number 12`, a line naming `rules 9`, `--number` twice: exit 2, stdout empty. Pin:
  T001's modules stay green. Run the toolkit module set.
  Files: `assets/toolkit/scripts/provisional.py`, `tests/provisional_fixture.py`, `tests/test_provisional_status.py`,
  `changelog.d/provisional-decisions.md`.

- [x] T003 [US8] **R2 — the rehearsal lines** (AC-S27-10 verb half; D196, D198; P2). `provisional.py` `status_lines()`
  prints, under `provisional-shadow` and `provisional-advisory` for an `approval` item, `- **Provisional (shadow):**
  <final tier> · <would-have> · Revert: commits carrying Decision: D<n>` (`(advisory)` for advisory), `<would-have>`
  `provisional · ratify by <date>`, `blocks (hard)`, or `blocks (<fact>=yes)`; under advisory, for an item that would
  have been provisional, stderr also prints the park reason `cruise: parked: D<n> needs a person's approval;
  recommended: provisional · ratify by <date> (<tier>) — answer accept through /cruise-tell`. No mode line for `no`,
  `fact`, `must`, `release`, nor under the two off values or `provisional`. RED→GREEN: e1 shadow, guarded fixture:
  `unavailable`, `Status: standing`, the `Provisional (shadow): guarded · provisional · ratify by 2026-10-14 · Revert:
  commits carrying Decision: D12` line · e2 shadow, D54 fixture: `Provisional (shadow): hard · blocks (hard) · Revert:
  …` · e3 shadow, flag fixture: `… guarded · blocks (flag_default=yes) · …` · e4 advisory, guarded fixture: the
  `Provisional (advisory):` line, and stderr carries the park reason naming `accept` · e5 advisory, D54 fixture: the
  line, and no park recommendation · e6 `provisional`, `recommended-first`: no mode line. Run the toolkit module set.
  Files: `assets/toolkit/scripts/provisional.py`, `tests/provisional_fixture.py`, `tests/test_provisional_status.py`.

- [x] T004 [US8] **R3 — the gate holds the new `Status` forms and `Revert:`; with R6 — old logs get the earlier
  answer** (AC-S27-8, AC-S27-7; D197, D198, D65; P4). `provisional.py`: `check_log()` (given the gate's parsed entries)
  for the `Status` forms and the `Revert:` line; `check-decisions.py`: the `STATUS` finding skips a status whose first
  word is `provisional`, `ratified` or `reverted` (left to the module), `provisional_findings(path)` beside
  `reversibility_findings` loading `provisional.py` by `sibling()` with bytecode off **only** for a log whose raw text
  matches `^- \*\*Status:\*\* ?(provisional|ratified|reverted)\b` or `^- \*\*(Revert|Provisional
  \((shadow|advisory)\)):\*\*`, and the module docstring gains the forms. RED→GREEN for R3: e1 D1 `provisional ·
  ratify by 2026-10-14` + `Revert: commits carrying Decision: D1` (with an easy line): exit 0 · e2 `ratified
  2026-10-09`, `reverted 2026-10-09` (with or without `Revert:`): exit 0 · e3 `provisional · ratify by 2026-13-01`,
  `ratified tomorrow`, `provisional`: each refused naming D1 and `Status` · e4 provisional, no `Revert:`: refused
  naming `Revert` · e5 two `Revert:` lines: refused · e6 `Revert:` naming D2 on D1: refused naming D2 · e7 `Revert:`
  on a `standing` entry: refused naming `Revert` · e8 `Revert: the last three commits`: refused. R6 (extend
  `tests/test_decisions_gate_differential.py`): e1 every case of the differential test and this repository's own log,
  through a scratch project holding the three scripts, equal to the released checker at `596740f` and the checker at
  `5f4fc00` (a guard: it passes when written; it freezes the loader's guard) · e2 a `Revert:` on a standing entry:
  passed before, refused now, with a comment stating D65's carve-out (a label only this release defines; P4) · e3
  `provisional.py` deleted from the scratch project and a log with no new form: same answer. Pin: T001 stays green.
  Run the toolkit module set.
  Files: `assets/toolkit/scripts/provisional.py`, `assets/toolkit/scripts/check-decisions.py`,
  `tests/provisional_fixture.py`, `tests/test_provisional_gate.py`, `tests/test_decisions_gate_differential.py`.

- [x] T005 [US8] **R4 — a provisional entry holds FR-033** (AC-S27-9; D195, D200). `provisional.py` `check_log()`
  refuses, one finding naming the entry and the field, a provisional entry with no `Reversibility:` line, whose last
  step is `hard`, or whose facts carry `ci_workflow=yes`, `migrate_file=yes` or `flag_default=yes` (one finding per
  fact); an unparseable line is S26's finding, not repeated; `ratified` and `reverted` entries are not held to it.
  RED→GREEN: e1 provisional, no `Reversibility:`: refused naming `Reversibility` · e2 provisional with `easy →
  guarded → hard`: refused (`hard`) · e3 provisional with the flag fixture's line: refused naming `flag_default` · e4
  with a `ci_workflow=yes` line: refused naming `ci_workflow` · e5 `ratified 2026-10-09` with a `hard` line:
  accepted. Run the toolkit module set.
  Files: `assets/toolkit/scripts/provisional.py`, `tests/test_provisional_gate.py`.

- [x] T006 [US8] **R5 — the gate holds the rehearsal lines** (AC-S27-10 gate half; D196). `check_log()` accepts a
  `- **Provisional (shadow):**` / `(advisory):` line exactly as `<tier> · <would-have> · Revert: commits carrying
  Decision: D<own>`, `<would-have>` `provisional · ratify by <date>`, `blocks (hard)` or `blocks (<fact>=yes)` for one
  of the three facts, `blocks (hard)` exactly when the tier is `hard`; a second such line (either label) is refused;
  an entry without one is never refused. RED→GREEN: e1 the T003 e1 line on a `standing` entry: exit 0 · e2 `hard ·
  blocks (hard) · …` accepted; `guarded · blocks (hard) · …` refused · e3 `medium · …`, `guarded · provisional · ratify
  by 2026-02-30 · …`, `Revert` naming another entry: each refused naming `Provisional (shadow)` · e4 a shadow line and
  an advisory line on one entry: refused · e5 a log whose entries have none: nothing new. Run the toolkit module set.
  Files: `assets/toolkit/scripts/provisional.py`, `tests/test_provisional_gate.py`.

- [x] T007 [US8] **R7 — `--scope` reads the new statuses** (AC-S27-15 second half; D197 rule 3).
  `check-decisions.py` `scope_verb`: a `provisional …` or `ratified …` entry in scope is printed as binding,
  verbatim; the summary gains `; provisional and binding: D<n>, …` only where one is printed; a `reverted …` entry is
  left out and listed with the overridden ones as `D<n> (reverted <date>)`. RED→GREEN: e1 D1 provisional, D2
  ratified, D3 reverted, all `Scope: S1`: D1 and D2 printed, the summary names D1 provisional and `D3 (reverted
  2026-10-09)` left out · e2 a log of standing entries: output byte-equal to before (a guard over the unchanged path;
  it passes when written, say so). Pin: `test_decisions_scope_gate`, `test_decisions_scope` stay green. Run the toolkit
  module set.
  Files: `assets/toolkit/scripts/check-decisions.py`, `tests/test_provisional_scope_audit.py`.

- [x] T008 [US8] **R8 — the completion audit's refusal** (AC-S27-14; D197; P6). `provisional.py` gains `unratified()`
  and `audit [--feature <name>]`: where any entry's first `Status` starts with `provisional`, print `cruise: parked:
  ratify D<n>` naming the lowest-numbered one, exit 3; otherwise `provisional: no unratified provisional decision in
  specs/<f>/decisions.md` (or `no decisions.md`), exit 0; `--feature` required only where `specs/` holds several
  logs (exit 2, one line naming them). RED→GREEN: e1 D4 and D2 provisional: `cruise: parked: ratify D2`, exit 3 · e2
  D2 `ratified 2026-10-09`, D4 `reverted 2026-10-09`, D5 `overridden by human 2026-10-09`: exit 0 · e3 no log: exit
  0, says none · e4 two features and no `--feature`: exit 2 naming both. Run the toolkit module set.
  Files: `assets/toolkit/scripts/provisional.py`, `tests/test_provisional_scope_audit.py`.

## Phase 3: US8 — the runner (chain B, sequential; **[P]** against Phase 2)

Chain B writes only `assets/toolkit/scripts/agents/cruise.py`, `tests/test_cruise_decide_ladder.py` and the two
refusal-text lines of `tests/test_cruise_runner.py` / `tests/test_cruise_sweep.py`; Phase 2 writes
neither, so the two chains are disjoint (Phase 5).

- [x] T009 [US8] [P] **R9 — the ladder and the iteration guard in `--set`** (AC-S27-11, -13; D196 part 3, D201).
  `agents/cruise.py`: `CHOICES["decide"]` and `DEFAULTS` hold the five values in order, `RUNGS` (`recommended-first`,
  `skipper-always` 0; `provisional-shadow` 1; `provisional-advisory` 2; `provisional` 3), the refusal in `--set`
  before the file is written (a step up of more than one rung: `` `decide` moves one mode at a time: set `<next>`
  first ``, exit 1, file unchanged; steps down, one-rung steps and the move between the two rung-0 values written),
  and with `CRUISE_ITERATION` in the environment any `--set decide=…` refused in one line naming `/cruise-settings` as a
  person's command (other keys untouched); `check()` accepts every one of the five values; the docstring's usage line.
  The tests scratch a project holding `scripts/agents/` copied from the toolkit. RED→GREEN: e1 `recommended-first` →
  `provisional`: refused naming `provisional-shadow`, file bytes equal · e2 `recommended-first` →
  `provisional-advisory`: refused naming `provisional-shadow` · e3 `provisional-shadow` → `provisional`: refused naming
  `provisional-advisory` · e4 `recommended-first` → `provisional-shadow` → `provisional-advisory` → `provisional`,
  each written · e5 `provisional` → `recommended-first`: written; `provisional` → `provisional-shadow`: written · e6
  `skipper-always` → `provisional-shadow`: written · e7 `CRUISE_ITERATION=4`, `--set decide=recommended-first`:
  refused naming `/cruise-settings`, file bytes equal; `--set max_hours=2` still written · e8 a hand-edited file holding
  `provisional`: `--check` passes. The two assertions of the old value list in `tests/test_cruise_runner.py:116` and
  `tests/test_cruise_sweep.py:55` change here, in the increment that changes the list (only those lines; line counts
  unchanged), so the suite stays green at this commit. Run the toolkit module set and
  `test_cruise_decide_ladder`.
  Files: `assets/toolkit/scripts/agents/cruise.py`, `tests/test_cruise_decide_ladder.py`, `tests/test_cruise_runner.py`,
  `tests/test_cruise_sweep.py`.

- [x] T010 [US8] [P] **R10 — the mode entry and the skipping hand edit** (AC-S27-12; D196 part 4; P3).
  `agents/cruise.py` gains the verb `mode [--feature <name>]` (writes nothing): compares `decide` with the last
  `## D<n> — decide moved from <a> to <b>` heading of the feature's log; equal: `cruise: decide is <v>, as D<n>
  recorded`, exit 0; no mode entry: the entry to append with `<a>` `unrecorded`; a step R9 would write: the entry
  (heading with the next number, `Decided by: human`, `Scope: global`, `Written to: .specify/cruise.json`, its
  **Decision** citing `git log -1 --format=%h -- .specify/cruise.json`, or `uncommitted at <instant>` where `git
  status --porcelain` shows it changed), exit 0; a forward skip of more than one rung: `cruise: parked: decide=<v>
  skips <next>; set it through /cruise-settings`, exit 3, nothing to append. The tests use a scratch project holding
  `scripts/agents/` and a scratch git repository. RED→GREEN: e1 last mode entry `provisional-shadow`, the file
  `provisional-shadow`: `decide is …`, exit 0 · e2 the file committed at `provisional-advisory`: an entry `decide moved
  from provisional-shadow to provisional-advisory`, number = last + 1, citing that commit's hash, that passes
  `check-decisions` once appended (scored with `reversibility.py` as every entry is) · e3 uncommitted change:
  `uncommitted at <instant>` · e4 no mode entry, file `recommended-first`: `decide moved from unrecorded to
  recommended-first` · e5 last mode `recommended-first`, file hand-edited to `provisional`: the park line naming
  `provisional-shadow`, exit 3 · e6 last mode `provisional`, file `recommended-first`: an entry (a step back). Run
  the toolkit module set and `test_cruise_decide_ladder`.
  Files: `assets/toolkit/scripts/agents/cruise.py`, `tests/test_cruise_decide_ladder.py`.

## Phase 4: US8 — the scoped-gate record, the writers, and a project made before (sequential, after Phases 2 and 3)

- [x] T011 [US8] **The scoped-gate record** (plan *Structure Decision*; S26's `6cfe48b`). Run `make test
  TESTS="test_verify_scoped_table_held test_verify_scoped_record <every other test_verify_scoped_* module>
  test_verify_stamp_scan"` on the tree T002–T010 left. If the table scan flags a literal in `provisional.py` or in the
  new `cruise.py mode` verb (including the new `check-decisions.py` load of `provisional.py` by path, which the scan's
  import-following cannot see), widen the row in `assets/toolkit/scripts/verify_scoped/table.py` (the
  `check-decisions` row must name whatever `provisional.py` and the gate's new load read) or add the exemption in
  `tests/test_verify_scoped_table_held.py` with a written reason; change the smallest thing that makes the scan
  honest. RED: the scan fails on the new literal (if it does not fail, write nothing, say so, and make no commit —
  this task then has an empty GREEN and is dropped). Files edited only when the scan says so.
  Files: `assets/toolkit/scripts/verify_scoped/table.py`, `tests/test_verify_scoped_table_held.py`,
  `tests/test_verify_scoped_record.py`.

- [x] T012 [US8] **R11 — five values, one default, one sentence, everywhere** (AC-S27-16; D196 part 1).
  `src/slipwai/project/cruise_provisional.py` (new): `DECIDE_VALUES`, `DECIDE_CONTROLS` (with the sentence *Change it
  to `provisional-shadow` when always-ask questions are stalling slices and you want to see which ones would have
  been taken provisionally before letting any be; move on to `provisional-advisory`, then `provisional`, once the
  shadow lines read right.*); `src/slipwai/project/cruise.py`: the `decide` row from the new module (net change keeps
  the file ≤ 350); `agents/cruise.py` `CONTROLS["decide"]` carries the sentence; the generated
  `commands/cruise-settings.md` table and `docs/cruise.md`'s table list the same five values in the same order and the
  sentence; `provisional.py`'s accepted values equal them (T009 already moved the two refusal-text assertions). RED→GREEN: e1 the four
  sources (server-side `SETTINGS`, toolkit `CHOICES`, the settings command, `docs/cruise.md`) compared, values and
  order, and equal to `provisional.DECIDE` · e2 a generated project's `.specify/cruise.json` still says
  `recommended-first` · e3 the sentence in `CONTROLS`, the settings command and `docs/cruise.md` · e4 `cruise.py --set
  decide=nope` names the five. Pin: `test_cruise_scope_writers`, `test_cruise_record`, `test_cruise`,
  `test_reversibility_writers` stay green. Run the toolkit module set.
  Files: `src/slipwai/project/cruise_provisional.py`, `src/slipwai/project/cruise.py`,
  `assets/toolkit/scripts/agents/cruise.py`, `docs/cruise.md`, `tests/test_cruise_provisional_writers.py`.

- [x] T013 [US8] **R12 — the command and the briefs say it** (AC-S27-5 last clause, -6, -10 advisory park, -15 first
  half; D198, D200, D201; P5). New constants in `cruise_provisional.py` (`PROVISIONAL_VERB`, `AUDIT_VERB`, `MODE_VERB`,
  the command's provisional paragraph, the audit sentence, the mode-check sentence, the skipper's paragraph, the
  stop-row exception, the settings-words sentence), interpolated, never inlined in the capped files:
  `cruise.py` (the command: *Before anything* runs `cruise.py mode`, appends the printed entry scored with
  `reversibility.py` and ends on the park line where printed; the skipper protocol's provisional paragraph; the
  completion audit runs `provisional.py audit` before `cruise: done` and ends on its line; *What holds throughout* says
  the run never sets `decide`; every implement brief carries the trailer `Decision: D<n>`; `told: accept` is written as
  a `Decided by: human` entry taking the recommendation, the `unavailable` entry becoming `overridden by D<m>`) — in
  place, net ≤ +9 lines; `cruise_record.py` `DECISION_ENTRY` shows the three `Status` forms, `Revert:` and the mode
  line; `cruise_agents.py` the skipper's paragraph; `cruise_stops.py` the approval row's exception naming `decide:
  provisional`; `decisions.py` one sentence under *Always ask a person* and one under *What the record looks like*;
  `docs/cruise.md` row 12's exception and a short *Provisional decisions* section; the settings command's words map
  "take easy decisions provisionally" to `decide=provisional-shadow` first. Assertions on `DECISION_ENTRY` or the
  skipper's brief in `tests/test_cruise_record.py` and `tests/test_reversibility_writers.py` are updated, only those
  lines (never `tests/test_cruise.py`). RED→GREEN: e1 a generated project: `commands/cruise.md` names `scripts/
  provisional.py status`, `provisional.py audit`, `cruise.py mode`, `Decision: D<n>`, `accept`, "no bosun", "only the
  skipper" · e2 `agents/drive-skipper.md` names the verb, the quoted owner-brief line, "a gate, a check or CI",
  `decided` · e3 `.specify/product-owner.md` holds `DECISION_ENTRY` with `provisional · ratify by`, `Revert:` and
  `Provisional (shadow`, and the always-ask sentence · e4 the stop table's approval row names `decide: provisional` ·
  e5 an adopted repository: the same text with `delivery/scripts/provisional.py` · e6 `wc -l
  src/slipwai/project/cruise.py` ≤ 350. Pin: `test_cruise_scope_writers`, `test_cruise_record`, `test_cruise`,
  `test_hand_backs_coverage`, `test_reversibility_writers` stay green.
  Files: `src/slipwai/project/cruise_provisional.py`, `src/slipwai/project/cruise.py`,
  `src/slipwai/project/cruise_record.py`, `src/slipwai/project/cruise_agents.py`,
  `src/slipwai/project/cruise_stops.py`, `src/slipwai/project/decisions.py`, `docs/cruise.md`,
  `tests/test_cruise_provisional_writers.py`, `tests/test_cruise_record.py`, `tests/test_reversibility_writers.py`.

- [x] T014 [US8] **R13 — a project made before** (AC-S27-17; D196). `tests/test_provisional_migrate.py` takes the
  factory at `5f4fc00` with `git archive` (as `test_reversibility_migrate` does) into a scratch dir, generates a
  project there, runs this checkout's `slipwai migrate`; and completes `changelog.d/provisional-decisions.md`: first
  line `MINOR`, one standalone **Catch-up.** paragraph naming the three new values, that they are off by default and
  `.specify/cruise.json` is untouched, the one-rung-at-a-time rule, and that a provisional entry is ratified by hand
  (`Status: ratified <date>`, or reverted and `reverted <date>`) until `S28` ships, since the run will not say `done`
  while one is unratified. RED→GREEN: e2 the fragment's words (a test reads the first line and the one paragraph; this
  is the RED) · e1 the migration: `scripts/provisional.py` arrives, `.specify/cruise.json` is byte-unchanged, `make
  check-agents`, `make check-decisions` and `make verify` pass in the migrated project (e1 passes once T002–T013 stand:
  keep it as the guard, say so). Run `make test TESTS="test_provisional_migrate test_changelog"`.
  Files: `tests/test_provisional_migrate.py`, `changelog.d/provisional-decisions.md`.

## Phase 5: Parallel opportunities

The default is the order above, one delegate at a time. Disjoint manifests allow exactly one concurrent split:

- **T009 → T010 (chain B, the runner) may run alongside T002 → T008 (chain A, the verb and the gate).** Chain A owns
  `assets/toolkit/scripts/provisional.py`, `check-decisions.py`, `tests/provisional_fixture.py`,
  `tests/test_provisional_status.py`, `test_provisional_gate.py`, `test_provisional_scope_audit.py`,
  `test_decisions_gate_differential.py` and `changelog.d/provisional-decisions.md`; chain B owns
  `assets/toolkit/scripts/agents/cruise.py` and `tests/test_cruise_decide_ladder.py`. Neither names a file the other
  writes. T010's e2 only reads `check-decisions.py` and `reversibility.py` as shipped, so it passes against whatever
  chain A has committed; a delegate for chain B runs only its own manifest's tests. Mark: **[P]** across the two chains
  only, never inside one.
- **Not parallel**: T002 → T003 → T004 → T005 → T006 → T007 → T008 (one script, one gate, one fixture; T007 and T008
  write `check-decisions.py` / `provisional.py` which T004–T006 own); T009 → T010 (one script, one test module);
  T011 after both chains (it reads every new literal); T012 → T013 (both write `cruise_provisional.py`, `cruise.py`,
  `docs/cruise.md` and `tests/test_cruise_provisional_writers.py`; T012 also needs T009's `CHOICES`); T014 after
  everything and completes the fragment T002 created. T001 first.
- The host runs the toolkit module set after the chains rejoin.

## Phase 6: Gate before converge

- [x] T015 [US8] **The slice's gates, on the final tip.** Run `make lint typecheck check-structure` (each `$?` tested),
  then `make test SINCE=adopt-method TESTS="<every test_verify_scoped_* module> test_verify_stamp_scan test_toolkit
  test_utf8_io test_changelog test_assets_bytecode <every test_decisions_*, test_reversibility_*, test_cruise* and
  test_provisional_* module>"` (names from `ls tests/`, none dropped silently; T001's modules run once more inside it),
  and report the line counts of `src/slipwai/project/cruise.py`, `tests/test_cruise.py`, `provisional.py` and every new
  module (each ≤ 350 except as noted at T001). Confirm `git diff --stat adopt-method -- VERSION delivery` is empty and no
  `__pycache__/` or `.pyc` lies under `assets/`. No file is written, no commit.
  Files: none.

## Phase 7: Converge pass 1 — what the slice still owes (appended by `drive-converge`, at `76927e4`)

Graded. Only `CRITICAL` and `HIGH` re-open the loop. Every task keeps the *Constraints* above. `src/slipwai/project/cruise.py`
is at 343 lines and `assets/toolkit/scripts/provisional.py` at 339: new text goes in `cruise_provisional.py`, and new
code that would take `provisional.py` past 350 goes in a module the host names. Each task's evidence is what this pass
observed on a project generated by this checkout's `./slipwai` (`/tmp/s27-converge1/`, since removed).

- [x] T016 [US8] **HIGH — the generated text says shadow and advisory take an always-ask item provisionally; they take
  nothing** (AC-S27-3, AC-S27-10; D196 part 2). *Evidence:* `cruise_provisional.py:35-36` (the command) says "Under
  `decide: provisional-shadow`, `provisional-advisory` or `provisional`, only the skipper takes an always-ask item
  provisionally". `cruise_provisional.py:67-70` (the skipper's brief) says that under those three "a person's approval
  … is yours alone to take provisionally", and ends "An enforced provisional decision is not a block: your `status` is
  `decided`". Under `provisional-shadow` the verb prints `unavailable: a person's approval`, the rehearsal line, and
  `- **Status:** standing` (observed). A skipper following its brief writes "the lines it prints" and so produces
  `Status: standing` with `status: decided`, and the host then goes ahead on a person's approval in a mode that was
  meant to change nothing. Separately, `src/slipwai/project/cruise.py:191` (generated `commands/cruise.md`:160) still
  says an approval "is never decided, whatever `decide` says", which `decide: provisional` now contradicts.
  *GREEN:* the generated command and the skipper's brief state each mode separately. Under `provisional-shadow` and
  `provisional-advisory` the item stays `unavailable` and the skipper's `status` is `unavailable`; the entry gains only
  the rehearsal line. Only `provisional` takes an item. The sentence at `cruise.py:191` names the exception.
  RED→GREEN in `tests/test_cruise_provisional_writers.py`: for each of the three values, assert the generated
  command's and the skipper brief's sentence for that value, and assert that no sentence grants taking under the
  shadow or advisory value.
  *Class sweep:* every surface that names the three values together or describes an approval as never decided:
  `COMMAND_PARAGRAPH`, `SKIPPER_PARAGRAPH`, `cruise.py:191`, `docs/cruise.md` *Provisional decisions* (its first
  sentence has the same "under the last three" shape), `OWNER_ALWAYS`, `STOP_EXCEPTION`, and the fragment's first
  paragraph.
  Files: `src/slipwai/project/cruise_provisional.py`, `src/slipwai/project/cruise.py`, `docs/cruise.md`,
  `tests/test_cruise_provisional_writers.py`.

- [x] T017 [US8] **HIGH — the skipper hand-off is not wired: the host is never told to name `decide` in the brief,
  nothing maps the verb's `unavailable:` line to a status, and advisory's park line goes nowhere** (AC-S27-5, -6, -10;
  D196 part 2 advisory, D201). *Evidence:*
  - The skipper's brief (`cruise_provisional.py:67`) says "The brief names the `decide` value". The command's dispatch
    sentence (`cruise.py:169`: "the question, the stage, the options and the recommendation in its brief … and the
    number") never tells the host to put it there.
  - Nothing tells the host to send an always-ask item to the skipper when the stage recommends an answer, so under
    `recommended-first` rules the host may decide it itself. Then no verb runs, and no rehearsal line or provisional
    status is written.
  - The verb's first stdout line, `unavailable: a person's approval`, has no place in the entry shape, and no text says
    it means `status: unavailable`.
  - Under advisory, the recommendation (`cruise: parked: D<n> needs a person's approval; recommended: … — answer accept
    through /cruise-tell`) goes to the verb's **stderr**, in the skipper's shell. The command says "the park line is the
    one the verb prints", but no text carries that line from the skipper to the host.

  AC-S27-10's "the park question names it as the recommendation a person can accept in one word" therefore holds only
  for the verb (`test_provisional_status` R2 e4), not for the run.
  *GREEN:*
  - The command's dispatch sentence: under the three provisional values, every always-ask item goes to the skipper,
    even where the stage recommends an answer, and the brief names `decide`.
  - The skipper's brief: the verb's `unavailable: …` line is `status: unavailable`, with the **Decision:** saying what
    a person must provide. The rehearsal line goes into the entry. Under advisory, the stderr `cruise: parked: …` line
    is returned verbatim in `unresolved`.
  - The command: a park on that item ends on that line.

  RED→GREEN in `tests/test_cruise_provisional_writers.py`, one assertion per sentence.
  *Class sweep:* every line the verb can print (the `unavailable:` line, `Status`, `Revert`, the rehearsal line, the
  stderr park line), under each of the three values, has one sentence saying where it goes. Check the table, not one
  mode.
  Files: `src/slipwai/project/cruise_provisional.py`, `src/slipwai/project/cruise.py`,
  `tests/test_cruise_provisional_writers.py`.

- [x] T018 [US8] **MEDIUM — one `--set` with several `decide=` assignments climbs three rungs** (AC-S27-11; D196
  part 3: "refuses any forward step of more than one rung from the file's current value"). *Evidence:* from
  `recommended-first`, `cruise.py --set decide=provisional-shadow decide=provisional-advisory decide=provisional`
  printed three `decide = …` lines and wrote `provisional` (observed, exit 0). `climb()`
  (`assets/toolkit/scripts/agents/cruise.py:279`) judges each assignment against the table `assign()` has already
  changed. The next iteration's `mode` catches it only where the log already holds a mode entry.
  *GREEN:* the refusal judges against the value the file held when the call started: refused naming
  `provisional-shadow`, file bytes unchanged. Alternatively, a second `decide=` in one call is refused, `key given
  twice`.
  RED→GREEN in `tests/test_cruise_decide_ladder.py`.
  *Class sweep:* every check `climb` makes (the rung, the iteration guard) is judged against the file's value at load,
  never the value mid-call.
  Files: `assets/toolkit/scripts/agents/cruise.py`, `tests/test_cruise_decide_ladder.py`.

- [x] T019 [US8] **MEDIUM — the first mode entry says a person changed a setting nobody touched** (AC-S27-12;
  constitution VII, the actor of a recorded fact). *Evidence:* in a freshly generated project, `cruise.py mode` printed
  `decide moved from unrecorded to recommended-first` with **Decision:** "as a person set it … (commit ec40855)", the
  generator's initial commit, and **Why:** "a person changed the setting through /cruise-settings"
  (`agents/cruise.py:300-301`). Neither is true of a default. Every feature log of every migrated project gets this
  entry at its first iteration, and the fragment's **Catch-up.** never says so.
  *GREEN:* where `<a>` is `unrecorded`, the Decision and Why say the mode is recorded as found and that the earlier
  mode is unknown (D196 part 4), still citing the commit. The step-up and step-back wording stays. The **Catch-up.**
  says that the first iteration after upgrading appends this entry to the feature's log.
  RED→GREEN in `tests/test_cruise_decide_ladder.py` (`test_the_first_entry_moves_from_unrecorded`) and
  `tests/test_provisional_migrate.py`.
  *Class sweep:* the three cases `mode` prints (unrecorded, a step up, a step back) each get a Why that is true of that
  case.
  Files: `assets/toolkit/scripts/agents/cruise.py`, `changelog.d/provisional-decisions.md`,
  `tests/test_cruise_decide_ladder.py`, `tests/test_provisional_migrate.py`.

- [x] T020 [US8] **MEDIUM — the completion audit passes a `--feature` that names no feature** (AC-S27-14). *Evidence:*
  `provisional.py audit --feature nope` printed `provisional: no decisions.md, so no unratified provisional decision`
  and exited 0 (observed), so `done` is not held. Its sibling `check-decisions.py --scope … --feature nope` refuses with
  exit 1 (`check-decisions.py:466-469`). `cruise.py mode --feature nope` prints an entry to append to a log that does
  not exist. The command's `AUDIT_SENTENCE` and `MODE_SENTENCE` say nothing of an exit of 2 (several features, none
  named), so a host may read it as "no park".
  *GREEN:* `--feature` naming no `specs/<name>/` directory is exit 2 naming it, in both verbs. A named feature with no
  log yet stays exit 0. The two sentences say that an exit other than 0 or 3 is a park, never `done`.
  RED→GREEN in `tests/test_provisional_scope_audit.py` and `tests/test_cruise_decide_ladder.py`.
  *Class sweep:* every verb this slice gave a `--feature` (`audit`, `mode`), set against `--scope`'s refusal.
  Files: `assets/toolkit/scripts/provisional.py`, `assets/toolkit/scripts/agents/cruise.py`,
  `src/slipwai/project/cruise_provisional.py`, `tests/test_provisional_scope_audit.py`,
  `tests/test_cruise_decide_ladder.py`, `tests/test_cruise_provisional_writers.py`.

- [x] T021 [US8] **LOW — the ratify-by date is not the UTC date when `When` carries an offset** (AC-S27-1 "+ 7 days,
  UTC"; D199). *Evidence:* `--when 2026-10-07T23:30:00-05:00` gave `ratify by 2026-10-14`; the UTC date is
  2026-10-08, so the answer is 2026-10-15 (`ratify_by`, `provisional.py:69-74`, reads the first ten characters).
  *GREEN:* an instant with an offset is converted to UTC before the seven days are added. An instant with no time
  keeps today's reading.
  RED→GREEN in `tests/test_provisional_status.py`.
  *Class sweep:* the verb's two date outputs (Status and the rehearsal line) share `ratify_by`. The gate does not
  re-derive either from `When`, and AC-S27-8 does not ask it to, so nothing changes there.
  Files: `assets/toolkit/scripts/provisional.py`, `tests/test_provisional_status.py`.

- [x] T022 [US8] **LOW — summaries of what `provisional` takes are wider than the verb, and three Catch-up sentences
  are not quite true.** *Evidence:*
  - `COMMAND_PARAGRAPH` lists the verb's options without `--reversibility`. The verb with no `--reversibility` reads
    the item as hard, so it fails safe.
  - `STOP_EXCEPTION`, `docs/cruise.md` row 12 and the fragment's first paragraph say "easy or guarded to reverse" and
    omit the three facts FR-033 holds back (`flag_default`, `ci_workflow`, `migrate_file`) and the gate/CI exclusion.
  - The **Catch-up.** says "it can only happen under `provisional`". An entry written under `provisional` still holds
    the run after a person steps back to shadow.
  - The **Catch-up.** names the files `migrate` brings without `agents/drive-skipper.md` and
    `commands/cruise-settings.md`, which it also regenerates. It also says `/cruise-settings` "refuses a larger step",
    which T018 makes true.

  *GREEN:* each sentence matches the verb, and the writers and migrate tests assert the new words.
  *Class sweep:* every one-sentence summary of what `provisional` takes: stop row, docs row 12, the page's section,
  `OWNER_ALWAYS`, the fragment's two paragraphs.
  Files: `src/slipwai/project/cruise_provisional.py`, `docs/cruise.md`, `changelog.d/provisional-decisions.md`,
  `tests/test_cruise_provisional_writers.py`, `tests/test_provisional_migrate.py`.

## Design review

No screen in this slice.

## Convergence

### Pass 1 — `drive-converge`, at `76927e4` — **not converged**

Two HIGH tasks (T016, T017) re-open the loop. The rules' domain is sound: the verb's table, the gate and the ladder
did what the criteria say on every case run. The failure is in what the generated text tells a run to do with those
outputs under shadow and advisory.

**Levels.**
- **Domain** (`provisional.py`, `check-decisions.py`, `agents/cruise.py`). Checked:
  - `status` was run under all five values on the guarded fixture: provisional only under `provisional`, rehearsal
    lines only under shadow and advisory, and the advisory park on stderr.
  - The gate was run on a provisional entry, then on the appended mode entry: exit 0, and `--scope` printed
    `provisional and binding: D1`.
  - `audit` exited 3 with `cruise: parked: ratify D1`.
  - The ladder refused `recommended-first → provisional` naming shadow, and refused inside an iteration (`CRUISE_ITERATION`).
  - `mode` parked on a skipping hand edit (exit 3).

  Not proven: T018 (a multi-assignment climb), T021 (a non-UTC `When`).
- **Use case** (a skipper following generated `commands/cruise.md` and `agents/drive-skipper.md`). Under
  `provisional` the steps lead to the right entry. Under shadow and advisory the text grants taking the item (T016),
  and the hand-off of `decide`, the `unavailable` line and the advisory park line is unwired (T017).
- **Delivery adapter** (the CLIs). Usage is exit 2 on stderr with stdout empty (R1 e11). The audit is exit 3/0; `mode`
  is exit 3/0, with the entry on stdout. `--set` refuses in one line, exit 1. Not proven: `--feature` naming nothing
  (T020).
- **Published contract** (`DECISION_ENTRY`, which the gate holds). The three `Status` forms, `Revert:` and the mode
  line are shown and held (`test_provisional_gate` R3–R5). On the fragment's **Catch-up.**, each sentence was followed:
  `cruise.json` is byte-unchanged and `make verify` passes after `migrate` (`test_provisional_migrate` e1, run green
  here). Three sentences are imprecise (T022, T019).
- **D65.** A log with none of the new forms gets the released checker's findings and exit code
  (`test_decisions_gate_differential` R6 e1–e3, run green). The one moved answer, a `Revert:` on a standing entry, is
  the stated carve-out (P4).

**Constitution.**
- **I** (a project owns its files and passes its gate).
  - `cruise.json` gains no key: `tests/test_provisional_migrate.py:54`. `make verify` passes after `migrate`:
    `tests/test_provisional_migrate.py:64-68`.
  - The gate only adds a check: `assets/toolkit/scripts/check-decisions.py:645`.
  - `VERSION` stays `1.6.0.dev0`, and the fragment is `MINOR`: `changelog.d/provisional-decisions.md:1`.
- **III** (simplicity). No new key: the five values are one enum, `assets/toolkit/scripts/agents/cruise.py:160`. One
  script serves the verb, the audit and the gate.
- **V** (acceptance-driven). Every rule R1–R13 has its test (below).
- **VII** (auditability, actor of a recorded fact).
  - Each refusal is one line naming the entry and the field: `provisional.py:227-232`.
  - The mode entry is `Decided by: human` citing the commit: `agents/cruise.py:295-306`.
  - **Unmet** for the unrecorded case: the Why attributes a default to a person (T019).
- **VIII** (versioning, published contract). The decision-entry grammar grows additively. An old log is read as
  before: `check-decisions.py:264-268` and `296`. MINOR.
- **XIV** (an agent never widens its own authority, and stops at a published contract or persisted field).
  - `contract`, `schema`, `auth`, `customer_visible` and `export` set to `yes` each score `hard` (observed), so they
    are never provisional: `provisional.py:124`, and the gate at `provisional.py:184-187`.
  - The iteration guard is at `agents/cruise.py:284`.
  - **Partly unmet:** the text grants shadow and advisory authority they do not have (T016, T017), and one `--set`
    climbs past a rung (T018).

**Criteria.** The 127 tests of the slice's named modules were run green at `76927e4`.
- AC-S27-1 — `test_provisional_status` R1 e1–e3, and observed.
- AC-S27-2 — R1 e4.
- AC-S27-3 — R1 e6. Verb only; the text contradicts it for shadow and advisory (T016).
- AC-S27-4 — R1 e5.
- AC-S27-5 — R1, and writers e1/e2 name the verb. The command omits `--reversibility` (T022).
- AC-S27-6 — R1 e9–e10. "Decided exactly as under `recommended-first`" is text only, and the routing of an always-ask
  item to the skipper is unstated (T017).
- AC-S27-7 — differential R6 e1–e3.
- AC-S27-8 — `test_provisional_gate` R3 e1–e8.
- AC-S27-9 — R4 e1–e6.
- AC-S27-10 — the verb in R2 e1–e6 and the gate in R5 e1–e5. The advisory park question is **not met in the run**
  (T017).
- AC-S27-11 — `test_cruise_decide_ladder` (jump, step down, rung-0 tests), and observed. A multi-assignment bypass
  remains (T018).
- AC-S27-12 — ladder `mode` tests, and observed (skip park exit 3; entry cites the commit and passes the gate). The
  unrecorded wording is false (T019).
- AC-S27-13 — `test_an_iteration_never_sets_decide_but_other_keys_still_write`, and observed.
- AC-S27-14 — `test_provisional_scope_audit` R8 e1–e4, and observed. A `--feature` naming nothing fails open (T020).
- AC-S27-15 — R7 e1–e2 and writers e1 ("no bosun"), and observed `--scope`.
- AC-S27-16 — writers e1–e4 (`test_the_four_sources_list_the_same_five_values_in_order_and_provisional_accepts_them`).
- AC-S27-17 — `test_provisional_migrate` e1–e2 (run green, `make verify` inside).

**Returned to the host, not decided (product question).** Mode entries are per feature log, and D196 part 4 records
a log with no mode entry "with no order check". So every new feature, and every project before its first iteration,
accepts a hand edit straight to `provisional` without parking. Observed: a second feature's `mode` printed `decide
moved from unrecorded to provisional`, exit 0. The options:
- (a) Keep D196 as written.
- (b) Read `unrecorded` as rung 0. Before this release only rung-0 values existed, so the earlier mode is known.
- (c) Take the last mode entry across every feature's log, falling back to (b).

Recommendation: (c). It closes the hole without making a project that already reached `provisional` in one feature
re-climb in the next. It needs a person's override of D196 part 4.

### After pass 1 — host, at `510e022`

T016–T022 implemented by three concurrent `drive-implement` delegates (sonnet, disjoint manifests: the text,
the runner, the verb) in `7115a22..510e022`; lint, typecheck and structure green at the tip; no `.pyc` under `assets/`.
T013 (pass 0) wrote its text before its tests and showed their teeth by mutation afterwards, restored by hand: a
recorded departure from RED-first, not repeated in T016–T022. Pass 2 waits on plan.md's open question Q1 (the mode
baseline of a log with no mode entry, D196 part 4), returned to the host; the slice is blocked on it.
