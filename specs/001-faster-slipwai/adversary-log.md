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
| A3 | A | HIGH | The base is the newest of `main`, `origin/main`, `master`, `origin/master`: a `master` branch, a tag named `main` or an `origin/master` ref placed at HEAD empties the diff, and a shallow clone has *nothing to hold* | confirmed — older than this slice and the same in every generated project; changing how the base is chosen is a change to what the checker holds that S20's row defers | the minted base and the developer's checkout with no base: fixed by `S22-slice-scope-base` (D23; `f93da6d..cec171b`); at S22's slice gaps the CI half was found never to have held (every pull-request checkout is depth 1 with no trunk ref) and is placed as `S24-ci-fetches-slice-base`, waiting on a person's approval (D31) |
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
| A1 | A | MEDIUM | Where the adopted project is a subdirectory of its git repository, `changed()` (`src/slipwai/uncommitted.py`) reads `git status` paths relative to the repository's top and never matches a path the run writes: `adopt --refresh` wrote over uncommitted edits to `.specify/extensions.yml` and `delivery/commands/ground.md` with exit 0, and `.delivery-tools/written.json` stayed `{}`. The same before the slice (which also reset the four there) | confirmed; older than S21 | fixed — slice `S23-refusal-in-subdirectory`, `45184be` and `aedacf3` (D29, D36) |
| F1 | B | MEDIUM | A regression: adopted `--release pipeline`, later `release.path: manual` — the person's row stays `pipeline`, and `strategy.before` and the page, which followed the record before the slice, now drop *a pipeline that deploys on a passing `verify`* | confirmed | `fixed` `3561b99` (T010, D28) |
| F2 | B | MEDIUM | `strategy.before` and the page's heading follow the recommended strategy where an Accepted ADR decides another; byte-identical before the slice | question; older | Parking Lot (D29) |
| F3 | B | LOW | A convergence row with no `provenance` ends a refresh on `KeyError`, tree left clean; same before | confirmed; older | Parking Lot (D29) |
| F4 | B | LOW | A row for an axis the factory does not know ends a refresh on `KeyError: 'target'`, tree left clean; same before | confirmed; older | Parking Lot (D29) |
| F5 | B | LOW | A Strategy row confirmed at `decided` with no ADR: the map reads `decided`, the page *Nothing is decided yet*; same before | confirmed; older | Parking Lot (D29) |

Held under attack (seam A): uncommitted and staged edits to all four across `--refresh`, `--confirm`, `--decline` and repeated runs; delete → refresh → edit → refresh; a staged rename; a symlink; mode 000; CRLF; `.specify/` removed whole; a relocated delivery directory; no git; a git worktree; a repository a pre-slice refresh had already stamped. The write set is a strict subset of the pre-slice one. (Seam B): every provenance and rung spelling, duplicated, missing and reordered rows, a `strategy` record absent or hand-edited, each `--why` trigger; a second refresh was a no-op in every case that ran, and every refusal or traceback left the tree clean.

## S22 · bc919d6 · 2026-10-03

Slice `S22-slice-scope-base` (heading as D17 says). Diff: `git diff 7859512 bc919d6 -- assets tests changelog.d`.

