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
| A1 | A | HIGH | An empty `pom.xml` committed by a slice beside its own `target/` directory — a context's domain file importing an adapter, a migration dropping a column — makes both walking gates pass, at every depth and in every language; `check-slice-scope` passes the branch, since the file is inside the slice's own service. The scripts at `ed91b20` fail both. The first off switch on these gates a slice can write | confirmed; new with the slice (D45's test) | fixed `f592476` (T030, D52 — the test is the record: a deployable `project.json` records as Java, `target` at its root, `pom.xml` there) |
| A2 | A | LOW | A `contract:` marker naming a pruned directory beside the migration: `.venv` or `.git` → fails where the earlier script passed; `node_modules`, `__pycache__` → *is not a migration beside it* where it said *does not come before it* | confirmed; new (`children()` leaves pruned directories out) | fixed `e18006f` (T031, D53) |
| A3 | A | LOW | An unreadable `apps/` (`chmod 000`) passes `check-migrations` with `0 directory entries read` where the earlier script ended on a `PermissionError` traceback; `check-imports` passed silently before and after | confirmed; new for `check-migrations` | open — Parking Lot (D53) |
| A4 | A | LOW | A deployable recorded at a pruned directory (`apps/service/target` beside a `pom.xml`) is read by rules 4 and 5 and pruned by rules 1–3 and `check-migrations` | confirmed; new | fixed `f592476` (T030, D52 — a recorded deployable's path is descended whatever it is called) |
| F1 | B | MEDIUM | A narrowed run reads the index's rows, builds its candidates, and `drift()` reads the rows again: a row rewritten between the reads is never hashed, the run prints *index current* where the whole run fails, and the record keeps the unverified hash, so later narrowed runs pass too | confirmed (a `git` wrapper making the write at `git diff`); new. Needs a foreign writer or an indexer fault in the window, not an ordinary edit | fixed `795cfcd` (T032, D53) |
| F2 | B | MEDIUM | A symbolic link committed at `.codegraph/gate-memory.json.tmp` (`git add -f`): the first passing run outside CI writes the record through it, overwriting the link's target inside or outside the project, and `git status` then shows a deletion; on the trunk too after a merge. Whoever can commit to the branch can already change the gate scripts, so no role is gained | confirmed; new (the earlier script writes nothing) | fixed `28eec94` (T033, D53) |
| F3 | B | LOW | A FIFO at `.codegraph/gate-memory.json.tmp` blocks every passing run outside CI until it is killed | confirmed; new; a local actor only, git cannot carry a FIFO | fixed `28eec94` (T033, D53) |

Held, seam A: 44 import findings and 17 migration findings byte-identical over names where `Path` and string order differ; a `project.json` that is not an object, hostile `path`, `kind` and `contexts` values — the same last line as the earlier script, never a new traceback; names with newlines and non-UTF-8 bytes; FIFOs and sockets in the tree; link loops; 1900 levels of depth; the count equal to an independent enumeration on the Python, Java, Go and TypeScript skeletons (79, 130, 91, 76); the scripts run from another directory and from `<delivery>/scripts`. Older, not findings: `scripts/` linked from outside the project reads the wrong root; a path beyond the system's limit is skipped by both. Not probed: Python 3.12 and 3.13 (3.14 only on this machine), case-insensitive filesystems.

Held, seam B: every branch shape but `slice/<id>` exactly, a tag or remote ref of that name, a detached `HEAD`, `CI=0`/`false`/a space — all whole; `.gitignore` edited to un-ignore `.codegraph/`, a record committed with `git add -f`, a record naming `..` or absolute paths (membership only — nothing outside the project opened or written); `core.ignoreStat`, `core.fsmonitor`, `core.checkStat=minimal`, `core.trustctime=false`, a broken `diff.orderFile` — an edit still fails, since the stat record does not depend on git's answer; a merge in progress; sparse checkout; a future mtime; twelve simultaneous narrowed runs. Observed, not a finding: the residual D49 accepted is reachable without the clock — a byte changed through a shared memory map on tmpfs moved none of size, times or identity (the fragment now names it). Not run: a partial clone, textconv and external diff drivers, the real CodeGraph CLI (the hand drove it in the demo).

## S02 · eb2a40a · 2026-10-03

Slice `S02-runner-bookkeeping` (cruise iteration 9), diff `596740f..eb2a40a`: `assets/toolkit/scripts/agents/bookkeeping.py`
(new: the stat-vouched hash record, the log as the runner left it), `assets/toolkit/scripts/agents/cruise.py`
(`control_paths()`, `controls_signature()`, `fingerprint()`, the log's and the stream's offsets, the optional
`bookkeeping` object on an entry), `assets/toolkit/scripts/agents/code_index.py` (`health()` compares through the
gate's record and renews it; `delegate_use()` from an offset), `assets/toolkit/scripts/check-decisions.py` (the
`Scope:` line and the `--scope` verb), the generated command and briefs, the pages, fourteen test modules, one
fragment, `VERSION` `1.6.0.dev0`.

| Trigger | Status | Evidence |
|---|---|---|
| driving adapter (HTTP route, CLI command, queue consumer) | widened | A new verb with two flags, `check-decisions.py --scope <id> [--feature <name>]`, and two new refusals in the gate it shares a file with (`assets/toolkit/scripts/check-decisions.py`); `code_index.py health` prints a new `detail`; the runner's log entry gains an object. No earlier row covers `check-decisions`' arguments or the runner's log |
| driven adapter or the provider types behind one | widened | The filesystem behind the runner: content read through a record of `os.fstat` facts in place of every time (`assets/toolkit/scripts/agents/bookkeeping.py` `Record.digest`), the log and the stream read from remembered offsets (`Log`, `stream_use()`); the gate's record `.codegraph/gate-memory.json` gains a second writer (`renew()` in `code_index.py`; the S01 row covers the gate's own writer) |
| authorisation decision (who can reach one that already exists) | widened | The run's one authorisation rule — an iteration never edits a gate or a control, and the runner parks on any change — now rests on the record: `controls_signature()` and `control_paths()` in `assets/toolkit/scripts/agents/cruise.py` decide what is compared and what is re-read |
| concurrency, idempotency, ordering, retention, or time | widened | Three records kept across iterations and trusted by the next; a two-second rule on file times in the runner; the session, a person and the runner all able to write the log, the stream and the controls while an iteration runs; `health()` and the gate writing one record |

Not the slice that closes the split; `--full` not passed. A pass is owed: four triggers `widened`.

Spawned: seam A — the runner's records: can an iteration change a control unseen, still or move the fingerprint falsely, or break the runner through the log and the stream · `drive-adversary` · claude-fable-5-1 (host model) · delegated, fresh context · manifest: `assets/toolkit/scripts/agents/bookkeeping.py`, `assets/toolkit/scripts/agents/cruise.py`, `assets/toolkit/scripts/agents/registry.json`, `tests/test_runner_controls.py`, `tests/test_runner_controls_park.py`, `tests/test_runner_controls_paths.py`, `tests/test_runner_fingerprint.py`, `tests/test_runner_log.py`, `tests/test_runner_log_stale.py`, `tests/test_runner_stream.py`, `tests/test_cruise_runner.py`, `tests/test_cruise_guard.py`
Spawned: seam B — `health()` as a second reader and writer of the gate's record: a wrong `current`, a verdict laundered through the runner, two writers at once · `drive-adversary` · claude-fable-5-1 (host model) · delegated, fresh context · manifest: `assets/toolkit/scripts/agents/code_index.py`, `assets/toolkit/scripts/check-codegraph.py`, `tests/test_health_narrowed.py`, `tests/test_health_memory.py`, `tests/test_health_memory_states.py`, `tests/test_code_index_health.py`, `tests/test_codegraph_memory.py`, `tests/test_codegraph_races.py`
Spawned: seam C — `check-decisions.py`: a binding entry left out of `--scope` while the gate passes, an entry not printed whole, counts that disagree, arguments abused · `drive-adversary` · claude-fable-5-1 (host model) · delegated, fresh context · manifest: `assets/toolkit/scripts/check-decisions.py`, `tests/test_decisions_scope.py`, `tests/test_decisions_scope_edges.py`, `tests/test_decisions_scope_gate.py`, `tests/test_cruise_record.py`
Omitted: the generated command and briefs (`src/slipwai/project/cruise_record.py`, `src/slipwai/project/cruise_agents.py`, `src/slipwai/project/cruise.py`) and the pages — prose, no boundary; the hand read them in a generated and an adopted project at the demo. `slipwai migrate` carrying them — the diff does not change it, and the hand drove it
Findings: eighteen, none `CRITICAL` (no actor's data reaches another and no actor gains a role; A2 came back marked so under the host's wording to the seam and is graded `HIGH` by D64 on the log's standing definition). Reproductions were differential — this tip beside `596740f`, a narrowed comparison beside the whole one — in scratch projects under `/tmp`, with the tests' stand-in CLI for seam B. What held: every way seam A tried of changing a control's bytes within an iteration parks as before (append, same-size rewrite with the time restored, `mmap`, a hard link, a file swapped for a link, the directory replaced, truncate and regrow, a registry row, `tools/`); the fingerprint moves and stands as the earlier one does; `log_bytes` and `stream_bytes` were truthful in every run; seam B found no wrong `current`, no laundering through the record over 264 fuzzed `health()` runs, and the gate's answers off a slice branch and in CI identical to `596740f`'s; seam C found the gate's output on this repository's 62 entries byte for byte the earlier checker's. Triage is D63, D64 and D65.

| # | Seam | Severity | Finding | Triage | State |
|---|---|---|---|---|---|
| A1 | A | HIGH | An iteration that edits a gate and leaves a FIFO at `.specify/cruise-stream.jsonl` hangs the runner before it compares the controls or writes the entry; the earlier runner parks naming the gate. A person who kills and restarts it gets the edited gate as the baseline | confirmed; new with the slice (`stream_use()` opens what the earlier `delegate_use()` asked `is_file()` of) | fixed `a6ac3ce` (T024, D63 — a path of the runner's own that is not a regular file is never opened, and a changed control is named first) |
| A2 | A | HIGH | A process an iteration leaves in a session of its own edits a gate after the after-signature and before the next before-signature: no park, no `controls_changed`, later iterations run against it | confirmed; older, identical at `596740f`; taken now because the slice re-decided this control (D64) | fixed `cc4c3ee` (T023 — a change between two iterations parks the run; across a park it is named, `controls_changed_between`). Residual stated in the fragment: a change made while parked is named, not parked on; one between two runner processes is not seen |
| A3 | A | MEDIUM | A FIFO at `specs/cruise-log.jsonl` hangs the runner in the append, before `park()` | confirmed; older; same class as A1 | fixed `a6ac3ce` (T024) |
| A4 | A | LOW | One line of harness output shaped like the stream's marker, or bytes that are not UTF-8, ends the runner with the iteration unrecorded | confirmed; older, identical | open — Parking Lot (D63) |
| A5 | A | LOW | A file under `specs/` whose name is not UTF-8 ends the run at the next iteration | confirmed; older, identical | open — Parking Lot (D63) |
| B1 | B | LOW | A FIFO at the stream makes `cruise.py status` block; `596740f` exits 0 | confirmed; new | fixed `a6ac3ce` (T024) |
| B2 | B | LOW | On an index whose `files` table is empty `health()` says `current` and writes a record no gate run would | confirmed; the write is new | fixed `4cd0398` (T025) |
| B3 | B | LOW | Where the comparison gives no answer, `detail` says *compared everything* | confirmed; new | fixed `4cd0398` (T025) |
| C1 | C | HIGH | A `Scope:` naming the slice by its head in another spelling (`S02-runner`, `S2`, lower case) passes the gate and is left out of `--scope` | confirmed; new | fixed `d368f3a` (T026, D63 — ids meet on their head) |
| C2 | C | HIGH | A range or two joined ids (`S01-S03`) parses as one id with a slug: passes the gate, left out for `S02` and `S03` | confirmed; new | fixed `d368f3a` (T026 — refused by the gate, carried as global by the verb) |
| C3 | C | MEDIUM | Non-ASCII digits pass the gate and meet nothing | confirmed; new | fixed `d368f3a` (T026) |
| C4 | C | MEDIUM | A `--scope` value that is not id-shaped exits 0 with every scoped entry *out of scope* | confirmed; new | fixed `5c58152` (T027 — usage, exit 2) |
| C5 | C | MEDIUM | An argument the script does not know (`--scope=S02`, `--help`) runs the gate and exits 0 with no entries | fall-through older, consequence new | fixed `5c58152` (T027) |
| C6 | C | MEDIUM | An entry under a malformed heading is dropped by the verb, or rides out glued to the one before with counts that disagree | confirmed; new | fixed `5c58152` (T027 — printed, counted, exit 1), the byte-order-mark case `2bd37b8` (T028, D65) |
| C7 | C | LOW | A second `Status:` line decides whether the entry is carried, silently for the gate | confirmed; new for the verb | fixed `d368f3a`, `2bd37b8` (the verb carries it; the gate notes it and refuses only a second `Scope:` — D65) |
| C8 | C | LOW | A separator other than a line feed before a `Scope:` label makes an earlier `Scope` line | confirmed; consequence new | fixed `d368f3a`, `2bd37b8` |
| C9 | C | LOW | A log that is not UTF-8 ends the gate and the verb on a traceback | gate older; verb new | fixed `5c58152` (T027 — one line, exit 1) |
| C10 | C | LOW | Blank lines at an entry's end are not printed; no content is lost | confirmed; new | declined (D63) |

Also closed with these: the hand's note 2 at the demo (two `Scope:` lines, T022) and the convergence pass's T020 and T021. Mutation: no command recorded for `slipwai-graph` (as every slice of this feature so far).

## S11 · dde4317 · 2026-10-03

Slice `S11-render-once` (cruise iteration 10), diff `7226c2e^..dde4317`: `assets/toolkit/scripts/event-model/render.ts`
(the entry point, now thin), `assets/toolkit/scripts/event-model/render-plan.ts` (new: which diagrams are current,
removal by name, the finished-file write, the report), `assets/toolkit/scripts/event-model/render-session.ts` (new:
the one browser session, the renderer key, the failure lines), the two pages, eight test modules, one fragment.

| Trigger | Status | Evidence |
|---|---|---|
| driving adapter (HTTP route, CLI command, queue consumer) | widened | `make model` (`assets/toolkit/scripts/event-model/render.ts`): what it draws now depends on files already on disk and on the environment (`CI`, `GITHUB_ACTIONS`, `GITLAB_CI`, `MERMAID_PUPPETEER_CONFIG`, `PNG`), it prints a new closing line and new failure lines. No earlier row covers the event-model scripts |
| driven adapter or the provider types behind one | widened | The renderer: one browser launched through the installed `puppeteer` and driven through mermaid-cli's exported function in place of one `mmdc` process per diagram (`assets/toolkit/scripts/event-model/render-session.ts`); the filesystem under `docs/event-model/`: removal by name, a temporary then a rename (`assets/toolkit/scripts/event-model/render-plan.ts`) |
| authorisation decision (who can reach one that already exists) | not present | The diff decides nothing about who may do what; the scripts run as the developer in their own tree |
| concurrency, idempotency, ordering, retention, or time | widened | A re-run is claimed idempotent (a diagram shown current is left; text written only when different); up to four draws in flight in one session; a failure leaves the earlier file; two runs in one tree; a record kept in each SVG and trusted by the next run |

Not the slice that closes the split; `--full` not passed. A pass is owed: three triggers `widened`.

Spawned: seam A — what `make model` trusts on disk and what it removes and writes: a stale, forged or torn picture reported current; removal or a write through something the run does not own · `drive-adversary` · claude-fable-5-1 (host model) · delegated, fresh context · manifest: `assets/toolkit/scripts/event-model/render-plan.ts`, `assets/toolkit/scripts/event-model/render.ts`, `assets/toolkit/scripts/event-model/mermaid.ts`, `assets/toolkit/scripts/event-model/check.ts`, `assets/toolkit/scripts/event-model/page.ts`, `assets/toolkit/scripts/event-model/workspace.ts`, `assets/toolkit/scripts/event-model/model.ts`, `tests/render_fixture.py`, `tests/test_render_current.py`, `tests/test_render_files.py`, `tests/test_render_files_report.py`
Spawned: seam B — the renderer session: a browser left running, a hang, a second browser, success after a failure, a failure lost or misnamed, a renderer other than the one the key names · `drive-adversary` · claude-fable-5-1 (host model) · delegated, fresh context · manifest: `assets/toolkit/scripts/event-model/render-session.ts`, `assets/toolkit/scripts/event-model/render.ts`, `assets/toolkit/scripts/event-model/render-plan.ts`, `assets/toolkit/scripts/event-model/patch-mermaid-swimlanes.ts`, `tests/render_fixture.py`, `tests/test_render_once.py`, `tests/test_render_failures.py`
Omitted: the two pages and the fragment — prose, no boundary; the hand followed each sentence at the demo and `tests/test_render_docs.py` follows them. Windows and a run as root — no machine here to reach them; the render tests skip on Windows and say why
Findings: thirteen, none `CRITICAL` (no actor's data reaches another and no actor gains a role). Seam A ran `make model` in scratch projects with the tests' stand-in renderer; seam B with the real renderer and browser. What held: an SVG or `model.svg` that is a link to a file outside is replaced by the rename and the file behind it untouched; a byte-order mark, CRLF or bytes after the closing tag each redraw; names differing in case, a planted temporary and stray directories are removed with nothing drawn; a 3 GiB SVG is redrawn in seconds; SIGINT and SIGTERM leave no browser, no temporary and no torn file; every hostile but valid Puppeteer config gives one line and a non-zero exit; three runs started together on an empty prefix all end current; the closing line's counts were true wherever a run reached it; nothing started a second browser.

| # | Seam | Severity | Finding | Triage | State |
|---|---|---|---|---|---|
| A1 | A | HIGH | A symbolic link at `docs/event-model/slices` or `segments` is followed by the removal of what the model does not produce: the run deletes, recursively and at exit 0, everything in the directory the link names — with a committed link to `../..`, the repository itself | confirmed; new with the slice (the earlier renderer removed the link, not what was behind it) | fixed `c5eb98b` (T020 — the two directories are real directories or are removed as themselves; an entry at a produced name that is not a regular file is removed, never read, written through or descended; a link inside a removed directory is unlinked, not followed) |
| A2 | A | LOW | A dangling link or a regular file at `slices`, or a directory at a produced name, fails every run where the earlier renderer cleared it | confirmed; new | fixed `c5eb98b` (T020) |
| A3 | A | LOW | A `.mmd` in `slices/` or `segments/` that is a link is written through, to the file it names | confirmed; new for the two directories (`model.html` written through a link is older) | fixed `c5eb98b` (T020) |
| A4 | A | LOW | A slice id near 240 characters cannot be drawn: the temporary's name passes the filesystem's limit | confirmed; new | fixed `45f1032` (T021 — temporaries are named by process id and a counter) |
| A5 | A | LOW | A FIFO at an SVG's name hangs the run with nothing printed | confirmed; new (the earlier renderer never read an SVG before drawing) | fixed `c5eb98b` (T020) |
| A6 | A | LOW | The four conditions vouch for two lines and the closing tag, not the body: a hand-forged body under true stamps is left, and inlined into the page | declined — D68 rule 3 chose the record in the file; it takes a deliberate edit of an ignored file, and deleting the file redraws it | stated (the hand's note 2 is the same) |
| B1 | B | MEDIUM | The browser can change without the key changing: `PUPPETEER_EXECUTABLE_PATH`, or a `.puppeteerrc` file in the project, names another browser and every SVG stays current | confirmed; new | fixed `b895788` (T022, D72 — every `PUPPETEER_` variable is in the key; a Puppeteer rc file is stated in the page as not noticed) |
| B2 | B | MEDIUM | A first install interrupted after `mmdc` appears is treated as installed for ever: every later run fails to find the browser until `.mermaid-cli/` is deleted by hand, and no line says so | confirmed; older (the guard is the earlier renderer's) | the message fixed `bfb71c5` (T023 — the line says to delete the prefix and run again); the guard itself in the Parking Lot |
| B3 | B | MEDIUM | A browser that stops answering holds the run for six to nine minutes — Puppeteer's protocol timeout, paid twice or three times — then blames a window of diagrams | confirmed; the missing bound is older, the blame is new | the blame fixed `bfb71c5` (T023 — a browser that stopped is said once, as the browser); a bound of the run's own in the Parking Lot (a new setting or a number nobody chose) |
| B4 | B | LOW | The browser dying mid-run, or a SIGTERM, is reported as up to four diagrams that could not be drawn; the browser is never named | confirmed; new | fixed `bfb71c5` (T023) |
| B5 | B | LOW | SIGKILL of the render process leaves the browser running | confirmed by reading as older | Parking Lot |
| B6 | B | LOW | The Puppeteer config is read once for the key and again for the launch: an edit between the two is drawn and never keyed | confirmed; new | fixed `b895788` (T022 — the config's bytes are read once, keyed and launched with) |
| B7 | B | LOW | Two failures of the patcher are not `render:` lines, and an unreadable chunk directory is reported as a changed upstream layout | confirmed; older | Parking Lot |


## S03 · ef66461 · 2026-10-04

Slice `S03-verify-stamp` (cruise iteration 11), diff `5ab85e0..ef66461`: `assets/toolkit/scripts/verify-stamp.py` (new:
when a stamp may be read, the key, the stamp and the note under the git directory, the lines), `src/slipwai/project/gate.py`
(new: the stamped `verify` rule and `verify-checks`), `src/slipwai/backends.py` (the machine's tools per backend),
`src/slipwai/project/makefile.py` and `src/slipwai/project/adopted_targets.py` (which rule a project takes),
`assets/toolkit/scripts/check-slice-scope.py` (the trunk's own name exposed), `src/slipwai/project/docs.py`, eighteen test
modules, one fragment.

| Trigger | Status | Evidence |
|---|---|---|
| driving adapter (HTTP route, CLI command, queue consumer) | widened | `make verify` in a generated project (`src/slipwai/project/gate.py`): what it runs now depends on a record of an earlier run, on `VERIFY_FORCE`, on make's goals and modes and on the branch; two new verbs, `reuse` and `record`, in `assets/toolkit/scripts/verify-stamp.py`. No earlier row covers the gate's recipe |
| driven adapter or the provider types behind one | widened | git asked for the files, the index, the refs and the git directory; each machine-supplied tool launched for its version; a file and a note written under the git directory by rename (`assets/toolkit/scripts/verify-stamp.py`) |
| authorisation decision (who can reach one that already exists) | not present | The diff decides nothing about who may do what; the script runs as the developer in their own checkout. Where a stamp may be read (never the trunk, never CI) is a rule about places, attacked under the first trigger |
| concurrency, idempotency, ordering, retention, or time | widened | A second run is claimed equivalent to the first without running it; the key is taken before and after the checks; a record is kept with no expiry; two runs in one worktree, a killed run, two worktrees of one repository |

Not the slice that closes the split; `--full` not passed. A pass is owed: three triggers `widened`.

Spawned: seam A — what the key holds: a reused stamp standing for a gate that would fail now (files git lists and does not, refs, git configuration, ignored inputs, tools, variables, a project in a subdirectory of its repository) · `drive-adversary` · claude-fable-5-1 (host model) · delegated, fresh context · manifest: `assets/toolkit/scripts/verify-stamp.py`, `src/slipwai/backends.py`, `src/slipwai/project/gate.py`, `src/slipwai/project/gitignore.py`, `assets/toolkit/scripts/check-imports.py`, `assets/toolkit/scripts/check-migrations.py`, `assets/toolkit/scripts/check-slice-scope.py`, `tests/test_verify_stamp_working.py`, `tests/test_verify_stamp_key.py`, `tests/test_verify_stamp_tools.py`, `tests/test_verify_stamp_stored.py`, `tests/test_verify_stamp_launches.py`, `tests/test_verify_stamp_inputs.py`, `tests/test_verify_stamp_lists.py`, `tests/test_verify_stamp_scan.py`, `tests/stamp_fixture.py`
Spawned: seam B — the stamp's file and note under the git directory and what happens in time: two runs at once, a killed run, a hand-run verb, links and other things at the paths, worktrees, two projects · `drive-adversary` · claude-fable-5-1 (host model) · delegated, fresh context · manifest: `assets/toolkit/scripts/verify-stamp.py`, `src/slipwai/project/gate.py`, `tests/test_verify_stamp_reuse.py`, `tests/test_verify_stamp_runs.py`, `tests/test_verify_stamp_cannot.py`, `tests/test_verify_stamp_file.py`, `tests/test_verify_stamp_force.py`, `tests/stamp_fixture.py`
Spawned: seam C — where a stamp is never read, and the recipe: the trunk's name, CI markers, a detached `HEAD`, make's goals, modes and variables, every generated shape, a migrated project, an adopted repository · `drive-adversary` · claude-fable-5-1 (host model) · delegated, fresh context · manifest: `assets/toolkit/scripts/verify-stamp.py`, `assets/toolkit/scripts/check-slice-scope.py`, `src/slipwai/project/gate.py`, `src/slipwai/project/makefile.py`, `src/slipwai/project/adopted_targets.py`, `src/slipwai/project/model_targets.py`, `src/slipwai/project/ci_workflows.py`, `src/slipwai/project/adopted_ci.py`, `tests/test_verify_stamp_where.py`, `tests/test_verify_stamp_force.py`, `tests/test_verify_stamp_runs.py`, `tests/test_verify_stamp_ships.py`, `tests/test_verify_stamp_pinned.py`, `tests/stamp_fixture.py`
Omitted: the page and the fragment as prose — the hand followed each sentence at the demo and `tests/test_verify_stamp_ships.py` follows them (seam C read the adopted page and found C7). Windows, GNU Make 3.81 and a CI system that sets no marker — no machine here to reach them; each is named in the Parking Lot (D81, D83). Real toolchains other than Python's — the hand ran a TypeScript and React starter at the demo; seam A ran with a stand-in `uv`
Findings: eighteen, none `CRITICAL` on this log's scale (no actor's data reaches another and no actor gains a role); the trunk-and-CI promise held everywhere except C1. What held: file names with a newline or non-UTF-8 bytes, a tracked file replaced by a directory, sparse checkout, a link's target, notes and packed refs each move or rightly do not move the key; 23 spellings of make's dry-run, touch and question modes read and write nothing, and 7 of ignore-errors remove the stamp and write none; a killed or interrupted run leaves only the note; a link, FIFO or socket at the stamp's, the note's or the directory's path is never read or written through; a linked worktree, a bare repository with a worktree and a submodule each keep their own stamp; no committed file can make a stamp appear; the trunk is recognised on `main`, on `master` with no `main`, on a recorded `develop`, in a second worktree, with a tag named like it, through a symbolic-ref alias, in a reftable clone, detached and inside a rebase; every CI marker in every spelling runs in full and leaves a planted stamp byte-identical; the trunk's output is byte-identical to before the slice for thirteen invocations; twelve generated shapes carry on `verify-checks` exactly the prerequisites `verify` had; pruning a transport leaves a gate that parses; a project generated by the released factory and migrated runs, stamps and reuses; an adopted repository's `delivery/Makefile` is byte for byte what it was. Triage by `drive-skipper` (D83).

| # | Seam | Severity | Finding | Triage | State |
|---|---|---|---|---|---|
| A1 | A | HIGH | A file git ignores inside the project that a check reads by walking the tree (`compileall` over a service's tests, `check-imports`) is in no part of the key: the plain run reuses while the forced run fails | confirmed; new with the slice | fixed `2ee4a07` (T036) — D83: the key covers every file under the project except a closed exempt list |
| A2 | A | MEDIUM | A project in a subdirectory of its repository, on a `slice/<id>` branch: a sibling's uncommitted tracked edit fails `check-slice-scope` when forced and the plain run reuses (T022) | confirmed; new with the slice | fixed `2ee4a07` (T036) — D83: tracked and untracked files and the index for the whole repository |
| A3 | A | MEDIUM | A tag named like the trunk or the slice branch, and a replace ref, change what `check-migrations` or `check-slice-scope` resolves; the key holds two ref namespaces only | confirmed; new with the slice for the key. That a tag switches `check-slice-scope` off is older | fixed `2ee4a07` (T036 — every ref); the older part in the Parking Lot (D39) |
| A4 | A | LOW | `core.quotePath` changes what `check-migrations` sees; the repository's git configuration is not in the key | confirmed; new with the slice | fixed `2ee4a07` (T036) |
| B1 | B | HIGH | Two runs at once in one worktree stamp a failing tree: the second run's note replaces the first's, and the first run's `record` trusts it | confirmed; new with the slice | fixed `10c78c3` (T037) — D83: the note is bound to its run |
| B2 | B | MEDIUM | `record` typed by hand after a failed or killed run stamps the failing tree | confirmed; new with the slice | fixed `10c78c3` (T037) |
| B3 | B | MEDIUM | A git directory whose name ends in whitespace gets its stamp written in a sibling directory outside it | confirmed; new with the slice | fixed `b55d0a7` (T039) |
| B4 | B | LOW | Two projects whose directory names differ only in leading whitespace share one stamp | confirmed; new with the slice | fixed `b55d0a7` (T039) |
| B5 | B | LOW | A directory at the note's path stops every later run recording and the line names nothing to delete; a file where the stamp's directory should be gets a line naming a file that does not exist | confirmed; new with the slice | fixed `b55d0a7` (T039) |
| B6 | B | LOW | The stamp's instant is printed as stored: a hand-made stamp prints arbitrary lines | confirmed; new with the slice | fixed `b55d0a7` (T039) |
| C1 | C | MEDIUM | An unborn `master` with no `main` and no `ci.branch` reads and writes a stamp before the repository's first commit (AC-S03-21) | confirmed; new with the slice | fixed `72bf9f3` (T038) — D83: an unborn `HEAD` is not eligible; a trunk name with no ref cannot be told |
| C2 | C | MEDIUM | The recipe runs `$(MAKE)` unquoted: a make whose path holds a space cannot run the gate at all, on the trunk and in CI too | confirmed; new with the slice; fails closed | fixed `f53af33` (T040) |
| C3 | C | MEDIUM | `ci` reached as a prerequisite of another target, or with `MAKECMDGOALS` overridden, reuses a stamp | confirmed; new with the slice | fixed `f53af33` (T040) — D83: `ci` depends on the checks' own target |
| C4 | C | MEDIUM | A recorded `ci.branch` the gate cannot use, or an unreadable `project.json`, leaves the trunk stamping and nothing says so | confirmed; new with the slice | fixed `72bf9f3` (T038) |
| C5 | C | LOW | `HEAD` as a symbolic ref outside `refs/heads` is taken for a branch that is not the trunk | confirmed; new with the slice | fixed `72bf9f3` (T038) |
| C6 | C | LOW | Where git fails with several lines, the one line is four, on the trunk too | confirmed; new with the slice | fixed `b55d0a7` (T039) |
| C7 | C | LOW | An adopted repository's gates page describes a stamp its gate never uses | confirmed; new with the slice | fixed `8765ed7` (T041) |
| C8 | C | LOW | `make -f build.mk verify` with no file named `Makefile` fails where it passed; `make verify lint` runs `lint` twice; `make verify MAKE=/bin/true` exits 0 with no check run and records | the `-f` case confirmed, new; the doubled check stated (more, never less); the replaced make declined (D83, on D72's A6 precedent) | the `-f` case fixed `f53af33` (T040); the rest stated in the Parking Lot and for the cruise report |


## S24 · edb78cd · 2026-10-04

Slice `S24-ci-fetches-slice-base` (cruise iteration 12), diff `838a3b0..edb78cd`: `src/slipwai/project/ci_workflows.py`
and `src/slipwai/project/adopted_ci.py` (the `verify` jobs fetch full history; `GIT_DEPTH: "0"` on the GitLab job),
`assets/toolkit/scripts/check-slice-scope.py` (no base, and a comparison that could not run, fail in a forge's
checkout), `src/slipwai/adopt_report.py` and `docs/adopting.md` (what a CI of one's own needs), nine test modules and
a helper, two fragments. The CI half of S20's finding A3, left open by S22 (D31), is what this slice closes.

| Trigger | Status | Evidence |
|---|---|---|
| driving adapter (HTTP route, CLI command, queue consumer) | widened | `check-slice-scope`'s exit code in a forge's checkout (`assets/toolkit/scripts/check-slice-scope.py`, `check()`): two answers that exited 0 now exit 1; the generated and adopted CI jobs' checkout (`src/slipwai/project/ci_workflows.py`, `src/slipwai/project/adopted_ci.py`). The S22 row attacked the base selection with a base present and the no-base answers as they then were |
| driven adapter or the provider types behind one | widened | What the forge's checkout hands the three history gates: every branch and tag of the remote, where it was one commit — so refs a pull request's author can push are now inputs in CI to `check-slice-scope`, `check-migrations` and `check-flags` |
| authorisation decision (who can reach one that already exists) | not present | The diff decides nothing about who may do what; what a pull request's author can make CI conclude is attacked under the two rows above |
| concurrency, idempotency, ordering, retention, or time | not present | No claim about any of them: one checkout, one run |

Not the slice that closes the split; `--full` not passed. A pass is owed: two triggers `widened`.

Spawned: seam A — `check-slice-scope` in a forge's checkout with every branch and tag of the remote fetched, and its failing arms: what a pull request's author, or a misconfigured job, can make it conclude · `drive-adversary` · claude-fable-5-1 (host model) · delegated, fresh context · manifest: `assets/toolkit/scripts/check-slice-scope.py`, `tests/test_slice_scope_forge.py`, `tests/test_slice_scope_forge_nobase.py`, `tests/test_slice_scope_no_base.py`, `tests/test_slice_scope_hostile_base.py`, `tests/test_slice_scope_report.py`, `tests/forge_checkout.py`, `src/slipwai/project/ci_workflows.py`
Spawned: seam B — the three CI files as a forge parses them and `migrate` merges them, what `adopt` tells a CI it did not write, and `check-migrations` and `check-flags` on the full-history checkout · `drive-adversary` · claude-fable-5-1 (host model) · delegated, fresh context · manifest: `src/slipwai/project/ci_workflows.py`, `src/slipwai/project/adopted_ci.py`, `src/slipwai/project/adopted.py`, `src/slipwai/scaffold.py`, `src/slipwai/adopt_report.py`, `docs/adopting.md`, `changelog.d/ci-fetches-slice-base.md`, `changelog.d/slice-scope-base.md`, `assets/toolkit/scripts/check-migrations.py`, `assets/targets/aws/scripts/check-flags.py`, `assets/targets/azure/scripts/check-flags.py`, `tests/test_ci_fetch_generated.py`, `tests/test_ci_fetch_adopted.py`, `tests/test_ci_fetch_migrate.py`, `tests/test_ci_history_gates.py`, `tests/forge_checkout.py`
Omitted: a real runner on a real forge — nothing is pushed (D12); each checkout was built with git in the shape the forge documents, and what a GitLab merge-request pipeline checks out is assumed (B2). Windows — no machine here. The fragment as prose — the hand followed the catch-up as `migrate` writes it at both demos
Findings: eight, none `CRITICAL` on this log's scale. What held: tags and branches named `main`, `origin/main`, `HEAD`, `heads/main`, `remotes/origin/main`, `master` at the slice's head, each also recorded in `ci.branch`, never moved the base in a full fetch; odd values of the target variable left the trunk `main`; a keyed-but-shallow checkout fails; a hostile `ci.branch` is printed cleaned. The key is on the `verify` job once, and nowhere else, in 80 generated shapes, with five added services and a frontend, and in 12 adopted shapes, every file parsing; `migrate` from the factory before the slice brought the key or stopped at a named conflict in a dozen edit cases and dropped nothing silently; `check-migrations` passed a pull request behind the trunk, a first pull request, a squash-merged expand followed by its contract on GitHub's merge commit, and a push to `main`. Triage is D87

| # | Seam | Severity | Finding | Triage | State |
|---|---|---|---|---|---|
| F1 | A | HIGH | Where the base under the name the branch recorded in `ci.branch` and the pull-request target's base share no history, `older_of()` keeps the branch's: an orphan root merged into the slice and pushed as `evil` passes a `Makefile` edit in a forge's full-history checkout, *compared with `evil`*, exit 0 | confirmed; older code (S22), reachable in CI only since this slice | fixed `80cfa1f` (T020) — D87: where the two bases share no history the target's base is compared with (AC-S24-14) |
| F2 | A | MEDIUM | *The older base wins* (D30): where an old trunk commit records another trunk name and a branch of that name is pushed there, a pull request that puts everything outside its scope back to that commit's tree passes | question — D30's rule as written; whether the target is the base outright is a person's | deferred to the Parking Lot and the cruise report (D87); no person has ruled |
| F3 | A | MEDIUM | The fetch the gate prints, `git fetch origin main:refs/remotes/origin/main`, takes a tag named `main` before the branch, so the gate's own advice installs an author-pushed tag as the trunk | confirmed; older (S22, T027), a developer's-checkout answer | fixed `4531d3a` (T021) — D87: the command names `refs/heads/<name>` in full (AC-S24-16) |
| F4 | A | LOW | A checkout whose remote is not named `origin` has the history and is told *NOT checked … needs `fetch-depth: 0`*, exit 1, with nothing saying which ref was looked for | confirmed; the red is new with the slice | fixed `0637839` (T022) — D87: the line names the two refs it looked for and the remote called `origin` (AC-S24-15) |
| B1 | B | MEDIUM | A pull request to a branch other than the trunk is compared with the trunk by `check-migrations` and `check-flags`, so a contract whose expand reached that branch in an earlier pull request is refused | confirmed; older rule, the developer's full clone answers the same; the red CI job is new | stated in the fragment's catch-up (`bcd66dc`) and held by a test (`4182248`); the fix is `S31-gates-read-recorded-trunk`'s (D87) |
| B2 | B | MEDIUM | On a checkout of the branch's own tip, an expand squash-merged to the trunk and its contract on the same branch, not merged with the trunk, is refused (GitLab assumed; not present on GitHub's merge commit) | confirmed in the built checkout; the forge's behaviour assumed | stated in the fragment's catch-up (`bcd66dc`) and held by a test (`4182248`); `S31-gates-read-recorded-trunk` (D87) |
| B3 | B | LOW | A pull request that restores by `git revert` an expand and its contract removed in one commit is refused as new in the same change | confirmed; older rule, newly red in CI | declined here — Parking Lot (D87) |
| B4 | B | LOW | `delivery_workflow()` writes the trunk's name unquoted into `branches: [...]`: a trunk named `a,b`, `1.0`, `true` parses to something else, `x]` is a YAML error, and `adopt` exits 0 | confirmed; older than the slice, not in its diff | declined here — Parking Lot (D87, D39) |

## S04 · a7da5f0 · 2026-10-04

Slice `S04-parallel-gate` (cruise iteration 13), diff `3f44288..a7da5f0`: `src/slipwai/project/parallel_gate.py` (new: the
sync target, `check-python` first, the gate-only order, the page), `gate.py` (the recipe: output grouping, the order
variable, the failed run's line), `makefile.py`, `languages/python.py` (`--synced`), `backends.py`, `integration.py`,
`openapi.py`, `shared_packages.py`, `adopted_targets.py` (the guarded serial directive), `model_targets.py` (one file
target, `npm ci`, the skip line, the recipe's own marker), `assets/toolkit/scripts/event-model/package-lock.json` (new),
two shipped texts, one fragment, a test helper and nineteen test modules.

| Trigger | Status | Evidence |
|---|---|---|
| driving adapter (HTTP route, CLI command, queue consumer) | widened | A generated project's `make` goals and flags (`-j`, `-k`, `-n`, `-O`, several goals) as inputs to the gate's recipe in `src/slipwai/project/gate.py`; the second argument of the generated `scripts/verify` (`src/slipwai/project/languages/python.py`). The S03 row attacked the stamp's recipe under make's modes as it then was, serial |
| driven adapter or the provider types behind one | widened | What the gate asks npm for the model tooling: `npm ci` from a shipped lock behind a file target with a marker of the recipe's own (`src/slipwai/project/model_targets.py`), where it was `npm install` on every run; `slipwai migrate` carrying the lock into a project that has a file there |
| authorisation decision (who can reach one that already exists) | not present | The diff decides nothing about who may do what |
| concurrency, idempotency, ordering, retention, or time | widened | The slice's claim: under `-j` the gate gives the serial verdict, a writer never runs beside its reader, each service syncs once, one install serves several goals, a pass under `-j` and a serial pass share one stamp, an adopted gate started on its own Makefile is serial (`src/slipwai/project/parallel_gate.py`, `src/slipwai/project/adopted_targets.py`) |

Not the slice that closes the split; `--full` not passed. A pass is owed: three triggers `widened`.
