# Implementation Plan: S06-scoped-gate — a slice branch runs the checks whose inputs changed, and broadens where it cannot tell

**Branch**: `adopt-method` (D12 — no `slice/` branch, no claim, no push) | **Date**: 2026-10-05 |
**Spec**: [spec.md](../../spec.md), *Slice acceptance criteria* → `### S06-scoped-gate` (AC-S06-1 … AC-S06-19)

**Input**: User Story 2, FR-006, FR-007, FR-023 and SC-007 in [spec.md](../../spec.md); the slice's row in
[story-split.md](../../story-split.md); D114, D115, D116, D117 (and D73–D77, D89, D104 they cite) in
[decisions.md](../../decisions.md); ADR 0004 (Proposed), which this plan extends with the printed record's shape.
Written by cruise iteration 17's plan stage (delegated, strong model). Its two open questions were answered in
iteration 20 as D123 and D124 ([Open questions](#open-questions)).

## Summary

A generated project gets `make verify-scoped`. On a `slice/<id>` branch with a usable base, outside CI, a new
stdlib-only toolkit script, `scripts/verify-scoped.py` (with three modules under `scripts/verify_scoped/`), derives
the verification-dependency record each time it runs — the factory's table of what each check reads, joined with
`project.json`'s `deployables` and its optional `verification.obligations`, the make database's `verify-checks`
prerequisites, the shared packages and the event model — and runs, in **one** `$(MAKE)` call with the gate's
grouping and ordering, only the checks with a changed input: a deployable's own `lint-<name>`, `typecheck-<name>`
and `test-<name>`, the consumers of a changed contract, an obligation's checks, and the readers of a tool or variable
that answers differently from the baseline the last full green `make verify` on this branch left. Everything else is
named as skipped. Everywhere it cannot tell — the trunk, another branch, a detached `HEAD`, CI, no base,
`VERIFY_FORCE`, a change to `project.json`, the `Makefile` or `scripts/`, a file nothing claims, a record it cannot
build, a bad obligation, or a selection that is every check — it runs `make verify` itself and says why in one line.
A stamp `reuse` would accept ends the run at once. The baseline is written by `verify-stamp.py`'s own `record` beside
the stamp and removed when a full run starts, so the `verify`, `verify-checks` and `ci` rules keep every byte
(AC-S06-14). The per-deployable targets and `verify-scoped` are a suffix of the generated `Makefile`; an adopted
repository's `verify-scoped` is its full gate with one line. The ladder's slice start and pre-push gate become
`make verify-scoped`; Phase 4 and the merge root keep `make verify`; the agent settings allow it; the gates page
documents it. MINOR (D114): `VERSION` stays `1.6.0.dev0` (the last release is 1.5.1 and MINOR fragments already
stand), one `changelog.d/scoped-gate.md` fragment with a catch-up note.

## The example map

*Unit* below is a check the record names: a `verify-checks` prerequisite, except that `lint`, `typecheck` and `test`
are named per deployable (`lint-web`). Output lines are spelled in [data-model.md](data-model.md#what-a-run-prints).

| Rule | Criteria | What it says | Examples |
|---|---|---|---|
| **R1** where it is the full gate | AC-S06-1, -14 | Asked in this order — `-n`/`-t`/`-q` in `MAKEFLAGS`, a CI marker, `VERIFY_FORCE`, a detached or unborn `HEAD`, a branch not matching `check-slice-scope`'s `SLICE_BRANCH`, a trunk the gate cannot tell, no merge-base — the first that holds prints one line and runs `"$(MAKE)" -f <makefile> verify`, exiting with its status; the stamp's reuse and record are that target's | e1 on `main`: the line names the trunk, `make verify` runs, a stamp is neither read nor written (as today) · e2 `feature/x`: the line names the branch · e3 `CI=1` on `slice/a`: the line names `CI` · e4 `slice/a` with no `main`/`master` ref: the line carries `check-slice-scope`'s own reason · e5 `VERIFY_FORCE=1` on `slice/a`: `make verify` runs, forced · e6 a failing check under e1: exit status is `make verify`'s · e7 the generated `verify`, `verify-checks` and `ci` rules are byte-for-byte the pre-slice text in every shape |
| **R2** a stamp is stronger than any scoped run | AC-S06-10 | On a slice branch, before reading any change, the key `verify-stamp.py` would build (same tools, same `--environment`s) is compared with the stamp; equal prints verify-stamp's `REUSE_LINE` and exits 0. `verify-scoped` never writes, removes or refreshes a stamp: only `make verify`'s recipe does | e1 after a green `make verify` on `slice/a`, `make verify-scoped` prints the reuse line, starts no check, exits 0 · e2 an edit after it: the scoped selection runs and the stamp file is unchanged (bytes and mtime) · e3 a scoped run that fails leaves no stamp written |
| **R3** a component is a deployable with targets of its own | AC-S06-2, -4, -14 | The generated `Makefile` gains, after everything it has today, per deployable `lint-<name>`, `typecheck-<name>`, `test-<name>` built from that deployable's own recipe lines (`commands_of` per service, the web app's own three); a line naming no deployable's path is a family target `<check>_<family>` the units of that family name as a prerequisite, so it runs once; units take `build-packages` (npm family) or `sync` (Python) and `check-python` as the gate's checks do; under `VERIFY_ORDER` a Java unit chain and a Go `lint-` first, as `gate_order` has it. A deployable whose `test-<name>` would be an existing target (`integration`, `integration-<x>`) gets no units, and the script then cannot build the record (R5) | e1 TypeScript service + web: six units, no family target, each recipe one line of today's merged recipe · e2 two Python services: `lint_python` holds `./scripts/verify --lint-only --synced`; `lint-service` and `lint-billing` name it and nothing else · e3 a Go service: `lint_go` holds the `gofmt` line, `test_go` the `covdata` line · e4 for every shape, the unit and family lines of a check, in order, are exactly that check's recipe lines · e5 the text before the new section equals `makefile()`'s pre-slice output |
| **R4** a change selects its readers and its consumers | AC-S06-2, -3, -4, -7 | A unit runs when a changed path matches one of its file inputs ([data-model.md](data-model.md#the-table)); a pinning file is an input of the units its tool belongs to; a change under a service's path runs `check-openapi` and every web app's `typecheck-`/`test-` whose `api` names it; a change under `packages/<p>/` where `<p>/package.json` exists runs every npm-family deployable's `typecheck-`/`test-`; a change under a service X's path runs the `typecheck-`/`test-` of every service Y≠X whose `model.yaml` slice `reads` an event a slice of X produces (model read at the base and in the working tree); a family unit with no recipe line of its own runs with any sibling and says it shares one recipe; a Go or Java deployable's three run together | e1 `apps/web/src/App.tsx` changed (TS service + web): `lint-web`, `typecheck-web`, `test-web`, `check-styles`, `check-ux-gates`, `check-imports`, `check-migrations`, `check-model` run; `lint-service`, `typecheck-service`, `test-service`, `check-openapi`, `check-drawio`, `check-benchmark`, `check-decisions` skipped · e2 `apps/service/src/main.ts`: service's three, `check-openapi`, `typecheck-web`, `test-web` (consumer) run; `lint-web` skipped · e3 `packages/api-client/src/index.ts`: every npm deployable's typecheck and test · e4 two Python services, one changed: all six units run, the other's named *shares one recipe with* · e5 `apps/service/uv.lock` or root `.nvmrc`: every unit that runs that family's tools · e6 event edge billing→orders: a change in `apps/billing/` runs `typecheck-orders` and `test-orders` |
| **R5** what cannot be established runs the full gate | AC-S06-5 | A changed `project.json`, `Makefile`/`GNUmakefile`/`makefile`, or anything under `scripts/` (`is_gate_script`, which includes `verify-scoped.py` and its modules); a changed path no deployable, contract and claiming input matches (a `packages/<p>/` with no `package.json` included); a record the script cannot build (no `verify-checks` in the make database, a unit `project.json` implies missing from it, a model it cannot read when an event edge is needed) — one line per such file, *dependency knowledge was incomplete*, then `make verify` | e1 `README.md` changed: one line naming it, then the full gate · e2 `project.json` and `scripts/check-imports.py` changed: two lines, one full gate · e3 a deployable named `integration`: one line saying its units are missing, full gate · e4 `packages/shared-go/x.go`: unclaimed, full gate |
| **R6** checks that always run claim nothing | AC-S06-6 | `check-slice-scope` (compares the whole branch) and `check-codegraph` (reads every tracked file) run on every scoped run and claim no file; `check-python` runs on every scoped run because every check waits on it; a `verify-checks` prerequisite with no recorded inputs — `check-agents`, `check-speckit`, `check-extensions`, `check-constitution`, and any check a project added itself — runs, named *no recorded inputs*; none of them broadens anything else | e1 a web-only change: those seven are named as run with their reason, the service's units still skipped · e2 a project's own `check-licences` added to `verify-checks`: runs, *no recorded inputs* |
| **R7** tools and variables against the baseline | AC-S06-8, -9 | `verify-stamp.py record`, after it writes a stamp on a `slice/<id>` branch, writes `verify-baseline-<project>.json` beside it: the branch, the tools the run asked at its start, a SHA-256 of each `variable_record` of `VARIABLES`; every full run that `begin_full_run` starts (and a ratchet run) removes it first. A scoped run asks the same tools once; a unit runs when one of its tools answers differently or one of its variables' digests differs; `UX_GATES_JOBS` and the job count select nothing. No baseline, another branch's, one that does not parse, or a tool that does not answer: one line, and every reader runs — which is every unit, so the run is `make verify` (and that run writes the baseline) | e1 stand-in `node` answering `v20.11.0` then `v22.1.0`: npm-family units and `check-ux-gates`, `check-drawio` run, `test-service` names the tool · e2 `UX_GATES_SINCE` set, then unset: `check-ux-gates` runs; both as at the baseline: skipped · e3 `UX_GATES_JOBS=8`: nothing selected · e4 baseline from `slice/b` on `slice/a`: the line, then `make verify` · e5 a failing `make verify` leaves no baseline; a passing one under `-i` or `RATCHET_TIGHTEN` writes none; a scoped run never writes one |
| **R8** obligations a person declares | AC-S06-11 | `verification.obligations` in `project.json` (read at the base): a list of `{name, components, checks}`; a change under any component's path runs the obligation's checks, named with it. Missing key: none. Present but not that shape, a name twice, fewer than two distinct components, a component not among the `deployables`, a check the record does not know: one line naming the entry, then `make verify` | e1 `{"name": "checkout", "components": ["orders","billing"], "checks": ["test-orders","test-billing"]}` and a change in `apps/orders/`: `test-billing` runs, *obligation `checkout`* · e2 `"checks": ["test-nope"]`: the line names entry 1 and the check, full gate · e3 `"obligations": {}`: the line, full gate |
| **R9** every unit named once, one make call | AC-S06-12 | Each unit is printed once, `run` with the first changed input that chose it or `skip` with *none of its inputs changed*; the chosen units run as one `"$(MAKE)" $(VERIFY_GROUP) --no-print-directory -f <makefile> <units…> VERIFY_ORDER=1`, the script keeping make's jobserver descriptors open (`close_fds=False`); the last line counts run and skipped and says passed, or that the run failed and each failed check is named above on a line carrying `***`; the exit status is the sub-make's | e1 `make -j verify-scoped` with a stand-in check that waits for another: both start before either ends · e2 a failing `test-web`: make's `*** [...test-web]` line, the closing line, non-zero exit · e3 the counts equal the named lines |
| **R10** the record as JSON | AC-S06-13 | `python3 scripts/verify-scoped.py record` prints the derived record in ADR 0004's shape (schema 1): every unit with its gate, components, inputs (files, tools, variables) or `null`, whether it claims, why it always runs; each deployable; each contract with its consumers; each obligation | e1 the TS service + web starter's record parses and lists `check-agents` with `"inputs": null` · e2 a declared obligation appears under `obligations` |
| **R11** the ladder and the harness call it | AC-S06-15 | `drive_command()`: *start the slice from a green `make verify-scoped`*, and `make verify-scoped` before the first push; `concurrent_slices()`: the slice's pre-push gate `verify-scoped`; Phase 4 on `main` and the merge root keep `make verify`; no call carries `-j` (D124); `agent_settings` allows `make verify-scoped`; the constitution templates' principle V, the `planning` skill, and the implement and converge briefs say the scoped gate before the push and the full gate at the merge root and in CI (D123) | e1 a generated `commands/drive.md` carries both scoped calls and the Phase 4 `make verify` · e2 `.claude/settings.json` lists `Bash(make verify-scoped)` · e3 a generated constitution (both profiles) carries D123's principle V sentence as D126 reworded it and no longer *The whole suite MUST be green immediately before that first implementation push*; the `planning` skill and the implement and converge briefs carry D123's wording · e4 no ladder line types `-j` |
| **R12** an adopted repository | AC-S06-16 | Where the gate is not the stamped one (`gate.stamped()` false), `verify-scoped` prints *this layout has no verification-dependency record yet* and runs `$(MAKE) -f <its makefile> verify` | e1 `make -f delivery/Makefile verify-scoped` in an adopted fixture: the line, then the full gate's output and exit status |
| **R13** what a project already made gets, and the words | AC-S06-17, -18 | `migrate` brings the new `Makefile` section and scripts; `metadata()` never writes `verification`; the fragment claims MINOR with a standalone catch-up note; the gates page documents where it scopes, where it is the full gate, what broadens, the baseline, and the obligations key, its default (none) and when to declare one, and that `make -j verify-scoped` runs the chosen checks at once (D124); the catch-up note says a ratified constitution keeps its words and quotes D123's sentence, as D126 reworded it, for a maintainer who amends it | e1 a project generated at the last release, migrated: `make verify-scoped` exists, `project.json` has no `verification` · e2 the fragment's first line is `MINOR`, its note names `make verify-scoped`, the merge root and CI, and `verification.obligations` · e3 the page has the paragraph in a stamped project, the one sentence in an adopted one |
| **R14** measured, and S05 still holds | AC-S06-19 | At the merge root `make verify` runs pytest with xdist (S05's tests unchanged); the demo records `make verify-scoped` on `slice/S1` touching one deployable of the two-deployable starter against `VERIFY_FORCE=1 make verify` on the same tree, with the command and the machine, in the quickstart and the fragment | e1 three runs each, medians, the machine's CPU and `nproc` |

Every AC-S06-n is covered: 1, 14 (R1); 10 (R2); 2, 4, 14 (R3); 2, 3, 4, 7 (R4); 5 (R5); 6 (R6); 8, 9 (R7);
11 (R8); 12 (R9); 13 (R10); 15 (R11); 16 (R12); 17, 18 (R13); 19 (R14).

## Technical Context

**Language/Version**: Python 3 (the factory, `src/slipwai/`); Python ≥ 3.10 stdlib only (the toolkit scripts a
project runs, as `check-python` holds); GNU Make from 3.81 (the generated `Makefile`).
**Primary Dependencies**: none new. The script imports `check-slice-scope.py` (base, changes, slice-branch rule,
model loader) and `verify-stamp.py` (tools, variables, stamp, baseline) by path, as `verify-stamp.py` already
imports `check-slice-scope.py` (`trunk_module()`), with `sys.dont_write_bytecode` set.
**Storage**: one new JSON file under `<git-dir>/slipwai/` beside the stamp (the baseline); one optional
`project.json` key a person writes. Nothing in the working tree.
**Testing**: `unittest` in `tests/`; generated projects in temporary directories with stand-in executables on
`PATH` written in the test tree (a logging `npm`, a `node` whose `--version` the test sets) — no mocking framework.
Each new module under 350 lines (`make check-structure`).
**Target Platform**: Linux and macOS developer machines; CI is never scoped.
**Performance Goals**: the scoped run's own overhead (the stamp key, one make-database read, the diff) is a small
part of the checks it skips; AC-S06-19 measures the whole.
**Constraints**: SC-007 and constitution I — `verify`, `verify-checks`, `ci` unchanged; every doubt widens.
**Scale/Scope**: every generated shape the matrix and `test_verify_stamp_scan.SHAPES` cover, plus two-service shapes.

## Constitution Check

The factory's constitution (`.specify/memory/constitution.md`):

- **I. A generated project owns its files and passes its own gate** — *a scoped or memoised gate MUST be additive*:
  the merge root and CI run `make verify`; `verify-scoped` delegates to it everywhere but a slice branch it can read,
  and the rules `verify`, `verify-checks`, `ci` are byte-for-byte (R1 e7, R3 e5). `migrate` brings the change; the
  obligations key is the project's own and never written by the factory (R13). Every starter still passes its own
  `make verify` in the matrix. A `changelog.d/` fragment names MINOR; `VERSION` is unchanged.
- **III. Simplicity** — no stored record, no new file kind, no dependency (D114): one script and its table; the
  family target is the smallest construct that runs a shared line once.
- **VII. Auditability** — every unit is named with why it ran or was skipped; every broadening says its reason.
- **VIII. Versioning** — the printed record (schema 1) and `verification.obligations` are published contracts
  (ADR 0004); readers tolerate unknown fields (an obligation entry's extra keys are ignored).
- **IX. Security, privacy** — the baseline holds digests of variables, never values, and the tools' version words
  only (`stored_answer`), as the stamp does; no path or host name is persisted.
- **XIII. Fast feedback** (a target here) — this is the slice that scopes the branch gate; nothing leaves the gate.
- **XIV. Agent-generated change meets the same bar** — the ladder's merge root and Phase 4 keep the full gate; the
  generated constitution templates' principle V is reworded to *the scoped gate before the first push, the full gate
  at the merge root and in CI*, still a MUST (D123).

No ratified constitution is amended by this plan: the templates seed new projects only, and the catch-up note hands
the amendment to a project's maintainer (D123).

## Structure Decision

**Factory source**

- `src/slipwai/project/scoped_targets.py` *(new, < 350 lines)*: `scoped_section(apps, layout)` — the unit rules,
  family targets, their prerequisites and `VERIFY_ORDER` chains, the name-collision rule, and the `verify-scoped`
  rule for a stamped gate or the adopted one; `SCOPED_PAGE` and `ADOPTED_SCOPED_SENTENCE` for the gates page.
- `src/slipwai/project/makefile.py` (333 lines): import, and `{scoped_section(apps, layout)}` appended after
  `{adoption_targets(apps, layout)}` at the very end — nothing before it moves (+2 lines).
- `src/slipwai/project/native_commands.py` (308): `web_recipes(web)` extracted from `native_commands()` so the web
  lines are spelled once for the merged recipes and the units (net ≈ +6).
- `src/slipwai/project/docs.py` (331): the gates page adds `SCOPED_PAGE` where stamped, the adopted sentence
  elsewhere (+2).
- `src/slipwai/project/commands.py` (345): lines ~179 and ~190 reworded in place, no line added.
- `src/slipwai/project/parallel_slices.py`: the pre-push `{layout.make} verify` (~127) becomes `verify-scoped`;
  Phase 4 (~134) unchanged.
- `src/slipwai/project/agent_settings.py`: `"make verify-scoped"` beside `"make verify"`.
- `src/slipwai/project/agents.py`: the implement brief (~135) and the converge brief (~189) reworded in place (D123).
- `assets/profiles/standard/.specify/presets/standard/templates/constitution-template.md` (~124) and
  `assets/profiles/event-modelling/.specify/presets/event-modelling/templates/constitution-template.md` (~136):
  principle V's pre-push sentence, D123's wording; `tests/test_commit_boundaries.py`'s phrase kept.
- `assets/toolkit/skills/planning/SKILL.md` (~221): D123's wording.
- `assets/toolkit/scripts/verify-stamp.py`: `baseline_path()`, `variable_digests()`, `write_baseline()` called by
  `record()` after the stamp is written on a `slice/<id>` branch, the baseline removed in `begin_full_run()` and on
  the ratchet path of `reuse()`; nothing else changes (its split is S32's).
- `assets/toolkit/scripts/verify-scoped.py` *(new)*: verbs `run` and `record`; R1's borders, R2, printing, the one
  make call, delegation.
- `assets/toolkit/scripts/verify_scoped/table.py` *(new)*: the factory's table (data-model.md).
- `assets/toolkit/scripts/verify_scoped/record.py` *(new)*: the make database, the join, contracts, obligations,
  the JSON.
- `assets/toolkit/scripts/verify_scoped/choose.py` *(new)*: changed paths, the baseline comparison, the choice and
  its reasons.
  No literal `apps/service` or `apps/web` in any of them (`toolkit.spoken_for` rewrites those).
- `changelog.d/scoped-gate.md` *(new)*: MINOR, with the catch-up note and AC-S06-19's measurement.

Not changed: `gate.py`, `parallel_gate.py`, `adopted_targets.py`, `metadata.py`, `catalog.json`, `VERSION`, this
checkout's `delivery/` (it gains the target when `slipwai migrate` is run here, which is not this slice's).

**Tests** *(new modules, each < 350 lines; a fixture helper shared by them)*

- `tests/scoped_fixture.py` — generate a shape once per class, init a `slice/S1` branch, stand-ins on `PATH`.
- `tests/test_scoped_targets.py` — R3 (units, family targets, prerequisites, sums, collisions, the suffix), R1 e7.
- `tests/test_verify_scoped_borders.py` — R1, R2.
- `tests/test_verify_scoped_choose.py` — R4, R5, R6, R9.
- `tests/test_verify_scoped_baseline.py` — R7 (and verify-stamp's write/remove).
- `tests/test_verify_scoped_record.py` — R8, R10; the table held against the check scripts' reads (every
  project-relative path literal a check script reads lies under one of that check's recorded inputs, or it has no
  recorded inputs), reusing `test_verify_stamp_lists`.
- `tests/test_scoped_ladder.py` — R11, R12, R13.

## Pin

The generated `Makefile` and ladder text are generated code; their tests are the pin, run before and after:
`tests/test_verify_stamp_pinned.py` (the `verify` rule's bytes), `tests/test_verify_stamp_recipe.py`,
`tests/test_verify_stamp_scan.py`, `tests/test_parallel_gate_reads.py` (`READS_NOTHING` over the gate's targets —
units are not gate targets, so its closed list is unchanged; `test_scoped_targets.py` adds the same classification
for the units), `tests/test_commit_boundaries.py`, `tests/test_commands.py`, `tests/test_matrix.py`, and the
`tests/test_verify_stamp_*` modules for `verify-stamp.py`. Before the first increment, `make starters` and keep
`build/` aside; after the last, the diff of `build/` is the change a user sees (`docs/maintaining.md`, *Browse the
starters*): a `Makefile` suffix, the new scripts, `verify-stamp.py`, the gates page, the settings line, the ladder.

## Open questions

Both answered in iteration 20; the questions as raised are in the entries.

**Q1 — answered by D123: (a).** The ladder runs `make verify-scoped` before the first push; both generated
constitution templates' principle V, the `planning` skill and the implement and converge briefs are reworded to
*the scoped gate before the first push, the full gate at the merge root and in CI* — the exact words are D123's
items 1–4 — for new projects only. A ratified constitution keeps its words; the fragment's catch-up note says so and
quotes the new sentence (D123 item 5). Medium confidence: it reverses if the owner holds a template's MUST as
theirs to approve, and then only the template sentence parks.

**Q2 — answered by D124: (a).** The ladder types `make verify-scoped` and `make verify`, never `-j`; jobs come
from the person or the harness (`MAKEFLAGS`), which the scoped run's sub-make inherits (R9). The gates page says
`make -j verify-scoped` runs the chosen checks at once.
