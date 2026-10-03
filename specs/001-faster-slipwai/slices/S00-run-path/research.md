# Research — S00-run-path

Every statement below names the artefact it was read from or the run that produced it; a statement with no
citation would read *assumed*, and the plan does not rest on one. Written by cruise iteration 2, 2026-10-03.

## R1 — The smoke command runs

- **Decision:** the run path is `./slipwai --version`, recorded as `commands.smoke` in `project.json`
  (`deployables.slipwai-graph.commands.smoke`, provenance from the adoption commit `4d045f3`).
- **Evidence:** run on this checkout at `5460bf9`, 2026-10-03T02:3xZ: prints `slipwai 1.5.2.dev0`, exit 0;
  `python3 --version` → `Python 3.14.4`. `VERSION` reads `1.5.2.dev0`; `AGENTS.md` *Versioning* says it is the
  one place the number is written, so AC-S00-1 names `VERSION` and not the literal.
- **Alternatives:** none — the command is recorded; `make -f delivery/Makefile smoke` (line 97–99) runs the same line.

## R2 — Why the suite is red inside an iteration

- **Finding:** with `CRUISE_RUNNER=1` and `CRUISE_ITERATION=2` in the environment, 6 of the 43 tests in
  `tests/test_cruise*.py` fail (`/tmp/cruise-tests-inherited.log`, run at `5460bf9`): one error in
  `test_cruise_start` (`RuntimeError: this session is iteration 2 of a run already under way; the runner that
  started it re-invokes /cruise`), and five failures in `test_cruise_index`, `test_cruise_start`,
  `test_cruise_watch` (two) and `test_cruise_where`, each asserting exit 0 or a message and getting that same
  refusal. With both variables unset the same modules are green (iteration 1's record in `story-split.md`,
  *Parking Lot*; the full-suite baseline run of this iteration, `/tmp/full-tests-baseline.log`, confirms it when
  it ends).
- **Cause:** the tests spawn `scripts/agents/cruise.py` with `env={**os.environ, **env}` and the child inherits
  the runner's marks, so `start` (and the verbs that call its guard) refuse as designed — the design is proven
  by `tests/test_cruise_start.py:174`, which sets the two variables *deliberately* to get that refusal.
- **Decision:** the fix is in the tests, not in `cruise.py`: a child of a test is not an iteration, and the
  script's refusal is correct behaviour the tests must keep proving (AC-S00-4). Nothing user-visible changes
  (AC-S00-7).

## R3 — Where the fix lives and its shape

- **Sites that build a child environment from `os.environ`** (grep `os.environ` over `tests/test_cruise*.py`):
  1. `tests/test_cruise_runner.py:43–45` — `cruise()`, the helper every cruise test module imports.
  2. `tests/test_cruise_tell.py:146–148` — `subprocess.Popen([... "run"], env={**os.environ, **env, ...})`.
  3. `tests/test_cruise_watch.py:166–167` — `subprocess.run([... "watch", "--minutes", "1"], env={**os.environ, **env})`.
  4. `tests/test_cruise_start.py:282` and `:292` — in-process: `mock.patch.dict(module.os.environ, env)` then
     `module.start([])`; the patch *merges* into the real environment, so the marks stay.
  5. `tests/test_cruise_stop_hook.py:28–31` — `hook()` already strips both (`unset = {k: v for k, v in
     os.environ.items() if k not in ("CRUISE_RUNNER", "CRUISE_ITERATION")}`): the precedent to copy.
- **Decision:** one helper in `tests/test_cruise_runner.py` (the module `test_cruise_stop_hook.py` already
  imports `REGISTRY, enable` from), e.g. `outside_a_run(env: dict | None = None) -> dict[str, str]`, returning the
  parent environment without the two marks plus the overrides; `cruise()` and `hook()` call it; sites 2 and 3
  use it; site 4 uses `mock.patch.dict(module.os.environ, outside_a_run(env), clear=True)`. A test that wants the
  marks passes them in `env`, as `:174` does, and they win because overrides are applied last.
- **Mocking framework:** `tests/test_cruise_start.py` already uses `unittest.mock` for `Popen` and
  `os.environ`; `AGENTS.md` *Delivery method* says code that was here is held to what it had and no mocking
  framework is *added* — none is: the existing `patch.dict` call changes arguments only.
