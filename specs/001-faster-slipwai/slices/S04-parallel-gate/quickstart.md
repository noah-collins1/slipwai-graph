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

Expect: both exit 0; under `-j` every check's lines stay together; the sync (`./scripts/verify --install-only`) is
echoed once, before the first check that runs the service's code.
Break one check (add an unused import to a file under `apps/service/src`) and run `make -j verify`: non-zero, no
closing line, a `***` line naming `lint`, and the gate's own last line beginning `verify:` that says where to look: `verify: the gate did not pass; each failed check is named above on a line carrying ***`.

## 2. One sync, and a mode on its own (AC-S04-28 to -33)

`make lint` alone echoes the sync once, then lints. `./scripts/verify --lint-only` typed directly still syncs.

## 3. The model tooling (AC-S04-45 to -54, -64, -77)

`git status --porcelain` is empty after the first gate: no untracked lock. `make check-drawio` a second time
prints `check-drawio: scripts/event-model/package-lock.json is not newer than the installed model tooling; not reinstalled` and runs no npm command (the line's words since D97; demo 1 saw the earlier wording, *the model tooling matches …*). `touch scripts/event-model/package.json && make check-drawio` runs `npm ci` and does not print it.
On a branch (`git checkout -b work`) of a fresh clone where `make install` has run, the first `make verify` that
passes is recorded and the second prints the reuse line; on a fresh clone where nothing was installed, the first
pass installs as it goes and says it records nothing, the second runs in full and is recorded, the third reuses
(D93). Edit the tooling's manifest to another pinned version (`yaml` 2.8.0), run `npm install --package-lock-only`
in `scripts/event-model`, then `make check-drawio`: it runs `npm ci` and does not print the skip line (D96).

## 4. The measurement (AC-S04-22, -23)

On AC-S03-20's project — `./slipwai generate timed --backend python --frontend none --target none …` — warm, on a
branch other than the trunk:

```sh
for i in 1 2 3; do /usr/bin/time -f '%e' make verify VERIFY_FORCE=1 >/dev/null; done
for i in 1 2 3; do /usr/bin/time -f '%e' make -j verify VERIFY_FORCE=1 >/dev/null; done
```

The median under `-j` is lower than the serial median, or the demo failed. *Measured* at the demo (2026-10-04, cruise iteration 13, `drive-hand`; Linux x86_64, a 12th Gen Intel Core
i5-12400, `nproc` 12, GNU Make 4.4.1; project `timed`, warm, branch `work`, every run exit 0): `make verify
VERIFY_FORCE=1` 3.28 s, 3.28 s, 3.25 s — median 3.28 s; `make -j verify VERIFY_FORCE=1` 1.70 s, 1.72 s, 1.69 s —
median 1.70 s.

## 5. The other families (AC-S04-15, -17)

One starter each for Go, TypeScript and Java (Quarkus), fresh, real toolchain: `make install && make -j verify`
passes with its serial run's checks.

## 6. An adopted repository (AC-S04-24 to -27)

`./slipwai adopt` on a small repository with recorded `lint`, `typecheck` and `test`: its delivery Makefile carries a
bare `.NOTPARALLEL:` inside a conditional, `make -f delivery/Makefile -j verify` runs the three one after another,
and two targets of the repository's own in a root Makefile that includes the delivery one still run together under
`make -j` (D95).

## 7. A project that exists (AC-S04-56 to -60)

A project generated at the commit before this slice, its first gate run (so an untracked lock is there): `slipwai
migrate` refuses, saying the project has uncommitted changes; with the file deleted, as the fragment's catch-up says, it
merges, the lock arrives, and `make check-drawio` passes.

The factory before the slice, for this step: `git archive 3f44288 | tar -x -C <dir>` and that tree's `./slipwai`
(a worktree is not needed). *Run by hand during the slice (D96, G15 and G16):* converge pass 1 migrated a project
generated from that archive — `Makefile`, `docs/gates.md`, the lock and `scripts/verify` arrived as one
fast-forward and `make check-drawio` passed; the trace migrated a repository adopted by that archive's factory —
the lock arrived under `delivery/scripts/event-model/` with its line in `delivery/.written`, and `make -f
delivery/Makefile check-drawio` passed; T009's delegate followed the three lock cases on Python projects from an
archive of the same commit.
