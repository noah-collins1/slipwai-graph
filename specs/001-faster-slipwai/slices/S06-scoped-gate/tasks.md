# Tasks: S06-scoped-gate — a slice branch runs the checks whose inputs changed, and broadens where it cannot tell

**Input**: [plan.md](plan.md) (*The example map* R1–R14 is what the tasks cut on; *Structure Decision*; *Pin*),
[research.md](research.md), [data-model.md](data-model.md), [quickstart.md](quickstart.md); acceptance criteria
AC-S06-1 … AC-S06-19 in `specs/001-faster-slipwai/spec.md` under `### S06-scoped-gate`; decisions D114, D115, D116, D117,
D123, D124 in `specs/001-faster-slipwai/decisions.md`; ADR 0004 (Proposed). No `examples.md`: a method slice with no
screen and no event model of its own, so **no white box, no mockup task and no styling task**. The one story is **US2**
(FR-006, FR-007, FR-023, SC-007), *a slice branch runs the checks whose inputs changed, names the rest, and runs the
full gate wherever it cannot tell*.

**Branch**: `adopt-method` (D12). No `slice/` branch, no push, no claim. One commit per task.

**Delegation** (`.specify/drive.json`: `delegate: story`, `cycle: rule`): the host hands one `drive-implement` delegate
the whole of US2 — the Phase 1 tasks in dependency order — or, where the manifests below are disjoint, more than one,
each in a worktree of its own (*Parallel opportunities*). Each task is one RED-GREEN-REFACTOR cycle and one commit,
opening with **one rule's examples**; a delegate never writes a rule's tests ahead of the previous rule's commit. A
task's *Files* line is its manifest, the only files that delegate may write. Nobody but the host writes `tasks.md`. A
delegate that needs a file outside its manifest — a test elsewhere that pins text it changes — **stops and names the
file; the host adds it.**

