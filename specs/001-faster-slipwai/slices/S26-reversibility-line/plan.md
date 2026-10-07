# Implementation Plan: S26-reversibility-line — every decision says how hard it would be to take back

**Branch**: `slice/S26-reversibility-line` (worktree `../slipwai-graph-S26-reversibility-line`, cut from
`adopt-method` at `063c187`; the local branch is the claim, no push — D129) | **Date**: 2026-10-07 |
**Spec**: [spec.md](../../spec.md), *Slice acceptance criteria* → `### S26-reversibility-line` (AC-S26-1 … AC-S26-16)

**Input**: FR-029, FR-051, FR-056 (FR-057 is S39's, already built) in [spec.md](../../spec.md); the slice's split and
graph rows in [story-split.md](../../story-split.md) (S27's and S28's rows out of scope); D174–D178 with D54, D60,
D62, D65, D132, D159, D168 in [decisions.md](../../decisions.md); ADR 0007 at Proposed
(`delivery/docs/adr/0007-reversibility-scored-from-declared-facts.md`, never accepted by the run); the gaps report
`/home/noahc/math/.cruise27/gaps-S26.md`; the owner brief `.specify/product-owner.md`; `AGENTS.md` (MINOR, one
fragment). Written by cruise iteration 27's plan stage, inside the slice's `drive-slice` delegate (host model).

## Summary

A decision entry gains an optional `- **Reversibility:**` line: the tier (or a one-step-at-a-time escalation chain),
the version of the rules that scored it, and the declared facts as `key=value`. One shipped verb,
`scripts/reversibility.py`, turns facts plus the entry's `Scope:` (its dependants) and its `Written to` paths into
the line, fail-closed; the same module, loaded by path beside `check-decisions.py` only when a log carries the new
labels, lets the gate re-derive the tier under the named rules version and refuse a malformed or contradicting line,
note an entry missing the line after one that has it, and check a `Proposed rule:` line's citations. Whether a path
is one `migrate` propagates is read from a committed list: `delivery/.written` (or the root `.written`) in an adopted
repository, and a new `.slipwai/propagated` that `generate` writes and `migrate` carries in a generated project
(D175). `DECISION_ENTRY`, the cruise command, the owner-brief template and the skipper's brief show the line and
point at the verb; the skipper's brief gains FR-056's one-tier escalation and D178's proposed rule, and the
dispatch text adds the feature's entry headings to every skipper brief. `measures.py` is not touched. MINOR, one
fragment `changelog.d/reversibility-line.md`; `VERSION` stays `1.6.0.dev0`.

## The example map

Rules are numbered; each is one RED-GREEN-REFACTOR increment (constitution V). Grammar, facts and the rule table
are in [data-model.md](data-model.md); the reasons in [research.md](research.md). *A scratch project* is a temporary
directory holding `project.json`, `scripts/check-decisions.py` and `scripts/reversibility.py` copied from
`assets/toolkit/scripts/`, `README.md`, and `specs/f/decisions.md`; scripts run as subprocesses with `python3 -B`.

| Rule | Criteria | What it says | Examples |
|---|---|---|---|
| **R1** the verb scores declared facts | AC-S26-1, -2, -3, -4, -5, -6, -7 | `python3 scripts/reversibility.py --scope <value> [--written-to <value>] [--raise guarded\|hard] <key>=<value>…` prints the whole `- **Reversibility:** …` line on stdout (facts in the closed order of data-model.md), exit 0, and on stderr one line naming the rules that fired. Rules version 1 as data-model.md's table. A missing fact is written `<key>=missing`; an unaccepted value is written as given; both score `hard`. Any other key (`size`, `urgency` included), a key given twice or an argument not `key=value` is usage: one stderr line naming it, exit 2, nothing on stdout. Entries with no commits are scored only from what is declared; the `Written to` paths can only raise (R2) | e1 AC-S26-1's facts, `--scope S26-reversibility-line`: `easy` · e2 each of the seven hard facts `yes` alone: `hard`, seven tests · e3 `rollback_complexity` `days`, `needs-migration`: `hard`; `hours`: `guarded`; `trivial`: `easy` · e4 `behind_flag=no`: `guarded`; `no-code`: `easy` · e5 `flag_default=yes`: `guarded` · e6 scope of two ids: `guarded`; `global`: `hard`; an unreadable scope: `hard` · e7 `schema` omitted: `hard`, the line carries `schema=missing`; `rollback_complexity=weeks`: `hard`, the line carries it · e8 the same facts plus `size=large`, and plus `urgency=high`: exit 2, stderr names the key, stdout empty · e9 the D54 fixture (`ci_workflow=yes migrate_file=yes behind_flag=no-code`, `Written to` two records, no commits): `hard` · e10 `--raise hard` from `easy`: `easy → guarded → hard`; `--raise guarded` from `hard`: exit 2, a tier is never lowered |
| **R2** the committed list raises `migrate_file` | AC-S26-8, -7 | The list is `<delivery>/.written` where `project.json`'s `origin` is `adopted` (`.written` at the root where `layout.delivery` is `.`), else `.slipwai/propagated`; one path per line. A `--written-to` path on the list makes the written `migrate_file` `yes` whatever was declared, and says so on stderr. With no list, a declared `no` is written `migrate_file=no-list` (a value the fact does not accept, so `hard`, D175 condition 3); a declared `yes` stays | e1 generated, `--written-to "\`scripts/check-decisions.py\`"`, list names it, `migrate_file=no`: line carries `migrate_file=yes`, `hard` · e2 adopted (`origin: adopted`, `layout.delivery: delivery`), `delivery/.written` names the path: the same · e3 a `Written to` of `specs/f/spec.md` only: `migrate_file=no` stands · e4 no list: `migrate_file=no-list`, `hard` · e5 a declared `yes` with no path on the list: `yes`, never lowered |
| **R3** `generate` writes the list, `migrate` carries it | AC-S26-8, D175 | A generated project (no adoption) gets `.slipwai/propagated`: every path the factory assembles under `scripts/`, `skills/`, `commands/`, `agents/`, `.specify/`, plus `Makefile`, `init` and the list itself, sorted, one per line. Not `docs/`, `project.json`, application code or the root files a project owns (research R-7). An adopted repository gets no such file (its `.written` is unchanged). `replay` regenerates it, so `migrate` rewrites it in the merge that carries the files it names | e1 a generated project, both profiles: the list exists, names `scripts/check-decisions.py`, `scripts/reversibility.py`, `commands/cruise.md`, `.specify/product-owner.md`, `Makefile`, and names no path under `apps/`, `docs/`, nor `README.md` · e2 `slipwai replay` of it reproduces the list byte for byte · e3 an adopted repository: no `.slipwai/propagated`, `.written` as before · e4 the path the toolkit module reads equals `assets.PROPAGATED` |
| **R4** the gate holds the line | AC-S26-9 | In `make check-decisions`, an entry's `Reversibility:` line is accepted when well formed and its first tier equals what the named rules version derives from its facts, its `Scope:` and its `Written to` (R2's list check, as a refusal: `migrate_file=no` with a listed path, or with no list). Otherwise one finding per fault naming the entry (`<file>:<line>: D<n>`) and the field: a tier word that is not one of the three; a skipped, repeated or lowering step; an unknown rules version; an unknown or repeated key; a token that is not `key=value`; a second `Reversibility:` line; a first tier differing from the derived one (naming the rules that fired) | e1 a well-formed `easy` line on an AC-S26-1 entry: exit 0 · e2 `Reversibility: medium …`: refused, names D1 and `Reversibility` · e3 `easy → hard`: refused as a skipped step; `hard → guarded`: refused as lowering · e4 `rules 9`: refused · e5 `size=large` on the line: refused naming `size` · e6 two lines: refused · e7 `easy` with `ci_workflow=yes`: refused, names `ci_workflow` · e8 `hard` with `schema=maybe`: accepted · e9 `migrate_file=no` with a `Written to` on the list: refused naming `migrate_file` · e10 an escalation `easy → guarded → hard` whose first tier is right: accepted |
| **R5** old logs get the earlier answer; a missing line is a note | AC-S26-10 | A log with no `Reversibility:` and no `Proposed rule:` line never loads `reversibility.py`: exit code, findings and stdout less `note:` lines equal the checker released at `596740f`'s (the differential test extended). In a log that has the line, each later entry without it gets one `check-decisions: note: <file>:<line>: D<n> has no \`Reversibility:\` line after an entry that has one; score it with python3 scripts/reversibility.py`, exit unchanged; entries before the first line get none | e1 every case of `test_decisions_gate_differential` plus this repository's own log, through a scratch project that also holds `reversibility.py`: equal to the released checker · e2 a log with an unknown label before this release (`- **Reversibility:** whatever` read by neither): the released checker passed it; the gate now refuses it, and that is the only log shape whose answer moves — it holds a line only this release defines (D65's carve-out; stated in the test) · e3 D1 with the line, D2 without: exit 0, one note naming D2 and the verb · e4 D1 without, D2 with: no note |
| **R6** old lines under newer rules | AC-S26-11, FR-051 last sentence | The gate re-derives under the version the line names; every shipped version stays. A test freezes rules version 1 (a digest of its tier over every fact vector of the closed value sets and the three dependants classes), so a shipped version is never edited, only added to | e1 a fake in the test tree: `reversibility.py` copied with a version 2 that makes `behind_flag=no` `hard`; a log with a version-1 `guarded` line for it passes, and a version-2 line saying `guarded` for the same facts is refused · e2 the digest of version 1 equals the one written in the test |
| **R7** a proposed rule cites two standing entries | AC-S26-15 (gate half) | A `- **Proposed rule:** … (same shape as D<a>, D<b>)` line is accepted when it cites at least two distinct ids other than its own entry's, each the heading of an entry in the same log whose `Status` is `standing`; otherwise one finding naming the entry and `Proposed rule`. An entry without the line is never refused | e1 D3 citing D1, D2 standing: exit 0 · e2 citing D1 only: refused · e3 citing D1, D9 (absent): refused naming D9 · e4 citing D1, D2 with D2 `overridden by D3`: refused naming D2 · e5 citing D3 and D1 from D3: refused (its own id does not count) · e6 no entry has the line: nothing new |
| **R8** the shape and the briefs write it | AC-S26-12, -14, -15 | `DECISION_ENTRY` gains `- **Reversibility:** <tier> · rules <n> · <facts> — from python3 scripts/reversibility.py` after the `Confidence` line and `- **Proposed rule:** …` as an optional line; so the generated `commands/cruise.md` and `.specify/product-owner.md` show both. The cruise command's skipper protocol says the session runs the verb for every entry it writes and adds the feature's entry headings (each `D<n>` with its heading, Stage and Scope) to every skipper brief. The skipper's brief says: run the verb with the declared facts; escalate one reversibility tier at a time with `--raise`, writing each step, never lowering a computed tier, never leaving a question in a diff or a note instead of escalating; after three standing entries of the feature decided by the same reason, add the `Proposed rule:` line citing the earlier ids, decide the question anyway, never edit the owner brief; out-of-scope headings are evidence for the count, never binding. Generated and adopted projects both carry the text (paths re-pointed in adopted) | e1 a generated project: `commands/cruise.md` and `.specify/product-owner.md` hold `DECISION_ENTRY` with both lines · e2 the skipper brief (`agents/drive-skipper.md`) names the verb, `--raise`, `one tier at a time`, `never lowers`, `Proposed rule:`, `never edits` the owner brief · e3 the cruise command tells the host to run the verb and to add the headings list · e4 an adopted repository: the same text with `delivery/scripts/reversibility.py` |
| **R9** S39's reader reads the verb's lines | AC-S26-13 | Lines the verb writes, chains included, are read by `measures.decision_entries` / `decision_health` with the tier the verb computed and an escalation exactly where the chain reaches `hard`; `measures.py` is unchanged | e1 twenty entries carrying verb output, four of them `--raise hard`: tiers and escalation share as computed (20 %) · e2 `easy → guarded` is not an escalation to hard · e3 `git diff 063c187 -- assets/toolkit/scripts/agents/measures.py` is empty |
| **R10** a project made before | AC-S26-16 | A project generated by the factory at `063c187`, with a decisions log written then (no line), migrated by this checkout: `scripts/reversibility.py` and `.slipwai/propagated` arrive, `make check-decisions` passes as before, the owner brief is unchanged, and an entry appended with the verb's line passes. The fragment's first line is `MINOR`; its one **Catch-up.** paragraph stands alone and names the line, the verb, the committed list, the note for a missing line, and that the owner brief keeps the old shape until edited by hand | e1 the migration above · e2 the fragment's words |

The demo (full `make verify` on a migrated project; AC-S26-16's last clause as an actor would see it) is the host's
`drive-hand` stage, after this delegate returns. Every criterion is covered: 1–7 (R1, R2), 8 (R2, R3), 9 (R4),
10 (R5), 11 (R6), 12 (R8), 13 (R9), 14 (R1 e10, R4 e3, R8), 15 (R7, R8), 16 (R10).

## Technical Context

**Language/Version**: Python ≥ 3.10 standard library only for the toolkit script (a project runs it); Python 3.11+
for `src/slipwai/`.
**Primary Dependencies**: none new.
**Storage**: none new beyond the committed list file; the line lives in `decisions.md` (append-only).
**Testing**: `unittest` in `tests/`; scratch projects in temporary directories, scripts run as subprocesses with
`python3 -B`; the released checker taken from git as `test_decisions_scope_gate.released_checker` does; the old
factory taken with `git archive` as `test_benchmark_elapsed_migrate.old_factory` does. Fakes are files written in the
test tree (a copied `reversibility.py` with a version 2). No mocking framework. Each new file ≤ 350 lines.
**Target Platform**: wherever a generated project's agents run; Linux and macOS for the factory's tests.
**Performance Goals**: none; the gate's extra work is linear in the log.
**Constraints**: D65 — a log without the new labels gets the earlier checker's answer, and no old line is re-scored
under newer rules; D176 — absence is a note, never a refusal; D168 — `SPELLING` unchanged; D62 — the run never
sets `decide`; FR-051 — fail-closed, size and urgency never move a tier.
**Scale/Scope**: one new toolkit script, one gate edit, four generator modules plus one new, one fragment.

## Constitution Check

The factory's constitution (`.specify/memory/constitution.md`):

- **I. A generated project owns its files and passes its own gate** — a log written before passes unchanged (R5,
  R10); the new file reaches an existing project only through `migrate`, which the maintainer runs. The starters'
  own `make verify` is the host's to run at the merge root; here the touched modules and
  `make test TESTS="test_toolkit test_utf8_io test_changelog test_assets_bytecode"` run.
- **III. Simplicity** — one module serves the verb and the gate; the gate loads it only when needed; no new
  dependency.
- **V. Acceptance-driven** — every example enters through the verb, the gate or `slipwai generate`/`migrate` as a
  subprocess.
- **VII. Auditability** — every refusal is one line naming the entry and the field; the verb names the rules that
  fired; the line names its rules version.
- **VIII. A persisted schema is a contract** — the line's grammar is versioned by `rules <n>`, and a shipped version
  is frozen by a test (R6).
- **XIV. Agent-generated change** — the decisions this plan takes inside D174's delegation (dependants mapping,
  `no-code`, the list's contents) are in research.md and under *Open questions* for the host to overrule.

## Structure Decision

One deployable, `slipwai-graph` (`kind: tool`, D3). The change lands under `assets/toolkit/` and `src/slipwai/` and
reaches this repository only through `slipwai migrate` (D130); this checkout's `delivery/` is a control and is not
edited, so its own gate (`delivery/scripts/check-decisions.py`) is untouched and its `decisions.md` is not migrated.

**Toolkit (what a project runs)**

- `assets/toolkit/scripts/reversibility.py` *(new, ≤ 350 lines)*: `FACTS` (the closed list and accepted values),
  `RULES = {1: …}` (each a function from facts and dependants class to `(tier, fired)`), `parse_line()`,
  `score()`, `propagated(root)` (the list for the layout, or None), `check_log()` (the gate's findings and notes for
  one parsed log, given the gate's own `scope_tokens` and `STATUS` so readings cannot drift), and `main()` (the verb).
  Every `read_text` names `encoding="utf-8"`.
- `assets/toolkit/scripts/check-decisions.py`: the module docstring gains the line and the proposed rule; a loader
  shared with `hand_backs_module()` (`sibling(name)`); `gate()` calls `check_log()` for each log whose text carries a
  `- **Reversibility:**` or `- **Proposed rule:**` label, printing its notes beside `scope_notes` and adding its
  findings. Nothing else in the file moves.

**Factory source**

- `src/slipwai/assets.py`: `PROPAGATED = ".slipwai/propagated"` beside `NOTES`.
- `src/slipwai/project/propagated.py` *(new)*: `propagated_file(files)` — the list's text from the assembled files.
- `src/slipwai/scaffold.py`: where no adoption is given, the list is added after `layout.relocate` (and before the
  adoption cut), so `replay` regenerates it.
- `src/slipwai/project/cruise_record.py`: `DECISION_ENTRY`'s two lines; `REVERSIBILITY_RULE` (the host's sentence:
  run the verb, add the headings list to every skipper brief).
- `src/slipwai/project/cruise_agents.py`: `SCORE_VERB = "python3 scripts/reversibility.py"`; the skipper's brief.
- `src/slipwai/project/cruise.py`: interpolates `REVERSIBILITY_RULE` after the entry's shape (two lines; the module
  is at 341).
- `src/slipwai/project/decisions.py`: one sentence in *What the record looks like* naming the verb.
- `src/slipwai/migrate.py`: unchanged — `replay` regenerates the list and the merge carries it (research R-7).
- `changelog.d/reversibility-line.md` *(new)*: MINOR, one standalone **Catch-up.** paragraph.

Not changed: `VERSION`, `catalog.json`, `measures.py` (AC-S26-13), `DECISION_FIELDS`, `delivery/` in this checkout,
every record under `specs/` but this slice's folder, and S07's (`verify_scoped/`, `check-ux-gates.py`) and S43's
(`tests/` declarations, helper moves) files.

**Tests** *(new modules, each ≤ 350 lines)*

- `tests/reversibility_fixture.py` — the scratch project (both scripts, `project.json` with or without `origin`,
  a list), `score(...)` and `gate(...)` as subprocesses, an entry builder with a line.
- `tests/test_reversibility_score.py` — R1, R2.
- `tests/test_reversibility_gate.py` — R4, R7.
- `tests/test_reversibility_versions.py` — R5 (e2–e4), R6, R9.
- `tests/test_reversibility_writers.py` — R3, R8.
- `tests/test_reversibility_migrate.py` — R10.
- `tests/test_decisions_gate_differential.py` — R5 e1: the same cases through a scratch project that also holds
  `reversibility.py` (the module is 112 lines).

## Pin

Factory code needs no separate pin: its existing tests are the pin. The gate's current behaviour on logs without
the new labels is already pinned by `tests/test_decisions_gate_differential.py` and
`tests/test_decisions_scope_gate.py` against the checker released at `596740f`; they run before the first increment
and after the last, beside `test_decisions_scope*`, `test_hand_backs_*`, `test_cruise_scope_writers`,
`test_cruise_record`, `test_cruise`, `test_replay`, `test_adopt`, `test_benchmark_feature` and the toolkit set
(`test_toolkit test_utf8_io test_changelog test_assets_bytecode`).

## Open questions

None blocks the plan; each is written for the host to number or overrule, and the plan proceeds on the
recommendation.

**Q1 — Which paths does a generated project's list name?** D175 condition 2 says both "the same contents as an
adopted repository's list" and "only the factory-owned method material … the toolkit scripts, `.specify/` files,
agents, skills, commands and their `Makefile` wiring … not the starter application code". An adopted `.written`
also names `docs/` (in an adopted repository, `delivery/docs/architecture.md`) and `project.json`. In a generated
event-modelling project, almost every decision writes `docs/event-model/model.yaml`; listing `docs/` would score
nearly every such decision `hard`, the outcome D175's *Why* rules out. **Recommend**: the enumerated categories
only (`scripts/`, `skills/`, `commands/`, `agents/`, `.specify/`, `Makefile`, `init`), leaving an adopted
`.written` as `adopt` writes it; the reader serves both through one format.

**Q2 — Extension-projected files.** `migrate`'s refresh re-runs an elected extension's projector after the merge
(`src/slipwai/migrate.py:185-244`), and those files are not in `project_files`, so neither layout's list names
them (an adopted `.written` does not either). D175's reversal condition names extension files *not recorded in*
`.slipwai/extensions.json`; elections are recorded there, so the condition does not fire. **Recommend**: leave them
off; the declared `migrate_file` governs them, and the list only ever raises.

**Q3 — A `Proposed rule:` citing an entry that is later overridden.** AC-S26-15 refuses a cited id that is not a
standing entry. Read literally, a person overriding D<a> makes the gate refuse a later entry D<z> that cited it,
whose only remedy is editing D<z>. **Recommend**: implement AC-S26-15 as written (R7 e4) and let the host decide
whether a person's override should turn that refusal into a note.

**Q4 — How dependants map to a tier** (D174 rule 2 left it to planning). **Taken**: one slice id fires nothing, two
or more `guarded`, `global` or no readable `Scope:` `hard` (research R-2). A person may prefer `global` as `guarded`.
