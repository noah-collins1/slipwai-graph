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
