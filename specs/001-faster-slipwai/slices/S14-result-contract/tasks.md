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

- [ ] T012 [US6] **HIGH — `--hand-backs` gives the wrong reading of what was delegated, and its finding line names
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

- [ ] T013 [US6] **HIGH — the rebase onto S06's tip is textually clean and leaves the suite red.**
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

- [ ] T014 [US6] **HIGH — the demo script cannot be run as written** (AC-S14-19).
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

- [ ] T015 [US6] **MEDIUM — the gate crashes with a traceback on a record whose preamble holds an unclosed
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

- [ ] T016 [US6] **MEDIUM — AC-S14-14's first half is neither stated nor pinned.**
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

- [ ] T017 [US6] **MEDIUM — retrying `--hand-back` duplicates the entry** (constitution II: *a retry MUST NOT be
  able to duplicate a side effect; a test proving this MUST accompany each new write path*).
  - **Evidence:** `append` and `write` (`hand_backs.py:233-270`) append without looking at what is there. A session
    that retries after an interrupted stage close writes the same block twice, with two headings.
  - **GREEN:** the same type, stage and byte-identical block as the record's last entry for that type and stage is a
    no-op with exit 0 and a stderr note. A different block is still appended, because D134 says a wrong entry is
    followed by a new one. `--hand-back-missing` follows the same rule.
  - **Sweep:** both write verbs, each with its retry test.
  - Files: `assets/toolkit/scripts/hand_backs.py`, `assets/toolkit/scripts/check-decisions.py`,
    `tests/test_hand_backs_append.py`.

- [ ] T018 [US6] **LOW — `make benchmark` and `--hand-backs` can count different blocks** (AC-S14-15).
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

- [ ] T019 [US6] **LOW — the three verbs refuse a directory with a trailing slash or a leading `./`, and print only
  the usage text.**
  - **Evidence:** in the generated project, `--hand-back specs/f/slices/S1/ …` and `--hand-back ./specs/f/slices/S1
    …` both exit 2. A stage name such as `after_converge` is refused the same way, without the line saying which
    argument failed.
  - **GREEN:** the directory is normalised before the `FOLDER` match, and each refusal adds one line naming the
    argument.
  - **Sweep:** `hand_back_verb` and `coverage_verb`.
  - Files: `assets/toolkit/scripts/check-decisions.py`, `tests/test_hand_backs_append.py`.
