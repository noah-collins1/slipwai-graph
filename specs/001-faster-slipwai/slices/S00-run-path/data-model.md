# Data model — S00-run-path

The slice stores no application data. Its entities are records the method keeps, each with one owner, and the
one state transition the slice makes.

## Run-path record (`delivery/survey/running.md`, section `## . (python)`)

| Field | Value for this slice | Source |
|---|---|---|
| command | `./slipwai --version` | `project.json` `deployables.slipwai-graph.commands.smoke` |
| printed | `slipwai <VERSION>` — one line, exit 0 | the run (AC-S00-1) |
| interpreter | the `python3 --version` the run used; floor `>=3.11` | `pyproject.toml` line 16; D4 |
| port, seed, backing service | none | the command reads `VERSION` and prints; nothing listens |
| cannot run on | not tested — recorded as such, never guessed | `running.md` header: record what was proven |
| proved by, date | cruise iteration 2, 2026-10-03 | the section's own rule |

Validation: the words *Not yet proven* are absent from the section (AC-S00-2). The file is the repository's own:
`slipwai migrate` and `/survey` never rewrite it.

## Gate evidence (recorded in `tasks.md` under `## Convergence`, and summarised in the convergence row)

| Field | Meaning |
|---|---|
| command | `make verify` or `make -f delivery/Makefile verify` |
| commit | the commit the gate ran on |
| environment | `CRUISE_RUNNER=1`, `CRUISE_ITERATION=2` present (AC-S00-5) |
| exit | 0 |
| summary | the unittest `Ran N tests … OK (skipped=K)` line; `K` no higher than the pre-slice baseline |
| ratchet | silent: a command that exits 0 with no prior entry prints nothing and writes nothing (`delivery/scripts/ratchet.py:205–212`), so a clean first run leaves no `delivery/baseline.json`; a `QUARANTINED` line or a `test` entry in that file would be the failure |

## Convergence row (`project.json` `convergence[]`, axis `safety-net`)

| Field | Before | After (AC-S00-6, D11) |
|---|---|---|
| rung | `tests-exist` | `tests-pass` |
| target | `mutation-measured` | unchanged |
| evidence | `test recorded for slipwai-graph` | the two commands, the commit, *established by cruise iteration 2; no person has read the gate* |
| provenance | `detected` | `confirmed` |
| planned | null | null |

Transition rule: `tests-exist → tests-pass` is made only after both gate-evidence rows above exist with exit 0.
`check-convergence` contradicts `tests-pass` when `delivery/baseline.json` records a `test` quarantine
(`src/slipwai/project/ground_command.py:36`) — **but only when that file exists**
(`delivery/scripts/check-convergence.py:98`, `if BASELINE.is_file():`). After a clean first run there is no file,
so the guard is latent: the row rests on the recorded gate evidence above until a baseline is ever written (D14).
`delivery/docs/convergence.md` is derived from this row by `/survey` and is never edited by hand.

## Ratchet baseline (`delivery/baseline.json` — not written by this slice)

`{ "slipwai-graph": { "<target>": { "exit": <int>, "findings": [<string>] } } }` per target the ratchet runs
(`lint`, `typecheck`, `test`). Rule (`delivery/scripts/ratchet.py` lines 27–35, 205–212, 215–245): a command that
exits 0 with no prior entry records nothing; findings on a first run are recorded and committed; a red `test`
with no entry stops the run and records nothing; `make -f delivery/Makefile ratchet-tighten` is the only thing
that records a quarantine, and this slice never runs it. Observed (T003): every ratcheted command was clean, so
the file does not exist after this slice.

## Test child environment (the test fix)

`child_env = {k: v for k, v in os.environ.items() if k not in ("CRUISE_RUNNER", "CRUISE_ITERATION")} | overrides`

Invariant: a test that spawns `scripts/agents/cruise.py` — or drives it in-process — never lets the child see
the runner's two marks unless the test sets them itself (AC-S00-3, AC-S00-4). Precedent: `hook()` in
`tests/test_cruise_stop_hook.py:28–31`.
