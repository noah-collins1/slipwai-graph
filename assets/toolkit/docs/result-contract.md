# Result contract

Every delegated agent ends its hand-back with one block, so the session that dispatched it, the gate and the
benchmark read the same thirteen fields from every type and not a paragraph written a different way each time.
The shape is `scripts/hand_backs.py`; this page is the same shape in words, and a test holds the two tables below
equal to it.

## The block

One JSON object inside a fence whose info string is exactly `result-contract`:

````markdown
```result-contract
{"contract": 1, "delegate": "drive-gaps", "scope": "S14-result-contract converge pass 1", "status": "gaps",
 "contracts_changed": [], "invariants_checked": ["AC-S14-16 bytes"], "tests": ["make test TESTS=test_x: 12 passed"],
 "decisions": ["D134"], "assumptions": [], "unresolved": [], "change_summary": "Read the diff; two gaps.",
 "files_changed": [], "difficulty_observed": {"score": 2, "reason": "one module, clear criteria"}}
```
````

Keys outside the thirteen are ignored, and a block that says `"contract": 2` or later is passed with a note and its
fields are not held: a reader of this version does not refuse a newer one.

## The fields

| Field | Kind | Rule (a fault names the field) |
|---|---|---|
| `contract` | integer | `1`, and not a boolean. Greater than 1: passed with a note, no field held. Anything else is a fault |
| `delegate` | string | one of the ten types below, and equal to the type in the entry's heading |
| `scope` | string | non-empty |
| `status` | string | in the set for `delegate` |
| `contracts_changed` | list | strings; may be empty |
| `invariants_checked` | list | strings; may be empty |
| `tests` | list | strings; may be empty |
| `decisions` | list | strings, each `D<n>` and a `## D<n> — ` heading in the feature's `decisions.md` |
| `assumptions` | list | strings; may be empty |
| `unresolved` | list | strings; may be empty |
| `change_summary` | string | non-empty |
| `files_changed` | list | strings, repository-relative: no leading `/` or `\`, no `X:` drive, no `..` segment; may be empty |
| `difficulty_observed` | object | exactly `score` (an integer 1 to 5, not a boolean) and `reason` (a non-empty string) |

## Status, per type

| Type | Allowed `status` |
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

The hand's three verdicts and the bosun's three words are these `status` values, and the skipper returns its
decision entry first and the block after it.

## The record

The dispatching session appends each block, verbatim, to an append-only `hand-backs.md`:
`specs/<feature>/slices/<id>/hand-backs.md` for a slice's stages, `specs/<feature>/hand-backs.md` for feature-level
ones (the split, the ready set's `drive-slice` delegates under stage `ready-set`, the completion audit). Each entry
is a heading and a body:

```text
## <UTC time> — drive-<name> — <stage>
```

The time is `YYYY-MM-DDTHH:MM:SSZ` and is written by the verb, never by the delegate. The body is exactly one of one
`result-contract` fence, or one line `- **Missing:** <reason>` when the delegate handed back no block. The reasons the
method writes are `refused: <the delegate's words>`, `malformed: <field>`, `no continuation` and
`stopped: <reason>`; any non-empty reason passes the gate. Text before the first `## ` heading is the file's own.

## The verbs

All three are `scripts/check-decisions.py`; `<dir>` is `specs/<feature>` or `specs/<feature>/slices/<id>`, existing,
`<type>` one of the ten and `<stage>` a lowercase word such as `gaps`, `implement` or `ready-set`.

| Call | Reads | Writes | Exit |
|---|---|---|---|
| `scripts/check-decisions.py --hand-back <dir> <type> <stage>` | the hand-back on stdin | the heading and the fence, verbatim, only when the block passes | 0 appended, 1 faults on stderr and nothing written, 2 usage |
| `scripts/check-decisions.py --hand-back-missing <dir> <type> <stage> <reason>` | nothing | the heading and `- **Missing:** <reason>` | 0, 2 usage |
| `scripts/check-decisions.py --hand-backs <slice-dir>` | `benchmark.json` and `hand-backs.md` | nothing | 0, 2 usage |

`--hand-backs` lists, for each ended benchmark entry that was delegated, whether the record holds a passing block for
that stage, a `Missing:` line, or nothing; converge reads it, and `make benchmark` prints the count per slice.
`make check-decisions` holds every `hand-backs.md` to the shape above and prints one line per fault, naming the file,
the entry's heading and the field. A project with no `hand-backs.md` gets the gate it always had.
