# Quickstart — S21-refresh-keeps-owned-files

Runs this checkout's `./slipwai` against a throwaway repository. No port, no seed, no backing service.

```sh
SLIPWAI="$PWD/slipwai"; T=$(mktemp -d); cd "$T"; git init -q -b main .
printf '[project]\nname = "shop"\nversion = "0.1.0"\nrequires-python = ">=3.11"\n' > pyproject.toml
mkdir -p shop tests; echo 'x = 1' > shop/__init__.py
printf 'import unittest\nclass T(unittest.TestCase):\n    def test_x(self):\n        self.assertTrue(True)\n' > tests/test_x.py
git add -A; git -c user.name=a -c user.email=a@b commit -qm start
"$SLIPWAI" adopt --yes   # commits what it wrote itself
```

1. **The four stay.** Set `"enabled": true` and `"max_iterations": 10` in `.specify/cruise.json`, write a real
   paragraph into `.specify/product-owner.md`, change one value in `.specify/models.json` and `.specify/drive.json`,
   commit. `"$SLIPWAI" adopt --refresh` → `git status --short` lists none of the four.
2. **A missing one comes back.** `git rm -q .specify/cruise.json`, commit, refresh → the file exists with
   `"enabled": false`.
3. **An uncommitted edit is not a refusal.** Edit `.specify/cruise.json`, do not commit, refresh → exit 0, the
   edit is still there.
4. **The pages still follow.** In `project.json`, set the `safety-net` row to `"rung": "tests-pass"`,
   `"provenance": "confirmed"`; refresh → `<delivery>/docs/convergence.md` shows `tests-pass`;
   `project.json` `strategy.before` and `<delivery>/docs/change-strategy.md` no longer say *a green suite in the
   gate*.

Then the tests: `make test TESTS="test_refresh_owned test_refresh_strategy"`.
