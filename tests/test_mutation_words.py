"""S08 T009 (rule 9 · AC-S08-16, -17): the words — command text, notes, the skill, the docs and the fragment.

What a person reads about `make mutation` has to say what the target now does: it scopes itself on a slice branch,
`SINCE=<ref>` scopes it anywhere, `make mutation-full` is the sweep, CI and the trunk sweep, Phase 4 on `main` names the
commit before the merge, and a backend with no tool wired refuses until one is. Every sentence is held where it is
written, backend by backend.
"""
from __future__ import annotations

import re
import unittest

from slipwai.assets import ROOT
from slipwai.project.mutation import mutation_command, mutation_notes
from slipwai.services import App

BACKENDS = ("go", "java-spring", "java-quarkus", "typescript", "python")
PLACEHOLDERS = ("java-quarkus",)
SKILL = ROOT / "assets/toolkit/skills/mutation-testing/SKILL.md"
FRAGMENT = ROOT / "changelog.d/scoped-mutation.md"
PAGES = ("docs/backend-obligations.md", "docs/verification.md", "docs/requirements.md", "docs/maintaining.md")


def service(name: str, backend: str) -> App:
    language, _, framework = backend.partition("-")
    framework = {"spring": "spring-boot", "quarkus": "quarkus"}.get(framework, "")
    return App(name, f"apps/{name}", "service", language, framework or None, 3000)


def flat(text: str) -> str:
    """The text on one line with comment markers and line breaks gone, so a sentence is found wherever it wraps."""
    return " ".join(line.removeprefix("# ").removeprefix("#").strip() for line in text.splitlines())


class CommandTextTest(unittest.TestCase):
    def test_e1_every_backend_is_told_how_the_target_scopes_and_what_sweeps(self) -> None:
        for backends in [[b] for b in BACKENDS] + [list(BACKENDS)]:
            with self.subTest(backends=backends):
                text = flat(mutation_command(backends))
                for sentence in ("scopes itself on a `slice/<id>` branch", "`make mutation SINCE=<review-base>`",
                                 "on any checkout, CI included", "`make mutation-full` is the sweep",
                                 "CI and the trunk get the sweep", "make mutation SINCE=<the commit before the merge>",
                                 "Phase 4 on `main`"):
                    self.assertIn(sentence, text)
                self.assertNotIn("Without `SINCE` it mutates the whole module", text)
                self.assertEqual("refuses until a tool is wired" in text, bool(set(PLACEHOLDERS) & set(backends)))
        self.assertIn("gremlins.json", mutation_command(["go", "typescript"]))


# T024: the two whole-run causes T018 added, in the words every published place that lists what sweeps uses (D154).
CAUSES = ("`mutation-full` rule", "recipe that is not the one the factory wrote", "runs as written")


class CauseWordsTest(unittest.TestCase):
    def assertCauses(self, text: str) -> None:
        for words in CAUSES:
            self.assertIn(words, text)

    def test_t024_the_command_text_of_every_backend_names_both_causes(self) -> None:
        for backends in [[b] for b in BACKENDS] + [list(BACKENDS)]:
            with self.subTest(backends=backends):
                self.assertCauses(flat(mutation_command(backends)))

    def test_t024_the_go_and_spring_notes_name_both_causes(self) -> None:
        for backend in ("go", "java-spring"):
            with self.subTest(backend=backend):
                self.assertCauses(flat(mutation_notes([service("orders", backend)])))

    def test_t024_the_skill_names_both_causes(self) -> None:
        self.assertCauses(" ".join(SKILL.read_text(encoding="utf-8").split()))

    def test_t024_the_fragments_paragraph_and_catch_up_each_name_both_causes(self) -> None:
        text = FRAGMENT.read_text(encoding="utf-8")
        catch_up = next(block for block in text.split("\n\n") if block.startswith("**Catch-up.**"))
        body = text.split("\n\n")[1]
        for where, words in (("paragraph", body), ("catch-up", catch_up)):
            with self.subTest(where=where):
                self.assertCauses(" ".join(words.split()))


class NoteTest(unittest.TestCase):
    def test_e2_each_backends_note_says_the_same_in_its_own_words(self) -> None:
        for backend in ("go", "java-spring", "java-quarkus"):
            with self.subTest(backend=backend):
                note = flat(mutation_notes([service("orders", backend)]))
                self.assertIn("slice/<id>", note)
                self.assertIn("make mutation-full", note)
                self.assertNotIn("__APP__", note)
                self.assertNotIn("Without SINCE", note)
                self.assertIn("scopes itself on a `slice/<id>` branch", note)
                self.assertIn("make mutation SINCE=<", note)
                self.assertRegex(note, r"`make mutation-full` is the sweep|sweep, `make mutation-full`")
                self.assertRegex(note, r"CI(,| and) the trunk")
                self.assertIn("Phase 4 on `main` runs `make mutation SINCE=<the commit before the merge>`", note)
                if backend == "java-quarkus":
                    self.assertIn("once a tool is wired", note)

    def test_e2_python_has_mutmuts_note_and_is_not_told_the_target_refuses(self) -> None:
        """S42 T010 inverts S08's hold for Python only: mutmut is wired, so Python has a note (S08's other backends'
        notes are held byte for byte by `test_mutmut_generated`) and the command text no longer says it refuses."""
        self.assertIn("Wired up: mutmut", mutation_notes([service("orders", "python")]))
        self.assertNotIn("refuses until a tool is wired", mutation_command(["python"]))

    def test_e2_springs_failwhennomutations_paragraph_names_the_scoped_exception(self) -> None:
        note = flat(mutation_notes([service("ledger", "java-spring")]))
        self.assertIn("failWhenNoMutations", note)
        self.assertIn("scoped run is the exception", note)
        self.assertIn("no mutant to run", note)

    def test_e2_the_files_of_a_service_still_substitute(self) -> None:
        go = mutation_notes([service("orders", "go"), service("billing", "go")])
        self.assertIn("`apps/orders/.gremlins.yaml` and `apps/billing/.gremlins.yaml`", go)
        self.assertIn("`apps/ledger/pom.xml`", mutation_notes([service("ledger", "java-spring")]))


