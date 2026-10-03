# Research: S11-render-once

Each statement about a dependency names what it was read from. The install read is mermaid-cli 11.16.0 with
mermaid 11.17.2 and puppeteer 25.12.0, as `make model` fetched them on 2026-10-03 into a project generated for
the purpose (`/tmp/s11-measure/fx/fx/scripts/event-model/.mermaid-cli/node_modules/`); the implementer re-reads
each in the install a test or the demo makes.

1. **mermaid-cli exports a function that draws one diagram in a browser it is given.**
   `@mermaid-js/mermaid-cli/package.json`: `"exports": {".": {"default": "./src/index.js"}}`, `"type": "module"`.
   `src/index.js` ends `export { run, renderMermaid, cli, error }`; `renderMermaid(browser, definition,
   outputFormat, { viewport, backgroundColor, … })` opens a page in the given browser, draws, closes the page and
   returns `{ data: Uint8Array }` (lines 414–680 of that file). **Decision**: the real session imports that file
   from the local prefix and calls `renderMermaid`; it does not spawn `mmdc`. **Alternative rejected**: `mmdc`
   with a Markdown input of many diagrams (one browser, but output names are the tool's, and a failure does not
   say which diagram).
2. **What `mmdc --width 2400` passes, so the bytes stay today's.** `src/index.js` lines 349–384: the CLI launches
   with `{ headless: "shell", …the JSON of --puppeteerConfigFile }` and draws with `viewport: { width, height:
   600 (its default), deviceScaleFactor: 1 }` and `backgroundColor: "white"`. The PNG call today passes
   `--backgroundColor white`, the same value. **Measured**: 25 diagrams drawn through `renderMermaid` with those
   options were byte for byte what `mmdc` wrote for the same sources (`/tmp/s11-measure/spike.mjs`, 25 of 25).
3. **Puppeteer is reached the way mermaid-cli reaches it.** `src/index.js` line 8: `import puppeteer from
   "puppeteer"`; `puppeteer/package.json` `"exports"."."."import"` is `./lib/puppeteer/puppeteer.js`.
   **Decision**: resolve both packages from the prefix (`createRequire` on the prefix's `package.json`, or the
   two paths joined), so the session uses the one install the patcher patched. Nothing is added to
   `scripts/event-model/package.json`: the browser stays out of every `npm install` the project makes, as the
   comment at the head of `render.ts` says it must.
4. **The stand-in renderer for the suite.** A test writes, under the fixture's
   `scripts/event-model/.mermaid-cli/node_modules/`: `@mermaid-js/mermaid-cli` (`package.json` with a version and
   the same `exports`; `src/index.js` exporting `renderMermaid` that appends a line to a log named by an
   environment variable and returns a small SVG, or throws for a source containing a marker the test chose),
   `puppeteer` (`launch(options)` appends a line with its options to the same log and returns an object with
   `close()`), `mermaid` (`package.json` with a version, and an ESM chunk carrying the text the patcher accepts as
   already fixed — read `patch-mermaid-swimlanes.ts`, `applySwimlaneFix` and `esmChunks`, for what that is), and
   `.bin/mmdc` (a script doing what one `renderMermaid` call does, so the pin tests pass before the change and
   after, unedited). It implements the installed renderer's real exports; it is a fake in the test tree, not a
   mocking framework (AGENTS.md, *Tests written here*). The demo is what validates it against the real renderer.
   How a test gets a generated event-modelling project with `scripts/event-model` installed:
   `tests/test_event_model.py`, `test_the_two_bands_are_namespaced_independently`.
5. **The time.** Measured on this machine (12 cores, Node 22.22.1), warm tree, the fixture's three changed
   diagrams: importing the two packages 0.12 s, launch 0.07 s, three draws one after another 0.88 s, four pages at
   a time 0.48–0.52 s, close 0.02 s; the recipe's install step 0.29 s; `tsx` starting and loading the model
   0.41 s. Sum with four pages at a time: about 1.4 s; one at a time: about 1.8 s. 25 diagrams: 6.7 s one at a
   time, 2.9–3.2 s four or eight at a time, against 15.95 s today. **Decision**: the session draws up to four
   pages at a time in the one browser. Bytes are unchanged by it (25 of 25 identical at every width tried). Each
   file is still written and reported in the model's order.
6. **How the toolkit's scripts reach a project.** *Assumed until read*: `assets/toolkit/scripts/event-model/` is
   copied whole for the event-modelling profile (`src/slipwai/project/event_model.py`), and
   `tests/test_monorepos.py` line 238 names scripts it expects. The first cycle reads both and adds the two new
   files wherever a list names its neighbours.
7. **The temporary file.** Every drawn file's temporary sits in `docs/event-model/slices/`, which
   `src/slipwai/project/gitignore.py` already ignores and which is the same directory tree as every output, so
   the rename never crosses a filesystem in a normal checkout. Its name cannot be one the model produces (a
   leading dot and a suffix the plan's code fixes), so R4 removes one left behind by a killed run.
8. **Chromium on this machine has no usable sandbox** (Ubuntu's AppArmor user-namespace restriction; the first
   measured run failed with *No usable sandbox*). The demo sets the product's documented
   `MERMAID_PUPPETEER_CONFIG` to a JSON holding `--no-sandbox` and `--disable-dev-shm-usage`, and the quickstart
   says so. The browser is the one in `~/.cache/puppeteer` (chrome-headless-shell 154).
