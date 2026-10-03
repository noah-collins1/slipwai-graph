# Feature Specification: Faster Slipwai

**Feature Branch**: `001-faster-slipwai`

**Created**: 2026-10-02

**Status**: Draft

**Input**: User description: "Make the delivery loop faster without weakening its gates: tree-shaped merges,
scoped and memoised gates, incremental event-model rendering, result contracts and difficulty scores so model
routing by difficulty and role can be measured. PRD: https://claude.ai/code/artifact/3b81e4c3-9a65-4f5b-882c-5b8ab4745d67
Analysis: https://claude.ai/code/artifact/dec16150-cc8a-4487-a1ea-60f8c2895e03"

## User Scenarios & Testing *(mandatory)*

The actor throughout is a developer driving or cruising a repository that slipwai generated or adopted. Every
story lands in the files the factory writes (`assets/`, `src/slipwai/project/`) and reaches existing projects,
including this repository, through `slipwai migrate`.

### User Story 1 - The gate stops repeating itself (Priority: P1)

A developer's slice runs `make verify` three times between start and `main`. Two of those runs see a tree the
gate has already passed. After this story the gate recognises a tree it has verified and returns in under a
second, runs its independent checks concurrently, syncs each toolchain once, and no longer walks `.venv` or
re-parses `model.yaml` five times.

**Why this priority**: Smallest change, no design decisions, removes two of three full gates per slice and
makes every later story's acceptance faster to run.

**Independent Test**: On a generated Python project, run `make verify` twice; the second run exits 0 in under a
second and says it reused the stamp. `make -j verify` passes with the same set of check outputs as the serial
run. `check-imports` enumerates at most 100 entries on the skeleton.

**Acceptance Scenarios**:

1. **Given** a tree the gate passed, **When** `make verify` runs again with no change, **Then** it prints the
   stamp it reused and exits in under 1 s.
2. **Given** a one-character change to a source file, **When** `make verify` runs, **Then** the full gate runs
   and a new stamp is recorded.
3. **Given** `VERIFY_FORCE=1`, **When** `make verify` runs on a stamped tree, **Then** the full gate runs.
4. **Given** a changed `scripts/check-*.py`, **When** `make verify` runs, **Then** the stamp is invalid and the
   full gate runs.
5. **Given** the skeleton, **When** `make -j verify` runs, **Then** every check that ran serially runs, in any
   order, and the exit code matches.

---

### User Story 2 - A slice branch runs the gate for what it touched (Priority: P1)

On a `slice/<id>` branch the developer runs `make verify-scoped`: ruff, byte-compile, imports and migrations on
the changed files, mypy from its incremental cache, and the tests of the contexts the slice touched plus the
contract tests of its `depends_on` neighbours. The merge root and CI still run the whole gate, with xdist.

**Why this priority**: The branch gate is what the merge tree (Story 3) relies on; it also makes the per-slice
mutation run proportional to the change.

**Independent Test**: On a branch touching one context, `make verify-scoped` runs only that context's tests and
its neighbours' contract tests; on `main`, `make verify-scoped` is the full gate; the full gate's findings on
the same tree are identical before and after.

**Acceptance Scenarios**:

1. **Given** a slice branch that changed one context, **When** `make verify-scoped` runs, **Then** only files
   of that context are linted and only its tests and its neighbours' contract tests run.
2. **Given** `main`, **When** `make verify-scoped` runs, **Then** it is `make verify`.
3. **Given** a branch that changed one production module, **When** `make mutation` runs, **Then** only that
   module's mutants run, for every backend, and `make mutation-full` still runs the whole module.
4. **Given** the merge root, **When** `make verify` runs, **Then** pytest runs with xdist and the pass/fail set
   equals the serial run's.

---

### User Story 3 - A fan-out converges through a merge tree (Priority: P2)

After a fan-out of L slices, each slice's adversary, mutation and scoped gate run in its own worktree in
parallel; passing slices merge pairwise into integration branches, each running the scoped gate on its union,
and the root runs the full gate once before `main` fast-forwards. Diagrams render once at the root.

**Why this priority**: This is the depth win, from L − 1 serial steps to ⌈log₂ L⌉, but it is the riskiest
change and depends on Story 2.

**Independent Test**: With a synthetic 8-slice fan-out on a generated project, the cruise stream shows Phase 4
steps overlapping in time, the longest chain of dependent merge steps is 3, one full `make verify` at the
root, and `main` only ever fast-forwards. A deliberate two-slice conflict parks that pair only.

**Acceptance Scenarios**:

1. **Given** 8 ready slices, **When** the fan-out finishes, **Then** adversary, mutation and scoped gate ran
   per slice concurrently.
2. **Given** 8 passing slices, **When** they merge, **Then** the longest dependent chain of merges is 3 and the
   root runs the full gate once.
3. **Given** two slices whose changes conflict, **When** their merge node rebases the later-in-split side and
   the conflict does not resolve, **Then** that subtree parks and the other subtrees continue.
4. **Given** a fan-out, **When** it converges, **Then** `make model` and `make model-drawio` run once at the root.

---

### User Story 4 - The event model is read and rendered incrementally (Priority: P2)

`make model` renders every diagram through one browser session and only re-renders diagrams whose source
changed. A per-slice stage is briefed with its own slice block and one hop of neighbours, not the whole model.
`check.py` and `board-plan.ts` are linear in the number of slices.

**Why this priority**: Rendering is quadratic over a feature today (one browser per diagram per merge) and the
per-slice stages read the whole model, so context grows with every slice.

**Independent Test**: On the 16-slice fixture, change one slice; `make model` launches one browser, rewrites
two diagrams and finishes in under 2 s. Bytes handed to the example-map stage for slice 16 equal those for
slice 1.

**Acceptance Scenarios**:

1. **Given** a 16-slice model with one changed slice, **When** `make model` runs, **Then** one browser launches
   and only that slice's and its segment's diagrams are rewritten.
2. **Given** a 200-slice synthetic model, **When** `make check-model` runs, **Then** it finishes in time linear
   in slices.
3. **Given** a per-slice stage, **When** it is briefed, **Then** the brief holds the slice's block and the
   blocks it reads from or is read by, and nothing else of the model.

---

### User Story 5 - The cruise runner costs the same at iteration 50 as at iteration 1 (Priority: P3)

The runner tails its logs from a stored offset, fingerprints by path and mtime, drift-checks only changed files,
and the skipper reads only decisions whose scope intersects the slice's neighbourhood.

**Why this priority**: Pure overhead, but it grows quadratically over a long run.

**Independent Test**: Time `entries()`, `delegate_use()` and `fingerprint()` at iteration 1 and at iteration
50 of a synthetic log; they are within noise of each other.

**Acceptance Scenarios**:

1. **Given** a 50-iteration log, **When** the runner starts iteration 51, **Then** its bookkeeping reads only
   the new entries.
2. **Given** an unchanged `specs/` tree a runner process has fingerprinted once, **When** `fingerprint()` runs
   again, **Then** it reads no file contents (D57).
3. **Given** 100 standing decisions of which 4 are in scope, **When** the skipper is briefed, **Then** it
   receives those 4 and the ones marked global.

---

### User Story 6 - Delegates hand back a contract and the planner scores difficulty (Priority: P3)

Every delegate ends with a fenced `result-contract` block; the planner writes a difficulty score per task;
`make benchmark` joins planned difficulty, observed difficulty, converge passes, escalations and mutation
survivors per task. A default-off `route_by_difficulty` setting logs the tier it would choose and changes no
model.

**Why this priority**: Measurement before behaviour: routing by difficulty is a later decision made with this
data in hand.

**Independent Test**: After one feature, every hand-back in the stream carries the block, `check-decisions`
holds its shape, `make benchmark` prints the joined table, and the routing log line appears while model choice
is unchanged.

**Acceptance Scenarios**:

1. **Given** a delegate hand-back without the block, **When** converge runs, **Then** it is a finding.
2. **Given** `tasks.md`, **When** the planner writes it, **Then** every task carries `difficulty: 1–5 — reason`.
3. **Given** `route_by_difficulty` off, **When** a worker is dispatched, **Then** a log line names the tier the
   policy would have chosen and the dispatched model is unchanged.

---

### User Story 7 - Slice blocks declare contract edges and the gate reports locality (Priority: P3)

A slice block may declare `provides:` and `requires:` contract ids; `check-model` validates them and reports
per-slice degree, boundary cut, cross-context edges and top-3 share.

**Why this priority**: Makes the bounded-degree assumption behind the whole design measurable, and gives the
scoped gate its neighbour contract tests.

**Independent Test**: A slice requiring a contract nothing provides fails `check-model` naming the slice; the
report appears in verify output and under `specs/<feature>/benchmark`.

**Acceptance Scenarios**:

1. **Given** a `requires` with no provider, **When** `make check-model` runs, **Then** it fails and names the
   slice and the contract.
2. **Given** a valid model, **When** `make check-model` runs, **Then** it reports degree, cut, cross-context
   edges and top-3 share.

---

### User Story 8 - Easily reversible decisions are approved provisionally (Priority: P3)

A decision the owner brief says to ask a person about no longer stops a slice when it is easy to revert. Each
decision entry carries a reversibility score computed from the tree; under a new `decide: provisional` setting
the skipper takes `easy` and `guarded` always-ask items as provisional, names the commits that revert them, and
batches them for the owner to ratify or revert; `hard` items still block. Added 2026-10-03 from the paper's
author's own experience: decision throughput, not tier design, was the problem the paper left unsolved.

**Why this priority**: It removes the decision-wait tax the run has already paid once (S24 on D54), without
widening what anyone may do to the merge root, CI, flags or stored data.

**Independent Test**: With `decide: provisional`, a fixture decision that changes a flag default (guarded)
proceeds as provisional with a revert range; the D54 fixture (one workflow line propagated by `migrate`) still
blocks; a run with an unratified provisional decision past its date ends `parked: ratify D<n>`, not `done`.

**Acceptance Scenarios**:

1. **Given** a new decision entry, **When** it is written, **Then** it carries `Reversibility: easy | guarded |
   hard` derived from its commits, dependants, flag, and whether a schema, contract, CI workflow or
   migrate-propagated file is touched.
2. **Given** `decide: provisional` and a `guarded` always-ask item, **When** the skipper decides, **Then** the
   entry is `Status: provisional · ratify by <date>` with `Revert: <range>` and the slice continues.
