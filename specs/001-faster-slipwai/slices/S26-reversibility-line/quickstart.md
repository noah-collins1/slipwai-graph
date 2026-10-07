# Quickstart: S26-reversibility-line — the demo script

The actor is the person who reads a project's decision log, and the skipper that writes it. Run from this
worktree's checkout (`./slipwai`, not the one on PATH), in a scratch directory under `/home/noahc/math/.cruise27/`.

1. **A project, and its committed list.**
   `./slipwai generate demo26 --output /home/noahc/math/.cruise27/s26-demo --no-init --no-install --skip-checks`,
   then `git -C …/demo26 ls-files .slipwai` shows `.slipwai/propagated`; it names `scripts/check-decisions.py` and no
   path under `apps/` or `docs/`.
2. **Score an easy decision** (AC-S26-1):
   `python3 scripts/reversibility.py --scope S1 contract=no schema=no auth=no customer_visible=no export=no ci_workflow=no migrate_file=no behind_flag=yes flag_default=no rollback_complexity=trivial`
   prints `- **Reversibility:** easy · rules 1 · …`.
3. **Score the D54 fixture** (AC-S26-6): the same with `ci_workflow=yes migrate_file=yes behind_flag=no-code` →
   `hard`, stderr naming the two rules.
4. **Size is not a fact** (AC-S26-5): add `size=large` → exit 2, one line naming `size`, nothing on stdout.
5. **Escalate one step at a time** (AC-S26-14): step 2 with `--raise hard` → `easy → guarded → hard`.
6. **The gate.** Append entries to `specs/demo/decisions.md` in `DECISION_ENTRY`'s shape: D1 with the line from
   step 2, D2 with no line; `make check-decisions` → exit 0 and one `note:` naming D2 and the verb (AC-S26-10).
   Edit D1's line to `easy` with `ci_workflow=yes` → one finding naming D1 and `ci_workflow` (AC-S26-9); to
   `easy → hard` → a skipped step.
7. **A proposed rule** (AC-S26-15): D3 standing, with `- **Proposed rule:** … (same shape as D1, D2)` passes; with
   `(same shape as D1)` it is refused.
8. **A project made before** (AC-S26-16): generate with the factory at `063c187` (`git archive 063c187`), write a log
   there, `slipwai migrate` with this checkout, then `make verify` → passes; `.slipwai/propagated` and
   `scripts/reversibility.py` arrived; `.specify/product-owner.md` is as it was; `.slipwai/catch-up.md` names the
   line.
9. **What S39 reads** (AC-S26-13): `make benchmark` on a log of verb-written lines shows decision health with a
   tier count and an escalation share.

Clear `/home/noahc/math/.cruise27/s26-demo` afterwards.
