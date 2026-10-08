# Benchmark — 001-faster-slipwai

Drawn 2026-10-08T05:16:04Z at `faa03e0` from 23 record(s) under `specs/001-faster-slipwai/` by `scripts/agents/benchmark.py overview`; `/benchmark` redraws it, and so does closing a slice. Regenerated whole, never edited: the records beside each slice are the source.

## Slices

22 slice(s) recorded, 100h46m+ in all.

| slice | delegate/cycle | wall | in | out | models | sessions | converge | +tasks | gaps | mutation | adversary | demo | verify✗ | rework | tasks | files | ±lines |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| (feature) | — | 1h47m | 46.9M | 167.2k | claude-fable-5-1, claude-opus-5-5, claude-sonnet-5-5 | 3 | 0 | 0 | 0/0 | — | 26 | — | 0 | 0 | — | — | — |
| S00-run-path | rule/rule | 1h44m+ | 20.1M (+1 unread) | 157k | claude-fable-5-1, claude-sonnet-5-5 | 1 | 2 | 1 | 7/5 | — | 0 | accepted | 1 | 0 | 9 | 44 | +3151/-203 |
| S01-gate-walks | story/rule, task/example, task/rule | 2h29m+ | 47.1M (+2 unread) | 165.7k | claude-fable-5-1, claude-sonnet-5-5 | 1 | 2 | 9 | 22/13 | — | 7 | accepted | 1 | 0 | 33 | 45 | +6623/-59 |
| S02-runner-bookkeeping | story/rule, task/example | 3h00m | 81M (+1 unread) | 205.3k | claude-fable-5-1, claude-sonnet-5-5 | 1 | 2 | 5 | 69/0 | — | 18 | accepted | 0 | 0 | 28 | 79 | +11047/-78 |
| S03-verify-stamp | story/rule, task/rule | 5h05m | 112.5M | 267.2k | claude-fable-5-1, claude-sonnet-5-5 | 1 | 3 | 15 | 31/8 | — | 18 | accepted | 27 | 0 | 42 | 78 | +12971/-48 |
| S04-parallel-gate | task/rule | 5h06m | 106.5M | 251.2k | claude-fable-5-1, claude-sonnet-5-5 | 1 | 3 | 8 | 63/19 | — | 9 | accepted | 0 | 0 | 24 | 68 | +11069/-78 |
| S05-xdist | story/rule, task/rule | 1h43m | 45.2M | 112.9k | claude-opus-5-5, claude-sonnet-5-5 | 2 | 2 | 6 | 13/3 | — | 8 | accepted | 0 | 0 | 25 | 82 | +5806/-64 |
| S06-scoped-gate | rule/rule, task/rule | 12h37m+ | 410.1M (+1 unread) | 523.9k | claude-opus-5-5, claude-sonnet-5-5 | 4 | 5 | 19 | 19/0 | — | 20 | accepted | 0 | 0 | 55 | 179 | +51773/-134 |
| S07-scoped-checks | drive-implement/?, drive-implement/rule, drive-tasks/? | 7h57m | 258.7M | 299k | claude-opus-5-5, claude-sonnet-5-5 | 1 | 1 | 0 | 14/7 | — | 17 | accepted | 1 | 0 | 10 | 117 | +14709/-197 |
| S08-scoped-mutation | story/rule | 8h43m | 338.7M | 399.2k | claude-opus-5-5, claude-sonnet-5-5 | 2 | 2 | 8 | 19/7 | — | 16 | accepted | 0 | 0 | 44 | 249 | +27959/-455 |
| S11-render-once | story/rule, task/rule | 2h49m | 41.4M (+1 unread) | 132.2k | claude-fable-5-1, claude-sonnet-5-5 | 1 | 2 | 6 | 17/7 | n/a (no command recorded) | 13 | accepted | 0 | 0 | 24 | 48 | +6103/-164 |
| S14-result-contract | story/rule | 2h11m | 216.9M | 266.8k | claude-opus-5-5, claude-sonnet-5-5 | 2 | 2 | 12 | 0/7 | — | 14 | accepted | 0 | 0 | 41 | 309 | +34705/-485 |
| S20-slice-scope-root | rule/rule, task/example, task/rule | 1h09m+ | 22.8M (+3 unread) | 113.4k | claude-fable-5-1, claude-sonnet-5-5 | 1 | 2 | 8 | 8/6 | — | 9 | accepted | 1 | 0 | 34 | 44 | +3998/-36 |
| S21-refresh-keeps-owned-files | rule/rule, task/rule | 1h01m | 19.4M | 81.3k | claude-fable-5-1, claude-sonnet-5-5 | 1 | 1 | 3 | 8/8 | — | 6 | accepted | 0 | 0 | 11 | 42 | +3092/-24 |
| S22-slice-scope-base | rule/rule, task/rule | 1h41m | 32M | 200.2k | claude-fable-5-1, claude-sonnet-5-5 | 1 | 2 | 7 | 21/11 | — | 11 | accepted | 0 | 0 | 29 | 29 | +5634/-42 |
| S23-refusal-in-subdirectory | rule/rule, task/rule | 1h16m | 22.5M | 117.8k | claude-fable-5-1, claude-sonnet-5-5 | 1 | 1 | 6 | 10/6 | — | 8 | accepted | 0 | 0 | 17 | 30 | +4009/-11 |
| S24-ci-fetches-slice-base | rule/rule, task/rule | 1h17m | 43.5M | 174.7k | claude-fable-5-1, claude-sonnet-5-5 | 2 | 2 | 4 | 13/7 | — | 8 | accepted | 0 | 0 | 24 | 226 | +34959/-339 |
| S26-reversibility-line | drive-converge/?, drive-implement/rule, drive-tasks/? | 5h04m | 219.3M | 268.6k | claude-opus-5-5, claude-sonnet-5-5 | 1 | 1 | 0 | 16/8 | — | 21 | accepted | 1 | 0 | 26 | 55 | +6773/-22 |
| S27-provisional-decisions | story/rule | 4h20m+ | 98.1M (+1 unread) | 131.5k | claude-opus-5-5, claude-sonnet-5-5 | 1 | 2 | 10 | 0/0 | — | 0 | accepted | 0 | 0 | 43 | 67 | +7854/-58 |
| S33-factory-gate-stamp | rule/rule, task/rule | 4h30m | 39.7M | 120.9k | claude-opus-5-5, claude-sonnet-5-5 | 5 | 2 | 6 | 10/7 | — | 5 | accepted | 0 | 0 | 31 | 135 | +42301/-105 |
| S38-factory-test-selection | rule/rule, story/rule | 18h00m | 237.8M | 352k | claude-opus-5-5, claude-sonnet-5-5 | 3 | 2 | 11 | 0/0 | — | 18 | accepted | 0 | 0 | 56 | 227 | +38148/-124 |
| S39-benchmark-elapsed | story/rule, task/rule | 6h50m | 207.4M | 265.3k | claude-opus-5-5, claude-sonnet-5-5 | 2 | 2 | 16 | 0/0 | — | 28 | accepted | 0 | 0 | 57 | 81 | +23082/-242 |
| S43-test-declarations | — | 17m27s | 10.7M | 14k | claude-opus-5-5 | 1 | 0 | 0 | 11/0 | — | 0 | — | 0 | 0 | — | — | — |

