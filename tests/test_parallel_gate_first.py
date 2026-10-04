"""R2 (AC-S04-13, -1, -18): `check-python` is first, serial and parallel; and nothing under `.specify/` moves.

The older `python3` is the `sitecustomize` stand-in of `tests/test_check_python.py` — a directory on `PYTHONPATH` that
sets `sys.version_info` to 3.9.6 — and `python3` itself is a wrapper first on `PATH` that logs each call to the
stand-in log and hands it to the real one, so evidence is what started, never a printed line. A **hold** is an
example that is true today and must stay true; each says so in its docstring and was seen to have teeth.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from parallel_gate import ROOT, SHAPES, ParallelGateTestCase, log_lines, log_text, run_lines, sync_lines
from test_verify_stamp_pinned import gate_prerequisites
from test_verify_stamp_scan import makefile_rules

from slipwai.project import model_targets
from slipwai.project.shared_packages import NODE_DEPS

sys.dont_write_bytecode = True

OLDER = "import sys\nsys.version_info = (3, 9, 6, 'final', 0)\nsys.version = '3.9.6 (default)'\n"
VERSION_QUESTION = "-c import sys; sys.exit(0 if sys.version_info >= (3, 10)"
WRAPPER = """#!/bin/sh
printf 'start\\tpython3 %s\\n' "$*" >> "$STANDIN_LOG"
{real} "$@"
status=$?
printf 'end\\tpython3 %s\\n' "$*" >> "$STANDIN_LOG"
exit $status
"""


# The scripts a serial `make verify` of the `plain` shape launches, in the order the gate has always run them.
ORDER = [
    "scripts/check-imports.py", "scripts/check-migrations.py", "scripts/check-slice-scope.py",
    "scripts/extensions/project.py", "scripts/agents/project.py", "scripts/agents/models.py",
    "scripts/agents/drive.py", "scripts/agents/cruise.py", "scripts/check-speckit.py", "scripts/check-codegraph.py",
    "scripts/check-ux-gates.py", "scripts/check-constitution.py", "scripts/test_benchmark.py",
    "scripts/agents/benchmark.py", "scripts/check-decisions.py",
]


def quiet(arguments: str) -> bool:
    """A call that is the stamp's own, or a version question: not a check, and nested inside the stamp."""
    return "verify-stamp.py" in arguments or arguments in ("python3 --version", "--version")


def specify_bytes(repo: Path) -> dict[str, bytes]:
    """Every file under `.specify/` and what it holds."""
    return {p.relative_to(repo).as_posix(): p.read_bytes() for p in sorted((repo / ".specify").rglob("*"))
            if p.is_file()}


class FirstTestCase(ParallelGateTestCase):
    """A project whose `python3` is logged, and can be made to say it is 3.9.6."""

    def setUp(self) -> None:
        super().setUp()
        real = shutil.which("python3")
        assert real is not None
        (self.bin / "python3").write_text(WRAPPER.format(real=real), encoding="utf-8")
        (self.bin / "python3").chmod(0o755)
        self.older = self.bin.parent / "older"
        self.older.mkdir()
        (self.older / "sitecustomize.py").write_text(OLDER, encoding="utf-8")

    def python_starts(self) -> list[str]:
        """The arguments of every `python3` that started, in order."""
        return [a.removeprefix("python3 ") for e, a in log_lines(self.log) if e == "start" and a.startswith("python3 ")]

    def checks_started(self) -> list[str]:
        """Every check that started: a script, or a `uv` sync or run — not the version question or the stamp."""
        scripts = [a for a in self.python_starts() if not a.startswith(VERSION_QUESTION) and "verify-stamp.py" not in a]
        return scripts + sync_lines(self.log) + run_lines(self.log)

    def under_older_python(self, *args: str) -> subprocess.CompletedProcess[str]:
        return self.make(*args, env={"PYTHONPATH": str(self.older)})

    def assert_stopped_at_check_python(self, done: subprocess.CompletedProcess[str]) -> None:
        self.assertNotEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertIn("is Python 3.9.6, and the gate scripts need 3.10 or newer", done.stderr)
        self.assertEqual(self.checks_started(), [], log_text(self.log))
        self.assertEqual(sync_lines(self.log), [], "a sync started")


class OlderPythonTest(FirstTestCase):
    def test_e1_serial_names_check_python_and_starts_nothing(self) -> None:
        """HOLD (AC-S04-13, serial): `check-python` is first in the list and make stops there."""
        self.assert_stopped_at_check_python(self.under_older_python("verify"))

    def test_e2_parallel_names_check_python_and_starts_nothing(self) -> None:
        """AC-S04-13, `-j`: every other check, and the sync, waits for `check-python` (fails before R2)."""
        self.assert_stopped_at_check_python(self.under_older_python("-j", "verify"))

    def test_e2_a_newer_python_is_not_stopped(self) -> None:
        """HOLD: the same `-j` run on the real interpreter passes, and `check-python` is among what ran first."""
        self.assert_passed(self.make("-j", "verify"))
        self.assertTrue(any(a.startswith(VERSION_QUESTION) for a in self.python_starts()), log_text(self.log))


