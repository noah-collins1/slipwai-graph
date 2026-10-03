# Implementation Plan: S23-refusal-in-subdirectory — a refresh never writes over uncommitted work where the project sits in a subdirectory of its git repository

**Branch**: `adopt-method` (D12 — no `slice/` branch, no claim, no push) | **Date**: 2026-10-03 |
**Spec**: [spec.md](../../spec.md), *Slice acceptance criteria* → `### S23-refusal-in-subdirectory` (AC-S23-1 … AC-S23-10)

**Input**: the slice's row in [story-split.md](../../story-split.md) and its criteria in `spec.md`; decisions
D12, D29, D36, D37, D38 in [decisions.md](../../decisions.md); finding A1 under `## S21` in
[adversary-log.md](../../adversary-log.md). Written by cruise iteration 6 (host, strong model). The optional
`before_plan` hook (`/characterise`) is taken as the ladder's Pin stage, after tasks.

## Summary

`adopt --refresh`, `--confirm` and `--decline` (experimental: brownfield adoption) refuse to write over an
uncommitted change slipwai did not make, and record what slipwai itself left so a later answer may write over
its own. Both rest on `changed()` in `src/slipwai/uncommitted.py`, which reads `git status` — and git spells
every path from the repository's top, while a run spells what it writes from the project. Where the project is
in `sub/`, nothing ever matches: the refusal never fires, a person's edit is written over at exit 0, and
`.delivery-tools/written.json` stays `{}`. `changed()` now answers with the changes under the project's own
directory, spelled relative to it (D36). A PATCH: the same answers, generated better.

## The example map (rules the tasks cut on)

The repository in every example is the one the criteria describe: one git repository, the adopted project in
`sub/` with the adoption committed, `other/` beside it, commands run in `sub/`.

| Rule | Criteria | What it says | Examples |
|---|---|---|---|
| **R1** a person's uncommitted change to a file the run writes is refused, by the project's name for it | AC-S23-1, -2 | The refusal fires in a subdirectory project and prints the path with no `sub/` | e1 `delivery/docs/convergence.md` edited → `adopt --refresh` exits 2, stderr holds `` `delivery/docs/convergence.md` `` and not `sub/delivery`, the edit is still in the file, `git status` shows that one path only · e2 the same edit → `adopt --confirm shop` exits 2 and `project.json` is byte-for-byte what it was · e3 the same edit → `adopt --decline themes` the same · e4 a listed file deleted, not committed → the refresh is refused naming it · e5 a path the run writes present on disk and untracked (its removal from the index committed) → refused naming it |
| **R2** what slipwai left is slipwai's | AC-S23-3, -4 | A run's own uncommitted regeneration is recorded, project-relative, and a later run writes over it | e1 `--confirm shop`, a row settled by hand in `project.json`, `--confirm themes`, `--refresh`, nothing committed between → each exits 0 (holds today, for the wrong reason: nothing is ever refused) · e2 after e1's first step `sub/.delivery-tools/written.json` is not `{}`, every key is a path that exists under `sub/` as spelled, none starts with `sub/`, and `git status` does not list the file · e3 after e1's first step a person appends a line to one recorded file → the refresh is refused naming that file |
| **R3** what is outside the project is not this run's | AC-S23-5 | A change elsewhere in the repository refuses nothing and is never recorded | e1 `other/note.txt` edited → the refresh exits 0 and the edit stands · e2 a file committed at the repository's top as `delivery/docs/convergence.md`, then edited → the refresh in `sub/` exits 0 (today: refused, by mistake), the top-level file keeps the edit, and no key of `written.json` names it |
| **R4** wherever the project sits | AC-S23-6 | Depth, a name git would quote, and a symbolic link change nothing | e1 the project in `a/b/` → R1e1, R2e2 and R3e1 hold · e2 the project in `dé pt/` (a space and a non-ASCII letter) → the same · e3 the commands run in a symbolic link to `sub/` → the same |
| **R5** an earlier factory's leftovers are refused once | AC-S23-9 | An uncommitted regenerated file with no record is not told apart from a person's edit | e1 after `--confirm shop`, `written.json` emptied to `{}` (what an earlier factory left there) → the refresh is refused naming regenerated files · e2 those files committed → the refresh exits 0 |
| **R6** at the top, and without git, every answer is today's | AC-S23-7, -8 | No change where the project is the repository's top, or is in no repository | e1 `tests/test_uncommitted.py` and `tests/test_refresh_owned.py` pass with no edit to either · e2 at the top, after `--confirm shop`, the keys of `written.json` are the paths as before (no leading `./`, none absolute) · e3 an adopted project copied out to a directory in no git repository → the refresh exits 0, refuses nothing, writes no `written.json`, no traceback |
| **R7** the release says what it is | AC-S23-10 | One `PATCH` fragment, labelled experimental; `VERSION` unchanged; `add-service` untouched | e1 `changelog.d/refusal-in-subdirectory.md`, first line `PATCH`, says *experimental: brownfield adoption*, what was lost, and what R5 asks once; `tests/test_changelog.py` green · e2 `git diff` over the slice shows no change to `src/slipwai/add_service.py` or `VERSION` |

R2e1, R3e1, R5e2 and all of R6 hold today and are written as holds, saying so. R2e2, R2e3, R4 and R5e1 fail
today for R1's reason and turn green with R1's change: each is still **seen** failing — with the production
hunk reversed in the working tree, then restored, the tree clean afterwards — before it is committed.

## Technical Context

