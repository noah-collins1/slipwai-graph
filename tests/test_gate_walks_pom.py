"""A `target` is build output only where `project.json` says so (S01-gate-walks, T030, D52; AC-S01-4, -5, -8, -26).

A slice owns every file inside its own service, an empty `pom.xml` among them, so a `pom.xml` beside a directory
called `target` cannot be what makes that directory build output. The record can: a deployable `project.json`
records as Java, `target` at its path, a `pom.xml` there. Every other `target` is read as the scripts at `ed91b20`
(before the slice) read it, and a deployable recorded at a name the gates prune is descended all the same.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from support import FactoryTestCase
from test_gate_walks import GATES, reported, run_gate

BAD_DOMAIN = "from ..adapters.store import save\n"
BAD_JAVA = "package x;\nimport jakarta.inject.Inject;\n"
DROP = "DROP TABLE events;\n"
IMPORTS, MIGRATIONS = "scripts/check-imports.py", "scripts/check-migrations.py"


def plant(base: Path, java: bool = False) -> None:
    """A context directory `base/target/` holding a domain file and a migration a gate must find fault with."""
    (base / "target/domain").mkdir(parents=True)
    (base / "target/migrations").mkdir(parents=True)
    (base / f"target/domain/evil.{'java' if java else 'py'}").write_text(BAD_JAVA if java else BAD_DOMAIN)
    (base / "target/migrations/202610031200_drop.sql").write_text(DROP)


class Project(FactoryTestCase):
    def record(self, repo: Path, change: object) -> None:
        manifest = json.loads((repo / "project.json").read_text())
        change(manifest["deployables"])  # type: ignore[operator]
        (repo / "project.json").write_text(json.dumps(manifest, indent=2) + "\n")

    def both_read(self, repo: Path, imports: str, migrations: str) -> None:
        """Both gates fail, `check-imports` naming `imports` and `check-migrations` naming `migrations`."""
        for script, name in ((IMPORTS, imports), (MIGRATIONS, migrations)):
            with self.subTest(script=script):
                result = run_gate(repo, script)
                self.assertEqual(result.returncode, 1, result.stdout)
                self.assertIn(name, result.stderr)


class PomBesideATargetTest(Project):
    def test_an_empty_pom_a_slice_commits_does_not_switch_the_gates_off(self) -> None:
        """A1: the adversary's reproduction, at depth and at the service's root, on a Python project."""
        for under in ("apps/service/src/shop", "apps/service"):
            with self.subTest(under=under), tempfile.TemporaryDirectory() as directory:
                repo = self.generate(directory, "pom", "event-modelling", "python")
                (repo / under).mkdir(parents=True, exist_ok=True)
                (repo / under / "pom.xml").write_text("")
                plant(repo / under)
                self.both_read(repo, f"{under}/target/domain/evil.py:1",
                               f"{under}/target/migrations/202610031200_drop.sql")

    def test_a_nested_modules_target_below_a_recorded_java_root_is_read(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "nested", "event-modelling", "java-quarkus")
            module = repo / "apps/service/modules/inner"
            module.mkdir(parents=True)
            (module / "pom.xml").write_text("")
            plant(module, java=True)
            self.both_read(repo, "modules/inner/target/domain/evil.java:2",
                           "modules/inner/target/migrations/202610031200_drop.sql")

    def test_a_target_beside_a_pom_under_packages_with_no_record_is_read(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = self.generate(directory, "pkg", "event-modelling", "python")
            (repo / "packages/lib").mkdir(parents=True)
            (repo / "packages/lib/pom.xml").write_text("")
            plant(repo / "packages/lib")
            self.both_read(repo, "packages/lib/target/domain/evil.py:1",
                           "packages/lib/target/migrations/202610031200_drop.sql")

    def test_a_record_with_a_path_or_language_that_is_not_a_string_prunes_nothing(self) -> None:
        for change in ({"path": 7}, {"language": ["java"]}, {"language": None}):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as directory:
                repo = self.generate(directory, "odd", "event-modelling", "java-quarkus")
                self.record(repo, lambda deployables, change=change: deployables["service"].update(change))
                plant(repo / "apps/service", java=True)
                result = run_gate(repo, MIGRATIONS)
                self.assertEqual(result.returncode, 1)
                self.assertIn("apps/service/target/migrations/202610031200_drop.sql", result.stderr)

    def test_no_record_prunes_no_target(self) -> None:
        """A missing `project.json`, one that is not valid JSON, one that is not an object: both gates read `target`,
        and answer as the scripts at `ed91b20` did (`check-imports` ends on its traceback, `check-migrations`
        never read the record)."""
        last = {None: "", "{": "json.decoder.JSONDecodeError", "[]": "AttributeError: 'list' object"}
        for text, error in last.items():
            with self.subTest(text=text), tempfile.TemporaryDirectory() as directory:
                repo = self.generate(directory, "none", "event-modelling", "java-quarkus")
                plant(repo / "apps/service", java=True)
                if text is None:
                    (repo / "project.json").unlink()
                else:
                    (repo / "project.json").write_text(text)
                migrations = run_gate(repo, MIGRATIONS)
                self.assertEqual(migrations.returncode, 1)
                self.assertIn("apps/service/target/migrations/202610031200_drop.sql", migrations.stderr)
                imports = run_gate(repo, IMPORTS)
                self.assertEqual(imports.returncode, 1)
                if text is None:
                    self.assertIn("apps/service/target/domain/evil.java:2", imports.stderr)
                else:
                    self.assertTrue(imports.stderr.strip().splitlines()[-1].startswith(error), imports.stderr)

    def test_hold_an_unreadable_record_does_not_make_check_migrations_fail_a_clean_tree(self) -> None:
        """A hold: it never read the record before the slice and must not trace back on it now."""
        for text in ("{", "[]", '"x"'):
            with self.subTest(text=text), tempfile.TemporaryDirectory() as directory:
                repo = self.generate(directory, "clean", "event-modelling", "python")
                (repo / "project.json").write_text(text)
                result = run_gate(repo, MIGRATIONS)
                self.assertEqual((result.returncode, result.stderr), (0, ""))


class RecordedDeployableTest(Project):
    def test_a_deployable_recorded_at_a_pruned_name_is_read_by_every_rule(self) -> None:
        """A4, AC-S01-26: at `apps/service/target` (a recorded Java root beside its `pom.xml`) and beneath `.venv`."""
        for path in ("apps/service/target/inner", "apps/.venv/svc", "apps/service/node_modules"):
            with self.subTest(path=path), tempfile.TemporaryDirectory() as directory:
                repo = self.generate(directory, "recorded", "event-modelling", "java-quarkus")
                self.record(repo, lambda deployables, path=path: deployables.update(
                    extra={"kind": "service", "path": path, "language": "java"}))
                base = repo / path
                (base / "domain").mkdir(parents=True)
                (base / "migrations").mkdir()
                (base / "domain/Evil.java").write_text(BAD_JAVA)
                (base / "migrations/202610031200_drop.sql").write_text(DROP)
                self.both_read(repo, f"{path}/domain/Evil.java:2", f"{path}/migrations/202610031200_drop.sql")

    def test_the_directory_on_the_way_to_one_is_descended_whatever_the_record_spells(self) -> None:
        for spelled in ("apps/.venv/svc/", "./apps/.venv/svc"):
            with self.subTest(spelled=spelled), tempfile.TemporaryDirectory() as directory:
                repo = self.generate(directory, "spelled", "event-modelling", "python")
                self.record(repo, lambda deployables, spelled=spelled: deployables.update(
                    extra={"kind": "service", "path": spelled, "language": "python"}))
                base = repo / "apps/.venv/svc"
                (base / "domain").mkdir(parents=True)
                (base / "domain/evil.py").write_text(BAD_DOMAIN)
                result = run_gate(repo, IMPORTS)
                self.assertEqual(result.returncode, 1)
                self.assertIn("apps/.venv/svc/domain/evil.py:1", result.stderr)


class RecordedJavaTargetHoldTest(Project):
    def test_hold_a_recorded_java_roots_target_beside_its_pom_is_not_descended(self) -> None:
        """AC-S01-4, holds: however the path is spelled, `generated` true or false; the count grows by one."""
        for spelled in ("apps/service", "apps/service/", "./apps/service"):
            for generated in (True, False):
                with self.subTest(spelled=spelled, generated=generated), tempfile.TemporaryDirectory() as directory:
                    repo = self.generate(directory, "held", "event-modelling", "java-quarkus")
                    before = {script: reported(run_gate(repo, script), line) for script, line in GATES.items()}
                    self.record(repo, lambda deployables, spelled=spelled, generated=generated: deployables[
                        "service"].update(path=spelled, generated=generated))
                    plant(repo / "apps/service", java=True)
                    for script, line in GATES.items():
                        self.assertEqual(reported(run_gate(repo, script), line), before[script] + 1)


class PrunedEntryStillAnEntryTest(Project):
    """T031, A2: a directory the walk does not descend is still an entry of its parent."""

    def test_a_contract_marker_naming_a_pruned_directory_is_answered_as_before_the_slice(self) -> None:
        """`.venv` and `.git` sort before the migration, so the marker was satisfied; `node_modules` and
        `__pycache__` sort after it, so it was *does not come before it*, never *is not a migration beside it*."""
        for name, expected in ((".venv", None), (".git", None),
                               ("node_modules", "does not come before it"), ("__pycache__", "does not come before it")):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                repo = self.generate(directory, "entry", "event-modelling", "python")
                migrations = repo / "apps/service/migrations"
                (migrations / name).mkdir(parents=True)
                (migrations / "202610031200_drop.sql").write_text(f"-- contract: {name}\n{DROP}")
                result = run_gate(repo, MIGRATIONS)
                if expected is None:
                    self.assertEqual((result.returncode, result.stderr), (0, ""))
                else:
                    self.assertEqual(result.returncode, 1)
                    self.assertIn(f"names `{name}`, which {expected}.", result.stderr)