3. **Given** `decide: provisional` and a `hard` item, **When** the skipper decides, **Then** it is
   `unavailable: a person's approval` as today.
4. **Given** a provisional decision, **When** the owner sends `ratify D<n>` or `revert D<n>`, **Then** the
   status changes, and a revert applies the named commits in reverse, runs the gate, and names the slices that
   must re-enter the ladder.
5. **Given** an unratified provisional decision past its date, **When** the ready set is empty, **Then** the
   run parks on it instead of saying `done`.

---

### Edge Cases

- A stamped tree whose toolchain changed (new ruff, new mypy): the stamp key includes recorded tool versions,
  so the gate re-runs.
- `make -j` on a target that writes `.specify/`: such targets are declared `.NOTPARALLEL` locally.
- A merge-tree node where both sides changed the events module additively: the rebase succeeds; the scoped gate
  on the union runs contract tests of both.
- A model with one slice: `make model` launches one browser and renders three diagrams, as today.
- A harness that cannot delegate: the fan-out degrades to one slice at a time as today, but the gate stamps
  and the scoped gate still apply.
- Windows under Git Bash: worktree fan-out and `-j` are exercised by the matrix tests before release.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `make verify` MUST record a success stamp keyed by git tree hash, gate script hash and recorded
  tool versions, reuse it on an unchanged tree, and honour `VERIFY_FORCE=1`.
- **FR-002**: The gate's read-only checks MUST be declared so `make -j verify` runs them concurrently with the
  same results as the serial run; writers MUST be `.NOTPARALLEL` locally.
- **FR-003**: `./scripts/verify` MUST sync each toolchain once per invocation; `check-drawio` MUST skip
  `npm install` when the installed tree matches a committed lockfile.
- **FR-004**: `check-imports` and `check-migrations` MUST prune `.venv`, `node_modules`, `target/`,
  `__pycache__` and `.git` before descending, and read `project.json` once.
- **FR-005**: `model.yaml` MUST be parsed once per verify into a sidecar every consumer reads.
- **FR-006**: `make verify-scoped` MUST exist, MUST equal `make verify` on `main`, and on a `slice/<id>` branch
  MUST run per-file checks on changed files, mypy incrementally, and tests of touched contexts plus
  `depends_on` neighbours' contract tests.
- **FR-007**: The drive ladder MUST call `verify-scoped` at slice start and before the push, and the full gate
  once at the merge root.
- **FR-008**: `make mutation` MUST scope to the diff against merge-base for every backend; `mutation-full` MUST
  keep the whole-module run.
- **FR-009**: The root gate MUST run pytest with xdist where the project is marked parallel-safe (default on
  for new projects, with a one-line opt-out in `project.json`).
- **FR-010**: After a fan-out, Phase 4 MUST run per slice in its worktree concurrently; merges MUST form a tree
  with fan-in `drive.json.merge_fanin` (default 2); the root MUST run the full gate once; `main` MUST only be
  fast-forwarded; an unresolved conflict MUST park its subtree only.
- **FR-011**: `make model` and `make model-drawio` MUST run once per fan-out, at the root.
- **FR-012**: `render.ts` MUST render through one browser session and re-render only changed diagrams.
- **FR-013**: `check.py` cycle detection and `board-plan.ts` frame lookup MUST be linear in slices.
- **FR-014**: Per-slice stages MUST be briefed with the slice block and its one-hop neighbours; the model MAY
  be a single file with a sidecar index or split per slice (owner decision 3).
- **FR-015**: The runner MUST tail its logs from a stored offset, fingerprint by path and mtime, and drift-check
  only changed files. *Amended by D57:* the runner MUST fingerprint `specs/` by each file's path and content,
  opening a file only where its path is new or its size, modification time, change time or identity differ from
  what the runner recorded when it last read it. *Read by D58 and D59:* the offset is the runner process's own
  memory of the log it last appended to; the drift check is `health()` before an iteration.
- **FR-016**: Decision entries MUST carry a `Scope:` line; the skipper MUST be briefed with in-scope and global
  decisions only. *Read by D60:* every writer adds the line from `S02-runner-bookkeeping` on; an entry without
  one passes the gate and is carried as global; making absence a finding is a person's to approve.
- **FR-017**: Every delegate MUST end with a `result-contract` block of the shape in the PRD; `check-decisions`
  MUST hold it; a missing block MUST be a converge finding.
- **FR-018**: The planner MUST write a difficulty score and reason per task; `make benchmark` MUST join planned
  and observed difficulty with converge passes, escalations and mutation survivors.
- **FR-019**: `models.json` MUST gain a documented, default-off `route_by_difficulty` whose only effect is a log
  line naming the tier the policy would choose.
- **FR-020**: Slice blocks MAY declare `provides`/`requires`; `check-model` MUST validate providers and report
  degree, cut, cross-context edges and top-3 share.
- **FR-021**: Every user-visible change MUST carry a `changelog.d/` fragment naming its level; nothing in this
  feature is MAJOR.

- **FR-022**: `check-codegraph` MUST hash only files git reports changed since the last sync and run the
  SQLite integrity check in CI only; `check-ux-gates` MUST default `UX_GATES_SINCE` to the merge-base on
  `slice/<id>` branches and to everything on `main`.
- **FR-023**: `check-agents`, `check-speckit`, `check-extensions` and `check-constitution` MUST run only when
  their inputs changed since the stamp on a branch, and always on `main` and in CI.
- **FR-024**: The runner MUST compute `controls_signature()` once per iteration from mtimes, and run one
  codegraph sync per iteration unless a delegate reports changed files. *Read by D56:* each control file's content
  is read at most once per iteration unless its size, times or identity changed; what the run parks on stays a
  comparison of content. *Read by D59:* the *unless a delegate reports* half waits for `S14-result-contract`.
- **FR-025**: `make benchmark` MUST report K-effective, the Gini coefficient of slice-touch frequency and the
  top-3 share per feature, and flag a node above a configurable share as a decomposition candidate.
- **FR-026**: Every read beyond a stage's or delegate's one-hop brief MUST be logged as a context-expansion
  event with its reason, and `make benchmark` MUST report expansions per slice.
- **FR-027**: The documented semantics of `route_by_difficulty` MUST fix: planner, judge/converge and skipper
  always strong; worker tier a function of difficulty, boundary cut and cross-context edges with an upward
  cascade on a failed scoped gate; adversary at least the worker's tier and on a different model family.
- **FR-028**: The features a later learned difficulty predictor would need (planned and observed difficulty,
  converge passes, escalations, mutation survivors, boundary cut, cross-context edges) MUST be logged per
  task; building the predictor is out of scope.

- **FR-029**: Every decision entry MUST carry a `Reversibility:` line scored from the tree (commits produced,
  dependants, flag, schema or contract or CI or migrate-propagated file touched) as `easy`, `guarded` or `hard`.
- **FR-030**: `cruise.json` MUST gain `decide: provisional` (default unchanged); under it `easy` and `guarded`
  always-ask items MUST be taken as `Status: provisional · ratify by <date>` with `Revert: <range>`, and `hard`
  items MUST still block.
- **FR-031**: Provisional decisions MUST be listed with their revert recipes in `cruise-report.md` and
  `cruise-status`; `ratify D<n>` and `revert D<n>` MUST resolve them, a revert applying the named commits in
  reverse and running the gate; the completion audit MUST refuse `done` while one is unratified past its date.
- **FR-032**: The slice register and the result contract MUST carry the decision ids a slice depended on, so a
  revert names the slices that must re-enter the ladder.
- **FR-033**: Provisional approval MUST never widen what the merge root or CI checks, flip a flag, or take a
  `hard` decision.

### Key Entities

- **Verify stamp**: tree hash, gate script hash, tool versions, timestamp, result.
- **Merge tree node**: an integration branch, its two (or f) children, its scoped-gate result, its conflict state.
- **Result contract**: scope, status, contracts_changed, invariants_checked, tests, decisions, assumptions,
  unresolved, change_summary, difficulty_observed.
- **Contract edge**: provider slice, consumer slice, contract id; derived: degree, cut, cross-context flag.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On an unchanged tree, `make verify` returns in under 1 second.
- **SC-002**: One slice reaching `main` triggers exactly one full gate run.
- **SC-003**: For a fan-out of 8 slices, the longest chain of dependent post-acceptance steps is 3.
- **SC-004**: `make model` on a 16-slice model with one changed slice launches one browser and finishes in
  under 2 seconds.
- **SC-005**: `check-imports` enumerates at most 100 entries on the generated skeleton.
- **SC-006**: Runner bookkeeping at iteration 50 is within 20 percent of iteration 1.
- **SC-007**: The full gate's findings on the same tree are identical before and after every story.
- **SC-008**: 100 percent of delegate hand-backs carry a result contract; 100 percent of tasks carry a
  difficulty score.
- **SC-009**: On a slice branch touching one source file, `check-codegraph` hashes one file, `check-ux-gates`
  renders only that file's previews, and the four method-file checks report that they were skipped.
- **SC-011**: Under `decide: provisional`, the guarded fixture proceeds, the D54 fixture blocks, and an
  unratified provisional decision past its date parks the run rather than ending it.
- **SC-010**: After one feature, `make benchmark` prints K-effective, Gini, top-3 share and the
  context-expansion count per slice.

## Assumptions

- The generated Python event-modelling project is the reference fixture; TypeScript, Go and Java backends
  take the same changes through their `native_commands.py` entries and are held by the matrix tests.
- A worktree per slice is already how fan-out isolates work; the merge tree reuses it.
- The factory's own repository takes these changes through `slipwai migrate` after each lands (E8 in the PRD),
  so this cruise run speeds up as it goes.
- Owner decisions 1–7 in the PRD's Risks section are taken by the skipper under `decide: recommended-first`
  except where the owner brief says to ask a person.

## Slice acceptance criteria

One subsection per slice, written by the slice-gaps stage before the slice is planned. The input is the slice's
*Acceptance Examples* column in `story-split.md`; the output is criteria in precondition → trigger → observable
outcome form, one outcome each, and a `Gaps reviewed` note saying what was checked and which decisions in
`decisions.md` the answers rest on.

### S00-run-path (method slice)

