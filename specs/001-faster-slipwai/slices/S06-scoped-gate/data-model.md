# Data model: S06-scoped-gate

Four shapes: the obligations key a person writes in `project.json`, the baseline `verify-stamp.py` keeps under the git
directory, the factory's table inside the script, and the record the script prints (ADR 0004's contract). Nothing is
written into the working tree.

## `project.json`: `verification.obligations` (optional, the project's own)

```json
"verification": {
  "obligations": [
    { "name": "checkout", "components": ["orders", "billing"], "checks": ["test-orders", "test-billing"] }
  ]
}
```

- Missing `verification`, or `verification` without `obligations`: no obligations (the default).
- Read from `project.json` at the base (`check-slice-scope.deployables`' reading); a branch that changes
  `project.json` runs the full gate anyway.
- Well-formed: `verification` an object; `obligations` a list; each entry an object with `name` a non-empty string
  used once, `components` a list of at least two distinct names each a key of `deployables`, `checks` a non-empty
  list of names each a unit the record holds, or a gate name (`lint`, `typecheck`, `test`) meaning all its units.
  Other keys in an entry are ignored. Anything else: one line naming the entry by position and name, then
  `make verify`.
- `metadata()`, `replay`, `adopt` never write it; `migrate`'s three-way merge keeps a person's.

## The baseline: `<git-dir>/slipwai/verify-baseline-<project>.json`

`<project>` is `verify-stamp.project_name()`, the same suffix as the stamp's. Written with `write_file` (temporary
file, rename) by `verify-stamp.py record`, right after the stamp, only where the branch matches `SLICE_BRANCH`.

```json
{ "branch": "slice/S1",
  "tools": { "make": "4.4.1 [answer 0f3c…]", "node": "v22.1.0 [answer 9a2e…]", "interpreter apps/billing/.venv": "3.13.1" },
  "variables": { "UX_GATES_SINCE": "<sha256 of variable_record>", "…": "…" },
  "ignored": "<the stamp key's ignored part, as key_parts computes it>" } }
```

- `tools` is the pending note's `tools` — what the run asked at its start, the stamp's `tools` exactly.
- `variables` holds, for every name in `VARIABLES`, the hex SHA-256 of `variable_record(name)`; never a value.
- `ignored` is the stamp key's `ignored` part from the same run, as `key_parts` computes it — one digest, no path
  (D125). `verify-scoped` computes the tree's through the same function and compares; a difference is the full gate.
- Removed by `begin_full_run` (every full run of an eligible checkout that starts its checks, `-i` included) and on
  `reuse`'s ratchet path; never written under `declined()`, never off a slice branch, never by `verify-scoped`.
- Unusable when absent, not a regular file, not JSON of this shape (one without `ignored` included), or its `branch`
  is not the current branch.

## The table (`scripts/verify_scoped/table.py`)

