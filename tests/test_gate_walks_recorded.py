"""`check-imports` finds what it always found however a deployable's path is recorded (S01-gate-walks, T015).

A walk filtered against a listing taken at another top must yield what the directory's own listing would, so
a recorded path spelled with `..`, or through a symbolic link, is read as the pre-slice script read it.
"""
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from support import FactoryTestCase

BAD_IMPORT = "import { y } from '../../service/src/domain/thing';\n"
BAD_CONTEXT = "from billing.domain import thing\n"


def run(repo: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["python3", "scripts/check-imports.py"], cwd=repo, text=True, capture_output=True)


class RecordedPathTest(FactoryTestCase):
    def project(self, directory: str) -> Path:
        repo = self.generate(directory, "recorded", "event-modelling", "python", frontend="react-vite")
        (repo / "apps/web/src").mkdir(parents=True, exist_ok=True)
        (repo / "apps/web/src/bad.ts").write_text(BAD_IMPORT)
        return repo

    def record(self, repo: Path, key: str, path: str, **extra: object) -> None:
        manifest = json.loads((repo / "project.json").read_text())
        manifest["deployables"][key]["path"] = path
        manifest["deployables"][key].update(extra)
        (repo / "project.json").write_text(json.dumps(manifest, indent=2) + "\n")

    def link(self, link: Path, target: Path) -> None:
        try:
            link.symlink_to(target, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("this platform cannot make a symbolic link")

    def assert_fails_naming(self, repo: Path, spelling: str) -> None:
        result = run(repo)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(f"{spelling}:1:", result.stderr)

    def test_a_web_app_recorded_with_a_dot_dot_is_still_read(self) -> None:
        """T015 e1."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory)
            self.record(repo, "web", "apps/service/../web")
            self.assert_fails_naming(repo, "apps/service/../web/src/bad.ts")

    def test_a_web_app_recorded_as_a_link_to_the_app_is_still_read(self) -> None:
        """T015 e2."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory)
            self.link(repo / "apps/weblink", repo / "apps/web")
            self.record(repo, "web", "apps/weblink")
            self.assert_fails_naming(repo, "apps/weblink/src/bad.ts")

    def test_a_web_app_that_is_itself_a_link_out_of_apps_is_still_read(self) -> None:
        """T015 e3."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory)
            outside = Path(directory) / "outside"
            (repo / "apps/web").rename(outside)
            self.link(repo / "apps/web", outside)
            self.assert_fails_naming(repo, "apps/web/src/bad.ts")

    def test_hold_every_plain_spelling_of_the_web_app_fails_as_before(self) -> None:
        """T015 holds: `apps/web`, `apps/web/`, `./apps/web`, `frontends/web` and `.`."""
        for spelling in ("apps/web", "apps/web/", "./apps/web", "frontends/web", "."):
            with self.subTest(spelling=spelling), tempfile.TemporaryDirectory() as directory:
                repo = self.project(directory)
                if spelling == "frontends/web":
                    (repo / "frontends").mkdir()
                    (repo / "apps/web").rename(repo / "frontends/web")
                self.record(repo, "web", spelling)
                result = run(repo)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn("bad.ts:1:", result.stderr)

    def test_a_context_holding_service_recorded_with_a_dot_dot_is_still_read(self) -> None:
        """T015 rule 5: a context reaches into another, the service recorded as `apps/web/../service`."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.project(directory)
            (repo / "apps/web/src/bad.ts").unlink()
            context = repo / "apps/service/src/orders"
            context.mkdir(parents=True, exist_ok=True)
            (context / "bad.py").write_text(BAD_CONTEXT)
            self.record(repo, "service", "apps/web/../service", contexts=["orders", "billing"])
            self.assert_fails_naming(repo, "apps/web/../service/src/orders/bad.py")
