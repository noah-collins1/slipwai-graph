# Quickstart — S00-run-path

How to prove the slice from this checkout. Each block maps to a criterion in `spec.md`, *Slice acceptance
criteria*, `### S00-run-path`. Run everything from the repository root on `adopt-method` (D12). The cruise
runner's two marks are set deliberately, because that is the environment every iteration's gate runs in.

## Prerequisites

- Python 3.11 or newer on `PATH` as `python3` (`pyproject.toml`; the maintainer machine runs 3.14).
- `make`, `git`. No service, port or seed.

## AC-S00-1 — the smoke command

```sh
./slipwai --version
# expect: slipwai 1.5.2.dev0   (the contents of VERSION), exit 0
# pinned by tests/test_cli.py:17 test_version_flag, which reads VERSION and asserts the line
```

## AC-S00-2 — the run path is written

```sh
grep -c "Not yet proven" delivery/survey/running.md   # expect: 0
sed -n '/^## `.` (python)/,$p' delivery/survey/running.md
# expect: the command, the line it printed, the interpreter, no port/seed/service, who proved it and the date
```

## AC-S00-3 and AC-S00-4 — the suite is green inside an iteration's environment

```sh
CRUISE_RUNNER=1 CRUISE_ITERATION=2 make test TESTS="test_cruise test_cruise_guard test_cruise_index test_cruise_record test_cruise_runner test_cruise_start test_cruise_stop_hook test_cruise_sweep test_cruise_tell test_cruise_watch test_cruise_where"
# expect: OK — before the slice, 6 of 43 are red with "this session is iteration 2 of a run already under way"
# AC-S00-4: test_a_typed_cruise_starts_the_runner_detached_and_a_person_stops_it_from_anywhere still passes,
# and it sets CRUISE_RUNNER/CRUISE_ITERATION itself for the nested-start refusal (tests/test_cruise_start.py:174)
```

## AC-S00-5 — both gates, with the marks set

```sh
CRUISE_RUNNER=1 CRUISE_ITERATION=2 make verify
CRUISE_RUNNER=1 CRUISE_ITERATION=2 make -f delivery/Makefile verify
# expect: both exit 0; the unittest summary's skipped= count is no higher than the pre-slice baseline run
# (OK (skipped=9) at 5460bf9); no ratchet line and no delivery/baseline.json — the ratchet prints and records
# nothing when a command exits 0 with no prior entry (delivery/scripts/ratchet.py:205–212), so a silent, green
# run is the clean case and "no test quarantine" holds with no file. A `ratchet: … QUARANTINED` line or a
# baseline file with a `test` entry would be the failure.
# Each gate takes about 17 minutes here; the recorded runs at 030ad00 are in /tmp/gate1.log and /tmp/gate2.log.
```

## AC-S00-6 — the map moved, and the tree agrees

```sh
python3 -c "import json; print([r for r in json.load(open('project.json'))['convergence'] if r['axis']=='safety-net'][0])"
# expect: rung tests-pass, provenance confirmed, planned None, evidence naming both commands and the commit
make -f delivery/Makefile check-convergence     # expect: green
grep -n "Safety net" delivery/docs/convergence.md  # expect: `tests-pass` … `confirmed`
```

## AC-S00-7 — nothing user-visible changed

```sh
git diff --stat 5460bf9..HEAD -- assets src/slipwai catalog.json VERSION changelog.d
# expect: empty
```
