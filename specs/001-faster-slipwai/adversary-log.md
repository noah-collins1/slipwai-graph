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

Spawned: seam A — a generated project's gate under `make -j` as a developer, an agent or the environment can drive it: a green or a stamp on a tree a check fails, a check that did not run, a sync skipped, a failure's name lost · `drive-adversary` · claude-fable-5-1 (host model) · delegated, fresh context · manifest: `src/slipwai/project/parallel_gate.py`, `src/slipwai/project/gate.py`, `src/slipwai/project/makefile.py`, `src/slipwai/project/languages/python.py`, `src/slipwai/project/adopted_targets.py`, `src/slipwai/project/shared_packages.py`, `src/slipwai/project/openapi.py`, `src/slipwai/project/integration.py`, `src/slipwai/backends.py`, `assets/toolkit/scripts/verify-stamp.py` (read), `tests/parallel_gate.py` and the gate's test modules
Spawned: seam B — the model tooling's install rule and how the shipped lock reaches a project that exists: tooling that disagrees with the lock while the gate says otherwise, an install that never happens, a gate that writes into the tree, `migrate` losing a project's file · `drive-adversary` · claude-fable-5-1 (host model) · delegated, fresh context · manifest: `src/slipwai/project/model_targets.py`, `assets/toolkit/scripts/event-model/package.json`, `assets/toolkit/scripts/event-model/package-lock.json`, `src/slipwai/migrate.py` (read), `assets/toolkit/scripts/verify-stamp.py` (read), `changelog.d/parallel-gate.md`, `assets/toolkit/docs/event-model/README.md`, the model tooling's test modules and `tests/test_parallel_gate_carry.py`
Omitted: GNU Make 3.81 and 4.3 — none on this machine. Windows and macOS. A Java gate with its real toolchain under attack (its Makefile was read; converge pass 2 and the demo ran it). A real kill of `uv sync` or `npm ci` part-way. `make -j ci` and goals other than `verify`, not promised (D88) — the two unpromised doors tried were red and wrote no stamp
Findings: nine, none `CRITICAL`, none `HIGH`. What held: on a red tree every spelling tried — `-j`, `-j1`, `-j -k`, `-j -s`, `-j -B`, `-j -O`, `-o test`, `-W`, two goals — exited 2 on the gate's line with each failed check on a `***` line; `-n`, `-t`, `-q` and every spelling of `-i` left no stamp; 22 forced `-j` runs over Python, TypeScript and Go were green; a stale lock under `-j` failed as the sync with no Python mode after it; nothing ran beside a failing `check-python` on a fresh clone; two gates at once on a green tree left one valid stamp; a fresh clone installs once, a second run installs nothing, and no gate or model target left anything in `git status`; a manifest and lock that disagree are refused with the tree left intact; `migrate` added, refused, merged clean and stopped on the one file as the criteria say.

