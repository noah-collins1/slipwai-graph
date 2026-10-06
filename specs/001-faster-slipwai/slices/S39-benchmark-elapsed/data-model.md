# Data model: S39-benchmark-elapsed

Nothing here is persisted: `benchmark.json` keeps its shape (the `gate` stage's entries are ordinary entries), and
every figure below is derived each time a reader runs. This page spells what the plan's rules compute and print.

## Moments (per slice record)

| Moment | Read from | Absent |
|---|---|---|
| `added` | oldest commit whose `specs/<f>/story-split.md` names `` `<id>` ``; else whose `docs/event-model/model.yaml` has a `- id: <id>` block | `{"unknown": "<id> is in neither specs/<f>/story-split.md nor docs/event-model/model.yaml"}` |
| `dependencies` | backticked ids in the `depends_on` cell of the `## Slice graph` row whose first cell is `` `<id>` ``; else the block's `depends_on` list; `—` or empty is none | none |
| `done[<dep>]` | oldest commit whose `specs/<f>/slices/README.md` has a row whose first cell is `` `<dep>` ``, or whose `model.yaml` has `<dep>`'s block at `status: implemented` — the earlier of the two | the slice is not ready |
| `ready` | max(`added`, every `done[<dep>]`) | `{"unknown": "not ready: <dep> is not done"}` |
| `accepted` | the slice's own `done` | elapsed reads `open since <ready>` |
| `demo_accepted` | `ended` of the first `demo` entry with `signals.outcome == "accepted"` | not shown |
| `merged` | oldest merge commit whose subject contains `slice/<id>` | integration counts only `gate` brackets |

Times are UTC seconds; a commit's moment is its committer time (`%ct`). Each moment carries the commit (short sha)
or the record it came from in `read_from`. Outside a git repository, or where `git` fails, every git-read moment is
`{"unknown": "git could not be read: <why>"}`.

## Intervals and causes (per slice record, accepted slices only)

All intervals are clipped to `[ready, accepted]`, and integer seconds.

| Name | Intervals | Read from |
|---|---|---|
| `worked` | union of the record's brackets `[started, end]`, except stage `gate` and a `demo` whose signals carry no `driver`; `end` is the last attributed line for a `cut_off` entry where one was read, else `ended` | the brackets |
| `integration` | `[merged, accepted]` ∪ every `gate` bracket | the merge commit, the `gate` brackets |
| `dependency` | `[demo_accepted, L]`, where `L` is the latest *landing* of a slice earlier in the `## Slice graph`'s row order that falls after `demo_accepted` and before `merged` (or before `accepted` where there is no merge); a landing is the sibling's `merged`, else its own `done` | git, the graph's order |
| `review` | each cruise-log row whose `last_line` ends `stopped: human`: `[ended, next row's started]` (to now if none); each `demo` bracket with no `driver` signal | `specs/cruise-log.jsonl`, the brackets |
| `worker` | `[first row's started, last row's ended]` of the cruise log, less the parks | `specs/cruise-log.jsonl` |
| `unattributed` | what is left | — |

Each cause takes only seconds no earlier row of this table (from `worked` down) has taken. Hence
`worked + integration + dependency + review + worker + unattributed == elapsed`, exactly. A cause with no record to
read (no cruise log, no merge commit and no gate bracket, no accepted demo) is `0` with `read_from` saying none was
present — its seconds are already in `unattributed`; the plan's R10 checks that nothing is lost. For a slice not yet
accepted, `waiting` and `worked_seconds` are `{"unknown": "open since <ready>"}`.

## Stage time, rework

- `stage_seconds` = Σ over ended entries of (`end` − `started`), with `end` as in `worked`'s row; an unbracketed entry
  counts 0 as today, and the existing `+` floor marker stays.
- `rework` = entries after a `demo` whose outcome is `behaviour` or `implementation`, up to the next `demo` (not
  included), or to the end of the record: `seconds` = their stage time, `tokens` = their attributed tokens.

## Attribution (per project)

Inputs: every record's ended entries with a `span`, and open ones with a `cursor`; for each Claude Code session
named in a record, `<projects>/<slug>/<session>.jsonl` and `<session>/subagents/agent-<a>.jsonl` with
`agent-<a>.meta.json`.

1. **Requests.** An assistant line with `message.usage` and a key (`requestId`, else `message.id`, else `uuid`); the
   first line of a key is the request (offset, file, `timestamp`, `attributionAgent`, the four usage counts). Tokens =
   `input_tokens + output_tokens + cache_read_input_tokens + cache_creation_input_tokens`.
2. **Chain.** For a sub-agent file, follow `parentAgentId` through the session's `meta.json` files; the first
   `agentType == "drive-slice"` names the slice: its description after `drive-slice `, else its first word, matched
   to a record's `slice` exactly or as the only record whose slice starts with `<word>-`. The main transcript and a
   file with no `drive-slice` above it have no chain.
3. **Opener.** For each window, the transcript among the session's files whose bytes at its `from` offset (the next
   1 MiB) contain `benchmark: <stage> started (<record path relative to the root>`; its chain is the window's
   *class*. No opener found: class none.
