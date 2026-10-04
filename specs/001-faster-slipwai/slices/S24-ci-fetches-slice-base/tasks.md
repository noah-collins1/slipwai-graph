# Tasks: S24-ci-fetches-slice-base — a slice pull request's CI holds the slice to its scope instead of saying it could not look

**Input**: [plan.md](plan.md) (*The example map* R1–R7 is what the tasks cut on; *Design*; *Pin*; *Project
Structure*), [research.md](research.md), [data-model.md](data-model.md), [quickstart.md](quickstart.md); acceptance
criteria AC-S24-1 … AC-S24-13 in `specs/001-faster-slipwai/spec.md` under `### S24-ci-fetches-slice-base`;
decisions D12, D31, D32, D35, D54, D82, D84 in `specs/001-faster-slipwai/decisions.md`. No `examples.md`: a method
slice with no screen and no event model.

**Branch**: `adopt-method` (D12). No `slice/` branch, no push, no claim. One commit per task.

**Delegation** (`.specify/drive.json`: `delegate: story`, `cycle: rule`): these tasks carry no user-story tag, so
they are delegated **per rule**, one delegate per implementation task, each its own RED-GREEN-REFACTOR increment and
its own commit. The "Files" line of a task is its manifest: the only files that delegate may write. Nobody but the
host writes `tasks.md`. A delegate that finds it needs a file outside its manifest — a test elsewhere that pins the
text it changes, a page that still says the old thing (AC-S24-12) — stops and names the file; the host adds it.

**Constraints that hold for every task** (plan.md *Constraints*): `PATCH` — no setting, flag or file added to a
generated project; `check-migrations.py` and both `check-flags.py` do not change by a byte; nothing under
`delivery/scripts/`, `tools/`, the `Makefile`, this repository's own CI or hook settings changes (the installed
`delivery/scripts/check-slice-scope.py` and `.github/workflows/verify-delivery.yml` here arrive by `slipwai migrate`,
a person's — D9); `VERSION` stays `1.6.0.dev0`; every file under `src/` and `tests/` stays within the 350 lines
`make check-structure` holds (`tests/test_slice_scope_no_base.py` is at 343: what R4 adds goes in a new file, and an
edit to that file may not grow it past 350); every `read_text`/`open` in a toolkit script names `encoding="utf-8"`;
standard library only, no mocking framework — a fake is a class or function in the test tree, and the checkouts are
built with git itself. Added for this slice:

- A test that runs a script's command line builds its environment with `CI`, `GITHUB_ACTIONS`, `GITLAB_CI`,
  `GITHUB_HEAD_REF`, `GITHUB_BASE_REF`, `CI_COMMIT_REF_NAME` and `CI_MERGE_REQUEST_TARGET_BRANCH_NAME` **removed**
  unless the test sets that one, so the suite is the same on a runner that sets `CI=true` and on a laptop (AC-S24-13).
- A test that loads a toolkit script as a module sets `sys.dont_write_bytecode = True` first.
- Commit by path — `git commit -m … -- <the task's files>` — never `git add -A`, never `git commit -a`. A new file is
  `git add`ed by its exact path first.
- Before changing a generator, search `tests/` for helpers that rebuild an old workflow or Makefile by regex and for
  tests pinning the whole text of a generated workflow (`grep -rn "verify.yml\|verify-delivery\|checkout@v6" tests`);
  the sweep at planning found none that pins a whole file (`tests/test_ci_caches.py` asserts fragments;
  `tests/test_ratchet.py:236–250` and `tests/test_adopt.py:166,295` use `assertIn`/`assertNotIn`), and the delegate
  repeats it and reports any it finds rather than editing it.

**Quick test and pre-commit.** The quick test of an increment is `make test TESTS="<modules>"`, the modules each task
names. Before each commit run `make lint typecheck check-structure` as well.

**Versioning, on every commit** (`AGENTS.md`, *Versioning is not optional*): a commit that changes `src/slipwai/`,
`assets/` or the fragment says `Level PATCH; VERSION is not raised because it already carries the MINOR (1.6.0.dev0)
the number needed and the fragment claims PATCH` and names the reason (the same answers, generated better). A commit
that changes only `tests/` says it reaches no user and so does not raise the number. `VERSION` and anything under
`release/` are never edited. **The fragment `changelog.d/ci-fetches-slice-base.md` lands in T002**, the first commit
that changes a user-visible tree (`src/slipwai/project/ci_workflows.py`); the host commits T002 before T003 and T004,
whatever order the delegates finish in. T002 writes it whole as a first draft (the four things, both refusals, the
catch-up, the cost of the fetch); T008 completes the wording against what T003 and T004 landed. T003 and T004 do not
touch it.

**Observing a RED, and the "seen failing" rule.** Each RED is observed failing for its stated reason before the
production edit. A hold is written as a hold, saying so in the test's name or comment, and is **seen to have teeth**
before it is committed: invert one assertion, or remove the history the fixture gives, and observe the failure; then
restore. The sanctioned route for a production file is change it, run the test, restore with
`git checkout -- <exact path>`; confirm `git status` shows only the task's own files. The tree is clean of the
reversal on every exit path, including a stop.

**The Pin stage** (`/characterise`, plan.md *Pin*) is a host task, T001, before any implementation.

## Format: `[ID] [P?] Description` — each task is one increment, one commit

`[P]` marks a task whose files are disjoint from every sibling's it could run beside; see *Parallel opportunities*.

---

## Phase 1: Pin (host)

### T001 — Pin how the three files check the code out, and what the check answers in a forge's checkout today (host task)

- [x] **Host task — not delegated.** The host appends rows to `delivery/survey/pinned.md` before T002 and commits them
  alone: (1) what `check-slice-scope` answers in a forge's checkout with no base — already pinned by
  `tests/test_slice_scope_no_base.py` and `tests/test_slice_scope_hostile_base.py` (the 2026-10-03 row), named, not
  re-pinned; (2) how the generated `verify` job, the adopted `verify` job and the GitLab `verify-delivery` job check
  the code out today (a bare `actions/checkout@v6`, no `variables:`) — `/characterise` records it if no test holds it.
  Not pinned, because the slice changes it on purpose: the two answers above. Pinned tests run green here. The commit
  says no user-visible tree changed, so the number is not raised.

**Files:** `delivery/survey/pinned.md` (the only file under `delivery/` this slice changes).

---

## Phase 2: Implementation stage

Each implementation task starts from the green committed suite at the commit that closes T001. T002, T003, T004 and
T005 are disjoint by manifest and may run together (*Parallel opportunities*); T006 follows T005; T007 follows T004;
T008 follows T002, T003 and T004.

### T002 — [P] A generated project's `verify` job fetches history, and nothing else does (R1 · AC-S24-1)

