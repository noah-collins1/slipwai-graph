# 0010. mutmut in every generated Python service

Date: 2026-10-08

## Status

Proposed

Drafted by `/cruise` iteration 29 of `001-faster-slipwai`, at the plan stage of `S42-mutmut-mutation` (decisions D137,
D138, D212 and D216 in `specs/001-faster-slipwai/decisions.md`; research in
`specs/001-faster-slipwai/slices/S42-mutmut-mutation/research.md`). The run never accepts its own architecture
decision; the word `Accepted` here is a person's.

## Context

FR-008 asks `make mutation` to run the changed module's mutants for every backend whose mutation tool is wired, and
D137 left Python as a placeholder: its recipe ran `mutmut run` only where somebody had installed mutmut by hand, with
no configuration and no service named. There is no standard-library mutation tester for Python; mutmut is the
maintained one, its 2.x line is unmaintained, and 3.x reads its configuration from `[tool.mutmut]` in the
`pyproject.toml` every generated Python service already has. A dependency added here lands in every Python project the
factory makes and in all four committed Python locks, so removing or replacing it later is a relock and a `migrate`
note in every such project.

Three facts about mutmut 3.8.0 shape the choice (research R3–R7). It exits 0 when mutants survive, so its exit status
cannot be the verdict. It reaches a scope only as mutant names, matched with `fnmatch`, and asserts when none matches,
so a changed module with nothing to mutate is a crash unless something decides it first. And it caches every result
in `mutants/` and reuses it on the next run.

## Decision

Every generated Python service carries `mutmut==3.8.0` in its `dev` dependency group, installed only from the
committed `uv.lock` (`uv sync --locked`), and a `[tool.mutmut]` table naming `src` as the source, the default suite
without `tests/integration` as the test selection, and `-p no:xdist`. One wrapper per project,
`scripts/mutmut-mutation.py`, runs it per service from a fresh `mutants/`: it runs mutmut's own generation step first,
reads which mutants each scoped file holds from the `.meta` files that step writes, hands `mutmut run` exactly those
names, and decides the verdict from the `.meta` results (D212) — killed passes, *no tests* is counted, everything else
fails. It refuses, with exit 2, a host without `os.fork` and an environment whose mutmut is not the version it was
written against.

## Consequences

`uv sync` installs thirteen more packages in every Python service (mutmut, libcst, coverage, textual and their
dependencies); `pip-audit` covers them through `make audit`. The generation step calls functions mutmut does not
document as public, so the wrapper is written against one exact version: a pin change sweeps every scoped run, and a
project that raises the pin before the factory does gets an exit 2 naming `slipwai migrate`, never a silent run under
a step that moved. Windows has no `fork` and mutmut does not run there; WSL does. Replacing mutmut would mean a new
wrapper, a relock of every Python service and a `migrate` note: this record is why.
