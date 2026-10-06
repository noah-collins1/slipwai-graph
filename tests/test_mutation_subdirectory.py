"""S08 T026 (AC-S08-2, AC-S08-8): a project in a subdirectory of its repository compares every path from one root.

Real `git`: the repository is `outer`, the project is `outer/sub`, so git's tracked paths start `sub/` and
an untracked one does not. Each path source the script reads — the change set (tracked and untracked), the
`Makefile`, the scope and backend scripts, a service's configuration and
`git show <base>:<path>` — is held to the project's root.
"""
from __future__ import annotations

import contextlib
import io
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from mutation_scope_fixture import HEALTH, SLICE, Ran, ScopeCase, with_recipe
from stamp_fixture import git
from test_mutation_borders import FULL, calls, clean_environment, loaded
from test_mutation_scope_spring import POM, params
from test_mutation_targets import full_recipe

POM_TEXT = POM.format(targets=params("com.example.x.*"), excluded="")
SPRING = "java-spring:apps/spring"
TWO_GO = ("go:apps/service", "go:apps/billing")


class Recording:
    """Which services were asked for a scope, which for a sweep."""

    def __init__(self, module: Any) -> None:
        self.result = module.Result
        self.seen: list[tuple[str, list[str]]] = []
        self.swept: list[str] = []

    def run(self, backend: str, path: str, files: list[str]) -> Any:
        self.seen.append((path, list(files)))
        return self.result(0, list(files), [])

    def sweep(self, backend: str, path: str) -> Any:
        self.swept.append(path)
        return self.result(0, [], [])


