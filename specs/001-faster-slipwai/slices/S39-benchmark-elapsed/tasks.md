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

- [x] T001 [US1] **R8 — old records still read the same** (AC-S39-8; D65). The pin, and the whole of R8's e1–e2.
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

- [x] T002 [US1] **R1 — ready and accepted are read from git** (AC-S39-1). `tests/elapsed_fixture.py` (the scratch git
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

- [x] T003 [US1] **R2 — waiting by cause adds up to elapsed** (AC-S39-2). `measures.py`: `parks(...)`,
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

- [x] T004 [US1] **R3 — worked once, stage time renamed** (AC-S39-3). `measures.py` `stage_seconds(...)`;
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

- [x] T005 [US1] **R6 — the feature's elapsed is not its stage time** (AC-S39-6). `measures.py`
  `feature_figures(...)`; the aggregate's feature line and the page's print `stage time`, `elapsed` and `time with any
  slice in flight` under those names; `--json`'s feature record gains `feature: {elapsed, stage_seconds,
  in_flight_seconds}`. RED→GREEN: e1 three overlapping slices: elapsed < summed stage time; the line carries all
  three names, each its own number · e2 one slice open: elapsed `open since …`, the other two figures still printed.
  Files: `tests/test_benchmark_feature.py`, `assets/toolkit/scripts/agents/measures.py`,
  `assets/toolkit/scripts/agents/benchmark.py`.

- [x] T006 [US1] **R10 — a `/drive` project with no cruise log** (AC-S39-10). Where `specs/cruise-log.jsonl` is
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

- [x] T007 [US2] **R4 — rework is what a non-accepted demo cost** (AC-S39-4). `measures.py` `rework(...)`: every
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

- [x] T008 [US2] **R5 — each request in one record** (AC-S39-5). New `attribution.py`: reads each session's
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

- [x] T009 [US3] **R7 — decision health reads unknown until a tier exists** (AC-S39-7; D159). `measures.py`
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

- [x] T010 [US4] **R9 — `--json` carries what S37 reads** (AC-S39-9), with R8's e3. `summarise()` assembles every
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

- [x] T011 [US5] **R11 — the ladder names the slice and brackets the gate** (AC-S39-2, -5). Factory text only:
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

- [x] T012 [US5] **R12 — what a project already made gets** (AC-S39-12). Last, because it needs every file. A
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

- [x] T013 **Hold the gate** (no new behaviour, no new test). Run and report, changing nothing unless a failure names a
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

## Phase 8: Converge pass 1 — every figure from a record that says it (appended)

Each task closes a class, not the instance found: its RED is the reproduction under *Convergence* below, written as
a test that enters through `benchmark.py` as a `python3 -B` subprocess over `tests/elapsed_fixture.py`'s scratch
project, and its GREEN holds the T001 pin and the identity `worked + causes + unattributed == elapsed` on every
fixture it touches. The Constraints above hold unchanged (≤ 350 lines, `encoding="utf-8"`, no mocking, scratch
under `/tmp/s39/`, `VERSION` stays `1.6.0.dev0`). Order: T014 → T016 → T017 (one file, `attribution.py`, and
`summarise()`), T015 → T018 → T019 (one file, `measures.py`'s readers), then T020, T021, T022, T023.

- [ ] T014 [US4] **HIGH — `read_from.cost` names what the cost was read from** (AC-S39-9; constitution VII).
  `sources()` is passed `bool(found.get("cost"))`, and `attribute()` sets a `cost` on every record, so every record says
  `the transcripts, by delegate and bracket` even when no transcript is on the machine and every figure is the
  entries' recorded usage. Close the class: `attribute()` returns, per record, which entries it read from the
  transcripts and which from recorded usage, and `read_from.cost` (and each `entries[i]`) names that. Where both are
  mixed it names both, with counts. RED: e1 the `test_benchmark_attribution` e7 fixture (empty `HOME`, `costed`
  entries): `read_from.cost` names the recorded usage and never says `transcripts` · e2 one session present and one
  absent: both are named · e3 every `read_from` value in `test_benchmark_feature`'s e2 is asserted against a run with
  and without transcripts, not only for being present.
  Files: `assets/toolkit/scripts/agents/attribution.py`, `assets/toolkit/scripts/agents/measures.py`,
  `assets/toolkit/scripts/agents/benchmark.py`, `tests/test_benchmark_feature.py`, `tests/test_benchmark_attribution.py`.

- [ ] T015 [US1] **HIGH — a slice id is read the same way in every table the ladder writes** (AC-S39-1, -2). Today
  `graph_rows` reads only backticked ids in `depends_on` (measures.py:96), and `added()`/`done()` search with
  `` `<id>` `` (measures.py:152, 164). The generated split template writes `— or id list` and `[ID]`, and
  `done_slices()` (benchmark.py:679) accepts a bare `S1-a`. So a bare `depends_on` drops the dependency and prints a
  doubled elapsed, and a bare register row reads `open since` for a slice `check-benchmark` calls done. Close the class:
  one cell reader in `measures.py` for the graph's first cell, its `depends_on` cell (backticked or bare,
  comma-separated, `—` empty), the register's first cell (the rule `done_slices` uses) and the split's mention. The
  pickaxe needle is the bare id, and the `holds` content check stays exact, so `S1` never matches `S10`. RED: e1 graph
  `` | `S2-b` | S1-a | `` → S2-b's ready is S1-a's row commit and elapsed is 2 days (today 4) · e2 register `| S1-a |` →
  accepted read, not `open since` · e3 a split naming `S2-b` bare → ready read · e4 bare `S1` beside `S10` in all three
  tables: S1's moments are its own.
  Files: `assets/toolkit/scripts/agents/measures.py`, `tests/elapsed_fixture.py`, `tests/test_benchmark_elapsed.py`.

- [ ] T016 [US4] **HIGH — no figure is a bare `0` where nothing was read** (AC-S39-8 "each new figure is derived or
  reads unknown"; R8 e3; the fragment's own claim). Today, with transcripts present, an unbracketed entry is held, so
  its `tokens` is `0` and the record's `cost.tokens` prints a number. Without transcripts the same entry reads `unknown —
  not recorded: the stage was not bracketed`. On this repository that is S00 `mutation`, S01 `gaps` and `plan`, and
  S20 `gaps`. `entries[i].stage_seconds` is `0` for an open entry and for an unbracketed one, against READING's "its
  stage time and tokens are missing, not zero". The pin's e3 is vacuous for waiting (its tree is no git repository, so
  every cause is unknown) and never reads `entries`. Close the class: an unbracketed entry's tokens are unknown in both
  paths, and its record's `cost.tokens` follows one rule in both. An open or unbracketed entry's `stage_seconds` is
  unknown with its reason. The record-level `stage_seconds`/`seconds` keep today's sum and the `+` floor (the pin). RED:
  e1 a fixture with an unbracketed and an open entry, with and without a `Session`: per-entry `stage_seconds` and
  `tokens` unknown, the record's `cost.tokens` the same in both runs · e2 the pin's e3 also run over a dated git copy
  of the 8072724 records, with transcripts and without, and asserting every `entries[i]` figure and every waiting cause.
  Files: `assets/toolkit/scripts/agents/attribution.py`, `assets/toolkit/scripts/agents/benchmark.py`,
  `assets/toolkit/scripts/agents/measures.py`, `tests/test_benchmark_pin.py`, `tests/test_benchmark_attribution.py`.

- [ ] T017 [US2] **HIGH — without transcripts, the overlap check sees every record that could overlap** (AC-S39-5
  "brackets kept in a worktree and on the integration branch do not see each other"; R5 e7). `overlapping()` reads only
  the working tree's records, so on a slice branch a concurrent slice's brackets, which sit on that slice's branch, are
  invisible, and the recorded sum (every sub-agent in the session's window) is printed as the slice's cost. On this
  branch, with an empty `HOME`, S39's `plan` reads 28 417 982 tokens against 3 918 980 attributed, and the record
  100 114 540 against 32 198 975. Close the class: the overlap check also reads every record on local `slice/*` branches
  and the integration branch (`git for-each-ref`, `git show <ref>:<path>`). Where git cannot list them, the recorded sum
  is unknown with that reason. RED: e1 S1 on `slice/S1`, S2's overlapping record committed only on `slice/S2`, empty
  `HOME`: S1's `cost.tokens` reads `unknown — brackets of S2 … overlap` · e2 no branch holds an overlapping bracket: the
  recorded sum stands (today's e7 kept).
  Files: `assets/toolkit/scripts/agents/attribution.py`, `assets/toolkit/scripts/agents/benchmark.py`,
  `tests/test_benchmark_attribution.py`, `tests/elapsed_fixture.py`.

- [ ] T018 [US1] **MEDIUM — a truncated or failing git history is not an absent one**. In a `--depth 1` clone, the
  oldest commit holding every row is the graft, so every done slice reads `elapsed 0`, `worked 0` and every cause `0`.
  `first()` also treats `git log` returning None (a failure) as "no such commit". Close the class: `Reader` says
  `unknown — git history is shallow: …` when `git rev-parse --is-shallow-repository` is `true`, and `unknown — git
  failed: <command>` when a `git log`/`git show` it depends on fails. Only an empty answer means "not found". RED: e1
  the R1 e1 fixture cloned `--depth 1`: elapsed, worked and every cause unknown naming the shallow history · e2 a `git`
  that fails on `log` (a fake `git` first on `PATH` in the test tree): unknown naming the failure, not `open since`.
  Files: `assets/toolkit/scripts/agents/measures.py`, `tests/test_benchmark_elapsed.py`.

- [ ] T019 [US1] **MEDIUM — a cruise log that cannot be read whole leaves review and worker unknown**. `parse_log`
  skips a non-JSON line, and `iterations`/`parks` skip a row without a parsable `started`/`ended`, so a torn park row
  moves its seconds to `worker`/`unattributed` while `read_from.review` says `none present: no park`. A log whose
  times all fail to parse says `none present: no cruise log`. Close the class: the reader keeps what it could not read,
  with its line number. Any such line makes `review`, `worker` and `unattributed` unknown, naming the line, and a log
  that exists is never reported as absent. RED: e1 the park row cut mid-line: review, worker and unattributed unknown
  naming line 1 (today review 0, unattributed 115 200) · e2 every row's `started` with fractional seconds: unknown,
  never `no cruise log` · e3 a clean log: today's figures unchanged.
  Files: `assets/toolkit/scripts/agents/measures.py`, `assets/toolkit/scripts/agents/benchmark.py`,
  `tests/test_benchmark_waiting.py`.

- [ ] T020 [US1] **MEDIUM — a cut-off entry ends at its last line, read as a last line** (AC-S39-3). `Totals.last` is
  each request's *first* line (`read_requests` keeps the first line per key), so the feature's cut-off `ground` entry
  (started 01:44:46Z, lines to 01:44:47Z) "ends at its last transcript line 2026-10-03T01:44:42Z", before its own
  start, and its stage time is clamped to `0`. S14 `gaps` says its transcript "could not be read" when it was read and
  held no request. Close the class: the last line is the latest timestamped line of any request attributed to the
  entry. One that precedes the start leaves the recorded end standing, with a note that the transcript contradicts the
  bracket. Read-with-nothing-found and not-read are two different notes. RED: e1 a cut-off entry whose one request
  writes lines at start−4 s and start+1 s: stage time 1 s, note names start+1 s · e2 a request wholly before the
  start: recorded end, the contradiction noted · e3 transcripts present, no request in the entry: the note says none
  was found.
  Files: `assets/toolkit/scripts/agents/attribution.py`, `assets/toolkit/scripts/agents/measures.py`,
  `tests/test_benchmark_elapsed.py`.

- [ ] T021 [US4] **MEDIUM — every feature's figures are in `--json`, with or without a feature record** (AC-S39-6,
  -9). `json_records()` attaches `feature_figures`, `session_totals` and `decision_health` only to a record with no
  `slice`. A feature whose stages above the slice loop were never bracketed (which `check-benchmark` warns of, but
  which happens) prints all three on the aggregate's line and carries none of them in `--json`, with no unknown and no
  reason. Close the class: each feature in `--json` carries the three once. **Carrier is the host's call**
  (recommendation: on the feature's first slice record in path order where no feature record exists, with
  `read_from.feature_figures` saying so). RED: e1 two slice records and no feature record: the three keys present
  exactly once for the feature · e2 with a feature record: unchanged.
  Files: `assets/toolkit/scripts/agents/benchmark.py`, `tests/test_benchmark_feature.py`.

- [ ] T022 [US3] **MEDIUM — decision health reads no figure over a partial or mis-read set** (AC-S39-7; the
  `218cb7f` class). The median wait per tier is taken over only the entries a skipper bracket holds, and is printed with
  no count: of ten `easy` entries, two held gives `easy 6m00s`. `reviewed`/`reverted` are substring tests on the
  Status line, so `- **Status:** standing — to be ratified at S28` counts as reviewed: 0 % of 3, not flagged, when
  nothing was reviewed. Close the class: each median carries how many entries it was read from, of how many
  (`{median, read, of}`, and the line `easy 6m00s (2 of 10)`). A review verdict is the Status line's first word, in
  `SPELLING`. RED: e1 ten `easy` entries, two held: the line and `--json` name 2 of 10 · e2 three entries whose Status
  says `to be ratified`: the rate unknown, `no tiered entry was ratified or reverted` · e3 today's e2–e5 unchanged.
  Files: `assets/toolkit/scripts/agents/measures.py`, `tests/test_benchmark_feature.py`.

- [ ] T023 **LOW — the fragment and the slice's records say what was built**. The catch-up's list of what `migrate`
  brings leaves out the regenerated `commands/benchmark.md` (`benchmark_command`, src/slipwai/project/benchmark.py:97,
  whose page description changed). Its "never a bare `0`" and "overlapping brackets … read `unknown`" become true only
  with T016 and T017, so re-read them after those land. `data-model.md` still names `feature`/`sessions` (built:
  `feature_figures`/`session_totals`, because the pin holds the old keys), a figure where decision health returns
  `{percent, numerator, denominator, flagged, why}`, and "the skipper bracket" where the shortest holding one is taken.
  The plan's test list lacks `tests/test_benchmark_attribution_chain.py`. RED: `test_benchmark_elapsed_migrate`'s
  catch-up example names `commands/benchmark.md`.
  Files: `changelog.d/benchmark-elapsed.md`, `tests/test_benchmark_elapsed_migrate.py`, `data-model.md`, `plan.md`.

- [ ] T024 [US1] **MEDIUM (host, after pass 1) — time outside any iteration is *worker*, as AC-S39-2 says**
  (AC-S39-2, -10). Where `specs/cruise-log.jsonl` exists, *worker* takes every second from the log's first row's
  `started` to accepted that worked time and the earlier causes did not take — the gaps between iterations and the time
  after the last logged row included ("outside any iteration"); only time before the log's first row stays
  *unattributed*, and with no log every such second stays *unattributed* (R10 unchanged). `read_from` for worker names
  the log and says it counts time outside any iteration. RED: a slice accepted after the log's last row — the seconds
  between that row's `ended` and accepted, unclaimed by any other cause, read as worker (today: unattributed); S08 on
  this repository's records reads 0 s unattributed. Data-model's *worker* row is amended with T023.
  Files: `assets/toolkit/scripts/agents/measures.py`, `tests/test_benchmark_waiting.py`.

**Host decision on T021** (pass 1 asked): a feature with no feature record carries its `feature_figures`,
`decision_health` and `session_totals` on its first slice record in `--json` (path order), and the aggregate is
unchanged.

## Convergence

### Pass 1 — 2026-10-06, cruise iteration 24, `drive-converge` (worktree at `957c808`)

**Verdict: not converged.** 4 HIGH, 5 MEDIUM, 1 LOW, each a task above (T014–T023). Budget: complete, nothing marked
incomplete.

**How it was judged.** No `.codegraph/` exists in this worktree or the main checkout, so symbols were read directly.
The reproductions ran under `/tmp/s39/`: a clone of this worktree, `/tmp/s39/real`, with the main checkout's
`specs/cruise-log.jsonl` copied in, run with the real transcripts and with an empty `HOME`; scratch projects from
`tests/elapsed_fixture.py` under `/tmp/s39/repro/out`; direct calls into `measures.py`/`attribution.py`. Teeth were
checked by mutating the *clone* only and restoring each file with `git checkout -- <path>` there; the worktree was
never mutated. Suites: the 13 targeted modules (102 tests) OK, 1 skipped (`test_changelog`'s history guard);
`make lint typecheck check-structure` clean; no `__pycache__` under `assets/`; no mocking import; every text
`open`/`read_text` names `utf-8` (the two binary opens in `attribution.py` excepted); `VERSION` `1.6.0.dev0`.

**Findings (most severe first), each with its reproduction.**

1. **HIGH — `read_from.cost` is false on every record without transcripts** (T014). `HOME=/tmp/s39/emptyhome
   python3 -B assets/toolkit/scripts/agents/benchmark.py --json` in `/tmp/s39/real`: all 18 records read
   `"cost": "the transcripts, by delegate and bracket"` while their `cost.shared` says `no transcript was read`
   (measures.py:496-497, benchmark.py:891-892, attribution.py:335-336 sets `cost` unconditionally).
2. **HIGH — a bare id in the split or register is misread** (T015). A fixture with graph row `` | `S2-b` | S1-a | ``
   (the template's `— or id list`): S2-b elapsed `345600` (ready = the split commit), against `172800` with
   backticks. A bare register row `| S1-a |`: S1-a reads `open since 2026-10-01T09:00:00Z` and S2-b `not ready: S1-a
   is not done`, while `done_slices()` counts both done.
3. **HIGH — bare zeros where nothing was read** (T016). The real records with transcripts: S00 `mutation`, S01
   `gaps`/`plan` and S20 `gaps` (unbracketed) read `tokens: 0`, `stage_seconds: 0`, and their records' `cost.tokens`
   a number. Without transcripts the same entries read `unknown — not recorded: the stage was not bracketed`. A
   fixture's open `converge` entry reads `stage_seconds: 0`. The pin's e3 (test_benchmark_pin.py:134-150) runs where
   git is absent, so its waiting branch never executes.
4. **HIGH — without transcripts, a concurrent slice on another branch is invisible** (T017). The empty-`HOME` run:
   S39 `cost.tokens` 100 114 540 (the `plan` entry 28 417 982) against 32 198 975 (3 918 980) attributed from the
   transcripts, printed as a number. S14's concurrent brackets live on `slice/S14`, which `overlapping()`
   (attribution.py:216-232) never reads.
5. **MEDIUM — shallow history reads as zero** (T018). The R1 fixture cloned `--depth 1`: S2-b `elapsed 0`, ready =
   accepted = `2026-10-05T09:00:00Z`, `worked_seconds 0`, every cause `0` (deep clone: 172800).
6. **MEDIUM — a torn or unparsable cruise log is read as a smaller one** (T019). Park row 1 (day 4 12:00 → 18:00) cut
   mid-line: review `21600 → 0`, unattributed `0 → 115200`, `read_from.review` `none present: no park`. Every row with
   fractional seconds: `read_from.worker` `none present: no cruise log` with the log present.
7. **MEDIUM — the cut-off end is a first line, and can precede the start** (T020). The aggregate over the real
   records: `(feature) ground: stage time ends at its last transcript line 2026-10-03T01:44:42Z` for an entry started
   01:44:46Z whose window holds lines to 01:44:47Z. Its `stage_seconds` is `0`. `S14-result-contract gaps: … its
   transcript's last line could not be read`, though the transcript was read.
8. **MEDIUM — feature figures vanish from `--json` with no feature record** (T021). Two slice records and no feature
   record: no record carries `feature_figures`, `session_totals` or `decision_health`, while the aggregate prints
   `stage time 2h00m in all; elapsed 96h00m; …`.
9. **MEDIUM — decision health over a partial or substring-matched set** (T022). `decision_health` over ten `easy`
   entries, two held by a 360 s skipper bracket: `median wait: easy 360` with no count. Three entries whose Status says
   `to be ratified at S28`: `misclassification rate 0% (0 of 3 reviewed)`.
10. **LOW — the fragment and records drift from what was built** (T023). See the task.

**Judged and left as built.**
- *An entry with no recorded usage makes `cost.tokens` unknown even when transcripts were read.* This is the honest
  answer. Such an entry has no window (no `span`, no cursor), so the transcripts cannot place its work, and its host
  requests sit in the shared bucket. A number would be a floor presented as a total. T016 makes the unbracketed case
  follow the same rule.
- *`--json` keys `feature_figures`/`session_totals`.* These are right, because the pin holds `feature` (a string) and
  `sessions` (a count) on every old record. *Decision health as objects* and *the shortest skipper bracket holding
  `When:`* are sound. All three are written into the data model by T023.
- *The D65 pin genuinely compares.* `benchmark.py` at `525399b` against the working copy over the `8072724`
  records, cell by cell. Mutating one cell (`converge_passes + 1`) failed it 17 times. `check` is byte-identical.
- *Teeth.* An `unattributed + 1` mutation failed 5 tests (waiting/elapsed); a chain that never finds `drive-slice`
  failed 3; turning off the `218cb7f` partial-ready guard failed 5 plus 1 error; inverting the cost provenance failed 3;
  turning off dedup of a merged bracket failed 1.
- *The identity* `worked + causes + unattributed == elapsed` holds on every accepted slice of the real records (15 of
  15) and by construction (measures.py:470-477). *Token conservation:* `attributed + shared == total` per session by
  construction (attribution.py:312).
- *Scope.* `git diff --name-only 525399b HEAD` is the Structure Decision's paths, this folder, and
  `tests/test_hand_backs_coverage.py`. `tests/test_benchmark_attribution_chain.py` is one test module beyond the plan's
  list (T023). Nothing under `delivery/`. The uncommitted `benchmark.json` change is the host's open `converge`
  bracket, untouched.
- *Factory text.* `drive.md` (parallel_slices.py) and `cruise.md` (cruise.py) say `drive-slice <id>`, and *What each
  stage costs* names `gate` and its bracket, as AC-S39-2/-5 ask.

**Handed back (no task — a reading of the spec, not a defect).** AC-S39-2 lists *worker* as "no bracket of the
slice open, **or outside any iteration**". The data model and code count seconds outside the cruise log's span as
*unattributed*: the more conservative reading, which leaves S08 with 20 s unattributed after iteration 23's end. The
host can keep it, and say so in the AC, or ask for those seconds under *worker*.

**Not judged.** AC-S39-11 is the demo. The code produces what `quickstart.md` steps 1–4 expect: the columns, three
named feature figures, decision-health unknowns, S08's `implement` delegates all `S08 …`, and `attributed + shared ==
total` per session. One exception is S08's dependency: `quickstart.md` derives it as 9 712 s "less any S08 bracket",
and the code gives 7 538 s; the demo's hand derivation is where that is checked. The shared bucket of a session
whose requests serve two features is summed into both features' `shared` (attribution.py:346). This repository has
one feature, so that was not reproduced.

**Constitution, by principle the diff touches.**
- **I (a generated project owns its files)**: `check()` is unchanged (benchmark.py:707-742) and pinned byte for byte
  (test_benchmark_pin.py:152-155). `migrate` carries the modules (test_benchmark_elapsed_migrate.py:112). The catch-up
  note exists (changelog.d/benchmark-elapsed.md:5) but its file list is incomplete (T023).
- **III (simplicity)**: the two new modules are justified at plan.md:85-86 and loaded by path, bytecode off
  (benchmark.py:99-121).
- **V (acceptance-driven)**: every example enters through `benchmark.py` as a subprocess (elapsed_fixture.py:172-174),
  and the tests have teeth (above).
- **VII (auditability)**: `read_from` per figure (measures.py:480-498) is **unmet** where it is false or a figure is
  a bare `0` (T014, T016), and where a partial record is read as whole (T015, T017-T022).
- **VIII (versioning)**: the fragment's first line is `MINOR`; `VERSION` is `1.6.0.dev0`. The `--json` `rework` key's
  move is named in the catch-up and held by the pin (`RENAMED_KEYS`, test_benchmark_pin.py:34).
- **II, IV, VI**: not touched. No write endpoint, no domain/adapter code, no third-party adapter; transcripts and
  `meta.json` are read at `attribution.py`'s boundary into its own `Request`/`Session`.

**By level.**
- *Domain* (`measures.py`, `attribution.py`): the identity and attribution are proven. Reading partial or
  differently-spelled records is not (T015, T018-T020, T022).
- *Use case* (`summarise`, `json_records`, `aggregate`): figures are assembled. Provenance, bare zeros and feature
  figures are not right (T014, T016, T021).
- *Delivery adapter* (the CLI and the generated `drive.md`/`cruise.md`/`benchmark.md`): proven by
  `test_benchmark_elapsed_migrate`. The catch-up's file list is not (T023).
- *Screen*: the overview page's columns, headings and decision-health section are proven by the tests and by
  `/tmp/s39/aggregate.txt`. Its figures inherit the defects above.
- *Published contract* (`--json`, the fragment, `benchmark.json` untouched): the old keys are proven by the pin. The
  new keys' truthfulness is not (T014, T016, T017, T021).
