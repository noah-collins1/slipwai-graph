# 0008. Provisional approval's rollout mode is a value of `decide`, not a new key

Date: 2026-10-07

## Status

Proposed

Drafted by `/cruise` iteration 28 of `001-faster-slipwai`, at the pre-planning gaps stage of `S27-provisional-decisions`
(decision D196 in `specs/001-faster-slipwai/decisions.md`). The run never accepts its own architecture decision; the
word `Accepted` here is a person's.

## Context

- FR-053 requires provisional approval to roll out through three recorded modes, in a fixed order: shadow, advisory, enforced.
- FR-030 spells the enforced mode as `decide: provisional`.
- `.specify/cruise.json` is seeded once and never rewritten by `slipwai migrate` (`src/slipwai/project/seeded.py`).
- `check()` in `assets/toolkit/scripts/agents/cruise.py` reports a missing key as a finding, and `load()` raises on any finding. A new required key would therefore break every existing project.

## Decision

- `decide` gains three values: `provisional-shadow`, `provisional-advisory` and `provisional`.
- Each acts as `recommended-first` for every question that is not an always-ask item.
- The default stays `recommended-first`.
- `cruise.py --set` refuses a forward step of more than one mode. Stepping back is always allowed.
- Each move between modes is recorded as a decision entry with `Decided by: human`.

## Consequences

- Existing `cruise.json` files stay valid and keep their meaning, and no catch-up note is needed.
- Cost: provisional approval cannot be combined with `skipper-always`. Adding that later means a separate key and a second rule for what a missing key means.
- Cost: once a project sets any of the three values, removing or renaming one is a MAJOR.
- Cost: an order rule that lives in the settings command can be bypassed by editing the file by hand. The run makes up for that by parking, which a person then has to clear.
