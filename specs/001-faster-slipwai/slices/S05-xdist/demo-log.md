# Demo log: S05-xdist

## 2026-10-04T20:42:21Z — implementation · iteration 14 · drive-hand (claude-opus-5-5)
- **Started with:** `./slipwai generate shop --backend python --output "$D" --no-init --no-install --skip-checks` (this checkout at 31bd632), then the quickstart line by line inside `$D/shop`. For the older-project path: `git archive 8b0d103 | tar -x -C <dir>`, that tree's `./slipwai generate shop --backend python …` (it commits as it generates), then this checkout's `slipwai migrate` inside it. · **Seeded:** none. A disposable Postgres (`docker compose -p s05demo-shop up -d --wait postgres` in the scratch project) was started only so `make test-integration` could run. It was stopped with `down -v`.
- **Driven through:** CLI. `.specify/cruise.json` names `browser`, but this slice has no screen and no HTTP surface. What it changes is a generated `project.json`, the generated `scripts/verify` and `docs/gates.md`, so a browser or HTTP rung has nothing to drive.
- **Examples:**
  - AC-S05-1: passed. `"parallelSafe": true` sits on the line after `"target"` for python (four store/http combinations), typescript, go, java-quarkus and java-spring.
  - AC-S05-2: passed. `make test`, `make verify`, `make -j verify` and `--adversarial-only` run `pytest -n auto --maxprocesses 4` ("created: 4/4 workers"). The per-test outcome set from `-rA` is identical to the serial run: 87 passed.
  - AC-S05-3: passed. `false`, a missing key, `"true"`, `1`, a key written twice, truncated JSON and a file with mode 000 each give the serial command, word for word as before, and each takes effect on the next run with nothing regenerated.
  - AC-S05-4: passed. `make test-integration` runs `pytest apps/service/tests/integration` with no `-n` while the mark is `true`.
  - AC-S05-5: passed. With the mark `true`, `-k adversarial` matches 0 items under 4 workers, pytest exits 5, and the mode exits 0.
  - AC-S05-6: passed. `addopts = "--strict-config --strict-markers"` has no `-n`.
  - AC-S05-7: passed. `pytest-xdist==3.8.0` is in each service's dev dependencies. All four lock variants (memory/postgres × none/fastapi) pass `uv sync --locked` and `make test`.
  - AC-S05-8: passed. A project made by 8b0d103 still has no key after `migrate`, and `make test` is serial (87 passed, no workers). Projects committed with `false` and with `true` keep that same single line after `migrate`.
  - AC-S05-9: passed. `adopt --yes` and `adopt --refresh --yes` write no `parallelSafe`. The application's recorded test command stays `python3 -m pytest`, and its `Makefile`, `pyproject.toml`, `src` and `tests` are unchanged.
  - AC-S05-10: passed. Against 8b0d103, the TypeScript, Go, Quarkus and Spring starters differ only in `project.json` (the mark) and `docs/gates.md`. The page says: Vitest runs by file, `go test` by package, Surefire one at a time. `make test` passes on typescript (86), go and quarkus. Spring was generated and diffed but not run.
  - AC-S05-11: passed. The page gives the default, says "A missing mark is serial", and says when to set `false` (shared file, port, database or module-level state).
  - AC-S05-12: **failed**. The fragment claims MINOR. Its catch-up note says a project made before stays serial, but the line it names, `"parallelSafe": true`, does not opt in when pasted literally after `"target"`. It has no trailing comma, so `project.json` becomes invalid JSON. `make test` then quietly stays serial, and the `make verify` the note asks for fails in `check-imports` with `JSONDecodeError: Expecting ',' delimiter`. The same line with a comma opts in: 4 workers, and `make verify` passes.
  - AC-S05-13: measured (numbers below). Copying them into the quickstart and the fragment is the session's job, because both files are outside this demo's writes.
- **Measurement (AC-S05-13):**
  - Machine: 12th Gen Intel(R) Core(TM) i5-12400, `nproc` 12, Linux 7.0.0-31-generic.
  - Project: a fresh `./slipwai generate shop --backend python --frontend none` (event-modelling, FastAPI, Postgres store, target `none`, 87 unit tests, pytest 9.1.1, xdist 3.8.0, Python 3.14.4). It was warm, on branch `demo-measure` with no CI marker. Runs were interleaved, three each.
  - Times are wall-clock medians.

    | Command | Mark `true` (4 workers) | Mark `false` (serial) |
    |---|---|---|
    | `./scripts/verify --test-only` | 1.36 s (1.35/1.36/1.36) | 0.99 s (1.01/0.99/0.97) |
    | `VERIFY_FORCE=1 make verify` | 3.70 s (3.73/3.62/3.70) | 3.30 s (3.25/3.30/3.30) |
    | `VERIFY_FORCE=1 make -j verify` | 2.11 s (2.11/2.11/2.08) | 1.72 s (1.75/1.67/1.72) |

  - D89's criterion holds with the cap: the `-j` median of 2.11 s is below the serial median of 3.70 s. It also holds with serial pytest: 1.72 s against 3.30 s.
  - D103's *Would reverse if* is **not** triggered, because the capped run does not fail where serial pytest passes. On this starter the cap costs about 0.37 s on the test step and about 0.39 s on `make -j verify`, as D103 predicted.