**Gaps reviewed** 2026-10-03, cruise iteration 2, host: the two examples in `story-split.md` against the
acceptance-criteria checklist — measurability, precondition/trigger/outcome, negative paths, completion. Seven
gaps, all closed as the criteria below: the version string was a moving target (AC-S00-1), two gates were named
in the slice but one in the example (AC-S00-5), "run the way the cruise runner runs it" named no environment
(AC-S00-3), the refusal the fix must not lose had no criterion (AC-S00-4), "no quarantined test" had no
measurement (AC-S00-5), what `running.md` must record was unstated (AC-S00-2), and who flips the Safety net row
and with what provenance was decided as D11 (AC-S00-6). AC-S00-7 states what the slice must not do.

- **AC-S00-1** — Given this checkout, when `./slipwai --version` runs, then it exits 0 and prints `slipwai `
  followed by the contents of `VERSION` — the one place the number is written (`1.5.2.dev0` today).
- **AC-S00-2** — Given `delivery/survey/running.md`, when the slice is done, then its `## . (python)` section
  no longer contains *Not yet proven* and records the command, the exact line it printed, the interpreter it
  ran on (`python3 --version`), that no port, seed or backing service is needed, who proved it and the date.
- **AC-S00-3** — Given `CRUISE_RUNNER=1` and `CRUISE_ITERATION=<n>` in the environment, as every cruise
  iteration has, when `make test` runs, then every test passes: each test that spawns
  `scripts/agents/cruise.py` runs the child with both variables cleared from its environment.
- **AC-S00-4** — Given the same environment, when the test that proves `start` refuses inside an iteration
  runs, then it still passes by setting the two variables itself in the child's environment, so the refusal
  stays proven after the fix.
- **AC-S00-5** — Given this checkout at the slice's final commit with the two variables set, when `make verify`
  and `make -f delivery/Makefile verify` run, then both exit 0, the ratchet reports the test suite green and not
  quarantined (`delivery/baseline.json` records no `test` quarantine), and the unittest summary's `skipped=`
  count is no higher than the run recorded before the slice.
- **AC-S00-6** — Given both gates green, when the Convergence stage runs, then `project.json`'s `safety-net`
  row reads rung `tests-pass`, provenance `confirmed`, `planned` null, and its `evidence` names the two
  commands, the commit they were green on, and that cruise iteration 2 established it with no person having
  read the gate (D11); `/survey` regenerates `delivery/docs/convergence.md` and
  `make -f delivery/Makefile check-convergence` passes.
- **AC-S00-7** — Given the slice's diff, when it is reviewed, then nothing under `assets/`, `src/slipwai/`,
  `catalog.json` or the CLI changed: the slice is not user-visible, adds no `changelog.d/` fragment and leaves
  `VERSION` at `1.5.2.dev0`.

### S20-slice-scope-root

**Gaps reviewed** 2026-10-03, cruise iteration 3, host with `drive-skipper` for D18: the three examples in
`story-split.md` and the D17 clause against the acceptance-criteria checklist — measurability,
precondition/trigger/outcome, negative paths, completion. Eight gaps, all closed as the criteria below: "owning
every path not under another deployable" contradicted the `Makefile` example and named no host surface
(D18; AC-S20-2 to AC-S20-5); the delivery directory outside `docs/` had no rule at a root deployable (AC-S20-3);
the survey pages the ladder makes a slice write were unplaced (AC-S20-4); the root manifest and lock were
unplaced (AC-S20-6); a root deployable beside a subdirectory one had no owner rule (AC-S20-7); the spellings of
the root path were unstated (AC-S20-8); "answers unchanged" had no measurement (AC-S20-9); and reading the
register id whole would have turned records written under the bare prefix red (D19; AC-S20-10 to AC-S20-12).
AC-S20-13 states the release level. Unless a criterion says otherwise, the project is one adopted at `.` with one
deployable and `layout.delivery` set, and the check runs on a `slice/<id>` branch.

- **AC-S20-1** — Given a changed file under `tests/`, `src/`, or a root `scripts/` or `docs/` directory, when
  `make -f delivery/Makefile check-slice-scope` runs, then it exits 0 and prints *touches only what one slice may*.
- **AC-S20-2** — Given a changed root `Makefile`, `project.json`, a file under `.specify/`, a file under
  `.github/workflows/`, `AGENTS.md`, or a file under `.claude/` — one at a time — when the check runs, then it
  exits non-zero naming the path with today's *outside every deployable … Land it on `main` before the fan-out*
  message. The CI names held are `.github/`, `.gitea/`, `.forgejo/`, `.gitlab/`, `.gitlab-ci.yml` and
  `project.json`'s `ci.gate`; the harness names are `AGENTS.md`, `CLAUDE.md`, `.claude/`, `.codex/`, `.cursor/`,
  `.gemini/`, `.opencode/`. *Amended by D20 (converge pass 1):* these names are the floor; AC-S20-14 to
  AC-S20-16 say what is added to it and what stays the repository's own.
- **AC-S20-3** — Given a changed file under `<delivery>/scripts/`, `<delivery>/skills/` or `<delivery>/commands/`,
  or `<delivery>/Makefile`, or `<delivery>/baseline.json`, when the check runs, then it is refused with the same
  message; and a file under `<delivery>/docs/` other than the model, the canvas, a mockup and a new ADR keeps
  today's *the docs are the host's* message.
- **AC-S20-4** — Given a changed `<delivery>/survey/pinned.md` or `<delivery>/survey/running.md`, when the check
  runs, then it is green; given any other page under `<delivery>/survey/`, then it is refused.
- **AC-S20-5** — Given a path listed in `<delivery>/.written`, when it changes, then it is refused; given a path
  on the fixed list whose line was deleted from `.written`, then it is still refused; given no `.written` file,
  then the fixed list still holds and the check does not fail for its absence.
- **AC-S20-6** — Given a changed root `pyproject.toml` (or `package.json`) or its lock, when the check runs, then
  it is green, as a manifest inside `apps/<service>/` is today.
- **AC-S20-7** — Given a second deployable of kind `service` under a subdirectory and a model block naming
  another service for the slice, when a path under that subdirectory changes, then it gets today's *service … is
  not slice …'s* message; and a path elsewhere falls to the root deployable and is green.
- **AC-S20-8** — Given the root deployable's `path` recorded as `./` instead of `.`, when the check runs, then
  every answer above is the same; given a deployable with an empty or missing `path`, then it owns nothing, as
  today.
- **AC-S20-9** — Given a generated project with its deployables under `apps/`, when the check runs, then every
  assertion in `tests/test_parallel_slices.py`'s `SliceScopeGateTest` passes with the test unchanged, including
  a root `Makefile` refused.
- **AC-S20-10** — Given a register row whose first cell is `` `S00-run-path` `` and an adversary-log row headed
  `## S00-run-path · …`, when `make check-decisions` runs, then it finds the row and passes.
- **AC-S20-11** — Given the same register row and an adversary-log row headed `## S00 · …` (the bare prefix, as
  D17 wrote them), when `make check-decisions` runs, then it still passes; given neither heading, then it fails
  naming `S00-run-path`.
- **AC-S20-12** — Given the same register row, when `make check-benchmark` runs, then it reads the record at
  `slices/S00-run-path/benchmark.json`, or at `slices/S00/benchmark.json` where only that exists, and warns only
  where neither does; a register's header and separator rows are still not ids, and an id with no slug reads as
  today.
- **AC-S20-13** — Given the slice's diff, when it is reviewed, then it carries one fragment under `changelog.d/`
  whose first line is `PATCH`, saying what changed and that it asks nothing of a repository already generated;
  `VERSION` stays `1.5.2.dev0`; nothing under `delivery/scripts/` changed (the fix reaches this repository
  through a person's `slipwai migrate`, D9); and `make verify` and `make -f delivery/Makefile verify` are green.
- **AC-S20-14** — Given the registry at `<delivery>/scripts/agents/registry.json`, when a slice branch changes
  `.mcp.json`, `opencode.json`, `GEMINI.md`, a file under `.agents/` or a file under `.kiro/` — one at a time —
  then each is refused with today's message: every path a harness row names (`contextFile`, `skillsDir`,
  `commandsDir`, `agentFile.dir`, `hooks.projection.where`, `projectMcp.file`) is the host's, by its first
  segment where it has more than one (D20). Given the registry removed, unreadable or not JSON, then D18's fixed
  names are still refused, those five pass, and the checker exits with its own code, never a traceback.
- **AC-S20-15** — Given a changed `Jenkinsfile`, `azure-pipelines.yml`, `bitbucket-pipelines.yml`, a file under
  `.circleci/`, `.woodpecker.yml`, `.drone.yml`, `.travis.yml`, `GNUmakefile` or `makefile` — one at a time —
  then each is refused; and the checker's CI names cover every key of `CI_FORGES` in
  `src/slipwai/delivery_facts.py`, held by a test, so a forge `adopt` learns later is not forgotten here.
- **AC-S20-16** — Given a changed `.gitignore`, `.githooks/pre-commit` or `.pre-commit-config.yaml`, then the
  check is green: git hooks and the ignore file are the repository's own (D20).
- **AC-S20-17** — Given a new `shop/migrations/0002_add_field.py` or a new `db/migrations/20261003120000_add.js`
  under the root deployable, when the check runs, then it is green: a new migration there carries whatever name
  the repository's own tool wrote (D21). Given an edited or deleted existing migration there, then it is refused,
  and the message says to add a new migration with the repository's own tool, with no mention of a timestamp.
- **AC-S20-18** — Given a removed line in a pre-existing `domain/events.py` under the root deployable whose record
  has no `layout`, then the check is green; given the record says `"layout": "hexagonal"`, then it is refused
  with today's *the events module is the contract* message (D21).
- **AC-S20-19** — Given a deployable recorded `"generated": false` under a subdirectory, or a generated project
  with its deployables under `apps/`, then a numbered new migration and a removed events line are refused as
  today (D21); and no file the checker reads — `project.json`, `.written`, the registry — ends it on a traceback,
  whatever it holds (D22).

### S21-refresh-keeps-owned-files

