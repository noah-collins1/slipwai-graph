# 0003. pytest-xdist in every generated Python service

Date: 2026-10-04

## Status

Proposed

Drafted by `/cruise` iteration 14 of `001-faster-slipwai`, at the gaps stage of `S05-xdist` (decisions D102 to D104
in `specs/001-faster-slipwai/decisions.md`). The run never accepts its own architecture decision; the word
`Accepted` here is a person's.

## Context

FR-009 asks a project's root gate to run pytest across cores where `project.json` marks the project parallel-safe,
on by default for a new project and off with one line. pytest has no parallel runner of its own; pytest-xdist is
the plugin the ecosystem uses for it. Whether the gate passes `-n` is read from `project.json` when the gate runs,
so a person flips the line without regenerating anything — which means the plugin has to be installed whatever the
line says. Every generated Python service already pins its development tools exactly (`BASE_DEVELOPMENT` in
`src/slipwai/project/languages/python.py`) and installs them from a committed `uv.lock`.

## Decision

`pytest-xdist==3.8.0` joins `BASE_DEVELOPMENT`, so every generated Python service carries it as a development
dependency and its four committed locks name it. The plugin is used only by the gate's own pytest command, as
`-n auto --maxprocesses 4`, and only where `project.json` says `"parallelSafe": true` (D102, D103). The
service's `pyproject.toml` gains no `addopts` for it: a person's own `pytest` run stays serial.

## Consequences

A generated project gains one development dependency (and `execnet`, which it requires), pinned and locked like
the rest, which Renovate keeps current with them. Removing it later is a release with a `migrate` catch-up note and
a relock in every Python service — a migration, which is why this is recorded. A project made before keeps a
serial gate until a person adds the line (D102); after `slipwai migrate` it has the plugin installed either way.
Tests that share a file, a port or module-level state fail or pass differently under the plugin; the gates page
says that is when to set the line to `false`.
