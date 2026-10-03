# Implementation Plan: S20-slice-scope-root — a slice branch in a root-adopted repository passes the slice-scope gate

**Branch**: `adopt-method` (D12 — no `slice/` branch, no claim, no push) | **Date**: 2026-10-03 |
**Spec**: [spec.md](../../spec.md), *Slice acceptance criteria* → `### S20-slice-scope-root` (AC-S20-1 … AC-S20-13)

**Input**: the slice's row in [story-split.md](../../story-split.md) and its criteria in `spec.md`; decisions
D9, D12, D13, D17, D18, D19 in [decisions.md](../../decisions.md). Written by cruise iteration 3 (host, strong
model). The optional `before_plan` hook (`/characterise`) is taken as the ladder's Pin stage, after tasks.

## Summary

Three generated checkers read a repository the way a generated project is laid out, and are wrong in one that
adopted the method at its root with slice ids that carry a slug. (1) `check-slice-scope.py`: a deployable
recorded at `path: "."` owns no path today, so every file on a `slice/<id>` branch is *outside every deployable*;
it becomes the fallback owner of every path no other deployable claims, except a named host surface (D18).
(2) `check-decisions.py` and (3) `agents/benchmark.py` cut a register id `S00-run-path` to `S00`; they read the
first cell whole and fall back to the bare prefix wherever the whole id finds nothing (D19). A PATCH: the same
answers, generated better; a project with its deployables under `apps/` and bare ids gets today's answers.

## The example map (rules the tasks cut on)

