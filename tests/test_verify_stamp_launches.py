"""R5 (AC-S03-14), T031: every tool the machine supplies that a recipe of the gate launches is asked.

The subject is derived from the generated `Makefile` of every shape `test_verify_stamp_scan` generates, by the same
walk from `verify-checks` through prerequisites and `$(MAKE)`: the first word of each command on each recipe line.
Each must be on that project's tool list (the `--tool` words of `VERIFY_STAMP`), a file of the project, shell syntax,
or named below with the reason it is pinned. A recipe that later launches another machine tool fails here.
"""
from __future__ import annotations

import re
import shutil
import tempfile
from pathlib import Path

from support import FactoryTestCase
from test_verify_stamp_scan import SHAPES, gate_targets, makefile_rules

# Words that are the shell's, not a tool the machine supplies.
SHELL = {"echo", "cd", "test", "[", "for", "touch", "true", "exit", "continue", "done", "do", "then", "fi", "if"}
# Launched by a recipe the gate runs and not on the list: the reason is the value.
PINNED = {
    "gofmt": "ships in the Go distribution beside the `go` the list asks; one install, one version",
}
COMMAND_SUBSTITUTION = re.compile(r"\$\$\(\s*([\w./-]+)")
QUOTED = re.compile(r"\"[^\"]*\"|'[^']*'")
SEPARATORS = re.compile(r"&&|\|\||[;|]")
CD_TARGET = re.compile(r"\bcd\s+([\w./-]+)")


def stamp_tools(makefile: str) -> list[str]:
    line = re.search(r"^VERIFY_STAMP :=(.*)$", makefile, re.M)
    assert line is not None
    words = line.group(1).split()
    return [words[i + 1] for i, word in enumerate(words) if word == "--tool"]


def launched(line: str) -> list[str]:
    """The first word of every command on a recipe line, command substitutions included, shell words and variable
    references (`$(MAKE)`, assignments) left out."""
    line = line.strip().lstrip("@-+ ")
    found = COMMAND_SUBSTITUTION.findall(line)
    words = []
    for command in SEPARATORS.split(QUOTED.sub('""', line)):
        parts = command.split()
        while parts and parts[0] in ("do", "then"):
            parts = parts[1:]
        if parts:
            words.append(parts[0])
    return found + [word for word in words if word not in SHELL and not word.startswith("$") and "=" not in word]


_projects: dict[str, Path] = {}


class EveryLaunchIsAskedTest(FactoryTestCase):
    def project(self, shape: tuple[str, str, str, str, dict[str, str]]) -> Path:
        _, profile, backend, frontend, axes = shape
        name = f"launch{SHAPES.index(shape)}"
        if name not in _projects:
            directory = tempfile.mkdtemp(prefix="stamp-launch-")
            self.addClassCleanup(shutil.rmtree, directory, ignore_errors=True)
            self.addClassCleanup(_projects.pop, name, None)
            _projects[name] = self.generate(directory, name, profile, backend, frontend, **axes)
        return _projects[name]

    def unasked(self, project: Path) -> dict[str, str]:
        """Each command a gate recipe launches that is neither asked, a file, shell nor pinned, with the line."""
        text = (project / "Makefile").read_text(encoding="utf-8")
        asked = set(stamp_tools(text))
        rules = makefile_rules(text)
        missing: dict[str, str] = {}
        for target in sorted(gate_targets(rules)):
            for line in rules[target][1]:
                directories = [project] + [project / found for found in CD_TARGET.findall(line)]
                for word in launched(line):
                    is_file = word.startswith(("./", "scripts/")) and any((d / word).is_file() for d in directories)
                    if word not in asked and word not in PINNED and not is_file:
                        missing[word] = f"{target}: {line}"
        return missing

    def test_every_command_a_recipe_of_the_gate_launches_is_asked_in_every_shape(self) -> None:
        for shape in SHAPES:
            with self.subTest(shape=shape[0]):
                self.assertEqual(self.unasked(self.project(shape)), {})

    def test_a_tool_a_recipe_launches_that_the_list_lacks_is_found(self) -> None:
        """The derivation has teeth: a line added to a gate recipe that launches `cargo` is the one finding."""
        project = self.project(SHAPES[0])
        makefile = project / "Makefile"
        original = makefile.read_text(encoding="utf-8")
        makefile.write_text(original + "\nverify-checks: check-cargo\ncheck-cargo:\n\t@cargo test && echo ok\n",
                            encoding="utf-8")
        try:
            self.assertEqual(sorted(self.unasked(project)), ["cargo"])
        finally:
            makefile.write_text(original, encoding="utf-8")

    def test_every_pinned_command_is_still_launched(self) -> None:
        seen: set[str] = set()
        for shape in SHAPES:
            project = self.project(shape)
            rules = makefile_rules((project / "Makefile").read_text(encoding="utf-8"))
            seen.update(word for t in gate_targets(rules) for line in rules[t][1] for word in launched(line))
        self.assertEqual(sorted(set(PINNED) - seen), [], "a reason for a launch no recipe makes any more")