**Gaps reviewed** 2026-10-03, cruise iteration 4, host: the two examples in `story-split.md` and the D16 clause
against the acceptance-criteria checklist — measurability, precondition/trigger/outcome, negative paths,
completion. Eight gaps, all closed as the criteria below: the two files named are two of four the factory seeds
and then hands to the project — `.specify/models.json` and `.specify/drive.json` are reset by the same loop
(D24; AC-S21-1 to AC-S21-3); what a refresh does where one of them is missing was unstated (AC-S21-4); a refresh
refuses an uncommitted change to a path it writes, and whether it still may for a file it no longer writes was
unstated (AC-S21-5); `slipwai adopt --confirm` runs the same refresh and was not named (AC-S21-6); "still
regenerated" had no measurement (AC-S21-7); whether the four leave `.written`, and with it `migrate`'s merge, was
unstated (AC-S21-8); which rows `strategy.before` is derived from, and for which preconditions, was unstated
(D25; AC-S21-9, AC-S21-10); and the release level (AC-S21-11). Unless a criterion says otherwise, the repository
is one `slipwai adopt` wrote into, committed and clean, and *the four* are `.specify/cruise.json`,
`.specify/product-owner.md`, `.specify/models.json` and `.specify/drive.json`.

- **AC-S21-1** — Given `.specify/cruise.json` committed with `enabled: true` and `max_iterations: 10`, when
  `slipwai adopt --refresh` runs, then the file's bytes are unchanged, `git status` does not list it, and the
  report's count of rewritten files does not include it.
- **AC-S21-2** — Given `.specify/product-owner.md` committed with its sections filled in, when the refresh runs,
  then the same three things hold for it.
- **AC-S21-3** — Given `.specify/models.json` or `.specify/drive.json` committed with a value that is not the
  factory's default, when the refresh runs, then the same three things hold for it (D24).
- **AC-S21-4** — Given one of the four absent from the tree (its deletion committed), when the refresh runs, then
  the file is written with the factory's default and counted among the rewritten files: a project is never left
  without a file `make check-agents` and `/cruise` read.
- **AC-S21-5** — Given an uncommitted edit to one of the four that slipwai did not make — what
  `/cruise-settings` leaves before a commit — when the refresh runs, then it does not refuse because of that
  file, and leaves the edit as it is; an uncommitted change to any other path the refresh writes is refused as
  today. *Amended after the demo (D29):* an uncommitted **deletion** of one of the four is still refused by name,
  as today — the refresh would write the default there, and that is a path it writes.
- **AC-S21-6** — Given the same repository, when `slipwai adopt --confirm` records an answer (it runs the same
  refresh), then AC-S21-1 to AC-S21-3 hold for it.
- **AC-S21-7** — Given a convergence row moved by hand in `project.json`, when the refresh runs, then
  `<delivery>/docs/convergence.md` is rewritten to show the row, and `<delivery>/commands/ground.md` and
  `<delivery>/survey/structure.md` are rewritten wherever the disk differs from what the record drives — the
  assertions `tests/` already makes about what a refresh regenerates pass unchanged.
- **AC-S21-8** — Given the refresh has run, then `<delivery>/.written` still lists the four, so `slipwai migrate`
  still merges a newer factory's version of each with the project's; and the report prints no `owned:` line for
  them — that line stays what it is, a file a person took over by deleting its line.
- **AC-S21-9** — Given the Safety net row recorded `confirmed` at `tests-pass` while the tree alone reads
  `tests-exist`, when the refresh runs, then `project.json`'s `strategy.before` no longer carries *a green suite
  in the gate — the safety net is `tests-exist`*, and `<delivery>/docs/change-strategy.md` no longer prints it
  (D25). Given the row still at `tests-exist` or `none`, then both still carry it.
- **AC-S21-10** — Given the Path to production row or the Structure row recorded by a person above the rung its
  precondition names (`unknown`, `manual`, `scripted`; `as-found`), when the refresh runs, then that
  precondition is gone from `strategy.before` the same way: every entry is derived from the rows the map shows
  after the refresh, never from the tree's reading alone. What the strategy record recommends, its `because`,
  `decided`, `finished` and `programme` are derived as today.
- **AC-S21-11** — Given the slice's diff, when it is reviewed, then it carries one fragment under `changelog.d/`
  whose first line is `PATCH`, labelled experimental (brownfield adoption), saying what changed and what a
  repository whose refresh already reset one of the four does (restore it from its history); `VERSION` stays
  `1.5.2.dev0`; nothing under `delivery/` changed but `delivery/survey/pinned.md`; `generate`, `add-service` and
  `migrate` write what they wrote before; and `make verify` and `make -f delivery/Makefile verify` are green.
- **AC-S21-12** — *Added by D28 (adversary F1).* Given a repository adopted with `--release pipeline` (the Path
  to production row `pipeline`, `overridden`) whose `release.path` a person then changed to `manual` and
  committed, when `slipwai adopt --refresh` runs, then the row reads `manual` with the `release` record's
  provenance and its `planned` kept; the report says *convergence: path-to-production refreshed from `pipeline`
  to `manual`* and names `release.path`; `project.json`'s `strategy.before` and
  `<delivery>/docs/change-strategy.md` carry *a pipeline that deploys on a passing `verify` — the path to
  production is `manual`*; and `<delivery>/docs/convergence.md` shows `manual`. The same holds for `unknown` and
  `scripted`, and for any recorded rung above the one the record names. Given instead a person's row at or below
  the rung `release.path` names, a row at `one-path` or `pipeline-decides` over `release.path: pipeline`, or a
  `release` record whose provenance is `detected` or `unrecorded`, then the row stands as recorded (D25, D28).

### S22-slice-scope-base

**Gaps reviewed** 2026-10-03, cruise iteration 5, host with `drive-skipper` for D30 and D31: the three examples in
`story-split.md` against `merge_base()`, `current_branch()` and `check()` in
`assets/toolkit/scripts/check-slice-scope.py`, and against how generated and adopted CI checks a pull request out
(`src/slipwai/project/ci_workflows.py`, `src/slipwai/project/adopted_ci.py`). Found and written back: which commit's
`project.json` names the trunk was unstated, and the working tree's taken as is lets a branch name itself the trunk
(D30; AC-S22-4, AC-S22-5); the `master` rule had a mirror — a `main` minted beside a `master` trunk (AC-S22-3,
AC-S22-9); a `ci.branch` that is not a usable name, or has no ref here, had no answer (AC-S22-6, AC-S22-7); the
forge's pull-request target was unused (AC-S22-8 to AC-S22-10); what the gate prints had no trunk in it
(AC-S22-13); "a shallow clone fails" taken literally turns every slice pull request's CI red, because every such
checkout is depth 1 with no trunk ref, and the CI half of the gate has never held (D31; AC-S22-16 to AC-S22-18,
and slice `S24-ci-fetches-slice-base`, which waits on a person); a full clone with no trunk, and a trunk with no
common ancestor, were unplaced (AC-S22-14, AC-S22-15); branches that are not slices were unstated (AC-S22-19); the
same base selection in `check-migrations.py` is left alone and held so (AC-S22-20, Parking Lot). AC-S22-21 states
the release level. Unless a criterion says otherwise, the project is on a `slice/<id>` branch cut from `main`,
with a host-surface change committed, no forge variable set, and a full clone.

- **AC-S22-1** — Given a project whose record names no `ci.branch`, when a `master` branch, an `origin/master` ref
  or a tag named `main` is placed at the branch's head, then `make check-slice-scope` still refuses the change and
  its header names `main` (D30).
- **AC-S22-2** — Given a record naming `ci.branch: trunk` and a `trunk` branch, when the slice changes only a file
  of its own, then the check is green and its line says it compared with `trunk`; given the same project and a
  `main` or `master` minted at the branch's head, then a host-surface change is still refused.
- **AC-S22-3** — Given a record naming `master` and a `main` minted at the branch's head, then the change is still
  refused.
- **AC-S22-4** — Given a slice that sets `ci.branch` to its own branch name or to any `slice/<id>` name, committed
  or not, then that name is not taken as a trunk, the base is the fallback's, and `project.json` is among the
  refusals.
- **AC-S22-5** — Given a slice that sets `ci.branch` to a name with no branch in the checkout while `main` exists,
  then the base is `main`'s, `project.json` is refused, and the output says the recorded name was passed over.
- **AC-S22-6** — Given a `ci.branch` that is a number, a list, an empty string, whitespace, `-x` or
  `refs/tags/main`, then the check ends in a verdict with no traceback and compares with `main`; given
  `refs/heads/main`, then it reads as `main`.
- **AC-S22-7** — Given an unchanged record naming a trunk with no ref in the checkout and a `main` that has one,
  when the slice changes only its own files, then the verdict is today's against `main`, and its line names the
  recorded trunk and the fetch that would bring it.
- **AC-S22-8** — Given `GITHUB_BASE_REF=main` (and, separately, `CI_MERGE_REQUEST_TARGET_BRANCH_NAME=main`), a
  slice that committed `ci.branch: evil` and an `origin/evil` ref at its head, then the base is `main`'s and
  `project.json` is refused.
- **AC-S22-9** — Given a `master` trunk with no record, `GITHUB_BASE_REF=master` and an `origin/main` ref at the
  branch's head, then the base is `master`'s and the change is refused.
- **AC-S22-10** — Given a pull-request target naming another branch that sits ahead of the trunk's base, then the
  base is still the trunk's: across two names the oldest base wins.
- **AC-S22-11** — Given `main` moved locally past `origin/main` and merged into the slice, then the base is the
  newer of the two, as today, and `main`'s own files are not charged to the slice.
- **AC-S22-12** — Given a repository with a `main` trunk and an older `master` branch left behind, no minted ref
  and no pull-request target, then every verdict is today's.
- **AC-S22-13** — Given a passing slice branch, then the one line printed names the trunk compared with and the
  base's short commit; a refusal's header names them too.
- **AC-S22-14** — Given a developer's shallow clone of a `slice/<id>` branch with no trunk ref, or a full clone
  with none under `refs/heads/` or `refs/remotes/origin/`, when the check runs, then it exits 1 and its one line
  names the trunk and `git fetch origin <trunk>` (D31).
- **AC-S22-15** — Given a shallow clone that has the trunk ref but no common ancestor within its depth, then the
  check exits 1 and the line names `git fetch --unshallow origin`; given a full clone whose slice branch shares
  no history with the trunk, then it exits 1 saying a slice branch is cut from the trunk, and names no fetch.
- **AC-S22-16** — Given a detached depth-1 checkout with `GITHUB_HEAD_REF=slice/<id>` (and, separately,
  `CI_COMMIT_REF_NAME`) and no trunk ref, when the check runs, then it exits 0, prints nothing on stdout that
  reads as a pass, and its stderr line says the slice was NOT checked and names `fetch-depth: 0`. The words
  *nothing to hold* do not appear.
