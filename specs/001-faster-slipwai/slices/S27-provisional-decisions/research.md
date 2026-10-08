# Research: S27-provisional-decisions

Each entry: the question, what was read, the choice and why. Facts about the tree cite the file and line read at
`5f4fc00`; nothing here rests on an uncited statement about a dependency (the slice adds none).

## R-1 One new script beside the gate, not a second verb inside `reversibility.py`

- **Read:** `assets/toolkit/scripts/reversibility.py` (373 lines; its docstring promises a version, once shipped, is
  never edited, and its `main` is one verb with fixed options); `check-decisions.py`'s `sibling()` (loads a module
  beside it by path, bytecode off) and `reversibility_findings()` (loads only for a log carrying its label);
  `verify_scoped/table.py:55-60` (a gate script's change is already the full gate).
- **Choice:** `scripts/provisional.py`, loaded by `check-decisions.py` through `sibling("provisional")` only for a log
  with a new form, and run as the verb (`status`) and the audit (`audit`). It reads `reversibility.parse_line` for the
  final tier and facts: injected by the gate (which already has the module or loads it), loaded by path in `main`.
- **Why:** S26's shape exactly (D174 put the rules beside the gate); `reversibility.py`'s option parser and frozen
  rules stay untouched; one module holds the verb's table and the gate's reading of the same lines, so they cannot
  drift (*one shipped verb*, D201).
- **Rejected:** a subcommand of `reversibility.py` (mixes a frozen classifier with a mode table that S28 extends);
  checks inline in `check-decisions.py` (780 lines, and every old log would pay for them).

## R-2 What the verb takes: `--ask <kind>` and the whole `Reversibility:` line

- **Read:** D201 (the verb prints from the `decide` value, the final tier and the always-ask flag); AC-S27-5 (adds the
  three facts); AC-S27-6 (fact, credential, third party, MUST, release: unavailable whatever `decide` says);
  `cruise_agents.py:70-75` (the skipper's `unavailable` for a fact); `cruise_stops.py:59-63, 70-73`.
- **Choice:** `--reversibility` takes the line the skipper already wrote (with or without its label): its last step is
  the final tier, its facts give the three FR-033 facts, and parsing it with S26's `parse_line` refuses a malformed
  one. `--ask` is `no | approval | fact | must | release`.
- **Why:** passing the line rather than a tier and three flags means the skipper cannot report a tier the line does
  not say; a yes/no always-ask flag cannot express AC-S27-6, and the verb is where the table must live for a test to
  pin it (G8). `--decide` is passed, not read from `.specify/cruise.json`: the verb then reads no file, so the scoped
  gate's row for `check-decisions` (which loads this module) gains no input, and the skipper's brief names the file it
  copies the value from.

## R-3 The rehearsal line for an item held back by a fact but not `hard`

- **Read:** AC-S27-10 (`<tier> · <the Status it would have had, or blocks (hard)> · Revert: …`); D195 rule 1 (an
  item with `flag_default=yes` is never provisional, whatever its tier); `reversibility.py:69-92` (`ci_workflow=yes`
  and `migrate_file=yes` are H6/H7, so always `hard`; `flag_default=yes` is F2, `guarded`).
- **Choice:** `blocks (hard)` for a `hard` final tier; `blocks (flag_default=yes)` (in general `blocks (<fact>=yes)`,
  the first of the three in the line's order) for a non-hard item one of them holds back.
- **Why:** the line's purpose (FR-057's measures, D196) is to say what would have happened and why; writing
  `blocks (hard)` beside the tier `guarded` would be false. Only `flag_default` can reach this branch under rules 1;
  the general form keeps a later rules version honest. Recorded as P2 for the host.

## R-4 Where the gate checks: a module loaded on demand, and `STATUS` left alone for old forms

- **Read:** `check-decisions.py:104` (`STATUS`), `:277-279` (its finding), `:455-462` (`--scope` drops overridden),
  `:621-640` (`gate()`); `tests/test_decisions_gate_differential.py` (D65's comparison with `596740f`).
- **Choice:** `check_decisions` skips the `STATUS` finding for a status whose first word is `provisional`, `ratified`
  or `reverted`; `provisional_findings(path)` runs after `reversibility_findings`, and loads the module only where the
  raw text matches `^- \*\*Status:\*\* ?(provisional|ratified|reverted)\b` or `^- \*\*(Revert|Provisional
  \((shadow|advisory)\)):\*\*`. Entries are parsed the way `check_decisions` parses them (`entries(…, legacy=True)` on
  the raw text), so what one skips the other checks.
- **Why:** a log with none of those forms never loads the module and never sees a different message (AC-S27-7). A
  status with a new first word was refused before; now it is held to its exact form. A stray `Revert:` on an old log
  passed before and is refused now: a label only this release defines (D65's carve-out; P4).

## R-5 The mode ladder and the mode entry

- **Read:** D196 parts 3–4; `agents/cruise.py:159-195` (`CHOICES`, `DEFAULTS`, `CONTROLS`), `:247-268` (`assign`),
  `:1794-1835` (`--set` writes after `check`); `:118` (`CRUISE_ITERATION`, which `run` sets for every iteration);
  ADR 0008.
- **Choice:** `RUNGS` in `agents/cruise.py`; the refusal in the `--set` branch of `main`, before the file is written,
  reading the current value from the file; the iteration guard there too (`ITERATION_VARIABLE` in the environment,
  `decide` among the keys). `mode` is a verb of the same script: it reads `CONFIG`, every feature's `specs/*/decisions.md` headings, the latest `When` as an instant (D202), `git log -1 --format=%h -- .specify/cruise.json` and
  `git status --porcelain -- .specify/cruise.json`, and prints; it writes nothing. The first entry's heading is
  `decide moved from unrecorded to <v>` (P3).
- **Why:** the runner already owns the file, the iteration variable and git; the ladder is a property of the setting,
  so it sits beside `CHOICES`. Printing the entry keeps the append (and the `D<n>`) with the session, as the command
  already says, and lets a test pin the text. `check()` stays shape-only (D196: a valid value is never a finding).

## R-6 Advisory's one-word answer

- **Read:** D196 part 2 (advisory: a person answers in one word through `/cruise-tell`); `src/slipwai/project/
  cruise_told.py` (a person's message reaches the next iteration as `told: <message>`); D62/D132 (a person's message
  is written down by the host as `Decided by: human`).
- **Choice:** the verb prints, under advisory and only for an item that would have been provisional, the park reason
  `cruise: parked: D<n> needs a person's approval; recommended: provisional · ratify by <date> (<tier>) — answer accept
  through /cruise-tell`. The command says: `told: accept` is written as a `Decided by: human` entry that takes the
  recommendation (`Status: standing`), and the `unavailable` entry becomes `overridden by D<m>`.
- **Why:** the person's word is the approval, so the answer is a person's decision, not a provisional one; the
  override route already exists and keeps the log honest about who decided (P5).

## R-7 What `migrate` carries, and what it leaves

- **Read:** `src/slipwai/project/seeded.py:1-17` (`.specify/cruise.json` seeded, never rewritten); S26's
  `tests/test_reversibility_migrate.py` (an old factory from `git archive`, a project generated with it, migrated by
  this checkout, `make verify`).
- **Choice:** nothing in `migrate.py` changes; `replay` carries `scripts/provisional.py` and the regenerated
  `.slipwai/propagated` (which then names it, D183), and the command, brief and template merge as every text does.
- **Why:** AC-S27-17's file stays byte-equal because no key was added (ADR 0008).

## R-8 Line budgets

- **Read:** `wc -l` at `5f4fc00`: `src/slipwai/project/cruise.py` 341, `tests/test_cruise.py` 350,
  `tests/test_cruise_runner.py` 336, `cruise_agents.py` 198, `cruise_record.py` 76, `cruise_stops.py` 89,
  `decisions.py` 103.
- **Choice:** every new paragraph is a constant in `cruise_provisional.py`; `cruise.py` replaces its three-line
  `decide` row with one line and gains at most nine interpolation lines; `test_cruise.py` is not touched; the runner
  test's one changed line keeps its count.
