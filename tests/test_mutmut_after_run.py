"""S42 T009 (rule 8 · AC-S42-9): after a Python run the stamp, `check-imports` and the scoped gate hold.

A fake `uv` written here stands in front of the stamp fixture's: it answers mutmut's version, writes the `mutants/` tree
a generation leaves (a copy of `src/` and `tests/`, a `.meta` per source file, `mutmut-stats.json`) and the results of
`mutmut run`, and hands every other call to the stand-in. `make`, the scripts and the stamp are the project's own.
Nothing here starts mutmut: the one real run of the slice is T012's.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from scoped_fixture import SLICE, ShapeCase
from stamp_fixture import git
from support import FactoryTestCase, commit_all
from test_gate_walks import run_gate

from slipwai.assets import ROOT

sys.dont_write_bytecode = True

FAKE_UV = f"""#!{sys.executable}
import json, os, shutil, sys
args = sys.argv[1:]
stand_in = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uv-stand-in")
rest = args[args.index("--project") + 2:] if args[:1] == ["run"] and "--project" in args else []


def log(word):
    with open(os.environ["STANDIN_LOG"], "a", encoding="utf-8") as handle:
        handle.write(word + "\\t" + " ".join(args) + "\\n")


def metas(code):
    for current, _, names in os.walk("mutants"):
        for name in names:
            if name.endswith(".meta"):
                path = os.path.join(current, name)
                keys = json.load(open(path, encoding="utf-8"))["exit_code_by_key"]
                json.dump({{"exit_code_by_key": {{key: code for key in keys}}}}, open(path, "w", encoding="utf-8"))


if rest[:2] == ["python", "-c"] and "importlib.metadata" in rest[2]:
    print("3.8.0")
    sys.exit(0)
if rest[:2] == ["python", "-c"]:
    log("generate")
    for top in ("src", "tests"):
        shutil.copytree(top, os.path.join("mutants", top))
    for current, _, names in os.walk("src"):
        for name in names:
            path = os.path.join(current, name)
            if name.endswith(".py") and "def " in open(path, encoding="utf-8").read():
                module = path[:-3].replace(os.sep, ".")
                meta = os.path.join("mutants", path + ".meta")
                keys = {{module + ".x_f__mutmut_1": None}}
                json.dump({{"exit_code_by_key": keys}}, open(meta, "w", encoding="utf-8"))
    json.dump({{}}, open(os.path.join("mutants", "mutmut-stats.json"), "w", encoding="utf-8"))
    sys.exit(0)
if rest[:2] == ["mutmut", "run"]:
    log("mutmut-run")
    metas(int(os.environ.get("FAKE_CODE", "1")))
    sys.exit(0)
os.execv(stand_in, [stand_in, *args])
"""
CODE = "def health() -> int:\n    return 1\n"
BAD_DOMAIN = "from ..adapters.store import save\n"
SERVICE = "apps/service"
IGNORED = "import sys, json, importlib.util\nsys.dont_write_bytecode = True\n" + (
    "spec = importlib.util.spec_from_file_location('s', 'scripts/verify-stamp.py')\n"
    "stamp = importlib.util.module_from_spec(spec); spec.loader.exec_module(stamp)\n"
    "print(json.dumps(stamp.key_parts({})[1]['ignored']))\n")


class PythonCase(ShapeCase):
    """A Python shape on `slice/S1` with the fake `uv` in front of the stamp fixture's."""

    shape = "standard-python"
    module = f"{SERVICE}/src/health_probe.py"

    def setUp(self) -> None:
        super().setUp()
        os.replace(self.bin / "uv", self.bin / "uv-stand-in")
        (self.bin / "uv").write_text(FAKE_UV, encoding="utf-8")
        (self.bin / "uv").chmod(0o755)
        self.write_baseline()

    def make(self, *words: str, **env: str | None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["make", *words], cwd=self.repo, env=self.environment({"SINCE": None, **env}), text=True,
                              capture_output=True, timeout=180)

    def mutmut_runs(self) -> list[str]:
        """What each `mutmut run` was handed after the service, one line each."""
        lines = self.log.read_text(encoding="utf-8").splitlines() if self.log.exists() else []
        return [line.partition("\t")[2] for line in lines if line.startswith("mutmut-run\t")]

    def state(self) -> tuple[Any, str, set[str]]:
        digest = subprocess.run([sys.executable, "-B", "-c", IGNORED], cwd=self.repo, env=self.environment(), text=True,
                                capture_output=True, check=True, timeout=60).stdout
        status = git(self.repo, "status", "--porcelain", "--ignored")
        return self.decided(self.scoped({"STANDIN_DRY": "1"})), digest, set(status.splitlines())


