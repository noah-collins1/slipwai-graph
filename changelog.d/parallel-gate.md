MINOR

**The gate's independent checks can run at once, and each toolchain syncs once per `make` run.** `make -j verify` runs
the gate's checks side by side, from GNU Make 3.81 on, and each check's output is kept together where the make can
(4.0 and later); `make verify` is the serial run it was, and the generated CI workflow and the commands the ladder types
still say `make verify`. A failed run ends on its own line, naming where to look, and `check-python` is first under `-j`
as it is serially. The checks that write one directory are ordered by prerequisite inside the gate alone, so a target
typed by itself is what it was: a Java service's three Maven checks run lint, typecheck, test in turn, and a Go project's
`lint` and `test` wait for `typecheck`, which resolves the workspace. A Java gate therefore gains little under `-j`: on the one run measured by hand it was not faster than the serial one.

`make verify` used to run `uv sync` for every Python service in each of `lint`, `typecheck` and `test` (three syncs, and
under `make -j` all three at once on one `.venv`). A Python project's `Makefile` now has a `sync` target that every
target running a Python mode names as a prerequisite, so `make verify`, `make -j verify`, `make ci`, `make lint test`
and `make install test` each sync every service once; `make migrate` and `make dev` take the same target. The recipes
call `./scripts/verify <mode> --synced`, an argument only the `Makefile` passes: a mode run any other way — by hand, from
a CI step, from an agent's hook — syncs first exactly as before, and nothing the factory publishes outside the `Makefile`
spells it. A failed sync stops the run before any check starts, and says so once.

In a project with the event profile the model tooling now installs from a lock the factory ships,
`scripts/event-model/package-lock.json`, with `npm ci`, once per `make` run and only when the lock or the manifest is newer
than what is installed: `check-drawio` says on one line when it did not reinstall, and `make install` now also installs
the model tooling from its committed lock, needing Node as the gate already did. A passing run that installed
dependencies as it went is not recorded (the stamp's rule stands), so on a fresh clone the first `make verify` runs in
full again unless `make install` came first. An adopted repository's gate is serial whatever `-j` says.

Run with the real toolchain: Go, TypeScript, Java (Quarkus) and Python, each serially and under `-j`. Read and not run: Java
(Spring). Not run: GNU Make 3.81 and 4.3 (4.4.1 was the make), Windows and macOS.

**Catch-up.** The model tooling's lockfile, `scripts/event-model/package-lock.json`, is new in a project with the event profile, and what `slipwai migrate` does with it depends on what the project has there. If the project has no lock there, `slipwai migrate` adds it and nothing is asked. If an earlier `make verify` or `make model` wrote an untracked lock there, `migrate` refuses as it does for any uncommitted change, so delete that file, then run `slipwai migrate`. If the project committed a lock of its own, the merge stops on `scripts/event-model/package-lock.json` as the conflicting file: run `git checkout --theirs scripts/event-model/package-lock.json`, `git add` it and commit to take the factory's, or, where the project edited `scripts/event-model/package.json`, run `npm install --package-lock-only` in `scripts/event-model` to regenerate the lock from its own manifest, then commit. A project that edited that `package.json` must now commit a lock that agrees with it, because the install refuses a manifest and a lock that disagree; nothing else is asked, since the new `Makefile` and `scripts/verify` arrive in the same merge. In an adopted repository (experimental) the `make verify` gate now runs serially whatever `-j` says, so `make -j verify` there is the serial run, and a recorded command of the application's own that calls `make` keeps whatever `-j` it passes.
