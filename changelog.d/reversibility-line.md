MINOR

**Every decision can now say how hard it would be to take back.** `scripts/reversibility.py` scores the facts
a decision's writer declares (contract, schema, auth, customer-visible effect, export, CI workflow, a file `migrate`
propagates, flag, rollback effort) and the entry's `Scope:` into a tier, `easy`, `guarded` or `hard`, and prints the
whole `- **Reversibility:** ...` line for the entry. The rules are versioned, so a line is always judged by the
version that scored it; `--raise` writes an escalation one tier at a time and never lowers one.

**Catch-up.** To be completed with the rest of the slice.
