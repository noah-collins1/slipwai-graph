# Tasks: S41-stryker-mutation — a TypeScript slice's mutation run is real and proportional to its change

**Input**: [plan.md](plan.md) (*Rules* 1–11 are what the tasks cut on; *Source Code*; *Structure Decision*; *Pin*),
[research.md](research.md) (R1–R9), [data-model.md](data-model.md) (*The config*, *`matched`*, *`refused`*, *`versions`*,
*The report*, *The wrapper's lines and status*, *What sweeps a TypeScript service*, *The scope script's new lines* — the
words are fixed there and tested verbatim), [quickstart.md](quickstart.md); acceptance criteria AC-S41-1 … AC-S41-14 in
`specs/001-faster-slipwai/spec.md` under `### S41-stryker-mutation`; decisions D212, D213, D215 (this slice's), D137,
D138, D139, D149–D155 (S08's, cited, not re-decided) in `specs/001-faster-slipwai/decisions.md`; ADR 0009
(`delivery/docs/adr/0009-stryker-for-typescript-mutation.md`, already written, `Proposed`). No `examples.md`: a method slice
with no screen and no event model of its own, so **no white box, no mockup task and no styling task**. The one story is
**US2** (FR-008 as D137 amends it, scenario 6), *a mutation run is priced per change where a tool is wired, and says so
where it is not*.

**Branch**: `slice/S41-stryker-mutation`, worktree `/home/noahc/math/slipwai-graph-S41-stryker-mutation`. One commit per
task. No push, no claim.

**Delegation**: one `drive-implement` delegate takes US2 — T002 … T013 in dependency order — or more than one where the
manifests below are disjoint (*Parallel opportunities*). Each task is one RED-GREEN-REFACTOR cycle and one commit and
opens with **one rule's examples**; a delegate never writes a rule's tests ahead of the previous rule's commit. A task's
*Files* line is its manifest, the only files that delegate may write. Nobody but the host writes `tasks.md`. A delegate
that needs a file outside its manifest — a test elsewhere that pins text it changes — **stops and names the file; the
host adds it.**

**Not tasks:**
- **AC-S41-14** (plan rule list, last line; quickstart) is the demo's (T017): `make mutation` against `make
  mutation-full` on a TypeScript starter, wall time, mutant counts and the machine, measured by the hand after the
  converged verdict. A task for it would be a test that cannot fail.
- **Handed back 1** (the default starter's own 90 survivors and 1 timeout, R9) and **handed back 2** (D213 item 4's
  Parking Lot line, not in `spec.md`) are the host's. Neither changes a criterion or a decision this slice implements; no
  task widens the slice to kill or suppress a starter survivor, and no task edits `spec.md`.
- **Open questions** (concurrency, the Windows junction, Renovate grouping, a future TypeScript framework backend) are
  recorded residuals, not tasks.
- **ADR 0009** exists at `Proposed` (`delivery/docs/adr/`); T011 only holds that the words agree with it and does not
  edit it unless a test shows it disagrees (then the delegate stops and names it).
- No white box: `check-model` has nothing to refuse. *Design review* below says so.

## Constraints that hold for every task

- **MINOR, `VERSION` stays `1.6.0.dev0`.** `changelog.d/` already holds MINOR fragments, so a MINOR fragment leaves the
  number as it is (`tests/test_changelog.py` checks the pair). **`changelog.d/stryker-mutation.md` lands in T002** — the
  first commit that changes a user-visible tree — as a first draft whose first line is `MINOR`, one bold lead sentence and
  one paragraph beginning `**Catch-up.**` that stands alone; T012 completes it. No other task touches it. Shape: `changelog.d/README.md`. A commit that changes `src/slipwai/`
  or `assets/` says `Level MINOR; VERSION already carries it (1.6.0.dev0); inside S41's fragment` and the reason; a commit
  that changes only `tests/` says it reaches no user.
- **Commit messages end `(cruise iteration 29)`**, then the attribution lines the host's reminder gives.
- **Write scope of the whole slice** (every manifest stays inside it): `specs/001-faster-slipwai/slices/S41-stryker-mutation/`,
  the files listed under *Source Code* in `plan.md`, `tests/` (the new modules plan.md names, and the named lines of the
  S08/S06 tests listed in *The sweep at planning*), `changelog.d/stryker-mutation.md`. **Never edited:** the root
  `Makefile`, `delivery/scripts/`, `tools/`, CI files, `.github/`, `spec.md`, `decisions.md`, `story-split.md`,
  `slices/README.md`, `VERSION`, anything under `release/`, S06's `rules.py`, `scoped_targets.py`, `verify-scoped.py`,
  `check-slice-scope.py`, `verify_scoped/*` (read, never written). A delegate that finds one of them needs a change stops
  and names it.
- **Size and width.** Every file under `src/` and `tests/` stays within 350 lines and 120 columns (`make check-structure`).
  Current: `src/slipwai/project/languages/typescript.py` **336** (T002 adds two call sites, net ≤ 6; **new code goes in
  `src/slipwai/project/stryker.py`**, never in `typescript.py`), `native_commands.py` **320** (T002 nets ≤ 4: the
  TypeScript `mutation-full` line, the text from `stryker.py`; nothing else), `mutation.py` **288** (T011 rewrites notes
  and command text and must end ≤ 330 — Stryker's note text lives in `stryker.py`, imported, not written in
  `mutation.py`), `backends.py` **332** (T002 nets ≤ 2), `gitignore.py` 170. A new test file that nears 350 stops and
  names the split; the host adds the manifest line. Assets are not counted by `check-structure`, but
  `stryker-mutation.py` and the additions to `mutation-scope.py` stay readable: small named functions, no class beyond the
  seams that exist.
- **Before every commit** run `make lint typecheck check-structure`. **When `assets/toolkit/` is touched** (T007–T011) also
  `make test TESTS="test_toolkit test_utf8_io test_changelog"`. Do not run `make verify`; the host runs the suites once, in T014.
- **Assets.** Every `read_text`/`open` in a script under `assets/` names `encoding="utf-8"`. A test that loads a toolkit or
  asset script as a module sets `sys.dont_write_bytecode = True` first (the helper in `tests/test_mutation.py` is the
  model, imported or copied, not edited); every probe of anything under `assets/` runs as **`python3 -B`**, so no
  `__pycache__/` is left under `assets/`. No literal `apps/service` or `apps/web` in a new script (`toolkit.spoken_for`
  rewrites those). `mutation-scope.py` **loads** the wrapper by path (never copies it) and writes nothing under the project.
- **Path literals** a toolkit check loads: `tests/test_verify_scoped_table_held.py` reads a path literal in a check as a
  file that check reads. Write such lists as segments (`("scripts", "stryker-mutation.py")`), not as one literal.
- **Tests.** Standard library only; **no mocking framework, `unittest.mock` included.** The wrapper is tested in-process
  and as a subprocess against a **fake `npm` executable written into a temporary directory first on `PATH`**: it records
  its argv and cwd and writes the `mutation.json` a test hands it. The scope script is tested behind S08's `FakeRunner`
  (`tests/mutation_scope_fixture.py`, read, not edited). **Real `git` in temporary repositories** (`git init`, `slice/S1`,
  a `main` ref) — never a stubbed diff. Evidence is a log, a file or an exit status, never a clock. **Every
  `subprocess.run` carries `timeout=`**, and anything that can hang (a fake `npm` that waits, a real Stryker) runs under one.
  A test that runs a generated project's command removes `CI`, `GITHUB_ACTIONS`, `GITLAB_CI` (and, as S08's
  `clean_environment` does, `MAKEFLAGS`, `MFLAGS`, `MAKELEVEL`, `MAKEOVERRIDES`, `MAKEFILES`, `SINCE`) from its environment
  unless the example sets one; **each touched test module is also run once under `CI=true`** and the report says so.
  Projects are generated with **this worktree's `./slipwai`** (`FactoryTestCase.generate` does; a hand run says
  `./slipwai generate …`, never the one on `PATH`). Scratch only under `/tmp/s41/`.
- **A recipe line is never changed before the tests that rebuild it are searched** (*The sweep at planning*): `tests/` was
  searched for helpers that rebuild an old Makefile by regex or pin the `mutation` recipe; the hits are met by the tasks
  named. A delegate who changes a recipe line searches again for the one it changes.
- **`verify`, `verify-checks`, `ci` and the CI workflow stay byte for byte**; the `mutation` line is unchanged, only
  `mutation-full`'s TypeScript recipe line changes, and `factory_recipe` mirrors it in the same commit (T002). No Makefile
  variable, `export` or `define` is added.
- **Real runs are slow and few.** Exactly one real Stryker run of the slice, in T013, gated like
  `tests/test_mutation_scope_real_go.py` (`backends_under_test()` names `typescript`, `npm` on `PATH`) and skipped
  otherwise. Every other example fakes `npm` or the `Runner`.
- **Commit by path** — `git commit -m … -- <the task's files>`, a new file `git add`ed by its exact path first; never
  `git add -A`, never `git commit -a`, never `git checkout --` on work that is not the delegate's own (the sanctioned
  RED/teeth route in `delivery/docs/delegated-agent-safety.md` is the only one).
- **RED is seen** for its stated reason before the production file is touched. A **hold** (an example that passes today)
  is written as a hold, said so in its name or docstring, and **seen to have teeth** before commit: change the production
  file, observe the failure, restore with `git checkout -- <exact path>`. A hold with no teeth is not claimed.
- **GREEN is a class**, not an instance: where a rule says *every service* or *every backend*, the examples run a
  two-service project (two TypeScript services; Go beside TypeScript) and the shapes the rule names.

### The sweep at planning

`tests/` searched for helpers that rebuild or pin a generated Makefile's `mutation` / `mutation-full` recipe, a `.PHONY`
line, a TypeScript placeholder, or a lock against its manifest (`grep -rn "mutation" tests`, `grep -rn "typescript" tests/test_mutation*.py`,
`grep -rln "locks" tests`, `grep -rn "factory_recipe" tests`). **Hits**, each met by the task named:

| Hit | Pins | Met by |
|---|---|---|
| `tests/test_mutation_targets.py:182` (`factory_recipe(services)` equals the generated `mutation-full` recipe, shapes `model-typescript-web` and `go-typescript`) | the script's reconstruction of the recipe equals the generated one | **T002** changes both sides in one commit (`native_commands.py` and `factory_recipe`'s TypeScript branch); no edit to the test expected |
| `tests/test_scoped_targets.py:47` `PRE_SLICE` | sha256 of each shape's Makefile above `# Scoped gate`, TypeScript shapes among them | **T002**, **T011**: hashes only, regenerated by the delegate where a TypeScript shape's text above the section moved (the recipe line, the note) |
| `tests/test_mutation_placeholders.py:27, :77–137, :149, :166, :177` | TypeScript as the placeholder: its message, `refuse`, the file classes, and e6 (`make mutation-full` on a TypeScript project prints the setup message) | e6 and `PLACEHOLDER_MESSAGES["typescript"]` re-pointed at `java-quarkus` in **T002** (the sweep recipe moved); the rest in **T007** (TypeScript leaves `PLACEHOLDERS`); the file-class table keeps TypeScript's row |
| `tests/test_mutation_words_script.py:79`, `tests/test_mutation_dry_run.py:96` | TypeScript in a class of backends the placeholder words apply to | **T007**: TypeScript moves from the placeholder class to the wired one in those lines only |
| `tests/test_mutation_words.py:17–18, :98–101`, `tests/test_mutation.py:112–114` | `PLACEHOLDERS = ("java-quarkus", "typescript", "python")`; TypeScript has no note; `mutation_command(["typescript"])` text | **T011**: named lines only |
| `tests/test_monorepos.py:103, :120–126` | every shape's Makefile contains `mutation:`; Go's recipes contain `python3 scripts/go-mutation.py apps/service` | hold, **T002**: both stay true; no edit expected |
| `tests/test_verify_stamp_pinned.py`, `tests/test_verify_stamp_*.py` | `.PHONY: verify ci` then the exact `verify` rule bytes; `EXEMPT` | hold in **T002**; **T010** adds two `EXEMPT` rows and runs the whole `test_verify_stamp*` set |
| `tests/test_verify_scoped_*`, `tests/test_scoped_adopted.py`, `tests/test_scoped_migrate.py` | `rules.json` from-text equals from-database; a fresh slice branch is not broadened | read-only suites, run in **T002**, **T010**; none is edited |
| `tests/test_backend_obligations.py` | names no `mutation` text, rebuilds no Makefile | **T011**: reads `docs/backend-obligations.md`; the delegate runs it, edits it only if the new sentence breaks a pin |
| `tests/test_changelog.py` | the fragments' highest level against `VERSION` | hold in every commit touching `changelog.d/` |
| lock checks (`scripts/regenerate-locks.py --check`, `tests/test_pruning.py`, `tests/test_language_skeletons.py` read the TypeScript manifest and locks) | each committed lock agrees with its manifest | **T002**: the manifest and all twelve locks move in one commit, or the suite is red between them |

