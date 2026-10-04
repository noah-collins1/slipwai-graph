"""The Makefile targets the event profile adds: the model's gate, and its two renderings.

Two renderings, because they have different properties and a project needs both. `make model` draws the
Mermaid diagrams, the README's segments and the browsable page, and drives a headless browser to do it —
so nothing browser-free can prove its output current, none of it is committed, and `make verify` does not
include it. `make model-drawio` writes one draw.io canvas, which is arithmetic and a string: no browser, no
account, no network. So it *is* committed, and `check-drawio` regenerates it in memory and compares on
every commit, inside `verify`. `check-model` — the model's own validation and its links to the code — is a
different question from whether a drawing is current, and stays exactly as it is.
"""
from __future__ import annotations

# The model tooling's install is one file target, in the root's pattern (`node_modules/.package-lock.json`, see
# `shared_packages.py`): npm writes that marker at the end of a successful install, so it is newer than both
# manifests exactly when the tree was installed from them. Every target that runs the pipeline names it as a
# prerequisite rather than installing inside its own recipe, because make runs a shared file target once — under
# `-j` four recipes each running an install would be four writers on one tree. `npm ci`, not `npm install`: it
# installs only what the committed lock says and refuses a manifest and lock that disagree, where `install` would
# rewrite a tracked file under a gate. `MODEL_INSTALLED` is set by the recipe that installed, and read when
# `check-drawio`'s recipe is expanded, which make does after its prerequisites: so the line saying the install was
# skipped is said only where it is true. `$(eval)` is GNU Make 3.80's.
MODEL_DIR = "scripts/event-model"
MARKER = f"{MODEL_DIR}/node_modules/.package-lock.json"
INSTALL = f"npm --prefix {MODEL_DIR} ci --no-audit --no-fund --loglevel=error"
SKIPPED = f"check-drawio: the model tooling matches {MODEL_DIR}/package-lock.json; not reinstalled"
# tsx's own entry point, run by `node`, rather than `node_modules/.bin/tsx`: that is npm's POSIX shim, which a
# native Windows `make` cannot run (`'scripts' is not recognized as an internal or external command`), and it
# was the one gate recipe `make verify` failed on there. The shim runs this same file everywhere else, and the
# exact `tsx` pin in `scripts/event-model/package.json` is what keeps the path from moving under it.
TSX = "node scripts/event-model/node_modules/tsx/dist/cli.mjs"

MODEL_TARGETS = f"""
{MARKER}: {MODEL_DIR}/package.json {MODEL_DIR}/package-lock.json
\t{INSTALL}
\t$(eval MODEL_INSTALLED := yes)

.PHONY: check-model
check-model: ## Validate the global event model and its links to implemented code
\tpython3 scripts/event-model/check.py

.PHONY: model
model: {MARKER} ## Regenerate the event-model diagrams and browsable page from model.yaml (needs Node; PNG=1 for a raster copy; MERMAID_PUPPETEER_CONFIG=<json> where Chromium cannot sandbox)
\t{TSX} scripts/event-model/render.ts

.PHONY: model-drawio
model-drawio: {MARKER} ## Write the committed draw.io canvas, docs/event-model/model.drawio, from model.yaml (needs Node, no browser)
\t{TSX} scripts/event-model/render-drawio.ts

.PHONY: check-drawio
check-drawio: {MARKER} ## Fail when docs/event-model/model.drawio is missing or no longer matches model.yaml
\t@$(if $(MODEL_INSTALLED),true,echo '{SKIPPED}')
\t{TSX} scripts/event-model/render-drawio.ts --check

.PHONY: model-drawio-test
model-drawio-test: {MARKER} ## Run the canvas planner's and serialiser's own tests — no browser, no network
\t{TSX} --test scripts/event-model/board-plan.test.ts scripts/event-model/drawio.test.ts
"""

# What the event profile adds to `verify`, after `test`: the model's validation, then the canvas's currency.
MODEL_GATES = " check-model check-drawio"


def model_targets(event: bool) -> str:
    """The block, or nothing: a project without the event profile has no model to draw."""
    return MODEL_TARGETS if event else ""
