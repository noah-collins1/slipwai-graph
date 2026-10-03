# Tasks: S20-slice-scope-root — a slice branch in a root-adopted repository passes the slice-scope gate

**Input**: [plan.md](plan.md) (*The example map* R1–R7 is what the tasks cut on; *Design*; *Pin*),
[research.md](research.md), [data-model.md](data-model.md), [quickstart.md](quickstart.md); acceptance criteria
AC-S20-1 … AC-S20-13 in `specs/001-faster-slipwai/spec.md` under `### S20-slice-scope-root`; decisions D9, D12,
D13, D17, D18, D19 in `specs/001-faster-slipwai/decisions.md`. No `examples.md`: a method slice with no screen and
no event model.

**Branch**: `adopt-method` (D12). No `slice/` branch, no push, no claim. One commit per task.

**Delegation** (`.specify/drive.json`: `delegate: story`, `cycle: rule`): these tasks carry no user-story tag, so
they are delegated **per rule**, one delegate per task, each its own RED-GREEN-REFACTOR increment and its own commit.

**Constraints that hold for every task** (plan.md *Constraints*): standard library only, no mocking framework (tests
drive each script as a subprocess in a temporary repository, the seam `tests/test_parallel_slices.py`
`SliceScopeGateTest.check` already uses; a root-adopted repository is made with `tests/test_adopt.py`'s
`repository()` and `slipwai(repo, "adopt", "--yes")`); nothing under `delivery/scripts/`, `tools/`, the `Makefile`,
CI or hook settings changes (the fix reaches this repository through a person's `slipwai migrate`, D9);
`tests/test_parallel_slices.py` is not edited; `VERSION` stays `1.5.2.dev0`; no setting, flag or file added to a
generated project; the `make check-structure` and `tests/test_line_widths.py` budgets hold at every commit. Each
RED is observed failing for its stated reason before the production edit.

**The Pin stage** (`/characterise`, plan.md *Pin*) is the ladder's step after this file and before T001; it records
the three pinned behaviours in `delivery/survey/pinned.md` and is not a task here.

## Format: `[ID] [P?] Description` — each task is one increment, one commit

`[P]` marks a task whose files are disjoint from every sibling's it could run beside; see *Parallel opportunities*.

---

## Phase 1: Implementation stage

### T001 — A deployable at `.` is the fallback owner of every path nobody else claims (R1, R3, R4, R7 · AC-S20-1, -6, -7, -8, -9, -13)

- [x] **Done** — `c281272` (drive-implement · model: sonnet · delegated, fresh context · rule/rule · split=0). RED seen as assertion failures (*outside every deployable*) for R1 e1–e4 and R3 e2; R1 e5 and R3 e1 green on arrival, as held. The fixture is a hand-built repository in the adopted layout (script under `delivery/scripts/`), not a real `slipwai adopt`; R1 e2's root `docs/x.md` is green only where the delivery directory is not the root, which is the adopted layout.

**Rule R1** — on a `slice/<id>` branch in a repository whose one deployable is at `.`, a file that is the
application's own is the slice's. **R3** (a subdirectory deployable owns its own), **R4** (nothing moves under
`apps/`) and **R7** (the PATCH fragment) are folded in here and are not tasks of their own: R3's examples are the
other half of the same `owning_app()` ordering (e2 is red until R1's fallback exists and e1 is the proof the
fallback does not outrank a subdirectory service), R4's one example is an existing test that is green before and
after and so has no RED of its own, and R7 is a file whose check (`tests/test_changelog.py`) is already in the
suite; scheduling any of them apart would instruct the implementer to write a test that passes the moment it is
written. The fragment rides in this commit because plan.md (Principle VIII) puts it in the commit that changes the
first asset.

**RED** (new `tests/test_slice_scope_root.py`, one example at a time, each seen failing with *outside every
deployable* before the edit):
- R1 e1 `tests/test_x.py` → exit 0, *touches only what one slice may*. e2 `worker/x.py`, root `scripts/x.py`, root
  `docs/x.md` → green. e3 root `requirements.txt` (the fixture's manifest) and a `pyproject.toml` → green. e4 the
  deployable's path recorded as `./` → same answers. e5 a deployable with `path: ""` owns nothing: its file stays
  *outside every deployable* (passes today; it guards the fallback from over-reaching, held in this task).
- R3 e1 a second `service` under `apps/api` and a model block naming another service for the slice,
  `apps/api/x.py` changed → *service `api` is not slice …'s*. e2 same branch, `tests/test_x.py` → green.

**GREEN** — `assets/toolkit/scripts/check-slice-scope.py`: `Scope.owning_app()` tries every deployable whose
stripped path is not `.` first, in today's order and with today's test; a deployable whose stripped path is `.`
(`./` too) is returned only when none matched; an empty or missing path still owns nothing. Add the root case to
the docstring in the same plain words. Add `changelog.d/slice-scope-root-deployable.md`, first line `PATCH`, saying
what changed and that it asks nothing of a repository already generated.

**REFACTOR:** only if the root test duplicates `SliceScopeGateTest`'s helper; keep its own copy small.

**Verify:** `python3 -m unittest tests.test_slice_scope_root tests.test_parallel_slices.SliceScopeGateTest
tests.test_changelog` green with `tests/test_parallel_slices.py` untouched (R4 / AC-S20-9, including a root
`Makefile` refused under `apps/`). Commit.

**Known window:** after T001 and before T002 the root `Makefile`, `project.json` and the rest of the host surface are
not yet refused at a root deployable. R2's refusals cannot be observed red before the fallback exists (today
everything is refused), so the order is forced. The branch carries nothing pushed (D12); T002 closes the window
the next commit.

**Files:** `assets/toolkit/scripts/check-slice-scope.py`, `tests/test_slice_scope_root.py` (new),
`changelog.d/slice-scope-root-deployable.md` (new).

### T002 — The host surface stays the host's at a root deployable (R2 · AC-S20-2, -3, -4, -5)

- [x] **Done** — `5345251` (drive-implement · model: sonnet · delegated, fresh context · rule/rule · split=0). RED seen as `<path> was let through` for e1, e2, e4, e5, e6, e7, e8; e3 green on arrival. One example added at the host's request: `test_a_real_adoption_at_the_root` drives `slipwai adopt --yes` and checks the adopted tree's own `delivery/scripts/check-slice-scope.py`; it was not seen red before the code (its first run errored in its own setup) and was shown to have teeth afterwards by running it against the script at `c281272` (*Makefile was let through*). A real adoption records `kind: application`.

**Rule R2** — where the root deployable would claim a path, the host's surface is refused with today's *outside
every deployable … Land it on `main` before the fan-out*. Needs T001 (the fallback it restricts).

**RED** (in `tests/test_slice_scope_root.py`; each fails after T001 because the root deployable now claims the path):
- e1 one at a time: root `Makefile`, `project.json`, `.specify/x.json`, `.github/workflows/x.yml`, `AGENTS.md`,
  `.claude/settings.json` → refused. e2 `<delivery>/scripts/x.py`, `<delivery>/skills/x/SKILL.md`,
  `<delivery>/commands/x.md`, `<delivery>/Makefile`, `<delivery>/baseline.json` → refused.
- e4 `<delivery>/survey/pinned.md` and `<delivery>/survey/running.md` → green; `<delivery>/survey/survey.md` →
  refused. e5 a path listed in `<delivery>/.written` and on no fixed name → refused. e6 `.written` with the CI
  gate's line deleted → the gate workflow is still refused. e8 `ci.gate` naming a file outside the fixed CI names
  (say `ci/gate.yml`) → refused.
- Held in this task, green on arrival and so not a RED of their own: e3 `<delivery>/docs/x.md` → today's *the docs
  are the host's* (the order in `violation()` answers docs before `code_violation()`); e7 `.written` absent → the
  fixed list holds, no crash. They guard the edit below and belong to the rule.

**GREEN** — `check-slice-scope.py`: constants and one predicate for the D18 host surface (the delivery directory
when it is not the root, less `survey/pinned.md` and `survey/running.md`; `project.json`; root `Makefile`;
`.specify/`; `.github/`, `.gitea/`, `.forgejo/`, `.gitlab/`, `.gitlab-ci.yml`, `ci.gate` where `project.json` records
a string; `AGENTS.md`, `CLAUDE.md`, `.claude/`, `.codex/`, `.cursor/`, `.gemini/`, `.opencode/`; and every line of
`<delivery>/.written` where it exists — only ever an addition to the fixed list). `code_violation()` asks it when
the owner is the root deployable and returns today's message unchanged. The order in `violation()` does not change.
Update the docstring.

**REFACTOR:** group the constants beside `DOCS`/`MODEL`; keep `check-structure` and line-width budgets.

**Verify:** `python3 -m unittest tests.test_slice_scope_root tests.test_parallel_slices.SliceScopeGateTest` green,
the second file untouched (R4 holds again). Commit.

**Files:** `assets/toolkit/scripts/check-slice-scope.py`, `tests/test_slice_scope_root.py`.

### T003 [P] — `check-decisions` reads the register id whole (R5 · AC-S20-10, -11)

- [x] **Done** — `5cb9d83` (drive-implement · model: sonnet · delegated, fresh context · rule/rule · split=0). RED seen: e1 exit 1 with *no row for S00*, e3 naming `S00` instead of `S00-run-path`; e2 and e4 green on arrival. `lacking_rows()` is the one id-matching function; `baseline()` uses it too, so a baselined row is not written for a slice already recorded under its prefix.

**Rule R5** — a done slice is found in the adversary log under its whole id or its bare prefix. Disjoint from T001
and T002 (different script, different test file).

**RED** (new `tests/test_register_ids.py`, a generated project's register driven through `check-decisions.py`):
- e1 register `` `S00-run-path` `` and a row headed `## S00-run-path · …` → pass (fails today: the id reads as
  `S00`, no row found). e3 neither heading → fails naming `S00-run-path` (fails today by naming `S00`).
- Held in this task, green on arrival: e2 row `## S00 · …` → pass (D17's rows, D19); e4 register `S1`, row
  `## S1 · …` → pass as today, and the header and separator rows are no ids.

**GREEN** — `assets/toolkit/scripts/check-decisions.py`: `done_slices()` reads the first cell's leading id whole
(letters, digits, then `[A-Za-z0-9._-]*`), so `Slice` and `---` still are no ids; `check_adversary_rows()` accepts
a row headed with the whole id or the bare prefix `[A-Za-z]+\d+`, and its finding names the whole id.

**REFACTOR:** one small id-reading function; no shared module (plan.md, Principle III).

**Verify:** `python3 -m unittest tests.test_register_ids tests.test_cruise_record` green. Commit.

**Files:** `assets/toolkit/scripts/check-decisions.py`, `tests/test_register_ids.py` (new).

### T004 — `check-benchmark` finds the record under the whole id (R6 · AC-S20-12)

- [x] **Done** — `d4a85da` (drive-implement · model: sonnet · delegated, fresh context · rule/rule · split=0). RED seen: e1 warned of `slices/S00`, e3 named `slices/S00` instead of `slices/S00-run-path`; e2 and e4 green on arrival. `check()` is `done_slices()`'s only caller in the script; the not-closed warning names whichever folder holds the record.

**Rule R6** — the record is looked for at `slices/<whole id>/`, then `slices/<prefix>/`. Shares
`tests/test_register_ids.py` with T003, so it follows T003.

**RED** (in `tests/test_register_ids.py`): e1 `slices/S00-run-path/benchmark.json` closed → no warning (fails
today: warns of `slices/S00`). e3 neither record → one warning naming `slices/S00-run-path`. Held, green on
arrival: e2 only `slices/S00/benchmark.json` → no warning; e4 register `S1` → as today.

**GREEN** — `assets/toolkit/scripts/agents/benchmark.py`: `done_slices()` reads the id whole as in T003;
`check()` looks for `slices/<id>/benchmark.json` and, where that directory holds none, `slices/<prefix>/`; its
findings name the whole id's path.

**REFACTOR:** only if the id-reading function now duplicates T003's beyond what Principle III accepts.

**Verify:** `python3 -m unittest tests.test_register_ids tests.test_benchmark_brackets` green. Commit.

**Files:** `assets/toolkit/scripts/agents/benchmark.py`, `tests/test_register_ids.py`.

---

## Phase 2: Convergence stage — after the converge verdict and gaps pass, before the demo

No task is written ahead of the verdict. The gates (`make verify`, `make -f delivery/Makefile verify`) run once on
the tip before the demo (AC-S20-13); the demo is `quickstart.md` run from this checkout against a temporary
repository adopted at `.`; the Convergence stage holds the map to what the slice did.

---

## Dependencies & Execution Order

T001 → T002 (T002 restricts the fallback T001 creates, and edits the same script and test file).
T003 has no dependency on T001/T002. T003 → T004 (one test file). Both chains end before the converge pass.

## Parallel opportunities

- **T003 `[P]` beside the chain T001 → T002.** T003 writes `assets/toolkit/scripts/check-decisions.py` and
  `tests/test_register_ids.py`; T001 and T002 write `check-slice-scope.py`, `tests/test_slice_scope_root.py` and the
  changelog fragment. The manifests are disjoint. Commits are still one per task, made one at a time: the host
  serialises the commits, since all land on `adopt-method`.
- **Not parallel:** T001 and T002 (one script, one test file); T003 and T004 (one test file,
  `tests/test_register_ids.py`; T004 is therefore not marked `[P]`); T004 beside the slice-scope chain is possible
  by manifest (`benchmark.py`) only after T003, so it waits for T003.
- Most delegates at once: two (one on T001 → T002, one on T003 → T004). The gates at the end read the whole tree and
  run alone.

## Design review

No screen in this slice

## Convergence

*(Written by the Convergence stage: gate evidence, converge verdicts, gaps pass, demo and archive.)*
