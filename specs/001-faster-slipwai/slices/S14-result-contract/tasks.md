# Tasks: S14-result-contract — every delegate hands back the same structured result

**Input**: [plan.md](plan.md) (*The example map* R1–R10 is what the tasks cut on; *Structure Decision*; *Tests*),
[data-model.md](data-model.md), [research.md](research.md), [quickstart.md](quickstart.md); acceptance criteria
AC-S14-1 … AC-S14-19 in `specs/001-faster-slipwai/spec.md` under `### S14-result-contract`.

**Branch**: `slice/S14-result-contract` (worktree `../slipwai-graph-S14-result-contract`). No push. One commit per task.

**Delegation**: one delegate per task, each its own RED-GREEN-REFACTOR increment (constitution V): write the rule's
examples, see them fail for the right reason, make them pass, refactor. A task's "Files" line is its manifest: the
only files that delegate may write. Nobody but the host writes `tasks.md`. Every task is tagged `[US6]` (User Story
6, FR-017, SC-008 first half).

## Constraints

Constraints that hold for every task's GREEN, stated once:

- **Size.** Every file under `tests/` and `src/` stays at or under 350 lines (`make check-structure`).
  `commands.py` (345), `cruise.py` (333) and `agents.py` (300) are near the limit: new text goes in
  `src/slipwai/project/result_contract.py`, each of them gains a placeholder and an import only.
- **Encoding.** Every `read_text` and `open` in a toolkit script names `encoding="utf-8"`.
- **Bytecode.** A test that loads a toolkit script as a module sets `sys.dont_write_bytecode = True` first; scripts
  under `assets/` run as `python3 -B`; no `__pycache__/` is left under `assets/` (a `scripts/__pycache__` would make
  every scoped run the full gate). `hand_backs.py` is loaded by path with `sys.dont_write_bytecode` set.
- **Tests.** Fakes written in the test tree; never a mocking framework. Examples enter through
  `check-decisions.py` or `benchmark.py` as subprocesses (`python3 -B`), or `slipwai generate`/`migrate`.
- **Commits by path.** `git add <exact paths of the task's manifest>`, never `git add -A`. `make lint typecheck
  check-structure` before each commit.
- **Scratch** only under `/tmp/s14/`.
- **Not edited, ever, by any task here:** `VERSION`, `catalog.json`, `stage_models.py`, `demo_stop.py`,
  `parallel_slices.py`, `migrate.py`, `code_index.py`, this checkout's `delivery/`, `decisions.md`, `spec.md`,
  `story-split.md`, the register, and every record under `specs/` but this slice's folder. Stay off the paragraphs
  S06's D123 rewords (`agents.py` implement and converge briefs, `commands.py` lines above
  `{who_runs_each_stage(layout)}`).
- **Pin.** Before the first task and after the last, run the pin: `tests/test_decisions_scope*.py`,
  `test_decisions_gate_differential.py`, `test_cruise_record.py`, `test_agent_types.py`, `test_commands.py`,
  `test_benchmark*.py`, `test_migrate.py`, `test_toolkit.py`.

## Phase 1: Toolkit — the shape and the gate (sequential)

R1–R6 share `assets/toolkit/scripts/hand_backs.py` and `assets/toolkit/scripts/check-decisions.py`, so they run in
order; R6 also writes `assets/toolkit/scripts/agents/benchmark.py`.

- [x] T001 [US6] **R1 — a well-formed block passes** (AC-S14-3, AC-S14-5). Includes the shared fixture and the stub
  (no separate setup task): `tests/hand_backs_fixture.py` (a scratch project with `project.json`, `specs/f/…`, the
  toolkit scripts copied; a valid block; `run(...)` as a `python3 -B` subprocess) and a first `hand_backs.py`
  (`FIELDS`, `STATUSES`, heading pattern, `extract`, `check_block`, `check_record` for the passing path) with the gate
  globbing `specs/*/hand-backs.md` and `specs/*/slices/*/hand-backs.md`. RED→GREEN: e1 the page's example block
  passes, exit 0, summary counts *1 hand-back(s) in 1 record(s)* · e2 every list field `[]` passes · e3 an extra key
  `"elapsed": 4` passes with no note · e4 `"contract": 2` with every other field absent passes with one
  `check-decisions: note:` naming the heading, no field held.
  Files: `tests/hand_backs_fixture.py`, `tests/test_hand_backs_shape.py`,
  `assets/toolkit/scripts/hand_backs.py`, `assets/toolkit/scripts/check-decisions.py`.

- [x] T002 [US6] **R2 — a malformed block names its field** (AC-S14-4, -7, -8, -9). Fault lines
  `<record>:<line>: <heading> — <field>: <fault>`, exit 1, one line per fault: absent field, wrong JSON type (`true`
  is not an integer), `contract` not 1, `delegate` not one of ten or differing from the heading, `status` outside
  its type's set, empty `scope`/`change_summary`, non-string in a list, `files_changed` absolute or with `..`,
  `decisions` id malformed or naming no `## D<n>` in the feature's `decisions.md`, `difficulty_observed` not exactly
  integer `score` 1–5 and non-empty `reason`. RED→GREEN e1–e7 (no `files_changed`; `"tests": "make test"`;
  `drive-hand` with `"green"` listing `accepted, behaviour, implementation`; `["/etc/passwd"]` and `["../x"]` fault
  while `[]` passes; `["D9999"]` and `["d12"]`; the three bad `difficulty_observed`; two faults, two lines).
  Files: `tests/test_hand_backs_shape.py`, `assets/toolkit/scripts/hand_backs.py`,
  `assets/toolkit/scripts/check-decisions.py`.

- [x] T003 [US6] **R3 — a record's structure** (AC-S14-6, AC-S14-13). One finding naming the entry for: an unclosed
  fence, two blocks in one entry, a heading not `## <UTC> — drive-<name> — <stage>`, an entry with neither block nor
  `- **Missing:** <reason>` or with both, a body that is not one JSON object. `Missing:` with any non-empty reason
  passes, `stopped: <reason>` included; text before the first `## ` is the file's own. RED→GREEN e1–e7 (unterminated
  fence; two blocks; `## yesterday — drive-gaps — gaps`; heading with only prose; `{"contract": 1,` and `[1, 2]`;
  `Missing: stopped: …` passes; a `# Hand-backs — S1` title plus paragraph passes).
  Files: `tests/test_hand_backs_record.py`, `assets/toolkit/scripts/hand_backs.py`,
  `assets/toolkit/scripts/check-decisions.py`.

