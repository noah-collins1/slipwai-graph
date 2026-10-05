# 0004. The verification-dependency record is derived when the scoped gate runs

Date: 2026-10-05

## Status

Proposed

Drafted by `/cruise` iteration 17 of `001-faster-slipwai`, at the gaps stage of `S06-scoped-gate` (decisions D114
and D115 in `specs/001-faster-slipwai/decisions.md`). The plan extends it with the printed record's exact shape.
The run never accepts its own architecture decision; the word `Accepted` here is a person's.

## Context

FR-006 asks `make verify-scoped` to choose, on a `slice/<id>` branch, which of the gate's checks to run from a
record of each check's inputs — files, contract versions, tools, configuration, environment variables — and the
components it asserts, consumers of a changed contract and multi-component integration obligations included, and
to broaden up to the full gate wherever the record cannot say what is affected. `S07-scoped-checks` adds the four
method-file checks' inputs to the record; `S34`–`S36` read input fingerprints and obligations through it.

A generated project's Makefile is written from `project.json` only at `generate`, `add-service`, `add-frontend` and
`migrate`; a person edits `project.json` at any time with nothing regenerated (D104 answered the same problem by
reading `project.json` when the gate runs). `lint`, `typecheck` and `test` are each one target merging every
deployable's recipe, and a generated project has no contract-test target of its own. An adopted repository's gate
wraps each application's recorded commands through `ratchet.py` and has no `verify-checks`.

## Decision

- The record is never stored. The toolkit script that implements `verify-scoped` carries the factory's table of
  what each check reads, joins it with `project.json`'s `deployables` and declared obligations each time it runs,
  and can print the result as JSON. That printed shape is the contract its readers use.
- A component is a deployable in `project.json`. Per-deployable `lint-<name>`, `typecheck-<name>` and
  `test-<name>` targets, built from each deployable's own recipe lines, are reached only by `verify-scoped`; a
  recipe line that names no deployable's path is shared by its family and runs once if any member is selected.
  `verify`'s prerequisites, recipes and output are unchanged.
- A generated project's contracts are three: a service's committed OpenAPI document (consumed by every web app
  whose `api` names the service), a shared package under `packages/` (consumed by every npm-family deployable), and
  an event a `model.yaml` slice in one service produces and another service's slice `reads`. A consumer's contract
  tests are its typecheck and test.
- Integration obligations are declared in `project.json` under one optional key (name, components, checks), which
  `migrate` merges as the project's own.
- A change on the branch to `project.json`, to the script or to any other gate script runs the full gate, and so
  does a malformed or unresolvable obligation, a file no deployable or check claims, or a record the script cannot
  build. Each says its reason in one line.
- An adopted repository's `verify-scoped` runs the full gate and says this layout has no record yet.

## Consequences

The record can never be staler than the tree it judges, and a person edits one file they already own. The merge
root and CI still run everything. Every scoped run pays a JSON read and a table join; any edit to `project.json` on
a branch costs a full gate; a check a project adds itself always runs; a Python project with several services gets
no per-service narrowing until `scripts/verify` filters by service; any change in a producing service runs every
event consumer's tests; an adopted repository gets no speedup from this slice. The `project.json` key and the
printed shape are published contracts: renaming either, or moving components to bounded contexts later, needs a
`migrate` catch-up note.
