# Tasks: S42-mutmut-mutation — a Python slice's mutation run is real and proportional to its change

**Input**: [plan.md](plan.md) (*Rules* 1–11 are what the tasks cut on; *Source Code*; *Structure Decision*; *Pin*;
*Applied, not decided*; *Handed back*), [research.md](research.md) (R1–R9), [data-model.md](data-model.md) (`[tool.mutmut]`,
`targets`, `matched`, `refused`, `versions`, `.meta`, the exit-code table, the wrapper's lines and status, what sweeps a
Python service, the scope script's tables — the words are fixed there and tested verbatim), [quickstart.md](quickstart.md);
acceptance criteria AC-S42-1 … AC-S42-13 in `specs/001-faster-slipwai/spec.md` under `### S42-mutmut-mutation`; decisions
D212, D216 (this slice's), D137, D138, D149, D150, D219, D222 (cited, not re-decided) in
`specs/001-faster-slipwai/decisions.md`; ADR 0010 (`delivery/docs/adr/0010-mutmut-for-python-mutation.md`, already
written, `Proposed`). Precedent read for shape: `slices/S41-stryker-mutation/tasks.md`. No `examples.md`: a method slice with
no screen and no event model of its own, so **no white box, no mockup task and no styling task**. The one story is **US2**
(FR-008 as D137 amends it, scenario 6), *a mutation run is priced per change where a tool is wired, and says so where it is
not*.

**Branch**: `slice/S42-mutmut-mutation`, worktree `/home/noahc/math/slipwai-graph-S42-mutmut-mutation`. One commit per
task. No push, no claim.

**Delegation**: one `drive-implement` delegate takes US2 — T002 … T012 in dependency order — or more than one where the
manifests below are disjoint (*Parallel opportunities*). Each task is one RED-GREEN-REFACTOR cycle and one commit and
opens with **one rule's examples**; a delegate never writes a rule's tests ahead of the previous rule's commit. A task's
*Files* line is its manifest, the only files that delegate may write. Nobody but the host writes `tasks.md`. A delegate
that needs a file outside its manifest — a test elsewhere that pins text it changes — **stops and names the file; the host
adds it.**

**Not tasks:**
- **AC-S42-13** (plan rule list, last line; quickstart) is the demo's (T016): `make mutation` against `make
  mutation-full` on a two-service Python starter, wall time, mutant counts, the command and the machine, measured by the
  hand after the converged verdict. A task for it would be a test that cannot fail.
- **Handed back 1** (the default Python starter's own 114 survivors, R9) and **Handed back 2** (S41's fragment, which rule 9
  narrows — that *is* a task, T010) — the first is the host's: no task widens the slice to kill or suppress a starter
  survivor, none narrows `[tool.mutmut]` to the green files, and the note and fragment are written to option (a) without
  promising a follow-on.
- **Open questions** (`type_check_command`, a project with no test reaching any mutant, `os.cpu_count()` workers) are
  recorded residuals, not tasks.
- **ADR 0010** exists at `Proposed`; T010 only holds that the words agree with it and does not edit it unless a test shows it
  disagrees (then the delegate stops and names it).
- No white box: `check-model` has nothing to refuse. *Design review* below says so.
- No task edits `spec.md`, `decisions.md`, `story-split.md`, `slices/README.md`, the root `Makefile`, `delivery/scripts/`,
  `tools/`, CI files, `.github/`, `VERSION`, anything under `release/`, S06's `rules.py`, `scoped_targets.py`,
  `verify-scoped.py`, `check-slice-scope.py`, `verify_scoped/*`.

## Constraints that hold for every task

- **MINOR, `VERSION` stays `1.6.0.dev0`.** `changelog.d/` already holds MINOR fragments (S41's among them), so a MINOR
  fragment leaves the number as it is (`tests/test_changelog.py` checks the pair). **`changelog.d/mutmut-mutation.md` lands
  in T002** — the first commit that changes a user-visible tree — as a first draft whose first line is `MINOR`, one bold
  lead sentence and one paragraph beginning `**Catch-up.**` that stands alone and says only what is true at that commit; T011
  completes it. T010 alone edits `changelog.d/stryker-mutation.md` (the Python clause only). Shape: `changelog.d/README.md`.
  A commit that changes `src/slipwai/` or `assets/` says `Level MINOR; VERSION already carries it (1.6.0.dev0); inside S42's
  fragment` and the reason; a commit that changes only `tests/` says it reaches no user.
- **Commit messages end `(cruise iteration 30)`**, then `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- **Write scope of the whole slice** (every manifest stays inside it): `specs/001-faster-slipwai/slices/S42-mutmut-mutation/`,
  the files listed under *Source Code* in `plan.md`, `tests/` (the new modules this file names and the named lines of the
  existing tests listed in *The sweep at planning*), `changelog.d/mutmut-mutation.md`, `changelog.d/stryker-mutation.md`
  (T010, one clause). A delegate that finds a file outside it needs a change stops and names it.
- **Size and width.** Every file under `src/` and `tests/` stays within 350 lines and 120 columns (`make check-structure`).
  Current line counts (`wc -l`) and each task's budget: `src/slipwai/project/languages/python.py` **283** (T002 adds one
  call site, net ≤ 6; **new code goes in `src/slipwai/project/mutmut.py`**, never in `python.py`),
  `src/slipwai/project/native_commands.py` **321** (T002 replaces the Python `mutation` line with `FULL_COMMAND` from
  `mutmut.py`, net ≤ 0; T010 net ≤ 2), `src/slipwai/backends.py` **332** (T002 net 0: `set()` becomes the script's
  `frozenset`), `src/slipwai/project/gitignore.py` **172** (T002 net ≤ 2), `src/slipwai/project/mutation.py` **291** (T010
  rewrites notes and command text and ends ≤ 330 — mutmut's note text lives in `mutmut.py`, imported, not written in
  `mutation.py`), `src/slipwai/project/mutmut.py` new (≤ 200). Tests: `test_mutation_placeholders.py` 178,
  `test_mutation_words.py` 187, `test_mutation_words_script.py` 186, `test_mutation_dry_run.py` 118, `test_mutation.py` 300,
  `test_scoped_targets.py` 240, `test_stryker_generated.py` 301, `test_stryker_migrate.py` 209, `test_verify_stamp_lists.py`
  141, `test_uv.py` (read its count before editing), `test_select_tests_real_loaders.py` 231,
  `test_select_tests_cross_reads.py` 251. **A new test module that nears 350 stops and names the split; the host adds the
  manifest line.** Assets are not counted by `check-structure` (`assets/toolkit/scripts/mutation-scope.py` 1066,
  `verify-stamp.py` 1108, `check-imports.py` 405), but the wrapper and the additions to `mutation-scope.py` stay readable:
  small named functions, no class beyond the seams that exist.
- **Before every commit** run `make lint typecheck check-structure`. **When `assets/toolkit/` is touched** (T002 `factory_recipe`,
  T007–T009) also `make test TESTS="test_toolkit test_utf8_io test_changelog"`. Do not run `make verify`; the host runs the
  suites once, in T013.
- **A task that adds a `tests/test_*` module owes the selector's three pins,** and runs
  `make test TESTS="test_select_tests_declarations test_select_tests_real_helpers test_select_tests_real_audit test_select_tests_real_declared"`
  before committing, with those test files in its manifest: (1) a module that generates nothing and loads the wrapper or
  the scope script by path declares `TEST_SELECTION = {"reads": [...]}` naming every path it opens, copies, runs or loads, and
  the module's row goes into `tests/test_select_tests_real_loaders.py`'s `READS` (`test_select_tests_real_audit` checks it
  under an audit hook) and so into `tests/test_select_tests_real_declared.py`'s pin — which is satisfied by `READS` alone,
  the file is edited only if a module must be named in `LEFT_UNDECLARED`; (2) a module that generates a project or imports a
  test module that does stays undeclared (as `test_stryker_generated` is) and is not added to `READS`; (3) a new
  `src/slipwai/project/*.py` module owes a `SERVES` row in `tests/test_select_tests_cross_reads.py` (T002:
  `"project/mutmut.py": {("backend", "python")}`, as `project/stryker.py` has its row); (4) no void declaration — a declared
  `reads` that the module never opens is a failure. Add the wrapper path to `READS` as a segment-built constant beside
  `TS_WRAPPER` (`PY_WRAPPER = "assets/languages/python/scripts/mutmut-mutation.py"`).
- **A task that changes what a toolkit check script reads runs every `test_verify_scoped_*` module** (T009, T007/T008 if
  `mutation-scope.py` gains a read). A path literal a toolkit check loads is read by `test_verify_scoped_table_held` as a file
  the check reads: write such lists as segments (`("scripts", "mutmut-mutation.py")`), or add a reasoned `NOT_AN_INPUT_FOR`
  entry. A literal the verify stamp's scan reads as a path under an exempt entry needs a reasoned row in
  `tests/test_verify_stamp_lists.py`'s `EXEMPT_PATHS` (S41 added `.stryker-tmp`); **T009, which adds `apps/*/mutants/` to
  `EXEMPT`, carries that file and runs every `test_verify_stamp*` module** (the root `Makefile` runs the stamp files as this
  repository's own stamp — say so in the report).
- **A generated-Makefile text change moves `tests/test_scoped_targets.py`'s e5 digests (`PRE_SLICE`), deliberately:** the task
  that changes the Python recipe line (T002) or the note (T010) carries that file and regenerates the Python shapes' hashes
  only (`standard-python`, `model-python-sqlite`, `two-python`, `java-python-web` and any other shape whose Makefile above
  `# Scoped gate` holds a Python service).
- **A new test module that imports a `test_verify_scoped_*` module and sorts before `test_benchmark*` shadows
  `tests/test_benchmark`:** name such a module `test_verify_scoped_*`. None of this slice's modules is expected to; if one
  imports `test_verify_scoped_*` (T009's `test_mutmut_after_run` might, for the `verify-scoped` not-broadened example) the
  delegate names it accordingly or imports nothing from there.
- **Docs prose pinned by writers' tests breaks when reworded.** A task that edits a doc (T010) runs `grep -rln "<sentence>" tests`
  for every sentence it changes and carries the pinning tests (`tests/test_backend_obligations.py`, `test_docs_index`,
  `test_commands`, `test_scoped_ladder`, `test_mutation_words`) in its manifest or stops and names them.
- **Assets.** Every `read_text`/`open` in a script under `assets/` names `encoding="utf-8"`. A test that loads a toolkit or
  asset script as a module sets `sys.dont_write_bytecode = True` first (the helper in `tests/test_mutation.py` is the
  model); every probe of anything under `assets/` runs as **`python3 -B`**, so no `__pycache__/` is left under `assets/`. No
  literal `apps/service` or `apps/web` in a new script (`toolkit.spoken_for` rewrites those). `mutation-scope.py` **loads** the
  wrapper by path (never copies it) and writes nothing under the project. The wrapper imports `tomllib` lazily (inside the
  reader), so loading it on Python 3.10 never fails — `Unreadable` is raised where it is read.
- **Tests.** Standard library only; **no mocking framework, `unittest.mock` included.** The wrapper is tested in-process and as
  a subprocess against **a fake `uv` executable written into a temporary directory first on `PATH`**: it records its argv and
  cwd (one JSON line per call) and, for `run … python -c` writes the `.meta` files the example hands it under
  `<service>/mutants/`, for `run … mutmut run` writes the results the example hands it, for `sync` exits as the example says.
  The scope script is tested behind S08's `FakeRunner` (`tests/mutation_scope_fixture.py`, read, not edited). **Real `git` in
  temporary repositories** (`git init`, `slice/S1`, a `main` ref) — never a stubbed diff. Evidence is a log, a file or an exit
  status, never a clock. **Every `subprocess.run` carries `timeout=`**, and anything that can hang (a fake `uv` that waits, a
  real mutmut) runs under one. A test that runs a generated project's command removes `CI`, `GITHUB_ACTIONS`, `GITLAB_CI`
  (and, as S08's `clean_environment` does, `MAKEFLAGS`, `MFLAGS`, `MAKELEVEL`, `MAKEOVERRIDES`, `MAKEFILES`, `SINCE`) from its
  environment unless the example sets one; **each touched test module is also run once under `CI=true`** and the report says
  so. Projects are generated with **this worktree's `./slipwai`** (`FactoryTestCase.generate` does; a hand run says
  `./slipwai generate …`, never the one on `PATH`). **Scratch only under `/tmp/s42/`**; keep `/tmp` clean on every exit
  path. A Go module cache under `/tmp/tmp*` is read-only — `chmod -R u+w` before `rm -rf` — should one appear.
- **A recipe line is never changed before the tests that rebuild it are searched** (*The sweep at planning*): `tests/` was
  searched for helpers that rebuild an old Makefile by regex or pin the `mutation` recipe; the hits are met by the tasks
  named. A delegate who changes a recipe line searches again for the one it changes.
- **`verify`, `verify-checks`, `ci` and the CI workflow stay byte for byte**; the `mutation` line is unchanged, only
  `mutation-full`'s Python recipe line changes, and `factory_recipe` mirrors it in the same commit (T002). **`SINCE` reaches
  no Python line** (D216). No Makefile variable, `export` or `define` is added.
- **Real runs are slow and few.** Exactly one real mutmut run of the slice as a test, in T012, gated like
  `tests/test_mutation_scope_real_typescript.py` (`backends_under_test()` names `python`, `uv` on `PATH`; network for the first
  `uv sync`) and skipped otherwise. Every other example fakes `uv` or the `Runner`. **T005 owes one hand probe**, not a test:
  its generation snippet (R3's calls — `copy_src_dir`, `copy_also_copy_files`, `setup_source_paths`,
  `store_lines_covered_by_tests`, `create_mutants` — are mutmut 3.8.0's, not documented as public, and a fake `uv` cannot
  prove them) is run once by hand against a real mutmut 3.8.0 install in `/tmp/s42/` on a generated starter, and the report
  says what it printed; a snippet that fails there is T005's defect, found before T012.
- **Commit by path** — `git commit -m … -- <the task's files>`, a new file `git add`ed by its exact path first; never
  `git add -A`, never `git commit -a`, never `git checkout --` on work that is not the delegate's own (the sanctioned
  RED/teeth route in `delivery/docs/delegated-agent-safety.md` is the only one).
- **RED is seen** for its stated reason before the production file is touched. A **hold** (an example that passes today) is
  written as a hold, said so in its name or docstring, and **seen to have teeth** before commit: change the production file,
  observe the failure, restore with `git checkout -- <exact path>`. A hold with no teeth is not claimed.
- **GREEN is a class**, not an instance: where a rule says *every service* or *every backend*, the examples run a two-service
  project (two Python services; Go beside Python) and the shapes the rule names.
- **No `.codegraph/`** in this repository: callers were found by text search; the tasks name them.

### The sweep at planning

`tests/` searched for helpers that rebuild or pin a generated Makefile's `mutation` / `mutation-full` recipe, Python as a
placeholder, the Python lock against its manifest, `BASE_DEVELOPMENT`'s contents and the ignore text
(`grep -rn "mutmut" tests`, `grep -rn "PYTHON_REFUSED\|UNWIRED" tests assets src`, `grep -rn "factory_recipe" tests`,
`grep -rln "uv.lock\|regenerate-locks" tests`, `grep -rn "pytest-xdist==\|ruff==\|mypy==" tests`, `grep -rn "python" tests/test_mutation*.py`).
**Hits**, each met by the task named:

| Hit | Pins | Met by |
|---|---|---|
| `tests/test_mutation_targets.py:49` (`standard-python` shape) and `:182` (`factory_recipe(services)` equals the generated `mutation-full` recipe) | the script's reconstruction of the recipe equals the generated one | **T002** changes both sides in one commit (`native_commands.py` and `factory_recipe`'s Python branch); no edit to the test expected |
| `tests/test_scoped_targets.py:47–58` `PRE_SLICE` | sha256 of each shape's Makefile above `# Scoped gate`; Python shapes `standard-python`, `model-python-sqlite`, `two-python`, `java-python-web` among them | **T002** (the recipe line), **T010** (the note): hashes only, regenerated by the delegate where a Python shape's text above the section moved |
| `tests/test_mutation_placeholders.py:24–25` `PYTHON_ENDING`, `:27` `FILES["python"]`, `:67–68`, `:77–78`, `:97–108` (`test_d149_*` pin the Python refusal words and the "other refusals do not name mutmut" hold), `:128–141`, `:150` (file-class table), `:176` `PLACEHOLDER_MESSAGES["python"]`, and the `test_e1_the_scripts_table…` hold (`set(PLACEHOLDERS) == set(FILES)`; each recipe's `echo`) | Python as the placeholder: its message, `PYTHON_REFUSED`, the file classes, the recipe echo | `test_e1_the_scripts_table…` and the `PLACEHOLDER_MESSAGES` row re-pointed in **T002** (the recipe stops echoing a setup message; Python leaves the loop of echo-bearing placeholders, the script's `PLACEHOLDERS["python"]` stays until T007); the rest in **T007** (Python leaves `PLACEHOLDERS`, `PYTHON_ENDING` and the two `test_d149_*` Python examples are deleted or inverted — D149's *until a later release* is the sentence that stops being true; the file-class table keeps Python's row; `test_d149_hold_the_other_refusals_do_not_name_mutmut` stays, with Quarkus) |
| `tests/test_mutation_words_script.py:78–81`, `tests/test_mutation_dry_run.py:96` | Python in the class of backends the placeholder words apply to (`python:apps/service`, `python:apps/worker` mixed) | **T007**: Python moves from the placeholder class to the wired one in those lines only |
| `tests/test_stryker_after_run.py:167` (`mutation: refuse apps/billing — install and configure mutmut`) and the test around it (`test_e3_quarkus_and_python_still_refuse…`) | a Python service beside a TypeScript one is refused with the setup message | **T007**: the example is re-pointed (Python now runs; Quarkus is the refused one), the TypeScript half of the example is unchanged; `tests/test_stryker_after_run.py` is in T007's manifest for that line only |
| `tests/test_mutation_words.py:17–18` (`PLACEHOLDERS = ("java-quarkus", "python")`), `:102` (`mutation_notes([python])` is `""`), `:163–182` (`FragmentTest`: S41's fragment says Python is refused *until a later slipwai release wires mutmut*; `"TypeScript, Python and `java-quarkus`"`) | Python has no note; S41's fragment carries Python's stub words | **T010**: named lines only — the inverse of S08's hold for Python, and the fragment tests re-pointed at the narrowed clause (*Handed back* 2) |
| `tests/test_mutation.py:112–114` | `mutation_command(["typescript"])` text | hold in **T010**; a `["python"]` example is added beside it in `test_mutmut_generated.py`, not here |
| `tests/test_stryker_generated.py:265` (`assertIn("Python and Quarkus", UNWIRED)`), `:282–283` (docs no longer say "TypeScript and Python exit 2" / "no tool wired (TypeScript, Python") | `UNWIRED`'s wording and the docs' | **T010**: the `UNWIRED` line becomes `UNWIRED` names only Quarkus; `:282–283` stay true (hold) |
| `tests/test_stryker_migrate.py:67` (`for words in (…, "Python", "java-quarkus")` in S41's fragment) | S41's Catch-up names Python | **T010**: the `"Python"` word dropped from that tuple; `"java-quarkus"` stays |
| `tests/test_uv.py:59` (the exact `dependency-groups.dev` list of the default Python starter) and `:139` (`uv{suffix}.lock` names) | `["httpx==0.28.1", "mypy==2.3.1", "pytest-xdist==3.8.0", "pytest==9.1.1", "ruff==0.16.3"]`; the four lock names | **T002**: `"mutmut==3.8.0"` joins the list at `:59` (sorted: after `mypy`); `:139` is a hold |
| `tests/test_xdist_plugin.py:20,42`, `tests/test_gates.py:143`, `tests/test_renovate.py:44–55` | `assertIn` of a pin in `dev`; `mypy==` present; `apps/service/uv.lock` is Renovate's | holds, **T002**: all stay true; no edit expected |
| lock checks (`scripts/regenerate-locks.py --check`, `tests/test_pruning.py`, `tests/test_language_skeletons.py`, `tests/test_backing_services.py` read the Python manifest and `uv*.lock`) | each committed lock agrees with its manifest | **T002**: the manifest line and all four `uv*.lock` move in one commit, or the suite is red between them |
| `tests/test_monorepos.py:103,:120–126` | every shape's Makefile contains `mutation:`; Go's recipes contain `python3 scripts/go-mutation.py apps/service` | hold, **T002**: both stay true; no edit expected |
| `tests/test_verify_stamp_pinned.py`, `tests/test_verify_stamp_*.py`, `tests/test_verify_stamp_lists.py:20–28` (`EXEMPT_PATHS`) | `.PHONY: verify ci` then the exact `verify` rule bytes; `EXEMPT`; a literal under an exempt entry needs a reason | hold in **T002**; **T009** adds the `EXEMPT` row and, if the scan demands it, a reasoned `EXEMPT_PATHS` row for `mutants`, and runs the whole `test_verify_stamp*` set |
| `tests/test_verify_scoped_*`, `tests/test_scoped_adopted.py`, `tests/test_scoped_migrate.py` | `rules.json` from-text equals from-database; a fresh slice branch is not broadened; a path literal in a check is a read | read-only suites, run in **T002**, **T009**; none is edited |
| `tests/test_select_tests_real_loaders.py` `READS`, `tests/test_select_tests_real_declared.py`, `tests/test_select_tests_cross_reads.py` `SERVES` | every declared module's reads; every `project/*.py` module's serving configuration | **T002** (`project/mutmut.py`), and each task that adds a wrapper-loading module (**T003**, **T004**, **T005/T006** share one, **T007**, **T008** if they load by path) |
| `tests/test_backend_obligations.py` | names no `mutation` text, rebuilds no Makefile | **T010**: reads `docs/backend-obligations.md`; the delegate runs it and edits it only if the new sentence breaks a pin |
| `tests/test_changelog.py` | the fragments' highest level against `VERSION` | hold in every commit touching `changelog.d/` |
| `tests/test_matrix.py`, every Python row's `make verify` | the starters pass their own gate; each now `uv sync --locked`s mutmut | not edited; run by the host in **T013** |
| `.gitignore`'s Python line (`src/slipwai/project/gitignore.py:70–72`; `test_stryker_generated.py:160–167` is the TypeScript analogue) | the Python block `__pycache__/ … /apps/*/requirements.txt` | **T002**: `apps/*/mutants/` joins the Python block; the new example reads it; a Go-only and a TypeScript-only project do not have it |
| `PYTHON_REFUSED` (`assets/toolkit/scripts/mutation-scope.py:611, :801`), `UNWIRED` (`src/slipwai/project/mutation.py:262`), `native_commands.py:103` (`@command -v mutmut … mutmut run`) | the old Python stub, in the scope script, the command text and the recipe | `native_commands.py:103` in **T002**; `PYTHON_REFUSED` and `:801` in **T007**; `UNWIRED` in **T010** |

## Format: `[ID] [P?] [Story] Description` — each task is one increment, one commit

`[P]` marks a task whose files are disjoint from every sibling it could run beside; see *Parallel opportunities*.

---

## Phase 1: Implementation stage

Each task starts from the green committed suite.

### T001 — Pin: the baseline before anything moves (host task)

- [x] **Host task; no story; no commit.** *(Done: 166 tests OK, 2 skipped, 88 s; `VERSION` 1.6.0.dev0; ADR 0010 Proposed; uv 0.12.21; `make starters` kept at `/tmp/s42/starters-before`.)* Run the pin set once and record that it is green:
  `make test TESTS="test_mutation_targets test_mutation_placeholders test_mutation_words test_mutation_words_script test_mutation_dry_run test_mutation test_monorepos test_scoped_targets test_uv test_verify_stamp_pinned test_verify_scoped_rules test_scoped_adopted test_scoped_migrate test_changelog test_backend_obligations test_stryker_generated test_stryker_migrate test_stryker_after_run"`.
  Confirm `cat VERSION` reads `1.6.0.dev0`, that `delivery/docs/adr/0010-mutmut-for-python-mutation.md` is `Proposed`, that `uv`
  and network are reachable (T002 regenerates four locks) and `uv --version` prints 0.12 or newer. Then `make starters` and
  keep `build/` aside (untracked) so T013's diff of that tree is the change a user sees (`docs/maintaining.md`): a `mutmut`
  dev pin and a `[tool.mutmut]` table per Python service, one new script, an ignore line, a Makefile line, a changed
  command text.

### T002 — [US2] What a Python service is given: the dev pin, the table, the wrapper's path, the ignore line, the recipe line, the four locks (R1 · AC-S42-1, AC-S42-4 recipe, AC-S42-9 first clause, AC-S42-11 `mutation-full` carries no `SINCE`)

- [x] **Rule 1.** First commit that changes a user-visible tree, so the fragment's first draft lands in it (first line `MINOR`; *(Done: 9c1b345 — host added to the manifest: `tests/test_scoped_migrate.py` (two-Python migrate now settles `apps/billing/pyproject.toml` and `uv.lock` with `--theirs`), `tests/test_uv.py`'s second pin; the four locks are `python_locks()`'s fresh resolution, so other dev transitive pins moved too (`ast-serialize` 0.11.2 → 0.12.1).)*
  a **Catch-up.** paragraph that stands alone and says only what is true at this commit: a project made before gains
  `mutmut==3.8.0` in every Python service's dev group and `[tool.mutmut]` where its files merge, `scripts/mutmut-mutation.py`,
  the `apps/*/mutants/` ignore line and the regenerated `scripts/verify_scoped/rules.json`; T011 completes it). The wrapper
  lands here as a **skeleton**: it parses `<service> [--file <path> …]`, and every run ends `exit 2` with one line saying
  mutmut is not wired by this script yet. That transient can only fail, never pass, and is the same refusal `mutation-full`
  printed before (exit 2), so `mutation-full` is never wrong in between; T003–T006 build it. **The locks are regenerated
  here, not in a final task:** `uv sync --locked` refuses a lock that disagrees with its manifest, and the lock checks read
  the manifest, so a commit that moves `BASE_DEVELOPMENT` without the four locks leaves the suite red and every generated
  Python starter unsyncable. Needs network; if it is absent the delegate stops and says so. If `scripts/regenerate-locks.py
  --check` cannot run with the machine's `uv` (S41's npm 9.2 problem), the delegate regenerates with a newer `uv` in
  `/tmp/s42/` and says so; the evidence of AC-S42-1 is then `uv sync --locked` accepting each of the four combinations.

**RED** (new `tests/test_mutmut_generated.py`; `FactoryTestCase.generate`; files read from the project, nothing run except
`make -npq` and the lock check):
- e1 a Python project (default answers: FastAPI, Postgres) and a project with a Python service beside a Go one:
  `apps/service/pyproject.toml`'s `dependency-groups.dev` holds `mutmut==3.8.0` exactly, sorted among the base tools, no
  range *(fails today: not there)*. A `--profile standard --frontend none --http none --event-store memory` project has it too.
- e2 `apps/service/pyproject.toml` parses (`tomllib`) and `[tool.mutmut]` equals data-model's table: `source_paths = ["src"]`,
  `pytest_add_cli_args_test_selection = ["tests", "--ignore=tests/integration"]`, `pytest_add_cli_args = ["-p", "no:xdist"]`;
  the raw text carries a comment line above each key (the table is read from the template, so every Python service has it,
  a second service too) *(fails today: no table)*.
- e3 `scripts/mutmut-mutation.py` exists once per project however many Python services it has, is executable
  (`os.access(…, os.X_OK)`), holds no literal `apps/service` or `apps/web`, a `python3 -B` import leaves no `__pycache__/`, and
  is absent from a Go-only and a TypeScript-only project; in an adopted layout it lands under `<delivery>/scripts/` as
  `go-mutation.py` does *(fails today: no script)*. Run as a subprocess with no arguments or an unknown flag it exits 2 with
  one `mutation: ` line.
- e4 `mutation-full:` in the generated Makefile of a Python project is exactly `python3 scripts/mutmut-mutation.py apps/service`
  — no `SINCE`, no `$(if`, no `@command -v` — and in a two-Python-service project one such line per service in service
  order; Go beside Python keeps Go's `$(if $(SINCE),--since $(SINCE))` line byte for byte; `mutation:` is byte for byte what
  it was; `verify`, `verify-checks`, `ci` and the generated workflows are byte for byte the pre-slice text for the shapes of
  `test_verify_stamp_scan.SHAPES` and `test_mutation_targets.SHAPES` *(the first half fails today: the `@command -v mutmut`
  line; the second is a hold, teeth: add `mutation-full` as a prerequisite of `verify-checks` and see it fail)*.
- e5 `.gitignore` of a Python project names `apps/*/mutants/` (inside the Python block, leading it as S41 led the TypeScript
  block so `migrate` merges beside `add-service`'s lines); a Go-only project does not; `git status --short` of a fresh commit
  is empty after `apps/service/mutants/src/x.py.meta` is created *(fails today)*.
- e6 **hold, the class** (the lock rule, AC-S42-1): for each of the four committed `uv*.lock`, `uv lock --check --project`
  over a service written with that combination's manifest exits 0, and `uv sync --locked --dry-run` accepts it (skipped, with
  its reason, where `uv` is not on `PATH`); the lock names `mutmut` and its closure (`libcst`, `textual`, `coverage`,
  `setproctitle`, `click`) *(fails the moment `BASE_DEVELOPMENT` changes without the locks — the RED this task goes through
  before the locks are regenerated; teeth: restore one lock from `git` and see it fail)*. Use `scripts/regenerate-locks.py
  --check`'s own comparison through its module, imported with bytecode off, where it runs; do not reimplement it.

**GREEN** — `src/slipwai/project/mutmut.py` (new): `SCRIPT_PATH = "scripts/mutmut-mutation.py"`, `SCRIPT_ASSET`,
`FULL_COMMAND = f"python3 {SCRIPT_PATH} {APP}"`, `mutmut_files(services)` (the wrapper once per project with a Python
service); `assets/languages/python/scripts/mutmut-mutation.py` (new, skeleton); `assets/languages/python/app/pyproject.toml`
(the `[tool.mutmut]` table, below `[tool.pytest.ini_options]`, a comment above each key); `python.py` one call site writing
the script once (net ≤ 6) and `BASE_DEVELOPMENT` gaining `mutmut==3.8.0`; `native_commands.py` the Python `mutation` line
becomes `FULL_COMMAND` (net ≤ 0); `backends.py` `BACKEND_EXECUTABLES["python"] = frozenset({"scripts/mutmut-mutation.py"})`;
`gitignore.py` the `apps/*/mutants/` line; `assets/toolkit/scripts/mutation-scope.py` **`factory_recipe` only**: its Python
branch writes `python3 scripts/mutmut-mutation.py <path>` (so `test_mutation_targets.py:182` stays green — the rest of rule 6
is T007); `python3 scripts/regenerate-locks.py` rewrites the four locks; `changelog.d/mutmut-mutation.md` first draft;
`tests/test_select_tests_cross_reads.py` the `project/mutmut.py` row.

**REFACTOR:** the line `python3 scripts/mutmut-mutation.py <path>` is spelled once, in `mutmut.py`, and used by
`native_commands.py` and `factory_recipe`'s test-side expectation; the `[tool.mutmut]` comment lines sit in the template, once.

**Verify:** `make test TESTS="test_mutmut_generated test_mutation_targets test_mutation_placeholders test_uv test_xdist_plugin test_gates test_monorepos test_scoped_targets test_verify_stamp_pinned test_verify_scoped_rules test_scoped_adopted test_scoped_migrate test_pruning test_language_skeletons test_backing_services test_select_tests_cross_reads test_select_tests_declarations test_select_tests_real_helpers test_select_tests_real_audit test_select_tests_real_declared test_changelog test_toolkit test_utf8_io"`,
then `python3 scripts/regenerate-locks.py --check` (or the `uv` equivalent above), then `make lint typecheck check-structure`;
the touched modules once under `CI=true`. Commit by path; level line as above.

**Files:** `src/slipwai/project/mutmut.py` (new), `src/slipwai/project/languages/python.py`,
`src/slipwai/project/native_commands.py`, `src/slipwai/backends.py`, `src/slipwai/project/gitignore.py`,
`assets/languages/python/scripts/mutmut-mutation.py` (new, skeleton), `assets/languages/python/app/pyproject.toml`,
`assets/languages/python/locks/uv.lock`, `uv-fastapi.lock`, `uv-postgres.lock`, `uv-fastapi-postgres.lock`,
`assets/toolkit/scripts/mutation-scope.py` (`factory_recipe` only), `changelog.d/mutmut-mutation.md` (new),
`tests/test_mutmut_generated.py` (new, undeclared: it generates), `tests/test_mutation_placeholders.py` (the
`test_e1_the_scripts_table…` hold and the Python row of `PLACEHOLDER_MESSAGES` only), `tests/test_uv.py` (`:59` only),
`tests/test_scoped_targets.py` (`PRE_SLICE` hashes only, where a Python shape moved), `tests/test_select_tests_cross_reads.py`
(one row).

### T003 — [US2] The configuration the wrapper reads: `targets`, `matched`, `refused`, `versions`, and what a table it cannot read says (R2 · AC-S42-6 half, AC-S42-8 half; D215 d's reason, D218)

- [x] **Rule 2.** Needs T002 (the skeleton). In `mutmut-mutation.py`: `targets(service)` reads the service's `pyproject.toml` *(Done: bdd10f5.)*
  with `tomllib` (imported inside the function; `Unreadable("no tomllib: Python 3.11 or newer reads [tool.mutmut]")` where it
  is absent) and returns the parsed table: `source_paths` (or, only where empty, deprecated `paths_to_mutate`) must be a
  non-empty list of relative POSIX strings with no `..`, no leading `/`, no `*`, `?`, `[` — else `Unreadable` naming the
  value; `only_mutate` and `do_not_mutate` lists of strings; no `[tool.mutmut]` is `Unreadable("no [tool.mutmut] table")`.
  `matched(config, file)` is mutmut's `should_mutate` with Python's `fnmatch` exactly as `configuration.py` applies it (R2).
  `refused(service, file)` returns data-model's words for a path holding `*`, `?` or `[`. `versions(pyproject_text,
  lock_text)` returns `{"tool.mutmut": <table>, "requirement": [<every mutmut requirement string>]}` from a manifest (the
  `mutmut` entries of `[dependency-groups]`, `[project.dependencies]`, `[project.optional-dependencies]`) and `{"<name>":
  [<every version>]}` for `mutmut` and the closure of `libcst` (traversing the lock's `[[package]]` `dependencies`, R6)
  from a lock; text that does not parse, and no `tomllib`, raise `Unreadable`. `main` reaches the first lines of the
  data-model table and nothing that starts a process: **a refused `--file` is exit 2, one line, before anything else is
  looked for or deleted**; an unreadable table is `<service>/pyproject.toml: <why>`, exit 2 (the no-table words of the
  data-model's table); neither starts `uv`. `versions` is the reader T008 compares; it is tested here because it is the
  wrapper's, not the scope script's.

**RED** (new `tests/test_mutmut_config.py`, declared `TEST_SELECTION` reads = the wrapper; wrapper loaded in-process with
bytecode off, and run as a subprocess with a fake `uv` that fails the example if it is ever called):
- e1 `targets` on the generated table: `{"source_paths": ["src"], …}`; the deprecated `paths_to_mutate = ["lib"]` alone is read as
  `source_paths`, and ignored when `source_paths` is also set; `matched` — `src/pkg/a.py`, `src/a.py`, `src/pkg/sub/b.py`,
  `src/pkg/__init__.py` match; `src/pkg/a.pyi`, `src/pkg/data.txt`, `tests/test_a.py`, `scripts/x.py`, `srcx/a.py` do not; with
  `only_mutate = ["src/pkg/a*"]` only the matching files are in; with `do_not_mutate = ["*/gen_*"]` a `src/pkg/gen_x.py` is out;
  a table with two `source_paths` matches under either *(fails today: no such function)*.
- e2 each value outside the subset is `Unreadable` naming it: `source_paths = []`, `["../x"]`, `["/abs"]`, `["s*"]`, `["s?"]`,
  `["s[ab]"]`, `"src"` (a string), `[1]`; `only_mutate = "x"`, `do_not_mutate = [1]`; a missing `[tool.mutmut]` table, a missing
  `pyproject.toml`, invalid TOML; no `tomllib` (the example blocks the import by running the subprocess with `sys.modules`
  poisoned through a one-line `sitecustomize`-free `-c` wrapper: `sys.modules["tomllib"] = None`) gives the no-tomllib words.
- e3 `refused`: `` `apps/service/src/pkg/a*.py` holds `*`, which mutmut reads as a pattern over mutant names; rename it, or run
  `make mutation-full` `` for `*`, `?`, `[` as a table test, one example per character; an ordinary path, a path with a
  space, `$`, `#`, `!`, `,`, `{`, a unicode letter, and `]` alone return `None` (a **hold**: only the three fnmatch openers
  are refused; teeth: refuse every non-alphanumeric and see it fail).
