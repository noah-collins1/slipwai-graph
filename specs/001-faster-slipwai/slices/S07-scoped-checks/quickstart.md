# Quickstart: seeing S07 work

Run from this checkout; the scratch directory is the run's own (`/home/noahc/math/.cruise27/`), cleared afterwards.
`generate` writes the project to `<output>/<name>`, so every step below runs in `/home/noahc/math/.cruise27/s07demo/s07demo`.

## 1. The record names the four

```sh
./slipwai generate s07demo --output /home/noahc/math/.cruise27/s07demo --frontend react-vite --integration claude --no-init --no-install --skip-checks
cd /home/noahc/math/.cruise27/s07demo/s07demo
python3 -B scripts/verify-scoped.py record | python3 -c 'import json,sys; c=json.load(sys.stdin)["checks"]; [print(n, c[n]["inputs"] is not None, c[n]["claims"]) for n in ("check-agents","check-speckit","check-extensions","check-constitution")]'
```

Expected: each `True True` ([data-model.md](data-model.md#the-four-rows-verify_scopedtablepy)).

## 2. Make the project runnable, then take a baseline on a slice branch

Steps 3 and 4 need the integration and the ux-gates kit installed, the dependencies, previews to render, a browser the
kit can open, and a green baseline on the slice branch. `--integration claude` given to `generate` is not carried to a
later bare `./init`, which picks another non-interactively, so name it again:

```sh
./init --integration claude --extension ux-gates
npm install
mkdir -p apps/web/screens
printf '<!doctype html><link rel="stylesheet" href="../src/styles/tokens.css"><button type="button">Go</button>\n' > apps/web/screens/home.html
printf '<!doctype html><link rel="stylesheet" href="plain.css"><button type="button">Go</button>\n' > 'apps/web/screens/plain page.html'
printf '.p {\n  color: var(--ink);\n}\n' > apps/web/screens/plain.css    # as the web app's formatter writes it
git add -A && git commit -qm 'previews, and the lockfile npm install rewrote'
git switch -c slice/S1
make verify    # green; run it again until it ends without `this pass was not recorded`
```

The first green pass on a fresh checkout is usually not recorded: a check writes a file git ignores while it runs,
and the line says so. The second records it, and that pass is the baseline the scoped gate compares with.

Committing on `main` keeps the previews and the rewritten `package-lock.json` (which is in `check-ux-gates`'
every-preview set) out of the slice's own changes. The render gates need Playwright: where the kit cannot resolve it
(`tools/ux-gates/` is ignored and installs no browser here), its render gates say `SKIPPED, not passed` and only the
scope lines below can be read. To render, make a Playwright whose release matches a Chromium already in
`~/.cache/ms-playwright` resolvable from `tools/ux-gates/node_modules/` (a link there is ignored, so it moves nothing
the baseline sees), and take the baseline after that.

## 3. SC-009 on a slice branch (AC-S07-1)

On `slice/S1` with that baseline, edit `apps/service/src/<file>` and run `make verify-scoped`. Expected: `skip
check-agents — none of its inputs changed`, and the same for `check-speckit`, `check-extensions`, `check-constitution`
and `check-ux-gates`. Edit `apps/web/src/<file>` instead: `run  check-ux-gates — apps/web/src/<file> changed`, and the
check's own line naming the commit on `main` the branch is built on, its file gate, and no preview rendered.

## 4. The default and its way back (AC-S07-11)

With step 2 done:

- on `main`: `make check-ux-gates` prints `check-ux-gates: every preview in scope — this is the trunk (`main`)`;
- on `slice/S1`: `… — previews scoped to what changed since <short> (the commit on `main` this branch is built on);
  UX_GATES_SINCE=all renders every preview`;
- `UX_GATES_SINCE=all make check-ux-gates`: `check-ux-gates: UX_GATES_SINCE=all — every preview in scope`;
- `CI=1 make check-ux-gates` on `slice/S1`: `… every preview in scope — CI is set, so this is a CI run`;
- with `main` deleted (`m=$(git rev-parse main); git branch -D main`): `… every preview in scope — no usable base:
  slice/S1 has no `main` to compare with, …`, the reason said once; `make verify-scoped` says the same after `the full
  gate runs, as `make verify` —`. Put it back with `git branch main "$m"`;
- a file git ignores edited by hand (a projected `.claude/skills/<name>/SKILL.md`): `make verify-scoped` runs the full
  gate (`a file git ignores differs from the baseline`) and then `you may have edited one, or a check written one; …`.

## 5. Tests that hold it

After the host releases the machine, only the touched modules:

```sh
make test TESTS="test_verify_scoped_methods test_verify_scoped_derived test_verify_scoped_held test_verify_scoped_table_held test_verify_scoped_record test_ux_gates_default test_ux_gates_scale"
make test TESTS="test_verify_scoped_choose test_verify_scoped_borders test_verify_scoped_ignored test_verify_scoped_baseline test_scoped_targets"
make test TESTS="test_verify_scoped_symlinks test_verify_scoped_since_root test_ux_gates_borders"
make test TESTS="test_toolkit test_utf8_io test_changelog test_assets_bytecode test_verify_stamp_scan"
```
