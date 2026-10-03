# slipwai-graph — the product owner's brief

`/cruise` runs `/drive` with nobody at the wheel, and this page is the owner it decides for. The `drive-skipper`
delegate reads it before every product decision, after the specification and the constitution and before the
standing entries in `specs/<feature>/decisions.md`. Edit it at any time: the next decision reads the new text.

This file is human-owned. `/cruise` reads it and never writes it; `slipwai migrate` never rewrites it.

The full PRD this brief summarises: https://claude.ai/code/artifact/3b81e4c3-9a65-4f5b-882c-5b8ab4745d67
The analysis behind it: https://claude.ai/code/artifact/dec16150-cc8a-4487-a1ea-60f8c2895e03

## Who the actor is

A developer who ran `slipwai generate` or `slipwai adopt` and now drives or cruises a product repository with
coding agents. They never see the factory's internals; they see how long a slice takes to reach `main` and
whether the gate is still trustworthy. A second actor is the factory maintainer, who needs every change to
land as a release with its level named in `changelog.d/`. When the specification does not say, a slice serves
the first actor.

## What the product is for

Slipwai gives a developer a repository whose delivery loop produces good code without them at the wheel. The
loop is slow because it pays its gates serially, about three times per slice, over the whole repository, and
merges and finishes slices one at a time on `main` in split order. The outcome this work buys is a loop whose
time per feature grows like S·log S rather than S², with every gate still run on every change before it reaches
`main`. The one thing that would make it pointless: a faster loop that lets through what today's gate catches.

## Priorities and tie-breakers

1. The merge root and CI run the full gate on every change; a scoped gate is additive, never a replacement.
2. Fewer runs of the same check on the same content over cleverer checks: memoise and scope before optimising.
3. The generated project's loop over the factory's own convenience: a change lands under `assets/` and
   `src/slipwai/project/` first, and reaches this repository through `slipwai migrate`.
4. Smaller slices in the order the PRD gives (walks and logs, then stamps, then `-j`, then the scoped gate,
   then the merge tree); the merge tree comes after the gate it relies on is proven.
5. Deterministic over fast: a stamp or cache that could cache a false green is wrong; include tool versions
   and script hashes in its key, and never trust it in CI.
6. Measurement before behaviour: result contracts and difficulty scores are recorded in this release; model
   routing by difficulty is logged, not switched on.

## Taste

Plain words in prose and in error messages, the way `AGENTS.md` and `docs/` already read. A gate says what it
checked and why it failed in one line a person can act on. A new setting has a documented default and one
sentence on when to change it. No new dependency where a stdlib or an existing script will do. Scripts stay
within `make check-structure`'s budgets: split along the structure rather than growing one file.

## Out of scope

- Changing what the gate, the adversary or mutation testing check at the merge root and in CI.
- Replacing the harness, Spec Kit, or the ladder's stages; the organisational parts of the coordination-tax
  paper (decision tiers, the PM model, the inventory-size rule).
- Switching model routing on. Logging the tier it would choose is in scope; choosing is not.
- Making this repository's own unittest suite fast beyond what the general changes give it.
- Any MAJOR change: no axis, option, CLI flag or `schemaVersion` is removed or renamed.

## Always ask a person

- Anything that changes what the merge root or CI checks, or removes a check anywhere.
- Deleting or renaming a generated file an existing project may rely on, without a `migrate` catch-up note.
- Raising `VERSION` to a MAJOR.
- Accepting the strategy ADR under `delivery/docs/adr/`.
- Splitting `model.yaml` into per-slice files (decision 3 in the PRD) rather than adding a sidecar index.
