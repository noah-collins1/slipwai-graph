# Tasks: S07-scoped-checks — the method-file and preview checks skip what did not change on a slice branch

**Input**: [plan.md](plan.md) (*The example map* R1–R10 is what the tasks cut on), [research.md](research.md),
[data-model.md](data-model.md), [quickstart.md](quickstart.md); AC-S07-1 … AC-S07-14 in
`specs/001-faster-slipwai/spec.md` under `### S07-scoped-checks`; D170–D173 in `decisions.md`; S06's D114–D117 and
ADR 0004. A method slice: **no screen, no white box, no mockup task and no styling task**. The host runs the demo;
there is no demo task here.

**Branch**: `slice/S07-scoped-checks`, worktree `/home/noahc/math/slipwai-graph-S07-scoped-checks`. Delegates do not
commit-switch, push or touch branches. One commit per task, by path.

**Delegation**: one task is one RED-GREEN-REFACTOR increment opening with one rule's examples; a delegate never writes a
later rule's tests early. A task's **Files** line is its manifest, the only files that delegate may write. Nobody but
the host writes `tasks.md`. A delegate that needs a file outside its manifest stops and names it.

**Siblings.** `S43-test-declarations` may add `TEST_SELECTION` declarations to `tests/` modules, and T001 **edits
`tests/test_verify_scoped_record.py`** and moves a class out of it: the host orders the two merges so the later one is
rebased over the other. `S26-reversibility-line` owns `check-decisions.py` and the cruise briefs: untouched here.

## Constraints that hold for every task

- **MINOR, `VERSION` stays `1.6.0.dev0`** (D171; `changelog.d/` already holds MINOR fragments). Every commit that changes
  `assets/` or `src/slipwai/` says `Level MINOR; VERSION already carries it; the fragment changelog.d/scoped-checks.md
  claims MINOR` (the fragment itself lands in T007); a commit that changes only `tests/` says it reaches no user.
