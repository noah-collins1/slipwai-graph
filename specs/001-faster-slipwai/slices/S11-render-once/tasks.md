# Tasks: S11-render-once — diagrams draw through one browser, and only when their source changed

**Input**: [plan.md](plan.md) (*The example map* R1–R6 is what the tasks cut on; *Project Structure*; *What this slice
changes in code that was here*; *Delegation*), [research.md](research.md), [data-model.md](data-model.md),
[quickstart.md](quickstart.md); acceptance criteria AC-S11-1 … AC-S11-17 in `specs/001-faster-slipwai/spec.md` under
`### S11-render-once` (example e*n* is criterion AC-S11-*n*); decisions D7, D9, D12, D32, D39, D67, D68, D69 in
`specs/001-faster-slipwai/decisions.md`. No `examples.md`: a method slice with no screen and no event model of its own.

**Branch**: `adopt-method` (D12). No `slice/` branch, no push, no claim. One commit per task.

**Delegation**: one delegate per implementation task, each its own RED-GREEN-REFACTOR increment and its own commit.
The "Files" line of a task is its manifest: the only files that delegate may write. Nobody but the host writes
`tasks.md`.

**User stories** (from the plan's example map): **US1** one session, and only what changed — `render.ts`, new
`render-plan.ts`, new `render-session.ts` (R1–R3); **US2** what the run leaves and says — the same scripts, the page,
the docs and the fragment (R4–R6). T001 belongs to no story: it is the Pin stage.

**Not a task:** AC-S11-15 (the whole recipe under 2 seconds with one real browser seen to start) is the demo's: the
hand measures it on the reference fixture with a real browser ([quickstart.md](quickstart.md)); the suite holds counts
only.

## Constraints

Constraints that hold for every task, stated once:

- **Not edited, ever, by any task here:** anything under this repository's `delivery/` (except the one `pinned.md` row
  T001 appends, which is the host's `/characterise` step), `tools/`, the `Makefile`, `.github/`, or hook settings (D9);
  nothing under `release/`; no file `delivery/.written` lists. `check-model`, `check-drawio` and `check.ts` are not
  edited (Principle I: the gate is not narrowed).
- **Tests.** Fakes written in the test tree: the stand-in renderer of [research.md](research.md) item 4, written once in
  `tests/render_fixture.py` and shared. It implements the installed renderer's real exports (`renderMermaid`,
  `puppeteer.launch`, `.bin/mmdc`) and logs every call to a file named by an environment variable; the suite's counts
  (sessions, draws, diagrams left) are read from that log, never from the run's own closing line (e14). Never a
  mocking framework (`unittest.mock` included). Never a wall-clock assertion: SC-004 is the demo's, not the suite's
  (D69). A test that loads a script as a module sets `sys.dont_write_bytecode` first. Where a platform cannot make a
  link or set a time, the example skips, saying why. The stand-in is validated against the real renderer by the demo
  (e15), not by a test.
- **Size.** Every file under `src/` and `tests/` stays within 350 lines (`make check-structure`). A task whose examples
  will not fit one test file names a second; the cut is made in advance below (R2 → `tests/test_render_current.py`,
  R5 → `tests/test_render_files_report.py`) and a delegate who finds a file nearing the limit splits by rule, not by
  truncating. The `.ts` files under `assets/` are not under that limit but `render.ts` stays thin: logic goes to
  `render-plan.ts` and `render-session.ts` (`render.ts` runs `main()` on import today, which is why the logic moves
  into modules a test could import).
- **Commits are by path.** `git add <exact path>` for the files in the task's manifest, never `git add -A`.
  `make lint typecheck check-structure` before each commit.
- **RED is seen** for its stated reason before the production file is touched. A **hold** (the plan's *What this slice
  changes in code that was here* says which behaviour is pinned) is written as a hold, saying so in the test's name or
  comment, and is observed passing; it is not a RED. A hold is shown to have teeth by changing the production file in
  the working tree, seeing the test fail, and restoring with `git checkout -- <exact path>`; `git status` then shows
  only the task's own files.
- **Output bytes.** The bytes of a drawn SVG below the two comment lines are today's (the spike drew 25 of 25
  identical, [research.md](research.md) item 2); nothing is added to `scripts/event-model/package.json` (item 3); no
  ignore line is added (item 7).
- **Versioning** (`AGENTS.md`). PATCH: the same answers, generated faster. `VERSION` stays `1.6.0.dev0`. T002 is the
  first commit that changes what `make model` does and carries `changelog.d/render-once.md` in its first form (first
  line `PATCH`); its message names the level and the reason. T007 completes the fragment. Every other commit that
  changes `assets/` or `src/` says `Level PATCH; VERSION already 1.6.0.dev0` once T002 is in; a commit that changes
  only `tests/` says it reaches no user.
- **Quickest test per task:** `make test TESTS="<modules>"`, the modules each task names.

## Format: `[ID] [P?] [Story] Description` — each task is one increment, one commit

`[P]` marks a task whose files are disjoint from every task that may run at the same time. No task here is `[P]`: see
*Parallel opportunities*.

---

## Phase 1: Pin (no story)

### T001 — The shared fixture and the stand-in renderer; what `make model` leaves on disk, pinned (host's `/characterise` step)

- [x] **Pin, no rule, no production change.** *(done at `7226c2e`: three holds, teeth shown on the stamp, the two deletions and the empty-model branch; 13 s.)* The host runs this as the ladder's `/characterise` step before the
  implement stage; the implement stage does **not** repeat it — it starts at T002 with the helper and the pin green.
  Written by `/characterise`; nothing under `assets/` or `src/` changes.

**Pins** (plan, *What this slice changes in code that was here*; each green against today's `render.ts` before any
production change, written as holds, teeth shown):
- `make model` on the fixture project leaves the `.mmd` beside each SVG; the source stamp as the SVG's first line
  with the hash `check.ts` expects; the page `model.html`; nothing for a slice the model no longer has; and the
  empty-model branch removes every artifact.
- *Not pinned, changed on purpose:* one renderer process per diagram, every diagram redrawn on every run, the closing
  line's words, the wholesale deletion of `slices/` and `segments/`.

