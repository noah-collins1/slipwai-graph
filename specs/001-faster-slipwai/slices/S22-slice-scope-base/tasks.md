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

- [x] (both green at `27acb52`, 2026-10-03: `make verify` — 1071 tests, *all gates passed*; `make -f delivery/Makefile verify` — *all gates passed*; evidence `demo/gates-27acb52.txt`) **Host task — not delegated.** Run `make verify` and `make -f delivery/Makefile verify` once on the final tip
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

**Converged on pass 2, the bound** (2026-10-03, cruise iteration 5, `drive-converge`, host model, fresh context each
pass) at `a46b2f1`: no `CRITICAL` or `HIGH` open. Pass 1 at `eaa6161` found one `HIGH` (T011), three `MEDIUM`
(T012–T014; T013 a product question, decided as D32) and two `LOW` (T015, T016); all six are closed above, each as
its class — pass 2 re-ran every reproduction and 16 mutants in a disposable clone, 15 killed, the survivor appended
as T017 (`LOW`, Phase 4, tests only). Levels accounted for: the functions (`usable`, `bases_of`, `is_ancestor`,
`target_base`, `target_name`, `older_of`, `merge_base`, `forge_checkout`, `not_checked`, `check`, `main`); their
callers (`merge_base()` ← `check()` ← `main()`; the script is run only from `src/slipwai/project/makefile.py`;
nothing in `assets/` or `src/slipwai/` imports it or parses its output — by text search: this tree has no
`.codegraph/`); the command line (D31's four answers and D32's marker arm, every no-base state, both streams, with
and without a marker — a marker never turns a refusal with a usable base into a pass); the generated project's gate
(a branch that is not `slice/<id>`, `main` itself and a detached checkout with no variable keep *nothing to hold*);
the published contract (fragment `PATCH`, the trunk defined once, the two promises separate, the catch-up true;
docstring matches the code; `VERSION` `1.5.2.dev0` untouched). No screen. The sweep: every name source that reaches
a ref lookup goes through `usable()`; every no-base state × target present, absent, without a ref; every route by
which a checkout is the forge's; the factory's own suites under `CI=true GITHUB_ACTIONS=true` and under hostile
forge variables — green. Constitution (line numbers at `a46b2f1`): **I** — a non-slice branch still exits 0
(`assets/toolkit/scripts/check-slice-scope.py:682–684`), CI's exit stays 0 where there is no base (`:690–691`), the
suites carry their own git identity (`tests/test_slice_scope_no_base.py:20–23`); **III** — no setting, flag or
file; D32 is one function (`check-slice-scope.py:660–667`); **V** — every criterion through the command line
(`tests/test_slice_scope_base.py`, `tests/test_slice_scope_no_base.py`), one capability, the workflow change left to
`S24`; **VIII** — `changelog.d/slice-scope-base.md:1` `PATCH`, catch-up at `:22–29`, `VERSION` unchanged; **X**
(not yet in force; its interim bullet) — the base comes only from full ref names (`:258–259`), the older base wins
across names (`:297–305`), a no-base CI run is said on stderr and never as a pass (`:714–715`); **XIV** — a
developer's no-base checkout is exit 1 with the command to run (`:692–699`), a slice name is never the trunk in any
case (`:315`), a lost record fails on every path. The slice touches no application start-up path. The map: no rung
reached by this slice; `make -f delivery/Makefile check-convergence` green. Not run by either pass: the full gates
(T010, the host's, on the final tip). Four findings outside the slice's diff went to the split's Parking Lot.

### Pass 1 (at eaa6161)

### T011 — The new suites carry their own git identity (HIGH · constitution I, X, XIV: the factory's own gate)

- [x] **HIGH.** (fc929ba) `tests/test_slice_scope_no_base.py` `out()` runs `git commit-tree` with the machine's identity, so
  `test_an_unrelated_trunk_is_not_a_slice_branchs_trunk` and
  `test_every_missing_base_state_of_a_forge_checkout_says_not_checked` ERROR (exit 128) wherever git has no global
  `user.name`/`user.email` — a CI runner; `.github/workflows/verify.yml` configures none, and no other test under
  `tests/` writes a commit outside the fixture's `git()` helper, which passes `-c user.name=t -c user.email=t@local`.

**RED (observed, pass 1):**
`env -i PYTHONPATH=src:tests PATH=/usr/bin:/bin HOME=/tmp python3 -m unittest test_slice_scope_no_base` →
`FAILED (errors=2)`, both at `commit-tree`.

**GREEN names the class:** every git call in `tests/test_slice_scope_base.py` and `tests/test_slice_scope_no_base.py`
that writes an object or a ref carries the identity itself (the fixture's helper, or `-c user.name -c user.email`
in `out()`), and both suites are green under the `env -i … HOME=<a directory with no .gitconfig>` command above.
No production change.

**Files:** `tests/test_slice_scope_no_base.py` (and `tests/test_slice_scope_base.py` only if the sweep finds one).

### T012 — A no-base line never names a branch the state is not about (MEDIUM · R4, R5, R6 · D30 *Depends on D31 only for this*)

- [x] (0012825) **MEDIUM.** In `merge_base()`'s in-loop no-base return (`Base(None, target_name() or name, True, …)`) the
  trunk HAS a ref and shares no history, yet the name handed to `check()` is the forge target's even where that
  target has no ref here. With `main` an unrelated root and `GITHUB_BASE_REF=release` (no `release` ref), a
  developer's checkout prints *slice/S1 shares no history with `release` — a slice branch is cut from `release`*,
  a shallow one *shares no history with `release` at this depth*, and the forge's line says *no `release` history*:
  each sentence is about `main`. D30 gives the target's name only as **the name to fetch** where no candidate has a
  ref. The same in-loop block's other arm (`if base is None and target and target[1]`: trunk ref with no shared
  history, target with a base → held against the target) has no test: mutants replacing either line survive both
  suites.

