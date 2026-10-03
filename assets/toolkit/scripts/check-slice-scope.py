#!/usr/bin/env python3
"""Hold a slice branch to the files one slice may touch — the shared-surface rule, held mechanically.

Once the event contract is settled, ready slices run concurrently: one delegate per slice, each on a
`slice/<id>` branch in its own worktree, merged back in split order (`commands/drive.md`, *Running ready
slices concurrently*). That works only because the files two slices could fight over are few and named.
This is the list, and the gate on it. On a branch that is not `slice/<id>` there is nothing to hold, and the
script says so and exits 0 — which is why `make verify` runs it everywhere.

What a slice's change may contain — everything since the branch left the trunk, committed or not:

- **its own record**, `specs/<feature>/slices/<id>/**`, and the feature's cumulative artifacts — `spec.md`,
  `story-split.md`, `contracts/`, `checklists/`, `adversary-log.md`, `decisions.md`, `slices/README.md` — which
  every slice amends and the host merges in split order. `decisions.md` is among them because `/cruise` writes
  a decision where the ladder took it, which during a slice's stages is the slice's branch, and `check-decisions`
  wants every `Written to` path in the tree, which for a slice's artifacts is only true there;
- **its own block of `docs/event-model/model.yaml`**: every other slice's block reads exactly as on `main`.
  Events, commands and read models are frames inside a slice's block, so the contract another slice builds
  against cannot move underneath it; `docs/event-model/mockups/` is per screen and open;
- **the committed canvas, `docs/event-model/model.drawio`**, because it is rendered from the model the slice
  just changed and `check-drawio` fails the branch until it is: that gate holds it to `model.yaml`, so it can
  carry nothing of the slice's own. The host regenerates it again after each merge;
- **a new ADR under `docs/adr/`**: a decision taken during the slice whose reversal would be a migration is
  written there at `Proposed`, by `/cruise` or by the slice's own planning. New files only — an ADR that exists
  is never edited; superseding one is the host's, on `main`;
- **code and tests of the service that owns it** — `service` in its model block, or any service where the
  model names none — and, where the block names a `context`, nothing under another context's directory in
  `domain/` or `application/`. A browser app is open to every slice: a white box is one screen. A deployable
  recorded at `.` — an adopted repository's one application — owns every path no other deployable claims, its
  tests and sibling directories included (where several are recorded at `.`, the slice's own `service` if it is
  one of them, else the first listed), except the host's surface: `project.json`, the root `Makefile`
  (`GNUmakefile` and `makefile` too), `.specify/`, CI configuration (`.github/` and its forge siblings, the other
  CI systems `slipwai adopt` recognises, and `ci.gate`), the harnesses' files and directories as
  `<delivery>/scripts/agents/registry.json` names them (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.mcp.json`,
  `.claude/`, `.agents/`, `.kiro/` and the rest; a registry that is missing or unreadable adds nothing), the
  delivery directory less `survey/pinned.md` and `survey/running.md` (where the delivery directory is the root,
  `.written`, `baseline.json` and the other survey pages), and every path in `<delivery>/.written`.
  Git hooks and `.gitignore` are the repository's own. A path is recorded as `x`, `x/` or `./x` alike;
- **the context's events module additively**: a line may be added, none removed. It is the contract. At the
  root deployable of an adopted repository the rule applies only where its record says `"layout": "hexagonal"`,
  as `check-imports` does: `domain/events.py` there may be anything;
- **new migration files only**, timestamped so two slices never mint the same name: `YYYYMMDDHHMM_<name>`,
  or `V<YYYYMMDDHHMM>__<name>` under Flyway. The shipped numbered ones keep working — the order is lexical
  either way, and every stamp sorts after every number. Under the root deployable of an adopted repository a
  new migration carries whatever name the repository's own tool wrote (`0002_add_field.py`, a 14-digit stamp);
  an existing one is still never edited or deleted, there as everywhere;
- **the composition root** — one line per use case, the one code file every slice touches, resolved in
  split order at merge and allowed here for that reason.

Refused, each with what to do instead: the canonical slot at the feature root (`specs/<feature>/plan.md`,
`research.md`, `data-model.md`, `quickstart.md`, `tasks.md` — links into `slices/<id>/`, never committed;
a regular file there is a record about to be lost, on every branch), another slice's directory or model
block, another context's code, an edited or deleted migration, a numbered new migration (outside the root
deployable), and anything else outside every deployable — `Makefile`, `project.json`, package manifests and
locks, `scripts/`, `skills/`, `commands/`, `agents/`, CI, the docs other than the model and its canvas — which is
the host's (under a root deployable, the host's surface above is all of it): landed on `main`
before the fan-out, or handed back as the question it is. A refusal is a hand-back, not something to work around.

Two readings are stated, not coded. A repository whose delivery directory is the root, with a deployable at the
root too, is a layout neither `generate` nor `adopt` produces: the fixed names and `.written` hold there and
nothing more is promised. The harness registry's own fields are the source of the host's paths: a name it carries
only in prose is not read.

The base the branch is compared with is where it left the trunk, or last merged it in, and the trunk is found
by its full ref name: only `refs/heads/<trunk>` and `refs/remotes/origin/<trunk>` answer, so a tag, or a
`master` branch made at the slice's head, cannot stand in for it. The trunk is `ci.branch` in `project.json`
where that is a branch name, not a `slice/<id>` and not `HEAD`, and has a ref in this checkout; else `main`; else
`master`. A ref that is a symbolic ref, such as `origin/HEAD`, is where a remote's checkout points and never a trunk
ref. Where
CI names the pull request's target (`GITHUB_BASE_REF`, `CI_MERGE_REQUEST_TARGET_BRANCH_NAME`) and it has a ref, it
is a second candidate, and where the two bases differ the older one wins, so the target can only move the base
back. Within one name the newer of its local and `origin` base wins: `origin/main` alone goes stale the moment
`main` moves locally and is not yet pushed, and a stale base charges the slice with `main`'s own files. Where
there is a base, what was compared is said: the pass line and the refusal header each carry
`compared with `<trunk>` at <commit>`, with nothing after it but words about a recorded name that was passed over
or the `master` clause below. Where there is none, the no-base line below says so instead. A recorded name that has
a ref and shares no history with the branch is passed over for the next name, and said so; a pull-request target
that does is no base at all. Where the target's base won over the trunk's, the line names the target and says the
pull request targets it.

Where `project.json` records no usable trunk, `main` and `master` both have refs, and `master`'s base is strictly
newer than `main`'s, the same line and header add that `master` is here too and `project.json` records no trunk,
and what to do: set `ci.branch` to `master` in `project.json` on it, or delete the stale `main`. That is words
only: `main` is still the trunk, no base and no exit code changes, and a `master` that is older or level, or a
recorded name that is usable, adds no such clause.

What is promised differs by where it runs. On a developer's machine nothing the slice commits, and no stray
`master`, `origin/master` or tag named `main`, moves the base forward; a person who moves refs in their own
checkout can defeat it, as they can by moving `main` itself. In CI on a pull request against the trunk, nothing the
branch commits or pushes moves the base forward — given a base to compare with at all. A push pipeline with no
pull-request target has only the local promise, and a pull request aimed at another branch is held only as far as
`project.json` reaches.

With no base to compare with, a developer's checkout fails with one line on stderr, of its own and under no
header, naming the command to run: `git fetch origin <trunk>:refs/remotes/origin/<trunk>` where there is no trunk
ref (a bare `git fetch origin <trunk>` in a single-branch clone writes only `FETCH_HEAD`, and the check would say
the same again), `git fetch --unshallow origin` where a shallow clone is too short to reach the branch point. A
header, `a slice branch reaches outside what one slice may touch`, stands only above refused paths and lost
records, with that line after them. A CI run — a detached pull-request checkout (the branch name in `GITHUB_HEAD_REF` or
`CI_COMMIT_REF_NAME`, `HEAD` detached) or any run with `CI`, `GITHUB_ACTIONS` or `GITLAB_CI` set — exits 0 and says
on stderr that the slice was NOT checked, because that checkout is depth 1; the verify job's checkout needs
`fetch-depth: 0` (on GitLab, `GIT_DEPTH: "0"`) for the check to hold there. A local shell with one of those
variables set gets the same NOT-checked line, and one set to `false` still counts: any non-empty value does.
That line carries no `git fetch`, since nobody can run one on a runner. With a usable base a CI run is held
as locally, and a lost record still fails it.

A fetch command is printed only for a plain branch name (`[A-Za-z0-9._/-]`) and where a remote named `origin`
exists, because it is pasted into a shell; otherwise the line says which branch to create or fetch. A recorded value
that is no usable name is printed with its control characters dropped and cut to 80 characters. Where a base was
found and a git call after it fails — the diff, `ls-files`, a `show` of a path that is not merely absent — that is
*could not compare*, never *no changes*: a developer's checkout exits 1 with one line naming the trunk, the base and
git's own first line, and a forge's says NOT checked with that reason and exits 0. Where git cannot read the checkout
at all the check says so on stderr and exits 0.
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import NamedTuple


def project_root(script: Path, depth: int) -> Path:
    """The repository's root: the git work tree's top where it holds a `project.json` and the script is inside it,
    else the nearest ancestor above the script's own tree that holds one, else `depth` levels up. A `project.json`
    a slice plants beside the script or under the delivery directory moves nothing."""
    try:
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=script.parent, text=True,
                             capture_output=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        top = ""
    if top and (Path(top).resolve() / "project.json").is_file() and Path(top).resolve() in script.parents:
        return Path(top).resolve()
    for candidate in script.parents[1:]:
        if (candidate / "project.json").is_file():
            return candidate
    return script.parents[depth]


ROOT = project_root(Path(__file__).resolve(), 1)
# Where the delivery material sits: the root, or `project.json`'s `layout.delivery` where the method was
# installed beside an existing codebase — this script's own tree is `<root>/<delivery>/scripts`. `specs/` stays
# at the root either way; the docs and the model checker move with the material.
DELIVERY = Path(__file__).resolve().parent.parent.relative_to(ROOT)
DOCS = (DELIVERY / "docs").as_posix() + "/"
MODEL = DELIVERY / "docs/event-model/model.yaml"
CANVAS = DELIVERY / "docs/event-model/model.drawio"
ADRS = (DELIVERY / "docs/adr").as_posix() + "/"
SLICE_BRANCH = re.compile(r"^slice/(?P<id>[A-Za-z0-9][A-Za-z0-9._-]*)$")
# A name is held to be a slice's without regard to case: where the filesystem folds case, `Slice/S1` is the ref.
SLICE_NAME = re.compile(SLICE_BRANCH.pattern, re.IGNORECASE)
CANONICAL_SLOTS = ("plan.md", "research.md", "data-model.md", "quickstart.md", "tasks.md")
FEATURE_SHARED = ("spec.md", "story-split.md", "adversary-log.md", "decisions.md")
FEATURE_SHARED_DIRECTORIES = ("contracts", "checklists")
MIGRATION_DIRECTORIES = ("migrations", "migration")
MIGRATION_NAME = re.compile(r"^(?:\d+_|V\d+__)")
MIGRATION_SUFFIXES = {".sql", ".js", ".ts", ".py"}
STAMPED_MIGRATION = re.compile(r"^(?:\d{12}_|V\d{12}__)")
LAYERS_BY_CONTEXT = ("domain", "application")
# The host's surface in a repository whose application is the root: what a slice never writes though the root
# deployable would otherwise own it. A floor — `<delivery>/.written` only ever adds to it. The two survey pages
# the ladder has a slice write are the one part of the delivery directory that is not the host's.
HOST_FILES = ("project.json", "Makefile", "GNUmakefile", "makefile", "AGENTS.md", "CLAUDE.md", ".gitlab-ci.yml",
              "Jenkinsfile", "azure-pipelines.yml", "bitbucket-pipelines.yml", ".woodpecker.yml", ".drone.yml",
              ".travis.yml")
HOST_DIRECTORIES = (".specify", ".github", ".gitea", ".forgejo", ".gitlab", ".circleci", ".claude", ".codex",
                    ".cursor", ".gemini", ".opencode")
SLICE_SURVEY_PAGES = ("survey/pinned.md", "survey/running.md")


def recorded_path(value: object) -> str | None:
    """A path as `project.json` records it, in the one spelling git reports paths in: `x/`, `./x` and `.//x` are `x`;
    `.`, `./` and `./.` are `.`, the whole repository; an empty path, or none, owns nothing."""
    if not isinstance(value, str):
        return None
    if not value.strip("/"):
        return ""
    return "/".join(part for part in value.split("/") if part not in ("", ".")) or "."


# The most the gate reads of any one file in the working tree: a real `project.json`, model, registry or `.written`
# is kilobytes. A file a slice committed as a link to a device, a pipe or something enormous reads as absent.
MAX_READ = 8 * 1024 * 1024


def read_text(path: Path) -> str | None:
    """A file the gate reads, or None: one that is absent, unreadable, not UTF-8, not a regular file (a link to a
    device or a pipe would never end) or larger than `MAX_READ` adds nothing and ends nothing. Every read of the
    working tree goes through here."""
    try:
        if not path.is_file():
            return None
        with path.open("rb") as handle:
            data = handle.read(MAX_READ + 1)
        return None if len(data) > MAX_READ else data.decode("utf-8")
    except (OSError, ValueError):  # UnicodeDecodeError is a ValueError
        return None


def read_json(path: Path) -> object:
    """A JSON file the gate reads, or None where it is absent, unreadable, undecodable, malformed or nested past
    the parser's recursion limit."""
    text = read_text(path)
    if text is None:
        return None
    try:
        return json.loads(text)
    except (ValueError, RecursionError):
        return None


