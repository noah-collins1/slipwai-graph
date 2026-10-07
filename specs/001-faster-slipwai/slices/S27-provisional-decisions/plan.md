# Implementation Plan: S27-provisional-decisions — a decision that is easy to take back no longer stops a slice

**Branch**: `slice/S27-provisional-decisions` (worktree `../slipwai-graph-S27-provisional-decisions`, cut from
`adopt-method` at `5f4fc00`; the local branch is the claim, no push — D129) | **Date**: 2026-10-07 |
**Spec**: [spec.md](../../spec.md), *Slice acceptance criteria* → `### S27-provisional-decisions` (AC-S27-1 … AC-S27-17)

**Input**: User Story 8, FR-029–FR-033, FR-053 (and SC-011's first two clauses) in [spec.md](../../spec.md); S27's
split and graph rows in [story-split.md](../../story-split.md) (S28's row out of scope); D195–D201 with D54, D62, D65,
D132, D174–D178, D183–D185 in [decisions.md](../../decisions.md); ADR 0008 at Proposed
(`delivery/docs/adr/0008-provisional-mode-is-a-decide-value.md`, never accepted by the run); the gaps report
`/tmp/s27/gaps.md` (G1–G19); the owner brief `.specify/product-owner.md`; `AGENTS.md` (MINOR, one fragment, `VERSION`
stays `1.6.0.dev0`). Written by cruise iteration 28's plan stage, inside the slice's `drive-slice` delegate (host
model, current context).

## Summary

`decide` gains three values — `provisional-shadow`, `provisional-advisory`, `provisional` — each acting as
`recommended-first` for every question that is not an always-ask item (D196, ADR 0008). One shipped verb,
`scripts/provisional.py status`, turns the `decide` value, the kind of item, the entry's `Reversibility:` line, its
`When:` and its number into the lines the entry carries: `Status: provisional · ratify by <When + 7 days>` with
`Revert: commits carrying Decision: D<n>` only for `provisional` with an `easy` or `guarded` approval item that
declares none of `flag_default=yes`, `ci_workflow=yes`, `migrate_file=yes`; `unavailable: a person's approval`
otherwise, with a `Provisional (shadow|advisory):` line in the two rehearsal modes (D195, D198, D199, D201). The same
module, loaded by path beside `check-decisions.py` only for a log that carries one of the new forms, holds the three new
`Status` forms, the `Revert:` line, the FR-033 refusals and the mode lines (D197, D200); a log without them gets the
earlier checker's answer (D65). `check-decisions --scope` prints provisional and ratified entries as binding and leaves
a reverted one out. `scripts/provisional.py audit` is the completion audit's refusal (`cruise: parked: ratify D<n>`,
D197). The runner's `cruise.py --set` refuses a forward skip of the mode ladder and any `decide` change inside an
iteration (D196, D201), and `cruise.py mode` gives the iteration the entry recording a person's move, or the park for a
hand edit that skipped a rung. The command, the skipper's brief, the stop table, the entry shape, the settings command
and `docs/cruise.md` say all of it. MINOR, one fragment `changelog.d/provisional-decisions.md`.

## The example map

Rules are numbered; each is one RED-GREEN-REFACTOR increment (constitution V). Grammar, verbs and findings are in
[data-model.md](data-model.md); reasons in [research.md](research.md). *A scratch project* is a temporary directory
holding `project.json`, `scripts/check-decisions.py`, `scripts/reversibility.py` and `scripts/provisional.py` copied
from `assets/toolkit/scripts/`, `README.md` and `specs/f/decisions.md` (S26's `tests/reversibility_fixture.py`
pattern); scripts run as subprocesses with `python3 -B`. *The guarded fixture* is AC-S27-1's facts:
`contract=no schema=no auth=no customer_visible=no export=no ci_workflow=no migrate_file=no behind_flag=yes
flag_default=no rollback_complexity=hours`, scope one slice. *The flag fixture* is AC-S27-4's: the same with
`flag_default=yes rollback_complexity=trivial`. *The D54 fixture* is `ci_workflow=yes migrate_file=yes
behind_flag=no-code`.

| Rule | Criteria | What it says | Examples |
|---|---|---|---|
| **R1** the verb's table | AC-S27-1, -2, -3, -4, -5, -6; D195, D199, D201 | `python3 scripts/provisional.py status --decide <v> --ask <kind> --when <instant> --number D<n> [--reversibility '<line>']` prints on stdout the lines the entry carries, exit 0, and on stderr one line saying why. `--ask` is `no` (not an always-ask item), `approval` (an owner-brief always-ask line: a person's approval), `fact` (a credential, a third party's behaviour, anything nobody here has), `must` (an option breaking a constitution MUST) or `release` (a release nobody asked for). `no` prints `- **Status:** standing` under every `decide`. `fact`, `must`, `release` print `unavailable: <reason>` and `- **Status:** standing` under every `decide`. `approval` is provisional only where `decide` is `provisional`, the final tier of the line (its last step) is `easy` or `guarded`, and its facts carry none of `flag_default=yes`, `ci_workflow=yes`, `migrate_file=yes`: then `- **Status:** provisional · ratify by <date>` and `- **Revert:** commits carrying Decision: D<n>`, `<date>` the `When` date plus seven days (UTC calendar date). Otherwise `unavailable: a person's approval` and `- **Status:** standing`. No `--reversibility` reads as `hard` (D176). A `decide` outside the five values, an `--ask` outside the five kinds, a `When` whose first ten characters are no ISO date, a number not `D<digits>`, an unparseable line, an option missing or given twice: one stderr line naming it, exit 2, nothing on stdout | e1 guarded fixture, `provisional`, `approval`, `When: 2026-10-07T21:17:49Z`, D12: `Status: provisional · ratify by 2026-10-14`, `Revert: commits carrying Decision: D12` · e2 the same with the `easy` line: provisional · e3 `When: 2026-12-28T00:00Z`: `ratify by 2027-01-04` · e4 D54 fixture's (`hard`) line under `provisional`: `unavailable: a person's approval` · e5 the flag fixture (`guarded` by F2): unavailable, stderr names `flag_default=yes` · e6 each of `recommended-first`, `skipper-always`, `provisional-shadow`, `provisional-advisory` with the easy, guarded and hard lines: unavailable (12 cases) · e7 no `--reversibility` under `provisional`: unavailable, stderr says hard · e8 `easy → guarded → hard` escalation: unavailable (the last step governs) · e9 `--ask no` under each of the five values: `Status: standing` only · e10 `--ask fact`, `must`, `release` under `provisional` with the easy line: `unavailable`, never provisional · e11 `--decide sometimes`, `--ask maybe`, `--when yesterday`, `--number 12`, a line naming `rules 9`, `--number` twice: exit 2, stdout empty |
| **R2** the rehearsal lines | AC-S27-10 (verb half); D196, D198 | Under `provisional-shadow` and `provisional-advisory` an `approval` item also prints `- **Provisional (shadow):** <final tier> · <would-have> · Revert: commits carrying Decision: D<n>` (label `Provisional (advisory):` for advisory), `<would-have>` the Status R1 would have printed under `provisional` (`provisional · ratify by <date>`), or `blocks (hard)` for a `hard` final tier, or `blocks (<fact>=yes)` for a non-hard item one of the three facts holds back (research R-3). Under advisory, for an item that would have been provisional, stderr also prints the park reason: `cruise: parked: D<n> needs a person's approval; recommended: provisional · ratify by <date> (<tier>) — answer accept through /cruise-tell`. No mode line for `no`, `fact`, `must`, `release`, nor under the two off values or `provisional` | e1 shadow, guarded fixture: `unavailable`, `Status: standing`, `Provisional (shadow): guarded · provisional · ratify by 2026-10-14 · Revert: commits carrying Decision: D12` · e2 shadow, D54 fixture: `Provisional (shadow): hard · blocks (hard) · Revert: …` · e3 shadow, flag fixture: `… guarded · blocks (flag_default=yes) · …` · e4 advisory, guarded fixture: the `Provisional (advisory):` line, and stderr carries the park reason naming `accept` · e5 advisory, D54 fixture: the line, and no park recommendation · e6 `provisional`, `recommended-first`: no mode line |
| **R3** the gate holds the new `Status` forms and `Revert:` | AC-S27-8; D197, D198 | In `make check-decisions`, a `Status` whose first word is `provisional`, `ratified` or `reverted` is accepted exactly as `provisional · ratify by YYYY-MM-DD`, `ratified YYYY-MM-DD`, `reverted YYYY-MM-DD` (each a real calendar date); otherwise one finding naming the entry and `Status` with the three forms. A `- **Revert:**` line is accepted exactly as `commits carrying Decision: D<own number>`, once, on an entry whose `Status` is one of the three forms; otherwise one finding naming the entry and `Revert`. A provisional entry without `Revert:` is refused naming `Revert` | e1 D1 `provisional · ratify by 2026-10-14` + `Revert: commits carrying Decision: D1` (with an easy line): exit 0 · e2 `ratified 2026-10-09`, `reverted 2026-10-09` (with or without `Revert:`): exit 0 · e3 `provisional · ratify by 2026-13-01`, `ratified tomorrow`, `provisional`: each refused naming D1 and `Status` · e4 provisional, no `Revert:`: refused naming `Revert` · e5 two `Revert:` lines: refused · e6 `Revert:` naming D2 on D1: refused naming D2 · e7 `Revert:` on a `standing` entry: refused naming `Revert` · e8 `Revert: the last three commits`: refused |
| **R4** a provisional entry holds FR-033 | AC-S27-9; D195, D200 | A well-formed provisional entry is refused, one finding naming the entry and the field, where it has no `Reversibility:` line, where the line's last step is `hard`, or where its facts carry `ci_workflow=yes`, `migrate_file=yes` or `flag_default=yes` (one finding per fact). An unparseable line is S26's finding, not repeated here. `ratified` and `reverted` entries are not held to it (a person decided) | e1 provisional, no `Reversibility:`: refused naming `Reversibility` · e2 provisional with `easy → guarded → hard`: refused (`hard`) · e3 provisional with the flag fixture's line: refused naming `flag_default` · e4 with a `ci_workflow=yes` line: refused naming `ci_workflow` (and S26's `hard` re-derivation as it already is) · e5 `ratified 2026-10-09` with a `hard` line: accepted |
| **R5** the gate holds the rehearsal lines | AC-S27-10 (gate half); D196 | A `- **Provisional (shadow):**` or `- **Provisional (advisory):**` line is accepted when it is `<tier> · <would-have> · Revert: commits carrying Decision: D<own>`, `<would-have>` `provisional · ratify by YYYY-MM-DD` or `blocks (hard)` or `blocks (<fact>=yes)` for one of the three facts, `blocks (hard)` exactly when the tier is `hard`; a second such line (either label) is refused; an entry without one is never refused | e1 the R2 e1 line on a `standing` entry: exit 0 · e2 `hard · blocks (hard) · …`: accepted; `guarded · blocks (hard) · …`: refused · e3 `medium · …`, `guarded · provisional · ratify by 2026-02-30 · …`, `Revert` naming another entry: each refused naming `Provisional (shadow)` · e4 a shadow line and an advisory line on one entry: refused · e5 a log whose entries have none: nothing new |
| **R6** old logs get the earlier answer | AC-S27-7; D65 | A log with no `Status` starting `provisional`, `ratified` or `reverted`, no `- **Revert:**` and no `- **Provisional (shadow\|advisory):**` line never loads `provisional.py`: exit code, findings and stdout less `note:` lines equal the checker released at `596740f`'s (the differential test extended to a scratch project that also holds `provisional.py`) and the checker at `5f4fc00`'s. The one moved answer is a log that already held one of those labels or words: the released checker refused `provisional …`/`ratified …` statuses and passed a stray `Revert:`; now they are read (D65's carve-out — lines only this release defines — stated in the test) | e1 every case of `test_decisions_gate_differential` and this repository's own log, through a scratch project holding the three scripts: equal to the released checker · e2 a `Revert:` on a standing entry: passed before, refused now — the stated carve-out · e3 `provisional.py` deleted from the scratch project and a log with no new form: same answer |
| **R7** `--scope` reads the new statuses | AC-S27-15 (second half); D197 rule 3 | `check-decisions.py --scope <id>` prints a `provisional …` or `ratified …` entry in scope as binding, verbatim; its summary line gains `; provisional and binding: D<n>, …` only where one is printed; a `reverted …` entry is left out and listed with the overridden ones as `D<n> (reverted <date>)`. A log without them prints exactly what it printed | e1 D1 provisional, D2 ratified, D3 reverted, all `Scope: S1`: D1 and D2 printed, the summary names D1 provisional and `D3 (reverted 2026-10-09)` left out · e2 a log of standing entries: output byte-equal to before |
| **R8** the completion audit's refusal | AC-S27-14; D197 | `python3 scripts/provisional.py audit [--feature <name>]` reads the feature's `decisions.md` (`--feature` required only where `specs/` holds several) and, where any entry's `Status` starts with `provisional`, prints `cruise: parked: ratify D<n>` naming the lowest-numbered one and exits 3; otherwise prints `provisional: no unratified provisional decision in specs/<f>/decisions.md`, exit 0. `ratified`, `reverted`, `overridden by …` and `standing` never hold it. The command's completion audit runs it before `cruise: done` and ends on its line | e1 D4 and D2 provisional: `cruise: parked: ratify D2`, exit 3 · e2 D2 `ratified 2026-10-09`, D4 `reverted 2026-10-09`, D5 `overridden by human 2026-10-09`: exit 0 · e3 no log: exit 0, says none · e4 two features and no `--feature`: exit 2 naming both |
| **R9** the ladder and the iteration guard in `--set` | AC-S27-11, -13; D196 part 3, D201 | The rungs: `recommended-first`, `skipper-always` 0; `provisional-shadow` 1; `provisional-advisory` 2; `provisional` 3. `cruise.py --set decide=<v>` from the file's current value refuses a step up of more than one rung, in one line, `` `decide` moves one mode at a time: set `<next>` first ``, exit 1, file unchanged; any step down, a one-rung step up and a move between the two rung-0 values are written. With `CRUISE_ITERATION` in the environment, any `--set decide=…` is refused in one line naming `/cruise-settings` as a person's command, file unchanged; other keys are not touched by this rule. `check()` still accepts every one of the five values whatever the file held before | e1 `recommended-first` → `provisional`: refused naming `provisional-shadow`, file bytes equal · e2 `recommended-first` → `provisional-advisory`: refused naming `provisional-shadow` · e3 `provisional-shadow` → `provisional`: refused naming `provisional-advisory` · e4 `recommended-first` → `provisional-shadow` → `provisional-advisory` → `provisional`, each written · e5 `provisional` → `recommended-first`: written; `provisional` → `provisional-shadow`: written · e6 `skipper-always` → `provisional-shadow`: written · e7 `CRUISE_ITERATION=4`, `--set decide=recommended-first`: refused naming `/cruise-settings`, file bytes equal; `--set max_hours=2` still written · e8 a hand-edited file holding `provisional`: `--check` passes |
| **R10** the mode entry and the skipping hand edit | AC-S27-12; D196 part 4 | `cruise.py mode [--feature <name>]` compares `decide` with the last mode entry of the feature's log — the last heading `## D<n> — decide moved from <a> to <b>`, whose `<b>` is the recorded mode. Equal: prints `cruise: decide is <v>, as D<n> recorded`, exit 0. No mode entry: prints the entry to append with `<a>` `unrecorded`, no order check. Different by a step R9 would write: prints the entry to append — heading with the next number, `Decided by: human`, `Scope: global`, `Written to: .specify/cruise.json`, its **Decision** citing the short hash of the commit that last changed `.specify/cruise.json`, or `uncommitted at <instant>` where `git status` shows it changed — exit 0. A forward skip of more than one rung: prints `cruise: parked: decide=<v> skips <next>; set it through /cruise-settings`, exit 3, and nothing to append. The command runs it at the start of every iteration, appends the printed entry (scored with `reversibility.py` as every entry is) and ends on the park line where printed | e1 a log whose last mode entry says `provisional-shadow`, the file `provisional-shadow`: `decide is …`, exit 0 · e2 the file committed at `provisional-advisory`: an entry `decide moved from provisional-shadow to provisional-advisory`, number = last + 1, citing that commit's hash, passes `check-decisions` once appended · e3 uncommitted change: `uncommitted at <instant>` · e4 no mode entry, file `recommended-first`: `decide moved from unrecorded to recommended-first` · e5 last mode `recommended-first`, file hand-edited to `provisional`: the park line naming `provisional-shadow`, exit 3 · e6 last mode `provisional`, file `recommended-first`: an entry (a step back) |
| **R11** five values, one default, one sentence, everywhere | AC-S27-16; D196 part 1 | The server-side `SETTINGS`, the toolkit's `CHOICES` (and `CONTROLS["decide"]`), the generated `commands/cruise-settings.md` table, `commands/cruise.md`'s protocol and `docs/cruise.md`'s table list the same five values in the same order, the default `recommended-first`, and the one sentence *Change it to `provisional-shadow` when always-ask questions are stalling slices and you want to see which ones would have been taken provisionally before letting any be; move on to `provisional-advisory`, then `provisional`, once the shadow lines read right.* `provisional.py`'s accepted values equal them. The two tests that assert the old refusal text read the new list | e1 the four sources compared, values and order · e2 a generated project's `.specify/cruise.json` still says `recommended-first` · e3 the sentence in `CONTROLS`, the settings command and `docs/cruise.md` · e4 `cruise.py --set decide=nope` names the five |
| **R12** the command and the briefs say it | AC-S27-5 (last clause), -6, -10 (advisory park), -15 (first half); D198, D200, D201 | `commands/cruise.md`'s skipper protocol gains the provisional paragraph: only the skipper takes an always-ask item provisionally; it scores the tier first, then runs `python3 scripts/provisional.py status` with `.specify/cruise.json`'s `decide`, writes the lines it prints, and quotes the owner-brief line the item falls under; every other question is decided as under `recommended-first`; a question about a gate, a check or CI is never provisional (D200); an enforced provisional decision is not a block — no bosun, no ⛔, the skipper's `status` `decided`; every commit made under it carries the trailer `Decision: D<n>` and the host puts that in every implement brief; under advisory the park line is the verb's; a person's `accept` through `/cruise-tell` is written as a `Decided by: human` entry taking the recommendation. *Before anything* runs `cruise.py mode`; the completion audit runs `provisional.py audit` before `done`; *What holds throughout* says the run never sets `decide`. The skipper's brief (`agents/drive-skipper.md`) says the same from its side. `DECISION_ENTRY` shows the three new `Status` forms, `Revert:` and the mode line; the stop table's approval row names the exception; the owner-brief template's *Always ask a person* gains one sentence naming the exception; the settings command's words map "take easy decisions provisionally" to `decide=provisional-shadow` first. `cruise.py` stays ≤ 350 lines: the text lives in a new `cruise_provisional.py` | e1 a generated project: `commands/cruise.md` names `scripts/provisional.py status`, `provisional.py audit`, `cruise.py mode`, `Decision: D<n>`, `accept`, "no bosun", "only the skipper" · e2 `agents/drive-skipper.md` names the verb, the quoted owner-brief line, "a gate, a check or CI", `decided` · e3 `.specify/product-owner.md` holds `DECISION_ENTRY` with `provisional · ratify by`, `Revert:` and `Provisional (shadow`, and the always-ask sentence · e4 the stop table's approval row names `decide: provisional` · e5 an adopted repository: the same text with `delivery/scripts/provisional.py` · e6 `wc -l src/slipwai/project/cruise.py` ≤ 350 |
| **R13** a project made before | AC-S27-17; D196 | A project generated by the factory at `5f4fc00`, migrated by this checkout: `scripts/provisional.py` arrives, `.specify/cruise.json` is byte-unchanged, `make check-agents`, `make check-decisions` and `make verify` pass. The fragment's first line is `MINOR`; its one **Catch-up.** paragraph stands alone and names the three new values, that they are off by default and the file is untouched, the one-rung-at-a-time rule, and that a provisional entry is ratified by hand (`Status: ratified <date>`, or reverted and `reverted <date>`) until `S28` ships, since the run will not say `done` while one is unratified | e1 the migration above · e2 the fragment's words |

The demo (a generated project's `make verify`, the verbs as the actor runs them; quickstart.md) is the host's
`drive-hand` stage, after this delegate returns. Every criterion is covered: 1 (R1 e1–e3), 2 (R1 e4), 3 (R1 e6),
4 (R1 e5), 5 (R1, R12), 6 (R1 e9–e10, R12), 7 (R6), 8 (R3), 9 (R4), 10 (R2, R5, R12), 11 (R9), 12 (R10, R12),
13 (R9 e7), 14 (R8, R12), 15 (R7, R12), 16 (R11), 17 (R13).

## Technical Context

**Language/Version**: Python ≥ 3.10 standard library only for toolkit scripts (a project runs them); Python 3.11+
for `src/slipwai/`.
**Primary Dependencies**: none new.
**Storage**: none new; the lines live in `decisions.md` (append-only); `.specify/cruise.json` gains no key.
**Testing**: `unittest` in `tests/`; scratch projects in temporary directories, scripts as `python3 -B` subprocesses;
the released checker taken from git as `test_decisions_scope_gate.released_checker` does; the old factory with
`git archive 5f4fc00` as `test_reversibility_migrate` does; the runner's `--set` and `mode` run against a scratch
project holding `scripts/agents/` copied from the toolkit and a scratch git repository. Fakes are files in the test
tree. No mocking framework. Each new or touched file under `tests/` and `src/` ≤ 350 lines.
**Target Platform**: wherever a generated project's agents run; Linux and macOS for the factory's tests.
**Performance Goals**: none; the gate's extra work is linear in the log and runs only for a log with a new form.
**Constraints**: D65 (old logs keep their answer); D62/D201 (the run never sets `decide`); D176 (no line is hard);
FR-033 via D195/D200; `measures.py` unchanged (its `ratified`/`reverted` reading already matches, D197 rule 4);
S26's rules version 1 unchanged.
**Scale/Scope**: one new toolkit script, edits to `check-decisions.py` and `agents/cruise.py`, one new generator module
and five edited, one doc page, one fragment.

## Constitution Check

The factory's constitution (`.specify/memory/constitution.md`):

- **I. A generated project owns its files and passes its own gate** — `cruise.json` is never rewritten (no new key);
  a log written before passes unchanged (R6, R13); the new script reaches a project only through `migrate`.
- **III. Simplicity** — no new setting key; one script serves the verb, the audit and the gate's checks; the gate
  loads it only for a log that needs it.
- **V. Acceptance-driven** — every example enters through a verb, the gate, `cruise.py`, or `generate`/`migrate`.
- **VII. Auditability** — every refusal is one line naming the entry and the field, or the setting and the next rung;
  a mode move is a `Decided by: human` entry citing the commit; a provisional entry names its revert by trailer.
- **XIV. Agent-generated change** — the run can never widen its own authority: `--set decide` refuses inside an
  iteration, a skipping hand edit parks, and only enforced mode — set by a person, one rung at a time — takes
  anything provisionally, never a `hard`, flag, CI or migrate-propagated item.

## Structure Decision

One deployable, `slipwai-graph` (`kind: tool`, D3). The change lands under `assets/toolkit/` and `src/slipwai/` and
reaches this repository only through a person's `slipwai migrate` (D9, D130); this checkout's `delivery/` is not
edited, so its own gate and runner are untouched.

**Toolkit (what a project runs)**

- `assets/toolkit/scripts/provisional.py` *(new)*: `DECIDE` (the five values, in order), `ASKS`, `HELD_FACTS`,
  `ratify_by()`, `status_lines()` (R1, R2), `check_log()` (R3–R5, given the gate's parsed entries and S26's
  `parse_line`), `unratified()` (R8), and `main()` with `status` and `audit`. Loads `reversibility.py` beside it by
  path, bytecode off, only in `main`. Every `read_text` names `encoding="utf-8"`.
- `assets/toolkit/scripts/check-decisions.py`: `STATUS`'s finding skips a status whose first word is a new one (left to
  the module); `provisional_findings(path)` beside `reversibility_findings` loads the module only when the log carries
  a new form; `scope_verb` treats `reverted …` as left out and counts provisional entries (R7); the docstring gains
  the forms.
- `assets/toolkit/scripts/agents/cruise.py`: `CHOICES["decide"]` and `DEFAULTS` order, `CONTROLS["decide"]` with the
  sentence, `RUNGS`, the refusal in `--set` (R9), the `mode` verb (R10), the docstring's usage line.
- `assets/toolkit/scripts/verify_scoped/table.py` and `tests/test_verify_scoped_table_held.py`: only where the scan
  says a new literal needs a row or an exemption (S26's `6cfe48b`).

**Factory source**

- `src/slipwai/project/cruise_provisional.py` *(new)*: `DECIDE_VALUES`, `DECIDE_CONTROLS` (with the sentence),
  `PROVISIONAL_VERB`, `AUDIT_VERB`, `MODE_VERB`, the command's provisional paragraph, the audit sentence, the
  mode-check sentence, the skipper's paragraph, the stop-row exception and the settings-words sentence.
- `src/slipwai/project/cruise.py`: the `decide` row from the new module; interpolations (net ≤ +9 lines; ≤ 350).
- `src/slipwai/project/cruise_record.py`: `DECISION_ENTRY`'s `Status` line, `Revert:` and the mode line.
- `src/slipwai/project/cruise_agents.py`: the skipper's paragraph, interpolated.
- `src/slipwai/project/cruise_stops.py`: the approval row's exception.
- `src/slipwai/project/decisions.py`: one sentence under *Always ask a person*, one under *What the record looks like*.
- `docs/cruise.md`: the `decide` row, the sentence, row 12's exception, a short *Provisional decisions* section.
- `changelog.d/provisional-decisions.md` *(new)*: MINOR, one standalone **Catch-up.** paragraph.

Not changed: `VERSION`, `catalog.json`, `reversibility.py`, `measures.py`, `seeded.py`, `delivery/` in this checkout,
every record under `specs/` but this slice's folder.

**Tests** *(new modules, each ≤ 350 lines)*

- `tests/provisional_fixture.py` — the scratch project (three scripts), `status(...)`, `audit(...)`, `gate(...)`, an
  entry builder with `Status`, `Revert`, `Reversibility` and mode lines.
- `tests/test_provisional_status.py` — R1, R2.
- `tests/test_provisional_gate.py` — R3, R4, R5.
- `tests/test_provisional_scope_audit.py` — R7, R8.
- `tests/test_decisions_gate_differential.py` — R6 (extended; 134 lines now).
- `tests/test_cruise_decide_ladder.py` — R9, R10.
- `tests/test_cruise_provisional_writers.py` — R11, R12.
- `tests/test_provisional_migrate.py` — R13.
- `tests/test_cruise_runner.py:116`, `tests/test_cruise_sweep.py:55` — the refusal text's value list (R11).

## Pin

Generated code: the factory's own tests are the pin, and no code that predates the method is changed. The gate's
behaviour on logs without the new forms is pinned by `tests/test_decisions_gate_differential.py` and
`tests/test_decisions_scope_gate.py` against `596740f`; `--set`'s by `test_cruise_runner`, `test_cruise_sweep`; the
command's text by `test_cruise`, `test_cruise_record`, `test_cruise_scope_writers`, `test_reversibility_writers`.
They run before the first increment and after the last, with every `test_verify_scoped_*`, `test_verify_stamp_scan`,
`test_toolkit`, `test_utf8_io`, `test_changelog`, `test_assets_bytecode` and the `test_decisions_*`,
`test_reversibility_*` and `test_cruise*` modules (`make test SINCE=adopt-method TESTS="…"`).

## Plan decisions (taken inside D195–D201; for the host to overrule)

None of these is a product question the artifacts leave open; each is the narrowest reading of a decided entry,
recorded so the host can overturn it.

- **P1 — `--ask` has five kinds, not a yes/no flag** (research R-2). AC-S27-6 makes a fact, a MUST and a release
  unavailable whatever `decide` says; a yes/no flag cannot tell them from an approval, and the verb is where D201 puts
  the table.
- **P2 — `blocks (<fact>=yes)` in a rehearsal line** (research R-3). AC-S27-10's grammar names `blocks (hard)`; a
  `guarded` item held back by `flag_default=yes` would otherwise have to claim a tier it does not have.
  *For the host:* AC-S27-10's `<…, or blocks (hard)>` may read `<…, or blocks (hard) or blocks (<fact>=yes)>`.
- **P3 — the first mode entry's heading is `decide moved from unrecorded to <v>`** (research R-5), one grammar for
  every mode entry; D196 asks for the record but names no heading.
- **P4 — a `Revert:` line on a non-provisional entry in an otherwise old log is refused** (AC-S27-8 over AC-S27-7;
  D65's carve-out for a label only this release defines, as S26's R5 e2 did). Stated in the differential test.
- **P5 — advisory's one word is `accept`** (research R-6): the next iteration writes the person's answer as a
  `Decided by: human` entry taking the recommendation, `Status: standing`, and the `unavailable` entry's `Status`
  becomes `overridden by D<m>`, the route a later decision already takes.
- **P6 — the audit reads one feature's log**; with several and no `--feature`, it refuses as `--scope` does.

## Open questions

Product questions met in planning: none — D195–D201 settle every one the criteria raise.

- **Q1 (open, raised by converge pass 1 at `76927e4`; the slice is blocked on it before pass 2) — where does a
  feature's log with no mode entry take its baseline?** D196 part 4: *"A log with no mode entry: the first iteration
  records the current mode as it finds it, with no order check, because the earlier mode is unknown."* Mode entries
  are per feature log, so every new feature — and every project before its first iteration — accepts a hand edit
  straight to `provisional` without the park AC-S27-12 promises for a skip. Observed: a second feature's
  `cruise.py mode` printed `decide moved from unrecorded to provisional`, exit 0.
  - (a) Keep D196 part 4 as written: the first entry of each log is unchecked.
  - (b) Read `unrecorded` as rung 0: before this release only rung-0 values (`recommended-first`, `skipper-always`)
    existed, so a log with no mode entry was at rung 0, and a first reading above `provisional-shadow` parks.
  - (c) **Recommended:** take the last mode entry across every feature's `decisions.md` (by its `When`), falling back
    to (b) where no log has one. It closes the hole without making a project that already reached `provisional` in one
    feature climb again in the next; one more file read in `mode`, no new setting.

  Either (b) or (c) overrides D196 part 4's "no order check" and needs the host's entry; (c) also changes R10 e4's
  example and AC-S27-12's wording ("the last mode entry in the feature's log" → "in any feature's log").
