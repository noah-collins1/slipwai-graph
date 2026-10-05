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

*Appended by T017, converge pass 1 (2026-10-05).* Each finding is a run of `make verify-scoped` that printed `passed`,
or skipped a check, where `make verify` on the same tree runs that check and it fails. Reproductions are probes over
`tests/scoped_fixture.ShapeCase` (the fixture's stand-in `npm`/`node`, the real `python3` and `make`), kept outside the
tree; each RED below restates one as an example.

### T024 — [US2] CRITICAL — A check's row is as wide as what the check walks and what its data names (R4, R10 e4 · AC-S06-2, -5, -6, -13)

- [x] **Finding.** Some rows in `table.py` are narrower than the paths their checks read. When another row claims
  the changed path, R5's safety net never fires, and the narrow check is skipped. Three checks are shown:
  `check-migrations` walks **every** `apps/*/` and `packages/*/` (`check-migrations.py` 16, 157), but its row is
  `{dep}`. `check-imports` walks every directory under `apps/` and `packages/` (`check-imports.py` 142, 284), but its
  row is `{dep}`, `{npm}`. `check-model` requires every path an implemented slice names in `gwt`, `code` (and a
  mockup's `at`) to exist (`event-model/check.py` 336–340, 376), and the documented `gwt` is under `specs/`
  (`docs/event-model/README.md` 72). Its row is `docs/event-model/`, `{dep}`. **Why the e4 hold did not catch it:**
  `tests/test_verify_scoped_record.covered()` counts a literal as covered when *any entry lies under it*
  (`entry.startswith(literal + "/")`). So `"packages"` is "covered" by `packages/api-client/`, which accepts a row
  narrower than the read, against the data-model's rule. The scan also reads only literals, never paths the model
  names. **Reproduced:**
  (a) In the TS service + web starter on `slice/S1` with a baseline, add `packages/api-client/migrations/202610051200_drop.sql`
  holding `ALTER TABLE orders DROP COLUMN status;`. The run says `skip check-migrations — none of its inputs changed`,
  then `13 run, 9 skipped, compared with \`main\` at …; passed` and exits 0. `python3 scripts/check-migrations.py` on
  the same tree exits 1 (*drops a column…*).
  (b) Commit to `main` an implemented slice with `gwt: specs/001-ordering/slices/S1.md` (`check-model: valid`). On the
  branch, `git rm` that file and add `S1-moved.md`. The run says `run check-decisions`/`check-benchmark —
  specs/…-moved.md changed`, then `skip check-model — none of its inputs changed`, then `passed`. Run directly,
  `check-model` exits 1: *S1: implemented slice has missing gwt evidence*.

**RED** (extend `tests/test_verify_scoped_record.py`; new `tests/test_verify_scoped_walks.py` if it nears 350):
- e1 (a) above as an example: `check-migrations` is `run — packages/api-client/migrations/… changed`. *(fails today)*
- e2 (b) above: `check-model` runs when a path the model names changes, at the base or in the working tree.
  *(fails today)*
- e3 `packages/shared/src/domain/x.ts` with no `package.json`, in a project where something else claims
  `packages/` (T027's case): `check-imports` runs. *(fails today under a target)*
- e4 the hold is made honest: `covered()` loses its `entry.startswith(literal + "/")` arm, so a directory literal is
  covered only by an entry at or above it. The scan also gains the walk roots, `ROOT / <literal>` and a `for area in
  (…)` tuple of literals, and is run red first against today's table. *(fails today on `check-migrations`,
  `check-imports`)*

**GREEN — the class, not the instance.** Hold **every** row of `CHECKS` against every way its script finds a path: a
literal, a walk root, a path read from `project.json`, and a path read from the model. Widen each row the sweep
contradicts: `check-migrations` → `apps/`, `packages/`; `check-imports` → `apps/`, `packages/`; `check-model` →
`docs/event-model/`, `{dep}`, plus every path the model at the base and in the working tree names (derived in
`record.py` from `check-slice-scope`'s `load_model`, or `specs/` if that is all the sweep can prove). Do the same for
`check-flags` and `check-deploy-role` under a target shape, and for `check-styles`/`check-ux-gates` over each web app's
`screens/` and `src/`. Run the e4 scan over every shape in `test_scoped_targets.SHAPES`, including a cloud shape. If a
row cannot be bounded, it becomes `inputs: null` (it always runs), never narrower.

**Verify:** `make test TESTS="test_verify_scoped_record test_verify_scoped_choose test_verify_scoped_contracts test_verify_scoped_incomplete test_verify_scoped_always"`
(plus the new module), then `make lint typecheck check-structure`. Level line: MINOR, already carried.

**Files:** `assets/toolkit/scripts/verify_scoped/table.py`, `assets/toolkit/scripts/verify_scoped/record.py`,
`tests/test_verify_scoped_record.py`, `tests/test_verify_scoped_walks.py` (new, if needed).

### T025 — [US2] CRITICAL — The recipe-sum guard: a check whose recipe is not the sum of its units runs whole (R3, R4 · AC-S06-2, -4; data-model *How a unit is chosen*, last paragraph)

- [x] **Finding.** The data-model specifies a recipe-sum guard: where a gate check's recipe lines (from the make database)
  are not exactly its units' and family targets' lines, the check runs whole under its gate name. **It is not
  built.** Nothing in `record.py` or `choose.py` compares the two. T002 e4 proves the sum only for the generated text,
  at generate time. A project owns its `Makefile` (Principle I), and a project that adds a line to `lint:` is the case
  the guard exists for. A `Makefile` change on the branch broadens (`it is the Makefile`), but once that change is on
  the trunk, every later slice branch skips the project's line. **Reproduced:** on `main` of the TS service + web
  starter, add `@! grep -rq FORBIDDEN apps/web/src` as a second line of `lint:` and commit. On `slice/S1` (baseline
  written), append `// FORBIDDEN` to `apps/web/src/App.tsx`. The run says `run lint-web — apps/web/src/App.tsx
  changed`, then `15 run, 7 skipped, …; passed`, and exits 0. `make lint` on the same tree exits 2 (`*** [Makefile:95:
  lint] Error 1`).

**RED** (new `tests/test_verify_scoped_sum.py`, on the fixture):
- e1 the reproduction above: `lint` runs whole with the reason `its recipe is not the sum of its per-deployable
  targets`, and the run fails. *(fails today)*
- e2 a prerequisite a project added to a gate check (`lint: lint-docs`, with `lint-docs` failing) is part of the sum:
  the same reason, and the run fails. *(fails today)*
- e3 a merged-recipe line *removed* (a unit runs a line `lint` no longer has): the same reason. *(fails today)*
- e4 **hold**, every generated shape in `test_scoped_targets.SHAPES` plus two-service: no check carries the reason.
  *(teeth: drop one unit line in `scoped_targets.py` and see e4 fail)*

**GREEN — the class.** `record.py` compares, for every gate in `verify-checks` that has units, the recipe lines and the
non-order-only prerequisites of the gate target against the union of its units' and family targets' lines and
prerequisites, in order, from the same `make -npq` database. On a mismatch the record marks the gate `whole: true` and
gives the reason. In `choose.py`, a chosen unit of a `whole` gate puts the gate's own name in the make call in place
of its units, and the line printed for each of its units carries the reason. The sweep covers all three gates, every
family (npm, Python, Go, Java), and a project-added prerequisite.

**Verify:** `make test TESTS="test_verify_scoped_sum test_verify_scoped_record test_verify_scoped_choose test_verify_scoped_run test_scoped_targets"`,
then `make lint typecheck check-structure`. Level line: MINOR, already carried.

**Files:** `assets/toolkit/scripts/verify_scoped/record.py`, `assets/toolkit/scripts/verify_scoped/choose.py`,
`assets/toolkit/scripts/verify-scoped.py`, `tests/test_verify_scoped_sum.py` (new).

### T026 — [US2] CRITICAL — Every part of the stamp's key is compared by the selection, the ignored files included (R4, R7 · AC-S06-5, -8, -9)

- [x] **Finding.** The stamp's key holds the ignored part: every file git ignores under the project, except
  `EXEMPT` (`verify-stamp.py` 42–48, 499). It holds it because a check reads those files: `.env` (Vite and Vitest
  load it from the app's root), `node_modules/.package-lock.json` (kept in the key on purpose, line 79), the UX kit
  under `tools/ux-gates/` and `skills/ui-ux-pro-max/` (ignored, run by `check-ux-gates`), and a new test file excluded
  by `.git/info/exclude`. The selection reads only `check-slice-scope.changed_files(base)`, which is `git diff` plus
  `ls-files --others --exclude-standard`, so ignored files are invisible to it. The baseline records tools and
  variables, not the ignored part. **Reproduced:** on `slice/S1` of the TS service + web starter with a baseline,
  write `apps/web/.env` and change `node_modules/.package-lock.json`. `git status --ignored` lists both. The run says
  `skip lint-web`, `skip typecheck-web`, `skip test-web`, `skip check-ux-gates — none of its inputs changed`, then
  `7 run, 15 skipped, …; passed`. `make verify` on the same tree finds the stamp's key moved and runs every check.

**RED** (new `tests/test_verify_scoped_ignored.py`):
- e1 the reproduction above: the run says the ignored part differs from the baseline, and is the full gate, or runs
  every check whose `{own}` holds the ignored path, whichever the host's decision picks (below). *(fails today)*
- e2 an ignored file under an `EXEMPT` entry (`.venv/`, `dist/`, `coverage/`) changes: nothing is selected.
  *(hold, teeth)*
- e3 the class: a test that lists `key_parts`' part names (`files`, `scripts`, `index`, `history`, `ignored`,
  `variables`, `tools`) and requires each to map to what the selection compares. A part with no mapping fails.
  *(fails today on `ignored`)*

**GREEN — the class.** Have `write_baseline` also record the stamp's `ignored` digest (and, if the decision
needs per-path selection, the per-path digests, never a name the constitution's persisted-data rule forbids). Have
`verify-scoped.py` compute it through `verify-stamp.py`'s own function, never a copy, and compare it. Before GREEN,
the host records in the decision log whether a moved ignored part broadens to the full gate (simplest; the stamp's
own choice) or selects by path. Either way, the sweep is e3: every part of the key is compared.

**Decided — D125 (a):** a moved ignored part is the full gate. The baseline gains one field, `ignored`, the stamp key's
`ignored` part from the same run (`key_parts`, never a copy; no path stored); `verify-scoped` computes the tree's the
same way and, where they differ, prints `the full gate runs, as \`make verify\` — a file git ignores differs from the
baseline` with the stamp's `git status --ignored` hint, then runs `make verify`. A baseline without `ignored` is
unusable. e1 is that line and the full gate. e3's mapping: `files`, `index` → changed paths; `scripts` → D117 rule 4;
`history` → the base and branch check; `tools`, `variables` → the baseline comparison; `ignored` → D125. data-model.md
and AC-S06-9 carry it.

**Verify:** `make test TESTS="test_verify_scoped_ignored test_verify_scoped_baseline test_verify_scoped_compare test_verify_stamp_pinned"`
and every `test_verify_stamp_*`, because `verify-stamp.py` is the root `Makefile`'s stamp. Then `make lint typecheck
check-structure`. Level line: MINOR, already carried.

**Files:** `assets/toolkit/scripts/verify-stamp.py`, `assets/toolkit/scripts/verify-scoped.py`,
`assets/toolkit/scripts/verify_scoped/choose.py`, `tests/test_verify_scoped_ignored.py` (new).

### T027 — [US2] HIGH — A claim means every reader of the path is chosen: `check-flags`' `packages/` (R5 · AC-S06-5)

- [x] **Finding.** A check's file inputs claim a path for R5. That is safe only if every unit reading the path is then
  chosen. `check-flags` (present under any target) claims all of `packages/`, so a change in a package without a
  `package.json` is no longer unclaimed, and nothing broadens. Examples: a Python path dependency, a
  `go.work` member, a shared migrations package. Only `check-flags` runs. The deployables that build the package,
  `check-imports` and `check-migrations` are skipped. **Reproduced:** in the `model-typescript-web-cloud` shape on
  `slice/S1`, change `packages/shared-py/shared/__init__.py` and add `packages/shared/migrations/202610051200_drop.sql`.
  The run says `run check-flags — packages/shared-py/shared/__init__.py changed`, skips every other check with inputs,
  and prints `8 run, 16 skipped, …; passed`. Without a target, the same paths broaden (T009 e4). T024 closes the
  `check-imports`/`check-migrations` half; this task closes the consumer half.

**RED** (in `tests/test_verify_scoped_incomplete.py`, or the new module of T024):
- e1 the reproduction under a target: `dependency knowledge was incomplete for packages/shared-py/… — no deployable
  or contract consumes it`, then the full gate. *(fails today)*
- e2 the same path without a target: unchanged (it broadens). *(hold)*

**GREEN — the class.** A path under `packages/<p>/` with no `package.json` is unknown unless a contract or deployable
consumes it, whatever a check's row claims. More generally, `claimed()` holds that only a deployable or a contract
can stand for its consumers, so a check row that is not a unit can make a path *chosen* but never *known* for the
units it does not name. Sweep every row whose files reach outside its own deployable (`check-flags`,
`check-imports`, `check-migrations`, `check-model`, `check-benchmark`, `check-decisions`, `check-ux-gates`) with one
example each, and leave every row whose claim covers only what it alone reads unchanged.

**Verify:** `make test TESTS="test_verify_scoped_incomplete test_verify_scoped_choose test_verify_scoped_always test_verify_scoped_contracts"`,
then `make lint typecheck check-structure`. Level line: MINOR, already carried.

**Files:** `assets/toolkit/scripts/verify_scoped/choose.py`, `assets/toolkit/scripts/verify_scoped/table.py`,
`tests/test_verify_scoped_incomplete.py`.

### T028 — [US2] MEDIUM — The words say what the comparison is (R11, R13 · AC-S06-15, -18; D123)

- [x] **Finding.** The gates page (`scoped_targets.SCOPED_PAGE`, line 41), both constitution templates (D123's
  sentence) and the fragment's **Catch-up.** say the scoped gate runs *every check whose inputs changed since the
  branch last passed the full gate*. The code compares changed **paths** with the trunk's merge base
  (`records.base_of`, `changed_files(base)`), and only **tools and variables** with the baseline that the last green
  full run left. The run's own last line says so: `compared with \`main\` at <short>`. The two differ after a rebase
  or a trunk merge, and they differ in what a reader may assume: the skipped checks are taken to pass because the
  **trunk** passed them, not because this branch did. That is a product sentence (D123), so it goes back to the host.
  Do not reword it here.

**RED** (`tests/test_scoped_page.py`, `tests/test_scoped_migrate.py`): the page, both templates and the Catch-up
paragraph name what paths are compared with and what tools and variables are compared with, in the words the host's
decision fixes *(fails today)*.

**Decided — D126 (a), with D125 applied (its item 2):** the behaviour stays; the words change. Both templates' D123
sentence becomes, word for word: *"The branch's scoped gate MUST be green immediately before that first implementation
push: it runs every check that reads a file changed since the trunk commit the branch is built on, or a tool, a
variable or an ignored file that differs from the branch's last green full gate, and it is the full gate wherever it
cannot tell; a check it skips is taken as passing because the trunk passed it. The full gate MUST be green at the merge
root and in CI before anything lands on trunk."* `SCOPED_PAGE`'s first sentence becomes D126 item 3's text with
*"Tools and variables"* read as *"Tools, variables and the files git ignores"*; the Catch-up quotes the new template
sentence word for word. Nothing else (the planning skill, briefs and ladder keep D123's words).

**GREEN — the class.** Every published place that describes the comparison takes the same words: the page, the
adopted sentence, both templates, the planning skill, the implement/converge briefs, the ladder and the fragment.
Sweep them with `grep -rn "since the branch last passed" src assets changelog.d`. If D123's sentence changes, the
decision log entry comes first.

**Verify:** `make test TESTS="test_scoped_page test_scoped_migrate test_scoped_ladder test_commit_boundaries test_changelog"`,
then `make lint typecheck check-structure`.

**Files:** `src/slipwai/project/scoped_targets.py`, the two `constitution-template.md` files,
`changelog.d/scoped-gate.md`, `tests/test_scoped_page.py`, `tests/test_scoped_migrate.py`, and
`specs/001-faster-slipwai/decisions.md` (host only).

### T029 — [US2] LOW — The tests claim what they hold: a migrate from the real last factory, a jobserver example with teeth (R9, R13 · AC-S06-12, -17)

- [x] **Finding.** (1) `tests/test_scoped_migrate.made_before_the_slice` builds its "made before" project by
  stripping the scoped section from a project this checkout generated. That project still has the stamp, the new
  `verify-stamp.py` and today's every other line, which is not what any earlier factory made. A real migrate passes:
  `git archive 58a9aed` → `slipwai generate product --profile event-modelling --backend typescript --frontend
  react-vite`, then this checkout's `slipwai migrate` gives one commit, `verify-scoped` and `lint-web` in the `Makefile`,
  `scripts/verify_scoped/` complete, and the Catch-up paragraph in `.slipwai/catch-up.md`. But no test holds that.
  (2) `tests/test_verify_scoped_run.py`'s fifo-jobserver example passes on GNU Make 4.4.1 whatever `close_fds` is,
  so it is a hold with no teeth. Only the `--jobserver-style=pipe` example discriminates.

**RED/GREEN:** (1) the migrate example generates with the factory at the commit before the slice, or at the last
release tag where one is fetched, through `git archive` into a temporary directory. It covers the TS + web shape and
the two-Python shape, and asserts the same four facts. (2) The fifo example is renamed and documented as a hold over
make's own fifo jobserver, or dropped, so the module claims teeth only where it has them. The sweep covers every
`test_verify_scoped_*`/`test_scoped_*` example named as a hold: each is seen to fail under the mutation its docstring
names.

**Verify:** `make test TESTS="test_scoped_migrate test_verify_scoped_run"`, then `make lint typecheck check-structure`.
Tests only: reaches no user.

**Files:** `tests/test_scoped_migrate.py`, `tests/test_verify_scoped_run.py`.

*Appended by T017, converge pass 2 (2026-10-05), over `58a9aed..c3694ae`.* T024–T029's reproductions all now hold;
what follows is what pass 2 found still open.

### T030 — [US2] CRITICAL — Every rule `make verify` reaches is read, not only the three gates with units (R3, R4, R5 · AC-S06-2, -4, -5; data-model *How a unit is chosen*, last paragraph)

- [x] **Finding.** T025 closed its instance: a line or a normal prerequisite a project gives `lint`, `typecheck` or
  `test`. The class is wider. *The selection trusts a rule's text that the project owns and that nothing compares*
  (Principle I: the project owns its `Makefile`; a `Makefile` change broadens only while it is on the branch). Four
  rules `make verify` reaches are still taken on trust. (1) **A named check's recipe and prerequisites.** `table.py`'s
  row says what the factory's recipe reads. A line or a prerequisite a project adds to `check-drawio`,
  `check-decisions` or any row in `CHECKS` is never read. (2) **Order-only prerequisites.** `record.database` drops
  everything after `|` (`record.py` 76), but make still builds an order-only prerequisite, so `lint: | lint-docs` runs
  `lint-docs` under `make lint` and is outside the sum. (3) **`verify`'s own prerequisites.** (4) **`verify-checks`'
  own recipe lines.** The scoped run names only `verify-checks`' prerequisites. **Reproduced** in the TS service + web
  starter. On `main`, commit one Makefile edit; on `slice/S1` with a baseline, append `// FORBIDDEN` to
  `apps/web/src/App.tsx`. Each of the four edits gives `run  lint-web — apps/web/src/App.tsx changed`, then
  `15 run, 7 skipped, compared with \`main\` at …; passed`, exit 0:
  (a) `\t@! grep -rq FORBIDDEN apps/web/src` as a second line of `check-drawio:` (`skip check-drawio — none of its
  inputs changed`);
  (b) `lint-docs:` with that line, and `check-decisions: lint-docs` (`skip check-decisions`; `make check-decisions`
  exits 2, `*** [Makefile:263: lint-docs] Error 1`);
  (c) the same `lint-docs`, and `lint: | lint-docs` (`make lint` exits 2 at `lint-docs`);
  (d) the same `lint-docs`, and `verify: lint-docs`;
  (e) the grep line before `@echo 'verify: all gates passed'` in `verify-checks:`.

**RED** (extend `tests/test_verify_scoped_sum.py`, or new `tests/test_verify_scoped_rules.py` if it nears 350):
- e1 (a): `check-drawio` runs, with a reason saying its recipe is not the one its row describes, and the run fails.
  *(fails today)*
- e2 (b): the same for a prerequisite a project gave a named check. *(fails today)*
- e3 (c): an order-only prerequisite of a gate with units is part of the sum, so `lint` runs whole. *(fails today)*
- e4 (d) and (e): a prerequisite of `verify` or a recipe line of `verify-checks` that the factory did not write makes
  the run the full gate, with its reason. *(fails today)*
- e5 **hold**: every shape in `test_scoped_targets.SHAPES` plus two-service and a cloud shape. No named check, no
  `verify` and no `verify-checks` carries the new reason. *(teeth: add one line to one generated check's recipe in
  `makefile.py` and see e5 fail)*

**GREEN — the class.** No rule that `make verify` reaches may be skipped on the strength of text the selection never
compared. Parse order-only prerequisites (make builds them) for units, family targets and gates alike. For each
named check, compare its recipe lines and every prerequisite with what its row stands for. Where they differ, the
check gets `inputs: null` with its reason, so it always runs and claims nothing. It never gets a narrower row. Give
`verify` and `verify-checks` the same comparison, where a difference is the full gate. The factory's text for each
rule must come from where `makefile.py` writes it, or from a property the row records (for example, the one script
each line must call). It must never be a second spelling that drifts. If that needs a product choice, the host
records the choice in the decision log first. The sweep is every rule reachable from `verify` in the make database:
each one is held by the sum (T025), by this comparison, or is an always-run check. A test walks the database and
fails on a reachable rule held by none of the three.

**Verify:** `make test TESTS="test_verify_scoped_sum test_verify_scoped_record test_verify_scoped_choose test_verify_scoped_run test_scoped_targets test_verify_scoped_contracts"`
(plus the new module), then `make lint typecheck check-structure`. Level line: MINOR, already carried.

**Decided — D127 (a), ADR 0005 at Proposed.** The generator writes `scripts/verify_scoped/rules.json` (schema 1:
`rules` and `variables`, target or variable name → sha256; stamped layouts only) from the same `makefile()` output,
added beside `"Makefile"` in `scaffold.project_files`, so `generate`, `add-service` and `migrate` carry the two
together. Fingerprinted: every rule reachable from `verify` through normal **and order-only** prerequisites plus
every rule the scoped section writes — one digest over canonical JSON `{"needs", "order_only", "recipe"}`
(unexpanded lines, repeated rule lines merged as make merges them, `ifeq ($(origin X),command line)` read as false) —
and every variable the factory's Makefile assigns (flavour and value as written). The canonical form lives once, in
a new stdlib toolkit module `scripts/verify_scoped/rules.py` with two readers, `from_text` (the Makefile text, used by
the factory through `importlib.util.spec_from_file_location`) and `from_database` (`record.database`'s output, which
now keeps order-only prerequisites and each variable's origin). The charge rule (D127 item 4): a difference reached by
exactly one named check → that check `inputs: null`, `claims: false`, reason `its rule is not the one the factory
wrote (scripts/verify_scoped/rules.json)`; by exactly one unit gate (or its units/family targets) → that gate whole
(T025's `whole`), same reason; anything else (`verify`, `verify-checks`, a prerequisite of `verify` outside
`verify-checks`, anything two or more members reach — `check-python`, `sync`, `build-packages`, `SHELL` — or none) →
the full gate, `the Makefile's \`<target>\` rule is not the one the factory wrote` (or `variable \`<name>\``); a
missing, unreadable or unknown-schema file → the full gate, *dependency knowledge was incomplete*; a fingerprinted
rule the database lacks → a difference in `verify-checks`. Environment- and command-line-origin variables are the
baseline's (D116), not compared here. **e5 becomes:** for every shape in `test_scoped_targets.SHAPES`, plus two-service
and a cloud shape, `from_text(makefile(...))` equals `from_database(make -npq)` and no check carries the new reason;
**teeth:** make one reader stop merging repeated rule lines, or drop `|` handling, and see e5 fail. The sweep (item 7):
a test walks the database and fails on a reachable rule held by none of the sum, this comparison, or an always-run
check. The fragment's **Catch-up.** gains D127 item 6's sentence word for word.

**Files:** `assets/toolkit/scripts/verify_scoped/rules.py` (new), `assets/toolkit/scripts/verify_scoped/record.py`,
`assets/toolkit/scripts/verify_scoped/choose.py`, `assets/toolkit/scripts/verify_scoped/table.py`,
`assets/toolkit/scripts/verify-scoped.py`, `src/slipwai/scaffold.py`, `src/slipwai/project/makefile.py` or
`src/slipwai/project/scoped_targets.py` (the factory's call of `from_text`), `changelog.d/scoped-gate.md` (the one
Catch-up sentence), `tests/test_verify_scoped_sum.py`, `tests/test_verify_scoped_rules.py` (new), and an existing test
that lists a generated project's files only where the new file changes it (named).

### T031 — [US2] MEDIUM — The record's contract says what the record now holds (R10 · AC-S06-13; ADR 0004, data-model *The printed record*)

- [x] **Finding.** ADR 0004 says the printed shape is the contract its readers use (S07, S34–S36). Three things the
  record now does are written nowhere in that contract:
  (1) T025 added a `whole: true` key to units (`record.py` 215). In that case `targets` names the gate, not the unit.
  Neither ADR 0004's shape (lines 60–80) nor data-model.md's (lines 126–169) names the key.
  (2) T027 changed what `claims: true` means. A row that is not a unit no longer makes a path under `apps/` or
  `packages/` known (`choose.claimed`). The contract still says only that `claims: false` marks a check whose files
  never make a path known. So a reader that rebuilds R5 from the record broadens less than the script does.
  (3) data-model.md's table (lines 55–76) still gives the rows as they were before T024: `check-imports`
  `<dep>/, packages/<p>/`, `check-migrations` `<dep>/`, `check-flags` without `apps/`, `check-model` without the
  paths the model names, and `check-benchmark` with `.specify/integration.json` alone.
  An added key is MINOR under the ADR's own rule (line 82), so nothing breaks today. But a contract that leaves out
  what changes a reader's answer is the drift Principle VIII guards against.

**RED** (`tests/test_verify_scoped_contracts.py`): every key a record of every shape emits, at every depth, is named in
data-model.md's *printed record* section. *(fails today on `whole`)*. Each row of data-model.md's table equals
`table.py`'s row for that check. *(fails today on the five rows above)*

**GREEN — the class.** One test holds the published shape against the emitted one, keys and rows, so the next change
to the record changes its contract in the same commit. Bring data-model.md up to date, and have the host bring
ADR 0004's *printed shape* up to date too: `whole`, and what `claims` means under `apps/` and `packages/`. The ADR
is Proposed, so its wording is the host's.

**Verify:** `make test TESTS="test_verify_scoped_contracts test_verify_scoped_record"`, then `make lint typecheck check-structure`.
Records and tests only: reaches no user.

**Files:** `tests/test_verify_scoped_contracts.py`, `specs/001-faster-slipwai/slices/S06-scoped-gate/data-model.md`,
`delivery/docs/adr/0004-verification-dependency-record.md` (host only).

### T032 — [US2] MEDIUM — The migrate example cannot pass by being skipped (R13 · AC-S06-17)

- [x] **Finding.** T029 builds the "made before" project from `git archive 58a9aed`, and it skips the class when that
  commit is not in the clone (`tests/test_scoped_migrate.py` 39, 76–83). `58a9aed` lies on this feature branch only:
  it is not reachable from `main` or from any remote branch (`git merge-base --is-ancestor 58a9aed main` fails), and
  the clone has no `v*` tag. After a squash or rebase merge, CI's clone of `main` never has the commit, even with
  `fetch-depth: 0` (`verify.yml` 144). Every later run then reports `OK` with AC-S06-17's only end-to-end example
  skipped, and no line in the run's output says so.

**RED/GREEN:** the factory before the change comes from something every clone that runs the suite holds: the last
`v*` tag where one is fetched, otherwise `git merge-base HEAD <trunk>`, never a hash on a branch. Where none can be
found, the class fails under a CI marker (`CI`, `GITHUB_ACTIONS`) and skips only outside CI. The sweep covers every
`skipUnless`/`skipIf` in `tests/test_verify_scoped_*` and `tests/test_scoped_*`: none may skip in CI on a condition
the CI clone always meets or never meets.

**Verify:** `make test TESTS="test_scoped_migrate"`, and once with `CI=true`. Then `make lint typecheck check-structure`.
Tests only: reaches no user.

**Files:** `tests/test_scoped_migrate.py`.

*Appended by T017, converge pass 3 (2026-10-05), over `58a9aed..47cb343`.* Pass 2's five T030 reproductions now each
run the check or the full gate and exit 2. What follows is what pass 3 found still open.

### T033 — [US2] CRITICAL — A variable the comparison never reads changes what a skipped check runs (R4, R5 · AC-S06-2, -5; D127 item 4)

- [x] **Finding.** T030 closed the class for rule text. It is still open for variables. `rules.py` keeps a variable from
  the make database only when its origin is `file` and its name does not begin with a dot (`rules.py` 144). It compares a
  variable the factory never assigned only when a reached recipe names it (`rules.py` 241). That leaves three ways a
  project can change what a factory check runs, and the comparison never sees any of them.
  (1) **An `override` directive.** Its origin is `'override' directive`, so `from_database_parsed` drops it. It is in
  `data.origins`, so `changed_variables` does not count it as removed (242). D127 item 4 compares every variable the
  Makefile assigns and excludes only environment and command-line origins. Dropping `override` is a gap in the
  implementation, not in the decision.
  (2) **A variable that reaches every recipe without being named in one.** An exported variable reaches every recipe
  through the environment: `PATH`, `BASH_ENV`, `NODE_OPTIONS`, `PYTHONPATH`, anything `export`ed. So does one that
  came from the environment and is reassigned in the Makefile. None of them is "referenced" under D127 item 4.
  (3) **Dot-names** (`.SHELLFLAGS`, `.EXTRA_PREREQS`), which `rules.py` 123/144 skip on both sides.
  **Reproduced** in the TS service + web starter, with the pass-2 shape (probe
  `/home/noahc/math/.s06-tmp-main/probe3/probe_p3.py`). On `main`, commit one project edit and a 4-line wrapper that exits 1 when its command line
  names `render-drawio` and `apps/web/src` holds `FORBIDDEN`. Then on `slice/S1`, with a baseline, append
  `// FORBIDDEN` to `apps/web/src/App.tsx`. Two edits each give `skip check-drawio — none of its inputs changed`,
  then `15 run, 7 skipped, …; passed`, exit 0, while `make check-drawio` exits 2 (`veto: FORBIDDEN in apps/web/src`):
  (a) `override SHELL := ./tools/shell`;
  (b) `export PATH := $(CURDIR)/tools/bin:$(PATH)`, with the wrapper as `tools/bin/node`.

**RED** (`tests/test_verify_scoped_rules.py`, or a new `tests/test_verify_scoped_variables.py` if it nears 350):
- e1 (a): an `override` of a factory variable is a difference. For `SHELL`, which every recipe reads, that is the full
  gate with `variable \`SHELL\``. *(fails today)*
- e2 (b): a Makefile assignment of a variable the factory never assigned, where the variable is exported or born in
  the environment, is a difference. *(fails today)*
- e3: a `.SHELLFLAGS` the factory did not write is a difference. *(fails today)*
- e4 **hold**: T030's e5. For every shape in `test_scoped_targets.SHAPES`, plus two-service and a cloud shape, the
  factory's own `override VERIFY_GROUP` and its dot-names give no difference.

**GREEN — the class.** Every variable make can hand a recipe is compared. That covers a Makefile assignment of any
origin except environment and command line (D116's), `override` included. It also covers the special variables
make reads, and every variable that reaches a recipe through the environment. Item (1) is D127 as written. Items (2)
and (3) widen D127 item 4's *referenced* rule. Before GREEN, the host records in the decision log what an unnamed,
exported project variable is charged to: the full gate, or nothing where it is provably unexported. `make -p` does
not print export status, so "provably" needs a reader, for example a `--eval` target that prints `$(.VARIABLES)`
with their exported values. The sweep covers each place `rules.py` and `record.database` decide a variable is not
compared. Each one is either an origin D116 gives the baseline, or a test names why make cannot hand it to a recipe.

**Verify:** `make test TESTS="test_verify_scoped_rules test_verify_scoped_sum test_verify_scoped_record test_scoped_targets"`
(plus any new module), then `make lint typecheck check-structure`. Level line: MINOR, already carried.

**Decided — D133 (a), tightened; ADR 0005 amended at Proposed.** Read `## D133 ` in
`specs/001-faster-slipwai/decisions.md` in full — its seven items are this task's GREEN: (1) every database variable of
origin `file` or `override` is compared, dot-names and specials (`MAKEFLAGS`, `VPATH`, `GPATH`, `MAKEFILES`,
`MAKESHELL`) included, `define` blocks read; only `environment`, `environment override`, `command line`, `default`,
`automatic`, bare `makefile` (`CURDIR`) and `MAKEFILE_LIST` are left out, each named in the sweep test; an override
keeps its own flavour; (2) a variable the factory did not write is the full gate; a changed fingerprinted one is
charged per D127 item 4, except a factory-exported one (`DATABASE_URL`, `WEB_HOST`) and `SHELL`/`.SHELLFLAGS`, which are
the full gate; a pattern-specific variable is the full gate; a target-specific variable becomes the rule's `"vars"` key;
(3) `rules.json` gains `exports`, one digest over every `export`/`unexport`/`.EXPORT_ALL_VARIABLES`/`$(eval` line of the
files in `MAKEFILE_LIST`; a difference is the full gate, an unreadable file or a missing key *dependency knowledge was
incomplete*; (4) the factory's `override VERIFY_GROUP` is held by its written text through a table in `rules.py`; (5)
the printed lines, word for word; (6) e2 widened, e5–e7 added, e4 extended, teeth; (7) the Catch-up sentence, word for
word. Not here: a project's `.ONESHELL:` or `.POSIX:` (rule text, T030's class) — the next converge pass.

**Files:** `changelog.d/scoped-gate.md` (D133 item 7),  `assets/toolkit/scripts/verify_scoped/rules.py`, `assets/toolkit/scripts/verify_scoped/record.py`,
`tests/test_verify_scoped_rules.py` (or the new module), `specs/001-faster-slipwai/decisions.md` (host only).

### T034 — [US2] HIGH — The rules are read under the goal the full gate gives them (R4, R5 · AC-S06-2, -5; D127 item 2)

- [x] **Finding.** `record.database` reads the make database with the goal `.DEFAULT` (`record.py` 28). `make verify`
  hands its sub-make the goal `verify-checks`. A conditional on `MAKECMDGOALS`, or on `MAKELEVEL`, can add a
  prerequisite or a line that the full gate runs and the comparison never sees. **Reproduced** (probe
  `GoalConditional`). On `main`, commit
  `ifneq ($(filter verify-checks,$(MAKECMDGOALS)),)` / `check-drawio: lint-docs` / `endif`, plus a `lint-docs` that
  greps `apps/web/src` for `FORBIDDEN`. On `slice/S1`, the same edit to `App.tsx` gives `skip check-drawio`, then
  `passed`, exit 0. `make -n verify-checks` plans `lint-docs`, and `make lint-docs` exits 2.
  Graded HIGH, not CRITICAL: the rule has to exist only under the full gate's own goal, and the merge root runs that
  gate (owner priority 1).

**RED:** e1 is the reproduction above: `check-drawio` runs, or the run is the full gate. *(fails today)* e2 **hold**:
for every shape, the database read under `verify-checks` (at `MAKELEVEL=1`) and the one read under `.DEFAULT` agree.

**GREEN:** compare under the full gate's conditions. Read the database under the goal and level `verify`'s recipe gives
its sub-make. Where that read differs from the read under the scoped run's own goals, the run is the full gate, with
its reason. The sweep covers each conditional a project's Makefile can branch on that differs between the two runs:
`MAKECMDGOALS`, `MAKELEVEL` and `MAKEFLAGS`. A test names each one.

**Verify:** `make test TESTS="test_verify_scoped_rules test_verify_scoped_incomplete test_scoped_targets"`, then
`make lint typecheck check-structure`.

**Files:** `assets/toolkit/scripts/verify_scoped/record.py`, `assets/toolkit/scripts/verify_scoped/rules.py`,
`tests/test_verify_scoped_rules.py`.

### T035 — [US2] MEDIUM — A prune the project ran is not a Makefile the project wrote (R5, R13 · AC-S06-5, -18)

- [x] **Finding.** `generate` writes `rules.json` from the Makefile it has already pruned. With or without explicit
  answers (`--event-store memory --http none`, postgres + fastify + keycloak, python + fastapi), and after
  `add-service`, the database matches and nothing is charged. A later `./init --event-store …` or `--http none`
  behaves differently. The project README offers it under *Changing your mind*, with the example
  `./init --event-store memory --http none`. The prune cuts marked regions from the Makefile through
  `prune.prune` → `strip_markers` (`assets/backing-services/prune.py` 1270–1274), but leaves `rules.json` alone.
  - `--event-store memory` from a postgres-holding Makefile → every scoped run is the full gate, with
    `the Makefile's variable \`CI_DATABASE\` is not the one the factory wrote`.
  - `--http none` → the full gate, with `` `verify-checks` rule `` (it drops `verify-checks: check-openapi`).

  Measured in all four generated starters. No false green: the run is safe and only slow. It lasts until the next
  `slipwai migrate`, which regenerates `rules.json` for the recorded answers; a merge that keeps the pruned Makefile
  then matches. Meanwhile the scoped gate never scopes, and its words blame an edit the person never made.

**RED** (`tests/test_verify_scoped_rules.py`): generate a starter that keeps the postgres and fastify regions. Run
`scripts/backing-services.py --event-store memory` and, separately, `--http none`. `rules.judge` then charges nothing.
*(fails today)* **Hold:** a Makefile edited by the project before the prune still gives its difference after the
prune.

**GREEN:** the prune that edits the Makefile re-fingerprints it, but only when the Makefile matched `rules.json` before
the prune. It uses `scripts/verify_scoped/rules.py`'s `from_text` over the pruned text, written by temporary file and
rename (Principle II). A Makefile that already differed is left differing. The sweep covers every code path that
writes the Makefile of a stamped project: `generate`, `add-service`, `migrate`/`replay`, `prune`, and any `./init`
step. Each one leaves `rules.json` matching, and a test names each.

**Verify:** `make test TESTS="test_verify_scoped_rules"` plus the prune's own suite, then
`make lint typecheck check-structure`. Level line: PATCH-sized, already carried by the MINOR.

**Files:** `assets/backing-services/prune.py`, `tests/test_verify_scoped_rules.py` (and the prune test module that
covers `prune()`, named by the implementer).

*Appended by T017, converge pass 4 (2026-10-05), over `58a9aed..b3b51c0`.* Pass 3's two T033 reproductions and T034's
`GoalConditional` now each run the full gate. Each new test has teeth: dropping `override` from `rules.COMPARED`,
dropping the unwritten-variable cause, ignoring the exports digest, returning None from `under_the_full_gate`, not
giving the goal or the level, or skipping `refingerprint` each fails its module. What follows is what pass 4 found
still open. Probes: `/tmp/s06-c4/probe4/probe_p4.py`, `probe_specials.py` (run from a clone at `b3b51c0` with
`PYTHONPATH=src:tests:/tmp/s06-c4/probe4`).

### T036 — [US2] CRITICAL — A rule make applies that no fingerprint holds: implicit rules, special targets, `vpath` (R4, R5 · AC-S06-2, -5; D127 items 2, 4, 7)

- [x] **Finding.** T030 and D127 item 7 hold "every rule reachable from `verify`". Reachable means through *explicit*
  prerequisites only (`rules.reach`, `rules.py` 205–214; `ruled` 217–220; `fingerprint` 277–282). But make also
  applies rules that no explicit prerequisite names. None of them is compared, and none of them is the full gate.
  (1) **Implicit rules.** A pattern rule, a suffix rule, a match-anything `%::` rule or a `.DEFAULT:` recipe whose
  target matches a reached name that has no recipe of its own. That includes reached files such as
  `scripts/event-model/package.json`, the prerequisite of `scripts/event-model/node_modules/.installed`, which
  `check-drawio` waits for. (2) **Special targets** that change how every recipe runs or whether it runs:
  `.ONESHELL`, `.POSIX` (it gives `.SHELLFLAGS` `-e`), `.SECONDEXPANSION`, `.SUFFIXES`, `.DEFAULT`, `.DELETE_ON_ERROR`,
  `.PRECIOUS`, `.INTERMEDIATE`, `.SECONDARY`, `.NOTINTERMEDIATE`, `.NOTPARALLEL`, `.SILENT`, `.LOW_RESOLUTION_TIME`,
  and `.PHONY` membership of a reached target, which also turns implicit-rule search on or off. (3) **`vpath`
  directives**, which the database prints in its own *VPATH Search Paths* section and `record.database` never reads.
  **Reproduced** (probe `PatternRule`, TS service + web starter). On `main`, commit
  `scripts/event-model/%.json: FORCE` / `\t@! grep -rq FORBIDDEN apps/web/src` / `FORCE:`. On `slice/S1` with a
  baseline, append `// FORBIDDEN` to `apps/web/src/App.tsx`. The result is `skip check-drawio — none of its inputs
  changed`, then `15 run, 7 skipped, …; passed`, exit 0. Meanwhile the full gate's sub-make (`make verify-checks
  VERIFY_ORDER=1`) exits 2 with `*** [Makefile:262: scripts/event-model/package.json] Error 1`. The rule has no
  condition: it is T030's class. A project's own `%.json: %.yaml`-style rule is ordinary Makefile writing, not an attack.
  `probe_specials` appends each of `.ONESHELL:`, `.POSIX:`, `.SECONDEXPANSION:`, `.DELETE_ON_ERROR:`,
  `.NOTPARALLEL:`, `.SUFFIXES: .x .y` with a suffix rule, `.SILENT:`, `.DEFAULT:`, `%::`, a pattern rule, `vpath`,
  `.PRECIOUS:`, `.INTERMEDIATE:` and a `.PHONY` line. Each gives `skip check-drawio — none of its inputs changed`,
  exit 0: neither compared nor the full gate. (`.IGNORE:` is the full gate today only because it adds `i` to `MAKEFLAGS`.)

**RED** (a new `tests/test_verify_scoped_implicit.py`; `test_verify_scoped_rules.py` is at 132 lines, so it may hold this if it stays under 350):
- e1: the reproduction above. `check-drawio` runs, or the run is the full gate. *(fails today)*
- e2: a match-anything rule (`%:: FORCE` with a recipe) and a `.DEFAULT:` recipe are each the full gate. *(fails today)*
- e3: each special target in (2) that the factory did not write is the full gate, with its own reason. *(fails today)*
- e4: a `vpath` directive whose pattern matches a reached name is the full gate. *(fails today)*
- e5: a project pattern rule whose target pattern matches no reached name, and a `.PHONY` line naming only targets
  `verify` does not reach (a project's `deploy`), charge nothing. This is the scoping a project keeps (D131's reasoning).
- e6 **hold**: for every shape in `test_scoped_targets.SHAPES`, plus two-service and a cloud shape, the factory's own
  `.PHONY` lines, its built-in implicit rules (under the make on the machine and, where present, 3.81) and its special
  targets give no difference.

**GREEN — the class.** Every rule make can apply while it builds a name `verify` reaches is held. Held means one of
three things: a fingerprint, a charge, or the full gate. "Reached" covers the names make *searches* for as well as
the names prerequisites list. Read the database's implicit rules (pattern and suffix rules whose definition comes from
a makefile, not `(built-in)`), its special targets and its *VPATH Search Paths* section. A makefile-origin implicit
rule whose target pattern matches a reached name, or that matches anything, is charged per D127 item 4 to the members
that reach the matched name. Where no single member can be charged, it is the full gate. A special target the factory
did not write, or a reached target's `.PHONY` membership that differs from the factory's, is the full gate. `vpath`
is the full gate wherever its pattern matches a reached name. **The sweep:** a test lists every special target GNU Make
4.4 documents and every section header `make -p` prints. For each one it names whether it is compared, the full gate,
or provably unable to change a recipe that runs (with the reason, for example `.NOTPARALLEL` orders and never adds),
and it fails on a header nobody classified. Before GREEN, the host records in the decision log what a project's own
pattern rule matching no reached name, and a project's own `.PHONY` line, are charged to (recommended: nothing, per e5).

**Verify:** `make test TESTS="test_verify_scoped_implicit test_verify_scoped_rules test_verify_scoped_variables test_verify_scoped_goal test_scoped_targets"`,
then `make lint typecheck check-structure`. Level line: MINOR, already carried. Catch-up: the fragment gains one sentence
naming a pattern rule, a special target and `vpath`, in the words the decision gives.

**Files:** `assets/toolkit/scripts/verify_scoped/rules.py`, `assets/toolkit/scripts/verify_scoped/record.py`,
`changelog.d/scoped-gate.md`, `tests/test_verify_scoped_implicit.py` (new), `specs/001-faster-slipwai/decisions.md`
(host only).


**Decided — D140 (a): the Makefile is held by its text; ADR 0005 amended at Proposed.** Read `## D140 ` in `specs/001-faster-slipwai/decisions.md` in full — its eight points replace this task's GREEN and T037's together (one implementer, both tasks): the `makefile` digest checked before any make call, `GNUmakefile`/`makefile`/`MAKEFILES`, matching text's database differences as the full gate, D127 item 4's narrower charges and `rules.used` removed, the factory-text hold over every shape (point 4), the words (point 6), the writers (point 7), the examples and teeth (point 8, e5 reversed). The same commit series updates plan.md R6 e2, data-model.md *How a unit is chosen*, and replaces the Catch-up sentences D127 and D133 put in `changelog.d/scoped-gate.md` with:

> `make verify-scoped` scopes only the `Makefile` the factory wrote. If yours differs from it in any way — a check, a target, a variable, a rule or a condition of your own — or if make would also read a `GNUmakefile`, a `makefile` or a file named in `MAKEFILES`, every scoped run is the full gate, `make verify`, and says so on its first line, until the file is the factory's text again. `slipwai migrate` carries the factory's changes into your `Makefile` but never makes your edits count as the factory's. To keep scoping, put targets of your own in a file `make verify` does not read and run them with `make -f deploy.mk <target>`. Your merge root and CI run `make verify` either way.

### T037 — [US2] HIGH — The conditions a scoped run reads are not the conditions any real run has (R4, R5 · AC-S06-2, -5; D127 item 2; T034 closed one instance)

- [x] **Finding.** T034 reads the database a second time, with `MAKECMDGOALS=verify-checks` given *on the command
  line*, `MAKELEVEL` 1 and `VERIFY_GROUP` (`record.py` 69–80, 301–317). Every read still carries `-npq`. That models
  the real sub-make (`gate.py` 36: `"$(MAKE)" $(VERIFY_GROUP) --no-print-directory -f … verify-checks VERIFY_ORDER=1`)
  for the one conditional per variable that T034's sweep tried (`test_verify_scoped_goal.py` 24–28). It differs from
  the real runs in five ways, and each is a route T034's GREEN named as its class:
  (a) **`VERIFY_ORDER=1` is never given.** Real runs get it: the full gate's sub-make, and the scoped run's own call
  (`verify-scoped.py` 246). The factory's own `ifeq ($(origin VERIFY_ORDER),command line)` block is skipped by
  `from_text` (`rules.py` 40, 87–89) and absent from both reads, so nothing written inside it, or under the same idiom
  that the generated Makefile shows the project, is ever compared.
  (b) **The `n`, `p`, `q` flags are visible to the Makefile in every read and in no real run.**
  (c) **`MAKECMDGOALS` has origin `command line` in T034's read and `default` in make's.** `MAKEFLAGS` also gains
  `-- MAKECMDGOALS=verify-checks`.
  (d) **The scoped run's own call has the chosen units as its goals.** No read models those, so a conditional on them
  changes a unit that *runs*.
  (e) **`MAKEFLAGS += -e` in the Makefile is printed with origin `environment under -e`.** `ORIGIN` (`record.py` 34)
  takes it as `environment` and `compared_variables` drops it (`rules.py` 186). It is the one Makefile flag that hides,
  and it hands every factory variable to the environment. Of the others, `n`, `p`, `q`, `--no-print-directory` and
  `-O…` hide in `own_flags` (`rules.py` 168–173), but each applies equally to the scoped call and to `make verify`, so
  none can make one pass where the other fails. `-k`, `-B`, `-r`, `--trace` and `-i` show in the value and are the full gate.
  **Reproduced** (probe `probe_p4.py`, TS service + web starter, a `lint-docs` that greps `apps/web/src` for
  `FORBIDDEN`). On `main`, commit one of the following; on `slice/S1` with a baseline, append to `App.tsx`. Each of
  (a)–(d) gives `skip check-drawio — none of its inputs changed` (or `run lint-web`), then `…; passed`, exit 0. The
  full gate's sub-make exits 2 each time:
  (a) `ifeq ($(origin VERIFY_ORDER),command line)` / `check-drawio: lint-docs` / `endif`, which is the factory's own idiom;
  (b) `ifeq (,$(findstring n,$(filter-out --%,$(firstword $(MAKEFLAGS)))))` around the same line;
  (c) `ifneq ($(origin MAKECMDGOALS),command line)` around T034's own goal conditional;
  (a′) unconditional `check-drawio: $(if $(VERIFY_ORDER),lint-docs)`;
  (d) `ifneq ($(filter lint-web,$(MAKECMDGOALS)),)` / `override SHELL := /bin/true` / `endif`, with web lint failing
  (`STANDIN_NPM_FAIL`). The output says `run  lint-web — apps/web/src/App.tsx changed`, then `passed`, exit 0, while
  the full gate fails at `lint`. The unit that *ran* passed vacuously.
  Graded HIGH, as T034 was: each case needs a rule that exists only under conditions the merge root's full gate gives
  it, and the merge root runs that gate (owner priority 1). (a) is the likeliest shape, because the factory prints the idiom.

**RED** (`tests/test_verify_scoped_goal.py`, or a new module if it nears 350): e1 is (a) through (d) as above, each the
full gate. *(fails today)* e2: `MAKEFLAGS += -e` is the full gate. *(fails today)* e3 **hold**: T034's e2, together with
the factory's own `VERIFY_ORDER` block, gives no difference in any shape.

**GREEN — the class.** A Makefile's parse can branch on anything that differs between a database read and a real run:
the goals, the flags, the command-line variables, `MAKELEVEL`, `MAKE_RESTARTS`, the clock, the environment. No read
under `-n` can reproduce all of them. A real goal under `-n` runs `$(MAKE)` lines, as T034 found and pass 4 confirmed:
`make -npq verify-checks` runs a `$(MAKE)` line and a `+` line. So hold the branch points by **text**, as D133 item 3
holds `exports`. `rules.json` gains `conditionals`: one digest over every conditional directive (`ifeq`, `ifneq`,
`ifdef`, `ifndef`, `else`, `endif`), together with the lines they enclose, and over every non-recipe line that names a
run-varying name (`MAKECMDGOALS`, `MAKEFLAGS`, `MFLAGS`, `MAKEOVERRIDES`, `MAKELEVEL`, `MAKE_RESTARTS`, `VERIFY_ORDER`)
or calls `$(origin` or `$(flavor`. The digest covers every file in `MAKEFILE_LIST`, read like `export_lines`, with the
factory's own `VERIFY_ORDER` block included. A difference is the full gate. `MAKEFLAGS` of origin `environment under -e`
is compared like `file`. T034's second read then stays only as a hold, or goes, as the decision says. **The sweep:** a
test names each of (a)–(e), plus `MAKE_RESTARTS` and a `$(shell date)` condition, and each is the full gate. Before
GREEN, the host records in the decision log the text rule and its cost: a project's own `ifdef CI` block then makes
every scoped run the full gate, and the decision weighs that against a reader that models each real run.

**Verify:** `make test TESTS="test_verify_scoped_goal test_verify_scoped_rules test_verify_scoped_variables test_verify_scoped_prune test_scoped_targets"`,
then `make lint typecheck check-structure`. Level line: MINOR, already carried; the fragment's Catch-up gains the
decision's sentence.

**Files:** `assets/toolkit/scripts/verify_scoped/rules.py`, `assets/toolkit/scripts/verify_scoped/record.py`,
`changelog.d/scoped-gate.md`, `tests/test_verify_scoped_goal.py`, `specs/001-faster-slipwai/decisions.md` (host only).

**Decided — D140:** see T036; T037 is implemented with it.

### T038 — [US2] LOW — D127 item 4's per-member charge of a changed factory variable has an example (R4 · AC-S06-2)

- [x] **Superseded by D140 point 3** — the charge this task tested is removed. **Finding.** `rules.used` (`rules.py` 323–333) charges a changed factory variable to the one member whose reached
  recipes name it. Disabling it (`… is not None and False`) leaves all 205 tests of the 18 `test_verify_scoped_*`
  modules green. With the reader off, every such change is the full gate. That is the safe direction, but nothing
  holds D127 item 4's decided scoping.

**RED/GREEN** (`tests/test_verify_scoped_variables.py`): a factory variable that exactly one named check's recipe names
(directly, and through another variable's value) is given a new value on the trunk. That check runs with
`its rule is not the one the factory wrote …` and the run is not the full gate. The same mutation must then fail the
example. Tests only: reaches no user.

**Verify:** `make test TESTS="test_verify_scoped_variables"`, then `make lint typecheck check-structure`.

**Files:** `tests/test_verify_scoped_variables.py`.

### T039 — [US2] MEDIUM — Text and conditions that reach every make through `MAKEFLAGS` are compared by nobody (R4, R5, R7 · AC-S06-2, -5, -8; D140 point 2, D116 rule 5)

- [ ] **Finding.** D140 point 2 makes a non-empty `MAKEFILES` the full gate because it "adds makefiles the factory did not
  write". `MAKEFLAGS` carries the same kind of text and conditions, and it reaches every make the script starts.
  - Nothing reads it beyond the idle letters (`verify-scoped.py` 65–67, `verify-stamp.py` 683–687).
  - The database read strips it (`record.py` 35, 75), so the comparison reads clean factory text.
  - The scoped call (`verify-scoped.py` 253) and the full gate (`verify-scoped.py` 171) both inherit it.
  - The baseline keys none of it (`verify-stamp.py` 115–119; D116 rule 5 names only the job count).

  `MAKEFLAGS` carries `--eval` text, `-I`/`--include-dir` together with an eval'd `include`, `-e`, `-r`/`-R`, `-B`,
  `-W`/`-o`, and `-- NAME=value` command-line variables. These reach the scoped call from the command line, from
  `MAKEFLAGS` in the environment, and from `GNUMAKEFLAGS`.

  **Reproduced** (`/tmp/s06-c5/probe5/probe_p5.py`). Set-up: the TS service + web starter, factory text, a baseline
  written, then `// FORBIDDEN` appended to `apps/web/src/App.tsx`. Each of (a)–(d) gives `skip check-drawio — none of
  its inputs changed`, then `15 run, 7 skipped, …; passed`, exit 0. Under the same conditions the full gate's sub-make
  exits 2:
  - (a) `make verify-scoped '--eval=scripts/event-model/%.json: FORCE ; @! grep -rq FORBIDDEN apps/web/src' --eval=FORCE:`,
    which fails with `*** [<builtin>: scripts/event-model/package.json] Error 1`;
  - (b) `--eval=check-drawio: lint-docs` together with an eval'd `lint-docs` recipe. This is an explicit prerequisite,
    and the database comparison still never sees it, because it reads without `MAKEFLAGS`;
  - (c) the text of (a) in `MAKEFLAGS` in the environment;
  - (d) the same text in `GNUMAKEFLAGS`.

  Not an escape:
  - A second `-f` (`make -f Makefile -f extra.mk verify-scoped`) is read by neither the scoped call (`-f <first>`,
    `verify-scoped.py` 171, 253) nor the full gate's sub-make (`gate.py` 36).
  - An untracked `extra.mk`, or an `inc/x.mk` reached through `-I`, is an unclaimed path, and that is the full gate
    (probes e, f).

  **Graded MEDIUM, not HIGH.** Every route needs the person who runs the scoped gate to give the condition. The false
  *passed* is therefore relative to a `make verify` run under that same condition, never to the merge root's. The
  merge root runs without it, and there the skipped check's inputs have not changed since a green base (owner
  priority 1 holds). The published words still claim more than holds: the contract says the scoped run reads only
  text it has proved to be the factory's (data-model *How a unit is chosen*, ADR 0005), and `--eval` is such text.
  There is a second effect: a full green `make verify --eval='override SHELL := /bin/true'` on a slice branch writes a
  baseline that vouches for tools under which no check ran, because `declined()` reads only letters.

**RED** (`tests/test_verify_scoped_text.py`, at 192 lines; a new module if it nears 350):
- e1: (a)–(d) above are each the full gate, with their own words. *(fails today)*
- e2: each of these stays scoped: a `MAKEFLAGS` holding only a job count, the jobserver's words, `--no-print-directory`,
  `-O…`/`--output-sync=…`, `-k` or `-s`.
- e3: a full green `make verify --eval=…` on a slice branch writes no baseline. *(fails today)*

**GREEN — the class.** Hold `MAKEFLAGS` by an allowlist, as D140 holds the `Makefile` by its text, so that anything
not on the list fails closed.
- **Where.** Before any make call, beside `text_problem`, the script reads the `MAKEFLAGS` its recipe was handed.
- **The allowlist.** The single-letter word may hold only letters that apply alike to the scoped call and to
  `make verify` and change no recipe: `k`, `s`, `w`, and the idle letters the borders already take. Every other word
  must be one of: a job count, a jobserver word (`--jobserver-auth=`, `--jobserver-fifo=`), `--no-print-directory`,
  or an output-sync word.
- **Everything else is the full gate.** That includes any `--eval`, `-I`, `-e`, `-r`, `-R`, `-B`, `-W`, `-o`, `-L`,
  `--trace` and `--shuffle`, and anything after `--`.
- **The words**, after D140 point 6: `… — make was run with \`<the first word not allowed>\`, which can add text or
  conditions the factory did not write; …`.
- **The baseline.** The baseline writer in `verify-stamp.py` declines under the same predicate. The predicate is defined
  once, and both scripts load it.

**Decide before GREEN** (host, in the decision log):
- whether a command-line variable after `--` is the full gate (recommended: yes, failing closed) or the baseline's
  (D116);
- whether the stamp's own `declined()` takes the predicate too. The stamp is S05's, so that half is a decision for the
  log; this task's files do not include it.

**Verify:** `make test TESTS="test_verify_scoped_text test_verify_scoped_baseline test_verify_scoped_borders test_verify_scoped_run"`,
then `make lint typecheck check-structure`. Level line: MINOR, already carried. Catch-up: the fragment's D140 sentence
gains "or if make is run with an option that adds text or conditions — `--eval`, `-I`, `-e`, a variable on the
command line —" in the words the decision gives.

**Files:** `assets/toolkit/scripts/verify_scoped/rules.py`, `assets/toolkit/scripts/verify-scoped.py`,
`assets/toolkit/scripts/verify-stamp.py` (the baseline writer only), `changelog.d/scoped-gate.md`,
`tests/test_verify_scoped_text.py`, `tests/test_verify_scoped_baseline.py`, `specs/001-faster-slipwai/decisions.md`
(host only).

**Decided — D146:** (1a) a command-line variable after `--` is the full gate; (2a) the stamp's own `declined()` takes the same predicate, so `verify-stamp.py`'s stamp writer is in this task's files too. Read `## D146 ` in decisions.md.

**Decided — D147:** `VERIFY_FORCE` after `--` is on the allowlist, by name (the page's `make verify VERIFY_FORCE=1`); relayed to the implementer.

### T040 — [US2] MEDIUM — The factory-text hold covers the units and named checks only, and does not assert what makes its ordering exception sound (R4 · AC-S06-2; D140 point 4)

- [ ] **Finding.** D140 point 4 rests the class on one finite argument: the factory's text reads the same under the
  scoped call, the full gate's sub-make and the database read, for everything a scoped run can run. The test falls
  short of that in two ways.

  **First, its scope.** `test_verify_scoped_factory_text.py` compares only the units, the named checks, `verify` and
  `verify-checks` (`reached` 65–68, `held` 70–72 and 83–84). The fingerprint and the scoped call reach further,
  through prerequisites such as `node_modules/.package-lock.json`, `scripts/event-model/node_modules/.installed`,
  `sync` and `build-packages`. Those are the rules T030 established must be held.
  - **Mutation** (in a clone): `gate_order` (`parallel_gate.py` 150–151) writes
    `node_modules/.package-lock.json: VERIFY_HIDDEN := 1` inside the factory's `VERIFY_ORDER` block.
    `test_e6_hold_every_shape_reads_the_same_under_the_three_conditions` stays green.
  - **Control:** the same line on `check-python` fails that test, in `model-typescript-web` and
    `model-typescript-web-cloud`.

  **Second, its ordering exception.** The exception (`differences` 93–94) admits needs that grow by existing targets.
  That is sound only while three conditions hold:
  - no rule that gains a prerequisite has a recipe naming `$^`, `$+`, `$<`, `$?` or `$|`;
  - no target on the path sets a target-specific variable. make passes such a variable down to the prerequisites it
    runs, and no database read shows it on the prerequisite;
  - a normal prerequisite added to a *file* target does not change when that target is rebuilt.

  All three hold today. A scan of every `SHAPES` entry finds no target-specific variable and no automatic variable in
  any recipe, and the block's file-target line is order-only. Nothing asserts them, so a later `makefile()` construct
  can break the argument and still pass the hold.

  **Graded MEDIUM:** no false *passed* exists today, but this is the one argument D140 left to enumeration, and the
  test covers less than the gate runs.

**RED/GREEN** (tests only):
- e1: the hold compares every target that `rules.reach` finds from `verify`, `verify-checks` and the units, in each of
  the three reads, and the mutation above fails it.
- e2: the exception admits a grown `needs` or `order_only` only where all three hold:
  - (i) no recipe of the target names an automatic variable;
  - (ii) neither the target nor any target that reaches it has `target_vars` in any read;
  - (iii) a file target (one not in `.PHONY`) grows only its `order_only`.

  Each condition has a mutation of its own that fails e2.
- e3: a fourth read, the scoped call's goals *without* `VERIFY_ORDER`, must equal the database read exactly. That
  makes any growth attributable to the factory's `VERIFY_ORDER` block and no other conditional.

**Verify:** `make test TESTS="test_verify_scoped_factory_text"`, then `make lint typecheck check-structure`. Tests only:
reaches no user.

**Files:** `tests/test_verify_scoped_factory_text.py`.

### T041 — [US2] MEDIUM — The record's contract still describes D127's charges: `differs`, a named check's `always`, "each charged difference marked" (R10 · AC-S06-13; ADR 0004, data-model *The printed record*; D140 point 3)

- [ ] **Finding.** D140 point 3 removed the per-check `inputs: null` and per-gate Makefile charges.
  - The record now sets `whole` only where a recipe is not the sum of its units (`record.py` 286–289), and it never
    emits `differs`.
  - A Makefile difference on matching text is the full gate, charged to no check (`record.py` 319–323,
    `rules.py` 359–363).

  The published text still describes the old behaviour in three places:
  - ADR 0004, lines 81–85: `whole` "or its rule is not the one the factory wrote", `differs: true`, and a named check
    printed with `inputs: null` and an `always` reason;
  - data-model.md, lines 206–215: the same three, plus "the record is still printed, with each charged difference
    marked";
  - `verify-scoped.py` line 275: those words again, as a comment.

  ADR 0004's *Consequences* calls the printed shape a published contract, and a reader built from it looks for a key
  that never comes. **Graded MEDIUM**, as T031 was for the same drift: schema 1 is unreleased, so there is no released
  consumer.

**RED** (`tests/test_verify_scoped_contracts.py`): every backticked key that ADR 0004's record bullets give a value
(`` `<key>: true` ``, `` `: false` ``, `` `: null` ``) is a key that some shape's record prints. The same holds for
data-model.md *The printed record*. `differs` fails it today.

**GREEN:** ADR 0004's bullet and data-model's both say three things:
- `whole` means a gate's recipe is not the sum of its units;
- no key marks a Makefile difference;
- on such a difference the record is printed as it is, and the run is the full gate with *dependency knowledge was
  incomplete* (D140 point 3).

Delete `differs` and the named check's `always` reason from both texts, and the comment at `verify-scoped.py` 275. ADR
0004 records the amendment as ADR 0005 does: `Amended by D140 (…)`.

**Verify:** `make test TESTS="test_verify_scoped_contracts test_verify_scoped_record"`, then
`make lint typecheck check-structure`. Level line: MINOR, already carried. The fragment gains nothing, because no key
changed, only the text that describes the keys.

**Files:** `delivery/docs/adr/0004-verification-dependency-record.md`,
`specs/001-faster-slipwai/slices/S06-scoped-gate/data-model.md`, `assets/toolkit/scripts/verify-scoped.py`,
`tests/test_verify_scoped_contracts.py`.

### T042 — [US2] LOW — D140 point 2 as written: a `rules.json` that cannot be read lets the project's `Makefile` be parsed, and the name check is exact on a case-insensitive filesystem (R5 · AC-S06-5; D140 point 2)

- [ ] **Finding.** Two places where the code is weaker than D140 point 2's words.

  **(1) An unreadable `rules.json` lets the Makefile be parsed.** Where `rules.json` is missing or is not JSON,
  `text_problem` returns None (`rules.py` 230–234). `run` then reads the database with `make -npq`
  (`verify-scoped.py` 209) and asks `standing()`, and only then fails at `records.compared` and runs the full gate. So
  a `Makefile` the factory may not have written is parsed by the scoped run, and its `$(shell …)` runs. D140 point 2
  lists "`rules.json` has no `makefile` key" among the checks made before any make call, and a missing file has no
  key. The run still ends in the full gate.

  **(2) The name check is exact.** The entry-list check is exact (`rules.py` 225–227). On a filesystem where make's
  lookup of `GNUmakefile` opens `gnumakefile` or `GNUMakefile`, the list passes it. Not reproduced, because this host's
  filesystem is case-sensitive; if make does find such a file, the check fails open.

**RED/GREEN** (`tests/test_verify_scoped_text.py`):
- e1: with `rules.json` deleted, the first line is the `Makefile` words, and the stand-in make logs no `-npq` call.
- e2: a root entry `gnumakefile`, or `MAKEFILE`, is the full gate with D140's words, naming the entry as listed.
- GREEN for e1: `text_problem` returns `NOT_THE_TEXT` wherever `rules.json` cannot be read or is not an object with
  the key.
- GREEN for e2: compare entries casefolded. Any entry other than `Makefile` whose casefold is `gnumakefile` or
  `makefile` is the full gate. On a case-sensitive filesystem that costs a full gate for a file make would not read,
  which is the safe direction.

**Verify:** `make test TESTS="test_verify_scoped_text test_verify_scoped_matching"`, then
`make lint typecheck check-structure`. Level line: MINOR, already carried.

**Files:** `assets/toolkit/scripts/verify_scoped/rules.py`, `tests/test_verify_scoped_text.py`.

---

### T043 — [US2] HIGH — One deployable reading another's source is invisible to the selection (after-converge gaps G1 · AC-S06-2, -3, -5)

- [ ] **Finding** (T018's `drive-gaps`, reproduced in `/tmp/s06-g/two/two`). A TypeScript service plus `add-service billing`. On `main`, `apps/service/src/uses-billing.ts` imports `../../billing/src/rate.js`. On `slice/S2`, `rate` becomes a string, and `verify-scoped` prints `skip typecheck-service — none of its inputs changed`, then *passed*, while `make verify`'s `tsc` fails (noEmit, no `rootDir`). `check-imports.py` allows service-to-service imports. The same hole exists for npm workspace dependencies between apps, Go modules in one `go.work`, and uv path dependencies. The page's "chosen when a changed file is one it reads" is untrue here. **Decide before GREEN: D148** (skipper, pending at the time of writing). Its decision is this task's GREEN, with a RED example per language it names.

### T044 — [US2] MEDIUM — An index the stamp will not vouch for is not a border of the selection (G2 · AC-S06-1, -5)

- [ ] **Finding.** With `git update-index --assume-unchanged` (or skip-worktree, or sparse checkout) on a changed service file, the scoped run skips every service unit and says *passed*. `make verify` runs everything, because the stamp's `index_problem` refuses that index. `verify-scoped.py` calls `index_problem` only inside `standing()` (136), never before selecting. **RED:** assume-unchanged, skip-worktree and a sparse checkout are each the full gate, with the stamp's words. **GREEN — the class:** every reason the stamp gives for not vouching for a tree is a border before `changed_files`, through one shared predicate. **Files:** `assets/toolkit/scripts/verify-scoped.py`, `tests/test_verify_scoped_borders.py`.

### T045 — [US2] MEDIUM — The generated gates page says what D140 and D146 do (G3, G8, G9 · AC-S06-15, -18)

- [ ] **Finding.** `scoped_targets.SCOPED_PAGE` (48–67) names only "a changed `Makefile`" as broadening. It does not say that any text differing from the factory's, a `GNUmakefile`/`makefile`/`MAKEFILES`, or a make option that adds text or conditions makes every scoped run the full gate, nor how to scope again (`make -f deploy.mk`). Its obligation example (a service and the web app that calls it) is one the `openapi:<service>` contract already joins, so name a service pair instead (G8). "The trunk's own full gate passed it there" overstates a base that may be a local `main` nobody gated: say "the base" and what that is (G9). **RED:** `test_scoped_page.py` asserts each sentence. **GREEN:** the page says each, in the Catch-up's words where they overlap. **Files:** `src/slipwai/project/scoped_targets.py`, `tests/test_scoped_page.py`.

### T046 — MEDIUM — The quickstart's last step prints what it promises (G4 · AC-S06-19; host, records)

- [ ] **Finding.** At quickstart.md line 36, the README edit makes the full gate fail at `check-slice-scope` (outside every deployable). The failed run removes the baseline, so line 40 prints "no usable baseline" and not "check-ux-gates runs: UX_GATES_SINCE differs from the baseline". **GREEN:** use a path the slice may write that nothing claims, or run `make verify` once on the restored tree before line 40. Follow every step by hand before T019. **Files:** `quickstart.md` (host).

### T047 — LOW — AC-S06-5's words after D140, the record's tools, the Catch-up's contradiction (G6, G7, G10)

- [ ] (G6, host) AC-S06-5 in spec.md says "dependency knowledge was incomplete for …" per file. Under D140, a changed `Makefile` prints only the Makefile line. Amend the criterion to say the first cause is printed. (G7) In a Go starter with no web app, the record names `node`/`npm` for `check-ux-gates`, but `VERIFY_STAMP` asks only `make git python3 go`. Add a test that the record's tools are a subset of what the baseline asks for, across shapes, and make it so. (G10) The Catch-up says "nothing else asks anything of it" and then asks for a constitution amendment: reword it so it stands alone without contradicting itself. **Files:** `assets/toolkit/scripts/verify_scoped/record.py` or `table.py`, `tests/test_verify_scoped_record.py`, `changelog.d/scoped-gate.md`; spec.md (host).


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

### Pass 1 — iteration 22, `drive-converge` · model: host (claude-opus-5-5) · delegated, fresh context · over `58a9aed..aa7e45a`

**Not converged.** Three CRITICAL findings and one HIGH, each reproduced: `make verify-scoped` prints *passed* while a
check `make verify` runs on the same tree fails or is never run — table rows narrower than what their checks read
(T024), the data-model's recipe-sum guard never built (T025), ignored files the selection never sees (T026), and
`check-flags`' claim on `packages/` turning off R5's broadening (T027). MEDIUM T028 (the published sentence names a
comparison the code does not make; D123's words, so a decision) and LOW T029 (the migrate test and the fifo jobserver
example claim more than they hold). Leads cleared: deployables read from the working tree and obligations at the base
(a `project.json` change broadens); a `Makefile` change on a slice branch has its end-to-end example
(`tests/test_verify_scoped_incomplete.py`); T002 e5's sha256 pins cost only a test update; T006/T007's contract suite has
teeth. Levels: the generated Makefile (`verify`, `verify-checks`, `ci` byte for byte, `makefile.py` 334,
`scoped_targets.py` 38; a project's later Makefile edits unguarded, T025), the script (T024, T026, T027), the baseline
(`verify-stamp.py` written 907, removed 770 and 798, digests never values 733–735; lacks the ignored part, T026), the
published words (T028), migrate (works from the pre-slice commit; untested, T029). Principles touched: I (additive —
the gate's own rules unchanged, nothing under CI, `delivery/`, `tools/`, the root `Makefile` or `VERSION`; versioning —
`changelog.d/scoped-gate.md` line 1 `MINOR`), II (the baseline written by temporary file and rename), VIII (the record's
`schema: 1`, `record.py` 211; an unreadable baseline broadens, `choose.py` 53–56), IX (variable digests, never values,
`verify-stamp.py` 733–735). Pass 2 follows once T024–T029 are closed.

### Pass 2 — iteration 22, `drive-converge` · model: host (claude-opus-5-5) · delegated, fresh context · over `58a9aed..c3694ae`

**Not converged — one CRITICAL re-opens the loop past its bound.** Pass 1's T024, T026, T027, T028 closed, each
re-run from pass 1's probes; T025 closed its instance and T029 closed in part. New: **T030 CRITICAL** — the recipe-sum
guard reads only the three gates with units, so a project's own line or prerequisite on a named check, an order-only
prerequisite, a prerequisite of `verify` or a line of `verify-checks` is trusted unread, and the run says *passed* while
`make verify` fails (five reproductions); **T031 MEDIUM** — ADR 0004 and data-model.md do not name the record's `whole`
key or T027's claim rule; **T032 MEDIUM** — the only end-to-end migrate example skips silently where `58a9aed` is not in
the clone. Leads cleared: `load_model` installing `yaml` happens before the ignored digest is computed, so the run is
the full gate and the key moves with it (the script's docstring overstates; T031 carries it); a check that rewrites an
ignored file makes the next run full only after a real rewrite (`verify-stamp.py` 899–900); T025's multiset keeps each
target's own line order (`record.py` 187–189). Levels: the generated Makefile (gate rules unchanged; later project edits
outside the three unit gates unheld, T030), the selection (proved but T030), the baseline (written only when the key did
not move, 899–908; removed by any full run, 771), the record (T031), the words (T028 closed), migrate (T032). Principles:
I (satisfied in what changed; unmet in what a project's own `Makefile` edit gets — T030), II (`write_file`,
`verify-stamp.py` 747), VIII (`schema: 1`, `record.py` 23, 414; contract text drifted, T031), IX (digests,
`verify-stamp.py` 740–746). A pass 3 follows T030.

### Pass 3 — iteration 22, `drive-converge` · model: host (claude-opus-5-5) · delegated, fresh context · over `58a9aed..47cb343`

**Not converged — one CRITICAL re-opens the loop again.** T030 confirmed closed: pass 2's five reproductions now run
the changed check, run the gate whole, or run the full gate, each exit 2. Leads: `generate` (default and pruning
answers) and `add-service` leave `rules.json` matching the Makefile, so a real project scopes; D131 holds (a project's
prerequisite of `verify-checks` always runs and changes no factory check's rule without charging it); `rules.json` is
written on every stamped path and on no adopted one (`scaffold.py` 120, `gate.py` 48–50). New: **T033 CRITICAL** — an
`override` variable or an exported variable no recipe names (`override SHELL`, `export PATH := …`) changes what a
skipped check runs and is never compared; **T034 HIGH** — the database is read under `.DEFAULT`, not the
`verify-checks` goal the full gate runs (`record.py` 28), so a goal-conditional rule is unseen; **T035 MEDIUM** — a later
`./init` prune leaves `rules.json` stale: every scoped run is then full (safe) and its message blames an edit nobody
made, until `migrate`. Principles: I (met in what changed; the *passed* line overclaims in T033, T034), II (T035's
re-write must rename), VIII (`rules.py` 24 `SCHEMA = 1`; an unknown schema is the full gate, 216–218), IX (`rules.json`
holds digests only, 148–150).

### Pass 4 — iteration 23, `drive-converge` · model: host (claude-opus-5-5) · delegated, fresh context · over `58a9aed..b3b51c0`

**Not converged — one CRITICAL re-opens the loop again.** T033, T034 and T035 are confirmed closed. Pass 3's `override
SHELL`, `export PATH` and `GoalConditional` reproductions now run the full gate. A prune re-fingerprints a matching
`rules.json` (`prune.py` 1282–1309, 1336–1338). Seven mutations, one to each new guard, each fail their own module, and
each closing commit ships its test with its code (`bc39ad7`, `0b429e6`, `043d696`). New:
**T036 CRITICAL**: the fingerprint follows explicit prerequisites only. A project pattern rule on a reached file
(`scripts/event-model/%.json`) makes `check-drawio` fail under `make verify` while the scoped run says *passed*. Special
targets (`.ONESHELL`, `.POSIX`, …) and `vpath` are neither compared nor the full gate.
**T037 HIGH**: the database reads carry `-npq`, never `VERIFY_ORDER=1`, and give the goal as a command-line variable.
Conditionals on the factory's own `VERIFY_ORDER` idiom, on the dry-run flags, on `MAKECMDGOALS`' origin and on the scoped
call's own unit goals each give a false *passed* (five reproductions). `MAKEFLAGS += -e` hides as origin
`environment under -e`.
**T038 LOW**: D127 item 4's per-member variable charge has no example; the safe mutant survives 205 tests.
**Leads.** Lead 4 is graded LOW with no task: after a conflicted `migrate`, the resolved rule *is* the project's, and
D127 item 5 chose those words. `./init` records its answers, so replay matches a pruned project
(`test_verify_scoped_prune` e7). Lead 5 is a note only: `check-structure.py` bounds `src/slipwai` and `tests` (109,
150) and nothing under `assets/`, so `record.py` at 545 lines and `rules.py` at 392 break no rule. D127 item 3's "inside
check-structure's budget" was a premise no rule held.
**The class, each route.** Compared: rule text (`rules.py` 223–225), variables of origin `file` and `override` (186),
export lines (232–246, 379), `MAKEFLAGS` letters outside `npq` (168–173), `include`d and `-include`d files, which the
read remakes as make does and which are in `MAKEFILE_LIST` and the database. Not compared, and taken by T036: implicit
rules, special targets and `vpath`. Not compared, and taken by T037: conditionals on goals, flags, origin and
`VERIFY_ORDER`, and `-e`. Left to D116's baseline: `MAKEFILES` and a recipe's run-time environment, held by the stamp's
closed `VARIABLES` (`verify-stamp.py` 115–119) and the tools' versions, the same trust S05's stamp reuse extends.
Provably unable to change a recipe that runs: `-n`/`-q`/`-O`/`--no-print-directory` in a Makefile's `MAKEFLAGS`, which
apply alike to the scoped call and to `make verify`.
**Levels.** No domain or screen. The selection (use case: `choose.py`, `rules.judge`) is proved for explicit rules,
variables and exports; T036 and T037 are open. The adapter (the generated Makefile): `verify` and `ci` are unchanged
(`gate.py` 36), and the scoped section is unchanged in this range. The published contract: the record (ADR 0004) is
untouched. `rules.json` (ADR 0005, Proposed) gains `exports`, and T036 and T037 will add keys while it is unreleased
schema 1. The fragment's Catch-up carries D133 item 7.
**Principles.** I: additive. Merge root and CI still run `make verify` (`gate.py` 36). Nothing under CI, `tools/`, the
root `Makefile` or `VERSION` changed; `delivery/` gained ADR records only. `changelog.d/scoped-gate.md` line 1 is
`MINOR`. A prune rewrites `rules.json` only inside a command the maintainer ran, and only where it matched (`prune.py`
1282–1291). The *passed* line still overclaims (T036, T037). II: the rewrite is by temporary file and rename
(`prune.py` 1302–1307; `test_verify_scoped_prune` e5). VIII: `SCHEMA = 1` (`rules.py` 27); a file without `exports` or
of an unknown schema is the full gate (`rules.py` 317–319, `record.py` 328–329). IX: `rules.json` holds names and
digests only (`rules.py` 200–202, 277–287); exported values are never stored. XIII (not in force) and XIV: tests ship
in each code commit, and the mutations above fail them. No money, time or identity value is touched.

### Pass 5 — iteration 23, `drive-converge` · model: host (claude-opus-5-5) · delegated, fresh context · over `58a9aed..3b74bf9`

**Converged.** No CRITICAL or HIGH finding: nothing re-opens the loop. D140 closes pass 4's class. Four tasks are
appended, all below the grade that re-opens: T039, T040 and T041 MEDIUM, T042 LOW.

**Pass 4 re-run against `3b74bf9`.** Every reproduction now ends in the full gate, with D140's `Makefile` words on
the first line:
- T037 (a), (b), (c), (a′) and (d), and T036 e1: exit 2, the full gate's sub-make also exits 2;
- `probe_specials`' 17 constructs (T036 e2–e5, with `.PHONY` reversed per point 8): each is the full gate.
  `MAKEFLAGS += n` is the `-n` border.

**Teeth.** One mutation per new module, each made in a clone under `/tmp/s06-c5` and restored by path:
- dropping the `MAKEFILES` test from `text_problem` fails 2 of `test_verify_scoped_text`;
- skipping the text check in `run` fails 21 subtests of `test_verify_scoped_implicit`;
- a `VERIFY_ORDER`-only target variable on `node_modules/.package-lock.json` passes
  `test_verify_scoped_factory_text`. The same line on `check-python` fails it. That gap is T040.

**The class, each route** (item 2 of the brief):
- **`-f`.** The first file is compared: it is the recipe's `$(firstword $(MAKEFILE_LIST))` (`scoped_targets.py` 135),
  digested at `rules.py` 236–240. Later `-f` files are read by neither the scoped call (`verify-scoped.py` 171, 253)
  nor the full gate's sub-make (`gate.py` 36), and `-f` never travels in `MAKEFLAGS`.
- **`include` in the factory's text.** Cannot exist: `from_text` raises on `include`, `-include` and `sinclude`
  (`rules.py` 91–96). A project's own `include` changes the text, so it is the full gate.
- **`-I` alone.** Has nothing to resolve.
- **`--eval`, and `-I` with an eval'd `include`, from the command line, `MAKEFLAGS` or `GNUMAKEFLAGS`.** Neither
  compared nor the full gate, nor the baseline's (`verify-stamp.py` 115–119; D116 rule 5 keys only the job count).
  Four false *passed* reproductions: T039.
- **A symlinked `Makefile`.** Compared: `open` follows the link and digests what make reads (`rules.py` 236–237). A
  dangling link is the full gate (238–239).
- **A case-insensitive filesystem.** A `Makefile` found under the name `makefile` is the same text. A
  differently-cased `gnumakefile` passes the exact list (`rules.py` 225–227). Not reproduced: T042.
- **`MAKEFILES` in the environment.** The full gate (`rules.py` 228–229). Given on make's command line instead, it was
  not probed.
- **Command-line variables outside `VARIABLES`.** Not compared. Whether they are the full gate or the baseline's is
  T039's decision.

**Item 3: the `VERIFY_ORDER` exception.** Sound today, by fact and not by test. Both real runs carry the block
(`gate.py` 36, `verify-scoped.py` 253), so over-running is the worst it does. Under the block, units gain normal
prerequisites (`scoped_targets.py` 116–126). The block's file-target line is order-only. No shape has a
target-specific variable or an automatic variable in any recipe (a scan of every `SHAPES` entry). The test asserts
none of these conditions, and it compares only named targets: T040. Not reproduced: a unit that the block pulls in as
a prerequisite still prints `skip` while it runs (safe direction).

**Item 4: the stale record text.** ADR 0004 (lines 81–85), data-model.md (206–215) and `verify-scoped.py` 275 still
describe `differs`, D127's per-check `always` and "each charged difference marked". The record emits none of them
(`record.py` 286–289): T041, MEDIUM, as T031 was.

**Item 5: the relay from S14.** Not S06's, graded LOW, no task.
- `NOT_AN_INPUT` (`tests/test_verify_scoped_record.py` 42–46) is the e4 sweep's list of explanations; it is not
  `table.py`.
- The sweep's stale rule (`test_verify_scoped_record.py` 330–331) fails an entry that no check reads uncovered. On
  this tree the literal `agents` is read only by `scripts/agents/benchmark.py`, and check-benchmark's `agents/` covers
  it there. An entry added here would fail e4.
- The entry belongs in S14's own commit that makes check-decisions load `hand_backs.py`:
  `"agents": "a key of a benchmark.json stage, not a path"`. That commit should also spell the literal plainly:
  `"agent" + "s"` evades the sweep instead of explaining the literal to it. The host relays this to S14.

**Levels.** No domain or screen.
- **Use case** (`text_problem`, `rules.difference`, `choose`): proved for the `Makefile`'s text. `MAKEFLAGS` is open
  (T039).
- **Adapter** (the generated `Makefile`): `verify`, `verify-checks` and `ci` are unchanged (`gate.py` 36), and so is
  the recipe of `verify-scoped` (`scoped_targets.py` 135). The factory-text hold is partial (T040).
- **Published contracts.** `rules.json` gains `makefile` under unreleased schema 1, and ADR 0005 is amended
  (Proposed). The record's text has drifted (T041). The fragment's Catch-up carries D140's sentence
  (`changelog.d/scoped-gate.md` 13).

**Principles.**
- **I.** Met. The merge root and CI run `make verify` (`gate.py` 36). A project's edit costs the full gate and is
  never blessed (`rules.py` 214–240, `verify-scoped.py` 202–207). Nothing under CI, `tools/`, the root `Makefile` or
  `VERSION` (`1.6.0.dev0`) changed; `delivery/` gained ADR text only. `changelog.d/scoped-gate.md` line 1 is `MINOR`.
  The *passed* line overclaims only under a person's own `MAKEFLAGS` (T039).
- **II.** Met. A prune rewrites `rules.json` by temporary file and rename (`prune.py` 1294–1307), and only where the
  whole file, `makefile` included, equals `from_text` (1280–1291).
- **VIII.** Met. `SCHEMA = 1` (`rules.py` 28). A file of an unknown schema, or one without `exports`, is `Unreadable`
  (346–356). One without `makefile` is the full gate (240). The record's contract text is T041.
- **IX.** Met. `rules.json` holds digests only (`text_digest` 201–204, `variable_digest` 271–272). The baseline stores
  variable digests, never values (`verify-stamp.py` 733–735).
- **X.** Met. On the trunk and under a CI marker, the scoped gate is `make verify` (`verify-scoped.py` 70–74, 87–89,
  111).
- **XIII.** Not in force.
- **XIV.** Met. `be74b85` ships its tests with its code, and the mutations above fail them, except T040's gap.

No money, time or identity value is touched.

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