delegate/cycle = how implementation was delegated and driven; in = input + cache read + cache creation tokens; gaps = before/after converge; +tasks = tasks converge appended; sessions = harness sessions read; a stage's tokens are a floor (the turn that ends it is partly uncounted); a trailing + makes wall a floor because an unbracketed stage is missing; tokens are not prices.

## Stages

### The feature, above the slice loop — 1h47m

| stage | started (UTC) | wall | in | out | model | agent | delegated | reported |
|---|---|---|---|---|---|---|---|---|
| ground | 2026-10-03 01:44 | 40s | 90.5k | 3.5k | claude-fable-5-1 | — | no | — |
| bosun | 2026-10-03 01:45 | 6m27s | 1.6M | 36.2k | claude-fable-5-1 | drive-bosun | yes | — |
| split | 2026-10-03 01:51 | 42m16s | 2.4M | 14.7k | claude-fable-5-1 | — | no | — |
| skipper | 2026-10-06 03:16 | 1m52s | 718.8k | 7.6k | claude-opus-5-5 | drive-skipper | yes | driver=cruise |
| skipper | 2026-10-06 03:33 | 4m13s | 447.4k | 1.2k | claude-opus-5-5 | drive-skipper | yes | driver=cruise |
| gaps | 2026-10-06 04:16 | 9m57s | 2.3M | 3.5k | claude-opus-5-5 | drive-gaps | yes | findings=14, driver=cruise |
| skipper | 2026-10-06 04:26 | 12m05s | 4.9M | 15.8k | claude-opus-5-5 | drive-skipper | yes | driver=cruise |
| gaps | 2026-10-06 06:22 | 10m03s | 3.5M | 8.9k | claude-opus-5-5 | drive-gaps | yes | findings=12, driver=cruise |
| skipper | 2026-10-06 07:28 | 8m24s | 18.4M | 33.8k | claude-opus-5-5, claude-sonnet-5-5 | drive-gaps, drive-implement, drive-skipper, drive-slice, drive-tasks | yes | driver=cruise |
| skipper | 2026-10-07 06:28 | 6m09s | 4.2M | 25.3k | claude-opus-5-5 | drive-skipper | yes | driver=cruise |
| skipper | 2026-10-07 07:43 | 4m56s | 8.2M | 16.8k | claude-opus-5-5, claude-sonnet-5-5 | drive-implement, drive-skipper, drive-slice | yes | driver=cruise |

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

### S03-verify-stamp — 5h05m

| stage | started (UTC) | wall | in | out | model | agent | delegated | reported |
|---|---|---|---|---|---|---|---|---|
| gaps | 2026-10-04 01:40 | 1m57s | 760.7k | 5.7k | claude-fable-5-1 | — | no | driver=cruise |
| skipper | 2026-10-04 01:42 | 3m31s | 1.7M | 10.1k | claude-fable-5-1 | drive-skipper | yes | driver=cruise |
| gaps | 2026-10-04 01:45 | 1m58s | 432.9k | 12.3k | claude-fable-5-1 | — | no | gaps=31, driver=cruise |
| plan | 2026-10-04 01:48 | 5m06s | 1.7M | 28.9k | claude-fable-5-1 | — | no | driver=cruise |
| tasks | 2026-10-04 01:53 | 2m51s | 867.9k | 5.1k | claude-fable-5-1, claude-sonnet-5-5 | drive-tasks | yes | driver=cruise |
| implement | 2026-10-04 01:56 | 1h23m | 35M | 51.1k | claude-fable-5-1, claude-sonnet-5-5 | drive-implement | yes | verify_failures=18, delegate=story, cycle=rule, split=0, driver=cruise |
| converge | 2026-10-04 03:20 | 14m36s | 4.4M | 6.3k | claude-fable-5-1 | drive-converge | yes | driver=cruise |
| implement | 2026-10-04 03:34 | 17m10s | 6.3M | 23.1k | claude-fable-5-1, claude-sonnet-5-5 | drive-implement | yes | verify_failures=1, delegate=task, cycle=rule, split=0, driver=cruise |
| converge | 2026-10-04 03:52 | 12m36s | 2M | 8.3k | claude-fable-5-1 | drive-converge | yes | driver=cruise |
| implement | 2026-10-04 04:04 | 20m45s | 2.2M | 9.2k | claude-fable-5-1, claude-sonnet-5-5 | drive-implement | yes | verify_failures=3, delegate=task, cycle=rule, split=0, driver=cruise |
| converge | 2026-10-04 04:25 | 5m46s | 1.8M | 6.1k | claude-fable-5-1 | drive-converge | yes | driver=cruise |
| gaps | 2026-10-04 04:31 | 6m53s | 2.8M | 4k | claude-fable-5-1 | drive-gaps | yes | gaps=8, driver=cruise |
| skipper | 2026-10-04 04:38 | 4m43s | 1.2M | 5.3k | claude-fable-5-1 | drive-skipper | yes | driver=cruise |
| implement | 2026-10-04 04:43 | 27m38s | 10.7M | 17.3k | claude-fable-5-1, claude-sonnet-5-5 | drive-implement | yes | verify_failures=3, delegate=task, cycle=rule, split=0, driver=cruise |
| demo | 2026-10-04 05:11 | 15m13s | 3.3M | 6.8k | claude-fable-5-1 | drive-hand | yes | outcome=accepted, driver=cruise |
| adversary | 2026-10-04 05:27 | 12m02s | 8.2M | 17.6k | claude-fable-5-1 | drive-adversary | yes | findings=18, seams=3, driver=cruise |
| skipper | 2026-10-04 05:39 | 5m09s | 1.2M | 11.4k | claude-fable-5-1 | drive-skipper | yes | driver=cruise |
| implement | 2026-10-04 05:45 | 59m06s | 26.4M | 30.3k | claude-fable-5-1, claude-sonnet-5-5 | drive-implement | yes | verify_failures=2, delegate=task, cycle=rule, split=0, driver=cruise |
| demo | 2026-10-04 06:45 | 4m50s | 1.6M | 8.3k | claude-fable-5-1 | drive-hand | yes | outcome=accepted, driver=cruise |

### S04-parallel-gate — 5h06m

