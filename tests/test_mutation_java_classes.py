"""S08 T036 (D138 item 1, A1, A2, B4, B8 Kotlin): Spring hands PIT the classes a changed file declares.

The file-to-class mapping reads the file's `package` line and every top-level type it declares, and each class is
decided against the pom's `targetClasses` and `excludedClasses` with PIT's own glob rule, `Foo$*` included. A file
the reader cannot map with certainty sweeps the service, with words naming the file. The tool is the fake `execute`
of `test_mutation_scope_spring`; the pom and the sources are real files in the project.
"""
from __future__ import annotations

from test_mutation_scope_spring import PACKAGE, SWEEP, FakeExecute, SpringCase

MAIN = f"apps/spring/src/main/java/{PACKAGE}"
PREFIX = "com.example.x.a."


class JavaClassesTest(SpringCase):
    def source(self, path: str, text: str) -> None:
        self.write(f"apps/spring/src/main/{path}", text)

    def classes(self, execute: FakeExecute) -> list[str]:
        """The `-DtargetClasses` words PIT was handed, one per class, or an empty list where Maven did not start."""
        if not execute.seen:
            return []
        word = [word for word in execute.seen[0][0] if word.startswith("-DtargetClasses=")][0]
        return word.split("=", 1)[1].split(",")

    def test_a_a_second_top_level_class_in_a_changed_file_is_a_target_too(self) -> None:
        self.pom(("com.example.x.*",))
        self.source(f"java/{PACKAGE}/a/Foo.java", "package com.example.x.a;\n\npublic class Foo {}\n\nclass Helper {}\n"
                    "interface Port {}\nenum Mode { A }\nrecord Pair(int a) {}\n@interface Marker {}\n")
        execute = FakeExecute()
        status, _ = self.run_spring(execute)
        self.assertEqual(status, 0)
        names = ("Foo", "Helper", "Port", "Mode", "Pair", "Marker")
        self.assertEqual(self.classes(execute), [c for n in names for c in (PREFIX + n, PREFIX + n + "$*")])

    def test_a_what_is_not_a_top_level_declaration_is_not_a_class(self) -> None:
        self.pom(("com.example.x.*",))
        self.source(f"java/{PACKAGE}/a/Foo.java", 'package com.example.x.a;\n// class Fake {}\n/* class Other {} */\n'
                    '@Anno(Foo.class)\npublic final class Foo<T extends Comparable<T>> {\n  class Inner {}\n'
                    '  String s = "class Quoted {}";\n  String t = """\n  class Block {}\n  """;\n'
                    "  char c = '{';\n}\n")
        execute = FakeExecute()
        self.run_spring(execute)
        self.assertEqual(self.classes(execute), ["com.example.x.a.Foo", "com.example.x.a.Foo$*"])

    def test_b_a_package_that_differs_from_the_directory_is_the_declared_package(self) -> None:
        self.source(f"java/{PACKAGE}/health/Moved.java", "package com.example.x.other;\n\npublic class Moved {}\n")
        for targets, taken in ((("com.example.x.other.*",), True), (("com.example.x.health.*",), False)):
            with self.subTest(targets=targets):
                self.pom(targets)
                execute = FakeExecute()
                _, lines = self.run_spring(execute)
                if taken:
                    moved = "com.example.x.other.Moved"
                    self.assertEqual(self.classes(execute), [moved, moved + "$*"])
                else:
                    self.assertEqual(execute.seen, [])
                    self.assertTrue(lines[0].startswith("mutation: no mutant to run — every changed"), lines)
                    self.assertIn("mutation: not mutated apps/spring/src/main/java/com/example/x/health/Moved.java"
                                  " — outside PIT's configured targets", lines)

    def test_b_a_file_in_the_default_package_is_its_bare_name(self) -> None:
        self.pom(("Top",))
        self.source("java/Top.java", "public class Top {}\n")
        execute = FakeExecute()
        self.run_spring(execute)
        self.assertEqual(self.classes(execute), ["Top", "Top$*"])

    def test_c_a_nested_class_of_an_exactly_excluded_class_is_still_targeted(self) -> None:
        self.source(f"java/{PACKAGE}/a/Foo.java", "package com.example.x.a;\n\npublic class Foo { class In {} }\n")
        cases = (("com.example.x.a.Foo", True), ("com.example.x.a.Foo*", False), ("com.example.x.a.*", False))
        for excluded, taken in cases:
            with self.subTest(excluded=excluded):
                self.pom(("com.example.x.*",), (excluded,))
                execute = FakeExecute()
                self.run_spring(execute)
                wanted = ["com.example.x.a.Foo", "com.example.x.a.Foo$*"]
                self.assertEqual(self.classes(execute), wanted if taken else [])

    def test_c_each_class_of_a_file_is_decided_on_its_own(self) -> None:
        self.pom(("com.example.x.*",), ("com.example.x.a.Wiring*",))
        self.source(f"java/{PACKAGE}/a/Foo.java", "package com.example.x.a;\nclass Foo {}\nclass WiringConfig {}\n")
        execute = FakeExecute()
        self.run_spring(execute)
        self.assertEqual(self.classes(execute), ["com.example.x.a.Foo", "com.example.x.a.Foo$*"])

    def test_d_a_jvm_source_other_than_java_sweeps_the_service_naming_the_file(self) -> None:
        self.pom(("com.example.x.*",))
        for path in ("kotlin/com/example/x/A.kt", "groovy/com/example/x/A.groovy", "scala/com/example/x/A.scala"):
            with self.subTest(path=path):
                self.source(path, "package com.example.x\n")
                execute = FakeExecute()
                status, lines = self.run_spring(execute)
                named = f"`apps/spring/src/main/{path}` changed"
                self.assertEqual(lines[0], f"mutation: the sweep runs — {named}", lines)
                self.assertIn(f"mutation: sweep apps/spring — {named}", lines)
                self.assertEqual((status, execute.seen), (0, [(SWEEP, "apps/spring")]))
                self.assertNotIn("mutation: no mutant to run — no production file changed", lines)
                (self.repo / f"apps/spring/src/main/{path}").unlink()

    def test_d_a_java_file_with_no_readable_declaration_sweeps_naming_the_file(self) -> None:
        self.pom(("com.example.x.*",))
        for text in ("package com.example.x.a;\n", "package com.example.x.a;\npublic class Broken {\n", "\u0000"):
            with self.subTest(text=text[:30]):
                self.source(f"java/{PACKAGE}/a/Broken.java", text)
                execute = FakeExecute()
                _, lines = self.run_spring(execute)
                self.assertTrue(lines[0].startswith(f"mutation: the sweep runs — {MAIN}/a/Broken.java: "), lines)
                self.assertEqual(execute.seen, [(SWEEP, "apps/spring")])
