"""A failure that is not one diagram's draw is reported as itself, once (S11-render-once, T010; AC-S11-8, AC-S11-16).

The browser that will not start, the PNG, a Puppeteer config that cannot be read, and a file that cannot be written
each leave as one `render:` line naming what failed. The root-launch line is held through a probe script written
into the project: it imports `render-session.ts`, claims to be root, and gives `lazySession` an `open` that throws,
a fake in the test tree standing where Chromium would refuse to start.
"""
from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from render_fixture import (
    CLOSE_FAILS_VARIABLE,
    EVENT_MODEL,
    FAIL_MARKER,
    IS_WINDOWS,
    LAUNCH_FAILS_VARIABLE,
    MODEL_DIR,
    PNG_FAILS_VARIABLE,
    WINDOWS_SKIP,
    RenderCase,
    render_env,
)

# Generates nothing itself: the project comes from `RenderCase.project`, whose declaration the join carries.
TEST_SELECTION: dict[str, object] = {}

ROOT_LINE = "render: running as root, and Chromium will not start without --no-sandbox."
NAMES = [f"Do thing {i}" for i in range(1, 5)]

PROBE_LOAD = """import { BrowserError, lazySession } from './render-session.ts';
process.getuid = () => 0;
const message = 'render: could not load puppeteer from the prefix';
const session = lazySession(async () => { throw new BrowserError(message); });
try { await session.draw('x', 'svg'); } catch (error) { console.log((error as Error).message); }
await session.close();
"""

PROBE = """import { lazySession } from './render-session.ts';
process.getuid = () => 0;
const session = lazySession(async () => { throw new Error('stand-in: no sandbox'); });
const outcomes: string[] = [];
for (let n = 0; n < 3; n += 1) {
  try { await session.draw('x', 'svg'); } catch (error) { outcomes.push((error as Error).message); }
}
await session.close();
console.log(JSON.stringify(outcomes));
"""


def render_lines(stderr: str) -> list[str]:
    return [line for line in stderr.splitlines() if line.startswith("render:")]