class SubdirectoryTest(ScopeCase):
    def start(self, *services: str, base: dict[str, str] | None = None) -> None:
        """A repository `outer` whose project is `outer/sub`, `main` holding the project (its recipe the factory's for
        `services`) and `base`, and `slice/S1` cut from it."""
        words = services or ("go:apps/service",)
        outer = Path(tempfile.mkdtemp(dir=self.parent)) / "outer"
        self.repo = outer / "sub"
        shutil.copytree(self.template or "", self.repo, symlinks=True, ignore=shutil.ignore_patterns(".git"))
        makefile = self.repo / "Makefile"
        makefile.write_text(with_recipe(makefile.read_text(encoding="utf-8") + "\n", full_recipe(list(words)))[:-1],
                            encoding="utf-8")
        for name, text in (base or {}).items():
            self.write(name, text)
        git(outer, "init", "-q", "-b", "main")
        self.commit("base")
        git(outer, "checkout", "-q", "-b", SLICE)

    def fit_recipe(self, words: tuple[str, ...]) -> None:
        """`start` has fitted the recipe in the base already."""

    def edit(self, name: str, tail: str = "// probe\n") -> None:
        with open(self.repo / name, "a", encoding="utf-8") as handle:
            handle.write(tail)

    def recorded(self, *services: str, env: dict[str, str] | None = None) -> tuple[Ran, Recording]:
        words = services or ("go:apps/service",)
        module = loaded(self.repo / "scripts/mutation-scope.py")
        recording = Recording(module)
        saved, here = dict(os.environ), os.getcwd()
        os.environ.clear()
        os.environ.update(clean_environment() if env is None else env)
        os.chdir(self.repo)
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out):
                status = module.main(["--make", str(self.make), "--makefile", "Makefile", *words], recording)
        finally:
            os.chdir(here)
            os.environ.clear()
            os.environ.update(saved)
        return Ran(status, out.getvalue(), recording, calls(self.log)), recording  # type: ignore[arg-type]

    def test_a_tracked_and_an_untracked_change_are_both_scoped_to_the_service(self) -> None:
        self.start()
        self.edit(HEALTH)  # tracked, uncommitted: git reports it as `sub/apps/…`
        self.write("apps/service/config/untracked.go")  # untracked: git reports it from the project
        ran, recording = self.recorded()
        self.assertEqual(recording.seen, [("apps/service", ["config/untracked.go", "health/health.go"])], ran.out)
        self.assertEqual((ran.status, ran.make_calls), (0, []))

    def test_a_committed_change_is_scoped_to_the_service(self) -> None:
        self.start()
        self.edit(HEALTH)
        self.commit()
        ran, recording = self.recorded()
        self.assertEqual(recording.seen, [("apps/service", ["health/health.go"])], ran.out)
        self.assertNotIn("no mutant to run", ran.out)

    def test_a_changed_mutation_rule_sweeps_the_whole_run_and_a_change_beside_it_does_not(self) -> None:
        self.start()
        self.edit("Makefile", "\n# beside the rule\n")
        self.edit(HEALTH)
        ran, recording = self.recorded()
        self.assertEqual(recording.seen, [("apps/service", ["health/health.go"])], ran.out)
        text = (self.repo / "Makefile").read_text(encoding="utf-8")
        (self.repo / "Makefile").write_text(text.replace("mutation-full:", "mutation-full: # edited\n\t@true\n#", 1),
                                            encoding="utf-8")
        ran, recording = self.recorded()
        self.assertEqual(ran.first, "mutation: the sweep runs — `Makefile` changed", ran.out)
        self.assertEqual(ran.make_calls, [[*FULL]], ran.out)

    def test_a_changed_scope_script_sweeps_the_whole_run(self) -> None:
        self.start()
        self.edit("scripts/mutation-scope.py", "\n# probe\n")
        ran, recording = self.recorded()
        self.assertEqual(ran.first, "mutation: the sweep runs — `scripts/mutation-scope.py` changed", ran.out)
        self.assertEqual(ran.make_calls, [[*FULL]])

    def test_a_changed_backend_script_sweeps_every_go_service(self) -> None:
        self.start(*TWO_GO)
        self.edit("scripts/go-mutation.py", "\n# probe\n")
        self.edit(HEALTH)
        ran, recording = self.recorded(*TWO_GO)
        self.assertEqual(sorted(recording.swept), ["apps/billing", "apps/service"], ran.out)
        self.assertIn("mutation: sweep apps/service — `scripts/go-mutation.py` changed", ran.lines)

    def test_a_changed_gremlins_yaml_sweeps_that_service(self) -> None:
        self.start(*TWO_GO, base={"apps/billing/.gremlins.yaml": "unleash: {}\n"})
        self.edit("apps/billing/.gremlins.yaml", "integration: true\n")
        ran, recording = self.recorded(*TWO_GO)
        self.assertEqual(recording.swept, ["apps/billing"], ran.out)
        self.assertIn("mutation: sweep apps/billing — `apps/billing/.gremlins.yaml` changed", ran.lines)

    def test_a_pom_is_compared_with_the_base_as_parsed_structure(self) -> None:
        """Outside the `pitest-maven` block a change sweeps nothing; inside it, the service."""
        self.start(SPRING, base={"apps/spring/pom.xml": POM_TEXT})
        self.edit("apps/spring/pom.xml", "<!-- beside the block -->\n")
        ran, recording = self.recorded(SPRING)
        self.assertEqual(recording.swept, [], ran.out)
        self.write("apps/spring/pom.xml", POM_TEXT.replace("com.example.x.*", "com.example.y.*"))
        ran, recording = self.recorded(SPRING)
        self.assertEqual(recording.swept, ["apps/spring"], ran.out)
        self.assertIn("mutation: sweep apps/spring — `apps/spring/pom.xml` changed", ran.lines)

    def test_a_file_of_an_unpushed_trunk_commit_is_scoped_by_its_project_relative_path(self) -> None:
        """T035(c) in a subdirectory: git names the unpushed file `sub/apps/…`; the run says `health/health.go`."""
        self.start()
        outer = self.repo.parent
        bare = outer.parent / "origin.git"
        subprocess.run(["git", "init", "-q", "--bare", str(bare)], check=True, capture_output=True, timeout=60)
        git(outer, "remote", "add", "origin", str(bare))
        git(outer, "push", "-q", "origin", "main")
        git(outer, "fetch", "-q", "origin")
        git(outer, "checkout", "-q", "main")
        self.edit(HEALTH)
        self.commit("main, unpushed")
        git(outer, "checkout", "-q", "-B", SLICE)
        ran, recording = self.recorded()
        self.assertEqual(recording.seen, [("apps/service", ["health/health.go"])], ran.out)
        self.assertIn("has 1 commits `origin/main`", ran.first)