- **AC-S22-17** — Given `GITHUB_HEAD_REF=slice/<id>` set in a checkout whose `HEAD` is attached to a branch and
  has no usable base, then the check exits 1: the branch-name variable alone does not buy the exit 0. *Amended by
  D32:* and no CI marker (`CI`, `GITHUB_ACTIONS`, `GITLAB_CI`) is set.
- **AC-S22-18** — Given a detached pull-request checkout with full history and the trunk ref, with
  `GITHUB_HEAD_REF=slice/<id>` and a host-surface change in the diff, then the change is refused exactly as
  locally.
- **AC-S22-19** — Given a branch that is not `slice/<id>`, or a detached checkout with no forge variable, in a
  shallow clone, then the answer is today's (*not a `slice/<id>` branch — nothing to hold*, exit 0); and given
  any no-base case on a slice branch, a regular file at a canonical slot is still reported and still fails.
- **AC-S22-20** — Given `check-migrations.py` in a shallow checkout, then its output is what it was before the
  slice: its base selection is left alone (D31; Parking Lot).
- **AC-S22-21** — Given the slice's diff, when it is reviewed, then it carries one fragment under `changelog.d/`
  claiming PATCH, `VERSION` unchanged, that states the local promise and the pull-request promise separately and
  says what the change asks of a repository already generated: after `migrate`, a slice branch in a checkout
  with no trunk to compare with fails locally with the fetch to run, and CI on a default checkout says the slice
  was not checked.
- **AC-S22-22** — *Added by D32 (converge T013).* Given a depth-1 single-branch clone of `slice/<id>` with `HEAD`
  attached, no trunk ref, neither branch-name variable, and `GITHUB_ACTIONS=true` (separately `GITLAB_CI=true`, and
  `CI=true` alone), when the check runs, then it exits 0, prints nothing on stdout, and stderr says the slice was
  NOT checked, naming the trunk and `fetch-depth: 0`; neither *nothing to hold* nor `git fetch origin` appears.
  The same holds, with a CI marker set, for a trunk ref with no common ancestor at this depth and for an unrelated
  trunk.
- **AC-S22-23** — Given a CI marker, an attached slice branch, a usable base and a host-surface change in the
  diff, then the change is refused, exit 1, exactly as locally; given a CI marker, no base and a regular file at a
  canonical slot, then the check exits 1 and prints the lost record beside the NOT checked line; given a CI marker
  on a branch that is not `slice/<id>`, then the answer is today's *nothing to hold*, exit 0.
- **AC-S22-24** — Given the factory's suite run with `CI=true GITHUB_ACTIONS=true` in its environment, then every
  test asserting a developer's exit 1 still passes: the gate under test is run with the markers cleared.
- **AC-S22-25** — *Added by D33 (gaps G4).* Given a project with no `ci.branch`, a `master` trunk ahead of an older
  `main`, and a slice cut from `master` that changes only its own files, when the check runs, then it compares
  with `main`, refuses `master`'s own host-surface files, and its header says `master` is here too, that no trunk
  is recorded, and the fix: set `ci.branch` to `master` in `project.json`, or delete the stale `main`. Given the
  same repository once `ci.branch: master` is recorded on `master`, then the slice is green against `master`.
  Given a `main` trunk with a `master` minted at the branch's head, then the refusal stands (AC-S22-1) and the
  clause moves neither the base nor the exit. Given AC-S22-12's repository, or any usable `ci.branch` with a ref,
  then the clause is absent.
- **AC-S22-26** — *Added by D34 (gaps G1); amends the command named in AC-S22-7 and AC-S22-14.* Given a developer's
  single-branch clone of a slice branch with no trunk ref, when the command the failure prints —
  `git fetch origin <trunk>:refs/remotes/origin/<trunk>` — is run there and the check is run again, then the
  check has moved on: to a verdict in a full clone, and in a shallow one to the `git fetch --unshallow origin`
  line, which run in turn leads to a verdict. The passed-over note names the same form of fetch.
- **AC-S22-27** — *Added by D34 (gaps G2).* Given a slice that commits `ci.branch: HEAD` (in any case) in a clone
  whose `refs/remotes/origin/HEAD` points at the slice's own branch, when the check runs, then `HEAD` is not taken
  as a trunk, the base is `main`'s, and `project.json` is refused; the same holds for `HEAD` in either target
  variable; and a ref that is symbolic is never a trunk ref.
- **AC-S22-28** — *Added by D34 (gaps G5–G8).* What the gate prints is true where it is printed: given a CI marker,
  no base and a recorded `ci.branch` with no ref, then no `git fetch` command appears anywhere in the output;
  given a recorded `slice/<id>` name, then the note says a slice branch is never the trunk, not that it is no
  branch name; given a `ci.branch` that is not a string, then the output says the record was passed over; given a
  developer's no-base failure, then it is one line of its own on stderr, exit 1, and the header *reaches outside
  what one slice may touch* appears only where a path was refused or a record is about to be lost.
- **AC-S22-29** — *Added by D35 (adversary B1, A1).* Given a slice that commits `ci.branch: zz` and an unrelated-root
  `origin/zz`, a full clone with `origin/main`, and a host-surface change, when the check runs — attached, detached
  with a branch variable, with and without a CI marker — then `zz` is passed over and said so, the base is
  `main`'s and the change is refused. Given a usable pull-request target with a ref that shares no history with
  the branch, whatever the record names, then there is no base: a developer's checkout exits 1 saying the branch
  shares no history with the target, a forge's says NOT checked, and the pass line is never printed.
- **AC-S22-30** — *Added by D35 (adversary A2, A3, B4).* Given a `ci.branch` holding a NUL or a lone surrogate, then
  the check ends in a verdict against `main` with no traceback. Given `project.json` or the model committed as a
  symlink to a device, a pipe or a file larger than the cap, then the check ends in a verdict within seconds, with
  no traceback and without reading it. Given a checkout git cannot read at all, then the exit is 0 as before the
  slice and stderr says git could not read the checkout, with git's own first line, and nothing about history.
- **AC-S22-31** — *Added by D35 (adversary B2).* Given a base and a `git diff` (or `git ls-files`) that fails, then
  the pass line is not printed: a developer's checkout exits 1 with one line naming the base and git's own first
  line; under a CI marker the slice is NOT checked, exit 0, with that reason.
