PATCH

**`check-slice-scope` compares a slice branch with the trunk's own refs, so a branch no longer empties its own
check by minting a base.** The base was found by short name, so a `master` branch, an `origin/master`, or a tag
named `main` created at the slice's head made the diff empty and the check pass. Only `refs/heads/<trunk>` and
`refs/remotes/origin/<trunk>` answer now, the trunk being `ci.branch` where `project.json` records one and has a
ref, else `main`, else `master`. This asks nothing of a repository already generated: `slipwai migrate` carries
the corrected script.
