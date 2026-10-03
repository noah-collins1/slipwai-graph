# Tasks: S23-refusal-in-subdirectory — a refresh never writes over uncommitted work where the project sits in a subdirectory of its git repository

**Input**: [plan.md](plan.md) (*The example map* R1–R7 is what the tasks cut on; *Design*; *Pin*; *Project
Structure*), [research.md](research.md), [data-model.md](data-model.md), [quickstart.md](quickstart.md); acceptance
criteria AC-S23-1 … AC-S23-10 in `specs/001-faster-slipwai/spec.md` under `### S23-refusal-in-subdirectory`;
decisions D12, D29, D36, D37, D38 in `specs/001-faster-slipwai/decisions.md`. No `examples.md`: a method slice with
no screen and no event model.

**Branch**: `adopt-method` (D12). No `slice/` branch, no push, no claim. One commit per task.

**Delegation** (`.specify/drive.json`: `delegate: story`, `cycle: rule`): these tasks carry no user-story tag, so
they are delegated **per rule**, one delegate per implementation task, each its own RED-GREEN-REFACTOR increment and
its own commit. The "Files" line of a task is its manifest: the only files that delegate may write. Nobody but the
host writes `tasks.md`.

**Constraints that hold for every task** (plan.md *Constraints*): standard library only, no mocking framework (tests
drive `slipwai adopt` through the CLI against a temporary git repository, with the helpers already in the test tree —
`tests/test_adopt.py` `repository()` and `slipwai()`, `tests/test_candidates.py` `adopted()`, `MONOREPO` and
`record()`, `tests/test_replay.py` `git()`); `PATCH` — no setting, flag or file added to a generated project; nothing
under `delivery/scripts/`, `tools/`, the `Makefile`, CI or hook settings changes; `VERSION` stays `1.5.2.dev0`;
`src/slipwai/add_service.py` is untouched; `tests/test_uncommitted.py` and `tests/test_refresh_owned.py` are **not
edited** (R6e1); every file under `src/` and `tests/` stays within the 350 lines `make check-structure` holds. A test
that needs a symbolic link or a non-ASCII directory name skips, saying why, where the platform cannot make one.

**Quick test and pre-commit.** The quick test of an increment is `make test TESTS="<modules>"`, the modules each task
names. Before each commit run `make lint typecheck check-structure` as well.

**Versioning, on every commit** (`AGENTS.md`, *Versioning is not optional*): the commit message states the level.
A commit that changes `src/slipwai/`, `docs/adopting.md` or the fragment says `Level PATCH; VERSION is not raised
because it already carries the PATCH (1.5.2.dev0) the fragment claims` and names the reason (the same answers,
generated better). A commit that changes only `tests/` says it reaches no user and so does not raise the number.
`VERSION` and anything under `release/` are never edited.

**Observing a RED, and the "seen failing" rule.** Each RED is observed failing for its stated reason before the
production edit. Examples the plan marks as green with R1's change (R2e2, R2e3, R4, R5e1) cannot fail on the tree
once R1 is committed; each is **seen** failing by reversing R1's production hunk in the working tree
(`src/slipwai/uncommitted.py` only), running the test, then restoring it with `git checkout -- src/slipwai/uncommitted.py`
and confirming `git status` shows only the task's own files. The tree is clean of the reversal on every exit path,
including a stop. Holds (R2e1, R3e1, R5e2, all of R6) are written as holds, saying so in the test's name or comment,
and are observed passing — they are not a RED.

**The Pin stage** (`/characterise`, plan.md *Pin*) is a host task, T001, before any implementation.

## Format: `[ID] [P?] Description` — each task is one increment, one commit

`[P]` marks a task whose files are disjoint from every sibling's it could run beside; see *Parallel opportunities*.
None is marked: every implementation task shares `src/slipwai/uncommitted.py` or a test file with a neighbour.

---

## Phase 1: Pin (host)

### T001 — Pin what the refusal answers where the project is the repository's top (host task)

- [x] **Host task — not delegated.** The host appends one row to `delivery/survey/pinned.md` before T002 and commits
  it alone: what the refusal answers where the project is the top of its repository, naming the holding tests —
  `tests/test_uncommitted.py` (the `/ground` sequence commits once; a hand edit to a file a refresh writes is refused
  by name; what slipwai left is its own after the record moves; the same where `.git` is read-only) and
  `tests/test_refresh_owned.py`. Not pinned, because the slice changes it on purpose: in a subdirectory project
  nothing is refused and nothing is recorded. The pinned tests are run green here
  (`make test TESTS="test_uncommitted test_refresh_owned"`). The commit says no user-visible tree changed, so the
  number is not raised.

