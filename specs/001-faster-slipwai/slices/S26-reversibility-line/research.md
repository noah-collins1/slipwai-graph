# Research: S26-reversibility-line

Every claim names the artefact it was read from. No `.codegraph/` exists in this checkout, so every code lookup was
a text search or a file read, and says so where it matters. The gaps report behind the criteria is
`/home/noahc/math/.cruise27/gaps-S26.md` (cited as *gaps*).

## R-1 What exists today

- **Nothing writes, reads or checks a `Reversibility:` line except S39's reader.** `DECISION_ENTRY`
  (`src/slipwai/project/cruise_record.py:42-52`) has no such line; `DECISION_FIELDS`
  (`assets/toolkit/scripts/check-decisions.py:88`) does not name it; `entries()` (`:159-173`) records an unknown
  label in the entry's fields, and the order check (`:260`) keeps only `DECISION_FIELDS`, so a line added today
  passes silently whatever it says. Read from the files; *gaps* §1 says the same.
- **S39's reader** is `SPELLING` and `decision_entries()` in `assets/toolkit/scripts/agents/measures.py:764-791`:
  the first of `easy|guarded|hard` on the line (word-bounded) is the tier, `(easy|guarded)\s*(→|->)\s*hard`
  anywhere on it is an escalation, an entry with no line is left out (D168). Nothing in S26 changes it
  (AC-S26-13); the line's grammar (data-model.md) is chosen so that reader is right about every line the verb
  writes: the tier comes first, no key or value contains a tier word, a chain `easy → guarded → hard` matches the
  escalation pattern on its `guarded → hard` step.
- **The gate's shape for a second module.** `hand_backs.py` sits beside `check-decisions.py` and is loaded by
  path with bytecode off (`hand_backs_module()`, `check-decisions.py:483-492`), and only when a record exists
  ("no record: the module is not even loaded, and the gate is what it was", `:499`). S26 copies that: the rules
  live in `reversibility.py` beside the gate, loaded only when a decisions log carries a `Reversibility:` or
  `Proposed rule:` line. `check-decisions.py` is 699 lines (`wc -l`), which *gaps* G8 and the owner brief's
  *Taste* both turn into "a module beside it".
- **The scratch harness of the gate's tests** (`tests/test_decisions_scope.py:33-43`) copies only
  `check-decisions.py` into `scripts/`. A gate that loaded `reversibility.py` unconditionally would break every
  one of those tests and the differential test; loading it only on a log that carries the new labels keeps them
  unchanged, which is AC-S26-10's first half by construction.
- **The differential test** (`tests/test_decisions_gate_differential.py`) runs the gate as released at
  `596740f` (`test_decisions_scope_gate.released_checker`) and as it stands over sixteen log shapes plus this
  repository's own `decisions.md`, comparing exit code, stderr and stdout less `note:` lines. None of those logs
  carries the new labels (checked: `grep '^- \*\*Reversibility\|^- \*\*Proposed rule' specs/*/decisions.md` finds
  nothing), so it holds as is; S26 extends it with the same comparison on logs carrying an unknown label the old
  checker ignored, and a log with lines before and without after.

## R-2 Where the facts come from (D174, ADR 0007 at Proposed)

The entry's writer declares every fact about what accepting the decision would change; the gate re-derives the
tier under the rules version the line names. Dependants come from the entry's `Scope:` line. *How a scope maps to
a tier is left to planning, within FR-051* (D174 rule 2) — the plan's choice, data-model.md rules D1/D2:

