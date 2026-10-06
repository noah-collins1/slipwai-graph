# Data model: S14-result-contract

Schema 1 is D134's and ADR 0006's; this page spells what the plan's rules read and print. Nothing here adds a field.

## The block (schema 1)

One JSON object inside a fence whose info string is exactly `result-contract`:

````markdown
```result-contract
{"contract": 1, "delegate": "drive-gaps", "scope": "S14-result-contract converge pass 1", "status": "gaps",
 "contracts_changed": [], "invariants_checked": ["AC-S14-16 bytes"], "tests": ["make test TESTS=test_x: 12 passed"],
 "decisions": ["D134"], "assumptions": [], "unresolved": [], "change_summary": "Read the diff; two gaps.",
 "files_changed": [], "difficulty_observed": {"score": 2, "reason": "one module, clear criteria"}}
```
````

| Field | JSON type | Rule (a fault names the field) |
|---|---|---|
| `contract` | integer, not boolean | `1`. Greater than 1: passed with a note, no field held. Anything else: a fault |
| `delegate` | string | one of the ten types below, and equal to the heading's type |
| `scope` | string | non-empty |
| `status` | string | in the set for `delegate` |
| `contracts_changed` | list of strings | may be empty |
| `invariants_checked` | list of strings | may be empty |
| `tests` | list of strings | may be empty |
| `decisions` | list of strings | each `^D[0-9]+$` and a `## D<n> — ` heading in the feature's `decisions.md` |
| `assumptions` | list of strings | may be empty |
| `unresolved` | list of strings | may be empty |
| `change_summary` | string | non-empty |
| `files_changed` | list of strings | repository-relative: no leading `/` or `\`, no `X:` drive, no `..` segment; may be empty |
| `difficulty_observed` | object | exactly `score` (integer 1–5, not boolean) and `reason` (non-empty string) |

Keys outside these thirteen are ignored (constitution VIII).

### Status, per type (D134 §3)

| Type | Allowed |
|---|---|
| `drive-gaps` | `gaps`, `none` |
| `drive-skipper` | `decided`, `unavailable` |
| `drive-adversary` | `broken`, `held` |
| `drive-bosun` | `unblocked`, `cannot`, `catastrophic` |
| `drive-converge` | `converged`, `not-converged`, `incomplete` |
| `drive-hand` | `accepted`, `behaviour`, `implementation` |
| `drive-implement` | `green`, `partial`, `stopped` |
| `drive-mutation` | `scored`, `failed-run` |
| `drive-slice` | `converged`, `stopped` |
| `drive-tasks` | `written`, `contradiction` |

## The record — `hand-backs.md`

`specs/<feature>/slices/<id>/hand-backs.md` for a slice's stages; `specs/<feature>/hand-backs.md` for feature-level
stages (the split, the ready set's `drive-slice` delegates, the completion audit). Append-only.

```text
record   := preamble entry*
preamble := any lines before the first line starting "## "      (the verb writes "# Hand-backs — <id>")
entry    := heading body
heading  := "## " TIME " — " TYPE " — " STAGE
TIME     := YYYY-MM-DDTHH:MM:SSZ                                (UTC, written by the verb)
TYPE     := "drive-" [a-z]+
STAGE    := [a-z][a-z0-9-]*                                      (gaps, tasks, implement, converge, …, ready-set)
body     := exactly one of: one result-contract fence | one "- **Missing:** <non-empty reason>" line
            (blank lines and other prose may sit around it; a fence with another info string is skipped whole)
```

The reasons the method writes after `Missing:` (R-4): `refused: <the delegate's words>`, `malformed: <field>`,
`no continuation`, `stopped: <reason>`.

## What the gate prints

A finding is one stderr line under the gate's existing header, two spaces in, as every other finding:

```text
  specs/f/slices/S1/hand-backs.md:7: ## 2026-10-05T17:00:00Z — drive-hand — demo — status: 'green' is not one of accepted, behaviour, implementation
  specs/f/slices/S1/hand-backs.md:7: ## 2026-10-05T17:00:00Z — drive-hand — demo — files_changed: '/etc/passwd' is absolute; a path is repository-relative
  specs/f/slices/S1/hand-backs.md:12: ## 2026-10-05T17:00:00Z — drive-gaps — gaps — the result-contract fence is not closed
  specs/f/slices/S1/hand-backs.md:20: a heading that is not `## <UTC time> — <drive-type> — <stage>`
```

A later schema: `check-decisions: note: specs/f/slices/S1/hand-backs.md:7: ## … — contract 2 is newer than this
checker reads; its fields are not held` on stdout.

The summary line, only where a record exists:
`check-decisions: <n> decision(s) in <f> file(s), <d> demo(s) in <l> log(s), <h> hand-back(s) in <r> record(s), every
field present and every path in the tree, every done slice in the adversary log`. With no record, the line is
exactly today's.

## The verbs

| Call | Reads | Writes | Exit |
|---|---|---|---|
| `check-decisions.py --hand-back <dir> <type> <stage>` | the hand-back on stdin | appends heading + blank line + the fence verbatim + blank line, only when it passes | 0 appended · 1 faults on stderr, nothing written · 2 usage |
| `check-decisions.py --hand-back-missing <dir> <type> <stage> <reason…>` | — | appends heading + blank line + `- **Missing:** <reason>` + blank line | 0 · 2 usage |
| `check-decisions.py --hand-backs <slice-dir>` | `benchmark.json`, `hand-backs.md` | nothing | 0 (2 usage) |

`<dir>` is `specs/<feature>` or `specs/<feature>/slices/<id>`, relative to the root, existing; `<type>` one of the
ten; `<stage>` matches `STAGE`. Stdin without a block: `check-decisions: no result-contract block in the hand-back`;
with two: `… two result-contract blocks …`.

`--hand-backs` prints one line per ended benchmark entry, then a total:

```text
hand-backs: implement 2026-10-05T17:01:02Z drive-implement: block
hand-backs: converge 2026-10-05T18:00:00Z drive-converge: nothing recorded — a finding for converge
hand-backs: gaps 2026-10-05T18:30:00Z drive-gaps: missing — refused: out of budget
hand-backs: tasks 2026-10-05T16:00:00Z: the harness could not attribute its delegates — not counted
hand-backs: with a result contract: 1 of 3
```

A stage is listed only when a typed `drive-*` delegate that belongs to it ran (`OWNERS` in `benchmark.py`, copied as
`hand_backs.OWNERS` and held equal by a test): entries run in the host's context, stages whose only sub-agents were
untyped helpers (Explore, general-purpose), and `drive-slice`'s own context (its block goes to the feature record, plan
Q2) owe none and are not listed. A delegated entry whose `agents` is null or empty is *could not attribute*, never a
finding. Each line names the stage and the type(s); the finding for nothing recorded always reads `a finding for
converge`. The `<stage>` passed to `--hand-back` is the open benchmark entry's stage name. `make benchmark` (and the overview page) carry the
last line per slice, as `<slice>: hand-backs with a result contract: <n> of <m>` with
`; <k> stage(s) the harness could not attribute — not counted` where k > 0, and print nothing for a slice with m = k = 0.
