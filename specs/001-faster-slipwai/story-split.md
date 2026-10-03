# Story split — Faster Slipwai (001-faster-slipwai)

Written by `/cruise` iteration 1 from `spec.md`, `.specify/product-owner.md` and the convergence map
(`delivery/docs/convergence.md`). The PRD the owner brief links is a Claude Docs artifact this session could not
open; where the spec and the brief are silent, the split says so rather than guessing what the PRD says.

## Parent

**Actor:** a developer who ran `slipwai generate` or `slipwai adopt` and now drives or cruises that repository
with coding agents. **Need:** a delivery loop whose time per feature grows like S·log S instead of S², while
every gate still runs on every change before it reaches `main`. **Outcome:** slices reach `main` sooner and the
gate stays trustworthy; the one thing that would make the work pointless is a faster loop that lets through what
today's gate catches. **Constraint:** the loop pays its gate serially about three times per slice over the whole
repository, merges slices one at a time in split order, re-renders every diagram on every merge, and its runner's
bookkeeping grows with the log. Every change lands in the files the factory writes (`assets/`,
`src/slipwai/project/`) and reaches a generated project through `slipwai migrate`; this repository is a user of
the factory like any other, and a second actor, the factory maintainer, needs each change to land as a release
with its level named in `changelog.d/`.

## Recommended First Slice

`S00-run-path` is a method slice the ladder requires before any slice changes code that was here (Pin stage: an
application nobody has proved starts refuses every slice). The first **product** slice is `S01-gate-walks`: the
generated gate stops walking `.venv`, `node_modules`, `target/`, `__pycache__` and `.git`, and reads
`project.json` once.

Why this first: the owner's order is walks and logs, then stamps, then `-j`, then the scoped gate, then the
merge tree. Pruning walks needs no design decision, is a PATCH (the same answers, generated better), is
measurable on its own (SC-005: at most 100 entries enumerated on the skeleton), and its demo — generate a Python
starter, run its gate, read what it enumerated — is the demo path every later slice reuses.

## Split Candidates

