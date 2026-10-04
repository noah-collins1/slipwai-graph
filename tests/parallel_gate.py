"""What the `test_parallel_gate_*` modules share: shapes, stand-in tools, a bounded `make`, and readers over the log.

Not a test module. A shape is generated once per process and copied per test; the stand-ins are executables written
into a directory first on `PATH`; evidence is the log a stand-in appends to, never a printed line. A stand-in `uv`
logs `start<TAB>arguments` when it is called and `end<TAB>arguments` when it returns, so a log shows what ran and
whether two calls overlapped; where a test asks, a `sync` holds, bounded, while another `uv` call is in flight and
logs `met` if another call was in flight or started meanwhile, else `alone`. Nothing sleeps as proof or reads a clock.
"""
from __future__ import annotations

import atexit
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from stamp_fixture import BRANCH, CI_MARKERS, GIT_STATE, MAKE_STATE, PYVENV_CFG, git

from slipwai.assets import ROOT

sys.dont_write_bytecode = True

SERVICE = "apps/service"
# name -> the arguments of `slipwai generate`; ADDED is `add-service <name> --language <language>` on top of it.
SHAPES: dict[str, tuple[str, ...]] = {
    "plain": ("--profile", "standard", "--backend", "python", "--frontend", "none", "--http", "none"),
    "db": ("--profile", "event-modelling", "--backend", "python", "--frontend", "none", "--http", "none",
           "--event-store", "postgres"),
    "api": ("--profile", "event-modelling", "--backend", "python", "--frontend", "none", "--http", "fastapi",
            "--event-store", "postgres"),
}
SHAPES["two"] = SHAPES["plain"]
for _name, _backend, _frontend in (("quarkus", "java-quarkus", "none"), ("spring", "java-spring", "react-vite"),
                                   ("go", "go", "none"), ("go-web", "go", "react-vite"), ("ts", "typescript", "none"),
                                   ("java-py", "java-quarkus", "react-vite"), ("java-go", "java-quarkus", "none")):
    SHAPES[_name] = ("--profile", "standard", "--backend", _backend, "--frontend", _frontend, "--http", "none")
ADDED = {"two": ("second", "python"), "java-py": ("second", "python"), "java-go": ("second", "go")}