**RED:** through the command line, in `tests/test_slice_scope_no_base.py`: (1) unrelated `main`, target `release`
with no ref, attached → the line names `main`, not `release`; (2) the same in a `--depth 1 --no-single-branch`
clone → *shares no history with `main` at this depth*; (3) unrelated `main`, target `develop` with a ref and a
shared base → exit 0 `compared with `develop``, and a host change refused.

**GREEN names the class:** every state of the plan's *No usable base* table × {no target, target with a ref,
target without one}: a *shares no history with* line names the ref that was actually compared; the target's name
appears only in a line that tells a person what to fetch.

**Files:** `assets/toolkit/scripts/check-slice-scope.py`, `tests/test_slice_scope_no_base.py`.

### T013 — A push pipeline on a slice branch: decide and say it (MEDIUM · a question for the host, not a code task yet · D31, plan *Constraints* "CI's exit code unchanged in every project")

- [x] (b2c0968, as D32 decided) **MEDIUM — hand-back.** D31 defines the forge checkout as *name from a variable and `HEAD` detached*, and the
  code does exactly that. A GitHub/Gitea **push** run on a `slice/<id>` branch is neither: `actions/checkout`
  leaves `HEAD` attached, depth 1, single branch, and `GITHUB_HEAD_REF` is empty. Reproduced:
  `git clone --depth 1 --branch slice/S1 file://…`, then `GITHUB_ACTIONS=true CI=true python3
  delivery/scripts/check-slice-scope.py` → exit 1, *run `git fetch origin main`* — a command nobody can run on a
  runner. The generated and adopted workflows trigger `push` only on the trunk, so no project as generated meets
  it; a project that widened its own triggers does, and the plan's constraint and the fragment's *it still exits 0*
  (said of the pull-request checkout only) do not cover it. Before `S22`, that run printed *nothing to hold*, exit 0.
  The host decides (a D-entry): (a) leave the exit, and the fragment and docstring say a push pipeline on a slice
  branch is a developer's checkout and fails, with `fetch-depth: 0` as the fix there too; or (b) the forge answer
  also covers a CI checkout with no pull-request variable. Then a test pins whichever it is.

**Files (after the decision):** `changelog.d/slice-scope-base.md`, the docstring, and for (b)
`assets/toolkit/scripts/check-slice-scope.py`, `tests/test_slice_scope_no_base.py`.

**Decided (D32, 2026-10-03):** option (b). T013 is a code task: `forge_checkout()` is also true where `GITHUB_ACTIONS`,
`GITLAB_CI` or `CI` is non-empty; every no-base state there answers *NOT checked*, exit 0, stderr; with a usable base
the slice is held as locally; a lost record still fails; AC-S22-22 to AC-S22-24 are its examples; every test that
asserts a developer's exit 1 runs the gate with the three markers cleared (`run_gate` in
`tests/test_slice_scope_base.py`, and the runner in `tests/test_slice_scope_no_base.py`); the docstring's last
paragraph and the fragment's catch-up say *a CI run*, not only *a pull-request checkout*. **GREEN names the class:**
every route by which a checkout is called the forge's, in every no-base state, on both streams.

