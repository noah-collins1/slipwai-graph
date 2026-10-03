# Implementation Plan: S00-run-path — prove the run path and establish a green gate

**Branch**: `adopt-method` (D12 — no `slice/` branch; see *Branch and integration*) | **Date**: 2026-10-03 |
**Spec**: [spec.md](../../spec.md), *Slice acceptance criteria* → `### S00-run-path` (AC-S00-1 … AC-S00-7)

**Input**: the slice's row in [story-split.md](../../story-split.md) and its criteria in `spec.md`; decisions
D2, D8, D11, D12, D13 in [decisions.md](../../decisions.md). Written by cruise iteration 2 (host, strong model).

## Summary

A method slice, the one the Pin stage exempts: before any product slice changes code that was here, the team
knows the factory starts and its suite is green in the gate. Three things change, none of them user-visible:
(1) the tests that spawn or drive `scripts/agents/cruise.py` stop letting the child inherit the cruise runner's
two environment marks, so the suite is green inside an iteration as it already is outside one (R2, R3);
(2) `delivery/survey/running.md` records the proven run path (R1); (3) with both gates green, the Safety net
row moves `tests-exist → tests-pass` with the evidence that established it, the constitution's principle V
comes into force as the journey says it does, and `/survey` redraws the page (R5, R6, D11). The first run of
the delivery gate would have recorded a ratchet baseline, `delivery/baseline.json`, had any ratcheted command
had findings; every one was clean, so no file came into being (R4, T003).

## Technical Context

**Language/Version**: Python ≥ 3.11 (`pyproject.toml:16`); this machine runs 3.14.4 (R1).
**Primary Dependencies**: none added. Standard library (`subprocess`, `os`, `unittest`, `unittest.mock`
already used by `tests/test_cruise_start.py`).
**Storage**: N/A — files under `delivery/survey/`, `delivery/baseline.json`, `project.json`, the constitution.
**Testing**: `unittest` via `make test` (`Makefile:31–32`), through the ratchet in the delivery gate (R4).
**Target Platform**: Linux (the maintainer machine and GitHub Actions). Windows is not touched by this slice.
**Project Type**: CLI tool, the factory itself — deployable `slipwai-graph`, kind `tool`, path `.`.
**Performance Goals**: none beyond the gates finishing; the full suite's wall time is recorded, not targeted.
**Constraints**: nothing under `assets/`, `src/slipwai/`, `catalog.json` or the CLI changes (AC-S00-7); no
`changelog.d/` fragment; `VERSION` stays `1.5.2.dev0`; nothing under `delivery/scripts/`, `tools/`, the
`Makefile`, CI or hook settings changes (cruise controls); no test is quarantined, skipped or moved.
**Scale/Scope**: 5 test files, 1 survey page, 1 row of `project.json`, 2 principles' journey text; no new file
(the ratchet baseline the plan first expected is written only when a command has findings, R4).

## Constitution Check

*GATE: evaluated against `.specify/memory/constitution.md` before research; re-checked after design (below).*

| Principle | Touched? | How this slice satisfies it |
|---|---|---|
| I. A generated project owns its files and passes its own gate (NON-NEGOTIABLE) | Yes — this repository is held to its own gates | Both `make verify` and `make -f delivery/Makefile verify` green on the final commit, with the runner's marks set (AC-S00-5). No gate is changed to pass: the fix is in the tests' child environment. |
| III. Simplicity, and the rung you are on | Yes | One helper copying an existing precedent (`hook()`); no new dependency; no abstraction beyond a function. |
| V. Acceptance-driven development (target → in force by this slice) | Yes — the slice brings it into force | The one behaviour change (the child environment) is driven RED-GREEN: an example through the existing seam (`cruise(repo, "loop")` with the marks in the parent) fails today with *iteration 2 of a run already under way* and passes after; the existing 6 red tests are the second observation. Written as the principle in force once the row moves (R6). |
| IX. Security, privacy, compliance | No | No data, no secret, no credential; `delivery/baseline.json` records exit codes and finding strings only. |
| X. Continuous integration on trunk (target, not in force) | Touched by D12 | Nothing is pushed; `adopt-method` is where the person left the work; constitution X's current text (*work lands through short pull requests*) is a person's step this slice leaves to them. |
| XIII. Fast feedback (target) | Touched | The marker moves from `tests-exist` to `tests-pass`; the principle stays a target until `fast`. |
| XIV. Agent-generated change meets the same bar (NON-NEGOTIABLE) | Yes | Every increment is a local commit with the quickest relevant tests green; the full gates run before the convergence commit; the hand runs the demo as the actor. |
| IV, VI, VII, VIII, XI, XII, XV | No | No domain code, contract, event, release or type changes. |

**Gate result:** no violation; *Complexity Tracking* stays empty.

## Project Structure

### Documentation (this slice)

```text
specs/001-faster-slipwai/slices/S00-run-path/
├── plan.md              # this file
├── research.md          # R1–R9, every statement cited
├── data-model.md        # the records the slice writes and the one transition it makes
├── quickstart.md        # how to prove each AC from this checkout
├── tasks.md             # written by drive-tasks
├── demo-log.md          # written by drive-hand at the demo
└── benchmark.json       # one entry per stage
```

No `contracts/`: the slice exposes no interface to a user or another system.

### Source code (repository root — the one deployable, `slipwai-graph`, kind `tool`, path `.`)