| stage | started (UTC) | wall | in | out | model | agent | delegated | reported |
|---|---|---|---|---|---|---|---|---|
| skipper | 2026-10-04 11:11 | 5m17s | 2M | 12.4k | claude-fable-5-1 | drive-skipper | yes | driver=cruise |
| gaps | 2026-10-04 11:17 | 2m27s | 1.1M | 20.1k | claude-fable-5-1 | — | no | gaps=63, driver=cruise |
| plan | 2026-10-04 11:22 | 3m49s | 1.4M | 21.5k | claude-fable-5-1 | — | no | driver=cruise |
| tasks | 2026-10-04 11:26 | 12m51s | 7.5M | 6k | claude-fable-5-1, claude-sonnet-5-5 | drive-tasks | yes | driver=cruise |
| pin | 2026-10-04 11:39 | 2m01s | 1.6M | 5.3k | claude-fable-5-1, claude-sonnet-5-5 | drive-implement | yes | driver=cruise |
| implement | 2026-10-04 11:41 | 36m38s | 14.9M | 28.6k | claude-fable-5-1, claude-sonnet-5-5 | drive-implement | yes | — |
| skipper | 2026-10-04 12:18 | 17m28s | 8.4M | 19k | claude-fable-5-1, claude-sonnet-5-5 | drive-implement, drive-skipper | yes | driver=cruise |
| converge | 2026-10-04 13:04 | 8m29s | 3.7M | 6.9k | claude-fable-5-1 | drive-converge | yes | driver=cruise |
| implement | 2026-10-04 13:13 | 13m35s | 2.4M | 4.8k | claude-fable-5-1, claude-sonnet-5-5 | drive-implement | yes | verify_failures=0, delegate=task, cycle=rule, split=0, driver=cruise |
| converge | 2026-10-04 13:27 | 7m57s | 2.7M | 6.1k | claude-fable-5-1 | drive-converge | yes | driver=cruise |
| skipper | 2026-10-04 13:35 | 5m02s | 666.5k | 7.3k | claude-fable-5-1 | drive-skipper | yes | driver=cruise |
| implement | 2026-10-04 13:40 | 11m04s | 1.6M | 4.9k | claude-fable-5-1, claude-sonnet-5-5 | drive-implement | yes | verify_failures=0, delegate=task, cycle=rule, split=0, driver=cruise |
| gaps | 2026-10-04 13:51 | 12m28s | 13.9M | 12.8k | claude-fable-5-1 | drive-gaps | yes | gaps=19, driver=cruise |
| skipper | 2026-10-04 14:03 | 6m01s | 1.6M | 3k | claude-fable-5-1 | drive-skipper | yes | driver=cruise |
| implement | 2026-10-04 14:10 | 49m41s | 13.6M | 29.5k | claude-fable-5-1, claude-sonnet-5-5 | drive-implement | yes | verify_failures=0, delegate=task, cycle=rule, split=0, driver=cruise |
| converge | 2026-10-04 15:00 | 7m25s | 2.6M | 7.1k | claude-fable-5-1 | drive-converge | yes | driver=cruise |
| demo | 2026-10-04 15:08 | 11m26s | 4.2M | 9.5k | claude-fable-5-1 | drive-hand | yes | outcome=accepted, driver=cruise |
| adversary | 2026-10-04 15:20 | 12m02s | 6M | 12.5k | claude-fable-5-1 | drive-adversary | yes | findings=9, seams=2, driver=cruise |
| skipper | 2026-10-04 15:33 | 7m31s | 2.2M | 10.1k | claude-fable-5-1 | drive-skipper | yes | driver=cruise |
| implement | 2026-10-04 15:40 | 25m47s | 4.9M | 8.9k | claude-fable-5-1, claude-sonnet-5-5 | drive-implement | yes | verify_failures=0, delegate=task, cycle=rule, split=0, driver=cruise |
| demo | 2026-10-04 16:06 | 47m07s | 9.5M | 14.7k | claude-fable-5-1 | drive-hand | yes | outcome=accepted, driver=cruise |

### S05-xdist — 1h43m

| stage | started (UTC) | wall | in | out | model | agent | delegated | reported |
|---|---|---|---|---|---|---|---|---|
| skipper | 2026-10-04 19:16 | 1m37s | 1.4M | 7.6k | claude-opus-5-5 | drive-skipper | yes | driver=cruise |
| gaps | 2026-10-04 19:17 | 49s | 927.3k | 5.4k | claude-opus-5-5 | — | no | gaps=13, driver=cruise |
| plan | 2026-10-04 19:18 | 30s | 194.7k | 728 | claude-opus-5-5 | — | no | driver=cruise |
| tasks | 2026-10-04 19:19 | 2m31s | 757.4k | 2.8k | claude-opus-5-5, claude-sonnet-5-5 | drive-tasks | yes | driver=cruise |
| implement | 2026-10-04 19:21 | 21m54s | 7.3M | 10.4k | claude-opus-5-5, claude-sonnet-5-5 | drive-implement | yes | verify_failures=0, delegate=story, cycle=rule, split=0, driver=cruise |
| converge | 2026-10-04 20:06 | 6m37s | 4M | 4.4k | claude-opus-5-5 | drive-converge | yes | driver=cruise |
| implement | 2026-10-04 20:12 | 10m43s | 3.6M | 7.2k | claude-opus-5-5, claude-sonnet-5-5 | drive-implement | yes | verify_failures=0, delegate=task, cycle=rule, split=0, driver=cruise |
| converge | 2026-10-04 20:23 | 4m59s | 3.5M | 2.3k | claude-opus-5-5 | drive-converge | yes | driver=cruise |
| gaps | 2026-10-04 20:28 | 4m30s | 2.6M | 2.2k | claude-opus-5-5 | drive-gaps | yes | gaps=3, driver=cruise |
| implement | 2026-10-04 20:33 | 1m49s | 1.1M | 3.8k | claude-opus-5-5, claude-sonnet-5-5 | drive-implement | yes | verify_failures=0, delegate=task, cycle=rule, split=0, driver=cruise |
| demo | 2026-10-04 20:35 | 8m02s | 3.5M | 5.1k | claude-opus-5-5 | drive-hand | yes | outcome=implementation, driver=cruise |
| implement | 2026-10-04 20:43 | 1m36s | 661.4k | 4.3k | claude-opus-5-5, claude-sonnet-5-5 | drive-implement | yes | verify_failures=0, delegate=task, cycle=rule, split=0, driver=cruise |
| demo | 2026-10-04 20:45 | 4m07s | 1.8M | 5.5k | claude-opus-5-5 | drive-hand | yes | outcome=accepted, driver=cruise |
| adversary | 2026-10-04 22:13 | 6m11s | 3.2M | 7.6k | claude-opus-5-5 | drive-adversary | yes | findings=8, seams=2, driver=cruise |
| skipper | 2026-10-04 22:20 | 3m02s | 1.8M | 10.9k | claude-opus-5-5 | drive-skipper | yes | driver=cruise, note=D106-D108 |
| implement | 2026-10-04 22:24 | 14m54s | 6.5M | 24.2k | claude-opus-5-5, claude-sonnet-5-5 | drive-implement | yes | verify_failures=0, delegate=task, cycle=rule, driver=cruise |
| demo | 2026-10-04 22:39 | 9m54s | 2.4M | 8.3k | claude-opus-5-5 | drive-hand | yes | outcome=accepted, driver=cruise |

### S06-scoped-gate — 12h37m+

