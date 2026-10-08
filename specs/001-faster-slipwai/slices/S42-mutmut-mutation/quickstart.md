# Quickstart: S42-mutmut-mutation (the demo, AC-S42-13)

Prerequisites: Python 3.11+, `uv` on `PATH`, network for the first `uv sync`, Linux or macOS (or WSL).

```sh
F=/home/noahc/math/slipwai-graph-S42-mutmut-mutation/slipwai            # this worktree's factory, never the one on PATH
$F generate demo --backend python --output /tmp/s42-demo --no-init --no-install --skip-checks  # FastAPI, Postgres
cd /tmp/s42-demo/demo && $F add-service billing --backend python
git add -A && git commit -qm "Add billing" && git checkout -b slice/S1
make mutation                          # nothing changed: "no mutant to run — no production file changed", exit 0
$EDITOR apps/service/src/demo/settings.py  # change one production file
time make mutation                     # "scoped to 1 changed file(s) since `main` at …"; "skip apps/billing"
time make mutation-full                # both services, one line each; record the mutant counts
```

Expected, and what to record (the command, wall time, mutant counts, `nproc`, CPU model):

1. The scoped run names `apps/service/src/demo/settings.py` only, starts no mutmut for `apps/billing`, and its last
   line counts it `1 scoped, 0 swept, 1 skipped`; `apps/service/mutants/src/demo/settings.py.meta` holds the only keys
   that are not `null`.
2. `make mutation-full` runs `python3 scripts/mutmut-mutation.py apps/service` and `… apps/billing`, each from a fresh
   `mutants/`; on the default starter it fails naming its survivors (plan, *Handed back* 1); the billing service — a
   bare `add-service` skeleton — passes.
3. A changed `src/demo/application/ports/read_models.py` alone (types only): *no mutant to run*, exit 0, no `mutmut run`.
4. A changed `src/demo/__init__.py`: only `demo.x_…` keys of that file are run.
5. A change to `[tool.mutmut]` in `apps/billing/pyproject.toml`: `sweep apps/billing — … changed`.
6. `git status --short` is empty after each run (`mutants/` ignored), and `make verify` afterwards reuses its stamp.
