# Quickstart: S42-mutmut-mutation (the demo, AC-S42-13)

Prerequisites: Python 3.11+, `uv` on `PATH`, network for the first `uv sync`, Linux or macOS (or WSL).

```sh
F=/home/noahc/math/slipwai-graph-S42-mutmut-mutation/slipwai            # this worktree's factory, never the one on PATH
$F generate demo --backend python --output /tmp/s42-demo --no-init --no-install --skip-checks  # FastAPI, Postgres
cd /tmp/s42-demo/demo && $F add-service billing --backend python       # takes the first service's answers: FastAPI, Postgres
git add -A && git commit -qm "Add billing" && git checkout -b slice/S1
make verify; make verify               # passes; the first can print "this pass was not recorded" (the checks wrote ignored files), the second records it
make mutation                          # nothing changed: "no mutant to run — no production file changed", exit 0
echo "# a change" >> apps/service/src/demo/__init__.py   # change one production file whose mutants the starter's tests kill
time make mutation                     # "scoped to 1 changed file(s) since `main` at …"; "skip apps/billing"
time make mutation-full                # both services; record the mutant counts
```

Expected, and what to record (the command, wall time, mutant counts, `nproc`, CPU model):

1. The scoped run names `apps/service/src/demo/__init__.py` only, starts no mutmut for `apps/billing`, and ends `4 mutants: 4 killed,
   0 no tests …; passed` and `1 scoped, 0 swept, 1 skipped, 0 refused; passed`; `apps/service/mutants/src/demo/__init__.py.meta`
   holds the only keys that are not `null`. The same run on `src/demo/settings.py` instead is the starter's own red: `14 mutants: 12
   killed, … 2 survived; failed`, naming `demo.settings.x_load_settings__mutmut_3` and `_6` (survivors of the starter's tests, which
   the verdict reports rather than hides).
2. `make mutation-full` runs `python3 scripts/mutmut-mutation.py apps/service` and `… apps/billing`, each from a fresh
   `mutants/`; on the default starter each fails naming its survivors (plan, *Handed back* 1): `apps/billing` is `add-service`'s
   skeleton with the first service's answers, so it ends as `apps/service` does, `992 mutants: 415 killed, 463 no tests (reported,
   never failed), 114 survived; failed`. (Awaits plan.md's Q1: what the recipe does across two services once the first fails.)
3. A changed `src/demo/application/ports/read_models.py` alone (types only): *no mutant to run*, exit 0, no `mutmut run`.
4. A changed `src/demo/__init__.py`: only `demo.x_…` keys of that file are run.
5. A change to `[tool.mutmut]` in `apps/billing/pyproject.toml`: `sweep apps/billing — … changed`, and the sweep ends in the same
   114 survivors.
6. `git status --short` is empty after each run (`mutants/` ignored), and after the edited file is put back
   (`git checkout -- apps/service/src/demo/__init__.py`) `make verify` says the full gate did not run because this tree already
   passed it (the pass recorded before the first edit): the stamp is reused. With the edit in the tree it runs the gate again.
