PATCH

**`check-slice-scope` compares a slice branch with the trunk's own refs, so a branch no longer empties its own
check by minting a base.** The base was found by short name, so a `master` branch, an `origin/master`, or a tag
named `main` created at the slice's head made the diff empty and the check pass. Only `refs/heads/<trunk>` and
`refs/remotes/origin/<trunk>` answer now, the trunk being `ci.branch` where `project.json` records one and has a
ref, else `main`, else `master`. This asks nothing of a repository already generated: `slipwai migrate` carries
the corrected script.

The trunk is `ci.branch` in `project.json` where that is a branch name with a ref in the checkout, else `main`,
else `master`; a `slice/<id>` name is never one. Where CI names the pull request's target
(`GITHUB_BASE_REF`, `CI_MERGE_REQUEST_TARGET_BRANCH_NAME`) and it has a ref, it is a second candidate, and when the
two bases differ the older one wins, so the target can only move the base back. The line the check prints now says
what it compared with — `compared with `main` at 3f2a9c1` — and, where `ci.branch` names a branch this checkout
does not have, which one and the `git fetch` that would bring it.

**What is promised, locally and on a pull request.** On a developer's machine nothing the slice commits, and no
stray `master`, `origin/master` or tag named `main`, moves the base forward; someone who moves refs in their own
checkout can still defeat it, as they can by moving `main`, and that is not promised against. On a pull request
against the trunk in CI, nothing the branch commits or pushes moves the base forward, given a base to compare with
at all. Left over: a push pipeline with no pull-request target has only the local promise, and a pull request aimed
at a branch other than the trunk is held only as far as `project.json` reaches.

**Catch-up.** Run `slipwai migrate`; it carries the corrected script and asks for nothing else. Two things you may
see afterwards. A slice branch in a checkout with no trunk to compare with — no `main` ref, or a shallow clone too
short to reach the branch point — used to pass as "nothing to hold"; it now fails locally with the command to run
(`git fetch origin <trunk>`, or `git fetch --unshallow origin`). And CI's pull-request checkout, which is depth 1
by default and has no trunk history, does not hold slice scope: it still exits 0, and now says on stderr that the
slice was NOT checked. A maintainer who wants it held adds `fetch-depth: 0` to the verify job's checkout
(`GIT_DEPTH: "0"` on GitLab). No setting, flag or file is added.
