# Implementation Plan: S07-scoped-checks — the method-file and preview checks skip what did not change on a slice branch

**Branch**: `slice/S07-scoped-checks` (local claim, cut from `adopt-method` at `063c187`; no push) | **Date**: 2026-10-07 |
**Spec**: [spec.md](../../spec.md), *Slice acceptance criteria* → `### S07-scoped-checks` (AC-S07-1 … AC-S07-14)

**Input**: FR-022 (rest), FR-023 as revised, SC-009 and SC-007 in [spec.md](../../spec.md); S07's row in
[story-split.md](../../story-split.md); D170–D173 in [decisions.md](../../decisions.md), and S06's D114–D117, D133,
D140 and ADR 0004 (`delivery/docs/adr/0004-verification-dependency-record.md`) it builds on; the gaps report
(cruise iteration 27, `drive-gaps`), whose file and line leads [research.md](research.md) re-reads. Written by cruise
iteration 27's `drive-slice` delegate (strong model, `/speckit-plan`). The optional `before_plan` hook (`characterise`)
was not run: it pins wrapped code, and this slice changes only factory code, whose tests are its pin (below).

## Summary

S06's verification-dependency record (`assets/toolkit/scripts/verify_scoped/`) has no row for `check-agents`,
`check-speckit`, `check-extensions` or `check-constitution`, so each runs on every scoped run as *no recorded inputs*.
This slice gives each a row in `table.py` (static files and directories, `variables: []`, claiming), and a new module
`verify_scoped/methods.py` works out at record time the inputs those rows cannot write down: the paths the Spec Kit
manifests and the presets' `preset.yml` list, and each installed integration's context file, hook file and projection
directories from `.specify/integration.json` with `registry.json` — from the working tree and the base both, failing
closed (`inputs: null`) on anything it cannot parse or that leaves the project (D172). A table row that declares no
file inputs becomes *no recorded inputs* (FR-023, G6). `check-ux-gates.py` gains its slice-branch default (D170,
D171): with `UX_GATES_SINCE` unset or empty, on a `slice/<id>` branch outside CI with a usable base, it scopes its
previews from S06's base — the unpushed span of the local trunk included — and says so in one line; everywhere else it
renders every preview and says why; `UX_GATES_SINCE=all` renders every preview; an explicit ref keeps today's meaning,
now read with `--no-renames` and NUL-separated names (AC-S07-12). The generated `Makefile` and `rules.json` do not
change (AC-S07-13); the scoped page, `docs/verification.md` and the script's docstring say all of it; one fragment
claims MINOR (D171) and `VERSION` stays `1.6.0.dev0`.

## The example map