def harness_paths(registry: Path) -> tuple[set[str], set[str]]:
    """The files and the directories the harness registry names as the host's, read as `<delivery>/scripts/agents/
    registry.json` lists them: every row's `contextFile`, `skillsDir`, `commandsDir`, `agentFile.dir`,
    `hooks.projection.where` and `projectMcp.file`. A path with more than one segment makes its first segment the
    host's whole, as `.claude/` is; one segment is that file. A path outside the repository (`~/…`, `/…`) is not
    here, a row of the wrong shape adds nothing, and a registry that is absent, unreadable or not JSON adds
    nothing at all: the fixed names still answer."""
    document = read_json(registry)
    harnesses = document.get("harnesses") if isinstance(document, dict) else None
    files: set[str] = set()
    directories: set[str] = set()
    for row in harnesses if isinstance(harnesses, list) else []:
        found = row_paths(row)
        for value in found:
            parts = [part for part in value.split("/") if part not in ("", ".")]
            if not value.startswith(("~", "/")) and parts:
                (directories if len(parts) > 1 else files).add(parts[0])
    return files, directories


def row_paths(row: object) -> list[str]:
    """The paths one registry row names, or none where the row is not shaped as the registry's rows are."""
    if not isinstance(row, dict):
        return []
    found: list[object] = []
    for keys in (("contextFile",), ("skillsDir",), ("commandsDir",), ("agentFile", "dir"),
                 ("hooks", "projection", "where"), ("projectMcp", "file")):
        value: object = row
        for key in keys:
            if value is None:
                break  # a harness that has no such thing
            if not isinstance(value, dict):
                return []
            value = value.get(key)
        found.append(value)
    return [] if any(value is not None and not isinstance(value, str) for value in found) else [
        value for value in found if value]