- **Not edited by any task**: `VERSION`, anything under `release/`, the root `Makefile`, `delivery/`, `.github/`,
  `tools/`, `project.json`, `specs/*/decisions.md`, `spec.md`, `story-split.md`, `slices/README.md`,
  `scripts/check-decisions.py` and the cruise briefs (S26's), `tests/gate_audit.py`, the generated `Makefile` text and
  `rules.json` (AC-S07-13: no task may move the digests `tests/test_scoped_targets.py` pins), `verify-stamp.py`.
- **Size and width.** Every file under `tests/`, `src/` and `scripts/` stays <= 350 lines (`tests/test_verify_scoped_record.py`
  is **350 now**, `src/slipwai/project/scoped_targets.py` 225) and 120 columns; name a new test file rather than grow one.
  Toolkit assets are not counted by `check-structure`.
- **Tests.** Standard library; a fake is a class or script written in the test tree, **never `unittest.mock`**. A test
  that loads a toolkit script sets `sys.dont_write_bytecode = True`; a probe importing an `assets/` script runs as
  `python3 -B`. Every `read_text`/`open` in a toolkit script names `encoding="utf-8"`; every `subprocess.run` carries
  `timeout=`. A generated project's commands run with CI markers (`CI`, `GITHUB_ACTIONS`, `GITLAB_CI`), make state
  (`MAKEFLAGS`, `MFLAGS`, `MAKELEVEL`, `MAKEOVERRIDES`, `MAKEFILES`), `VERIFY_FORCE` and the `GIT_*` state variables
  stripped unless the example sets them (reuse `tests/scoped_fixture.py` and `tests/stamp_fixture.py`, never edit them).
- **RED is seen** for its stated reason before production code is touched. A **hold** (passes today) is written as a
  hold and seen to have **teeth** — change the production file, watch the failure, `git checkout -- <that exact path>`.
- **The toolkit set.** Every task touching `assets/toolkit/` also runs
  `make test TESTS="test_toolkit test_utf8_io test_changelog test_assets_bytecode"`; T005 and T006 (`check-ux-gates`
  changes how it calls git and reads the environment) also `test_verify_stamp_scan`. Call it **TK** below.
- **Before each commit** `make lint typecheck check-structure`, and test `$?` (never chain a commit after a pipe).
  Commit by path: `git commit -m … -- <the task's files>`, new files `git add`ed by exact path first.
- **The machine is reserved** until the host says it is free: no test is run before then. *(Released by the host
  before T001.)*
- **AC-S07-15 (D188), from T005 on.** Every test module a task adds or edits carries a `TEST_SELECTION` declaration in
  the same commit, added to the `real_*` list `tests/test_select_tests_real_declared.py` requires and held with a
  planted-fault case per declared axis — or, where the selector cannot state its reach (it imports an undeclared helper
  such as `scoped_fixture`, `stamp_fixture` or the test module `test_scoped_targets`, or loads a script by `importlib`
  without naming it), the module goes under *Undeclared modules* below with the selector's reason. The modules T001–T004
  committed before D188 are T008's.

## Phase 1: Implementation

### T001 — The four have rows; existence is an input; a row with no files is no recorded inputs (R1 + R4 + R5 · AC-S07-2, -5, -6, -7, -10)

R4 is folded in: its whole GREEN is two entries (`{web}`, `specs/`) of R1's table edit, so a task of its own would have
a RED and no GREEN beside R1's.

**First, inside this task (a refactor from green to green, before any RED):** move `TableHeldTest` and its helpers
(`reads_of`, `covered`, `modules_of`, `candidates`, `NOT_AN_INPUT`, `ROOT_OWN`) **verbatim** out of
`tests/test_verify_scoped_record.py` into new `tests/test_verify_scoped_table_held.py`; run both modules and see the
same tests pass. Then:

**RED** — new `tests/test_verify_scoped_methods.py` (against a generated project's `verify-scoped.py record` and
`choose`), plus the two assertion changes in `tests/test_verify_scoped_record.py` (the four now have inputs, line ~112;
`check-ux-gates`' variables, line ~165 — the variables part waits for T006, so change only the first here):
- e1 TS service + web starter: the four listed with an input object, `claims: true`, `always: null`, `variables: []`,
  `schema` still 1, no new key.
- e2 `.specify/drive.json` changed alone: `check-agents` runs naming it, the other three skip. e3 `AGENTS.md` alone:
  `check-agents` and `check-extensions` run. e4 `.specify/presets/x/templates/constitution-template.md`:
  `check-speckit` and `check-constitution` run. e5 `specs/001-x/spec.md` added over the template constitution:
  `check-constitution` runs and fails as `make check-constitution` does.
- R4 e1 `apps/web/` deleted, `project.json` unchanged: `check-extensions` runs; R4 e2 a service's `src/` changed:
  `check-extensions` skipped; under `apps/` it claims nothing.
- R5 e1 a test table with a stand-in `Row()` (no files, no `always`): record shows `inputs: null`, `claims: false`,
  `always: "no recorded inputs"`; R5 e2 (hold, with teeth) `chmod 000 .specify/drive.json`: `check-agents` runs naming it.

**GREEN** — four rows in `table.py` exactly as plan R1 lists them (`variables: ()`, `claims` default); `check_entry` in
`record.py` treats a `Row` with no `files` and no `always` as the `row is None` case. The scan in
`test_verify_scoped_table_held.py` will now walk the four: every literal it raises that `--check` never reads (R-1:
`cruise.py`'s run files) goes into `NOT_AN_INPUT` with its reason (fails when stale, as today), so the class stays green.

**Files:** `assets/toolkit/scripts/verify_scoped/table.py`, `assets/toolkit/scripts/verify_scoped/record.py`,
`tests/test_verify_scoped_record.py`, `tests/test_verify_scoped_table_held.py` *(new)*,
`tests/test_verify_scoped_methods.py` *(new)*.
**Run:** `make test TESTS="test_verify_scoped_methods test_verify_scoped_record test_verify_scoped_table_held test_verify_scoped_choose test_scoped_targets"` and TK.
**Done when:** the listed examples pass; the moved class passes unchanged; no other S06 scoped module changes outcome.

### T002 — Paths a manifest or preset lists are inputs of `check-speckit` (R2 · AC-S07-3; D172 limit i)

**RED** — new `tests/test_verify_scoped_derived.py`: e1 a `.specify/integrations/*.manifest.json` listing
`.specify/scripts/bash/common.sh`, that file changed: `check-speckit` runs naming it; e2 the path listed only by the
base's manifest (the branch deleted the manifest): still runs; e3 a manifest `{`: the record shows `check-speckit`
`inputs: null`, `claims: false`, `always: "no recorded inputs"`; e4 a manifest listing `../outside` or `/etc/x`, an
empty key, a backslash, or no `files` map: the same; e5 a `preset.yml` declaring `file: ../../x`, or unreadable: the same.
Absent manifests add nothing.
**GREEN** — new `verify_scoped/methods.py` with `with_derived(checks, root, scope, base)` (manifests and presets part;
the path test of research R-3; base read with `scope.git_show` and `ls-tree`, as `with_named` does); `record.build`
calls it right after `with_named`. Derived directories end in one `/`, `files` stays sorted and de-duplicated.
**Files:** `assets/toolkit/scripts/verify_scoped/methods.py` *(new)*, `assets/toolkit/scripts/verify_scoped/record.py`,
`tests/test_verify_scoped_derived.py` *(new)*.
**Run:** `make test TESTS="test_verify_scoped_derived test_verify_scoped_methods test_verify_scoped_record test_verify_scoped_table_held"` and TK.
**Done when:** the examples pass; the T001 scan stays green with the derived paths.

### T003 — Paths an integration names are inputs of `check-agents` (R3 · AC-S07-4; D172 limit i)

**RED** — extend `tests/test_verify_scoped_derived.py` (split to a new `tests/test_verify_scoped_integrations.py` if it
nears 350): e1 claude installed, `CLAUDE.md` changed: `check-agents` runs naming it; e2 a harness with a hooks file,
that file changed: runs; e3 `.specify/integration.json` `{` or with neither key: `inputs: null`; e4 an installed row
whose `skillsDir` is `~/.hermes/skills`, or an unreadable `registry.json`: `inputs: null`; an unknown registry key adds
nothing; working tree and base both read (`installed_integrations`, else `default_integration`).
**GREEN** — `methods.with_derived` gains the integration part, reading `scripts/agents/registry.json` beside the
record's own scripts: `skillsDir`, `commandsDir`, `agentFile.dir` as directories, `contextFile` and
`hooks.projection.where` as files.
**Files:** `assets/toolkit/scripts/verify_scoped/methods.py`, `tests/test_verify_scoped_derived.py`,
`tests/test_verify_scoped_integrations.py` *(new, only if the split is needed)*.
**Run:** `make test TESTS="test_verify_scoped_derived test_verify_scoped_integrations test_verify_scoped_methods test_verify_scoped_table_held"` (drop a name that was not created) and TK.
**Done when:** the examples pass.

### T004 — The four are held to what they read (R6 · AC-S07-8; D172 limit ii)

A proof over T001–T003; kept as a task because R6 is a rule of the map and its GREEN is real: the test-tree machinery
below, and any row widening the audit exposes.

**RED** — new `tests/test_verify_scoped_held.py`, with its own audit wrapper (`open`, `os.listdir`, `os.scandir`,
`os.stat`, `os.lstat`; **not** an edit of `tests/gate_audit.py`): e1 every shape in `test_scoped_targets.SHAPES`, with an
integration and a manifest written in, each of the four commands run under the audit — every project path touched lies
under that shape's recorded inputs for the check, or is `project.json`, under `scripts/`, or git-ignored; e2 teeth —
drop `.specify/drive.json` from the row and e1 fails naming it; e3 the literal-path scan finds `models.py`, `drive.py`,
`cruise.py` and `project.py` under `check-agents`; e4 limit ii — a copy of the table marking `check-codegraph` claiming
with a script reading `registry.json` fails (today only `check-slice-scope`, always-run, reads it outside the four).
**GREEN** — the scan in `tests/test_verify_scoped_table_held.py` is taught to walk all four of `check-agents`' scripts
and to scan every claiming check's closure for `registry.json` and `.manifest.json`; widen a row or add a reasoned
`NOT_AN_INPUT` entry for what the audit finds. Seen-to-have-teeth is e2 and e4.
**Files:** `tests/test_verify_scoped_held.py` *(new)*, `tests/test_verify_scoped_table_held.py`,
`assets/toolkit/scripts/verify_scoped/table.py` (only if the audit proves a row too narrow).
**Run:** `make test TESTS="test_verify_scoped_held test_verify_scoped_table_held test_verify_scoped_record test_scoped_targets"` (TK if `table.py` changed).
**Done when:** every shape passes; both teeth fail when provoked and are restored.

### T005 — An explicit ref reads names NUL-separated and without renames (R8, explicit ref · AC-S07-12)

**RED** — new `tests/test_ux_gates_default.py` on `tests/test_ux_gates_scale.py`'s fake `node`/`npx` kit: e5 `slice/S1`
with `UX_GATES_SINCE=HEAD~1` keeps today's ref scoping (hold); e6 a stylesheet renamed that a preview still links by its
old name: the preview renders; e7 `screens/my page.html` changed: it renders (fails today: quoted or split names).
**GREEN** — `check-ux-gates.py`'s `changed_since` uses `git diff --name-only --relative -z --no-renames` and
`ls-files --others --exclude-standard -z`, split on NUL.
**Files:** `assets/toolkit/scripts/check-ux-gates.py`, `tests/test_ux_gates_default.py` *(new)*.
**Run:** `make test TESTS="test_ux_gates_default test_ux_gates_scale"`, TK and `test_verify_stamp_scan`.
**Done when:** e6 and e7 pass, e5 holds, `test_ux_gates_scale` is unchanged.

### T006 — `check-ux-gates` scopes by default on a slice branch; `all` renders everything (R8 default + R9 · AC-S07-11, -1, -9)

R9 and AC-S07-1's end-to-end example (R8 e9) are folded in: each is red until the default exists (a default-run key
and an `all`-run key differ only once the default does; a web `src/` change renders no preview only under it).

**RED** — extend `tests/test_ux_gates_default.py` (new `tests/test_ux_gates_borders.py` if it nears 350), and add
`tests/test_verify_scoped_methods_run.py` (end to end through `scoped_fixture.ShapeCase`): e1 `slice/S1`, one
preview's stylesheet changed: that preview's four gates and the app's directory gates render, one line names the base;
e2 `main`: every preview, *this is the trunk*; e3 `feature/x`, detached `HEAD`, `CI=1`, no `main`: every preview, each
with its reason; e4 `UX_GATES_SINCE=all` on `slice/S1`: every preview, the `all` line; e8 a commit on local `main` not
on `origin/main` touching a stylesheet, branch cut after it: renders; the existing "every preview" rule (script,
`init.py`, `package-lock.json`, `verify.yml`) holds for the default; **R9** a stamped green `make verify` with the
default is not reused by `UX_GATES_SINCE=all`, and the baseline's `UX_GATES_SINCE` digest differs, so a scoped run
selects `check-ux-gates` (holds, teeth: remove the variable from the row); **e9** a service `src/` change with a
baseline: the four and `check-ux-gates` named skipped; a web app `src/` change: `check-ux-gates` runs, its file gate
runs, no preview renders; AC-S07-9's `test_verify_scoped_ignored`, `-borders`, `-baseline` and `test_scoped_targets`
re-run unchanged. In `tests/test_verify_scoped_record.py` change the `check-ux-gates` variables assertion (line ~165);
in `test_verify_scoped_table_held.py` add the named list of *base modules* (the stamp, `check-slice-scope.py`,
`verify_scoped/`: loaded to find the base, not walked for `check-ux-gates`; reasons given, fails when stale — research
R-6), which T004's limit ii scan shares; hold that `check-ux-gates` on a slice branch opens only paths under its row,
`project.json`, `scripts/` or git's own directory, under T004's audit wrapper.
**GREEN** — `check-ux-gates.py`: the borders in the order of plan R8 (move to new `verify_scoped/since.py` if the file
passes ~470 lines), the base and changed set from `changes.changed(scope, base)` ∪ `changes.unpushed(...).paths` loaded
lazily as `verify-scoped.py`'s `Ground` does, the `all` value, the one-line messages verbatim from the data model;
`table.py` widens `check-ux-gates`' variables with `GITHUB_HEAD_REF`, `CI_COMMIT_REF_NAME`, `GITHUB_BASE_REF`,
`CI_MERGE_REQUEST_TARGET_BRANCH_NAME`. No change to `verify-stamp.py`.
**Files:** `assets/toolkit/scripts/check-ux-gates.py`, `assets/toolkit/scripts/verify_scoped/since.py` *(new, only if
needed)*, `assets/toolkit/scripts/verify_scoped/table.py`, `tests/test_ux_gates_default.py`,
`tests/test_ux_gates_borders.py` *(new, only if needed)*, `tests/test_verify_scoped_methods_run.py` *(new)*,
`tests/test_verify_scoped_record.py`, `tests/test_verify_scoped_table_held.py`.
**Run:** `make test TESTS="test_ux_gates_default test_ux_gates_borders test_ux_gates_scale test_verify_scoped_methods_run test_verify_scoped_record test_verify_scoped_table_held test_verify_scoped_held test_verify_scoped_ignored test_verify_scoped_borders test_verify_scoped_baseline test_scoped_targets"` (drop a name not created), TK and `test_verify_stamp_scan`.
**Done when:** the examples pass; S06's unchanged modules pass unchanged; the digests `test_scoped_targets` pins have not moved.

### T007 — The words and the release (R10 · AC-S07-14)

**RED** — a test in an existing module that reads the generated gates page (find it with
`grep -rln "SCOPED_PAGE\|UX_GATES_SINCE" tests`; add to `tests/test_scoped_targets.py` if it has room, else new
`tests/test_scoped_page.py`): e1 a generated project's gates page carries `UX_GATES_SINCE=all`, D171 rule 6's sentence
(*set `UX_GATES_SINCE=all` when a change the scope cannot follow — a script or asset a preview loads, a browser upgrade —
could alter a preview*), the slice-branch/CI/trunk statement and that a ref named `all` is passed as `refs/heads/all`.
`test_changelog` passes with `VERSION` unchanged (e2).
**GREEN** — `SCOPED_PAGE` in `src/slipwai/project/scoped_targets.py` (keep <= 350 lines), `docs/verification.md`
(`check-ux-gates` gates-table row and the scoped section), the docstring of `check-ux-gates.py`, and new
`changelog.d/scoped-checks.md`: first line `MINOR`, one bold lead sentence, a standalone **Catch-up.** paragraph saying
a slice branch now renders fewer previews and `UX_GATES_SINCE=all` renders them all.
**Files:** `src/slipwai/project/scoped_targets.py`, `docs/verification.md`, `assets/toolkit/scripts/check-ux-gates.py`
(docstring only), `changelog.d/scoped-checks.md` *(new)*, `tests/test_scoped_targets.py` or `tests/test_scoped_page.py`
*(new)*.
**Run:** `make test TESTS="test_scoped_targets test_scoped_page test_gates test_verify_stamp_page test_docs_index test_ux_gates_default"` (drop a name not created; add any test the grep names), TK.
**Done when:** the page test and `test_changelog` pass; no other page test changed outcome.

### T008 — Each test module S07 adds or edits is declared, or listed with the selector's reason (AC-S07-15 · D188)

Rides with implementation: T005–T007 declare their own modules in their own commits (constraint above); this task
covers what T001–T004 committed before D188 — `tests/test_verify_scoped_record.py` (edited),
`tests/test_verify_scoped_table_held.py`, `tests/test_verify_scoped_methods.py`, `tests/test_verify_scoped_derived.py`,
`tests/test_verify_scoped_held.py` — and checks T005–T007's at the end.

**RED** — for each module, run the selector's own reading (`scripts/select_tests/declarations.py`: `scan`, `held`,
`effective`) and decide: declarable (its imports are all declared helpers or none, its by-path reads can be named) or
not (the selector's reason). For a declarable module: add it to the right `real_*` test (`test_select_tests_real_loaders`
`READS` for a reads-only module, `test_select_tests_real_backends` `DECLARED` for a generating one) first and see
`test_select_tests_real_declared` and that `real_*` test fail; then a planted-fault case per declared axis (a copy of the
declaration that omits an option or a read the source uses fails the selector's check), as the existing `real_*` tests do.
**GREEN** — the `TEST_SELECTION` line in the module. A module that cannot be declared is written into *Undeclared
modules* below with the selector's reason, verbatim from `declarations`' own output (S43's committed list does not exist
on this branch; the host carries these rows onto it at the merge).
**Files:** the five modules above, `tests/test_select_tests_real_loaders.py`, `tests/test_select_tests_real_backends.py`,
and only if a planted-fault case needs a module of its own, `tests/test_select_tests_real_s07.py` *(new)*. Not
`tasks.md`: the delegate returns the undeclared rows and the host writes them.
**Run:** `make test TESTS="test_select_tests_real_declared test_select_tests_real_loaders test_select_tests_real_backends test_select_tests_real_helpers"` plus every module it declared.
**Done when:** every S07 module is declared and held, or listed below with its reason.

### T009 — `check-decisions` declares the reversibility list S26 makes it read (S26 converge O1, MEDIUM)

S26 (merging into `adopt-method` before S07) makes the toolkit's `check-decisions` also read `.slipwai/propagated` in a
generated project and `<delivery>/.written` in an adopted one, through a new `scripts/reversibility.py`. Without a row
entry a scoped run skips `check-decisions` after a change to the list alone. On this branch: `scripts/reversibility.py`
is under `scripts/`, so any change to it is already the full gate (`choose.unknown`, *it is a gate script*), and needs no
row entry; `<delivery>/.written` exists only in an adopted repository, whose `verify-scoped` is always the full gate
(D114 item 3), so it needs none either — both said in a comment on the row. `.slipwai/propagated` is added to
`check-decisions`' files now (it does not need S26's code to be declared).
**RED** — in `tests/test_verify_scoped_methods.py` (or a new module if it nears 350): the record's `check-decisions`
files include `.slipwai/propagated`; on a slice branch with a baseline, a change to `.slipwai/propagated` alone runs
`check-decisions` naming it (today: unclaimed, so the full gate).
**GREEN** — the entry in `table.py`.
**After the host rebases S07 onto S26's merge:** run `test_verify_scoped_table_held` (the literal-path scan then walks
`reversibility.py` and must find `.slipwai/propagated` covered; if it raises the `.written` literal, it gets a reasoned
`NOT_AN_INPUT` entry: adopted layout only, always the full gate there) and `test_verify_scoped_held`.
**Files:** `assets/toolkit/scripts/verify_scoped/table.py`, `tests/test_verify_scoped_methods.py`.
**Run:** `make test TESTS="test_verify_scoped_methods test_verify_scoped_record test_verify_scoped_table_held"` and TK.

