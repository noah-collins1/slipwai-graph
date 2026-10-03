# Tasks: S01-gate-walks — a generated gate stops reading what it never needed

**Input**: [plan.md](plan.md) (*The example map* R1–R11 is what the tasks cut on; *Design*; *Pin*; *Project
Structure*), [research.md](research.md), [data-model.md](data-model.md), [quickstart.md](quickstart.md); acceptance
criteria AC-S01-1 … AC-S01-22 in `specs/001-faster-slipwai/spec.md` under `### S01-gate-walks`; decisions D7, D9, D12,
D39, D45, D46, D47 in `specs/001-faster-slipwai/decisions.md`. No `examples.md`: a method slice with no screen and no
event model.

**Branch**: `adopt-method` (D12). No `slice/` branch, no push, no claim. One commit per task.

**Delegation**: one delegate per implementation task, each its own RED-GREEN-REFACTOR increment and its own commit.
The "Files" line of a task is its manifest: the only files that delegate may write. Nobody but the host writes
`tasks.md`.

**User stories** (from the plan's example map): **US1** the walking gates, `check-imports.py` and
`check-migrations.py` (R1–R5); **US2** `check-codegraph.py` on a slice branch (R6–R10); **US3** the release (R11).

## Constraints

Constraints that hold for every task, not tasks of their own:

- Every file under `tests/` and `src/` stays within the 350 lines `make check-structure` holds.
- `make lint typecheck check-structure` before each commit.
- RED is seen before the production file is touched. A **hold** (the plan says which) is written as a hold, saying so
  in the test's name or comment, and is observed passing; it is not a RED.
- No mocking framework. Fakes and the audit hook only: the fake `codegraph` CLI already in
  `tests/test_code_index_health.py` (`indexed()`), and `tests/gate_audit.py`.
- The three scripts (`assets/toolkit/scripts/check-imports.py`, `check-migrations.py`, `check-codegraph.py`) each stay
  one standard-library file. The walk helper is duplicated between the two walking scripts, as `project_root()`
  already is.
- Nothing under this repository's `delivery/scripts/`, `tools/`, the `Makefile`, CI or hook settings changes (D9).
  `VERSION` stays `1.5.2.dev0`; nothing under `release/` is edited. A symbolic-link example skips, saying why, where
  the platform cannot make a link.
- **Versioning, on every commit** (`AGENTS.md`): a commit that changes `assets/` states `Level PATCH; VERSION is not
  raised because it already carries the PATCH (1.5.2.dev0) the fragment claims` and names the reason (the same answers,
  generated better); a commit that changes only `tests/` says it reaches no user and so does not raise the number.
  The fragment `changelog.d/gate-walks.md` lands in R11's commit (T013), after the production changes it describes.
  *Open point for the host:* Principle I and `AGENTS.md` ask that the fragment land in the first user-visible commit;
  S23's T002 did that. If the host holds to that here, T003's commit carries a first draft of the fragment and T013
  completes it. As written, T013 owns it because R11 is a rule of its own.
- **Observing a RED.** The failing run is seen, for its stated reason, before the production edit. A test the plan
  marks as green with an earlier rule's change is **seen** failing by reversing that production hunk in the working
  tree, running the test, then restoring with `git checkout -- <exact path>` and confirming `git status` shows only the
  task's own files. The tree is clean of the reversal on every exit path.
- **Quickest test per task:** `make test TESTS="<module>"`, the module each task names.

## Format: `[ID] [P?] [Story] Description` — each task is one increment, one commit

`[P]` marks a task whose files are disjoint from the other story's tasks; it says nothing about tasks inside the same
story, which share a script and run in order. See *Parallel opportunities*.

---

## Phase 1: Setup

### T001 — Pin what the three gates answer today (host task)

- [x] **Host task — not delegated.** Before any production change, in one commit alone:
  1. Write `tests/test_gate_walks_pinned.py` (the Pin stage; plan.md *Pin*). It runs the scripts in a generated
     skeleton (`self.generate(...)`) with a planted violating tree — one for `check-imports`, one for
     `check-migrations` — and asserts findings, their order, the exact bytes on stderr, empty stdout and the exit
     status. **Holds (R4e1, R4e2): green today, observed passing.** Not pinned, because the slice changes it on
     purpose: the pass line's tail, and findings inside a pruned directory.
  2. Append three rows to `delivery/survey/pinned.md`: (1) what `check-imports` prints and exits with on a violating
     tree, held by `tests/test_gate_walks_pinned.py`, `tests/test_gates_imports.py`, `tests/test_gates.py`; (2) the
     same for `check-migrations`, held by `tests/test_gate_walks_pinned.py`, `tests/test_gates.py`,
     `tests/test_go_migrate_embed.py`; (3) what `check-codegraph` answers off a slice branch, held by
     `tests/test_code_index_health.py` (already there, green).
  3. Run `make test TESTS="test_gate_walks_pinned test_gates_imports test_gates test_go_migrate_embed test_code_index_health"`
     green. The commit says no user-visible tree changed, so the number is not raised.

**Files:** `tests/test_gate_walks_pinned.py` (new), `delivery/survey/pinned.md` (the only file under `delivery/` this
slice changes).

### T002 — The audit-hook wrapper both stories use (setup)

- [x] **Setup, no rule.** `tests/gate_audit.py` is a helper with no tests of its own: a small module that builds the
  three-line wrapper a test passes to `python3 -c`. It installs `sys.addaudithook`, records `open` events and
  `os.scandir` events (path, and mode where it matters) to a file or to stderr, then runs the gate script given as
  `argv` (via `runpy`, with `sys.argv` set and `SystemExit` passed through). Its readers return the opened paths
  and listed directories as lists, so a test can ask *was any path inside X listed*, *how many times was
  `project.json` opened*, *which tracked files were opened*. Needs T001 (tree green and committed). Both US1 (R2e4,
  R5) and US2 (R6e1, R7e2) depend on it.

**RED:** none — a helper is not behaviour. It is first exercised, and so first proved, by T004 (R2e4) and T008 (R6e1);
if either finds it wrong, it is corrected in that task's commit and the file is in that task's manifest.
**GREEN:** the module, importable as `from tests.gate_audit import ...` the way the other test helpers are imported
(follow `tests/test_code_index_health.py`'s import style). **REFACTOR:** none.

**Verify:** `make test TESTS="test_gate_walks_pinned"` still green; `make lint typecheck check-structure`. Commit (tests
only: reaches no user).

**Files:** `tests/gate_audit.py` (new).

---

## Phase 2: User Story 1 — the walking gates [US1]

`check-imports.py` and `check-migrations.py`. Rules are sequential inside the story: T003, T004 and T006 edit the
same scripts; T005 and T006 add tests beside them. Needs T001 and T002.

### T003 — [P] [US1] Each directory is listed once, and the pass line says how many entries (R1 · AC-S01-1, -2, -7, -9)

- [x] **Rule R1.** `listing(top)`, the memoised per-top listing in `check-imports`, `check-migrations` using the same
  listing, and the count on the pass line. Test module `tests/test_gate_walks.py` (new).

**RED** (each seen failing for its stated reason before the scripts are touched):
- e1 skeleton → `check-imports` exits 0 and stdout is exactly `check-imports: inward dependency rule holds (N directory
  entries read)`, N ≤ 100 and N equal to the test's own enumeration of `apps/` and `packages/` (79 today's walk
  would read 256). Fails today: the line has no count, and the script lists `apps/` and `packages/` repeatedly.
- e2 skeleton → `check-migrations` stdout is today's sentence, unbroken, then ` (N directory entries read)` with the
  same N. Fails today: no count.
- e3 150 empty files added under `apps/service/src/extra/` → both pass, the count is over 100, stdout is the one
  line and stderr is empty. Fails today: no count to be over 100.
- e4 a project directory holding only `project.json` and `scripts/` → both pass and report `0 directory entries
  read`. Fails today: no count.
- e5 a symbolic link under `apps/service/` to a directory outside `apps/` that holds a `domain/` violation → no finding
  and the count rises by one. Skipped, saying why, where a link cannot be made. Fails today: no count to rise (the
  no-finding half is a hold).

**GREEN** — in each script the small helper from plan.md *Design*: `PRUNED` and `skipped(directory, name)` (at this
increment the four names only; `target` is T005's), `listing(top)` over `os.walk` (top-down, links not followed),
adding `len(dirnames) + len(filenames)` to a module-level count per listed directory and returning every path under
`top`, files and directories, sorted as `sorted(top.rglob("*"))` sorts. `check-imports`: listings memoised by top,
`source_files(layer)` filters the one listing of `apps/` and `packages/`, rules 4 and 5 ask `under(directory)`, which
filters a listing already taken or takes and counts a new one. `check-migrations`: `migrations()` filters
`listing(ROOT / area)`. The pass line gains ` (N directory entries read)`; the failure path is untouched.

**REFACTOR:** one walk helper per script, no more; confirm both copies read alike.

**Verify:** `make test TESTS="test_gate_walks test_gate_walks_pinned test_gates_imports test_gates"`, then `make lint
typecheck check-structure`. Commit, level line (PATCH, `VERSION` not raised).

**Files:** `assets/toolkit/scripts/check-imports.py`, `assets/toolkit/scripts/check-migrations.py`,
`tests/test_gate_walks.py` (new).

### T004 — [P] [US1] Four names are never descended (R2 · AC-S01-3)

- [x] **Rule R2.** `.venv`, `node_modules`, `__pycache__`, `.git`, at any depth, in every walk. Needs T003 (the helper
  and `tests/test_gate_walks.py`). Uses `tests/gate_audit.py` (T002).

**RED** (in `tests/test_gate_walks.py`):
- e1 under `apps/service/`: `.venv/lib/pkg/domain/bad.py` importing an adapter, `node_modules/pkg/migrations/0001_drop.sql`
  with `DROP TABLE`, `src/__pycache__/x.py`, `.git/hooks/x` → both scripts pass and each count is the skeleton's plus
  exactly the number of pruned directories planted. **Fails today only if** the planted directories are descended or
  counted; the pass-or-fail half is seen failing on `.venv` and `node_modules` (T003 already prunes the four names, so
  the failing reason is **seen** by reversing T003's `PRUNED` set to empty in the working tree, running the test, then
  restoring with `git checkout -- assets/toolkit/scripts/check-imports.py assets/toolkit/scripts/check-migrations.py`).
- e2 the same four planted two directories deeper (`apps/service/src/a/b/`) → the same. Seen failing the same way.
- e3 `node_modules/pkg/src/x.ts` importing `apps/service`, planted under `apps/web/` → rule 4 does not report it.
  Seen failing the same way.
- e4 run under the audit hook (`os.scandir` events) → no listing of any path inside a pruned directory. Seen failing
  the same way.

**GREEN** — none in `assets/` if T003's `PRUNED` set already covers the four; this task's increment is the proof, and
it is committed with the reversal seen. The one production edit this task owns: remove `check-migrations`'s own
`"node_modules" not in path.parts` test, now redundant because the walk no longer descends there (plan.md *Design*).
If a test fails with T003 in place for any other reason, stop and report.

**REFACTOR:** none.

**Verify:** `make test TESTS="test_gate_walks test_gates test_go_migrate_embed"`, then `make lint typecheck
check-structure`. Commit, level line (PATCH where the script changed; the commit names the removed redundant test).

**Files:** `assets/toolkit/scripts/check-migrations.py`, `tests/test_gate_walks.py`, `tests/gate_audit.py` (only if
T002's helper is found wanting).

### T005 — [P] [US1] `target` is build output only beside a `pom.xml` (R3 · AC-S01-4, -5)

- [x] **Rule R3.** Maven's directory is skipped; a source directory of that name is read. Needs T004 (helper in both
  scripts). Test module `tests/test_gate_walks_target.py` (new).

**RED:**
- e1 a Java (`java-quarkus`) service with `target/classes/db/migration/V2__drop.sql` (`DROP TABLE`, no marker) and
  `target/generated-sources/domain/Bad.java` importing `jakarta.inject` → both pass and the count rises by one.
  **Fails today**: both files are read and reported, and no `target` is pruned.
- e2 a Python service recording contexts `orders` and `target`: `src/target/domain/bad.py` importing an adapter →
  fails rule 1 naming the file. **A hold: green today and must stay green** once `target` is pruned only beside a
  `pom.xml`; it guards the change from widening into "skip every `target`" (D45).
- e3 the same service: a file under `src/target/` importing `orders.domain` → fails rule 5. **A hold.**
- e4 the same service: `src/target/migrations/0002_drop.sql` → `check-migrations` fails naming it. **A hold.**
- e5 the Java service with a package directory `src/main/java/…/target/` under `domain/` holding a `jakarta` import →
  fails. **A hold** (no `pom.xml` beside that `target`).

**GREEN** — `skipped(directory, name)` in each script is also true for `target` where `directory / "pom.xml"` is a
file. Nothing else.

**REFACTOR:** none.

**Verify:** `make test TESTS="test_gate_walks_target test_gate_walks test_gates"`, then `make lint typecheck
check-structure`. Commit, level line (PATCH, `VERSION` not raised).

**Files:** `assets/toolkit/scripts/check-imports.py`, `assets/toolkit/scripts/check-migrations.py`,
`tests/test_gate_walks_target.py` (new).

### T006 — [P] [US1] `project.json` is opened at most once (R5 · AC-S01-8)

- [x] **Rule R5.** One read per run. Needs T005 (same script). Plan numbers this R5; the rule R4 sits between, see T007.
  Uses `tests/gate_audit.py`.

**RED** (in `tests/test_gate_walks.py`):
- e1 `check-imports` under the audit hook counting `open` events on `project.json`, in a project with a web app and a
  two-context service (every rule that asks the manifest runs) → exactly 1. **Fails today**: the manifest is opened
  more than once (by `deployables()` and `unruled()` and the rules that call them).
- e2 `check-migrations` → 0 or 1. **A hold**: it does not read the manifest today; guards against its gaining a read.
- e3 a tree whose `project.json` is deleted after generation → both answer as today (pass; the rules that need the
  manifest find no applications). **A hold.**

**GREEN** — in `check-imports`, one memoised `manifest()`; `deployables()` and `unruled()` read from it.

**REFACTOR:** none.

**Verify:** `make test TESTS="test_gate_walks test_gate_walks_target test_gates_imports test_gates"`, then `make lint
typecheck check-structure`. Commit, level line (PATCH, `VERSION` not raised).

**Files:** `assets/toolkit/scripts/check-imports.py`, `tests/test_gate_walks.py`.

### T007 — [P] [US1] Findings and failure output are today's (R4 · AC-S01-6)

- [x] **Rule R4 — a hold, checked last in the story.** Same findings, same order, same bytes on stderr, no count.
  e1 and e2 are the pinned tests written at T001, **already green and unchanged**; e3 is five existing modules run
  with no edit. The task writes no new test: a test written now would pass the moment it was written (the rule
  produces no behaviour of its own; the walk change of T003–T006 is what it guards). It sits here, after the walk is
  complete, as the proof the rule's reason requires.

**Checks:**
- e1 `make test TESTS="test_gate_walks_pinned"` green on the pinned `check-imports` tree: stderr and exit unchanged,
  stdout empty. If it fails, the failure is a regression of T003–T006: stop and report; do not edit the pin.
- e2 the same module, the pinned `check-migrations` tree.
- e3 `make test TESTS="test_gates_imports test_gates test_go_migrate_embed test_frontend test_monorepos"` green with
  `git diff` over the slice showing none of the five edited.
- To show e1 and e2 have teeth, reverse the sort in `listing()` in the working tree (return paths unsorted), see
  e1 or e2 fail on order, then restore with `git checkout -- <the exact script path>`.

**GREEN:** none. If a check fails, stop and report. **Commit:** none expected — the task is a checkpoint, and its
evidence is the green run and the teeth check, noted in T003–T006's commit trail. If the host wants a commit per rule,
add the teeth check as a comment-only change to `tests/test_gate_walks_pinned.py`; not required.

**Verify:** the three commands above; `make lint typecheck check-structure`.

**Files:** none (checkpoint).

---

## Phase 3: User Story 2 — `check-codegraph.py` on a slice branch [US2]

One script, `check-codegraph.py`, and two test modules. Rules are sequential: T008 → T009 → T010 → T011 → T012. Needs
T001 and T002. Disjoint from every US1 task.

In every example the indexed project's index is current and committed work is on `main`; *a whole comparison* is one
run of the gate on `main` that passed. `NARROW` is: checked out on `slice/S1`, none of `CI`, `GITHUB_ACTIONS`,
`GITLAB_CI` set. The indexed project is `indexed()` from `tests/test_code_index_health.py`.

### T008 — [P] [US2] Off a slice branch, and in CI, the run is today's (R6 · AC-S01-11, -12)

- [x] **Rule R6 — every example is a hold: green today, written as holds, saying so, observed passing.** The task pins
  what R7 must not break, and is committed before any production change in this story. Test module
  `tests/test_codegraph_narrowed.py` (new). Uses `tests/gate_audit.py`.

**Tests (all holds):**
- e1 on `main` after a whole comparison → stdout matches today's `check-codegraph: index current — N file(s),
  indexed …` exactly, and the audit hook sees every indexed tracked file opened.
- e2 on `slice/S1` with `CI=true` (then `GITHUB_ACTIONS`, then `GITLAB_CI`) → the same line; the memory file's bytes
  are unchanged by the run (an absent file stays absent today).
- e3 on a branch `feature/x`, and on a detached `HEAD` → the same line.
- e4 on `main` and with `CI=true` on `slice/S1`, the database overwritten with garbage → rebuilt as today (`rebuilt a
  corrupt database first`), and with `CODEGRAPH_GATE_NO_SYNC=1` exit 1 with *fails SQLite's integrity check*.
- e5 `tests/test_code_index_health.py`, `tests/test_code_index_open.py`, `tests/test_code_index.py`,
  `tests/test_cruise_index.py` pass with no edit.

**GREEN:** none. **Teeth:** e1 and e2 are shown to discriminate by, in the working tree, making the whole run skip
hashing (a `return` at the top of `drift()`), seeing e1 fail, and restoring with
`git checkout -- assets/toolkit/scripts/check-codegraph.py`.

**Verify:** `make test TESTS="test_codegraph_narrowed test_code_index_health test_code_index_open test_code_index
test_cruise_index"`, then `make lint typecheck check-structure`. Commit (tests only: reaches no user).

**Files:** `tests/test_codegraph_narrowed.py` (new), `tests/gate_audit.py` (only if T002's helper is found wanting).

### T009 — [P] [US2] On a slice branch the gate hashes what changed (R7 · AC-S01-10)

- [x] **Rule R7.** One changed file, one hash, and the line says so. Needs T008 (same test file, holds in place).
  Uses `tests/gate_audit.py` and the fake `codegraph` CLI.

**RED** (in `tests/test_codegraph_narrowed.py`; each fails today because every run hashes every file and prints
today's line):
- e1 `NARROW`, nothing changed → exit 0, stdout one line: `check-codegraph: index current — hashed 0 of N file(s),
  only what changed since the last whole comparison (<moment>); the integrity check was not run here and runs in the
  full gate`.
- e2 `NARROW`, one `.py` file edited and the index synced for it (fake CLI `sync`) → `hashed 1 of N`, and the audit
  hook sees that file and no other indexed source file opened.
- e3 `NARROW`, the edit committed on the slice branch → still `hashed 1 of N`; after e2's pass the next run reports 0.
- e4 `NARROW`, one file edited and the index *not* synced, CLI reachable → `synced 1 file(s) first; index current —
  hashed 1 of N …`, exit 0.
- e5 the same with `CODEGRAPH_GATE_NO_SYNC=1` → exit 1 with today's report naming the file.

**GREEN** — `check-codegraph.py` gains, per plan.md *Design* and `data-model.md`: `narrowable()` (`git symbolic-ref
--short -q HEAD` matching `^slice/[A-Za-z0-9][A-Za-z0-9._-]*$`, none of `CI`, `GITHUB_ACTIONS`, `GITLAB_CI`
non-empty); the minimum of the memory `.codegraph/gate-memory.json` that e1–e5 need (the key, the `HEAD` commit, the
paths dirty at the time, the vouched rows, the database identity, the moment), **written at the *index current* exit
of a passing run outside CI**, and read back; a narrowed run that skips `damage()`, reads the rows, and hashes the
candidates a `git diff --name-only --no-renames -z <commit>` reports; `drift(only)` applying today's per-file
judgement to those paths alone, `drift()` with no argument being today's (it is also called by `behind()` in
`assets/toolkit/scripts/agents/code_index.py`); the new pass line. Sync as today on drift, rows read again, memory
renewed on a pass. The candidates beyond git's diff (T010) and every refusal to narrow (T011) are not this task's.

**REFACTOR:** keep the narrowed path in functions apart from today's `main()` flow so T010–T012 add to a list, not
a branch.

**Verify:** `make test TESTS="test_codegraph_narrowed test_code_index_health test_code_index_open"`, then `make lint
typecheck check-structure`. Commit, level line (PATCH, `VERSION` not raised).

**Files:** `assets/toolkit/scripts/check-codegraph.py`, `tests/test_codegraph_narrowed.py`.

### T010 — [P] [US2] What the memory cannot vouch for is hashed (R8 · AC-S01-13, -14, -15, -21)

- [x] **Rule R8.** Dirty-then-reverted, a rewritten row, a file git was told not to report. Needs T009. Test module
  `tests/test_codegraph_memory.py` (new).

**RED** (each fails today for the reason given; each is **narrowed to miss it** until the candidates are widened, and
"today" means the T009 tree):
- e1 a file edited, the index synced (it holds the dirty content), whole comparison on `main`, then `git checkout --
  file`, `NARROW`, `CODEGRAPH_GATE_NO_SYNC=1` → exit 1 naming the file, as the whole run on the same tree does. Fails
  at T009: the file is not in git's diff against the commit, so it is passed by.
- e2 after a whole comparison one row's `content_hash` rewritten in the database with `indexed_at` untouched, `NARROW`,
  no sync → exit 1 naming that file. Fails at T009: the row's change is not a candidate.
- e3 a row deleted → that file is re-examined and the verdict equals the whole run's. Fails at T009: same.
- e4 a row added for a tracked file → that file is hashed. Fails at T009: same.
- e5 `git update-index --assume-unchanged f`, `f` edited, `NARROW`, no sync → exit 1 naming `f`; the same with
  `--skip-worktree`. Fails at T009: git does not report `f`.
- e6 the database file replaced by a copy of itself (another inode) → a whole run, saying why. Fails at T009: no
  database identity is checked and no clause names it. (The clause's exact wording is R9's; here the run is whole and
  the line names the identity change in the clause form T011 fixes — if T011's wording is not yet in place, assert the
  whole-run effect, `hashed N of N`-free output, and leave the words to T011.)

**GREEN** — widen the candidates in `check-codegraph.py` to: every path that was dirty at the memory; every path
`git ls-files -v` marks `assume-unchanged` or `skip-worktree`; every path whose row differs from, is new since, or is
gone since the vouched rows; a database with another `st_ino` is not narrowed at all (the whole run).

**REFACTOR:** the candidate set is one function returning one set, so T011 and T012 add no branch to it.

**Verify:** `make test TESTS="test_codegraph_memory test_codegraph_narrowed test_code_index_health"`, then `make lint
typecheck check-structure`. Commit, level line (PATCH, `VERSION` not raised).

**Files:** `assets/toolkit/scripts/check-codegraph.py`, `tests/test_codegraph_memory.py` (new).

### T011 — [P] [US2] A memory that cannot be used means the whole run, said in one clause (R9 · AC-S01-16, -17, -18)

- [x] **Rule R9.** Never a failure for that alone, never a narrower pass. Needs T010 (same test file).

**RED** (in `tests/test_codegraph_memory.py`; each fails at T010 because the unusable memory either yields a
narrower pass without the clause or an error):
- e1 `NARROW` with no memory file → exit 0, today's line plus ` (compared everything: no earlier whole comparison is
  recorded)`.
- e2 the memory file holding `{` → the same with *the record of the last whole comparison could not be read*.
- e3 the memory's commit replaced by forty zeros → *the commit it was taken at is gone*.
- e4 one byte appended to `scripts/check-codegraph.py` (a comment), and separately to `scripts/agents/code_index.py` →
  *the gate's scripts changed since*.
- e5 `NARROW`, the database overwritten with garbage, CLI reachable → rebuilt as today, exit 0; with
  `CODEGRAPH_GATE_NO_SYNC=1` → exit 1, *fails SQLite's integrity check*, never `skipped`.

**GREEN** — in `check-codegraph.py` every route to "not narrowed" (no file, unreadable file, commit not in the
repository, key mismatch, rows unreadable by `sqlite3.Error` or no `files` table, another database identity from
T010) returns a reason string; `main()` runs the whole comparison and the pass line gains ` (compared everything:
<why>)`, on a slice branch only. A failure prints today's report. A database that `damage()` would rebuild is rebuilt
as today.

**REFACTOR:** the reasons are one small table or one function, so the wording lives in one place.

**Verify:** `make test TESTS="test_codegraph_memory test_codegraph_narrowed test_code_index_health"`, then `make lint
typecheck check-structure`. Commit, level line (PATCH, `VERSION` not raised).

**Files:** `assets/toolkit/scripts/check-codegraph.py`, `tests/test_codegraph_memory.py`.

### T012 — [P] [US2] The memory is written only by a pass, and git never sees it (R10 · AC-S01-19, -20)

- [x] **Rule R10.** No renewal after a failure or a skip; nothing in `git status`; it lives and dies with
  `.codegraph/`. Needs T011 (same test file).

**RED / hold, per example** (in `tests/test_codegraph_memory.py`). Each is observed at T011's tree before the
production edit; an example that already passes there is **a hold** and is written as one, saying so, rather than
removed:
- e1 a failing run (`NO_SYNC`, a stale file) → the memory file's bytes are what they were. Likely a hold from T009's
  write-at-pass-only; **seen failing** by writing the memory before the verdict in the working tree, then restoring.
- e2 a narrowed run that synced and passed → the memory is renewed: the next `NARROW` run reports `hashed 0`, keeping
  the last whole comparison's moment. Fails if a narrowed pass does not renew.
- e3 after any run `git status --porcelain` is empty.
- e4 `.codegraph/` not ignored by git (the ignore line removed and committed) → no memory file is written and every
  run is whole. Fails today: the write is not guarded by `git check-ignore -q`.
- e5 `.codegraph/` copied into a second clone at another commit, `NARROW` there, no sync → the verdict equals that
  clone's whole run (stale files named). Fails if a memory from another clone's commit is trusted.

**GREEN** — write the memory only at the *index current* exit, only where no CI marker is set and only where `git
check-ignore -q` says git ignores the path; a temporary name beside it, renamed; renewed only on a pass, keeping the
moment of the last whole comparison; a memory whose commit is another clone's is covered by the commit-gone and
candidate rules and needs no extra code if T010–T011 hold (if it fails, stop and report).

**REFACTOR:** none expected.

**Verify:** `make test TESTS="test_codegraph_memory test_codegraph_narrowed test_code_index_health test_code_index_open
test_code_index test_cruise_index"`, then `make lint typecheck check-structure`. Commit, level line (PATCH,
`VERSION` not raised).

**Files:** `assets/toolkit/scripts/check-codegraph.py`, `tests/test_codegraph_memory.py`.

---

## Phase 4: User Story 3 — the release [US3]

### T013 — [US3] The release says what it is (R11 · AC-S01-22)

- [x] **Rule R11.** One `PATCH` fragment; `VERSION` unchanged; nothing changed under `delivery/` beyond T001's one
  file. Needs T007 and T012 (both stories done; the fragment names what both did).

**RED:** none — `tests/test_changelog.py` is already in the suite. Both examples are holds on a tree the fragment
completes: e1 `changelog.d/gate-walks.md`, first line `PATCH`, names the five directories (`.venv`,
`node_modules`, `__pycache__`, `.git`, a `target` beside a `pom.xml`), the `pom.xml` test, the one kind of finding that
can disappear (a violation inside a pruned directory), the count on the two pass lines, and where `check-codegraph`
compares only what changed (a `slice/<id>` branch outside CI; the trunk, every other branch and CI as today);
`make test TESTS="test_changelog"` green. e2 `git diff` over the slice shows no change to `VERSION` or under
`delivery/` other than `delivery/survey/pinned.md`.

**GREEN** — write the fragment. It asks nothing of a repository already generated (the same answers, generated
better); say so.

**REFACTOR:** none.

**Verify:** `make test TESTS="test_changelog"`, then `make lint typecheck check-structure`; `git diff --stat` over the
slice shows e2. Commit, level line (PATCH, `VERSION` not raised because it already carries 1.5.2.dev0).

**Files:** `changelog.d/gate-walks.md` (new).

---

## Phase 5: Gates (host)

### T014 — Both full gates on the final tip (host task)

- [ ] **Host task — not delegated.** Run `make verify` and `make -f delivery/Makefile verify` on the tree after T013;
  both green (Principle XIV). Confirm the slice's diff touches under `delivery/` only `delivery/survey/pinned.md`,
  `VERSION` is `1.5.2.dev0`, and no test file under 350 lines is over. Then the demo from [quickstart.md](quickstart.md).

---

## Parallel opportunities

- **US1 and US2 may run concurrently.** US1 (T003–T007) writes `assets/toolkit/scripts/check-imports.py`,
  `assets/toolkit/scripts/check-migrations.py`, `tests/test_gate_walks.py` and `tests/test_gate_walks_target.py`; US2
  (T008–T012) writes `assets/toolkit/scripts/check-codegraph.py`, `tests/test_codegraph_narrowed.py` and
  `tests/test_codegraph_memory.py`. They share no file, so the `[P]` on each task means *against the other story*.
  Two conditions bind: each delegate commits only the exact paths of its own manifest (`git add <path>`, never
  `git add -A`), because the branch is one; and each runs `make lint typecheck check-structure` knowing the other
  story's half-done file may be in the tree. If that is not acceptable, give each story its own worktree.
- **Not parallel inside a story.** T003–T006 all edit `check-imports.py`; T003, T004 and T005 edit `check-migrations.py`;
  T003, T004 and T006 write `tests/test_gate_walks.py`. T009–T012 all edit `check-codegraph.py`; T010–T012 write
  `tests/test_codegraph_memory.py`; T008 and T009 write `tests/test_codegraph_narrowed.py`. Two delegates would write
  one file. They run one at a time, in order.
- **Setup and Pin first.** T001 (host) and T002 precede every implementation task; both stories depend on `tests/gate_audit.py`.
  T001 and T002 touch different files and may run together.
- **US3 follows both.** T013 needs T007 and T012; it writes one file no other task writes, but its wording depends on
  what both stories did.
- **Host tasks:** T001 and T014; the host writes `tasks.md` and nothing else here.
- Most delegates at once: two (one per story).

## Design review

No screen in this slice

## Convergence

**Converged on pass 2, the loop's bound** (2026-10-03, cruise iteration 7, `drive-converge`, host model, fresh
context each pass) at `e531ca0`, over `ed91b20..e531ca0`: no `CRITICAL` or `HIGH` open. Pass 1 (at `4262f24`) was
not converged — three `HIGH` (T015, T016, T017), two `MEDIUM` (T018, T019), one `LOW` (T020), all implemented
(`607c0f2`, `3012d4c`, `da107bf`, `44629fe`, `b0ee8e8`, `9057a93`) with decisions D48 and D49. Pass 2 confirmed each
closed its class but T018 (one hostile content left: T022) and appended T021 `MEDIUM`, T022 `LOW`, T023 `LOW` as
Phase 4 tasks, none of which re-opens the loop (D50 says what each becomes). Pass 2 ran inside its budget. No
`.codegraph/` in this tree: callers were found by text search.

**Levels.** *Domain* — the candidate set (`assets/toolkit/scripts/check-codegraph.py:345–376`), the stat record
taken by `os.fstat` on the handle opened for hashing before any read (`:141–149`, `:263–267`), `under()`
(`assets/toolkit/scripts/check-imports.py:70–78`), the pruning test (`:46–49`; `check-migrations.py:74–77`). Left
open at this level by pass 2: how a narrowed run judges a tracked file with no row (T021). *Use case* —
`narrowed()` (`check-codegraph.py:392–420`), `whole()` (`:451–492`), `conclude()` (`:423–448`), the only caller of
`remember()` and only on the pass branch; `behind()` in `agents/code_index.py` still calls `drift()` with no
argument and gets today's answer. *Delivery adapter* — the pass lines (`check-codegraph.py:438`,
`check-imports.py:351`), exit codes, and the trunk line byte for byte `ed91b20`'s; the read of the memory outside
the guard at `:503` is T022. *Screen* — none. *Published contract* — `changelog.d/gate-walks.md` (first line
`PATCH`), every sentence followed in the state it describes (the 79 confirmed on a generated skeleton; deleting
the memory gives a whole run; two imprecisions corrected by the host after the pass: the two-second condition,
and that a trunk run now writes the memory); `VERSION` `1.5.2.dev0`; no file added under `assets/`; nothing
`delivery/.written` lists changed; the memory's shape (`SHAPE`, `:302`).