- **Alternatives considered:** making `cruise.py start` ignore the marks when `CRUISE_HARNESS_COMMAND` is set
  (a production change for a test's convenience, and it would weaken the refusal `:174` proves); clearing the
  variables in `make test` (hides the cause from anyone running `python -m unittest` directly).

## R4 — The two gates and the ratchet

- `make verify` (root `Makefile:35`): `lint typecheck check-structure test`. `make test` (`Makefile:31–32`):
  `PYTHONPATH=src python3 -m unittest discover -s tests -v`.
- `make -f delivery/Makefile verify` (`delivery/Makefile:84`): `check-python lint typecheck check-imports
  check-migrations check-slice-scope check-extensions check-agents check-speckit check-codegraph check-ux-gates
  check-constitution check-benchmark check-decisions test check-convergence`; its `test` (line 72–73) is
  `python3 delivery/scripts/ratchet.py slipwai-graph test -- 'make test'`.
- **Ratchet** (`delivery/scripts/ratchet.py`): the baseline is `delivery/baseline.json` beside the Makefile
  (line 33, 90); it does not exist in this checkout (`cat` → no such file), so this slice's gate run is the
  first — `lint` and `typecheck` record their findings on the first run *when there are any* (lines 239–250,
  *commit `delivery/baseline.json`*); a command that exits 0 with no prior entry records nothing and prints
  nothing (lines 205–212); a red `test` with no baseline stops the run and records nothing (lines 27–35,
  230–236); `make -f delivery/Makefile ratchet-tighten` is the only thing that records a quarantine, and the
  slice never runs it. So the order is fixed: the test fix lands first, then the delivery gate runs. **Observed
  (T003):** every ratcheted command was clean, so no `delivery/baseline.json` came into being and none is
  committed — the plan's expectation of a baseline file was the case for a repository with findings, not this one.
- `check-slice-scope` on `adopt-method` prints *not a `slice/<id>` branch — nothing to hold*
  (`delivery/scripts/check-slice-scope.py:372–375`); D12 is why the slice is on that branch.
- `check-benchmark` warns, never fails (`delivery/commands/drive.md`, *What each stage costs*).

## R5 — Moving the Safety net row and redrawing the page

- The row's definition: `tests-pass` = *the suite is green in the gate, with no quarantine*
  (`src/slipwai/convergence.py:59`); the survey can only *detect* `tests-exist` or `none` (`:148`), so
  `tests-pass` is written by the slice with provenance `confirmed` (D11; `delivery/commands/drive.md` stage 9).
- `check-convergence` contradicts `tests-pass` and above when `delivery/baseline.json` records a quarantined
  suite (`src/slipwai/project/ground_command.py:36`) — the tree check that keeps the claim honest.
- `/survey` = `./slipwai adopt --refresh` from this checkout (`delivery/commands/survey.md`): refuses an unclean
  tree (`src/slipwai/adopt.py:94`, `git status --porcelain`), refreshes `detected` facts in place and *reports*
  a disagreement with a `confirmed` fact without changing it (`src/slipwai/resurvey.py:6–8`). The person's
  refresh commit `5460bf9` shows what one rewrites: `delivery/commands/ground.md`, `delivery/commands/strangle.md`,
  `delivery/docs/change-strategy.md`, `delivery/docs/convergence.md`, `delivery/survey/structure.md`,
  `project.json`. None is a control the runner watches (`delivery/scripts/`, `tools/`, `Makefile`, CI, hooks).
- Sequence therefore: commit the test fix and `running.md`; edit `project.json`'s row and commit; run
  `./slipwai adopt --refresh`; read its three kinds of line; commit what it regenerated;
  `make -f delivery/Makefile check-convergence`.

## R6 — The constitution follows the map

- `.specify/memory/constitution.md` principle V carries `<!-- journey: acceptance-driven-testing at tests-exist -->`
  (line 102) and is written as *a target, not yet in force … comes into force at `tests-pass`*; principle XIII
  (*Fast Feedback*) is the same journey shape, in force at `fast`. `src/slipwai/project/constitution_journey.py`
  `JOURNEY`: `acceptance-driven-testing → ("safety-net", "tests-pass")`, `fast-feedback → ("safety-net", "fast")`.
- `delivery/scripts/check-constitution.py` holds the marker to the map (`MARKER`, line 110; lines 902–908): a
  marker at another rung than the row's is drift, and a requirement no longer in the journey must be present
  in full. Its module docstring (`constitution_journey.py` lines 1–16): *when a row reaches its rung, the marker
  comes out, the quotation becomes the text, and the check asks for the principle in full.*
- **Decision:** the Convergence stage edits the constitution in the same commit as the row: principle V's
  preamble and marker come out and its quoted text becomes the principle, with the two *what holds here* bullets
  folded into the first paragraph as history; principle XIII's marker moves to `at tests-pass` and its *stands
  at* sentence follows. This is the stage the slice exists for (D8), not a new principle; `make -f
  delivery/Makefile check-constitution` is the check. Principle V in force binds every later slice to
  RED-first acceptance scenarios — which the constitution's own bullet under V already announced for this feature.

## R7 — Branch, claim and push

- D12 (skipper, iteration 2): S00's commits land on `adopt-method` on top of `5460bf9`; no `slice/` branch, no
  claim, no push; merging the adoption and pushing are a person's. `git rev-list --left-right --count
  origin/main...HEAD` → `0 7`; `git ls-remote --heads origin 'slice/*'` → none.

## R8 — The slice-scope checker's root-path case

- D13: `delivery/scripts/check-slice-scope.py:213–219` `owning_app()` cannot match a deployable at `.`;
  placed in the split as `S20-slice-scope-root` (PATCH, factory asset). Not this slice's work; recorded so the
  plan says why S00 does not use a slice branch even if the adoption were merged.

## R9 — The pre-slice baseline

- A full `make test` with the two variables cleared, run at `5460bf9` (`/tmp/full-tests-baseline.log`, cruise
  iteration 2): `Ran 829 tests in 1033.671s` — `OK (skipped=9)`, exit 0. AC-S00-5's baseline is therefore
  **K = 9**, and the full suite costs about 17 minutes per gate run on this machine.
