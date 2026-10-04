# Quickstart — S24-ci-fetches-slice-base

Runs this checkout's `./slipwai` (the `slipwai` on `PATH` may be an older one) under a temporary directory. No
port, no seed, no backing service. **Not shown:** a real runner on a real forge — nothing is pushed; each CI
checkout is made with git, in the shape the forge's documentation gives (research R-1). Every step below was run
as written on 2026-10-04 (cruise iteration 12).

```sh
SLIPWAI="$PWD/slipwai"; T=$(mktemp -d); G="git -c user.name=a -c user.email=a@b"
CI_ENV="env -u GITHUB_BASE_REF -u CI_COMMIT_REF_NAME GITHUB_ACTIONS=true CI=true"
"$SLIPWAI" generate shop --backend python --target aws --output "$T" --no-init --no-install --skip-checks
```

`generate` makes `$T/shop`, a git repository on `main` with one commit.

1. **The generated gate fetches history.** `grep -n -B3 -A3 'fetch-depth' "$T/shop/.github/workflows/verify.yml"`
   → the `verify` job's checkout carries `fetch-depth: 0` under a comment naming the checks that need it;
   `grep -c 'fetch-depth' "$T/shop/.github/workflows/verify.yml"` → `1`: no other job carries it.
2. **So does the adopted one, on both forges.** Make two small repositories and adopt each:

   ```sh
   for forge in gh gl; do
     mkdir -p "$T/$forge/app/shop" "$T/$forge/app/tests"; cd "$T/$forge/app"; git init -q -b main .
     printf '[project]\nname = "shop"\nversion = "0.1.0"\nrequires-python = ">=3.11"\n' > pyproject.toml
     echo 'x = 1' > shop/__init__.py
     printf 'import unittest\nclass T(unittest.TestCase):\n    def test_x(self):\n        self.assertTrue(True)\n' > tests/test_x.py
     if [ $forge = gh ]; then mkdir -p .github/workflows; printf 'on: push\njobs: {}\n' > .github/workflows/ci.yml
     else printf 'stages: [test]\n' > .gitlab-ci.yml; fi
     git add -A; $G commit -qm start; "$SLIPWAI" adopt --yes --no-init | grep 'CI:'
   done
   ```

   `grep -n -A2 'actions/checkout' "$T/gh/app/.github/workflows/verify-delivery.yml"` → the `verify` job's checkout
   has `with:` / `fetch-depth: 0`. `grep -n -B1 -A3 'variables\|rules' "$T/gl/app/delivery/ci/verify-delivery.gitlab-ci.yml"`
   → `verify-delivery` carries `variables:` / `GIT_DEPTH: "0"`, and there is no `rules:`.
3. **A slice pull request is held.** In `$T/shop`:

   ```sh
   cd "$T/shop"; git checkout -q -b slice/S1; echo '# mine' >> Makefile; $G commit -qam 'a host change'
   git checkout -q main
   git clone -q "file://$T/shop" "$T/pr"; cd "$T/pr"; git checkout -q --detach origin/slice/S1; git branch -D main
   $CI_ENV GITHUB_HEAD_REF=slice/S1 GITHUB_BASE_REF=main python3 scripts/check-slice-scope.py; echo "exit $?"
   ```

   → exit 1, `Makefile` named, *compared with `main` at …*.
4. **With no history it now fails, and says what the job needs.** This is also the fragment's catch-up, followed:
   a job whose checkout has no key.

   ```sh
   git clone -q --depth 1 --branch slice/S1 "file://$T/shop" "$T/shallow"; cd "$T/shallow"
   $CI_ENV GITHUB_HEAD_REF=slice/S1 python3 scripts/check-slice-scope.py; echo "exit $?"
   ```

   → exit 1, one line: *NOT checked*, `fetch-depth: 0`, `GIT_DEPTH: "0"`, *a full clone with the trunk's branch
   fetched*; no `git fetch`. Adding the key is step 3's checkout: the same branch, with history, is held.
5. **A branch that is not a slice is as before, and the migrations gate now looks.** In `$T/shop`, a pull request
   that carries an expand and its contract together:

   ```sh
   cd "$T/shop"; git checkout -q -b feature/x
   printf 'ALTER TABLE orders ADD COLUMN status text;\n' > apps/service/migrations/202610010900_orders_add_status.sql
   printf -- '-- contract: 202610010900_orders_add_status\nALTER TABLE orders DROP COLUMN legacy;\n' \
     > apps/service/migrations/202610020900_orders_drop_legacy.sql
   git add apps/service/migrations; $G commit -qm 'expand and contract together'; git checkout -q main
   git clone -q "file://$T/shop" "$T/fx"; cd "$T/fx"; git checkout -q --detach origin/feature/x; git branch -D main
   $CI_ENV GITHUB_HEAD_REF=feature/x python3 scripts/check-slice-scope.py; echo "exit $?"
   $CI_ENV GITHUB_HEAD_REF=feature/x python3 scripts/check-migrations.py; echo "exit $?"
   ```

   → `check-slice-scope`: *nothing to hold*, exit 0. `check-migrations`: exit 1, *is new in this same change*.
6. **The same change with no history passes, as it did before the slice.**

   ```sh
   git clone -q --depth 1 --branch feature/x "file://$T/shop" "$T/fx1"; cd "$T/fx1"
   $CI_ENV GITHUB_HEAD_REF=feature/x python3 scripts/check-migrations.py; echo "exit $?"
   ```

   → exit 0. (`check-flags` answers the same way for a flag seeded other than `off`; it needs the flag's reader and
   both its tests beside the seed, so it is shown by `tests/test_ci_history_gates.py` and not by hand here.)
7. **The fragment says it.** `cat changelog.d/ci-fetches-slice-base.md` in this checkout: `check-migrations` and
   `check-flags` are named, with both refusals, what to do about a red pull request, and what a repository whose
   trunk is not `main` or `master` meets.

Then the tests: `make test TESTS="test_ci_fetch_generated test_ci_fetch_adopted test_ci_fetch_migrate
test_slice_scope_forge test_slice_scope_forge_nobase test_ci_history_gates test_slice_scope_no_base
test_slice_scope_hostile_base test_slice_scope_report"`.
