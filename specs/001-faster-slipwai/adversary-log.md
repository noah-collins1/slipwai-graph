# Adversary log — 001-faster-slipwai

One row per finished slice, in the shape `delivery/commands/adversary.md` gives: the trigger table first, then what
was spawned or why nothing was, then the findings. A skip is a reported decision, never silence, and
`make -f delivery/Makefile check-decisions` holds every done slice to a row here.

## S00 · 2108b81 · 2026-10-03

Slice `S00-run-path`. The heading carries the id the checker reads — `check-decisions.py` and `benchmark.py` take a
slice's id as the `[A-Za-z]+\d+` prefix of the register row's first cell, so a slug after the number is not part of
it (D17; the factory fix rides in `S20`). Every later row here is headed the same way.

| Trigger | Status | Evidence |
|---|---|---|
| driving adapter (HTTP route, CLI command, queue consumer) | not present | `git diff --stat 5460bf9..2108b81`: no file under `src/slipwai/`, `assets/` or `scripts/` changed; the CLI (`./slipwai`, `scripts/agents/cruise.py`) is untouched — the slice ran `./slipwai --version` and recorded it (`delivery/survey/running.md`) |
| driven adapter or the provider types behind one | not present | the diff is five test files under `tests/` (the child environment a test hands `cruise.py`), a survey page, one `project.json` convergence row, the constitution's journey text, and the slice's own artifacts under `specs/` |
| authorisation decision (who can reach one that already exists) | not present | no authorisation exists in this tool and none was added |
| concurrency, idempotency, ordering, retention, or time | not present | the one behavioural change is in test fixtures (`outside_a_run()` in `tests/test_cruise_runner.py`), which makes no claim about any of these; `cruise.py start`'s refusal inside an iteration is unchanged and still proven by `tests/test_cruise_start.py:174` |

Not the slice that closes the feature's split (21 slices remain); `--full` not passed. **Skipped**: no trigger
`widened`; the slice's boundaries are the factory's own test tree and method records, and the external surface
(`./slipwai --version`) is the smoke command the gate already exercises (`tests/test_cli.py:17`).

Spawned: none
Omitted: none — no seam widened to omit
Findings: none · `drive-adversary` not run · `seams=0` · `findings=0` · driver=cruise, iteration 2

## S20 · c1f203e · 2026-10-03

Slice `S20-slice-scope-root` (heading as D17 says, until the fix this slice ships reaches this repository through
`slipwai migrate`). Diff: `git diff f151b80 c1f203e -- assets tests changelog.d`.

| Trigger | Status | Evidence |
|---|---|---|
| driving adapter (HTTP route, CLI command, queue consumer) | widened | three generated command-line checkers change what they answer: `assets/toolkit/scripts/check-slice-scope.py` (a deployable at `.` now owns paths; registry, `.written` and `project.json` read to decide), `assets/toolkit/scripts/check-decisions.py` and `assets/toolkit/scripts/agents/benchmark.py` (register id read whole) |
| driven adapter or the provider types behind one | not present | no adapter; the checkers read files and run `git` as before |
| authorisation decision (who can reach one that already exists) | widened | `check-slice-scope` is the decision about what a slice branch may write; at a root deployable it went from refusing every path to allowing all but a named host surface (D18, D20, D21) — `check-slice-scope.py` `owning_app()`, `host_names()`, `root_owned()` |
| concurrency, idempotency, ordering, retention, or time | not present | the 12-digit migration stamp is no longer asked at a root deployable (D21), a decision recorded there with its reason; the diff makes no new claim about ordering |

Not the slice that closes the split; `--full` not passed. A pass is owed: two triggers `widened`, no prior row
covers either surface.

Spawned: seam A — what a slice branch may write at a root deployable · `drive-adversary` · claude-fable-5-1 (host model) · delegated, fresh context · manifest: `assets/toolkit/scripts/check-slice-scope.py`, `assets/toolkit/scripts/agents/registry.json`, `tests/test_slice_scope_root.py`, `tests/test_slice_scope_adopted_rules.py`, `tests/fixtures/adopt/python-worker`
Spawned: seam B — how the register id is read · `drive-adversary` · claude-fable-5-1 (host model) · delegated, fresh context · manifest: `assets/toolkit/scripts/check-decisions.py`, `assets/toolkit/scripts/agents/benchmark.py`, `tests/test_register_ids.py`, `tests/test_cruise_record.py`, `tests/test_benchmark_brackets.py`
Omitted: none
Findings: nine, none `CRITICAL` (no actor's data reaches another and no actor gains a role; the checker is a slice-branch gate and the merge root's full gate is unchanged). Every reproduction ran in a temporary repository through the checker's command line.