| Slice | Value | Includes | Defers | Acceptance Examples | Release Constraint |
|---|---|---|---|---|---|
| `S00-run-path` (method) | The team knows the factory starts and its suite is green before anything changes it | `delivery/survey/running.md` written from a real run of the recorded `smoke` (`./slipwai --version`); one green `make verify` and `make -f delivery/Makefile verify` recorded as evidence, run the way the cruise runner runs it; the tests under `tests/test_cruise_*.py` that spawn `cruise.py` clear `CRUISE_RUNNER` and `CRUISE_ITERATION` from the child's environment, since inherited from an iteration they make `start` refuse and the suite red for no fault of the tree (seen in iteration 1: 7 of 829 red inside the iteration, 0 with the two variables unset); `safety-net: tests-exist → tests-pass` | Nothing it changes in code | Given this checkout, when `./slipwai --version` runs, then it prints `1.5.2.dev0` and `running.md` no longer reads *Not yet proven* · Given this checkout, when `make verify` runs, then it is green with no quarantined test, and the convergence row's evidence names the run | Docs and the map only; nothing reaches a generated project |
| `S20-slice-scope-root` | A slice branch in a repository adopted at its root passes the slice-scope gate | `assets/toolkit/scripts/check-slice-scope.py`: `Scope.owning_app()` recognises a deployable whose recorded `path` is `.` as owning every path not under another deployable, so `tests/`, `scripts/` and the survey pages on a `slice/<id>` branch are inside the one app rather than *outside every deployable* (D13; found by D12's read-only run: 319 violations on this checkout, every one the adoption's or S00's own file). Also `assets/toolkit/scripts/check-decisions.py` and `assets/toolkit/scripts/agents/benchmark.py` read a done slice's id from the register as the whole first cell (today `[A-Za-z]+\d+` cuts `S00-run-path` to `S00`, so an adversary row headed with the full id is *missing* and `check-benchmark` looks for `slices/S00/`) — D17, found at S00's archive | Any other change to what the checker holds | Given a project adopted at `.` with one deployable, when a `slice/<id>` branch changes a test file under `tests/`, then `make -f delivery/Makefile check-slice-scope` is green · Given the same project, when the branch changes `Makefile`, then it is still a violation · Given a project with deployables under `apps/`, then the checker's answers are unchanged | PATCH; snapshot + `migrate` — this repository sees it only after a person runs `slipwai migrate` (D9). Placed second in split order, numbered last |
| `S21-refresh-keeps-owned-files` | `slipwai adopt --refresh` leaves a repository's own settings and the owner brief alone | `src/slipwai/resurvey.py` (and whatever renders them): a refresh regenerates the pages the record drives and never rewrites `.specify/cruise.json` (reset to `enabled: false`, `max_iterations: null` — a run's committed settings, changed only through `/cruise-settings`) or `.specify/product-owner.md` (human-owned by its own first lines; reset to the template with every section a placeholder). Found by S00's T005 on this repository (D15): both were rewritten and reverted by hand before commit. Also re-derives `strategy.before` from the convergence rows at refresh, so `delivery/docs/change-strategy.md` stops saying a prerequisite is unmet after the row moved (D16; seen on this repository after S00); and, so that this cannot show a prerequisite as met when it is not, a person's Path to production row gives way to a person's lower `release.path` at a refresh (D28; found by this slice's adversary pass) | Any other change to what a refresh writes | Given an adopted repository with `/cruise` enabled and an owner brief filled in, when `slipwai adopt --refresh` runs, then `git status` shows neither file changed · Given the same repository, then `delivery/docs/convergence.md`, `delivery/commands/ground.md` and `delivery/survey/structure.md` are still regenerated | PATCH; snapshot + `migrate`. Placed third in split order (after `S20`), numbered last: until it lands, every `/survey` inside a cruise run has to be followed by a revert of those two files, as S00's T005 was |
| `S22-slice-scope-base` | A slice branch cannot empty its own scope check by minting a base | `assets/toolkit/scripts/check-slice-scope.py` `merge_base()`: the base is where the branch left the trunk — `ci.branch` as the working tree's `project.json` records it where that is a usable name with a ref (never a `slice/<id>` name), else `main`, else `master` — read from `refs/heads/` and `refs/remotes/origin/` by full name so a tag cannot shadow it; on a pull request the forge's target branch is a second candidate and the oldest base across the two names wins (D30); a developer's checkout with no usable base fails on a `slice/<id>` branch with what to fetch instead of holding nothing, and a forge's detached pull-request checkout with none keeps its exit 0 but says the slice was NOT checked and which workflow key would make it (D31). Found by S20's adversary pass (A3 in `adversary-log.md`, D23): HIGH, open until this lands | Any other change to what the checker holds | Given a slice branch with a host-surface change committed, when a `master` branch, a tag named `main` or an `origin/master` ref is placed at its head, then `make check-slice-scope` still refuses the change · Given a developer's shallow clone of a slice branch with no trunk ref, then the check fails saying what to fetch (amended by D31: a forge's depth-1 pull-request checkout says *NOT checked* and exits 0 until `S24-ci-fetches-slice-base`) · Given a project whose `main` moved locally and is not yet pushed, then the newest of `main` and `origin/main` is still the base, as today | PATCH; snapshot + `migrate`. Placed fourth in split order (after `S21`), numbered last |
| `S23-refusal-in-subdirectory` | A refresh never writes over uncommitted work where the project sits in a subdirectory of its git repository | `src/slipwai/uncommitted.py` `changed()`: `git status` paths are relative to the repository's top while every path a run writes is relative to the project, so `refuse_foreign` never matches and `stamp` records nothing when `project.json` is not at the top — `adopt --refresh`, `--confirm` and `--decline` then write over an uncommitted edit to any listed file in silence. Found by S21's adversary pass (A1 in `adversary-log.md`, D29): MEDIUM, older than S21, open until this lands | Any other change to what the refusal protects | Given a project adopted in `sub/` of a repository, when a listed file under it holds an uncommitted edit and `slipwai adopt --refresh` runs there, then it refuses naming the file and the edit stands · Given the same repository, when slipwai itself left the change, then the refresh runs · Given a project at the top of its repository, then every answer is today's | PATCH; snapshot + `migrate`. Placed fifth in split order (after `S22`), numbered last |
| `S24-ci-fetches-slice-base` | A slice pull request's CI holds the slice to its scope instead of saying it could not look | `src/slipwai/project/ci_workflows.py` (the generated `verify` job's checkout) and `src/slipwai/project/adopted_ci.py` (the adopted delivery workflow, and its GitLab job) fetch the history `check-slice-scope` needs; the checker's *NOT checked* answer in a forge's checkout — a detached pull-request checkout (D31, answer 3) or any run with a CI marker set (D32) — then becomes a failure. The CI half of S20's adversary finding A3, open until this lands. It changes what CI checks (owner brief, *Always ask a person*, first item; D31), and **the owner approved it on 2026-10-03 (D39)** | The container jobs' depth-1 checkout where they do not run `check-slice-scope`; any change to what the checker holds | Given a generated project's slice pull request with a host-surface change, when CI's `verify` job runs, then `check-slice-scope` refuses it · Given a pull-request checkout that still has no trunk history, then the check fails naming the workflow key · Given a pull request from a branch that is not `slice/<id>`, then every answer is today's | PATCH, with a catch-up note where a taken-over workflow is not rewritten by `migrate`; snapshot + `migrate`. Placed after `S01-gate-walks` by the owner (D39), numbered last; approved by the owner on 2026-10-03 (D39) for its effect on `check-slice-scope`. **Blocked since iteration 8 on a person's approval (D54):** the same fetch gives `check-migrations` and `check-flags` a base in CI, so on every pull request they would start refusing a contract whose expand is new in the same pull request and a new flag seeded other than `off` — a change to what CI checks that D39's words do not cover. The third example (*every answer is today's*) is rewritten only once that is approved |
| `S25-refusal-when-git-cannot-answer` | A refresh that cannot ask git what changed says so instead of writing over uncommitted work | `src/slipwai/uncommitted.py` `changed()` and its callers: where the project's directory is inside a git work tree and `git status` fails — a bad value in the repository's config, *dubious ownership* in a container, an unreadable index — `adopt --refresh`, `--confirm` and `--decline` refuse with git's own first line; where it is in no repository they run as today. Found by S23's adversary pass (B1 under `## S23` in `adversary-log.md`, D44): MEDIUM, older than S23, open until this lands. Its neighbours, to be decided in its own gaps stage: `git` not installed (D41) and `GIT_DIR` exported alone (D40) | The other findings of that pass (Parking Lot) | Given an adopted project whose repository's config holds `color.status maybe`, when a listed file holds an uncommitted edit and `slipwai adopt --refresh` runs, then it refuses naming what git said and the edit stands · Given a project copied out to a directory in no repository, then the refresh runs as today · Given a readable repository, then every answer is today's | PATCH; snapshot + `migrate`. In the pool behind the PRD's slices (D39), numbered last |
| `S01-gate-walks` | A generated gate stops reading what it never needed | FR-004: `check-imports` and `check-migrations` prune `.venv`, `node_modules`, `target/`, `__pycache__`, `.git` before descending and read `project.json` once; FR-022 (part): `check-codegraph` hashes only files git reports changed since the last sync and runs the SQLite integrity check in CI only; SC-005 | Per-branch scoping of the UX gate (→ `S07`); the verify stamp (→ `S03`; `check-codegraph`'s own memory of its last whole comparison is this slice's, D46) | Given the generated Python skeleton, when `make check-imports` runs, then it enumerates at most 100 entries and reports the count on its pass line (an entry is one name a directory listing returns, summed over the run; D47) · Given a skeleton with a populated `.venv` and `node_modules`, when `check-migrations` runs, then its findings equal the run without them and it never descends into either; `target` is pruned only beside a `pom.xml` (D45) · Given one source file changed since the gate's last whole comparison, when `check-codegraph` runs on a `slice/<id>` branch outside CI, then it hashes that one file; on the trunk, any other branch and in CI the run is today's, integrity check included (D46) | PATCH; lands on `main` as a `.dev` snapshot and reaches a project only through `slipwai migrate` run by its maintainer |
| `S02-runner-bookkeeping` | Cruising at iteration 50 costs what iteration 1 did | FR-015: the runner tails `cruise-log.jsonl` and the stream from a stored offset, fingerprints `specs/` by path and content, reading a file only where its size, times or identity moved (D57), drift-checks only changed files — `health()` through the gate's memory, on any branch outside CI (D59); FR-024: `controls_signature()` reads each control's content once per iteration unless it changed, the comparison still of content (D56), one codegraph sync per iteration (pinned as it is; D59); FR-016: a `Scope:` line on decision entries, `check-decisions` accepts it, the skipper brief carries in-scope and global entries only; SC-006 | Result contracts (→ `S14`); a further sync inside an iteration tied to the changed files a delegate reports in its result contract, in place of the unconditional sync after every delegate's return, and handing those reported files to the runner's comparison as candidates (→ `S14`; D59); the skipper seeing a neighbour's decisions through the Slice graph (→ `S13`; D60) | Given a 50-entry log, when one runner process runs two iterations, then entry 51's `bookkeeping.log_bytes` is the seeded log's size and entry 52's is 0, the same as over a 1-entry log (D58: a count of bytes, never a wall-clock ratio) · Given an unchanged `specs/` tree a runner process has fingerprinted once, when `fingerprint()` runs again, then it opens no file for content (D57) · Given 100 standing decisions of which 4 name the slice's scope, when the skipper is briefed, then it receives those 4 and the ones marked global · Given an entry without `Scope:`, when `check-decisions` runs, then it still passes (the line is optional until every writer adds it; every writer adds it in this slice, and making absence a finding is a person's — D60) | MINOR, one fragment: the `Scope:` line and the entry's `bookkeeping` object are new things an entry may carry (D58, D60), the runner's changes alone would be a PATCH; raises `VERSION` to `1.6.0.dev0`; snapshot + `migrate` as above |
| `S03-verify-stamp` | The gate returns in under a second on a tree it already passed | FR-001: `make verify` records a success stamp keyed by git tree hash, gate-script hash and recorded tool versions, reuses it on an unchanged tree saying so in one line, honours `VERIFY_FORCE=1`, and never trusts a stamp in CI (owner priority 5); SC-001 | Per-check stamps (→ `S07`) | Given a tree the gate passed, when `make verify` runs again unchanged, then it prints the stamp it reused and exits 0 in under 1 s · Given a one-character source change, when `make verify` runs, then the full gate runs and a new stamp is written · Given `VERIFY_FORCE=1` on a stamped tree, then the full gate runs · Given a changed `scripts/check-*.py` or a new ruff version, then the stamp is invalid and the full gate runs · Given `CI=true`, then no stamp is read | MINOR (a new variable, a new file the gate writes); first slice to raise `VERSION` to `1.6.0.dev0`; snapshot + `migrate` |
| `S04-parallel-gate` | The gate's independent checks run at once and each toolchain syncs once | FR-002: read-only checks declared so `make -j verify` runs them concurrently with the serial run's results; writers `.NOTPARALLEL` locally (edge case: anything writing `.specify/`); FR-003: `./scripts/verify` syncs each toolchain once per invocation, `check-drawio` skips `npm install` when the installed tree matches the committed lockfile | xdist (→ `S05`) | Given the skeleton, when `make -j verify` runs, then every check the serial run ran runs, in any order, and the exit code matches · Given a Python starter, when `./scripts/verify` runs, then `uv sync` runs once · Given an installed `node_modules` matching the lockfile, when `check-drawio` runs, then it skips the install and says so | PATCH; snapshot + `migrate` |
| `S05-xdist` | The root gate's tests run across cores where the project says they may | FR-009: pytest runs with xdist where `project.json` marks the project parallel-safe (default on for new projects, one-line opt-out); other backends record what their runner already does | Scoped test selection (→ `S06`) | Given a new Python project, when `make verify` runs at the root, then pytest runs with `-n auto` and the pass/fail set equals the serial run's · Given `"parallelSafe": false` in `project.json`, then pytest runs serially · Given a TypeScript, Go or Java starter, then the matrix test still passes and the recorded test command is unchanged | MINOR (a new `project.json` key with a documented default); snapshot + `migrate` |
| `S06-scoped-gate` | A slice branch runs the gate for what it touched | FR-006: `make verify-scoped` exists, equals `make verify` on `main`, and on `slice/<id>` runs per-file checks on changed files, mypy incrementally, and tests of touched contexts plus `depends_on` neighbours' contract tests (neighbours read from the slice graph or `model.yaml`); FR-007: the drive ladder calls it at slice start and before the push, the full gate once at the merge root | Neighbours declared by `provides`/`requires` (→ `S16`); per-check skipping (→ `S07`) | Given a slice branch that changed one context, when `make verify-scoped` runs, then only that context's files are linted and only its tests and its neighbours' contract tests run · Given `main`, when `make verify-scoped` runs, then it is `make verify` · Given the same tree, then the full gate's findings before and after are identical (SC-007) | MINOR (a new target); snapshot + `migrate`; the merge root and CI still run the full gate — constitution I |
| `S07-scoped-checks` | The method-file and preview checks skip what did not change on a branch | FR-023: `check-agents`, `check-speckit`, `check-extensions`, `check-constitution` run only when their inputs changed since the stamp on a branch, always on `main` and in CI; FR-022 (rest): `check-ux-gates` defaults `UX_GATES_SINCE` to the merge-base on `slice/<id>` and to everything on `main`; SC-009 | — | Given a slice branch touching one source file, when `make verify-scoped` runs, then the four method-file checks report they were skipped and `check-ux-gates` renders only that file's previews · Given `main` or `CI=true`, then all four run | PATCH; snapshot + `migrate` |
| `S08-scoped-mutation` | A slice's mutation run is proportional to its change | FR-008: `make mutation` scopes to the diff against merge-base for every backend; `make mutation-full` keeps the whole-module run | — | Given a branch that changed one production module, when `make mutation` runs, then only that module's mutants run, for Python, TypeScript, Go and Java starters · Given `make mutation-full`, then the whole module runs as today | MINOR (a new target); snapshot + `migrate` |
| `S09-phase4-fanout` | After a fan-out, each slice's Phase 4 runs in its own worktree at the same time | FR-010 (part): adversary, mutation and the scoped gate per slice, concurrently, in the slice's worktree; the ladder text and the runner's stream say so | The merge tree (→ `S10`) | Given 8 ready slices on a generated project, when the fan-out finishes, then the cruise stream shows adversary, mutation and scoped-gate steps overlapping in time, one set per slice | MINOR (the ladder changes); snapshot + `migrate`; `main` still moves one merge at a time until `S10` |
| `S10-merge-tree` | A fan-out converges through a merge tree instead of one merge after another | FR-010 (rest): passing slices merge pairwise into integration branches with fan-in `drive.json.merge_fanin` (default 2), each running the scoped gate on its union; the root runs the full gate once; `main` only fast-forwards; an unresolved conflict parks its subtree only; FR-011: `make model` and `make model-drawio` once at the root; SC-002, SC-003 | — | Given 8 passing slices, when they merge, then the longest dependent chain is 3 and the root runs the full gate once · Given two slices whose changes conflict, when the later-in-split side rebases and fails, then that subtree parks and the others continue · Given a fan-out that converges, then diagrams render once at the root and `main` fast-forwarded | MINOR (a new `drive.json` setting with a documented default); snapshot + `migrate`; nothing merges to a real project's `main` from here |
| `S11-render-once` | Diagrams render through one browser and only when their source changed | FR-012: `render.ts` opens one browser session per run and re-renders only diagrams whose source changed; SC-004 | Linear model checks (→ `S12`) | Given the 16-slice fixture with one changed slice, when `make model` runs, then one browser launches, two diagrams are rewritten and it finishes in under 2 s · Given a one-slice model, then one browser renders three diagrams as today | PATCH; event-modelling profile only; snapshot + `migrate` |
| `S12-model-sidecar` | The model is parsed once and its checks stay linear as slices grow | FR-005: `model.yaml` parsed once per verify into a sidecar every consumer reads; FR-013: `check.py` cycle detection and `board-plan.ts` frame lookup linear in slices; one file plus a sidecar index, never per-slice files (owner brief: splitting `model.yaml` is a person's call) | One-hop briefs (→ `S13`); contract edges (→ `S16`) | Given a 200-slice synthetic model, when `make check-model` runs, then its time grows linearly with slices · Given one verify run, then `model.yaml` is parsed once and every consumer reads the sidecar | MINOR (a new generated file); event-modelling profile; snapshot + `migrate` |
| `S13-one-hop-brief` | A per-slice stage reads its slice and its neighbours, not the whole model | FR-014: example-map, plan, tasks, implement and converge briefs carry the slice's block and the blocks it reads from or is read by, and nothing else of the model | Logging reads beyond the brief (→ `S17`) | Given slice 16 of the fixture, when the example-map stage is briefed, then the bytes handed to it equal those for slice 1 · Given a slice with two neighbours, then the brief holds exactly three blocks | PATCH; snapshot + `migrate` |
| `S14-result-contract` | Every delegate hands back the same structured result | FR-017: every delegate ends with a fenced `result-contract` block (scope, status, contracts_changed, invariants_checked, tests, decisions, assumptions, unresolved, change_summary, difficulty_observed); `check-decisions` holds its shape; a missing block is a converge finding; SC-008 (first half) | Difficulty scoring (→ `S15`) | Given a delegate hand-back without the block, when converge runs, then it is a finding · Given a hand-back with the block, when `check-decisions` runs, then a malformed block fails naming the field | MINOR (every agent brief changes); snapshot + `migrate` |
| `S15-difficulty-score` | The planner says how hard each task is and the record shows how hard it was | FR-018: every task carries `difficulty: 1–5 — reason`; `make benchmark` joins planned and observed difficulty with converge passes, escalations and mutation survivors per task; FR-028 (part): those features logged per task; SC-008 (second half) | Boundary-cut and cross-context features (→ `S17`); routing (→ `S18`) | Given the tasks stage writes `tasks.md`, then every task carries a difficulty and reason · Given one finished slice, when `make benchmark` runs, then it prints the joined table per task | MINOR (the tasks template changes); snapshot + `migrate` |
| `S16-contract-edges` | A slice says what it provides and requires, and the gate checks it | FR-020: slice blocks may declare `provides`/`requires`; `check-model` validates every `requires` has a provider and reports per-slice degree, boundary cut, cross-context edges and top-3 share; the scoped gate's neighbour set may read these edges | Benchmark locality metrics (→ `S17`) | Given a `requires` nothing provides, when `make check-model` runs, then it fails naming the slice and the contract · Given a valid model, then it reports degree, cut, cross-context edges and top-3 share | MINOR (a new optional key in `model.yaml`, additive); event-modelling profile; snapshot + `migrate` |
| `S17-locality-report` | The team can see whether the bounded-degree assumption holds | FR-025: `make benchmark` reports K-effective, the Gini coefficient of slice-touch frequency and top-3 share per feature, flagging a node above a configurable share as a decomposition candidate; FR-026: every read beyond a one-hop brief logged as a context-expansion event with its reason, reported per slice; FR-028 (rest) | — | Given one finished feature, when `make benchmark` runs, then it prints K-effective, Gini, top-3 share and expansions per slice · Given a stage that opened a block outside its brief, then the log carries an expansion event with a reason | PATCH on top of `S15`/`S16`; snapshot + `migrate` |
| `S18-route-log` | Model routing by difficulty is measurable before it is ever switched on | FR-019: `models.json` gains a documented, default-off `route_by_difficulty` whose only effect is a log line naming the tier the policy would choose; FR-027: the documented semantics (planner, converge and skipper always strong; worker tier from difficulty, cut and cross-context edges with an upward cascade on a failed scoped gate; adversary at least the worker's tier on a different model family) | Switching routing on — out of scope by the owner brief | Given `route_by_difficulty` off, when a worker is dispatched, then a log line names the tier the policy would have chosen and the dispatched model is unchanged · Given the setting absent, then nothing is logged and nothing changes | MINOR (a new setting, default off); snapshot + `migrate`; never switched on by this run |
| `S19-pip-audit` (method) | The factory's own dependencies are audited by its gate | `platform: supported → audited`: `pip-audit` run green once, then recorded as `slipwai-graph`'s `audit` command; the programme's one tooling step | Any other row of the map | Given this checkout, when `pip-audit` runs over the locked environment, then it reports no known vulnerability · Given the command recorded in `project.json`, then `make -f delivery/Makefile check-convergence` reads the Platform row at `audited` | Docs, the map and this repository's own command record; a dev dependency and `project.json` are the host's to write on `main`, not a slice branch's |

## Slice graph

| Slice | depends_on | parallel_ok_with | Notes |
|---|---|---|---|
| `S00-run-path` | — | — | Alone first: the Pin stage refuses every other slice until `running.md` is proven |
| `S20-slice-scope-root` | `S00-run-path` | any | Second in split order (D13): one file, `assets/toolkit/scripts/check-slice-scope.py`, and its tests; disjoint from every other slice |
| `S21-refresh-keeps-owned-files` | `S00-run-path` | any | Third in split order (D15): `src/slipwai/resurvey.py` and its tests; disjoint from every other slice |
| `S22-slice-scope-base` | `S00-run-path` | any | Fourth in split order (D23): `merge_base()` in `assets/toolkit/scripts/check-slice-scope.py` and its tests; after `S20`, which owns the same file |
| `S23-refusal-in-subdirectory` | `S00-run-path` | any | Fifth in split order (D29): `src/slipwai/uncommitted.py` and its tests; disjoint from every other slice |
| `S24-ci-fetches-slice-base` | `S22-slice-scope-base`, `S01-gate-walks` (the owner's order, D39) | any | **Approved by the owner (D39)**; taken after `S01-gate-walks`, not before. Was sixth in split order (D31): `src/slipwai/project/ci_workflows.py`, `src/slipwai/project/adopted_ci.py`, one branch of `check()` in `assets/toolkit/scripts/check-slice-scope.py`, and their tests. The person's approval D31 waited on was given on 2026-10-03 (D39). **Blocked (D54): waits on a person's approval of what the fetch does to `check-migrations` and `check-flags` in CI; not ready until then**. The bosun found no stub or narrower reading that builds any part of it without that approval (D55); the run takes the next ready slice meanwhile |
| `S25-refusal-when-git-cannot-answer` | `S23-refusal-in-subdirectory` | any | In the pool behind the PRD's slices (D39, D44): `src/slipwai/uncommitted.py` and its tests. Ready once S23 is done, and taken after the PRD's slices, not before |
| `S01-gate-walks` | `S00-run-path` | `S02-runner-bookkeeping`, `S11-render-once` | Touches `assets/toolkit/scripts/check-*.py`; disjoint from the runner and from `event-model/` |
| `S02-runner-bookkeeping` | `S00-run-path` | `S01-gate-walks`, `S11-render-once` | Touches `assets/toolkit/scripts/agents/` and `check-decisions.py` |
| `S03-verify-stamp` | `S01-gate-walks` | `S11-render-once` | Touches `src/slipwai/project/makefile.py` and `src/slipwai/tooling.py`; `VERSION` is already `1.6.0.dev0` by then (`S02`, D60) |
| `S04-parallel-gate` | `S03-verify-stamp` | `S11-render-once` | Same files as `S03`; the stamp's key must know the gate's script set before `-j` reshapes it |
| `S05-xdist` | `S04-parallel-gate` | `S08-scoped-mutation`, `S11-render-once`, `S12-model-sidecar` | Python `pyproject` template and `native_commands.py` |
| `S06-scoped-gate` | `S04-parallel-gate` | `S08-scoped-mutation`, `S11-render-once`, `S12-model-sidecar` | The ladder text (`parallel_slices.py`, `commands.py`) and a new toolkit script |
| `S07-scoped-checks` | `S06-scoped-gate`, `S03-verify-stamp` | `S08-scoped-mutation`, `S12-model-sidecar` | Stays inside the check scripts; shares nothing with `S08` |
| `S08-scoped-mutation` | `S04-parallel-gate` | `S05-xdist`, `S06-scoped-gate`, `S07-scoped-checks`, `S12-model-sidecar` | `mutation.py`, `native_commands.py`; the `mutation-full` target is its one `makefile.py` line |
| `S09-phase4-fanout` | `S06-scoped-gate`, `S08-scoped-mutation` | `S12-model-sidecar`, `S14-result-contract` | Needs the scoped gate and scoped mutation to run per slice |
| `S10-merge-tree` | `S09-phase4-fanout`, `S07-scoped-checks` | `S13-one-hop-brief`, `S14-result-contract` | The riskiest slice; after every gate it relies on is proven (owner priority 4) |
| `S11-render-once` | `S00-run-path` | `S01`–`S06`, `S08` | `event-model/render.ts` only |
| `S12-model-sidecar` | `S11-render-once` | `S05`–`S09` | Not a build dependency on `S11` — serialised because both live in `event-model/` and `check-drawio` holds the canvas to the model |
| `S13-one-hop-brief` | `S12-model-sidecar` | `S10-merge-tree`, `S14-result-contract` | Reads the sidecar index |
| `S14-result-contract` | `S02-runner-bookkeeping` | `S09`, `S10`, `S13` | Shares `check-decisions.py` with `S02`, so after it |
| `S15-difficulty-score` | `S14-result-contract` | `S16-contract-edges` | Observed difficulty arrives in the result contract |
| `S16-contract-edges` | `S12-model-sidecar` | `S15-difficulty-score` | `check.py` after its linear rewrite |
| `S17-locality-report` | `S13-one-hop-brief`, `S15-difficulty-score`, `S16-contract-edges` | `S18-route-log` | Benchmark output only |
| `S18-route-log` | `S15-difficulty-score`, `S16-contract-edges` | `S17-locality-report` | `models.json`, `models.py` and their docs |
| `S19-pip-audit` | `S00-run-path` | any | Cheap; placed last by the owner's priority 3 (the generated project's loop first); taken earlier if a fan-out has a free seat |

`/drive` and `/where-are-we` read this table to compute the **ready** set: not yet done, every `depends_on`
already done. Ready slices whose contract is settled run in parallel: one `/drive` session fans out over the
unclaimed ones, one delegate per slice on a `slice/<id>` branch, and merges them back in split order; a session
that cannot delegate takes the earliest ready slice in split order and names the rest.

## Parking Lot

- **FR-021 is every slice's.** Each user-visible slice adds its `changelog.d/` fragment in the commit that makes the
  change; `S02-runner-bookkeeping` is the first MINOR and raises `VERSION` to `1.6.0.dev0` (D60; `S03-verify-stamp` finds it
  there); nothing here is MAJOR.
- **From S02's gaps review (D58, D60), for the completion audit to place.** A line of `specs/cruise-log.jsonl` that
  does not parse ends the run on a traceback, before the slice and after — a one-line message in its place is an
  older defect (D39's order). `status` reads the raw stream three times in one invocation; it is on demand and not
  the runner's bookkeeping. And **a person's:** whether `check-decisions` should one day fail an entry with no
  `Scope:` line — a new refusal in a gate CI runs (D54's kind of question); until a person says so the checker
  notes it and the filter carries the entry as global.
- **E8 — this repository taking each change through `slipwai migrate`** — is not done inside the cruise run: a
  migrate rewrites `delivery/scripts/`, which the runner treats as a changed control and parks on. It is a
  person's step between runs, or the first thing a person does when the run ends. Until then this repository's
  own loop runs the gate it has today.
- **Safety net `tests-pass` → `fast` → `pinned` → `mutation-measured`**: `pinned` is held per slice by the Pin
  stage; `mutation-measured` for this repository means a mutation command for the factory itself, which the owner
  brief rules out of scope (making this repository's own suite fast beyond what the general changes give it).
  Not planned in this run.
- **Structure `named` → `laid-out`** would move the factory under `apps/`; the owner brief puts the generated
  project's loop first and no product slice waits on it. Not planned in this run.
- **Constitution row reads `template` while the file is ratified** — `/survey` re-reads it; the row flips at the
  first Convergence stage that runs `/survey`, from the fact already in the tree.
- **The PRD's owner decisions 1–7** could not be read (the artifact needs a permission this session lacks).
  Decision 3 is known from the brief (sidecar index, never per-slice files without a person). The others are
  taken slice by slice through the skipper protocol as their stages raise them, and the entry says the PRD was
  not consulted.
- **The gate inside an iteration inherits the runner's environment.** `make -f delivery/Makefile verify` run from a cruise iteration carries `CRUISE_RUNNER` and `CRUISE_ITERATION` into the factory's own tests, and the ones that start a runner refuse; the same suite is green with them unset. `S00-run-path` fixes the tests (a change under `tests/`, not user-visible); until it lands, a green gate for a commit made inside an iteration is established by running the suite with the two variables cleared and saying so in the commit.
- **Where slices land while the adoption is unmerged (D12).** `adopt-method` has not been merged to `main` and
  that merge is a person's (`delivery/docs/adoption.md`, step 6). Until they do it, every slice's commits land
  on `adopt-method` directly, one slice at a time in split order, with no `slice/<id>` branch, no claim and no
  push; the register's *Merged as* names each slice's first and last commit so a person can cut it into its own
  PR. The ladder's full shape — claim, worktree, fan-out, merge into `main` — returns when a person merges the
  adoption (or says in writing that `slice/<id>` branches may be cut from `adopt-method`) **and** the
  slice-scope checker's root-path defect (`S20-slice-scope-root`, D13) has reached this repository through
  `slipwai migrate`; until both, no `slice/<id>` branch here passes `check-slice-scope`.
- **`survey/pinned.md` on a slice branch where the adoption is under `apps/`** (found deciding D18): the Pin
  stage makes a slice add its row to `<delivery>/survey/pinned.md`, and `check-slice-scope` refuses that file as
  *outside every deployable* in a repository whose deployables are not at `.` — today and after `S20`, which is
  held to the root case. A candidate PATCH slice for the completion audit to place; not planned yet.
- **The migration and events rules at an adopted deployable under a subdirectory** (D21): `S20` lifts the
  12-digit stamp and the events rule only at a deployable recorded at `.`. One recorded `"generated": false`
  under `apps/` or elsewhere keeps both, as every released version has it; lifting them there removes a refusal
  that exists today and is a person's call (owner brief, *Always ask a person*).
- **`specs/cruise-log.jsonl` on a slice branch** (found by S20's gaps pass, D22): the runner writes its log
  beside the feature directories, nothing ignores it, and `check-slice-scope` refuses any path directly under
  `specs/` on a `slice/<id>` branch — so the first slice branch a `/cruise` run works on is red for the runner's
  own file. Older than `S20` and hidden until it; a candidate PATCH slice (ignore the log, or let the checker
  pass it) for the completion audit to place.
- **A refresh in a relocated delivery directory rewrites `survey/structure.md` straight after `adopt`** (found by
  S21's converge pass): with `--delivery ops/method` the delivery directory's own file count moves 281 → 285 between
  `adopt --yes` and the first refresh, so the page is rewritten with no fact behind it; the default layout rewrites
  nothing. Older than `S21`; a candidate PATCH slice for the completion audit to place.
- **A refresh moves an `overridden` `ci.branch` to the checked-out branch** (found by S21's converge pass, on a
  clone of this repository): `ci.branch` went `main` → `adopt-method` and `.github/workflows/verify-delivery.yml`
  was rewritten, though the `ci` record's provenance is `overridden`. Not investigated; older than `S21`. A
  candidate PATCH slice for the completion audit — and until it lands, a `/survey` run in this repository off
  `main` is followed by a revert of `project.json`'s `ci.branch` and the workflow, which is a control the runner
  parks on.
- **Left by S21's gaps pass for the completion audit** (D27), each older than `S21` and the same before and after
  it: no test runs `slipwai migrate` over a seeded file the project edited (the tripwire D26 names); a seeded path
  that is a directory ends a refresh on a traceback, and one that is a dangling symlink is written through; a
  convergence row whose rung is not on its ladder ends a refresh on a traceback (`constitution_journey.py`); and
  the adoption block in `AGENTS.md` says *never edit anything listed in `.written` by hand … `slipwai migrate`
  replaces them*, which reads against the four files a project owns and against `migrate` being a merge — a
  generated sentence in a block `adopt` appends once, so a PATCH with a catch-up note.
- **Left by S21's adversary pass for the completion audit** (D28, D29), each older than `S21`: `strategy.before`
  and the strategy page's heading follow the *recommended* strategy where an Accepted ADR decides another (F2) —
  a question about what the page is for once a strategy is decided; a convergence row with no `provenance`, or
  for an axis the factory does not know, ends a refresh on a traceback (F3, F4); a Strategy row confirmed at
  `decided` with no ADR leaves the map and the page disagreeing (F5); and a person's row does not follow a
  person's `release`, `database` or `infrastructure` record upward or sideways, though `ground.md` says the row
  follows when `/survey` re-reads the record (D28 fixes only the downward case on Path to production).
- **Windows under Git Bash** (edge case): worktree fan-out and `-j` are held by the matrix tests before release;
  `S04` and `S09` name that in their plans rather than opening a slice.

## Warnings

- Every slice changes code that existed before the method did, so the Pin stage applies to each: the seam it
  changes is pinned by `/characterise` first, with a fake in the test tree and no mocking framework.
- Most slices share `src/slipwai/project/makefile.py`, `src/slipwai/tooling.py` and `native_commands.py`; the
  `parallel_ok_with` column lists only pairs whose files are disjoint, and a fan-out that finds otherwise
  serialises the pair rather than merging a conflict.
- `S09` and `S10` change the ladder's own text (`drive.md`, `cruise.md` as generated) and the runner; they are the
  only slices whose demo is a synthetic fan-out rather than a gate run, and the demo is on a generated project,
  never on this repository's live run.
- `S19-pip-audit` and `S00-run-path` write things a slice branch may not (`project.json`, a dev dependency, a survey
  page); the host does those writes on `main` at the Convergence stage, as the ladder says.

- **The same mintable base in two other checkers** (found at S22's slice gaps, D31): `assets/toolkit/scripts/check-migrations.py`
  `merge_base()` and `assets/targets/*/scripts/check-flags.py` choose their base from `main`, `origin/main`, `master`,
  `origin/master` by short name, as `check-slice-scope` did before S22 — a stray `master`, or a tag named `main`, moves
  it. `check-migrations` states its own stance on a shallow checkout (*says nothing false on a shallow one*), which
  stands. Not swept into S22 (its row excludes any other change to what a checker holds); for the completion audit, or
  a slice of its own.
- **The forge's default branch on push pipelines** (D30): where CI runs a slice branch on a push, with no pull-request
  target, only the local promise holds. Reading `CI_DEFAULT_BRANCH` or the event payload is another anchor and another
  capability.

- **Left outside S22 by its converge passes** (older than the slice or outside its row): `current_branch()` in
  `check-slice-scope.py` trusts `GITHUB_HEAD_REF` over git even where `HEAD` is attached to another branch;
  `bases_of()` uses plain `git merge-base`, which takes one of several best ancestors on a criss-cross history;
  whether the *checked* branch is a slice is still read case-sensitively (a branch checked out as `Slice/S1` has
  *nothing to hold* — S22 closed the trunk-name side only); and under a CI marker a full clone whose trunk is
  unrelated is told `fetch-depth: 0`, which would not help it (AC-S22-22 decides the line). For the completion audit.

- **An unborn `HEAD` on a slice branch has nothing to hold** (S22's gaps pass, G9; older than the slice):
  `git init -b slice/S1` with no commit reads as a detached checkout, though D31 says a new repository whose first
  branch is a slice branch fails. `current_branch()` asks `rev-parse --abbrev-ref HEAD`; `symbolic-ref --short HEAD`
  would answer. With the other `current_branch()` line above, for the completion audit.

- **Left outside S22 by its adversary pass** (D35): a rebase in progress reads as a detached checkout with *nothing
  to hold* (`rebase-merge/head-name` would answer) — with the other `current_branch()` lines; a gate that cannot
  ask git at all still exits 0, now saying so — whether it should fail is, in CI, a person's, beside `S24`; and a
  refused path is still told *Land it on `main`* where the trunk has another name (the script's older messages).
- **The survey's history in a subdirectory project (D38; found by S23's gaps sweep).** `history()` in
  `src/slipwai/structure.py` runs `git log --name-only` in the project's directory, which lists the whole
  repository's commits with paths spelled from its top, so the structure page of a project adopted in `sub/`
  counts its neighbours' commits and names files under `sub/…` it cannot find. The same mistake as S23's,
  in what the survey reads rather than what the refusal protects. For the completion audit to place.
- **The order from S23 on is the owner's (D39).** After `S23-refusal-in-subdirectory`: `S01-gate-walks`, then
  `S24-ci-fetches-slice-base` (approved; the host's reading of *taken after S01*; blocked at its gaps review
  since iteration 8 on a second approval, D54 — the run goes on past it), `S02-runner-bookkeeping`,
  `S11-render-once`, and on through the PRD's order. A slice an adversary or gaps finding opens from here on
  goes behind the PRD's slices unless the finding is `CRITICAL`.
- **`GIT_DIR` exported with no `GIT_WORK_TREE`, project in a subdirectory (D40; found by S23's converge pass, T012).**
  An absolute `GIT_DIR` makes git take the project's directory for the top of the work tree, so every run is refused
  and *commit or stash* cannot clear it; a relative one finds no repository, so nothing is refused and an uncommitted
  edit is written over (AC-S23-8's *git cannot read*, as today). `LOW`, older than S23, correct at the top and
  wherever `GIT_WORK_TREE` is also set. Not to be fixed by removing git's variables from the environment: that writes
  over an edit where the repository is kept outside the work tree. If taken up: one sentence naming the variable,
  swept over every `GIT_*` variable that moves the repository, the work tree or the index, for both callers of
  `changed()`. For the completion audit to place behind the PRD's slices (D39) or rule out.
- **`git` not installed (D41; found by S23's converge pass, T013).** With no `git` on `PATH`, `adopt --refresh`,
  `--confirm` and `--decline` end on a `FileNotFoundError` traceback from `changed()` (`src/slipwai/uncommitted.py`),
  exit 1, nothing written; older than S23 and the same at the top. When placed: a one-line refusal that the command
  needs git, exit 2 — never *as not a repository*, which would let a run write over an edit it could not see — swept
  over every `git` call an adopted project's commands reach (`uncommitted.py`, `structure.py`, `quick_wins.py`,
  `add_service.py`'s `refuse_uncommitted`). `LOW`; behind the PRD's slices (D39).
- **Older findings of S23's after-converge gaps pass (D43), behind the PRD's slices (D39).** *O1, `MEDIUM`:* the
  `/survey` page adoption ships (`src/slipwai/project/pin_commands.py`, *`git status --porcelain` prints nothing. The
  command refuses an unclean tree …*) and `src/slipwai/resurvey.py`'s docstring describe the refusal as it was before
  `uncommitted.py`; an agent following step 1 in a subdirectory project stops on a neighbour's work, and the undo it
  promises would discard uncommitted answers. A shipped page: a PATCH with a fragment. *O2, `LOW`:* `adopt` ends on a
  `CalledProcessError` traceback from `git add`, with its files written and partly staged, where a global excludes
  file names a path it writes. *O3, `LOW`:* the refusal prints *each holds* for a single path.
- **What S23's adversary pass found beside B1 (D44), each older than the slice and the same at the top of a repository;
  for the completion audit to place behind the PRD's slices (D39) or rule out.** *A1, `MEDIUM`:* a path a run starts
  writing during the run (a person's own `.github/workflows/verify-delivery.yml` once `ci.forge` reads `github`) is
  not in `writes()`, so it is written over and recorded as slipwai's own. *A2, `MEDIUM`:* a run that dies between its
  first write and its stamp leaves its own files refused by the next run, and with a read-only `.written` two factory
  scripts afterwards read as `owned`. *A3, `LOW`:* the stamp digests the disk at the run's end, not what the run
  wrote. *A4, `LOW`:* a tracked symbolic link at a written path, at `delivery/` or at `.delivery-tools/written.json` is
  written through, outside the project and the repository. *B2, `LOW`:* `delivery/` as a nested repository or gitlink
  hides its files from the refusal. *B3, `LOW`:* `assume-unchanged` or `skip-worktree` on a written path. *B4, `LOW`:*
  a deeply nested `written.json` ends on a `RecursionError`. And from the hand's demo, not this slice's: argparse's
  usage block precedes every refusal, so the sentence that matters is line 15; a directory whose name is not a
  project name cannot be adopted without `--name` and the error does not say so; a refresh prints *not wrapped … has
  no record* for directories recorded as candidates.

- **Directories the gate walks still descend (D45; S01's gaps stage).** FR-004's list is closed at five for S01. Other
  tools' `target/` in adopted repositories (Cargo, sbt), and `dist`, `build`, `.build`, `coverage`, `.pytest_cache`,
  `.ruff_cache`, `.mypy_cache`, `.terraform`, wait for a measurement that shows a walk needs them; `dist` and
  `build` can be source names, as `target` can, and would each need a test of their own. For the completion audit.

- **An adopted application outside `apps/` and `packages/` is read by neither walking gate (D51; S01's gaps pass,
  walking G5).** `source_files()` in `check-imports.py` and `migrations()` in `check-migrations.py` walk only
  those two directories; a deployable recorded at `services/legacy` with `layout: hexagonal` passes both with a
  `domain/` file importing an adapter. Older than S01, which only made it visible (`0 directory entries read`).
  `LOW`; for the completion audit to place behind the PRD's slices (D39) or rule out.

- **What S01's adversary pass and demo left (D52, D53), behind the PRD's slices (D39), for the completion audit.**
  *`MEDIUM`, older:* `check-imports` rule 1 reads an import line for a layer name between separators, so in a
  Python `domain/` file `from ..adapters import store`, `from shop.adapters import store`, `from .. import adapters`
  and `from ..infrastructure import db` all pass (the hand's evidence:
  `slices/S01-gate-walks/demo/import-spellings-both-scripts.txt`). *`LOW`:* an unreadable `apps/` passes both
  walking gates with `0 directory entries read` (A3); `scripts/` linked from outside the project reads the wrong
  root; a nested Maven module's `target` in an adopted repository is still walked, and tracked files force-added
  under a recorded Java deployable's `target/` are not read (D52's residual).

## Next Step

Enter the ladder for `S00-run-path` at its Slice gaps stage; it is the only ready slice. `S01-gate-walks`,
`S02-runner-bookkeeping` and `S11-render-once` form the first fan-out once it is done.
