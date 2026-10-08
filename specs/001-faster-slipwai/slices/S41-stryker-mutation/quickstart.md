# Quickstart: S41-stryker-mutation (the demo, AC-S41-14)

Prerequisites: Node ≥ 22 and npm on `PATH`, network for the first `npm ci`, Python 3.11+.

```sh
./slipwai generate demo --backend typescript --output /tmp/s41-demo   # the default answers: Fastify, Postgres
cd /tmp/s41-demo/demo && git checkout -b slice/S1
make mutation                      # nothing changed: "no mutant to run — no production file changed", exit 0
$EDITOR apps/service/src/health.ts # change one production file
time make mutation                 # first line "scoped to 1 changed file(s) since `main` at …", Stryker mutates health.ts only
time make mutation-full            # every file stryker.config.json lists; record the mutant counts
```

Expected, and what to record (wall time, mutant counts, `nproc`, CPU model):

1. The scoped run's report (`apps/service/reports/mutation/mutation.json`) names `src/health.ts` only.
2. `make mutation-full` mutates the config's list (not `main.ts`, `openapi.ts`, the Postgres adapters) and, on the
   default starter, fails naming its survivors (plan, *Handed back* 1).
3. A changed `src/main.ts` alone: *outside Stryker's configured targets*, Stryker not started, exit 0.
4. A types-only file: *no mutant to run*, exit 0. A file named `src/a,b.ts`: refused, exit 2.
5. A changed `apps/web/src/App.tsx`: *browser app — not mutated by this target*, exit 0.
6. `git status --short` is empty after each run (report and sandbox ignored), and `make verify-scoped` afterwards is not
   broadened.
