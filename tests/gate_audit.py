"""Run a gate script under an audit hook, and say what it opened and which directories it listed.

S01-gate-walks promises things about what a gate reads — `project.json` once, nothing inside `.venv` — that its
output cannot show. Python raises an audit event for every `open()` and every `os.scandir()`, so a wrapper passed
to `python3 -c` records them and then runs the script exactly as `python3 scripts/<gate>.py` would. Nothing is
replaced: the script runs unmodified, and the record is what the interpreter itself reported.
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

# Runs the script a caller names inside the project a caller made; opens nothing of the repository.
TEST_SELECTION: dict[str, object] = {}

WRAPPER = """
import json, os, runpy, sys
seen = []
def hook(event, arguments):
    if event in ("open", "os.scandir") and arguments and isinstance(arguments[0], (str, bytes, os.PathLike)):
        seen.append([event, os.fsdecode(arguments[0])])
sys.addaudithook(hook)
script, record = sys.argv[1], sys.argv[2]
sys.argv = [script]
try:
    runpy.run_path(script, run_name="__main__")
finally:
    with open(record, "w") as handle:
        json.dump(seen, handle)
"""


class Audited:
    """One run of a gate: its result, and every path it opened or listed, resolved against the project."""

    def __init__(self, repo: Path, script: str, env: dict[str, str] | None = None) -> None:
        record = repo.parent / f"audit-{Path(script).stem}.json"
        # `env`, where given, is the whole environment: a caller that cleared the CI markers must not get them back.
        self.result = subprocess.run(["python3", "-c", WRAPPER, script, str(record)], cwd=repo, text=True,
                                     capture_output=True, env=env)
        events = json.loads(record.read_text()) if record.is_file() else []
        record.unlink(missing_ok=True)
        root = repo.resolve()
        self.opened = [self.within(root, path) for event, path in events if event == "open"]
        self.listed = [self.within(root, path) for event, path in events if event == "os.scandir"]

    @staticmethod
    def within(root: Path, path: str) -> str:
        """The path as the project spells it, or the absolute path where it is outside the project."""
        absolute = Path(os.path.normpath(root / path))
        try:
            return absolute.relative_to(root).as_posix()
        except ValueError:
            return absolute.as_posix()
