# Implementation Plan: S41-stryker-mutation — a TypeScript slice's mutation run is real and proportional to its change

**Branch**: `slice/S41-stryker-mutation` | **Date**: 2026-10-08 | **Spec**: `specs/001-faster-slipwai/spec.md`,
`### S41-stryker-mutation` (AC-S41-1..14), FR-008 as D137 amends it

**Input**: the slice's criteria; D137, D138, D139, D149–D155 (S08's, cited), D212, D213, D215 (this slice's), D214 (S42
follows; mutmut and Python's placeholder are not touched beyond AC-S41-10); research.md R1–R9; ADR 0009 (Proposed).

## Summary

Every generated TypeScript service gets Stryker 10.0.0 with its Vitest runner as exact devDependencies, a checked-in
`stryker.config.json` whose `mutate` list is D213's, and a wrapper, `scripts/stryker-mutation.py`, that installs from
the committed lock, starts Stryker without ever fetching it, and decides the verdict from `mutation.json` by D212's rule.
`make mutation-full` runs the wrapper per service; `make mutation` (S08's `mutation-scope.py`) treats TypeScript as
wired: it intersects the changed files with the config's list in Python before any tool starts, refuses a path
`--mutate` would misread, names a browser-app file as not mutated, and sweeps a service whose config, wrapper or Stryker
versions changed. Twelve committed locks are regenerated; the stamp, the gitignore and the provisional gate-configuration
list learn Stryker's files; the words — the Makefile note, the mutation command, the skill, the obligations page — say
TypeScript is wired. Research R1 proved the pair runs under Vitest 4.1.11 and TypeScript 7.0.2 once Stryker's
tsconfig rewrite is pointed away from TypeScript's (removed) JavaScript API.

## Technical Context

**Language/Version**: Python 3.11+ (the factory, and the wrapper and scope script it writes, stdlib only); the generated
service's Node ≥ 22 (Stryker 10's engine), TypeScript 7.0.2, Vitest 4.1.11

**Primary Dependencies**: new in every generated TypeScript service: `@stryker-mutator/core` 10.0.0 and
`@stryker-mutator/vitest-runner` 10.0.0 (devDependencies, exact) — ADR 0009. Nothing new in the factory itself.

**Storage**: none. The wrapper reads `reports/mutation/mutation.json` the run wrote and nothing persists past it.

**Testing**: `unittest` under the factory's runner. The wrapper is tested in-process (loaded with
`sys.dont_write_bytecode`) and as a subprocess against fakes written in the test tree — a fake `npm` executable on a
temporary `PATH` that records its arguments and writes the report a test hands it; the scope script behind S08's
`FakeRunner` seam. One real Stryker run on a generated starter, gated like `test_mutation_scope_real_go.py`
(`backends_under_test()` names `typescript`, `npm` on `PATH`) and skipped otherwise. No `unittest.mock`.

**Target Platform**: Linux and macOS developer machines; CI unchanged (no gate runs `make mutation`).

**Project Type**: CLI factory (`slipwai`) generating repositories.