### T014 — A slice name in another case is still a slice name (MEDIUM · R2, AC-S22-4 · not reproducible on this platform)

- [x] (6a0d9a2) **MEDIUM.** `usable()` refuses a `slice/<id>` name by `SLICE_BRANCH`, which is case-sensitive; on a
  case-insensitive filesystem (macOS, Windows) with loose refs, `refs/heads/Slice/S1` resolves to the slice's own
  branch, so a committed `ci.branch: Slice/S1` would make the base HEAD and the `project.json` edit unseen — the
  door D30 closes. On Linux the name has no ref and `main` answers (run in pass 1: refused, *`Slice/S1` … has no
  branch here*), so this is read from the code, not observed.

**RED:** a command-line test that records `Slice/S1` (and `SLICE/s1`) and, so that it bites on every platform,
creates the loose ref file `refs/heads/Slice/S1` at HEAD on Linux: `project.json` is refused.

**GREEN names the class:** every name source that reaches a ref lookup — `ci.branch`, `GITHUB_BASE_REF`,
`CI_MERGE_REQUEST_TARGET_BRANCH_NAME` — refuses a name that is the checked branch, or any `slice/<id>`, compared
without regard to case.

**Files:** `assets/toolkit/scripts/check-slice-scope.py`, `tests/test_slice_scope_base.py`.

### T015 — Teeth for the two unpinned arms of name and base selection (LOW)

