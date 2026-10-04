# Tasks: S05-xdist — the root gate's tests run across cores where the project says they may

**Input**: [plan.md](plan.md) (*The example map* R1–R5 is what the tasks cut on; *Pin*; *Structure Decision*),
[research.md](research.md), [data-model.md](data-model.md), [quickstart.md](quickstart.md); acceptance criteria
AC-S05-1 … AC-S05-13 in `specs/001-faster-slipwai/spec.md` under `### S05-xdist`; decisions D102, D103, D104 in
`specs/001-faster-slipwai/decisions.md`; ADR 0003 (Proposed). No `examples.md`: a method slice with no screen and no
event model of its own, so **no white box, no mockup task and no styling task**; the one story is **US2** (FR-009),
*a new Python service's gate runs its tests across cores, a project made before stays serial, and one line in
`project.json` turns it off*.

**Branch**: `adopt-method` (D12). No `slice/` branch, no push, no claim. One commit per task.

**Delegation** (`.specify/drive.json`: `delegate: story`, `cycle: rule`): the host hands one `drive-implement` delegate
the whole of US2 — T001 to T005, in dependency order — or, where the manifests below are disjoint, more than one, each
in a worktree of its own (*Parallel opportunities*). Each task is one RED-GREEN-REFACTOR cycle and one commit, opening
with **one rule's examples** (R1 … R5); a delegate never writes a rule's tests ahead of the previous rule's commit. A
task's "Files" line is its manifest, the only files that delegate may write. Nobody but the host writes `tasks.md`. A
delegate that needs a file outside its manifest — a test elsewhere that pins text it changes — **stops and names the
file; the host adds it.**

