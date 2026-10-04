"""Shared by the render tests: a generated event-modelling project whose renderer is a stand-in.

The stand-in sits where `make model` installs mermaid-cli (`scripts/event-model/.mermaid-cli/node_modules/`)
and carries both shapes the renderer can be reached by: `.bin/mmdc`, one process per diagram, and the module
packages `@mermaid-js/mermaid-cli` (`renderMermaid`) and `puppeteer` (`launch`). Every call appends one JSON
line to the file named by `STAND_IN_LOG`, so a test counts sessions and draws from that log and never from
what the run printed. It is a fake written in the test tree, validated against the real renderer by the demo.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import signal
import stat
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from support import FactoryTestCase

LOG_VARIABLE = "STAND_IN_LOG"
LAUNCH_FAILS_VARIABLE = "STAND_IN_LAUNCH_FAILS"
"""Set this and `puppeteer.launch` throws, as a browser that cannot be started does."""
PNG_FAILS_VARIABLE = "STAND_IN_PNG_FAILS"
"""Set this and every PNG draw throws `png refused`, whatever the source; an SVG draws as always."""
CLOSE_FAILS_VARIABLE = "STAND_IN_CLOSE_FAILS"
"""Set this and the browser's `close` throws, as a browser that will not shut down does."""
REWRITE_CONFIG_VARIABLE = "STAND_IN_REWRITE_CONFIG"
"""Set this to some text and loading the stand-in's mermaid-cli, which a run does after it has keyed the Puppeteer
config and before it launches, overwrites the file `MERMAID_PUPPETEER_CONFIG` names with that text."""
FAIL_MARKER = "STAND-IN-DRAW-FAILS"
"""Put this in a slice's name and the draw of every diagram whose source carries it throws."""

CI_MARKERS = ("CI", "GITHUB_ACTIONS", "GITLAB_CI")
"""The variables under which `render.ts` draws every diagram (AC-S11-5)."""

EVENT_MODEL = Path("scripts/event-model")
MODEL_DIR = Path("docs/event-model")
IS_WINDOWS = os.name == "nt"
WINDOWS_SKIP = (
    "the tests generate a project through the `./slipwai` launcher, a shebang script, and run its `make model`"
)

# The text `applySwimlaneFix` reads as "already fixed", so the patcher leaves the stand-in alone.
_ALREADY_FIXED = "function findSwimlaneByNamespace(swimlanes, namespace, boundaryMin, boundaryMax) {}\n"

_LOG_AND_DRAW = f"""
const fs = require('node:fs');
const crypto = require('node:crypto');
const FAIL = {FAIL_MARKER!r};
function log(entry) {{
  const path = process.env.{LOG_VARIABLE};
  if (path) fs.appendFileSync(path, JSON.stringify(entry) + '\\n');
}}
function sha(text) {{ return crypto.createHash('sha256').update(text).digest('hex'); }}
function draw(definition, format) {{
  if (format === 'png' && process.env.{PNG_FAILS_VARIABLE}) throw new Error('png refused');
  if (definition.includes(FAIL)) throw new Error('stand-in: draw refused (' + FAIL + ')');
  if (format === 'png') return Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a, 0, 0, 0, 0]);
  return Buffer.from('<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"><desc>' + sha(definition)
    + '</desc></svg>');
}}
"""

MMDC = "#!/usr/bin/env node\n" + _LOG_AND_DRAW + """
const path = require('node:path');
function chunkFixed() {
  const chunk = path.join(__dirname, '..', 'mermaid', 'dist', 'chunks', 'mermaid.esm', 'chunk-stand-in.mjs');
  return fs.readFileSync(chunk, 'utf8').includes('boundaryMin');
}
const argv = process.argv.slice(2);
const value = (flag) => { const at = argv.indexOf(flag); return at < 0 ? undefined : argv[at + 1]; };
const input = value('--input');
const output = value('--output');
const config = value('--puppeteerConfigFile');
// One process is one browser session and one draw: that is what this shape means today.
log({ event: 'session', via: 'mmdc', chunk_fixed: chunkFixed(),
  options: config ? JSON.parse(fs.readFileSync(config, 'utf8')) : {} });
const definition = fs.readFileSync(input, 'utf8');
log({ event: 'draw', via: 'mmdc', input, output, source_sha256: sha(definition), width: Number(value('--width')),
  background: value('--backgroundColor') || 'white' });
try {
  fs.writeFileSync(output, draw(definition, output.endsWith('.png') ? 'png' : 'svg'));
} catch (error) {
  console.error(String(error.message));
  process.exit(1);
}
log({ event: 'close', via: 'mmdc' });
"""

_MODULE_EXPORTS = {"type": "module", "exports": {".": {"default": "./src/index.js", "import": "./src/index.js"}}}

