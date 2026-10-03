# Quickstart — S23-refusal-in-subdirectory

Runs this checkout's `./slipwai` against a throwaway repository. No port, no seed, no backing service.

```sh
SLIPWAI="$PWD/slipwai"; T=$(mktemp -d); cd "$T"; git init -q -b main .
mkdir -p sub/shop sub/tests other
printf '[project]\nname = "shop"\nversion = "0.1.0"\nrequires-python = ">=3.11"\n' > sub/pyproject.toml
echo 'x = 1' > sub/shop/__init__.py
printf 'import unittest\nclass T(unittest.TestCase):\n    def test_x(self):\n        self.assertTrue(True)\n' > sub/tests/test_x.py
echo 'a neighbour' > other/note.txt
git add -A; git -c user.name=a -c user.email=a@b commit -qm start
cd sub; "$SLIPWAI" adopt --yes --no-init   # commits what it wrote itself
```

1. **A person's edit is refused, by the project's name for it.** `echo 'A note of mine.' >>
   delivery/docs/convergence.md`, then `"$SLIPWAI" adopt --refresh` → exit 2; the message names
   `` `delivery/docs/convergence.md` `` with no `sub/`; `tail -1 delivery/docs/convergence.md` is still the note.
   `git checkout -- delivery/docs/convergence.md` to go on.
2. **What slipwai left is its own.** In `project.json`, set the `safety-net` row's `"provenance"` to
   `"confirmed"` (the rows are a list under `convergence`, each keyed `"axis"`):
   `python3 -c 'import json; d = json.load(open("project.json")); [r.update(provenance="confirmed") for r in d["convergence"] if r["axis"] == "safety-net"]; json.dump(d, open("project.json", "w"), indent=2)'`;
   `"$SLIPWAI" adopt --refresh` → exit 0, pages rewritten, nothing committed;
   `cat .delivery-tools/written.json` lists them without `sub/`; `git status --short` does not list
   `.delivery-tools/`. Run the refresh again → exit 0.
3. **Then a person's edit on top is refused.** Append a line to one file `written.json` names; refresh → exit 2
   naming it. Take the line off again.
4. **A neighbour's work is not this run's.** `echo more >> ../other/note.txt`; refresh → exit 0; the neighbour's
   edit stands.

Then the tests: `make test TESTS="test_uncommitted test_uncommitted_subdirectory test_uncommitted_places"`.
