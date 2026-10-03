# Benchmark — 001-faster-slipwai

Drawn 2026-10-03T08:30:53Z at `345dded` from 4 record(s) under `specs/001-faster-slipwai/` by `scripts/agents/benchmark.py overview`; `/benchmark` redraws it, and so does closing a slice. Regenerated whole, never edited: the records beside each slice are the source.

## Slices

3 slice(s) recorded, 4h44m+ in all.

| slice | delegate/cycle | wall | in | out | models | sessions | converge | +tasks | gaps | mutation | adversary | demo | verify✗ | rework | tasks | files | ±lines |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| (feature) | — | 49m23s | 4.2M | 54.5k | claude-fable-5-1 | 1 | 0 | 0 | 0/0 | — | 0 | — | 0 | 0 | — | — | — |
| S00-run-path | rule/rule | 1h44m+ | 20.1M (+1 unread) | 157k | claude-fable-5-1, claude-sonnet-5-5 | 1 | 2 | 1 | 7/5 | — | 0 | accepted | 1 | 0 | 9 | 44 | +3151/-203 |
| S20-slice-scope-root | rule/rule, task/example, task/rule | 1h09m+ | 22.8M (+3 unread) | 113.4k | claude-fable-5-1, claude-sonnet-5-5 | 1 | 2 | 8 | 8/6 | — | 9 | accepted | 1 | 0 | 34 | 44 | +3998/-36 |
| S21-refresh-keeps-owned-files | rule/rule, task/rule | 1h01m | 19.4M | 81.3k | claude-fable-5-1, claude-sonnet-5-5 | 1 | 1 | 3 | 8/8 | — | 6 | accepted | 0 | 0 | 11 | 42 | +3092/-24 |

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

### S20-slice-scope-root — 1h09m+

| stage | started (UTC) | wall | in | out | model | agent | delegated | reported |
|---|---|---|---|---|---|---|---|---|
| gaps | 2026-10-03 05:02 | unbracketed | unknown | unknown | claude-fable-5-1 | — | no | — |
| skipper | 2026-10-03 05:02 | 3m41s | 685.4k | 1.8k | claude-fable-5-1 | drive-skipper | yes | driver=cruise |
| gaps | 2026-10-03 05:05 | unbracketed | unknown | unknown | — | — | no | gaps=8, driver=cruise |
| plan | 2026-10-03 05:05 | 2m00s | 880.1k | 12.9k | claude-fable-5-1 | — | no | driver=cruise |
| tasks | 2026-10-03 05:07 | 1m19s | 483.6k | 2.3k | claude-fable-5-1, claude-sonnet-5-5 | drive-tasks | yes | driver=cruise |
| implement | 2026-10-03 05:09 | 21m27s | 3.3M | 19.3k | claude-fable-5-1, claude-sonnet-5-5 | drive-implement | yes | verify_failures=0, delegate=rule, cycle=rule, split=0, driver=cruise |
| converge | 2026-10-03 05:31 | 4m33s | 2M | 5k | claude-fable-5-1 | drive-converge | yes | driver=cruise |
| skipper | 2026-10-03 05:35 | 2m32s | 528.6k | 6.1k | claude-fable-5-1 | drive-skipper | yes | driver=cruise |
| implement | 2026-10-03 05:38 | 5m03s | 2.1M | 8.3k | claude-fable-5-1, claude-sonnet-5-5 | drive-implement | yes | verify_failures=0, delegate=rule, cycle=rule, split=0, driver=cruise |
| converge | 2026-10-03 05:43 | 3m37s | 1.8M | 7.3k | claude-fable-5-1 | drive-converge | yes | driver=cruise |
| implement | 2026-10-03 05:47 | 13s | 0 | 0 | — | — | no | verify_failures=1, delegate=task, cycle=example, split=0, driver=cruise |
| gaps | 2026-10-03 05:47 | 2m50s | 913.5k | 2k | claude-fable-5-1 | drive-gaps | yes | gaps=6, driver=cruise |
| skipper | 2026-10-03 05:50 | 2m39s | 565k | 5.7k | claude-fable-5-1 | drive-skipper | yes | driver=cruise |
| demo | 2026-10-03 05:53 | 5m25s | 3.4M | 9k | claude-fable-5-1 | drive-hand | yes | outcome=accepted, driver=cruise |
| implement | 2026-10-03 05:58 | 6m03s | 2.4M | 10.9k | claude-fable-5-1, claude-sonnet-5-5 | drive-implement | yes | verify_failures=0, delegate=task, cycle=rule, split=0, driver=cruise |
| adversary | 2026-10-03 06:05 | 4m42s | 2M | 8.3k | claude-fable-5-1 | drive-adversary | yes | findings=9, seams=2, driver=cruise |
| implement | 2026-10-03 06:09 | 3m23s | 1.8M | 14.6k | claude-fable-5-1, claude-sonnet-5-5 | drive-implement | yes | verify_failures=0, delegate=task, cycle=rule, split=0, driver=cruise |

