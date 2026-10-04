# Verification gates

`make verify` is the deterministic local and CI entry point. It runs , architecture direction,
agent-projection and Spec Kit manifest drift, constitution coverage, event-model validation in the event profile,
and `check-benchmark`, which warns of a benchmark entry left open or a done slice with no record, and
keeps missing measurements visibly unbracketed. `make help` lists integration,
adversarial, mutation, model, benchmark and dependency-audit targets. Mutation and dependency audit remain
explicit end-of-phase/CI operations, not hidden costs in every local increment.

`make check-codegraph` is in the gate for a project that has adopted a code index and a no-op for one that
has not: it fails when `.codegraph/` no longer describes the tracked source — files it has never seen, or
files that changed after it read them. CodeGraph indexes only while a client is attached to its daemon, so a
checkout opened where that tooling is missing keeps a database nothing updates, and a stale index answers
*nothing calls that* in the same words an accurate one uses. The failure says how to catch it up.
On a `slice/<id>` branch in a developer's checkout, outside CI, the gate compares only what changed since its last
whole comparison and leaves the integrity check to the trunk and CI; it keeps that record in
`.codegraph/gate-memory.json` (ignored by Git), and deleting that file makes the next run whole.
The runner's check before an iteration narrows the same way, on any branch outside CI, from the same record: it
hashes only what changed since the last whole comparison; what a narrowed comparison cannot see — a file whose bytes
changed while its size, times and identity all read as before — it cannot see either; and deleting that file makes
its next comparison whole.

`make check-constitution` is the one gate that reads a document rather than code, and it waits for the
document: `./delivery/init` installs the constitution *template*, and while that file is still the untouched template
the gate reports that nothing has been drafted and passes, so the commit `./delivery/init` pushes goes through
`verify` before a principle has been written. From the first edit — and regardless, once any feature exists
under `specs/` — it applies in full: `.specify/memory/constitution.md` must carry minimum CD, the practices the skills in
`delivery/skills/` teach. Nothing about event sourcing is asked of this profile. An unfilled
`[PLACEHOLDER]` means drafted rather than ratified.

`make constitution-requirements` prints the normative text and `/constitution-coverage` runs the same check
from an agent session. Amend the constitution rather than the gate: a principle deleted from that file is a
gate that silently stopped existing, because every later phase reads it as the authority it claims to be.

Minimum CD here follows [MinimumCD](https://minimumcd.org/minimumcd/) (CC BY-SA 4.0), restated for this
repository and extended with the clause on agent-generated change; `delivery/skills/REFERENCES.md` records what was
taken and what was added.

Tests should protect observable behaviour. Keep fast domain tests focused, add adapter contract tests at
real boundaries, and add end-to-end tests only for paths whose integration risk justifies them.
