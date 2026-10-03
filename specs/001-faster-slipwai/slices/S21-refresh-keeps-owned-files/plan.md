# Implementation Plan: S21-refresh-keeps-owned-files — a refresh leaves the project's own settings and the owner brief alone

**Branch**: `adopt-method` (D12 — no `slice/` branch, no claim, no push) | **Date**: 2026-10-03 |
**Spec**: [spec.md](../../spec.md), *Slice acceptance criteria* → `### S21-refresh-keeps-owned-files` (AC-S21-1 … AC-S21-11)

**Input**: the slice's row in [story-split.md](../../story-split.md) and its criteria in `spec.md`; decisions
D9, D12, D15, D16, D24, D25 in [decisions.md](../../decisions.md). Written by cruise iteration 4 (host, strong
model). The optional `before_plan` hook (`/characterise`) is taken as the ladder's Pin stage, after tasks.

## Summary

`slipwai adopt --refresh` (experimental: brownfield adoption) rewrites every file the factory assembles
wherever the disk differs from the assembly. Four of those files are seeded by the factory and then changed by
the project — `.specify/cruise.json`, `.specify/product-owner.md`, `.specify/models.json`, `.specify/drive.json`
— so a refresh resets a run's settings and replaces a filled-in owner brief with the template (D15, seen on
this repository). A refresh now writes each of the four only where it is absent (D24). Separately, the refresh
derives `strategy.before` from the tree's reading of the map before a person's recorded rows are reconciled
into it, so the strategy page names a prerequisite the map shows as met; `before` now follows the rows as the
map shows them after the refresh (D25). A PATCH: the same answers, generated better.

## The example map (rules the tasks cut on)

| Rule | Criteria | What it says | Examples |
|---|---|---|---|
| **R1** a seeded file that is there is the project's | AC-S21-1, -2, -3, -6 | A refresh never compares, rewrites or counts one of the four where it exists | e1 `cruise.json` committed with `enabled: true`, `max_iterations: 10` → bytes unchanged, not in `git status`, not in the rewritten count · e2 `product-owner.md` committed with its sections filled → the same · e3 `models.json` and `drive.json` each committed with a non-default value → the same · e4 the same repository, `slipwai adopt --confirm` recording one answer → the four unchanged |
| **R2** a seeded file that is missing is written | AC-S21-4 | Absent (deletion committed), the refresh writes the factory's default and counts it | e1 `cruise.json` deleted and committed → after the refresh it holds the factory default and the report counts it · e2 the same for `product-owner.md` |
| **R3** an uncommitted change to a seeded file refuses nothing | AC-S21-5 | The refusal protects what a run writes, and the run no longer writes these | e1 `cruise.json` edited, not committed → the refresh runs, the edit stands · e2 an uncommitted hand edit to `<delivery>/docs/convergence.md` → refused by name, as today |
| **R4** what the record drives still follows, and the listing stands | AC-S21-7, -8 | The pages follow the record; `.written` keeps the four; no `owned:` line for them | e1 a convergence row moved by hand in `project.json` → `<delivery>/docs/convergence.md` rewritten to show it · e2 after any refresh `.written` lists the four · e3 the report has no `owned:` line naming one of the four |
| **R5** `strategy.before` follows the map | AC-S21-9, -10 | Each row-derived precondition is read from the rows after reconciliation | e1 Safety net `confirmed` at `tests-pass`, tree reads `tests-exist` → no *a green suite in the gate* entry in `project.json` `strategy.before`, none in `<delivery>/docs/change-strategy.md` · e2 row left at `tests-exist` → both still carry it · e3 Path to production recorded by a person at a rung above `scripted` → *a pipeline that deploys* entry gone · e4 Structure recorded above `as-found` → its entry gone · e5 `recommended`, `because`, `decided`, `finished`, `programme` equal before and after |
| **R6** the release says what it is | AC-S21-11 | One `PATCH` fragment, labelled experimental; `VERSION` unchanged | e1 `changelog.d/refresh-keeps-owned-files.md`, first line `PATCH`; `tests/test_changelog.py` green |

## Technical Context

**Language/Version**: Python ≥ 3.11 (`pyproject.toml:16`).
**Primary Dependencies**: none added; standard library only (owner brief, *Taste*).
**Storage**: N/A — the refresh reads and writes files in the adopted repository.
**Testing**: `unittest` via `make test`; new tests drive `slipwai adopt`, `adopt --refresh` and `adopt --confirm`
as the existing suites do, against a temporary git repository — the seam and helpers in `tests/test_adopt.py`
(`repository()`, `slipwai(...)`) and the refresh assertions in `tests/test_adopt_facts.py` and
`tests/test_uncommitted.py`. No mocking framework.
**Target Platform**: wherever `slipwai` runs (Linux, macOS, Git Bash).
**Project Type**: CLI tool, the factory — deployable `slipwai-graph`, kind `tool`, path `.`.
**Performance Goals**: none.
**Constraints**: PATCH — no setting, no flag, no new file in a project; nothing under `delivery/scripts/`,
`tools/`, the `Makefile`, CI or hook settings changes in this repository; `src/slipwai/resurvey.py` is at the
350-line budget `make check-structure` holds, so what is added lands beside it (a small module, or
`strategy.py` for R5) rather than in it; every file under `tests/` is held to 350 lines too.
**Scale/Scope**: `resurvey.py`, `strategy.py`, at most one new small module under `src/slipwai/`, 2 new test
files, 1 fragment, one sentence in `docs/adopting.md`.

