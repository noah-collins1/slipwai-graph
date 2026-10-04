"""R5 (AC-S03-18), T033: what the stamp stores of a tool's answer.

Per tool its name, the version-shaped words of its answer (digits and dots with a short suffix, nothing else) and a
digest of the whole answer — the digest alone where no such word is found. Whatever else a tool printed (a path, a
host name, a user name) is in no file under the git directory, and the key still takes the whole answer (D80).
"""
from __future__ import annotations

import re

from stamp_fixture import StampTestCase

# What a tool may print as its first line: (what the stand-in prints, the words that must be in no stored file).
# Backslashes are doubled once, for the stand-in's `printf %b`.
PRINTED = (
    ("uv 0.12.20 cache at C:\\\\Program Files\\\\uv\\\\cache", ("Program Files", "cache at")),
    ("uv 0.12.20 home=~noah/.cache", ("noah", ".cache")),
    ("uv 0.12.20 config,/home/noah/x", ("noah", "config")),
    ("uv 0.12.20 built on ci-host-7.corp.example.com by noah (pid 4242)", ("ci-host", "corp.example", "noah", "4242")),
)
STORED = re.compile(r"^(?:[0-9][0-9.]*(?: [0-9][0-9.]*)* )?\[answer [0-9a-f]{16}\]$")


class WhatIsStoredTest(StampTestCase):
    def stored_text(self) -> str:
        directory = self.repo / ".git" / "slipwai"
        return "\n".join(path.read_text(encoding="utf-8") for path in sorted(directory.iterdir()))

    def test_no_file_under_the_stamps_directory_holds_a_word_a_tool_printed_beyond_its_version(self) -> None:
        for printed, words in PRINTED:
            with self.subTest(printed=printed):
                self.run_gate({"STANDIN_UV_VERSION": printed})
                text = self.stored_text()
                for word in words:
                    self.assertNotIn(word, text)

    def test_a_tool_is_stored_as_its_version_words_and_the_digest_of_its_answer(self) -> None:
        self.run_gate({"STANDIN_UV_VERSION": "uv 0.12.20 (stand-in) build 7"})
        tools = self.stamp()["tools"]
        assert isinstance(tools, dict)
        self.assertRegex(str(tools["uv"]), r"^0\.12\.20 \[answer [0-9a-f]{16}\]$")
        for name in ("make", "git", "python3"):
            self.assertRegex(str(tools[name]), STORED, name)

    def test_the_digest_alone_is_stored_where_no_word_is_version_shaped(self) -> None:
        self.run_gate({"STANDIN_UV_VERSION": "uv from a build of the day"})
        tools = self.stamp()["tools"]
        assert isinstance(tools, dict)
        self.assertRegex(str(tools["uv"]), r"^\[answer [0-9a-f]{16}\]$")

    def test_the_key_takes_the_whole_answer_so_a_changed_word_that_is_not_stored_runs_the_gate(self) -> None:
        """D80: only what is shown is narrowed."""
        self.run_gate({"STANDIN_UV_VERSION": "uv 0.12.20 build 7"})
        before = self.stamp()["key"]
        self.forget_log()
        self.run_gate({"STANDIN_UV_VERSION": "uv 0.12.20 build 8"})
        self.assertTrue(self.checks(), "a changed word of the answer was reused")
        self.assertNotEqual(self.stamp()["key"], before)
