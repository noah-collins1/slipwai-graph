"""S08 T005 (rule 4 · AC-S08-2): `go-mutation.py --file`, the files handed over instead of a `git diff`.

The script is loaded as a module (bytecode off, as `tests/test_mutation.py` does) and run in this process with a fake
`go` and a fake `git` first on `PATH`, written here: the fake `go` logs its arguments and writes the report Gremlins
would, the fake `git` fails when it is called. Nothing is mutated and nothing is staged outside a temporary directory.
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

from slipwai.assets import LANGUAGE_ROOT

sys.dont_write_bytecode = True
SCRIPT = LANGUAGE_ROOT / "go" / "scripts/go-mutation.py"
FAKE_GO = """#!/usr/bin/env python3
import json, os, sys
with open(os.environ["FAKE_LOG"], "a", encoding="utf-8") as log:
    log.write(json.dumps(["go", *sys.argv[1:]]) + "\\n")
if sys.argv[1:2] == ["run"]:
    out = sys.argv[sys.argv.index("--output") + 1]
    with open(out, "w", encoding="utf-8") as report:
        json.dump({"files": [{"file_name": "a.go", "mutations": [{"status": "KILLED"}]}]}, report)
"""
FAKE_GIT = """#!/bin/sh
echo git >> "$FAKE_LOG"
exit 1
"""
YAML = "unleash:\n  exclude-files:\n    - \"cmd/.*\"\n"


def loaded() -> Any:
    specification = importlib.util.spec_from_file_location("go_mutation_under_test", SCRIPT)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    was, sys.dont_write_bytecode = sys.dont_write_bytecode, True
    try:
        specification.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = was
    return module


def executable(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


class FakeTools:
    """A directory first on `PATH` holding a fake `go` (and, if asked, a fake `git`), and the log they share."""

    def __init__(self, directory: Path, git: bool = True) -> None:
        self.bin = directory / "bin"
        self.bin.mkdir()
        self.log = directory / "tools.log"
        executable(self.bin / "go", FAKE_GO)
        if git:
            executable(self.bin / "git", FAKE_GIT)

    def entries(self) -> list[Any]:
        lines = self.log.read_text(encoding="utf-8").splitlines() if self.log.exists() else []
        return [json.loads(line) if line.startswith("[") else line for line in lines]

    def runs(self) -> list[list[str]]:
        return [entry for entry in self.entries() if isinstance(entry, list) and entry[1:2] == ["run"]]

    def environment(self) -> dict[str, str]:
        return {"PATH": f"{self.bin}{os.pathsep}{os.environ['PATH']}", "FAKE_LOG": str(self.log)}


class FileTest(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = Path(tempfile.mkdtemp(prefix="go-file-", dir="/tmp"))
        self.addCleanup(shutil.rmtree, self.directory, ignore_errors=True)
        self.service = self.directory / "svc"
        for name in ("a.go", "b.go", "a_test.go", "cmd/serve/main.go"):
            (self.service / name).parent.mkdir(parents=True, exist_ok=True)
            (self.service / name).write_text("package x\n", encoding="utf-8")
        (self.service / "go.mod").write_text("module example.com/svc\n\ngo 1.22\n", encoding="utf-8")
        (self.service / ".gremlins.yaml").write_text(YAML, encoding="utf-8")
        self.tools = FakeTools(self.directory)

    def main(self, *arguments: str) -> tuple[int, str, str]:
        module = loaded()
        saved = dict(os.environ)
        os.environ.update(self.tools.environment())
        out, err = io.StringIO(), io.StringIO()
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                status = module.main(["go-mutation.py", str(self.service), *arguments])
        finally:
            os.environ.clear()
            os.environ.update(saved)
        return status, out.getvalue(), err.getvalue()

    def excludes(self) -> list[str]:
        (run,) = self.tools.runs()
        return [run[i + 1] for i, word in enumerate(run) if word == "--exclude-files"]

    def test_e1_one_file_is_staged_alone_and_git_is_never_asked(self) -> None:
        status, out, _ = self.main("--file", "a.go")
        self.assertEqual(status, 0, out)
        self.assertEqual(self.excludes(), ["cmd/.*", r"^b\.go$", r"^cmd/serve/main\.go$"])
        self.assertNotIn("git", self.tools.entries())
        self.assertIn("mutation: scoped to 1 given file(s): a.go", out)

    def test_e2_the_flag_repeats(self) -> None:
        status, out, _ = self.main("--file", "a.go", "--file", "b.go")
        self.assertEqual(status, 0, out)
        self.assertEqual(self.excludes(), ["cmd/.*", r"^cmd/serve/main\.go$"])
        self.assertIn("scoped to 2 given file(s): a.go, b.go", out)

    def test_e2_file_wins_over_since_and_says_so(self) -> None:
        status, out, _ = self.main("--since", "main", "--file", "a.go")
        self.assertEqual(status, 0, out)
        self.assertIn("scoped to 1 given file(s): a.go (--file wins; --since main is not read)", out)
        self.assertNotIn("git", self.tools.entries())

    def test_e2_a_file_the_yaml_excludes_is_dropped_and_named(self) -> None:
        status, out, _ = self.main("--file", "a.go", "--file", "cmd/serve/main.go")
        self.assertEqual(status, 0, out)
        self.assertIn(f"mutation: not mutated {self.service}/cmd/serve/main.go — outside Gremlins' configured targets",
                      out)
        self.assertIn("scoped to 1 given file(s): a.go", out)

    def test_e2_every_file_excluded_is_no_mutant_to_run_and_no_tool_starts(self) -> None:
        status, out, _ = self.main("--file", "cmd/serve/main.go", "--file", "a_test.go")
        self.assertEqual(status, 0, out)
        self.assertIn("no mutant to run", out)
        self.assertEqual(self.tools.runs(), [])

    def test_e2_a_file_flag_with_no_path_is_usage(self) -> None:
        status, _, err = self.main("--file")
        self.assertEqual(status, 2)
        self.assertIn("usage:", err)

    def test_e3_hold_since_is_as_published(self) -> None:
        """HOLD (teeth: make `--file` the default path and see `--since` stop reading git): the real `git` answers."""
        shutil.rmtree(self.tools.bin / "git", ignore_errors=True)
        (self.tools.bin / "git").unlink()
        identity = ["-c", "user.name=t", "-c", "user.email=t@l"]
        for command in (["init", "-q", "-b", "main"], ["add", "-A"], [*identity, "commit", "-q", "-m", "x"]):
            subprocess.run(["git", *command], cwd=self.directory, check=True, capture_output=True, timeout=60)
        (self.service / "b.go").write_text("package x\n// edited\n", encoding="utf-8")
        status, out, _ = self.main("--since", "HEAD")
        self.assertEqual(status, 0, out)
        self.assertIn("mutation: scoped to 1 changed file(s) since HEAD: b.go\n", out)
        self.assertEqual(self.excludes(), ["cmd/.*", r"^a\.go$", r"^cmd/serve/main\.go$"])


if __name__ == "__main__":
    unittest.main()
