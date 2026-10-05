# 0005. The generated Makefile's rules are fingerprinted next to the scoped gate's scripts

Date: 2026-10-05

## Status

Proposed

Drafted by `/cruise` iteration 22 of `001-faster-slipwai`, at converge pass 2 of `S06-scoped-gate` (decision D127 in
`specs/001-faster-slipwai/decisions.md`, finding T030 in `specs/001-faster-slipwai/slices/S06-scoped-gate/tasks.md`).
The run never accepts its own architecture decision; the word `Accepted` here is a person's.

## Context

`make verify-scoped` skips a check because of what the table says that check reads. The table describes the factory's recipe for each rule. A project owns its Makefile (Principle I) and can add a line, a prerequisite (order-only included), or a variable to any rule `make verify` reaches. Once that edit is on the trunk, the scoped run skips it and says *passed* while `make verify` fails (T030). The script runs inside the project, which has no copy of the factory's `makefile.py` to compare against.

## Decision

- The generator writes `scripts/verify_scoped/rules.json` (schema 1) from the same `makefile()` output that becomes the Makefile. It holds one sha256 per rule reachable from `verify`, plus the scoped units and family targets, over that rule's normal prerequisites, order-only prerequisites and unexpanded recipe lines. It holds one sha256 per variable the factory assigns.
- One stdlib toolkit module defines the canonical form. It reads the form from the Makefile text at generate time and from `make -npq` at run time, and a test holds the two readings equal for every starter shape.
- A difference charged to one named check makes that check run every time and claim nothing. Charged to one gate with units, the gate runs whole. Anything else is the full gate.
- `generate`, `add-service` and `migrate` write the file together with the Makefile. No command lets a project re-fingerprint its own edits.

## Consequences

- A project that edits a check the factory wrote loses scoping for that check, permanently and visibly. An edit to `verify`, `verify-checks`, a shared prerequisite, or `SHELL` makes every scoped run the full gate. That is the cost of never trusting text nobody compared.
- Every generated project carries one more file, and its schema is a contract between the factory's writer and the project's script.
- A new construct in `makefile()` needs `from_text` to understand it before the factory's tests pass.
- A project that edits `rules.json` by hand can silence the guard on its own trunk. That is Principle I's price, and no factory tool offers it.
- Removing this file later is a generated-file deletion with a catch-up note, decided by a person.
