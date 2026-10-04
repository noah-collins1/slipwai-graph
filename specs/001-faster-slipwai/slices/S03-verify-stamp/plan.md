# Implementation Plan: S03-verify-stamp — the gate returns in under a second on a tree it already passed

**Branch**: `adopt-method` (D12 — no `slice/` branch, no claim, no push) | **Date**: 2026-10-04 |
**Spec**: [spec.md](../../spec.md), *Slice acceptance criteria* → `### S03-verify-stamp` (AC-S03-1 … AC-S03-31)

**Input**: the slice's row in [story-split.md](../../story-split.md) and its criteria in `spec.md`; decisions D7,
D9, D12, D30, D32, D33, D36, D39, D73, D74, D75, D76, D77 in [decisions.md](../../decisions.md). Written by cruise
iteration 11 (host, strong model). The optional `before_plan` hook (`/characterise`) is taken as the ladder's Pin
stage, after tasks.

## Summary

A generated project's `make verify` runs every check every time, about three times per slice, two of them on a
tree it has already passed. After this slice a full passing run records a stamp under the git directory, keyed by
everything a check answers from — the working files' raw bytes, the index, `HEAD` and every ref, the gate scripts,
the versions of the tools the machine supplies, the ignored files and the variables a check reads — and the next
run on the same key prints one line and starts no check. A stamp is never read on the trunk, under a CI marker, on
a detached `HEAD`, by `make ci`, or by the gate of a repository that adopted the method; there the gate does and
prints exactly what it does today. `VERIFY_FORCE` runs it anyway. MINOR: a new variable and a new file the gate
writes where `git status` never shows it; `VERSION` is already `1.6.0.dev0`; one fragment.

## The example map (rules the tasks cut on)

Each example is the criterion of the same number in `spec.md` — **e*n* is AC-S03-*n*** — read there, not restated
here. The **fixture project** is one the factory generates with the standard profile, the Python backend, no
transport (`http="none"`) and no frontend, on a branch other than the trunk, every CI marker removed from the
environment; the **stand-in tools** are executables the test writes into a directory put first on `PATH`
([research.md](research.md) item 5), so the real recipe and the real check scripts run and the full gate passes in
about half a second with no network.

### User story 1 — a tree that passed is not judged again (`verify-stamp.py`, the recipe) `[US1]`

