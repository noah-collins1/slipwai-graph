MINOR

**A generated project's `Makefile` gains `make verify-scoped` and a `lint-`, `typecheck-` and `test-` target for each deployable.** Each service and each browser app is a component with
checks of its own, built from the same recipe lines the gate already runs, so the checks of one deployable can be named
without running the others'; a line shared by several of one language family (the Python family's `./scripts/verify`,
Go's `gofmt`) is a family target, `lint_python`, that each of the family's units names and make runs once. `make verify`,
`make verify-checks` and `make ci` are byte for byte what they were.

**Catch-up.** A project made before gains `make verify-scoped` and the per-deployable targets after `slipwai migrate`;
its merge root and CI still run `make verify`, and nothing else asks anything of it. An optional `verification.obligations`
key in `project.json` declares an integration obligation the scoped gate then honours; the factory never writes it.
