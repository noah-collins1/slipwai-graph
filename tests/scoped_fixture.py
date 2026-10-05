"""What the `test_verify_scoped_*` modules share: the stamp fixture's project on a slice branch, and readers over a run.

Not a test module. A project is the stamp fixture's (generated once per process, copied per test), with the stand-in
`uv`, `make`, `git` and `python3` first on `PATH` that log each call to `$STANDIN_LOG`, on `slice/S1` cut from the
`main` it began on. Evidence is the log and the files a run leaves, never a clock and never a line the run printed
about itself.
"""
from __future__ import annotations

import subprocess
import sys

from stamp_fixture import StampTestCase, git

sys.dont_write_bytecode = True

SLICE = "slice/S1"
LINE = "verify-scoped: "
FULL = LINE + "the full gate runs, as `make verify` — "


class ScopedCase(StampTestCase):
    """The stamp fixture's project, checked out on `slice/S1` with `main` behind it."""

    def setUp(self) -> None:
        super().setUp()
        git(self.repo, "checkout", "-q", "main")
        git(self.repo, "checkout", "-q", "-b", SLICE)

    def checkout(self, *args: str) -> None:
        git(self.repo, "checkout", "-q", *args)

    def scoped(
        self, env: dict[str, str | None] | None = None, args: list[str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        """`make verify-scoped` as a person types it, in the project."""
        return subprocess.run(
            ["make", "verify-scoped", *(args or [])], cwd=self.repo, env=self.environment(env), text=True,
            capture_output=True, timeout=180,
        )

    def scoped_lines(self, run: subprocess.CompletedProcess[str]) -> list[str]:
        """The lines `verify-scoped` said, in order."""
        return [line for line in run.stdout.splitlines() if line.startswith(LINE)]

    def verify_calls(self) -> list[str]:
        """The `make` calls the stand-in saw whose goal is `verify`: the full gate was asked for, however it ended."""
        calls = []
        for line in self.log.read_text(encoding="utf-8").splitlines() if self.log.exists() else []:
            tool, _, arguments = line.partition("\t")
            if tool == "make" and arguments.split()[-1:] == ["verify"]:
                calls.append(arguments)
        return calls
