# Research: S33-factory-gate-stamp

## R-1 The script runs where it ships

`assets/toolkit/scripts/verify-stamp.py` finds the trunk through `check-slice-scope.py` beside it
(`trunk_module()`), and that finds the repository's root as the git top holding `project.json` with the script
inside it (`project_root()` in `assets/toolkit/scripts/check-slice-scope.py`). This repository's root holds
`project.json`, recording `ci.branch` `main`. Run here, read-only, at `c34ccc6` on `adopt-method`: `standing()`
answered `(True, None)` and `key_parts({})` returned in 0.6 s. The key's `scripts` part is the `Makefile` and
everything under `scripts/` (`is_gate_script()`), which at this root is the factory's own `scripts/verify` and
`scripts/check-structure.py` — the right part, unchanged.

## R-2 What the tree holds that git ignores

204 MB, of which 93 MB is `.python-tools/` (the pinned ruff and mypy, so keyed by bytes — a tool version moving
moves the key). `.venv/`, `__pycache__/`, `.mypy_cache/`, `.ruff_cache/` and the runner's records
(`specs/cruise-checkpoint.md`, `.specify/cruise-*`) are on the exempt list. `specs/cruise-log.jsonl` is untracked
and not ignored, so the runner's append between iterations moves the key between iterations, never within one.

## R-3 What the suite skips on

`skipTest` reasons in `tests/`: a tool not installed (`tofu`, `pack`, `docker`, `gh`, `uv`, `node`, `npm`, `go`,
`java` through `NEEDS` and `shutil.which`), platform features that do not change on a machine, and the npm
registry not reachable (four examples) — the last is not keyed (spec, S33's gaps note). `ask()` raises
`CannotAsk` for a tool not on `PATH`, which makes the run unstampable, hence D100's on-`PATH` list. Here `pack`
and `tofu` are missing; `mvn` is not looked for by the suite.