MERMAID_CLI_MODULE = """import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
""" + _LOG_AND_DRAW + """
if (process.env.__REWRITE__ && process.env.MERMAID_PUPPETEER_CONFIG) {
  fs.writeFileSync(process.env.MERMAID_PUPPETEER_CONFIG, process.env.__REWRITE__);
}
export async function renderMermaid(browser, definition, outputFormat, opts = {}) {
  log({ event: 'draw', via: 'module', format: outputFormat, source_sha256: sha(definition),
    width: opts.viewport && opts.viewport.width, background: opts.backgroundColor });
  return { data: new Uint8Array(draw(definition, outputFormat)), title: null, desc: null };
}
export async function run() { throw new Error('stand-in: run is not provided'); }
export async function cli() { throw new Error('stand-in: cli is not provided'); }
export function error() { throw new Error('stand-in: error is not provided'); }
""".replace("__REWRITE__", REWRITE_CONFIG_VARIABLE)

PUPPETEER_MODULE = """import fs from 'node:fs';
function chunkFixed() {
  const chunk = new URL('../../mermaid/dist/chunks/mermaid.esm/chunk-stand-in.mjs', import.meta.url);
  return fs.readFileSync(chunk, 'utf8').includes('boundaryMin');
}
function log(entry) {
  const path = process.env.__LOG__;
  if (path) fs.appendFileSync(path, JSON.stringify(entry) + '\\n');
}
export default {
  async launch(options = {}) {
    if (process.env.__LAUNCH__) throw new Error('Failed to launch the browser process');
    log({ event: 'session', via: 'module', chunk_fixed: chunkFixed(), options });
    return { async close() {
      log({ event: 'close', via: 'module' });
      if (process.env.__CLOSE__) throw new Error('browser would not close');
    } };
  },
};
""".replace("__LOG__", LOG_VARIABLE).replace("__LAUNCH__", LAUNCH_FAILS_VARIABLE).replace(
    "__CLOSE__", CLOSE_FAILS_VARIABLE)


def broken_swimlane_chunk(project: Path) -> str:
    """A chunk in the broken shape of mermaid#7925, built from the patcher's own text, so it is the patcher's to fix."""
    patcher = (project / EVENT_MODEL / "patch-mermaid-swimlanes.ts").read_text()
    parts = [re.search(rf"const {name} = `(.*?)`;", patcher, re.S) for name in
             ("BROKEN_FIND", "BROKEN_CALCULATE", "BROKEN_CREATE")]
    return "\n".join(match.group(1) for match in parts if match) + "\n"


