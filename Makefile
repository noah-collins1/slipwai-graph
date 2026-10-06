# The factory's own local and CI entry points. `make verify` is the gate, and it is the same command here
# and in .github/workflows/verify.yml — the rule this factory writes into every project it generates.
.DEFAULT_GOAL := help

.PHONY: help
help: ## Show the available targets
	@grep -hE '^[a-z][a-zA-Z0-9_-]*:.*?## ' $(MAKEFILE_LIST) | awk -F':.*?## ' '{ printf "  %-18s %s\n", $$1, $$2 }'

.PHONY: install
install: ## Install the pinned development tooling into .python-tools
	./scripts/verify --install-only

.PHONY: lint
lint: ## Run ruff over the factory's own source, scripts and tests
	./scripts/verify --lint-only

.PHONY: typecheck
typecheck: ## Byte-compile everything, then type-check it with mypy
	python3 -m compileall -q src scripts tests
	./scripts/verify --typecheck-only

.PHONY: check-structure
check-structure: ## Fail when a module imports against the declared direction, cycles, or outgrows its budget
	python3 scripts/check-structure.py

# The suite, or a slice of it. On a slice branch `make test` runs the modules the change can reach, and says which and
# why (`scripts/select-tests.py`); on the trunk, off a branch, or after a change to this file it runs every module.
# `SINCE=<ref>` names the base it compares against, `FULL=1` runs every module, and `TESTS="test_matrix test_add_service"`
# runs exactly those modules, `SKIP="test_matrix"` every module but those: each of the last two prints `selection off`.
# CI holds the gate in parallel jobs this way. `make verify` always runs every module: it passes `FULL=1` below.
ALL_TESTS := $(patsubst tests/%.py,%,$(wildcard tests/test_*.py))
RUN_TESTS = $(or $(strip $(TESTS)),$(filter-out $(SKIP),$(ALL_TESTS)))
.PHONY: test
test: ## Run the modules this slice branch can reach (SINCE=<ref>, FULL=1 for all), or TESTS="test_a test_b" / SKIP="test_a"
	$(if $(strip $(TESTS)$(SKIP)),echo 'selection off: $(if $(strip $(TESTS)),TESTS,SKIP) given$(if $(RUN_TESTS),, - no module runs)'$(if $(RUN_TESTS),; PYTHONPATH=src:tests python3 -m unittest -v $(RUN_TESTS)),PYTHONPATH=src python3 -B scripts/select-tests.py)

# A tree that already passed is not judged again: the verify stamp every generated project carries answers first, from
# where it ships, so the factory's own gate is the one it generates. The four checks are `verify-checks`; CI never reads
# a stamp, because the script stands down under a CI marker and on the trunk. A slice of the suite (`TESTS`, `SKIP`)
# is not the gate, and nor is `FACTORY_BACKENDS`, which cuts the backend matrix: neither asks the script, so nothing reads,
# writes or removes a stamp for a run that skipped checks. Every variable that narrows what the suite runs belongs here.
# The key also holds what each tool the suite looks for answers to `--version`, since a test skips when its tool is
# missing and a tool appearing or changing can change what the suite does. Only a tool this machine has is asked: the
# script cannot ask a missing one, and would then record nothing. The Docker Compose plugin answers to `docker compose
# version`, which the script cannot ask, so the recipe writes that answer (or `absent`) to the ignored `.factory-work/verify-probes`,
# which the key reads like any ignored file. The recipe stops, in one line, where `.factory-work` is a symbolic link or not
# a directory (the key would read the link, not what is behind it) or the probe file cannot be written (it would be stale). The line holds `$(MAKE)`, so `make -n verify` and `make -q verify` write that
# file too: harmless, an ignored file with its true answer, and no stamp is touched. The paths of interpreter caches
# under `assets/` follow it, because the suite reads them as text and the stamp exempts them; their contents are not
# keyed (D119). Where they cannot be listed (no `sort`, or `find` exits non-zero part-way), the line is unique to the run, so nothing is reused. `make` itself is
# always there, under the name it was run as.
VERIFY_STAMP_SCRIPT := assets/toolkit/scripts/verify-stamp.py
VERIFY_TOOLS := python3 git uv node npm npx go java docker pack ko mvn tofu gh codegraph
VERIFY_STAMP = --tool make --make "$(MAKE)" $(foreach tool,$(VERIFY_TOOLS),$(if $(shell command -v $(tool) 2>/dev/null),--tool $(tool)))
.PHONY: verify
verify: ## Full local gate — a tree that already passed is not judged again; VERIFY_FORCE=1 runs it anyway
ifneq ($(strip $(TESTS)$(SKIP)$(FACTORY_BACKENDS)),)
	@"$(MAKE)" --no-print-directory -f "$(firstword $(MAKEFILE_LIST))" verify-checks FULL=1
