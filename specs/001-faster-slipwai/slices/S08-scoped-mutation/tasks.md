# Tasks: S08-scoped-mutation — a slice's mutation run is proportional to its change

**Input**: [plan.md](plan.md) (*Rules* 1–9 are what the tasks cut on; *Structure Decision*; *Pin*; *Open questions*),
[research.md](research.md), [data-model.md](data-model.md) (*The invocation*, *Change set*, *Classification*, *Service
outcome*, *The words* — the words are fixed there and tested verbatim), [quickstart.md](quickstart.md); acceptance
criteria AC-S08-1 … AC-S08-19 in `specs/001-faster-slipwai/spec.md` under `### S08-scoped-mutation`; decisions D137,
D138, D139 (this slice's) and D117, D125, D133 (S06's, cited, not re-decided) in `specs/001-faster-slipwai/decisions.md`;
ADR 0005. No `examples.md`: a method slice with no screen and no event model of its own, so **no white box, no mockup task
and no styling task**. The one story is **US2** (FR-006, FR-008 as D137 amends it, SC-007, scenario 6), *a mutation run is
priced per change where a tool is wired, and says so where it is not*.

**Branch**: `slice/S08-scoped-mutation`, worktree `/home/noahc/math/slipwai-graph-S08-scoped-mutation`. One commit per
task. No push, no claim.

**Delegation**: one `drive-implement` delegate takes US2 — T002 … T009 in dependency order — or more than one where the
manifests below are disjoint (*Parallel opportunities*). Each task is one RED-GREEN-REFACTOR cycle and one commit and
opens with **one rule's examples**; a delegate never writes a rule's tests ahead of the previous rule's commit. A task's
*Files* line is its manifest, the only files that delegate may write. Nobody but the host writes `tasks.md`. A delegate
that needs a file outside its manifest — a test elsewhere that pins text it changes — **stops and names the file; the
host adds it.**

**Not tasks:**
- **AC-S08-19** (plan rule list, last line; quickstart *Demo measurement*) is the demo's (T013): `make mutation` against
  `make mutation-full` on a two-service Go starter and on the Spring starter, wall time and mutant counts, is measured by
  the hand after the converged verdict. A task for it would be a test that cannot fail.
- **Rule 8 (AC-S08-14, the stamp is untouched) is folded into T006** (rule 5), not cut on its own. Its GREEN would be empty
  as a task: research R7 reads `verify-stamp.py`'s `EXEMPT` as already holding `gremlins.json` and `target/`, the Go run
  stages outside the project, and the script sets `sys.dont_write_bytecode`. The behaviour it guards is produced by the
  scoped runs of T005 (Go) and T006 (Spring), so its examples sit in T006, after both exist. If one of them fails for a
  reason a cache row would cure, the row is T006's GREEN (the only case `verify-stamp.py` is in a manifest).
- No white box: `check-model` has nothing to refuse. *Design review* below says so.

## Constraints that hold for every task

- **MINOR, `VERSION` stays `1.6.0.dev0`.** `cat VERSION` reads `1.6.0.dev0`; `changelog.d/` already holds MINOR fragments
  (`scoped-gate.md`, `parallel-gate.md`, …), so a MINOR fragment leaves the number as it is (`tests/test_changelog.py`
  checks the pair). **`changelog.d/scoped-mutation.md` lands in T002** — the first commit that changes a user-visible tree
  — as a first draft whose first line is `MINOR`, one bold lead sentence and one paragraph beginning `**Catch-up.**` that
  stands alone; T009 completes it. No other task touches it. Shape: `changelog.d/README.md`. A commit that changes
  `src/slipwai/` or `assets/` says `Level MINOR; VERSION already carries it (1.6.0.dev0); the fragment
  changelog.d/scoped-mutation.md claims MINOR` and the reason (`make mutation` scopes on a slice branch; a new
  `mutation-full` target; a new toolkit script); a commit that changes only `tests/` says it reaches no user.
