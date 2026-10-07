# Research: S07-scoped-checks

Every claim below names the artefact it was read from, at `063c187`. Paths are repository-relative; the toolkit's are
under `assets/toolkit/scripts/`. No `.codegraph/` exists in this checkout, so every route was a file read or a text
search.

## R-1 What each of the four reads under `--check`

- **`check-agents`** is four commands (`src/slipwai/project/agent_targets.py:27-29`): `agents/project.py --check`,
  `agents/models.py --check`, `agents/drive.py --check`, `agents/cruise.py --check`.
  - `project.py`: `registry.json` beside it (`:41`, gate script); `.specify/integration.json` (`selected_integrations`,
    `:109-122`); `AGENTS.md` (`:42`, `sync_context` `:381-400`, `copy_context_blocks` `:427-434`); `skills/`,
    `commands/`, `agents/` under `DELIVERY` (the project root in a generated project, `:37`); per installed harness its
    `skillsDir`, `commandsDir`, `agentFile.dir` (existence, `unprojected` `:530-540`; contents, `project` `:543-586`),
    `contextFile` (`:395`) and `hooks.projection.where` (`hook_file` `:481-520`); `project.json` (`project_capabilities`
    `:589-610`, a printed report only, and a full-gate input anyway); `.specify/models.json` through `agent_model`
    (`:244-257`).
  - `models.py`: `.specify/models.json`, `.specify/integration.json`, `registry.json` (`:43-47`).
  - `drive.py`: `.specify/drive.json` (`:35`). `cruise.py --check`: `load()` of `.specify/cruise.json` only
    (`:90`, `:1827-1830`); its other constants (`cruise.stop`, `cruise.pid`, `specs/cruise-log.jsonl`, `.mcp.json`,
    `.codegraph/codegraph.db`, `tools`, `:91-149`) belong to `run`/`watch`/`status`, never to `--check`.
- **`check-speckit`** (`check-speckit.py`): `project.json` (profile, `:40-46`); `.specify/memory/constitution.md`
  (`:41`); `.specify/presets/` — `.registry`, each `preset.yml` and what its `file:` lines declare (`:63-102`);
  `.specify/integrations/*.manifest.json` and every path a manifest's `files` map lists (`:146-176`); `registry.json`
  for the projection directories (`:105-122`); existence of those directories (`:125-139`).
- **`check-extensions`** is `extensions/project.py --check` (`agent_targets.py:25-26`): `guidance.py`'s
  `.slipwai/extensions.json` and `AGENTS.md` (`guidance.py:23-24, 61-106`); each elected extension's `init.py`
  (gate scripts); `ready()` of `ux-gates` and `uipro` — whether a `frontend` deployable's directory exists
  (`extensions/ux-gates/init.py:169-186`, `extensions/uipro/init.py:112-114`), which reads `project.json`.
- **`check-constitution`**: `.specify/memory/constitution.md`, `.specify/memory/.constitution-template.json`,
  `.specify/templates/constitution-template.md`, `.specify/presets/*/templates/`, and whether any `specs/*/spec.md`
  exists (`workflow_started`, `check-constitution.py:82, 829-830`), per the gaps report G3/G4 and D172 item 1.
- **Environment.** None of the four reads a variable under `--check`: `SLIPWAI_INTEGRATION` is read on the write paths
  only (`guidance.py:153`, `uipro/init.py:164`) — gaps report G5. So each row's `variables` is empty (AC-S07-8).

**Decision**: R1's rows as listed in the plan, which are AC-S07-2's lists exactly. **Rationale**: the AC is the
contract and each entry is read above; `project.json`, `registry.json`, `init.py` files and everything under `scripts/`
are already the full gate (`choose.unknown`, `verify_scoped/choose.py:190-203`), so they need no row entry.
**Alternatives**: declaring `.specify/` whole for `check-agents` — rejected, it would run `check-agents` on every
constitution or template edit, against AC-S07-2's "exactly the checks declaring it".

