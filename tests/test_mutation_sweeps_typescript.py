"""S41 T008 (rule 6 · AC-S41-6): what sweeps a TypeScript service, with real `git` and the base holding the old files.

The tool is `test_mutation_scope_typescript`'s recording `Runner`, which says whether a service was asked for a scope
or a sweep. A change no scope can be trusted across names its file and sweeps the service; a change that cannot be
told apart from a harmless one sweeps too, and a harmless one does not.
"""
from __future__ import annotations

import json
import sys

from mutation_scope_fixture import SLICE
from stamp_fixture import git
from test_mutation_borders import clean_environment
from test_mutation_scope_typescript import GO_AND, HEALTH, TWO, TypeScriptCase

sys.dont_write_bytecode = True
CORE, RUNNER = "@stryker-mutator/core", "@stryker-mutator/vitest-runner"
DEV = {CORE: "10.0.0", RUNNER: "10.0.0", "vitest": "4.1.11"}
MANIFEST = {"scripts": {"test": "vitest run"}, "devDependencies": DEV}
LOCK = {"packages": {"": {}, f"node_modules/{CORE}": {"version": "10.0.0"},
                     f"node_modules/{RUNNER}": {"version": "10.0.0"}, "node_modules/vitest": {"version": "4.1.11"}}}
CONFIG = "apps/service/stryker.config.json"
MANIFEST_PATH = "apps/service/package.json"
THIRD = (*TWO, "typescript:apps/third")


def text(document: object, **style: int) -> str:
    return json.dumps(document, **style) + "\n"  # type: ignore[arg-type]


