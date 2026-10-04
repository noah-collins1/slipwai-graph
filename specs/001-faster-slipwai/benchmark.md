# Benchmark — 001-faster-slipwai

Drawn 2026-10-04T01:38:53Z at `abc216d` from 10 record(s) under `specs/001-faster-slipwai/` by `scripts/agents/benchmark.py overview`; `/benchmark` redraws it, and so does closing a slice. Regenerated whole, never edited: the records beside each slice are the source.

## Slices

9 slice(s) recorded, 16h10m+ in all.

| slice | delegate/cycle | wall | in | out | models | sessions | converge | +tasks | gaps | mutation | adversary | demo | verify✗ | rework | tasks | files | ±lines |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| (feature) | — | 49m23s | 4.2M | 54.5k | claude-fable-5-1 | 1 | 0 | 0 | 0/0 | — | 0 | — | 0 | 0 | — | — | — |
| S00-run-path | rule/rule | 1h44m+ | 20.1M (+1 unread) | 157k | claude-fable-5-1, claude-sonnet-5-5 | 1 | 2 | 1 | 7/5 | — | 0 | accepted | 1 | 0 | 9 | 44 | +3151/-203 |
| S01-gate-walks | story/rule, task/example, task/rule | 2h29m+ | 47.1M (+2 unread) | 165.7k | claude-fable-5-1, claude-sonnet-5-5 | 1 | 2 | 9 | 22/13 | — | 7 | accepted | 1 | 0 | 33 | 45 | +6623/-59 |
| S02-runner-bookkeeping | story/rule, task/example | 3h00m | 81M (+1 unread) | 205.3k | claude-fable-5-1, claude-sonnet-5-5 | 1 | 2 | 5 | 69/0 | — | 18 | accepted | 0 | 0 | 28 | 79 | +11047/-78 |
| S11-render-once | story/rule, task/rule | 2h49m | 41.4M (+1 unread) | 132.2k | claude-fable-5-1, claude-sonnet-5-5 | 1 | 2 | 6 | 17/7 | n/a (no command recorded) | 13 | accepted | 0 | 0 | 24 | 48 | +6103/-164 |
| S20-slice-scope-root | rule/rule, task/example, task/rule | 1h09m+ | 22.8M (+3 unread) | 113.4k | claude-fable-5-1, claude-sonnet-5-5 | 1 | 2 | 8 | 8/6 | — | 9 | accepted | 1 | 0 | 34 | 44 | +3998/-36 |
| S21-refresh-keeps-owned-files | rule/rule, task/rule | 1h01m | 19.4M | 81.3k | claude-fable-5-1, claude-sonnet-5-5 | 1 | 1 | 3 | 8/8 | — | 6 | accepted | 0 | 0 | 11 | 42 | +3092/-24 |
| S22-slice-scope-base | rule/rule, task/rule | 1h41m | 32M | 200.2k | claude-fable-5-1, claude-sonnet-5-5 | 1 | 2 | 7 | 21/11 | — | 11 | accepted | 0 | 0 | 29 | 29 | +5634/-42 |
| S23-refusal-in-subdirectory | rule/rule, task/rule | 1h16m | 22.5M | 117.8k | claude-fable-5-1, claude-sonnet-5-5 | 1 | 1 | 6 | 10/6 | — | 8 | accepted | 0 | 0 | 17 | 30 | +4009/-11 |
| S24-ci-fetches-slice-base | — | 7m24s | 1.9M | 16k | claude-fable-5-1 | 1 | 0 | 0 | 0/0 | — | 0 | — | 0 | 0 | — | — | — |

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

### S01-gate-walks — 2h29m+

