PATCH

**`adopt --refresh` (experimental: brownfield adoption) no longer rewrites the four files a project owns.**
`.specify/cruise.json`, `.specify/product-owner.md`, `.specify/models.json` and `.specify/drive.json` are seeded by
the factory and then changed by the project — a run's settings, a filled-in owner brief, which model runs each
stage — and a refresh, `adopt --confirm` included, wrote each back to the factory's default wherever the disk
differed. A refresh now writes one only where it is absent, so a project is never left without a file
`make check-agents` and `/cruise` read; an uncommitted change to one no longer refuses the refresh; and a later run
does not take the project's edit for slipwai's own. `<delivery>/.written` still lists all four, so `slipwai migrate`
still merges a newer factory's version of each with yours, and the pages the record drives follow it as before.

A repository whose refresh already reset one of the four restores it from its history: `git checkout <commit> --
.specify/cruise.json` (and likewise the others) from the commit before that refresh. Nothing else is asked of a
repository already adopted.
