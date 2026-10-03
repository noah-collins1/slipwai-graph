PATCH

**`adopt --refresh`, `--confirm` and `--decline` (experimental: brownfield adoption) now refuse to write over an uncommitted change where the project sits in a subdirectory of its git repository.** Git names a path from the repository's top (`sub/delivery/docs/convergence.md`) and a run names what it writes from the project (`delivery/docs/convergence.md`), so in a subdirectory project no path ever matched: a hand edit, a deletion or an untracked file at a path the run writes was written over at exit 0. The refusal now compares the project's own spelling and names the file that way, as it does where the project is the top of its repository, which is unchanged.

**Catch-up.** Nothing is asked of a repository already adopted. One whose project sits in a subdirectory may now be refused at its next refresh, confirm or decline where it never was, naming the file; commit or stash that change first.
