# Implementation Plan: S24-ci-fetches-slice-base — a slice pull request's CI holds the slice to its scope instead of saying it could not look

**Branch**: `adopt-method` (D12 — no `slice/` branch, no claim, no push) | **Date**: 2026-10-04 |
**Spec**: [spec.md](../../spec.md), *Slice acceptance criteria* → `### S24-ci-fetches-slice-base` (AC-S24-1 … AC-S24-13)

**Input**: the slice's row in [story-split.md](../../story-split.md) and its criteria in `spec.md`; decisions
D12, D30, D31, D32, D35, D39, D54, D55, D82, D84 in [decisions.md](../../decisions.md); finding A3 under S20 in
[adversary-log.md](../../adversary-log.md), whose CI half this closes. Written by cruise iteration 12 (host,
strong model). The optional `before_plan` hook (`/characterise`) is taken as the ladder's Pin stage, after tasks.

## Summary

A generated project's `verify` job, and the delivery gate `adopt` writes, check a pull request out at depth 1 with
no trunk ref, so `check-slice-scope` has never held a slice in CI: since S22 it says *NOT checked* and exits 0.
The three jobs that run the gate now fetch full history (`fetch-depth: 0`; `GIT_DEPTH: "0"` on GitLab), and in a
forge's checkout *NOT checked* becomes a failure. The same history gives `check-migrations` and `check-flags`
their base, so their *new in this change* rules hold in CI on every pull request as they do on a developer's
machine — approved by the owner (D82), and said plainly in the fragment. A PATCH (D54): the same answers,
generated better; no file, option, flag or setting is added.

## The example map (rules the tasks cut on)

*A forge's checkout*, the trunk `main` and the branch `slice/S1` are as the criteria define them. *The
pull-request checkout* is the one [research.md](research.md) R-1 describes and `tests/forge_checkout.py` builds.

| Rule | Criteria | What it says | Examples |
|---|---|---|---|
| **R1** the generated `verify` job fetches history, and nothing else does | AC-S24-1 | `fetch-depth: 0` under the `verify` job's checkout, unconditional, with a comment; every other checkout as it was | e1 a generated project's `.github/workflows/verify.yml`: the `verify` job's `actions/checkout@v6` step carries `with:` `fetch-depth: 0`, no `${{` on that line, and the comment names the checks · e2 a project with an integration job: `CONTAINER_CHECKOUT` still fetches `--depth 1` and carries no `fetch-depth` · e3 the event-model workflow, the deploy workflows and the `ux-gates` workflow are byte for byte what the commit before the slice generates |
| **R2** the adopted gate fetches history, on both forges | AC-S24-2, -3 | The same key on `verify-delivery.yml`'s `verify` job; `GIT_DEPTH: "0"` on `verify-delivery` | e1 an adopted repository on GitHub: the `verify` job carries the key; with a `smoke` command recorded the `smoke` job's checkout carries none · e2 an adopted repository on GitLab: `verify-delivery` carries `variables:` / `GIT_DEPTH: "0"`; `smoke-delivery` has no `variables:`; the file has no `rules:` |
| **R3** on the checkout the workflow now makes, a slice is held | AC-S24-4 | AC-S22-23's rule on the pull-request checkout | e1 a host-surface change on `slice/S1`, the pull-request checkout with GitHub's variables → exit 1 naming the path, *compared with `main` at* · e2 the same with GitLab's variables · e3 a slice inside its scope → exit 0 with the *compared with* line. All three hold today and are written as holds, saying so |
| **R4** in a forge's checkout, no base is a failure | AC-S24-5, -6, -7 | *NOT checked* exits 1; the line names both keys and what any other CI needs; unreadable keeps exit 0 | e1 depth-1 single-branch clone of `slice/S1`, `GITHUB_ACTIONS=true` (separately `GITLAB_CI=true`, `CI=true`) → exit 1, stdout empty, one stderr line with *NOT checked*, `` `main` ``, `fetch-depth: 0`, `GIT_DEPTH: "0"` and *a full clone with the trunk's branch fetched*; no `git fetch`, no *nothing to hold* · e2 the detached pull-request route (name in `GITHUB_HEAD_REF`, no marker) at depth 1 → the same · e3 a trunk ref with no common ancestor at this depth, an unrelated trunk, and a pull-request target with no history in common, each under a marker → the same, with the passed-over words kept · e4 a lost record at a canonical slot under a marker with no base → exit 1 with the record and the line (holds today) · e5 a base and a `git diff` that fails, under a marker → exit 1 with *NOT checked — git could not compare* · e6 a checkout git cannot read, under a marker → exit 0 and the *could not read* line (holds) · e7 a branch that is not `slice/<id>` under a marker, with and without history → *nothing to hold*, exit 0 (holds) |
| **R5** with history, the two other gates answer as on a full clone | AC-S24-8 | The shipped `check-migrations.py` and both `check-flags.py`, unchanged, on the pull-request checkout | e1 a pull request from `feature/x` carrying an expand and its contract together → `check-migrations` exits 1 on the pull-request checkout, 0 on the depth-1 checkout with no trunk ref · e2 a pull request declaring a flag seeded `on` → `check-flags` (aws; azure) exits 1 on the pull-request checkout, 0 at depth 1 · e3 the same commits pushed to the trunk → both exit 0 at either depth · e4 on the pull-request checkout from `feature/x`, `check-slice-scope` says *nothing to hold*, exit 0. All hold today — the slice changes no line of the three scripts — and are written as holds |
| **R6** a developer's checkout is untouched | AC-S24-9, -13 | No marker, no detached variable route: every answer is today's; and the suite is green under CI's own markers | e1 the developer's-answer tests in `tests/test_slice_scope_*.py` pass with no edit to their assertions · e2 the touched modules pass with `CI=true GITHUB_ACTIONS=true` in the environment |
| **R7** the words are true | AC-S24-10, -11, -12 | One `PATCH` fragment; the S22 fragment's sentence amended; the docstring; the catch-up followed | e1 `changelog.d/ci-fetches-slice-base.md`, first line `PATCH`, says the four things and names both refusals; `tests/test_changelog.py` green; `VERSION` unchanged · e2 `changelog.d/slice-scope-base.md` no longer says a CI run with nothing to compare with exits 0 · e3 the docstring of `check-slice-scope.py` says a forge's checkout with no base fails · e4 the catch-up paragraph followed on a workflow without the key: add the key, the slice is held |