**Language/Version**: Python ≥ 3.11 (`pyproject.toml:16`).
**Primary Dependencies**: none added; standard library and the `git` already required.
**Storage**: `.delivery-tools/written.json` under the project — same file, same shape, same spelling at the top.
**Testing**: `unittest` via `make test`; new tests drive `slipwai adopt` through the CLI against a temporary git
repository, with the helpers already in the test tree (`tests/test_adopt.py` `repository()`, `slipwai()`;
`tests/test_candidates.py` `adopted()`, `MONOREPO`, `record()`; `tests/test_replay.py` `git()`). No mocking
framework.
**Target Platform**: wherever `slipwai` runs (Linux, macOS, Git Bash). A test that needs a symbolic link or a
non-ASCII directory name skips, saying why, where the platform cannot make one.
**Project Type**: CLI tool, the factory — deployable `slipwai-graph`, kind `tool`, path `.`.
**Performance Goals**: none; one more short `git` call per `changed()`.
**Constraints**: PATCH — no setting, no flag, no new file in a project; nothing under `delivery/scripts/`,
`tools/`, the `Makefile`, CI or hook settings changes; every file under `src/` and `tests/` stays within
`make check-structure`'s 350 lines (`uncommitted.py` is at 93, `tests/test_uncommitted.py` at 87 and is not
edited — R6e1).
**Scale/Scope**: one function in `src/slipwai/uncommitted.py` and its module docstring; two new test files; one
fragment; one sentence in `docs/adopting.md`.

## Constitution Check

*GATE: evaluated against `.specify/memory/constitution.md` before research; re-checked after design.*

| Principle | Touched? | How this slice satisfies it |
|---|---|---|
| I. A generated project owns its files and passes its own gate (NON-NEGOTIABLE) | Yes | *The factory MUST NOT overwrite … a file in a repository it … adopted except through a command the project's maintainer ran*: the commands are the maintainer's, and the slice restores the refusal that keeps them from writing over the maintainer's own uncommitted work; no gate changes; `VERSION` untouched; the fragment lands in the first user-visible commit. |
| III. Simplicity | Yes | `changed()` asks git for the project's prefix and keeps what is under it. No setting, no new module. |
| V. Acceptance-driven development (in force since S00) | Yes | Each rule a RED-GREEN-REFACTOR cycle through the CLI; each example observed failing for its stated reason before it is committed; holds are written as holds. |
| VIII. Versioning and breaking changes | Yes | PATCH; experimental label on the fragment; the fragment says what a repository already adopted in a subdirectory may meet once (D37). |
| XIV. Agent-generated change meets the same bar (NON-NEGOTIABLE) | Yes | Increment commits with the quickest relevant tests green; both full gates on the final tip; the hand runs the demo as the actor. |
| II, IV, VI, VII, IX, X, XI, XII, XIII, XV | No | No retry path, domain code, contract, telemetry, secret, pipeline or type changes. |

**Gate result:** no violation; *Complexity Tracking* stays empty. **Post-design re-check:** unchanged.

## Project Structure

```text
src/slipwai/uncommitted.py                 # R1–R5: `changed()`; the docstring says where it looks
tests/test_uncommitted_subdirectory.py     # new — R1, R2, R3, R5
tests/test_uncommitted_places.py           # new — R4, R6e2, R6e3
changelog.d/refusal-in-subdirectory.md     # R7
docs/adopting.md                           # the `--refresh` row: one sentence
```

**Structure Decision**: one deployable, `slipwai-graph` (kind `tool`, path `.`, purpose confirmed); one bounded
context (the factory; D3). The decided strategy is `leave-it` (`delivery/docs/adr/0002-change-strategy.md`): no
new home. The code changed existed before the method did, so the Pin stage applies. `changed()` has two callers
in the same module, `stamp()` and `refuse_foreign()`, and those have three call sites: `src/slipwai/resurvey.py`
(`refresh()`, twice) and `src/slipwai/confirm.py` (found by text search — this tree has no `.codegraph/`).

## Design

`changed(root)` keeps its signature and its three answers — a list, an empty list, `None` where git cannot
answer. It asks git two things in `root`: the project's prefix (`git rev-parse --show-prefix` — empty at the
top, `sub/` below it; [research.md](research.md) R-2) and the status limited to the project (`git status
--porcelain=v1 -z --untracked-files=all -- .`; R-3). Every path git reports that starts with the prefix is
returned with the prefix taken off; one that does not is not this project's and is dropped. Either call failing
is `None`, as a failing status is today. The rename rule (the entry after an `R` or `C` is where it came from,
and is skipped) stands. `stamp()` and `refuse_foreign()` are not edited: they already compare, record and print
what `changed()` returns. At the top the prefix is empty and the pathspec is the whole tree, so every answer and
every key in `written.json` is today's (R6).

R1's smallest change is taking the prefix off; R3e2 is what drives dropping what is outside the project — a path
from the top that spells a project path is refused until then.

## Pin

`delivery/survey/running.md` records the run path proven (S00) and `project.json` records `smoke`. One behaviour
changes, recorded in `delivery/survey/pinned.md` before implementation: what the refusal answers where the
project is the top of its repository — `tests/test_uncommitted.py` (the `/ground` sequence commits once; a hand
edit to a file a refresh writes is refused by name; what slipwai left is its own after the record moves; the
same where `.git` is read-only) and `tests/test_refresh_owned.py`. Not pinned, because the slice changes it on
purpose: in a subdirectory project nothing is refused and nothing is recorded.

## Branch and integration

As D12: increments land on `adopt-method`, one slice at a time, no `slice/` branch, nothing pushed. The demo runs
this checkout's `./slipwai` against a temporary repository ([quickstart.md](quickstart.md)). The fix is in
`src/slipwai/`, which this checkout runs directly; no `slipwai migrate` is involved, and this repository — adopted
at its top — sees no change.

## Deliberate stubs

None.

## Complexity Tracking

Empty.