else
	@if [ -L .factory-work ] || { [ -e .factory-work ] && [ ! -d .factory-work ]; }; then echo 'verify: .factory-work is a symbolic link or not a directory; the stamp cannot key what is behind it - make it a plain directory' >&2; exit 2; fi; { mkdir -p .factory-work && { docker compose version 2>/dev/null || echo absent; { command -v sort >/dev/null && list=$$(find assets \( -name __pycache__ -o -name '*.pyc' -o -name '*.pyo' \) 2>/dev/null) && printf '%s\n' "$$list" | LC_ALL=C sort; } || echo "caches: not listed, run $$$$"; } > .factory-work/verify-probes; } || { echo 'verify: .factory-work/verify-probes could not be written, so the stamp would key a stale answer; the gate stops' >&2; exit 2; }; run=$$(python3 $(VERIFY_STAMP_SCRIPT) token); python3 $(VERIFY_STAMP_SCRIPT) reuse --token "$$run" $(VERIFY_STAMP) || { "$(MAKE)" --no-print-directory -f "$(firstword $(MAKEFILE_LIST))" verify-checks FULL=1 && python3 $(VERIFY_STAMP_SCRIPT) record --token "$$run" $(VERIFY_STAMP); } || { rc=$$?; [ "$$rc" -eq 1 ] || echo 'verify: the gate did not pass; each failed check is named above'; exit "$$rc"; }
endif

.PHONY: verify-checks
# Run directly or through `verify`, the gate is whole: `test` is made by a recipe of its own with `FULL=1`, not as a
# prerequisite, so naming it before this goal (`make test verify-checks`) cannot leave this one with a selected run.
verify-checks: lint typecheck check-structure
	@"$(MAKE)" --no-print-directory -f "$(firstword $(MAKEFILE_LIST))" test FULL=1
	@echo
	@echo 'verify: all gates passed'

.PHONY: changelog
changelog: ## List the commits since the last VERSION bump, for the changelog.d/ fragment they owe
	@python3 scripts/changelog-draft.py $(VERSION)

.PHONY: release
release: ## Turn the snapshot on main into a release: commit, tag v<release>, open the next snapshot, push
	python3 scripts/tag-release.py $(RELEASE_ARGS)

.PHONY: test-migration
test-migration: ## Generate at the last release tag, replay at HEAD, merge, and hold the result to its own gate
	python3 scripts/test-migration.py $(MIGRATION_ARGS)

.PHONY: test-adoption
test-adoption: ## Adopt each fixture repository, re-survey, verify, migrate from a newer factory, verify again (experimental)
	python3 scripts/test-adoption.py $(ADOPTION_ARGS)

.PHONY: starters
starters: ## Materialize every starter combination under build/ for inspection
	python3 scripts/regenerate-starters.py

.PHONY: locks
locks: ## Rebuild every committed dependency lock (needs network)
	python3 scripts/regenerate-locks.py

.PHONY: check-locks
check-locks: ## Report a stale committed lock, changing nothing (needs network)
	python3 scripts/regenerate-locks.py --check

.PHONY: executable
executable: ## Build the standalone slipwai executable
	./scripts/build-executable

.PHONY: test-executable
test-executable: executable ## Build it, then prove it scaffolds with Git alone
	python3 scripts/smoke-executable.py dist/slipwai$(if $(filter Windows_NT,$(OS)),.exe,)

.PHONY: package-executable
package-executable: test-executable ## Build, prove, and package it for release
	python3 scripts/package-executable.py dist/slipwai$(if $(filter Windows_NT,$(OS)),.exe,)

.PHONY: wheel
wheel: ## Build the pip-installable package (wheel and sdist) into dist/
	./scripts/build-wheel

.PHONY: test-wheel
test-wheel: wheel ## Build it, install it into a throwaway venv, then prove it scaffolds with Git alone
	./scripts/smoke-wheel

.PHONY: publish-wheel
publish-wheel: test-wheel ## Build, prove, and upload it: PYPI_URL, PYPI_INDEX and PYPI_USER; PYPI_TOKEN from the environment
	PYTHONPATH=.build-tools/publish python3 scripts/publish-wheel.py --url "$(PYPI_URL)" --index-url "$(PYPI_INDEX)" --user "$(PYPI_USER)"

.PHONY: publish-release
publish-release: ## Attach release/* to a tag's release: FORGE_URL, FORGE_REPO and TAG; GITEA_TOKEN from the environment
	python3 scripts/publish-release.py --api "$(FORGE_URL)/api/v1" --repository "$(FORGE_REPO)" --tag "$(TAG)" release/*
