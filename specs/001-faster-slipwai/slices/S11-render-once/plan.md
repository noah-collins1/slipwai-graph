# Implementation Plan: S11-render-once — diagrams draw through one browser, and only when their source changed

**Branch**: `adopt-method` (D12 — no `slice/` branch, no claim, no push) | **Date**: 2026-10-03 |
**Spec**: [spec.md](../../spec.md), *Slice acceptance criteria* → `### S11-render-once` (AC-S11-1 … AC-S11-17)

**Input**: the slice's row in [story-split.md](../../story-split.md) and its criteria in `spec.md`; decisions D7,
D9, D12, D32 (the CI markers), D39, D67, D68, D69 in [decisions.md](../../decisions.md). Written by cruise
iteration 10 (host, strong model). The optional `before_plan` hook (`/characterise`) is taken as the ladder's Pin
stage, after tasks.

## Summary

`make model` starts one browser per diagram — 25 for a model of 16 slices, 15.95 s measured — and redraws every
one on every run after deleting `slices/` and `segments/` wholesale. After this slice the renderer opens at most
one browser session per run, on the first diagram it has to draw, and draws only the diagrams whose SVG cannot be
shown to be current: the hash of the source the model produces now, the key of the renderer that drew it, and a
closing `</svg>` (D68). An SVG reaches its name only by a rename of a finished file; what the model no longer
produces is removed by name; text files are written only when they differ; the closing line says how many
diagrams were drawn and how many were left (D69). Nothing is skipped under a CI marker. A PATCH: no setting, no
flag, no new generated file a project is asked about; `VERSION` stays `1.6.0.dev0`, one fragment.

## The example map (rules the tasks cut on)

Each example is the criterion of the same number in `spec.md` — **e*n* is AC-S11-*n*** — read there, not restated
here. The **fixture project** in every example is a project the factory generates with the event-modelling
profile, its `docs/event-model/model.yaml` written by the test; the **stand-in renderer** is a tree the test
writes at `scripts/event-model/.mermaid-cli/` ([research.md](research.md) item 4) so the real entry point runs
with no browser and no network beyond the `npm install` the event-model tests already make.

### User story 1 — one session, and only what changed (`render.ts`, new `render-plan.ts`, new `render-session.ts`) `[US1]`