class SerialOrderTest(FirstTestCase):
    def test_e3_a_serial_run_starts_the_checks_in_the_order_they_had_one_at_a_time(self) -> None:
        """HOLD (AC-S04-1): `check-python`, then the sync, then the checks in the gate's list, never two at once."""
        self.assert_passed(self.make("verify"))
        scripts = [a.split()[0] for a in self.python_starts()
                   if a.startswith("scripts/") and "verify-stamp.py" not in a]
        self.assertEqual(scripts, ORDER, log_text(self.log))
        starts = [(e, a) for e, a in log_lines(self.log) if e == "start" and a.split()[0] in ("python3", "sync", "run")
                  and "verify-stamp.py" not in a and a != "python3 --version"]
        self.assertTrue(starts[0][1].startswith("python3 " + VERSION_QUESTION), starts[:3])
        self.assertTrue(starts[1][1].startswith("sync"), starts[:3])
        flight = 0
        for event, argument in log_lines(self.log):
            if event in ("start", "end") and not quiet(argument):
                flight += 1 if event == "start" else -1
                self.assertLessEqual(flight, 1, "two ran at once:\n" + log_text(self.log))
        lines = [a for e, a in log_lines(self.log) if e == "start"]
        order = [i for i, a in enumerate(lines) if a.startswith("run")]
        first_script = next(i for i, a in enumerate(lines) if a.startswith("python3 scripts/check-imports.py"))
        last_script = max(i for i, a in enumerate(lines) if a.startswith("python3 scripts/check-"))
        self.assertLess(order[0], first_script, "lint and typecheck did not run before the check scripts")
        self.assertGreater(order[-1], last_script, "test did not run last")


# An npm workspace, a browser app and the event profile: the root's `npm ci` and the model tooling's are in the gate.
SHAPES["ts-event"] = ("--profile", "event-modelling", "--backend", "typescript", "--frontend", "react-vite")
# `npm`, as a gate recipe calls it: logged, and leaving the directory a marker would be in.
NPM = """#!/bin/sh
printf 'start\\tnpm %s\\n' "$*" >> "$STANDIN_LOG"
d=.; [ "$1" = --prefix ] && d=$2
mkdir -p "$d/node_modules"
"""


class InstallWaitsTest(FirstTestCase):
    """G2 (AC-S04-72, -73): under the gate nothing installs before `check-python` has answered; typed alone, nothing
    waits for it. `build-packages` builds the shape's `api-client` package, so that its start is a logged `npm` call."""

    SHAPE = "ts-event"

    def setUp(self) -> None:
        super().setUp()
        (self.bin / "npm").write_text(NPM, encoding="utf-8")

    def install(self) -> None:
        """The tree as an earlier install left it: both markers, newer than the manifests they came from."""
        for marker in (self.repo / NODE_DEPS, self.repo / model_targets.MARKER):
            marker.parent.mkdir(parents=True, exist_ok=True)
            marker.touch()

    def npm_starts(self) -> list[str]:
        return [a for e, a in log_lines(self.log) if e == "start" and a.startswith("npm ")]

    def test_e5_an_older_python_starts_no_npm_beside_check_python_on_a_fresh_tree(self) -> None:
        """AC-S04-72 (fails before G2): the root's `npm ci`, the model tooling's and `build-packages` wait for it."""
        done = self.under_older_python("-j", "verify")
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("is Python 3.9.6", done.stderr)
        self.assertEqual(self.npm_starts(), [], log_text(self.log))

    def test_e5_an_older_python_starts_no_build_on_an_installed_tree(self) -> None:
        """AC-S04-72, installed: `build-packages` is a phony target and would start beside `check-python`."""
        self.install()
        done = self.under_older_python("-j", "verify")
        self.assertNotEqual(done.returncode, 0)
        self.assertEqual(self.npm_starts(), [], log_text(self.log))

    def test_e6_a_newer_python_on_an_installed_tree_runs_no_npm_ci(self) -> None:
        """HOLD (AC-S04-73): the order-only prerequisite does not make the markers out of date, serial or `-j`.
        Teeth: a `check-python` ordinary prerequisite of the marker reinstalls on every run."""
        self.install()
        for flags in ((), ("-j",)):
            with self.subTest(flags=flags):
                self.forget_log()
                # Run on through a check the stand-ins cannot satisfy (`-k`): the question is what installed.
                self.make(*flags, "-k", "verify", env={"VERIFY_FORCE": "1"})
                self.assertIn("npm --workspace packages/api-client run build --if-present", self.npm_starts())
                self.assertEqual([a for a in self.npm_starts() if " ci" in a], [], log_text(self.log))

    def test_e6_a_target_typed_alone_does_not_run_check_python(self) -> None:
        """HOLD (AC-S04-73): `make build-packages` and `make dev-web` name no `check-python`. Teeth: put the line
        outside the gate's conditional."""
        for target in ("build-packages", "dev-web"):
            with self.subTest(target=target):
                out = self.make("-n", target).stdout
                self.assertIn("npm", out)
                self.assertNotIn("sys.version_info", out)