**Not a task:** AC-S05-13 (serial and parallel test times on a fresh starter, and `make -j verify`'s median against the
serial gate's) is the demo's: the hand measures and the host writes the numbers into the quickstart and the fragment;
the suite holds causes, never a clock.

## Constraints that hold for every task

- **MINOR, `VERSION` stays `1.6.0.dev0`** (a new `project.json` key with a documented default, AGENTS.md's table).
  Not edited by any task: `VERSION`; anything under `release/`; `assets/toolkit/scripts/verify-stamp.py`; this
  repository's `delivery/scripts/`, `tools/`, the root `Makefile`, CI and hook settings; no file `delivery/.written`
  lists. `assets/` changes only through `make locks` (the four `assets/languages/python/locks/*.lock`). The service
  `pyproject.toml` template's `addopts` is not edited (AC-S05-6).
- **Size and width.** Every file under `src/` and `tests/` stays within 350 lines (`make check-structure`) and 120
  columns (ruff). Current: `docs.py` **330**, `python.py` 267, `scaffold.py` 247, `replay.py` 297, `metadata.py` 77. What the
  gates page gains goes in a new `src/slipwai/project/parallel_tests.py` and `docs.py` takes it in three lines at most. A
  test file that nears 350 splits by example and the report names the new file. Every `read_text`/`open` names
  `encoding="utf-8"`.
- **Tests.** Standard library only; a fake is an executable or a class written in the test tree implementing the real
  tool's command line — **never a mocking framework, `unittest.mock` included**. The gate's tests run
  `./scripts/verify <mode>` of a generated project with a stand-in `uv` first on `PATH` that appends its argv to a log
  (reuse `tests/parallel_gate.py`'s stand-in writer and `gate_environment`, imported, never edited here, and
  `tests/stamp_fixture.py`'s `CI_MARKERS`, `MAKE_STATE`, `GIT_STATE`); evidence is the log, never a printed line. No
  wall-clock assertion. Every `subprocess.run` carries `timeout=`.
- **Environment of a run.** `CI`, `GITHUB_ACTIONS`, `GITLAB_CI`, `MAKEFLAGS`, `MFLAGS`, `MAKELEVEL`, `MAKEOVERRIDES`,
  `MAKEFILES` and the three `GIT_*` state variables are removed from a generated project's command, as the S04 suites do.
- **Commit by path** — `git commit -m … -- <the task's files>`, a new file `git add`ed by its exact path first; never
  `git add -A`, never `git commit -a`, never `git checkout -- <file>` on work that is not the delegate's own.
- **RED is seen** for its stated reason before the production file is touched. A **hold** (an example that passes today)
  is written as a hold, said so in its name or docstring, and **seen to have teeth** before commit: change the
  production file (or invert one assertion), observe the failure, restore. A hold with no teeth is not claimed.
- **GREEN is a class**, not an instance: every value, mode and backend a criterion names, each with its example.
- **Before each commit** run `make lint typecheck check-structure`.
- **Versioning, on every commit** (`AGENTS.md`): a commit that changes `src/slipwai/` or `assets/` says `Level MINOR;
  VERSION already carries it (1.6.0.dev0); the fragment changelog.d/xdist.md claims MINOR` and names the reason (a new
  `project.json` key, `parallelSafe`, and a new pinned development tool); a commit that changes only `tests/` says it
  reaches no user. **The fragment `changelog.d/xdist.md` lands in T001**, the first commit that changes a user-visible
  tree, as a first draft with first line `MINOR` (so `tests/test_changelog.py` holds from then on); T005 completes it.
  No other task touches it. Shape: [`changelog.d/README.md`](../../../../changelog.d/README.md) — the level on the
  first line, one bold lead sentence, and **one paragraph beginning `**Catch-up.**`** that stands alone.

### The sweep at planning

Tests under `tests/` that read a generated Python project's dev list, `scripts/verify`, `project.json` or the gates page,
and that a new key, a new pin or a new paragraph can break. **Hits** (met by the task named; none is edited by a task
that does not list it in *Files*):

| Hit | Pins | Met by |
|---|---|---|
| `tests/test_uv.py:59,86` | the exact dev list `["httpx==0.28.1", "mypy==2.3.1", "pytest==9.1.1", "ruff==0.16.3"]` (and the one without httpx); `:151` the set of pins a feature adds over `base` | **T003** amends the two lists and `base` (one pin added each; the sync lines at `:94–98` stay byte for byte) |
| `tests/test_uv.py:94–104` | `uv sync --project "$app" --locked --quiet` and `run="uv run --project $app --no-sync"` in `scripts/verify` | hold: **T002** keeps both lines byte for byte |
| `tests/test_replay.py`, `tests/test_migrate.py`, `tests/test_add_service.py` | `project.json` before and after a replay, a migrate, an `add-service` | hold, **T001/T004**: any test that compares a whole `project.json` to a new project's learns the key in the task that adds it, named in the report |
| `tests/test_adopt.py`, `tests/test_adopt_facts.py`, `tests/test_adopted_manifest.py` | the adopted record's keys | hold, **T001/T004**: adopt writes no key (AC-S05-9) |
| `tests/test_verify_stamp_page.py`, `tests/test_gates.py` | the gates page's text (two adopted holds: an adopted page says nothing of a stamp) | watch, **T005**: the new paragraph is on every project's page, so a stamp-free adopted page may not gain a *stamp* word; amend only if a hold names the new text, and say so |
| `tests/test_matrix.py` | every backend's real `make verify` | watch, **T003/T006**: the plugin is installed for real; AC-S05-10's "test command unchanged" for TypeScript, Go and Java |
| `tests/test_parallel_gate_families.py`, `tests/test_verify_stamp_*.py` | the gate's Makefile and recipes by regex | hold: nothing in this slice edits `makefile.py` or `gate.py` |
| `tests/test_changelog.py` | the fragments' highest level against `VERSION` | hold: MINOR on `1.6.0.dev0`, run in T001's Verify |

## Format: `[ID] [P?] [Story] Description` — each task is one increment, one commit

`[P]` marks a task whose files are disjoint from a sibling's it could run beside; see *Parallel opportunities*.

---

## Phase 1: Implementation stage

Each task starts from the green committed suite. **T001 first and alone** (it lands the fragment and the `metadata()`
signature T004 extends).

### T001 — [US2] A new project is marked (R1 · AC-S05-1)

- [x] **Rule R1.** First commit that changes a user-visible tree, so the fragment's first draft lands in it (first
  line `MINOR`, the lead sentence, and a **Catch-up.** paragraph standing alone: a project made before stays serial and
  `"parallelSafe": true` is the one line that opts it in, then `make verify` once; T005 completes it).

**RED** (new `tests/test_xdist_mark.py`; `FactoryTestCase.generate` from `tests/support.py`):
- e1 `generate` a Python project → `project.json` parses and `["parallelSafe"] is True` *(fails today: no key)*.
- e2 `generate` a TypeScript project → `True` too, the key covering the whole project, whatever the backend *(fails
  today)*; the class: one example per backend the catalog offers (Python, TypeScript, Go, both Java).

**GREEN** — `metadata()` (`project/metadata.py`) takes the mark as a keyword and writes `"parallelSafe"` at the top
level beside `target`/`profile` only where it is given a boolean (`None` writes nothing — what T004's replay and every
other caller needs); `project_files` and `write_project` (`scaffold.py`) thread it; the `generate` path in `cli.py`
(`write_project` call) passes `True`. Nothing else passes it in this task, so replay, `add-service`, `adopt`, `converge`
and `resurvey` are unchanged until T004 — a test of theirs that now sees a changed `project.json` is named in the report.
`changelog.d/xdist.md` first draft.

**REFACTOR:** none expected; the keyword is one name through every layer, not a second flag.

**Verify:** `make test TESTS="test_xdist_mark test_changelog test_cli test_replay test_add_service test_adopt"` green,
then `make lint typecheck check-structure`. Commit by path; level line as above.

**Files:** `src/slipwai/project/metadata.py`, `src/slipwai/scaffold.py`, `src/slipwai/cli.py`, `changelog.d/xdist.md`
(new), `tests/test_xdist_mark.py` (new).

### T002 — [P] [US2] The mark reaches the gate's pytest at run time (R2 · AC-S05-2, -3, -4, -5)

- [x] **Rule R2.** Needs T001 only for a project with the key to exist in the generator; the gate's tests may also write
  the key into a copied `project.json` themselves, so the manifest is disjoint from T001's.

**RED** (new `tests/test_xdist_gate.py`; a generated Python project, a stand-in `uv` recording argv, `./scripts/verify`
run from the project root; the delegate reads how `tests/test_parallel_gate_families.py` and `tests/parallel_gate.py`
write a `uv` stand-in):
- e1 `"parallelSafe": true`: `--test-only` and the no-argument mode (`all`) each record a `pytest` line carrying
  `-n auto --maxprocesses 4` *(fails today: no flags)*.
- e2 the mark `false`; the key removed; `"yes"`; `1`; `"true"` (a string); `project.json` unreadable (not JSON) or
  absent → each `pytest` line has **no `-n`**, and every other word of the line equals the line from the key-removed run
  *(**hold** for the key-removed and `false` cases today; the string, number and unreadable cases are held by the same
  teeth — make the read treat any truthy value as on and see them fail)*; the change takes effect on the next run with
  nothing regenerated (the same project, `project.json` edited between two runs).
- e3 `--integration-only` with `true` → the `pytest` line has no `-n` *(**hold** today; teeth: add the flags to that mode)*.
- e4 `--adversarial-only` with `true` and a `-k` that matches nothing (the stand-in `pytest` exits 5) → the script exits 0
  and the line carries the flags *(fails today: no flags; the exit-5 half is a hold)*.
- Class: the three modes that take the flags and the one that does not, over a project with **two** Python services (each
  service's `pytest` line carries them), and a project whose `python3` is the one the gate already requires.

**GREEN** — `python_verify()` (`project/languages/python.py`): once, before the loop, the script reads `parallelSafe`
from the root `project.json` with `python3` (only the JSON `true` sets the flags; a failing read is serial, set `-e`
aware); `--test-only`, `all` and `--adversarial-only` splice the flags into their `pytest` command, `--integration-only`
never does. No variable, no argument, no template change: a person's `pytest` stays serial. The sync lines and the
`run=` line stay byte for byte (`tests/test_uv.py`). If the reading outgrows a few lines, the shell text still lives
in `python_verify`, never in a second generated file.

**REFACTOR:** the flags are one shell variable used by the three modes, not three copies.

**Verify:** `make test TESTS="test_xdist_gate test_uv test_parallel_gate_families test_verify_stamp_runs
test_flag_gate test_check_python"` green, then `make lint typecheck check-structure`. Commit by path; level line as above.

**Files:** `src/slipwai/project/languages/python.py`, `tests/test_xdist_gate.py` (new).

### T003 — [P] [US2] The plugin is installed, locked, and only the gate uses it (R3 · AC-S05-6, -7)

- [x] **Rule R3.** **Shares `src/slipwai/project/languages/python.py` with T002**, so it runs after T002 (or T002 after
  it), never beside it. Disjoint from T001, T004 and T005.

**RED** (new `tests/test_xdist_plugin.py`; the existing `tests/test_uv.py` is amended in this task, its pins named in
the sweep):
- e1 the dev list in each of the four selections' generated `pyproject.toml` (plain, `fastapi`, `postgres`,
  `fastapi`+`postgres`) contains `pytest-xdist==3.8.0` *(fails today)*.
- e2 each committed lock under `assets/languages/python/locks/` names `pytest-xdist` at 3.8.0 and `execnet`, and
  `uv sync --locked` accepts it (read the lock's `[[package]]` entries; run `uv lock --check` per selection where `uv`
  is present, skipped with its reason where not) *(fails today)*.
- e3 the template's `addopts` (read from the generated `pyproject.toml`) has no `-n` and equals what the template
  held *(**hold**; teeth: put `-n auto` in the template and see it fail)*.

**GREEN** — add `"pytest-xdist==3.8.0"` to `BASE_DEVELOPMENT` (`languages/python.py`), so every selection has it; run
`make locks` (network) so the four locks are rebuilt by the tool, never by hand, and read the diff: only the plugin and
`execnet` are added, no other pin moves. Amend `tests/test_uv.py` (the two exact dev lists and `base`).

**REFACTOR:** none expected.

**Verify:** `make test TESTS="test_xdist_plugin test_uv test_services test_backing_services test_axes"` green, then
`make check-locks` (network) reports no stale lock, then `make lint typecheck check-structure`. Commit by path; level
line as above (a new pinned tool in every Python service).

**Files:** `src/slipwai/project/languages/python.py`, `assets/languages/python/locks/uv.lock`,
`assets/languages/python/locks/uv-fastapi.lock`, `assets/languages/python/locks/uv-postgres.lock`,
`assets/languages/python/locks/uv-fastapi-postgres.lock`, `tests/test_xdist_plugin.py` (new), `tests/test_uv.py`.

### T004 — [P] [US2] What exists keeps its answer (R4 · AC-S05-8, -9)

- [x] **Rule R4.** Needs T001 (the `metadata()` keyword). Disjoint from T002, T003 and T005 by manifest.

**RED** (new `tests/test_xdist_carry.py`; `newer_factory`, `git` from `tests/test_replay.py`, `migrate` from
`tests/test_migrate.py`, `add_service` from `tests/test_add_service.py`, `adopted` and `slipwai` from
`tests/test_candidates.py`; a project "made before this release" is a generated project with the key removed and the
commit amended, as `tests/test_ci_fetch_migrate.made_before_the_slice` does):
- e1 replay and `migrate` of a project made before: its `project.json` has **no** `parallelSafe` afterwards *(fails
  today only once T001 has `generate` write it and replay would too — red here because `project_files` in replay is not
  yet told the project's own value; if the key does not appear, the example stands as a hold with teeth: make replay
  pass `True`)*.
- e2 a project whose mark is `false` and one whose mark is `true`: after replay and after `migrate`, the same value
  *(fails today: replay's regenerated document carries none, so `migrate`'s merge drops or keeps it by luck — observe
  first)*.
- e3 `adopt` and `adopt --refresh`: the record has no `parallelSafe`, and no adopted application's test command differs
  from the one recorded *(**hold**; teeth: make `adopt` pass `True`)*.
- e4 `add-service` on a project with `false` keeps `false`, and on one with no key adds none *(**hold** / red as read
  first; teeth: make it pass `True`)*.
- Class: replay, `migrate`, `converge`, `resurvey` and `add-service` — every caller of `project_files` the sweep finds
  (`grep -n "project_files(" src/slipwai`) — takes the project's own value from the document it loaded, `None` where
  there is no key.

**GREEN** — `replay.py` reads the project's own `parallelSafe` from the loaded document and passes it only where the
key is present (a boolean, as written); `add_service.py`, `converge.py` and `resurvey.py` pass the same for their
before/after pair so the key never appears as a difference; `adopt.py` passes nothing and is not edited if it already
passes nothing.

**REFACTOR:** the "own value or `None`" read is one small function used by every caller, not repeated.

**Verify:** `make test TESTS="test_xdist_carry test_xdist_mark test_replay test_migrate test_add_service test_adopt
test_adopt_facts test_adopted_manifest test_candidates test_ci_fetch_migrate"` green, then `make lint typecheck
check-structure`. Commit by path; level line as above.

**Files:** `src/slipwai/replay.py`, `src/slipwai/add_service.py`, `src/slipwai/converge.py`, `src/slipwai/resurvey.py`,
`src/slipwai/adopt.py` (only if it passes a value today), `tests/test_xdist_carry.py` (new).

### T005 — [P] [US2] The words are true (R5 · AC-S05-10, -11, -12, -13)

- [x] **Rule R5.** Needs T001 only for the fragment it completes; disjoint from T002–T004 except
  `changelog.d/xdist.md`, which no one but T001 and T005 touches.

**RED** (new `tests/test_xdist_page.py`; generated projects' `docs/gates.md`):
- e1 a Python project's page carries the mark's paragraph: the key `parallelSafe`, that new projects have it `true`,
  that **a missing mark is serial**, the flags `-n auto --maxprocesses 4`, and one sentence on when to set it `false`
  (tests that share a file, a port, a database or module-level state) *(fails today)*.
- e2 a TypeScript + Go + Java project's page says, for each backend it has, what its runner does — Vitest by file,
  `go test` by package, Surefire one at a time — and says nothing of a backend the project lacks *(fails today)*.
- e3 `changelog.d/xdist.md` exists, its first line is `MINOR`, and it holds exactly one paragraph beginning
  `**Catch-up.**` that, read alone, says a project made before stays serial and names the line `"parallelSafe": true`
  *(the file exists from T001; red on the missing sentence until completed)*.
- Class: e1/e2 over every backend the catalog offers, alone and mixed, and over an adopted repository's page
  (**hold**: it may gain the mark's paragraph but nothing about a stamp, and `tests/test_verify_stamp_page.py`'s two
  adopted holds stand unedited unless this task names why).

**GREEN** — new `src/slipwai/project/parallel_tests.py` holds the page text (the mark; one runner sentence per
backend, built from `backends_of(apps)`), and `docs.py` takes it in at most three lines; the fragment completed:
lead sentence, what the gate now does and the cap (D103), Python's integration run never parallel, the plugin pinned,
the three runners' words, and the **Catch-up.** paragraph. The measured times of AC-S05-13 are **left for the demo**
(a host edit, T009), so this task checks the paragraphs, not the figures.

**REFACTOR:** none expected.

**Verify:** `make test TESTS="test_xdist_page test_verify_stamp_page test_gates test_docs_index test_render_docs
test_changelog"` green, then `make lint typecheck check-structure`; `git diff --stat` shows `VERSION` unchanged. Commit
by path; level line as above.

**Files:** `src/slipwai/project/parallel_tests.py` (new), `src/slipwai/project/docs.py`, `changelog.d/xdist.md`,
`tests/test_xdist_page.py` (new), `tests/test_verify_stamp_page.py` (only if a hold names the new text).

### T006 — Every suite that reads generated Python output, once, before the gates (host task)

- [x] **Host task; no story.** After T001–T005 are committed, run, in one command, every suite that reads a generated
  Python project's dev list, `scripts/verify`, `project.json` or the gates page, so a break that no task's own Verify
  reached surfaces here and not in the full gate:
  `make test TESTS="test_uv test_matrix test_parallel_gate_families test_parallel_gate_sync test_parallel_gate_run
  test_verify_stamp_ships test_verify_stamp_page test_verify_stamp_pinned test_verify_stamp_scan
  test_verify_stamp_launches test_gates test_services test_running test_flag_gate test_host test_check_python
  test_replay test_migrate test_add_service test_adopt test_adopted_manifest test_candidates test_layout
  test_monorepos test_toolkit test_docs_index test_render_docs test_changelog test_xdist_mark test_xdist_gate
  test_xdist_plugin test_xdist_carry test_xdist_page"`, then `make lint typecheck check-structure`. A suite that
  fails is fixed in the owning task's files as a new task below (a test pinning old text is amended in tests only, and
  named), never skipped. Confirm the slice's diff touches nothing under `delivery/` or `tools/` and not `VERSION`.

---

## Phase 2: Host closing tasks

### T007 — Converge, two passes (host task)

- [x] `drive-converge` over the slice's diff, pass 1 then pass 2, at the loop's bound; every finding appends a task
  under *Phase 4* below (the S04 shape), and the verdict goes under `## Convergence`. The passes read the generated
  `scripts/verify` of a Python project under the real `uv` with the mark `true`, `false` and removed, `--integration-only`
  with the mark `true`, and a project replayed from before the release.

### T008 — After-converge gaps (host task)

- [x] `drive-gaps` traces AC-S05-1 … AC-S05-13 over the diff; each gap is answered by a decision entry and, where it
  changes code, a task appended below.

### T009 — The demo, with the measurement (host task)

- [x] The demo of [quickstart.md](quickstart.md) run as the actor with this checkout's `./slipwai`: `grep parallelSafe
  project.json`, `make test` showing `-n auto --maxprocesses 4`, the opt-out run, a project made before `migrate`d and
  still serial. **AC-S05-13:** on a fresh Python starter measure serial against parallel test time (three runs each,
  the command, the machine, its core count) and the median of `make -j verify` against the serial gate's (D89's
  criterion); the host writes the numbers into the quickstart and the fragment. If D103's *Would reverse if* fires
  (the capped run fails D89's criterion where serial passes), stop and hand the cap back as D103 says.

### T010 — The adversary pass (host task)

- [x] Per the trigger table in `delivery/skills/adversary` / `adversary-log.md`: `drive-adversary` over the one seam this
  slice opens — the mark's reader in the generated script (a `project.json` that is a directory, huge, invalid UTF-8,
  `{"parallelSafe": true, "parallelSafe": false}`, a symlink, run from another working directory) and `migrate` over a
  project with each value; confirmed findings become regression tests at the owning layer, appended as tasks below.

### T011 — Mutation (host task)

- [x] **N/A** — this repository records no mutation command in `project.json`, as for every slice before it; said in the
  register row and owed to the cruise report, not pretended.

### T012 — Both full gates on the final tip (host task)

- [ ] On the tree after the last task above: `make verify`, then `CI=true GITHUB_ACTIONS=true make -f delivery/Makefile
  verify` **once**, both green (Principle XIV); `make test TESTS="test_toolkit test_utf8_io test_changelog"` first as the
  slice touches `assets/`. Confirm `VERSION` is `1.6.0.dev0`, `assets/toolkit/scripts/verify-stamp.py` is not among the
  changed files, and nothing under `tools/`, the root `Makefile` or this repository's CI changed.

### T013 — Register row and benchmark close (host task)

- [ ] The slice's row in the register and `benchmark.json` closed, after-acceptance commits riding in this slice's own
  pull request (`AGENTS.md`).

---

## Parallel opportunities

By manifest (each task's *Files* line):

| Task | Writes | Imports another task's file |
|---|---|---|
| T001 | `metadata.py`, `scaffold.py`, `cli.py`, `changelog.d/xdist.md`, `tests/test_xdist_mark.py` | none |
| T002 | `languages/python.py`, `tests/test_xdist_gate.py` | `tests/parallel_gate.py`, `tests/stamp_fixture.py` (existing, unedited) |
| T003 | `languages/python.py`, the four `locks/*.lock`, `tests/test_xdist_plugin.py`, `tests/test_uv.py` | none |
| T004 | `replay.py`, `add_service.py`, `converge.py`, `resurvey.py`, (`adopt.py`), `tests/test_xdist_carry.py` | `metadata()`'s keyword (T001) |
| T005 | `parallel_tests.py`, `docs.py`, `changelog.d/xdist.md`, `tests/test_xdist_page.py`, (`tests/test_verify_stamp_page.py`) | the fragment (T001) |

- **May run together** (after T001 is committed): **T002 or T003** (chain A — they share `python.py`, so one of them at
  a time, T002 first because R3's lock rebuild needs the network and is slower), **T004** and **T005**: three disjoint
  manifests, so up to **three** delegates at once. T003's lock rebuild and `tests/test_uv.py` are disjoint from T004's
  `replay.py` and metadata callers, and from T005's page.
- **May not:** T002 beside T003 (the same `python.py`: `python_verify` and `BASE_DEVELOPMENT` are one file, and two
  worktrees would conflict on it); any task beside T001 (it writes `metadata.py` and the fragment first); T004 before T001
  (the keyword); T005 beside T001 (the fragment); T006 before T001–T005; nobody beside T006–T013.
- **Shared-tree caution.** The RED reversals and teeth of T002 and T003 change `python.py`, which every generated Python
  project in the other groups' tests is built from. Run each concurrent delegate in a worktree of its own off the commit
  that closes T001 (`isolation: worktree`), or run one group at a time while the others' quick tests run. The host
  commits by path in order — T001, then T002, T003, T004, T005 in any order that keeps T002 before T003 — and resolves no
  conflict by hand: a conflict is a manifest overlap, which this table says there is none of outside the one named.
- **Host tasks:** T006 runs alone after T005; T007–T013 follow in order. `[P]` is on T002, T003, T004 and T005 — each
  disjoint from at least the siblings named above — and nowhere else.

## Design review

No screen in this slice

## Convergence

*(Written by the converge stage, at the end of this file, after Phase 4.)*

## Differences from plan.md

Written for the host to correct the plan; none changes a requirement or a decision.

1. **The fragment lands in T001, not R5.** `changelog.d/xdist.md` is listed under R5's structure; the first commit that
   changes a user-visible tree is R1's, and `AGENTS.md` says the entry is written in the commit that makes the change.
   T001 writes a first draft (MINOR), T005 completes it.
2. **Every task owns a new test module** (`test_xdist_mark`, `_gate`, `_plugin`, `_carry`, `_page`); the plan suggested
   two. Split by rule so each stays well under 350 lines and each commit holds one rule's tests.
3. **R4 reaches `converge.py` and `resurvey.py`.** The plan names `replay.py`, `add_service.py` and `adopt.py`; the
   tree has two more callers of `project_files` that take a before/after pair and would show the key as a difference.

---

## Phase 4: Convergence pass 1 (cruise iteration 14)

Appended by `drive-converge`, pass 1 of 2, over `git diff 8b0d103 HEAD -- src tests assets changelog.d` at `e6abe1f`.
Reproductions ran on projects generated by this checkout under `/tmp/cv5` (Python, FastAPI, Postgres; real `uv`,
Python 3.14.4, pytest 9.1.1, pytest-xdist 3.8.0), on a project generated by the factory archived at `8b0d103`
(`git archive`) under `/tmp/cvm` and `slipwai migrate`d by this checkout, and through `tests/`' own helpers
(`newer_factory`, `migrate`, `own_mark`) in throwaway probe modules under `/tmp/cvt`. No production file was mutated.
Two `HIGH`: both are the catch-up a project made before this release is told to follow.

### T014 — `HIGH` — A mark a person adds by hand comes out of `migrate` once; the documented catch-up can leave it twice, and the gate obeys the last

- [x] **Finding.** The **Catch-up.** paragraph (`changelog.d/xdist.md:5`) and the gates page (`src/slipwai/project/parallel_tests.py:14-19`)
  say *add the line `"parallelSafe": true`* and nowhere say where. Replay reads the project's current `project.json`
  (`replay.py:74`, `recorded_parallel_safe`) and `metadata()` writes the key at one place, after `"target"`
  (`metadata.py:65`). The merge then sees the base without the key, the project adding it at line *m*, and the factory
  adding it after `"target"` — two hunks, merged cleanly, so `project.json` carries the key **twice** and `migrate` exits 0.
  The script's `json.load` takes the last occurrence (`python.py:177`), so a person who later sets the line they wrote to
  `false` — the one-line opt-out AC-S05-3 promises — keeps a parallel gate when theirs is the first of the two.
  `tests/test_xdist_carry.py` never meets this: `own_mark` writes the key and **amends the root commit**, so the mark is
  always in the base and the catch-up as written (the line added in a later commit) is untested.
  **Evidence.** Probe over `tests/`' helpers: made-before project (key line deleted, root amended), then a commit adding
  `  "parallelSafe": true,` after `"name"`, then `migrate` to a `newer_factory` → `rc=0`, clean status, two lines
  `"parallelSafe": true,`. The same line added after `"target"` → one line. A key appended at the end, then edited to
  `false` in place after a first migrate → `migrate` stops on `project.json` with conflict markers around the second
  copy. The reader on `{"parallelSafe": false, "parallelSafe": true}` → `-n auto` (parallel).
  **GREEN (the class).** Every route the published words give for writing the mark — added after `"name"`, after
  `"target"`, at the end, edited in place from `true` to `false` and back — survives `migrate` as exactly one key with the
  person's value: a carry test that makes each edit **in a commit after the root**, then migrates, and asserts one
  occurrence in the text (not only `json.loads`), red first for the after-`"name"` case. The fix is the host's to choose
  between (a) the offered side writes the key only where the base it is merged against already has it, so a mark the
  person added is the person's change alone, and (b) the reader in `scripts/verify` treats a duplicated `parallelSafe` as
  unreadable (serial, `object_pairs_hook`), with the catch-up and the page naming where the line goes; (b) alone leaves the
  duplicate in the file. Sweep: every `project.json` key the published words tell a person to add by hand (`ci.branch` is
  the other one the 1.6.0 notes name) gets the same later-commit carry example.

### T015 — `HIGH` — A project that changed its own Python dependencies meets a conflict on `uv.lock` that no catch-up note mentions

- [x] **Finding.** The slice adds `pytest-xdist` and `execnet` to every service's `pyproject.toml` and committed lock
  (`python.py:49`, the four `assets/languages/python/locks/*.lock`). A project that ever ran `uv add` has a lock of its own,
  so `migrate` stops on `apps/<service>/uv.lock`, and either side taken whole fails the gate's `uv sync --locked`
  (`python.py:170`). Constitution I: *`slipwai migrate` MUST leave a catch-up note for every change it cannot complete* —
  the **Catch-up.** paragraph (`changelog.d/xdist.md:5`) and the assembled `.slipwai/catch-up.md` say only that the project
  stays serial. The 1.6.0 entry already gives the npm twin of this (`scripts/event-model/package-lock.json`: take the
  factory's, or regenerate with `npm install --package-lock-only`); the Python lock has nothing.
  **Evidence.** `/tmp/cvm/shop`, generated by the factory at `8b0d103`; `uv add --project apps/service --dev
  freezegun==1.5.1`, committed; `slipwai migrate` with this checkout → *stopped at 1 conflict(s)*: `apps/service/uv.lock`
  (`UU`), `pyproject.toml` merged with both pins. `git checkout --ours -- apps/service/uv.lock` then `uv lock --project
  apps/service --check` → *To update the lockfile, run `uv lock`*. `grep` of `CHANGELOG.md`, `docs/` and the generated
  project's docs for a relock instruction → none.
  **GREEN (the class).** The fragment's **Catch-up.** paragraph, standing alone, names the conflict and its resolution
  for each service: take either side of `apps/<service>/uv.lock`, run `uv lock --project apps/<service>`, `git add` it,
  commit (in an adopted repository, the service's path as the record writes it). A test in `tests/test_xdist_page.py`'s
  fragment class asserts the paragraph names `uv.lock` and `uv lock --project`. Sweep: every fragment in `changelog.d/` whose
  change moves a committed lock under `assets/` (`git diff 8b0d103 HEAD --stat -- assets/**/locks`, and each later slice's)
  carries the same sentence for its ecosystem; a `make test-migration` run over a project that added a dependency of its own
  is the end-to-end form, for the host to judge whether it belongs in the suite.

### T016 — `MEDIUM` — `migrate` deletes a mark that is not a boolean when it sits in the base, and keeps it when it was added later

- [x] **Finding.** `recorded_parallel_safe` (`manifest.py:89-95`) carries only a boolean, so replay offers no key where the
  project wrote `"yes"`, `1`, `"true"` or `null`. D102 rule 3 says replay *writes the project's own value* and *never adds
  the key and never flips it*; deleting it is neither, and it is not even consistent: the merge deletes the line when the
  value was in the base, and keeps it when the person added it after. The gate's behaviour is the same before and after
  (serial), so nothing runs wrongly — but a person's own line in a file the project owns is removed by the factory with
  no word (constitution I: the factory does not delete what the project wrote except through a command it ran, and
  `migrate` is that command only for what the merge can show).
  **Evidence.** Probe: root commit `"parallelSafe": "yes"` → `migrate` fast-forwards, key absent after; root `1` → absent;
  `"yes"` added in a later commit → `'yes'` after. `tests/test_xdist_carry.py:43` `MARKS` covers no key, `false`, `true` only.
  **GREEN (the class).** The project's own value is carried as written, whatever its JSON type: `recorded_parallel_safe`
  returns the value or an absent marker, `metadata()` writes any present value, and the gate still reads only `true`
  as on (`python.py:177` is unchanged). A carry example per value — `"yes"`, `1`, `"true"`, `null`, `[]` — in the base and
  added later, through replay, `migrate`, `add-service`, `converge` and `resurvey`'s before/after pair, red first for `"yes"`
  in the base. The gates page says in its existing sentence that only the JSON `true` turns it on (a string `"true"` is
  serial).

### T017 — `LOW` — The mark is read by every mode, by an interpreter that imports from the project's root

- [x] **Finding.** The read (`python.py:176-179`) runs before the loop for every mode — `--lint-only`, `--typecheck-only`,
  `--format`, `--migrate`, `--integration-only` — none of which uses `$parallel`; under `make -j verify` that is three
  interpreter starts for one answer (≈17 ms each here). And `python3 -c` puts the working directory first on `sys.path`, so a
  `json.py` (or `json/`) at a project's root makes the import fail and the gate silently serial.
  **Evidence.** The reader extracted from `/tmp/cv5/shop/scripts/verify` and run in a scratch directory: with
  `json.py` beside `project.json` holding `{"parallelSafe": true}` → serial; without → parallel; `time` → 0.017 s real.
  **GREEN (the class).** The reader runs `python3 -I` (isolated: no cwd, no `PYTHON*` variables) and only in the three
  modes that splice `$parallel`; `tests/test_xdist_gate.py` gains a `json.py` at the generated project's root with the mark
  `true` and still sees the flags, and a `--lint-only` run whose stand-in `python3` log shows no read. Sweep: every other
  `python3 -c` the factory writes into a generated script (`grep -rn "python3 -c" src/slipwai/project`) takes `-I` where it
  reads only the standard library.

## Phase 4: Convergence pass 2 (cruise iteration 14, the loop's bound)

Appended by `drive-converge`, pass 2 of 2, over `git diff 8b0d103 HEAD -- src tests assets changelog.d` at `9902f44`.
Reproductions ran on projects generated by this checkout under `/tmp/cv2` (real `uv`, Python 3.14, pytest 9.1.1,
pytest-xdist 3.8.0, Vitest 4.1.11), on projects generated by the factory archived at `8b0d103` and `migrate`d by this
checkout, and on a scratch repository `adopt`ed by this checkout. No production file was mutated. Neither finding is
`CRITICAL` or `HIGH`; both are left as tasks because the loop stopped at its bound.

### T018 — `MEDIUM` — A mark added anywhere but after `"target"` comes out of `migrate` twice, silently, and the opt-in does nothing

- [x] **Finding.** T014's fix took pass 1's option (b): the reader in `scripts/verify` treats a key written twice as
  serial (`python.py:181`), and the catch-up and the gates page name where the line goes (`changelog.d/xdist.md:5`,
  `parallel_tests.py:19`). So the opt-out can no longer be defeated, which is what made T014 `HIGH`. What is left is the
  duplicate: `metadata()` writes the key after `"target"` (`metadata.py:65`), so a person who added it anywhere else —
  after `"name"`, at the end — gets the factory's copy beside theirs from the merge, `migrate` exits 0 and says nothing,
  and the `true` they wrote now reads as serial. The gate is in the safe direction (D102's deterministic over fast), and
  the assembled catch-up says *a mark written twice is serial*; but nothing tells the person that *their* file now has it
  twice, so the opt-in they made is inert without a word. Is the duplicate acceptable? To ship, yes: it fails safe, the
  published route avoids it (`TheLineTheCatchUpTellsAPersonToAddComesOutOnce` holds it), and it is visible in the merge.
  Left as is, no.
  **Evidence.** `/tmp/cv2/before/shop`, generated at `8b0d103`; a commit adding `  "parallelSafe": true,` after
  `"name"`; `slipwai migrate` with this checkout → *migrated … 5 files changed*, rc 0, `project.json` lines 10 and 14 both
  `"parallelSafe": true,`; the reader one-liner on that file → exit 1 (serial). `.slipwai/catch-up.md:17` carries the
  where-the-line-goes sentence.
  **GREEN (the class).** After the merge, `migrate` says one line naming `project.json` when a key the factory writes appears there more than once, and what the gate makes of it —
  or the offered side writes the key at the place the project already has it (pass 1's option (a)), so no duplicate
  arises. A carry example per route the words could be misread into — after `"name"`, at the end, after `"target"` — in a
  commit after the root: one key in the text after `migrate`, or the line said. Sweep: `ci.branch`, the other key the
  1.6.0 notes tell a person to add by hand, gets the same later-commit example.

### T019 — `LOW` — A module at the project's root named like one the xdist workers import crashes every worker where the serial run passes

- [x] **Finding.** T017's `-I` keeps the reader honest when a `json.py` sits at the project's root, so the mark now reads
  `true` there — and then pytest-xdist's workers, started from the root, import that `json.py` and crash: *maximum crashed
  workers reached: 48*, *no tests ran*, exit 5, and `--test-only` fails the gate. The same tree with the mark `false`
  passes all 87 tests per service. AC-S05-2 says the parallel run's pass/fail set equals the serial run's on the same
  tree; here it does not. Loud rather than silent, contrived (a root-level module shadowing a standard-library name), and
  the page's `false` sentence is the remedy — hence `LOW`.
  **Evidence.** `/tmp/cv2/two/shop` (two Python services): `json.py` holding `raise SystemExit(3)` at the root, mark
  `true` → `created: 4/4 workers` then the crash, rc 5; mark `false` → `87 passed` twice, rc 0.
  **GREEN (the class).** Either the gates page's sentence on when to set the mark `false` names a module at the project's
  root that shadows a standard-library name, or the gate's parallel `pytest` runs so that the workers' import path does
  not start at the root; a `tests/test_xdist_gate.py` example states which, with a stand-in that records the worker's
  working directory if the second.

### T020 — `MEDIUM` — The words the after-converge gaps pass found missing (G1–G3; D105)

- [x] **Host-routed fix, before the demo (it changes the page the demo reads).** RED first, as examples in
  `tests/test_xdist_page.py`: (G1) a TypeScript-, a Go- and a Java-only project's gates page names `parallelSafe`, says
  in one sentence what it does and that it changes nothing until a Python service is added, and no sentence opens
  with "the other runners" where no Python paragraph precedes it; (G2) the fragment's catch-up says a dependency of
  the project's own, dev or not, can stop `migrate` on a service's `uv.lock`; (G3) the page's sentence on `false`
  says the mark needs `pytest-xdist` in each Python service's development tools. GREEN in
  `src/slipwai/project/parallel_tests.py` and `changelog.d/xdist.md`. Sweep: every sentence of the mark's paragraph
  and the runners' paragraph read against a project of each backend family, and against a Python project after
  `add-service` of another backend.

**Verify:** `make test TESTS="test_xdist_page test_xdist_gate test_changelog"`, then `make lint typecheck check-structure`.

### T021 — `HIGH` — The line the catch-up note and the gates page tell a person to add breaks `project.json` (demo 1, `implementation`)

- [x] **Demo feedback, before demo 2.** Demo 1 followed the fragment's **Catch-up.** paragraph literally: `"parallelSafe": true`
  pasted after the `"target"` line, as the note and the page at `src/slipwai/project/parallel_tests.py` say, leaves
  `project.json` invalid (the line needs its trailing comma there) — the gate goes serial silently and `make verify`
  fails in `check-imports` (`demo/12-catch-up-literal.txt`). RED first in `tests/test_xdist_page.py`: the line both the
  note and the page name, pasted after a generated project's `"target"` line exactly as written, leaves JSON that
  parses with `parallelSafe` true. Sweep: every place a person is told to type or edit the mark — the page's opt-in,
  its `false` sentence, the note — held the same way. Also, from the demo: the page carries D103's rule 6 sentence
  (on a small suite the workers cost a fraction of a second; they pay once the suite takes several seconds), and the
  fragment carries AC-S05-13's measurement from `demo/17-timings.tsv` (medians of three on a 12-core i5-12400, a fresh
  Python starter, 87 tests: `./scripts/verify --test-only` 1.36 s with the mark, 0.99 s without; `make verify` 3.70 s
  and 3.30 s; `make -j verify` 2.11 s and 1.72 s), as S04's fragment carries its own.

**Verify:** `make test TESTS="test_xdist_page test_xdist_gate test_changelog"`, then `make lint typecheck check-structure`.


## Phase 4: Adversary pass (cruise iteration 15)

Appended by the host after the adversary pass (`adversary-log.md`, row `S05 · 8c7e4cd`) and its triage, D106–D108.
T022 and T023 have disjoint manifests and run concurrently; T024 follows both (it shares `python.py`,
`parallel_tests.py` with T022 and `manifest.py` with T023). The host writes the fragment's lines for all three.

### T022 — `HIGH` — A parallel run passes a test that leaks state into another, and CI runs it in parallel (A1, A2; D106)

- [x] **RED first**, in a new `tests/test_xdist_ci.py` (the gate's existing stand-in harness in `tests/test_xdist_gate.py`
  is the model; keep both files under 350 lines): (1) with the mark `true` and each of `CI`, `GITHUB_ACTIONS`,
  `GITLAB_CI` set alone — to `true` and to `false` — the generated `scripts/verify --test-only` and `all` run pytest
  with no `-n`; with none set, the flags are there; (2) with the mark `true`, `--adversarial-only` runs pytest with no
  `-n`, whatever the environment; (3) the page's mark paragraph carries one sentence that a parallel run can also hide
  a test that depends on another test's leftovers, because the two may run on different workers, so CI runs the suite
  serially to catch it. **GREEN** in `src/slipwai/project/languages/python.py` (the `parallel` reader's `case`: drop
  `--adversarial-only`; leave `parallel` empty when any of the three markers is non-empty — the stamp's own list and
  reading, `assets/toolkit/scripts/verify-stamp.py`) and `src/slipwai/project/parallel_tests.py` (the sentence; the page's
  existing words on which runs take the flags corrected to drop the adversarial run). Every existing test that reads the
  flags in a generated gate, or the page, keeps passing or is corrected to the new reading — search `tests/` for
  `maxprocesses` and `adversarial`. Tests that run a generated command build their environment with the three CI
  markers removed unless they set one. AC-S05-2, -5, -14.

**Verify:** `make test TESTS="test_xdist_ci test_xdist_gate test_xdist_page test_xdist_plugin"`, then
`make lint typecheck check-structure`.

### T023 — `MEDIUM` — A key written twice in `project.json` is collapsed by `add-service`, `describe-service` and `adopt --refresh`, and `migrate` makes one without a word (B1, T018; D107)

- [x] **RED first**, in a new `tests/test_manifest_duplicates.py`: the B1 file (`"parallelSafe": false,` after `"name"`,
  the generated `true` after `"target"`) through `add-service`, `describe-service` and `adopt --refresh` (an adopted
  scratch repository) — each exits non-zero with one line naming `project.json`, the key and "keep one copy";
  `project.json` byte-for-byte unchanged; nothing committed. A duplicate nested in `deployables` refused the same way.
  `migrate` over a project whose `project.json` already holds a duplicate refuses before the replay. `migrate` over a
  project made at the commit before the slice with the mark added (in a commit after the root) after `"name"`, and at
  the end: exit 0, the merge kept, one line saying the key is twice, the gate reads it serial, keep one copy — and the
  same sentence in `.slipwai/catch-up.md`; after `"target"`: one key, no line. `ci.branch` placed by hand away from
  where the factory writes it: the same `migrate` line, and a refusal through `add-service`. **GREEN**: one reader
  with a standard-library `object_pairs_hook` that refuses a key written twice at any depth — in `src/slipwai/manifest.py`
  (`read_manifest` or a sibling sharing its check) — and every factory read of a project's `project.json` goes through it
  (`grep -rn 'project.json' src/slipwai` and every `json.loads` near it: `add_service.py`, `resurvey.py`, `replay.py`,
  `migrate.py`, `confirm`, `add-frontend`, `survey`, `cli_init`); `migrate` reads the merged file after a clean merge
  and says the line. This closes T018. AC-S05-15. Do not touch `changelog.d/` (the host writes the fragment's line),
  `src/slipwai/project/languages/python.py` or `src/slipwai/project/parallel_tests.py`.

**Verify:** `make test TESTS="test_manifest_duplicates test_xdist_carry test_xdist_mark"` and every module that tests
`migrate`, `add-service`, `describe-service`, `adopt` or `confirm` (`ls tests | grep -E 'migrate|add_service|describe|adopt|confirm|resurvey|replay|manifest'`),
then `make lint typecheck check-structure`.

### T024 — `LOW` — The plugin with autoload off, the words on a root module and `-p no:xdist`, the page of a project with no Python, and a non-finite mark (A3, B2, B3, T019; D108)

- [x] **RED first**, in a new `tests/test_xdist_words.py`: (1) with the mark `true` and `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`,
  a generated Python project's real `./scripts/verify --test-only` starts its workers (`created:`), and without it no
  "already registered" error — the spelling (`-p xdist` or `-p xdist.plugin`) is the one that passes both; `FLAGS` in
  `parallel_tests.py` and the script carry the same words; (2) the page's sentence on when to set the mark `false` names a
  module at the project's root named like a standard-library one (a `json.py`) as crashing every worker with
  *maximum crashed workers reached*, and the plugin sentence names `-p no:xdist` in `PYTEST_ADDOPTS` as the same case as a
  service that removed the plugin; (3) a project with no Python service gets "Where `project.json` carries
  `"parallelSafe": true`, a Python service's tests run across cores; it changes nothing until a Python service is
  added."; (4) a mark `1e400` and one `NaN`, through `describe-service` and `migrate`, are refused with one line naming
  the file, the key and the value and saying to set `true` or `false`, `project.json` byte-identical. **GREEN** in
  `src/slipwai/project/languages/python.py`, `src/slipwai/project/parallel_tests.py`, `src/slipwai/manifest.py`
  (`recorded_parallel_safe`). If no `-p` spelling passes both settings, the page sentence names
  `PYTEST_DISABLE_PLUGIN_AUTOLOAD` instead and the flags stay (D108 part 2's fallback). This closes T019. AC-S05-16.

**Verify:** `make test TESTS="test_xdist_words test_xdist_ci test_xdist_gate test_xdist_page test_xdist_carry"`, then
`make lint typecheck check-structure`.


### T025 — The two maintenance skills name the gates page's per-backend table (a person's note, iteration 15; D109)

- [x] **From the owner, through `/cruise-tell`.** `tests/test_maintenance_skills.py::test_every_language_keyed_table_is_documented`
  is red: `parallel_tests_page` in `src/slipwai/project/parallel_tests.py` indexes `RUNNERS` by backend, and the
  `add-language` and `add-framework` skills must name it. Fixed inside S05, before its gates: `add-language` section 2
  item 14 and a row in `add-framework`'s table (`.claude/skills/add-language/SKILL.md`,
  `.claude/skills/add-framework/SKILL.md`). Factory-maintenance text — reaches no user.

**Verify:** `make test TESTS="test_maintenance_skills test_backend_obligations"`.

## Convergence

**Not converged — pass 1 of 2 (cruise iteration 14, `drive-converge`, host model, fresh context): two `HIGH` open, T014
and T015, both on the path a project made before this release is told to take; T016 `MEDIUM` and T017 `LOW` beside
them.** The tree was clean after the pass; nothing outside this file was written.

**What each level proves, and what it does not.**

- **Domain.** None: the factory has no domain layer, and the slice touches no generated domain code.
- **Use cases.** `generate` writes `true` (`cli.py:281` → `scaffold.py:100`, `scaffold.py:213-216` → `metadata.py:65`):
  proved by `test_xdist_mark` and by `/tmp/cv5/shop/project.json:13`. Replay, `migrate`, `add-service`, `converge`,
  `resurvey` take the project's own boolean (`replay.py:102-105`, `add_service.py:215-217`, `converge.py:103-106`,
  `resurvey.py:244-246`, through `manifest.py:89-95`); `adopt` passes none: proved for no key / `false` / `true` **in the
  base**; not proved for a mark added later (T014, which breaks) or a non-boolean (T016, which is deleted).
- **Delivery adapter — the generated `scripts/verify`.** Real `uv`, mark `true` → `created: 4/4 workers`, 87 passed;
  `false` and removed → no workers, 87 passed (the pass/fail set equal, AC-S05-2); `true` back on the next run with nothing
  regenerated (AC-S05-3); `--integration-only` with `true` → no workers (AC-S05-4); `--adversarial-only` with `true` → 4
  workers, 0 items, exit 0 (AC-S05-5). The reader on a directory, a top-level list, a UTF-8 BOM, a symlink, duplicate keys:
  serial except a symlink to `true` and a duplicate ending in `true` (T014). The script already requires the project root as
  its working directory (`apps/service` is relative; from `apps/service` it fails at `uv sync`), and every caller —
  the Makefile's recipes, CI's `--install-only` step (which exits before the read) — runs it from there. Under `make -j
  verify` only `test` reads the mark that matters; `adversarial` is not in `verify-checks`; each mode reads once, and two
  modes disagree only if `project.json` is edited mid-run. The stamp keys on every tracked file
  (`assets/toolkit/scripts/verify-stamp.py:11-12`), so an edited mark is never answered by a stale stamp. Windows/Git
  Bash: the one-liner is single-quoted with only double quotes inside, valid in any POSIX `sh`; a missing or Store-stub
  `python3` reads as serial, and the same script's `compileall` already needs a real one — not a finding.
- **Screen.** None.
- **Published contract.** The `project.json` key is additive (`metadata.py:65`, written only when given). The gates
  page (`parallel_tests.py:14-36`, `docs.py:156`) is true of what runs, names only the backends a project has, and is empty
  for an adopted repository's own applications (`services.py:196` filters `generated`; this repository's page gains
  nothing). The fragment claims MINOR on `VERSION` `1.6.0.dev0` (`changelog.d/xdist.md:1`); its **Catch-up.** paragraph
  stands alone but omits where the line goes (T014) and the lock conflict (T015).
- **Locks.** All four committed locks only *add* `execnet 2.1.2` and `pytest-xdist 3.8.0` (no `-` line in `git diff
  8b0d103 HEAD` of any of them); `test_xdist_plugin`'s `uv lock --check` per selection ran (not skipped) and passed; a real
  `uv sync --locked` of the FastAPI + Postgres selection installed them.

**Constitution, principle by principle.**

- **I — owns its files, passes its own gate.** *Catch-up note for every change `migrate` cannot complete:* **unmet** for a
  project with its own lock (T015). *The factory deletes nothing the project wrote outside what the merge shows:* the
  non-boolean mark (T016). *Every starter passes its own gate:* the matrix suite ran at T006 (`e6abe1f`); this pass re-ran
  one starter's tests for real, not the matrix. *`VERSION` and a fragment naming its level:* `VERSION` 1.6.0.dev0,
  `changelog.d/xdist.md:1` `MINOR`. *A memoised or scoped gate is additive:* no check removed; the integration run stays
  serial (`python.py:207-212`); the stamp re-runs on an edited mark.
- **VIII — a persisted schema is additive, readers tolerant.** The key is new and optional (`metadata.py:65`); the factory's
  reader tolerates its absence and any type (`manifest.py:94-95`) but does not carry what it does not understand (T016).
- **XIII — fast feedback (in force in a generated project).** *No shared mutable environment, no ordering between tests:*
  xdist on the default suite enforces it from a project's first test; the database-backed suite is kept serial
  (`python.py:207-212`). The measured times are AC-S05-13's, at the demo (T009).
- **Additional constraints.** *Persisted data records facts true on any machine:* the key is a boolean, the worker count is
  resolved at run time (`python.py:178`). *Every read names its encoding:* `python.py:177` (`encoding="utf-8"`).
- **XIV — agent-generated change meets the same bar.** The full gates are T012's, after demo acceptance; not run here.
- **II, III, IV, V, VI, VII, IX, X, XI, XII, XV** — not touched: no write endpoint, no new layer or service, no domain
  code, no integration, no telemetry, no security surface, no CI or pipeline change, no domain types.

**For pass 2.** Re-run the T014 and T015 reproductions after their tasks close; reach what this pass did not: two Python
services in one project under real `uv`, a mixed Python + TypeScript project's `make -j verify`, `add-service` of a Python
service into an adopted repository then the opt-in line, and `resurvey`/`converge` over a project carrying `false`.

### Pass 2

**Converged at the loop's bound: no `CRITICAL` or `HIGH` open — pass 2 of 2 (cruise iteration 14, `drive-converge`,
host model, fresh context, at `9902f44`). T014–T017 are closed and reproduce no longer; T018 `MEDIUM` and T019 `LOW` are
left as Phase 4 tasks because this is the bound, and neither re-opens the loop.** The slice's suites
(`test_xdist_mark _gate _plugin _carry _page`, `test_changelog`, `test_uv`) ran green, 62 tests, one skip that is
`test_changelog`'s no-release-tag skip; `make lint check-structure` green. No production file was mutated; the tree's
status is what it was at the start; nothing outside this file was written.

**Pass 1's findings, against HEAD.**

- **T014 — closed; its class reduced to T018.** The reader treats a duplicated key as serial (`python.py:181`): a project
  made at `8b0d103` with the mark added after `"name"` and `migrate`d still carries two keys, and now reads serial, so the
  opt-out can no longer be defeated. The words name the place (`changelog.d/xdist.md:5`, `parallel_tests.py:19`, and the
  assembled `.slipwai/catch-up.md:17`); the after-`"target"` route and the edit-in-place route come out as one key
  (`tests/test_xdist_carry.py:146,160`). The duplicate left in the file is T018.
- **T015 — closed.** `/tmp/cv2/lock/shop` (made at `8b0d103`, `uv add --dev freezegun==1.5.1`, committed): `migrate`
  stops on `UU apps/service/uv.lock`; the catch-up's steps followed literally — `git checkout --ours`, `uv lock --project
  apps/service`, `git add`, commit — and `./scripts/verify --test-only` syncs `--locked` and passes 87 tests. Pinned by
  `tests/test_xdist_page.py:113`.
- **T016 — closed.** Replay of a project carrying `"yes"`, `null`, `1` writes each back as written; the gate stays
  serial on each (no `created:` line). `manifest.py:93-98` returns the value or `ABSENT`; `metadata.py:65` writes any
  present value; the carry class covers base and added-later through replay, `migrate`, `add-service`, and the
  `converge`/`resurvey` pair (`tests/test_xdist_carry.py:179-225`).
- **T017 — closed; the sweep judged.** `-I` and the three-mode `case` (`python.py:178-184`); a `json.py` at the root no
  longer turns the mark off (and see T019 for what that exposes). The sweep's other `python3 -c` sites — `check-python`
  (`agent_targets.py:19`, imports only `sys`, a builtin no file can shadow) and `init_pyyaml.py:45-54` (asks whether
  *this* interpreter can import `yaml`, where `-I` would change the answer) — rightly keep no `-I`; `c971759`'s revert is
  correct.

**What each level proves, and what it does not.**

- **Domain.** None: no domain layer in the factory, no generated domain code touched.
- **Use cases.** `generate` writes `true` for every backend (`cli.py:281` → `scaffold.py:215` → `metadata.py:65`).
  `add-service` of a second Python service keeps `true` (`/tmp/cv2/two/shop`); of a Python service into an adopted
  repository adds no key (`/tmp/cv2/adopted`, D102 rule 5). `adopt --refresh` over an adopted repository carrying `false`
  and then `"yes"` keeps each (line 14 before and after), and `converge --check` lists neither `project.json` nor the mark
  among its clashes (`resurvey.py:244-246`, `converge.py:103-106`). `converge`'s move itself was not reached — the
  scratch repository's rows are below target — and is held by the before/after pair test only. Not proved: a mark outside
  the published place coming out once (T018).
- **Delivery adapter — the generated `scripts/verify`.** Two Python services under real `uv`, mark `true`: each service's
  run `created: 4/4 workers`, 87 passed, twice; `false`: no workers, the same 87 passed twice. A mixed Python + TypeScript
  project (`add-service orders --backend typescript`, plus the React frontend) under real `make -j verify`: `verify: all
  gates passed`, 9.3 s; Python `created: 4/4 workers`; Vitest's commands unchanged (`npm --workspace apps/<x> test`,
  AC-S05-10); the mixed project's script is `scripts/verify-python` and still reads the root `project.json`, since every
  recipe runs from the root. In the adopted repository, `delivery/scripts/verify --test-only` run from the root with the
  mark added after `"target"` → `created: 4/4 workers`, 32 passed. Not proved: the parallel run's equality with the
  serial one where a root module shadows a standard-library name (T019).
- **Screen.** None.
- **Published contract.** The key is additive and carried as written (`metadata.py:65`, `manifest.py:93-98`). The
  gates page names the mark, the place, *twice is serial*, and only the runners the project has
  (`parallel_tests.py:14-41`, `docs.py:156`; the mixed project's page carries the mark and the Vitest sentence, no Go or
  Java). The fragment claims MINOR on `VERSION` `1.6.0.dev0` (`changelog.d/xdist.md:1`) and its **Catch-up.** paragraph
  (`:5`) stands alone with the place, the lock conflict and its resolution.
- **Outside the slice, handed back (not a task here).** In an adopted repository, `add-service` of a Python service
  writes `delivery/scripts/verify`, but `delivery/Makefile`'s recipes call `./scripts/verify` from the root
  (`delivery/Makefile:21,118` of the scratch repository): `make -f delivery/Makefile test` fails *No such file*, Error
  127. The factory archived at `8b0d103` writes the same (`/tmp/cv2/adopted-old`), so it predates S05 and is not this
  slice's; but it means the gates page's *`make test` … adds the flags* is unreachable in an adopted repository until it
  is fixed. For the host to route to the register or a slice of its own.

**Constitution, principle by principle.**

- **I — owns its files, passes its own gate.** *No file overwritten or deleted except through a command the maintainer
  ran:* the project's own mark is carried whatever its value (`manifest.py:98`, `metadata.py:65`, through `replay.py:104`,
  `add_service.py:215-217`, `converge.py:105`, `resurvey.py:244-246`); the duplicate T018 names is a merge result the
  maintainer's `migrate` shows, not a deletion. *Catch-up note for every change `migrate` cannot complete:* met for the
  lock conflict and the opt-in (`changelog.d/xdist.md:5`, reproduced end to end). *Every starter passes its own gate:*
  the matrix ran at T006; this pass ran two real gates (two Python services; Python + TypeScript under `-j`), both green.
  *`VERSION` and a fragment naming its level:* `1.6.0.dev0`, `changelog.d/xdist.md:1` `MINOR`; the diff does not touch
  `VERSION`. *A scoped gate is additive:* no check removed; the integration run never takes the flags
  (`python.py:215-217`).
- **VIII — persisted schema additive, readers tolerant.** The key is new and optional (`metadata.py:65`); the factory's
  readers tolerate any value and carry it unchanged (`manifest.py:93-98`); the gate's reader tolerates every value,
  a duplicate and an unreadable file, reading only the JSON `true` as on (`python.py:181`).
- **XIII — fast feedback** (target here, in force in a generated project). *No shared state between tests:* xdist on the
  default suite from a project's first test; the database-backed suite serial (`python.py:217`). T019 is the one case
  where the parallel run differs from the serial. AC-S05-13's times are T009's.
- **Additional constraints.** *Persisted data records facts true on any machine:* the key is a value, the worker count
  resolved at run time (`python.py:182`). *Every read names its encoding:* `python.py:181` (`encoding="utf-8"`).
- **XIV — agent-generated change meets the same bar.** The full gates are T012's, after demo acceptance; not run here.
- **II, III, IV, V, VI, VII, IX, X, XI, XII, XV** — not touched: no write endpoint, no new layer, service or
  integration, no domain code or types, no telemetry, no security surface, no CI or pipeline change.
