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
   (AC-S11-15, SC-004). One real browser start is confirmed by a means other than that line: after another
   one-frame edit, `strace -f -e trace=execve -o /tmp/s11-demo/exec.log make model`, then count the executions of
   the browser's binary whose arguments carry no `--type=` (Chromium starts its helper processes from the same
   binary with `--type=…`; the browser itself is the one without). Do not name a wrapper as `executablePath` in
   the Puppeteer config to count: the config's bytes are in the renderer key, so that run redraws all 25.
4. Remove slices `S15` and `S16` from the model, `make model` — `slices/S15.*` and `slices/S16.*` are gone, and so
   is `segments/model-8.*`, which the model no longer fills (the fixture packs two slices to a segment).
5. Truncate one SVG (cut bytes off its end — the drawing is one line, so cutting the last line removes it all),
   `make model` — that diagram is drawn again.
6. `PNG=1 make model` twice — `model.png` drawn both times.
7. `CI=true make model` — every diagram drawn, and the closing line says a CI marker is set.
8. Delete `docs/event-model/model.svg`, `segments/` and `slices/`, `make model` — every diagram drawn (the page's one sentence on redrawing everything, followed as written).

**Measured at the demo** (2026-10-03, `drive-hand`, cruise iteration 10, code at `dde4317`; numbers from
[demo-log.md](demo-log.md) and `demo/03-changed-slice-timings.txt`, `demo/04-strace-one-browser.txt`). Machine: Linux
x86_64, i5-12400, 12 cores, Node v22.22.1; `MERMAID_PUPPETEER_CONFIG` set as above; command `time make model`, the
whole recipe, `real`.

| Run | Wall time | Browsers |
|---|---|---|
| Before this slice (`render.ts` at `7226c2e^`), same model, renderer installed | 15.449 s | 25 |
| First run, renderer already installed, every diagram deleted | 4.397 s | 1 |
| First run in a fresh project (includes installing the renderer) | 11.068 s | 1 |
| **Changed slice, warm** (one frame of S7 renamed afresh each time; seven runs, in order) | **1.410, 1.460, 1.428, 1.440, 1.444, 1.399, 1.505 s** | 1 |
| Nothing changed (three runs) | 0.692, 0.691, 0.706 s | 0 |

SC-004 (under 2 seconds, one browser) held on every one of the seven; the browser count is `strace`'s — one
execution of `chrome-headless-shell` without `--type=` — not the run's own closing line.