**Fixture** (`tests/render_fixture.py`, new): generates a project with the event-modelling profile and
`scripts/event-model` installed (how: `tests/test_event_model.py`, `test_the_two_bands_are_namespaced_independently`);
writes `docs/event-model/model.yaml` for a one-slice model and for the 16-slice reference model (16 state-change
slices of three frames each, no slice reading another: 1 + 8 + 16 = 25 diagrams); writes the stand-in renderer under
`scripts/event-model/.mermaid-cli/node_modules/` (`@mermaid-js/mermaid-cli`, `puppeteer`, `mermaid` carrying the text the
patcher accepts as already fixed — read `patch-mermaid-swimlanes.ts`, `applySwimlaneFix` and `esmChunks`, `.bin/mmdc`);
reads the log into counts of sessions opened, diagrams drawn and the launch options; offers a marker the test chooses
that makes a draw throw. Written to be imported by `test_render_pinned.py`, `test_render_once.py`,
`test_render_current.py`, `test_render_files.py` and `test_render_files_report.py`.

**Verify:** `make test TESTS="test_render_pinned"` green against the unchanged `render.ts`, then
`make lint typecheck check-structure`. Commit by path (tests only: reaches no user).

**Files:** `tests/render_fixture.py` (new), `tests/test_render_pinned.py` (new), `delivery/survey/pinned.md` (one row
appended, as `/characterise` does — the only file under `delivery/` any task here touches; append-only).

---

## Phase 2: User Story 1 — one session, and only what changed [US1]

`render.ts`, new `render-plan.ts`, new `render-session.ts`. T002, T003 and T004 all edit these three: they run in order.
Needs T001's helper.

### T002 — [US1] At most one browser, opened on the first diagram to draw (R1 · AC-S11-1, -4, -14, -16)

- [x] **Rule R1.** *(done at `5af7de2`. RED: 25 sessions where 1 was expected; research item 6: the toolkit copies `scripts/event-model/` whole, the one list is `tests/test_monorepos.py`.)* Introduces `RenderSession` (`draw(source, 'svg'|'png') → bytes`, `close()`) with one real
  implementation in new `render-session.ts` (install, patch, launch, draw, close; research items 1–3 and 5: it imports
  `@mermaid-js/mermaid-cli`'s `renderMermaid` and `puppeteer` from the local prefix, never spawns `mmdc`, draws up to
  four pages at a time in the one browser, writes each file in the model's order). `render.ts` becomes the thin wiring;
  `render-plan.ts` enumerates the diagrams the model produces in their order (the whole timeline, segments, slices).
  Also **research item 6**: read how the toolkit's scripts reach a project (`src/slipwai/project/event_model.py`;
  `tests/test_monorepos.py` around line 238 names scripts it expects), find every list that names
  `render.ts`'s neighbours, and add `render-plan.ts` and `render-session.ts` there; if the toolkit copies the directory
  whole and the list is only a test's expectation, extend that expectation and say which it was in the report.
  Also the fragment `changelog.d/render-once.md` in its first form (first line `PATCH`; what `make model` now does:
  one browser per run, opened on the first diagram drawn), and the commit message names the level and the reason
  (the same answers, generated faster): this is the first commit that changes what `make model` does.
  Test module `tests/test_render_once.py` (new).

