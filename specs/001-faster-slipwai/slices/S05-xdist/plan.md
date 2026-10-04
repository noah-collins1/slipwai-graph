# Implementation Plan: S05-xdist — the root gate's tests run across cores where the project says they may

**Branch**: `adopt-method` (D12 — no `slice/` branch, no claim, no push) | **Date**: 2026-10-04 |
**Spec**: [spec.md](../../spec.md), *Slice acceptance criteria* → `### S05-xdist` (AC-S05-1 … AC-S05-13)

**Input**: the slice's row in [story-split.md](../../story-split.md), FR-009, decisions D102, D103, D104 in
[decisions.md](../../decisions.md), ADR 0003 (Proposed). Written by cruise iteration 14 (host, strong model).

## Summary

A generated Python service's gate runs pytest serially. This slice adds `pytest-xdist==3.8.0` to every Python
service's pinned development tools (four locks rebuilt), writes `"parallelSafe": true` into the `project.json` of
every project `generate` makes, and has the Python `scripts/verify` read that mark from the root `project.json`
each time it runs: the JSON `true` puts `-n auto --maxprocesses 4` on the gate's pytest in `--test-only`, `all`
and `--adversarial-only`; anything else — false, missing, unreadable — is today's command. `--integration-only`
never takes it. `migrate` carries a project's own mark and never adds one, so a project made before stays serial
(D102); `adopt` writes none. The gates page records the mark (default, missing is serial, when to set `false`) and
what each backend's runner already does (D104). MINOR (a new `project.json` key with a documented default):
`VERSION` stays `1.6.0.dev0`, one `changelog.d/` fragment with a catch-up note.

## The example map

| Rule | Criteria | What it says | Examples |
|---|---|---|---|
| **R1** a new project is marked | AC-S05-1 | `metadata()` writes `"parallelSafe": true` where its caller says a project is new | e1 `generate` (Python) → `true` · e2 `generate` (TypeScript) → `true` |
| **R2** the mark reaches the gate's pytest at run time | AC-S05-2, -3, -4, -5 | The script reads the root `project.json` with `python3` (only JSON `true` is on) and adds `-n auto --maxprocesses 4` to the three modes; never to `--integration-only` | e1 `true`: `--test-only` and `all` carry the flags (stand-in `uv` records argv) · e2 `false` / removed / `"yes"` / unreadable file: no `-n`, rest identical · e3 `--integration-only` with `true`: no `-n` · e4 `--adversarial-only`, `true`, nothing matches: exit 0 |
| **R3** the plugin is installed, locked, and only the gate uses it | AC-S05-6, -7 | `pytest-xdist==3.8.0` in `BASE_DEVELOPMENT`; `make locks` rebuilds the four locks; template `addopts` unchanged | e1 the dev list in each selection's `pyproject.toml` · e2 each committed lock names `pytest-xdist` 3.8.0 and `execnet` · e3 `addopts` is what it was |
| **R4** what exists keeps its answer | AC-S05-8, -9 | Replay writes the project's own mark (or none); adopt writes none; add-service keeps it | e1 replay of a pre-release project: no key · e2 `false` and `true` survive replay · e3 adopt / refresh: no key · e4 add-service keeps `false` |
| **R5** the words are true | AC-S05-10, -11, -12, -13 | Gates page: the mark, and each backend's runner; MINOR fragment with a standalone catch-up note; measurement | e1 Python project's page carries the mark's paragraph · e2 a TypeScript+Go+Java page says Vitest by file, `go test` by package, Surefire one at a time · e3 the fragment's first line is MINOR |

## Technical Context

**Language**: Python 3 (the factory), POSIX `sh` (the generated `scripts/verify`). **Testing**: `unittest` in
`tests/`, stand-ins on `PATH` (a fake `uv` recording its arguments) — no mocking framework. New test modules under
350 lines each (suggested: `tests/test_xdist_gate.py`, `tests/test_xdist_mark.py`). **Lock rebuild**:
`make locks` needs the network (reachable here). **Real run**: the matrix (`tests/test_matrix.py`) runs a
generated Python project's real `make verify`, so it exercises the plugin for real.

## Constitution Check

The gate's checks are unchanged in what they hold: the same tests run, the pass/fail set equal (AC-S05-2), CI the
same command. A project made before is untouched until a person adds a line (owner brief, priority 5). The new
dependency is recorded (ADR 0003, Proposed). No mocking framework.

## Structure Decision

Factory source: `src/slipwai/project/languages/python.py` (pin; verify script), `src/slipwai/project/metadata.py`
and its callers `src/slipwai/scaffold.py`, `src/slipwai/replay.py` (and whichever of `cli*.py`/`add_service.py`
`/adopt.py` thread the value), `src/slipwai/project/docs.py` (gates page), `assets/languages/python/locks/*.lock`
(rebuilt by `make locks`), `changelog.d/xdist.md`. No `assets/` template besides the locks. Tests: new modules plus
the existing ones that pin the dev list (`tests/test_uv.py`) or the verify script's text.

## Pin

The Python `scripts/verify` is generated code; its tests are the pin. Existing tests that hold the script's
commands (`tests/test_uv.py`, `tests/test_parallel_gate_families.py`) run before and after.