## Format: `[ID] [P?] [Story] Description` — each task is one increment, one commit

`[P]` marks a task whose files are disjoint from every sibling it could run beside; see *Parallel opportunities*.

---

## Phase 1: Implementation stage

Each task starts from the green committed suite.

### T001 — Pin: the baseline before anything moves (host task)

- [x] **Host task; no story; no commit.** Run the pin set once and record that it is green: *(Done: 134 tests OK, 1 skipped; `make starters` kept at `/tmp/cruise29/s41-scratch/starters-before`.)*
  `make test TESTS="test_mutation_targets test_mutation_placeholders test_mutation_words test_mutation_words_script test_mutation_dry_run test_mutation test_monorepos test_scoped_targets test_verify_stamp_pinned test_verify_scoped_rules test_scoped_adopted test_scoped_migrate test_changelog test_backend_obligations"`.
  Confirm `cat VERSION` reads `1.6.0.dev0`, that `delivery/docs/adr/0009-stryker-for-typescript-mutation.md` is `Proposed`,
  and that `npm` and network are reachable (T002 regenerates locks). Then `make starters` and keep `build/` aside
  (untracked) so T014's diff of that tree is the change a user sees (`docs/maintaining.md`): a `package.json` with two
  devDependencies, a `stryker.config.json` per TypeScript service, one new script, ignore lines, a Makefile line, a
  changed command text.

### T002 — [US2] What a TypeScript service is given: the dependencies, the config, the wrapper's path, the ignore lines, the recipe line, the twelve locks (R1 · AC-S41-2 part, AC-S41-11, AC-S41-13 part)

- [x] **Rule 1.** First commit that changes a user-visible tree, so the fragment's first draft lands in it (first line *(Done: 0562a84 (+ c6612c0, 8f66e69: the ignore lines).)*
  `MINOR`; a **Catch-up.** paragraph that stands alone and says only what is true at this commit: a project made before
  gains the two devDependencies, `stryker.config.json`, `scripts/stryker-mutation.py` and the ignore lines after `slipwai
  migrate`; T012 completes it). The wrapper lands here as a **skeleton**: it parses `<service> [--file <path> …]`, and
  every run ends `exit 2` with one line saying Stryker is not wired by this script yet. That is a transient state that can
  only fail, never pass, which is the same refusal `mutation-full` printed before, so `mutation-full` is never wrong in
  between; T003–T006 build it. **The locks are regenerated here, not in a final task:** `npm ci` refuses a lock that
  disagrees with its manifest, and the lock checks read the manifest, so a commit that moves `app/package.json` without the
  twelve locks leaves the suite red (and every generated TypeScript starter uninstallable). Needs network; if it is
  absent the delegate stops and says so.

**RED** (new `tests/test_stryker_generated.py`; `FactoryTestCase.generate`; files read from the project, nothing run
except `make -npq` and the lock check):
- e1 a TypeScript project (default answers) and a project with a TypeScript service beside a Go one: `apps/service/package.json`
  names `@stryker-mutator/core` and `@stryker-mutator/vitest-runner` in `devDependencies`, both exactly `10.0.0`, no `^` or
  `~` *(fails today: neither is there)*.
- e2 `apps/service/stryker.config.json` is JSON and carries data-model's keys: `testRunner` `vitest`, `vitest.related` false
  and `configFile`, `mutate` equal to D213's list (`src/**/*.ts`, `!src/main.ts`, `!src/openapi.ts`, and
  `!src/adapters/driven/event-store-postgres/**` **only** where the service's event store is Postgres — a `memory` store
  project has no such entry), `reporters` `json`/`html`/`clear-text`, `incremental` false, `cleanTempDir` `"always"`,
  `thresholds.break` null, a `tsconfigFile` naming a file that does not exist in the service (R1), and a `_comment` beside
  each of `vitest`, `mutate`, `thresholds`, `tsconfigFile` — text, not a value Stryker reads. A second TypeScript service
  has its own file with its own Postgres decision *(fails today: no file)*.
- e3 `scripts/stryker-mutation.py` exists once per project however many TypeScript services it has, is executable
  (`os.access(…, os.X_OK)`), holds no literal `apps/service` or `apps/web`, a `python3 -B` import leaves no `__pycache__/`,
  and is absent from a Go-only project; in an adopted layout it lands under `<delivery>/scripts/` as `go-mutation.py` does
  *(fails today: no script)*. Run as a subprocess with no arguments or an unknown flag it exits 2 with one line.
- e4 `mutation-full:` in the generated Makefile of a TypeScript project is exactly `python3 scripts/stryker-mutation.py
  apps/service`, and in a two-service project one such line per TypeScript service in service order; `mutation:` is
  byte for byte what it was; `verify`, `verify-checks`, `ci` and the generated workflows are byte for byte the pre-slice
  text for the shapes of `test_verify_stamp_scan.SHAPES` and `test_mutation_targets.SHAPES` *(the first half fails today:
  the placeholder `@echo … exit 2`; the second is a hold, teeth: add `mutation-full` as a prerequisite of `verify-checks`
  and see it fail)*.
- e5 `.gitignore` of a TypeScript project names `.stryker-tmp/` and `reports/mutation/`; a Go-only project does not
  *(fails today)*; `git status --short` of a fresh commit is empty after the two paths are created.
- e6 **hold, the class** (the lock rule, AC-S41-11): for each of the four TypeScript locks and the eight react-vite
  `typescript-backend*` locks, the lock's root `packages[""]`/workspace entry agrees with the manifest the factory writes
  for that combination (use `scripts/regenerate-locks.py --check`'s own comparison through its module, imported with
  bytecode off — do not reimplement it) *(fails the moment `package.json` changes without the locks: that is the RED
  this task goes through before the locks are regenerated; teeth: restore one lock from `git` and see it fail)*.
- e7 `make audit` stays green over the new tree: `npm audit --audit-level=critical` in a generated starter after `npm ci`
  exits 0 — **one** example, gated like T013 (`npm` on `PATH`, network), skipped otherwise, under `timeout=`.

**GREEN** — `src/slipwai/project/stryker.py` (new): `stryker_config(service)` returning the config text (the Postgres
entry by the service's event store), `SCRIPT_PATH`, the skeleton wrapper is read from the asset;
`assets/languages/typescript/scripts/stryker-mutation.py` (new, skeleton); `assets/languages/typescript/app/package.json`
(the two exact devDependencies); `typescript.py` two call sites (write the config per service, write the script once
per project) and nothing else, net ≤ 6; `native_commands.py` the TypeScript `mutation-full` line, taking its text from
`stryker.py`; `backends.py` `BACKEND_EXECUTABLES["typescript"]` gains the script; `gitignore.py` the two lines;
`assets/toolkit/scripts/mutation-scope.py` **`factory_recipe` only**: its TypeScript branch writes the same line (so
`test_mutation_targets.py:182` stays green — the rest of rule 5 is T007); `python3 scripts/regenerate-locks.py` rewrites
the twelve locks and `python3 scripts/regenerate-locks.py --check` passes; `changelog.d/stryker-mutation.md` first draft.

**REFACTOR:** the line `python3 scripts/stryker-mutation.py <path>` is spelled once, in `stryker.py`, and used by
`native_commands.py` and `factory_recipe`'s test-side expectation; the config's comment texts are constants beside the writer.

**Verify:** `make test TESTS="test_stryker_generated test_mutation_targets test_mutation_placeholders test_monorepos test_scoped_targets test_verify_stamp_pinned test_verify_scoped_rules test_scoped_adopted test_scoped_migrate test_pruning test_language_skeletons test_changelog test_toolkit test_utf8_io"`,
then `python3 scripts/regenerate-locks.py --check`, then `make lint typecheck check-structure`; the touched module once under
`CI=true`. Commit by path; level line as above.

**Files:** `src/slipwai/project/stryker.py` (new), `src/slipwai/project/languages/typescript.py`,
`src/slipwai/project/native_commands.py`, `src/slipwai/backends.py`, `src/slipwai/project/gitignore.py`,
`assets/languages/typescript/scripts/stryker-mutation.py` (new, skeleton), `assets/languages/typescript/app/package.json`,
`assets/languages/typescript/locks/*.json` (4), `assets/frontends/react-vite/locks/typescript-backend*.json` (8),
`assets/toolkit/scripts/mutation-scope.py` (`factory_recipe` only), `changelog.d/stryker-mutation.md` (new),
`tests/test_stryker_generated.py` (new), `tests/test_mutation_placeholders.py` (e6 and the TypeScript row of
`PLACEHOLDER_MESSAGES` only), `tests/test_scoped_targets.py` (`PRE_SLICE` hashes only, where a TypeScript shape moved).

### T003 — [US2] The list the wrapper reads: `targets`, `matched`, `versions`, and what a config it cannot read says (R3, R7 · AC-S41-3 first clause, AC-S41-6 half)

- [x] **Rule 2.** Needs T002 (the skeleton). In `stryker-mutation.py`: `targets(service)` reads the service's *(Done: a4a72d1.)*
  `stryker.config.json` and returns `mutate`; `matched(patterns, file)` applies the patterns in order (positive marks, `!`
  unmarks) with data-model's segment rules (R3: a literal segment equal; `*` within a segment, never matching a leading
  `.` unless the pattern segment starts with one; `**` a whole segment of zero or more segments none starting with `.`; a
  leading `./`); anything outside that subset is `Unreadable` naming the pattern. `versions(manifest_text, lock_text)`
  (R7) returns `{"@stryker-mutator/core": "10.0.0", …}` from a manifest's `dependencies` and `devDependencies` or a lock's
  `packages` keys ending `node_modules/@stryker-mutator/<name>`; text that is not a JSON object is `Unreadable`.
  `versions` is the reader T008 compares; it is tested here because it is the wrapper's, not the scope script's.
  `main` reaches the first lines of the data-model table: a `--file` the list does not match is named, a run with no
  `--file` left is `nothing under <service> that was given is a file Stryker would mutate; no mutant to run`, exit 0, and
  an unreadable config is `<service>/stryker.config.json: <why>`, exit 2 — none of them starts `npm`.

**RED** (new `tests/test_stryker_list.py`; wrapper loaded in-process with bytecode off, and run as a subprocess with a
fake `npm` that fails the example if it is ever called):
- e1 the generated list (`src/**/*.ts`, `!src/main.ts`, `!src/openapi.ts`, with and without
  `!src/adapters/driven/event-store-postgres/**`): `src/app.ts`, `src/a/b/c.ts`, `src/health.ts` match; `src/main.ts`,
  `src/openapi.ts`, `src/adapters/driven/event-store-postgres/store.ts` (Postgres list only), `tests/app.test.ts`, `src/a.js`,
  `src/.hidden/x.ts` and `src/.x.ts` do not; a later positive pattern re-marks what an earlier `!` unmarked, in order
  *(fails today: no such function)*.
