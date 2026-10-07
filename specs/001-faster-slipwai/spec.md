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

**Independent Test**: On a generated Python project, on a branch other than the trunk with no CI marker set
(D74), run `make verify` twice; the second run exits 0 in under a second and says it reused the stamp. `make -j verify` passes with the same set of checks as the serial
run, each with the verdict it had (D89). `check-imports` enumerates at most 100 entries on the skeleton.

**Acceptance Scenarios**:

1. **Given** a tree the gate passed, on a branch other than the trunk with no CI marker set (D74), **When**
   `make verify` runs again with no change, **Then** it prints the stamp it reused and exits in under 1 s.
2. **Given** a one-character change to a source file, **When** `make verify` runs, **Then** the full gate runs
   and a new stamp is recorded.
3. **Given** `VERIFY_FORCE=1`, **When** `make verify` runs on a stamped tree, **Then** the full gate runs.
4. **Given** a changed `scripts/check-*.py`, **When** `make verify` runs, **Then** the stamp is invalid and the
   full gate runs.
5. **Given** the skeleton, **When** `make -j verify` runs, **Then** every check that ran serially runs, in any
   order after `check-python` and the syncs, and the exit status is zero exactly when the serial run's is (D89).

---

### User Story 2 - A slice branch runs the checks whose inputs changed (Priority: P1)

*Revised 2026-10-04 (owner, after external review): selection is by verification dependency, not by touched
context; incomplete knowledge broadens the run.*

On a `slice/<id>` branch the developer runs `make verify-scoped`. It selects checks from a
**verification-dependency record**: for each check, the inputs it reads (files, contract versions, tools,
configuration, environment variables) and the components whose behaviour it asserts, including downstream
consumers of a changed contract and any multi-component integration obligation. A check runs when any of its
inputs changed against the slice's base. **Where the record cannot establish which checks are affected** (a
changed file no check claims, a check with no recorded inputs, an input the record never saw), the scheduler
broadens: first to the checks of every component that file could reach, and up to the full gate. The output
names every check it skipped and why. The merge root and CI always run the full gate, with xdist.

**Why this priority**: The branch gate is what the merge tree (Story 3) and peer reconciliation (Story 10)
rely on. Conservative broadening lets it deliver speedups while dependency coverage is still incomplete.

**Independent Test**: On a branch changing one file that exactly one context's checks claim, only those checks
and the contract tests of that context's consumers run. On a branch changing a file no check claims,
`verify-scoped` runs the full gate and says why. On `main` it is the full gate. The full gate's findings on the
same tree are identical before and after.

**Acceptance Scenarios**:

1. **Given** a change to a file one check set claims, **When** `make verify-scoped` runs, **Then** those checks
   run, plus the contract tests of every consumer of a contract the file implements, and every skipped check is
   named with its reason.
2. **Given** a change to a file no recorded check claims, **When** `make verify-scoped` runs, **Then** it runs
   the full gate and prints that dependency knowledge was incomplete for that file.
3. **Given** a change to a tool version, a configuration file or an environment variable a check reads,
   **When** `make verify-scoped` runs, **Then** every check that reads it runs.
4. **Given** a change touching a component named in a multi-component integration obligation, **When**
   `make verify-scoped` runs, **Then** that obligation's checks run.
5. **Given** `main`, **When** `make verify-scoped` runs, **Then** it is `make verify`.
6. **Given** a branch that changed one production module, **When** `make mutation` runs, **Then** only that
   module's mutants run, for every backend with a wired mutation tool (Go and Java Spring now; TypeScript and Python
   as their slices land), a placeholder backend still exits 2 with its setup message, and `make mutation-full` still
   runs the whole module. *(Amended by D137.)*
7. **Given** the merge root, **When** `make verify` runs, **Then** pytest runs with xdist and the pass/fail set
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