- **Evidence:**
  - `specs/001-faster-slipwai/slices/S05-xdist/demo/01-project-json.txt`
  - `specs/001-faster-slipwai/slices/S05-xdist/demo/02-make-test-parallel.txt`
  - `specs/001-faster-slipwai/slices/S05-xdist/demo/03-make-test-integration.txt`
  - `specs/001-faster-slipwai/slices/S05-xdist/demo/04-make-test-serial.txt`
  - `specs/001-faster-slipwai/slices/S05-xdist/demo/05-mark-values.txt`
  - `specs/001-faster-slipwai/slices/S05-xdist/demo/06-outcome-sets.txt`
  - `specs/001-faster-slipwai/slices/S05-xdist/demo/07-gates-page-and-deps.txt`
  - `specs/001-faster-slipwai/slices/S05-xdist/demo/08-every-backend-and-lock.txt`
  - `specs/001-faster-slipwai/slices/S05-xdist/demo/09-other-backends-diff.txt`
  - `specs/001-faster-slipwai/slices/S05-xdist/demo/10-other-backends-make-test.txt`
  - `specs/001-faster-slipwai/slices/S05-xdist/demo/11-older-project-migrate.txt`
  - `specs/001-faster-slipwai/slices/S05-xdist/demo/12-catch-up-literal.txt`
  - `specs/001-faster-slipwai/slices/S05-xdist/demo/13-catch-up-with-comma.txt`
  - `specs/001-faster-slipwai/slices/S05-xdist/demo/14-migrate-carries-mark.txt`
  - `specs/001-faster-slipwai/slices/S05-xdist/demo/15-adopt.txt`
  - `specs/001-faster-slipwai/slices/S05-xdist/demo/16-make-j-verify-mark-true.txt`
  - `specs/001-faster-slipwai/slices/S05-xdist/demo/17-measure.sh`
  - `specs/001-faster-slipwai/slices/S05-xdist/demo/17-timings.tsv`
  - `specs/001-faster-slipwai/slices/S05-xdist/demo/18-integration-before-slice.txt`
- **Feedback:**
  - **Re-enters as a task (implementation):** fix the line the opt-in instruction names, in both places it appears.
    - Where: the fragment's catch-up note (`changelog.d/xdist.md`) and the gates-page sentence (`src/slipwai/project/parallel_tests.py`, line 19). Each says to add the line `"parallelSafe": true` "right after the `"target"` line".
    - Problem: in that position the line needs its trailing comma. Pasted as written, it silently keeps the gate serial and then turns `make verify` red with a JSON error that names neither the mark nor the comma.
    - Reproduction: `specs/001-faster-slipwai/slices/S05-xdist/demo/12-catch-up-literal.txt`.
    - Fix: name `"parallelSafe": true,` with the comma, as the quickstart already does.
  - **Notes for the next slice (not reasons to withhold acceptance):**
    - On a `slice/*` branch, `check-slice-scope` refuses an edit to `project.json`, so the one-line opt-out cannot ride in a slice. It has to land on `main` first. The gates page tells a developer to "set it `false`" without saying this.
    - D103 rule 6 says the page states that xdist costs a fraction of a second on a small suite and pays back once the suite takes several seconds. The generated page does not say it. AC-S05-11 does not ask for it, so this is not a failed example.
    - In the migrated project, `.slipwai/catch-up.md` puts this slice's note at the end of one ~1,000-word **Owes:** paragraph shared with every other unreleased note. A developer will not find it there unless they search for it.
    - Not S05's: `test_a_conditional_append_is_refused_by_an_event_in_flight_when_the_boundary_was_read` fails serially against a real Postgres, at `assert isinstance(found, list)` (a tuple came back). It fails the same way in a project made before the slice (`specs/001-faster-slipwai/slices/S05-xdist/demo/18-integration-before-slice.txt`). This is a separate defect for the Parking Lot.
    - With the mark `true`, every pytest warning appears once per worker (8 warnings instead of 2), as D103 expected.
  - The scratch projects were the only app this demo ran, and they are gone. No long-lived app was started apart from the disposable Postgres, which was stopped.

