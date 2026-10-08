# Quickstart: S42-mutmut-mutation (the demo, AC-S42-13; D223 item 5, D225 item 2)

Prerequisites: Python 3.11+, `uv` on `PATH`, network for the first `uv sync`, Linux or macOS (or WSL). No seed data.

```sh
F=/home/noahc/math/slipwai-graph-S42-mutmut-mutation/slipwai            # this worktree's factory, never the one on PATH
$F generate demo --backend python --output /tmp/s42-demo --no-init --no-install --skip-checks  # FastAPI, Postgres
cd /tmp/s42-demo/demo && $F add-service billing --backend python       # takes the first service's answers: FastAPI, Postgres
git add -A && git commit -qm "Add billing" && git checkout -b slice/S1
make verify; make verify               # passes; the first can print "this pass was not recorded" (the checks wrote ignored files), the second records it
grep -A2 '^mutation-full:' Makefile    # one Python line: python3 scripts/mutmut-mutation.py apps/service apps/billing
make mutation                          # nothing changed: "no mutant to run — no production file changed", exit 0
echo "# a change" >> apps/service/src/demo/__init__.py   # change one production file whose mutants the starter's tests kill
time make mutation                     # "scoped to 1 changed file(s) since `main` at …"; "skip apps/billing"
time make mutation-full; echo "exit $?"   # both services, each in full; red at the end
```

Expected, and what to record (the commands, wall time of each run, mutant counts for **both** services, `nproc`, CPU model):

1. **Scoped.** The run names `apps/service/src/demo/__init__.py` only, starts no mutmut for `apps/billing`, and ends `4 mutants:
   4 killed, 0 no tests …; passed` and `1 scoped, 0 swept, 1 skipped, 0 refused; passed`, exit 0;
   `apps/service/mutants/src/demo/__init__.py.meta` holds the only keys that are not `null`. The same run on
   `src/demo/settings.py` instead is the starter's own red: `14 mutants: 12 killed, … 2 survived; failed`, naming
   `demo.settings.x_load_settings__mutmut_3` and `_6`.
2. **The sweep, both services (D223).** `make mutation-full` runs the one line: `apps/service` from a fresh `mutants/`, then
   `apps/billing` from its own, the first's failure not stopping the second. Each ends `992 mutants: 415 killed, 463 no tests
   (reported, never failed), 114 survived; failed`, naming its survivors (the starter's own, D225); then
   `mutation: 2 swept; failed: apps/service, apps/billing`, and make exits non-zero. Record the wall time and both counts.
3. **Hand-replay a sample of the reported survivors (D225 item 2, D221's lesson).** Take at least five survivor names from
   step 2's `survived apps/service …` lines, from at least four different files (e.g. `settings.py`, `logging_setup.py`,
   `tracing.py`, `adapters/driven/event_store_memory.py`). For each, in `apps/service`:
   ```sh
   uv run --no-sync mutmut show <name>          # the diff mutmut applied
   uv run --no-sync mutmut apply <name>         # writes the mutant into src/ — the working tree, so restore it below
   PYTHONPATH=src uv run --no-sync pytest tests --ignore=tests/integration -p no:xdist -q; echo "pytest exit $?"
   git checkout -- src                          # restore the source before the next one
   ```
   A real survivor leaves pytest green (exit 0). A survivor that a direct pytest run **kills** (non-zero) is S42's own defect,
   to be fixed in S42 (D225's *would reverse if*); record each name with its pytest exit. `git status --short` is empty after
   the last restore.
4. A changed `src/demo/application/ports/read_models.py` alone (types only): *no mutant to run*, exit 0, no `mutmut run`.
5. A change to `[tool.mutmut]` in `apps/billing/pyproject.toml`: `sweep apps/billing — … changed`, and that sweep ends in the
   same 114 survivors.
6. `git status --short` is empty after each run (`mutants/` ignored), and after the edited file is put back
   (`git checkout -- apps/service/src/demo/__init__.py`) `make verify` says the full gate did not run because this tree already
   passed it: the stamp is reused.