**Independent Test**: On the 16-slice fixture, change one slice; `make model` launches one browser, redraws
the three diagrams whose source changed (that slice's, its segment's and the whole timeline's; D67) and finishes
in under 2 s. Bytes handed to the example-map stage for slice 16 equal those for
slice 1.

**Acceptance Scenarios**:

1. **Given** a 16-slice model with one changed slice, **When** `make model` runs, **Then** one browser launches
   and exactly the diagrams whose source changed are redrawn: that slice's, its segment's and the whole
   timeline's, which contains every slice (D67).
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

### User Story 9 - A learned classifier chooses the model for each spec node (Priority: P3)

Model routing is not left to a hand-written rule. A JEV-style joint-embedding predictive model, or an open-source
equivalent that runs locally, is the classifier: for each spec node it reads the slice block, its one-hop
contracts, the task manifest, the planner's difficulty score and the agent's role, and returns the model tier.
It is calibrated on this repository's own result contracts and benchmark records, and the rule-based policy of
User Story 6 is its fallback while it has too little data or is unavailable.

**Why this priority**: Depends on User Stories 6 and 7 for its inputs and training data, and on the gate slices
for a cheap enough loop to measure it.

**Independent Test**: With `route_by_difficulty: model`, dispatching a worker on a fixture spec node produces a
tier from the classifier with its inputs and confidence logged; with the classifier absent or below its record
floor, the same dispatch logs `fallback: rule` and the rule's tier; the merge root's gate findings are
unchanged either way.

**Acceptance Scenarios**:

1. **Given** `route_by_difficulty: model` and a calibrated classifier, **When** a worker is dispatched on a spec
   node, **Then** the tier comes from the classifier and the log names the node, role, inputs, tier and
   confidence.
2. **Given** fewer than the record floor of result contracts, or the classifier unreachable, **When** a worker is
   dispatched, **Then** the rule-based policy decides and the log says `fallback: rule`.
3. **Given** a worker's scoped gate fails after a low-tier dispatch, **When** it is re-dispatched, **Then** the
   cascade goes one tier up and the outcome is recorded against the classifier's prediction.
4. **Given** the open-source backend is selected, **When** the classifier runs, **Then** no spec text leaves the
   machine.

---

### User Story 10 - Neighbouring slices reconcile their contracts with versioned evidence (Priority: P2)

*Added 2026-10-04 (owner, after external review). Supersedes the idea that pairwise agreement alone implies
consistency, or that an edge-colouring schedule bounds reconciliation time.*

Workers start against explicit contract versions. When a change actually affects a boundary, the two slices on
that edge negotiate directly: they exchange structured proposals (contract diff, assumptions, affected input
fingerprints, failing examples, evidence references), never reasoning transcripts. The current contract owner
decides within the spec; a change to a requirement escalates. An agreement is recorded as **evidence**: the
contract version and checks that passed, pinned to **local input fingerprints** of the components, contract
versions, tools and dependencies those checks read, not to the repository's commit. A change to any input of a
piece of evidence invalidates it and every obligation that depends on it; an unrelated change leaves it
reusable. Local negotiation has a small configurable budget of rounds, after which the unresolved coupled
subgraph escalates to a coordinator. **Multi-component invariants** (for example an order, payment and stock
reservation committing together) carry a declared owner and an integration obligation that peer agreement
cannot discharge. Integration accepts one coherent revision set: every required invariant must be covered by
recorded evidence or an integration obligation, and the full acceptance gate runs on the exact integrated tree,
whose complete manifest is kept.

**Why this priority**: It moves most contract reconciliation off the central coordinator without trading away
correctness. It depends on the verification-dependency record (Story 2) and the result contract (Story 6).

**Independent Test**: The milestone demonstration: two agents produce compatible changes on an edge; evidence is
recorded; a relevant input changes; the affected evidence is invalidated; the disagreement is resolved or
escalated; the resulting revision passes acceptance.

**Acceptance Scenarios** (protocol correctness, independent of performance):

1. **Given** evidence pinned to inputs that have since changed, **When** integration is attempted, **Then** the
   stale evidence cannot authorise it.
2. **Given** a change to a file none of a piece of evidence's inputs include, **When** the evidence is checked,
   **Then** it is reused, not re-run.
3. **Given** a relevant input change, **When** invalidation runs, **Then** every dependent piece of evidence and
   every dependent integration obligation is invalidated.
4. **Given** three slices whose pairwise proposals cannot all hold together (A = B, B = C, C ≠ A), **When** the
   local budget is spent, **Then** the coupled subgraph escalates explicitly; it is never accepted.
5. **Given** a change for which dependency information is missing, **When** verification is selected, **Then**
   it broadens, up to the full gate.
6. **Given** a revision set accepted for integration, **When** the integrated tree is built, **Then** acceptance
   runs on that exact tree and its manifest is recorded.
7. **Given** a required invariant with no evidence and no integration obligation covering it, **When**
   integration is attempted, **Then** it is refused and the uncovered invariant is named.

---

### Edge Cases

- A stamped tree whose toolchain changed (new ruff, new mypy): the gate re-runs. A tool a committed lock pins
  moves the key through the lock, a tracked file; the recorded tool versions are those of the tools the machine
  supplies (D75).
- `make -j` and a target that writes `.specify/`: no target of the gate writes there, and a test holds it;
  `agents` and `install`, which do, are not in the gate, and running them beside it in one `make -j` is not
  promised (D88).
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
- **FR-002**: The gate's checks MUST be declared so `make -j verify` runs concurrently every check that writes
  nothing another reads, with the same results as the serial run; a target that writes what another target of the
  gate reads or writes MUST never run beside it, on every GNU Make from 3.81, by being ordered ahead of it as a
  prerequisite (D88). The gate of a repository that adopted the method, started on its own Makefile, MUST run serially whatever `-j`
  says, and MUST leave the `-j` of a root Makefile that includes it to that repository's own targets (D88, D95).
  *Same results* is the same checks, each with the verdict it had, an exit status that is zero exactly when the
  serial run's is, and the closing line on a pass; it is not the order of lines (D88, D89).
- **FR-003**: `./scripts/verify` MUST sync each toolchain once per invocation; `check-drawio` MUST skip
  `npm install` when the installed tree matches a committed lockfile. *The invocation* is one `make` run, and a
  mode of the script reached any other way syncs first (D90); the lockfile is one the factory ships beside the
  model tooling's manifest, and *matches* is the root's rule, a marker newer than both manifests (D91).
- **FR-004**: `check-imports` and `check-migrations` MUST prune `.venv`, `node_modules`, `target/`,
  `__pycache__` and `.git` before descending, and read `project.json` once.
- **FR-005**: `model.yaml` MUST be parsed once per verify into a sidecar every consumer reads.
- **FR-006** *(revised 2026-10-04)*: `make verify-scoped` MUST exist and MUST equal `make verify` on `main`. On
  a `slice/<id>` branch it MUST select checks from a verification-dependency record (each check's inputs:
  files, contract versions, tools, configuration, environment variables; the components it asserts, including
  consumers of changed contracts and multi-component obligations), run every check with a changed input, name
  every skipped check with its reason, and broaden, up to the full gate, wherever the record cannot establish
  which checks are affected. Selecting tests by touched context alone is not sufficient.
- **FR-007**: The drive ladder MUST call `verify-scoped` at slice start and before the push, and the full gate
  once at the merge root.
- **FR-008**: `make mutation` MUST scope to the diff against merge-base for every backend whose mutation tool is
  wired; `mutation-full` MUST keep the whole-module run. A backend whose target is a placeholder MUST keep failing with
  its setup message, never pass. Stryker (TypeScript) and mutmut (Python) are each wired by their own slice;
  `java-quarkus` stays a placeholder while pitest #1287 stands. *(Amended by D137.)*
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
  MUST hold it; a missing block MUST be a converge finding. *Read by D134, D135, D136 (ADR 0006):* the shape is a
  JSON object, schema `contract: 1`, kept in the slice's append-only `hand-backs.md`; the block also carries
  `files_changed`; a missing block is closed by one continuation of the same delegate or a recorded `Missing:` line.
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
- **FR-023** *(revised 2026-10-04)*: `check-agents`, `check-speckit`, `check-extensions` and
  `check-constitution` MUST declare their inputs in the verification-dependency record and run on a branch only
  when one of them changed; a check with undeclared or unreadable inputs MUST run. Always on `main` and in CI.
- **FR-024**: The runner MUST compute `controls_signature()` once per iteration from mtimes, and run one
  codegraph sync per iteration unless a delegate reports changed files. *Read by D56:* each control file's content
  is read at most once per iteration unless its size, times or identity changed; what the run parks on stays a
  comparison of content. *Read by D59:* the *unless a delegate reports* half waits for `S40-reported-sync` (D135; `S14-result-contract`
  adds the `files_changed` field it reads).
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

- **FR-034**: `models.json` MUST accept `route_by_difficulty: off | log | rule | model`; `model` MUST route each
  spec node through a classifier whose backend is pluggable: a JEV-style joint-embedding predictive model where
  one is available, otherwise an open-source equivalent that runs locally.
- **FR-035**: The classifier's inputs MUST be the spec node's block, its one-hop contracts, the task manifest,
  the planner's difficulty score and the agent's role; its output MUST be a tier and a confidence, both logged.
- **FR-036**: The classifier MUST be calibrated on this repository's result contracts and benchmark records, and
  MUST fall back to the rule-based policy (FR-027) below a documented record floor or when unreachable, logging
  `fallback: rule`.
- **FR-037**: Planner, judge/converge, skipper and adversary roles MUST keep the fixed tiers of FR-027; the
  classifier decides workers only, and a failed scoped gate MUST cascade one tier up with the outcome recorded
  against the prediction.
- **FR-038**: With the open-source backend, no spec text MUST leave the machine.

- **FR-039**: Agreements between neighbouring slices MUST be recorded as evidence: the contract version and the
  checks that passed, pinned to local input fingerprints (component contents, contract versions, tools,
  dependencies), not to the repository commit.
- **FR-040**: A change to any input of a piece of evidence MUST invalidate it and every evidence record and
  integration obligation that depends on it; a change outside its inputs MUST leave it reusable.
- **FR-041**: Peer negotiation MUST exchange structured proposals only (contract diff, assumptions, affected
  fingerprints, failing examples, evidence references); the contract owner decides within the spec; a
  requirement change escalates.
- **FR-042**: Local negotiation MUST stop after a configurable round budget and escalate the unresolved coupled
  subgraph to a coordinator; it MUST never accept a set of agreements that cannot all hold together.
- **FR-043**: Every multi-component invariant MUST have a declared owner and an integration obligation; peer
  agreement MUST NOT discharge it.
- **FR-044**: Integration MUST accept one coherent revision set only when every required invariant is covered by
  current evidence or an integration obligation, MUST run the full acceptance gate on the exact integrated tree,
  and MUST record that tree's complete manifest.
- **FR-045**: Performance claims for the merge tree (Story 3) and peer reconciliation (Story 10) MUST be
  established by a comparison under the same worker budget and acceptance criteria: optimised gates with existing
  integration; plus the merge tree; plus versioned peer reconciliation; on fixtures of disjoint changes,
  dependency chains, cyclic disagreements and shared-file changes; measuring accepted changes per hour, median
  and tail completion time, cost per accepted change, invalidations, escalations and independently detected
  integration defects. Protocol acceptance (Story 10's scenarios) is separate from and precedes it.

- **FR-046** *(added 2026-10-05, owner, after external code review)*: Coordination state MUST live in an executable
  tool with explicit, versioned state, not only in generated instructions: slice readiness, claims, evidence
  records and their validity, invalidation, and integration eligibility are operations an agent calls and a gate
  checks (for example `python3 scripts/agents/coordinate.py ready|claim|evidence|invalidate|eligible`). Agents make
  the semantic decisions; the tool enforces the coordination rules and refuses an operation its state does not
  allow. The Lean protocol work formalises these same states and transitions.
- **FR-047**: Each active slice MUST record its write set (files and contract versions it changes) and its read set
  (the inputs its checks and evidence depend on). Two active slices whose write sets overlap, or where one writes
  what the other reads, MUST NOT both be eligible for integration until one is serialised behind the other or the
  overlap is escalated. Permission under the shared-surface rule is not compatibility.
- **FR-048**: The factory's own test selection MUST follow generation dependencies: a change to a generator, an asset
  or the catalog maps to the generated configurations it affects, to the files those generate, and to the checks
  that apply to them. Where that mapping cannot establish the affected set, selection broadens, up to the full
  matrix. The merge root and CI keep running the full matrix. This is the factory analogue of FR-006.
- **FR-049**: The benchmark MUST record, per slice and per feature, separately: elapsed time from a slice becoming
  ready to its accepted integration; accumulated stage time; waiting time by cause (dependency, worker, review,
  integration); and inference cost with rework. Summed stage time MUST NOT be reported as elapsed time once slices
  overlap. FR-045's comparison uses these measures.

- **FR-050** *(added 2026-10-05, owner, from the author's updated product and engineering material)*: Every
  record FR-046's tool writes (claim, evidence, eligibility, decision classification) MUST be append-only and carry
  the hash of its full input, the version of the rules that produced it, the rules that fired and a timestamp; a
  record MUST NOT be reclassified after the fact, only superseded by a new record.
- **FR-051**: The reversibility score (FR-029) MUST be computed by a fail-closed classifier over factual booleans and
  enums only, never free text: at least contract change, schema change, permission or authentication change,
  pricing or customer-visible effect, data export, and `rollback_complexity` (trivial | hours | days |
  needs-migration). A missing or unrecognised field MUST classify as `hard`. `days` and `needs-migration` MUST be
  `hard`. Size of change and urgency MUST NOT change the classification. The classifier MUST have a test per rule
  and MUST change only as a decision taken at the hard tier.
- **FR-052**: A contract-edge change MUST follow the contract-first sequence: the consumer slice writes a failing
  expectation against the provider's contract first; the provider slice's gate runs every consumer expectation on
  its edges against the real provider (never only against the consumer's fake); destructive changes go through
  expand then contract, the contract phase no earlier than the next convergence. The expectation file's hash and
  the provider's input fingerprint are the evidence record's inputs (FR-039).
- **FR-053**: Provisional approval (FR-030) and classifier routing (FR-034) MUST roll out through recorded modes:
  shadow (the decision is computed and logged, nothing changes), advisory (shown beside the human or rule decision),
  enforced, in that order, with the mode in the run's settings and the move between modes a decision entry.
- **FR-054**: The locality report (FR-025) MUST flag a hot spot when, for two consecutive weeks or two consecutive
  features, the top-3 share of slice touches exceeds 50 percent, or the Gini coefficient exceeds 0.6, or K-effective
  falls below 0.4 times the number of slices; thresholds MUST be calibrated to the number of slices (a top-3 share
  target below 3/K is unreachable) and stated with the report. The recommended response is a two- or three-way
  split, re-measured after the next two features, never added queueing.
- **FR-055**: The split skill MUST flag for splitting a slice whose plan exceeds about one day of agent work or whose
  contract exposes more than ten operations, and a slice reading more than five operations from one neighbour as a
  boundary to reconsider; these are prompts to the split stage, not hard refusals.
- **FR-056**: The skipper MUST escalate one tier at a time, never skipping a tier, and MUST NOT surface a question
  in a diff or a note as a substitute for escalating. When three decisions with the same shape occur within one
  feature, it MUST propose a rule for the owner brief in a decision entry instead of continuing to decide case by
  case.
- **FR-057**: The benchmark MUST report decision health: the share of easy and guarded decisions escalated to hard
  (healthy band 5 to 15 percent; zero or above 25 percent is flagged), the misclassification rate found by review
  (flag above 5 percent), and median decision wait by tier.

### Key Entities

- **Verify stamp**: tree hash, gate script hash, tool versions, timestamp, result. The tree hash is of the working
  files and of everything else a check answers from (D73); each tool is recorded by name with the line it
  reported (D75); the result is only ever a pass (D76).
- **Merge tree node**: an integration branch, its two (or f) children, its scoped-gate result, its conflict state.
- **Result contract**: scope, status, contracts_changed, invariants_checked, tests, decisions, assumptions,
  unresolved, change_summary, difficulty_observed.
- **Contract edge**: provider slice, consumer slice, contract id; derived: degree, cut, cross-context flag.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On an unchanged tree, `make verify` returns in under 1 second — on a generated Python project, on a
  branch other than the trunk, outside CI, measured at the demo (D74, D75; AC-S03-20).
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
- **SC-012**: Over one feature with `route_by_difficulty: model`, the classifier's predicted tier and the
  realised outcome are joined per task in `make benchmark`, with the fallback rate reported.
- **SC-013**: The Story 10 milestone runs end to end: compatible changes, evidence recorded, a relevant input
  changes, the affected evidence is invalidated, the disagreement is resolved or escalated, and the resulting
  revision passes acceptance.
- **SC-014**: The FR-045 comparison is run and reported; no performance figure for Stories 3 or 10 is stated as
  a result before it.
- **SC-015**: Readiness, claims, evidence validity and integration eligibility are answered by FR-046's tool, and a
  gate refuses an integration whose recorded state does not allow it.
- **SC-016**: A change to one generator touches only the factory tests of the configurations it affects; a change
  whose effect cannot be established runs the full matrix.
- **SC-017**: A decision with a missing or unknown classifier field is `hard`; the same input always yields the same
  record hash and classification; no record is edited in place.
- **SC-018**: A provider change is accepted only when every consumer expectation on its edges passes against the
  real provider.
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

*Added after acceptance by the adversary pass (D63, D64).* D56's sentence *the after-signature of one iteration never
serves as the before of the next* stands, with D64's clause: *it is compared with it, so no control changes between
two iterations silently.*

- **AC-S02-70** — Given an iteration that leaves a process outside its process group, and that process changes a
  gate after the iteration's log entry is written, when the next iteration would start, then the run parks before
  it starts, naming that file `(modified)` and saying the change came between the two iterations. (D64, adversary
  A2)
- **AC-S02-71** — Given the same change under `--no-park`, when the next iteration would start, then the run exits
  3 with that park line as its last line, and the log holds no entry for an iteration that did not run. (D64,
  adversary A2)
- **AC-S02-72** — Given a run parked on a between-iterations change, when a person keeps the change and resumes,
  then the next iteration runs, its entry carries `controls_changed_between` naming that file and no
  `controls_changed` for it, and the feed carries one line naming it. (D64, adversary A2)
- **AC-S02-73** — Given a run parked on a between-iterations change, when a person reverts the change and resumes,
  then the next iteration runs and its entry carries neither field. (D64, adversary A2)
- **AC-S02-74** — Given a run parked for any other reason, when a control is changed during the park and the run
  resumes, then the run does not park for it, the next entry carries `controls_changed_between` naming the file,
  and a later iteration that changes the same file still parks naming it in `controls_changed`. (D64, adversary
  A2)
- **AC-S02-75** — Given an iteration that changed a gate and was parked for it, when a person keeps the change and
  resumes with a message, then the next entry carries no `controls_changed_between`. (D64, adversary A2)
- **AC-S02-76** — Given a file added under `tools/` between two iterations, when the next iteration starts, then
  the run does not park and no field is written; and a file modified or deleted under `tools/` between two
  iterations parks the run naming it. (D64, adversary A2)
- **AC-S02-77** — Given no control changed between two iterations, when the next iteration starts, then no line is
  printed, no field is written, and no control file's content is read that the record vouches for. (D64, adversary
  A2)
- **AC-S02-78** — Given a runner process's first iteration, when it starts, then nothing is compared with an
  earlier process's controls, and its entry carries no `controls_changed_between`. (D64, adversary A2)
- **AC-S02-79** — Given an iteration ended by `tell --now` and a control changed before the next starts, when the
  next iteration would start, then the run parks as between any two iterations, and the person's message is given
  to the iteration that runs after the park. (D64, adversary A2)
- **AC-S02-80** — Given a path the runner reads or appends to as its own — the raw stream, the log — holding
  something that is not a regular file (a FIFO, a directory, a device), when an iteration ends, then the runner
  never blocks on it: a stream that is not a regular file gives no `index_use`, as before the slice, in the runner
  and in `status`; a log that is not one ends the run with one line naming it; and in both cases a control the
  iteration changed is compared and named first, so the run parks or ends saying so (A1, B1, A3). (D63)
- **AC-S02-81** — Given a standing entry whose `Scope:` names the slice by its head in another spelling —
  `S02-runner` or `S2` or `s02-runner-bookkeeping` for `S02-runner-bookkeeping` — when `--scope` runs for that
  slice, then the entry is printed: ids meet when their letters, case set aside, and their number, read as a
  number, are equal, whatever the slug; `S1` still does not meet `S12` (C1; amends AC-S02-49). (D63)
- **AC-S02-82** — Given a `Scope:` token holding more than one id-shaped head — a range `S01-S03`, two ids joined
  by a full stop — or any digit that is not ASCII, when `check-decisions` runs, then it exits 1 naming the entry,
  and the verb carries the entry as global (C2, C3). (D63)
- **AC-S02-83** — *Reworded by D65.* Given an entry with more than one `Scope:` line at the start of a line, when
  `check-decisions` runs, then it exits 1 naming the entry; given more than one `Status:` line, then it prints a
  `note:` naming the entry and its exit code is what it would have been; in both cases the verb carries the entry
  whatever either line says. Lines are divided at line feeds only, so a form feed or U+2028 inside a field does not
  make a second field (T022, C7, C8). (D63, D65)
- **AC-S02-84** — Given `--scope` with a value that is not id-shaped — empty, lower case, a path, a trailing
  space, another flag — or any argument the script does not know (`--scope=S02`, `-scope`), when it runs, then it
  prints the usage line on stderr and exits 2, and never runs the gate in its place; `--help` prints the usage and
  exits 0; with no argument, and with `--adversary-baseline`, the script does what it did (C4, C5). (D63)
- **AC-S02-85** — *Reworded by D65.* Given a log holding a block under a `## ` heading the checker cannot read as
  `## D<n> — <question>`, when the verb runs, then that block is printed in its place and counted on the closing
  line as carried for want of a heading it can read, what was printed and what was counted agree, and the verb
  exits 1 saying the log does not pass `check-decisions`. A byte-order mark at the start of the file is read past
  by the verb, which prints and counts the first entry as an entry; the gate reads such a log as the earlier checker
  did. And given any log with no `Scope:` line that is UTF-8, then the gate's exit code
  and findings are the earlier checker's (C6). (D63, D65)
- **AC-S02-86** — Given a `decisions.md` that is not UTF-8, when the gate or the verb runs, then it prints one
  line naming the file and exits 1, with no traceback (C9). (D63)
- **AC-S02-87** — Given an index whose `files` table holds no row, when `health()` ends `current`, then it writes
  no record, as no gate run would; given a comparison that gives no answer — not a checkout, no `files` table —
  then `detail` says that, and never *compared everything* (B2, B3). (D63)
- **AC-S02-88** — Given the stream's identity check and each `except` arm around the record in `health()`, then
  each is seen red when removed, by an example with a stand-in written in the test tree, or is gone (T020, T021).
  (D63)

### S11-render-once

**Gaps reviewed** 2026-10-03, cruise iteration 10, host with `drive-skipper` for D68 and D69: the two examples in
`story-split.md` against `main()`, `runMermaid()` and `stampSvg()` in `assets/toolkit/scripts/event-model/render.ts`,
`stamp()` and `extractHash()` in `mermaid.ts`, the stamp's reader in `check.ts`, the `model` recipe in
`src/slipwai/project/model_targets.py` and the ignore lines in `src/slipwai/project/gitignore.py`. Measured on a
project generated for the purpose (event-modelling profile, Python backend, no frontend, target `none`; a model of
16 state-change slices): today's run starts 25 browsers and takes 15.95 s; one browser drawing one diagram takes
about 0.6 s; the recipe's install step, already installed, 0.29 s. Found and written back: the example's *two
diagrams* left out the whole timeline, which contains every slice (D67); a skip resting on the source hash alone
would keep a picture drawn by an older renderer, and a stamped file cut short would be skipped as current (D68);
the two output directories are deleted wholesale today, which a skip cannot survive (D68); nothing said what the
2 seconds times, on what, or what holds *one browser* without a browser in the suite (D69). Every rendered file is
ignored in a generated project, so a fresh checkout and CI draw everything: the skip is a developer's-machine
saving and the single browser is the saving everywhere.

- **AC-S11-1** — Given any model with at least one slice, when `make model` runs, then at most one renderer session
  (one browser) is opened: exactly one where at least one diagram is drawn, opened on the first diagram to draw,
  and none where nothing is drawn. (D69)
- **AC-S11-2** — Given the reference fixture (D69: 16 state-change slices of three frames each, default `render`
  settings, no slice reading another — 25 diagrams: 1 whole timeline, 8 segments, 16 slices), every diagram drawn
  by a previous run, and an edit to one slice's own content that keeps its frame count and that no other slice
  reads, when `make model` runs, then one session is opened, exactly three diagrams are redrawn — the timeline,
  that slice's segment and that slice — and 22 are left as they were, byte for byte. (D67)
- **AC-S11-3** — Given any edit to the model, then exactly the diagrams whose Mermaid source hash changed are
  redrawn and no other: an edit that adds a frame to one slice also redraws the whole timeline and every later
  segment, whose numbering moves, and no later slice's own diagram, whose source does not (read from the code at
  T003; D68's illustration said every later slice, and the rule, not the illustration, is the criterion).
  (D67, D68)
- **AC-S11-4** — Given a first run, a fresh checkout or a CI run on the fixture, then one session is opened, 25
  diagrams are drawn and none is left; no time is claimed for it. Given a one-slice model on a first run, then one
  session draws three diagrams. (D69)
- **AC-S11-5** — Given a diagram, then it is left only when all four hold, and is drawn otherwise: the first line
  of its SVG is `<!-- em-source-sha256: <hash> -->` with the hash of the Mermaid the model produces now (the `.mmd`
  on disk is never the evidence); its second line is `<!-- em-renderer-sha256: <key> -->` with this run's renderer
  key; the file ends with `</svg>` once trailing whitespace is trimmed; and no CI marker is set (`CI`,
  `GITHUB_ACTIONS` or `GITLAB_CI` non-empty). (D68)
- **AC-S11-6** — Given the renderer key, then it is one SHA-256 over the installed mermaid-cli version and the
  installed mermaid version and the installed puppeteer version (D70), each read from its `package.json` under
  `scripts/event-model/.mermaid-cli/`; the bytes
  of `render.ts`, of `patch-mermaid-swimlanes.ts` and of any other script the drawing runs through (the plan names
  the closed set); and the bytes of the file `MERMAID_PUPPETEER_CONFIG` names, or a fixed word where it is unset.
  A change to any one of them redraws every diagram on the next run. A browser upgraded behind an `executablePath`
  the config names is not noticed, and the page says so beside the sentence on forcing a redraw. (D68, D70)
- **AC-S11-7** — Given an SVG with no renderer line (one an earlier factory drew), then it is redrawn, once. Given
  the second line, then `extractHash` reads the source stamp exactly as before, and the page carries both comments
  where it inlines the picture. (D68)
- **AC-S11-8** — Given a diagram being drawn, then its SVG reaches its final name only by a rename of a complete
  file that already carries both lines; the temporary file sits on the same filesystem in a directory the
  project's ignore list already covers, and no ignore line is added. Given a draw that fails, then the earlier
  file is as it was, the run names the diagram and exits non-zero. Given a file torn by anything else (no closing
  `</svg>`), then it is redrawn. (D68)
- **AC-S11-9** — Given `PNG=1` or `--png`, then `model.png` is drawn on every such run, never left, in the same
  session and by the same rename; not asked for, an existing `model.png` is left as today. (D68)
- **AC-S11-10** — Given a person who wants everything redrawn, then there is no setting and no flag: deleting a
  diagram redraws it, and deleting `docs/event-model/model.svg`, `segments/` and `slices/` redraws all of them —
  the whole timeline sits outside the two directories — and `assets/toolkit/docs/event-model/README.md` says so in
  one sentence. (D68, D71)
- **AC-S11-11** — Given `segments/` and `slices/`, when a run starts, then every entry whose name the current model
  does not produce (`model-<i>.mmd` and `model-<i>.svg` per segment, `<slice id>.mmd` and `<slice id>.svg` per
  slice) is removed before anything is drawn — file or directory, a leftover temporary included — so a renamed or
  removed slice still leaves nothing behind. The empty-model branch does what it does today. (D68)
- **AC-S11-12** — Given the `.mmd` files, `model.html` and the README block, then each is computed every run and
  written only where its bytes differ from the file on disk; `model.html` is built from the SVGs on disk after
  drawing. One `wrote <path>` line is printed for each file the run wrote and none for a file it left. (D68, D69)
- **AC-S11-13** — Given a run on a model with slices, then its closing line says what it did: on the fixture's edit,
  `model: 16 slices, 3 of 25 diagrams drawn, 22 unchanged. Open docs/event-model/model.html to browse it.`; where
  nothing changed, `model: 16 slices, 0 of 25 diagrams drawn, 25 unchanged; no browser started. Open
  docs/event-model/model.html to browse it.` The empty-model message stays as it is. (D69)
- **AC-S11-14** — Given the suite, then the counts — sessions opened, diagrams drawn, diagrams left — are held for
  the changed-slice run, the nothing-changed run and the first run through a stand-in written in the test tree that
  implements the session's interface: no browser, no mocking framework, no clock. (D69)
- **AC-S11-15** — Given the reference fixture on a warm tree (mermaid-cli installed, every diagram drawn by a
  previous run, then the one edit; no PNG), when `make model` runs at the demo, then the whole recipe as typed,
  its install step included, finishes in under 2 seconds of wall time and one real browser is seen to start by a
  means other than the run's closing line. The command, the machine and the number are written in the quickstart,
  beside the first run's time and today's 15.95 s. A measurement of 2 seconds or more is a failed demo, never a
  revised number. (D69, SC-004)
- **AC-S11-16** — Given what the renderer already does — the swimlane patch applied to the installed mermaid before
  the first draw, `MERMAID_PUPPETEER_CONFIG` passed to the browser, the line naming that variable when Chromium
  will not start as root, the pinned width — then each still holds through the one session.
- **AC-S11-17** — Given a repository already generated, after `slipwai migrate`, then nothing is asked of it: its
  first `make model` redraws every diagram once, and since the output is ignored nothing committed changes; one
  that removed the ignore lines and commits the diagrams sees the second comment line in each SVG once. The
  fragment in `changelog.d/` says both and claims PATCH; `VERSION` stays `1.6.0.dev0`. (D68)

- **AC-S11-18** — Given two runs in one tree, then they never write the same temporary: its name carries the
  process id. The page says one run per tree at a time; a run whose temporary another run removed fails naming
  the file, and the next run draws it. (D71)
- **AC-S11-19** — Given a CI marker, then the closing line says in one clause that everything was drawn because
  one is set; the two lines of AC-S11-13 are unchanged where none is. (D71)
- **AC-S11-20** — Given a repository that edited `render.ts`, then the fragment's catch-up says `slipwai migrate`
  may meet a conflict there, because the renderer's pin, width and browser handling moved to `render-session.ts`.
  (D71)

- **AC-S11-21** — Given `docs/event-model/segments` or `slices` that is a symbolic link, a file or anything but a
  real directory, when a run starts, then that entry is removed as itself — never what a link names — and a
  directory is made; nothing outside `docs/event-model/` is removed by any run. Given an entry at a name the model
  produces (an SVG, a `.mmd`, the page, the PNG) that is not a regular file — a link, a directory, a FIFO — then it
  is removed and drawn or written afresh, never read, written through or descended. Each thing removed from the two
  directories is printed as `removed <path>`. (D72)
- **AC-S11-22** — Given a slice id as long as the model allows a file name for, then its diagram is drawn: the
  temporary's name does not carry the file's name. (D72)
- **AC-S11-23** — Given the renderer key, then every environment variable whose name begins `PUPPETEER_` is in it,
  as name and value in name order, and the Puppeteer config's bytes are read once: the bytes keyed are the bytes
  launched with. A Puppeteer rc file is not noticed, and the page says so beside the browser behind a path the
  config names. (D70, D72)
- **AC-S11-24** — Given a browser that stops during a run — killed, crashed or disconnected — then the run says
  once that the browser stopped, blames no diagram for it, exits non-zero, and leaves the earlier files, no
  temporary and no browser. Given a browser that cannot start for want of a sandbox, then the line names
  `MERMAID_PUPPETEER_CONFIG` whoever runs it; given one whose files are missing from the install, then the line says
  to delete `scripts/event-model/.mermaid-cli` and run again. (D72)
- **AC-S11-25** — Given a run that drew only the PNG, then the closing line says the PNG was drawn. (D72)

### S03-verify-stamp

**Gaps reviewed** 2026-10-04, cruise iteration 11, host with `drive-skipper` for D73 to D76 and the host's own
D77: the five examples in `story-split.md` against `makefile()` in `src/slipwai/project/makefile.py`, `GATE` and
`gate_target()` in `src/slipwai/project/adopted_targets.py`, the Python backend's `scripts/verify`, the ignore
lines in `src/slipwai/project/gitignore.py` and what each `assets/toolkit/scripts/check-*.py` reads. Measured on a
project generated for the purpose (event-modelling profile, Python backend, 379 tracked files) and on this
repository (2181): hashing the working files through a scratch index 5 to 10 ms, hashing every covered file's raw
bytes 60 ms here, asking `uv`, `python3`, `node`, `git` and `make` for their versions 0.10 s together, hashing
`scripts/` 0.02 s. Found and written back: the gate judges working files, not a commit, and FR-001's *git tree
hash* said neither (D73); several checks answer from history, from files git ignores and from variables, none of
which a tree hash holds (D73); nothing said whether the trunk, `make ci` or an adopted repository's gate may reuse
a stamp, and the constitution's MUST decides the first (D74); *recorded tool versions* named no tool, and SC-001's
second no project and no holder (D75); nothing said what a failing or interrupted run leaves, which values force,
whether a stamp ages, or where it is kept (D76); two entries differed on which full runs say a line (D77). A
generated project starts on `main`, where the second run is a full run by design: the saving is on the branch a
slice is built on. A run that writes under `specs/` between two gates — a decision, a benchmark record — moves the
key honestly, so `/cruise` reuses fewer stamps than a developer does; narrowing that was `S07`'s per-check stamps, now
in the Parking Lot (D173).

*Where a stamp may be used* below means: a generated project (no wrapped application, and its layout not moved
under `delivery/`: D78), on a branch that is not the
trunk, `HEAD` attached, no CI marker set, the run not forced.

- **AC-S03-1** — Given a tree that just passed the full gate where a stamp may be used, when `make verify` runs
  again with nothing changed, then no check starts, the run exits 0, and it prints exactly one line of its own,
  beginning `verify:`, carrying five facts: the full gate did not run; this tree already passed it; the instant of
  that pass, from the stamp, in UTC to the second; an abbreviation of the key of at least seven hexadecimal
  characters; and `VERIFY_FORCE=1` as the way to run the gate anyway. It never prints `verify: all gates passed`,
  which stays, byte for byte, the closing line of a full passing run and of nothing else. (D76)
- **AC-S03-2** — Given a stamped tree, when one character of a tracked file changes, or an untracked file git does
  not ignore appears, or a covered file is deleted, changes its executable bit, or is a link whose target changes —
  committed or not — then the full gate runs and a passing run writes a new stamp. (D73)
- **AC-S03-3** — Given the key, then it covers every tracked file and every untracked file git does not ignore by
  path, raw bytes, executable bit and a link's target, read on every run: a file rewritten with CRLF line endings
  under `* text=auto eol=lf`, and a file rewritten at the same size with its modification time restored, each run
  the full gate. The real index is never written by a run. (D73)
- **AC-S03-4** — Given a stamped tree, when an untracked file becomes tracked with the same bytes, then the full
  gate runs: the index's entries (names, modes, blob ids, stages) are in the key. (D73)
- **AC-S03-5** — Given a stamped tree, when `HEAD` names another commit, or another branch with the same files is
  checked out, or any ref under `refs/heads` or `refs/remotes` names another commit (a fetch), or the checkout's
  shallow boundary changes, then the full gate runs. (D73)
- **AC-S03-6** — Given a stamped tree, when a file under `scripts/` or the `Makefile` the gate ran from changes,
  then the stamp is invalid and the full gate runs; the gate-script hash is a named part of the key and of the
  stamp, beside the tree's. (D73)
- **AC-S03-7** — Given the files git ignores that a check reads and the gate does not rebuild from the tree — the
  code index's database and its write-ahead file, every harness projection directory the registry names, the
  installed UX-gates kit, the installed `skills/ui-ux-pro-max/`, and `.env` where a gate step reads it — then each
  is in the key by its bytes, or by the installed manifest that pins it, with absence a value: a change to one, or
  one appearing or disappearing, runs the full gate. They are one closed list beside the checks, and a test fails
  when a check script reads an ignored path that is not on it. (D73)
- **AC-S03-8** — Given an installed environment (`.venv`, `node_modules`), then it is outside the key only where the
  gate's own recipe rebuilds it from a committed lock on every run; where a backend's recipe does not, it is an
  entry of AC-S03-7's list by its installed manifest. The plan says which, per backend, from the recipe. (D73)
- **AC-S03-9** — Given the environment variables a check reads that can change its answer — at least
  `UX_GATES_REQUIRE`, `UX_GATES_SINCE`, `UX_GATES_SHARD`, `CODEGRAPH_GATE_NO_SYNC`, `SLIPWAI_NO_INSTALL`,
  `GITHUB_HEAD_REF`, `CI_COMMIT_REF_NAME` — then each is in the key by value, unset distinct from empty, and
  `UX_GATES_JOBS` is not; the same closed-list test holds them. A run that makes the gate write the tree it judges
  (`RATCHET_TIGHTEN`) neither reads nor writes a stamp. (D73)
- **AC-S03-10** — Given a full run, then a stamp is written only where every prerequisite of `verify` ran and
  exited 0: `make -i verify` on a failing tree leaves no stamp, and a run under make's dry-run, touch or question
  mode neither reads nor writes one. The key is computed before the first check and again after the last, and the
  stamp is written only where the two are equal. A stamp is never written after a failure, a skip or a reuse.
  (D73)
- **AC-S03-11** — Given a full run that passed and whose key moved during the run, or whose stamp could not be
  written, then it exits 0, prints `verify: all gates passed`, and adds one line saying the pass was not recorded
  and why: which part of the key moved and, where it is the files, that a check may have written one, that
  `git status` shows it and that the next run records (D81). A stamp never changes the gate's exit code. (D76)
- **AC-S03-12** — Given a checkout where any index entry is marked `assume-unchanged` or `skip-worktree`, or is a
  submodule, or an untracked directory is itself a repository, then no stamp is read or written, the full gate
  runs, and one line before the first check says which. (D73, D77)
- **AC-S03-13** — Given no git on `PATH`, a directory that is no repository, or a git that fails, then the full
  gate runs, no stamp is read or written, and one line before the first check carries git's reason; given a
  covered file that cannot be read, the same, the line naming the file. The run never fails for that reason alone
  and never passes on less. Where git cannot answer, a stamp that stood before is left where it is, since its place
  cannot be asked; it is for a key that passed, and only a later run with git answering can match it. (D73, D76,
  D77, D79)
- **AC-S03-14** — Given the key's tool versions, then they are those of every tool the machine supplies that a
  recipe of the gate launches and no committed file pins (D81) — `node` and `npm` too wherever the gate has the
  model's checks, and a test over the generated recipes of every shape fails when a recipe launches a command that
  is neither on the project's tool list, a file of the project, nor named with the reason it is pinned: `make`, `git` and the `python3` on `PATH` in every project; `uv` for a Python backend;
  `node` and `npm` for a TypeScript backend or any project with a frontend; `go` for Go; `java` for both Java
  backends — the JVM the wrapper would run: `JAVA_HOME`'s where that variable is non-empty, else the one on `PATH`;
  the variable's value is never in the key (D81). A project with several backends takes the union, each tool asked once per run. The set is one table
  beside `BACKEND_TOOLING` in `src/slipwai/backends.py`, and a test fails when a backend there has no row. (D75)
- **AC-S03-15** — Given a tool in the set, then it is launched once with its version argument on every run that
  would read or write a stamp, and the key takes everything it prints in answer, on both streams (D80): a changed byte from
  any one tool — on a second line behind a notice included — runs the full gate and a passing run writes a new stamp;
  the stamp shows the first non-empty line. No path, size or modification time of an
  executable is in the key or the stamp. (D75, D80)
- **AC-S03-16** — Given a tool a committed lock pins (ruff, mypy, pytest, everything under `package-lock.json`,
  the Maven wrapper's pin), then it is never asked: a new ruff version is a changed `uv.lock` or `pyproject.toml`,
  which AC-S03-2 holds. A Python service's interpreter is the one thing read from its environment, from
  `.venv/pyvenv.cfg` without a launch, and a changed version there runs the full gate. (D75)
- **AC-S03-17** — Given a tool that is not on `PATH`, exits non-zero, prints nothing or does not answer within a
  fixed timeout, or a `pyvenv.cfg` AC-S03-16 names that is missing or unreadable, then no stamp is read, the full
  gate runs, one line before the first check names the tool or the file, and that run writes no stamp even if it
  passes — so the first gate of a fresh clone, which has no environment yet, records nothing and the second does.
  The run never fails for this reason alone. (D75, D76, D77)
- **AC-S03-18** — Given a stamp, then it holds the entity's five fields — the tree's hash, the gate-script hash,
  each tool's name with the line it reported, the instant of the pass, and the result, which is only ever a pass —
  as plain text a person can read; of a tool's answer it stores the tool's name, the version-shaped words of the
  answer (digits and dots with a short suffix, nothing else) and a digest of the whole answer, never a path, a host
  name or any other word of the tool's (D81); one that cannot be parsed or lacks any of the five is no stamp. (D75, D76)
- **AC-S03-19** — Given a reuse run, then the only processes it starts are git's and the version questions of
  AC-S03-14: no sync, no check script, no linter, type checker or test runner. The suite holds this with stand-in
  executables written in the test tree and put on `PATH`, each recording its calls, and holds no clock. (D75)
- **AC-S03-20** — Given SC-001, then its second is the wall time of the whole `make verify` as a developer types
  it, on a project generated with the Python backend, no frontend and target `none`, on a branch other than the
  trunk with no CI marker, the tree just passed and unchanged. It is measured at the demo and written into the
  slice's quickstart with the command, the machine and the number; one second or more is a failed demo, not a
  revised number. Other backends carry the mechanism and no time claim, and the quickstart names the Java backends
  as the residual. (D75)
- **AC-S03-21** — Given any of `CI`, `GITHUB_ACTIONS` or `GITLAB_CI` non-empty (`CI=false` included), or the
  checked-out branch being the trunk as D30 and D33 resolve it, or a detached `HEAD`, then the run reads no stamp,
  runs every prerequisite of `verify`, writes no stamp, leaves any stamp file there untouched, and prints what it
  prints today and nothing more. (D74, D77)
- **AC-S03-22** — Given any other branch — `slice/<id>`, a topic branch, a long-lived branch that is not the trunk
  — then a stamp is read and written under these criteria. (D74)
- **AC-S03-23** — Given `make ci` on a stamped tree, on any branch, then every prerequisite of `verify` runs: it
  is a forced run, says so in the forced line, and writes what a forced pass writes where AC-S03-21 does not
  apply. (D74, D77)
- **AC-S03-24** — Given a project with a wrapped application, or one whose delivery material sits under `delivery/`
  (the gate of a repository that adopted the method; D78),
  then its `verify` rule neither reads nor writes a stamp and two consecutive runs both run every prerequisite;
  the refusal that stands in for the gate while nothing is confirmed is unchanged. (D74, D78)
- **AC-S03-25** — Given `VERIFY_FORCE`, then unset, empty or `0` does not force and any other value does, read
  from the make command line or the environment. A forced run reads no stamp, runs every check, prints one line
  before the first check naming `VERIFY_FORCE` and its value, and on passing writes a stamp like any other full
  pass. The page a project gets about the gate carries its default (unset) and one sentence on when to set it.
  (D76)
- **AC-S03-26** — Given a full run where a stamp may be used, or a forced one, then the project's stamp is
  removed before the first check starts and written only after the last check passed: after a run that failed,
  was interrupted or was killed, no stamp exists for any key. Where the stamp cannot be removed, one line names
  the file to delete and the run writes no stamp. A run under make's ignore-errors mode removes the stamp too and
  writes none; a stamp that stood is left in three cases only, each for a key every check passed on: AC-S03-13's git that
  cannot answer, a run where the trunk cannot be resolved for a reason that is not git's, and a run with no
  `python3` on `PATH` able to run the stamp script (D79, D81). A run that both tightens the ratchet and ignores
  errors touches nothing: the ratchet rule is asked first. (D76, D79, D80, D81)
- **AC-S03-27** — Given a stamp of any age, then it is reused where the key matches: its instant is shown, never
  compared, and there is no setting. Deleting the stamp is always safe and has the effect of forcing. (D76)
- **AC-S03-28** — Given a run that writes a stamp, then the file is in a directory of the factory's own under the
  directory `git rev-parse --git-dir` answers for this checkout — never a file git owns, never in the working
  tree — and `git status` reports nothing the stamp left; no ignore line is added. There is one stamp per project
  per worktree, the last passing key, replaced by the rename of a complete file; two projects in one repository
  (D36) never read each other's; worktrees of one repository never share one. A stamp path that is not a regular
  file is removed as itself, never read or written through. (D76)
- **AC-S03-29** — Given a full run, then every check that ran before this slice runs and the run ends `verify: all
  gates passed`. Without `-j` the checks run in the order they had among themselves, `check-python` first, each
  printing what it printed. What `S04-parallel-gate` changes, and nothing else: each toolchain's sync or install
  runs once, after `check-python` and ahead of the checks that need it, where it ran inside each of them; and
  `check-drawio` prints a line saying it skipped its install where it did. Under `make -j verify` the same checks
  run, in any order after `check-python` and the syncs, and the closing line is still the last line of a passing
  run (*amended by D89*): the per-transport `verify: check-openapi` line still gates and
  is still cut out with its transport by `./init`, a project with several services or language families has one
  gate and one stamp, the recipe gives a GNU Make 3.81 nothing it does not document, the one newer option, output grouping, being passed only to a make that lists it among its features (*amended by D89*; read, not run: an assumption, D81), and every starter combination `make starters`
  materialises passes its own gate. (constitution I; D74)
- **AC-S03-30** — Given a project generated before this release, then the change asks nothing of it: `slipwai
  migrate` brings the new `Makefile`, the first `make verify` runs in full, and its `.gitignore` is not touched — with one exception the fragment's
  catch-up states: a repository whose trunk is named neither `main` nor `master` and whose `project.json` records
  no `ci.branch` records it, so that its trunk always runs the full gate (D81).
  The `changelog.d/` fragment says so and claims MINOR; `VERSION` is already `1.6.0.dev0`. (D76)
- **AC-S03-31** — Given the page that describes the gate, then it says what a stamp cannot see: what a project's
  own tests or tools read from outside the repository — the clock, the network, user-level tool configuration,
  `PATH`, a variable no gate script names — so a gate that would now fail for one of those alone is reused as
  green until a file, a ref or a listed input moves or `VERIFY_FORCE` is given, and CI and the trunk, which never
  read a stamp, are where it is caught. The page also says when to force (a check answers from one of those
  things), how the trunk is recognised (the branch `project.json` records as `ci.branch`, else `main`, else
  `master`) and what a team with another trunk name does (record `ci.branch`; until then that branch reuses a
  stamp like any other); it says *non-empty* of a CI marker and never *everything the checks answer from*.
  (D73, D81)

Added after the demo by the adversary pass (D83); each is held by a test, and where one differs from a criterion above, it
holds:

- **AC-S03-32** — Given the key, then it covers every file under the project's directory — tracked, untracked or
  ignored, whatever makes git ignore it — by AC-S03-3's record, except what matches a closed exempt list beside the
  checks, each entry with its reason: the gate's own recipe rebuilds it from a committed lock on every run; it is a
  cache or an output no check reads as an input; or it is a record the gate or the runner writes about itself. An
  entry may name exceptions that stay in the key (`node_modules` apart from its installed manifest, `.codegraph/`
  apart from the database and its write-ahead file). An ignored directory nobody listed is hashed whole; one that is
  itself a repository is AC-S03-12's case. The closed-list test holds that every ignore line the factory generates,
  for every shape, is covered or exempt with a reason, and that no check script reads under an exempt entry outside
  its exceptions. An ignored scratch test that does not compile, and a module ignored through `.git/info/exclude`
  that breaks `check-imports`, each run the full gate. This replaces AC-S03-7's list and AC-S03-8. (A1)
- **AC-S03-33** — Given a project in a subdirectory of its repository, then the tracked files, the untracked files git
  does not ignore, the index's entries and AC-S03-12's refusals are taken for the whole repository; ignored files
  are covered under the project's directory only; the stamp stays one per project. A sibling's uncommitted edit on a
  `slice/<id>` branch runs the full gate. (A2, T022)
- **AC-S03-34** — Given the key, then every ref git lists is in it with what it names, tags and replace refs
  included, and so are the bytes of the repository's own configuration file and of the worktree's where there is
  one, absence a value. User-level and system git configuration stay unseen, and the page says so. (A3, A4)
- **AC-S03-35** — Given a run, then its note carries a token only that run's two halves share, stored as a random
  value or a digest and never a process id, host or path; `record` writes nothing where the note's token is not its
  own or it was given none, and says one line. Two runs at once in one worktree, the second on an edited tree that
  fails or is interrupted, leave no stamp for the edited tree; `record` typed by hand after a failed run writes
  nothing. (B1, B2)
- **AC-S03-36** — Given git's answer for a path, then it loses exactly one trailing line feed and nothing else: a git
  directory or a project directory whose name begins or ends in whitespace has its own stamp, inside its own git
  directory. An empty directory at the note's path is removed as itself and a full one is named as the directory to
  delete; a file where the factory's directory should be is named as that file. A stamp whose instant is not exactly
  the UTC-to-the-second shape the reuse line prints is no stamp. Git's reason on a line is its first non-empty line,
  escaped. (B3, B4, B5, B6, C6)
- **AC-S03-37** — Given a `HEAD` that names no commit, or that is a symbolic ref outside `refs/heads`, then the run
  reads, writes and removes no stamp and says nothing. Given a `HEAD` that names a commit where the name the trunk
  resolves to has no ref, or where `project.json` is missing, unreadable or not an object, or records a `ci.branch`
  the trunk the gate resolves is not, then the run cannot tell which branch is the trunk: it reads, writes and
  removes no stamp, and one line before the first check names what to fix (record `ci.branch`, or fetch the trunk).
  A `ci.branch` simply not recorded, with `main` or `master` present, stamps as before (D81). The questions are
  asked in this order: a CI marker, the `HEAD` cases (silent), cannot tell (the line), the trunk (silent). (C1, C4,
  C5)
- **AC-S03-38** — Given `make ci`, by any route — a goal, a prerequisite of another target, any `MAKECMDGOALS` — then
  every check runs, no stamp is read, written or removed, and no stamp line is printed: in a stamped project `ci`
  depends on the checks' own target, not on `verify`. This replaces AC-S03-23. (C3)
- **AC-S03-39** — Given a make whose path holds a space, then the gate runs, records and reuses. Given `make -f
  <file> verify` in a project with no file named `Makefile`, then the gate runs and records: the checks are run
  from the makefile the gate ran from. (C2, C8)
- **AC-S03-40** — Given a project whose gate is not stamped (a wrapped application, or the delivery material under
  `delivery/`), then its gates page says nothing of a stamp or `VERIFY_FORCE` and is byte for byte what it was
  before the slice. (C7)
- **AC-S03-41** — Given the page and the fragment, then each says that a pipeline which sets none of `CI`,
  `GITHUB_ACTIONS` or `GITLAB_CI` sets `CI=1` itself, that `make ci` records nothing, and that a `ci.branch` the
  gate cannot use is said on a line; the page names git's user-level configuration and a file edited by hand inside
  an installed dependency tree among what a stamp cannot see. Still MINOR. (D83 items 1, 3, 14)
- **AC-S03-42** — Given SC-001 after these changes, then it is measured again on AC-S03-20's project and the number
  replaces the one in the quickstart; one second or more is a failed demo. (D83 item 1)

### S24-ci-fetches-slice-base

**Gaps reviewed** 2026-10-04, cruise iteration 12, host (resumed from the note iteration 8 left open; the owner
answered D54 with its option (a), D82; D84 records what the standing decisions make of it): the three examples in
`story-split.md` against `workflow()` in `src/slipwai/project/ci_workflows.py`, `delivery_workflow()` and
`gitlab_job()` in `src/slipwai/project/adopted_ci.py`, and `forge_checkout()`, `not_checked()` and `check()` in
`assets/toolkit/scripts/check-slice-scope.py`. Found and written back: which jobs fetch and in what words, and
which do not (D54; AC-S24-1 to AC-S24-3); the first example had no checkout it could be shown on without a forge
(AC-S24-4); which no-base answers become failures in a forge's checkout, what the line says where the CI is neither
GitHub nor GitLab, and which answer keeps its exit 0 (D31, D32, D35; AC-S24-5 to AC-S24-7); the third example,
*every answer is today's*, was untrue under any fetch and is rewritten as the owner approved it (D54, D82;
AC-S24-8); a developer's checkout had no measurement (AC-S24-9); what `migrate` does with a workflow the project
took over, and what a maintainer reads afterwards (AC-S24-10, AC-S24-11); the suites and the words that still say
CI does not check (AC-S24-12, AC-S24-13). Swept for the same consequence — a check in the `verify` job whose answer
changes once history is there — over every script under `assets/toolkit/scripts/` and `assets/targets/*/scripts/`
that asks git for a merge base or a ref: `check-migrations.py` and both `check-flags.py` (D54, approved in D82), and
no other. `check-codegraph.py` runs whole under a CI marker whatever the history (D46), a verify stamp is never read
in CI (D74), and `check-ux-gates.py` reads history only under `UX_GATES_SINCE`, in a workflow of its own that
already fetches it. Not run here, and said so in the plan with the page it was read from: what a real forge's
runner leaves in the checkout — this run pushes nothing (D12), so the checkout is built with git in the shape the
forge's documentation gives.

Unless a criterion says otherwise, *a forge's checkout* is one by either of D31's and D32's routes (the branch name
in `GITHUB_HEAD_REF` or `CI_COMMIT_REF_NAME` with `HEAD` detached, or `CI`, `GITHUB_ACTIONS` or `GITLAB_CI`
non-empty), the trunk is `main`, and the branch is `slice/S1`.

- **AC-S24-1** — Given a project `slipwai generate` wrote, of any backend and target, then the `verify` job of
  `.github/workflows/verify.yml` checks out with `actions/checkout@v6` and `fetch-depth: 0`, written
  unconditionally — no expression, the same on `push` and on `pull_request` — with a comment saying which checks
  need the history; and every other job in that file (the integration jobs and their `CONTAINER_CHECKOUT`) and every
  other generated workflow (the event model's, the deploy workflows, the `ux-gates` extension's) is what it was,
  byte for byte (D54, D82).
- **AC-S24-2** — Given a repository `slipwai adopt` wrote a GitHub workflow for, then the `verify` job of
  `verify-delivery.yml` carries the same key the same way, and its `smoke` job is unchanged.
- **AC-S24-3** — Given a repository `slipwai adopt` wrote a GitLab job for, then `verify-delivery` carries
  `variables:` with `GIT_DEPTH: "0"`, `smoke-delivery` is unchanged, and no `rules:` is added: when the job runs is
  still the repository's own configuration's to say.
- **AC-S24-4** — *The first example.* Given a checkout in the shape the forge makes with that key for a pull
  request from `slice/S1` — full history, every branch under `refs/remotes/origin/`, `HEAD` detached on the pull
  request's merge commit, the branch name in `GITHUB_HEAD_REF` and the target in `GITHUB_BASE_REF` (on GitLab
  `CI_COMMIT_REF_NAME` and `CI_MERGE_REQUEST_TARGET_BRANCH_NAME`), the CI markers set — and a host-surface change in
  the slice's commits, when `check-slice-scope` runs, then it exits 1 naming the path, *compared with `main` at*
  the commit; and the same checkout of a slice that stays inside its scope passes with that *compared with* line.
  This is AC-S22-23's rule on the checkout the workflow now makes.
- **AC-S24-5** — *The second example.* Given a `slice/<id>` branch in a forge's checkout with no usable base —
  no trunk ref; a trunk ref with no common ancestor at this depth; an unrelated trunk; a pull-request target with
  no history in common — when the check runs, then it exits 1 with nothing on stdout and one line on stderr that
  says the slice was NOT checked, names the trunk, and says what the job's checkout needs: `fetch-depth: 0`, on
  GitLab `GIT_DEPTH: "0"`, and on any other CI a full clone with the trunk's branch fetched. The line carries no
  `git fetch` command and no *nothing to hold*, and it keeps the words about a recorded name that was passed over
  (AC-S22-28, AC-S22-32). A lost record at a canonical slot is still printed beside it. This replaces the exit 0 of
  AC-S22-22 and of D31's answer 3, on both routes, as D31 and D32 said it would once a person approved.
- **AC-S24-6** — Given a base and a comparison git could not run (AC-S22-31) in a forge's checkout, then the check
  exits 1 with the *NOT checked — git could not compare* line it prints today; it took its exit 0 from the two
  answers above (D35) and follows them.
- **AC-S24-7** — What does not change in a forge's checkout: where git cannot read the checkout at all, the check
  says so and exits 0 (D35: whether that fails in CI is a person's, and nobody has said); a branch that is not
  `slice/<id>`, or a detached `HEAD` no variable names, answers *nothing to hold*, exit 0, with history or without;
  with a usable base the slice is held exactly as on a developer's machine.
- **AC-S24-8** — *The third example, rewritten (D54, D82).* Given a pull request from a branch that is not
  `slice/<id>`, in the checkout of AC-S24-4, then `check-slice-scope`'s answer is today's, and `check-migrations`
  and `check-flags` (aws and azure) answer as they do on a developer's full clone: a contracting migration whose
  `contract:` names an expand added in the same pull request is refused, and so is a flag declared in the pull
  request and seeded anything but `off`; the same change at depth 1 with no trunk ref passes both, as it did before
  the slice; and a push to the trunk passes both at either depth. None of the three scripts changes by a byte: the
  slice gives them the history, and tests that run the shipped scripts on those checkouts hold what they then say.
  **Reading (D86).** The above is under this section's default, a trunk named `main`; it holds the same for
  `master`. `check-migrations` and `check-flags` find their base by those two names and do not read `ci.branch`. In
  a repository whose trunk has another name: where neither branch exists, they have no base in CI and pass, with
  history or without; where one exists, they compare with it in CI as on a developer's full clone, so a push to the
  trunk and every pull request are refused for an expand and its contract both landed since that branch, and pass
  at depth 1. That is the developer's machine's answer, not a new one. The fragment says so and what to do, and a
  test runs the shipped `check-migrations.py` on both repositories and holds those answers. Reading the recorded
  trunk is `S31-gates-read-recorded-trunk`.
  **And (D87; adversary B1, B2).** Two more cases answer in CI as on a developer's full clone, and are refused: a
  pull request that targets a branch other than the trunk is compared with the trunk all the same, so a contract
  is refused there although its expand reached that branch in an earlier pull request; and where CI checks out the
  branch's own tip and not its merge with the trunk, a branch whose expand landed by squash and which carries on
  with the contract is refused until it merges the trunk. The fragment's catch-up says both and what clears each, a
  hold test for each is in `tests/test_ci_history_gates.py`, and both are `S31-gates-read-recorded-trunk`'s to
  weigh at its gaps stage.
- **AC-S24-9** — Given a developer's checkout (no CI marker, and no branch-name variable with a detached `HEAD`),
  then every exit code and every line of `check-slice-scope` is what it was before the slice — except the printed
  fetch, which names the branch in full (AC-S24-16; D87).
- **AC-S24-10** — Given a project made by the factory before this change, when `slipwai migrate` runs, then each of
  the three files is carried forward or left alone exactly as `migrate` treats a file of its kind today — the slice
  changes nothing about what `migrate` owns — and the catch-up paragraph of the fragment is true to that: followed
  as written on a project whose workflow `migrate` did not rewrite, it ends with the key in the job and the slice
  held.
- **AC-S24-11** — Given the slice's diff, then it carries one fragment under `changelog.d/` claiming PATCH with
  `VERSION` unchanged (D54), which says: CI's `verify` job now fetches full history; a slice pull request is held to
  its scope in CI; *NOT checked* in CI is now a failure; and, plainly, that `check-migrations` and `check-flags` now
  hold their *new in this change* rules in CI on every pull request, naming both refusals, so a maintainer who sees
  a red pull request after `slipwai migrate` knows why (D82). Its catch-up paragraph says a workflow the project
  took over, and a pipeline of the project's own that sets a CI marker on a shallow clone, are not rewritten by
  `migrate` and turn red on a slice branch until the job fetches history, with the key to add; that an open pull
  request carrying either pattern goes red and is fixed by landing the expand first or seeding `off`; and that a
  repository with a long history pays the full fetch on that one job. The unreleased `changelog.d/slice-scope-base.md`
  no longer says a CI run with nothing to compare with exits 0, so the release's entry does not say both.
- **AC-S24-12** — Given the words that describe the old answer — the docstring of `check-slice-scope.py`, and any
  page or message under `assets/`, `src/slipwai/` or `docs/` that says a CI checkout is depth 1, that the slice is
  not checked there, or that a maintainer adds the key by hand — then each says what is now true; the docstrings of
  `check-migrations.py` and `check-flags.py` stand, since what they say of a shallow checkout is still so of one.
- **AC-S24-13** — Given the factory's suite run with `CI=true GITHUB_ACTIONS=true` in its environment, then it is
  green: the suites that asserted *NOT checked*, exit 0, under a CI marker (`tests/test_slice_scope_no_base.py`,
  `tests/test_slice_scope_hostile_base.py`, and any other the sweep finds) assert the failure, and every test of a
  developer's answer still clears the markers (AC-S22-24).
- **AC-S24-14** — *Added by D87 (adversary F1).* Given the checkout of AC-S24-4, where the slice's commits record
  `ci.branch: evil` and edit `Makefile`, merge an orphan root commit carrying the slice's own tree, and that root is
  pushed as branch `evil`, with `GITHUB_BASE_REF=main` (and the same on GitLab's two variables), when
  `check-slice-scope` runs, then it exits 1 naming `Makefile` and `project.json`, compared with `main` at the commit
  where the branch left `main`, in the words it uses where the pull request's target won; the same refs on a slice
  that stays inside its scope pass with that line; and in every pull-request checkout with a usable target that has
  a base, the commit compared with is the target's base or an ancestor of it — where the two bases share no
  history, the target's.
- **AC-S24-15** — *Added by D87 (adversary F4).* Given a forge's checkout with no usable base, then the NOT-checked
  line names the two refs it looked for, `refs/heads/<trunk>` and `refs/remotes/origin/<trunk>`, and its last clause
  reads *on any other CI, a full clone with the trunk's branch fetched from a remote named `origin`*; given a
  full-history checkout whose only remote is `upstream`, the line is that one, exit 1; no base selection changes and
  no other remote is read (D30: only the two full names answer).
- **AC-S24-16** — *Added by D87 (adversary F3).* Given any line in which the gate prints a fetch, then the command
  is `git fetch origin refs/heads/<name>:refs/remotes/origin/<name>`; given a remote with a branch `main` and a tag
  `main` at the slice's head, when the printed command is run and the gate re-run, then the slice is compared with
  the branch, not the tag.

### S04-parallel-gate

**Gaps reviewed** 2026-10-04, cruise iteration 13, host with `drive-skipper` for D88 to D91 and the host's own
D92: the three examples in `story-split.md` against `stamped_gate()` in `src/slipwai/project/gate.py`, `makefile()`
in `src/slipwai/project/makefile.py`, the model targets in `src/slipwai/project/model_targets.py`, `GATE` in
`src/slipwai/project/adopted_targets.py` and each backend's `scripts/verify` under `src/slipwai/project/languages/`.
Run on a project generated for the purpose (event-modelling profile, Python backend, a browser app; GNU Make 4.4.1):
warm, the serial gate took 6.2 s and `make -j verify` 3.2 s, three times, each exit 0 with the serial run's 106
lines in another order and one test-progress line cut in two by another check's output. Found and written back:
FR-002's *writers `.NOTPARALLEL` locally* names a directive that keeps no target from running beside another on
any GNU Make — before 4.4 it serialises the whole makefile, from 4.4 the named target's own prerequisites (make's
NEWS, and a run here) — so the requirement is re-worded to what is held, a writer ordered ahead as a prerequisite,
and the writers are named (D88); `check-python` is *Fail, first* and is not first under `-j` (D88); an adopted
repository's gate runs commands nobody here can call read-only, three of them through one `baseline.json` (D88);
nothing said who gets the parallel gate, what a parallel run prints, what a failed one ends on, or what is measured
(D89); FR-003's *once per invocation* was already true of one call of the script, and the cost is three calls per
gate, each syncing, under `-j` at one moment on one `.venv` (D90); the third example's *committed lockfile* does
not exist — a generated project ships the model tooling's `package.json` alone, and the first gate writes an
untracked lock beside it, which is also why a first stamped pass is not recorded (D91); the split of
`verify-stamp.py` the Parking Lot handed this slice is another capability and becomes `S32-verify-stamp-split`
(D91). No target of the gate was found writing under `.specify/`. Not run here, and said so in the plan: GNU Make
3.81 and 4.3 (none on this machine); the TypeScript, Go and Java gates under `-j` before the plan's own runs;
Windows under Git Bash, which the matrix tests hold before release (Edge Cases).

Unless a criterion says otherwise, the project is one the factory generated (no wrapped application, its layout not
moved), *a full run* is one in which no stamp is reused, *serial* is `make verify` with no `-j` and no `MAKEFLAGS`,
and *a stand-in* is an executable written in the test tree and put first on `PATH`, which records when it was
started with what and exits as the test says — a fake, never a mocking framework.

**The parallel run (FR-002; D88, D89, D92)**

- **AC-S04-1** — *Re-worded by D96.* Given a generated project of each backend family's shape (Python, TypeScript,
  Go, Java, and a project with two families), when a serial full run completes, then no two checks ran at the same
  time, and the checks started in the order the gate's list gives them, `check-python` first, `lint` before
  `typecheck` before `test`; the order is compared as it happened, not sorted (AC-S03-29 as amended).
- **AC-S04-2** — Given a tree the serial run passes, when `make -j verify` runs in full, then the set of check
  commands started equals the set the serial run of the same Makefile starts on the same tree.
- **AC-S04-3** — Given that run, then it exits 0 and its last line is `verify: all gates passed`.
- **AC-S04-4** — Given `make -j verify` in full on a tree the serial run passes, then at least two checks are
  running at the same moment (held with stand-ins, no clock).
- **AC-S04-5** — Given a Python project with a browser app, freshly generated, with no `.venv` and no
  `node_modules`, when `make -j verify` runs with the real toolchain, then it exits 0 and ends `verify: all gates
  passed`.
- **AC-S04-6** — Given a tree on which one check fails, when `make -j verify` runs, then it exits non-zero and
  prints no `verify: all gates passed`.
- **AC-S04-7** — Given that failed run, then no stamp exists afterwards.
- **AC-S04-8** — Given a tree on which two checks that both start fail, when `make -j verify` runs, then each is
  named on a line of make's own carrying `***` and the check's target name, as the running make prints it (D92).
- **AC-S04-9** — Given a run that did not pass, with `-j` or without, then the last line of the gate's own begins
  `verify:`, says the gate did not pass, and says the failed checks are named above on the lines carrying `***`.
- **AC-S04-10** — Given a make that lists `output-sync` among its features, when `make -j verify` runs, then each
  check's output lines are contiguous, with no other check's line between them.
- **AC-S04-11** — Given a make that does not list `output-sync`, when `make -j verify` runs, then the option is not
  passed to it and the run completes (read on 3.81, not run: the guard is held by a test that reads the recipe).
- **AC-S04-12** — Given a serial run on a make that lists `output-sync`, then a check's lines appear as the check
  produces them, not held until it ends.
- **AC-S04-13** — Given a `python3` on `PATH` older than 3.10, when `make verify` or `make -j verify` runs, then
  `check-python`'s line is printed, no sync and no other check has started, and the exit code is non-zero.
- **AC-S04-14** — Given a Python project with an HTTP transport and no `.venv`, when `make -j check-openapi lint`
  runs, then the sync has finished before either starts and both pass.
- **AC-S04-15** — Given a project with a Java service, when `make -j verify` runs, then no two Maven runs over one
  service's `target/` overlap, and the gate's verdict equals the serial run's.
- **AC-S04-16** — Given the Makefile of every starter combination `make starters` materialises, when it is read,
  then it contains no `.WAIT` and no `.NOTPARALLEL` with a prerequisite, every order the gate relies on is a
  prerequisite, and the one construct newer than GNU Make 3.81 documents is output grouping, named only behind a
  test of the running make's own feature list (D92).
- **AC-S04-17** — Given one starter of each backend family, freshly materialised, with its real toolchain where
  this machine has it, when `make -j verify` runs, then it passes with the checks and verdicts of its serial run;
  the plan and the fragment say which families were run and which only read.
- **AC-S04-18** — Given a generated project, when `make -j verify` runs in full, then every file under `.specify/`
  has the bytes it had before.
- **AC-S04-19** — Given a tree that passed under `make -j verify`, on a branch other than the trunk with no CI
  marker, when `make verify` runs with no change, then it reuses the stamp.
- **AC-S04-20** — Given a tree that passed under `make verify`, on such a branch, when `make -j verify` runs with
  no change, then it reuses the stamp.
- **AC-S04-21** — Given the generated CI workflow and the ladder's commands after this slice, then the gate
  command each types is `make verify`, unchanged (D89; whether the ladder types `-j` is `S06-scoped-gate`'s).
- **AC-S04-22** — Given AC-S03-20's project, warm, on a branch other than the trunk with no CI marker, when
  `VERIFY_FORCE=1 make verify` and `VERIFY_FORCE=1 make -j verify` are each run three times at the demo, then the
  median under `-j` is lower than the serial median; otherwise the demo failed and the criterion is not revised.
- **AC-S04-23** — Given that demo, then both sets of numbers are written into the slice's quickstart and the
  fragment with the command, the machine and its core count.

**An adopted repository's gate (D88; experimental as `AGENTS.md` defines the word)**

- **AC-S04-24** — *Re-worded by D95.* Given a repository that adopted the method (a wrapped application, the
  refusal while nothing is confirmed, or the delivery material moved), when its generated delivery Makefile is
  read, then it carries a bare `.NOTPARALLEL:` with no prerequisites exactly once, after the `verify` rule, inside
  a conditional that is true only when no other makefile has been read, written with nothing GNU Make 3.81 lacks,
  under a comment that says the gate is serial when make is started on this file and that a Makefile which
  includes it keeps its own `-j`.
- **AC-S04-25** — Given a generated project with no wrapped application and no moved layout, when its Makefile is
  read, then it carries no `.NOTPARALLEL`.
- **AC-S04-26** — *Re-worded by D95.* Given an adopted repository whose recorded `lint`, `typecheck` and `test`
  are stand-ins, when the gate is started on the delivery Makefile under `-j` (the path spelled relative, with a
  leading `./`, or absolute), then no two of them overlap and they run in the serial gate's order.
- **AC-S04-27** — *Re-worded by D95.* Given an adopted repository with no baseline yet, when the gate is started
  on the delivery Makefile under `-j`, then `baseline.json` holds the entries a serial first run records.

**One sync per run (FR-003; D90)** — a stand-in `uv` logs its arguments; a *sync line* is one whose first argument
is `sync`, a *run line* one whose first is `run`.

- **AC-S04-28** — Given a Python project with one service, when `make verify` runs in full, then the log holds
  exactly one sync line for that service's `--project`.
- **AC-S04-29** — Given the same project, when `make -j verify` runs in full, then the log holds exactly one sync
  line per service, and every sync line precedes the first run line.
- **AC-S04-30** — Given a Python project with two services, when `make verify` runs in full, then the log holds
  exactly two sync lines, one per service's `--project`.
- **AC-S04-31** — Given the one-service project, when `make lint test` runs as one command, then the log holds
  exactly one sync line.
- **AC-S04-32** — Given the one-service project, when `make lint`, `make typecheck` or `make test` runs alone, then
  the log holds exactly one sync line, before the first run line.
- **AC-S04-33** — Given the one-service project, when `./scripts/verify` is run directly — with `--lint-only`,
  `--typecheck-only`, `--test-only`, or no argument — then the log holds exactly one sync line, before the first
  run line: a mode reached any way but the Makefile's own recipes syncs first, as today.
- **AC-S04-34** — Given the one-service project, when `make ci` runs with its database targets, then the log holds
  exactly one sync line.
- **AC-S04-35** — Given a Python project with Postgres, when `make migrate` runs, then the log holds exactly one
  sync line, before the migration's run line.
- **AC-S04-36** — Given a Python project with an HTTP transport, when `make dev` runs against the stand-in, then
  the log holds exactly one sync line, before the service's run line.
- **AC-S04-37** — Given the one-service project, when `make install test` runs as one command, then the log holds
  exactly one sync line.
- **AC-S04-38** — Given a stand-in `uv` whose `sync` exits non-zero, when `make verify` or `make -j verify` runs,
  then make exits non-zero and the log holds no run line.
- **AC-S04-39** — *Re-worded by D98.* Given a generated Python project, when its CI workflow, the commands
  `native_commands.py` records for it and its pages are read, then none names the non-syncing spelling as a thing
  to type: it is an argument only the Makefile's recipes pass, and the gate's page names it once, in the sentence
  that says so (D97).
- **AC-S04-40** — Given the non-syncing argument absent and any environment variable set to any value, when
  `./scripts/verify --test-only` runs, then it still syncs first: the script reads no variable to skip the sync.
- **AC-S04-41** — Given a generated Python project, when `make verify` runs, then the script prints nothing about
  the sync it did not print before; the one new line is make's echo of the sync target's recipe, once.
- **AC-S04-42** — Given a generated TypeScript project, when its Makefile is read, then every gate target reaches
  `npm ci` only through the file target `node_modules/.package-lock.json` (holds already; pinned, not changed).
- **AC-S04-43** — Given a generated Go or Java project, when its gate targets `lint`, `typecheck` and `test` are
  read, then none carries a dependency-install step: FR-003's sync is a step that builds a service's environment
  from its committed lock before a mode runs, and it is not applicable there (D90).
- **AC-S04-44** — Given `make verify lint` on a Python project, when the gate runs in full, then the log holds at
  most two sync lines per service: two make processes, as D83 left `lint` running twice there — more, never less.

**The model tooling's install (FR-003; D91)**

- **AC-S04-45** — Given a newly generated project with the event profile, when its tree is listed, then
  `scripts/event-model/package-lock.json` is a tracked file whose root entry names exactly the dependencies and
  versions `scripts/event-model/package.json` pins.
- **AC-S04-46** — Given the shipped lock, when it is read, then its `lockfileVersion` is 3, every `resolved`
  address begins `https://registry.npmjs.org/`, and it lists a package for every platform esbuild publishes one
  for. It is made by npm against that registry, never by hand; where the registry cannot be reached when it is
  made, the slice parks on that (D91).
- **AC-S04-47** — Given a fresh clone of a generated event-profile project, when `make check-drawio` runs, then
  the model tooling is installed with `npm ci` and `git status --porcelain` is empty afterwards.
- **AC-S04-48** — *Re-worded by D96 and D97.* Given an installed `scripts/event-model/node_modules` whose marker
  `scripts/event-model/node_modules/.installed` is newer than both manifests, when `make check-drawio` runs, then
  no npm command runs and the output carries the line `check-drawio: scripts/event-model/package-lock.json is not newer than the installed model tooling; not reinstalled`. The marker is a file only the install recipe writes,
  after a successful `npm ci`.
- **AC-S04-49** — *Re-worded by D96.* Given that installed tree, when `scripts/event-model/package-lock.json` or
  `scripts/event-model/package.json` is modified and `make check-drawio` runs, then `npm ci` runs again and the
  skip line is not printed — whether the file was changed by an editor, a checkout or npm itself.
- **AC-S04-50** — Given a `scripts/event-model/package.json` that disagrees with the committed lock, when `make
  check-drawio` runs, then it exits non-zero with npm's refusal and no tracked file is changed.
- **AC-S04-51** — Given an installed tree that matches, when `make model`, `make model-drawio` or `make
  model-drawio-test` runs, then no npm install runs for the model tooling and no skip line is printed.
- **AC-S04-52** — Given a fresh clone, when two or more of the four model targets are goals of one `make -j`
  invocation, then `npm ci` for the model tooling runs once and finishes before any of them starts.
- **AC-S04-53** — Given a generated Makefile with the event profile, when it is read, then `npm` is spelled for
  `scripts/event-model` in exactly one recipe and that recipe is `npm ci`.
- **AC-S04-54** — *Re-worded by D93.* Given a fresh clone of a generated event-profile project on a branch that is
  not the trunk, on which `make install` has completed, when `make verify` passes for the first time, then no npm
  command runs for the model tooling during it, the pass is recorded, and the next `make verify` on the unchanged
  tree prints the reuse line.
- **AC-S04-55** — Given the skip line of AC-S04-48, then it is said only where it is true in that make invocation,
  by a mechanism GNU Make 3.81 has; where the plan finds none, the line is said only where it can be said
  truthfully and this criterion and the example are re-worded — a line that could be wrong is not shipped (D91).
  *Re-worded by D97, taking D94's reversal:* the line says what make compared, the marker's date against both
  manifests', and claims no more. Given a lock that differs from what is installed and is dated before the marker —
  brought in by `cp -p`, `rsync -a`, `tar` or a restored backup — when `make check-drawio` runs, then no install
  runs and the line is still true as worded; the model's README names deleting `scripts/event-model/node_modules`
  as the way to install it.

**Carrying it to a project that exists (constitution I; D88, D91, D92)**

- **AC-S04-56** — Given a project made by an earlier factory with no lock under `scripts/event-model/`, when
  `slipwai migrate` runs on a clean tree, then the merge adds the lock and the project's `make check-drawio`
  passes.
  *A reading (D96):* migrating a project made by the factory at the commit before this slice — generated,
  adopted, and with the layout moved, so that a Makefile the earlier factory wrote is the one replaced — was run by
  hand against a factory archived at that commit; the kept test's earlier project is this checkout's with the lock
  removed, since a test that needs an old commit in history fails on a shallow CI clone.
- **AC-S04-57** — Given a project made by an earlier factory with an untracked
  `scripts/event-model/package-lock.json`, when `slipwai migrate` runs, then it refuses as it does for any
  uncommitted change, and the untracked file is left as it was.
- **AC-S04-58** — Given a project that committed a lock of its own which differs from the shipped one, when
  `slipwai migrate` runs, then the merge is left in progress naming `scripts/event-model/package-lock.json` as the
  conflicting file.
- **AC-S04-59** — Given a project generated or adopted before this release, when `slipwai migrate` runs, then
  beyond AC-S04-56 to AC-S04-58 it brings the new Makefile and `scripts/verify` and asks nothing else.
  *A reading (D96):* migrating a project made by the factory at the commit before this slice — generated,
  adopted, and with the layout moved, so that a Makefile the earlier factory wrote is the one replaced — was run by
  hand against a factory archived at that commit; the kept test's earlier project is this checkout's with the lock
  removed, since a test that needs an old commit in history fails on a shallow CI clone.
- **AC-S04-60** — Given the slice's one changelog fragment, when it is read, then its first line is `MINOR` (a new
  generated file; `VERSION` stays `1.6.0.dev0`), and its **Catch-up.** paragraph, standing alone, says what to do
  in each of the three cases (no lock, an untracked lock, a committed lock), that an edited tooling manifest now
  needs a lock that agrees with it, and — under the experimental label, in the body and in the catch-up — that an
  adopted repository's gate started on its own Makefile runs serially whatever `-j` says, that a root Makefile
  which includes it keeps `-j` for its own targets, and that `make -j verify` typed at such a root is not promised;
  the catch-up still says `slipwai migrate` brings the line and asks nothing else (*re-worded by D95*).
  *Added by D96:* the catch-up also says `git add` before the commit in the regenerate branch, names the lock's
  and the manifest's paths for both layouts in one clause (under `delivery/` in an adopted repository), and says in
  one sentence that a teammate who ran the earlier gate and has the untracked lock deletes it and then pulls.
  *Added by D97:* the catch-up also says that a lock the project's `.gitignore` or `.git/info/exclude` names is
  replaced by the merge, and by a teammate's pull, without a refusal, and to move it aside first if it is wanted.
- **AC-S04-61** — Given the page a project gets about the gate, when it is read, then it says: `make -j verify`
  runs the checks at once, from GNU Make 3.81, and when to use it (when you wait on the gate locally); each
  check's output appears when that check finishes; on a make older than 4.0 lines may interleave; the order of
  lines is not promised; the claim is for `verify` as the only goal, and `make -j ci` is not promised; and an
  adopted repository's gate runs serially whatever `-j` says when make is started on the delivery Makefile; a root
  Makefile that includes it keeps `-j` for its own targets, and `make -j verify` typed there is not promised; a
  recorded command that itself calls `make` is that application's own (*re-worded by D95*).
- **AC-S04-62** — Given S04's finished diff, when its files are listed, then `assets/toolkit/scripts/verify-stamp.py`
  is not among them unless `S32-verify-stamp-split` landed first (D91, D92).
- **AC-S04-63** — Given the suites that pin the gate's order and its recipe (S03's), then they are amended beside
  AC-S03-29 for the sync phase and the failed run's closing line, every other S03 suite passes unchanged, and
  every starter combination `make starters` materialises passes its own gate (constitution I; SC-007).
