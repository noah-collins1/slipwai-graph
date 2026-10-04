MINOR

**`make verify` returns at once on a tree that already passed it.** A full passing run records a stamp under the
git directory — keyed by the working files' bytes — and the next run on the same tree prints one line, starts no
check and exits 0; `VERIFY_FORCE=1` runs the gate anyway. The checks themselves are unchanged, in the same order,
ending `verify: all gates passed`; they now hang on a `verify-checks` target that `verify` runs after asking the
stamp. The stamp is never in the working tree and `git status` shows nothing of it.

**Catch-up.** Nothing is asked of a repository already generated: `slipwai migrate` brings the new `Makefile` and
`scripts/verify-stamp.py`, the first `make verify` runs in full, and `.gitignore` is not touched.