_UV = """#!/bin/sh
log() { printf '%s\\t%s\\n' "$1" "$2" >> "$STANDIN_LOG"; }
args="$*"
log start "$args"
starts() { grep -c '^start' "$STANDIN_LOG"; }
in_flight() { echo $(($(starts) - $(grep -c '^end' "$STANDIN_LOG"))); }
case "$1" in
  --version) echo "uv 0.12.20 (stand-in)" ;;
  sync)
    while [ $# -gt 0 ]; do
      if [ "$1" = --project ]; then dir=$2; fi
      shift
    done
    if [ -n "$STANDIN_SYNC_HOLD" ]; then
      n=0; seen=alone; first=$(starts)
      while [ "$n" -lt 40 ]; do
        if [ "$(in_flight)" -ge 2 ] || [ "$(starts)" -gt "$first" ]; then seen=met; break; fi
        sleep 0.05; n=$((n + 1))
      done
      log "$seen" "sync $dir"
    fi
    if [ -n "$STANDIN_SYNC_FAIL" ]; then
      echo "uv: sync failed (stand-in)" >&2; log end "$args"; exit 1
    fi
    mkdir -p "$dir/.venv"
    [ -f "$dir/.venv/pyvenv.cfg" ] || printf '%s' "$STANDIN_PYVENV" > "$dir/.venv/pyvenv.cfg"
    ;;
  run)
    # The tool a gate recipe runs (`ruff check` and `mypy` are the two a barrier or a failure names), as `lint` and
    # `typecheck` call it: the word after `--no-sync`.
    tool=; after=; word=
    for a in "$@"; do
      if [ -n "$after" ]; then tool=$a; after=; word=1; continue; fi
      if [ -n "$word" ]; then [ "$tool" = ruff ] && [ "$a" != check ] && tool=; word=; fi
      [ "$a" = --no-sync ] && after=1
    done
    peer=
    case "$tool" in ruff) peer=mypy ;; mypy) peer=ruff ;; esac
    # Met only where the peer arrived before this call left the barrier and was not already through it: a serial run's
    # second check finds the first one's `.done` and is alone, however the first one's marker stands.
    rendezvous() {
      seen=alone
      if [ ! -e "$STANDIN_LOG.$peer.$1.done" ]; then
        : > "$STANDIN_LOG.$tool.$1"
        n=0
        while [ "$n" -lt 60 ]; do
          if [ -e "$STANDIN_LOG.$peer.$1" ]; then seen=met; break; fi
          sleep 0.05; n=$((n + 1))
        done
      fi
      : > "$STANDIN_LOG.$tool.$1.done"
      log "barrier-$seen" "$tool $1"
    }
    # One line out, then a bounded wait for the test to have read it from the pipe: `line-seen` if it came,
    # `line-held` if the line was still in make's hands when the ceiling was reached.
    if [ "$tool" = ruff ] && [ -n "$STANDIN_WAIT_FILE" ]; then
      echo "ruff line 1"
      n=0; seen=held
      while [ "$n" -lt 100 ]; do
        if [ -e "$STANDIN_WAIT_FILE" ]; then seen=seen; break; fi
        sleep 0.05; n=$((n + 1))
      done
      log "line-$seen" ruff
      echo "ruff line 2"
    fi
    if [ -n "$peer" ]; then
      if [ -n "$STANDIN_BARRIER" ]; then rendezvous 0; fi
      i=1
      while [ "$i" -le "${STANDIN_LINES:-0}" ]; do
        echo "$tool line $i"
        if [ -n "$STANDIN_BARRIER" ]; then rendezvous "$i"; fi
        i=$((i + 1))
      done
    fi
    case " $STANDIN_FAIL_TOOLS " in
      "  ") ;;
      *" $tool "*) echo "uv: $tool failed (stand-in)" >&2; log end "$args"; exit 1 ;;
    esac
    # `python -m <package>.openapi <out>`: the document the project already commits, as the app would write it.
    prev=; module=; project=.
    for a in "$@"; do
      [ "$prev" = -m ] && module=$a
      [ "$prev" = --project ] && project=$a
      prev=$a; last=$a
    done
    case "$module" in *.openapi) cp "$project/openapi.json" "$last" ;; esac
    ;;
esac
log end "$args"
exit 0
"""
_QUIET = "#!/bin/sh\nexit 0\n"
_NPM = '#!/bin/sh\nd=.; [ "$1" = --prefix ] && d=$2\nmkdir -p $d/node_modules; : >$d/node_modules/.package-lock.json\n'
# `./mvnw`, `go`, `gofmt`: logs `native-start`/`native-end` around a bounded wait for another native call in flight
# (`barrier-met`, else `barrier-alone`); `go test -coverprofile` and `go list` answer so the coverage script passes.
_NATIVE = """#!/bin/sh
[ "$1" = version ] && { echo "go version go1.24.0 linux/amd64"; exit 0; }
log() { printf '%s\\t%s\\n' "$1" "$2" >> "$STANDIN_LOG"; }
log native-start "@NAME@ $*"
n=0; seen=alone
flying() { echo $(($(grep -c '^native-start' "$STANDIN_LOG") - $(grep -c '^native-end' "$STANDIN_LOG"))); }
while [ "$n" -lt 15 ]; do
  [ "$(flying)" -ge 2 ] && { seen=met; break; }
  sleep 0.05; n=$((n + 1))
done
log "barrier-$seen" "@NAME@ $*"
case "@NAME@ $*" in
  "go test"*coverprofile*) printf 'mode: set\\nexample/x/x.go:1.1,2.2 1 1\\n' > coverage.out ;;
  "go list"*) echo '{"ImportPath":"example/x","Name":"x","TestGoFiles":["x_test.go"]}' ;;
esac
log native-end "@NAME@ $*"
"""
_cache: dict[str, Path] = {}