- **AC-S04-64** — *Added by D93.* Given a fresh clone of a generated event-profile project on a branch that is not
  the trunk, on which nothing has been installed, when `make verify` passes for the first time, then the model
  tooling is installed during the run, the pass is not recorded, and the output carries one of the stamp's two lines for a run that
  records nothing — on a Python project, which has no `.venv` yet, the line before the first check that the full
  gate runs and this run records nothing because the environment's file cannot be read; on a TypeScript or Java
  project, the line after the checks that the pass was not recorded because a file git ignores changed while they
  ran (*amended at converge pass 2, T019*); when `make verify` runs again on
  the unchanged tree, it runs in full, installs nothing and is recorded, and the run after that prints the reuse
  line. The stamp's script is not changed by this slice (D73, rule 8).
- **AC-S04-65** — *Added by D93, re-worded by D96.* Given a generated Makefile with the event profile, when it is
  read, then `install` names the model tooling's marker `scripts/event-model/node_modules/.installed` as a
  prerequisite, and `npm` is still spelled for `scripts/event-model` in exactly one recipe; given one without the
  event profile, then `install` is what it was before this slice's model-tooling change.
- **AC-S04-66** — *Added by D93.* Given the page that describes the gate, then it says in one sentence that a
  passing run which installed dependencies as it went is not recorded, that the next run on the unchanged tree is,
  and that `make install` beforehand makes the first one count; given the slice's fragment, then its body says that
  in an event-profile project `make install` now also installs the model tooling from its committed lock, and its
  catch-up asks nothing more for it.