**Not a task:** R14 / AC-S06-19 (the measurement, and S05's xdist still holding at the merge root) is the demo's
(T019): its measured part is the hand's, and its "pytest still runs with `-n auto --maxprocesses 4`" part is a hold
over S05's own unedited tests, so a task for it would be a test that passes the moment it is written. Writing the white
boxes back as mockups is not a task either: the slice has none (`check-model` has nothing to refuse).

## Constraints that hold for every task

- **MINOR, `VERSION` stays `1.6.0.dev0`.** `cat VERSION` reads `1.6.0.dev0`; the last released entry is `1.5.1`;
  `changelog.d/` already holds MINOR fragments (`parallel-gate.md`, `runner-bookkeeping.md`, `verify-stamp.md`,
  `xdist.md`), so a MINOR fragment leaves the number as it is (`tests/test_changelog.py` checks the pair; D114). Not
  edited by any task: `VERSION`; anything under `release/`; the root `Makefile`; this repository's `delivery/`
  (including `delivery/scripts/` and `delivery/.written`'s files), `tools/`, CI and hook settings; `gate.py`,
  `parallel_gate.py`, `adopted_targets.py`, `metadata.py`, `catalog.json`. **No control needs a change** (plan,
  *Not changed*), so there is **no patch task for a person**; a delegate that finds one is needed stops and names it.
  The root `Makefile`'s `VERIFY_STAMP_SCRIPT` is `assets/toolkit/scripts/verify-stamp.py`, the file T005 edits: T005
  therefore also runs the factory's own stamp suites (below) and says so in its report.
- **Size and width.** Every file under `src/` and `tests/` stays within 350 lines (`make check-structure`) and 120
  columns (ruff). Current: `makefile.py` **333**, `docs.py` **331**, `commands.py` **345**, `native_commands.py` **308**,
  `agent_settings.py` 200, `parallel_slices.py` 138. The new factory code goes in `scoped_targets.py`; `makefile.py`
  takes it in two lines, `docs.py` in two, `native_commands.py` nets about six, `commands.py` gains no line (reworded in
  place). A test file that nears 350 splits by example and the report names the new file — the plan's six test modules
  are cut into more below (*Differences from plan.md*). Assets are not counted by `check-structure`, but the three
  `scripts/verify_scoped/` modules still split along the plan's table / record / choose lines. No literal `apps/service`
  or `apps/web` in any new script or module (`toolkit.spoken_for` rewrites those); `sys.dont_write_bytecode = True`
  before any sibling import. Every `read_text`/`open` names `encoding="utf-8"`.
- **Tests.** Standard library only; a fake is an executable or a class written in the test tree implementing the real
  tool's command line — **never a mocking framework, `unittest.mock` included**. Generated projects live in temporary
  directories with stand-ins first on `PATH` (a logging `npm`, a `node` whose `--version` the test sets; reuse
  `tests/parallel_gate.py`'s stand-in writer and `gate_environment` and `tests/stamp_fixture.py`'s `CI_MARKERS`,
  `MAKE_STATE`, `GIT_STATE`, imported, never edited here). Evidence is a log or a file, never a clock. Every
  `subprocess.run` carries `timeout=`. `CI`, `GITHUB_ACTIONS`, `GITLAB_CI`, `MAKEFLAGS`, `MFLAGS`, `MAKELEVEL`,
  `MAKEOVERRIDES`, `MAKEFILES`, `VERIFY_FORCE` and the three `GIT_*` state variables are removed from a generated
  project's command unless the example sets them.
- **Probes** that import a script under `assets/` (`verify-stamp.py`, `check-slice-scope.py`, `verify-scoped.py`) run as
  **`python3 -B`**, so no `__pycache__/` is left under `assets/` (it would be a change under `scripts/` in a generated
  copy, and an untracked file in this tree).
- **A task that changes a generated `Makefile`'s `verify`/`ci` recipe or its text** (T002, T003, T013): before editing,
  **search `tests/` for helpers that rebuild an old Makefile by regex** —
  `grep -rn "re\.\(sub\|compile\|search\|match\)" tests | grep -i "make"` and `grep -rln "verify-checks\|\.PHONY" tests`
  — and keep them working or name them in the report; and run **every suite that reads a generated gate**:
  `make test TESTS="$(ls tests | grep -E '^test_(verify_stamp|parallel_gate|model_|gate_)' | sed 's/\.py$//' | tr '\n' ' ')"`
  (one command; it is the list `ls tests | grep -E '^test_(verify_stamp|parallel_gate|model_|gate_)'` prints) together with
  `test_matrix test_commands test_commit_boundaries`. `tests/test_verify_stamp_pinned.py` (the `verify` rule's bytes) and
  `tests/test_parallel_gate_reads.py` (`READS_NOTHING` over the gate's targets) are the two that matter most.
- **Commit by path** — `git commit -m … -- <the task's files>`, a new file `git add`ed by its exact path first; never
  `git add -A`, never `git commit -a`, never `git checkout -- <file>` on work that is not the delegate's own (the
  sanctioned RED/teeth route in `delivery/docs/delegated-agent-safety.md` is the only one).
- **RED is seen** for its stated reason before the production file is touched. A **hold** (an example that passes today)
  is written as a hold, said so in its name or docstring, and **seen to have teeth** before commit: change the
  production file (or invert one assertion), observe the failure, restore. A hold with no teeth is not claimed. A task
  whose GREEN would be empty is not in this file: its examples are folded into the task that makes the behaviour.
- **GREEN is a class**, not an instance: every shape the matrix and `tests/test_verify_stamp_scan.SHAPES` cover, plus a
  two-service shape, where the rule says *every*.
- **Before each commit** run `make lint typecheck check-structure`.
- **Versioning, on every commit** (`AGENTS.md`): a commit that changes `src/slipwai/` or `assets/` says `Level MINOR;
  VERSION already carries it (1.6.0.dev0); the fragment changelog.d/scoped-gate.md claims MINOR` and names the reason
  (a new target, a derived record and one optional `project.json` key, D114); a commit that changes only `tests/` says it
  reaches no user. **The fragment `changelog.d/scoped-gate.md` lands in T002**, the first commit that changes a
  user-visible tree, as a first draft with first line `MINOR` (so `tests/test_changelog.py` holds from then on); T015
  completes it. No other task touches it. Shape: [`changelog.d/README.md`](../../../../changelog.d/README.md) — the level
  on the first line, one bold lead sentence, and **one paragraph beginning `**Catch-up.**`** that stands alone.

### The sweep at planning

Tests under `tests/` that read a generated `Makefile`, `scripts/` list, ladder text, agent settings, constitution
templates or the gates page, and that this slice can break. **Hits** (met by the task named; none is edited by a task
that does not list it in *Files*):

| Hit | Pins | Met by |
|---|---|---|
| `tests/test_verify_stamp_pinned.py`, `_recipe.py`, `_scan.py`, `tests/test_parallel_gate_reads.py` | the `verify` rule's bytes; the gate's recipes by regex; `READS_NOTHING` over the gate's targets | hold: **T002, T003** append after everything; units are not gate targets |
| `tests/test_gate_recipes_pinned.py`, `tests/test_gate_walks*.py` | the gate's recipe lines as the walk sees them | watch, **T002**: the units repeat today's merged lines; amend only where a test counts recipe lines in the whole file, and name it |
| `tests/test_toolkit.py`, `tests/test_toolkit_*` (if present) | the toolkit's file list and the `spoken_for` rewrite | watch, **T003**: the new script and `verify_scoped/` ship; a test that lists the scripts learns them |
| `tests/test_verify_stamp_*` (all) | `verify-stamp.py`'s `record`, `begin_full_run`, `reuse` | **T005** adds the baseline; every one stays green, the stamp's bytes unchanged |
| `tests/test_commit_boundaries.py:33` | the ladder does not say *start from a green `make verify`, take one…*; the constitution phrase *immediately before that first implementation push*; the planning skill's *After demo acceptance* | **T014** keeps all three phrases |
| `tests/test_commands.py`, `tests/test_agent_settings*.py`, `tests/test_parallel_slices*.py` | the ladder and settings text | **T014** amends only the lines its words replace, and names them |
| `tests/test_gates.py`, `tests/test_verify_stamp_page.py`, `tests/test_docs_index.py` | the gates page; two adopted holds say an adopted page says nothing of a stamp | **T015**: an adopted page gains the one sentence and no *stamp* word; amend a hold only if it names the new text |
| `tests/test_replay.py`, `tests/test_migrate.py`, `tests/test_adopt*.py` | `project.json` before and after a replay, migrate, adopt | **T015**: `metadata()` writes no `verification` key (AC-S06-17); adopt writes none |
| `tests/test_matrix.py` | every backend's real `make verify` | watch, **T016**: the gate's text before the new suffix is byte for byte, so each starter still passes its own gate |
| `tests/test_changelog.py` | the fragments' highest level against `VERSION` | hold: MINOR on `1.6.0.dev0`, in every Verify that touches `changelog.d/` |

## Format: `[ID] [P?] [Story] Description` — each task is one increment, one commit

`[P]` marks a task whose files are disjoint from every sibling it could run beside; see *Parallel opportunities*.

---

## Phase 1: Implementation stage

Each task starts from the green committed suite.

### T001 — Pin: the generated gate before anything moves (host task)

- [x] **Host task; no story; no commit.** Before the first increment: run the pin set once and record that it is green:
  `make test TESTS="test_verify_stamp_pinned test_verify_stamp_recipe test_verify_stamp_scan test_parallel_gate_reads test_commit_boundaries test_commands test_matrix"`.
  Then `make starters` and keep `build/` aside (untracked output, not a tracked file) so the last task's diff of that tree
  is the change a user sees (`docs/maintaining.md`, *Browse the starters*): a `Makefile` suffix, the new scripts,
  `verify-stamp.py`, the gates page, the settings line, the ladder text.

### T002 — [US2] A component is a deployable with targets of its own (R3 · AC-S06-2, -4, -14)

- [x] **Rule R3.** First commit that changes a user-visible tree, so the fragment's first draft lands in it (first line
  `MINOR`, one lead sentence, a **Catch-up.** paragraph that stands alone: a project made before gains `make
  verify-scoped` and the per-deployable targets after `slipwai migrate`, its merge root and CI still run `make verify`,
  and an optional `verification.obligations` key in `project.json` declares an integration obligation; T015 completes
  it). Follow *the Makefile-recipe search* in the constraints before editing.

**RED** (new `tests/test_scoped_targets.py`; `FactoryTestCase.generate` from `tests/support.py`; parse the generated
`Makefile` and read the make database with `make -npq -f Makefile .DEFAULT`, exit 2 and nothing run, research R-4):
- e1 TypeScript service + web app: six units (`lint-`, `typecheck-`, `test-` each for `service` and `web`), no family
  target, each unit's recipe one line of today's merged recipe *(fails today: no such targets)*.
- e2 two Python services: a family target `lint_python` holding `./scripts/verify --lint-only --synced`; `lint-service`
  and `lint-billing` name it as a prerequisite and have no recipe of their own; units take `sync` and `check-python` as the
  gate's checks do *(fails today)*.
- e3 a Go service: `lint_go` holds the `gofmt` line, `test_go` the `covdata` line; a Java service's units run in the
  order `VERIFY_ORDER` gives (`gate_order`); npm-family units take `build-packages` *(fails today)*.
- e4 the class — every shape in `test_verify_stamp_scan.SHAPES`, the matrix's shapes and a two-service shape: for every
  check, the unit and family lines **in order** are exactly that check's recipe lines in the pre-slice make database *(fails
  today)*.
- e5 **hold**: the generated text before the new section equals `makefile()`'s pre-slice output for every shape; the
  `verify`, `verify-checks` and `ci` rules are byte for byte *(teeth: edit one byte of `verify-checks` and see it fail)*.
- e6 a deployable named `integration` (and `integration-billing`): it gets **no** units, because `test-integration` and
  `test-integration-<service>` are existing targets, and the existing recipes are untouched (R-3) *(fails today only as
  far as the class: red on the missing units elsewhere; this one is a hold with teeth — emit `test-integration` and see
  the redefinition fail)*.
- e7 every unit and family target is classified by `READS_NOTHING`'s rules as `tests/test_parallel_gate_reads.py` does for
  the gate's own, and none appears in `make help`.

**GREEN** — new `src/slipwai/project/scoped_targets.py` (`scoped_section(apps, layout)`: unit rules, family targets,
their prerequisites and `VERIFY_ORDER` chains, the name-collision rule); `native_commands.py` extracts `web_recipes(web)`
so the web lines are spelled once for the merged recipes and the units; `makefile.py` imports it and appends
`{scoped_section(apps, layout)}` after `{adoption_targets(apps, layout)}` at the very end — **nothing before it moves**.
`changelog.d/scoped-gate.md` first draft.

**REFACTOR:** the recipe lines are read from `commands_of` once, not spelled twice.

**Verify:** `make test TESTS="test_scoped_targets test_changelog"` and the *every suite that reads a generated gate*
command from the constraints, then `make lint typecheck check-structure`. Commit by path; level line as above.

**Files:** `src/slipwai/project/scoped_targets.py` (new), `src/slipwai/project/makefile.py`,
`src/slipwai/project/native_commands.py`, `changelog.d/scoped-gate.md` (new), `tests/test_scoped_targets.py` (new).

### T003 — [US2] `make verify-scoped` is the full gate wherever it cannot read the branch (R1 · AC-S06-1, -14)

- [x] **Rule R1.** Needs T002 (`scoped_section` gains the `verify-scoped` rule). Creates `scripts/verify-scoped.py` with
  verb `run` and only R1's borders: everything past them is later tasks, and until then a slice branch with a usable base
  also runs `make verify` (said as one line), so the target is never wrong in between. Follow *the Makefile-recipe search*.

**RED** (new `tests/scoped_fixture.py` — generate a shape once per class, `git init`, `slice/S1` branch, stand-ins on
`PATH`, a `main` ref — and new `tests/test_verify_scoped_borders.py`; stand-in `make` is **not** used: the project's own
`make verify` is replaced by a logging recipe by running against a generated project whose checks are stand-ins):
- e1 on `main`: `make verify-scoped` prints `verify-scoped: the full gate runs, as \`make verify\` — this is the trunk
  (\`main\`)`, then `make verify` runs, a stamp is neither read nor written *(fails today: no target)*.
- e2 `feature/x`: the line names the branch; e3 `CI=1` on `slice/a` (and `GITHUB_ACTIONS`, `GITLAB_CI`): names `CI`; e4
  `slice/a` with no `main`/`master` ref: the line carries `check-slice-scope`'s own reason (`slice/<id> has no usable
  base — …`); e5 `VERIFY_FORCE=1`: `VERIFY_FORCE=1` and a forced `make verify`; e6 a detached `HEAD` and an unborn `HEAD`;
  e7 `MAKEFLAGS` carrying `n`, `t` or `q`: `make was run with -<flags>`; e8 a trunk the gate cannot tell: verify-stamp's
  words. The order is the plan's, asked in that order: a case where two hold prints the first only.
- e9 a failing check under e1: the exit status is `make verify`'s *(fails today as e1)*.
- e10 **hold**: the generated `verify`, `verify-checks` and `ci` rules in every shape are byte for byte the pre-slice text
  *(T002's e5 stands; teeth: rename `verify` in the suffix)*.
- e11 the script ships: `scripts/verify-scoped.py` and `scripts/verify_scoped/` are in a generated project, hold no
  literal `apps/service` or `apps/web`, and importing them writes no `__pycache__/` (`python3 -B` probe, then
  `git status --porcelain` clean).

**GREEN** — `assets/toolkit/scripts/verify-scoped.py` (`run` and `record` verbs, only `run`'s borders now: argument and
environment checks, `check-slice-scope`'s `SLICE_BRANCH` and `merge_base()` imported by path with
`sys.dont_write_bytecode` set, one line, then `"$(MAKE)" -f <makefile> verify` with its status); `verify_scoped/` created
with an empty package marker if the import needs one; `scoped_targets.py` adds the `verify-scoped` rule (a
`$(MAKE){layout.make_flag}` convention, as `ratchet-tighten` has it) for a stamped gate.

**REFACTOR:** the borders are an ordered list of small predicates, one reason each.

**Verify:** `python3 -B scripts/verify-scoped.py` is exercised through the generated project, not imported here;
`make test TESTS="test_verify_scoped_borders test_scoped_targets test_toolkit test_changelog"` and the every-gate-suite
command, then `make lint typecheck check-structure`. Commit by path; level line as above.

**Files:** `assets/toolkit/scripts/verify-scoped.py` (new), `assets/toolkit/scripts/verify_scoped/__init__.py` (new, only
if the import needs it), `src/slipwai/project/scoped_targets.py`, `tests/scoped_fixture.py` (new),
`tests/test_verify_scoped_borders.py` (new), and `tests/test_toolkit.py` only if it lists the scripts.

### T004 — [US2] A stamp is stronger than any scoped run (R2 · AC-S06-10)

- [x] **Rule R2.** Needs T003.

**RED** (new `tests/test_verify_scoped_stamp.py`; `tests/stamp_fixture.py`; the fixture of T003):
- e1 after a green `make verify` on `slice/a`, `make verify-scoped` prints verify-stamp's `REUSE_LINE`, starts no check
  (the stand-in log is unchanged), exits 0 *(fails today: T003's body runs `make verify`, whose own reuse prints the line
  but after the target's header line — the example reads the exact lines: **verify-scoped itself** has compared the key and
  printed `REUSE_LINE` before any `make verify` line)*.
- e2 an edit after it: a scoped selection runs (so far the full gate, as T003 left it) and the stamp file is unchanged,
  bytes and `mtime`; e3 a scoped run that fails leaves no stamp written; e4 `VERIFY_FORCE=1` after a green run: the
  forced full gate, not the reuse line; e5 the key is built with the same tools and the same `--environment`s as
  `verify-stamp.py` would (one example per `--environment` a project records).

**GREEN** — `verify-scoped.py` builds verify-stamp's key through its own functions (`python3 -B` import by path, never a
copy of its logic) and compares it with the stamp before reading any change; equal prints `REUSE_LINE` and exits 0; the
script never writes, removes or refreshes a stamp.

**REFACTOR:** the import of `verify-stamp.py` is one helper `trunk_module()`-style, shared with T003's borders.

**Verify:** `make test TESTS="test_verify_scoped_stamp test_verify_scoped_borders test_verify_stamp_reuse test_verify_stamp_two_runs"`,
then `make lint typecheck check-structure`. Commit by path; level line as above.

**Files:** `assets/toolkit/scripts/verify-scoped.py`, `tests/test_verify_scoped_stamp.py` (new).

### T005 — [P] [US2] A full green run on a slice branch leaves the baseline; any full run removes it (R7, first half · AC-S06-9)

- [x] **Rule R7, the writing half** (the comparison is T010). Needs T002 only for the fragment's existence; the manifest
  is disjoint from T003/T004. **Edits `assets/toolkit/scripts/verify-stamp.py`, which the root `Makefile` runs as the
  factory's own stamp**: run every `test_verify_stamp_*` suite and say so. The stamp's and the `verify` rule's bytes do
  not change (AC-S06-14).

**RED** (new `tests/test_verify_scoped_baseline.py`; `tests/stamp_fixture.py`; read the file under
`<git-dir>/slipwai/verify-baseline-<project>.json`):
- e1 a green `make verify` on `slice/a` writes the baseline beside the stamp: `branch`, `tools` equal to the stamp's
  `tools` exactly, `variables` holding the hex SHA-256 of `variable_record(name)` for every name in `VARIABLES`, never a
  value, unset distinct from empty *(fails today: no file)*.
- e2 a failing `make verify` leaves **no** baseline, and removes the one a previous green run left (`begin_full_run`);
  e3 a green run under `-i`, `-n`, `-t`, `-q` or `RATCHET_TIGHTEN` writes none and, where it is a full run that begins,
  removes it; e4 the ratchet path of `reuse` removes it; e5 off a slice branch (trunk, `feature/x`, detached, CI) none is
  written; e6 a baseline is written only when the stamp is: the key moved during the run, no baseline; e7 a scoped run
  (T003/T004's script) never writes one — **hold, teeth: make the script call `record`**.
- e8 the stamp file and the pending note are byte for byte what they were (every `test_verify_stamp_*` stays green).

**GREEN** — `verify-stamp.py`: `baseline_path()`, `variable_digests()`, `write_baseline()` called by `record()` right
after the stamp is written on a `slice/<id>` branch (written with `write_file`: temporary file, rename); the baseline
removed in `begin_full_run()` and on the ratchet path of `reuse()`; nothing else changes (its split is S32's).

**REFACTOR:** none expected.

**Verify:** `make test TESTS="test_verify_scoped_baseline test_verify_stamp_working test_verify_stamp_runs test_verify_stamp_reuse test_verify_stamp_file test_verify_stamp_stored test_verify_stamp_tools test_verify_stamp_lists test_verify_stamp_key test_verify_stamp_ships test_verify_stamp_pinned"`
and the *every suite that reads a generated gate* command, then `make lint typecheck check-structure`. Commit by path;
level line as above (this is an `assets/` change).

**Files:** `assets/toolkit/scripts/verify-stamp.py`, `tests/test_verify_scoped_baseline.py` (new).

### T006 — [US2] The record prints as JSON (R10 · AC-S06-13, AC-S06-6's table half)

- [x] **Rule R10.** Needs T002 (units in the make database) and T003 (the script). Obligations in the record are T012's
  (R10 e2 moves there). The table is the one place the factory's knowledge of what each check reads lives; a row the scan
  contradicts is corrected by widening it, never by narrowing below what the script reads (data-model, *The table*).

**RED** (new `tests/test_verify_scoped_record.py`; the TypeScript service + web starter, a Python two-service starter, a
Go one):
- e1 `python3 -B scripts/verify-scoped.py record` parses as JSON, `schema` is `1`, `sort_keys`, two-space indent; every
  unit with `gate`, `components`, `inputs` (`files` sorted, `/`-ended for a directory; `tools`; `variables`) or `null`,
  `claims`, `always`, `targets`; each deployable (`kind`, `path`, `family`, `api` for a web app); each contract with its
  consumers (`openapi:<svc>`, `package:<p>` where `packages/<p>/package.json` exists, `event:<E>` with `event`) — and
  lists `check-agents` with `"inputs": null` *(fails today: no `record` verb)*.
- e2 a record the script cannot build (no `verify-checks` in the make database, a unit `project.json` implies missing from
  it, a model it cannot read where an event edge is needed): stdout empty, one line on stderr, exit 1.
- e3 `packages/shared-go/` with no `package.json` is not an npm contract; a `packages/<p>/package.json` added in the
  working tree counts (base *or* now).
- e4 the **table held against the scripts** (reusing `tests/test_verify_stamp_lists.py`'s scan): every project-relative
  path literal a check script reads lies under one of that check's recorded inputs, or the check has no recorded inputs;
  a row the scan contradicts is a failure *(red where the first draft of the table misses a read, research R-8)*.
- e5 the table's own claims: `check-slice-scope` and `check-codegraph` have `"claims": false` and an `always` reason;
  `check-python` has `always`; the four method-file checks and any check a project added have `inputs: null`.

**GREEN** — `verify_scoped/table.py` (data-model *The table*), `verify_scoped/record.py` (the make database read through
`make -npq`, the join with `project.json`'s `deployables`, shared packages, the model via `check-slice-scope`'s
`load_model`, the JSON), `verify-scoped.py`'s `record [--make <make>] [--makefile <file>]`.

**REFACTOR:** table rows are data, one entry each, not branches.

**Verify:** `make test TESTS="test_verify_scoped_record test_verify_stamp_lists test_scoped_targets test_toolkit"`, then
`make lint typecheck check-structure`. Commit by path; level line as above.

**Files:** `assets/toolkit/scripts/verify_scoped/table.py` (new), `assets/toolkit/scripts/verify_scoped/record.py` (new),
`assets/toolkit/scripts/verify-scoped.py`, `tests/test_verify_scoped_record.py` (new).

### T007 — [US2] A change selects its readers and its consumers (R4 · AC-S06-2, -3, -4, -7)

- [x] **Rule R4.** Needs T004 and T006. First task that reads the changes: `verify_scoped/choose.py` (changed paths from
  `check-slice-scope`'s `changed_files(base)`, the selection, the reasons) and the first line-per-unit printing and one
  `$(MAKE)` call for the chosen units (plain; T011 adds the jobserver and the last line). Always-run checks are T008's,
  incomplete knowledge T009's, tools and variables T010's: until then a run names only what a changed path chose, and the
  tests below assert on those unit lines alone.

**RED** (new `tests/test_verify_scoped_choose.py` for e1, e4, e5 and `tests/test_verify_scoped_contracts.py` for e2, e3, e6;
the fixture, stand-in `npm`/`uv` logging argv):
- e1 TypeScript service + web, `apps/web/src/App.tsx` changed: `run  lint-web — apps/web/src/App.tsx changed`,
  `typecheck-web`, `test-web`, `check-styles`, `check-ux-gates`, `check-imports`, `check-migrations`, `check-model` run;
  `skip lint-service`, `typecheck-service`, `test-service`, `check-openapi`, `check-drawio`, `check-benchmark`,
  `check-decisions` — `none of its inputs changed`; the stand-in log shows exactly the chosen units ran *(fails today:
  T003 runs the full gate)*.
- e2 `apps/service/src/main.ts`: service's three, `check-openapi`, and `typecheck-web`, `test-web` as
  `consumes openapi:service (apps/service/src/main.ts)`; `lint-web` skipped; a service's committed OpenAPI document counts
  as a change under its path.
- e3 `packages/api-client/src/index.ts` (`packages/<p>/package.json` present): every npm-family deployable's typecheck and
  test run, `consumes package:api-client (…)`.
- e4 two Python services, one changed: all six units run, the other's named `shares one recipe with <unit>`; a Go or Java
  deployable's three run together (`shares a build directory with <unit>`).
- e5 a pinning file: `apps/service/uv.lock`, `.python-version`, `pyproject.toml`, root `.nvmrc`, `package-lock.json`,
  `go.mod`, `go.sum`, `pom.xml`, the Maven wrapper's properties → every unit that runs that family's tools, one example
  per file named in AC-S06-7.
- e6 an event edge billing→orders in the model (read at the base and in the working tree): a change in `apps/billing/`
  runs `typecheck-orders` and `test-orders`; an edge only in the working tree's model counts too.
- Class: every unit named once (the first that holds wins, in the data-model's order of reasons); changed paths taken in
  sorted order; a deletion and both sides of a rename count as changed.

**GREEN** — `choose.py`, the units' selection and reasons per data-model *How a unit is chosen*; `verify-scoped.py`
prints `run  <unit> — <reason>` / `skip <unit> — none of its inputs changed` and makes one
`"$(MAKE)" <chosen…> VERIFY_ORDER=1 --no-print-directory -f <makefile>` call.

**REFACTOR:** reasons are produced by one function in the order of the data-model.

**Verify:** `make test TESTS="test_verify_scoped_choose test_verify_scoped_contracts test_verify_scoped_record test_verify_scoped_borders test_verify_scoped_stamp"`,
then `make lint typecheck check-structure`. Commit by path; level line as above.

**Files:** `assets/toolkit/scripts/verify_scoped/choose.py` (new), `assets/toolkit/scripts/verify-scoped.py`,
`tests/test_verify_scoped_choose.py` (new), `tests/test_verify_scoped_contracts.py` (new).

### T008 — [US2] Checks that always run claim nothing (R6 · AC-S06-6)

- [x] **Rule R6.** Needs T007.

**RED** (new `tests/test_verify_scoped_always.py`):
- e1 a web-only change: `check-python`, `check-slice-scope`, `check-codegraph` (their *Always* reasons) and
  `check-agents`, `check-speckit`, `check-extensions`, `check-constitution` (`no recorded inputs`) are named `run`, and the
  service's units are still `skip` *(fails today: T007 names only what a path chose)*.
- e2 a project's own `check-licences` added to `verify-checks`: runs, `no recorded inputs`; it broadens nothing else (the
  service's units stay skipped).
- e3 `check-slice-scope` and `check-codegraph` claim no file: a changed path only they could read is **not** claimed (the
  assertion is the record's `claims: false`, and R5's behaviour on it is T009's).

**GREEN** — `choose.py` adds the always-run reasons from the record: `always` and `inputs: null` units run on every
scoped run with their reason, and never contribute a claim.

**REFACTOR:** none expected.

**Verify:** `make test TESTS="test_verify_scoped_always test_verify_scoped_choose test_verify_scoped_record"`, then
`make lint typecheck check-structure`. Commit by path; level line as above.

**Files:** `assets/toolkit/scripts/verify_scoped/choose.py`, `tests/test_verify_scoped_always.py` (new).

### T009 — [US2] What cannot be established runs the full gate (R5 · AC-S06-5)

- [x] **Rule R5.** Needs T008.

**RED** (new `tests/test_verify_scoped_incomplete.py`):
- e1 `README.md` changed: one line `dependency knowledge was incomplete for README.md — no deployable, contract or check
  claims it`, then the full gate (`verify-scoped: the full gate runs, as \`make verify\` — …`) *(fails today)*.
