# Data model: S08-scoped-mutation

Nothing is persisted. These are the shapes the scope script computes in one run and the words it prints; the
words are the contract a person and `/mutation` read (AC-S08-12), so they are fixed here.

## The invocation

The generated `mutation` recipe is one line:

```make
mutation: ## Run native mutation testing, or explain the missing project decision
	@python3 scripts/mutation-scope.py --make "$(MAKE)" --makefile "$(firstword $(MAKEFILE_LIST))" <backend>:<path> …
```

one `<backend>:<path>` per generated service in service order (`go:apps/service go:apps/billing`), and
`mutation-full` carries today's merged recipe, byte for byte (AC-S08-11). `SINCE` is read from the environment
(research R5).

## Service

| Field | Meaning |
|---|---|
| `backend` | `go`, `java-spring`, `java-quarkus`, `typescript` or `python` — from the argument |
| `path` | the service directory, relative to the project root |
| `wired` | `go` and `java-spring`; every other backend is a placeholder (D137) |

## Change set

What changed, as `{path: status}` (`A`, `M`, `D`), from one of two bases:

| Base | When | Read by |
|---|---|---|
| the merge-base | no `SINCE`, and no border holds (D117 rule 1) | `check-slice-scope.changed_files(base)`, via `verify-scoped`'s `Ground` |
| `SINCE`'s commit | `SINCE` is set and non-empty, on any checkout | the same `changed_files`, after `git rev-parse --verify <ref>^{commit}` |

An unresolvable `SINCE` fails, status 2, naming the ref. `SINCE=` (empty) is the sweep.

## Classification of each changed path

Evaluated in this order; the first that holds wins.

| Class | Rule | Effect |
|---|---|---|
| `rule-text` | `Makefile`'s `mutation` rule (target line and recipe lines) differs from the base's | the whole run sweeps |
| `scope-script` | `scripts/mutation-scope.py` | the whole run sweeps |
| `backend-script` | `scripts/go-mutation.py` | every Go service sweeps |
| `config` | a service's `.gremlins.yaml` (any status); its `pom.xml` whose `pitest-maven` plugin element differs as parsed structure, or cannot be parsed on either side | that service sweeps |
| `shared` | under `packages/` | named *not mutated by this target*, nothing runs for it |
| `deleted` | status `D` | named *deleted, no mutants*, when it was a production file |
| `test` | a service's test file (research R9) | collected for the *only tests changed* line |
| `production` | a service's production file (research R9) | that service's scope |
| `other` | anything else | counted, never named one by one |

For a wired service, a production file is then intersected with the tool's own configuration (D138 item 1):
Go through `go-mutation.py`'s `excluded()`/`mutable()`, Spring through `targetClasses`/`excludedClasses` (research
R2). A file the configuration excludes is named *outside <tool>'s configured targets*.

## Service outcome

| Outcome | When | Run |
|---|---|---|
| `scoped` | wired, at least one mutable production file | Go: `go-mutation.py <path> --file …`; Spring: the sweep command plus `-DtargetClasses=<Foo>,<Foo$*>,…` |
| `swept` | `config` or `backend-script` names it | the service's sweep command |
| `skipped` | nothing to mutate in it | none |
| `refused` | placeholder with a changed production file | none; status 2 |

The whole run sweeps (`$(MAKE) --no-print-directory -f <makefile> mutation-full`, its status the run's) when a
border holds, `SINCE` is empty, `layout.delivery` is set, or a `rule-text`/`scope-script` change exists.

## The words

Every line starts `mutation: `. The first line is exactly one of:

- `mutation: scoped to <n> changed file(s) since <base>: <file>, <file>, …` — `<base>` is `` `<trunk>` at <short> ``
  for the merge-base, `` `<ref>` `` for `SINCE`
- `mutation: the sweep runs — <reason>` — a border's own words (verify-scoped's), `SINCE is set and empty`,
  `` `<file>` changed `` for a whole-run sweep
  — this form also opens a run where no service is scoped and only some services sweep for a configuration change;
  the per-service lines below it say which swept and which were skipped (settled by the host at implementation)
- `mutation: no mutant to run — <why>` — `only tests changed: <files>; \`make mutation-full\` is the run that
  measures them` · `no production file changed` · `every changed production file is outside the tools' targets`
- `mutation: this layout has no mutation scope — the recorded command runs` (adopted layout only)

Then each service once, in service order:

- `mutation: scope <path> — <file>, …`
- `mutation: sweep <path> — \`<file>\` changed`
- `mutation: skip <path> — no changed production file`
- `mutation: refuse <path> — <the placeholder's setup message>; the scope will apply once a tool is wired; it
  would mutate: <file>, …`

Each changed production file that is not mutated, once: `mutation: not mutated <file> — <reason>`.

The last line: `mutation: <a> scoped, <b> swept, <c> skipped, <d> refused; passed` or `…; failed: <path>, …`.
A failing or refusing service fails the run, after every service has run; the status is the first non-zero one
in service order.

A Spring scoped run that PIT finds nothing to mutate in prints `mutation: no mutant to run in <path> — PIT found
no code to mutate in <classes>; no report was written` and counts as passed (research R3).
