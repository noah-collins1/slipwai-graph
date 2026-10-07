MINOR

**Every decision can now say how hard it would be to take back.** `scripts/reversibility.py` scores the facts
a decision's writer declares (contract, schema, auth, customer-visible effect, export, CI workflow, a file `migrate`
propagates, flag, rollback effort) and the entry's `Scope:` into a tier, `easy`, `guarded` or `hard`, and prints the
whole `- **Reversibility:** ...` line for the entry. The rules are versioned, so a line is always judged by the
version that scored it; `--raise` writes an escalation one tier at a time and never lowers one.

**Catch-up.** `slipwai migrate` brings the new `scripts/reversibility.py` and the committed list `.slipwai/propagated` (the paths `migrate` carries, which the verb reads to tell whether a decision touches a file `migrate` propagates), and nothing else asks anything of the project; in a repository adopted with `layout.delivery` (experimental: brownfield adoption) the script lands under the delivery directory and the verb reads the `.written` already there, so no `.slipwai/propagated` is added. Existing decisions logs pass unchanged: `make check-decisions` reads an entry with no `Reversibility:` line exactly as it did, and an entry without the line that follows one that has it gets a `note:`, never a refusal. To give a new entry the line, run `python3 scripts/reversibility.py` with the facts you declare and paste the `- **Reversibility:**` line it prints after the `Confidence` line. The owner brief `.specify/product-owner.md` is merged like any other file: a brief the project never edited takes the new entry shape, and one it edited keeps its own edits, so where the merge leaves the entry example without the `Reversibility:` line, add it by hand; `commands/cruise.md` is the authority on the shape.
