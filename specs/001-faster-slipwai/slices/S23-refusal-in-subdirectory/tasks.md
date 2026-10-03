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
