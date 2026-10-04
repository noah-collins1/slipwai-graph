MINOR

**A new Python service's gate runs its tests across cores, and a project can turn that off with one line.** `slipwai generate` now writes `"parallelSafe": true` into a new project's `project.json`, and the generated `scripts/verify` reads it each time it runs: where it is the JSON `true`, the gate's pytest runs with `-n auto --maxprocesses 4` (`pytest-xdist`, pinned in every Python service's development tools). Anything else — `false`, no key, a file that cannot be read — is the serial run it was, and `--integration-only` is never parallel.

**Catch-up.** A project made before this release stays serial: `slipwai migrate` carries a project's own `parallelSafe` and never adds one. To opt in, add the line `"parallelSafe": true` to the project's `project.json` and run `make verify` once; set it `false` to turn it off again.