def install_stand_in(project: Path, *, unpatched: bool = False) -> None:
    """Write the stand-in renderer where `render.ts` looks for an installed one.

    `unpatched` leaves mermaid in the shape the swimlane patcher has to fix, so the stand-in can say at launch
    whether the patch had already run."""
    prefix = project / EVENT_MODEL / ".mermaid-cli"
    modules = prefix / "node_modules"
    prefix.mkdir(parents=True, exist_ok=True)
    (prefix / "package.json").write_text('{"name":"event-model-mermaid-cli","private":true}\n')

    def package(name: str, files: dict[str, str], manifest: Mapping[str, object]) -> None:
        root = modules / name
        for relative, text in files.items():
            (root / relative).parent.mkdir(parents=True, exist_ok=True)
            (root / relative).write_text(text)
        (root / "package.json").write_text(json.dumps({"name": name, "version": "0.0.0-stand-in", **manifest}))

    package("@mermaid-js/mermaid-cli", {"src/index.js": MERMAID_CLI_MODULE}, _MODULE_EXPORTS)
    package("puppeteer", {"src/index.js": PUPPETEER_MODULE}, _MODULE_EXPORTS)
    chunk = broken_swimlane_chunk(project) if unpatched else _ALREADY_FIXED
    package("mermaid", {"dist/chunks/mermaid.esm/chunk-stand-in.mjs": chunk}, {})
    bin_dir = modules / ".bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    mmdc = bin_dir / "mmdc"
    mmdc.write_text(MMDC)
    mmdc.chmod(mmdc.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def slice_yaml(index: int, name: str | None = None) -> str:
    """One state-change slice of three frames that reads no other slice."""
    return (
        f"  - id: S{index}\n    name: {name or f'Do thing {index}'}\n    pattern: state-change\n"
        f"    status: modelled\n    actor: Guest\n    stream: thing-{{thingId}}\n"
        f"    frames:\n      - {{type: ui, name: Screen{index}}}\n"
        f"      - {{type: cmd, name: Do{index}}}\n      - {{type: evt, name: Done{index}}}\n"
    )


def write_model(project: Path, slices: int | list[str]) -> None:
    """Rewrite `model.yaml` keeping its header. `slices` is a count, or the names of the slices wanted."""
    model = project / MODEL_DIR / "model.yaml"
    header = model.read_text().split("\nslices:")[0]
    names = [None] * slices if isinstance(slices, int) else slices
    body = "".join(slice_yaml(i + 1, name) for i, name in enumerate(names)) if names else " []\n"
    model.write_text(header + "\nslices:" + ("\n" + body if names else body))


@dataclass(frozen=True)
class RendererLog:
    """What the stand-in recorded: one entry per call, in order."""

    entries: list[dict[str, object]]

    @property
    def sessions(self) -> int:
        return sum(1 for entry in self.entries if entry["event"] == "session")

    @property
    def draws(self) -> int:
        return sum(1 for entry in self.entries if entry["event"] == "draw")

    @property
    def drawn_sources(self) -> list[str]:
        """SHA-256 of the Mermaid source of each draw, in order (what `sha256_of` gives for a `.mmd`)."""
        return [str(entry["source_sha256"]) for entry in self.entries if entry["event"] == "draw"]

    @property
    def png_draws(self) -> int:
        return sum(1 for entry in self.entries if entry["event"] == "draw" and entry.get("format") == "png")

    @property
    def closes(self) -> int:
        return sum(1 for entry in self.entries if entry["event"] == "close")

    @property
    def launch_options(self) -> list[object]:
        return [entry["options"] for entry in self.entries if entry["event"] == "session"]


def read_log(path: Path) -> RendererLog:
    if not path.exists():
        return RendererLog([])
    return RendererLog([json.loads(line) for line in path.read_text().splitlines() if line.strip()])


def render_env(**env: str) -> dict[str, str]:
    """The environment a render test's subprocess gets: the suite's own, without the CI markers it may run under
    and without any `PUPPETEER_` variable the machine sets (the renderer key reads them).

    A variable the test names in `env` is kept, so a test that wants one sets it and no other leaks in."""
    base = {key: value for key, value in os.environ.items()
            if key not in CI_MARKERS and not key.startswith("PUPPETEER_")}
    return {**base, **env}


def make_model(
    project: Path, log: Path | None = None, **env: str
) -> subprocess.CompletedProcess[str]:
    """`make model` through the project's own recipe (its npm install is the one network call)."""
    if log is not None:
        log.unlink(missing_ok=True)
        env[LOG_VARIABLE] = str(log)
    return subprocess.run(
        ["make", "model"], cwd=project, text=True, capture_output=True, env=render_env(**env)
    )


def make_model_within(project: Path, seconds: float, log: Path) -> subprocess.CompletedProcess[str] | None:
    """`make model` in a process group of its own, killed whole after `seconds`; `None` when it had to be.

    For a run that may hang (a FIFO where a file is read): a failing example ends, it does not stall the suite."""
    log.unlink(missing_ok=True)
    process = subprocess.Popen(
        ["make", "model"], cwd=project, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env=render_env(**{LOG_VARIABLE: str(log)}), start_new_session=True,
    )
    try:
        out, err = process.communicate(timeout=seconds)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.communicate()
        return None
    return subprocess.CompletedProcess(process.args, process.returncode, out, err)


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mmd_hashes(project: Path) -> dict[str, str]:
    """Every `.mmd` the run wrote, by path under `docs/event-model/`, with the SHA-256 of its bytes."""
    root = project / MODEL_DIR
    return {str(path.relative_to(root)): sha256_of(path) for path in sorted(root.rglob("*.mmd"))}


class RenderCase(FactoryTestCase):
    """A generated project with the stand-in installed, run through its own `make model`."""

    def project(self, directory: str, slices: int | list[str], name: str = "render-case") -> Path:
        repo = self.generate(directory, name)
        install_stand_in(repo)
        write_model(repo, slices)
        return repo

    def run_model(self, repo: Path, **env: str) -> subprocess.CompletedProcess[str]:
        return make_model(repo, repo.parent / "renderer.log", **env)

    def model_log(self, repo: Path, **env: str) -> RendererLog:
        """Run `make model`, require it to succeed, and return what the stand-in recorded for that run."""
        done = self.run_model(repo, **env)
        self.assertEqual(done.returncode, 0, done.stderr + done.stdout)
        return self.model_log_of(repo)

    def model_log_of(self, repo: Path) -> RendererLog:
        """What the stand-in recorded for the last run, whether it succeeded or not."""
        return read_log(repo.parent / "renderer.log")


def rename_frame(project: Path, old: str, new: str) -> None:
    """Rename one frame of the model (`Do7` to `Do7b`): the slice keeps its id and its three frames."""
    model = project / MODEL_DIR / "model.yaml"
    text = model.read_text()
    assert f"name: {old}}}" in text, old
    model.write_text(text.replace(f"name: {old}}}", f"name: {new}}}"))


def mtimes(project: Path) -> dict[str, int]:
    """Every file under `docs/event-model/` and the README, by path, with its modification time in nanoseconds."""
    files = [*(project / MODEL_DIR).rglob("*"), project / "README.md"]
    return {str(path.relative_to(project)): path.stat().st_mtime_ns for path in files if path.is_file()}


def wrote(done: subprocess.CompletedProcess[str]) -> list[str]:
    """The paths of the `wrote <path>` lines a run printed, in order."""
    return [line.split("wrote ", 1)[1] for line in done.stdout.splitlines() if line.strip().startswith("wrote ")]
