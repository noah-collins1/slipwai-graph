# Research: S43-test-declarations — what the measured run says declarations can save

**Inputs:** [runtime-table.md](runtime-table.md) (AC-S43-1, `063c187`, 3448 s wall, per-test sums 3415.6 s = 99.1%);
the selector as it stands at `063c187` (`scripts/select_tests/declarations.py`, `generation.py`, `choose.py`,
`rules.py`); `tests/test_select_tests_real_audit.py`; the gaps report's probes (`/tmp/s43/`), re-pointed at this
worktree (`/tmp/s43w/facts.py`, `classify2.py`, `bprime.py`: they read the tree through `declarations.scan` and join it
with the table). No `.codegraph/` index exists here; the routes were text search and those probes.

## R-1 The table attributes the run to modules

The per-test sums account for 3415.6 of 3448 s (99.1%). D180's *would reverse if* (time mostly in shared setup outside
the durations) does not hold; the table is the ranking.

## R-2 Where the 3448 s sits, by what a module's source lets a declaration say

Each module is put in the first class that holds it, from its own facts and its `tests/` import closure as
`declarations.scan` reads them (seconds are the table's sums):

| Class | Modules | Seconds | What a declaration can do on a one-Go-file change |
|---|---|---|---|
| A — claimed by S07/S26 (`test_verify_scoped_*`, `test_ux_gates_*`, `test_decisions_*`, `test_result_contract_briefs`), to stay undeclared this slice (host, iteration 27) | 36 | 569.2 | nothing: undeclared, runs |
| B — its own source runs the launcher or `refuse(` (D164 rule 3: must be `"every"`) | 47 | 580.0 | nothing: `"every"` admits go |
| B′ — routes only through a helper it imports | 161 | 1518.4 | see R-3 |
| C — generates go, or a computed backend | 32 | 79.4 | narrows to go (`FACTORY_BACKENDS`), saves the other backends' share |
| D — generates, not go, statable | 24 | 61.5 | skipped |
| E — generates nothing anywhere in its closure | 58 | 69.2 | skipped, but re-run by the audit (R-4): no saving |
| Z — declared today (`test_matrix` 447.9, `test_images` 31.6, …) | 15 | 537.4 | already narrowed or skipped by S38 |

## R-3 B′: the helpers the heavy modules import generate through the launcher themselves

Of B′'s 1518.4 s, 1179.8 s is in modules whose own source generates nothing; 338.6 s in modules that do. What they
borrow decides what D179 (b) can do:

- **The heavy fixtures generate a project with a literal argv through `ROOT / "slipwai"`, not through
  `FactoryTestCase.generate`:** `stamp_fixture.template` (line 96: `--profile standard --backend python`),
  `parallel_gate` (lines 162, 166: `generate` and `add-service`), `scoped_fixture` (83, 147), and `render_fixture`
  (declared `"every"` for that reason, its own comment says). Non-sibling undeclared modules importing one of these sum
  to **1060.5 s** (`test_parallel_gate_families` 116, `test_parallel_gate_adopted` 60, `test_render_current` 46,
  `test_model_install_first` 30, `test_verify_stamp_key` 29, `test_verify_stamp_working` 28, …). They use the
  generated project; moving a helper out does not change that they generate every configuration under D164 rule 3.
- **The launcher wrappers** `test_adopt.slipwai` (borrowed by 25 modules, 328.9 s), `test_migrate.migrate`,
  `test_add_service.add_service`, `test_replay.replay` run `./slipwai adopt|migrate|add-service|replay`: moved into a
  helper file they carry the same route, so their borrowers stay `"every"`.
- **The non-generating helpers** (`test_replay.git` 221.1 s, `stamp_fixture.git` 207.1 s, `test_adopt.repository`,
  `test_candidates.commit/record`, `test_codegraph_narrowed.Project`, `test_mutation_borders.clean_environment`) can move
  out; a borrower that then generates nothing becomes a reads-only declaration — class E, re-run by the audit.

## R-4 A reads-only declaration saves nothing while the audit re-runs it (D181)

`test_select_tests_real_audit.LISTING` lists every declared module whose effective declaration does not generate, and
`AUDIT` runs each one under `sys.addaudithook` on every run; the audit module is undeclared, so it always runs. A
reads-only module declared by this slice is skipped by the selector and run again by the audit: the same seconds on a
selected run, twice the seconds on a full one.

## R-5 The bound

On a one-Go-file change at `063c187`, S38's selector already narrows or skips the 537.4 s of class Z (most of it
`test_matrix`'s non-go variants). Taking D179 (b) at its most generous — every C module narrowed to go (≤ 79.4 s saved),
every D module skipped (61.5 s), every own-generating B′ module freed of its helper's route (≤ 338.6 s, though several
borrow a launcher wrapper and stay `"every"`) — saves **at most ≈ 480 s** beyond what S38 saves today.

What still runs whatever (b) does: A 569.2 + B 580.0 + B′ own-non-generating 1179.8 (re-run by the audit if declared,
`"every"` if they keep a launcher fixture) ≈ **2329 s**, before any go share of C and Z. That is 2.6× the 900 s target.

- With D181 reversed (the audit narrowed to the reads-only modules a change reaches), the floor is still about
  A 569 + B 580 + the launcher-fixture importers 1060 ≈ **2209 s**.
- Only resolving a *literal* launcher argv per axis (D179's option (c), a selector rule change against D164 rule 3)
  touches B and the 1060 s of fixture importers: every one of the fixtures above names a literal non-go configuration.
  With (c), D181 reversed and the sibling-claimed modules declared after S07/S26 merge, the floor drops to the go share
  of the suite plus what genuinely computes its configuration; whether that is under 900 s is not provable without
  writing (c).

D179's *would reverse if* reads: "the per-module timing run shows that the modules (b) can narrow add up to less than
the gap between the full suite and 900 s". The gap is 3448 − 900 = 2548 s; (b) can narrow at most ≈ 480 s beyond
S38's. It holds, so per D179 condition 4 and the brief this goes back as a question before any declaration is written.

## R-6 After D187 (rule and narrowed audit), the per-name ideal

`/tmp/s43w/ideal.py` re-runs the probe on a scratch copy of the selector with the argv rule
(`/tmp/s43w/sel/select_tests/argv.py`), crediting each module only with the facts of the names it actually uses from
each `tests/` file (as if every borrowed helper had been moved), and with `".git" / "slipwai"` rewritten. On a Go change
it still runs ≈ 2641 s: siblings 570.7, launcher routes the rule does not read (`adopt`, `add-service`, `migrate`,
`*SHAPES[name]`, the module's own non-literal argvs) 1033.0, generating closures with `importlib` (`stamp_fixture.
load_script`) 370.3, go or computed backends 653.3 (`test_matrix` 447.9 and `test_images` 31.6 of it, both narrowed to
go by S38), reads of `assets/languages` 13.9. Skippable: 773.9 s, led by the codegraph/health group (≈ 277 s), the render
group (≈ 160 s), `test_factory_gate_stamp` (46.4 s), `test_mutation_scope_real_spring` (31.7 s). With the matrix's and
images' non-go share taken off, the estimated floor is ≈ 2250 s: AC-S43-6 is expected to miss (plan *Status*).

Two false launcher routes found on the way, both rewritable without changing behaviour: a `/ "slipwai"` path chain
naming a stamp directory (`self.repo / ".git" / "slipwai"`), and a `["slipwai"]` list in a declaration's own `reads`
(`render_fixture`), which `names_launcher` reads as the launcher on `PATH`.
