MINOR

**The gate's independent checks run at once, and each Python service syncs once per `make` run.** First draft, completed
when the slice lands. `make verify` used to run `uv sync` for every Python service in each of `lint`, `typecheck` and
`test` (three syncs, and under `make -j` all three at once on one `.venv`). A Python project's `Makefile` now has a
`sync` target that every target running a Python mode names as a prerequisite, so `make verify`, `make -j verify`,
`make ci`, `make lint test` and `make install test` each sync every service once; `make migrate` and `make dev` take
the same target and no longer write out their own sync. The recipes call `./scripts/verify <mode> --synced`, an argument
only the `Makefile` passes: a mode run any other way — by hand, from a CI step, from an agent's hook — syncs first exactly
as before, whatever the environment says, and nothing the factory publishes outside the `Makefile` (the CI workflow, the
commands in `project.json`, the pages) spells it. A failed sync stops the run before any check starts, and says so once.

**Catch-up.** The three cases of the model tooling's lockfile are written when that part lands. For the sync alone,
`slipwai migrate` brings the new `Makefile` and `scripts/verify`; nothing is asked of a repository that takes both.