**Performance Goals**: a slice that changed one production file mutates that file's mutants only (US2 scenario 6);
the demo measures it against `mutation-full` (AC-S41-14; R8's reference: 3 mutants in 4.4 s against 519 in 41 s).

**Constraints**: owner priority 1 — `verify`, `verify-checks`, `ci` and the CI workflow unchanged; the `mutation` line
unchanged (only `mutation-full`'s TypeScript recipe line changes, which `factory_recipe` mirrors); no Makefile
variable added; `src/` and `tests/` files ≤ 350 lines; anything under `assets/` opens files with `encoding="utf-8"`,
runs as `python3 -B` in probes and leaves no `__pycache__`; path literals a toolkit check loads written as segments.

**Scale/Scope**: one backend (TypeScript), any number of TypeScript services beside any others.

## Constitution Check

| Principle | How this slice meets it | Where |
|---|---|---|
| I — owns its files; passes its own gate | the config and wrapper are the project's from generation; `migrate` brings them, the regenerated `rules.json` and the ignore lines to older projects; `make verify` is untouched and still passes (the matrix's TypeScript rows); the scope script reads the config and never writes it | rules 1, 10 |
| I — `VERSION` and fragment | `changelog.d/stryker-mutation.md`, MINOR, with a **Catch-up.** for the lock conflict and hand-wired Stryker (AC-S41-12); `VERSION` stays `1.6.0.dev0` | rule 10 |
| II — idempotency, retry safety | the wrapper starts every run from a clean slate (report and sandbox removed before; sandbox removed after), `incremental` is off: a second run never reads the first's output (D212 item 7) | rule 3 |
| III — simplicity | one wrapper, as Go's; JSON config read by stdlib (D213); the glob reader implements the subset the factory writes and calls the rest unreadable rather than guessing; no new factory dependency | research R3 |
| V — GWT, one rule per increment | rules 1–11 below, each its own RED-GREEN-REFACTOR, entered through the wrapper's and the scope script's `main` | Rules |
| VI — contract-bounded integration | Stryker's report is read through its published schema (`mutation-testing-report-schema` 1.0); an unknown status fails closed | research R4 |
| VIII — versioning | the new dependency is pinned exactly; a change to the pins sweeps (D215 b); the bump is MINOR | rules 6, 10 |
| IX — supply chain | installed only from the committed lock (`npm ci`), started with `npm exec --no`; `npm audit --audit-level=critical` stays green over the new tree | rules 4, 1; R6 |
| XIII (target) — fast feedback | the point of the slice | quickstart |
| XIV — stop on a decision | the starter's own survivors and the Parking Lot line are handed back below, with options | *Handed back* |
| ADR rule (*Development Workflow*) | a new dependency in every TypeScript project: ADR 0009, `Proposed` | `delivery/docs/adr/0009-stryker-for-typescript-mutation.md` |
| Stubs recorded | Python (until S42) and `java-quarkus` stay placeholders that refuse (AC-S41-10) — unchanged stubs, recorded in S08 | rule 8 |

No violation; nothing in *Complexity Tracking*.

## Rules (the map the tasks are cut from — all `[US2]`, User Story 2 scenario 6)

1. **What a TypeScript service is given** (AC-S41-2, -11, -13 part). `app/package.json` gains the two exact
   devDependencies; `stryker.config.json` is written per service by the factory with D213's list (`src/**/*.ts`,
   `!src/main.ts`, `!src/openapi.ts`, and `!src/adapters/driven/event-store-postgres/**` where Postgres is the store),
   `testRunner` `vitest` with `related: false`, `json`/`html`/`clear-text` reporters, `incremental: false`,
   `cleanTempDir: "always"`, `thresholds.break: null`, `tsconfigFile` pointed away (R1), each with a `_comment` Stryker
   ignores; `scripts/stryker-mutation.py` is written once per project with a TypeScript service and is executable;
   `mutation-full`'s TypeScript line is `python3 scripts/stryker-mutation.py <path>`; `.stryker-tmp/` and
   `reports/mutation/` are ignored; the four TypeScript and eight react-vite `typescript-backend*` locks are regenerated
   by `scripts/regenerate-locks.py` and `--check` passes; `make audit` stays green.
2. **The list the wrapper reads** (D213 items 1–3, AC-S41-3 first clause). `targets(service)` reads the config's
   `mutate`; `matched(patterns, file)` applies them in order as R3; anything outside the subset is `Unreadable` naming
   the pattern; a missing config, a missing or non-list `mutate` is `Unreadable`.
3. **The verdict** (D212, AC-S41-4). From `mutation.json`, for the given files (or all, swept): `Killed`/`Ignored`
   pass, `NoCoverage` counted on the last line, every other status — `Survived`, `Timeout`, `RuntimeError`,
   `CompileError`, `Pending`, unknown — fails, one line per mutant naming service, file:line:column, mutator, status and
   the report path; a scoped run whose files hold no mutant is `no mutant to run — <file>: …` exit 0; a sweep with none
   fails; no readable report fails whatever Stryker exited; Stryker's exit code is printed, never the verdict; report and
   sandbox removed before, sandbox after.
4. **Install and setup** (D215 a, AC-S41-5). Marker missing or older than either manifest → `npm ci` at the project
   root, then the marker touched; no `npm` → exit 2, one line; Stryker core or runner absent from the installed tree →
   exit 2, one line naming the two packages and the versions; Stryker started as `npm exec --no -- stryker run`.