**Constitution.** *I* — `narrowable()` (`check-codegraph.py:234–240`) keeps the trunk, every non-slice branch, a
detached `HEAD` and CI whole (dropping the CI test is killed by a test); pruning removes no check on the
project's code (`check-imports.py:46–49`: `target` only beside a `pom.xml`); the fragment rode in the first
user-visible commit (`8494a73`); *every starter passes its own gate* is the full verify, run by T014. *III* — one
memory file, no setting. *V* — every acceptance enters through the script's command line; each of T015–T018 is
code and test in one commit. *VIII* — PATCH; the memory is read tolerantly (`:302`, `:331–335`): unknown fields
ignored, a record without `files` is the whole run, the key retires a record across script versions. *XIV* — the
same gates as any change; AC-S01-18's rewording (D48) and AC-S01-23 to -25 (D49) are the run's amendments to
criteria and wait on a person's review, as every entry of this run does (the cruise report lists them).

**Sweeps.** Pass 1: bytes or a row changing without becoming a candidate (found T016, T017; row rewritten in
place caught; staged-only, newly tracked, rename, deletion, gitlink, a quoted path, another slice branch, a
rebased `HEAD`, a linked worktree — by reading, no hole); the memory written per exit path (only on a pass);
walks filtered against a listing at another top (found T015). Pass 2: T015's class by 14 differential scenarios
against the `ed91b20` script, exit code and stderr byte for byte — a link above the directory, a recorded path
through a pruned name, a nested deployable, an absolute path, rule 5 as well as rule 4 — all identical; T016's
class — rename-replace with times copied, bytes restored on a new inode, hashed-unequal-then-synced, CRLF after a
synced narrowed pass, the two-second rule over three immediate runs — each equal to the whole run; 24 contents
of the memory file (found T022); 25 mutations of the production code in scratch copies — killed for R2, R3, R5,
R6, R9, R10, T015, T016, AC-S01-25; survived: each of git's report, `dirty` and the flagged paths removed alone
(the stat record covers the same files — two mechanisms, one behaviour; T021 e2 holds git's report), size and
modification time compared alone (the two-second rule covers change time and identity on Linux), the catch-all
re-raising (T022). No test passes vacuously for `settle()`: every narrowed claim asserts its `hashed N of`.
Not reached by either pass: Windows and network filesystems (D49 says so); R4 and R11 by mutation.

Converge pass 1 (cruise iteration 7), against `ed91b20..4262f24`. Each was reproduced in a scratch project generated
under `/tmp` (reference skeleton; the pre-slice script from `ed91b20` beside the new one; `CI=1` for the whole run).

- [x] T015 [US1] **HIGH** — `check-imports.py` `under()` answers from a listing taken at another top by comparing
  path *spellings*, so a recorded deployable whose spelling is not the one that listing produced is read as empty
  and rules 4 and 5 pass where the pre-slice gate failed (AC-S01-6, SC-007, constitution I, D45's *no finding
  outside a pruned directory changes*).

  **RED** — in `tests/test_gate_walks.py`, with a `.ts` file under the web app importing
  `../../service/src/domain/thing`, and separately a rule-5 violation in a context-holding service:
  - e1 the web app recorded as `apps/service/../web` → today exit 0 `(80 directory entries read)`; the pre-slice
    script exits 1 naming `apps/service/../web/src/bad.ts:1`.
  - e2 the web app recorded as `apps/weblink`, a symbolic link to `apps/web` → today exit 0; pre-slice exit 1 naming
    `apps/weblink/src/bad.ts:1` (skipped where the platform cannot make a link).
  - e3 `apps/web` itself a symbolic link to a directory outside `apps/` → today exit 0; pre-slice exit 1.
  - holds: recorded as `apps/web`, `apps/web/`, `./apps/web`, `frontends/web` and `.` — all five fail today as before.

  **GREEN** — closes the class *a walk filtered against a listing taken at another top*: `under()` reuses an earlier
  listing only where that provably yields the files the directory's own listing would, and otherwise lists the
  directory itself (pruned, counted); findings and their path spellings equal the pre-slice script's for every
  recorded path it could read. Not the three spellings above.

  **Files:** `assets/toolkit/scripts/check-imports.py`, `tests/test_gate_walks.py`. PATCH, `VERSION` not raised.

- [x] T016 [US2] **HIGH** — a narrowed `check-codegraph` run reports *current* for a file whose bytes differ from
  its row when git's diff does not report the change: under the generated `.gitattributes` (`* text=auto eol=lf`) a
  file rewritten with CRLF is ` M` in `git status` and absent from `git diff --name-only <commit>`, so it is no
  candidate (D46's must-never; AC-S01-21).

  **RED** — in `tests/test_codegraph_memory.py`: whole pass on `main`, `slice/S1`, one indexed file's line endings
  rewritten to CRLF, no sync → the narrowed run must fail naming it as the whole run does; today it prints
  `hashed 0 of 55` and exits 0 while `CI=1` exits 1. The mirror: CRLF on disk when the memory was written, LF after.

  **GREEN** — closes the class *working-tree bytes git's comparison normalises away* (line-ending and `text`
  attributes, `core.autocrlf`, clean filters, `ident`), at the write of `dirty` and at the read of the candidates
  alike, as D49 decides it (read the entry; AC-S01-23 to AC-S01-25): the memory records, for every tracked file the
  index holds a row for, its size, modification time and change time in nanoseconds and its identity, taken from the
  file as it was opened for hashing; a narrowed run stats each and hashes any whose record is missing or differs,
  and any whose times are not safely older (two seconds) than the start of the run that vouched for it; a narrowed
  pass renews the record of each file it hashed and found equal; a memory without these records is the whole run
  with the one clause. Owed beside the CRLF pair (before `git add`, after `git add`, and the mirror): a same-size
  rewrite in place with its modification time restored (`os.utime`) → the narrowed run fails as the whole run
  does; a `touch` → hashed once, pass, then `hashed 0`.

  **Files:** `assets/toolkit/scripts/check-codegraph.py`, `tests/test_codegraph_memory.py`. PATCH.

- [x] T017 [US2] **HIGH** — a file git was told not to report *when the memory was written* is not recorded in
  `dirty` (`remember()` takes `git diff HEAD`, which the flag silences), so after the flag is cleared and the file
  reverted it is no candidate and the narrowed run passes on a row holding the old content (D46 rules 2 and 4;
  AC-S01-13, -15, -21).

  **RED** — `--assume-unchanged` (and `--skip-worktree`) on a file, edit it, index follows, a passing run writes the
  memory (`dirty: []` today); clear the flag, `git checkout -- <file>`, no sync → narrowed must report it changed;
  today `hashed 0`, exit 0, while the whole run exits 1 naming it. Both after a whole pass and after a narrowed pass.

  **GREEN** — closes the class *what git was not reporting at the moment the memory vouched*: every path flagged at
  the write is remembered as dirty (or the memory is not written while any exists), on both writers of the memory.

  **Files:** `assets/toolkit/scripts/check-codegraph.py`, `tests/test_codegraph_memory.py`. PATCH.

- [x] T018 [US2] **MEDIUM** — a memory that is well-formed JSON of the right outer shape but unusable inside ends
  the run with a traceback and exit 1, where AC-S01-17 says the run is whole and *never fails for that reason alone*.

  **RED** — `"dirty": [["a"]]` → `TypeError` in `candidates_of`; `"whole": 1e300` (or `Infinity`) → `OverflowError`
  in `moment`; each must be today's line plus *the record of the last whole comparison could not be read*.

  **GREEN** — closes the class *any content of the memory file*: every field is validated to the depth it is used
  before the narrowed path starts, or any exception reading or using the record means the whole run with the one clause.

  **Files:** `assets/toolkit/scripts/check-codegraph.py`, `tests/test_codegraph_memory.py`. PATCH.

- [x] T019 [US2] **MEDIUM** — *answered by D48: the whole run's skip is today's answer and stands; AC-S01-18 is
  reworded; what is owed is one hold test — on `slice/S1` with a usable memory, the `files` table renamed → the
  run goes whole and prints today's `schema may have moved on — skipped`, exit 0 — and no production change.* As
  raised: a question for the host before any code: on a slice branch with a usable memory, a
  database that passes the integrity check but whose `files` table cannot be read (renamed here) goes whole and
  prints today's `… schema may have moved on — skipped`, exit 0, with no clause. AC-S01-18 says both *never
  skipped* and *answers as AC-S01-12* (today's whole run, which skips here); plan R9 e5 covers only garbage bytes.
  Decide which reading stands, then: either a test holding the skip as today's answer and the criterion's wording
  narrowed to *damage*, or the skip refused on a slice branch. **GREEN** closes the class *every exit of `whole()`
  reached from a narrowed attempt* — each either carries the clause or is recorded as deliberately today's words.

  **Files:** `specs/001-faster-slipwai/spec.md` or `assets/toolkit/scripts/check-codegraph.py`, `tests/test_codegraph_memory.py`.

- [x] T020 [US2] **LOW** — the tests' stand-in `sync` replaces the database file, so no test runs the gate's own
  sync-then-compare-again on a narrowed run against a database written in place (same inode), which is what SQLite
  does. Observed correct by hand (in-place stand-in: `synced 1 file(s) first; … hashed 1 of 55`, memory renewed,
  inode unchanged; a failing sync leaves the memory byte-identical). **GREEN** closes the class *the stand-in CLI
  differs from CodeGraph in how it writes*: one narrowed-sync test with an in-place stand-in.

  **Files:** `tests/test_codegraph_narrowed.py` (and its fixture helper).


Converge pass 2 (cruise iteration 7), against `ed91b20..e531ca0` — the confirming pass. T015–T020 re-run and their
classes attacked in scratch projects under `/tmp`; nothing `CRITICAL` or `HIGH` was found. What is still owed:

- [x] T021 [US2] **MEDIUM** — a narrowed run judges a tracked file *the index holds no row for* only where git
  reports it changed, so its verdict differs from the whole run's where such a file's modification time moves
  without git reporting anything; and no test holds git's report as a source of candidates at all.

  **RED** — in `tests/test_codegraph_memory.py`:
  - e1 a tracked `.py` file with no row, older than the index's last `indexed_at` (a file CodeGraph declined), whole
    pass on `main`, `slice/S1`, then `touch` it (or rewrite it with CRLF, which git does not report) → the whole run
    (`CI=1`, `NO_SYNC`) exits 1 naming it under *the index has never seen*; the narrowed run today prints
    `hashed 0 of 36` and exits 0. Reproduced: `indexed_at` set five seconds ahead, `declined.py` committed, whole
    pass, six seconds, `os.utime`.
  - e2 (a hold with no test today) a file newly tracked after the memory — committed, staged, and `git add -N` —
    with no row → the narrowed run fails naming it as the whole run does. It does today (observed: both exit 1
    naming `brand_new.py`), but with `*changed` removed from `candidates_of` all 38 tests of
    `test_codegraph_narrowed`, `test_codegraph_memory` and `test_codegraph_bytes` still pass: the stat record
    covers every file that has a row, and nothing else covers one that has none.

  **GREEN** — closes the class *a tracked file with no row*: narrowing narrows the hashing, never the never-seen
  judgement — every tracked file of an indexed suffix with no row is judged by the whole run's own test (its
  modification time against the last `indexed_at`) on a narrowed run too, whatever git reports. If the host
  instead decides the narrowed run's leniency is the answer (the whole run's verdict here is the one the script's
  own comment calls CodeGraph's decision), that is a decision entry and AC-S01-21 names the state; e2 is owed
  either way.

  **Files:** `assets/toolkit/scripts/check-codegraph.py`, `tests/test_codegraph_memory.py`. PATCH, `VERSION` not raised.

- [x] T022 [US2] **LOW** — T018's class *any content of the memory file* is not closed: `remembered()` runs outside
  the `try` in `main()` and catches only `OSError` and `ValueError` from `json.loads`, so a memory file of deeply
  nested JSON ends the run with a traceback and exit 1 (AC-S01-17).

  **RED** — `gate-memory.json` holding `"[" * 200000`, and a valid record whose `dirty` is nested 100000 deep → today
  `RecursionError: Stack overflow … while decoding a JSON array`, exit 1; each must be today's line plus *the
  record of the last whole comparison could not be read*. Every other content tried (22 shapes: non-UTF-8, empty,
  `null`, `whole` as a 400-digit integer, `NaN`, `-Infinity`, a boolean; each `files` record field as a huge integer,
  a string, a float, a boolean, a dict, a short list; `rows` values not strings; `database` of three or of
  strings; a `commit` of `--help`; a lone surrogate or an option-shaped string in `dirty`; the file a directory)
  answered whole or narrowed with exit 0.

  **GREEN** — closes the class *any failure of reading the memory, not only of using it*: the read sits inside the
  same guard as the use (`RecursionError`, `MemoryError` included), and nothing between `narrowable()` and
  `whole()` can raise past it.

  **Files:** `assets/toolkit/scripts/check-codegraph.py`, `tests/test_codegraph_memory.py`. PATCH.

- [x] T023 [US2] **LOW** — *closed by D50: the waits stand; no seam, no setting.* `Project.settle()` waits on the wall clock, up to 2.1 seconds, in about 36 places across
  `test_codegraph_narrowed`, `test_codegraph_memory` and `test_codegraph_bytes` (38 tests; the nine of
  `test_codegraph_bytes` with five others took 33 seconds), because a change time cannot be set back and the gate has no seam for its two-second rule.
  Constitution XIII, when in force, forbids wall-clock sleeps in the deterministic suite; it is a target today,
  and this feature is the one that climbs to it. No test passes vacuously for it (see the pass-2 verdict). A
  question for the host before any code: a seam costs a setting the fragment says is not added. **GREEN** closes
  the class *a test that waits for the gate's own rule to expire*: either the wait is paid once per module rather
  than once per project, or the decision that it stands is recorded against XIII.

  **Files:** `tests/test_codegraph_narrowed.py` (and whatever the decision names).

## Phase 4: after converge — the gaps pass over the diff (D51)

Two `drive-gaps` delegates (host model, fresh context), one per seam, at `26e3d2c`: no `CRITICAL` or `HIGH`; four
`MEDIUM`, nine `LOW`. D51 says what each becomes. The ones new with the slice:

- [x] T024 [US1] **MEDIUM** (walking gates G1, G4) — tests only. No test compares a count on a tree where `under()`
  is called: `GateWalkListingTest.skeleton()` generates with no frontend, though the reference skeleton is Python
  with `react-vite`; with the reuse loop of `under()` deleted the gate prints 98, still under 100, and no test
  fails. And AC-S01-3's *findings equal those of the tree without them* is observed only on a passing tree.
  **RED/teeth** — R1e1's equality (count equals the test's own enumeration, exactly) on the `react-vite` skeleton,
  and on a project with a two-context service; each shown to fail with the reuse loop removed in the working tree
  (restored before the commit). The four pruned directories planted beside the pinned violations
  (`plant_import_violations`, `plant_migration_violations` in `tests/test_gate_walks_pinned.py`) → stderr byte for
  byte the pinned findings. **GREEN** closes the class *a count or a finding asserted only on a tree that does not
  reach the code*. **Files:** `tests/test_gate_walks.py`, `tests/test_gate_walks_recorded.py`.
