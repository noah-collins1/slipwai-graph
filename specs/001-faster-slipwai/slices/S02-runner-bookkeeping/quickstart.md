# Quickstart: S02-runner-bookkeeping — the demo

Run from this checkout. Everything is written under a scratch directory; nothing here changes.

```sh
D=$(mktemp -d) && ./slipwai generate shop --profile event-modelling --backend python --frontend none \
  --output "$D" --skip-checks --no-init --no-install && cd "$D/shop" && git init -q && git add -A && git commit -qm start
```

1. **The log.** Enable the run (`python3 scripts/agents/cruise.py --set enabled=true`), write a 50-entry
   `specs/cruise-log.jsonl`, and run two iterations against a stand-in harness
   (`python3 scripts/agents/cruise.py --set max_iterations=2`, then
   `CRUISE_HARNESS_COMMAND='echo "cruise: continue"' python3 scripts/agents/cruise.py run --no-park` — the budget
   is a setting, not a flag of `run`; corrected after the demo, where the step as first written parked and waited). Entries 51 and 52 follow; 51's
   `bookkeeping.log_bytes` is the 50-entry file's size and 52's is `0`.
2. **The fingerprint.** In the same run both entries carry the same `fingerprint`; `touch specs/*/spec.md` between
   two runs does not change it; editing a byte does.
3. **The controls.** A stand-in harness that appends a line to `scripts/check-imports.py` parks the run naming
   `scripts/check-imports.py (modified)`; one that rewrites it in place at the same size and restores its
   modification time parks the same way.
4. **`Scope:`.** Write a `specs/demo/decisions.md` with three entries — one `Scope: S02`, one `Scope: global`,
   one naming another slice — and one with no line. `python3 scripts/check-decisions.py --scope S02` prints the
   first two and the unscoped one, then a line of counts; `make check-decisions` passes; an entry with an empty
   `- **Scope:**` makes it fail naming the entry.
5. **The writers.** `commands/cruise.md` shows the `Scope:` line in the entry's shape; `agents/drive-skipper.md`
   points at the verb.
6. **The index** (with `codegraph` on `PATH`, or the tests' stand-in from `tests/test_code_index_health.py`):
   `./init --extension codegraph`, commit, `python3 scripts/agents/code_index.py health` twice — the second says
   it hashed 0 of N and compared only what changed; `CI=true` makes it compare everything.

Expected: the second iteration reads nothing it already read, a gate edit still parks the run, and a slice's
question is handed the decisions that bind it.
