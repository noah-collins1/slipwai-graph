# Data model: S01-gate-walks

One record, owned by `check-codegraph.py`, at `.codegraph/gate-memory.json` in a project. Not generated, not
tracked, removed with the index.

| Field | What it holds | Why |
|---|---|---|
| `key` | SHA-256 of `scripts/check-codegraph.py` and of `scripts/agents/code_index.py`, joined | A changed gate does not trust an older gate's memory (D46, rule 7) |
| `commit` | The commit `HEAD` named when the memory was written | What git is asked to compare the tree with |
| `dirty` | Tracked paths that differed from `commit` then | Hashed on every narrowed run: a later revert is not in a diff (rule 2) |
| `rows` | `path → content_hash` for every row of `files` then | A row rewritten, added or removed since is seen by content (rules 5, 6) |
| `database` | `st_dev`, `st_ino` of `codegraph.db` then | Another or a rebuilt database is never narrowed |
| `whole` | The moment of the last whole comparison, epoch seconds | Said on the narrowed pass line; kept across renewals |