| stage | started (UTC) | wall | in | out | model | agent | delegated | reported |
|---|---|---|---|---|---|---|---|---|
| gaps | 2026-10-03 13:15 | 1m47s | 722.9k | 7.4k | claude-fable-5-1 | — | no | driver=cruise |
| skipper | 2026-10-03 13:16 | 4m39s | 2M | 18.1k | claude-fable-5-1 | drive-skipper | yes | driver=cruise |
| gaps | 2026-10-03 13:21 | unbracketed | unknown | unknown | — | — | no | gaps=22, driver=cruise |
| plan | 2026-10-03 13:25 | unbracketed | unknown | unknown | — | — | no | driver=cruise |
| tasks | 2026-10-03 13:25 | 2m12s | 512.1k | 3.7k | claude-fable-5-1, claude-sonnet-5-5 | drive-tasks | yes | driver=cruise |
| implement | 2026-10-03 13:28 | 11m18s | 7.8M | 15.8k | claude-fable-5-1, claude-sonnet-5-5 | drive-implement | yes | delegate=story, cycle=rule, split=0, verify_failures=0, driver=cruise |
| converge | 2026-10-03 13:39 | 6m02s | 1.8M | 7.8k | claude-fable-5-1 | drive-converge | yes | driver=cruise |
| skipper | 2026-10-03 13:45 | 3m20s | 960.1k | 9k | claude-fable-5-1 | drive-skipper | yes | driver=cruise |
| implement | 2026-10-03 13:49 | 18m50s | 3.7M | 10.2k | claude-fable-5-1, claude-sonnet-5-5 | drive-implement | yes | delegate=task, cycle=rule, split=0, verify_failures=0, driver=cruise |
| converge | 2026-10-03 14:08 | 14m22s | 3.4M | 8.2k | claude-fable-5-1 | drive-converge | yes | driver=cruise |
| implement | 2026-10-03 14:22 | 11m27s | 3.1M | 11.4k | claude-fable-5-1, claude-sonnet-5-5 | drive-implement | yes | delegate=task, cycle=rule, split=0, verify_failures=0, driver=cruise |
| gaps | 2026-10-03 14:34 | 5m26s | 1.9M | 7.1k | claude-fable-5-1 | drive-gaps | yes | gaps=13, driver=cruise |
| implement | 2026-10-03 14:40 | 21m09s | 7.8M | 19.1k | claude-fable-5-1, claude-sonnet-5-5 | drive-implement | yes | delegate=task, cycle=rule, split=0, verify_failures=0, driver=cruise |
| demo | 2026-10-03 15:01 | 11m37s | 4M | 7.4k | claude-fable-5-1 | drive-hand | yes | outcome=accepted, driver=cruise |
| adversary | 2026-10-03 15:13 | 8m17s | 2.8M | 6.9k | claude-fable-5-1 | drive-adversary | yes | findings=7, seams=2, driver=cruise |
| skipper | 2026-10-03 15:22 | 3m57s | 1.7M | 14.1k | claude-fable-5-1 | drive-skipper | yes | driver=cruise |
| implement | 2026-10-03 15:26 | 22m30s | 4.6M | 18.7k | claude-fable-5-1, claude-sonnet-5-5 | drive-implement | yes | delegate=task, cycle=example, split=0, verify_failures=0, driver=cruise |
| implement | 2026-10-03 16:12 | 2m42s | 384.9k | 867 | claude-fable-5-1 | — | no | delegate=task, cycle=rule, split=0, verify_failures=1, driver=cruise |

### S02-runner-bookkeeping — 3h00m

