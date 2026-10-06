# Tasks: S39-benchmark-elapsed — time waited told apart from time worked

**Input**: [plan.md](plan.md) (*The example map* R1–R12 is what the tasks cut on; *Structure Decision*; *Pin*;
*Tests*), [data-model.md](data-model.md), [research.md](research.md), [quickstart.md](quickstart.md); acceptance
criteria AC-S39-1 … AC-S39-12 in `specs/001-faster-slipwai/spec.md` under `### S39-benchmark-elapsed (method slice)`;
D159 in `specs/001-faster-slipwai/decisions.md`.

**Branch**: `slice/S39-benchmark-elapsed` (worktree `../slipwai-graph-S39-benchmark-elapsed`). No push. One commit per
task.

**Delegation**: one delegate per task, each its own RED-GREEN-REFACTOR increment (constitution V): write the rule's
examples, see them fail for the right reason, make them pass, refactor. A task's "Files" line is its manifest: the
only files that delegate may write. Nobody but the host writes `tasks.md`. Tasks are tagged by the user-story group
they deliver (this slice has no numbered story of its own; FR-049 and FR-057, SC-014's input): `[US1]` elapsed,
waiting and stage time, `[US2]` cost, `[US3]` decision health, `[US4]` reading surfaces, `[US5]` ladder text and
migrate. AC-S39-11 is the demo, not a task ([quickstart.md](quickstart.md) is its script).

## Constraints

Constraints that hold for every task's GREEN, stated once:

- **Size.** Every file under `tests/` and `src/` stays at or under 350 lines (`make check-structure`). Each new
  module and test module ≤ 350. `tests/test_benchmark.py` is already at 350 lines: a task that must edit it keeps it
  at or under 350 (it moves a line, it does not add one), and asks the host to name a second module rather than
  splitting on its own. `src/slipwai/project/cruise.py` is at 336: the change there is in place, no new paragraph.
- **Repository rules.** No edit under `delivery/` in this checkout (its `scripts/` copy is a control; attribution
  here stays by delegate type until a person runs `migrate`). No change to `VERSION` (it stays `1.6.0.dev0`), to
  `catalog.json`, to `benchmark.json`'s shape, to `check()`, nor to any record under `specs/` but this slice's folder.
- **Encoding.** Every `open` and `read_text` names `encoding="utf-8"`.
- **Bytecode.** Tests set `sys.dont_write_bytecode = True` before loading any toolkit script; scripts under `assets/`
  run as `python3 -B`; `benchmark.py` loads `measures.py` and `attribution.py` by path with bytecode off; no
  `__pycache__/` is left under `assets/`.
- **Tests.** Fakes live in the test tree; never `unittest.mock` or any mocking framework. Examples enter through
  `benchmark.py` as a `python3 -B` subprocess (aggregate, `--json`, `check-benchmark`), or `slipwai generate`/`migrate`,
  against a scratch git project built by `tests/elapsed_fixture.py` (dated commits via `GIT_COMMITTER_DATE`, a fake
  `HOME` with transcripts and `meta.json`).
- **Commits by path.** `git add <exact paths of the task's manifest>`, never `git add -A`. `make lint typecheck
  check-structure` before each commit.
- **Scratch** only under `/tmp/s39/`.
- **Pin.** The pin of T001 runs green before every later task's commit; a rename it has to learn is written into it in
  the increment that makes the rename, and only there.

## Phase 1: Pin (before any change)

- [ ] T001 [US1] **R8 — old records still read the same** (AC-S39-8; D65). The pin, and the whole of R8's e1–e2.
  `tests/test_benchmark_pin.py` takes `assets/toolkit/scripts/agents/benchmark.py` at git `525399b` with
  `git show` (and `assets/toolkit/scripts/hand_backs.py` beside it, because the script loads it) into a scratch
  project under `/tmp/s39/`, takes the 16 `benchmark.json` records as committed at `8072724` into the scratch
  project's `specs/`, and runs the old script and the working copy's on that tree: the aggregate, `--json`, and
  `check-benchmark`. Examples e1 every aggregate cell for every column S39 does not rename equal, column by column
  (a table of the columns S39 renames, empty today, is where the later increments write `wall` → `stage time` and
  `rework` → `re-entered`) · e2 `check` stdout, stderr and exit byte-identical. It compares the script with itself at
  first, so it is **green before any change**; the delegate proves it has teeth by changing one cell in the working
  copy, seeing it fail, and restoring the file with `git checkout -- <exact path>`. R8's e3 (no new figure is a bare
  `0` where nothing was read) has no behaviour to guard yet and lands in T011. Also run, and report, the suite that
  must stay green throughout: `tests/test_benchmark*.py`, `test_toolkit`, `test_utf8_io`, `test_changelog`.
  Files: `tests/test_benchmark_pin.py`.

