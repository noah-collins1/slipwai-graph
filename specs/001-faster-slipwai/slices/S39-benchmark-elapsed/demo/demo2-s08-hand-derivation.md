# Demo 2: S08 derived by hand (iteration 25, clone of adopt-method at 75bd48c)

Moments, from the quickstart's `first`/`row` shell functions run in the clone:

| moment | commit | instant (UTC) |
|---|---|---|
| added to the split | d3a0926 | 2026-10-03T02:34:09Z |
| ready (S04's register row) | b31c864 | 2026-10-04T18:13:05Z |
| demo accepted (last demo bracket's end) | — | 2026-10-06T00:31:54Z |
| S06 lands (S06's register row) | 1d6cc17 | 2026-10-06T03:13:46Z |
| merged (the only merge naming S08: `Merge slice/S08-scoped-mutation into adopt-method in split order`) | 3138416 | 2026-10-06T03:14:44Z |
| accepted (S08's register row) | c88fe2f | 2026-10-06T07:16:58Z |

Brackets: 17 entries in `slices/S08-scoped-mutation/benchmark.json`, all ended, Σ seconds 31 439, none overlapping.

Parks (cruise-log rows ending `cruise: stopped: human`, ended → next row's start, clipped to [ready, accepted],
less S08 brackets): iteration 13 2 513 s, 14 4 972 s, 17 5 127 s, 18 5 099 s, 20 2 611 s = 20 322 s.

| part | by hand (s) | script `--json` (s) |
|---|---|---|
| elapsed | 133 433 | 133 433 |
| worked = stage time | 31 439 | 31 439 |
| integration (03:14:44Z→07:16:58Z less adversary 1 002, implement 2 537) | 10 995 | 10 995 |
| dependency (00:31:54Z→03:13:46Z less S08 implement 00:35–01:11, 2 174) | 7 538 | 7 538 |
| review | 0 | 0 |
| a person held the run (in unattributed) | 20 322 | 20 322 |
| worker = elapsed − the rest | 63 139 | 63 139 |
| unattributed | 20 322 | 20 322 |

Sum 31 439 + 10 995 + 7 538 + 0 + 63 139 + 20 322 = 133 433: equal to elapsed. Unchanged from demo 1.

Every record with a number sums to its elapsed (16 records, 0 mismatches); S14 now has numbers (accepted
2026-10-06T10:44:48Z, merged 37cdf3f matched as `slice/S14-result-contract`), S39 alone reads open.

The 17:17:50Z implement: tokens 50 725 980 (demo 1: 50 537 230), delegates exactly
`S08 US2 implement T002-T009` and `drive-slice S08-scoped-mutation`; the recorded `in` for that row is unchanged.
