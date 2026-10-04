"""R5 (AC-S03-14, -15, -16, -17): the key is the machine's tools.

The table of tools a machine supplies is data beside `BACKEND_TOOLING`; the recipe's `--tool` words come from it; the
script asks each once with its version argument and takes the first non-empty line, whole. Everything it asks is read
from the stand-ins' log. A tool it cannot ask is a reason on one line and a run that records nothing, never a failure.
"""
from __future__ import annotations

import re
import shutil
import unittest
from pathlib import Path

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

    def test_the_model_checks_add_node_and_npm_whatever_the_backend(self) -> None:
        """T031: `check-drawio` launches both, in a project with no TypeScript and no frontend."""
        everywhere = ["make", "git", "python3"]
        self.assertEqual(machine_tools(["python"], False, True), everywhere + ["uv", "node", "npm"])
        self.assertEqual(machine_tools(["go"], False, True), everywhere + ["go", "node", "npm"])
        self.assertEqual(machine_tools(["typescript"], True, True), everywhere + ["node", "npm"])

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
        self.assertRegex(str(tools["uv"]), r"^0\.12\.20 \[answer [0-9a-f]{16}\]$")
        self.assertIn("interpreter apps/service/.venv", tools)
        self.assertEqual(tools["interpreter apps/service/.venv"], "3.14.4")
        self.forget_log()
        self.run_gate()
        self.assertEqual(sorted(self.asked()), sorted(ASKED))
        self.assertEqual(self.checks(), [])

    def test_another_line_from_a_tool_runs_the_gate(self) -> None:
        """e15: a changed first line runs the gate and writes a new stamp."""
        self.assertEqual(self.run_gate().returncode, 0)
        before = self.stamp()["key"]
        self.forget_log()
        run = self.run_gate({"STANDIN_UV_VERSION": "\\n\\nuv 0.13.0 (another build)\\nsecond line"})
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertTrue(self.checks(), "no check started: the tool's new line was not in the key")
        stamp = self.stamp()
        tools = stamp["tools"]
        assert isinstance(tools, dict)
        self.assertTrue(str(tools["uv"]).startswith("0.13.0 [answer "), tools["uv"])
        self.assertNotEqual(stamp["key"], before)
        self.forget_log()
        self.run_gate({"STANDIN_UV_VERSION": "\\n\\nuv 0.13.0 (another build)\\nsecond line"})
        self.assertEqual(self.checks(), [], "the new stamp was not written")
        self.run_gate()
        self.assertTrue(self.checks(), "the first line came back and the other stamp was reused")

    def test_a_notice_ahead_of_the_version_does_not_hide_a_changed_version(self) -> None:
        """e15 (T026, D80): the key takes everything the tool printed, on both streams — a notice on its first line
        and the version on its second, here on the other stream, and a change of the version runs the gate."""
        notice: dict[str, str | None] = {"STANDIN_UV_NOTICE": "warning: something"}
        self.assertEqual(self.run_gate(notice).returncode, 0)
        self.forget_log()
        self.run_gate(notice)
        self.assertEqual(self.checks(), [], "the same answer was not reused")
        changed: list[dict[str, str | None]] = [
            {**notice, "STANDIN_UV_VERSION": "uv 0.99.0"},
            {"STANDIN_UV_NOTICE": "warning: something\\nuv 0.12.20", "STANDIN_UV_VERSION": "uv 0.99.0"},
        ]
        for env in changed:
            with self.subTest(str(env)):
                self.forget_log()
                self.run_gate(env)
                self.assertTrue(self.checks(), "a changed version behind a notice was reused")

    def test_a_changed_byte_on_the_second_line_of_standard_output_runs_the_gate(self) -> None:
        """e15 (T026): the same on one stream."""
        self.assertEqual(self.run_gate({"STANDIN_UV_VERSION": "uv 0.12.20\\nbuild 1"}).returncode, 0)
        self.forget_log()
        self.run_gate({"STANDIN_UV_VERSION": "uv 0.12.20\\nbuild 2"})
        self.assertTrue(self.checks(), "a changed second line was reused")

    def test_the_stamp_shows_the_version_words_of_either_stream_and_no_other_word(self) -> None:
        """e15 (T026, T033, D80): one line per tool, for a person: the version-shaped words, on either stream."""
        self.run_gate({"STANDIN_UV_NOTICE": "warning: something 9.9"})
        tools = self.stamp()["tools"]
        assert isinstance(tools, dict)
        self.assertRegex(str(tools["uv"]), r"^0\.12\.20 9\.9 \[answer [0-9a-f]{16}\]$")
        self.assertNotIn("warning", str(tools["uv"]))

    def test_no_file_under_the_git_directory_holds_a_path_a_tool_printed(self) -> None:
        """e15 (T026): a notice with a path on either stream and in the first line of standard output; the stamp and the
        note hold none of it."""
        printed: list[dict[str, str | None]] = [
            {"STANDIN_UV_NOTICE": "warning: cache at /home/someone/.cache/uv"},
            {"STANDIN_UV_VERSION": "warning: cache at /home/someone/.cache/uv\\nuv 0.12.20"},
            {"STANDIN_UV_VERSION": "Picked up JAVA_TOOL_OPTIONS: -Djava.io.tmpdir=/home/someone/tmp"},
        ]
        for env in printed:
            with self.subTest(str(env)):
                self.run_gate(env)
                for path in (self.repo / ".git" / "slipwai").iterdir():
                    self.assertNotIn("/home/someone", path.read_text(encoding="utf-8"), path.name)

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