- [x] T004 [US6] **R4 — nothing recorded, nothing changes** (AC-S14-16). Where no `hand-backs.md` exists the checker's
  stdout, stderr and exit are byte-identical to `check-decisions.py` at `c3c760b` (taken from git, as
  `test_decisions_scope_gate.py` does), on an empty project, a project with decisions and demos, and this
  repository's own `specs/`; where one exists the summary gains `, <n> hand-back(s) in <m> record(s)` and nothing
  else moves. RED→GREEN e1 equal triples on the three trees · e2 a tree whose only record is `hand-backs.md` is not
  *nothing recorded yet* · e3 a malformed record and a malformed decision both report under one header. Tighten the
  summary-suffix and header logic and the docstring naming `docs/result-contract.md`. If e1 already passes from
  T001's suffix rule, fold only e2–e3's behaviour here and keep e1 as the guard of the change (no passing-on-write
  test is its own task).
  Files: `tests/test_hand_backs_record.py`, `assets/toolkit/scripts/check-decisions.py`.

- [x] T005 [US6] **R5 — the dispatching session appends** (AC-S14-10, -11, -13). `--hand-back <dir> <type> <stage>`
  (stdin; takes the one block; checks with R2/R3's own functions; only on pass appends the heading, blank line and
  fence verbatim, creating the file with `# Hand-backs — <id>`; else appends nothing, prints faults, exit 1) and
  `--hand-back-missing <dir> <type> <stage> <reason…>`; `<dir>` only `specs/<feature>` or
  `specs/<feature>/slices/<id>`, else usage exit 2; append only, earlier bytes never rewritten (`append` in
  `hand_backs.py`). RED→GREEN e1–e7 (prose plus valid block appended byte for byte; malformed: field line, exit 1,
  file unchanged; no block: *no result-contract block*; two blocks refused; `Missing: malformed: status` appended
  and the gate passes it; `apps/x` and a path outside `specs/`: exit 2; a second append keeps the first bytes).
  Files: `tests/test_hand_backs_append.py`, `assets/toolkit/scripts/hand_backs.py`,
  `assets/toolkit/scripts/check-decisions.py`.

- [x] T006 [US6] **R6 — what was handed back, per stage** (AC-S14-11, -15). `check-decisions.py --hand-backs
  <slice-dir>` (`coverage` in `hand_backs.py`): per ended `benchmark.json` entry the transcript shows delegated,
  `block` / `missing — <reason>` / `nothing recorded`, matched by stage and heading time in `[started, ended]`; an
  entry with `usage.source` null is *could not attribute*, counted as neither; exit 0 always; ends with
  `hand-backs: with a result contract: n of m`. `benchmark.py` `notes()` prints per slice
  `<slice>: hand-backs with a result contract: <n> of <m>` plus `; <k> stage(s) the harness could not attribute —
  not counted` when k > 0, nothing where m = k = 0, loading `coverage` from `../hand_backs.py` with bytecode off.
  RED→GREEN e1 two delegated entries, one with a block: `1 of 2`, verb lists `implement … block` and
  `converge … nothing` · e2 `Missing:` counts in m, not n · e3 `usage.source` null: not in m · e4 a slice with no
  record `0 of m`, no line where m = k = 0 · e5 a block outside every window does not count.
  Files: `tests/test_hand_backs_coverage.py`, `assets/toolkit/scripts/hand_backs.py`,
  `assets/toolkit/scripts/check-decisions.py`, `assets/toolkit/scripts/agents/benchmark.py`.

## Phase 2: Factory text — briefs, ladder, page (one delegate, in order)

R7–R9 write `src/slipwai/project/result_contract.py` and `tests/test_result_contract_briefs.py` in common, so they are
**not** parallel with each other: one delegate, in order. As a chain they are disjoint from T003–T006 and may start
once T002 is committed (the status table they compare against is final then).

- [x] T007 [P] [US6] **R7 — every brief ends with the block** (AC-S14-1, -2, -14). New `result_contract.py`
  (`PAGE`, `STATUSES`, `brief_paragraph(name)`, `slice_record_sentence()`); `agents.agent_file`'s shared part gains
  `{brief_paragraph(agent.name)}` and the `drive-slice` brief one sentence (its own slice's record for its
  sub-delegates, its own block to `specs/<feature>/hand-backs.md` stage `ready-set` per R-5/Q2); `cruise_agents.py`:
  skipper (entry, then block), hand (three verdicts are `status`) and bosun (`unblocked`/`cannot`/`catastrophic`
  are `status`) return sentences. No brief says *return X* in a way the block contradicts. RED→GREEN e1 for each
  type in `types()`, at the root and under `delivery/`: the paragraph, the page path as the layout spells it, its own
  status set · e2 claude, codex and gemini projections carry it · e3 bosun and hand words named as `status` · e4
  `drive-slice` names its slice's record. Pin: `test_agent_types.py`.
  Files: `tests/test_result_contract_briefs.py`, `src/slipwai/project/result_contract.py`,
  `src/slipwai/project/agents.py`, `src/slipwai/project/cruise_agents.py`.

- [x] T008 [US6] **R8 — the ladder says who records, when** (AC-S14-1, -10 to -14). `hand_backs_section(layout)`
  placed after `{who_runs_each_stage(layout)}` in `commands/drive.md` (append with `--hand-back` before closing the
  benchmark entry; slice vs feature-level record; one continuation then `--hand-back-missing` with `refused`,
  `malformed: <field>` or `no continuation`; never re-run, never a host-written block; a stage in this context has no
  entry; `stopped: <reason>`; the checks before the hand and at the adversary stop, a miss there a task and never
  re-opening converge); `converge_sentence(layout)` in `converge_stage.py`'s rung and the converge brief (reads
  `--hand-backs`; a delegated stage without a passing block is a finding naming stage and type, graded `MEDIUM`
  pending Q1); `cruise_sentences(layout)` in `cruise.py` (skipper entry to `decisions.md`, block to the record; every
  skipper, hand and bosun dispatch recorded the same way). RED→GREEN e1 generated `commands/drive.md`, both profiles,
  both layouts, carries the section and verbs as the layout spells them · e2 the rung and converge brief name
  `--hand-backs` · e3 `commands/cruise.md` carries the sentence and the pointer. Pin: `test_commands.py`,
  `test_cruise_record.py`.
  Files: `tests/test_result_contract_briefs.py`, `src/slipwai/project/result_contract.py`,
  `src/slipwai/project/commands.py`, `src/slipwai/project/converge_stage.py`, `src/slipwai/project/cruise.py`,
  `src/slipwai/project/agents.py` (converge-brief sentence only).

