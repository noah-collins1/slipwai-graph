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

- [ ] T015 [US8] **The slice's gates, on the final tip.** Run `make lint typecheck check-structure` (each `$?` tested),
  then `make test SINCE=adopt-method TESTS="<every test_verify_scoped_* module> test_verify_stamp_scan test_toolkit
  test_utf8_io test_changelog test_assets_bytecode <every test_decisions_*, test_reversibility_*, test_cruise* and
  test_provisional_* module>"` (names from `ls tests/`, none dropped silently; T001's modules run once more inside it),
  and report the line counts of `src/slipwai/project/cruise.py`, `tests/test_cruise.py`, `provisional.py` and every new
  module (each ≤ 350 except as noted at T001). Confirm `git diff --stat adopt-method -- VERSION delivery` is empty and no
  `__pycache__/` or `.pyc` lies under `assets/`. No file is written, no commit.
  Files: none.

## Design review

No screen in this slice.

## Convergence
