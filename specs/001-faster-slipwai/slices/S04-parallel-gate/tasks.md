# Tasks: S04-parallel-gate — the gate's independent checks run at once and each toolchain syncs once

**Input**: [plan.md](plan.md) (*The example map* R1–R8 is what the tasks cut on; *Design*; *Pin*; *Project
Structure*; *Constraints*), [research.md](research.md), [data-model.md](data-model.md), [quickstart.md](quickstart.md);
acceptance criteria AC-S04-1 … AC-S04-63 in `specs/001-faster-slipwai/spec.md` under `### S04-parallel-gate`;
decisions D12, D74, D78, D81, D83, D88, D89, D90, D91, D92 in `specs/001-faster-slipwai/decisions.md`. No
`examples.md`: a method slice with no screen and no event model of its own, so **no white box, no mockup task and no
styling task**; the one story is **US1**, *a developer's `make -j verify` gives the serial run's verdict in about
half the time, each toolchain syncs once per `make` run, and a failed run says where to look*.

**Branch**: `adopt-method` (D12). No `slice/` branch, no push, no claim. One commit per task.

**Delegation** (`.specify/drive.json`: `delegate: story`, `cycle: rule`): `delegate: story` means the host hands **one
`drive-implement` delegate the whole of US1** — T002 to T009, in dependency order — rather than one delegate per
task; `cycle: rule` means each RED-GREEN-REFACTOR cycle opens with **one rule's examples** (R1 … R8), so each task
below is one cycle and one commit, and a delegate never writes a rule's tests ahead of the previous rule's commit.
Where manifests are disjoint the host **may hand the story to more than one delegate** — each its own tasks, each in a
worktree of its own (*Parallel opportunities* says which and why); the "Files" line of a task is its manifest, the
only files that delegate may write. Nobody but the host writes `tasks.md`. A delegate that finds it needs a file
outside its manifest — a test elsewhere that pins the text it changes — **stops and names the file; the host adds it.**
A delegate that finds it must change `assets/toolkit/scripts/verify-stamp.py` stops and hands back: the split of that
script is `S32-verify-stamp-split`, which lands first (D91, D92; AC-S04-62).

