# Quickstart: S43-test-declarations — how to see it work

Run from the slice's worktree. The machine is shared: run only the modules named.

1. **The rule and the audit:**
   `make test TESTS="test_select_tests_argv test_select_tests_audit_narrow test_select_tests_real_s43 test_select_tests_real_declared test_select_tests_real_audit test_select_tests_generation"`
   — all pass; each planted form in R2 is named by `held()` and selected on a one-Go-file change.
2. **Nothing held:** `python3 -B -c "import sys; sys.path.insert(0,'scripts'); from pathlib import Path; from select_tests import declarations as d; print(d.held(Path('.').resolve()))"` prints `[]`.
3. **What a Go change selects:** `python3 -B scripts/select-tests.py --dry-run` on a scratch commit that touches
   `assets/languages/go/app/` only — the modules the slice declared are listed as skipped (*reads no go configuration*),
   `test_matrix` narrowed to go. (Or `--dry-run --replay <base>..<commit>`.)
4. **Same test ids (AC-S43-9):** list ids at the tip and at `063c187` (`git archive 063c187 tests src | tar -x -C <scratch>`),
   each with `python3 -B -c "import unittest,sys; sys.path[:0]=['src','tests']; s=unittest.defaultTestLoader.discover('tests'); …"`
   walking the suite; the two sorted lists are equal.
5. **The undeclared list:** `undeclared.md` equals `declarations.scan` at the tip: every `test_*` module whose
   `tree.effective(name)` is None, with its reason.
6. **The demo (the host's, D188):** after the rebase onto `adopt-method` past S26, one Go app file changed, `make test`
   inside an S39 `gate` bracket; under 900 s is acceptance, reported against 3448 s; S07's undeclared seconds on a line
   of their own; the one full run on the faulted tree (AC-S43-8). Two things decide whether the run selects at all:
   - **The branch must be a `slice/<id>` branch.** On any other name (a `demo/…` scratch branch, the trunk,
     `adopt-method`, a detached `HEAD`) the selector prints `full: not a slice branch` and runs everything. Cut the
     scratch branch as `slice/S43-demo` from the slice tip (`git switch -c slice/S43-demo <tip>`), and delete it after.
   - **`SINCE` must be the slice's tip, not `adopt-method`.** `SINCE=adopt-method` measures the whole slice, which
     changes `scripts/select-tests.py` and `scripts/select_tests/`, so the run is `full: … the selector: its effect cannot
     be established`. The actor's case is one Go file changed past what has merged: commit that one file on
     `slice/S43-demo`, then `env -u CI -u GITHUB_ACTIONS -u GITLAB_CI make test SINCE=<slice tip>`. After the fault
     commit, the same selected run, then the one full run, `env -u CI -u GITHUB_ACTIONS -u GITLAB_CI make test FULL=1`.
