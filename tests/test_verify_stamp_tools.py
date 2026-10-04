"""R5 (AC-S03-14, -15, -16, -17): the key is the machine's tools.

The table of tools a machine supplies is data beside `BACKEND_TOOLING`; the recipe's `--tool` words come from it; the
script asks each once with its version argument and takes the first non-empty line, whole. Everything it asks is read
from the stand-ins' log. A tool it cannot ask is a reason on one line and a run that records nothing, never a failure.
"""
from __future__ import annotations

import re
import shutil
import unittest

from stamp_fixture import CLOSING, StampTestCase, template

from slipwai.backends import BACKEND_TOOLING, MACHINE_TOOLS, machine_tools
from slipwai.catalog import CATALOG

ASKED = ["make", "git", "python3", "uv"]


class TableTest(unittest.TestCase):
    def test_every_backend_has_a_row(self) -> None:
        """e14: a backend that `BACKEND_TOOLING` has and this table has not fails here."""
        self.assertEqual(sorted(MACHINE_TOOLS), sorted(BACKEND_TOOLING))
        self.assertEqual(sorted(MACHINE_TOOLS), sorted(CATALOG["backends"]))
        for backend, tools in MACHINE_TOOLS.items():
            self.assertTrue(tools, f"{backend} asks for no tool")

    def test_each_backend_asks_for_its_own_tools(self) -> None:
        """e14: make, git and python3 everywhere; uv, node and npm, go, java by backend."""
        everywhere = ["make", "git", "python3"]
        self.assertEqual(machine_tools(["python"], False), everywhere + ["uv"])
        self.assertEqual(machine_tools(["typescript"], False), everywhere + ["node", "npm"])
        self.assertEqual(machine_tools(["go"], False), everywhere + ["go"])
        self.assertEqual(machine_tools(["java-quarkus"], False), everywhere + ["java"])
        self.assertEqual(machine_tools(["java-spring"], False), everywhere + ["java"])

    def test_several_backends_take_the_union_each_tool_once(self) -> None:
        """e14: the union, in order of first appearance, with a frontend's node and npm among it."""
        everywhere = ["make", "git", "python3"]
        self.assertEqual(machine_tools(["python", "typescript"], False), everywhere + ["uv", "node", "npm"])
        self.assertEqual(machine_tools(["java-quarkus", "java-spring"], False), everywhere + ["java"])
        self.assertEqual(machine_tools(["typescript"], True), everywhere + ["node", "npm"])
        self.assertEqual(machine_tools(["go"], True), everywhere + ["go", "node", "npm"])

    def test_the_recipe_names_the_tools_the_table_gives(self) -> None:
        """e14, the sweep: the words the Makefile hands the script are the table's, one environment per service."""
        makefile = (template() / "Makefile").read_text(encoding="utf-8")
        words = " ".join(f"--tool {tool}" for tool in machine_tools(["python"], False))
        self.assertIn(f"VERIFY_STAMP := {words} --environment apps/service/.venv\n", makefile)


