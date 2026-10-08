# 0009. Stryker, with its Vitest runner, in every generated TypeScript service

Date: 2026-10-08

## Status

Proposed

Drafted by `/cruise` iteration 29 of `001-faster-slipwai`, at the plan stage of `S41-stryker-mutation` (decisions D137,
D212, D213 and D215 in `specs/001-faster-slipwai/decisions.md`; research in
`specs/001-faster-slipwai/slices/S41-stryker-mutation/research.md`). The run never accepts its own architecture
decision; the word `Accepted` here is a person's.

## Context

FR-008 asks `make mutation` to run the changed module's mutants for every backend whose mutation tool is wired, and
D137 left TypeScript — the catalog's default backend — as a placeholder that exits 2 until a slice wired a tool. There
is no standard-library mutation tester for TypeScript; Stryker is the ecosystem's, and the factory's own
mutation-testing skill already names it as the entry point for JavaScript and TypeScript. A dependency added here lands
in every TypeScript project the factory makes and in all twelve committed TypeScript locks, so removing or replacing it
later is a relock and a `migrate` note in every such project.

Two facts about the starter shape the choice. It pins Vitest 4.1.11, which `@stryker-mutator/vitest-runner` 10.0.0
supports (`vitest >=2.0.0`), giving per-test coverage so each mutant runs only the tests that reach it. And it pins
TypeScript 7.0.2, the native compiler, which ships no JavaScript compiler API: Stryker's sandbox preprocessor calls
`ts.parseConfigFileTextToJson` and the TypeScript checker plugin calls the compiler host, and both fail at start under
it (research R1, R2).

## Decision

Every generated TypeScript service carries `@stryker-mutator/core` 10.0.0 and `@stryker-mutator/vitest-runner` 10.0.0
as exact development dependencies, installed only from the committed lock and started with `npm exec --no`, so a run
never fetches a release nobody chose. No type-checker plugin: it cannot run under TypeScript 7. The service's checked-in
`stryker.config.json` points `tsconfigFile` at a file that does not exist, which keeps Stryker's tsconfig rewrite —
needed only for `extends` or `references` that leave the service — from loading TypeScript, and sets Vitest's
`related` mode off so a file with no mutants yields a report rather than an exit 1. The verdict is not Stryker's:
`thresholds.break` is `null`, and `scripts/stryker-mutation.py` reads `mutation.json` and fails on every status but
killed, ignored and uncovered (D212).

## Consequences

`npm ci` installs about 160 more packages in every TypeScript project (3.1 s against 2.5 s warm on the reference
machine), and `npm audit --audit-level=critical` covers them; Renovate keeps them current, each major as its own item.
A project whose tsconfig later gains an `extends` or `references` outside the service will see the initial test run
fail inside Stryker's sandbox until it sets `tsconfigFile` back — a red run, never a silent one — and the day
TypeScript publishes a JavaScript API again, or Stryker stops needing one, the redirect and the absent checker are
both revisited. Replacing Stryker would mean a new wrapper, a relock of every TypeScript service and a `migrate` note:
this record is why.
