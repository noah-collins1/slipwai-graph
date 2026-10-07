"""T004 (R6 · AC-S07-8; D172 limit ii): the four method-file checks are held to what they read.

Each check's recipe, as the generated Makefile writes it, runs under a wrapper that records every `open`, `os.listdir`,
`os.scandir` and every `os.stat` and `os.lstat` (patched in the wrapper: Python raises no audit event for them), in a
project with an integration installed, projected and a manifest written. Every path inside the project it touched lies
under the check's recorded inputs, is `project.json`, lies under `scripts/` (the full gate) or is git-ignored (the
digest AC-S06-9 keeps). `tests/gate_audit.py` is not used: it records no stat.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from test_scoped_targets import SHAPES as SHAPE_TABLE
from test_scoped_targets import database
from test_verify_scoped_record import RecordCase, covered, environment, loaded, record
from test_verify_scoped_table_held import derived_readers, entries_of, modules_of

from slipwai.assets import ROOT

sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "assets" / "toolkit" / "scripts"))

FOUR = ("check-agents", "check-speckit", "check-extensions", "check-constitution")
OWN = ("project.json", "scripts", ".git")
LISTINGS = ("os.scandir", "os.listdir")
SAMPLE = ".specify/templates/sample.md"
MANIFEST = ".specify/integrations/claude.manifest.json"
WRAPPER = """
import json, os, runpy, sys
root = os.getcwd()
seen = []
def note(kind, path):
    try:
        found = os.path.normpath(os.path.join(root, os.fsdecode(path)))
    except TypeError:
        return
    seen.append([kind, found])
def hook(event, arguments):
    if event in ("open", "os.scandir", "os.listdir") and arguments:
        note(event, arguments[0])
sys.addaudithook(hook)
for name in ("stat", "lstat"):
    def patched(path, *args, _real=getattr(os, name), _name=name, **kwargs):
        note(_name, path)
        return _real(path, *args, **kwargs)
    setattr(os, name, patched)
script = sys.argv[1]
sys.argv = sys.argv[1:]
sys.path.insert(0, os.path.dirname(os.path.abspath(script)))
try:
    runpy.run_path(script, run_name="__main__")
finally:
    text = json.dumps([[kind, os.path.relpath(path, root)] for kind, path in seen])
    with open(os.environ["AUDIT_LOG"], "a", encoding="utf-8") as handle:
        handle.write(text + "\\n")
"""


# Touched, and not an input: the check's answer (exit status) cannot change by it. The reason is the value.
REPORT_ONLY = {
    "check-agents": "`agents/project.py`'s `project_capabilities` tests that each deployable's directory exists, to "
                    "print which skills nothing in the project serves — `report_unjustified_skills` is a report, "
                    "never a failure; `project.json` is the full gate",
}


def reported(project: Path) -> list[str]:
    """What `check-agents` stat-s for its report: each deployable's directory, as `project.json` names it."""
    deployables = json.loads((project / "project.json").read_text(encoding="utf-8")).get("deployables") or {}
    return [item["path"].strip("/") for item in deployables.values() if isinstance(item, dict) and item.get("path")]


def held(kind: str, path: str, files: list[str]) -> bool:
    """Whether a path a check touched is one of its inputs, or the full gate's. An ancestor of an input may be opened or
    stat-ed (a directory exists because its entries do) but never listed: a listing reads every sibling too."""
    if path == "." or path.split("/")[0] in OWN or covered(path, files):
        return True
    return kind not in LISTINGS and any(entry.startswith(path + "/") for entry in files)


def ignored(project: Path, path: str) -> bool:
    done = subprocess.run(["git", "check-ignore", "-q", "--", path], cwd=project, capture_output=True, timeout=60)
    return done.returncode == 0


def touched(project: Path, line: str, scratch: Path) -> list[list[str]]:
    """What one recipe line (`python3 …`, perhaps chained) opened, listed and stat-ed, as `[kind, path]`."""
    wrapper, shim, log = scratch / "wrapper.py", scratch / "bin" / "python3", scratch / "audit.log"
    shim.parent.mkdir(parents=True, exist_ok=True)
    wrapper.write_text(WRAPPER, encoding="utf-8")
    shim.write_text(f'#!/bin/sh\nexec {sys.executable} -B {wrapper} "$@"\n', encoding="utf-8")
    shim.chmod(0o755)
    log.unlink(missing_ok=True)
    env = {**environment(), "PATH": f"{shim.parent}{os.pathsep}{os.environ['PATH']}", "AUDIT_LOG": str(log)}
    done = subprocess.run(["sh", "-c", line.lstrip("@-")], cwd=project, env=env, text=True, capture_output=True,
                          timeout=120)
    assert done.returncode == 0, f"{line}: {done.stdout}{done.stderr}"
    return [event for each in log.read_text(encoding="utf-8").splitlines() for event in json.loads(each)]


def findings_of(project: Path, events: list[list[str]], files: list[str], report: list[str] | None = None) -> list[str]:
    exempt = report or []
    seen = {path for kind, path in events if not held(kind, path, files) and not path.startswith("..")
            and not (kind in ("stat", "lstat") and path in exempt)}
    return sorted(path for path in seen if not ignored(project, path))


