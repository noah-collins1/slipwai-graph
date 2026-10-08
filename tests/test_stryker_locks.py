"""S41 T029 (rule 8 · AC-S41-11): every TypeScript lock a `generate` can reach agrees with its manifest by npm's rule.

`test_stryker_generated` reads the two `@stryker-mutator` entries of each lock; this module asks npm itself, which is
the only judge of "the lock and the manifest move together": `npm ci --dry-run --offline --ignore-scripts` in a freshly
generated project, exit 0. Ten combinations are reachable, one project each: the service's own lock (`fastify`,
`postgres` and both, or neither) and the workspace lock beside a react-vite app, which also names `users-keycloak`.
Two workspace locks, `typescript-backend-users-keycloak.json` and `typescript-backend-postgres-users-keycloak.json`, are
unreachable: `users` requires a transport, and the only transport a TypeScript service has is `fastify`, so no
`generate` selects them. Both predate S41 and are not this module's to hold.

Nothing here reaches the network, and no cache is needed: a dry run builds the tree from the lock and fetches no
tarball, so `--offline` with an empty `npm_config_cache` still exits 0 (tried by hand on this machine). The module
declares no `TEST_SELECTION`, as the other modules that generate projects declare none: its helpers are undeclared,
so a declaration would be void and `test_select_tests_declarations` would say so.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from stamp_fixture import CI_MARKERS, GIT_STATE, MAKE_STATE
from support import FactoryTestCase

sys.dont_write_bytecode = True
NPM = ["npm", "ci", "--dry-run", "--offline", "--ignore-scripts"]
COMBINATIONS = {
    "service": ("none", {"http": "none", "event_store": "memory"}),
    "service-fastify": ("none", {"http": "fastify", "event_store": "memory"}),
    "service-postgres": ("none", {"http": "none", "event_store": "postgres"}),
    "service-fastify-postgres": ("none", {"http": "fastify", "event_store": "postgres"}),
    "web": ("react-vite", {"http": "none", "event_store": "memory"}),
    "web-fastify": ("react-vite", {"http": "fastify", "event_store": "memory"}),
    "web-postgres": ("react-vite", {"http": "none", "event_store": "postgres"}),
    "web-fastify-postgres": ("react-vite", {"http": "fastify", "event_store": "postgres"}),
    "web-fastify-keycloak": ("react-vite", {"http": "fastify", "event_store": "memory", "users": "keycloak"}),
    "web-fastify-postgres-keycloak": ("react-vite", {"http": "fastify", "event_store": "postgres",
                                                     "users": "keycloak"}),
}


def environment() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if k not in CI_MARKERS + MAKE_STATE + GIT_STATE}


def dry_run(project: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(NPM, cwd=project, env=environment(), text=True, capture_output=True, check=False, timeout=180)


class LocksTest(FactoryTestCase):
    parent: Path

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.parent = Path(tempfile.mkdtemp(prefix="stryker-locks-"))
        cls.addClassCleanup(shutil.rmtree, cls.parent, ignore_errors=True)

    def setUp(self) -> None:
        if shutil.which("npm") is None:
            self.skipTest("npm is not on PATH: there is no judge of the lock to ask")

    def generated(self, name: str, project: str | None = None) -> Path:
        frontend, axes = COMBINATIONS[name]
        return self.generate(self.parent, project or name, "event-modelling", "typescript", frontend, **axes)

    def test_e1_npm_ci_accepts_the_lock_of_every_reachable_combination(self) -> None:
        for name in COMBINATIONS:
            with self.subTest(combination=name):
                result = dry_run(self.generated(name))
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_e2_teeth_npm_ci_refuses_a_lock_whose_manifest_moved(self) -> None:
        project = self.generated("service", "teeth")
        manifest = next(project.glob("apps/*/package.json"))
        document = json.loads(manifest.read_text(encoding="utf-8"))
        document["devDependencies"]["@stryker-mutator/core"] = "10.0.1"
        manifest.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
        result = dry_run(project)
        self.assertNotEqual(result.returncode, 0, "the dry run accepted a manifest its lock does not name")
