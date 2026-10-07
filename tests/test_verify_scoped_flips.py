"""T017 (AC-S07-2, -8): every file input the four method-file rows declare is shown to be an input twice over.

Per (declared input, check): ONE change to the generated project that flips the check's own verdict, run as the
Makefile's `make check-<name>` before and after, and the scoped selection of the path that change touched, which picks
exactly the checks whose rows declare the input and names the path. The record is taken once; `choose` is called on it
with the touched path, so no run of the gate is spent on a selection. `NOT_FLIPPABLE` is the named, reasoned list of
declared inputs no change flips; it fails when an entry is flipped after all, and a declared input in neither
place fails.
"""
from __future__ import annotations

import hashlib
import importlib
import json
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any, NamedTuple

from test_verify_scoped_record import RecordCase, environment, record

from slipwai.assets import ROOT

sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "assets" / "toolkit" / "scripts"))

FOUR = ("check-agents", "check-speckit", "check-extensions", "check-constitution")
AGENTS, SPECKIT, EXTENSIONS, CONSTITUTION = FOUR
# Each declared input of the four rows, and the checks whose rows declare it (the table's, written out so that an input
# added to a row, or taken from one, fails here).
DECLARED: dict[str, tuple[str, ...]] = {
    ".specify/integration.json": (AGENTS,), ".specify/models.json": (AGENTS,), ".specify/drive.json": (AGENTS,),
    ".specify/cruise.json": (AGENTS,), "skills/": (AGENTS,), "commands/": (AGENTS,), "agents/": (AGENTS,),
    "AGENTS.md": (AGENTS, EXTENSIONS), ".specify/integrations/": (SPECKIT,),
    ".specify/presets/": (SPECKIT, CONSTITUTION),
    ".specify/memory/constitution.md": (SPECKIT, CONSTITUTION), ".slipwai/extensions.json": (EXTENSIONS,),
    "{web}": (EXTENSIONS,), "specs/": (CONSTITUTION,), ".specify/memory/.constitution-template.json": (CONSTITUTION,),
    ".specify/templates/constitution-template.md": (CONSTITUTION,),
}
# A declared input no change of a generated project flips the check's verdict through, (input, check) -> why.
NOT_FLIPPABLE: dict[tuple[str, str], str] = {}
TEMPLATE = "# [PROJECT_NAME] Constitution\n\n## Principle 1\n[PRINCIPLE_1_NAME]\n"
DRAFT = "# A constitution\n\nIt says nothing a principle needs.\n"
BLOCK = "\n<!-- extension:{key}:begin -->\nan edit\n<!-- extension:{key}:end -->\n"
CORE_TEMPLATE = ".specify/templates/constitution-template.md"
UNCHANGED = "none of its inputs changed"


def put(project: Path, relative: str, text: str) -> str:
    (project / relative).parent.mkdir(parents=True, exist_ok=True)
    (project / relative).write_text(text, encoding="utf-8")
    return relative


def append(project: Path, relative: str, text: str) -> str:
    (project / relative).write_text((project / relative).read_text(encoding="utf-8") + text, encoding="utf-8")
    return relative


def run(project: Path, *command: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=project, env=environment(), text=True, capture_output=True, timeout=120)


def integrate(project: Path, key: str, context: str | None = None) -> None:
    """The integration installed and its projections written, as `./init` leaves them: the check then holds files."""
    put(project, ".specify/integration.json", json.dumps({"installed_integrations": [key], "default_integration": key}))
    if context:
        put(project, context, "# context\n")
    done = run(project, "python3", "-B", "scripts/agents/project.py")
    assert done.returncode == 0, done.stderr


def elect(project: Path) -> None:
    put(project, ".slipwai/extensions.json", json.dumps({"schemaVersion": 1, "extensions": ["ux-gates"]}))


class Flip(NamedTuple):
    """`change` makes the one change and returns the path it touched; `before` is the verdict it flips from."""

    key: str
    check: str
    change: Callable[[Path], str]
    setup: Callable[[Path], None] = lambda project: None
    before: bool = True
    shape: str = "model-typescript-web"


def damage(relative: str, text: str) -> Callable[[Path], str]:
    return lambda project: put(project, relative, text)


def edit(relative: str) -> Callable[[Path], str]:
    return lambda project: append(project, relative, "\nan edit\n")


def claude(project: Path) -> None:
    integrate(project, "claude")


def gemini(project: Path) -> None:
    integrate(project, "gemini", "GEMINI.md")


def draft(project: Path) -> None:
    put(project, ".specify/memory/constitution.md", DRAFT)


def template_constitution(project: Path) -> None:
    put(project, ".specify/memory/constitution.md", TEMPLATE)
    put(project, CORE_TEMPLATE, TEMPLATE)


def manifest(project: Path) -> str:
    return put(project, ".specify/integrations/x.manifest.json",
               json.dumps({"integration": "x", "files": {"no-such-file.txt": "0" * 64}}))


def registry_gone(project: Path) -> str:
    (project / ".specify/presets/.registry").unlink()
    return ".specify/presets/.registry"


