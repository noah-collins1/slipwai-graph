# Quickstart: S33-factory-gate-stamp

Once `s33.patch`, `s33-2.patch` and `s33-3.patch` are applied and committed, on `adopt-method` (not the trunk) with
no CI variable set.

**Before step 1 (D120).** `git worktree list` shows no worktree inside the checkout — nothing under
`.claude/worktrees/` — `git status --porcelain` is empty, and nothing writes the tree between the two runs (a cruise
runner writes `specs/cruise-log.jsonl` and a slice's `benchmark.json`; stop it first). Where a worktree is inside the
checkout, the second run is a full gate whose line names the nested repository and says it recorded nothing: the
stamp declining to vouch, not a fault. The gate's own first run on a fresh checkout writes
`assets/backing-services/__pycache__/` (the pruner, D119), which the key lists, so on a fresh checkout run it a third
time before measuring.

```sh
make verify            # the full gate, about forty minutes; ends `verify: all gates passed`
make verify            # unchanged tree: one line saying it already passed, and when; well under a second
VERIFY_FORCE=1 make verify   # every check again
CI=1 make verify       # the full gate; no stamp read or written
make verify TESTS=test_changelog   # a slice of the suite: runs as before, reads and writes no stamp
FACTORY_BACKENDS=python make verify   # a slice of the matrix: the same, no stamp (T015)
```
