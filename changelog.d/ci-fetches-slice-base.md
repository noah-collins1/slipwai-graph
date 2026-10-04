PATCH

**CI's `verify` job now fetches full history, so a pull request is held in CI to what `make verify` already holds
on a developer's machine.** The job's checkout carries `fetch-depth: 0`, written unconditionally and the same on
`push` and on `pull_request`, in a generated project's `.github/workflows/verify.yml` and in the
`verify-delivery.yml` that `slipwai adopt` writes (experimental: brownfield adoption); the GitLab job `adopt`
writes, `verify-delivery`, carries `GIT_DEPTH: "0"`. Before, that checkout was one commit with no trunk in it, so
the checks that compare a change with the trunk — `check-slice-scope` and `check-migrations` in every project, and
`check-flags` in a project with a production target of `aws` or `azure`, the only ones that have it — had nothing
to compare with and let the pull request through. No other job fetches differently: the integration jobs, the smoke
jobs, and the event-model, deploy and `ux-gates` workflows are as they were.

**`check-migrations`, and `check-flags` where a project has it, now run their *new in this change* rules in CI, on
every pull request.** They already held them on a developer's machine; CI now gives the same answer. So a pull
request that was green before `slipwai migrate` can be red after it, and this is why. Two refusals are new in CI:
`check-migrations` refuses a contracting migration whose `contract:` names an expand added in the same pull
request, and `check-flags` (in a project that has it) refuses a flag declared in the pull request and seeded
anything but `off`. To clear one, land the expand first and the contract in a later pull request, or seed the new
flag `off`. Both find the trunk by name: a branch called `main` or `master`. Where a repository's trunk has another
name and it has neither branch, they still have nothing to compare with in CI and say nothing, as before;
`check-slice-scope` reads the recorded trunk (`ci.branch`) and holds there. Nothing is newly allowed. Where the
trunk is `main` or `master`, a push to it answers as it did.

**A slice pull request is held to its scope in CI, and *NOT checked* is now a failure.** With history, a
`slice/<id>` pull request that touches what one slice may not is refused in CI as it is locally. Where a CI run
still has no trunk to compare with, or git could not run the comparison, `check-slice-scope` no longer exits 0
saying the slice was NOT checked: it exits 1 with that line, which names what the job's checkout needs —
`fetch-depth: 0`, on GitLab `GIT_DEPTH: "0"`, on any other CI a full clone with the trunk's branch fetched from a
remote named `origin`. The line names the two refs it looked for, `refs/heads/<trunk>` and
`refs/remotes/origin/<trunk>`: a job that clones under another remote name has the history and is still told NOT
checked until the trunk is there under `origin`. A branch that is not `slice/<id>` has nothing to hold, as before;
on a developer's machine every answer is what it was, except that the fetch the check prints now names the branch
in full — `git fetch origin refs/heads/<trunk>:refs/remotes/origin/<trunk>` — so a tag of the trunk's name is never
fetched in its place, and a shell with `CI`, `GITHUB_ACTIONS` or `GITLAB_CI` exported and no trunk to compare with
now fails as CI does; and where git cannot read the checkout at all the check still says so and exits 0.

**Catch-up.** `slipwai migrate` carries the changed workflow into a project that kept it as generated, and replaces
the two files `adopt` wrote. It does not rewrite a workflow you took over or edited at that step (the merge shows
you the change), or a pipeline of your own. There — in any CI job that runs `make verify` on a shallow clone with
`CI`, `GITHUB_ACTIONS` or `GITLAB_CI` set — a `slice/<id>` branch turns red after `migrate` until the job fetches
history: add `fetch-depth: 0` under the checkout's `with:` (on GitLab, `GIT_DEPTH: "0"` under the job's
`variables:`). Where `adopt` writes no CI configuration, its report now says the job needs a full clone with the
trunk's branch fetched. An open pull request that carries an expand with its contract, or a new flag seeded other
than `off`, goes red on its next run, because `check-migrations` and `check-flags` now have the trunk to compare
with in CI: land the expand first and the contract in a later pull request, or seed the new flag `off`. Where CI
checks out the branch's own tip and not its merge with the trunk, a branch whose expand already landed by squash or
rebase and which carries on with the contract is still refused, because the branch's own copy of the expand is what
the check sees: merge the trunk into the branch, or rebase onto it, and the contract passes. A pull request that
targets a branch other than the trunk — a release branch — is compared with the trunk all the same, in CI as on a
full clone: everything that branch has landed since it left the trunk counts as new, so a contract is refused there
although its expand reached that branch in an earlier pull request, and so is a flag declared there earlier and
seeded other than `off` now. It clears once the trunk carries the expand, or the flag's declaration, and that
branch has merged the trunk. Where the trunk is not `main` or `master` and the repository still has a branch of
either name — a release branch, or one left behind by a rename — `check-migrations`, and `check-flags` where a
project has it, compare with that branch in CI, as `make verify` already does on a full clone. Everything the trunk
has that the old branch does not counts as new, on a push to the trunk and on every pull request: an expand and its
contract that both landed since that branch are refused, and so is a flag declared since it and seeded other than
`off`. If the branch is left over, delete it on the remote. If it is your release branch, land the contract once
the expand has reached it. Nothing in `project.json` changes this yet. A repository with a long history pays the
full fetch on that one job, on every run. No setting, flag or file is added.
