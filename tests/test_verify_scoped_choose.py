"""R4 (AC-S06-2, -4, -7), the file inputs: a change selects the units that read it.

A unit runs when a changed path is one of its file inputs; every unit is named once, with the first path that chose it;
a unit that shares one recipe with a chosen unit runs with it. What ran is read from the stand-ins' log: the one `make`
call that names the units, and the `npm` calls those units make. The contracts are `test_verify_scoped_contracts`'s.
"""
from __future__ import annotations

import sys
import unittest

from scoped_fixture import ShapeCase

sys.dont_write_bytecode = True

NONE_CHANGED = "none of its inputs changed"
WEB_RUNS = {"lint-web", "typecheck-web", "test-web", "check-styles", "check-ux-gates", "check-imports",
            "check-migrations", "check-model"}
WEB_SKIPPED = {"lint-service", "typecheck-service", "test-service", "check-openapi", "check-drawio",
               "check-benchmark", "check-decisions"}


class TypescriptTest(ShapeCase):
    def test_e1_a_change_under_the_web_app_runs_what_reads_it_and_nothing_else(self) -> None:
        self.edit("apps/web/src/App.tsx")
        run = self.scoped()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        ran, skipped = self.decided(run)
        self.assertTrue(set(ran) >= WEB_RUNS, sorted(WEB_RUNS - set(ran)))
        self.assertTrue(set(skipped) >= WEB_SKIPPED, sorted(WEB_SKIPPED - set(skipped)))
        self.assertEqual({ran[unit] for unit in WEB_RUNS}, {"apps/web/src/App.tsx changed"})
        self.assertEqual({skipped[unit] for unit in WEB_SKIPPED}, {NONE_CHANGED})
        self.assertIn("run  lint-web — apps/web/src/App.tsx changed", self.lines(run))
        self.assertEqual(set(ran) & set(skipped), set(), "a unit was named twice")
        (goals,) = self.called()
        self.assertEqual(set(goals), set(ran), "the make call is not the chosen units")
        log = self.log.read_text(encoding="utf-8")
        self.assertIn("npm\t--workspace apps/web run lint", log)
        self.assertNotIn("apps/service", log, "a service unit ran for a change under the web app")

    def test_e1_every_unit_is_named_once_and_the_lines_follow_the_records_order(self) -> None:
        self.edit("apps/web/src/App.tsx")
        run = self.scoped()
        units = [line.partition(" — ")[0].split()[-1] for line in self.lines(run)]
        self.assertEqual(len(units), len(set(units)), units)
        self.assertEqual(units.index("lint-web") < units.index("typecheck-web") < units.index("test-web"), True)

    def test_e1_changed_paths_are_taken_in_sorted_order_so_the_first_names_the_unit(self) -> None:
        self.edit("apps/web/src/main.tsx")
        self.edit("apps/web/src/App.tsx")
        ran, _ = self.decided(self.scoped())
        self.assertEqual(ran["lint-web"], "apps/web/src/App.tsx changed")

    def test_e1_a_deletion_and_both_sides_of_a_rename_count_as_changed(self) -> None:
        (self.repo / "apps" / "web" / "src" / "App.tsx").rename(self.repo / "apps" / "service" / "src" / "Moved.tsx")
        ran, _ = self.decided(self.scoped({"STANDIN_DRY": "1"}))
        self.assertEqual(ran["lint-web"], "apps/web/src/App.tsx changed")
        self.assertEqual(ran["lint-service"], "apps/service/src/Moved.tsx changed")

    def test_e1_nothing_changed_is_nothing_run(self) -> None:
        run = self.scoped()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertEqual(self.decided(run)[0], {})
        self.assertEqual(self.called(), [])


class PinningFilesTest(ShapeCase):
    """E5: a file that pins a family's tools runs every unit that runs that family's tools, one example per file."""

    def assert_chosen(self, path: str, units: set[str]) -> None:
        self.reset()
        self.edit(path)
        ran, _ = self.decided(self.scoped({"STANDIN_DRY": "1"}))
        self.assertTrue(units <= set(ran), f"{path}: {sorted(units - set(ran))} did not run")
        self.assertEqual({ran[unit] for unit in units}, {f"{path} changed"}, path)

    def test_e5_the_npm_pins(self) -> None:
        units = {f"{gate}-{name}" for gate in ("lint", "typecheck", "test") for name in ("service", "web")}
        for path in (".nvmrc", "package-lock.json"):
            with self.subTest(path=path):
                self.assert_chosen(path, units)


class PythonTest(ShapeCase):
    shape = "two-python"

    def test_e4_a_python_service_changed_runs_all_six_and_names_the_shared_recipe(self) -> None:
        self.edit("apps/billing/src/billing/extra.py", "x = 1\n")
        ran, skipped = self.decided(self.scoped({"STANDIN_DRY": "1"}))
        for gate in ("lint", "typecheck", "test"):
            self.assertEqual(ran[f"{gate}-billing"], "apps/billing/src/billing/extra.py changed")
            self.assertEqual(ran[f"{gate}-service"], f"shares one recipe with {gate}-billing")
        self.assertNotIn("lint-service", skipped)

    def test_e5_the_python_pins(self) -> None:
        for path in ("apps/billing/uv.lock", "apps/billing/.python-version", "apps/billing/pyproject.toml"):
            with self.subTest(path=path):
                self.reset()
                self.edit(path)
                ran, _ = self.decided(self.scoped({"STANDIN_DRY": "1"}))
                self.assertEqual({ran[f"{gate}-billing"] for gate in ("lint", "typecheck", "test")},
                                 {f"{path} changed"})
                self.assertEqual(ran["test-service"], "shares one recipe with test-billing")


class JavaGoTest(ShapeCase):
    shape = "java-go"

    def test_e5_the_java_and_go_pins(self) -> None:
        for path, deployable in (("apps/service/pom.xml", "service"),
                                 ("apps/service/.mvn/wrapper/maven-wrapper.properties", "service"),
                                 ("apps/second/go.mod", "second"), ("apps/second/go.sum", "second")):
            with self.subTest(path=path):
                self.reset()
                self.edit(path)
                ran, skipped = self.decided(self.scoped({"STANDIN_DRY": "1"}))
                self.assertEqual({ran[f"{gate}-{deployable}"] for gate in ("lint", "typecheck", "test")},
                                 {f"{path} changed"})
                other = "second" if deployable == "service" else "service"
                self.assertTrue({f"{gate}-{other}" for gate in ("lint", "typecheck", "test")} <= set(skipped))


if __name__ == "__main__":
    unittest.main()
