# Running slipwai-graph

What is proven about running each application that existed before the delivery method did — the command, the
port, what has to be seeded first, the runtime it actually needs and the ones it cannot run on — written by
whoever proved it, with the date. This file is the repository's own: `slipwai migrate` and `/survey` never
rewrite it, and `skills/run-the-app/SKILL.md` points here. Record what was proven, not what a README promises,
and record the run that failed too: a runtime the gate compiles on and the application cannot load is the kind
of fact that is only ever learned once if it is written down.

## `.` (python)

Proven 2026-10-03 by cruise iteration 2 of `001-faster-slipwai` (slice `S00-run-path`), from this checkout at
`5460bf9` on `adopt-method`.

- **Command:** `./slipwai --version` — the `smoke` command `project.json` records for `slipwai-graph`;
  `make -f delivery/Makefile smoke` runs the same line.
- **Printed:** `slipwai 1.5.2.dev0`, one line on stdout, exit 0. The number is the contents of `VERSION`, the one
  place it is written (`AGENTS.md`, *Versioning*), so what the command prints moves with that file.
- **Runtime it ran on:** `Python 3.14.4` (`python3 --version`). The floor is `>=3.11` (`pyproject.toml`);
  CI runs 3.11 (`.github/workflows/verify-delivery.yml`). Nothing else is needed: the launcher is a script at the
  repository root that imports `src/slipwai/` and reads `VERSION`.
- **Port, seed, backing service:** none. The command listens on nothing and reads nothing but the tree.
- **Cannot run on:** not tested. No runtime it fails on is known; none is recorded until one is seen.
- **What this proves and does not:** that the factory starts and answers from this checkout. Generating or
  adopting a project (`./slipwai generate`, `./slipwai adopt`) is exercised by the test suite (`make test`),
  not by this smoke command.