| stage | started (UTC) | wall | in | out | model | agent | delegated | reported |
|---|---|---|---|---|---|---|---|---|
| gaps | 2026-10-05 01:00 | 4m26s | 3.9M | 12.4k | claude-opus-5-5 | Explore | yes | driver=cruise |
| skipper | 2026-10-05 01:05 | 2m20s | 1.7M | 7.6k | claude-opus-5-5 | drive-skipper | yes | driver=cruise |
| gaps | 2026-10-05 01:09 | unbracketed | unknown | unknown | claude-opus-5-5 | — | no | gaps=19, driver=cruise |
| plan | 2026-10-05 01:09 | 15m25s | 12.9M | 8.2k | claude-opus-5-5 | general-purpose | yes | driver=cruise |
| skipper | 2026-10-05 08:10 | 2m08s | 1.3M | 5.4k | claude-opus-5-5 | drive-skipper | yes | driver=cruise |
| tasks | 2026-10-05 08:12 | 17s | 209.8k | 1.9k | claude-opus-5-5 | — | no | — |
| tasks | 2026-10-05 10:24 | 4m17s | 1M | 5.4k | claude-opus-5-5, claude-sonnet-5-5 | drive-tasks | yes | driver=cruise |
| implement | 2026-10-05 10:37 | 2h06m | 47.1M | 55.2k | claude-opus-5-5, claude-sonnet-5-5 | drive-implement | yes | verify_failures=0, delegate=rule, cycle=rule, split=3, driver=cruise |
| converge | 2026-10-05 13:07 | 10m10s | 7.1M | 7k | claude-opus-5-5 | drive-converge | yes | driver=cruise |
| skipper | 2026-10-05 13:17 | 10m08s | 2.2M | 7.9k | claude-opus-5-5 | drive-skipper | yes | driver=cruise |
| implement | 2026-10-05 13:27 | 53m30s | 16.1M | 20.3k | claude-opus-5-5, claude-sonnet-5-5 | drive-implement | yes | verify_failures=0, delegate=task, cycle=rule, split=2, driver=cruise |
| converge | 2026-10-05 14:21 | 10m04s | 4.7M | 3.6k | claude-opus-5-5 | drive-converge | yes | driver=cruise |
| skipper | 2026-10-05 14:31 | 4m25s | 2M | 7.2k | claude-opus-5-5 | drive-skipper | yes | driver=cruise |
| implement | 2026-10-05 14:36 | 1h49m | 25.7M | 32k | claude-opus-5-5, claude-sonnet-5-5 | drive-implement | yes | verify_failures=0, delegate=task, cycle=rule, split=0, driver=cruise |
| converge | 2026-10-05 16:25 | 9m56s | 4.3M | 5.6k | claude-opus-5-5 | drive-converge | yes | driver=cruise |
| skipper | 2026-10-05 16:35 | 4m26s | 1.8M | 5.1k | claude-opus-5-5 | drive-skipper | yes | driver=cruise |
| implement | 2026-10-05 16:41 | 29m56s | 24.3M | 29.8k | claude-opus-5-5, claude-sonnet-5-5 | drive-implement, drive-slice, drive-tasks | yes | verify_failures=0, delegate=task, cycle=rule, split=2, driver=cruise |
| converge | 2026-10-05 17:11 | 19m34s | 42.2M | 57.3k | claude-opus-5-5, claude-sonnet-5-5 | drive-converge, drive-implement, drive-slice, drive-tasks | yes | driver=cruise |
| implement | 2026-10-05 17:37 | 48m20s | 64.1M | 59.8k | claude-opus-5-5, claude-sonnet-5-5 | drive-converge, drive-gaps, drive-implement, drive-slice | yes | verify_failures=0, delegate=task, cycle=rule, split=0, driver=cruise |
| converge | 2026-10-05 18:26 | 16m55s | 6.9M | 5.5k | claude-opus-5-5 | drive-converge | yes | driver=cruise |
| implement | 2026-10-05 18:43 | 2h43m | 70.6M | 82.3k | claude-opus-5-5, claude-sonnet-5-5 | drive-converge, drive-gaps, drive-implement, drive-skipper, drive-slice | yes | verify_failures=0, delegate=task, cycle=rule, split=2, driver=cruise |
| demo | 2026-10-05 21:56 | 10m12s | 4.4M | 13.6k | claude-opus-5-5 | drive-hand | yes | outcome=accepted, driver=cruise |
| adversary | 2026-10-05 22:07 | 21m06s | 23.9M | 24.5k | claude-opus-5-5 | drive-adversary, drive-hand | yes | findings=20, seams=3, driver=cruise |
| implement | 2026-10-05 22:34 | 1h20m | 41.7M | 66.7k | claude-opus-5-5, claude-sonnet-5-5 | drive-hand, drive-implement, drive-slice | yes | verify_failures=0, delegate=task, cycle=rule, split=3, driver=cruise |

### S07-scoped-checks — 7h57m

| stage | started (UTC) | wall | in | out | model | agent | delegated | reported |
|---|---|---|---|---|---|---|---|---|
| gaps | 2026-10-07 06:16 | 17m28s | 96.5k | 478 | claude-opus-5-5 | — | no | gaps=14, driver=cruise |
| plan | 2026-10-07 06:36 | 7m39s | 17M | 8.3k | claude-opus-5-5 | Explore, drive-slice | yes | note=10 rules, no open question, driver=cruise |
| tasks | 2026-10-07 06:43 | 2m09s | 2.6M | 14.9k | claude-opus-5-5, claude-sonnet-5-5 | drive-slice, drive-tasks | yes | note=7 tasks, T005 parallel to T002-T004, delegate=drive-tasks, driver=cruise |
| implement | 2026-10-07 07:33 | 39m46s | 67.9M | 92.4k | claude-opus-5-5, claude-sonnet-5-5 | drive-converge, drive-gaps, drive-implement, drive-skipper, drive-slice, drive-tasks | yes | note=T001-T009, 4 delegates, 9 modules undeclared, delegate=drive-implement, cycle=rule, driver=cruise |
| converge | 2026-10-07 08:13 | 35m11s | 54.3M | 67.8k | claude-opus-5-5, claude-sonnet-5-5 | drive-adversary, drive-converge, drive-hand, drive-implement, drive-slice | yes | findings=9, note=pass 2 not converged: T014 HIGH needs the host (S06 data-model table), driver=cruise |
| gaps | 2026-10-07 09:11 | 20m00s | 21M | 15.6k | claude-opus-5-5 | drive-gaps, drive-slice | yes | gaps=7, driver=cruise |
| implement | 2026-10-07 09:32 | 24m32s | 24M | 34.9k | claude-opus-5-5, claude-sonnet-5-5 | drive-implement, drive-slice | yes | note=after-converge T015-T020, 3 delegates, delegate=drive-implement, driver=cruise |
| demo | 2026-10-07 09:59 | 10m40s | 6.8M | 7.8k | claude-opus-5-5 | drive-hand | yes | outcome=accepted, driver=cruise |
| adversary | 2026-10-07 15:24 | 12m30s | 10.1M | 9.8k | claude-opus-5-5 | drive-adversary | yes | findings=8, seams=2, driver=cruise |
| implement | 2026-10-07 15:36 | 56m21s | 37.2M | 32.5k | claude-opus-5-5 | drive-implement | yes | verify_failures=0, delegate=drive-implement, cycle=rule, split=2, driver=cruise |
| gate | 2026-10-07 17:00 | 4h10m | 17.7M | 14.4k | claude-opus-5-5 | — | no | verify_failures=1, driver=cruise |

### S08-scoped-mutation — 8h43m

