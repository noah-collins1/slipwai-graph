"""A failure whose cause is the browser is said once, as the browser (S11-render-once, T023; AC-S11-24).

A browser that stops mid-run, one that cannot start for want of a sandbox, and one whose files are missing from the
install each leave as lines about the browser and blame no diagram. The stand-in disconnects on the Nth draw
(`STAND_IN_DISCONNECT`) and refuses to launch with the message a real Chromium and Puppeteer gave
(`STAND_IN_LAUNCH_FAILS`).
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from render_fixture import (
    CLOSE_FAILS_VARIABLE,
    DISCONNECT_VARIABLE,
    IS_WINDOWS,
    LAUNCH_FAILS_VARIABLE,
    MODEL_DIR,
    WINDOWS_SKIP,
    RenderCase,
)

NAMES = [f"Do thing {i}" for i in range(1, 6)]

NO_SANDBOX = (
    "Failed to launch the browser process:  Code: null\n\nstderr:\n[1003/164646.263911:FATAL:content/browser/"
    "zygote_host/zygote_host_impl_linux.cc:129] No usable sandbox! If you are running on Ubuntu 23.10+ or another "
    "Linux distro that has disabled unprivileged user namespaces with AppArmor, see https://example.invalid. If you "
    "want to live dangerously and need an immediate workaround, you can try using --no-sandbox.\n\n"
    "TROUBLESHOOTING: https://pptr.dev/troubleshooting\n"
)
NO_BROWSER = (
    "Could not find chrome-headless-shell (ver. 154.0.8037.57). This can occur if either\n"
    " 1. you did not perform an installation before running the script or\n"
    " 2. your cache path is incorrectly configured (which is: /home/someone/.cache/puppeteer).\n"
    "For (2), check out our guide on configuring puppeteer at https://pptr.dev/guides/configuration."
)
CONFIG_VARIABLE = "MERMAID_PUPPETEER_CONFIG"


def render_lines(stderr: str) -> list[str]:
    return [line for line in stderr.splitlines() if line.startswith("render:")]


@unittest.skipIf(IS_WINDOWS, WINDOWS_SKIP)
class BrowserTest(RenderCase):
    def svgs(self, repo: Path) -> list[str]:
        return sorted(str(p.relative_to(repo / MODEL_DIR)) for p in (repo / MODEL_DIR).rglob("*.svg"))

    def test_e24_a_browser_that_stops_mid_window_is_one_line_about_the_browser_and_blames_no_diagram(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, NAMES)  # nine diagrams: the timeline and three segments, then the slices
            done = self.run_model(repo, **{DISCONNECT_VARIABLE: "5", CLOSE_FAILS_VARIABLE: "1"})
            self.assertNotEqual(done.returncode, 0)
            lines = render_lines(done.stderr)
            self.assertEqual(len(lines), 1, done.stderr)
            self.assertTrue(lines[0].startswith("render: the browser stopped"), lines)
            self.assertNotIn("could not draw", done.stderr)
            self.assertNotIn("Connection closed.\nrender:", done.stderr)
            self.assertEqual(self.svgs(repo), ["model.svg", *(f"segments/model-{n}.svg" for n in (1, 2, 3))],
                             "the window that finished is written, the one that stopped is not")
            self.assertEqual(list((repo / MODEL_DIR).rglob(".tmp-*")), [])
            log = self.model_log_of(repo)
            self.assertEqual((log.sessions, log.closes), (1, 1), "the browser was let go of")

    def test_e24_a_browser_that_stops_while_the_png_is_drawn_is_the_browser_and_not_the_png(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, NAMES[:1])
            self.model_log(repo)
            done = self.run_model(repo, PNG="1", **{DISCONNECT_VARIABLE: "1"})
            self.assertNotEqual(done.returncode, 0)
            lines = render_lines(done.stderr)
            self.assertEqual(len(lines), 1, done.stderr)
            self.assertTrue(lines[0].startswith("render: the browser stopped"), lines)
            self.assertFalse((repo / MODEL_DIR / "model.png").exists())

    def test_e24_a_launch_that_found_no_usable_sandbox_and_no_config_names_the_variable_whoever_runs_it(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, NAMES[:1])
            done = self.run_model(repo, **{LAUNCH_FAILS_VARIABLE: NO_SANDBOX})
            self.assertNotEqual(done.returncode, 0)
            self.assertEqual(done.stderr.count("MERMAID_PUPPETEER_CONFIG"), 1, done.stderr)
            self.assertIn("render: could not start the browser: Failed to launch", done.stderr)
            self.assertNotIn("could not draw", done.stderr)

    def test_e24_with_a_config_given_a_sandbox_failure_is_not_given_the_advice(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, NAMES[:1])
            config = Path(directory) / "puppeteer.json"
            config.write_text("{}")
            done = self.run_model(repo, **{LAUNCH_FAILS_VARIABLE: NO_SANDBOX, CONFIG_VARIABLE: str(config)})
            self.assertNotEqual(done.returncode, 0)
            self.assertNotIn("Point MERMAID_PUPPETEER_CONFIG", done.stderr)

    def test_e24_a_browser_missing_from_the_install_says_to_delete_the_prefix_and_run_again(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, NAMES[:1])
            done = self.run_model(repo, **{LAUNCH_FAILS_VARIABLE: NO_BROWSER})
            self.assertNotEqual(done.returncode, 0)
            advice = [line for line in render_lines(done.stderr) if "scripts/event-model/.mermaid-cli" in line]
            self.assertEqual(len(advice), 1, done.stderr)
            self.assertIn("delete", advice[0])
            self.assertIn("run again", advice[0])
            self.assertIn("render: could not start the browser: Could not find chrome-headless-shell", done.stderr)

    def test_e24_a_launch_failure_with_neither_message_is_one_line_and_no_advice(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory, NAMES[:1])
            done = self.run_model(repo, **{LAUNCH_FAILS_VARIABLE: "Failed to launch: something else"})
            self.assertEqual(len(render_lines(done.stderr)), 1, done.stderr)
            self.assertNotIn("MERMAID_PUPPETEER_CONFIG", done.stderr)
            self.assertNotIn(".mermaid-cli", done.stderr)


if __name__ == "__main__":
    unittest.main()
