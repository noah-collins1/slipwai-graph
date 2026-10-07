# Demo log: S38-factory-test-selection

## 2026-10-06T19:36:38Z — implementation · iteration 25 · drive-hand (claude-opus-5-5)
- **Started with:** the quickstart at `52ecbd3` on `slice/S38-factory-test-selection`, run on noahc-server (12 cores) with `CI`, `GITHUB_ACTIONS` and `GITLAB_CI` unset. In the worktree: `python3 -B scripts/select-tests.py --dry-run`, `SINCE=adopt-method python3 -B scripts/select-tests.py --dry-run`, `make test SINCE=adopt-method`, `make test SINCE=adopt-method FULL=1`, `make test SKIP=test_matrix`, then `python3 -B scripts/select-tests.py --dry-run --replay <range>` for S06 `51c6de4..45ebedb`, S33 `1e8f880..e82bb06`, S08 `3138416^1..3138416` and S14 `37cdf3f^1..37cdf3f`. The three `make test` lines were each stopped by process group after their header and about three minutes of tests. The selection they print is the evidence; the timed runs below are complete runs of the same code paths. In a scratch clone: `git switch adopt-method && python3 -B scripts/select-tests.py --dry-run`. On throwaway `slice/` branches in scratch clones of the worktree under `/tmp/s38/`: `time make test SINCE=52ecbd3`, then `time make test FULL=1`, run serially, one run on the machine at a time. · **Seeded:** three one-line commits on top of `52ecbd3`:
  - (a) `slice/S38-demo-go` `308f3d3`: a comment line in `assets/languages/go/app/health/health.go`.
  - (b) `slice/S38-demo-toolkit` `8b464e8`: a comment line in `assets/toolkit/scripts/mutation-scope.py`, which `test_pit_globs` declares and loads by path.
  - (a′) `slice/S38-demo-go-module` `3acad5e`: a comment line in `assets/languages/go/modules/base/go.mod`. This was added because (a) narrows nothing (see Examples).

  Each case also got one fault commit:
  - (a) `195cae8`: `Check()` returns `"okay"`.
  - (b) `005c4ed`: `pit_matches` uses `match`, not `fullmatch`.
  - (a′) `1ad28f9`: the `tool honnef.co/go/tools/cmd/staticcheck` directive is dropped.

  The scratch clones were removed afterwards.
