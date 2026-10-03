# 0002. Change strategy for slipwai-graph

Date: 2026-10-03

## Status

Proposed

Drafted by `drive-bosun` during `/cruise` iteration 1 of `001-faster-slipwai` (decision D5 in
`specs/001-faster-slipwai/decisions.md`). Accepting a strategy is a person's act — `.specify/product-owner.md`
lists it under *Always ask a person*, and `delivery/docs/change-strategy.md` says the word `Accepted` is theirs.
Until a person writes it here, `/survey` keeps the convergence map's Strategy row at `recommended`.

## Context

`project.json` records why this work is happening: *make the delivery loop faster without weakening its
gates — tree-shaped merges, scoped and memoised gates, incremental event-model rendering, routing by
difficulty and role* (PRD: Faster Slipwai). The survey read that trigger against the five strategies the
method knows — leave it, change in place, modular monolith, strangler fig, rewrite — and recommended
*leave it*: the trigger names neither a platform that has to go, a delivery problem in the architecture, a
change problem, a capability that has to change, nor a host, so no architectural strategy follows from it.

The map says two delivery rungs have to hold before anything architectural would be worth starting, and
neither does yet: the path to production is `scripted` (a pipeline that deploys on a passing `verify` is
missing) and the safety net is `tests-exist` (a suite proven green in the gate is not recorded).

Faster Slipwai itself changes the delivery loop the factory *generates* — files under `assets/` and
`src/slipwai/project/`, which reach this repository through `slipwai migrate` — not the structure of the
factory. The constitution says as much: principle IV names no hexagonal slice in this feature, and principle
XV names no typed-boundary slice. The repository is one Python tool at its root, held by
`make check-structure` to a declared import direction, no cycles and per-module budgets.

The owner brief rules out any MAJOR change and replacing the harness, Spec Kit or the ladder's stages.

## Decision

Strategy: leave-it

Leave the architecture of `slipwai-graph` where it is: one Python tool at the repository root, its layout
(`src/slipwai/`, `assets/`, `delivery/`, `tests/`) and its import gate as they stand. No capability is moved
to a new home, no routing seam is introduced, no retirement ledger is opened and no rewrite is started.

The work the trigger asks for proceeds as delivery slices — the memoised and scoped gate, the merge tree,
incremental rendering, result contracts and difficulty scores — on the convergence map's rows, each landing
first in what the factory generates and arriving here through `slipwai migrate`.

## Consequences

- *Leave it* is a decision like any other and finishes the Strategy axis: once this ADR is accepted the row
  moves to `decided`, and with no retirement ledger to empty, to `done`.
- `/strangle` will not move a capability, because the line above does not say `strangler-fig`.
- The programme the survey derived still applies where it is not architectural: the quick wins are judged
  one by one (decision D6 reads each), and the `tooling` step — `pip-audit` as an `audit` command — is one
  tool, one slice, over time, green through the ratchet before it is recorded.
- The two delivery preconditions the map names — a pipeline that deploys on a passing `verify`, a green suite
  in the gate — remain the rungs to climb, and nothing about this choice makes them cheaper or dearer.
- Should the trigger change — a platform that has to go, a capability that has to serve from somewhere
  else — the answer is a new ADR that supersedes this one and links back here, never an edit of this page
  once it is accepted.
- While this ADR is `Proposed`, the run works on the recommendation as a stated assumption (D5); a person
  who disagrees writes a different strategy into a superseding ADR, and `/survey` follows it.
