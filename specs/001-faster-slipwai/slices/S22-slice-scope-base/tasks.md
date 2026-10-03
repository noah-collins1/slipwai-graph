# Tasks: S22-slice-scope-base — a slice branch cannot empty its own scope check by minting a base

**Input**: [plan.md](plan.md) (*The example map* R1–R8 is what the tasks cut on; *Design*; *Pin*),
[research.md](research.md), [data-model.md](data-model.md), [quickstart.md](quickstart.md); acceptance criteria
AC-S22-1 … AC-S22-21 in `specs/001-faster-slipwai/spec.md` under `### S22-slice-scope-base`; decisions D9, D12,
D19, D22, D23, D30, D31 in `specs/001-faster-slipwai/decisions.md`. No `examples.md`: a factory slice with no screen
and no event model.

**Branch**: `adopt-method` (D12). No `slice/` branch, no push, no claim. One commit per task.

**Delegation** (`.specify/drive.json`: `delegate: story`, `cycle: rule`): these tasks carry no user-story tag, so
they are delegated **per rule**, one delegate per implementation task, each its own RED-GREEN-REFACTOR increment and
its own commit.

**Constraints that hold for every task** (plan.md *Constraints*): standard library and `git` only, no mocking
framework (tests drive `assets/toolkit/scripts/check-slice-scope.py` through its command line in a temporary git
repository, as `tests/test_slice_scope_root.py` `SliceScopeFixtures` and `tests/test_slice_scope_hostile_branch.py`
`HostileBranchTest.run_gate` do; shallow and single-branch checkouts through `git clone --depth 1 file://…`, a plain
path ignores `--depth`); `PATCH` — no setting, flag or file added to a project; CI's exit code unchanged in every
project (D31); nothing under `delivery/scripts/`, `tools/`, the `Makefile`, CI or hook settings changes;
`assets/toolkit/scripts/check-migrations.py`, `assets/targets/*/scripts/check-flags.py`,
`src/slipwai/project/ci_workflows.py`, `src/slipwai/project/adopted_ci.py` and `tests/test_parallel_slices.py` are not
edited; `VERSION` stays `1.5.2.dev0`; **every file under `tests/` stays within 350 lines**
(`tests/test_line_widths.py`); the words existing tests read — `slice/S1 touches only what one slice may` and
`reaches outside what one slice may touch` — stay unchanged. Before each commit run
`make lint typecheck check-structure` as well as the task's quick test. Each RED is observed failing for its stated
reason before the production edit; a hold is observed passing before the change and again after.

