# Data model — S21-refresh-keeps-owned-files

No stored shape changes. Two derived things are named:

- **Seeded file** — one of `.specify/cruise.json`, `.specify/product-owner.md`, `.specify/models.json`,
  `.specify/drive.json`: written by the factory once, the project's from then on. A refresh's state for each:
  *present* → left, uncounted, unstamped, no refusal; *absent* → written with the factory default, counted.
  Always listed in `<delivery>/.written`.
- **`strategy.before`** (`project.json`) — a list of sentences: the platform entries first, then one per
  row-derived precondition (path to production, safety net, structure, and the strategy's own). After a refresh
  the row-derived entries are computed from `convergence` as written back to `project.json` by that refresh.
