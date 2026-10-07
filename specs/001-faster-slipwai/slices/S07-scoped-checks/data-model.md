# Data model: S07-scoped-checks

Nothing is stored. Two things are derived each run: the four checks' entries in S06's record (ADR 0004, schema 1,
unchanged shape), and `check-ux-gates`' scope.

## The four rows (`verify_scoped/table.py`)

`Row(files, tools=(), variables=(), claims=True, always=None)` as S06 defines it. `tools` stays empty: `make` and
`python3` are every row's (`record.ALWAYS_TOOLS`).

| Check | `files` | Derived at record time (`methods.py`) |
|---|---|---|
| `check-agents` | `.specify/integration.json`, `.specify/models.json`, `.specify/drive.json`, `.specify/cruise.json`, `skills/`, `commands/`, `agents/`, `AGENTS.md` | per installed integration: `skillsDir/`, `commandsDir/`, `agentFile.dir/`, `contextFile`, `hooks.projection.where` |
| `check-speckit` | `.specify/integrations/`, `.specify/presets/`, `.specify/memory/constitution.md` | every `files` key of every `.specify/integrations/*.manifest.json`; each `preset.yml`'s declared files only checked to stay inside |
| `check-extensions` | `.slipwai/extensions.json`, `AGENTS.md`, `{web}` | — |
| `check-constitution` | `specs/`, `.specify/memory/constitution.md`, `.specify/memory/.constitution-template.json`, `.specify/templates/constitution-template.md`, `.specify/presets/` | — |
| `check-ux-gates` *(widened)* | unchanged | variables gain `GITHUB_HEAD_REF`, `CI_COMMIT_REF_NAME`, `GITHUB_BASE_REF`, `CI_MERGE_REQUEST_TARGET_BRANCH_NAME` |

A directory input ends in `/`; a derived directory is written with one trailing `/`, a derived file as it is; the
entry's `files` stays sorted and de-duplicated.

## The record entry

```json
"check-speckit": {
  "gate": "check-speckit", "components": [], "targets": ["check-speckit"],
  "inputs": {"files": [".specify/integrations/", ".specify/memory/constitution.md", ".specify/presets/",
                       ".specify/scripts/bash/common.sh"],
             "tools": ["make", "python3"], "variables": []},
  "claims": true, "always": null
}
```

Where limit (i) holds, the entry is S06's no-recorded-inputs form, unchanged:
`"inputs": null, "claims": false, "always": "no recorded inputs"`. A row with `files == ()` and `always` null takes the
same form (R5).

### `with_derived(checks, root, scope, base)` — the states

| Source | Read from | Fails closed (`inputs: null`) when |
|---|---|---|
| `.specify/integrations/*.manifest.json` | working tree glob; base `ls-tree -r --name-only <base> -- .specify/integrations` + `git_show` | unreadable; not JSON; not an object; `files` not an object; a key that is empty, absolute, `~…`, has a `..` segment or a backslash |
| `.specify/presets/*/preset.yml` | same two trees | unreadable; a `file:` value (check-speckit's `PRESET_FILE_ENTRY`) failing the same path test once joined to `.specify/presets/<name>/` |
| `.specify/integration.json` | working tree; base `git_show` | present but unreadable, not JSON, not an object, or neither `installed_integrations` (a list) nor `default_integration` (a string) |
| `scripts/agents/registry.json` (beside the record's package) | the file | unreadable or not `{"harnesses": [...]}`; an installed integration's row naming a path failing the path test |

Absent files are not failures: no manifest, no `preset.yml`, no `integration.json` add nothing (the check's own
"not initialized" branches). A check whose entry is already null is left alone. A base of `None` reads the working
tree only.

## `check-ux-gates`' scope

`UX_GATES_SINCE` is read and stripped as today; then:

| Value | Where | Scope | The one line |
|---|---|---|---|
| `all` | anywhere | every preview | `check-ux-gates: UX_GATES_SINCE=all — every preview in scope` |
| any other non-empty | anywhere | changed since `git merge-base <ref> HEAD` (`-z --no-renames`, untracked `-z`) | today's lines |
| empty or unset | first border that holds (order below) | every preview | `check-ux-gates: every preview in scope — <why>` |
| empty or unset | `slice/<id>`, no border | `changes.changed(scope, base)` ∪ `changes.unpushed(scope, base).paths` | `check-ux-gates: <branch> — previews scoped to what changed since <short> (the base of `<trunk>`)[; <span note>]; UX_GATES_SINCE=all renders every preview` |

Borders, in order, with their `<why>`: a CI marker (`<NAME> is set, so this is a CI run`); `HEAD is detached` / `HEAD
names no commit`; `this is the trunk (`<trunk>`)`; `` `<branch>` is not a slice/<id> branch ``; `<branch> has no usable
base — …`; `the trunk cannot be told — …`; the stamp's `not_vouched()` words; `the project is not the repository's top`;
`Span.failure`; and any exception while loading or asking (`the slice's base could not be read (<error>)`). These are
`verify-scoped.py`'s own words where it has them.

After a scope is found, the existing "every preview" rule applies to both the ref and the default: this script, the
extension's `init.py`, `package-lock.json` or `.github/workflows/verify.yml` among the changed paths renders every
preview, with today's line naming them. The file gate over `src/` always runs.