- [x] (71220bf; both mutants now die) **LOW.** Mutants that survive both suites (pass 1, 21 run): `usable()` without `git check-ref-format`
  (`a..b`, `a b` then read *has no branch here* rather than *is not a branch name* — same verdict, wrong sentence);
  `older_of()` without its `git merge-base first second` fallback (two bases neither an ancestor of the other —
  the plan's *Design* states it, the map has no example). One command-line test each; no production change expected.

**Files:** `tests/test_slice_scope_base.py`.

### T016 — The fragment's first paragraph does not contradict its catch-up (LOW · R8, AC-S22-21)

- [x] (01d9fd3; rewritten once, with D32's CI run) **LOW.** `changelog.d/slice-scope-base.md` paragraph 1 ends *This asks nothing of a repository already
  generated*, and the **Catch-up** paragraph then names two things a project will see, one of them a new local
  failure; paragraphs 1 and 2 also each define the trunk. Say once what the trunk is, and replace *asks nothing*
  with what is true: `migrate` carries the script, and a checkout with no trunk to compare with now fails locally.

**Files:** `changelog.d/slice-scope-base.md`.

### Pass 2 (at a46b2f1)

### T017 — Teeth for *within one name the newer base wins* when the newer one is `origin`'s (LOW · R1, AC-S22-11 · Phase 4, does not re-open the loop)

- [x] (53acc69, with T022) **LOW.** In `bases_of()` (`assets/toolkit/scripts/check-slice-scope.py` lines 267–271) the loop that picks the
  newer of the local and the `origin` base can be replaced by *keep the first found* (the local one) and both suites
  stay green (pass 2, mutant 16 of 16; the other 15 die). The suites pin the direction where local `main` is ahead
  of `origin/main`; nothing pins the inverse — `origin/main` fetched ahead of a local `main` that was not pulled,
  and merged into the slice. The code is right there today (read, and the order of `bases` is local then origin);
  broken, the slice would be charged with `main`'s own files — a false refusal, never a false pass, which is why
  this is LOW.

**RED:** one command-line test in `tests/test_slice_scope_base.py`: `refs/remotes/origin/main` one commit (a host
file, `Makefile`) ahead of `refs/heads/main`, that commit merged into `slice/S1` → exit 0 and the pass line reads
`compared with `main` at <origin/main's short commit>`. It must fail under the mutant above.

**GREEN names the class:** both orders of the two refs of one name — local ahead, `origin` ahead — each with a test
that dies when the choice is removed. No production change expected.

**Files:** `tests/test_slice_scope_base.py`.

## Phase 4: Gaps after converge (2026-10-03; `drive-gaps`, read-only, at `2b43255`; triaged as D33 and D34)

Eleven findings: one `HIGH`, three `MEDIUM`, seven `LOW`; the quickstart's steps ran as written. T017 (converge pass
2) rides with T022. One task per commit, in this order — all but T022 and T023 edit the script.

### T018 — The fetch the gate prints writes the ref it says is missing (`HIGH` G1 · AC-S22-26, D34)

- [x] (6cc28a9) **RED:** in a `--single-branch` clone (full, and `--depth 1`) the test reads the command out of the failure
  line, runs it, and runs the gate again: today the same line comes back. The same for the passed-over note's fetch.
  **GREEN names the class:** every `git fetch` the script prints — the no-trunk line and the passed-over note — is
  `git fetch origin <name>:refs/remotes/origin/<name>`; the `--unshallow` line is already true and is run by the
  shallow example to its verdict.

**Files:** `assets/toolkit/scripts/check-slice-scope.py`, `tests/test_slice_scope_no_base.py`,
`tests/test_slice_scope_base.py` (the constant or assertions that quote the old command only).

### T019 — `HEAD` is never a trunk's name, and a symbolic ref is never a trunk ref (`MEDIUM` G2 · AC-S22-27, D34)

- [x] (6b1e112; each part dies under its own mutant) **RED:** a slice commits `ci.branch: HEAD`; in a plain clone of a repository whose own `HEAD` is on the slice,
  the gate passes today with *compared with `HEAD`*. **GREEN names the class:** `usable()` refuses `HEAD` in any
  case from every source (`ci.branch`, both target variables); `bases_of()` skips a candidate ref that
  `git symbolic-ref -q` resolves.

**Files:** `assets/toolkit/scripts/check-slice-scope.py`, `tests/test_slice_scope_base.py`.

### T020 — An unrecorded `master` trunk beside a stale `main` is told what to record (`MEDIUM` G4 · AC-S22-25, D33)

- [x] (937239b; follow-up below) **RED:** one test per clause of AC-S22-25. **GREEN:** the clause joins the existing passed-over words in
  `merge_base()` where nothing usable is recorded, the trunk chosen is `main`, `master` has a ref and `master`'s
  base is strictly newer than `main`'s; no base and no exit changes. Teeth: without *strictly newer*, AC-S22-12's
  output changes.

**Files:** `assets/toolkit/scripts/check-slice-scope.py`, `tests/test_slice_scope_base.py` (or a new
`tests/test_slice_scope_report.py` importing its helpers, if the file would pass 350 lines).

**Follow-up (host, reading 937239b's report):** the clause is printed where the chosen trunk is `main` and `main` is
not the recorded name — so a record naming a valid branch with no ref here (`develop`) also gets *`project.json`
records no trunk*, which is false there. D33 says *where `ci.branch` records nothing usable*. Closed with T022's
delegate as its own RED-GREEN commit.

- [x] (78a22ea) The clause appears only where `ci.branch` records nothing usable (absent, `null`, blank, not a string, not a
  branch name, a slice's name); a usable recorded name with no ref keeps its own passed-over sentence and no clause.

### T021 — What the gate prints is true where it is printed (`LOW` G5, G6, G7, G8 · AC-S22-28, D34)

- [x] (4f5cf6c; RED not observed before the fix — the script was edited first; teeth shown afterwards by four mutants on the committed script) **RED:** one test per clause of AC-S22-28. **GREEN names the class:** every sentence on the report line, the
  refusal header and the no-base lines, in every state they are printed in — the forge's output carries no fetch;
  a slice-shaped record has its own sentence; a non-string record is said to be passed over; a developer's no-base
  failure prints as its own one line (`check-slice-scope: slice/<id> has no …`), exit 1, stderr, with the
  *reaches outside* header only above refused paths and lost records. Existing tests that pinned the old header on a
  no-base failure (`fails_with` in `tests/test_slice_scope_no_base.py`) are rewritten to the decided shape.

**Files:** `assets/toolkit/scripts/check-slice-scope.py`, `tests/test_slice_scope_no_base.py`,
`tests/test_slice_scope_base.py` (or `tests/test_slice_scope_report.py`).

### T022 — Every clause of AC-S22-1, -2, -11, -19 and D32's *non-empty* is held (`LOW` T017, G10, G11 · tests only)

- [x] (53acc69; six mutants, all die) No production change expected; each assertion shown to have teeth by a one-line mutation restored with
  `git checkout --`. T017: `origin/main` ahead of a local `main` and merged into the slice. G10: the header names
  `main` in AC-S22-1's three examples; the pass line names `trunk` where `trunk` and `main` are different commits;
  a lost record in the unrelated-trunk state, attached and under a marker. G11: `CI=false` is a marker.

**Files:** `tests/test_slice_scope_base.py`, `tests/test_slice_scope_no_base.py` (or the new report file).

### T023 — The fragment and the docstring say all of it (`MEDIUM` G3 · AC-S22-21, D33, D34) — last

- [x] (420909e) `changelog.d/slice-scope-base.md`: the catch-up gains (1) a trunk named neither `main` nor `master`, recorded
  in `ci.branch`, is compared with for the first time — slice branches in flight there are now held; (2) D33's
  sentence for an unrecorded `master` trunk beside a stale `main`; (3) the fetch as T018 made it. The module
  docstring's last paragraphs follow T018–T021 (the fetch form; `HEAD`; the clause; the one-line failure; *the pass
  line and the refusal header end `compared with …`* made true). `tests/test_changelog.py` green.

**Files:** `changelog.d/slice-scope-base.md`, `assets/toolkit/scripts/check-slice-scope.py` (docstring only).

## Phase 4: Adversary findings (2026-10-03; two seams at `bc919d6`; `adversary-log.md` `## S22`; triaged as D35)

One task per commit, in order; all edit the script. New tests go in new files (`tests/test_slice_scope_base.py`,
`tests/test_slice_scope_no_base.py` are full; `tests/test_slice_scope_report.py` is at 278 of 350 lines).

### T024 — A name that cannot be compared with is not a base and not the end of the search (`HIGH` B1 · `MEDIUM` A1 · AC-S22-29)

- [x] (9b41d68) **RED:** B1's and A1's reproductions from the log, through the command line, each failing today. **GREEN names
  the class:** every candidate name — recorded, `main`, `master`, the target — in the state *has a ref, shares no
  history*: a trunk candidate is passed over for the next and said so; a target is no base at all. The existing
  no-base examples (an unrelated `main` and nothing else) keep their answers.

**Files:** `assets/toolkit/scripts/check-slice-scope.py`, `tests/test_slice_scope_hostile_base.py` (new).

### T025 — The gate ends in a verdict whatever it is given (`MEDIUM` A2, A3, B4 · AC-S22-30)

- [x] (3037ae5; cap 8 MiB; `project.json` as a symlink was already a verdict — a hold) **RED:** a NUL and a lone surrogate in `ci.branch`; `project.json` and `model.yaml` as symlinks to `/dev/zero`
  and to a FIFO (the test bounds each run with a timeout); `GIT_DIR` pointing nowhere. **GREEN names the class:**
  every `git()` call survives any `ValueError`; every working-tree read goes through one guard (regular file, size
  cap); where `git rev-parse --git-dir` fails the gate says so with git's first line and exits 0, as before the slice.

**Files:** `assets/toolkit/scripts/check-slice-scope.py`, `tests/test_slice_scope_hostile_base.py`.

### T026 — A comparison that could not run is *could not compare* (`HIGH` B2 · AC-S22-31)

- [x] (d07148d; B2's own treeless clone, offline; `ls-files --others` failing goes through the same guard, untested — no offline way to make it fail) **RED:** a base, and a `git diff` that fails (B2's treeless clone with its remote gone, or the smallest
  honest stand-in the test can build offline): today the pass line. **GREEN names the class:** every git call
  between the base and the verdict whose failure would read as *no changes* (`diff --name-status`, `ls-files
  --others`, `diff --numstat`, `show <base>:…` where a failure is not *absent*): developer exit 1, one line;
  forge NOT checked.

**Files:** `assets/toolkit/scripts/check-slice-scope.py`, `tests/test_slice_scope_hostile_base.py`.

### T027 — What the gate prints is safe to paste and true (`MEDIUM` B3 · `LOW` A5, B5, A4 · the hand's notes 2, 3 · AC-S22-32)

- [x] (f8a01ac; a hostile name is still named, cleaned, as the missing branch — never inside a command) **RED:** one test per clause of AC-S22-32, B3's with the printed text handed to `sh -c` in a scratch
  directory and a sentinel file asserted absent. **GREEN names the class:** every place the script prints a name it
  did not choose or a command — `fetch_command()`, the passed-over words, the no-base lines, the NOT-checked line,
  the report line.

**Files:** `assets/toolkit/scripts/check-slice-scope.py`, `tests/test_slice_scope_printed.py` (new).

### T028 — The fragment and the docstring follow (AC-S22-21) — last

- [x] (cec171b) `changelog.d/slice-scope-base.md` and the module docstring say what T024–T027 changed for a reader: when a
  fetch command is and is not printed; that a comparison that could not run fails locally and is NOT checked in
  CI; that a recorded trunk sharing no history is passed over for `main`.

**Files:** `changelog.d/slice-scope-base.md`, `assets/toolkit/scripts/check-slice-scope.py` (docstring only).