| # | Seam | Severity | Finding | Triage | State |
|---|---|---|---|---|---|
| A1 | A | HIGH | A path git quotes (a non-ASCII byte, a tab, a quote) is kept quoted by `changed_files()`, so `.github/workflows/déploy.yml`, `delivery/scripts/é.py` or an edited `db/migrations/0002_añadir.py` matches no host rule and passes at a root deployable (AC-S20-2, -3, -14, -15, -17) | confirmed — this slice's: under `apps/` a quoted path owns nothing and is refused | fixed `8e84546` |
| A2 | A | HIGH | Ownership is read from the slice's own `project.json`: a planted deployable whose `path` is `project.json`, `.github`, `delivery` or `Makefile` owns that path ahead of the host surface, so one edit unlocks all of it (AC-S20-2, -3, -5) | confirmed | fixed `f3da33e` |
| A3 | A | HIGH | The base is the newest of `main`, `origin/main`, `master`, `origin/master`: a `master` branch, a tag named `main` or an `origin/master` ref placed at HEAD empties the diff, and a shallow clone has *nothing to hold* | confirmed — older than this slice and the same in every generated project; changing how the base is chosen is a change to what the checker holds that S20's row defers | open → slice `S22-slice-scope-base` (D23) |
| A4 | A | MEDIUM | A committed `delivery/project.json` moves the checker's root to `delivery/`, so the delivery rule matches nothing and untracked files outside it are not seen (AC-S20-3) | confirmed | fixed `3db79e3` |
| A5 | A | LOW | A `project.json` beside the script ends the checker on a traceback at import (AC-S20-19) | confirmed — same root lookup as A4 | fixed `3db79e3` |
| A6 | A | LOW | An application's own root `specs/` directory (say RSpec's) is held to Spec Kit's feature-directory rule | declined — `specs/` is Spec Kit's in every repository the method is installed in, adopted or generated; an adoption that already had one is `adopt`'s question, not this checker's | declined |
| B1 | B | MEDIUM | A first cell with letters straight after its digits (`S03a`, and any table row starting `e2e`, `k8s`, `sha256sum`) was never an id and now is: a project green before turns red with *no row for S03a* (D19, PATCH) | confirmed | fixed `0243e01` |
| B2 | B | LOW | An unclosed record at `slices/<whole id>/` now shadows a closed one at `slices/<prefix>/` — a new warning, exit 0 | declined — an open record under the slice's own id is what the warning exists to say | declined |
| B3 | B | LOW | A trailing `.` or `-` in the cell is taken into the id, so the finding names an id nobody wrote | confirmed — same pattern as B1 | fixed `0243e01` |

Recorded as the same at `f151b80` and not this slice's: decorated register cells (links, bold) are never ids; a non-UTF-8 register or log ends `check-decisions` on a traceback; a `benchmark.json` holding `5` ends `check-benchmark` on one. Not probed: submodules, `.gitattributes`, case-insensitive filesystems.

## S21 · 9950bd2 · 2026-10-03

Slice `S21-refresh-keeps-owned-files` (heading as D17 says). Diff: `git diff c72571d 9950bd2 -- src tests changelog.d docs`.

| Trigger | Status | Evidence |
|---|---|---|
| driving adapter (HTTP route, CLI command, queue consumer) | widened | `slipwai adopt --refresh`, `--confirm` and `--decline` change what they write and what they refuse on: `src/slipwai/resurvey.py` (`writes()`, the rewrite loop, the final `stamp`), `src/slipwai/project/seeded.py`; and what they derive: `src/slipwai/strategy.py` (`with_reconciled()`, `before_of()`) |
| driven adapter or the provider types behind one | not present | no adapter; the refresh reads and writes files and runs `git status` as before |
| authorisation decision (who can reach one that already exists) | widened | `refuse_foreign` is the decision about whose uncommitted work a run may write over; the diff takes four paths out of what it protects, on the ground that the run no longer writes them (`resurvey.py` `writes()` less `kept()`; `src/slipwai/confirm.py:124` shares it) |
| concurrency, idempotency, ordering, retention, or time | widened | two claims: a second refresh straight after is a no-op with a person's row in place, and a later run does not take a project's edit for slipwai's own (`.delivery-tools/written.json`, the stamp less the kept files) |