class SweepsTypeScriptTest(TypeScriptCase):
    def setUp(self) -> None:
        super().setUp()
        self.on_main(MANIFEST_PATH, text=text(MANIFEST, indent=2))
        self.on_main("package-lock.json", text=text(LOCK, indent=2))

    def edit(self, name: str) -> None:
        path = self.repo / name
        path.write_text(path.read_text(encoding="utf-8") + "\n# e\n", encoding="utf-8")

    def swept(self, *services: str, env: dict[str, str] | None = None) -> tuple[list[str], list[str], list[str]]:
        """(the services swept, the files scoped by `service/file`, the lines) of one run."""
        status, lines, recording = self.run_planned(*services, env=env)
        self.assertEqual(status, 0, lines)
        return recording.swept, [f"{path}/{name}" for path, names in recording.scoped for name in names], lines

    def test_e1_a_changed_added_or_deleted_config_sweeps_that_service_only(self) -> None:
        self.write("apps/second/src/b.ts", "export const b = 1;\n")
        for change in ("edit", "delete", "add"):
            with self.subTest(change=change):
                git(self.repo, "checkout", "-q", "--", ".")
                git(self.repo, "clean", "-qfd", "apps/third")
                if change == "edit":
                    self.write(CONFIG, text({"mutate": ["src/**/*.ts"]}))
                elif change == "delete":
                    (self.repo / CONFIG).unlink()
                else:
                    self.write("apps/third/stryker.config.json", text({"mutate": ["src/**/*.ts"]}))
                target = "apps/third" if change == "add" else "apps/service"
                swept, scoped, lines = self.swept(*THIRD)
                self.assertEqual(swept, [target], lines)
                self.assertIn(f"mutation: sweep {target} — `{target}/stryker.config.json` changed", lines)
                self.assertEqual(scoped, ["apps/second/src/b.ts"])

    def test_e1_a_go_service_beside_is_not_swept_by_a_typescript_config(self) -> None:
        self.write("apps/second/stryker.config.json", text({"mutate": ["src/**/*.ts"]}))
        self.write("apps/service/domain/x.go", "package domain\n")
        swept, scoped, _ = self.swept(*GO_AND)
        self.assertEqual((swept, scoped), (["apps/second"], ["apps/service/domain/x.go"]))

    def test_e2_the_wrapper_changing_sweeps_every_typescript_service_and_not_a_go_one(self) -> None:
        self.edit("scripts/stryker-mutation.py")
        swept, _, lines = self.swept(*THIRD)
        self.assertEqual(sorted(swept), ["apps/second", "apps/service", "apps/third"], lines)
        self.assertIn("mutation: sweep apps/service — `scripts/stryker-mutation.py` changed", lines)
        swept, _, _ = self.swept(*GO_AND)
        self.assertEqual(swept, ["apps/second"])

    def test_e2_hold_go_mutation_py_changing_sweeps_no_typescript_service(self) -> None:
        self.edit("scripts/go-mutation.py")
        swept, _, lines = self.swept(*TWO)
        self.assertEqual(swept, [], lines)

    def test_e3_a_stryker_version_moving_in_the_manifest_sweeps_that_service_only(self) -> None:
        self.write(MANIFEST_PATH, text({**MANIFEST, "devDependencies": {**DEV, CORE: "10.0.1"}}))
        swept, _, lines = self.swept(*TWO)
        self.assertEqual(swept, ["apps/service"], lines)
        self.assertIn(f"mutation: sweep apps/service — `{MANIFEST_PATH}` changed", lines)

    def test_e3_the_root_lock_deleted_on_the_branch_sweeps_every_typescript_service(self) -> None:
        """T024: a side that is gone is a version change (`stryker_versions_moved`), not an unreadable-nothing."""
        (self.repo / "package-lock.json").unlink()
        swept, _, lines = self.swept(*TWO)
        self.assertEqual(sorted(swept), ["apps/second", "apps/service"], lines)
        self.assertIn("mutation: sweep apps/service — `package-lock.json` changed", lines)

    def test_e3_hold_nothing_that_is_not_a_stryker_version_sweeps(self) -> None:
        """HOLD (teeth: compare the raw text of the manifest and see the first three sweep)."""
        self.write("apps/service/src/health.ts", "export const a = 1;\n")
        reordered = {"devDependencies": dict(reversed(list(DEV.items()))),
                     "scripts": MANIFEST["scripts"]}
        other = {**MANIFEST, "devDependencies": {**DEV, "vitest": "4.2.0"}}
        scripted = {**MANIFEST, "scripts": {"test": "vitest run --coverage"}}
        for name, content in (("key order and indent", text(reordered, indent=4)), ("another package", text(other)),
                              ("a script", text(scripted)), ("scripts/ elsewhere", None)):
            with self.subTest(change=name):
                if content is None:
                    self.write("scripts/other.py", "x = 1\n")
                else:
                    self.write(MANIFEST_PATH, content)
                swept, scoped, lines = self.swept(*TWO)
                self.assertEqual((swept, scoped), ([], ["apps/service/src/health.ts"]), lines)

    def test_e3_a_manifest_that_does_not_parse_on_either_side_sweeps_naming_the_file(self) -> None:
        self.write(MANIFEST_PATH, "{not json")
        swept, _, lines = self.swept(*TWO)
        self.assertEqual(swept, ["apps/service"])
        self.assertIn(f"mutation: sweep apps/service — `{MANIFEST_PATH}` changed", lines)
        self.on_main(MANIFEST_PATH, text="{not json")
        self.write(MANIFEST_PATH, text(MANIFEST))
        swept, _, _ = self.swept(*TWO)
        self.assertEqual(swept, ["apps/service"])

    def test_e3_the_root_lock_moving_a_stryker_entry_sweeps_every_typescript_service(self) -> None:
        moved = {"packages": {**LOCK["packages"], f"node_modules/{RUNNER}": {"version": "10.0.1"}}}
        unrelated = {"packages": {**LOCK["packages"], "node_modules/vitest": {"version": "4.2.0"}}}
        for name, content, sweeps in (("a stryker entry", text(moved), True),
                                      ("an unrelated entry", text(unrelated), False),
                                      ("a lock that does not parse", "{nope", True)):
            with self.subTest(change=name):
                self.write("package-lock.json", content)
                swept, _, lines = self.swept(*TWO)
                self.assertEqual(sorted(swept), ["apps/second", "apps/service"] if sweeps else [], lines)
                self.assertEqual(sweeps, "mutation: sweep apps/service — `package-lock.json` changed" in lines, lines)

    def test_e3_either_copy_of_a_stryker_package_in_the_lock_moving_sweeps(self) -> None:
        """T023: a nested copy beside a hoisted one at another version; only the nested, or only the hoisted, moves."""
        nested = f"node_modules/{CORE}/node_modules/@stryker-mutator/util"

        def lock(hoisted: str, copy: str) -> str:
            packages = {**LOCK["packages"], "node_modules/@stryker-mutator/util": {"version": hoisted},
                        nested: {"version": copy}}
            return text({"packages": packages})

        self.on_main("package-lock.json", text=lock("10.0.0", "9.0.0"))
        for name, content, sweeps in (("only the nested copy", lock("10.0.0", "9.1.0"), True),
                                      ("only the hoisted copy", lock("10.0.1", "9.0.0"), True),
                                      ("neither", lock("10.0.0", "9.0.0"), False)):
            with self.subTest(change=name):
                self.write("package-lock.json", content)
                swept, _, lines = self.swept(*TWO)
                self.assertEqual(sorted(swept), ["apps/second", "apps/service"] if sweeps else [], lines)

    def test_e4_a_list_the_script_cannot_read_sweeps_naming_the_config_changed_or_not(self) -> None:
        bad = ({"mutate": ["src/**/*.{ts,tsx}"]}, {"other": 1}, None)
        for content in bad:
            with self.subTest(config=content):
                self.on_main(CONFIG, text="{not json" if content is None else text(content))
                self.write(HEALTH, "export const a = 1;\n")  # the config is unchanged since the base
                swept, scoped, lines = self.swept(*TWO)
                self.assertEqual((swept, scoped), (["apps/service"], []), lines)
                self.assertTrue([line for line in lines if line.startswith("mutation: sweep apps/service — ")
                                 and "apps/service/stryker.config.json" in line], lines)
                self.write(CONFIG, text({"mutate": ["src/**/*.{ts,tsx}"]}))  # and changed: still named
                swept, _, lines = self.swept(*TWO)
                self.assertEqual(swept, ["apps/service"], lines)
                self.reset()

    def test_e5_hold_an_ignored_file_under_src_sweeps_that_service(self) -> None:
        """HOLD (teeth: take TypeScript out of `PRODUCTION_ROOT` and see it fail)."""
        ignores = (self.repo / ".gitignore").read_text(encoding="utf-8")
        self.on_main(".gitignore", text=ignores + "apps/service/src/gen/\n")
        self.write("apps/service/src/gen/x.ts", "export const g = 1;\n")
        swept, _, lines = self.swept(*TWO)
        self.assertEqual(swept, ["apps/service"], lines)
        self.assertTrue([line for line in lines if "apps/service/src/gen" in line and "ignores" in line], lines)

    def test_e6_two_causes_in_one_service_sweep_it_once_naming_the_config(self) -> None:
        self.write(CONFIG, text({"mutate": ["src/**/*.ts"]}))
        self.write(HEALTH, "export const a = 1;\n")
        swept, scoped, lines = self.swept(*TWO)
        self.assertEqual((swept, scoped), (["apps/service"], []), lines)
        sweeps = [line for line in lines if line.startswith("mutation: sweep apps/service — ")]
        self.assertEqual(len(sweeps), 1, lines)
        self.assertIn(f"`{CONFIG}` changed", sweeps[0])

    def test_e6_since_sweeps_on_the_same_triggers(self) -> None:
        self.fit_recipe(TWO)
        self.write(CONFIG, text({"mutate": ["src/**/*.ts"]}))
        self.commit("config")
        swept, _, lines = self.swept(*TWO, env={**clean_environment(), "SINCE": "HEAD~1"})
        self.assertEqual(swept, ["apps/service"], lines)

    def test_t045_a_swept_service_that_is_gone_opens_with_the_refusal_not_a_sweep(self) -> None:
        """B5: `git rm -r apps/second` with the Makefile unchanged: the first line must not promise a sweep."""
        git(self.repo, "rm", "-rq", "apps/second")
        status, lines, recording = self.run_planned(*TWO, directories=True)
        self.assertEqual(status, 2, lines)
        self.assertEqual(lines[0], "mutation: refusing apps/second — its directory does not exist, so nothing is swept")
        self.assertFalse([line for line in lines if "the sweep runs" in line], lines)
        self.assertTrue([line for line in lines if line.startswith("mutation: refuse apps/second — ")], lines)
        self.assertEqual((recording.swept, recording.scoped), ([], []))

    def test_t045_hold_another_service_still_sweeping_keeps_the_sweep_line_without_the_gone_one(self) -> None:
        git(self.repo, "rm", "-rq", "apps/second")
        self.write(CONFIG, text({"mutate": ["src/**/*.ts"]}))
        status, lines, recording = self.run_planned(*TWO, directories=True)
        self.assertEqual(status, 2, lines)
        self.assertTrue(lines[0].startswith("mutation: the sweep runs — "), lines)
        self.assertIn(CONFIG, lines[0])
        self.assertNotIn("apps/second", lines[0])
        self.assertEqual(recording.swept, ["apps/service"])

    def reset(self) -> None:
        super().reset()
        git(self.repo, "checkout", "-q", "-B", SLICE, "main")
