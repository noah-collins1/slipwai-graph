# Data model: S38-factory-test-selection

Nothing is persisted. The selector reads the tree, git and the environment, prints, and runs `unittest`. Its inputs and
outputs are below.

## A module's declaration: `TEST_SELECTION`

A module-level assignment of a literal, in a `tests/test_*.py` module or a helper under `tests/`, read with `ast` and
`ast.literal_eval` — never by importing the module.

```python
TEST_SELECTION = {
    "configurations": {"backend": ["go"], "frontend": ["none"], "command": ["generate"]},   # or "every"
    "reads": ["assets/toolkit/scripts/verify-stamp.py", "tests/fixtures/forge"],
}
```

| Key | Absent means | Present means |
|---|---|---|
| `configurations` | the module generates no project | the configurations it generates: `"every"`, or axis → options |
| `reads` | it reads no file by path | each path (a file, or a directory meaning everything under it) it reads by path, besides its imports |

- **Axes** and their options: `backend` (the catalog's `backends`), `frontend` (`frontends`), `profile` (`profiles`),
  `target` (`targets`), `command` (`generate`, `adopt`). An axis the declaration does not name means *any option*:
  a module is left out for an axis only where it names that axis and the option is not in its list.
- **Held** (AC-S38-8): every axis and option exists in `catalog.json` (or is `command`'s two), every `reads` path
  exists in the tree, and the value is a literal of this shape. A declaration that fails any of these fails the test,
  and the selector treats the module as undeclared.
- **Undeclared** (no `TEST_SELECTION`, or one the selector cannot read): the module always runs.
- **Effective declaration** of a module: its own, joined with that of every helper in its import closure inside
  `tests/` (`configurations` and `reads` unioned). A module whose closure holds an undeclared helper is undeclared.
  A test holds that no declared module is voided this way, so a declaration cannot be silently dead.
- **Who may be declared**: only what a reading of the module (and its helpers) proves. A doubt leaves it undeclared.
- **Under-claims are held** (T030): a declared module whose closure calls `generate(` or `refuse(`, or whose own file runs
  `./slipwai`, and whose joined declaration names no `configurations`, fails the held-declarations check.

## The base

| Case | First line |
|---|---|
| no `SINCE` | ``compared with `main` at <short> (the trunk)`` — plus `; ` and D153's note where the trunk has unpushed commits |
| `SINCE=<ref>` resolved | ``compared with `<ref>` at <short>, named by SINCE — taken as passing on the word of whoever named it`` |

The trunk base is `check-slice-scope.merge_base().commit`, its name `.named`. A `SINCE` base is `<ref>^{commit}`,
compared with as a tree (D138 item 4); it must share history with `HEAD` (`git merge-base HEAD <commit>` answers).

## The change set

`verify_scoped.changes.changed(scope, base)` (git's `--no-renames` diff against the base with the working tree,
untracked files, deletions, both sides of a rename, and raw-byte differences), plus, for the trunk base,
`changes.unpushed(scope, base).paths` (D153). Then, separately, every file git ignores under `assets/`, `src/` or
`tests/` other than `__pycache__/`, `*.pyc`, `*.pyo`.

Two additions from converge pass 1. **The root makefiles** (`Makefile`, `GNUmakefile`, `makefile`) are compared raw with the
base — bytes, mode, presence, ignored or not — so an edit hidden by `--assume-unchanged`, `--skip-worktree` or an ignore
rule is still the root Makefile's full row (T028). **An interpreter cache under `assets/`** that git ignores never makes
the run full and carries no configuration, but joins the paths a module's `reads` match, so a module reading `assets`
runs (T026); a replay leaves the working tree, caches included, out.

## Where a run is full, and its one line

Checked in this order; the first that holds is the line, and every module runs as today's full command.

| # | Holds when | Line |
|---|---|---|
| 1 | `FACTORY_BACKENDS` set | `selection off: FACTORY_BACKENDS given` (the run is exactly what was asked) |
| 2 | `FULL` non-empty | `full: FULL=<value> given` |
| 3 | `CI`, `GITHUB_ACTIONS` or `GITLAB_CI` non-empty | `full: <NAME> is set — a CI run is the full gate` |
| 4 | `RATCHET_TIGHTEN` non-empty | `full: RATCHET_TIGHTEN is set — a tightened baseline must not lose the findings of modules that did not run` |
| 5 | a repository-locating `GIT_*` variable set (research R-7) | `full: <NAME> is set — the change set would describe another tree` |
| 6 | `HEAD` detached or unborn | `full: HEAD is not on a branch` |
| 7 | the branch is not `slice/<id>` | ``full: not a slice branch (`<name>`)`` |
| 8 | `SINCE` names no commit, or shares no history with `HEAD` | `full: SINCE=<ref> could not be resolved — <why>` |
| 9 | no `SINCE` and the trunk cannot be told | `full: the trunk cannot be told — <merge_base's bare words>` |
| 10 | the unpushed range cannot be established | `full: <Span.failure>` |
| 11 | the scoped-gate scripts cannot be loaded, or git fails | `full: the change set cannot be established — <why>` |
| 12 | a changed path broadens (below) | ``full: `<path>` changed — <rule>`` (a path from the unpushed range is worded as D153 words it) |
| 13 | an ignored file under `assets/`, `src/`, `tests/` | ``full: `<path>` is a file git ignores — what it changes cannot be established`` |

`TESTS` and `SKIP` never reach the selector: the `test` recipe runs them as today and prints
`selection off: TESTS given` or `selection off: SKIP given`.

## The path rules

Every changed path is matched by the first row that claims it.

| Path | Effect |
|---|---|
| `catalog.json`, `assets/backing-services/prune.py`, `src/**`, `Makefile`, `scripts/verify`, `requirements-dev.txt`, `pyproject.toml`, `VERSION`, `project.json`, `slipwai`, `.gitignore`, `.gitattributes`, the selector (`scripts/select-tests.py`, `scripts/select_tests/**`) and its tests, the selector's change-set scripts (`assets/toolkit/scripts/check-slice-scope.py`, `assets/toolkit/scripts/verify_scoped/**` — T029), a `test*.py` or `__init__.py` under a `tests/` sub-package `discover` would import (*a test module the selector cannot name* — T027) | **full**, with the row's rule (*the catalog*, *the pruner*, *the generator*, *the root Makefile*, …: *its effect cannot be established*) |
| `tests/test_<m>.py` | module `m` runs, and every module importing it |
| `tests/<helper>.py` | every module whose import closure holds it |
| `tests/**` (anything else) | the modules whose `reads` name it |
| `assets/languages/<b>/**`, `assets/backing-services/<b>/**` — `<b>` a catalog backend or family | `backend` ∈ that backend or family's backends; plus R-5's cross-read rows (`typescript/biome/**`, `typescript/app/package.json` → also `frontend` `react-vite`; `java/build/**` → also `command` `adopt`; and `assets/frontends/react-vite/app/package.json` → also `backend` `typescript`, which `biome.py` reads for the Biome version — found by the held scan at T007). A pair reached only by a cross-read never narrows |
| `assets/backing-services/keycloak/**`, `sql/**`, `docker-compose.yml`, `env.example` | every configuration (any other entry there is **full** — *no rule claims it*) |
| `assets/frontends/<f>/**` | `frontend` = `f` |
| `assets/profiles/<p>/**` | `profile` = `p` |
| `assets/targets/<t>/**` | `target` = `t` |
| `assets/toolkit/**` | every configuration |
| `assets/adoption/**` | `command` = `adopt` |
| `assets/**` (anything else, a name no catalog row knows included) | **full** — *no rule claims it* |
| `docs/**`, `specs/**`, `delivery/**`, `.github/**`, `.specify/**`, `.claude/**`, `changelog.d/**`, `coordination-lean/**`, `scripts/**` (the rows above aside), `README.md`, `CHANGELOG.md`, `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `SECURITY.md`, `LICENSE`, `NOTICE` | the modules whose `reads` name it |
| anything else | **full** — *no rule claims it* |

Every path under `assets/` also selects the modules whose `reads` name it. A path's configurations select a declared
module whose `configurations` admits any of them (*every* admits all; absent admits none).

## The selection

For each module, in name order: **runs** — with the first reason that selected it (*undeclared*, ``tests/test_x.py`
changed``, ``reads `<path>` ``, *reads the go configuration*, ``imports `<helper>` ``) — or **skipped**, with one
reason: *reads no `<options>` configuration* where configurations changed and none reached it, *reads none of the
changed files* otherwise, joined where both apply.

**Narrowing** (AC-S38-9): let *B* be the backends that changed backend-asset paths name. A running module is narrowed
to *B* when every reason it was selected for is a backend-asset path. Narrowed modules run in one `unittest` process
with `FACTORY_BACKENDS=<B, comma-separated>`; the rest run in another with `FACTORY_BACKENDS` unset. Both run, and the
run fails when either fails. No other change to how a test runs.

## What a run prints

```text
compared with `adopt-method` at 8072724, named by SINCE — taken as passing on the word of whoever named it
skipped test_add_service: reads no go configuration
…
narrowed test_matrix: backend go only (java-quarkus, java-spring, python, typescript unaffected)
selected 41 of 318 modules against `adopt-method` at 8072724
<unittest output>
selected 41 of 318 modules against `adopt-method` at 8072724
```

A full run prints its one line, then today's output. The **dry run** (`python3 -B scripts/select-tests.py --dry-run`)
prints the same lines up to the summary and runs nothing; with `--replay <base>..<tip>` it takes the change set from
that range of commits instead of the working tree and the branch rules, and selects over the current tree's
declarations (AC-S38-15).