- **AC-S04-67** — *Added by D95.* Given an adopted repository whose root Makefile includes the delivery one and has
  two targets of its own that each log a start and wait a bounded while for the other's, when `make -j` is asked
  for both, then each logs that it met the other (the evidence is the log, never a clock); and with the include
  line taken out the log is the same.
- **AC-S04-68** — *Added by D95.* Given that same root Makefile, when `make -j ratchet-tighten` is run at the root,
  then the three recorded stand-ins run one after another in the gate's order.
- **AC-S04-69** — *Added by D95.* Given that same root Makefile and one target of its own asked for beside
  `ratchet-tighten` in one `make -j`, when it runs, then the root's own target is not made to wait for the three
  stand-ins, and the three do not overlap each other.
- **AC-S04-70** — *Added by D95.* Given the adoption page's `-include` step and the comment in the root Makefile
  block `adopt` writes where there was none, when each is read, then it says the include adds the method's targets
  and leaves the repository's own `-j` alone, and names `make -f <delivery>/Makefile -j verify` as the run that is
  held serial; and no text the factory writes into an adopted repository says the gate is serial *whatever `-j`
  says* without naming that command.
- **AC-S04-71** — *Added by D96 (G1).* Given a generated project with a Go service and none in Java, when `make -j
  verify` runs in full with stand-ins, then every `go` command of `lint` has ended before `typecheck` or `test`
  starts, and `typecheck` and `test` are running at the same moment; given `make typecheck` or `make test` typed
  alone, then `lint` does not run.
