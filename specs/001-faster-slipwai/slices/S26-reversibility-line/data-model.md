# Data model: S26-reversibility-line

Nothing here is stored outside `decisions.md`. The line is a new optional field of a decision entry; the rules are
code in `assets/toolkit/scripts/reversibility.py`; the committed list of what `migrate` propagates is one file per
project (D175). The spellings below are the plan's, under D174 rule 3 ("exact key names belong to planning").

## The `Reversibility:` line

```
- **Reversibility:** <tiers> · rules <n> · <fact>=<value> <fact>=<value> …
```

- `<tiers>` — the tier the rules computed, alone (`easy`, `guarded`, `hard`), or that tier followed by each
  escalation step, one tier per step: `easy → guarded`, `guarded → hard`, `easy → guarded → hard` (D177). The
  first tier is always the computed one; `->` is read as `→` (as `measures.SPELLING["escalation"]` reads it).
  A step that skips a tier (`easy → hard`), repeats one (`easy → easy`) or lowers one (`hard → guarded`) is malformed.
- `rules <n>` — the version of the rule table that scored the line, a positive integer the gate knows. The gate
  re-derives the first tier under *that* version, never a later one (D65, AC-S26-11).
- the facts — space-separated `key=value`, each key at most once, every key from the closed list below. No fact
  value and no key contains a tier word, so `measures.decision_health`'s "first of `easy|guarded|hard` on the
  line" is always the computed tier (D168, AC-S26-13).

A well-formed example (AC-S26-1):

```
- **Reversibility:** easy · rules 1 · contract=no schema=no auth=no customer_visible=no export=no ci_workflow=no migrate_file=no behind_flag=yes flag_default=no rollback_complexity=trivial
```

The D54 fixture (AC-S26-6), escalation not taken:

```
- **Reversibility:** hard · rules 1 · contract=no schema=no auth=no customer_visible=no export=no ci_workflow=yes migrate_file=yes behind_flag=no-code flag_default=no rollback_complexity=trivial
```

### Placement in the entry

After the `Confidence` line, before `Written to`. It is **not** one of `DECISION_FIELDS`: the gate's
presence-and-order check is unchanged, so an entry without the line is never a finding (D176 rule 1).

## Facts (rules version 1)

| Key | Values | FR-051 / D174 fact |
|---|---|---|
| `contract` | `yes` · `no` | contract change |
| `schema` | `yes` · `no` | schema change |
| `auth` | `yes` · `no` | permission or authentication change |
| `customer_visible` | `yes` · `no` | pricing or customer-visible effect |
| `export` | `yes` · `no` | data export |
| `ci_workflow` | `yes` · `no` | a CI workflow touched |
| `migrate_file` | `yes` · `no` | a file `migrate` propagates touched |
| `behind_flag` | `yes` · `no` · `no-code` | whether what it changes sits behind a flag; `no-code` for a decision that changes no code |
| `flag_default` | `yes` · `no` | a flag's default changed — kept apart from `behind_flag` for S27 (D174 rule 1) |
| `rollback_complexity` | `trivial` · `hours` · `days` · `needs-migration` | FR-051's enum |

Dependants are not a fact on the line: they are read from the entry's own `Scope:` line (D174 rule 2).

`size`, `urgency` and any other key are not facts: a line carrying one is **malformed** (D176 rule 3) — the verb
gives no tier, the gate refuses the entry naming the key.

## Rules version 1 (a test per rule, AC-S26-2/-3/-4)

The tier is the highest any rule gives; with none firing it is `easy`.

| Rule | Fires when | Tier |
|---|---|---|
| H1–H7 | `contract`, `schema`, `auth`, `customer_visible`, `export`, `ci_workflow` or `migrate_file` is `yes` (one rule each) | `hard` |
| R1 | `rollback_complexity` is `days` or `needs-migration` | `hard` |
| R2 | `rollback_complexity` is `hours` | `guarded` |
| F1 | `behind_flag` is `no` | `guarded` |
| F2 | `flag_default` is `yes` | `guarded` |
| D1 | the entry's `Scope:` names two or more slice ids | `guarded` |
| D2 | the entry's `Scope:` is `global`, absent or unreadable (the gate's own `scope_tokens`) | `hard` |
| U1 | a known fact is missing, or carries a value the fact does not accept (`schema=maybe`, `rollback_complexity=weeks`, `migrate_file=no-list`) | `hard` (D176 rule 4) |

`trivial`, `behind_flag=yes|no-code`, `flag_default=no`, a single slice id and every hard fact `no` fire nothing.

## The committed list of migrate-propagated files (D175)

| Layout | Path | Written by |
|---|---|---|
| adopted | `delivery/.written` (unchanged) | `adopt`, rewritten by `migrate` |
| generated | `.slipwai/propagated` (new): `scripts/`, `skills/`, `commands/`, `agents/`, `.specify/`, `Makefile`, `init`, itself | `generate`; `migrate` through `replay` |

Format: `.written`'s own — one project-relative path per line. `migrate_file` is checked against it:

- the list exists and a path the entry's `Written to` names is on it → the effective `migrate_file` is `yes`
  whatever was declared (paths only ever raise, D174 rule 5, AC-S26-7);
- no list exists → the verb writes `migrate_file=no-list`, which is a value the fact does not accept, so U1 scores
  `hard` and the line names the fact (D175 condition 3); the gate refuses `migrate_file=no` there.

## `Proposed rule:` (D178)

```
- **Proposed rule:** <one sentence written to sit in the owner brief> (same shape as D<a>, D<b>)
```

Optional, after `Reversibility:`. Every `D<n>` in the parenthesis counts; the gate refuses the line when fewer
than two distinct ids other than the entry's own are cited, or when one is not an entry of the same
`decisions.md` whose `Status` is `standing`. An entry without the line is never refused.

## Gate findings and notes added

All only on content this release introduces (D65): a log with no `Reversibility:` and no `Proposed rule:` line
never loads `reversibility.py` and gets the earlier checker's answer byte for byte (AC-S26-10).

| Kind | When |
|---|---|
| finding | malformed tier word, a skipped/repeated/lowering step, unknown `rules` version, unknown or repeated key, malformed `key=value` |
| finding | a second `Reversibility:` line |
| finding | the first tier differs from what the named rules version derives (the message names the rules that fired) |
| finding | `migrate_file=no` while a `Written to` path is on the list, or where no list exists |
| finding | a `Proposed rule:` citing fewer than two ids, or a non-standing / absent id |
| note | an entry with no `Reversibility:` line after one that has it (names the entry and the verb; exit unchanged) |
