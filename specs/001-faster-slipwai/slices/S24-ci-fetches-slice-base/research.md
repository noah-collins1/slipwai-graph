# Research — S24-ci-fetches-slice-base

No dependency is added. What is said of a forge below is cited to the page it was read from on 2026-10-04 and was
**not run**: this run pushes nothing (D12). What is said of this tree was read from it.

- **R-1 What `actions/checkout@v6` leaves at `fetch-depth: 0`.** The action's README
  (`https://github.com/actions/checkout/blob/v6/README.md`): *"Only a single commit is fetched by default, for the
  ref/SHA that triggered the workflow"*; `fetch-depth` — *"Number of commits to fetch. 0 indicates all history for
  all branches and tags. Default: 1"*; and on a pull request the checkout is *"in detached HEAD mode"*. So with the
  key the checkout holds every branch under `refs/remotes/origin/` — the trunk among them — and `HEAD` detached on
  the pull request's merge commit. That the detached commit is the merge of the head into the base
  (`refs/pull/<n>/merge`) is **assumed** from GitHub's documented `pull_request` event (`GITHUB_SHA` is the *last
  merge commit on the `GITHUB_REF` branch*); nothing in the plan rests on merge-versus-head: either has `main` as
  an ancestor or shares one with it. Gitea and Forgejo run the same action from the same file: **assumed**, as D32
  already took it.
- **R-2 What a GitLab runner fetches at `GIT_DEPTH: "0"`.** GitLab's *Configuring runners*
  (`https://docs.gitlab.com/ci/runners/configure_runners/`): `GIT_DEPTH` can be set *"globally or per-job in the
  `variables` section"*, and new projects default to a depth of 20. GitLab's *CI/CD pipeline settings*
  (`https://docs.gitlab.com/ci/pipelines/settings/`): *"To disable shallow clone and make GitLab CI/CD fetch all
  branches and tags each time, keep the value empty or set to `0`"*, and the setting *"can be overridden by the
  `GIT_DEPTH` variable"*. So a job-level `GIT_DEPTH: "0"` gives `verify-delivery` every branch, whatever the
  project's setting. `GIT_STRATEGY: none`, set by a repository's own configuration, would defeat it: **assumed**
  rare, and then the check fails saying what it needs — which is the point of R4.
- **R-3 What the three checks do with it.** `check-slice-scope.py` `merge_base()` reads only
  `refs/heads/<trunk>` and `refs/remotes/origin/<trunk>` (D30). `check-migrations.py` tries `main`, `origin/main`,
  `master`, `origin/master` by short name and takes the newest merge base; `check-flags.py` (aws, azure) tries
  `origin/main`, `main`, `origin/master`, `master` and takes the first. D54's skipper ran both shipped scripts in
  scratch repositories: a pull-request merge ref at depth 1 with no trunk ref — both exit 0; the same with all
  branches fetched — both exit 1 on an expand and contract together and on a flag seeded `on`; a push to the trunk
  — both exit 0 at either depth. R5's tests are that run, kept.
- **R-4 What `migrate` does with each file.** `docs/upgrading.md`, *What the merge does, file by file*: a file only
  the factory changed since the base is taken silently, *"where … the CI workflow … mostly land"*; one both changed
  merges, or conflicts where the hunks meet. So a generated project's `verify.yml` gains the key unless its
  maintainer edited that step. `docs/adopting.md`: an adopted repository's `verify-delivery.yml` and GitLab job are
  listed in `.written` and replaced; one a person took over (its line deleted from `.written`) *"meets yours in
  `slipwai migrate`'s three-way merge"*. The repository's own `.gitlab-ci.yml`, and any CI the factory did not
  write, are never touched. The catch-up paragraph is written to those three cases.
- **R-5 Who else reads history in the `verify` job.** Swept at the gaps stage (D84): only the three scripts above.
- **R-6 Where the old answer is written down.** `assets/toolkit/scripts/check-slice-scope.py` (the docstring's
  paragraph on a CI run; `not_checked()`), `changelog.d/slice-scope-base.md` (*Catch-up*, and its last paragraph),
  and the tests named in the plan. A search of `docs/`, `assets/` and `src/slipwai/` for *NOT checked*,
  `fetch-depth` and *depth 1* finds no other statement of it; the implementation repeats the search.