class HeldCase(RecordCase):
    SHAPES = tuple(SHAPE_TABLE)
    audits: dict[str, tuple[Path, dict[str, list[list[str]]], dict[str, list[str]]]]

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.audits = {}

    def install(self, project: Path) -> None:
        """An integration installed and projected, and a manifest listing a template, as `./init` leaves them."""
        (project / ".specify" / "templates").mkdir(parents=True, exist_ok=True)
        (project / SAMPLE).write_text("# a template\n", encoding="utf-8")
        (project / ".specify" / "integration.json").write_text(
            json.dumps({"installed_integrations": ["claude"], "default_integration": "claude"}), encoding="utf-8")
        done = subprocess.run(["python3", "-B", "scripts/agents/project.py"], cwd=project, env=environment(),
                              text=True, capture_output=True, timeout=120)
        assert done.returncode == 0, done.stdout + done.stderr
        digest = hashlib.sha256((project / SAMPLE).read_bytes()).hexdigest()
        (project / MANIFEST).parent.mkdir(parents=True, exist_ok=True)
        (project / MANIFEST).write_text(json.dumps({"integration": "claude", "files": {SAMPLE: digest}}),
                                        encoding="utf-8")

    def audit(self, shape: str) -> tuple[Path, dict[str, list[list[str]]], dict[str, list[str]]]:
        """A shape's project with the integration in, what each of the four touched, and each one's recorded files."""
        if shape not in self.audits:
            project = self.project(shape)
            self.install(project)
            data = loaded(project)["checks"]
            recipes = recipes_of(project)
            events: dict[str, list[list[str]]] = {}
            for name in FOUR:
                events[name] = [event for line in recipes[name] for event in
                                touched(project, line, self.parent / f"audit-{name}")]
            self.audits[shape] = (project, events, {name: data[name]["inputs"]["files"] for name in FOUR})
        return self.audits[shape]

    def buildable(self, shape: str) -> bool:
        return record(self.project(shape)).returncode == 0  # a shape whose record is refused has no table to hold


class AuditHeldTest(HeldCase):
    maxDiff = None

    def test_e1_every_path_a_check_touches_lies_under_its_recorded_inputs(self) -> None:
        findings = []
        for shape in self.SHAPES:
            if not self.buildable(shape):
                continue
            project, events, files = self.audit(shape)
            findings += [f"{shape}: {name} touched {path}, under none of its inputs" for name in FOUR
                         for path in findings_of(project, events[name], files[name],
                                                 reported(project) if name in REPORT_ONLY else None)]
        self.assertEqual(findings, [])

    def test_e2_teeth_dropping_drive_json_from_the_row_names_it(self) -> None:
        project, events, files = self.audit("standard-python")
        narrowed = [path for path in files["check-agents"] if path != ".specify/drive.json"]
        report = reported(project)
        self.assertEqual(findings_of(project, events["check-agents"], files["check-agents"], report), [])
        self.assertEqual(findings_of(project, events["check-agents"], narrowed, report), [".specify/drive.json"])

    def test_the_report_only_reads_are_still_made(self) -> None:
        """An exemption nothing needs any more is stale, as `NOT_AN_INPUT` is when no check fires it."""
        project, events, files = self.audit("standard-python")
        bare = findings_of(project, events["check-agents"], files["check-agents"])
        self.assertEqual(bare, reported(project))

    def test_the_manifests_file_and_the_projections_were_touched(self) -> None:
        _, events, _ = self.audit("standard-python")
        speckit = {path for _, path in events["check-speckit"]}
        agents = {path for _, path in events["check-agents"]}
        self.assertIn(SAMPLE, speckit)
        self.assertTrue(any(path.startswith(".claude/skills/") for path in agents), sorted(agents)[:20])
        self.assertIn("CLAUDE.md", agents)


def recipes_of(project: Path) -> dict[str, list[str]]:
    return {name: lines for name, (_, lines) in database(project).items()}


class ScanTest(HeldCase):
    def test_e3_the_scan_walks_all_four_scripts_of_check_agents(self) -> None:
        project = self.project("standard-python")
        entries = entries_of(recipes_of(project)["check-agents"])
        names = ["cruise.py", "drive.py", "models.py", "project.py"]
        self.assertEqual(sorted(Path(entry).name for entry in entries), names)
        walked = {path.name for entry in entries for path in modules_of(project, project / entry)}
        self.assertTrue({"models.py", "drive.py", "cruise.py", "project.py"} <= walked)

    def test_e4_limit_ii_a_claiming_check_that_reads_the_registry_fails(self) -> None:
        project = self.project("standard-python")
        table = project / "scripts" / "verify_scoped" / "table.py"
        table.write_text(table.read_text(encoding="utf-8").replace(
            '(EVERYTHING,), ("git",), ("CODEGRAPH_GATE_NO_SYNC",), False, "it reads every tracked file"',
            '(EVERYTHING,), ("git",), ("CODEGRAPH_GATE_NO_SYNC",), True, None'), encoding="utf-8")
        script = project / "scripts" / "check-codegraph.py"
        script.write_text(script.read_text(encoding="utf-8") + '\nREGISTRY = "agents/registry.json"\n',
                          encoding="utf-8")
        data = loaded(project)
        self.assertEqual((data["checks"]["check-codegraph"]["claims"], data["checks"]["check-codegraph"]["always"]),
                         (True, None))
        found = derived_readers(project, data, recipes_of(project))
        self.assertEqual([line.split(" reads ")[0] for line in found], ["check-codegraph"])
        self.assertIn("registry.json", found[0])
