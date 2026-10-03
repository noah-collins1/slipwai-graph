# Implementation Plan: S22-slice-scope-base — a slice branch cannot empty its own scope check by minting a base

**Branch**: `adopt-method` (D12 — no `slice/` branch, no claim, no push) | **Date**: 2026-10-03 |
**Spec**: [spec.md](../../spec.md), *Slice acceptance criteria* → `### S22-slice-scope-base` (AC-S22-1 … AC-S22-21)

**Input**: the slice's row in [story-split.md](../../story-split.md) and its criteria in `spec.md`; decisions
D9, D12, D19, D22, D23, D30, D31 in [decisions.md](../../decisions.md); adversary finding A3 under `## S20` in
[adversary-log.md](../../adversary-log.md). Written by cruise iteration 5 (host, strong model). The optional
`before_plan` hook (`/characterise`) is taken as the ladder's Pin stage, after tasks.

## Summary

`check-slice-scope.py` compares a `slice/<id>` branch with the newest base among `main`, `origin/main`, `master`
and `origin/master`, each asked of git by its short name. A `master` branch, an `origin/master` ref or a tag
named `main` placed at the branch's head therefore becomes the base, the diff is empty and the gate passes; and
a checkout with no base at all prints *nothing to hold* and passes. After this slice the base is where the
branch left **the trunk** — the name the working tree's `project.json` records in `ci.branch` where that is a
usable name with a ref (never a `slice/<id>` name), else `main`, else `master` — looked up only as
`refs/heads/<name>` and `refs/remotes/origin/<name>`; on a pull request the forge's target branch is a second
candidate and the oldest base across the two names wins (D30). A developer's checkout with no usable base fails
with the command to run; a forge's detached pull-request checkout with none keeps exit 0 but says the slice was
NOT checked and which workflow key would make it (D31). A PATCH: one asset, no setting, no new file in a project.

## The example map (rules the tasks cut on)