**Files:** `delivery/survey/pinned.md` (the only file under `delivery/` this slice changes).

---

## Phase 2: Implementation stage

Every implementation task starts from the green committed suite its predecessor left, and each is one commit.

### T002 — A person's uncommitted change is refused by the project's name for it (R1 · AC-S23-1, -2)

- [x] **Rule R1** (`45184be`) — a person's uncommitted change to a file the run writes is refused where the project sits in
  `sub/`, the path printed as the project spells it. **This is the first commit that changes `src/slipwai/`, so the
  R7 fragment lands in it** (a first draft; T008 completes the wording).

**RED** (new `tests/test_uncommitted_subdirectory.py`; the repository is one git repository, the adopted project in
`sub/` with the adoption committed, `other/` beside it, commands run in `sub/`). Each fails today because the paths
git reports begin `sub/` and never match what the run writes:
- e1 `delivery/docs/convergence.md` edited → `adopt --refresh` exits 2, stderr holds `` `delivery/docs/convergence.md` ``
  and not `sub/delivery`, the edit is still in the file, `git status` lists that one path only.
- e2 the same edit → `adopt --confirm shop` exits 2 and `project.json` is byte-for-byte what it was.
- e3 the same edit → `adopt --decline themes` exits 2 and `project.json` is byte-for-byte what it was.
- e4 a listed file deleted, not committed → the refresh is refused naming it.
- e5 a path the run writes present on disk and untracked (its removal from the index committed) → refused naming it.

**GREEN** — `changed(root)` in `src/slipwai/uncommitted.py` asks git for the project's prefix
(`git rev-parse --show-prefix`, run in `root`; research R-2) and returns each path with that prefix taken off. Keep
the signature and the three answers (a list, an empty list, `None` where git cannot answer); a failing
`rev-parse` is `None`, as a failing status is today. Keep the rename rule (the entry after an `R` or `C` is where it
came from and is skipped). The smallest change is taking the prefix off: dropping paths outside the project is R3's.
Update the module docstring to say where `changed()` looks. Add `changelog.d/refusal-in-subdirectory.md`, first line
`PATCH`, labelled *experimental: brownfield adoption*, saying that a refresh, confirm or decline in a project that
sits in a subdirectory of its repository now refuses to write over an uncommitted change (it never did, and
`written.json` stayed `{}`); T008 completes it.

**REFACTOR:** none expected.

**Verify:** `make test TESTS="test_uncommitted_subdirectory test_uncommitted test_refresh_owned test_changelog"`
green, then `make lint typecheck check-structure`. `VERSION` untouched. Commit, level line as above — the fragment
is in this commit, the first user-visible change (Principle VIII, AC-S23-10).

**Files:** `src/slipwai/uncommitted.py`, `tests/test_uncommitted_subdirectory.py` (new),
`changelog.d/refusal-in-subdirectory.md` (new).

### T003 — What slipwai left is slipwai's (R2 · AC-S23-3, -4)

- [x] **Rule R2** (`16cd0c9`) — a run's own uncommitted regeneration is recorded, project-relative, and a later run writes over
  it; a person's edit on top of it is refused. Needs T002 (R1's change is what makes `stamp()` recognise the path).

**Tests** (in `tests/test_uncommitted_subdirectory.py`):
- e1 `--confirm shop`, a row settled by hand in `project.json`, `--confirm themes`, `--refresh`, nothing committed
  between → each exits 0. **A hold: green today, for the wrong reason (nothing is ever refused); passes before and
  after, and is observed passing.**
- e2 after e1's first step `sub/.delivery-tools/written.json` is not `{}`, every key is a path that exists under
  `sub/` as spelled, none starts with `sub/`, and `git status` does not list the file. **Fails today; green with
  R1's change — seen failing with R1's hunk reversed in the working tree, then restored (see *Observing a RED*).**
- e3 after e1's first step a person appends a line to one recorded file → the refresh is refused naming that file.
  **Fails today; green with R1's change — seen failing the same way.**

**GREEN** — none in `src/`: the behaviour R1 produced. The increment is the proof, and it is committed with the
reversal seen. If a test fails with R1's change in place, stop and report; do not edit `uncommitted.py`.

**REFACTOR:** none.

**Verify:** `make test TESTS="test_uncommitted_subdirectory test_uncommitted"` green, then
`make lint typecheck check-structure`. Commit, level line (tests only: reaches no user, number not raised).

**Files:** `tests/test_uncommitted_subdirectory.py`.

### T004 — What is outside the project is not this run's (R3 · AC-S23-5)

