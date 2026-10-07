# Data model: S43-test-declarations

- **Literal launcher argv** (`scripts/select_tests/argv.py`): an `ast.List` whose first element is `ROOT / "slipwai"` (or
  `str(ROOT / "slipwai")`), second the literal `"generate"`, and every other element a string literal except the name
  positional and `--output`'s value. Read as `{backend, profile, frontend, target} → frozenset | None` (None: every
  option): `--backend`→backend, `--profile`, `--frontend`, `--target` as named; the catalog's `axes` flags take one literal
  value and answer no declared axis; `--output <any>` and `--skip-checks` nothing; an omitted axis flag every option; any
  other element → the list is not read and stays a route (every option of every axis).
- **`Call`** (unchanged shape, `generation.Call`): a read argv is one, at the list's line; D164 rule 2 holds it to the
  declaration as it holds a `generate(` call.
- **Selected set**: `SELECTED_TEST_MODULES`, comma-separated module names, set by `scripts/select-tests.py` on the
  modules it starts in a selected run, removed for a full run. Absent → the audit covers every reads-only declared
  module; present → the declared reads-only modules in it.
- **`real_*` list for S43** (`tests/test_select_tests_real_s43.py`): `DECLARED` (modules) and `HELPERS` (helpers) this
  slice declared; `test_select_tests_real_declared` unions it with the others.
- **Undeclared list** (`undeclared.md`): one row per `test_*` module `tree.effective` leaves None — module, reason.
