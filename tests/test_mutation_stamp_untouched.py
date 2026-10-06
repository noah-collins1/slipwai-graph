"""S08 T006 (rule 8, folded · AC-S08-14): after `make mutation` and `make mutation-full` the stamp reads nothing new.

Real runs on the Go and the Spring starter, gated as their own suites are. The tree git ignores differs from before
only by paths `.gitignore` already names (the Go report, Maven's `target/`), the stamp's own digest of the ignored
files and the key built from it are what they were, and so a reusable stamp still stands and `verify-scoped` has no
ignored file to broaden on. Evidence is the files and the digests, never a clock.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from stamp_fixture import git
from support import FactoryTestCase, backends_under_test
from test_mutation_borders import clean_environment
from test_mutation_scope_real_spring import spring_project

SNIPPET = """
import importlib.util, json, sys
sys.dont_write_bytecode = True
sys.path.insert(0, "scripts")
from verify_scoped import record
spec = importlib.util.spec_from_file_location("stamp", "scripts/verify-stamp.py")
stamp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stamp)
found = record.database("make", "Makefile").variables["VERIFY_STAMP"]
tools = stamp.machine_tools(stamp.Options(["--make", "make", *found.split()]))
print(json.dumps({"key": stamp.build_key(tools)["key"], "ignored": stamp.key_parts(tools)[1]["ignored"]}))
"""
NAMED = ("gremlins.json", "/target/")


def stamp_inputs(project: Path) -> dict[str, str]:
    done = subprocess.run(["python3", "-B", "-c", SNIPPET], cwd=project, env=clean_environment(), text=True,
                          capture_output=True, timeout=180)
    assert done.returncode == 0, done.stderr[-2000:]
    return json.loads(done.stdout.splitlines()[-1])


class StampUntouchedTest(FactoryTestCase):
    def untouched_by(self, repo: Path) -> None:
        before_tree = git(repo, "status", "--porcelain", "--ignored").splitlines()
        before = stamp_inputs(repo)
        for target in ("mutation", "mutation-full"):
            done = subprocess.run(["make", target], cwd=repo, env=clean_environment(), text=True,
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=600)
            self.assertEqual(done.returncode, 0, done.stdout[-3000:])
        after_tree = git(repo, "status", "--porcelain", "--ignored").splitlines()
        added = [line for line in after_tree if line not in before_tree]
        for line in added:  # (a) only paths .gitignore already names, and only the ones a tool writes by design
            self.assertTrue(line.startswith("!! ") and any(word in "/" + line[3:] for word in NAMED), line)
        after = stamp_inputs(repo)
        self.assertEqual(after["ignored"], before["ignored"], "(b) the stamp's digest of the ignored files moved")
        self.assertEqual(after["key"], before["key"], "(c) the stamp's key moved, so it would not reuse")

    def test_e8_the_go_starter(self) -> None:
        if "go" not in backends_under_test() or shutil.which("go") is None:
            self.skipTest("the Go slice of the matrix, with a go toolchain")
        with tempfile.TemporaryDirectory(prefix="untouched-go-", dir="/tmp") as directory:
            repo = self.generate(directory, "untouched-go", "standard", "go", "none", http="none")
            git(repo, "checkout", "-q", "-b", "slice/S1")
            (repo / "apps/service/health/health.go").write_text(
                'package health\n\ntype Status struct {\n\tStatus string `json:"status"`\n}\n\n'
                'func Check() Status {\n\tlabel := "ok"\n\tif len(label) == 0 {\n\t\tlabel = "unknown"\n\t}\n'
                '\treturn Status{Status: label}\n}\n', encoding="utf-8")
            self.untouched_by(repo)

    def test_e8_the_spring_starter(self) -> None:
        with tempfile.TemporaryDirectory(prefix="untouched-spring-", dir="/tmp") as directory:
            repo = spring_project(self, directory)
            if repo is None:
                self.skipTest("the Spring slice of the matrix, with a JDK and a runnable mvnw")
            self.untouched_by(repo)