def run_git(*arguments: str) -> tuple[str | None, str]:
    """git's stdout, or None where it failed, and git's own first line of stderr — empty where it printed none."""
    try:
        completed = subprocess.run(["git", *arguments], cwd=ROOT, text=True, errors="surrogateescape", capture_output=True)
    except (OSError, ValueError) as error:  # a NUL or a lone surrogate in an argument is a ValueError
        return None, str(error)
    if completed.returncode:
        lines = completed.stderr.strip().splitlines()
        return None, lines[0] if lines else f"git exited with status {completed.returncode}"
    return completed.stdout, ""


def git(*arguments: str) -> str | None:
    return run_git(*arguments)[0]


class CouldNotCompare(Exception):
    """A git call between the base and the verdict failed: the answer is *could not compare*, never *no changes*."""


def git_must(*arguments: str) -> str:
    """Like `git`, but a failure is `CouldNotCompare` with git's first line, so it cannot read as an empty answer."""
    out, reason = run_git(*arguments)
    if out is None:
        raise CouldNotCompare(reason)
    return out


ABSENT = ("does not exist in", "exists on disk, but not in")


def git_show(base: str, path: str) -> str | None:
    """`git show <base>:<path>`: None where the path is absent at the base — an answer — and `CouldNotCompare`
    where git failed for any other reason."""
    out, reason = run_git("show", f"{base}:{path}")
    if out is None and not any(words in reason for words in ABSENT):
        raise CouldNotCompare(reason)
    return out


