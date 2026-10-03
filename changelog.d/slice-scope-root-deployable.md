PATCH

**`check-slice-scope` no longer refuses a slice's own code in a repository adopted at its root (`adopt`,
experimental), and a slice id with a slug is read whole.** A repository adopted with its one application at
the root records that deployable at `.`, and the gate read `.` as owning no path, so a slice's tests and its
code were all refused as *outside every deployable*. A deployable at `.` now owns every path no deployable in a
subdirectory claims, except what stays the host's there: `project.json`, the root `Makefile` in any spelling
make reads, `.specify/`, CI configuration for every system `adopt` recognises, every agent's guidance, skills,
hooks and settings as `scripts/agents/registry.json` names them, every path in `<delivery>/.written`, and the
delivery directory apart from `survey/pinned.md` and `survey/running.md`, which the ladder has a slice write.
Git hooks and `.gitignore` are the repository's own. A new migration under a deployable at `.` keeps
whatever name the repository's own tool gave it — the 12-digit stamp is asked only of code the factory lays out —
while an existing migration is still never edited; and the events-module rule holds there only where the record
says `"layout": "hexagonal"`. The record a branch is judged by is the `project.json` it left `main` with, so a slice cannot grant itself a
path by editing it, and a file name git would quote is held like any other. A service
under `apps/` still owns its own files, an empty `path` still owns nothing, and a project with no deployable at
`.` gets the answers it had.

`check-decisions` and `check-benchmark` cut a register id such as `S00-run-path` to `S00`, so an adversary-log
row headed with the full id was reported missing and the slice's `benchmark.json` was looked for under
`slices/S00/`. Both now read the id whole, and still accept a row or a record written under the bare prefix.

This asks nothing of a repository already generated: `slipwai migrate` carries the corrected scripts.