- **AC-S04-72** — *Added by D96 (G2).* Given a project with an npm workspace and the event profile and a `python3`
  older than 3.10, when `make -j verify` runs on a fresh tree or on an installed one, then no npm command and no
  `build-packages` starts.
- **AC-S04-73** — *Added by D96 (G2).* Given a `python3` of 3.10 or newer and an installed tree, when `make verify`
  or `make -j verify` runs, then no `npm ci` runs; and given `make build-packages` or a `dev` target typed alone,
  then it does not run `check-python`, as before the slice.
- **AC-S04-74** — *Added by D96 (G3).* Given a generated project with a browser app, freshly cloned with no
  `node_modules`, when `make -j verify` runs with stand-ins, then `check-ux-gates` starts after the root's `npm ci`
  has ended.
- **AC-S04-75** — *Added by D96 (G3, G4).* Given the Makefile of every starter combination `make starters`
  materialises, when it is read, then every target of the gate whose recipe or script reads the root's installed
  tree names the root's install marker as a prerequisite, directly or through `build-packages`, and names
  `build-packages` where it runs the project's own npm code; every other gate target is named in the test with the
  reason it reads nothing there.
- **AC-S04-76** — *Added by D96 (G4).* Given a project with a TypeScript service that exports its API document,
  when its Makefile is read, then `check-openapi` names `build-packages`; and when `make -j verify` runs on a fresh
  tree with stand-ins, then `check-openapi` starts after the package builds have ended.
- **AC-S04-77** — *Added by D96 (G9).* Given an installed model tooling and a `scripts/event-model/package.json`
  edited to another pinned version, when `npm install --package-lock-only` is run in `scripts/event-model` and then
  `make check-drawio` (real npm), then `npm ci` runs, the installed version is the lock's, and the skip line is not
  printed; and when `make check-drawio` runs again, then no npm command runs and the skip line is printed.
- **AC-S04-78** — *Added by D96 (G9).* Given an installed model tooling, when `npm ci` for it starts and does not
  complete, then `scripts/event-model/node_modules/.installed` does not exist and the next `make check-drawio`
  installs.
- **AC-S04-79** — *Added by D96 (G13).* Given the model's README and the tooling manifest's description as a
  project receives them, when each is read, then neither says the gate installs on a first run by `npm install` or
  that `make model` is what installs; each says the tooling installs from its committed lock; and given the shipped
  lock, when the manifest's description changes, then `npm ci` accepts it unchanged.
- **AC-S04-80** — *Added by D96 (G14).* Given a project that committed its own lock and edited the tooling's
  manifest, stopped in the merge `slipwai migrate` leaves on that file, when the catch-up's commands for that case
  are run as written (real npm: regenerate, `git add`, commit), then the commit succeeds and `make check-drawio`
  passes.
- **AC-S04-81** — *Added by D96 (G5 to G8, G17).* Given the criteria AC-S04-26 (the three spellings of the delivery
  Makefile's path), AC-S04-9 (a failed sync and a failed `check-python`), AC-S04-29 (two services under `-j`),
  AC-S04-25 and -16 (a Go and a Java starter) and AC-S04-54 and -64 (a TypeScript project with real npm), then
  each has an example in the suite, written as a hold and seen once to have teeth.
- **AC-S04-82** — *Added by D97 (adversary A1).* Given a generated project whose `lint` and `test` fail (stand-ins),
  when `make -j verify VERIFY_GROUP=-i` runs, and when `VERIFY_GROUP=-i make -e -j verify` runs, then each exits
  non-zero, ends on the failed-run line, writes no stamp, and the next `make verify` runs in full; given the same
  two commands on a tree that passes, then each passes and groups output as a run without the variable; and the
  generated Makefile defines `VERIFY_GROUP` with `override`.
- **AC-S04-83** — *Added by D97 (adversary A3).* Given a generated project with a Go service or a Java service whose
  `lint` fails (stand-ins), when `make -k verify` or `make -j -k verify` runs, then it exits non-zero, `lint`'s
  failure is printed, and `typecheck` and `test` do not start; when `make -k lint typecheck test` runs, then all
  three start. The gates page says a check that waits for a failed one is not run under `-k` and names that
  command, and the fragment's sentence that `make verify` is the serial run it was carries the exception.
- **AC-S04-84** — *Added by D97 (adversary A5, B1).* Given the gates page of a stamped project, when it is read,
  then it says `--synced` in a recipe make echoes is the Makefile's own and that a mode typed by hand takes none,
  and that one `make` at a time runs in a tree, since two started together can install over each other; given the
  model's README as a project receives it, then it says that where a run prints the not-reinstalled line and then
  cannot find a module — or where a lock arrived with an old date — deleting `scripts/event-model/node_modules`
  (under the layout's prefix) and running the gate again installs from the lock.
- **AC-S04-85** — *Added by D97 (adversary B4).* Given a project that ignores `scripts/event-model/package-lock.json`
  and holds its own copy untracked, when `slipwai migrate` runs, then it does not refuse and the file on disk
  afterwards is the factory's — a hold, so the parked question for `migrate` starts from a test it must change;
  held only if the untracked-lock fixture takes an ignore line without a new fixture.

### S33-factory-gate-stamp (method slice)

**Gaps reviewed** 2026-10-04, cruise iteration 14, host (D100, D101): the three examples in `story-split.md` against
the root `Makefile`, `assets/toolkit/scripts/verify-stamp.py` (its `Options`, `standing()`, `key_parts()`, `ask()`
and `EXEMPT`), `STAMPED` in `src/slipwai/project/gate.py`, and every reason the factory's suite skips an example.
Run here, read-only: the script loaded from where it ships answers `standing()` with a stamp allowed on
`adopt-method` (`project.json` records `ci.branch` `main`), and computes the key over this tree, 204 MB of it
ignored, in 0.6 s. Found and written back: `make verify TESTS=…` or `SKIP=…` runs a slice of the suite under the
gate's name, so a stamp written then would let a later full run skip the rest (D100); the suite skips an example
where `tofu`, `pack`, `docker`, `gh`, `uv`, `node`, `npm`, `go` or `java` is missing, so a stamp keyed on fewer
tools than the suite looks for could stand after one is installed, and one keyed on a tool this machine lacks is
never usable (`ask()` cannot ask it) — `pack` and `tofu` are missing here (D100); `sh` answers no version flag
under dash and is left out (D100); the script runs unchanged from `assets/toolkit/scripts/`, because it finds the
root through `check-slice-scope.py` beside it and that finds the git top holding `project.json`, so `S32` is not
owed (D91); the runner's own records are already on the script's exempt list. The root `Makefile` is a control
the cruise guard refuses an iteration to edit: by D99 the edit is a person's, and the run prepares it as one patch
a person reads and applies (D101). Not keyed, and said so: whether the npm registry can be reached (four examples
skip when it cannot), and git's user-level configuration (as S03).

Unless a criterion says otherwise, *the root gate* is `make verify` at this repository's root, *a full run* is one
in which no stamp is reused, and *a stand-in* is an executable written in the test tree, first on `PATH`, that
records it was started and exits as the test says.

- **AC-S33-1** — Given a tree the root gate passed, on a branch other than the trunk and with no CI marker set,
  when `make verify` runs again unchanged, then no check starts, one line says the tree already passed and when,
  and it exits 0.
- **AC-S33-2** — Given that pass, when a tracked file, a file git does not ignore, the `Makefile` or a file under
  `scripts/` changes, then the next `make verify` is a full run.
- **AC-S33-3** — Given that pass, when `make verify VERIFY_FORCE=1` runs, then every check runs and one line says the
  run was forced.
- **AC-S33-4** — Given the trunk checked out, or any of `CI`, `GITHUB_ACTIONS`, `GITLAB_CI` set, when `make verify`
  runs, then it is a full run and no stamp is read, written or removed.
- **AC-S33-5** — *Added by D100.* Given `TESTS` or `SKIP` set, when `make verify` runs, then lint, typecheck,
  check-structure and the named tests run as they do today, and no stamp is read, written or removed.
- **AC-S33-6** — *Added by D100.* Given a pass, when one of `python3`, `git`, `uv`, `node`, `npm`, `go`, `java`,
  `docker`, `pack`, `tofu` or `gh` appears on `PATH`, leaves it, or answers another version, or `make` does, then the
  next `make verify` is a full run; given one of them missing, the stamp is still written and reused.
- **AC-S33-7** — Given a check that fails, when `make verify` runs, then it exits non-zero, names the failure, writes
  no stamp, and the next run is a full run.
- **AC-S33-8** — The root `Makefile` runs `assets/toolkit/scripts/verify-stamp.py` where it ships, unchanged; no copy
  of it is added to the tree, and nothing a generated project receives changes.
- **AC-S33-9** — `make lint`, `make typecheck`, `make check-structure`, `make test` and every other target behave as
  before, `.github/workflows/verify.yml` is unchanged, and `make help` lists `verify` with a line that says a tree
  that already passed is not judged again.
- **AC-S33-10** — Each of AC-S33-1 to -7 has an example in the suite that runs the root `Makefile`, copied into a
  temporary repository with stand-in checks, written as a hold and seen once to have teeth; the factory's own
  second `make verify` on an unchanged tree is measured at the demo.
- **AC-S33-11** — *Added by converge pass 1 (T015, CRITICAL).* Given any environment variable the factory's suite
  reads that narrows or redirects what it runs — `FACTORY_BACKENDS` first — set, when `make verify` runs, then it is
  a full run of what that variable selects and no stamp is read, written or removed, as AC-S33-5; every variable
  the suite reads is named in a table in the suite as either such a bypass or as changing nothing the suite runs,
  with its reason, and a name the table does not carry fails the suite.
- **AC-S33-12** — *Added by converge pass 1 (T016, HIGH) and D112.* Every tool whose presence or version changes what
  the suite runs is in the key: `ko` and `mvn` join the tools of AC-S33-6, and the Docker Compose plugin, which
  `docker --version` cannot see, is keyed through `.factory-work/verify-probes`, a git-ignored file the root gate
  writes from `docker compose version` (or `absent`) before it asks the stamp; a tool the suite probes that is in
  neither the key nor a written exemption with its reason fails the suite.
- **AC-S33-13** — *Added by the after-converge gaps pass (T009, HIGH) and D119.* Given a tree the root gate passed,
  when an interpreter cache (`__pycache__/`, `*.pyc`, `*.pyo`) appears or goes anywhere under `assets/`, then the next
  `make verify` is a full run, because the root gate writes the sorted list of those paths into
  `.factory-work/verify-probes` before it asks the stamp; their contents are not keyed, and the shipped script's
  `EXEMPT` is unchanged.

### S05-xdist

**Gaps reviewed** 2026-10-04, cruise iteration 14, host with `drive-skipper` for D102 and D103 and the host's own
D104: the three examples in `story-split.md` against `python_verify()` in `src/slipwai/project/languages/python.py`,
`metadata()` in `src/slipwai/project/metadata.py`, `replay.py`'s handling of `project.json`, the service
`pyproject.toml` template, the generated gates page (`src/slipwai/project/docs.py`), and each other backend's test
command (`typescript.py`, `go.py`, `java.py`). Run on a Python starter generated for the purpose (event profile,
FastAPI, SQLite store, 130 tests, 12 cores, pytest 9.1.1, pytest-xdist 3.8.0): serial 0.95 s, `-n 2` 1.13 s, `-n 4`
1.26 s, `-n auto` 1.9 s; every run passed, and a `-k` that matches nothing exits 5 under the plugin as without it.
Found and written back: `migrate` regenerates `project.json` through `metadata()`, so a key a new release writes
would reach every existing project through the merge and switch its tests to parallel unasked (D102); every xdist
setting is slower than serial on a new project, and twelve workers beside `make -j`'s mypy and ruff is the worst of
them (D103); the script names its services at generation and nothing rewrites it when `project.json` is edited, so
a one-line opt-out has to be read when the gate runs (D104); the integration suite shares one database (D104);
Maven's Surefire runs tests one at a time here, so "the other runners already run in parallel" is not true of
Java (D104); a new development dependency in every generated Python service is recorded as ADR 0003 at
`Proposed`.

Unless a criterion says otherwise, *the Python project* is a project generated with a Python service, and *the
mark* is `parallelSafe` at the top level of the project's `project.json`.

- **AC-S05-1** — *D102.* Given `slipwai generate` with any backend, then `project.json` carries `"parallelSafe": true`.
- **AC-S05-2** — *D103, D104, D106, D108.* Given the Python project with the mark `true` and no CI marker set (`CI`,
  `GITHUB_ACTIONS`, `GITLAB_CI`), when `make verify` or `make test` runs, then its pytest command carries the parallel
  flags (`-n auto --maxprocesses 4`, with the plugin loaded explicitly — D108 part 2), and every test that fails in the
  parallel run also fails in the serial run on the same tree, where no module at the project's root is named like a
  standard-library one. The parallel run does not promise to fail every test the serial run fails: a test that depends
  on another test's state may pass in it, and AC-S05-14 is what catches that.
- **AC-S05-3** — *D104.* Given the mark set to `false`, removed, or any value but the JSON `true`, or `project.json`
  unreadable, when the gate runs, then pytest runs with no `-n` and every other word of the command as today; the
  change takes effect on the next run with nothing regenerated.
- **AC-S05-4** — *D104.* Given the mark `true`, when `make test-integration` runs, then pytest runs with no `-n`.
- **AC-S05-5** — *D104, D106.* Given the mark `true`, when `--adversarial-only` runs, then pytest runs with no `-n`,
  and a `-k` that matches no test passes as it does today (exit 5); a test module whose import crashes the
  interpreter fails it.
- **AC-S05-6** — *D103.* The service `pyproject.toml` template's `addopts` is unchanged: a person's own `pytest` run
  is serial.
- **AC-S05-7** — *D104.* `pytest-xdist==3.8.0` is in every generated Python service's development dependencies and
  in each of the four committed locks, which `uv sync --locked` accepts.
- **AC-S05-8** — *D102.* Given a project generated before this release, when `slipwai migrate` runs, then its
  `project.json` has no `parallelSafe` and its gate runs pytest serially; given a project whose mark says `false`
  or `true`, then after `migrate` it says the same.
- **AC-S05-9** — *D102.* Given `slipwai adopt` or `adopt --refresh`, then the record carries no `parallelSafe`, and
  no adopted application's own test command changes.
- **AC-S05-10** — *D104.* Given a TypeScript, Go or Java starter, then the matrix test still passes and its test
  command is unchanged; the generated gates page says, for each backend the project has, whether its runner runs
  tests in parallel — Vitest by file, `go test` by package, Maven's Surefire one at a time.
- **AC-S05-11** — *D102, D103.* The gates page documents the mark: its default, that a missing mark is serial, and
  one sentence on when to set it to `false` (tests that share a file, a port, a database or module-level state).
- **AC-S05-12** — The `changelog.d/` fragment claims MINOR (a new `project.json` key with a documented default), and
  its catch-up note, standing alone, says a project made before stays serial and names the one line that opts it in.
- **AC-S05-13** — *D103.* The demo records, in the quickstart and the fragment, serial and parallel test times on a
  fresh starter with the command, the machine and its core count, and `make -j verify`'s median against the serial
  gate's (D89's criterion still holds).
- **AC-S05-14** — *D106.* Given the mark `true` and any one of `CI`, `GITHUB_ACTIONS` or `GITLAB_CI` set (to anything,
  `false` included), when `make verify` runs, then pytest runs with no `-n`; given two tests that share module-level
  state, so the serial run fails, then the gate run with `CI=true` fails. The gates page says in one sentence that a
  parallel run can hide a test that depends on another's leftovers, and that CI runs serially to catch it.
- **AC-S05-15** — *D107.* Given a `project.json` with any key written twice, at any depth, when `add-service`,
  `describe-service`, `add-frontend`, `confirm`, `adopt --refresh` or `migrate` runs, then it refuses before writing
  anything, in one line naming the file, the key and "keep one copy", and `project.json` is byte-for-byte unchanged;
  given a mark a person added anywhere but after `"target"`, when `migrate`'s merge leaves it twice, then `migrate`
  exits 0, keeps the merge, and says in one line (and in the catch-up note) that the gate reads it serial and to keep
  one copy. `ci.branch` is held by the same rule.
- **AC-S05-16** — *D108.* `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` leaves the parallel run starting its workers; the gates
  page names `-p no:xdist` in `PYTEST_ADDOPTS` as the case that fails on an argument error, and names a root module
  named like a standard-library one (a `json.py`) as crashing every worker; a project with no Python service gets the
  sentence "Where `project.json` carries `"parallelSafe": true`, …"; a mark that is a non-finite number (`1e400`,
  `NaN`) is refused by every factory rewrite of `project.json` with one line and nothing written.

### S06-scoped-gate

**Gaps reviewed** 2026-10-05, cruise iteration 17, host with `drive-skipper` for D114, D115 and D116 and the host's
own D117: User Story 2's scenarios 1–5 and its Independent Test, revised FR-006 and FR-007, FR-023 (what S07 adds to
the record) and FR-039–FR-044 (what S34–S36 read through it), against `makefile()` and `native_commands()` in
`src/slipwai/project/`, the stamped gate (`gate.py`, `parallel_gate.py`, `assets/toolkit/scripts/verify-stamp.py`),
the base and change rules of `assets/toolkit/scripts/check-slice-scope.py`, the contracts a generated project has
(`openapi.py`, `shared_packages.py`, the event model's `reads`), the ladder text (`commands.py`,
`parallel_slices.py`) and the adopted `delivery/Makefile`. Found and written back: nothing regenerates a stored
record when a person edits `project.json`, so the record is derived when the gate runs and the obligations a person
declares live in `project.json` (D114, ADR 0004 at `Proposed`); `lint`, `typecheck` and `test` are each one target
over every deployable, so a component is a deployable with targets of its own, and a recipe line shared by a family
— Python's `scripts/verify` — selects the whole family (D115); a machine's tool version and a variable's value are
not in git, so they are compared with a baseline only a full green gate on the branch writes (D116); the stamp is
stronger than any scoped run and only `make verify` writes it (D116); `check-slice-scope` reads every changed file,
so it runs always and claims nothing, or no file would ever be unclaimed (D117); the ladder's three gate calls are
two scoped and one full (D117); an adopted repository gets the target as its full gate (D114).

