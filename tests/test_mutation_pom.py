"""S08 T037 (A3, B8 two blocks; D138 item 3): every place PIT's configuration can change sweeps the service.

The pom's PIT configuration is every `pitest-maven` element in the document and the properties they reference, compared
base against tree; more than one such element is read as the sweep with its own words, never as the first. Real `git`,
the base commit holding the old pom; the tool is the recording `Runner` of `test_mutation_sweeps`.
"""
from __future__ import annotations

from test_mutation_scope_spring import POM, SWEEP, FakeExecute, SpringCase, params
from test_mutation_sweeps import SPRING, Recorded

JAVA = "apps/spring/src/main/java/com/example/x/A.java"
POM_PATH = "apps/spring/pom.xml"
PIT = POM.format(targets=params("com.example.x.*"), excluded="")
SECOND = ("<plugin><groupId>org.pitest</groupId><artifactId>pitest-maven</artifactId><configuration>"
          "<targetClasses><param>com.example.y.*</param></targetClasses></configuration></plugin>")
PROFILE = f"<profiles><profile><id>fast</id><build><plugins>{SECOND}</plugins></build></profile></profiles></project>"
READ = "<param>${pit.targets}</param></targetClasses>"
SET = ("<properties><pit.targets>com.example.x.*</pit.targets><pit.version>1.25.9</pit.version>"
       "<other>1</other></properties>")
PROPERTIES = (PIT.replace("<param>com.example.x.*</param></targetClasses>", READ)
              .replace("<groupId>org.pitest", "<version>${pit.version}</version><groupId>org.pitest")
              .replace("<build>", SET + "<build>"))


class PomTest(Recorded):
    def swept(self, text: str, base: str = PIT) -> tuple[list[str], list[str]]:
        """The pom changes from `base` to `text` beside a changed class: which services swept, and the lines said."""
        self.on_main(POM_PATH, text=base)
        self.write(JAVA, "package com.example.x;\n\npublic class A {}\n")
        self.write(POM_PATH, text)
        status, lines, recording = self.run_recording(SPRING)
        self.assertEqual(status, 0, lines)
        return recording.swept, lines

    def test_a_a_pitest_plugin_added_in_a_profile_or_a_second_one_sweeps_the_service(self) -> None:
        cases = {
            "a profile": PIT.replace("</project>", PROFILE),
            "pluginManagement": PIT.replace("<build>", f"<build><pluginManagement><plugins>{SECOND}</plugins>"
                                                      "</pluginManagement>"),
            "plugins": PIT.replace("</plugins>", f"{SECOND}</plugins>"),
        }
        for name, text in cases.items():
            with self.subTest(second=name):
                self.setUp()
                swept, lines = self.swept(text)
                self.assertEqual(swept, ["apps/spring"], lines)
                self.assertIn(f"mutation: sweep apps/spring — `{POM_PATH}` changed", lines)

    def test_a_a_change_to_a_property_the_block_reads_sweeps_and_an_unread_one_does_not(self) -> None:
        retargeted = PROPERTIES.replace("<pit.targets>com.example.x.*", "<pit.targets>com.example.y.*")
        changes = (("targets", retargeted, True),
                   ("version", PROPERTIES.replace("1.25.9", "1.26.0"), True),
                   ("unread", PROPERTIES.replace("<other>1<", "<other>2<"), False))
        for name, text, sweeps in changes:
            with self.subTest(property=name):
                self.setUp()
                swept, lines = self.base_properties(text)
                self.assertEqual(swept == ["apps/spring"], sweeps, lines)

    def base_properties(self, text: str) -> tuple[list[str], list[str]]:
        self.on_main(POM_PATH, text=PROPERTIES)
        self.write(JAVA, "package com.example.x;\n\npublic class A {}\n")
        self.write(POM_PATH, text)
        _, lines, recording = self.run_recording(SPRING)
        return recording.swept, lines

    def test_b_a_pom_already_holding_two_pitest_elements_sweeps_with_its_own_words_never_reads_the_first(self) -> None:
        self.write(POM_PATH, PIT.replace("</plugins>", f"{SECOND}</plugins>"))
        self.write(JAVA, "package com.example.x;\n\npublic class A {}\n")
        execute = FakeExecute()
        status, lines = SpringCase.run_spring(self, execute)  # type: ignore[arg-type]
        self.assertEqual((status, execute.seen), (0, [(SWEEP, "apps/spring")]), lines)
        self.assertTrue(lines[0].startswith(f"mutation: the sweep runs — {POM_PATH}: the pom has more than one "
                                            "pitest-maven plugin"), lines)
