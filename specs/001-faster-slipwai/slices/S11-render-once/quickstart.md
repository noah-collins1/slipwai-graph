# Quickstart: S11-render-once — the demo

The actor is a developer in a generated project who changed one slice of the event model and runs `make model`.

**Seed** (from this checkout; nothing outside `/tmp` is written):

```sh
rm -rf /tmp/s11-demo && mkdir -p /tmp/s11-demo && cd /tmp/s11-demo
PYTHONPATH=/home/noahc/math/slipwai-graph/src python3 -m slipwai generate fx --profile event-modelling \
  --backend python --frontend none --target none --output /tmp/s11-demo/fx --skip-checks --no-init --no-install
cd /tmp/s11-demo/fx/fx
```

Then replace the `slices:` block of `docs/event-model/model.yaml` with 16 state-change slices of three frames
each (`ui`, `cmd`, `evt`), ids `S1` to `S16`, no slice reading another, default `render` settings (D69's
reference fixture).

Chromium has no usable sandbox on this machine, so every run below is made with the product's documented
variable: `echo '{"args": ["--no-sandbox", "--disable-dev-shm-usage"]}' > /tmp/s11-demo/pptr.json` and
`export MERMAID_PUPPETEER_CONFIG=/tmp/s11-demo/pptr.json`.

**Run, and what to expect:**

1. `time make model` — the first run. One browser; `model: 16 slices, 25 of 25 diagrams drawn, 0 unchanged.`
   Today this is 25 browsers and 15.95 s on this machine; no time is claimed, the number is written here.
2. `time make model` again — `model: 16 slices, 0 of 25 diagrams drawn, 25 unchanged; no browser started.` and no
   `wrote` line.
3. Rename one frame of `S7` in `model.yaml` (its `cmd`, say), then `time make model` — one browser;
   `model: 16 slices, 3 of 25 diagrams drawn, 22 unchanged.`; `wrote` lines for `model.mmd`, `model.svg`, S7's
   segment and S7's slice (`.mmd` and `.svg` each) and `model.html`; **the whole recipe under 2 seconds**
   (AC-S11-15, SC-004). One real browser start is confirmed by a means other than that line — for example
   `strace -f -e trace=execve -o /tmp/s11-demo/exec.log make model` after another one-frame edit, counting the
   `chrome-headless-shell` executions, or a wrapper named as `executablePath` in the Puppeteer config that logs
   each start.
4. Remove slice `S16` from the model, `make model` — `slices/S16.svg` and `S16.mmd` are gone, and so is a segment
   the model no longer fills.
5. Truncate one SVG (cut its last line), `make model` — that diagram is drawn again.
6. `PNG=1 make model` twice — `model.png` drawn both times.
7. `CI=true make model` — 25 of 25 drawn.

**Measured at the demo** (the hand writes these into its demo log; the host copies them here):

| Run | Machine | Command | Wall time | Browsers |
|---|---|---|---|---|
| Today, first run | this machine (12 cores, Node 22.22.1) | `make model` | 15.95 s | 25 |
| First run | | | | |
| Changed slice, warm | | | | |
| Nothing changed | | | | |
