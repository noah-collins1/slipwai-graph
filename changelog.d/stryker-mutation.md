MINOR

**A generated TypeScript service now carries Stryker, wired: `@stryker-mutator/core` and `@stryker-mutator/vitest-runner` at exactly 10.0.0 in its `devDependencies`, a checked-in `apps/<service>/stryker.config.json` listing the files it mutates, and `scripts/stryker-mutation.py` beside the other gate scripts.** The reports and sandboxes a run leaves are ignored (`.stryker-tmp/`, `reports/mutation/`), and the twelve committed TypeScript dependency locks move with the manifest.

**Catch-up.** A project made before gains the two devDependencies, `stryker.config.json`, `scripts/stryker-mutation.py` and the ignore lines after `slipwai migrate`; run `npm install` after it so `package-lock.json` agrees with the manifest. This is the first step: the wrapper is not yet the whole mutation run, and the rest of this entry is completed by the commits that follow it.