class SkillAndPagesTest(unittest.TestCase):
    def test_e3_the_skill_no_longer_demands_a_clean_tree(self) -> None:
        text = SKILL.read_text(encoding="utf-8")
        self.assertNotIn("Require a clean working tree before running it", text)
        self.assertNotIn("staged, unstaged, and untracked work is excluded", text)
        self.assertRegex(text, r"staged, unstaged and untracked production files are included and mutated")
        self.assertIn("nothing is committed or stashed to run it", text)

    def test_e3_the_skills_commands_collect_the_working_tree_and_untracked_files_too(self) -> None:
        """The sentence says the working tree is included; the commands the section runs have to do as it says."""
        text = SKILL.read_text(encoding="utf-8")
        self.assertNotIn("...HEAD", text, "a three-dot diff collects committed changes only")
        self.assertNotIn("git status --porcelain` is non-empty", text)
        lines = text.splitlines()
        diffs = [line for line in lines if "git diff" in line]
        listings = [line for line in lines
                    if "git ls-files" in line and "--others" in line and "--exclude-standard" in line]
        self.assertEqual((len(diffs), len(listings)), (2, 2), (diffs, listings))
        for line in diffs:
            self.assertIn("<merge-base>", line)

    def test_e3_hold_the_neighbouring_sentences_of_the_skill_are_untouched(self) -> None:
        text = SKILL.read_text(encoding="utf-8")
        for kept in ("- Use the actual review boundary: the detected default branch for a single PR, or the",
                     "- For a stacked slice, mutate the focused layer against its parent.",
                     "- In monorepos, start in the smallest affected package,",
                     "- Identify the package manager, test runner, affected package(s), and existing Stryker config."):
            self.assertIn(kept, text)

    def test_e4_the_pages_that_name_the_target_say_what_it_does(self) -> None:
        for page in PAGES:
            text = flat((ROOT / page).read_text(encoding="utf-8"))
            if "make mutation" not in text:
                continue
            with self.subTest(page=page):
                self.assertIn("mutation-full", text)
                if page != "docs/maintaining.md":
                    self.assertIn("slice branch", text)
        obligations = flat((ROOT / "docs/backend-obligations.md").read_text(encoding="utf-8"))
        self.assertIn("no gate runs `make mutation` or `make mutation-full`", obligations)

    def test_e4_the_gates_page_of_a_generated_project_is_unchanged(self) -> None:
        """HOLD: the pages a project is given say nothing of mutation, as before."""
        self.assertNotIn("mutation-full", (ROOT / "src/slipwai/project/docs.py").read_text(encoding="utf-8"))


class FragmentTest(unittest.TestCase):
    def test_e5_the_fragment_claims_minor_and_its_catch_up_stands_alone(self) -> None:
        text = FRAGMENT.read_text(encoding="utf-8")
        self.assertEqual(text.splitlines()[0], "MINOR")
        paragraphs = [block for block in text.split("\n\n") if block.startswith("**Catch-up.**")]
        self.assertEqual(len(paragraphs), 1)
        catch_up = " ".join(paragraphs[0].split())
        for sentence in ("`make mutation` on a `slice/<id>` branch", "`make mutation-full`", "`SINCE`", "CI", "trunk",
                         "TypeScript, Python and `java-quarkus`", "stub"):
            self.assertIn(sentence, catch_up)
        self.assertTrue(re.match(r"^\*\*[^*]+[.!?]\*\*", text.split("\n\n")[1]), "a bold lead sentence")

    def test_d149_the_fragment_says_python_is_refused_until_a_later_release_wires_mutmut(self) -> None:
        text = FRAGMENT.read_text(encoding="utf-8")
        catch_up = " ".join(next(block for block in text.split("\n\n") if block.startswith("**Catch-up.**")).split())
        for where, words in (("body", " ".join(text.split())), ("catch-up", catch_up)):
            with self.subTest(where=where):
                self.assertIn("until a later slipwai release wires mutmut", words)
                self.assertNotIn("S42", words)
                self.assertIn("whether or not mutmut is installed", words)
                self.assertIn("`make mutation-full` runs mutmut today where it is installed", words)
        self.assertNotIn("until you wire a tool", text)


if __name__ == "__main__":
    unittest.main()
