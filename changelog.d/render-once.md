PATCH

**`make model` draws through one browser, and only the diagrams whose source or renderer changed.** It started
a browser per diagram and redrew every one on every run — twenty-five browsers for a model of sixteen slices,
about sixteen seconds. It now opens one browser session per run, on the first diagram it has to draw, draws up
to four at a time in it, and closes it on every path, success or failure; a run with nothing to draw opens none.
A diagram is left when its SVG carries the stamp of the Mermaid the model produces now and the renderer that
draws it (the installed mermaid-cli, Mermaid and Puppeteer versions, the drawing scripts and the Puppeteer config's
bytes), and ends `</svg>`; under a CI marker (`CI`, `GITHUB_ACTIONS`, `GITLAB_CI`) every diagram is drawn,
as before. A file reaches its name finished or not at all: a failed draw leaves the earlier file, names the
diagram and exits non-zero. What the model no longer produces is removed by name (never through a link: `segments` or `slices` that is a link or a file is removed as itself and a directory made, an entry at a name the model produces that is not a regular file is removed and drawn afresh, and each thing removed from the two directories is printed as `removed <path>`), and the Mermaid sources, the
page and the README block are written only where their bytes differ, one `wrote` line each. The run closes by
saying what it did, for example `model: 16 slices, 3 of 25 diagrams drawn, 22 unchanged.` and, when nothing
changed, `model: 16 slices, 0 of 25 diagrams drawn, 25 unchanged; no browser started.` The drawn SVGs are the
same bytes as before, below one added comment line. To force a redraw, delete a diagram, or `docs/event-model/model.svg`, `segments/` and `slices/`: there is no setting and no flag.

**Catch-up.** Nothing is asked of a repository that left `render.ts` as generated. After `slipwai migrate` its first
`make model` redraws every diagram once, and since the output is ignored nothing committed changes; a repository that
removed the ignore lines and commits its diagrams sees the second comment line in each SVG, once.
A repository that edited `render.ts` may meet a conflict there when `slipwai migrate` carries it forward, because the
renderer's pin, width and browser handling moved to `render-session.ts`.
