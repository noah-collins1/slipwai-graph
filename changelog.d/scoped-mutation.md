MINOR

**A generated project's `make mutation` is split into `make mutation` and `make mutation-full`.** `mutation-full` is the mutation run exactly as `make mutation` was before, and `make mutation` is now one call to a new script, `scripts/mutation-scope.py`, which runs `mutation-full` and reports its status; the script is where a mutation run on a slice branch is priced per change rather than per repository, and this first step only introduces the two targets. `make verify`, `make verify-checks`, `make ci` and the CI workflow are byte for byte what they were, and neither new target is reachable from them.

**Catch-up.** A project made before gains `make mutation-full`, the scoped `make mutation` and `scripts/mutation-scope.py` after `slipwai migrate`; `make mutation` runs the same tools it ran, CI, the trunk and `SINCE` behave as before, and nothing else asks anything of the project.
