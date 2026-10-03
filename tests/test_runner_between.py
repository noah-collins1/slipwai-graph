"""A control changed between two iterations parks the run before the next one starts (D64; AC-S02-70, -71, -76, -79).

The runner takes the controls' signature before and after every iteration. What changes a gate in between, after the
after-signature and before the next before-signature, used to become the next baseline unseen. The runner now keeps the
last after-signature and compares it with the next before-signature; where no park came between, a difference parks the
run before the iteration starts.

The change is made deterministically, in the runner's own gap: the index check before an iteration calls the CLI's
`sync` where a tracked file is ahead of the index, and the stand-in CLI written here runs a script the iteration left
armed. That is what a process left behind in a session of its own does (the adversary's reproduction waits for the
entry and then appends to a gate), without the race between that process and the next signature. The runs are bounded
by `max_iterations` and a timeout, so a run that fails to park fails an assertion.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import time
from pathlib import Path

from support import FactoryTestCase
from test_code_index_health import indexed
from test_cruise_index import bare_path
from test_cruise_runner import enable, fake_harness, logged, outside_a_run

GATE = "scripts/check-ux-gates.py"
# `codegraph`, wrapped: where `sync` is called and a script was armed, the script runs first, once.
WRAPPER = """#!/bin/sh
here="$(dirname "$0")"
if [ "$1" = sync ] && [ -f "$GAP_EDIT" ]; then sh "$GAP_EDIT"; rm -f "$GAP_EDIT"; fi
exec "$here/codegraph-real" "$@"
"""
TIMEOUT = 120


def gapped(case: FactoryTestCase, directory: str, name: str) -> tuple[Path, dict[str, str]]:
    """A project with the stand-in index CLI, wrapped so that an armed script runs at the index check's `sync`."""
    repo, env, _ = indexed(case, directory, name)
    here = Path(directory)
    bare_path(here, "sleep", "rm")
    (here / "tools/codegraph").rename(here / "tools/codegraph-real")
    (here / "tools/codegraph").write_text(WRAPPER)
    (here / "tools/codegraph").chmod(0o755)
    return repo, {**env, "GAP_EDIT": str(here / "gap-edit.sh")}


def arm(directory: str, repo: Path, shell: str) -> str:
    """The harness lines that make the index stale (so `sync` is called before the next iteration) and arm `shell`
    for it; the iteration itself changes no control."""
    stale = next(path for path in sorted(repo.rglob("*.py")) if ".codegraph" not in path.parts
                 and "scripts" not in path.parts and "tools" not in path.parts and ".git" not in path.parts)
    return (f"echo '# stale' >> {stale}\n"
            f"cat > {Path(directory) / 'gap-edit.sh'} <<'ARMED'\n{shell}\nARMED")


def ran(repo: Path, *arguments: str, env: dict[str, str]) -> subprocess.CompletedProcess:
    return subprocess.run(["python3", "scripts/agents/cruise.py", *arguments], cwd=repo, text=True,
                          capture_output=True, stdin=subprocess.DEVNULL, env=outside_a_run(env), timeout=TIMEOUT)


class Resumable:
    """A runner that parks and is resumed by a person: started with its output to a file, waited for by what it
    prints, and ended by the test, never by a hang."""

    def __init__(self, repo: Path, directory: str, env: dict[str, str]) -> None:
        self.repo, self.out = repo, Path(directory) / "runner.out"
        self.handle = self.out.open("wb")
        self.process = subprocess.Popen([sys.executable, "scripts/agents/cruise.py", "run"], cwd=repo,
                                        stdin=subprocess.DEVNULL, stdout=self.handle, stderr=subprocess.STDOUT,
                                        env=outside_a_run(env))

    def text(self) -> str:
        return self.out.read_text(encoding="utf-8")

    def wait_for(self, words: str, count: int = 1) -> None:
        deadline = time.monotonic() + TIMEOUT
        while self.text().count(words) < count:
            if self.process.poll() is not None or time.monotonic() > deadline:
                raise AssertionError(f"the runner never said {words!r} ({count}x):\n{self.text()}")
            time.sleep(0.05)

    def tell(self, message: str) -> None:
        subprocess.run([sys.executable, "scripts/agents/cruise.py", "tell", message], cwd=self.repo,
                       stdin=subprocess.DEVNULL, capture_output=True, env=outside_a_run(), timeout=TIMEOUT, check=True)

    def end(self) -> str:
        try:
            self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            pass  # a run still going is ended below, and what it printed is the evidence
        finally:
            if self.process.poll() is None:
                self.process.terminate()
                self.process.wait()
            self.handle.close()
        return self.text()


PARK = ("cruise: parked — a gate or a control of the run changed between iterations 1 and 2 — "
        f"{GATE} (modified) — and nothing an iteration starts may change one; revert the change, or keep it on "
        "purpose and resume with a message")