- [x] T025 [US1] **MEDIUM** (G2) — `check-migrations` lists directories outside `listing()`: `go_migrate_embeds()`
  lists `apps/` and each `migrations/` again, and `check()` lists a marked contraction's directory once more, so
  its count (79 on the reference skeleton) is not the sum D47 defines (86 listed) and *each directory is now
  listed once* is untrue of it. **RED** — under `tests/gate_audit.py`: on the reference skeleton, on one with a
  marked contraction, and on a Go project, no directory is listed twice and the reported count equals the names the
  listings returned. **GREEN** closes the class *a directory read outside the one listing*: every directory read in
  both walking scripts goes through `listing()` or is counted by it; findings and failure output unchanged (the
  pinned tests, `tests/test_gates.py`, `tests/test_go_migrate_embed.py`). **Files:**
  `assets/toolkit/scripts/check-migrations.py`, `tests/test_gate_walks.py`. PATCH.
- [x] T026 [US1] **LOW** (G3, G6) — sentences that ship and are now untrue: the `deployables()` docstring in
  `check-imports.py` (*inside every directory under `apps/` and `packages/` whatever it is called*), the module
  docstring of `check-migrations.py` (*every migration file under every `apps/*/` and `packages/*/`*),
  `src/slipwai/project/guidance.py` (the sentence that ships in a project's `docs/architecture.md`), and
  `docs/services.md`. Each names the five directories not descended, in a clause. **GREEN** closes the class *a
  shipped sentence about what these two gates walk* — search `assets/`, `src/slipwai/project/` and `docs/` for
  both scripts' names and correct every one. **Files:** those four, and any test that holds the sentence. PATCH.
- [x] T027 [US2] **MEDIUM** (code-index G1, G3, G5) — what a developer is told about the narrowed run. The gate's
  module docstring, the block `assets/toolkit/scripts/extensions/codegraph/init.py` writes into `AGENTS.md`, the
  docstring of `agents/code_index.py` and `src/slipwai/project/docs.py` say the gate always integrity-checks and
  rebuilds, and nothing that ships names `.codegraph/gate-memory.json`. The narrowed pass line says the integrity
  check *runs in the full gate*, which names nothing a developer can find. Where git does not ignore
  `.codegraph/`, every slice-branch run says *no earlier whole comparison is recorded* — the wrong reason.
  **RED** — the narrowed pass line names the route: *the integrity check was not run here; it runs on the trunk, on
  any other branch and in CI*; where the record cannot be kept the clause is *the record cannot be kept here: git
  does not ignore `.codegraph/`*. **GREEN** closes the class *what the gate and its pages say about where it
  narrows*: the four texts say that on a `slice/<id>` branch outside CI the gate compares only what changed and
  leaves the integrity check to the trunk and CI, that it keeps its record in `.codegraph/gate-memory.json`, and
  that deleting that file makes the next run whole. **Files:** `assets/toolkit/scripts/check-codegraph.py`,
  `assets/toolkit/scripts/agents/code_index.py` (docstring only), `assets/toolkit/scripts/extensions/codegraph/init.py`,
  `src/slipwai/project/docs.py`, the three `tests/test_codegraph_*.py`, and any test that holds those texts. PATCH.
- [x] T028 [US2] **MEDIUM** (G2) — tests only. AC-S01-17's *git unable to list what changed* has no test; three
  routes return it. **Hold with teeth** — after a whole run on `main`, on `slice/S1`, the loose tree object of the
  memory's commit moved away (`cat-file -e` passes, `git diff <commit>` fails) → today's line plus `(compared
  everything: git could not say what changed)`, exit 0; shown failing with the route returning an empty set.
  **Files:** `tests/test_codegraph_memory.py` or `tests/test_codegraph_bytes.py`.
- [x] T029 [US2] **LOW** (G6) — `files_of` keys its records with the platform's separator while the index and git
  use `/`; on Windows every file in a subdirectory would never be vouched for (safe, no saving). **GREEN** closes
  the class *a path compared across git, the index and the filesystem*: one spelling, POSIX, everywhere a path is a
  key. **Files:** `assets/toolkit/scripts/check-codegraph.py`, a test where one can be written on this platform.

## Phase 4: after acceptance — the adversary pass (D52, D53)

Seven findings under `## S01 · 4357da0` in `specs/001-faster-slipwai/adversary-log.md`, none `CRITICAL`.

- [x] T030 [US1] **HIGH** (A1, A4; D52 — read the entry: it is the contract) — a slice can commit a `pom.xml`
  beside its own `target/` directory and both walking gates stop reading it. **RED** — in
  `tests/test_gate_walks_pom.py` (new): the adversary's reproduction on a Python project (an empty
  `apps/service/src/shop/pom.xml` beside `target/domain/evil.py` importing an adapter and
  `target/migrations/202610031200_drop.sql` dropping a column, and the same at the service's root) → both gates
  fail naming the files, as the scripts at `ed91b20` do; a nested module's `target` below a recorded Java
  deployable's root → read; a `target` beside a `pom.xml` under `packages/` → read; a tree with no `project.json`
  and one whose record is not an object, or carries a non-string `path` or `language` → no `target` pruned, and the
  exit and last stderr line equal the `ed91b20` script's; a deployable recorded at `apps/service/target` (and
  beneath a `.venv`-named directory) → every rule and `check-migrations` read it (AC-S01-26). **Holds** — a
  recorded Java deployable's `target/` beside its `pom.xml` is not descended, under `apps/service`, `apps/service/`
  and `./apps/service`, `generated` true and false (AC-S01-4); the Java package directory is read. **GREEN** closes
  the class *a prune test a slice can write*: both scripts' `skipped()` take the test from `project.json`'s
  deployables — `language` `java`, the directory is that deployable's `path`, `pom.xml` a file there — and never
  prune a directory that is, or leads to, a recorded deployable's `path`; `check-migrations` reads `project.json`
  once (AC-S01-8); `tests/test_gate_walks_target.py` moves to the new rule. The shipped sentences T026 wrote (*a
  Maven `target` beside its `pom.xml`*) are reworded to the record's test wherever they stand. **Files:**
  `assets/toolkit/scripts/check-imports.py`, `assets/toolkit/scripts/check-migrations.py`,
  `tests/test_gate_walks_pom.py` (new), `tests/test_gate_walks_target.py`, `tests/test_gate_walks.py`,
  `tests/test_gate_walks_counts.py`, `src/slipwai/project/guidance.py`, `docs/services.md`. PATCH.