| # | Seam | Severity | Finding | Triage | State |
|---|---|---|---|---|---|
| A1 | A | LOW | `VERIFY_GROUP=-i` from the command line or with `-e` reaches the sub-make only: a red tree prints *all gates passed* and is stamped. New with S04 | Fix now: the variable is defined with `override` (D97) | fixed at T023 (AC-S04-82) |
| A2 | A | LOW | `--eval='.IGNORE: test lint'` stamps a red tree; older (S03's recipe) | Parking Lot and the cruise report, beside D83's `MAKE=/bin/true` (D97) | parked |
| A3 | A | LOW | Under `-k` on a Go or Java project a red `lint` leaves `typecheck` and `test` unrun and unnamed. New | A stated reading: one sentence on the page, one clause in the fragment, a hold (D97) | fixed at T023 (AC-S04-83) |
| A4 | A | LOW | The adopted guard is false under `MAKEFILES` and an absolute `-f` path with a space. New | Parking Lot, beside D95's line (D97) | parked |
| A5 | A | LOW | `./scripts/verify --lint-only --synced` typed by hand lints on a stale lock. New | D90 stands; one clause on the page; the cruise report (D97) | fixed at T023 (AC-S04-84) |
| B1 | B | MEDIUM | Two makes at once leave a broken tree under the marker; every later run says not reinstalled and fails; no page named the way out. New | Words now on the page and in the README; a self-healing rule parked as a slice (D97) | words fixed at T023 (AC-S04-84); mechanism parked |
| B2 | B | MEDIUM | Manifests arriving with dates older than the marker are never installed and the line said *matches*. New | D94's reversal taken: the line says what make compared (D97) | fixed at T023 (AC-S04-48, -55) |
| B3 | B | LOW | An npm command or `make -t` that moves the tree or the marker without a manifest is not seen. New | Parking Lot and the cruise report (D97) | parked |
| B4 | B | LOW | The merge `migrate` makes replaces a lock the project ignores, without a refusal; older | One sentence in the catch-up, a hold where cheap; whether `migrate` should refuse is parked (D97) | fixed at T023 (AC-S04-60, -85); question parked |


## S05 · 8c7e4cd · 2026-10-04

Slice `S05-xdist` (cruise iterations 14–15), diff `9acded6^..8c7e4cd` plus `c971759`: `src/slipwai/project/languages/python.py`
(the mark's reader in the generated `scripts/verify`, the flags spliced into the default suite only),
`src/slipwai/project/parallel_tests.py` (new: the gates page's paragraph), `src/slipwai/project/metadata.py`,
`src/slipwai/manifest.py` (`recorded_parallel_safe`), `replay.py`, `add_service.py`, `converge.py`, `resurvey.py`,
`scaffold.py`, `cli.py`, `docs.py`, the four committed Python locks (`pytest-xdist`, `execnet`), one fragment and five
test modules.

| Trigger | Status | Evidence |
|---|---|---|
| driving adapter (HTTP route, CLI command, queue consumer) | widened | The generated `scripts/verify` now reads `project.json` and its modes splice `-n auto --maxprocesses 4` (`src/slipwai/project/languages/python.py`); `generate`, `migrate`, `add-service`, `adopt --refresh` and `converge` carry a new key (`src/slipwai/manifest.py`, `src/slipwai/replay.py`) |
| driven adapter or the provider types behind one | widened | A new dependency the gate drives, `pytest-xdist` with `execnet`, in every Python service's lock (`assets/languages/python/locks/uv.lock` and its three siblings) |
| authorisation decision (who can reach one that already exists) | not present | The diff decides nothing about who may do what |
| concurrency, idempotency, ordering, retention, or time | widened | The slice's claim: the parallel default suite gives the serial run's pass/fail set; the database-backed suite stays serial; the mark is read fresh on every run, so the stamp never answers a stale mark (`src/slipwai/project/languages/python.py`, `assets/toolkit/scripts/verify-stamp.py` unchanged) |

Not the slice that closes the split; `--full` not passed. A pass is owed: three triggers `widened`.

Spawned: seam A — the generated gate with the mark on: a green, or a stamp, on a tree whose serial run is red; a verdict that differs from the serial one without a word · `drive-adversary` · claude-opus-5-5 (host model) · delegated, fresh context · manifest: `src/slipwai/project/languages/python.py`, `src/slipwai/project/parallel_tests.py`, `src/slipwai/project/metadata.py`, `assets/toolkit/scripts/verify-stamp.py` (read), `assets/languages/python/locks/uv.lock`, `changelog.d/xdist.md`, `tests/test_xdist_gate.py`, `tests/test_xdist_plugin.py`, `tests/test_xdist_page.py`
Spawned: seam B — the mark through `generate`, `migrate`, `add-service`, `describe-service`, `adopt --refresh` and `converge`: a person's mark deleted, flipped, added or duplicated, or `project.json` corrupted · `drive-adversary` · claude-opus-5-5 (host model) · delegated, fresh context · manifest: `src/slipwai/manifest.py`, `src/slipwai/replay.py`, `src/slipwai/add_service.py`, `src/slipwai/converge.py`, `src/slipwai/resurvey.py`, `src/slipwai/scaffold.py`, `src/slipwai/project/metadata.py`, `src/slipwai/migrate.py` (read), `changelog.d/xdist.md`, `src/slipwai/project/parallel_tests.py`, `tests/test_xdist_carry.py`, `tests/test_xdist_mark.py`
Omitted: what converge passes 1 and 2 already ran — the reader on a directory, a list, a BOM, a symlink and duplicate keys; a root `json.py` (T017, T019); Windows quoting; the integration run; make's modes against the stamp (the S04 row). `converge`'s own move and a mark nested under `deployables` were read, not run (time). Windows and macOS
Findings: eight — one `HIGH`, three `MEDIUM` counting T018's class, four `LOW`. What held: a session fixture failing at teardown, a worker crashing mid-run, a collection that differs between workers, an import error, a `-k` matching nothing in `--test-only`, `PYTEST_XDIST_AUTO_NUM_WORKERS` and `PYTEST_ADDOPTS=-n0`, `--sw`, `-x`, `--maxfail`, `--lf` — all give the serial verdict; `migrate` twice is idempotent; odd spacing, an escaped key name, an object value and a reformatted file conflict loudly; CRLF merges clean with one copy; `add-service` and `describe-service` never add or flip a single mark; `adopt` writes no key.

| # | Seam | Severity | Finding | Triage | State |
|---|---|---|---|---|---|
| A1 | A | HIGH | Tests that share module-level state, or a `pytest_sessionfinish` hook that sets the exit status, are red serially and green in parallel; the generated CI runs `make verify` with the mark on, so no gate runs the suite serially. New | D106; T022 | fixed at 7235418 |
| A2 | A | MEDIUM | `--adversarial-only` reads every worker crashing at collection (exit 5) as no adversarial tests and passes. New | D106; T022 | fixed at 7235418 |
| A3 | A | LOW | `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` or `PYTEST_ADDOPTS="-p no:xdist"` fails the gate on a bare usage error. New | D108; T024 | fixed at 39f41ea |
| A4 | A | LOW | The stamp keys on no pytest variable: `PYTEST_ADDOPTS=--co make verify` would stamp a tree whose tests never ran (read, not run). Older (S03) | D108 part 5: a method slice behind S32 (Parking Lot), and the cruise report | parked |
| B1 | B | MEDIUM | `add-service`, `describe-service` and `adopt --refresh` collapse a mark written twice to the last copy's value, flipping a person's `false` (serial) to `true`. New | D107; T023, closing T018 | fixed at 85bb78e |
| B2 | B | LOW | A project with no Python service has a page sentence saying `project.json` carries the mark `true`, whatever it carries. New | D108; T024 | fixed at 39f41ea |
| B3 | B | LOW | A mark `1e400` is rewritten as `Infinity`, which is not JSON. Older mechanism, newly reachable | D108; T024 | fixed at 39f41ea |
| A5 | A | LOW | With the mark `false` a test that calls `os._exit(0)` ends the serial run green part way; parallel is red. Older; S05 makes it stricter | Declined: not this slice's; the cruise report | declined |

## S33 · b7ad13e · 2026-10-05

Slice `S33-factory-gate-stamp` (cruise iterations 13–19), diff: the root `Makefile` (`cab6cda`, `d92f908`, `63d529d`, owner-applied
patches), `src/slipwai/assets.py` (`dbbc0ef`: the pruner loads with bytecode writing off), the test modules
`tests/test_factory_gate_stamp.py`, `tests/test_factory_gate_stamp_inputs.py`, `tests/test_assets_bytecode.py` and the
suite's fixes (`e3bc084`, `e997a5f`, `2a8c10c`, `f35f981`, `f326372`, `d69f345`, `d26bb55`, `3b9cd90`), one fragment.
`assets/toolkit/scripts/verify-stamp.py` is unchanged and run from where it ships.

| Trigger | Status | Evidence |
|---|---|---|
| driving adapter (HTTP route, CLI command, queue consumer) | widened | The maintainer's `make verify` at the root now asks the stamp first and can return without a check (`Makefile`, the `verify` and `verify-checks` targets) |
| driven adapter or the provider types behind one | not present | No new dependency; the stamp script is the one the S03 row covers, unchanged |
| authorisation decision (who can reach one that already exists) | not present | The diff decides nothing about who may do what |
| concurrency, idempotency, ordering, retention, or time | widened | The slice's claim: an unchanged tree is not judged twice, a changed one always is; the recipe writes `.factory-work/verify-probes` on every run, which the key reads; two runs at once, an interrupted run, a tool or cache changing under a run (`Makefile`; the script's own locking and interruption rules are the S03 row's) |

Not the slice that closes the split; `--full` not passed. A pass is owed: two triggers `widened`.

Spawned: seam A — the root recipe asking the stamp: a reuse for a tree whose full gate would now say something different, or no reuse where one is owed · `drive-adversary` · claude-opus-5-5 (host model) · delegated, fresh context · manifest: `Makefile`, `assets/toolkit/scripts/verify-stamp.py` (read), `src/slipwai/assets.py`, `tests/test_factory_gate_stamp.py`, `tests/test_factory_gate_stamp_inputs.py`, `tests/test_assets_bytecode.py`, `.gitignore`
Omitted: the script's own locking, interruption and key rules (the S03 row, unchanged); two terminals with different Docker set-ups racing the probe file, variables reaching the generated gates under `test_matrix`, and `JAVA_HOME` against `PATH` (time). Windows and macOS
Findings: five — three `MEDIUM` counting A3, two `LOW`. What held: 19 asset-touching modules (195 tests) run with bytecode writing on leave no cache under `assets/` after D121; two runs at once leave one stamp and the next run reuses it; a blank `FACTORY_BACKENDS` is refused (T022); every tool the suite looks for outside `VERIFY_TOOLS` is stubbed or not run by the gate; the Docker daemon's state fails the Postgres test rather than skipping it.

| # | Seam | Severity | Finding | Triage | State |
|---|---|---|---|---|---|
| A1 | A | MEDIUM | A probe file the recipe cannot write (left by a run as root) or a symlinked `.factory-work` turns D112's and D119's keying off: a cache planted under `assets/` is reused past while the forced run fails. The step ends in `;`, and the script keys a link, not what is behind it. New | D122; T031 (`s33-4.patch`, a person applies) | fixed `5842ba9` (T031) |
| A2 | A | MEDIUM | A gate whose output is written into an ignored, non-exempt file in the tree (`make verify > .factory-work/verify.log`, `tee build/…`) never records, and its line says the next run will. New in the root's set-up | D122: the quickstart says where a log goes; the general question behind S32 (Parking Lot) | stated |
| A3 | A | MEDIUM | `tests/test_gitea_pages.py` loads `scripts/gitea-pages.py`, which reads `GITEA_PAGES_*` at import; a value in the maintainer's shell fails the suite but is not keyed, so a pass is reused past it. The scan reads no `scripts/*.py`. New | D122; T030 | fixed `06d0732` (T030) |
| A4 | A | LOW | `MAKE=/bin/true` in the environment makes the root gate a stamped no-op. Same class as S03's C8 (D83) | Declined on D83; the cruise report | declined |
| A5 | A | LOW | Where `find` fails part-way the probe lists nothing and does not fall back to a line unique to the run, as the `Makefile`'s comment promises; no false green reached. New | D122; T031 (`s33-4.patch`) | fixed `5842ba9` (T031) |

## S06 · d36097e · 2026-10-06

Slice `S06-scoped-gate` (cruise iterations 17–23), diff `58a9aed..d36097e`: the generated `make verify-scoped` and the per-deployable `lint-`, `typecheck-` and `test-` targets (`src/slipwai/project/scoped_targets.py`, `src/slipwai/project/makefile.py`, `src/slipwai/project/native_commands.py`), the toolkit script and its package (`assets/toolkit/scripts/verify-scoped.py`, `assets/toolkit/scripts/verify_scoped/`), the baseline and the flags predicate in `assets/toolkit/scripts/verify-stamp.py`, the prune's re-fingerprint (`assets/backing-services/prune.py`), the ladder and template words, one fragment.

| Trigger | Status | Evidence |
|---|---|---|
| driving adapter (HTTP route, CLI command, queue consumer) | widened | A new make target a developer and the ladder run, `make verify-scoped`, and the script's `run` and `record` commands (`src/slipwai/project/scoped_targets.py`, `assets/toolkit/scripts/verify-scoped.py`) |
| driven adapter or the provider types behind one | widened | The script drives git (merge-base, diff, ls-files, cat-file) and make (`-npq` database reads, the sub-make with the jobserver) and reads `project.json`, `rules.json` and the baseline (`assets/toolkit/scripts/verify_scoped/record.py`, `assets/toolkit/scripts/verify_scoped/reach.py`, `assets/toolkit/scripts/verify-stamp.py`) |
| authorisation decision (who can reach one that already exists) | not present | The diff decides nothing about who may do what |
| concurrency, idempotency, ordering, retention, or time | widened | `make -j verify-scoped` keeps make's jobserver; the baseline is written only by a green full run and removed by any other; the base is the newer of two refs (`assets/toolkit/scripts/verify-scoped.py`, `assets/toolkit/scripts/verify-stamp.py`) |

Not the slice that closes the split; `--full` not passed. A pass is owed: three triggers `widened`.

Spawned: seam A — the selection's inputs from git and the tree, and D148's reach reader · `drive-adversary` · claude-opus-5-5 (host model) · delegated, fresh context · manifest: `assets/toolkit/scripts/verify-scoped.py`, `assets/toolkit/scripts/verify_scoped/choose.py`, `assets/toolkit/scripts/verify_scoped/table.py`, `assets/toolkit/scripts/verify_scoped/record.py`, `assets/toolkit/scripts/verify_scoped/reach.py`, `assets/toolkit/scripts/check-slice-scope.py`, `src/slipwai/project/scoped_targets.py`, `tests/scoped_fixture.py`
Spawned: seam B — the baseline file, obligations and the flags predicate (D116, D125, D146, D147) · `drive-adversary` · claude-opus-5-5 (host model) · delegated, fresh context · manifest: `assets/toolkit/scripts/verify-stamp.py`, `assets/toolkit/scripts/verify-scoped.py`, `assets/toolkit/scripts/verify_scoped/record.py`, `assets/toolkit/scripts/verify_scoped/choose.py`, `tests/test_verify_scoped_baseline.py`, `tests/test_verify_scoped_flags.py`
Spawned: seam C — make (one call, the jobserver, versions) and every factory writer of `rules.json` · `drive-adversary` · claude-opus-5-5 (host model) · delegated, fresh context · manifest: `assets/toolkit/scripts/verify_scoped/rules.py`, `assets/toolkit/scripts/verify_scoped/record.py`, `src/slipwai/project/scoped_targets.py`, `src/slipwai/project/makefile.py`, `src/slipwai/project/native_commands.py`, `src/slipwai/scaffold.py`, `assets/backing-services/prune.py`, `tests/test_verify_scoped_factory_text.py`
Omitted: the project-edited Makefile text and `MAKEFLAGS` (classes closed by D140 and D146, five converge passes); assume-unchanged and skip-worktree (T044). GNU Make 3.81, Windows and macOS: not on this machine (C5 read, not run)
Findings: twenty — three `HIGH`, five `MEDIUM`, twelve `LOW` or unverified. What held: paths with tabs, quotes, a leading dash or case-only differences; renames, deletions and a directory replaced by a file; every `project.json` change; a submodule; an ignored regular file; a tracked or untracked link; colour, `diff.relative` and `core.quotePath` settings; a baseline that is a directory, a link, a FIFO, invalid UTF-8, truncated, another branch's; two runs at once; SIGINT mid-run; every malformed obligation but two; the flags allowlist under real make 4.4.1; `rules.json` matching after `generate` (20 combinations), 40 prunes, every other writer and `migrate` from `58a9aed`; the adopted layout; no unit run twice; the jobserver under `-j4`, `-j2` and `-j`; a CRLF Makefile.

| # | Seam | Severity | Finding | Triage | State |
|---|---|---|---|---|---|
| A1 | A | HIGH | Content git's filters normalise away — CRLF under the project's `text=auto eol=lf`, a mode bit under `core.fileMode=false` — is never *changed*: the scoped run says *passed* while `make verify` fails (biome on the CRLF file; `scripts/verify` not executable). New | Confirmed; S06 T048 | open |
| B1 | B | HIGH | `make -f <file> verify` writes the stamp and the baseline for a tree no check judged: `-f` is not in `MAKEFLAGS`, and the sub-make reads the alternate file; the next plain `make verify` and `make verify-scoped` reuse it. Older hole (S03's stamp), widened by S06's baseline and `make -f deploy.mk` advice | Confirmed; S06 T049 | open |
| B2 | B | HIGH | `MAKEFILES=<file> make verify` does the same; `.SHELLFLAGS` from the environment reaches recipes unseen (not built to a false green). Same class as B1 | Confirmed; S06 T049 | open |
| A2 | A | HIGH | A local `main` with commits nobody gated, merged into the slice, becomes the base; its breakage is never checked by the scoped run. New in S06 | Question: D153 | open |
| A3 | A | MEDIUM | An ignored symlink out of a deployable is invisible to D148's reader and to the ignored-files digest (it records the link's text): a change through it is skipped. New | Confirmed; S06 T051 | open |
| A6 | A | MEDIUM | D148's reader is quadratic in deployables: 40 deployables of 300 files take 115 s on every scoped run. New | Confirmed; S06 T053 | open |
| C1 | C | MEDIUM | A fresh `generate --users keycloak` with the browser app can never scope: the factory's own Go, TypeScript and Python identity assets name `apps/web` in a comment, which D148 reads as a reach. New | Confirmed; S06 T054 | open |
| A4 | A | MEDIUM | A non-UTF-8 path crashes the run with a traceback (fails closed, no verdict). New | Confirmed; S06 T052 | open |
| A5 | A | LOW | A path with a newline forges `verify-scoped:` lines. New | Confirmed; S06 T052 | open |
| B5 | B | LOW | Obligation and check names, and a hand-written baseline's branch, print raw control characters. New | Confirmed; S06 T052 | open |
| B3 | B | LOW | A deeply nested baseline or stamp crashes with `RecursionError` instead of the full gate. New | Confirmed; S06 T052 | open |
| B4 | B | LOW | An unhashable obligation component does not name the entry. New | Confirmed; S06 T052 | open |
| A7 | A | LOW | A `../` string that is not a path (a traversal test's input) is a reach with wrong words. New | Confirmed; S06 T055 | open |
| C2 | C | LOW | With two Go services the scoped order lets one service's lint run beside another's test (D96's order is whole-gate). New | Confirmed; S06 T055 | open |
| C3 | C | LOW | `-l`/`--load-average` is refused by D146's allowlist though it adds no text. New | D152; S06 T055 | open |
| B8 | B | LOW | Under `MAKEFILES` the scoped run's fallback runs `make -f <that file> verify` and fails with *No rule*. New | Confirmed; S06 T049 | open |
| B6 | B | LOW | A failed full run under a CI marker leaves the baseline; AC-S06-9 and D116 rule 6 differ. No false green: a CI machine's baseline is never read locally | Declined: D116 rule 6 stands; the cruise report | declined |
| B7 | B | LOW | 20,000 obligations take 17 s. New | Declined: nobody writes that list | declined |
| C4 | C | LOW | SIGTERM to the outer make orphans the sub-make, which keeps running checks. Older (S04's `make verify` does the same) | Declined: not this slice's; the cruise report | declined |
| C5 | C | unverified | GNU Make 3.81 may print the `override` origin in backtick style, which `record.py`'s pattern would miss (read, not run). Older class (S04's 3.81 lines) | The cruise report | parked |

## S08 · 3138416 · 2026-10-06

Slice `S08-scoped-mutation` (cruise iterations 22–24), diff `66e49e8..3138416` (merged into adopt-method at `3138416`): the generated `make mutation` scoped to the change and `make mutation-full` as the sweep (`src/slipwai/project/mutation.py`, `src/slipwai/project/native_commands.py`, `src/slipwai/project/makefile.py`), the toolkit script that decides and runs the scope (`assets/toolkit/scripts/mutation-scope.py`), Go's `--file` and report reading (`assets/languages/go/scripts/go-mutation.py`), the mutation skill's commands, one fragment.

| Trigger | Status | Evidence |
|---|---|---|
| driving adapter (HTTP route, CLI command, queue consumer) | widened | `make mutation` changes from the sweep to a scoped run on a slice branch and under `SINCE`; `make mutation-full` is new (`src/slipwai/project/mutation.py`, `assets/toolkit/scripts/mutation-scope.py`) |
| driven adapter or the provider types behind one | widened | The script drives git (merge-base, diff, ls-files, unpushed commits), make (`mutation-full`, `-n`/`-q`/`-t`, `MAKEFLAGS`), Gremlins through `go-mutation.py` and its report, and PIT through `./mvnw` with `-DtargetClasses` (`assets/toolkit/scripts/mutation-scope.py`, `assets/languages/go/scripts/go-mutation.py`) |
| authorisation decision (who can reach one that already exists) | not present | The diff decides nothing about who may do what |
| concurrency, idempotency, ordering, retention, or time | not present | One run, one tool at a time; the stamp is untouched (`tests/test_mutation_stamp_untouched.py`) |

Not the slice that closes the split; `--full` not passed. A pass is owed: two triggers `widened`.

Spawned: seam A — what the scoped run counts as changed (git refs, paths, renames, a project in a subdirectory, unpushed trunk commits, git configuration and environment) · `drive-adversary` · claude-opus-5-5 (host model) · delegated, fresh context · manifest: `assets/toolkit/scripts/mutation-scope.py`, `assets/toolkit/scripts/check-slice-scope.py`, `assets/toolkit/scripts/verify_scoped/changes.py`, `assets/toolkit/scripts/verify-stamp.py`, `src/slipwai/project/mutation.py`, `tests/mutation_scope_fixture.py`, `tests/test_mutation_change_set.py`, `tests/test_mutation_borders.py`, `tests/test_mutation_subdirectory.py`, `tests/test_mutation_unpushed.py`, `tests/test_mutation_sweeps.py`
Spawned: seam B — how the scoped run starts Gremlins and PIT and reaches its verdict (reports, exit codes, signals, the pom, `.gremlins.yaml`, `MAKEFLAGS`, the project's recipe) · `drive-adversary` · claude-opus-5-5 (host model) · delegated, fresh context · manifest: `assets/toolkit/scripts/mutation-scope.py`, `assets/languages/go/scripts/go-mutation.py`, `src/slipwai/project/mutation.py`, `src/slipwai/project/native_commands.py`, `src/slipwai/project/makefile.py`, `tests/mutation_scope_fixture.py`, `tests/test_mutation_uncovered.py`, `tests/test_mutation_recipe.py`, `tests/test_mutation_dry_run.py`, `tests/test_mutation_scope_go.py`, `tests/test_mutation_scope_spring.py`, `tests/test_pit_globs.py`, `tests/test_go_mutation_file.py`
Omitted: the known open converge and gaps tasks (T022–T025, T030–T032); GNU Make 3.81, Windows and macOS (not on this machine)
Findings: sixteen — seven `MEDIUM`, nine `LOW`; no `CRITICAL`. Five of them let changed code go unmeasured while the run says `passed` (A1, A2, A3, B1, B4), each reproduced against real PIT 1.25.9 or Gremlins 0.6.0. What held: hostile `SINCE` values (an option, spaces, `main -- x`, a tree, a path, `$(…)`); git configuration (`color.ui`, `diff.noprefix`, `diff.renames=false`, `core.quotePath`, `diff.relative`, `diff.external`, `status.showUntrackedFiles=no`); `GIT_DIR`, `GIT_WORK_TREE`, `GIT_INDEX_FILE`; a project in a subdirectory; a submodule and an intent-to-add file; file names with spaces, a leading dash, `$`, quotes, a newline, unicode; case variants of `slice/`; every dry-run form of make tried (`-n`, `-q`, `-t`, `MAKEFLAGS`, `GNUMAKEFLAGS`, with `-j`, `-l`, `--trace`, `--shuffle`); `SINCE` precedence between the command line and the environment; `go run`'s exit 10 to 1 (T034 holds); two Go services under `-k`, in order, piped.

| # | Seam | Severity | Finding | Triage | State |
|---|---|---|---|---|---|
| A1 | A | MEDIUM | A second top-level class in a changed `.java` file is never mutated: the class name comes from the path. The scoped run reports 100% and passes, while `make mutation-full` finds a survivor in it. New | Confirmed; S08 T036 | open |
| A2 | A | MEDIUM | A `.java` file whose `package` does not match its directory is judged by its path: outside the targets (skipped, passes) or a class that does not exist (PIT's *No mutations found* becomes *no mutant to run*). The sweep finds a survivor. New | Confirmed; S08 T036 | open |
| B4 | B | MEDIUM | Spring decides per file where PIT matches per class: a nested class of an exactly excluded class, and a second top-level class, are left out of the scoped report though the sweep reports them surviving. New | Confirmed; S08 T036 (A1's and A2's class) | open |
| A3 | A | MEDIUM | A change to PIT's configuration outside the first `pitest-maven` element (a profile's plugin, a property the block reads) does not sweep; the sweep finds survivors in a class the scoped run calls outside the targets. New | Confirmed; S08 T037 | open |
| B1 | B | MEDIUM | Gremlins stopped by a signal exits 0 with no report, which the scoped Go run reads as *no mutant to run* and passes while a lived mutant is on screen; the sweep fails the same case. New (T034's exit-0 branch) | Confirmed; S08 T038 | open |
| B2 | B | MEDIUM | `.gremlins.yaml`'s reader keeps the quotes of a quoted item that has a trailing comment, and refuses a comment after the key: the scoped run hands Gremlins a wrong exclusion and mutates what the project excluded, failing where the sweep passes. Older reader (`--since`), on by default now | Confirmed; S08 T039 | open |
| B3 | B | MEDIUM | Gremlins' efficacy threshold is applied to the scoped subset: a project that lowered it for one named equivalent mutant fails every scoped run that touches that file, though the sweep passes. Older mechanism (`--since`), on by default now | Question: D155; S08 T040 | open |
| A4 | A | LOW | A new production file git does not list as untracked — ignored, or inside a nested repository — is never counted (*no production file changed*, passes), though the sweep mutates it. New | Confirmed; S08 T042 | open |
| A5 | A | LOW | With the Makefile named by an absolute path a change to the `mutation` rule's target line does not sweep. New | Confirmed; S08 T041 | open |
| A6 | A | LOW | A file deleted by an unpushed trunk commit (D153) is scoped as changed rather than named deleted. New | Confirmed; S08 T042 | open |
| A7 | A | LOW | An `exclude-files` pattern Go accepts and Python cannot compile crashes the scoped run with a traceback. New | Confirmed; S08 T043 | open |
| A8 | A | LOW | `SINCE=:/<message>` is refused though git resolves it (fails loudly). New | Confirmed; S08 T042 | open |
| B5 | B | LOW | A `mutation-full` recipe overridden from an included makefile is not what the scoped run runs. New; T025(b)'s sibling | Confirmed; S08 T041 | open |
| B6 | B | LOW | `MAKEFILES` in the environment makes `make mutation` say the recipe is not the factory's and then fail with *No rule*. New | Confirmed; S08 T041 | open |
| B7 | B | LOW | A run that starts no tool leaves an earlier `gremlins.json` in place, which the note says the next run replaces. Older file behaviour, met more often now | Confirmed; S08 T044 | open |
| B8 | B | LOW | Read, not run: two `pitest-maven` elements (`pluginManagement` and `plugins`) are read as the first only; a Kotlin source under `src/main/kotlin` is `other` and never counted. New | Confirmed; S08 T037 (two blocks), S08 T036 (Kotlin) | open |

## S14 · 37cdf3f · 2026-10-06

Slice `S14-result-contract` (cruise iterations 22–24), diff `ee0a167..37cdf3f` (merged into adopt-method at `37cdf3f`): the result-contract block every delegate hands back, the record each is appended to and the coverage check over them (`assets/toolkit/scripts/hand_backs.py`, `assets/toolkit/scripts/check-decisions.py`'s `--hand-back` and `--hand-backs`), the benchmark's reading of which delegates ran (`assets/toolkit/scripts/agents/benchmark.py`), the brief paragraphs spliced into every agent and command (`src/slipwai/project/result_contract.py` and its callers), the page `assets/toolkit/docs/result-contract.md`, one fragment.

| Trigger | Status | Evidence |
|---|---|---|
| driving adapter (HTTP route, CLI command, queue consumer) | widened | Two new verbs of the decisions check a host and a delegate run, `--hand-back` (reads a delegate's reply on stdin) and `--hand-backs` (coverage over a slice) (`assets/toolkit/scripts/check-decisions.py`, `assets/toolkit/scripts/hand_backs.py`) |
| driven adapter or the provider types behind one | widened | The verbs append to a slice's record file and read the benchmark record and its delegates (`assets/toolkit/scripts/hand_backs.py`, `assets/toolkit/scripts/agents/benchmark.py`) |
| authorisation decision (who can reach one that already exists) | not present | The diff decides nothing about who may do what |
| concurrency, idempotency, ordering, retention, or time | widened | A retried hand-back is not appended twice; several delegates append to one record (`assets/toolkit/scripts/hand_backs.py`) |

Not the slice that closes the split; `--full` not passed. A pass is owed: three triggers `widened`.

Spawned: seam A — the two verbs and the record they write (stdin, arguments, the record file, retries, two appends at once, the benchmark record coverage reads) · `drive-adversary` · claude-opus-5-5 (host model) · delegated, fresh context · manifest: `assets/toolkit/scripts/hand_backs.py`, `assets/toolkit/scripts/check-decisions.py`, `assets/toolkit/scripts/agents/benchmark.py`, `assets/toolkit/docs/result-contract.md`, `tests/hand_backs_fixture.py`, `tests/test_hand_backs_append.py`, `tests/test_hand_backs_record.py`, `tests/test_hand_backs_shape.py`, `tests/test_hand_backs_coverage.py`
Spawned: seam B — what reaches a generated or adopted project and through `migrate` (every brief, every harness projection, both layouts, the gate before and after) · `drive-adversary` · claude-opus-5-5 (host model) · delegated, fresh context · manifest: `src/slipwai/project/result_contract.py`, `src/slipwai/project/agents.py`, `src/slipwai/project/commands.py`, `src/slipwai/project/converge_stage.py`, `src/slipwai/project/cruise.py`, `src/slipwai/project/cruise_agents.py`, `src/slipwai/project/docs_index.py`, `assets/toolkit/docs/result-contract.md`, `assets/toolkit/scripts/check-decisions.py`, `changelog.d/result-contract.md`, `tests/test_result_contract_briefs.py`, `tests/test_result_contract_migrate.py`
Omitted: the known open tasks T021–T028; harnesses with no agent file of their own (the brief never reaches their delegates — older, and those stages read as *could not attribute*)
Findings: fourteen — two `HIGH`, five `MEDIUM`, seven `LOW`; no `CRITICAL`. What held: two processes appending 200 KB blocks raced eight times without interleaving; several blocks, an unclosed block, a body that is not a JSON object refused; a `delegate` that differs from the agent refused; every hostile slice-folder argument refused with exit 2; a record that is a directory, CRLF, no trailing newline, truncated mid-entry; every brief in five generated shapes and six harness projections carries the section, the Codex TOML parses, the Claude projection is byte-identical; a clean `migrate` in both layouts with `check-agents`, `check-benchmark` and `check-decisions` green and `make verify` passing after it; `check-decisions` over this repository's real records byte-identical between the old and new script.

| # | Seam | Severity | Finding | Triage | State |
|---|---|---|---|---|---|
| A1 | A | HIGH | `--hand-back-missing` writes its reason without refusing line breaks: a multi-line reason forges a backdated block that coverage counts, an innocent one turns the gate red for good (the record is append-only), a fence in it swallows the next entry. New | Confirmed; S14 T029 | open |
| B1 | B | HIGH | Coverage counts an entry only inside its stage's benchmark window; a continuation always comes after the window closed, so the finding AC-S14-11 says one continuation or a `Missing:` closes can never close. New | Question: D160; S14 T030 | open |
| A2 | A | MEDIUM | The retry check compares with the last entry of that type and stage in any window, so a later pass's identical `Missing:` reason or block is dropped as a retry. New | Question: D160; S14 T030 | open |
| B2 | B | MEDIUM | After `migrate`, stages that ran before the contract existed are graded as missing hand-backs by converge and counted `0 of m` by `make benchmark`, which the catch-up does not say. New | Question: D161; S14 T031 | open |
| B3 | B | MEDIUM | `commands/adversary.md`, which owns the adversary pass, never tells the session to record the adversaries' blocks before closing the entry. New | Confirmed; S14 T032 | open |
| A3 | A | MEDIUM | On Codex every delegated stage reads as not delegated, so coverage owes nothing and says nothing, where AC-S14-15 says it must say it could not attribute. New | Confirmed; S14 T033 | open |
| A4 | A | MEDIUM | `--hand-back` decodes stdin with the locale encoding, so a non-UTF-8 locale records a delegate's em dash as mojibake and the gate passes it. New | Confirmed; S14 T034 | open |
| A5 | A | LOW | A stage window includes both ends, so one block at the second two stages meet covers both. New | Question: D160; S14 T030 | open |
| A6 | A | LOW | A damaged `benchmark.json`, a record ending mid-UTF-8, invalid stdin or a deeply nested body give a traceback instead of the page's exits; a stage with no `started` takes every earlier entry. New | Confirmed; S14 T035 | open |
| A7 | A | LOW | A block quoted inside a `~~~` fence is recorded as the delegate's own. New | Duplicate of T024 (CommonMark fences, tildes in its sweep) | open |
| B4 | B | LOW | A `~~~result-contract` fence is refused, though the brief does not say backticks. New | Duplicate of T024 | open |
| A8 | A | LOW | A block reading `{"contract": 2}` passes the verb with no field checked and counts as covered. New | Question: D162; S14 T036 | open |
| B6 | B | LOW | An `unavailable` skipper answer cites a `D<n>` the host may never write, and the verb refuses the block. New (read, not run) | Question: D163; S14 T037 | open |
| B5 | B | LOW | On harnesses with no agent file of their own the instruction never reaches a delegate. Older (the safety page is the same) | Declined: not this slice's; those stages read as *could not attribute*; the cruise report | declined |

## S39 · 02cf1ed · 2026-10-06

Slice `S39-benchmark-elapsed` (cruise iterations 22–25), diff `525399b..02cf1ed` (merged into adopt-method at `02cf1ed`): elapsed ready-to-accepted time read from git, waiting by cause read from the cruise log and the records, stage time with cut-off entries ended at their last transcript line (`assets/toolkit/scripts/agents/measures.py`), each request charged to one slice by the harness's spawn chain and cost with rework (`assets/toolkit/scripts/agents/attribution.py`), the overview and `--json` that print them and the new `gate` stage (`assets/toolkit/scripts/agents/benchmark.py`), the ladder text that asks for `drive-slice <id>` descriptions and the gate bracket (`src/slipwai/project/benchmark.py`, `src/slipwai/project/cruise.py`, `src/slipwai/project/parallel_slices.py`), one fragment.

| Trigger | Status | Evidence |
|---|---|---|
| driving adapter (HTTP route, CLI command, queue consumer) | widened | `benchmark.py`'s overview and `--json` change shape (`rework` an object, `reentered`, `feature_figures`, `session_totals`, `decision_health`, `read_from`, `unattributed_person`) and `start`/`end` take a new stage `gate` (`assets/toolkit/scripts/agents/benchmark.py`) |
| driven adapter or the provider types behind one | widened | New readers of git history (ready, accepted and merged commits, every local branch's copy of a record), of `specs/cruise-log.jsonl`, of the harness's transcripts and sub-agent metadata (`assets/toolkit/scripts/agents/measures.py`, `assets/toolkit/scripts/agents/attribution.py`) |
| authorisation decision (who can reach one that already exists) | not present | The diff decides nothing about who may do what |
| concurrency, idempotency, ordering, retention, or time | widened | Elapsed and waiting are claims about time and ordering (windows, overlaps, cut-off ends, a park's span); figures must not double-count across branches or overlapping brackets (`assets/toolkit/scripts/agents/measures.py`, `assets/toolkit/scripts/agents/attribution.py`) |

Not the slice that closes the split; `--full` not passed. A pass is owed: three triggers `widened`.

Spawned: seam A — the time measures (elapsed, waiting by cause, stage time, the merge, the cruise log, git's history) · `drive-adversary` · claude-opus-5-5 (host model) · delegated, fresh context · manifest: `assets/toolkit/scripts/agents/measures.py`, `assets/toolkit/scripts/agents/benchmark.py`, `tests/elapsed_fixture.py`, `tests/test_benchmark_elapsed.py`, `tests/test_benchmark_elapsed_cutoff.py`, `tests/test_benchmark_elapsed_done_mark.py`, `tests/test_benchmark_elapsed_merged.py`, `tests/test_benchmark_waiting.py`, `tests/test_benchmark_waiting_park.py`, `tests/test_benchmark_waiting_person.py`, `tests/test_benchmark_feature.py`, `tests/test_benchmark_pin.py`
Spawned: seam B — cost by spawn chain, the printed contract and `migrate` (transcripts, sub-agent metadata, sessions, `--json`, a project made before the slice) · `drive-adversary` · claude-opus-5-5 (host model) · delegated, fresh context · manifest: `assets/toolkit/scripts/agents/attribution.py`, `assets/toolkit/scripts/agents/benchmark.py`, `assets/toolkit/scripts/agents/measures.py`, `src/slipwai/project/benchmark.py`, `src/slipwai/project/cruise.py`, `src/slipwai/project/parallel_slices.py`, `changelog.d/benchmark-elapsed.md`, `tests/test_benchmark_attribution.py`, `tests/test_benchmark_attribution_chain.py`, `tests/test_benchmark_attribution_gaps.py`, `tests/test_benchmark_elapsed_migrate.py`, `tests/test_benchmark_notes.py`, `tests/test_benchmark_brackets.py`
Omitted: the actor's open page notes T040–T042 (known, LOW); the ladder prose (no claim it can break beyond the description convention seam B covered)
Findings: eighteen — two `HIGH`, seven `MEDIUM`, nine `LOW`; no `CRITICAL`. What held: worked plus the five causes equals elapsed exactly on all 16 real slices; overlapping brackets counted once; CRLF, a truncated last line, a byte-order mark and non-UTF-8 bytes in the cruise log read `unknown` naming the line; a shallow clone and a directory that is no repository read `unknown`; only `%ct` epoch seconds are read, so timezones skew nothing; a catch-up merge into the slice is excluded and octopus merges name each slice; every git call but A5's lazy fetch is read-only and ids cannot be injected as options; `S3`/`S33` and `S10`/`S10a` resolve apart, case and two-slice descriptions go to shared with a note; chain loops and bad metadata terminate; 60 records, 300 brackets and 162k requests in 8.2 s with tokens conserved; `--json` holds its shape on an empty tree; a project made at `525399b` migrates with `make check-benchmark` byte-identical and every record unchanged.

| # | Seam | Severity | Finding | Triage | State |
|---|---|---|---|---|---|
| A1 | A | HIGH | *Merged* matches `slice/<id>` anywhere in a first-parent merge subject, so a sibling's merge that mentions the slice, a `slice/<id>-v2` retry, or a merge later reverted is taken as the slice's merge, charging days to integration. New | Confirmed; S39 T043 | fixed `5ac06ee` |
| B1 | B | HIGH | Claude Code copies earlier requests into another session's transcript with the same `requestId`; requests are de-duplicated only within a session, so one request is charged to two slices and the session totals double. New | Confirmed; S39 T051 | fixed `d685bfc` |
| A2 | A | MEDIUM | The feature's elapsed is built from slices whose own figures are contradicted (accepted before ready), and can print negative. New | Confirmed; S39 T044 | fixed `ff8fd55` |
| A3 | A | MEDIUM | One non-UTF-8 byte in any historical copy of the split, the register or the model makes the whole benchmark exit 1. New (regression) | Confirmed; S39 T045 | fixed `0168e32` |
| A4 | A | MEDIUM | With no `git` on PATH the run exits 1 instead of reading `unknown`, as the fragment promises. New (regression) | Confirmed; S39 T045 | fixed `0168e32` |
| A5 | A | MEDIUM | In a partial (blobless) clone each historical read fetches over the network into `.git/objects`, with no time limit — a hanging remote stalls a cruise run. New | Confirmed; S39 T045 | fixed `0168e32` |
| B2 | B | MEDIUM | A streamed response's lines share one `requestId` with growing `output_tokens`; the first line is kept, so output tokens read about 3.3 times too low. Older (`claude_usage` at `end`), copied into S39 | Confirmed; S39 T048 (the stage `end` path), T051 (attribution) | fixed `f791776`, `d685bfc` |
| B3 | B | MEDIUM | A broken spawn chain (a `drive-slice`'s metadata absent or corrupt, a parent that resolves nowhere) sends a child's requests to another slice's host bracket with no note, where the contract says shared. New | Confirmed; S39 T052 | fixed `faecc82` |
| B4 | B | MEDIUM | Tokens leak across features: a session with one feature's brackets is wholly that feature's while chain attribution charges another feature's record, so neither feature's totals add up; a slice id repeated across features resolves to the first in path order. New | Confirmed; S39 T053 | fixed `4ca8ee2` |
| B5 | B | MEDIUM | An entry that falls back to its recorded usage still has its live requests counted again (in shared, or by the chain), breaking conservation. New | Confirmed; S39 T053 | fixed `4ca8ee2` |
| A6 | A | LOW | A dependency marked done in the same commit as its dependant gives the dependant `0s` elapsed beside hours of its own brackets, with no note. New | Confirmed; S39 T044 | fixed `ff8fd55` |
| A7 | A | LOW | A bracket that ends before it starts gives negative stage time. Older | Confirmed; S39 T046 | fixed `224eeb6` |
| A8 | A | LOW | An accepted demo with an unreadable `ended` crashes with a traceback. New | Confirmed; S39 T046 | fixed `224eeb6` |
| A9 | A | LOW | A cruise log whose rows are out of time order makes a park vanish from the person's wait, counted as worker. New | Confirmed; S39 T047 | fixed `e2cfa37` |
| A10 | A | LOW | An inherited `GIT_DIR` is followed and another repository's history read. Older | Declined: needs an environment nobody runs the benchmark in, and the toolkit's git callers all share it; Parking Lot | declined |
| B6 | B | LOW | A record with no ended bracket reads `cost.tokens: 0` where nothing was read, against *never a bare 0*. New | Confirmed; S39 T049 | fixed `66cc431` |
| B7 | B | LOW | One unreadable metadata or transcript file, a dangling link, a line that is a JSON array, or a `parentAgentId` with `/` stops the whole report. New | Confirmed; S39 T054 | fixed `4e59e52` |
| B8 | B | LOW | The catch-up omits `scripts/test_benchmark.py`, which `migrate` changes; a description like `drive-slice S1-alpha (resumed)` reads as naming no slice. New | Confirmed; S39 T050 (fragment), T054 (description) | fixed `299b6bb`, `4e59e52` |

## S38 · 5600fb9 · 2026-10-06

Slice `S38-factory-test-selection` (cruise iterations 17–26), diff `8072724..5600fb9^2` (merged into adopt-method at `5600fb9` by a person, with their root `Makefile` commit `75150f9`): `make test` on a slice branch runs the factory modules the change can reach and says which and why (`scripts/select-tests.py`, `scripts/select_tests/`), `SINCE=<ref>` and `FULL=1`, `make verify` and `verify-checks` always whole (`Makefile`), module declarations (`reads`, `configurations`) on the suite's modules (`tests/test_*.py`), `docs/maintaining.md`. Reaches no user: the factory's own suite.

| Trigger | Status | Evidence |
|---|---|---|
| driving adapter (HTTP route, CLI command, queue consumer) | widened | `make test` now runs `scripts/select-tests.py` with `SINCE`, `FULL`, `TESTS`, `SKIP`, `--dry-run`; `verify` and `verify-checks` pass `FULL=1` (`Makefile`, `scripts/select-tests.py`) |
| driven adapter or the provider types behind one | widened | New readers of git (base resolution, the range's and the working tree's changes, ignored files, the root makefiles' bytes) and of each module's declarations and imports (`scripts/select_tests/__init__.py`, `base.py`, `declarations.py`, `loaded.py`, `generation.py`, `rules.py`) |
| authorisation decision (who can reach one that already exists) | not present | The diff decides nothing about who may do what |
| concurrency, idempotency, ordering, retention, or time | not present | The selection is a function of the tree and the diff against one base; it keeps no state between runs and reads no clock (`scripts/select_tests/`) |

Not the slice that closes the split; `--full` not passed. A pass is owed: two triggers `widened`.

Spawned: seam A — the change set and the whole gate (base resolution, git's view, the root makefiles, `SINCE`/`FULL`/`TESTS`/`SKIP`, `verify` and `verify-checks` whole, what reaches a child) · `drive-adversary` · claude-opus-5-5 (host model) · delegated, fresh context · manifest: `Makefile`, `scripts/select-tests.py`, `scripts/select_tests/__init__.py`, `scripts/select_tests/base.py`, `scripts/select_tests/report.py`, `scripts/select_tests/choose.py`, `tests/select_fixture.py`, `tests/select_fixture_declare.py`, `tests/test_select_tests_make.py`, `tests/test_select_tests_makefile.py`, `tests/test_select_tests_base.py`, `tests/test_select_tests_changes.py`, `tests/test_select_tests_full.py`, `tests/test_select_tests_paths.py`, `tests/test_select_tests_environment.py`, `tests/test_select_tests_replay.py`, `tests/test_select_tests_pin.py`, `tests/test_select_tests_report.py`, `tests/test_factory_repository.py`
Spawned: seam B — what a change reaches (declarations, imports, generation reads, cross-reads, the skip reason) · `drive-adversary` · claude-opus-5-5 (host model) · delegated, fresh context · manifest: `scripts/select_tests/declarations.py`, `scripts/select_tests/generation.py`, `scripts/select_tests/loaded.py`, `scripts/select_tests/rules.py`, `scripts/select_tests/choose.py`, `scripts/select-tests.py`, the declarations on `tests/test_*.py`, `src/slipwai/project/`, `src/slipwai/examples.py`, `src/slipwai/toolkit.py`, `catalog.json`, `assets/`, `tests/test_select_tests_declarations.py`, `tests/test_select_tests_cross_reads.py`, `tests/test_select_tests_generation.py`, `tests/test_select_tests_go_app.py`, `tests/test_select_tests_imports.py`, `tests/test_select_tests_narrow.py`, `tests/test_select_tests_subpackages.py`, `tests/test_select_tests_caches.py`, `tests/test_select_tests_real_*.py`
Omitted: the actor's demo-2 notes T047–T049 (known, LOW); `docs/maintaining.md` (prose, no boundary)
Findings: thirteen — three `HIGH`, three `MEDIUM`, seven `LOW`; no `CRITICAL`. None is reachable as a false green in today's tree: every declaration of the 15 declared modules held under an audit hook, 60 generated configurations opened nothing claimed only by another backend, and `make verify`/`verify-checks` stayed whole for every goal order and `FULL` value tried. The `HIGH`s are guards a later edit walks past. What held: tags, future commits, orphans, trees, blobs and `:/msg` as `SINCE`; `FULL=0` and `FULL=' '` run full; `make test verify-checks` runs a scoped pass then a full one; mode changes, `assume-unchanged`, `skip-worktree`, symlink swaps, paths with spaces, newlines, non-UTF-8 bytes and a leading dash; an untracked or ignored `GNUmakefile`/`makefile`; linked worktrees; malformed declarations (missing path, `..`, absolute, non-literal, duplicate, unknown axis or option, a computed import) run the module; every skip reason printed was true.

| # | Seam | Severity | Finding | Triage | State |
|---|---|---|---|---|---|
| A1 | A | HIGH | The change-set scripts run from the working tree judge their own change: a regression in `verify_scoped/changes.py` committed beside a test edit narrows the run and skips that test. New | Confirmed; S38 T050 | fixed `4044de8` |
| B1 | B | HIGH | A generating module that reads the repository by a relative path (`Path("AGENTS.md")`, a subprocess with no `cwd`) keeps its declaration, so a change there skips it. New, latent | Confirmed; S38 T053 | fixed `2a7f2dd`, `06873a4` |
| B3 | B | HIGH | The reads-only audit drops paths under `tests/` and does not see subprocesses, so a fixture read or a script run passes it and its change skips the module. New, latent | Confirmed; S38 T055 | fixed `675c65e` |
| A2 | A | MEDIUM | `SINCE:=`/`SINCE::=` and a spaced value survive `without_knobs`; on the `TESTS`/`SKIP` path `SINCE` and `verify`'s `FULL=1` reach the modules, and a generated project's `make mutation` reads `SINCE`. New | Confirmed; S38 T051 | fixed `d9d7bbd` (residual: a module importing neither `tests/support.py` nor the selector — the verify-stamp modules — still sees `SINCE` under an explicit `make test TESTS=… SINCE=…`; Parking Lot) |
| B2 | B | MEDIUM | `names()` holds a read by any suffix of a `reads` entry, and `./README.md` is a valid entry, where the selector matches by prefix: a declaration held by a path the selector never matches. New, latent | Confirmed; S38 T054 | fixed `917a4bc` |
| B4 | B | MEDIUM | `from tests.support import X` records `tests`, so a change to the helper skips a declared module importing it so. New, latent | Confirmed; S38 T056 | fixed `d837e74` |
| A3 | A | LOW | A `git remote` that fails reads as no remote, dropping the trunk's unpushed commits from the change set. Older (`assets/toolkit/scripts/verify_scoped/changes.py`) | Declined: older generated-project code, needs a git that fails for `remote` alone; Parking Lot | declined |
| A4 | A | LOW | A hanging git hangs `make test` silently: `check-slice-scope.run_git` has no time limit. Older | Declined: fails safe (never green), older generated-project code; Parking Lot | declined |
| A5 | A | LOW | `make verify TESTS=x` prints `verify: all gates passed` after a partial run. Older (the same on `main`) | Declined: it now prints `selection off: TESTS given` first; the override is the person's | declined |
| A6 | A | LOW | `MAKE=true` in the environment makes `verify-checks` pass with no test run. New (recursion) | Declined: redefining make's own variable defeats every recursive make; common values (`make -j8`) fail safe | declined |
| A7 | A | LOW | `MAKEFILES=x.mk` makes `verify-checks` fail with no rule for `test`. New | Declined: fails safe | declined |
| A8 | A | LOW | A slice branch with no commits of its own is reported as *HEAD is not on a branch*. New | Confirmed; S38 T052 | fixed `792ed9a` |
| A9 | A | LOW | Ignored files outside `assets/`, `src/`, `tests/` never make a run full (research R-6). New | Declined: no declared module reads such a directory; R-6 chose it | declined |

## S26 · 3b8ee69 · 2026-10-07

Slice `S26-reversibility-line` (cruise iteration 27), diff `063c187..3b8ee69^2` (merged into adopt-method at `3b8ee69`): every decision entry may carry `Reversibility:`, scored by the new verb `assets/toolkit/scripts/reversibility.py` from declared facts, `Scope:` and `Written to`; `check-decisions` holds the line and `Proposed rule:` citations; generated projects carry `.slipwai/propagated`.

| Trigger | Status | Evidence |
|---|---|---|
| driving adapter (HTTP route, CLI command, queue consumer) | widened | A new CLI, `scripts/reversibility.py` (facts as `key=value`, `--scope`, `--written-to`, `--raise`), run by the host and the skipper; `check-decisions` reads two new labels from every log |
| driven adapter or the provider types behind one | widened | New readers of `.slipwai/propagated` and `<delivery>/.written`, and of each entry's `Scope:` and `Written to`; `generate` and `migrate` write and carry the list (`src/slipwai/project/propagated.py`) |
| authorisation decision (who can reach one that already exists) | not present | The tier decides nothing yet: nothing acts on it until `S27` |
| concurrency, idempotency, ordering, retention, or time | not present | The verb and the gate are functions of the text and the committed list; rules versions are frozen by digest, and nothing reads a clock |

Not the slice that closes the split; `--full` not passed. A pass is owed: two triggers `widened`.

Spawned: seam A — the scoring verb and the committed lists it reads (CLI inputs, paths, `--raise`, the briefs' commands) · `drive-adversary` · claude-opus-5-5 (host model) · delegated, fresh context · manifest: `assets/toolkit/scripts/reversibility.py`, `src/slipwai/project/propagated.py`, `cruise_record.py`, `cruise_agents.py`
Spawned: seam B — the gate over a log (grammar, re-derivation, notes, citations, fences, an old project migrated) · `drive-adversary` · claude-opus-5-5 (host model) · delegated, fresh context · manifest: `assets/toolkit/scripts/check-decisions.py`, `assets/toolkit/scripts/reversibility.py`, `assets/toolkit/scripts/agents/measures.py`
Omitted: the actor's demo notes (quickstart steps 6, 8, 9; `--help`) — known, LOW, Phase 4 tasks
Findings: twelve — one `HIGH`, three `MEDIUM` (one found by both seams), seven `LOW` (one found by both); no `CRITICAL`. Every one is new in S26 except the byte-order-mark count, which D65 settled.

| # | Seam | Severity | Finding | Triage | State |
|---|---|---|---|---|---|
| A1 | A, B | HIGH | An absolute or `..` `Written to` path to a listed file is never found on the committed list, so `migrate_file=no` scores `easy` and the gate passes it. New | Confirmed; S26 T020 | fixed `b8f5b90` |
| A2 | A, B | MEDIUM | Bare paths beside a backticked one, and `;`, `and` or a glob as separators, are never looked up on the list: a listed file written that way scores `easy`. New use of an older reader | Confirmed; S26 T021 | fixed `45e81db` |
| B1 | B | MEDIUM | A log with a `Proposed rule:` line and no `Reversibility:` line, written by hand before this release, turns red after `migrate` (D65). New | Confirmed; S26 T022: citations are held only in a log carrying a `Reversibility:` line, a note otherwise | fixed `61775d6` |
| B2 | B | MEDIUM | `measures.py` counts a fenced `Reversibility:` line the gate skipped, so an unchecked tier reaches decision health. New (S39's reader against S26's gate) | Confirmed; S26 T023 | fixed `8a73dad` |
| A3 | A | LOW | A listed path spelled in another case is not found on a case-insensitive filesystem. New | Confirmed; S26 T020 (the lookup only ever raises, so it folds case) | fixed `b8f5b90` |
| A4 | A | LOW | A damaged list fails open: an empty or comment-only list names nothing, a byte-order mark drops the first entry, a listed directory does not cover files under it. New | Confirmed; S26 T020 | fixed `b8f5b90` |
| A5 | A | LOW | `.slipwai/propagated` leaves out CI workflows, `AGENTS.md`, `.claude/settings.json` and `project.json`, which `migrate` also carries | Declined: D183 chose the method categories; `ci_workflow` covers workflows (ADR 0007) | declined |
| B4 | B | LOW | A near-miss label (`Reversibility :`, other case, `__…__`, `*` bullet) is checked or ignored depending on the rest of the file, silently. New | Confirmed; S26 T022: a near-miss label is a note naming the entry | fixed `61775d6` |
| B5 | B | LOW | A second `Proposed rule:` line in an entry is never read. New | Confirmed; S26 T022 | fixed `61775d6` |
| B7 | B | LOW | A `layout.delivery` holding a NUL byte crashes the gate with a traceback. New, contrived | Confirmed; S26 T020 | fixed `b8f5b90` |
| B8 | B | LOW | A log starting with a byte-order mark counts 0 entries, so its lines go unchecked. Older | Declined: D65 settled the counting before S26 | declined |

## S07 · d5e3351 · 2026-10-07

Slice `S07-scoped-checks` (cruise iteration 27), merged into adopt-method at `d5e3351` ahead of S43 (D193): `check-agents`, `check-speckit`, `check-extensions` and `check-constitution` get rows in S06's verification-dependency record, with the paths manifests, presets and installed integrations name derived at run time (`verify_scoped/methods.py`); `check-ux-gates` scopes previews by default on `slice/<id>` outside CI (`verify_scoped/since.py`), `UX_GATES_SINCE=all` renders every preview; an ignored projection directory with no files forces the full gate.

| Trigger | Status | Evidence |
|---|---|---|
| driving adapter (HTTP route, CLI command, queue consumer) | widened | `make verify-scoped` now skips four more checks; `make check-ux-gates` and `make verify` on a slice branch take a default preview scope; a new value of `UX_GATES_SINCE` |
| driven adapter or the provider types behind one | widened | New readers of Spec Kit manifests, `preset.yml`, `.specify/integration.json` with `registry.json`, the projection directories, and git's base and changed names (`-z --no-renames`) |
| authorisation decision (who can reach one that already exists) | not present | Nothing decides who may do what |
| concurrency, idempotency, ordering, retention, or time | not present | The record and the default are functions of the two trees and the base; nothing reads a clock or keeps state between runs beyond S06's baseline, unchanged |

Not the slice that closes the split; `--full` not passed. A pass is owed: two triggers `widened`.

Spawned: seam A — the four method-file checks under the scoped gate (rows, run-time derivation, projection directories, the check scripts) · `drive-adversary` · claude-opus-5-5 (host model) · delegated, fresh context · manifest: `assets/toolkit/scripts/verify_scoped/`, `assets/toolkit/scripts/check-speckit.py`, `check-constitution.py`, `scripts/agents/project.py`
Spawned: seam B — `check-ux-gates`' slice-branch default, its base and its keys · `drive-adversary` · claude-opus-5-5 (host model) · delegated, fresh context · manifest: `assets/toolkit/scripts/verify_scoped/since.py`, `check-ux-gates.py`, `verify-stamp.py`
Omitted: the actor's demo notes (quickstart prerequisites; wording of three lines) — known, LOW, Phase 4 tasks
Findings: eight — two `HIGH`, three `MEDIUM`, three `LOW`; no `CRITICAL`. Both `HIGH` are reproduced false greens: `make verify-scoped` passes a tree `make verify` fails.

| # | Seam | Severity | Finding | Triage | State |
|---|---|---|---|---|---|
| A1 | A | HIGH | A declared input that is a symlink (or sits under one) makes a check read a file no row names — a constitution moved behind a link, a skills projection linked outside the project — so the check is skipped while `make verify` fails. New | Confirmed; S07 T021: an input that is, or passes through, a symlink gives its check no recorded inputs, for every row of the record (closes S07's T013, the Parking Lot line) | fixed `342eefe` |
| A2 | A | HIGH | `check-agents` walks every file under `skills/`, `__pycache__/*.pyc` included, which the baseline's ignored digest exempts; a skill's own script run on the branch writes one and the scoped gate skips a check that then fails. New false green over an older exempt list | Confirmed; S07 T022: the projection never reads a path the stamp exempts (one shared list), and a test holds every recursive walk of a check to it | fixed `40c673e` |
| B1 | B | MEDIUM | A stylesheet linked without quotes (`href=app.css`) is never followed, so its change renders nothing on a slice branch. Older regex, now reached by default | Confirmed; S07 T023 | fixed `ac07338` |
| B2 | B | MEDIUM | An `@import` of a file name with a space is cut at the space. Older, now reached by default | Confirmed; S07 T023 | fixed `ac07338` |
| A3 | A | MEDIUM | `check-agents` crashes with a bare `UnicodeDecodeError` on any non-UTF-8 file under `skills/`. Older | Confirmed; S07 T022: one line naming the file | fixed `40c673e` |
| B3 | B | LOW | A percent-encoded `href` never matches its file. Older | Confirmed; S07 T023 | fixed `ac07338` |
| B4 | B | LOW | Run directly from inside another repository, `since.py` reads that repository's branch and scopes a trunk run. New | Confirmed; S07 T024: every git question in `since.py` runs at the project root | fixed `a3c88b3` |
| B5 | B | LOW | An uncommitted `ci.branch` in `project.json` retargets a slice's own base | Declined: `check-slice-scope` refuses a `project.json` edit on a slice branch, and CI renders every preview whatever the branch says | declined |


## S27 · f2d8473 · 2026-10-07

Slice `S27-provisional-decisions` (cruise iteration 28), diff `5f4fc00..f2d8473^2` (merged into adopt-method at `f2d8473`): `decide` gains `provisional-shadow`, `provisional-advisory` and `provisional`, climbed one rung at a time; a new verb `assets/toolkit/scripts/provisional.py` (`status`, `audit`) says what an always-ask entry's `Status:` and `Revert:` are; `check-decisions` holds the three new Status forms, `Revert:`, the rehearsal lines and FR-033's refusals (tier, facts, a closed list of paths); `agents/cruise.py` gains `mode`, a guard on `.specify/cruise.json` and the runner's park when `decide` moves inside an iteration; the command, the skipper's brief and the stop table say all of it.

| Trigger | Status | Evidence |
|---|---|---|
| driving adapter (HTTP route, CLI command, queue consumer) | widened | A new CLI, `scripts/provisional.py` (`status`, `audit`); `agents/cruise.py` gains `mode` and changes `--set`; `check-decisions` reads new labels from every log |
| driven adapter or the provider types behind one | widened | `mode` and `audit` read every feature's `decisions.md`; the runner reads `.specify/cruise.json` before and after each iteration; the guard reads the editing tool's target path |
| authorisation decision (who can reach one that already exists) | widened | The slice's whole point: under `provisional` an always-ask approval is taken without a person (FR-030), bounded by FR-033's refusals and by the run never setting `decide` (D62, D201, D203) |
| concurrency, idempotency, ordering, retention, or time | widened | Ratify-by dates computed from `When` (UTC, D199); `mode` orders mode entries by instant across logs (D202); the runner compares `decide` across an iteration (D203) |

Not the slice that closes the split; `--full` not passed. A pass is owed: four triggers `widened`.

Spawned: seam A — the verb and the gate over a log (`provisional.py status`, its protected list, `check-decisions` with what it loads, the audit) · `drive-adversary` · claude-opus-5-5 (host model) · delegated, fresh context · manifest: `assets/toolkit/scripts/provisional.py`, `assets/toolkit/scripts/check-decisions.py`, `assets/toolkit/scripts/reversibility.py`
Spawned: seam B — the setting and the run (`--set`, `mode`, `guard`, the runner's comparison, the generated text) · `drive-adversary` · claude-opus-5-5 (host model) · delegated, fresh context · manifest: `assets/toolkit/scripts/agents/cruise.py`, `src/slipwai/project/cruise_provisional.py`, `src/slipwai/project/cruise_agents.py`
Omitted: the actor's demo notes (quickstart steps 3, 4, 6, 7; the `decide` row; the Catch-up's `migrate_file=yes`) — known, LOW, Phase 4 tasks
Findings: twenty — nine `HIGH`, six `MEDIUM`, five `LOW`; no `CRITICAL`. All new in S27 but B9 and the byte-order mark.

| # | Seam | Severity | Finding | Triage | State |
|---|---|---|---|---|---|
| A1 | A | HIGH | A ratified entry with hard facts whose `Status` sits in a fence passes the gate and the audit. New | Confirmed; D210, S27 T038 | fixed `c717648` |
| A2 | A | HIGH | A near-miss `Status :` label with a fenced example elsewhere passes the gate holding hard facts. New | Confirmed; D210, T038 | fixed `c717648` |
| A3 | A | HIGH | `GNUmakefile` or `makefile`, which make reads ahead of `Makefile`, is not on the protected list. New | Confirmed; D210, T039 | fixed `8d83cf9` |
| A4 | A | HIGH | A protected path spelled absolute, with `..`, `././` or `//` passes. New | Confirmed; D210, T039 | fixed `8d83cf9` |
| A5 | A | HIGH | A bare protected path beside a backticked one passes. New | Confirmed; D210, T039 | fixed `8d83cf9` |
| A6 | A | HIGH | A second `Written to` line is never read. New on a held entry | Confirmed; D210, T039 | fixed `8d83cf9` |
| A7 | A | MEDIUM | A fenced `Status: standing` before the real provisional one: the gate holds the entry provisional, the audit does not. New | Confirmed; D210, T038 | fixed `c717648` |
| A8 | A | MEDIUM | A fullwidth digit in the heading: the gate reads the entry, the audit skips it. New | Confirmed; D210, T038 | fixed `c717648` |
| A9 | A | MEDIUM | An adopted layout's delivery directory (`<delivery>/scripts/…`) is protected only through S26's list. New | Confirmed; D210, T039 | fixed `8d83cf9` |
| A10 | A | LOW | The registry's hook projections, flag files and tool configurations a gate reads when present are off the list. New | Confirmed; D210, T039 | fixed `8d83cf9` |
| A11 | A | LOW | A log whose second `Status` is `reverted` turns red; a byte-order mark hides the first entry | Declined: a new-release Status form gets the new rules (D206); the mark is D65's | declined |
| B1 | B | HIGH | The `decide_moved` park resumes on any change, and the raised value becomes the baseline. New | Confirmed; D208, T040 | fixed `9048f71` |
| B2 | B | HIGH | A process an iteration leaves (`setsid`) raises `decide` after it ends, unseen; `mode` credits a person. New | Confirmed; D208, T040 | fixed `9048f71` |
| B3 | B | HIGH | A mode entry dated in the future becomes the baseline for ever. New | Confirmed; D209, T041 (gate), T042 (`mode`) | fixed `b76e635`, `9048f71` |
| B4 | B | MEDIUM | `provisional.py status --decide provisional` under `recommended-first` writes a provisional entry the gate accepts. New | Confirmed; D209, T041 | fixed `b76e635` |
| B5 | B | MEDIUM | A broken file hides a raise until a person's unrelated `--set` repairs it. New | Confirmed; D208, T040 | fixed `9048f71` |
| B6 | B | MEDIUM | `mode` without `--feature` in a project with two features exits 1, a stray last line every iteration. New | Confirmed; S27 T042 | fixed `9048f71` |
| B7 | B | LOW | A second `"decide"` key passes `check()`. New | Confirmed; T042 | fixed `9048f71` |
| B8 | B | LOW | A hard link or another case passes the guard (the runner's comparison then falls to B1). New | Confirmed; D208, T040 | fixed `9048f71` |
| B9 | B | LOW | An iteration may still `--set` `release`, `constitution`, `unblock`, `max_iterations`. Older | Declined to the Parking Lot: S27 holds `decide` (D62 for the rest is older prose) | declined |

## S41 · 7fbe7cb · 2026-10-08

Slice `S41-stryker-mutation` (cruise iteration 29), diff `b5e694f..7fbe7cb^2` (merged into adopt-method at `7fbe7cb`): every generated TypeScript service gets Stryker 10 behind a wrapper of its own (`assets/languages/typescript/scripts/stryker-mutation.py`), a checked-in `stryker.config.json`, the scope script's TypeScript rows, the twelve locks, ignore lines, the stamp's exempt rows and a MINOR fragment with a Catch-up.

| Trigger | Status | Evidence |
|---|---|---|
| driving adapter (HTTP route, CLI command, queue consumer) | widened | A new script a project runs (`scripts/stryker-mutation.py`) and new behaviour behind `make mutation` and `make mutation-full` for TypeScript |
| driven adapter or the provider types behind one | widened | The wrapper starts `npm ci` and `npm exec --no -- stryker run` and reads Stryker's `mutation.json` and the project's sources |
| authorisation decision (who can reach one that already exists) | unchanged | Nothing grants or checks access |
| concurrency, idempotency, ordering, retention, or time | widened | An install lock in the temporary directory; report and sandbox cleanup before each run; incremental results |

Not the slice that closes the split; `--full` not passed. A pass is owed: three triggers `widened`.

Spawned: seam A — the wrapper as a TypeScript project reaches it (verdict, excuses, `Incomplete`, the inert reader, install lock, hostile configs and arguments) · `drive-adversary` · claude-opus-5-5 (host model) · delegated, fresh context · manifest: `assets/languages/typescript/scripts/stryker-mutation.py`
Spawned: seam B — what scopes, sweeps, refuses or skips a TypeScript service, and what generation and `migrate` put in a project · `drive-adversary` · claude-opus-5-5 (host model) · delegated, fresh context · manifest: `assets/toolkit/scripts/mutation-scope.py`, `src/slipwai/project/stryker.py`
Omitted: the actor's demo-2 notes (the `Incomplete` line's remedy, the inert-file wording, Stryker's table before the verdict) — known, LOW, T035
Findings: fifteen — one `HIGH`, six `MEDIUM`, eight `LOW`; no `CRITICAL`. All new in S41 but B5's pattern, which the Go rows share.

| # | Seam | Severity | Finding | Triage | State |
|---|---|---|---|---|---|
| A1 | A | HIGH | `incremental: true` in a project's config reuses an earlier run's kills: a gutted test helper still passes. New | Confirmed; S41 T036 | open |
| A2 | A | MEDIUM | The inert reader reads a statement by how it begins: with no semicolons, code after an `import` or `type` line is hidden, and with `ignorePatterns` a file of real code is *no mutant to run*. New | Confirmed; T037 | open |
| A3 | A | MEDIUM | A `.d.ts` of `declare` statements or an `enum` without initialisers fails as code Stryker could mutate. New | Confirmed; T037 | open |
| A4 | A | MEDIUM | Two runs in one service: the second's cleanup deletes the first's report, and a scoped run whose Stryker crashed passes on the sweep's report. New | Confirmed; T038 | open |
| A7 | A | MEDIUM | A run killed by a signal leaves the install lock: the next waits fifteen minutes and does not name the lock; the lock is keyed by `TMPDIR`. New | Confirmed; T040 | open |
| B1 | B | MEDIUM | Stryker reads `stryker.conf.json` (and `.js`, `.mjs`, `.cjs`) ahead of `stryker.config.json`; the scope script reads only the factory's file, and `migrate` keeps a hand-wired one silently. New | Confirmed; T042 | open |
| B2 | B | MEDIUM | `make -j mutation-full build-packages` runs two `npm ci` on one `node_modules`: the wrapper's lock does not cover the Makefile's install target. New | Confirmed; T040 | open |
| A5 | A | LOW | A form feed or NEL shifts the wrapper's line count against Stryker's, so a reasoned comment two lines up excuses a mutant. New | Confirmed; T039 | open |
| A6 | A | LOW | Text in a template literal that looks like a next-line comment excuses a mutant a block comment ignored. New | Confirmed; T039 | open |
| A8 | A | LOW | A blank line or a doc comment between the next-line comment and its statement: Stryker honours it, the wrapper fails it. New | Confirmed; T039 | open |
| A9 | A | LOW | With `ignoreStatic: true`, static survivors read *Incomplete — a hook or a file failed*. Exit right, words wrong. New | Confirmed; T041 | open |
| A10 | A | LOW | Run from the service directory, the wrapper installs there and exits 2; a root-relative or absolute `--file` reads as outside the targets. New | Confirmed; T040 | open |
| B3 | B | LOW | A `.spec.ts`/`.test.ts` under `src/` that the mutate list matches is scoped as a test and never mutated, then fails the sweep. New | Confirmed; T043 | open |
| B4 | B | LOW | A move of the instrumenter's own dependencies (`@babel/*`, `weapon-regex`) in the lock does not sweep. New | Confirmed; D222, T044 | open |
| B5 | B | LOW | A deleted service's first line says the sweep runs, then the service is refused and nothing sweeps. Older pattern (the Go rows), newly reachable | Confirmed; T045 | open |

## S42 · 1f2a0b7 · 2026-10-08

Slice `S42-mutmut-mutation` (cruise iteration 30), diff `b9f16ef..1f2a0b7^2` (merged into adopt-method at `1f2a0b7`): every generated Python service gets `mutmut==3.8.0` in its dev group and a `[tool.mutmut]` table, a wrapper of its own (`assets/languages/python/scripts/mutmut-mutation.py`) taking one or several services, one combined Python `mutation-full` line (D223), the scope script's Python rows and sweep triggers, the four Python locks, the `apps/*/mutants/` ignore, stamp and `check-imports` rows, and a MINOR fragment with a Catch-up.

| Trigger | Status | Evidence |
|---|---|---|
| driving adapter (HTTP route, CLI command, queue consumer) | widened | A new script a project runs (`scripts/mutmut-mutation.py`) and new behaviour behind `make mutation` and `make mutation-full` for Python |
| driven adapter or the provider types behind one | widened | The wrapper starts `uv sync --locked`, mutmut's generation step and `mutmut run`, and reads mutmut's `.meta` files, `pyproject.toml` and `uv.lock` |
| authorisation decision (who can reach one that already exists) | not present | Nothing grants or checks access |
| concurrency, idempotency, ordering, retention, or time | widened | A per-service `flock`; a fresh `mutants/` before each run; several services in one run, failing at the end in service order |

Not the slice that closes the split; `--full` not passed. A pass is owed: three triggers `widened`.

Spawned: seam A — the wrapper as a Python project reaches it (verdict, stale and forged `.meta`, silencing and narrowing settings, environment, paths, several services, the lock, the version) · `drive-adversary` · claude-opus-5-5 (host model) · delegated, fresh context · manifest: `assets/languages/python/scripts/mutmut-mutation.py`, `src/slipwai/project/mutmut.py`, `assets/languages/python/app/pyproject.toml`, `tests/test_mutmut_*.py`
Spawned: seam B — what scopes, sweeps, refuses or skips a Python service, and what generation, `add-service` and `migrate` put in a project · `drive-adversary` · claude-opus-5-5 (host model) · delegated, fresh context · manifest: `assets/toolkit/scripts/mutation-scope.py`, `assets/toolkit/scripts/verify-stamp.py`, `assets/toolkit/scripts/check-imports.py`, `src/slipwai/project/{mutation,native_commands,mutmut,gitignore}.py`, `src/slipwai/project/languages/python.py`, `src/slipwai/backends.py`, `changelog.d/mutmut-mutation.md`, `tests/test_mutation_scope*.py`, `tests/test_mutmut_*.py`
Omitted: the default starter's survivors (D225, known; S45) · the OpenTelemetry `atfork` noise and mutmut's spinner (the demo's notes, LOW, known) · `add-service` on an older project (D224; S46)
Findings: twelve — four `HIGH`, five `MEDIUM`, five `LOW` counted with B2's pre-existing pattern; no `CRITICAL`. Reproduced against real mutmut 3.8.0 in scratch projects (seam A) and factory-generated projects (seam B).

| # | Seam | Severity | Finding | Triage | State |
|---|---|---|---|---|---|
| A1 | A | HIGH | A killed wrapper releases its `flock` while its `mutmut run` child lives on; the orphan writes its `.meta` results into the next run's fresh `mutants/`, which mutmut keeps — a weak suite reads `8 killed; passed`. New | Confirmed (3/3 reproductions); S42 Phase 4 | open |
| A2 | A | HIGH | A committed `.meta` file beside a source (or under `tests/`, copied by `also_copy`) is copied into `mutants/` and taken as the verdict: forged codes with matching hashes hide survivors; a ghost `.meta` makes an empty sweep pass. No check that every code is null after the wrapper's own generation step. New | Confirmed; S42 Phase 4 | open |
| A3 | A | MEDIUM | Narrowing the test selection (`pytest_add_cli_args_test_selection`, `tests_dir`, `-k`/`--deselect` in `pytest_add_cli_args`, pytest's own `addopts`, `PYTEST_PLUGINS` in the environment) turns survivors into `no tests`, which pass. New | Question → D227 | open |
| A4 | A | MEDIUM | A `mutmut` package on `PYTHONPATH` runs in place of the venv's 3.8.0 while `importlib.metadata` still reads 3.8.0; a patched copy makes a weak suite pass. New | Confirmed; S42 Phase 4 | open |
| A5 | A | MEDIUM | `do_not_mutate` / `only_mutate` drop whole files from the sweep with no line naming them. New | Question → D227 | open |
| A6 | A | LOW | With several services, one that could not start (exit 2) is reported as exit 1 and counted as swept. New | Question → D228 | open |
| A7 | A | LOW | An absolute `--file` path reads as *outside mutmut's configured targets* (exit 0); `also_copy = ["../x"]` copies outside `mutants/` and is never cleaned. From reading; unreproduced. New | Confirmed (by reading the code); S42 Phase 4 | open |
| B1 | B | HIGH | A changed module under a `source_paths` root other than `src/` is never scoped (`PRODUCTION_ROOT`/`python_kind` fix `src/`), though the wrapper and mutmut mutate it: `make mutation` passes with no mutant run. New | Confirmed; S42 Phase 4 | open |
| B2 | B | MEDIUM | `rule_of` matches only `mutation-full:`; `mutation-full :` or a multi-target line overrides the recipe unseen by the recipe check and the rule-changed sweep. Predates S42 (Go, Spring share it) | Confirmed; S42 Phase 4 | open |
| B3 | B | LOW | A libcst or mutmut lock entry whose `source` or hashes change at the same version does not sweep (`lock_versions` compares only `version`). New | Confirmed; S42 Phase 4 | open |
| B4 | B | LOW | The sweep's first line repeats one cause once per Python service. Go's pattern, multiplied. New | Confirmed; S42 Phase 4 | open |
| B5 | B | LOW | `migrate` of a project with an added Python service conflicts in five files (`Makefile`, `pyproject.toml`, `uv.lock`, `commands/mutation.md`, `rules.json`); the Catch-up names two. New | Confirmed; S42 Phase 4 | open |
