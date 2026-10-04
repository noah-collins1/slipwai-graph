# Tasks: S03-verify-stamp — the gate returns in under a second on a tree it already passed

**Input**: [plan.md](plan.md) (*The example map* R1–R13 is what the tasks cut on; *The design*; *Project Structure*; *What
this slice changes in code that was here*; *Delegation*), [research.md](research.md), [data-model.md](data-model.md),
[quickstart.md](quickstart.md); acceptance criteria AC-S03-1 … AC-S03-31 in `specs/001-faster-slipwai/spec.md` under
`### S03-verify-stamp` (example e*n* is criterion AC-S03-*n*); decisions D7, D9, D12, D30, D32, D33, D36, D39, D73, D74,
D75, D76, D77 in `specs/001-faster-slipwai/decisions.md`. No `examples.md`: a method slice with no screen and no event
model of its own.

**Branch**: `adopt-method` (D12). No `slice/` branch, no push, no claim. One commit per task.

**Delegation**: one delegate per implementation task, each its own RED-GREEN-REFACTOR increment and its own commit. The
"Files" line of a task is its manifest: the only files that delegate may write. Nobody but the host writes `tasks.md`.

**User stories** (from the plan's example map): **US1** a tree that passed is not judged again — `verify-stamp.py` and the
recipe (R1–R6); **US2** where a stamp is not used, and what a run leaves — the same script and recipe (R7–R11); **US3**
what ships — `gate.py`'s reach, the page, the fragment (R12–R13). T001 belongs to no story: it is the Pin stage.

**Not a task:** AC-S03-20 (the whole reuse run under one second on the Independent Test's project with the real toolchain)
is the demo's: the hand measures it ([quickstart.md](quickstart.md)); the suite holds causes only, never a clock.

## Constraints

Constraints that hold for every task, stated once:

- **Not edited, ever, by any task here:** anything under this repository's `delivery/` (except the `pinned.md` rows T001
  appends, which are the host's `/characterise` step), `tools/`, the root `Makefile`, `.github/`, or hook settings (D9);
  nothing under `release/`; no file `delivery/.written` lists. No check is removed or narrowed (Principle I).
- **Tests.** The fixture project and the stand-in tools of [research.md](research.md) item 5 live in
  `tests/stamp_fixture.py`, written by the first task that needs it (T002) and extended by later ones (additions only). A
  fake is an executable or a class written in the test tree implementing the tool's real command line; **never a mocking
  framework, `unittest.mock` included**. The evidence is the stand-ins' log, never the run's own line (e19). **No
  wall-clock assertion** (D75): SC-001 is the demo's. **Every test builds its environment with `CI`, `GITHUB_ACTIONS` and
  `GITLAB_CI` removed** unless the example sets one. A test that loads a toolkit script as a module sets
  `sys.dont_write_bytecode = True` first. Where a platform cannot make a link or an executable bit, the example skips,
  saying why — never a sleep.
- **Toolkit scripts.** Every `read_text` and `open` in `assets/toolkit/scripts/verify-stamp.py` names `encoding="utf-8"`
  (or is binary). The script starts, and answers *no stamp*, on any `python3` (it may use nothing newer than the syntax
  the `check-python` message is printed from). Nothing it meets can fail the gate: `reuse` exits 0 only after printing the
  reuse line; `record` always exits 0.
- **Size.** Every file under `src/` and `tests/` stays within 350 lines (`make check-structure`). The cuts are made in
  advance below (R2 → `tests/test_verify_stamp_working.py`, R6's closed-list test → `tests/test_verify_stamp_lists.py`,
  R8 → `tests/test_verify_stamp_force.py`, R10 → `tests/test_verify_stamp_cannot.py`); a delegate who finds a file nearing
  the limit splits by rule, never truncates, and names the new file in its report. `makefile.py` is 326 of 350 lines:
  the recipe's text goes to `gate.py`, not there.
- **Commits are by path.** `git commit -m … -- <the task's manifest paths>` (new files first `git add <exact path>`),
  never `git add -A`. `make lint typecheck check-structure` before each commit.
- **RED is seen** for its stated reason before the production file is touched. A **hold** (the plan's *What this slice
  changes in code that was here*) is written as a hold, saying so in the test's name or comment, and observed passing;
  it is not a RED. A hold is shown to have teeth by changing the production file, seeing the test fail, and restoring
  with `git checkout -- <exact path>`.
- **GREEN is a class**, not an instance: every entry of a list, every marker, every mode the criterion names, each with
  its own example, and a sweep named in the report of where else the same shape occurs.
- **Versioning** (`AGENTS.md`). MINOR: `VERIFY_FORCE` and the stamp file are new, every existing answer means what it
  meant. `VERSION` stays `1.6.0.dev0`. T002 is the first commit that changes what `make verify` does and carries
  `changelog.d/verify-stamp.md` in its first form (first line `MINOR`); its message names the level and the reason.
  T014 completes the fragment. Every later commit that changes `assets/` or `src/` says `Level MINOR; VERSION already
  1.6.0.dev0`; a commit that changes only `tests/` says it reaches no user.
- **Quickest test per task:** `make test TESTS="<modules>"`, the modules each task names.

## Format: `[ID] [P?] [Story] Description` — each task is one increment, one commit

`[P]` marks a task whose files are disjoint from every task that may run at the same time. **No task here is `[P]`:** see
*Parallel opportunities*.

---

## Phase 1: Pin (no story)

### T001 — What `make verify` runs, and what a wrapped application's gate says, pinned (host's `/characterise` step)

- [x] **Pin, no rule, no production change.** The host runs this as the ladder's `/characterise` step before the implement
  stage; the implement stage does not repeat it and starts at T002 with the pin green. Nothing under `assets/` or `src/`
  changes.

**Pins** (plan, *What this slice changes in code that was here*; green against today's generator before any change,
written as holds, teeth shown on each by changing `makefile.py` or `adopted_targets.py` and restoring):
1. The `verify` rule of a generated project's `Makefile`: which checks a full run runs, in which order, and the closing
   line `verify: all gates passed` — for a project with a transport (`check-openapi` inside its markers) and without, and
   that `./init --http none` leaves a gate that runs with no `check-openapi`. The pin reads the *prerequisites of the
   gate target*, by a helper that follows `verify` to `verify-checks` when it exists, so it is green before and after.
2. The `verify` rule of a project with a wrapped application, and the refusal while nothing is confirmed
   (`GATE`, `NOTHING_CONFIRMED`): byte for byte.
- *Not pinned, changed on purpose:* that `verify` itself carries the prerequisites.

**Verify:** `make test TESTS="test_verify_stamp_pinned"` green against the unchanged generator, then
`make lint typecheck check-structure`. Commit by path (tests only: reaches no user).

**Files:** `tests/test_verify_stamp_pinned.py` (new), `delivery/survey/pinned.md` (rows appended, as `/characterise` does —
the only file under `delivery/` any task here touches; append-only).

---

## Phase 2: User Story 1 — a tree that passed is not judged again [US1]

`assets/toolkit/scripts/verify-stamp.py`, `src/slipwai/project/gate.py`, `src/slipwai/backends.py`, the tests. T002–T007
all edit the script: they run in order. Needs T001.

### T002 — [US1] A pass is recorded and reused, saying so in one line (R1 · AC-S03-1, -18, -19)

- [x] **Rule R1.** The first increment of the slice: it introduces the recipe, the script and the fixture. Reads and does
  **research item 6** first: how the toolkit's scripts reach a project (the copier, `migrate`'s file list,
  `tests/test_toolkit.py`, `tests/test_monorepos.py`), and adds `verify-stamp.py` to every list that names the script's
  neighbours; if the toolkit copies `assets/toolkit/scripts/` whole and the list is only a test's expectation, extends
  that expectation and says in the report which it was. Writes `tests/stamp_fixture.py` (the fixture project generated
  once per class and copied per test — standard profile, Python backend, `http="none"`, no frontend, on branch `topic`;
  stand-ins for `make`'s tools — `uv` (which also writes `apps/service/.venv/pyvenv.cfg` with `version_info`), `git`
  wrapping nothing unless an example needs a failing one, a logged `python3` question — put first on `PATH`; the log
  reader; `run_gate(env, args)` that removes the three CI markers). New `src/slipwai/project/gate.py`: the stamped
  `verify` rule (the two-step recipe of the plan's *The design*), `verify-checks` carrying today's prerequisites, blank
  line and closing line, and the `VERIFY_STAMP` variable; `gate_target` chooses it **only for a project whose shape is the
  fixture's (no transport, one Python service, no wrapped application)** and today's text otherwise — the widening is
  T013's. `adopted_targets.py` delegates `gate_target`; `GATE` and `NOTHING_CONFIRMED` stay byte for byte. The script's
  `reuse` and `record` with the minimum key (every covered file's raw bytes by `git ls-files -z --cached --others
  --exclude-standard`, `lstat`/`open`, never through git's filters), the stamp's five fields as plain JSON under the git
  directory, the reuse line (the five facts of AC-S03-1), a pending note. Also the fragment `changelog.d/verify-stamp.md`
  in its first form (`MINOR`; what `make verify` now does on a tree that already passed), and the commit message names
  the level and the reason. Test module `tests/test_verify_stamp_reuse.py` (new).

**RED** (each seen failing for its stated reason before `gate.py` or the script exists):
- e1 the fixture's gate run twice → the second prints one line beginning `verify:` with the five facts (not the closing
  line), exits 0; the stand-ins' log gains only version questions (no check started). Fails today: the second run runs
  every check.
- e18 the stamp parsed: the five fields (`key`, `tree`, `scripts`, `tools`, `passed`, `result` per data-model) as plain
  text; one field removed, or the file cut short, is no stamp and the full gate runs, writing a new one. Fails today:
  no file.
- e19 the evidence is the log, not the run's own line: the example's assertion on "no check started" reads the stand-ins'
  log and fails the example's own wording if it reads the output. This is the shape of every "no check ran" in the slice.
- the closing line of a full passing run is `verify: all gates passed` byte for byte and of nothing else; a reuse never
  prints it.

**GREEN** — the recipe, `verify-checks`, the script with the minimum key, the lines; the smallest change that has the
second run read the first's stamp. Nothing is added to the key beyond the working files' bytes (T003 on).

**REFACTOR:** the key builder is functions in the script, each part its own digest so the stamp can show `tree`,
`scripts` and `tools` apart; no abstraction layer.

**Verify:** `make test TESTS="test_verify_stamp_pinned test_verify_stamp_reuse test_toolkit test_monorepos test_changelog"`,
then `make lint typecheck check-structure`. Commit (`Level MINOR`; the fragment's first form).

**Files:** `assets/toolkit/scripts/verify-stamp.py` (new), `src/slipwai/project/gate.py` (new),
`src/slipwai/project/adopted_targets.py`, whichever list or test expectation research item 6 finds (named in the report;
expected `tests/test_toolkit.py` or `tests/test_monorepos.py`), `changelog.d/verify-stamp.md` (new),
`tests/stamp_fixture.py` (new), `tests/test_verify_stamp_reuse.py` (new).

### T003 — [US1] The key is the working files, as they are (R2 · AC-S03-2, -3, -4)

- [x] **Rule R2.** The key covers raw bytes, the executable bit, a link's target, untracked-not-ignored files and
  deletions, and the index's entries (names, modes, blob ids, stages) — read on every run, through no filter, and the
  real index is never written. Test module `tests/test_verify_stamp_working.py` (new — the cut from R1's file is made in
  advance).

**RED:**
- e2 one example each: a tracked edit uncommitted; the same edit committed; a new untracked file; a deleted file;
  `chmod +x`; a link retargeted → the full gate runs and a passing run writes a new stamp (read from the log, e19).
  Fails against T002's key where it holds only bytes: the executable bit, the link target and the deleted file.
- e3 a CRLF rewrite under `* text=auto eol=lf` runs the full gate; a rewrite at the same size with the modification time
  restored runs it; the index file's bytes are equal before and after a run (the example reads them). Fails where a
  filter or a stat shortcut is used.
- e4 `git add` of an untracked file with the same bytes runs the full gate (the index's entries are in the key).

**GREEN (the class):** every kind a covered path can be — regular file, executable, link (target as bytes, never
followed), missing, and an index entry's four parts — each with its own example above; the index read with
`git ls-files -z --stage`, never with a command that refreshes it; sweep every git call the script makes for one that
could write the index.

**REFACTOR:** one function reads a covered path into its record; no second walk.

**Verify:** `make test TESTS="test_verify_stamp_reuse test_verify_stamp_working"`, then `make lint typecheck check-structure`.
Commit (`Level MINOR; VERSION already 1.6.0.dev0`).

**Files:** `assets/toolkit/scripts/verify-stamp.py`, `tests/stamp_fixture.py` (additions only),
`tests/test_verify_stamp_working.py` (new).

### T004 — [US1] The key is history and position (R3 · AC-S03-5)

- [x] **Rule R3.** `HEAD`'s commit, the branch name, every ref under `refs/heads` and `refs/remotes`, and the shallow
  boundary (the file `git rev-parse --git-path shallow` names) are in the key; an unborn branch is a value, not a
  failure (research item 3). Test module `tests/test_verify_stamp_key.py` (new).

**RED:**
- e5 one example each: an empty commit; another branch checked out at the same commit; `git update-ref
  refs/remotes/origin/main <other>`; a `shallow` file appearing → the full gate runs, a new stamp. Fails against T003.

**GREEN (the class):** every part of the history the criterion names, each with its example; the ref list is every ref
under both namespaces, not the checked-out one; `git rev-parse -q --verify HEAD` on an unborn branch gives a value.

**REFACTOR:** the history part is one function returning one digest.

**Verify:** `make test TESTS="test_verify_stamp_reuse test_verify_stamp_working test_verify_stamp_key"`, then
`make lint typecheck check-structure`. Commit (`Level MINOR; VERSION already 1.6.0.dev0`).

**Files:** `assets/toolkit/scripts/verify-stamp.py`, `tests/stamp_fixture.py` (additions only),
`tests/test_verify_stamp_key.py` (new).

### T005 — [US1] The key is the gate's scripts (R4 · AC-S03-6)

- [x] **Rule R4.** The `Makefile` and every covered file under `scripts/` are one named part, `scripts`, of the key and
  of the stamp, beside `tree`. Test module `tests/test_verify_stamp_key.py`.

**RED:**
- e6 a comment added to `scripts/check-imports.py` runs the full gate; a comment added to the `Makefile` runs it; and
  in the new stamp the `scripts` field differs from the old one **and the `tree` field differs too** (a covered file
  moved), so the part is named and not a duplicate of the other. Fails against T004: no `scripts` part distinct from
  `tree`.

**GREEN (the class):** the `Makefile` and every file under `scripts/` at any depth, covered files only; the field is its
own digest.

**REFACTOR:** `tree` and `scripts` share one file-record function (T003's), not a second reader.

**Verify:** `make test TESTS="test_verify_stamp_reuse test_verify_stamp_working test_verify_stamp_key"`, then
`make lint typecheck check-structure`. Commit (`Level MINOR; VERSION already 1.6.0.dev0`).

**Files:** `assets/toolkit/scripts/verify-stamp.py`, `tests/test_verify_stamp_key.py`.
If `tests/test_verify_stamp_key.py` nears 350 lines, R4's examples move to `tests/test_verify_stamp_scripts.py` (new),
named in the report.

### T006 — [US1] The key is the machine's tools (R5 · AC-S03-14, -15, -16, -17)

- [x] **Rule R5.** The table of machine-supplied tools per backend, beside `BACKEND_TOOLING` in `src/slipwai/backends.py`
  (`make`, `git`, `python3` in every project; `uv` for Python; `node` and `npm` for TypeScript or a frontend; `go`; `java`
  for both Java backends; a project with several backends takes the union, each asked once per run). `gate.py` writes
  `VERIFY_STAMP` from it (`--tool uv`, one `--environment` per Python service). The script launches each tool once with
  its version argument and the key takes the first non-empty line, whole; lock-pinned tools are never asked; the
  interpreter is read from `pyvenv.cfg`'s `version_info`; a tool that cannot be asked is a reason, not a failure. Test
  module `tests/test_verify_stamp_tools.py` (new).

**RED:**
- e14 the table has a row per backend (a test over `BACKEND_TOOLING`'s keys fails when a backend has none); the fixture
  asks `make`, `git`, `uv` and reads `python3` (read from the log). Fails today: no table.
- e15 the `uv` stand-in reports another first line → full gate, new stamp; no path of an executable in the stamp file.
- e16 no `ruff`, `mypy` or `pytest` version question in the log; a changed `uv.lock` runs the gate; a changed
  `version_info` in `pyvenv.cfg` runs the gate.
- e17 one example each: tool absent, non-zero exit, silent, hung past the script's timeout (the stand-in sleeps; the test
  holds the cause, not the duration), `pyvenv.cfg` missing → the full gate, one line naming the cause, **no stamp after
  the pass**, exit 0.

**GREEN (the class):** every tool of the table for every backend, asked once, first non-empty line whole; every way a
question can fail (absent, non-zero, silent, hung, unreadable `pyvenv.cfg`) is the same "cannot tell" answer R10 will
extend; sweep that the table is the only list of tools and the recipe's `--tool` words come from it.

**REFACTOR:** the table's rows are data in `backends.py`; `gate.py` reads them; the script carries no table.

**Verify:** `make test TESTS="test_verify_stamp_reuse test_verify_stamp_tools test_backends test_verify_stamp_pinned"`, then
`make lint typecheck check-structure`. Commit (`Level MINOR; VERSION already 1.6.0.dev0`).

**Files:** `assets/toolkit/scripts/verify-stamp.py`, `src/slipwai/backends.py`, `src/slipwai/project/gate.py`,
`tests/stamp_fixture.py` (additions only), `tests/test_verify_stamp_tools.py` (new).

### T007 — [US1] The key is what a check reads that git ignores, and the variables that change an answer (R6 · AC-S03-7, -8, -9)

- [x] **Rule R6.** The two closed lists beside the checks: the ignored inputs (`.codegraph/codegraph.db` and its
  write-ahead file — never `gate-memory.json`; every harness projection directory `gitignore.py` names; `tools/ux-gates/`;
  `skills/ui-ux-pro-max/`; `.env`) by bytes, absence a value; and the variables (`UX_GATES_REQUIRE`, `UX_GATES_SINCE`,
  `UX_GATES_SHARD`, `CODEGRAPH_GATE_NO_SYNC`, `SLIPWAI_NO_INSTALL`, `GITHUB_HEAD_REF`, `CI_COMMIT_REF_NAME`) by value,
  unset distinct from empty; `UX_GATES_JOBS` is not in it; `RATCHET_TIGHTEN` neither reads nor writes a stamp. Also
  **research item 8's assumed readings**, read at the start: what a kit under `tools/ux-gates/` consists of and which
  file pins it; whether any gate step reads `.env`; and the **plan's *Installed environments* table, per backend** —
  Python's `uv sync --locked` on every run (outside the key, `pyvenv.cfg`'s `version_info` in it, T006), and for every
  other backend the recipe's own text read from its `scripts/verify`: where it does not reinstall from the lock on every
  run, the installed manifest (`node_modules/.package-lock.json`, and the same under `scripts/event-model/`) joins the
  ignored list. Each backend's reading is written into the report. Test modules `tests/test_verify_stamp_inputs.py` (new)
  and `tests/test_verify_stamp_lists.py` (new — e7's closed-list test).

**RED:**
- e7 each list entry changed, created and removed in turn → the full gate runs (one example per entry); and the
  closed-list test: a planted check script that reads an ignored path not on the list fails it (the test scans
  `scripts/check-*.py` of a generated project and the lists).
- e8 the installed-environment table held per backend: for each backend, an example generated for it shows its recipe
  reinstalls from the lock (outside the key) or its manifest is on the list (inside it).
- e9 each variable set, set empty and unset gives three distinct keys; `UX_GATES_JOBS` changes nothing;
  `RATCHET_TIGHTEN=1` reads and writes nothing (the stamp's bytes stand, today's output).

**GREEN (the class):** every entry of both lists, every state of every variable, every backend's row of the table; the
lists are one place each in the script, and the closed-list test fails when a check reads an ignored path or a variable
not on them — sweep every `check-*.py` for `os.environ` and for reads of ignored paths, naming the result.

**REFACTOR:** lists as data at the top of the script; the key reads them; no second copy in the test (the test imports
them).

**Verify:** `make test TESTS="test_verify_stamp_reuse test_verify_stamp_inputs test_verify_stamp_lists"`, then
`make lint typecheck check-structure`. Commit (`Level MINOR; VERSION already 1.6.0.dev0`).

**Files:** `assets/toolkit/scripts/verify-stamp.py`, `tests/stamp_fixture.py` (additions only),
`tests/test_verify_stamp_inputs.py` (new), `tests/test_verify_stamp_lists.py` (new).

---

## Phase 3: User Story 2 — where a stamp is not used, and what a run leaves [US2]

Needs US1 whole. Edits the same script and recipe.

### T008 — [US2] Never on the trunk, in CI, detached or adopted (R7 · AC-S03-21, -22, -24)

- [x] **Rule R7.** Step (2) of `reuse`, and `record`'s: a CI marker, a detached `HEAD` or the trunk — no read, no write,
  no removal, today's output. The trunk is one definition with `check-slice-scope.py`'s (D30, D33; research item 3): the
  script loads that function, or a test holds the two answers equal over D30's and D33's cases. A project with a wrapped
  application has no stamp step. Test module `tests/test_verify_stamp_where.py` (new).

**RED:**
- e21 each of the three markers (`CI=false` among them: any non-empty value is a marker), `main`, `master` where it is the
  trunk, a `ci.branch` from `project.json`, a detached `HEAD` → a planted stamp is byte-identical afterwards, and
  stdout equals a run of the same tree without the script's lines.
- e22 `slice/S01-x`, `fix/y`, `adopt-method` read the stamp (reuse line).
- e24 the `Makefile` of a project with a wrapped application has no stamp step and `NOTHING_CONFIRMED` is unchanged
  (the pin's holds stay green).

**GREEN (the class):** every marker, every trunk resolution of D30 and D33, detached, and the wrapped application;
the equality of the two trunk answers is held.

**REFACTOR:** eligibility is one function, called by both verbs.

**Verify:** `make test TESTS="test_verify_stamp_reuse test_verify_stamp_where test_verify_stamp_pinned test_check_slice_scope"`,
then `make lint typecheck check-structure`. Commit (`Level MINOR; VERSION already 1.6.0.dev0`).

**Files:** `assets/toolkit/scripts/verify-stamp.py`, `tests/stamp_fixture.py` (additions only),
`tests/test_verify_stamp_where.py` (new).

### T009 — [US2] `VERIFY_FORCE` runs the gate anyway, and `make ci` always does (R8 · AC-S03-23, -25)

- [x] **Rule R8.** Step (4): forced — `VERIFY_FORCE` set to anything other than empty or `0`, on the command line or in the
  environment, or `ci` among `MAKECMDGOALS`: one line naming it and the value, the stamp removed, every check runs, and a
  passing run writes a new stamp. Test module `tests/test_verify_stamp_force.py` (new).

**RED:**
- e25 `VERIFY_FORCE=1` and `=yes`, each on the command line and in the environment: one line naming `VERIFY_FORCE` and the
  value, every check, a new stamp; `VERIFY_FORCE=` and `=0`: reuse.
- e23 `make ci` on a stamped tree: every prerequisite of `ci` runs and the forced line says why.

**GREEN (the class):** every spelling of "unset", every other value, both channels, and `ci`.

**REFACTOR:** the force decision is one function reading the two sources.

**Verify:** `make test TESTS="test_verify_stamp_reuse test_verify_stamp_where test_verify_stamp_force"`, then
`make lint typecheck check-structure`. Commit (`Level MINOR; VERSION already 1.6.0.dev0`).

**Files:** `assets/toolkit/scripts/verify-stamp.py`, `tests/stamp_fixture.py` (additions only),
`tests/test_verify_stamp_force.py` (new).

### T010 — [US2] A stamp is written only by a run in which everything ran and passed (R9 · AC-S03-10, -11, -26)

- [x] **Rule R9.** Removed before the first check; `record` writes it after the last, by rename, only where the key is
  equal to the pending one; `make -i`, `-n`, `-t`, `-q` leave none and reuse none; a key that moved during the run, or a
  stamp that cannot be written or removed, exits 0 with the closing line and one line *not recorded* with its reason.
  Test module `tests/test_verify_stamp_runs.py` (new).

**RED:**
- e26 a failing check leaves no stamp though one stood before; a run killed mid-gate leaves none (the stamp was removed
  first).
- e10 `make -i verify` on a failing tree: no stamp; `-n`, `-t`, `-q` on a stamped tree: the stamp's bytes stand and there
  is no reuse line.
- e11 a stand-in that edits a tracked file during the gate: exit 0, the closing line, one line *not recorded*; a read-only
  stamp directory: the same.

**GREEN (the class):** every make mode of the criterion (`i`, `n`, `t`, `q`, and their combinations with `-k`), every way
the write can not happen (key moved, unwritable, unremovable), each its example; a stamp never changes the gate's exit
code.

**REFACTOR:** `record`'s write is one function (temporary then rename) that T013's file rule will reuse.

**Verify:** `make test TESTS="test_verify_stamp_reuse test_verify_stamp_runs test_verify_stamp_force"`, then
`make lint typecheck check-structure`. Commit (`Level MINOR; VERSION already 1.6.0.dev0`).

**Files:** `assets/toolkit/scripts/verify-stamp.py`, `tests/stamp_fixture.py` (additions only),
`tests/test_verify_stamp_runs.py` (new).

### T011 — [US2] When it cannot tell, it runs the gate and never stamps (R10 · AC-S03-12, -13)

- [x] **Rule R10.** Step (3): one line before the first check, the stamp removed, a pending note saying this run records
  nothing, the full gate, the gate's own exit code. Test module `tests/test_verify_stamp_cannot.py` (new).

**RED:**
- e12 `assume-unchanged`; `skip-worktree`; a submodule entry (mode `160000`); an untracked directory that is itself a
  repository (research item 2's *assumed* reading is read here and written into the report) → the line names which, the
  full gate runs, no stamp after the pass.
- e13 no `git` on `PATH`; no repository; a `git` stand-in that fails; an unreadable covered file (the line names the
  file) → the line carries git's reason, the full gate, no stamp, exit as the gate's.

**GREEN (the class):** every index mark and entry kind named, every way git can be absent or fail, an unreadable file
anywhere in the covered set; "never passes on less" is held by a check that the gate runs in each.

**REFACTOR:** T006's "cannot tell" answers and these are one reason type with one line shape.

**Verify:** `make test TESTS="test_verify_stamp_runs test_verify_stamp_cannot test_verify_stamp_tools"`, then
`make lint typecheck check-structure`. Commit (`Level MINOR; VERSION already 1.6.0.dev0`).

**Files:** `assets/toolkit/scripts/verify-stamp.py`, `tests/stamp_fixture.py` (additions only),
`tests/test_verify_stamp_cannot.py` (new).

### T012 — [US2] Where it lives and how long (R11 · AC-S03-27, -28)

- [x] **Rule R11.** Under the git directory (`git rev-parse --absolute-git-dir`), one file per project per worktree
  (`<project>` the digest of `--show-prefix`), a rename of a finished file, never through a link; no expiry. Test module
  `tests/test_verify_stamp_file.py` (new).

**RED:**
- e28 `git status --porcelain --ignored` shows nothing of it; a second worktree has no stamp of the first; two projects in
  one repository have two files; a link at the stamp's path, and a directory planted there, are replaced or refused as
  themselves and nothing outside is written through them.
- e27 a stamp whose `passed` is ten years old is reused; the stamp deleted, the gate runs.

**GREEN (the class):** every kind of thing that can already stand at the stamp's or the note's path (regular file, link,
directory, FIFO where the platform has one), `lstat` before use, never followed; sweep every path the script reads,
writes, renames onto or removes under the git directory and say for each what a link and a directory there now gives.

**REFACTOR:** one path function for the stamp and the pending note.

**Verify:** `make test TESTS="test_verify_stamp_reuse test_verify_stamp_runs test_verify_stamp_file"`, then
`make lint typecheck check-structure`. Commit (`Level MINOR; VERSION already 1.6.0.dev0`).

**Files:** `assets/toolkit/scripts/verify-stamp.py`, `tests/stamp_fixture.py` (additions only),
`tests/test_verify_stamp_file.py` (new).

---

## Phase 3 (continued): User Story 3 — what ships [US3]

Needs US2 whole. T013 edits `gate.py` and `makefile.py`; T014 the page and the fragment.

### T013 — [US3] The full gate is the gate it was, for every project the factory generates (R12 · AC-S03-29)

- [x] **Rule R12.** T002 chose the stamped rule only for the fixture's shape; this task widens `gate_target` to every
  generated project without a wrapped application. The per-transport line becomes `verify-checks: check-openapi` inside
  the same markers (`makefile.py`: the line and `.PHONY` only — 326 of 350 lines today), `./init --http none` cuts it,
  several services are one gate with one `--environment` each, and every starter passes its own gate. Test module
  `tests/test_verify_stamp_ships.py` (new).

**RED:**
- e29 per fixture of the pin (with a transport, without, `--http none`, several services, each backend), the
  prerequisites of `verify-checks` equal those `verify` had, in the same order, with the same closing line (by T001's
  helper); `./init --http none` leaves no `check-openapi` anywhere; the matrix tests (`tests/test_monorepos.py` and the
  starter matrix), unedited, pass with the CI marker they run under. Fails against T002's narrow choice: a project with
  a transport still carries today's text and no stamp step, so the widened examples (the transport's line cut by
  `./init`, several services) fail.

**GREEN (the class):** every combination the catalog offers (each backend, with and without a transport, one and several
services) takes the stamped rule and is held by one example over the catalog, not by a hand-picked instance; sweep every
place that edits the `verify` line (`makefile.py`, the init cutter, `migrate`) for text that names `verify:` and still
expects prerequisites on it, and report each.

**REFACTOR:** `gate_target` has one decision (wrapped application or not); the shape-guard of T002 is deleted.

**Verify:** `make test TESTS="test_verify_stamp_pinned test_verify_stamp_ships test_monorepos test_toolkit test_init"`, then
`make lint typecheck check-structure`. Commit (`Level MINOR; VERSION already 1.6.0.dev0`).

**Files:** `src/slipwai/project/gate.py`, `src/slipwai/project/makefile.py`, `src/slipwai/project/adopted_targets.py`,
whatever the sweep names in `src/slipwai/` (each in the report), `tests/stamp_fixture.py` (additions only),
`tests/test_verify_stamp_ships.py` (new).

### T014 — [US3] The page and the fragment say it (R13 · AC-S03-25, -30, -31)

- [x] **Rule R13.** Carries **research item 7**: finds the page a generated project gets about its gate (search for
  *Full deterministic* and `make verify` under `src/slipwai/project/` — `readme`, `rules`, the toolkit's `docs/` — and
  `docs/learn-generate.md` where the reuse line belongs) and writes there: `VERIFY_FORCE`'s default and the one sentence
  on how to run the gate anyway; what a stamp cannot see (a tool a recipe pins, a service outside the checkout, the
  network); that the trunk, CI and `make ci` always run the full gate. Completes `changelog.d/verify-stamp.md`, first
  line still `MINOR`: nothing is asked of an existing project — `slipwai migrate` brings the new `Makefile` and script,
  `.gitignore` is unchanged, the first run is a full one. Test module `tests/test_verify_stamp_ships.py`.

**RED:**
- e25 each sentence of the page and the fragment followed as written: `VERIFY_FORCE`, its default and the sentence are in
  the generated page. Fails today: absent.
- e31 the fragment: first line `MINOR`, the catch-up sentence present, `VERSION` reads `1.6.0.dev0`, and
  `make test TESTS="test_changelog"` is green (a hold on the arithmetic, observed passing, teeth shown by changing the
  first line).
- e30 `slipwai migrate` over a project generated before: the new `Makefile` and `scripts/verify-stamp.py` arrive,
  `.gitignore` unchanged, the first run is full (the project's gate runs every check and writes a stamp). Fails if
  research item 6's list missed the migrate path.

**GREEN (the class):** every place the page says what `make verify` does (sweep: the generated README, the rules, the
toolkit's docs, `docs/learn-generate.md`) agrees; the fragment's final form.

**REFACTOR:** none.

**Verify:** `make test TESTS="test_verify_stamp_ships test_changelog test_toolkit test_migrate"`, then
`make lint typecheck check-structure`. Commit (`Level MINOR; VERSION already 1.6.0.dev0`).

**Files:** `changelog.d/verify-stamp.md`, the page research item 7 finds (named in the report; expected under
`src/slipwai/project/`), `docs/learn-generate.md` (only if the reuse line belongs there), `tests/test_verify_stamp_ships.py`.
If that file nears 350 lines, R13's examples move to `tests/test_verify_stamp_page.py` (new), named in the report.

---

## Phase 4: Gates

### T015 — The slice's neighbouring suites, then the lint, type and structure gates (closing task before convergence)

- [x] *(Run by the host at `dc02731`, cruise iteration 11: the thirteen `test_verify_stamp_*` modules with `test_toolkit`,
  `test_utf8_io`, `test_changelog`, `test_migrate`, `test_backend_obligations`, `test_monorepos` and `test_layout` — 179 tests, OK,
  one skip in `test_changelog` that is not this slice's; `test_init` and `test_check_slice_scope` do not exist, `test_layout` and,
  inside T008, `test_slice_scope_base` and `test_slice_scope_root` stood in; `make lint typecheck check-structure` green; no change
  required.)* `make test TESTS="test_toolkit test_monorepos test_changelog test_migrate test_init test_check_slice_scope"` and the
  nine `test_verify_stamp_*` modules green, then `make lint typecheck check-structure`. No file over 350 lines under
  `src/` or `tests/`; `verify-stamp.py` is wholly the owner of the key and the stamp (no second copy of the lists in
  `gate.py` or a test). If any of this fails, the delegate stops and reports which task's change broke it; it does not
  edit a file outside this slice's manifests. Commit only if the run required a change, by path.

**Host's, after T015 (Principle XIV):**
- **The demo** (AC-S03-20): `drive-hand` follows [quickstart.md](quickstart.md) on the Independent Test's project with the
  real toolchain and writes the measured time, command and machine; the suite never asserts it.
- **Adversary** (`drive-adversary`): the seams the plan's rules name — the key's inputs, the stamp's file, the recipe under
  make's modes — findings become failing tests and fixes as tasks below this line.
- **Mutation:** `make -f delivery/Makefile mutation` where a command is recorded in `project.json`; otherwise N/A and
  teeth shown by hand per hold.
- **Both full gates**, one after the other, on the final tip: `make verify` and `make -f delivery/Makefile verify`.
- **The register row** and the benchmark closed.

---

## Phase 4: Convergence passes

*(appended by `drive-converge`)*

### Pass 1 (2026-10-04, at `c53a9ab`)

Every finding below was reproduced on a scratch project under `/tmp/s03c` — the fixture of `tests/stamp_fixture.py` with
its stand-in tools, or a project generated with `./slipwai generate … --skip-checks` — unless it says otherwise. The 134
tests of the thirteen `test_verify_stamp_*` modules are green at this tip, and five mutations of
`assets/toolkit/scripts/verify-stamp.py` (the trunk not excluded, `record` ignoring a moved key, the stamp not removed
before the checks, `-i` not declining, the `CI` marker dropped) each fail them; the file was restored with
`git checkout --` after each.

#### T016 — `CRITICAL` — The trunk reads and writes a stamp when a pull-request target variable is set (AC-S03-21, D74 R2, constitution I)

- [x] *(done at `6bab49c`: the trunk's name is taken from D30 and D33's resolution alone; RED was four subtests on `main` with each target variable)* Evidence: `trunk_name()` (`verify-stamp.py` 456–470) returns `merge_base().trunk` of `check-slice-scope.py`, and that
  field is *the name the branch is compared with*, not the trunk: where `GITHUB_BASE_REF` or
  `CI_MERGE_REQUEST_TARGET_BRANCH_NAME` names a branch whose base is older than the trunk's, `merge_base()` returns
  `Base(chosen, target[0], …, True)` (`check-slice-scope.py` 365–376, 470–484). Reproduced on the fixture: on `main`, with a
  branch `release` left one commit behind and no CI marker, plain `make verify` twice ran 7 checks each time and wrote no
  stamp; `GITHUB_BASE_REF=release make verify` twice printed `verify: all gates passed` and left
  `.git/slipwai/verify-stamp-e3b0c44298fc1c14.json`, then `verify: the full gate did not run; this tree already passed it
  at 2026-10-04T03:23:40Z (key 1b9df918d9f9); …`, exit 0, 0 checks. The same with
  `CI_MERGE_REQUEST_TARGET_BRANCH_NAME=release`. The reach is a run with one of those two variables and none of the three
  CI markers — a forge's runner sets both, so this is a hand-set variable, a container step handed part of the
  environment, or a local replay of a pull request — but on that run the merge root does not run the full gate, which is
  the constitution's MUST (Principle I, line 33) and the one place D74 says *never*.

**RED:** in `tests/test_verify_stamp_where.py`: on the trunk with a planted stamp and each of the two target variables
naming a branch that exists and is older, every check runs, the planted stamp's bytes are unchanged, no line is added;
the same where the target shares no history with the branch (`Base(None, target[0], True, …)`), and where it names a
branch with no ref.

**GREEN (the class, not the instance):** the stamp asks for *the trunk's name* — D30's and D33's resolution with no
target in it — from one definition `check-slice-scope.py` owns and both callers use, never for the name a comparison was
made against. Sweep every return of `merge_base()` (there are five) and say for each what `.trunk` holds and which
example holds the stamp's answer there; sweep `eligible()` for any other answer that an environment variable can move.

**Files:** `assets/toolkit/scripts/verify-stamp.py`, `assets/toolkit/scripts/check-slice-scope.py` (if the resolution is
split out there), `tests/test_verify_stamp_where.py`.

#### T017 — `HIGH` — A check reads an ignored directory that is on no list, and the closed-list test cannot see the script that reads it (AC-S03-7, D73 rule 5)

- [x] *(done at `5d8f58e`: `.delivery-tools/` is in the key; the scan derives every script the gate launches from the generated Makefile of seven shapes and follows imports (`tests/test_verify_stamp_scan.py`))* Evidence: (a) `scripts/event-model/check.py` — `check-model`, a prerequisite of `verify-checks` in every
  event-modelling project — puts `.delivery-tools/` first on `sys.path` and imports `yaml` from it (lines 33, 62–64);
  `.gitignore` ignores `.delivery-tools/`, the gate installs into it only on an `ImportError`, never from a lock on every
  run, and `IGNORED_INPUTS` does not name it. On a generated project (event-modelling, TypeScript, react-vite) on branch
  `topic`: the key was `0868ce020cf0` before and after writing `.delivery-tools/yaml.py`, while `python3
  scripts/event-model/check.py` went from `check-model: valid`, exit 0, to exit 1; with a stamp planted for the tree as
  `plant_stamp` writes one, `make verify` printed the reuse line and exited 0 while `make check-model` exited 2. A reused
  stamp stood for a gate that fails if it runs. (The stamp was planted, not earned: that project's real gate needs
  `npm ci` from the network.) (b) `tests/test_verify_stamp_lists.py` reads `scripts/check-*.py` only (`unlisted`, the
  `glob` at its line 88), on one project shape. With `os.environ.get("A_NEW_SWITCH")` and a read of
  `.pytest_cache/v/cache/lastfailed` appended to six scripts the gate runs — `scripts/extensions/project.py`,
  `scripts/agents/project.py`, `scripts/agents/code_index.py` (which `check-codegraph.py` imports),
  `scripts/event-model/check.py`, `scripts/test_benchmark.py`, `scripts/extensions/uipro/init.py` — `unlisted()` returned
  `[]`. A sweep by hand of every environment read under `assets/` found no variable a stamped gate's check reads that
  `VARIABLES` lacks today, so (b) is a guard with a hole, and (a) is what came through it.

**RED:** the key moves when a file under `.delivery-tools/` appears, changes or goes (`tests/test_verify_stamp_inputs.py`,
beside the other ignored inputs); the closed-list test fails on a read planted in each script the gate runs that is not
named `check-*.py`, on a project that has `check-model`, `check-drawio` and `check-styles`.

**GREEN (the class):** the scan's subject is *every Python script a prerequisite of `verify-checks` runs or imports*, in
every project shape that adds a prerequisite — derived from the generated `Makefile`'s recipes, not from a file-name
pattern — plus the targets' and the extensions' check scripts; each ignore line of each shape's `.gitignore` is either on
`IGNORED_INPUTS`, rebuilt by the recipe on every run, or exempt with its reason in the test. What the scan cannot read (a
shell script, the `.ts` checks) is listed in the test by name with the reason it holds nothing, so a new one fails it.

**Files:** `assets/toolkit/scripts/verify-stamp.py` (the list), `tests/test_verify_stamp_lists.py`,
`tests/test_verify_stamp_inputs.py`, `tests/stamp_fixture.py` if a second shape is generated.

#### T018 — `HIGH` — The page says three things a stamp cannot see, and AC-S03-31 names five others and a consequence (AC-S03-31, D73 residual)

- [x] *(done at `391a91c`: the page and the fragment carry the five, the consequence and where it is caught)* Evidence: the page `src/slipwai/project/docs.py` writes (lines 116–124) says *a tool a recipe fetches at a version of
  its own, a service outside the checkout, or the network; when a check depends on one, run the gate forced*. AC-S03-31
  requires the clock, the network, user-level tool configuration, `PATH`, and a variable no gate script names; that a
  gate failing for one of those alone *is reused as green until a file, a ref or a listed input moves or `VERIFY_FORCE`
  is given*; and that CI and the trunk are where it is caught. Four of the five are absent, as is the consequence and the
  catch; `changelog.d/verify-stamp.md` carries the same shorter sentence, and
  `tests/test_verify_stamp_ships.py` 155–163 pins the shorter sentence, so the suite holds the page to less than the
  criterion. The blind spot is real and one command away: on a stamped fixture, `STANDIN_UV_FAIL=1 make verify` printed
  the reuse line, exit 0, 0 checks, and `STANDIN_UV_FAIL=1 make verify VERIFY_FORCE=1` failed at `lint`, exit 2. (The
  page's *a tool a recipe fetches at a version of its own* is T017's `.delivery-tools/`, which D73 rule 5 puts in the
  key rather than in the residual.)

**RED:** the ships test asserts each of the five by name, the *reused as green until …* consequence, and CI and the
trunk as where it is caught — on the generated page, and the fragment's sentence against the same list.

**GREEN (the class):** every place a person reads what a stamp cannot see — the page, the fragment, `docs/learn-generate.md`'s
pointer — says D73's residual in full or points at the page that does; none carries a shorter list of its own.

**Files:** `src/slipwai/project/docs.py`, `changelog.d/verify-stamp.md`, `tests/test_verify_stamp_ships.py`.

#### T019 — `MEDIUM` — A gate that fails while git cannot answer leaves the earlier stamp, which is then reused (AC-S03-26, AC-S03-10, D73 rule 8)

- [x] *(done at `a761dce`: a run that ignores errors, or tightens the ratchet, removes the stamp before its checks; an unforeseen failure of `reuse` removes it too. Left, by D79: where git cannot answer, the stamp's place cannot be asked and it stands)* Evidence: on a stamped fixture with a `git` first on `PATH` that exits 128 (`fatal: detected dubious ownership in
  repository`) and `STANDIN_UV_FAIL=1`: `verify: the full gate runs and this run records nothing — git symbolic-ref -q
  --short HEAD: fatal: …`, `lint` failed, exit 2, and `.git/slipwai/verify-stamp-e3b0c44298fc1c14.json` was still there;
  the next plain run printed the reuse line, exit 0, 0 checks. `begin_full_run` (529–549) takes `remove_stamp()` raising
  `CannotTell` as *nothing to remove*. The same shape under `-i`: `STANDIN_UV_FAIL=1 make -i verify` on a stamped tree
  ran the checks, and the stamp stood (`declined()` returns before anything is removed). Both leave a stamp only for the
  key that did pass, so neither vouches for a changed tree — which is why this is not `HIGH` — but AC-S03-26's *after a
  run that failed … no stamp exists for any key* and D73 rule 8's *`make -i verify` on a failing tree must leave no stamp*
  are not what happens when a stamp was there first.

**RED:** a stamped tree, git failing, the gate failing: no stamp afterwards (or the criterion's sentence narrowed, by a
decision, to what a run that cannot find the git directory can do); a stamped tree, `make -i verify` with a failing
check: no stamp afterwards.

**GREEN (the class):** sweep every return of `reuse` that sends the run on to the checks — declined, not eligible,
cannot tell, an unexpected exception (`main`'s `except Exception`), forced, no match — and say for each whether a stamp
that stood is removed, left by D74 R5, or left for a reason a decision names. Where it cannot be removed because git
cannot say where it is, the question of finding it another way is the host's to decide, not the delegate's.

**Files:** `assets/toolkit/scripts/verify-stamp.py`, `tests/test_verify_stamp_runs.py`, `tests/test_verify_stamp_cannot.py`.

#### T020 — `MEDIUM` — The note a full run leaves under the git directory can hold an absolute path (constitution, *Additional Constraints*: persisted data)

- [x] *(done at `df58e2a`: the note holds a marker or the key and tool lines, never the reason's words)* Evidence: with a non-empty directory at the stamp's path, after `make verify` the file
  `.git/slipwai/verify-stamp-e3b0c44298fc1c14.pending` held `{"nothing": "cannot remove
  /tmp/s03c/project/.git/slipwai/verify-stamp-e3b0c44298fc1c14.json (Directory not empty); delete that file"}` —
  `begin_full_run` writes the printed reason into the note (line 542). The stamp itself holds none (`project_name()`,
  385–388, is a digest so that *the file holds no path*), and the constitution's line 480–481 says persisted data MUST
  NOT carry file paths. git's own reasons (`fatal: not a git repository …: /abs/path`) take the same route. The note is
  read only for the presence of its `nothing` field.

**RED:** after each cannot-tell run the suite drives (`tests/test_verify_stamp_cannot.py`, `_tools.py`, `_file.py`), no
file under `.git/slipwai/` contains the scratch directory's path or the reason's text.

**GREEN (the class):** what is written under `.git/slipwai/` is a closed set of fields — the key, the parts, the tools'
lines, the instant, the result, and a marker that the run records nothing — and no free text; sweep both `write_file`
calls.

**Files:** `assets/toolkit/scripts/verify-stamp.py`, the three test modules named.

#### T021 — `LOW` — Lines that say something other than what happened

- [x] *(closed by T034 and T032 (D81))* Evidence: (a) a Go project generated here (`--backend go --frontend none`), branch `topic`, real toolchain: the first
  `make verify` ended `verify: all gates passed` / `verify: this pass was not recorded — the tree changed while the checks
  ran`, and `git status --short` showed `?? go.work.sum`, which the gate's own `go` wrote; the second run recorded and the
  third was reused. Nobody changed the tree. AC-S03-11 is met; the line sends a person looking for an edit they did not
  make. (b) A non-empty directory at the stamp's path is named and not removed (AC-S03-26's branch, and the run is full
  every time until it is deleted — safe), and the line ends *delete that file* for a directory. (c) On the Java backend
  the key asks the `java` on `PATH`, and `mvnw` runs `JAVA_HOME`'s where it is set: **not reproduced**, read from the
  wrapper; D75 names `java`, so this is the residual's *a variable no gate script names* and belongs in T018's page.

**RED/GREEN (the class):** each `NOT_RECORDED_LINE` and `CANNOT_LINE` reason, against what a person would do on reading
it: the moved-key reason names a path that differs where one can be found cheaply; *file* is *file or directory*.

**Files:** `assets/toolkit/scripts/verify-stamp.py`, `tests/test_verify_stamp_runs.py`.

#### T022 — `LOW` — A project in a subdirectory of its repository: a sibling's uncommitted edit is not in the key (D36; **not reproduced as a failing gate**)

- [ ] Evidence: the fixture copied to `proj/` of a new repository beside a tracked `sibling.txt`, branch `topic`: the key
  was `bf2b84264d20` before and after an uncommitted edit to `../sibling.txt`, while `git diff --name-status main` run
  from `proj/` — the call `changed_files()` of `check-slice-scope.py` makes — printed `M sibling.txt`. Whether any check's
  verdict moves on that path was not shown; D36 says only changes under the project's directory are looked at.

**RED/GREEN (the class):** decide, from `check-slice-scope.py`, `check-migrations.py` and the targets' `check-flags.py`,
whether any git question a check asks is answered repository-wide; where one is, the key's tracked-file part covers
what that question covers, and where none is, a test says so.

**Files:** `tests/test_verify_stamp_file.py` or `_key.py`; the script only if a check is found to read above the project.

#### T023 — `LOW` — `verify-stamp.py` is 643 lines in one file (owner brief, *Taste*)

- [x] *(placed by D81: `S04`, the first slice to change the script next, splits it (Parking Lot); not done here)* Evidence: `wc -l assets/toolkit/scripts/verify-stamp.py` → 643. It holds four things with their own reasons to
  change: the two closed lists, the key (git, files, tools), the stamp's file (path, read, write, remove), and the two
  verbs with make's modes. The lists are what T017's test imports.

**GREEN:** split along that structure only if the script stays one thing `slipwai migrate` delivers and the `Makefile`
calls by one path, and the closed-list test still imports the lists from where they are defined; otherwise leave it and
say why here.

**Files:** `assets/toolkit/scripts/verify-stamp.py` and whatever beside it the split names; `delivery/.written` is not
edited by hand.

### Pass 2 (2026-10-04, at `9195588`)

Pass 1's five reproductions were run again as written, on the fixture of `tests/stamp_fixture.py` copied to
`/tmp/s03p2/fx` with its stand-in tools. T016: on `main` with `release` one commit behind, `GITHUB_BASE_REF=release` and
`CI_MERGE_REQUEST_TARGET_BRANCH_NAME=release` each ran 24 checks twice, no reuse line, and the stamp of `topic` kept its
bytes. T017: the key moved when `.delivery-tools/yaml.py` appeared, changed and went, and
`test_verify_stamp_scan` (five tests, seven shapes, a read planted in every derived script) is green. T018: the page and
the fragment carry the five, the consequence and the catch. T019: `STANDIN_UV_FAIL=1 make -i verify` on a stamped tree
left only the `.pending` note; with a `git` that exits 128 the stamp stood and was reused afterwards, which is D79's case.
T020: the note held `{"nothing": true}` after each cannot-tell run and no file under `.git/slipwai/` held `/tmp` or
`/home`. What follows is what those fixes left open or opened. The fourteen `test_verify_stamp_*` modules ran 147 tests at
this tip: 145 pass, two do not (T024).

#### T024 — `CRITICAL` — The slice's own suite is red at this tip: T019's fix changed what a ratchet run does and two T007 tests, the plan and AC-S03-9 still say the opposite (AC-S03-9, AC-S03-26, constitution I and XIV)

- [x] *(done at `54adcac`: a ratchet run touches nothing (D80); T019's example for it corrected; all fourteen stamp modules green)* Evidence: `PYTHONPATH=src:tests python3 -m unittest test_verify_stamp_inputs.RatchetTest` at `9195588` →
  `ERROR: test_a_run_that_tightens_the_ratchet_reads_no_stamp` (`FileNotFoundError` on the stamp at
  `tests/test_verify_stamp_inputs.py` 196: the test asserts *the stamp's bytes stand*) and
  `FAIL: test_a_run_that_tightens_the_ratchet_writes_no_stamp` (`['verify-stamp-e3b0c44298fc1c14.pending'] != []`, line
  203: *no note is left*); `Ran 2 tests … FAILED (failures=1, errors=1)`, the same twice in the run of all fourteen
  modules (147 tests). `a761dce` (T019) made `reuse` send a declined run through `begin_full_run`
  (`verify-stamp.py` 569–572), which removes the stamp and leaves the note, for `-i` *and* for `RATCHET_TIGHTEN`; it
  touched `tests/test_verify_stamp_runs.py` only. On the fixture: a stamped tree, `RATCHET_TIGHTEN=1 make verify` → 24
  checks, and `.git/slipwai/` held only `verify-stamp-….pending`. AC-S03-9 says such a run *neither reads nor writes a
  stamp*, `plan.md` line 40 (e9) *reads and writes nothing* and line 84 *say nothing, touch nothing*; AC-S03-26 names
  only make's ignore-errors mode as removing. The factory's `make verify` cannot pass with these two tests red, so the
  slice cannot be pushed as it stands, and which of the two behaviours is right is not written anywhere.

**RED:** it is already red — the two tests above.

**GREEN (the class, not the instance):** one statement of what each declined run does to a stamp that stood — `-i`, and a
ratchet run — in AC-S03-9, AC-S03-26, the plan's e9 and line 84, the script's docstrings (`declined`, 510–514, still
says *neither reads nor writes*) and the tests, all saying the same thing. Whether a ratchet run removes the stamp
(T019's reading: its checks may rewrite the tree) or leaves it (AC-S03-9's words) is the host's to decide; either way no
test asserts the other. Sweep: run all fourteen `test_verify_stamp_*` modules after every change to
`verify-stamp.py`, not the module the task names.

**Files:** `tests/test_verify_stamp_inputs.py`, `assets/toolkit/scripts/verify-stamp.py` (if the decision is to leave the
stamp), `specs/001-faster-slipwai/spec.md` and `plan.md` (the host's).

#### T025 — `CRITICAL` — The trunk reads and writes a stamp where its short name is ambiguous: a tag named `main` (AC-S03-21, D74 R2, constitution I — T016's class, another route)

- [x] *(done at `534f4d2`: the trunk is recognised by `refs/heads/<trunk>`, never a short name; left for Phase 4's triage: `current_branch()` in `check-slice-scope.py` reads a short name, older than this slice)* Evidence: `eligible()` (`verify-stamp.py` 487–488) compares `git symbolic-ref -q --short HEAD` with the trunk's
  name. git shortens a branch only as far as the name stays unambiguous: on the fixture, on `main`, after `git tag main`,
  `git symbolic-ref -q --short HEAD` prints `heads/main`, which is not `main`. Before the tag, two plain `make verify`
  runs on `main` ran 24 checks each. After it: the first ran 24 checks, `verify: all gates passed`, and wrote the stamp;
  the second printed `verify: the full gate did not run; this tree already passed it at 2026-10-04T03:53:37Z (key
  7f969efa87e7); VERIFY_FORCE=1 runs it anyway`, exit 0, 0 checks. A ref `refs/remotes/main` did not do it (24 checks
  twice). The reach is a repository that has a tag (or any ref git's shortening rules weigh) with the trunk's name — rare,
  and git warns of it on every checkout — but it holds for every run on that trunk by everyone who fetched the tag, with
  no variable set; CI stays behind its markers. Graded as pass 1 graded T016, for the same reason: the merge root does
  not run the full gate, which is the one place D74 says *never*.

**RED:** in `tests/test_verify_stamp_where.py`: on the trunk with a planted stamp and a tag of the trunk's name, every
check runs, the planted stamp's bytes are unchanged and no line is added; the same on `master` as the trunk with a tag
`master`, and where `ci.branch` names the trunk and a tag has that name.

**GREEN (the class):** the branch is read as a full ref name (`git symbolic-ref -q HEAD`, as `history_digest` already
does at line 308) and compared as `refs/heads/<trunk>`; no answer `eligible()` gives depends on how git abbreviates a
name. Sweep every `--short`, `--abbrev-ref` and bare branch name the stamp script compares, and say for
`check-slice-scope.py`'s own reading of the current branch whether the same ambiguity moves it.

**Files:** `assets/toolkit/scripts/verify-stamp.py`, `tests/test_verify_stamp_where.py`.

#### T026 — `MEDIUM` — A tool whose first line is not its version: the version is not in the key, and the line persisted can hold a path (AC-S03-15, D75; constitution, *Additional Constraints*: persisted data)

- [x] *(done at `c304510`: a tool's whole answer on both streams is in the key (D80); the stamp shows one line per tool with path-like words replaced)* Evidence: `ask()` (`verify-stamp.py` 313–339) takes the first non-empty line of standard output and standard error
  together. On this machine `JAVA_TOOL_OPTIONS=-Djava.io.tmpdir=/home/someone/tmp java -version 2>&1 | head -1` prints
  `Picked up JAVA_TOOL_OPTIONS: -Djava.io.tmpdir=/home/someone/tmp`; the version (`openjdk version "25.0.4.1" …`) is on a
  later line. With the stand-in: `STANDIN_UV_VERSION='warning: something\nuv 0.12.20' make verify` stamped, and the next
  run with `…\nuv 0.99.0` printed the reuse line, exit 0, 0 checks — the stamp's `tools` held `"uv": "warning:
  something"`. And `STANDIN_UV_VERSION='warning: cache at /home/someone/.cache/uv'` left that line, path and all, in
  `.git/slipwai/verify-stamp-….json`. So on a Java project whose developer has `JAVA_TOOL_OPTIONS` or `_JAVA_OPTIONS`
  set, a changed JDK does not move the key — a reused stamp can stand for a gate the new JDK fails — and the stamp
  carries whatever that variable holds. **Not reproduced through a generated Java project's gate**: the `java` line and
  the stand-in were each shown, the two together were not.

**RED:** in `tests/test_verify_stamp_tools.py`: a tool that prints a notice line before its version — the version on the
second line changes, the full gate runs; and no file under `.git/slipwai/` holds a path the tool printed.

**GREEN (the class):** what the key takes from a tool is every line it prints when asked (or a digest of them), so a
notice ahead of the version cannot hide it; what the stamp *stores* per tool is a fact true on any machine, or a digest.
D75 rule 4 says *the first non-empty line, whole*, so the change of wording there is the host's. Sweep each tool of
`MACHINE_TOOLS` for what it prints ahead of its version under a common variable (`JAVA_TOOL_OPTIONS`, npm's `npm warn`
on an unknown configuration, uv's warnings).

**Files:** `assets/toolkit/scripts/verify-stamp.py`, `tests/test_verify_stamp_tools.py`.

#### T027 — `LOW` — Two more runs that start checks with a stamp left standing, which AC-S03-26 does not name (AC-S03-26, D79)

- [x] *(closed by T034's holds and AC-S03-26's reading (D81))* Evidence: AC-S03-26 says *the one case where a stamp that stood is left is AC-S03-13's git that cannot answer*.
  (a) On a stamped fixture with `scripts/check-slice-scope.py` moved away and `STANDIN_UV_FAIL=1`: `lint` failed, exit 2,
  no line, and `.git/slipwai/verify-stamp-e3b0c44298fc1c14.json` was still there; with the script back, the next run
  printed the reuse line, exit 0, 0 checks. `trunk_name()` raises something other than `CannotTell`, `main` calls
  `remove_after_failure()`, which asks `eligible()` again, which raises again, and nothing is removed (645–652). (b)
  **Not reproduced**, read from `main` 658–659 and the recipe: a `python3` older than 3.10, or none on `PATH`, sends the
  run to the checks before anything is asked. In each the stamp left is for a key that passed and the tree that failed
  was a different one, which is D79's argument and why this is `LOW`.

**RED/GREEN (the class):** every exit of `main` that sends a run to the checks either removes a stamp that stood or is
named in AC-S03-26 beside git's; where eligibility cannot be told for a reason that is not git's, say which.

**Files:** `assets/toolkit/scripts/verify-stamp.py`, `tests/test_verify_stamp_runs.py`; the criterion's sentence is the host's.

#### T028 — `LOW` — The page says how to force and not when (AC-S03-25)

- [x] *(closed by T035 (D81))* Evidence: AC-S03-25 asks the page for the default *and one sentence on when to set it*. The page
  (`src/slipwai/project/docs.py` 116–126) has *To run the gate anyway, run `make verify VERIFY_FORCE=1`* and, three
  sentences on, *reused as green until … `VERIFY_FORCE` is given*; `391a91c` took out pass 1's *when a check depends on
  one, run the gate forced*. `tests/test_verify_stamp_ships.py` 146 pins the *how* sentence. The page also opens *keyed by
  everything the checks answer from* and then says what the key cannot see, and says a marker *set* where the code means
  non-empty (`eligible`, 485).

**RED/GREEN (the class):** the page has one sentence that says when — a check that answers from one of the five — and no
sentence that claims more than the residual allows; the ships test holds it.

**Files:** `src/slipwai/project/docs.py`, `tests/test_verify_stamp_ships.py`.

### Pass 3 (2026-10-04, at `0c78c0c`)

Pass 2's three reproductions were run again as written, on the fixture of `tests/stamp_fixture.py` copied to
`/tmp/s03p3/` with its stand-in tools. **T024:** the fourteen `test_verify_stamp_*` modules through `make test TESTS=…`
→ `Ran 155 tests … OK`; on a stamped tree `RATCHET_TIGHTEN=1 make verify` (and `make verify RATCHET_TIGHTEN=1`) ran 24
checks, printed no line, left the stamp's bytes as they were (same SHA-256 before and after) and no `.pending`, and the
next plain run printed the reuse line; with no stamp, two ratchet runs left `.git/slipwai/` absent. **T025:** on `main`
with a tag `main` (`git symbolic-ref -q --short HEAD` → `heads/main`), two plain runs ran 24 checks each and wrote
nothing; a stamp planted valid for that tree kept its bytes and was not reused. The same with `master` as the trunk and
a tag `master`, with `ci.branch` naming `develop` and a tag `develop`, with `ci.branch` spelled `refs/heads/develop`,
under each of `CI=false`, `GITHUB_ACTIONS=true`, `GITLAB_CI=1` and `make verify CI=1`, and on a detached `HEAD`: 24
checks, no line, the planted stamp's bytes unchanged. `eligible()` (`verify-stamp.py` 488–496) compares the full ref
with `refs/heads/<named>`; `merge_base()` in `check-slice-scope.py` (443–493) answers from `bases_of` (336–358), full
ref names only, and never calls `current_branch()`. **T026:** `STANDIN_UV_VERSION='warning: something\nuv 0.12.20'`
stamped and was reused; with `…\nuv 0.99.0` the run ran 24 checks and wrote a new stamp (`[answer 10e5cfba…]` became
`[answer 19a9b3a8…]`); a notice on standard error that changed did the same; `'warning: cache at
/home/someone/.cache/uv'` is stored as `warning: cache at <path> [answer 1dd79d6911fbbee7]` and no file under
`.git/slipwai/` holds `/home`, `/tmp` or `someone`. The regression look: with the real `uv` 0.12.20, `git` 2.53.0 and GNU
Make 4.4.1 the fixture's gate passed and stamped, and the two runs after it each printed the reuse line for one key
(`91feb4e7a4da`); `make -i verify` left only the `{"nothing": true}` note. No `CRITICAL` and no `HIGH`: what follows
is Phase 4's.

#### T029 — `LOW` — A ratchet run under make's ignore-errors mode leaves the stamp, which AC-S03-26 says such a run removes (AC-S03-26, D80)

- [x] *(closed by T034's hold and AC-S03-26's reading (D81))* Evidence: `reuse` asks `ratcheting()` before `declined()` (`verify-stamp.py` 583–588), so with both set the
  ratchet rule wins. On a stamped fixture, `RATCHET_TIGHTEN=1 STANDIN_UV_FAIL=1 make -i verify` → exit 0, 23 checks,
  `verify: all gates passed`, the stamp still there; the next plain run printed the reuse line, 0 checks. AC-S03-26 says
  *a run under make's ignore-errors mode removes the stamp too*; D80 says a ratchet run *removes none*; neither names
  the run that is both. The stamp left is for a key that passed, which is D79's and D80's own argument, and a ratchet
  run that fails without `-i` leaves it the same way — so `LOW`, a sentence to settle, not a wrong green.

**RED/GREEN (the class):** one sentence, in AC-S03-26 or D80, says which rule holds where a run is both, and one example
in `tests/test_verify_stamp_inputs.py` holds it.

**Files:** `tests/test_verify_stamp_inputs.py`, `assets/toolkit/scripts/verify-stamp.py` (only if `-i` is to win); the
criterion's sentence is the host's.

#### T030 — `LOW` — What the stamp stores of a tool is still a line the tool chose, with paths taken out by a pattern (AC-S03-18; constitution, *Additional Constraints*: persisted data)

- [x] *(closed by T033 (D81))* Evidence: `ask()` stores `PATH_LIKE.sub("<path>", line)` and sixteen hex digits of the answer (`verify-stamp.py`
  131, 342–345). The pattern, asked directly: `cache at C:\Program Files\uv\cache` → `cache at <path> Files\uv\cache`;
  `home=~noah/.cache` and `config,/home/noah/x` come back unchanged; a host name, a user name or a process id in the
  line is not a path and stays. None of the tools of `MACHINE_TOOLS` was seen to print such a first line (the real
  `uv`, `git`, `make`, `python3` and `java` lines here hold none), and T026's own case (`JAVA_TOOL_OPTIONS`) is elided —
  so `LOW`. The stored value also ends ` [answer <digest>]`, where AC-S03-18 says *the line it reported*.

**RED/GREEN (the class):** what is stored per tool cannot carry runtime context whatever the tool prints — the digest
alone with a version read by a pattern that admits only version-like words, or the line printed and not stored — and
AC-S03-18's words say what the field holds.

**Files:** `assets/toolkit/scripts/verify-stamp.py`, `tests/test_verify_stamp_tools.py`; the criterion's sentence is the host's.

---

### After-converge gaps (2026-10-04, at `0d222de`; `drive-gaps` G1–G8, placed by D81)

Placed without code by D81: T022 goes to the adversary pass as a seam (a project in a subdirectory of its repository);
T023 is `S04`'s (Parking Lot); G4, G7 and G8 are Parking Lot and cruise-report lines; G5 and G6 are corrected in
[quickstart.md](quickstart.md). T021, T027, T028, T029 and T030 are closed by the tasks below.

#### T031 — `MEDIUM` — Every machine-supplied tool a recipe of the gate launches is asked (G1 · AC-S03-14, D81)

- [x] *(done at `2fb7004`: `node` and `npm` are asked wherever the gate has the model's checks; `tests/test_verify_stamp_launches.py` derives every command a gate recipe launches in seven shapes)* **RED:** an event-modelling project's `VERIFY_STAMP` asks neither `node` nor `npm`, though `check-drawio`'s recipe
  launches both; and a test over the generated `Makefile` of every shape `tests/test_verify_stamp_scan.py` generates —
  the command each recipe line reachable from the gate launches is on that project's tool list, a file of the project,
  or named in the test with the reason it is pinned — fails today on those two. **GREEN (the class):** a row of the one
  table in `src/slipwai/backends.py`, not a special case in the recipe; the test derives the commands from the recipes,
  so a recipe that later launches another machine tool fails it.

**Files:** `src/slipwai/backends.py`, `src/slipwai/project/gate.py`, `tests/test_verify_stamp_tools.py` or a new
`tests/test_verify_stamp_launches.py`, `tests/test_verify_stamp_ships.py`, `docs/backend-obligations.md` if the table's row changes.

#### T032 — `MEDIUM` — The JVM asked is the one the wrapper would run (G2, T021's third item · AC-S03-14, -17, D81)

- [x] *(done at `cca6b04`: the JVM asked is `JAVA_HOME`'s where set, else the one on `PATH`; the scan names each shell script's selecting variables)* **RED:** with `JAVA_HOME` naming a JVM that reports another version than the `java` on `PATH`, a stamped Java
  project is reused today. **GREEN:** `JAVA_HOME`'s `bin/java` is asked where the variable is non-empty, else the one on
  `PATH`; one that cannot be launched is AC-S03-17's case; the variable's value is in neither key nor stamp. The
  closed-list test stops saying the wrapper and each backend's `scripts/verify` *hold nothing*: each shell script the
  scan cannot read is named with the variables that select which executable runs, and such a variable either decides
  which tool is asked or fails the test.

**Files:** `assets/toolkit/scripts/verify-stamp.py`, `tests/test_verify_stamp_tools.py`, `tests/test_verify_stamp_scan.py`, `tests/stamp_fixture.py` (additions only).

#### T033 — `LOW`, a MUST — What the stamp stores of a tool's answer (T030 · AC-S03-18, D81; constitution, persisted data)

- [x] *(done at `6634452`: a stored tool entry is its version-shaped words and a digest of the whole answer)* **RED:** each of T030's lines (a Windows path with a space, a `~user` path, a path after a comma) and a host name,
  printed by a stand-in tool, is found in a file under the stamp's directory today. **GREEN:** per tool the stamp stores
  its name, the version-shaped words of its answer and the digest of the whole answer — the digest alone where no such
  word is found; the key is unchanged (D80). Closes T030.

**Files:** `assets/toolkit/scripts/verify-stamp.py`, `tests/test_verify_stamp_tools.py`.

#### T034 — `LOW` — Each line says what happened, and the two readings are pinned (T021, T027, T029 · AC-S03-11, -26, D81)

- [x] *(done at `9f462be`: the not-recorded line names the part that moved; a directory is called a directory; three holds with teeth)* **RED:** the *not recorded* line does not say which part of the key moved, nor — where it is the files — that a
  check may have written one, that `git status` shows it and that the next run records; a directory at the stamp's path
  is told *delete that file*. **GREEN:** both, with no list of files kept between the two halves of a run. **Holds,
  pinning what the code already does, each shown to have teeth:** a run that both tightens the ratchet and ignores
  errors touches nothing (T029); a run where the trunk cannot be resolved for a reason that is not git's, and a run
  with no `python3` able to run the script, each leave a stamp that stood (T027). Closes T021, T027, T029.

**Files:** `assets/toolkit/scripts/verify-stamp.py`, `tests/test_verify_stamp_runs.py`, `tests/test_verify_stamp_cannot.py`.

#### T035 — `LOW` — The page and the fragment say when to force and how the trunk is recognised (T028, G3 · AC-S03-25, -30, -31, D81)

- [x] *(done at `ef66461`: the page and the fragment say when to force, how the trunk is recognised and the `ci.branch` catch-up)* **RED:** the page has no sentence on when to force, none on how the trunk is recognised or what a team with another
  trunk name does, says *everything the checks answer from* and *set* of a CI marker; the fragment's catch-up says nothing
  is asked. **GREEN:** the page's three sentences as AC-S03-31 now reads, *non-empty*, and no *everything*; the fragment's
  tool wording (*the tools the machine supplies that the gate launches*), its trunk sentence and its catch-up exception
  (a trunk named neither `main` nor `master` with no `ci.branch` recorded: record it); still MINOR. Each sentence that
  tells a developer to do something is followed by a test — recording `ci.branch` on a `develop` trunk stops the reuse.
  Closes T028.

**Files:** `src/slipwai/project/docs.py`, `changelog.d/verify-stamp.md`, `tests/test_verify_stamp_ships.py` (or a new
`tests/test_verify_stamp_page.py`), `docs/learn-generate.md` if it repeats a corrected sentence.

## Parallel opportunities

- **Nothing here is concurrent.** Every implementation task (T002–T014) writes `assets/toolkit/scripts/verify-stamp.py`
  (T013 and T014 are the exceptions, which write `gate.py` and the page) and every one of them extends
  `tests/stamp_fixture.py`; two delegates would write one file. They run one at a time, in order: T001 (host, Pin),
  T002, T003, T004, T005, T006, T007, T008, T009, T010, T011, T012, T013, T014, T015.
- **No `[P]` is claimed.** T014's page and fragment are disjoint from T013's `gate.py`, but T014 needs T013's widened rule
  before its page is true, and the fragment is T002's file, so it waits.
- **Most delegates at once: one.**
- **Host tasks:** T001 (the Pin, `/characterise`), the demo, the adversary pass, the full gates after T015, the register
  row, and the writing of `tasks.md`.

## Design review

No screen in this slice

## Convergence

**Converged at `0c78c0c` (code tip `c304510`), after three passes** (`drive-converge`, host model, fresh context each).
The bound is two; the third ran only because pass 2 left an open `CRITICAL`, which is the one thing the bound does
not hold against. Pass 1 at `c53a9ab` found one `CRITICAL` (T016: a pull-request target variable let the trunk read
and write a stamp), two `HIGH` (T017: an ignored directory a check reads was on no list and the closed-list test
scanned only `check-*.py`; T018: the page against AC-S03-31), two `MEDIUM` (T019, T020) and three `LOW` (T021–T023).
Pass 2 at `9195588` re-ran those reproductions, found T017, T018 and T020 closed, and found two `CRITICAL` — T024,
the slice's own suite red because T019's fix contradicted AC-S03-9 on a ratchet run (D80 settled it), and T025, a
tag named like the trunk — with one `MEDIUM` (T026) and two `LOW` (T027, T028). Pass 3 re-ran T024–T026's
reproductions, found all three closed, ran the gate twice with the real `uv`, `git` and `make` (one key, the reuse
line twice, 0.31 s), and left two `LOW` (T029, T030). T016–T020 and T024–T026 are done; the seven `LOW` are Phase
4's and do not re-open the loop. The tree was clean after each pass (`git status`: this file and the run's own
records).

**Sweeps performed.** Every route by which the trunk, a run under a CI marker or a detached `HEAD` could read,
write or remove a stamp: the three markers, both target variables, a target with no ref or no shared history, a tag
and a remote ref named like the trunk, `ci.branch` in both spellings (T016, T025). Every script a prerequisite of
the gate launches, derived from the generated `Makefile` of seven project shapes and followed through imports, with
a read planted in each (T017). Every return of `reuse` and `main` that leads to checks, against what it leaves of a
stamp: idle modes, not eligible, ignore-errors, ratchet, cannot tell, unforeseen exception, forced, no match (T019,
T024; D79 leaves one on purpose). Every write under the git directory and every field in it (T020, T026). Five
mutations of the script, each killed by the suite and restored (pass 1).

**Principles the diff touches.**
- **I, a memoised gate MUST be additive; the merge root and CI run the full gate; no check removed:**
  `assets/toolkit/scripts/verify-stamp.py` 488–496 (`eligible()`: the CI markers at 492, the trunk by its full ref
  at 495–496), asked by `reuse` at 581 and `record` at 629; the prerequisites unchanged on `verify-checks` at
  `src/slipwai/project/gate.py` 22–28; held by `tests/test_verify_stamp_where.py` 112–136 and the pin. No file of a
  project's is touched: the stamp's place is `project_name()` at 399–402 under the git directory.
- **V, acceptance-driven:** fourteen `tests/test_verify_stamp_*.py` modules, 155 examples, at `make verify`'s
  command line through stand-in executables (`tests/stamp_fixture.py` 38–73); no mocking framework.
- **VIII, versioning:** `changelog.d/verify-stamp.md` line 1 (`MINOR`); `VERSION` `1.6.0.dev0`; a stamp lacking a
  field is no stamp (`verify-stamp.py`, `FIELDS` and its reader).
- **XIII, fast feedback:** the reuse path at `verify-stamp.py` 583–600 starts no check; no clock in the suite; the
  second is the demo's (AC-S03-20).
- **XIV, the same bar:** increment commits with their tests; the full gates run on the final tip in Phase 4.
- **Additional Constraints, persisted data:** the note holds a marker, never a reason (569); a tool's line is stored
  with path-like words replaced (131, 345); the instant is UTC (648). Residual: T030.

**The map.** `make -f delivery/Makefile check-convergence`: 3 of 9 axes at target, unchanged — this slice reaches no
rung: it changes what the factory generates, and this repository's own gate (an adopted one, D74 and D78) does not
stamp.

**Open, graded, for Phase 4:** T021 (lines that say other than what happened), T022 (a sibling's edit in a
subdirectory project), T023 (the script's length), T027 (two more runs that leave a stamp for a key that passed),
T028 (the page says how to force and not when), T029 (a run that is both ratchet and ignore-errors), T030 (the
stored tool line is free text).
