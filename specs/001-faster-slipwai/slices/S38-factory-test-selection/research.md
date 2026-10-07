# Research: S38-factory-test-selection

Every fact below was read or run in the slice's worktree at `8072724` (`slice/S38-factory-test-selection`, cut from
`adopt-method`), with `python3 -B` and nothing written under `assets/`. There is no `.codegraph/` in this tree, so
every answer came from reading files and text search. Make probes ran in `/tmp/s38/mk`.

## R-1 The scoped gate's change functions load as they stand, and cost nothing

`assets/toolkit/scripts/check-slice-scope.py` loads by path under any module name, and the package
`assets/toolkit/scripts/verify_scoped/` loads with `spec_from_file_location(..., submodule_search_locations=[...])`
registered as `verify_scoped`, so `verify_scoped.changes` imports its own `.record` unchanged. Neither left an
interpreter cache: `changes.py` sets `sys.dont_write_bytecode` itself, and the probe ran under `-B` with the switch on
before the first load (D118, D121).

- `merge_base()` here returns `Base(commit=e1a9e43…, trunk='main', named='main', …)`; the field is `commit`, not `sha`.
- `changes.changed(scope, base)` — git's `--no-renames` diff, untracked files, and every path whose raw bytes or mode
  differ — took 0.06 s against the trunk (1140 paths) and 0.08 s against `adopt-method` (1 path: this slice's
  `benchmark.json`).
- `changes.unpushed(scope, base)` returned an empty `Span` (local `main` level with `origin/main`).

So the selector takes D117 rule 2, D125's raw comparison and D153's unpushed range from those two files, loaded as
they ship (D156 point 1), and runs full where either cannot be loaded. Selection costs well under a second.

## R-2 The base: 1140 paths against the trunk, 1 against `adopt-method`

Measured against `main`'s merge-base, this branch's change set includes `Makefile`, `catalog.json` and
`tests/support.py`, so every run here would be full (the reason D156 exists). With `SINCE=adopt-method` it is the slice's
own folder. `SINCE` therefore decides whether S38 saves anything in this repository before `adopt-method` reaches
`main`; it is D156's (b) and the host's practice, not something the selector infers.

## R-3 Make: a sub-make's own assignment wins, and `@` survives `$(if)`

In `/tmp/s38/mk`, an outer recipe calling `"$(MAKE)" … inner FULL=1` gave the inner recipe `FULL=1`, in make and in
its environment, under each of: no `FULL`; `make outer FULL=`; `FULL=0 make outer`; `make outer FULL=0`;
`MAKEFLAGS='FULL=' make outer`; `make -e outer FULL=x`. So `verify` can force the whole suite by passing `FULL=1` to
its `verify-checks` call, and nothing on the command line or in the environment undoes it. A recipe written
`$(if $(T),@echo a,@echo b)` runs silently either way: the `@` is read after expansion. Command-line variables
(`SINCE`, `FULL`, `FACTORY_BACKENDS`, `RATCHET_TIGHTEN`) reach the recipe's environment, so the selector reads them
there and the Makefile does not pass them by hand.

## R-4 The suite's shape

- 318 `tests/test_*.py` modules and eight helpers (`support`, `scoped_fixture`, `stamp_fixture`, `render_fixture`,
  `parallel_gate`, `gate_audit`, `forge_checkout`, `mutation_scope_fixture`) plus `tests/fixtures/`.
- 31 modules call `spec_from_file_location`; ten modules and `scoped_fixture.py` use `importlib.import_module` or
  `__import__` — loads an import scan cannot see. A module or helper that loads by path must name what it loads in
  its declaration, or stay undeclared and always run.
- The modules that read `backends_under_test()` or `FACTORY_BACKENDS`: `test_matrix`, `test_images`, `test_monorepos`,
  `test_postgres`, `test_readiness`, `test_flag_gate`, `test_line_widths`, `test_no_mocking_frameworks`,
  `test_stale_references`, `test_mutation_scope_real_go`, `test_mutation_scope_real_spring`,
  `test_mutation_stamp_untouched`, `test_factory_repository`, `test_factory_gate_stamp`, `test_factory_gate_stamp_inputs`.
  The last four name the variable rather than narrow by it; whether each narrows is read per module.
