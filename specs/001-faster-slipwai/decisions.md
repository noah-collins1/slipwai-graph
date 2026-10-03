# Decisions — 001-faster-slipwai

## D1 — How does this repository integrate today? (Integration row `unrecorded`, rung `unknown`)
- **Stage:** ground · **Slice:** none (feature-level) · **When:** 2026-10-03T01:47:02Z · **Iteration:** 1
- **Question:** The Ground stage asks a person to place the Integration row before a slice that changes how slices merge and how `main` moves (FR-010). Nobody is at the wheel. What does the run assume about how work reaches `main` here today?
- **Options:** (a) stop and wait for a person; (b) mark the row `confirmed` from the tree — not available, a fact about the world is not a decision (cruise.md stop 11); (c) leave the row exactly as it is and work on a stated assumption drawn from the tree — recommended by cruise.md stop 11.
- **Decision:** (c). The Integration row stays `unrecorded` at `unknown` in `project.json` and `delivery/docs/convergence.md`. The run works on this assumption, named as one: changes reach `main` through short topic-branch pull requests (`fix/…`, `feat/…`, `docs/…`) merged with a merge commit after CI has run on the pull request; `main` is pushed to directly only by `make release`, whose Release and Open commits and `v*` tag land in one atomic push; `verify.yml` and `verify-delivery.yml` run on every pull request and on every push to `main` on this forge. That is the ladder's `branches` rung with CI on every commit — not `trunk`, because branch lifetime is unmeasured, and not `continuous`, because whether a red build stops the line depends on forge settings (branch protection, required checks) the tree cannot show. FR-010's fast-forward-only `main` is something this feature builds for the merge tree generated projects run, reaching this repository through `slipwai migrate`; the run does not assume it already holds here.
- **Why:** `AGENTS.md` *Versioning*: `main` carries the next release as a `.dev` snapshot and every green push publishes it; *Delivery method*: one pull request per slice. `project.json` `ci`: forge `github`, branch `main`, gate `.github/workflows/verify-delivery.yml`, provenance `overridden`. `.github/workflows/verify.yml` lines 8–18: triggers are `push` to `main`, `v*` tags and `pull_request`, and its `concurrency` block never cancels a `main` run. `.github/workflows/verify-delivery.yml`: `push` to `main` and `pull_request`, running `make -f delivery/Makefile verify`. `git log --first-parent main`: 28 of the last 30 first-parent commits are `Merge pull request … into main`; the other two are `Release 1.5.1` and `Open 1.5.2.dev0`. Also seen and left alone: `verify.yml` and `publish-package.yml` name `https://git.treyco.dev` as the canonical forge and GitHub as a mirror; `ci.forge` is a person's `overridden` value and is not touched by this entry.
- **Decided by:** drive-bosun
- **Confidence:** medium · **Would reverse if:** a person places the Integration row through `/ground` — the rung, whether required checks protect `main`, and the measured branch lifetime — or says they cannot place it today.
- **Written to:** `specs/001-faster-slipwai/decisions.md`
- **Status:** standing