| Rule | Criteria | What it says | Examples |
|---|---|---|---|
| **R1** the four have rows | AC-S07-2, -6, -10 | `table.py` gains a row each, `variables` empty, `claims` true (the default): `check-agents` — `.specify/integration.json`, `.specify/models.json`, `.specify/drive.json`, `.specify/cruise.json`, `skills/`, `commands/`, `agents/`, `AGENTS.md`; `check-speckit` — `.specify/integrations/`, `.specify/presets/`, `.specify/memory/constitution.md`; `check-extensions` — `.slipwai/extensions.json`, `AGENTS.md`, `{web}`; `check-constitution` — `specs/`, `.specify/memory/constitution.md`, `.specify/memory/.constitution-template.json`, `.specify/templates/constitution-template.md`, `.specify/presets/`. The record keeps `schema: 1` and gains no key | e1 `verify-scoped.py record` in the TS service + web starter lists the four with input objects, `claims: true`, `always: null`, `variables: []` · e2 `.specify/drive.json` changed alone: `check-agents` runs naming it, the other three skip · e3 `AGENTS.md` alone: `check-agents` and `check-extensions` (and `check-ux-gates`, `check-benchmark`, which declared it already) run · e4 `.specify/presets/x/templates/constitution-template.md`: `check-speckit` and `check-constitution` (and `check-benchmark`) run · e5 `specs/001-x/spec.md` added over the template constitution: `check-constitution` runs and fails, as `make check-constitution` does |
| **R2** paths a manifest or preset lists | AC-S07-3 | `methods.py` reads every `.specify/integrations/*.manifest.json` in the working tree and at the base; each `files` key is a file input of `check-speckit`. Each `.specify/presets/*/preset.yml` (both trees) is read with `check-speckit`'s own `PRESET_FILE_ENTRY`; what it declares lies under `.specify/presets/` already, so it only has to stay inside the project. A manifest that is not JSON, has no `files` map, cannot be read, or names a path that is absolute, has a `..` segment or a backslash, or is empty; a `preset.yml` that cannot be read or declares such a path — `check-speckit` gets `inputs: null`, `claims: false`, `always: "no recorded inputs"` (D172 limit i) | e1 a manifest listing `.specify/scripts/bash/common.sh`; that file changed: `check-speckit` runs naming it · e2 the same path listed only by the base's manifest (the branch deleted the manifest): still `check-speckit` · e3 a manifest `{`: the record shows `check-speckit` with `inputs: null`, and the run names it *no recorded inputs* · e4 a manifest listing `../outside` or `/etc/x`: the same · e5 a `preset.yml` declaring `file: ../../x`: the same |
| **R3** paths an integration names | AC-S07-4 | For each integration installed in `.specify/integration.json` (working tree and base: `installed_integrations`, else `default_integration`, as `agents/project.py`'s `selected_integrations` reads it), its `registry.json` row (`scripts/agents/registry.json`, beside the record's own scripts) gives `skillsDir`, `commandsDir`, `agentFile.dir` (directories) and `contextFile`, `hooks.projection.where` (files), each a file input of `check-agents`. An integration file that does not parse or has neither key, a registry that cannot be read, or an installed integration whose row names a path outside the project — `check-agents` gets `inputs: null` (limit i). A key the registry does not know adds nothing (the check fails on `integration.json`, which it declares) | e1 claude installed: `CLAUDE.md` changed runs `check-agents` naming it · e2 a harness with a hooks file: that file changed runs `check-agents` · e3 `.specify/integration.json` `{`: `check-agents` has no recorded inputs · e4 a row whose `skillsDir` is `~/.hermes/skills` installed: no recorded inputs |
| **R4** existence is an input | AC-S07-5, -6 | `check-extensions` declares `{web}` (every web deployable's directory), so a web app's directory added or removed — its files appear or disappear — runs it; under `apps/` it claims nothing (S06's `SHARED` rule), so it never narrows another check. `check-constitution` declares `specs/` (D172 a) | e1 `apps/web/` deleted with `project.json` unchanged: `check-extensions` runs · e2 a service's `src/` changed: `check-extensions` skipped |
| **R5** what runs because it cannot be told | AC-S07-7 | A row whose `files` is empty (and has no `always`) is *no recorded inputs*: `check_entry` gives it `inputs: null`, `claims: false`. A declared file that exists but cannot be read is already a changed path (`changes.raw_differs` returns true on `OSError`), so its readers run naming it | e1 a test table row `Row()` for a stand-in check: the record shows it with no recorded inputs and the run names that reason · e2 `chmod 000 .specify/drive.json`: `check-agents` runs naming `.specify/drive.json` |
| **R6** the four are held to what they read | AC-S07-8 | For every buildable starter shape (`test_scoped_targets.SHAPES`, with an integration and a manifest written in so the derived paths are exercised), each of the four check commands runs under an audit hook recording `open`, `os.listdir`, `os.scandir` and every `os.stat`/`os.lstat`; every path inside the project it touched lies under that shape's recorded inputs for the check, or is `project.json` or under `scripts/` (both the full gate), or is git-ignored (AC-S06-9's digest). The literal-path scan of `test_verify_scoped_record.py` now holds the four rows, and is shown to walk all four of `check-agents`' scripts. A factory test scans every claiming check's script closure for `registry.json` and `.manifest.json`: any outside the four fails unless it always runs or claims nothing (D172 limit ii) | e1 every shape: no path outside the rows · e2 teeth: drop `.specify/drive.json` from the row and e1 fails naming it · e3 the scan finds `models.py`, `drive.py`, `cruise.py` and `project.py` under `check-agents` · e4 limit ii: today only `check-slice-scope` (always) reads `registry.json` outside the four; a copy of the table marking `check-codegraph` claiming with a script reading `registry.json` fails |
| **R7** where nothing narrows | AC-S07-9, -13 | Unchanged from S06 and proven again here: a changed ignored projection is the full gate (AC-S06-9); the trunk, a CI marker and a branch not `slice/<id>` are `make verify`; `make check-<name>` is the check as the Makefile writes it; the generated `Makefile` and `rules.json` are byte-identical (the digests `test_scoped_targets` pins do not move) | e1 `test_verify_scoped_ignored`, `-borders`, `-baseline` and `test_scoped_targets` pass unchanged |
| **R8** `check-ux-gates` scopes by default on a slice branch | AC-S07-11, -1, -12 | With `UX_GATES_SINCE` stripped empty, the script asks, in order: a CI marker (`verify-stamp.py`'s `CI_MARKERS`), a detached or unborn `HEAD`, the trunk, a branch that is no `slice/<id>`, no usable base, a trunk that cannot be told, a project that is not the repository's top, a base the changed paths cannot be read against or an unpushed span that cannot be established; the first that holds prints `check-ux-gates: every preview in scope — <why>` and renders all. Otherwise the changed paths are `verify_scoped.changes.changed(scope, base)` with `changes.unpushed(scope, base).paths`, the same set the scoped gate selects on, and one line names the base: `check-ux-gates: slice/<id> — previews scoped to what changed since <short> (the base of `<trunk>`)<, and the unpushed commits of `<trunk>`>; UX_GATES_SINCE=all renders every preview`. The existing "every preview" rule (this script, the extension's `init.py`, `package-lock.json`, `verify.yml` changed) holds for the default too. `UX_GATES_SINCE=all` prints `check-ux-gates: UX_GATES_SINCE=all — every preview in scope`; any other value is a ref, as today, now with `git diff --name-only --relative -z --no-renames` and `ls-files -z`. The row's variables gain the four `check-slice-scope` reads for the base (`GITHUB_HEAD_REF`, `CI_COMMIT_REF_NAME`, `GITHUB_BASE_REF`, `CI_MERGE_REQUEST_TARGET_BRANCH_NAME`) | e1 `slice/S1`, one preview's stylesheet changed: that preview's four gates and the app's directory gates render, the line names the base · e2 `main`: every preview, *this is the trunk* · e3 `feature/x`, detached `HEAD`, `CI=1`, no `main`: every preview, each with its reason · e4 `slice/S1` with `UX_GATES_SINCE=all`: every preview, the `all` line · e5 `slice/S1` with `UX_GATES_SINCE=HEAD~1`: today's ref scoping · e6 a renamed stylesheet a preview still links by its old name: the preview renders · e7 `screens/my page.html` changed: it renders · e8 a commit on local `main` not on `origin/main` touching a stylesheet, branch cut after it: the preview renders · e9 AC-S07-1: a service `src/` change on a slice branch with a baseline: the four and `check-ux-gates` are named skipped; a web app `src/` change: `check-ux-gates` runs, its file gate runs and no preview renders |
| **R9** a stamp never vouches across the two meanings | AC-S07-11 | No change to `verify-stamp.py`: `UX_GATES_SINCE` is already in the stamp's and the baseline's variables (`variable_record`), so a default run (unset) and an `all` run have different keys; and the stamp's history digest holds `HEAD` and every ref, so a stamp never outlives the base it scoped from | e1 a green stamped `make verify` on `slice/S1` with the default; `UX_GATES_SINCE=all make verify` does not reuse it · e2 the baseline's digest for `UX_GATES_SINCE` differs between the two runs, so a scoped run selects `check-ux-gates` |
| **R10** the words and the release | AC-S07-14 | The generated scoped page (`SCOPED_PAGE` in `src/slipwai/project/scoped_targets.py`), `docs/verification.md` (gates table row for `check-ux-gates`, the scoped section) and the script's docstring say: the four are scoped by what they declare and run with *no recorded inputs* where a manifest or integration file cannot be read; `check-ux-gates` scopes from the slice's base on a slice branch outside CI, and renders every preview on the trunk and in CI; D171 rule 6's sentence (*set `UX_GATES_SINCE=all` when a change the scope cannot follow — a script or asset a preview loads, a browser upgrade — could alter a preview*); a ref named `all` is passed as `refs/heads/all`. `changelog.d/scoped-checks.md`: `MINOR`, what changed, and a standalone **Catch-up.** paragraph saying a slice branch now renders fewer previews and that `UX_GATES_SINCE=all` renders them all | e1 a generated project's gates page carries `UX_GATES_SINCE=all` and the sentence · e2 `test_changelog` passes with `VERSION` unchanged |

Every AC-S07-n is covered: 2, 6, 10 (R1); 3 (R2); 4 (R3); 5, 6 (R4); 7 (R5); 8 (R6); 9, 13 (R7); 11, 1, 12 (R8);
11 (R9); 14 (R10). AC-S07-1's first half is R1–R4 together (R8 e9 runs it end to end).

## Technical Context

**Language/Version**: Python ≥ 3.10, standard library only, for every toolkit script (`assets/toolkit/scripts/`);
Python 3 for the factory (`src/slipwai/`).
**Primary Dependencies**: none new. `methods.py` imports nothing outside `verify_scoped/`; `check-ux-gates.py` loads
`verify-stamp.py` (and through it `check-slice-scope.py`) and `verify_scoped.changes` beside itself, lazily and only
when the default is asked, exactly as `verify-scoped.py`'s `Ground` does.
**Storage**: none. The record stays derived and written nowhere (D114); no stamp, baseline or file of S07's own.
**Testing**: `unittest` under `tests/`, generated projects in temporary directories; `scoped_fixture.ShapeCase` for
runs through `make verify-scoped`; `test_ux_gates_scale`'s fake `node`/`npx` kit for `check-ux-gates`; fakes written
in the test tree, never `unittest.mock`. No test runs until the host releases the machine; then only the modules the
change touches (`make test TESTS="…"`), never the whole suite.
**Target Platform**: Linux and macOS developer machines; CI and the trunk never scope.
**Performance Goals**: SC-009 — a one-file change outside the four's inputs skips all four and renders no preview it
cannot reach. `methods.py` adds at most a handful of small JSON reads and one `git ls-tree` per record.
**Constraints**: SC-007 / constitution I and X — `verify`, `verify-checks`, `ci`, the generated `Makefile` and
`rules.json` unchanged; the merge root and CI run every check and every preview; every doubt widens (owner priority 5).
**Scale/Scope**: every shape in `test_scoped_targets.SHAPES` that has a record.

## Constitution Check

| Principle | How this plan holds it |
|---|---|
| I. A generated project owns its files and passes its own gate | `migrate` replaces only factory toolkit scripts and the generated page; the `Makefile` text and `rules.json` are byte-identical (R7), so no project's own edit is touched |
| II. Idempotency | The record is derived on every call; nothing is written; a repeated run says the same |
| III. Simplicity | One new module (`methods.py`) beside `with_named`'s precedent; no glob form, no schema key (D172 rejects (b)); the `all` value is one string compare (D171) |
| V. Acceptance-driven | Each rule above is a RED test first, in modules named under *Structure Decision* |
| VIII. Versioning | MINOR fragment (D171), `VERSION` unchanged; catch-up paragraph stands alone |
| X. CI on trunk / XIII. Fast feedback | The trunk, CI and the merge root are untouched full gates; the saving is on slice branches only |
| XIV. Agent change meets the same bar | Same gates, same tests, no exemption |

No violation; nothing to justify. Re-checked after design: unchanged.

## Structure Decision

Factory repository; the slice lives in the toolkit's scoped-gate package and `check-ux-gates.py`, with one line of
documentation in the factory's page generator.

**Factory source** *(user-visible: toolkit scripts and a generated page)*

- `assets/toolkit/scripts/verify_scoped/table.py` — four rows; `check-ux-gates`'s variables widened (R1, R4, R8).
- `assets/toolkit/scripts/verify_scoped/methods.py` *(new)* — `with_derived(checks, root, scope, base)`: R2, R3.
- `assets/toolkit/scripts/verify_scoped/record.py` — `check_entry`: an empty `files` row is no recorded inputs (R5);
  `build` calls `methods.with_derived` after `with_named`. No other change (the file is past 350 lines today, and the
  350-line rule binds `tests/`, `src/` and the root `scripts/`; nothing is added to it beyond two calls).
- `assets/toolkit/scripts/check-ux-gates.py` — the default, `all`, the `-z --no-renames` ref path, the docstring (R8).
  If the default's border logic pushes the file past ~470 lines it moves into `verify_scoped/since.py` *(new)*.
- `src/slipwai/project/scoped_targets.py` — `SCOPED_PAGE` gains the paragraph (R10).
- `docs/verification.md` — the `check-ux-gates` row and the scoped section (R10).
- `changelog.d/scoped-checks.md` *(new)* — `MINOR`.

**Tests** *(new modules, each under 350 lines)*

- `tests/test_verify_scoped_methods.py` — R1, R4, R5 against a generated project's record and `choose` (AC-S07-2, -5,
  -6, -7, -10).
- `tests/test_verify_scoped_derived.py` — R2, R3 (AC-S07-3, -4, limit i).
- `tests/test_verify_scoped_held.py` — R6 (AC-S07-8): the audit run over every shape, limit ii, the four-script walk.
  It holds its own audit wrapper (with `os.stat`), not an edit of `tests/gate_audit.py`.
- `tests/test_verify_scoped_table_held.py` — `TableHeldTest` and its helpers (`reads_of`, `covered`, `modules_of`,
  `candidates`, `NOT_AN_INPUT`, `ROOT_OWN`) **moved out of** `tests/test_verify_scoped_record.py`, which is at 350 lines
  and must change (e1's and e5's assertions on the four and on `check-ux-gates`'s variables). The move is verbatim;
  then the scan learns the base-finding modules `check-ux-gates` loads (see research R-6) and any literal the four's
  scripts name that `--check` never reads, each with its reason, failing when stale as `NOT_AN_INPUT` does.
- `tests/test_ux_gates_default.py` — R8, R9 (AC-S07-11, -12, -1's second half), on `test_ux_gates_scale`'s fake kit.
- `tests/test_verify_scoped_methods_run.py` — R8 e9 / AC-S07-1 end to end through `scoped_fixture.ShapeCase`, and R7's
  ignored-projection case on the four (AC-S07-9), if it does not fit `test_verify_scoped_methods.py`.

**Siblings in flight.** `S26-reversibility-line` owns `check-decisions.py` and the cruise briefs: untouched here.
`S43-test-declarations` writes `TEST_SELECTION` declarations into `tests/` modules and moves helpers. This plan
**edits `tests/test_verify_scoped_record.py`** (moving `TableHeldTest` out, changing two assertions) and adds new
`tests/test_verify_scoped_*.py` and `tests/test_ux_gates_default.py` modules that S43's declarations may later name. The
host should merge S07 and S43 in an order that rebases the later one over the other's change to that module.

## Pin

Factory code: no characterisation pin. Its tests are the pin — the S06 modules this slice re-runs unchanged
(`test_verify_scoped_record` less the moved class, `-choose`, `-borders`, `-ignored`, `-baseline`, `-always`,
`test_scoped_targets`, `test_ux_gates_scale`) hold today's behaviour, and every behaviour this slice changes is named
in a rule above with its RED test.

## Open questions

**Q1 (open, for the host; blocks convergence — T014, HIGH).** `tests/test_verify_scoped_contracts.py` e2 holds the
published table in `specs/001-faster-slipwai/slices/S06-scoped-gate/data-model.md` equal to `table.CHECKS` row by row.
S07 changed six rows (`check-ux-gates` variables; `check-decisions` files, from T009; the four method-file checks'
files, claims and always), so the test fails, and the page's record example still shows `check-agents` with
`inputs: null`. Writing S06's records is outside this slice's scope. Options: (a) amend S06's data-model table and
example to match `table.py` (about six lines; the test unchanged), or (b) make the test read S07's rows over S06's (more
than a path change: S07's table has other columns). Recommended: (a) — the page is the record's published contract
(ADR 0004), so it should say what the script holds, and a dated note there can say S07 amended it.

Three readings the artefacts settle, recorded in [research.md](research.md) so a later stage can disagree:
R-4 (the projection directories AC-S07-4 names are declared although git ignores them), R-7 (`make check-ux-gates` on a
slice branch takes the default, by D170 (a)), R-6 (the literal-path scan stops at the modules `check-ux-gates` loads to
find the base, and an audit run holds what it opens instead).