- A full run is `PYTHONPATH=src python3 -m unittest discover -s tests -v`; a named run is
  `PYTHONPATH=src:tests python3 -m unittest -v <modules>`, which CI already trusts (`verify.yml`). The suite runs
  serially; S05's xdist does not reach it (G12).

## R-5 Asset directories are not all read by the configuration their name suggests

`src/slipwai` reads `assets/languages/` through `LANGUAGE_ROOT`:

| Directory | Read by | So a change there reaches |
|---|---|---|
| `typescript/app`, `typescript/locks` | `project/languages/typescript.py` | backend `typescript` |
| `typescript/biome`, `typescript/app/package.json` | `project/biome.py` — the browser app too | backend `typescript` **or** frontend `react-vite` |
| `java/build` | `project/languages/java_*.py` **and** `wrappers.py` (adoption's Maven Wrapper) | backends of family `java` **or** `slipwai adopt` |
| `<x>/…` through `examples.py` | the backend or its family | that backend or family |
| `FLAG_READERS[backend].tree` (`project/flags.py`) | per backend | that backend (to be confirmed per row at implementation) |

So a path map derived only from directory names is unsound for `typescript/biome` and `java/build`. The map takes its
backend and family names from `catalog.json` (`backends`, each one's `family`) and adds the cross-reads above as named
rows; a test holds the rule rather than the list: every reference to an asset root (`LANGUAGE_ROOT`, `FRONTEND_ROOT`
and the other roots `slipwai.assets` exports, and literal `assets/<tree>/` strings) in `src/slipwai/` names a directory
the map attributes to the module that holds it, or the test fails naming the reference. `src/slipwai/` itself never
changes in a selected run (any change there is full), so the scan holds the map to the generator the run executes.
The same check covers `assets/backing-services/<x>/` against `prune.py`'s `LANGUAGES` and `OWNED_FILES`.

## R-6 What git ignores under the trees the suite reads

Here, nothing but interpreter caches is ignored under `assets/`, `src/` or `tests/`. Git cannot say whether an
ignored file changed since the base, so the presence of one (other than `__pycache__/`, `*.pyc`, `*.pyo` — D119's
caches) is the change AC-S38-10 broadens on.

## R-7 Environment that changes what the selector would see

Beyond the variables the criteria name (`CI`, `GITHUB_ACTIONS`, `GITLAB_CI`, `RATCHET_TIGHTEN`, `FULL`, `SINCE`,
`TESTS`, `SKIP`, `FACTORY_BACKENDS`), git reads repository-locating variables — `GIT_DIR`, `GIT_WORK_TREE`,
`GIT_INDEX_FILE`, `GIT_OBJECT_DIRECTORY`, `GIT_ALTERNATE_OBJECT_DIRECTORIES`, `GIT_COMMON_DIR`, `GIT_NAMESPACE`,
`GIT_CONFIG_PARAMETERS`, `GIT_CONFIG_COUNT` — which would make the change set describe another tree than the one the
tests read. Any of them set means full, with the variable named. This is S06's lesson (the converge passes kept finding
"what make or the environment can change"), applied before the first pass rather than after the fifth.

## R-8 Versioning

The selector is under `scripts/`, which the wheel does not carry (`pyproject.toml`'s force-include names `assets/`,
`catalog.json`, `VERSION`). The declarations and the selector's tests are under `tests/`; the root `Makefile` comes by
patch; `docs/maintaining.md` is a factory page. Nothing under `assets/`, `src/slipwai/` or `catalog.json` changes, so
there is no bump and no fragment (AC-S38-17, G14).

## R-9 `SKIP` naming every module (converge pass 2's question, answered by the host)

T032 made `make test SKIP="<every module>"` say `selection off: SKIP given` and run no module, where the unpatched
recipe ran the whole suite — by accident: `filter-out` left `TESTS` empty and the empty branch was `discover`.
Converge pass 2 asked whether priority 5 should make it run every module instead. It stays as T032 left it, with the
line saying no module runs: AC-S38-13 gives `SKIP` the meaning *every module but these*, the person named every module,
and a run with `SKIP` set never reads, writes or removes a stamp (the bypass list), so nothing is recorded as a pass.
That is not a doubt about what changed — the only thing priority 5 broadens on. An explicitly empty `TESTS` is not
*given* (T034): it reads as unset.