## D2 — Is the test suite green and trusted? (Safety net `detected` at `tests-exist`)
- **Stage:** ground · **Slice:** none (feature-level) · **When:** 2026-10-03T01:47:02Z · **Iteration:** 1
- **Question:** The row is the tree's reading and nobody's answer. What does the run assume about the suite it changes code beside?
- **Options:** (a) stop and ask; (b) mark the row `confirmed` or raise it to `tests-pass` from CI history — not available, the rung is a person's to place; (c) work on the detected value as a stated assumption — recommended by cruise.md stop 11.
- **Decision:** (c). The row stays `detected` at `tests-exist`. The run works on this assumption: `make test` is the recorded test command and runs the unittest suite (829 tests, per the constitution's note under principle V); whether it is green in the gate with no quarantine is not claimed. Every slice therefore establishes green on its own tree through `make -f delivery/Makefile verify` before it pushes, as principle V requires, and no test is quarantined, skipped or moved to get there.
- **Why:** `project.json` `deployables.slipwai-graph.commands.test` is `make test`, provenance `confirmed`; the row's evidence is `test recorded for slipwai-graph`. `verify.yml` runs `make verify`, tests included, on every pull request and `main` push — which suggests `tests-pass`, but the ladder says that rung is established by a person reading the gate, not inferred by the run.
- **Decided by:** drive-bosun
- **Confidence:** high · **Would reverse if:** a person confirms the row at `tests-exist`, raises it to `tests-pass` having read the gate, or overrides it with a quarantine the run must respect.
- **Written to:** `specs/001-faster-slipwai/decisions.md`
- **Status:** standing

## D3 — What is this repository, structurally? (Structure `detected` at `named`)
- **Stage:** ground · **Slice:** none (feature-level) · **When:** 2026-10-03T01:47:02Z · **Iteration:** 1
- **Question:** The row is the tree's reading and nobody's answer. What layout does the run work within?
- **Options:** (a) stop and ask; (b) mark the row `confirmed` — not available; (c) work on the detected value as a stated assumption — recommended by cruise.md stop 11.
- **Decision:** (c). The row stays `detected` at `named`. The run works on this assumption: `slipwai-graph` is one deployable of kind `tool` at `.`, and slices keep its layout — `src/slipwai/`, `assets/`, `delivery/`, `tests/` — within `make check-structure`'s import direction and per-module budgets. No slice in this feature moves the tool under `apps/` or opens a ports-and-adapters split: the constitution says none is planned under principles IV and XV. Changes to what the factory generates land under `assets/` and `src/slipwai/project/` first (owner brief, priority 3) and reach this repository through `slipwai migrate`.
- **Why:** `project.json` `deployables.slipwai-graph`: `kind: tool` and `purpose` both `confirmed`, `path: "."`; the row's evidence is `slipwai-graph: tool; not under apps/: .`; `.specify/memory/constitution.md` principle IV: *no slice is planned for it in Faster Slipwai*; principle XV and the typing constraint say the same of `typed`.
- **Decided by:** drive-bosun
- **Confidence:** high · **Would reverse if:** a person confirms or overrides the row, or asks for a `laid-out` or `hexagonal` slice on the map's Structure row.
- **Written to:** `specs/001-faster-slipwai/decisions.md`
- **Status:** standing

## D4 — What does this repository run on? (Platform `detected` at `supported`)
- **Stage:** ground · **Slice:** none (feature-level) · **When:** 2026-10-03T01:47:02Z · **Iteration:** 1
- **Question:** The row is the tree's reading and nobody's answer. What runtime floor does the run hold itself to, and does it add the missing `audit` command?
- **Options:** (a) stop and ask; (b) mark the row `confirmed` — not available; (c) work on the detected value as a stated assumption and leave the `tooling` step to its own slice — recommended by cruise.md stop 11 and the programme's pacing.
- **Decision:** (c). The row stays `detected` at `supported`. The run works on this assumption: Python 3.11 is the floor, in support on 2026-10-02, and every change keeps running there; Node, Go and a JDK are present only to exercise the generated starters. No `audit` command is recorded, and this entry records none: the programme's `tooling` step (`pip-audit`) is one tool, one slice, over time, green through the ratchet before it is written into `project.json`, and nothing here runs it uninvited.
- **Why:** `pyproject.toml` line 16: `requires-python = ">=3.11"`; `.github/workflows/verify-delivery.yml` sets up Python 3.11; the constitution's *Technology Stack* names 3.11 or newer with 3.14 on the maintainer machine; the row's evidence is `in support on 2026-10-02: Python 3.11; no audit command recorded for slipwai-graph`; `project.json` `strategy.programme` last row, kind `tooling`, evidence `commands.audit: null`.
- **Decided by:** drive-bosun
- **Confidence:** high · **Would reverse if:** a person confirms or overrides the row, names a different floor, or records an `audit` command after its slice is green.
- **Written to:** `specs/001-faster-slipwai/decisions.md`
- **Status:** standing

## D5 — Which change strategy does the run proceed on? (Strategy `recommended: leave-it`, nothing decided)
- **Stage:** ground · **Slice:** none (feature-level) · **When:** 2026-10-03T01:47:02Z · **Iteration:** 1
- **Question:** The map recommends `leave-it` and says the decision is a person's, written as an accepted ADR. Nobody is at the wheel, and the owner brief lists accepting that ADR under *Always ask a person*.
- **Options:** `leave-it` (recommended by the survey); `in-place`; `modular-monolith`; `strangler-fig`; `rewrite` (never recommended here). Then: (a) stop and ask; (b) write the ADR as `Accepted` — not available, the word is a person's; (c) draft the ADR at `Proposed` and proceed on the recommendation — recommended by cruise.md stop 12.
- **Decision:** (c). `delivery/docs/adr/0002-change-strategy.md` is written in Nygard's five sections at Status `Proposed`, carrying the one line `Strategy: leave-it`. The run proceeds on that recommendation: no capability moves, no routing seam, no retirement ledger, no rewrite; the feature's work is delivery slices landing first in what the factory generates. The Strategy row stays `recommended`, provenance `detected`; `/survey` will not read the ADR as a decision until a person changes its Status.
- **Why:** The trigger — a faster delivery loop with its gates intact — names no platform, delivery, change, capability or host problem for an architectural strategy to answer (`project.json` `strategy.because`); the constitution plans no structural slice in this feature (IV, XV); the owner brief rules out any MAJOR change and replacing the harness or the ladder. `src/slipwai/strategy.py` reads a strategy only from an ADR whose `## Status` is `Accepted`, so a `Proposed` draft changes no record.
- **Decided by:** drive-bosun
- **Confidence:** high · **Would reverse if:** a person accepts the ADR (the row then moves to `decided` and, with no ledger to empty, `done`), or chooses another strategy in a superseding ADR.
- **Written to:** `specs/001-faster-slipwai/decisions.md`, `delivery/docs/adr/0002-change-strategy.md`
- **Status:** standing

## D6 — Do the programme's quick wins come first? (four "connection string with a password" hits, seven "no lockfile" hits)
- **Stage:** ground · **Slice:** none (feature-level) · **When:** 2026-10-03T01:47:02Z · **Iteration:** 1
- **Question:** The ladder says a secret in the tree is a slice of its own, first, whatever else is planned, and the programme lists eleven `quick-win` rows. Is any of the four flagged lines a credential, and are the seven missing lockfiles a step this run takes ahead of the feature?
- **Options:** (a) open a secret-rotation slice first, as the pacing says; (b) read each flagged line and decide from what is written there — recommended by this stop's brief; (c) commit a lockfile beside each of the seven `package.json`; (d) take none; (e) take the one the feature already owns, inside its own slice.
- **Decision:** (b) for the secrets, then (d) for them: none of the four hits is a credential, so no rotation, no purge of history and no secret slice. (e) for the lockfiles: six of the seven sit where a lockfile beside the file would be wrong or where the factory keeps it elsewhere; the seventh — the event-model tooling — is FR-003's own deliverable (`check-drawio` skips `npm install` when the installed tree matches a committed lockfile) and is taken inside the User Story 1 slice that owns it, not as a quick win ahead of it. Nothing in the tree is rotated, purged, rewritten or committed by this entry; the programme rows stay as `/survey` derived them, and the detector that raised them (`src/slipwai/quick_wins.py`, `SHAPES`) is left as it is — teaching it the placeholder rule it already applies to keyed literals is product work for the host to plan, not a workaround for this stop.
- **Why:** Each line, read in place:
  - `assets/backing-services/java/database_url.java:10` — a Javadoc comment: `{@code postgres://user:pass@host:port/db}`, the documented shape of `DATABASE_URL` with every part a placeholder word. Not a secret.
  - `assets/backing-services/java/tests/database_url_test.java:19` — `DatabaseUrl.parse("postgres://app:secret@localhost:5433/app")`, the fixture a parser test splits into JDBC URL, username and password; the host is `localhost` and the password is the word `secret`. Not a secret.
  - `tests/test_release.py:299` — `module.web_url("https://someone:a-token@git.example/owner/slipwai.git")`, a fixture proving `web_url` strips credentials from a remote URL; `.example` is a reserved name. Not a secret.
  - `tests/test_upgrade.py:187` — the first line of a test docstring: `pip --index-url https://user:token@forge/...`, illustrating the case the test covers; the test's own value is `someone:a-token` against its local test server. Not a secret.
  - The detector matches the shape `scheme://user:pass@host` without the placeholder test it applies to keyed literals, which is why four placeholders read as secrets.
  - `assets/frontends/react-vite/api-client/package.json` and `assets/frontends/react-vite/app/package.json` — templates the generator merges per variant; the lockfile a project gets is written from `assets/frontends/react-vite/locks/<variant>.json` (`src/slipwai/project/frontend.py:172`, `:223`), ten committed variants. A lock beside the template would be a copy nothing reads. Not a step.
  - `assets/languages/typescript/app/package.json` — the same pattern: four committed locks under `assets/languages/typescript/locks/`. Not a step.
  - `assets/toolkit/scripts/event-model/package.json` — exact pins (`yaml` 2.9.0, `zod` 4.4.3, `tsx` 4.23.12), installed by `make model` in a generated project; no lockfile is committed for it anywhere, and `src/slipwai/ecosystems.py:89` chooses `npm ci` only when one is present. Real, and owned by FR-003 of this feature: taken in User Story 1's slice.
  - `tests/fixtures/adopt/converging/apps/shop/package.json`, `tests/fixtures/adopt/javascript-gitlab/package.json`, `tests/fixtures/adopt/javascript-service/package.json` — checked-in fixture repositories for the adopt tests; `tests/test_adopt.py:59` says a lockfile-less JavaScript service is deliberate so an install needs no registry, and `tests/test_quick_wins.py:69` asserts that the `no-lockfile` finding is raised. A lock here would change what the tests prove. Not a step.
  - The pacing text on the seven lockfile rows reads *a secret in the tree today*, which is the quick-win pacing shared across kinds, not a claim about those files.
- **Decided by:** drive-bosun
- **Confidence:** high · **Would reverse if:** a person reads one of the four lines and says it is a live credential, or wants the event-model lockfile taken as a slice of its own ahead of User Story 1.
- **Written to:** `specs/001-faster-slipwai/decisions.md`
- **Status:** standing

## D7 — What is every slice's release constraint under `release: flagged`?
- **Stage:** split · **Slice:** none (feature-level) · **When:** 2026-10-03T01:52:46Z · **Iteration:** 1
- **Question:** The release-constraint stage asks what hides a merged slice from a real actor until a person says it ships. Here the product is a factory: a merge to `main` publishes a `1.5.2.dev<N>` snapshot and a generated project only changes when its maintainer runs `slipwai migrate`. What constraint does every slice in the split carry?
- **Options:** (a) a feature flag per slice inside the generated toolkit — recommended against by the stage, since nothing here runs in production and a flag would be a new setting with no reader; (b) the standing one: the change lands on `main` as a pre-release snapshot no installer takes unasked, reaches a project only through `slipwai migrate` run by its maintainer, and becomes a release only through `make release`, which this run never runs — recommended by the stage, as the smallest constraint that already holds; (c) park at the first push.
- **Decision:** (b). Every slice's *Release Constraint* column in `story-split.md` says so; a slice that adds a setting ships it with a documented default (owner brief, *Taste*) and the run never flips one. `make release`, a `v*` tag and raising `VERSION` to a MAJOR stay a person's.
- **Why:** `AGENTS.md` *Versioning*: a `.dev` version is a pre-release every installer passes over unless asked, and `make release` is the only thing that writes a release. The owner brief's *Out of scope* rules out switching routing on and any MAJOR; the cruise rule *Flags stay off* is satisfied by the snapshot's own semantics.
- **Decided by:** host (stage recommendation)
- **Confidence:** high · **Would reverse if:** a person asks for a snapshot to be held back from `main` as well, in which case slices accumulate on a long-lived branch and the constraint becomes that branch.
- **Written to:** `specs/001-faster-slipwai/story-split.md`
- **Status:** standing

## D8 — Where do the method slices and the unplanned map rows go in the split?
- **Stage:** split · **Slice:** none (feature-level) · **When:** 2026-10-03T01:52:46Z · **Iteration:** 1
- **Question:** The ladder offers the programme top-first and then the lowest map row still below target; the split places method slices among the product slices, never ahead of all of them by default, a secret and an open CRITICAL excepted. D6 found no secret. What is placed, and where?
- **Options:** (a) one method slice per row below target, ahead of the product (safety net, structure, platform, constitution, integration, strategy) — against the split's rule and the owner's priority 3; (b) only the step a product slice waits on, first, and the programme's one cheap tooling step, last — recommended by the stage; (c) no method slices at all — refused by the Pin stage, which will not take a slice while `running.md` reads *Not yet proven*.
- **Decision:** (b). `S00-run-path` goes first: it proves the recorded `smoke`, writes `delivery/survey/running.md`, and claims `safety-net: tests-exist → tests-pass` from a green gate, because every product slice changes code that was here and the Pin stage refuses them until then. `S19-pip-audit` (`platform: supported → audited`) goes last, taken earlier only when a fan-out has a free seat. Structure (`named → laid-out`), the rest of the safety-net ladder, and the Constitution row are not planned in this run; the Parking Lot in `story-split.md` says why for each.
- **Why:** owner brief, priority 3 (the generated project's loop over the factory's own convenience) and *Out of scope* (this repository's own suite beyond what the general changes give it); `delivery/commands/drive.md` stage 7 (the application has to start before any pin) and stage 9 (a method slice is placed by the split, never ahead of all product slices by default); `project.json` `strategy.programme` has one step left after D6, the `audit` command.
- **Decided by:** host (stage recommendation)
- **Confidence:** high · **Would reverse if:** a person asks for a map row to move in this run, or an open CRITICAL appears in `adversary-log.md`, which pre-empts every slice.
- **Written to:** `specs/001-faster-slipwai/story-split.md`
- **Status:** standing

## D9 — Does this repository take each change through `slipwai migrate` inside the run (E8)?
- **Stage:** split · **Slice:** none (feature-level) · **When:** 2026-10-03T01:52:46Z · **Iteration:** 1
- **Question:** The spec's *Assumptions* say the factory's own repository takes these changes through `slipwai migrate` after each lands, so the run speeds up as it goes. Can an iteration do that?
- **Options:** (a) run `./slipwai migrate` here after each slice merges — it rewrites files under `delivery/scripts/`, which the runner treats as a changed control and parks the run on, whatever the last line said; (b) leave E8 to a person between runs, and let this repository's loop run the gate it has today — recommended, as the only option that does not park; (c) exempt migrate from the control check — changing the gate, on the catastrophic list.
- **Decision:** (b). No iteration runs `slipwai migrate` on this repository. The split's Parking Lot names E8 as a person's step; the cruise report will list it as the first thing to do when the run ends.
- **Why:** `delivery/commands/cruise.md`, *A failing gate is never repaired in the gate*: the runner compares `delivery/scripts/`, `tools/`, the `Makefile`, CI and hook settings before and after every iteration and parks on any change; `delivery/.written` lists the files migrate replaces, and `delivery/scripts/` is among them.
- **Decided by:** host (stage recommendation)
- **Confidence:** high · **Would reverse if:** a person runs the migrate themselves between iterations, or the factory learns to migrate without touching a control the runner watches.
- **Written to:** `specs/001-faster-slipwai/story-split.md`
- **Status:** standing

## D10 — Does `model.yaml` stay one file with a sidecar index, or split per slice?
- **Stage:** split · **Slice:** S12-model-sidecar (named ahead) · **When:** 2026-10-03T01:52:46Z · **Iteration:** 1
- **Question:** FR-014 leaves it open: the model MAY be a single file with a sidecar index or split per slice (the PRD's owner decision 3). Which does the split plan for?
- **Options:** (a) split `model.yaml` per slice — the owner brief lists it under *Always ask a person*, so not available to this run; (b) one file plus a generated sidecar index every consumer reads — the only option open to the run, and the one FR-005 already needs.
- **Decision:** (b). `S12-model-sidecar` builds the sidecar; the per-slice split is not planned and is asked of a person if a later slice finds the sidecar insufficient.
- **Why:** `.specify/product-owner.md`, *Always ask a person*, last item; `spec.md` FR-005 and FR-014.
- **Decided by:** host (stage recommendation)
- **Confidence:** high · **Would reverse if:** a person decides for per-slice files, which would then be a MINOR with a `migrate` catch-up note.
- **Written to:** `specs/001-faster-slipwai/story-split.md`
- **Status:** standing