| stage | started (UTC) | wall | in | out | model | agent | delegated | reported |
|---|---|---|---|---|---|---|---|---|
| gaps | 2026-10-05 16:41 | 17m48s | 5.8M | 12.7k | claude-opus-5-5 | drive-gaps | yes | gaps=19, driver=cruise |
| plan | 2026-10-05 17:03 | 8m36s | 11.6M | 19.2k | claude-opus-5-5, claude-sonnet-5-5 | drive-converge, drive-implement, drive-slice, drive-tasks | yes | driver=cruise |
| tasks | 2026-10-05 17:11 | 4m29s | 8.7M | 14.3k | claude-opus-5-5, claude-sonnet-5-5 | drive-converge, drive-implement, drive-slice, drive-tasks | yes | driver=cruise |
| implement | 2026-10-05 17:17 | 1h35m | 126.4M | 128.4k | claude-opus-5-5, claude-sonnet-5-5 | drive-converge, drive-gaps, drive-implement, drive-skipper, drive-slice | yes | verify_failures=0, delegate=story, cycle=rule, split=0, driver=cruise |
| converge | 2026-10-05 18:53 | 7m29s | 7.8M | 14k | claude-opus-5-5, claude-sonnet-5-5 | drive-converge, drive-implement, drive-skipper, drive-slice | yes | driver=cruise |
| implement | 2026-10-05 19:01 | 31m54s | 17M | 23.3k | claude-opus-5-5, claude-sonnet-5-5 | drive-implement, drive-slice | yes | verify_failures=0, delegate=story, cycle=rule, split=0, driver=cruise |
| converge | 2026-10-05 19:33 | 5m51s | 2.9M | 3.6k | claude-opus-5-5, claude-sonnet-5-5 | drive-converge, drive-implement, drive-slice | yes | driver=cruise |
| gaps | 2026-10-05 19:39 | 5m39s | 5.7M | 3.3k | claude-opus-5-5, claude-sonnet-5-5 | drive-gaps, drive-implement, drive-slice | yes | gaps=7, driver=cruise |
| implement | 2026-10-05 19:52 | 2h03m | 27.7M | 30.1k | claude-opus-5-5, claude-sonnet-5-5 | drive-implement, drive-slice | yes | verify_failures=0, delegate=story, cycle=rule, split=0, driver=cruise |
| demo | 2026-10-05 22:08 | 19m31s | 21.7M | 16.8k | claude-opus-5-5 | drive-adversary, drive-hand | yes | outcome=implementation, driver=cruise |
| implement | 2026-10-05 22:36 | 52m57s | 24.9M | 36.4k | claude-opus-5-5, claude-sonnet-5-5 | drive-hand, drive-implement, drive-slice | yes | verify_failures=0, delegate=story, cycle=rule, split=0, driver=cruise |
| demo | 2026-10-05 23:32 | 9m57s | 6.6M | 11.2k | claude-opus-5-5, claude-sonnet-5-5 | drive-hand, drive-implement | yes | outcome=implementation, driver=cruise |
| implement | 2026-10-05 23:43 | 37m32s | 8.6M | 17.6k | claude-opus-5-5, claude-sonnet-5-5 | drive-implement, drive-slice | yes | verify_failures=0, delegate=story, cycle=rule, split=0, driver=cruise |
| demo | 2026-10-06 00:23 | 8m01s | 5.8M | 10.7k | claude-opus-5-5 | drive-hand | yes | outcome=accepted, driver=cruise |
| implement | 2026-10-06 00:35 | 36m14s | 9M | 10.5k | claude-opus-5-5, claude-sonnet-5-5 | drive-implement, drive-slice | yes | verify_failures=0, delegate=story, cycle=rule, split=0, driver=cruise |
| adversary | 2026-10-06 03:16 | 16m42s | 12.7M | 11.1k | claude-opus-5-5 | drive-adversary | yes | findings=16, seams=2, driver=cruise |
| implement | 2026-10-06 03:33 | 42m17s | 35.7M | 35.9k | claude-opus-5-5, claude-sonnet-5-5 | drive-implement | yes | driver=cruise |

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

### S14-result-contract — 2h11m

| stage | started (UTC) | wall | in | out | model | agent | delegated | reported |
|---|---|---|---|---|---|---|---|---|
| gaps | 2026-10-05 16:41 | 10m14s | 101.9k | 899 | claude-opus-5-5 | — | no | — |
| skipper | 2026-10-05 16:51 | 7m34s | 5.3M | 28.6k | claude-opus-5-5 | drive-skipper | yes | driver=cruise |
| plan | 2026-10-05 17:00 | 6m44s | 10.5M | 6.1k | claude-opus-5-5, claude-sonnet-5-5 | drive-implement, drive-slice | yes | driver=cruise |
| tasks | 2026-10-05 17:07 | 2m51s | 2.8M | 7.5k | claude-opus-5-5, claude-sonnet-5-5 | drive-implement, drive-slice, drive-tasks | yes | driver=cruise |
| implement | 2026-10-05 17:11 | 19m16s | 41.1M | 54.9k | claude-opus-5-5, claude-sonnet-5-5 | drive-converge, drive-implement, drive-slice, drive-tasks | yes | verify_failures=0, delegate=story, cycle=rule, split=2, driver=cruise |
| converge | 2026-10-05 17:30 | 16m12s | 29.7M | 34.7k | claude-opus-5-5, claude-sonnet-5-5 | drive-converge, drive-implement, drive-skipper, drive-slice | yes | driver=cruise |
| implement | 2026-10-05 17:47 | 16m14s | 29.1M | 24.7k | claude-opus-5-5, claude-sonnet-5-5 | drive-implement, drive-slice | yes | verify_failures=0, delegate=story, cycle=rule, split=0, driver=cruise |
| converge | 2026-10-05 18:03 | 6m04s | 12M | 6.4k | claude-opus-5-5, claude-sonnet-5-5 | drive-converge, drive-implement, drive-slice | yes | driver=cruise |
| gaps | 2026-10-05 18:09 | 4m51s | 3.7M | 2.7k | claude-opus-5-5, claude-sonnet-5-5 | drive-gaps, drive-implement, drive-slice | yes | gaps=7, driver=cruise |
| demo | 2026-10-05 22:34 | 10m30s | 9.5M | 24.8k | claude-opus-5-5, claude-sonnet-5-5 | drive-hand, drive-implement, drive-slice | yes | outcome=accepted, driver=cruise |
| adversary | 2026-10-06 07:17 | 10m48s | 24.5M | 19.3k | claude-opus-5-5 | drive-adversary, drive-gaps, drive-slice | yes | findings=14, seams=2, driver=cruise |
| implement | 2026-10-06 07:37 | 20m40s | 48.6M | 56.3k | claude-opus-5-5, claude-sonnet-5-5 | drive-implement, drive-slice | yes | driver=cruise |

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

### S24-ci-fetches-slice-base — 1h17m