Unless a criterion says otherwise, *a slice branch* is a branch named `slice/<id>` with a usable base, outside CI;
*the base* is the merge-base `check-slice-scope` finds; *changed* is a path that differs from the base in a commit,
the working tree or an untracked file git does not ignore (a deletion and both sides of a rename included); *the
checks* are this project's `verify-checks` prerequisites; and *the record* is what `verify-scoped` derives.

- **AC-S06-1** — *D117.* Given the trunk, a branch not named `slice/<id>`, a detached `HEAD`, any of `CI`,
  `GITHUB_ACTIONS` or `GITLAB_CI` set, or a slice branch with no usable base, when `make verify-scoped` runs, then it
  runs `make verify` — its stamp reuse and record as that target has them — and says in one line which of those it
  was; its exit status is `make verify`'s.
- **AC-S06-2** — *D115, scenario 1.* Given a generated project with two deployables and a slice branch changing one
  source file under one deployable's path, when `make verify-scoped` runs, then that deployable's `lint-<name>`,
  `typecheck-<name>` and `test-<name>` run, with every project-wide check whose recorded inputs include the file, and
  the other deployable's three are named as skipped with *none of its inputs changed*.
- **AC-S06-3** — *D115, scenario 1.* Given a change to a service's committed OpenAPI document or its source, then
  `check-openapi` and the typecheck and test of every web app whose `api` names the service run; given a change under
  `packages/<name>/`, then the typecheck and test of every npm-family deployable run; given a change in a service
  that produces an event another service's slice `reads` in `model.yaml`, then the reading service's typecheck and
  test run.
- **AC-S06-4** — *D115.* Given two Python services and a change in one, then all three checks of both run, and the
  run says the Python services share one recipe; `verify`'s targets, recipes and output are byte-for-byte today's.
- **AC-S06-5** — *D114, D117, scenario 2.* Given a changed file no deployable's path and no check's recorded inputs
  claim, or a change to `project.json`, the `Makefile`, anything under `scripts/`, then `make verify-scoped` runs
  `make verify` and prints, once per such file, that dependency knowledge was incomplete for it; so does a record
  the script cannot build, naming why. *(Amended by D140, D146, D148:)* a `Makefile` that is not the factory's text,
  a make option that adds text or conditions, or a deployable reaching another's path is a cause checked first, and
  only the first cause found is printed.
- **AC-S06-6** — *D117.* `check-slice-scope` runs on every scoped run and claims no file; a check with no recorded
  inputs — until `S07-scoped-checks`, `check-agents`, `check-speckit`, `check-extensions` and `check-constitution` —
  runs on every scoped run, named with *no recorded inputs*, and broadens nothing else.
- **AC-S06-7** — *D116, scenario 3.* Given a change to a file that pins a tool (`.python-version`, `.nvmrc`,
  `uv.lock`, `pyproject.toml`, `package-lock.json`, `go.mod`, `go.sum`, `pom.xml`, the Maven wrapper's properties),
  then every check whose tool it pins runs.
- **AC-S06-8** — *D116, scenario 3.* Given a green `make verify` that ran every check on this slice branch, when a
  machine tool a check reads answers its version differently, or a variable a check reads changes — set, unset or
  given another value — then every check that reads it runs; with both as they were, those checks are skipped with
  *none of its inputs changed*. `UX_GATES_JOBS` and the job count select nothing.
- **AC-S06-9** — *D116.* Given no baseline, a baseline taken on another branch, one that does not parse, or a tool
  the record names that does not answer, then every check that reads a tool or a variable runs, and the run says
  why once. The baseline is kept in the git directory beside the stamp, holds the branch, each tool's answer, a
  digest — never the value — of each variable, and one digest of the files git ignores that the stamp's key holds
  (never a path; *D125*): where that digest differs from the tree's, the run is the full gate and says the ignored
  part moved; it is written only by a `make verify` that ran and passed every check
  on this slice branch, never by a scoped run that ran fewer, never under `-i`, `-n`, `-t`, `-q` or
  `RATCHET_TIGHTEN`, and a failed `make verify` removes it.
- **AC-S06-10** — *D116.* Given a verify stamp `reuse` accepts for the current tree, then `make verify-scoped` prints
  the reuse line and exits 0 running nothing else; `VERIFY_FORCE` set makes it `make verify`; `verify-scoped` never
  writes, removes or refreshes the stamp except through `make verify`'s own recipe.
- **AC-S06-11** — *D114, scenario 4.* Given an integration obligation declared in `project.json` at the base, naming
  two deployables and the checks that hold it, and a slice branch changing a file of either, then the obligation's
  checks run and are named with it. A missing key is no obligation; a key that does not parse, or an entry naming a
  deployable or a check the record does not know, runs `make verify` with one line naming the entry.
- **AC-S06-12** — *D117.* Every check is named once — run, with the first changed input that chose it, or skipped
  with its reason — and a last line counts each; the chosen checks run in one `make` call with the gate's grouping
  and ordering, so `make -j verify-scoped` runs them in parallel as `make -j verify` does; a failed check fails the
  run and is named.
- **AC-S06-13** — *D114.* `verify-scoped` can print the record as JSON in the shape ADR 0004 fixes: every check
  with its inputs (files, tools, variables) and its components, each deployable, each contract with its consumers,
  each obligation; a check with no recorded inputs appears with none.
- **AC-S06-14** — *D117, scenario 5, SC-007.* Given `main`, then `make verify-scoped` is `make verify`; the
  generated `verify`, `verify-checks` and `ci` rules are unchanged, and the full gate's findings on the same tree are
  identical before and after the slice.
- **AC-S06-15** — *D117, FR-007.* The generated drive ladder starts a slice from a green `make verify-scoped` and
  runs it before the first push; Phase 4 on `main` and the merge root keep `make verify`; the generated agent
  settings allow `make verify-scoped`.
- **AC-S06-16** — *D114.* Given an adopted repository, then `make -f delivery/Makefile verify-scoped` runs its full
  gate and says in one line that this layout has no verification-dependency record yet.
- **AC-S06-17** — Given a project generated before this release, when `slipwai migrate` runs, then it gains
  `verify-scoped` and the per-deployable targets, and its `project.json` gains no obligations key. The `changelog.d/`
  fragment claims MINOR, and its catch-up note, standing alone, names `make verify-scoped`, says the merge root and
  CI still run the full gate, and names the key that declares an obligation.
- **AC-S06-18** — The generated gates page documents `verify-scoped`: where it scopes and where it is the full gate,
  what broadens it, the baseline, and the obligations key with its default (none) and one sentence on when to
  declare one.
- **AC-S06-19** — Scenario 7 re-checked: given the merge root, `make verify` runs pytest with xdist as `S05-xdist`
  delivered. The demo records, in the quickstart and the fragment, `make verify-scoped` on a slice branch touching
  one deployable of a two-deployable starter against `make verify` on the same tree, with the command and the machine.

### S08-scoped-mutation

**Gaps reviewed** 2026-10-05, cruise iteration 23, `drive-gaps` (read only) with `drive-skipper` for D137 and D138 and
the host's own D139: User Story 2's scenario 6, FR-008, FR-007 and FR-010's placement, S08's split and graph rows
against D129 and the rows of `S06-scoped-gate`, `S14-result-contract` and `S38-factory-test-selection`; D110, D111,
D117, D123, D125, D127–D133, ADR 0004 and ADR 0005; the owner brief's priorities, *Out of scope* and *Always ask a
person*; against `mutation.py`, `native_commands.py` and `makefile()` in `src/slipwai/project/`,
`assets/languages/go/scripts/go-mutation.py`, the Spring pom's `pitest-maven` block, `verify-stamp.py`'s cache table,
`verify_scoped/rules.py`, the adopted `delivery/Makefile`, `commands/mutation.md`, the Phase 4 text in
`parallel_slices.py`, `docs/backend-obligations.md` and `mutation-testing/SKILL.md`. Found and written back: no gate
in a generated project runs `make mutation`, so scoping is additive except through a project's own CI and Phase 4 on
`main`; only Go and Spring have a working tool — TypeScript and Python are wired by follow-on slices, Quarkus stays a
placeholder (D137, FR-008 amended); the unit, what changed, what sweeps and an explicit `SINCE` (D138); Phase 4 on
`main` names the commit before the merge (D139); a merged recipe stops at the first placeholder's `exit 2`; Spring's
`failWhenNoMutations` would turn an empty scope red; mutation output must stay out of the stamp's key and the
ignored-files digest; a new Make construct must be one `rules.py` reads, or every scoped run is the full gate; the graph
rows now say S08 runs beside S06 and S14 (D129).

Unless a criterion says otherwise, *a slice branch*, *the base* and *changed* are as S06 defines them (D117 rule 2,
D138 item 2); *a production file* is a source file of a service that is not a test; *the sweep* is the command
`make mutation` runs today for that backend.

- **AC-S08-1** — *D117 rule 1, owner priority 1.* Given the trunk, a branch not named `slice/<id>`, a detached `HEAD`,
  any of `CI`, `GITHUB_ACTIONS` or `GITLAB_CI` set, a slice branch with no usable base, or a directory git cannot read,
  when `make mutation` runs with no `SINCE`, then it runs the sweep and says which case it was in one line; its exit
  status is the tool's.
- **AC-S08-2** — *Scenario 6, Go.* Given a two-service Go starter and a slice branch changing one production file in
  one service, when `make mutation` runs, then that service's Gremlins run mutates only that file, and the other service
  is named as skipped with *no changed production file* and starts no Gremlins.
- **AC-S08-3** — *Scenario 6, Spring; D138 item 1.* Given a Spring starter and a slice branch changing one class inside
  the pom's `targetClasses`, then PIT mutates only that class and its inner classes (`Foo` and `Foo$*`, never a `Foo*`
  prefix); the pom's `excludedClasses`, `targetTests` and `*IT` exclusion still hold.
- **AC-S08-4** — *Spring.* Given a change only to classes outside `targetClasses`, then Maven is not invoked, each such
  file is named with its reason, one line says no mutant runs, and the exit is 0 — a scoped run never trips
  `failWhenNoMutations`.
- **AC-S08-5** — *D137 item 2.* Given a changed production file in a TypeScript, Python or `java-quarkus` service, when
  `make mutation` runs, then that service's placeholder still exits 2 with its setup message, adding that the scope will
  apply once a tool is wired, and names the files it would mutate; an untouched placeholder service is named as skipped
  and does not fail the run.
- **AC-S08-6** — *Mixed backends.* Given a project with a wired backend and a placeholder one and a slice branch
  changing only the wired one's file, then the scoped run completes and exits by that backend's result — a placeholder
  ahead of it in service order no longer stops it.
- **AC-S08-7** — *D138 items 1 and 3.* A change only to tests runs no mutants: one line names the changed test files and
  says `make mutation-full` is the run that measures them, exit 0. A change only to non-source files or only deletions
  runs no mutants, one line, exit 0. A renamed production file is mutated at its new path (for Java, its new fully
  qualified name).
- **AC-S08-8** — *D138 item 3.* A change to a service's own mutation configuration (`.gremlins.yaml`, its pom's
  `pitest-maven` block compared as parsed structure, a Stryker config or `[tool.mutmut]` table where wired) sweeps that
  service; a change to `go-mutation.py` or the new scope script sweeps every service of that backend; a change to the
  `mutation` rule's text sweeps every service; a configuration file that cannot be parsed on either side counts as
  changed. Each names the file that caused it.
- **AC-S08-9** — *D138 item 3.* A changed file under `packages/` is named as *not mutated by this target* and exits 0.
- **AC-S08-10** — *D138 item 4.* Given `make mutation SINCE=<ref>` on any checkout, CI included, every wired backend
  scopes to the production files `git diff <ref>` names, the working tree and untracked files included — Go's published
  meaning, unchanged. An unresolvable `<ref>` fails naming it; `SINCE` with an empty value is the sweep.
- **AC-S08-11** — *FR-008.* On every checkout `make mutation-full` runs the sweep, each backend's recipe lines byte for
  byte today's; it appears in `make help` and `.PHONY`.
- **AC-S08-12** — *D138 item 5.* The run's first line is one of *scoped to <n> changed file(s) since <base>: …*, *the
  sweep runs — <reason>* or *no mutant to run — <why>*; every service is named once — scoped with its files, skipped or
  swept with its reason — and a last line counts each; a scoped service's failure fails the run and is named.
- **AC-S08-13** — *SC-007, ADR 0005, D133.* `mutation` and `mutation-full` are reachable from none of `verify`,
  `verify-checks` and `ci`; those rules and the generated CI workflow are byte for byte unchanged; `rules.json` is
  generated from the new Makefile, and on a freshly generated project `make verify-scoped` on a slice branch is not
  driven to the full gate by anything S08 wrote.