```text
tests/
├── test_cruise_runner.py     # `cruise()` helper → gains the shared child-environment helper (R3 site 1)
├── test_cruise_stop_hook.py  # `hook()` → calls the shared helper instead of its own copy (R3 site 5)
├── test_cruise_tell.py       # the `run` Popen (R3 site 2)
├── test_cruise_watch.py      # the `watch --minutes 1` run (R3 site 3)
└── test_cruise_start.py      # two in-process `patch.dict` calls, `clear=True` (R3 site 4)
delivery/
├── survey/running.md         # `## . (python)` section written from the run (R1)
└── baseline.json             # NOT written: the first delivery-gate run was clean, and a clean run records nothing (R4, T003)
project.json                  # convergence[axis=safety-net] → tests-pass / confirmed (R5, D11)
delivery/docs/convergence.md  # regenerated by `./slipwai adopt --refresh`, never by hand (R5)
.specify/memory/constitution.md  # V in force; XIII marker at tests-pass (R6)
```

**Structure Decision**: the code lives in the one deployable `project.json` records, `slipwai-graph` (kind
`tool`, purpose confirmed, path `.`) — there is no second service to choose against. Bounded context: one
vocabulary, the factory's own test tree and method records; by the language test there is nothing to split,
and saying so is the decision. No hexagonal layout is opened (D3; constitution IV plans none for this feature).

## Branch and integration (D12)

S00's increment commits land on `adopt-method`, on top of `5460bf9`. No `slice/S00-run-path` branch is cut, no
claim is pushed, and nothing is pushed to `origin` under any name during this slice; the local branch is the
claim and the board says so. The demo runs from `adopt-method` at the slice's tip. After acceptance, Phase 4
(adversary, mutation, both gates, the register row) runs on `adopt-method` too, and the register row's *Merged
as* names the first and last S00 commit so a person can cut them into their own pull request. Merging the
adoption to `main` and pushing `adopt-method` are a person's (`delivery/docs/adoption.md` step 6; D7).
`check-slice-scope` holds nothing on this branch (R4); its root-path defect is `S20-slice-scope-root` (D13).

## Pin

This slice changes no production code that existed before the method did: its edits are to the factory's own
tests, a survey page the repository owns, the convergence record and the constitution's journey text. The Pin
stage passes by saying so — and S00 is the one slice that stage exempts in any case, because it is the slice
that proves the run path and records what `delivery/survey/running.md` lacked.

## Phases of work (the order the tasks must keep)

1. **RED → GREEN: the child environment.** Add the shared helper in `tests/test_cruise_runner.py` and route the
   five sites through it (R3). RED first: with `CRUISE_RUNNER=1 CRUISE_ITERATION=2` in the parent, a new example
   in `test_cruise_runner.py` asserts `cruise(repo, "loop")` prints the *nobody is reading* line (the constant
   `UNREAD` already imported by `test_cruise_stop_hook.py`) — it fails today with the iteration refusal — and the
   6 red tests of R2 are observed red for the same stated reason before the change and green after.
   `tests/test_cruise_start.py:174` keeps passing by setting the marks itself (AC-S00-4). Commit.
2. **The run path.** Run `./slipwai --version`; write the `## . (python)` section of `delivery/survey/running.md`
   per `data-model.md` (command, printed line, interpreter, no port/seed/service, not tested elsewhere, who,
   date). Commit.
3. **Both gates, marks set.** `CRUISE_RUNNER=1 CRUISE_ITERATION=2 make verify`, then
   `… make -f delivery/Makefile verify`. The second records `delivery/baseline.json` only where a ratcheted
   command has findings (none did: no file, no ratchet line); confirm no `QUARANTINED` line, record the unittest
   summary and compare its `skipped=` with the baseline run (R9).
4. **Convergence writes (after the converge verdict and the after-converge gaps pass, before the demo; drive.md
   stage 9 — corrected from an earlier draft that said after acceptance).** Edit
   `project.json`'s `safety-net` row (rung `tests-pass`, provenance `confirmed`, evidence naming the two
   commands, the commit, *established by cruise iteration 2; no person has read the gate*, planned null); edit
   the constitution (V in force, XIII marker) in the same commit; commit; `./slipwai adopt --refresh` on the
   clean tree; read its report (Refreshed / Disagrees / Not wrapped) and commit what it regenerated;
   `make -f delivery/Makefile check-convergence` and `check-constitution` green. `make ratchet-tighten` is
   **not** run.

## Demo

A CLI demo (the slice has no screen; `.specify/cruise.json` `hand` is `browser`, which falls through to the
CLI for a slice without one): the hand runs the commands in `quickstart.md` in order from `adopt-method` at the
slice's tip, with the two marks set, and judges each criterion. Nothing long-lived is started, so nothing is
stopped afterwards.

## Risks and what is deliberately not done

- The first delivery-gate run could have recorded lint or typecheck findings into `delivery/baseline.json`; it
  recorded none because every command was clean (T003). A red `test` would have stopped the run, and the slice
  does not quarantine one (AC-S00-5). With no baseline file, `check-convergence`'s quarantine guard on the
  `tests-pass` row is latent (D14): the row rests on the recorded gate runs.
- `./slipwai adopt --refresh` may rewrite files beyond `convergence.md` (R5 lists what the person's refresh
  touched); every rewrite is read before it is committed, and a *Disagrees* line on the Safety net row is the
  one thing it must not say — if it does, D11's reading was wrong and the row goes back (D11, *Would reverse if*).
- Principle V coming into force binds every later slice to RED-first acceptance scenarios; the constitution
  already announced it for this feature. It is the intended consequence of D8, not a side effect.
- E8 (`slipwai migrate` here) stays a person's step (D9); `S20-slice-scope-root` reaches this repository only
  through it.

## Complexity Tracking

None — the Constitution Check has no violation to justify.
