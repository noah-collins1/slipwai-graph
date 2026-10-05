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
  build — and a deployable whose files reach outside its own path, through a relative path, another deployable's
  package or module identity (read in the tree and at the base), or a symlink, or whose reach cannot be established
  (D148). Each says its reason in one line.
- An adopted repository's `verify-scoped` runs the full gate and says this layout has no record yet.

### The printed shape (schema 1)

Added at S06's plan stage (`specs/001-faster-slipwai/slices/S06-scoped-gate/data-model.md`).
`python3 scripts/verify-scoped.py record` prints one JSON object, keys sorted, two-space indent:

```json
{
  "schema": 1,
  "deployables": { "<name>": { "kind": "service|web", "path": "<path>", "family": "<language family>",
                               "api": "<service>" } },
  "checks": {
    "<unit>": {
      "gate": "<the verify-checks prerequisite it stands for>",
      "components": ["<deployable>"],
      "inputs": { "files": ["<path>", "<directory>/"], "tools": ["<tool>"], "variables": ["<NAME>"] },
      "claims": true,
      "always": null,
      "targets": ["<make target>"]
    }
  },
  "contracts": [ { "id": "<kind>:<name>", "kind": "openapi|package|event", "owner": "<deployable>|null",
                   "paths": ["<directory>/"], "consumers": ["<deployable>"], "event": "<name, for kind event>" } ],
  "obligations": [ { "name": "<name>", "components": ["<deployable>"], "checks": ["<unit>"] } ]
}
```

- A *unit* is a `verify-checks` prerequisite, except that `lint`, `typecheck` and `test` appear once per deployable
  (`lint-<name>`); `api` is present only for a web app that names one.
- `inputs` is `null` for a check with no recorded inputs. `tools` uses the verify stamp's names (`make`, `git`,
  `python3`, `uv`, `node`, `npm`, `go`, `java`, `interpreter <path>/.venv`); `variables` are names, never values.
- `claims: false` marks a check whose file inputs never make a changed path known (it reads every file); `always` is
  the reason a check runs on every scoped run, or `null`. `claims: true` makes a path under `apps/` or `packages/`
  known only through a deployable's units and a contract's paths; a check beside them can choose itself for such a
  path but never makes it known (T027).
- `whole: true` on a unit means its gate runs whole — its recipe is not the sum of its units — and `targets` then
  names the gate, not the unit (T025). No key marks a Makefile difference: a `Makefile` that is not the factory's
  text is the full gate, charged to no check, and the record is printed as it is, with the run saying *dependency
  knowledge was incomplete* (D140 point 3).
- The obligations come from `project.json`'s optional `verification.obligations`: a list of objects with `name`
  (used once), `components` (at least two distinct `deployables` keys) and `checks` (units, or `lint`, `typecheck`,
  `test` for all their units); other keys in an entry are ignored.
- Amended by D140 (iteration 23, converge pass 4, T036/T041): the `differs` key and the named check's per-check `always`
  reason that D127 gave a rule not the factory's are retired, and `whole` keeps the one meaning above.
- Readers tolerate unknown keys. Adding a key is MINOR; renaming or removing one raises `schema` and needs a
  `migrate` catch-up note.

## Consequences

The record can never be staler than the tree it judges, and a person edits one file they already own. The merge
root and CI still run everything. Every scoped run pays a JSON read and a table join; any edit to `project.json` on
a branch costs a full gate; a check a project adds itself always runs; a Python project with several services gets
no per-service narrowing until `scripts/verify` filters by service; any change in a producing service runs every
event consumer's tests; a project whose deployables share source directly, rather than through `packages/` or a
published contract, gets the full gate on every scoped run, and every scoped run reads every deployable's listed
files once; an adopted repository gets no speedup from this slice. The `project.json` key and the
printed shape are published contracts: renaming either, or moving components to bounded contexts later, needs a
`migrate` catch-up note.
