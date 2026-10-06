# Research: S39-benchmark-elapsed

Every statement about existing code cites the file it was read from at `525399b`; every statement about a real
record cites the record or the commit. The slice adds no dependency.

## R-1 Derive at read time; never rewrite a record

- **Decision**: every new figure is computed when `make benchmark`, `overview` or `--json` runs, from the records,
  git, `specs/cruise-log.jsonl`, `decisions.md` and the transcripts. `start`, `end` and `cut-off` write what they
  write today.
- **Rationale**: D65 — a record written by an earlier factory must read the same after `migrate`, and a record
  cannot be re-bracketed afterwards (`benchmark.py` `check()`, lines 1020–1021). *Ready* and *accepted* are not
  moments any record holds (D159, G1), and S08 shows why a write-time stamp would be wrong: it merged at `3138416`
  before its own Phase 4 ran (S08 record: `adversary` 2026-10-06T03:16:18Z, after the merge at 03:14:44Z).
- **Alternatives**: stamping `ready`/`accepted` into the record at `close` (a second source that can disagree with
  git; old records would lack it).

## R-2 Ready and accepted from git, by first appearance

- **Decision**: `git log --reverse --format='%H %ct' -S<needle> -- <path>` lists the candidate commits oldest first;
  each candidate's file is read with `git show <sha>:<path>` and the first one whose content holds the predicate is
  the moment. Needles: `` `<id>` `` in `story-split.md`; ``| `<id>` |`` in `slices/README.md`; `id: <id>` in
  `docs/event-model/model.yaml` (the event profile's done mark, `parallel_slices.py` `done_marker`, line 19).
  Dependencies are the backticked ids in the `depends_on` cell of the slice's `## Slice graph` row, else the block's
  `depends_on` in `model.yaml`.
- **Rationale**: `-S` alone counts substring occurrences, so `S1` would match `S10`; the content check reads the row
  or block whole, the way `done_slices()` does (`benchmark.py` lines 624–641). Commit time (`%ct`) is when the moment
  entered the branch the reader is on. Hand check on this repository: S08's split commit `d3a0926`
  (2026-10-03T02:34:09Z), S04's register row `b31c864` (2026-10-04T18:13:05Z), S08's own row `c88fe2f`
  (2026-10-06T07:16:58Z) — elapsed 133 433 s.
- **Merged**: `git log --merges --fixed-strings --grep=slice/<id> --format='%H %ct'`, oldest. S06 worked on
  `adopt-method` directly and has none; its merge reads unknown and its sibling *landing* is its register row.

## R-3 Waiting causes are disjoint by a fixed order

- **Decision**: integration, then dependency, then review, then worker; each takes only seconds not already taken by
  the worked union or an earlier cause; the remainder is unattributed. Integer seconds throughout, so the identity
  holds exactly.
- **Rationale**: AC-S39-2 requires the parts to sum to elapsed, which overlapping causes would break (a park can fall
  inside a merge-to-row interval). The order is most-specific record first: a merge commit and a gate bracket name
  one slice; a sibling's landing names two; a park names the whole run; the cruise log's span names nothing in
  particular.
- **The gate bracket** is integration's, not worked time: AC-S39-2 puts *the full gate inside* integration. A `demo`
  bracket with no `driver` signal is a person at the demo, AC-S39-2's *demo waiting on a person*, so it is review's.
  Every other bracket is worked.
- **S08 by hand** (the demo re-derives these): merge 03:14:44Z → row 07:16:58Z is 14 534 s, less the adversary
  (1 002 s) and the fix (2 537 s) brackets inside it; S06's row `1d6cc17` (03:13:46Z) is the sibling landing that S08's
  accepted demo (00:31:54Z) waited on; parks in the interval: iterations 13, 14, 17, 18 and 20 (`stopped: human`).

## R-4 Attribution follows the spawn chain, then the bracket's opener

- **Decision**: a request in a sub-agent transcript whose chain reaches a `drive-slice` belongs to that slice; any
  other request may be claimed only by a bracket a `drive-slice` did not open.
- **Rationale**: Claude Code writes `<session>/subagents/agent-<id>.meta.json` beside each sub-agent transcript with
  `agentType`, `description`, `parentAgentId` and `spawnDepth` (read on this machine 2026-10-06, sessions
  `d883234c…` and `c1c52109…`). Iteration 23's two `drive-slice` delegates are described `drive-slice
  S08-scoped-mutation` and `drive-slice S14-result-contract`; their implementers carry `parentAgentId` of their
  `drive-slice`. Iteration 24's are described `S38 slice ladder to converge` and `S39 slice ladder to converge` — the
  convention not yet written down, hence the fallback to the first word and AC-S39-5's text in the ladder.
- **The opener**: a bracket's cursor is each transcript's size at `start`; the transcript that ran `start` holds
  `benchmark: <stage> started (<record path>` in the bytes right after its own cursor (`start()`, line 482). Checked
  on S08's record: `gaps` and both `demo` brackets were opened by the host's transcript, `plan` to the third
  `implement` by `agent-a0180709359d1f0d0` (S08's `drive-slice`). Without this, a host-spawned S06 implementer at
  17:40Z would be claimable by S08's 17:17–18:53Z bracket — the defect AC-S39-11 names.
- **Shared**: a request no chain ties and either no host-opened bracket covers, or host-opened brackets of two records
  cover with no stage owning its type in exactly one. `Window.counts` (lines 245–252) still picks the entry inside
  one record, so a skipper nested in an implement keeps its own lines.
- **Alternatives**: the delegate-type rule alone (today's; three concurrent `implement` brackets all own
  `drive-implement`); reading the slice from the manifest text (D159 option (b), not chosen).

## R-5 Cost without transcripts

- **Decision**: where a session's transcripts are not on the reading machine, an entry's tokens are its recorded
  `usage` — counted when no bracket of another record overlaps it in time, and otherwise `unknown` with the reason.
- **Rationale**: the recorded usage was split by today's rule, which double-counts only where brackets of different
  records overlap (`other_windows`, lines 268–278, reads only this checkout's records). A clone in CI has no
  transcripts; the figure it can stand behind is the non-overlapping one.

## R-6 Cut-off stage time ends at the last attributed line

- **Decision**: for an entry with `cut_off`, stage time ends at the `timestamp` of the last request R-4 attributed to
  it, where one exists; the note names that moment and the recorded end.
- **Rationale**: `cut_off_entry()` (lines 567–591) stamps `ended` with the moment the cut-off ran, which can be the
  next iteration's start hours later (AC-S39-3). Counting only the entry's own lines keeps a sibling's later activity
  from extending it.

## R-7 Renames, not reuse

- **Decision**: `wall` → `stage time` in both tables and headings; the old `rework` column → `re-entered`, the
  `--json` list → `reentered`; `rework` now means AC-S39-4's.
- **Rationale**: AC-S39-3 names the first; reusing `rework` for a second meaning would let a reader compare two
  different things under one name, and AC-S39-9 fixes the key. The fragment names both.

## R-8 Decision health reads only what FR-029 and FR-031 name

- **Decision**: Q1 (a) in [plan.md](plan.md): tier and escalation from the `Reversibility:` line, review from
  `Status:` `ratified`/`reverted`, wait from the skipper bracket holding `When:`.
- **Rationale**: this repository's 159 entries carry no `Reversibility:` line (`grep -c` 0), so every figure reads
  unknown today and nothing is computed from a field that does not exist (D159).