class AskedTest(StampTestCase):
    def asked(self) -> list[str]:
        """The tools the stand-ins were asked their version of, in order, from the log."""
        lines = self.log.read_text(encoding="utf-8").splitlines()
        return [line.split("\t")[0] for line in lines if line.endswith("\t--version")]

    def test_the_fixture_asks_each_tool_once_and_reads_the_interpreter(self) -> None:
        """e14: make, git, python3 and uv each launched once on a full run and once on a reuse; `pyvenv.cfg` is read."""
        self.assertEqual(self.run_gate().returncode, 0)
        self.assertEqual(sorted(self.asked()), sorted(ASKED))
        stamp = self.stamp()
        tools = stamp["tools"]
        assert isinstance(tools, dict)
        for name in ASKED:
            self.assertTrue(str(tools[name]).strip(), name)
        self.assertEqual(tools["uv"], "uv 0.12.20 (stand-in)")
        self.assertIn("interpreter apps/service/.venv", tools)
        self.assertEqual(tools["interpreter apps/service/.venv"], "3.14.4")
        self.forget_log()
        self.run_gate()
        self.assertEqual(sorted(self.asked()), sorted(ASKED))
        self.assertEqual(self.checks(), [])

    def test_another_line_from_a_tool_runs_the_gate(self) -> None:
        """e15: the first non-empty line, whole; a changed one runs the gate and writes a new stamp."""
        self.assertEqual(self.run_gate().returncode, 0)
        before = self.stamp()["key"]
        self.forget_log()
        run = self.run_gate({"STANDIN_UV_VERSION": "\\n\\nuv 0.13.0 (another build)\\nsecond line"})
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertTrue(self.checks(), "no check started: the tool's new line was not in the key")
        stamp = self.stamp()
        tools = stamp["tools"]
        assert isinstance(tools, dict)
        self.assertEqual(tools["uv"], "uv 0.13.0 (another build)")
        self.assertNotEqual(stamp["key"], before)
        self.forget_log()
        self.run_gate({"STANDIN_UV_VERSION": "\\n\\nuv 0.13.0 (another build)\\nsecond line"})
        self.assertEqual(self.checks(), [], "the new stamp was not written")
        self.run_gate()
        self.assertTrue(self.checks(), "the first line came back and the other stamp was reused")

    def test_no_path_of_an_executable_is_in_the_stamp(self) -> None:
        """e15: not the stand-ins' directory, not where the real tools are."""
        self.run_gate()
        text = self.stamp_path().read_text(encoding="utf-8")  # type: ignore[union-attr]
        for name in ("make", "git", "python3"):
            found = shutil.which(name)
            assert found is not None
            self.assertNotIn(found, text)
        self.assertNotIn(str(self.bin), text)
        self.assertEqual(re.findall(r"(?<![\w.])/[\w.-]+/", text), [], text)

    def test_a_tool_a_lock_pins_is_never_asked(self) -> None:
        """e16: ruff, mypy and pytest are the lock's; nothing but the table's tools is asked a version."""
        self.run_gate()
        lines = self.log.read_text(encoding="utf-8").splitlines()
        for tool in ("ruff", "mypy", "pytest"):
            self.assertEqual([line for line in lines if tool in line and "version" in line.lower()], [], tool)
        self.assertEqual(sorted(self.asked()), sorted(ASKED))

    def test_a_changed_lock_runs_the_gate(self) -> None:
        """e16: a new ruff is a changed `uv.lock`, a covered file."""
        self.run_gate()
        self.forget_log()
        lock = self.repo / "apps/service/uv.lock"
        lock.write_text(lock.read_text(encoding="utf-8") + "# a newer ruff\n", encoding="utf-8")
        self.run_gate()
        self.assertTrue(self.checks())

    def test_a_changed_interpreter_in_the_environment_runs_the_gate(self) -> None:
        """e16: `version_info` in `pyvenv.cfg`, which git ignores and the sync does not rewrite."""
        self.run_gate()
        before = self.stamp()
        self.forget_log()
        cfg = self.repo / "apps/service/.venv/pyvenv.cfg"
        cfg.write_text(cfg.read_text(encoding="utf-8").replace("3.14.4", "3.14.5"), encoding="utf-8")
        run = self.run_gate()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertTrue(self.checks(), "no check started: the interpreter's version was not in the key")
        tools = self.stamp()["tools"]
        assert isinstance(tools, dict)
        self.assertEqual(tools["interpreter apps/service/.venv"], "3.14.5")
        self.assertNotEqual(self.stamp()["key"], before["key"])


class CannotAskTest(StampTestCase):
    def cannot(self, reason: str, env: dict[str, str | None] | None = None) -> None:
        """The full gate runs, one line before it names the cause, and a pass writes no stamp; exit 0."""
        run = self.run_gate(env)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertTrue(self.checks(), "no check started")
        self.assertTrue(run.stdout.endswith(f"{CLOSING}\n"))
        lines = self.reuse_lines(run)
        self.assertEqual(len(lines), 1, run.stdout[:400])
        self.assertIn(reason, lines[0])
        self.assertIn("records nothing", lines[0])
        self.assertTrue(run.stdout.startswith(lines[0] + "\n"), "the line is not the run's first")
        self.assertIsNone(self.stamp_path(), "a run that could not ask a tool recorded a stamp")

    def test_a_tool_that_is_not_on_the_path(self) -> None:
        """e17: a tool the table names that no directory of `PATH` has."""
        makefile = self.repo / "Makefile"
        asked = "VERIFY_STAMP := --tool no-such-tool-xyz"
        makefile.write_text(makefile.read_text(encoding="utf-8").replace("VERIFY_STAMP :=", asked), encoding="utf-8")
        self.cannot("no-such-tool-xyz")

    def test_a_tool_that_exits_non_zero(self) -> None:
        """e17."""
        self.cannot("uv", {"STANDIN_UV_MODE": "fail"})

    def test_a_tool_that_prints_nothing(self) -> None:
        """e17: blank lines are nothing."""
        self.cannot("uv", {"STANDIN_UV_MODE": "silent"})

    def test_a_tool_that_does_not_answer(self) -> None:
        """e17: the stand-in sleeps past the script's timeout; the cause is what is held, not the duration."""
        self.cannot("did not answer", {"STANDIN_UV_MODE": "hang"})

    def test_an_environment_with_no_pyvenv_cfg_records_nothing_and_the_next_run_does(self) -> None:
        """e17: a fresh clone has no environment yet; the sync makes one, and the second gate stamps."""
        (self.repo / "apps/service/.venv/pyvenv.cfg").unlink()
        self.cannot("pyvenv.cfg")
        self.forget_log()
        self.assertEqual(self.run_gate().returncode, 0)
        self.assertIsNotNone(self.stamp_path(), "the second gate recorded nothing either")
        self.forget_log()
        self.run_gate()
        self.assertEqual(self.checks(), [])

    def test_a_pyvenv_cfg_without_the_version_records_nothing(self) -> None:
        """e17: unreadable as what it must be."""
        (self.repo / "apps/service/.venv/pyvenv.cfg").write_text("home = /usr/bin\n", encoding="utf-8")
        self.cannot("pyvenv.cfg")
