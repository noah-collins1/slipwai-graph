# Implementation Plan: S08-scoped-mutation — a slice's mutation run is proportional to its change

**Branch**: `slice/S08-scoped-mutation` | **Date**: 2026-10-05 | **Spec**: `specs/001-faster-slipwai/spec.md`,
`### S08-scoped-mutation` (AC-S08-1..19), FR-008 as D137 amends it

**Input**: the slice's criteria; decisions D137, D138, D139 (this slice's), D117, D125, D133 (S06's, cited); ADR 0005.

## Summary

In every generated project `make mutation` becomes one call to a new toolkit script, `scripts/mutation-scope.py`,
handed each service as `<backend>:<path>`. On a `slice/<id>` branch with a usable base it measures what changed
since the merge-base (D117 rule 2, through `check-slice-scope`), or since `SINCE` on any checkout (D138 item 4),
classifies each changed path (data-model), and runs each wired service's tool over only its changed production
files: Gremlins through `go-mutation.py`'s new `--file`, PIT through `-DtargetClasses` (research R1–R3).
Placeholder backends keep refusing with their setup message and say what they would mutate (D137). Every other
checkout — trunk, CI, detached, no base, unreadable — and every whole-run trigger runs `make mutation-full`, which
is today's recipe byte for byte (AC-S08-11). The command text, each backend's note, the skill and the docs are
rewritten to say so, Phase 4 on `main` included (D139).

## Technical Context

**Language/Version**: Python 3.11+ (factory and the generated toolkit script, stdlib only); GNU Make 3.81–4.4

**Primary Dependencies**: none new. Gremlins 0.6.0 (pinned already), pitest-maven 1.25.9 (pinned in the Spring pom)

**Storage**: none — nothing persisted (data-model)

**Testing**: `unittest` under the factory's runner (`make test`, pytest-xdist where present); real `git` in temporary
repositories; the tool runs stand behind a `Runner` seam faked in the test tree — no `unittest.mock`. One real
Go run and one real Spring run, each on one generated starter, gated like `test_matrix.py`'s existing Go mutation test.

**Target Platform**: Linux and macOS developer machines; CI unchanged

**Project Type**: CLI factory (`slipwai`) generating repositories

**Performance Goals**: a slice that changed one production file mutates that file's mutants only (SC/US2 scenario 6);
measured at the demo against `mutation-full` (AC-S08-19)

**Constraints**: owner priority 1 — `verify`, `verify-checks`, `ci` and the CI workflow byte for byte unchanged; ADR
0005/D133 — no new Makefile variable, export or define; `src/`, `tests/` files ≤ 350 lines; scripts under `assets/`
open files with `encoding="utf-8"` and leave no `__pycache__`

**Scale/Scope**: five backends, any number of services; two wired (Go, Spring)

## Constitution Check

| Principle | How this slice meets it | Where |
|---|---|---|
| I — owns its files; scoped gate additive | `mutation-full` is today's recipe; the merge root and CI never run `mutation`; a project's pom and `.gremlins.yaml` are read, never written; `migrate` carries the new Makefile and script | rule 1, 2; research R1, R7 |
| I — `VERSION` and fragment | `changelog.d/scoped-mutation.md`, MINOR, with a standalone **Catch-up.**; `VERSION` already `1.6.0.dev0` | rule 9 |
| III — simplicity | one script, no new dependency, no temp files; a `Runner` seam only where tests need one | research R1, R4 |
| V — GWT, one rule per increment | rules 1–9 below, each its own RED-GREEN-REFACTOR; the use case is `make mutation` in a generated project, entered through the script's `main` with the git repo real and the tool faked; one real end-to-end per wired backend | Rules |
| XIII (target) — fast feedback | the point of the slice: a mutation run priced per change | quickstart |
| XIV — stop on a decision | no new name in a published contract beyond the target D138 already named; open questions handed back | *Open questions* |
| Stubs recorded (*Development Workflow*) | TypeScript, Python and `java-quarkus` stay placeholders that refuse (D137 item 2): recorded here and in the fragment | rule 6 |

No violation; nothing in *Complexity Tracking*.

## Rules (the map the tasks are cut from — all `[US2]`, User Story 2 scenario 6)

1. **The two targets** (AC-S08-11, AC-S08-13). `mutation-full` carries the merged per-service recipe as today,
   appears in `make help` and `.PHONY`; `mutation` is the one script line of data-model *The invocation*. Neither is
   reachable from `verify`, `verify-checks` or `ci`, which are byte for byte unchanged with the CI workflow; the
   generated `rules.json` reads the new Makefile without a difference (S06's from-text/from-database hold covers
   every starter shape), and a fresh project's `verify-scoped` on a slice branch is not broadened by it.
2. **The checkouts that sweep** (AC-S08-1, AC-S08-15). Trunk, a branch not `slice/<id>`, detached `HEAD`, `CI` /
   `GITHUB_ACTIONS` / `GITLAB_CI`, no usable base, an unreadable checkout, `SINCE=` empty: one line `the sweep runs —
   <reason>`, then `mutation-full`, its status the run's. An adopted layout: the no-scope line, then `mutation-full`.
3. **What changed and how it prints** (AC-S08-7, AC-S08-9, AC-S08-10, AC-S08-12). The change set and classification
   of data-model; `SINCE=<ref>` on any checkout, CI included; an unresolvable ref fails naming it; tests-only,
   non-source-only, deletions-only, `packages/`, a rename's new path; first line, per-service lines, last line.
4. **Go, scoped** (AC-S08-2). `go-mutation.py --file`; a two-service Go project with one changed production file
   mutates only that file and names the other service skipped without starting Gremlins; a `.gremlins.yaml`
   exclusion is named, not mutated.
5. **Spring, scoped** (AC-S08-3, AC-S08-4). `Foo` and `Foo$*` within `targetClasses`, never `Foo*`; outside it, or in
   `excludedClasses`, named and Maven not invoked, exit 0; PIT's *No mutations found* on a scoped run is the
   no-mutant line, exit 0; the pom's excludes, `targetTests` and `*IT` hold (a real run on the Spring starter holds
   the `-DtargetClasses` override against the pin).
