# Demo log: S41-stryker-mutation

## 2026-10-08T09:11:08Z — implementation · iteration 29 · drive-hand (claude-opus-5-5)
- **Started with:** `./slipwai generate demo --backend typescript --output /tmp/cruise29/s41-demo` from the worktree at `b80c219`, then `cd /tmp/cruise29/s41-demo/demo && git checkout -b slice/S1`, then quickstart scenarios 1–6 with `make mutation`, `make mutation-full`, `make verify-scoped`, `make verify`. Minimal starter: `./slipwai generate minimal --backend typescript --profile standard --event-store memory --http none --frontend none --output /tmp/cruise29/s41-demo`. D217's check ran against a scratch copy (`cp -a demo scratch`), with `npx --no vitest run` in `apps/service`. · **Seeded:** none
- **Driven through:** CLI. `.specify/cruise.json`'s `hand` is `browser`, but the slice has no screen and no HTTP surface. It is a make target, so the browser and HTTP rungs were skipped.
- **Examples:**
  - Nothing changed on `slice/S1`: passed. *no mutant to run — no production file changed*, exit 0.
  - Q1, `health.ts` changed: passed. The first line was *scoped to 1 changed file(s) since `main` at 7287334: apps/service/src/health.ts*. Stryker found 1 of 37 files and 3 mutants, all 3 killed. The report names only `src/health.ts` and the exit is 0.
  - Q2, `make mutation-full`: passed as the criterion is written. It mutated 10 of 37 files, nine of which hold mutants: the list without `main.ts`, `openapi.ts` and the Postgres adapter. Result: 519 mutants, 415 killed, 13 not covered, 90 survived, 1 timeout. The run was red, exit 2, and named every survivor.
  - Q3, only `main.ts` changed: passed. *not mutated apps/service/src/main.ts — outside Stryker's configured targets*. Stryker did not start, no report was written, exit 0.
  - Q4, a new types-only port (`ports/notifier.ts`): passed, both untracked and committed. *no mutant to run … (types or comments only)*, exit 0.
  - Q4, a comment edit to the starter's own port `ports/read-models.ts`: failed. Expected *no mutant to run*, exit 0 (AC-S41-3: "a matched file with no mutant (a types-only port)"). Instead it said *Stryker found no mutant in … read-models.ts, which holds code it could mutate; that is not a pass*, exit 2. Stryker instrumented 0 mutants there. The only statement that is not a type is `export const FROM_THE_BEGINNING = 0;`, and Stryker 10 has no numeric-literal mutator. The developer has no remedy: no test and no disable comment can make that run green.
  - Q4, `src/a,b.ts`: passed. Refused in one line that names `,` and offers rename or `make mutation-full`, exit 2.
  - Q5, `apps/web/src/App.tsx`: passed. *not mutated apps/web/src/App.tsx — browser app, not mutated by this target*, exit 0.
  - Q6: passed. `git status --short` showed only the actor's own edit after every run; the report is `!!` (ignored). After a recorded `verify-scoped`, a `make mutation` run left `verify-scoped` and `verify` both reusing the stamp in 0.4 s, so the gate was not broadened.
  - D217a: passed in part. The default sweep is red, and at least one named survivor is real and not equivalent: `tracing.ts:91:7 ConditionalExpression → true` survives with Vitest run directly (all 86 tests green). However, D217's own example, `tracing.ts:91:7 EqualityOperator → endpoint !== undefined`, is not a real survivor (see D217c).
  - D217b: passed. The minimal starter's `make mutation-full` is green: 3 mutants, 3 killed, exit 0, 4.38 s.
  - D217c: failed, and D217's *Would reverse if* is met. With `endpoint !== undefined` applied by hand, Vitest run directly is red: `tracing.test.ts`'s `beforeAll` throws (`Cannot read properties of undefined (reading 'replace')`), so 1 file fails and 5 tests are skipped, exit 1. All 91 failing mutants were then replayed by hand, one at a time:
    - 85 stay green. They are real survivors.
    - 1 is the timeout, which also hangs Vitest directly.
    - 5 are reported Survived by Stryker but turn the suite red: `tracing.ts:81:5` ConditionalExpression→false, `tracing.ts:81:5` EqualityOperator `!== ''`, `tracing.ts:81:44` StringLiteral, `tracing.ts:91:7` ConditionalExpression→false, and `tracing.ts:91:7` EqualityOperator `!== undefined`.

    All five are `static: true`, with `testsCompleted: 81` against the dry run's 86. The hook threw, Vitest skipped the file's tests, and Stryker read "no test failed" as Survived. The wrapper takes that status as given, so its red is partly a Stryker/runner defect.
  - AC-S41-14: measured on `nproc` 12, 12th Gen Intel i5-12400.
    - `make mutation` with one file changed: 4.46 s on a warm tree, or 7.86 s on the first run including `npm ci`. 3 mutants.
    - `make mutation-full`: 49.33 s, 519 mutants.
    - About 11× faster. A scoped run's fixed cost is about 4 s: Stryker starting plus the 86-test dry run.
- **Evidence:** `demo/q0-nothing-changed.txt`, `demo/q1-health-scoped.txt`, `demo/q1-health-scoped-run2.txt`, `demo/q2-default-mutation-full.txt`, `demo/q2-default-mutation-full-files.txt`, `demo/q3-main-outside-targets.txt`, `demo/q4a-types-only.txt`, `demo/q4b-types-only-new-port.txt`, `demo/q4c-comma-path.txt`, `demo/q4d-starter-port-with-const.txt`, `demo/q5-browser-app.txt`, `demo/q6-clean-tree-verify-scoped.txt`, `demo/q6b-verify-after-mutation.txt`, `demo/d217b-minimal-mutation-full.txt`, `demo/d217c-survivor-by-hand.txt`, `demo/d217c-replay-all-survivors.txt`, `demo/d217c-report-excerpt-tracing.json`, `demo/ac-s41-14-measurement.txt`
- **Feedback:** Two tasks re-enter S41's implementation, in the wrapper `assets/languages/typescript/scripts/stryker-mutation.py`:
  - (1) **D217 reversal.** D217 says S41 does not converge until this is fixed. A `Survived` mutant whose `testsCompleted` is below the dry run's test count shows that the suite did not run to completion under it: a hook threw and tests were skipped. The wrapper must not report such a mutant as a survivor. Reproduction: `demo/d217c-survivor-by-hand.txt` and `demo/d217c-report-excerpt-tracing.json`. The Makefile note, the fragment and D217's example (`endpoint === undefined`) need re-checking once that is fixed. The real survivor on the same line is `ConditionalExpression → true`.
  - (2) **AC-S41-3, the T026 overreach.** `holds_code` treats `export const X = 0` as code Stryker could mutate. A scoped run on the starter's own `read-models.ts` is therefore permanently red, exit 2, with a claim that is false. Reproduction: `demo/q4d-starter-port-with-const.txt`.

  Notes for the next slice:
  - `npm ci` reports 9 vulnerabilities (7 high) in the default starter's lock.
  - On a browser-only change, the first line says *no production file changed* even though `App.tsx` is production code; the next line names it correctly.
  - The quickstart's comment "the default answers: Fastify, Postgres" holds, but `generate --help` prints `--event-store` default `memory` and `--http` default `none`, which reads as a contradiction.