## Constitution Check

*GATE: evaluated against `.specify/memory/constitution.md` before research; re-checked after design.*

| Principle | Touched? | How this slice satisfies it |
|---|---|---|
| I. A generated project owns its files and passes its own gate (NON-NEGOTIABLE) | Yes | *The factory MUST NOT overwrite … a file in a repository it … adopted except through a command the project's maintainer ran*: the refresh is such a command, and it stops writing over four files the project owns; nothing a gate checks is removed; `VERSION` untouched, fragment in the first user-visible commit. |
| III. Simplicity | Yes | One tuple of paths and one presence test at the three places the refresh decides what it writes; one function deriving `before` from rows. No setting. |
| V. Acceptance-driven development (in force since S00) | Yes | Each rule a RED-GREEN-REFACTOR cycle through the CLI; each example observed failing for its stated reason first (R2, R3e2, R4 and R5e2 are today's behaviour and are written as holds, saying so). |
| VIII. Versioning and breaking changes | Yes | PATCH; experimental label on the fragment as `AGENTS.md` requires for the adoption path; the fragment says what a repository already reset does. |
| XIV. Agent-generated change meets the same bar (NON-NEGOTIABLE) | Yes | Increment commits with the quickest relevant tests green; both full gates before the demo; the hand runs the demo as the actor. |
| II, IV, VI, VII, IX, X, XI, XII, XIII, XV | No | No retry path, domain code, contract, telemetry, secret, pipeline or type changes. |

**Gate result:** no violation; *Complexity Tracking* stays empty. **Post-design re-check:** unchanged.

## Project Structure

```text
src/slipwai/resurvey.py                    # R1–R4: what a refresh writes, refuses on and stamps; R5: where `before` is re-derived
src/slipwai/strategy.py                    # R5: `before` derived from given rows (a function the refresh can call again)
src/slipwai/<small module, if the budget needs it>
tests/test_refresh_owned.py                # new — R1–R4
tests/test_refresh_strategy.py             # new — R5
changelog.d/refresh-keeps-owned-files.md   # R6
docs/adopting.md                           # the `--refresh` row: one sentence
```

**Structure Decision**: one deployable, `slipwai-graph` (kind `tool`, path `.`, purpose confirmed); one bounded
context (the factory; D3). The decided strategy is `leave-it` (`delivery/docs/adr/0002-change-strategy.md`,
Accepted by a person): no new home. The code changed existed before the method did, so the Pin stage applies.

## Design

**The four.** Named once, from the constants their writers already export (`project/cruise_record.py` `CONFIG`,
`project/drive_settings.py` `CONFIG`, `project/decisions.py` `PAGE`, and the models table's path in
`scaffold.py`), as they are placed for the repository's layout. *Kept* = those of the four that exist on disk
when the refresh starts. In `refresh()`: `writes()` leaves the kept out, so `refuse_foreign` does not refuse on
them (R3); the rewrite loop skips the kept exactly as it skips `owned` (R1), and so writes an absent one (R2);
the final `stamp` leaves them out, so a later run does not take a project's edit for slipwai's own. The
`.written` content in `after` is not touched, and `done.owned` is not extended (R4). `confirm` calls `refresh()`
and inherits all of it.

**`strategy.before`.** `with_recommendation()` builds the record from `detected()` rows; `refresh()` then
reconciles those rows with what was recorded. After that reconciliation, and before `project_files(...)`
assembles `after`, the strategy record's `before` is replaced by the platform entries it leads with followed by
`preconditions(reconciled rows, recommended strategy)` — through one function in `strategy.py` used by both
`recommend()` and the refresh, so the two cannot drift. `change-strategy.md` is assembled from the record and
follows; `project.json` takes `strategy` from the same assembly.

## Pin

`delivery/survey/running.md` records the run path proven (S00) and `project.json` records `smoke`. Two
behaviours change, each recorded in `delivery/survey/pinned.md` before implementation with the tests that
already hold what must stay: (1) what a refresh rewrites, refuses and leaves — `tests/test_adopt_facts.py`
(the record stays still between surveys; a file taken over stays taken; the page follows the record) and
`tests/test_uncommitted.py` (a hand edit to a file a refresh writes is refused by name); (2) the strategy
record a survey derives — `tests/test_strategy.py`. Not pinned, because the slice changes it on purpose: that a
seeded file differing from the factory default is rewritten, and that `before` reads the tree's rows.

## Branch and integration

As D12: increments land on `adopt-method`, one slice at a time, no `slice/` branch, nothing pushed. The demo
runs this checkout's `./slipwai` against a temporary repository ([quickstart.md](quickstart.md)). The fix is in
`src/slipwai/`, which this checkout runs directly — so from this slice on a `/survey` here no longer needs
D15's revert; no `slipwai migrate` is involved.

## Deliberate stubs

None.

## Complexity Tracking

Empty.
