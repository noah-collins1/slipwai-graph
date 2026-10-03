# Research: S01-gate-walks

Each statement about a dependency's behaviour cites what it was read from; one with no citation reads *assumed*.

- **R-1 What the walks cost today.** On the skeleton, `apps/` and `packages/` hold 79 entries (56 files, 23
  directories) and one run of `check-imports` lists 256: `source_files()` is called three times (rules 1, 2, 3)
  and rule 4 walks `apps/web` (19) again. *Read from:* a run against `/tmp/s01gaps/shop/shop` (host and the D47
  skipper, independently), cruise iteration 7.
- **R-2 `os.walk` against `Path.rglob`.** `os.walk(top)` is top-down by default, lets the caller remove names from
  `dirnames` in place to stop descent, and does not follow symbolic links to directories unless `followlinks` is
  true; a link to a directory is listed among `dirnames`. *Read from:* the Python 3.13 library reference, `os.walk`.
  `Path.rglob` does not follow symbolic links by default from 3.13 (`recurse_symlinks=False`); earlier versions
  did. *Read from:* the 3.13 reference, `Path.rglob`, *Changed in version 3.13*. The skeleton pins 3.13
  (`.python-version` in the generated tree). On a project run with an older `python3`, a linked directory was
  descended and no longer is: stated in AC-S01-9.
- **R-3 Audit events.** `open()` raises the audit event `open` with the path; `os.scandir()` raises `os.scandir`
  with the path, and `os.walk` and `Path.rglob` list through `os.scandir`. *Read from:* the 3.13 reference,
  *Audit events table*; to be confirmed by the first RED run of R2e4 — until then *assumed* for `rglob`.
- **R-4 What git reports.** `git diff --name-only <commit>` compares the working tree with the commit, so it
  covers committed, staged and unstaged changes to tracked paths, and a path added to the index; `--no-renames`
  reports a rename as a removal and an addition. A path marked `assume-unchanged` or `skip-worktree` is not
  compared; `git ls-files -v` prints such paths with a lower-case tag or `S`. *Read from:* `git-diff(1)`,
  `git-ls-files(1)` (`-v`), `git-update-index(1)`; the flags are exercised by R8e5's RED run.
- **R-5 The index.** `files(path, content_hash, indexed_at)` are the three columns the gate reads
  (`check-codegraph.py`, `rows_of`). Whether CodeGraph moves `indexed_at` on every rewrite is *assumed* nowhere:
  the design compares rows by content (D46, rule 6). The rebuild moves the database aside and makes a new file
  (`agents/code_index.py`, `set_aside`, `health`), so a rebuilt database has another inode.
- **R-6 `.codegraph/` is ignored.** The generated `.gitignore` carries `.codegraph/` (line 20 of the skeleton's).
  An adopted repository's may not: the memory is written only where `git check-ignore -q` says the path is
  ignored (R10e4).
