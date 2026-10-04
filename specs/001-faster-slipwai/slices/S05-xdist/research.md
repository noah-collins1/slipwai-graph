# Research: S05-xdist

## R-1 What xdist costs on a new project

Measured at the gaps stage (spec, S05's note): a fresh Python starter, 130 tests, 12 cores, pytest 9.1.1,
pytest-xdist 3.8.0, `uv run --no-sync pytest …`, three runs: serial 0.95 s, `-n 2` 1.13 s, `-n 4` 1.26 s,
`-n auto` 1.9 s; warnings printed per worker. Hence D103's cap.

## R-2 pytest-xdist 3.8.0

The current release on PyPI (read 2026-10-04 from `https://pypi.org/pypi/pytest-xdist/json`): requires
`execnet>=2.1` and `pytest>=7.0.0`. `-n auto` takes one worker per CPU; `--maxprocesses N` caps it (the plugin's
own option). A `-k` matching nothing exits 5 under the plugin as without it (run here).

## R-3 How project.json travels

`metadata()` writes it at generate (`scaffold.project_files`); `replay` regenerates it and carries only
`generator` forward, then `migrate` three-way merges against the factory's last commit, so any key `metadata()`
writes reaches existing projects — the reason replay must write the project's own mark and no other (D102).
`add-service` and `describe-service` edit the loaded document in place. Nothing validates the key set
(`manifest.py`). The generated Python `scripts/verify` lists its services at generation; nothing rewrites it on an
edit to `project.json` (D104).

## R-4 The other runners

Vitest runs test files in parallel by default (`assets/languages/typescript/app/package.json`, `vitest run`, no
`pool` override); `go test ./...` runs packages in parallel (`GO_TEST_COMMAND` in `go.py`); `./mvnw -B -q test`
with no Surefire `parallel` or `forkCount` and no JUnit parallel setting under `assets/` runs one at a time.