5. **TypeScript is wired in the scope script** (AC-S41-1, -2, -3, -8, D138 items 1 and 5). `WIRED` and
   `PRODUCTION_ROOT` gain TypeScript, `PLACEHOLDERS` loses it; `Tools.plan/run/sweep` hand TypeScript to the wrapper as
   Go's are handed to `go-mutation.py`; `factory_recipe` writes the TypeScript line; a matched file is scoped with
   `--file`; a file the list does not match is named *outside Stryker's configured targets* and Stryker does not start;
   a skipped TypeScript service keeps no earlier report (`drop_report`); two TypeScript services, and Go beside
   TypeScript, run only the changed one and name the other skipped; a changed browser-app file is named *browser app —
   not mutated by this target*, exit 0 (D213 item 4).
6. **What sweeps a TypeScript service** (AC-S41-6, D138 item 3, D215 b). Its `stryker.config.json` changed; the
   wrapper changed (every TypeScript service); the parsed `@stryker-mutator/*` versions differ in its `package.json` or
   in the project's `package-lock.json` (the lock: every TypeScript service); a side that cannot be parsed; a config
   whose list cannot be read; an ignored file under `src/`. Each line names the file.
7. **A path `--mutate` would misread** (D215 d, AC-S41-7). A matched changed file whose path within the service
   contains `,` `*` `?` `{` `[` `!` or ends in `:<digits>` refuses its service in one line, exit 2, no tool started —
   never a sweep, never a narrower or wider scope; the wrapper refuses the same `--file` on its own.
8. **The stamp, the scoped gate and the placeholders** (AC-S41-9, -10). After a passing and a failing TypeScript run
   the stamp's ignored digest and `git status` are unchanged and `verify-scoped` is not broadened: `.stryker-tmp/` and
   `reports/mutation/` are `EXEMPT` rows; a sandbox left behind (with a service-local `node_modules` link, R5) is no
   reach. Python and `java-quarkus` still refuse with their messages, now exemplified by Quarkus; `SINCE` and D117's
   borders hold for TypeScript; `make mutation-full SINCE=<ref>` sweeps TypeScript whole (D150).
9. **The words** (AC-S41-13). A TypeScript note above the target (what runs, the report path, where the verdict is
   decided, the escape for an equivalent mutant, why `related` is off and `tsconfigFile` points away);
   `mutation_command` names the TypeScript report and `UNWIRED` no longer names TypeScript; the mutation-testing skill
   says a generated TypeScript service is already wired (no `.mjs`, no `mutation:diff` script, no threshold);
   `docs/backend-obligations.md`; the provisional gate-configuration list gains `stryker.config.*`; ADR 0009.
