"""G3, G4 (AC-S04-74, -75, -76): a gate target that reads the root's installed tree waits for the install under `-j`.

The instances run a browser project with stand-ins: `npm` logs `start`/`end` around a bounded wait for the call that
must not have started yet (a barrier and a log, never a clock), and `python3` logs the gate scripts it starts. The class
is a closed list over every shape: each target of the gate either names the prerequisite its recipe needs, or is named
below with the reason it reads nothing there, so a target added to the gate fails here until it is classified.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import test_parallel_gate_first as first
from parallel_gate import ROOT, SHAPES, log_lines, log_text
from test_parallel_gate_families import reaches
from test_verify_stamp_scan import gate_targets, makefile_rules

from slipwai.project import model_targets
from slipwai.project.shared_packages import NODE_DEPS

sys.dont_write_bytecode = True

# `npm` as a gate recipe calls it. A call whose arguments match `$STANDIN_HOLD` waits, bounded, for a line holding
# `$STANDIN_UNTIL` to be in the log, and logs `met` or `alone`; every call logs `start` and `end`.
NPM = """#!/bin/sh
log() { printf '%s\\t%s\\n' "$1" "$2" >> "$STANDIN_LOG"; }
log start "npm $*"
d=.; [ "$1" = --prefix ] && d=$2
case "$*" in
  $STANDIN_HOLD)
    n=0; seen=alone
    while [ "$n" -lt 40 ]; do
      if grep -q -F "$STANDIN_UNTIL" "$STANDIN_LOG"; then seen=met; break; fi
      sleep 0.05; n=$((n + 1))
    done
    log "$seen" "npm $*" ;;