- [x] **Rule R1.** **The first commit that changes a user-visible tree, so the fragment lands in it.**

**RED** (new `tests/test_ci_fetch_generated.py`; generate through the same entry points the neighbouring generator
tests use, and read the files back; never edit an existing test). Each fails today because the `verify` job's checkout
is a bare `actions/checkout@v6`:
- e1 the `verify` job's `actions/checkout@v6` step in `.github/workflows/verify.yml` carries `with:` and
  `fetch-depth: 0`, the line has no `${{`, and the comment above it names `check-slice-scope`, `check-migrations`
  and `check-flags`.
- e2 a project with an integration job: `CONTAINER_CHECKOUT` still fetches `--depth 1` and neither it nor the
  integration job's checkout carries `fetch-depth`. **A hold — green today; seen to have teeth by writing the key
  into `CONTAINER_CHECKOUT` in the working tree and watching it fail, then restoring.**
- e3 the event-model workflow, the deploy workflows and the `ux-gates` workflow are byte for byte what the commit
  before the slice generates. **A hold, written against a recorded expectation: compare with the text generated from
  `git show <T001 commit>:<file>` of the three generators, loaded to a temporary directory, or assert on the one
  property that matters — none of those files contains `fetch-depth` — if the three generators cannot be loaded from
  an old commit without an edit. Teeth: add the key to one in the working tree, observe the failure, restore.**
- **The sweep that closes the class:** the examples run over every backend and every target the catalog offers (the
  loop the neighbouring generator tests already make), so no combination keeps a bare checkout on its `verify` job and
  none gains the key on another job.

**GREEN** — in `workflow()` (`src/slipwai/project/ci_workflows.py`) the `verify` job's step becomes the one in plan.md
*Design* R1, with its two-line comment; nothing else in the module changes. Add `changelog.d/ci-fetches-slice-base.md`,
first line `PATCH`, written whole: the `verify` job now fetches full history, a slice pull request is held to its scope
in CI, *NOT checked* in CI is a failure, and `check-migrations` and `check-flags` now hold their *new in this change*
rules on every pull request, naming both refusals (an expand and its contract together; a flag seeded anything but
`off`), what a maintainer does about a red pull request (land the expand first; seed `off`), the catch-up (a workflow a
project took over, or a pipeline of its own that sets a CI marker on a shallow clone, is not rewritten by `migrate`:
add `fetch-depth: 0`, on GitLab `GIT_DEPTH: "0"`), and that a long history pays the full fetch on that one job.

**REFACTOR:** none expected.

**Verify:** `make test TESTS="test_ci_fetch_generated test_ci_caches test_pins test_renovate test_changelog"` green,
then `make lint typecheck check-structure`. `VERSION` untouched. Commit by path, level line as above.

**Files:** `src/slipwai/project/ci_workflows.py`, `tests/test_ci_fetch_generated.py` (new),
`changelog.d/ci-fetches-slice-base.md` (new).

### T003 — [P] The adopted gate fetches history, on both forges (R2 · AC-S24-2, -3)

- [x] **Rule R2.** Disjoint from T002 and T004 by manifest; its commit lands after T002's.

