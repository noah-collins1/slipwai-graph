# Research: S14-result-contract

Every statement about existing code cites the file it was read from at `c3c760b`. Nothing here rests on an
uncited dependency behaviour: the slice adds no dependency, and the one library it leans on is `json` from the
standard library (`json.loads` rejects trailing commas and returns `bool` for `true`, which `isinstance(x, int)`
also accepts — R-3 handles it).

## R-1 The block is validated by a module beside the checker, not inside it

- **Decision**: `assets/toolkit/scripts/hand_backs.py`, loaded by path from `check-decisions.py` and from
  `agents/benchmark.py` with `sys.dont_write_bytecode` set.
- **Rationale**: `check-decisions.py` is 526 lines and holds three record kinds already; D134 wants one table and
  the session to validate "with the checker's own function", and `benchmark.py` needs the same reader for the count.
  A module two scripts load is that one function. Loading by path with bytecode off is the toolkit's existing pattern
  (`verify-scoped.py` line 24, `verify-stamp.py` lines 607–616, `check-codegraph.py` line 235); a `__pycache__`
  under `scripts/` would make every later scoped run the full gate (`verify-scoped.py` line 24's comment).
- **Shipping**: `assets/toolkit/scripts/` is copied whole — `verify_scoped/` is named nowhere in `src/` (`grep -rn
  verify_scoped src/` is empty) and still ships. A script's text is not repointed for an adopted layout
  (`layout.py`, `CODE = "scripts/"`); it finds its root through `project.json` (`check-decisions.py` lines 65–72).
  The scoped gate's table already takes all of `specs/` as `check-decisions`' input (`verify_scoped/table.py`
  line 55), and a change under `scripts/` is the full gate, so S06's table needs no row.
- **Alternatives**: all in `check-decisions.py` (too large, and benchmark would import the gate's whole module);
  a package directory (one module does not need one).

## R-2 Coverage is matched by stage and time window, against `benchmark.json`

- **Decision**: a delegated entry is covered when the record holds an entry with a passing block whose heading's
  stage equals the entry's `stage` and whose heading time lies in `[started, ended]`.
- **Rationale**: `benchmark.py end` sets `delegated` from sub-agent tokens read in the transcript (lines 505–507)
  and records `started`/`ended` in UTC (`now()`); the append verb writes the heading time itself, and the ladder
  text says to append before closing the entry, so the time falls inside the bracket. An entry whose usage has no
  `source` (lines 733–746, `usage_unread`) cannot say whether it delegated: that is *could not attribute*
  (AC-S14-15), never a guess.
- **Alternatives**: counting record entries against `agents` (several delegates per stage, e.g. an adversary pass's
  seams, would make n exceed m); matching by type (the record's type and the transcript's attribution are two
  readings of one fact, and only Claude Code attributes).

## R-3 Field rules that the criteria imply but do not spell

- `contract`, `score`: an integer that is not a `bool` (`json` reads `true` as `bool`, a subclass of `int`).
- *Path-valued fields* (AC-S14-7): in schema 1 only `files_changed`. Absolute is a leading `/` or `\` or a drive
  letter `X:`; `..` is a path segment equal to `..` after splitting on `/` and `\`. `[]` passes (D135).
- `delegate` must equal the heading's type: the entry says one fact twice, and disagreement is a malformed entry
  named by the field `delegate`.
- `decisions` ids are checked against `## D<n> — ` headings of `specs/<feature>/decisions.md` for the feature the
  record sits under; a feature with no log names no entry.

## R-4 `Missing:` reasons are written, not enumerated by the gate

- **Decision**: the gate accepts any non-empty reason after `- **Missing:** `; the ladder text and the page name the
  four the method writes — `refused: <the delegate's words>`, `malformed: <field>`, `no continuation`,
  `stopped: <reason>`.
- **Rationale**: ADR 0006 writes `- **Missing:** <reason>`; AC-S14-6 refuses only an entry with *neither* a block nor
  the line; AC-S14-13 needs a stopped delegate to be recorded "with its reason" and not charged with a malformed
  block. Holding the words would be a vocabulary nobody decided; naming them in the text is enough for a reader.

## R-5 Where the hand-back of a `drive-slice` goes

The ready set's fan-out is a feature-level stage (D134 item 1); the main session writes feature-level records only.
So `drive-slice`'s own block goes to `specs/<feature>/hand-backs.md`, stage `ready-set`, and the slice's own record
is written only from inside its worktree. Open question Q2 asks the host to confirm.

## R-6 The text lives in a new factory module

`src/slipwai/project/commands.py` is 345 lines, `cruise.py` 333, `agents.py` 300, against `make check-structure`'s
350. The paragraphs go in `result_contract.py`; each of those files gains a placeholder and an import. The status
table is duplicated there from the toolkit script and a test holds the two equal: the factory cannot import a toolkit
script by module name, and loading a bundled asset at generation time has no precedent in `src/slipwai/project/`.

## R-7 Where the drive text goes, and what stays off S06's paragraphs

D123 rewords `agents.py`'s implement brief (lines 135–137) and converge brief (lines 189–191), and S06 changed
`commands.py` lines 179 and 190. This slice adds a section after `{who_runs_each_stage(layout)}` (line 174), a
sentence in the converge brief after its levels paragraph (lines 175–181), and nothing in the paragraphs above.

## R-8 Projection and layout

`agents.agent_file` renders the shared part every type carries (lines 259–295); `scripts/agents/project.py`
projects the body into each harness's file, so one paragraph there reaches every harness. Pointers such as
`docs/result-contract.md` and `scripts/check-decisions.py` in generated prose are rewritten to `delivery/…` by
`Layout.repoint` (`layout.py` lines 85–89), as `docs/delegated-agent-safety.md` is in this repository's own
`delivery/agents/drive-slice.md`.
