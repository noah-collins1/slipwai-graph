# Tasks: S21-refresh-keeps-owned-files — a refresh leaves the project's own settings and the owner brief alone

**Input**: [plan.md](plan.md) (*The example map* R1–R6 is what the tasks cut on; *Design*; *Pin*),
[research.md](research.md), [data-model.md](data-model.md), [quickstart.md](quickstart.md); acceptance criteria
AC-S21-1 … AC-S21-11 in `specs/001-faster-slipwai/spec.md` under `### S21-refresh-keeps-owned-files`; decisions D9,
D12, D15, D16, D24, D25 in `specs/001-faster-slipwai/decisions.md`. No `examples.md`: a method slice with no screen
and no event model.

**Branch**: `adopt-method` (D12). No `slice/` branch, no push, no claim. One commit per task.

**Delegation** (`.specify/drive.json`: `delegate: story`, `cycle: rule`): these tasks carry no user-story tag, so
they are delegated **per rule**, one delegate per implementation task, each its own RED-GREEN-REFACTOR increment and
its own commit.

**Constraints that hold for every task** (plan.md *Constraints*): standard library only, no mocking framework (tests
drive `slipwai adopt`, `adopt --refresh` and `adopt --confirm` against a temporary git repository, using
`tests/test_adopt.py`'s `repository()` and `slipwai(...)` as `tests/test_adopt_facts.py` and
`tests/test_uncommitted.py` do); `PATCH` — no setting, flag or file added to a generated project; nothing under
`delivery/scripts/`, `tools/`, the `Makefile`, CI or hook settings changes; `VERSION` stays `1.5.2.dev0`;
`src/slipwai/resurvey.py` is at the 350-line budget `make check-structure` holds, so every edit to it is net zero or
negative and what is added lands in a small new module or in `strategy.py`; every file under `tests/` stays under 350
lines (`tests/test_line_widths.py`). Before each commit run `make lint typecheck check-structure` as well as the quick
test. Each RED is observed failing for its stated reason before the production edit; a hold is observed passing
before the change and again after.

**How the example map was cut.** R2 (a missing seeded file is written) and R4 (the pages that follow the record, the
`.written` listing, no `owned:` line) are today's behaviour in every example, so their GREEN would be empty: tests for
them pass the moment they are written. They are not tasks of their own; they are written as holds inside T002, the
task whose edit could break them (the skip that must not skip an absent file, the skip that must not touch `.written`
or `owned`), and are seen passing before the production edit and after it. R3 has a real RED (e1) and its own
production line, so it stays a task. R6 is a file whose check (`tests/test_changelog.py`) is already in the suite;
it rides with the first user-visible commit (T002) and is extended in T004, as below.

**The Pin stage** (`/characterise`, plan.md *Pin*) is a host task, T001, before any implementation.

## Format: `[ID] [P?] Description` — each task is one increment, one commit

`[P]` marks a task whose files are disjoint from every sibling's it could run beside; see *Parallel opportunities*.
None is marked: every implementation task shares a file with its neighbour.

---

## Phase 1: Pin (host)

### T001 — Pin what a refresh rewrites, refuses and leaves, and the strategy record a survey derives (host task)

- [x] **Host task — not delegated.** The host writes two rows in `delivery/survey/pinned.md` before T002 and commits
  them alone: (1) what a refresh rewrites, refuses and leaves, naming the holding tests —
  `tests/test_adopt_facts.py` (the record stays still between surveys; a file taken over stays taken; the page follows
  the record) and `tests/test_uncommitted.py` (a hand edit to a file a refresh writes is refused by name); (2) the
  strategy record a survey derives, naming `tests/test_strategy.py`. Not pinned, because the slice changes it on
  purpose: that a seeded file differing from the factory default is rewritten, and that `before` reads the tree's
  rows. The pinned tests are run green here (`make test TESTS="test_adopt_facts test_uncommitted test_strategy"`).

**Files:** `delivery/survey/pinned.md` (the only file under `delivery/` this slice changes, AC-S21-11).

---

## Phase 2: Implementation stage

### T002 — A seeded file that is there is the project's; one that is missing is written (R1, with R2 and R4 held, and R6 begun · AC-S21-1, -2, -3, -4, -6, -7, -8, -11)

- [x] **Rule R1** — a refresh never compares, rewrites, counts or stamps `.specify/cruise.json`,
  `.specify/product-owner.md`, `.specify/models.json` or `.specify/drive.json` where it exists on disk when the
  refresh starts. **R2**, **R4** and **R6** are folded in, for the reason given under *How the example map was cut*.