- **Driven through:** CLI. The slice has no screen, so agent-browser, a browser tool and HTTP do not apply. The setting's rung is `browser`; this demo dropped to the CLI for that reason.
- **Examples:**
  - **Top block, dry run with no `SINCE`:** passed. Full, `` full: `.gitignore` changed — the ignore rules: its effect cannot be established ``. The trunk's diff names `.gitignore` before `Makefile`.
  - **Top block, `SINCE=adopt-method` dry run:** full, `` full: `Makefile` changed — the root Makefile … ``. This is as the quickstart warns: `adopt-method`'s `Makefile` lacks `s38.patch`. As a result the quickstart's promised "every skip with its reason, the summary" cannot be seen on this branch until the merge.
  - **Top block, `make test SINCE=adopt-method`:** the same `full:` line, then `unittest discover`. Passed as described.
  - **Top block, `FULL=1`:** `full: FULL=1 given`. Passed.
  - **Top block, `SKIP=test_matrix`:** `selection off: SKIP given`, and 340 modules named with `test_matrix` absent. Passed.
  - **Top block, `adopt-method`:** the step as written is unreachable. After `git switch adopt-method` (`6e90d21`) there is no `scripts/select-tests.py`, because S38 has not merged. With a local branch named `adopt-method` at `52ecbd3` (the merged state, simulated), it prints `` full: not a slice branch (`adopt-method`) ``. A detached HEAD prints `full: HEAD is not on a branch`, and `CI=1` prints `full: CI is set — a CI run is the full gate`. Passed.
  - **AC-S38-15, replays:** passed as printed. All four are full, and each prints its `full:` line and `selected 341 of 341 modules against <base>` (D165):
    - S06: `assets/backing-services/prune.py`, the pruner.
    - S33: `Makefile`.
    - S08: `src/slipwai/project/makefile.py`, the generator.
    - S14: `src/slipwai/project/agents.py`, the generator.

    No replay narrowed a backend or skipped a module. That is a finding about D130's payback (D157 point 3), not a failed example.
  - **AC-S38-15, timed case (a), go app:** failed against AC-S38-8 and AC-S38-9.
    - The criteria expect that the modules reading no go configuration are skipped, and that `test_matrix` and the other generating modules run with `FACTORY_BACKENDS=go`.
    - Instead it printed `selected 341 of 341`: no skip, no narrowing, and no line saying why.
    - The cause, from the selector's own API (`demo/case-a-probe.txt`): the `slipwai` package's read list holds `assets/languages/go/app` and `assets/languages/go/event-port`. Every declared module imports `slipwai`, even if only for `ROOT`, so every one gains the non-narrowable reason ``imports `slipwai`, which reads `assets/languages/go/app` ``. All 15 declared modules run, and the 7 that would narrow run whole.
    - The same holds under `go/event-port/`. `go/scripts/`, `go/modules/` and `go/flags/` do narrow. The real-tree test `test_select_tests_real_backends` uses `go/scripts/go-mutation.py`, so it never meets the case.
    - Times on `308f3d3`: selected 3268.5 s, `FULL=1` 3314.9 s.
  - **AC-S38-15, timed case (b), toolkit script:** passed. 335 of 341 selected, with six modules skipped (*reads no configuration*). Times on `8b464e8`: selected 3254.7 s, `FULL=1` 3312.1 s.
  - **AC-S38-15, case (a′), go module file:** passed. 334 of 341 selected, seven skipped (*reads no go configuration*), and seven narrowed to go, with java-quarkus, java-spring, python and typescript named as unaffected. A clean timed pair was not run here. The faulted pair below is on one commit, so it serves as this case's figure: selected 2804.5 s, full 2884.1 s.
  - **AC-S38-16, soundness:** passed, at the level of results, in all three cases. Every module that failed in the full run also failed in the selected run.
    - (a): full failed `test_add_service`, `test_matrix` and `test_factory_repository`; selected failed the same three. Both ran 341 modules.
    - (b): full failed `test_pit_globs`, `test_mutation_java_classes`, `test_select_tests_real_audit` and `test_factory_repository`; selected failed all four, plus `test_matrix`.
    - (a′): full failed `test_matrix`, `test_language_skeletons`, `test_monorepos`, `test_mutation_stamp_untouched` and `test_factory_repository`; selected failed all five, with `test_matrix` narrowed to go and red in 26 s.
    - Each fault fails modules beyond `test_factory_repository`, which is red without any fault (below).
  - **Found while running, not an example:** `make test SINCE=<ref>` goes red on a clean tree.
    - In every selected run, `test_matrix.test_a_go_service_importing_a_workspace_module_is_mutation_tested` failed with ``mutation: SINCE `52ecbd3` names no commit``. `make` exports the command-line `SINCE` to the tests, and the generated project's `make mutation` reads it.
    - That breaks AC-S38-17's "no change to how a test runs". The quickstart's own `make test SINCE=adopt-method` will fail the same way whenever this test runs.
    - With `FULL=1` the test passes.
  - **Found while running, not an example:** the slice tip fails the full suite.
    - Every full and selected run, faulted or clean, failed `test_factory_repository.test_the_factorys_own_gate_runs_the_same_checks_ci_does`, which reports ``'test' not found in 'verify-checks: lint typecheck check-structure'``.
    - The person's `s38.patch` (`75150f9`) moved `test` from `verify-checks`' prerequisites into its recipe (`test FULL=1`). The test still reads the prerequisite line.
    - So `make verify` on this branch is red until the test or the patch agrees.
