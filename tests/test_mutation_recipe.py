"""S08 T018 (rule 2 · D138 item 3, AC-S08-8): the recipe the project owns is the recipe that runs.

`mutation-full`'s recipe lines are the tool's invocation for every wired backend, so a change to them, or a recipe that
is not the one the factory wrote for the services the script was handed, makes the whole run the sweep through
`make mutation-full`. Real `git` in a generated Go project; the Makefile's `mutation-full` rule is rewritten to the
factory's recipe for the services under test (built from the factory's own per-backend table) and committed on `main`.
"""
from __future__ import annotations

import stat

import test_mutation_sweeps
from mutation_scope_fixture import SLICE, ScopeCase, with_recipe
from stamp_fixture import git
from test_mutation_borders import calls, clean_environment
from test_mutation_sweeps import SPRING, TWO_GO, Recording
from test_mutation_targets import full_recipe

NOT_FACTORY = ("mutation: the sweep runs — `mutation-full`'s recipe is not the one the factory wrote, "
               "so it runs as written")
SPRING_FILE = "apps/spring/src/main/java/com/example/x/A.java"
GO_FILE = "apps/service/health/more.go"
SHAPES = {"go two-service": (TWO_GO, GO_FILE), "spring": ((SPRING,), SPRING_FILE)}


class RecipeBase(ScopeCase):
    makefile_arg = "Makefile"

    def fit_recipe(self, words: tuple[str, ...]) -> None:
        """These examples set the recipe themselves, so the run does not fit it."""

    def run_recording(self, *services: str, env: dict[str, str] | None = None) -> tuple[int, list[str], Recording]:
        return test_mutation_sweeps.SweepsTest.run_recording(self, *services, env=env)  # type: ignore[arg-type]

    def on_main(self, words: tuple[str, ...], lines: list[str] | None = None) -> list[str]:
        """The base commit holds `mutation-full` as the factory writes it for `words` (or as `lines`); the slice is cut
        again from it. Returns the recipe lines the Makefile now has."""
        written = lines if lines is not None else full_recipe(list(words))
        git(self.repo, "checkout", "-q", "main")
        makefile = self.repo / "Makefile"
        makefile.write_text(with_recipe(makefile.read_text(encoding="utf-8"), written), encoding="utf-8")
        self.commit("base")
        git(self.repo, "checkout", "-q", "-B", SLICE)
        return written

    def edit_line(self, needle: str, new: str) -> None:
        makefile = self.repo / "Makefile"
        text = makefile.read_text(encoding="utf-8")
        self.assertIn(needle, text)
        makefile.write_text(text.replace(needle, new, 1), encoding="utf-8")

    def swept_whole(self, status: int, lines: list[str], recording: Recording) -> None:
        self.assertEqual((recording.scoped, recording.swept), ([], []), lines)
        self.assertEqual(len(calls(self.log)), 1, lines)
        self.assertEqual(calls(self.log)[0][3], "mutation-full")
        self.assertEqual(status, 0)


