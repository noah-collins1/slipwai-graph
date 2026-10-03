# Research — S23-refusal-in-subdirectory

No dependency is added. What is said of `git` below was read from a run against git 2.53.0 on this machine, in a
scratch repository with the project adopted in `sub/` (cruise iteration 6); what is said of this tree was read
from it.

- **R-1 Why nothing matches.** `changed()` (`src/slipwai/uncommitted.py`) runs `git status --porcelain=v1 -z
  --untracked-files=all` in the project's directory and returns each path as printed. Run: with
  `sub/delivery/commands/ground.md` edited, the entry is ` M sub/delivery/commands/ground.md` — the porcelain
  format spells paths from the repository's top wherever it is run. `refuse_foreign()` tests `path in writes`,
  and `writes()` (`src/slipwai/resurvey.py`) holds `delivery/commands/ground.md`. Run: `adopt --refresh` wrote
  over two edited files at exit 0 and `.delivery-tools/written.json` held `{}`.
- **R-2 The prefix.** Run: `git rev-parse --show-prefix` in `sub/` prints `sub/`; at the top, an empty line; in a
  symbolic link to `sub/`, `sub/`; in `dé pt/`, the raw bytes `d\303\251 pt/` — not quoted. **Decision:** take
  the prefix from git rather than computing it from two resolved paths, so a link and a quoted name need no
  code. **Alternative:** `git rev-parse --show-toplevel` and `Path.relative_to` — rejected: two resolutions of
  the same path that must agree across symlinks and Windows spellings.
- **R-3 The pathspec.** Run: `git status --porcelain=v1 -z --untracked-files=all -- .` in `sub/`, with
  `../other/note.txt` also edited, lists only the entries under `sub/`, still spelled from the top
  (`sub/src/new.py`). A file moved from `other/` into `sub/` with `git mv` is listed as `A  sub/src/moved.txt`
  with no second field. With `-z` no path is quoted (the non-ASCII name above came back as raw bytes).
  **Decision:** limit the status with `-- .` and still drop any entry that does not start with the prefix, so
  the answer does not rest on the pathspec alone.
- **R-4 The same mistake elsewhere.** Every `git` call under `src/slipwai/` was read. `history()` in
  `src/slipwai/structure.py` has it (`git log --name-only`; run: `sub/.gitignore`, where `--relative` prints
  `.gitignore`) — the survey's, placed in the Parking Lot (D38). `add_service.py` and `adopt.py` ask only whether
  anything is uncommitted; `quick_wins.py` (`ls-files`) and `replay.py` (`diff -- <relative>`) are relative to
  where they run.
- **R-5 What an earlier factory left.** In a subdirectory project `stamp()` kept nothing (`path in now` was never
  true), so regenerated files left uncommitted by `--confirm` have no digest. **Decision:** no special case; they
  are refused once and the fragment says so (D37).
