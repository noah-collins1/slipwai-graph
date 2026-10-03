# Research — S20-slice-scope-root

- **R-1 — Why the root path owns nothing today.** Decision: fix in `Scope.owning_app()`. Read from
  `assets/toolkit/scripts/check-slice-scope.py:213–219`: the test is `path == app_path or
  path.startswith(app_path + "/")` with `app_path = record["path"].strip("/")`; git never reports a path equal
  to `.` or starting `./`. `"./".strip("/")` is `.`, so one comparison covers both spellings. Alternatives:
  normalising `project.json` at adoption — changes a recorded answer, not a PATCH.
- **R-2 — The host surface.** Decision: D18 as written (fixed floor, `.written` adds). `.written` is one path
  per line relative to the repository root (`delivery/.written` here: 289 lines, including
  `.github/workflows/verify-delivery.yml`, `.specify/…`, `project.json`); `src/slipwai/survey.py:177–180` reads it
  from `<delivery>/.written`, or `.written` where delivery is the root. Alternatives considered in D18.
- **R-3 — Delivery at the root with a deployable at the root.** Decision: where `DELIVERY` is `.` the
  delivery-directory clause cannot apply (it would be every path) and is skipped; the fixed names and
  `.written` hold. *Assumed*: no generated project records a deployable at `.` (generated deployables sit under
  `apps/`); the case is covered so the checker is defined there, and is not among the slice's examples.
- **R-4 — How a root-adopted repository is made in a test.** Decision: `tests/test_adopt.py` `repository()`
  (line 45) and `slipwai()` (line 34), then `adopt --yes`, as `tests/test_adopt_next.py:89` does; commit on
  `main`, branch `slice/S1`, run `python3 delivery/scripts/check-slice-scope.py` with `GITHUB_HEAD_REF` and
  `CI_COMMIT_REF_NAME` emptied, as `SliceScopeGateTest.check` does. To be confirmed by the first RED: that the
  adopted tree carries `delivery/scripts/check-slice-scope.py` and records the deployable at `.`
  (this repository's `delivery/.written` line 75 and `project.json` say an adoption does).
- **R-5 — The id's alphabet.** Decision: `[A-Za-z]+\d+[A-Za-z0-9._-]*`, anchored at the start of the first cell
  after backticks are stripped. Read from `check-slice-scope.py:77` (`SLICE_BRANCH`) for the tail and from
  `check-decisions.py:184`, `agents/benchmark.py:633` for today's head. The adversary log's row pattern
  `^## (\S+) · ` (`check-decisions.py`, `check_adversary_rows`) already takes a slug.
- **R-6 — The level.** Decision: PATCH, `VERSION` stays `1.5.2.dev0`. AGENTS.md: a release opens the next number
  as a PATCH over an empty `changelog.d/`; `changelog.d/` holds only its README today; `tests/test_changelog.py`
  holds the pairing.