class RecipeTest(RecipeBase):
    def test_e1_an_edit_to_mutation_fulls_recipe_line_sweeps_the_whole_run_for_each_wired_backend(self) -> None:
        for name, (words, produced) in SHAPES.items():
            with self.subTest(backend=name):
                git(self.repo, "checkout", "-q", "-B", SLICE, "main")
                git(self.repo, "checkout", "-q", "--", ".")
                written = self.on_main(words)
                self.edit_line(written[0], "GOFLAGS=-tags=probe " + written[0])
                self.write(produced)
                status, lines, recording = self.run_recording(*words)
                self.assertTrue(lines[0].startswith("mutation: the sweep runs — "), lines)
                self.swept_whole(status, lines, recording)
                self.log.unlink()

    def test_e1_an_edit_to_mutation_fulls_target_line_sweeps_the_whole_run_naming_the_makefile(self) -> None:
        self.on_main(TWO_GO)
        self.edit_line("mutation-full: ## Run", "mutation-full: ## (changed) Run")
        self.write(GO_FILE)
        status, lines, recording = self.run_recording(*TWO_GO)
        self.assertEqual(lines[0], "mutation: the sweep runs — `Makefile` changed", lines)
        self.swept_whole(status, lines, recording)

    def test_e1_hold_a_change_elsewhere_in_the_makefile_still_scopes_for_each_wired_backend(self) -> None:
        for name, (words, produced) in SHAPES.items():
            with self.subTest(backend=name):
                git(self.repo, "checkout", "-q", "-B", SLICE, "main")
                git(self.repo, "checkout", "-q", "--", ".")
                self.on_main(words)
                makefile = self.repo / "Makefile"
                makefile.write_text(makefile.read_text(encoding="utf-8") + "\nelsewhere:\n\t@true\n", encoding="utf-8")
                self.write(produced)
                _, lines, recording = self.run_recording(*words)
                self.assertTrue(lines[0].startswith("mutation: scoped to 1 changed file(s)"), lines)
                self.assertEqual(recording.swept, [], lines)
                self.assertEqual(calls(self.log), [])

    def test_e3_a_recipe_the_trunk_already_changed_is_the_sweep_with_its_reason_first(self) -> None:
        for name, (words, produced) in SHAPES.items():
            for since in (False, True):
                with self.subTest(backend=name, since=since):
                    git(self.repo, "checkout", "-q", "-B", SLICE, "main")
                    git(self.repo, "checkout", "-q", "--", ".")
                    written = self.on_main(words)
                    self.edit_line(written[0], "A=1 " + written[0])
                    git(self.repo, "checkout", "-q", "main")
                    self.commit("the trunk edits the recipe")
                    git(self.repo, "checkout", "-q", "-B", SLICE)
                    self.write(produced)
                    if since:
                        self.commit("the change")
                    env = clean_environment(SINCE="HEAD~1") if since else None
                    status, lines, recording = self.run_recording(*words, env=env)
                    self.assertEqual(lines[0], NOT_FACTORY + (", with `SINCE=HEAD~1`" if since else ""), lines)
                    self.assertEqual(len([line for line in lines if line.startswith("mutation: ")]), 1, lines)
                    self.swept_whole(status, lines, recording)
                    self.log.unlink()
                    (self.repo / produced).unlink(missing_ok=True)

    def test_t025_a_prerequisite_the_trunk_added_to_the_target_line_is_not_the_factorys_recipe(self) -> None:
        origin = git(self.repo, "rev-parse", "main").strip()
        for name, (words, produced) in SHAPES.items():
            with self.subTest(backend=name):
                git(self.repo, "checkout", "-q", "-f", SLICE)
                git(self.repo, "branch", "-q", "-f", "main", origin)
                git(self.repo, "checkout", "-q", "-B", SLICE, "main")
                git(self.repo, "checkout", "-q", "--", ".")
                self.on_main(words)
                self.edit_line("mutation-full: ## Run", "mutation-full: tools ## Run")
                git(self.repo, "checkout", "-q", "main")
                self.commit("the trunk adds a prerequisite")
                git(self.repo, "checkout", "-q", "-B", SLICE)
                self.write(produced)
                status, lines, recording = self.run_recording(*words)
                self.assertEqual(lines[0], NOT_FACTORY, lines)
                self.swept_whole(status, lines, recording)
                self.log.unlink()
                (self.repo / produced).unlink(missing_ok=True)

    def test_e3_a_recipe_for_other_services_than_the_ones_handed_is_not_the_factorys(self) -> None:
        self.on_main(TWO_GO)
        self.write(GO_FILE)
        _, lines, recording = self.run_recording("go:apps/service")
        self.assertEqual(lines[0], NOT_FACTORY, lines)
        self.assertEqual(recording.scoped, [])

    def test_e4_hold_an_adopted_layout_never_reaches_the_recipe_check_whatever_its_recipe_holds(self) -> None:
        """Wrapped applications add lines to `mutation-full` and exist only in adopted layouts, which never scope."""
        self.on_main(TWO_GO, [*full_recipe(list(TWO_GO)), "echo wrapped application"])
        project = self.repo / "project.json"
        project.write_text(project.read_text(encoding="utf-8").rstrip().removesuffix("}")
                           + ', "layout": {"delivery": "delivery"}}', encoding="utf-8")
        self.write(GO_FILE)
        status, lines, recording = self.run_recording(*TWO_GO)
        self.assertEqual(lines, ["mutation: this layout has no mutation scope — the recorded command runs"])
        self.swept_whole(status, lines, recording)