**RED** (new `tests/test_refresh_owned.py`, one example at a time; each fails today because the refresh rewrites the
file to the factory default, so its bytes differ and the report counts it):
- R1 e1 `cruise.json` committed with `enabled: true`, `max_iterations: 10` → after `adopt --refresh` bytes unchanged,
  absent from `git status`, not in the rewritten count. e2 `product-owner.md` committed with its sections filled →
  the same three. e3 `models.json` and `drive.json`, each committed with a non-default value → the same, one test
  each. e4 the same repository, `slipwai adopt --confirm` recording one answer → the four unchanged (the confirm
  path calls `refresh()` and inherits the fix; RED today for the same reason).

**Held in this task** (green on arrival, written first and run before the edit, run again after; they guard the
edit, they are not a RED of their own):
- R2 e1 `cruise.json` deleted and the deletion committed → after the refresh it holds the factory default and the
  report counts it. e2 the same for `product-owner.md`. (Today's behaviour: a missing file is written. The edit must
  not turn "skip the four" into "skip the four whether present or not".)
- R4 e1 a convergence row moved by hand in `project.json` → `<delivery>/docs/convergence.md` is rewritten to show it
  (today's behaviour; the edit must not take the pages out of the loop). e2 after any refresh `<delivery>/.written`
  lists the four. e3 the report prints no `owned:` line naming one of the four.

**GREEN** — name the four once, in one small new module under `src/slipwai/` (for example `seeded.py`), from the
constants their writers already export (`project/cruise_record.py` `CONFIG`, `project/drive_settings.py` `CONFIG`,
`project/decisions.py` `PAGE`, and the models table's path in `scaffold.py`), placed for the repository's layout, with
one function returning *kept* = those of the four that exist on disk. In `resurvey.py` `refresh()`: the rewrite loop
skips the kept exactly as it skips `owned`; the final `stamp(...)` leaves them out. Do not touch the `.written`
content in `after`; do not extend `done.owned`. The edit to `resurvey.py` is net zero lines or fewer: if it would
exceed 350, move a self-contained block out beside the new module first (a REFACTOR step in this task, run on green).
Add `changelog.d/refresh-keeps-owned-files.md`, first line `PATCH`, labelled experimental (brownfield adoption),
saying a refresh no longer rewrites the four settings and owner-brief files and what a repository whose refresh
already reset one of them does (restore it from its history). Add the one sentence to the `--refresh` row of
`docs/adopting.md`: a refresh leaves those four files where they exist.

**REFACTOR:** if `resurvey.py` was over budget, the move-out above; otherwise none.

**Verify:** `make test TESTS="test_refresh_owned test_adopt_facts test_uncommitted test_changelog"` green, then
`make lint typecheck check-structure`. `VERSION` untouched. Commit — the fragment is in this commit, the first
user-visible change (Principle VIII, AC-S21-11).

**Files:** `src/slipwai/seeded.py` (new; name at the implementer's discretion, one small module),
`src/slipwai/resurvey.py`, `tests/test_refresh_owned.py` (new), `changelog.d/refresh-keeps-owned-files.md` (new),
`docs/adopting.md`.

### T003 — An uncommitted change to a seeded file refuses nothing (R3 · AC-S21-5)

- [x] **Rule R3** — the refusal protects what a run writes, and the refresh no longer writes these four where they
  exist. Needs T002 (the *kept* function).

**RED** (in `tests/test_refresh_owned.py`):
- R3 e1 `cruise.json` edited, not committed → today `refuse_foreign` refuses by name because `writes()` lists it;
  after the change the refresh runs and the edit stands, byte for byte. Fails today with a refusal naming
  `.specify/cruise.json`.
- R3 e2 an uncommitted hand edit to `<delivery>/docs/convergence.md` → refused by name, as today. **A hold: today's
  behaviour, passes before the change** (and `tests/test_uncommitted.py` already holds it); it guards the edit from
  widening into "refuse nothing".

**GREEN** — `resurvey.py` `writes()` leaves out the kept (the same function from T002), so `refuse_foreign` does not
refuse on them. Net zero lines in `resurvey.py` or fewer.

**REFACTOR:** none expected.

**Verify:** `make test TESTS="test_refresh_owned test_uncommitted test_adopt_facts"` green, then
`make lint typecheck check-structure`. Commit.

**Files:** `src/slipwai/resurvey.py`, `tests/test_refresh_owned.py`.

### T004 — `strategy.before` follows the map as the refresh leaves it (R5, and the fragment extended · AC-S21-9, -10, -11)

- [x] **Rule R5** — each row-derived precondition is read from the rows after reconciliation, never from the tree's
  reading alone. Independent of T002/T003 in logic; sequenced after them only because it edits `resurvey.py`.

**RED** (new `tests/test_refresh_strategy.py`; read `project.json` `strategy.before` and
`<delivery>/docs/change-strategy.md` after `adopt --refresh`; a repository whose tree reads Safety net `tests-exist`):
- R5 e1 Safety net recorded `confirmed` at `tests-pass` → no *a green suite in the gate — the safety net is
  `tests-exist`* entry in either file. Fails today: the entry is derived from the tree's reading. e3 Path to
  production recorded by a person at a rung above `scripted` → the *a pipeline that deploys* entry gone, both files.
  Fails today for the same reason. e4 Structure recorded above `as-found` → its entry gone, both files. Fails today.
- R5 e2 the row left at `tests-exist` → both files still carry the entry. **A hold: today's behaviour, passes before
  the change.** e5 `recommended`, `because`, `decided`, `finished`, `programme` equal before and after the refresh
  (an unchanged-derivation proof taken in the same repository as e1). **A hold: today's behaviour, passes before the
  change.** Both guard the new derivation from altering anything but `before`.

**GREEN** — `strategy.py`: one function that, given the reconciled rows and the recommended strategy, returns the
platform entries the record leads with followed by `preconditions(rows, strategy)`; `recommend()` calls it too, so
the two cannot drift (a behaviour-preserving extraction, covered by `tests/test_strategy.py`, which stays green).
`resurvey.py` `refresh()`: after the rows are reconciled and before `project_files(...)` assembles `after`, replace
the strategy record's `before` with that function's result; `change-strategy.md` and `project.json` take it from the
same assembly. Net zero lines in `resurvey.py` or fewer; the body of the new function lives in `strategy.py`.
Extend `changelog.d/refresh-keeps-owned-files.md` (same file, still `PATCH`, still experimental) with the second
change: the strategy page no longer names a prerequisite the map shows as met. R6 e1: `tests/test_changelog.py`
green.

**REFACTOR:** only the extraction above, run on green with `tests/test_strategy.py`.

**Verify:** `make test TESTS="test_refresh_strategy test_strategy test_adopt_facts test_refresh_owned test_changelog"`
green, then `make lint typecheck check-structure`. Commit.

**Files:** `src/slipwai/strategy.py`, `src/slipwai/resurvey.py`, `tests/test_refresh_strategy.py` (new),
`changelog.d/refresh-keeps-owned-files.md`.

---

## Phase 3: Gates (host)

### T005 — Both full gates (host task)

- [ ] **Host task — not delegated.** Run `make verify` and `make -f delivery/Makefile verify` on the tree after T004;
  both green (AC-S21-11). Confirm the diff touches under `delivery/` only `delivery/survey/pinned.md`, `VERSION` is
  `1.5.2.dev0`, and `generate`, `add-service` and `migrate` write what they wrote (their existing tests are in
  `make verify`). Then the demo from [quickstart.md](quickstart.md).

---

## Parallel opportunities

- **Nothing here runs concurrently.** T002, T003 and T004 all edit `src/slipwai/resurvey.py`; T002 and T003 also
  share `tests/test_refresh_owned.py`; T002 and T004 share `changelog.d/refresh-keeps-owned-files.md`. Two delegates
  would write one file, and `resurvey.py` has no spare lines for a merge to absorb. They run one at a time, in order,
  each a green committed suite before the next starts.
- **By manifest only:** T004's new test file and its `strategy.py` extraction are disjoint from T002/T003's new
  module and test file, so a delegate could draft T004's RED in `tests/test_refresh_strategy.py` while T003 runs. It
  is not worth a second agent: the `resurvey.py` edit still has to wait, and a RED written against a tree that has
  not yet gained T002/T003 is observed against the wrong baseline.
- **Host tasks:** T001 precedes T002 (it records the baseline T002 changes); T005 runs alone after T004, reading
  the whole tree.
- Most delegates at once: one.

## Design review

No screen in this slice


---

## Phase 4: Convergence pass 1 (appended 2026-10-03; converge delegate)

**Verdict: converged.** No `CRITICAL` or `HIGH` finding; AC-S21-1 … AC-S21-10 hold at HEAD (`7be3773`) by reading
and by running, and AC-S21-11 holds as far as this pass may check it (both full gates are T005's). The three tasks
below are what the slice still owes, none of which re-opens the loop. Evidence for each is in the pass's return.

### T006 — A refresh's `before` is held whole at the CLI, not only its three row entries (`MEDIUM` · AC-S21-10 · Principle V)

- [x] `with_reconciled()` (`src/slipwai/strategy.py`) is a second place `before` is assembled, and two of its three
  inputs have no test through a refresh. Reproduced in a disposable clone, each restored afterwards: replacing
  `record.get("recommended", "leave-it")` with the literal `"leave-it"`, and replacing the platform products with
  `[]`, each left `make test TESTS="test_refresh_owned test_refresh_strategy test_strategy test_adopt_facts
  test_platform test_programme"` green — while the first would drop *a seam requests enter through* and
  *`/characterise` pinning each seam* from a `strangler-fig` page, and the second every *the platform in support*
  line. The behaviour at HEAD is right (run by hand: a Maven repository with Spring 3.2.8, `--why "split it so teams
  can move"`, Safety net confirmed at `tests-pass`, then `adopt --refresh` — five platform entries and both
  strangler-fig entries stand, only the safety-net entry goes); only the test is missing.

**RED** (in `tests/test_refresh_strategy.py`, under 350 lines): a hold that is green on arrival, shown to have teeth
by the two mutations above, each restored with `git checkout -- src/slipwai/strategy.py`.
**GREEN names the sweep:** for every argument `with_reconciled()` hands `before_of()` — the rows, the strategy
name, the products — one example through `slipwai adopt --refresh` whose `strategy.before` and
`<delivery>/docs/change-strategy.md` would differ if that argument were wrong; not the two instances found here.
No production edit is expected.

**Files:** `tests/test_refresh_strategy.py`.

### T007 — The stamp's `- left` is observed or removed (`LOW` · AC-S21-5 · Principle III)

- [x] `resurvey.py`'s last line subtracts the kept files from what `stamp()` records, and nothing observes it:
  removing `- left` left `test_refresh_owned` and `test_refresh_strategy` green (clone, restored). By reading
  `uncommitted.py`, `refuse_foreign` consults the stamp only for paths in `writes()`, which already leaves the kept
  out, so the only observable is `.delivery-tools/written.json` itself. The changelog's *a later run does not take
  the project's edit for slipwai's own* rests on this line alone.

**GREEN names the sweep:** every clause of rule R1 (*never compares, rewrites, counts or stamps*) has an example
that fails without its line, or the line it has none for is removed as mechanism with no behaviour — decided for
the whole rule, not for `stamp` alone.

**Files:** `tests/test_refresh_owned.py`, and `src/slipwai/resurvey.py` only if the line is removed (net negative).

### T008 — Generated text about who writes the four agrees with D24 (`LOW` · AC-S21-8 · Principle I) — verify first

- [x] `src/slipwai/project/decisions.py` writes into every project's `.specify/product-owner.md`: *`slipwai
  migrate` never rewrites it*. AC-S21-8, D24 and this slice's fragment say `.written` lists it so that `migrate`
  merges a newer factory's version with the project's. Found by reading; **not reproduced by running `migrate`** in
  this pass, so the first step is to see which of the two a migrate over a filled-in brief actually does. The text
  predates the slice; the slice is what put the other statement beside it.

**GREEN names the sweep:** every sentence the factory generates — pages, commands, the four files' own headers —
about what `adopt --refresh`, `adopt --confirm` and `migrate` do to any of the four says what D24 says, held by
one test over the generated text; not this one sentence. If the brief is meant to be exempt from `migrate`'s
merge, that is a product question for the host, not this task's to choose.

**Files:** to be named by the host once the first step says which statement is true.

**T006, T007 done** (commit after `7b84df0`, tests only): three examples over a Maven repository with a product out
of support and a capability trigger hold the strategy name, the products and the rows a refresh hands `before`; a
record example holds *never stamps* and a non-text brief holds *never compares* — each seen failing under its
mutation in a disposable clone. **T008 closed as stated, not changed** (D26): a merge is not a rewrite; the brief's
line stands.

## Convergence

**Converged on pass 1** (2026-10-03, cruise iteration 4, `drive-converge`, host model, fresh context) at `7be3773`:
no `CRITICAL` or `HIGH`; one `MEDIUM` and two `LOW` appended as T006–T008 and closed above, so no second pass was
spent. Levels accounted for in the one pass: functions (`recommend()` unchanged over 2160 input combinations against
`c72571d`), callers (`cli_adopt.py:202`, `confirm.py:124`, `:161`; `adopt.py:234` reconciles nothing), the CLI
(`adopt --refresh`, `adopt --confirm`, default and relocated delivery directory), the pages (`change-strategy.md`
renders the record's `before`, `strangle_command.py:53`; no generated text tells anyone to revert the four), the
published contract (fragment `PATCH`, experimental, restore instruction; `VERSION` `1.5.2.dev0`). The sweep for
siblings: 283 other listed files appended-to and refreshed, all reset, none of them seeded-then-project-owned (D24
leaves the record-driven ones in the loop). Constitution: **I** — `resurvey.py:263–267` (the kept files skipped),
`resurvey.py:63` (left out of the refusal), `project/seeded.py:20–22`; **III** — one 22-line module, one function
(`strategy.py:118–121`); **V** — `tests/test_refresh_owned.py`, `tests/test_refresh_strategy.py` through the CLI,
each example with teeth; **VIII** — `changelog.d/refresh-keeps-owned-files.md:1` `PATCH`, `VERSION` unchanged. No
application start-up path changed. The map: no rung reached by this slice; `make check-convergence` run at T005.
Two findings outside the slice's diff went to the split's Parking Lot.