- [x] T031 [US1] **LOW** (A2) — `children()` in `check-migrations.py` leaves a pruned directory out of its
  parent's entries, so a `contract:` marker naming one (`.venv`, `.git` → a failure where the `ed91b20` script
  passed; `node_modules`, `__pycache__` → *is not a migration beside it* where it said *does not come before it*)
  changes the answer on the project's own file. **RED** — both markers, compared with the `ed91b20` script's exit
  and stderr. **GREEN** closes the class *an entry that is pruned is still an entry*: every reader of a
  directory's entries sees the pruned names; only descent stops. **Files:**
  `assets/toolkit/scripts/check-migrations.py`, `tests/test_gate_walks_pom.py`. PATCH.
- [x] T032 [US2] **MEDIUM** (F1) — `narrowed()` reads the index's rows and `drift()` reads them again; a row that
  changes between the two reads is no candidate, is never hashed, and is recorded as vouched for, so every later
  narrowed run passes where the whole run fails. **RED** — in `tests/test_codegraph_races.py` (new): a `git`
  wrapper first on `PATH` that rewrites one row's `content_hash` when the gate calls `git diff`, on `slice/S1`,
  `CODEGRAPH_GATE_NO_SYNC=1` → the run must fail naming the file as the whole run does, and the record must not
  hold the rewritten hash. **GREEN** closes the class *two reads of one provider inside one verdict*: each
  comparison judges, and the record keeps, one read of the rows — including the comparison after a sync.
  **Files:** `assets/toolkit/scripts/check-codegraph.py`, `tests/test_codegraph_races.py`. PATCH.
- [x] T033 [US2] **MEDIUM** (F2, F3) — `remember()` writes through the fixed name `.codegraph/gate-memory.json.tmp`:
  a symbolic link committed there (`git add -f`) has its target overwritten with the record on the first passing
  run — on the trunk too — and `git status` shows a deletion; a FIFO there hangs the run. **RED** — the link
  (its target's bytes unchanged afterwards, `git status` unchanged by the run, on `slice/S1` and on `main`); a
  FIFO (the run returns; `timeout`); the record itself a directory, a link, a FIFO → the run passes whole and
  nothing outside `.codegraph/` is written. **GREEN** closes the class *a write through a path that was already
  there*: the record is written to a file the gate creates exclusively under a name of its own inside
  `.codegraph/`, then renamed over the record only where the record is absent or a regular file; anything else is
  *cannot be kept here*, never fatal; no stray temporary file survives a run. **Files:**
  `assets/toolkit/scripts/check-codegraph.py`, `tests/test_codegraph_races.py`. PATCH.
