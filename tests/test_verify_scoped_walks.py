"""T024 (R4, R10 e4 · AC-S06-2, -5, -6, -13): a check's row is as wide as what the check walks and what its data names.

A check that walks every `apps/*/` and `packages/*/`, or that requires every path the model names to exist, is chosen
when any of those paths changes, whichever other row claims the path. A row narrower than the read is a check skipped
where `make verify` runs it and it fails. Generated projects are the scoped fixture's; the model's paths come from the
record the project's own script prints.
"""
from __future__ import annotations

import sys

from scoped_fixture import LINE, ShapeCase
from stamp_fixture import git
from test_scoped_targets import SHAPES
from test_verify_scoped_record import EVENT_MODEL, RecordCase, covered, loaded, record

sys.dont_write_bytecode = True

DRY: dict[str, str | None] = {"STANDIN_DRY": "1"}
MODEL = """slices:
  - id: S1
    name: Place an order
    pattern: state-change
    status: implemented
    actor: Customer
    service: service
    stream: order-{orderId}
    gwt: specs/001-ordering/slices/S1.md
    code:
      - apps/service/src/main.ts
    frames:
      - type: ui
        name: Order form
        mockups:
          - state: empty
            at: docs/event-model/mocks/order-empty.html
      - type: cmd
        name: PlaceOrder
      - type: evt
        name: OrderPlaced
"""


class WalksTest(ShapeCase):
    shape = "model-typescript-web"

    def test_e1_a_migration_in_a_package_is_read_by_check_migrations(self) -> None:
        self.edit("packages/api-client/migrations/202610051200_drop.sql", "ALTER TABLE orders DROP COLUMN status;\n")
        ran, skipped = self.decided(self.scoped(env=DRY))
        self.assertEqual(ran.get("check-migrations"), "packages/api-client/migrations/202610051200_drop.sql changed")
        self.assertNotIn("check-migrations", skipped)

    def implemented(self, model_text: str) -> None:
        """`main` holds an implemented slice whose evidence exists; the branch is cut from it, with a baseline."""
        model = self.repo / EVENT_MODEL
        model.write_text(model.read_text(encoding="utf-8").replace("slices: []\n", model_text), encoding="utf-8")
        self.edit("specs/001-ordering/slices/S1.md", "# S1\n")
        git(self.repo, "checkout", "-q", "main")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "S1 implemented")
        git(self.repo, "checkout", "-q", "-B", "slice/S1")
        self.write_baseline()

    def test_e2_a_path_the_model_names_moves_and_check_model_runs(self) -> None:
        self.implemented(MODEL)
        git(self.repo, "rm", "-q", "specs/001-ordering/slices/S1.md")
        self.edit("specs/001-ordering/slices/S1-moved.md", "# S1\n")
        ran, skipped = self.decided(self.scoped(env=DRY))
        self.assertEqual(ran.get("check-model"), "specs/001-ordering/slices/S1.md changed")
        self.assertNotIn("check-model", skipped)

    def test_e2_a_directory_the_model_names_is_read_through(self) -> None:
        self.implemented(MODEL.replace("specs/001-ordering/slices/S1.md", "specs/001-ordering/slices"))
        git(self.repo, "rm", "-q", "-r", "specs/001-ordering/slices")
        ran, _ = self.decided(self.scoped(env=DRY))
        self.assertEqual(ran.get("check-model"), "specs/001-ordering/slices/S1.md changed")


class CloudWalksTest(ShapeCase):
    shape = "model-typescript-web-cloud"

    def test_e3_a_package_without_a_package_json_is_read_by_check_imports(self) -> None:
        """Another row (`check-flags`) names `packages/`; `check-imports` walks it, and is never skipped for it: the
        path is one no deployable or contract consumes, so what runs is the full gate, `check-imports` with it."""
        self.edit("packages/shared/src/domain/x.ts", "export const x = 1;\n")
        run = self.scoped(env=DRY)
        ran, skipped = self.decided(run)
        self.assertNotIn("check-imports", skipped)
        self.assertIn(LINE + "dependency knowledge was incomplete for packages/shared/src/domain/x.ts — "
                      "no deployable, contract or check claims it", self.scoped_lines(run))
        self.assertEqual(len(self.verify_calls()), 1)


class NamedByTheModelTest(RecordCase):
    def test_e2_every_path_the_model_names_is_an_input_of_check_model(self) -> None:
        project = self.project("model-typescript-web")
        (project / EVENT_MODEL).write_text(MODEL, encoding="utf-8")
        files = loaded(project)["checks"]["check-model"]["inputs"]["files"]
        for named in ("specs/001-ordering/slices/S1.md", "apps/service/src/main.ts",
                      "docs/event-model/mocks/order-empty.html"):
            self.assertTrue(any(entry == named or entry == named + "/" for entry in files), (named, files))


# What a check reads from `project.json`: the paths of these deployables, whatever directory they are in.
LISTED = {"check-imports": ("service", "web"), "check-flags": ("service", "web"), "check-model": ("service", "web"),
          "check-styles": ("web",), "check-ux-gates": ("web",)}


class ListedByProjectJsonTest(RecordCase):
    def test_e4_every_path_project_json_lists_for_a_check_is_one_of_its_inputs(self) -> None:
        held = 0
        for shape in SHAPES:
            project = self.project(shape)
            if record(project).returncode != 0:
                continue
            data = loaded(project)
            for name, kinds in LISTED.items():
                if name not in data["checks"]:
                    continue
                for deployable, item in data["deployables"].items():
                    if item["kind"] in kinds:
                        held += 1
                        self.assertTrue(covered(item["path"] + "/", data["checks"][name]["inputs"]["files"]),
                                        (shape, name, deployable))
        self.assertGreater(held, 20)