- e2 each construct outside the subset is `Unreadable` and names the pattern: `?`, `[`, `{`, `(`, `+`, `@`, `\`, a `**`
  inside a segment, `..`, an absolute path, a `:<line>-<line>` range, a non-string entry; a missing config, an empty,
  missing or non-list `mutate`, invalid JSON: `Unreadable` with the data-model words.
- e3 `versions`: a manifest naming both exactly; a manifest naming neither (`{}`); a lock with the two under
  `packages["node_modules/@stryker-mutator/core"]` and a nested `apps/service/node_modules/@stryker-mutator/core`;
  non-JSON, a JSON array and a JSON string raise `Unreadable`.
- e4 `main`: a `--file` the list does not match prints `mutation: not mutated <service>/<file> — outside Stryker's
  configured targets` and, with nothing left, the *nothing under …* line; exit 0; the fake `npm` was never called and
  nothing was created under the service. A matched `--file` reaches the skeleton's exit 2 line (the next task's seam).
  An unreadable config is exit 2 with the one line, no `npm`.
- e5 **hold** (class): the same list read in a service nested one level (`apps/billing`) and with a path argument that has
  a trailing `/` — the same answers.

**GREEN** — `stryker-mutation.py`: `Unreadable`, `targets`, `matched`, `versions`, the argument handling and the first
lines of `main`.

**REFACTOR:** one `segments(pattern)` function used by `matched` and by the readability check, so "readable" and
"matches" cannot drift.

**Verify:** `make test TESTS="test_stryker_list test_stryker_generated test_toolkit test_utf8_io"`, then
`make lint typecheck check-structure`. Commit by path; level line as above.

**Files:** `assets/languages/typescript/scripts/stryker-mutation.py`, `tests/test_stryker_list.py` (new).

### T004 — [US2] The verdict is the report's, by D212's rule, and every run starts clean (R4 · AC-S41-4)

- [x] **Rule 3.** Needs T003. The wrapper deletes `<service>/reports/mutation` and `<service>/.stryker-tmp` before the *(Done: 8d94248.)*
  run, starts Stryker as `npm exec --no -- stryker run` from the service directory (scoped: `--mutate <files>`, never
  incremental), prints Stryker's exit code and never uses it as the verdict, reads
  `reports/mutation/mutation.json`, and decides: `Killed`/`Ignored` pass; `NoCoverage` is counted on the last line; every
  other status — `Survived`, `Timeout`, `RuntimeError`, `CompileError`, `Pending`, an unknown string — fails, one line per
  mutant naming service, `file:line:column`, mutator, status and the report path; a scoped run whose files hold no mutant
  is `no mutant to run — <files>: …`, exit 0; a sweep with none fails; no readable report fails whatever Stryker exited;
  the sandbox is removed after. The test fixture (a fake `npm` that makes the installed tree and a fresh install marker
  exist, so this task does not depend on T005's behaviour) lives in `tests/test_stryker_verdict.py`.

**RED** (new `tests/test_stryker_verdict.py`; the fake `npm` records argv/cwd and writes the report each example hands
it; services generated by hand-written fixtures, not by the factory — the factory's config is T002's):
- e1 a scoped run with every mutant `Killed`: argv is `exec --no -- stryker run --mutate <file>` (and the incremental flag
  is never present), cwd the service; first line `scoped to 1 given file(s): <file>`; last line `<n> mutants: <k> killed,
  0 ignored, 0 not covered (reported, never failed); passed — report <path>`; exit 0 *(fails today: the skeleton exits 2)*.
- e2 the class over statuses (a table test): `Survived`, `Timeout`, `RuntimeError`, `CompileError`, `Pending` and a made-up
  `Bogus` each fail the run, exit 1, with a line `<status> <service>/<file>:<line>:<column> <mutator> → <replacement>
  (report <path>)`; `Killed` and `Ignored` pass; `NoCoverage` passes and is counted — `n not covered` appears and the
  words `reported, never failed` stay; two failing mutants give two lines and the last line counts both statuses.
- e3 Stryker's exit code is printed and never decides: a fake that exits 0 with a `Survived` report fails (exit 1); one
  that exits 1 with an all-`Killed` report passes; one that exits 0/1/2 with no report, or an unparseable or
  schema-less one, fails with `Stryker exited <code> and left no readable report at <path>; that is not a pass`.
- e4 zero mutants: scoped (`files` empty or the named file absent from the report) is `no mutant to run — <file>: Stryker
  found no mutant in them (types or comments only)`, exit 0; a sweep with none is `Stryker found nothing to mutate in
  <service>; a pass on nothing is not a pass`, exit 1.
- e5 scoped means scoped: a report holding mutants in a file that was **not** given (the whole-list report a sweep
  would write) does not fail a scoped run for the other file's survivor, and a sweep judges every file in the report.
- e6 clean slate: a `mutation.json` and an `.stryker-tmp/sandbox-x/` from an earlier run are gone before the fake runs
  (the fake asserts it) and `.stryker-tmp` is gone after; a previous green report cannot make a run that writes none
  pass *(teeth: skip the delete and see e3's no-report example pass wrongly)*.
- e7 **hold** with teeth: the argv never contains `incremental` and never `thresholds`; no file under the service other
  than `reports/mutation` and `.stryker-tmp` is written (hash of the service tree before/after).

**GREEN** — `stryker-mutation.py`: `run_stryker`, `read_report`, `judge`, the printer; one place spells a `mutation: ` line.

**REFACTOR:** the status table is one dict (`PASS`, `COUNTED`, everything else fails by default), so an unknown status
fails closed by construction rather than by a branch.

**Verify:** `make test TESTS="test_stryker_verdict test_stryker_list test_stryker_generated"`, then
`make lint typecheck check-structure`; the touched module once under `CI=true`. Commit by path; level line as above.

**Files:** `assets/languages/typescript/scripts/stryker-mutation.py`, `tests/test_stryker_verdict.py` (new).

### T005 — [US2] Install from the committed lock, never fetch; a missing tool is a setup line (R6 · AC-S41-5)

- [x] **Rule 4.** Needs T004 (the run it guards). Install marker (`node_modules/.package-lock.json` at the project root) *(Done: 131eee0.)*
  missing or older than the service's or the root's `package.json`/`package-lock.json` → `npm ci` at the project root,
  then the marker touched; one line `installing from the committed lock (npm ci)`. No `npm` on `PATH` → exit 2, one line.
  `@stryker-mutator/core` or `@stryker-mutator/vitest-runner` absent from the installed tree (looked for from the service
  up to the project root) → exit 2, one line naming the two packages and the versions. Stryker is only ever started as
  `npm exec --no -- stryker run` — `--no` makes npm refuse rather than download.

**RED** (in `tests/test_stryker_verdict.py`; the fake `npm` logs every call):
- e1 a fresh clone (no `node_modules`): the first call is `ci` with cwd the project root, the marker exists after it,
  then `exec --no -- stryker run` follows; `installing from the committed lock (npm ci)` is printed once *(fails today:
  no install step)*.
- e2 a fresh marker (newer than both manifests): `ci` is not called; a manifest touched after the marker: it is called
  again; the root `package-lock.json` newer than the marker: called.
- e3 `npm ci` failing (fake exits 1): the run exits 2 with one setup line and Stryker is never started.
- e4 no `npm` on `PATH` (an empty temporary `PATH`): exit 2, `npm is not on PATH; install Node <.nvmrc> to run Stryker`,
  nothing created.
- e5 Stryker missing after install (the fake's install leaves the tree without the runner, then without core): exit 2, one
  line `Stryker is not installed in this project: add @stryker-mutator/core and @stryker-mutator/vitest-runner <ver> to
  <service>/package.json's devDependencies and run npm install`, `exec` never called.
- e6 **hold, with teeth** (nothing is fetched): in every example the recorded argv of `exec` contains `--no`; no call is
  `npx`, `npm install` or `npm exec` without `--no` *(teeth: drop `--no` and see it fail)*.
- e7 both targets use it: the same install happens for a swept run and a scoped run (class over `--file` present/absent).

**GREEN** — `stryker-mutation.py`: `ensure_installed`, `stryker_present`, the exit-2 setup lines, called before the run.

**REFACTOR:** the marker rule is the one function the `Makefile`'s install rule and the family verify script already
share in words (R6); its docstring says so, so a change to one reads the other.

**Verify:** `make test TESTS="test_stryker_verdict test_stryker_list test_stryker_generated"`, then
`make lint typecheck check-structure`; under `CI=true` once. Commit by path; level line as above.

**Files:** `assets/languages/typescript/scripts/stryker-mutation.py`, `tests/test_stryker_verdict.py`.

### T006 — [US2] The wrapper refuses a path `--mutate` would misread (D215 d · AC-S41-7, wrapper half)

- [x] **Rule 7, wrapper half.** Needs T005. `refused(file)` returns data-model's words for a path within the service *(Done: 16a5a3e.)*
  containing `,` `*` `?` `{` `[` `!` or ending `:<digits>`; `main` refuses the whole invocation, exit 2, one line, **before
  `npm` is looked for, the config is read for matching, or anything is deleted** — never a narrower or wider scope.

**RED** (in `tests/test_stryker_list.py`; fake `npm` that fails the example if called):
- e1 the class: one example per character — `src/a,b.ts`, `src/a*.ts`, `src/a?.ts`, `src/{a}.ts`, `src/[a].ts`,
  `src/!a.ts` — and the trailing forms `src/a.ts:12`, `src/a.ts:3`: `refused` returns `` `apps/service/src/a,b.ts` holds `,`,
  which Stryker's --mutate reads as pattern syntax; rename it, or run `make mutation-full` `` (the char differs per
  example); `src/a.ts:x`, `src/a.ts:`, `src/a:1.ts` and an ordinary path return `None` *(fails today: no function)*.
- e2 `main` with one refused file among matched ones: exit 2, one line, `npm` never called, no `reports/` or `.stryker-tmp`
  created or deleted (a pre-placed old report is still there), and the matched file is **not** mutated alone — no run.
- e3 the refusal wins over "outside Stryker's targets": a file both unmatched and refused is refused (a misread glob is
  the louder fact), and a refused file among files all unmatched still exits 2.
- e4 **hold** (a path with a space, `$`, a unicode letter or `#`) is not refused and reaches the run *(teeth: refuse
  every non-alphanumeric and see it fail)*.

**GREEN** — `stryker-mutation.py`: `refused`, its call in `main` ahead of everything.

**REFACTOR:** `main` becomes the ordered list of its checks (refusal, list, install, run, verdict), each returning an exit
or nothing, so the order the rules fix is read in one place.

**Verify:** `make test TESTS="test_stryker_list test_stryker_verdict test_stryker_generated"`, then
`make lint typecheck check-structure`. Commit by path; level line as above.

**Files:** `assets/languages/typescript/scripts/stryker-mutation.py`, `tests/test_stryker_list.py`.

### T007 — [P] [US2] TypeScript is wired in the scope script: a changed file mutates alone, an unmatched one starts nothing, the other service starts no Stryker (R5 · AC-S41-1, -2, -3, -8, D138 items 1 and 5, D213 item 4)

- [x] **Rule 5.** Needs T003 (`targets`/`matched` loaded by path); does **not** need T004–T006 (every example runs behind *(Done: b5045e1.)*
  `FakeRunner`; the real wrapper is T013's), so it may run beside them. In `mutation-scope.py`, tables and dispatch only:
  `WIRED` and `PRODUCTION_ROOT` gain TypeScript (`src/`), `PLACEHOLDERS` loses it; `Tools.plan/run/sweep` hand TypeScript
  to the wrapper as Go's are handed to `go-mutation.py` (`python3 scripts/stryker-mutation.py <path> --file <within>` per
  file, paths relative to the service); the wrapper is **loaded** for the list, never copied; a matched file is scoped
  with `--file`; a file the list does not match is named *outside Stryker's configured targets* and the runner is not
  called; `drop_report` removes a skipped TypeScript service's earlier `reports/mutation`; two TypeScript services, and Go
  beside TypeScript, run only the changed one and name the other skipped; a changed file under a `kind: web` deployable
  of `project.json` is `not mutated <path> — browser app, not mutated by this target`, exit 0, alongside S08's `packages/`
  line. (`factory_recipe` was done in T002.)