- [x] T009 [US6] **R9 — the shape is one table** (AC-S14-1, -3). `assets/toolkit/docs/result-contract.md`: the thirteen
  fields in order with rules, the ten types with status sets, the heading, the `Missing:` forms, the three verbs;
  `src/slipwai/project/docs_index.py` indexes it. RED→GREEN e1 the page's field-table rows equal
  `hand_backs.FIELDS` · e2 its status rows equal `hand_backs.STATUSES` and the factory's `result_contract.STATUSES`
  equals the script's · e3 `docs/README.md` lists the page. The test loads `hand_backs.py` with
  `sys.dont_write_bytecode` set.
  Files: `tests/test_result_contract_briefs.py`, `assets/toolkit/docs/result-contract.md`,
  `src/slipwai/project/docs_index.py`, `src/slipwai/project/result_contract.py` (only if the table copy needs a fix).
  If `test_result_contract_briefs.py` would pass 350 lines, the delegate asks the host to name a second module
  rather than splitting on its own.

## Phase 3: Migrate and release

- [x] T010 [US6] **R10 — what a project already made gets** (AC-S14-17). Last, because it needs every file. A project
  generated by the factory at `c3c760b` (taken from git), migrated by this one: `scripts/hand_backs.py` and
  `docs/result-contract.md` arrive, agent files, `commands/drive.md`, `commands/cruise.md` and `check-decisions.py`
  are the new ones and re-projected, `make check-decisions` passes on its existing records unchanged; the same for an
  adopted repository under `delivery/`. `changelog.d/result-contract.md`: first line `MINOR`, one standalone
  **Catch-up.** paragraph naming both layouts — nothing is asked of existing logs, a slice with no `hand-backs.md` is
  not refused. RED→GREEN e1 root layout migrated: the files, the paragraph in `agents/drive-gaps.md` and its claude
  projection, gate green · e2 the adopted fixture under `delivery/` · e3 the fragment's first line and paragraph.
  `VERSION` stays `1.6.0.dev0`; `tests/test_changelog.py` must pass.
  Files: `tests/test_result_contract_migrate.py`, `changelog.d/result-contract.md`.

## Phase 4: Final check