class AfterARunTest(PythonCase):
    def setUp(self) -> None:
        super().setUp()
        self.edit(self.module, CODE)
        self.write_baseline()

    def test_e1_a_passing_and_a_failing_run_of_either_target_leave_the_stamp_and_the_scoped_gate_alone(self) -> None:
        """Teeth: remove the `apps/*/mutants/` row from `EXEMPT` in `verify-stamp.py` and see it fail."""
        before = self.state()
        self.assertTrue(before[0][0], "the baseline selects nothing: the examples below would hold with no teeth")
        for code, status in (("1", 0), ("0", 2)):  # make's own status for a recipe that failed
            for target in ("mutation", "mutation-full"):
                done = self.make(target, FAKE_CODE=code)
                self.assertEqual(done.returncode, status, f"{target}: {done.stdout}{done.stderr}")
        after = self.state()
        self.assertEqual(after[:2], before[:2], "a run moved what the scoped gate or the stamp compares")
        left = after[2] - before[2]
        self.assertTrue(left, "the runs left nothing to ignore")
        self.assertTrue(all(line.startswith("!! ") and "apps/service/mutants/" in line for line in left), left)

    def test_e3_a_left_behind_mutants_directory_is_no_reach_unless_its_link_leaves_the_deployable(self) -> None:
        """Teeth: the last example, a link out of the deployable, is a reach."""
        base = self.state()[0]
        self.assertTrue(base[0], "the baseline selects nothing: the examples below would hold with no teeth")
        left = self.repo / SERVICE / "mutants"
        (left / ".venv").mkdir(parents=True)
        (left / ".venv/pyvenv.cfg").write_text("home = /usr/bin\n", encoding="utf-8")
        (left / "src").mkdir()
        (left / "src/x.py").write_text(CODE, encoding="utf-8")
        self.assertEqual(self.state()[0], base, "a copy of the sources with a pyvenv.cfg read as a reach")
        os.symlink("../src", left / "inside")  # back inside the service
        self.assertEqual(self.state()[0], base, "a link back inside the service read as a reach")
        (left / "inside").unlink()
        os.symlink("../../../scripts", left / "outside")  # out of the deployable
        self.assertNotEqual(self.state()[0], base)


class BordersTest(PythonCase):
    """HOLD (D117's borders and `SINCE` for Python, D150): the recipe carries no `SINCE`, and the fake `uv` sees it."""

    def setUp(self) -> None:
        super().setUp()
        self.edit(self.module, CODE)

    def test_e5_the_borders_and_since_decide_scoped_or_swept_for_python(self) -> None:
        scoped, swept = "--", ""
        for name, words, env, handed in (
                ("slice", ["mutation"], {}, scoped), ("CI", ["mutation"], {"CI": "true"}, swept),
                ("empty SINCE", ["mutation"], {"SINCE": ""}, swept),
                ("SINCE in CI", ["mutation"], {"SINCE": "main", "CI": "true"}, scoped),
                ("mutation-full", ["mutation-full", "SINCE=main"], {}, swept)):
            with self.subTest(case=name):
                self.forget_log()
                shutil.rmtree(self.repo / SERVICE / "mutants", ignore_errors=True)
                done = self.make(*words, **env)
                self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
                (run,) = self.mutmut_runs()
                self.assertEqual("--" in run.split(), handed == scoped, run)
        for how in (["checkout", "-q", "main"], ["checkout", "-q", "--detach", SLICE]):
            self.forget_log()
            shutil.rmtree(self.repo / SERVICE / "mutants", ignore_errors=True)
            git(self.repo, *how)
            with self.subTest(border=how[-1]):
                self.assertEqual(self.make("mutation").returncode, 0)
                (run,) = self.mutmut_runs()
                self.assertNotIn("--", run.split(), run)


class ImportsTest(FactoryTestCase):
    """`check-imports` prunes `mutants` at the root of a recorded Python deployable, beside its `pyproject.toml`, and
    nowhere else."""

    def plant(self, repo: Path, base: str) -> Path:
        (repo / base / "domain").mkdir(parents=True)
        (repo / base / "domain/evil.py").write_text(BAD_DOMAIN, encoding="utf-8")
        return repo / base

    def test_e2_a_mutants_copy_at_a_python_deployable_s_root_is_neither_read_nor_a_violation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "imports", "event-modelling", "python")
            self.plant(repo, f"{SERVICE}/mutants/src/pkg")
            done = run_gate(repo, "scripts/check-imports.py")
            self.assertEqual((done.returncode, done.stderr), (0, ""), done.stdout)

    def test_e2_hold_a_mutants_directory_anywhere_else_is_read(self) -> None:
        """HOLD (teeth: prune every directory called `mutants` and see the second fail)."""
        for base in (f"{SERVICE}/src/mutants", f"{SERVICE}/docs/mutants", "apps/other/mutants/src/pkg"):
            with self.subTest(base=base), tempfile.TemporaryDirectory() as directory:
                repo = self.generate(directory, "imports", "event-modelling", "python")
                self.plant(repo, base)
                done = run_gate(repo, "scripts/check-imports.py")
                self.assertEqual(done.returncode, 1, done.stdout)
                self.assertIn(f"{base}/domain/evil.py:1", done.stderr)

    def test_e2_hold_a_mutants_directory_at_a_go_or_typescript_deployable_s_root_is_read(self) -> None:
        for language in ("go", "typescript"):
            with self.subTest(language=language), tempfile.TemporaryDirectory() as directory:
                repo = self.generate(directory, "imports", "event-modelling", language)
                self.plant(repo, f"{SERVICE}/mutants")
                done = run_gate(repo, "scripts/check-imports.py")
                self.assertEqual(done.returncode, 1, done.stdout)
                self.assertIn(f"{SERVICE}/mutants/domain/evil.py:1", done.stderr)

    def test_e2_a_package_called_mutants_under_src_is_read(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "imports", "event-modelling", "python")
            self.plant(repo, f"{SERVICE}/src/mutants")
            done = run_gate(repo, "scripts/check-imports.py")
            self.assertEqual(done.returncode, 1, done.stdout)