class RunnerBetweenTest(FactoryTestCase):
    def test_e70_a_gate_changed_in_the_gap_parks_the_run_before_the_next_iteration_starts(self) -> None:
        """AC-S02-70 and -71: under `--no-park` the run exits 3 with the park line last; no entry for the
        iteration that did not start, and the harness ran once."""
        with tempfile.TemporaryDirectory() as directory:
            repo, env = gapped(self, directory, "between-parks")
            enable(repo, max_iterations="3")
            arming = arm(directory, repo, f"echo '# edited by what the iteration left behind' >> {repo / GATE}")
            harness = fake_harness(Path(directory), f'[ "$n" -eq 1 ] && {{ {arming}\n}}\necho "cruise: continue"')
            ended = ran(repo, "run", "--no-park", env={**env, **harness})
            self.assertEqual(ended.returncode, 3, ended.stdout + ended.stderr)
            self.assertEqual(ended.stdout.splitlines()[-1], PARK)
            self.assertEqual([entry["iteration"] for entry in logged(repo)], [1])
            self.assertEqual((Path(directory) / "calls").read_text().strip(), "1")
            self.assertNotIn("controls_changed", logged(repo)[0])

    def test_e76_a_file_added_under_tools_between_iterations_is_an_install_and_does_not_park(self) -> None:
        """AC-S02-76, first half (hold): the same function answers, so an install is not a change."""
        with tempfile.TemporaryDirectory() as directory:
            repo, env = gapped(self, directory, "between-installs")
            enable(repo, max_iterations="2")
            made = repo / "tools/ext/installed-in-the-gap"
            arming = arm(directory, repo, f"mkdir -p {made.parent} && echo new > {made}")
            harness = fake_harness(Path(directory), f'[ "$n" -eq 1 ] && {{ {arming}\n}}\necho "cruise: continue"')
            ended = ran(repo, "run", "--no-park", env={**env, **harness})
            self.assertEqual(ended.returncode, 0, ended.stdout + ended.stderr)
            self.assertTrue((repo / "tools/ext/installed-in-the-gap").is_file(), "the gap edit never ran")
            self.assertEqual([entry["iteration"] for entry in logged(repo)], [1, 2])
            self.assertTrue(all("controls_changed_between" not in entry for entry in logged(repo)))

    def test_e76_a_file_modified_or_deleted_under_tools_between_iterations_parks_the_run(self) -> None:
        """AC-S02-76, second half: an install is not a change, an edit is."""
        for how, shell, kind in (("modified", "echo more >> {t}", "modified"), ("deleted", "rm {t}", "deleted")):
            with self.subTest(how), tempfile.TemporaryDirectory() as directory:
                repo, env = gapped(self, directory, f"between-tools-{how}")
                enable(repo, max_iterations="3")
                target = "tools/ext/installed"
                arming = arm(directory, repo, shell.format(t=repo / target))
                harness = fake_harness(Path(directory), f'''[ "$n" -eq 1 ] && {{ mkdir -p tools/ext; echo one > {target}
{arming}
}}
echo "cruise: continue"''')
                ended = ran(repo, "run", "--no-park", env={**env, **harness})
                self.assertEqual(ended.returncode, 3, ended.stdout + ended.stderr)
                park = PARK.replace(f"{GATE} (modified)", f"{target} ({kind})")
                self.assertEqual(ended.stdout.splitlines()[-1], park)
                self.assertEqual([entry["iteration"] for entry in logged(repo)], [1])

    def test_e79_an_iteration_ended_by_tell_now_parks_and_the_message_waits_for_the_park(self) -> None:
        """AC-S02-79: iteration 1 is ended for a message; a gate changes in the gap; the run parks, and once
        something under `specs/` resumes it the message is given to the iteration that runs."""
        with tempfile.TemporaryDirectory() as directory:
            repo, env = gapped(self, directory, "between-tell-now")
            enable(repo)
            arming = arm(directory, repo, f"echo '# edited' >> {repo / GATE}")
            harness = fake_harness(Path(directory), f'''case "$n" in
  1) {arming}
     python3 scripts/agents/cruise.py tell --now "mind the gate"; sleep 30; echo "cruise: continue";;
  *) echo "cruise: done";;
esac''')
            runner = Resumable(repo, directory, {**env, **harness})
            try:
                runner.wait_for("cruise: waiting;")
                self.assertEqual(logged(repo)[0].get("interrupted"), True)
                self.assertEqual([entry["iteration"] for entry in logged(repo)], [1])
                (repo / "specs/answer.md").write_text("carry on\n", encoding="utf-8")
                runner.wait_for("cruise: done")
            finally:
                output = runner.end()
            self.assertIn(PARK, output)
            entries = logged(repo)
            self.assertEqual([entry["iteration"] for entry in entries], [1, 2])
            self.assertEqual(entries[1]["told"], ["mind the gate"])
            self.assertEqual(entries[1]["controls_changed_between"], [f"{GATE} (modified)"])