def shape(name: str) -> Path:
    """The generated project of this shape, on a branch that is not the trunk, with no `.venv`; tests copy it."""
    if name not in _cache:
        parent = Path(tempfile.mkdtemp(prefix=f"parallel-gate-{name}-"))
        atexit.register(shutil.rmtree, parent, ignore_errors=True)
        subprocess.run([str(ROOT / "slipwai"), "generate", "project", *SHAPES[name], "--output", str(parent),
                        "--skip-checks"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        repo = parent / "project"
        if name in ADDED:
            subprocess.run([str(ROOT / "slipwai"), "add-service", ADDED[name][0], "--language", ADDED[name][1]],
                           cwd=repo, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        git(repo, "checkout", "-q", "-b", BRANCH)
        for key, value in (("user.name", "t"), ("user.email", "t@local"), ("commit.gpgsign", "false")):
            git(repo, "config", key, value)
        git(repo, "add", "-A")
        git(repo, "-c", "maintenance.auto=false", "commit", "-q", "--allow-empty", "-m", "shape")
        _cache[name] = repo
    return _cache[name]


def write_stand_ins(directory: Path) -> None:
    """`uv` as above; `npm` leaving its marker; `node` and `pip-audit` as tools that do nothing and succeed."""
    directory.mkdir(parents=True, exist_ok=True)
    for name, text in (("uv", _UV), ("npm", _NPM), ("node", _QUIET), ("pip-audit", _QUIET)):
        (directory / name).write_text(text, encoding="utf-8")
        (directory / name).chmod(0o755)


def write_native(path: Path, name: str) -> None:
    """The native tool `name` (`mvnw`, `go`, `gofmt`) written at `path`."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_NATIVE.replace("@NAME@", name), encoding="utf-8")
    path.chmod(0o755)


def gate_environment(
    bin_dir: Path, log: Path, extra: dict[str, str | None] | None = None,
) -> dict[str, str]:
    """The stand-ins first on `PATH`, the three CI markers and make's and git's state removed unless `extra` sets
    one (a `None` removes a name)."""
    env = {key: value for key, value in os.environ.items() if key not in CI_MARKERS + MAKE_STATE + GIT_STATE}
    env["PATH"] = f"{bin_dir}{os.pathsep}{env.get('PATH', '')}"
    env["STANDIN_LOG"] = str(log)
    env["STANDIN_PYVENV"] = PYVENV_CFG
    for key, value in (extra or {}).items():
        if value is None:
            env.pop(key, None)
        else:
            env[key] = value
    return env


def run_make(repo: Path, env: dict[str, str], *args: str) -> subprocess.CompletedProcess[str]:
    """`make <args>` in `repo`, bounded."""
    return subprocess.run(["make", *args], cwd=repo, env=env, text=True, capture_output=True, timeout=180)


def log_text(log: Path) -> str:
    """The whole log, for a failure message."""
    return log.read_text(encoding="utf-8") if log.exists() else ""


def log_lines(log: Path) -> list[tuple[str, str]]:
    """Each line of the log as (event, arguments), in the order written."""
    found = []
    for line in log.read_text(encoding="utf-8").splitlines() if log.exists() else []:
        event, _, arguments = line.partition("\t")
        found.append((event, arguments))
    return found


def _started(log: Path, first: str) -> list[str]:
    return [a for e, a in log_lines(log) if e == "start" and a.split()[:1] == [first]]


def sync_lines(log: Path) -> list[str]:
    """The arguments of every `uv sync` that started."""
    return _started(log, "sync")


def run_lines(log: Path) -> list[str]:
    """The arguments of every `uv run` that started."""
    return _started(log, "run")


def synced_projects(log: Path) -> list[str]:
    """The `--project` of each sync that started, in order."""
    return [a.split("--project ")[1].split()[0] for a in sync_lines(log) if "--project " in a]


def syncs_precede_runs(log: Path) -> bool:
    """True where every sync started before the first run did (and there was at least one sync)."""
    kinds = [a.split()[0] for e, a in log_lines(log) if e == "start" and a.split()[:1] in (["sync"], ["run"])]
    if "sync" not in kinds:
        return False
    last_sync = len(kinds) - 1 - kinds[::-1].index("sync")
    return "run" not in kinds[:last_sync]


def sync_ended_before_any_run(log: Path) -> bool:
    """True where every sync's `end` line precedes the first run's `start` line."""
    events = [(e, a.split()[0]) for e, a in log_lines(log) if a.split()[:1] in (["sync"], ["run"])]
    runs = [i for i, (e, kind) in enumerate(events) if e == "start" and kind == "run"]
    ends = [i for i, (e, kind) in enumerate(events) if e == "end" and kind == "sync"]
    return bool(ends) and (not runs or max(ends) < runs[0])


def barrier_events(log: Path) -> list[str]:
    """Each barrier verdict a stand-in logged, `met` or `alone`, in the order written."""
    return [e.removeprefix("barrier-") for e, _ in log_lines(log) if e.startswith("barrier-")]


def line_events(log: Path) -> list[str]:
    """What a held-line stand-in logged: `seen` where its first line reached the reader first, else `held`."""
    return [e.removeprefix("line-") for e, _ in log_lines(log) if e.startswith("line-")]


def has_output_sync() -> bool:
    """Whether the `make` on this machine lists `output-sync` among its features."""
    done = subprocess.run(["make", "-f", "-"], input="$(info $(.FEATURES))\nx:;@:\n", text=True,
                          capture_output=True, timeout=60)
    return "output-sync" in done.stdout.split()


def native_calls(log: Path) -> list[tuple[str, str]]:
    """Each native tool's `start` and `end` as (event, "<tool> <arguments>"), in the order written."""
    return [(e.removeprefix("native-"), a) for e, a in log_lines(log) if e.startswith("native-")]


def native_overlapped(log: Path) -> bool:
    """Whether a native call started while another was still running."""
    events = [event for event, _ in native_calls(log)]
    return any(events[: i + 1].count("start") - events[: i + 1].count("end") > 1 for i in range(len(events)))


def overlapped(log: Path) -> bool:
    """Whether a sync was held while another `uv` call was in flight (the stand-in logged `met`)."""
    return any(event == "met" for event, _ in log_lines(log))


class ParallelGateTestCase(unittest.TestCase):
    """One copy of `SHAPE` per test, a stand-in directory first on `PATH`, and `run`."""

    SHAPE = "plain"
    # Whether each service starts with an environment (as a developer's does), or with none (as a fresh clone's).
    VENV = True
    repo: Path
    log: Path
    bin: Path

    def setUp(self) -> None:
        sys.dont_write_bytecode = True
        scratch = Path(tempfile.mkdtemp(prefix="parallel-gate-run-"))
        self.addCleanup(shutil.rmtree, scratch, ignore_errors=True)
        self.repo = scratch / "project"
        shutil.copytree(shape(self.SHAPE), self.repo, symlinks=True)
        self.bin = scratch / "bin"
        write_stand_ins(self.bin)
        self.log = scratch / "standin.log"
        for manifest in sorted(self.repo.glob("apps/*/pyproject.toml")) if self.VENV else []:
            (manifest.parent / ".venv").mkdir(exist_ok=True)
            (manifest.parent / ".venv" / "pyvenv.cfg").write_text(PYVENV_CFG, encoding="utf-8")

    def environment(self, extra: dict[str, str | None] | None = None) -> dict[str, str]:
        return gate_environment(self.bin, self.log, extra)

    def run_in(
        self, *command: str, env: dict[str, str | None] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        """A command in the project, as a person types it; the log is kept between runs."""
        return subprocess.run(command, cwd=self.repo, env=self.environment(env), text=True, capture_output=True,
                              timeout=180)

    def make(self, *args: str, env: dict[str, str | None] | None = None) -> subprocess.CompletedProcess[str]:
        return self.run_in("make", *args, env=env)

    def make_merged(self, *args: str, env: dict[str, str | None] | None = None) -> tuple[int, list[str]]:
        """`make <args>` with both streams on one pipe, so lines are in the order they were written: (exit, lines)."""
        done = subprocess.run(["make", *args], cwd=self.repo, env=self.environment(env), text=True, timeout=180,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return done.returncode, done.stdout.splitlines()

    def forget_log(self) -> None:
        """Empty the log and take away the barrier's markers, so a second run in one test starts afresh."""
        self.log.write_text("", encoding="utf-8")
        for marker in self.log.parent.glob(f"{self.log.name}.*"):
            marker.unlink()

    def stamps(self) -> list[Path]:
        """The stamps the project holds, under the git directory."""
        return sorted((self.repo / ".git" / "slipwai").glob("verify-stamp-*.json"))

    def assert_passed(self, done: subprocess.CompletedProcess[str]) -> None:
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