class RefusalAfterTest(FactoryTestCase):
    """`java-quarkus` still refuses, and a Python service beside it or beside Go runs only if it changed."""

    parent: Path
    projects: dict[str, Path]

    @classmethod
    def setUpClass(cls) -> None:
        cls.parent = Path(tempfile.mkdtemp(prefix="mutmut-after-"))
        cls.addClassCleanup(shutil.rmtree, cls.parent, ignore_errors=True)
        cls.projects = {}

    def project(self, name: str) -> Path:
        if name in self.projects:
            return self.projects[name]
        language = {"quarkus": "java-quarkus", "go-python": "go", "quarkus-python": "java-quarkus"}[name]
        made = self.generate(self.parent, name, "standard", language, "none", http="none")
        if name.endswith("python") and name != "python":
            subprocess.run([str(ROOT / "slipwai"), "add-service", "second", "--language", "python"], cwd=made,
                           check=True, capture_output=True, timeout=120)
            commit_all(made, "second")
        git(made, "checkout", "-q", "-b", "slice/S1")
        self.projects[name] = made
        return made

    def edit(self, project: Path, path: str) -> None:
        target = project / path
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as handle:
            handle.write("\n# an edit\n")

    def make(self, project: Path, bin_dir: Path, *words: str) -> subprocess.CompletedProcess[str]:
        env = {k: v for k, v in os.environ.items() if k not in ("CI", "GITHUB_ACTIONS", "GITLAB_CI", "SINCE")}
        env.update({"PATH": f"{bin_dir}{os.pathsep}{env['PATH']}", "STANDIN_LOG": str(bin_dir / "log")})
        return subprocess.run(["make", *words], cwd=project, env=env, text=True, capture_output=True, timeout=180)

    def fake_bin(self) -> Path:
        directory = Path(tempfile.mkdtemp(dir=self.parent))
        (directory / "uv").write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")  # a Python run would fail loudly here
        (directory / "uv").chmod(0o755)
        return directory

    def test_e4_quarkus_still_refuses_with_its_setup_message_on_both_targets(self) -> None:
        """HOLD (teeth: change the Quarkus message in `native_commands` and see it fail)."""
        project = self.project("quarkus")
        self.edit(project, "apps/service/src/main/java/com/x/Foo.java")
        for target in ("mutation", "mutation-full"):
            with self.subTest(target=target):
                done = self.make(project, self.fake_bin(), target)
                self.assertEqual(done.returncode, 2, done.stdout)
                self.assertIn("Configure PIT for the domain packages only", done.stdout)

    def test_e4_a_python_service_beside_quarkus_runs_and_quarkus_is_refused(self) -> None:
        project = self.project("quarkus-python")
        self.edit(project, "apps/service/src/main/java/com/x/Foo.java")
        self.edit(project, "apps/second/src/second/probe.py")
        bin_dir = self.fake_bin()
        done = self.make(project, bin_dir, "mutation")
        self.assertEqual(done.returncode, 2, done.stdout)
        self.assertIn("mutation: refuse apps/service — Configure PIT for the domain packages only", done.stdout)
        self.assertIn("mutation: scope apps/second — src/second/probe.py", done.stdout)
        self.assertNotIn("mutmut", done.stdout.split("mutation: scope apps/second")[0].split("refuse apps/service")[1])

    def test_e4_a_go_service_beside_python_is_skipped_when_only_python_changed(self) -> None:
        project = self.project("go-python")
        self.edit(project, "apps/second/src/second/probe.py")
        done = self.make(project, self.fake_bin(), "mutation")
        self.assertIn("mutation: skip apps/service — no changed production file", done.stdout)
        self.assertIn("mutation: scope apps/second — src/second/probe.py", done.stdout)