- **one slice id → nothing fires; two or more → `guarded`; `global`, absent or unreadable → `hard`.** A decision
  scoped to one slice binds only that slice's later decisions, so taking it back re-opens one slice. Several ids
  re-open several slices: reversible, with care. `global` binds every slice of the feature ("a feature-level or
  doubtful decision is `global`", `DECISION_ENTRY`), and a scope that cannot be read is carried as global by the
  `--scope` verb (`placed()`, `check-decisions.py:414-425`); FR-051's fail-closed rule then makes both `hard`.
  The `Scope:` value is read with the gate's own `scope_tokens()` so the two readings cannot drift.

### R-2a `behind_flag` and code that is not code

FR-029 names the flag as a factor and AC-S26-1 makes `behind_flag=yes` part of the `easy` case; nothing says what
`no` gives, and *gaps* G1 notes that most decisions have no code at all (D54's *Written to* is two records). The
plan's choice: `behind_flag` takes `yes`, `no` or `no-code`; `no` fires F1 (`guarded`), the other two nothing.
Without `no-code`, a records-only decision would have to declare `no` (and be `guarded` for a flag it never
needed) or `yes` (and say something false). `flag_default` stays its own fact (D174 rule 1; S27's guarded
flag-default fixture, User Story 8's Independent Test), firing F2 (`guarded`).

### R-2b Reading D174 rule 4 beside D176 and AC-S26-4/-9

D174 rule 4 lists "a missing or unrecognised fact" among what the gate refuses. D176 (later, rule 4) and
AC-S26-4 make a missing fact or an unaccepted value *score `hard`*, and AC-S26-9's refusal list does not name
them. The one reading under which all three hold: a missing or unaccepted fact is refused exactly when the line
claims a tier lower than `hard` — which is the "tier that disagrees with its facts" refusal — and a line that says
`hard` with `schema=maybe` is honest and passes. The plan implements that; the verb, given a missing fact, writes
`<key>=missing` so the fact is named on the line (AC-S26-4).

### R-2c `size`, `urgency`, and every other key (D176 rule 3)

The verb's facts are a closed list (data-model.md). Any other key — `size` and `urgency` included — makes the
input malformed: the verb prints one line naming the key and gives no tier (exit 2, usage, as `check-decisions`
answers a call it does not understand, `:684-687`); the gate refuses the entry naming the entry and the key.

## R-3 The escalation chain (D177, FR-056)

The first tier is the computed one and stays first; each step raises by exactly one tier. The verb takes the tier
to raise to and writes every step (`--raise hard` from `easy` writes `easy → guarded → hard`), and refuses a
target lower than the computed tier ("never lowers"). The gate refuses a skipped, repeated or lowering step.
FR-056's "never a question in a diff or a note instead of escalating" is the skipper brief's text, not the gate's
(D177).

## R-4 Old lines under newer rules (AC-S26-11, ADR 0007 Consequences)

The rule table is versioned: `RULES = {1: …}`, and the gate keeps every version it has shipped. The line names
its version; an unknown version is malformed. FR-051's "MUST change only as a decision taken at the hard tier"
(*gaps* G5): in a project the module is a migrate-propagated file, so editing it scores `hard` by H7; in this
factory, a test freezes each shipped version's table (every fact vector over the closed value sets and the three
dependants classes, as a digest), so a shipped version can only be added to, never edited, and the module's
docstring says a new version is a decision taken at the hard tier. AC-S26-11 is proven with a fake written in the
test tree: a copy of `reversibility.py` with a version 2 that scores the same facts higher, run through the gate
over lines scored under version 1.

## R-5 Who writes the line, and where they are told (AC-S26-12/-14/-15)

- `DECISION_ENTRY` is the one shape; the cruise command (`cruise.py:185-187`) and the owner brief template
  (`decisions.py:79-85`) both interpolate it, so adding the line there shows it in both. The skipper's brief
  (`cruise_agents.py:62-110`) says "in the shape `{DECISIONS}` shows" — it gains the verb, FR-056's one-tier
  escalation and D178's proposed rule.
- **Host**: the skipper protocol (`cruise.py:160-187`) gains one sentence (from a constant in
  `cruise_record.py`, as `ADR_RULE` is, because `cruise.py` is at 341 of 350 lines) telling the session to run the
  verb for every entry it writes and to add the feature's entry headings to every skipper brief (D178 rule 2).
- **The owner brief keeps the old shape in projects already generated**: `migrate` never rewrites it (the
  template's own words, `decisions.py:30`; *gaps* G7). The fragment's catch-up note says so (AC-S26-16).
- **SCOPE_READ stays** (`cruise_agents.py:21-23`): out-of-scope headings are evidence for counting a shape,
  never binding (D178 rule 2).

## R-6 The `Proposed rule:` line (D178)

The gate checks only what is mechanical: at least two distinct cited ids other than the entry's own, each an
entry of the same log whose `Status` reads `standing` (`STATUS`, `check-decisions.py:98`). Whether three entries
share a deciding reason is the skipper's judgement (D178 rule 2); no script counts.

## R-7 The committed list (D175)

Read by an `Explore` delegate (text search; no `.codegraph/`) and checked against the files cited:

- **Adopted**: `adopted_files()` (`src/slipwai/project/adopted.py:51-68`) writes `<delivery>/.written`: every path
  `project_files` assembles less the repository's own root files (`OWN`, `:36-40`), sorted, one per line, no header;
  `replay` (`src/slipwai/replay.py:102-121`) recomputes it on `migrate`. This checkout's own `delivery/.written` (291
  lines) names `delivery/docs/…`, `.specify/…`, `project.json` and `.github/workflows/verify-delivery.yml`.
- **Generated**: no list exists. `migrate` → `replay` → `project_files` regenerates every file and a three-way
  merge decides each (`src/slipwai/migrate.py:96`, `replay.py:188-214`); which parts are the factory's is a table in
  `docs/upgrading.md:72-82`, not code. So a file `project_files` adds is written by `generate` and rewritten by
  `migrate` with no change to `migrate.py`; `tests/test_replay.py:60` already holds a replay byte-equal to the
  generation, which the list (a pure function of the assembled paths) keeps.
- **Path**: `.slipwai/propagated`. Not `.written` at the root: `survey.written_by_factory` (`src/slipwai/survey.py:172-182`)
  and `check-slice-scope.py:625-640` read a root `.written`, and a converged adopted repository already has one
  (`converge.py:137`). `survey` skips dot-directories other than `.github` (`survey.py:201-202`), `.slipwai/` is not
  among `check-slice-scope`'s host directories (`:177-178`), and `.slipwai/extensions.json` is already committed there.
  The generated `.gitignore` ignores only `.slipwai/catch-up.md` under it (`src/slipwai/project/gitignore.py:147-151`).
- **Contents**: Q1 in plan.md — the categories D175 enumerates (`scripts/`, `skills/`, `commands/`, `agents/`,
  `.specify/`, `Makefile`, `init`) and the list itself; `docs/` left off because a project grows its model and its
  architecture page there, which would make nearly every product decision `hard` (D175's *Why*).
- **Pruned paths**: the pruner may delete feature files after assembly (`prune.py:1059-1065`); a listed path that is
  not on disk is harmless to a lookup.
- **Extensions** (plan Q2): an elected extension's projector runs after the merge (`migrate.py:185-244`), so its
  files are on neither layout's list; the declared fact governs them.
- **The reader**: `origin: adopted` in `project.json` (the adoption signal, `src/slipwai/origin.py:104-110`) →
  `<layout.delivery>/.written` (`.written` where delivery is `.`); anything else → `.slipwai/propagated`.

## R-8 Migrating a project made before (AC-S26-16)

Precedent: `tests/test_benchmark_elapsed_migrate.py` (S39 R12) extracts the factory at a commit with
`git archive`, generates with it, migrates with this checkout's copy (`test_replay.newer_factory`) and runs the
project's `make` targets. S26 takes the same route from `063c187`, runs `make check-decisions` on the migrated
project (the part of `make verify` this slice changes) and checks the list arrived and the owner brief is
untouched; the full `make verify` of a migrated project is the demo's step, which this delegate stops before.