| stage | started (UTC) | wall | in | out | model | agent | delegated | reported |
|---|---|---|---|---|---|---|---|---|
| gaps | 2026-10-03 17:23 | 1m21s | 785.5k | 7.4k | claude-fable-5-1 | — | no | driver=cruise |
| skipper | 2026-10-03 17:24 | 5m09s | 2.4M | 29.9k | claude-fable-5-1 | drive-skipper | yes | driver=cruise |
| gaps | 2026-10-03 17:30 | 5s | 0 | 0 | — | — | no | gaps=69, driver=cruise |
| plan | 2026-10-03 17:30 | 2m02s | 853.7k | 13.5k | claude-fable-5-1 | — | no | driver=cruise |
| tasks | 2026-10-03 17:33 | 2m51s | 974k | 2.9k | claude-fable-5-1, claude-sonnet-5-5 | drive-tasks | yes | driver=cruise |
| implement | 2026-10-03 17:36 | 57m20s | 34.5M | 42.5k | claude-fable-5-1, claude-sonnet-5-5 | drive-implement | yes | delegate=story, cycle=rule, split=0, verify_failures=0, driver=cruise |
| converge | 2026-10-03 18:35 | 12m50s | 2.7M | 6.7k | claude-fable-5-1 | drive-converge | yes | driver=cruise |
| implement | 2026-10-03 18:48 | 11m34s | 3.4M | 9.1k | claude-fable-5-1, claude-sonnet-5-5 | drive-implement | yes | delegate=task, cycle=example, split=0, verify_failures=0, driver=cruise |
| converge | 2026-10-03 19:00 | 16m47s | 2.2M | 5.3k | claude-fable-5-1 | drive-converge | yes | driver=cruise |
| demo | 2026-10-03 19:17 | 13m54s | 6.4M | 13.8k | claude-fable-5-1 | drive-hand | yes | outcome=accepted, driver=cruise |
| adversary | 2026-10-03 19:52 | 17m04s | 5.7M | 20.9k | claude-fable-5-1 | drive-adversary | yes | findings=18, seams=3, driver=cruise |
| skipper | 2026-10-03 20:09 | 5m07s | 910.7k | 7.8k | claude-fable-5-1 | drive-skipper | yes | driver=cruise |
| implement | 2026-10-03 20:15 | 34m40s | 20.1M | 45.4k | claude-fable-5-1, claude-sonnet-5-5 | drive-implement | yes | delegate=task, cycle=example, split=0, verify_failures=0, driver=cruise |

### S11-render-once — 2h49m

| stage | started (UTC) | wall | in | out | model | agent | delegated | reported |
|---|---|---|---|---|---|---|---|---|
| gaps | 2026-10-03 21:44 | 2m24s | 1.2M | 9.6k | claude-fable-5-1 | — | no | driver=cruise |
| skipper | 2026-10-03 21:47 | 2m48s | 915.8k | 7.8k | claude-fable-5-1 | drive-skipper | yes | driver=cruise |
| gaps | 2026-10-03 21:51 | 3s | 0 | 0 | — | — | no | gaps=17, driver=cruise |
| plan | 2026-10-03 21:51 | 3m21s | 1.6M | 17.1k | claude-fable-5-1 | — | no | driver=cruise |
| tasks | 2026-10-03 21:55 | 2m01s | 882.7k | 4k | claude-fable-5-1, claude-sonnet-5-5 | drive-tasks | yes | driver=cruise |
| implement | 2026-10-03 21:57 | 4m03s | 1.7M | 6.9k | claude-fable-5-1, claude-sonnet-5-5 | drive-implement | yes | verify_failures=0, delegate=task, cycle=rule, split=0, driver=cruise |
| implement | 2026-10-03 22:01 | 15m21s | 4.4M | 14.3k | claude-fable-5-1, claude-sonnet-5-5 | drive-implement | yes | verify_failures=0, delegate=story, cycle=rule, split=0, driver=cruise |
| implement | 2026-10-03 22:17 | 8m36s | 2.2M | 8.5k | claude-fable-5-1, claude-sonnet-5-5 | drive-implement | yes | verify_failures=0, delegate=story, cycle=rule, split=0, driver=cruise |
| converge | 2026-10-03 22:25 | 6m00s | 1.7M | 2.5k | claude-fable-5-1 | drive-converge | yes | driver=cruise |
| skipper | 2026-10-03 22:32 | 1m07s | 384.4k | 3.2k | claude-fable-5-1 | drive-skipper | yes | driver=cruise |
| implement | 2026-10-03 22:33 | 17m25s | 4.3M | 7.3k | claude-fable-5-1, claude-sonnet-5-5 | drive-implement | yes | verify_failures=0, delegate=task, cycle=rule, split=0, driver=cruise |
| converge | 2026-10-03 22:50 | 5m24s | 890.2k | 4.7k | claude-fable-5-1 | drive-converge | yes | driver=cruise |
| gaps | 2026-10-03 22:56 | 4m06s | 1.2M | 6.6k | claude-fable-5-1 | drive-gaps | yes | gaps=7, driver=cruise |
| implement | 2026-10-03 23:00 | 31m30s | 5.1M | 14k | claude-fable-5-1, claude-sonnet-5-5 | drive-implement | yes | verify_failures=0, delegate=task, cycle=rule, split=0, driver=cruise |
| demo | 2026-10-03 23:32 | 9m59s | 2.6M | 6.6k | claude-fable-5-1 | drive-hand | yes | outcome=accepted, driver=cruise |
| adversary | 2026-10-03 23:43 | 16m11s | 3.5M | 9.5k | claude-fable-5-1 | drive-adversary | yes | findings=13, seams=2, driver=cruise |
| implement | 2026-10-03 23:59 | 39m33s | 8.4M | 8.8k | claude-fable-5-1, claude-sonnet-5-5 | drive-implement | yes | verify_failures=0, delegate=task, cycle=rule, split=0, driver=cruise |
| mutation | 2026-10-04 00:40 | 2s | 325k | 906 | claude-fable-5-1 | — | no | mutation_score=n/a (no command recorded), driver=cruise |

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