- e4 `versions`: a manifest naming `mutmut==3.8.0` in the dev group and one table; a manifest with two mutmut entries in two
  groups lists both; a manifest naming neither (`{"tool.mutmut": None, "requirement": []}`); a lock holding `mutmut`, `libcst`
  and the packages `libcst` resolves to (`pyyaml` on one marker, `pyyaml-ft` on another) keyed by name with every version,
  while `pytest`, `coverage` and `textual` are **not** keys (D222's reason read as R6 reads it — a hold, teeth: add them and
  see it fail); two versions of one name are both listed; non-TOML text and a TOML document without `package` raise
  `Unreadable`.
- e5 `main`: `--file src/pkg/a*.py` among matched ones is exit 2, one line, the fake `uv` never called, nothing created
  under the service (a pre-placed `mutants/old.meta` still there); a service with no `[tool.mutmut]` is exit 2 with `<service>/pyproject.toml: no [tool.mutmut] table`,
  `uv` never called; a valid invocation reaches the skeleton's exit 2 line (the next tasks' seam).
- e6 **hold** (class): the same table read in a service nested one level (`apps/billing`) and with a path argument that has a
  trailing `/` — the same answers.

**GREEN** — `mutmut-mutation.py`: `Unreadable`, `targets`, `matched`, `refused`, `versions`, the argument handling and the
first lines of `main`.

