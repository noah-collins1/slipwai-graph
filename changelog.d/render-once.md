PATCH

**`make model` draws every diagram through one browser, opened on the first diagram it has to draw.** It started
a browser per diagram — twenty-five for a model of sixteen slices, about sixteen seconds. It now opens one
browser session per run, draws up to four diagrams at a time in it, and closes it on every path, success or
failure; a run that has nothing to draw opens none. The drawn SVGs are the same bytes as before.

**Catch-up.** Nothing is asked of a repository already generated: `slipwai migrate` brings the scripts, and the
next `make model` fetches nothing new.