| Rule | Criteria | What it says | Examples |
|---|---|---|---|
| **R1** root deployable is the fallback owner | AC-S20-1, -6, -8 | On a `slice/<id>` branch in a repository whose one deployable is at `.`, a file that is the application's own is the slice's | e1 `tests/test_x.py` changed → exit 0, *touches only what one slice may* · e2 `worker/x.py`, root `scripts/x.py`, root `docs/x.md` → green · e3 root `requirements.txt` (the fixture's manifest) and a `pyproject.toml` → green · e4 `path: "./"` recorded → same answers · e5 a deployable with `path: ""` owns nothing: its file is *outside every deployable* |
| **R2** the host surface stays the host's | AC-S20-2, -3, -4, -5 | Where the root deployable would claim a path, the host's surface is refused with today's *outside every deployable … Land it on `main` before the fan-out* | e1 one at a time: root `Makefile`, `project.json`, `.specify/x.json`, `.github/workflows/x.yml`, `AGENTS.md`, `.claude/settings.json` → refused · e2 `<delivery>/scripts/x.py`, `<delivery>/skills/x/SKILL.md`, `<delivery>/commands/x.md`, `<delivery>/Makefile`, `<delivery>/baseline.json` → refused · e3 `<delivery>/docs/x.md` → today's *the docs are the host's* · e4 `<delivery>/survey/pinned.md`, `<delivery>/survey/running.md` → green; `<delivery>/survey/survey.md` → refused · e5 a path listed in `<delivery>/.written` and on no fixed name → refused · e6 `.written` with the CI gate's line deleted → the gate workflow still refused · e7 `.written` absent → fixed list holds, no crash · e8 `ci.gate` naming a file outside the fixed CI names (say `ci/gate.yml`) → refused |
| **R3** a subdirectory deployable owns its own | AC-S20-7 | With a root deployable and a `service` under `apps/api`, the subdirectory wins for paths under it | e1 slice whose model block names another service, `apps/api/x.py` changed → *service `api` is not slice …'s* · e2 same branch, `tests/test_x.py` → green (root) |
| **R4** nothing moves under `apps/` | AC-S20-9 | A generated project gets today's answers | e1 `SliceScopeGateTest` passes with the test file untouched |
| **R5** `check-decisions` reads the register id whole | AC-S20-10, -11 | A done slice is found in the adversary log under its whole id or its bare prefix | e1 register `` `S00-run-path` ``, row `## S00-run-path · …` → pass · e2 row `## S00 · …` → pass · e3 neither → fails naming `S00-run-path` · e4 register `S1`, row `## S1 · …` → pass as today; header and separator rows are no ids |
| **R6** `check-benchmark` finds the record under the whole id | AC-S20-12 | The record is looked for at `slices/<whole id>/`, then `slices/<prefix>/` | e1 `slices/S00-run-path/benchmark.json` closed → no warning · e2 only `slices/S00/benchmark.json` → no warning · e3 neither → one warning naming `slices/S00-run-path` · e4 register `S1` → as today |
| **R7** the release says what it is | AC-S20-13 | One `PATCH` fragment; `VERSION` unchanged | e1 `changelog.d/slice-scope-root-deployable.md`, first line `PATCH`; `tests/test_changelog.py` green |

## Technical Context

**Language/Version**: Python ≥ 3.11 (`pyproject.toml:16`).
**Primary Dependencies**: none added; standard library only (owner brief, *Taste*).
**Storage**: N/A — the checkers read `project.json`, `<delivery>/.written`, the register and the adversary log.
**Testing**: `unittest` via `make test`; new tests drive each script as a subprocess in a temporary repository,
the seam the existing suites use (`tests/test_parallel_slices.py` `SliceScopeGateTest.check`,
`tests/test_cruise_record.py` `gate`, `tests/test_benchmark_brackets.py`). A root-adopted repository is made
with `tests/test_adopt.py`'s `repository()` and `slipwai(repo, "adopt", "--yes")`. No mocking framework.
**Target Platform**: wherever a generated or adopted project runs its gate (Linux, macOS, Git Bash).
**Project Type**: CLI tool, the factory — deployable `slipwai-graph`, kind `tool`, path `.`; the change is to
assets it copies into projects (`assets/toolkit/scripts/`).
**Performance Goals**: none; one extra small file read (`.written`) per slice-branch check.
**Constraints**: PATCH — no setting, no flag, no file added to a project; nothing under `delivery/scripts/`,
`tools/`, the `Makefile`, CI or hook settings changes in this repository (cruise controls; the fix reaches
here through a person's `slipwai migrate`, D9); `tests/test_parallel_slices.py` is not edited (R4);
`make check-structure` and `tests/test_line_widths.py` budgets hold.
**Scale/Scope**: 3 asset scripts, 2 new test files, 1 changelog fragment.

## Constitution Check

*GATE: evaluated against `.specify/memory/constitution.md` before research; re-checked after design.*

| Principle | Touched? | How this slice satisfies it |
|---|---|---|
| I. A generated project owns its files and passes its own gate (NON-NEGOTIABLE) | Yes | The gate is made right in the files the factory writes (`assets/toolkit/scripts/`), never in this repository's installed copy; nothing a generated project's gate checks is removed — the host surface is still refused (R2), and `apps/` projects are unchanged (R4). |
| III. Simplicity | Yes | Constants and one predicate in the checker; one small id-reading function in each of the two others (they already duplicate `done_slices`; no shared module is introduced for a PATCH). No setting. |
| V. Acceptance-driven development (in force since S00) | Yes | Each rule is a RED-GREEN-REFACTOR cycle through the script's own command line; each example observed failing for its stated reason first. |
| VIII. Versioning and breaking changes | Yes | PATCH fragment in the commit that changes the first asset; `VERSION` stays `1.5.2.dev0` (a release opens the next number as a PATCH — AGENTS.md); D19 keeps records written under the bare prefix green, so nothing is asked of a generated repository. |
| XIV. Agent-generated change meets the same bar (NON-NEGOTIABLE) | Yes | Increment commits with the quickest relevant tests green; both full gates before the demo; the hand runs the demo as the actor. |
| II, IV, VI, VII, IX, X, XI, XII, XIII, XV | No | No retry path, domain code, contract, telemetry, secret, pipeline or type changes. |

**Gate result:** no violation; *Complexity Tracking* stays empty. **Post-design re-check:** unchanged — the
design adds no file to a generated project and no dependency.

## Project Structure

### Documentation (this slice)

```text
specs/001-faster-slipwai/slices/S20-slice-scope-root/
├── plan.md, research.md, data-model.md, quickstart.md
├── tasks.md             # the tasks stage
└── benchmark.json, demo-log.md, demo/
```

### Source code (repository root)

```text
assets/toolkit/scripts/check-slice-scope.py     # R1–R3: fallback owner, host surface, docstring
assets/toolkit/scripts/check-decisions.py       # R5: register id whole, prefix accepted in the log
assets/toolkit/scripts/agents/benchmark.py      # R6: record under the whole id, then the prefix
tests/test_slice_scope_root.py                  # new — R1–R3 on a repository adopted at `.`
tests/test_register_ids.py                      # new — R5, R6 on a generated project's register
changelog.d/slice-scope-root-deployable.md      # R7
```

**Structure Decision**: one deployable, `slipwai-graph` (kind `tool`, path `.`, purpose confirmed) — the only
one in `project.json`; one bounded context (the factory; D3). The decided strategy is `leave-it`
(`delivery/docs/adr/0002-change-strategy.md`, Accepted by a person): no new home, no routing seam. The code
changed existed before the method did, so the Pin stage applies (see *Pin*).

## Design

**`check-slice-scope.py`.** `Scope.owning_app()` tries every deployable whose path is not the root first, in
today's order and with today's test; a deployable whose stripped path is `.` (so `./` too) is returned only
when none of them matched. An empty or missing path still owns nothing. `code_violation()` asks one more
question when the owner is the root deployable: is the path on the host surface? If so it returns today's
*outside every deployable* message unchanged. The host surface (D18): the delivery directory (`DELIVERY`, when
it is not the root) except `survey/pinned.md` and `survey/running.md`; `project.json`; root `Makefile`;
`.specify/`; `.github/`, `.gitea/`, `.forgejo/`, `.gitlab/`, `.gitlab-ci.yml`, and `ci.gate` where
`project.json` records a string; `AGENTS.md`, `CLAUDE.md`, `.claude/`, `.codex/`, `.cursor/`, `.gemini/`,
`.opencode/`; and every line of `<delivery>/.written` where the file exists. The order in `violation()` does not
change: specs, model, canvas, mockups, ADRs and docs are answered before `code_violation()` is reached. The
docstring gains the root case in the same plain words.

**`check-decisions.py` and `agents/benchmark.py`.** `done_slices()` reads the first cell's leading id whole —
letters, digits, then any of `[A-Za-z0-9._-]` (the alphabet `SLICE_BRANCH` already allows) — so a header
(`Slice`) and a separator (`---`) are still no ids. `check_adversary_rows()` takes a row headed with the whole
id or with its bare prefix (`[A-Za-z]+\d+`); the finding names the whole id. `benchmark.check()` looks for
`slices/<id>/benchmark.json` and, where that directory holds none, `slices/<prefix>/`; its findings name the
whole id's path. An id with no slug has prefix equal to itself: today's behaviour.

## Pin

`delivery/survey/running.md` records the run path proven (S00) and `project.json` records `smoke`. The three
behaviours this slice changes, each to be recorded in `delivery/survey/pinned.md` by `/characterise` before
implementation, with the tests that already hold them where they do: (1) the slice-scope gate's answers on a
generated project — `tests/test_parallel_slices.py` `SliceScopeGateTest`; (2) `check-decisions`' adversary-row
finding for a done slice — `tests/test_cruise_record.py`; (3) `check-benchmark`'s done-slice warnings —
`tests/test_benchmark_brackets.py`. **Pinned 2026-10-03** (cruise iteration 3, host): three rows appended to `delivery/survey/pinned.md`, each naming tests that were already there and green before any change (9 tests in `SliceScopeGateTest` and `test_cruise_record`, and `test_benchmark_brackets`); no new characterisation test was needed and no seam introduced. What is not pinned is exactly what the slice changes on purpose: the root
path owning nothing, and the id cut to its prefix.

## Branch and integration

As D12: increments land on `adopt-method`, one slice at a time, no `slice/` branch, nothing pushed; the
register's *Merged as* names the first and last commit. The demo runs from this checkout's tip against a
temporary repository adopted at `.` ([quickstart.md](quickstart.md)). The fix does not reach this repository's
own `delivery/scripts/` inside the run (D9): after it, this checkout's gate still reads ids by prefix and still
has the root defect, and the adversary row is headed `## S20 · …` (D17).

## Deliberate stubs

None.

## Complexity Tracking

Empty.