def checkout_problem() -> str | None:
    """Why git cannot read this checkout at all — its own first line — or None where `git rev-parse --git-dir` works."""
    try:
        completed = subprocess.run(["git", "rev-parse", "--git-dir"], cwd=ROOT, text=True, errors="surrogateescape",
                                   capture_output=True)
    except (OSError, ValueError) as error:
        return str(error)
    if completed.returncode == 0:
        return None
    lines = completed.stderr.strip().splitlines()
    return lines[0] if lines else f"git exited with status {completed.returncode}"


def current_branch() -> str | None:
    """The branch under check: the checkout's, or the pull request's head where CI checks out a detached
    merge commit (`GITHUB_HEAD_REF`, which Gitea Actions sets the same way)."""
    for variable in ("GITHUB_HEAD_REF", "CI_COMMIT_REF_NAME"):
        if os.environ.get(variable):
            return os.environ[variable]
    name = git("rev-parse", "--abbrev-ref", "HEAD")
    if name is None:
        return None
    name = name.strip()
    return None if name == "HEAD" else name


class Base(NamedTuple):
    """What the trunk answered: the commit the branch is compared with (None where there is none), the trunk's
    name, and whether any ref of that name exists in this checkout."""

    commit: str | None
    trunk: str
    has_ref: bool
    passed_over: str = ""  # the report words where `ci.branch` named something that was not used; else empty
    bare: str = ""  # the same words with no `git fetch` command in them: what a forge's output may carry
    targeted: bool = False  # the pull request's target, not the trunk's own base, is what the branch is compared with


def bases_of(name: str) -> tuple[bool, str | None]:
    """Whether `refs/heads/<name>` or `refs/remotes/origin/<name>` exists, and the newest base the branch shares
    with either. Only the full ref names answer — a short name resolves to a tag first, and a tag, like a stray
    branch, is not a trunk. A local `main` moved past `origin/main` and merged into the slice is the newer base:
    trying `origin/main` alone would put `main`'s own files in the slice's diff."""
    exists = False
    bases: list[str] = []
    for ref in (f"refs/heads/{name}", f"refs/remotes/origin/{name}"):
        if git("rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}") is None:
            continue
        if git("symbolic-ref", "-q", ref) is not None:
            continue  # `origin/HEAD` and any alias: where the remote's checkout points, not a trunk
        exists = True
        found = git("merge-base", "HEAD", ref)
        if found and found.strip() not in bases:
            bases.append(found.strip())
    if not bases:
        return exists, None
    newest = bases[0]
    for candidate in bases[1:]:
        if is_ancestor(newest, candidate):
            newest = candidate
    return exists, newest


def is_ancestor(older: str, newer: str) -> bool:
    """`--is-ancestor` exits 0, with nothing printed, when the first commit is an ancestor of the second."""
    return git("merge-base", "--is-ancestor", older, newer) is not None


def target_base(trunk: str) -> tuple[str, str | None] | None:
    """The name CI says the pull request targets (`GITHUB_BASE_REF`; GitLab's `CI_MERGE_REQUEST_TARGET_BRANCH_NAME`)
    and the base under it: the first of the two that is usable, has a ref, and is not the trunk's own name. A
    branch can push what it likes but cannot change its target."""
    for variable in ("GITHUB_BASE_REF", "CI_MERGE_REQUEST_TARGET_BRANCH_NAME"):
        name = usable(os.environ.get(variable))
        if name and name != trunk:
            exists, base = bases_of(name)
            if exists:
                return name, base
    return None


def target_name() -> str | None:
    """The pull request's target where CI gives a usable one, ref or no ref."""
    return next(filter(None, (usable(os.environ.get(v)) for v in ("GITHUB_BASE_REF", "CI_MERGE_REQUEST_TARGET_BRANCH_NAME"))), None)


def older_of(first: str, second: str | None) -> str:
    """Across two names the older base: the one that is an ancestor of the other, else where the two histories
    meet, else the first — the target can only move the base back."""
    if second is None or second == first or is_ancestor(first, second):
        return first
    if is_ancestor(second, first):
        return second
    found = git("merge-base", first, second)
    return found.strip() if found and found.strip() else first


def usable(value: object) -> str | None:
    """A branch name a record may name: a string, stripped, `refs/heads/` taken off, one git accepts as a branch,
    and neither `HEAD` nor a `slice/<id>` in any case — a slice branch is never the trunk. Anything else is None, never an exception."""
    if not isinstance(value, str):
        return None
    name = value.strip()
    name = name[len("refs/heads/"):] if name.startswith("refs/heads/") else name
    if not name or name.startswith(("-", "refs/")) or name.upper() == "HEAD" or SLICE_NAME.match(name):
        return None
    if git("check-ref-format", f"refs/heads/{name}") is None:
        return None
    return name


SAFE_NAME = re.compile(r"^[A-Za-z0-9._/-]+$")


