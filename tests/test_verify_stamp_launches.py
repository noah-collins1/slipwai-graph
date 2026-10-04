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

from slipwai.assets import ROOT

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


# What a shell script a recipe launches reads from the environment — the scan reads Python, not shell, so each such
# script is named here with its variables, which `Makefile` recipes reach through `./name` (T032, D81).
# A variable that selects which executable runs, with the tool whose version is asked for it: the stamp must read it.
SELECTS = {"JAVA_HOME": "java"}
# A variable that only configures what the script does, with the reason it is no part of the key.
CONFIGURES = {
    "MVNW_REPOURL": "where the pinned Maven distribution is downloaded from; its URL and checksum are committed",
    "MVNW_VERBOSE": "how much the wrapper says",
    "MVNW_USERNAME": "a credential for that download",
    "MVNW_PASSWORD": "a credential for that download",
    "MAVEN_USER_HOME": "where the pinned distribution is cached",
    "HOME": "where the pinned distribution is cached, by default",
    "PROCESSOR_ARCHITECTURE": "Windows: whether the pinned distribution is Maven or the Maven daemon",
    "PROCESSOR_ARCHITEW6432": "Windows: the same",
}
# A name the script assigns before it reads, so it is the script's own and the environment selects nothing by it.
LOCAL = {"TMP_DOWNLOAD_DIR", "MVN_CMD", "JAVACMD", "JAVACCMD", "MAVEN_HOME"}
READ = re.compile(r"\$\{?([A-Z][A-Z0-9_]*)")
SHELL_SCRIPT = re.compile(rb"^#!\s*/\S*(?:/env\s+)?(?:ba|da|z)?sh\b")


def shell_variables(path: Path) -> set[str]:
    """The upper-case names a shell script reads."""
    return set(READ.findall(path.read_text(encoding="utf-8")))


def assigned(path: Path, name: str) -> bool:
    return re.search(rf"(?m)^[ \t]*(?:if\s+|export\s+)?{name}=", path.read_text(encoding="utf-8")) is not None


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

    def shell_scripts(self, project: Path) -> list[Path]:
        """Every shell script a recipe of the gate launches by path: `./scripts/verify`, `./mvnw` after a `cd`."""
        rules = makefile_rules((project / "Makefile").read_text(encoding="utf-8"))
        found: set[Path] = set()
        for target in gate_targets(rules):
            for line in rules[target][1]:
                directories = [project] + [project / cd for cd in CD_TARGET.findall(line)]
                for word in launched(line):
                    for directory in directories:
                        path = directory / word
                        if word.startswith(("./", "scripts/")) and path.is_file() and SHELL_SCRIPT.match(
                                path.read_bytes()[:80]):
                            found.add(path)
        return sorted(found)

    def unaccounted(self, project: Path, scripts: list[Path]) -> list[str]:
        """What a shell script reads that is neither a variable that selects the executable, one that only configures
        it, nor the script's own."""
        missing = []
        for path in scripts:
            for name in sorted(shell_variables(path)):
                local = name in LOCAL and assigned(path, name)
                if name not in SELECTS and name not in CONFIGURES and not local:
                    missing.append(f"{path.relative_to(project).as_posix()}: reads {name}")
        return missing

    def test_every_shell_script_the_gate_launches_names_the_variables_that_select_what_runs(self) -> None:
        """T032: the wrapper and each backend's `scripts/verify` do not hold nothing: a variable they read is a choice
        of executable, which the stamp asks, or a configuration, named with the reason, or the script's own."""
        selecting: set[str] = set()
        self.assertTrue(self.shell_scripts(self.project(SHAPES[0])), "the derivation found no shell script")
        for shape in SHAPES:
            with self.subTest(shape=shape[0]):
                project = self.project(shape)
                scripts = self.shell_scripts(project)
                self.assertEqual(self.unaccounted(project, scripts), [])
                for path in scripts:
                    selecting.update(shell_variables(path) & set(SELECTS))
                    for name in shell_variables(path) & set(SELECTS):
                        self.assertIn(SELECTS[name], stamp_tools((project / "Makefile").read_text(encoding="utf-8")))
        self.assertEqual(sorted(selecting), sorted(SELECTS), "a variable named as selecting that no script reads")

    def test_a_variable_that_selects_what_runs_must_be_read_by_the_stamp(self) -> None:
        """T032: naming it is not enough; the script that asks the tool reads it."""
        script = (ROOT / "assets/toolkit/scripts/verify-stamp.py").read_text(encoding="utf-8")
        for name in SELECTS:
            self.assertIn(f'os.environ.get("{name}"', script)

    def test_a_variable_a_wrapper_gains_that_selects_what_runs_fails_the_scan(self) -> None:
        """T032: the derivation has teeth on shell, as `test_a_read_planted_in_each_script` has on Python."""
        project = self.project(SHAPES[5])
        wrapper = project / "apps/service/mvnw"
        original = wrapper.read_text(encoding="utf-8")
        wrapper.write_text(original + '\n"$JAVA_CMD_OVERRIDE" -version\n', encoding="utf-8")
        try:
            found = self.unaccounted(project, self.shell_scripts(project))
        finally:
            wrapper.write_text(original, encoding="utf-8")
        self.assertEqual(found, ["apps/service/mvnw: reads JAVA_CMD_OVERRIDE"])

    def test_every_pinned_command_is_still_launched(self) -> None:
        seen: set[str] = set()
        for shape in SHAPES:
            project = self.project(shape)
            rules = makefile_rules((project / "Makefile").read_text(encoding="utf-8"))
            seen.update(word for t in gate_targets(rules) for line in rules[t][1] for word in launched(line))
        self.assertEqual(sorted(set(PINNED) - seen), [], "a reason for a launch no recipe makes any more")