6. **Placeholders and mixed projects** (AC-S08-5, AC-S08-6). TypeScript, Python, `java-quarkus` with a changed
   production file refuse, exit 2, with the setup message, the *scope will apply* clause and the files; untouched,
   skipped; a placeholder earlier in service order no longer stops a wired service; status per data-model.
7. **What sweeps** (AC-S08-8). `.gremlins.yaml`; the `pitest-maven` block as parsed structure (a comment or another
   plugin's change does not sweep; an unparseable side does); `go-mutation.py` → every Go service; the scope script or
   the `mutation` rule's text → the whole run; each names its file.
8. **The stamp is untouched** (AC-S08-14). After a scoped and a full run, `git status --ignored` and the stamp's
   ignored digest are what they were, so the stamp reuses and `verify-scoped` is not broadened.
9. **The words** (AC-S08-16, AC-S08-17, AC-S08-18). `mutation_command()` for every backend: bare target scopes on a
   slice branch, `SINCE=<ref>` anywhere, `mutation-full` is the sweep, CI and the trunk sweep, Phase 4 on `main` runs
   `make mutation SINCE=<the commit before the merge>`; each backend's note in `mutation.py` (Go's *Without SINCE it
   mutates the whole module* rewritten; Spring's `failWhenNoMutations` paragraph says the scoped exception);
   `mutation-testing/SKILL.md`'s clean-tree sentence replaced (D138 item 2); `docs/backend-obligations.md` and the
   fragment; `migrate` carries the script and Makefile (a test on an older project).

AC-S08-19 is the demo's (quickstart), after the converged verdict.

## Project Structure

### Documentation (this slice)

```text
specs/001-faster-slipwai/slices/S08-scoped-mutation/
├── plan.md  research.md  data-model.md  quickstart.md  tasks.md  benchmark.json
```

### Source Code

```text
assets/toolkit/scripts/mutation-scope.py      # new: the scope, the borders' reuse, the per-backend runners
assets/languages/go/scripts/go-mutation.py    # --file
src/slipwai/project/native_commands.py        # native['mutation'] = the scope line, native['mutation-full'] = today's
src/slipwai/project/makefile.py               # the mutation-full rule and its .PHONY word — nothing else
src/slipwai/project/mutation.py               # notes and mutation_command() text; the scope line's builder
assets/toolkit/skills/mutation-testing/SKILL.md
docs/backend-obligations.md (and any docs/ page naming `make mutation`)
changelog.d/scoped-mutation.md
tests/test_mutation_scope_*.py                # new, each ≤ 350 lines; tests/test_mutation.py extended
```

**Structure Decision**: the one deployable `slipwai-graph` (kind `tool`, D3); one vocabulary — the factory's
generated toolkit — so one context, and saying so is the decision. Code generated into projects lands under
`assets/` and `src/slipwai/project/` first (owner priority 3). Shared surfaces stay S06's and S14's (D129):
`rules.py`, `scoped_targets.py`, `commands.py`, `parallel_slices.py`, `agents.py`, `verify-scoped.py`,
`check-slice-scope.py` are read or loaded, never edited.

**Pin**: code the factory generates; its tests are the pin (`tests/test_mutation.py`, `tests/test_matrix.py`,
`tests/test_backend_obligations.py`, S06's rules hold).

## Open questions

None blocks the plan. Two readings are recorded for the host to confirm or overturn:

1. **`make mutation-full SINCE=<ref>` still scopes Go.** AC-S08-11 asks for today's recipe byte for byte, and
   today's Go line honours `SINCE`. Recommendation: keep it (byte for byte wins; `SINCE` is a person's explicit
   request); the words say `mutation-full` is the sweep *without* `SINCE`. Alternative: drop `SINCE` from the
   full recipe — that edits a line AC-S08-11 freezes.
2. **An empty `SINCE` under make 3.81** is *assumed* to reach the recipe's environment (research R5); not run here.
   Recommendation: accept, since the manual says so for every version; a macOS CI leg would prove it.

## Complexity Tracking

Nothing to justify.