## R-2 How the record carries what a row cannot name

`record.with_named` (`verify_scoped/record.py:430-442`) is the precedent: after the table expands, `check-model`'s
entry gains every path the model names, and becomes `inputs: None, claims: False, always: NO_INPUTS` where the model is
no mapping. `models_of` (`:389-405`) reads the working tree and `scope.git_show(base, "./" + path)` for the base.
`packages_of` (`:363-369`) lists the base with `scope.git("ls-tree", "-r", "--name-only", base, "--", dir)`.

**Decision**: a new `verify_scoped/methods.py` with `with_derived(checks, root, scope, base)`, called from `build`
right after `with_named`, using exactly those two scope calls. **Rationale**: same shape as the precedent, and
`record.py` is already 577 lines. **Alternatives**: computing them inside `table.py` (it is data only by its own
docstring, `table.py:1-13`); a new record key (D172 forbids: no key, `schema: 1`).

## R-3 What "outside the project" and "does not parse" mean (limit i)

A manifest `files` key and a preset `file:` value are joined to a root by `check-speckit` (`ROOT / relative`,
`:165`; `directory / declared`, `:96`): an absolute value replaces the root, and `..` climbs it. **Decision**: a path is
inside when it is a non-empty string, not absolute (`PurePosixPath.is_absolute`, or a leading `~`), has no `..`
segment and no backslash, and once joined (for a preset, to `.specify/presets/<name>/`) still starts under the root.
Anything else — and JSON that does not parse, a `files` that is not an object, an unreadable file (`OSError`,
`UnicodeError`, `RecursionError`) — sets the check's entry to no recorded inputs. **Rationale**: D172 limit (i) fails
closed; a check that runs costs under a second.

## R-4 The projection directories AC-S07-4 names are git-ignored

