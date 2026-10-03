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

### Converge pass 1 — 2026-10-03, on `6379351` — **NOT CONVERGED** (one HIGH)

Quick suite (`make test TESTS="test_slice_scope_root test_register_ids test_parallel_slices test_cruise_record
test_benchmark_brackets test_changelog"`): 50 tests, OK, skipped=1. No file was mutated; every reproduction ran in a
temporary directory against a copy of the asset scripts or a real `slipwai adopt --yes` of
`tests/fixtures/adopt/python-worker`.

**Constitution, by principle the diff touches.**
- **I. A generated project owns its files and passes its own gate** — *unmet in one case*: the two id readers crash
  on a model slice id with no letters-then-digits head (T005). Otherwise met: nothing under `delivery/` changed
  (diff is 3 asset scripts, 2 tests, 1 fragment), and the host surface is still refused
  (`check-slice-scope.py:329`, `:242–256`).
- **III. Simplicity** — met: two tuples and one predicate (`check-slice-scope.py:94–97`, `:242`); one function
  `lacking_rows()` (`check-decisions.py:193`); no setting, no shared module.
- **V. Acceptance-driven** — met for the criteria as written, with the holes T006 names (ten of sixteen fixed host
  names have no example).
- **VIII. Versioning** — met in form: `changelog.d/slice-scope-root-deployable.md` line 1 `PATCH`, `adopt` labelled
  experimental, `VERSION` `1.5.2.dev0`, `test_changelog` green. Its last sentence (*asks nothing of a repository
  already generated*) is false until T005 lands.
- **XIV. Agent-generated change meets the same bar** — met: one commit per task, RED recorded per task.

**By level.**
1. *Checker logic.* AC-S20-1, -2, -3, -4, -5, -6, -7, -9 proven on a real adoption (probes: `tests/test_x.py`,
   `requirements.txt`, `delivery/survey/pinned.md` exit 0; `Makefile`, `.specify/drive.json`,
   `.github/workflows/x.yml`, `delivery/.written`, `delivery/survey/survey.md`, `delivery/docs/x.md` exit 1).
   AC-S20-8 holds for the root's `./`; a *subdirectory* spelled `./apps/api` is not proven and fails open (T007).
   AC-S20-10, -11, -12 hold for ids of the form letters-digits-slug; not for ids from the model of any other form
   (T005). D18's list is implemented exactly as written; what the list leaves out is T008.
2. *Command line.* Exit codes and messages are today's on every path probed. The exception is T005: a traceback and
   exit 1 where the same project got a finding or a warning and exit 0.
3. *What ships beside the scripts.* Swept `assets/`, `docs/`, `src/slipwai/project/` for `check-slice-scope`,
   *outside every deployable*, the register id and the adversary row heading: `first-slice.md`, `guidance.py`,
   `parallel_slices.py`, `docs/delivery-loop.md`, `docs/adopting.md` describe the rule generically and none says a
   root deployable owns nothing or that an id is cut to its prefix. Nothing is now wrong; no page is owed.
4. *Published contract.* Fragment level and label correct; no catch-up paragraph owed once T005 lands (a merge
   brings the change whole). `VERSION` correct.
5. *Tests.* Holes in T006. Everything else has an example that names its criterion.

### T005 — **HIGH** — A done slice whose id has no letters-then-digits head crashes both id readers (R5, R6 · AC-S20-13, D19, Principle I)

- [x] **Done** — `06850ab` (drive-implement · sonnet · fresh context). RED: the traceback for `place-order` in `check-decisions`, in `--adversary-baseline` and in `check-benchmark` (the third seen in the run summary only). Sweep: three unguarded prefix derivations, all closed; an id with no letters-then-digits head is looked up whole.
- [x] `re.match(r"[A-Za-z]+\d+", ident).group(0)` is applied to every id in `done_slices()`, which also holds ids
  from `implemented()` — the model's `id:` taken verbatim, constrained by nothing (`event-model/check.py` accepts
  any string; `SLICE_BRANCH` allows `[A-Za-z0-9][A-Za-z0-9._-]*`). For `place-order` or `1-checkout` the match is
  `None`.
- **Reproduction** (temporary project: `project.json`, a copy of `assets/toolkit/scripts`, `docs/event-model/model.yaml`
  with `- id: place-order` / `status: implemented` / `spec: specs/f/spec.md`, `specs/f/slices/place-order/`):
  `python3 scripts/agents/benchmark.py check` → `AttributeError: 'NoneType' object has no attribute 'group'`
  (`agents/benchmark.py:670`), exit 1; with the scripts at `f151b80` → two warnings, exit 0. With a `decisions.md`
  and an adversary log lacking the row, `python3 scripts/check-decisions.py` → the same error in `lacking_rows()`
  (`check-decisions.py:193–198`) instead of *no row for place-order*; `--adversary-baseline` goes through the same
  function. Both targets are in `verify`, so a project that was green turns red on `slipwai migrate` — which a
  PATCH may not do and the fragment says it does not.
