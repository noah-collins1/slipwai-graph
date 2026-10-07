"""`check-ux-gates` and what it renders: a ref reads names the way git gives them NUL-separated (R8 · AC-S07-12), and
on a slice branch outside CI the default scopes from the slice's base (T006, AC-S07-11).

The project is one the factory generates with a React app and the gates adopted, three previews and one named with a
space committed on `main`, generated once per process and copied per test. `node` and `npx` are `test_ux_gates_scale`'s
fakes: what rendered is read from `node`'s own log, never from what the script printed.
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

from support import FactoryTestCase
from test_design_extensions import FAKE_NODE, FAKE_NPX, FAKE_SPECIFY

sys.dont_write_bytecode = True

SCREENS = {
    "linked.html": '<!doctype html><link rel="stylesheet" href="../src/styles/linked.css"><button>Go</button>\n',
    "imported.html": "<!doctype html><style>@import url('../src/styles/entry.css');</style><button>Go</button>\n",
    "plain.html": '<!doctype html><link rel="stylesheet" href="https://cdn.example/x.css"><button>Go</button>\n',
    "my page.html": '<!doctype html><link rel="stylesheet" href="https://cdn.example/y.css"><button>Go</button>\n',
}
EVERY = {"linked.html", "imported.html", "plain.html", "my page.html"}
STRIPPED = ("CI", "GITHUB_ACTIONS", "GITLAB_CI", "MAKEFLAGS", "MFLAGS", "MAKELEVEL", "MAKEOVERRIDES", "MAKEFILES",
            "VERIFY_FORCE", "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GITHUB_HEAD_REF", "GITHUB_BASE_REF",
            "CI_COMMIT_REF_NAME", "CI_MERGE_REQUEST_TARGET_BRANCH_NAME", "UX_GATES_SINCE", "UX_GATES_SHARD",
            "UX_GATES_REQUIRE", "UX_GATES_JOBS")
IDENTITY = ("-c", "user.name=t", "-c", "user.email=t@local", "-c", "commit.gpgsign=false", "-c",
            "maintenance.auto=false")
STYLES = "apps/web/src/styles"
SCREENS_DIR = "apps/web/screens"
_made: list[tuple[Path, Path]] = []


def git(repo: Path, *arguments: str) -> str:
    done = subprocess.run(["git", *IDENTITY, *arguments], cwd=repo, check=True, text=True, capture_output=True,
                          timeout=60)
    return done.stdout


def commit_all(repo: Path, message: str) -> None:
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", message)


def made() -> tuple[Path, Path]:
    """The generated project with the gates adopted and the previews committed on `main`, and the stand-in `bin`."""
    if not _made:
        parent = Path(tempfile.mkdtemp(prefix="ux-default-"))
        atexit.register(shutil.rmtree, parent, ignore_errors=True)
        repo = FactoryTestCase().generate(parent, "scaled", frontend="react-vite")
        stand_ins = parent / "fake-bin"
        stand_ins.mkdir()
        for name, body in (("npx", FAKE_NPX), ("node", FAKE_NODE), ("specify", FAKE_SPECIFY)):
            (stand_ins / name).write_text(body, encoding="utf-8")
            (stand_ins / name).chmod(0o755)
        environment = {key: value for key, value in os.environ.items() if key not in STRIPPED}
        environment |= {"PATH": f"{stand_ins}:{os.environ['PATH']}", "NPX_LOG": f"{parent}/n",
                        "NODE_LOG": f"{parent}/c", "FAKE_BROWSER": "chrome"}
        subprocess.run(["./init", "--integration", "codex", "--extension", "ux-gates"], cwd=repo, check=True,
                       env=environment, capture_output=True, timeout=300)
        (repo / SCREENS_DIR).mkdir()
        for name, text in SCREENS.items():
            (repo / SCREENS_DIR / name).write_text(text, encoding="utf-8")
        styles = repo / STYLES
        (styles / "linked.css").write_text(".a { color: var(--ink); }\n", encoding="utf-8")
        (styles / "entry.css").write_text('@import "./deep.css";\n', encoding="utf-8")
        (styles / "deep.css").write_text(".b { color: var(--ink); }\n", encoding="utf-8")
        commit_all(repo, "screens")
        _made.append((repo, stand_ins))
    return _made[0]


class GatesCase(unittest.TestCase):
    """A copy of that project on `main`, and `check-ux-gates` run in it with the environment a person has."""

    def setUp(self) -> None:
        template, stand_ins = made()
        scratch = Path(tempfile.mkdtemp(prefix="ux-case-"))
        self.addCleanup(shutil.rmtree, scratch, ignore_errors=True)
        self.repo = scratch / "project"
        shutil.copytree(template, self.repo, symlinks=True)
        self.log = scratch / "node-calls"
        self.stand_ins = stand_ins
        self.scratch = scratch

    def environment(self, **more: str) -> dict[str, str]:
        base = {key: value for key, value in os.environ.items() if key not in STRIPPED}
        base |= {"PATH": f"{self.stand_ins}:{os.environ['PATH']}", "NPX_LOG": f"{self.scratch}/n",
                 "NODE_LOG": str(self.log), "FAKE_BROWSER": "chrome", "SLIPWAI_NO_INSTALL": "1"}
        return base | more

    def gate(self, **more: str) -> tuple[str, set[str], int]:
        """What the script printed, the previews the render gates opened, and how many calls opened them."""
        self.log.unlink(missing_ok=True)
        done = subprocess.run(["python3", "-B", "scripts/check-ux-gates.py"], cwd=self.repo, text=True,
                              capture_output=True, env=self.environment(**more), timeout=300)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        calls = [line for line in self.log.read_text(encoding="utf-8").splitlines() if line != "probe"] \
            if self.log.exists() else []
        previews = {line.split(f"{SCREENS_DIR}/", 1)[1].split(" --dark")[0] for line in calls
                    if f"{SCREENS_DIR}/" in line and ".html" in line}
        return done.stdout, previews, len(calls)

    def branch(self, name: str = "slice/S1") -> None:
        git(self.repo, "checkout", "-q", "-b", name)

    def edit(self, path: str, text: str = "/* edit */\n") -> None:
        target = self.repo / path
        target.write_text(target.read_text(encoding="utf-8") + text, encoding="utf-8")


class RefTest(GatesCase):
    """`UX_GATES_SINCE=<ref>` as it was, with the names git gives it read whole (AC-S07-12)."""

    def test_e5_a_ref_scopes_as_it_did_on_a_slice_branch(self) -> None:
        self.branch()
        self.edit(f"{STYLES}/linked.css")
        commit_all(self.repo, "style")
        said, previews, _ = self.gate(UX_GATES_SINCE="HEAD~1")
        self.assertEqual(previews, {"linked.html"})
        self.assertIn("check-ux-gates: UX_GATES_SINCE=HEAD~1 — ", said)
        self.assertNotIn("previews scoped to what changed since", said)

    def test_e6_a_stylesheet_renamed_is_changed_where_a_preview_links_it_by_its_old_name(self) -> None:
        git(self.repo, "mv", f"{STYLES}/linked.css", f"{STYLES}/renamed.css")
        _, previews, _ = self.gate(UX_GATES_SINCE="HEAD")
        self.assertEqual(previews, {"linked.html"})

    def test_e7_a_preview_named_with_a_space_renders_when_it_changes(self) -> None:
        self.edit(f"{SCREENS_DIR}/my page.html", "<p>more</p>\n")
        _, previews, _ = self.gate(UX_GATES_SINCE="HEAD")
        self.assertEqual(previews, {"my page.html"})

    def test_e7_and_so_does_one_that_is_new_and_untracked(self) -> None:
        (self.repo / SCREENS_DIR / "a new one.html").write_text(SCREENS["plain.html"], encoding="utf-8")
        _, previews, _ = self.gate(UX_GATES_SINCE="HEAD")
        self.assertEqual(previews, {"a new one.html"})


if __name__ == "__main__":
    unittest.main()
