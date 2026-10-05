# 0005. The generated Makefile is held by its text next to the scoped gate's scripts

Date: 2026-10-05

## Status

Proposed

Drafted by `/cruise` iteration 22 of `001-faster-slipwai`, at converge pass 2 of `S06-scoped-gate` (decision D127 in
`specs/001-faster-slipwai/decisions.md`, finding T030 in `specs/001-faster-slipwai/slices/S06-scoped-gate/tasks.md`).
The run never accepts its own architecture decision; the word `Accepted` here is a person's.

## Context

`make verify-scoped` skips a check because of what the table says that check reads. The table describes the factory's recipe for each rule. A project owns its Makefile (Principle I) and can add a line, a prerequisite (order-only included), or a variable to any rule `make verify` reaches. Once that edit is on the trunk, the scoped run skips it and says *passed* while `make verify` fails (T030). The script runs inside the project, which has no copy of the factory's `makefile.py` to compare against.

## Decision

- Amended by D140 (iteration 23, converge pass 4, T036/T037): `rules.json` holds a `makefile` digest over the exact text `makefile()` wrote, normalised only for CRLF. The scoped run compares it before any make call, and also checks for `GNUmakefile`, `makefile` and a non-empty `MAKEFILES`. Any difference is the full gate. On matching text the per-rule, per-variable and `exports` comparisons are a second check, and any difference they find is the full gate. D127's per-check and per-gate charges for Makefile differences, and D131, are retired.
- The generator writes `scripts/verify_scoped/rules.json` (schema 1) from the same `makefile()` output that becomes the Makefile. It holds one sha256 per rule reachable from `verify`, plus the scoped units and family targets, over that rule's normal prerequisites, order-only prerequisites and unexpanded recipe lines. It holds one sha256 per variable the factory assigns.
- One stdlib toolkit module defines the canonical form. It reads the form from the Makefile text at generate time and from `make -npq` at run time, and a test holds the two readings equal for every starter shape.
- `generate`, `add-service` and `migrate` write the file together with the Makefile. No command lets a project re-fingerprint its own edits.
- Amended by D133 (iteration 22, converge pass 3, T033): every variable of origin `file` or `override`, dot-names and make's specials included, `define` blocks too, is compared; an override is held with its own flavour; a rule's canonical form gains `"vars"` for its target-specific variables; the file gains an `exports` digest over every `export`, `unexport`, `.EXPORT_ALL_VARIABLES` and `$(eval` line in the files make read. A variable the factory did not write, a pattern-specific variable, a changed exported factory variable, or a changed export line is the full gate; environment and command-line origins stay the baseline's (D116).

## Consequences

- A project that edits its `Makefile` in any way makes every scoped run the full gate, permanently, until the file is the factory's text again. Correctness no longer depends on listing make's features. Speed for a customising project is the cost.
- The factory must hold its own text equal under the scoped call's, the full gate's and the database read's conditions for every shape (D140 point 4).
- Every generated project carries one more file, and its schema is a contract between the factory's writer and the project's script.
- A new construct in `makefile()` needs `from_text` to understand it before the factory's tests pass.
- A project that edits `rules.json` by hand can silence the guard on its own trunk. That is Principle I's price, and no factory tool offers it.
- Removing this file later is a generated-file deletion with a catch-up note, decided by a person.
