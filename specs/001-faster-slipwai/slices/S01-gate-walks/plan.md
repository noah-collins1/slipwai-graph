# Implementation Plan: S01-gate-walks — a generated gate stops reading what it never needed

**Branch**: `adopt-method` (D12 — no `slice/` branch, no claim, no push) | **Date**: 2026-10-03 |
**Spec**: [spec.md](../../spec.md), *Slice acceptance criteria* → `### S01-gate-walks` (AC-S01-1 … AC-S01-22)

**Input**: the slice's row in [story-split.md](../../story-split.md) and its criteria in `spec.md`; decisions
D7, D9, D12, D39, D45, D46, D47 in [decisions.md](../../decisions.md). Written by cruise iteration 7 (host, strong
model). The optional `before_plan` hook (`/characterise`) is taken as the ladder's Pin stage, after tasks.

## Summary

Three gate scripts every generated project runs in `make verify` do work the answer never needed.
`check-imports` lists `apps/` and `packages/` three times and each browser app again, and descends `.venv` and
`node_modules`; `check-migrations` descends them too; `check-codegraph` hashes every tracked file and runs
SQLite's integrity check on every run. After this slice the two walking gates list each directory once, do not
descend `.venv`, `node_modules`, `__pycache__`, `.git`, or a `target` beside a `pom.xml` (D45), and say on their
pass line how many directory entries they read (D47); and on a `slice/<id>` branch outside CI `check-codegraph`
hashes only what changed since its last whole comparison (D46). The trunk, every other branch and CI run what
they run today. A PATCH: the same answers, generated better.

## The example map (rules the tasks cut on)

The **skeleton** in every example is `slipwai generate` with the `event-modelling` profile, the Python backend, the
`react-vite` frontend and target `none`, freshly generated, nothing installed (`self.generate(...)` in the test
tree). The **indexed project** is `indexed()` from `tests/test_code_index_health.py`: a generated Python project
with an index built by the fake `codegraph` CLI there, which keeps a real SQLite database.

### User story 1 — the walking gates (`check-imports.py`, `check-migrations.py`)

