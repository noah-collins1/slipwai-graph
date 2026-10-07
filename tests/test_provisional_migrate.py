"""R13 (AC-S27-17; D196): a project made before provisional decisions gets the verb from `migrate`, its
`.specify/cruise.json` is left as it was, its gate still passes, and the fragment says what to do by hand."""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

from reversibility_fixture import entry
from support import FactoryTestCase
from test_reversibility_migrate import catch_up_paragraphs, commit, make, migrated, squashed

from slipwai.assets import ROOT

sys.dont_write_bytecode = True

BEFORE = "5f4fc00"  # the factory as it was before the slice: no provisional verb, the two-value `decide`
FRAGMENT = ROOT / "changelog.d/provisional-decisions.md"
CONFIG = ".specify/cruise.json"
VALUES = ("provisional-shadow", "provisional-advisory", "provisional")


def made_before(directory: str) -> Path:
    """A project the factory at `BEFORE` made, with a decisions log written then, committed."""
    old = Path(directory) / "factory-before"
    old.mkdir()
    archive = subprocess.run(["git", "archive", BEFORE], cwd=ROOT, capture_output=True, check=True, timeout=120).stdout
    subprocess.run(["tar", "-x", "-C", str(old)], input=archive, check=True, timeout=120)
    subprocess.run([str(old / "slipwai"), "generate", "product", "--profile", "event-modelling", "--backend",
                    "typescript", "--frontend", "none", "--output", directory, "--skip-checks"],
                   check=True, capture_output=True, timeout=300)
    repo = Path(directory) / "product"
    assert not (repo / "scripts/provisional.py").exists(), "the factory as it was had no provisional verb"
    (repo / "specs/shop").mkdir(parents=True, exist_ok=True)
    (repo / "specs/shop/decisions.md").write_text("# Decisions\n\n" + entry(1) + "\n" + entry(2), encoding="utf-8")
    commit(repo, "a log written before provisional decisions")
    return repo


class AProjectMadeBeforeKeepsItsSettingsAfterMigrateTest(FactoryTestCase):
    def test_e1_migrate_brings_the_verb_leaves_the_settings_and_the_whole_gate_passes(self) -> None:
        """Passes once T002-T013 stand: kept as the guard, not a RED."""
        with tempfile.TemporaryDirectory() as directory:
            repo = made_before(directory)
            settings = (repo / CONFIG).read_bytes()
            before = make(repo, "check-decisions")
            self.assertEqual(before.returncode, 0, before.stdout + before.stderr)

            result = migrated(directory, repo)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue((repo / "scripts/provisional.py").is_file(), "the verb arrives with migrate")
            self.assertEqual((repo / CONFIG).read_bytes(), settings, "migrate adds no key and edits no value")
            notes = squashed((repo / ".slipwai/catch-up.md").read_text(encoding="utf-8"))
            for value in VALUES:
                self.assertIn(f"`{value}`", notes)
            for check in ("check-agents", "check-decisions"):
                done = make(repo, check)
                self.assertEqual(done.returncode, 0, check + done.stdout + done.stderr)
            self.assertEqual(make(repo, "check-decisions").stdout, before.stdout, "the old log passes unchanged")
            self.assertIn("provisional", (repo / ".specify/product-owner.md").read_text(encoding="utf-8"),
                          "a brief the project never edited takes the new sentences through the merge")

            gate = make(repo, "verify", "VERIFY_FORCE=1", timeout=400)

            self.assertEqual(gate.returncode, 0, gate.stdout[-3000:] + gate.stderr[-3000:])
            self.assertIn("verify: all gates passed", gate.stdout)


class TheFragmentIsMinorAndItsCatchUpStandsAloneTest(FactoryTestCase):
    def setUp(self) -> None:
        self.text = FRAGMENT.read_text(encoding="utf-8")
        paragraphs = catch_up_paragraphs(self.text)
        self.assertEqual(len(paragraphs), 1, "exactly one paragraph begins **Catch-up.**")
        self.note = squashed(paragraphs[0])

    def test_e2_the_level_is_minor_and_a_blank_line_follows(self) -> None:
        lines = self.text.splitlines()
        self.assertEqual(lines[0], "MINOR")
        self.assertEqual(lines[1], "")

    def test_e2_the_catch_up_names_the_values_the_default_the_rung_rule_and_the_hand_ratification(self) -> None:
        for words in ("`provisional-shadow`", "`provisional-advisory`", "`provisional`", "off by default",
                      "`.specify/cruise.json`", "one rung at a time", "`/cruise-settings`", "`scripts/provisional.py`",
                      "pass unchanged", "`Status`", "`ratified <date>`", "`reverted <date>`", "`Decision: D<n>`",
                      "will not say `done`", "`.specify/product-owner.md`"):
            self.assertIn(words, self.note)

    def test_e2_the_catch_up_stands_alone_and_marks_nothing_experimental(self) -> None:
        for reference in ("T0", "AC-S27", "D19", "D20", "S27", "S28", "above", "R13", "experimental"):
            self.assertNotIn(reference, self.note)
