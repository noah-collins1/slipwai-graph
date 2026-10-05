"""T036 + T037 (R4, R5, R6 · AC-S06-2, -5; D140, ADR 0005): the Makefile is held by its text.

`rules.json` carries `makefile`: the sha256 of the exact `Makefile` text the factory wrote, a CRLF read as LF and
nothing else changed. This module holds the digest (rule 1), the writers that carry it, and the script's check of
the text before any make call (rule 2): every text the factory did not write is the full gate, whatever make feature
it uses.
"""
from __future__ import annotations

import hashlib
import importlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

from scoped_fixture import FULL, MAKEFILE_WORDS, TAIL
from test_verify_scoped_record import RecordCase
from test_verify_scoped_sum import DRAWIO, RuleCase

from slipwai.assets import ROOT

sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "assets" / "toolkit" / "scripts"))

RULES = "scripts/verify_scoped/rules.json"
KEY = "makefile"


def expected(text: str) -> str:
    return hashlib.sha256(text.replace("\r\n", "\n").encode("utf-8")).hexdigest()


def nothing(_repo: Path) -> None:
    """A trunk commit of the project's own that changes no file."""


class DigestTest(RecordCase):
    def rules(self) -> Any:
        return importlib.import_module("verify_scoped.rules")

    def text(self, shape: str = "model-typescript-web") -> str:
        return (self.project(shape) / "Makefile").read_text(encoding="utf-8")

    def test_e1_the_digest_is_the_sha256_of_the_exact_text(self) -> None:
        text = self.text()
        self.assertEqual(self.rules().from_text(text).get(KEY), expected(text))

    def test_e1_a_crlf_copy_has_the_digest_of_its_lf_text(self) -> None:
        text = self.text()
        self.assertEqual(self.rules().from_text(text.replace("\n", "\r\n")).get(KEY), expected(text))

    def test_e1_nothing_else_is_normalised(self) -> None:
        text = self.text()
        held = self.rules().from_text(text).get(KEY)
        for what, changed in (("a trailing space", text.replace("verify-checks:", "verify-checks: ", 1)),
                              ("a blank line", text + "\n"),
                              ("a tab for a space in a recipe", text.replace("node scripts", "node\tscripts", 1)),
                              ("a comment", text + "# a comment\n")):
            with self.subTest(what):
                self.assertNotEqual(self.rules().from_text(changed).get(KEY), held)
                self.assertEqual(self.rules().from_text(changed).get(KEY), expected(changed))

    def test_e1_the_file_a_generated_project_holds_carries_its_makefiles_digest(self) -> None:
        for shape in ("model-typescript-web", "two-python"):
            with self.subTest(shape=shape):
                project = self.project(shape)
                held = json.loads((project / RULES).read_text(encoding="utf-8"))
                self.assertEqual(held.get(KEY), expected((project / "Makefile").read_text(encoding="utf-8")))

    def test_e1_the_digest_is_defined_once_in_rules_py(self) -> None:
        """The script and the factory both ask `rules.text_digest`."""
        self.assertEqual(self.rules().text_digest("a\r\nb\n"), expected("a\nb\n"))