**RED** (new `tests/test_mutation_scope_typescript.py`; `FakeRunner`; real git; services declared as
`typescript:apps/service typescript:apps/second` / `go:apps/service typescript:apps/second`):
- e1 `slice/S1`, one changed `apps/service/src/health.ts`: first line `mutation: scoped to 1 changed file(s) since `main` at
  <short>: apps/service/src/health.ts`, `mutation: scope apps/service — src/health.ts`, last line `mutation: 1 scoped, 0
  swept, 0 skipped, 0 refused; passed`; the fake saw `(typescript, apps/service, ["src/health.ts"])` once *(fails today:
  TypeScript is a placeholder and refuses)*.
- e2 two TypeScript services, a change in one: the other is `skip apps/second — no changed production file`, its runner
  not called, and `reports/mutation` it held from an earlier run is gone (`drop_report`); likewise Go + TypeScript with the
  change in the TypeScript side (Gremlins not called, its `gremlins.json` gone) and in the Go side (Stryker not called).
- e3 a changed `src/main.ts` alone, and `src/openapi.ts` alone: `mutation: not mutated apps/service/src/main.ts — outside
  Stryker's configured targets`, `no mutant to run — every changed production file is outside the tools' targets`, exit
  0, the runner **not** called; a matched and an unmatched file together: only the matched one is handed over and the
  other is named.