| Rule | Criteria | What it says | Examples |
|---|---|---|---|
| **R1** the base is the trunk's, by full ref name | AC-S22-1, -2, -3, -11, -12 | Only `refs/heads/<trunk>` and `refs/remotes/origin/<trunk>` answer; within the one name the newest base wins; `master` counts only as the recorded name or where no `main` has a ref | e1 no `ci.branch`, host-surface change committed; a `master` branch at HEAD → still refused · e2 the same with `refs/remotes/origin/master` at HEAD · e3 the same with a tag `main` at HEAD · e4 `ci.branch: trunk` and a `trunk` branch: the slice's own file → green; a `main` or a `master` minted at HEAD and a host change → refused · e5 `ci.branch: master`, trunk `master`, a `main` minted at HEAD → refused · e6 `main` and an older `master` left behind, nothing minted: own file green, host change refused (today's) · e7 `main` moved locally past `origin/main` and merged into the slice → green, `main`'s files not charged (held by `tests/test_parallel_slices.py`, unedited) |
| **R2** the record's name is read tolerantly and is never a slice's | AC-S22-4, -5, -6, -7 | A `ci.branch` that is unusable, a `slice/<id>` name, or has no ref adds nothing; `main` answers | e1 the slice commits `ci.branch: slice/S1` → `project.json` refused · e2 the same uncommitted · e3 `ci.branch: slice/S9` with a `slice/S9` branch at HEAD → refused · e4 the slice sets `ci.branch: nowhere` (no such branch) → base is `main`'s, `project.json` refused, output says `nowhere` was passed over · e5 `ci.branch` `7`, `["main"]`, `""`, `"  "`, `"-x"`, `"refs/tags/main"` → a verdict against `main`, no traceback · e6 `"refs/heads/main"` reads as `main` · e7 the base's own record names `develop`, no such ref here, the slice changes only its own file → green against `main`, and the line names `develop` and `git fetch origin develop` |
| **R3** the forge's target is a second candidate, oldest across names | AC-S22-8, -9, -10 | Where `GITHUB_BASE_REF` or `CI_MERGE_REQUEST_TARGET_BRANCH_NAME` is usable and has a ref it is a candidate; across two names the older base wins | e1 `GITHUB_BASE_REF=main`, the slice committed `ci.branch: evil`, `refs/remotes/origin/evil` at HEAD → base `main`'s, `project.json` refused · e2 the same through `CI_MERGE_REQUEST_TARGET_BRANCH_NAME` · e3 trunk `master`, no record, `GITHUB_BASE_REF=master`, `refs/remotes/origin/main` at HEAD → refused · e4 target `feature` cut from `main` and ahead of it, the slice cut from `feature`: base is `main`'s, so `feature`'s own host change is among the refusals · e5 a target with no ref, or unusable → ignored, the recorded trunk answers |
| **R4** the line says what was compared | AC-S22-13 | The pass line and the refusal header name the trunk and the base's short commit | e1 pass: `check-slice-scope: slice/S1 touches only what one slice may (compared with `main` at <7+ hex>)` — the words before the bracket unchanged · e2 refusal header ends `… — compared with `main` at <hex>` |
| **R5** a developer's checkout with no usable base fails with what to run | AC-S22-14, -15, -17, -19 | Exit 1, one line | e1 `git clone --depth 1 --branch slice/S1` (single branch: no trunk ref) → exit 1, names `main` and `git fetch origin main` · e2 a full repository whose only branch is `slice/S1` → the same line · e3 shallow clone with `origin/main` and no common ancestor in depth → exit 1, `git fetch --unshallow origin` · e4 full clone, `main` an unrelated root → exit 1, *a slice branch is cut from `main`*, no fetch named · e5 `GITHUB_HEAD_REF=slice/S1` with HEAD attached and no base → exit 1 · e6 any of these with a regular untracked file at a canonical slot → that finding is printed too |
| **R6** a forge's detached checkout with no base says NOT checked | AC-S22-16, -18, -19 | Exit 0, stderr, never *nothing to hold* | e1 detached depth-1 checkout, `GITHUB_HEAD_REF=slice/S1`, no trunk ref → exit 0, stdout empty, stderr has `NOT checked` and `fetch-depth: 0` · e2 the same through `CI_COMMIT_REF_NAME`, stderr names `GIT_DEPTH` too · e3 detached, full history and `origin/main`, `GITHUB_HEAD_REF=slice/S1`, host change → refused as locally · e4 branch `feature/x` in a shallow clone, and a detached checkout with no variable → today's *not a `slice/<id>` branch — nothing to hold*, exit 0 |
| **R7** nothing else moves | AC-S22-12, -20 | `check-migrations.py` is not edited; `tests/test_parallel_slices.py` is not edited and stays green | e1 `git diff` of the slice touches neither file · e2 `make test TESTS="test_parallel_slices test_slice_scope_root test_slice_scope_hostile_branch test_slice_scope_adopted_rules"` green |
| **R8** the release says what it is | AC-S22-21 | One `PATCH` fragment; `VERSION` unchanged | e1 `changelog.d/slice-scope-base.md`, first line `PATCH`, the local and the pull-request promise stated separately, and what a project sees after `migrate`; `tests/test_changelog.py` green |

## Technical Context

**Language/Version**: Python ≥ 3.11 (`pyproject.toml:16`).
**Primary Dependencies**: none added; standard library and `git` only.
**Storage**: N/A — the checker reads `project.json` (working tree, for the trunk's name only; ownership is still
read from the base, T017), git refs and four environment variables.
**Testing**: `unittest` via `make test`; new tests drive the script through its command line in a temporary
repository — the seam `tests/test_slice_scope_root.py` `SliceScopeFixtures` and
`tests/test_slice_scope_hostile_branch.py` `HostileBranchTest.run_gate` already use. Shallow and single-branch
checkouts are made with `git clone --depth 1 file://…`. No mocking framework.
**Target Platform**: wherever a generated or adopted project runs its gate.
**Project Type**: CLI tool, the factory — deployable `slipwai-graph`, kind `tool`, path `.`; the change is to an
asset it copies into projects.
**Performance Goals**: none; a handful of extra `git rev-parse` calls on a slice branch.
**Constraints**: PATCH — no setting, flag or file added to a project; CI's exit code unchanged in every project
(D31); nothing under `delivery/scripts/`, `tools/`, the `Makefile`, CI or hook settings changes in this
repository (cruise controls; the fix reaches here through a person's `slipwai migrate`, D9);
`assets/toolkit/scripts/check-migrations.py`, `assets/targets/*/scripts/check-flags.py`,
`src/slipwai/project/ci_workflows.py` and `adopted_ci.py` are not edited; `tests/test_parallel_slices.py` is not
edited (350 lines, the pin); every file under `tests/` stays within 350 lines; `tests/test_line_widths.py` and
`make check-structure` hold.
**Scale/Scope**: 1 asset script, 2 new test files, 1 changelog fragment.

## Constitution Check

*GATE: evaluated against `.specify/memory/constitution.md` before research; re-checked after design.*

| Principle | Touched? | How this slice satisfies it |
|---|---|---|
| I. A generated project owns its files and passes its own gate (NON-NEGOTIABLE) | Yes | The gate is made right in the file the factory writes, never in this repository's installed copy; nothing a project's gate checks is removed — it refuses in cases where it passed by comparing a branch with itself, and CI's exit is unchanged (D31). |
| III. Simplicity | Yes | Functions beside `merge_base()` in the one script; no setting, no shared module. |
| V. Acceptance-driven development | Yes | Each rule is a RED-GREEN-REFACTOR cycle through the script's command line; one capability — how the base is chosen and what happens without one; the workflow change is `S24`, not here. |
| VIII. Versioning and breaking changes | Yes | PATCH fragment in the commit that first changes the asset; `VERSION` stays `1.5.2.dev0`; the fragment says what a project sees after `migrate`. |
| XIV. Agent-generated change meets the same bar (NON-NEGOTIABLE) | Yes | Increment commits with the quickest relevant tests green; both full gates before the slice is marked done; the hand runs the demo as the actor. |
| II, IV, VI, VII, IX, X, XI, XII, XIII, XV | No | No retry path, domain code, contract, telemetry, secret, pipeline or type changes. |

**Gate result:** no violation; *Complexity Tracking* stays empty. **Post-design re-check:** unchanged.

## Project Structure

### Documentation (this slice)

```text
specs/001-faster-slipwai/slices/S22-slice-scope-base/
├── plan.md, research.md, data-model.md, quickstart.md
├── tasks.md             # the tasks stage
└── benchmark.json, demo-log.md, demo/
```

### Source code (repository root)

```text
assets/toolkit/scripts/check-slice-scope.py   # R1–R6: trunk name, full-ref bases, target candidate, no-base answers, docstring
tests/test_slice_scope_base.py                # new — R1–R4
tests/test_slice_scope_no_base.py             # new — R5, R6
changelog.d/slice-scope-base.md               # R8
```

**Structure Decision**: one deployable, `slipwai-graph` (kind `tool`, path `.`, purpose confirmed) — the only
one in `project.json`; one bounded context (the factory; D3). The decided strategy is `leave-it`
(`delivery/docs/adr/0002-change-strategy.md`, Accepted by a person): no new home, no routing seam. The code
changed existed before the method did, so the Pin stage applies (see *Pin*).

## Design

All in `assets/toolkit/scripts/check-slice-scope.py`.

**Who named the branch.** `current_branch()` keeps its answer and also says where it came from: a forge
variable, or git. `check()` asks one more thing of git — is `HEAD` detached (`git symbolic-ref -q HEAD` fails) —
and a **forge checkout** is: the name came from a variable *and* `HEAD` is detached. Everything else is a
developer's checkout.

**Usable name.** `usable(value)`: a `str`; stripped; a leading `refs/heads/` taken off; non-empty; not starting
with `-`; not starting with `refs/`; accepted by `git check-ref-format refs/heads/<name>`; and not matching
`SLICE_BRANCH`. Anything else is `None` — never an exception (D22).

**Refs.** `bases_of(name)`: for `refs/heads/<name>` and `refs/remotes/origin/<name>`, where
`git rev-parse --verify --quiet <ref>^{commit}` answers, `git merge-base HEAD <ref>`; returns whether any ref
exists and the newest of the bases found (today's `--is-ancestor` walk).

**The trunk.** The recorded name is `ci.branch` of `ROOT / "project.json"` as the working tree has it, read with
the script's own tolerant `read_json`. The trunk is the recorded name where usable and a ref exists; else `main`
where a ref exists; else `master` where a ref exists; else none. A recorded name that was passed over is kept
for the report line.

**The target.** The first of `GITHUB_BASE_REF`, `CI_MERGE_REQUEST_TARGET_BRANCH_NAME` that is set, usable and has
a ref, and is not the trunk's own name. With a base under each name: the one that is an ancestor of the other;
where neither is, `git merge-base` of the two — a base behind both, so the target still only moves the base
back; where even that is nothing, the trunk's.

**What `merge_base()` returns.** A small result — base commit or `None`, the trunk's name (or the name a person
would fetch: target, else recorded, else `main`), whether a trunk ref exists, the passed-over name — instead of
a bare string; `check()` is its only caller in this script.

**No usable base** (`check()`, on a `slice/<id>` branch only; `lost_records()` findings are kept in every case):

| Checkout | State | Exit | Line |
|---|---|---|---|
| developer's | no trunk ref | 1 | `slice/<id> has no `<trunk>` to compare with, so nothing can be held — run `git fetch origin <trunk>`` |
| developer's | ref, no common ancestor, `git rev-parse --is-shallow-repository` is `true` | 1 | `slice/<id> shares no history with `<trunk>` at this depth — run `git fetch --unshallow origin`` |
| developer's | ref, no common ancestor, not shallow | 1 | `slice/<id> shares no history with `<trunk>` — a slice branch is cut from `<trunk>`` |
| forge's | any of the three | 0 | stderr: `slice/<id> was NOT checked — this CI checkout has no `<trunk>` history to compare with. The check holds on a developer's machine; for it to hold here the verify job's checkout needs `fetch-depth: 0` (on GitLab, `GIT_DEPTH: "0"`).` Nothing on stdout. |

The failure lines go through the existing refusal printing (header, indented finding), so the exit and the
stream are the ones a refusal has today.

**Report.** Pass: `check-slice-scope: slice/<id> touches only what one slice may (compared with `<trunk>` at
<short>)`; where a recorded name was passed over, the line ends `; `ci.branch` names `<name>`, which has no
branch here — `git fetch origin <name>` would bring it` (or *is not a branch name* where unusable). The refusal
header gains ` — compared with `<trunk>` at <short>`. The words existing tests read
(`slice/S1 touches only what one slice may`, `reaches outside what one slice may touch`) stay as they are.

**Docstring.** The last paragraph is rewritten to this rule in the same plain words, with the local promise and
the pull-request promise said separately and the CI checkout's *NOT checked* named.

## Pin

`delivery/survey/running.md` records the run path proven (S00) and `project.json` records `smoke`. The behaviour
this slice changes — which commit a slice branch is compared with, and what the gate answers without one — is
recorded in `delivery/survey/pinned.md` before implementation. Tests already there hold what must not move:
`tests/test_parallel_slices.py` `SliceScopeGateTest` (off a slice branch nothing is held; a slice's own files
pass; a `main` that moved locally and was merged in is the base), `tests/test_slice_scope_root.py`,
`tests/test_slice_scope_hostile_branch.py`, `tests/test_slice_scope_adopted_rules.py`. Not pinned, because the
slice changes it on purpose: a short-named `master`, `origin/master` or tag `main` counting as a base; *nothing
to hold* on a slice branch with no base; the pass line ending at *may*. No new seam.

## Branch and integration

As D12: increments land on `adopt-method`, one slice at a time, no `slice/` branch, nothing pushed; the
register's *Merged as* names the first and last commit. The demo runs from this checkout's tip against
temporary repositories ([quickstart.md](quickstart.md)). The fix does not reach this repository's own
`delivery/scripts/` inside the run (D9); the adversary row is headed `## S22 · …` (D17).

## Deliberate stubs

None in the slice. **Not working yet, by decision:** in CI on a default (depth-1) checkout the gate still holds
nothing for a slice pull request — it now says so. `S24-ci-fetches-slice-base` closes it and waits on a person's
approval (D31).

## Complexity Tracking

Empty.