class TextBorderTest(RuleCase):
    def text_first(self, run: Any) -> None:
        """The reason is the first line, `make verify` ran once, no unit line was said, and no database was read."""
        self.assertEqual(len(self.verify_calls()), 1)
        self.assertEqual(self.lines(run), [])
        reads = [line for line in self.log.read_text(encoding="utf-8").splitlines() if " -npq" in line]
        self.assertEqual(reads, [], "the project's Makefile was read by make before its text was compared")

    def test_e2_an_edited_makefile_is_the_full_gate_with_the_words_before_any_read(self) -> None:
        self.trunk(lambda text: text.replace(DRAWIO, DRAWIO + "\t@echo\n", 1))
        self.forbidden()
        run = self.scoped()
        self.assertEqual(self.scoped_lines(run)[0], FULL + MAKEFILE_WORDS, run.stdout)
        self.text_first(run)

    def test_e2_a_makefile_edit_in_whitespace_alone_is_the_full_gate(self) -> None:
        self.trunk(lambda text: text.replace("verify-checks:", "verify-checks: ", 1))
        self.forbidden()
        run = self.scoped()
        self.assertEqual(self.scoped_lines(run)[0], FULL + MAKEFILE_WORDS, run.stdout)
        self.text_first(run)

    def test_e2_a_makefile_with_a_crlf_for_every_lf_stays_scoped(self) -> None:
        """Only if make reads it as it reads the LF text, which the factory-text hold below proves for every shape."""
        def crlf(repo: Path) -> None:
            (repo / "Makefile").write_bytes((repo / "Makefile").read_bytes().replace(b"\n", b"\r\n"))

        self.trunk(change=crlf)
        self.forbidden()
        run = self.scoped()
        self.assertNotIn(MAKEFILE_WORDS, run.stdout)
        self.assertEqual(self.verify_calls(), [], run.stdout)

    def test_e2_a_rules_file_without_the_key_is_the_full_gate_with_the_makefile_words(self) -> None:
        def drop(repo: Path) -> None:
            held = json.loads((repo / RULES).read_text(encoding="utf-8"))
            held.pop(KEY)
            (repo / RULES).write_text(json.dumps(held), encoding="utf-8")

        self.trunk(change=drop)
        self.forbidden()
        run = self.scoped()
        self.assertEqual(self.scoped_lines(run)[0], FULL + MAKEFILE_WORDS, run.stdout)
        self.text_first(run)

    def test_e1_a_rules_file_that_is_gone_is_the_full_gate_with_the_makefile_words_before_any_read(self) -> None:
        self.trunk(change=lambda repo: (repo / RULES).unlink())
        self.forbidden()
        run = self.scoped()
        self.assertEqual(self.scoped_lines(run)[0], FULL + MAKEFILE_WORDS, run.stdout)
        self.text_first(run)

    def test_e1_a_rules_file_that_is_not_json_or_not_an_object_is_the_full_gate(self) -> None:
        for what, content in (("not JSON", "{"), ("a list", "[]"), ("a string", '"x"')):
            with self.subTest(what):
                def write(repo: Path, text: str = content) -> None:
                    (repo / RULES).write_text(text, encoding="utf-8")

                self.trunk(change=write)
                self.forbidden()
                run = self.scoped()
                self.assertEqual(self.scoped_lines(run)[0], FULL + MAKEFILE_WORDS, run.stdout)
                self.text_first(run)

    def test_e2_a_makefile_the_script_cannot_read_is_the_full_gate(self) -> None:
        self.trunk(change=nothing)
        self.forbidden()
        run = subprocess.run(["python3", "-B", "scripts/verify-scoped.py", "run", "--make", "make", "--makefile",
                              "NoSuchMakefile"], cwd=self.repo, env=self.environment(), text=True,
                             capture_output=True, timeout=120)
        self.assertEqual(self.scoped_lines(run)[0], FULL + MAKEFILE_WORDS, run.stdout)

    def other_makefile(self, name: str) -> None:
        def write(repo: Path) -> None:
            (repo / name).write_text("include Makefile\n", encoding="utf-8")

        self.trunk(change=write)
        self.forbidden()

    def test_e2_a_gnumakefile_is_the_full_gate_and_make_reads_it_first(self) -> None:
        self.other_makefile("GNUmakefile")
        run = self.scoped()
        self.assertEqual(self.scoped_lines(run)[0], FULL + OTHER.format("GNUmakefile"), run.stdout)
        self.text_first(run)

    def test_e2_a_lowercase_makefile_is_the_full_gate(self) -> None:
        self.other_makefile("makefile")
        run = self.scoped()
        self.assertEqual(self.scoped_lines(run)[0], FULL + OTHER.format("makefile"), run.stdout)
        self.text_first(run)

    def only_in_case(self, name: str) -> None:
        self.other_makefile(name)
        run = self.scoped()
        self.assertEqual(self.scoped_lines(run)[0], FULL + OTHER.format(name), run.stdout)
        self.text_first(run)

    def test_e2_a_lowercase_gnumakefile_is_the_full_gate_naming_it_as_listed(self) -> None:
        self.only_in_case("gnumakefile")

    def test_e2_an_uppercase_makefile_is_the_full_gate_naming_it_as_listed(self) -> None:
        self.only_in_case("MAKEFILE")

    def test_e2_a_mixed_case_gnumakefile_is_the_full_gate_naming_it_as_listed(self) -> None:
        self.only_in_case("GNUMakefile")

    def test_e2_makefiles_in_the_environment_is_the_full_gate(self) -> None:
        self.trunk(change=nothing)
        self.forbidden()
        run = self.scoped(env={"MAKEFILES": "/nonexistent/extra.mk"})
        self.assertEqual(self.scoped_lines(run)[0], FULL + ENVIRONMENT, run.stdout)
        self.text_first(run)

    def test_e2_an_empty_makefiles_is_not_a_cause(self) -> None:
        self.trunk(change=nothing)
        self.forbidden()
        run = self.scoped(env={"MAKEFILES": ""})
        self.assertNotIn(ENVIRONMENT, run.stdout)

    def test_e2_only_the_first_cause_is_printed(self) -> None:
        self.trunk(lambda text: text + "\n# edited\n")
        self.forbidden()
        run = self.scoped(env={"MAKEFILES": "/nonexistent/extra.mk"})
        self.assertEqual(self.scoped_lines(run)[0], FULL + ENVIRONMENT, run.stdout)
        self.assertEqual(len([line for line in self.scoped_lines(run) if "full gate runs" in line]), 1)


class EntryListTest(unittest.TestCase):
    """The root's entry list is read exactly, so a case-insensitive filesystem cannot pass `makefile` as `Makefile`."""

    def test_e2_the_list_is_what_the_directory_names_not_what_a_lookup_finds(self) -> None:
        rules = importlib.import_module("verify_scoped.rules")
        folder = Path(tempfile.mkdtemp(prefix="scoped-entries-"))
        self.addCleanup(shutil.rmtree, folder, ignore_errors=True)
        text = "verify:\n\t@true\n"
        (folder / "Makefile").write_text(text, encoding="utf-8")
        (folder / "rules.json").write_text(json.dumps({KEY: expected(text)}), encoding="utf-8")
        args = (str(folder / "Makefile"), str(folder / "rules.json"))
        self.assertIsNone(rules.text_problem(*args, {}))
        (folder / "makefile").write_text("include Makefile\n", encoding="utf-8")
        if sorted(entry.name for entry in folder.iterdir() if entry.name.lower() == "makefile") == ["Makefile"]:
            return  # a filesystem that cannot hold both names lists one of them
        self.assertIn("`makefile`", rules.text_problem(*args, {}) or "")


OTHER = "make reads `{}`, which the factory did not write; " + TAIL
ENVIRONMENT = "`MAKEFILES` in the environment adds makefiles the factory did not write; " + TAIL