@unittest.skipIf(IS_WINDOWS, WINDOWS_SKIP)
class FailuresTest(RenderCase):
    def test_e8_a_browser_that_cannot_start_is_one_line_about_the_browser_and_blames_no_diagram(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, NAMES)
            done = self.run_model(repo, **{LAUNCH_FAILS_VARIABLE: "1"})
            self.assertNotEqual(done.returncode, 0)
            lines = render_lines(done.stderr)
            self.assertEqual(lines, ["render: could not start the browser: Failed to launch the browser process"])
            self.assertNotIn("could not draw", done.stderr)
            log = self.model_log_of(repo)
            self.assertEqual((log.sessions, log.draws, log.closes), (0, 0, 0), "no close on a session never opened")

    def test_e8_a_draw_that_failed_and_a_browser_that_will_not_close_are_both_said_the_draw_first(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, [*NAMES[:1], f"Bad {FAIL_MARKER}"])
            done = self.run_model(repo, **{CLOSE_FAILS_VARIABLE: "1"})
            self.assertNotEqual(done.returncode, 0)
            lines = render_lines(done.stderr)
            self.assertTrue(lines[0].startswith("render: could not draw "), lines)
            self.assertTrue(any("docs/event-model/slices/S2.svg: " in line for line in lines), lines)
            self.assertEqual(lines[-1], "render: could not close the browser: browser would not close")
            self.assertEqual(sum("could not close" in line for line in lines), 1)

    def test_e8_a_browser_that_will_not_close_after_every_draw_succeeded_is_one_line_and_the_files_stay(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, NAMES[:2])
            done = self.run_model(repo, **{CLOSE_FAILS_VARIABLE: "1"})
            self.assertNotEqual(done.returncode, 0)
            self.assertEqual(
                render_lines(done.stderr), ["render: could not close the browser: browser would not close"])
            self.assertTrue((repo / MODEL_DIR / "slices" / "S1.svg").exists())
            self.assertTrue((repo / MODEL_DIR / "model.svg").exists())

    def test_e8_a_package_that_cannot_be_loaded_from_the_prefix_is_named_and_is_not_a_browser_that_would_not_start(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, NAMES[:1])
            (repo / EVENT_MODEL / ".mermaid-cli/node_modules/puppeteer/src/index.js").unlink()
            done = self.run_model(repo, MERMAID_PUPPETEER_CONFIG="")
            self.assertNotEqual(done.returncode, 0)
            lines = render_lines(done.stderr)
            self.assertEqual(len(lines), 1, done.stderr)
            self.assertTrue(lines[0].startswith("render: could not load puppeteer from "), lines)
            self.assertIn(".mermaid-cli", lines[0])
            self.assertNotIn("could not start the browser", done.stderr)
            self.assertNotIn(ROOT_LINE, done.stderr)

    def test_e8_a_png_that_cannot_be_drawn_names_the_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, NAMES[:1])
            done = self.run_model(repo, PNG="1", **{PNG_FAILS_VARIABLE: "1"})
            self.assertNotEqual(done.returncode, 0)
            self.assertEqual(render_lines(done.stderr), [
                "render: could not draw docs/event-model/model.png: png refused"])
            self.assertFalse((repo / MODEL_DIR / "model.png").exists())
            self.assertEqual(self.model_log_of(repo).closes, 1)

    def test_e8_a_puppeteer_config_that_cannot_be_read_names_the_variable_before_anything_is_drawn(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, NAMES[:1])
            done = self.run_model(repo, MERMAID_PUPPETEER_CONFIG="/nonexistent.json")
            self.assertNotEqual(done.returncode, 0)
            lines = render_lines(done.stderr)
            self.assertEqual(len(lines), 1, done.stderr)
            self.assertTrue(
                lines[0].startswith("render: could not read MERMAID_PUPPETEER_CONFIG (/nonexistent.json): "))
            self.assertEqual(self.model_log_of(repo).sessions, 0)

    def test_e8_a_puppeteer_config_that_is_not_json_names_the_variable_once(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, NAMES[:1])
            config = Path(directory) / "puppeteer.json"
            config.write_text("{not json")
            done = self.run_model(repo, MERMAID_PUPPETEER_CONFIG=str(config))
            self.assertNotEqual(done.returncode, 0)
            lines = render_lines(done.stderr)
            self.assertEqual(len(lines), 1, done.stderr)
            self.assertIn(f"MERMAID_PUPPETEER_CONFIG ({config}) is not valid JSON", lines[0])

    def test_e8_an_installed_package_whose_manifest_is_unreadable_is_named(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, NAMES[:1])
            manifest = repo / EVENT_MODEL / ".mermaid-cli/node_modules/@mermaid-js/mermaid-cli/package.json"
            manifest.write_text("{")
            done = self.run_model(repo)
            self.assertNotEqual(done.returncode, 0)
            lines = render_lines(done.stderr)
            self.assertEqual(len(lines), 1, done.stderr)
            self.assertIn(f"could not read the installed version in {manifest}", lines[0])

    def probe(self, repo: Path, source: str = PROBE, **env: str) -> subprocess.CompletedProcess[str]:
        self.model_log(repo)  # the project's own run, which installs the TypeScript runner the probe needs
        script = repo / EVENT_MODEL / "probe-root.mts"
        script.write_text(source)
        return subprocess.run(
            ["node", str(repo / EVENT_MODEL / "node_modules/tsx/dist/cli.mjs"), str(script)],
            cwd=repo, text=True, capture_output=True, env=render_env(**env),
        )

    def test_e16_run_as_root_with_no_config_the_launch_failure_says_which_variable_fixes_it_once(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, NAMES[:1])
            done = self.probe(repo, MERMAID_PUPPETEER_CONFIG="")
            self.assertEqual(done.returncode, 0, done.stderr)
            self.assertEqual(done.stderr.count(ROOT_LINE), 1, "once, however many draws were in flight")
            self.assertIn("MERMAID_PUPPETEER_CONFIG", done.stderr)
            self.assertEqual(done.stdout.strip(),
                             '["render: could not start the browser: stand-in: no sandbox",'
                             '"render: could not start the browser: stand-in: no sandbox",'
                             '"render: could not start the browser: stand-in: no sandbox"]')

    def test_e16_run_as_root_a_failure_that_is_not_the_launch_does_not_get_the_root_advice(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, NAMES[:1])
            done = self.probe(repo, PROBE_LOAD, MERMAID_PUPPETEER_CONFIG="")
            self.assertEqual(done.returncode, 0, done.stderr)
            self.assertNotIn(ROOT_LINE, done.stderr)
            self.assertEqual(done.stdout.strip(), "render: could not load puppeteer from the prefix")

    def test_e16_run_as_root_with_a_config_given_the_root_line_is_not_said(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, NAMES[:1])
            config = Path(directory) / "puppeteer.json"
            config.write_text("{}")
            done = self.probe(repo, MERMAID_PUPPETEER_CONFIG=str(config))
            self.assertEqual(done.returncode, 0, done.stderr)
            self.assertNotIn(ROOT_LINE, done.stderr)
            self.assertIn("could not start the browser: stand-in: no sandbox", done.stdout)


if __name__ == "__main__":
    unittest.main()
