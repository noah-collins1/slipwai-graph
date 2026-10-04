"""Which job of a generated project's CI fetches history, and that it is only that one (AC-S24-1).

`check-slice-scope`, `check-migrations` and `check-flags` compare a change with the trunk, and a checkout of one
commit gives them nothing to compare with. The `verify` job fetches everything; every other job and every
other generated workflow is left exactly as it was.
"""
from __future__ import annotations

import re

from support import FactoryTestCase

from slipwai.catalog import CATALOG
from slipwai.scaffold import project_files
from slipwai.selection import resolve_selection
from slipwai.services import default_apps

VERIFY = ".github/workflows/verify.yml"
KEY = "fetch-depth"


def generated(backend: str, target: str) -> dict[str, str]:
    selection = resolve_selection({}, "event-modelling", backend, target)
    return project_files("fetched", "event-modelling", target, default_apps(backend, "none", selection))


def jobs_of(workflow: str) -> dict[str, str]:
    """Each job's text, by name, read off the two-space-indented keys under `jobs:`."""
    body = workflow.split("\njobs:\n", 1)[1]
    parts = re.split(r"^  ([\w-]+):\n", body, flags=re.MULTILINE)
    return {parts[i]: parts[i + 1] for i in range(1, len(parts), 2)}


class CiFetchGeneratedTest(FactoryTestCase):
    def test_the_verify_job_checks_out_with_full_history_and_says_which_checks_need_it(self) -> None:
        for backend in CATALOG["backends"]:
            for target in CATALOG["targets"]:
                with self.subTest(backend=backend, target=target):
                    workflow = generated(backend, target)[VERIFY]
                    verify = jobs_of(workflow)["verify"]
                    self.assertEqual(workflow.count(KEY), 1, "the key is on the verify job only")
                    step = "      - uses: actions/checkout@v6\n        with:\n          fetch-depth: 0\n"
                    self.assertIn(step, verify)
                    lines = verify.splitlines()
                    at = lines.index("      - uses: actions/checkout@v6")
                    self.assertNotIn("${{", "\n".join(lines[at : at + 3]), "written unconditionally")
                    comment = "\n".join(lines[max(0, at - 3) : at])
                    for check in ("check-slice-scope", "check-migrations", "check-flags"):
                        self.assertIn(check, comment)

    def test_hold_the_integration_jobs_keep_their_depth_one_fetch_and_carry_no_fetch_depth(self) -> None:
        """A hold: green before the change, and it has to stay green."""
        for backend in CATALOG["backends"]:
            with self.subTest(backend=backend):
                jobs = jobs_of(generated(backend, "none")[VERIFY])
                others = {name: text for name, text in jobs.items() if name != "verify"}
                self.assertTrue(others, "the sweep has an integration job to hold")
                for name, text in others.items():
                    self.assertNotIn(KEY, text, name)
                    self.assertIn("fetch -q --depth 1 origin", text, name)

    def test_hold_no_other_generated_workflow_fetches_history(self) -> None:
        """A hold: the event model's, the deploy, promotion and rollback workflows are what they were."""
        for backend in CATALOG["backends"]:
            for target in CATALOG["targets"]:
                with self.subTest(backend=backend, target=target):
                    files = generated(backend, target)
                    for path, text in files.items():
                        if path.startswith(".github/workflows/") and path != VERIFY:
                            self.assertNotIn(KEY, text, path)