- **Write scope of the whole slice** (every manifest stays inside it): `specs/001-faster-slipwai/slices/S08-scoped-mutation/`,
  `src/slipwai/project/mutation.py`, `src/slipwai/project/native_commands.py` (mutation entries only),
  `src/slipwai/project/makefile.py` (only the `mutation-full` rule and its `.PHONY` word),
  `assets/languages/go/scripts/go-mutation.py`, the new `assets/toolkit/scripts/mutation-scope.py`,
  `assets/toolkit/scripts/verify-stamp.py` (cache/ignore rows only, and only if a test proves one is needed),
  `assets/toolkit/skills/mutation-testing/SKILL.md`, `tests/`, `docs/`, `changelog.d/scoped-mutation.md`.
  **Never edited:** `rules.py`, `scoped_targets.py`, `commands.py`, `parallel_slices.py`, `agents.py`, `verify-scoped.py`,
  `check-slice-scope.py`, `verify_scoped/*` (S06's — loaded by path, read, never written), `decisions.md`, `spec.md`,
  `story-split.md`, `delivery/`, the root `Makefile`, `tools/`, CI, `VERSION`, anything under `release/`. A delegate that
  finds one of them needs a change stops and names it.
- **No new Makefile variable, `export` or `define`** (ADR 0005, D133): the new rule spells only `$(MAKE)` and
  `$(firstword $(MAKEFILE_LIST))`, which `verify-scoped`'s own recipe already uses; `SINCE` is read from the environment
  (research R5). `verify`, `verify-checks`, `ci` and the generated CI workflow stay byte for byte (AC-S08-13).
- **Size and width.** Every file under `src/` and `tests/` stays within 350 lines and 120 columns. Current:
  `makefile.py` **334** (T002 adds the `mutation-full` rule — three lines — and one `.PHONY` word: net ≤ 4, so ≤ 338; no
  helper, no comment block longer than two lines), `native_commands.py` **318** (T002 nets ≤ 8: `native_commands()` renames the
  merged `mutation` recipe to `mutation-full` and takes the scope line from `mutation.py`'s builder; **no per-backend
  entry in the dicts above it changes**), `mutation.py` **253** (T002 adds the builder, ≤ 12 lines; T009 rewrites notes
  and command text and must end ≤ 330 — a note is shortened rather than the file split, and a delegate that cannot make
  it fit stops and names it, because a new `src/` file is outside the slice's write scope), `tests/test_mutation.py`
  **295** (T009 edits it in place for the lines the new words replace and adds no example to it; every new example goes in
  a new file). A new test file that nears 350 splits by example and the report names the new file. Assets are not counted
  by `check-structure`, but `mutation-scope.py` is one file by the plan and stays readable: small named functions, no
  class beyond the `Runner` seam and the data-model's shapes. `go-mutation.py` is 352 lines already; T005 keeps its net
  growth ≤ 15 and does not reformat it.
- **Assets.** Every `read_text`/`open` in an asset script names `encoding="utf-8"`. No literal `apps/service` or
  `apps/web` in a new script (`toolkit.spoken_for` rewrites those). `sys.dont_write_bytecode = True` before any sibling
  import. `mutation-scope.py` loads `verify-scoped.py` and `check-slice-scope.py` by path (research R6) and writes
  nothing under the project.
- **Tests.** Standard library only; **no mocking framework, `unittest.mock` included.** Where a test needs the tool
  not to run, a **fake class written in the test tree** implements the script's `Runner` seam (data-model; research R4);
  the `--make` argument is the seam for the sweep and is a fake executable written into the temp directory that logs
  its arguments. **Real `git` in temporary repositories** (`git init`, `slice/S1`, a `main` ref) — never a stubbed
  diff. A test that loads an asset script as a module sets `sys.dont_write_bytecode` first (the helper in
  `tests/test_mutation.py` is the model, imported or copied, not edited here). Evidence is a log, a file or an exit
  status, never a clock. **Every `subprocess.run` carries `timeout=`.** A test that runs a generated project's command
  removes `CI`, `GITHUB_ACTIONS`, `GITLAB_CI`, `MAKEFLAGS`, `MFLAGS`, `MAKELEVEL`, `MAKEOVERRIDES`, `MAKEFILES` and
  `SINCE` from the environment unless the example sets it. Projects are generated with **this worktree's `./slipwai`**
  (`FactoryTestCase.generate` in `tests/support.py` does; a hand run says `./slipwai generate …`, never the one on
  `PATH`). Scratch only under `/tmp/s08/`.
- **Real runs are slow and few.** Exactly one real starter run per wired backend: Go in T005 and Spring in T006, each
  `skipTest`ed unless `backends_under_test()` (`tests/support.py`, the gate `tests/test_matrix.py`'s Go mutation test
  uses) names the backend, and the Spring one also unless a JDK and the project's `mvnw` are runnable. Every other example
  fakes the `Runner`.
- **Probes** that import a script under `assets/` run as **`python3 -B`**, so no `__pycache__/` is left under `assets/`.
- **Commit by path** — `git commit -m … -- <the task's files>`, a new file `git add`ed by its exact path first; never
  `git add -A`, never `git commit -a`, never `git checkout --` on work that is not the delegate's own (the sanctioned
  RED/teeth route in `delivery/docs/delegated-agent-safety.md` is the only one).
- **RED is seen** for its stated reason before the production file is touched. A **hold** (an example that passes today)
  is written as a hold, said so in its name or docstring, and **seen to have teeth** before commit: change the
  production file, observe the failure, restore with `git checkout -- <exact path>`. A hold with no teeth is not claimed.
- **GREEN is a class**, not an instance: where a rule says *every service* or *every backend*, the examples run a
  two-service project and the backends the rule names.
- **Before each commit** run `make lint typecheck check-structure`. **Do not run `make verify`** — the host runs the
  suites that read a generated gate once, in T010.

### The sweep at planning

`tests/` searched for helpers that rebuild or pin a generated Makefile's `mutation` recipe or `.PHONY` line
(`grep -rn "mutation" tests`, `grep -rln "\.PHONY" tests`, `grep -rn "re\.\(sub\|compile\|search\|match\)" tests | grep -i make`).
**Hits**, each met by the task named (none is edited by a task that does not list it in *Files*):

| Hit | Pins | Met by |
|---|---|---|
| `tests/test_monorepos.py:103, :126` | every shape's Makefile contains `mutation:`; a Go shape's recipes contain `python3 scripts/go-mutation.py apps/service` | hold, **T002**: both stay true (`mutation:` stays; the line moves into `mutation-full`); no edit expected, named if one is needed |
| `tests/test_matrix.py:110–170` (`test_a_go_service_importing_a_workspace_module_is_mutation_tested`) | real `make mutation` and `make mutation SINCE=HEAD` on a Go starter; asserts `scoped to 1 changed file(s) since HEAD: health/health.go` and `KILLED … at health/health.go` in the output | watch, **T002/T003**; **T005** edits it (the scope line the script prints is data-model's; Go's own line from `go-mutation.py` is kept under it) — it is in T005's manifest and is the Go real run's home beside the new file |
| `tests/test_mutation.py:50–109` | `mutation_notes` text (`Wired up: Gremlins`, `make mutation SINCE=`), `mutation_command(["go"])` says `make mutation SINCE=<review-base>`, and `assertNotIn("SINCE", mutation_command(["typescript"]))` | **T009** amends exactly these lines (the last is inverted by D139: every backend now names `SINCE`); T002's builder adds no text they read |
| `tests/test_mutation.py:168+` (`go-mutation.py` argument and `changed()` tests) | the script's `--since`, `mutable()`, `scope()` | hold, **T005**: `--since` stays as published; new `--file` examples go in a new file |
| `tests/test_adopted_manifest.py:51, :132` | wrapped applications' `mutation` is `None` in the manifest | hold, **T002**: the rename happens in `native_commands()`'s merged result, after the per-service dicts these read |
| `tests/test_layout.py:165` (`make -s help` in an adopted layout) | the help listing | watch, **T002/T003**: `mutation-full` appears in help; the adopted listing gains it |
| `tests/test_verify_scoped_rules.py`, `_sum.py`, `_walks.py`, `_prune.py`, `_run.py`, `tests/test_scoped_targets.py`, `tests/test_scoped_adopted.py`, `tests/test_scoped_migrate.py` (S06's rules-hold over every starter shape; `.PHONY` pins at `_rules.py:81`, `_sum.py:31`, `_adopted.py:99`) | `rules.json` from-text equals from-database; a fresh slice branch is not broadened; verify-scoped on an adopted layout | **T002** adds its own hold over the same shapes (new file) and runs these suites read-only; none is edited |
| `tests/test_verify_stamp_pinned.py:136, :147` | `.PHONY: verify ci` followed by the exact `verify` rule bytes | hold, **T002**: the new `mutation-full` word goes on the `.PHONY` line of the *test* section (`… adversarial mutation mutation-full audit`), not on `verify ci`'s |
| `tests/test_factory_repository.py:114, :220` | no `language == "go"`-style comparison in `src/slipwai`; the factory's own root `Makefile` `verify` recipe | hold, **T002, T009**: any new `src/` code goes through `backends_of`/`family_of`, never `backend == "go"` |
| `tests/test_backend_obligations.py` | **names no `mutation` text and rebuilds no Makefile** (grep finds none; it reads obligations by backend) | no edit; named so nobody searches again |
| `tests/test_factory_gate_stamp.py:262` | `make help` of the factory's own repository | out of reach — the root `Makefile` is not generated |
| `tests/test_changelog.py` | the fragments' highest level against `VERSION` | hold: MINOR on `1.6.0.dev0`, in every commit that touches `changelog.d/` |
| `tests/test_commands.py:60`, `tests/test_scoped_ladder.py:25` | the ladder says `/mutation`; the mutation gate sentence | hold: **T009** changes `mutation_command()`'s text only, not the ladder |

## Format: `[ID] [P?] [Story] Description` — each task is one increment, one commit

`[P]` marks a task whose files are disjoint from every sibling it could run beside; see *Parallel opportunities*.

---

## Phase 1: Implementation stage

Each task starts from the green committed suite.

### T001 — Pin: the generated Makefile and gate before anything moves (host task)

- [x] **Host task; no story; no commit.** *(Done 2026-10-05 at `2007688`: 67 tests OK, 1 skipped, 54 s. `make starters` not run here — the change is user-visible by construction, and T016's `build/` diff is the host's.)* Run the pin set once and record that it is green:
  `make test TESTS="test_mutation test_monorepos test_verify_stamp_pinned test_verify_scoped_rules test_scoped_targets test_scoped_adopted test_layout test_adopted_manifest test_changelog"`.
  Then `make starters` and keep `build/` aside (untracked) so T016's diff of that tree is the change a user sees
  (`docs/maintaining.md`): a `Makefile` with a new rule, one new script, a changed Go script, a changed command text.

### T002 — [US2] Two targets: `mutation` is one script line, `mutation-full` is today's recipe (R1 · AC-S08-11, AC-S08-13)

- [x] *(Done at `67c454f`.)* **Rule 1.** Creates `scripts/mutation-scope.py` with only the argument parser and the delegation, so the target is
  never wrong in between: `mutation-scope.py --make <make> --makefile <file> <backend>:<path> …` runs
  `<make> --no-print-directory -f <file> mutation-full` and exits with its status; every later rule changes the script,
  none changes the recipe line. First commit that changes a user-visible tree, so the fragment's first draft lands in it
  (first line `MINOR`; a **Catch-up.** paragraph that stands alone: a project made before gains `make mutation-full`, the
  scoped `make mutation` and `scripts/mutation-scope.py` after `slipwai migrate`; CI, the trunk and `SINCE` behave as before; T009 completes it).

**RED** (new `tests/test_mutation_targets.py`; `FactoryTestCase.generate`; read the Makefile text and the make database
with `make -npq -f Makefile .DEFAULT`, which runs nothing):
- e1 a Go project, a Go + Go (two services) project, a Spring project, and a TypeScript, a Python and a Quarkus project:
  `mutation:` has exactly one recipe line, `@python3 scripts/mutation-scope.py --make "$(MAKE)" --makefile
  "$(firstword $(MAKEFILE_LIST))" <backend>:<path> …` with one `<backend>:<path>` per service in service order (`go:apps/service
  go:apps/billing`) *(fails today: `mutation` holds the merged tool recipe)*.
- e2 the same shapes: `mutation-full:` exists, carries a `## …` description, appears in `make help`, is in the `.PHONY`
  line, and its recipe lines are **byte for byte** the pre-slice `mutation` recipe (the expected text is built from
  `native_commands.commands_of` per service, in the test, not copied from the new code) *(fails today: no such target)*.
- e3 **hold**: `verify`, `verify-checks`, `ci`, the generated `.github/workflows` files and `Makefile` text before the
  test section are byte for byte `makefile()`'s pre-slice output for every shape of e1 and `test_verify_stamp_scan.SHAPES`
  *(teeth: add `mutation` as a prerequisite of `verify-checks` and see it fail)*; `mutation` and `mutation-full` are
  reachable from none of the three in the make database *(teeth: same edit)*.
- e4 **hold** (AC-S08-13, the rules half): in every shape of e1, `rules.json` from the generated Makefile's text equals
  `rules.json` from the make database (S06's own reader, loaded by path, not edited), and on a `slice/S1` branch of a fresh
  project with a one-file source change `make verify-scoped` is not the full gate for any reason naming `mutation` or a
  variable *(teeth: add a global `MUTATION_X := 1` to the generated text and see the full gate chosen)*.
- e5 the delegation: the script, run with a fake `--make` executable in the temp directory, calls it once with
  `--no-print-directory -f <makefile> mutation-full`, passes its exit status through (0 and 7), and with an unknown
  `<backend>` or no service argument exits 2 with a one-line message *(fails today: no script)*.
- e6 the script ships: `scripts/mutation-scope.py` is in a generated project (and in an adopted layout's
  `<delivery>/scripts/`), holds no literal `apps/service` or `apps/web`, and a `python3 -B` import leaves no `__pycache__/`.

**GREEN** — `assets/toolkit/scripts/mutation-scope.py` (parser, `Runner` seam declared but not yet used, delegation);
`native_commands.py`: `native_commands()` returns `mutation-full` = the merged recipe it returns today and `mutation` =
the line from `mutation.py`'s new `scope_command(services)`; `makefile.py`: the `mutation-full` rule beside `mutation`
and its word on the `.PHONY` line; `changelog.d/scoped-mutation.md` first draft.

**REFACTOR:** the `<backend>:<path>` spelling is written once, in `mutation.py`.

**Verify:** `make test TESTS="test_mutation_targets test_mutation test_monorepos test_verify_stamp_pinned test_verify_scoped_rules test_scoped_targets test_scoped_adopted test_layout test_adopted_manifest test_changelog"`, then
`make lint typecheck check-structure`. Commit by path; level line as above.

**Files:** `assets/toolkit/scripts/mutation-scope.py` (new), `src/slipwai/project/mutation.py`,
`src/slipwai/project/native_commands.py`, `src/slipwai/project/makefile.py`, `changelog.d/scoped-mutation.md` (new),
`tests/test_mutation_targets.py` (new), `tests/test_scoped_targets.py` (**`PRE_SLICE` hashes only**, added by the host at
implementation: `test_e5_hold_the_text_before_the_section_is_what_the_gate_was` hashes the Makefile above `# Scoped gate`,
which holds the `mutation` rule, its note and the `.PHONY` line; the sweep at planning missed the hash pin).

### T003 — [US2] The checkouts that sweep say so, then sweep (R2 · AC-S08-1, AC-S08-15)

- [x] *(Done at `e9d5274`.)* **Rule 2.** Needs T002 (the script and its delegation). The script loads `verify-scoped.py` beside it, asks its
  `Ground` and borders `ci`, `head`, `trunk`, `slice_branch`, `base`, `told` in that order (research R6; `idle` and
  `forced` are the stamp's and are not asked), catching what `reason()` catches; and reads `project.json`'s
  `layout.delivery` (R8). Everything past the borders is still the sweep.

**RED** (new `tests/test_mutation_borders.py`; real `git` in a temp project generated once per class, `slice/S1`, a `main`
ref; `--make` is the logging fake):
- e1 on `main`: first line `mutation: the sweep runs — this is the trunk (`main`)` (the border's own words, as
  `verify-scoped` prints them), then the fake `make … mutation-full` is called once; exit status is the fake's *(fails
  today: the script prints nothing)*.
- e2 `feature/x`; e3 a detached `HEAD`; e4 each of `CI`, `GITHUB_ACTIONS`, `GITLAB_CI` set on `slice/S1`; e5 `slice/S1` with
  no `main`/`master` ref (`has no usable base`); e6 a directory git cannot read (no `.git`); e7 `SINCE=` empty on
  `slice/S1` (`mutation: the sweep runs — SINCE is set and empty`): each prints its one line, then sweeps, status the fake's
  *(each fails today as e1)*. The order is verify-scoped's: where two hold, the first only is printed.
- e8 the order and the status: a fake `make` exiting 3 gives exit 3; a border check that raises is a sweep, not a crash.
- e9 an adopted layout (`project.json` with `layout.delivery` set): the line `mutation: this layout has no mutation scope —
  the recorded command runs`, then `mutation-full` through the project's `-f <delivery>/Makefile` *(fails today)*; and
  `make -f delivery/Makefile mutation` on a generated adopted repository reaches it (use S06's adopted fixture, imported).
- e10 **hold** (class): over every border e1–e7 no byte under the project changes (`git status --porcelain --ignored`
  before and after, `python3 -B`).

**GREEN** — `mutation-scope.py`: `sweep_reason(env, ground)` over the ordered borders, the `layout.delivery` read, the
`mutation: …` printer; the delegation of T002 stays the one exit.

**REFACTOR:** the borders are an ordered list, one reason each, as `verify-scoped` has them; no border is re-implemented.

**Verify:** `make test TESTS="test_mutation_borders test_mutation_targets test_scoped_adopted"`, then
`make lint typecheck check-structure`. Commit by path; level line as above.

**Files:** `assets/toolkit/scripts/mutation-scope.py`, `tests/test_mutation_borders.py` (new).

### T004 — [US2] What changed, and how it prints (R3 · AC-S08-7, AC-S08-9, AC-S08-10, AC-S08-12)

- [x] *(Done at `3d7328b`.)* **Rule 3.** Needs T003. The change set is `check-slice-scope.py`'s `changed_files(base)` through the same `Ground.scope`
  with `base` the merge-base or the commit `SINCE` resolves to (`git rev-parse --verify <ref>^{commit}`); classification
  is data-model's table **for `shared`, `deleted`, `test`, `production`, `other`** (the sweep classes are T008's); outcomes
  `scoped`, `skipped` and the words of *The words*. The tool run is behind the `Runner` seam; **the default runner is
  `refuse: no runner for <backend>`, exit 2, until T005/T006/T007 add theirs** — a transient state that can only fail,
  never pass, which is why this task's fake-runner examples are the proof and no real tool is started here.

**RED** (new `tests/test_mutation_change_set.py` and `tests/test_mutation_words_script.py`; `FakeRunner` is a class
in `tests/mutation_scope_fixture.py` (new) recording `(service, files)` and returning a set status; real `git`; Go and
Spring services are declared as `go:apps/service go:apps/billing` / `java-spring:apps/service` on the command line):
- e1 `slice/S1`, one changed `*.go` production file in `apps/service`, a second Go service untouched: first line `mutation:
  scoped to 1 changed file(s) since `main` at <short>: apps/service/health/health.go`, then `mutation: scope apps/service —
  health/health.go` and `mutation: skip apps/billing — no changed production file`, last line `mutation: 1 scoped, 0 swept, 1
  skipped, 0 refused; passed`; the fake saw one call *(fails today: only the sweep exists)*.
- e2 staged, unstaged and **untracked** production files are all in the set; a committed one is too (D138 item 2: the same
  `changed_files` `verify-scoped` uses) *(fails today)*.
- e3 only a `*_test.go` changed: `mutation: no mutant to run — only tests changed: <files>; `make mutation-full` is the
  run that measures them`, exit 0, the fake never called; only a README / `go.mod` / `pom.xml` (pitest block unchanged)
  changed: `no production file changed`, exit 0; only a deletion: the file is named `not mutated … deleted, no mutants`, `no
  production file changed`, exit 0 *(fail today)*.
- e4 a file under `packages/`: `mutation: not mutated packages/greeting/greeting.go — not mutated by this target`, exit 0, no
  service run for it; a renamed production file (`git mv`): the old path is `deleted`, the **new path** is the scope.
- e5 `make mutation SINCE=HEAD~1` on `main` scopes (first line ends `` since `HEAD~1`: … ``), also with `CI=1` set;
  `SINCE=nope`: exit 2, one line naming `nope`, no tool run, no sweep; the working tree and untracked files are included in
  a `SINCE` diff.
- e6 the failure rule: the fake returning 1 for one of two scoped services fails the run after **both** have run, the last
  line `…; failed: apps/service`, status the first non-zero in service order; `every changed production file is outside the
  tools' targets` is printed when the fake reports no file mutable (the Runner's `files` result is empty).
- e7 the class: the same e1 over a Python, a TypeScript, a Go + Go and a mixed project (declared backends only; the fake is
  used) — the words are identical (every line starts `mutation: `).
- e8 **hold**: the T003 sweeps and their one-line words are unchanged, and a `slice/S1` branch with **no** change is `no
  production file changed`, not a sweep *(teeth: make the empty set sweep and see it fail)*.

**GREEN** — `mutation-scope.py`: `change_set(base)`, `classify(path, services)`, `outcomes`, the printer, `main`'s order
(borders → set → classify → run → last line), the `Runner` protocol and the refusing default.

**REFACTOR:** classification is one function returning a class name; the printer is the only place a `mutation:` line is spelled.

**Verify:** `make test TESTS="test_mutation_change_set test_mutation_words_script test_mutation_borders test_mutation_targets"`, then
`make lint typecheck check-structure`. Commit by path; level line as above.

**Files:** `assets/toolkit/scripts/mutation-scope.py`, `tests/mutation_scope_fixture.py` (new),
`tests/test_mutation_change_set.py` (new), `tests/test_mutation_words_script.py` (new — the first/last/per-service lines
of e1, e5, e6, e7; name differs from T009's `test_mutation_words.py` so the two never share a file).

### T005 — [US2] Go: one changed file mutates that file only, the other service starts no Gremlins (R4 · AC-S08-2)

- [x] *(Done at `614836a`.)* **Rule 4.** Needs T004. `go-mutation.py` gains `--file <path within the module>` (repeatable): it skips its own
  `git diff` and feeds the files through the same `mutable()` and `scope()` it uses for `--since`, so `.gremlins.yaml`
  exclusions are carried back exactly as today (research R4); `--since` is unchanged. `mutation-scope.py`'s Go runner
  calls `go-mutation.py <path> --file …` (paths relative to the service) and reports a file the yaml excludes as `outside
  Gremlins' configured targets`. The one **real Go run** of the slice lives here.

**RED** (new `tests/test_go_mutation_file.py`: `go-mutation.py` loaded as a module with bytecode off, as
`tests/test_mutation.py` does; new `tests/test_mutation_scope_go.py`: the script with the fake `Runner`; and the real run
in `tests/test_mutation_scope_real_go.py`):
- e1 `go-mutation.py apps/service --file health/health.go` stages the service, hands Gremlins a scope of every other file
  excluded, and never runs `git diff` (a fake `git` first on `PATH` that fails when called) *(fails today: unknown
  argument)*.
- e2 `--file` repeated; `--file` and `--since` together: `--file` wins and the line says so; a `--file` the yaml's
  `exclude-files` names is dropped and named, not mutated; all files excluded prints `no mutant to run` and exits 0 *(fail
  today)*.
- e3 **hold**: `--since <ref>` behaves as before (the existing `test_mutation.py` examples stay green untouched; one new
  example asserts its output line is byte for byte) *(teeth: make `--file` the default path and see `--since` break)*.
- e4 script-level, two Go services, one changed production file in `apps/service`: the Go runner is called once with `apps/service`
  and the file, `apps/billing` is `skip … no changed production file` and its runner is **not** called (AC-S08-2's
  second half: no Gremlins starts for it) *(fails today)*.
- e5 a changed file excluded by `.gremlins.yaml` of its service: `mutation: not mutated apps/service/x.go — outside
  Gremlins' configured targets`, `no mutant to run — every changed production file is outside the tools' targets`, exit 0.
- e6 **real Go run** (gated by `backends_under_test()` and `go` on `PATH`, the way `test_matrix.py` gates Go): a generated
  two-service Go starter on `slice/S1`, one file edited in `apps/service`; `make mutation` prints the e1 words of T004,
  `apps/service/gremlins.json` names only that file, `apps/billing/gremlins.json` does not exist, exit 0. The existing
  `tests/test_matrix.py` Go test is amended (in this manifest) where the output it asserts moved: its `SINCE=HEAD` scoped
  line is now the script's `mutation: scoped to 1 changed file(s) since `HEAD`: apps/service/health/health.go` with
  Gremlins' own `KILLED … at health/health.go` unchanged *(fails today: no scoped line, both services mutate)*.

**GREEN** — `go-mutation.py` `--file`; `mutation-scope.py` Go runner (a `Runner` implementation, argv built in one function).

**REFACTOR:** `--since` and `--file` share one `files()` in `go-mutation.py`; net growth ≤ 15 lines.

**Verify:** `make test TESTS="test_go_mutation_file test_mutation_scope_go test_mutation_scope_real_go test_mutation test_matrix"`
(`FACTORY_BACKENDS=go` for the two real ones), then `make lint typecheck check-structure`. Commit by path; level line
as above.

**Files:** `assets/languages/go/scripts/go-mutation.py`, `assets/toolkit/scripts/mutation-scope.py`,
`tests/test_go_mutation_file.py` (new), `tests/test_mutation_scope_go.py` (new), `tests/test_mutation_scope_real_go.py` (new),
`tests/test_matrix.py` (only the Go mutation test's asserted lines).

### T006 — [US2] Spring: PIT mutates `Foo` and `Foo$*` within the pom's targets; nothing outside them starts Maven; the stamp is untouched (R5, R8 · AC-S08-3, AC-S08-4, AC-S08-14)

- [x] *(Done at `631e827`.)* **Rule 5, with rule 8's examples folded in** (see *Not tasks*). Needs T005 (the real Go run it also covers for
  AC-S08-14). The Spring runner reads `<targetClasses>` and `<excludedClasses>` of the `pitest-maven` plugin from the
  service's `pom.xml` and matches each changed class's fully qualified name with PIT's own glob rules (research R2:
  anchored, `*` any run including `.`, `?` one character, `$` and `.` literal, leading `~` a raw regex, `**.`); the
  command is the sweep's own plus `-DtargetClasses=<Foo>,<Foo$*>,…`, run in the service directory (R1); PIT's `No
  mutations found` on a scoped run is the line `mutation: no mutant to run in <path> — PIT found no code to mutate in
  <classes>; no report was written`, exit 0 (R3), every other non-zero exit is the run's. A pattern the script cannot read
  (`${property}` in a param, a `~` regex Python cannot compile, a pom that does not parse) makes that service's run the
  sweep, named with the file (D138 item 3, fail closed — the *sweep* classification itself is T008's; here the runner
  reports `unreadable` to it).

**RED** (new `tests/test_mutation_scope_spring.py`, fake `Runner` recording the argv it would run; new
`tests/test_pit_globs.py` for the glob; the real run in `tests/test_mutation_scope_real_spring.py`):
- e1 a changed `src/main/java/<pkg>/health/HealthStatus.java` inside `targetClasses`: argv is the sweep's argv plus
  `-DtargetClasses=<pkg>.health.HealthStatus,<pkg>.health.HealthStatus$*` — `Foo` and `Foo$*`, never `Foo*` — cwd the
  service *(fails today: no Spring runner)*.
- e2 two changed classes: both pairs in one comma-separated value; a class `FooBar` beside `Foo` is **not** matched by
  `Foo$*`; `package-info.java` and `module-info.java` are not production files.
- e3 a class outside `targetClasses`, one inside `excludedClasses`: named `mutation: not mutated <file> — outside PIT's
  configured targets`, the runner is **not** called, `no mutant to run — every changed production file is outside the
  tools' targets`, exit 0 (AC-S08-4).
- e4 the globs against research R2's table: `**.`, `*` across dots, `?`, `$` literal, `~` regex, anchoring (`events.Tag` does
  not match `events.TagQuery`) — each an example in `test_pit_globs.py`; an unreadable pattern / unparseable pom gives the
  runner's `unreadable` result naming the file.
- e5 the fake reports PIT's `No mutations found` text with exit 1: the run prints the no-mutant line and passes; any
  other exit 1 fails the run naming the service; a **sweep** (no scoped files) keeps `failWhenNoMutations` untouched — no
  `-DfailWhenNoMutations` is ever passed *(teeth: pass it and see e5 fail)*.
- e6 the pom's `<excludedClasses>`, `<targetTests>` and `*IT` exclusion are unchanged by the run: the pom is read, never
  written (the file's bytes and mtime-free hash before/after), and no new file appears in the service.
- e7 **real Spring run** (gated by `backends_under_test()` naming `java-spring` and a runnable `mvnw`/JDK, otherwise
  `skipTest`): a generated Spring starter on `slice/S1`, `HealthStatus` edited; `make mutation` mutates `HealthStatus` only
  (the `target/pit-reports/mutations.xml` names that class and no other), fewer mutants than the sweep's, exit 0 — this
  holds the `-DtargetClasses` override against the **pinned** plugin (research R1), so a new pin that stops honouring it
  fails here *(fails today: sweep)*.
- e8 **folded rule 8 — hold, AC-S08-14**: in the generated Go starter (T005's real-run project, a fake `Runner` that writes
  nothing is not enough, so this uses the real runs of e7 and T005's e6, same gating) and the Spring starter, with a
  reusable stamp and a scoped baseline recorded, after `make mutation` and after `make mutation-full` (a) `git status
  --porcelain --ignored` differs from before only by paths `.gitignore` already names, (b) `verify-stamp.py`'s ignored-files
  digest is what it was, (c) the stamp reuses and `make verify-scoped` is not broadened. *Teeth:* make the Spring
  runner write `pit-tmp/` in the service and see (a) fail. **If (a)–(c) fail for a real run, the cache/ignore row is this
  task's GREEN (RED seen first)**; if they pass, no row is added and the commit says so.

**GREEN** — `mutation-scope.py`: the Spring runner, `pit_glob`, the pom reader (stdlib `xml.etree`, `encoding="utf-8"`
where a file is opened), the no-mutations recognition; `verify-stamp.py` cache/ignore row **only if e8 proves one**.

**REFACTOR:** the pom is parsed once per service and handed to this runner and, later, to T008's comparison.

**Verify:** `make test TESTS="test_mutation_scope_spring test_pit_globs test_mutation_scope_real_spring test_mutation_scope_real_go test_verify_stamp_pinned"`
(`FACTORY_BACKENDS=java-spring` / `go`), then `make lint typecheck check-structure`. If `verify-stamp.py` was edited, also
`make test TESTS="$(ls tests | grep -E '^test_verify_stamp' | sed 's/\.py$//' | tr '\n' ' ')"` — the root `Makefile` runs
that file as this repository's own stamp — and say so in the report. Commit by path; level line as above.

**Files:** `assets/toolkit/scripts/mutation-scope.py`, `assets/toolkit/scripts/verify-stamp.py` (only if e8 proves a row),
`tests/test_mutation_scope_spring.py` (new), `tests/test_pit_globs.py` (new), `tests/test_mutation_scope_real_spring.py`
(new), `tests/test_mutation_stamp_untouched.py` (new — e8).

### T007 — [US2] Placeholders refuse with their setup message and name what they would mutate; a placeholder no longer stops a wired service (R6 · AC-S08-5, AC-S08-6)

- [x] *(Done at `0a33dd6`.)* **Rule 6.** Needs T006. TypeScript, Python and `java-quarkus` runners are refusals: a service with a changed
  production file prints `mutation: refuse <path> — <the placeholder's setup message>; the scope will apply once a tool is
  wired; it would mutate: <files>`, counts as `refused`, fails the run (status 2) after every service has run; an untouched
  one is `skip`. The setup message is the placeholder's existing one, read from `mutation.py` (single source —
  `native_commands`' strings for the three are unchanged), held by **the script's own table, checked equal in a test**
  to the text `service_commands(<backend>, …)["mutation"]` echoes today (host's choice at tasks: the Makefile line stays
  one short line and `native_commands.py` keeps its headroom). Recorded as a stub (Development Workflow) in the commit and, in T009, the fragment.

**RED** (new `tests/test_mutation_placeholders.py`; fake `Runner` for the wired side):
- e1 TypeScript service, a changed `src/…/x.ts`: `refuse apps/service — …` carrying the exact Stryker setup sentence the
  placeholder prints today, the *scope will apply* clause and the file; status 2; last line `0 scoped, 0 swept, 0 skipped,
  1 refused; failed: apps/service` *(fails today: the T004 default refuses without these words)*.
- e2 Python (`src/**/*.py`) with mutmut's message, and `java-quarkus` with pitest #1287's message: same shape.
- e3 mixed (AC-S08-6): a placeholder service first in service order, a Go service second; only the Go file changed:
  placeholder `skip`, Go runner called, status the Go runner's (0 and 1), the run completes — and with both changed,
  the Go service still runs and the run exits 2 (the first non-zero in service order).
- e4 an untouched placeholder is `skip` and the run passes; a placeholder with only a changed `*.test.ts` / `tests/` file
  is `no mutant to run — only tests changed`, not `refuse` (a test file is not a production file, research R9).
- e5 the class: R9's production/test split for each backend (`*.d.ts`, `*.test.*`, `*.spec.*`, `src/test/**`,
  `tests/**`, `_test.go`) as a table test over `classify`.
- e6 **hold**: the **sweep** is still today's: `make mutation-full` on a TypeScript project still `exit 2`s with the same
  text (generated Makefile text from T002's e2, not re-proved; one real `make mutation-full` call with CI unset on a
  TypeScript starter without `npm install`, `timeout=`) *(teeth: change a placeholder string)*.

**GREEN** — `mutation-scope.py`: the three placeholder runners (one function, three messages), the exit order.

**REFACTOR:** R9's file classes are one table keyed by backend, used by T004's `classify` and by this runner.

**Verify:** `make test TESTS="test_mutation_placeholders test_mutation_change_set test_mutation_targets"`, then
`make lint typecheck check-structure`. Commit by path; level line as above.

**Files:** `assets/toolkit/scripts/mutation-scope.py`, `src/slipwai/project/mutation.py` (only if the message source moves
there), `tests/test_mutation_placeholders.py` (new).

### T008 — [US2] What sweeps: configuration, the scripts, and the rule's own text (R7 · AC-S08-8)

- [x] *(Done at `5df8e61`.)* **Rule 7.** Needs T007 (and T006's pom reader). Classes `rule-text`, `scope-script`, `backend-script`, `config`
  of data-model's table, evaluated first in its order; each names its file in `mutation: sweep <path> — `<file>` changed` or
  the whole-run `the sweep runs — `<file>` changed`. The `pitest-maven` block of a service's `pom.xml` is compared **as
  parsed structure** at the base and in the working tree (a comment or another plugin's change does not sweep; a side that
  cannot be parsed does); `.gremlins.yaml` is a sweep on any status; `go-mutation.py` sweeps every Go service;
  `mutation-scope.py` or the `Makefile`'s `mutation` target line and recipe lines differing from the base sweep the whole run.
  A service swept runs its **sweep command**: Go's `go-mutation.py <path>`, Spring's `mvnw … mutationCoverage` without
  `-DtargetClasses`; a swept placeholder is `refuse` as before.

**RED** (new `tests/test_mutation_sweeps.py`; fake `Runner` recording whether it was asked for a sweep or a scope; real git
with the base commit holding the old pom / Makefile):
- e1 `apps/billing/.gremlins.yaml` changed (also added, also deleted): `sweep apps/billing — `apps/billing/.gremlins.yaml`
  changed`, only that service sweeps, the other still scopes to its file *(fails today: the yaml is a non-source file)*.
- e2 the pom's `pitest-maven` `<targetClasses>` edited: that service sweeps; a pom change **outside** the plugin, a comment
  or whitespace inside it, the plugin reordered among the others: no sweep (`other`, counted) *(the second half passes
  today, a hold with teeth: compare raw text and see it sweep)*; a pom unparseable at the base, or in the working tree:
  sweeps, naming the file (fail closed).
- e3 `scripts/go-mutation.py` changed: every Go service sweeps, a Spring one does not; `scripts/mutation-scope.py` changed,
  or the `Makefile`'s `mutation` rule text changed: first line `the sweep runs — `<file>` changed`, `mutation-full` runs,
  status its; a change elsewhere in the `Makefile` (another rule) does not sweep.
- e4 two causes at once (a yaml and a production file in the same service): the service sweeps once, naming the yaml; the
  production file is not additionally scoped; each file that caused it is named.
- e5 **hold**: T004's `SINCE` runs sweep on the same triggers (`make mutation SINCE=HEAD~1` with the yaml changed since
  that ref sweeps that service) — one reader of "changed".

**GREEN** — `mutation-scope.py`: the four sweep classes, `pitest_block(pom)` returning comparable structure or `None`, the
`Makefile` rule-text comparison, the swept-service command.

**REFACTOR:** classification's first four rows share one `is_sweep(path)` returning `(scope, file)`; no second diff is run.

**Verify:** `make test TESTS="test_mutation_sweeps test_mutation_scope_spring test_mutation_scope_go test_mutation_placeholders test_mutation_change_set"`,
then `make lint typecheck check-structure`. Commit by path; level line as above.

**Files:** `assets/toolkit/scripts/mutation-scope.py`, `tests/test_mutation_sweeps.py` (new).

### T009 — [P] [US2] The words: command text, notes, the skill, the docs, the fragment, and `migrate` (R9 · AC-S08-16, AC-S08-17, AC-S08-18)

- [x] *(Done at `df3f854`.)* **Rule 9.** Needs T002 (the target and the builder exist; the words describe what T003–T008 build, as the plan and
  data-model fix them, so this task does not read their code). Disjoint from T003–T008's manifests, so it may run beside them.
  Applies the open-question recommendations of the plan as written (1: `mutation-full SINCE=<ref>` still scopes Go, the words
  say `mutation-full` is the sweep *without* `SINCE`; 2: an empty `SINCE` under make 3.81 is assumed, said in the page);
  the host confirms or overturns before this task starts.

**RED** (new `tests/test_mutation_words.py`, new `tests/test_mutation_migrate.py`; `tests/test_mutation.py` amended only at
the lines the new words replace — :64–80 where they read the Go note, :96–109 where `mutation_command(["typescript"])`
must now contain `SINCE`):
- e1 `mutation_command(backends)` for **each** of the five backends and for a mixed list says: the bare `make mutation`
  scopes on a `slice/<id>` branch; `make mutation SINCE=<ref>` scopes anywhere, CI included; `make mutation-full` is the
  sweep; CI and the trunk get the sweep; and Phase 4 on `main` runs `make mutation SINCE=<the commit before the merge>` (D139)
  *(fails today: the SINCE sentence is Go-only)*. For a placeholder backend it also says the target refuses until a tool is
  wired.
- e2 each backend's note in `mutation_notes` says the same in its own words: Go's *Without SINCE it mutates the whole
  module* is gone and replaced; Spring's `failWhenNoMutations` paragraph names the scoped exception (no mutants to run is not
  a failure); the placeholders' notes say the scope applies once a tool is wired; the names of the service's own files
  (`apps/<name>/.gremlins.yaml`, `pom.xml`) still substitute and `__APP__` never survives.
- e3 `mutation-testing/SKILL.md`: the clean-tree sentence (the "Diff-scoped mutation intentionally covers committed branch
  changes only. Require a clean working tree …" bullet) is gone; the replacement says staged, unstaged and untracked
  production files are included and mutated and nothing is committed or stashed to run it (AC-S08-16); no other
  sentence of the skill is touched (a hold: the file equals the old one except that bullet).
- e4 `docs/backend-obligations.md` and every `docs/` page that names `make mutation` say `mutation` scopes on a slice
  branch, `mutation-full` sweeps, and that no gate runs either; the gates page of a generated project is unchanged.
- e5 the fragment `changelog.d/scoped-mutation.md`: first line `MINOR`; one **Catch-up.** paragraph that stands alone and
  says what `make mutation` does on a slice branch, that it is unchanged in CI, on the trunk and with `SINCE`, that
  `mutation-full` is the old behaviour, which backends still need a tool wired (TypeScript, Python, `java-quarkus`), and the
  recorded stub; `tests/test_changelog.py` holds.
- e6 `migrate` (AC-S08-18): a project generated by the commit before this slice's first (the same technique
  `tests/test_scoped_migrate.py` uses, **failing, never skipping,** where that commit is not in the clone) after `slipwai
  migrate` has `mutation-full`, the scoped `mutation`, `scripts/mutation-scope.py`, the changed `go-mutation.py` and a
  regenerated `rules.json`, and `make verify-scoped` on a slice branch of it is not broadened *(fails until T002's files
  exist; passes on this task's tip)*.

**GREEN** — `mutation.py` (notes, `mutation_command()`), `mutation-testing/SKILL.md`, `docs/…`, the fragment completed.

**REFACTOR:** the SINCE paragraph is built once in `mutation.py` and used by the command text and the notes.

**Verify:** `make test TESTS="test_mutation test_mutation_words test_mutation_migrate test_changelog test_commands test_scoped_ladder test_docs_index test_scoped_page"`,
then `make lint typecheck check-structure`. Commit by path; level line as above.

**Files:** `src/slipwai/project/mutation.py`, `assets/toolkit/skills/mutation-testing/SKILL.md`,
`docs/backend-obligations.md` (and any other `docs/` page naming `make mutation`: `docs/requirements.md`,
`docs/maintaining.md`, `docs/verification.md` — the delegate lists exactly the ones it edits), `changelog.d/scoped-mutation.md`,
`tests/test_mutation.py` (named lines only), `tests/test_mutation_words.py` (new), `tests/test_mutation_migrate.py` (new), `tests/test_scoped_targets.py` (`PRE_SLICE` hashes only — the notes above `mutation:` move them). Extended by the host at
implementation: `src/slipwai/project/makefile.py` (`mutation-full` gets its own `.PHONY` line beside its rule — the
test section's `.PHONY` line stays untouched, so `migrate`'s three-way merge no longer conflicts, as
`test_scoped_migrate`'s two-Python-service example showed) and `tests/test_mutation_targets.py` (its `.PHONY` regex).

---

## Phase 2: Host closing tasks

### T010 — Every suite that reads a generated gate, once, before the gates (host task)
- [x] *(Done at `3e7aa4f`: 775 tests OK, 1 skipped, 1441 s; lint, typecheck, structure green at T009.; re-run on the final tip `8e8c66d` after T018–T029: 803 tests OK, 1 skipped, 1419 s.)* After T009 is committed and the chain T002 … T008 is: `make test TESTS="$(ls tests | grep -E '^test_(verify_stamp|parallel_gate|model_|gate_|verify_scoped|scoped_|mutation)' | sed 's/\.py$//' | tr '\n' ' ') test_matrix test_commands test_commit_boundaries test_monorepos test_layout test_changelog"`, then `make lint typecheck check-structure`. Not `make verify`.

### T011 — Converge, passes as needed (host task)
- [ ] `drive-converge` over the slice's range; findings append as tasks below.

### T012 — After-converge gaps (host task)
- [ ] `drive-gaps` over the slice and the code it produced.

### T013 — The demo, with the measurement (host task; AC-S08-19)
- [ ] The hand runs quickstart scenarios 1–7 in a project generated by this worktree's `./slipwai`, and fills the *Demo
  measurement* table: `make mutation` against `make mutation-full` on a two-service Go starter (one file changed) and on the
  Spring starter (one class changed), wall time, mutant counts, machine. The Phase 1 real runs (T005 e6, T006 e7) are
  evidence for AC-S08-2/-3, not for this.

## Phase 3: Findings appended by converge and gaps

*Converge pass 1 (2026-10-05, range `c3c760b..8d66e29`).* Probes ran in a Go starter generated by this worktree's
`./slipwai generate gp --backend go --output /tmp/s08/conv --no-init --no-install --skip-checks`, on `slice/S1` cut from
its `main`, with `CI`, `GITHUB_ACTIONS`, `GITLAB_CI`, `MAKEFLAGS` and `MAKELEVEL` removed; scripts run as `python3 -B`.
The scratch is removed. No file of this worktree was mutated.

### T018 — [US2] HIGH · A change to the recipe that runs the tool sweeps, and the scoped run runs the recipe the project owns, for every wired backend (D138 item 3, AC-S08-8, Principle I · contradicts)
- [x] *(Done at `ca92129`.)* **The surface:** the tool invocation of every wired backend — Go's and Spring's — now lives in `mutation-full`'s
  recipe (`native_commands.py:126`, `:177`, moved there at `:318`), but the scoped run neither reads it nor watches it:
  `mutation_rule()` (`mutation-scope.py:179–191`) matches `mutation:` only, and the commands the script runs are its own
  literals — `go()` at `:310`, `Tools.sweep` at `:437–444`, `PIT` at `:389`. D138 item 3 makes "the `mutation` recipe's
  text" sweep every service *because* a change to how the tool is run makes a path-computed scope untrustworthy; after
  the split that recipe is `mutation-full`'s. And a project owns its Makefile (Principle I): an edit it makes to its
  `mutation-full` line (a Maven profile, `-DthreadCount`, an environment variable before `go-mutation.py`) is silently
  not what `make mutation` runs. Nothing holds the script's literals equal to the factory's recipes either
  (`test_mutation_scope_spring.py:35` pins `SWEEP` against itself; `test_mutation_placeholders.py:75–79` holds the
  placeholders, not the wired commands).
  **Reproduction:** in the Go starter on `slice/S1`, `sed` prefixed `mutation-full`'s Go line with `GOFLAGS=-tags=probe`
  and `apps/service/health/health.go` gained a comment line; the script run in process with a fake `Runner` printed
  `mutation: scoped to 1 changed file(s) since \`main\` at 481cd72: apps/service/health/health.go`, `mutation: scope
  apps/service — health/health.go`, `FAKE run go apps/service ['health/health.go']`, `mutation: 1 scoped, 0 swept, 0
  skipped, 0 refused; passed`, exit 0 — no sweep, and the edited recipe is not what ran.
  **Owed, as a class over both wired backends:** (1) the `rule-text` class (data-model *Classification*) covers the
  `mutation-full` rule's target and recipe lines as well as `mutation`'s, so a change to either sweeps the whole run
  naming `Makefile` — an example per wired backend (Go two-service, Spring), and a hold that a change elsewhere in the
  Makefile still does not sweep (`test_mutation_sweeps.py:152` extended); (2) a factory test that the script's Go command
  (`go-mutation.py <path>`) and Spring command (`PIT`) are the generated `mutation-full` recipe's for each wired backend,
  with teeth (change `native_commands.py:177`, see it fail, restore). Whether the scoped run should instead *derive* its
  command from the project's `mutation-full` recipe is a design choice the host may take instead of (2); it is not
  required by the criteria. Files: `mutation-scope.py`, `tests/test_mutation_sweeps.py` (or a new file), a new factory hold
  file; `data-model.md`'s `rule-text` row says "`mutation` or `mutation-full` rule". MINOR already carried.
  **Host decision (triage of pass 1):** both (1) and (2), and a third, so the class closes on the trunk as well as on the
  branch: (3) before scoping, the script reads the *current* `mutation-full` rule's recipe lines from the Makefile text
  (unexpanded) and compares them with the lines the factory writes for the services it was handed, in order, deduplicated
  as `merged()` does (placeholders included). A recipe that is not the factory's — whether the trunk or the branch changed
  it — makes the whole run the sweep through `make mutation-full`, with the first line `the sweep runs — \`mutation-full\`'s
  recipe is not the one the factory wrote, so it runs as written`. The factory test of (2) becomes: for every starter shape
  `tests/test_mutation_targets.py` generates, the script's reconstruction equals the generated `mutation-full` recipe
  (teeth: change `native_commands.py:177`, see it fail, `git checkout --` it). Files add `tests/test_mutation_targets.py`
  (or the new hold file) and `data-model.md` (*Classification* and *The words*: the new first-line reason).
  **Manifest extended by the host at implementation:** `tests/mutation_scope_fixture.py`, `tests/test_mutation_scope_go.py`,
  `tests/test_mutation_scope_spring.py`, `tests/test_mutation_placeholders.py` — each run site commits the `mutation-full`
  recipe of the services it hands the script, so its scoped example stays scoped (the check is not weakened). Wrapped
  applications are left out of the reconstruction on purpose: they exist only in an adopted layout, which never scopes.

### T019 — [US2] MEDIUM · A whole-run sweep under `SINCE` is a sweep for every backend, Go included (D138 items 3–4, AC-S08-8, AC-S08-12 · partial)
- [x] *(Done at `e830b3a`.)* **The surface:** every whole-run sweep cause that can co-occur with a set `SINCE` — `scope-script` and `rule-text`
  (borders are not asked under `SINCE`; an empty `SINCE` already sweeps Go). `main` raises `Sweep` and `full()`
  (`mutation-scope.py:125–128`, `:541–545`) runs `make mutation-full` with `SINCE` still in the environment and in
  `MAKEFLAGS`, so Go's line `$(if $(SINCE),--since $(SINCE))` scopes Go by its own `git diff` while the first line says
  `the sweep runs`. The per-service sweep under `SINCE` is a true sweep (`test_mutation_sweeps.py:171`, `Tools.sweep`), so
  the two sweep paths disagree, and the whole-run one is the one D139's Phase 4 command reaches after a `migrate` that
  changed the script or the rule.
  **Reproduction:** in the Go starter on `slice/S1`, one line appended to `scripts/mutation-scope.py`, then
  `SINCE=main python3 -B scripts/mutation-scope.py --make <a fake make that echoes its arguments and SINCE> --makefile
  Makefile go:apps/service` printed `mutation: the sweep runs — \`scripts/mutation-scope.py\` changed` and `FAKEMAKE
  args: --no-print-directory -f Makefile mutation-full | SINCE=main`; `SINCE=main make -n --no-print-directory
  mutation-full` printed `python3 scripts/go-mutation.py apps/service --since main` — a scoped Go run under a sweep line.
  **Owed:** the delegation for a whole-run cause runs `mutation-full` with `SINCE` cleared for the sub-make — on its
  command line (`SINCE=`), since a `make mutation SINCE=<ref>` puts it in `MAKEFLAGS` where the environment does not
  reach — for both causes, under `SINCE` from the environment and from make's command line, with the fake `--make`
  recording what it received; the adopted layout's no-scope path keeps the recorded command as it is (AC-S08-15) and is
  held so. Plan *Open question 1* (a person typing `make mutation-full SINCE=<ref>` keeps Go's scope) is untouched.
  Files: `mutation-scope.py`, `tests/test_mutation_sweeps.py` or `tests/test_mutation_borders.py`.

### T020 — [US2] MEDIUM · The first line and the per-service lines say what the run did, in every outcome where no service is scoped (data-model *The words*, AC-S08-4, AC-S08-12 · contradicts)
- [x] *(Done at `499bcb7`.)* **The surface:** the first line of data-model's set, over every outcome in which a production file changed but no
  service ends `scoped`: (a) every changed file outside the tool's targets — Go's `.gremlins.yaml` exclusion, Spring's
  `targetClasses`/`excludedClasses`; (b) a wired service whose configuration cannot be read (`Result.unreadable`); (c)
  only placeholder services changed; (d) Spring's PIT *No mutations found*. The first line is decided at
  `mutation-scope.py:471–479` from the classification alone, before any runner filters, so (a) opens `scoped to <n>
  changed file(s)` and puts data-model's first-line form `no mutant to run — every changed production file is outside the
  tools' targets` later (`:515–516`); and a wired service is announced `scope <path>` (`:497–498`) before the runner
  decides, so (a) names it `scope` and counts it `skipped`, and (b) names it twice, `scope` then `sweep` (`:501–503`),
  against *every service is named once* (AC-S08-12). The tests pin the late line with `assertIn`
  (`test_mutation_words_script.py:54`, `test_mutation_scope_spring.py:112`, `test_mutation_scope_go.py:69`), never as
  `lines[0]`.
  **Reproduction:** in the Go starter on `slice/S1`, one comment line appended to `apps/service/cmd/migrate/main.go`
  (excluded by `.gremlins.yaml`'s `cmd/.*`), the script run with its real runner printed, in order: `mutation: scoped to
  1 changed file(s) since \`main\` at 481cd72: apps/service/cmd/migrate/main.go` · `mutation: scope apps/service —
  cmd/migrate/main.go` · `mutation: not mutated apps/service/cmd/migrate/main.go — outside Gremlins' configured targets`
  · `mutation: no mutant to run — every changed production file is outside the tools' targets` · `mutation: 0 scoped, 0
  swept, 1 skipped, 0 refused; passed`, exit 0. With `python:apps/service`
  and an untracked `apps/service/src/x.py`: first line `mutation: scoped to 1 changed file(s) …`, then `refuse
  apps/service — …`, `0 scoped, 0 swept, 0 skipped, 1 refused; failed: apps/service`, exit 2.
  **Owed, as the sweep of (a)–(d):** the runner's intersection (Go's `mutable()`, Spring's target match, the readability
  of the pom) is decided for every service before the first line is printed, so the first line is the data-model form the
  outcome is — (a) `no mutant to run — every changed production file is outside the tools' targets` as `lines[0]`; (b)
  each service named once, as `sweep` with its reason; (c) and (d) — data-model has no form for them: the host either
  confirms `scoped to <n>` for them in data-model's words or names the form (a words decision, handed back, not chosen
  here). One example per outcome with `lines[0]` asserted and a count of each service's lines; Go's own
  `mutation: scoped to <n> given file(s)` line from `go-mutation.py` under it is out of this task (tasks *The sweep at
  planning*, `test_matrix.py` row). Files: `mutation-scope.py`, the four test files named, `data-model.md` if (c)/(d) gain
  a form.
  **Host decision on (c) and (d):** both keep the first line `scoped to <n> changed file(s) since <base>: …` — the scope was
  computed and is true; (c)'s per-service `refuse` line and (d)'s `no mutant to run in <path> — PIT found no code to mutate
  in …` say why nothing ran. `data-model.md` *The words* says so in one sentence.

### T021 — [US2] MEDIUM · Each wired and placeholder backend's note says what the command text says (AC-S08-17 · partial)
- [x] *(Done at `d3e0e63`.)* **The surface:** the three notes `mutation_notes()` emits above the target (TypeScript and Python carry none, held
  deliberately by `test_mutation_words.py`'s e2 hold — that reading is not reopened here). AC-S08-17: *each backend's note
  above the target in `mutation.py` says the same* as the command text — bare target scopes on a slice branch, `SINCE=<ref>`
  anywhere, `mutation-full` is the sweep, CI and the trunk get the sweep, Phase 4 on `main` runs `make mutation SINCE=<the
  commit before the merge>`. Go's note (`mutation.py:86–94`) lacks Phase 4; Spring's (`:193–196`) lacks *CI and the trunk
  sweep* and Phase 4; Quarkus's (`:166–168`) lacks `SINCE`, *CI and the trunk*, and Phase 4. `NoteTest.test_e2_…`
  (`test_mutation_words.py`) asserts only `slice/<id>` and `make mutation-full` per note, so the gap is unpinned.
  **Reproduction:** `grep -n "Phase 4\|trunk\|SINCE" src/slipwai/project/mutation.py` — `Phase 4` only at `:246`
  (`SCOPING`, the command text); `trunk` at `:87`, `:89` (Go) and `:243–246`; `SINCE` in Go's note and Spring's, not
  Quarkus's.
  **Owed:** the note test asserts all five claims for each of `go`, `java-spring`, `java-quarkus` (one loop, the
  sentences as `CommandTextTest` spells them or each note's own words for them), and the three notes gain the missing
  clauses — a sentence each, `mutation.py` stays ≤ 330 lines (279 now). Files: `src/slipwai/project/mutation.py`,
  `tests/test_mutation_words.py`, `tests/test_scoped_targets.py` (`PRE_SLICE` hashes only — the notes sit above `# Scoped gate`). A generated Makefile changes, MINOR already carried; the fragment needs no new line.

*Converge pass 2 (2026-10-05, range `d216e5b..9b17d5f`).* Probes ran in a Go starter generated by this worktree's
`./slipwai generate gp --backend go --output /tmp/s08/conv --no-init --no-install --skip-checks`, on `slice/S*` branches
cut from its `main`, with `CI`, `GITHUB_ACTIONS`, `GITLAB_CI`, `MAKEFLAGS` and `MAKELEVEL` removed; scripts run as
`python3 -B`; `make -n` reaches the script because its recipe names `$(MAKE)`. The scratch is removed. One file of this
worktree was mutated and restored (T018's teeth, below).

### T022 — [US2] MEDIUM · The first line is the outcome when tests change beside production files no tool takes (data-model *The words*, AC-S08-7, AC-S08-12 · contradicts; T020's class)
- [ ] **The surface:** the precedence of the first line in `scope()` (`mutation-scope.py:540–551`) over every outcome where
  no file is `named`: tests, `packages/` files, deleted production files and production files every tool leaves out, in
  each combination. T020 moved the *outside the tools' targets* form ahead of the per-service lines but put it after the
  `only tests changed` branch (`:545` before `:548`), so a run in which a production file changed outside Gremlins' or
  PIT's targets *and* a test changed opens with *only tests changed* — false, since a production file changed and is
  named `not mutated` two lines below. Before T020 the same run opened `scoped to 1 changed file(s)`; this is a
  regression T020 introduced. (`packages/` beside tests opens *only tests changed* too; that predates T020 and is the
  same surface.)
  **Reproduction:** in the Go starter on `slice/S1`, `// probe` appended to `apps/service/cmd/migrate/main.go` (excluded
  by `.gremlins.yaml`'s `cmd/.*`) and to `apps/service/health/health_test.go`; `python3 -B scripts/mutation-scope.py
  --make <fake> --makefile Makefile go:apps/service` printed `mutation: no mutant to run — only tests changed:
  apps/service/health/health_test.go; \`make mutation-full\` is the run that measures them` · `skip apps/service — no
  changed production file within the tool's targets` · `not mutated apps/service/cmd/migrate/main.go — outside Gremlins'
  configured targets` · `0 scoped, 0 swept, 1 skipped, 0 refused; passed`, exit 0.
  **Owed, as the sweep of the precedence:** *only tests changed* is the first line only when tests are the only source
  files that changed; a production file outside every tool's targets (with or without tests, `packages/` files or
  deletions beside it) opens *every changed production file is outside the tools' targets*; data-model says which form
  wins for `packages/` beside tests (a words decision the host settles, as T020's (c)/(d) were — not chosen here). One
  example per combination — {tests, `packages/`, deleted} × {an outside-targets file present, absent} — asserting
  `lines[0]`, for Go and for Spring. Files: `mutation-scope.py`, `tests/test_mutation_scope_go.py`,
  `tests/test_mutation_scope_spring.py`, `tests/test_mutation_words_script.py`, `data-model.md` if a form is settled.

### T023 — [US2] MEDIUM · A recipe the project owns runs as written under `SINCE`, or the words say it does not (AC-S08-10, AC-S08-18 catch-up, D138 item 4 · contradicts; decision handed back)
- [ ] **The surface:** every whole-run sweep cause under a set `SINCE` whose reason is not the factory's own files —
  today only `NOT_FACTORY` (`mutation-scope.py:76`, raised at `:619`). T019 clears `SINCE` for every whole-run sweep
  (`:622`, `full()` at `:135`), which is right for `scope-script` and `rule-text` (the sweep is the trustworthy run), but
  the `NOT_FACTORY` first line says the recipe *runs as written*, and it does not: the project's own
  `$(if $(SINCE),--since $(SINCE))` is emptied. So `make mutation SINCE=<ref>` in a project whose `mutation-full` recipe
  differs from the factory's — by an edit made on the trunk long ago — now runs a whole-module Gremlins sweep where the
  same command before this slice ran Go scoped by `--since`; the fragment's catch-up says "with `SINCE=<ref>` Go scopes
  as it did" (`changelog.d/scoped-mutation.md:5`), and D139's Phase 4 command on `main` becomes a sweep for every such
  project.
  **Reproduction:** in the Go starter, `mutation-full`'s line prefixed `GOFLAGS=-tags=probe ` and committed on `main`,
  a slice cut from it and `health.go` edited; `make -n --no-print-directory mutation SINCE=HEAD` printed `mutation: the
  sweep runs — \`mutation-full\`'s recipe is not the one the factory wrote, so it runs as written` then `GOFLAGS=-tags=probe
  python3 scripts/go-mutation.py apps/service ` — no `--since HEAD`, which the written recipe would have passed.
  **Owed, a decision first (Principle XIV — handed back, not chosen):** either (i) the `NOT_FACTORY` sweep keeps `SINCE`
  for the sub-make (the recipe runs exactly as written; `scope-script`/`rule-text` keep T019's clearing), or (ii) it
  clears it and the first line and the catch-up say so (`… so it runs as written, without \`SINCE\``; the catch-up's "Go
  scopes as it did" gains "unless `mutation-full`'s recipe is not the factory's"). Then one example per source of `SINCE`
  (environment, make's command line) for the chosen behaviour, the fake `--make` recording what it received. Files:
  `mutation-scope.py`, `tests/test_mutation_recipe.py`, and under (ii) `data-model.md` and `changelog.d/scoped-mutation.md`.

### T024 — [US2] LOW · The published words name every whole-run sweep cause T018 added (AC-S08-8, AC-S08-18 · partial)
- [ ] **The surface:** every published place that lists what makes `make mutation` sweep — the fragment
  (`changelog.d/scoped-mutation.md:3`, "or the `mutation` rule"), the command text (`SCOPING`, `mutation.py:246–252`),
  the Go and Spring notes, `mutation-testing/SKILL.md`. None says that a change to `mutation-full`'s rule, or a
  `mutation-full` recipe that is not the factory's, makes the whole run the sweep — and the notes now point at
  `mutation-full` as the place the tool's invocation lives, so a project that tunes it there loses scoping and learns it
  only from the run's first line.
  **Reproduction:** `grep -rn "factory wrote\|mutation-full\` rule" changelog.d/scoped-mutation.md
  src/slipwai/project/mutation.py assets/toolkit/skills/mutation-testing/SKILL.md` finds nothing.
  **Owed:** one clause in the fragment's paragraph and catch-up, and in `SCOPING`, naming both causes; `CommandTextTest`
  asserts it. Files: `changelog.d/scoped-mutation.md`, `src/slipwai/project/mutation.py`, `tests/test_mutation_words.py`,
  `tests/test_scoped_targets.py` (`PRE_SLICE` hashes only, if a note moves). MINOR already carried.

### T025 — [US2] LOW · A scoped service's line names the files its tool takes, and the recipe check reads the target line's prerequisites (AC-S08-12, D138 item 3 · partial)
- [ ] **The surface:** (a) the `scope <path> — <files>` line (`mutation-scope.py:579`) lists every changed production file
  of the service, including those the plan leaves out, while the first line counts only the kept ones; (b) the
  `NOT_FACTORY` comparison (`:618`) reads `mutation-full`'s recipe lines only (`[1:]`), so a prerequisite the trunk added to
  its target line (`mutation-full: tools ## …`) — part of how the sweep runs — is neither compared nor run by the scoped
  run (on a branch, `rule-text` already catches an edit to that line).
  **Reproduction (a):** in the Go starter on `slice/S3`, `health/health.go` and `cmd/migrate/main.go` edited, the script
  run with `Tools` whose `run` is faked printed `scoped to 1 changed file(s) … : apps/service/health/health.go` then
  `scope apps/service — cmd/migrate/main.go, health/health.go`, then `not mutated apps/service/cmd/migrate/main.go`. (b)
  is read from the source, not run.
  **Owed:** (a) the scope line names `plan.keep`, the `not mutated` lines the rest, held by one Go and one Spring example;
  (b) the target line's prerequisites are compared with the factory's (none), a trunk-added prerequisite sweeping with
  the `NOT_FACTORY` line, one example. Files: `mutation-scope.py`, `tests/test_mutation_scope_go.py`,
  `tests/test_mutation_scope_spring.py`, `tests/test_mutation_recipe.py`.

### After-converge gaps (2026-10-05, `drive-gaps`, range `c3c760b..1db94ad`, read only)

Every AC-S08-1..18 has a holding test (trace in the gaps report); these are what T022–T025 miss. Each is a task; the host
recommends T026 and T027 land before the demo (a silent green, and a dry run that runs the tool). **Host (coordinator), after
the gaps:** T026, T027, T028 and T029 land before the demo; T030–T032 and T022–T025 stay for Phase 4.

- [x] *(Done at `403548c`.)* **T026 — HIGH · A project in a git subdirectory reports `no mutant to run` for a changed production file, exit 0
  (G1; AC-S08-2, AC-S08-8, priority 5).** `check-slice-scope.changed_files` gives tracked paths from the repository top
  (`sub/apps/…`) and untracked ones from the project (`check-slice-scope.py:511`, `:515`); `classify` and `sweep_causes`
  (`mutation-scope.py:273–281`, `:322–332`) match project-relative roots, so a committed or modified change is `other`
  and a changed `Makefile` or scope script does not sweep. Repro: a Go starter at `outer/sub`, git at `outer`,
  `slice/S1`, `// probe` appended to `sub/apps/service/health/health.go` → `no mutant to run — no production file
  changed`, `0 scoped, 0 swept, 1 skipped`, exit 0. **Owed, as the class:** every path the script compares (the change
  set, the `Makefile`, the scope and backend scripts, each service's config, `git show <base>:<path>`) is made
  project-relative through the stamp's `project_prefix()` — or the prefix is a border that sweeps with its reason — with
  a tracked and an untracked example. Files: `mutation-scope.py`, `tests/test_mutation_change_set.py` or a new file.
- [x] *(Done at `699ebec`, amended at `8e8c66d`.)* **T027 — MEDIUM · `make -n mutation` on a slice branch runs the tool (G2; AC-S08-1).** The recipe names
  `$(MAKE)`, so make runs it under `-n`/`-q`/`-t`; the script never asks verify-scoped's `idle` border, and the scoped
  path starts `go-mutation.py`/`./mvnw` itself. Repro: `make -n mutation` with `health.go` edited printed `scope
  apps/service — …` and reached `go run … unleash`. **Owed:** honour `idle` — print the plan and run nothing on every
  path (scoped, per-service sweep, whole sweep, refusal) — with an example under `MAKEFLAGS=n` for each.
- [x] *(Done at `ec59223`.)* **T028 — MEDIUM · The skill's commands collect committed changes only (G4; AC-S08-16, D138 item 2).**
  `SKILL.md:84` and `:132` (`git diff <base>...HEAD`) contradict the rewritten `:89`. **Owed:** the section's commands
  include the working tree and untracked files (`git diff <merge-base>` plus `git ls-files --others --exclude-standard`),
  and the test reads the commands, not only the sentence.
- [x] *(Done at `eef52fa`.)* **T029 — MEDIUM · Python with mutmut on PATH is refused (G3; AC-S08-5, D137) — decided: D149, option (a).** The
  refusal and the fragment say a Python service is refused until `S42-mutmut-mutation` wires the tool, and that
  `make mutation-full` runs mutmut today where it is installed. Files: `assets/toolkit/scripts/mutation-scope.py`,
  `changelog.d/scoped-mutation.md`, `tests/test_mutation_placeholders.py`, `tests/test_mutation_words.py`. The
  question as handed back:
  `make mutation-full` still runs `mutmut run` where it is installed (`native_commands.py:102`); the scoped run refuses
  Python unconditionally (`mutation-scope.py:469–475`). The fragment's *until you wire a tool* names no step a project
  can take. Host recommendation: (a) keep D137's refusal and change the words — the refusal and the fragment say the
  scope refuses whether or not mutmut is installed, until `S42-mutmut-mutation` wires it, and `make mutation-full` runs
  what it ran; alternative (b) sweep a Python service when `mutmut` is on PATH (narrows D137's item 2).
- [ ] **T030 — LOW · A deleted Spring service whose Makefile was not regenerated raises a traceback (G5; AC-S08-12).**
  `stream()` (`mutation-scope.py:429`) raises `FileNotFoundError`; no closing line, the service not named. **Owed:** every
  runner (Go, Spring, sweep) on a missing service directory fails that service by name and the run closes.
- [ ] **T031 — LOW · States that work and nothing holds (G6).** A unicode path with a space; `SINCE` as an annotated tag,
  `refs/tags/…`, a full and a short hash, detached with `CI=1`; a Java rename keeping its new FQN (AC-S08-7); a rename
  across services; a Go + TypeScript shape in `test_mutation_targets.SERVICES`. **Owed:** an example each.
- [ ] **T032 — LOW · Tests that hold less than their criterion (G7).** AC-S08-3: assert `targetTests` and the `*IT`
  exclusion under `-DtargetClasses` in the real Spring run; AC-S08-13: the CI workflow byte for byte, not *no
  "mutation"*; AC-S08-14: a stamp written, then reused after `make mutation`, and `verify-scoped` from a scoped baseline
  not broadened; AC-S08-15: the adopted example sees the recorded command run.

### T033 — [US2] HIGH — A scoped Go run whose changed code no test reaches fails where the sweep passes (demo 1, `implementation`)

- [ ] **Finding** (drive-hand, demo 1, iteration 23; `demo/24-uncovered-scoped.log`, `demo/24-uncovered-full.log`). In the two-service Go starter on `slice/demo`, a new untested `func Degraded(failures int) bool` in `apps/service/health/health.go` gives `Killed: 0, Lived: 0, Not covered: 2 … Test efficacy: 0.00% … ERROR: below efficacy-threshold`, then `failed: apps/service`, exit 2; `make mutation-full` on the same tree passes (efficacy 100%) and `make test` passes. The project's `.gremlins.yaml` and the Makefile note promise *not covered* is reported and never fails the run. Gremlins scores zero tested mutants as 0% efficacy; the `SINCE=` path before this slice had the same flaw, and scoping by default makes every slice branch meet it. **RED:** a scoped run whose mutants are all not covered passes, naming the not-covered count; a scoped run with a lived mutant still fails. **GREEN — the class:** every scoped run judges by the same rule the sweep's configuration states, for every wired backend — Go's efficacy over zero tested mutants, and PIT's equivalent (`mutationThreshold` with zero covered) — and the words say what was not covered. **Also from the demo, LOW:** the Python refusal names the factory-internal `S42-mutmut-mutation` (say "until a later slipwai release wires mutmut"); the Go scoped line prints after Gremlins' output when piped (flush); `make help` does not say `mutation` scopes on a slice branch; a dry run ends "passed" (say "planned"); the quickstart's scenario 5 `SINCE=HEAD~1` sweeps because `add-service` rewrote the rule (reword the step). **Files:** `assets/languages/go/scripts/go-mutation.py` or `assets/toolkit/scripts/mutation-scope.py`, `src/slipwai/project/mutation.py`, `src/slipwai/project/native_commands.py`, the tests, `quickstart.md`.


## Phase 4: After acceptance (host tasks)

### T014 — The adversary pass (host task)
- [ ] `drive-adversary` over the script's reachable boundary (`make mutation` with hostile refs, paths with spaces and
  `$`, a rename plus config change, a pom with entities, `MAKEFLAGS` set).

### T015 — Mutation (host task)
- [ ] `drive-mutation` over `mutation-scope.py` and `go-mutation.py`'s `--file`; this slice's own scoped run is the first customer.

### T016 — Both full gates on the final tip (host task)
- [ ] `make verify` once, with the `build/` diff of T001: only the intended generated changes.

### T017 — Register row and benchmark close (host task)
- [ ] Slice register row, `benchmark.json`.

---

## Parallel opportunities

By manifest (each task's *Files* line):

| Task | Writes | Imports another task's file |
|---|---|---|
| T002 | `mutation-scope.py` (new), `mutation.py`, `native_commands.py`, `makefile.py`, `changelog.d/scoped-mutation.md`, `tests/test_mutation_targets.py` | none |
| T003 | `mutation-scope.py`, `tests/test_mutation_borders.py` | T002's script |
| T004 | `mutation-scope.py`, `tests/mutation_scope_fixture.py`, `tests/test_mutation_change_set.py`, `tests/test_mutation_words_script.py` | T003 |
| T005 | `go-mutation.py`, `mutation-scope.py`, `tests/test_matrix.py` (Go test), three new test files | T004's seam |
| T006 | `mutation-scope.py`, `verify-stamp.py` (only if proved), four new test files | T005 |
| T007 | `mutation-scope.py`, `mutation.py` (only if the message source moves), `tests/test_mutation_placeholders.py` | T006 |
| T008 | `mutation-scope.py`, `tests/test_mutation_sweeps.py` | T006's pom reader, T007 |
| T009 | `mutation.py`, `mutation-testing/SKILL.md`, `docs/…`, `changelog.d/scoped-mutation.md`, `tests/test_mutation.py`, two new test files | T002's builder and fragment |

- **The script chain is serial:** T002 → T003 → T004 → T005 → T006 → T007 → T008 each write `mutation-scope.py`, which the
  plan makes one file and the write scope allows to be one file; two worktrees would conflict, so **never two of them at
  once**. None of them is marked `[P]`: no manifest among them is disjoint from its neighbours', and each consumes the
  previous task's code.
- **The one `[P]`: T009.** Its files (`mutation.py`'s notes and command text, the skill, `docs/`, the fragment, `test_mutation.py`,
  two new test files) share none with T003–T008 (T007 writes `mutation.py` only if a message source moves — the delegate who
  runs T007 beside T009 does not move it, and says so), and no rule among T003–T008 depends on T009's code. It starts after
  **T002 is committed** (it needs the builder, the target and the fragment draft) and may run beside T003–T008: two
  delegates at once, the chain's current task plus T009, each in a worktree of its own off T002's commit
  (`isolation: worktree`); the host commits by path and resolves no conflict by hand — a conflict means a manifest overlap
  this table says there is none of.
- **May not:** T009 before T002; T003 … T008 in any order other than the chain's (T008 needs T006's pom reader; T006's
  folded stamp examples need T005's real Go run); two script-chain tasks together; T009's `test_mutation.py` edits beside
  T005's `tests/test_mutation.py` examples — T005 puts every new example in new files and does not edit `test_mutation.py`.
- **Host tasks:** T001 first, alone; T010 alone after T009 and T008; T011 … T017 follow in order.

## Design review

No screen in this slice

## Convergence

(the verdict that comes later)

### Pass 1 — 2026-10-05, range `c3c760b..8d66e29` — **not converged**

One HIGH re-opens the loop: **T018** (a change to the recipe that runs the tool does not sweep, and the scoped run does
not run the project's recipe). Three MEDIUM ship-without-able findings: **T019** (whole-run sweep under `SINCE` scopes
Go), **T020** (first line and per-service lines where nothing ends scoped), **T021** (the notes miss clauses of
AC-S08-17). No CRITICAL. The pin and the slice's suites were green at `3e7aa4f` (T010: 775 OK, 1 skipped); `8d66e29` adds
records only, so they were not re-run here. No code was mutated to prove a finding: each is reproduced by a run on a
generated starter or a read of the source, quoted in its task.

**Constitution, principle by principle:**

- **I — the scoped gate is additive.** Satisfied: `mutation` and `mutation-full` are reached from none of `verify`,
  `verify-checks`, `ci` (`src/slipwai/project/makefile.py:327–331` adds the rule beside `audit`, outside them; held by
  `tests/test_mutation_targets.py:132`); the rule spells only `$(MAKE)` and `$(firstword $(MAKEFILE_LIST))`
  (`src/slipwai/project/mutation.py:275–279`), and `rules.json` from text equals from database over every shape
  (`tests/test_mutation_targets.py:168`, teeth at `:183`); the stamp is untouched by a real Go and Spring run
  (`tests/test_mutation_stamp_untouched.py:59`, `:71`).
- **I — a generated project owns its files.** Satisfied in what is written: the pom and `.gremlins.yaml` are read, never
  written (`assets/toolkit/scripts/mutation-scope.py:356–370`, `go-mutation.py`'s `excluded()`); `migrate` carries the two
  targets, the script and a gate that is not broadened (`tests/test_mutation_migrate.py:42`). **Broken in spirit by T018:**
  the scoped run runs the factory's literals (`mutation-scope.py:310`, `:389`, `:437–444`), not the `mutation-full`
  recipe the project owns (`native_commands.py:126`, `:177`, `:318`).
- **I — `VERSION` and the fragment.** Satisfied: `changelog.d/scoped-mutation.md:1` claims `MINOR` on `1.6.0.dev0`;
  `:5` is a standalone **Catch-up.** that says what `make mutation` does on a slice branch, that CI, the trunk and an
  empty `SINCE` run `mutation-full`, what `SINCE=<ref>` now does, and which backends need a tool (AC-S08-18).
- **III — simplicity.** Satisfied: one stdlib script, no dependency, one `Runner` seam
  (`mutation-scope.py:45–48`), the borders and change set loaded from `verify-scoped.py`/`check-slice-scope.py` and not
  copied (`:78–96`). T018 is also the III cost of the duplicated tool commands.
- **V — GWT, one rule per increment.** Satisfied: T002–T009 one rule each, one commit each (`67c454f` … `df3f854`), real
  git in temporary repositories, no mocking framework (fakes in `tests/mutation_scope_fixture.py`), one real run per
  wired backend (`tests/test_mutation_scope_real_go.py`, `tests/test_mutation_scope_real_spring.py`). T020's tests pin the
  late line with `assertIn` rather than the first line — a V gap in the examples, owed there.
- **XIV — stop on a decision.** Satisfied: no name outside D137–D139's was invented; `--file` is research R4's plan
  decision on a factory script; data-model's first-line amendment is recorded as the host's (data-model *The words*).
  T020 hands its (c)/(d) words back rather than choosing them.
- **The stub record** (*Development Workflow*, `.specify/memory/constitution.md:532`). Satisfied: TypeScript, Python and
  `java-quarkus` refuse with their setup message (`mutation-scope.py:316–320`, `:414–420`, held equal to the factory's by
  `tests/test_mutation_placeholders.py:75–79`), recorded in `plan.md:55` and `changelog.d/scoped-mutation.md:5`
  ("which is a recorded stub").

**Level by level:**

- **The toolkit script's own logic.** *Proved:* classification order and kinds per backend (`mutation-scope.py:254–295`,
  `tests/test_mutation_change_set.py`), change set staged/unstaged/untracked and renames as D+A (`:14`, `:53`), borders
  and their words with the first-only rule (`tests/test_mutation_borders.py:109–192`), `SINCE` on any checkout, CI
  included, unresolvable ref status 2 naming it (`test_mutation_change_set.py:59–76`), config/backend-script/scope-script
  sweeps (`tests/test_mutation_sweeps.py`), status the first non-zero in service order. *Not proved / wrong:* the
  `rule-text` class misses `mutation-full` (T018); a whole-run sweep under `SINCE` is not a sweep for Go (T019); the first
  line and per-service lines where nothing ends scoped (T020).
- **Each backend's runner.** *Go* (`go-mutation.py --file`): proved by `tests/test_go_mutation_file.py` and the real run
  (`test_mutation_scope_real_go.py:39`); `.gremlins.yaml` exclusions carried back (reproduced: `cmd/migrate/main.go`
  named *outside Gremlins' configured targets*, no Gremlins started). *Spring* (`-DtargetClasses=Foo,Foo$*`): PIT's glob
  rules held by `tests/test_pit_globs.py`, the override's precedence over the pom held by the real run
  (`test_mutation_scope_real_spring.py:54`), outside-targets starts no Maven and exits 0, *No mutations found* is the
  no-mutant line. *Placeholders:* refuse, exit 2, with the setup message, the *scope will apply* clause and the files
  (reproduced for `python`); a wired service after one still runs (`tests/test_mutation_placeholders.py`). *Not proved:*
  that the wired commands are the generated recipe's (T018).
- **The generated Makefile and the factory code.** *Proved:* `mutation` is one script line per service in service order
  (`tests/test_mutation_targets.py:116`, seen in the probe: `@python3 scripts/mutation-scope.py --make "$(MAKE)"
  --makefile "$(firstword $(MAKEFILE_LIST))" go:apps/service`); `mutation-full` is the merged recipe byte for byte, in
  `make help` and `.PHONY` (`:121`; its `.PHONY` is its own line at `makefile.py:329`, the host's manifest extension);
  `native_commands.py:318–319` renames after the per-service dicts, so `test_adopted_manifest.py` holds. *Not proved:*
  nothing further at this level beyond T018.
- **The published contract.** *Proved:* `commands/mutation.md` text for every backend and for all five
  (`tests/test_mutation_words.py` `CommandTextTest`); the skill's clean-tree sentence replaced (AC-S08-16); the four
  `docs/` pages; the fragment's level and catch-up; `migrate` on an older project (`tests/test_mutation_migrate.py:42`).
  *Partial:* the notes above the target (T021). AC-S08-19 is the demo's (T013), not judged here.
- **Interplay with S06.** *Proved:* no new variable, `export` or `define`; `rules.json` equal from text and database;
  a fresh slice branch's `verify-scoped` not broadened, in a generated and a migrated project; the stamp's inputs and
  `git status --ignored` unchanged after a real scoped and full run; `verify-scoped.py`, `check-slice-scope.py` and
  `rules.py` loaded by path and not edited (`git diff --stat c3c760b..HEAD` names none of them). *Not proved here:* that a
  rebase onto S06's tip keeps the loaded names (research R6's named risk) — the rebase's own re-run owns it.

**Next:** T018 through `drive-implement`, then converge pass 2; T019–T021 ride with it or follow, at the host's call.
Converge pass 1 wrote only this file.

### Pass 2 — 2026-10-05, range `d216e5b..9b17d5f` (whole slice `c3c760b..9b17d5f`) — **converged**

No CRITICAL or HIGH remains, so nothing re-opens the loop. Every pass-1 finding is closed against HEAD and its sweep was
performed, except that T020's class has one combination left open (**T022**, MEDIUM — a regression T020 introduced). New
ship-without-able findings: **T022** MEDIUM, **T023** MEDIUM (a decision handed back), **T024** LOW, **T025** LOW. The
eight test files T018–T021 touched ran green at HEAD (`test_mutation_recipe`, `_sweeps`, `_words`, `_words_script`,
`_scope_go`, `_scope_spring`, `_placeholders`, `_targets`: 65 tests OK, 11 s); the full T010 set was not re-run here.

**Pass-1 findings, re-run against HEAD:**

- **T018 — closed; sweep performed.** (1) `mutation_rule()` is the `mutation` and `mutation-full` rules
  (`mutation-scope.py:206–208`); a branch edit to `mutation-full`'s Go line, in the generated starter through real make,
  printed `the sweep runs — \`Makefile\` changed` and ran the edited line — the pass-1 reproduction now sweeps. Held for
  Go two-service and Spring, and for the target line (`tests/test_mutation_recipe.py:54`, `:67`), with the elsewhere
  hold for both (`:75`). (2)+(3) `factory_recipe()` (`:211`) is compared with the current recipe before scoping (`:618–619`);
  a trunk-committed edit printed the `NOT_FACTORY` line on a branch, with and without `SINCE` (`:89`), and the trunk keeps
  its own border reason. The factory hold covers every shape `test_mutation_targets.py` generates
  (`tests/test_mutation_targets.py:133`); **teeth checked here:** `native_commands.py:177` given ` -DthreadCount=2`, the
  test failed on the Spring shape, file restored with `git checkout --`. Both wired backends covered; mixed-backend shapes
  are not among the generated ones (their lines are each backend's own, deduplicated as `merged()` does).
- **T019 — closed; sweep performed.** `full()` passes `SINCE=` on the sub-make's command line under a set `SINCE`
  (`:135`, `:622`); with real make, after a branch edit to `scripts/mutation-scope.py`, both `make -n mutation SINCE=main`
  and `SINCE=main make -n mutation` printed `python3 scripts/go-mutation.py apps/service` with no `--since`. Both causes ×
  both sources held (`tests/test_mutation_sweeps.py:182`); the adopted layout keeps the recorded command (`:198`). The
  `NOT_FACTORY` cause T018 added later inherits the clearing — whether it should is **T023**.
- **T020 — closed for (a)–(d); one combination open.** Each tool's `Plan` is decided before the first line
  (`mutation-scope.py:45`, `:485`, `:534–537`); the pass-1 reproduction (`cmd/migrate/main.go` only) now opens with *every
  changed production file is outside the tools' targets*; an unreadable pom is named once as `sweep` and opens *the sweep
  runs* (`test_mutation_scope_spring.py`'s `test_t020_an_unreadable_pom…`); (c) and (d) keep `scoped to` per the host's
  decision, written in `data-model.md` *The words*. Every test now asserts `lines[0]`. **Open:** tests changed beside an
  outside-targets file opens *only tests changed* (**T022**).
- **T021 — closed; sweep performed.** Go, Spring and Quarkus notes each carry the five clauses
  (`src/slipwai/project/mutation.py:86–94`, `:166–170`, `:196–200`); `NoteTest.test_e2_…` asserts all five per note
  (`tests/test_mutation_words.py:59–63`).

**Constitution, principle by principle:**

- **I — the scoped gate is additive.** Satisfied: neither target is reachable from `verify`, `verify-checks`, `ci`
  (`src/slipwai/project/makefile.py:327–331`; `tests/test_mutation_targets.py:142`); the fixes add no Make construct —
  `mutation` stays the one line at `src/slipwai/project/mutation.py:279–283`.
- **I — a generated project owns its files.** Satisfied, and pass 1's breach closed: a `mutation-full` recipe the project
  changed is what runs (`assets/toolkit/scripts/mutation-scope.py:618–622`), on the branch and from the trunk. The
  residue is **T023**: under `SINCE` the project's recipe runs with `SINCE` emptied.
- **I — `VERSION` and the fragment.** Satisfied for the level: `changelog.d/scoped-mutation.md:1` claims `MINOR`, which
  T018–T021 stay within. The fragment's list of sweep causes is short of T018's two (**T024**, LOW).
- **III — simplicity.** Satisfied: the T018 reconstruction is one 17-line function (`mutation-scope.py:211–228`) held
  equal to the factory's by a test rather than a second source of truth; T020's `Plan` splits each runner into plan and
  run without a new seam (`:485`).
- **V — GWT, one rule per increment.** Satisfied: one commit per task (`ca92129`, `e830b3a`, `499bcb7`, `d3e0e63`), real
  git and real make-shaped runs, fakes only (`PlanningRunner` in `tests/test_mutation_words_script.py`, `Recording`, the
  fake `--make`), `lines[0]` asserted where pass 1 found `assertIn`. T022's combination is an example the sweep missed.
- **XIV — stop on a decision.** Satisfied: T018 (3) and T020 (c)/(d) were the host's decisions and are recorded in
  `data-model.md`; this pass hands T023's choice and T022's `packages/` form back rather than choosing.
- **The stub record** (`.specify/memory/constitution.md:532`). Satisfied and unchanged: TypeScript, Python and Quarkus
  refuse with their setup message; `factory_recipe()` reconstructs their placeholder lines from the same `PLACEHOLDERS`
  the refusal uses (`mutation-scope.py:222–226`); `changelog.d/scoped-mutation.md:5` still names the stub.

**Level by level:**

- **The toolkit script's logic.** *Proved:* the rule-text class over both rules, the not-factory recipe check, `SINCE`
  cleared for whole-run sweeps, plans decided before the first line, an unreadable configuration named once. *Not proved
  / wrong:* the first line when tests change beside outside-targets files (**T022**); `SINCE` under the not-factory sweep
  (**T023**); the scope line's file list and target-line prerequisites (**T025**).
- **Go, Spring and placeholder runners.** *Go:* `go_plan`/`go` split, the excluded file named once and no Gremlins
  started, reproduced in the starter. *Spring:* `spring_plan` before the run, unreadable pom swept once, *No mutations
  found* keeps `scoped`. *Placeholders:* plan takes every file, refuse lines unchanged, only-placeholders keeps `scoped to`
  (`tests/test_mutation_placeholders.py`'s `test_t020_only_placeholders…`). Not re-run against real Gremlins or Maven
  here: the fixes change what is decided before the tool, not the tool command (held equal to the recipe by T018's test).
- **The generated Makefile and factory code.** *Proved:* the starter's `mutation` line and `mutation-full` recipe as
  pass 1 found them; the notes' new sentences above the rule; `PRE_SLICE` hashes updated in T021's commit. Nothing
  further owed at this level.
- **Published words and `migrate`.** *Proved:* the notes now say the five things (T021); `data-model.md` carries the new
  first-line form and the host's (c)/(d) sentence. *Partial:* the fragment and command text do not name T018's causes
  (**T024**); the catch-up's "Go scopes as it did" depends on **T023**'s decision. `migrate` was not re-probed: no fix
  touched what it carries beyond the script and the notes it already regenerates.
- **S06 interplay.** *Proved:* no fix touched `verify-scoped.py`, `check-slice-scope.py` or `verify_scoped/` (`git diff
  --stat c3c760b..HEAD` names none); no new variable, `export` or `define`. The rebase onto S06's tip (D140, the
  `PRE_SLICE` regeneration) is not this pass's to judge.

**Files mutated and restored:** `src/slipwai/project/native_commands.py` (line 177, T018's teeth), restored with
`git checkout -- src/slipwai/project/native_commands.py`. No `__pycache__` under `assets/`. Scratch `/tmp/s08/` removed.

**Next:** T013 (the demo) may proceed; T022–T025 ride before Phase 4 or after it at the host's call, T023 after its
decision. Converge pass 2 wrote only this file.

**Host, after pass 2 (2026-10-05):** the loop stops at its bound of two passes; no `CRITICAL` or `HIGH` is open, so the
slice is **converged at pass 2** and goes on to the after-converge gaps and then the demo. T022–T025 (`MEDIUM`, `LOW`) are
carried as Phase 4 work, ahead of the adversary pass, under these host decisions: **T023** — option (i): a `mutation-full`
recipe the factory did not write runs as written, `SINCE` included (plan *Open question 1*, the fragment's *Go scopes as
it did*); T019's clearing stays for the `Makefile`-changed and scope-script causes only. **T022** — `only tests changed`
opens a run only when no production file changed at all; a `packages/` file beside tests is named *not mutated by this
target* and the first line is `no mutant to run — no production file changed`.