| stage | started (UTC) | wall | in | out | model | agent | delegated | reported |
|---|---|---|---|---|---|---|---|---|
| gaps | 2026-10-03 17:13 | 1m37s | 630.6k | 8.4k | claude-fable-5-1 | — | no | driver=cruise |
| skipper | 2026-10-03 17:15 | 4m15s | 895.9k | 3.2k | claude-fable-5-1 | drive-skipper | yes | driver=cruise |
| bosun | 2026-10-03 17:19 | 1m32s | 384k | 4.5k | claude-fable-5-1 | drive-bosun | yes | driver=cruise |
| gaps | 2026-10-04 08:00 | 3m06s | 1.2M | 18.2k | claude-fable-5-1 | — | no | gaps=13, driver=cruise |
| plan | 2026-10-04 08:03 | 2m20s | 1.2M | 13.8k | claude-fable-5-1 | — | no | driver=cruise |
| tasks | 2026-10-04 08:06 | 2m40s | 645.2k | 3.2k | claude-fable-5-1, claude-sonnet-5-5 | drive-tasks | yes | driver=cruise |
| implement | 2026-10-04 08:09 | 8m12s | 6.9M | 28k | claude-fable-5-1, claude-sonnet-5-5 | drive-implement | yes | verify_failures=0, delegate=rule, cycle=rule, split=0, driver=cruise |
| converge | 2026-10-04 08:17 | 8m45s | 5.4M | 8.2k | claude-fable-5-1 | drive-converge | yes | driver=cruise |
| implement | 2026-10-04 08:26 | 3m59s | 2.6M | 9.8k | claude-fable-5-1, claude-sonnet-5-5 | drive-implement | yes | verify_failures=0, delegate=task, cycle=rule, split=0, driver=cruise |
| converge | 2026-10-04 08:30 | 2m14s | 1.1M | 4.9k | claude-fable-5-1 | drive-converge | yes | driver=cruise |
| gaps | 2026-10-04 08:33 | 4m28s | 2M | 5.4k | claude-fable-5-1 | drive-gaps | yes | gaps=7, driver=cruise |
| skipper | 2026-10-04 08:37 | 3m38s | 1.5M | 6.1k | claude-fable-5-1 | drive-skipper | yes | driver=cruise |
| implement | 2026-10-04 08:42 | 2m06s | 4.1M | 15.2k | claude-fable-5-1, claude-sonnet-5-5 | drive-implement | yes | verify_failures=0, delegate=task, cycle=rule, split=0, driver=cruise |
| demo | 2026-10-04 08:44 | 5m20s | 1.6M | 4k | claude-fable-5-1 | drive-hand | yes | outcome=implementation, driver=cruise |
| implement | 2026-10-04 08:50 | 25s | 900.5k | 3.2k | claude-fable-5-1 | — | no | verify_failures=0, delegate=task, cycle=rule, split=0, driver=cruise |
| demo | 2026-10-04 08:50 | 3m04s | 1.4M | 2.9k | claude-fable-5-1 | drive-hand | yes | outcome=accepted, driver=cruise |
| adversary | 2026-10-04 08:53 | 7m07s | 4M | 7.9k | claude-fable-5-1 | drive-adversary | yes | findings=8, seams=2, driver=cruise |
| skipper | 2026-10-04 09:01 | 4m21s | 2M | 15.7k | claude-fable-5-1 | drive-skipper | yes | driver=cruise |
| implement | 2026-10-04 09:06 | 8m16s | 4.9M | 12.1k | claude-fable-5-1, claude-sonnet-5-5 | drive-implement | yes | verify_failures=0, delegate=task, cycle=rule, split=0, driver=cruise |

### S26-reversibility-line — 5h04m

| stage | started (UTC) | wall | in | out | model | agent | delegated | reported |
|---|---|---|---|---|---|---|---|---|
| gaps | 2026-10-07 06:16 | 17m27s | 10.7M | 14k | claude-opus-5-5 | drive-gaps | yes | gaps=16, driver=cruise |
| plan | 2026-10-07 06:36 | 8m38s | 17.3M | 8.4k | claude-opus-5-5, claude-sonnet-5-5 | Explore, drive-slice, drive-tasks | yes | note=4 open questions, none blocking, driver=cruise |
| tasks | 2026-10-07 06:44 | 1m53s | 1.8M | 16.8k | claude-opus-5-5, claude-sonnet-5-5 | drive-slice, drive-tasks | yes | delegate=drive-tasks, driver=cruise |
| implement | 2026-10-07 07:34 | 14m42s | 25.6M | 43.4k | claude-opus-5-5, claude-sonnet-5-5 | drive-implement, drive-skipper, drive-slice | yes | delegate=drive-implement, cycle=rule, split=2, driver=cruise |
| converge | 2026-10-07 07:48 | 10m20s | 23.8M | 20.1k | claude-opus-5-5, claude-sonnet-5-5 | drive-converge, drive-implement, drive-slice, drive-tasks | yes | note=converged pass 1, findings=9, delegate=drive-converge, driver=cruise |
| gaps | 2026-10-07 08:07 | 9m27s | 11M | 16.5k | claude-opus-5-5, claude-sonnet-5-5 | drive-converge, drive-gaps, drive-implement, drive-slice | yes | gaps=8, driver=cruise |
| implement | 2026-10-07 08:17 | 5m54s | 14.6M | 14.6k | claude-opus-5-5, claude-sonnet-5-5 | drive-converge, drive-implement, drive-slice | yes | delegate=drive-implement, cycle=rule, split=2, note=after-converge T010-T017, driver=cruise |
| demo | 2026-10-07 08:27 | 9m48s | 10.6M | 11.5k | claude-opus-5-5, claude-sonnet-5-5 | drive-converge, drive-hand, drive-implement, drive-slice | yes | outcome=accepted, driver=cruise |
| adversary | 2026-10-07 08:37 | 10m32s | 13.3M | 17.9k | claude-opus-5-5, claude-sonnet-5-5 | drive-adversary, drive-converge, drive-implement, drive-slice | yes | findings=12, seams=2, driver=cruise |
| implement | 2026-10-07 08:47 | 20m04s | 24.4M | 29.7k | claude-opus-5-5, claude-sonnet-5-5 | drive-converge, drive-implement, drive-slice | yes | verify_failures=0, delegate=drive-implement, cycle=rule, split=2, driver=cruise |
| gate | 2026-10-07 09:11 | 3h15m | 66.1M | 75.8k | claude-opus-5-5, claude-sonnet-5-5 | drive-gaps, drive-hand, drive-implement, drive-slice | yes | verify_failures=1, driver=cruise |

### S27-provisional-decisions — 4h20m+

| stage | started (UTC) | wall | in | out | model | agent | delegated | reported |
|---|---|---|---|---|---|---|---|---|
| skipper | 2026-10-07 21:17 | 2m03s | 1.1M | 5.7k | claude-opus-5-5 | drive-skipper | yes | driver=cruise |
| plan | 2026-10-07 21:22 | 7m52s | 4.3M | 1.7k | claude-opus-5-5 | drive-slice | yes | driver=cruise |
| tasks | 2026-10-07 21:30 | 2m03s | 1.2M | 3.4k | claude-opus-5-5, claude-sonnet-5-5 | drive-slice, drive-tasks | yes | driver=cruise |
| implement | 2026-10-07 21:46 | 1h23m | 25.2M | 27.9k | claude-opus-5-5, claude-sonnet-5-5 | drive-implement, drive-slice | yes | driver=cruise, delegate=story, cycle=rule, split=6 |
| converge | 2026-10-07 23:10 | 18m09s | 10.5M | 21.1k | claude-opus-5-5, claude-sonnet-5-5 | drive-converge, drive-implement, drive-slice | yes | driver=cruise |
| implement | 2026-10-07 23:29 | 1m53s | 1M | 3.4k | claude-opus-5-5, claude-sonnet-5-5 | drive-implement, drive-slice | yes | driver=cruise, delegate=story, cycle=rule, split=1 |
| converge | 2026-10-07 23:31 | 5m47s | 3.2M | 5.2k | claude-opus-5-5 | drive-converge, drive-slice | yes | driver=cruise |
| implement | 2026-10-08 00:48 | 1h34m | 24.5M | 28.6k | claude-opus-5-5, claude-sonnet-5-5 | drive-implement | yes | driver=cruise |
| demo | 2026-10-08 02:28 | unbracketed | unknown | unknown | claude-opus-5-5 | — | no | driver=cruise, outcome=accepted |
| adversary | 2026-10-08 02:28 | 8m27s | 9.7M | 19.2k | claude-opus-5-5 | drive-adversary | yes | driver=cruise |
| implement | 2026-10-08 02:37 | 35m31s | 17.2M | 15.4k | claude-opus-5-5, claude-sonnet-5-5 | drive-implement | yes | driver=cruise |

### S33-factory-gate-stamp — 4h30m