R1, R2 and R4 change production code, each its own RED-GREEN-REFACTOR cycle with the examples red first for the
stated reason. R3, R5, R4e4, R4e6, R4e7 and R6 hold today: each is still **seen** to have teeth — the assertion
inverted or the fixture's history removed, observed failing, restored, the tree clean afterwards — before it is
committed.

## Technical Context

**Language/Version**: Python ≥ 3.11 (`pyproject.toml`).
**Primary Dependencies**: none added.
**Storage**: none.
**Testing**: `unittest` via `make test`; the workflow rules assert on what `workflow()`, `delivery_workflow()` and
`gitlab_job()` return and on a generated tree; the checker rules drive `check-slice-scope.py`, `check-migrations.py`
and `check-flags.py` through their command lines in temporary repositories, with the helpers already in the test
tree (`tests/test_slice_scope_root.py` `SliceScopeFixtures`, `git`; `tests/test_slice_scope_base.py` `run_gate`,
`commit`; `tests/test_slice_scope_no_base.py` `clone`). One new helper module, `tests/forge_checkout.py`, builds
the pull-request checkout with git itself. No mocking framework.
**Target Platform**: wherever `slipwai` runs; the generated workflows run on GitHub, Gitea, Forgejo and GitLab.
**Project Type**: CLI tool, the factory — deployable `slipwai-graph`, kind `tool`, path `.`.
**Performance Goals**: none here. In a generated project the `verify` job pays a full fetch in place of one
commit; the fragment says so (D54).
**Constraints**: PATCH — no setting, flag or file; `check-migrations.py` and both `check-flags.py` do not change by
a byte; nothing under `delivery/scripts/`, `tools/`, the `Makefile`, this repository's own CI or hook settings
changes (the installed `delivery/scripts/check-slice-scope.py` and `.github/workflows/verify-delivery.yml` here are
the factory's and arrive by `slipwai migrate`, a person's — D9); every file under `src/` and `tests/` stays within
`make check-structure`'s 350 lines (`tests/test_slice_scope_no_base.py` is at 343: what R4 adds goes in a new
file); every `read_text`/`open` in a toolkit script names `encoding="utf-8"`.
**Scale/Scope**: three generator functions, one branch of `check()` with `not_checked()` and the docstring, a test
helper, four new test files, two existing suites' assertions, two fragments.

## Constitution Check

*GATE: evaluated against `.specify/memory/constitution.md` before research; re-checked after design.*

| Principle | Touched? | How this slice satisfies it |
|---|---|---|
| I. A generated project owns its files and passes its own gate (NON-NEGOTIABLE) | Yes | No check is removed or weakened anywhere: three checks that could not look in CI now look. The change to what CI checks is the owner's, twice (D39, D82). A project's files change only through `slipwai migrate`, the maintainer's command; `VERSION` untouched; the fragment lands with the first user-visible commit. |
| III. Simplicity | Yes | One key on one step, one variable on one job, one exit code. No expression, no `rules:`, no setting. |
| V. Acceptance-driven development | Yes | Each rule a cycle through the generator's output or the script's command line; holds written as holds and seen to have teeth. |
| VIII. Versioning and breaking changes | Yes | PATCH (D54); the fragment says what a repository already generated meets after `migrate` and what to do. |
| XIV. Agent-generated change meets the same bar (NON-NEGOTIABLE) | Yes | Increment commits with the quickest relevant tests green; both full gates on the final tip; the hand runs the demo as the actor. |
| II, IV, VI, VII, IX, X, XI, XII, XIII, XV | No | No domain code, contract, telemetry, secret or type changes. |

