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
## <UTC time> — drive-<name> — <stage> — <started>
```

The time is `YYYY-MM-DDTHH:MM:SSZ` and is written by the verb, never by the delegate. The optional fourth part is the
`started` of the `benchmark.json` entry the entry answers, in the same form: it is what ties a block to the stage it
was written for, a continuation written long after the stage ended included. A heading without it answers no benchmark
entry (`ready-set`, or any stage with none), and `--hand-backs` does not count it. The body is exactly one of one
`result-contract` fence, or one line `- **Missing:** <reason>` when the delegate handed back no block. The reasons the
method writes are `refused: <the delegate's words>`, `malformed: <field>`, `no continuation` and
`stopped: <reason>`; any non-empty reason passes the gate. Text before the first `## ` heading is the file's own.

Helpers a delegate starts (Explore, general-purpose, the groups a `drive-implement` fans out to) get no block and no
entry of their own: what they did is reported in the delegate's own block, in `tests`, `files_changed`, `unresolved`
and `change_summary`, and that one block is what the dispatching session appends.

## The verbs

All three are `scripts/check-decisions.py`; `<dir>` is `specs/<feature>` or `specs/<feature>/slices/<id>`, existing,
`<type>` one of the ten and `<stage>` a lowercase word such as `gaps`, `implement` or `ready-set`.

| Call | Reads | Writes | Exit |
|---|---|---|---|
| `scripts/check-decisions.py --hand-back <dir> <type> <stage>` | the hand-back on stdin | the heading and the fence, verbatim, only when the block passes | 0 appended, 1 faults on stderr and nothing written, 2 usage |
| `scripts/check-decisions.py --hand-back-missing <dir> <type> <stage> <reason>` | nothing | the heading and `- **Missing:** <reason>` | 0, 1 refused, 2 usage |
| `scripts/check-decisions.py --hand-backs <slice-dir>` | `benchmark.json` and `hand-backs.md` | nothing | 0, 2 usage |

Both write verbs take `--started <instant>` after `<stage>` (before the reason): the `started` of an entry of that
stage in `<dir>/benchmark.json`; one that is not is refused (exit 1,
one line, nothing written). Left out, the verb answers the stage's one open entry, which is the on-time case: append
before ending the entry. A stage whose entries have all ended is refused until you pass `--started` with the instant
the `--hand-backs` line, or the converge, demo-stop or adversary-stop line, names; the verb never guesses. With no
`benchmark.json`, or no entry of that stage, the heading has three parts and the verb says it answers no benchmark
entry. A retry is the same block or reason for the same type, stage and start as the last such entry; for another
start of the stage it is appended.

`--hand-backs` lists, for each ended benchmark entry that owes a block, whether the record holds a passing block for
that stage (an entry whose `started` is the stage's own), a `Missing:` line, or nothing; converge reads it, and `make benchmark` prints the count per slice. A stage
owes a block only when a typed `drive-*` delegate that belongs to the stage ran (`implement` to `drive-implement`,
`converge` to `drive-converge`, and so on, the table in `scripts/agents/benchmark.py`): the untyped helpers it started
(Explore, general-purpose) and a `drive-slice`'s own context owe none, because the slice delegate's block goes to the
feature record under `ready-set`. A stage that was delegated but whose entry names no agent types, or whose tokens the
harness could not read, is listed as not attributable and counted as neither owed nor held; it is never a finding.
Each line names the stage and the type(s), and the one for nothing recorded reads `nothing recorded — a finding for
converge`. The `<stage>` you pass `--hand-back` is the name of the stage's open benchmark entry, so the record and
`benchmark.json` agree.
`make check-decisions` holds every `hand-backs.md` to the shape above and prints one line per fault, naming the file,
the entry's heading and the field. A project with no `hand-backs.md` gets the gate it always had.