- [x] **Rule R3** (`aedacf3`) — a change elsewhere in the repository refuses nothing and is never recorded. Needs T003 (same
  test file, green suite).

**RED** (in `tests/test_uncommitted_subdirectory.py`):
- e2 a file committed at the repository's top as `delivery/docs/convergence.md`, then edited → the refresh in `sub/`
  exits 0, the top-level file keeps its edit, and no key of `written.json` names it. **Fails today (refused, by
  mistake) and still fails after T002's prefix-stripping alone, because the top-level path spells a project path;
  this is the RED that drives the drop.**
- e1 `other/note.txt` edited → the refresh exits 0 and the edit stands. **A hold: passes before the change** (a path
  that spells nothing the run writes is not matched); it guards the change from widening into "refuse everything".

**GREEN** — `changed(root)` also limits the status to the project (`git status --porcelain=v1 -z
--untracked-files=all -- .`; research R-3) and drops any entry whose path does not start with the prefix, so the
answer does not rest on the pathspec alone; either git call failing is `None`. Extend the docstring to say a change
outside the project is not one.

**REFACTOR:** if `changed()` has grown past readable, split the prefix step and the status step into two small
functions in the same module, on green.

**Verify:** `make test TESTS="test_uncommitted_subdirectory test_uncommitted test_refresh_owned"` green, then
`make lint typecheck check-structure`. Commit, level line (PATCH, `VERSION` not raised, as above).

**Files:** `src/slipwai/uncommitted.py`, `tests/test_uncommitted_subdirectory.py`.

### T005 — An earlier factory's leftovers are refused once (R5 · AC-S23-9)

- [x] **Rule R5** (`e004e34`) — an uncommitted regenerated file with no record is not told apart from a person's edit. Needs
  T004 (same test file; the filter is in place).

**Tests** (in `tests/test_uncommitted_subdirectory.py`):
- e1 after `--confirm shop`, `written.json` emptied to `{}` (what an earlier factory left) → the refresh is refused
  naming regenerated files. **Fails today; green with R1's change — seen failing with R1's hunk reversed in the
  working tree, then restored.**
- e2 those files committed → the refresh exits 0. **A hold: green today; passes before and after.**

**GREEN** — none in `src/`: no special case is added (D37). If a test fails with the production code as it stands,
stop and report; do not edit `uncommitted.py`.

**REFACTOR:** none.

**Verify:** `make test TESTS="test_uncommitted_subdirectory test_uncommitted"` green, then
`make lint typecheck check-structure`. Commit, level line (tests only).

**Files:** `tests/test_uncommitted_subdirectory.py`.

### T006 — Wherever the project sits (R4 · AC-S23-6)

- [x] **Rule R4** (`8b592d7`) — depth, a name git would quote, and a symbolic link change nothing. Needs T005 (the rules R1,
  R2 and R3 it repeats are in place).

**Tests** (new `tests/test_uncommitted_places.py`, each a small run of the same three checks — R1e1, R2e2 and R3e1 —
against a different placement; share the setup with the helpers the other file uses, not by importing from it unless
`tests/test_adopt.py`/`tests/test_candidates.py` already export it):
- e1 the project in `a/b/`.
- e2 the project in `dé pt/` (a space and a non-ASCII letter); skip, saying why, where the filesystem cannot make it.
- e3 the commands run in a symbolic link to `sub/`; skip, saying why, where a link cannot be made.