class SinceTest(RecipeBase):
    """T023 (D154): a recipe the project owns runs as written, `SINCE` included; the factory's own causes clear it."""

    def seeing_since(self) -> None:
        """The fake make also logs the `SINCE` its environment carries, as a line `env SINCE=<value>`."""
        text = self.make.read_text(encoding="utf-8")
        self.make.write_text(text.replace("echo -- >>", f'echo "env SINCE=$SINCE" >> "{self.log}"; echo -- >>'),
                             encoding="utf-8")
        self.make.chmod(self.make.stat().st_mode | stat.S_IXUSR)

    def trunk_edits_recipe(self) -> None:
        written = self.on_main(TWO_GO)
        self.edit_line(written[0], "A=1 " + written[0])
        git(self.repo, "checkout", "-q", "main")
        self.commit("the trunk edits the recipe")
        git(self.repo, "checkout", "-q", "-B", SLICE)
        self.write(GO_FILE)
        self.commit("the change")

    def sources(self) -> dict[str, dict[str, str]]:
        return {"the environment": clean_environment(SINCE="HEAD~1"),
                "make's command line": clean_environment(SINCE="HEAD~1", MAKEFLAGS=" -- SINCE=HEAD~1")}

    def test_t023_a_recipe_the_factory_did_not_write_keeps_since_for_the_sub_make_from_either_source(self) -> None:
        self.seeing_since()
        self.trunk_edits_recipe()
        for source, env in self.sources().items():
            with self.subTest(source=source):
                status, lines, _ = self.run_recording(*TWO_GO, env=env)
                self.assertEqual(lines[0], NOT_FACTORY + ", with `SINCE=HEAD~1`", lines)
                made = calls(self.log)
                self.assertEqual(len(made), 1, made)
                self.assertEqual(made[0][:4], ["--no-print-directory", "-f", "Makefile", "mutation-full"])
                self.assertFalse([word for word in made[0] if word.startswith("SINCE=")], made)
                self.assertIn("env SINCE=HEAD~1", made[0])
                self.assertEqual(status, 0)
                self.log.unlink()

    def test_t023_hold_the_scope_script_changing_still_clears_since_under_the_same_ref(self) -> None:
        self.seeing_since()
        self.trunk_edits_recipe()
        script = self.repo / "scripts/mutation-scope.py"
        script.write_text(script.read_text(encoding="utf-8") + "\n#\n", encoding="utf-8")
        for source, env in self.sources().items():
            with self.subTest(source=source):
                _, lines, _ = self.run_recording(*TWO_GO, env=env)
                self.assertEqual(lines[0], "mutation: the sweep runs — `scripts/mutation-scope.py` changed", lines)
                made = calls(self.log)
                self.assertIn("SINCE=", made[0])
                self.log.unlink()


class MakefileTest(RecipeBase):
    """T041 (A5, B5, B6): the scoped run reads the Makefile make runs and sweeps where it cannot vouch for it."""

    def test_t041_the_mutation_rule_changing_sweeps_in_whatever_form_the_makefile_is_named(self) -> None:
        for form in ("Makefile", "./Makefile", "absolute", "sub/../Makefile"):
            with self.subTest(form=form):
                self.setUp()
                self.makefile_arg = str(self.repo / "Makefile") if form == "absolute" else form
                self.on_main(TWO_GO)
                self.edit_line("mutation: ## Run", "mutation: ## (changed) Run")
                self.write(GO_FILE)
                status, lines, recording = self.run_recording(*TWO_GO)
                self.assertEqual(lines[0], "mutation: the sweep runs — `Makefile` changed", lines)
                self.swept_whole(status, lines, recording)
                self.log.unlink()

    def test_t041_a_makefile_that_includes_another_is_a_sweep_with_its_own_first_line(self) -> None:
        for directive in ("include extra.mk", "-include extra.mk", "sinclude extra.mk", "  include extra.mk"):
            with self.subTest(directive=directive):
                self.setUp()
                self.on_main(TWO_GO)
                makefile = self.repo / "Makefile"
                makefile.write_text(makefile.read_text(encoding="utf-8") + f"\n{directive}\n", encoding="utf-8")
                self.commit("the trunk includes another makefile")
                self.write(GO_FILE)
                status, lines, recording = self.run_recording(*TWO_GO)
                self.assertEqual(lines[0], "mutation: the sweep runs — `Makefile` includes another makefile, "
                                 "which the factory cannot read, so it cannot vouch for what runs", lines)
                self.swept_whole(status, lines, recording)
                self.log.unlink()

    def test_t041_hold_a_word_include_in_a_comment_or_a_recipe_is_not_an_include(self) -> None:
        self.on_main(TWO_GO)
        makefile = self.repo / "Makefile"
        notes = "\n# include extra.mk\nnote:\n\t@echo include x\n"
        makefile.write_text(makefile.read_text(encoding="utf-8") + notes, encoding="utf-8")
        self.commit("comments")
        self.write(GO_FILE)
        _, lines, recording = self.run_recording(*TWO_GO)
        self.assertTrue(lines[0].startswith("mutation: scoped to 1 changed file(s)"), lines)
        self.assertEqual(recording.swept, [])

    def test_t041_makefiles_in_the_environment_is_a_sweep_that_runs_the_projects_own_makefile(self) -> None:
        self.on_main(TWO_GO)
        self.write(GO_FILE)
        for given in ("extra.mk", "Makefile"):  # make's `MAKEFILE_LIST` starts with the file `MAKEFILES` names
            with self.subTest(first=given):
                self.makefile_arg = given
                status, lines, recording = self.run_recording(*TWO_GO, env=clean_environment(MAKEFILES="extra.mk"))
                self.assertEqual(lines[0], "mutation: the sweep runs — `MAKEFILES` is set, so makefiles the factory "
                                 "cannot read run beside `Makefile`", lines)
                self.swept_whole(status, lines, recording)
                self.assertEqual(calls(self.log)[0][:3], ["--no-print-directory", "-f", "Makefile"])
                self.log.unlink()