### S22-slice-scope-base — 1h41m

| stage | started (UTC) | wall | in | out | model | agent | delegated | reported |
|---|---|---|---|---|---|---|---|---|
| gaps | 2026-10-03 08:31 | 1m55s | 712.9k | 10.1k | claude-fable-5-1 | — | no | gaps=0, driver=cruise |
| skipper | 2026-10-03 08:33 | 6m10s | 1M | 15.4k | claude-fable-5-1 | drive-skipper | yes | driver=cruise |
| gaps | 2026-10-03 08:39 | 1m24s | 153.2k | 7.7k | claude-fable-5-1 | — | no | gaps=21, driver=cruise |
| plan | 2026-10-03 08:41 | 1m54s | 698.8k | 13.8k | claude-fable-5-1 | — | no | driver=cruise |
| tasks | 2026-10-03 08:43 | 1m23s | 364.4k | 3.5k | claude-fable-5-1, claude-sonnet-5-5 | drive-tasks | yes | driver=cruise |
| implement | 2026-10-03 08:45 | 13m47s | 5.7M | 31.6k | claude-fable-5-1, claude-sonnet-5-5 | drive-implement | yes | verify_failures=0, delegate=rule, cycle=rule, split=0, driver=cruise |
| converge | 2026-10-03 08:59 | 7m53s | 1.3M | 10.2k | claude-fable-5-1 | drive-converge | yes | driver=cruise |
| skipper | 2026-10-03 09:07 | 2m40s | 562.9k | 5.1k | claude-fable-5-1 | drive-skipper | yes | driver=cruise |
| implement | 2026-10-03 09:10 | 7m55s | 4.1M | 21.5k | claude-fable-5-1, claude-sonnet-5-5 | drive-implement | yes | verify_failures=0, delegate=task, cycle=rule, split=0, driver=cruise |
| converge | 2026-10-03 09:18 | 5m47s | 951.2k | 1.8k | claude-fable-5-1 | drive-converge | yes | driver=cruise |
| gaps | 2026-10-03 09:24 | 6m31s | 1.4M | 2.6k | claude-fable-5-1 | drive-gaps | yes | gaps=11, driver=cruise |
| skipper | 2026-10-03 09:30 | 3m51s | 559.3k | 5.3k | claude-fable-5-1 | drive-skipper | yes | driver=cruise |
| implement | 2026-10-03 09:34 | 14m46s | 5M | 20.2k | claude-fable-5-1, claude-sonnet-5-5 | drive-implement | yes | verify_failures=0, delegate=task, cycle=rule, split=0, driver=cruise |
| demo | 2026-10-03 09:49 | 5m33s | 1.4M | 6.4k | claude-fable-5-1 | drive-hand | yes | outcome=accepted, driver=cruise |
| adversary | 2026-10-03 09:55 | 6m57s | 2.9M | 25.9k | claude-fable-5-1 | drive-adversary | yes | findings=11, seams=2, driver=cruise |
| implement | 2026-10-03 10:02 | 13m28s | 5M | 19k | claude-fable-5-1, claude-sonnet-5-5 | drive-implement | yes | verify_failures=0, delegate=task, cycle=rule, split=0, driver=cruise |

### S23-refusal-in-subdirectory — 1h16m

