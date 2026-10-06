"""The fixture project and the stand-in tools every `test_verify_stamp_*` module runs the real gate against.

Not a test module. The project is one the factory generates — standard profile, Python backend, no transport, no
frontend — on a branch that is not the trunk, copied per test from one generation. The stand-ins are executables
written here and put first on `PATH`: `uv`, which is the one tool whose work the gate cannot do offline, and `make`,
`git` and `python3`, which log the call and hand it to the real one. Every check script of the project is the real
one, so the full gate passes in about half a second with no network, and what ran is read from the stand-ins' log,
never from what the run printed (AC-S03-19).
"""
from __future__ import annotations

import atexit
import contextlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType

from slipwai.assets import ROOT
from slipwai.project.gate import FAILED

# Undeclared: `template()` generates its one project through the `./slipwai` launcher (every configuration to the
# selector) and `importlib` loads a generated project's script, which the scan reads as a reach into the repository
# (D164 rules 3 and 4). A module that imports it always runs.

sys.dont_write_bytecode = True

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

_template: Path | None = None


def template() -> Path:
    """The fixture project, generated once per process and never run in: tests copy it."""
    global _template
    if _template is None:
        parent = Path(tempfile.mkdtemp(prefix="stamp-fixture-"))
        atexit.register(shutil.rmtree, parent, ignore_errors=True)
        subprocess.run(
            [str(ROOT / "slipwai"), "generate", "fixture", "--profile", "standard", "--backend", "python",
             "--frontend", "none", "--http", "none", "--output", str(parent), "--skip-checks"],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        repo = parent / "fixture"
        git(repo, "checkout", "-q", "-b", BRANCH)
        for key, value in (("user.name", "t"), ("user.email", "t@local"), ("commit.gpgsign", "false")):
            git(repo, "config", key, value)
        (repo / SERVICE / ".venv").mkdir(parents=True, exist_ok=True)
        (repo / SERVICE / ".venv" / "pyvenv.cfg").write_text(PYVENV_CFG, encoding="utf-8")
        _template = repo
    return _template


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


class StampTestCase(unittest.TestCase):
    """One fixture project per test, a stand-in directory first on `PATH`, and `run_gate`."""

    repo: Path
    log: Path

    def setUp(self) -> None:
        sys.dont_write_bytecode = True
        scratch = Path(tempfile.mkdtemp(prefix="stamp-test-"))
        self.addCleanup(shutil.rmtree, scratch, ignore_errors=True)
        self.repo = scratch / "project"
        shutil.copytree(template(), self.repo, symlinks=True)
        self.bin = scratch / "bin"
        write_stand_ins(self.bin)
        self.log = scratch / "standin.log"

    def environment(self, extra: dict[str, str | None] | None = None) -> dict[str, str]:
        """The environment of a run: the stand-ins first on `PATH`, the three CI markers removed unless the
        example sets one, and `extra` on top (a `None` removes a name)."""
        env = {key: value for key, value in os.environ.items() if key not in CI_MARKERS + MAKE_STATE + GIT_STATE}
        env["PATH"] = f"{self.bin}{os.pathsep}{env.get('PATH', '')}"
        env["STANDIN_LOG"] = str(self.log)
        for key, value in (extra or {}).items():
            if value is None:
                env.pop(key, None)
            else:
                env[key] = value
        return env

    def run_gate(
        self, env: dict[str, str | None] | None = None, args: list[str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        """`make verify` as a developer types it, in the project, with the log kept between runs."""
        return subprocess.run(
            ["make", "verify", *(args or [])], cwd=self.repo, env=self.environment(env), text=True,
            capture_output=True, timeout=180,
        )

    def forget_log(self) -> None:
        self.log.write_text("", encoding="utf-8")

    def checks(self) -> list[str]:
        return checks_started(self.log)

    def stamp_path(self) -> Path | None:
        """The project's stamp, under the git directory; None where there is none."""
        found = sorted((self.repo / ".git" / "slipwai").glob("verify-stamp-*.json"))
        return found[0] if found else None

    def stamp(self) -> dict[str, object]:
        path = self.stamp_path()
        self.assertIsNotNone(path, "no stamp under .git/slipwai")
        assert path is not None
        return json.loads(path.read_text(encoding="utf-8"))

    def plant_stamp(self) -> bytes:
        """A stamp that is valid for the tree, the branch and the machine as they stand now, written as a pass would
        write it, and its bytes: what a run that may read it would reuse, so a run that does not is seen not to."""
        module = load_script(self.repo)
        makefile = (self.repo / "Makefile").read_text(encoding="utf-8")
        arguments = re.search(r"^VERIFY_STAMP := (.*)$", makefile, re.M)
        assert arguments is not None
        options = module.Options(["--make", "make", *arguments.group(1).split()])
        was, here, env = dict(os.environ), Path.cwd(), self.environment()
        os.environ.clear()
        os.environ.update(env)
        os.chdir(self.repo)
        try:
            stamp = dict(module.build_key(module.machine_tools(options)), passed="2026-01-01T00:00:00Z", result="pass")
            module.write_file(module.stamp_path(), json.dumps(stamp, indent=2, sort_keys=True) + "\n")
            return Path(module.stamp_path()).read_bytes()
        finally:
            os.chdir(here)
            os.environ.clear()
            os.environ.update(was)

    def reuse_lines(self, run: subprocess.CompletedProcess[str]) -> list[str]:
        """The stamp's lines of a run: those beginning `verify:` other than the gate's two closing lines, a pass's
        and, since S04, a failed run's (AC-S04-9)."""
        closing = (CLOSING, FAILED)
        return [line for line in run.stdout.splitlines() if line.startswith(REUSE_PREFIX) and line not in closing]


def key_of(repo: Path) -> str:
    """The key of `repo` as `reuse` would build it with no tool to ask, in this process, in that directory."""
    module = load_script(repo)
    was = Path.cwd()
    os.chdir(repo)
    try:
        return str(module.build_key({})["key"])
    finally:
        os.chdir(was)


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


def load_script(repo: Path) -> ModuleType:
    """The project's own `scripts/verify-stamp.py`, loaded as a module so a test can read its lists and build its
    key without a gate run. Nothing is written beside it."""
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("verify_stamp_under_test", repo / "scripts" / "verify-stamp.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class KeyTestCase(StampTestCase):
    """Examples that hold the key itself: it is built in this process, in the project's directory, for the tree and
    the environment as they stand — the same function a `reuse` run calls, with no tool to ask."""

    @contextlib.contextmanager
    def in_project(self) -> Iterator[None]:
        was = Path.cwd()
        os.chdir(self.repo)
        try:
            yield
        finally:
            os.chdir(was)

    def key(self) -> str:
        module = load_script(self.repo)
        with self.in_project():
            return str(module.build_key({})["key"])

    @contextlib.contextmanager
    def variable(self, name: str, value: str | None) -> Iterator[None]:
        """`name` set to `value` (unset for None) for the length of the block, as it was afterwards."""
        was = os.environ.get(name)
        if value is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = value
        try:
            yield
        finally:
            if was is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = was