- **AC-S08-14** — *D116, D125.* Given a reusable verify stamp and a scoped baseline, after `make mutation` or
  `make mutation-full` runs, the stamp still reuses and `verify-scoped` is not broadened: every report and temporary
  tree the run leaves is git-ignored and a cache row in `verify-stamp.py`'s key, as `gremlins.json` already is.
- **AC-S08-15** — *Adopted layout.* Given an adopted repository, `make -f delivery/Makefile mutation` and
  `mutation-full` run the recorded command unchanged, and one line says this layout has no mutation scope.
- **AC-S08-16** — *D138 item 2.* `mutation-testing/SKILL.md`'s clean-tree sentence is replaced: staged, unstaged and
  untracked production files are included and mutated, nothing is committed or stashed to run it.
- **AC-S08-17** — *D139.* `commands/mutation.md` (from `mutation_command()`), for every backend, says the bare target
  scopes on a slice branch, `SINCE=<ref>` scopes anywhere, `mutation-full` is the sweep, CI and the trunk get the sweep,
  and Phase 4 on `main` runs `make mutation SINCE=<the commit before the merge>`; each backend's note above the target
  in `mutation.py` says the same (Go's *Without SINCE it mutates the whole module* is rewritten).
- **AC-S08-18** — *Catch-up.* Given a project generated before this release, when `slipwai migrate` runs, then it gains
  the scoped `mutation`, `mutation-full`, any new script and a regenerated `rules.json`; the fragment claims MINOR, and
  its one-paragraph catch-up note says what `make mutation` now does on a slice branch, that it is unchanged in CI, on
  the trunk and with `SINCE`, that `mutation-full` is the old behaviour, and which backends still need a tool wired.
- **AC-S08-19** — *The row's "proportional".* The demo records `make mutation` against `make mutation-full` on a
  two-service Go starter and a Spring starter, on a slice branch touching one file — wall time, mutant counts, the
  command and the machine — in the quickstart.

### S14-result-contract

**Gaps reviewed** 2026-10-05, cruise iteration 23, `drive-gaps` (read only) with `drive-skipper` for D134, D135 and
D136: S14's split and graph rows, S02's *Defers* cell, the rows of S15, S28, S30, S34a, S34b, S38 and S39; User Story
6, FR-017, FR-024 (D59's reading), FR-032, FR-036, FR-046–FR-050, FR-057, SC-008 and the *Result contract* entity; D59,
D60, D65, D128–D133; constitution VIII, XIV and *Additional Constraints*; against `assets/toolkit/scripts/check-decisions.py`,
`assets/toolkit/scripts/agents/benchmark.py`, `code_index.py`'s `sync`, `cruise.py`'s stream, `agents.py` and
`cruise_agents.py` (ten types and their return clauses), `migrate.py`'s re-projection and `catch_up.py`; S06's plan and
tasks for shared files. Found and written back: hand-backs were persisted nowhere a gate can read — they go to the
slice's append-only `hand-backs.md`, written by the dispatching session (D134, ADR 0006 at `Proposed`); the PRD's shape
cannot be opened, so schema 1 is fixed here — JSON, thirteen fields, a per-type `status` set, `difficulty_observed` as
an object (D134); D59's deferred sync was dropped from the row — S14 adds `files_changed` and the sync is
`S40-reported-sync` (D135); a missing block is closed by one continuation or a recorded `Missing:` line, late stages
are checked at the demo and adversary stops, and the demo runs on a generated project (D136); three types already have
return words the block keeps; S14 shares `agents.py` and `commands.py` with S06; the graph rows now say S14 runs beside
S06 and S08 (D129).

Unless a criterion says otherwise, *a delegate* is one of the ten `drive-*` types; *a hand-back* is its final message
to the session that dispatched it; *the block* is the fenced `result-contract` block; *the record* is
`specs/<feature>/slices/<id>/hand-backs.md` (feature-level stages: `specs/<feature>/hand-backs.md`).

- **AC-S14-1** — *D134 item 6.* Given a project generated at the root or under `delivery/`, when its agent files are
  written, then each of the ten types' standing brief tells it to end its hand-back with the block, pointing at the shape
  written once (a page every type references, as the safety page is); one test runs over every type; `make agents`
  carries it into every harness's agent file, and the drive and cruise commands' dispatch text says the dispatching
  session appends each block to the record.
- **AC-S14-2** — *D134 item 3.* The types with a return protocol keep it: the bosun's and the hand's verdict words are
  their block's `status`; a skipper's entry is followed by the block, and the host writes the entry to `decisions.md`
  and the block to the record; no brief tells a delegate to end two ways at once.
- **AC-S14-3** — *D134 item 2.* Given a record holding one well-formed block — one JSON object, `contract: 1`, all
  thirteen fields of the right type — when `check-decisions` runs, then it passes; a list field may be empty, never
  absent.
- **AC-S14-4** — *The row's second example.* Given a block missing a field, holding a value of the wrong type, or a
  `status` outside its type's set, then `check-decisions` exits 1 with one line per fault naming the record file, the
  entry's heading and the field.
- **AC-S14-5** — *Constitution VIII.* Given a block with a field outside the thirteen, the gate passes; given
  `contract` greater than 1, it passes with a note and holds no field.
- **AC-S14-6** — An unterminated fence, two blocks in one entry, a heading not in D134's shape, an entry with neither a
  block nor a `Missing:` line, or a body that does not parse is a finding naming the entry.
- **AC-S14-7** — *D135, constitution Additional Constraints.* An absolute path or one containing `..` in
  `files_changed` or any path-valued field is a finding naming the field; `files_changed: []` passes.
- **AC-S14-8** — *D134 item 4.* A `decisions` id not matching `^D[0-9]+$` or naming no entry in the feature's
  `decisions.md` is a finding.
- **AC-S14-9** — *D134 item 5.* `difficulty_observed` is `{"score": 1–5, "reason": "<non-empty>"}`; anything else is a
  finding.
- **AC-S14-10** — *D134 item 1.* When a delegated stage ends, the dispatching session validates the block with the
  checker's own function and appends it verbatim under `## <UTC time> — <type> — <stage>`; a concurrent slice appends
  only to its own folder; entries are never edited.
- **AC-S14-11** — *The row's first example, D136 item 1.* Given a hand-back with no block, when converge runs, then its
  verdict carries a finding naming the stage and type; the finding closes with a block from one continuation of the same
  delegate that passes the checker, or a recorded `- **Missing:** refused | malformed: <field> | no continuation`; the
  stage is never re-run for it and the host never writes a block for a delegate.
- **AC-S14-12** — *D136 item 2.* Before the hand is dispatched, the host checks every hand-back since the last converge
  pass; at the adversary stop it checks the hand's, the adversary's and mutation's; a miss there is a task in the slice's
  `tasks.md` and does not reopen converge; the completion audit is the backstop.
- **AC-S14-13** — A stage run in the host's own context has no hand-back, and nothing is recorded or found for it; a
  stopped or cut-off delegate's entry says so with its reason and is not charged with a malformed block.
- **AC-S14-14** — *D134 item 6.* Untyped helpers a delegate starts report inside that delegate's one block; inside a
  `drive-slice` worktree, `drive-slice` records its own sub-delegates in its slice's record.
- **AC-S14-15** — *SC-008, first half.* `make benchmark` prints *hand-backs with a result contract: n of m* per slice,
  `m` the delegated stages in `benchmark.json`; a harness that cannot attribute a delegate says so rather than guessing.
- **AC-S14-16** — *D60, D65.* Given a project whose slices predate this release, with no record anywhere, then
  `check-decisions`' output and exit are byte-identical to today's, and the full gate's findings are unchanged (SC-007).
- **AC-S14-17** — *Migrate.* Given a project generated at the release before this one, when `slipwai migrate` runs,
  then the agent files, the commands, the shape's page and `check-decisions.py` are replaced and re-projected,
  `make verify` passes on the project's existing records unchanged, and the fragment's one-paragraph catch-up note says
  nothing is asked of existing logs and slices without a record are not refused; the same holds for an adopted
  repository under `delivery/`.
- **AC-S14-18** — *D129, the shared-surface rule.* S14's branch writes only under `assets/toolkit/`, `src/slipwai/project/`
  (`agents.py`, `cruise_agents.py`, the drive and cruise text in `commands.py`, `converge_stage.py`, `cruise.py`, `docs_index.py` and a new `result_contract.py` — D144), `tests/`,
  `docs/`, `changelog.d/result-contract.md` and its own slice folder; never `delivery/`, `decisions.md`, `spec.md`,
  `story-split.md` or the register; and stays off the paragraphs S06's D123 rewords.
- **AC-S14-19** — *D136 item 3.* The demo runs on a project generated from the slice branch: real delegates through
  its own headless harness produce hand-backs, and two seeded fixtures (no block; a malformed block) show the converge
  finding — in a real `drive-converge` verdict over the no-block fixture (D145) — and the field-naming refusal; the share of real hand-backs carrying a block is written into the quickstart
  with the project's axes, the harness and the number.
- **AC-S14-20** — *D160, adversary B1, A2, A5.* Given a stage whose benchmark entry has ended and a continuation
  recorded afterwards with `--hand-back … --started <that stage's started>` (or `--hand-back-missing … --started …`),
  when `--hand-backs` runs, then that stage reads `block` (or `missing — <reason>`) and no other stage of the same name
  does; an entry's heading carries ` — <started>` as its fourth part, the verb fills it from the stage's open entry and
  refuses, writing nothing, an instant naming no entry or an omitted one where only ended entries exist; an entry with no
  instant covers no stage; the same reason or block for a different start of the stage is appended, the same for the
  same start is not.
- **AC-S14-21** — *D161, adversary B2.* Given a project where `hand_backs.py` first reached the history at instant T
  (the earliest adding commit's author time), then a stage whose entry ended strictly before T owes nothing and is listed
  as *predates the result contract*, a stage that ended at or after T still owes a block, a shallow clone, no git, an
  uncommitted module or an unparseable time read as *could not tell* and are counted in neither n nor m, and
  `make benchmark` reports every predating stage in one line instead of a `0 of m` line per slice.
- **AC-S14-22** — *D162, adversary A8.* Given a block whose `contract` is anything other than 1, `--hand-back` exits 1
  and writes nothing, in one line naming the value; the gate keeps AC-S14-5's forward reading of a record already
  written; and `--hand-backs` reads such an entry as *a block this factory cannot check*, counted in m and not in n.
- **AC-S14-23** — *D163, adversary B6.* An `unavailable` skipper answer is a `decisions.md` entry with **Decision:**
  `unavailable: <what a person must provide>`; a skipper's own entry number goes in its block's `change_summary`,
  never in `decisions`, and the cruise text, the skipper's brief and the page say so.
- **AC-S14-24** — *Adversary A1, B3, A3, A4, A6.* Every value a verb writes outside the delegate's verbatim block is
  one line or is refused; every page that owns a stop with delegates says to append each block before ending the
  stage's entry; a harness whose reader attributes no subagents reads as *could not attribute*; stdin is read as
  UTF-8 whatever the locale; a damaged record, benchmark file or body ends in the page's exits, never a traceback.

### S38-factory-test-selection

**Gaps reviewed** 2026-10-06, cruise iteration 24, `drive-gaps` (read only) with `drive-skipper` for D156 and D157 and
the host's own D158: FR-048, SC-016, S38's split and graph rows against D128–D132, the owner brief's priorities, *Out
of scope* and *Always ask a person*; against the root `Makefile`'s `test`, `verify` and `verify-checks` rules and its
stamp bypass list, `tests/support.py`, the suite's 318 modules (140 generate a project, about 100 import a shared
fixture, 13 read `backends_under_test()`, many load scripts under `assets/` by path), `make starters`, `ratchet.py`
inside `make -f delivery/Makefile verify`, the CI workflow's `TESTS=` and `SKIP=` jobs, S33's stamp and S06's scoped
gate. Found and written back: this repository's merge root is `adopt-method`, not the trunk `project.json` names, and
a base of `main` makes every run here full (D156: the trunk, or a base named by `SINCE`); `make verify` reaches `make
test` through `verify-checks` and must stay full and stamped; the ratchet's tighten would erase findings of modules
that never ran; nothing in the suite declares what it reads, so an undeclared module always runs; the factory suite
runs serially under unittest, so S05's xdist does not meet it; the demo measures selection and soundness, and reports
time against a same-commit full run without a threshold (D157); the root `Makefile` is a patch a person applies, as
S33's was.

Unless a criterion says otherwise, *a slice branch* is a branch named `slice/<id>`, *the base* is D156's, *changed* is
what D117 rule 2, D125 and D153 count, and *full* means every test module, with `FACTORY_BACKENDS` unset.

- **AC-S38-1** — *G1, owner priority 1.* Given the trunk, `adopt-method`, any branch not named `slice/<id>`, a detached
  `HEAD`, a branch whose trunk cannot be told, or any of `CI`, `GITHUB_ACTIONS` or `GITLAB_CI` set, when `make test`
  runs, then it runs full and says which case it was in one line.
- **AC-S38-2** — *G2, D156 (AC-S38-G2a).* Given a slice branch with no `SINCE` whose only change since its merge-base
  with `main` is one path under `assets/languages/go/`, and `origin/main` level with local `main`, when `make test`
  runs, then the first line reads ``compared with `main` at <short> (the trunk)`` and the selection reflects that one
  path only.
- **AC-S38-3** — *G2, D156 (AC-S38-G2b).* Given a slice branch cut from `adopt-method` whose only change against
  `adopt-method`'s tree is one path under `assets/languages/go/`, when `make test SINCE=adopt-method` runs, or
  `SINCE=adopt-method make -f delivery/Makefile verify`, then the first line reads ``compared with `adopt-method` at
  <short>, named by SINCE — taken as passing on the word of whoever named it`` and the selection reflects that one path
  only; `SINCE` compares with that ref's tree (D138 item 4), not a merge-base.
- **AC-S38-4** — *G2, D156 (AC-S38-G2c, G2d, G2e).* Given the same branch with no `SINCE`, whose diff against `main`'s
  merge-base includes `Makefile` and `catalog.json`, then every module runs and the line names the first broadening path
  and its rule; given `SINCE=nonexistent`, or a `SINCE` with no history in common with `HEAD`, then every module runs
  and the line reads `full: SINCE=<ref> could not be resolved — <why>`; given `SINCE=main` on `adopt-method`, or on a
  slice branch with `CI=1`, then every module runs and the line gives AC-S38-1's reason, not the base.
- **AC-S38-5** — *G2, D117, D125, D153 (AC-S38-G2f).* Given a slice branch with `SINCE=adopt-method` whose only change
  is an untracked new file under `assets/languages/go/`, or the deletion of one, then the modules that read the `go`
  configuration are selected; given no `SINCE` and a local `main` with an unpushed commit touching `catalog.json`, then
  every module runs and the line names that path as D153 words it.
- **AC-S38-6** — *G3, S33's stamp.* Given a slice branch with a one-backend change, when `make verify` runs, then every
  module runs and the stamp is recorded as S33 records it; given a selection variable on `make verify` (`SINCE`
  excepted, which never narrows `make verify`), then no stamp is read, written or removed.
- **AC-S38-7** — *G4.* Given `RATCHET_TIGHTEN=1` on a slice branch, when `make test` runs, then every module runs and
  the line names `RATCHET_TIGHTEN`.
- **AC-S38-8** — *G5.* Given a change only under `assets/languages/go/`, when `make test` selects, then the modules
  that declare the `go` configuration, those that declare every configuration and those that declare nothing run, and
  every other module is named skipped with its reason (*reads no go configuration*); given a new directory under
  `assets/` that no rule claims, then every module runs and the line names the path. A module's declaration names
  only configurations and files that exist, held by a test.
- **AC-S38-9** — *G6.* Given a change that affects only the `go` backend, then `test_matrix` runs with
  `FACTORY_BACKENDS=go` and the output names the backends left out.
- **AC-S38-10** — *G7.* Given a one-line change to `catalog.json`, `assets/backing-services/prune.py`, any file under
  `src/slipwai/`, the root `Makefile`, `scripts/verify`, `requirements-dev.txt`, `pyproject.toml`, `VERSION`, the
  selector or its own tests, an ignored file under `assets/`, `src/` or `tests/` other than the caches D119 exempts, or
  any path no rule claims, then every module runs and the line names the path and the rule; given a change to one shared
  fixture module only, then exactly the modules that import it, directly or through another, run.
- **AC-S38-11** — *G8.* Given only `tests/test_x.py` edited, then `test_x` runs and every other declared module is named
  skipped; given a deleted test module, then the run does not fail on the missing name.
- **AC-S38-12** — *G9, SC-016.* Given any selected run, then before the tests start every module not run is named once
  with one reason, and the last line gives the modules selected, the total and the base; a dry run prints the same
  selection and runs nothing.
- **AC-S38-13** — *G10.* Given `make test SKIP="test_matrix"` on a slice branch, then every module but `test_matrix`
  runs and the line says *selection off: SKIP given* (likewise `TESTS` and `FACTORY_BACKENDS`); given `FULL=1`, then
  every module runs.
- **AC-S38-14** — *G13.* Given the root `Makefile` patch a person applies (the cruise guard refuses an iteration's edit
  there), then its `test` and `verify` recipes and its stamp bypass list match the text a test holds, and any change to
  the root `Makefile` on a slice branch makes `make test` run every module. Until the patch is applied the tests that
  need it fail with a message naming it.
- **AC-S38-15** — *G11, D157.* Given the change sets of S06, S08, S33 (merged) and S14 (its branch against its base),
  when the selector's dry run is run on each, then each prints the modules selected out of the total, the backends
  narrowed, the base and one reason for every skipped module, and the demo log records all four as printed, a full
  selection included; given a change under one backend's assets, and separately a change under
  `assets/toolkit/scripts/`, on a slice branch, when `make test` selects and then `make test FULL=1` runs on the same
  commit and machine, then the demo log records both elapsed times, the machine, the commit and the modules selected out
  of the total. No criterion requires a minimum saving.
- **AC-S38-16** — *G11, D157, the brief's one thing that would make this pointless.* Given a fault injected into the
  changed backend asset, and separately into a script under `assets/toolkit/scripts/` a test module loads by path, when
  the full suite and the selected run are each run on that tree, then the full run fails at least one module and every
  module that fails in the full run fails in the selected run.
- **AC-S38-17** — *G12, G14.* S38 selects and does nothing else: no parallelism, and no change to how a test runs.
  `git diff --stat <base> -- assets src/slipwai catalog.json` is empty at the slice's end, and `VERSION` and
  `changelog.d/` are unchanged; anything else goes back as a bump question.
- **AC-S38-18** — *D164, the after-converge gaps pass.* A declared module is held to what it reads by the selector's
  own scan of the tree being selected: every `generate(` call in it or its `tests/` closure is bound to
  `FactoryTestCase.generate`'s signature and resolved per axis, an argument the scan cannot resolve counting as every
  option of its axis; `refuse(`, the launcher and `slipwai.cli` count as every option of every axis; an in-process reach
  into the repository its `reads` does not name voids the declaration, which `held()` names and the module then runs;
  a reads-only declared module is run under an audit hook that fails on any opened path its `reads` or a run-everything
  row does not cover; and every asset path `src/slipwai/` reads reaches every module that imports `slipwai`. Nothing in
  `tests/support.py` changes and no module runs twice.

### S39-benchmark-elapsed (method slice)

**Gaps reviewed** 2026-10-06, cruise iteration 24, `drive-gaps` (read only) with the host's own D159: FR-049, FR-057,
S39's split and graph rows against D129, D130 and D132 (the owner's), S37's row that reads these measures; against
`assets/toolkit/scripts/agents/benchmark.py` (its copy under `delivery/scripts/agents/` read only), its tests, the 16
slice records and the feature record, the S08 and S14 worktree records, `specs/cruise-log.jsonl`, the register, the
`drive.md` and `cruise.md` passages that open and close entries, and the session transcripts' subagent metadata. Found
and written back: no record holds *ready* or *accepted* as a moment, so both are derived from git (the split commit and
the last dependency's register row; the slice's own register row); S08 merged before its own Phase 4 finished, so
*merged*, *demo accepted* and *done* are three moments; the overview heading prints summed stage time as if it were
elapsed, which FR-049 forbids once slices overlap; rework after an `implementation` or `behaviour` demo is not counted;
one session's transcript serves every concurrent slice and the delegate-type rule hands one slice's lines to another's
bracket, while a subagent's `meta.json` names the `drive-slice` that spawned it; brackets kept in a worktree and on the
integration branch do not see each other; no decision carries a tier yet (S26's `Reversibility:` line), so FR-057's
metrics read unknown until it does (D132 keeps them here); old records stay readable (D65).

Unless a criterion says otherwise, *ready* is the later of the commit that added the slice to `story-split.md` and the
commit that added the register row of its last dependency; *accepted* is the commit that added the slice's own register
row; *stage time* is what today's `wall` column sums; *elapsed* is accepted minus ready.

- **AC-S39-1** — *G1.* Given S08's history (demo 3 accepted, merged at `3138416`, adversary fixes after it, its register
  row added later), when the benchmark reports it, then elapsed runs from its ready commit to its register-row commit,
  and the demo-accepted and merge moments are shown inside that interval; before the row exists, elapsed reads *open
  since <ready>*, never a number.
- **AC-S39-2** — *G2, the split row's criterion.* Given a slice that waited on a sibling's merge, when its record is
  reported, then elapsed, accumulated stage time and waiting by cause — *dependency* (a sibling's merge in split order or
  a person's patch the slice needs), *worker* (no bracket of the slice open, or outside any iteration), *review* (a park
  ending `stopped: human` up to the next iteration, a demo waiting on a person), *integration* (merge to register row,
  the full gate inside it, timed by a new host-bracketed `gate` stage) — are separate numbers, each read from a record
  (git, `specs/cruise-log.jsonl`, `decisions.md`, the brackets), and the causes plus *unattributed* plus the union of the
  slice's brackets equal elapsed, to the second. *D167:* review and dependency count only what a record names; a park whose cause no record says (`stopped: human`, `parked:`) is time *a person held the run, cause unrecorded*, inside *unattributed* and named there, never guessed as review.
- **AC-S39-3** — *G3.* Given a skipper bracket nested inside an `implement` bracket of the same slice, then the slice's
  worked time counts that interval once; given an entry cut off at the next iteration's start hours after its last
  transcript line, then its stage time ends at that last line and the report says so; the `wall` column is renamed
  *stage time*, and no heading reports a sum of stage time as elapsed.
- **AC-S39-4** — *G4.* Given S08's record (demo 1 `implementation`, implement, demo 2 `implementation`, implement, demo 3
  `accepted`), then its rework is those two `implement` entries with their tokens and seconds, counted inside S08's total
  cost; the adversary-fix `implement` after acceptance is not rework. Rework is every entry after a `behaviour` or
  `implementation` demo up to the next demo's close.