- **Evidence:**
  - Top block: `specs/001-faster-slipwai/slices/S38-factory-test-selection/demo/top-1-dryrun-nosince.txt`, `specs/001-faster-slipwai/slices/S38-factory-test-selection/demo/top-2-dryrun-since.txt`, `specs/001-faster-slipwai/slices/S38-factory-test-selection/demo/top-3-make-n.txt`, `specs/001-faster-slipwai/slices/S38-factory-test-selection/demo/top-4-make-test.txt`, `specs/001-faster-slipwai/slices/S38-factory-test-selection/demo/top-5-make-test.txt`, `specs/001-faster-slipwai/slices/S38-factory-test-selection/demo/top-6-make-test.txt`, `specs/001-faster-slipwai/slices/S38-factory-test-selection/demo/top-7-adopt-method.txt`.
  - Replays: `specs/001-faster-slipwai/slices/S38-factory-test-selection/demo/replay-S06.txt`, `specs/001-faster-slipwai/slices/S38-factory-test-selection/demo/replay-S33.txt`, `specs/001-faster-slipwai/slices/S38-factory-test-selection/demo/replay-S08.txt`, `specs/001-faster-slipwai/slices/S38-factory-test-selection/demo/replay-S14.txt`.
  - Cases: `specs/001-faster-slipwai/slices/S38-factory-test-selection/demo/case-a-dryrun.txt`, `specs/001-faster-slipwai/slices/S38-factory-test-selection/demo/case-a-probe.txt`, `specs/001-faster-slipwai/slices/S38-factory-test-selection/demo/case-b-dryrun.txt`, `specs/001-faster-slipwai/slices/S38-factory-test-selection/demo/case-a2-dryrun.txt`, `specs/001-faster-slipwai/slices/S38-factory-test-selection/demo/branches-and-faults.txt`.
  - Timings: `specs/001-faster-slipwai/slices/S38-factory-test-selection/demo/timings.md`.
  - Run summaries (header, selector lines, every failure with its traceback, tail): `specs/001-faster-slipwai/slices/S38-factory-test-selection/demo/runs/`.
- **Feedback:**
  1. **implementation, to a task. AC-S38-8 and AC-S38-9 do not hold for the go backend's own code.**
     - A change under `assets/languages/<backend>/app/` or `event-port/` selects every module and narrows nothing, because importing `slipwai` at all counts as reading whatever the package reads (T037).
     - Reproduction: `demo/case-a-dryrun.txt` and `demo/case-a-probe.txt`.
     - Most backend slices change `app/`, so this is where the narrowing was meant to pay. The reach should be per imported submodule, or the "imports `slipwai`" reason should be narrowable when what it reaches is that backend's own assets. A real-tree test on a `go/app/` path should hold it.
     - A full selection with no skip should also say why.
  2. **implementation, to a task. `make test SINCE=<ref>` leaks `SINCE` into the tests,** and `test_matrix`'s go mutation test fails on every selected run. The selector should strip `SINCE` (and `FULL`) from the environment it hands `unittest`. This is AC-S38-17's "no change to how a test runs".
  3. **implementation, to a task (needs a person, since the root `Makefile` is theirs). `test_factory_repository` is red on the slice tip** against `s38.patch`'s `verify-checks` recipe. Either the test learns the recipe form, or the patch keeps `test` as a prerequisite in a way the person applies.
  4. **Figures, for D130 (reported, not judged).**
     - Saving on a selected run: case (a) 46 s (1.4%), case (b) 57 s (1.7%), case (a′) 80 s (2.8%). All four replays are full.
     - The cost is in the undeclared majority: 326 of 341 modules always run. A saving worth the name needs `test_matrix`-class modules narrowed, and those are exactly the ones finding 1 stops from narrowing.
  5. **S39.**
     - None of these figures belongs to S39's measures as a quantity S39 computes. S39 reads the benchmark brackets (stage, elapsed and worked time) and never times `make test`.
     - This demo's own wall time (about nine hours of runs) lands inside S38's open `hand` bracket (`52ecbd3`). In S39's stage time it counts as one demo stage, with the test runs indistinguishable from the rest.
  6. **Notes for the quickstart.**
     - Its `git switch adopt-method` line cannot run before the merge.
     - The `SINCE=adopt-method` line can only show a full run on this branch.
     - Case (b)'s skip reason, *reads no configuration*, omits *and none of the changed files*, which is the real reason a module reading files is skipped.