def printable(value: str) -> str:
    """A name the gate did not choose, as it may be printed: control and line-separating characters dropped, a
    backtick made an apostrophe, cut to 80 characters — so it can forge no line and end no span early."""
    kept = "".join("'" if char == "`" else char for char in value
                   if unicodedata.category(char)[0] != "C" and unicodedata.category(char) not in ("Zl", "Zp"))
    return kept[:80]


def has_origin() -> bool:
    return "origin" in (git("remote") or "").split()


def fetch_command(name: str) -> str | None:
    """The fetch that writes the remote-tracking ref this script looks for: a bare `git fetch origin <name>` in a
    single-branch clone fetches the commit into `FETCH_HEAD` and no ref, so the gate would say the same again.
    Printed only for a plain branch name and where a remote called `origin` exists: it is pasted into a shell."""
    if not SAFE_NAME.match(name) or not has_origin():
        return None
    return f"git fetch origin {name}:refs/remotes/origin/{name}"


MASTER_CLAUSE = ("`master` is here too and `project.json` records no trunk — if `master` is the trunk, set "
                 "`ci.branch` to `master` in `project.json` on it, or delete the stale `main`")


def newer_master(main_base: str) -> bool:
    """Whether `master` has a ref and a base strictly newer than `main`'s (D33): words only, never the base."""
    exists, base = bases_of("master")
    return exists and base is not None and base != main_base and is_ancestor(main_base, base)


def merge_base() -> Base:
    """Where the branch left the trunk: the name `ci.branch` of the working tree's `project.json` records where it
    is usable and has a ref, else `main` where it has one, else `master` — so `master` counts only as the recorded
    name or where no `main` exists, and a minted `master` cannot move the base. A recorded name passed over is
    said in `passed_over`."""
    record = read_json(ROOT / "project.json")
    ci = record.get("ci") if isinstance(record, dict) else None
    value = ci.get("branch") if isinstance(ci, dict) else None
    recorded = usable(value)
    names = [recorded] if recorded else []
    names += [name for name in ("main", "master") if name not in names]
    passed_over = bare = ""
    if isinstance(value, str) and value.strip():
        stripped = value.strip()
        if recorded is None and SLICE_NAME.match(stripped.removeprefix("refs/heads/")):
            passed_over = bare = f"`ci.branch` names `{printable(stripped)}`, a slice branch, which is never the trunk"
        elif recorded is None:
            passed_over = bare = f"`ci.branch` names `{printable(stripped)}`, which is not a branch name"
        elif not bases_of(recorded)[0]:
            bare = f"`ci.branch` names `{printable(recorded)}`, which has no branch here"
            command = fetch_command(recorded)
            passed_over = f"{bare} — `{command}` would bring it" if command else bare
    elif value is not None and not isinstance(value, str):
        passed_over = bare = "`ci.branch` is not a string, so it was passed over"
    skipped: list[str] = []  # names with a ref and no history in common with this branch: passed over, not the end
    for name in names:
        exists, base = bases_of(name)
        if exists and base is None:
            skipped.append(name)
            continue
        if exists:
            if skipped:
                said = "; ".join(f"`{other}` has a ref here but shares no history with this branch" for other in skipped)
                passed_over = "; ".join(filter(None, (passed_over, said)))
                bare = "; ".join(filter(None, (bare, said)))
            if recorded is None and name == "main" and base and newer_master(base):
                passed_over = "; ".join(filter(None, (passed_over, MASTER_CLAUSE)))
                bare = "; ".join(filter(None, (bare, MASTER_CLAUSE)))
            target = target_base(name)
            if target and target[1] is None:
                return Base(None, target[0], True, passed_over, bare)  # a target with no history in common is no base
            chosen = older_of(base, target[1] if target else None)
            if target and chosen != base:  # the target's base won: say so, and name the target, not the trunk
                return Base(chosen, target[0], True, passed_over, bare, True)
            return Base(chosen, name, True, passed_over, bare)
    target = target_base(names[0])
    if target:
        return Base(target[1], target[0], True, passed_over, bare, True)
    if skipped:
        return Base(None, skipped[0], True, passed_over, bare)
    return Base(None, target_name() or names[0], False, passed_over, bare)


def changed_files(base: str) -> dict[str, str]:
    """Every path that differs from the base, with its status: `A` added, `M` modified, `D` deleted. The working
    tree is compared, not the last commit, so an uncommitted edit is held the same as a committed one. Paths are
    read NUL-separated (`-z`): git quotes a name with a non-ASCII byte, a tab or a quote otherwise, and a quoted
    path matches no rule."""
    changes: dict[str, str] = {}
    fields = git_must("diff", "--name-status", "-z", "--no-renames", base).split("\0")
    for status, path in zip(fields[0::2], fields[1::2]):
        if path:
            changes[path] = status[:1]
    for path in git_must("ls-files", "-z", "--others", "--exclude-standard").split("\0"):
        if path:
            changes[path] = "A"
    return changes


def deletions(base: str, path: str) -> int:
    for record in git_must("diff", "--numstat", "-z", base, "--", path).split("\0"):
        parts = record.split("\t")
        if len(parts) >= 2 and parts[1].isdigit():
            return int(parts[1])
    return 0


def project_document(base: str) -> dict:
    """`project.json` as the base commit has it — never the branch's own, which a slice could rewrite to hand itself
    ownership of the host's paths. A base with no `project.json` (or an unreadable one) records nothing."""
    text = git_show(base, "./project.json")
    try:
        document = json.loads(text) if text is not None else None
    except (ValueError, RecursionError):
        return {}
    return document if isinstance(document, dict) else {}


def deployables(base: str) -> dict[str, dict]:
    listed = project_document(base).get("deployables")
    return {name: record for name, record in listed.items() if isinstance(record, dict)} if isinstance(listed, dict) else {}