**REFACTOR:** one `check_paths(values)` function used by `targets` for `source_paths` and for the refused-character set, so
"readable" and "refused" cannot drift; the lock walk is one function from a package name to its closure.

**Verify:** `make test TESTS="test_mutmut_config test_mutmut_generated test_select_tests_declarations test_select_tests_real_helpers test_select_tests_real_audit test_select_tests_real_declared test_toolkit test_utf8_io"`, then
`make lint typecheck check-structure`. Commit by path; level line as above.

**Files:** `assets/languages/python/scripts/mutmut-mutation.py`, `tests/test_mutmut_config.py` (new),
`tests/test_select_tests_real_loaders.py` (the module's `READS` row and `PY_WRAPPER`).

### T004 — [US2] Setup and environment: a host without `os.fork`, a project without `uv`, a lock that disagrees, an environment without mutmut 3.8.0, a stray `PYTEST_ADDOPTS`, one run at a time (R7 · AC-S42-10)

- [x] **Rule 4.** Needs T003. After the refusal and the table are read (both start nothing), `main` checks in this order, each *(Done: dd4577b — the lock is taken before `uv sync` only where `.venv/pyvenv.cfg` exists, after it otherwise (a `.venv/` holding only the lock is not an environment uv accepts); host accepted the reading; `tests/test_mutmut_config.py` e5 re-pointed.)*
  an exit 2 with the data-model line: no `os.fork` (or `sys.platform` Windows) → the WSL line; no `uv` on `PATH` → the `uv`
  line; `uv sync --project <svc> --locked --quiet` refused → the `uv lock --project <svc>` line (the refusal is `uv`'s exit
  status, never parsed); `importlib.metadata.version("mutmut")` read in the service's environment through `uv run --no-sync
  --project <svc> python -c …` — absent, or not `3.8.0`, → the mutmut line naming what was found; `PYTEST_ADDOPTS` removed
  from the environment handed to mutmut, and named in one line where it was set; an exclusive `fcntl.flock` on
  `<svc>/.venv/mutmut-run.lock` held for the run, non-blocking, a second run exiting 2 with one line naming the lock (released
  by the kernel when the process dies). The skeleton's exit-2 line remains after setup passes (T005 replaces it).

**RED** (new `tests/test_mutmut_setup.py`, declared reads = the wrapper; the fake `uv` logs every call as `{"argv", "cwd",
"env"}`; its `sync` exit status and its `python -c` output are the example's):
- e1 no `os.fork` (the example poisons `os.fork` through the in-process loader, or runs `main` with `os` patched by the
  subprocess driver's `del os.fork`): `mutation: mutmut needs os.fork, which this host does not have; run it under WSL`, exit 2,
  the fake `uv` never called, nothing created under the service *(fails today: the skeleton's own line, and no WSL words)*.
- e2 no `uv` (an empty temporary `PATH` that still finds `python3` by its absolute path): the data-model's `uv` line, exit 2.
- e3 `uv sync` fails (fake exits 1 with a message on stderr): exit 2, `<service>/uv.lock does not agree with
  <service>/pyproject.toml; run uv lock --project <service>, then this again`, `mutmut` never started; the call recorded is
  `sync --project <service> --locked --quiet` with cwd the project root, and the same invocation is made for a scoped and a
  swept run (class over `--file` present/absent).
- e4 the environment's mutmut: absent (the fake `python -c` prints nothing and exits 1), `3.7.0`, `3.8.1`, `3.8.0` — the first
  three are exit 2 with `mutmut is not installed in …'s environment` / `mutmut 3.7.0 installed in …` (data-model's line, found
  or "is not"); `3.8.0` passes the check *(fails today: no check)*.
- e5 `PYTEST_ADDOPTS="-n 2"` in the caller's environment: the fake `uv` records that `PYTEST_ADDOPTS` is **absent** from the
  environment of every call after the check, and the output carries the data-model's line once; without it set, no such line.
  Other variables (`PYTHONPATH`, `VIRTUAL_ENV`) are passed through unchanged (a **hold**; teeth: clear the whole environment
  and see it fail).
- e6 two runs of one service: the first holds the lock (the fake `uv` waits on a pipe the example controls, under a timeout);
  the second exits 2 with one line and never calls `uv sync`; after the first ends, a third run is not refused (the kernel
  released the lock — the example kills the first with a signal and checks it); two runs of two different services at once
  both proceed (class: the lock is per service).
- e7 **hold, with teeth** (nothing is fetched): in every example the recorded argv of every call to `uv` is `sync … --locked`,
  `run --no-sync …` — never `uv pip`, `uv add`, `uv run` without `--no-sync`, `uvx`, `pip` — *(teeth: drop `--no-sync` from one
  call and see it fail)*; no file under the service other than `.venv/mutmut-run.lock` is written by setup.

**GREEN** — `mutmut-mutation.py`: `check_host`, `ensure_synced`, `check_mutmut_version`, `mutmut_env`, `service_lock`, called
in that order after the config.

**REFACTOR:** `main` becomes the ordered list of its checks (refusal, table, host, uv, sync, version, lock), each returning an
exit or nothing, so the order the rules fix is read in one place; one place spells a `mutation: ` line.

**Verify:** `make test TESTS="test_mutmut_setup test_mutmut_config test_mutmut_generated test_select_tests_declarations test_select_tests_real_helpers test_select_tests_real_audit test_select_tests_real_declared test_toolkit test_utf8_io"`, then
`make lint typecheck check-structure`; the new module once under `CI=true`. Commit by path; level line as above.

**Files:** `assets/languages/python/scripts/mutmut-mutation.py`, `tests/test_mutmut_setup.py` (new),
`tests/test_select_tests_real_loaders.py` (the module's `READS` row).

### T005 — [US2] Generate, then run: a fresh `mutants/`, mutmut's own generation, the names read from `.meta`, an empty file is *no mutant to run*, `mutmut run` handed exactly those names (R3, R5 · AC-S42-6, AC-S42-4 fresh `mutants/`, AC-S42-3 own directory and configuration)

- [x] **Rule 5.** Needs T004 (the setup it follows). `<svc>/mutants/` is deleted before every run (and kept after: it is the report). *(Done: 82dece3 — hand probe against real mutmut 3.8.0: settings.py 14 mutants (12 killed, 2 survived), read_models.py no mutant to run, tests/x.py outside targets; `tests/test_mutmut_setup.py` end state re-pointed.)*
  Generation: `uv run --no-sync --project <svc> python -c <snippet>` from the service directory, the snippet making the same
  calls `mutmut run` makes before it collects stats (R3). Then, per given file (`src/…` within the service), `mutants/<file>.meta`'s
  `exit_code_by_key` is read: a given file with no `.meta` prints `not mutated <service>/<file> — outside mutmut's configured
  targets` and is dropped; no `--file` left prints the *nothing under …* line, exit 0; every remaining file's `exit_code_by_key`
  empty prints `no mutant to run — <files>: mutmut found no function to mutate in it|them`, exit 0, and `mutmut run` is **never
  started**; otherwise `scoped to <n> given file(s): <files> — <m> mutant(s)` and `uv run --no-sync --project <svc> mutmut run --
  <every key of the given files>` from the service directory (a sweep, no `--file`: `mutmut run` with no names). A changed
  `pkg/__init__.py` runs that file's keys only (its submodules share the `pkg.` prefix; the names come from the file's own
  `.meta`, never a pattern). The wrapper prints `mutmut exited <code> (…)` and — until T006 — ends exit 2 with the skeleton's
  one line (a transient that can only fail; the one exception is the exit-0 *no mutant to run* paths above, which are final).

**RED** (in new `tests/test_mutmut_verdict.py`, declared reads = the wrapper; the fake `uv` writes the `.meta` files the
example hands it for the `python -c` call, logs `run … mutmut run -- <names>` and exits as told; setup passes via a
`3.8.0` answer):
- e1 a scoped run of `src/pkg/a.py` whose `.meta` holds three keys: the call order is `sync`, `run … python -c`, `run … mutmut
  run -- pkg.x_f__mutmut_1 pkg.x_f__mutmut_2 pkg.x_g__mutmut_1` (the exact keys, in `.meta` order), cwd the service directory;
  first line `scoped to 1 given file(s): src/pkg/a.py — 3 mutant(s)`; `mutmut exited 0 (its exit status and the output above
  are mutmut's, never the verdict; the .meta files are)` is printed *(fails today: the skeleton exits 2 before generation)*.
- e2 clean slate: a `mutants/` from an earlier run (an old `.meta` with a `0` that would read as a survivor, a stale
  `mutmut-stats.json`) is gone before the fake runs (the fake asserts it) and is **present** after (the new one) — *(teeth: skip
  the delete and see the stale-results example below pass wrongly)*; a run that writes no `.meta` does not read the old one.
- e3 no mutant to run: a given file whose `.meta` is `{"exit_code_by_key": {}}` — the starter's types-only `read_models.py` — is
  `no mutant to run — src/pkg/types.py: mutmut found no function to mutate in it`, exit 0, and the fake never saw `mutmut run`;
  two such files read `in them`; one empty and one holding keys runs `mutmut run` with the non-empty file's keys only.
- e4 a given file with no `.meta` (a file `[tool.mutmut]` leaves out) is named `not mutated … — outside mutmut's configured
  targets`, exit 0 when nothing is left (the *nothing under …* line), `mutmut run` never started; a given file that is unmatched
  beside a matched one runs the matched one only and names the other.
- e5 `pkg/__init__.py`: `.meta` of `src/pkg/__init__.py` holds `pkg.x_health__mutmut_1`; `src/pkg/sub.py` holds `pkg.sub.x_f__mutmut_1`
  and is **not** given; the run is handed `pkg.x_health__mutmut_1` only, never `pkg.*` or the submodule's key.
- e6 a sweep (no `--file`): `mutmut run` is started with no names after the generation step; the fake sees no `--` (class over
  scoped/swept for the clean slate and the cwd).
- e7 two services: `apps/service` and `apps/second`, each run from its own directory with its own `pyproject.toml` read (the
  fake records cwd; a different `source_paths` in the second is honoured); one's `mutants/` is not touched by the other's run.
- e8 `./`-prefixed and trailing-slash forms of `--file` and of the service are read as the same file (a **hold**; teeth: drop the
  normalisation and see e1 fail for `./src/pkg/a.py`).

**GREEN** — `mutmut-mutation.py`: `clean`, `generate`, `keys_of`, `run_mutmut`, `scoped_names`, the printer lines.

**REFACTOR:** the snippet is one named constant with a docstring naming the 3.8.0 functions it calls (R3) and the sentence
"sweeps on a pin change (T008) and refuses another version (T004) because of this"; the `.meta` path is built in one function
shared with T006's reader.

**Verify:** `make test TESTS="test_mutmut_verdict test_mutmut_setup test_mutmut_config test_mutmut_generated test_select_tests_declarations test_select_tests_real_helpers test_select_tests_real_audit test_select_tests_real_declared"`, then
`make lint typecheck check-structure`; under `CI=true` once. **And the hand probe** (not a test): the snippet run once against a
real mutmut 3.8.0 in a starter under `/tmp/s42/` — report what it printed (the demo's `mutants/src/<pkg>/settings.py.meta` with 14
keys and `application/ports/read_models.py.meta` with `{}` are what R3 saw). Commit by path; level line as above.