- **AC-S39-5** — *G5.* Given two slices' `implement` brackets open at once in one session, each with `drive-implement`
  delegates spawned by its own `drive-slice`, then each request is counted in exactly one slice's record — the one whose
  `drive-slice` spawned it, read from the subagent's `meta.json` and the spawning `drive-slice`'s description, which
  `drive.md` and `cruise.md` fix as `drive-slice <id>`; across every record in the project, worktree copies after merge
  included, no request is counted twice; a line that ties to no slice is counted in the feature's *shared* bucket and in
  no slice.
- **AC-S39-6** — *G6.* Given S06, S08 and S14 overlapping in iterations 23–24, then the feature's elapsed (first slice
  ready to last slice accepted) is less than the sum of their stage times, the two appear under different names, and the
  union of the slices' intervals is shown as *time with any slice in flight*.
- **AC-S39-7** — *G7, FR-057, D132.* Given a decision log with no `Reversibility:` lines, when decision health is
  reported, then the escalation share, the misclassification rate and the median wait by tier each read *unknown* with
  that reason, and no figure is printed; given a fixture log of 20 easy or guarded entries with 4 escalated to hard, then
  the share reads 20% and is flagged outside 5–15%; a misclassification rate over 5% is flagged.
- **AC-S39-8** — *G8, D65.* Given the 16 records as committed at `8072724`, when `make benchmark` runs before and after
  S39, then every column S39 does not rename holds the same values, each new figure is derived or reads *unknown — <reason>*,
  and `check-benchmark` warns of no field an old record lacks.
- **AC-S39-9** — *G9, what S37 reads.* Given any record, then `benchmark.py --json` carries `elapsed`, `stage_seconds`,
  `waiting{dependency, worker, review, integration, unattributed}`, `rework{seconds, tokens}` and `cost{tokens, shared}`,
  each a number or `{"unknown": "<reason>"}`, with the record each was read from; the page's reading notes say in one
  sentence how elapsed differs from stage time. *D167:* `--json` also carries `unattributed_person` beside `waiting`, not inside it, so the five keys still sum to elapsed less worked; *D166:* each entry carries `recorded_seconds`.
- **AC-S39-10** — *G10.* Given a generated project with one slice driven by `/drive` and no `specs/cruise-log.jsonl`,
  when `make benchmark` runs, then elapsed and stage time are reported, every waiting cause the project has no record for
  is *unattributed*, and it exits 0 with no warning about the cruise log. *D167:* a demo is a person's (review) only when its entry was closed with `outcome=` and carries no `driver` signal; a cut-off demo is stage time.
- **AC-S39-11** — *G11.* Given the real records of iterations 23–24 (S06, S08, S14, S14's worktree record included),
  when the demo runs the asset copy of the script in place, then S08's elapsed, stage time and waiting by cause match
  figures recomputed by hand from git and the cruise log; the tokens over all records plus the shared bucket equal the
  session's distinct-request total; and S08's `implement` of 17:17–18:53Z no longer holds S06's or S14's delegates. The
  timings are reported, not judged against a threshold.
- **AC-S39-12** — *G12, AGENTS.md.* MINOR, with a fragment: given a project generated by the previous release with
  records from before S39, when `slipwai migrate` runs and then `make benchmark`, then it succeeds and the catch-up names
  what changed and that nothing must be redone; the new derivation lives in a module of its own beside `benchmark.py`
  under `assets/toolkit/scripts/agents/`. In this repository, attribution across concurrent slices stays by delegate type
  until a person runs `migrate`.

### S07-scoped-checks

**Gaps reviewed** 2026-10-07, cruise iteration 27, `drive-gaps` (read only) with `drive-skipper` for D171, D172 and
D173 and the host's own D170: FR-022, FR-023 as revised, SC-009, S07's split and graph rows against D110 and D111, S06's
record (`assets/toolkit/scripts/verify_scoped/`, ADR 0004) and its criteria, the owner brief's priorities 1, 2 and 5;
against the four method-file checks, the four scripts `check-agents` runs, `check-ux-gates.py`, `table.py`, `record.py`,
`scoped_targets.py` and `tests/test_verify_scoped_record.py`. Found and written back: the four have no row in S06's
table, so each runs on every scoped run today; the table's literal-path scan cannot see what `check-speckit` and
`check-agents` read through manifests, `.specify/integration.json` and `registry.json`, so those paths are worked out
at run time from both trees (D172); `check-extensions` reads whether a web deployable's directory exists, and
`check-constitution` whether any `specs/*/spec.md` exists, which only a directory input can say (D172: `specs/`); a row
with no file inputs is treated as unchanged when FR-023 says it runs; *unreadable* had no definition; the `check-ux-gates`
default had no base, no rule for the trunk, a detached `HEAD` or CI, no precedence and no way back to every preview
(D170, D171); `changed_since` detects renames and splits on whitespace; per-check stamps were handed to S07 by S03's
section and are moved to the Parking Lot (D173). No environment variable is read by the four under `--check`.

- **AC-S07-1** — *SC-009.* Given a slice branch with a baseline and one changed file under a service's `src/`, when
  `make verify-scoped` runs, then `check-agents`, `check-speckit`, `check-extensions`, `check-constitution` and
  `check-ux-gates` are each named as skipped because none of their inputs changed; with the file under a web app's
  `src/` instead, `check-ux-gates` runs and renders only the previews that file reaches.
- **AC-S07-2** — Given each input the four declare — `check-agents`: `.specify/integration.json`, `models.json`,
  `drive.json`, `cruise.json`, `skills/`, `commands/`, `agents/`, `AGENTS.md` and the paths of AC-S07-4;
  `check-speckit`: `.specify/integrations/`, `.specify/presets/`, `.specify/memory/constitution.md` and the paths of
  AC-S07-3; `check-extensions`: `.slipwai/extensions.json`, `AGENTS.md` and AC-S07-5; `check-constitution`: `specs/`,
  `.specify/memory/constitution.md`, `.specify/memory/.constitution-template.json`,
  `.specify/templates/constitution-template.md`, `.specify/presets/` — when that input alone changes, then exactly the
  checks declaring it run, each naming that path as its reason.
- **AC-S07-3** — Given a path only a Spec Kit manifest or a preset's `preset.yml` lists, in the working tree or at the
  base, when it changes, then `check-speckit` runs; given a manifest or `preset.yml` that does not parse, or names a
  path outside the project (absolute or through `..`), then `check-speckit` runs with *no recorded inputs* and claims
  nothing (D172 limit i).
- **AC-S07-4** — Given each installed integration, when its context file, hooks file, skills, commands or agents
  directory (from `registry.json`) changes, then `check-agents` runs; an integration file that does not parse gives
  `check-agents` no recorded inputs and no claim.
- **AC-S07-5** — Given a web deployable's directory added or removed without a `project.json` change, then
  `check-extensions` runs.
- **AC-S07-6** — Given the template constitution and a branch adding the first `specs/<f>/spec.md`, then
  `check-constitution` runs and fails, as `make verify` does (D172).
- **AC-S07-7** — Given a declared file that exists but cannot be read, or a table row with no file inputs, then the
  check runs and says why.
- **AC-S07-8** — Given every starter shape, a behavioural test flips each declared input and shows a check's result
  can change only through what it declares; the literal-path scan covers all four of `check-agents`' scripts; each of
  the four records `variables: []`; and a factory test fails when any gate script outside the four that reads
  `registry.json` or a `*.manifest.json` is not one that always runs or claims nothing (D172 limit ii).
- **AC-S07-9** — Given a changed ignored projection, then the run is the full gate with or without a baseline
  (AC-S06-9); on the trunk, under a CI marker, or on a branch that is not `slice/<id>`, `verify-scoped` is `make verify`;
  `make check-<name>` always runs the check in full; on `main`, `make verify`'s findings are unchanged (SC-007).
- **AC-S07-10** — Given `verify-scoped record`, then the four print with input objects and `claims: true`, the record
  keeps `schema: 1` and gains no key (D172).
- **AC-S07-11** — *D170, D171.* Given a `slice/<id>` branch outside CI with `UX_GATES_SINCE` unset or empty, then
  `check-ux-gates` scopes from S06's base, the unpushed span of the local trunk included, and names that base in one
  line; on the trunk, any other branch, a detached `HEAD`, under a CI marker or where the base cannot be found, it
  renders every preview and says why; an explicit `UX_GATES_SINCE` beats the default; `UX_GATES_SINCE=all` renders every
  preview and says so in one line; a ref named `all` is passed by its full name. A stamp or baseline written by a
  default-scoped run records the base it used, never the word `all`, so it cannot vouch for an all-previews run.
- **AC-S07-12** — Given a renamed stylesheet, or a preview path containing a space, then the affected preview is
  re-rendered (`--no-renames`, NUL-separated names).
- **AC-S07-13** — Given the slice, then the generated `Makefile` and `rules.json` are byte-identical before and after
  it; the default lives in `check-ux-gates.py`.
- **AC-S07-14** — Given the scoped page and `docs/verification.md`, then they describe the four checks' scoping and the
  default, with one sentence on when to set `UX_GATES_SINCE=all`; the fragment claims MINOR (a new value of a setting,
  D171), `VERSION` stays where it is, and its catch-up note says a slice branch now renders fewer previews and how to
  get them all.

### S26-reversibility-line

**Gaps reviewed** 2026-10-07, cruise iteration 27, `drive-gaps` (read only) with `drive-skipper` for D174 to D178: User
Story 8, FR-029, FR-051, FR-056 and FR-057, S26's split and graph rows against S27's and S28's, D54, D60, D62, D65,
D132, D159 and D168; against `check-decisions.py`, `DECISION_ENTRY` in `src/slipwai/project/cruise_record.py`, the
skipper's brief (`cruise_agents.py`), the cruise command, `measures.py`'s decision-health reader and the differential
test. Found and written back: nothing writes, reads or checks the line today except S39's reader, and an unknown label
passes silently; most decisions are written before any commit, so the facts describe what accepting the decision would
change and are declared by its writer, the gate re-deriving the tier (D174, ADR 0007 at Proposed); a generated project
has no committed list of what `migrate` propagates (D175: one is generated and migrated); FR-051's *unrecognised field*
and its size-and-urgency rule conflict when read literally (D176); a missing line is a note, never a refusal, which is a
person's question beside D60's (D176); *tier* in FR-056 is the reversibility tier (D177) and *same shape* is the same
deciding reason (D178); `check-decisions.py` is at 699 lines, so the line's rules live in a module beside it.

- **AC-S26-1** — Given the facts {contract, schema, permission or authentication, customer-visible, data export, CI
  workflow, migrate-propagated file: all `no`; behind a flag: `yes`; rollback: `trivial`} and a slice-local scope, when
  scored, then the line reads `easy`.
- **AC-S26-2** — Given each `hard` fact set to `yes` on its own, then the tier is `hard`, one test per rule.
- **AC-S26-3** — Given `rollback_complexity` `days` or `needs-migration`, then `hard`; given `hours`, then `guarded`.
- **AC-S26-4** — Given a known fact missing, or carrying a value the fact does not accept, then `hard`, the fact named
  on the line (D176 rule 4).
- **AC-S26-5** — Given two fact sets that differ only by a `size` or `urgency` key, then neither gets a tier: the
  scoring verb and the gate refuse the line as malformed, naming the key (D176 rule 3).
- **AC-S26-6** — Given the D54 fixture (a CI workflow line propagated by `migrate`, no commits), when scored from the
  facts it declares, then `hard`.
- **AC-S26-7** — Given an entry with no commits, then it is scored from declared facts about what the decision would
  change; its *Written to* paths never lower the tier; dependants are read from its `Scope:` line (D174).
- **AC-S26-8** — Given a migrate-propagated fact, then it is checked against `delivery/.written` in an adopted
  repository and against the committed list `generate` writes and `migrate` rewrites in a generated project; a project
  without the list scores the fact `hard` until `migrate` writes it (D175).
- **AC-S26-9** — Given a well-formed line, then `check-decisions` accepts it; given a malformed tier, an unknown key, a
  second `Reversibility:` line, a skipped escalation step (`easy → hard`), or a tier that disagrees with its facts under
  the rules version the line names, then it refuses with one line naming the entry and the field.
- **AC-S26-10** — *D65, D176.* Given a log with no `Reversibility:` line anywhere, then the gate's exit code and
  findings equal the earlier checker's (the differential test extended); given an entry without the line after one that
  has it, then the gate prints one `note:` naming the entry and the scoring verb, and exits 0.
- **AC-S26-11** — Given old lines scored under rules v1 and the rules now at v2, then the gate passes them unchanged.
- **AC-S26-12** — Given `DECISION_ENTRY`, then the cruise command, the owner-brief template and the skipper's brief all
  show the line, and both the host and the skipper are told to run the one shipped scoring verb.
- **AC-S26-13** — Given lines the classifier writes, escalation chains included, then `measures.decision_health` reads
  their tiers and escalations unchanged; a spelling changes only in `SPELLING`.
- **AC-S26-14** — *D177.* Given the skipper's brief, then it escalates one reversibility tier at a time, writes each
  step on the line, never lowers a computed tier, and never leaves a question in a diff or a note instead of escalating.
- **AC-S26-15** — *D178.* Given three standing entries in one feature decided by the same reason, then the skipper's
  entry carries a `Proposed rule:` line citing at least two earlier standing ids of the feature, and never edits the
  owner brief; the gate refuses such a line citing fewer than two ids or an id that is not a standing entry of the
  feature, and never refuses an entry for lacking it; every skipper brief carries the feature's list of entry headings.
- **AC-S26-16** — Given a project generated by the previous release, when `migrate` runs and then `make verify`, then it
  passes; the fragment claims MINOR and its catch-up note names the new line, the committed list, the note for a
  missing line, and that the project's owner brief keeps the old entry shape until edited by hand.

### S43-test-declarations

**Gaps reviewed** 2026-10-07, cruise iteration 27, `drive-gaps` (read only) with `drive-skipper` for D179 and D180 and
the host's own D181 and D182: D169 (the owner's), FR-048, SC-016, S43's split and graph rows, S38's records, its
adversary entries and D156–D158, D164, D165; against `scripts/select_tests/` (`declarations.py`, `generation.py`,
`choose.py`, `rules.py`), `tests/support.py`, the 19 declaring modules, `test_select_tests_real_declared.py`,
`test_select_tests_real_audit.py`, `check-structure.py`'s budget and the CI workflow's matrix jobs. Found and written
back: S38 recorded only whole-suite totals, so the ranking needs one measured run at the slice's start (D180); under
today's rules declaring every module as narrowly as its source allows still selects about 296 of 373 on a Go change,
because the join is per imported test file and about 96 modules inherit `test_replay`'s, `test_adopt`'s,
`test_migrate`'s or `test_add_service`'s launcher routes through a helper they borrow, so shared helpers move into
declared helper files and `CATALOG["backends"]` loops switch to `backends_under_test()` with CI's coverage unchanged,
and the selector's rules stay (D179); the audit of reads-only modules stays (D181); 15 minutes is acceptance (D182);
shared generation code already selects every module; eleven test files sit at the 350-line budget. No bump: nothing
under `tests/` or `scripts/select_tests/` is in the wheel.

- **AC-S43-1** — *D180.* Given the slice's base commit, before any declaration is written, when one full run with
  per-test durations is made on the reference machine (12 cores, no CI variable, nothing else running), then a
  per-module runtime table naming the commit, the machine, the module count and the run's wall-clock total is committed
  to the slice's records, and the declaration order follows it; a run that cannot finish green stops the slice.
- **AC-S43-2** — Given each module or helper newly carrying `TEST_SELECTION`, when `declarations.held()` runs on the
  real tree, then it names none of them, and each appears in a `real_*` list.
- **AC-S43-3** — Given each (axis, option) any declaration names, when one real path that pair claims is the change
  set, then every module whose source generates that option, or whose reads match the path, is selected — the
  expectation derived from `generation.facts`, not typed.
- **AC-S43-4** — Given a copy of a declared module whose declaration omits an option its source generates, then the
  selector does not skip it: the declaration is void and the module runs.
- **AC-S43-5** — Given a change under `src/`, `catalog.json` or `assets/backing-services/prune.py`, then every module
  runs.
- **AC-S43-6** — *D169, D182.* Given one Go app file changed on the slice branch, when `make test` runs inside an S39
  `gate` bracket, then it finishes in under 900 s on the reference machine, reported against AC-S43-1's total; a miss is
  a `behaviour` demo, and relaxing the target is a person's word.
- **AC-S43-7** — Given a module left undeclared, then a committed list names it with the selector's own reason.
- **AC-S43-8** — *D180.* Given the demo's planted Go fault, then the one full run of the demo is made on the faulted
  tree, and every module that fails there also fails in the selected run.
- **AC-S43-9** — *D179 condition 1.* Given the slice's last commit and its base, then a full run's test ids are the
  same set: none lost, none renamed away, none newly skipped.
- **AC-S43-10** — *D179 condition 2.* Given each module switched to `backends_under_test()`, then the set of (module,
  backend) pairs CI's jobs run is the same before and after; a module that cannot be shown so keeps its loop.
- **AC-S43-11** — Given `make check-structure`, then it passes, no test file over 350 lines; the selector's rules,
  `rules.py` and the audit module are unchanged (D179 condition 3, D181).
