# Slice register — 001-faster-slipwai

A row here is the ladder's mark that a slice is done: demo accepted, adversary and mutation recorded, `make verify`
green, merged to `main`. The ordered split and its slice graph are in [`../story-split.md`](../story-split.md);
`/drive` and `/where-are-we` read this register against that graph to compute the ready set. `accepted-by` says
who saw the demo — `drive-hand` under `/cruise`, a person otherwise.

| Slice | Done | Accepted by | Merged as | Notes |
|---|---|---|---|---|
| `S00-run-path` | 2026-10-03 | `drive-hand` (cruise iteration 2; demo 2 `accepted`, demo 1 `implementation`) | `e12ca58..2108b81` on `adopt-method`, plus the Phase 4 record commit after it — no `slice/` branch, nothing pushed, `main` untouched (D12) | Method slice: run path proven (`delivery/survey/running.md`), suite green inside an iteration (T001), Safety net `tests-exist → tests-pass` (D11), principle V in force; adversary skipped and recorded; mutation N/A (no command); found S20 (D13), S21 (D15, D16). Gates green at `2108b81` with the marks set |
