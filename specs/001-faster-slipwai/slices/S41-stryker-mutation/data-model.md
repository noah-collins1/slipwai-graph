# Data model: S41-stryker-mutation

Nothing is persisted. These are the shapes the wrapper and the scope script read and the words they print.

## `apps/<service>/stryker.config.json` (written by the factory, the project's from then on)

```json
{
  "testRunner": "vitest",
  "vitest": { "configFile": "vitest.config.ts", "related": false },
  "vitest_comment": "...why related is off (a types-only file then reports zero mutants instead of exiting 1)",
  "mutate": ["src/**/*.ts", "!src/main.ts", "!src/openapi.ts", "!src/adapters/driven/event-store-postgres/**"],
  "mutate_comment": "...D213: the entry points and the adapters only tests/integration reaches; add one the same way",
  "reporters": ["clear-text", "json", "html"],
  "incremental": false,
  "cleanTempDir": "always",
  "thresholds": { "high": 80, "low": 60, "break": null },
  "thresholds_comment": "...the verdict is scripts/stryker-mutation.py's (D212); no number here gates anything",
  "tsconfigFile": "stryker-does-not-rewrite-tsconfig.json",
  "tsconfigFile_comment": "...TypeScript 7 has no JavaScript API; the rewrite is for extends/references outside the service"
}
```

The Postgres exclusion is written only where the service's event store is Postgres. Keys ending `_comment` are
Stryker's documented way to annotate a JSON config (`options-validator.js:180`).

**Read by the wrapper's `targets()`**: `mutate` must be a non-empty list of strings; each is a pattern of the subset in
research R3, else `Unreadable("the pattern `<p>` …")`. Absent file → `Unreadable("no stryker.config.json")`.

## `matched(patterns, file) -> bool`

`file` is a path within the service, POSIX. Start unmatched; for each pattern in order, a positive pattern that matches
sets matched, a `!` pattern that matches clears it. Segment rules: literal equal; a segment with `*` → `[^/]*` and not
matching a leading `.` unless the pattern segment starts with `.`; `**` → zero or more segments none starting with `.`.

## `refused(file) -> str | None` (D215 d)

The words where the path within the service contains any of `, * ? { [ !` or ends in `:<digits>`:
`` `<service>/<file>` holds `<char>`, which Stryker's --mutate reads as pattern syntax; rename it, or run `make mutation-full` ``.

## `versions(manifest_text, lock_text)` (R7)

`{"@stryker-mutator/core": "10.0.0", …}` from the manifest's `dependencies` and `devDependencies`, or from a lock's
`packages` entries whose key ends `node_modules/@stryker-mutator/<name>` (`version`). Text that is not a JSON object
raises `Unreadable`.

## The report (`apps/<service>/reports/mutation/mutation.json`, schema 1.0)

`files: {<path within service>: {mutants: [{id, mutatorName, replacement, status, location: {start: {line, column}}}]}}`.

| Status | Verdict |
|---|---|
| `Killed`, `Ignored` | pass |
| `NoCoverage` | counted, never failed |
| `Survived`, `Timeout`, `RuntimeError`, `CompileError`, `Pending`, anything else | fail |

## The wrapper's lines and status (`scripts/stryker-mutation.py <service> [--file <path> …]`)

| Situation | Line(s) (prefix `mutation: `) | Exit |
|---|---|---|
| a `--file` the list does not match | `not mutated <service>/<file> — outside Stryker's configured targets` | — |
| no `--file` left | `nothing under <service> that was given is a file Stryker would mutate; no mutant to run` | 0 |
| a refused path | the refusal words | 2 |
| unreadable config | `<service>/stryker.config.json: <why>` | 2 |
| no `npm` | `npm is not on PATH; install Node <.nvmrc> to run Stryker` | 2 |
| Stryker missing | `Stryker is not installed in this project: add @stryker-mutator/core and @stryker-mutator/vitest-runner <ver> to <service>/package.json's devDependencies and run npm install` | 2 |
| install | `installing from the committed lock (npm ci)` | — |
| scoped | `scoped to <n> given file(s): <files>` | — |
| no readable report | `Stryker exited <code> and left no readable report at <path>; that is not a pass` | 1 |
| scoped, zero mutants | `no mutant to run — <files>: Stryker found no mutant in them (types or comments only)` | 0 |
| sweep, zero mutants | `Stryker found nothing to mutate in <service>; a pass on nothing is not a pass` | 1 |
| each failing mutant | `<status> <service>/<file>:<line>:<column> <mutator> → <replacement> (report <path>)` | — |
| last line | `<n> mutants: <k> killed, <i> ignored, <u> not covered (reported, never failed)[, <s> survived, <t> timed out, …]; <passed|failed> — report <path>` | 0/1 |

## What sweeps a TypeScript service (added to `sweep_causes`)

| Changed path | Sweeps |
|---|---|
| `<service>/stryker.config.json` | that service |
| `scripts/stryker-mutation.py` | every TypeScript service |
| `<service>/package.json` whose `@stryker-mutator/*` versions differ (either side unparseable counts) | that service |
| `package-lock.json` at the project root whose `@stryker-mutator/*` versions differ | every TypeScript service |
| a file git ignores under `<service>/src/` | that service (`unlisted`, via `PRODUCTION_ROOT`) |
| a config whose list cannot be read | that service (`Plan.unreadable`) |

## The scope script's new lines

- `not mutated <path> — browser app, not mutated by this target` (a path under a `kind: web` deployable in
  `project.json`), alongside S08's `packages/` line.
- `refuse <service> — <refusal words>` from `Plan.refusal`, status 2, no tool started (dry run: *would fail*).
