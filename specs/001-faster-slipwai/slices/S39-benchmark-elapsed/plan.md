# Implementation Plan: S39-benchmark-elapsed — time waited told apart from time worked

**Branch**: `slice/S39-benchmark-elapsed` (worktree `../slipwai-graph-S39-benchmark-elapsed`, cut from `adopt-method` at
`525399b`; the local branch is the claim, no push — D129) | **Date**: 2026-10-06 |
**Spec**: [spec.md](../../spec.md), *Slice acceptance criteria* → `### S39-benchmark-elapsed (method slice)`
(AC-S39-1 … AC-S39-12)

**Input**: FR-049 and FR-057 in [spec.md](../../spec.md); the slice's split and graph rows in
[story-split.md](../../story-split.md); D159 (with D129, D130, D132 and D65 it cites) in
[decisions.md](../../decisions.md); the owner brief `.specify/product-owner.md`; `AGENTS.md` (MINOR, one fragment).
Written by cruise iteration 24's plan stage, inside the slice's `drive-slice` delegate (host model, its own context).

## Summary

`make benchmark` today adds up each slice's stage brackets and prints the sum under the feature heading as if it
were elapsed time, and it charges every request in a bracket's byte window to that bracket — so three slices run at
once each pay for the other two's delegates. S39 keeps every record as it is and derives, at read time, what the
records and git already say: when a slice became ready and when it was accepted (git), how much of that interval it
was worked (the union of its brackets), how the rest was spent waiting (dependency, worker, review, integration,
each from a named record, the remainder *unattributed*), what rework after a non-accepted demo cost, and which slice
each request belongs to (the spawn chain in the harness's `meta.json`, a *shared* bucket for a line tied to none).
FR-057's decision health is built and reads *unknown* until a decision carries a tier. The derivation lives in two
new modules beside `benchmark.py` — `measures.py` (moments, waiting, rework, feature figures, decision health) and
`attribution.py` (requests to records) — which `benchmark.py` loads by path. The `wall` column is renamed *stage
time*; the feature heading prints stage time, elapsed and *time with any slice in flight* under three names. The
ladder text fixes each `drive-slice` delegate's description as `drive-slice <id>` and adds a host-bracketed `gate`
stage around the full gate after a merge. MINOR, one fragment `changelog.d/benchmark-elapsed.md`; `VERSION` stays
`1.6.0.dev0`.

## The example map

Rules are numbered; each is one RED-GREEN-REFACTOR increment (constitution V). *The scratch project* is a git
repository made by the test with `project.json`, `specs/f/story-split.md` (a `## Slice graph`),
`specs/f/slices/README.md` (the register), records, and commits dated with `GIT_COMMITTER_DATE`; *the transcripts*
are files under a fake `HOME`'s `.claude/projects/<slug>/`, each sub-agent with its `meta.json`. Every example
runs `assets/toolkit/scripts/agents/benchmark.py` as a subprocess with `python3 -B`. Field names, the moments'
derivation and the attribution order are in [data-model.md](data-model.md).

| Rule | Criteria | What it says | Examples |
|---|---|---|---|
| **R1** ready and accepted are read from git | AC-S39-1 | *ready* = the later of the first commit whose `story-split.md` names `` `<id>` `` and, per `depends_on` in the slice's `## Slice graph` row, the first commit holding that dependency's done mark (a register row, or `status: implemented` in `docs/event-model/model.yaml`); *accepted* = the first commit holding the slice's own done mark. Elapsed = accepted − ready, commit times in UTC. The moments *demo accepted* (the first `demo` entry with `outcome=accepted`, its `ended`) and *merged* (the oldest merge commit whose subject names `slice/<id>`) are shown inside the interval. With no done mark, elapsed reads `open since <ready>`, never a number; with no ready, unknown with the reason | e1 split commit day 1, dependency's row day 2, own row day 4: elapsed 2 days to the second, ready names the dependency's commit · e2 a merge commit and an accepted demo before the row: both moments printed inside the interval, the merge before the row · e3 no own row: `open since 2026-…Z`, and `--json` `elapsed` is `{"unknown": "open since …"}` · e4 a dependency with no done mark: `{"unknown": "not ready: <dep> is not done"}` · e5 the slice in no split and no model: unknown, naming `story-split.md` · e6 the event profile: the dependency's and the slice's `status: implemented` commits in `model.yaml` stand in for register rows |
| **R2** waiting by cause adds up to elapsed | AC-S39-2 | Inside [ready, accepted], after the worked union (R3) is taken out, each second goes to the first cause that claims it: *integration* (merged → accepted, and every `gate` bracket), *dependency* (demo accepted → the last landing of a sibling earlier in split order, before the slice's own merge — a landing being the sibling's merge commit, or its done mark where it has none), *review* (a cruise-log iteration ending `stopped: human` → the next iteration's start; a `demo` bracket with no `driver` signal, a person at the demo), *worker* (inside the cruise log's span and not a park: no bracket of the slice open), the rest *unattributed*. Each cause names the record it was read from. worked + the four causes + unattributed = elapsed, to the second | e1 the sibling-merge fixture (accepted demo, a sibling's merge, own merge, a gate bracket, own row): dependency = demo → sibling's merge, integration = merge → row less the bracketed fix, the gate inside integration · e2 a park inside the interval: review = its length · e3 the identity holds on every fixture · e4 a person's patch the slice needs: no record says it (Q2); the time stays where the other rules put it |
| **R3** worked once, stage time renamed | AC-S39-3 | The slice's *worked* time is the union of its brackets (a `gate` bracket and a person's `demo` bracket excepted — R2 owns them), so a nested skipper counts once. A `cut_off` entry's stage time ends at the last transcript line attributed to it (R5) where one is read, and the report says so with both moments; otherwise its recorded end stands and the note says why. The `wall` column, the stage table's `wall` and the per-slice heading read *stage time*; no heading prints summed stage time as elapsed | e1 skipper 10:10–10:20 inside implement 10:00–11:00: stage time 70 m, worked 60 m · e2 an entry cut off 3 h after its last line: stage time ends at that line, the note names both · e3 a cut-off entry whose transcript is gone: recorded end, the note says the transcript could not be read · e4 the aggregate's header and the page's column say `stage time`; the feature line says `stage time … in all`, never `… in all` alone |
| **R4** rework is what a non-accepted demo cost | AC-S39-4 | Rework = every entry after a `demo` whose outcome is `behaviour` or `implementation`, up to (not including) the next `demo`; its seconds (stage time) and tokens (R5's attribution) are counted, and they are inside the slice's cost. An entry after an `accepted` demo is not rework. The old count of stages re-entered above `gaps` keeps its values under the name `re-entered` | e1 S08's shape (demo `implementation`, implement, demo `implementation`, implement, demo `accepted`, implement): rework = the two middle implements, their seconds and tokens; the last implement is not rework · e2 a slice with no demo: rework 0 s, 0 tokens · e3 the trailing entries after a non-accepted demo with no next demo yet are rework |
| **R5** each request in one record | AC-S39-5 | A request (one `requestId`) in a sub-agent transcript whose `meta.json` chain (`parentAgentId` upwards) reaches a `drive-slice` is that slice's: the description `drive-slice <id>` (or, for transcripts written before the convention, its first word) names the record; it goes to that record's bracket covering it, else to the record outside any bracket. A request tied to no `drive-slice` goes to a covering bracket that a `drive-slice` did not open (the opener is the transcript that printed `benchmark: <stage> started (<record>` just after the bracket's cursor); when such brackets of two records cover it and no stage owns the delegate's type in exactly one of them, and when none covers it, it goes to the feature's *shared* bucket. Within one record the existing innermost/owner rule picks the entry. Across every record of the project and the shared bucket, each request is counted once, and per session the sum equals the session's distinct-request total | e1 two slices' implement brackets open at once, each with `drive-implement` delegates under its own `drive-slice`: each slice's cost holds only its own delegates' requests · e2 a host-spawned delegate inside a `drive-slice`-opened bracket: not that slice's · e3 a host line covered by two slices' host-opened brackets: shared · e4 records merged from a worktree and the integration branch both covering one request: counted once · e5 records + shared = the session total · e6 a `drive-slice` description naming no record: its requests are shared, with a note · e7 no transcripts on the machine: cost is the recorded sum where no other record's bracket overlaps, else unknown with that reason |
| **R6** the feature's elapsed is not its stage time | AC-S39-6 | Per feature: elapsed = first slice ready → last slice accepted (open while any recorded slice is), stage time = every record's stage time summed, and *time with any slice in flight* = the union of every slice record's brackets. The aggregate's and the page's feature line print the three under those names | e1 three overlapping slices: elapsed < summed stage time; the line carries `stage time`, `elapsed` and `time with any slice in flight`, each with its own number · e2 one slice open: elapsed `open since …`, the other two figures still printed |
| **R7** decision health reads unknown until a tier exists | AC-S39-7 | Per feature, from `decisions.md`: the escalation share (entries scored `easy` or `guarded` whose `Reversibility:` line records an escalation to `hard`, over entries scored `easy` or `guarded`; flagged outside 5–15 %), the misclassification rate (entries `revert`ed over entries `ratify`d or `revert`ed; flagged over 5 %), and the median wait by tier (the skipper bracket holding the entry's `When:`). With no `Reversibility:` line anywhere each reads `unknown — no decision entry carries a Reversibility: line`, and no figure is printed. The line's spelling is Q1's | e1 this repository's log: three unknowns, no `%` · e2 20 `easy`/`guarded` entries, 4 `guarded → hard`: `20%`, flagged · e3 1 reverted of 10 reviewed: `10%`, flagged; 0 of 10: `0%`, not flagged · e4 tiers but no review: the rate is unknown, naming that no entry was ratified or reverted |
| **R8** old records still read the same | AC-S39-8 | Over the 16 records committed at `8072724`, the aggregate of `benchmark.py` at `525399b` and the new one agree on every column S39 does not rename (`wall` → `stage time` and `rework` → `re-entered` keep their values); every new figure is derived or reads `unknown — <reason>`; `check` prints the same lines | e1 the two aggregates over the same tree: equal cells, column by column · e2 `check-benchmark`: byte-identical stdout, stderr and exit · e3 no new figure is a bare `0` where nothing was read |
| **R9** `--json` carries what S37 reads | AC-S39-9 | Each record in `--json` gains `elapsed`, `stage_seconds`, `worked_seconds`, `waiting{dependency, worker, review, integration, unattributed}`, `rework{seconds, tokens}`, `cost{tokens, shared}` — each a number or `{"unknown": "<reason>"}` — `moments`, `read_from` (the record each figure came from) and `entries` (per stage: stage time, attributed tokens, the delegates counted). The old `rework` list is `reentered`. The page's *Reading these numbers* gains one sentence on elapsed against stage time | e1 every key present on every record, each a number or an unknown object · e2 `read_from` names a commit, `specs/cruise-log.jsonl`, `decisions.md` or a bracket for each figure · e3 the reading paragraph's sentence |
| **R10** a `/drive` project with no cruise log | AC-S39-10 | With no `specs/cruise-log.jsonl`, elapsed and stage time are reported, worker and review (their cruise half) read nothing, the time they would hold is *unattributed*, and the run exits 0 with no warning about the log | e1 a generated project, one slice with brackets, a register row: elapsed and stage time printed, waiting all unattributed but integration and dependency where git says so, exit 0, stderr empty |
| **R11** the ladder names the slice and brackets the gate | AC-S39-2, -5 | The generated `commands/drive.md` (*Running ready slices concurrently*) and `commands/cruise.md` describe every `drive-slice` delegate as `drive-slice <id>`; *What each stage costs* gains the `gate` stage — the host brackets the full gate run after a slice's merge in the slice's record — and the `end` table its row; `LADDER` knows `gate`; the `/benchmark` command's page description says *stage time* and elapsed | e1 a generated project, both profiles: `drive-slice <id>` in both commands · e2 *What each stage costs* names `gate` and its bracket · e3 `benchmark.py start … gate` then `end … gate` records an entry sorted after `mutation` |
| **R12** what a project already made gets | AC-S39-12 | A project generated by the factory at `525399b` with records from before S39, migrated by this one: `scripts/agents/measures.py` and `attribution.py` arrive, `make benchmark` succeeds and `check-benchmark` warns of nothing new; the fragment claims MINOR and its one **Catch-up.** paragraph stands alone, naming what changed and that nothing must be redone | e1 generated at `525399b`, records written, migrated: both modules, `make benchmark` exit 0, the new columns · e2 the fragment's first line is `MINOR`, its catch-up names the rename, the `--json` key and that no record is rewritten |

AC-S39-11 is the demo, which this delegate stops before ([quickstart.md](quickstart.md) is its script). Every other
criterion is covered: 1 (R1); 2 (R2, R11); 3 (R3); 4 (R4); 5 (R5, R11); 6 (R6); 7 (R7); 8 (R8); 9 (R9); 10 (R10);
12 (R12).

## Technical Context

**Language/Version**: Python ≥ 3.10 standard library only (toolkit scripts a project runs, as `check-python` holds);
Python 3.11+ for the factory (`src/slipwai/`).
**Primary Dependencies**: none new. `git` on the PATH, which `benchmark.py` already calls (`git()`, line 91).
**Storage**: none new. Every record stays as written (D65); every figure is derived at read time from the records,
git, `specs/cruise-log.jsonl`, `decisions.md` and the harness transcripts. No field is added to `benchmark.json`
except the `gate` stage's ordinary entries.
**Testing**: `unittest` in `tests/`; scratch git repositories in temporary directories, scripts run as subprocesses
with `python3 -B` and a fake `HOME` for transcripts; `benchmark.py` at `525399b` taken from git for R8, as
`test_hand_backs_record.py` takes `c3c760b`; generated projects for R10–R12. No mocking framework. Each new module
≤ 350 lines.
**Target Platform**: wherever a generated project's agents run; Linux and macOS for the factory's tests.
**Performance Goals**: none stated. Reading a session's transcripts is linear in their size; only lines carrying
`"usage"` are parsed, and each session is read once per run. `check` reads no transcript.
**Constraints**: D65 — nothing a project already has may newly fail or warn (R8, R12); FR-049 — summed stage time
never printed as elapsed (R3, R6); constitution VIII — readers tolerate a record without any new field (R8).
**Scale/Scope**: one script, two new modules, three generator modules, one fragment.

## Constitution Check

The factory's constitution (`.specify/memory/constitution.md`):

- **I. A generated project owns its files and passes its own gate** — `check-benchmark` warns of nothing new and
  `make benchmark` succeeds on records written before S39 (R8, R12); `migrate` brings the two modules. The starters'
  own `make verify` in the matrix is not rerun on this branch (the host's brief rules out the full gate); it runs at
  the merge root. Here the touched modules and `make test TESTS="test_toolkit test_utf8_io test_changelog"` run.
- **III. Simplicity** — derived at read time, so no record format changes and nothing is migrated; two modules
  because `benchmark.py` is already 1056 lines and attribution is its own concern.
- **V. Acceptance-driven** — every example enters through `benchmark.py` as a subprocess or `slipwai
  generate`/`migrate`.
- **VII. Auditability** — every figure names the record it was read from (`read_from`), and a figure no record
  supports reads `unknown — <reason>`: the converge class *every figure that could be printed from a record that
  does not say it*.
- **VIII. A persisted schema is a contract** — `benchmark.json` is untouched; `--json` gains keys, and the one key
  whose meaning moves (`rework`) is renamed rather than reused silently, and the fragment says so.
- **XIV. Agent-generated change** — the spellings FR-057 needs before S26 writes any (Q1) and the patch half of
  *dependency* (Q2) are handed back below; nothing here mints a decision number.

## Structure Decision

One deployable, `slipwai-graph` (`kind: tool`, D3). The change lands under `assets/` and `src/slipwai/project/` and
reaches this repository only through `slipwai migrate` (D130); this checkout's `delivery/scripts/` is a control and
is not edited — here attribution stays by delegate type until a person migrates (AC-S39-12).

**Toolkit (what a project runs)**

- `assets/toolkit/scripts/agents/measures.py` *(new)*: `moments(...)` (ready, accepted, demo accepted, merged, from
  git), `parks(...)` and `iterations(...)` (from the cruise log), `waiting(...)`, `worked(...)`, `stage_seconds(...)`,
  `rework(...)`, `feature_figures(...)`, `decision_health(...)`, interval helpers.
- `assets/toolkit/scripts/agents/attribution.py` *(new)*: reads each session's transcripts once, resolves each
  sub-agent's chain from `meta.json`, finds each bracket's opener, and assigns each request to a record and entry or to
  the shared bucket; returns per-entry tokens, delegates and last-line moments, per-record cost, per-session totals.
- `assets/toolkit/scripts/agents/benchmark.py`: loads both by path with `sys.dont_write_bytecode` (as
  `hand_back_lines` loads `hand_backs.py`); `LADDER` gains `gate` after `mutation`; `summarise()` gains the new keys
  (`feature_figures`, `session_totals` and `decision_health` once per feature; `branch_records()` reads the records on
  local `slice/*` branches and `main`/`master` for the overlap check) and moves the old `rework` list to `reentered`; `COLUMNS`, `STAGE_COLUMNS`, `LEGEND`, `READING`, the feature
  heading and the page's slice heading as R3, R6, R9 say; a waiting table after the slice table; the decision-health
  lines; the notes for cut-off stage time and unresolved `drive-slice` descriptions. `check()` is unchanged.

**Factory source**

- `src/slipwai/project/benchmark.py`: *What each stage costs* — the `gate` stage and its bracket, the `end` table's
  row, one sentence on elapsed against stage time; `/benchmark`'s description of the page (`stage time`, elapsed,
  waiting).
- `src/slipwai/project/parallel_slices.py`: the `drive-slice` delegate described as `drive-slice <id>`; the full gate
  after a merge bracketed as the slice's `gate` stage.
- `src/slipwai/project/cruise.py`: the fan-out sentence names the description (in place; the module is at 336 lines).
- `changelog.d/benchmark-elapsed.md` *(new)*: MINOR, one standalone **Catch-up.** paragraph.

Not changed: `VERSION`, `catalog.json`, `benchmark.json`'s shape, `check()`, `delivery/` in this checkout, and every
record under `specs/` but this slice's folder.

**Tests** *(new modules, each ≤ 350 lines)*

- `tests/elapsed_fixture.py` — the scratch git project, dated commits, records, the fake `HOME` with transcripts and
  `meta.json`, `bench(...)` as a subprocess.
- `tests/test_benchmark_elapsed.py` — R1, R3.
- `tests/test_benchmark_waiting.py` — R2, R10.
- `tests/test_benchmark_attribution.py` — R4, R5.
- `tests/test_benchmark_attribution_chain.py` — R5, by spawn chain: a request belongs to the slice whose `drive-slice`
  spawned it.
- `tests/test_benchmark_feature.py` — R6, R7, R9.
- `tests/test_benchmark_pin.py` — R8 (the pin, written and green before the first change).
- `tests/test_benchmark_elapsed_migrate.py` — R11, R12.

Existing tests that assert `wall` or the `rework` list (`tests/test_benchmark*.py`) are updated in the increment that
renames, and only there.

## Pin

S39 changes an existing script, so today's output is pinned first (AC-S39-8): `tests/test_benchmark_pin.py` runs the
aggregate, `--json` and `check` of `benchmark.py` at `525399b` (taken from git with `hand_backs.py` beside it) over
the 16 records as committed at `8072724`, and the working copy's over the same tree, and holds every column S39 does
not rename equal. Before any change it compares the script with itself and is green; the renames are written into it
as the increments land. Beside it, `tests/test_benchmark*.py`, `tests/test_toolkit.py`, `tests/test_utf8_io.py` and
`tests/test_changelog.py` run before the first increment and after the last.

## Open questions

Neither blocks the plan; each is written for the host to number or overrule, and the plan proceeds on the
recommendation, which is one table in `measures.py` either way.

**Q1 — How does a decision entry record a tier, an escalation, and a review's verdict?** AC-S39-7 needs a fixture of
20 entries with 4 *escalated to hard*, and a misclassification rate; S26 writes the `Reversibility:` line and S28 the
ratify/revert statuses, and neither has started. FR-029 fixes the line and its three words. Options: (a) read
`- **Reversibility:** <tier>`; an escalation as `<tier> → hard` on that line (`->` too), FR-056's one tier at a time
recorded where the tier is; a review's verdict from the `Status:` words FR-031 already names, `ratified` and
`reverted`; a wait from the skipper bracket (any record of the feature) whose interval holds the entry's `When:`;
(b) a separate `- **Escalated:**` line, which S26 would have to add; (c) build nothing past the unknowns until S26.
**Recommend (a)**: it adds no field S26 or S28 does not already own, D159 chose to build the metrics now, and S26's
gaps stage can take or change the spelling in one table. AC-S39-7's first half — every figure unknown on this
repository's log — holds under any option.

**Q2 — Where does *a person's patch the slice needs* come from?** AC-S39-2 counts it under *dependency*, and no record
in this repository or a generated one marks a wait as one: a park for a patch and a park for a review are the same
cruise-log line (`stopped: human`). Options: (a) every park is *review*, and the patch half of dependency counts
nothing until a record names such a wait (FR-046's coordination tool, S34a, is where one would be written);
(b) call a park *dependency* when a commit inside it touches a path the slice may not write. **Recommend (a)**: (b)
reads a cause from a heuristic, which is the figure the converge class forbids; the time is still accounted for,
under review.
