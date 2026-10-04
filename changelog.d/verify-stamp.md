MINOR

**`make verify` returns at once on a tree that already passed it.** A full passing run on a branch that is not the
trunk records a stamp under the git directory — keyed by every file under the project, tracked, untracked or ignored, except what the gate rebuilds or never reads, the index, `HEAD`, every ref, the repository's own git configuration, the
gate's own scripts, the versions of the tools the machine supplies that the gate launches and the variables a check reads — and the next run
on the same tree prints one line, starts no check and exits 0. `VERIFY_FORCE` is unset by default; `make verify
VERIFY_FORCE=1` runs the gate anyway. The checks themselves are unchanged, in the same order, ending `verify: all gates
passed`; they now hang on a `verify-checks` target that `verify` runs after asking the stamp, for every project the
factory generates and for every backend. The stamp is never in the working tree and `git status` shows nothing of it.
The trunk — the branch `project.json` records as `ci.branch`, else `main`, else `master` — and CI (a non-empty `CI`,
`GITHUB_ACTIONS` or `GITLAB_CI`) always run the full gate and neither read nor write a stamp, `make ci` runs every check and records nothing, and the gate of
a repository that adopted the method is as it was (its `docs/gates.md` says nothing of a stamp). A stamp cannot see what a project's own tests or tools read from outside the repository — the clock, the network,
user-level tool configuration, `PATH`, a variable no gate script names, git's own user-level or system configuration, a file edited by hand inside an installed dependency tree whose manifest did not move — so a gate that would now fail for one of those
alone is reused as green until a file, a ref or a listed input moves or `VERIFY_FORCE` is given, and CI and the trunk,
which never read a stamp, are where it is caught. `docs/gates.md` in a generated project says so.

**Catch-up.** Nothing is asked of a repository already generated, with one exception: `slipwai migrate` brings the new
`Makefile` and `scripts/verify-stamp.py`, the first `make verify` runs in full, and `.gitignore` is not touched — but a
repository whose trunk is named neither `main` nor `master` and whose `project.json` records no `ci.branch` records it,
so that its trunk always runs the full gate; until then that branch reuses a stamp like any other.
`make ci` runs every check and records nothing, so the `make verify` that follows a green `make ci` runs in full.
A `ci.branch` the gate cannot use, or a trunk it cannot find, is said on one line before the first check, which says to
record `ci.branch` or fetch the trunk; that run runs every check and records nothing, where it once stamped in silence.
A pipeline that sets none of `CI`, `GITHUB_ACTIONS` or `GITLAB_CI` sets `CI=1` itself.