**Files:** `assets/languages/python/scripts/mutmut-mutation.py`, `tests/test_mutmut_verdict.py` (new),
`tests/test_select_tests_real_loaders.py` (the module's `READS` row).

### T006 — [US2] The verdict is the `.meta`'s, by D212's rule: killed passes, no tests is counted, everything else fails, a silenced mutant fails the run (R4 · AC-S42-5; D219's reason applied, *Applied, not decided* 2)

- [x] **Rule 3.** Needs T005. After `mutmut run`, the wrapper reads `exit_code_by_key` of the judged files — the given files *(Done: ef866aa — `tests/test_mutmut_verdict.py` is at 350 lines; e4 and the e7 hold were written with the code, their RED reconstructed.)*
  (scoped) or every file that has a `.meta` (swept) — and decides with its own copy of 3.8.0's table (data-model): `1`, `3` pass;
  `5`, `33` are counted on the last line (`no tests`, "reported, never failed"); every other code, `null` and any code not in the
  table fail, one line per mutant `<status> <service> <mutant name> (mutmut show <mutant name> in <service>; report
  <service>/mutants/)`, an unlisted code as `unknown (exit <n>)`; a sweep with no mutant at all is `mutmut found nothing to
  mutate in <service>; a pass on nothing is not a pass`, exit 1; the last line is `<n> mutants: <k> killed, <u> no tests (reported,
  never failed)[, <s> survived, <t> timed out, …]; passed|failed — report <service>/mutants/`. Before the verdict, a `# pragma: no
  mutate block|start|end` in a judged file, or a non-empty `do_not_mutate_patterns` in the table, fails in one line each
  (data-model's wording, file and line, or the `pyproject.toml` line); the bare `# pragma: no mutate` on a line is not flagged
  and needs no reason (*Applied, not decided* 2). `mutmut`'s exit status is printed and never the verdict. The skeleton's exit-2
  line is gone.

**RED** (in `tests/test_mutmut_verdict.py`; the fake `uv` writes each example's results into the `.meta` of its `mutmut run`
call):
- e1 a scoped run, every key `1`/`3`: argv as T005 e1; last line `3 mutants: 3 killed, 0 no tests (reported, never failed); passed
  — report apps/service/mutants/`; exit 0 *(fails today: the transient exits 2)*.
- e2 the class over codes (a table test over data-model's whole table, one example per code): `0` survived, `36`, `24`, `-24`,
  `152`, `255` timeout, `35` suspicious, `-11`, `-9` segfault, `null` not checked, `2` check was interrupted by user, `34`
  skipped, `37` caught by type check, `99` and `-1` `unknown (exit 99)` each fail the run, exit 1, with the line naming
  service, mutant and status; `1`, `3` pass; `5`, `33` pass and are counted (`n no tests` appears and `reported, never failed`
  stays); two failing mutants give two lines and the last line counts both statuses.
- e3 mutmut's exit code is printed and never decides: a fake that exits 0 with a survivor fails (exit 1) — R4's observed 114
  survivors under exit 0; one that exits 1 with every key `1` passes; one that exits 1 with every key `null` (R7's
  `PYTEST_ADDOPTS` shape) fails as `not checked`, never as *no tests*.
- e4 zero mutants: scoped is T005 e3 (hold here, no `mutmut run`); a sweep whose every `.meta` is empty is the *found nothing*
  line, exit 1.
- e5 scoped means scoped: a `.meta` of a file that was **not** given holding a `0` does not fail a scoped run for the given
  file's kills; a sweep judges every file's `.meta`.
- e6 silencing: `src/pkg/a.py:12` holding `# pragma: no mutate block`, `… start`, `… end` each fail the run in one line naming
  `<service>/src/pkg/a.py:12` with the data-model words (a source file is read with `encoding="utf-8"`, a file that cannot be
  decoded fails closed with its own line); a line `# pragma: no mutate` (bare, with or without a trailing reason) and
  `# no mutate` / `# pragma: no cover` are **not** flagged (a **hold**; teeth: flag every `pragma` and see it fail); a table with
  `do_not_mutate_patterns = ["x"]` fails with the `pyproject.toml` line, `[]` does not; a pragma in a file not judged (scoped,
  not given) is not read.
- e7 **hold** with teeth: no file under the service other than `mutants/` and `.venv/mutmut-run.lock` is written (hash of the
  service tree before/after, ignoring those); `mutmut run` is never passed `--max-children`, `--no-progress` or any option the
  wrapper does not own (the argv is `run` then `--` then names — teeth: add a flag and see it fail).

**GREEN** — `mutmut-mutation.py`: `STATUS` table (one dict: `PASS`, `COUNTED`, every other code fails by default), `read_meta`,
`judge`, `silenced`, the printer.

**REFACTOR:** the status table is one dict with a default, so an unknown code fails closed by construction rather than by a
branch; the summary line is built from the dict's order.

**Verify:** `make test TESTS="test_mutmut_verdict test_mutmut_setup test_mutmut_config test_mutmut_generated test_select_tests_declarations test_select_tests_real_helpers test_select_tests_real_audit test_select_tests_real_declared"`, then
`make lint typecheck check-structure`; under `CI=true` once. Commit by path; level line as above.

**Files:** `assets/languages/python/scripts/mutmut-mutation.py`, `tests/test_mutmut_verdict.py`.

### T007 — [P] [US2] Python is wired in the scope script: a changed module mutates alone, an unmatched one starts nothing, the other service starts no mutmut, a refused path refuses its service, `java-quarkus` still refuses (R6 · AC-S42-2, -3, -8, -11; D138 items 1 and 5)

- [x] **Rule 6.** Needs T003 (`targets`/`matched`/`refused` loaded by path); does **not** need T004–T006 (every example runs *(Done: a2d182d — one `WRAPPERS` table now drives plan, run and sweep for TypeScript and Python.)*
  behind `FakeRunner`; the real wrapper is T012's), so it may run beside them. In `mutation-scope.py`, tables and dispatch only:
  `WIRED = ("go", "java-spring", "typescript", "python")`, `PRODUCTION_ROOT` gains `"python": "src/"`, `PLACEHOLDERS` loses
  Python (`java-quarkus` stays), `PYTHON_REFUSED` and its use in `refusal` (`:801`) are removed, `REPORTS` gains `"python":
  "mutants"`; `Tools.plan/run/sweep` hand Python to the wrapper as TypeScript's are handed to `stryker-mutation.py`
  (`python3 scripts/mutmut-mutation.py <path> --file <within>` per file, paths relative to the service); the wrapper is
  **loaded** for the table, never copied; a matched file is scoped with `--file`; a file the table does not match is named
  *outside mutmut's configured targets* and the runner is not called; a changed path holding `*`, `?` or `[` refuses its
  service (`refuse <service> — <refusal words>`, status 2, counted `refused`, no tool started, never a sweep, the other
  services still run and the run fails after all have run); `drop_report` removes a skipped Python service's earlier `mutants/`;
  two Python services, and Go beside Python, run only the changed one and name the other skipped; a test-only change, a deleted
  module and a file outside the table are D138's lines, exit 0; `java-quarkus` still refuses; `SINCE` and D117's borders hold;
  `make mutation-full SINCE=<ref>` sweeps Python whole (the recipe carries no `SINCE`). (`factory_recipe` was done in T002.)

**RED** (new `tests/test_mutation_scope_python.py`; `FakeRunner`; real git; services declared as `python:apps/service
python:apps/second` / `go:apps/service python:apps/second` / `java-quarkus:apps/service python:apps/second`; the
`tests/mutation_scope_fixture.py` helpers are read, not edited):
- e1 `slice/S1`, one changed `apps/service/src/pkg/health.py`: first line `mutation: scoped to 1 changed file(s) since `main` at
  <short>: apps/service/src/pkg/health.py`, `mutation: scope apps/service — src/pkg/health.py`, last line `mutation: 1 scoped, 0
  swept, 0 skipped, 0 refused; passed`; the fake saw `(python, apps/service, ["src/pkg/health.py"])` once *(fails today: Python is a
  placeholder and refuses)*.
- e2 two Python services, a change in one: the other is `skip apps/second — no changed production file`, its runner not called,
  and the `mutants/` it held from an earlier run is gone (`drop_report`); likewise Go + Python with the change in the Python side
  (Gremlins not called, its `gremlins.json` gone) and in the Go side (mutmut not called); each service is handed its own path.
- e3 a changed `tests/test_x.py` alone, a deleted `src/pkg/old.py` alone (D138's lines), and a changed file that
  `[tool.mutmut]` leaves out (`only_mutate` not matching, `do_not_mutate` matching, a file outside `source_paths`): `mutation:
  not mutated apps/service/<file> — outside mutmut's configured targets` (the test and deleted cases carry S08's own words),
  `no mutant to run — every changed production file is outside the tools' targets` where that is the case, exit 0, the runner
  **not** called; a matched and an unmatched file together: only the matched one is handed over and the other is named.
- e4 a changed `apps/service/src/pkg/a*.py` (and `?`, `[`) refuses its service: `mutation: refuse apps/service — `apps/service/src/pkg/a*.py`
  holds `*`, which mutmut reads as a pattern over mutant names; rename it, or run `make mutation-full``, last line `0 scoped, 0
  swept, 0 skipped, 1 refused; failed: apps/service`, exit 2; the fake not called, no sweep; the refusal wins over "outside
  configured targets" (an unmatched refused path is refused); next to a good file in the same service the service is refused whole;
  next to a good file in another service that one runs and the run exits 2; the dry run says `would fail`, and `drop_report`
  does not delete the earlier `mutants/` of a refused service. A path with a space, `$`, `!`, `,` or `{` is **not** refused (hold).
- e5 `java-quarkus:apps/service` beside `python:apps/second`, a change in each: Quarkus is `refuse` with its setup message (the
  `Configure PIT …` text), Python `scope`; Python-alone is no longer refused; the Quarkus refusal never names mutmut (AC-S42-11,
  hold with teeth: put `mutmut` in the Quarkus message and see it fail).
- e6 **hold**: `SINCE`, the borders (`ci`, trunk, detached, no base) and an empty change set behave for Python as for Go and
  TypeScript — `make mutation SINCE=HEAD~1` scopes; on `main` the whole run is `mutation-full`; a branch with no change is `no
  production file changed` *(teeth: make the empty set sweep and see it fail)*; `factory_recipe` for `python` services has no
  `SINCE`.
- e7 a config whose table cannot be read (`source_paths = []`, no `[tool.mutmut]`, no `tomllib`) is the service's sweep via
  `Plan.unreadable` — the line names `apps/service/pyproject.toml` and the run calls `sweep`, not `run` *(the sweep cause for a
  changed table is T008; here only that the runner is not asked to scope it)*.
- e8 the S08 tests that used Python as their placeholder example are re-pointed (named lines of `test_mutation_placeholders.py` —
  `PYTHON_ENDING`, the Python entries of `FILES`, the loops at `:67–68`, `:77–78`, `:97–108`, `:128–141`, with `test_d149_*`'s Python
  examples deleted or inverted and the quarkus-only hold kept — and the Python rows of `test_mutation_words_script.py:78–81`,
  `test_mutation_dry_run.py:96`, and `test_stryker_after_run.py:167` and its example) at `java-quarkus` (placeholder) or moved to
  the wired class; every example they held for the placeholder class still holds with Quarkus *(they fail first, for the reason
  that Python is no longer a placeholder)*.

**GREEN** — `mutation-scope.py`: the tables, `Tools`, the Python runner (argv built in one function), `drop_report`, the
refusal wiring, the wrapper loader (generalised from TypeScript's, one loader per wrapper path).

**REFACTOR:** the Python runner, TypeScript's and Go's share the "intersect with the tool's own table, name what is left" step
and the `refused`/`unreadable` branch; no new `mutation:` line is spelled outside the printer.

**Verify:** `make test TESTS="test_mutation_scope_python test_mutation_placeholders test_mutation_words_script test_mutation_dry_run test_stryker_after_run test_mutation_targets test_mutation_scope_typescript test_mutation_scope_go test_mutation_scope_spring test_mutation_change_set test_mutation_borders test_select_tests_declarations test_select_tests_real_helpers test_select_tests_real_audit test_select_tests_real_declared test_toolkit test_utf8_io test_changelog"`,
then `make lint typecheck check-structure`; the new module once under `CI=true`. Commit by path; level line as above.

**Files:** `assets/toolkit/scripts/mutation-scope.py`, `tests/test_mutation_scope_python.py` (new),
`tests/test_mutation_placeholders.py` (named lines), `tests/test_mutation_words_script.py` (`:78–81` only),
`tests/test_mutation_dry_run.py` (`:96` only), `tests/test_stryker_after_run.py` (`:167` and its example only),
`tests/test_select_tests_real_loaders.py` (a `READS` row if the new module is declared; otherwise none — it uses
`mutation_scope_fixture`, which the helpers pin leaves undeclared).

### T008 — [P] [US2] What sweeps a Python service: its `[tool.mutmut]`, its mutmut requirement, its mutmut or libcst lock entries, the wrapper, a table it cannot read, an ignored file (R7 · AC-S42-7; D138 item 3, D216, D222's reason)

- [x] **Rule 7.** Needs T007 (same file, serial with it) and T003 (`versions`). `sweep_causes` gains data-model's table: *(Done: 5da4bb9 — `stryker_versions_moved` became `versions_moved(script, …)`, shared.)*
  `<service>/pyproject.toml` whose parsed `[tool.mutmut]` or mutmut requirement strings differ between base and working tree →
  that service; `<service>/uv.lock` whose `mutmut` or `libcst`-closure versions (keyed by name, every version) differ → that
  service; `scripts/mutmut-mutation.py` changed → every Python service; a side that cannot be parsed, or no `tomllib` → that service
  sweeps (fail closed); a table `targets()` cannot read → that service (`Plan.unreadable`); an ignored file under
  `<service>/src/` → that service (`unlisted`, via `PRODUCTION_ROOT`). Each line names the file. A swept service runs `sweep`,
  the wrapper without `--file`.

**RED** (new `tests/test_mutation_sweeps_python.py`; `FakeRunner` recording scope versus sweep; real git with the base commit
holding the old files):
- e1 `apps/service/pyproject.toml` with `[tool.mutmut]` changed (a key added, `source_paths` altered; also the table added, also
  removed): `sweep apps/service — `apps/service/pyproject.toml` changed`; a second Python service still scopes to its own file; a
  Go service is unaffected.
- e2 `scripts/mutmut-mutation.py` changed: every Python service sweeps, naming the file; a Go and a TypeScript service do not;
  `scripts/go-mutation.py` or `scripts/stryker-mutation.py` changed does not sweep a Python service (S08's/S41's hold with
  Python present).
- e3 the pin: the dev group's `mutmut==3.8.0` → `mutmut==3.8.1` sweeps that service only; an unrelated dependency changed
  (`ruff`), key order, whitespace or a comment in the file do **not** (the second half passes today, a hold with teeth: compare
  raw text and see it sweep); an unparseable `pyproject.toml` at the base or in the working tree sweeps naming the file; a
  `pyproject.toml` with no `tomllib` (the example runs the scope script's loader with `tomllib` blocked) sweeps.
- e4 the lock: `apps/service/uv.lock` with `mutmut` `3.8.0` → `3.8.1` sweeps; `libcst` `1.9.0` → `1.9.1` sweeps; `pyyaml` (in
  libcst's closure) moving sweeps; `pytest`, `coverage` or `textual` moving does **not** (R6/D222 — a hold with teeth: widen the
  closure to every package and see it fail); a second copy of `libcst` at another version in the lock counts as a version change
  (keyed by name, every version); a lock that does not parse sweeps; `apps/second/uv.lock` unchanged does not sweep `apps/second`.
- e5 a table `targets()` cannot evaluate (`source_paths = ["s*"]`, no `[tool.mutmut]`) sweeps that service naming the manifest;
  with the file unchanged since base it still sweeps (the sweep is about the unreadable table, not the diff).
- e6 an ignored file under `apps/service/src/` (`.gitignore`d, e.g. `src/pkg/gen/x.py`): `unlisted` sweeps that service, named.
- e7 two causes at once (table and a production file in one service): the service sweeps once, naming the manifest; the
  production file is not additionally scoped. `SINCE` runs sweep on the same triggers (S08's hold, with Python).

**GREEN** — `mutation-scope.py`: the Python rows of `sweep_causes`, the `versions` comparison through the loaded wrapper, the
swept Python command.

**REFACTOR:** the Python causes join S08's `is_sweep(path)` table and TypeScript's comparison helper (one `moved(base, now)` for
both ecosystems); no second diff is run.

**Verify:** `make test TESTS="test_mutation_sweeps_python test_mutation_scope_python test_mutation_sweeps test_mutation_sweeps_typescript test_mutation_change_set test_select_tests_declarations test_select_tests_real_helpers test_select_tests_real_audit test_select_tests_real_declared test_toolkit test_utf8_io"`,
then `make lint typecheck check-structure`; the new module once under `CI=true`. Commit by path; level line as above.

**Files:** `assets/toolkit/scripts/mutation-scope.py`, `tests/test_mutation_sweeps_python.py` (new),
`tests/test_select_tests_real_loaders.py` (a `READS` row if declared).

### T009 — [P] [US2] The stamp, `check-imports` and the scoped gate hold after a Python run (R5, R8 · AC-S42-9)

- [x] **Rule 8.** Needs T006 and T007 (real runs of the wrapper with a fake `uv`, and the scope script's Python dispatch), and T002 *(Done: 266b977 — no `EXEMPT_PATHS` row needed; `check-imports` prunes by one `OUTPUT` table (`target` beside `pom.xml`, `mutants` beside `pyproject.toml`); `check-migrations.py`'s copy of `recorded()` left Java-only (outside the manifest; it reads no `mutants/`).)*
  (the ignore line). `assets/toolkit/scripts/verify-stamp.py` gains one `EXEMPT` row — `apps/*/mutants/` — so a run's copy of `src/`
  and `tests/`, its `.meta` files and `mutmut-stats.json` are neither read as the stamp's input nor as a reach.
  `assets/toolkit/scripts/check-imports.py` prunes a directory named `mutants` at the root of a Python deployable `project.json`
  records, beside its `pyproject.toml`, and nowhere else (a package named `mutants` under `src/` is still read, a directory
  named `mutants` in a TypeScript or Go deployable is not pruned) — in `skipped()`, beside the `target` rule, by the record,
  never by a file the tree holds alone.

**RED** (new `tests/test_mutmut_after_run.py`, undeclared: it generates; a project generated once per class, `slice/S1`, a
baseline recorded; a fake `uv` on `PATH` writes the `.meta` files, runs nothing else, and for a second project leaves a failing
result):
- e1 after a passing and after a failing `make mutation`, and after `make mutation-full`: `git status --porcelain --ignored`
  differs from before only by `apps/service/mutants/` (ignored); `verify-stamp.py`'s ignored-files digest is what it was; the stamp
  reuses; `make verify-scoped` on the branch is not broadened *(fails today: the digest includes the copy under `mutants/`
  — the RED that brings the row; teeth: remove the row and see it fail)*.
- e2 `check-imports`: a `mutants/src/<pkg>/` copy beside `src/<pkg>/` in a Python deployable (a copy that would be read as a
  second set of modules and trip a layering or duplicate check) is neither read nor a violation, with `project.json` recording
  the deployable; a **hold** with teeth: `mutants/` at the root of a Go or TypeScript deployable, and a `mutants` directory that
  is not at a recorded Python deployable's root (`apps/service/src/mutants/`, `apps/other/docs/mutants/`) **is** read (teeth: prune
  every `mutants` and see the second fail); a Python package named `mutants` under `src/` is read.
- e3 a left-behind `mutants/` that holds a real `.venv`-like `pyvenv.cfg` or a symlink pointing back into the service: `verify-scoped`
  reads neither as a reach (`reach.py` unchanged); pinned for both shapes, with teeth (point a link outside the deployable and see a
  reach appear).
- e4 `java-quarkus` still exits 2 with its setup message on `make mutation` (changed file) and `make mutation-full` (**hold,
  teeth:** change the Quarkus message and see it fail), and a Go service beside a Python one: the changed one runs, the other is
  skipped; a Python service beside a Quarkus one: Python runs, Quarkus is `refuse`, the run exits 2 (AC-S08-6's class).
- e5 **hold** (D117's borders and `SINCE` for Python, D150): `make mutation` in CI markers, on `main`, detached and with an empty
  `SINCE` sweeps (`mutation-full`); `SINCE=<ref>` scopes Python on any checkout; `make mutation-full SINCE=<ref>` sweeps Python
  **whole** — the recipe line carries no `SINCE`, and the fake `uv` sees no `--`-names after `mutmut run`.

**GREEN** — `verify-stamp.py`: the one `EXEMPT` row, in the grouped cache rows beside `.stryker-tmp/` and
`apps/*/reports/mutation/`, in the same form; `check-imports.py`: the `skipped()` clause (the `mutants` literal built as a
segment or given a reasoned `NOT_AN_INPUT_FOR`/`EXEMPT_PATHS` row if `test_verify_scoped_table_held` or
`test_verify_stamp_lists` reads it as a path). If e3 or e5 fail for a real reason the delegate stops and names it: `reach.py` and
`rules.py` are not in this manifest.

**REFACTOR:** the `mutants` clause shares the "root of a recorded deployable of kind X, beside its manifest" helper with the Java
`target` rule rather than copying it.

**Verify:** `make test TESTS="test_mutmut_after_run test_mutation_placeholders test_mutation_scope_python $(ls tests | grep -E '^test_verify_stamp' | sed 's/\.py$//' | tr '\n' ' ') $(ls tests | grep -E '^test_verify_scoped_' | sed 's/\.py$//' | tr '\n' ' ') test_scoped_adopted test_gates_imports test_toolkit test_utf8_io"`, then
`make lint typecheck check-structure`; under `CI=true` once (the root `Makefile` runs the stamp files as this repository's own
stamp — say so in the report). Commit by path; level line as above.

**Files:** `assets/toolkit/scripts/verify-stamp.py`, `assets/toolkit/scripts/check-imports.py`,
`tests/test_mutmut_after_run.py` (new), `tests/test_verify_stamp_lists.py` (a reasoned `EXEMPT_PATHS` row if the scan demands it).

### T010 — [P] [US2] The words: the Makefile note, the mutation command, `UNWIRED`, the skill, the obligations and requirements pages, S41's fragment narrowed, ADR 0010 held (R9 · AC-S42-11 placeholder half, the *wired* half of the criteria)

- [x] **Rule 9.** Needs T002 (`mutmut.py` exists). Disjoint from the wrapper and scope-script tasks, so it may run beside them. The *(Done: 47a2d9a — also `docs/backend-obligations.md` §3 gained a `MUTATION_NOTES` row (`test_backend_obligations` required it); six `PRE_SLICE` hashes regenerated.)*
  words describe what T003–T009 build, as the plan and data-model fix them; this task reads none of their code. A Python note above
  the target in `mutmut.py` (what runs; the `.meta` report at `apps/<service>/mutants/`; that the verdict is decided in
  `scripts/mutmut-mutation.py`; the escape for an equivalent mutant — the bare `# pragma: no mutate` named in the commit, and that
  `block`, `start`/`end` and `do_not_mutate_patterns` fail the run; that the default starter's sweep reports its own survivors and the
  minimal one is green, written to *Handed back* 1 option (a) **without promising a follow-on**; why `tests/integration` is left out;
  why `-p no:xdist`); `mutation_command(["python"])` names mutmut, the wrapper and the `.meta` report, `UNWIRED` names only
  `java-quarkus`; `mutation-testing/SKILL.md` says a generated Python service is already wired and keeps every other sentence;
  `docs/backend-obligations.md` and `docs/requirements.md` say the same (the latter's "**Python** exits 2 asking for `mutmut` on the
  PATH" is replaced; "only three backends have one wired up" becomes four); `changelog.d/stryker-mutation.md`'s two Python clauses
  (*Python and `java-quarkus` still have no tool wired…*, *…stay recorded stubs…*) say `java-quarkus` only (*Handed back* 2); ADR 0010
  is read and agrees (its `Status` is `Proposed`, its decision line names `mutmut==3.8.0`).

**RED** (new examples in `tests/test_mutmut_generated.py`, named lines of `tests/test_mutation_words.py`, `tests/test_stryker_generated.py`,
`tests/test_stryker_migrate.py`):
- e1 `mutation_notes([service("service", "python")])` is non-empty and carries the facts above (each a sentence the test looks
  for); `__APP__` never survives and the service's own paths substitute; Go's, Spring's, Quarkus's and TypeScript's notes are byte for
  byte what they were *(fails today: Python has no note — `test_mutation_words.py:102` is inverted for Python only)*.
- e2 `mutation_command(["python"])` and a mixed `["go", "python"]` say `scripts/mutmut-mutation.py`, `mutants/`, `make mutation
  SINCE=<review-base>`, and that CI and the trunk sweep (S08's sentences stay); `mutation_command(["java-quarkus"])` still says the
  target refuses until a tool is wired; `UNWIRED` names exactly `java-quarkus` and not Python *(fails today: Python is in `UNWIRED`,
  `test_stryker_generated.py:265`'s assertion is inverted here)*.
- e3 `mutation-testing/SKILL.md`: the sentence saying a Python project must hand-wire mutmut is gone; the replacement says a
  generated service is already wired and names the table, the wrapper and the report; the file equals the old one except for that
  passage (a hold; teeth: edit another line).
- e4 `docs/backend-obligations.md` and `docs/requirements.md` say Python's mutation tool is mutmut and wired; no `docs/` page still
  says it is a placeholder or exits 2 asking for mutmut on the PATH; the gates page is unchanged. ADR 0010's `Status` is `Proposed`
  and its decision line names `mutmut==3.8.0` (a hold).
- e5 S41's fragment: first line `MINOR`, its Catch-up paragraph still stands alone and names `java-quarkus` as a recorded stub and
  **not** "Python and `java-quarkus`"; `test_mutation_words.py`'s D149 fragment examples (`:174–182`) and `test_stryker_migrate.py:67`
  are re-pointed at what the fragment now says (the clause about *until a later slipwai release wires mutmut* goes with Python's
  refusal, which T007 removed); `tests/test_changelog.py` holds.
- e6 the generated half: a Python project's `Makefile` note is the `mutmut.py` text; `make help` shows `mutation-full` with its
  description unchanged; `rules.json` from the generated text equals `rules.json` from the make database (S06's reader, imported)
  *(teeth: add a global variable to the note and see it fail)*.

**GREEN** — `mutmut.py` (the note text, constants), `mutation.py` (`MUTATION_NOTES`, `NAMED_FILES`, `UNWIRED`, the report line;
ends ≤ 330 lines, shortening a note rather than splitting a file — a delegate that cannot make it fit stops and names it),
`native_commands.py` only if the note is assembled there (net ≤ 2), `assets/toolkit/skills/mutation-testing/SKILL.md`,
`docs/backend-obligations.md`, `docs/requirements.md`, `changelog.d/stryker-mutation.md`.

**REFACTOR:** the `.meta` report path is spelled once in `mutmut.py` and used by the note, the command text and the
fragment-facing sentence.

**Verify:** `make test TESTS="test_mutation test_mutation_words test_mutmut_generated test_stryker_generated test_stryker_migrate test_backend_obligations test_provisional_gate test_commands test_scoped_ladder test_docs_index test_scoped_targets test_changelog test_toolkit test_utf8_io"`,
then `make lint typecheck check-structure`; the touched modules once under `CI=true`. Before editing a doc sentence:
`grep -rln "<sentence>" tests`. Commit by path; level line as above.

**Files:** `src/slipwai/project/mutmut.py`, `src/slipwai/project/mutation.py`, `src/slipwai/project/native_commands.py` (only if the
note is assembled there), `assets/toolkit/skills/mutation-testing/SKILL.md`, `docs/backend-obligations.md`, `docs/requirements.md`,
`changelog.d/stryker-mutation.md` (the Python clauses only), `tests/test_mutmut_generated.py` (new examples),
`tests/test_mutation_words.py` (named lines), `tests/test_mutation.py` (`:112–114` only, if a pin there breaks),
`tests/test_stryker_generated.py` (`:265` and `:282–283` only), `tests/test_stryker_migrate.py` (`:67` only),
`tests/test_scoped_targets.py` (`PRE_SLICE` hashes only — the note sits above `# Scoped gate`).

### T011 — [US2] A project made before is brought forward, and the fragment says what that asks of it (R10 · AC-S42-12)

- [x] **Rule 10.** Needs T009 and T010 (everything `migrate` must bring now exists) and T008. The fragment's **Catch-up.** paragraph is *(Done: d3be2e6 — no source change needed: the three-way merge keeps a hand-added dependency beside the pin and table, and a hand-written wrapper is a kept conflict.)*
  completed: it stands alone and names the `uv.lock` conflict in every Python service (take the factory's side, then run `uv lock
  --project apps/<svc>` for each service), that a leftover `mutants/` or `.mutmut-cache` may be deleted, that `make mutation` exits 2
  until the lock is redone (the wrapper's `uv sync --locked` is refused), that `make mutation-full` now runs mutmut and its sweep of
  the default starter reports the starter's own survivors (plan, *Handed back* 1(a), no promise of a follow-on), that Windows needs
  WSL, that `java-quarkus` stays a recorded stub, that `mutmut` hand-wired in a project is to be removed or kept knowingly (the scope
  script sweeps on the wrapper's change and refuses any pin but 3.8.0), that the `[tool.mutmut]` pragma forms other than the bare
  one fail the run, and that no `project.json` key changes.

**RED** (new `tests/test_mutmut_migrate.py`, undeclared; the technique of `tests/test_stryker_migrate.py` and
`tests/test_scoped_migrate.py`, **failing, never skipping,** where the commit before this slice's first (`b9f16ef`) is not in the
clone):
- e1 the fragment: first line `MINOR`; a `**Catch-up.**` paragraph naming `uv.lock`, `uv lock --project apps/`, `mutants/`,
  `.mutmut-cache`, `make mutation` exiting 2 until the lock is redone, `make mutation-full`, WSL, and the recorded stub;
  `tests/test_changelog.py` holds *(fails today: the draft says only what T002 could say)*.
- e2 a Python project generated by the commit before this slice's first, after `slipwai migrate`: `apps/service/pyproject.toml` names
  `mutmut==3.8.0` in `dev` and a `[tool.mutmut]` table that parses to data-model's, `scripts/mutmut-mutation.py` exists and is
  executable, `.gitignore` names `apps/*/mutants/`, `scripts/verify_scoped/rules.json` is regenerated, `mutation-full` is the wrapper's
  line, and `make verify-scoped` on a slice branch of it is not broadened.
- e3 a project made before whose `pyproject.toml` was edited by hand (an unrelated dependency added): `migrate` keeps the edit and adds
  the pin and the table (three-way); `uv.lock` is reported as conflicting (or left to the person) and the example follows the Catch-up —
  take the factory's lock, `uv lock --project apps/service` (skipped, with its reason, where `uv` or network is absent) — to `uv sync
  --locked` accepted and `rules.text_problem(...) is None`; a wrapper or table the project edited is not overwritten silently (the
  existing `migrate` rule for files the project owns, held with a mutmut file as the example); before the lock is redone, `make
  mutation` exits 2 with the lock line (AC-S42-12's last clause).
- e4 a Go-only project made before gains no mutmut file, and a project with two Python services gets the pin and the table in each
  service and one wrapper.

**GREEN** — `changelog.d/mutmut-mutation.md` completed. If e2–e4 fail for a real reason (the wrapper is not in `migrate`'s written set,
`pyproject.toml` merges badly) the fix is the smallest one in a file this manifest names, RED seen first; where a needed file is not
named the delegate stops and names it. If they pass at once they are written as holds and **seen to have teeth** (remove the wrapper
from the written set and see e2 fail, restore) — the fragment is the guaranteed RED.

**REFACTOR:** none expected; the fragment is edited for the reader who skips to its Catch-up.

**Verify:** `make test TESTS="test_mutmut_migrate test_mutmut_generated test_stryker_migrate test_scoped_migrate test_changelog test_toolkit test_utf8_io"`,
then `make lint typecheck check-structure`; under `CI=true` once. Commit by path; level line as above.

**Files:** `changelog.d/mutmut-mutation.md`, `tests/test_mutmut_migrate.py` (new), and, only if e2–e4 prove a gap,
`src/slipwai/project/mutmut.py` (named in the report if touched).

### T012 — [US2] One real mutmut run on a generated starter (R11 · AC-S42-1, AC-S42-2, AC-S42-4, AC-S42-5 end to end)

- [x] **Rule 11.** Needs T011. This is the **heavy** test: it is the one place the fake `uv` of T004–T006 and the `FakeRunner` of *(Done: b68b798 — a hold against real mutmut 3.8.0: scoped 2 mutants killed, sweep 6 killed, types-only module no mutant to run, weakened test 2 survivors; ~8 s warm.)*
  T007–T008 are checked against the real tool, mutmut 3.8.0 and libcst 1.9.0 (R1) — and the generation snippet and the `.meta` shape of
  T005–T006. Its file is `tests/test_mutation_scope_real_python.py` and its module docstring says **heavy — S43's list**, as
  `test_mutation_scope_real_typescript.py` carries its gate. It is gated by `backends_under_test()` naming `python`, `uv` on `PATH`
  (and network for the first `uv sync`), `skipTest` otherwise; every `subprocess.run` carries a `timeout=` (the sweep up to 600 s).
  **Honest about its RED:** the example proves behaviour T002–T011 produced, so it may pass at once. The delegate runs it first;
  whatever the real run shows wrong in the wrapper, the table, the snippet or the dispatch (R3's calls, R4's code table, the `.meta` path,
  the lock, the `PYTEST_ADDOPTS` handling) is this task's GREEN, RED seen first. If it passes untouched, it is committed as a hold and
  **seen to have teeth** by the sanctioned route — change the wrapper so a survivor's code `0` passes, run, see the weakened-test
  example fail, `git checkout -- <exact path>` — and the report says so.

**RED/hold** (one class, examples sharing one generated project, `--profile standard --frontend none --http none --event-store
memory` so the minimal starter is green, R9; `slice/S1` cut from its `main`; scratch under `/tmp/s42/`):
- e1 a changed `apps/service/src/<pkg>/<module>.py` and a test that kills its mutants: `make mutation` exits 0; the first line names the
  scope and its base, the last line counts it scoped; `apps/service/mutants/src/<pkg>/<module>.py.meta` holds the only keys that are not
  `null`; fewer mutants than e4's sweep.
- e2 the same module with the killing test weakened: `make mutation` exits 1 and names the survivor (`survived apps/service
  <pkg>.x_…__mutmut_<n> (mutmut show … in apps/service; report apps/service/mutants/)`); the previous `mutants/` was replaced.
- e3 a changed types-only module (the starter's `application/ports/read_models.py`-shaped file, declaring types only): *no mutant to run*,
  exit 0, no `mutmut run` started (the run's `mutants/` holds `{}` for it); a changed `pkg/__init__.py` mutates that file's functions only.
- e4 `make mutation-full` mutates the table's list: exit 0 on the minimal starter, every file under `src/` has a `.meta` and the sweep's
  mutants are those of every file (no named exclusion — mutmut has no coverage denominator, R2).
- e5 afterwards `git status --short` is empty and `make verify-scoped` is not broadened (AC-S42-9, end to end).

**GREEN** — only what the real run proves wrong, in the files below; otherwise none.

**REFACTOR:** none.

**Verify:** `FACTORY_BACKENDS=python make test TESTS="test_mutation_scope_real_python test_mutmut_generated"` (a hand run says so in the
report), then `make lint typecheck check-structure`; the module without `FACTORY_BACKENDS` is skipped, not failed. Commit by path; level
line as above when a `src/` or `assets/` file changed, else "reaches no user".

**Files:** `tests/test_mutation_scope_real_python.py` (new), and, only if the real run proves a defect,
`assets/languages/python/scripts/mutmut-mutation.py`, `src/slipwai/project/mutmut.py`, `assets/toolkit/scripts/mutation-scope.py`
(each named in the report if touched).

---

## Phase 2: Host closing tasks

### T013 — Every suite that reads a generated gate, once, before the gates (host task)
- [x] After T012 is committed and the chain T002 … T012 is: `make test TESTS="$(ls tests | grep -E '^test_(verify_stamp|parallel_gate|model_|gate_|verify_scoped|scoped_|mutation|mutmut|stryker|select_tests)' | sed 's/\.py$//' | tr '\n' ' ') test_matrix test_uv test_commands test_commit_boundaries test_monorepos test_layout test_changelog test_pruning test_language_skeletons test_backend_obligations"`, *(Done at fc9986c: 1722 tests OK, 4 skipped, 2250 s; the four Python locks equal `python_locks()`'s resolution (`regenerate-locks.py --check` stops on this machine's npm 9.2, as in S41); `make starters` diff is the intended set — the Python note and recipe line, the pin and table, the wrapper, the ignore line, the four locks, `rules.json`, the toolkit scripts and skill in every starter, Quarkus's command text; `make lint typecheck check-structure` green.)*
  `python3 scripts/regenerate-locks.py --check`, `make starters` and the diff of `build/` against T001's: only the intended generated
  changes (a `mutmut` dev pin and `[tool.mutmut]` per Python service, one wrapper per project with a Python service, the ignore line, the
  Makefile line and note, the changed command text, the four `uv*.lock`, Python's `UNWIRED` words gone); then `make lint typecheck
  check-structure`. Not `make verify`. A Go module cache under `/tmp/tmp*` made by a suite run is `chmod -R u+w`'d before it is removed.

*(Re-run after the answers' work, at the head after T035: the same set with `test_toolkit` and `test_utf8_io` — 1786 tests OK, 4 skipped, 2269 s, `test_matrix` and the four `test_select_tests_*` pins included; `make lint typecheck check-structure` green.)*

### T014 — Converge, passes as needed (host task)
- [x] `drive-converge` over the slice's range; findings append as tasks in Phase 3. *(Done: pass 1 not converged (T017–T021), pass 2 converged at `5a9840e`, loop stopped at its bound with T022 (MEDIUM) and T023 (LOW) in Phase 4; both `drive-converge · model: opus · delegated, fresh context`.)*

### T015 — After-converge gaps (host task)
- [x] `drive-gaps` over the slice and the code it produced; findings append in Phase 3. *(Done: eight findings, two product questions; T024–T029 in Phase 3; findings 1 and 4 handed back in `plan.md` *Blocked on*.)*

### T016 — The demo, with the measurement (host task; AC-S42-13)
- [ ] The hand runs quickstart scenarios 1–6 in a project generated by this worktree's `./slipwai`, and records `make mutation` against
  `make mutation-full` on a two-service Python starter (the default answers plus `add-service billing --backend python`): wall time,
  mutant counts, `nproc` and CPU model. The Phase 1 real run (T012) is evidence for AC-S42-1, -2, -4, -5, not for this. **And what
  *Handed back* 1 asks of the demo:** the default starter's sweep red, naming survivors that are not equivalent (R9's
  `settings.py` `"; "` → `"XX; XX"` among them); the minimal starter and the bare `add-service` skeleton green.

## Phase 3: Findings appended by converge and gaps

### Converge pass 1 (T014, cruise iteration 30) — two HIGH, so the loop re-opens

Judged at `bda2f7a` (range `15bf72b..bda2f7a`). Before the pass, the slice's fast suites were green (`test_mutmut_config
test_mutmut_setup test_mutmut_verdict test_mutation_scope_python test_mutation_sweeps_python test_mutation_words
test_changelog`: 108 tests OK, 1 skipped). Twelve hand mutations of the wrapper and the scope script were applied one at a time,
those suites run, and each file restored with `git checkout -- <path>`. **All twelve were killed**: code 5 read as killed, no
clean slate, `--` in a sweep, the libcst closure dropped, `PYTEST_ADDOPTS` kept, `do_not_mutate` ignored, `[` not refused, the
wrapper's change not sweeping, no `drop_report` for Python, no `do_not_mutate_patterns` check, a missing table defaulted, a
`3.8.*` prefix accepted. The findings below come from reading the wrapper against mutmut 3.8.0's source in
`/tmp/s42/research/p/apps/service/.venv` and from probes through the slice's own fake-`uv` harness (scratch under
`/tmp/s42/converge/`). They are not hand mutations. No `.codegraph/`: callers and blast radius come from `grep -rn`.

### T017 — [US2] HIGH · Every spelling of mutmut 3.8.0's silencing pragma fails the run, and the check runs before any *no mutant to run* exit (D212 items 1, 4, 6; D219's reason, *Applied, not decided* 2; AC-S42-5, -6)
- [x] **The rule the published words promise doesn't hold.** The fragment, the Makefile note (`src/slipwai/project/mutmut.py`) *(Done: dcbfc1a — the reader is `_parse_pragma_token`'s rule over `tokenize` comments, checked against the 3.8.0 install spelling by spelling; checked over the given files mutmut mutated (a file outside the targets silences nothing); `mutate_only_covered_lines` fails beside `do_not_mutate_patterns`.)*
  and the skill all say `# pragma: no mutate block`, `start`/`end` and `do_not_mutate_patterns` "fail the run". Two holes let a
  silenced mutant through to a green run:
  1. *The reader is not mutmut's.* mutmut 3.8.0's `_parse_pragma_token` (`mutmut/mutation/pragma_handling.py:98–110`) treats a
     comment as a pragma when it contains `# pragma:` and `no mutate` anywhere. It takes the tail after `no mutate`, runs
     `lstrip(": ")` on it and reads the first word before a comma. The wrapper's `SILENCING`
     (`assets/languages/python/scripts/mutmut-mutation.py:71`) is the regex `#\s*pragma:\s*no mutate\s+(block|start|end)\b`.
     **Reproduced against the installed mutmut:** `# pragma: no mutate: block` → `block`, `# pragma: no cover, no mutate block` →
     `block`, `# pragma: no mutate:start` → `start`. The wrapper's regex matches none of the three. Through the fake-`uv` harness of
     `tests/test_mutmut_verdict.py`, a scoped `src/pkg/a.py` holding `# pragma: no mutate: block` above `def g` printed
     `1 mutants: 1 killed, 0 no tests (reported, never failed); passed`, exit 0. The reverse also happens: `#pragma: no mutate
     block`, with no space, is flagged by the wrapper, but mutmut ignores it, so the wrapper fails a run over a comment that
     silences nothing.
  2. *The check runs too late.* `silenced` is called only from `judge` (`:420`, `:447`). `plan` exits 0 first (`:397–404`)
     when every given file's `.meta` is `{}`. A given file whose functions all sit inside `# pragma: no mutate start` … `end`
     (or that a `do_not_mutate_patterns` table empties) gets `{}` from mutmut. **Reproduced:** that file printed `no mutant to
     run — src/pkg/a.py: mutmut found no function to mutate in it`, exit 0.
- **RED:** a table test in a new module, one example per spelling. Each of these fails the run with the data-model line naming
  `<service>/<file>:<line>`: `: block`, `:block`, `, no mutate block` after another pragma, `start`/`end` with and without a colon.
  These are not flagged, as a hold with teeth: the bare `# pragma: no mutate`, `# pragma: no mutate, <reason>`, `#pragma: no
  mutate block` (not a pragma to mutmut), and the same text inside a string literal. Also: a scoped given file wholly inside
  `start`/`end` → exit 1 with the pragma line, never *no mutant to run*. A `do_not_mutate_patterns` table with a scoped `{}` file →
  exit 1. A sweep whose every file is silenced names the pragma beside *found nothing*. Hold: a genuinely function-less file is
  still *no mutant to run*, exit 0.
- **GREEN (the class):** one reader of the token that is mutmut 3.8.0's rule, applied to comments only (stdlib `tokenize`
  `COMMENT` tokens, not raw lines). `silenced` runs on every given file (scoped) or every `.meta` file (sweep), and the table
  check runs in `plan`, before the *nothing under*, *no mutant to run* and *found nothing* exits. One function, so the verdict
  and the empty exits can't disagree about what silences.
- **Rides along (host, from pass 1's question):** a table setting `mutate_only_covered_lines = true` fails the run in `plan` with
  one line naming the setting (and `data-model.md`'s row for it), as `do_not_mutate_patterns` does; the fragment, the note and the skill
  name it beside `do_not_mutate_patterns`.
- **Files:** `assets/languages/python/scripts/mutmut-mutation.py`; `src/slipwai/project/mutmut.py` (the note's sentence);
  `changelog.d/mutmut-mutation.md` and `assets/toolkit/skills/mutation-testing/SKILL.md` (the sentence naming what fails);
  `specs/001-faster-slipwai/slices/S42-mutmut-mutation/data-model.md` (the row); `tests/test_scoped_targets.py` (hashes, if the note
  moves); `tests/test_mutmut_silenced.py` (new, because
  `tests/test_mutmut_verdict.py` is at 350 lines; declared `TEST_SELECTION` reads = the wrapper);
  `tests/test_select_tests_real_loaders.py` (its `READS` row); `tests/test_mutmut_verdict.py` (only the e6 examples moved out,
  if they move).

### T018 — [US2] HIGH · Every fragment of the release says what the release ships: S08's stops saying Python (and TypeScript) has no tool (AGENTS.md *Write the entry in the same commit*; Constitution I's catch-up note; *Handed back* 2's class)
- [x] **RED evidence (reproduced):** `changelog.d/scoped-mutation.md:3` says *"TypeScript, Python and `java-quarkus` have no *(Done: 8cf9761 — only S08's fragment held the clause; a hold reads every `changelog.d/*.md`.)*
  mutation tool wired, so for them `make mutation` refuses a changed service … A Python service stays refused until a later
  slipwai release wires mutmut, whether or not mutmut is installed, and `make mutation-full` runs mutmut today where it is
  installed."* Its **Catch-up** (`:5`) says the same twice. `tests/test_mutation_words.py:167–182` pins those words
  (`"TypeScript, Python and \`java-quarkus\`"`, `"until a later slipwai release wires mutmut"`, `"\`make mutation-full\` runs
  mutmut today where it is installed"`). `VERSION` is `1.6.0.dev0` and `CHANGELOG.md` has no 1.6.0 entry, so S08's, S41's and
  S42's fragments are all assembled into one entry by `make release`. That entry would tell a maintainer reading the Catch-up
  that a Python service refuses with its setup message, two paragraphs after saying it is wired. *Handed back* 2 narrowed S41's
  fragment only. The TypeScript half of the same clause is S41's leftover in S08's fragment, and is part of this class.
- **RED:** a cross-fragment hold over every `changelog.d/*.md`: no fragment says Python or TypeScript has no mutation tool wired,
  or that a Python service is refused until a later release. Today it fails on `scoped-mutation.md`. Re-point the
  `FragmentTest` pins at the narrowed words. S08's `**Catch-up.**` still stands alone and still names `java-quarkus` as the
  recorded stub.
- **GREEN (the class):** narrow each such clause in every fragment for this release to `java-quarkus`. Say nothing about Python
  or TypeScript in S08's fragment beyond what S08 shipped for Go and Spring. S41's and S42's fragments say what those slices
  wired.
- **Files:** `changelog.d/scoped-mutation.md`, `tests/test_mutation_words.py` (`FragmentTest` only),
  `tests/test_mutation_migrate.py` (only if its Catch-up pin at `:75` reads the narrowed clause).

### T019 — [US2] MEDIUM · `targets()` accepts no `source_paths` entry that `matched()` cannot place as mutmut does: a mutated file is never named outside the configured targets (R2, data-model *targets*/*matched*; AC-S42-2, -8)
- [x] **RED evidence (reproduced, the wrapper loaded with bytecode off):** `check_paths` (`mutmut-mutation.py:115–123`) *(Done: 68d4e02 — one canonical `source_root`; data-model's *targets* paragraph updated by the host.)*
  accepts `["./src"]`, `["src/./pkg"]`, `["."]` and a file entry `["src/app.py"]`. For each of them, `matched` (`:150–158`)
  returns `False` for both `src/pkg/a.py` and `src/app.py`. mutmut reads each entry as `Path(entry)`
  (`mutmut/configuration.py:144`) and walks it, a file entry included (`mutmut/utils/file_utils.py:26–34`), so it does mutate
  those files. `wrapper_plan` in `assets/toolkit/scripts/mutation-scope.py` then names every changed file *outside mutmut's
  configured targets* and starts nothing, exit 0: a green over code the table covers. The plan's own rule (Technical Context,
  R2) is that the reader takes the subset the factory writes and calls the rest unreadable rather than guessing. These four forms
  are read, and read wrongly.
- **RED:** in `tests/test_mutmut_config.py`, one example per form. Each is `Unreadable` naming the value. Alternatively, each is
  normalised as `PurePosixPath` does and then matches as mutmut walks it; pick one, not both. In
  `tests/test_mutation_scope_python.py`, the same tables reach `Plan.unreadable` (a sweep) or a scoped run, never *outside
  configured targets*. Hold: `["src"]` and `["src/"]` are unchanged.
- **GREEN (the class):** one normalisation of a `source_paths` entry, shared by `check_paths` and `matched`, so that "readable"
  and "where it matches" cannot drift. Recommended: the canonical relative directory form only. Anything else is `Unreadable`, so
  the service sweeps, which fails closed.
- **Files:** `assets/languages/python/scripts/mutmut-mutation.py`, `tests/test_mutmut_config.py`,
  `tests/test_mutation_scope_python.py`.

### T020 — [US2] LOW · A `mutants/` the delete could not remove fails the run with exit 2, never a verdict over it (D212 item 7)
- [x] `clean` (`mutmut-mutation.py:351–355`) calls `shutil.rmtree(..., ignore_errors=True)` and goes on. If any entry survives (a *(Done: c9b640d — both wrappers' clean-slate steps refuse with exit 2 where something survived; `drop_report` in `mutation-scope.py` still warns and goes on (outside the manifest; left for pass 2 to judge).)*
  read-only directory, a file held open on a mounted volume), mutmut's `copy_src_dir` skips every target that already exists
  (`mutmut/utils/file_utils.py:55–56`), so a stale copy, or a stale `.meta` with its old exit codes, can be read as this run's.
  *Evidence by reading; not run against real mutmut.* **RED:** a `mutants/sub/` made read-only (`chmod 0o555`, restored in
  cleanup) → exit 2 with one line naming `<service>/mutants/` and what to delete; generation is never started (the fake `uv`
  logs no `python -c`). **GREEN (the class):** every clean-slate step, here and in `stryker-mutation.py`'s report delete, checks
  that what it removed is gone and refuses if it is not.
- **Files:** `assets/languages/python/scripts/mutmut-mutation.py`, `tests/test_mutmut_setup.py` (or `test_mutmut_silenced.py`
  if T017 lands first and the module has room); `assets/languages/typescript/scripts/stryker-mutation.py` and
  `tests/test_stryker_verdict.py` only if the same shape is found there.

### T021 — [US2] LOW · The words in files a project carries say what the code does now (Constitution I; the *words* level)
- [x] **RED evidence (reproduced):** the wrapper's module docstring still says *"This is the skeleton past the configuration: *(Done: 40d8610 — the `(T00n)` parentheticals in the wrapper's comments are left, as in S41's wrapper.)*
  it refuses to run, which can only fail, never pass."* (`assets/languages/python/scripts/mutmut-mutation.py:14`). That is
  T002's transient, and every generated Python project now carries it. `check-imports.py`'s `deployables` docstring
  (`assets/toolkit/scripts/check-imports.py:150–152`) still lists *"the six nobody reads … `.stryker-tmp` and the `target`"* and
  does not name `mutants` at a recorded Python deployable's root, which `OUTPUT` (`:81`) now prunes. **RED:** a words hold that
  the wrapper's docstring does not contain `skeleton`/`refuses to run`, and that `check-imports.py`'s docstrings name every
  `OUTPUT` entry. **GREEN (the class):** grep each file this slice touched under `assets/` for transient words (`skeleton`,
  `until T0`, `not wired by this script yet`) and for prune lists that omit `OUTPUT`'s entries.
- **Files:** `assets/languages/python/scripts/mutmut-mutation.py` (the docstring only), `assets/toolkit/scripts/check-imports.py`
  (docstrings only), `tests/test_mutmut_generated.py` (one words hold).

### After-converge gaps (T015, cruise iteration 30) — `drive-gaps · model: opus · delegated, fresh context`

Eight findings (one HIGH, four MEDIUM, three LOW) and two product questions, from real runs of generated projects (the
worktree's `./slipwai`; the main checkout's for a project made before) and text search (no `.codegraph/`). Finding 1 (HIGH: `make
mutation-full` stops at the first Python service that fails, so on the default two-service starter `apps/billing` is never
mutated — AC-S42-4, -13) and finding 4 (MEDIUM: `add-service --backend python` in a project an older factory wrote leaves the old
`mutation-scope.py` and `verify-stamp.py`, so every scoped run sweeps and the stamp cannot reuse) each turn on a product question,
recorded in `plan.md` *Blocked on* and handed back; no task is cut for them until the answer. The rest:

### T024 — [US2] MEDIUM · The quickstart says what the starter does: `billing` carries the first service's answers and fails the same way, the scoped `settings.py` run fails on its two survivors, and step 6 records a passing `make verify` before it claims reuse (AC-S42-13; gaps 2)
- [x] **RED evidence (gaps, real run):** `add-service billing --backend python` takes the first service's answers (FastAPI, *(Done: 36f2471 — the green scoped example is `src/demo/__init__.py`; step 2 awaits Q1.)*
  Postgres) and its `mutmut-mutation.py apps/billing` ends `992 mutants: … 114 survived; failed`; the scoped run on `settings.py`
  fails on `demo.settings.x_load_settings__mutmut_3` and `_6`; nothing in the steps runs `make verify` before step 6. **GREEN (the
  class):** every expectation line of `quickstart.md` read against what that step prints on the default starter; the scoped example
  is a file whose mutants the starter's tests kill, and the red one is named as the starter's own survivors. **Files:**
  `specs/001-faster-slipwai/slices/S42-mutmut-mutation/quickstart.md`.

### T025 — [US2] MEDIUM · The Catch-up gives the conflict steps for every service whose manifest or lock the project changed, not only one `add-service` wrote (AC-S42-12; gaps 3)
- [x] **RED evidence (gaps, real migrate):** a project made before, with `iniconfig==2.1.0` added to the dev group and relocked, *(Done: e580bbb — `uv add --dev` relocked conflicts on both files; the Catch-up's steps run end to end in the test; no Q2 sentence.)*
  stops `migrate` with `UU apps/service/pyproject.toml` and `UU apps/service/uv.lock`; the Catch-up says the factory's `uv.lock`
  arrives in that case. **RED:** a `tests/test_mutmut_migrate.py` example of that project (relocked dependency of its own) asserts
  the two conflicts, and the Catch-up pin requires the steps for it. **GREEN (the class):** the Catch-up's conflict paragraph covers
  every service whose `pyproject.toml` or `uv.lock` the project changed since generation (an own dependency, `add-service`), with
  one set of steps (take the factory's side, add back the project's own lines, `uv lock --project apps/<service>`). Rides with T023.
  **Files:** `changelog.d/mutmut-mutation.md` (Catch-up), `tests/test_mutmut_migrate.py`.

### T026 — [US2] MEDIUM · A `uv sync --locked` that fails says what uv said, and names a lock disagreement only where it is one (AC-S42-10, D212 item 5; gaps 5)
- [x] **RED evidence (gaps, real run):** offline with an empty cache, on a fresh project whose `uv lock --check` passes, the wrapper *(Done: 33eb09a — a mismatch is told by uv's `--locked` wording; any other failure prints uv's last non-hint stderr line, checked against real offline and mismatch runs.)*
  printed `apps/service/uv.lock does not agree with apps/service/pyproject.toml; run uv lock --project apps/service, then this
  again`, exit 2; `uv()` captures and drops uv's output (`mutmut-mutation.py:332`). **RED:** fake `uv sync` exiting 1 with an
  offline/network message on stderr → exit 2, one line carrying uv's last stderr line; with the lock-mismatch message uv 0.12
  prints (read it from a real run in `/tmp/s42/`) → the existing *does not agree* line. **GREEN (the class):** every subprocess the
  wrapper runs and judges by exit status (`uv sync`, the version probe, the generation step) reports the tool's own last error line
  where it fails. **Files:** `assets/languages/python/scripts/mutmut-mutation.py`, `tests/test_mutmut_setup.py`,
  `specs/001-faster-slipwai/slices/S42-mutmut-mutation/data-model.md` (the row).

### T027 — [US2] LOW · `data-model.md` fixes every line the wrapper prints (gaps 6)
- [x] The lines not fixed: `another mutmut run of <svc> holds …`, `mutmut could not generate mutants for <svc> (exit n)`, *(Done: fba5516 — the test reads `data-model.md` under `specs/` (see T030).)*
  `<svc>/mutants/ could not be removed …`, `<svc>/<file>: mutmut left no readable .meta …`, the no-`tomllib` setup line. **GREEN
  (the class):** every `say(` in the wrapper has its row, and a test reads each data-model row's fixed text from the wrapper's
  source (or the rows are copied from the code verbatim, checked by a test). **Files:**
  `specs/001-faster-slipwai/slices/S42-mutmut-mutation/data-model.md`, `tests/test_mutmut_generated.py` (one words hold, if added).

### T028 — [US2] LOW · `docs/requirements.md` says the host `python3` must be 3.11+ for a Python service's mutation run (AC-S42-7; gaps 7)
- [x] The row says "Python 3 and `uv`"; on 3.10 a changed service sweeps and the wrapper exits 2 at the table. **GREEN:** the row *(Done: b75a5cf.)*
  names 3.11+ and why (`tomllib`), and says what 3.10 does. **Files:** `docs/requirements.md` and its pinning tests (`grep -rln`).

### T029 — [US2] LOW · Each backend's Makefile note is its own block, and no generated note line runs past 120 columns after the paths are substituted (gaps 8)
- [x] In a Go + Python project the mutmut note starts on the line after the Go note's last, with no blank comment line, and two *(Done: fa9a9a5 — every backend's long note lines refilled after substitution, notes joined by one `#` line; twelve shapes' digests moved.)*
  lines pass 120 columns once `__APP__` is `apps/service` and `apps/billing`. **GREEN (the class):** `mutation_notes` separates every
  note from the next, and every backend's note is wrapped so that its substituted lines stay within 120 columns for two services —
  checked by a test over every note and a two-service project of each backend that names files. **Files:**
  `src/slipwai/project/mutation.py`, `src/slipwai/project/mutmut.py`, `tests/test_mutmut_generated.py`,
  `tests/test_scoped_targets.py` (hashes), and `src/slipwai/project/stryker.py` only if its note is one of the long ones.

## Phase 4: After acceptance (host tasks)

(the adversary pass, mutation, both full gates and the register row follow the demo as in S41 T018–T021 and are appended
here; converge pass 2 stopped at the loop's bound and left the two below, neither of which re-opens it)

### T022 — [US2] MEDIUM · A `[tool.mutmut]` table that sets `max_stack_depth` fails the run in `plan`, beside `do_not_mutate_patterns` and `mutate_only_covered_lines` (D212 items 1–2, 6; D219's reason as *Applied, not decided* 2 and 5 apply it; converge pass 2)
- [x] **RED evidence (reproduced against real mutmut 3.8.0, scratch `/tmp/s42/converge2/probe`).** mutmut records a function *(Done: 129756f, with T023 — `max_stack_depth` other than `-1` fails in `plan`; every other `Config` key judged unable to pass a survivor under a clean slate.)*
  as reached by a test only when the call is fewer than `max_stack_depth` user frames deep (`mutmut/stats.py:155–169`,
  `record_trampoline_hit`), and a mutant of a function no test is recorded reaching gets exit `33`, *no tests*. A
  `src/calc.py` with `helper(x)` called by `api(x)`, and a weak test `assert api(1) is not None`: without the key, both of
  `helper`'s mutants are `0`, *survived*. With `max_stack_depth = 1` in `[tool.mutmut]` they are `33`. The wrapper's
  `STATUS` (`assets/languages/python/scripts/mutmut-mutation.py:63`) counts `33` and never fails it, and `silenced`
  (`:483–496`) does not read the key. So a scoped run over a change to `helper` alone ends `2 mutants: … 2 no tests
  (reported, never failed); passed`, exit 0, over two survivors a test reaches. D212 item 2 counts *no tests* because a
  missing test is a coverage question. Here the test exists and runs the line, and the setting hides the result. That is
  D219's reason, the same one the host applied to `mutate_only_covered_lines` (pass 1's question, plan item 5).
- **RED:** in `tests/test_mutmut_silenced.py` (166 lines), beside e3: a table setting `max_stack_depth = 1` fails a scoped
  run in `plan` with one line naming the setting, exit 1, and no mutmut run is started. A sweep fails too. Hold:
  `max_stack_depth = -1` (mutmut's default) and an absent key are not flagged. *Teeth:* drop the branch and see the first
  example pass.
- **GREEN (the class):** sweep mutmut 3.8.0's `Config` (`mutmut/configuration.py:178–221`) for every key that changes
  which mutant reaches the verdict, or under which status, without a per-mutant comment. Each one is either named in
  `silenced` or recorded with a reason it cannot pass a survivor. Read in pass 2: `do_not_mutate_patterns` and
  `mutate_only_covered_lines` are named. `max_stack_depth` is the one left. `type_check_command` (`37`) and the timeout
  knobs can only fail. `pytest_add_cli_args_test_selection` that selects no test stops mutmut before testing, which fails
  as *not checked* (plan, *Open questions*). Narrowing it is the project's own test suite, not a silencing. `debug`,
  `also_copy`, the tracking keys and the forkserver keys change no status under a clean slate. The fragment, the note and
  the skill name the new key beside the other two.
- **Product reading (the host's, as for item 5):** (a) fail the run, as the two siblings do. **Recommended:** it is the
  same reading already applied, and no table the factory writes sets the key. (b) Allow it, because a table change already
  sweeps. But the sweep reads the same `33`s and is green too.
- **Files:** `assets/languages/python/scripts/mutmut-mutation.py`; `tests/test_mutmut_silenced.py`;
  `src/slipwai/project/mutmut.py` (the note's sentence) and `tests/test_scoped_targets.py` (hashes, if the note moves);
  `changelog.d/mutmut-mutation.md` and `assets/toolkit/skills/mutation-testing/SKILL.md` (the sentence naming what fails);
  `tests/test_mutmut_generated.py` (its pin of the named settings); `specs/001-faster-slipwai/slices/S42-mutmut-mutation/data-model.md`
  (the row, :83) and `plan.md` (*Applied, not decided*, as item 5's sibling; host).

### T023 — [US2] LOW · The fragment's Catch-up names every setting the wrapper fails, and stops saying that any pragma other than the bare one fails (Constitution I's catch-up note; T017's rides-along, left half-done)
- [x] **RED evidence (read):** T017's rides-along said that the fragment, the note and the skill name *(Done: 129756f — the fragment's two paragraphs, the note, the skill and data-model name the same three settings and three pragma words, checked by a test.)*
  `mutate_only_covered_lines` beside `do_not_mutate_patterns`. The fragment's first paragraph (`changelog.d/mutmut-mutation.md:3`),
  the note (`src/slipwai/project/mutmut.py:55–56`) and the skill (`SKILL.md:95`) do. The **Catch-up** (`:5`) still says only
  *"Pragma forms other than the bare `# pragma: no mutate`, and `do_not_mutate_patterns` in `[tool.mutmut]`, fail the run."*
  Its reader is the maintainer whose mutmut was wired by hand, which is the one project likely to carry
  `mutate_only_covered_lines = true` (and, after T022, `max_stack_depth`). That sentence also claims more than the code does.
  `# pragma: no mutate, a reason`, `# pragma: no mutate: a reason` and `#pragma: no mutate block` are not the bare form, and
  they pass, as `tests/test_mutmut_silenced.py:52–54` holds.
- **RED:** `tests/test_mutmut_migrate.py`'s Catch-up pin (`:45`) also requires `` `mutate_only_covered_lines` `` (and
  `` `max_stack_depth` `` once T022 lands) and no longer pins "Pragma forms other than".
- **GREEN (the class):** each of the fragment's two paragraphs, the note and the skill names the same list of settings that
  fail and the same three pragma words (`block`, `start`, `end`). Fix them in one commit with T022, so the list is written
  once and checked in each place.
- **Files:** `changelog.d/mutmut-mutation.md` (Catch-up only), `tests/test_mutmut_migrate.py` (the pin only).

### The answers (cruise iteration 30): D223, D224, D225, D226 — the tasks they need

D226 confirms the six readings as built (no task). D223 (Q1), D224 (Q2) and D225 (*Handed back* 1) need T031–T033; T030
above rides with them.

### T031 — [US2] HIGH · The wrapper takes several services, runs each fully and fails at the end (D223 item 2; AC-S42-4 as amended)
- [x] **RED:** in a new `tests/test_mutmut_services.py` (fake `uv` as `tests/test_mutmut_verdict.py`'s, imported, not copied): *(Done: e060dfa — the lock is released in a `finally` after each service's turn; one service prints what it printed before.)*
  `mutmut-mutation.py apps/a apps/b` where `apps/a`'s `.meta` holds a survivor and `apps/b`'s is all killed → both services are
  generated and judged (the fake logs a generation and a `mutmut run` in each, each from a fresh `mutants/`, each under its own
  lock), one result line per service, then one summary line `mutation: 2 swept; failed: apps/a`, exit 1 — the first non-zero in
  service order (a setup exit 2 in `apps/b` after a verdict 1 in `apps/a` → exit 1; reversed → 2); both green → `mutation: 2 swept;
  passed`, exit 0; `--file` with two services → exit 2 with the usage line, nothing started; one service keeps today's output
  byte for byte (no summary line) — a hold with teeth. **GREEN (the class):** every per-service step (refusal, setup, lock,
  clean, generate, run, judge) runs inside one service's turn, so no service's failure or exit leaks into the next; the usage
  line and data-model's rows say the new shape. **Files:** `assets/languages/python/scripts/mutmut-mutation.py`,
  `tests/test_mutmut_services.py` (new), `tests/test_select_tests_real_loaders.py` (its `READS` row),
  `specs/001-faster-slipwai/slices/S42-mutmut-mutation/data-model.md` (the rows and the usage).

### T032 — [US2] HIGH · All of a project's Python services share one `mutation-full` line (D223 item 1)
- [x] **RED:** `tests/test_mutmut_generated.py` (or a new `tests/test_mutmut_recipe.py` if it is at 350): a two-Python project's *(Done: ace93f8 — `one_line()` in `mutmut.py`, called by `merged()`, and the same rule in `factory_recipe`; D223's *would reverse if* did not hold: `billing` then `ledger` added one at a time render the line byte for byte.)*
  `mutation-full` recipe holds exactly one Python line, `python3 scripts/mutmut-mutation.py apps/service apps/billing`, where the
  first Python line sits today; Go before and after Python (`go`, `python`, `go`, `python` service order) keeps every Go line byte
  for byte and the one Python line at the first Python position; `factory_recipe` equals the generated recipe for those shapes
  (`tests/test_mutation_targets.py`'s check); `make mutation` on a slice branch of a two-Python project does not sweep with
  *the recipe is not the one the factory wrote*; a project whose Python services were added one at a time with `add-service`
  renders the same line byte for byte (D223's *would reverse if* — say what it showed). **GREEN (the class):** one rule, in
  `native_commands.py`'s merge, that collapses every Python service's wrapper line into one at the first one's place, and the
  same rule in `factory_recipe`; no other backend's line moves (AC-S42-11). **Files:** `src/slipwai/project/native_commands.py`,
  `src/slipwai/project/mutmut.py`, `assets/toolkit/scripts/mutation-scope.py` (`factory_recipe` only), the test module,
  `tests/test_scoped_targets.py` (hashes of the moved shapes), `tests/test_mutation_targets.py` (only if a shape needs adding).

### T033 — [US2] MEDIUM · The note and the fragment say what D223, D224 and D225 decided (D223 item 4, D224 item 1, D225 item 1; AC-S42-12)
- [x] **RED:** pins in `tests/test_mutmut_generated.py` / `tests/test_mutmut_migrate.py`: the Makefile note says the sweep runs *(Done: d61ccb9 — the note, the fragment's two paragraphs and the skill share the sweep's two sentences; pins in `tests/test_mutmut_migrate.py` (`SweepWordsTest`).)*
  every Python service and fails at the end naming each failed one, and that in a mixed project a failing Go or TypeScript service
  listed earlier still stops the sweep before Python runs; the note says the default starter's sweep reports its own starter
  tests' survivors and that a scoped run on a slice editing one of those files meets them (already there — hold), the minimal
  starter green; the fragment says the same, names `S45-python-starter-kills-mutants`' fix in a user's words (a later release
  makes the starter's tests kill them) and the mixed-project sentence; the Catch-up gains D224 item 1's sentence (migrate and
  commit before `add-service` of a Python or TypeScript service in a project an older factory last wrote; what is and is not
  brought; every `make mutation` sweeps and the stamp does not reuse until `migrate` runs; a `migrate` afterwards skips the notes
  in between). **GREEN (the class):** the note, the fragment's two paragraphs and the skill say one thing about the sweep's
  shape. **Files:** `src/slipwai/project/mutmut.py` (the note), `changelog.d/mutmut-mutation.md`,
  `assets/toolkit/skills/mutation-testing/SKILL.md` (only if it describes the sweep), `tests/test_mutmut_generated.py`,
  `tests/test_mutmut_migrate.py`, `tests/test_scoped_targets.py` (hashes).

### T030 — [US2] LOW · No factory test reads a slice's record under `specs/` (T027's words hold; found at host triage)
- [x] T027's hold reads `specs/001-faster-slipwai/slices/S42-mutmut-mutation/data-model.md`, so archiving or moving the slice *(Done: 58e3d72 — T027's check moved to `tests/test_mutmut_lines.py` with the factory's own table and a guard that no `tests/test_mutmut_*.py` reads a slice record; other slices' tests that read `specs/` (`test_verify_scoped_contracts.py`, S06's) are outside this slice.)*
  record fails the factory suite rather than the slice. **GREEN (the class):** the wrapper's fixed lines are held where the
  factory keeps its own contracts (the test's own table, or a page under `docs/`), and `grep -rn "specs/" tests` finds no test that
  reads a slice record. **Files:** `tests/test_scoped_targets.py` or the test holding T027's check, and whatever it moves the table to.

### Converge pass 3 (Phase 4; neither re-opens the loop)

### T034 — [US2] MEDIUM · The mixed-project sentence names every line that stops the sweep before or after Python, not only Go and TypeScript (D223 item 4's class; converge pass 3)
- [x] **RED:** in `tests/test_mutmut_migrate.py` (`SweepWordsTest`) or `tests/test_mutmut_generated.py`, reach the case the sentence *(Done: 961ca84 — one sentence in the note, both fragment paragraphs and the skill; no backend list.)*
  leaves out. A `java-quarkus:apps/service, python:apps/second` project (`QUARKUS_AND` in `tests/test_mutation_scope_python.py`)
  has a `mutation-full` recipe whose first line is the setup placeholder `@echo '…'; exit 2`, so make stops there on every run
  and the Python line never starts. A `java-spring` service listed earlier with a survivor stops it the same way. The note
  (`src/slipwai/project/mutmut.py:75–76`), the fragment (`changelog.d/mutmut-mutation.md:3` and the Catch-up at `:5`) and the
  skill (`assets/toolkit/skills/mutation-testing/SKILL.md:95`) say only "a failing Go or TypeScript service listed earlier". None
  of them says the converse either: the one Python line fails at the end, so make never runs a Go, TypeScript or Java line after
  it. That is new with D223 item 1 for a Go or TypeScript service that sat *between* two Python services, because it now runs
  after both (`full_recipe(["go:apps/a","python:apps/b","go:apps/c","python:apps/d"])` → `[go a, python b d, go c]`). The pin
  fails until the words name the class. **GREEN (the class):** one sentence, shared by the note, both fragment paragraphs and the
  skill, says what make does with the lines: each other service's line still stops the sweep where it fails, before or after the
  one Python line, and a Java Quarkus service's setup line always does. Name no backend list that a new backend would leave stale.
  This is the wording of D223 item 4 widened to its reason, and no product choice: the behaviour is the one D223 decided.
  **Files:** `src/slipwai/project/mutmut.py` (the note), `changelog.d/mutmut-mutation.md`,
  `assets/toolkit/skills/mutation-testing/SKILL.md`, `tests/test_mutmut_migrate.py`, `tests/test_scoped_targets.py` (hashes).

### T035 — [US2] LOW · The Catch-up says the sweep's shape once
- [x] The Catch-up (`changelog.d/mutmut-mutation.md:5`) says "`make mutation-full` now runs mutmut for every Python service." and *(Done: ca2fbc6 — the Catch-up's own repetition removed; the first paragraph and the Catch-up still share the sweep's words, as T033 requires.)*
  then, at once, "`make mutation-full` runs every Python service, each from a fresh `mutants/` …". These are T033's two
  sentences, set beside the one that was already there. Keep the second. **GREEN:** no sentence of the fragment repeats another
  (it rides with T034's edit to the same paragraph). **Files:** `changelog.d/mutmut-mutation.md`.

---

## Parallel opportunities

By manifest (each task's *Files* line):

| Task | Writes | Needs another task's file |
|---|---|---|
| T002 | `mutmut.py` (new), `python.py`, `native_commands.py`, `backends.py`, `gitignore.py`, wrapper skeleton (new), `app/pyproject.toml`, 4 `uv*.lock`, `mutation-scope.py` (`factory_recipe` only), fragment (new), `test_mutmut_generated.py` (new), `test_mutation_placeholders.py` (one hold + one row), `test_uv.py` (`:59`), `test_scoped_targets.py` (hashes), `test_select_tests_cross_reads.py` (one row) | none |
| T003 | wrapper, `test_mutmut_config.py` (new), `test_select_tests_real_loaders.py` (a row) | T002's skeleton |
| T004 | wrapper, `test_mutmut_setup.py` (new), `test_select_tests_real_loaders.py` (a row) | T003 |
| T005 | wrapper, `test_mutmut_verdict.py` (new), `test_select_tests_real_loaders.py` (a row) | T004 |
| T006 | wrapper, `test_mutmut_verdict.py` | T005 |
| T007 | `mutation-scope.py`, `test_mutation_scope_python.py` (new), `test_mutation_placeholders.py`, `test_mutation_words_script.py`, `test_mutation_dry_run.py`, `test_stryker_after_run.py` | T003 (`targets`, `matched`, `refused`) loaded by path; T002 |
| T008 | `mutation-scope.py`, `test_mutation_sweeps_python.py` (new) | T007; T003 (`versions`) |
| T009 | `verify-stamp.py`, `check-imports.py`, `test_mutmut_after_run.py` (new), `test_verify_stamp_lists.py` | T006 (a run that completes), T007, T002 |
| T010 | `mutmut.py`, `mutation.py`, `native_commands.py` (maybe), `SKILL.md`, two `docs/` pages, `changelog.d/stryker-mutation.md`, `test_mutmut_generated.py`, `test_mutation_words.py`, `test_mutation.py`, `test_stryker_generated.py`, `test_stryker_migrate.py`, `test_scoped_targets.py` (hashes) | T002 |
| T011 | `mutmut-mutation.md` fragment, `test_mutmut_migrate.py` (new), `mutmut.py` (only if a gap is proved) | T008, T009, T010 |
| T012 | `test_mutation_scope_real_python.py` (new), defect fixes only | T011 |

- **Two chains, each serial inside.** The **wrapper chain** T002 → T003 → T004 → T005 → T006 each write `mutmut-mutation.py` (T005/T006
  also share `test_mutmut_verdict.py`, and T003–T005 each add a `READS` row to `test_select_tests_real_loaders.py`), so never two of them
  at once. The **scope chain** T007 → T008 each write `mutation-scope.py`, so never both at once.
- **`[P]` means "beside the other chain", not "beside a sibling in its own".** T007 and T008 write nothing the wrapper chain's T004–T006
  write (T007's and T008's `test_select_tests_real_loaders.py` row, if they declare a module, is the one shared line: the host adds it
  after the merge rather than the two delegates both editing the file, and a delegate that declares a module names the row it needs), and
  they need only T003's functions — their examples run behind `FakeRunner`, so the real wrapper's later behaviour is not read. So **T007
  and T008 may each run beside any of T004, T005, T006**, in a worktree of its own off the commit that holds T003. T003 itself must
  precede T007. The wrapper tasks T004–T006 are not marked `[P]`, because marking them would let two of them be read as parallel with
  each other; they are parallel only with T007 and T008.
- **T009 `[P]` beside T008 only.** Its files (`verify-stamp.py`, `check-imports.py`, `test_mutmut_after_run.py`,
  `test_verify_stamp_lists.py`) are disjoint from T008's (`mutation-scope.py`, `test_mutation_sweeps_python.py`), but it needs T006 (a run
  that completes) and T007 (the dispatch it drives), so it starts in a worktree off a commit holding both; it may not run beside T004–T006
  or T007.
- **The other `[P]`: T010.** Its files (`mutmut.py`, `mutation.py`, the skill, two `docs/` pages, S41's fragment, `test_mutation_words.py`,
  `test_stryker_generated.py`, `test_stryker_migrate.py`) are disjoint from both chains' and from T009's, and it needs only T002
  (`mutmut.py` exists). It may run beside any of T003–T009 in a worktree of its own off T002's commit. It shares `test_mutmut_generated.py`
  and `test_scoped_targets.py` with T002, and the fragment story with T011, which it must not run beside: **T011 never runs beside T010**,
  and T010 never before T002 is committed. It does not share a file with T007 (`test_mutation_placeholders.py` is T007's;
  `test_mutation_words.py` is T010's).
- **May not:** T003 before T002; T004 before T003; T005 before T004 (the setup it follows); T006 before T005; T008 before T007; T009 before
  T006 and T007; T011 before T008, T009 and T010; T012 before T011; two tasks that write `mutation-scope.py` or `mutmut-mutation.py`
  together; T010 beside T011; any `[P]` task before T002 is committed. The host commits by path and resolves no conflict by hand — a
  conflict means a manifest overlap this table says there is none of.
- **Host tasks:** T001 first, alone; T013 alone after T012; T014 … T016 follow in order; Phase 4 after the demo.

## Design review

No screen in this slice

## Convergence

**Pass 1 — not converged** (2026-10-08, cruise iteration 30, judged at `bda2f7a`, range `15bf72b..bda2f7a`; `drive-converge ·
delegated, fresh context`; complete, within budget). Two HIGH findings re-open the loop: T017 (a silenced mutant passes the
verdict) and T018 (the release's entry says Python is unwired). One MEDIUM (T019) and two LOWs (T020, T021) are appended beside
them. Twelve hand mutations were applied and all twelve killed. Each was restored with `git checkout -- <path>`, and at the end
of the pass `git status` showed only the host's `benchmark.json` and this file.

**Per level.**
- *Domain (the wrapper's rules):* the verdict table (`mutmut-mutation.py:57–68`, an unknown code fails through the `.get`
  default at `:460`), the clean slate (`:351`), the names from `.meta` (`:345`, `:385–408`, `__init__.py` keys only) and the setup
  refusals in their order (`:475–478`) all hold under the suites and the hand mutations. **Not proved:** the silencing rule (T017)
  and the reader's `source_paths` subset (T019).
- *Use case (the scope script):* `WIRED`, `PRODUCTION_ROOT`, `REPORTS` and `WRAPPERS` (`mutation-scope.py:246`, `:115`, `:295`,
  `:185–186`), Python sweep causes (`python_moved`, `:144–148`), refusal before the table, `drop_report` and `java-quarkus` still
  refusing: all held by `test_mutation_scope_python` and `test_mutation_sweeps_python`. Each of the four mutations of this file
  and the dispatch was killed.
- *Delivery adapters:* the recipe line (`native_commands.py:104`, `mutmut.py:19`), the table
  (`assets/languages/python/app/pyproject.toml:27–34`), the four locks (`uv.lock:214,225`), the ignore line (`gitignore.py:71`),
  the stamp row (`verify-stamp.py:90`) and `check-imports`' `OUTPUT` (`:81`) are held by `test_mutmut_generated` and
  `test_mutmut_after_run`, and by T013's suites and the `make starters` diff. *Lead checked, no finding:*
  `check-migrations.py`'s Java-only `recorded()` (`:87–108`) does walk a `mutants/` copy. But mutmut copies only `src/`,
  `tests/`, `pyproject.toml` and `uv.lock` (`configuration.py:184–193`), and Python migrations live at
  `apps/<svc>/migrations/`, so the copy holds no migration. The cost is entries read, not a wrong verdict.
- *Screen:* none.
- *Published contract:* the data-model lines are tested verbatim. The fragment's Catch-up meets AC-S42-12 (the `uv.lock`
  conflict, `uv lock --project apps/<service>`, leftover `mutants/`/`.mutmut-cache`, exit 2 until the lock is redone). `migrate`
  is held by `test_mutmut_migrate`. ADR 0010 is `Proposed`. **Not proved:** the release entry as a whole (T018), and the promise
  that silencing fails the run (T017).
- *Words:* the note, the command text, `UNWIRED` (`mutation.py:265`), the skill line (`SKILL.md:95`), and
  `docs/backend-obligations.md:62` and `docs/requirements.md:30` all say Python is wired. Two words in shipped files lag (T021).

**Principles the diff touches.**
- I (owns its files; passes its own gate): the wrapper is written once per project (`languages/python.py:284`, `mutmut.py:26`
  `mutmut_files`) and made executable (`backends.py:102`). `verify`, `verify-checks`, `ci` are unchanged (T013:
  `test_matrix` Python rows green).
- I (version and fragment): `VERSION` `1.6.0.dev0`, unchanged; `changelog.d/mutmut-mutation.md:1` `MINOR` with a standing
  Catch-up. T018 is the unmet half.
- II (retry safety): the clean slate at `mutmut-mutation.py:354`, with T020 as the residual; one run per service through the
  `flock` (`:283–300`).
- III (simplicity): stdlib TOML and JSON only, and one `WRAPPERS` table for TypeScript and Python (`mutation-scope.py:185`).
- V (GWT, fakes): eight new modules, a fake `uv` executable and S08's `FakeRunner`, no `unittest.mock`.
- VI (contract-bounded): `.meta` is read through `exit_code_by_key` only (`:335–342`), the version is checked before generation
  (`:320–327`), and an unknown code fails closed.
- VIII (exact pins): `languages/python.py:51` `mutmut==3.8.0`; a pin or libcst change sweeps (`:198–207`).
- IX (supply chain): `uv sync --locked` and `uv run --no-sync` only (`:314`, `:361`).
- The ADR rule: `delivery/docs/adr/0010-mutmut-for-python-mutation.md`, `Proposed`.

**Question for the host (a product reading, not a task):** mutmut 3.8.0's `mutate_only_covered_lines = true`
(`mutmut/__main__.py:148–152`) stops generating mutants for lines no test reaches. It also stops generating them for every line
coverage excludes (`# pragma: no cover`, `exclude_lines`, `exclude_also`; `pragma_handling.py:35–39`), so those mutants never
reach D212's verdict. That includes covered lines whose mutants would survive.
- (a) Fail the run while the table sets it, as `do_not_mutate_patterns` does. **Recommended:** it is D219's reason, since it
  silences mutants nobody looked at, and it turns D212 item 2's counted *no tests* into nothing.
- (b) Allow it: a table change already sweeps.
- (c) Refuse it at setup with exit 2.

If (a) or (c), it rides with T017's `silenced` check.

**Host's reading (iteration 30):** (a), as D219's standing reason applied, the way plan.md's *Applied, not decided* 2
already applies it to `block` pragmas and `do_not_mutate_patterns`; recorded there as item 5 for the coordinator, who may read it
otherwise. It rides with T017: a `[tool.mutmut]` table that sets `mutate_only_covered_lines = true` fails the run in `plan`, in one
line naming the setting, beside `do_not_mutate_patterns`.

**Pass 2 — converged at the loop's bound, with one MEDIUM and one LOW left open as Phase 4 tasks** (2026-10-08, cruise
iteration 30, judged at `5a9840e`; fixes `81b5a2d..5a9840e`, slice `15bf72b..5a9840e`; `drive-converge · delegated, fresh
context`; complete, within budget). This is the second pass of a loop bounded at two, and it found nothing `CRITICAL`. No
`HIGH` is open. T022 (MEDIUM) and T023 (LOW) are appended under Phase 4 and do not re-open the loop. The bound was reached,
so the slice ships to the demo with them open. Before the pass, the slice's suites were green: `test_mutmut_config
test_mutmut_setup test_mutmut_verdict test_mutmut_silenced test_mutation_scope_python test_mutation_sweeps_python
test_mutation_words test_changelog test_stryker_verdict test_stryker_edges test_mutmut_generated test_mutmut_migrate
test_select_tests_real_loaders test_mutation_scope_typescript` ran 198 tests OK, 1 skipped, in 58 s. Fourteen hand mutations
of the fixes were applied one at a time, and each file was restored with `git checkout -- <path>` before the next.
Thirteen were killed: the `: ` strip, the comma split, the plan check moved after the empty exits, the sweep check dropped,
the `mutate_only_covered_lines` branch dropped, strings read as comments, `.` accepted, a `.py` entry accepted, `matched` on
the raw root, `clean` not checking, `judged` set after the check, and Stryker's incremental and sandbox remains unchecked.
One survived: `clean`'s `or left.is_symlink()` (`mutmut-mutation.py:374`). It matters only for a dangling `mutants`
symlink, since a live one is caught by `exists()`. That is no task: mutmut cannot make its directory over a dangling link,
so no `.meta` is written and no verdict can be read (by reading; not run). No `.codegraph/`, so blast radius comes from
`grep -rn`.

**The five pass-1 tasks, as classes.**
- *T017 (HIGH) — closed.* `pragma_word` (`mutmut-mutation.py:447–454`) is `_parse_pragma_token`
  (`mutmut/mutation/pragma_handling.py:98–110`) line for line, over `tokenize` `COMMENT` tokens only (`:464`). One `silenced`
  (`:483`) serves both paths: `plan` runs it before the *nothing under* and *no mutant to run* exits (`:421–424`), and `sweep`
  runs it before *found nothing* (`:401`). The table test covers each spelling, with holds that have teeth
  (`tests/test_mutmut_silenced.py:44–54`). The over-flag pass 1 named (`#pragma` with no space) is now a hold. One
  over-flag remains, and it is not a finding: a trailing `x = 1  # pragma: no mutate block` silences only its own line in
  mutmut (`visit_SimpleStatementLine`, `:212–217`), yet the wrapper fails it. That matches the published words ("`block`,
  `start` and `end` … fail the run") and fails closed. The rides-along `mutate_only_covered_lines` is checked (`:491`) and
  named in the note, the skill and the fragment's first paragraph, but not in its Catch-up (T023). Its siblings were not
  swept, and `max_stack_depth` passes survivors as *no tests* (T022, reproduced).
- *T018 (HIGH) — closed.* No fragment says TypeScript or Python is unwired. `scoped-mutation.md:3,5` and
  `stryker-mutation.md:3` name `java-quarkus` alone, and the hold in `tests/test_mutation_words.py` reads every
  `changelog.d/*.md`.
- *T019 (MEDIUM) — closed.* One `source_root` (`:119–129`) is shared by `check_paths` (`:132`) and `matched` (`:172`). mutmut
  walks `source_paths or paths_to_mutate` (`configuration.py:144–146`), and the wrapper reads the same fallback (`:161`).
  The `.`, file and raw-root mutations were killed by the config and scope suites.
- *T020 (LOW) — closed in both wrappers.* `clean` refuses with exit 2 (`mutmut-mutation.py:369–376`), as does Stryker's
  `clean` and `judge` (`stryker-mutation.py:469–483`, `:814–817`). **The implementer's lead, judged harmless; no task:**
  `drop_report` (`mutation-scope.py:877–886`) warns and carries on only on the `skip` paths (`:1000–1003`, `:1007–1012`).
  For those, the scope script starts no tool and judges nothing. The gate never reads the leftover: the verdict is the
  service's `skipped` count, and the next run that starts the tool meets its wrapper's `clean`, which now refuses. The line
  it prints names the leftover as "an earlier run's report", so a person reading the skill's report path is told. Making
  it exit 2 would fail a service this run did not touch over a file nothing reads. The same code predates S42 for Go and
  TypeScript, and S42 added only the `python` row (`:874`).
- *T021 (LOW) — closed.* The wrapper's docstring states the exit statuses (`:14–16`). `check-imports.py`'s `deployables`
  docstring names `.stryker-tmp`, `target` and `mutants` (`:151–154`). No `skeleton`, `until T0` or `not wired by this
  script` remains in the files the slice touched under `assets/` or `src/`.

**What the fixes introduced.** Nothing that breaks a verdict. `judge` no longer reads silencing, because `plan` and `sweep`
return 1 before mutmut starts. The run is the same failure, reached earlier, and it is cheaper. The one gap the fixes
opened is in the words: T017's new setting reached three places and missed the Catch-up (T023).

**Per level.**
- *Domain (the wrapper's rules):* the verdict table (`:57–72`), the silencing decision (`:447–503`), the canonical
  `source_paths` (`:119–176`), the clean slate (`:369–376`) and the setup order hold under the suites and the 13 killed
  mutations. **Not proved:** that no other `[tool.mutmut]` key turns a reached survivor into *no tests*. `max_stack_depth`
  does (T022).
- *Use case (the scope script):* unchanged by the fixes apart from the `matched` it loads from the wrapper. The T019
  mutations were killed through `test_mutation_scope_python`. `drop_report`'s warning is judged above.
- *Delivery adapters:* the note (`mutmut.py:55–56`), the skill line (`SKILL.md:95`), `check-imports` (`:151–154`) and
  Stryker's `clean` are held by `test_mutmut_generated`, `test_stryker_verdict` and `test_stryker_edges`. `make starters`
  was not re-run this pass. The fixes touched the note's text and two shipped scripts, and `test_scoped_targets`' hashes
  were updated in `dcbfc1a`.
- *Screen:* none.
- *Published contract:* the fragment's first paragraph matches the code. Its Catch-up lags (T023). The release entry as a
  whole no longer contradicts itself (T018). `VERSION` `1.6.0.dev0` against MINOR fragments is unchanged and agrees
  (`test_changelog` green).

**Principles the diff touches.**
- I (owns its files; passes its own gate; the catch-up note): the wrapper is still written once per project and made
  executable. `changelog.d/mutmut-mutation.md:1` is `MINOR`, and its Catch-up stands at `:5`, with T023 its unmet half.
  `changelog.d/scoped-mutation.md:3,5` now says what the release ships (T018).
- II (retry safety): the clean slate refuses rather than reading leftovers, at `mutmut-mutation.py:373–375` and
  `stryker-mutation.py:479–483`/`:814–817`.
- III (simplicity): the silencing reader is stdlib `tokenize` (`:457–465`), with one `silenced` for both paths and one
  `source_root` for both readers.
- V (GWT, fakes): `tests/test_mutmut_silenced.py` is new and uses the fake `uv` harness, with no `unittest.mock`.
- VI (contract-bounded): the pragma rule is read from the pinned tool's source, checked spelling by spelling against the
  3.8.0 install. An unreadable file fails closed (`:468–480`). T022 is the residual: one tool setting the contract does not
  yet bound.
- VIII (exact pins): `mutmut==3.8.0` is unchanged. The reader names its version in `pragma_word`'s docstring (`:448`).
- IX (supply chain): unchanged by the fixes.

**Question for the host (a product reading, carried in T022):** does `max_stack_depth` fail the run as
`mutate_only_covered_lines` does? (a) Yes. **Recommended**, as the same reading of D219's reason (plan item 5). (b) No,
because a table change sweeps. But the sweep reads the same `33`s and is green too, so (b) is the silent pass D212 rules
out.

**Tree.** Code touched while proving, each restored with `git checkout -- <path>` before the next:
`assets/languages/python/scripts/mutmut-mutation.py` and `assets/languages/typescript/scripts/stryker-mutation.py`. Scratch
lives outside the repository, at `/tmp/s42/converge2/`. At the end of the pass, `git status` shows only the host's
`benchmark.json` and this file.

**Pass 3 — converged, with one MEDIUM and one LOW appended to Phase 4** (2026-10-08, cruise iteration 30, judged at
`f6f8970`, new work `1e4398f..f6f8970`: T031 `e060dfa`, T032 `ace93f8`, T033 `d61ccb9`, T030 `58e3d72`; `drive-converge ·
delegated, fresh context`; complete, within budget). The coordinator asked for this pass over the answers to D223–D226
only. It adds no product scope. It found no `CRITICAL` and no `HIGH`. T034 (MEDIUM) and T035 (LOW) sit under Phase 4 and do
not re-open the loop. Before judging, `make test TESTS="test_mutmut_services test_mutmut_recipe test_mutmut_lines
test_mutmut_migrate test_mutmut_generated test_scoped_targets test_mutation_targets test_mutation_scope_python
test_changelog"` ran 94 tests OK, 1 skipped, in 35 s. No `.codegraph/` exists here, so blast radius comes from `grep -rn`.
`one_line` is called only from `merged()` (`native_commands.py:203`), and `_PREFIX` matches no other backend's line.

**The four tasks, as classes.**
- *T031 (D223 item 2; AC-S42-4 as amended) — holds.* Each service gets a whole turn in `run_service`
  (`mutmut-mutation.py:576–588`): its checks, its lock released in `finally` (`:584`), its own verdict. `main` (`:590–601`)
  runs every service (`dict.fromkeys` at `:598`), then prints the summary in the scope script's words (`:600`), and exits with
  the first non-zero status in service order. `parse` (`:94`) returns the usage line, exit 2, for `--file` given with more than
  one service. One service prints exactly what it printed before. All of it is pinned in `tests/test_mutmut_services.py`, e1–e9.
  **On the real mutmut 3.8.0** (`/tmp/s42/research/p`, run with this worktree's wrapper as `mutmut-mutation.py apps/web
  apps/service`): `apps/web` (no `pyproject.toml`) refuses first, with `cannot be read`. `apps/service` still runs fully: `992
  mutants: 415 killed, 463 no tests …, 114 survived; failed`, which is R9's 114. The run then prints `mutation: 2 swept; failed:
  apps/web, apps/service` and exits 2, the first non-zero. Wall time was 9.3 s. The run wrote `mutants/` only under `/tmp`.
- *T032 (D223 item 1; AC-S42-11) — holds in every service order.* `one_line` (`mutmut.py:28`) and `factory_recipe`
  (`mutation-scope.py:291,300`) write one line at the first Python line's place. They agree for Python only, Python first
  (`python, go, python`), Python last, Python between Go services (`go, python, go, python` → `[go a, python b d, go c]`),
  TypeScript between Python services, and three Python services (`test_mutmut_recipe` e1–e4). I also checked the Java case by
  hand: `java-quarkus, python, java-spring, python` gives `[placeholder, python b d, pit c]`. The recipe check
  (`mutation-scope.py:1070`) therefore holds for a project with two Python services (e6) and for Quarkus beside Python (e7).
  D223's *would reverse if* did not trigger: services added one at a time with `add-service` render the line byte for byte
  (e5). **AC-S42-11, byte for byte:** every non-Python line is kept as written, and the `test_scoped_targets` hashes moved only
  for the shapes that carry Python: `standard-python`, `model-python-sqlite`, `two-python`, `java-python-web`, `integration`
  and `integration-billing`, through the note text and the merged line. The Go, TypeScript, Spring and Quarkus shapes are
  unchanged. `make starters` was not re-run. **The scoped `make mutation`, when its causes sweep several Python services**,
  calls `Tools.sweep` → `wrapper_sweep` once per service (`mutation-scope.py:998–1001`, `:603–605`). Each call is the
  wrapper's one-service path, a failure goes into `failed` and does not stop the loop, and the closing line counts them. That is
  the same shape the sweep now has. A whole-run `Sweep` hands off to `make mutation-full` and gets the combined line.
- *T033 (D223 item 4, D224 item 1, D225 item 1; AC-S42-12) — holds as written, but the class is too narrow (T034).* The note
  (`mutmut.py:74–76`), the fragment (`:3`, `:5`) and the skill (`SKILL.md:95`) share the two sentences, pinned by
  `SweepWordsTest`. The Catch-up carries D224's sentence word for word against AC-S42-12's clause. The note and the fragment
  carry D225's survivors sentence, the green minimal starter, and "a later release makes the starter's own tests kill them".
  **A mixed project's sweep does not fully match what the note says.** A Quarkus service listed earlier always stops the sweep
  before Python runs, and a failing Spring service stops it the same way. The Python line now also stops any Go or TypeScript
  line after it, including one that used to sit between two Python services. The words name only "Go or TypeScript … earlier"
  (T034, MEDIUM: words only, since D223 decided this behaviour and the sweep fails closed). The Catch-up says the sweep's shape
  twice in a row (T035, LOW).
- *T030 — holds.* The table now lives in `tests/test_mutmut_lines.py:22–`. The guard keeps `tests/test_mutmut_*.py` from reading a
  slice record. `test_t027` in `test_mutmut_generated.py` is gone. `grep -ln "specs/" tests/test_mutmut*.py` finds only that
  module's docstring.
- *D226 — no code, and none was owed.* The six readings stand as built (the pass 2 verdict above).

**What the new work broke among the parts already converged:** nothing. The wrapper's single-service output, the scope script's
per-service sweep and the recipe check still hold under their own suites.

**Per level.**
- *Domain (the wrapper):* one service's turn, the summary, exit-status precedence and the usage refusal are proved by the
  fake-`uv` suite and by one real mutmut run. **Not proved:** a real run with two Python services that both reach mutmut.
  The fake proves each service starts from a fresh `mutants/` under its own lock (e1, e6), and the real run proves a refusal
  does not stop the next service.
- *Use case (the scope script):* `factory_recipe` is equal to the generated recipe in every shape named, and the scoped sweep
  is per service. Nothing in `scope()` changed.
- *Delivery adapter (the generated Makefile):* `merged()` + `one_line` is proved by `test_mutmut_recipe`, `test_mutmut_generated`
  and the hashes. **Not proved:** a fresh `make starters` diff in this pass.
- *Screen:* none.
- *Published contract:* AC-S42-4 (amended) and AC-S42-11 hold, as shown above. AC-S42-12's D224 clause is present. The
  fragment's mixed-project sentence is narrower than the behaviour (T034). `VERSION` `1.6.0.dev0` against `MINOR`
  (`changelog.d/mutmut-mutation.md:1`) is unchanged, and `test_changelog` is green.

**Principles the new work touches.**
- I (passes its own gate; the catch-up note): the generated recipe still matches the factory's own check
  (`mutation-scope.py:1070`). The Catch-up gains D224's migrate-before-`add-service` sentence (`changelog.d/mutmut-mutation.md:5`).
  T034 and T035 are the unmet words.
- II (retry safety): each service is a fresh run under its own lock, and the lock is let go on every exit path
  (`mutmut-mutation.py:584`).
- III (simplicity): one rule in two places that are held equal (`mutmut.py:28`, `mutation-scope.py:291`). No backend other than
  Python is touched.
- V (GWT, fakes): `test_mutmut_services` reuses `test_mutmut_verdict`'s fake `uv` and edits only its answer lookup, with no
  `unittest.mock`.
- VI (contract-bounded): exit-status precedence is the scope script's own fail-at-the-end rule, applied in the wrapper
  (`mutmut-mutation.py:601`).
- VIII and IX: unchanged (no pin or install path moved).

**Question for the host:** none is new. T034 widens wording only, inside D223's decision.

**Tree.** No code was mutated in this pass. The real run wrote only under `/tmp/s42/research/p/apps/service/mutants/` and
`/tmp/s42-converge3-run.log`. A `.venv/` that an aborted `uv run` created in the worktree was removed. At the end of the pass,
`git status` shows only the host's `benchmark.json` and this file.

## Phase 4 — adversary findings (cruise iteration 30; `adversary-log.md`, S42 · 1f2a0b7)

Two fix worktrees with disjoint manifests: **W** (`slice/S42-phase4-w`) owns `assets/languages/python/scripts/mutmut-mutation.py`, `src/slipwai/project/mutmut.py`, `src/slipwai/project/mutation.py`'s Python note, `changelog.d/mutmut-mutation.md` and `tests/test_mutmut_*.py`; **S** (`slice/S42-phase4-s`) owns `assets/toolkit/scripts/mutation-scope.py` and `tests/test_mutation_scope*.py` (+ `tests/mutation_scope_fixture.py`).

- [x] T036 [W] A1 (HIGH): a killed wrapper's `mutmut run` child can no longer write into a later run — the lock is held for as long as any process the run started lives (e.g. the lock's descriptor passed to the child, or the child in its own process group, ended with the wrapper), and a run that finds an earlier run's process still alive refuses (exit 2) — `20b3263`
- [x] T037 [W] A2 (HIGH): after the wrapper's own generation step every scoped key's exit code is null, or the run fails naming the file; the sweep reads only the `.meta` files the generation step wrote for sources under `source_paths` — a committed `*.py.meta` beside a source, or one under `tests/`, is never a verdict — `61b8ad3`
- [x] T038 [W] A3, D227 items 1–3: the test selection held to the generated values (exit 1, one line each), `tests_dir` failed, every `PYTEST_*` variable stripped with a note line; the residual sentence in the Makefile note and the fragment — `6eb9cc4`
- [x] T039 [W] A4 (MEDIUM): the `mutmut` (and `libcst`) the run imports is the venv's — a `mutmut` package found on `PYTHONPATH` ahead of the venv's dist-info exits 2 naming its location — `8b4b6bb`
- [x] T040 [W] A5, D227 item 4: every file `[tool.mutmut]` excludes is named, one line each with its reason; the sweep's last line counts them — `3c63b74`
- [x] T041 [W] A6, D228: the multi-service summary `<s> swept, <r> refused; …`, exit unchanged; the note and the fragment quote it — `a5dfa88`
- [x] T042 [W] A7 (LOW): an absolute or `..` `--file` is refused or made relative to the service before matching; an `also_copy` entry that leaves the service's `mutants/` is refused — `b2b9d65`
- [x] T043 [W] B3 (LOW): `lock_versions` compares each closure entry's version, source and hashes, so a same-version rebuild or a changed source sweeps — `4757201`
- [x] T044 [W] B5 (LOW): the Catch-up names every file a `migrate` of a project with an added Python service can conflict in (`Makefile`, `pyproject.toml`, `uv.lock`, `commands/mutation.md`, `scripts/verify_scoped/rules.json`) and says to take the factory's side of the `mutation-full` hunk — `bfc602a`
- [x] T045 [S] B1 (HIGH): a Python file is production when it sits under one of its service's `[tool.mutmut]` `source_paths` roots, read as the wrapper reads them; an unreadable table sweeps the service; `unlisted()` follows the same rule — `8e5496c`
- [x] T046 [S] B2 (MEDIUM): `rule_of` finds a `mutation-full` (and `mutation`) rule however make spells it — whitespace before the colon, several targets on one line — and a second rule for the target is *not the recipe the factory wrote* — `a6a50d3`
- [x] T047 [S] B4 (LOW): the sweep's first line names each cause once — `699967d`
