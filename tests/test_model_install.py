"""R7 (AC-S04-47, -50, -53): the model tooling installs with `npm ci`, from one rule, and a disagreeing lock is refused.

`npm` and `node` are stand-ins that log each call and make the marker npm makes; where an example needs npm's own
refusal or the real tools it says so and skips, with its reason, where they are absent. Evidence is the log.
"""
from __future__ import annotations

import atexit
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from parallel_gate import ParallelGateTestCase, log_lines, shape, write_stand_ins
from support import FactoryTestCase

from slipwai.layout import Layout
from slipwai.scaffold import project_files
from slipwai.selection import Selection
from slipwai.services import default_apps

sys.dont_write_bytecode = True

PREFIX = "scripts/event-model"
MARKER = f"{PREFIX}/node_modules/.package-lock.json"
CI = f"--prefix {PREFIX} ci --no-audit --no-fund --loglevel=error"
SKIP = "check-drawio: the model tooling matches scripts/event-model/package-lock.json; not reinstalled"
TARGETS = ("check-drawio", "model-drawio-test", "model", "model-drawio")

_NPM = """#!/bin/sh
log() { printf '%s\\t%s\\n' "$1" "$2" >> "$STANDIN_LOG"; }
args="$*"
log npm-start "$args"
dir=.
while [ $# -gt 0 ]; do
  if [ "$1" = --prefix ]; then dir=$2; fi
  shift
done
if [ -n "$STANDIN_NPM_HOLD" ]; then
  n=0; seen=alone
  while [ "$n" -lt 40 ]; do
    if [ "$(grep -c '^npm-start' "$STANDIN_LOG")" -gt 1 ] || grep -q '^node-start' "$STANDIN_LOG"; then
      seen=met; break
    fi
    sleep 0.05; n=$((n + 1))
  done
  log "npm-$seen" "$dir"
fi
mkdir -p "$dir/node_modules"
: > "$dir/node_modules/.package-lock.json"
log npm-end "$args"
exit 0
"""
_NODE = "#!/bin/sh\nprintf 'node-start\\t%s\\n' \"$*\" >> \"$STANDIN_LOG\"\nexit 0\n"
_starters: dict[str, Path] = {}


def starter(language: str) -> Path:
    """An event-profile project of this language, committed, with no installed tree; tests copy it."""
    if language == "python":
        return shape("db")
    if language not in _starters:
        parent = Path(tempfile.mkdtemp(prefix=f"model-install-{language}-"))
        atexit.register(shutil.rmtree, parent, ignore_errors=True)
        _starters[language] = FactoryTestCase().generate(parent, "project", "event-modelling", language)
    return _starters[language]


def write_model_stand_ins(directory: Path) -> None:
    write_stand_ins(directory)
    for name, text in (("npm", _NPM), ("node", _NODE)):
        (directory / name).write_text(text, encoding="utf-8")


class ModelCase(ParallelGateTestCase):
    """One copy of `LANGUAGE`'s starter per test, with the logging `npm` and `node` first on `PATH`."""

    LANGUAGE = "python"
    SHAPE = "db"
    VENV = False

    def setUp(self) -> None:
        super().setUp()
        if self.LANGUAGE != "python":
            shutil.rmtree(self.repo)
            shutil.copytree(starter(self.LANGUAGE), self.repo, symlinks=True)
        write_model_stand_ins(self.bin)

    def events(self, name: str) -> list[str]:
        return [arguments for event, arguments in log_lines(self.log) if event == name]

    def npm_calls(self) -> list[str]:
        return self.events("npm-start")

    def status(self) -> str:
        done = subprocess.run(["git", "status", "--porcelain"], cwd=self.repo, text=True, capture_output=True,
                              check=True)
        return done.stdout


class FreshCloneTest(ModelCase):
    def test_e3_check_drawio_on_a_fresh_clone_runs_npm_ci_and_leaves_the_tree_clean(self) -> None:
        """AC-S04-47: `npm --prefix scripts/event-model ci …` is the install, and nothing tracked or new remains."""
        self.assert_passed(self.make("check-drawio"))
        self.assertEqual(self.npm_calls(), [CI])
        self.assertEqual(self.status(), "")


class RealNpmTest(ModelCase):
    def need_real_tools(self) -> None:
        for tool in ("npm", "node"):
            if shutil.which(tool) is None:
                self.skipTest(f"{tool} is not installed here")

    def test_e6_a_manifest_that_disagrees_with_the_lock_is_refused_and_no_tracked_file_changes(self) -> None:
        """AC-S04-50: npm's own `ci` refuses before it fetches; the lock is byte for byte as it was."""
        self.need_real_tools()
        # npm is itself a script run by `node`, so the stand-in `node` goes too.
        for tool in ("npm", "node"):
            (self.bin / tool).unlink()
        manifest = self.repo / PREFIX / "package.json"
        manifest.write_text(manifest.read_text(encoding="utf-8").replace('"yaml": "2.9.0"', '"yaml": "2.8.0"'),
                            encoding="utf-8")
        lock = self.repo / PREFIX / "package-lock.json"
        before = lock.read_bytes()
        done = self.make("check-drawio")
        self.assertNotEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertIn("npm", done.stderr)
        self.assertEqual(lock.read_bytes(), before)
        changed = [line for line in self.status().splitlines() if "package-lock.json" in line]
        self.assertEqual(changed, [])


class OneRuleTest(unittest.TestCase):
    def test_e9_the_makefile_spells_npm_for_the_model_tooling_once_and_it_is_ci(self) -> None:
        """AC-S04-53: one recipe names `npm` with `scripts/event-model`, and it is `npm ci`."""
        makefile = (shape("db") / "Makefile").read_text(encoding="utf-8")
        spelled = [line for line in makefile.splitlines() if re.search(r"\bnpm\b", line) and PREFIX in line]
        self.assertEqual(len(spelled), 1, spelled)
        self.assertTrue(spelled[0].startswith("\tnpm --prefix scripts/event-model ci "), spelled)
        self.assertNotIn(" install", spelled[0])

    def test_e9_a_moved_layout_holds_the_file_target_its_prerequisites_and_the_prefix_together(self) -> None:
        """AC-S04-53: under `delivery/` the target, both prerequisites and `--prefix` all spell the moved path."""
        apps = default_apps("python", "none", Selection({"event-store": "postgres", "http": "none"}))
        files = project_files("moved", "event-modelling", "none", apps, Layout("delivery"))
        makefile = files["delivery/Makefile"]
        base = "delivery/scripts/event-model"
        rule = f"{base}/node_modules/.package-lock.json: {base}/package.json {base}/package-lock.json\n"
        self.assertIn("\n" + rule, makefile)
        npm = [line for line in makefile.splitlines() if re.search(r"\bnpm\b", line) and "event-model" in line]
        self.assertEqual(len(npm), 1, npm)
        self.assertIn(f"npm --prefix {base} ci ", npm[0])
        self.assertIn(f"{base}/package-lock.json", files)
        self.assertIn(f"{base}/package.json", files)
        self.assertNotIn(" scripts/event-model", makefile.replace(base, ""))


if __name__ == "__main__":
    unittest.main()
