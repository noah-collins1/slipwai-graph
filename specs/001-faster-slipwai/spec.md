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
2. **Given** an unchanged `specs/` tree, **When** `fingerprint()` runs, **Then** it reads no file contents.
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
  only changed files.
- **FR-016**: Decision entries MUST carry a `Scope:` line; the skipper MUST be briefed with in-scope and global
  decisions only.
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
  codegraph sync per iteration unless a delegate reports changed files.
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