**How the example map was cut.** R1 to R6 each have a real RED and are one task apiece. Examples that are today's
behaviour (R1 e6, e7; R2 e5's no-traceback half; R6 e3, e4) are written as holds inside the task whose edit could
break them, seen passing before the production edit and after it; they are not tasks of their own, because their
GREEN would be empty. R7 is a held check with no edit. R8 is the fragment: it must land **in the commit that first
changes the asset** (T002), so T002 creates it and T009 completes its wording.

**The Pin stage** (`/characterise`, plan.md *Pin*) is a host task, T001, before any implementation.

## Format: `[ID] [P?] Description` — each task is one increment, one commit

`[P]` marks a task whose files are disjoint from every sibling's it could run beside; see *Parallel opportunities*.
None is marked: every implementation task edits `assets/toolkit/scripts/check-slice-scope.py`.

---

## Phase 1: Pin (host)

### T001 — Pin which commit a slice branch is compared with, and what the gate answers without one (host task)

- [x] **Host task — not delegated.** The host appends one row to `delivery/survey/pinned.md`, as plan.md *Pin* says,
  and commits it alone before T002: the behaviour this slice changes, naming the holding tests
  `tests/test_parallel_slices.py` `SliceScopeGateTest` (off a slice branch nothing is held; a slice's own files pass;
  a `main` that moved locally and was merged in is the base), `tests/test_slice_scope_root.py`,
  `tests/test_slice_scope_hostile_branch.py`, `tests/test_slice_scope_adopted_rules.py`. Not pinned, because the
  slice changes it on purpose: a short-named `master`, `origin/master` or tag `main` counting as a base; *nothing to
  hold* on a slice branch with no base; the pass line ending at *may*. The four suites are run green here
  (`make test TESTS="test_parallel_slices test_slice_scope_root test_slice_scope_hostile_branch test_slice_scope_adopted_rules"`).

**Files:** `delivery/survey/pinned.md` (the only file under `delivery/` this slice changes).

---

## Phase 2: Implementation stage

### T002 — The base is where the branch left the trunk, by full ref name (R1 · AC-S22-1, -2, -3, -11, -12, -21 begun)

- [x] **Rule R1** (f93da6d) — only `refs/heads/<trunk>` and `refs/remotes/origin/<trunk>` answer; within the one name the newest
  base wins; `master` counts only as the recorded name or where no `main` has a ref. **This is the first change to
  the asset, so `changelog.d/slice-scope-base.md` is created in this commit** (Principle VIII).

**RED** (new `tests/test_slice_scope_base.py`, one example at a time, each through the command line; each of e1 to
e5 fails today because the short name resolves to the minted ref and the diff is empty):
- e1 no `ci.branch`, a host-surface change committed, a `master` branch placed at HEAD → still refused. e2 the same
  with `refs/remotes/origin/master` at HEAD. e3 the same with a tag `main` at HEAD.
- e4 `ci.branch: trunk` and a `trunk` branch: the slice's own file → green; a `main` or a `master` minted at HEAD and
  a host change → refused. e5 `ci.branch: master`, trunk `master`, a `main` minted at HEAD → refused.

**Held in this task** (green on arrival, run before the edit and after; they guard it):
- e6 `main` and an older `master` left behind, nothing minted: own file green, host change refused. e7 `main` moved
  locally past `origin/main` and merged into the slice → green, `main`'s files not charged (held by
  `tests/test_parallel_slices.py`, unedited — run it, do not copy it).

