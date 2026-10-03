"""What the two walking gates answer on a violating tree, pinned before S01-gate-walks changes how they walk.

`check-imports` and `check-migrations` are about to list each directory once and to stop descending `.venv`,
`node_modules` and their like. Nothing about what they find in the project's own code may move with that: the
same findings, in the same order, the same bytes on stderr, nothing on stdout, exit 1. These are holds — green
before the change and after it.
"""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from support import FactoryTestCase

IMPORT_FINDINGS = (
    "apps/service/src/application/bad_usecase.py:1: application imports an outer layer: "
    "from ..composition.container import container\n"
    "apps/service/src/domain/bad_policy.py:1: domain imports an outer layer: from ..adapters.store import save\n"
    "apps/web/src/bad.ts:1: frontend imports backend implementation: "
    "import { x } from '../../service/src/domain/thing';\n"
)
MIGRATION_FINDINGS = (
    "check-migrations: a schema change does not follow expand/contract\n"
    "\n"
    "  apps/service/migrations/900_drop.sql: drops a column. A contracting migration names the additive one it "
    "completes — `contract: <migration>` in a comment line — and ships in a later change than it.\n"
    "  apps/service/migrations/902_drop.sql: drops a table, and names `901_missing`, which is not a migration "
    "beside it.\n"
    "\n"
)


def plant_import_violations(repo: Path) -> None:
    """One finding for each of the layer rules and the frontend rule, in the project's own code."""
    for layer in ("domain", "application"):
        (repo / "apps/service/src" / layer).mkdir(parents=True, exist_ok=True)
    (repo / "apps/service/src/domain/bad_policy.py").write_text("from ..adapters.store import save\nimport os\n")
    (repo / "apps/service/src/application/bad_usecase.py").write_text(
        "from ..composition.container import container\n")
    (repo / "apps/web/src/bad.ts").write_text(
        "import { x } from '../../service/src/domain/thing';\nexport const y = x;\n")


def plant_migration_violations(repo: Path) -> None:
    """An unmarked contraction, and a marked one naming a migration that is not there."""
    migrations = repo / "apps/service/migrations"
    (migrations / "900_drop.sql").write_text("ALTER TABLE events DROP COLUMN payload;\n")
    (migrations / "902_drop.sql").write_text("-- contract: 901_missing\nDROP TABLE events;\n")


class GateWalksPinnedTest(FactoryTestCase):
    def skeleton(self, directory: str) -> Path:
        return self.generate(directory, "pinned", "event-modelling", "python", frontend="react-vite")

    def test_the_import_gate_reports_the_same_findings_in_the_same_bytes(self) -> None:
        """Hold (R4e1): the findings, their order, stderr to the byte, an empty stdout, exit 1."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.skeleton(directory)
            plant_import_violations(repo)
            result = subprocess.run(["python3", "scripts/check-imports.py"], cwd=repo, text=True,
                                    capture_output=True)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(result.stdout, "")
            self.assertEqual(result.stderr, IMPORT_FINDINGS)

    def test_the_migration_gate_reports_the_same_findings_in_the_same_bytes(self) -> None:
        """Hold (R4e2): the same for `check-migrations`."""
        with tempfile.TemporaryDirectory() as directory:
            repo = self.skeleton(directory)
            plant_migration_violations(repo)
            result = subprocess.run(["python3", "scripts/check-migrations.py"], cwd=repo, text=True,
                                    capture_output=True)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(result.stdout, "")
            self.assertEqual(result.stderr, MIGRATION_FINDINGS)