esac
mkdir -p "$d/node_modules"
log end "npm $*"
"""
SCRIPT = "python3 scripts/check-ux-gates.py"
EXPORT = "run --silent"  # what `check-openapi`'s recipe passes `npm` for a TypeScript service


class ReadsAfterInstallTest(first.FirstTestCase):
    SHAPE = "ts-event"

    def setUp(self) -> None:
        super().setUp()
        (self.bin / "npm").write_text(NPM, encoding="utf-8")

    def positions(self, event: str, word: str) -> list[int]:
        return [i for i, (e, a) in enumerate(log_lines(self.log)) if e == event and word in a]

    def test_check_ux_gates_starts_after_the_root_npm_ci_has_ended(self) -> None:
        """AC-S04-74 (fails before G3): on a fresh clone `npm ci` is held until the script has started, if it can."""
        done = self.make("-j", "-k", "verify", env={"STANDIN_HOLD": "ci", "STANDIN_UNTIL": SCRIPT, "VERIFY_FORCE": "1"})
        installed = [i for i in self.positions("end", "npm ci")]
        started = self.positions("start", SCRIPT)
        self.assertTrue(installed and started, done.stdout + done.stderr + log_text(self.log))
        self.assertGreater(min(started), max(installed), log_text(self.log))

    def test_check_openapi_starts_after_the_package_builds_have_ended(self) -> None:
        """AC-S04-76 (fails before G4): a build is held until the exporter has started, if it can be."""
        done = self.make("-j", "-k", "verify", env={"STANDIN_HOLD": "*run build*", "STANDIN_UNTIL": EXPORT,
                                                    "VERIFY_FORCE": "1"})
        builds = self.positions("end", "run build")
        exports = self.positions("start", EXPORT)
        self.assertTrue(builds and exports, done.stdout + done.stderr + log_text(self.log))
        self.assertGreater(min(exports), max(builds), log_text(self.log))

    def test_a_standalone_check_ux_gates_installs_first(self) -> None:
        """AC-S04-74: typed alone on a fresh clone it runs the install, then the script (read from `make -n`)."""
        printed = self.make("-n", "check-ux-gates").stdout
        self.assertIn("npm ci", printed)
        self.assertLess(printed.index("npm ci"), printed.index(SCRIPT), printed)


# Shapes beyond `first.SWEEP`: an npm workspace without a Node service, and one with a Python service.
SHAPES_TO_READ = (
    *first.SWEEP,
    ("go-web", ("--profile", "standard", "--backend", "go", "--frontend", "react-vite")),
    ("python-web", ("--profile", "standard", "--backend", "python", "--frontend", "react-vite", "--http", "fastapi")),
    ("ts-event", SHAPES["ts-event"]),
)
# Targets that are the install itself, or the one the recipes share: what the others name, not what reads it.
INSTALLS = {
    NODE_DEPS: "the root's `npm ci`",
    model_targets.MARKER: "the model tooling's `npm ci`",
    "build-packages": "builds the workspace's packages after the root's install",
    "sync": "builds the Python environments, which are not the npm tree",
}
# What a recipe that reads no npm tree is, each with why: not one of them opens `node_modules` (the scripts that walk
# the tree prune it by name), launches `node`, or runs an npm script. `lint`, `typecheck`, `test` and `check-openapi`
# are here for the shapes where their recipe is the native or Python tool alone; where it has an npm line the derived
# rule applies and they are not looked up.
READS_NOTHING = {
    "check-ux-gates": "in a project with no npm workspace there is no browser app, and it measures nothing",
    "check-python": "asks `python3` for its version",
    "check-agents": "refreshes and compares the agent harness projections: Python over tracked files",
    "check-benchmark": "Python scripts over the benchmark records",
    "check-codegraph": "compares the code index's election with tracked source",
    "check-constitution": "reads the constitution, a tracked document",
    "check-decisions": "reads the decision log, a tracked document",
    "check-deploy-role": "reads the target's deploy configuration",
    "check-extensions": "reads the extension election",
    "check-flags": "reads the target's flag declarations",
    "check-imports": "walks the source tree, pruning `node_modules`",
    "check-migrations": "walks the migrations, pruning `node_modules`",
    "check-model": "validates `model.yaml`, a tracked file, in Python",
    "check-slice-scope": "reads git's diff",
    "check-speckit": "compares tracked Spec Kit files with their manifest",
    "check-styles": "Python over a browser app's tracked styles",
    "lint": "the native or Python tool of a project with no npm workspace",
    "typecheck": "the native or Python tool of a project with no npm workspace",
    "test": "the native or Python tool of a project with no npm workspace",
    "check-openapi": "a Python or Go service's document, exported by that service's own tool",
}
# Reads the root's installed tree without an npm line in its recipe, and so is named: it takes `build-packages`.
READS_THE_ROOT_TREE = {"check-ux-gates": "resolves `playwright` in the root's `node_modules`; D96 takes build-packages"}
READS_THE_MODEL_TREE = {"check-drawio": "runs `tsx` from the model tooling's own `node_modules`"}
OWN_CODE = re.compile(r"\bnpm\b|\bnpx\b|\bnode\b")
_cache: dict[str, dict[str, tuple[set[str], list[str]]]] = {}


def rules_of(name: str, arguments: tuple[str, ...]) -> dict[str, tuple[set[str], list[str]]]:
    if name not in _cache:
        parent = Path(tempfile.mkdtemp(prefix=f"reads-{name}-"))
        subprocess.run([str(ROOT / "slipwai"), "generate", "project", *arguments, "--output", str(parent),
                        "--skip-checks"], check=True, capture_output=True, timeout=180)
        text = (parent / "project" / "Makefile").read_text(encoding="utf-8")
        shutil.rmtree(parent, ignore_errors=True)
        # A recipe in a transport's marked region sits after a marker comment, where the reader ends a rule.
        _cache[name] = makefile_rules(re.sub(r"^# backing-service:.*\n", "", text, flags=re.M))
    return _cache[name]


class EveryReaderWaitsTest(unittest.TestCase):
    def test_every_gate_target_names_what_its_recipe_reads_or_is_listed_as_reading_nothing(self) -> None:
        """AC-S04-75: the closed list. Teeth: take the `check-ux-gates` line out of `npm_workspace_targets`, or
        give a listed target a recipe line that runs `npm`."""
        seen: set[str] = set()
        for name, arguments in SHAPES_TO_READ:
            with self.subTest(shape=name):
                rules = rules_of(name, arguments)
                workspace = NODE_DEPS in rules
                for target in sorted(gate_targets(rules) - {"verify-checks"} - set(INSTALLS)):
                    recipe = " ".join(rules[target][1])
                    if target in READS_THE_MODEL_TREE:
                        self.assertIn(model_targets.MARKER, rules[target][0], target)
                    elif OWN_CODE.search(recipe) or (workspace and target in READS_THE_ROOT_TREE):
                        self.assertIn("build-packages", reaches(rules, target), (target, recipe))
                        self.assertIn(NODE_DEPS, reaches(rules, target), target)
                    else:
                        self.assertIn(target, READS_NOTHING, f"{target} is a gate target no list names: {recipe}")
                        seen.add(target)
        self.assertEqual(seen, set(READS_NOTHING) | set(), "a name is listed that no shape's gate has")


if __name__ == "__main__":
    unittest.main()