**Gate result:** no violation; *Complexity Tracking* stays empty. **Post-design re-check:** unchanged.

## Project Structure

```text
src/slipwai/project/ci_workflows.py            # R1: the `verify` job's checkout in `workflow()`
src/slipwai/project/adopted_ci.py              # R2: `delivery_workflow()`'s `verify` job; `gitlab_job()`'s `verify-delivery`
assets/toolkit/scripts/check-slice-scope.py    # R4: `check()`'s two forge arms, `not_checked()`, the docstring (R7e3)
tests/forge_checkout.py                        # new helper — the pull-request checkout, at full history and at depth 1
tests/test_ci_fetch_generated.py               # new — R1
tests/test_ci_fetch_adopted.py                 # new — R2
tests/test_slice_scope_forge.py                # new — R3, and R4's new examples
tests/test_ci_history_gates.py                 # new — R5
tests/test_slice_scope_no_base.py              # R4: the assertions that said exit 0 under a marker
tests/test_slice_scope_hostile_base.py         # R4: the same
changelog.d/ci-fetches-slice-base.md           # R7e1
changelog.d/slice-scope-base.md                # R7e2: the sentences about CI's exit 0
```

**Structure Decision**: one deployable, `slipwai-graph` (kind `tool`, path `.`, purpose confirmed); one bounded
context (the factory; D3). The decided strategy is `leave-it` (`delivery/docs/adr/0002-change-strategy.md`, at
`Proposed`; D5): no new home. The code changed existed before the method did, so the Pin stage applies.
`workflow()` is called from `src/slipwai/scaffold.py`; `delivery_workflow()` and `gitlab_job()` from
`src/slipwai/project/adopted.py` (found by text search — this tree has no `.codegraph/`). Any test that pins the
whole text of one of the three files, and any helper under `tests/` that rebuilds an old workflow by regex, is
found by search before the change and named in the task.

## Design

**R1.** In `workflow()` the `verify` job's step becomes

```yaml
      # Full history: `check-slice-scope`, `check-migrations` and `check-flags` compare this change with the
      # trunk, and a checkout of one commit gives them nothing to compare with.
      - uses: actions/checkout@v6
        with:
          fetch-depth: 0
```

Nothing else in the module changes: `CONTAINER_CHECKOUT` and `integration_job()` keep their depth-1 fetch.

**R2.** The same step, with the same comment, on the `verify` job in `delivery_workflow()`; `smoke_job()` is not
edited. In `gitlab_job()`, `verify-delivery` gains, after `stage: test`,

```yaml
  variables:
    # Full history: the gate's checks compare this change with the trunk.
    GIT_DEPTH: "0"
```

and `smoke-delivery` is not edited. No `rules:`.

**R4.** In `check()`, the two returns taken where `forge_checkout()` is true — no base, and `CouldNotCompare` —
return `True` for *failed* where they return `False`. `not_checked()` keeps its sentence and adds, after the two
keys, *on any other CI, a full clone with the trunk's branch fetched*. The `problem` arm (git cannot read the
checkout) is not edited. The docstring's paragraph on a CI run says exit 1 and drops *because that checkout is depth
1* for *because that checkout has no history to compare with*. `main()` already prints the lost records above the
notice and returns 1 on `failed`.

**The pull-request checkout** (`tests/forge_checkout.py`; research R-1): from an origin holding `main` and a head
branch, make the merge of the head into `main` as the forge does, under `refs/pull/1/merge`; clone with
`file://`, fetch `+refs/heads/*:refs/remotes/origin/*` and the merge ref, check the merge commit out detached, and
delete the local branch the clone made, so the only refs are `refs/remotes/origin/*` — as `actions/checkout`
leaves them. The depth-1 form fetches only the merge ref at `--depth 1`. The helper returns the path; the test
supplies the forge's variables.

## Pin

`delivery/survey/running.md` records the run path proven (S00) and `project.json` records `smoke`. Behaviours this
slice changes, each recorded in `delivery/survey/pinned.md` before implementation: what `check-slice-scope` answers
in a forge's checkout with no base (pinned already by `tests/test_slice_scope_no_base.py` and
`tests/test_slice_scope_hostile_base.py`, the 2026-10-03 row — named, not re-pinned); and how the three files check
the code out today (the generated `verify` job, the adopted `verify` job, the GitLab `verify-delivery` job: a bare
`actions/checkout@v6`, no `variables:`), pinned by `/characterise` if no test holds it now.

## Branch and integration

As D12: increments land on `adopt-method`, one slice at a time, no `slice/` branch, nothing pushed. The demo runs
this checkout's `./slipwai` to generate a project and adopt a repository under a temporary directory, reads the
three files, and runs the generated project's own `check-slice-scope`, `check-migrations` and `check-flags` on the
pull-request checkout built with git ([quickstart.md](quickstart.md)). **Not run, and said so on the board:** a
real runner on a real forge — this run pushes nothing.

## Deliberate stubs

None.

## Complexity Tracking

Empty.
