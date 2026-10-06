"""S08 T005 (rule 4 · AC-S08-2): the one real Go run — a two-service starter on a slice branch with one file changed.

Gated as `tests/test_matrix.py` gates its Go mutation test: by `backends_under_test()` and a `go` on `PATH`. Gremlins is
started for `apps/service` and for nothing else: the other service has no report because no tool ran for it.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile

from stamp_fixture import git
from support import FactoryTestCase, backends_under_test, commit_all
from test_mutation_borders import clean_environment

from slipwai.assets import ROOT


class RealGoTest(FactoryTestCase):
    def test_e6_make_mutation_mutates_the_one_changed_file_and_starts_nothing_for_the_other_service(self) -> None:
        if "go" not in backends_under_test() or shutil.which("go") is None:
            self.skipTest("the Go slice of the matrix, with a go toolchain")
        with tempfile.TemporaryDirectory(prefix="real-go-", dir="/tmp") as directory:
            repo = self.generate(directory, "scoped2", "standard", "go", "none", http="none")
            subprocess.run([str(ROOT / "slipwai"), "add-service", "billing", "--backend", "go"], cwd=repo, check=True,
                           capture_output=True, timeout=300)
            commit_all(repo, "billing")
            git(repo, "checkout", "-q", "-b", "slice/S1")
            health = repo / "apps/service/health/health.go"
            health.write_text(  # the starter's Check has nothing to mutate; this one has a condition its test kills
                'package health\n\ntype Status struct {\n\tStatus string `json:"status"`\n}\n\n'
                'func Check() Status {\n\tlabel := "ok"\n\tif len(label) == 0 {\n\t\tlabel = "unknown"\n\t}\n'
                '\treturn Status{Status: label}\n}\n', encoding="utf-8")
            done = subprocess.run(["make", "mutation"], cwd=repo, env=clean_environment(), text=True,
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=600)
            self.assertEqual(done.returncode, 0, done.stdout[-3000:])
            lines = done.stdout.splitlines()
            self.assertRegex(lines[0], r"^mutation: scoped to 1 changed file\(s\) since `main` at [0-9a-f]+: "
                                       r"apps/service/health/health\.go$")
            self.assertIn("mutation: scope apps/service — health/health.go", lines)
            self.assertIn("mutation: skip apps/billing — no changed production file", lines)
            self.assertEqual(lines[-1], "mutation: 1 scoped, 0 swept, 1 skipped, 0 refused; passed")
            report = json.loads((repo / "apps/service/gremlins.json").read_text(encoding="utf-8"))
            self.assertEqual({entry["file_name"] for entry in report["files"]}, {"health/health.go"})
            self.assertFalse((repo / "apps/billing/gremlins.json").exists())