## 2026-10-04T20:48:48Z — accepted · iteration 14 · drive-hand (claude-opus-5-5)
- **Started with:** this checkout at 610db14, after T021 (8c7e4cd). For the older-project path: `git archive 8b0d103 | tar -x -C <dir>`, then that tree's `./slipwai generate shop --backend python --output <dir2> --no-init --no-install --skip-checks`, then this checkout's `slipwai migrate` inside `<dir2>/shop`. For the fresh-project path: this checkout's `./slipwai generate shop --backend python --output <dir> --no-init --no-install --skip-checks`. · **Seeded:** none. No backing service was started.
- **Driven through:** CLI. `.specify/cruise.json` names `browser`, but this slice has no screen and no HTTP surface. It changes a generated `project.json`, `scripts/verify` and `docs/gates.md`, so the CLI is the demo.
- **Examples:** demo 2 covers what T021 changed, plus the demo-1 examples it could have touched. AC-S05-1, -2, -4 to -10 and -13 are not re-run. T021 changed only the page's words (`src/slipwai/project/parallel_tests.py`) and the fragment.
  - AC-S05-12: passed. The fragment's first line is `MINOR`.
    - Where the note sits: after `migrate`, `.slipwai/catch-up.md` carries the note word for word. It is still inside the 1.6.0 entry's **Owes:** paragraph.
    - Following it literally: the line `"parallelSafe": true,` was added once, with its comma, right after the `"target"` line. `project.json` stays valid JSON.
    - `make verify` passes ("created: 4/4 workers", 87 passed, "verify: all gates passed"). `make test` then runs with 4 workers, 87 passed.
    - Before the opt-in, the same migrated project's `make test` was serial. Setting it `false` "to turn it off again" made it serial on the next run.
  - AC-S05-11: passed. In a fresh project, `docs/gates.md` gives the default ("which every new project has"), "**A missing mark is serial**", and when to set it `false` (a file, a port, a database or module-level state).
    - The corrected opt-in line reads `"parallelSafe": true,` "once, with its comma". It is identical on the page that `migrate` writes into the older project.
    - Following the page: `false` gave a serial `make test` and a passing `make verify`. Back to `true` gave 4 workers on both, and `make verify` passed. Nothing was regenerated.
    - The new small-suite sentence is there and holds against the measurement.
      - "a fraction of a second": on the starter, `./scripts/verify --test-only` took 0.98 to 1.02 s serial and 1.34 to 1.36 s with workers, about 0.35 s more. This agrees with demo 1 and with the fragment's "about 0.4 s".
      - "pay back once the suite takes several seconds": I added a scratch file of 48 CPU-bound tests of about 0.1 s each, then deleted it. Serial took 5.80 to 5.82 s and the workers took 2.45 to 2.48 s.
  - AC-S05-3: passed, re-run on the fresh project. `false`, a missing key, `"true"`, `1`, a key written twice, truncated JSON and a file with mode 000 each run `pytest apps/service/tests --ignore=apps/service/tests/integration` with no `-n`. That is the serial command demo 1 recorded, word for word. `true` adds `-n auto --maxprocesses 4`. Each change took effect on the next run with nothing regenerated.
- **Evidence:**
  - `specs/001-faster-slipwai/slices/S05-xdist/demo/d2-01-older-project-catch-up.txt`
  - `specs/001-faster-slipwai/slices/S05-xdist/demo/d2-02-fresh-project-mark-and-page.txt`
  - `specs/001-faster-slipwai/slices/S05-xdist/demo/d2-03-mark-values.txt`
- **Feedback:**
  - Demo 1's implementation finding is fixed in both places. The fragment and the page now name the line with its comma, and pasting it as they say keeps `project.json` valid and opts the project in.
  - **Notes for the next slice (not reasons to withhold acceptance):**
    - Demo 1's note still stands: in `.slipwai/catch-up.md`, this slice's note is the tail of one long **Owes:** paragraph. It starts at character 11,182 of 12,436, and the paragraph starts at 2,356. A developer will not find it there without searching.
    - The page still tells a developer to "set it `false`" without saying that `check-slice-scope` refuses a `project.json` edit on a `slice/*` branch. This carries over from demo 1 and was not re-tested here.
    - The source wraps the page's paragraph unevenly. Some lines are 270 to 291 characters, beside lines of about 130. The rendered Markdown is unaffected, but the raw file reads ragged.
  - The scratch projects under `/tmp` were the only thing this demo ran. They are deleted, and no process was left running.

