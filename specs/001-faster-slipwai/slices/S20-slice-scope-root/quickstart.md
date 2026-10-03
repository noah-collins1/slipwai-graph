# Quickstart — S20-slice-scope-root

What proves the slice, run from this checkout (`FACTORY=$(pwd)`). No seed data, no service, no port.

## 1. A slice branch in a repository adopted at its root

```sh
FACTORY=$(pwd); T=$(mktemp -d); cp -r tests/fixtures/adopt/python-worker "$T/repo"; cd "$T/repo"
git init -q -b main && git add -A && git -c user.name=t -c user.email=t@local commit -q -m theirs
"$FACTORY/slipwai" adopt --yes
git add -A && git -c user.name=t -c user.email=t@local commit -q -m adopted
git checkout -q -b slice/S1
echo "# a slice's test" >> tests/test_scope_demo.py
make -f delivery/Makefile check-slice-scope
```

Expect: exit 0 and `check-slice-scope: slice/S1 touches only what one slice may`. (Before the slice: exit 1,
`tests/test_scope_demo.py: outside every deployable`.)

```sh
echo "x:" >> Makefile; make -f delivery/Makefile check-slice-scope; git checkout -- Makefile 2>/dev/null || rm Makefile
```

Expect: exit non-zero, `Makefile: outside every deployable … Land it on `main` before the fan-out`. The same
for `project.json`, `delivery/scripts/ratchet.py`, `.specify/drive.json`; `delivery/survey/pinned.md` is green.

## 2. A project with deployables under `apps/`

`python3 -m unittest tests.test_parallel_slices.SliceScopeGateTest` — green, with the test file unchanged.

## 3. A register id with a slug

In the repository from step 1, on `main`: a register row `` | `S00-run-path` | 2026-10-03 | `` under
`specs/f/slices/README.md` and an adversary log headed `## S00-run-path · abc · 2026-10-03` —
`make -f delivery/Makefile check-decisions` passes; headed `## S00 · …` it passes; with neither it fails naming
`S00-run-path`. `make -f delivery/Makefile check-benchmark` warns of `slices/S00-run-path` only where neither
`slices/S00-run-path/benchmark.json` nor `slices/S00/benchmark.json` exists.

## 4. The gates

`make verify` and `make -f delivery/Makefile verify` in this checkout — both green.
