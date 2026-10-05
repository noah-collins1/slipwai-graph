# Quickstart: S06-scoped-gate

With this checkout's `./slipwai` (the `slipwai` on PATH is older), on a two-deployable starter: a TypeScript service
with Fastify and the React web app whose `api` names it.

```sh
D=$(mktemp -d)
./slipwai generate shop --profile event-modelling --language typescript --http fastify --frontend react-vite \
  --output "$D" --no-init --no-install --skip-checks
cd "$D/shop"
make install                         # npm ci, so the first gate's pass is recorded (gates page)

make verify-scoped                   # on main: "verify-scoped: the full gate runs, as `make verify` — this is the trunk (`main`)"
git switch -c slice/S1
make verify-scoped                   # "no usable baseline (none yet on this branch) …", then the full gate as make verify,
                                     # which records the stamp and the baseline
make verify-scoped                   # the stamp's reuse line, exit 0, nothing run

printf '// scoped\n' >> apps/web/src/App.tsx
make verify-scoped                   # run lint-web, typecheck-web, test-web, check-imports, check-migrations, check-model,
                                     # check-styles, check-ux-gates (each "apps/web/src/App.tsx changed"), and check-python,
                                     # check-slice-scope, check-codegraph, check-agents, check-speckit, check-extensions,
                                     # check-constitution (their own reasons);
                                     # skip lint-service, typecheck-service, test-service, check-openapi, check-drawio,
                                     # check-benchmark, check-decisions — "none of its inputs changed";
                                     # last line: "N run, M skipped, compared with `main` at <sha>; passed"
make -j verify-scoped                # the same choice, the chosen checks at once
python3 scripts/verify-scoped.py record | head -40   # the record as JSON (schema 1)

git checkout apps/web/src/App.tsx
printf '// scoped\n' >> apps/service/src/main.ts
make verify-scoped                   # service's three, check-openapi, and typecheck-web, test-web
                                     # ("consumes openapi:service (apps/service/src/main.ts)"); lint-web skipped

printf 'note\n' >> README.md
make verify-scoped                   # "dependency knowledge was incomplete for README.md — no deployable, contract or
                                     # check claims it", then the full gate, which fails at check-slice-scope
                                     # ("README.md: outside every deployable") and removes the baseline
git checkout README.md apps/service/src/main.ts
make verify                          # green again on the restored tree: writes the baseline anew

UX_GATES_SINCE=main make verify-scoped   # check-ux-gates runs: "UX_GATES_SINCE differs from the baseline"
```

An obligation: add to `project.json` on `main` (a change on the branch would run the full gate),

```json
"verification": { "obligations": [
  { "name": "app-and-api", "components": ["service", "web"], "checks": ["test-service", "test-web"] } ] }
```

commit it, rebase `slice/S1`, change only `apps/web/src/App.tsx`: `test-service` now runs, *obligation `app-and-api`*.
Write `"checks": ["test-nope"]` instead and the run names the entry and runs the full gate.

An adopted repository (a fixture from `make test-adoption`, or any repository after `slipwai adopt`):
`make -f delivery/Makefile verify-scoped` says *this layout has no verification-dependency record yet* and runs its
full gate.

A project made at the last release, then `slipwai migrate`d with this checkout: `make help` lists `verify-scoped`,
`project.json` has no `verification` key, and `docs/gates.md` carries the scoped gate's paragraph.

## Measured at the demo (AC-S06-19)

On `slice/S1` with only `apps/web/src/App.tsx` changed: `make verify-scoped` three times (no stamp is written by a
scoped run, so each is a scoped run), then `VERIFY_FORCE=1 make verify` three times on the same tree (that run
writes the stamp — measure it last). Record the medians, the commands, the CPU model and `nproc` here and in
`changelog.d/scoped-gate.md`. At the merge root, `make verify` on a Python starter still runs pytest with
`-n auto --maxprocesses 4` (S05).

| Command | Median | Machine |
|---|---|---|
| `make verify-scoped` | 4.298 s (4.300, 4.275, 4.298) | 12th Gen Intel Core i5-12400, `nproc` 12 |
| `VERIFY_FORCE=1 make verify` | 7.596 s (7.645, 7.596, 7.591) | the same |

Taken by `drive-hand` at the demo of iteration 23 (`demo/35-measurement.txt`), `main` at 6d681b7 of the generated
project. `make -j verify-scoped` took 2.93 s once.