Per gate check: the file inputs (a path, or a directory ending in `/`; `<dep>` is each deployable's path, `<web>` a
web app's, `<svc>` a service's), the tools, the variables of `VARIABLES`, whether its file inputs claim, and why it
runs always. Every check also reads `make` and `python3` (D116's *Why*). A `verify-checks` prerequisite the table does
not name has no recorded inputs.

| Check (unit) | File inputs | Tools (beyond make, python3) | Variables | Claims | Always |
|---|---|---|---|---|---|
| `lint-<n>`, `typecheck-<n>`, `test-<n>` — npm family | `<dep>/`, `package.json`, `package-lock.json`, `.nvmrc`, `biome.jsonc` | `node`, `npm` | — | yes | — |
| the same — Python | `<dep>/` | `uv`, `interpreter <dep>/.venv` | — | yes | — |
| the same — Go | `<dep>/`, `go.work`, `go.work.sum` | `go` | — | yes | — |
| the same — Java | `<dep>/` | `java` | — | yes | — |
| `check-openapi` | `<svc>/`, `packages/api-client/`, `package.json`, `package-lock.json`, `.nvmrc` | `node`, `npm`, `<svc>` | — | yes | — |
| `check-imports` | `apps/`, `packages/`, `<dep>/` | — | — | yes | — |
| `check-migrations` | `apps/`, `packages/` | `git` | — | yes | — |
| `check-styles` | `<web>/` | — | — | yes | — |
| `check-ux-gates` | `<web>/`, `.slipwai/extensions.json`, `AGENTS.md`, `package-lock.json`, `.github/workflows/verify.yml` | `git`, `node`, `npm` | `UX_GATES_REQUIRE`, `UX_GATES_SINCE`, `UX_GATES_SHARD`, `SLIPWAI_NO_INSTALL` | yes | — |
| `check-model` | `docs/event-model/`, `<dep>/` | — | — | yes | — |
| `check-drawio` | `docs/event-model/model.yaml`, `docs/event-model/model.drawio` | `node`, `npm` | — | yes | — |
| `check-decisions` | `specs/`, `docs/event-model/model.yaml`, `.slipwai/propagated` | — | — | yes | — |
| `check-benchmark` | `specs/`, `.specify/`, `docs/event-model/model.yaml`, `AGENTS.md`, `agents/`, `commands/`, `skills/` | `git` | — | yes | — |
| `check-flags` | `apps/`, `packages/`, `<dep>/`, `infra/service/flags.auto.tfvars` | `git` | — | yes | — |
| `check-deploy-role` | `infra/bootstrap/`, `infra/service/` | — | — | yes | — |
| `check-convergence` | — (only an adopted gate has it; never reached) | — | — | no | — |
| `check-python` | — | — | — | no | every check waits on it |
| `check-slice-scope` | `./` | `git` | `GITHUB_HEAD_REF`, `CI_COMMIT_REF_NAME`, `GITHUB_BASE_REF`, `CI_MERGE_REQUEST_TARGET_BRANCH_NAME` | no | it compares the whole branch with its base |
| `check-codegraph` | `./` | `git` | `CODEGRAPH_GATE_NO_SYNC` | no | it reads every tracked file |
| `check-agents`, `check-speckit`, `check-extensions`, `check-constitution` | — | — | — | no | no recorded inputs |

Reading the cells: `<dep>/` is each deployable's directory, `<web>/` each browser app's, `<svc>/` each service that
exports an OpenAPI document, `packages/<p>/` an npm package; `./` is every path. A Python unit's `.python-version`,
`pyproject.toml` and `uv.lock`, a Go unit's `go.mod` and `go.sum`, and a Java unit's `pom.xml` and
`.mvn/wrapper/maven-wrapper.properties` lie inside `<dep>/`. `check-model` also reads every path a slice of the model
names (`gwt`, `code`, a mockup's `at`), added to its file inputs per run. A row that claims makes a changed path known,
except that under `apps/` and `packages/` only a deployable's own units and a contract do: a check beside them
(`check-flags`, `check-imports`, `check-migrations`, `check-model`'s named paths, `check-openapi`) is chosen by a path
there and never makes it known, so a package nobody builds is a path the script cannot reason about (R5).

`tests/test_verify_scoped_record.py` holds the file column against each check script's reads (research R-8); the
implement stage corrects a row the scan contradicts, never by narrowing below what the script reads.

**Contracts**, derived per run:

| Contract | Changed when | Consumers | Units chosen |
|---|---|---|---|
| `openapi:<svc>` | a path under `<svc>/` | every web app whose `api` is `<svc>` | `check-openapi` (where present), each consumer's `typecheck-`, `test-` |
| `package:<p>` (`packages/<p>/package.json` exists at the base or now) | a path under `packages/<p>/` | every npm-family deployable | each consumer's `typecheck-`, `test-` |
| `event:<E>` (a slice of service X produces `E`, a slice of service Y≠X reads it — model at the base and now) | a path under X's path | Y | Y's `typecheck-`, `test-` |

**Families**: a Python unit whose recipe is only its family target runs with any sibling chosen (*shares one recipe
with `<unit>`*); a Go or Java deployable's three units are chosen together (*shares a build directory with
`<unit>`*).

## How a unit is chosen, and the reason printed

Changed paths are taken in sorted order; for each unit the first that holds wins: (1) a changed path matches its file
inputs — `<path> changed`; (2) a contract it consumes changed — `consumes <contract> (<path>)`; (3) an obligation names
it — `obligation <name> (<path>)`; (4) a family rule — `shares one recipe with <unit>` / `shares a build directory with
<unit>`; (5) a tool answers differently — `<tool> answers differently from the baseline`; (6) a variable differs —
`<NAME> differs from the baseline`. Always-run units carry their *Always* reason. Otherwise: `none of its inputs
changed`. Where every unit is chosen, the run is `make verify`.

The changed paths are the slice's own plus, as a union, every file changed on a commit between the newest the forge's
trunk carries and the base (D153): `pushed = git merge-base <base> refs/remotes/origin/<trunk>`, the paths of every
commit in `pushed..<base>` (a merge against each parent, deletions and both sides of a rename included, so a file added
and reverted still counts). They go through the whole selector, borders included; a unit chosen only by one of them says
*`<path>` changed on `<trunk>` since `origin/<trunk>` at `<short>`, which nobody's push has gated*, and the last line
adds *`<trunk>` at `<short>` has `<n>` commits `origin/<trunk>` at `<short>` does not, and every file they changed
counts as changed*. With a remote but no `origin/<trunk>`, or where the range cannot be walked, the full gate runs; with
no remote at all, the local trunk is the base (D117).

Before any of that, and before any make call, the `Makefile` is held by its text (D140, ADR 0005): `rules.json` carries
`makefile`, the sha256 of the exact text the factory wrote (a CRLF read as LF, nothing else changed). Each of these is
the full gate, and only the first that holds is printed: the root directory's own entry list names `GNUmakefile` or
`makefile`; `MAKEFILES` is set non-empty in the environment; `Makefile`'s digest differs from the file's, or `Makefile`
cannot be read, or `rules.json` has no `makefile` key. Only text that matches is then read with `make -npq`, so a
project's `Makefile` is never parsed by a scoped run. On matching text any difference the database comparison finds
(a rule's fingerprint, a variable, the export lines, the second read under the full gate's goal) is the full gate with
*dependency knowledge was incomplete*, charged to no one check; the cost is permanent for a project that edits its
`Makefile` and nothing for one that does not.

After the text and before any path is chosen (D148), a deployable that reads outside its own path is the full gate,
naming the file: `reach.py` reads every file git lists under each deployable (tracked or untracked, not ignored) for the
three ways a resolver reaches another file. (1) A path: a quoted string, or a path token in a manifest or config, that
starts with `../` and lands outside the deployable (a manifest or config is read against the deployable's root as well
as its own directory), or any path that names another deployable's path from the root; a target that is one of the
deployable's own row file inputs, or a package it consumes under `packages/`, is not a reach. (2) Another
deployable's identity, read from its manifest in the tree and at the base: its npm `name` in any file of an npm-family
deployable, its Go `module` path in any file of a Go one, its normalised `[project] name` in a Python one's
`pyproject.toml`, `uv.lock` or `requirements*.txt`, its `artifactId` in a Java one's `pom.xml` or Gradle files. (3) A
symlink whose target resolves outside the deployable. Where it cannot tell — an identity unreadable in both trees, a
file it cannot open, a link it cannot resolve, a path that climbs above the repository — the full gate runs with
*what `<path>` reads outside its path cannot be established: …*. No edge is charged to a unit.

A recipe-sum guard: where a gate check's recipe lines (from the make database) are not exactly its units' and family
targets' lines, the check runs whole under its gate name whenever any of its units is chosen, with the reason
*its recipe is not the sum of its per-deployable targets*. On the factory's own text the sum always holds.

## The rules fingerprint: `scripts/verify_scoped/rules.json` (D127, ADR 0005)

Written by the generator from the same `makefile()` output as the `Makefile`, for a stamped layout only; carried by
`generate`, `add-service` and `migrate` with the `Makefile`; never written by the project's own tools.

```json
{ "schema": 1,
  "rules": { "verify": "<sha256>", "check-drawio": "<sha256>", "lint-web": "<sha256>", "…": "…" },
  "variables": { "SHELL": "<sha256>", "VERIFY_STAMP": "<sha256>", "…": "…" } }
```

- A rule's digest is over canonical JSON `{"needs": [...], "order_only": [...], "recipe": [unexpanded lines]}`; a
  variable's over its flavour and value as written. Defined once in `scripts/verify_scoped/rules.py`
  (`from_text`, `from_database`).
- A difference charged to one named check: it always runs and claims nothing. To one unit gate: the gate runs whole.
  Anything else, or a missing or unreadable file: the full gate.

## What a run prints

All lines begin `verify-scoped: `.

- Full gate: `the full gate runs, as \`make verify\` — <reason>`; reasons: `this is the trunk (\`<name>\`)`,
  `\`<branch>\` is not a slice/<id> branch`, `HEAD is detached` (or `names no commit`), `<MARKER> is set, so this is
  a CI run`, `VERIFY_FORCE=<value>`, `make was run with -<flags>`, `slice/<id> has no usable base — <check-slice-scope's
  words>`, `the trunk cannot be told — <verify-stamp's words>`, `every check was chosen`, `a file git ignores differs
  from the baseline`, `the Makefile's \`<target>\` rule is not the one the factory wrote` or `… variable \`<name>\` …`
  (D127) (D125; followed by the stamp's hint that `git status --ignored` shows it).
- Incomplete: `dependency knowledge was incomplete for <path> — <it is project.json | it is the Makefile | it is a
  gate script under scripts/ | no deployable, contract or check claims it>`, once per path; or `dependency knowledge
  was incomplete — <why the record cannot be built>`; or `obligation <n> (\`<name>\`) in project.json's
  verification.obligations <fault>`; then the full-gate line.
- Baseline: `no usable baseline (<none yet on this branch | it was taken on <branch> | it cannot be read | <tool> did
  not answer>) — every check that reads a tool or a variable runs`, once.
- Stamp: verify-stamp's `REUSE_LINE`, unchanged.
- Each unit: `run  <unit> — <reason>` or `skip <unit> — none of its inputs changed`.
- Last: `<n> run, <m> skipped, compared with \`<trunk>\` at <short>; passed` or `…; the scoped gate did not pass —
  each failed check is named above on a line carrying ***`.

## The printed record (schema 1) — the contract ADR 0004 fixes

`python3 scripts/verify-scoped.py record [--make <make>] [--makefile <file>]` prints, with `sort_keys`, two-space
indent:

```json
{
  "schema": 1,
  "deployables": {
    "service": { "kind": "service", "path": "apps/service", "family": "typescript" },
    "web":     { "kind": "web",     "path": "apps/web",     "family": "typescript", "api": "service" }
  },
  "checks": {
    "lint-web": {
      "gate": "lint",
      "components": ["web"],
      "inputs": { "files": ["apps/web/", "biome.jsonc", "package-lock.json", "package.json", ".nvmrc"],
                  "tools": ["make", "node", "npm", "python3"], "variables": [] },
      "claims": true,
      "always": null,
      "targets": ["lint-web"]
    },
    "check-agents": { "gate": "check-agents", "components": [], "inputs": null, "claims": false,
                      "always": "no recorded inputs", "targets": ["check-agents"] }
  },
  "contracts": [
    { "id": "openapi:service", "kind": "openapi", "owner": "service", "paths": ["apps/service/"], "consumers": ["web"] },
    { "id": "package:api-client", "kind": "package", "owner": null, "paths": ["packages/api-client/"],
      "consumers": ["service", "web"] }
  ],
  "obligations": [ { "name": "checkout", "components": ["orders", "billing"], "checks": ["test-billing", "test-orders"] } ]
}
```

- `checks` holds every unit: each `verify-checks` prerequisite, with `lint`, `typecheck`, `test` replaced by their
  units; `gate` is the prerequisite it stands for; `targets` are the Make targets the scoped call names for it.
- `inputs` is `null` for a check with no recorded inputs; otherwise `files` (sorted, `/`-ended for a directory),
  `tools` (the stamp's names: `make`, `git`, `python3`, `uv`, `node`, `npm`, `go`, `java`,
  `interpreter <path>/.venv`), `variables` (names only).
- `claims` false means its files never make a changed path known. `claims` true makes a path known only where the
  table says so: under `apps/` and `packages/`, a check that is not a deployable's unit (`check-flags`, `check-imports`,
  `check-migrations`, `check-model`, `check-openapi`) never makes a path there known, only a unit or a contract does,
  so a reader that rebuilds R5 from the record must apply the same rule. `always` is the reason it runs on every scoped
  run, else `null`.
- `whole` is present, and true, on every unit of a gate (`lint`, `typecheck` or `test`) that runs whole: its recipe is
  not the sum of its units' and family targets' lines. In that case `targets` names the gate, not the unit, and
  choosing any one unit runs the gate under its own name. The key is absent otherwise.
- No key marks a Makefile difference. A `Makefile` that is not the factory's text is the full gate, charged to no
  check; the record is printed as it is, and the run says *dependency knowledge was incomplete* (D140 point 3).
- `contracts[].kind` is `openapi`, `package` or `event` (`event` carries `"event": "<name>"`, `owner` the producer).
- Readers tolerate unknown keys; a new key is MINOR, a renamed or removed one needs `schema` raised and a catch-up note.
- A record the script cannot build prints nothing on stdout, one line on stderr, and exits 1.
