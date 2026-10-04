# Quickstart — S24-ci-fetches-slice-base

Runs this checkout's `./slipwai` (the `slipwai` on `PATH` may be an older one) under a temporary directory. No
port, no seed, no backing service. **Not shown:** a real runner on a real forge — nothing is pushed; the
pull-request checkout is made with git, in the shape the forge's documentation gives (research R-1).

```sh
SLIPWAI="$PWD/slipwai"; T=$(mktemp -d)
"$SLIPWAI" generate --help | head -5      # the flags this factory takes
```

1. **The generated gate fetches history.** Generate a project into `$T/shop` (any backend; `--output "$T/shop"`),
   then `grep -n -B3 -A3 'fetch-depth' "$T/shop/.github/workflows/verify.yml"` → the `verify` job's checkout
   carries `fetch-depth: 0` under a comment naming the three checks; no other job in the file carries it.
2. **So does the adopted one, on both forges.** Adopt a small repository with its CI on GitHub
   (`.github/workflows/ci.yml` present) and one with `.gitlab-ci.yml`; read `verify-delivery.yml` (the `verify` job
   carries the key, `smoke` does not) and `delivery/ci/verify-delivery.gitlab-ci.yml` (`verify-delivery` carries
   `GIT_DEPTH: "0"`; no `rules:`).
3. **A slice pull request is held.** In `$T/shop`: commit on `main`; `git checkout -b slice/S1`; change a host
   surface (append a line to `Makefile`) and commit. Make the pull-request checkout: `git clone -q
   "file://$T/shop" "$T/pr"`, then in `$T/pr`: `git checkout -q --detach origin/slice/S1; git branch -D main
   2>/dev/null`. Run `GITHUB_ACTIONS=true CI=true GITHUB_HEAD_REF=slice/S1 GITHUB_BASE_REF=main python3
   scripts/check-slice-scope.py` → exit 1, `Makefile` named, *compared with `main` at …*.
4. **With no history it now fails, and says what the job needs.** `git clone -q --depth 1 --branch slice/S1
   "file://$T/shop" "$T/shallow"`; the same command there → exit 1, one line: *NOT checked*, `fetch-depth: 0`,
   `GIT_DEPTH: "0"`, *a full clone with the trunk's branch fetched*; no `git fetch`.
5. **A branch that is not a slice is as before.** On a clone of a `feature/x` branch, with the same variables
   naming it → *nothing to hold*, exit 0.
6. **The two other gates now look.** On `feature/x` add a flag seeded `on` (the target's flag declaration) and
   commit; in the full clone `python3 scripts/check-flags.py` → exit 1 naming the flag; in a `--depth 1` clone
   with no trunk ref → exit 0.
7. **The fragment says it.** `cat changelog.d/ci-fetches-slice-base.md` in this checkout: `check-migrations` and
   `check-flags` are named, with both refusals and what to do about a red pull request.

Then the tests: `make test TESTS="test_ci_fetch_generated test_ci_fetch_adopted test_slice_scope_forge
test_ci_history_gates test_slice_scope_no_base test_slice_scope_hostile_base"`.
