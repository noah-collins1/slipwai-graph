"""The pages agent's tests give the same result whatever `GITEA_*` the maintainer's shell exports (S33 T030, A3).

`scripts/gitea-pages.py` reads six `GITEA_*` names when it is loaded, and `test_gitea_pages.py` loads it in the suite's
own process. The root gate's stamp keys no such name, so a shell that turns the module red must not be able to."""
from __future__ import annotations

import os
import subprocess
import sys
import unittest

from slipwai.assets import ROOT

sys.dont_write_bytecode = True

ODD = {
    "GITEA_REPOS_DIR": "/nowhere/at/all",
    "GITEA_PAGES_ROOT": "/nowhere/served",
    "GITEA_PAGES_HOST": "0.0.0.0",
    "GITEA_PAGES_PORT": "x",
    "GITEA_PAGES_BRANCH": "elsewhere",
    "GITEA_PAGES_POLL_SECONDS": "soon",
}


class TestThePagesAgentSuiteIgnoresTheShell(unittest.TestCase):
    def test_an_odd_value_for_each_name_the_script_reads_changes_nothing(self) -> None:  # AC-S33-11 e1
        env = {k: v for k, v in os.environ.items() if not k.startswith("GITEA_")}
        env.update(ODD, PYTHONPATH=f"{ROOT / 'src'}{os.pathsep}{ROOT / 'tests'}", PYTHONDONTWRITEBYTECODE="1")
        result = subprocess.run([sys.executable, "-m", "unittest", "test_gitea_pages"], cwd=ROOT, env=env,
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