**GREEN** — in `assets/toolkit/scripts/check-slice-scope.py`, beside `merge_base()`: `bases_of(name)` (for
`refs/heads/<name>` and `refs/remotes/origin/<name>` where `git rev-parse --verify --quiet <ref>^{commit}` answers,
`git merge-base HEAD <ref>`; returns whether any ref exists and the newest base found, today's `--is-ancestor` walk);
the trunk resolution (recorded `ci.branch` of `ROOT / "project.json"` as the working tree has it, read with the
script's own tolerant `read_json`, else `main` where a ref exists, else `master` where a ref exists, else none); and
`merge_base()` returning a small result (base or `None`, the trunk's name, whether a trunk ref exists) instead of a
bare string — `check()` is its only caller in this script. Only the plain-name read of `ci.branch` is needed here;
T003 makes it tolerant. Create `changelog.d/slice-scope-base.md`, first line `PATCH`, a first honest sentence of what
changes (a slice branch is compared with the trunk's own refs); T009 completes it.

**REFACTOR:** none expected.

**Verify:** `make test TESTS="test_slice_scope_base test_parallel_slices test_slice_scope_root test_slice_scope_hostile_branch test_slice_scope_adopted_rules test_changelog"`
green, then `make lint typecheck check-structure`. `VERSION` untouched. Commit — the fragment is in this commit.

**Files:** `assets/toolkit/scripts/check-slice-scope.py`, `tests/test_slice_scope_base.py` (new),
`changelog.d/slice-scope-base.md` (new).

### T003 — The record's name is read tolerantly and is never a slice's (R2 · AC-S22-4, -5, -6, -7)

- [x] **Rule R2** (604cc7d) — a `ci.branch` that is unusable, a `slice/<id>` name, or without a ref adds nothing; `main`
  answers. Needs T002.

**RED** (in `tests/test_slice_scope_base.py`; e1 to e4 and e7 fail today or after T002 because the recorded name is
taken as it stands):
- e1 the slice commits `ci.branch: slice/S1` → `project.json` refused. e2 the same uncommitted. e3 `ci.branch:
  slice/S9` with a `slice/S9` branch at HEAD → refused.
- e4 the slice sets `ci.branch: nowhere` (no such branch) → base is `main`'s, `project.json` refused, the output says
  `nowhere` was passed over. e7 the base's own record names `develop`, no such ref here, the slice changes only its
  own file → green against `main`, the line names `develop` and `git fetch origin develop`.
- e6 `"refs/heads/main"` reads as `main` (RED if T002 took the name raw).
- **Held:** e5 `ci.branch` of `7`, `["main"]`, `""`, `"  "`, `"-x"`, `"refs/tags/main"` → a verdict against `main`, no
  traceback (D22).

**GREEN** — `usable(value)`: a `str`; stripped; a leading `refs/heads/` taken off; non-empty; not starting with `-`;
not starting with `refs/`; accepted by `git check-ref-format refs/heads/<name>`; not matching `SLICE_BRANCH`;
anything else `None`, never an exception. The recorded name goes through it; a name passed over (unusable, a slice's,
or without a ref) is kept in the `merge_base()` result, and the pass line and refusal header end with the plan's
*Report* wording: `; `ci.branch` names `<name>`, which has no branch here — `git fetch origin <name>` would bring it`
(*is not a branch name* where unusable). The words before the bracket stay.

**REFACTOR:** none expected.

**Verify:** `make test TESTS="test_slice_scope_base test_slice_scope_hostile_branch test_slice_scope_root"` green,
then `make lint typecheck check-structure`. Commit.

**Files:** `assets/toolkit/scripts/check-slice-scope.py`, `tests/test_slice_scope_base.py`.

### T004 — The forge's target is a second candidate, oldest across names (R3 · AC-S22-8, -9, -10)

- [x] **Rule R3** (aad35a9; e4 and e5 were holds, e4's teeth checked) — where `GITHUB_BASE_REF` or `CI_MERGE_REQUEST_TARGET_BRANCH_NAME` is usable and has a ref it is a
  candidate; across two names the older base wins. Needs T003 (`usable`).

**RED** (in `tests/test_slice_scope_base.py`; if the file would pass 350 lines, put R3 in a second new file
`tests/test_slice_scope_target.py` and say so in the commit):
- e1 `GITHUB_BASE_REF=main`, the slice committed `ci.branch: evil`, `refs/remotes/origin/evil` at HEAD → base is
  `main`'s, `project.json` refused. e2 the same through `CI_MERGE_REQUEST_TARGET_BRANCH_NAME`.
- e3 trunk `master`, no record, `GITHUB_BASE_REF=master`, `refs/remotes/origin/main` at HEAD → refused.
- e4 target `feature` cut from `main` and ahead of it, the slice cut from `feature`: the base is `main`'s, so
  `feature`'s own host change is among the refusals.
- **Held:** e5 a target with no ref, or unusable → ignored, the recorded trunk answers (green on arrival).

**GREEN** — the target: the first of the two variables that is set, usable, has a ref, and is not the trunk's own
name. With a base under each name: the one that is an ancestor of the other; where neither is, `git merge-base` of
the two (research R-6); where even that is nothing, the trunk's.

**REFACTOR:** none expected.

**Verify:** `make test TESTS="test_slice_scope_base test_parallel_slices test_slice_scope_hostile_branch"` green
(add `test_slice_scope_target` if made), then `make lint typecheck check-structure`. Commit.

**Files:** `assets/toolkit/scripts/check-slice-scope.py`, `tests/test_slice_scope_base.py` (or
`tests/test_slice_scope_target.py`, new).

### T005 — The line says what was compared (R4 · AC-S22-13)

- [x] **Rule R4** (3f79e4f) — the pass line and the refusal header name the trunk and the base's short commit. Needs T004.

**RED** (in `tests/test_slice_scope_base.py` or the file T004 chose, within 350 lines):
- e1 pass: `check-slice-scope: slice/S1 touches only what one slice may (compared with `main` at <7+ hex>)` — the
  words before the bracket unchanged. e2 refusal header ends `… — compared with `main` at <hex>`. Both fail today;
  the hex is the actual short commit of the base the test reads from git.

**GREEN** — the report in `check()`: the trunk's name and `git rev-parse --short` of the base, in the plan's *Report*
wording; where T003's passed-over suffix applies it follows the bracket. The refusal header gains the
` — compared with ...` ending.

**REFACTOR:** none expected.

**Verify:** `make test TESTS="test_slice_scope_base test_parallel_slices test_slice_scope_root test_slice_scope_hostile_branch test_slice_scope_adopted_rules"`
green, then `make lint typecheck check-structure`. Commit.

**Files:** `assets/toolkit/scripts/check-slice-scope.py`, the T004 test file.

### T006 — A developer's checkout with no usable base fails with what to run (R5 · AC-S22-14, -15, -17, -19)

- [x] **Rule R5** (0fcc763; also: a target with a ref is the base where the trunk has none, D30) — exit 1, one line. Needs T005.

**RED** (new `tests/test_slice_scope_no_base.py`; each fails today with *nothing to hold*, exit 0):
- e1 `git clone --depth 1 --branch slice/S1 file://…` (single branch: no trunk ref) → exit 1, names `main` and
  `git fetch origin main`. e2 a full repository whose only branch is `slice/S1` → the same line.
- e3 shallow clone (`--no-single-branch`) with `origin/main` and no common ancestor in depth → exit 1,
  `git fetch --unshallow origin`. e4 full clone, `main` an unrelated root → exit 1, *a slice branch is cut from
  `main``*, no fetch named. e5 `GITHUB_HEAD_REF=slice/S1` with HEAD attached and no base → exit 1.
- e6 any of these with a regular untracked file at a canonical slot → that finding is printed too (`lost_records()`
  findings are kept in every case).

**GREEN** — `check()`, on a `slice/<id>` branch only: `git symbolic-ref -q HEAD` for detachment and the branch's source
(variable or git) from `current_branch()`, so a developer's checkout is anything that is not (variable name **and**
detached `HEAD`); `git rev-parse --is-shallow-repository` for the shallow answer; the three lines of plan.md *Design*
*No usable base*, through the existing refusal printing (header, indented finding), so exit and stream are today's
refusal. The forge's branch of that table is T007; until then a forge checkout is not yet distinguished.

**REFACTOR:** none expected.

**Verify:** `make test TESTS="test_slice_scope_no_base test_slice_scope_base test_slice_scope_root test_parallel_slices"`
green, then `make lint typecheck check-structure`. Commit.

**Files:** `assets/toolkit/scripts/check-slice-scope.py`, `tests/test_slice_scope_no_base.py` (new).

### T007 — A forge's detached checkout with no base says NOT checked (R6 · AC-S22-16, -18, -19)

- [x] **Rule R6** (ef43c7f; the line says *no trunk history* without naming the trunk — D31's wording names it, restored in T009) — exit 0, stderr, never *nothing to hold*. Needs T006.

**RED** (in `tests/test_slice_scope_no_base.py`):
- e1 detached depth-1 checkout, `GITHUB_HEAD_REF=slice/S1`, no trunk ref → exit 0, stdout empty, stderr has
  `NOT checked` and `fetch-depth: 0`. e2 the same through `CI_COMMIT_REF_NAME`, stderr names `GIT_DEPTH` too.
- **Held:** e3 detached, full history and `origin/main`, `GITHUB_HEAD_REF=slice/S1`, host change → refused as locally.
  e4 branch `feature/x` in a shallow clone, and a detached checkout with no variable → today's *not a `slice/<id>`
  branch — nothing to hold*, exit 0 (the pass-line words unchanged).

**GREEN** — `check()`: where the checkout is a forge's (T006's test) and the base is lacking in any of the three
states, print the plan's *NOT checked* sentence to stderr, nothing to stdout, exit 0; `lost_records()` findings still
printed and still decide the exit.

**REFACTOR:** if `check-slice-scope.py` has grown past comfort, fold the no-base branches into one small function; run
on green.

**Verify:** `make test TESTS="test_slice_scope_no_base test_slice_scope_base test_slice_scope_hostile_branch test_slice_scope_adopted_rules"`
green, then `make lint typecheck check-structure`. Commit.

**Files:** `assets/toolkit/scripts/check-slice-scope.py`, `tests/test_slice_scope_no_base.py`.

### T008 — Nothing else moves (R7 · AC-S22-12, -20) — a held check, no edit

- [x] **Rule R7** (host, at ef43c7f: `git diff 7859512..HEAD` touches only `assets/toolkit/scripts/check-slice-scope.py`, the two new test files and the fragment; `check-migrations.py`, `tests/test_parallel_slices.py` and the three older scope suites are unedited; 102 tests green across the six suites) — no RED and no GREEN: a proof over behaviour T002 to T007 leave alone, so no test is written.
  Run `git diff --stat` over the slice's commits and confirm neither `assets/toolkit/scripts/check-migrations.py` nor
  `tests/test_parallel_slices.py` appears (e1); run
  `make test TESTS="test_parallel_slices test_slice_scope_root test_slice_scope_hostile_branch test_slice_scope_adopted_rules"`
  green (e2). Nothing to commit unless a suite fails — then the fault is T002–T007's, fixed there.

**Files:** none.

### T009 — The release says what it is (R8 · AC-S22-21)

- [x] **Rule R8** (8098aca; with the NOT-checked line naming the trunk, D31) — completes `changelog.d/slice-scope-base.md` (created in T002). First line `PATCH`; states
  separately the local promise (a developer's checkout with no trunk fails with the command to run) and the
  pull-request promise (the forge's target is a second candidate; a detached checkout with no base keeps exit 0 and
  says NOT checked, and `fetch-depth: 0` / `GIT_DEPTH: "0"` is what makes it hold — closed by `S24`); what a project
  sees after `migrate` (the checker is replaced; a slice branch that was passing by a minted base now refuses, and
  the pass line gains `compared with`). Rewrite the script's docstring last paragraph to the same rule in the same
  plain words (plan.md *Design*, *Docstring*).

**RED:** `tests/test_changelog.py` is green with T002's first sentence; the observable proof here is the fragment
itself plus the docstring, so this task has no new failing test — it is the wording task the map asked for.

**Verify:** `make test TESTS="test_changelog test_slice_scope_base test_slice_scope_no_base"` green, then
`make lint typecheck check-structure`. `VERSION` untouched. Commit.

**Files:** `changelog.d/slice-scope-base.md`, `assets/toolkit/scripts/check-slice-scope.py` (docstring only).

---

## Phase 3: Gates (host)

### T010 — Both full gates (host task)

- [ ] **Host task — not delegated.** Run `make verify` and `make -f delivery/Makefile verify` once on the final tip
  after T009; both green. Confirm the diff touches under `delivery/` only `delivery/survey/pinned.md`, `VERSION` is
  `1.5.2.dev0`, and `check-migrations.py` and `tests/test_parallel_slices.py` are unedited. Then the demo from
  [quickstart.md](quickstart.md).

---

## Parallel opportunities

- **Nothing here runs concurrently.** T002 to T007 and T009 all edit
  `assets/toolkit/scripts/check-slice-scope.py`; T002 to T005 also share `tests/test_slice_scope_base.py` (or its
  T004 sibling), T006 and T007 share `tests/test_slice_scope_no_base.py`, and T002 and T009 share
  `changelog.d/slice-scope-base.md`. Two delegates would write one file. They run one at a time, in order, each a
  green committed suite before the next starts.
- **By manifest only:** `tests/test_slice_scope_no_base.py` (R5, R6) is disjoint from `tests/test_slice_scope_base.py`
  (R1 to R4), so a RED for R5 could be drafted while R3 runs. Not worth a second agent: the asset edit still has to
  wait, and a RED written against a tree without R1 to R4 is observed against the wrong baseline. No `[P]`.
- **Host tasks:** T001 precedes T002; T010 runs alone after T009. T008 is a read-only check and may be run by the
  host or the T009 delegate.
- Most delegates at once: one.

## Design review

No screen in this slice

## Convergence
