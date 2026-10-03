# Research — S21-refresh-keeps-owned-files

No dependency is added and none's behaviour is relied on; every statement below was read from this tree.

- **R-1 Why the four are rewritten.** `src/slipwai/scaffold.py` `project_files()` emits `.specify/models.json`,
  `.specify/drive.json`, `.specify/cruise.json` and (through `decision_files()`) `.specify/product-owner.md`
  with content no argument drives. `src/slipwai/resurvey.py` `refresh()` writes every path in `after` whose
  disk content differs. **Decision:** skip the four where present (D24). **Alternative:** remove them from
  `.written` — rejected: `migrate` is a three-way merge and is how a new default reaches them.
- **R-2 Why an uncommitted edit refuses.** `refuse_foreign()` (`src/slipwai/uncommitted.py`) refuses on any
  path in `writes()` with a change slipwai did not leave; `writes()` is `.written` plus three pages.
  **Decision:** `writes()` leaves out the four that exist.
- **R-3 Why `before` is stale.** `with_recommendation()` (`src/slipwai/strategy.py`) calls
  `recommend(why, detected(apps, adoption), products)`; `refresh()` reconciles rows afterwards
  (`convergence.reconciled`). **Decision:** re-derive `before` after reconciliation (D25).
- **R-4 Budget.** `src/slipwai/resurvey.py` is 350 lines; `make check-structure` holds the budget (lesson from
  S20: run `make lint typecheck check-structure` before each commit).
- **R-5 Seen here.** This repository: `.specify/cruise.json` reset to `enabled: false`, `max_iterations: null`
  and the brief replaced by the template at S00's T005 (D15); `project.json` `strategy.before[1]` reads *the
  safety net is `tests-exist`* with the row at `tests-pass` (D16).