| stage | started (UTC) | wall | in | out | model | agent | delegated | reported |
|---|---|---|---|---|---|---|---|---|
| gaps | 2026-10-04 18:59 | 53s | 477.1k | 5.4k | claude-opus-5-5 | — | no | gaps=10, driver=cruise |
| plan | 2026-10-04 19:00 | 33s | 253.8k | 3.7k | claude-opus-5-5 | — | no | driver=cruise |
| tasks | 2026-10-04 19:01 | 1m23s | 369.1k | 2.2k | claude-opus-5-5, claude-sonnet-5-5 | drive-tasks | yes | driver=cruise |
| implement | 2026-10-04 19:02 | 8m23s | 4.2M | 5k | claude-opus-5-5, claude-sonnet-5-5 | drive-implement | yes | verify_failures=0, delegate=rule, cycle=rule, split=0, driver=cruise |
| converge | 2026-10-05 00:25 | 6m00s | 3M | 7.2k | claude-opus-5-5 | drive-converge | yes | driver=cruise |
| skipper | 2026-10-05 00:31 | 1m11s | 550.6k | 1.3k | claude-opus-5-5 | drive-skipper | yes | driver=cruise |
| implement | 2026-10-05 00:33 | 11m45s | 3.3M | 4.8k | claude-opus-5-5, claude-sonnet-5-5 | drive-implement | yes | verify_failures=0, delegate=rule, cycle=rule, split=0, driver=cruise |
| converge | 2026-10-05 00:45 | 5m13s | 2.2M | 4k | claude-opus-5-5 | drive-converge | yes | driver=cruise |
| implement | 2026-10-05 00:50 | 9m00s | 1.9M | 6.7k | claude-opus-5-5, claude-sonnet-5-5 | drive-implement | yes | verify_failures=0, delegate=rule, cycle=rule, split=0, driver=cruise |
| gaps | 2026-10-05 02:56 | 6m51s | 3.4M | 2.5k | claude-opus-5-5 | drive-gaps | yes | driver=cruise, gaps=7 |
| skipper | 2026-10-05 03:03 | 1m02s | 1.1M | 7.2k | claude-opus-5-5 | drive-skipper | yes | — |
| implement | 2026-10-05 03:04 | 11m08s | 3.1M | 5.1k | claude-opus-5-5, claude-sonnet-5-5 | drive-implement, drive-skipper | yes | driver=cruise, delegate=rule, cycle=rule, verify_failures=0 |
| implement | 2026-10-05 03:16 | 11m13s | 2.4M | 11.2k | claude-opus-5-5, claude-sonnet-5-5 | drive-implement | yes | driver=cruise, delegate=rule, cycle=rule, verify_failures=0 |
| demo | 2026-10-05 05:36 | 2h16m | 3.2M | 14.5k | claude-opus-5-5 | drive-hand | yes | outcome=accepted, driver=cruise |
| implement | 2026-10-05 07:53 | 2m00s | 833k | 7.5k | claude-opus-5-5, claude-sonnet-5-5 | drive-implement | yes | verify_failures=0, delegate=task, cycle=rule, driver=cruise |
| adversary | 2026-10-05 07:55 | 8m50s | 6.3M | 12.1k | claude-opus-5-5 | drive-adversary | yes | findings=5, seams=1, driver=cruise |
| implement | 2026-10-05 08:04 | 4m16s | 2.1M | 12.5k | claude-opus-5-5, claude-sonnet-5-5 | drive-implement | yes | verify_failures=0, delegate=task, cycle=rule, driver=cruise |
| hand | 2026-10-05 08:57 | 43m49s | 1M | 7.7k | claude-opus-5-5 | drive-hand | yes | outcome=accepted, driver=cruise |

### S38-factory-test-selection — 18h00m

| stage | started (UTC) | wall | in | out | model | agent | delegated | reported |
|---|---|---|---|---|---|---|---|---|
| plan | 2026-10-06 04:44 | 3m13s | 1.8M | 4.5k | claude-opus-5-5 | drive-slice | yes | driver=cruise |
| tasks | 2026-10-06 04:48 | 3m36s | 1.8M | 2.7k | claude-opus-5-5, claude-sonnet-5-5 | drive-slice, drive-tasks | yes | driver=cruise |
| pin | 2026-10-06 04:51 | 2m15s | 977.2k | 2.6k | claude-opus-5-5, claude-sonnet-5-5 | drive-implement, drive-slice | yes | driver=cruise |
| implement | 2026-10-06 04:54 | 40m03s | 32.2M | 35.7k | claude-opus-5-5, claude-sonnet-5-5 | drive-implement, drive-slice | yes | driver=cruise, verify_failures=0, delegate=story, cycle=rule, split=0 |
| converge | 2026-10-06 05:34 | 14m06s | 9.8M | 3.2k | claude-opus-5-5 | drive-converge, drive-slice | yes | driver=cruise |
| implement | 2026-10-06 05:48 | 7m17s | 6M | 9.7k | claude-opus-5-5, claude-sonnet-5-5 | drive-implement, drive-slice | yes | driver=cruise, verify_failures=0, delegate=rule, cycle=rule, split=0 |
| converge | 2026-10-06 05:56 | 7m36s | 4.7M | 1.9k | claude-opus-5-5 | drive-converge, drive-slice | yes | driver=cruise |
| implement | 2026-10-06 06:03 | 8m04s | 5.3M | 10.1k | claude-opus-5-5, claude-sonnet-5-5 | drive-implement, drive-slice | yes | driver=cruise, verify_failures=0, delegate=rule, cycle=rule, split=0 |
| gaps | 2026-10-06 07:19 | 11m12s | 27.3M | 24.9k | claude-opus-5-5 | drive-adversary, drive-gaps, drive-skipper, drive-slice | yes | findings=5, driver=cruise |
| implement | 2026-10-06 07:31 | 26m59s | 59.8M | 79.4k | claude-opus-5-5, claude-sonnet-5-5 | drive-implement, drive-skipper, drive-slice, drive-tasks | yes | driver=cruise |
| hand | 2026-10-06 10:46 | 8h51m | 50.1M | 87.1k | claude-opus-5-5, claude-sonnet-5-5 | drive-adversary, drive-hand, drive-implement | yes | outcome=implementation, driver=cruise |
| implement | 2026-10-06 19:38 | 10m02s | 4.2M | 8.3k | claude-opus-5-5, claude-sonnet-5-5 | drive-implement | yes | driver=cruise |
| hand | 2026-10-06 23:16 | 3h23m | 4M | 14k | claude-opus-5-5 | drive-hand | yes | outcome=accepted, driver=cruise |
| gate | 2026-10-07 02:40 | 56m20s | 1.6M | 4.7k | claude-opus-5-5 | — | no | driver=cruise |
| adversary | 2026-10-07 03:39 | 22m00s | 16.9M | 32.9k | claude-opus-5-5 | drive-adversary | yes | findings=13, seams=2, driver=cruise |
| implement | 2026-10-07 04:01 | 18m02s | 9.3M | 25.6k | claude-opus-5-5, claude-sonnet-5-5 | drive-implement | yes | driver=cruise |
| gate | 2026-10-07 04:19 | 1h55m | 2M | 4.9k | claude-opus-5-5 | — | no | driver=cruise |

### S39-benchmark-elapsed — 6h50m

