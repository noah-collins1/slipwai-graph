# Decisions

## D1 — decide moved from unrecorded to provisional-shadow
- **Stage:** iteration start · **Slice:** none · **When:** 2026-10-08T02:24:10Z · **Iteration:** unknown
- **Scope:** global
- **Question:** which `decide` mode does this run work under?
- **Options:** recommended-first · skipper-always · provisional-shadow · provisional-advisory · provisional
- **Decision:** provisional-shadow, recorded as found in `.specify/cruise.json` (commit 8f73b05); no feature's log had an earlier mode entry, so what it was before is unknown
- **Why:** no feature's log had an earlier mode entry, so the run records the mode as found and claims no change (D196, D202)
- **Decided by:** human
- **Confidence:** high · **Would reverse if:** a person sets `decide` again
- **Reversibility:** hard · rules 1 · contract=no schema=no auth=no customer_visible=no export=no ci_workflow=no migrate_file=yes behind_flag=no-code flag_default=no rollback_complexity=trivial
- **Written to:** `.specify/cruise.json`
- **Status:** standing

## D2 — decide moved from provisional-shadow to provisional-advisory
- **Stage:** iteration start · **Slice:** none · **When:** 2026-10-08T02:24:31Z · **Iteration:** unknown
- **Scope:** global
- **Question:** which `decide` mode does this run work under?
- **Options:** recommended-first · skipper-always · provisional-shadow · provisional-advisory · provisional
- **Decision:** provisional-advisory, as a person set it in `.specify/cruise.json` (uncommitted at 2026-10-08T02:24:31Z)
- **Why:** a person raised the setting up the ladder through /cruise-settings; the run records the move and never sets it (D62)
- **Decided by:** human
- **Confidence:** high · **Would reverse if:** a person sets `decide` again
- **Reversibility:** hard · rules 1 · contract=no schema=no auth=no customer_visible=no export=no ci_workflow=no migrate_file=yes behind_flag=no-code flag_default=no rollback_complexity=trivial
- **Written to:** `.specify/cruise.json`
- **Status:** standing

## D3 — decide moved from provisional-advisory to provisional
- **Stage:** iteration start · **Slice:** none · **When:** 2026-10-08T02:24:41Z · **Iteration:** unknown
- **Scope:** global
- **Question:** which `decide` mode does this run work under?
- **Options:** recommended-first · skipper-always · provisional-shadow · provisional-advisory · provisional
- **Decision:** provisional, as a person set it in `.specify/cruise.json` (commit 5bab969)
- **Why:** a person raised the setting up the ladder through /cruise-settings; the run records the move and never sets it (D62)
- **Decided by:** human
- **Confidence:** high · **Would reverse if:** a person sets `decide` again
- **Reversibility:** hard · rules 1 · contract=no schema=no auth=no customer_visible=no export=no ci_workflow=no migrate_file=yes behind_flag=no-code flag_default=no rollback_complexity=trivial
- **Written to:** `.specify/cruise.json`
- **Status:** standing

## D4 — may the export button ship behind its flag before the owner has seen it?
- **Stage:** plan · **Slice:** S1 · **When:** 2026-10-07T21:00:00Z · **Iteration:** 1
- **Scope:** S1
- **Question:** may S1 ship its export button behind a flag, seeded off, before the owner approves the wording?
- **Options:** ship behind the flag (recommended) · wait for the owner
- **Decision:** ship behind the flag, seeded off
- **Why:** the owner sees it before the flag is flipped, and it stays dark meanwhile
- **Decided by:** drive-skipper (claude-opus-5-5)
- **Confidence:** medium · **Would reverse if:** the owner rejects the wording
- **Reversibility:** guarded · rules 1 · contract=no schema=no auth=no customer_visible=no export=no ci_workflow=no migrate_file=no behind_flag=yes flag_default=no rollback_complexity=hours
- **Written to:** `README.md`
- **Status:** provisional · ratify by 2026-10-14
- **Revert:** commits carrying Decision: D4
