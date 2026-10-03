"""When a diagram is left and when it is redrawn (S11-render-once, R2: the four conditions and the key).

Counts come from the stand-in's log. A condition is tested by spoiling one diagram's SVG on disk and seeing that
diagram, and only that diagram, drawn on the next run.
"""
from __future__ import annotations

import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from render_fixture import EVENT_MODEL, IS_WINDOWS, MODEL_DIR, WINDOWS_SKIP, RenderCase, sha256_of

SOURCE_LINE = re.compile(r"<!-- em-source-sha256: [0-9a-f]{64} -->")
RENDERER_LINE = re.compile(r"<!-- em-renderer-sha256: ([0-9a-f]{64}) -->")
ZEROS = "0" * 64


@unittest.skipIf(IS_WINDOWS, WINDOWS_SKIP)
class CurrentTest(RenderCase):
    def one_slice(self, directory: str) -> Path:
        repo = self.project(directory, 1)
        self.model_log(repo)
        return repo

    def only_the(self, repo: Path, relative: str, **env: str) -> None:
        """The next run draws exactly the diagram whose source is `relative` (a `.mmd` under the model dir)."""
        before = (repo / MODEL_DIR / relative).with_suffix(".svg").read_bytes()
        log = self.model_log(repo, **env)
        self.assertEqual(log.drawn_sources, [sha256_of(repo / MODEL_DIR / relative)], relative)
        self.assertNotEqual(before, b"")
        self.assertEqual(self.model_log(repo).draws, 0, "and then it is left")

    def test_e5_a_wrong_source_hash_redraws_that_diagram_alone(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.one_slice(directory)
            svg = repo / MODEL_DIR / "slices/S1.svg"
            svg.write_text(SOURCE_LINE.sub(f"<!-- em-source-sha256: {ZEROS} -->", svg.read_text(), count=1))
            self.only_the(repo, "slices/S1.mmd")

    def test_e5_no_renderer_line_redraws_that_diagram_alone(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.one_slice(directory)
            svg = repo / MODEL_DIR / "slices/S1.svg"
            # what an earlier factory drew: the source stamp and no renderer line
            svg.write_text(re.sub(r"<!-- em-renderer-sha256: [0-9a-f]{64} -->\n", "", svg.read_text(), count=1))
            self.only_the(repo, "slices/S1.mmd")

    def test_e5_a_wrong_key_redraws_that_diagram_alone(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.one_slice(directory)
            svg = repo / MODEL_DIR / "slices/S1.svg"
            self.assertIsNotNone(RENDERER_LINE.search(svg.read_text()), "the renderer line is the second comment")
            svg.write_text(RENDERER_LINE.sub(f"<!-- em-renderer-sha256: {ZEROS} -->", svg.read_text(), count=1))
            self.only_the(repo, "slices/S1.mmd")

    def test_e5_a_file_with_no_closing_tag_is_redrawn(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.one_slice(directory)
            svg = repo / MODEL_DIR / "model.svg"
            svg.write_text(svg.read_text().rstrip()[: -len("</svg>")])
            self.only_the(repo, "model.mmd")

    def spoil(self, repo: Path, change) -> Path:
        svg = repo / MODEL_DIR / "slices/S1.svg"
        change(svg, svg.read_text().split("\n", 2))
        return svg

    def test_e5_a_renderer_line_on_line_three_is_a_diagram_redrawn_once(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.one_slice(directory)
            self.spoil(repo, lambda svg, lines: svg.write_text("\n".join([lines[0], "", lines[1], lines[2]])))
            self.only_the(repo, "slices/S1.mmd")

    def test_e5_the_two_stamps_swapped_are_a_diagram_redrawn_once(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.one_slice(directory)
            self.spoil(repo, lambda svg, lines: svg.write_text("\n".join([lines[1], lines[0], lines[2]])))
            self.only_the(repo, "slices/S1.mmd")

    def test_e5_both_stamps_on_one_line_are_a_diagram_redrawn_once(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.one_slice(directory)
            self.spoil(repo, lambda svg, lines: svg.write_text(" ".join(lines[:2]) + "\n" + lines[2]))
            self.only_the(repo, "slices/S1.mmd")

    def test_e5_crlf_line_ends_are_a_diagram_redrawn_once(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.one_slice(directory)
            self.spoil(repo, lambda svg, lines: svg.write_bytes("\r\n".join(lines).encode()))
            self.only_the(repo, "slices/S1.mmd")

    def test_e5_a_second_wrong_source_stamp_on_line_three_is_left_and_the_gate_agrees(self) -> None:
        # Both readers look at the first stamp only: `isCurrent` at line one, `extractHash` at its first match.
        with tempfile.TemporaryDirectory() as directory:
            repo = self.one_slice(directory)
            self.spoil(repo, lambda svg, lines: svg.write_text(
                "\n".join([lines[0], lines[1], f"<!-- em-source-sha256: {ZEROS} -->", lines[2]])))
            self.assertEqual(self.model_log(repo).draws, 0, "left")
            gate = subprocess.run(["make", "check-model"], cwd=repo, text=True, capture_output=True)
            self.assertEqual(gate.returncode, 0, gate.stdout + gate.stderr)

    def test_e5_each_ci_marker_redraws_every_diagram_and_an_empty_one_is_no_marker(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.one_slice(directory)
            for marker in ("CI", "GITHUB_ACTIONS", "GITLAB_CI"):
                with self.subTest(marker=marker):
                    self.assertEqual(self.model_log(repo, **{marker: "true"}).draws, 3)
                with self.subTest(marker=marker, value="empty"):
                    self.assertEqual(self.model_log(repo, **{marker: ""}).draws, 0)

    def test_e6_each_input_of_the_key_changed_in_turn_redraws_every_diagram(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.one_slice(directory)
            config = Path(directory) / "puppeteer.json"
            config.write_text(json.dumps({"args": ["--no-sandbox"]}))
            self.assertEqual(self.model_log(repo, MERMAID_PUPPETEER_CONFIG=str(config)).draws, 3, "set: a new key")
            self.assertEqual(self.model_log(repo, MERMAID_PUPPETEER_CONFIG=str(config)).draws, 0, "kept")
            modules = repo / EVENT_MODEL / ".mermaid-cli/node_modules"

            def edit_version(package: str) -> None:
                manifest = modules / package / "package.json"
                manifest.write_text(manifest.read_text().replace("0.0.0-stand-in", "0.0.1-stand-in"))

            def edit_config() -> None:
                config.write_text(json.dumps({"args": ["--no-sandbox", "--another"]}))

            def edit_script(name: str):
                return lambda: (repo / EVENT_MODEL / name).write_text(
                    (repo / EVENT_MODEL / name).read_text() + "\n// edited by the test\n")

            changes = {
                "mermaid-cli's version": lambda: edit_version("@mermaid-js/mermaid-cli"),
                "mermaid's version": lambda: edit_version("mermaid"),
                "render.ts": edit_script("render.ts"),
                "render-plan.ts": edit_script("render-plan.ts"),
                "render-session.ts": edit_script("render-session.ts"),
                "patch-mermaid-swimlanes.ts": edit_script("patch-mermaid-swimlanes.ts"),
                "the config file's bytes": edit_config,
            }
            for name, change in changes.items():
                with self.subTest(changed=name):
                    change()
                    self.assertEqual(self.model_log(repo, MERMAID_PUPPETEER_CONFIG=str(config)).draws, 3)
                    self.assertEqual(self.model_log(repo, MERMAID_PUPPETEER_CONFIG=str(config)).draws, 0)
            with self.subTest(changed="the variable, set to unset"):
                self.assertEqual(self.model_log(repo).draws, 3)
                self.assertEqual(self.model_log(repo).draws, 0)

    def probe(self, repo: Path, body: str) -> str:
        script = repo / EVENT_MODEL / "probe-stamp.mts"
        script.write_text(body)
        done = subprocess.run(
            ["node", str(repo / EVENT_MODEL / "node_modules/tsx/dist/cli.mjs"), str(script)],
            cwd=repo, text=True, capture_output=True,
        )
        self.assertEqual(done.returncode, 0, done.stderr)
        return done.stdout.strip()

    def test_e7_hold_extract_hash_reads_the_source_stamp_of_a_two_line_svg_as_of_a_one_line_one(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.one_slice(directory)
            hash_ = "ab" * 32
            out = self.probe(repo, (
                "import { extractHash } from './mermaid.ts';\n"
                f"const one = '<!-- em-source-sha256: {hash_} -->\\n<svg></svg>';\n"
                f"const two = '<!-- em-source-sha256: {hash_} -->\\n"
                f"<!-- em-renderer-sha256: {ZEROS} -->\\n<svg></svg>';\n"
                "console.log(extractHash(one) === extractHash(two) ? extractHash(two) : 'differs');\n"
            ))
            self.assertEqual(out, hash_)

    def test_e7_the_page_carries_both_comments_where_it_inlines_a_picture(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.one_slice(directory)
            page = (repo / MODEL_DIR / "model.html").read_text()
            self.assertGreater(page.count("em-renderer-sha256"), 0)
            self.assertEqual(page.count("em-renderer-sha256"), page.count("em-source-sha256"))


if __name__ == "__main__":
    unittest.main()
