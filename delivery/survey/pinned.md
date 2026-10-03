# Pinned behaviour

What `/characterise` has pinned, one row per behaviour: the current behaviour of code that existed before
the delivery method did, recorded at the seam where it can be observed, so that a change to it can be told
apart from a regression. A slice reads this before it changes code that is here; `/strangle` reads it when a
behaviour moves. Rows are appended, never rewritten — a behaviour that stopped being pinned says so in a new row.

| Date | Behaviour | Seam | Tests | Runs with |
|---|---|---|---|---|
| 2026-10-03 | The slice-scope gate's answers on a generated project with its deployables under `apps/`: off a slice branch nothing is held; on one, its own record and service code pass, and another slice's record or model block, an edited or numbered migration, a removed event line, the docs and a file outside every deployable (a root `Makefile`) are refused, each with what to do instead (S20-slice-scope-root) | `python3 scripts/check-slice-scope.py` run in a generated repository: exit code and stderr | `tests/test_parallel_slices.py` (`SliceScopeGateTest`) — already there, green today; the slice leaves the file unedited | `make test TESTS="test_parallel_slices"` |
| 2026-10-03 | `check-decisions`' adversary-row rule: a done slice (a register row, or `status: implemented` in the model) with no `## <id> · ` row in the adversary log is a finding; a row satisfies it; the baseline is taken once (S20-slice-scope-root). Not pinned, because the slice changes it on purpose: a register id with a slug is cut to its letters-and-digits prefix | `python3 scripts/check-decisions.py` run in a generated repository: exit code, stdout and stderr | `tests/test_cruise_record.py` — already there, green today | `make test TESTS="test_cruise_record"` |
| 2026-10-03 | `check-benchmark`'s warnings: an entry left open, a done slice with no `slices/<id>/benchmark.json` or an unclosed one, a feature with done slices and no record above the slice loop (S20-slice-scope-root). Not pinned, changed on purpose: the same prefix cut of a register id | `python3 scripts/agents/benchmark.py check` in a generated repository: its findings | `tests/test_benchmark_brackets.py` — already there, green today | `make test TESTS="test_benchmark_brackets"` |