### Undeclared modules (AC-S07-15; carried onto S43's AC-S43-7 list at the merge)

| Module | The selector's reason |
|---|---|
| `tests/test_ux_gates_default.py` | it imports `tests/test_design_extensions.py`, which declares nothing |
| `tests/test_ux_gates_borders.py` | it imports `tests/parallel_gate.py`, which declares nothing |
| `tests/test_verify_scoped_methods_run.py` | it imports `tests/parallel_gate.py`, which declares nothing |

## Phase 2: After acceptance (host tasks)

Both full gates on the final tip; the register row and benchmark close; the demo (`drive-hand`). Not delegated here.

## Parallel opportunities

- **Serial chain:** T001 -> T002 -> T003 -> T004 (`methods.py`, `record.py`, `table.py` and the moved
  `test_verify_scoped_table_held.py` are shared; T004 reads what T001–T003 produce).
- **[P] T005** may run beside T002–T004: its files (`check-ux-gates.py`, `tests/test_ux_gates_default.py`) are disjoint
  from theirs. It must follow T001 only if the host wants the tree green throughout; it does not read T001's output.
- **Not parallel:** T006 follows T001–T005 (it edits `table.py`, `test_verify_scoped_record.py`,
  `test_verify_scoped_table_held.py` and `check-ux-gates.py`, all touched earlier); T007 is last (it edits
  `check-ux-gates.py`'s docstring after T006). T001 and T006 both edit `tests/test_verify_scoped_record.py`: never at once.

## Phase list

Phase 1 Implementation (T001–T009; order T007, T009, then T008, from D188); Phase 2 After acceptance (host).

**Done:** T001 (`bf319cc`, `0af5588`), T002 (`d723281`), T003 (`6830517`), T004 (`a510c86`), T005 (`daef4d8`), T006 (`048e3c7`; the default lives in new `verify_scoped/since.py`, which reads git's `changed_files` for the tree and `changes.raw_differs` only for the previews, their stylesheets and the four every-preview files, so the audit hold stays true).

## Differences from plan.md

- **R4 folds into T001** (two row entries; no GREEN of its own). **R9 and R8 e9 fold into T006**: each is red only until
  the default exists, so separate tasks would be holds over T006's behaviour. R7's re-runs are Done-when lines, not tests.
- **The scan work moves earlier than the plan places it.** Once T001 gives the four rows, `TableHeldTest` stops skipping
  them (it skipped null `inputs`), so T001 must keep it green with reasoned `NOT_AN_INPUT` entries (research R-9); T004
  extends it; the *base modules* list belongs to T006, where `check-ux-gates` first loads the stamp and `verify_scoped/`.
- The plan's single `test_verify_scoped_held.py` stays; two optional splits (`-integrations`, `-borders`) are named for the
  350-line rule.

## Design review

No screen in this slice.

## Convergence
