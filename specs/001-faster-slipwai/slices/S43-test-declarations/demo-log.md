# S43-test-declarations — demo log

## 2026-10-07T15:07:40Z — behaviour · iteration 27 · drive-hand (claude-opus-5-5)
- **Started with:** `git switch -c demo/S43 dbb723d`, renamed to `slice/S43-demo` (see Feedback 3). Then `python3 delivery/scripts/agents/benchmark.py start specs/001-faster-slipwai/slices/S43-test-declarations gate`, `env -u CI -u GITHUB_ACTIONS -u GITLAB_CI make test SINCE=dbb723d` (timed with `date -u +%s`), and `benchmark.py end … gate verify_failures=1 driver=cruise`. After the fault commit: `env -u CI -u GITHUB_ACTIONS -u GITLAB_CI make test SINCE=dbb723d`, then `env -u CI -u GITHUB_ACTIONS -u GITLAB_CI make test FULL=1`. Afterwards the worktree was switched back to `slice/S43-test-declarations` at `dbb723d` and the scratch branch deleted.
- **Seeded:** commit `5233691` adds the comment `// Check reports the service as ready.` above `Check()` in `assets/languages/go/app/health/health.go`. Fault commit `123d6c1` makes `Check()` return `"okay"`, the fault S38's demo used.
- **Driven through:** CLI. `hand` is `browser`, but this slice has no screen, so the demo is `make test`.
- **Examples:**
  - **AC-S43-6: failed.** The clean selected run took 2433 s against the 900 s target (D182). The full run at `063c187` took 3448 s (`runtime-table.md`), so this saves 29%.
    - Selection: 335 of 388 modules selected and 53 skipped (*reads no go configuration and none of the changed files*). Seven were narrowed to go: `test_images`, `test_line_widths`, `test_matrix`, `test_no_mocking_frameworks`, `test_postgres`, `test_readiness`, `test_stale_references`.
    - The selected modules sum to 2743.0 s in the table and the skipped ones to 672.1 s. That matches `undeclared.md`'s dry estimate (334 of 387, 2742 s), so the miss is what the plan predicted, not noise.
    - The run was red for a reason other than any fault: `test_factory_gate_stamp_inputs` failed (see AC-S43-8 and Feedback 2).
  - **S07's still-undeclared modules:** 563.5 s (from the table's rows). These are 29 modules, not 14: every selected `test_verify_scoped_*` plus `test_ux_gates_scale`. `undeclared.md` gives the same 564 s.
  - **AC-S43-8: passed.**
    - The full run on the faulted tree took 3222 s, ran 3389 tests and failed 3 modules: `test_add_service`, `test_matrix` (both because the generated project's `make verify` reports `--- FAIL: TestReportsReady … got "okay"`) and `test_factory_gate_stamp_inputs`.
    - The selected run on the same tree took 2389 s and failed the same 3 of its 335 modules. Every module that failed in the full run was selected and failed.
    - This was the demo's only full run.
  - **Step 3, a red that isn't the fault: failed.** `test_factory_gate_stamp_inputs.TestEveryVariableTheSuiteReadsIsAccountedFor.test_a_name_the_tests_read_is_a_bypass_or_has_its_reason_for_not_being_one` fails with `['SELECTED_TEST_MODULES'] != []`. It fails in all three runs and when run alone (`make test TESTS=test_factory_gate_stamp_inputs`, rc 2).
- **Evidence:** `specs/001-faster-slipwai/slices/S43-test-declarations/demo/run1-clean-selected.txt`, `specs/001-faster-slipwai/slices/S43-test-declarations/demo/run2-fault-selected.txt`, `specs/001-faster-slipwai/slices/S43-test-declarations/demo/run3-fault-full.txt`, `specs/001-faster-slipwai/slices/S43-test-declarations/demo/stamp-inputs-alone.txt`, `specs/001-faster-slipwai/slices/S43-test-declarations/demo/seed-and-fault.diff`; the gate bracket in `specs/001-faster-slipwai/slices/S43-test-declarations/benchmark.json`.
- **Feedback:**
  1. **behaviour, back to the plan:** a one-Go-file change still runs 335 of 388 modules for 2433 s, 2.7 times the 900 s acceptance figure. Most of that time is in modules the board already says aren't working yet:
     - S07's 29 modules (564 s);
     - the launcher-route and `parallel_gate` modules (`test_add_service` 118.6 s, `test_parallel_gate_families` 116.2 s, `test_parallel_gate_adopted` 60.5 s, and the `test_adopt_next.in_terminal` group);
     - `test_matrix`, which is narrowed to go but still runs.

     Even if every S07 module were declared and skipped, this run would be about 1870 s. The plan stage has to decide whether 900 s is met by declaring more modules (later slices) or whether the target is restated.
  2. **implementation, a task:** S43's new `SELECTED_TEST_MODULES` environment variable is read by `tests/test_select_tests_real_audit.py` and `tests/test_select_tests_audit_narrow.py`, but S33's guard in `tests/test_factory_gate_stamp_inputs.py` doesn't list it in `BYPASSES` or `UNCHANGING`. So `make verify`'s test step is red at `dbb723d` whatever the tree.
     - Reproduction: `make test TESTS=test_factory_gate_stamp_inputs` at `dbb723d`.
     - The task has to decide whether the variable is a stamp bypass or unchanging, and list it with its reason.
  3. **Note on the script:** the selector selects only on a `slice/<id>` branch. On `demo/S43` it prints `full: not a slice branch`, so I renamed the scratch branch `slice/S43-demo`. With `SINCE=adopt-method` the diff is the whole slice, including `scripts/select-tests.py`, so it prints `full: … the selector: its effect cannot be established`. I used `SINCE=dbb723d` (the slice tip), which is the actor's case: one Go file changed past what has merged. The quickstart's step 6 should name both points.
  4. **Note on benchmark bracketing:** opening the `gate` bracket printed `S43-test-declarations demo: cut off — a new gate entry started while it was open`. The host's open `demo` entry was cut off by the bracket the brief asked for.
  5. **Note:** in all three runs `test_images` skipped go (*ko is needed for the go image*), so the go image probe was not exercised on this machine.