10. **Catch-up** (AC-S41-12). `slipwai migrate` on a project made before brings the devDependencies, the config, the
    wrapper, the ignore lines and the regenerated `rules.json`; the fragment says how to settle a `package-lock.json`
    conflict (take the factory's side, then `npm install`) and what to do where Stryker was wired by hand.
11. **One real run** (AC-S41-1, -2, -4 end to end). On a generated TypeScript starter on `slice/S1`: one changed
    file with a test that kills its mutants scopes to it and passes; a weakened test fails naming the survivor; the
    sweep mutates the config's list.

AC-S41-14 is the demo's (quickstart), after the converged verdict.

## Project Structure

### Documentation (this slice)

```text
specs/001-faster-slipwai/slices/S41-stryker-mutation/
├── plan.md  research.md  data-model.md  quickstart.md  tasks.md  benchmark.json
delivery/docs/adr/0009-stryker-for-typescript-mutation.md
```

### Source Code

```text
assets/languages/typescript/scripts/stryker-mutation.py   # new: the wrapper — list, refusal, install, run, verdict
assets/languages/typescript/app/package.json              # the two devDependencies
assets/languages/typescript/locks/*.json (4)               # regenerated
assets/frontends/react-vite/locks/typescript-backend*.json (8)  # regenerated
src/slipwai/project/stryker.py                            # new: the config writer, the script path, the note
src/slipwai/project/languages/typescript.py               # two call sites (service config, the script)
src/slipwai/project/native_commands.py                    # the TypeScript `mutation` line
src/slipwai/project/mutation.py                           # MUTATION_NOTES, NAMED_FILES, UNWIRED, the report line
src/slipwai/project/gitignore.py  src/slipwai/backends.py # the ignore lines; the script's executable bit
assets/toolkit/scripts/mutation-scope.py                  # tables and dispatch only: WIRED, PLACEHOLDERS,
                                                          # PRODUCTION_ROOT, factory_recipe, sweep causes, Tools,
                                                          # drop_report, browser apps, Plan's refusal
assets/toolkit/scripts/verify-stamp.py                    # two EXEMPT rows
assets/toolkit/scripts/provisional.py                     # GATE_CONFIGURATION
assets/toolkit/skills/mutation-testing/SKILL.md  docs/backend-obligations.md  docs/requirements.md
changelog.d/stryker-mutation.md
tests/test_stryker_list.py            # new: rule 2, rule 7's wrapper half, versions (R7)
tests/test_stryker_verdict.py         # new: rules 3 and 4, through a fake npm
tests/test_mutation_scope_typescript.py  # new: rules 5 and 7
tests/test_mutation_sweeps_typescript.py # new: rule 6
tests/test_stryker_generated.py       # new: rules 1, 8 (stamp, reach), 9's generated half, 10
tests/test_mutation_scope_real_typescript.py  # new, heavy: rule 11 (for S43's list)
tests/test_mutation_placeholders.py, tests/test_mutation_words.py, tests/test_mutation.py  # re-pinned (rule 8, 9)
```

**Structure Decision**: the one deployable `slipwai-graph` (kind `tool`, D3); one vocabulary — the factory's generated
toolkit — so one context. Code that lands in generated projects goes under `assets/` and `src/slipwai/project/`
(owner priority 3). Stryker's logic lives in a wrapper of its own under the TypeScript backend's assets,
`assets/languages/typescript/scripts/stryker-mutation.py`, as `assets/languages/go/scripts/go-mutation.py` is Go's;
`mutation-scope.py` gains table rows and dispatch only, and loads the wrapper (never copies it) for the list, the
refusal and the version reader. The factory side's new text and writer go in a new module, `src/slipwai/project/stryker.py`,
because `typescript.py` (336), `native_commands.py` (320) and `mutation.py` (288) are near the 350-line budget. Shared
surfaces stay S06's and S14's: `rules.py`, `scoped_targets.py`, `verify_scoped/*` are read, never edited (R5 shows
`reach.py` needs no change).

**Pin**: this is the factory's own code, held by its own tests — the S08 mutation suites (`tests/test_mutation_*.py`),
`tests/test_matrix.py`, `tests/test_backend_obligations.py`, `tests/test_verify_scoped_*`, the lock checks. No code
here predates the method (`delivery/commands/drive.md` stage 7: code the factory generated needs no pin).

## Handed back (not blocking)

Both are recorded for the host; neither changes a criterion this slice implements or a decision it relies on, and
either answer only adds work. The slice proceeds under the criteria as written.

1. **The default TypeScript starter's `make mutation-full` is red on day one** (research R9: 90 survivors and 1
   timeout across `app.ts`, `events.ts`, `tracing.ts`, `projections*.ts`, `config.ts` and the memory stores, none
   equivalent; the minimal `standard`/`http none`/`memory` starter is green). Under D212 that is the true verdict on
   the starter's tests, and a slice that edits `app.ts` will meet that file's survivors in its scoped run.
   - (a) Ship as the criteria say, and say it: the note and the fragment state that the default starter's sweep
     reports its own weak tests, and a follow-on slice — *the TypeScript starter's own tests kill every mutant* —
     strengthens them across the variants (each a test-only change under `assets/backing-services/typescript/tests/`).
     **Recommended**: it keeps S41 the size D128 wants, the verdict honest (priority 5), and Go's starter shows the
     end state the follow-on reaches.
   - (b) Widen S41 to kill or suppress (`// Stryker disable next-line …: <reason>`) every starter survivor before it
     ships — roughly 90 mutants per variant across the event-store, transport and identity answers; triples the slice.
   - (c) Narrow D213's list to the files that are green today — refused: it hides weak tests (the false green D213's
     *Why* rules out).
2. **D213 item 4's Parking Lot line** ("mutation testing for browser apps, which would need its own runner (Vitest
   Browser Mode) and its own config") is not in `spec.md`; this slice may not edit `spec.md`. The host writes it.

## Open questions

None that block. Recorded residuals: Stryker's default concurrency (cores − 1) multiplied by concurrent Phase 4
worktrees (G19) is unchanged; a `.stryker-tmp` link on Windows needs a junction (G20, Stryker's own
`symlinkJunction`); Renovate raises the core and runner majors as two dashboard items (G21) — a grouping rule is
renovate.py's and not this slice's; a future TypeScript framework backend needs its own row (G22).

## Complexity Tracking

Nothing to justify.
