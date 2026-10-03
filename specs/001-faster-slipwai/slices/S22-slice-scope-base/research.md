# Research — S22-slice-scope-base

- **R-1 — Why a minted ref becomes the base.** Read from `assets/toolkit/scripts/check-slice-scope.py`
  `merge_base()`: each of `main`, `origin/main`, `master`, `origin/master` is handed to `git merge-base HEAD
  <name>` as a short name and the newest base wins. Git resolves a short name through `refs/<name>`,
  `refs/tags/<name>`, `refs/heads/<name>`, `refs/remotes/<name>` in that order (gitrevisions(7), *<refname>*),
  so a tag `main` answers before the branch, and any of the four names placed at HEAD yields HEAD as the newest
  base. Reproduced by the adversary (A3, `adversary-log.md`). Decision: full ref names only (D30).
- **R-2 — Where the trunk's name is recorded.** `src/slipwai/adopt.py:185` writes `ci.branch` from
  `default_branch()` (`src/slipwai/delivery_facts.py:51`); `generate` writes no `ci` block, and its workflow
  triggers on `main` (`src/slipwai/project/ci_workflows.py`, `push: branches: [main]`). Decision: working tree's
  `ci.branch`, tolerant, never a `slice/<id>` name (D30). The base's record cannot be used: it needs the base.
- **R-3 — The forge's target variables.** `GITHUB_BASE_REF` is set on `pull_request` runs to the target branch's
  short name (GitHub Actions, *Default environment variables*; Gitea Actions sets the same);
  `CI_MERGE_REQUEST_TARGET_BRANCH_NAME` is GitLab's on merge-request pipelines (*Predefined CI/CD variables*).
  *Assumed* — recalled by the skipper (D30), not read from an artefact in this tree; the checker reads both
  tolerantly, so a wrong assumption costs a missing second candidate, never a wrong base forward.
- **R-4 — What a CI checkout holds.** Generated `verify` job and adopted delivery workflow: `actions/checkout@v6`
  with no `fetch-depth` (`ci_workflows.py`, `adopted_ci.py`) — depth 1, detached, no `refs/remotes/origin/<trunk>`
  on a pull request. *Assumed* from the action's documented default, not run here (D31). The checker's answer
  does not depend on it: it asks git whether a ref and a base exist.
- **R-5 — Making the checkouts in a test.** `git clone --depth 1 --branch slice/S1 file://<repo> <dir>` gives a
  single-branch shallow clone with no trunk ref; adding `--no-single-branch` gives `origin/main` at depth 1 with
  no common ancestor once the slice has a commit of its own; `git checkout --detach` gives the forge's shape.
  `file://` is needed — a plain path clone ignores `--depth`. To be confirmed by the first RED of R5.
- **R-6 — Oldest across two names where neither base is an ancestor of the other.** Decision: `git merge-base`
  of the two bases — behind both, so D30's *the target can only move the base back* still holds; none found, the
  trunk's base. Not among the criteria's examples; covered so the function is defined there.
- **R-7 — The level.** PATCH, `VERSION` stays `1.5.2.dev0`; `changelog.d/` holds two PATCH fragments;
  `tests/test_changelog.py` holds the pairing.