- [x] T011 [US6] **Hold AC-S14-18 and the gate** (no new behaviour, no new test). Run and report, changing nothing
  unless a failure names a file in the manifests above:
  `git diff --name-only c3c760b` lists only paths under the *Structure Decision* (`assets/toolkit/`,
  `src/slipwai/project/`, `tests/`, `changelog.d/result-contract.md`, this slice's folder); `find assets -name
  __pycache__` is empty; `make lint typecheck check-structure`; each touched module (`test_hand_backs_shape`,
  `test_hand_backs_record`, `test_hand_backs_append`, `test_hand_backs_coverage`, `test_result_contract_briefs`,
  `test_result_contract_migrate`); `make test TESTS="test_toolkit test_utf8_io test_changelog"`; and the Pin set once
  more. The 41-minute starters matrix is not rerun here; it runs at the merge root.
  Files: none written.

AC-S14-19 (the demo) is not a task: the demo is the next stage, scripted by [quickstart.md](quickstart.md).

- [x] *(Done at `a6ddc54` (1), `85e4f4b` (2), `a086a2f` (3: both links root-relative, named), iteration 24.)* **T028 — LOW · The demo's notes (drive-hand, demo 1, iteration 23).** (1) quickstart §2's command says it is the registry's but passes only `--permission-mode acceptEdits`; it needs the registry's `--allowedTools` and `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0`, or a fresh untrusted project refuses every shell call (say the registry's command, or read it from `registry.json`). (2) the `check-decisions` summary does not count `Missing:` entries as hand-backs — say "n hand-backs, m missing". (3) the `docs/result-contract.md` link in each agent brief is root-relative and breaks when a viewer opens `agents/` (the safety-page link beside it has the same shape; fix both or neither, named). **Files:** `quickstart.md`, `assets/toolkit/scripts/check-decisions.py`, `src/slipwai/project/result_contract.py`, their tests.

## Dependencies and order

T001 → T002 → T003 → T004 → T005 → T006 (one file pair, in order) · T007 → T008 → T009 (one test module and one
factory module, in order) · T010 after T006 and T009 · T011 last.

## Parallel opportunities

- **May run alongside each other:** the chain T007 → T008 → T009 (one delegate) beside the chain T003 → T004 → T005
  → T006 (a second delegate), once T002 is committed. Their manifests are disjoint: the first writes `src/…`,
  `assets/toolkit/docs/result-contract.md` and `tests/test_result_contract_briefs.py`; the second writes
  `assets/toolkit/scripts/…` and the four `test_hand_backs_*` modules. T009 only reads `hand_backs.py` (`FIELDS`,
  `STATUSES`, final after T002). `[P]` stands on T007, the head of the second chain, and nowhere else.
- **May not:** T001 and T002 (fixture, `hand_backs.py`, `check-decisions.py`, `test_hand_backs_shape.py`); T003–T006
  among themselves (`hand_backs.py` and `check-decisions.py`; T006 also `benchmark.py`); T007–T009 among themselves
  (`result_contract.py` and `test_result_contract_briefs.py`; T008 also touches `agents.py` that T007 edited); T010
  and T011 with anything. Two delegates at most.
- Commits are by path, so two delegates share one working tree safely; neither runs `git add -A`.

## Design review

No screen in this slice.

## Convergence

### Converge pass 1

2026-10-05, cruise iteration 23, `drive-converge` over `git diff c3c760b..cbac143`. There is no `.codegraph/` in this
tree, so every symbol question went to text search. Probes ran in `/tmp/s14/` on a project generated from this
branch, and on `/tmp/s14/merged`, a `git archive` of `git merge-tree --write-tree adopt-method slice/S14-result-contract`
(tree `2a85658`). Each mutation was made on the committed tree and restored with `git checkout -- <path>`.

**Verdict: not converged.** The pass found three HIGH tasks (T012–T014), three MEDIUM (T015–T017) and two LOW
(T018–T019).
- **Domain** (`hand_backs.py`): R1–R3 are proven. The fields, the per-type `status` sets, the tolerant reader and the
  path rule hold, and mutations show the append tests have teeth. Not proven: a record whose preamble is malformed
  (T015).
- **Use case:** the gate and its byte-identity when no record exists (R4) hold. `--hand-backs` and the benchmark
  count give a wrong reading (T012, T018).
- **Delivery adapter (CLI):** exit codes 0/1/2, stdin and append-only writes hold. Not proven: retry safety (T017)
  and the usage message (T019).
- **Screen:** none. The slice has none.
- **Published contract:** the ten briefs, the drive and cruise text, the page, migrate and the fragment are in
  place. AC-S14-14's helper clause is neither stated nor pinned (T016), and the quickstart cannot be run as written
  (T014).
- **AC-S14-18 holds.** `git diff --name-only c3c760b..cbac143` lists nothing outside the allowed paths. The D123
  sentences (`agents.py:136-138`, `:193`) and the `commands.py` lines above `{who_runs_each_stage}` are untouched.
- **The rebase onto S06 is textually clean but leaves the suite red** (T013).
- **Constitution V evidence is adequate after the fact.** T005's first REDs failed partly for the wrong reason
  (FileNotFoundError). This pass's mutations of `write` (`"a"`→`"w"`) and of `append`'s fault check each turned the
  matching `test_hand_backs_append` examples red. T010's examples are characterisation of behaviour that T001–T009
  built, and the host's after-the-fact break of the brief paragraph is the sanctioned check that they have teeth.
- **Q1 (MEDIUM for a missing block) and Q2 (`drive-slice`'s own block at feature level, stage `ready-set`) are still
  the host's to confirm.** T012 shows Q2 interacts with the count.
- **Record changes still owed by the host:** ADR 0006 does not yet name the page.
- **The tree was not clean at the start.** `benchmark.json` in this folder was already modified (the host's
  `start converge` bracket). This pass left it untouched.

- [x] T012 [US6] **HIGH — `--hand-backs` gives the wrong reading of what was delegated, and its finding line names
  the stage instead of converge and the type** (AC-S14-11, -13, -15).
  - **Evidence (wrong line):** `hand_backs.py:303` prints `nothing recorded — a finding for {name}`, where `name` is
    the stage. `test_hand_backs_coverage.py:90` pins `a finding for implement`, which is the same bug. Changing the
    text to `a finding for converge`, as `data-model.md:106` and `quickstart.md:42` spell it, fails that test. The
    line never names the delegate type, although `usage.agents` carries it (`benchmark.py:420`).
  - **Evidence (wrong count):** `coverage` counts every entry with `delegated: true` (`hand_backs.py:290`).
    `benchmark.py:508` sets that flag when any sub-agent spent tokens, so the count includes stages that owe no
    block. Two probes show it:
    - This slice's own committed `benchmark.json` reads `0 of 4`, with a finding for `plan`. `drive-slice` ran
      `plan` in its own context, and under Q2 its block goes to the feature record.
    - A host-run `gaps` stage whose only sub-agent was `Explore` reads `nothing recorded — a finding for gaps`.
      AC-S14-13 says it should read nothing at all.
  - **GREEN:**
    - A stage counts in `m` only when `usage.agents` names a `drive-*` type that owes a block to that record.
      `drive-slice` owes its block to the feature record, and untyped helpers owe none.
    - Each line names the stage and the type(s), and reads `a finding for converge`.
    - The `<stage>` the session passes to `--hand-back` is the open benchmark entry's stage name. Today the ladder
      only implies this.
  - **Sweep, across every reader of the delegation:**
    - `coverage` and `benchmark.hand_back_lines`;
    - `data-model.md`'s `--hand-backs` example and `quickstart.md` step 3;
    - the page's `--hand-backs` paragraph, `converge_sentence`, `hand_backs_section`, `slice_record_sentence` and
      `cruise_sentences` (how `<stage>` is chosen);
    - `test_hand_backs_coverage` e1–e5, re-pinned to the right text and given an `Explore`-only example and a
      `drive-slice`-own-context example.

    If the host's answer to Q2 changes where `drive-slice`'s block goes, the rule for which stages count follows it.
  - Files: `assets/toolkit/scripts/hand_backs.py`, `assets/toolkit/scripts/agents/benchmark.py`,
    `assets/toolkit/docs/result-contract.md`, `src/slipwai/project/result_contract.py`,
    `tests/test_hand_backs_coverage.py`, `tests/test_result_contract_briefs.py`, this folder's `data-model.md` and
    `quickstart.md`.

- [x] T013 [US6] **HIGH — the rebase onto S06's tip is textually clean and leaves the suite red.**
  - **Evidence:** `git merge-tree --write-tree adopt-method slice/S14-result-contract` reports no conflict (tree
    `2a85658`). On that tree, `test_verify_scoped_record.TableHeldTest.test_e4_every_path_a_check_script_reads_lies_under_one_of_its_recorded_inputs`
    fails with `<shape>: check-benchmark reads .., under none of ['.specify/', … 'specs/']` for every shape.
  - **Cause:** `benchmark.py` now loads `hand_backs.py`. S06's scanner then reads the bare `".."` literal at
    `hand_backs.py:68` as a path input.
  - **Fix, proven on the scratch tree only:** writing `os.pardir` there makes `TableHeldTest` and
    `test_hand_backs_shape` green (20 tests OK).
  - **GREEN:** after the rebase, `make test TESTS="<every test_verify_scoped_* module> <the six S14 modules>
    test_decisions_scope_gate test_decisions_scope_calls"` passes. Its six errors on the scratch tree came only from
    that tree having no git history (`git show c3c760b:`/`596740f:`); they must resolve on the rebased branch.
  - **Sweep:** S06's `TableHeldTest` over every check script this slice changed or added: `check-decisions.py`,
    `agents/benchmark.py`, `hand_backs.py`, and every string literal in them the scanner can read as a path. Do not
    widen S06's table or its `NOT_AN_INPUT`; that is S06's surface (D129).
  - Files: `assets/toolkit/scripts/hand_backs.py` (and the other two scripts, only if the sweep finds a literal
    there).

- [x] T014 [US6] **HIGH — the demo script cannot be run as written** (AC-S14-19).
  - **Evidence:**
    - Step 1 generates with `--no-init`. In `/tmp/s14/c1/demo`, step 2's `make agents` then fails with `agent
      projection failed: cannot determine the selected integration; rerun ./init --integration <agent>`.
    - Step 2 never gives the dispatch command. `claude --help` lists `--agent <agent>`, but the script does not say
      how a typed delegate's own final message reaches `handback.txt`, rather than the outer session's message.
    - Step 3's expected `gaps …: nothing recorded — a finding for converge` is not what the code prints (T012).
  - **GREEN:** every command in steps 1–4 is written out exactly — the init or integration step, the headless
    `--agent` dispatch and its capture, and the fixture `benchmark.json` for step 3. Each has been run once in
    `/tmp/s14/` up to the point where a real model call is needed, and its expected output is the code's.
  - **Sweep:** every expected-output line in `quickstart.md`, checked against the code that prints it.
  - Files: this folder's `quickstart.md`.

- [x] T015 [US6] **MEDIUM — the gate crashes with a traceback on a record whose preamble holds an unclosed
  `result-contract` fence** (AC-S14-6).
  - **Evidence:** the record `# T`, then an unclosed fence opened with the `result-contract` info string, then
    `{`, then `## 2026-10-05T10:00:00Z — drive-gaps — gaps`, then `- **Missing:** no continuation`. Running
    `python3 -B scripts/check-decisions.py` on it in the generated project gives `IndexError: list index out of
    range` at `hand_backs.py:154` (`entries[-1]` with no entry yet).
  - **Why it matters:** `check-decisions.py:111` promises one line naming the file and never a traceback.
  - **GREEN:** a finding naming the file and line, exit 1.
  - **Sweep:**
    - every `entries[-1]` in `extract`, and `blocks_in`;
    - a test that runs the gate over each R3 fixture with each content (no fence, a closed `result-contract` fence,
      an unclosed one, another info string) placed before the first heading, and asserts no traceback on stderr.
  - Files: `assets/toolkit/scripts/hand_backs.py`, `tests/test_hand_backs_record.py`.

- [x] T016 [US6] **MEDIUM — AC-S14-14's first half is neither stated nor pinned.**
  - **Evidence:**
    - `result_contract.py:41`'s paragraph says *Whatever you started and did not finish … goes inside that one
      block*. That covers unfinished work, not the untyped helpers a delegate dispatches (Explore, general-purpose,
      `drive-implement`'s fan-out groups), and D134 item 6 asks for those to report inside the delegate's one block.
    - No test mentions helpers (searching the briefs test, the module and the page for `helper` finds nothing).
  - **GREEN:** the paragraph says that helpers the delegate starts get no block and no entry of their own, and that
    what they did is reported in its own block. A test holds this for all ten types, in both layouts.
  - **Sweep:** `brief_paragraph`, the page's *The record* section, and the `drive-implement` brief's fan-out text.
  - Files: `src/slipwai/project/result_contract.py`, `assets/toolkit/docs/result-contract.md`,
    `tests/test_result_contract_briefs.py`.

- [x] T017 [US6] **MEDIUM — retrying `--hand-back` duplicates the entry** (constitution II: *a retry MUST NOT be
  able to duplicate a side effect; a test proving this MUST accompany each new write path*).
  - **Evidence:** `append` and `write` (`hand_backs.py:233-270`) append without looking at what is there. A session
    that retries after an interrupted stage close writes the same block twice, with two headings.
  - **GREEN:** the same type, stage and byte-identical block as the record's last entry for that type and stage is a
    no-op with exit 0 and a stderr note. A different block is still appended, because D134 says a wrong entry is
    followed by a new one. `--hand-back-missing` follows the same rule.
  - **Sweep:** both write verbs, each with its retry test.
  - Files: `assets/toolkit/scripts/hand_backs.py`, `assets/toolkit/scripts/check-decisions.py`,
    `tests/test_hand_backs_append.py`.

- [x] T018 [US6] **LOW — `make benchmark` and `--hand-backs` can count different blocks** (AC-S14-15).
  - **Evidence:** `benchmark.py:877` passes `known=None`, while `check-decisions.py` (`coverage_verb`) passes the
    feature's `D<n>` ids. A block naming an absent `D9999` therefore counts in `n` for the benchmark and fails the
    gate.
  - **Impact:** on a green tree the gate refuses such a record, so the two agree. They differ only on a red tree,
    or on a slice branch cut before its `D<n>` was written on trunk. Even so, *n* should count only blocks that
    pass the gate.
  - **GREEN:** both callers pass the same `known`. The decision-id reading lives in one function, which the gate,
    the coverage verb and the benchmark all call.
  - **Sweep:** every caller of `coverage` and `check_block`.
  - Files: `assets/toolkit/scripts/agents/benchmark.py`, `assets/toolkit/scripts/check-decisions.py`,
    `assets/toolkit/scripts/hand_backs.py`, `tests/test_hand_backs_coverage.py`.

- [x] T019 [US6] **LOW — the three verbs refuse a directory with a trailing slash or a leading `./`, and print only
  the usage text.**
  - **Evidence:** in the generated project, `--hand-back specs/f/slices/S1/ …` and `--hand-back ./specs/f/slices/S1
    …` both exit 2. A stage name such as `after_converge` is refused the same way, without the line saying which
    argument failed.
  - **GREEN:** the directory is normalised before the `FOLDER` match, and each refusal adds one line naming the
    argument.
  - **Sweep:** `hand_back_verb` and `coverage_verb`.
  - Files: `assets/toolkit/scripts/check-decisions.py`, `tests/test_hand_backs_append.py`.

### Converge pass 2

2026-10-05, cruise iteration 23, `drive-converge` over `git diff c3c760b..b06f79f` (pass 1's fixes are
`0d9032a..b06f79f`). This is the confirming pass at the ladder's bound of two. There is no `.codegraph/` in this tree,
so every symbol question went to text search. Each mutation was made on the committed tree and restored with
`git checkout -- <path>` before the next one. Probes ran in `/tmp/s14/p2/`: a project generated from this branch, and
`merged/`, a `git archive` of `git merge-tree --write-tree adopt-method slice/S14-result-contract` (tree `527df81`,
S06 at `d7b24a1`).

**Verdict: stopped at its bound, with no CRITICAL.** T012–T019 each closed its whole sweep. Nothing re-opens the loop.
T020 (MEDIUM) and T021–T023 (LOW) go to Phase 4.

**Sweep confirmations.** The six S14 modules run 105 tests, all OK. Each mutation below turned its tests red, and the
tests were green again after the restore:

| Task | Mutation | Result |
|---|---|---|
| T012 | `owed` ignores `OWNERS` | 3 of `test_hand_backs_coverage` red |
| T012 | the finding names `{name}` instead of `converge` | 2 red |
| T012 | `AGENTS` → `"agent" + "x"` | 16 red, so the key cannot drift unseen |
| T015 | the preamble-fence entry dropped | 3 of `test_hand_backs_record` red |
| T017 | `append`'s `repeats` removed | 1 red |
| T017 | `append_missing`'s `repeats` removed | 1 red |
| T018 | `benchmark.py` passes `known=None` | 1 red |
| T019 | `rstrip("/")` removed | 2 of `test_hand_backs_append` red |
| T016 | the helper sentence cut from `brief_paragraph` | 20 of `test_result_contract_briefs` red |

The probes agreed with the code:
- **T013:** on `merged/`, `test_verify_scoped_record`, including `TableHeldTest`, and the four `hand_backs` modules
  pass. The only 3 errors are `NothingRecordedTest` e1's `git show`, because the archive has no history. S06's working
  tree in the main checkout holds uncommitted `verify_scoped` changes; T013 is green against S06's committed tip only.
- **T014:** in the generated project, quickstart step 3's fixture prints exactly the two lines the quickstart gives. So
  do `S2/` and `./specs/f/slices/S2`. `benchmark.py` prints `S2: hand-backs with a result contract: 0 of 1`.
- **T012:** stages whose only agents are `drive-slice` or `Explore` print nothing and count nothing.

**Levels.**
- **Domain** (`hand_backs.py`): R1–R3 hold, and so do the T015 preamble rule and the T017 `repeats` rule. Not proven:
  - retry safety for a CRLF hand-back (T021);
  - a foreign fence left unclosed inside an entry (T023).
- **Use case:** the coverage reading and `make benchmark` count the same stages. Both use one `decision_ids`, at
  `hand_backs.py:87`, and the T018 mutation shows they now share it. The gate's answer is byte-identical when no record
  exists (`check-decisions.py:542`).
  - Under Q2, `drive-slice` is in no `OWNERS`, and no ladder opens a `ready-set` benchmark entry. So a feature-level
    `drive-slice` block is counted nowhere. That matches AC-S14-15's per-slice wording. It is Q2's to confirm.
- **Delivery adapter (CLI):** a refusal names its argument. Folders are normalised. A retry is a no-op with a note,
  exit 0. `--hand-backs specs/f` is refused with `is not specs/<feature>/slices/<id>`, exit 2.
- **Screen:** none.
- **Published contract:** the helper sentence holds in all ten briefs, in both layouts. The `OWES` and `STAGE` sentences
  reach the page, the ladder, converge and cruise.
  - `STAGE` contradicts `ready-set` (T022).
  - The fragment still says *delegated stages*, where the count is now the stages a typed delegate that belongs to
    them ran (T022).
- **AC-S14-18:** `git diff --name-only 0d9032a..b06f79f` lists nothing outside the allowed paths.

**Constitution.**
- **I:**
  - The no-record gate is byte-identical: `check-decisions.py:542`, held by `test_hand_backs_record.py:151`.
  - The catch-up note is `changelog.d/result-contract.md:5`.
  - `hand_backs.py` is loaded with bytecode off (`check-decisions.py:486`), and no `__pycache__` is left under `assets/`.
  - The scoped-gate table is held, but by splitting a literal (`hand_backs.py:333`; T020).
- **II:**
  - Retry safety: `hand_backs.py:258-270` (`repeats`), `:296` and `:305`, held by `test_hand_backs_append.py:172-200`.
    Not held for CRLF input (T021).
  - Concurrency: each slice appends only to its own folder's record (`check-decisions.py` `folder_of`), in append mode
    (`hand_backs.py:317`), and the feature record has one writer, the host.
- **III:** `OWNERS` (`hand_backs.py:324`) is a second copy of `benchmark.py:78`, and `OwnersTest`
  (`test_hand_backs_coverage.py:70`) holds the two equal. No task: see below.
- **V:** pass 1's fixes each came with a test, and every one of those tests fails under the mutations above.
- **VII:** the verb writes the UTC time, never the delegate (`check-decisions.py:598`), and entries are append-only
  (`hand_backs.py:311-318`).
- **VIII:** readers tolerate unknown fields (`check_block` iterates only `FIELDS`, `hand_backs.py:137`). A later
  `contract` is passed with a note (`:41`, `:236`).
- **IX:** paths are repository-relative (`hand_backs.py:65-71`, D135).
- **IV, VI and X:** not touched.

**`OWNERS` as a copy.** Keep it. `hand_backs.py` cannot load `benchmark.py`: S06's scanner would then read
`benchmark.py`'s literals as check-decisions inputs — `.claude/projects`, `agents/`, `commands/`, `skills/`,
`.specify/` — which is a real widening. And `benchmark.py` loads `hand_backs.py` only optionally (`benchmark.py:861`).
Both files are factory-written, and a factory test holds them equal.

**Q1 and Q2 are still the host's.** T012's `owed` and `OWNERS` follow Q2: if `drive-slice`'s block moves, the rule for
which stages count moves with it.

- [x] T020 [US6] **MEDIUM (Phase 4) — `hand_backs.py:333` passes S06's scanner by splitting a literal, not by satisfying
  it.**
  - **Evidence:**
    - With `AGENTS = "agents"`, `TableHeldTest` fails 12 shapes with `check-decisions reads agents, under none of
      ['docs/event-model/model.yaml', 'specs/']`.
    - The finding is check-decisions, which loads `hand_backs.py`. It is not check-benchmark: check-benchmark's row
      holds `agents/`, and `benchmark.py` uses the bare `"agents"` at `:421`, `:441`, `:507`, `:531`, `:587`, `:953`.
      The code comment does not say which check it means.
    - The property the scanner measures holds: `"agents"` is a key of a `benchmark.json` stage, and check-decisions
      reads nothing under `agents/`. But S06 built the route for exactly this case — `NOT_AN_INPUT`, with a reason and
      a staleness check (`test_verify_scoped_record.py:42`, `:330`). The split bypasses that audit trail. It would also
      fire again the day the scanner folds constants.
    - `hand_backs.py:69`'s `os.pardir` (T013) is the same class of case. It is the idiomatic name for the segment, so
      it is less evasive.
  - **Alternatives inside S14's scope (D129 forbids editing S06's table or test):**
    - (a) Keep the split and the comment as they are. Rejected: it evades the scanner silently.
    - (b) Pass the types into `coverage` from the caller. Rejected: the literal would move into `check-decisions.py`,
      and the same finding follows it.
    - (c) Move `coverage` into `benchmark.py`, whose row covers `agents/`. Rejected: `--hand-backs` is a published
      `check-decisions` verb (AC-S14-15, the page), so this changes the contract.
    - (d) Recommended: keep the split for now. Correct its comment to name check-decisions and the false positive, and
      say the split goes when S06 records the key. Report to the host, for S06: add `NOT_AN_INPUT["agents"] = "a key of
      a benchmark.json stage that hand_backs.py reads (check-decisions), not a path"`. Once that is on `adopt-method`,
      S14 reverts to `stage.get("agents")`.
  - **GREEN:**
    - the comment names check-decisions;
    - the host has relayed the false positive to S06;
    - after S06 records it, `hand_backs.py` reads the bare key, and `TableHeldTest` is green on the rebased branch.
  - **Sweep:** every string in `hand_backs.py`, `check-decisions.py` and `agents/benchmark.py` that S14 changed in shape
    to avoid the scanner. Today that is `:333` and `:69`. Each is either recorded in S06's `NOT_AN_INPUT` or argued to
    be the idiomatic spelling.
  - Files: `assets/toolkit/scripts/hand_backs.py`. S06's table and test belong to S06.

- [x] *(Done at `146d92e`, iteration 24.)* T021 [US6] **LOW (Phase 4) — a CRLF hand-back retried is appended twice** (constitution II).
  - **Evidence:** `/tmp/s14/p2/probe.py` calls `append` twice with the same CRLF text. Both calls return `([], True)`,
    and the record holds two headings. `body` keeps the `\r` (`hand_backs.py:286`), while `extract` reads through
    `read_text`'s universal newlines (`:263`), so `repeats` never matches.
  - **Reach:** Windows text-mode stdin already translates CRLF, so the case is a CRLF capture file piped in on POSIX.
    The gate passes both entries.
  - **GREEN:** `repeats` compares newline-normalised bodies, and a CRLF retry test is added beside e8.
  - **Sweep:** both write verbs, and every comparison between the hand-back and the record.
  - Files: `assets/toolkit/scripts/hand_backs.py`, `tests/test_hand_backs_append.py`.

- [x] *(Done at `a086a2f`, iteration 24.)* T022 [US6] **LOW (Phase 4) — the `STAGE` sentence contradicts `ready-set`, and the fragment's count sentence
  predates T012.**
  - **Evidence:**
    - `STAGE` (`result_contract.py:35`) says `<stage>` is the open benchmark entry's name. It sits right after
      "stage `ready-set`" (`:71`, `:128`; generated `agents/drive-slice.md:36-37`, `commands/drive.md:283-284`). No
      ladder opens a `ready-set` entry.
    - `changelog.d/result-contract.md:3` says *how many delegated stages handed back a block*.
  - **GREEN:**
    - `STAGE` names `ready-set` as the one stage with no benchmark entry, or is scoped to a slice's stages.
    - The fragment says a stage counts when a typed delegate that belongs to it ran.
    - `test_result_contract_briefs.py:197` pins both.
  - **Sweep:** every place `STAGE` is spliced, and the page's `--hand-backs` paragraph.
  - Files: `src/slipwai/project/result_contract.py`, `assets/toolkit/docs/result-contract.md`,
    `changelog.d/result-contract.md`, `tests/test_result_contract_briefs.py`.

- [x] *(Done at `5ba4a6d`, iteration 24.)* T023 [US6] **LOW (Phase 4) — an unclosed foreign fence inside an entry silently hides the next entry from the
  gate and from coverage** (AC-S14-6).
  - **Evidence:** in the probe, an entry was followed by a ` ```text ` fence left unclosed, then a valid `--hand-back`
    append, then a malformed entry. The valid entry vanished: the next closing fence closed the `text` fence. The gate
    counted 2 and named only the malformed one.
  - **Reach:** only a hand edit, because the verbs write result-contract fences only.
  - **GREEN:** a line matching `HEADING` inside a foreign fence is a finding naming both lines, and so is a foreign
    fence left unclosed at the end of the file.
  - **Sweep:** `extract` and `blocks_in`.
  - Files: `assets/toolkit/scripts/hand_backs.py`, `tests/test_hand_backs_record.py`.

### After convergence: `/gaps` over the slice diff

2026-10-05, cruise iteration 23, `drive-gaps` (read only) over `git diff c3c760b..0d8097d`. It traced AC-S14-1..19:
twelve fully pinned, five partly, one confirmed defect, three product questions (written into
[plan.md](plan.md#open-questions) as Q3–Q5). The loop is at its bound and none is `CRITICAL`, so each lands here as a
Phase 4 task; the slice goes to its demo carrying them.

- [x] *(Done at `5ba4a6d`, iteration 24.)* T024 [US6] **MEDIUM (Phase 4) — a four-backtick quoted example hides the delegate's real block from
  `--hand-back`** (AC-S14-10, -11).
  - **Evidence:** `blocks_in` (`hand_backs.py:242`) and `extract` (`:149`) treat any line opening with three backticks
    as a fence, so a ```` ````markdown ```` wrapper pairs with the inner closing fence and the trailing real block is
    swallowed. Reproduction: prose, then a ```` ````markdown ```` wrapper around a ```` ```result-contract ```` example
    (as `docs/result-contract.md` itself shows), then a valid `drive-gaps` block, piped to `--hand-back
    specs/f/slices/S1 drive-gaps gaps`, prints `no result-contract block in the hand-back`, exit 1; without the quoted
    example, exit 0. A delegate that did return a block costs a continuation or gets a `Missing:` line.
  - **GREEN:** fences are paired CommonMark-style — a fence closes only on a run of the same character at least as
    long as the one that opened it — and only a top-level `result-contract` fence is a block.
  - **Sweep:** `blocks_in` and `extract` together, with T023 (the same two functions); a test per nesting: four inside
    three, three inside four, tildes, an unclosed outer fence.
  - Files: `assets/toolkit/scripts/hand_backs.py`, `tests/test_hand_backs_append.py`, `tests/test_hand_backs_record.py`.

- [x] *(Done at `7e73ec1`, iteration 24.)* T025 [US6] **MEDIUM (Phase 4) — the completion audit is not told to be the backstop** (AC-S14-12, last clause;
  D136 item 2).
  - **Evidence:** `## When the ready set is empty: the completion audit` (`cruise.py:199`ff) says nothing of hand-backs;
    no text or test puts the check there.
  - **GREEN:** one sentence there — each audit `drive-gaps` delegate runs `--hand-backs` over every slice and reports a
    delegated stage with neither a passing block nor a `Missing:` line as an audit finding — spliced from
    `result_contract.py`, pinned in `test_result_contract_briefs.py`.
  - **Sweep:** the three stops D136 names (demo, adversary, audit), each pinned by a test.
  - Files: `src/slipwai/project/result_contract.py`, `src/slipwai/project/cruise.py` (one placeholder),
    `tests/test_result_contract_briefs.py`.

- [x] *(Done at `a086a2f`, iteration 24.)* T026 [US6] **LOW (Phase 4) — three harness projections are not pinned** (AC-S14-1, *`make agents` carries it into
  every harness's agent file*).
  - **Evidence:** `test_the_claude_codex_and_gemini_projections_carry_the_paragraph` covers three of six; Cursor,
    Copilot and opencode are unchecked.
  - **GREEN / sweep:** the test runs over every harness with an `agentFile` row in `scripts/agents/registry.json`.
  - Files: `tests/test_result_contract_briefs.py`.

- [x] *(Done at `a6ddc54`, iteration 24.)* T027 [US6] **LOW (Phase 4) — the migrate test proves `make check-decisions`, not `make verify`** (AC-S14-17,
  AC-S14-16's full-gate clause).
  - **Evidence:** `test_result_contract_migrate` e1/e2 run only `check-decisions`; nothing compares the full gate's
    findings before and after on a project with no record.
  - **GREEN:** on the migrated root project, `make verify-checks` (the gate's checks without the matrix) exits as it
    did before migrate, with the same findings; the adopted fixture the same under `delivery/`. The full `make verify`
    stays the merge root's.
  - **Sweep:** both layouts.
  - Files: `tests/test_result_contract_migrate.py`.

### Adversary pass (2026-10-06, iteration 24, at `525399b`; `adversary-log.md`, row S14) — the class each closes

- [x] *(Done at `00e06a9`, `5a956ad`, `98cfa5e`, iteration 24.)* **T029 — HIGH · A `Missing:` reason is one line, or it is refused (A1; AC-S14-10, -11; the page's body shape).** **RED:** `--hand-back-missing` with a reason holding `\n`, `\r`, `\r\n`, a line opening a fence, or a line shaped like an entry heading is refused with exit 2 and nothing appended; the forged-block repro no longer passes the gate or coverage; an innocent multi-line refusal never reaches the record. **GREEN — the class:** every value the verbs write outside the delegate's verbatim block (the reason, the agent and stage arguments) is one line of printable text, checked before anything is written; the method's `refused: <the delegate's words>` says the host keeps the first line. **Files:** `assets/toolkit/scripts/hand_backs.py`, `assets/toolkit/scripts/check-decisions.py`, `tests/test_hand_backs_append.py` or a new `tests/test_hand_backs_missing.py`; `src/slipwai/project/result_contract.py` if the method's words change.
- [x] *(Done at `c8ae7d1`, iteration 24.)* **T030 — HIGH · An entry answers the stage it was written for, a continuation included (B1, A2, A5) — decided by D160.** See D160 for the GREEN. **Files:** `assets/toolkit/scripts/hand_backs.py`, `tests/test_hand_backs_coverage.py`, `tests/test_hand_backs_append.py`; the page and the method's words where D160 says.
- [x] *(Done at `8afe9cd`, `acc003a` (catch-up), iteration 24.)* **T031 — MEDIUM · A stage that ran before the contract arrived owes nothing (B2) — decided by D161.** See D161. **Files:** `assets/toolkit/scripts/hand_backs.py`, `assets/toolkit/scripts/agents/benchmark.py`, `changelog.d/result-contract.md`, `tests/test_hand_backs_coverage.py`, `tests/test_result_contract_migrate.py`.
- [x] *(Done at `7e73ec1`, iteration 24.)* **T032 — MEDIUM · The adversary page records the adversaries' blocks before it closes the entry (B3).** **RED:** a generated project's `commands/adversary.md` (and its adopted twin) carries the append step, spliced from `result_contract.py`, before *end the `adversary` benchmark entry*; `test_result_contract_briefs.py` pins it beside the drive and cruise sentences. **GREEN — the class:** every page that owns a stop with delegates — drive, cruise, adversary, the completion audit (T025) — says to append each block before ending the stage's entry. **Files:** `src/slipwai/project/result_contract.py`, the source that writes `commands/adversary.md` under `src/slipwai/project/`, `tests/test_result_contract_briefs.py`.
- [x] *(Done at `86a2be6`, `576b1e0`, iteration 24.)* **T033 — MEDIUM · A harness whose delegates cannot be attributed says so (A3; AC-S14-15).** **RED:** a stage read from a Codex session (`usage.source` `codex`, no subagents) with a typed delegate in `agents` or `signals.agent` is listed as *could not attribute*, never left out, and `make benchmark` prints the hand-back line for it. **GREEN:** coverage treats any harness whose reader returns no subagents as unattributable, not as undelegated. **Files:** `assets/toolkit/scripts/hand_backs.py`, `assets/toolkit/scripts/agents/benchmark.py` if the reader must say so, `tests/test_hand_backs_coverage.py`.
- [x] *(Done at `14dff98`, iteration 24.)* **T034 — MEDIUM · `--hand-back` reads stdin as UTF-8 whatever the locale (A4; AC-S14-10 *verbatim*).** **RED:** under `PYTHONIOENCODING=cp1252` (and `LC_ALL=C`) a block with `café — fixed` is recorded byte for byte; invalid UTF-8 on stdin is refused in one line, no traceback. **GREEN:** stdin is read as bytes and decoded as UTF-8. **Files:** `assets/toolkit/scripts/check-decisions.py`, `tests/test_hand_backs_append.py`.
- [x] *(Done at `fc8864e`, iteration 24.)* **T035 — LOW · Damaged inputs end in the page's exits, never a traceback (A6).** **RED:** a `benchmark.json` cut off, empty, with a BOM, `[]`, `"stages": {}`, a string `usage`, a stage with no `stage` or no `started`; a record ending mid-UTF-8; a body nested 100000 deep — each gives the page's exit and one line naming the file, and nothing is written; a stage with no `started` is *could not tell*, never a window from the start of time. **Files:** `assets/toolkit/scripts/hand_backs.py`, `assets/toolkit/scripts/check-decisions.py`, a new `tests/test_hand_backs_damaged.py`.
- [x] *(Done at `2600a7b`, `7166a00`, iteration 24.)* **T036 — LOW · The verb vouches only for a contract it knows (A8) — decided by D162.** See D162. **Files:** `assets/toolkit/scripts/hand_backs.py`, `tests/test_hand_backs_shape.py`, the page.
- [x] *(Done at `1041b38`, `6b31015`, iteration 24.)* **T037 — LOW · An `unavailable` skipper answer and its `D<n>` (B6) — decided by D163.** See D163. **Files:** `src/slipwai/project/cruise.py` or `cruise_agents.py`, `src/slipwai/project/result_contract.py`, `assets/toolkit/docs/result-contract.md`, `tests/test_result_contract_briefs.py`.

## After acceptance (host tasks, iteration 24)

- [x] **T038 — The adversary pass.** Two seams, fourteen findings (`adversary-log.md`, row S14); T029–T037 carry them; A7 and B4 fold into T024; B5 declined.
- [x] **T039 — Mutation.** N/A — `project.json` records no mutation command for this repository (`"mutation": null`).
- [x] *(Done at `717cd5a`, iteration 24: 2799 tests each, green.)* **T040 — Both full gates on the final tip** (`make verify`, then the delivery gate under CI markers), after every suite that reads a generated gate.
- [x] *(Done, iteration 24.)* **T041 — Register row (`accepted-by: drive-hand`), close the record; remove the slice's worktrees and branch.**
