# Quickstart: S33-factory-gate-stamp

Once `s33.patch`, `s33-2.patch`, `s33-3.patch` and `s33-4.patch` are applied and committed, on `adopt-method` (not the trunk) with
no CI variable set.

**Before step 1 (D120).** `git worktree list` shows no worktree inside the checkout — nothing under
`.claude/worktrees/` — `git status --porcelain` is empty, and nothing writes the tree between the two runs (a cruise
runner writes `specs/cruise-log.jsonl` and a slice's `benchmark.json`; stop it first). Where a worktree is inside the
checkout, the second run is a full gate whose line names the nested repository and says it recorded nothing: the
stamp declining to vouch, not a fault. Since T028 the gate writes no interpreter cache under `assets/` (D121), so the
second run is the one to measure, on a fresh checkout too.

**A log of the gate goes outside the checkout** (`make verify 2>&1 | tee /tmp/verify.log`), or to the terminal. A log
written into the tree — under `.factory-work/` or `build/` — is an ignored file the key covers, growing while the
checks run, so the pass is never recorded (D122).

```sh
make verify            # the full gate, about forty minutes; ends `verify: all gates passed`
make verify            # unchanged tree: one line saying it already passed, and when; about a second
VERIFY_FORCE=1 make verify   # every check again
CI=1 make verify       # the full gate; no stamp read or written
make verify TESTS=test_changelog   # a slice of the suite: runs as before, reads and writes no stamp
FACTORY_BACKENDS=python make verify   # a slice of the matrix: the same, no stamp (T015)
```

**Measured (T029, iteration 21, at `a8ab3f2`, from a tree with no cache under `assets/`):** the full gate 2512 s
(1961 tests); the second run 1.24 s, the reuse line and no check — about 0.7 s of it is the key asking npm, npx and uv
for their versions one after another, which AC-S33-6 and -12 require. No cache under `assets/` after either run.
