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


def scoped_line(branch: str, short: str, extra: str = "") -> str:
    return (f"check-ux-gates: {branch} — previews scoped to what changed since {short} (the base of `main`){extra}; "
            "UX_GATES_SINCE=all renders every preview")


class DefaultTest(GatesCase):
    """On a slice branch outside CI, with `UX_GATES_SINCE` unset: the previews the slice's changes can move."""

    def cut(self) -> str:
        """`slice/S1` cut from `main`; the short id of the base."""
        self.branch()
        return git(self.repo, "rev-parse", "--short", "main").strip()

    def test_e1_one_previews_stylesheet_renders_that_preview_and_the_apps_directory_gates(self) -> None:
        short = self.cut()
        self.edit(f"{STYLES}/linked.css")
        said, previews, calls = self.gate()
        self.assertEqual((previews, calls), ({"linked.html"}, 4 + 4), said)
        self.assertEqual([line for line in said.splitlines() if "previews scoped" in line],
                         [scoped_line("slice/S1", short)])
        self.assertIn("literal values outside the tokens", said, "the file gate always runs")
        self.assertIn("12 render gate(s) over previews nothing changed, not rendered", said)

    def test_a_stylesheet_reached_only_through_an_import_counts_as_it_does_for_a_ref(self) -> None:
        self.cut()
        self.edit(f"{STYLES}/deep.css")
        _, previews, _ = self.gate()
        self.assertEqual(previews, {"imported.html"})

    def test_e2_on_the_trunk_every_preview_renders_and_the_line_says_why(self) -> None:
        self.edit(f"{STYLES}/linked.css")
        said, previews, calls = self.gate()
        self.assertEqual((previews, calls), (EVERY, 4 + 4 * len(EVERY)))
        self.assertIn("check-ux-gates: every preview in scope — this is the trunk (`main`)\n", said)
        self.assertNotIn("previews scoped", said)

    def test_e4_all_renders_every_preview_on_a_slice_branch_and_says_so(self) -> None:
        self.cut()
        self.edit(f"{STYLES}/linked.css")
        said, previews, _ = self.gate(UX_GATES_SINCE="all")
        self.assertEqual(previews, EVERY)
        self.assertIn("check-ux-gates: UX_GATES_SINCE=all — every preview in scope\n", said)
        self.assertNotIn("previews scoped", said)

    def test_a_value_of_only_blanks_is_unset(self) -> None:
        short = self.cut()
        self.edit(f"{STYLES}/linked.css")
        said, previews, _ = self.gate(UX_GATES_SINCE="  ")
        self.assertEqual(previews, {"linked.html"})
        self.assertIn(scoped_line("slice/S1", short), said)

    def test_the_every_preview_rule_holds_for_the_default(self) -> None:
        self.cut()
        for moved in ("package-lock.json", ".github/workflows/verify.yml", "scripts/check-ux-gates.py",
                      "scripts/extensions/ux-gates/init.py"):
            with self.subTest(moved=moved):
                self.edit(moved, "\n# moved\n")
                said, previews, _ = self.gate()
                self.assertEqual(previews, EVERY)
                self.assertIn(f"{moved} changed, so every preview is in scope", said)
                git(self.repo, "checkout", "-q", "--", moved)

    def test_a_file_whose_bytes_a_filter_hides_from_git_still_counts(self) -> None:
        """`changes.changed` is what the scoped gate selects on: a stylesheet edited under an `eol` rule git
        normalises away is changed on disk, and renders."""
        self.cut()
        (self.repo / ".gitattributes").write_text("*.css text eol=lf\n", encoding="utf-8")
        commit_all(self.repo, "attributes")
        sheet = self.repo / STYLES / "linked.css"
        sheet.write_bytes(sheet.read_bytes().replace(b"\n", b"\r\n"))
        self.assertEqual(git(self.repo, "diff", "--name-only").strip(), "", "git sees no change")
        _, previews, _ = self.gate()
        self.assertEqual(previews, {"linked.html"})

    def test_e8_a_commit_on_local_main_the_forge_lacks_counts_as_changed(self) -> None:
        origin = self.scratch / "origin.git"
        subprocess.run(["git", "init", "-q", "--bare", str(origin)], check=True, timeout=60)
        git(self.repo, "remote", "add", "origin", str(origin))
        git(self.repo, "push", "-q", "origin", "main")
        self.edit(f"{STYLES}/linked.css")
        commit_all(self.repo, "a stylesheet, committed on main and not pushed")
        short = self.cut()
        said, previews, _ = self.gate()
        self.assertEqual(previews, {"linked.html"}, said)
        line = next(line for line in said.splitlines() if "previews scoped" in line)
        self.assertTrue(line.startswith(scoped_line("slice/S1", short).split(";")[0] + "; `main` at "), line)
        self.assertIn("has 1 commits `origin/main`", line)
        self.assertTrue(line.endswith("; UX_GATES_SINCE=all renders every preview"), line)

    def test_e8_with_nothing_unpushed_the_same_commit_renders_nothing(self) -> None:
        origin = self.scratch / "origin.git"
        subprocess.run(["git", "init", "-q", "--bare", str(origin)], check=True, timeout=60)
        git(self.repo, "remote", "add", "origin", str(origin))
        self.edit(f"{STYLES}/linked.css")
        commit_all(self.repo, "a stylesheet")
        git(self.repo, "push", "-q", "origin", "main")
        self.cut()
        _, previews, calls = self.gate()
        self.assertEqual((previews, calls), (set(), 0))


if __name__ == "__main__":
    unittest.main()