### S21-refresh-keeps-owned-files — 1h01m

| stage | started (UTC) | wall | in | out | model | agent | delegated | reported |
|---|---|---|---|---|---|---|---|---|
| gaps | 2026-10-03 06:49 | 1m44s | 602.9k | 4.4k | claude-fable-5-1 | — | no | gaps=8, driver=cruise |
| plan | 2026-10-03 06:51 | 1m19s | 601.8k | 8.5k | claude-fable-5-1 | — | no | driver=cruise |
| tasks | 2026-10-03 06:53 | 1m44s | 414.2k | 3.1k | claude-fable-5-1, claude-sonnet-5-5 | drive-tasks | yes | driver=cruise |
| implement | 2026-10-03 06:54 | 11m52s | 3.7M | 12.4k | claude-fable-5-1, claude-sonnet-5-5 | drive-implement | yes | verify_failures=0, delegate=rule, cycle=rule, split=0, driver=cruise |
| converge | 2026-10-03 07:06 | 9m31s | 3.1M | 5.3k | claude-fable-5-1 | drive-converge | yes | driver=cruise |
| implement | 2026-10-03 07:16 | 5m21s | 1.2M | 10.2k | claude-fable-5-1, claude-sonnet-5-5 | drive-implement | yes | verify_failures=0, delegate=task, cycle=rule, split=0, driver=cruise |
| gaps | 2026-10-03 07:21 | 6m46s | 1.2M | 2.2k | claude-fable-5-1 | drive-gaps | yes | gaps=8, driver=cruise |
| implement | 2026-10-03 07:28 | 4m18s | 1M | 9.2k | claude-fable-5-1, claude-sonnet-5-5 | drive-implement | yes | verify_failures=0, delegate=task, cycle=rule, split=0, driver=cruise |
| demo | 2026-10-03 07:33 | 5m59s | 2.5M | 7k | claude-fable-5-1 | drive-hand | yes | outcome=accepted, driver=cruise |
| adversary | 2026-10-03 07:39 | 6m10s | 2.7M | 9.1k | claude-fable-5-1 | drive-adversary | yes | findings=6, seams=2, driver=cruise |
| skipper | 2026-10-03 07:45 | 2m51s | 1.1M | 5.5k | claude-fable-5-1 | drive-skipper | yes | driver=cruise |
| implement | 2026-10-03 07:49 | 3m39s | 1.2M | 4.4k | claude-fable-5-1, claude-sonnet-5-5 | drive-implement | yes | verify_failures=0, delegate=task, cycle=rule, split=0, driver=cruise |

## Notes

- S20-slice-scope-root: implemented as rule/rule and task/example and task/rule — its wall compares with neither
- S21-refresh-keeps-owned-files: implemented as rule/rule and task/rule — its wall compares with neither
- (feature) ground: cut off — a new `bosun` entry started while it was open; its wall is real, its signals were never reported
- S00-run-path mutation: not bracketed around its work — start and end were called in the same moment, so this stage's wall and tokens are missing, not zero.
- S20-slice-scope-root gaps: cut off — a new `skipper` entry started while it was open; its wall is real, its signals were never reported
- S20-slice-scope-root gaps: not bracketed around its work — start and end were called in the same moment, so this stage's wall and tokens are missing, not zero.
- S20-slice-scope-root gaps: not bracketed around its work — start and end were called in the same moment, so this stage's wall and tokens are missing, not zero.

## Reading these numbers

These numbers compare the slices of this project on this harness, and one slice before and after a change
to a prompt, a skill or the layout. They are tokens, not prices. They do not compare harnesses, whose transcripts
count different things, or projects, whose slices are not the same size — the shape columns normalise, they do not
equate. A stage's tokens are a floor: the turn that closes the entry is still being written when it is read. A
number the script could not read is written as unknown with its reason, never estimated. A stage whose start and end
were called in the same moment is unbracketed: its wall and tokens are missing, not zero, and a slice containing one
shows its measured wall as a floor with a trailing `+`. Host context grows through a session, so otherwise identical
slices spanning different numbers or lengths of sessions are not directly comparable on host tokens.