- e4 a changed `apps/web/src/App.tsx` where `project.json` declares `apps/web` as `kind: web`: `not mutated
  apps/web/src/App.tsx — browser app, not mutated by this target`, exit 0, no service run for it; a Go-only project's
  `packages/` line is unchanged (S08's hold); a path under no declared deployable is whatever S08 made it.
- e5 a config whose `mutate` list cannot be read (`?` in a pattern) is the service's sweep via `Plan.unreadable` — the
  line names `apps/service/stryker.config.json` and the run calls `sweep`, not `run` *(the sweep cause itself is T008;
  here only that the runner is not asked to scope it)*.
- e6 **hold**: `SINCE`, the borders (`ci`, trunk, detached, no base) and an empty change set behave for TypeScript as for
  Go — `make mutation SINCE=HEAD~1` scopes; on `main` the whole run is `mutation-full`; a branch with no change is `no
  production file changed` *(teeth: make the empty set sweep and see it fail)*.
- e7 the S08 tests that used TypeScript as their placeholder example are re-pointed (named lines of
  `test_mutation_placeholders.py` — the `FILES`/`run_mixed`/e3/e4 cases that use `typescript:` — and the TypeScript rows of
  `test_mutation_words_script.py:79`, `test_mutation_dry_run.py:96`) at `java-quarkus` (placeholder) or moved to the wired
  class; every example they held for the placeholder class still holds with Quarkus *(they fail first, for the reason
  that TypeScript is no longer a placeholder)*.

**GREEN** — `mutation-scope.py`: the tables, `Tools`, the TypeScript runner (argv built in one function), `drop_report`,
the browser-app read from `project.json`, the wrapper loader.

**REFACTOR:** the TypeScript runner and Go's share the "intersect with the tool's own list, name what is left" step; no
new `mutation:` line is spelled outside the printer.

**Verify:** `make test TESTS="test_mutation_scope_typescript test_mutation_placeholders test_mutation_words_script test_mutation_dry_run test_mutation_targets test_mutation_scope_go test_mutation_scope_spring test_mutation_change_set test_mutation_borders test_toolkit test_utf8_io test_changelog"`,
then `make lint typecheck check-structure`; the new module once under `CI=true`. Commit by path; level line as above.

**Files:** `assets/toolkit/scripts/mutation-scope.py`, `tests/test_mutation_scope_typescript.py` (new),
`tests/test_mutation_placeholders.py` (named lines), `tests/test_mutation_words_script.py` (line 79 only),
`tests/test_mutation_dry_run.py` (line 96 only).

### T008 — [P] [US2] What sweeps a TypeScript service: its config, the wrapper, the Stryker versions, an ignored file, a list it cannot read (R7 · AC-S41-6, D138 item 3, D215 b)

- [x] **Rule 6.** Needs T007 (same file, serial with it) and T003 (`versions`). `sweep_causes` gains data-model's table: *(Done: d093aa9.)*
  `<service>/stryker.config.json` changed → that service; `scripts/stryker-mutation.py` changed → every TypeScript
  service; the parsed `@stryker-mutator/*` versions differ between base and working tree in the service's `package.json`
  → that service, or in the root `package-lock.json` → every TypeScript service; a side that cannot be parsed counts as
  changed; a config whose list cannot be read → that service (`Plan.unreadable`); an ignored file under `<service>/src/`
  → that service (`unlisted`, via `PRODUCTION_ROOT`). Each line names the file. A swept service runs `sweep`, the
  wrapper without `--file`.

**RED** (new `tests/test_mutation_sweeps_typescript.py`; `FakeRunner` recording scope versus sweep; real git with the
base commit holding the old files):
- e1 `apps/service/stryker.config.json` changed (also added, also deleted): `sweep apps/service — `apps/service/stryker.config.json`
  changed`; a second TypeScript service still scopes to its own file; a Go service is unaffected.
- e2 `scripts/stryker-mutation.py` changed: every TypeScript service sweeps, naming the file; a Go service does not;
  and `scripts/go-mutation.py` changed does not sweep a TypeScript service (S08's hold with TypeScript present).
- e3 the versions: `apps/service/package.json` with `@stryker-mutator/core` `10.0.0` → `10.0.1` sweeps that service only; a
  change to `scripts/` elsewhere, a version of another package, key order or whitespace do **not** (the second half passes
  today, a hold with teeth: compare raw text and see it sweep); an unparseable manifest at the base or in the working tree
  sweeps naming the file; the root `package-lock.json` with a `@stryker-mutator/vitest-runner` entry changed sweeps every
  TypeScript service, an unrelated lock entry does not, an unparseable lock sweeps all.
- e4 a list the scope script cannot evaluate (`mutate: ["src/**/*.{ts,tsx}"]`, a missing `mutate`, invalid JSON) sweeps that
  service naming the config; with the file unchanged since base it still sweeps (the sweep is about the unreadable list, not
  the diff).
- e5 an ignored file under `apps/service/src/` (`.gitignore`d, e.g. a generated `src/gen/x.ts`): `unlisted` sweeps that
  service, named.
- e6 two causes at once (config and a production file in one service): the service sweeps once, naming the config; the
  production file is not additionally scoped. `SINCE` runs sweep on the same triggers (S08's hold, with TypeScript).

**GREEN** — `mutation-scope.py`: the TypeScript rows of `sweep_causes`, `versions` comparison through the loaded wrapper,
the swept TypeScript command.

**REFACTOR:** the TypeScript causes join S08's `is_sweep(path)` table; no second diff is run.

**Verify:** `make test TESTS="test_mutation_sweeps_typescript test_mutation_sweeps test_mutation_scope_typescript test_mutation_change_set test_toolkit test_utf8_io"`,
then `make lint typecheck check-structure`; the new module once under `CI=true`. Commit by path; level line as above.

**Files:** `assets/toolkit/scripts/mutation-scope.py`, `tests/test_mutation_sweeps_typescript.py` (new).

### T009 — [US2] A path `--mutate` would misread refuses its service in one line, no tool started (D215 d · AC-S41-7, scope half)

- [x] **Rule 7, scope half.** Needs T008 (same file) and T006 (`refused` in the wrapper, loaded by path). `Plan.refusal`: *(Done: 3131ea1.)*
  a matched changed file whose path within the service contains `,` `*` `?` `{` `[` `!` or ends `:<digits>` refuses its
  service: `refuse <service> — <the refusal words>`, status 2, counted `refused`, no tool started for it, never a sweep,
  never a narrower or wider scope; the other services still run and the run fails after all have run (S08's failure rule);
  a dry run says *would fail*.

**RED** (in `tests/test_mutation_scope_typescript.py`; `FakeRunner`):
- e1 `apps/service/src/a,b.ts` changed: `mutation: refuse apps/service — `apps/service/src/a,b.ts` holds `,`, which Stryker's
  --mutate reads as pattern syntax; rename it, or run `make mutation-full``, last line `0 scoped, 0 swept, 0 skipped, 1
  refused; failed: apps/service`, exit 2; the fake was not called, and no sweep was run *(fails today: the file is
  scoped as written)*.
- e2 the class over the seven shapes (`,` `*` `?` `{` `[` `!` and `:12`) as a table test, one example each.
- e3 the refused file next to a good one in the same service: the service is refused whole (no scope of the good one alone);
  next to a good file in another service: that one runs, the run exits 2.
- e4 an unmatched refused path (`src/main.ts` renamed `src/main,x.ts` — unlisted by the list) is the refusal, not "outside
  Stryker's targets"; a refused **test** file or a refused path under another backend's service is not this rule's.
- e5 the dry run: `would fail` and the status the real run would give; `drop_report` does not delete the earlier report
  of a refused service *(the run did not happen)* — the earlier report stays and is named as the earlier run's.

**GREEN** — `mutation-scope.py`: `Plan.refusal` filled for TypeScript from the loaded wrapper's `refused`.

**REFACTOR:** the refusal shares the `refused`/`unreadable` branch that already exists for Spring's unreadable pom.

**Verify:** `make test TESTS="test_mutation_scope_typescript test_mutation_sweeps_typescript test_stryker_list test_mutation_change_set test_toolkit test_utf8_io"`,
then `make lint typecheck check-structure`; under `CI=true` once. Commit by path; level line as above.

**Files:** `assets/toolkit/scripts/mutation-scope.py`, `tests/test_mutation_scope_typescript.py`.

### T010 — [US2] The stamp, the scoped gate and the placeholders hold after a TypeScript run (R5, R8 · AC-S41-9, AC-S41-10)

- [x] **Rule 8.** Needs T009 and T002 (the ignore lines). `assets/toolkit/scripts/verify-stamp.py` gains two `EXEMPT` rows — *(Done: 79adf96.)*
  `.stryker-tmp/` and `reports/mutation/` — so a sandbox left behind and a report are neither read as the stamp's input
  nor as a reach. The remaining examples are holds over behaviour T002 and T007 produced; they sit here, after both
  exist, because their first RED is the stamp itself (a rule cut smaller would have an empty GREEN).

**RED** (in `tests/test_stryker_generated.py`; a project generated once per class, `slice/S1`, a baseline recorded; a
fake `npm` on `PATH` writes the report and leaves a sandbox, a second one leaves a failing report):
- e1 after a passing and after a failing `make mutation`, and after `make mutation-full`: `git status --porcelain
  --ignored` differs from before only by `.stryker-tmp/` and `reports/mutation/` (both ignored); `verify-stamp.py`'s
  ignored-files digest is what it was; the stamp reuses; `make verify-scoped` on the branch is not broadened *(fails
  today: the digest includes the two paths — the RED that brings the rows; teeth: remove one row and see it fail)*.
- e2 a sandbox left behind that holds a real `node_modules/` with no link (the workspace layout, R5) and one that holds a
  `node_modules` link pointing back inside the service: `verify-scoped` reads neither as a reach (`reach.py` unchanged);
  pinned for both shapes, with teeth (point the link outside the deployable and see a reach appear).
- e3 Python and `java-quarkus` still exit 2 with their setup messages on `make mutation` (changed file) and `make
  mutation-full`, with Quarkus the example (`tests/test_mutation_placeholders.py` already re-pointed in T007) — **hold,
  teeth: change a placeholder string and see it fail**; a Python service beside a TypeScript one: the TypeScript service
  runs, the Python one is `refuse`, the run exits 2 (AC-S08-6's class).
- e4 **hold** (D117's borders and `SINCE` for TypeScript, D150): `make mutation` in CI markers, on `main`, detached and
  with an empty `SINCE` sweeps (`mutation-full`); `SINCE=<ref>` scopes TypeScript on any checkout; `make mutation-full
  SINCE=<ref>` sweeps TypeScript **whole** — the recipe line carries no `SINCE`, and the fake `npm` sees no `--mutate`.

**GREEN** — `verify-stamp.py`: the two `EXEMPT` rows, nothing else. (If e2 or e4 fail for a real reason the delegate
stops and names it: `reach.py` and `rules.py` are not in this manifest.)

**REFACTOR:** the two rows join the grouped cache/ignore rows beside the `gremlins.json` and `target/` ones, in the same form.

**Verify:** `make test TESTS="test_stryker_generated test_mutation_placeholders $(ls tests | grep -E '^test_verify_stamp' | sed 's/\.py$//' | tr '\n' ' ') test_verify_scoped_rules test_scoped_adopted test_toolkit test_utf8_io"`,
then `make lint typecheck check-structure`; under `CI=true` once (the root `Makefile` runs the stamp files as this
repository's own stamp — say so in the report). Commit by path; level line as above.

**Files:** `assets/toolkit/scripts/verify-stamp.py`, `tests/test_stryker_generated.py`.

### T011 — [P] [US2] The words: the Makefile note, the mutation command, `UNWIRED`, the skill, the obligations page, the gate-configuration list (R9 · AC-S41-13)

- [x] **Rule 9.** Needs T002 (`stryker.py` exists). Disjoint from the wrapper and scope-script tasks, so it may run beside *(Done: 5a92cba.)*
  them. The words describe what T003–T010 build, as the plan and data-model fix them; this task reads none of their code.
  A TypeScript note above the target (what runs, the report path `apps/<service>/reports/mutation/mutation.json`, that
  the verdict is decided in `scripts/stryker-mutation.py`, the escape for an equivalent mutant — a `// Stryker disable
  next-line <mutator>: <reason>` comment named in the commit — and why `related` is off and `tsconfigFile` points away);
  `mutation_command(["typescript"])` names the TypeScript report and the wrapper, `UNWIRED` no longer names TypeScript,
  Python and `java-quarkus` still do; the mutation-testing skill says a generated TypeScript service is already wired (no
  `.mjs`, no `mutation:diff` script, no threshold) and keeps every other sentence; `docs/backend-obligations.md` and
  `docs/requirements.md` say the same; `provisional.py`'s `GATE_CONFIGURATION` learns `stryker.config.*`.

**RED** (new `tests/test_mutation_words.py` is S08's — edit its named lines; new examples in `tests/test_stryker_generated.py`;
`tests/test_mutation.py` amended only at the lines the new words replace, `:112–114`):
- e1 `mutation_notes(["typescript"])` is non-empty and carries the six facts above; `__APP__` never survives and the
  service's own paths substitute; Go's, Spring's, Quarkus's and Python's notes are byte for byte what they were
  *(fails today: TypeScript has no note — the S08 hold at `test_mutation_words.py:98` is inverted for TypeScript only)*.
- e2 `mutation_command(["typescript"])` and a mixed `["go", "typescript"]` say `scripts/stryker-mutation.py`,
  `reports/mutation/mutation.json`, `make mutation SINCE=<review-base>`, and that CI and the trunk sweep (the S08
  sentences stay); `mutation_command(["python"])` and `["java-quarkus"]` still say the target refuses until a tool is
  wired; `UNWIRED` names exactly `python` and `java-quarkus` *(fails today: TypeScript is in `UNWIRED`)*.
- e3 `mutation-testing/SKILL.md`: the sentence saying a TypeScript project must hand-wire Stryker (`.mjs`, `mutation:diff`,
  thresholds) is gone; the replacement says a generated service is already wired and names the config, the wrapper and the
  report; the file equals the old one except for that passage (a hold; teeth: edit another line).
- e4 `docs/backend-obligations.md` and `docs/requirements.md` say TypeScript's mutation tool is Stryker and wired; no
  `docs/` page still says it is a placeholder; the gates page is unchanged. ADR 0009's `Status` is `Proposed` and its
  decision line names `@stryker-mutator/core` and the vitest runner at `10.0.0` (a hold).
- e5 `GATE_CONFIGURATION` fullmatches `stryker.config.json`, `stryker.config.mjs` and `stryker.config.js` and not
  `stryker.config.json.bak` or `mystryker.config.json`; the existing names still match (a hold over the old list).
- e6 the generated half: a TypeScript project's `Makefile` note is the `stryker.py` text; `make help` shows `mutation-full`
  with its description unchanged; `rules.json` from the generated text equals `rules.json` from the make database (S06's
  reader, imported) *(teeth: add a global variable to the note and see it fail)*.

**GREEN** — `stryker.py` (the note text, constants), `mutation.py` (`MUTATION_NOTES`, `NAMED_FILES`, `UNWIRED`, the
report line; ends ≤ 330 lines, shortening a note rather than splitting a file — a delegate that cannot make it fit stops
and names it), `native_commands.py` only if the note is assembled there (net ≤ 2), `assets/toolkit/skills/mutation-testing/SKILL.md`,
`docs/backend-obligations.md`, `docs/requirements.md`, `assets/toolkit/scripts/provisional.py`.

**REFACTOR:** the Stryker report path is spelled once in `stryker.py` and used by the note, the command text and the
quickstart-facing sentence.

**Verify:** `make test TESTS="test_mutation test_mutation_words test_stryker_generated test_backend_obligations test_provisional_gate test_commands test_scoped_ladder test_docs_index test_scoped_targets test_changelog test_toolkit test_utf8_io"`,
then `make lint typecheck check-structure`; the touched modules once under `CI=true`. Commit by path; level line as above.

**Files:** `src/slipwai/project/stryker.py`, `src/slipwai/project/mutation.py`, `src/slipwai/project/native_commands.py`
(only if the note is assembled there), `assets/toolkit/skills/mutation-testing/SKILL.md`, `assets/toolkit/scripts/provisional.py`,
`docs/backend-obligations.md`, `docs/requirements.md`, `tests/test_mutation_words.py` (named lines), `tests/test_mutation.py`
(`:112–114` only), `tests/test_stryker_generated.py` (new examples), `tests/test_scoped_targets.py` (`PRE_SLICE` hashes
only — the note sits above `# Scoped gate`).

### T012 — [US2] A project made before is brought forward, and the fragment says what that asks of it (R10 · AC-S41-12)

- [x] **Rule 10.** Needs T010 and T011 (everything migrate must bring now exists). The fragment's **Catch-up.** *(Done: 90021bc.)*
  paragraph is completed: it stands alone and says how to settle a `package-lock.json` conflict (take the factory's side,
  then `npm install`), what to do where Stryker was wired by hand (remove the hand-wired script and config, keep the
  factory's, or keep yours and accept that the scope script sweeps on its change), that `make mutation-full` now runs
  Stryker, that the default starter's own survivors show in it and are the project's weak tests (plan, *Handed back* 1),
  that Python and `java-quarkus` stay recorded stubs, and that no `project.json` key changes.

**RED** (in `tests/test_stryker_generated.py`; the technique of `tests/test_scoped_migrate.py`, **failing, never skipping,**
where the commit before this slice's first is not in the clone):
- e1 the fragment: first line `MINOR`; a `**Catch-up.**` paragraph naming `package-lock.json`, `npm install`, `stryker`
  hand-wired, `make mutation-full` and the recorded stubs; `tests/test_changelog.py` holds *(fails today: the draft says
  only what T002 could say)*.
- e2 a TypeScript project generated by the commit before this slice's first, after `slipwai migrate`: `apps/service/package.json`
  names the two devDependencies, `stryker.config.json` exists, `scripts/stryker-mutation.py` exists and is executable,
  `.gitignore` names the two paths, `scripts/verify_scoped/rules.json` is regenerated, `mutation-full` is the wrapper's
  line, and `make verify-scoped` on a slice branch of it is not broadened.
- e3 a project made before whose `package.json` was edited by hand (an unrelated dependency added): migrate keeps the
  edit and adds the two (three-way); a config or wrapper the project edited is not overwritten silently (the existing
  `migrate` rule for files the project owns, held with a Stryker file as the example).
- e4 a Go-only project made before gains no Stryker file, and a project with two TypeScript services gets one config per
  service and one wrapper.

**GREEN** — `changelog.d/stryker-mutation.md` completed. If e2–e4 fail for a real reason (the wrapper is not in
`migrate`'s written set, `package.json` merges badly) the fix is the smallest one in a file this manifest names, RED seen
first; where a needed file is not named the delegate stops and names it. If they pass at once they are written as holds and
**seen to have teeth** (remove the wrapper from the written set and see e2 fail, restore) — the fragment is the
guaranteed RED.

**REFACTOR:** none expected; the fragment is edited for the reader who skips to its Catch-up.

**Verify:** `make test TESTS="test_stryker_generated test_scoped_migrate test_changelog test_toolkit test_utf8_io"`, then
`make lint typecheck check-structure`; under `CI=true` once. Commit by path; level line as above.

**Files:** `changelog.d/stryker-mutation.md`, `tests/test_stryker_generated.py`, and, only if e2–e4 prove a gap,
`src/slipwai/project/stryker.py` (named in the report if touched).

### T013 — [US2] One real Stryker run on a generated starter (R11 · AC-S41-1, AC-S41-2, AC-S41-4 end to end)

- [x] **Rule 11.** Needs T012. This is the **heavy** test: it is the one place the fake `npm` of T004–T006 and the *(Done: ffdfb86.)*
  `FakeRunner` of T007–T009 are checked against the real tool, Vitest 4.1.11 and TypeScript 7.0.2 (R1). Its file is named
  `tests/test_mutation_scope_real_typescript.py` and its module docstring says **heavy — S43's list**, as
  `test_mutation_scope_real_go.py` carries its gate. It is gated by `backends_under_test()` naming `typescript` and `npm`
  on `PATH` (and network for `npm ci`), `skipTest` otherwise; every `subprocess.run` carries a `timeout=` (the sweep up to
  600 s). **Honest about its RED:** the example proves behaviour T002–T012 produced, so it may pass at once. The delegate
  runs it first; whatever the real run shows wrong in the wrapper, the config or the dispatch (R1's settings, `related:
  false`, the Vitest config path, the report location) is this task's GREEN, RED seen first. If it passes untouched, it
  is committed as a hold and **seen to have teeth** by the sanctioned route — change the wrapper so `Survived` passes,
  run, see the weakened-test example fail, `git checkout -- <exact path>` — and the report says so.

**RED/hold** (one class, three examples sharing one generated project, `--profile standard --frontend none --http none
--event-store memory` so the minimal starter is green, R9; `slice/S1` cut from its `main`; scratch under `/tmp/s41/`):
- e1 a changed `apps/service/src/health.ts` and a test that kills its mutants: `make mutation` exits 0; the first line names
  the scope and its base, the last line counts it scoped; `apps/service/reports/mutation/mutation.json` names `src/health.ts`
  and no other file; fewer mutants than e3's sweep.
- e2 the same file with the killing test weakened: `make mutation` exits 1 and names the survivor (`Survived
  apps/service/src/health.ts:<line>:<column> … (report …)`); the previous report was replaced.
- e3 `make mutation-full` mutates the config's list (not `main.ts`, `openapi.ts`): exit 0 on the minimal starter, the report
  names every listed file and none excluded.
- e4 afterwards `git status --short` is empty and `make verify-scoped` is not broadened (AC-S41-9, end to end).

**GREEN** — only what the real run proves wrong, in the files below; otherwise none.

**REFACTOR:** none.

**Verify:** `FACTORY_BACKENDS=typescript make test TESTS="test_mutation_scope_real_typescript test_stryker_generated"` (a
hand run says so in the report), then `make lint typecheck check-structure`; the module without `FACTORY_BACKENDS` is
skipped, not failed. Commit by path; level line as above when a `src/` or `assets/` file changed, else "reaches no user".

**Files:** `tests/test_mutation_scope_real_typescript.py` (new), and, only if the real run proves a defect,
`assets/languages/typescript/scripts/stryker-mutation.py`, `src/slipwai/project/stryker.py`,
`assets/toolkit/scripts/mutation-scope.py` (each named in the report if touched).

### Implementation record

`drive-implement · model: sonnet · delegated, fresh context · story/rule`, one delegate, no fan-out (`split=1`). What
differs from the text above, and why:
- **Locks** were regenerated with npm 11.21 (installed in scratch, since removed): the machine's npm 9.2.0 cannot resolve
  Vitest 4's peer set, so `scripts/regenerate-locks.py --check` cannot run here at all (`edgesOut` error, any commit).
  The twelve locks carry the registry's transitive drift since they were last written (default backend lock: 164
  packages added, 25 moved — Vite 8.3.0 → 8.3.3, rolldown 1.2.8 → 1.2.13, …). Evidence of AC-S41-11 instead: `npm ci`
  with npm 9.2 succeeded in all ten generatable combinations (backend lock ×4; react-vite ×6 — the two `users-keycloak`
  locks without Fastify cannot be generated, `--users keycloak` needs `--http fastify`), and `npm audit
  --audit-level=critical` exits 0 in two of them. The `frontend-only*` and `uv*` locks were left untouched (not S41's).
- **Ignore lines:** `apps/*/reports/mutation/` (a pattern with an inner slash is anchored at the root), and the two
  lines now lead the TypeScript block (8f66e69) so `migrate` merges them beside `add-service`'s lines.
- **Test modules** beyond plan.md: `tests/test_stryker_after_run.py` (T010) and `tests/test_stryker_migrate.py` (T012),
  split off `test_stryker_generated.py` for the 350-line budget.
- **Host fixes:** 8f66e69 — S06's `test_the_same_for_two_python_services` migrated a TypeScript project with a Python
  service added, whose `mutation` recipe now conflicts under `migrate` (S41 rewrote the line `add-service` appends
  beside; the fragment's Catch-up says how to settle it, `test_stryker_migrate` e4 holds it); the example now builds the
  two Python services its name says. c524da2 — the wrapper's sweep refused a `mutate` list its own reader cannot
  evaluate, which is exactly when the scope script sweeps (D213 item 3); the sweep now starts Stryker over any list and
  refuses only a missing config.

---

## Phase 2: Host closing tasks

### T014 — Every suite that reads a generated gate, once, before the gates (host task)
- [x] After T013 is committed and the chain T002 … T013 is: `make test TESTS="$(ls tests | grep -E '^test_(verify_stamp|parallel_gate|model_|gate_|verify_scoped|scoped_|mutation|stryker)' | sed 's/\.py$//' | tr '\n' ' ') test_matrix test_commands test_commit_boundaries test_monorepos test_layout test_changelog test_pruning test_language_skeletons test_backend_obligations"`,
  `python3 scripts/regenerate-locks.py --check`, `make starters` and the diff of `build/` against T001's: only the intended generated
  changes; then `make lint typecheck check-structure`. Not `make verify`. *(Done: `make test` on the branch selected every module (`.gitignore` rule changed): 3708 tests; the failures it found — the stamp-inputs scanner (os.access, a mutmut probe), a feature branched on by name (`postgres`), the test-selection declarations and cross-read map, S08's planning fake missing `refusal` — fixed in e7cc480, 1b04314, 0d4066d and each re-run green; test_matrix's one error was a uv copy failure in a Python row (environmental), and `FACTORY_BACKENDS=python make test TESTS=test_matrix` re-ran green; every TypeScript row's `make verify` passed. `regenerate-locks.py --check` cannot run under npm 9.2 (see the implementation record). `make starters` diff: TypeScript gains `stryker.config.json`, `scripts/stryker-mutation.py`, the manifest, lock, Makefile, .gitignore, rules.json and command text; every backend's toolkit copies of mutation-scope.py, verify-stamp.py, provisional.py and the skill; Python's and Quarkus's command text (UNWIRED).)*

### T015 — Converge, passes as needed (host task)
- [x] `drive-converge` over the slice's range; findings append as tasks below. *(Done: pass 1, `drive-converge · model: host (opus) · delegated, fresh context`; converged, see *Convergence*.)*

### T016 — After-converge gaps (host task)
- [x] `drive-gaps` over the slice and the code it produced. *(Done, cruise iteration 29: eleven findings — one HIGH, five MEDIUM, five LOW — and one product question, D219; T026–T031 below, M2 folded into T017.)*

### T017 — The demo, with the measurement (host task; AC-S41-14)
- [x] *(Demo 1, cruise iteration 29: `implementation` — T032–T034; demo 2 `accepted` at `8dee83d`; see `demo-log.md`.)* The hand runs quickstart scenarios 1–6 in a project generated by this worktree's `./slipwai`, and records `make
  mutation` against `make mutation-full` on a TypeScript starter: wall time, mutant counts, `nproc` and CPU model. The
  Phase 1 real run (T013) is evidence for AC-S41-1, -2, -4, not for this. **And what D217 item 1 asks of the demo:** the
  default starter's sweep red, naming a survivor that is not equivalent (`tracing.ts`'s `endpoint === undefined`); the
  minimal starter (`standard`, `http none`, `memory`) green; and D217's *Would reverse if* checked once — one survivor
  confirmed by running Vitest directly with that mutant applied (the test suite stays green under it).

## Phase 3: Findings appended by converge and gaps

(none yet — T015 and T016 append here)

### Converge pass 1 (T015, cruise iteration 29) — no CRITICAL, no HIGH

The suites were green before the pass (`test_stryker_list`, `test_stryker_verdict`, `test_mutation_scope_typescript`,
`test_mutation_sweeps_typescript`, `test_stryker_after_run`, `test_stryker_generated`, `test_stryker_migrate`,
`test_mutation_placeholders`: 90 tests, 1 skipped — the heavy real run). Twenty hand mutations of the wrapper and the scope
script were applied one at a time, those suites run, and each file restored with `git checkout -- <path>`; fifteen were
killed. The survivors and two reproductions are the tasks below.

### T022 — [US2] MEDIUM · Every path Stryker's `--mutate` would read as something other than itself is refused, not only D215's six characters (D215 d's *why*, AC-S41-7; partial)
- [x] **Close the class, not the instance:** the refusal set and the pattern reader each decide what minimatch reads as *(Done: c21a339.)*
  syntax, from two tables (`MISREAD = ",*?{[!"`, `SYNTAX = "?[]{}()+@\\!"` in
  `assets/languages/typescript/scripts/stryker-mutation.py`) that have already drifted. Derive both from one table of
  what minimatch 10 (the version R3 read) treats as syntax inside a path — at least the extglob openers `+(` and `@(`
  and the `\` escape, beside the six D215 lists and the trailing line range — so a path is refused by exactly the rule
  that makes a pattern unreadable. One example per entry of that table, in the wrapper's refusal examples and in the scope
  script's (`RefusalTest`), each asserting the one refusal line, exit 2 and no tool started.
  **RED evidence (reproduced, minimatch 10.2.6 from the scratch install):** `minimatch("src/a+(b).ts", "src/a+(b).ts")`
  is `false` and `minimatch("src/ab.ts", "src/a+(b).ts")` is `true`; the same for `src/a@(b).ts` and `src/a\b.ts`. The
  wrapper's `refused("apps/service", f)` returns `None` and `matched(<D213 list>, f)` returns `True` for all three, so the
  file is handed to `--mutate`; Stryker mutates `src/ab.ts` (or nothing), and `judged(<report keyed src/ab.ts>,
  ["src/a+(b).ts"])` is `[]`, which `verdict` turns into *no mutant to run*, exit 0 — a green over a scope nobody chose,
  the outcome D215 d exists to prevent. **Product edge for the host:** D215 d enumerates six characters; if that list is
  read as exhaustive rather than as an instance of its *why*, this is a question for the owner, not a task.
- **Files:** `assets/languages/typescript/scripts/stryker-mutation.py`, `tests/test_stryker_list.py`,
  `tests/test_mutation_scope_typescript.py`, `changelog.d/stryker-mutation.md` (the list it names).

### T023 — [US2] LOW · A change to any copy of a `@stryker-mutator/*` package in the lock sweeps, not only the copy the reader keeps (D215 b, AC-S41-6; partial)
- [x] `stryker_in(..., "packages")` collapses every lock entry to one version per package name (`setdefault` over paths *(Done: 1d008bc.)*
  sorted by length), so a nested copy (`node_modules/@stryker-mutator/core/node_modules/@stryker-mutator/util`) can move
  without the comparison seeing it. Key the lock's versions by the lock path (every `…node_modules/@stryker-mutator/<name>`
  entry), so any copy moving is a version change; add an example where only the nested copy moves and the service
  sweeps, and one where the hoisted one moves. **RED evidence (reproduced):** `versions(lock_text=L("9.0.0")) ==
  versions(lock_text=L("9.1.0"))` is `True` for a lock with a hoisted `@stryker-mutator/util` 10.0.0 and a nested copy at
  9.0.0 / 9.1.0; and the hand mutation `key=len` → `key=len, reverse=True` (the nested copy wins) **survived** every
  suite, so nothing holds which copy is read.
- **Files:** `assets/languages/typescript/scripts/stryker-mutation.py`, `tests/test_stryker_list.py`,
  `tests/test_mutation_sweeps_typescript.py`.

### T024 — [US2] LOW · The guards the suites do not hold: each removal below left every S41 suite green (plan rules 3, 5, 6; test coverage)
- [x] Sweep the wrapper's and the scope script's TypeScript guards for one whose removal no example notices, and give *(Done: 10423c9; `marker.touch()` kept: it still matters where `npm ci` writes no hidden lockfile.)*
  each its example; the three found here by hand mutation (each applied, the suites run, the file restored):
  - `judged` strips a leading `./` from a given file (`wanted = [name[2:] if …]` → `list(given)`: **survived**). Without
    it `stryker-mutation.py <service> --file ./src/x.ts` — a form `matched` accepts — reads a report keyed `src/x.ts` as
    *no mutant to run*, exit 0. Example: a `./`-prefixed `--file` whose report holds a survivor fails and names it.
  - `stryker_versions_moved` counts a side that is gone as moved (`now is None or …` → `now is not None and …`:
    **survived**). Example: the root `package-lock.json` deleted on the branch sweeps every TypeScript service.
  - `scope` keeps *only tests changed* from swallowing a browser-app change (`not browser` dropped: **survived**).
    Example: a changed test and a changed `apps/web/**` file print *no production file changed* and the browser line.
  (`marker.touch()` removed also survived; it is equivalent where `npm ci` writes the marker itself, so it needs no
  example — say so in a comment or drop the touch.)
- **Files:** `tests/test_stryker_verdict.py`, `tests/test_mutation_sweeps_typescript.py`,
  `tests/test_mutation_scope_typescript.py` (and the wrapper only if the touch is dropped).

### T025 — [US2] LOW · The fragment names every shape that is refused (AC-S41-7, published contract; partial)
- [x] `changelog.d/stryker-mutation.md` lists the refused characters as "a comma, `*`, `?`, `{`, `[` or `!`" and omits *(Done: f111a55.)*
  the trailing `:<digits>` the wrapper also refuses (`TRAILING_LINE`) and D215 d names. Sweep every user-facing place that
  enumerates the refusal (today only the fragment; the Makefile note and `commands/mutation.md` name none) and make it
  say the set the wrapper refuses — after T022, from the same table. Evidence: `grep -n "trailing" changelog.d/stryker-mutation.md`
  finds nothing; `refused("s", "src/a.ts:12")` returns the refusal.
- **Files:** `changelog.d/stryker-mutation.md`.

### After-converge gaps (T016, cruise iteration 29) — one HIGH, five MEDIUM, five LOW

### T026 — [US2] HIGH · A scoped run never passes on a report that does not show the files it was given (D212, AC-S41-1, -3, -4)
- [x] **Close the class:** two ways a scoped run reads *no mutant to run*, exit 0, over files Stryker never tried. *(Done: 00c8383.)*
  (1) Stryker builds every `--mutate` and config pattern from the absolute path (`@stryker-mutator/core` 10.0.0,
  `config/file-matcher.js:13,24`), so a checkout whose directory name holds minimatch syntax (`/tmp/w[1]/`,
  `/tmp/w{a,b}/`, `/tmp/w+(x)/`) matches none of its own files and the report is `files: {}`. (2) A report whose
  `files` names only other files is read as *no mutant to run* — `tests/test_stryker_verdict.py:173-179` pins that as a
  pass. GREEN: the wrapper refuses (exit 2, one line naming the directory) a service whose absolute path holds any
  entry of the one `SYNTAX` table (T022's); a scoped report that names any file outside the given list fails naming
  it; `files: {}` stays the only valid zero, and only for a given file the wrapper's own reader says holds no mutant
  it could plant — otherwise it fails. Rewrite the pinned example. One example per syntax shape in the directory name.
- **Files:** `assets/languages/typescript/scripts/stryker-mutation.py`, `tests/test_stryker_verdict.py`,
  `tests/test_stryker_list.py`.

### T027 — [US2] MEDIUM · Every place D217 names carries its sentences (D217 item 1, AC-S41-13)
- [x] The generated Makefile note (`src/slipwai/project/stryker.py:121-122`) and `changelog.d/stryker-mutation.md` both *(Done: a635a10.)*
  say: the default TypeScript starter's `make mutation-full` fails the day it is generated, because its own starter tests
  leave survivors; a slice that edits one of those files meets that file's survivors in its scoped `make mutation`; the
  minimal starter is green; a fix is planned (the follow-on slice). `tests/test_stryker_generated.py`'s note example
  holds each sentence.
- **Files:** `src/slipwai/project/stryker.py`, `changelog.d/stryker-mutation.md`, `tests/test_stryker_generated.py`.

### T028 — [US2] MEDIUM · Only a per-mutant `next-line` comment excuses a mutant (D219, D212 items 1 and 6)
- [x] `PASS = ("Killed", "Ignored")` passes every `Ignored`, including those Stryker 10 marks for *(Done: a462f93 (and the note/fragment sentence in a635a10; R10).)*
  `mutator.excludedMutations` (`statusReason` "Ignored because of excluded mutation") and block or file-wide
  `// Stryker disable` comments. GREEN: an `Ignored` mutant passes only where the source line above it is a
  `// Stryker disable next-line <mutator>: <reason>` comment naming that mutant's mutator with a non-empty reason (read
  from the source the report names, or from `statusReason` where 10.0.0 distinguishes it — cite which, R-numbered in
  `research.md`); every other `Ignored` fails, naming the mutant and why. Examples: next-line with reason passes;
  next-line without reason, block disable, file-wide disable, `excludedMutations` each fail.
- **Files:** `assets/languages/typescript/scripts/stryker-mutation.py`, `tests/test_stryker_verdict.py`,
  `research.md` (one R entry), `src/slipwai/project/stryker.py` and `changelog.d/stryker-mutation.md` (one sentence
  each saying so).

### T029 — [US2] MEDIUM · Every reachable lock agrees with its manifest by npm's own rule (AC-S41-11)
- [x] `test_stryker_generated.py:170-181` checks only the two `@stryker-mutator` entries. GREEN: one example per *(Done: a99feb2.)*
  committed TypeScript lock a `generate` can reach runs `npm ci --dry-run --offline --ignore-scripts` (skipped, with its
  reason, where `npm` is not on `PATH`) and asserts exit 0; the two react-vite `*-users-keycloak` locks no `generate`
  can reach with `--http none` are named in a comment as unreachable (older than S41). The host runs `make check-locks`
  under npm 11 before Phase 4 and records it here.
- **Files:** a new `tests/test_stryker_locks.py` (declare it for test selection as the other S41 modules do).

### T030 — [US2] MEDIUM · A project that follows the catch-up ends consistent (AC-S41-12)
- [x] The fragment's **Catch-up** omits `apps/<second>/package.json`'s conflict after `add-service` *(Done: 42dd911 — no command regenerates `rules.json` in a project (ADR 0005), so the Catch-up says re-added Makefile edits put the scoped gate on the full gate and own targets go in a file `make verify` does not read (D220).)*
  (`test_stryker_migrate.py:155-157` shows it), says to re-add one's own Makefile edits without saying how to bring
  `rules.json` back in step, and names the two devDependencies only in the paragraph `migrate` does not copy. GREEN: the
  Catch-up stands alone — names each file that conflicts, the two devDependencies with their version, and the command
  that rewrites `rules.json` after a person re-adds Makefile edits — and a test follows it on the add-service project to
  `rules.text_problem(...) is None` and `npm ci --dry-run` passing where `npm` is present.
- **Files:** `changelog.d/stryker-mutation.md`, `tests/test_stryker_migrate.py`.

### T031 — [US2] LOW · The wrapper's setup and output edges (D212 items 5 and 7)
- [x] Sweep, one example each: (L1) a missing `node_modules/.bin/stryker` is exit 2 with the setup line, never 1; *(Done: f3c1259 — L3 covers the wrapper's own `npm ci`; the Makefile's install target runs outside that lock (Phase 4 / adversary).)*
  (L2) a previous report still present after `clean()` is exit 2, never read as this run's; (L3) the wrapper's own
  `npm ci` takes a lock (or waits on the install target's marker) so `make -j test mutation-full` on a fresh clone does not
  run two installs on one `node_modules` — or, if a lock is not stdlib-simple, the Makefile note says not to run them
  together; (L4) every line the wrapper prints survives a cp1252 stdout (ASCII arrow or `errors="replace"`); (L5)
  `check-imports`' pruned names gain `.stryker-tmp`, with an example that a left sandbox adds no entry read.
- **Files:** `assets/languages/typescript/scripts/stryker-mutation.py`, `tests/test_stryker_verdict.py`,
  `assets/toolkit/scripts/check-imports.py`, `tests/test_stryker_after_run.py`.

### Demo 1 (T017, cruise iteration 29) — `implementation`: two tasks, one wording

### T032 — [US2] HIGH · A mutant under which the suite did not run to completion is never reported as a survivor (D212, D217's *Would reverse if*, AC-S41-4)
- [x] Demo 1 replayed all 91 failing mutants of the default starter's sweep by hand: five reported `Survived` *(Done: 3fafdb1 — R11: no Stryker or Vitest setting turns a file-level hook error into a kill; a static `Survived` mutant with `testsCompleted` below the report's test total fails as `Incomplete`, never counted killed; real sweep 85 survived, 5 incomplete, 1 timeout.)*
  (`tracing.ts` 81:5 ×2, 81:44, 91:7 ×2) turn Vitest red when applied directly — `tracing.test.ts`'s `beforeAll`
  throws and its tests are skipped. All five are `static: true` with `testsCompleted: 81` against the dry run's 86
  (`demo/d217c-survivor-by-hand.txt`, `demo/d217c-replay-all-survivors.txt`, `demo/d217c-report-excerpt-tracing.json`).
  **Close the class:** every way a mutant can be reported `Survived` while the suite under it did not complete — a hook
  that throws, a file that fails to import, a static mutant whose run is shorter than the dry run. Research first
  (R-numbered in `research.md`, citing Stryker 10.0.0's vitest runner source or a run): where the skipped tests show
  (report fields, the runner's result), and whether a Stryker or Vitest setting makes the runner report the hook error
  as a failure. GREEN: such a mutant is counted killed only where the evidence shows the suite failed under it, and the
  wrapper never passes on a guess — an undecidable one fails with its own label, not *Survived*. Example from the
  demo's report excerpt; and a replay check that the five become killed and the 85 real survivors stay survivors.
  Then re-check D217's sentences in the note and the fragment (the real survivor on 91:7 is `ConditionalExpression →
  true`, not `!==`), and the survivor count the fragment states.
- **Files:** `assets/languages/typescript/scripts/stryker-mutation.py`, `tests/test_stryker_verdict.py` or a new
  `tests/test_stryker_incomplete.py`, `research.md`, `changelog.d/stryker-mutation.md`, `src/slipwai/project/stryker.py`.

### T033 — [US2] HIGH · A matched file with no construct Stryker 10 mutates is *no mutant to run*, never a failure (AC-S41-3, T026)
- [x] A comment edit to the starter's own `ports/read-models.ts` gives exit 2 — *holds code it could mutate* — because *(Done: 31c877c — R12.)*
  `holds_code` reads `export const FROM_THE_BEGINNING = 0;` as mutable; Stryker 10 has no numeric-literal mutator, so no
  test and no comment can ever make that run green (`demo/q4d-starter-port-with-const.txt`). **Close the class:** derive
  what `holds_code` counts from Stryker 10.0.0's mutator list (cite it) — a statement holds code only where it carries a
  construct some mutator reads; a declaration whose initialiser is a numeric literal (or any other construct no mutator
  reads) is not code for this purpose; anything the scanner cannot classify still fails closed. One example per
  construct class, including the starter's `read-models.ts` verbatim.
- **Files:** `assets/languages/typescript/scripts/stryker-mutation.py`, `tests/test_stryker_report.py` (or a split).

### T034 — [US2] LOW · A browser-only change does not open with *no production file changed*
- [x] On a change to `apps/web/src/App.tsx` alone, the first line says *no production file changed* and the next names *(Done: 075b6be.)*
  the browser app; the first line contradicts the second for the actor. GREEN: the first line counts the browser-app
  files it names (or says *no service production file changed*), in the scope script's one place that words it, with
  the example in `tests/test_mutation_scope_typescript.py`.
- **Files:** `assets/toolkit/scripts/mutation-scope.py`, `tests/test_mutation_scope_typescript.py`.

## Phase 4: After acceptance (host tasks)

### T035 — [US2] LOW · The actor's demo-2 notes on the wrapper's words (Phase 4)
- [x] (1) An `Incomplete` line names the test file whose tests were skipped where the report says, and says the *(Done: 4820543.)*
  remedy: the setup that failed must fail inside a test (a hook inside a `describe`) for the mutant to count as killed.
  (2) *no mutant to run* over a file with an inert declaration says so rather than *(types or comments only)*, and the
  singular/plural agrees with the count. (3) Where a scoped run's tool output is noise before the verdict (Stryker's
  clear-text table of 86 `✘ … (covered 0)` and *Ran NaN tests per mutant* when there are no mutants), the wrapper keeps
  the tool's output out of the way of the verdict line or says the table is Stryker's. One example each.
- **Files:** `assets/languages/typescript/scripts/stryker-mutation.py`, its test modules.

### T018 — The adversary pass (host task)
- [x] *(Done, cruise iteration 29: two seams, fifteen findings — T036–T045.)* `drive-adversary` over the wrapper's and the scope script's reachable boundaries (`make mutation` with hostile paths,
  a `stryker.config.json` with odd patterns, an unreadable `package-lock.json`, a rename plus a config change, `MAKEFLAGS`
  set, a fake `npm` that prints a malformed report).

### Adversary (T018, cruise iteration 29) — fifteen findings, one HIGH; rows A1–A10, B1–B5 under `## S41` in `adversary-log.md`

### T036 — [US2] HIGH · A green never rests on results an earlier run left (A1; D212 item 7, AC-S41-4)
- [x] `incremental: true` in a project's `stryker.config.json` reuses an earlier run's kills, so a gutted test helper *(Done: 494d751.)*
  still passes. **Sweep every way an earlier run's result reaches this one:** the wrapper forces incremental off on the
  command line (or refuses a config that turns it on, one line), removes `reports/stryker-incremental.json` with the
  report, and any other Stryker option that reuses results (`incrementalFile`, a `--force`-less mode) is named and
  closed. Example: the A1 reproduction, gutted helper → red.
- **Files:** the wrapper; its tests.

### T037 — [US2] MEDIUM · The inert reader reads whole statements (A2, A3; AC-S41-3, T026, T033)
- [x] A statement is inert only where all of it is a declaration Stryker 10 plants nothing in — split statements on *(Done: ec9be28.)*
  what TypeScript's grammar ends them with, not on semicolons alone (ASI: a newline before a token that cannot continue
  the statement), so `import …\nif (…)` is two statements. And `declare …` statements, `export {}`, `enum` members
  without initialisers read inert (A3). Anything not classified fails closed. One example per A2 and A3 shape.
- **Files:** the wrapper; `tests/test_stryker_report.py` or a split.

### T038 — [US2] MEDIUM · Two runs in one service never read each other's report (A4; D212 item 7)
- [x] A per-service run lock (or a report tagged with this run's token and checked), so a second run's cleanup cannot *(Done: f09a7ee.)*
  delete the first's report and a crashed scoped run never passes on another run's report. Example: A4's reproduction.
- **Files:** the wrapper; its tests.

### T039 — [US2] LOW · The next-line excuse is read the way Stryker reads it (A5, A6, A8; D219)
- [x] Lines split only at `\n`, `\r\n`, `\r`, U+2028, U+2029 (A5); the excuse also requires the `statusReason` Stryker *(Done: b24c070.)*
  gave to be the comment's reason (A6); the nearest comment above the statement's first line, skipping blank and
  comment-only lines, is the one read (A8). One example each.
- **Files:** the wrapper; `tests/test_stryker_ignored.py`.

### T040 — [US2] MEDIUM · One install at a time, whoever starts it, and a lock that cannot strand a run (A7, B2, A10)
- [x] The install lock records its holder's pid and is broken when that process is gone, is named in the waiting and *(Done: 98a223f (R13; the install target runs `scripts/stryker-mutation.py --install npm ci` where a TypeScript service is present).)*
  the failing line, and lives where every shell finds it (the project, not `TMPDIR`); the Makefile's install target
  takes the same lock, or `mutation`/`mutation-full` reach the install only through it, without the scope script
  reading the recipe as a project's own (G1); the wrapper finds the project root rather than assuming the current
  directory, and a root-relative or absolute `--file` is read as the service-relative path it names. Examples: A7, B2
  and A10's reproductions.
- **Files:** the wrapper; `src/slipwai/project/` where the install target is written; the Makefile note; tests.

### T041 — [US2] LOW · `Incomplete` only where the suite should have run whole (A9; T032)
- [x] Where Stryker did not run the whole suite for a static mutant (`ignoreStatic`), compare `testsCompleted` with its *(Done: 66106f2, 2adbb46.)*
  `coveredBy`, so a real survivor reads *Survived*. Example: A9's reproduction.
- **Files:** the wrapper; `tests/test_stryker_incomplete.py`.

### T042 — [US2] MEDIUM · The config Stryker reads is the config the scope reads (B1; D213)
- [x] The wrapper runs `stryker run stryker.config.json`; a service holding any other file Stryker would read first *(Done: a7b1166 (wrapper), 65b25bf (scope script, provisional.py).)*
  (`stryker.conf.json`, `.js`, `.mjs`, `.cjs`, `stryker.config.js|mjs|cjs`) sweeps or is refused with one line naming it;
  `provisional.py`'s gate-configuration pattern covers those names; the Catch-up tells a hand-wired project.
- **Files:** the wrapper, `assets/toolkit/scripts/mutation-scope.py`, `assets/toolkit/scripts/provisional.py`, the
  fragment, tests.

### T043 — [US2] LOW · A TypeScript file is production or test by the config's list, not by its name (B3)
- [x] A changed file under `src/` that the mutate list matches is scoped as production whatever its name. Example: B3. *(Done: f590223.)*
- **Files:** `assets/toolkit/scripts/mutation-scope.py`, `tests/test_mutation_scope_typescript.py`.

### T044 — [US2] LOW · A move in the instrumenter's dependency closure sweeps (B4; D222)
- [x] The lock comparison covers every entry `@stryker-mutator/instrumenter` resolves, keyed by lock path. Example: a *(Done: cfea409.)*
  move of `@babel/parser` alone sweeps every TypeScript service using that lock.
- **Files:** the wrapper (`versions`) or the scope script, wherever T023's comparison lives; tests.

### T045 — [US2] LOW · The first line says what the run will do (B5)
- [x] A deleted service's first line names the refusal, not a sweep — for every backend row that shares the pattern *(Done: a28eb0b.)*
  (Go's too). Example: B5.
- **Files:** `assets/toolkit/scripts/mutation-scope.py`, its tests.

### T019 — Mutation (host task)
- [x] Per `project.json`'s recorded mutation command for this repository (S08 recorded none: `"mutation": null`); if still *(Done, cruise iteration 29: N/A — `project.json` records no mutation command for this repository (S08: `"mutation": null`); owed to the cruise report.)*
  none, N/A, said in the register row and owed to the cruise report.

### T020 — Both full gates on the final tip (host task)
- [x] `make verify` once, and the delivery gate, with the `build/` diff of T001: only the intended generated changes. *(Done, cruise iteration 29: both full gates green at `a561bbe` (3787 tests, ~63 min the factory, ~63 min the delivery gate), after two red runs fixed by `slice/S41-gate` and `slice/S41-gate2` and one run the host spoiled with `VERIFY_FORCE=1` in the environment.)*

### T021 — Register row and benchmark close (host task)
- [x] Slice register row, `benchmark.json`. *(Done, cruise iteration 29: register row in `slices/README.md`; benchmark closed.)*

---

## Parallel opportunities

By manifest (each task's *Files* line):

| Task | Writes | Needs another task's file |
|---|---|---|
| T002 | `stryker.py` (new), `typescript.py`, `native_commands.py`, `backends.py`, `gitignore.py`, wrapper skeleton (new), `app/package.json`, 12 locks, `mutation-scope.py` (`factory_recipe` only), fragment (new), `test_stryker_generated.py` (new), `test_mutation_placeholders.py` (e6), `test_scoped_targets.py` (hashes) | none |
| T003 | wrapper, `test_stryker_list.py` (new) | T002's skeleton |
| T004 | wrapper, `test_stryker_verdict.py` (new) | T003 |
| T005 | wrapper, `test_stryker_verdict.py` | T004 |
| T006 | wrapper, `test_stryker_list.py` | T005 |
| T007 | `mutation-scope.py`, `test_mutation_scope_typescript.py` (new), `test_mutation_placeholders.py`, `test_mutation_words_script.py`, `test_mutation_dry_run.py` | T003 (`targets`, `matched`) loaded by path; T002 |
| T008 | `mutation-scope.py`, `test_mutation_sweeps_typescript.py` (new) | T007; T003 (`versions`) |
| T009 | `mutation-scope.py`, `test_mutation_scope_typescript.py` | T008; T006 (`refused`) |
| T010 | `verify-stamp.py`, `test_stryker_generated.py` | T009, T007 (the re-pointed placeholder tests), T002 |
| T011 | `stryker.py`, `mutation.py`, `native_commands.py` (maybe), `SKILL.md`, `provisional.py`, two `docs/` pages, `test_mutation_words.py`, `test_mutation.py`, `test_stryker_generated.py`, `test_scoped_targets.py` (hashes) | T002 |
| T012 | fragment, `test_stryker_generated.py`, `stryker.py` (only if a gap is proved) | T010, T011 |
| T013 | `test_mutation_scope_real_typescript.py` (new), defect fixes only | T012 |

- **Two chains, each serial inside.** The **wrapper chain** T002 → T003 → T004 → T005 → T006 each write
  `stryker-mutation.py` (T004/T005 also share `test_stryker_verdict.py`, T003/T006 `test_stryker_list.py`), so never two of
  them at once. The **scope chain** T007 → T008 → T009 each write `mutation-scope.py` (T007/T009 also share
  `test_mutation_scope_typescript.py`), so never two of them at once either.
- **`[P]` means "beside the other chain", not "beside a sibling in its own".** The scope chain's T007 and T008 write nothing
  the wrapper chain's T004–T006 write, and need only T003's functions (T007, T008) — their examples run behind
  `FakeRunner`, so the real wrapper's later behaviour is not read. So **T007 and T008 may each run beside any of T004, T005,
  T006**, in a worktree of its own off the commit that holds T003. **T009 is not `[P]`**: it needs T006's `refused` and T008's
  file, so it runs after both chains reach it. T003 itself must precede T007. The wrapper tasks T004–T006 are not marked
  `[P]`, because marking them would let two of them be read as parallel with each other; they are parallel only with T007 and T008.
- **The other `[P]`: T011.** Its files (`stryker.py`, `mutation.py`, the skill, two `docs/` pages, `provisional.py`,
  `test_mutation_words.py`, `test_mutation.py`) are disjoint from both chains', and it needs only T002 (`stryker.py`
  exists). It may run beside any of T003–T009 in a worktree of its own off T002's commit. It shares `test_stryker_generated.py`
  and `test_scoped_targets.py` with T002, T010 and T012, which it must not run beside: **T010 and T012 never run beside
  T011**.
- **May not:** T010 before T009 (and T007); T012 before T010 and T011; T013 before T012; two tasks that write
  `mutation-scope.py` or `stryker-mutation.py` together; T011 beside T010 or T012; any `[P]` task before T002 is
  committed. The host commits by path and resolves no conflict by hand — a conflict means a manifest overlap this table says
  there is none of.
- **Host tasks:** T001 first, alone; T014 alone after T013; T015 … T021 follow in order.

## Design review

No screen in this slice

## Convergence

**Converged at pass 1 of 2** (2026-10-08, cruise iteration 29, at f111a55 for the code; `drive-converge · model: host (opus)
· delegated, fresh context`). Pass 1 found no CRITICAL and no HIGH, so the loop did not re-open (*commands/drive.md* stage 9:
only those re-open it); its one MEDIUM (T022) and three LOWs (T023–T025) were implemented at once rather than left to
Phase 4, each its own RED-GREEN commit, and the slice's suites re-ran green after them (lint, typecheck, check-structure;
21 modules OK, 2 skipped — the heavy real run and one tool gate). Twenty hand mutations of the wrapper and the scope script
were applied by the pass; fifteen were killed, and the five survivors are now killed by T022–T024's examples or are
equivalent (`marker.touch()`).

**Per level.** *Domain:* D212's verdict (`stryker-mutation.py`, the `PASS`/`COUNTED` table and `verdict`), D213's list and
its intersection (`stryker.py` `mutate_list`, by the trait `integration_feature`; the wrapper's `matched`/`targets`), D215's
install from the lock, never fetching, version sweep (lock keyed by path, T023) and refusal (one `SYNTAX` table, T022).
*Use case:* `make mutation` scoped and swept, one and two TypeScript services, Go beside TypeScript, types-only, excluded,
browser-app and refused files — held by `test_mutation_scope_typescript`, `test_mutation_sweeps_typescript`,
`test_stryker_after_run` and, on the real tool, `test_mutation_scope_real_typescript`. *Delivery adapter:* the
`mutation-full` line (`stryker.py:21`), the wrapper's CLI, `npm ci`/`npm exec --no`, the ignore lines, the stamp's
`EXEMPT` rows, reach unchanged. *Screen:* none. *Published contract:* the generated config and wrapper, the Makefile note,
`commands/mutation.md`, the skill line, `docs/backend-obligations.md`, the fragment's Catch-up, `migrate`
(`test_stryker_migrate`), ADR 0009 `Proposed`.

**Principles the diff touches.** I (owns its files, passes its own gate): `src/slipwai/project/stryker.py` writes the config
and wrapper, `languages/typescript.py:28,332`; every TypeScript row of `test_matrix` passed `make verify`; `verify`,
`verify-checks`, `ci` unchanged. I (version and fragment): `VERSION` `1.6.0.dev0`, `changelog.d/stryker-mutation.md:1`
`MINOR` with its Catch-up. II (retry safety): the wrapper's `clean` and the sandbox removal after the run, `"incremental":
false`. III (simplicity): stdlib JSON reader, no factory dependency. V (GWT, fakes): seven new modules, a fake `npm` and S08's
`FakeRunner`, no mocking library. VI (contract-bounded): the report's statuses read through its schema, unknown fails. VIII
(versions): exact pins in `assets/languages/typescript/app/package.json`, a pin change sweeps. IX (supply chain): `npm ci`
and `npm exec --no`; `npm audit --audit-level=critical` exits 0. ADR rule: `delivery/docs/adr/0009-stryker-for-typescript-mutation.md`, `Proposed`.

**Not run here, by the brief:** the two full gates (the host runs them on the merged tip), the after-converge gaps (T016),
the demo (T017, AC-S41-14). `make check-convergence` and the map: no rung moved (the slice changes generated code, not this
repository's ladders). Handed back in `plan.md`: the default starter's own survivors, and D213's Parking Lot line.
