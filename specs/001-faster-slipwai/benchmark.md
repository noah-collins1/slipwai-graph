# Benchmark — 001-faster-slipwai

Drawn 2026-10-03T04:57:36Z at `2108b81` from 2 record(s) under `specs/001-faster-slipwai/` by `scripts/agents/benchmark.py overview`; `/benchmark` redraws it, and so does closing a slice. Regenerated whole, never edited: the records beside each slice are the source.

## Slices

1 slice(s) recorded, 2h33m+ in all.

| slice | delegate/cycle | wall | in | out | models | sessions | converge | +tasks | gaps | mutation | adversary | demo | verify✗ | rework | tasks | files | ±lines |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| (feature) | — | 49m23s | 4.2M | 54.5k | claude-fable-5-1 | 1 | 0 | 0 | 0/0 | — | 0 | — | 0 | 0 | — | — | — |
| S00-run-path | rule/rule | 1h44m+ | 20.1M (+1 unread) | 157k | claude-fable-5-1, claude-sonnet-5-5 | 1 | 2 | 1 | 7/5 | — | 0 | accepted | 1 | 0 | 9 | 44 | +3151/-203 |

delegate/cycle = how implementation was delegated and driven; in = input + cache read + cache creation tokens; gaps = before/after converge; +tasks = tasks converge appended; sessions = harness sessions read; a stage's tokens are a floor (the turn that ends it is partly uncounted); a trailing + makes wall a floor because an unbracketed stage is missing; tokens are not prices.

## Stages

### The feature, above the slice loop — 49m23s

| stage | started (UTC) | wall | in | out | model | agent | delegated | reported |
|---|---|---|---|---|---|---|---|---|
| ground | 2026-10-03 01:44 | 40s | 90.5k | 3.5k | claude-fable-5-1 | — | no | — |
| bosun | 2026-10-03 01:45 | 6m27s | 1.6M | 36.2k | claude-fable-5-1 | drive-bosun | yes | — |
| split | 2026-10-03 01:51 | 42m16s | 2.4M | 14.7k | claude-fable-5-1 | — | no | — |

### S00-run-path — 1h44m+

| stage | started (UTC) | wall | in | out | model | agent | delegated | reported |
|---|---|---|---|---|---|---|---|---|
| gaps | 2026-10-03 02:36 | 8m03s | 527k | 24.4k | claude-fable-5-1 | — | no | gaps=7, driver=cruise |
| skipper | 2026-10-03 02:44 | 9m30s | 2.1M | 21.1k | claude-fable-5-1 | drive-skipper | yes | driver=cruise |
| plan | 2026-10-03 02:54 | 6m01s | 1.4M | 25.8k | claude-fable-5-1 | — | no | driver=cruise |
| tasks | 2026-10-03 03:00 | 3m44s | 731k | 5.7k | claude-fable-5-1, claude-sonnet-5-5 | drive-tasks | yes | driver=cruise |
| implement | 2026-10-03 03:04 | 40m07s | 4M | 21.8k | claude-fable-5-1, claude-sonnet-5-5 | drive-implement | yes | verify_failures=1, delegate=rule, cycle=rule, split=0, driver=cruise |
| converge | 2026-10-03 03:44 | 6m20s | 1.9M | 9.6k | claude-fable-5-1 | drive-converge | yes | driver=cruise |
| gaps | 2026-10-03 03:50 | 6m31s | 1M | 5.1k | claude-fable-5-1 | drive-gaps | yes | gaps=5, driver=cruise |
| map | 2026-10-03 03:57 | 4m18s | 2M | 14.1k | claude-fable-5-1 | — | no | driver=cruise |
| demo | 2026-10-03 04:01 | 7m17s | 1.7M | 7.4k | claude-fable-5-1 | drive-hand | yes | outcome=implementation, driver=cruise |
| implement | 2026-10-03 04:08 | 1m25s | 1.3M | 7.7k | claude-fable-5-1, claude-sonnet-5-5 | drive-implement | yes | verify_failures=0, delegate=rule, cycle=rule, split=0, driver=cruise |
| converge | 2026-10-03 04:10 | 5m06s | 1.8M | 6.6k | claude-fable-5-1 | drive-converge | yes | driver=cruise |
| demo | 2026-10-03 04:50 | 5m12s | 1.3M | 6.6k | claude-fable-5-1 | drive-hand | yes | outcome=accepted, driver=cruise |
| adversary | 2026-10-03 04:56 | 37s | 405.3k | 1.2k | claude-fable-5-1 | — | no | findings=0, seams=0, driver=cruise |
| mutation | 2026-10-03 04:56 | unbracketed | unknown | unknown | — | — | no | driver=cruise |

## Notes

- (feature) ground: cut off — a new `bosun` entry started while it was open; its wall is real, its signals were never reported
- S00-run-path mutation: not bracketed around its work — start and end were called in the same moment, so this stage's wall and tokens are missing, not zero.

## Reading these numbers

These numbers compare the slices of this project on this harness, and one slice before and after a change
to a prompt, a skill or the layout. They are tokens, not prices. They do not compare harnesses, whose transcripts
count different things, or projects, whose slices are not the same size — the shape columns normalise, they do not
equate. A stage's tokens are a floor: the turn that closes the entry is still being written when it is read. A
number the script could not read is written as unknown with its reason, never estimated. A stage whose start and end
were called in the same moment is unbracketed: its wall and tokens are missing, not zero, and a slice containing one
shows its measured wall as a floor with a trailing `+`. Host context grows through a session, so otherwise identical
slices spanning different numbers or lengths of sessions are not directly comparable on host tokens.