4. **Assignment.** A request with chain `s`: the covering windows of class `s`, else of `s`'s record; inside one
   record `Window.counts` picks the entry; no covering window → `s`'s record, no entry. `s` names no record →
   shared. A request with no chain: covering windows of class none; one record → that record, its entry by
   `Window.counts`; several records → the one record with a window whose stage owns the request's agent type
   (`OWNERS`), else shared; none → shared.
5. **Outputs.** Per entry: `tokens`, `delegates` (descriptions of the sub-agent files whose requests it got),
   `last_line`. Per record: `cost.tokens` (everything assigned to it), `cost.shared` (for a slice record: shared
   requests inside its own brackets; for the feature record: the feature's bucket). Per session: `total`,
   `attributed`, `shared` — `attributed + shared == total`.

A session whose transcripts are absent: each entry's recorded `usage` totals stand in, counted where no bracket of
another record overlaps the entry's interval, else `{"unknown": "brackets of <record> overlap this one and the
transcripts are not on this machine"}`. A Codex session is read the same way, without step 2.

## Feature figures

| Name | Value |
|---|---|
| `elapsed` | min(slice `ready`) → max(slice `accepted`); `open since <first ready>` while any slice record is not accepted |
| `stage_seconds` | Σ `stage_seconds` over every record of the feature, the feature's own included |
| `in_flight_seconds` | the length of the union of every slice record's `worked` brackets (unclipped) |

## Decision health (per feature, Q1 (a))

`specs/<f>/decisions.md`, entries split on `## D<n> — `.

| Figure | Numerator / denominator | Flag |
|---|---|---|
| `escalation_share` | entries whose `- **Reversibility:**` value is `easy → hard` or `guarded → hard` (`->` too) / entries whose first tier is `easy` or `guarded` | outside 5–15 % |
| `misclassification_rate` | tiered entries whose `Status:` contains `reverted` / tiered entries whose `Status:` contains `ratified` or `reverted` | over 5 % |
| `median_wait[<tier>]` | median of the `seconds` of the `skipper` bracket (any record of the feature) holding the entry's `When:` | none |

No `Reversibility:` line in the log: all three `{"unknown": "no decision entry carries a Reversibility: line"}`. A
denominator of 0: unknown, naming it.

## `--json`, per record (added keys)

```json
{"elapsed": 133433, "stage_seconds": 36211, "worked_seconds": 30120,
 "waiting": {"dependency": 9832, "worker": 41800, "review": 20322, "integration": 10995, "unattributed": 20364},
 "rework": {"seconds": 5429, "tokens": 18200345}, "cost": {"tokens": 81233412, "shared": 2210345},
 "moments": {"ready": "2026-10-04T18:13:05Z", "accepted": "2026-10-06T07:16:58Z", "...": "..."},
 "read_from": {"ready": "b31c864 (slices/README.md: S04-parallel-gate)", "accepted": "c88fe2f (slices/README.md)", "...": "..."},
 "entries": [{"stage": "implement", "started": "…", "stage_seconds": 5755, "tokens": 0, "delegates": ["S08 US2 implement T002-T009"]}],
 "reentered": []}
```

(Numbers illustrative.) Any figure may instead be `{"unknown": "<reason>"}`. The feature record also carries
`feature: {elapsed, stage_seconds, in_flight_seconds}`, `decision_health` and `sessions` (per session `total`,
`attributed`, `shared`).