## 2026-10-07T02:38:47Z — accepted · iteration 25 · drive-hand (claude-opus-5-5)
- **Started with:** the slice tip `be5b646` cloned to `/tmp/s38/c`, on noahc-server (12 cores), with `CI`, `GITHUB_ACTIONS` and `GITLAB_CI` unset and one suite on the machine at a time. Commands, in order:
  1. `time make test TESTS=test_factory_repository`, run at the tip.
  2. On a throwaway `slice/S38-demo2-go`: `SINCE=be5b646 python3 -B scripts/select-tests.py --dry-run`, then `time make test SINCE=be5b646` and `time make test FULL=1`.
  3. After the fault commit, on the same branch: `time make test FULL=1`, then `time make test SINCE=be5b646`.
  4. In a second clone `/tmp/s38/q` on `slice/S38-factory-test-selection` itself: the quickstart's `SINCE=HEAD python3 -B scripts/select-tests.py --dry-run`, once after an uncommitted change and once after a committed one.

  Both clones were removed afterwards. · **Seeded:** two commits on `slice/S38-demo2-go` over `be5b646`:
  - `fe5e71b`: demo 1's case (a) line, the comment `// Check reports that the service is up.` in `assets/languages/go/app/health/health.go`.
  - `2130852`: demo 1's fault (a), `Check()` returns `"okay"`.
- **Driven through:** CLI. The slice has no screen, so agent-browser, a browser tool and HTTP do not apply. The setting's rung is `browser`; this demo dropped to the CLI for that reason.
- **Examples:**
  - **Defect 3, `test_factory_repository` on the tip:** passed. 16 tests OK in 1.6 s, including `test_the_factorys_own_gate_runs_the_same_checks_ci_does`. It is also green in all four runs below.
  - **Defect 1 and AC-S38-8/-9/-12, a go-app line:** passed. `selected 336 of 343 modules against be5b646`, where demo 1 got 341 of 341.
    - Seven modules narrowed to `backend go only (java-quarkus, java-spring, python, typescript unaffected)`: `test_images`, `test_line_widths`, `test_matrix`, `test_no_mocking_frameworks`, `test_postgres`, `test_readiness` and `test_stale_references`.
    - Seven were skipped, each as *reads no go configuration*: `test_gitea_pages`, `test_go_mutation_file`, `test_migration_script`, `test_mutation`, `test_pit_globs`, `test_release` and `test_versions`.
    - The other 329 ran whole. `make test` printed the same lines as the dry run.
  - **Timed pair on `fe5e71b`:** passed. Selected: 2886.7 s, 336 of 343, green. `FULL=1`: 3320.0 s, `full: FULL=1 given`, green. The saving is 433 s (13.1%); demo 1's case (a) saved 46 s (1.4%).
  - **Defect 2, `SINCE` leaking into the tests:** passed. The selected run on the clean change exits 0 with no FAIL or ERROR. `test_matrix.test_a_go_service_importing_a_workspace_module_is_mutation_tested` passes under `make test SINCE=be5b646`, where demo 1 saw ``mutation: SINCE `52ecbd3` names no commit``. It passes on the faulted selected run too.
  - **AC-S38-16, soundness, on `2130852`:** passed.
    - Full (2923.2 s, 343 modules) failed `test_add_service` and `test_matrix`. Both fail with `make verify` exit 2 in the generated project, which reports `--- FAIL: TestReportsReady … got "okay"`.
    - Selected (2846.8 s, 336 of 343) failed the same two. `test_matrix`, narrowed to go, was red in the second batch (21 tests, 78.5 s).
    - No module failed in full alone. With defect 3 fixed, `test_factory_repository` no longer pads either list.
  - **The quickstart's `SINCE=HEAD` pointer (T045's rewrite):** passed, for an uncommitted change.
    - After an uncommitted go-app edit on `slice/S38-factory-test-selection`, it prints the SINCE line, the seven skips (*reads no go configuration*), the seven narrowings and `selected 336 of 343`.
    - After an uncommitted `mutation-scope.py` edit, it prints six skips, each with T045's *reads no configuration and none of the changed files*, and `selected 337 of 343`.
    - After a committed change, `SINCE=HEAD` compares the commit with itself. All 15 declared modules are skipped as *reads none of the changed files* (328 of 343). That is right for an empty diff, but not what the reader wanted. `SINCE=HEAD~1` shows the change.
    - The rest of the top block stands from demo 1. Its lines now say what they show before the merge.
