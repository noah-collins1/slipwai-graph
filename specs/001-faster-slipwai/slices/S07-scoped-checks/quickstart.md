# Quickstart: seeing S07 work

Run from this checkout; the scratch directory is the run's own (`/home/noahc/math/.cruise27/`), cleared afterwards.

## 1. The record names the four

```sh
./slipwai generate s07demo --output /home/noahc/math/.cruise27/s07demo --frontend react-vite --no-init --no-install --skip-checks
cd /home/noahc/math/.cruise27/s07demo
python3 -B scripts/verify-scoped.py record | python3 -c 'import json,sys; c=json.load(sys.stdin)["checks"]; [print(n, c[n]["inputs"] is not None, c[n]["claims"]) for n in ("check-agents","check-speckit","check-extensions","check-constitution")]'
```

Expected: each `True True` ([data-model.md](data-model.md#the-four-rows-verify_scopedtablepy)).

## 2. SC-009 on a slice branch (AC-S07-1)

In a generated TypeScript service + web project with a baseline on `slice/S1` (a green `make verify` there first), edit
`apps/service/src/<file>` and run `make verify-scoped`. Expected: `skip check-agents — none of its inputs changed`, and
the same for `check-speckit`, `check-extensions`, `check-constitution` and `check-ux-gates`. Edit `apps/web/src/<file>`
instead: `run  check-ux-gates — apps/web/src/<file> changed`, and the check's own line naming the base, its file gate,
and no preview rendered.

## 3. The default and its way back (AC-S07-11)

With the ux-gates extension adopted and previews under `apps/web/screens/`:

- on `main`: `make check-ux-gates` prints `check-ux-gates: every preview in scope — this is the trunk (`main`)`;
- on `slice/S1`: `… — previews scoped to what changed since <short> …; UX_GATES_SINCE=all renders every preview`;
- `UX_GATES_SINCE=all make check-ux-gates`: `check-ux-gates: UX_GATES_SINCE=all — every preview in scope`;
- `CI=1 make check-ux-gates` on `slice/S1`: `… every preview in scope — CI is set, so this is a CI run`.

## 4. Tests that hold it

After the host releases the machine, only the touched modules:

```sh
make test TESTS="test_verify_scoped_methods test_verify_scoped_derived test_verify_scoped_held test_verify_scoped_table_held test_verify_scoped_record test_ux_gates_default test_ux_gates_scale"
make test TESTS="test_verify_scoped_choose test_verify_scoped_borders test_verify_scoped_ignored test_verify_scoped_baseline test_scoped_targets"
make test TESTS="test_toolkit test_utf8_io test_changelog test_assets_bytecode test_verify_stamp_scan"
```