**RED** (new `tests/test_ci_fetch_adopted.py`; adopt a temporary git repository through the CLI, with the helpers
`tests/test_adopt.py` already has — `repository()` and `slipwai()` — or a local copy; no import of another test
module's test class). Each fails today:
- e1 an adopted repository on GitHub: the `verify` job of `.github/workflows/verify-delivery.yml` carries
  `fetch-depth: 0` under its comment; with a `smoke` command recorded the `smoke` job's checkout carries none.
  **The `smoke` half is a hold — green today; teeth by writing the key into `smoke_job()` in the working tree,
  observing the failure, restoring.**
- e2 an adopted repository on GitLab: `delivery/ci/verify-delivery.gitlab-ci.yml`'s `verify-delivery` carries
  `variables:` with `GIT_DEPTH: "0"` after `stage: test`; `smoke-delivery` has no `variables:`; the file has no
  `rules:`. The `smoke-delivery` and no-`rules:` halves are holds, with teeth seen the same way.
- **The sweep that closes the class:** both forges, with and without a `smoke` command recorded (four states), and
  Gitea/Forgejo, which take the GitHub file (`tests/test_adopt_facts.py:103`); and the file `delivery_workflow()`
  writes when a refresh regenerates it equals the one `adopt` first wrote.

**GREEN** — in `src/slipwai/project/adopted_ci.py`: the same step and comment on `delivery_workflow()`'s `verify` job;
`gitlab_job()`'s `verify-delivery` gains the `variables:` block of plan.md *Design* R2. `smoke_job()` and
`smoke-delivery` are not edited. No `rules:`.

**REFACTOR:** if the two forges' comments repeat a sentence, one constant in the module, on green.

**Verify:** `make test TESTS="test_ci_fetch_adopted test_adopt test_adopt_facts test_ratchet test_pin"` green, then
`make lint typecheck check-structure`. Commit by path; level line (PATCH, `VERSION` not raised), the fragment being
T002's.

**Files:** `src/slipwai/project/adopted_ci.py`, `tests/test_ci_fetch_adopted.py` (new).

### T004 — [P] In a forge's checkout, no base is a failure (R4, with R6 and the docstring of R7 · AC-S24-5, -6, -7, -9, -12, -13)

- [x] **Rule R4.** R6 (a developer's checkout is untouched; the suite is green under CI's markers) is **folded in
  here**: its proofs are behaviour this task changes and guards, and a task of their own would write tests that pass
  the moment they are written. The docstring of `check-slice-scope.py` (R7e3) is folded in because it is the same
  file as the change. Disjoint from T002, T003 and T005 by manifest.

**RED** — first the two existing suites. In `tests/test_slice_scope_no_base.py` and
`tests/test_slice_scope_hostile_base.py` change **only** the assertions that say exit 0 (and *NOT checked*, stderr
only) under a forge marker or the detached route to exit 1, still with empty stdout and the same line; do not touch
a test that clears the markers (a developer's answer, AC-S22-24). Run them: they fail, for the reason that the script
still returns exit 0. The edit may not grow `test_slice_scope_no_base.py` past 350 lines; if it would, move the
changed test into the new file below, byte for byte but for the assertion.

Then new `tests/test_slice_scope_forge_nobase.py` (a `SliceScopeFixtures` subclass from
`tests/test_slice_scope_root.py`; **it builds its depth-1 and detached checkouts with its own small local helper and
does not use `tests/forge_checkout.py`**, so it needs nothing from T005). Examples e1–e3 and e5 fail today (exit 0):
- e1 a depth-1 single-branch clone of `slice/S1` with `GITHUB_ACTIONS=true`, separately `GITLAB_CI=true`, separately
  `CI=true` → exit 1, stdout empty, one stderr line with *NOT checked*, `` `main` ``, `fetch-depth: 0`,
  `GIT_DEPTH: "0"` and *a full clone with the trunk's branch fetched*; no `git fetch`, no *nothing to hold*.
- e2 the detached pull-request route (the name in `GITHUB_HEAD_REF`, then `CI_COMMIT_REF_NAME`, no marker) at depth 1
  → the same.
- e3 a trunk ref with no common ancestor at this depth, an unrelated trunk, and a pull-request target with no history
  in common (`GITHUB_BASE_REF`, `CI_MERGE_REQUEST_TARGET_BRANCH_NAME`), each under a marker → the same, with the
  passed-over words (AC-S22-28, AC-S22-32) kept.
- e5 a base exists and `git diff` fails, under a marker → exit 1 with *NOT checked — git could not compare*. The
  failure is made with git, not a fake: the `CouldNotCompare` fixture the existing suites use, or a corrupt object.
- **Holds, written as holds and seen to have teeth** — e4 a lost record at a canonical slot under a marker with no
  base → exit 1 with the record and the line (teeth: turn the record's assertion over); e6 a checkout git cannot
  read, under a marker → exit 0 and the *could not read* line (teeth: expect exit 1); e7 a branch that is not
  `slice/<id>` under a marker, with history and without → *nothing to hold*, exit 0 (teeth: expect the line). Also a
  hold for AC-S24-7's last clause: with a usable base the slice is held exactly as on a developer's machine, with the
  marker set and without.
- **The sweep that closes the class:** the table of no-base states × the forge's two routes × the markers
  (`GITHUB_ACTIONS`, `GITLAB_CI`, `CI`, and each branch-name variable with `HEAD` detached), looped so every cell is
  asserted — the same assertions as e1 in each — not three hand-picked ones; and both forges' variables.

**GREEN** — in `assets/toolkit/scripts/check-slice-scope.py`: the two returns of `check()` taken where
`forge_checkout()` is true — no base, and `CouldNotCompare` — return `True` for *failed* where they return `False`;
`not_checked()` keeps its sentence and adds, after the two keys, *on any other CI, a full clone with the trunk's
branch fetched*, and its docstring stops saying *not a pass, not a failure*; the `problem` arm is not edited. The
module docstring's paragraph on a CI run says exit 1 and drops *because that checkout is depth 1* for *because that
checkout has no history to compare with*. Search `assets/`, `src/slipwai/` and `docs/` for *NOT checked*,
`fetch-depth` and *depth 1* and report any other page that still says the old answer (AC-S24-12); do not edit it.
The docstrings of `check-migrations.py` and `check-flags.py` stand.

**REFACTOR:** none expected.

**Verify (R6 folded in):** `make test TESTS="test_slice_scope_forge_nobase test_slice_scope_no_base
test_slice_scope_hostile_base test_slice_scope_base test_slice_scope_root test_slice_scope_report
test_slice_scope_printed test_slice_scope_hostile_branch test_slice_scope_adopted_rules"` green; then **again with
`CI=true GITHUB_ACTIONS=true` exported** — green, which is R6e2 and AC-S24-13; then `git diff` over this task shows no
assertion changed in a test that clears the markers (R6e1, AC-S24-9). Then `make lint typecheck check-structure`.
Commit by path; level line (PATCH, `VERSION` not raised, the same answers generated better), the fragment being
T002's.

**Files:** `assets/toolkit/scripts/check-slice-scope.py`, `tests/test_slice_scope_forge_nobase.py` (new),
`tests/test_slice_scope_no_base.py`, `tests/test_slice_scope_hostile_base.py`.

### T005 — [P] On the checkout the workflow now makes, a slice is held (R3, and the helper · AC-S24-4)

- [x] **Rule R3.** This task **owns `tests/forge_checkout.py`** — it is the first and only task to write it; T006 uses
  it and comes after. A hold: every example is green today, since the slice changes no line R3 reads. Disjoint from
  T002, T003 and T004 by manifest. The plan's `tests/test_slice_scope_forge.py` held R3 and R4 together; it is split
  — R3 here as `tests/test_slice_scope_forge.py`, R4's examples in T004's `tests/test_slice_scope_forge_nobase.py` —
  so the two tasks share no file.

**Tests** (new `tests/forge_checkout.py`, new `tests/test_slice_scope_forge.py`, each ≤ 350 lines). The helper builds
the pull-request checkout with git as plan.md *Design* describes: from an origin holding `main` and a head branch,
the merge of the head into `main` under `refs/pull/1/merge`; a `file://` clone; fetch
`+refs/heads/*:refs/remotes/origin/*` and the merge ref; check the merge commit out detached; delete the local branch
the clone made, so the only refs are `refs/remotes/origin/*`. The depth-1 form fetches only the merge ref at
`--depth 1`. It returns the path; the caller supplies the variables; `sys.dont_write_bytecode` is not needed (it loads
no script). Then:
- e1 a host-surface change on `slice/S1`, the pull-request checkout with GitHub's variables (`GITHUB_ACTIONS`, `CI`,
  `GITHUB_HEAD_REF=slice/S1`, `GITHUB_BASE_REF=main`) → exit 1 naming the path, *compared with `main` at*.
- e2 the same with GitLab's (`GITLAB_CI`, `CI_COMMIT_REF_NAME`, `CI_MERGE_REQUEST_TARGET_BRANCH_NAME`).
- e3 a slice inside its scope → exit 0 with the *compared with* line, on both.
- The helper's own shape is asserted once, so a later change cannot quietly turn it into a full clone: the only refs
  are `refs/remotes/origin/*`, `HEAD` is detached, `main` is among the remote refs at full history and absent at
  depth 1.
- **The sweep that closes the class:** each of e1–e3 on both forges' variables and on the route with no marker (the
  branch name alone with `HEAD` detached), with and without `GITHUB_BASE_REF`/the target given.

All are holds, written as holds in the test names. **Teeth, seen before commit:** invert each assertion in turn; and
remove the history from the fixture (use the depth-1 form) and observe the e1 assertion fail (the script then says
*NOT checked*, whichever of T004's behaviours is in the tree), restore.

**GREEN:** none in `src/` or `assets/`. If a hold fails, stop and report: the checkout the plan assumes is not what
the script reads.

**REFACTOR:** none.

**Verify:** `make test TESTS="test_slice_scope_forge"` green, then `make lint typecheck check-structure`. Commit by
path; level line (tests only: reaches no user, number not raised).

**Files:** `tests/forge_checkout.py` (new), `tests/test_slice_scope_forge.py` (new).

### T006 — [P] With history, the two other gates answer as on a full clone (R5 · AC-S24-8)

- [x] **Rule R5.** **Uses `tests/forge_checkout.py`, so it needs T005 committed first.** All holds: the slice changes
  no line of the three scripts. Disjoint from T002, T003 and T004 by manifest (it runs the shipped scripts and does
  not write them), so it may run beside them once T005 is in.

**Tests** (new `tests/test_ci_history_gates.py`, the shipped `check-migrations.py` and both targets' `check-flags.py`
run through their command lines in a project generated into a temporary directory, with `sys.dont_write_bytecode`
where a script is loaded as a module):
- e1 a pull request from `feature/x` carrying an expand and its contract together → `check-migrations` exits 1 on the
  pull-request checkout, 0 on the depth-1 checkout with no trunk ref.
- e2 a pull request declaring a flag seeded `on` → `check-flags` (aws; azure) exits 1 on the pull-request checkout,
  0 at depth 1.
- e3 the same commits pushed to the trunk → both exit 0 at either depth.
- e4 on the pull-request checkout from `feature/x`, `check-slice-scope` says *nothing to hold*, exit 0.
- **The sweep that closes the class:** every target that ships a `check-flags.py` (aws and azure — the delegate lists
  `assets/targets/*/scripts/` and covers each), and both forges' variables, for e1–e3.

**Teeth:** all four are holds written as holds; each seen with its fixture's history removed (the depth-1 form where
the test expects exit 1) and with one assertion inverted, observed failing, restored; the tree clean afterwards.
`git diff` over this task shows none of the three scripts changed.

**GREEN:** none. If a hold fails, stop and report; do not edit a script.

**REFACTOR:** none.

**Verify:** `make test TESTS="test_ci_history_gates test_slice_scope_forge"` green, then
`make lint typecheck check-structure`. Commit by path; level line (tests only).

**Files:** `tests/test_ci_history_gates.py` (new). Reads `tests/forge_checkout.py` (T005's), writes nothing else.

### T007 — The sweep for the old words is finished (R7e3, AC-S24-12) — host decision, delegate only if T004 reports a page

- [x] *(ticked on T004's report: its search of `docs/`, `assets/` and `src/slipwai/` found no page that says the old answer; the one test file outside its manifest, `tests/test_slice_scope_report.py`, was edited by the host in T004's commit `ec599fc`; no commit of its own)* **Not a task unless T004's report names a page outside its manifest** that still says a CI checkout is depth 1,
  that the slice is not checked there, or that a maintainer adds the key by hand. If it does, the host adds that page
  to this task's manifest, and the increment is: the page says what is true (RED: a `grep`-style assertion in the
  page's own test where one exists, otherwise by search); if it does not, the host ticks this task on T004's report
  and it has no commit. Numbered here so the dependency order of T008 is plain.

**Files:** none until T004 reports.

### T008 — The release says what it is (R7 · AC-S24-10, -11)

- [x] *(host, current context — two fragments of prose; e4 is followed by the hand at the demo, quickstart step 4)* **Rule R7.** Needs T002, T003, T004 (it states what they landed). The fragment began in T002; this task
  completes its wording against the final behaviour and edits the second fragment.

**RED:** `tests/test_changelog.py` is in the suite and passes from T002. The checks, written as checks:
e1 `changelog.d/ci-fetches-slice-base.md` has first line `PATCH`; says the `verify` job fetches full history, a slice
pull request is held to its scope, *NOT checked* in CI is now a failure, and — plainly — that `check-migrations` and
`check-flags` now hold their *new in this change* rules in CI on every pull request, naming both refusals; its
catch-up says a workflow the project took over and a pipeline of its own that sets a CI marker on a shallow clone are
not rewritten by `migrate` and turn red on a slice branch until the job fetches history, with the key to add
(`fetch-depth: 0`; `GIT_DEPTH: "0"`), that an open pull request carrying either pattern goes red and is fixed by
landing the expand first or seeding `off`, and that a long history pays the full fetch on that one job. e2
`changelog.d/slice-scope-base.md` no longer says a CI run with nothing to compare with exits 0 or that a maintainer
adds the key by hand — its *Catch-up* and last paragraph — checked by `grep -n "exits 0\|still exits\|adds \`fetch-depth"`
over that file, empty. e3 the docstring of `check-slice-scope.py` says a forge's checkout with no base fails — T004's,
re-read. e4 the catch-up paragraph, **followed as written** on a project generated at the commit before the slice
(workflow without the key) in a scratch directory under `/tmp`: add the key, build the pull-request checkout, the
slice is held; the host or the delegate records that run in its report. `VERSION` unchanged. `make test
TESTS="test_changelog"` green.

**GREEN** — edit the two fragments as e1 and e2 say; nothing else.

**REFACTOR:** none.

**Verify:** `make test TESTS="test_changelog"` green, then `make lint typecheck check-structure`; `git diff --stat`
over the slice shows `VERSION` unchanged and no change to the three scripts but `check-slice-scope.py`. Commit by
path; level line (PATCH, `VERSION` not raised because it already carries the MINOR).

**Files:** `changelog.d/ci-fetches-slice-base.md`, `changelog.d/slice-scope-base.md`.

---

## Phase 3: Gates and closing (host)

### T009 — Both full gates on the final tip, then the demo (host task)

- [ ] **Host task — not delegated.** Run `make verify` and `make -f delivery/Makefile verify` on the tree after T008;
  both green (Principle XIV), once with `CI=true GITHUB_ACTIONS=true` exported (AC-S24-13). Confirm the slice's diff
  touches under `delivery/` only `delivery/survey/pinned.md`, `VERSION` is `1.6.0.dev0`, none of `check-migrations.py`
  or either `check-flags.py` changed, and nothing under `tools/`, the `Makefile` or this repository's CI did. Then the
  demo from [quickstart.md](quickstart.md), run as the actor with this checkout's `./slipwai`. **Not run, and said so
  on the board:** a real runner on a real forge.

### T010 — The adversary pass (host task)

- [x] *(two seams at `edb78cd`, eight findings, none `CRITICAL`; triage D87; fixes T020–T024)* **Host task.** `drive-adversary` over the no-base states and both routes of `forge_checkout()` through the
  script's command line; any confirmed finding is a regression test at the owning layer, appended as a task below.

### T011 — Mutation (host task)

- [x] *(N/A — no command: this repository has no mutation tool configured, as for every slice before it; `delivery/commands/mutation.md` says to report that and not pretend. The setup decision is a person's. Teeth were seen by hand for each hold and for the F1 fix.)* **Host task.** `drive-mutation` over `check()`/`not_checked()` and the three generator changes, the report
  recorded; the tree clean afterwards. Survivors append tasks.

### T012 — Register row and benchmark (host task)

- [ ] **Host task.** The slice's row in the register and `benchmark.json` closed, after-acceptance commits riding in
  this slice's own pull request (`AGENTS.md`).

---

## Phase 5: After-converge gaps (appended 2026-10-04; D86)

### T017 — The words say where the two other gates look, and `adopt` says what a CI of your own needs (`MEDIUM`/`LOW` · G1, G2, G5 · AC-S24-8, -11, -12)

- [x] *(9f9d660; the fragment's second paragraph put in reading order by the host afterwards)* **RED:** a test in `tests/test_ci_fetch_adopted.py` adopts a repository whose forge is `other` (and one with no
  CI, `none`) and asserts the report's CI line ends *on a full clone with the trunk's branch fetched*; observed failing
  on the old strings. **GREEN:** the two strings in `ci_lines()` (`src/slipwai/adopt_report.py`) and the sentence in
  `docs/adopting.md` gain those words, exactly as D86 gives them; the fragment gains D86's four passages, verbatim, at
  the places D86 names (read D86 in `decisions.md` and the skipper's sentences in this task's brief). **The class:**
  every place `adopt` tells a person to run the gate in a CI it did not write (search `src/slipwai/` and `docs/` for
  *have your CI run*, *have it run*, *have that CI run*).

**Files:** `src/slipwai/adopt_report.py`, `docs/adopting.md`, `tests/test_ci_fetch_adopted.py`,
`changelog.d/ci-fetches-slice-base.md`.

### T018 — The reading of AC-S24-8 rests on a kept run, and the pull-request checkout carries tags (`MEDIUM`/`LOW` · G1, G2, G3 · AC-S24-8)

- [x] *(a64fe35; no existing answer changed with tags fetched, and no fixture makes a tag)* Tests only — holds. In `tests/test_ci_history_gates.py`: the shipped `check-migrations.py` on a trunk `develop`
  beside an older `master`, an expand and its contract in separate commits on `develop` — a push to `develop` with
  every branch fetched is refused, at depth 1 passes; and on a trunk `develop` with no `main` or `master`, a pull
  request carrying both with full history passes. Each says in its name or comment that it holds a reading `S31` will
  change. In `tests/forge_checkout.py` the full-history arm fetches tags as the forge does (research R-1); if any
  existing test's answer changes with tags fetched, that is reported as a finding and the test is **not** adjusted.
  Teeth seen for each hold.

**Files:** `tests/test_ci_history_gates.py`, `tests/forge_checkout.py`.

## Phase 6: Demo feedback (appended 2026-10-04; demo 1, `drive-hand`: `implementation`)

### T019 — The catch-up paragraph stands alone (AC-S24-11)

- [x] *(host, current context — one paragraph of prose; followed afterwards: a project generated by the factory at
  `838a3b0`, migrated with this checkout, reads both fixes in `.slipwai/catch-up.md` and no *as above*)*
  `slipwai migrate` copies only a fragment's **Catch-up.** paragraph into `.slipwai/catch-up.md`. The paragraph said
  an open pull request *is fixed as above*, and the paragraph for a trunk that is not `main` or `master` came after
  it, so neither instruction reached the file a maintainer reads. The catch-up is now one paragraph that says why
  the pull request is red, both fixes, and what a trunk of another name meets and does.

**Files:** `changelog.d/ci-fetches-slice-base.md`.

## Phase 7: Adversary findings (appended 2026-10-04; D87)

T020, T021, T022 and T024 edit `assets/toolkit/scripts/check-slice-scope.py` or the fragments and run in that order, one
delegate; T023 is disjoint and runs beside them.

### T020 — On a pull request, an unrelated branch-chosen base never stands (`HIGH` · F1 · AC-S24-14)

- [x] *(80cfa1f; teeth seen by the host: the one-line fix reversed, three failures, restored)* **RED:** in a new `tests/test_slice_scope_forge_hostile.py`, AC-S24-14's checkout built with
  `tests/forge_checkout.py`: the slice records `ci.branch: evil`, edits `Makefile`, merges an orphan root commit
  carrying its own tree, and the root is pushed as `evil`; with GitHub's variables, and with GitLab's, the gate exits 1
  naming `Makefile` and `project.json`, *compared with `main`* at the commit where the branch left it, in the words
  used where the target won. Observed failing today: exit 0, *compared with `evil`*. A second example: the same refs
  on a slice inside its scope pass with that line. **GREEN:** D87's rule — the last fallback of `older_of()` returns
  its second argument; nothing else in `merge_base()` moves. **The class:** in every pull-request checkout with a
  usable target that has a base, the commit compared with is the target's base or an ancestor of it — a sweep test
  over the shapes the suite already builds (trunk base older, target base older, equal, unrelated) asserts that
  invariant with `git merge-base --is-ancestor`. The docstrings of `older_of()` and the module follow.

**Files:** `assets/toolkit/scripts/check-slice-scope.py`, `tests/test_slice_scope_forge_hostile.py` (new).

### T021 — The fetch the gate prints names the branch in full (`MEDIUM` · F3 · AC-S24-16, AC-S24-9)

- [x] *(4531d3a)* **RED:** every assertion in `tests/` that quotes the printed fetch expects
  `git fetch origin refs/heads/<name>:refs/remotes/origin/<name>`, and one new example in
  `tests/test_slice_scope_forge_hostile.py`: a remote with a branch `main` and a tag `main` at the slice's head; the
  printed command is run as printed; the gate re-run compares with the branch (a host change is refused). Observed
  failing today (the tag is fetched; exit 0). **GREEN:** `fetch_command()` and its docstring; the module docstring's
  sentence about the command. **The class:** every place the script prints or describes a fetch (search the script
  for `git fetch`); every test that quotes it (`grep -rn "git fetch origin" tests` — `tests/test_cruise_watch.py` is
  another script's and is not touched unless it quotes this gate's line).

**Files:** `assets/toolkit/scripts/check-slice-scope.py`, `tests/test_slice_scope_forge_hostile.py`,
`tests/test_slice_scope_base.py`, `tests/test_slice_scope_no_base.py`, `tests/test_slice_scope_printed.py`,
`tests/test_slice_scope_forge_nobase.py`, and any other test module the search finds quoting this gate's command.

### T022 — The NOT-checked line says which refs it looked for (`LOW` · F4 · AC-S24-15)

- [x] *(0637839)* **RED:** in `tests/test_slice_scope_forge_nobase.py` (or the hostile file if that one would pass 350 lines): a
  full-history checkout whose only remote is `upstream`, an in-scope slice, a CI marker → exit 1 and one line naming
  `refs/heads/main` and `refs/remotes/origin/main` and ending *on any other CI, a full clone with the trunk's branch
  fetched from a remote named `origin`*; and the existing no-base examples assert the two refs. **GREEN:**
  `not_checked()` and its docstring; the module docstring. No base selection changes.

**Files:** `assets/toolkit/scripts/check-slice-scope.py`, `tests/test_slice_scope_forge_nobase.py`,
`tests/test_slice_scope_forge_hostile.py`, and any test module asserting the old last clause.

### T023 — The two refused cases S31 will weigh rest on kept runs (`MEDIUM` · B1, B2 · AC-S24-8)

- [x] *(4182248, both in `tests/test_ci_history_gates.py`; `source_tip_checkout()` added to the helper)* Tests only — holds, each saying it holds a reading `S31-gates-read-recorded-trunk` will weigh. With the shipped
  `check-migrations.py`: a pull request to `release/1` whose expand landed there in an earlier pull request is refused
  on the full-history pull-request checkout; an expand squash-merged to `main` and its contract on the same branch,
  not merged with `main`, is refused on a checkout detached at the branch's tip and passes on the merge commit.
  If `tests/test_ci_history_gates.py` would pass 350 lines, the two go in a new `tests/test_ci_history_branches.py`.
  Teeth seen for each.

**Files:** `tests/test_ci_history_gates.py`, `tests/test_ci_history_branches.py` (new, if needed),
`tests/forge_checkout.py` (only if the source-tip checkout needs a helper there).

### T024 — The fragments say it (F3, F4, B1, B2 · AC-S24-11)

- [x] *(bcd66dc)* After T020–T022. D87 gives the sentences and where each goes: the third paragraph of
  `changelog.d/ci-fetches-slice-base.md` (the refs the line names and the remote's name; the printed fetch as the
  first exception to *every answer is what it was*); inside the single **Catch-up.** paragraph, after *…or seed the
  new flag `off`.* and before *Where the trunk is not `main` or `master`…* (the source-tip branch and the pull request
  to a non-trunk branch); `changelog.d/slice-scope-base.md` quotes the new command wherever it quotes the old one.
  Wrapped at about 115 columns; the catch-up stays one paragraph. `make test TESTS="test_changelog"` green.

**Files:** `changelog.d/ci-fetches-slice-base.md`, `changelog.d/slice-scope-base.md`.

## Parallel opportunities

By manifest (each task's "Files" line):

| Task | Writes | Reads of another task's file |
|---|---|---|
| T002 | `src/slipwai/project/ci_workflows.py`, `tests/test_ci_fetch_generated.py`, `changelog.d/ci-fetches-slice-base.md` | none |
| T003 | `src/slipwai/project/adopted_ci.py`, `tests/test_ci_fetch_adopted.py` | none |
| T004 | `assets/toolkit/scripts/check-slice-scope.py`, `tests/test_slice_scope_forge_nobase.py`, `tests/test_slice_scope_no_base.py`, `tests/test_slice_scope_hostile_base.py` | none (no `forge_checkout.py`) |
| T005 | `tests/forge_checkout.py`, `tests/test_slice_scope_forge.py` | runs `check-slice-scope.py` |
| T006 | `tests/test_ci_history_gates.py` | `tests/forge_checkout.py` (T005); runs the three scripts |
| T008 | `changelog.d/ci-fetches-slice-base.md`, `changelog.d/slice-scope-base.md` | — |

- **May run together:** T002, T003, T004 and T005 — four disjoint manifests. T006 joins as soon as T005 is
  committed, beside whichever of T002–T004 is still running. Most delegates at once: **four**.
- **May not:** T006 before T005 (it imports the helper T005 owns). T008 beside T002 (both write
  `changelog.d/ci-fetches-slice-base.md`), and before T003 and T004 (it states what they landed). T007, if it becomes
  a task, after T004. Nobody beside T009.
- **Shared-tree caution.** T004's teeth and RED reversals change `check-slice-scope.py` in the working tree, and T005
  and T006 run that script; T002 and T003 reverse their own generators, which nobody else reads. So run each
  concurrent delegate in a worktree of its own off the commit that closes T001 (`isolation: worktree`), or run T004
  alone of the four while T005/T006's quick tests run. The host commits by path in order — T002, then T003, T004,
  T005, T006 — and the first user-visible commit is T002's.
- **Host tasks:** T001 precedes T002 (it records what T002–T004 change); T009 runs alone after T008, reading the
  whole tree; T010 – T012 follow, in order.

## Design review

No screen in this slice

## Convergence

**Converged on pass 1** (2026-10-04, cruise iteration 12, `drive-converge`, host model, fresh context) at `ff4e6b1`,
over `838a3b0..ff4e6b1`: no `CRITICAL` or `HIGH`; two `MEDIUM` and two `LOW` appended as T013–T016 under Phase 4
below, none of which re-opens the loop. The pass ended inside its budget and is complete for what it lists; what it
did not run is named at the end. No `.codegraph/` in this tree: callers were found by text search (`grep` over
`src/slipwai/`). Scratch was `/tmp/s24-converge`; no file in the tree was mutated, and `git status` after the pass
shows only this file, the runner's `benchmark.json` and the untracked `specs/cruise-log.jsonl`.

**Levels.** *Domain* — `check()` (`assets/toolkit/scripts/check-slice-scope.py:822–876`): the two forge arms return
*failed* (`:842` no base, `:872` could not compare); the `problem` arm (`:833–834`) and the not-a-slice arm
(`:830–832`) are not in the diff and keep exit 0; `main()` (`:879–894`) prints lost records above the notice and
returns 1 on `failed`. `not_checked()` (`:812–820`) keeps its sentence and adds the third clause. `forge_checkout()`
(`:802–809`) is unchanged. Run on a generated project in scratch: the pull-request shape at full history → exit 1,
`Makefile` named, *compared with `main` at*; depth 1 under GitHub's and under GitLab's variables → exit 1, one stderr
line with all three needs; `GIT_DIR` unreadable under `CI` → exit 0. *Use case* — three generator changes and every
caller: `workflow()` from `scaffold.py:111` only; `delivery_workflow()` and `gitlab_job()` from
`project/adopted.py:58,60` only; `deploy_workflow.py:32` imports `NODE_SETUP` and `toolchain_setup`, neither changed.
All 80 combinations of profile × backend × target × frontend were generated from `838a3b0` and from `ff4e6b1` and the
file maps compared: exactly two paths differ in every one, `.github/workflows/verify.yml` (the comment and the
`with:` block, four lines) and `scripts/check-slice-scope.py`. In every generated workflow the only job that runs
`make verify` is `verify`; `integration` runs `make migrate test-integration` at depth 1, and the deploy, promote,
rollback and event-model jobs run none of the three checks, so no job is left that runs the scope check on one
commit. *Delivery adapter* — the three files parsed as YAML from an adopted and a generated tree: `fetch-depth: 0`
is under `jobs.verify.steps[0].with` in both Actions files and absent from `integration` and `smoke`;
`GIT_DEPTH: "0"` is a string under `verify-delivery.variables`, `smoke-delivery` has no `variables`, no `rules:`.
Exit codes and stderr as above. *Screen* — none. *Published contract* — `changelog.d/ci-fetches-slice-base.md:1`
`PATCH`; each sentence set against a run, and two found less than true: it names `check-flags` for projects that
ship none (T013) and says a developer's machine answers as before where a marker is exported (T015).
`changelog.d/slice-scope-base.md` no longer says CI exits 0 (the one *exits 0* left, `:43`, is the unreadable
checkout, still true). The module docstring (`check-slice-scope.py:99–106,112–114`) says exit 1; `check()`'s own
docstring (`:825`) still says *a developer's failure* (T015). `VERSION` `1.6.0.dev0`, unchanged, as are
`check-migrations.py`, both `check-flags.py`, `delivery/scripts/`, `.github/`, `tools/` and the `Makefile`
(`git diff --quiet 838a3b0..ff4e6b1 --` over those paths).

**Criteria.** AC-S24-1 — `tests/test_ci_fetch_generated.py`, three tests over every backend and target. *Byte for
byte* is held by this pass's 80-combination comparison and by the diff not touching `event_model.py`,
`deploy_workflow.py` or `extensions/ux-gates/init.py`; the kept test asserts only that no other workflow carries
`fetch-depth`, and never sees the `ux-gates` workflow, which `project_files()` does not return and which carries
that key already (`init.py:134`). True today, held by nothing tomorrow (T016). AC-S24-2, -3 —
`tests/test_ci_fetch_adopted.py`, four tests (both forges, Gitea, with and without `smoke`, a refresh). AC-S24-4 —
`tests/test_slice_scope_forge.py`, five holds. AC-S24-5 — `tests/test_slice_scope_forge_nobase.py`
`test_every_no_base_state_on_every_route_under_every_marker_fails`, `test_a_passed_over_name_…`,
`test_a_lost_record_…`. AC-S24-6 — `test_a_diff_that_cannot_run_fails_under_a_marker`, and
`tests/test_slice_scope_hostile_base.py:176`. AC-S24-7 — `test_a_checkout_git_cannot_read_still_exits_0_…`,
`test_another_branch_has_nothing_to_hold_…`, `test_a_usable_base_is_held_exactly_…`. AC-S24-8 —
`tests/test_ci_history_gates.py`, five holds, aws and azure. AC-S24-9 —
`test_a_developers_checkout_with_no_base_still_fails_with_a_fetch_command`, and the unedited developer's tests.
AC-S24-10 — **no kept test** (T016); run here: a project generated by `838a3b0` and migrated by `ff4e6b1` gains the
step by fast-forward; one edited elsewhere in the file merges clean with the key; one edited at the checkout
(`with: submodules: true`) stops in a conflict on that file, both sides shown; an adopted repository on each forge
has its file replaced; `.slipwai/catch-up.md` carries the fragment's *Catch-up* as *Owes*. AC-S24-11 — the two
fragments and `tests/test_changelog.py`, with T013 and T015. AC-S24-12 — a search of `docs/`, `assets/` and
`src/slipwai/` for *NOT checked*, `fetch-depth`, *depth 1* and *shallow* finds no page saying the old answer; T015
for the one docstring. AC-S24-13 — fifteen modules (237 tests) run with `CI=true GITHUB_ACTIONS=true` exported:
green. With a pull request's `GITHUB_HEAD_REF=slice/S1` exported as well, one test fails, as it did before the
slice (T014).

**Sweeps.** Every checkout step in every generated or adopted CI file: above. Every test asserting an exit code
under a marker (`grep` for the three markers over `tests/`): `test_slice_scope_no_base.py`,
`…_hostile_base.py`, `…_report.py:180,200` and the two new modules assert 1; none still asserts 0 for *NOT
checked*. This repository's installed `delivery/scripts/check-slice-scope.py` and `.github/workflows/` are not in
the diff. History readers under `assets/`: the three scripts and `check-ux-gates.py`, as D84 found. **Not run:** a
real runner on either forge (D12); `make verify` and the delivery gate (T009's); no mutation (T011's).

**Constitution.** **I** — no check removed: three that could not look now look
(`src/slipwai/project/ci_workflows.py:269–273`, `adopted_ci.py:74–79,150–152`), and one that passed without looking
fails (`check-slice-scope.py:842,872`); a project's files change only by `migrate`, seen above; `VERSION`
untouched; fragment at `changelog.d/ci-fetches-slice-base.md:1`. **III** — one key, one variable, two booleans; no
setting, expression or `rules:`. **V** — every example enters through the generator's output or a script's
command line; holds are named holds. **VIII** — `PATCH` with what a generated repository meets after `migrate`
(`ci-fetches-slice-base.md:28–35`). **XI** (the same verdict locally and in CI) and **XII** (expand and contract
in separate deployments; a new flag off) — now held in CI by the fetch, `tests/test_ci_history_gates.py:118–133`.
**XIV** — both full gates are T009's, not run by this pass. No money, time or identity in the diff.

**Pass 2 — converged** (2026-10-04, cruise iteration 12, `drive-converge`, host model, fresh context) at `f133c7f`,
over `ac781ca..f133c7f` (`4976faf`, `cd6b0a9`, `6510b05`): T013, T015 and T016 are closed, no new finding, no task
appended. Not a second full reading: the three commits, the fragment whole, and what they could have broken. Inside
its budget and complete. No `.codegraph/` in this tree; where `check-flags` ships was found by text search
(`src/slipwai/project/flags.py:125`, `managed(CATALOG, target)`). Scratch was `/tmp/s24-converge2`; no file in the
tree was mutated. *T013* — one wording in both Actions generators (`ci_workflows.py:269–270`,
`adopted_ci.py:74–75`): the two checks every gate runs, *and `check-flags` where the project has one*, as D85
decided; the GitLab job's comment (`adopted_ci.py:151`) names no check (*the gate's checks*). Generated here with
`./slipwai` for each target: `none` and `existing` have no `scripts/check-flags.py` and no `check-flags` in
`verify-checks`; `aws` and `azure` have both; all four carry the same comment. Adopted on `github` and on `gitlab`:
`verify` runs `check-slice-scope` and `check-migrations`, there is no `check-flags` rule or script, and the comment
or variable is as above. Held by `test_every_check_the_comment_names_without_a_clause_is_one_the_projects_gate_runs`
(every backend × target) and `…_is_in_the_verify_chain_beside_it` (adopted, `github` and `gitea`); the helper has
teeth — `checks_named()` given pass 1's wording returns `check-flags`, which the subset assertion refuses wherever
the chain lacks it. *T015* — the fragment's clause (`ci-fetches-slice-base.md:26–28`) run on a generated project with
its `main` deleted, on `slice/S1`: no marker → exit 1 with the fetch command, as before the slice; `CI=true` and
`GITLAB_CI=true` → exit 1 with *NOT checked* and the three needs; `GIT_DIR` unreadable under `CI` → exit 0;
`main` present → exit 0 with or without a marker. `check()`'s docstring (`check-slice-scope.py:824–826`) says a
failure on either checkout, and the generated copy carries it; a docstring only, no behaviour in that commit.
*T016* — `tests/test_ci_fetch_migrate.py`, three holds, green: the key arrives by merge on a project put back to the
bare step; a project's own `with:` conflicts on that one file with both sides present and an abort restores it;
the `ux-gates` job's checkout as `./init --extension ux-gates` writes it carries the key. *Published contract* —
the fragment read once more, each sentence against the runs above: `PATCH` (`:1`); *in every project* and *the
only ones that have it* (`:8–9`) true of the four targets and of both adopted repositories; the second paragraph
qualifies `check-flags` each time it is named (`:13`, `:17`); the *Catch-up* is as pass 1 read it and is not in the
diff. *Constitution* — **I** and **VIII**: words and tests only; no check, exit code, key or variable changed
(`git diff ac781ca..HEAD -- src assets` is two comments and a docstring), `VERSION` unchanged, the same `PATCH`
fragment. **III**: one sentence for every project, no branch on the target in either generator. **V**: the new
tests enter through the generator's output and `migrate`'s command line, with fakes on `PATH`, no mocking
framework. Run: `make test TESTS="test_ci_fetch_generated test_ci_fetch_adopted test_ci_fetch_migrate
test_changelog test_slice_scope_report"` — 76 tests, OK, one skipped (no release tag fetched here). **Not run:** the
whole suite, `make verify`, the delivery gate, a real runner. Seen and not a finding: `.PHONY` names `check-flags`
in a project with target `existing` and in an adopted `delivery/Makefile`, where there is no such rule
(`src/slipwai/project/makefile.py:292`, `target != 'none'`) — older than the slice, inert, and no comment or
fragment sentence rests on it.

## Phase 4: Convergence pass 1 (appended 2026-10-04; converge delegate)

### T013 — A comment and a fragment name only the checks the project has (`MEDIUM` · AC-S24-1, -2, -11 · R7)

- [x] *(cd6b0a9; D85)* The comment written above the checkout names `check-flags` in every project, and `check-flags.py` ships only
  with the `aws` and `azure` targets. Seen: generated with target `none` and `existing`, `scripts/check-flags.py`
  absent and not in `verify-checks`, the comment in `verify.yml` names it; every adopted repository's
  `delivery/Makefile` has no `check-flags` target and `verify-delivery.yml` names it. The fragment says the same of
  all projects (*`check-migrations` and `check-flags` now run … on every pull request*). **The class:** every check a
  generated comment names is one that project's gate runs — asserted over every backend × target and over an adopted
  repository on each forge by reading the names in the comment against the `verify` chain of the Makefile beside it.
  How the comment is worded where there is no `check-flags` (dropped, or *where the project has one*) is the host's
  to choose; the fragment says which projects have it.

**Files:** `src/slipwai/project/ci_workflows.py`, `src/slipwai/project/adopted_ci.py`,
`tests/test_ci_fetch_generated.py`, `tests/test_ci_fetch_adopted.py`, `changelog.d/ci-fetches-slice-base.md`.

### T014 — The suite is the same on a pull request from a `slice/<id>` branch (`MEDIUM` · AC-S24-13 · older than the slice)

- [x] *(not done in this slice — placed in the split's Parking Lot by D85: older than the slice, behind the PRD's slices by D39)* Tests only. `current_branch()` takes `GITHUB_HEAD_REF` whether or not `HEAD` is detached, and tests that run a
  whole adopted or generated gate inherit it. With `CI=true GITHUB_ACTIONS=true GITHUB_HEAD_REF=slice/S1
  GITHUB_BASE_REF=main` exported, `test_adopt_facts.AdoptFactsTest.test_the_gate_holds_the_map_to_the_tree_and_the_page_to_the_record`
  fails (`check-slice-scope` refuses `delivery/baseline.json`, *compared with `main`*); it fails the same way at
  `838a3b0`, so the slice did not cause it, and the host may park it. It is what this repository's own CI sets the
  day a slice here is a pull request from a `slice/<id>` branch (`AGENTS.md`, *One pull request per slice*). **The
  class:** every test that runs `make verify` or `make -f delivery/Makefile verify` in a temporary repository builds
  its environment with the seven forge variables removed (`tests/test_ci_history_gates.py:54` has the function);
  the sweep is `grep -rn '"verify"' tests/*.py`, and the modules already run green under those four variables here
  are `test_adopt`, `test_adopted_manifest`, `test_candidates`, `test_parallel_slices`. Not run under them:
  `test_matrix`, `test_add_service`, the `test_verify_stamp_*` modules.

**Files:** `tests/test_adopt_facts.py` (`:128`, `:231`, `:321`), and any module the sweep finds; `tests/support.py`
if the function is shared.

### T015 — The words about a developer's machine, where a marker is exported (`LOW` · AC-S24-11, -12)

- [x] *(6510b05; D85)* `changelog.d/ci-fetches-slice-base.md:25` says *on a developer's machine every answer is what it was*. A local
  shell with `CI`, `GITHUB_ACTIONS` or `GITLAB_CI` exported and no base went from exit 0 to exit 1
  (`tests/test_slice_scope_report.py:200` holds it); the sentence gains that clause. `check()`'s docstring
  (`assets/toolkit/scripts/check-slice-scope.py:825`) says the last value is *whether that line is a developer's
  failure*; it is now a failure on either checkout.

**Files:** `changelog.d/ci-fetches-slice-base.md`, `assets/toolkit/scripts/check-slice-scope.py` (the docstring only).

### T016 — What `migrate` does with the step, and the `ux-gates` workflow, are held by a test (`LOW` · AC-S24-1, -10)

- [x] *(4976faf, all in `tests/test_ci_fetch_migrate.py`; D85)* Tests only. AC-S24-10 was run by this pass and by nothing kept: a generated project whose `verify` job's
  checkout is put back to the bare step and committed as the factory's, then `slipwai migrate` — the key arrives
  where the step is as generated, and the file conflicts where the project wrote its own `with:`. And
  `test_hold_no_other_generated_workflow_fetches_history` does not see the `ux-gates` workflow: one assertion on what
  `extensions/ux-gates/init.py` writes (its checkout as it is at `ff4e6b1`), so the criterion's *byte for byte* has a
  holder for the one workflow `project_files()` does not return.

**Files:** `tests/test_ci_fetch_generated.py`, a new `tests/test_ci_fetch_migrate.py`.