| Rule | Criteria | What it says | Examples |
|---|---|---|---|
| **R1** at most one session, opened on the first diagram to draw | AC-S11-1, -4, -14, -16 | One browser for any number of diagrams; none when nothing is drawn; the patch, the Puppeteer config, the width and the root message as today | e1 e4 (first run of the fixture: 1 session, 25 drawn; one-slice model: 1 session, 3 drawn) · e14 (the counts come from the stand-in's log, never from the run's own line) · e16 (the stand-in is launched with the config file's contents; the patcher still runs before the first draw) |
| **R2** a diagram is left only when its SVG is shown current | AC-S11-2, -3, -5, -6, -7 | Source stamp, renderer line, closing tag, no CI marker; the key over installed versions, the drawing scripts and the config | e2 (the fixture's edit: 1 session, 3 drawn, 22 byte-identical) · e3 (an added frame redraws every later slice and segment) · e5 (one example per condition: wrong source hash, no renderer line, wrong key, no closing tag, each CI marker) · e6 (each input of the key changed in turn redraws all) · e7 (`extractHash` on a two-line SVG; the page carries both comments) |
| **R3** a file reaches its name finished, or not at all | AC-S11-8, -9 | Temporary file in an ignored directory beside the output, then rename; a failed draw leaves the earlier file and exits non-zero naming the diagram; the PNG always drawn when asked | e8 (stand-in fails on one diagram: earlier SVG's bytes stand, exit 1, name on stderr, no temporary left for `git status`) · e9 (`PNG=1` twice: drawn twice, same session as the SVGs) |

### User story 2 — what the run leaves and says (`render.ts`, `render-plan.ts`, the page, the docs) `[US2]`

| Rule | Criteria | What it says | Examples |
|---|---|---|---|
| **R4** what the model no longer produces is removed by name, before drawing | AC-S11-11 | Files, directories and leftover temporaries in `segments/` and `slices/`; the empty-model branch as today | e11 (a removed slice, a stray directory, a leftover temporary; then the empty model) |
| **R5** text files are written only when they differ, and the run says what it did | AC-S11-12, -13 | One `wrote` line per file written; the closing line's counts, and *no browser started* | e12 (second run on an unchanged tree: no `wrote` line, no mtime moved) · e13 (the two closing lines, verbatim) |
| **R6** the page, the fragment and the docs say it | AC-S11-10, -17 | One sentence on forcing a redraw; the fragment's two catch-up sentences, PATCH | e10 · e17 (each sentence followed as written) |

AC-S11-15 is the demo's: the hand measures it on the reference fixture with a real browser
([quickstart.md](quickstart.md)).

## Technical Context

**Language/Version**: TypeScript run by `tsx` 4.23.12 on Node (the event-model tooling's own pins); Python 3.11 for the tests
**Primary Dependencies**: none added. mermaid-cli 11.16.0 as pinned today, called through its exported `renderMermaid`; `puppeteer` as that install already carries it ([research.md](research.md) items 1–3)
**Storage**: the SVG files themselves — two comment lines at the head of each; no sidecar (D68)
**Testing**: `unittest` (`make test TESTS=…`), generating a project and running its `make model` against the stand-in renderer
**Target Platform**: wherever a generated project runs `make model`: Linux, macOS, Windows, CI containers
**Project Type**: a generator; the change is to assets a generated project receives
**Performance Goals**: SC-004 — the fixture's warm changed-slice run under 2 s for the whole recipe (spike: about 1.5 s here, [research.md](research.md) item 5)
**Constraints**: no new dependency, setting, flag or ignore line; output bytes of a drawn SVG identical to today's below the comment lines
**Scale/Scope**: three scripts under `assets/toolkit/scripts/event-model/`, one docs page, one fragment, three test files

## Constitution Check

*GATE: evaluated against `.specify/memory/constitution.md` before research; re-checked after design.*

| Principle | Touched? | How this slice satisfies it |
|---|---|---|
| I. A generated project owns its files and passes its own gate (NON-NEGOTIABLE) | Yes | *A scoped or memoised gate MUST be additive*: `make model` is not in `verify`, and `check-model`, `check-drawio` and `check.ts` are not edited; under a CI marker nothing is skipped (e5). The fragment says what a generated repository meets (e17). The matrix tests still pass each starter's own gate. |
| III. Simplicity | Yes | The record is two comment lines in the file they vouch for; no manifest, no setting. One interface (`RenderSession`) with one real implementation. |
| V. Acceptance-driven development | Yes | Each rule a RED-GREEN-REFACTOR cycle at `make model`'s command line; the stand-in is written in the test tree and implements the installed renderer's own exports — no mocking framework. |
| VIII. Versioning and breaking changes | Yes | PATCH: the same answers, generated faster. `extractHash` reads a two-line SVG as it read a one-line one (e7). |
| XIII. Fast feedback (a target here) | Yes | No wall clock in the suite: the counts are held by tests, the time is measured at the demo (D69). The stand-in is validated against the real renderer by the demo (e15). |
| XIV. Agent-generated change meets the same bar (NON-NEGOTIABLE) | Yes | Increment commits with the quickest relevant tests green; both full gates on the final tip; the hand runs the demo as the actor with a real browser. |
| II, IV, VI, VII, IX, X, XI, XII, XV | No | No retry path, domain code, contract, telemetry, secret, pipeline or type changes. |

**Gate result:** no violation; *Complexity Tracking* stays empty. **Post-design re-check:** unchanged.

## Project Structure

```text
assets/toolkit/scripts/event-model/render.ts           # the entry point: wiring, the README block, the page, the closing line
assets/toolkit/scripts/event-model/render-plan.ts      # new — R2–R5: which diagrams the model produces, which are current, orphans, the finished-file write
assets/toolkit/scripts/event-model/render-session.ts   # new — R1, R2: the RenderSession interface, the real session (install, patch, launch, draw, close), the renderer key
assets/toolkit/docs/event-model/README.md              # R6: one sentence on forcing a redraw
docs/event-model.md                                    # R6: where it describes the renderer, if it names one browser per diagram
tests/render_fixture.py                                # new — the fixture project, the 16-slice model, the stand-in renderer and its log (shared by the three below)
tests/test_render_pinned.py                            # new — the Pin stage's holds, green before the change and after
tests/test_render_once.py                              # new — R1, R2
tests/test_render_files.py                             # new — R3, R4, R5
tests/test_changelog.py, changelog.d/render-once.md    # R6: the fragment (PATCH)
```

**Structure Decision**: one deployable, `slipwai-graph` (kind `tool`, path `.`, purpose confirmed); one bounded
context — the factory. The strategy on the map is `leave-it` (D5, as a person left it): the code lands where the
code it changes already is. The two new scripts are files a generated project receives under
`scripts/event-model/`; [research.md](research.md) item 6 is how the toolkit's files reach a project and what
lists them, to be read before the first cycle. `render.ts` runs `main()` on import today, which is why the logic
moves into modules a test could import and the entry point stays thin.

## What this slice changes in code that was here (for the Pin stage)

1. What `make model` leaves on disk for a model: the `.mmd` beside each SVG, the source stamp as the SVG's first
   line with the hash `check.ts` expects, the page, nothing left for a slice the model no longer has, and the
   empty-model branch removing every artifact. Not pinned, changed on purpose: one renderer process per diagram,
   every diagram redrawn on every run, the closing line's words, the wholesale deletion of the two directories.

## Delegation

One story at a time: `[US1]` then `[US2]`, each one `drive-implement` delegate (story/rule). They share
`render.ts` and `render-plan.ts`, so they are not concurrent. The fragment is written in the commit that first
changes what `make model` does (AGENTS.md: the entry in the same commit); `[US2]` completes it.

## Complexity Tracking

None.
