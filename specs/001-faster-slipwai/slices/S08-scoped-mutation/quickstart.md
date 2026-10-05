# Quickstart: S08-scoped-mutation

How to see the slice work, by hand, in a project this worktree generates. Words are data-model's; nothing here
is a test the suite does not already hold.

## Prerequisites

Go 1.25+, a JDK, `git`, network for the first Gremlins and Maven fetch. Unset `CI`, `GITHUB_ACTIONS`,
`GITLAB_CI` (each makes the bare target the sweep).

```sh
./slipwai generate demo-go --backend go --output /tmp/s08/demo --no-init --no-install --skip-checks
cd /tmp/s08/demo/demo-go && slipwai add-service billing --backend go && git add -A && git commit -qm billing
```

(and `--backend java-spring` for the Spring starter).

## Scenarios

1. **Trunk sweeps.** On `main`: `make mutation` → `mutation: the sweep runs — this is the trunk (\`main\`)`, then
   both services' Gremlins runs; the status is theirs.
2. **One file, one service.** `git switch -c slice/demo`, edit `apps/service/health/health.go`; `make mutation` →
   `scoped to 1 changed file(s) since \`main\` at <sha>: apps/service/health/health.go`, `scope apps/service — …`,
   `skip apps/billing — no changed production file`, and a last line `1 scoped, 0 swept, 1 skipped, 0 refused; passed`.
3. **Tests only.** Revert, edit `apps/service/health/health_test.go` → `no mutant to run — only tests changed: …`, exit 0.
4. **Config sweeps.** Edit `apps/billing/.gremlins.yaml` → `sweep apps/billing — \`apps/billing/.gremlins.yaml\` changed`.
5. **`SINCE` anywhere.** Before `add-service` (which rewrites the `mutation` rule, and a changed rule sweeps), `make mutation SINCE=HEAD~1` on `main` scopes; `make mutation SINCE=nope` fails naming `nope`;
   `make mutation SINCE=` sweeps.
6. **Spring.** On a slice branch, edit a class under a `targetClasses` package (`health/HealthStatus.java`) → PIT
   mutates `HealthStatus` and `HealthStatus$*` only; edit an adapter outside it → named, Maven not started, exit 0.
7. **The sweep is still there.** `make mutation-full` on any branch runs today's recipe.

## Demo measurement (AC-S08-19 — filled at the demo, not before)

| Starter | Command | Wall | Mutants | Machine |
|---|---|---|---|---|
| two-service Go, one file changed | `make mutation` | | | |
| two-service Go | `make mutation-full` | | | |
| Spring, one class changed | `make mutation` | | | |
| Spring | `make mutation-full` | 28.5 s (plan-time baseline, research R10) | 64 | |