- **The class, swept:** every place the bare prefix is derived — three (`benchmark.py:670`,
  `check-decisions.py` `lacking_rows()`, and through it `baseline()`). The register regex itself (`done_slices()`
  in both files) guards with `if found`. Fix all three with one rule: an id with no such head has no prefix and is
  looked up whole, as before the slice.
- **RED** in `tests/test_register_ids.py`: a model slice `place-order`, implemented, naming the feature — (a)
  `check-benchmark` exits 0 and warns of `slices/place-order`; (b) `check-decisions` with no row fails naming
  `place-order`, with the row passes.

### T006 — **MEDIUM** — Ten of the sixteen fixed host names, and three behaviours, have no example (AC-S20-2, -8, D19)

- [x] **Done** — `40ce2a6`. Held, green on arrival: one table over the 24 fixed host names, a missing/None/non-string `path`, a refusal under `./`. Teeth shown by deleting `.opencode`, `.circleci`, `CLAUDE.md`, `.gitlab-ci.yml` one at a time (red each time, restored). The `--adversary-baseline` example is in `06850ab` (green on arrival; teeth not shown).
- [x] `tests/test_slice_scope_root.py` refuses `Makefile`, `project.json`, `.specify/`, `.github/`, `AGENTS.md`,
  `.claude/`. No test names `.gitea`, `.forgejo`, `.gitlab`, `.gitlab-ci.yml`, `CLAUDE.md`, `.codex`, `.cursor`,
  `.gemini`, `.opencode` (`grep -c` for each over both new test files: 0) — deleting any from
  `check-slice-scope.py:94–96` leaves the suite green. Also without an example: a deployable with the `path` key
  *missing* (AC-S20-8 says empty or missing; only `""` is tested); a refusal under `path: "./"` (only greens are);
  `--adversary-baseline` writing no row for a slice already recorded under its bare prefix (T003's note claims it).
- **The class:** one table-driven example over every name in AC-S20-2, so the criterion's list and the test's
  list are the same list.

### T007 — **MEDIUM** — A subdirectory deployable spelled `./apps/api` beside a root deployable loses its files to the root (AC-S20-7, -8)

- [x] **Done** — `bb594ab`. RED: `./apps/api` forms let through to the root, `ci.gate` as `./ci/gate.yml` let through. One function, `recorded_path()`, for deployable paths and `ci.gate`; only the `./x` forms answered wrongly.
- [x] `service_path()` strips only `/`, so `./apps/api` never prefixes a git path. Before the slice the file was
  refused (*outside every deployable*); now it falls to the root deployable and the other-service rule is skipped.
- **Reproduction** (temporary repository, root `shop` at `.`, `api` of kind `service`, model block `service: shop`,
  `apps/api/x.py` changed on `slice/S1`): path `apps/api` → *service `api` is not slice `S1`'s*; `apps/api/` → the
  same; `./apps/api` → exit 0, *touches only what one slice may*.
- **The class, swept:** the spellings of a recorded path — `.`, `./`, `""`, missing, `x/`, `./x`. Only `./x` answers
  wrongly; `ci.gate` has the same reader (`gate.strip("/")`, `check-slice-scope.py:253`) and the same hole for
  `./ci/gate.yml`. One normalising function for both.

### T008 — **MEDIUM** — a question for the host, not a task to implement: D18's harness and CI names are a subset of what the checker ships beside

- [x] **Done** — `5082b5f` (as D20 decided). RED: the five harness paths, every added CI and Makefile name, and the `CI_FORGES` coverage test (seven keys). Held: a missing, unreadable or malformed registry; `.gitignore` and git hooks. A malformed row adds nothing while well-formed rows beside it still count; the registry, `.written` and `ci.gate` are read once per run.
- [x] D18 fixes the list and AC-S20-2 repeats it; the diff implements it exactly. On a real root adoption these are
  let through (each probed, exit 0): `.mcp.json`, `opencode.json`, `GEMINI.md`, `.agents/skills/x/SKILL.md`,
  `.kiro/settings/mcp.json`, `.circleci/config.yml`, `Jenkinsfile`, `.gitignore` (which carries the factory's
  `slipwai:delivery` block), `.githooks/pre-commit`, `.pre-commit-config.yaml`, `GNUmakefile`.
  `assets/toolkit/scripts/agents/registry.json`, installed beside the checker, names about thirty harnesses'
  projection directories and context files: Codex's skills are `.agents/skills` (not `.codex/`), Gemini's context
  file is `GEMINI.md`, Claude Code's and opencode's MCP files are `.mcp.json` and `opencode.json`. None is in
  `.written` (projections are made by `make agents`). D18's stated purpose is that a slice cannot rewrite the run's
  settings.
- **The decision owed:** keep the list as decided; extend the floor by name; or read the harness names from
  `registry.json`. This pass does not choose. Not graded higher because the criteria are met as written and the
  gate on `main` and CI still see the change.

**Answered by D20** (drive-skipper, cruise iteration 3) — T008 is now a task to implement, in
`assets/toolkit/scripts/check-slice-scope.py` and `tests/test_slice_scope_root.py`, against AC-S20-14 to AC-S20-16
in `spec.md`: harness paths read from `<delivery>/scripts/agents/registry.json` (tolerantly — absent, unreadable or
malformed adds nothing and never a traceback); the CI names of `CI_FORGES` and the `GNUmakefile`/`makefile`
spellings added by name, with a test holding the checker's CI names to every key of `CI_FORGES`; git hooks and
`.gitignore` green. RED: each newly refused path let through today; the hooks and `.gitignore` examples are held,
green on arrival.

### T009 — **LOW** — Delivery at the root with a deployable at the root leaves `.written` itself writable (R-3)

- [x] **Done** — `9e82aad`, `d0d69fc` (docstring). RED: `.written` let through where delivery is the root. D18 not widened.
- [x] Where `DELIVERY` is `.` the delivery clause is skipped, so `.written`, `baseline.json` and `survey/` are the
  slice's unless `.written` lists them, and the checker reads `.written` from the slice's own tree. research.md R-3
  assumes no project is laid out so; nothing checks the assumption. Not reproduced — read from
  `check-slice-scope.py:248–256`.

### Converge pass 2 — 2026-10-03, on `4f16fd5` — **CONVERGED** (three LOW appended; nothing CRITICAL or HIGH)

Quick suite (`make test TESTS="test_slice_scope_root test_register_ids"`): 38 tests, OK. No tracked file was
changed; every probe ran in a temporary directory against a copy of `assets/toolkit/scripts/check-slice-scope.py`
and the shipped `agents/registry.json`. `make verify` and `make -f delivery/Makefile verify` were not run by this
pass (they were running in the checkout); AC-S20-13's last clause rests on them.

**Pass 1's tasks, each as its class.**
- **T005 — closed.** Every derivation of the bare prefix is guarded: `agents/benchmark.py:671–674` (`head and …`),
  `check-decisions.py:197–201` (`headed()`, which `baseline()` goes through). No other unguarded `.group(` on a
  register id in either file. Examples: `tests/test_register_ids.py:130–163` (`IdWithoutAPrefixTest`, three).
- **T006 — closed.** `tests/test_slice_scope_root.py:271–285`: 24 names written out in the test, equal in number to
  `HOST_FILES` (13) plus `HOST_DIRECTORIES` (11) at `check-slice-scope.py:98–102`; a missing/None/non-string `path`
  (`:287`), a refusal under `./` (`:293`), the baseline beside a bare row (`test_register_ids.py:165`).
- **T007 — closed.** One function, `recorded_path()` (`check-slice-scope.py:106–113`), read by `service_path()`
  (`:277`) and by `ci.gate` (`:322`); `x`, `x/`, `./x`, `./x/`, `.//x`, `.`, `./`, `./.` held at `:192–210`.
  Probed besides: `apps/api/.` beside a root spelled `./` gives the other-service answer's owner; `apps/apix/` is
  not taken for `apps/api`.
- **T008 — closed as D20 decided.** Clause by clause: the six fields and no other (`:143–144`); every row, no
  installed filter (`:129`); `~` and `/` skipped (`:133`); more than one segment makes the first segment a
  directory, one segment a file (`:134`); absent, unreadable, not JSON, not an object, `harnesses` not a list, a row
  not an object or with a wrong-typed field add nothing (`:123–126`, `:129`, `:140`, `:149–150`, `:153`) while
  well-formed rows beside it count; CI names and Makefile spellings by name (`:98–101`), held to `CI_FORGES` by
  `tests/test_slice_scope_root.py:259`; `ci.evidence` not read (no occurrence); hooks and `.gitignore` green
  (`:266`); all of it only where the root deployable would own the path (`:400`), read once per run (`:316`), so a
  project with no deployable at `.` never opens the registry. On the shipped registry every in-repository path is a
  root file or sits under a dot-directory, so no single-segment directory is misread as a file. Two edges are T011
  and T012.
- **T009 — closed as its instance, by decision; the rest of its class is T010.** `check-slice-scope.py:307–310`
  with the example at `tests/test_slice_scope_root.py:298`.

**Constitution, by principle the diff touches.**
- **I. A generated project owns its files and passes its own gate** — met. Nothing under `delivery/scripts/`, `src/`
  or `VERSION` differs from `f151b80`; a project with its deployables under `apps/` reaches none of the new code
  (`check-slice-scope.py:400`); the id readers no longer exit on a traceback (`benchmark.py:671`,
  `check-decisions.py:198`). The scoped gate only refuses more than D18's (`:304`), never less: additive.
- **III. Simplicity** — met: one normalising function (`:106`), one registry reader in two small functions
  (`:116`, `:138`), one cache (`:316`); no setting, no new file in a project, no shared module.
- **V. Acceptance-driven** — met: each of AC-S20-1 to -16 has a named example; T006's table is written in the test,
  not read from the checker; RED recorded per task, held examples said to be held.
- **VIII. Versioning** — met: `changelog.d/slice-scope-root-deployable.md:1` `PATCH`, `adopt` labelled experimental
  (`:3–4`), `VERSION` `1.5.2.dev0`. The fragment is true of what ships: any spelling make reads (`:98`), every
  system `adopt` recognises (test `:259`), the registry's names (`:116`), `.written` and the delivery directory less
  the two survey pages (`:304–311`), hooks and `.gitignore` the repository's own, the whole id with the bare prefix
  still accepted. *Asks nothing of a repository already generated* now holds (T005).
- **XIV. Agent-generated change meets the same bar** — met: one commit per task, each naming PATCH.

**By level.**
1. *Checker logic.* As above; `recorded_path()` and the registry reading answer as D20 and AC-S20-7, -8, -14 to -16
   say, on the shipped registry and on malformed ones.
2. *Command line.* Exit codes and messages are today's on every path probed; two tracebacks remain on inputs no
   criterion names (T011).
3. *What ships beside the scripts.* The checker's docstring (`:28–37`) says the registry, the spellings and the
   root-delivery case. No other page was re-swept this pass; pass 1's sweep found none owed and nothing since
   changed a page.
4. *Published contract.* One fragment, PATCH, wording true. Not proven here: the two full gates.
5. *Tests.* No hole found against the criteria. The delivery-at-root example asserts `scripts/x.py` green, which is
   T010's question, not an oversight.

### T010 — **LOW** — Delivery at the root with a deployable at the root: `scripts/`, `skills/`, `commands/`, `agents/`, `init` are the slice's

- [ ] T009 closed `.written`, `baseline.json` and the survey pages; the other delivery roots
  (`DELIVERY_ROOTS` in `src/slipwai/layout.py:34`) are the slice's there unless `.written` lists them, and
  `tests/test_slice_scope_root.py:303` holds `scripts/x.py` green. **Reproduction** (temporary repository,
  `delivery="."`, root deployable, shipped registry): `skills/x/SKILL.md` and `commands/drive.md` exit 0; `.written`,
  `baseline.json`, `Makefile`, `docs/x.md` exit 1. No factory path makes this layout (generated projects keep
  deployables under `apps/`; `adopt` defaults `--delivery delivery`, and `adopt --delivery .` would list the
  scripts in `.written`), so it is a decision for the host — name the delivery roots there, or say in D18 that the
  layout is unsupported — not a defect in what ships.

### T011 — **LOW** — Two inputs still end the checker on a traceback: an undecodable `.written`, and a registry nested past the recursion limit

- [ ] `host_names()` reads `.written` with no guard (`check-slice-scope.py:325`; the same read stood at pass 1), and
  `harness_paths()` catches `OSError, ValueError, AttributeError` but not `RecursionError` (`:125`).
  **Reproduction** (temporary repository, root deployable): `.written` holding `b"\xff\xfe\n"`, `tests/t.py` changed
  → `UnicodeDecodeError`, exit 1; `registry.json` holding 100 000 `[` → `RecursionError`, exit 1. Both files are the
  factory's and the host's, neither input is one AC-S20-5 or AC-S20-14 names (absent, unreadable, not JSON — an
  invalid-UTF-8 registry is handled), and the exit is still non-zero, so nothing is let through. One tolerant
  reader for both would close the class.

### T012 — **LOW** — What the registry says only in prose is not the host's, and a future row could take a source directory

- [ ] D20 reads six fields. The shipped registry's prose names `opencode.jsonc` (`projectMcp.how`) and
  `.amp/plugins/` (`hooks.why`); both exit 0 on a slice branch, as does `.vscode/mcp.json`, which no row names.
  `opencode.jsonc` is to `opencode.json` what `GNUmakefile` is to `Makefile`. In the other direction, a row naming
  `src/mcp.json` makes all of `src/` the host's (probed: `src/app.py` refused) — D20's first-segment rule working as
  written, harmless today because every first segment in the registry is a dot-directory, and held by no test.
  Either is a registry or D20 question for the host; neither is a criterion unmet.
