# Quickstart: S38-factory-test-selection

Once `s38.patch` is applied and committed on `slice/S38-factory-test-selection`, with no CI variable set. Until
`adopt-method` merges into `main`, a slice branch here names its base: `SINCE=adopt-method` (D156 point 6).

```sh
python3 -B scripts/select-tests.py --dry-run                          # on this branch, no SINCE: full — the trunk's diff holds the Makefile
SINCE=adopt-method python3 -B scripts/select-tests.py --dry-run       # the SINCE line, every skip with its reason, the summary
make test SINCE=adopt-method                                          # the same selection, then the selected modules run
make test SINCE=adopt-method FULL=1                                   # every module
make test SKIP=test_matrix                                            # selection off: SKIP given — as before
git switch adopt-method && python3 -B scripts/select-tests.py --dry-run   # full: not a slice branch (`adopt-method`)
```

## The demo (AC-S38-15, AC-S38-16 — D157)

Run on one machine, recording its name, the commit and each elapsed time in `demo-log.md`.

1. **Replays.** Four ranges, each run as `python3 -B scripts/select-tests.py --dry-run --replay <range>` and copied as
   printed: modules selected of the total, backends narrowed, the base, one reason per skipped module. A replay that
   runs everything prints its `full:` line and then `selected N of N modules against <base>`; that is recorded as
   printed, a full selection included (D165). S06 and S33 landed on `adopt-method`'s main line with no merge commit,
   S08 and S14 as merge commits:

   | Slice | Range |
   |---|---|
   | S06 | `51c6de4..45ebedb` |
   | S33 | `1e8f880..e82bb06` (its register row's *Merged as* range, ending at its done commit) |
   | S08 | `3138416^1..3138416` |
   | S14 | `37cdf3f^1..37cdf3f` (merged since the plan) |

   The `SINCE=adopt-method` line above is read on a tree whose `Makefile` matches its base: where `adopt-method`'s
   `Makefile` lacks `s38.patch`, the diff holds the `Makefile` and the run is full.
2. **Two timed cases, each on a throwaway `slice/` branch off this one**, in a scratch clone under `/tmp/s38/`:
   (a) one line changed under `assets/languages/go/`; (b) one line changed in a script under
   `assets/toolkit/scripts/` that a declared module loads by path. For each: `time make test SINCE=<this branch's tip>`,
   then `time make test FULL=1` on the same commit; record both, the machine, the commit and *selected of total*.
3. **Soundness.** On each of the two cases, inject a fault that breaks the changed file's behaviour, then run the full
   suite and the selected run on that tree. The full run must fail at least one module (else the fault does not
   count), and every module that fails in the full run must fail in the selected run.
4. Say which part of each figure, if any, belongs to S39's elapsed-time measures.

No criterion requires a minimum saving.
