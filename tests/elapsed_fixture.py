"""A scratch project for S39's examples: a git repository holding `project.json`, the toolkit's scripts as the
working copy has them, `specs/f/story-split.md` with a `## Slice graph`, the register, records, and commits dated
with `GIT_COMMITTER_DATE`. Fakes are files: no mocking framework."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from slipwai.assets import ROOT

sys.dont_write_bytecode = True

SCRIPTS = ROOT / "assets/toolkit/scripts"
FEATURE = "f"


def clean(home: Path) -> dict[str, str]:
    env = {key: value for key, value in os.environ.items() if not key.startswith(("CLAUDE", "CODEX"))}
    env["HOME"] = str(home)
    return env


def stamp(day: int, clock: str = "09:00:00") -> str:
    """Seconds-precise UTC time on October `day`, 2026, as git and the records spell it."""
    return f"2026-10-{day:02d}T{clock}Z"


def git(repo: Path, *arguments: str, when: str | None = None) -> str:
    env = clean(repo / ".home")
    if when:
        env["GIT_COMMITTER_DATE"] = env["GIT_AUTHOR_DATE"] = when.replace("Z", "+0000")
    done = subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@local", *arguments], cwd=repo, env=env,
                          text=True, capture_output=True, check=True)
    return done.stdout.strip()


def project(base: Path, name: str = "p") -> Path:
    """A git repository with the scripts under `scripts/`; the scripts are not committed."""
    repo = base / name
    repo.mkdir(parents=True)
    (repo / ".home").mkdir()
    (repo / "project.json").write_text("{}\n", encoding="utf-8")
    shutil.copytree(SCRIPTS / "agents", repo / "scripts/agents", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copy2(SCRIPTS / "hand_backs.py", repo / "scripts/hand_backs.py")
    (repo / ".gitignore").write_text("scripts/\n.home/\n", encoding="utf-8")
    git(repo, "init", "-q", "-b", "main")
    git(repo, "add", ".gitignore", "project.json")
    git(repo, "commit", "-q", "-m", "start", when=stamp(1, "00:00:00"))
    return repo


def write(repo: Path, path: str, text: str) -> None:
    target = repo / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8", newline="\n")


def commit(repo: Path, when: str, message: str, *paths: str) -> str:
    git(repo, "add", "--", *paths)
    git(repo, "commit", "-q", "--allow-empty", "-m", message, when=when)
    return git(repo, "rev-parse", "--short", "HEAD")


def merge(repo: Path, when: str, ident: str) -> str:
    """A merge commit whose subject names `slice/<ident>`, on `main`, as `/drive`'s own merge does."""
    git(repo, "checkout", "-q", "-b", f"slice/{ident}")
    write(repo, f"work-{ident}.txt", ident)
    git(repo, "add", f"work-{ident}.txt")
    git(repo, "commit", "-q", "-m", f"work on {ident}", when=when)
    git(repo, "checkout", "-q", "main")
    git(repo, "merge", "-q", "--no-ff", "-m", f"Merge branch 'slice/{ident}' into main", f"slice/{ident}", when=when)
    return git(repo, "rev-parse", "--short", "HEAD")


def graph(rows: list[tuple[str, list[str]]]) -> str:
    lines = ["# Story split", "", "## Slice graph", "", "| Slice | depends_on | parallel_ok_with | Notes |",
             "|---|---|---|---|"]
    lines += [f"| `{ident}` | {', '.join(f'`{dep}`' for dep in deps) or '—'} | — | n |" for ident, deps in rows]
    return "\n".join(lines) + "\n"


def register(done: list[str]) -> str:
    rows = "".join(f"| `{ident}` | 2026-10-01 | x |\n" for ident in done)
    return "# Slices\n\n| Slice | Date | Demo |\n|---|---|---|\n" + rows


def entry(stage: str, started: str, ended: str, **signals: object) -> dict:
    seconds = int(_epoch(ended) - _epoch(started))
    return {"stage": stage, "started": started, "ended": ended, "seconds": seconds, "signals": signals,
            "usage": {"source": None, "reason": "fixture"}}


def costed(item: dict, tokens: int, session: str = "s1") -> dict:
    """The entry with a recorded `usage` of `tokens` (all input), as `end` leaves one read from a transcript."""
    item["usage"] = {"source": "claude", "session": session, "subagents": {},
                     "host": {"m": {"input": tokens, "output": 0, "cache_read": 0, "cache_creation": 0}}}
    item["ran"] = ["m"]
    return item


def _epoch(text: str) -> int:
    return int(datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC).timestamp())


def record(repo: Path, ident: str, *stages: dict, feature: str = FEATURE) -> str:
    path = f"specs/{feature}/slices/{ident}/benchmark.json"
    write(repo, path, json.dumps({"feature": feature, "slice": ident, "stages": list(stages)}, indent=1) + "\n")
    return path


def bench(repo: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["python3", "-B", str(repo / "scripts/agents/benchmark.py"), *arguments], cwd=repo,
                          env=clean(repo / ".home"), text=True, capture_output=True, timeout=120)


def summaries(repo: Path) -> dict[str, dict]:
    """`--json`, by slice."""
    done = bench(repo, "--json")
    assert done.returncode == 0, done.stderr
    return {item["slice"] or "(feature)": item for item in json.loads(done.stdout)}