All three **fail today (R1's reason) and are green with R1's change — each seen failing with R1's hunk reversed in
the working tree, then restored.**

**GREEN** — none in `src/`: the prefix comes from git, so a link and a quoted name need no code (research R-2). If a
placement fails with the production code as it stands, stop and report.

**REFACTOR:** none.

**Verify:** `make test TESTS="test_uncommitted_places test_uncommitted_subdirectory"` green, then
`make lint typecheck check-structure`. Commit, level line (tests only).

**Files:** `tests/test_uncommitted_places.py` (new).

### T007 — At the top, and without git, every answer is today's (R6 · AC-S23-7, -8)

- [x] **Rule R6** (`d91b989`) — no change where the project is the repository's top, or is in no repository. **Every example is
  a hold: green before T002 and after; none is a RED, and each is written as a hold, saying so.** The task adds
  proof of what T002–T004 must not break. Needs T006 (same new file).

**Tests:**
- e1 `tests/test_uncommitted.py` and `tests/test_refresh_owned.py` pass with **no edit to either**: run unchanged,
  observed green; confirm `git diff` over the slice shows neither changed.
- e2 (in `tests/test_uncommitted_places.py`) at the top, after `--confirm shop`, the keys of `written.json` are the
  paths as before: no leading `./`, none absolute.
- e3 (in `tests/test_uncommitted_places.py`) an adopted project copied out to a directory in no git repository →
  the refresh exits 0, refuses nothing, writes no `written.json`, and prints no traceback.

Observe e2 and e3 passing against the pre-T002 `uncommitted.py` as well, by the sanctioned route: write the old text
over `src/slipwai/uncommitted.py` (`git show <T001 commit>:src/slipwai/uncommitted.py`), run the tests, restore with
`git checkout -- src/slipwai/uncommitted.py`.

**GREEN** — none in `src/`. If a hold fails, stop and report: it is a regression of T002 or T004.

**REFACTOR:** none.

**Verify:** `make test TESTS="test_uncommitted_places test_uncommitted test_refresh_owned"` green, then
`make lint typecheck check-structure`. Commit, level line (tests only).

**Files:** `tests/test_uncommitted_places.py`.

### T008 — The release says what it is (R7 · AC-S23-10)

- [x] **Rule R7** (`3f45d00`) — one `PATCH` fragment, labelled experimental; `VERSION` unchanged; `add-service` untouched.
  The fragment began in T002; this task completes its wording and adds the one sentence of documentation.

**RED:** none — `tests/test_changelog.py` is already in the suite and passes from T002. The checks are R7e1 and
R7e2, both holds: e1 the fragment `changelog.d/refusal-in-subdirectory.md` has first line `PATCH`, says
*experimental: brownfield adoption*, says what was lost (in a subdirectory project the refusal never fired, a person's
edit was written over at exit 0, and `written.json` stayed `{}`), and says what R5 asks once (a repository already
adopted in a subdirectory whose earlier run left regenerated files uncommitted is refused naming them at the first
run, because slipwai cannot tell them from an edit of a person's; committing or stashing once clears it — D37);
`make test TESTS="test_changelog"` green. e2 `git diff` over the slice's commits shows no change to
`src/slipwai/add_service.py` or `VERSION`.

**GREEN** — complete the fragment's wording as e1 says. In `docs/adopting.md`, the `--refresh` row gets one
sentence: the refusal looks at the changes under the project's own directory, whether or not that directory is the
top of its repository.

**REFACTOR:** none.

**Verify:** `make test TESTS="test_changelog"` green, then `make lint typecheck check-structure`; `git diff --stat`
over the slice shows e2. Commit, level line (PATCH, `VERSION` not raised because it already carries 1.5.2.dev0).

**Files:** `changelog.d/refusal-in-subdirectory.md`, `docs/adopting.md`.

**Implementation record (host, cruise iteration 6).** T002–T008 each ran as one `drive-implement` delegate on
sonnet, fresh context, boundary `rule`, cycle `rule`, no fan-out, one after another. What differs from the task
text: with the project in `sub/` the candidate for the project's own directory is named `sub`, not `shop`, so
R1e2, R2e1 and R5e1 confirm `sub`; `tests/test_uncommitted_places.py` adopts with `--name shop`, because a
directory named `dé pt` is not a name adoption accepts on its own; and R3e2 uses `delivery/agents/drive-implement.md`
at the repository's top with `--confirm sub` rather than `delivery/docs/convergence.md` with `--refresh`, so that the
run records something and the *not recorded* assertion can fail (a confirm runs the same refresh).

---

## Phase 3: Gates (host)

### T009 — Both full gates on the final tip (host task)

- [ ] **Host task — not delegated.** Run `make verify` and `make -f delivery/Makefile verify` on the tree after
  T008; both green (Principle XIV). Confirm the slice's diff touches under `delivery/` only
  `delivery/survey/pinned.md`, `VERSION` is `1.5.2.dev0`, `src/slipwai/add_service.py` is unchanged, and
  `tests/test_uncommitted.py` and `tests/test_refresh_owned.py` are unedited. Then the demo from
  [quickstart.md](quickstart.md).

---

## Parallel opportunities

- **Nothing here runs concurrently.** T002 and T004 both edit `src/slipwai/uncommitted.py`; T002–T005 all write
  `tests/test_uncommitted_subdirectory.py`; T006 and T007 both write `tests/test_uncommitted_places.py`; T002 and T008
  share `changelog.d/refusal-in-subdirectory.md`. Two delegates would write one file, and the file-size budget leaves
  no room for a merge to absorb two drafts. They run one at a time, in order, each from a green committed suite.
- **By manifest only:** T006's new file is disjoint from T003–T005's, so a delegate could draft its tests while
  T004 or T005 runs. It is not worth a second agent: each of its tests is seen failing by reversing T002's production
  hunk in the working tree, and doing that while another delegate edits `uncommitted.py` would reverse the wrong
  file state. T008's two files are disjoint from T003–T007's, and T008 could run beside them, but its fragment wording
  must reflect T005 and T002's final text; run it after.
- **Host tasks:** T001 precedes T002 (it records the baseline T002 changes); T009 runs alone after T008, reading
  the whole tree.
- Most delegates at once: one.

## Design review

No screen in this slice

## Convergence

**Converged on pass 1** (2026-10-03, cruise iteration 6, `drive-converge`, host model, fresh context) at `12a4608`,
over `13ec3c1..12a4608`: no `CRITICAL` or `HIGH`; one `MEDIUM` and five `LOW` appended as T010–T015 under Phase 4
below, none of which re-opens the loop. The pass ended inside its budget and is complete for what it lists; what it
could not sweep on this machine is named at the end. No `.codegraph/` in this tree: callers were found by text
search (`grep` over `src/slipwai/`).

**Levels.** *Domain* — `changed()` (`src/slipwai/uncommitted.py:31–57`) probed directly in scratch repositories
under `/tmp` over the status shapes listed under *Sweeps*; `stamp()` (`:76–85`) and `refuse_foreign()` (`:88–105`)
are unchanged by the diff and read `changed()` only through `path in now`, so the project-relative spelling reaches
both by construction. *Use case* — three call sites, all of them: `resurvey.py:167` (the refusal, before the first
write of a refresh, the wrappers at `:172`), `confirm.py:124` (before `project.json` is written at `:156`; `--confirm`
and `--decline` are one function, `cli_adopt.py:192`), `resurvey.py:305` (the stamp, last line of a refresh). A
confirm's refresh runs `clean_checked=True`, after the check at `confirm.py:124` and nothing but `project.json`
written in between. Every path through `--refresh`, `--confirm`, `--decline` reaches the refusal before it writes.
*Delivery adapter* — exit 2 and the message on stderr, run by hand and held by the tests; the message for a
`--decline` given alone says `` `slipwai adopt --confirm` writes `` (T015, not this slice's). *Screen* — none.
*Published contract* — the fragment (`changelog.d/refusal-in-subdirectory.md:1` `PATCH`, *experimental: brownfield
adoption*, what was lost, the catch-up of D37): each sentence checked against a run and none found untrue in the
state it describes; `docs/adopting.md:149` one sentence, true; `written.json`'s keys project-relative in a
subdirectory and spelled as before at the top; `VERSION` `1.5.2.dev0`; `add_service.py`, `tests/test_uncommitted.py`
and `tests/test_refresh_owned.py` not in the diff. T002 asked for the *module* docstring to say where `changed()`
looks; the function's docstring says it and the module's is unchanged and still true — a difference from the task
text the Implementation record does not list, no task.

**Criteria** (tests in `tests/test_uncommitted_subdirectory.py` unless `places`, which is
`tests/test_uncommitted_places.py`). AC-S23-1 — `test_a_hand_edit_to_a_file_a_refresh_writes_is_refused_by_the_projects_name_for_it`.
AC-S23-2 — `test_the_same_edit_refuses_confirm_…`, `…refuses_decline_…`, `test_a_listed_file_deleted_…`,
`test_a_path_the_run_writes_that_is_present_and_untracked_…`. AC-S23-3 — `test_hold_what_a_run_left_and_a_row_settled_by_hand_…`
(a hold) with `test_what_a_run_leaves_uncommitted_is_recorded_as_the_project_spells_it`. AC-S23-4 —
`test_an_edit_on_top_of_what_a_run_left_is_refused_naming_that_file`. AC-S23-5 — `test_hold_an_edit_elsewhere_…`,
`test_a_file_at_the_top_that_spells_a_path_the_run_writes_is_neither_refused_nor_recorded`; the criterion as written
(`delivery/docs/convergence.md` at the top, `--refresh`) run by hand: exit 0, both edits stand, record `{}`.
AC-S23-6 — `places`, four placement tests; they repeat AC-S23-1, the record's spelling and the `other/` edit, not
AC-S23-3's second run nor AC-S23-5's top-level file (T014). AC-S23-7 — `tests/test_uncommitted.py` and
`tests/test_refresh_owned.py` unedited and green (run here, with the two new modules: 42 tests), `places`
`test_hold_at_the_top_…`. AC-S23-8 — `places` `test_hold_a_project_copied_to_a_directory_in_no_repository_…` holds
the first clause; **the second, *one git cannot read*, has no example** (T010; right at HEAD by hand). AC-S23-9 —
`test_an_earlier_factorys_uncommitted_leftovers_are_refused_once_naming_them`, `test_hold_those_files_committed_…`,
and the fragment's *Catch-up* paragraph. AC-S23-10 — the fragment, `tests/test_changelog.py`, `git diff --stat`
over the slice.

**Mutation** (one, restored with `git checkout -- src/slipwai/uncommitted.py`; `git diff --stat -- src tests` empty
after): the rename rule's two lines (`uncommitted.py:55–56`) deleted → `test_uncommitted test_uncommitted_subdirectory
test_uncommitted_places test_refresh_owned` 42 tests OK. The rule T002 was told to keep is observed by nothing (T011).

**Sweeps** (git 2.53.0, `changed()` called on scratch repositories; project in `sub/` unless said). Siblings whose
name the project's is a prefix of (`sub2/`, `subdir/`) and the top's `d/a.md`, all edited → `[]`; `sub/sub/d/a.md`
→ `sub/d/a.md` (the prefix comes off once). Staged rename inside→outside → the deletion, by the project's name;
outside→inside → the new path, no stray field; inside→inside → the new path only; a rename onto a path → that path;
`status.renames=copies` → the copy. Unmerged `UU` → reported. Tracked-and-ignored, edited → reported;
untracked-and-ignored at a path → not seen, as at the top (AC-S23-7; today's answer, not a task — the host may park
it). An untracked nested repository → `nested/`; a dirty gitlink → `nested`; neither is a path a run writes; a project
that is itself a nested repository is its own top. `status.relativePaths`, `status.showUntrackedFiles=no`,
`core.quotePath` → no effect. A linked worktree, a directory named `s[u]b*` (the pathspec is `.`, not the name) →
right. `GIT_DIR` and `GIT_WORK_TREE` both set, `GIT_WORK_TREE` alone, `GIT_PREFIX` → right; `GIT_DIR` alone → T012;
`GIT_CEILING_DIRECTORIES`, a corrupt `HEAD` → `None`, nothing refused. A worktree rename under intent-to-add (` R`) →
T011. `git` not installed → T013. **Not swept:** a case-insensitive filesystem (the directory entered as `SUB`
where the index says `sub`) and Windows path spellings — neither can be made on this machine.

**Constitution.** **I** (the factory does not write over a person's file) — `uncommitted.py:39–57` gives the refusal
the project's spelling, `resurvey.py:167` and `confirm.py:124` refuse before any write, and nothing outside the
project is recorded or written (`uncommitted.py:53`). **III** — one function grown by twelve lines, no module, flag
or setting; the prefix filter at `:53` is unreachable while the pathspec at `:40` holds, kept on purpose
(research R-3). **V** — every example enters through the CLI (`tests/test_uncommitted_subdirectory.py:44–171`,
`tests/test_uncommitted_places.py:62–122`), the fix begins with a boundary scenario (`:44`), holds are named holds;
gaps T010, T011, T014. **VIII** — `changelog.d/refusal-in-subdirectory.md:1` `PATCH`, `VERSION` unchanged; the
persisted `written.json` keeps its spelling at the top (`tests/test_uncommitted_places.py:94`). **XIV** — both full
gates are T009's, the host's, not run by this pass. No other principle is touched: no money, time, identity or
service boundary in the diff.

## Phase 4: Convergence pass 1 (appended 2026-10-03; converge delegate)

### T010 — *One git cannot read* is held by an example (`MEDIUM` · AC-S23-8 · Principle V)

- [x] (`9511efe`) Tests only; no production edit expected. AC-S23-8 names two states and `tests/test_uncommitted_places.py` holds
  one (a directory in no repository). By hand at `12a4608`: project in `sub/`, `delivery/docs/convergence.md`
  edited, `.git/HEAD` overwritten with `garbage` → `adopt --refresh` exit 0, no traceback, no `written.json`, the
  edit written over — the criterion's *as today*. Nothing fails if that becomes a refusal or a traceback.

**RED:** none — a hold, green on arrival, shown to have teeth by turning `return None` (`uncommitted.py:47`) into
`return []` and seeing it fail, restored with `git checkout -- src/slipwai/uncommitted.py`.
**GREEN names the sweep:** every way `changed()` answers `None` — no repository, a repository git cannot read, and
either of the two git calls failing — each with the project at the top *and* in a subdirectory (the hold there
today copies a top-level project only), each asserting exit 0, nothing refused, nothing recorded, no traceback.

**Files:** `tests/test_uncommitted_places.py` (≤ 350 lines).

### T011 — Every status entry that carries a second path is read as one entry (`LOW` · AC-S23-2, -7 · Principle V)

- [x] (`0bd2d2d`) `changed()` skips the origin of a rename or copy only where the *first* status letter is `R` or `C`
  (`uncommitted.py:55`), and nothing observes even that: with the two lines deleted, 42 tests stay green (this
  pass's mutation). Where the second letter is `R` — a file renamed in the working tree and added with
  `git add -N` — the origin is read as an entry of its own with its first three characters cut off. Reproduced:
  project in `ab/`, `ab/ab/x.md` renamed to `ab/moved.md`, `git add -N ab/moved.md` → status
  `' R ab/moved.md\0ab/ab/x.md\0'`, `changed()` returns `['moved.md', 'x.md']`; `x.md` is a different file with no
  change, and were it one a run writes the run would be refused naming it. At the top the same misreading gives a
  path that matches nothing; it is older than this slice.

**RED:** the reproduction above through `changed()`'s nearest boundary the suite already uses, expecting `x.md`
absent. **GREEN names the sweep:** every pair of status letters `git status --porcelain=v1 -z` can print whose
entry carries a second field — `R` or `C` in either column — with one example each for a staged rename inside the
project (the new path reported, the origin not), outside→inside, inside→outside (the deletion reported), at the top
and in a subdirectory; not the one pair found here. Extend the fragment by a clause only if a refusal a person could
have met changes.

**Files:** `src/slipwai/uncommitted.py`, `tests/test_uncommitted_subdirectory.py` or `tests/test_uncommitted_places.py`.

### T012 — `GIT_DIR` in the environment, with no `GIT_WORK_TREE` (`LOW` · **needs a decision** · AC-S23-8, D36)

- [x] **Decided by D40: option (a), no files, no criterion; a Parking Lot line.** Not answered by the criteria, the plan or D36–D38. With `GIT_DIR=<absolute>/.git` exported and the project
  in `sub/`, git takes `sub/` for the top of the working tree: on a clean tree `adopt --refresh` exits 2 naming
  284 files (*… and 276 more*), and *commit or stash* cannot clear it. With `GIT_DIR=.git` (relative) git finds no
  repository from `sub/`: exit 0 and a person's edit to `delivery/docs/convergence.md` is written over. Before this
  slice a subdirectory project was never refused, so neither is a regression; at the top both spellings answer
  correctly. **Options:** (a) leave it — the person exported git's own override, and `git status` in that shell
  says the same; (b) run the two git calls with `GIT_DIR`, `GIT_WORK_TREE`, `GIT_INDEX_FILE` and `GIT_PREFIX`
  removed from their environment, so the refusal is about the repository the project's directory is in; (c) refuse
  with one sentence naming the variable. The sweep, whichever is chosen: every `GIT_*` variable that moves the
  repository, the work tree or the index, for both callers of `changed()`.

**Files:** none until decided.

### T013 — `git` is not installed (`LOW` · **needs a decision** · AC-S23-8)

- [x] **Decided by D41: option (c); AC-S23-8 narrowed to a machine where `git` runs; a Parking Lot line.** With no `git` on `PATH`, `adopt --refresh` ends on a `FileNotFoundError` traceback raised in `changed()`
  (`uncommitted.py:39`, from `resurvey.py:167`), exit 1, nothing written. It is older than this slice and the same
  at the top. AC-S23-8 says *no run ends on a traceback* of a directory *git cannot read*; whether a machine without
  git is that state is not said. **Options:** (a) as *not a repository* — `None`, nothing refused, nothing recorded;
  (b) a one-line refusal that the command needs git; (c) leave it, out of this feature. The sweep: every
  `subprocess` call to `git` under `src/slipwai/` that an adopted project's commands reach.

**Files:** none until decided.

### T014 — Each placement repeats the criteria AC-S23-6 names (`LOW` · AC-S23-6 · Principle V)

- [x] (`6e6c154`) `PlacementChecks.check` runs AC-S23-1, the record's spelling and the `other/` edit. AC-S23-6 says AC-S23-1,
  -3 and -5 hold *as written*: the second run that must exit 0 over what the first left (AC-S23-3) and the file
  outside the project whose path spells one the run writes (AC-S23-5) are not repeated per placement. Both rest on
  the same twelve lines and hold in `sub/`; the gap is the example, not the behaviour.

**GREEN names the sweep:** for every placement in the file — `a/b/`, the quoted name, both links — a second run
after the first exits 0, and a committed-then-edited file outside the project at the project-relative spelling of
a recorded path (for `a/b/`, at the top *and* in `a/`) neither refuses nor is recorded. Tests only.

**Files:** `tests/test_uncommitted_places.py` (≤ 350 lines).

### T015 — A refused `--decline` is told what `--decline` writes (`LOW` · AC-S23-2 · delivery adapter)

- [x] (`d803713`) `slipwai adopt --decline themes` over an uncommitted edit prints `` `slipwai adopt --confirm` writes
  `delivery/docs/convergence.md` … `` (`confirm.py:124`): the person is told of a flag they did not give. Older than
  this slice and the same at the top; AC-S23-2 asks only that it is *refused the same way*, which it is. For the
  host to place — here or the Parking Lot. **GREEN names the sweep:** every verb string handed to
  `refuse_foreign()` names the flags the run was given (`--confirm`, `--decline`, both, `--refresh`), with an
  assertion on stderr for each; a `PATCH` clause in a fragment, since the message is what a person reads.

**Files:** `src/slipwai/confirm.py`, `tests/test_uncommitted.py` is not to be edited — a new example beside it.

**Host note on T010, T011, T014, T015 (D42).** All four are this slice's, each through its test. T015's files:
`src/slipwai/confirm.py`, a new example in `tests/test_uncommitted_subdirectory.py`, and a clause in
`changelog.d/refusal-in-subdirectory.md`; T011's fragment clause the same way where a person could have met it.

**Phase 4 record (host, cruise iteration 6).** T011, T015, T010 and T014 each ran as one `drive-implement` delegate
on sonnet, fresh context, boundary `task`, one after another. T011: `R` or `C` in either status column is one entry
(new `tests/test_uncommitted_renames.py`, twelve shapes at the top and in `ab/`, the converge pass's mutation now
caught by sixteen subtests); the fragment is unchanged, since no refusal a person could meet through the CLI was
reproduced. T015: a refused run names the flags it was given; the fragment says so. T010: no repository, an
unreadable `HEAD` and an unreadable index, at the top and in `sub/` — a state where only `rev-parse` fails could
not be made with a real repository, so that half of the test is held through `status` alone. T014: every placement
repeats the second run, the edit on top and the file outside the project; the second-run and edit-on-top
assertions were not seen failing on their own (every mutation tried fails the first refusal first).
Pass 1's verdict stands: converged, nothing `HIGH` or `CRITICAL`, no second pass.

## Phase 4: Gaps after converge (appended 2026-10-03; host, from the `drive-gaps` pass at `60d0284`; D43)

### T016 — What the refusal and the fragment tell a person can be followed (`MEDIUM` G1, `LOW` G2, G3 · AC-S23-9, AC-S23-11)

- [x] (`f507453`) Three findings on one surface — the words a refused person reads. The message keeps *Commit or stash those first* (true for a person's own edit to the named files) and adds *Each path is spelled from the project's directory.*; the fragment's catch-up says commit, and says why not to stash.

**RED** (in `tests/test_uncommitted_subdirectory.py`):
- G2 — a refusal's stderr says the paths it names are spelled from the project's directory; asserted in `sub/` and,
  in a new example beside (not in) `tests/test_uncommitted.py`, at the top of a repository. Fails today: the message
  has no such clause.
- G3 — `test_an_earlier_factorys_uncommitted_leftovers_are_refused_once_naming_them` asserts the names the message
  prints: the first eight leftovers in sorted order, each backticked, and *and N more* with N the rest. Tightening
  a test that passes: seen failing by cutting the message's list to seven in the working tree, then restored.

**GREEN names the sweep:** every sentence of advice the refusal and the fragment give — `refuse_foreign()`'s message
gains one clause after the names, in plain words, the same at the top and below it, keeping every word
`tests/test_uncommitted.py` asserts; the fragment's catch-up says to commit the named files and run again, with *or
stash them* taken out (G1: a stash takes the uncommitted answer in `project.json` with it and the refusal returns
after `git stash pop`), and gains a clause that the message now says where its names are spelled from. Each sentence
is read against a run in the state it describes: follow the catch-up as written in a scratch repository under `/tmp`
(the gaps pass's reproduction: a row settled, a refresh, `written.json` emptied to `{}`, the refusal, then what the
fragment says to do) and see the next run exit 0.

**Verify:** `make test TESTS="test_uncommitted test_uncommitted_subdirectory test_uncommitted_places test_refresh_owned
test_changelog"`, then `make lint typecheck check-structure`. Commit, level line (PATCH, `VERSION` not raised).

**Files:** `src/slipwai/uncommitted.py`, `tests/test_uncommitted_subdirectory.py`, `changelog.d/refusal-in-subdirectory.md`.
