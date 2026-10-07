# Demo 2 timings — machine noahc-server (12 cores), no CI variable set, one run on the machine at a time; bash `time`, wall clock

Branch `slice/S38-demo2-go` in scratch clone `/tmp/s38/c`, base `be5b646` (the slice's tip). The total is 343
modules: two more than demo 1's 341, from T042–T045's new test modules.

| run | commit | command | selected of total | elapsed | modules failing |
|---|---|---|---|---|---|
| clean-selected | fe5e71b | `time make test SINCE=be5b646` | 336 of 343 (7 skipped, 7 narrowed to go) | 2886.7 s (48m06.7s) | none |
| clean-full | fe5e71b | `time make test FULL=1` | 343 of 343 (full: FULL=1 given) | 3320.0 s (55m20.0s) | none |
| fault-full | 2130852 | `time make test FULL=1` | 343 of 343 (full: FULL=1 given) | 2923.2 s (48m43.2s) | test_add_service test_matrix |
| fault-selected | 2130852 | `time make test SINCE=be5b646` | 336 of 343 (7 skipped, 7 narrowed to go) | 2846.8 s (47m26.8s) | test_add_service test_matrix |

Saving on the clean pair: 433.3 s, 13.1% of the full run. Demo 1's case (a) saved 46 s (1.4%).
On the faulted pair it is 76.4 s (2.6%). The faulted full run is itself 397 s shorter than the clean full run
(2923 s against 3320 s); the logs do not say why, so the clean pair is the figure for the saving.
Tests run: the selected runs execute 2741 + 21 = 2762 tests, the full runs 2838.