JAVA = """#!/bin/sh
printf '%s\\t%s\\n' "{name}" "$*" >> "$STANDIN_LOG"
echo 'openjdk version "{version}"' >&2
"""


class TheJvmTheWrapperRunsTest(StampTestCase):
    """T032 (AC-S03-14, -17): `JAVA_HOME`'s JVM where that variable is non-empty, else the `java` on `PATH` — the one
    the Maven wrapper runs. The fixture is a Python project with `java` added to what its recipe asks."""

    def setUp(self) -> None:
        super().setUp()
        makefile = self.repo / "Makefile"
        text = makefile.read_text(encoding="utf-8").replace("VERIFY_STAMP :=", "VERIFY_STAMP := --tool java", 1)
        makefile.write_text(text, encoding="utf-8")
        self.install(self.bin, "path-java", "21.0.1")

    def install(self, directory: Path, name: str, version: str) -> Path:
        directory.mkdir(parents=True, exist_ok=True)
        java = directory / "java"
        java.write_text(JAVA.format(name=name, version=version), encoding="utf-8")
        java.chmod(0o755)
        return directory

    def home(self, name: str, version: str) -> str:
        return str(self.install(self.bin.parent / name / "bin", f"{name}-java", version).parent)

    def asked_java(self) -> list[str]:
        lines = self.log.read_text(encoding="utf-8").splitlines()
        return [line.split("\t")[0] for line in lines if line.endswith("\t-version")]

    def test_a_java_home_that_reports_another_version_than_the_one_on_the_path_runs_the_gate(self) -> None:
        self.assertEqual(self.run_gate().returncode, 0)
        self.forget_log()
        self.run_gate()
        self.assertEqual(self.checks(), [], "the same JVM was not reused")
        self.forget_log()
        other = self.home("jdk17", "17.0.9")
        self.run_gate({"JAVA_HOME": other})
        self.assertTrue(self.checks(), "a JAVA_HOME naming another JVM was reused")
        self.assertEqual(self.asked_java(), ["jdk17-java"], "the wrapper's JVM is the one asked, and only it")
        self.forget_log()
        self.run_gate({"JAVA_HOME": other})
        self.assertEqual(self.checks(), [], "the new stamp was not written")

    def test_an_empty_java_home_asks_the_one_on_the_path(self) -> None:
        self.run_gate({"JAVA_HOME": ""})
        self.assertEqual(self.asked_java(), ["path-java"])

    def test_the_value_of_java_home_is_in_neither_the_key_nor_the_stamp(self) -> None:
        """A directory with the same answer from another place is not a change; and no file holds the path."""
        first, second = self.home("jdk-a", "17.0.9"), self.home("jdk-b", "17.0.9")
        self.run_gate({"JAVA_HOME": first})
        key = self.stamp()["key"]
        self.forget_log()
        self.run_gate({"JAVA_HOME": second})
        self.assertEqual(self.checks(), [], "a moved directory with the same JVM ran the gate")
        self.assertEqual(self.stamp()["key"], key)
        for path in (self.repo / ".git" / "slipwai").iterdir():
            text = path.read_text(encoding="utf-8")
            for home in (first, second):
                self.assertNotIn(home, text, path.name)

    def test_a_java_home_whose_jvm_cannot_be_launched_is_the_case_of_a_tool_that_cannot_be_asked(self) -> None:
        """AC-S03-17: the full gate, one line naming java, no stamp — though `java` on `PATH` answers."""
        nowhere = self.bin.parent / "no-jdk"
        nowhere.mkdir()
        run = self.run_gate({"JAVA_HOME": str(nowhere)})
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertTrue(self.checks(), "no check started")
        lines = self.reuse_lines(run)
        self.assertEqual(len(lines), 1, run.stdout[:400])
        self.assertIn("java", lines[0])
        self.assertIn("records nothing", lines[0])
        self.assertNotIn(str(nowhere), lines[0])
        self.assertIsNone(self.stamp_path())
