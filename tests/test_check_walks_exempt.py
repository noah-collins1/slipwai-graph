"""S07 T029 (the class of A2): a check the scoped gate may skip reads nothing the verify stamp leaves out of its key.

`make verify-scoped` skips a check when nothing it declares changed, and an ignored path the stamp's `EXEMPT` names
(`.terraform/`, `__pycache__/`, `node_modules/` …) changes nothing it compares. A check that walked into one answered
from a file the scoped gate cannot see: `tofu init` downloads a module into `infra/service/.terraform/modules/`, and
`check-deploy-role` read its IAM, failed under `make verify`, and was skipped by `make verify-scoped`. The walk hold of
every check is `test_agents_projection_exempt.WalksHeldTest`; this module holds the reproduction and the verdicts.
"""
from __future__ import annotations

import subprocess
import sys

from scoped_fixture import ShapeCase

sys.dont_write_bytecode = True

DRY: dict[str, str | None] = {"STANDIN_DRY": "1"}
DOWNLOADED = "infra/service/.terraform/modules/identity/main.tf"
# IAM the generated deploy role is granted nothing for: a failure wherever it is read.
UNKNOWN_IAM = 'resource "aws_iam_saml_provider" "corporate" {\n  name = "corporate"\n}\n'


class DownloadedModuleTest(ShapeCase):
    shape = "model-typescript-web-cloud"

    def deploy_role(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["python3", "-B", "scripts/check-deploy-role.py"], cwd=self.repo, text=True,
                              capture_output=True, timeout=60)

    def test_a_module_tofu_downloaded_is_neither_compared_by_the_scoped_gate_nor_read_by_the_check(self) -> None:
        self.assertEqual(self.deploy_role().returncode, 0, "the generated stack is within the deploy role's grants")
        self.edit(DOWNLOADED, UNKNOWN_IAM)
        ignored = subprocess.run(["git", "check-ignore", "-q", DOWNLOADED], cwd=self.repo, timeout=60)
        self.assertEqual(ignored.returncode, 0, "the generated .gitignore ignores what tofu downloads")
        _, skipped = self.decided(self.scoped(env=DRY))
        self.assertIn("check-deploy-role", skipped)
        checked = self.deploy_role()
        self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
        self.assertNotIn(".terraform", checked.stdout)

    def test_the_same_resource_in_the_stack_itself_still_fails_the_check(self) -> None:
        self.edit("infra/service/identity.tf", UNKNOWN_IAM)
        checked = self.deploy_role()
        self.assertEqual(checked.returncode, 1)
        self.assertIn("infra/service/identity.tf: aws_iam_saml_provider.corporate needs iam:CreateSAMLProvider",
                      checked.stdout)