| stage | started (UTC) | wall | in | out | model | agent | delegated | reported |
|---|---|---|---|---|---|---|---|---|
| plan | 2026-10-06 07:18 | 11m19s | 28.4M | 26.7k | claude-opus-5-5 | drive-adversary, drive-gaps, drive-skipper, drive-slice | yes | driver=cruise |
| tasks | 2026-10-06 07:30 | 1m55s | 5.1M | 11.1k | claude-opus-5-5, claude-sonnet-5-5 | drive-implement, drive-skipper, drive-slice, drive-tasks | yes | driver=cruise |
| pin | 2026-10-06 07:32 | 1m13s | 1.7M | 4.4k | claude-opus-5-5, claude-sonnet-5-5 | drive-implement, drive-skipper, drive-slice | yes | driver=cruise |
| implement | 2026-10-06 07:33 | 35m35s | 64.8M | 83.1k | claude-opus-5-5, claude-sonnet-5-5 | drive-implement, drive-skipper, drive-slice | yes | verify_failures=0, delegate=story, cycle=rule, split=0, driver=cruise |
| converge | 2026-10-06 08:09 | 11m51s | 6.7M | 8.3k | claude-opus-5-5 | drive-converge, drive-slice | yes | driver=cruise |
| implement | 2026-10-06 08:21 | 19m08s | 12.2M | 10.5k | claude-opus-5-5, claude-sonnet-5-5 | drive-implement, drive-slice | yes | verify_failures=0, delegate=task, cycle=rule, split=0, driver=cruise |
| converge | 2026-10-06 08:40 | 10m27s | 8.5M | 8.7k | claude-opus-5-5 | drive-converge, drive-slice | yes | driver=cruise |
| implement | 2026-10-06 08:51 | 12m16s | 10.3M | 11.5k | claude-opus-5-5, claude-sonnet-5-5 | drive-implement, drive-slice | yes | verify_failures=0, delegate=task, cycle=rule, split=0, driver=cruise |
| gaps | 2026-10-06 09:04 | 19m02s | 7.9M | 3.9k | claude-opus-5-5 | drive-gaps | yes | findings=10, driver=cruise |
| implement | 2026-10-06 09:23 | 18m47s | 16.7M | 20.4k | claude-opus-5-5, claude-sonnet-5-5 | drive-implement, drive-skipper | yes | driver=cruise |
| demo | 2026-10-06 09:42 | 7m06s | 3.3M | 4k | claude-opus-5-5 | drive-hand | yes | outcome=accepted, driver=cruise |
| adversary | 2026-10-06 10:47 | 11m15s | 10.1M | 13.4k | claude-opus-5-5 | drive-adversary, drive-hand | yes | findings=18, seams=2, driver=cruise |
| implement | 2026-10-06 10:58 | 22m05s | 13.7M | 21.2k | claude-opus-5-5, claude-sonnet-5-5 | drive-hand, drive-implement | yes | driver=cruise |
| hand | 2026-10-06 11:21 | 9m50s | 2.4M | 4.3k | claude-opus-5-5 | drive-hand | yes | outcome=accepted, driver=cruise |
| gate | 2026-10-06 19:37 | 3h38m | 15.8M | 33.8k | claude-opus-5-5, claude-sonnet-5-5 | drive-hand, drive-implement | yes | driver=cruise |

### S43-test-declarations — 17m27s

| stage | started (UTC) | wall | in | out | model | agent | delegated | reported |
|---|---|---|---|---|---|---|---|---|
| gaps | 2026-10-07 06:16 | 17m27s | 10.7M | 14k | claude-opus-5-5 | drive-gaps | yes | gaps=11, driver=cruise |

## Notes

- S03-verify-stamp: converge ran 3 times, appending 15 task(s) — a slice too large, or fixes too narrow to close the class of what they found
- S04-parallel-gate: converge ran 3 times, appending 8 task(s) — a slice too large, or fixes too narrow to close the class of what they found
- S06-scoped-gate: converge ran 5 times, appending 19 task(s) — a slice too large, or fixes too narrow to close the class of what they found
- S01-gate-walks: implemented as story/rule and task/example and task/rule — its wall compares with neither
- S02-runner-bookkeeping: implemented as story/rule and task/example — its wall compares with neither
- S03-verify-stamp: implemented as story/rule and task/rule — its wall compares with neither
- S05-xdist: implemented as story/rule and task/rule — its wall compares with neither
- S06-scoped-gate: implemented as rule/rule and task/rule — its wall compares with neither
- S07-scoped-checks: implemented as drive-implement/? and drive-implement/rule and drive-tasks/? — its wall compares with neither
- S11-render-once: implemented as story/rule and task/rule — its wall compares with neither
- S20-slice-scope-root: implemented as rule/rule and task/example and task/rule — its wall compares with neither
- S21-refresh-keeps-owned-files: implemented as rule/rule and task/rule — its wall compares with neither
- S22-slice-scope-base: implemented as rule/rule and task/rule — its wall compares with neither
- S23-refusal-in-subdirectory: implemented as rule/rule and task/rule — its wall compares with neither
- S24-ci-fetches-slice-base: implemented as rule/rule and task/rule — its wall compares with neither
- S26-reversibility-line: implemented as drive-converge/? and drive-implement/rule and drive-tasks/? — its wall compares with neither
- S33-factory-gate-stamp: implemented as rule/rule and task/rule — its wall compares with neither
- S38-factory-test-selection: implemented as rule/rule and story/rule — its wall compares with neither
- S39-benchmark-elapsed: implemented as story/rule and task/rule — its wall compares with neither
- (feature) ground: cut off — a new `bosun` entry started while it was open; its wall is real, its signals were never reported
- S00-run-path mutation: not bracketed around its work — start and end were called in the same moment, so this stage's wall and tokens are missing, not zero.
- S01-gate-walks gaps: not bracketed around its work — start and end were called in the same moment, so this stage's wall and tokens are missing, not zero.
- S01-gate-walks plan: not bracketed around its work — start and end were called in the same moment, so this stage's wall and tokens are missing, not zero.
- S04-parallel-gate implement: cut off — a new `skipper` entry started while it was open; its wall is real, its signals were never reported
- S06-scoped-gate gaps: not bracketed around its work — start and end were called in the same moment, so this stage's wall and tokens are missing, not zero.
- S06-scoped-gate tasks: cut off — iteration 20 ended with the entry open; its wall is real, its signals were never reported
- S14-result-contract gaps: cut off — a new `skipper` entry started while it was open; its wall is real, its signals were never reported
- S20-slice-scope-root gaps: cut off — a new `skipper` entry started while it was open; its wall is real, its signals were never reported
- S20-slice-scope-root gaps: not bracketed around its work — start and end were called in the same moment, so this stage's wall and tokens are missing, not zero.
- S20-slice-scope-root gaps: not bracketed around its work — start and end were called in the same moment, so this stage's wall and tokens are missing, not zero.
- S27-provisional-decisions demo: not bracketed around its work — start and end were called in the same moment, so this stage's wall and tokens are missing, not zero.
- S33-factory-gate-stamp skipper: cut off — a new `implement` entry started while it was open; its wall is real, its signals were never reported

## Reading these numbers

These numbers compare the slices of this project on this harness, and one slice before and after a change
to a prompt, a skill or the layout. They are tokens, not prices. They do not compare harnesses, whose transcripts
count different things, or projects, whose slices are not the same size — the shape columns normalise, they do not
equate. A stage's tokens are a floor: the turn that closes the entry is still being written when it is read. A
number the script could not read is written as unknown with its reason, never estimated. A stage whose start and end
were called in the same moment is unbracketed: its wall and tokens are missing, not zero, and a slice containing one
shows its measured wall as a floor with a trailing `+`. Host context grows through a session, so otherwise identical
slices spanning different numbers or lengths of sessions are not directly comparable on host tokens.
