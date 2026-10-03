PATCH

**`check-imports`, `check-migrations` and `check-codegraph` stop reading what the answer never needed.** The two
walking gates listed `apps/` and `packages/` several times a run — three times over, and each browser app again,
on a new Python project that holds 79 entries — and descended into `.venv` and `node_modules`, so after an install they read thousands of files
that are not the project's. Each directory is now listed once, and five directories are not descended into:
`.venv`, `node_modules`, `__pycache__` and `.git` wherever they are, and `target` only at the root of a deployable
`project.json` records as Java with a `pom.xml` there — Maven's output. Any other directory called `target` is
read as before, and a deployable recorded inside a skipped name is still read. Both
pass lines keep their words and end with what was read: `check-imports: inward dependency rule holds (79
directory entries read)`. The count is a measurement, not a limit: no project fails on its size.

One kind of finding can disappear: one on a file inside those directories — an installed package's `domain/`
module or `migrations/`, or Maven's copy of a migration under `target/classes`. Findings on the project's own
code are the same, in the same order, in the same words.

On a `slice/<id>` branch on a developer's machine, `check-codegraph` now hashes only the files that changed since
its last whole comparison instead of every tracked file, and leaves SQLite's integrity check to the full gate; its
pass line says how many files it hashed, of how many, since when, and where the integrity check does run — the
trunk, any other branch and CI. It remembers that comparison in
`.codegraph/gate-memory.json`, beside the index git already ignores, and trusts it only for what it can vouch for:
a file that was uncommitted then, a row the index rewrote since, a file git was told not to report, a changed gate
script or another database each mean that file, or everything, is compared again. A file it does not hash is one
git reports unchanged and whose size, modification time, change time and identity all read as they did when the
gate last hashed it — and a file written within two seconds of that run is hashed again regardless. What that leaves: a file whose bytes were changed while all four read as before — a clock
set back, a filesystem that keeps no such times, a write through a shared memory map where the filesystem moves no
times for it, or, on a platform with no change time, a tool that restores the modification time on a same-size
rewrite — is not seen by a narrowed run; the next whole run sees it: the trunk,
any branch not named `slice/<id>`, or any run after `.codegraph/gate-memory.json` is deleted. On the trunk, on any
other branch and in CI the check compares exactly as it did — every file, and the integrity check — and outside CI
a passing run leaves the record a slice branch then starts from.

Where git does not ignore `.codegraph/` the record is not kept, every run is whole, and the pass line says why.
The pages that describe these gates — `docs/architecture.md` and the verification page in a project, the CodeGraph
extension's block in `AGENTS.md` — say what is no longer read and where the code-index check narrows.

`slipwai migrate` carries the scripts and the corrected pages; nothing is asked of a repository already generated. No setting, flag
or generated file is added.
