MINOR

**`make verify` returns at once on a tree that already passed it.** A full passing run on a branch that is not the
trunk records a stamp under the git directory — keyed by the working files' bytes, the index, `HEAD` and the refs, the
gate's own scripts, the versions of the tools the machine supplies and the variables a check reads — and the next run
on the same tree prints one line, starts no check and exits 0. `VERIFY_FORCE` is unset by default; `make verify
VERIFY_FORCE=1` runs the gate anyway. The checks themselves are unchanged, in the same order, ending `verify: all gates
passed`; they now hang on a `verify-checks` target that `verify` runs after asking the stamp, for every project the
factory generates and for every backend. The stamp is never in the working tree and `git status` shows nothing of it.
The trunk and CI always run the full gate and neither read nor write a stamp, `make ci` always runs it, and the gate of
a repository that adopted the method is as it was. A stamp cannot see what a project's own tests or tools read from outside the repository — the clock, the network,
user-level tool configuration, `PATH`, a variable no gate script names — so a gate that would now fail for one of those
alone is reused as green until a file, a ref or a listed input moves or `VERIFY_FORCE` is given, and CI and the trunk,
which never read a stamp, are where it is caught. `docs/gates.md` in a generated project says so.

**Catch-up.** Nothing is asked of a repository already generated: `slipwai migrate` brings the new `Makefile` and
`scripts/verify-stamp.py`, the first `make verify` runs in full, and `.gitignore` is not touched.