| stage | started (UTC) | wall | in | out | model | agent | delegated | reported |
|---|---|---|---|---|---|---|---|---|
| gaps | 2026-10-03 10:55 | 2m12s | 1.2M | 13.2k | claude-fable-5-1 | — | no | gaps=10, driver=cruise |
| plan | 2026-10-03 10:57 | 1m32s | 143.3k | 9.9k | claude-fable-5-1 | — | no | driver=cruise |
| tasks | 2026-10-03 10:59 | 1m38s | 423.7k | 2.6k | claude-fable-5-1, claude-sonnet-5-5 | drive-tasks | yes | driver=cruise |
| implement | 2026-10-03 11:02 | 16m57s | 4.6M | 24.9k | claude-fable-5-1, claude-sonnet-5-5 | drive-implement | yes | verify_failures=0, delegate=rule, cycle=rule, split=0, driver=cruise |
| converge | 2026-10-03 11:20 | 7m20s | 1.5M | 5.2k | claude-fable-5-1 | drive-converge | yes | driver=cruise |
| skipper | 2026-10-03 11:28 | 2m46s | 933.2k | 7.3k | claude-fable-5-1 | drive-skipper | yes | driver=cruise |
| implement | 2026-10-03 11:31 | 18m55s | 3.7M | 21.8k | claude-fable-5-1, claude-sonnet-5-5 | drive-implement | yes | verify_failures=0, delegate=task, cycle=rule, split=0, driver=cruise |
| gaps | 2026-10-03 11:50 | 4m17s | 1.7M | 5.8k | claude-fable-5-1 | drive-gaps | yes | gaps=6, driver=cruise |
| implement | 2026-10-03 11:54 | 4m29s | 795.1k | 3.6k | claude-fable-5-1, claude-sonnet-5-5 | drive-implement | yes | verify_failures=0, delegate=task, cycle=rule, split=0, driver=cruise |
| demo | 2026-10-03 12:01 | 7m21s | 3.1M | 6k | claude-fable-5-1 | drive-hand | yes | outcome=accepted, driver=cruise |
| adversary | 2026-10-03 12:08 | 7m44s | 2.8M | 13.2k | claude-fable-5-1 | drive-adversary | yes | findings=8, seams=2, driver=cruise |
| implement | 2026-10-03 12:16 | 1m21s | 1.7M | 4.4k | claude-fable-5-1, claude-sonnet-5-5 | drive-implement | yes | verify_failures=0, delegate=task, cycle=rule, split=0, driver=cruise |

### S24-ci-fetches-slice-base — 7m24s

| stage | started (UTC) | wall | in | out | model | agent | delegated | reported |
|---|---|---|---|---|---|---|---|---|
| gaps | 2026-10-03 17:13 | 1m37s | 630.6k | 8.4k | claude-fable-5-1 | — | no | driver=cruise |
| skipper | 2026-10-03 17:15 | 4m15s | 895.9k | 3.2k | claude-fable-5-1 | drive-skipper | yes | driver=cruise |
| bosun | 2026-10-03 17:19 | 1m32s | 384k | 4.5k | claude-fable-5-1 | drive-bosun | yes | driver=cruise |

## Notes

- S01-gate-walks: implemented as story/rule and task/example and task/rule — its wall compares with neither
- S02-runner-bookkeeping: implemented as story/rule and task/example — its wall compares with neither
- S11-render-once: implemented as story/rule and task/rule — its wall compares with neither
- S20-slice-scope-root: implemented as rule/rule and task/example and task/rule — its wall compares with neither
- S21-refresh-keeps-owned-files: implemented as rule/rule and task/rule — its wall compares with neither
- S22-slice-scope-base: implemented as rule/rule and task/rule — its wall compares with neither
- S23-refusal-in-subdirectory: implemented as rule/rule and task/rule — its wall compares with neither
- (feature) ground: cut off — a new `bosun` entry started while it was open; its wall is real, its signals were never reported
- S00-run-path mutation: not bracketed around its work — start and end were called in the same moment, so this stage's wall and tokens are missing, not zero.
- S01-gate-walks gaps: not bracketed around its work — start and end were called in the same moment, so this stage's wall and tokens are missing, not zero.
- S01-gate-walks plan: not bracketed around its work — start and end were called in the same moment, so this stage's wall and tokens are missing, not zero.
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
