PATCH

**`check-slice-scope` compares a slice branch with the trunk's own refs, so a branch no longer empties its own
check by minting a base.** The base was found by short name, so a `master` branch, an `origin/master`, or a tag
named `main` created at the slice's head made the diff empty and the check pass. Only `refs/heads/<trunk>` and
`refs/remotes/origin/<trunk>` answer now.

The trunk is `ci.branch` in `project.json` where that is a branch name with a ref in the checkout, else `main`,
else `master`; a `slice/<id>` name is never one, in any case. Where CI names the pull request's target
(`GITHUB_BASE_REF`, `CI_MERGE_REQUEST_TARGET_BRANCH_NAME`) and it has a ref, it is a second candidate, and when the
two bases differ the older one wins, so the target can only move the base back. The line the check prints now says
what it compared with — `compared with `main` at 3f2a9c1` — and, where `ci.branch` names a branch this checkout
does not have, which one — and the `git fetch` that would bring it, printed only for a plain branch name and where
a remote named `origin` exists; otherwise the line says which branch is missing. A recorded trunk that shares no
history with the branch is passed over for `main`, and said so.

**What is promised, locally and on a pull request.** On a developer's machine nothing the slice commits, and no
stray `master`, `origin/master` or tag named `main`, moves the base forward; someone who moves refs in their own
checkout can still defeat it, as they can by moving `main`, and that is not promised against. On a pull request
against the trunk in CI, nothing the branch commits or pushes moves the base forward, given a base to compare with
at all. Left over: a push pipeline with no pull-request target has only the local promise, and a pull request aimed
at a branch other than the trunk is held only as far as `project.json` reaches.

**Catch-up.** `slipwai migrate` carries the corrected script; nothing else in a repository changes. Two things you
may see afterwards. On a developer's machine, a slice branch with no trunk to compare with — no `main` ref, or a
shallow clone too short to reach the branch point — used to pass as "nothing to hold"; it now fails with a
single line that names the command to run (`git fetch origin refs/heads/<trunk>:refs/remotes/origin/<trunk>`, or
`git fetch --unshallow origin`); the longer form is there because a bare `git fetch origin <trunk>` in a
single-branch clone leaves no ref for the check to find. In any CI run with no trunk to compare with — a
checkout of one commit, or any run with `CI`, `GITHUB_ACTIONS` or `GITLAB_CI` set — the check says on stderr that
the slice was NOT checked, with no `git fetch` in it, since nobody can run one on a runner; a local shell with one
of those variables set gets the same line. What that line's exit code is, and how CI gets the history, is the entry
beside this one (*CI's `verify` job now fetches full history*).

Two more things, for a repository whose trunk is not the usual one. A trunk named neither `main` nor `master`,
recorded in `ci.branch`, is compared with for the first time, so slice branches already in flight in such a
repository are now held to the files one slice may touch, and may be refused where they were not. And where
`project.json` records no trunk, `main` and `master` both exist and `master` is the newer, the check still
compares with `main` and says so, on its pass line and where it fails: that `master` is here too, and that the fix
is to set `ci.branch` to `master` in `project.json` on the trunk, or to delete the stale `main`.
A comparison that could not run — git's diff failing, as in a partial clone whose remote is gone — used to pass; it
now fails with git's own first line, on a developer's machine and in CI. Where git cannot read the
checkout at all, the check says so and exits 0, as it always did. No setting, flag or file is added.