def load_model(text: str) -> object:
    """Parse the model with the loader `check-model` uses, so the two agree on how it reads."""
    checker = ROOT / DELIVERY / "scripts/event-model/check.py"
    if not checker.is_file():
        return None
    spec = importlib.util.spec_from_file_location("event_model_check", checker)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    # Loading the checker must not leave a `__pycache__` beside it: that would be an untracked file outside every
    # deployable, and this very gate would then refuse the branch for something it did itself.
    sys.dont_write_bytecode = True
    spec.loader.exec_module(module)
    sys.path.insert(0, str(module.TOOLS))
    try:
        import yaml  # type: ignore[import-not-found]
    except ImportError:
        module.load_yaml()  # installs the parser beside the checker's other tools
        import yaml  # type: ignore[import-not-found]
    return yaml.safe_load(text)


def slices_of(model: object) -> dict[str, dict]:
    if not isinstance(model, dict) or not isinstance(model.get("slices"), list):
        return {}
    return {str(item["id"]): item for item in model["slices"] if isinstance(item, dict) and "id" in item}


class Scope:
    """What one slice may touch, read off the branch, the model and the manifest."""

    def __init__(self, slice_id: str, base: str) -> None:
        self.slice_id = slice_id
        self.base = base
        self.apps = deployables(base)
        self.host: tuple[set[str], set[str], set[str]] | None = None
        model_text = read_text(ROOT / MODEL)
        self.model = load_model(model_text) if model_text is not None else None
        own = slices_of(self.model).get(slice_id, {})
        self.service = own.get("service") if isinstance(own.get("service"), str) else None
        self.context = own.get("context") if isinstance(own.get("context"), str) else None

    def service_path(self, name: str) -> str | None:
        record = self.apps.get(name)
        return recorded_path(record.get("path") if record else None)

    def other_contexts(self) -> list[str]:
        if self.service is None or self.context is None:
            return []
        record = self.apps.get(self.service, {})
        contexts = record.get("contexts") if isinstance(record.get("contexts"), list) else []
        return [str(context) for context in contexts if str(context) != self.context]

    def owning_app(self, path: str) -> str | None:
        """The deployable a path sits under, by its recorded `path`, or None for a path outside every app.
        A deployable at `.` (or `./`) is the whole repository, so it is asked last: it owns what no deployable
        in a subdirectory claims. Where several are recorded at `.`, the slice's own `service` owns the path if it
        is one of them, else the first listed."""
        roots = []
        for name in self.apps:
            app_path = self.service_path(name)
            if app_path == ".":
                roots.append(name)
            elif app_path and (path == app_path or path.startswith(app_path + "/")):
                return name
        if self.service in roots:
            return self.service
        return roots[0] if roots else None

    def host_surface(self, path: str) -> bool:
        """Whether a path is the host's where the root deployable would own it: the fixed names, the delivery
        directory (unless it is the root) less the slice's two survey pages, the recorded CI gate, and every path
        the factory wrote under `<delivery>/.written`."""
        files, directories, written = self.host_names()
        if path in files or path.split("/")[0] in directories or path in written:
            return True
        slice_pages = [(DELIVERY / page).as_posix() for page in SLICE_SURVEY_PAGES]
        if DELIVERY == Path("."):
            # The repository is the delivery directory, so the code is the slice's; only the delivery's own
            # ledger and survey stay the host's.
            return path in (".written", "baseline.json") or (path.startswith("survey/") and path not in slice_pages)
        return Path(path).is_relative_to(DELIVERY) and path not in slice_pages

    def host_names(self) -> tuple[set[str], set[str], set[str]]:
        """The host's files, directories and exact paths, read once for the run: the fixed names, the harness
        registry, `ci.gate`, and `<delivery>/.written`."""
        if self.host is None:
            files, directories = harness_paths(ROOT / DELIVERY / "scripts/agents/registry.json")
            files |= set(HOST_FILES)
            directories |= set(HOST_DIRECTORIES)
            ci = project_document(self.base).get("ci")
            gate = ci.get("gate") if isinstance(ci, dict) else None
            exact = {recorded_path(gate)} if isinstance(gate, str) else set()
            ledger = read_text(ROOT / DELIVERY / ".written")
            exact |= {line.strip() for line in (ledger or "").splitlines() if line.strip()}
            self.host = files, directories, exact
        return self.host

    def spec_violation(self, path: str) -> str | None:
        parts = path.split("/")
        if len(parts) < 3:
            return f"{path}: a slice writes under a feature directory, `specs/<feature>/`, never beside one."
        feature, rest = parts[1], parts[2:]
        if rest[0] in CANONICAL_SLOTS and len(rest) == 1:
            return (
                f"{path}: the canonical slot is a link into `specs/{feature}/slices/{self.slice_id}/`, where the "
                f"record lives, and is never committed. Move the file there, `ln -s slices/{self.slice_id}/{rest[0]} "
                f"specs/{feature}/{rest[0]}`, and leave the link unstaged."
            )
        if rest[0] == "slices":
            if len(rest) == 2 and rest[1] == "README.md":
                return None
            if len(rest) >= 2 and rest[1] == self.slice_id:
                return None
            other = rest[1] if len(rest) >= 2 else "?"
            return (
                f"{path}: slice `{other}`'s record. A slice writes `slices/{self.slice_id}/` only; if `{other}` "
                f"needs a change, that is a question for the host."
            )
        if rest[0] in FEATURE_SHARED or rest[0] in FEATURE_SHARED_DIRECTORIES:
            return None
        return (
            f"{path}: not a slice's to write. A slice amends `spec.md`, `story-split.md`, `contracts/`, "
            f"`checklists/`, `adversary-log.md`, `decisions.md` and its own `slices/{self.slice_id}/`."
        )

    def model_violations(self) -> list[str]:
        """Every other slice's block must read as it does on the base."""
        if self.model is None:
            return []
        base_text = git_show(self.base, MODEL.as_posix())
        if base_text is None:
            return []
        base_slices, head_slices = slices_of(load_model(base_text)), slices_of(self.model)
        violations = []
        for slice_id, block in base_slices.items():
            if slice_id == self.slice_id:
                continue
            if slice_id not in head_slices:
                violations.append(
                    f"{MODEL}: slice `{slice_id}` is gone. A slice branch edits its own block of the model and "
                    f"removes nothing; removing a slice is the host's, on `main`."
                )
            elif head_slices[slice_id] != block:
                violations.append(
                    f"{MODEL}: slice `{slice_id}`'s block changed on `{self.slice_id}`'s branch. The contract "
                    f"another slice builds against does not move under it: hand the change back to the host."
                )
        return violations

    def root_owned(self, path: str) -> bool:
        """Whether the path is the root deployable's own code: its owner is recorded at `.` and it is not the
        host's. Where it is, the repository's own tools name migrations and its own layout is not the factory's."""
        app = self.owning_app(path)
        return app is not None and self.service_path(app) == "." and not self.host_surface(path)

    def migration_violation(self, path: str, status: str) -> str | None:
        name = Path(path).name
        if self.root_owned(path):
            if status == "A":
                return None  # whatever name the repository's own tool wrote
            return (
                f"{path}: an existing migration was {'deleted' if status == 'D' else 'edited'}. A slice adds "
                f"migrations and never changes one that shipped — the release running against the database "
                f"already applied it. Add a new migration with the repository's own tool instead."
            )
        if status != "A":
            return (
                f"{path}: an existing migration was {'deleted' if status == 'D' else 'edited'}. A slice adds "
                f"migrations and never changes one that shipped — the release running against the database "
                f"already applied it. Add a new, timestamped migration instead."
            )
        if not STAMPED_MIGRATION.match(name):
            stamp = "202609151030"
            return (
                f"{path}: a new migration on a slice branch is timestamped — `{stamp}_{name.split('_', 1)[-1]}` "
                f"(`V{stamp}__…` under Flyway), `date -u +%Y%m%d%H%M` for the stamp — so two slices never mint "
                f"the same name. A number is what the sibling branch is also about to take."
            )
        return None

    def code_violation(self, path: str, status: str) -> str | None:
        app = self.owning_app(path)
        if app is not None and self.service_path(app) == "." and self.host_surface(path):
            app = None
        if app is None:
            return (
                f"{path}: outside every deployable and not a slice's to write — shared configuration, tooling and "
                f"docs are the host's. Land it on `main` before the fan-out, or hand it back as the question it is."
            )
        record = self.apps.get(app, {})
        if record.get("kind") == "service" and self.service is not None and app != self.service:
            return (
                f"{path}: service `{app}` is not slice `{self.slice_id}`'s (`service: {self.service}` in the model). "
                f"A slice's code lives in the service that owns it; a change another service needs is a slice of "
                f"its own."
            )
        parts = Path(path).parts
        for layer in LAYERS_BY_CONTEXT:
            if layer in parts:
                index = parts.index(layer)
                if index + 1 < len(parts) and parts[index + 1] in self.other_contexts():
                    return (
                        f"{path}: bounded context `{parts[index + 1]}` is not slice `{self.slice_id}`'s "
                        f"(`context: {self.context}`). One context per slice; a change there is another slice's."
                    )
        stem = Path(path).stem
        # An adopted application's `domain/events.py` may be anything: at the root the events rule is opt-in, as
        # `check-imports` makes its layer rules, by the record's `"layout": "hexagonal"`.
        generic = self.service_path(app) == "." and record.get("layout") != "hexagonal"
        if not generic and "domain" in parts and stem.lower().endswith("events") and status != "A" and deletions(self.base, path):
            return (
                f"{path}: the events module is the contract and grows additively — a line was removed. Add the new "
                f"shape beside the old; retiring one is the host's, once nothing folds it."
            )
        return None

    def violation(self, path: str, status: str) -> str | None:
        if path.startswith("specs/"):
            return self.spec_violation(path)
        if path == MODEL.as_posix():
            return None
        if path == CANVAS.as_posix():
            # Rendered from the model, and `check-drawio` holds it to the model: a slice that advanced its own
            # block has to regenerate it to pass `verify`, and can put nothing else in it.
            return None
        if path.startswith(DOCS + "event-model/mockups/"):
            return None
        if path.startswith(ADRS) and path.endswith(".md"):
            if status == "A":
                return None
            return (
                f"{path}: an ADR that exists was {'deleted' if status == 'D' else 'edited'} on a slice branch. A "
                f"slice adds an ADR at `Proposed`; superseding or accepting one that stands is the host's, on `main`."
            )
        if path.startswith(DOCS):
            return f"{path}: the docs are the host's; a slice writes its record under `specs/` and the model."
        parent = Path(path).parent.name
        if parent in MIGRATION_DIRECTORIES and Path(path).suffix in MIGRATION_SUFFIXES and MIGRATION_NAME.match(
            Path(path).name
        ):
            return self.migration_violation(path, status)
        return self.code_violation(path, status)


