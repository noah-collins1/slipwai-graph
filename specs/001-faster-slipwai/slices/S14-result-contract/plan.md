# Implementation Plan: S14-result-contract — every delegate hands back the same structured result

**Branch**: `slice/S14-result-contract` (worktree `../slipwai-graph-S14-result-contract`, cut from `adopt-method` at
`c3c760b`; the local branch is the claim, no push — D129) | **Date**: 2026-10-05 |
**Spec**: [spec.md](../../spec.md), *Slice acceptance criteria* → `### S14-result-contract` (AC-S14-1 … AC-S14-19)

**Input**: User Story 6, FR-017 and SC-008 (first half) in [spec.md](../../spec.md); the slice's row and graph row in
[story-split.md](../../story-split.md); D134, D135, D136 in [decisions.md](../../decisions.md); ADR 0006 (`Proposed`)
under `delivery/docs/adr/`. Written by cruise iteration 23's plan stage, inside the slice's `drive-slice` delegate
(host model, its own context).

## Summary

A generated project's ten `drive-*` agent types end every hand-back with one fenced `result-contract` block: one
JSON object, `contract: 1`, the thirteen fields D134 fixes, `status` drawn from the set for its type. The shape is
written once, on a new page `docs/result-contract.md` that every type's standing brief points at, the way each points
at `docs/delegated-agent-safety.md`. The session that dispatched a delegate appends its block, verbatim, to the
slice's append-only `hand-backs.md` through a new `check-decisions.py` verb that validates with the gate's own
function and writes the heading itself; a delegate that returns no block is asked once, through a continuation, and
otherwise gets a `- **Missing:** <reason>` line. `check-decisions` holds every `hand-backs.md` it finds to the shape,
one line per fault naming the file, the entry's heading and the field, and passes a project with no record exactly as
it does today. A third verb lists, for converge, each delegated stage in `benchmark.json` against the record — the
source of the converge finding — and `make benchmark` prints *hand-backs with a result contract: n of m* per slice.
The drive ladder gains one section saying who appends, when, the continuation, and the checks at the demo and
adversary stops; the cruise command points every skipper, hand and bosun dispatch at it. MINOR, one fragment
`changelog.d/result-contract.md`; `VERSION` stays `1.6.0.dev0`.

## The example map

Rules are numbered; each is one RED-GREEN-REFACTOR increment (constitution V). *The gate* is
`python3 scripts/check-decisions.py` with no arguments, run in a scratch project; *the record* is a `hand-backs.md`.
Field rules, line spellings and the verbs' grammar are in [data-model.md](data-model.md).

