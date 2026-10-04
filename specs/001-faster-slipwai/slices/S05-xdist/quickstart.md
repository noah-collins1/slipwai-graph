# Quickstart: S05-xdist

With this checkout's `./slipwai` (the `slipwai` on PATH is older):

```sh
D=$(mktemp -d)
./slipwai generate shop --backend python --output "$D" --no-init --no-install --skip-checks
cd "$D/shop"
grep -n parallelSafe project.json        # line after "target": "parallelSafe": true
make test                                # pytest … -n auto --maxprocesses 4: "created: 4/4 workers" (fewer on fewer cores)
make test-integration                    # never parallel (no -n)
# opt out: change the line to  "parallelSafe": false  — nothing regenerated
make test                                # pytest as before, serial, the same tests passing
cat docs/gates.md                        # the mark: its default, missing is serial, when to set false
```

A project made before this release, then `slipwai migrate`d with this checkout: `project.json` has no
`parallelSafe` and `make test` is serial; adding `"parallelSafe": true,` (with its comma) on the line after `"target"` turns it on.

## Measured at demo 1 (AC-S05-13)

A fresh Python starter (event-modelling, FastAPI, Postgres store, 87 tests), warm, on a branch other than the trunk;
12th Gen Intel i5-12400, `nproc` 12; medians of three (`demo/17-timings.tsv`, `demo/17-measure.sh`):

| Command | Mark `true` (4 workers) | Mark `false` (serial) |
|---|---|---|
| `./scripts/verify --test-only` | 1.36 s | 0.99 s |
| `VERIFY_FORCE=1 make verify` | 3.70 s | 3.30 s |
| `VERIFY_FORCE=1 make -j verify` | 2.11 s | 1.72 s |

D89's criterion holds both ways (the `-j` median below the serial one), so D103's cap stands.