def lost_records() -> list[str]:
    """A regular, untracked file at a canonical slot, on any branch: the Spec Kit command wrote through the link
    and something replaced it, and `.gitignore` would now hide the only copy of the record."""
    findings = []
    specs = ROOT / "specs"
    if not specs.is_dir():
        return findings
    tracked = set((git("ls-files", "-z", "specs") or "").split("\0"))
    for feature in sorted(specs.iterdir()):
        for slot in CANONICAL_SLOTS:
            candidate = feature / slot
            relative = candidate.relative_to(ROOT).as_posix()
            if candidate.is_file() and not candidate.is_symlink() and relative not in tracked:
                findings.append(
                    f"{relative}: a regular file at the canonical slot, untracked and ignored — the record is "
                    f"about to be lost. Move it under `specs/{feature.name}/slices/<id>/` and link the slot to it."
                )
    return findings


def forge_checkout() -> bool:
    """A forge's checkout, by either route (D31, D32): the branch name came from a variable and `HEAD` is detached,
    or the environment says the run is CI — `GITHUB_ACTIONS`, `GITLAB_CI` or `CI` non-empty. Anything else is a
    developer's."""
    if any(os.environ.get(v) for v in ("GITHUB_ACTIONS", "GITLAB_CI", "CI")):
        return True
    named = any(os.environ.get(v) for v in ("GITHUB_HEAD_REF", "CI_COMMIT_REF_NAME"))
    return named and git("symbolic-ref", "-q", "HEAD") is None