| Rule | Criteria | What it says | Examples |
|---|---|---|---|
| **R1** a well-formed block passes | AC-S14-3, -5 | A record holding one entry under a `## <UTC> — <type> — <stage>` heading with one `result-contract` fence around one JSON object carrying all thirteen fields, each of its type, passes; a list field may be `[]`; a key outside the thirteen is ignored; `contract` > 1 passes with one `check-decisions: note:` naming the entry and no field is held | e1 the page's example block passes, exit 0, the summary line counts *1 hand-back(s) in 1 record(s)* · e2 every list field `[]` passes · e3 an extra key `"elapsed": 4` passes with no note · e4 `"contract": 2` with every other field absent passes with one note naming the heading |
| **R2** a malformed block names its field | AC-S14-4, -7, -8, -9 | Each fault is one stderr line `<record>:<line>: <heading> — <field>: <fault>`, exit 1: a field absent; a value of the wrong JSON type (`true` is not an integer); `contract` not `1`; `delegate` not one of the ten; `status` outside the set for that `delegate`; an empty `scope` or `change_summary`; a list holding a non-string; a `files_changed` path absolute (`/…`, `\…`, `C:…`) or with a `..` segment; a `decisions` id not `^D[0-9]+$` or naming no `## D<n>` heading in the feature's `decisions.md`; `difficulty_observed` not an object of exactly an integer `score` 1–5 and a non-empty string `reason`; `delegate` differing from the heading's type. Two faults in one block are two lines | e1 no `files_changed`: one line naming `files_changed` · e2 `"tests": "make test"`: names `tests` · e3 `drive-hand` with `"status": "green"`: names `status` and lists `accepted, behaviour, implementation` · e4 `["/etc/passwd"]` and `["../x"]`: each names `files_changed`; `[]` passes · e5 `["D9999"]` with no such entry and `["d12"]`: each names `decisions` · e6 `{"score": 6, "reason": "x"}`, `{"score": 3}`, `"3 — hard"`: each names `difficulty_observed` · e7 two faults, two lines |
| **R3** a record's structure | AC-S14-6, -13 | One finding, naming the entry, for: a `result-contract` fence not closed before the next `## ` heading or the end; two blocks in one entry; a `## ` heading not in the shape (time not `YYYY-MM-DDTHH:MM:SSZ`, type not `drive-` and a name, no stage); an entry with neither a block nor a `- **Missing:** <reason>` line, or with both; a body that is not one JSON object. A `Missing:` entry with any non-empty reason passes — `stopped: <reason>` included, so a stopped or cut-off delegate is not charged with a malformed block. Text before the first `## ` heading is the file's own | e1 an unterminated fence · e2 two blocks under one heading · e3 `## yesterday — drive-gaps — gaps` · e4 a heading followed only by prose · e5 `{"contract": 1,` (does not parse) and `[1, 2]` (not an object) · e6 `- **Missing:** stopped: the run was stopped mid-pass` passes · e7 a `# Hand-backs — S1` title and a paragraph before the first entry pass |
| **R4** nothing recorded, nothing changes | AC-S14-16 | `check-decisions` reads `specs/*/hand-backs.md` and `specs/*/slices/*/hand-backs.md`. Where neither exists its stdout, stderr and exit are byte-identical to the checker at `c3c760b`, on an empty project, a project with decisions and demos, and this repository's own `specs/`; where one exists, the summary line gains `, <n> hand-back(s) in <m> record(s)` and nothing else moves | e1 the three trees through both checkers: equal triples · e2 a tree whose only record is `hand-backs.md` is not *nothing recorded yet* · e3 a malformed record and a malformed decision both report, one header |
| **R5** the dispatching session appends | AC-S14-10, -11, -13 | `check-decisions.py --hand-back <dir> <type> <stage>` reads a delegate's whole hand-back on stdin, takes the one `result-contract` block out of it, checks it with R2's and R3's own functions (the decisions ids against the feature's log) and, only when it passes, appends `## <now, UTC> — <type> — <stage>`, a blank line and the fence verbatim to `<dir>/hand-backs.md`, creating it with a `# Hand-backs — <id>` title; otherwise it appends nothing, prints the faults, exits 1. `--hand-back-missing <dir> <type> <stage> <reason…>` appends the heading and `- **Missing:** <reason>`. `<dir>` is `specs/<feature>` or `specs/<feature>/slices/<id>` and nothing else; the verbs only append — bytes already in the file are never rewritten | e1 a hand-back with prose and a valid block: the record ends with the heading and the block byte for byte · e2 a malformed block: the field line, exit 1, the file unchanged · e3 no block: *no result-contract block*, exit 1, unchanged · e4 two blocks: refused · e5 `--hand-back-missing … malformed: status`: appended, and the gate passes it · e6 `<dir>` `apps/x`, or a path outside `specs/`: usage, exit 2 · e7 a second append keeps the first entry's bytes |
| **R6** what was handed back, per stage | AC-S14-11, -15 | `check-decisions.py --hand-backs <slice-dir>` lists, for each ended `benchmark.json` entry the transcript shows was delegated, whether the record holds a passing block for that stage inside the entry's window, a `Missing:` line (its reason), or nothing; an entry the harness could not attribute (no usage read) is listed as such and counted as neither; exit 0 always (it is a reading, converge decides). `make benchmark` prints, per slice with any delegated or unattributed entry, `<slice>: hand-backs with a result contract: <n> of <m>` with `; <k> stage(s) the harness could not attribute — not counted` where k > 0 | e1 two delegated entries, one with a block, one with nothing: `1 of 2`, the verb lists `implement … block` and `converge … nothing` · e2 a `Missing:` entry counts in m and not n · e3 an entry with `usage.source` null: *could not attribute*, not in m · e4 a slice with no record: `0 of m`, and no line where m = k = 0 · e5 a block whose time falls outside every window does not count |
| **R7** every brief ends with the block | AC-S14-1, -2, -14 | Every one of the ten generated agent files, at the root and under `delivery/`, carries in its shared part one paragraph: end the hand-back with one `result-contract` block, shape on `docs/result-contract.md`, this type's `status` set spelled, anything it started reporting inside its one block; `drive-slice`'s brief adds that inside its worktree it is the dispatching session for its sub-delegates and appends their blocks to its slice's record; the bosun's and hand's return words are their block's `status`; the skipper returns the entry, then the block. No brief says *return X* in a way the block contradicts. `make agents` carries the paragraph into every projected file | e1 for each type in `types()`, generated at the root and under `delivery/`: the paragraph, the page path as that layout spells it, its own set · e2 the claude, codex and gemini projections carry it · e3 the bosun's `unblocked`/`cannot`/`catastrophic` and the hand's three verdicts are named as `status` · e4 `drive-slice` names its slice's record |
| **R8** the ladder says who records, when | AC-S14-1, -10–-14 | `commands/drive.md` gains *What every delegate hands back* after *Who runs each stage*: the dispatching session appends each block with `--hand-back` before it closes the stage's benchmark entry, a slice's stages to its own folder and feature-level stages (the split, the ready set's `drive-slice` delegates, the completion audit) to `specs/<feature>/hand-backs.md`; no block, or a refused one, gets one continuation of the same delegate asking only for the block, then `--hand-back-missing` with `refused`, `malformed: <field>` or `no continuation`; the stage is never re-run for it and the session never writes a block; a stage run in this context has no entry; a stopped delegate's entry is `stopped: <reason>`; before the hand (the demo stop) the hand-backs since the last converge pass are checked, at the adversary stop the hand's, the adversary's and mutation's, a miss there is a task and never re-opens converge. The convergence rung says converge reads `--hand-backs` and a delegated stage without a passing block is a finding naming the stage and type; the converge brief says the same. `commands/cruise.md` says the skipper's entry goes to `decisions.md` and its block to the record, and that every skipper, hand and bosun dispatch is recorded the same way | e1 a generated `commands/drive.md` (both profiles, both layouts) carries the section and the verbs as the layout spells them · e2 the convergence rung and the converge brief name `--hand-backs` · e3 `commands/cruise.md` carries the skipper sentence and the pointer |
| **R9** the shape is one table | AC-S14-1, -3 | `docs/result-contract.md` lists the thirteen fields in order with their rules, the ten types with their status sets, the heading, the `Missing:` forms and the three verbs, and its tables equal `hand_backs.FIELDS` and `hand_backs.STATUSES`; `src/slipwai/project/result_contract.py`'s status table equals the script's; `docs/README.md` indexes the page | e1 the page's field table rows equal `FIELDS` · e2 its status rows equal `STATUSES`, and so does the factory's · e3 the index lists the page |
| **R10** what a project already made gets | AC-S14-17 | A project generated by the factory at `c3c760b`, migrated by this one: `scripts/hand_backs.py` and `docs/result-contract.md` arrive, the agent files, `commands/drive.md`, `commands/cruise.md` and `check-decisions.py` are the new ones and re-projected, `make check-decisions` passes on its existing records unchanged; the same for an adopted repository under `delivery/`. The fragment claims MINOR and its **Catch-up.** paragraph stands alone: nothing is asked of existing logs; a slice with no `hand-backs.md` is not refused | e1 generated at the root, migrated: the files, the paragraph in `agents/drive-gaps.md` and its claude projection, gate green · e2 the adopted fixture under `delivery/` · e3 the fragment's first line is `MINOR` and its one catch-up paragraph names both |

AC-S14-18 (the shared-surface rule) is held by the diff itself: `git diff --name-only c3c760b` lists only paths under
the *Structure Decision* below, and the converge pass checks it. AC-S14-19 is the demo, which this delegate stops
before ([quickstart.md](quickstart.md) is its script). Every other criterion is covered: 3, 5 (R1); 4, 7, 8, 9 (R2);
6, 13 (R3); 16 (R4); 10, 11, 13 (R5); 11, 15 (R6); 1, 2, 14 (R7); 1, 10–14 (R8); 1, 3 (R9); 17 (R10).

## Technical Context

**Language/Version**: Python 3.11+ (the factory, `src/slipwai/`); Python ≥ 3.10 standard library only (toolkit
scripts a project runs, as `check-python` holds).
**Primary Dependencies**: none new. `json` and `re` from the standard library read the block (D134 Q2).
**Storage**: one new append-only markdown file per slice, `specs/<feature>/slices/<id>/hand-backs.md`, and one per
feature, `specs/<feature>/hand-backs.md` (ADR 0006); both in git. No other file kind.
**Testing**: `unittest` in `tests/`; scratch projects in temporary directories, scripts run as subprocesses with
`python3 -B`; the checker at `c3c760b` taken from git for R4, as `test_decisions_scope_gate.py` does; generated
projects for R7–R10. No mocking framework. Each new test module ≤ 350 lines.
**Target Platform**: wherever a generated project's agents run; Linux and macOS for the factory's tests.
**Performance Goals**: none stated; the gate reads two more globs.
**Constraints**: D60/D65 and SC-007 — nothing a project already has may newly fail (R4, R10); constitution VIII —
readers tolerate unknown keys and a later version (R1); *Additional Constraints* — no runtime paths persisted (R2's
path rule).
**Scale/Scope**: ten agent types, two layouts, two profiles.

## Constitution Check

The factory's constitution (`.specify/memory/constitution.md`):

- **I. A generated project owns its files and passes its own gate** — `check-decisions` refuses only what this release
  introduces (`hand-backs.md`); a project without one gets today's bytes (R4); `migrate` brings every changed file
  and the fragment's catch-up note says nothing is asked (R10). The starters' own `make verify` in the matrix is not
  rerun on this branch (the host's brief rules out the 41-minute gate); it runs at the merge root. Here the touched
  modules and `make test TESTS="test_toolkit test_utf8_io test_changelog"` run. MINOR fragment; `VERSION` unchanged.
- **III. Simplicity** — one module beside the checker, one page, one factory module for the text; no new file kind
  beyond ADR 0006's, no dependency.
- **V. Acceptance-driven** — the use case here is the gate and the verbs a session runs; every rule's examples enter
  through `check-decisions.py` or `benchmark.py` as a subprocess, or through `slipwai generate`/`migrate`.
- **VII. Auditability** — every hand-back is in git, every miss is a recorded line with its reason, and the session
  never writes a block for a delegate (D136).
- **VIII. A persisted schema is a contract** — schema 1 exactly as D134 and ADR 0006 fix it; unknown keys ignored;
  `contract` > 1 passed with a note (R1). No field is added, renamed or retyped here.
- **IX / Additional Constraints** — `files_changed` refuses absolute paths and `..` (R2), so no runtime path is
  persisted through it; the heading's time is UTC, written by the verb, never by the delegate.
- **XIV. Agent-generated change** — the shape is the owner's proxy's (D134), not this plan's; this plan adds no
  persisted field. Two spellings the criteria leave to the plan are recorded in [research.md](research.md) (R-4, R-5)
  and touch no field.

## Structure Decision

One deployable, `slipwai-graph` (`kind: tool`, D3); one vocabulary — the method's. The change lands under `assets/`
and `src/slipwai/project/` first (owner priority 3) and reaches this repository only through `slipwai migrate`.

**Toolkit (what a project runs)**

- `assets/toolkit/scripts/hand_backs.py` *(new, < 350 lines)*: `FIELDS`, `STATUSES`, the heading and `Missing:`
  patterns, `check_block`, `check_record`, `extract`, `append`, `coverage` ([data-model.md](data-model.md)).
- `assets/toolkit/scripts/check-decisions.py`: the gate globs both record paths and adds their findings and notes;
  the summary line's suffix only where a record exists (R4); the verbs `--hand-back`, `--hand-back-missing`,
  `--hand-backs`; the docstring names the shape's page. `hand_backs` is loaded by path with
  `sys.dont_write_bytecode` set.
- `assets/toolkit/scripts/agents/benchmark.py`: `notes()` gains the per-slice line (R6), reading `coverage` from
  `../hand_backs.py` the same way.
- `assets/toolkit/docs/result-contract.md` *(new)*: the page (R9).

**Factory source**

- `src/slipwai/project/result_contract.py` *(new, < 200 lines)*: `PAGE`, `STATUSES` (the factory's copy, held equal by
  test), `brief_paragraph(name)`, `slice_record_sentence()`, `hand_backs_section(layout)` for `commands/drive.md`,
  `converge_sentence(layout)`, `cruise_sentences(layout)`. Its own module because `commands.py` (345), `cruise.py`
  (333) and `agents.py` (300) are near the 350-line budget.
- `src/slipwai/project/agents.py`: the shared part of `agent_file` gains `{brief_paragraph(agent.name)}`; the
  converge brief one sentence after its levels paragraph (not D123's sentence); the `drive-slice` brief one sentence.
- `src/slipwai/project/cruise_agents.py`: the skipper's, hand's and bosun's return sentences name the block and that
  their words are its `status`.
- `src/slipwai/project/commands.py`: `{hand_backs_section(layout)}` after `{who_runs_each_stage(layout)}` (+2 lines);
  D123's two paragraphs untouched.
- `src/slipwai/project/converge_stage.py`: one sentence in the rung (R8).
- `src/slipwai/project/cruise.py`: the skipper-protocol sentence and the pointer (R8). *Proven needed:* the cruise
  text lives here, not in `commands.py`.
- `src/slipwai/project/docs_index.py`: the page's index line (R9). *Proven needed:* an unindexed page is listed under
  its own title at the end of `docs/README.md` (`docs_index()` docstring).
- `changelog.d/result-contract.md` *(new)*: MINOR, one standalone **Catch-up.** paragraph.

Not changed: `VERSION`, `catalog.json`, `stage_models.py`, `demo_stop.py`, `parallel_slices.py`, `migrate.py`,
`code_index.py` (S40's), this checkout's `delivery/` and every record under `specs/` but this slice's folder.

**Tests** *(new modules, each ≤ 350 lines)*

- `tests/hand_backs_fixture.py` — a scratch project (`project.json`, `specs/f/…`, the toolkit scripts copied), a valid
  block, `run(...)` as a subprocess with `-B`.
- `tests/test_hand_backs_shape.py` — R1, R2.
- `tests/test_hand_backs_record.py` — R3, R4.
- `tests/test_hand_backs_append.py` — R5.
- `tests/test_hand_backs_coverage.py` — R6.
- `tests/test_result_contract_briefs.py` — R7, R8, R9.
- `tests/test_result_contract_migrate.py` — R10.

## Pin

No code that existed before the method is changed: everything this slice edits is the factory's generator and the
toolkit it ships, whose tests are the pin — `tests/test_decisions_scope*.py`, `tests/test_decisions_gate_differential.py`,
`tests/test_cruise_record.py`, `tests/test_agent_types.py`, `tests/test_commands.py`, `tests/test_benchmark*.py`,
`tests/test_migrate.py`, `tests/test_toolkit.py`, run before the first increment and after the last. R4 pins the
checker's bytes on every tree without a record against `c3c760b` itself.

## Open questions

Neither blocks the plan; each is written for the host to number or overrule, and the plan proceeds on the
recommendation, which reverses with one sentence of generated text.

**Q1 — How is a converge finding for a missing block graded?** D136 says a miss found at the demo or adversary stop
is a task and does not re-open converge, and says nothing of one found *by* converge. The grade decides whether it
re-opens the loop. Options: (a) `MEDIUM` — it rides with the next pass or lands in Phase 4, and the host closes it
with one continuation before then; (b) `HIGH` — it re-opens the loop; (c) left to converge's judgement. **Recommend
(a)**: closing it costs one short exchange, not a pass, and D136's reason (a missing summary should not cost a stage)
applies the same way. The generated converge brief says `MEDIUM`.

**Q2 — Where does a `drive-slice` delegate's own hand-back go?** D134 item 1 puts the ready-set stage's hand-backs in
`specs/<feature>/hand-backs.md` and says a concurrent slice writes only its own folder; the main session appending
into `slices/<id>/hand-backs.md` on its checkout while the slice branch appends to the same file would conflict at
merge. **Recommend** the feature-level record, stage `ready-set` — which is how D134 already reads; the plan proceeds
on it and asks only for confirmation.

**Record changes the host owns** (not this branch's to write, AC-S14-18): ADR 0006 names no page, and AC-S14-1 needs
one — a line naming `docs/result-contract.md` in its *Decision*, while it is `Proposed`; D136 item 3's *this
repository's own measurement* line in the cruise report.