## Phase 2: US1 — elapsed, waiting and stage time (sequential)

R1–R3, R6 and R10 all write `assets/toolkit/scripts/agents/measures.py` and `benchmark.py`, so they run in order.
T002 also writes the shared fixture and the first `measures.py` (no separate setup task).

- [ ] T002 [US1] **R1 — ready and accepted are read from git** (AC-S39-1). `tests/elapsed_fixture.py` (the scratch git
  project with `project.json`, `specs/f/story-split.md` and its `## Slice graph`, `specs/f/slices/README.md`,
  records, commits dated with `GIT_COMMITTER_DATE`; the fake `HOME` with transcripts and `meta.json`; `bench(...)` as
  a `python3 -B` subprocess) and a first `measures.py` (`moments(...)` and the interval helpers), loaded by
  `benchmark.py` by path; `summarise()` gains `elapsed`, `moments`, `read_from`; the page's slice heading prints
  elapsed and the moments. RED→GREEN: e1 split commit day 1, dependency's register row day 2, own row day 4: elapsed
  2 days to the second, ready names the dependency's commit · e2 a merge commit (subject names `slice/<id>`) and an
  accepted demo before the row: both printed inside the interval, the merge before the row · e3 no own row:
  `open since 2026-…Z`, `--json` `elapsed` is `{"unknown": "open since …"}` · e4 a dependency with no done mark:
  `{"unknown": "not ready: <dep> is not done"}` · e5 the slice in no split and no model: unknown, naming
  `story-split.md` · e6 the event profile: `status: implemented` commits in `docs/event-model/model.yaml` stand in for
  register rows. Pin: T001 stays green (new keys and columns only).
  Files: `tests/elapsed_fixture.py`, `tests/test_benchmark_elapsed.py`,
  `assets/toolkit/scripts/agents/measures.py`, `assets/toolkit/scripts/agents/benchmark.py`.

