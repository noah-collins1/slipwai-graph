# 0006. Delegate result contracts are kept as JSON blocks in per-slice, append-only `hand-backs.md` files

Date: 2026-10-05

## Status

Proposed

Drafted by `/cruise` iteration 23 of `001-faster-slipwai`, at the pre-planning gaps stage of `S14-result-contract`
(decision D134 in `specs/001-faster-slipwai/decisions.md`). The run never accepts its own architecture decision; the
word `Accepted` here is a person's.

## Context

FR-017 requires every delegate to end its hand-back with a `result-contract` block that `check-decisions` holds, "of
the shape in the PRD", and no session can open the PRD. FR-032, FR-018 and FR-036 make the block an input to revert
(`S28-ratify-revert`), to difficulty joins (`S15-difficulty-score`) and to classifier calibration
(`S30-route-classifier`); `S34a-evidence-records` reads it too. D129 runs slices concurrently, each writing only its
own folder. Constitution VIII treats a persisted schema as a contract, and XIV forbids an agent inventing a persisted
field, so the shape is fixed before anything is planned.

## Decision

- The dispatching session — never the delegate — appends each delegate's block verbatim to
  `specs/<feature>/slices/<id>/hand-backs.md`, or to `specs/<feature>/hand-backs.md` for feature-level stages. Inside a
  `drive-slice` worktree, that delegate is the dispatching session for its own sub-delegates.
- Each entry opens `## <UTC ISO-8601 time> — <delegate type> — <stage>`, followed by the block, or by one line
  `- **Missing:** <reason>` where no valid block came back (D136: one continuation asks for it; the stage is never re-run
  and the host never writes a block for a delegate). Entries are only appended.
- An entry's heading may carry a fourth part, ` — <started>`: the `started` instant of the `benchmark.json` entry the
  entry answers (D160). The verbs take it as `--started`, defaulting to the stage's one open entry and refusing rather
  than guessing; coverage counts an entry for a stage only when its `started` is the stage's own. A heading without it
  answers no benchmark entry.
- A retry is the same block or reason for the same type, stage and `started` as the last such entry; the same content
  for another start of a stage is a different entry and is appended (D160).
- The body is one JSON object in a fence whose info string is `result-contract`: `contract` (integer `1`), `delegate`,
  `scope`, `status`, `contracts_changed`, `invariants_checked`, `tests`, `decisions` (`D<n>` ids the work relied on),
  `assumptions`, `unresolved`, `change_summary`, `files_changed` (repository-relative paths, D135) and
  `difficulty_observed` (`{"score": 1–5, "reason": "…"}`), every one required. `status` is drawn from one set per
  delegate type, keeping the verdict words people already act on.
- Readers ignore unknown keys. A block whose `contract` is greater than 1 is passed with a note. Changes are additive
  only; removing or retyping a field needs `contract: 2` and a reader that maps version 1 forward.
- The shape is written once for a generated project's readers, on its `docs/result-contract.md` (S14).
- `check-decisions` refuses a malformed block, a malformed heading and an entry with neither a block nor a `Missing:`
  line, each on one line naming the file, the entry and the field. It does not refuse a slice with no `hand-backs.md`;
  a missing entry is a converge finding, not a gate failure (D60, D65).

## Consequences

- Every hand-back is in git, readable with the standard library, and a gate in CI can hold it.
- Concurrent slices never contend for a file.
- Every field is now permanent: a wrong name or type costs a schema version and a reader that translates forward.
- The per-type status table has to grow whenever a delegate type is added; until then that type's blocks fail the gate.
- The dispatching session validates every block before appending it, which costs a round trip when a delegate returns
  a malformed one.
- `hand-backs.md` grows with every dispatch.
- A continuation for a missed block is written at any later time and still answers the stage it names, because the
  record carries the stage's start and no time window has to contain it; an entry that names no start covers nothing
  (D160).