`skillsDir`/`commandsDir`/agent directories are ignored by the generated `.gitignore` (`agents/project.py:530-540`'s
docstring; `check-speckit.py:105-111`). D172's last bullet says *ignored harness projections stay out of the
committed-file inputs*, and AC-S07-4 lists *skills, commands or agents directory (from `registry.json`)* among what runs
`check-agents`. **Reading**: both hold if those directories are declared — an ignored path is never a changed path
(`changes.changed` is `git diff` + untracked-not-ignored + the base's blobs, `verify_scoped/changes.py:92-101`), so
declaring them claims nothing a git change can name, and a projection that *was* committed is a path `check-agents`
really reads; the ignored-file digest (AC-S06-9, `verify-scoped.py`'s `IGNORED` border) still makes a changed
projection the full gate. D172's sentence is read as "the digest, not a committed-file input, is what covers them",
which declaring does not weaken. The same reasoning lets a manifest list a path under `.claude/skills/`.

## R-5 The empty row (G6)

`check_entry` (`record.py:244-251`) gives any row an input object; a row with `files == ()` and no `always` would claim
nothing and never be chosen by a path, while FR-023 says a check that declares none runs. **Decision**: in
`check_entry`, a `Row` with no files and no `always` is the `row is None` case. No table row is such today
(`check-python` has `always`), so no shape's record changes; a test proves it with a stand-in row.

An unreadable declared file (AC-S07-7): `changes.raw_differs` (`changes.py:52-77`) returns `True` on `OSError`, so a
tracked file `chmod 000` is a changed path and its readers run naming it. Pinned by a test, not changed.

## R-6 The base `check-ux-gates` scopes from, and how the scans see it

- S06's base and changed set: `verify-scoped.py` builds `Ground` (`:51-62`: `verify-stamp.py` loaded beside it,
  `stamp.trunk_module()` → `check-slice-scope.py`), asks its borders in order (`:66-117`: idle, CI, forced, head,
  trunk, slice branch, base, trunk told, index), then `changes.changed(scope, base)` and
  `changes.unpushed(scope, base)` (`:233-243`). `check-slice-scope.changed_files` already uses `-z --no-renames`
  (`check-slice-scope.py:505-518`).
- **Decision**: the default reuses those same functions (loaded lazily, as `Ground` does); its borders are `ci`,
  `head`, `trunk`, `slice_branch`, `base`, `told`, plus *the project is not the repository's top* (the changed paths
  are the top's, `changes.py:95`, and `scoped()` compares paths relative to the project, `check-ux-gates.py:257-269`)
  and a `Span.failure` (`changes.py:118-151`). `idle` (`-n`/`-q`) and `forced` (`VERIFY_FORCE`) are not borders here:
  D171 rule 5 keeps `VERIFY_FORCE` to its one meaning. `index` (a sparse or `skip-worktree` index) **is** asked: a
  change git does not look at cannot scope previews either. **Rationale**: AC-S07-11 asks for *S06's base* — one
  function, never a second reading of the trunk that could disagree.
- **The scans.** `TableHeldTest` follows every module a check's script imports or names as `"*.py"`
  (`tests/test_verify_scoped_record.py:275-309`) and fails on any literal under none of the row's inputs. Loading
  `verify-stamp.py`, `check-slice-scope.py` and `verify_scoped/` pulls their literals (the stamp's cruise files,
  `docs/event-model/model.yaml`, `registry.json`) into `check-ux-gates`'s closure, though the default calls only
  base-finding functions. **Decision**: the scan gets a named list of *base modules* — loaded by a check only to find
  the slice's base and changed paths — that it does not walk for `check-ux-gates`, each with its reason, failing when
  stale; `tests/test_ux_gates_default.py` runs `check-ux-gates` on a slice branch under the same audit wrapper as R6
  and holds that every project path it opens is under its row, `project.json`, `scripts/`, or git's own directory.
  Limit (ii)'s scan uses the same list. **Alternatives**: widening `check-ux-gates`' row to those literals (it would
  run on every `specs/` change, i.e. every slice-branch run — against SC-009); computing the base with private git
  calls (a second reading of the trunk, which D117 rule 2 and AC-S07-11 rule out).

## R-7 `make check-ux-gates` on a slice branch

AC-S07-9 says `make check-<name>` always runs the check in full; D170 (a) says the default holds on *every* run on a
slice branch outside CI. **Reading**: AC-S07-9's clause is about the scoped gate never skipping a check called by name
(S06's rule: only `verify-scoped` selects); what the check itself renders is D170's, so `make check-ux-gates` on a slice
branch takes the default and says so in its one line, and `UX_GATES_SINCE=all` is the way to every preview.

## R-8 What a stamp or baseline records of the default (D170, AC-S07-11 last sentence)

`verify-stamp.py`: `UX_GATES_SINCE` is in `VARIABLES` (`:116-121`), recorded by `variable_record` as unset, empty or its
bytes (`:379-382`); the key's history digest holds `HEAD`, the branch and every ref with what it names (`:399-404`); the
baseline holds a digest per variable (`:890`). **Decision**: no change. A default run's key carries `UX_GATES_SINCE`
unset and the refs its base was computed from; an `all` run carries `all`; they never match, and a stamp from one base
is never reused after any ref moves. Proven by R9's tests.

## R-9 The table's own scan and the four

`TableHeldTest.findings` skips a check whose `inputs` is null (`:334`), so the four were never held. Once they have rows
it walks `re.findall(SCRIPT, line)` over every recipe line (`:336`), which for `check-agents` finds all four scripts
(the second recipe line holds three). Literals the scan will raise that `--check` does not read (R-1: `cruise.py`'s run
files) go into `NOT_AN_INPUT` with their reason, or the row widens where the script does read them.

## R-10 Release level

D171 item 7: a new value of an existing setting is MINOR; `VERSION` is `1.6.0.dev0` and already carries MINOR fragments
(`changelog.d/scoped-gate.md`), so nothing is raised. The fragment's catch-up paragraph is copied alone by `migrate`
(`changelog.d/README.md`).
