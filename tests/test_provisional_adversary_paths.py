"""S27 Phase 4, T039 (A3-A6, A9, A10; D210, AC-S27-25): a protected path is refused however its writer spelled it.

Each case writes a provisional entry whose `Written to` names the path into a scratch project holding the three toolkit
scripts and every path the line names, and runs the gate as a `python3 -B` subprocess. `{repo}` in a line is the
project's own directory.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from provisional_fixture import EASY_LINE, NAMES, basis, entry, run
from reversibility_fixture import SCRIPTS, scratch

sys.dont_write_bytecode = True

PROVISIONAL = "provisional · ratify by 2026-10-14"
RATIFIED = "ratified 2026-10-08"


def provisional(written: str, status: str = PROVISIONAL) -> str:
    kind = status.split()[0]
    log = entry(1, status, revert="own" if kind == "provisional" else None, reversibility=EASY_LINE)
    return log.replace("- **Written to:** `README.md`", f"- **Written to:** {written}")


def gate(written: str, status: str = PROVISIONAL, origin: str | None = None, delivery: str | None = None,
         extra: str = "") -> subprocess.CompletedProcess[str]:
    """The gate over one entry writing to `written`; the files it names exist, so only the list can refuse it."""
    with tempfile.TemporaryDirectory() as directory:
        repo = basis(scratch(directory, "", origin=origin, names=NAMES, delivery=delivery,
                             listed=("scripts/check-decisions.py",))).resolve()
        log = provisional(written.replace("{repo}", repo.as_posix()), status) + extra
        (repo / "specs/f/decisions.md").write_text("# Decisions\n\n" + log, encoding="utf-8")
        for name in re.findall(r"`([^`]+)`", written.replace("{repo}", repo.as_posix())) or \
                [part.strip() for part in re.split(r"[,;]|\sand\s", written)]:
            target = Path(name) if name.startswith("/") else repo / name
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("x\n", encoding="utf-8")
        return run(repo, "check-decisions")


def findings(result: subprocess.CompletedProcess[str]) -> list[str]:
    return [row for row in result.stderr.splitlines() if row.startswith("  ")]


class PathTest(unittest.TestCase):
    def refused(self, written: str, *words: str, **keywords: str) -> None:
        result = gate(written, **keywords)
        self.assertEqual(1, result.returncode, f"{written}: {result.stdout}{result.stderr}")
        found = findings(result)
        self.assertEqual(1, len(found), found)
        for word in ("D1", "`Written to`", *words):
            self.assertIn(word, found[0])

    def passes(self, written: str, **keywords: str) -> None:
        result = gate(written, **keywords)
        self.assertEqual((0, ""), (result.returncode, result.stderr), f"{written}: {result.stdout}")


class MakeReadsOtherNamesTest(PathTest):
    def test_t039_a3_gnumakefile_and_makefile_are_refused_where_make_reads_them_ahead_of_makefile(self) -> None:
        for path in ("GNUmakefile", "makefile", "apps/svc/GNUmakefile", "apps/svc/makefile"):
            self.refused(f"`{path}`", path)

    def test_t039_a3b_either_case_of_a_listed_name_is_refused(self) -> None:
        for path in ("MAKEFILE", "gnumakefile", "Ruff.toml"):
            self.refused(f"`{path}`", path)


class SpellingTest(PathTest):
    def test_t039_a4_an_absolute_path_inside_the_project_is_refused_as_the_relative_one_is(self) -> None:
        self.refused("`{repo}/Makefile`", "Makefile")
        self.refused("`{repo}/.github/workflows/verify.yml`", ".github/workflows/verify.yml")

    def test_t039_a4b_dot_dot_dot_and_doubled_slashes_are_resolved_before_the_list_is_read(self) -> None:
        for spelled, resolved in (("specs/../Makefile", "Makefile"), ("./././Makefile", "Makefile"),
                                  ("scripts//x.py", "scripts/x.py"),
                                  (".github//workflows/verify.yml", ".github/workflows"),
                                  ("docs/../.github/workflows/verify.yml", ".github/workflows")):
            self.refused(f"`{spelled}`", resolved)

    def test_t039_a5_a_bare_protected_path_beside_a_backticked_one_is_refused(self) -> None:
        for line in ("`README.md`, Makefile", "`README.md` and Makefile", "`README.md`; Makefile",
                     "`README.md`, scripts/other.py"):
            self.refused(line, line.split(", ")[-1].split("; ")[-1].split(" and ")[-1])

    def test_t039_a5b_a_protected_path_beside_an_ordinary_bare_one_is_refused_too(self) -> None:
        self.refused("README.md, Makefile", "Makefile")

    def test_t039_a5c_ordinary_paths_pass_however_they_are_listed(self) -> None:
        for line in ("`README.md`, docs/guide.md", "`README.md` and docs/guide.md", "`README.md`; docs/guide.md"):
            self.passes(line)


class SecondLineTest(PathTest):
    def test_t039_a6_a_second_written_to_on_a_provisional_entry_is_refused(self) -> None:
        log = provisional("`README.md`").replace("- **Status:**", "- **Written to:** `.github/workflows/verify.yml`\n"
                                                 "- **Status:**")
        with tempfile.TemporaryDirectory() as directory:
            repo = basis(scratch(directory, log, names=NAMES, listed=("scripts/check-decisions.py",)))
            result = run(repo, "check-decisions")
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertTrue(any("D1" in row and "`Written to` is on more than one line" in row for row in findings(result)),
                        result.stderr)

    def test_t039_a6b_a_ratified_entry_too_and_a_standing_one_beside_it_is_not(self) -> None:
        second = "- **Written to:** `README.md`\n- **Status:**"
        ratified = provisional("`README.md`", RATIFIED).replace("- **Status:**", second)
        standing = entry(2, "standing").replace("- **Status:**", second)
        with tempfile.TemporaryDirectory() as directory:
            repo = basis(scratch(directory, ratified + standing, names=NAMES,
                                 listed=("scripts/check-decisions.py",)))
            result = run(repo, "check-decisions")
        rows = findings(result)
        self.assertEqual(1, len(rows), result.stderr)
        self.assertIn("D1", rows[0])


class TheListGrowsTest(PathTest):
    def test_t039_a9_an_adopted_layouts_delivery_directory_is_protected(self) -> None:
        for path in ("method/scripts/verify_scoped/local-rules.json", "method/scripts/check-decisions.py",
                     "method/Makefile", "method/.written"):
            self.refused(f"`{path}`", path, origin="adopted", delivery="method")

    def test_t039_a9b_the_same_paths_are_ordinary_where_the_project_is_not_adopted(self) -> None:
        self.passes("`method/scripts/check-decisions.py`")

    def test_t039_a9c_an_adopted_layout_with_the_delivery_at_the_root_adds_only_its_record(self) -> None:
        self.refused("`.written`", ".written", origin="adopted", delivery=".")

    def test_t039_a10_hook_files_flag_files_and_tool_configurations_a_gate_reads_are_protected(self) -> None:
        for path in (".cursor/hooks.json", ".gemini/settings.json", "infra/prod-flags.tfvars", "flags.tfvars",
                     ".ruff.toml", "ruff.toml", "apps/svc/conftest.py", "conftest.py", ".mvn/wrapper/x.properties",
                     "apps/svc/.mvn/jvm.config", ".mvn"):
            self.refused(f"`{path}`", path)

    def test_t039_a10b_every_hook_file_the_registry_projects_is_protected(self) -> None:
        registry = json.loads((SCRIPTS / "agents/registry.json").read_text(encoding="utf-8"))
        wheres = {(row.get("hooks") or {}).get("projection", {}).get("where") for row in registry["harnesses"]
                  if isinstance((row.get("hooks") or {}).get("projection"), dict)}
        self.assertTrue(wheres)
        for where in sorted(wheres):
            self.refused(f"`{where}`", where)

    def test_t039_a10c_neighbours_of_the_new_names_stay_ordinary(self) -> None:
        for path in ("docs/flags.md", "apps/svc/conftest.pyi", "apps/svc/mvn/notes.txt", "infra/prod.tfvars"):
            self.passes(f"`{path}`")


if __name__ == "__main__":
    unittest.main()
