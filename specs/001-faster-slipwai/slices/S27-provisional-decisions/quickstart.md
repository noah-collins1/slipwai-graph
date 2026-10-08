# Quickstart: S27-provisional-decisions — the demo script

The actor is the maintainer who turns provisional approval on, and the skipper that writes the entries. Run from this
worktree's checkout (`./slipwai`, not the one on PATH), in a scratch directory under `/tmp/s27-demo/`. Commands below
run inside the generated project.

1. **A project, and the setting's ladder** (AC-S27-11, -16).
   `./slipwai generate demo27 --output /tmp/s27-demo --no-init --no-install --skip-checks`; `generate` has already made
   the first commit, so work inside `/tmp/s27-demo/demo27` without a `git init` or a `git commit`.
   `python3 scripts/agents/cruise.py` lists `decide` with its five values' sentence.
   `python3 scripts/agents/cruise.py --set decide=provisional` → refused: set `provisional-shadow` first; the file is
   unchanged (`git diff --quiet .specify/cruise.json`).
2. **The run cannot set it** (AC-S27-13). `CRUISE_ITERATION=1 python3 scripts/agents/cruise.py --set
   decide=provisional-shadow` → refused, naming `/cruise-settings`.
3. **Step up one rung at a time.** `--set decide=provisional-shadow`, commit it; `python3 scripts/agents/cruise.py
   mode --feature demo` prints the entry `decide moved from unrecorded to provisional-shadow` citing that commit
   (AC-S27-12). Append it to `specs/demo/decisions.md` (create it with a `# Decisions` title) with the `Reversibility:`
   line `python3 scripts/reversibility.py --scope global contract=no schema=no auth=no customer_visible=no export=no
   ci_workflow=no migrate_file=no behind_flag=no-code flag_default=no rollback_complexity=trivial` prints, and commit.
4. **Shadow** (AC-S27-10). Score the guarded fixture:
   `python3 scripts/reversibility.py --scope S1 contract=no schema=no auth=no customer_visible=no export=no ci_workflow=no migrate_file=no behind_flag=yes flag_default=no rollback_complexity=hours`
   → `guarded`. Then `python3 scripts/provisional.py status --decide provisional-shadow --ask approval --when
   2026-10-07T21:00:00Z --number D2 --reversibility '<that line>'` → `unavailable: a person's approval`, a
   `Provisional (shadow): guarded · provisional · ratify by 2026-10-14 · Revert: commits carrying Decision: D2` line,
   `Status: standing`.
5. **A skipping hand edit parks** (AC-S27-12). Edit `.specify/cruise.json` by hand to `"decide": "provisional"`;
   `python3 scripts/agents/cruise.py mode --feature demo` → `cruise: parked: decide=provisional is more than one rung
   above provisional-shadow (D1); set decide=provisional-advisory through /cruise-settings and let an iteration record
   it …`, exit 3. Restore it with `git checkout -- .specify/cruise.json`.
6. **Enforced** (AC-S27-1, -2, -4). `--set decide=provisional-advisory`, then `mode --feature demo` and append the entry it prints (D2, scored as in step 3),
   then `--set decide=provisional`: an iteration records each rung before the next is taken. The step-4
   command with `--decide provisional` → `Status: provisional · ratify by 2026-10-14` and
   `Revert: commits carrying Decision: D2`. The flag fixture (`flag_default=yes rollback_complexity=trivial`) →
   `unavailable`, stderr naming `flag_default=yes`. The D54 fixture (`ci_workflow=yes migrate_file=yes
   behind_flag=no-code`) → `unavailable`.
7. **The gate** (AC-S27-8, -9). Append to `specs/demo/decisions.md` (create it with a `# Decisions` title if absent)
   an entry in `DECISION_ENTRY`'s shape
   (`commands/cruise.md`) with the guarded line and the two lines from step 6; `make check-decisions` → passes. Change
   its `Reversibility:` to the flag fixture's line → refused naming `flag_default`; change `Revert:` to name D9 →
   refused naming `Revert`; write `Status: ratified tomorrow` → refused naming `Status`. Restore the passing entry.
8. **What binds later decisions** (AC-S27-15). `python3 scripts/check-decisions.py --scope S1` prints the entry and
   names it `provisional and binding`.
9. **The run will not say `done`** (AC-S27-14). `python3 scripts/provisional.py audit` → `cruise: parked: ratify D2`,
   exit 3. Edit the `Status` to `ratified 2026-10-08`; the audit → none unratified, exit 0; `make check-decisions`
   still passes.
10. **A project made before** (AC-S27-17). Generate with the factory at `5f4fc00` (`git archive 5f4fc00`), commit,
    `slipwai migrate` with this checkout, `make verify` → passes; `.specify/cruise.json` is byte-unchanged;
    `scripts/provisional.py` arrived; `.slipwai/catch-up.md` names the three values.

Clear `/tmp/s27-demo` afterwards.
