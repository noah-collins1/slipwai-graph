"""The names and plain helpers the stamp tests share, apart from the project they generate.

Not a test module. The environment-variable lists, the stand-in tools, and the git and log readers: none of it
generates a project, loads a script or reaches into the repository, so a test that needs only these is declared
without borrowing `stamp_fixture`, whose `importlib` loads a generated project's script. `stamp_fixture` re-exports
every name here, so the tests that import them from it keep working.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import unittest
from pathlib import Path

# Reads and writes only paths a caller hands it; generates nothing and opens nothing of the repository.
TEST_SELECTION: dict[str, object] = {}

CI_MARKERS = ("CI", "GITHUB_ACTIONS", "GITLAB_CI")
# What a `make test` that runs these suites hands to every child: a gate run inside it is a gate run by a person.
MAKE_STATE = ("MAKEFLAGS", "MFLAGS", "MAKELEVEL", "MAKEOVERRIDES", "MAKEFILES")
GIT_STATE = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE")
CLOSING = "verify: all gates passed"
REUSE_PREFIX = "verify: "
BRANCH = "topic"
SERVICE = "apps/service"
# What `uv sync` leaves in an environment it made, as uv 0.12 writes it.
PYVENV_CFG = "home = /usr/bin\nversion_info = 3.14.4\nuv = 0.12.20\n"


_UV = """#!/bin/sh
printf 'uv\\t%s\\n' "$*" >> "$STANDIN_LOG"
if [ -n "$STANDIN_HOLD" ] && [ "$1" = run ] && [ ! -e "$STANDIN_HOLD.held" ]; then
  : > "$STANDIN_HOLD.held"; echo "uv: held (stand-in)"
  n=0; while [ ! -e "$STANDIN_HOLD" ] && [ "$n" -lt 1200 ]; do sleep 0.05; n=$((n + 1)); done
fi
if [ -n "$STANDIN_UV_FAIL" ] && [ "$1" = run ]; then echo "uv: a check failed (stand-in)" >&2; exit 1; fi
if [ -n "$STANDIN_UV_HANG" ] && [ "$1" = run ]; then echo "uv: waiting (stand-in)"; exec sleep 600; fi
if [ -n "$STANDIN_EDIT" ] && [ "$1" = run ]; then echo "edited by a check" >> "$STANDIN_EDIT"; fi
if [ -n "$STANDIN_STAGE" ] && [ "$1" = run ]; then git update-index --chmod=+x -- "$STANDIN_STAGE"; fi
case "$1" in
  --version)
    case "$STANDIN_UV_MODE" in
      fail) echo "uv: broken" >&2; exit 3;;
      silent) printf '\\n\\n'; exit 0;;
      hang) exec sleep 60;;
    esac
    [ -n "$STANDIN_UV_NOTICE" ] && printf '%b\\n' "$STANDIN_UV_NOTICE" >&2
    printf '%b\\n' "${STANDIN_UV_VERSION:-uv 0.12.20 (stand-in)}"
    exit 0;;
  sync)
    while [ $# -gt 0 ]; do
      if [ "$1" = --project ]; then dir=$2; fi
      shift
    done
    mkdir -p "$dir/.venv"
    cfg="$dir/.venv/pyvenv.cfg"
    [ -f "$cfg" ] || printf 'home = /usr/bin\\nversion_info = 3.14.4\\nuv = 0.12.20\\n' > "$cfg"
    ;;
esac
exit 0
"""
# `make` is run under the name it was found by, so that `$(MAKE)` is `make` and the version question the recipe hands
# the script comes back through the stand-in, as it does on a machine whose `make` is on `PATH`.
_PASS_THROUGH = """#!/bin/bash
printf '%s\\t%s\\n' "{name}" "$*" >> "$STANDIN_LOG"
exec -a {name} "{real}" "$@"
"""



def git(repo: Path, *args: str) -> str:
    done = subprocess.run(["git", *args], cwd=repo, check=True, text=True, capture_output=True)
    return done.stdout


def commit_all(repo: Path, message: str) -> None:
    git(repo, "add", "-A")
    git(repo, "-c", "maintenance.auto=false", "commit", "-q", "-m", message)


def write_stand_ins(directory: Path) -> None:
    """The stand-ins, executable, in `directory`; each appends `tool<TAB>arguments` to `$STANDIN_LOG`."""
    directory.mkdir(parents=True, exist_ok=True)
    scripts = {"uv": _UV}
    for name in ("make", "git", "python3"):
        real = shutil.which(name)
        if real is None:
            raise unittest.SkipTest(f"{name} is not on PATH")
        scripts[name] = _PASS_THROUGH.format(name=name, real=real)
    for name, text in scripts.items():
        path = directory / name
        path.write_text(text, encoding="utf-8")
        path.chmod(0o755)


def write_spaced_make(parent: Path) -> Path:
    """A `make` that logs the call and hands it to the real one, reached through a directory whose name holds a space,
    and run under its own full path, so that `$(MAKE)` is that path with the space in it. Returns the executable."""
    real = shutil.which("make")
    if real is None:
        raise unittest.SkipTest("make is not on PATH")
    directory = parent / "a directory with a space"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "make"
    path.write_text(_PASS_THROUGH.replace("exec -a {name}", 'exec -a "$0"').format(name="make", real=real),
                    encoding="utf-8")
    path.chmod(0o755)
    return path


def checks_started(log: Path) -> list[str]:
    """What the stand-ins saw that is a check starting: a sync, a linter, a type checker or a test runner through
    `uv`, or a `python3` that is neither a version question nor the stamp script. Read from the log only — never
    from what a run printed (e19)."""
    started = []
    for line in log.read_text(encoding="utf-8").splitlines() if log.exists() else []:
        tool, _, arguments = line.partition("\t")
        asked = arguments == "--version" or "verify-stamp.py" in arguments
        if tool in ("uv", "python3") and not asked:
            started.append(line)
    return started



def probe_path(entry: str, under: str = "") -> str:
    """A path an exempt entry or an ignore line matches, made concrete: a star becomes a name, a directory a file in
    it. `under` is a directory it is put in, for an entry that matches at any depth."""
    path = entry.lstrip("/").replace("**/", "x/").replace("*", "x")
    if path.endswith("/"):
        path += "probe.txt"
    return under + path


def exclude(repo: Path, *paths: str) -> None:
    """Make git ignore `paths` through `.git/info/exclude`, which no commit carries and `.gitignore` does not list."""
    with (repo / ".git" / "info" / "exclude").open("a", encoding="utf-8") as handle:
        handle.write("".join(f"/{path}\n" for path in paths))


INSTANT = re.compile(r"\b\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ\b")