Not the slice that closes the split; `--full` not passed. A pass is owed: three triggers `widened`; no prior row
covers the refresh (S00 skipped, S20 attacked the generated checkers).

Spawned: seam A — what a refresh, `--confirm` and `--decline` write, leave and refuse on for the four seeded files, and what slipwai records as its own · `drive-adversary` · claude-fable-5-1 (host model) · delegated, fresh context · manifest: `src/slipwai/resurvey.py`, `src/slipwai/project/seeded.py`, `src/slipwai/uncommitted.py`, `src/slipwai/confirm.py`, `src/slipwai/cli_adopt.py`, `tests/test_refresh_owned.py`, `tests/test_uncommitted.py`, `tests/test_adopt.py`
Spawned: seam B — how a refresh derives `strategy.before` from rows reconciled with a hand-edited `project.json` · `drive-adversary` · claude-fable-5-1 (host model) · delegated, fresh context · manifest: `src/slipwai/strategy.py`, `src/slipwai/convergence.py`, `src/slipwai/resurvey.py`, `src/slipwai/project/strangle_command.py`, `tests/test_refresh_strategy.py`, `tests/test_strategy.py`, `tests/test_adopt.py`
Omitted: `slipwai migrate` over the four — the diff does not change it (D26; a Parking Lot line asks for its example)
Findings: six, none `CRITICAL` (no actor's data reaches another and no actor gains a role). Every reproduction ran in a temporary repository through the CLI, against the slice's tip and against the factory at `c72571d`.

| # | Seam | Severity | Finding | Triage | State |
|---|---|---|---|---|---|
| A1 | A | MEDIUM | Where the adopted project is a subdirectory of its git repository, `changed()` (`src/slipwai/uncommitted.py`) reads `git status` paths relative to the repository's top and never matches a path the run writes: `adopt --refresh` wrote over uncommitted edits to `.specify/extensions.yml` and `delivery/commands/ground.md` with exit 0, and `.delivery-tools/written.json` stayed `{}`. The same before the slice (which also reset the four there) | confirmed; older than S21 | `open` — slice `S23-refusal-in-subdirectory` (D29) |
| F1 | B | MEDIUM | A regression: adopted `--release pipeline`, later `release.path: manual` — the person's row stays `pipeline`, and `strategy.before` and the page, which followed the record before the slice, now drop *a pipeline that deploys on a passing `verify`* | confirmed | `fixed` `3561b99` (T010, D28) |
| F2 | B | MEDIUM | `strategy.before` and the page's heading follow the recommended strategy where an Accepted ADR decides another; byte-identical before the slice | question; older | Parking Lot (D29) |
| F3 | B | LOW | A convergence row with no `provenance` ends a refresh on `KeyError`, tree left clean; same before | confirmed; older | Parking Lot (D29) |
| F4 | B | LOW | A row for an axis the factory does not know ends a refresh on `KeyError: 'target'`, tree left clean; same before | confirmed; older | Parking Lot (D29) |
| F5 | B | LOW | A Strategy row confirmed at `decided` with no ADR: the map reads `decided`, the page *Nothing is decided yet*; same before | confirmed; older | Parking Lot (D29) |

Held under attack (seam A): uncommitted and staged edits to all four across `--refresh`, `--confirm`, `--decline` and repeated runs; delete → refresh → edit → refresh; a staged rename; a symlink; mode 000; CRLF; `.specify/` removed whole; a relocated delivery directory; no git; a git worktree; a repository a pre-slice refresh had already stamped. The write set is a strict subset of the pre-slice one. (Seam B): every provenance and rung spelling, duplicated, missing and reordered rows, a `strategy` record absent or hand-edited, each `--why` trigger; a second refresh was a no-op in every case that ran, and every refusal or traceback left the tree clean.