def not_checked(slice_id: str, trunk: str, note: str = "") -> str:
    """The forge's answer where there is no base: not a pass, not a failure, and said on stderr (D31). It names
    no `git fetch`: the fix there is the job's checkout, not a command a person runs."""
    said = f"; {note}" if note else ""
    return (f"check-slice-scope: slice/{slice_id} was NOT checked — this CI checkout has no `{trunk}` history to "
            "compare with. The check holds on a developer's machine; for it to hold here the verify job's "
            f"checkout needs `fetch-depth: 0` (on GitLab, `GIT_DEPTH: \"0\"`){said}.")


def check(branch: str | None) -> tuple[list[str], str, str, str, bool]:
    """The violations, the one line to print when there are none, what the refusal header ends with, a line
    for stderr that is neither — printed after any findings — and whether that line is a developer's failure."""
    violations = lost_records()
    match = SLICE_BRANCH.match(branch or "")
    problem = checkout_problem()
    unreadable = f"check-slice-scope: git could not read this checkout — {problem}" if problem else ""
    if match is None:
        where = f"on `{branch}`" if branch else "on a detached checkout"
        return (violations, f"check-slice-scope: {where}, not a `slice/<id>` branch — nothing to hold", "", unreadable,
                False)
    if problem:
        return violations, "", "", unreadable, False  # exit 0 as before the slice: there is nothing to compare with
    slice_id = match.group("id")
    found_base = merge_base()
    base = found_base.commit
    note = f"; {found_base.passed_over}" if found_base.passed_over else ""
    if base is None:
        if forge_checkout():
            return violations, "", "", not_checked(slice_id, found_base.trunk, found_base.bare), False
        trunk = printable(found_base.trunk)
        command = fetch_command(found_base.trunk)
        if not found_base.has_ref:
            line = f"slice/{slice_id} has no `{trunk}` to compare with, so nothing can be held"
            if command is None:
                line += f" — create or fetch a local `{trunk}` branch"
            elif f"`{command}`" not in found_base.passed_over:  # the note below may have said it already
                line += f" — run `{command}`"
        elif (git("rev-parse", "--is-shallow-repository") or "").strip() == "true":
            line = f"slice/{slice_id} shares no history with `{trunk}` at this depth — " + (
                "run `git fetch --unshallow origin`" if has_origin() else "fetch the missing history")
        else:
            line = f"slice/{slice_id} shares no history with `{trunk}` — a slice branch is cut from `{trunk}`"
        return violations, "", "", f"check-slice-scope: {line}{note}", True
    short = (git("rev-parse", "--short", base) or base).strip()
    compared = f"compared with `{printable(found_base.trunk)}` at {short}"
    if found_base.targeted:
        compared += f", which the pull request targets"
    try:
        scope = Scope(slice_id, base)
        for path, status in sorted(changed_files(base).items()):
            found = scope.violation(path, status)
            if found:
                violations.append(found)
        violations.extend(scope.model_violations())
    except CouldNotCompare as error:  # D31, D32: the diff did not run, so there is nothing to say passed
        why = str(error) or "git gave no reason"
        if forge_checkout():
            return violations, "", "", (f"check-slice-scope: slice/{slice_id} was NOT checked — git could not compare it "
                                        f"with `{found_base.trunk}` at {short}: {why}"), False
        return violations, "", "", (f"check-slice-scope: slice/{slice_id} could not be compared with "
                                    f"`{found_base.trunk}` at {short} — {why}"), True
    return violations, f"check-slice-scope: slice/{slice_id} touches only what one slice may ({compared}){note}", \
        f" — {compared}{note}", "", False


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(errors="backslashreplace")  # a recorded name with a lone surrogate must not end the run
    violations, report, note, notice, failed = check(current_branch())
    if violations:
        print(f"check-slice-scope: a slice branch reaches outside what one slice may touch{note}\n", file=sys.stderr)
        for violation in violations:
            print(f"  {violation}", file=sys.stderr)
        print(file=sys.stderr)
    if notice:
        print(notice, file=sys.stderr)
    if violations or failed:
        return 1
    if report:
        print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
