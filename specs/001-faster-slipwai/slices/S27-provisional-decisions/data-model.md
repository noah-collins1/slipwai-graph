# Data model: S27-provisional-decisions

No stored data is added. What follows are the grammars of the lines a decision entry may now carry, the setting's
values, and the verbs' inputs and outputs. A `<date>` is `YYYY-MM-DD`, a real calendar date (`date.fromisoformat`).

## The `decide` setting (`.specify/cruise.json`, no new key)

| Value | Rung | Always-ask item | Any other question |
|---|---|---|---|
| `recommended-first` (default) | 0 | `unavailable: a person's approval` | host where the stage recommends or a standing entry covers it, else the skipper |
| `skipper-always` | 0 | `unavailable: a person's approval` | the skipper |
| `provisional-shadow` | 1 | `unavailable`, plus a `Provisional (shadow):` line | as `recommended-first` |
| `provisional-advisory` | 2 | `unavailable`, plus a `Provisional (advisory):` line; the park recommends it | as `recommended-first` |
| `provisional` | 3 | provisional where R1's table allows, else `unavailable` | as `recommended-first` |

`--set decide=<v>` writes when `rung(v) <= rung(current) + 1`; otherwise it refuses
`` `decide` moves one mode at a time: set `<the value of rung(current)+1>` first `` (the next rung's single value).
With `CRUISE_ITERATION` set, any `--set decide=…` refuses: `` `decide` changes only through /cruise-settings, a
person's command; an iteration never sets it (D62) ``. The sentence (CONTROLS, settings command, docs):

> Change it to `provisional-shadow` when always-ask questions are stalling slices and you want to see which ones
> would have been taken provisionally before letting any be; move on to `provisional-advisory`, then `provisional`,
> once the shadow lines read right.

## Entry lines

```markdown
- **Reversibility:** <tier>[ → <tier>…] · rules <n> · <facts>          (S26; the last step is the final tier)
- **Provisional (shadow):** <final tier> · <would-have> · Revert: commits carrying Decision: D<n>
- **Provisional (advisory):** <final tier> · <would-have> · Revert: commits carrying Decision: D<n>
- **Status:** standing | overridden by D<m> | overridden by human <date> | provisional · ratify by <date> | ratified <date> | reverted <date>
- **Revert:** commits carrying Decision: D<n>
```

- `<would-have>` is `provisional · ratify by <date>`, `blocks (hard)`, or `blocks (<fact>=yes)` with `<fact>` one of
  `flag_default`, `ci_workflow`, `migrate_file`; `blocks (hard)` exactly when the tier is `hard`.
- `D<n>` in `Revert` is the entry's own number, always.
- Placement: the mode line after `Reversibility:` (and `Proposed rule:`), before `Written to:`; `Revert:` directly
  after `Status:`. `DECISION_FIELDS`' order check reads only its nine labels, so neither moves it.
- `ratify by <date>` = the `When:` instant's calendar date + 7 days (D199).

## `scripts/provisional.py status`

```
python3 scripts/provisional.py status --decide <value> --ask no|approval|fact|must|release
        --when <ISO instant> --number D<n> [--reversibility '<line, with or without its label>']
```

| decide | ask | final tier (no line = hard) | held fact | stdout |
|---|---|---|---|---|
| any | `no` | any | any | `- **Status:** standing` |
| any | `fact` / `must` / `release` | any | any | `unavailable: <a fact nobody here has \| an option that breaks a constitution MUST \| a release nobody asked for>`, `- **Status:** standing` |
| `provisional` | `approval` | easy, guarded | none | `- **Status:** provisional · ratify by <date>`, `- **Revert:** commits carrying Decision: D<n>` |
| `provisional` | `approval` | hard, or a held fact | | `unavailable: a person's approval`, `- **Status:** standing` |
| `provisional-shadow` / `-advisory` | `approval` | any | any | `unavailable: a person's approval`, the mode line, `- **Status:** standing` |
| `recommended-first` / `skipper-always` | `approval` | any | any | `unavailable: a person's approval`, `- **Status:** standing` |

Stderr: one line, `provisional: <why>` (e.g. `provisional: unavailable — flag_default=yes: provisional approval never
flips a flag (FR-033)`); under advisory, for an item that would have been provisional, a second line, the park
reason `cruise: parked: D<n> needs a person's approval; recommended: provisional · ratify by <date> (<tier>) — answer
accept through /cruise-tell`. Usage faults: one stderr line naming the option, exit 2, stdout empty.

## `scripts/provisional.py audit [--feature <name>]`

Exit 3 and `cruise: parked: ratify D<n>` (the lowest-numbered entry whose first `Status` starts with `provisional`);
exit 0 and `provisional: no unratified provisional decision in specs/<f>/decisions.md` (or `no decisions.md`);
exit 2 and one line naming the features where `specs/` holds several logs and none is chosen.

## `scripts/agents/cruise.py mode [--feature <name>]`

Mode entry heading: `## D<n> — decide moved from <a> to <b>`, `<a>` a value or `unrecorded`. Outputs: exit 0
`cruise: decide is <v>, as D<n> recorded`; exit 0 and the entry to append (below); exit 3
`cruise: parked: decide=<v> skips <next>; set it through /cruise-settings`.

```markdown
## D<next> — decide moved from <a> to <b>
- **Stage:** iteration start · **Slice:** none · **When:** <now> · **Iteration:** <CRUISE_ITERATION or unknown>
- **Scope:** global
- **Question:** which `decide` mode does this run work under?
- **Options:** recommended-first · skipper-always · provisional-shadow · provisional-advisory · provisional
- **Decision:** <b>, as a person set it in `.specify/cruise.json` (<commit <hash> | uncommitted at <instant>>)
- **Why:** a person changed the setting through /cruise-settings; the run records the move and never sets it (D62)
- **Decided by:** human
- **Confidence:** high · **Would reverse if:** a person sets `decide` again
- **Written to:** `.specify/cruise.json`
- **Status:** standing
```

## Gate findings (each `<file>:<line>: D<n> …`, one per fault)

| Fault | Field named |
|---|---|
| a status with a new first word not in one of the three exact forms, or a date that is not a calendar date | `Status` |
| a provisional entry with no `Revert:`; a `Revert:` twice; not `commits carrying Decision: D<own>`; on an entry whose status is not one of the three forms | `Revert` |
| a provisional entry with no `Reversibility:` line; its final tier `hard` | `Reversibility` |
| a provisional entry whose facts carry `ci_workflow=yes`, `migrate_file=yes` or `flag_default=yes` | the fact |
| a mode line not in its grammar, its tier/`blocks (hard)` disagreeing, its `Revert` naming another entry; a second mode line | `Provisional (shadow)` / `Provisional (advisory)` |

## `--scope`

`reverted <date>` joins the left-out list as `D<n> (reverted <date>)`; `provisional …` and `ratified …` entries are
placed like standing ones; the summary gains `; provisional and binding: D<n>, …` only where one is printed.
