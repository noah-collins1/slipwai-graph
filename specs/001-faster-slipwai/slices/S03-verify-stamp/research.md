# Research: S03-verify-stamp

Each item says what it was read from. *Assumed* means nobody read it yet, and names the cycle that must.

1. **The recipe shape.** Spiked on GNU Make 4.4.1 (this machine): a `verify` recipe of the form
   `@stamp reuse … || { $(MAKE) --no-print-directory verify-checks && stamp record; }`. Seen: a passing run prints
   exactly what the prerequisites and the closing lines print, with no *Entering directory*; the line runs under
   `-n`, `-t` and `-q` because it contains `$(MAKE)` (GNU Make manual, *How the MAKE Variable Works*), so the
   script itself must decline in those modes; `MAKEFLAGS` reaches the script with the single-letter flags as its
   first word (`n`, `i`, `in`, `k`; empty or a leading space when there are none, then `-j4 …` or `-- VAR=value`)
   (*Communicating Options to a Sub-make*); under `-i` the sub-make exits 0 on a failing check, which is why
   `record` reads the flags too; a variable given on the command line (`make verify VERIFY_FORCE=1`) is in the
   recipe's environment; `$(MAKECMDGOALS)` is `ci` under `make ci`; `-j4` passes its job server to the sub-make. A
   failing run's last lines gain make's own `make[1]: ***` beside `make: *** [Makefile:N: verify] Error 2`: the
   checks' output is unchanged, make's trailer is not, and no criterion holds the trailer. **Assumed**: the same
   under GNU Make 3.81 (no 3.81 on this machine); the flags are parsed as *the first word, only where it is made
   of letters*, which is the documented form in both.
2. **What a covered file is.** `git ls-files -z --cached --others --exclude-standard`, run in the project's
   directory, lists tracked files and untracked files git does not ignore, under that directory only (run here on
   the scratch project and on this repository). A tracked file deleted from disk is still listed and is hashed as
   *missing*. An untracked directory that is a repository is listed as one entry ending in `/` (git's
   documentation of `--others`; **assumed** until R10's cycle plants one). `git ls-files -z --stage` gives the
   index's entries; `git ls-files -v` marks `assume-unchanged` with a lower-case letter and `skip-worktree` with
   `S` (git-ls-files documentation, `-v`); a submodule is an entry of mode `160000`.
3. **History.** `git symbolic-ref -q HEAD`, `git rev-parse -q --verify HEAD` (an unborn branch is a value, not a
   failure), `git for-each-ref refs/heads refs/remotes`, and the bytes of the file `git rev-parse --git-path
   shallow` names. The trunk is D30 and D33's resolution, which `assets/toolkit/scripts/check-slice-scope.py`
   already implements: **one definition** — the stamp script loads that function, or, where the module cannot be
   loaded without running, a test holds the two answers equal over D30's and D33's cases.
4. **Time.** Measured at the gaps stage: every covered file's raw bytes hashed in 60 ms on this repository (2181
   files); the version questions of `uv`, `python3`, `node`, `git` and `make` 0.10 s together, one after another;
   `python3` starting about 20 ms; a git call 3 to 5 ms. The whole reuse run is budgeted at a quarter of a second
   on the fixture; the demo measures it.
5. **The fixture and its stand-ins.** Run here: a project generated with `--profile standard --backend python
   --http none --frontend none`, on a branch `topic`, with a `uv` stand-in first on `PATH` that logs its
   arguments and exits 0, passes its whole `make verify` in 0.54 s and leaves nothing for `git status` but ignored
   `__pycache__`. The event-modelling profile with a transport does not pass that way (`check-openapi` needs the
   real environment) and its first gate writes an untracked `scripts/event-model/package-lock.json` — a run whose
   key moves, which R9's *not recorded* line is for. The `uv` stand-in must also do the one thing the key reads of
   a sync: write `apps/service/.venv/pyvenv.cfg` with the lines uv writes (`version_info = 3.14.4`, `uv =
   0.12.20`; read from environments uv 0.12 made on this machine). A stand-in is a fake in the test tree
   implementing the tool's command line (`AGENTS.md`, *Tests written here*); the demo validates it against the
   real toolchain. Tests build their environment with `CI`, `GITHUB_ACTIONS` and `GITLAB_CI` removed unless the
   example sets one.
6. **How the script reaches a project.** *Assumed until read*: the files under `assets/toolkit/scripts/` are
   copied whole into a project's `scripts/` (and an adopted repository's `delivery/scripts/`, where this one is
   never called), and `slipwai migrate` replaces them with the `Makefile`. The first cycle reads the copier and
   `migrate`'s file list, and `tests/test_toolkit.py` and `tests/test_monorepos.py` for a list naming the
   script's neighbours, and adds the new file wherever one does.
7. **The page.** *Assumed until read*: a generated project's own page about its gate is written under
   `src/slipwai/project/` (search for *Full deterministic* and for `make verify` in `readme`, `rules` and the
   toolkit's `docs/`). The first cycle of `[US3]` finds it; the paragraph goes where the gate is first described.
8. **What the checks read that git ignores.** Read at the gaps stage: `.codegraph/codegraph.db`
   (`check-codegraph.py`; its own `gate-memory.json` is that check's memo of itself and is written by every pass,
   so it is *not* an input); the harness projection directories `src/slipwai/project/gitignore.py` ignores, which
   `check-agents` compares with their sources; `tools/ux-gates/` (`check-ux-gates.py`) and `skills/ui-ux-pro-max/`
   (the extension's ignore lines in `catalog.json`). **Assumed until R6's cycle reads them**: what a kit
   installed under `tools/ux-gates/` consists of and which file pins it; whether any gate step reads `.env` — it
   joins the list by its bytes either way, since a test suite may. Variables: `check-ux-gates.py` and
   `check-codegraph.py` for the five, `check-slice-scope.py` for `GITHUB_HEAD_REF` and `CI_COMMIT_REF_NAME`.
9. **Windows.** *Assumed, not run* (no Windows here; D81): a tool is launched without a shell, which on Windows is
   believed not to find `npm.cmd`; such a project would run the full gate every time and say `npm` is not on
   `PATH`. Nothing false is recorded. The story split's Parking Lot carries the line.