**RED** (each seen failing for its stated reason before `render.ts` is touched; counts read from the stand-in's log):
- e1 a first run of the fixture → one session opened, 25 drawn through it. Fails today: one launch per diagram.
- e4 a first run, a fresh checkout and a CI run on the fixture → one session, 25 drawn, none left; a one-slice model on a
  first run → one session, three drawn. Fails today for the same reason.
- e14 the counts above are asserted from the stand-in's log, not from the run's own closing line (a test whose
  assertion reads the closing line fails the example's own wording; this is the shape of every count in this slice).
- e16 the stand-in is launched with the contents of the file `MERMAID_PUPPETEER_CONFIG` names; the swimlane patcher still
  runs before the first draw (the stand-in logs the order); the width and the line naming the variable when Chromium
  will not start as root as today. Today's per-diagram `mmdc` passes the config on its command line, so the
  launch-options half is seen failing against the session, and the patch-order half is a hold (pinned by T001's
  fixture, observed passing, teeth shown).
- a model whose every diagram is current → no session opened (the second half of AC-S11-1; its RED waits for T003,
  since "current" does not exist yet: written in T003, listed here so the AC is traced).

**GREEN** — `render-session.ts` with `RenderSession` and the real session (opened lazily by the first `draw`, one per
run, at most four draws in flight, `close()` at the end of the run and on a failure); `render-plan.ts` with the diagram
enumeration; `render.ts` wires them and keeps the README block, the page and the root message as today. The smallest
change that has one session draw every diagram: no skipping, no stamp change, no temporary file yet (T003, T004).

**REFACTOR:** `render.ts` carries no drawing logic; `RenderSession` is the one seam a test substitutes. Today's
`runMermaid()` per-diagram spawn is deleted, not kept beside the session.

**Verify:** `make test TESTS="test_render_pinned test_render_once test_toolkit test_monorepos test_event_model"`, then
`make lint typecheck check-structure`. Commit (`Level PATCH`; the fragment's first form).

**Files:** `assets/toolkit/scripts/event-model/render.ts`, `assets/toolkit/scripts/event-model/render-plan.ts` (new),
`assets/toolkit/scripts/event-model/render-session.ts` (new), whichever list or test expectation research item 6 finds
(named in the report; expected `tests/test_monorepos.py`, possibly `src/slipwai/project/event_model.py`),
`changelog.d/render-once.md` (new), `tests/test_render_once.py` (new).

### T003 — [US1] A diagram is left only when its SVG is shown current (R2 · AC-S11-2, -3, -5, -6, -7)

- [x] **Rule R2.** *(done at `d512cd0`. RED: 25 drawn where 3 were expected, and one failure per condition of the skip; removal by name moved here from T005, since a wholesale deletion cannot leave a current SVG.)* `render-plan.ts` decides current: the first line is the source stamp with the hash of the Mermaid the
  model produces now (never the `.mmd` on disk), the second line the renderer line carrying this run's key, the trimmed
  file ends `</svg>`, and none of `CI`, `GITHUB_ACTIONS`, `GITLAB_CI` is non-empty. `render-session.ts` computes the
  renderer key once per run, after the install and the patch and before any comparison: SHA-256 over the installed
  mermaid-cli version, the installed mermaid version (each read from its `package.json` under
  `scripts/event-model/.mermaid-cli/`), the bytes of `render.ts`, `render-plan.ts`, `render-session.ts` and
  `patch-mermaid-swimlanes.ts`, and the bytes of the file `MERMAID_PUPPETEER_CONFIG` names or a fixed word where it is
  unset, each part length-prefixed or separated (data-model). `extractHash` in `mermaid.ts` reads the source stamp as
  before from a two-line SVG; the page carries both comments where it inlines the picture. Test modules
  `tests/test_render_once.py` (e2, e3) and `tests/test_render_current.py` (new; e5, e6, e7).

**RED:**
- e2 the fixture, every diagram drawn by a previous run, one slice's frame renamed (frame count kept, no other slice
  reads it) → one session, three drawn (the timeline, that slice's segment, that slice), 22 left byte for byte. Fails
  today: 25 drawn.
- e3 an added frame redraws every later slice and segment (frame numbers are global), and no earlier one. Fails today.
- e5 one example per condition, each redrawing that diagram alone (CI marker: all): a wrong source hash; no renderer
  line; a wrong key; a file with no closing `</svg>`; each of `CI`, `GITHUB_ACTIONS`, `GITLAB_CI` set non-empty (an empty
  value is not a marker). Fails today: nothing is left.
- e6 each input of the key changed in turn — mermaid-cli's version, mermaid's version, each of the four scripts' bytes
  (the test edits a copy in the fixture, never `assets/`), the config file's bytes, the variable set versus unset —
  redraws every diagram on the next run, and a run with none changed redraws none. Fails today.
- e7 `extractHash` on a two-line SVG reads the same hash it read from a one-line one (a hold on the reader, written as
  one: observed passing, teeth shown by changing `mermaid.ts`'s regex); and the page, built from the SVGs on disk,
  carries both comments. An SVG with no renderer line (one an earlier factory drew) is redrawn once and then left.
  The page half fails today.
- AC-S11-1's second half: nothing to draw → no session opened (the stand-in's log holds no launch). Fails today.

**GREEN** — the stamp becomes two lines; the plan marks each diagram drawn or left from the four conditions; the session
opens only when a draw is asked for. The `.mmd` files and the README block are written as today (R5 narrows them).

**REFACTOR:** the condition is one function with the four conditions named; the key is one function with one separator
rule, not four concatenations.

**Verify:** `make test TESTS="test_render_pinned test_render_once test_render_current test_event_model"`, then
`make lint typecheck check-structure`. Commit (`Level PATCH; VERSION already 1.6.0.dev0`).

**Files:** `assets/toolkit/scripts/event-model/render.ts`, `render-plan.ts`, `render-session.ts`, `mermaid.ts`
(only if `extractHash` or `stamp` need it; named in the report), `tests/test_render_once.py`,
`tests/test_render_current.py` (new).

### T004 — [US1] A file reaches its name finished, or not at all (R3 · AC-S11-8, -9)

- [x] **Rule R3.** *(done at `6c7d667`. RED: the failed diagram was not named and a draw in flight was not written; e9 held on arrival after T002, teeth shown.)* `render-plan.ts` writes each drawn SVG to a temporary in `docs/event-model/slices/` (already ignored by
  `src/slipwai/project/gitignore.py`, same directory tree as every output; research item 7), carrying both comment lines,
  then renames it to its name; its name cannot be one the model produces (a leading dot and a suffix the code fixes). A
  failed draw leaves the earlier file's bytes, removes its own temporary, names the diagram on stderr and exits non-zero
  after no further draw is started and the draws already in flight have finished and been written (plan.md, under the example map); the session is closed on every path. `PNG=1` or `--png`
  draws `model.png` on every such run, never leaves it, in the same session and by the same rename; not asked for, an
  existing `model.png` is left as today. Test module `tests/test_render_files.py` (new).

**RED:**
- e8 the stand-in throws on one diagram (the marker the fixture offers) → the earlier SVG's bytes stand, exit code 1,
  the diagram's name on stderr, no temporary left for `git status` (asserted by listing the tree and by `git status
  --porcelain` over a repository the fixture initialises). Fails today: `mmdc` failing leaves a torn or absent file and
  no name.
- e9 `PNG=1` twice → `model.png` drawn twice, both in the same session as the SVGs; `model.png` not drawn without it,
  an existing one untouched. Fails today: a second browser for the PNG.
- a file torn by anything else (no closing `</svg>`) is redrawn: a hold on T003's e5, not repeated.

**GREEN** — the temporary-then-rename write in `render-plan.ts`, the failure path, the PNG through the session.

**REFACTOR:** one finished-file write function, used by SVG and PNG alike.

**Verify:** `make test TESTS="test_render_pinned test_render_once test_render_current test_render_files"`, then
`make lint typecheck check-structure`. Commit (`Level PATCH; VERSION already 1.6.0.dev0`).

**Files:** `assets/toolkit/scripts/event-model/render.ts`, `render-plan.ts`, `render-session.ts`,
`tests/test_render_files.py` (new).

---

## Phase 3: User Story 2 — what the run leaves and says [US2]

Needs US1 whole (the plan, the session and the finished-file write exist). Edits the same scripts.

### T005 — [US2] What the model no longer produces is removed by name, before drawing (R4 · AC-S11-11)

- [x] **Rule R4.** *(done at `87fb091`: a hold on arrival — removal by name landed in T003; teeth shown by a wholesale delete and by removing nothing.)* The two directories are no longer deleted wholesale. At the start of a run, every entry in `segments/`
  and `slices/` whose name the current model does not produce (`model-<i>.mmd` and `model-<i>.svg` per segment,
  `<slice id>.mmd` and `<slice id>.svg` per slice) is removed before anything is drawn — file or directory, a
  leftover temporary included (T004's prefix and suffix). The empty-model branch does what it does today. Test module
  `tests/test_render_files.py`.

**RED:**
- e11 a removed slice, a stray directory, a leftover temporary → each gone after the run and nothing the model still
  produces touched (its SVG's bytes unchanged, no session opened for it); then the empty model → every artifact removed
  as the pin holds. Fails today only in that the wholesale deletion is what removes them and a skip cannot survive it:
  seen failing against the rest of the tree — a current slice's SVG whose bytes must stand and whose mtime must not
  move, which today's deletion fails.

**GREEN** — `render-plan.ts` lists the names the model produces and removes the rest of each directory before the first
draw; the wholesale deletion is gone.

**REFACTOR:** the set of names the model produces is the one the plan already enumerates, not a second list.

**Verify:** `make test TESTS="test_render_pinned test_render_files"`, then `make lint typecheck check-structure`.
Commit (`Level PATCH; VERSION already 1.6.0.dev0`).

**Files:** `assets/toolkit/scripts/event-model/render.ts`, `render-plan.ts`, `tests/test_render_files.py`. If the file
nears 350 lines, this task's examples move to `tests/test_render_files_report.py` (new, R5's) — decided by the delegate,
named in the report.

### T006 — [US2] Text files are written only when they differ, and the run says what it did (R5 · AC-S11-12, -13)

- [x] **Rule R5.** *(done at `7a99ba5`: RED: the old closing line, and every `.mmd` and the page rewritten on an unchanged tree.)* The `.mmd` files, `model.html` and the README block are each computed every run and written only
  where their bytes differ from the file on disk; `model.html` is built from the SVGs on disk after drawing. One
  `wrote <path>` line per file written and none for a file left. The closing line reports `{ slices, diagrams, drawn,
  unchanged, sessionOpened }` (data-model, *Report*): on the fixture's edit `model: 16 slices, 3 of 25 diagrams drawn,
  22 unchanged. Open docs/event-model/model.html to browse it.`; with nothing changed `model: 16 slices, 0 of 25
  diagrams drawn, 25 unchanged; no browser started. Open docs/event-model/model.html to browse it.` The empty-model
  message stays. Test module `tests/test_render_files_report.py` (new).

**RED:**
- e12 a second run on an unchanged tree → no `wrote` line, no file's mtime moved (the fixture reads `st_mtime_ns` before
  and after; the example skips, saying why, where the platform's time is too coarse to show a rewrite — never a sleep).
  Fails today: every text file is rewritten and reported.
- e13 the two closing lines, verbatim, on the fixture's edit and on the nothing-changed run (the line is the
  specification here, and the counts come from the log as in e14); the empty-model message unchanged. Fails today: the
  old closing words.

**GREEN** — a write-if-different helper used by the three text outputs; a `Report` built through the run and the closing
line written from it.

**REFACTOR:** one write-if-different helper; the closing-line builder is a pure function of the report.

**Verify:** `make test TESTS="test_render_pinned test_render_once test_render_current test_render_files test_render_files_report"`,
then `make lint typecheck check-structure`. Commit (`Level PATCH; VERSION already 1.6.0.dev0`).

**Files:** `assets/toolkit/scripts/event-model/render.ts`, `render-plan.ts`, `tests/test_render_files_report.py` (new).

### T007 — [US2] The page, the fragment and the docs say it (R6 · AC-S11-10, -17)

- [x] **Rule R6.** *(done at `273129c`: the sentences were written before their test, so a hold with teeth shown on each of the three files, not a RED.)* Completes `changelog.d/render-once.md` and corrects the page. The one sentence in
  `assets/toolkit/docs/event-model/README.md` on forcing a redraw (no setting and no flag: delete a diagram, or
  `segments/` and `slices/`). The fragment's two catch-up sentences, first line still `PATCH`: after `slipwai migrate`
  nothing is asked of a repository, its first `make model` redraws every diagram once and nothing committed changes
  since the output is ignored; one that removed the ignore lines and commits the diagrams sees the second comment line
  in each SVG once. `docs/event-model.md` where it describes the renderer and names one browser per diagram. Needs T006.
  Test module `tests/test_render_docs.py` (new).

**RED:**
- e10 the shipped README holds the sentence about forcing a redraw by deleting a diagram or the two directories, and says
  there is no setting and no flag; `docs/event-model.md` no longer says one browser per diagram. Fails today: absent.
- e17 each sentence of the fragment followed as written: the first line is `PATCH`, the two catch-up sentences are
  present, `VERSION` reads `1.6.0.dev0`, and `make test TESTS="test_changelog"` is green (the arithmetic of
  `tests/test_changelog.py`). The two-sentence half fails today; the version half is a hold.

**GREEN** — the fragment's final form, the README sentence, the `docs/event-model.md` correction. `git diff` over the
slice shows no change under `delivery/` beyond T001's row, `tools/`, `.github/`, the `Makefile` or hook settings, and no
file `delivery/.written` lists.

**REFACTOR:** none.

**Verify:** `make test TESTS="test_render_docs test_changelog test_event_model"`, then
`make lint typecheck check-structure`. Commit (`Level PATCH; VERSION already 1.6.0.dev0`).

**Files:** `changelog.d/render-once.md`, `assets/toolkit/docs/event-model/README.md`, `docs/event-model.md`,
`tests/test_render_docs.py` (new).

---

## Phase 4: Gates

### T008 — The slice's neighbouring suites, then the lint, type and structure gates (closing task before convergence)

- [x] *(run at `273129c` with the six render modules added: 71 tests OK, 1 skipped; lint, typecheck and structure green.)* `make test TESTS="test_toolkit test_utf8_io test_changelog test_event_model test_layout test_monorepos"` green,
  then `make lint typecheck check-structure`. No file over 350 lines under `src/` or `tests/`; the three scripts under
  `assets/toolkit/scripts/event-model/` are each wholly the owner of their rule (no second copy of the enumeration or of
  the write). If any of this fails, the delegate stops and reports which task's change broke it; it does not edit a file
  outside this slice's manifests to make it pass. Commit only if the run required a change, by path, otherwise no
  commit.

The full gates (`make verify` and `make -f delivery/Makefile verify`) on the final tip and the demo from
[quickstart.md](quickstart.md) are the host's, after this task (Principle XIV).

**Files:** none unless the run requires a fix, which is then named in the report.

---

## Parallel opportunities

- **Nothing here is concurrent.** US1 (T002–T004) and US2 (T005–T007) both write `render.ts` and `render-plan.ts`;
  T002–T004 and T005–T006 also write `render-session.ts` or the test files each other's examples live in; T002, T003 and
  T004 share `tests/test_render_once.py` or `tests/test_render_files.py`, and T005 shares `tests/test_render_files.py`
  with T004. Two delegates would write one file. They run one at a time, in order: T001 (host, Pin), T002, T003, T004,
  T005, T006, T007, T008.
- **No `[P]` is claimed.** The only disjoint pair is T007's docs files against the scripts, but T007 needs the closing
  line of T006 to be worded as the docs describe it, and the fragment is T002's file, so it waits.
- **Most delegates at once: one.**
- **Host tasks:** T001 (the Pin, `/characterise`), the full gates after T008, the demo (AC-S11-15 is measured there),
  and the writing of `tasks.md`.

## Design review

No screen in this slice

## Phase 4: Convergence passes

*(appended by `drive-converge`)*

### Pass 1 (2026-10-03, at `273129c`)

#### T009 — `HIGH` — The finished-file write has no example that fails when the rename is removed (AC-S11-8, AC-S11-9)

- [x] *(done at `765cad5`: holds on arrival; teeth: a direct write fails five tests, a kept temporary fails one.)* **Hold with teeth, tests only unless the sweep finds a write that bypasses it.** Evidence: `writeFinished`
  (`render-plan.ts` 109–120) changed in the working tree to `writeFileSync(join(ROOT, path), bytes)` — no temporary, no
  rename — and `make test TESTS="test_render_files test_render_files_report test_render_pinned"` ran 15 tests, OK; the
  file was restored with `git checkout --`. "Reaches its final name only by a rename of a complete file" and the PNG's
  "by the same rename" are implemented and unheld; `test_e8`'s `leftovers == []` cannot fail either, because a failed
  *draw* never writes a temporary.

**RED/hold:** (1) an SVG and `model.png` that exist and are redrawn arrive as a *new* file — an example a direct
write fails, e.g. the earlier file made read-only (`chmod 0444`) is still replaced, or its inode changes; skips, saying
why, on Windows and as root where the platform cannot show it. (2) The rename cannot happen (`segments/` made
`0555`): exit non-zero, the earlier file's bytes stand, no `.tmp-*` anywhere under `docs/event-model/`, the session
closed (log: one close). Teeth shown for each by the mutation above and by deleting the `rmSync(temporary)` in the
catch.

**GREEN (the class, not the instance):** sweep every write under `docs/event-model/` that `render.ts`,
`render-plan.ts` and `render-session.ts` make and say for each which example fails if it stops being temporary-then-
rename (SVG, PNG) or write-if-different (`.mmd`, page, README block); any without one gets one here.

**Files:** `tests/test_render_files.py` (or a new `tests/test_render_finished.py` if it nears 350 lines).

#### T010 — `MEDIUM` — A failure that is not one diagram's draw is reported as itself, once, and held (AC-S11-8, AC-S11-16)

- [x] *(done at `0b3409d`: RED: seven assertions against the pre-fix scripts; the root line held through a probe with a stand-in `open`.)* Evidence, each reproduced on a scratch project with the stand-in (`/tmp/s11-converge/fx2`): (a) the stand-in's
  `launch` throwing → stderr is `render: could not draw <svg>: Failed to launch the browser process` once per diagram
  of the first window (three lines for a one-slice model, four on the fixture): the browser's failure is reported as
  three or four diagrams'; (b) a PNG draw throwing → stderr is the bare reason (`png refused`), no `render:` and no
  `model.png`; (c) `MERMAID_PUPPETEER_CONFIG` naming a missing file → bare `ENOENT … open '/nonexistent.json'`, the
  variable not named; (d) no test in `tests/` names the root line (`grep -rn 'running as root' tests/` is empty), so
  AC-S11-16's third clause — `explainRootLaunch`, `render-session.ts` 137–146 and 160–162 — is unheld, as is any launch
  failure at all.

**RED:** a launch that fails → exit non-zero, one line saying the browser could not be started, no diagram blamed, no
close on a session never opened; the root line through a probe that imports `render-session.ts`, sets
`process.getuid = () => 0` and gives `lazySession` an `open` that throws (a fake in the test tree, D69's seam) — with
and without `MERMAID_PUPPETEER_CONFIG`; a failed PNG names `docs/event-model/model.png`; a config path that cannot be
read names the variable.

**GREEN (the class):** sweep every `throw` and rejected promise that can leave `main()` in the three scripts
(`drawDiagrams`, `drawPng`, `writeFinished`, `rendererKey`, `launch`, `entryOf`) and give each a `render:` line naming
what failed — the diagram, the file, or the browser — exactly once.

**Files:** `assets/toolkit/scripts/event-model/render-plan.ts`, `render-session.ts`, `tests/test_render_files.py` or a
new module; the fragment if a sentence of it changes (`Level PATCH; VERSION already 1.6.0.dev0`).

#### T011 — `LOW` — The skip rule's positions have examples (AC-S11-5)

- [x] *(done at `bf86868`: five examples, held on arrival; teeth: `includes` in place of the line comparison fails four.)* Reproduced as *held by the code, not by a test*: a renderer line on line 3 (a blank line 2), the two lines
  swapped, both stamps on one line, and CRLF line ends each redraw that diagram once and then leave it; a second,
  wrong source stamp on line 3 is left, and `check.py` agrees (it reads the first match). Add the four redraw
  examples and the one left example to `tests/test_render_current.py`; teeth by changing `isCurrent`'s
  `split('\n', 2)` comparison to a `includes`. **Sweep:** every reader of the two lines (`isCurrent`, `extractHash`
  in `mermaid.ts`, `check.ts` 96 and 142, `page.ts`) named with the line it reads and the example that holds it.

**Files:** `tests/test_render_current.py`.

#### T012 — `LOW` — `1 slices`, `--png`, and a skip reason that stopped being true

- [x] *(done at `e39f2fc`: `1 slice`; `--png` has an example; the Windows skip says its true reason and is not lifted.)* (a) A one-slice model closes `model: 1 slices, 3 of 3 diagrams drawn, 0 unchanged.` (reproduced; the pre-slice
  line said `1 slices rendered` too, so nothing regressed) — the closing-line builder agrees its nouns with their
  counts, the two verbatim lines of AC-S11-13 unchanged; sweep every count the three scripts print. (b) `--png` is
  read at `render.ts` 69 and no test passes it; one example beside `PNG=1`. (c) every render test is skipped on
  Windows "because the stand-in's `.bin/mmdc` is a shebang script", and since T002 nothing spawns `mmdc`: say the
  true reason (`make`, the recipe) or lift the skip where it no longer applies; sweep the six modules.

**Files:** `assets/toolkit/scripts/event-model/render-plan.ts`, `tests/test_render_files_report.py`,
`tests/test_render_files.py`, the skip decorators of `tests/test_render_*.py`.

#### T013 — `MEDIUM` — The installed puppeteer version joins the renderer key (D70; AC-S11-6)

- [x] *(done at `107f008`: RED: a changed puppeteer version redrew 0 where 3 were expected.)* Pass 1's lead, decided as D70: the key gains one part — the `version` in
  `scripts/event-model/.mermaid-cli/node_modules/puppeteer/package.json`, length-prefixed like the others, after the
  mermaid version and before the script bytes; a missing or unreadable manifest fails as the mermaid-cli one does.

**RED:** in e6's sweep, the stand-in's `puppeteer` version changed → every diagram redrawn on the next run (today:
none). **GREEN (the class):** every package the session loads from the prefix (`entryOf` and its callers) has its
installed version in the key; the comment on `rendererKey` lists the closed set as D70 gives it. The README's
sentence on forcing a redraw gains the clause on a browser upgraded behind an `executablePath`; the fragment's line on
what the key covers names Puppeteer; `tests/test_render_docs.py` follows both.

**Files:** `assets/toolkit/scripts/event-model/render-session.ts`, `assets/toolkit/docs/event-model/README.md`,
`changelog.d/render-once.md`, `tests/test_render_current.py`, `tests/test_render_docs.py`, `tests/render_fixture.py`
(additions only).

### Pass 2 (2026-10-03, at `107f008`)

No `CRITICAL` or `HIGH`. T009–T013 re-checked as classes: the direct-write mutation of `writeFinished` now fails two
examples of `tests/test_render_files.py` (it failed none at pass 1); a launch that throws, a PNG that throws and a
config naming a missing file each give one `render:` line (stand-in, and the first and third on the real renderer).
Real run on the 16-slice project: `25 of 25 … drawn, 0 unchanged`, then `0 of 25 … 25 unchanged; no browser started`,
then `3 of 25 … 22 unchanged` after one frame's edit; all 25 SVGs below the two comment lines byte-identical to the
pre-slice renderer's. Two leads from reading T010's diff, neither reproduced through `main()`, neither re-opening
the loop.

#### T014 — `LOW` — A browser that will not close does not replace the failure the run already had (AC-S11-8)

- [x] *(done at `e05d7ca`: the lead reproduced — a close that failed hid the draw's lines; both are now said, the draw's first.)* Lead, from the code and not reproduced: `render.ts` 96–101 closes the session in a `finally`, and since T010
  `close` throws `render: could not close the browser: …` (`render-session.ts` 203–209). A throw in a `finally`
  replaces the error in flight, so a run whose draw failed *and* whose browser then fails to close prints only the
  close line: the `could not draw <svg>` lines are lost. Exit is still non-zero. Reproduction: give the stand-in a
  `close` that throws beside `STAND_IN_PNG_FAILS` (a new variable in `tests/render_fixture.py`) and read stderr.

**RED:** a draw that fails and a close that fails → both lines on stderr, the draw's first, exit non-zero; a close
that fails after every draw succeeded → its one line, exit non-zero, every SVG already at its name.
**GREEN (the class):** every `finally` and `catch` in the three scripts that can itself throw (`render.ts` 99–101,
`writeFinished`'s `rmSync` in its catch, `lazySession.close`) keeps the first failure and adds the second.

**Files:** `assets/toolkit/scripts/event-model/render.ts`, `tests/render_fixture.py`, `tests/test_render_failures.py`;
the fragment only if a sentence of it changes (`Level PATCH; VERSION already 1.6.0.dev0`).

#### T015 — `LOW` — The root line and "could not start the browser" are said only of the browser's launch (AC-S11-16)

- [x] *(done at `e287dc6`: the lead reproduced — a package that cannot be loaded read as *could not start the browser*; it is now named as itself and the root line is said only of the launch.)* Lead, from the code and not reproduced: T010 moved the root explanation from around `puppeteer.launch` to
  `lazySession`'s `open().catch` (`render-session.ts` 221–223), so `browserFailure` now also wraps `entryOf` and the
  two `import()`s of `launch` (190–195). A prefix whose mermaid-cli or Puppeteer entry cannot be imported is reported
  as `render: could not start the browser: Cannot find module …`, and as root with no config it is preceded by the
  advice to pass `--no-sandbox`, which would not fix it. Reproduction: the stand-in's `puppeteer` entry file deleted
  after the install (its `package.json` kept, so `rendererKey` passes), then `make model`; and the probe of
  `test_e16` with an `open` that throws a module-not-found error.

**RED:** an entry that cannot be imported → one `render:` line naming the package and the prefix, no root line even
as root. **GREEN (the class):** each step of `launch` (resolve, import, read config, start) fails under its own
name; the root line is printed only when the step that failed is the start.

**Files:** `assets/toolkit/scripts/event-model/render-session.ts`, `tests/test_render_failures.py`,
`tests/render_fixture.py` (additions only).

### After-converge gaps (2026-10-03, `drive-gaps` at `107f008`; D71)

#### T016 — `MEDIUM` — The way to redraw everything names the whole timeline's file (G1 · AC-S11-10)

- [x] *(done at `65a3843`: RED: the followed remedy drew 5 of 6, the timeline left.)* `docs/event-model/model.svg` is outside `segments/` and `slices/`, so the remedy as written redraws 24 of 25.
  **RED:** `tests/test_render_docs.py`'s followed example deletes exactly what the sentence names and expects every
  diagram drawn (today: the timeline is left). **GREEN (the class):** every text that gives the remedy — the README
  block under `assets/toolkit/docs/event-model/README.md` (both places: forcing a redraw, and the browser behind an
  `executablePath`), `docs/event-model.md`, `changelog.d/render-once.md` — names `docs/event-model/model.svg`,
  `segments/` and `slices/`; sweep the three for any other sentence that says what a deletion redraws.

**Files:** `assets/toolkit/docs/event-model/README.md`, `docs/event-model.md`, `changelog.d/render-once.md`,
`tests/test_render_docs.py`.

#### T017 — `LOW` — Two runs, a CI marker, and an edited `render.ts` are each said (G4, G6, G7 · AC-S11-18, -19, -20)

- [x] *(done at `1d336ea`: teeth, not a clean RED; the naming is held through a probe that imports it.)* (a) The temporary's name carries the process id (`.tmp-<kind>-<pid>-<file name>`); removal of what the model
  does not produce still takes any `.tmp-` entry; the README says one run per tree at a time. **RED:** an example
  that reads the temporary's name while a draw is held (the stand-in can pause on a marker file) or, failing that, a
  probe importing `writeFinished`'s naming — and the hold that a leftover `.tmp-` of any process is removed.
  (b) Under a CI marker the closing line gains one clause saying everything was drawn because one is set; AC-S11-13's
  two lines are byte for byte unchanged where none is. **RED:** `CI=true` on a drawn tree → the clause. (c) The
  fragment's catch-up gains the sentence of AC-S11-20; `tests/test_render_docs.py` asserts it.
  **Sweep:** every place the three scripts print a count or name a temporary.

**Files:** `assets/toolkit/scripts/event-model/render-plan.ts`, `render.ts`, `assets/toolkit/docs/event-model/README.md`,
`changelog.d/render-once.md`, `tests/test_render_files.py`, `tests/test_render_files_report.py`,
`tests/test_render_docs.py`, `tests/render_fixture.py` (additions only), a new `tests/test_render_runs.py` if a file
would pass 350 lines.

#### T018 — `HIGH` — The render tests pass whatever CI marker the suite itself runs under (found by the host at `1d336ea`)

- [x] *(done at `dde4317`: one helper, `render_env`, builds every render test's environment with the three markers removed unless the test sets one; five sites swept; the seven modules green plain, under `CI=true`, and under `GITHUB_ACTIONS=true GITLAB_CI=true`.)* Evidence: `CI=true make test TESTS="test_render_once"` → `FAILED (failures=3)` at `1d336ea`. Every render test
  hands `os.environ` to `make model`, and under `CI`, `GITHUB_ACTIONS` or `GITLAB_CI` nothing is skipped (AC-S11-5), so
  in this factory's own CI every example that expects a diagram to be left fails: the full gate would be red on the
  forge and green here.

**RED:** the module run with each marker set in the suite's own environment fails today. **GREEN (the class):**
one helper in `tests/render_fixture.py` builds the environment every render test's subprocess gets, with the three
markers removed unless the test sets one; sweep every `subprocess` call and every `env=` in the seven render modules
and the fixture so none passes `os.environ` through unfiltered. **Verify:** the seven modules green three times —
plain, under `CI=true`, and under `GITHUB_ACTIONS=true GITLAB_CI=true`. Also, in the fragment's catch-up, the first
sentence and the `render.ts` sentence stop contradicting each other: nothing is asked of a repository that left
`render.ts` as generated (`tests/test_render_docs.py` follows the wording).

**Files:** `tests/render_fixture.py`, `tests/test_render_once.py`, `tests/test_render_current.py`,
`tests/test_render_files.py`, `tests/test_render_files_report.py`, `tests/test_render_docs.py`,
`tests/test_render_failures.py`, `changelog.d/render-once.md`. (`tests/test_render_pinned.py` reaches `make model`
only through the fixture's helper; if it passes an environment of its own, say so and the host decides.)

#### T019 — `MEDIUM` — The hold that a second run writes nothing is never run on Linux (found by the host at `dde4317` · AC-S11-12)

- [ ] Evidence: the seven modules report `skipped=1`, and it is
  `test_e12_a_second_run_on_an_unchanged_tree_writes_nothing_and_says_nothing_was_written`: its guard `clock_is_fine`
  writes a probe twice in a row and skips where the two modification times are equal, which on Linux they are (the
  kernel stamps both within one tick). The two `make model` runs it guards are seconds apart, so the guard asks the
  wrong question, and the example — including `wrote(second) == []`, which needs no clock — has never run here.

**GREEN (the class):** the guard goes, or asks what the example needs (a time apart at least as long as the two runs
are); the `wrote` assertion never depends on a clock; sweep the seven modules for any other `skipTest` or guard that
fires on this machine and say which examples ran. **Verify:** the module reports no skip here; teeth by making
`writeIfDifferent` always write.

**Files:** `tests/test_render_files_report.py`, `tests/render_fixture.py` (additions only).

### After the adversary pass (2026-10-03, two seams at `dde4317`; D72; the row under `## S11` in `adversary-log.md`)

#### T020 — `HIGH` — Nothing is removed, read or written through a link, and nothing outside `docs/event-model/` is ever removed (A1, A2, A3, A5 · AC-S11-21)

- [ ] Evidence (seam A, `/tmp/s11-adv-A.md`): `docs/event-model/slices -> <dir>` and `make model` empties `<dir>` at
  exit 0; committed as `slices -> ../..` it removed `.git`, the `Makefile` and `model.yaml`. A dangling link or a file
  at `slices`, or a directory at `slices/S1.svg` or `S1.mmd`, fails every run; `slices/S2.mmd -> <file>` is written
  through; `mkfifo slices/S1.svg` hangs the run.

**RED:** each of those, with the stand-in: the victim directory's and file's bytes stand; the link, the file or the
FIFO is gone and a real directory or a drawn file is in its place; exit 0; a `removed <path>` line for each thing
removed from the two directories (the hand's note 3). **GREEN (the class):** one rule in `render-plan.ts` — `lstat`
before use: the two directories must be real directories or are removed as themselves and made; an entry at a
produced name that is not a regular file is removed, then drawn or written; sweep every path the three scripts read,
write, rename onto or descend under `docs/event-model/` (`model.svg`, `model.png`, `model.mmd`, `model.html`, each
segment's and slice's two files, the temporaries) and say for each what a link, a directory and a FIFO there now
gives. The pins stay green unedited.

**Files:** `assets/toolkit/scripts/event-model/render-plan.ts`, `render.ts`, a new `tests/test_render_links.py`,
`tests/render_fixture.py` (additions only), `changelog.d/render-once.md` (one clause: removal by name never follows
a link).

#### T021 — `LOW` — The temporary's name does not carry the file's name (A4 · AC-S11-22)

- [ ] Evidence: an id of `S` and 245 letters passes the model; `.tmp-slice-<pid>-<id>.svg` passes 255 bytes and the run
  fails `ENAMETOOLONG`. **RED:** that id is drawn. **GREEN:** `.tmp-<pid>-<n>` with a counter per process, still in
  `docs/event-model/slices/`, still removed as a leftover by any later run; AC-S11-18's example follows the new shape.

**Files:** `assets/toolkit/scripts/event-model/render-plan.ts`, `tests/test_render_files.py` or `tests/test_render_links.py`.

#### T022 — `MEDIUM` — Puppeteer's environment is in the key, and the config is read once (B1, B6 · AC-S11-23)

- [ ] Evidence (seam B, `/tmp/s11-adv-B.md`): `PUPPETEER_EXECUTABLE_PATH=<other browser> make model` → `0 of 25 drawn`;
  a config swapped between the key and the launch is drawn under the first bytes' key. **RED:** in e6's sweep, a
  `PUPPETEER_` variable set, changed and unset each redraws everything; the stand-in's `launch` receives exactly the
  options the keyed bytes parse to (a config file replaced after the key is computed — through a probe, a fake `open`
  in the test tree — is not what is launched with). **GREEN (the class):** every input the launch takes from outside
  the scripts is either in the key or named in the README's sentence on what the key does not notice (a browser
  behind a path the config names; a Puppeteer rc file); the fragment's line on the key says the same.

**Files:** `assets/toolkit/scripts/event-model/render-session.ts`, `render.ts`, `assets/toolkit/docs/event-model/README.md`,
`changelog.d/render-once.md`, `tests/test_render_current.py`, `tests/test_render_docs.py`, `tests/test_render_failures.py`,
`tests/render_fixture.py` (additions only).

#### T023 — `LOW` — A browser that stopped is said once, as the browser, and a browser that cannot start says what to do (B4, B3's blame, B2's message, the hand's note 4 · AC-S11-24)

- [ ] Evidence: `kill -9` of the browser mid-window → four `could not draw …: Connection closed.` lines; no sandbox and
  no config → Chromium's own paragraph, the variable never named unless root; an interrupted install →
  `Could not find chrome-headless-shell` on every run with no word on the prefix. **RED:** the stand-in's browser
  disconnects mid-window (a new fixture variable) → one line saying the browser stopped, no diagram blamed, exit
  non-zero, earlier files and no temporary; a launch failing with a no-sandbox message and no config → the line names
  `MERMAID_PUPPETEER_CONFIG`; a launch failing for a missing browser → the line says to delete
  `scripts/event-model/.mermaid-cli` and run again. **GREEN (the class):** every failure whose cause is the browser
  rather than a diagram is reported once as the browser; sweep `drawDiagrams`, `drawPng` and `lazySession`.

**Files:** `assets/toolkit/scripts/event-model/render-session.ts`, `render-plan.ts`, `render.ts`,
`tests/test_render_failures.py` (or a new `tests/test_render_browser.py` past 350 lines), `tests/render_fixture.py`.

#### T024 — `LOW` — A PNG-only run says the PNG was drawn (the hand's note 1 · AC-S11-25)

- [ ] Evidence (demo): `PNG=1` with nothing else to draw closes `0 of 22 diagrams drawn, 22 unchanged.` though a
  browser ran. **RED:** that run's closing line says the PNG was drawn; AC-S11-13's two lines unchanged without `PNG`.
  **GREEN:** one clause; sweep the closing line's cases (drawn, none, CI, PNG, each with the others).

**Files:** `assets/toolkit/scripts/event-model/render-plan.ts`, `render.ts`, `tests/test_render_files_report.py`.

## Convergence

**Converged at `107f008`, at the loop's bound: two passes** (`drive-converge`, host model, fresh context each). Pass 1
at `273129c` found one `HIGH` (T009), two `MEDIUM` (T010, and the lead D70 decided, T013) and two `LOW` (T011,
T012); all five are done. Pass 2 at `107f008` found nothing `CRITICAL` or `HIGH`, re-ran pass 1's reproductions
(the direct-write mutation now fails two tests; a launch that throws, a PNG that throws and a config that names a
missing file each give one `render:` line) and left two `LOW` leads, T014 and T015, which are Phase 4's and do not
re-open the loop. The tree was clean after each pass (`git status`: only this file and the run's own records).

**Sweeps performed.** Every write under `docs/event-model/` the three scripts make: SVG and PNG through the
temporary-then-rename, `.mmd`, page and README block through write-if-different, none bypassing either (T009).
Every `throw` and rejected promise that can leave `main()`: each gives one `render:` line naming the diagram, the
file or the browser (T010). Every reader of the two comment lines: `isCurrent` reads lines 1 and 2 exactly,
`extractHash` the first match, `check.ts` through it, `page.ts` neither (T011). Every package the session loads
from the prefix has its installed version in the key (T013).

**With a real browser** (pass 2, a copy of the 16-slice project): first run 25 of 25 drawn; unchanged run 0 of 25,
no browser started; a one-frame edit 3 of 25 (`model.svg`, its segment, its slice); all 25 SVGs byte-identical below
the two comment lines to what the renderer before the slice drew.

**Constitution principles the diff touches.** I — `check.ts`, `check.py` and the recipe are not in the diff; the
fragment's first line is `PATCH` (`changelog.d/render-once.md`), `VERSION` reads `1.6.0.dev0`; nothing is skipped
under a CI marker (`isCurrent`, `render-plan.ts` 74–84); removal is by name, never of what the model still produces
(`render-plan.ts` 87–105). II, for a re-run — temporary then rename (`render-plan.ts` 113–124), write-if-different
(180–191). III — the record is two comment lines; no manifest, no setting. V — every criterion AC-S11-1 to -17
but -15 has an example that fails without the behaviour (pass 1's table, with T009–T013's additions); -15 is the
demo's. VII — a failure is reported as itself, once (`render-session.ts` 53–62, 169–187; `render-plan.ts` 137–138,
156–165), short of T014 and T015. VIII — the renderer line is additive and an SVG without it is redrawn once.
XIII — no wall-clock assertion; the stand-in is validated by the real runs above and by the demo. XIV — fakes in
the test tree, no mocking framework (`tests/render_fixture.py`, `tests/test_render_failures.py`).

**Not claimed.** The slice does not touch how an application starts, so no `smoke` run is owed; no row of the
convergence map moves (`make -f delivery/Makefile check-convergence` run at this commit). The `.ts` files are run
under `tsx` by the tests and are not type-checked by a compiler: the event-model tooling carries none. The render
tests skip on Windows, saying why.
