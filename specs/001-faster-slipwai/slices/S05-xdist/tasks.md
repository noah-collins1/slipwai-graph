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

- [ ] **Rule R1.** First commit that changes a user-visible tree, so the fragment's first draft lands in it (first
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

- [ ] **Rule R2.** Needs T001 only for a project with the key to exist in the generator; the gate's tests may also write
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

- [ ] **Rule R3.** **Shares `src/slipwai/project/languages/python.py` with T002**, so it runs after T002 (or T002 after
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

- [ ] **Rule R4.** Needs T001 (the `metadata()` keyword). Disjoint from T002, T003 and T005 by manifest.

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

- [ ] **Rule R5.** Needs T001 only for the fragment it completes; disjoint from T002–T004 except
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

- [ ] **Host task; no story.** After T001–T005 are committed, run, in one command, every suite that reads a generated
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

- [ ] `drive-converge` over the slice's diff, pass 1 then pass 2, at the loop's bound; every finding appends a task
  under *Phase 4* below (the S04 shape), and the verdict goes under `## Convergence`. The passes read the generated
  `scripts/verify` of a Python project under the real `uv` with the mark `true`, `false` and removed, `--integration-only`
  with the mark `true`, and a project replayed from before the release.

### T008 — After-converge gaps (host task)

- [ ] `drive-gaps` traces AC-S05-1 … AC-S05-13 over the diff; each gap is answered by a decision entry and, where it
  changes code, a task appended below.

### T009 — The demo, with the measurement (host task)

- [ ] The demo of [quickstart.md](quickstart.md) run as the actor with this checkout's `./slipwai`: `grep parallelSafe
  project.json`, `make test` showing `-n auto --maxprocesses 4`, the opt-out run, a project made before `migrate`d and
  still serial. **AC-S05-13:** on a fresh Python starter measure serial against parallel test time (three runs each,
  the command, the machine, its core count) and the median of `make -j verify` against the serial gate's (D89's
  criterion); the host writes the numbers into the quickstart and the fragment. If D103's *Would reverse if* fires
  (the capped run fails D89's criterion where serial passes), stop and hand the cap back as D103 says.

### T010 — The adversary pass (host task)

- [ ] Per the trigger table in `delivery/skills/adversary` / `adversary-log.md`: `drive-adversary` over the one seam this
  slice opens — the mark's reader in the generated script (a `project.json` that is a directory, huge, invalid UTF-8,
  `{"parallelSafe": true, "parallelSafe": false}`, a symlink, run from another working directory) and `migrate` over a
  project with each value; confirmed findings become regression tests at the owning layer, appended as tasks below.

### T011 — Mutation (host task)

- [ ] **N/A** — this repository records no mutation command in `project.json`, as for every slice before it; said in the
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

*(Written by the converge stage.)*

## Differences from plan.md

Written for the host to correct the plan; none changes a requirement or a decision.

1. **The fragment lands in T001, not R5.** `changelog.d/xdist.md` is listed under R5's structure; the first commit that
   changes a user-visible tree is R1's, and `AGENTS.md` says the entry is written in the commit that makes the change.
   T001 writes a first draft (MINOR), T005 completes it.
2. **Every task owns a new test module** (`test_xdist_mark`, `_gate`, `_plugin`, `_carry`, `_page`); the plan suggested
   two. Split by rule so each stays well under 350 lines and each commit holds one rule's tests.
3. **R4 reaches `converge.py` and `resurvey.py`.** The plan names `replay.py`, `add_service.py` and `adopt.py`; the
   tree has two more callers of `project_files` that take a before/after pair and would show the key as a difference.