**Not a task:** AC-S04-22 and -23 (on AC-S03-20's project, the median of three `VERIFY_FORCE=1 make -j verify` runs is
lower than the serial median; the numbers, the command, the machine and its core count written into the quickstart and
the fragment) are the demo's: the hand measures, the host writes the numbers back; the suite holds causes, never a
clock. So are the runs with the **real toolchain** — AC-S04-5, AC-S04-17, R5e6, and AC-S04-47's real `npm ci` on a
fresh clone — which need Go, Java, Node and the registry: the delegate of T006 and T008 runs each once by hand and
reports it (as S24's T008 did its e4), the demo runs them again (quickstart §1, §5, §3), and the suite adds no test
that needs a toolchain this machine may lack. AC-S04-62 (S04's diff does not name `verify-stamp.py`) is a check of the
whole diff, so it is the host's at T010, not a test.

## Constraints that hold for every task

Plan *Constraints*, stated once, then this run's standing lessons:

- **MINOR, `VERSION` stays `1.6.0.dev0`** (D91: one new generated file, the lockfile). Nothing newer than GNU Make 3.81
  documents is used in a generated Makefile, except output grouping behind a test of `.FEATURES` (D92): no `.WAIT`, no
  `.NOTPARALLEL` with a prerequisite, no `$(file …)`, no `grouped targets`. `ifdef`/`endif`, `$(eval)` and `$(if)` are 3.80/3.81.
- **Not edited, by any task:** `assets/toolkit/scripts/verify-stamp.py` (comment included); anything under this
  repository's `delivery/scripts/`, `tools/`, the root `Makefile`, this repository's own CI or hook settings
  (`delivery/Makefile` takes the adopted line by `slipwai migrate`, a person's — D9); `VERSION`; anything under
  `release/`; no file `delivery/.written` lists. No check is removed, weakened or reordered out of the gate (Principle I);
  the generated CI workflow and the ladder's commands keep typing `make verify` (AC-S04-21).
- **Size and width.** Every file under `src/` and `tests/` stays within 350 lines (`make check-structure`) and 120
  columns (ruff). `makefile.py` is **328**, `docs.py` **329**, `native_commands.py` **308**, `backends.py` **331**: what
  this slice adds goes in `parallel_gate.py` (new, `src/slipwai/project/`) and `gate.py`; an edit to one of the four
  may not take it past 350, and if it would, the code moves to `parallel_gate.py` and the report names it. A test file
  that nears 350 splits by rule or example and the report names the new file; the splits are made in advance below.
  Every `read_text`/`open` in a toolkit script or a test names `encoding="utf-8"`.
- **Tests.** Standard library only; a fake is an executable or a class written in the test tree implementing the
  tool's real command line — **never a mocking framework, `unittest.mock` included**. Evidence is a stand-in's log, never
  a printed line. **No wall-clock assertion**: concurrency is shown by a **barrier** — a stand-in that, after logging
  its start, waits *bounded* (a stand-in's own loop, with a ceiling, never `sleep` as proof) for another stand-in's
  start line and logs `met` or `alone` — and the test reads `met`/`alone`, never the elapsed time.
- **Environment of a run.** A test that runs a generated project's command builds its environment with `CI`,
  `GITHUB_ACTIONS` and `GITLAB_CI` **removed** unless the example sets one, **and** with `MAKEFLAGS`, `MFLAGS` and
  `MAKELEVEL` (and `MAKEOVERRIDES`, `MAKEFILES`, `GIT_DIR`, `GIT_WORK_TREE`, `GIT_INDEX_FILE`) removed, so the
  factory's own `make test` does not leak its jobs into the project's make: `tests/stamp_fixture.py` already holds the
  three tuples (`CI_MARKERS`, `MAKE_STATE`, `GIT_STATE`) and `tests/parallel_gate.py` imports them, never re-lists them.
- **A test that can hang runs under a timeout.** Every `subprocess.run` of a `make` carries `timeout=` (180 s is the
  stamp suites' bound; a barrier's own ceiling is far below it), and a stand-in that waits has a ceiling in its loop.
- **A test that loads a toolkit script as a module sets `sys.dont_write_bytecode = True` first**; a teeth check leaves
  **no `__pycache__` under `assets/toolkit/scripts/`** (`git status --short assets/toolkit` shows only the task's own files).
- **Commit by path** — `git commit -m … -- <the task's files>` — a new file `git add`ed by its exact path first; never
  `git add -A`, never `git commit -a`, never `git checkout -- <file>` on uncommitted work (a file with edits that are
  not yours to discard). The sanctioned route for observing a failure on a production file is: change it, run the test,
  restore with `git checkout -- <exact path>` **only for a change you made and have not committed over**; confirm
  `git status` shows only the task's own files.
- **RED is seen** for its stated reason before the production file is touched. A **hold** is written as a hold, saying
  so in the test's name or docstring, and is **seen to have teeth** before it is committed: change the production file (or
  invert one assertion, or break the fixture), observe the failure, restore; the tree is clean of the reversal on every
  exit path, a stop included. Where a hold's teeth cannot be shown by the means the task names, the report says so —
  a hold with no teeth is not claimed.
- **GREEN is a class**, not an instance: every backend family, every transport, every service count the criterion
  names, each with its example; the sweep that closes the class is in the task, and the report names where else the
  same shape occurs.
- **Before each commit** run `make lint typecheck check-structure`. **The slice touches `assets/toolkit/`** (T008's
  lock), so before the full gates `make test TESTS="test_toolkit test_utf8_io test_changelog"` is run (T008's Verify and
  T010).
- **Pinned suites (AC-S04-63).** Two of S03's suites are amended and **no other S03 suite is edited** —
  `tests/test_verify_stamp_recipe.py` (T005) and `tests/test_verify_stamp_pinned.py` (T007); each amendment is in the
  task whose change breaks it, below. Every other `tests/test_verify_stamp_*.py` passes **unchanged**; a task whose
  change turns one red stops and names it.

### The sweep at planning

Run for this slice as S24's precedent describes: tests under `tests/` that pin the whole text of a generated Makefile,
a recipe, `scripts/verify`, the adopted gate or the model targets, and helpers that rebuild an old Makefile by regex.
**Hits** (named in the task that will meet each; none is edited by a task that does not list it in *Files*):

| Hit | Pins | Met by |
|---|---|---|
| `tests/test_verify_stamp_recipe.py` `assert_recipe` | the substring `"$(MAKE)" --no-print-directory -f "$(firstword $(MAKEFILE_LIST))" verify-checks`; `$(VERIFY_GROUP)` goes between `"$(MAKE)"` and `--no-print-directory` | **T005** (R4) amends it |
| `tests/test_verify_stamp_pinned.py` `WrappedGatePinnedTest` (two tests) | the adopted `verify` rule byte for byte, prefixed `.PHONY: verify ci\n` and followed by `ci: verify ` | **T007** (R6) amends it |
| `tests/test_verify_stamp_pinned.py` generated half, and its importers `tests/test_verify_stamp_ships.py`, `tests/test_check_python.py` | `gate_prerequisites(makefile)` (every `^verify-checks:` line), `gate_rule(...).endswith(CLOSING)`, `[0] == "check-python"`, the `GENERATED`/`STANDARD` order | hold: T003 must not put a line beginning `verify-checks:` anywhere but where it is now, nor change that line; T007 keeps every exported name |
| `tests/test_verify_stamp_ships.py` `assert_stamped_gate` and `make_it_old` | counts `^verify:` (1) and `^verify-checks:(?!.*check-openapi)` (1); **rebuilds the pre-stamp Makefile by regex** `^VERIFY_STAMP := .*?^verify-checks: ([^\n]*)\n`, then asserts the word `verify-checks` is gone | hold: T004–T006 put nothing between `VERIFY_STAMP :=` and the `verify-checks:` rule but the `verify` rule and `VERIFY_GROUP`, and name `verify-checks` in no line outside that span (an `ifdef VERIFY_ORDER` block names `lint`, `typecheck`, `test`, never `verify-checks`) |
| `tests/test_verify_stamp_where.py` `assert_untouched` | stdout of `make verify` under a CI marker **equals** stdout of `make verify-checks` | hold: T002, T004, T005, T006 keep a passing run's output equal on the Python fixture |
| `tests/test_verify_stamp_scan.py`, `tests/test_verify_stamp_launches.py` | derive the gate's scripts and launched commands **from the generated Makefile by regex** (`RULE`, `LAUNCHED`, `gate_targets`) | hold: the new `sync` target, `$(eval …)` and `$(if …)` lines, the `ifdef` block and the file target must parse and every launched word (`npm`, `node`, `touch`) be on the project's tool list — run in each task's Verify |
| `tests/test_verify_stamp_inputs.py:208–214` | `npm --prefix scripts/event-model install` present, `… ci` absent | **T008** (R7) amends it |
| `tests/test_npm_install.py` (`plan(repo, "verify")`, an event-profile TypeScript project) | `make -n verify` holds exactly one `npm ci`; with the root marker present, none | **T008** (R7) amends it: the model tooling's `npm ci --prefix` is now a second, expected one |
| `tests/test_uv.py:94–98`, `tests/test_services.py:244–246`, `tests/test_running.py`, `tests/test_flag_gate.py:111`, `tests/test_host.py:98` | `uv sync --project "$app" --locked --quiet` and `run="uv run --project $app --no-sync"` in `scripts/verify`; `./scripts/verify-python --lint-only` (substring) and its `NotIn`; `dev:` inside its transport's region and the `uv run … runnable.main` line; the exact gate-prerequisite string; the tsx path | hold: **T002** keeps those script lines byte for byte and appends ` --synced` after the mode, **T003** leaves the `verify-checks:` line alone, **T008** keeps `TSX` |
| `tests/test_drawio_canvas.py`, `tests/test_event_model.py`, `tests/render_fixture.py` | run `make check-drawio` / `make model` through real npm in a generated project | watch, **T008**: they now install from the shipped lock; they need the registry as they did |
| `tests/test_layout.py:74–75,138–144`, `tests/test_monorepos.py:238–243`, `tests/test_toolkit.py` | the moved layout's `.gitignore`/workflow pointers; the event-model files an event project has and a standard one lacks; the toolkit fully routed | watch, **T008**: the lock is `profile-excluded` for `standard` by the existing `scripts/event-model/` rule, and nothing is added to these |
| `tests/test_verify_stamp_page.py` (two adopted holds) | an adopted page says nothing of a `stamp` and a moved layout's page equals the root page up to the stamp paragraph | **T009** (R8) amends it only if AC-S04-61's adopted clause is put on the adopted page |
| `tests/test_changelog.py` | the fragments' highest level against `VERSION` | hold: MINOR on `1.6.0.dev0` — T002 lands the fragment, run in T002's Verify |

**No hit:** no test pins the text of the adopted `GATE` other than `test_verify_stamp_pinned.py`; none pins `install`,
`migrate` or `dev` recipes of a Python project line for line (T001 pins their behaviour); no other helper rebuilds an
old Makefile by regex (`test_ci_fetch_migrate.made_before_the_slice` rebuilds a *workflow*, and is the precedent for
T009's old project).

**Helpers reused by name** (read before writing a new one): `tests/stamp_fixture.py` — `template()`, `git()`,
`write_stand_ins()`, `checks_started()`, `StampTestCase`, `CI_MARKERS`, `MAKE_STATE`, `GIT_STATE`, `BRANCH`; `tests/support.py`
— `FactoryTestCase.generate`, `commit_all`; `tests/test_add_service.py` — `add_service`; `tests/test_candidates.py` —
`adopted`, `slipwai`; `tests/test_migrate.py` — `migrate`; `tests/test_replay.py` — `newer_factory`, `git`;
`tests/test_check_python.py` — the `sitecustomize` stand-in for a `python3` that says 3.9.6 (the precedent for T003);
`tests/test_verify_stamp_pinned.py` — `gate_prerequisites`, `gate_rule`, `CLOSING`.

**Quick test and pre-commit.** The quick test of an increment is `make test TESTS="<modules>"`, the modules each task
names. Before each commit run `make lint typecheck check-structure` as well.

**Versioning, on every commit** (`AGENTS.md`): a commit that changes `src/slipwai/` or `assets/` says `Level MINOR;
VERSION already carries it (1.6.0.dev0); the fragment changelog.d/parallel-gate.md claims MINOR` and names the reason
(a new generated file, the model tooling's lockfile, D91); a commit that changes only `tests/` says it reaches no user.
**The fragment `changelog.d/parallel-gate.md` lands in T002**, the first commit that changes a user-visible tree, as a
first draft with first line `MINOR` (so `tests/test_changelog.py` holds in every commit after it); T009 completes it.
No other task touches it. The host commits T002 before any other task, whatever order delegates finish in.

**The Pin stage** (`/characterise`, plan *Pin*) is a host task, T001, before any implementation.

## Format: `[ID] [P?] [Story] Description` — each task is one increment, one commit

`[P]` marks a task whose files are disjoint from every sibling's it could run beside; see *Parallel opportunities*.

---

## Phase 1: Pin (host)

### T001 — Pin what each mode of the Python `scripts/verify` runs first, what `install`, `migrate` and `dev` do, and what the four model targets run (host task)

- [x] *(c225d78: five tests, green before any change, teeth seen on `python.py`, `backends.py` and `model_targets.py`; written by a `drive-implement` delegate from this task's wording, the ledger row by the host)* **Host task; no story.** The host runs `/characterise` before T002 and commits it alone. Named,
  **not re-pinned** (the 2026-10-04 rows from S03 hold them, and their suites are the ones AC-S04-63 amends): what a
  generated project's `make verify` runs, in order, with its closing line, and the adopted repository's `verify` rule byte
  for byte (`tests/test_verify_stamp_pinned.py`). **Pinned, new, each green before any change and written to survive the
  slice** (they assert behaviour the slice keeps, never a count it changes): (1) each mode of a Python project's
  `./scripts/verify` — `--install-only`, `--lint-only`, `--typecheck-only`, `--test-only`, `--migrate`,
  `--integration-only`, `--adversarial-only`, none — syncs every service before its first `uv run`, read from a stand-in
  `uv`'s log; (2) `make install`, `make migrate` (Postgres) and `make dev` (a transport) on a Python project each run a
  sync **before** the command they exist for — *a* sync, not *one* (T002 makes it one); (3) the four model targets
  (`model`, `model-drawio`, `check-drawio`, `model-drawio-test`) each run an npm install and then `node
  scripts/event-model/node_modules/tsx/dist/cli.mjs` with the script and arguments they run today — not `install` against
  `ci`, which T008 changes on purpose. Teeth by changing `makefile.py`, `backends.py` or `model_targets.py` and
  restoring. The commit says no user-visible tree changed, so the number is not raised.

**Files:** `delivery/survey/pinned.md` (the only file under `delivery/` this slice changes), `tests/test_gate_recipes_pinned.py`
(new, ≤ 350 lines; the host names a second file if it needs one).

---

## Phase 2: Implementation stage

Each task starts from the green committed suite at the commit that closes T001. **T002 first and alone** (it creates the
helper every other task imports and lands the fragment). Then two chains and two lone tasks may run together — chain A
(T003), chain B (T004 then T005), T007 and T008; T006 follows T003 and T005; T009 follows everything (*Parallel
opportunities*).

### T002 — [US1] One sync per `make` run, and a mode reached any other way syncs first (R1 · AC-S04-28 to -41, -44, -14)

- [x] *(55283e2: one `…: sync` line beside the `consumers` line rather than a word on each target line, `migrate` and `dev` on their own lines inside their regions; `openapi.py` and `native_commands.py` not edited; e5, e6, e9, e11, e12, e13 holds with teeth)* **Rule R1.** **The first commit that changes a user-visible tree, so the fragment lands in it** (first line
  `MINOR`, a first draft: the gate in parallel, one sync, the lockfile, the three catch-up cases in one stand-alone
  **Catch-up.** paragraph; T009 completes it against what landed). Builds `tests/parallel_gate.py` **only as far as R1
  needs it**.

**The helper** (new `tests/parallel_gate.py`, ≤ 350 lines; imports `CI_MARKERS`, `MAKE_STATE`, `GIT_STATE` from
`tests/stamp_fixture.py` and does not import a test module's test class): (a) a cached generator of the shapes below,
copied per test, the way `tests/test_verify_stamp_scan.py` caches `_projects` (the fixture's `template()` is one
service, no transport, no frontend — R1 needs a transport, Postgres and two services too); (b) `gate_environment(extra)`
— the stand-ins first on `PATH`, the three CI markers and `MAKE_STATE`/`GIT_STATE` removed unless the example sets one;
(c) `run_make(repo, env, *args)` with `timeout=180` and `text=True, capture_output=True`; (d) a stand-in writer for `uv`
that appends `start<TAB>args` and `end<TAB>args` to `$STANDIN_LOG`, makes `<project>/.venv/pyvenv.cfg` on `sync`
(as `stamp_fixture._UV` does), exits non-zero on `sync` when told to, and — for `sync` only — can hold, bounded, until
another `uv` call has started and log `met`/`alone` (so a second concurrent sync is *seen*); (e) readers over the log:
`sync_lines(log)` (first argument `sync`, with its `--project`), `run_lines(log)` (first argument `run`), and "every
sync line precedes the first run line". **A later task extends this file only if its manifest names it** (T004, T005,
T006 do; T007, T008, T009 import it unedited).

**RED** (new `tests/test_parallel_gate_sync.py`, `tests/test_parallel_gate_sync_ways.py`,
`tests/test_parallel_gate_sync_edges.py` — split in advance by example so each stays under 350 lines; the plan named two,
the third is the split of e11, e14, e15). *The Python project* is a generated project with one Python service, the event
profile, FastAPI and Postgres unless the example says otherwise; the standard profile with `--http none` is the fixture's
and is enough where the example needs no transport. Each fails today for the reason given, **or is a hold, written as
one and seen to have teeth**:
- `test_parallel_gate_sync.py` — e1 `make verify` on one service → exactly one sync line for that `--project` *(fails
  today: `lint`, `typecheck` and `test` each call the script, which syncs each time → three)* · e2 `make -j verify` →
  one per service, **and every sync line precedes the first run line** *(fails today: three, racing)* · e3 two services
  (`add_service`) → exactly two, one per `--project` *(fails today: six)* · e4 `make lint test` as one command → one
  *(fails today: two)* · e5 `make lint`, `make typecheck`, `make test` alone → one sync, before the first run line
  *(**hold**: today each is one script call; teeth by deleting `sync` from that target's prerequisites in the generated
  Makefile in the working tree of the generator and seeing the sync line go missing)* · e6 `./scripts/verify`
  typed directly with `--lint-only`, `--typecheck-only`, `--test-only` and with no argument → one sync, first *(**hold**
  today; teeth: make the script skip the sync whatever its arguments)*.
- `test_parallel_gate_sync_ways.py` — e7 `make ci` with its database targets → one *(fails today: the gate's three plus
  `test-integration` and `migrate`)* · e8 `make migrate` → one, before the migration's run line *(fails today: the recipe's
  `--install-only` line and the script's own sync make two)* · e9 `make dev` against the stand-in → one, before the
  service's run line *(**hold** today — the recipe's own `--install-only` line is the one sync; teeth by dropping the
  prerequisite)* · e10 `make install test` → one *(fails today: two)* · e12 the generated CI workflow, `service_commands()`
  (`native_commands.py`) and every page `project_files()` produces **never say `--synced`** — a sweep over every backend
  the catalog offers, with a transport and without, with a browser app, and with several services; `Makefile` and
  `scripts/verify*` are the only files that may carry it *(**hold** today; teeth by applying the rewrite to
  `service_commands()` and seeing the failure)* · e13 with `--synced` absent and **any** environment variable set to any
  value (a list of the plausible names — `CI`, `UV_*`, `VERIFY_*`, `SYNCED`, `SKIP_SYNC`, `NO_SYNC` — and a few random
  ones), `./scripts/verify --test-only` still syncs first *(**hold**; teeth as e6)* · e16 no `.venv`,
  `make -j check-openapi lint` → both pass, and the sync **ended** before either started (the barrier on `sync`: a second
  concurrent sync would log `met`) *(fails today: two syncs overlap)*.
- `test_parallel_gate_sync_edges.py` — e11 a stand-in `uv` whose `sync` exits non-zero, `make verify` and `make -j
  verify` → make exits non-zero and the log holds **no run line** *(**hold** today; teeth by making the `sync` recipe
  ignore its failure with a leading `-`)* · e14 `make verify` prints nothing new but make's echo of the sync recipe,
  once: the script's own `--install-only` run prints nothing, and `make verify`'s output holds exactly one line carrying
  `scripts/verify --install-only` *(fails today: no sync target, so no such line)* · e15 `make verify lint` → at most two
  sync lines per service, more than zero *(fails today: four)*.

**GREEN** — a new `src/slipwai/project/parallel_gate.py`, and in it: the target in plan.md *Design* R1, `sync: check-python`
with the family's own script (`verify_path()` where there are several), emitted only where the project has a Python
service; the rewrite function that appends ` --synced` after the mode of every call of that script in the recipes
`makefile()` merged — **both spellings of an integration command**: the `INTEGRATION_TEST … ?=` default **and** the
`INTEGRATION_TEST … :=` the store's marked region sets (`integration.py`; the plan names "the default" only, the tree has
two) — and `service_commands()` stays the syncing spelling (AC-S04-39). Every target whose recipe runs a mode of the
script or `uv run --no-sync` takes `sync` as a prerequisite: `lint`, `typecheck`, `test`, `format`, `adversarial`,
`install`, `test-integration` and its per-service targets, `openapi` and `check-openapi` (where a Python service
exports — their target lines are unmarked and stay defined after a prune, `openapi.py`'s docstring says why) — and
`migrate`, `migrate-<service>`, `dev` and `dev-<service>`, **on the target line inside their marked region**
(`install_step()` does it for npm; a prerequisite line left outside would define a pruned target with no recipe).
Their recipes lose the written-out `--install-only` line (`install_step()`'s second element, `backends.dev_command()`'s
Python line), and `install`'s recipe loses its Python line. `verify_script()` (`languages/python.py`) skips the loop
only when `"${2:-}" = --synced`, reading no variable; the sync line of the loop stays byte for byte
(`tests/test_uv.py`). `native_commands.py` is edited **only** if the rewrite cannot be applied from `makefile.py`.
`changelog.d/parallel-gate.md` first draft, as above.

**REFACTOR:** if `makefile.py` or `backends.py` would pass 350, the new code lives in `parallel_gate.py`; the rewrite and
the per-target prerequisite are one function each, not a string replace in six places.

**Verify:** `make test TESTS="test_parallel_gate_sync test_parallel_gate_sync_ways test_parallel_gate_sync_edges
test_uv test_services test_running test_flag_gate test_changelog test_verify_stamp_pinned test_verify_stamp_recipe
test_verify_stamp_ships test_verify_stamp_where test_verify_stamp_scan test_verify_stamp_launches test_verify_stamp_runs
test_backing_services test_axes"` green, then `make lint typecheck check-structure`. `git diff` shows
`assets/toolkit/scripts/verify-stamp.py` untouched. Commit by path; level line as above.

**Files:** `tests/parallel_gate.py` (new), `tests/test_parallel_gate_sync.py` (new), `tests/test_parallel_gate_sync_ways.py`
(new), `tests/test_parallel_gate_sync_edges.py` (new), `src/slipwai/project/parallel_gate.py` (new),
`src/slipwai/project/makefile.py`, `src/slipwai/project/languages/python.py`, `src/slipwai/backends.py`,
`src/slipwai/project/integration.py`, `src/slipwai/project/openapi.py`, `src/slipwai/project/native_commands.py` (only if
the rewrite cannot be applied from `makefile.py`), `changelog.d/parallel-gate.md` (new).

### T003 — [P] [US1] `check-python` is first, serial and parallel (R2 · AC-S04-13, -1, -18)

- [x] *(b5429f5: the line follows the gate's rule and is emitted only where the gate is the stamped one; `check-openapi: check-python` in `openapi.py`; e2 and the sweep red first, e1, e3, e4 holds with teeth)* **Rule R2.** Needs T002 (its helper, and the `sync` target that already names `check-python`). Disjoint from
  T004, T005, T007 and T008 by manifest.

**RED** (new `tests/test_parallel_gate_first.py`; the old `python3` is **the `sitecustomize` stand-in of
`tests/test_check_python.py`**, a directory on `PYTHONPATH` that sets `sys.version_info` to 3.9.6 — no new mechanism; the
gate-run examples use the standard profile and the fixture shape so the event profile's model targets (T008's) are not in
the way, except e4 which uses a generated event-profile project only to show nothing under `.specify/` moves):
- e1 an older `python3`, `make verify` → `check-python`'s line, **no sync line**, no other check started, non-zero
  *(the serial half is a **hold**: `check-python` is first in the list today and make stops; teeth by moving it last in
  `verify_dependencies`)*.
- e2 the same under `make -j verify` → the same *(fails today: every other check starts at once, and so do three syncs)*.
- e3 a serial full run starts the checks in the order they had, no two at once *(**hold**; teeth by reordering the
  dependencies in the working tree)*.
- e4 `make -j verify` leaves every byte under `.specify/` as it was *(**hold**: no gate target was found writing there;
  teeth by adding a write to a stand-in's `uv run` under `.specify/` and seeing it fail)*.
- **The sweep that closes the class:** a Makefile-derived assertion — every target that is a prerequisite of
  `verify-checks` (derived with `tests/test_verify_stamp_scan.makefile_rules`'s method, not a list) other than
  `check-python` names `check-python` as a prerequisite, directly or through `sync`, for every backend the catalog
  offers, with a transport and without (`./init --http none` leaves no `check-openapi` and no target with a prerequisite
  line and no recipe), with a browser app, with the event profile, and with a deploy target (`check-flags`, the role gate).

**GREEN** — in `parallel_gate.py`: one line after the gate's rule, built from the same `verify_dependencies` string
`makefile()` already holds, `<every prerequisite but check-python>: check-python` — **and `check-openapi`**, which is not in
that string (it hangs on `verify-checks` inside its transport's markers): its own target line in `openapi.py`
(unmarked, always defined where it exists) names `check-python`, beside `sync` where a Python service exports. No line
beginning `verify-checks:` is added or edited, and the `verify-checks:` line's text is byte for byte what it is
(`tests/test_flag_gate.py:111`, `tests/test_check_python.py`). The root's `npm ci` file target and the model tooling's do
not name `check-python` (a file target depending on a phony one would reinstall on every run; plan *Design* R2).

**REFACTOR:** none expected.

**Verify:** `make test TESTS="test_parallel_gate_first test_parallel_gate_sync test_check_python test_flag_gate
test_verify_stamp_pinned test_verify_stamp_ships test_verify_stamp_scan test_verify_stamp_launches test_verify_stamp_where"`
green, then `make lint typecheck check-structure`. Commit by path; level line (MINOR, `VERSION` not raised, fragment
T002's).

**Files:** `src/slipwai/project/parallel_gate.py`, `src/slipwai/project/makefile.py`, `src/slipwai/project/openapi.py`,
`tests/test_parallel_gate_first.py` (new).

### T004 — [P] [US1] A parallel run is the serial run's verdict, and a failed one ends on the gate's own line (R3 · AC-S04-2 to -9, -19, -20)

- [x] *(bfe8c2a: the failed run ends on `verify: the gate did not pass; each failed check is named above on a line carrying ***`; the last group passes the sub-make's status through and is silent on 1, so `make -q verify` says nothing; e6 red first, the rest holds with teeth)* **Rule R3.** Needs T002 (the helper). **Mostly holds**: the plan's map lists e1, e2, e7 and e8 as holding today;
  research R-2 and R-6 show e3, e4 and e5 hold as well (the checks already run together by luck, make prints a `***` line per
  failed target, a failed gate exits non-zero) — each is **observed first**, written as a hold if it passes, and a
  RED with its own GREEN named in the report if it does not. **The one rule-changing example is e6**, so the GREEN is not
  empty. Extends `tests/parallel_gate.py` (its manifest names it): the barrier stand-in and the readers of `***` lines
  and of the last line.

**RED** (new `tests/test_parallel_gate_run.py`; the Python fixture shape with stand-in `uv`; a project where one check
fails is made by the stand-in's `uv run` failing for one tool, as `STANDIN_UV_FAIL` does in `stamp_fixture`, or by a
`python3 scripts/check-….py` replaced in the copy with one that exits 1):
- e1 the set of commands started under `-j` equals serial's *(**hold**; teeth by dropping a prerequisite from the
  parallel path)* · e2 exit 0 and last line `verify: all gates passed` *(**hold**; teeth by changing the closing line)*.
- e3 two checks running at the same moment — a barrier between two stand-ins (`lint`'s and `typecheck`'s `uv run`), `met`
  in the log, no clock *(**hold**; teeth by adding `.NOTPARALLEL:` to the project's Makefile and seeing `alone`)*.
- e4 one check fails under `-j` → non-zero, no closing line, **no stamp** *(**hold**; teeth by recording on failure)* ·
  e5 two fail → each on a `***` line carrying its target's name, as the running make prints it (D92) *(**hold**; teeth by
  making one stand-in not fail)*.
- e6 a failed run, **serial and `-j`** → the gate's last line begins `verify:`, says the gate did not pass, and says the
  failed checks are named above on the lines carrying `***` — and make's own last line for the gate's target follows it
  or precedes it as run showed (R-2: the line the recipe echoes after the sub-make is printed before make's last
  line) *(**fails today**: the last line is make's `Error 2`)*; with a passing run **not** printing it.
- e7 a pass under `-j` is reused by `make verify` on a branch other than the trunk, no CI marker *(**hold**; teeth by
  skipping `record` under `-j`)* · e8 a pass under `make verify` is reused by `make -j verify` *(**hold**; same teeth)*.
- **The sweep that closes the class:** e6 over every state that makes the gate fail (one check, two checks, the stand-in's
  `uv` failing, a `python3` check failing) × serial and `-j`; and e2/e6 over the event profile (the closing line is last
  on a pass, and absent on a fail) — the two shapes that differ in their prerequisites.

**GREEN** — in `gate.py`: `STAMPED`'s `verify` recipe gains the third group of plan *Design* R3, `… || { echo '<the
sentence>'; exit 1; }`, so `reuse`'s exit 0 still ends the recipe at once and `record` (always 0) means the last group
runs only when the checks failed. **The exact sentence is this task's to settle against AC-S04-9** (it begins `verify:`,
says the gate did not pass, says each failed check is named above on a line carrying `***`) **and it is the sentence
T009's page quotes**. The stamp's script, the sub-make's quoting and `--no-print-directory -f "$(firstword
$(MAKEFILE_LIST))"` are not touched (`tests/test_verify_stamp_recipe.py` still passes unedited here). `ci` still hangs on
`verify-checks` and gets neither the line nor the order variable (D88: `make -j ci` is not promised).

**REFACTOR:** none expected.

**Verify:** `make test TESTS="test_parallel_gate_run test_parallel_gate_sync test_verify_stamp_recipe
test_verify_stamp_cannot test_verify_stamp_where test_verify_stamp_runs test_verify_stamp_two_runs
test_verify_stamp_ships"` green (make exits 2 for a failed gate whatever the recipe's `exit` says, so
`test_verify_stamp_cannot`'s exit-code comparison stands), then `make lint typecheck check-structure`. Commit by path;
level line (MINOR, fragment T002's).

**Files:** `src/slipwai/project/gate.py`, `tests/parallel_gate.py`, `tests/test_parallel_gate_run.py` (new).

### T005 — [P] [US1] Each check's output stays together where the make can (R4 · AC-S04-10 to -12, -16)

- [x] *(c1a67ab: `VERIFY_GROUP` behind the feature test; e1, e2 red first; e3's teeth are a `MAKEFLAGS` line, the option alone does not hold a serial sub-make's output on 4.4.1; e4 over 40 starters)* **Rule R4.** Follows T004 (same `gate.py`, same helper). Disjoint from T003, T007, T008 by manifest.

**RED** (new `tests/test_parallel_gate_output.py`; GNU Make 4.4.1 on this machine lists `output-sync`, so the examples
that need the feature skip, saying so, on a make that does not):
- e1 `make -j verify`, two checks each printing three lines **with a barrier between the lines** (stand-ins for `lint`'s
  and `typecheck`'s `uv run`, using the helper's barrier; no `sleep` as proof) → each check's three lines are
  contiguous in the output *(fails today: they interleave)*.
- e2 the Makefile names the option only inside `$(if $(filter output-sync,$(.FEATURES)),--output-sync=target)` — read from
  the generated text, the AC-S04-11 stand-in for 3.81, which is not run here *(fails today: no `VERIFY_GROUP`)*.
- e3 a serial run on a make that lists the feature: a check's first line is **seen before its last is written** (a
  stand-in that prints line one, then waits, bounded, for the test to see line one on the pipe — read incrementally from a
  `Popen`, under a timeout) *(**hold** today; teeth: GNU Make 4.4.1 may ignore `--output-sync` at one job, in which case
  the assertion cannot be falsified by the option and **the report says so**, claiming the claim is held by reading e2 and
  by AC-S04-12's run, not by teeth it does not have)*.
- e4 every starter's Makefile — the catalog's backends × `http` with and without × frontend `none`/`react-vite` × the two
  profiles, as `tests/test_monorepos.py` and `test_verify_stamp_recipe.py` loop them — has no `.WAIT`, no `.NOTPARALLEL`
  with a prerequisite, and contains no `output-sync`/`-O` outside the one guarded expression *(**hold**; teeth by adding
  `.WAIT` to the generated text)*. Adopted repositories' Makefiles are R6's, not this sweep's.

**GREEN** — in `gate.py`: `VERIFY_GROUP := $(if $(filter output-sync,$(.FEATURES)),--output-sync=target)` beside
`VERIFY_STAMP`, and `"$(MAKE)" $(VERIFY_GROUP) --no-print-directory -f "$(firstword $(MAKEFILE_LIST))" verify-checks`.
Nothing else newer than 3.81.

**Amend, in this task** (AC-S04-63; the change breaks it): `tests/test_verify_stamp_recipe.py` `assert_recipe` — the
recipe's substring becomes `"$(MAKE)" $(VERIFY_GROUP) --no-print-directory -f "$(firstword $(MAKEFILE_LIST))" verify-checks`;
every other assertion in that file is untouched, and the amendment is the one line.

**REFACTOR:** none expected.

**Verify:** `make test TESTS="test_parallel_gate_output test_parallel_gate_run test_verify_stamp_recipe
test_verify_stamp_ships test_verify_stamp_where test_verify_stamp_runs test_verify_stamp_scan"` green, then
`make lint typecheck check-structure`. Commit by path; level line (MINOR, fragment T002's).

**Files:** `src/slipwai/project/gate.py`, `tests/parallel_gate.py` (printing-with-barrier option),
`tests/test_parallel_gate_output.py` (new), `tests/test_verify_stamp_recipe.py`.

### T006 — [US1] Every backend family holds the rule: Java's three Maven checks and Go's first `go` command are ordered (R5 · AC-S04-15, -17, -42, -43, -5)

- [x] *(33a4757: `VERIFY_ORDER=1` on the gate's sub-make and an `ifdef VERIFY_ORDER` block — Java: `typecheck: lint`, `test: typecheck`; Go alone: `lint test: typecheck`; e1, e2 red first, e3–e5 holds with teeth; real toolchain run by hand for Go, TypeScript and Java (Quarkus), each exit 0 serial and `-j` with the same checks — Java's `-j` run was not faster there, and a fresh-clone run is the demo's)* **Rule R5.** Needs T003 and T005 (same `makefile.py` and `parallel_gate.py` as T002/T003, same `gate.py` and helper as
  T004/T005, so it follows both chains). **`VERIFY_ORDER=1` is added here, not in R3/R4 as the plan's structure lists
  it**: before this rule nothing reads it, and a variable no test can fail on is dead code.

**RED** (new `tests/test_parallel_gate_families.py`; a Java project's `apps/service/mvnw` is **replaced in the test's copy**
by a stand-in that logs `start`/`end` and a `met`/`alone` barrier — the recipes `cd` into the service and run `./mvnw`, which
a `PATH` stand-in cannot reach; a Go project gets `go`, `gofmt` and whatever `GO_STATICCHECK`/`GO_COVDATA_READY` launch
as stand-ins on `PATH`, read from `native_commands.py` and `tests/test_verify_stamp_launches.launched()`; all with the
helper's writer, which this task extends):
- e1 a Java project (Quarkus; and Spring, the same tree shape) under `-j`, a stand-in `./mvnw` → no two overlap (every
  `end` precedes the next `start`; the barrier reads `alone`) and the verdict equals the serial run's *(fails today: all
  three start at once)*.
- e2 a Go project under `-j`, a stand-in `go` → `typecheck`'s commands end before `lint`'s or `test`'s start *(fails
  today)*; the project with both a Java and a Go service takes the Java chain, which covers Go.
- e3 `make test` alone on a Java project starts **no** `lint` command; `make lint` alone starts no `typecheck` *(**hold**
  today; teeth by removing the `ifdef VERIFY_ORDER` guard so the chain applies standalone)*.
- e4 a TypeScript Makefile: every gate target reaches `npm ci` only through the file target `node_modules/.package-lock.json`
  *(**hold**, AC-S04-42, pinned not changed; teeth by adding an `npm ci` to a recipe)* · e5 Go's and Java's `lint`,
  `typecheck`, `test` recipes carry no install step — no `go mod download`, no `mvnw` download, no `npm ci` (AC-S04-43,
  **hold**; teeth by adding `go mod download` to a recipe).
- **The sweep that closes the class:** e1–e3 over both Java backends and Go, with and without a TypeScript browser app and
  with a Python service beside (so the Python `sync` does not break the chain); a run where the gate's *standalone* targets
  (`make lint`, `make test`, `make typecheck`) are read from `make -n`, never run, for every family.
- **Not a test:** R5e6 and AC-S04-5/-17 — a fresh starter of each family with its real toolchain, `make install && make -j
  verify` passes with its serial run's checks. The delegate runs it **once by hand** for Go, TypeScript and Java (Quarkus) on
  this machine (research R-6 ran them) and reports the exit codes and the closing lines; the demo runs it again (quickstart §5).

**GREEN** — in `parallel_gate.py`, `makefile.py` and `gate.py`: inside `ifdef VERIFY_ORDER` … `endif` (3.80/3.81), so only
the gate's own sub-make sees it — with a Java service `typecheck: lint` and `test: typecheck`; otherwise, with a Go
service, `lint test: typecheck`; both families → the Java chain; Python and TypeScript need neither (plan *Design* R5).
The gate's recipe passes `VERIFY_ORDER=1` to its sub-make. A line inside the block names no `verify-checks`
(`make_it_old` in `tests/test_verify_stamp_ships.py` asserts that word gone). The cost is named for the fragment: under `-j`
a Java gate's three native checks still run one after another, beside the gate's other checks.

**REFACTOR:** if `gate.py`, `makefile.py` or `parallel_gate.py` have grown a second place that spells the chain, one
function; `tests/parallel_gate.py` keeps each stand-in writer to one function.

**Verify:** `make test TESTS="test_parallel_gate_families test_parallel_gate_run test_parallel_gate_output
test_parallel_gate_sync test_parallel_gate_first test_verify_stamp_ships test_verify_stamp_scan test_verify_stamp_launches
test_verify_stamp_recipe test_verify_stamp_where test_npm_install test_shared_packages"` green, then `make lint typecheck
check-structure`. Commit by path; level line (MINOR, fragment T002's).

**Files:** `src/slipwai/project/parallel_gate.py`, `src/slipwai/project/makefile.py`, `src/slipwai/project/gate.py`,
`tests/parallel_gate.py`, `tests/test_parallel_gate_families.py` (new).

### T007 — [P] [US1] An adopted repository's gate is serial (R6 · AC-S04-24 to -27)

- [x] *(b0edd4a: the directive follows the `verify` rule, the refusal and the moved layout included; e1, e3 and the `ratchet-tighten` sweep red first; e2, e4 holds)* **Rule R6.** Needs T002 (the helper, unedited here). Disjoint from every other task's manifest — it is the plan's
  second group, and it shares no file with the first.

**RED** (new `tests/test_parallel_gate_adopted.py`; an adopted repository is made through the CLI with `adopted()` and
`slipwai(repo, "adopt", "--confirm", …)` from `tests/test_candidates.py`; the recorded `lint`, `typecheck` and `test` come
from the survey of the fixture's own build files, so the test writes their `scripts` to call **stand-ins** that log
`start`/`end` and use the helper's barrier — the delegate reads how `tests/test_adopt.py:166–190` and
`tests/test_adopt_facts.py:141` get commands recorded):
- e1 an adopted repository's Makefile carries a bare `.NOTPARALLEL:` — no prerequisite, one comment above it *(fails
  today)* — **and** the one where nothing is confirmed (the refusal) does too: the rule is *not stamped, so serial*.
- e2 a generated project's Makefile carries no `.NOTPARALLEL`, whatever its backends, with and without a transport and a
  browser app *(**hold** today; teeth by emitting it unconditionally)*.
- e3 recorded `lint`, `typecheck`, `test` as stand-ins, `make -f delivery/Makefile -j verify` → none overlap, serial order
  (the barrier reads `alone` for each) *(fails today: the three start together)*.
- e4 no baseline yet, `make -j verify` → `baseline.json` equals the one a serial first run records. The three ratchet runs
  are made to **overlap without the line** by the barrier, so this is red today for a reason, not by luck; if it
  nonetheless passes today the report says so and the example stands as a hold whose teeth are e3's.
- **The sweep that closes the class:** e1/e2 over a wrapped application, a moved layout with a generated service beside it
  (`Layout("delivery")`), and the refusal; and `ratchet-tighten`'s sub-make reads the same Makefile, so its three targets
  run serially with it.

**GREEN** — in `adopted_targets.py`: `gate_target()` returns its text with one comment and a line `.NOTPARALLEL:` wherever it
does not return the stamped gate, the refusal included; no prerequisite. **The placement is this task's to settle**, with
the constraint that the `verify` rule's own bytes do not change (`tests/test_verify_stamp_pinned.py` holds them) and that
the directive is not inside `adoption_targets()` (an adopted repository with nothing confirmed has no wrapped
application, so that function returns nothing).

**Amend, in this task** (AC-S04-63): `tests/test_verify_stamp_pinned.py` `WrappedGatePinnedTest` — the two tests keep the
rule held **byte for byte** and now also hold the directive and its position; every exported name other tests import
(`gate_prerequisites`, `gate_rule`, `gate_target_name`, `CLOSING`, `GENERATED`, `STANDARD`, `WRAPPED`) stays, and
`GeneratedGatePinnedTest` is untouched.

**REFACTOR:** none expected.

**Verify:** `make test TESTS="test_parallel_gate_adopted test_verify_stamp_pinned test_verify_stamp_where test_candidates
test_adopt test_adopt_facts test_adopted_manifest test_layout test_check_python"` green, then `make lint typecheck
check-structure`. Commit by path; level line (MINOR; the adopted line is under the experimental label — the fragment, T009,
says so).

**Files:** `src/slipwai/project/adopted_targets.py`, `tests/test_parallel_gate_adopted.py` (new),
`tests/test_verify_stamp_pinned.py`.

### T008 — [P] [US1] The model tooling installs from a committed lock, once, and says when it did not (R7 · AC-S04-45 to -55)

- [x] *(42aaac6, e7dab3f, a7ce7b0: the lock made by npm 9.2.0 against the registry (version 3, 31 packages and the root, 26 esbuild platforms); the install is spelled `npm --prefix scripts/event-model ci`; `@touch` after it; `install` names the marker (D93); a `NOT_SCANNED` entry in `tests/test_verify_stamp_scan.py` for the lock the skip line names; `tests/test_npm_install.py` not amended; the pin test's stand-in npm writes the marker and each model target starts uninstalled; AC-S04-54 as re-worded and AC-S04-64, -65 held with the real npm)* **Rule R7.** Needs T002 (the helper, unedited here). Disjoint from every other task's manifest — the plan's third
  group; it shares no file with the first two. **The only task that changes `assets/toolkit/`.**

**The lock** is made by npm against the registry, never by hand (AC-S04-46): in an empty scratch directory holding only
`assets/toolkit/scripts/event-model/package.json`, `npm install --package-lock-only --no-audit --no-fund`; the result is
copied to `assets/toolkit/scripts/event-model/package-lock.json`. Research R-4 got `lockfileVersion` 3, 32 packages, 26
`@esbuild/*` platforms, every `resolved` from `registry.npmjs.org`. **If the registry cannot be reached, the task stops and
reports: the slice parks on it (D91).**

**RED** (new `tests/test_model_lock.py` — e1, e2 — and `tests/test_model_install.py` and `tests/test_model_install_skip.py`
— e3 to e10, split in advance by example; `tests/parallel_gate.py` imported, unedited; `npm` and `node` are stand-ins that
log and make the marker `scripts/event-model/node_modules/.package-lock.json`, except where the example needs npm's own
refusal or the real check):
- e1 a new event-profile project tracks `scripts/event-model/package-lock.json`, and its root entry names exactly the
  `dependencies` and `devDependencies` of `scripts/event-model/package.json` *(fails today: no such file; no network)*.
- e2 the shipped lock: `lockfileVersion` 3, every `resolved` begins `https://registry.npmjs.org/`, a package for every
  platform esbuild publishes one for — read from the lock's own `esbuild` entry's `optionalDependencies` *(fails today)*.
- e3 fresh clone, `make check-drawio` → `npm ci --prefix scripts/event-model …` runs and `git status --porcelain` is empty
  afterwards *(fails today: `npm … install`)*.
- e4 installed, marker newer than both manifests → no npm command, and the line `check-drawio: the model tooling matches
  scripts/event-model/package-lock.json; not reinstalled` *(fails today)*. e5 either manifest touched → `npm ci` again and
  **no** skip line *(fails today)*.
- e6 `package.json` disagrees with the lock → `make check-drawio` exits non-zero with npm's own refusal, no tracked file
  changed. **Real `npm ci`** (it refuses before it fetches, so no registry is needed — the delegate confirms, and skips with
  its reason where `npm` is absent) *(fails today: `npm install` rewrites the lock)*.
- e7 `make model-drawio-test`, `make model`, `make model-drawio` on a matching tree → no install, **no** skip line *(fails
  today: each installs)*. e8 `make -j check-drawio model-drawio-test`, fresh → one `npm ci`, ended **before** either starts
  (the stand-in `npm` holds, bounded, for a second call: `met` would show two) *(fails today: two installs)*.
- e9 the generated Makefile spells `npm` for `scripts/event-model` in exactly one recipe, and it is `npm ci` *(fails today)*;
  swept over a project with a moved layout (`Layout("delivery")`), where the file target, its two prerequisites and the
  `--prefix` each spell `delivery/scripts/event-model/…` — the delegate **reads `layout.POINTER` and `repoint()` first**
  and holds the three spellings together *(fails or holds as the read shows)*.
- e10 a fresh clone on a branch other than the trunk, **real `npm` and `node`**, first `make verify` passes → the pass is
  recorded and the next `make verify` prints the reuse line *(fails today: the first gate writes an untracked lock that moves
  the key, D91)*; skipped, with its reason, where `npm`, `node` or the registry is absent.
- **The sweep that closes the class:** e3–e5 and e7 over all four targets and over the Python, Go and TypeScript starters
  with the event profile; and e1 over a standard-profile project, which gets **no** lock (the `scripts/event-model/` rule
  excludes it).

**GREEN** — `model_targets.py`: `MODEL_TARGETS` becomes the file target of plan *Design* R7 in the root's pattern (its
recipe `npm ci --prefix scripts/event-model --no-audit --no-fund --loglevel=error`, then `@touch` the marker, then
`$(eval MODEL_INSTALLED := yes)`), `check-drawio` with the skip line said only where `$(MODEL_INSTALLED)` is empty, and
`model`, `model-drawio`, `model-drawio-test` taking the file target and losing their install line. `TSX` and the
Windows-shim comment stay. The module's comment that the install is *repeated per recipe rather than shared through a
prerequisite* is rewritten. The lock file as above. If a manifest or a test lists the toolkit's files (the pruner, a
count), the delegate finds it by running the suite after adding the lock, and names it in the report.

**Amend, in this task** (the change breaks them): `tests/test_verify_stamp_inputs.py` e8 test — the model tooling's install
is `npm ci --prefix scripts/event-model`, the manifest still in the key (`exempt("…/.package-lock.json")` is still `None`);
and `tests/test_npm_install.py` — the model tooling's `npm ci --prefix` is a **second, expected** `npm ci` in `make -n verify`
of an event-profile TypeScript project, so the assertions count the root's (`npm ci` with no `--prefix`), and the
already-installed case checks the root's is absent. Neither amendment weakens what the test holds.

**REFACTOR:** none expected.

**Verify:** `make test TESTS="test_model_lock test_model_install test_model_install_skip test_verify_stamp_inputs
test_npm_install test_verify_stamp_scan test_verify_stamp_launches test_drawio_canvas test_toolkit test_layout
test_monorepos test_host test_utf8_io test_changelog"` green, then `make lint typecheck check-structure`, then
`git status --short assets/toolkit` shows only the lock. The real `npm ci` of the shipped lock on a fresh clone is run once
by hand and reported (AC-S04-47; the demo, quickstart §3, runs it again). Commit by path; level line (MINOR: one new
generated file, D91).

**Files:** `src/slipwai/project/model_targets.py`, `assets/toolkit/scripts/event-model/package-lock.json` (new, made by
npm), `tests/test_model_lock.py` (new), `tests/test_model_install.py` (new), `tests/test_model_install_skip.py` (new),
`tests/test_verify_stamp_inputs.py`, `tests/test_npm_install.py`.

### T009 — [US1] It reaches a project that exists, and the words are true (R8 · AC-S04-56 to -63, -21)

- [x] *(5e16e66: the page's paragraph is `PAGE` in `parallel_gate.py`, on the stamped project's page only — an adopted or moved-layout page says nothing of `-j`, and its maintainer is told in the fragment's catch-up; the fragment opens `MINOR`, its catch-up one paragraph standing alone, followed by hand against a factory archived at 3f44288 for the three lock cases; e4, e5 red first, e1–e3, e6 holds with teeth; `migrate`'s refusal does not name the untracked file, as AC-S04-57 does not ask)* **Rule R8. Last** — needs T002 to T008: the page and the fragment say what they landed, and `migrate` carries all of
  it. Completes the fragment T002 began.

**RED** (new `tests/test_parallel_gate_carry.py`; a project "made at the commit before this slice" is **this checkout's
project with the lock removed and the root commit amended**, as `tests/test_ci_fetch_migrate.made_before_the_slice` and
`test_verify_stamp_ships.make_it_old` do — `newer_factory()` and `migrate()` from `tests/test_replay.py` and
`tests/test_migrate.py`):
- e1 a project made before the slice, clean → `slipwai migrate` adds `scripts/event-model/package-lock.json` and the new
  Makefile and `scripts/verify`, and asks nothing else (AC-S04-59), and its `make check-drawio` passes *(real `npm`, as
  `tests/test_drawio_canvas.py` runs it; skipped with its reason where `npm` is absent)* *(fails today: the shipped tree has
  the lock, so the removed lock comes back — this is a **hold** if it passes before the page and fragment are written, with
  teeth by deleting the lock from the toolkit in the factory copy `newer_factory` makes)*.
- e2 the same with an **untracked** `scripts/event-model/package-lock.json` → `migrate` refuses as it does for any
  uncommitted change, naming it, and the file is as it was *(**hold**: `migrate.py` refuses on any uncommitted change;
  teeth by committing it and seeing the refusal go)*.
- e3 the same with the project's **own committed** lock that differs → the merge stops and names
  `scripts/event-model/package-lock.json` as the conflicting file, `.git/MERGE_HEAD` present, `git merge --abort` restores
  the project's own *(**hold**; teeth by making the two locks equal and seeing no conflict)*.
- e4 **the fragment** `changelog.d/parallel-gate.md` — first line `MINOR`; its **Catch-up.** paragraph, **stand-alone** (read
  on its own, the way the note `migrate` writes carries it — iteration 12's lesson), says what to do in each of the three
  cases (no lock: `migrate` adds it; an untracked lock: delete it, then `migrate`; a committed lock of the project's own:
  resolve the conflict, taking theirs or `npm install --package-lock-only` in `scripts/event-model`), that an edited tooling
  manifest now needs a lock that agrees with it, and — under the experimental label — that an adopted repository's gate now
  runs serially whatever `-j` says; it carries the measured numbers **only after the demo wrote them back** (a host edit,
  T010), so this task checks the paragraphs, not the figures. **The catch-up is followed as written**: each case is run on
  the old project above and does what the sentence says.
- e5 the page (`docs/gates.md` of a generated project) says the six things of AC-S04-61: `make -j verify` runs the checks at
  once, from GNU Make 3.81, and when to use it (when you wait on the gate locally); each check's output appears when that
  check finishes; on a make older than 4.0 lines may interleave; the order of lines is not promised; the claim is for
  `verify` as the only goal, `make -j ci` is not promised; and an adopted repository's gate runs serially whatever `-j`
  says, a recorded command that itself calls `make` being the one thing a bare `.NOTPARALLEL:` cannot hold. The sentence a
  failed run ends on (T004's) is quoted from the code, not retyped. **Where the adopted clause goes is this task's to
  settle against AC-S04-61:** in the paragraph a stamped project gets, which an adopted repository's page does not carry,
  `tests/test_verify_stamp_page.py`'s two adopted holds stand unedited; if it is also put on the adopted page, those two
  holds are amended in this task, named in the report, and nothing about a stamp enters that page.
- e6 the generated CI workflow and the ladder's commands (every generated workflow, and the `commands/` the toolkit ships)
  still type `make verify` and none types `-j` *(**hold**, AC-S04-21; teeth by adding `-j` to the workflow step in the
  working tree of the generator)*.
- **The sweep that closes the class:** e1–e3 over a TypeScript, a Python and a Go project; e5 over a stamped project, a
  moved layout, and an adopted repository's page.

**GREEN** — `parallel_gate.py` holds the page's paragraph and `docs.py` takes it beside `STAMP_PAGE` (`docs.py` is at 329:
three lines at most; the text lives in `parallel_gate.py`); `changelog.d/parallel-gate.md` completed — **Catch-up.** as e4,
the cost under `-j` for a Java gate (T006), which families were run and which only read (plan *Branch and integration*: Go,
TypeScript, Java (Quarkus) and Python run with the real toolchain; Spring read; GNU Make 3.81 and 4.3, Windows and macOS not
run), and the measurement left for the demo to fill. The delegate searches `docs/`, `assets/toolkit/docs/` and
`src/slipwai/` for text that still says the gate's checks run one after another or that `check-drawio` installs on every
run, and **reports any it finds without editing it** (not in this manifest).

**REFACTOR:** none expected.

**Verify:** `make test TESTS="test_parallel_gate_carry test_verify_stamp_page test_verify_stamp_ships test_changelog
test_migrate test_ci_fetch_migrate test_docs_index test_render_docs"` green, then `make lint typecheck check-structure`;
`git diff --stat` over the slice shows `VERSION` unchanged and **no `assets/toolkit/scripts/verify-stamp.py`**. Commit by
path; level line (MINOR, `VERSION` not raised, the fragment is this slice's one).

**Files:** `src/slipwai/project/parallel_gate.py`, `src/slipwai/project/docs.py`, `changelog.d/parallel-gate.md`,
`tests/test_parallel_gate_carry.py` (new), `tests/test_verify_stamp_page.py` (only if the adopted clause is put on the
adopted page).

---

## Phase 3: Gates and closing (host)

### T010 — Both full gates on the final tip, then the demo (host task)

- [ ] **Host task — not delegated.** First `make test TESTS="test_toolkit test_utf8_io test_changelog"` (the slice touches
  `assets/toolkit/`), then `make verify` and `make -f delivery/Makefile verify` on the tree after T009, both green
  (Principle XIV), the second also once with `CI=true GITHUB_ACTIONS=true` exported. `make verify`'s `test_matrix` holds every
  distinct native-gate shape of every backend to its own gate, which with `make starters` materialising every combination
  is AC-S04-63's *starters* clause; the Spring starter is read, not run. Confirm the slice's diff touches under `delivery/`
  only `delivery/survey/pinned.md` (and `tests/` under T001), `VERSION` is `1.6.0.dev0`, **`assets/toolkit/scripts/verify-stamp.py`
  is not among the changed files (AC-S04-62, R8e7)**, and nothing under `tools/`, the `Makefile` or this repository's CI
  changed. Then the demo from [quickstart.md](quickstart.md), run as the actor with this checkout's `./slipwai`; the
  measurement of §4 (AC-S04-22, -23) is written into the quickstart and the fragment by the host. **Not run, and said so on
  the board:** GNU Make 3.81 and 4.3, Windows under Git Bash, macOS, and `npm ci` from the shipped lock on any platform but this one.

### T011 — The adversary pass (host task)

- [ ] **Host task.** `drive-adversary` over the sync's boundary (a `uv` that fails halfway, two `make` runs at once on one
  `.venv`, `MAKEFLAGS` set by a caller), the gate's failure line under `-j`, the lock's three migration cases and the
  adopted line; any confirmed finding is a regression test at the owning layer, appended as a task below.

### T012 — Mutation (host task)

- [ ] **Host task.** `drive-mutation` over `parallel_gate.py`, `gate.py` and `model_targets.py`; the report recorded, the tree clean
  afterwards. This repository has no mutation command configured (as for every slice before it), which is reported, not
  pretended; survivors append tasks.

### T013 — Register row and benchmark (host task)

- [ ] **Host task.** The slice's row in the register and `benchmark.json` closed, after-acceptance commits riding in this
  slice's own pull request (`AGENTS.md`).

---

## Parallel opportunities

By manifest (each task's *Files* line):

| Task | Writes | Imports another task's file |
|---|---|---|
| T002 | `tests/parallel_gate.py`, three `tests/test_parallel_gate_sync*.py`, `parallel_gate.py`, `makefile.py`, `languages/python.py`, `backends.py`, `integration.py`, `openapi.py`, (`native_commands.py`), `changelog.d/parallel-gate.md` | none |
| T003 | `parallel_gate.py`, `makefile.py`, `openapi.py`, `tests/test_parallel_gate_first.py` | `tests/parallel_gate.py` (T002) |
| T004 | `gate.py`, `tests/parallel_gate.py`, `tests/test_parallel_gate_run.py` | — |
| T005 | `gate.py`, `tests/parallel_gate.py`, `tests/test_parallel_gate_output.py`, `tests/test_verify_stamp_recipe.py` | — |
| T006 | `parallel_gate.py`, `makefile.py`, `gate.py`, `tests/parallel_gate.py`, `tests/test_parallel_gate_families.py` | — |
| T007 | `adopted_targets.py`, `tests/test_parallel_gate_adopted.py`, `tests/test_verify_stamp_pinned.py` | `tests/parallel_gate.py` (T002) |
| T008 | `model_targets.py`, `assets/toolkit/scripts/event-model/package-lock.json`, `tests/test_model_{lock,install,install_skip}.py`, `tests/test_verify_stamp_inputs.py`, `tests/test_npm_install.py` | `tests/parallel_gate.py` (T002) |
| T009 | `parallel_gate.py`, `docs.py`, `changelog.d/parallel-gate.md`, `tests/test_parallel_gate_carry.py`, (`tests/test_verify_stamp_page.py`) | `tests/parallel_gate.py` |

The plan's three groups — the gate's own Makefile and recipe (R1–R5), the adopted gate (R6), the model tooling (R7) —
**hold against these manifests, with one correction**: R1–R5 are not one group of five, they are two chains that join.
R1 and R2 share `parallel_gate.py`, `makefile.py` and `openapi.py`; R3 and R4 share `gate.py` and the helper; R5 writes
all of those. R6 and R7 share no file with R1–R5 or with each other, **including their test files** (the only suites two
groups might both have edited — `test_verify_stamp_pinned.py` and `test_verify_stamp_recipe.py` — are R6's and R4's
alone, and `test_verify_stamp_inputs.py` and `test_npm_install.py` are R7's alone).

- **May run together** (after T001 and T002 are committed — T002 creates the helper they import and lands the fragment):
  **T003** (chain A), **T004** (chain B), **T007** (R6) and **T008** (R7) — four disjoint manifests. T005 joins as soon as T004
  is committed, beside whichever of T003, T007, T008 is still running. Most delegates at once: **four**.
- **May not:** T003 beside T002 (same `parallel_gate.py`/`makefile.py`/`openapi.py`), T005 beside T004 (same `gate.py` and
  helper), T006 before **both** T003 and T005 (it writes `makefile.py`/`parallel_gate.py`/`gate.py` and the helper), T004 or
  T005 beside T006 (helper and `gate.py`), T009 before T002–T008 (it states what they landed and edits the fragment T002
  began), and nobody beside T010. T004 and T003 cannot start before T002 because the helper is T002's. T007 and T008 import
  the helper unedited, so a T004/T005/T006 edit to it in another worktree does not reach them.
- **Shared-tree caution.** Every task's RED reversals and teeth change a generator (`gate.py`, `makefile.py`,
  `adopted_targets.py`, `model_targets.py`) that **every test in the other groups generates a project from**. So run each
  concurrent delegate in a worktree of its own off the commit that closes T002 (`isolation: worktree`), or run one group at
  a time while the others' quick tests run. The host commits by path in order — T002 first (the fragment lands in it), then
  T003, T004, T005, T007, T008 in any order, then T006, then T009 — and rebuilds nothing by hand: a conflict in a
  generator is a manifest overlap, which this table says there is none of.
- **Host tasks:** T001 precedes T002 (it records what T002, T007 and T008 change); T010 runs alone after T009, reading the
  whole tree; T011 – T013 follow, in order. `[P]` is on T003, T004, T005, T007 and T008 and nowhere else.

## Design review

No screen in this slice

## Convergence

**Converged at `9938fe9`, at the loop's bound of two passes; no `CRITICAL` and no `HIGH` in either** (cruise iteration 13;
`drive-converge`, host model, delegated, fresh context, both passes). Pass 1 accounted for every level — the ten
generators, what they generate over nine shapes (each family alone and mixed, a transport, a browser app, the event
profile, a production target, several services, an adopted repository, a project pruned by its backing-services script),
the generated projects' own `make` with the real Python, TypeScript, Go and Java toolchains, the published words, and the
carry through `slipwai migrate` from a factory archived at `3f44288` — and appended T014 (`MEDIUM`), T015 to T017 (`LOW`)
and one question (D94). Pass 2 re-ran each reproduction and found the four closed as classes, reached what pass 1 had
not (a moved layout with the event profile, Java Spring under `make -j verify`, AC-S04-54 and -64 by hand, AC-S04-57 and
-58 by hand) and appended T018 (`MEDIUM`, answered by D95 and fixed at `9938fe9`) and T019 (`LOW`, AC-S04-64 amended).
Nothing is left unchecked below. The tree was clean after each pass.

| Principle | Where the diff satisfies it |
|---|---|
| I. A generated project owns its files and passes its own gate | `verify-checks` and `ci` carry the same prerequisites before and after `migrate`; `python_first` and `gate_order` in `src/slipwai/project/parallel_gate.py` only add order; the model tooling installs with `npm … ci` (`src/slipwai/project/model_targets.py`), so no gate writes a lock; the adopted directive is confined to make started on the delivery Makefile (`src/slipwai/project/adopted_targets.py`, D95), so existing code keeps what it had; the fragment's catch-up says the three lock cases. Every starter's own gate is T010's |
| III. Simplicity | One phony `sync` and one prerequisite line; one file target in the root's pattern; one guarded directive; no new script, setting or content comparison |
| V. Acceptance-driven development | Each rule a cycle through a generated project's own `make`; holds seen to have teeth; the criteria run by hand in the passes held |
| VIII. Versioning | `VERSION` untouched at `1.6.0.dev0`; `changelog.d/parallel-gate.md` opens `MINOR` (a new generated file, D91); the adopted lines carry the experimental label |
| XI. Dependencies are locked | `assets/toolkit/scripts/event-model/package-lock.json`, made by npm, installed with `ci` |
| XIV. Agent-generated change meets the same bar | `assets/toolkit/scripts/verify-stamp.py` is not in the diff (AC-S04-62); `--synced` is an argument, never a default or a variable (`src/slipwai/project/languages/python.py`) |

Not run by either pass, and carried to the board: GNU Make 3.81 and 4.3 (`.FEATURES`, `$(eval)`, `ifeq`, `$(origin)`,
`$(words)` and `MAKEFILE_LIST` read or assumed, not run); Go's first run on a fresh clone; `migrate` carrying the
guarded directive into an already-adopted repository; the `make starters` matrix and the full gates (T010).

**After the gaps fixes (D96, item 11).** The acceptance trace that followed found eighteen things, none above
`MEDIUM`; T020 and T021 changed the code, and a bounded third reading over `1a8b3ef..HEAD` — taken for that reason only
— found nothing `CRITICAL`, `HIGH` or `MEDIUM` and one `LOW` (T022, a docstring, closed). The verdict stands at
`13f5afe`. Not reached by it: a Java run, `check-ux-gates` and `check-openapi` under `-j` with real tools, the catch-up's
conflict branch by hand.

The map: `make check-convergence` is run with the delivery gate at T010; this slice reached no new rung (no row of
`project.json`'s `convergence` moves — the factory's own gate is unchanged until a person migrates, D9).

## Differences from plan.md

Written for the host to correct the plan; none changes a requirement or a decision.

1. **The fragment lands in T002, not R8.** `changelog.d/parallel-gate.md` is listed under R8 in *Project Structure*; the first
   commit that changes a user-visible tree is R1's, and `AGENTS.md` says the entry is written in the commit that makes the
   change. T002 writes a first draft (MINOR), T009 completes it.
2. **`VERIFY_ORDER=1` is R5's, not R3/R4's.** *Project Structure* puts it in `gate.py` under R3, R4; nothing reads it until
   R5's `ifdef`, so a test cannot be red for it before then. T006 adds it; T004 and T005 do not.
3. **Two spellings of an integration command need `--synced`.** *Design* R1 says "`INTEGRATION_TEST`'s default"; the tree has
   the `?=` fallback **and** the `:=` the Postgres region sets (`integration.py`), and a Postgres project runs the second.
   T002 rewrites both.
4. **`check-openapi` is not in the string R2's one line is built from.** It hangs on `verify-checks` inside its transport's
   markers (`makefile.py`, `document_gate`), not in `verify_dependencies`, so *Design* R2's "one line after the gate's rule"
   misses it. T003 names `check-python` on `check-openapi`'s own target line in `openapi.py` (unmarked, always defined where
   it exists), and adds `openapi.py` to its manifest.
5. **Two more tests break under R7 than the plan lists.** `tests/test_verify_stamp_inputs.py:211–212` pins `npm --prefix
   scripts/event-model install` and the absence of `ci`; `tests/test_npm_install.py` counts exactly one `npm ci` in `make -n
   verify` of an event-profile TypeScript project (the model tooling's `npm ci --prefix` is now a second). Both are in T008's
   manifest, which the plan's *Project Structure* does not name.
6. **`tests/test_verify_stamp_pinned.py`'s amendment is R6's, not "for the sync phase".** *Project Structure* says it is
   "amended for the sync phase". Read against the tree, its generated half (`gate_prerequisites`, `gate_rule`, the `GENERATED`
   order, `check-python` first) holds unchanged after R1–R5 — the sync is not a prerequisite of `verify-checks` — and what
   breaks is `WrappedGatePinnedTest`'s byte-for-byte adopted rule, which R6's `.NOTPARALLEL:` moves. The sync phase is proved in
   `test_parallel_gate_sync*.py`. `tests/test_verify_stamp_recipe.py`'s amendment is R4's one line.
7. **Test files are split in advance.** R1's examples go in three files (`…_sync.py`, `…_sync_ways.py`, plus the new
   `…_sync_edges.py` for e11, e14, e15) and R7's e3–e10 in two (`test_model_install.py`, plus the new
   `test_model_install_skip.py`), so no file nears 350 lines.
8. **Real-toolchain examples are not suite tests.** R5e6, AC-S04-5, AC-S04-17 and AC-S04-47's real `npm ci` need Go, Java, Node
   and the registry; they are run once by hand by T006's and T008's delegate and again at the demo. R7e6 and R7e10 and R8e1 use
   real `npm`/`node` only where the example is *about* npm's own answer, and skip with their reason where the tool is absent.
9. **R3e3, e4, e5 are expected holds.** The plan's *Example map* lists only R3e1, e2, e7, e8 as holding today; research R-2 and
   R-6 show the checks already run together and make already prints a `***` line per failed target, so T004 observes each
   first. e6 (the gate's own last line) is the one example that is red today.
10. **R8e7 is the host's check, not a test.** A test cannot know which commits are the slice's; AC-S04-62 is confirmed at T010
    from the slice's diff.

## Phase 4: Convergence pass 1 (cruise iteration 13)

Appended by `drive-converge`, pass 1 of 2, over `3f44288..HEAD`. Each reproduction was run on a project generated by this
checkout under `/tmp`, with `CI`, `GITHUB_ACTIONS`, `GITLAB_CI` and `MAKEFLAGS` unset; GNU Make 4.4.1. No `CRITICAL` and no
`HIGH`: nothing below gives a wrong verdict or loses a check.

### T014 — `MEDIUM` — Every target that names `sync` runs its Python mode with `--synced`; `format` does not

- [x] *(f614b2f: `format`'s recipe passes through `in_recipe`; swept both ways over five shapes)* **Finding.** `format` is on the `…: sync` line (`parallel_gate.sync_rules`, `dependents`), but its recipe is built by
  `format_command(apps)` at `src/slipwai/project/makefile.py:163` and never passes through `in_recipe`, so it is written
  `./scripts/verify --format` (mixed: `./scripts/verify-python --format`) and syncs a second time inside the recipe. The
  Makefile's own comment (*every target below names it rather than syncing inside its own recipe*) and the fragment (*every
  target running a Python mode … sync every service once*) are untrue of it, and under `-j` with a second goal the recipe's own
  sync runs on the `.venv` another target is already running from — the overlap D90 removes.
  **Evidence.** Python + FastAPI + browser app, a `uv` stand-in that logs and execs the real one: `make format` → 2 lines
  beginning `sync --project apps/service`; `make -j format lint` → 2 sync lines, the second after lint's first `run` line.
  `grep -- --format Makefile` → `./scripts/verify --format` in the single-family, event-profile, aws-target and Python+Go
  projects alike.
  **GREEN (the class).** In every generated Makefile, every target that names `sync` as a prerequisite has `--synced` on every
  call of the Python family's script in its recipe, and every recipe line carrying `--synced` or `uv run … --no-sync` belongs to
  a target that names `sync`: a test that reads both directions over one starter per shape (one Python service, two, Python
  beside another family, with and without a formatter), red first for `format`. `make format` and `make format lint` then log
  one sync line per service.
  **Sweep performed.** Both directions over five generated Makefiles (Python/FastAPI/web; event profile with Postgres; aws
  target; Python + Go; two Python services + Go): `typecheck`, `lint`, `test`, `adversarial`, `migrate`, `test-integration[-<name>]`
  (both `INTEGRATION_TEST` spellings), `openapi`, `check-openapi` and `dev` agree; `format` is the only member that does not.
  No target was found running `--synced` or `--no-sync` without naming `sync`.

### T015 — `LOW` — Every sentence the fragment and the page say about order is true of a `-j` run; one is not

- [x] *(f91818b: the sentence now says a failed sync starts no check that runs a Python service's code)* **Finding.** `changelog.d/parallel-gate.md` says *A failed sync stops the run before any check starts, and says so once.*
  That is the serial run. Under `-j` only the targets that name `sync` wait for it; every other check has started.
  **Evidence.** A `uv` stand-in whose `sync` exits 1, `make -j verify` on a Python project: exit 2, no `run` line in the log
  (AC-S04-38 holds), `make[1]: *** [Makefile:44: sync] Error 1` once, and beneath it the output of `check-speckit`,
  `check-decisions`, `check-imports`, `check-migrations`, `check-slice-scope`, `check-codegraph`, `check-constitution`,
  `check-extensions`, `check-ux-gates`, `check-benchmark`, `check-agents` and `check-models`, all of which ran.
  **GREEN (the class).** Every sentence in the fragment and in `parallel_gate.PAGE` that states what precedes what is true of
  both runs or names the run it is true of; this one becomes what AC-S04-38 holds — no check that runs a Python service's code
  starts after a failed sync.
  **Sweep performed.** The other ordering sentences, each against a run here: *`check-python` is first under `-j`* (a stand-in
  old `python3`: no `uv` line, no check started); *a failed run ends on its own line, then make's own last line* (`-j`, `-k -j`
  and serial); the model tooling's *once per `make` run* (`make -j check-drawio model-drawio-test` on a fresh clone: one `npm ci`);
  *a passing run that installed as it went is not recorded* (Python + Go, first run writing `go.work.sum`). All true.

### T016 — `LOW` — Every variable that only the gate's recipe is meant to set is read only from there; `VERIFY_ORDER` is read from the environment

- [x] *(dd12f65: `ifeq ($(origin VERIFY_ORDER),command line)`; `$(origin)` on 3.81 assumed, not run)* **Finding.** `ifdef VERIFY_ORDER` (`parallel_gate.gate_order`) is true for a variable exported in a developer's shell, so
  the sentence in `gate.py` and the fragment — *a target typed by itself is what it was* — does not hold there. More work, never
  a different verdict.
  **Evidence.** Java (Quarkus) project: `make -n test` prints one Maven line (`./mvnw -B -q test`); `VERIFY_ORDER=1 make -n test`
  prints three (`… compile checkstyle:check pmd:check spotbugs:check`, `… test-compile`, `… test`).
  **GREEN (the class).** Every variable a generated Makefile reads that only its own recipe is meant to set takes effect only
  when it came from make's command line (`$(origin …)` is 3.80's), with a test that sets it in the environment and sees the
  target typed alone unchanged.
  **Sweep performed.** `VERIFY_ORDER`: reads the environment (this finding). `MODEL_INSTALLED`: set in the environment it only
  silences the skip line and never says it falsely (run: `MODEL_INSTALLED=1 make check-drawio`). `VERIFY_GROUP`, `VERIFY_STAMP`:
  assigned with `:=` in the Makefile, so the environment does not reach them. `--synced` is an argument, never a variable
  (`./scripts/verify --synced` → `unknown verify mode`, exit 2, after syncing; `--lint-only x --synced` syncs).

### T017 — `LOW` — `in_recipe` applied twice corrupts the recipe: the look-ahead meant to make it idempotent backtracks

- [x] *(9f87a12: the mode is taken whole; applied twice over every mode and both script spellings)* **Finding.** `src/slipwai/project/parallel_gate.py:66` — `(… --[a-z]+(?:-[a-z]+)*)(?! --synced)` gives back one letter of the
  mode when ` --synced` already follows. Latent: every caller applies it once today.
  **Evidence.** The line's own expression applied to its own output: `./scripts/verify --lint-only --synced` →
  `./scripts/verify --lint-onl --syncedy --synced`.
  **GREEN (the class).** For every recipe the generators build, `in_recipe(in_recipe(r)) == in_recipe(r)`, held by a unit test
  over each mode the script has and each family spelling of the script's path.
  **Sweep performed.** The four call sites (`makefile.py` `native`, `per_suite`, the two `migrate` recipes; `integration.py`'s
  `INTEGRATION_TEST`) each apply it once, and `grep -- '--synced'` over five generated Makefiles finds no doubled or broken
  spelling; a path such as `./scripts/verify-go` is not matched by the Python script's expression.

### Question for the owner — `LOW` — does the skip line say *matches*, or what make knows?

- [x] *(answered by D94: make's notion of matches stands, as D91 decided; AC-S04-55 says so)* **A question, not a task.** `check-drawio: the model tooling matches scripts/event-model/package-lock.json; not
  reinstalled` is printed whenever the marker is newer than both manifests. A lock whose bytes changed while its modification
  time stayed older than the marker (a copy or an archive that preserves times; reproduced with `sed -i` on the lock, then
  `touch -d 2020-01-01` on it) gets the line and no install. AC-S04-55 says a line that could be wrong is not shipped; AC-S04-48
  fixes the line's words. `git checkout` and an editor both date the file now, so ordinary work never meets it, and the Parking
  Lot already places the hand-edited *installed tree*, not the back-dated lock. Either the line is accepted as make's own notion
  of *matches* and AC-S04-55 says so, or it is re-worded to what is known (*not older than*) with AC-S04-48 amended.

## Phase 4: Convergence pass 2 (cruise iteration 13)

Appended by `drive-converge`, pass 2 of 2, over `3f44288..HEAD` at `d2f23fb`. Each reproduction was run on a project made by
this checkout under `/tmp/s04p2`, with `CI`, `GITHUB_ACTIONS`, `GITLAB_CI` and `MAKEFLAGS` unset, on a branch other than
`main`; GNU Make 4.4.1. Pass 1's four findings are closed as classes (T014: `make format` and `make -j format lint` log one
sync line; T015: the fragment's sentence is the `-j` one; T016: `VERIFY_ORDER=1 make -n test` prints one Maven line, on the
command line three, and `$(origin)` answers `command line` in the gate's sub-make and the make below it, `environment` for an
export; T017: the expression applied to its own output is unchanged for every spelling tried). No `CRITICAL` and no `HIGH`:
nothing below gives a wrong verdict or loses a check. Levels reached this pass: an adopted repository with the event profile
(the moved layout), Java Spring under `make -j verify` with its real toolchain, AC-S04-64 and AC-S04-54 by hand on Python,
AC-S04-57 and -58 by hand against a factory archived at `3f44288`.

### T018 — `MEDIUM` — Every sentence that says what the bare `.NOTPARALLEL:` holds is true of the make it is read by; through `-include` it holds the repository's own targets too

- [x] *(9938fe9: `ifeq ($(words $(MAKEFILE_LIST)),1)` around the directive; the five places re-worded; AC-S04-67 to -70 in `tests/test_parallel_gate_include.py`)* **Finding.** `src/slipwai/project/adopted_targets.py:90` writes a bare `.NOTPARALLEL:` into `delivery/Makefile`. `slipwai adopt`
  ends its report with *add `-include delivery/Makefile` to the root Makefile* (and writes that line itself where there was no
  root Makefile), and GNU Make applies the directive to the whole run, not to the file it sits in. So after `slipwai migrate`,
  every target of the adopted repository's own root Makefile runs serially under `make -j`, the build it had before adoption
  included. The fragment says *An adopted repository's gate is serial whatever `-j` says*, the page (`parallel_gate.PAGE`) says
  *a bare `.NOTPARALLEL:` holds its own targets*, and D88's R7 says *Nothing else in that Makefile changes*; none says the
  repository's own targets lose `-j`, and AGENTS.md holds existing code *to nothing it did not have before*. Slower, never a
  different verdict; experimental path.
  **Evidence.** A repository adopted with `--profile event-modelling`, two targets of its own in the root Makefile (`own-a`,
  `own-b`, each `sleep 2`): with `-include delivery/Makefile`, `make -j own-a own-b` takes 4.0 s; with the line taken out, 2.0 s.
  **GREEN (the class).** Every place a user of an adopted repository reads what is serial — the fragment's body and catch-up,
  `PAGE`, the comment the Makefile carries above the directive, and the adopt report's `-include` line — says what make does:
  a root Makefile that includes the delivery one runs every target serially under `-j`, and `make -f delivery/Makefile` leaves
  the root's own as they were. A test reads the four for that sentence.
  **A question inside it, for the owner.** Words are the smallest fix and keep D88's R7 as decided. The other answer is a
  mechanism that holds the gate and leaves the repository's own targets their `-j` — and that is a decision about
  `baseline.json`'s one writer, not this task's to make: does D88's R7 stand with the sentence corrected, or is the reach
  through `-include` to be removed?
  **Sweep performed.** The directive is written in one place (`adopted_targets.SERIAL`; `grep -rn NOTPARALLEL src/slipwai`), and a
  stamped project's Makefile has none (five read). Paths in the adopted Makefile are spelled for the layout: the marker, the
  `npm --prefix delivery/scripts/event-model ci` recipe, `install:` naming the marker, and the skip line all say
  `delivery/scripts/event-model/…`; `make -f delivery/Makefile -j check-drawio model-drawio-test` on a fresh adoption ran one
  `npm ci`, 38 tests passed, and the next `check-drawio` printed the skip line with the `delivery/` path. A sub-make
  (`$(MAKE) -C`) of the repository's own is not held, as the page already says.
  **Answered by D95 — the GREEN is now this, and it replaces the one above.** The directive is written inside a
  conditional that is true only when the delivery Makefile is the one make was started on (D95's R1), still once,
  after the pinned `verify` rule, whose bytes do not move; the five places D95's R5 lists say R2 to R4; the adopt
  report's `-include` line stays as it is. Criteria: AC-S04-24, -26, -27, -60 and -61 as re-worded, AC-S04-67 to -70.
  **Files:** `src/slipwai/project/adopted_targets.py`, `src/slipwai/project/parallel_gate.py` (`PAGE`),
  `src/slipwai/project/adopted.py` (at 350 lines: a sentence replaces a sentence, or the text moves to
  `adopted_targets.py`), `changelog.d/parallel-gate.md`, `tests/test_parallel_gate_adopted.py`,
  `tests/test_verify_stamp_pinned.py` (the `SERIAL` constant only), `tests/test_parallel_gate_carry.py` and
  `tests/test_parallel_gate_converge.py` (the sentences they hold), and a new `tests/test_parallel_gate_include.py`
  for AC-S04-67 to -70.

### T019 — `LOW` — Every family's first unrecorded pass says the line the criterion names; Python's says the stamp's other one

- [x] *(the host amended AC-S04-64: one of the stamp's two lines, with which family says which)* **Finding.** AC-S04-64 and D93 (point 4) name the line of the unrecorded first pass: `verify: this pass was not recorded — a
  file git ignores changed while the checks ran …`. A Python event-profile clone with nothing installed has no `.venv`, so the
  stamp cannot build its key and says D73's rule 5 instead, before the first check: `verify: the full gate runs and this run
  records nothing — cannot read apps/service/.venv/pyvenv.cfg (No such file or directory)`. The line the criterion names is not
  printed. What the criterion is for holds: the pass installs and is not recorded, the second runs in full, installs nothing
  and is recorded, the third reuses; and the page's sentence (AC-S04-66) is true of both.
  **Evidence.** `pyev` (Python, event profile, Postgres), fresh: run 1 exit 0, line 1 the *records nothing* line, `npm --prefix
  scripts/event-model ci` at line 114, no *was not recorded* line; run 2 exit 0, the skip line, no npm for the model tooling;
  run 3 the reuse line. `tsev` (TypeScript, event profile) and `jspring` (Java Spring): run 1 ends on the *was not recorded*
  line, run 2 records, run 3 reuses. AC-S04-54 on a second fresh Python clone: `make install` ran the model tooling's `npm ci`
  once and left `git status --porcelain` empty, the first `make verify` ran no npm for it and was recorded, the second reused.
  **GREEN (the class).** AC-S04-64 and its example say *one of the stamp's two lines for a run that records nothing* and name
  which family says which; the stamp's script is not changed (D73, rule 8). A criterion's wording, so the host amends
  `spec.md` beside D93 rather than a delegate.
  **Sweep performed.** The first run's line over three families with their real toolchains (Python, TypeScript, Java Spring);
  Go not run here — the Parking Lot already places its `go.work.sum`.

## Phase 4: The after-converge gaps pass (cruise iteration 13)

Two `drive-gaps` delegates traced AC-S04-1 to -70 over `3f44288..HEAD` and returned eighteen findings (G1–G18), none
above `MEDIUM`; D96 says what each becomes. The findings as numbered are quoted in D96's *Question*; the criteria it
re-words and adds are AC-S04-1, -48, -49, -56, -59, -60, -65 and AC-S04-71 to -81 in `spec.md`.

### T020 — `MEDIUM` — The gate's own order: Go keeps the serial order, nothing starts beside a failing `check-python`, and every gate target that reads the root's installed tree waits for it (G1–G8 · D96 items 1, 2, 3, 5 · AC-S04-1, -71 to -76, -81)

- [x] *(940893e, c7e72ae, 165ef50, 3452901: Go is `typecheck test: lint` — on a fresh Go clone with the real toolchain `go.work.sum` is written by `lint`'s last `go` command and not changed after, serial and `-j`, both exit 0; the two install markers take `| check-python` inside the command-line guard; `check-ux-gates: build-packages` in a project with an npm workspace and `check-openapi` on `build-packages` for a TypeScript exporter; the class held over twelve shapes in `tests/test_parallel_gate_reads.py`; the holds with teeth)* G1: the gate-only order for Go becomes `typecheck test: lint`; AC-S04-1's test runs every family's shape with the
  order unsorted; the Go chain test stops sorting; `gate_order`'s docstring says the new order. G2: inside the same
  command-line guard, the root's install marker and the model tooling's marker take `| check-python` (the model
  marker by the name `model_targets.MARKER`, whatever its value — T021 changes the value, not the name); `python_first`'s
  docstring is corrected. G3, G4: `check-ux-gates` takes `build-packages` (or the root marker) in a project with an npm
  workspace, a TypeScript service's `check-openapi` takes `build-packages`; the class is held by a closed-list test
  over every starter shape. G5–G8: the hold examples D96 item 5 lists for this seam, each with teeth shown once.
  After GREEN, run a Go starter with the real toolchain on a fresh clone, serially and under `-j`, and report whether
  `typecheck` or `test` wrote `go.work.sum` after `lint` ended (D96's *Would reverse if*).

**Files:** `src/slipwai/project/parallel_gate.py`, `src/slipwai/project/makefile.py` (333 of 350), `src/slipwai/project/openapi.py`,
`src/slipwai/project/shared_packages.py`, `tests/test_parallel_gate_first.py`, `tests/test_parallel_gate_families.py`,
`tests/test_parallel_gate_adopted.py`, `tests/test_parallel_gate_run.py`, `tests/test_parallel_gate_sync.py`, and a new
`tests/test_parallel_gate_reads.py` (the class, AC-S04-72 to -76). Not `tests/parallel_gate.py` (at 350) and not
`src/slipwai/project/model_targets.py` (T021's).

### T021 — `MEDIUM` — The model tooling's marker is the recipe's own, and the words a maintainer follows are true (G9–G14, G17 · D96 items 4 to 8 · AC-S04-48, -49, -60, -65, -77 to -81)

- [x] *(3aa7cc2, 35c5804, a85e096, b6e33fc, and the host's fragment commit after them: `MARKER` is `scripts/event-model/node_modules/.installed`; AC-S04-77 red first with real npm; the catch-up's three corrections; the README's sentence and the manifest's description, a regenerated lock byte-identical to the shipped one; AC-S04-54 and -64 on TypeScript with real npm)* G9: `model_targets.MARKER` becomes `scripts/event-model/node_modules/.installed` (the name `MARKER` stays), touched
  after a successful `npm … ci`; the skip line's words and the stamp's script do not change; a real-npm test regenerates
  the lock on an installed tree and sees the reinstall (AC-S04-77), and one holds AC-S04-78. G10–G12: the catch-up says
  `git add` before the commit in the regenerate branch, names the paths for both layouts in one clause, and has one
  sentence for a teammate with the untracked lock. G13: the model README's sentence and the manifest's description.
  G14, G17: the regenerate branch run with real npm; AC-S04-54 and -64 on TypeScript with real npm. G15, G16: the
  fragment's run-and-read paragraph says the migration of a project made before the slice was run by hand.

**Files:** `src/slipwai/project/model_targets.py`, `changelog.d/parallel-gate.md`, `assets/toolkit/docs/event-model/README.md`,
`assets/toolkit/scripts/event-model/package.json` (the description only), `tests/test_model_install.py`,
`tests/test_model_install_skip.py`, `tests/test_model_install_first.py`, `tests/test_model_lock.py`,
`tests/test_parallel_gate_carry.py`, `tests/test_gate_recipes_pinned.py` (the marker's name in its stand-in only),
`tests/test_verify_stamp_inputs.py` (only if it names the marker), and a new `tests/test_model_install_regenerate.py`.

## Phase 4: Convergence re-check after the gaps fixes (cruise iteration 13)

Taken over `git diff 1a8b3ef..HEAD -- src assets tests changelog.d` only, by running generated projects under
`/tmp/s04-recheck` with `CI`, `GITHUB_ACTIONS`, `GITLAB_CI` and `MAKEFLAGS` unset (GNU Make 4.4.1, real `uv`, `npm` and
`go`; Java not run in this pass). **No `CRITICAL` or `HIGH`, no `MEDIUM`: the verdict of pass 2 stands.** One `LOW`,
which does not re-open the loop.

### T022 — `LOW` — `gate_order`'s docstring says which `go` command writes `go.work.sum` as the run shows it

- [x] *(13f5afe: the docstring corrected)* `src/slipwai/project/parallel_gate.py`, `gate_order`'s docstring: *"Go's first `go` command resolves the workspace
  and writes `go.work.sum` on a fresh clone"*. On a fresh clone of a Go starter (go-std, real toolchain) `go vet ./...`,
  the first `go` command of `lint`, left no `go.work.sum`; `go tool staticcheck ./...`, the last, wrote it; `go test
  -run '^$' ./...` after it left the file's hash unchanged. The fragment already says it right (*"`lint`, whose last
  `go` command resolves the workspace"*); the docstring and the fragment should say the same thing. A comment only:
  nothing generated changes, no fragment, `VERSION` stays. D96's *Would reverse if* did not fire.

