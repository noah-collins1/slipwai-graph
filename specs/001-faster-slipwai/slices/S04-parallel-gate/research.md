# Research: S04-parallel-gate

Every statement about a tool's behaviour cites what it was read from or the run that showed it. Runs are from
cruise iteration 13, 2026-10-04, this machine (Linux, GNU Make 4.4.1, uv, node and npm, go, java), on projects this
checkout's `./slipwai generate … --no-init --no-install --skip-checks` made under a scratch directory.

## R-1 What `.NOTPARALLEL` does, and what orders targets on every GNU Make

- **Read:** GNU Make's own NEWS (`/usr/share/doc/make/NEWS.gz`). Version 3.79: *"A new pseudo-target .NOTPARALLEL
  is available. If defined, the current makefile is run serially regardless of the value of -j. However, submakes
  are still eligible for parallel execution."* Version 4.4: *"New feature: .NOTPARALLEL accepts prerequisites. If the
  .NOTPARALLEL special target has prerequisites then all prerequisites of those targets will be run serially (as if
  .WAIT was specified between each prerequisite)."*
- **Run (4.4.1):** `all: a b c` with `.NOTPARALLEL: b` and `-j3`, each recipe sleeping one second: a, b and c
  started together and the run took 1.0 s. `a b: w` with `-j3`: w ran alone, then a and b together, 2.0 s.
- **So:** a bare `.NOTPARALLEL:` serialises a makefile on every version since 3.79; naming a target isolates it on
  none. A prerequisite is what orders two targets everywhere. `.WAIT` is 4.4 only and is not used.
- **Assumed, not run:** GNU Make 3.81 and 4.3 — none on this machine.

## R-2 The gate's sub-make under `-j`

- **Run (4.4.1):** `verify`'s recipe names `"$(MAKE)"`, so make treats the line as a recursive make and the
  sub-make shares the jobs: on the Python project `make -j verify` ran the checks together (R-6).
- **Run (4.4.1):** in a sub-make a failed target is reported as `make[1]: *** [M4:5: a] Error 1`, then
  `make[1]: *** Waiting for unfinished jobs....`, then the other running target's output and its own `***` line,
  and last the outer `make: *** [M4:2: v] Error 2`. A line the recipe echoes after the sub-make returns is printed
  before that last line.
- **Read:** NEWS, version 3.81: *"New special variables available in this release: … .FEATURES: Contains a list of
  special features available in this version of GNU Make"*; version 4.0: *"New command line option: --output-sync
  (-O) enables grouping of output by target or by recursive make."* **Run (4.4.1):** `$(.FEATURES)` lists
  `output-sync`, and
  `$(if $(filter output-sync,$(.FEATURES)),--output-sync=target)` expanded to the option and the sub-make took it.
  The decision's delegate (D89) ran a serial sub-make with the option and saw lines arrive as produced; the task's
  test holds that (AC-S04-12).

## R-3 A make variable set by one recipe and read by another, for the skip line

- **Run (4.4.1):** a file target whose recipe ends `$(eval INSTALLED := yes)`, and a phony target depending on it
  whose recipe is `@$(if $(INSTALLED),true,echo '… not reinstalled')`: fresh, under `-j4`, the install ran and the
  line was not printed; second run, no install and the line was printed; after touching the manifest, the install
  ran and the line was not printed. A recipe is expanded when its target is about to run, after its prerequisites.
- **Read:** NEWS, version 3.80: *"A new function is defined: $(eval ...)"*. **Assumed, not run on 3.81.**

## R-4 The model tooling's lockfile

- **Run:** in an empty directory holding only `assets/toolkit/scripts/event-model/package.json`, `npm install
  --package-lock-only --no-audit --no-fund` wrote a lock with `lockfileVersion` 3 and 32 package entries; the root
  entry carries `yaml` 2.9.0, `zod` 4.4.3 and `tsx` 4.23.12; every `resolved` begins
  `https://registry.npmjs.org/`; 26 `@esbuild/*` platform packages are listed, `darwin-arm64`, `darwin-x64`,
  `win32-x64` and `linux-x64` among them. The registry was reachable.
- **Run:** in a git repository holding only those two files under `scripts/event-model/`, `npm ci --prefix
  scripts/event-model --no-audit --no-fund --loglevel=error` installed 5 packages in 0.5 s, wrote
  `scripts/event-model/node_modules/.package-lock.json`, and `git status --porcelain` showed only the untracked
  `node_modules/` (ignored in a generated project).
- **Run:** today's `check-drawio` on a generated project leaves `scripts/event-model/package-lock.json` untracked
  after the first gate, on the Python, Go and TypeScript starters alike.

## R-5 The sync

- **Read:** `verify_script()` in `src/slipwai/project/languages/python.py`: every mode opens with `uv sync
  --project "$app" --locked --quiet` per service. **Run:** with the environment built, one such call takes 0.09 s.
- **Read:** `service_commands()` in `src/slipwai/project/native_commands.py`: Python's `lint`, `typecheck`, `test`,
  `integration`, `adversarial` and `install` are each a call of the script; `dev_command()` in
  `src/slipwai/backends.py` and `install_step()` in `src/slipwai/project/makefile.py` write `--install-only` as a
  recipe line ahead of `dev` and `migrate`.
- **Read:** TypeScript reaches `npm ci` through the file target `node_modules/.package-lock.json`
  (`src/slipwai/project/shared_packages.py`). Go's and Java's `lint`, `typecheck` and `test` carry no install step.

## R-6 The gates as they are today, under `-j`

| Starter (event profile, a browser app) | serial, warm | `-j`, warm | `-j`, first run after `make install` |
|---|---|---|---|
| Python | 6.2 s | 3.2 s (three runs) | — (run warm only) |
| Go | 5.4 s | 2.9 s | 4.8 s, exit 0 |
| TypeScript | 7.5 s | 3.8 s | 3.9 s, exit 0 |
| Java (Quarkus) | 22.2 s | 14.6 s | 16.4 s, exit 0 |

Each run exit 0 and ended `verify: all gates passed`. On Python the 106 lines of the serial run all appear under
`-j`, one test-progress line cut in two by another check's output. **Go:** on a fresh clone `go mod download` writes
an untracked `go.work.sum` (116 lines), and so does any other `go` command that resolves the workspace first.
**Java:** the three native checks each run `./mvnw` over the service's `target/` (read in `native_commands.py`),
and under `-j` today all three run at once over it; they passed here three times, which shows nothing about the
next time. The starter's gate ran here with its real toolchain (`./mvnw`, the machine's `java`).

## R-7 `slipwai migrate` and an untracked file

- **Read:** `src/slipwai/migrate.py` refuses on any uncommitted change, an untracked file among them (D91 read it;
  the task's test holds it as AC-S04-57).