- [ ] T003 [US1] **R2 — waiting by cause adds up to elapsed** (AC-S39-2). `measures.py`: `parks(...)`,
  `iterations(...)` from `specs/cruise-log.jsonl`, `worked(...)` (the brackets' union, `gate` and a driverless `demo`
  excepted) and `waiting(...)` with the first-claim order *worked, integration, dependency, review, worker,
  unattributed* of [data-model.md](data-model.md); `benchmark.py` prints a waiting table after the slice table and
  adds `waiting`, `worked_seconds` to `--json`, each cause naming the record it was read from. RED→GREEN: e1 the
  sibling-merge fixture (accepted demo, a sibling's merge, own merge, a `gate` bracket, own row): dependency = demo →
  sibling's merge, integration = merge → row less the bracketed fix, the gate inside integration · e2 a park inside
  the interval: review = its length · e3 worked + the four causes + unattributed = elapsed, to the second, asserted
  on every fixture of the module · e4 a person's patch the slice needs: no record says it (Q2), the time stays where
  the other rules put it. Pin: T001 stays green.
  Files: `tests/test_benchmark_waiting.py`, `tests/elapsed_fixture.py`,
  `assets/toolkit/scripts/agents/measures.py`, `assets/toolkit/scripts/agents/benchmark.py`.

- [ ] T004 [US1] **R3 — worked once, stage time renamed** (AC-S39-3). `measures.py` `stage_seconds(...)`;
  `benchmark.py`: `COLUMNS`, `STAGE_COLUMNS`, `LEGEND`, the page's slice heading and the feature line read *stage
  time* (the feature line `stage time … in all`); the old `rework` list moves to `reentered` in `summarise()` and its
  column to `re-entered` (values unchanged); a `cut_off` entry's stage time ends at the last attributed transcript
  line where one is read, the note names both moments, else the recorded end stands with the reason. This is the
  renaming increment: it updates the existing assertions on `wall` and on the `rework` list in
  `tests/test_benchmark*.py` (`test_benchmark_brackets.py` lines 147 and 154, `test_benchmark.py` line 215) and
  writes the two renames into the pin's table; **only those lines**, and `test_benchmark.py` stays at 350 lines.
  RED→GREEN: e1 skipper 10:10–10:20 inside implement 10:00–11:00: stage time 70 m, worked 60 m · e2 an entry cut off
  3 h after its last line: stage time ends at that line, the note names both · e3 a cut-off entry whose transcript is
  gone: recorded end, the note says the transcript could not be read · e4 the aggregate's header and the page's
  column say `stage time`; no heading prints summed stage time as elapsed.
  Files: `tests/test_benchmark_elapsed.py`, `tests/test_benchmark_pin.py`, `tests/test_benchmark.py`,
  `tests/test_benchmark_brackets.py`, `assets/toolkit/scripts/agents/measures.py`,
  `assets/toolkit/scripts/agents/benchmark.py`.

- [ ] T005 [US1] **R6 — the feature's elapsed is not its stage time** (AC-S39-6). `measures.py`
  `feature_figures(...)`; the aggregate's feature line and the page's print `stage time`, `elapsed` and `time with any
  slice in flight` under those names; `--json`'s feature record gains `feature: {elapsed, stage_seconds,
  in_flight_seconds}`. RED→GREEN: e1 three overlapping slices: elapsed < summed stage time; the line carries all
  three names, each its own number · e2 one slice open: elapsed `open since …`, the other two figures still printed.
  Files: `tests/test_benchmark_feature.py`, `assets/toolkit/scripts/agents/measures.py`,
  `assets/toolkit/scripts/agents/benchmark.py`.

- [ ] T006 [US1] **R10 — a `/drive` project with no cruise log** (AC-S39-10). Where `specs/cruise-log.jsonl` is
  absent, worker and review (their cruise half) read nothing, the time they would hold stays *unattributed*, and the
  run exits 0 with no warning about the log. If e1 passes the moment it is written, fold only what it forces into
  `measures.py`'s missing-log path and keep e1 as the guard (no passing-on-write test is its own task).
  RED→GREEN: e1 a generated project (`slipwai generate` into `/tmp/s39/`), one slice with brackets and a register
  row: elapsed and stage time printed, waiting all unattributed except integration and dependency where git says so,
  exit 0, stderr empty.
  Files: `tests/test_benchmark_waiting.py`, `assets/toolkit/scripts/agents/measures.py`,
  `assets/toolkit/scripts/agents/benchmark.py` (only if e1 is red).

## Phase 3: US2 — cost attributed to one record (sequential)

R4 and R5 share `benchmark.py` and read each other's figures, so they run in order, after Phase 2.

- [ ] T007 [US2] **R4 — rework is what a non-accepted demo cost** (AC-S39-4). `measures.py` `rework(...)`: every
  entry after a `demo` whose outcome is `behaviour` or `implementation`, up to (not including) the next `demo`, or to
  the end of the record; its seconds are stage time, its tokens the entry's tokens (here the recorded `usage` totals;
  T008 points them at attributed tokens); both inside the slice's `cost`. `--json` gains `rework{seconds, tokens}` and
  `cost{tokens, shared}` (cost: the recorded sum until T008); the waiting table gains `rework` and `cost`. RED→GREEN:
  e1 S08's shape (demo `implementation`, implement, demo `implementation`, implement, demo `accepted`, implement):
  rework = the two middle implements, their seconds and tokens; the last implement is not rework · e2 a slice with no
  demo: rework 0 s, 0 tokens · e3 the trailing entries after a non-accepted demo with no next demo yet are rework.
  Pin: T001 stays green (the old list is already `reentered`).
  Files: `tests/test_benchmark_attribution.py`, `assets/toolkit/scripts/agents/measures.py`,
  `assets/toolkit/scripts/agents/benchmark.py`.

- [ ] T008 [US2] **R5 — each request in one record** (AC-S39-5). New `attribution.py`: reads each session's
  transcripts once (only lines carrying `"usage"`), resolves each sub-agent's chain from `meta.json`
  (`parentAgentId` upwards to a `drive-slice`; description `drive-slice <id>`, or its first word for older
  transcripts), finds each bracket's opener (`benchmark: <stage> started (<record>` at the bracket's cursor), assigns
  every request to a record and entry or to the feature's *shared* bucket, and returns per-entry tokens, delegates
  and last-line moments, per-record cost, per-session totals. `benchmark.py` loads it by path with bytecode off; the
  per-entry tokens, `cost`, `entries` and `sessions` come from it; `rework` tokens and R3's cut-off last line now
  read attributed tokens and moments; a note for an unresolved `drive-slice` description. RED→GREEN: e1 two slices'
  `implement` brackets open at once, each with `drive-implement` delegates under its own `drive-slice`: each cost
  holds only its own delegates' requests (and T007's e1 re-asserted on attributed tokens) · e2 a host-spawned
  delegate inside a `drive-slice`-opened bracket: not that slice's · e3 a host line covered by two slices'
  host-opened brackets: shared · e4 records merged from a worktree and the integration branch both covering one
  request: counted once · e5 records + shared = the session's distinct-request total · e6 a `drive-slice`
  description naming no record: its requests are shared, with a note · e7 no transcripts on the machine: cost is the
  recorded sum where no other record's bracket overlaps, else `{"unknown": "brackets of <record> overlap this one and
  the transcripts are not on this machine"}`. Pin: T001 stays green (the old script's token columns equal the new
  where a single record covers the window).
  Files: `tests/test_benchmark_attribution.py`, `tests/elapsed_fixture.py`,
  `assets/toolkit/scripts/agents/attribution.py`, `assets/toolkit/scripts/agents/measures.py`,
  `assets/toolkit/scripts/agents/benchmark.py`.

## Phase 4: US3 — decision health (FR-057)

- [ ] T009 [US3] **R7 — decision health reads unknown until a tier exists** (AC-S39-7; D159). `measures.py`
  `decision_health(...)` on Q1 option (a), one table of spellings: `- **Reversibility:** <tier>` with `<tier> → hard`
  (and `->`) an escalation, `Status:` words `ratified`/`reverted`, the median wait from the skipper bracket (any
  record of the feature) holding the entry's `When:`; `benchmark.py` prints three lines under the feature heading and
  `--json` carries `decision_health`. RED→GREEN: e1 this repository's `decisions.md` (copied into the scratch tree):
  three `unknown — no decision entry carries a Reversibility: line`, no `%` in the lines · e2 20 `easy`/`guarded`
  entries, 4 `guarded → hard`: `20%`, flagged outside 5–15 % · e3 1 reverted of 10 reviewed: `10%`, flagged; 0 of 10:
  `0%`, not flagged · e4 tiers but no review: the rate is unknown, naming that no entry was ratified or reverted.
  Files: `tests/test_benchmark_feature.py`, `assets/toolkit/scripts/agents/measures.py`,
  `assets/toolkit/scripts/agents/benchmark.py`.

## Phase 5: US4 — the reading surfaces

- [ ] T010 [US4] **R9 — `--json` carries what S37 reads** (AC-S39-9), with R8's e3. `summarise()` assembles every
  key of [data-model.md](data-model.md)'s *`--json`, per record*: `elapsed`, `stage_seconds`, `worked_seconds`,
  `waiting{…}`, `rework{…}`, `cost{…}`, `moments`, `read_from`, `entries`, `reentered`; the page's *Reading these
  numbers* (`READING`) gains one sentence on elapsed against stage time. Mostly already built by T002–T009: fold into
  this task only the missing keys, the `read_from` completeness and the sentence, and keep e1–e2 as the guard. RED→GREEN
  e1 every key present on every record, each a number or an unknown object · e2 `read_from` names a commit,
  `specs/cruise-log.jsonl`, `decisions.md` or a bracket for each figure · e3 the reading paragraph's sentence · e4
  (R8's e3, written into `test_benchmark_pin.py`) no new figure over the 16 old records is a bare `0` where nothing
  was read.
  Files: `tests/test_benchmark_feature.py`, `tests/test_benchmark_pin.py`,
  `assets/toolkit/scripts/agents/benchmark.py`, `assets/toolkit/scripts/agents/measures.py`.

## Phase 6: US5 — ladder text and what a project already made gets (sequential)

- [ ] T011 [US5] **R11 — the ladder names the slice and brackets the gate** (AC-S39-2, -5). Factory text only:
  `src/slipwai/project/parallel_slices.py` describes every `drive-slice` delegate as `drive-slice <id>` and brackets
  the full gate run after a merge as the slice's `gate` stage; `src/slipwai/project/cruise.py` names the description in
  the fan-out sentence, in place; `src/slipwai/project/benchmark.py` *What each stage costs* gains `gate` and its
  bracket, the `end` table its row, one sentence on elapsed against stage time, and `/benchmark`'s page description
  says *stage time*, elapsed and waiting; `benchmark.py`'s `LADDER` gains `gate` after `mutation`. RED→GREEN: e1 a
  generated project, both profiles: `drive-slice <id>` in `commands/drive.md` and `commands/cruise.md` · e2 *What
  each stage costs* names `gate` and its bracket · e3 `benchmark.py start … gate` then `end … gate` records an entry
  sorted after `mutation`. Pin: `test_commands.py`, `test_cruise_record.py`, `test_agent_types.py`, T001.
  Files: `tests/test_benchmark_elapsed_migrate.py`, `src/slipwai/project/parallel_slices.py`,
  `src/slipwai/project/cruise.py`, `src/slipwai/project/benchmark.py`,
  `assets/toolkit/scripts/agents/benchmark.py`.

- [ ] T012 [US5] **R12 — what a project already made gets** (AC-S39-12). Last, because it needs every file. A
  project generated by the factory at `525399b` (taken from git) with records written before S39, migrated by this
  one: `scripts/agents/measures.py` and `attribution.py` arrive, `make benchmark` succeeds, `check-benchmark` warns of
  nothing new. `changelog.d/benchmark-elapsed.md`: first line `MINOR`, one standalone **Catch-up.** paragraph naming
  the `wall` → `stage time` and `rework` → `re-entered` renames, the `--json` `rework` key's new meaning, that no
  record is rewritten and nothing must be redone. RED→GREEN e1 generated at `525399b`, records written, migrated: both
  modules, `make benchmark` exit 0, the new columns · e2 the fragment's first line is `MINOR`, its catch-up names the
  rename, the `--json` key and that no record is rewritten. `VERSION` stays `1.6.0.dev0`;
  `tests/test_changelog.py` must pass.
  Files: `tests/test_benchmark_elapsed_migrate.py`, `changelog.d/benchmark-elapsed.md`.

## Phase 7: Polish and final check

- [ ] T013 **Hold the gate** (no new behaviour, no new test). Run and report, changing nothing unless a failure names a
  file in the manifests above: `make lint typecheck check-structure`; `make test TESTS="test_toolkit test_utf8_io
  test_changelog"`; the six new modules and the existing `tests/test_benchmark*.py` (`make test TESTS="test_benchmark_pin
  test_benchmark_elapsed test_benchmark_waiting test_benchmark_attribution test_benchmark_feature
  test_benchmark_elapsed_migrate test_benchmark test_benchmark_brackets test_benchmark_overview"`); every file under
  `tests/` and `src/` ≤ 350 lines (`wc -l`); every `open` and `read_text` in `measures.py`, `attribution.py` and
  `benchmark.py` names `encoding="utf-8"`; every test that loads a toolkit script sets `sys.dont_write_bytecode`, probes
  run as `python3 -B`, and `find assets -name __pycache__` is empty; no `unittest.mock` or other mocking import in the
  new tests (`grep -rn "unittest.mock\|mock" tests/test_benchmark_*.py tests/elapsed_fixture.py`); scratch only under
  `/tmp/s39/`; `git diff --name-only 525399b` lists only `assets/toolkit/scripts/agents/`,
  `src/slipwai/project/{benchmark,parallel_slices,cruise}.py`, `tests/`, `changelog.d/benchmark-elapsed.md` and this
  slice's folder (nothing under `delivery/`, no `VERSION`). The 41-minute starters matrix is not rerun here; it runs at
  the merge root.
  Files: none written.

AC-S39-11 (the demo) is not a task: it is the next stage, scripted by [quickstart.md](quickstart.md).

## Dependencies and order

T001 → T002 → T003 → T004 → T005 → T006 (one pair of scripts, in order) · T007 → T008 (T008 re-points T007's tokens)
· T009 after T005 · T010 after T009 · T011 after T004 (the `gate` stage feeds R2's integration) · T012 after T010 and
T011 · T013 last. Tasks are numbered in dependency order, grouped by story; T001's pin runs before every commit.

## Parallel opportunities

`benchmark.py` and `measures.py` are written by T002–T010, so those tasks serialize; `tests/elapsed_fixture.py` is
shared by T002, T003 and T008.

- **May run alongside each other:** nothing. T011 is disjoint from T005–T010 in the factory modules it writes, but
  it also writes `assets/toolkit/scripts/agents/benchmark.py` (`LADDER`), which T002–T010 write, so it would be two
  agents on one file. No task carries `[P]`.
- **May not:** T001–T010 among themselves (`benchmark.py`, `measures.py`; T002/T003/T008 `elapsed_fixture.py`; T004
  also `test_benchmark.py`, `test_benchmark_brackets.py` and the pin; T005 and T009 and T010 one test module,
  `test_benchmark_feature.py`); T012 and T013 with anything. Two delegates at most.
- Commits are by path, so two delegates share one working tree safely; neither runs `git add -A`.

## Design review

No screen in this slice. (No white box either: a method slice with no entry in `docs/event-model/model.yaml`, so no
mockup states to write back.)

## Convergence

*(The verdict is written here by the converge stage.)*
