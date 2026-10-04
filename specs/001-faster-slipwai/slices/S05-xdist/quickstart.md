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
`parallelSafe` and `make test` is serial; adding `"parallelSafe": true,` on the line after `"target"` turns it on.

The measurement (AC-S05-13) is written here by the demo.