## 2026-10-04T22:44:13Z — accepted · iteration 15 · drive-hand (claude-opus-5-5)
- **Started with:** this checkout at 4b397e4. Fresh projects: `./slipwai generate shop --backend python --output /tmp/s05d3/py --no-init --no-install --skip-checks`. The brief's command without `--backend` made a typescript service, which was used for example 8. Each Python project was prepared with `uv sync --project apps/service --locked`, then driven with `make test`, `make verify` and `./scripts/verify --test-only` / `--adversarial-only`. Older-project path: `git archive 8b0d103 | tar -x`, then that tree's `./slipwai generate shop --backend python --output /tmp/s05d3/before --no-init --no-install --skip-checks`, then this checkout's `slipwai migrate` in two copies. · **Seeded:** none. A scratch test file with two tests sharing a module list (example 3) was added and then removed. Marks were edited and committed in disposable copies.
- **Driven through:** CLI. `.specify/cruise.json` names `browser`, but this slice has no screen and no HTTP surface. It changes a generated `project.json`, `scripts/verify`, `docs/gates.md` and what `slipwai` commands do.
- **Examples:** demo 3 covers what D106 to D108 changed.
  - AC-S05-2: passed.
    - With mark `true` and no CI marker, pytest runs `-p xdist -n auto --maxprocesses 4` and reports "created: 4/4 workers" (87 passed).
    - With `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`, it still reports 4/4 workers. This is also the first point of AC-S05-16.
  - AC-S05-14: passed.
    - `CI=true`, `GITHUB_ACTIONS=true`, `CI=false` and `GITLAB_CI=1` each run pytest with no `-n`.
    - A leaking pair of tests passed five local parallel `make test` runs.
    - `CI=true make test` and `CI=true make verify` both failed on the second test (`['a', 'b'] == ['b']`).
    - The gates page says why the two runs differ and what to look for.
  - AC-S05-5: passed. With mark `true`, `--adversarial-only` runs with no `-n`. It exits 0 on 87 deselected.
  - AC-S05-15: passed.
    - A committed duplicate mark (`false` after "name", `true` after "target") is refused by `describe-service`, `add-service`, `add-frontend` and a second `migrate`. Each prints one line: `project.json has "parallelSafe" twice; keep one copy and run this again`. The hash is unchanged and `git status` is clean.
    - An older project whose own mark sat after "name" migrates with exit 0. The report and `.slipwai/catch-up.md` (its own `## project.json` section) carry the same sentence, and the gate runs serial.
    - Following the fragment's **Catch-up.** paragraph literally gives one key, valid JSON and no such line. `make verify` passes with 4 workers.
  - AC-S05-16: passed.
    - `1e400` (with `describe-service`) and `NaN` (with `add-service`) are each refused in one line ending "set it to true or false", with nothing written.
    - Typescript and go projects carry the no-Python sentence verbatim. In the go project, adding a Python service swaps it for the full paragraph and gives 4 workers.
    - The page names `-p no:xdist` in `PYTEST_ADDOPTS` and a root `json.py`.
  - Reading the words (example 9): passed. Every new sentence in the fragment and on the page matched a run above.
- **Evidence:**
  - `specs/001-faster-slipwai/slices/S05-xdist/demo/d3-01-parallel-local-and-autoload-off.txt`
  - `specs/001-faster-slipwai/slices/S05-xdist/demo/d3-02-ci-markers-serial.txt`
  - `specs/001-faster-slipwai/slices/S05-xdist/demo/d3-03-shared-state-ci-catches.txt`
  - `specs/001-faster-slipwai/slices/S05-xdist/demo/d3-04-adversarial-serial.txt`
  - `specs/001-faster-slipwai/slices/S05-xdist/demo/d3-05-duplicate-mark-refused.txt`
  - `specs/001-faster-slipwai/slices/S05-xdist/demo/d3-06-migrate-older-project.txt`
  - `specs/001-faster-slipwai/slices/S05-xdist/demo/d3-07-non-finite-mark-refused.txt`
  - `specs/001-faster-slipwai/slices/S05-xdist/demo/d3-08-no-python-service-page.txt`
  - `specs/001-faster-slipwai/slices/S05-xdist/demo/d3-09-reading-the-words.txt`
- **Feedback:** nothing re-enters the ladder. Notes for the next slice, none a reason to withhold acceptance:
  - The page explains why a test can pass locally and fail in CI, but it does not name the command that reproduces CI's serial run locally. The developer has to infer `CI=1 make test` from "set, to anything".
  - "keep one copy" does not say which copy to keep. After `migrate`'s merge, both copies hold the person's own value, so either is right, and the line could say so.
  - The refusals print under argparse's usage block (9 lines for `add-service`) even though the arguments were fine. Every existing refusal of this CLI does the same, so this is a CLI-wide note, not S05's.
  - In one of two local parallel `make verify` runs, the leaking test was also caught. The words "can hide" are the accurate ones.
  - The scratch projects under `/tmp/s05d3` were the only thing this demo ran, and they are deleted. No process was left running.