| Rule | Criteria | What it says | Examples |
|---|---|---|---|
| **R1** a pass is recorded and reused, saying so in one line | AC-S03-1, -18, -19 | Second run: one `verify:` line with the five facts, no check started, exit 0, never the closing line; the stamp's five fields as plain text | e1 (run twice: the second prints one line, the stand-ins' log gains only version questions) · e18 (the file parsed: five fields; one field removed, or the file cut short, is no stamp) · e19 (the log, never the run's own line, is the evidence) |
| **R2** the key is the working files, as they are | AC-S03-2, -3, -4 | Raw bytes, executable bit, link target, untracked-not-ignored files, deletions; the index's entries; the real index never written | e2 (one example each: tracked edit uncommitted, tracked edit committed, new untracked file, deleted file, `chmod +x`, a link retargeted) · e3 (CRLF rewrite under `* text=auto eol=lf`; same size with the modification time restored; the index file's bytes equal before and after a run) · e4 (`git add` of an untracked file) |
| **R3** the key is history and position | AC-S03-5 | The `HEAD` commit, the branch name, every ref under `refs/heads` and `refs/remotes`, the shallow boundary | e5 (an empty commit; another branch at the same commit; `git update-ref refs/remotes/origin/main`; a `shallow` file appearing) |
| **R4** the key is the gate's scripts | AC-S03-6 | `Makefile` and everything covered under `scripts/`, a named part of key and stamp | e6 (a comment added to `scripts/check-imports.py`; to the `Makefile`; the stamp's script field differs, its tree field differs too) |
| **R5** the key is the machine's tools | AC-S03-14, -15, -16, -17 | The table beside `BACKEND_TOOLING`; first non-empty line, whole; lock-pinned tools never asked; the interpreter from `pyvenv.cfg`; a tool that cannot be asked | e14 (the table has a row per backend; the fixture asks `make`, `git`, `uv` and reads `python3`) · e15 (the `uv` stand-in reports another line: full gate, new stamp; no path in the file) · e16 (no `ruff`, `mypy` or `pytest` version question in the log; a changed `uv.lock` runs the gate; a changed `version_info` in `pyvenv.cfg` runs the gate) · e17 (one example each: tool absent, non-zero, silent, hung past the timeout, `pyvenv.cfg` missing — full gate, one line naming it, no stamp after the pass, exit 0) |
| **R6** the key is what a check reads that git ignores, and the variables that change an answer | AC-S03-7, -8, -9 | The closed lists, absence a value; installed environments; `RATCHET_TIGHTEN` | e7 (each list entry changed, created and removed in turn; the closed-list test fails on a planted read) · e8 (the plan's table below, held per backend) · e9 (each variable set, set empty and unset; `UX_GATES_JOBS` changes nothing; `RATCHET_TIGHTEN=1` reads and writes nothing) |

### User story 2 — where a stamp is not used, and what a run leaves (`verify-stamp.py`, the recipe) `[US2]`

| Rule | Criteria | What it says | Examples |
|---|---|---|---|
| **R7** never on the trunk, in CI, detached or adopted | AC-S03-21, -22, -24 | No read, no write, no removal, today's output; every other branch reads; a wrapped project's rule is today's text | e21 (each of the three markers, `CI=false` among them; `main`; `master` where it is the trunk; a `ci.branch` from `project.json`; detached — a planted stamp is byte-identical afterwards and stdout equals a run without the script's lines) · e22 (`slice/S01-x`, `fix/y`, `adopt-method`) · e24 (the Makefile of a project with a wrapped application has no stamp step; `NOTHING_CONFIRMED` unchanged) |
| **R8** forced | AC-S03-23, -25 | `VERIFY_FORCE` unset, empty, `0`; anything else; command line or environment; `make ci` | e25 (`VERIFY_FORCE=1`, `=yes` on the command line and in the environment: one line naming it and the value, every check, a new stamp; `=`, `=0`: reuse) · e23 (`make ci` on a stamped tree: every prerequisite, the forced line) |
| **R9** written only by a run in which everything ran and passed | AC-S03-10, -11, -26 | Removed before the first check; written after the last; `-i`, `-n`, `-t`, `-q`; the key moved during the run; the stamp cannot be written or removed | e26 (a failing check: no stamp afterwards though one stood before; a run killed mid-gate: none) · e10 (`make -i verify` on a failing tree: none; `-n`, `-t`, `-q` on a stamped tree: the stamp's bytes stand, no reuse line) · e11 (a stand-in that edits a tracked file during the gate: exit 0, the closing line, one line *not recorded*; a read-only stamp directory: the same) |
| **R10** cannot tell, and never stamped | AC-S03-12, -13 | One line before the first check, the full gate, exit as the gate's | e12 (`assume-unchanged`; `skip-worktree`; a submodule entry; an untracked directory that is a repository) · e13 (no `git` on `PATH`; no repository; a `git` stand-in that fails; an unreadable covered file) |
| **R11** where it lives and how long | AC-S03-27, -28 | Under the git directory, per project, per worktree, a rename of a finished file, never through a link; no expiry | e28 (`git status --porcelain --ignored` shows nothing of it; a second worktree has none; two projects in one repository; a link, a directory planted at the path) · e27 (a stamp dated ten years ago is reused; deleted, the gate runs) |

### User story 3 — what ships (`gate.py`, the page, the fragment) `[US3]`

| Rule | Criteria | What it says | Examples |
|---|---|---|---|
| **R12** the full gate is the gate it was | AC-S03-29 | Same prerequisites, order and closing line; the transport's line cut by `./init`; several services, one gate; every starter passes its own gate | e29 (the prerequisites of `verify-checks` equal those `verify` had, per fixture of the pin; `./init --http none` leaves no `check-openapi`; the matrix tests, unedited, with the CI marker they run under) |
| **R13** the page and the fragment say it | AC-S03-25, -30, -31 | `VERIFY_FORCE`'s default and one sentence; what a stamp cannot see; nothing asked of an existing project; MINOR | e25, e31 (each sentence followed as written) · e30 (`migrate` over a project generated before: the new `Makefile` and script arrive, `.gitignore` unchanged, the first run is full) |

AC-S03-20 is the demo's: the hand measures it on the Independent Test's project with the real toolchain
([quickstart.md](quickstart.md)).

## The design

**The recipe.** `verify` keeps its name, loses its prerequisites and gains a two-step recipe; the checks move to
`verify-checks`, which carries the prerequisite list, the blank line and the closing line exactly as `verify` did
([research.md](research.md) item 1, spiked):

```make
verify: ## Full deterministic pre-commit gate (a tree that already passed is not judged again; VERIFY_FORCE=1 runs it anyway)
	@python3 scripts/verify-stamp.py reuse --goals "$(MAKECMDGOALS)" --make "$(MAKE)" $(VERIFY_STAMP) || { $(MAKE) --no-print-directory verify-checks && python3 scripts/verify-stamp.py record --make "$(MAKE)" $(VERIFY_STAMP); }
verify-checks: check-python lint … test
	@echo
	@echo 'verify: all gates passed'
```

`$(VERIFY_STAMP)` is a variable the generator writes from the table: `--tool uv --environment apps/service/.venv`,
one `--tool` per machine-supplied tool of the project's backends and one `--environment` per Python service. The
per-transport line becomes `verify-checks: check-openapi` inside the same markers. A project with a wrapped
application keeps `GATE` and `NOTHING_CONFIRMED` byte for byte (R7). `reuse` exits 0 only when it printed the reuse
line; any other answer — not eligible, forced, no stamp, cannot tell, an old `python3`, an exception — exits
non-zero so the checks run, and nothing it meets can fail the gate. `record` always exits 0.

**`reuse`, in order.** (1) `python3` older than 3.10, or make's flags hold `n`, `t`, `q` or `i`, or
`RATCHET_TIGHTEN` is set: say nothing, touch nothing. (2) A CI marker, a detached `HEAD` or the trunk: say nothing,
touch nothing. (3) Cannot tell or never stamped (R10, R5's e17): one line, remove the stamp, leave a pending note
that this run records nothing. (4) Forced (`VERIFY_FORCE`, or `ci` among the goals): one line, remove the stamp,
leave the key as pending. (5) Build the key; a stamp whose key equals it: the reuse line, exit 0. (6) Otherwise
remove the stamp and leave the key as pending. `record`: steps 1 and 2 again; no pending note, or one that says
*nothing*: silent; build the key; equal to the pending key: write the stamp by rename and remove the note;
different, or the write fails: one line, *not recorded*, and why.

**The key** is one SHA-256 over named parts, each a digest of its own, so the stamp can show `tree`, `scripts` and
`tools` apart ([data-model.md](data-model.md)). Files come from `git ls-files -z --cached --others
--exclude-standard` run in the project's directory, read with `lstat` and `open` — never through git's filters.

**Installed environments (AC-S03-8), read from each backend's recipe at T-research:** Python — `uv sync --locked`
on every run, outside the key, with `pyvenv.cfg`'s `version_info` in it; every other backend — *assumed until the
first cycle of R6 reads its verify script*: where the recipe does not reinstall from the lock on every run, the
installed manifest joins the ignored-inputs list (`node_modules/.package-lock.json` for npm, the same file under
`scripts/event-model/` for the model tooling).

## Technical Context

**Language/Version**: Python 3.10+ for the script a project receives (it must also start, and answer *no stamp*, on an older `python3`, before `check-python` says its line); Python 3.11 for the generator and the tests; GNU Make 3.81 and later
**Primary Dependencies**: none added — `hashlib`, `subprocess`, `json`, `os` and git
**Storage**: one JSON file per project per worktree under `<git-dir>/slipwai/`, with a pending note beside it during a run
**Testing**: `unittest` (`make test TESTS=…`): the fixture project's real `make verify` with stand-in tools on `PATH`
**Target Platform**: wherever a generated project runs its gate: Linux, macOS, Windows under Git Bash
**Project Type**: a generator; the change is to what a generated project receives
**Performance Goals**: SC-001 — under 1 s for the whole reuse run on the Independent Test's project (budget from the gaps stage's measurements: about 0.25 s)
**Constraints**: no new dependency, setting file or ignore line; a full passing run's output is byte for byte today's; no path of an executable in the stamp
**Scale/Scope**: one new toolkit script, one new generator module, the tool table, the page, one fragment, nine test files

## Constitution Check

*GATE: evaluated against `.specify/memory/constitution.md` before research; re-checked after design.*

| Principle | Touched? | How this slice satisfies it |
|---|---|---|
| I. A generated project owns its files and passes its own gate (NON-NEGOTIABLE) | Yes | *A scoped or memoised gate MUST be additive*: no check is removed or narrowed; the trunk and CI neither read nor write a stamp and print what they print today (e21); `make ci` always runs (e23); the stamp is written only by a run in which every check ran and passed (e10). No file of a project's is touched: the stamp is under the git directory and no ignore line is added (e28, e30). The matrix tests pass each starter's own gate (e29). |
| III. Simplicity | Yes | One script with two verbs, one file, no setting beyond the variable FR-001 names. No abstraction layer: the key builder is functions in that script. |
| V. Acceptance-driven development | Yes | Every rule a RED-GREEN-REFACTOR cycle at `make verify`'s command line; stand-ins are executables written in the test tree, no mocking framework. |
| VIII. Versioning and breaking changes | Yes | MINOR, as the row names it: `VERIFY_FORCE` is new, every existing answer means what it meant. `VERSION` stays `1.6.0.dev0`; the fragment claims MINOR. |
| XIII. Fast feedback (a target here) | Yes | No clock in the suite (e19 holds the cause); the time is the demo's (e20). |
| XIV. Agent-generated change meets the same bar (NON-NEGOTIABLE) | Yes | Increment commits with the quickest relevant tests green; both full gates on the final tip; the hand runs the demo as the actor with the real toolchain. |
| II, IV, VI, VII, IX, X, XI, XII, XV | No | No retry path, domain code, contract, telemetry, secret, pipeline or type changes. |

*Additional Constraints* — persisted data records facts true on any machine, never a file path: the stamp holds digests, tool names with the lines they reported, an instant and a result, and e15 holds that no path is in it (D75's rule 10). **Gate result:** no violation; *Complexity Tracking* stays empty. **Post-design re-check:** unchanged.

## Project Structure

```text
assets/toolkit/scripts/verify-stamp.py        # new — `reuse` and `record`: eligibility, the key, the stamp, the lines
src/slipwai/project/gate.py                   # new — the stamped `verify` rule, `verify-checks`, the VERIFY_STAMP variable; `gate_target` chooses it or today's text
src/slipwai/project/adopted_targets.py        # `GATE` and `NOTHING_CONFIRMED` stay; `gate_target` moves or delegates
src/slipwai/project/makefile.py               # the transport's line names `verify-checks`; `.PHONY`; nothing else (326 of 350 lines today)
src/slipwai/backends.py                       # the machine-supplied tools per backend, beside `BACKEND_TOOLING`
<the page a generated project gets about its gate>   # R13 — found at the first cycle of US3 (research item 7)
docs/learn-generate.md                        # where it shows the gate's output, if the reuse line belongs there
changelog.d/verify-stamp.md                   # MINOR
tests/stamp_fixture.py                        # new — the fixture project (generated once per class, copied per test), the stand-ins and their log, `run_gate()`
tests/test_verify_stamp_pinned.py             # new — the Pin stage's holds
tests/test_verify_stamp_reuse.py              # new — R1, R2
tests/test_verify_stamp_key.py                # new — R3, R4
tests/test_verify_stamp_tools.py              # new — R5
tests/test_verify_stamp_inputs.py             # new — R6
tests/test_verify_stamp_where.py              # new — R7, R8
tests/test_verify_stamp_runs.py               # new — R9, R10
tests/test_verify_stamp_file.py               # new — R11
tests/test_verify_stamp_ships.py              # new — R12, R13
```

**Structure Decision**: one deployable, `slipwai-graph` (kind `tool`, path `.`, purpose confirmed); one bounded
context — the factory. The strategy on the map is `leave-it` (D5, as a person left it): the code lands where the
code it changes already is. Every file under `tests/` and `src/` is held to 350 lines; a test file that would pass
it is split by rule, never grown. How the toolkit's scripts reach a project and a migrated one, and what lists
them, is [research.md](research.md) item 6, read before the first cycle.

## What this slice changes in code that was here (for the Pin stage)

1. The `verify` rule of a generated project's `Makefile`: which checks a full run runs, in which order, and the
   closing line — for a project with a transport (the `check-openapi` line inside its markers) and without, and
   that `./init --http none` leaves a gate that runs with no `check-openapi`. Not pinned, changed on purpose: that
   `verify` itself carries the prerequisites.
2. The `verify` rule of a project with a wrapped application, and the refusal while nothing is confirmed: byte for
   byte what they are (the slice must not change them).

## Delegation

One story at a time: `[US1]`, then `[US2]`, then `[US3]`, each one `drive-implement` delegate (story/rule). All
three write `verify-stamp.py`, so they are not concurrent. The fragment is written in the commit that first changes
what `make verify` does (`AGENTS.md`: the entry in the same commit) — the first cycle of `[US1]` — and `[US3]`
completes it.

## Complexity Tracking

None.