class SpecifyTest(FirstTestCase):
    SHAPE = "db"

    def test_e4_a_parallel_run_leaves_every_byte_under_specify_as_it_was(self) -> None:
        """HOLD (AC-S04-18): no gate target writes there. The gate may fail on this shape's stand-ins; what it
        leaves behind is the question, so the run continues past a failure (`-k`)."""
        before = specify_bytes(self.repo)
        self.assertTrue(before, "the shape has nothing under .specify/")
        self.make("-j", "-k", "verify")
        self.assertEqual(specify_bytes(self.repo), before)

    def test_e4_a_write_under_specify_would_be_seen(self) -> None:
        """The teeth of e4: a `uv run` that writes under `.specify/` makes the same comparison fail."""
        uv = self.bin / "uv"
        uv.write_text(uv.read_text(encoding="utf-8").replace(
            '  run)\n', '  run)\n    echo moved >> "$PWD/.specify/drive.json"\n', 1), encoding="utf-8")
        before = specify_bytes(self.repo)
        self.make("-j", "-k", "verify")
        self.assertNotEqual(specify_bytes(self.repo), before)


# What a project is generated with: (name, arguments after `generate project`). Every backend with its transport and
# without one, a browser app, the event profile, and a deploy target (`check-flags`, the role gate).
SWEEP = (
    ("typescript-http", ("--profile", "standard", "--backend", "typescript", "--frontend", "none")),
    ("typescript-none", ("--profile", "standard", "--backend", "typescript", "--frontend", "none", "--http", "none")),
    ("python-http", ("--profile", "event-modelling", "--backend", "python", "--frontend", "none", "--http", "fastapi",
                     "--event-store", "postgres")),
    ("python-none", ("--profile", "standard", "--backend", "python", "--frontend", "none", "--http", "none")),
    ("go-http", ("--profile", "standard", "--backend", "go", "--frontend", "none")),
    ("quarkus-http", ("--profile", "standard", "--backend", "java-quarkus", "--frontend", "none")),
    ("spring-none", ("--profile", "standard", "--backend", "java-spring", "--frontend", "none", "--http", "none")),
    ("browser", ("--profile", "standard", "--backend", "typescript", "--frontend", "react-vite")),
    ("event-cloud", ("--profile", "event-modelling", "--backend", "typescript", "--frontend", "react-vite",
                     "--target", "aws")),
)
# Where a service exports a published API document (Go's is hand-written and Quarkus publishes its own).
EXPORTING = ("typescript-http", "python-http", "browser", "event-cloud")
_projects: dict[str, str] = {}


class EveryCheckWaitsTest(unittest.TestCase):
    def project(self, name: str, arguments: tuple[str, ...]) -> str:
        if name not in _projects:
            parent = Path(tempfile.mkdtemp(prefix=f"first-{name}-"))
            self.addCleanup(shutil.rmtree, parent, ignore_errors=True)
            subprocess.run([str(ROOT / "slipwai"), "generate", "project", *arguments, "--output", str(parent),
                            "--skip-checks"], check=True, capture_output=True, timeout=180)
            _projects[name] = (parent / "project" / "Makefile").read_text(encoding="utf-8")
        return _projects[name]

    @staticmethod
    def reaches(rules: dict[str, tuple[set[str], list[str]]], target: str, wanted: str) -> bool:
        seen: set[str] = set()
        todo = [target]
        while todo:
            current = todo.pop()
            if current == wanted:
                return True
            if current not in seen and current in rules:
                seen.add(current)
                todo.extend(rules[current][0])
        return False

    def test_every_prerequisite_of_the_gate_names_check_python_directly_or_through_the_sync(self) -> None:
        """The sweep that closes the class (AC-S04-13): derived from the Makefile's own rules, for each shape."""
        for name, arguments in SWEEP:
            with self.subTest(shape=name):
                makefile = self.project(name, arguments)
                # A recipe in a transport's marked region sits after a marker comment, where the reader ends a rule.
                rules = makefile_rules(re.sub(r"^# backing-service:.*\n", "", makefile, flags=re.M))
                gate = rules["verify-checks"][0] - {"check-python"}
                self.assertGreater(len(gate), 10, "the derivation found almost nothing")
                for target in sorted(gate):
                    self.assertTrue(rules[target][1], f"{target} has a prerequisite line and no recipe")
                    self.assertTrue(self.reaches(rules, target, "check-python") and target != "check-python",
                                    f"{target} does not wait for check-python")
                self.assertEqual("check-openapi" in rules, name in EXPORTING,
                                 "check-openapi is defined exactly where a service exports a document")
                self.assertEqual(gate_prerequisites(makefile)[0], "check-python")


if __name__ == "__main__":
    unittest.main()