- e2 `project.json` and `scripts/check-imports.py` changed: two lines (*it is project.json*, *it is a gate script under
  scripts/*), one full gate; `Makefile`, `GNUmakefile`, `makefile` and `scripts/verify-scoped.py` and its modules count
  (`is_gate_script`).
- e3 a deployable named `integration`: one line saying its units are missing (T002 e6's consequence), full gate.
- e4 `packages/shared-go/x.go` (no `package.json`): unclaimed, full gate; a record the script cannot build (T006 e2): the
  line names why, then the full gate; a model it cannot read when an event edge is needed: the same.
- e5 every unclaimed path gets its own line and there is **one** full gate; exit status is `make verify`'s.

**GREEN** — `choose.py`/`verify-scoped.py`: unclaimed paths, gate files and an unbuildable record broaden with their lines,
as data-model *What a run prints*.

**REFACTOR:** the broadening reasons share one printer with the border lines.

**Verify:** `make test TESTS="test_verify_scoped_incomplete test_verify_scoped_always test_verify_scoped_choose test_verify_scoped_borders"`,
then `make lint typecheck check-structure`. Commit by path; level line as above.

**Files:** `assets/toolkit/scripts/verify_scoped/choose.py`, `assets/toolkit/scripts/verify-scoped.py`,
`tests/test_verify_scoped_incomplete.py` (new).

### T010 — [US2] Tools and variables are compared with the baseline (R7, second half · AC-S06-8, -9)

- [x] **Rule R7, the comparison.** Needs T005 (the baseline) and T009.

**RED** (new `tests/test_verify_scoped_compare.py`; a stand-in `node` whose `--version` the test sets, a baseline written
through a green `make verify` of T005):
- e1 `node` answering `v20.11.0` at the baseline then `v22.1.0`: npm-family units and `check-ux-gates`, `check-drawio` run,
  `test-service` named `node answers differently from the baseline`; unchanged: skipped *(fails today)*.
- e2 `UX_GATES_SINCE` set, then unset, then given another value: `check-ux-gates` runs, `UX_GATES_SINCE differs from the
  baseline`; both as at the baseline: skipped; set-to-empty differs from unset.
- e3 `UX_GATES_JOBS=8` (and the job count in `MAKEFLAGS`): nothing selected.
- e4 no baseline, a baseline from `slice/b` on `slice/a`, one that does not parse, or a tool that does not answer: one
  line `no usable baseline (…) — every check that reads a tool or a variable runs`, and, as every reader is every unit, the
  run is `make verify` (which then writes the baseline: T005).
- e5 a scoped run never writes the baseline (hold with teeth: T005's e7).

**GREEN** — `choose.py` asks the same tools once through `verify-stamp.py`'s `machine_tools` and compares with the
baseline's `tools` and `variables` digests; the line is printed once.

**REFACTOR:** none expected.

**Verify:** `make test TESTS="test_verify_scoped_compare test_verify_scoped_baseline test_verify_scoped_choose test_verify_scoped_incomplete test_verify_stamp_tools"`,
then `make lint typecheck check-structure`. Commit by path; level line as above.

**Files:** `assets/toolkit/scripts/verify_scoped/choose.py`, `assets/toolkit/scripts/verify-scoped.py`,
`tests/test_verify_scoped_compare.py` (new).

### T011 — [US2] Every unit named once, in one make call that keeps the jobserver (R9 · AC-S06-12)

- [x] **Rule R9.** Needs T010.

**RED** (new `tests/test_verify_scoped_run.py`):
- e1 `make -j2 verify-scoped` with two stand-in checks that each wait (bounded, by a marker file and a timeout) for the
  other: both start before either ends *(fails today: T007's call loses the descriptors, so the sub-make says
  `jobserver unavailable: using -j1` and the stand-ins time out)*.
- e2 a failing `test-web`: make's `*** [...test-web]` line is printed, the last line says `the scoped gate did not pass —
  each failed check is named above on a line carrying ***`, the exit status is non-zero and the sub-make's.
- e3 a passing run's last line is `<n> run, <m> skipped, compared with \`main\` at <short>; passed` and the counts equal
  the named lines.
- e4 every unit is named exactly once.

**GREEN** — the single call is `"$(MAKE)" $(VERIFY_GROUP) --no-print-directory -f <makefile> <units…> VERIFY_ORDER=1`
launched with `close_fds=False` (research R-5); the closing line and its counts; the sub-make's status.

**REFACTOR:** none expected.

**Verify:** `make test TESTS="test_verify_scoped_run test_verify_scoped_choose test_verify_scoped_compare test_parallel_gate_run"`,
then `make lint typecheck check-structure`. Commit by path; level line as above.

**Files:** `assets/toolkit/scripts/verify-scoped.py`, `tests/test_verify_scoped_run.py` (new).

### T012 — [US2] Obligations a person declares (R8 · AC-S06-11, R10 e2)

- [x] **Rule R8.** Needs T011. Also the record's `obligations` array (R10 e2).

**RED** (new `tests/test_verify_scoped_obligations.py`; `project.json` committed on `main`, branch rebased):
- e1 `{"name": "checkout", "components": ["orders","billing"], "checks": ["test-orders","test-billing"]}` and a change in
  `apps/orders/`: `test-billing` runs, `obligation checkout (…)`; the record's `obligations` lists it, checks sorted
  *(fails today)*.
- e2 `"checks": ["test-nope"]`: a line naming entry 1, `checkout` and the check, then the full gate; e3 `"obligations":
  {}`, a name used twice, fewer than two distinct components, a component not among `deployables`, `verification` not an
  object: each one line naming the entry by position and name, then `make verify`; a gate name (`test`) means all its
  units; other keys in an entry are ignored.
- e4 missing `verification` or `verification` without `obligations`: no obligation, no line; an obligation read **at the
  base** (a branch that changes `project.json` is T009's full gate).
- e5 `metadata()` never writes the key: a generated project's `project.json` has no `verification` (hold; teeth: write it).

**GREEN** — `record.py` parses and validates the key; `choose.py` selects through it (reason order 3).

**REFACTOR:** none expected.

**Verify:** `make test TESTS="test_verify_scoped_obligations test_verify_scoped_record test_verify_scoped_choose test_verify_scoped_incomplete"`,
then `make lint typecheck check-structure`. Commit by path; level line as above.

**Files:** `assets/toolkit/scripts/verify_scoped/record.py`, `assets/toolkit/scripts/verify_scoped/choose.py`,
`tests/test_verify_scoped_obligations.py` (new).

### T013 — [P] [US2] An adopted repository runs its full gate and says it has no record (R12 · AC-S06-16)

- [x] **Rule R12.** Needs T002/T003 for `scoped_section`; disjoint by manifest from the script chain T004–T012, but it
  shares `scoped_targets.py` with T002/T003 (already committed) and with T015. Follow *the Makefile-recipe search*.

**RED** (new `tests/test_scoped_adopted.py`; an adopted fixture as `tests/test_parallel_gate_adopted.py` makes one):
- e1 `make -f delivery/Makefile verify-scoped` in an adopted fixture: `this layout has no verification-dependency record
  yet`, then the full gate's output and exit status *(fails today: no target)*; `gate.stamped()` false for a wrapped
  application and for a moved layout both reach it.
- e2 the adopted `GATE` and `SERIAL` stay pinned and `.NOTPARALLEL` follows where the file is the only makefile
  (`adopted_targets.py`, unedited); the rule follows `ratchet-tighten`'s `$(MAKE){layout.make_flag}` convention.
- e3 **hold**: an adopted repository's `verify` rule bytes are unchanged (teeth: edit one).

**GREEN** — `scoped_section` returns, where the gate is not the stamped one, the single-line target.

**REFACTOR:** none expected.

**Verify:** `make test TESTS="test_scoped_adopted test_scoped_targets test_parallel_gate_adopted test_adopt test_adopted_manifest"`
and the every-gate-suite command, then `make lint typecheck check-structure`. Commit by path; level line as above.

**Files:** `src/slipwai/project/scoped_targets.py`, `tests/test_scoped_adopted.py` (new).

### T014 — [P] [US2] The ladder, the settings, the templates and the briefs say the scoped gate (R11 · AC-S06-15, D123, D124)

- [x] **Rule R11.** Needs only that `make verify-scoped` is a target's name; disjoint from the script chain and from T013.
  Every other word in each file stays as it is (D123).

**RED** (new `tests/test_scoped_ladder.py`; generated projects of both profiles):
- e1 a generated `commands/drive.md` says *start the slice from a green `make verify-scoped`* and carries `make
  verify-scoped` before the first push; Phase 4 and the merge root keep `make verify`; `concurrent_slices()`'s pre-push
  gate is `{layout.make} verify-scoped` and its Phase 4 `verify` *(fails today)*; `tests/test_commit_boundaries.py:33`'s
  phrase is still absent.
- e2 `.claude/settings.json` lists `Bash(make verify-scoped)` beside `Bash(make verify)`.
- e3 both generated constitution templates (standard and event-modelling) carry D123's principle V sentence word for word:
  *"The branch's scoped gate MUST be green immediately before that first implementation push: it runs every check whose
  inputs changed since the branch last passed the full gate, and it is the full gate wherever it cannot tell. The full
  gate MUST be green at the merge root and in CI before anything lands on trunk."*, no longer *The whole suite MUST be green
  immediately before that first implementation push*, and still the phrase *immediately before that first implementation
  push*; the `planning` skill carries D123 item 2's wording and keeps *After demo acceptance*; the implement and converge
  briefs carry items 3 and 4.
- e4 no ladder line types `-j` (D124): `commands/drive.md`, the concurrent-slices ladder, the briefs and the settings,
  searched for `make -j` and `-j` as a word.
- Class: both profiles, a stamped and an adopted layout (an adopted layout says `delivery/Makefile` through
  `{layout.make}`).

**GREEN** — reword in place: `commands.py` ~179 and ~190 (no line added), `parallel_slices.py` ~127 (Phase 4 ~134
unchanged), `agent_settings.py` (`"make verify-scoped"` beside `"make verify"`), `agents.py` implement brief ~135–136 and
converge brief ~189–190, the two `constitution-template.md` files, `assets/toolkit/skills/planning/SKILL.md` ~221. This
repository's own `delivery/skills/planning/SKILL.md` is in `delivery/.written`: **not edited** (`slipwai migrate` carries
it).

**REFACTOR:** none expected.

**Verify:** `make test TESTS="test_scoped_ladder test_commit_boundaries test_commands test_agent_settings test_parallel_slices test_constitution test_toolkit"`
(any of these names that do not exist are dropped, and `grep -rln "whole suite MUST\|full gate\|verify-scoped" tests` lists
the others to add), then `make lint typecheck check-structure`. Commit by path; level line as above.

**Files:** `src/slipwai/project/commands.py`, `src/slipwai/project/parallel_slices.py`,
`src/slipwai/project/agent_settings.py`, `src/slipwai/project/agents.py`,
`assets/profiles/standard/.specify/presets/standard/templates/constitution-template.md`,
`assets/profiles/event-modelling/.specify/presets/event-modelling/templates/constitution-template.md`,
`assets/toolkit/skills/planning/SKILL.md`, `tests/test_scoped_ladder.py` (new), and the existing test a hit above names
(`tests/test_commands.py`, `tests/test_commit_boundaries.py`) only where it pins words this task replaces.

### T015 — [US2] What a project already made gets, and the words (R13 · AC-S06-17, -18, D123 item 5, D124 item 3)

- [x] **Rule R13.** Needs T012 and T013 (the page and the fragment describe the whole), and T014 (the quoted sentence).
  Completes `changelog.d/scoped-gate.md`.

**RED** (new `tests/test_scoped_page.py` for the page, `tests/test_scoped_migrate.py` for migrate and the fragment):
- e1 a project generated at the last release (a `newer_factory`-style fixture, as `tests/test_ci_fetch_migrate.made_before_the_slice`),
  then `slipwai migrate` with this checkout: `make help`'s project has `verify-scoped` and the per-deployable targets, the
  scripts arrive, `project.json` has **no** `verification` key (AC-S06-17) *(fails today)*.
- e2 `changelog.d/scoped-gate.md`: first line `MINOR`; exactly one paragraph beginning `**Catch-up.**` that, read alone,
  names `make verify-scoped`, says the merge root and CI still run `make verify`, and names `verification.obligations`; it
  then says `slipwai migrate` never touches a ratified constitution and quotes D123's template sentence **word for word,
  equal to the sentence in the constitution template** (the test reads both) and says nothing breaks if left alone.
- e3 a stamped project's `docs/gates.md` carries the scoped paragraph: where it scopes (a `slice/<id>` branch with a usable
  base, outside CI), where it is the full gate, what broadens it, the baseline (beside the stamp, written by a green full
  run, removed by a full run), the obligations key with its default (none) and one sentence on when to declare one, and
  that `make -j verify-scoped` runs the chosen checks at once as `make -j verify` does (D124); an adopted project's page
  has the one sentence, and no word about a stamp (`tests/test_verify_stamp_page.py`'s adopted holds stand).
- e4 the fragment names AC-S06-19's measurement where T019 will write it (the host writes the figures, not this task).

**GREEN** — `SCOPED_PAGE` and `ADOPTED_SCOPED_SENTENCE` in `scoped_targets.py`; `docs.py` takes them in at most two
lines (331 → ≤ 333); the fragment completed.

**REFACTOR:** none expected.

**Verify:** `make test TESTS="test_scoped_page test_scoped_migrate test_gates test_verify_stamp_page test_docs_index test_render_docs test_migrate test_replay test_adopt test_changelog"`,
then `make lint typecheck check-structure`; `git diff --stat` shows `VERSION` unchanged. Commit by path; level line as
above.

**Files:** `src/slipwai/project/scoped_targets.py`, `src/slipwai/project/docs.py`, `changelog.d/scoped-gate.md`,
`tests/test_scoped_page.py` (new), `tests/test_scoped_migrate.py` (new), `tests/test_verify_stamp_page.py` (only if a hold
names the new text).

---

## Phase 2: Host closing tasks

### T016 — Every suite that reads a generated gate, once, before the gates (host task)

- [x] **Host task; no story.** After T002–T015 are committed: run `make test TESTS="<every name>"` over
  `ls tests | grep -E '^test_(verify_stamp|parallel_gate|model_|gate_)'` plus `test_matrix test_commands
  test_commit_boundaries test_toolkit test_gates test_docs_index test_render_docs test_replay test_migrate test_adopt
  test_changelog test_xdist_mark test_xdist_gate test_xdist_plugin test_xdist_carry test_xdist_page` and every
  `test_scoped_*` and `test_verify_scoped_*`, then `make lint typecheck check-structure`. A suite that fails is fixed in
  the owning task's files as a new task under *Phase 3* (a test pinning old text is amended in tests only, and named),
  never skipped. Confirm the diff touches nothing under `delivery/`, `tools/`, the root `Makefile` or CI, not `VERSION`,
  and that `make starters`'s `build/` differs from T001's only by the suffix, the scripts, `verify-stamp.py`, the page,
  the settings line and the ladder text.

**T016 result (host, iteration 22):** 705 tests OK (1 skipped: `test_changelog`'s release-tag hold, no tag fetched here, older than this slice) at `c1f2716` with every gate-reading suite, the scoped and xdist suites; `make lint typecheck check-structure` green; nothing under `delivery/`, `tools/`, the root `Makefile`, CI or `VERSION` changed. `make starters` differs from T001's copy in exactly: `Makefile`, `scripts/verify-scoped.py`, `scripts/verify_scoped/`, `scripts/verify-stamp.py`, `docs/gates.md`, `.claude/settings.json`, `commands/drive.md`, `agents/drive-implement.md`, `agents/drive-converge.md`, `skills/planning/SKILL.md` and the two constitution templates — every one the plan names.

### T017 — Converge, two passes (host task)

- [ ] `drive-converge` over the slice's diff, pass 1 then pass 2, at the loop's bound; every finding appends a task under
  *Phase 3*, and the verdict goes under `## Convergence`. The passes read the generated `verify-scoped` of a TypeScript +
  web starter and a two-service Python starter under the real `npm` and `uv`, on a `slice/S1` branch, with a README edit,
  a web-only edit, a `node` that changes version, an obligation declared and a bad one.

### T018 — After-converge gaps (host task)

- [ ] `drive-gaps` traces AC-S06-1 … AC-S06-19 over the diff; each gap is answered by a decision entry and, where it
  changes code, a task appended under *Phase 3*.

### T019 — The demo, with the measurement (host task)

- [ ] The demo of [quickstart.md](quickstart.md) run as the actor with this checkout's `./slipwai`, every step. **R14 /
  AC-S06-19:** on `slice/S1` with only `apps/web/src/App.tsx` changed, `make verify-scoped` three times, then
  `VERIFY_FORCE=1 make verify` three times on the same tree (that run writes the stamp, so it is measured last); the
  medians, the commands, the CPU model and `nproc` go into the quickstart's table and `changelog.d/scoped-gate.md` (host
  edit). At the merge root, `make verify` on a Python starter still runs pytest with `-n auto --maxprocesses 4` (S05's
  tests, unedited). If the scoped median is not below the forced full gate's, stop and hand the result back.

---

## Phase 3: Findings appended by converge and gaps

*(Empty until T017/T018 append tasks here, in the shape of the Phase 1 tasks.)*

---

## Phase 4: After acceptance (host tasks)

### T020 — The adversary pass (host task)

- [ ] Per the trigger table in `delivery/skills/adversary`: `drive-adversary` over the seams this slice opens — the
  selection's inputs (a path with a newline, a symlink, a rename out of a deployable's path, a deleted file, a changed
  `project.json` at the base against the working tree), the baseline file (a directory, huge, invalid UTF-8, another
  branch's), `verification.obligations` (every malformed shape), a make database with a stand-in `verify-checks`, and
  the jobserver under `-j`. Confirmed findings become regression tests at the owning layer, appended under *Phase 3*.

### T021 — Mutation (host task)

- [ ] **N/A** unless `project.json` records a mutation command for this repository by now; it recorded none for any slice
  before this one, so said in the register row and owed to the cruise report, not pretended.

### T022 — Both full gates on the final tip (host task)

- [ ] On the tree after the last task above: `make test TESTS="test_toolkit test_utf8_io test_changelog"` first (the slice
  touches `assets/`), then `make verify`, then `CI=true GITHUB_ACTIONS=true make -f delivery/Makefile verify` **once**,
  both green (Principle XIV). Confirm `VERSION` is `1.6.0.dev0` and nothing under `tools/`, the root `Makefile`, CI or
  `delivery/` changed.

### T023 — Register row and benchmark close (host task)

- [ ] The slice's row in the register (`slices/README.md`) and `benchmark.json` closed, the after-acceptance commits
  riding in this slice's own pull request (`AGENTS.md`).

---

## Parallel opportunities

By manifest (each task's *Files* line):

| Task | Writes | Imports another task's file |
|---|---|---|
| T002 | `scoped_targets.py`, `makefile.py`, `native_commands.py`, `changelog.d/scoped-gate.md`, `tests/test_scoped_targets.py` | none |
| T003 | `verify-scoped.py`, `verify_scoped/__init__.py`, `scoped_targets.py`, `tests/scoped_fixture.py`, `tests/test_verify_scoped_borders.py` | T002's section |
| T004 | `verify-scoped.py`, `tests/test_verify_scoped_stamp.py` | `verify-stamp.py` (read), the fixture |
| T005 | `verify-stamp.py`, `tests/test_verify_scoped_baseline.py` | none |
| T006 | `verify_scoped/table.py`, `verify_scoped/record.py`, `verify-scoped.py`, `tests/test_verify_scoped_record.py` | T002's units |
| T007–T011 | `verify_scoped/choose.py`, `verify-scoped.py`, one new test file each | the one before |
| T012 | `record.py`, `choose.py`, `tests/test_verify_scoped_obligations.py` | T011 |
| T013 | `scoped_targets.py`, `tests/test_scoped_adopted.py` | T002/T003's section |
| T014 | `commands.py`, `parallel_slices.py`, `agent_settings.py`, `agents.py`, two templates, the planning skill, `tests/test_scoped_ladder.py` | none |
| T015 | `scoped_targets.py`, `docs.py`, `changelog.d/scoped-gate.md`, two new test files | T012–T014 |

- **The script chain is serial:** T003 → T004 → T006 → T007 → T008 → T009 → T010 → T011 → T012 each write
  `verify-scoped.py` and/or `choose.py`/`record.py`; two worktrees would conflict, so **never two of them at once**.
  Only T005, T013 and T014 are marked `[P]`: no other task has a manifest disjoint from its siblings.
- **May run together** (after T003 is committed, so the fixture and the target exist): **T005** (`verify-stamp.py` only —
  but T010 needs it, so it is committed before T010), **T013** (`scoped_targets.py` and its own test) and **T014** (the
  ladder texts and templates): three disjoint manifests beside the script chain, so up to **four** delegates at once
  (the chain's current task plus the three). T013 may also start right after T002/T003 and before T004.
- **May not:** T013 beside T002, T003 or T015 (`scoped_targets.py`); T014 beside T015's fragment edit — T014 does not
  touch the fragment, and T015 reads the template T014 writes, so T015 is after T014; T010 before T005; T015 before
  T012, T013, T014; any task beside T001, T016–T023.
- **Shared-tree caution.** T005 edits `assets/toolkit/scripts/verify-stamp.py`, which the root `Makefile` runs as this
  repository's own stamp and which every generated project in the other groups' tests copies: run each concurrent
  delegate in a worktree of its own off the commit that closes T003 (`isolation: worktree`), and the host commits by path
  in dependency order, resolving no conflict by hand — a conflict means a manifest overlap this table says there is none
  of.
- **Host tasks:** T001 first, alone; T016 runs alone after T015; T017–T023 follow in order.

## Design review

No screen in this slice

## Convergence

*(Written by the converge stage, at the end of this file, after Phase 4.)*

## Differences from plan.md

Written for the host to correct the plan; none changes a requirement or a decision.

1. **R7 is two tasks (T005, T010).** The baseline's writing is in `verify-stamp.py`, the comparison in the script; each
   has its own RED, and the writing half is disjoint from the script chain, which makes it `[P]`.
2. **R10 e2 (obligations in the record) moves to T012**, with R8, because it cannot be red before the key is parsed.
3. **The plan's six test modules are cut into more** (`test_verify_scoped_stamp`, `_always`, `_incomplete`, `_compare`,
   `_run`, `_obligations`, `_contracts`, `test_scoped_adopted`, `_page`, `_migrate`) so each stays under 350 lines; the
   plan's fixture helper `tests/scoped_fixture.py` lands in T003.
4. **The script is built in rule order, not file order**: T003 creates `verify-scoped.py` with R1's borders only, and until
   T007 a slice branch with a usable base runs `make verify`, so the target is correct at every commit.
5. **R14 is no task** (its examples are a hold over S05 and a measurement); it is T019's.
6. **No controls patch task.** The plan changes nothing under the root `Makefile`, `delivery/scripts/`, `tools/` or CI.