- **AC-S22-32** — *Added by D35 (adversary B3, A5, B5, A4; the hand's notes 2, 3).* Given a recorded name with a
  character outside `[A-Za-z0-9._/-]`, or no remote named `origin`, then no `git fetch` command is printed and the
  line says which branch is missing. Given a recorded value that is not a usable name, then it is printed with
  its control characters dropped and cut to 80 characters, so no line of the output is the slice's own. Given a
  pull-request target whose base won over the recorded trunk's, then the line names the target and says the pull
  request targets it. Given a recorded trunk with no ref and no other base, then the fetch is printed once.


### S23-refusal-in-subdirectory

**Gaps reviewed** 2026-10-03, cruise iteration 6, host: the three examples in `story-split.md` against `changed()`,
`stamp()` and `refuse_foreign()` in `src/slipwai/uncommitted.py` and their two callers (`src/slipwai/resurvey.py`,
`src/slipwai/confirm.py`), and against a scratch repository adopted in `sub/` (both edits to
`delivery/docs/convergence.md` and `delivery/commands/ground.md` were written over at exit 0, and
`.delivery-tools/written.json` stayed `{}`). Found and written back: which name the refusal prints was unstated
(D36; AC-S23-1); `--confirm` and `--decline` were named in the slice and had no example, nor had a deletion or an
untracked file (AC-S23-2); *slipwai itself left the change* had no measurement (AC-S23-3, AC-S23-4); a change
elsewhere in the repository had no answer, and one whose path from the top spells a path the run writes is refused
today by mistake (D36; AC-S23-5); a deeper directory, a name git would quote and a symbolic link were unstated
(AC-S23-6); *every answer is today's* had no measurement (AC-S23-7, AC-S23-8); what a repository already adopted in
a subdirectory meets at its first run after the fix was unstated (D37; AC-S23-9); and the release level
(AC-S23-10). Swept for the same mistake — a path git reports from the repository's top compared with one relative
to the project — over every `git` call under `src/slipwai/`: one more, `history()` in `src/slipwai/structure.py`,
which is the survey's and not the refusal's, placed in the Parking Lot (D38). Unless a criterion says otherwise the
repository is one git repository whose adopted project — `project.json` and the delivery directory — is in `sub/`,
with the adoption committed, a sibling directory `other/` beside it, and every command run in `sub/`.

- **AC-S23-1** — Given an uncommitted edit a person made to a file the refresh writes
  (`delivery/docs/convergence.md`), when `slipwai adopt --refresh` runs, then it exits 2, the message names
  `` `delivery/docs/convergence.md` `` — the path as the project spells it, with no `sub/` in front, the way it reads
  at the top of a repository — the edit stands, and no other file is written.
- **AC-S23-2** — Given the same edit, when `slipwai adopt --confirm <candidate>` or `--decline <candidate>` runs,
  then it is refused the same way and `project.json` is not changed. Given instead an uncommitted deletion of a
  listed file, or an untracked file at a path the run writes, then the refusal names it as it does at the top.
- **AC-S23-3** — Given no edit of a person's, when `adopt --confirm` records one answer, a convergence row is then
  settled by hand in `project.json`, and `adopt --confirm` and `adopt --refresh` run after it with nothing
  committed in between, then each exits 0: what the first run left is recognised as slipwai's own.
  `sub/.delivery-tools/written.json` holds those paths spelled relative to the project, and `git status` does not
  show the file.
- **AC-S23-4** — Given what AC-S23-3's first run left uncommitted, when a person then edits one of those files and
  a refresh runs, then it is refused naming that file.
- **AC-S23-5** — Given uncommitted changes outside the project — `other/note.txt` edited, and a file at the
  repository's top whose path from the top is one the run writes inside the project
  (`delivery/docs/convergence.md` at the top, beside `sub/`) — when the refresh runs, then neither stops it, neither
  is written to, and neither is recorded in `written.json`.
- **AC-S23-6** — Given the project two directories down (`a/b/`), in a directory whose name holds a space and a
  non-ASCII letter, or reached through a symbolic link to its directory, then AC-S23-1, AC-S23-3 and AC-S23-5 hold
  as written.
- **AC-S23-7** — Given a project at the top of its repository, then every answer is today's: the assertions
  `tests/test_uncommitted.py` and `tests/test_refresh_owned.py` already make pass unchanged, and the paths in
  `written.json` are spelled as before.
- **AC-S23-8** — *Narrowed by D41.* Given a machine where `git` runs, and a project directory that is not in a git
  repository, or in one git cannot read, then nothing is refused and nothing is recorded, as today, and no run ends
  on a traceback. A machine with no `git` on `PATH` is neither state and is not changed by this slice (D41): the
  run ends as it did before, writing nothing.
- **AC-S23-9** — Given a repository adopted in a subdirectory where an earlier factory's `--confirm` or `--refresh`
  left regenerated files uncommitted (it recorded nothing there), when the first run after this change meets them,
  then it refuses naming them, as it does a person's edit — it cannot tell the two apart — and committing them
  once is what clears it (D37; *or stashing* taken out by D43: a stash takes the uncommitted answers with it).
  The fragment says so.
- **AC-S23-10** — Given the slice's diff, when it is reviewed, then it carries one fragment under `changelog.d/`
  whose first line is `PATCH`, which says *experimental: brownfield adoption*, what was lost before, and what
  AC-S23-9 asks of a repository already adopted; `VERSION` stays `1.5.2.dev0`; and `slipwai add-service`'s own
  refusal — any uncommitted change anywhere in the repository — is not changed by this slice.
- **AC-S23-11** — *Added by D43 (gaps G2).* Given any refusal, at the top of a repository or below it, then the
  message says the paths it names are spelled from the project's directory, so a person typing a git command
  elsewhere in the repository knows where they are names from.

### S01-gate-walks

**Gaps reviewed** 2026-10-03, cruise iteration 7, host with `drive-skipper` for D45, D46 and D47: the three
examples in `story-split.md` against `source_files()` and rules 4 and 5 in `assets/toolkit/scripts/check-imports.py`,
`migrations()` in `assets/toolkit/scripts/check-migrations.py`, and `drift()` and `main()` in
`assets/toolkit/scripts/check-codegraph.py`, and against a scratch Python skeleton with a React frontend (79
entries under `apps/` and `packages/` with nothing installed; today's run lists 256). Found and written back: what
an *entry* is, on which tree the 100 is measured and where the count is said were unstated (D47; AC-S01-1,
AC-S01-2, AC-S01-6, AC-S01-7); pruning `target` by name would stop the gate reading a source directory of that
name, against SC-007 and constitution I (D45; AC-S01-3 to AC-S01-5); *read `project.json` once* had no
measurement, and `check-migrations` reads it not at all today (AC-S01-8); a tree with neither `apps/` nor
`packages/`, and a symbolic link to a directory, were unstated (AC-S01-9); for `check-codegraph`, *on a branch*,
*since the last sync* and *in CI only* each had no definition, read to the letter the integrity check would run
nowhere, and nothing said what the gate does when it cannot tell (D46; AC-S01-10 to AC-S01-21); and the release
level (AC-S01-22). The reference skeleton is `slipwai generate` with the `event-modelling` profile, the Python
backend, the `react-vite` frontend and target `none`, freshly generated, nothing installed.

- **AC-S01-1** — Given the reference skeleton, when `make check-imports` runs, then it exits 0 and its one stdout
  line is `check-imports: inward dependency rule holds (N directory entries read)`, where N is at most 100 and
  equals an independent enumeration of `apps/` and `packages/` with the pruned directories' contents left out. An
  entry is one name a directory listing returns, summed over the run: a directory read twice counts twice (D47).
- **AC-S01-2** — Given the same skeleton, when `make check-migrations` runs, then its pass line is today's words
  unbroken, closed by the same parenthetical count. It carries no bound.
- **AC-S01-3** — Given a populated `.venv`, `node_modules`, `__pycache__` and `.git` planted under an app — holding
  a `domain/` file that imports an adapter and a contracting migration under `migrations/` — when either script
  runs, then its findings equal those of the tree without them, its count is higher by exactly the number of
  directories planted, and nothing inside them is listed, at any depth, in any walk the script makes (D45).
- **AC-S01-4** — *Rewritten by D52 (adversary A1).* Given a Java service `project.json` records — `language`
  `java`, `path` `apps/service`, spelled `apps/service`, `apps/service/` or `./apps/service`, `generated` or not —
  after a build: `target/` beside that path's `pom.xml`, holding a copy of a contracting migration under
  `target/classes/db/migration/` and `.java` files under `target/generated-sources/` — then findings equal those
  with `target/` deleted and it is not descended.
- **AC-S01-5** — *Rewritten by D52.* Every other directory called `target` is read as before the slice, and each
  of these fails as it did: an empty `pom.xml` beside a context directory `target/` under a Python service, at the
  service's root and at depth, holding a `domain/` file that imports an adapter and a contracting migration (the
  adversary's reproduction); a nested module's `target` below a recorded Java deployable's root; a `target` beside
  a `pom.xml` under `packages/` with no record; any `target` in a tree with no `project.json`, or one whose record
  is unreadable or carries a `path` or `language` that is not a string; a `target` with no `pom.xml` — a context
  of that name whose domain file imports an adapter, an import from it into another context's insides, a
  contracting migration under it; and a Java package directory `src/main/java/…/target/`.
- **AC-S01-6** — Given a tree with violations outside any pruned directory, when either script runs, then its
  stderr and exit code are byte for byte what they were before this slice — the same findings in the same order,
  and no count (D47; SC-007).
- **AC-S01-7** — Given a project whose walk lists more than 100 entries, then the gate passes with its count
  printed and no other word: 100 is a measurement on the skeleton, never a limit on a project (D47).
- **AC-S01-8** — *Reworded by D52.* Given any run, then `check-imports` opens `project.json` at most once and
  `check-migrations` exactly once where it exists (to learn which deployables are Java; it did not read it before
  the slice). A tree with no `project.json`, or an unreadable one, prunes no `target` and is answered as before
  the slice — the same exit, and never a traceback the earlier script did not have.
- **AC-S01-9** — Given a tree with neither `apps/` nor `packages/`, then both scripts pass as today, reporting 0
  entries; given a symbolic link to a directory under an app, then it is one entry and is not descended into, as
  the Python the skeleton pins (3.13) does today.
- **AC-S01-10** — Given a checkout on a `slice/<id>` branch with no CI marker set (`CI`, `GITHUB_ACTIONS`,
  `GITLAB_CI`), an index the gate's last whole comparison found current, and one tracked source file changed
  since, when `check-codegraph` runs with the index current for that file, then it hashes exactly that one file and
  its pass line says, in one line, how many files it hashed of how many the index holds, that it compared only
  what changed since its last whole comparison and when that was, and that the integrity check was not run here
  and runs in the full gate. With nothing changed it reports 0 hashed (D46).
- **AC-S01-11** — Given the trunk, a branch not shaped `slice/<id>`, a detached `HEAD`, or any CI marker set, then
  the run is today's — every tracked file hashed, the integrity check run, today's pass line byte for byte — with
  the memory present and neither read nor, in CI, written (D46).
- **AC-S01-12** — Given a corrupt database on the trunk or with a CI marker set, then it fails or is rebuilt
  exactly as today.
- **AC-S01-13** — Given a file that was dirty when the memory was written and is reverted afterwards, with the
  index still holding the dirty content, then a narrowed run reports it changed.
- **AC-S01-14** — Given an index row rewritten, added or removed after the memory was written, with `indexed_at`
  unmoved, then a narrowed run re-hashes that file and reports what a whole run would; a different or rebuilt
  database is a whole run.
- **AC-S01-15** — Given a tracked file marked `assume-unchanged` or `skip-worktree` and edited on disk, then a
  narrowed run still catches it.
- **AC-S01-16** — Given `check-codegraph.py` or `agents/code_index.py` edited since the memory was written, then
  the memory is not used and the run is whole.
- **AC-S01-17** — Given a memory the run cannot use — none, unreadable, its commit gone, git unable to list what
  changed — on a slice branch, then the run is today's whole check, its pass line today's plus one clause saying
  why; it never fails for that reason alone and never passes narrower.
- **AC-S01-18** — *Reworded by D48.* Given a database whose rows a narrowed run cannot read — damage the read
  meets, or any other SQLite error — then the result is never a narrowed pass: the run goes whole, integrity check
  included, and answers as the whole run does — a damaged database fails or is rebuilt (AC-S01-12), never
  *skipped*; a sound one whose `files` table cannot be read is skipped in today's words. Damage the read of its
  rows does not meet is what the integrity check finds, in the full gate (D46).
- **AC-S01-19** — Given a run that fails or skips, then no memory is written or renewed; a narrowed run that finds
  drift syncs as today, compares again, and renews the memory only on a pass.
- **AC-S01-20** — Given any run, then `git status` reports nothing the gate left, and where `.codegraph/` is
  removed the memory goes with it; a `.codegraph/` copied from another checkout never yields a narrower pass than
  the whole run would give.
- **AC-S01-21** — For each drift state in AC-S01-13 to AC-S01-18 and AC-S01-23, the narrowed run's verdict equals
  the whole run's on the same tree and index. *Restated by D49:* a narrowed run never reports *current* for a file
  whose bytes differ from its row unless the file's size, modification time, change time and identity all read
  exactly as they did when the gate last hashed it and found it equal. *Added by D50 (converge T021):* a tracked file
  the index holds no row for is judged on a narrowed run by the whole run's own test, whatever git reports.
- **AC-S01-22** — Given the slice's diff, when it is reviewed, then it carries one fragment under `changelog.d/`
  whose first line is `PATCH`, naming the five directories, the record's test for `target` (D52) and the one kind of finding that
  can disappear (one inside a pruned directory), the count on the two pass lines, and where `check-codegraph`
  compares only what changed; it asks nothing of a generated repository; `VERSION` stays `1.5.2.dev0`; and no
  file `delivery/.written` lists changes in this repository (D9; the Pin stage's rows in
  `delivery/survey/pinned.md` are the method's record, not the factory's files).
- **AC-S01-23** — *Added by D49 (converge T016).* Given a tracked file whose bytes change in a way git's comparison
  normalises away — rewritten with CRLF line endings under `* text=auto eol=lf`, before or after `git add`, or the
  mirror — or a same-size rewrite in place with its modification time restored, then a narrowed run hashes it and
  answers as the whole run does: the memory records each indexed tracked file's size, modification time, change
  time and identity, as many as the platform reports, and a file whose record is missing or differs is hashed.
- **AC-S01-24** — *Added by D49.* Given a file whose modification or change time is not safely older than the start
  of the run that vouched for it (two seconds where the gate cannot know the filesystem's granularity), then it is
  hashed on every narrowed run until a later passing run vouches for it again.
- **AC-S01-25** — *Added by D49.* Given a `touch`, a checkout or a rebase that moves a file's times without changing
  a byte, then a narrowed run hashes that file once, passes, renews its record, and does not hash it again on the
  next run. A memory without these records means the whole run with the one clause (AC-S01-17).
- **AC-S01-26** — *Added by D52 (adversary A4).* Given a deployable recorded at, or beneath, a directory carrying
  a pruned name, then that directory is descended in every walk of both scripts: all five rules of `check-imports`
  and `check-migrations` read the deployable, as rules 4 and 5 always did.

### S02-runner-bookkeeping

**Gaps reviewed** 2026-10-03, cruise iteration 9, host with `drive-skipper` for D56 to D60: the four examples in
`story-split.md` against `fingerprint()`, `entries()`, `controls_signature()`, `iterate()` and the loop in `drive()`
in `assets/toolkit/scripts/agents/cruise.py`, `health()`, `behind()` and `delegate_use()` in
`assets/toolkit/scripts/agents/code_index.py`, `check_decisions()` in `assets/toolkit/scripts/check-decisions.py`,
and where the skipper's brief and the entry's shape are generated (`src/slipwai/project/cruise_agents.py`,
`src/slipwai/project/cruise_record.py`). Found and written back: a signature *from mtimes* would let an iteration
edit a gate and put its time back, so the comparison stays one of content and only the reading is saved (D56;
AC-S02-1 to AC-S02-11); a fingerprint of path and time alone reads a `touch` or a same-bytes rewrite as progress, so
a spinning run would never park (D57; AC-S02-12 to AC-S02-21, FR-015 and User Story 5's scenario 2 amended); where
the offset lives, which readers it covers, what an edited, cut, replaced or deleted log answers, and how *only the
new bytes* is measured without a timing were unstated (D58; AC-S02-22 to AC-S02-33); *drift-check only changed
files* and *one sync per iteration* named no function and had no example (D59; AC-S02-34 to AC-S02-46); and the
`Scope:` line had no values, no word for global, no place, no answer for an entry without it and no means of
reaching the skipper (D60; AC-S02-47 to AC-S02-69). Reconciled by the host between siblings: D57's timing criterion
is held by D58's rule that no test asserts a wall-clock ratio (AC-S02-21), and the slice carries one fragment,
`MINOR`, not one per part (AC-S02-46, AC-S02-69). Deferred by name: a sync tied to what a delegate reports, and the
skipper seeing a neighbour's decisions through the Slice graph (`S14-result-contract`, `S13-one-hop-brief`).

*The controls (FR-024, D56).*

- **AC-S02-1** — Given a run whose controls no one touches, when the second and every later signature of the
  runner's process is taken, then no control file is opened for content and the signature equals the first. (D56)
- **AC-S02-2** — Given an iteration that appends a line to a gate script, when the iteration ends, then the run
  parks naming `<path> (modified)` with `controls_changed` on the log entry, as today. (D56)
- **AC-S02-3** — Given an iteration that rewrites a gate in place with the same size and sets its modification
  time back to what it was, when the iteration ends, then the run parks naming that file `(modified)`. (D56)
- **AC-S02-4** — Given an iteration that replaces a gate by rename with a same-size file carrying the old
  modification time, when the iteration ends, then the run parks naming that file `(modified)`. (D56)
- **AC-S02-5** — Given an iteration that only touches a gate, or rewrites it with the same bytes, when the
  iteration ends, then the run does not park for it, and that file's content is read once and not again while it
  stays unchanged. (D56)
- **AC-S02-6** — Given a run parked between iterations, when a person edits a control and the run resumes, then
  the next iteration's log entry carries no `controls_changed` for that file, and a later iteration that changes
  the same file still parks naming it. (D56)
- **AC-S02-7** — Given an iteration that deletes a control and adds a script beside the gates, when it ends, then
  the run parks naming `(deleted)` and `(added)`; and a file added under `tools/` is still not a change. (D56)
- **AC-S02-8** — Given a control file that cannot be read after an iteration and was read before it, when the
  iteration ends, then it is reported `(deleted)` as today and no hash is reused for it. (D56)
- **AC-S02-9** — Given a control file modified within two seconds of the moment the runner hashed it, when the
  next signature is taken, then that file's content is read again. (D56)
- **AC-S02-10** — Given a platform that reports no change time or no file identity, when any signature is taken,
  then every control file's content is read. (D56)
- **AC-S02-11** — Given a new runner process over a tree whose controls changed while no runner was alive, when
  its first iteration starts, then every control file is hashed and nothing from an earlier process is consulted.
  (D56)

*The fingerprint (FR-015, D57).*

- **AC-S02-12** — Given a `specs/` tree last written more than the granularity window ago and a runner process
  that has fingerprinted it once, when `fingerprint()` runs again, then it opens no file under `specs/` for
  content and returns the same value. (D57)
- **AC-S02-13** — Given a runner process's first `fingerprint()` call, when it runs, then each file under `specs/`
  but the log and the checkpoint is opened exactly once. (D57)
- **AC-S02-14** — Given a fingerprinted tree, when one file is touched or rewritten with the same bytes, then the
  next call opens that file alone and returns the same value, and the call after opens none. (D57)
- **AC-S02-15** — Given a fingerprinted tree, when one file is rewritten in place with different bytes of the same
  size, then the next call returns a different value; and the same holds when its modification time is restored on
  a platform that reports a change time. (D57)
- **AC-S02-16** — Given a fingerprinted tree, when a file is added, removed, or renamed with its bytes unchanged,
  then the next call returns a different value, and a removed file's record is no longer held. (D57)
- **AC-S02-17** — Given a file written within the granularity window of its read, when `fingerprint()` runs again
  with nothing changed, then that file is read again and the value is the same. (D57)
- **AC-S02-18** — Given two runner processes over the same tree at the same commit and status, when each
  fingerprints, then the values are equal (the test at `tests/test_cruise_runner.py` line 196, *no progress since
  iteration 2* across two runs, still passes). (D57)
- **AC-S02-19** — Given a new commit, or a change outside `specs/` that alters `git status`, with `specs/`
  unchanged, when `fingerprint()` runs, then the value differs and no file under `specs/` is opened. (D57)
- **AC-S02-20** — Given a log whose entries carry fingerprints written by the earlier code, when the runner
  starts, then it reads them without error and parks as stuck only after `stuck_after` values of its own are
  equal. (D57)
- **AC-S02-21** — Given 50 calls over an unchanged tree, when the 50th is timed against the second, then it is
  within 20 percent. *Read with D58:* held in the suite by the count of files opened, which does not depend on the
  call's number; a timing is the demo's evidence only. (D57)

*The log and the stream (FR-015, D58).*

- **AC-S02-22** — Given a log of 50 entries and a fake harness, when one runner process runs two iterations, then
  the entries are numbered 51 and 52, entry 51's `bookkeeping.log_bytes` is the seeded log's size in bytes,
  counted once, and entry 52's is 0. (D58)
- **AC-S02-23** — Given the same run over a log of 1 entry, when the second iteration's entry is written, then its
  `log_bytes` is 0, the same as over 50 entries. (D58)
- **AC-S02-24** — Given a runner whose iteration cut the log down to its first 3 entries while it ran, when the
  iteration ends, then its entry is appended as today, the next iteration is numbered from the entries then in the
  file, and that next entry's `log_bytes` is the size of the file it re-read. (D58)
- **AC-S02-25** — Given a log deleted during an iteration, when the iteration ends, then the file is recreated
  holding that one entry and the next iteration is numbered 2. (D58)
- **AC-S02-26** — Given a log replaced during an iteration by a new file with the same bytes, when the next
  iteration starts, then its number is what it would have been and its entry's `log_bytes` is the whole file's
  size. (D58)
- **AC-S02-27** — Given a log one of whose entries was edited in place to the same length during an iteration,
  when the next iteration starts, then the log is read whole (`log_bytes` is its size) and the number is the count
  of entries plus one. (D58)
- **AC-S02-28** — Given a log to which another hand appended one entry during an iteration, when the next
  iteration starts, then its number counts that entry and `log_bytes` is the whole file's size. (D58)
- **AC-S02-29** — Given a log whose last line is not a whole entry, when the runner starts, or next reads it after
  a change, then the run ends as it does today and nothing is appended to the log. (D58)
- **AC-S02-30** — Given a stream already holding 50 iterations and an index in use, when iteration 51's entry is
  written, then its `index_use` equals what `delegate_use(STREAM, 51)` returns over the whole file, and its
  `bookkeeping.stream_bytes` is no more than the bytes from this iteration's marker to the end of the file. (D58)
- **AC-S02-31** — Given a stream that was replaced or cut short during the iteration, so that the marker is not at
  the byte the runner wrote it, when the entry is written, then `index_use` is what today's whole read gives and
  `stream_bytes` is the size of what was read; a deleted stream gives no `index_use`. (D58)
- **AC-S02-32** — Given a log of 50 entries, when `status`, `where`, `tell` and `resume` each run, then each
  prints what it printed before the slice. (D58)
- **AC-S02-33** — Given a run whose fingerprint has not moved for `stuck_after` iterations, when the log is cut
  short during a park, then the stuck window is what it was, as today. (D58)

*The code index before an iteration (FR-015, FR-024, D59).*

- **AC-S02-34** — Given an index the last comparison found current, a usable memory and nothing changed since, on
  the trunk, a `slice/<id>` branch, another branch or a detached `HEAD`, when `health()` runs, then it hashes 0
  files and reports `current`. Its `detail` says in one line how many files it hashed of how many the index holds,
  that it compared only what changed since the last whole comparison, and when that was. (D59)
- **AC-S02-35** — Given the same and one tracked indexed file changed since that the index has not read, when
  `health()` runs, then it hashes exactly that file, syncs once, compares again and reports `synced`; where the
  sync does not take it reports `failed`, as today. (D59)
- **AC-S02-36** — For each state in AC-S01-13 to AC-S01-18, AC-S01-23, AC-S01-24 and the no-row state of
  AC-S01-21, given that state, when `health()` runs narrowed, then its state equals what `health()` gives with the
  memory deleted, on the same tree and index. (D59)
- **AC-S02-37** — Given a memory `health()` cannot use (each reason listed above), when it runs, then every
  tracked file is hashed as today, the state is what today's `health()` gives, and `detail` carries one clause
  saying why. (D59)
- **AC-S02-38** — Given any CI marker set, when `health()` runs, then it compares everything and the memory file's
  bytes and times are unchanged afterwards. (D59)
- **AC-S02-39** — Given a corrupt database, when `health()` runs with a usable memory present, then it is moved
  aside and rebuilt as today, and the comparison that follows hashes every tracked file. (D59)
- **AC-S02-40** — Given a `health()` that ends `current`, or `synced` with the second comparison clean, when it
  returns, then the memory holds what a passing gate run on the same tree would have written. Given one that ends
  `failed` or `unreachable`, cannot open the database, or gets no answer from the comparison, then the memory is
  as it was. (D59)
- **AC-S02-41** — Given a `touch`, a checkout or a rebase that moves a file's times without changing a byte, when
  `health()` runs twice, then the first run hashes that file once and reports `current`, and the second hashes 0.
  (D59)
- **AC-S02-42** — Given a tree unchanged across iterations, when the runner readies iteration 50, then `health()`
  hashes as many files as it did readying iteration 2 (zero), and opens no tracked file for content. (D59)
- **AC-S02-43** — Given any state of the index, when the runner readies one iteration, then it invokes `codegraph
  sync` at most once, before the iteration starts, only where the comparison found files behind; a `current` index
  means no sync, and a built or rebuilt one is made with `codegraph init` and no sync. (D59)
- **AC-S02-44** — Given the trunk, a branch not shaped `slice/<id>`, a detached `HEAD` or any CI marker, when
  `make check-codegraph` runs after this slice, then its output and exit code are today's byte for byte, a corrupt
  database it has `health()` rebuild included, and AC-S01-10 to AC-S01-26 hold unchanged. (D59)
- **AC-S02-45** — Given any `health()` run, when it ends, then `git status` reports nothing it left and no
  `__pycache__/` sits beside the toolkit's scripts. (D59)
- **AC-S02-46** — Given the slice's diff, when it is reviewed, then the slice's one fragment (AC-S02-69) says
  three things for this part: the runner's check before an iteration compares only what changed since the last
  whole comparison; D49's sentence on what a narrowed comparison cannot see holds for it too; deleting
  `.codegraph/gate-memory.json` makes the next comparison whole. The pages that say only the gate narrows say the
  runner does as well: the docstring of `agents/code_index.py`, `scripts/extensions/codegraph/init.py`,
  `src/slipwai/project/docs.py`, `docs/cruise.md`. (D59)

*The `Scope:` line (FR-016, D60).*

- **AC-S02-47** — Given a log of 100 standing entries of which 4 carry a `Scope:` naming `S02-runner-bookkeeping`,
  10 carry `Scope: global` and 86 name other slices, when `check-decisions.py --scope S02-runner-bookkeeping`
  runs, then it prints those 14 entries verbatim in number order and no other, and exits 0. (D60)
- **AC-S02-48** — Given an entry with `Scope: S02-runner-bookkeeping, S14-result-contract`, when the verb runs for
  either id, then the entry is printed; when it runs for `S11-render-once`, then it is not. (D60)
- **AC-S02-49** — Given an entry with `Scope: S02` and another with `Scope: S12-model-sidecar`, when the verb runs
  for `S02-runner-bookkeeping`, then the first is printed; when it runs for `S1`, then neither is. (D60)
- **AC-S02-50** — Given a standing entry with no `Scope:` line, when the verb runs for any slice, then the entry
  is printed and the closing line counts it as carried as global for want of a line. (D60)
- **AC-S02-51** — Given a standing entry whose `Scope:` value is empty or unreadable, when the verb runs, then the
  entry is printed as global. (D60)
- **AC-S02-52** — Given an in-scope entry whose `Status` is `overridden by D<m>` or `overridden by human <date>`,
  when the verb runs, then it is not printed and the closing line names it by number with what overrode it. (D60)
- **AC-S02-53** — Given any run of the verb, then its last line says how many entries it carried of how many,
  split into in scope, global and carried for want of a line, and how many it left out as out of scope. (D60)
- **AC-S02-54** — Given a slice id no entry names, when the verb runs, then it prints the global and unscoped
  standing entries and exits 0. (D60)
- **AC-S02-55** — Given `specs/` with two features' `decisions.md` and no `--feature`, when the verb runs, then it
  exits non-zero with one line naming the features to choose from; given one feature, then `--feature` is not
  needed. (D60)
- **AC-S02-56** — Given any run of the verb, then no file in the tree is created or changed. (D60)
- **AC-S02-57** — Given a log in which no entry carries `Scope:` (this repository's own D1–D60 as a fixture), when
  `check-decisions` runs, then its exit code and output are what they were before the change. (D60)
- **AC-S02-58** — Given an entry with `Scope: global`, or `Scope:` listing ids bare or in backticks, placed after
  the Stage line, when `check-decisions` runs, then it passes. (D60)
- **AC-S02-59** — Given an entry with `- **Scope:**` and no value, when `check-decisions` runs, then it exits 1
  with one line naming the entry and saying the value is `global` or slice ids. (D60)
- **AC-S02-60** — Given an entry with `Scope: global, S02-runner-bookkeeping` or `Scope: the runner`, when
  `check-decisions` runs, then it exits 1 with the same kind of line. (D60)
- **AC-S02-61** — Given an entry whose `Scope:` names an id no slice in the split has, when `check-decisions`
  runs, then it passes. (D60)
- **AC-S02-62** — Given an entry with no `Scope:` after an entry that has one, when `check-decisions` runs, then
  it exits 0 and prints one `note:` naming the entry and saying it is carried as global. (D60)
- **AC-S02-63** — Given a log carrying well-formed `Scope:` lines, when the checker as released before this change
  runs over it, then it passes. (D60)
- **AC-S02-64** — Given a generated or adopted project, when the cruise command and a newly seeded owner brief are
  read, then the entry shape shows `- **Scope:** <slice ids, comma-separated> | global` directly after the Stage
  line, with the rule that a feature-level or doubtful decision is `global`. (D60)
- **AC-S02-65** — Given the generated `drive-skipper` brief, then it tells the delegate to read the standing
  entries for the brief's slice through the verb (the whole log where the brief names no slice) and to return its
  entry with a `Scope:` line. (D60)
- **AC-S02-66** — Given the generated `drive-bosun` brief, then it says the same of reading, and that every entry
  it writes carries a `Scope:` line. (D60)
- **AC-S02-67** — Given the generated cruise command, then its iteration-start and *Deciding* text point at the
  verb for a slice's question, and keep *every standing entry* for a feature-level one. (D60)
- **AC-S02-68** — Given a project whose owner brief was seeded by an earlier factory, when `slipwai migrate` runs,
  then what the project wrote in that file survives (D24) and the catch-up note says the line may be added by hand.
  *Read by D61:* `migrate` is a three-way merge, so a brief nobody edited takes the new shape from it; a refresh
  never writes the file. (D60)
- **AC-S02-69** — Given the commit that adds the line, then `VERSION` reads `1.6.0.dev0`, a fragment in
  `changelog.d/` claims `MINOR` with the catch-up paragraph, and `tests/test_changelog.py` passes. One fragment
  for the slice, the highest level winning: it also names the optional `bookkeeping` object on a log entry (D58),
  the fingerprint's one-off change of value and what it cannot see (D57), what the controls' record cannot see
  (D56) and AC-S02-46's sentences; and no file `delivery/.written` lists changes in this repository (D9). (D60)

### S24-ci-fetches-slice-base

**Gaps review open — blocked on a person's approval (D54)**, 2026-10-03, cruise iteration 8, host with `drive-skipper`
for D54: the three examples in `story-split.md` against `workflow()` in `src/slipwai/project/ci_workflows.py`,
`delivery_workflow()` and `gitlab_job()` in `src/slipwai/project/adopted_ci.py`, and `forge_checkout()`,
`not_checked()` and `check()` in `assets/toolkit/scripts/check-slice-scope.py`. No criterion is written yet, and this
note is not a *Gaps reviewed* mark: the stage is re-entered here when a person answers D54. What the review found,
for whoever resumes it:

- **Needs the person (D54).** `check-migrations` and `check-flags` run in the same `verify` job and choose a base
  from the same refs. With history fetched they hold their *new in this change* rules on every pull request — a
  contract whose expand is new in the same pull request, and a new flag seeded other than `off`, are refused in CI
  as they already are on a developer's machine. The slice's third example (*every answer is today's*) is untrue
  under any fetch, and the owner's approval (D39) was given on a description that said the opposite.
- **Answered by standing decisions once D54 is, to be written as criteria then.** Which jobs fetch: the generated
  `verify` job, the adopted `verify` job and the adopted GitLab `verify-delivery` job; never the smoke jobs, the
  container jobs (`CONTAINER_CHECKOUT`), the event-model, deploy or `ux-gates` workflows, none of which runs the
  check (the split's *Defers*). Which answers become exit 1 in a forge's checkout: no base (D31 answer 3, D32's
  arm) and *could not compare* (D35, T026, which took its exit from those two); *git could not read this checkout*
  keeps exit 0 (D35: a person's, in CI). What the failing line says where the CI is neither GitHub nor GitLab
  (D20's other forges): the same line, with words for *a full clone with the trunk's branch fetched*. The catch-up
  note: a workflow the project took over, and a pipeline of the project's own with a CI marker set and a shallow
  clone, are not rewritten by `migrate` and turn red on a slice branch until the job fetches history.
- **For the plan's research, each with its citation or marked assumed.** What `actions/checkout@v6` leaves under
  `refs/remotes/origin/` at `fetch-depth: 0` on a `pull_request` run; that a GitLab runner with `GIT_DEPTH: "0"`
  fetches every branch; that Gitea's and Forgejo's runners do the same with the action.
- **The slice's own leftovers.** The unreleased fragment `changelog.d/slice-scope-base.md` says a CI run with
  nothing to compare with keeps exit 0; released together with this slice's fragment the entry would say both, so
  the plan amends that sentence. The suites that assert *NOT checked*, exit 0, under a CI marker change with the
  checker (`tests/test_slice_scope_no_base.py`, `tests/test_slice_scope_hostile_base.py`).
