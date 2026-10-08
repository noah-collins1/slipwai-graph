"""S41 T040 (B2): the Makefile's install target takes the wrapper's lock, and `mutation` gains no prerequisite for it.

`make -j2 mutation-full build-packages` on a fresh clone ran the wrapper's `npm ci` and the Makefile's in one root, two
installs on one `node_modules`. The target's recipe is now `python3 scripts/stryker-mutation.py --install npm ci`,
which takes the same lock; `mutation` and `mutation-full` keep the recipe and the (absent) prerequisites the scope
script holds them to, because it reads a prerequisite there as a project's own recipe. A project with no TypeScript
service has no wrapper and keeps `npm ci`. The projects are generated; the `npm` is `test_stryker_verdict`'s, which
sleeps in `ci`.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from support import FactoryTestCase
from test_stryker_after_run import PASSING, fake_npm

sys.dont_write_bytecode = True
TEST_SELECTION = {"reads": ["assets/languages/typescript/scripts/stryker-mutation.py",
                            "src/slipwai/project/shared_packages.py"]}
MARKER = "node_modules/.package-lock.json"


def recipe(makefile: str, target: str) -> list[str]:
    """The recipe lines of `target`, and its prerequisites as the first element."""
    found = re.search(rf"^{re.escape(target)}:([^\n]*)\n((?:\t[^\n]*\n|#[^\n]*\n)*)", makefile, re.MULTILINE)
    assert found is not None, target
    return [found[1].split("##")[0].strip(), *[line.strip() for line in found[2].splitlines() if line.startswith("\t")]]


class MakefileInstallTest(FactoryTestCase):
    parent: Path

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.parent = Path(tempfile.mkdtemp(prefix="stryker-makefile-"))
        cls.addClassCleanup(shutil.rmtree, cls.parent, ignore_errors=True)

    def makefile(self, name: str, frontend: str, language: str = "typescript") -> str:
        made = self.generate(self.parent, name, "standard", language, frontend, http="none")
        return (made / "Makefile").read_text(encoding="utf-8")

    def test_e1_a_typescript_project_installs_through_the_wrappers_lock_and_runs_npm_ci(self) -> None:
        self.assertEqual(recipe(self.makefile("ts", "none"), MARKER),
                         ["package.json package-lock.json", "python3 scripts/stryker-mutation.py --install npm ci",
                          f"@touch {MARKER}"])

    def test_e2_mutation_and_mutation_full_keep_their_recipe_and_gain_no_prerequisite(self) -> None:
        text = self.makefile("ts-recipe", "none")
        for target in ("mutation", "mutation-full"):
            with self.subTest(target=target):
                lines = recipe(text, target)
                self.assertEqual(lines[0], "", lines)
        self.assertEqual(recipe(text, "mutation-full")[1:], ["python3 scripts/stryker-mutation.py apps/service"])

    def test_e3_a_project_with_no_typescript_service_has_no_wrapper_and_keeps_npm_ci(self) -> None:
        self.assertEqual(recipe(self.makefile("go-web", "react-vite", "go"), MARKER)[1], "npm ci")

    def test_e4_make_j_on_a_fresh_clone_runs_one_install_between_the_wrapper_and_the_target(self) -> None:
        made = self.generate(self.parent, "fresh", "standard", "typescript", "none", http="none")
        bin_directory = Path(tempfile.mkdtemp(dir=self.parent))
        fake_npm(bin_directory)
        (bin_directory / "plan.json").write_text(json.dumps({**PASSING, "ci_sleep": 2}), encoding="utf-8")
        env = {key: value for key, value in os.environ.items()
               if key not in ("CI", "GITHUB_ACTIONS", "GITLAB_CI", "SINCE", "MAKEFLAGS", "MFLAGS")}
        env.update({"PATH": f"{bin_directory}{os.pathsep}{env['PATH']}", "FAKE_LOG": str(bin_directory / "npm.log"),
                    "FAKE_PLAN": str(bin_directory / "plan.json")})
        done = subprocess.run(["make", "-j2", "mutation-full", "build-packages"], cwd=made, env=env, text=True,
                              capture_output=True, timeout=180)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        calls = [json.loads(line)["argv"][0] for line in (bin_directory / "npm.log").read_text(
            encoding="utf-8").splitlines()]
        self.assertEqual([call for call in calls if call in ("ci", "ci-done")], ["ci", "ci-done"], calls)


if __name__ == "__main__":
    import unittest
    unittest.main()