- **Evidence:**
  - Step 1: `specs/001-faster-slipwai/slices/S38-factory-test-selection/demo/demo2-1-factory-repository.txt`.
  - Dry run: `specs/001-faster-slipwai/slices/S38-factory-test-selection/demo/demo2-2-go-app-dryrun.txt`.
  - Quickstart pointer: `specs/001-faster-slipwai/slices/S38-factory-test-selection/demo/demo2-5-quickstart-since-head.txt`.
  - Branch and fault diffs: `specs/001-faster-slipwai/slices/S38-factory-test-selection/demo/demo2-branches-and-faults.txt`.
  - Timings: `specs/001-faster-slipwai/slices/S38-factory-test-selection/demo/demo2-timings.md`.
  - Run summaries (header, selector lines, every failure with its traceback, the generated project's go test failure, the mutation example's result, tail): `specs/001-faster-slipwai/slices/S38-factory-test-selection/demo/demo2-runs/clean-selected.txt`, `specs/001-faster-slipwai/slices/S38-factory-test-selection/demo/demo2-runs/clean-full.txt`, `specs/001-faster-slipwai/slices/S38-factory-test-selection/demo/demo2-runs/fault-full.txt`, `specs/001-faster-slipwai/slices/S38-factory-test-selection/demo/demo2-runs/fault-selected.txt`.
- **Feedback:** All three demo 1 defects are fixed as the actor sees them. Nothing re-enters the ladder. Notes for the next slice:
  1. **Skip reason for a go change.** *reads no go configuration* is not quite true of `test_go_mutation_file`, which declares `assets/languages/go/scripts/go-mutation.py`. It reads go material, just not the changed file. T045 gave the toolkit case *… and none of the changed files*; the go case wants the same tail.
  2. **Quickstart, `SINCE=HEAD`.** "after a change" should read "after an uncommitted change". The alternative is to add `SINCE=HEAD~1` for a committed one. A reader who commits first sees every declared module skipped and may take the selector to be broken.
  3. **Reading a selected run's result.** A narrowed run is two `unittest` batches (here 2741 tests, then 21), each with its own `Ran …`/`OK`/`FAILED`. The `selected N of M` line is printed again after them. A reader skimming the tail must read both batches or trust make's exit status. One closing line, *N modules, all passed* or *failed: <modules>*, would settle it.
  4. **Figures, for D130 (reported, not judged).** A go-app change now saves 13.1% of a full run (433 s of 3320 s). All 15 declared modules either narrow or skip; the remaining cost is the 328 undeclared modules, which always run.
  5. **S39.** None of these figures is a quantity S39 computes. This demo's roughly 3.5 h of runs lands in S38's open `hand` bracket (`be5b646`).
