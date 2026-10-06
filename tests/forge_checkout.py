"""The checkout a forge makes for a pull request, built with git itself.

`pull_request_checkout` takes an origin repository holding a base branch and a head branch (of any name) and
builds, in a directory the caller owns:

- on the origin, the merge of the head into the base under `refs/pull/1/merge` (what GitHub's `pull_request`
  event checks out);
- a `file://` clone of it with no local branch: the only refs are `refs/remotes/origin/*`, and `HEAD` is
  detached on the merge commit;
- at full history (`depth=None`), every branch of the origin fetched under `refs/remotes/origin/` and the
  merge ref after it, as `actions/checkout` does at `fetch-depth: 0`, and every tag with them (research R-1);
  at `depth=1`, only the merge ref at `--depth 1`, as it does by default:
  no branch of the origin, the base among them, is a ref there.

It returns the path of the checkout. It sets no environment variable, runs no script and knows nothing of what
a caller checks: the caller supplies `GITHUB_HEAD_REF` and the rest.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from support import NO_MAINTENANCE

# Runs git in directories its callers hand it; opens nothing of the repository and generates nothing.
TEST_SELECTION: dict[str, object] = {}

MERGE_REF = "refs/pull/1/merge"


def run(repo: Path, *arguments: str) -> str:
    """One git command in `repo`, its stdout stripped; a failure raises with git's own words."""
    result = subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@local", *NO_MAINTENANCE, *arguments],
                            cwd=repo, text=True, capture_output=True)
    if result.returncode:
        raise AssertionError(f"git {' '.join(arguments)}: {result.stderr}")
    return result.stdout.strip()


def publish_merge(origin: Path, head: str, base: str, scratch: Path) -> None:
    """Merge `head` into `base` in a scratch clone and push the result to the origin's `MERGE_REF`."""
    work = scratch / "merge"
    run(scratch, "clone", "-q", f"file://{origin}", str(work))
    run(work, "checkout", "-q", "-b", "merging", f"origin/{base}")
    run(work, "merge", "-q", "--no-ff", "-m", f"Merge {head} into {base}", f"origin/{head}")
    run(work, "push", "-q", "origin", f"HEAD:{MERGE_REF}")


def pull_request_checkout(origin: Path, head: str, workdir: Path, *, base: str = "main",
                          depth: int | None = None) -> Path:
    """The pull-request checkout of `head` into `base`, under `workdir`, at full history or at `depth`."""
    publish_merge(origin, head, base, workdir)
    clone = workdir / "checkout"
    clone.mkdir()
    run(clone, "init", "-q")
    run(clone, "remote", "add", "origin", f"file://{origin}")
    if depth is None:
        run(clone, "fetch", "-q", "origin", "+refs/heads/*:refs/remotes/origin/*", "+refs/tags/*:refs/tags/*")
        run(clone, "fetch", "-q", "--no-tags", "origin", MERGE_REF)
    else:
        run(clone, "fetch", "-q", "--no-tags", "--depth", str(depth), "origin", MERGE_REF)
    run(clone, "checkout", "-q", "--detach", "FETCH_HEAD")
    for branch in run(clone, "for-each-ref", "--format=%(refname)", "refs/heads").splitlines():
        run(clone, "update-ref", "-d", branch)
    return clone


def source_tip_checkout(origin: Path, head: str, workdir: Path) -> Path:
    """A full-history checkout detached at the tip of `head` itself, not at a merge with the base.

    Every branch and tag of the origin is fetched under `refs/remotes/origin/` and `refs/tags/`, and no local
    branch is left, as in `pull_request_checkout` at full history. It is what a pipeline that checks out the
    source branch's own commit sees; whether a given forge does is not asserted here."""
    clone = workdir / "tip"
    clone.mkdir()
    run(clone, "init", "-q")
    run(clone, "remote", "add", "origin", f"file://{origin}")
    run(clone, "fetch", "-q", "origin", "+refs/heads/*:refs/remotes/origin/*", "+refs/tags/*:refs/tags/*")
    run(clone, "checkout", "-q", "--detach", f"origin/{head}")
    for branch in run(clone, "for-each-ref", "--format=%(refname)", "refs/heads").splitlines():
        run(clone, "update-ref", "-d", branch)
    return clone
