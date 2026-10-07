# S43 — the modules left undeclared (AC-S43-7)

Written from `declarations.scan` at the slice's tip (rebased onto `adopt-method` `0000e5b`, after S26 merged). 383 test modules; 50 carry an effective declaration; 333 are undeclared and always run, each with the selector's own reason (`Tree.effective`). Seconds are the AC-S43-1 table's at `063c187` (— for a module added since).

**What one Go app file selects now** (`assets/languages/go/app/.gremlins.yaml`, `choose.select` on this tree, a dry estimate, not AC-S43-6's measurement): 342 of 383 modules run, 7 of them narrowed to go; their seconds in the table sum to 2734 s (of 3448 s). Of that, S07's still-undeclared modules (`test_verify_scoped_*`, `test_ux_gates_*`): 564 s (D188 item 4). `test_matrix` and `test_images` count whole here; narrowed to go they cost a fraction.

S26's modules (`test_decisions_*`, `test_hand_backs_record`, `test_result_contract_briefs`/`_stops`, `test_reversibility_*`) may be declared since the rebase (D188 item 2); they sum to about 9 s in the table plus S26's new modules, and are left for a later pass.
The last column is the first thing that keeps the module running on a Go change even if every helper it borrows were moved: `route` is a launcher, `refuse(` or `adopt`/`add-service`/`migrate` route (D164 rule 3, D187 rule 3), `unstatable` an in-process reach in a generating closure (D164 rule 4), `generates go`/`computed backend` a generation the Go change reaches, `sibling` a module S07 or S26 claimed.


| Module | Seconds | Why it is undeclared (the selector's words) | What a declaration would meet (S43 probe, `/tmp/s43w/ideal.py`) |
|---|---|---|---|
| `test_add_service` | 118.6 | TEST_SELECTION is missing | route test_add_service.*:21 |
| `test_parallel_gate_families` | 116.2 | TEST_SELECTION is missing | route parallel_gate.shape:162 |
| `test_parallel_gate_adopted` | 60.5 | TEST_SELECTION is missing | route test_adopt_next.in_terminal:54 |
| `test_verify_scoped_makefiles` | 60.2 | TEST_SELECTION is missing | sibling |
| `test_verify_scoped_baseline` | 58.7 | TEST_SELECTION is missing | sibling |
| `test_codegraph_bytes` | 46.6 | TEST_SELECTION is missing | unstatable importlib or runpy test_codegraph_bytes.*:9 |
| `test_verify_scoped_flags` | 43.4 | TEST_SELECTION is missing | sibling |
| `test_verify_scoped_reach` | 43.3 | TEST_SELECTION is missing | sibling |
| `test_refresh_owned` | 37.0 | TEST_SELECTION is missing | route test_adopt_next.in_terminal:54 |
| `test_verify_stamp_tools` | 35.1 | TEST_SELECTION is missing | unstatable importlib stamp_fixture.load_script:93 |
| `test_mutation_stamp_untouched` | 34.6 | TEST_SELECTION is missing | generates go test_mutation_stamp_untouched.*:63 |
| `test_uncommitted_subdirectory` | 29.8 | TEST_SELECTION is missing | route test_adopt_next.in_terminal:54 |
| `test_model_install_first` | 29.7 | TEST_SELECTION is missing | route parallel_gate.shape:162 |
| `test_factory_gate_stamp_inputs` | 29.3 | TEST_SELECTION is missing | route test_factory_gate_stamp_scan.SRC_DIR:17 |
| `test_xdist_carry` | 29.2 | TEST_SELECTION is missing | route test_xdist_carry.*:133 |
| `test_verify_stamp_where` | 28.2 | TEST_SELECTION is missing | route test_adopt_next.in_terminal:54 |
| `test_candidates` | 26.3 | TEST_SELECTION is missing | route test_adopt_next.in_terminal:54 |
| `test_verify_scoped_implicit` | 26.3 | TEST_SELECTION is missing | sibling |
| `test_verify_scoped_sum` | 25.3 | TEST_SELECTION is missing | sibling |
| `test_verify_scoped_variables` | 24.7 | TEST_SELECTION is missing | sibling |
| `test_confirm` | 23.3 | TEST_SELECTION is missing | route test_adopt_next.in_terminal:54 |
| `test_verify_scoped_goal` | 22.9 | TEST_SELECTION is missing | sibling |
| `test_verify_stamp_runs` | 22.9 | TEST_SELECTION is missing | unstatable importlib stamp_fixture.load_script:93 |
| `test_uncommitted_places` | 22.7 | TEST_SELECTION is missing | route test_adopt_next.in_terminal:54 |
| `test_verify_scoped_obligations` | 22.6 | TEST_SELECTION is missing | sibling |
| `test_verify_scoped_compare` | 21.9 | TEST_SELECTION is missing | sibling |
| `test_verify_scoped_borders` | 21.8 | TEST_SELECTION is missing | sibling |
| `test_refresh_strategy` | 21.2 | TEST_SELECTION is missing | route test_adopt.slipwai:40 |
| `test_named_apps` | 20.6 | TEST_SELECTION is missing | route test_named_apps.*:39 |
| `test_verify_stamp_exact` | 20.5 | TEST_SELECTION is missing | route test_verify_stamp_exact.*:159 |
| `test_verify_scoped_text` | 19.8 | TEST_SELECTION is missing | sibling |
| `test_verify_scoped_record` | 19.2 | TEST_SELECTION is missing | sibling |
| `test_scoped_adopted` | 18.9 | TEST_SELECTION is missing | route test_adopt.slipwai:40 |
| `test_verify_stamp_trunk` | 18.8 | TEST_SELECTION is missing | unstatable importlib stamp_fixture.load_script:93 |
| `test_parallel_gate_include` | 18.5 | TEST_SELECTION is missing | route test_adopt.slipwai:40 |
| `test_verify_stamp_file` | 17.5 | TEST_SELECTION is missing | route test_verify_stamp_file.*:78 |
| `test_verify_scoped_words` | 17.2 | TEST_SELECTION is missing | sibling |
| `test_parallel_gate_carry` | 16.9 | TEST_SELECTION is missing | route test_migrate.migrate:44 |
| `test_verify_scoped_prune` | 16.8 | TEST_SELECTION is missing | sibling |
| `test_verify_stamp_scan` | 16.7 | TEST_SELECTION is missing | unstatable importlib stamp_fixture.load_script:93 |
| `test_result_contract_migrate` | 16.4 | TEST_SELECTION is missing | route test_result_contract_migrate.*:126 |
| `test_verify_stamp_ships` | 15.7 | TEST_SELECTION is missing | route test_add_service.add_service:21 |
| `test_verify_stamp_cannot` | 15.6 | TEST_SELECTION is missing | unstatable importlib stamp_fixture.load_script:93 |
| `test_verify_stamp_force` | 15.3 | TEST_SELECTION is missing | unstatable importlib stamp_fixture.load_script:93 |
| `test_verify_scoped_incomplete` | 14.9 | TEST_SELECTION is missing | sibling |
| `test_ratchet` | 14.1 | TEST_SELECTION is missing | route test_adopt.slipwai:40 |
| `test_verify_scoped_choose` | 13.0 | TEST_SELECTION is missing | sibling |
| `test_parallel_gate_output` | 12.8 | TEST_SELECTION is missing | route parallel_gate.shape:162 |
| `test_verify_scoped_rules` | 11.7 | TEST_SELECTION is missing | sibling |
| `test_verify_scoped_walks` | 11.4 | TEST_SELECTION is missing | sibling |
| `test_verify_stamp_inputs` | 11.2 | TEST_SELECTION is missing | unstatable importlib stamp_fixture.load_script:93 |
| `test_verify_stamp_ignored` | 10.9 | TEST_SELECTION is missing | unstatable importlib stamp_fixture.load_script:93 |
| `test_migrate` | 10.7 | TEST_SELECTION is missing | route test_migrate.*:44 |
| `test_verify_scoped_base` | 10.0 | TEST_SELECTION is missing | sibling |
| `test_render_docs` | 9.9 | TEST_SELECTION is missing | unstatable ROOT test_render_docs.*:81 |
| `test_verify_scoped_stamp` | 9.9 | TEST_SELECTION is missing | sibling |
| `test_frontend` | 9.8 | TEST_SELECTION is missing | generates go test_frontend.*:73 |
| `test_verify_stamp_repository` | 9.8 | TEST_SELECTION is missing | unstatable importlib stamp_fixture.load_script:93 |
| `test_uncommitted` | 9.5 | TEST_SELECTION is missing | route test_adopt_next.in_terminal:54 |
| `test_slice_scope_root` | 9.3 | TEST_SELECTION is missing | route test_adopt.slipwai:40 |
| `test_verify_scoped_run` | 9.2 | TEST_SELECTION is missing | sibling |
| `test_verify_stamp_page` | 9.1 | TEST_SELECTION is missing | route test_adopt_next.in_terminal:54 |
| `test_adopt_next` | 8.8 | TEST_SELECTION is missing | route test_adopt_next.*:54 |
| `test_gates` | 8.8 | TEST_SELECTION is missing | generates go test_gates.*:163 |
| `test_parallel_gate_run` | 8.7 | TEST_SELECTION is missing | route parallel_gate.shape:162 |
| `test_cruise_watch` | 8.4 | TEST_SELECTION is missing | unstatable __file__ test_cruise_watch.*:22 |
| `test_layout` | 8.2 | TEST_SELECTION is missing | route test_replay.replay:31 |
| `test_select_tests_real_audit` | 8.1 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_parallel_gate_reads` | 7.9 | TEST_SELECTION is missing | route test_parallel_gate_reads.*:134 |
| `test_verify_scoped_changed` | 7.8 | TEST_SELECTION is missing | sibling |
| `test_axes` | 7.7 | TEST_SELECTION is missing | route test_axes.*:130 |
| `test_publish_release` | 7.6 | TEST_SELECTION is missing | reads assets |
| `test_verify_scoped_factory_text` | 7.6 | TEST_SELECTION is missing | sibling |
| `test_verify_stamp_recipe` | 7.6 | TEST_SELECTION is missing | route test_add_service.add_service:21 |
| `test_codegraph_said` | 7.5 | TEST_SELECTION is missing | unstatable __file__ test_codegraph_said.*:36 |
| `test_existing_target` | 7.2 | TEST_SELECTION is missing | route test_adopt.slipwai:40 |
| `test_verify_scoped_contracts` | 7.2 | TEST_SELECTION is missing | sibling |
| `test_verify_scoped_ignored` | 7.0 | TEST_SELECTION is missing | sibling |
| `test_xdist_words` | 7.0 | TEST_SELECTION is missing | route test_describe_service.describe:23 |
| `test_adopt_facts` | 6.7 | TEST_SELECTION is missing | route test_adopt.slipwai:40 |
| `test_benchmark` | 6.7 | TEST_SELECTION is missing | route test_adopt.slipwai:40 |
| `test_xdist_page` | 6.7 | TEST_SELECTION is missing | route test_xdist_page.*:90 |
| `test_adopt` | 6.5 | TEST_SELECTION is missing | route test_adopt.*:40 |
| `test_spoken_toolchain` | 6.4 | TEST_SELECTION is missing | route test_adopt_next.in_terminal:54 |
| `test_upgrade` | 6.3 | TEST_SELECTION is missing | route test_upgrade.*:103 |
| `test_model_install_regenerate` | 6.1 | TEST_SELECTION is missing | route parallel_gate.shape:162 |
| `test_harness` | 5.9 | TEST_SELECTION is missing | route test_adopt.slipwai:40 |
| `test_parallel_gate_first` | 5.9 | TEST_SELECTION is missing | route test_parallel_gate_first.*:241 |
| `test_model_install_skip` | 5.8 | TEST_SELECTION is missing | route parallel_gate.shape:162 |
| `test_verify_stamp_pinned` | 5.7 | TEST_SELECTION is missing | route test_adopt_next.in_terminal:54 |
| `test_auth0_identity` | 5.6 | TEST_SELECTION is missing | computed backend test_auth0_identity.*:32 |
| `test_ci_fetch_adopted` | 5.5 | TEST_SELECTION is missing | route test_adopt.slipwai:40 |
| `test_runner_between_park` | 5.5 | TEST_SELECTION is missing | unstatable importlib or runpy test_runner_between_park.*:10 |
| `test_replay` | 5.4 | TEST_SELECTION is missing | route test_replay.*:31 |
| `test_slice_scope_base` | 5.3 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_slice_scope_forge_nobase` | 5.3 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_benchmark_brackets` | 5.1 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_catch_up` | 5.1 | TEST_SELECTION is missing | route test_migrate.migrate:44 |
| `test_flag_gate` | 5.1 | TEST_SELECTION is missing | computed backend test_flag_gate.*:69 |
| `test_parallel_gate_sync_ways` | 5.1 | TEST_SELECTION is missing | route parallel_gate.shape:162 |
| `test_verify_scoped_always` | 5.1 | TEST_SELECTION is missing | sibling |
| `test_aws_target` | 4.9 | TEST_SELECTION is missing | route test_aws_target.*:317 |
| `test_mutation_words_script` | 4.9 | TEST_SELECTION is missing | unstatable importlib test_mutation_borders.loaded:53 |
| `test_scoped_targets` | 4.8 | TEST_SELECTION is missing | route test_scoped_targets.*:74 |
| `test_register_ids` | 4.4 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_slice_scope_report` | 4.4 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_pruning` | 4.3 | TEST_SELECTION is missing | computed backend test_pruning.*:51 |
| `test_runner_log_stale` | 4.3 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_running` | 4.3 | TEST_SELECTION is missing | generates go test_running.*:179 |
| `test_runner_controls_park` | 4.1 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_cruise_start` | 4.0 | TEST_SELECTION is missing | unstatable importlib or runpy test_cruise_start.*:12 |
| `test_shared_packages` | 4.0 | TEST_SELECTION is missing | route test_add_service.add_service:21 |
| `test_factory_gate_stamp_probes` | 3.9 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_manifest_duplicates_migrate` | 3.9 | TEST_SELECTION is missing | route test_migrate.migrate:44 |
| `test_select_tests_pin` | 3.9 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_backing_services` | 3.8 | TEST_SELECTION is missing | computed backend test_backing_services.*:64 |
| `test_mutation_recipe` | 3.8 | TEST_SELECTION is missing | unstatable importlib test_mutation_borders.loaded:53 |
| `test_pin` | 3.8 | TEST_SELECTION is missing | route test_adopt.slipwai:40 |
| `test_commands` | 3.7 | TEST_SELECTION is missing | generates go test_commands.*:260 |
| `test_extensions` | 3.7 | TEST_SELECTION is missing | unstatable __file__ test_extensions.*:299 |
| `test_mutation_change_set` | 3.7 | TEST_SELECTION is missing | unstatable importlib test_mutation_borders.loaded:53 |
| `test_manifest_duplicates` | 3.4 | TEST_SELECTION is missing | route test_manifest_duplicates.*:118 |
| `test_runner_between` | 3.4 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_select_tests_changes` | 3.4 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_select_tests_real_loaders` | 3.4 | TEST_SELECTION is missing | reads assets |
| `test_constitution` | 3.3 | TEST_SELECTION is missing | route test_adopt.slipwai:40 |
| `test_hand_backs_append` | 3.3 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_parallel_gate_sync` | 3.3 | TEST_SELECTION is missing | route parallel_gate.shape:162 |
| `test_runner_fingerprint` | 3.3 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_code_index` | 3.2 | TEST_SELECTION is missing | generates go test_code_index.*:153 |
| `test_converge` | 3.2 | TEST_SELECTION is missing | route test_adopt.slipwai:40 |
| `test_mutation_targets` | 3.2 | TEST_SELECTION is missing | route test_mutation_targets.*:131 |
| `test_benchmark_feature` | 3.1 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_benchmark_pin` | 3.1 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_changelog` | 3.1 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_cruise` | 3.1 | TEST_SELECTION is missing | generates go test_cruise.*:230 |
| `test_users_axis` | 3.1 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_aws_flags` | 3.0 | TEST_SELECTION is missing | route test_aws_flags.*:159 |
| `test_benchmark_elapsed_migrate` | 3.0 | TEST_SELECTION is missing | route test_benchmark_elapsed_migrate.*:115 |
| `test_mutation_borders` | 3.0 | TEST_SELECTION is missing | route test_adopt.slipwai:40 |
| `test_select_tests_knobs` | 3.0 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_spec_kit` | 3.0 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_cli` | 2.9 | TEST_SELECTION is missing | route test_cli.*:20 |
| `test_runner_nonregular` | 2.9 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_select_tests_full` | 2.9 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_select_tests_narrow` | 2.9 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_cruise_tell` | 2.8 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_monorepos` | 2.8 | TEST_SELECTION is missing | unstatable __file__ test_monorepos.*:336 |
| `test_runner_stream` | 2.8 | TEST_SELECTION is missing | unstatable importlib or runpy test_runner_stream.*:10 |
| `test_scoped_migrate` | 2.8 | TEST_SELECTION is missing | route test_scoped_migrate.*:58 |
| `test_slice_scope_no_base` | 2.8 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_benchmark_elapsed` | 2.7 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_ci_history_gates` | 2.7 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_gate_walks_recorded` | 2.7 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_observability` | 2.6 | TEST_SELECTION is missing | computed backend test_observability.*:54 |
| `test_ux_gates_scale` | 2.6 | TEST_SELECTION is missing | sibling |
| `test_xdist_plugin` | 2.6 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_ci_fetch_migrate` | 2.5 | TEST_SELECTION is missing | route test_migrate.migrate:44 |
| `test_mutation_states` | 2.5 | TEST_SELECTION is missing | route scoped_fixture.events_project:147 |
| `test_gates_event_model` | 2.4 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_targets` | 2.4 | TEST_SELECTION is missing | route test_targets.*:210 |
| `test_mutation_sweeps` | 2.3 | TEST_SELECTION is missing | unstatable importlib test_mutation_borders.loaded:53 |
| `test_cruise_guard` | 2.2 | TEST_SELECTION is missing | unstatable ROOT test_cruise_guard.*:130 |
| `test_cruise_record` | 2.2 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_gates_imports` | 2.2 | TEST_SELECTION is missing | computed backend test_gates_imports.*:37 |
| `test_select_tests_generation` | 2.2 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_stage_models` | 2.2 | TEST_SELECTION is missing | route test_adopt.slipwai:40 |
| `test_toolkit` | 2.2 | TEST_SELECTION is missing | route test_add_service.add_service:21 |
| `test_decisions_scope_spelling` | 2.1 | TEST_SELECTION is missing | sibling |
| `test_describe_service` | 2.1 | TEST_SELECTION is missing | route test_describe_service.*:23 |
| `test_gate_walks_counts` | 2.1 | TEST_SELECTION is missing | generates go test_gate_walks_counts.*:105 |
| `test_mutation_scope_spring` | 2.1 | TEST_SELECTION is missing | unstatable importlib test_mutation_borders.loaded:53 |
| `test_parallel_gate_sync_edges` | 2.1 | TEST_SELECTION is missing | route parallel_gate.shape:162 |
| `test_schema_edge` | 2.1 | TEST_SELECTION is missing | generates go test_schema_edge.*:96 |
| `test_select_tests_report` | 2.1 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_wrappers` | 2.1 | TEST_SELECTION is missing | route test_adopt.slipwai:40 |
| `test_agent_types` | 2.0 | TEST_SELECTION is missing | route test_adopt.slipwai:40 |
| `test_cruise_scope_writers` | 2.0 | TEST_SELECTION is missing | route test_migrate.migrate:44 |
| `test_cruise_sweep` | 2.0 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_hand_backs_coverage` | 2.0 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_health_said` | 2.0 | TEST_SELECTION is missing | unstatable importlib or runpy test_health_said.*:15 |
| `test_mutation_placeholders` | 2.0 | TEST_SELECTION is missing | unstatable importlib test_mutation_borders.loaded:53 |
| `test_mutation_unpushed` | 2.0 | TEST_SELECTION is missing | unstatable __file__ test_mutation_unpushed.*:52 |
| `test_scoped_page` | 2.0 | TEST_SELECTION is missing | route test_adopt_next.in_terminal:54 |
| `test_select_tests_real_declared` | 2.0 | TEST_SELECTION is missing | reads assets |
| `test_skill_capabilities` | 2.0 | TEST_SELECTION is missing | route test_skill_capabilities.*:150 |
| `test_verify_scoped_matching` | 2.0 | TEST_SELECTION is missing | sibling |
| `test_xdist_gate` | 2.0 | TEST_SELECTION is missing | route parallel_gate.shape:162 |
| `test_xdist_mark` | 2.0 | TEST_SELECTION is missing | computed backend test_xdist_mark.*:19 |
| `test_add_commands` | 1.9 | TEST_SELECTION is missing | route test_add_service.add_service:21 |
| `test_benchmark_waiting` | 1.9 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_mutation_subdirectory` | 1.9 | TEST_SELECTION is missing | unstatable importlib test_mutation_borders.loaded:53 |
| `test_repository` | 1.9 | TEST_SELECTION is missing | generates go test_repository.*:89 |
| `test_adopted_manifest` | 1.8 | TEST_SELECTION is missing | route test_replay.replay:31 |
| `test_agent_context` | 1.8 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_cruise_stop_hook` | 1.8 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_mutation_java_classes` | 1.8 | TEST_SELECTION is missing | unstatable importlib test_mutation_borders.loaded:53 |
| `test_pins` | 1.8 | TEST_SELECTION is missing | computed backend test_pins.*:57 |
| `test_slice_scope_forge_hostile` | 1.8 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_benchmark_attribution` | 1.7 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_factory_repository` | 1.7 | TEST_SELECTION is missing | route test_factory_repository.*:340 |
| `test_hand_backs_shape` | 1.7 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_host` | 1.7 | TEST_SELECTION is missing | route test_host.*:161 |
| `test_runner_controls_paths` | 1.7 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_select_tests_cross_reads` | 1.7 | TEST_SELECTION is missing | route test_select_tests_cross_reads.*:24 |
| `test_slice_scope_forge` | 1.7 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_verify_stamp_launches` | 1.7 | TEST_SELECTION is missing | computed backend test_verify_stamp_launches.*:100 |
| `test_benchmark_attribution_chain` | 1.6 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_gate_walks_target` | 1.6 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_gitea_pages_environment` | 1.6 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_model_lock` | 1.6 | TEST_SELECTION is missing | route parallel_gate.shape:162 |
| `test_mutation_scope_real_go` | 1.6 | TEST_SELECTION is missing | route test_mutation_scope_real_go.*:26 |
| `test_renovate` | 1.6 | TEST_SELECTION is missing | computed backend test_renovate.*:90 |
| `test_select_tests_base` | 1.6 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_aws_forge` | 1.5 | TEST_SELECTION is missing | unstatable importlib or runpy test_aws_forge.*:14 |
| `test_azure_target` | 1.5 | TEST_SELECTION is missing | computed backend test_azure_target.*:30 |
| `test_catalog` | 1.5 | TEST_SELECTION is missing | computed backend test_catalog.*:108 |
| `test_ci_fetch_generated` | 1.5 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_hand_backs_damaged` | 1.5 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_language_skeletons` | 1.5 | TEST_SELECTION is missing | computed backend test_language_skeletons.*:89 |
| `test_mutation_dry_run` | 1.5 | TEST_SELECTION is missing | unstatable importlib test_mutation_borders.loaded:53 |
| `test_mutation_pom` | 1.5 | TEST_SELECTION is missing | unstatable importlib test_mutation_borders.loaded:53 |
| `test_mutation_scope_go` | 1.5 | TEST_SELECTION is missing | unstatable importlib test_mutation_borders.loaded:53 |
| `test_runner_controls` | 1.5 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_runner_log` | 1.5 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_select_tests_scripts` | 1.5 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_slice_scope_adopted_rules` | 1.5 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_slice_scope_printed` | 1.5 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_benchmark_attribution_gaps` | 1.4 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_npm_install` | 1.4 | TEST_SELECTION is missing | generates go test_npm_install.*:76 |
| `test_aws_promotion` | 1.3 | TEST_SELECTION is missing | computed backend test_aws_promotion.*:25 |
| `test_drive_settings` | 1.3 | TEST_SELECTION is missing | generates go test_drive_settings.*:39 |
| `test_generate_here` | 1.3 | TEST_SELECTION is missing | computed backend test_generate_here.*:26 |
| `test_model_install` | 1.3 | TEST_SELECTION is missing | route parallel_gate.shape:162 |
| `test_select_tests_imports` | 1.3 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_slice_scope_hostile_base` | 1.3 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_styles` | 1.3 | TEST_SELECTION is missing | generates go test_styles.*:29 |
| `test_biome` | 1.2 | TEST_SELECTION is missing | unstatable ROOT test_biome.*:117 |
| `test_deploy_role` | 1.2 | TEST_SELECTION is missing | unstatable importlib or runpy test_deploy_role.*:12 |
| `test_drive_evidence` | 1.2 | TEST_SELECTION is missing | generates go test_drive_evidence.*:22 |
| `test_azure_stack` | 1.1 | TEST_SELECTION is missing | computed backend test_azure_stack.*:28 |
| `test_decisions_gate_differential` | 1.1 | TEST_SELECTION is missing | sibling |
| `test_decisions_scope_calls` | 1.1 | TEST_SELECTION is missing | sibling |
| `test_go_mutation_threshold` | 1.1 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_hand_backs_missing` | 1.1 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_hand_backs_record` | 1.1 | TEST_SELECTION is missing | sibling |
| `test_mutation_migrate` | 1.1 | TEST_SELECTION is missing | route test_mutation_migrate.*:51 |
| `test_select_tests_replay` | 1.1 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_select_tests_subpackages` | 1.1 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_slice_scope_hostile_branch` | 1.1 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_benchmark_elapsed_cutoff` | 1.0 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_cruise_where` | 1.0 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_design_stage` | 1.0 | TEST_SELECTION is missing | unstatable importlib or runpy test_design_stage.*:5 |
| `test_scoped_ladder` | 1.0 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_benchmark_elapsed_merged` | 0.9 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_ground` | 0.9 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_services` | 0.9 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_uv` | 0.9 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_aws_workflows` | 0.8 | TEST_SELECTION is missing | generates go test_aws_workflows.*:110 |
| `test_hand_backs_arrival` | 0.8 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_quick_wins` | 0.8 | TEST_SELECTION is missing | route test_adopt.slipwai:40 |
| `test_uncommitted_renames` | 0.8 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_hand_backs_fences` | 0.7 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_project_mcp` | 0.7 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_utf8_io` | 0.7 | TEST_SELECTION is missing | reads assets |
| `test_benchmark_waiting_person` | 0.6 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_gate_recipes_pinned` | 0.6 | TEST_SELECTION is missing | route test_add_service.add_service:21 |
| `test_gate_walks_pinned` | 0.6 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_result_contract_briefs` | 0.6 | TEST_SELECTION is missing | sibling |
| `test_select_tests_caches` | 0.6 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_code_index_open` | 0.5 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_commit_boundaries` | 0.5 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_docs_index` | 0.5 | TEST_SELECTION is missing | computed backend test_docs_index.*:34 |
| `test_extension_pending` | 0.5 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_select_tests_environment` | 0.5 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_strangle` | 0.5 | TEST_SELECTION is missing | route test_adopt.slipwai:40 |
| `test_structure` | 0.5 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_verify_stamp_lists` | 0.5 | TEST_SELECTION is missing | unstatable importlib stamp_fixture.load_script:93 |
| `test_whats_next` | 0.5 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_xdist_ci` | 0.5 | TEST_SELECTION is missing | route parallel_gate.shape:162 |
| `test_aws_init` | 0.4 | TEST_SELECTION is missing | generates go test_aws_init.*:28 |
| `test_benchmark_git` | 0.4 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_benchmark_page` | 0.4 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_mutation_uncovered` | 0.4 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_result_contract_stops` | 0.4 | TEST_SELECTION is missing | sibling |
| `test_aws_stack` | 0.3 | TEST_SELECTION is missing | computed backend test_aws_stack.*:29 |
| `test_benchmark_overview` | 0.3 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_benchmark_waiting_park` | 0.3 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_check_python` | 0.3 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_decisions_scope` | 0.3 | TEST_SELECTION is missing | sibling |
| `test_decisions_scope_gate` | 0.3 | TEST_SELECTION is missing | sibling |
| `test_drive_adoption` | 0.3 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_go_migrate_embed` | 0.3 | TEST_SELECTION is missing | generates go test_go_migrate_embed.*:19 |
| `test_benchmark_elapsed_done_mark` | 0.2 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_decisions_scope_edges` | 0.2 | TEST_SELECTION is missing | sibling |
| `test_initial_release` | 0.2 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_maintenance_skills` | 0.2 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_parallel_gate_converge` | 0.2 | TEST_SELECTION is missing | route parallel_gate.shape:162 |
| `test_rule_increment` | 0.2 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_backend_obligations` | 0.1 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_benchmark_attribution_dedupe` | 0.1 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_benchmark_notes` | 0.1 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_go_mutation_signal` | 0.1 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_backend_naming` | 0.0 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_ci_caches` | 0.0 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_ci_image` | 0.0 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_convergence` | 0.0 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_factory_gate_stamp_scan` | 0.0 | TEST_SELECTION is missing | route test_factory_gate_stamp_scan.*:17 |
| `test_go_mutation_yaml` | 0.0 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_launcher` | 0.0 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_mutation_flush` | 0.0 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_mutation_words` | 0.0 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_platform` | 0.0 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_programme` | 0.0 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_reserved_names` | 0.0 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_reversibility_gate` | — | TEST_SELECTION is missing | — |
| `test_reversibility_migrate` | — | TEST_SELECTION is missing | — |
| `test_reversibility_paths` | — | TEST_SELECTION is missing | — |
| `test_reversibility_score` | — | TEST_SELECTION is missing | — |
| `test_reversibility_versions` | — | TEST_SELECTION is missing | — |
| `test_reversibility_writers` | — | TEST_SELECTION is missing | — |
| `test_runner_pages` | 0.0 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_scoped_order` | 0.0 | TEST_SELECTION is missing | route test_scoped_targets.build:74 |
| `test_select_tests_argv` | — | TEST_SELECTION is missing | — |
| `test_select_tests_argv_forms` | — | TEST_SELECTION is missing | — |
| `test_select_tests_audit_narrow` | — | TEST_SELECTION is missing | — |
| `test_select_tests_docs` | 0.0 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_select_tests_real_backends` | 0.0 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_select_tests_real_helpers` | 0.0 | TEST_SELECTION is missing | route test_select_tests_real_helpers.*:58 |
| `test_select_tests_real_mutation` | 0.0 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_select_tests_real_s43` | — | TEST_SELECTION is missing | — |
| `test_strategy` | 0.0 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |
| `test_survey` | 0.0 | TEST_SELECTION is missing | nothing on a go change: declarable by the D179 (b) pattern, not reached this slice |

## AC-S43-9 — the same test ids

`unittest.defaultTestLoader.discover('tests')` walked without running, on `git archive adopt-method` (`0000e5b`, the
rebased base) and on the slice's tip: 3271 ids at the base, 3333 at the tip, no import failure in either. The base's
ids are all at the tip but one: `test_select_tests_real_helpers…test_the_render_fixture_runs_the_launcher_so_it_declares_every_configuration`
is now `…test_the_render_fixture_names_the_one_project_it_generates_and_reads_the_launcher_through_support` — a
selector test about `render_fixture`'s declaration, which T006 narrowed from `"every"`, so its old name would be false.
The 63 added ids are the slice's selector tests (`test_select_tests_argv` 9, `_argv_forms` 36, `_audit_narrow` 11,
`_real_s43` 6, `_real_helpers` 1). Whether any test is newly skipped is not visible without running; the host's full
run on the faulted tree (AC-S43-8) is where it shows.

## AC-S43-10 — CI's (module, backend) pairs

No `CATALOG["backends"]` loop was switched to `backends_under_test()`: none of the modules declared here loops over
backends, and the ones that do run on a Go change whatever they declare. CI's pairs are therefore unchanged. (Had one
been switched: only `.github/workflows/verify.yml`'s `matrix` jobs set `FACTORY_BACKENDS`, and they run
`test_matrix test_images` only.)

## held()

`declarations.held()` on the tip prints `[]`.
