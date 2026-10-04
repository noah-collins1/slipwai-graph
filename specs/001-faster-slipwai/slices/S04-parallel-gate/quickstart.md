# Quickstart: S04-parallel-gate — what the demo follows

The actor is a developer with a generated project. Everything runs from this checkout's `./slipwai` (the one on
`PATH` is an old release) into a temporary directory, with no CI marker set (`env -u CI -u GITHUB_ACTIONS -u
GITLAB_CI`). Seed data: none.

## 1. The gate in parallel (AC-S04-2 to -9, -13)

```sh
T=$(mktemp -d)
./slipwai generate shop --profile event-modelling --backend python --output "$T" --no-init --no-install --skip-checks
cd "$T/shop" && make install
make verify            # one check after another; ends `verify: all gates passed`
make -j verify         # the same checks, together; the same last line
```

Expect: both exit 0; under `-j` every check's lines stay together; `uv sync` is echoed once, before the checks.
Break one check (add an unused import to a file under `apps/service/src`) and run `make -j verify`: non-zero, no
closing line, a `***` line naming `lint`, and the gate's own last line beginning `verify:` that says where to look.

## 2. One sync, and a mode on its own (AC-S04-28 to -33)

`make lint` alone echoes the sync once, then lints. `./scripts/verify --lint-only` typed directly still syncs.

## 3. The model tooling (AC-S04-45 to -54)

`git status --porcelain` is empty after the first gate: no untracked lock. `make check-drawio` a second time
prints `check-drawio: the model tooling matches scripts/event-model/package-lock.json; not reinstalled` and runs no
npm command. `touch scripts/event-model/package.json && make check-drawio` runs `npm ci` and does not print it.
On a branch (`git checkout -b work`), the first `make verify` that passes is recorded and the second prints the
reuse line.

## 4. The measurement (AC-S04-22, -23)

On AC-S03-20's project — `./slipwai generate timed --backend python --frontend none --target none …` — warm, on a
branch other than the trunk:

```sh
for i in 1 2 3; do /usr/bin/time -f '%e' make verify VERIFY_FORCE=1 >/dev/null; done
for i in 1 2 3; do /usr/bin/time -f '%e' make -j verify VERIFY_FORCE=1 >/dev/null; done
```

The median under `-j` is lower than the serial median, or the demo failed. *Measured:* written here at the demo
with the machine and its core count.

## 5. The other families (AC-S04-15, -17)

One starter each for Go, TypeScript and Java (Quarkus), fresh, real toolchain: `make install && make -j verify`
passes with its serial run's checks.

## 6. An adopted repository (AC-S04-24 to -27)

`./slipwai adopt` on a small repository with recorded `lint`, `typecheck` and `test`: its Makefile carries a bare
`.NOTPARALLEL:` and `make -j verify` runs the three one after another.

## 7. A project that exists (AC-S04-56 to -60)

A project generated at the commit before this slice, its first gate run (so an untracked lock is there): `slipwai
migrate` refuses and names the uncommitted change; with the file deleted, as the fragment's catch-up says, it
merges, the lock arrives, and `make check-drawio` passes.