| Rule | Criteria | What it says | Examples |
|---|---|---|---|
| **R1** each directory is listed once, and the pass line says how many entries that was | AC-S01-1, -2, -7, -9 | The count is the sum of names every directory listing returned; today's words stand before it | e1 skeleton → `check-imports` exits 0, stdout is exactly `check-imports: inward dependency rule holds (N directory entries read)`, N ≤ 100 and N equals the test's own enumeration of `apps/` and `packages/` (79 today; today's script would list 256) · e2 skeleton → `check-migrations` stdout is today's sentence, unbroken, then ` (N directory entries read)` with the same N · e3 150 empty files added under `apps/service/src/extra/` → both pass, the count is over 100, stdout is the one line and stderr is empty · e4 a project directory holding only `project.json` and `scripts/` → both pass and report `0 directory entries read` · e5 a symbolic link under `apps/service/` to a directory outside `apps/` holding a `domain/` violation → no finding, the count rises by one (skipped where the platform cannot make a link) |
| **R2** four names are never descended | AC-S01-3 | `.venv`, `node_modules`, `__pycache__`, `.git`, at any depth, in every walk | e1 under `apps/service/`: `.venv/lib/pkg/domain/bad.py` importing an adapter, `node_modules/pkg/migrations/0001_drop.sql` with `DROP TABLE`, `src/__pycache__/x.py`, `.git/hooks/x` → both scripts pass, each count is the skeleton's plus exactly the number of pruned directories planted · e2 the same four planted two directories deeper (`apps/service/src/a/b/`) → the same · e3 `node_modules/pkg/src/x.ts` importing `apps/service` planted under `apps/web/` → rule 4 does not report it · e4 run under an audit hook (`sys.addaudithook`, `os.scandir` events) → no listing of any path inside a pruned directory |
| **R3** `target` is build output only beside a `pom.xml` | AC-S01-4, -5 | Maven's directory is skipped; a source directory of that name is read | e1 a Java (`java-quarkus`) service with `target/classes/db/migration/V2__drop.sql` (`DROP TABLE`, no marker) and `target/generated-sources/domain/Bad.java` importing `jakarta.inject` → both pass; the count rises by one · e2 a Python service recording contexts `orders` and `target`: `src/target/domain/bad.py` importing an adapter → fails rule 1 naming the file · e3 the same service: a file under `src/target/` importing `orders.domain` → fails rule 5 · e4 the same service: `src/target/migrations/0002_drop.sql` → `check-migrations` fails naming it · e5 the Java service with a package directory `src/main/java/…/target/` under `domain/` holding a `jakarta` import → fails |
| **R4** findings and failure output are today's | AC-S01-6 | Same findings, same order, same bytes on stderr, no count | e1 the pinned violating tree for `check-imports` (Pin stage) → stderr and exit unchanged, stdout empty · e2 the pinned violating tree for `check-migrations` → the same · e3 `tests/test_gates_imports.py`, `tests/test_gates.py`, `tests/test_go_migrate_embed.py`, `tests/test_frontend.py`, `tests/test_monorepos.py` pass with no edit |
| **R5** `project.json` is opened at most once | AC-S01-8 | One read per run | e1 `check-imports` run under an audit hook counting `open` events on `project.json` in a project with a web app and a two-context service (every rule that asks the manifest runs) → exactly 1 · e2 `check-migrations` → 0 or 1 · e3 a tree whose `project.json` is deleted after generation → both answer as today (pass; the rules that need the manifest find no applications) |

### User story 2 — `check-codegraph.py` on a slice branch

In every example the indexed project's index is current and committed work is on `main`; *a whole comparison*
is one run of the gate on `main` that passed. `NARROW` below is: checked out on `slice/S1`, none of `CI`,
`GITHUB_ACTIONS`, `GITLAB_CI` set.

| Rule | Criteria | What it says | Examples |
|---|---|---|---|
| **R6** off a slice branch, and in CI, the run is today's | AC-S01-11, -12 | Every file hashed, integrity check run, today's line byte for byte | e1 on `main` after a whole comparison → stdout matches today's `check-codegraph: index current — N file(s), indexed …` exactly, and the audit hook sees every indexed tracked file opened · e2 on `slice/S1` with `CI=true` (then `GITHUB_ACTIONS`, `GITLAB_CI`) → the same line; the memory file's bytes are unchanged by the run · e3 on a branch `feature/x`, and on a detached `HEAD` → the same line · e4 on `main` and with `CI=true` on `slice/S1`, the database overwritten with garbage → rebuilt as today (`rebuilt a corrupt database first`), and with `CODEGRAPH_GATE_NO_SYNC=1` exit 1 with *fails SQLite's integrity check* · e5 `tests/test_code_index_health.py`, `tests/test_code_index_open.py`, `tests/test_code_index.py`, `tests/test_cruise_index.py` pass with no edit |
| **R7** on a slice branch the gate hashes what changed | AC-S01-10 | One changed file, one hash, and the line says so | e1 `NARROW`, nothing changed → exit 0, stdout one line: `check-codegraph: index current — hashed 0 of N file(s), only what changed since the last whole comparison (<moment>); the integrity check was not run here and runs in the full gate` · e2 `NARROW`, one `.py` file edited and the index synced for it (fake CLI `sync`) → `hashed 1 of N`, and the audit hook sees that file and no other indexed source file opened · e3 `NARROW`, the edit committed on the slice branch → still `hashed 1 of N` (the memory's tree is the whole comparison's until a pass renews it — after e2's pass the next run reports 0) · e4 `NARROW`, one file edited and the index *not* synced, CLI reachable → `synced 1 file(s) first; index current — hashed 1 of N …`, exit 0 · e5 the same with `CODEGRAPH_GATE_NO_SYNC=1` → exit 1 with today's report naming the file |
| **R8** what the memory cannot vouch for is hashed | AC-S01-13, -14, -15, -21 | Dirty-then-reverted, a rewritten row, a file git was told not to report | e1 a file edited, the index synced (it holds the dirty content), whole comparison on `main`, then `git checkout -- file`, `NARROW`, `CODEGRAPH_GATE_NO_SYNC=1` → exit 1 naming the file, as the whole run on the same tree does · e2 after a whole comparison one row's `content_hash` rewritten in the database with `indexed_at` untouched, `NARROW`, no sync → exit 1 naming that file · e3 a row deleted → that file is re-examined and the verdict equals the whole run's · e4 a row added for a tracked file → that file is hashed · e5 `git update-index --assume-unchanged f`, f edited, `NARROW`, no sync → exit 1 naming f; the same with `--skip-worktree` · e6 the database file replaced by a copy of itself (another inode) → a whole run, saying why |
| **R9** a memory that cannot be used means the whole run, said in one clause | AC-S01-16, -17, -18 | Never a failure for that alone, never a narrower pass | e1 `NARROW` with no memory file → exit 0, today's line plus ` (compared everything: no earlier whole comparison is recorded)` · e2 the memory file holding `{` → the same with *the record of the last whole comparison could not be read* · e3 the memory's commit replaced by forty zeros → *the commit it was taken at is gone* · e4 one byte appended to `scripts/check-codegraph.py` (a comment), and separately to `scripts/agents/code_index.py` → *the gate's scripts changed since* · e5 `NARROW`, the database overwritten with garbage, CLI reachable → rebuilt as today, exit 0; with `CODEGRAPH_GATE_NO_SYNC=1` → exit 1, *fails SQLite's integrity check*, never `skipped` |
| **R10** the memory is written only by a pass, and git never sees it | AC-S01-19, -20 | No renewal after a failure or a skip; nothing in `git status`; it lives and dies with `.codegraph/` | e1 a failing run (`NO_SYNC`, a stale file) → the memory file's bytes are what they were · e2 a narrowed run that synced and passed → the memory is renewed: the next `NARROW` run reports `hashed 0` · e3 after any run `git status --porcelain` is empty · e4 `.codegraph/` not ignored by git (the ignore line removed and committed) → no memory file is written and every run is whole · e5 `.codegraph/` copied into a second clone at another commit, `NARROW` there, no sync → the verdict equals that clone's whole run (stale files named) |

### User story 3 — the release

| Rule | Criteria | What it says | Examples |
|---|---|---|---|
| **R11** the release says what it is | AC-S01-22 | One `PATCH` fragment; `VERSION` unchanged; nothing the factory wrote under this repository's `delivery/` | e1 `changelog.d/gate-walks.md`, first line `PATCH`, names the five directories, the `pom.xml` test, the finding that can disappear, the count on the two pass lines, and where `check-codegraph` compares only what changed; `tests/test_changelog.py` green · e2 `git diff` over the slice shows no change to `VERSION` or to any file `delivery/.written` lists |

R4, R5e3, R6 and R3e2–e5 hold today and are written as holds, saying so. Every other example is **seen** failing
for its stated reason before the production file is touched.

## Technical Context

**Language/Version**: the scripts run on the project's `python3` — the skeleton pins 3.13 (`.python-version`);
standard library only, like every gate script. The factory's tests: Python ≥ 3.11 (`pyproject.toml`).
**Primary Dependencies**: none added. `git`, as today.
**Storage**: one file the gate owns, `.codegraph/gate-memory.json`, inside the directory git already ignores; not a
generated file — nothing writes it at `generate`, and it is absent from `.written`.
**Testing**: `unittest` via `make test`; new tests run the scripts as a generated project runs them
(`python3 scripts/check-….py` in a `self.generate(...)` tree). What a run opened or listed is observed with
`sys.addaudithook` in a three-line wrapper the test passes to `python3 -c` (`open` and `os.scandir` events), not a
mocking framework. The fake `codegraph` CLI is the one already in `tests/test_code_index_health.py`.
**Target Platform**: Linux, macOS, Git Bash. A symbolic-link example skips, saying why, where no link can be made.
**Project Type**: CLI tool, the factory — deployable `slipwai-graph`, kind `tool`, path `.`.
**Performance Goals**: SC-005 — `check-imports` lists at most 100 entries on the skeleton (79).
**Constraints**: PATCH — no setting, no flag, no new generated file, no pass-line word removed; nothing under
`delivery/scripts/`, `tools/`, the `Makefile`, CI or hook settings of this repository changes (D9); every file
under `src/` and `tests/` stays within 350 lines; each script stays one standard-library file.
**Scale/Scope**: three scripts under `assets/toolkit/scripts/`; five new test files; one fragment.

## Constitution Check

*GATE: evaluated against `.specify/memory/constitution.md` before research; re-checked after design.*

| Principle | Touched? | How this slice satisfies it |
|---|---|---|
| I. A generated project owns its files and passes its own gate (NON-NEGOTIABLE) | Yes | *A scoped or memoised gate MUST be additive: the merge root and CI run the full gate … no check is removed anywhere*: the trunk, every non-slice branch and CI run `check-codegraph` exactly as today (R6); pruning removes no check on the project's code — `target` is read wherever it is not Maven's (R3). Every starter still passes its own gate (the matrix tests in `make verify`). The fragment lands in the first user-visible commit; `VERSION` untouched. |
| III. Simplicity | Yes | One walk helper per script; one memory file; no setting. |
| V. Acceptance-driven development | Yes | Each rule a RED-GREEN-REFACTOR cycle at the script's command line; holds are written as holds. |
| VIII. Versioning and breaking changes | Yes | PATCH; the pass lines keep today's words; the fragment names the one kind of finding that can disappear. |
| XIV. Agent-generated change meets the same bar (NON-NEGOTIABLE) | Yes | Increment commits with the quickest relevant tests green; both full gates on the final tip; the hand runs the demo as the actor. |
| II, IV, VI, VII, IX, X, XI, XII, XIII, XV | No | No retry path, domain code, contract, telemetry, secret, pipeline or type changes. |

**Gate result:** no violation; *Complexity Tracking* stays empty. **Post-design re-check:** unchanged.

## Project Structure

```text
assets/toolkit/scripts/check-imports.py      # R1–R5: one pruned listing, the count, one manifest read
assets/toolkit/scripts/check-migrations.py   # R1–R4: the same listing, the count
assets/toolkit/scripts/check-codegraph.py    # R6–R10: the narrowed run and its memory
tests/test_gate_walks_pinned.py              # Pin stage — R4e1, R4e2 (green before any change)
tests/test_gate_walks.py                     # new — R1, R2, R5
tests/test_gate_walks_target.py              # new — R3
tests/test_codegraph_narrowed.py             # new — R6, R7
tests/test_codegraph_memory.py               # new — R8, R9, R10
tests/gate_audit.py                          # new — the audit-hook wrapper both groups use (a helper, no tests)
changelog.d/gate-walks.md                    # R11
```

**Structure Decision**: one deployable, `slipwai-graph` (kind `tool`, path `.`, purpose confirmed); one bounded
context (the factory; D3). The decided strategy is `leave-it` (`delivery/docs/adr/0002-change-strategy.md`): no
new home. The code changed existed before the method did, so the Pin stage applies. Callers, by text search (this
tree has no `.codegraph/`): `drift()` in `check-codegraph.py` is also called by `behind()` in
`assets/toolkit/scripts/agents/code_index.py`, with no argument — its no-argument answer stays today's. The
factory copies `assets/toolkit/scripts/` into a project as it is; no table in `src/slipwai/` names a line of
these scripts.

## Design

### The walk (both walking scripts; [research.md](research.md) R-1, R-2)

Each script gains the same small helper — duplicated, as `project_root()` already is, because each gate script is
one self-contained file:

- `PRUNED = {".venv", "node_modules", "__pycache__", ".git"}`; `skipped(directory, name)` is true for those and
  for `target` where `directory / "pom.xml"` is a file.
- `listing(top)` walks `top` with `os.walk` (top-down, links not followed), adds `len(dirnames) + len(filenames)`
  to a module-level count for every directory it lists, removes skipped names from `dirnames` before descending,
  and returns every path under `top` — files and directories — sorted as `sorted(top.rglob("*"))` sorts them
  (`Path` ordering), so every loop over it meets files in today's order.
- `check-imports`: listings are memoised by top. `source_files(layer)` filters the one listing of `apps/` and of
  `packages/`; rule 4 and rule 5 ask `under(directory)`, which filters a listing already taken where `directory`
  sits inside one and takes (and counts) a new listing only where it does not. `project.json` is read by one
  memoised `manifest()`; `deployables()` and `unruled()` read from it.
- `check-migrations`: `migrations()` filters `listing(ROOT / area)`; its own `"node_modules" not in path.parts`
  test goes, since the walk no longer descends there. It does not read `project.json`.
- The pass line gains ` (N directory entries read)`; the failure path prints what it prints today.

### The narrowed comparison (`check-codegraph.py`; research R-3 to R-6; [data-model.md](data-model.md))

- **When.** `narrowable()`: `git symbolic-ref --short -q HEAD` matches `^slice/[A-Za-z0-9][A-Za-z0-9._-]*$` (the
  shape `check-slice-scope.py` holds) and none of `CI`, `GITHUB_ACTIONS`, `GITLAB_CI` is non-empty. Otherwise
  `main()` runs as it does today, to the byte, except that a passing run outside CI records the memory.
- **The memory**, `.codegraph/gate-memory.json`: the key (SHA-256 of `check-codegraph.py` and of
  `agents/code_index.py`), the commit `HEAD` named, every tracked path that differed from that commit at the
  time (`git diff --name-only --no-renames -z HEAD`), the index's rows as vouched for (`path → content_hash`),
  the database file's identity (`st_dev`, `st_ino`), and the moment of the last whole comparison. Written only at
  the *index current* exit, only where no CI marker is set, and only where git ignores the path
  (`git check-ignore -q`); written to a temporary name beside it and renamed.
- **A narrowed run** skips `damage()`, reads the rows (any `sqlite3.Error`, or no `files` table → not narrowed),
  and hashes only the **candidates**: what `git diff --name-only --no-renames -z <commit>` reports now; every path
  that was dirty at the memory; every path `git ls-files -v` marks `assume-unchanged` or `skip-worktree`; and
  every path whose row differs from, is new since, or is gone since the vouched rows. `drift(only)` applies
  today's per-file judgement to those paths alone; `drift()` with no argument is today's. Drift found → sync as
  today → rows read again → compared again over the same candidates plus whatever rows moved → memory renewed
  only on a pass, keeping the last whole comparison's moment.
- **Why a file outside the candidates is current.** At the memory it was current (the run passed); its bytes are
  the same (git reports no difference from the commit, it was not dirty then, and it is not a file git was told
  to ignore); its row is the same (rows are compared by content). A database that is not the one vouched for
  (another `st_ino`) is not narrowed at all.
- **Not narrowed → the whole run, with one clause** on the pass line, ` (compared everything: <why>)`, on a slice
  branch only. A failure prints today's report.
- **Stated readings.** A `touch` that changes no byte is not a change. A tracked file the index has no row for is
  judged, in a narrowed run, only when it is a candidate; the whole run's rule for such a file reads its
  modification time, which a `touch` moves — the one place the two can differ, and the whole run is what the
  merge root and CI run. Damage the read of the rows does not meet waits for the integrity check in the full gate.

## Pin

`delivery/survey/running.md` records the run path proven (S00) and `project.json` records `smoke`. Three
behaviours change, recorded in `delivery/survey/pinned.md` before implementation:

1. What `check-imports` prints and exits with on a violating tree — the findings, their order, the bytes on
   stderr: `tests/test_gate_walks_pinned.py` (new at the Pin stage, green today) beside `tests/test_gates_imports.py`
   and `tests/test_gates.py`. Not pinned, changed on purpose: the pass line's tail, and findings inside a pruned
   directory.
2. The same for `check-migrations`: `tests/test_gate_walks_pinned.py`, `tests/test_gates.py`,
   `tests/test_go_migrate_embed.py`.
3. What `check-codegraph` answers off a slice branch: `tests/test_code_index_health.py` (already there, green
   today). Not pinned, changed on purpose: on a `slice/<id>` branch outside CI it hashes only what changed.

## Branch and integration

As D12: increments land on `adopt-method`, one slice at a time, no `slice/` branch, nothing pushed. The change is
under `assets/`, so this repository's own `delivery/scripts/` do not move (D9) and its gate runs as before; the
demo generates a project with this checkout's `./slipwai` and runs the scripts there
([quickstart.md](quickstart.md)).

## Deliberate stubs

None.

## Complexity Tracking

Empty.