| Trigger | Status | Evidence |
|---|---|---|
| driving adapter (HTTP route, CLI command, queue consumer) | widened | the gate's command line changes what it compares with, what it prints and when it exits 1: `assets/toolkit/scripts/check-slice-scope.py` (`merge_base()`, `bases_of()`, `usable()`, `target_base()`, `older_of()`, `forge_checkout()`, `check()`, `main()`); five environment variables are newly read (`GITHUB_BASE_REF`, `CI_MERGE_REQUEST_TARGET_BRANCH_NAME`, `CI`, `GITHUB_ACTIONS`, `GITLAB_CI`) |
| driven adapter or the provider types behind one | widened | names taken from the working tree's `project.json` and from the environment now reach `git` as arguments (`rev-parse --verify`, `symbolic-ref`, `check-ref-format`, `merge-base`) |
| authorisation decision (who can reach one that already exists) | widened | which commit a slice branch is held against is the decision about what the branch may touch; the diff changes who can name it (the record, the forge's target) and when the gate declines to decide (*NOT checked*, D31, D32) |
| concurrency, idempotency, ordering, retention, or time | not present | the gate reads refs once and writes nothing |

Not the slice that closes the split; `--full` not passed. A pass is owed: three triggers `widened`. S20's row
attacked the same script's ownership rules and found A3, which this slice exists to close; its base selection is new.

Spawned: seam A — every source of a name that decides the base (`ci.branch`, the two target variables, the refs they are looked up as) and the `git` commands those names reach · `drive-adversary` · claude-fable-5-1 (host model) · delegated, fresh context · manifest: `assets/toolkit/scripts/check-slice-scope.py`, `tests/test_slice_scope_base.py`, `tests/test_slice_scope_report.py`, `tests/test_slice_scope_root.py`
Spawned: seam B — the no-base answers and the developer/forge classification: exit codes, streams, and the truth of every command and sentence printed · `drive-adversary` · claude-fable-5-1 (host model) · delegated, fresh context · manifest: `assets/toolkit/scripts/check-slice-scope.py`, `tests/test_slice_scope_no_base.py`, `tests/test_slice_scope_report.py`, `tests/test_slice_scope_root.py`, `src/slipwai/project/makefile.py`
Omitted: the ownership rules of the same script — S20's row covers them and the diff does not change them; `check-migrations.py` and `check-flags.py` — not in the diff (Parking Lot); the CI checkout itself — `S24`, a person's (D31)
Findings: eleven, none `CRITICAL` (no actor's data reaches another and no actor gains a role). Every reproduction ran in a scratch repository through the command line, at `bc919d6` and against the script at `7859512`. Held: option and revision injection through a name (`--upload-pack=…`, `@{…}`, `^{…}`, `~`, `:`, `..`); stray refs at the head (a tag `main`, branches `heads/main` and `origin/main`, `refs/remotes/origin/origin/main`); packed refs; no base moved forward on related histories with an honest target; every `project.json` shape but the two below; the whole D31/D32 environment matrix; every printed command in single-branch and shallow clones with an `origin`; partial and sparse checkouts, linked worktrees, a subdirectory, `GIT_DIR`.

| # | Seam | Severity | Finding | Triage | State |
|---|---|---|---|---|---|
| B1 | B | HIGH | A slice that commits `ci.branch: zz` and pushes an unrelated-root branch `zz` makes `merge_base()` stop at the first name with a ref: in a full-history run under a CI marker with no pull-request target the gate says *NOT checked*, exit 0, where the script before the slice refused `Makefile` | confirmed — a regression; the search must go on to the remaining names (D35) | fixed — T024 |
| A1 | A | MEDIUM | With an honest pull-request target that has a ref but shares no history with `HEAD`, the branch-chosen base stands: an orphan slice that records and pushes `evil` gets *touches only what one slice may (compared with `evil` …)* | confirmed — new with the slice; a target with no common history is no base, not no opinion (D35) | fixed — T024 |
| B2 | B | HIGH | Where `git diff` itself fails (a treeless partial clone whose remote is gone) the failure reads as no changes and the gate prints the pass line, now naming a commit it never compared with | confirmed — the swallow is older than the slice, the untrue sentence is new; a diff that could not run is *could not compare*, D31's and D32's answers (D35) | fixed — T026 |
| B3 | B | MEDIUM | The printed `git fetch` interpolates a name `check-ref-format` accepts with `;`, `$`, backticks: pasted, it runs what the slice committed in `ci.branch`; an unusable value is echoed raw | confirmed — new with the slice (D35) | fixed — T027 |
| A5 | A | LOW | A `ci.branch` with newlines and escape sequences is printed verbatim: a forged *touches only what one slice may* line in the output of a refusal; a 3 MB name is echoed whole | confirmed — the same echo as B3 (D35) | fixed — T027 |
| A2 | A | MEDIUM | `ci.branch` holding a NUL or a lone surrogate ends the gate on a traceback (`ValueError`, `UnicodeEncodeError` from `subprocess`) | confirmed — AC-S22-6 says a verdict (D35) | fixed — T025 |
| A3 | A | MEDIUM | `project.json` committed as a symlink to `/dev/stdin` (root and `delivery/`) blocks the gate; to a huge file, a `MemoryError` traceback; `model.yaml` → `/dev/zero` the same | confirmed — the unbounded read is older than the slice, the working-tree read of `project.json` is new (D35) | fixed — T025 |
| B4 | B | MEDIUM | Where git cannot read the checkout at all (dubious ownership in a container job, no git) the gate exits 0 as before the slice, but now says the checkout lacks history and to set `fetch-depth: 0` — untrue there | confirmed for the sentence; the exit is older and is left (D35; Parking Lot) | fixed — T025 (the sentence) |
| A4 | A | LOW | Where the pull-request target's base wins, the line still names the recorded trunk beside the target's commit (the hand's note 2) | confirmed (D35) | fixed — T027 |
| B5 | B | LOW | With no remote named `origin` (a clone `-o upstream`, or no remote) the printed fetch cannot work | confirmed (D35) | fixed — T027 |
| B6 | B | LOW | Mid-rebase a developer's slice branch is a detached checkout with *nothing to hold* | confirmed — AC-S22-19's letter and the same before the slice | declined here — Parking Lot, with the other `current_branch()` lines (D35) |

## S23 · 44fde15 · 2026-10-03

Slice `S23-refusal-in-subdirectory` (cruise iteration 6), diff `13ec3c1..44fde15`: `src/slipwai/uncommitted.py`
(`changed()`, the refusal's message), `src/slipwai/confirm.py` (the verb a refused run is told), four test modules,
one fragment, one row of `docs/adopting.md`.

| Trigger | Status | Evidence |
|---|---|---|
| driving adapter (HTTP route, CLI command, queue consumer) | widened | `adopt --refresh`, `--confirm` and `--decline` now refuse (exit 2) in a layout where they never did, and the message changed: `src/slipwai/uncommitted.py` `refuse_foreign()`, `src/slipwai/confirm.py` (the verb names the flags given) |
| driven adapter or the provider types behind one | widened | git is the provider behind `changed()`: a second call (`git rev-parse --show-prefix`), a pathspec on `git status`, the prefix taken off each path, and `R`/`C` read in either status column |
| authorisation decision (who can reach one that already exists) | widened | `refuse_foreign` decides whose uncommitted work a run may write over; the diff changes which changes it sees — those under the project's directory, spelled from it (D36) |
| concurrency, idempotency, ordering, retention, or time | widened | `.delivery-tools/written.json` is now written in a subdirectory project, and a later run takes what it records for slipwai's own; `## S21` seam A covered the record at the top of a repository only |

Not the slice that closes the split; `--full` not passed. A pass is owed: four triggers `widened`.

Spawned: seam A — whose uncommitted work `--refresh`, `--confirm` and `--decline` may write over in a subdirectory project, and what `written.json` makes a later run take for slipwai's own · `drive-adversary` · claude-fable-5-1 (host model) · delegated, fresh context · manifest: `src/slipwai/uncommitted.py`, `src/slipwai/resurvey.py`, `src/slipwai/confirm.py`, `src/slipwai/cli_adopt.py`, `src/slipwai/project/seeded.py`, `tests/test_uncommitted_subdirectory.py`, `tests/test_uncommitted_places.py`, `tests/test_uncommitted.py`, `changelog.d/refusal-in-subdirectory.md`
Spawned: seam B — git as the provider behind `changed()`: what its two calls can be made to print, and what is then recorded and printed · `drive-adversary` · claude-fable-5-1 (host model) · delegated, fresh context · manifest: `src/slipwai/uncommitted.py`, `tests/test_uncommitted_renames.py`, `tests/test_uncommitted_places.py`, `tests/test_uncommitted_subdirectory.py`, `src/slipwai/resurvey.py`, `src/slipwai/assets.py`
Omitted: `slipwai migrate` and `add-service` — the diff changes neither (`git diff 13ec3c1..44fde15 --stat`)
Findings: eight, none `CRITICAL` (no actor's data reaches another and no actor gains a role), and **none new with the slice**: each is the same at the top of a repository at this commit, and — A2's refusal apart, which the slice makes reachable below the top as it already was at it — with the factory at `13ec3c1`. Every reproduction ran through the CLI in scratch repositories under `/tmp`, at `9e240e2` and against a worktree at `13ec3c1`. Held: a stale record across a commit, a checkout and a stash; `null` and wrong types in the record; a project moved with `git mv` after a run left its record; a poisoned `.written`; the seeded files; nothing written before the refusal; project directories named with a newline, spaces, pathspec magic, globs, control characters and bytes that are not UTF-8; hostile file names; `UU`, ` T`, a page replaced by a directory; a locked index, a read-only `.git`, a detached or unborn `HEAD`; `core.fsmonitor`, `core.ignoreCase`; a linked worktree and a submodule with the project in a subdirectory.

| # | Seam | Severity | Finding | Triage | State |
|---|---|---|---|---|---|
| A1 | A | MEDIUM | A path the run starts writing during the run — not in `.written` before it — is never checked: a person's own `.github/workflows/verify-delivery.yml` with an uncommitted line is replaced by the factory's gate at exit 0 once `ci.forge` reads `github`, and recorded as slipwai's own | confirmed; older than the slice, the same at the top | declined here — Parking Lot (D44) |
| A2 | A | MEDIUM | A run that dies after its first write and before the stamp (seen with a read-only page: `PermissionError`, exit 1) leaves 64 regenerated files with no record, and the next run refuses them as *not what slipwai left there*; with a read-only `.written`, two factory scripts are afterwards reported `owned` and drop out of the listing | confirmed; older at the top, reachable below it since the refusal works there | declined here — Parking Lot (D44) |
| A3 | A | LOW | `stamp()` digests what is on disk when the run ends, not what the run wrote: an edit saved inside the run's 0.3 s is recorded as slipwai's own (simulated in-process; not timed with a real editor) | confirmed by simulation; older design | declined here — Parking Lot (D44) |
| A4 | A | LOW | A tracked symbolic link at a written path, at `delivery/`, or at `.delivery-tools/written.json` is written through — outside the project, and outside the repository — past the refusal (also B's F2) | confirmed; older, the same at the top | declined here — Parking Lot (D44) |
| B1 | B | MEDIUM | `git status` failing in a repository git can read turns the refusal off in silence: a bad value for a `status.*`, `diff.*` or `column.status` key in the repository's config, or *dubious ownership* (a checkout mounted into a container under another uid), makes `changed()` answer `None`, and a person's edit is written over at exit 0. AC-S23-8's *as today*, and the state T010 could not make with a real repository | confirmed; older, the same at the top and at `13ec3c1` | **open** — slice `S25-refusal-when-git-cannot-answer`, behind the PRD's slices (D44, D39) |
| B2 | B | LOW | `delivery/` as a nested repository or a gitlink: git prints the directory, not its files, and an edit under it is written over | confirmed; older, the same at the top | declined here — Parking Lot (D44) |
| B3 | B | LOW | `git update-index --assume-unchanged` or `--skip-worktree` on a written path hides the edit from the refusal | confirmed; older; the person hid the file from git themselves | declined here — Parking Lot (D44) |
| B4 | B | LOW | A `written.json` of 100,000 nested brackets ends the run on a `RecursionError` traceback (`recorded()` catches `OSError` and `ValueError` only) | confirmed with a dirty tree, before any write; self-inflicted | declined here — Parking Lot (D44) |

## S01 · 4357da0 · 2026-10-03

Slice `S01-gate-walks` (cruise iteration 7), diff `ed91b20..4357da0`: `assets/toolkit/scripts/check-imports.py`
and `check-migrations.py` (one pruned listing, the count on the pass line, one read of `project.json`),
`assets/toolkit/scripts/check-codegraph.py` (the narrowed comparison on a `slice/<id>` branch and its record,
`.codegraph/gate-memory.json`), the pages that describe them, eleven test modules, one fragment.

| Trigger | Status | Evidence |
|---|---|---|
| driving adapter (HTTP route, CLI command, queue consumer) | widened | Three commands a project runs from `make verify`: both walking gates' pass lines changed and what they descend changed (`assets/toolkit/scripts/check-imports.py` `listing()`, `under()`; `assets/toolkit/scripts/check-migrations.py` `listing()`, `children()`); `check-codegraph` has a second mode with its own pass line and clauses (`assets/toolkit/scripts/check-codegraph.py` `narrowed()`, `conclude()`). No earlier row covers any of the three |
| driven adapter or the provider types behind one | widened | git behind `check-codegraph` — five new calls (`symbolic-ref`, `diff --name-only`, `ls-files -v`, `check-ignore`, `cat-file -e`); the filesystem behind all three (`os.walk` in place of `rglob`, `os.fstat` records); SQLite read without the integrity check on a narrowed run |
| authorisation decision (who can reach one that already exists) | not present | No decision about who may do what; the gates read and report |
| concurrency, idempotency, ordering, retention, or time | widened | A record kept between runs and trusted by the next (`remember()`, `remembered()`), written by rename; a two-second rule on file times (`SAFELY`); a claim that a narrowed verdict equals the whole run's |

Not the slice that closes the split; `--full` not passed. A pass is owed: three triggers `widened`.

Spawned: seam A — the two walking gates as commands over a tree and a `project.json` the attacker controls: can either pass where the earlier script failed, fail or crash where it passed, or print a count that is not what it listed · `drive-adversary` · claude-fable-5-1 (host model) · delegated, fresh context · manifest: `assets/toolkit/scripts/check-imports.py`, `assets/toolkit/scripts/check-migrations.py`, `tests/test_gate_walks.py`, `tests/test_gate_walks_target.py`, `tests/test_gate_walks_recorded.py`, `tests/test_gate_walks_counts.py`, `tests/test_gate_walks_pinned.py`, `tests/gate_audit.py`, the scripts at `ed91b20`
Spawned: seam B — `check-codegraph` on a `slice/<id>` branch: who decides the mode, the record as a surface a slice can reach, git as provider, time, two processes · `drive-adversary` · claude-fable-5-1 (host model) · delegated, fresh context · manifest: `assets/toolkit/scripts/check-codegraph.py`, `assets/toolkit/scripts/agents/code_index.py`, `tests/test_codegraph_narrowed.py`, `tests/test_codegraph_memory.py`, `tests/test_codegraph_bytes.py`, `tests/test_codegraph_said.py`, `tests/test_code_index_health.py`
Omitted: the pages that describe the gates (`src/slipwai/project/guidance.py`, `src/slipwai/project/docs.py`, the extension's `AGENTS.md` block) — prose, no boundary; `slipwai migrate` carrying the scripts — the diff does not change it, and the hand drove it in the demo
Findings: seven, none `CRITICAL` (no actor's data reaches another and no actor gains a role), all new with the slice. Every reproduction was differential — the scripts at the attacked commit (`622df56`, the trigger-table commit on top of `4357da0`; the three scripts are identical at both) beside the scripts at `ed91b20`, or a narrowed run beside the whole run on the same tree and index — in scratch projects under `/tmp`, with the tests' stand-in CLI for seam B (no daemon started). What held is listed after the table. D52 decides A1 and A4; D53 the rest.

| # | Seam | Severity | Finding | Triage | State |
|---|---|---|---|---|---|
| A1 | A | HIGH | An empty `pom.xml` committed by a slice beside its own `target/` directory — a context's domain file importing an adapter, a migration dropping a column — makes both walking gates pass, at every depth and in every language; `check-slice-scope` passes the branch, since the file is inside the slice's own service. The scripts at `ed91b20` fail both. The first off switch on these gates a slice can write | confirmed; new with the slice (D45's test) | fix: T030 (D52 — the test is the record: a deployable `project.json` records as Java, `target` at its root, `pom.xml` there) |
| A2 | A | LOW | A `contract:` marker naming a pruned directory beside the migration: `.venv` or `.git` → fails where the earlier script passed; `node_modules`, `__pycache__` → *is not a migration beside it* where it said *does not come before it* | confirmed; new (`children()` leaves pruned directories out) | fix: T031 (D53) |
| A3 | A | LOW | An unreadable `apps/` (`chmod 000`) passes `check-migrations` with `0 directory entries read` where the earlier script ended on a `PermissionError` traceback; `check-imports` passed silently before and after | confirmed; new for `check-migrations` | declined here — Parking Lot (D53) |
| A4 | A | LOW | A deployable recorded at a pruned directory (`apps/service/target` beside a `pom.xml`) is read by rules 4 and 5 and pruned by rules 1–3 and `check-migrations` | confirmed; new | fix: T030 (D52 — a recorded deployable's path is descended whatever it is called) |
| F1 | B | MEDIUM | A narrowed run reads the index's rows, builds its candidates, and `drift()` reads the rows again: a row rewritten between the reads is never hashed, the run prints *index current* where the whole run fails, and the record keeps the unverified hash, so later narrowed runs pass too | confirmed (a `git` wrapper making the write at `git diff`); new. Needs a foreign writer or an indexer fault in the window, not an ordinary edit | fix: T032 (D53) |
| F2 | B | MEDIUM | A symbolic link committed at `.codegraph/gate-memory.json.tmp` (`git add -f`): the first passing run outside CI writes the record through it, overwriting the link's target inside or outside the project, and `git status` then shows a deletion; on the trunk too after a merge. Whoever can commit to the branch can already change the gate scripts, so no role is gained | confirmed; new (the earlier script writes nothing) | fix: T033 (D53) |
| F3 | B | LOW | A FIFO at `.codegraph/gate-memory.json.tmp` blocks every passing run outside CI until it is killed | confirmed; new; a local actor only, git cannot carry a FIFO | fix: T033 (D53) |

Held, seam A: 44 import findings and 17 migration findings byte-identical over names where `Path` and string order differ; a `project.json` that is not an object, hostile `path`, `kind` and `contexts` values — the same last line as the earlier script, never a new traceback; names with newlines and non-UTF-8 bytes; FIFOs and sockets in the tree; link loops; 1900 levels of depth; the count equal to an independent enumeration on the Python, Java, Go and TypeScript skeletons (79, 130, 91, 76); the scripts run from another directory and from `<delivery>/scripts`. Older, not findings: `scripts/` linked from outside the project reads the wrong root; a path beyond the system's limit is skipped by both. Not probed: Python 3.12 and 3.13 (3.14 only on this machine), case-insensitive filesystems.

Held, seam B: every branch shape but `slice/<id>` exactly, a tag or remote ref of that name, a detached `HEAD`, `CI=0`/`false`/a space — all whole; `.gitignore` edited to un-ignore `.codegraph/`, a record committed with `git add -f`, a record naming `..` or absolute paths (membership only — nothing outside the project opened or written); `core.ignoreStat`, `core.fsmonitor`, `core.checkStat=minimal`, `core.trustctime=false`, a broken `diff.orderFile` — an edit still fails, since the stat record does not depend on git's answer; a merge in progress; sparse checkout; a future mtime; twelve simultaneous narrowed runs. Observed, not a finding: the residual D49 accepted is reachable without the clock — a byte changed through a shared memory map on tmpfs moved none of size, times or identity (the fragment now names it). Not run: a partial clone, textconv and external diff drivers, the real CodeGraph CLI (the hand drove it in the demo).
