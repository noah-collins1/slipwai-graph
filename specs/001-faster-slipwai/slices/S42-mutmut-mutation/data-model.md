# Data model: S42-mutmut-mutation

Nothing is persisted beyond the run's own `mutants/`. These are the shapes the wrapper and the scope script read and
the words they print; the words are fixed here and tested verbatim.

## `apps/<service>/pyproject.toml` — what the factory adds (the project's from then on)

`dev` gains `"mutmut==3.8.0"` (sorted among the base tools). The template gains, below `[tool.pytest.ini_options]`:

```toml
[tool.mutmut]
# What `make mutation` mutates and how it runs the tests (scripts/mutmut-mutation.py, ADR 0010) …
source_paths = ["src"]
# … the default suite, as `make test` runs it: tests/integration needs a database, so it is left out …
pytest_add_cli_args_test_selection = ["tests", "--ignore=tests/integration"]
# … and never across cores: mutmut records which tests reach which function from one process …
pytest_add_cli_args = ["-p", "no:xdist"]
```

## `targets(service)` — the configuration the wrapper and the scope script read (R2)

Read with `tomllib` (`Unreadable("no tomllib: Python 3.11 or newer reads [tool.mutmut]")` where it is absent). The
table must exist (`Unreadable("no [tool.mutmut] table")`). `source_paths` (or, only where it is empty, the deprecated
`paths_to_mutate`) must be a non-empty list of relative POSIX strings with no `..`, no leading `/`, no `*`, `?`, `[` —
else `Unreadable` naming the value. `only_mutate` and `do_not_mutate` are lists of strings (else `Unreadable`).

## `matched(config, file) -> bool`

`file` is a path within the service, POSIX. True when the file ends `.py`, lies at or under one of `source_paths`, and
passes mutmut's own `should_mutate` with Python's `fnmatch` exactly as `configuration.py` applies it: included when
`only_mutate` is empty or one pattern matches; excluded when one `do_not_mutate` pattern matches.

## `refused(service, file) -> str | None` (D215 d's reason, D218)

A path within the service holding `*`, `?` or `[` — which `mutmut run` would read through `fnmatch` as a pattern over
mutant names — is refused: `` `<service>/<file>` holds `<char>`, which mutmut reads as a pattern over mutant names;
rename it, or run `make mutation-full` ``.

## `versions(pyproject_text, lock_text)` (R6)

`{"tool.mutmut": <table as parsed>, "requirement": [<every mutmut requirement string>]}` from a manifest;
`{"<name>": [<every version>]}` for `mutmut` and the closure of `libcst` from a lock. Text that does not parse raises
`Unreadable`; no `tomllib` raises `Unreadable`.

## `mutants/<path>.meta` (mutmut 3.8.0, `mutation/data.py`)

`{"exit_code_by_key": {<mutant name>: <exit code or null>}, "hash_by_function_name": …, "type_check_error_by_key": …,
"durations_by_key": …, "estimated_durations_by_key": …}`. The wrapper reads `exit_code_by_key` only.

| Exit code | mutmut's status | Verdict |
|---|---|---|
| `1`, `3` | killed | pass |
| `5`, `33` | no tests | counted, never failed |
| `0` | survived | fail |
| `36`, `24`, `-24`, `152`, `255` | timeout | fail |
| `35` | suspicious | fail |
| `-11`, `-9` | segfault | fail |
| `null` | not checked | fail |
| `2` | check was interrupted by user | fail |
| `34` | skipped | fail |
| `37` | caught by type check | fail |
| anything else | (unknown) | fail, as `unknown (exit <n>)` |

## The wrapper's lines and status (`scripts/mutmut-mutation.py <service> [--file <path> …]`)

Every line is prefixed `mutation: `.

| Situation | Line | Exit |
|---|---|---|
| no `os.fork` (Windows) | `mutmut needs os.fork, which this host does not have; run it under WSL` | 2 |
| no `uv` | `uv is not on PATH; install it to run mutmut (see scripts/verify)` | 2 |
| `uv sync --locked` refused | `<service>/uv.lock does not agree with <service>/pyproject.toml; run uv lock --project <service>, then this again` | 2 |
| mutmut absent or another version | `mutmut <found or "is not"> installed in <service>'s environment; this wrapper runs mutmut 3.8.0: add mutmut==3.8.0 to the dev group of <service>/pyproject.toml and run uv lock --project <service> (slipwai migrate brings the wrapper for a newer pin)` | 2 |
| no `[tool.mutmut]` | `<service>/pyproject.toml: no [tool.mutmut] table` | 2 |
| a refused `--file` | the refusal words | 2 |
| `PYTEST_ADDOPTS` set | `PYTEST_ADDOPTS is not passed to mutmut (it would change how every mutant's tests run); [tool.mutmut] pytest_add_cli_args is where this service adds pytest options` | — |
| a `--file` with no `.meta` after generation | `not mutated <service>/<file> — outside mutmut's configured targets` | — |
| no `--file` left | `nothing under <service> that was given is a file mutmut would mutate; no mutant to run` | 0 |
| scoped, every file empty | `no mutant to run — <files>: mutmut found no function to mutate in it` / `in them` | 0 |
| scoped | `scoped to <n> given file(s): <files> — <m> mutant(s)` | — |
| mutmut's exit | `mutmut exited <code> (its exit status and the output above are mutmut's, never the verdict; the .meta files are)` | — |
| a silencing pragma or setting | `<service>/<file>:<line> holds "# pragma: no mutate <block|start|end>", which silences mutants nobody looked at; only a bare "# pragma: no mutate" on the line excuses one` · `<service>/pyproject.toml sets do_not_mutate_patterns, which silences …` | — (fails) |
| each failing mutant | `<status> <service> <mutant name> (mutmut show <mutant name> in <service>; report <service>/mutants/)` | — |
| sweep, zero mutants | `mutmut found nothing to mutate in <service>; a pass on nothing is not a pass` | 1 |
| last line | `<n> mutants: <k> killed, <u> no tests (reported, never failed)[, <s> survived, <t> timed out, …]; <passed|failed> — report <service>/mutants/` | 0 / 1 |

## What sweeps a Python service (added to `sweep_causes`)

| Changed path | Sweeps |
|---|---|
| `<service>/pyproject.toml` whose `[tool.mutmut]` or mutmut requirement differs (either side unparseable, or no `tomllib`, counts) | that service |
| `<service>/uv.lock` whose `mutmut` or `libcst`-closure versions differ (the same fail-closed rule) | that service |
| `scripts/mutmut-mutation.py` | every Python service |
| a file git ignores under `<service>/src/` | that service (`unlisted`, via `PRODUCTION_ROOT`) |
| a configuration `targets()` cannot read | that service (`Plan.unreadable`) |

## The scope script's tables after the slice

`WIRED = ("go", "java-spring", "typescript", "python")`; `PLACEHOLDERS = {"java-quarkus": …}`; `PRODUCTION_ROOT` gains
`"python": "src/"`; `REPORTS` gains `"python": "mutants"`; `factory_recipe` writes `python3 scripts/mutmut-mutation.py
<path>` per Python service; `PYTHON_REFUSED` is removed.