def web_gone(project: Path) -> str:
    shutil.rmtree(project / "apps" / "web")
    return "apps/web/src/App.tsx"


FLIPS = (
    Flip(".specify/integration.json", AGENTS, damage(".specify/integration.json",
                                                     '{"installed_integrations": ["nonesuch"]}'), claude),
    Flip(".specify/models.json", AGENTS, damage(".specify/models.json", "{}\n")),
    Flip(".specify/drive.json", AGENTS, damage(".specify/drive.json", '{"delegate": "nobody"}\n')),
    Flip(".specify/cruise.json", AGENTS, damage(".specify/cruise.json", "[]\n")),
    Flip("skills/", AGENTS, edit("skills/acceptance-review/SKILL.md"), claude),
    Flip("commands/", AGENTS, edit("commands/drive.md"), claude),
    Flip("agents/", AGENTS, edit("agents/drive-slice.md"), claude),
    Flip("AGENTS.md", AGENTS, lambda project: append(project, "AGENTS.md", BLOCK.format(key="codegraph")), gemini),
    Flip(".specify/integrations/", SPECKIT, manifest),
    Flip(".specify/presets/", SPECKIT, registry_gone),
    Flip(".specify/memory/constitution.md", SPECKIT,
         damage(".specify/memory/constitution.md", "The event sourced core is the premise.\n"),
         shape="standard-python"),
    Flip(".slipwai/extensions.json", EXTENSIONS,
         damage(".slipwai/extensions.json", json.dumps({"schemaVersion": 1, "extensions": ["nonesuch"]}))),
    Flip("AGENTS.md", EXTENSIONS, lambda project: append(project, "AGENTS.md", BLOCK.format(key="ux-gates"))),
    Flip("{web}", EXTENSIONS, web_gone, elect, before=False),
    Flip("specs/", CONSTITUTION, damage("specs/001-x/spec.md", "# a spec\n"), template_constitution),
    Flip(".specify/memory/constitution.md", CONSTITUTION, damage(".specify/memory/constitution.md", DRAFT)),
    Flip(".specify/memory/.constitution-template.json", CONSTITUTION,
         damage(".specify/memory/.constitution-template.json",
                json.dumps({"sha256": hashlib.sha256(DRAFT.encode()).hexdigest()})), draft, before=False),
    Flip(CORE_TEMPLATE, CONSTITUTION, damage(CORE_TEMPLATE, DRAFT), draft, before=False),
    Flip(".specify/presets/", CONSTITUTION, damage(".specify/presets/x/templates/constitution-template.md", DRAFT),
         draft, before=False),
)


class TableTest(RecordCase):
    def test_the_declared_inputs_are_the_rows_of_the_table_and_each_is_flipped_or_reasoned(self) -> None:
        table = importlib.import_module("verify_scoped.table")
        for name in FOUR:
            self.assertEqual(set(table.CHECKS[name].files), {key for key, who in DECLARED.items() if name in who}, name)
        flipped = {(flip.key, flip.check) for flip in FLIPS}
        every = {(key, name) for key, who in DECLARED.items() for name in who}
        self.assertEqual(len(flipped), len(FLIPS), "one flip for each input of each check")
        self.assertEqual(flipped | set(NOT_FLIPPABLE), every, "an input is neither flipped nor reasoned")
        self.assertEqual(flipped & set(NOT_FLIPPABLE), set(), "a flipped input is still listed as not flippable")
        self.assertTrue(all(reason.strip() for reason in NOT_FLIPPABLE.values()))


class FlipTest(RecordCase):
    record_of: dict[str, Any] = {}

    def recorded(self) -> dict[str, Any]:
        if not self.record_of:
            done = record(self.project("model-typescript-web"))
            self.assertEqual(done.returncode, 0, done.stderr)
            type(self).record_of = json.loads(done.stdout)
        return self.record_of

    def verdict(self, project: Path, name: str) -> subprocess.CompletedProcess[str]:
        return run(project, "make", name)

    def test_each_declared_input_flips_its_check_and_the_selection_names_the_checks_declaring_it(self) -> None:
        choose = importlib.import_module("verify_scoped.choose")
        data = importlib.import_module("verify_scoped.record").Database({}, {}, {})
        for flip in FLIPS:
            with self.subTest(input=flip.key, check=flip.check):
                project = self.project(flip.shape)
                flip.setup(project)
                before = self.verdict(project, flip.check)
                self.assertEqual(before.returncode == 0, flip.before, before.stdout + before.stderr)
                touched = flip.change(project)
                after = self.verdict(project, flip.check)
                self.assertEqual(after.returncode == 0, not flip.before, after.stdout + after.stderr)
                chosen = {item.unit: item for item in choose.choose(self.recorded(), data, [touched])}
                for name in FOUR:
                    if name in DECLARED[flip.key]:
                        self.assertEqual((chosen[name].runs, chosen[name].reason), (True, f"{touched} changed"), name)
                    else:
                        self.assertEqual((chosen[name].runs, chosen[name].reason), (False, UNCHANGED), name)
