# Timings — machine noahc-server (12 cores), no CI variable set, each run alone on the machine except another session's light work; bash `time`, wall clock
| run | commit | command | selected of total | elapsed | modules failing |
|---|---|---|---|---|---|
| timed-a-selected | 308f3d3 | `time make test SINCE=52ecbd3` | 341 of 341 | 3268.5 s | test_factory_repository test_matrix |
| timed-a-full | 308f3d3 | `time make test FULL=1` | 341 of 341 (full) | 3314.9 s | test_factory_repository |
| timed-b-selected | 8b464e8 | `time make test SINCE=52ecbd3` | 335 of 341 | 3254.7 s | test_factory_repository test_matrix |
| timed-b-full | 8b464e8 | `time make test FULL=1` | 341 of 341 (full) | 3312.1 s | test_factory_repository |
| fault-a-full | 195cae8 | `time make test FULL=1` | 341 of 341 (full) | 2911.0 s | test_add_service test_factory_repository test_matrix |
| fault-a-selected | 195cae8 | `time make test SINCE=52ecbd3` | 341 of 341 | 2869.1 s | test_add_service test_factory_repository test_matrix |
| fault-b-full | 005c4ed | `time make test FULL=1` | 341 of 341 (full) | 3321.1 s | test_factory_repository test_mutation_java_classes test_pit_globs test_select_tests_real_audit |
| fault-b-selected | 005c4ed | `time make test SINCE=52ecbd3` | 335 of 341 | 3259.0 s | test_factory_repository test_matrix test_mutation_java_classes test_pit_globs test_select_tests_real_audit |
| fault-a2-full | 1ad28f9 | `time make test FULL=1` | 341 of 341 (full) | 2884.1 s | test_factory_repository test_language_skeletons test_matrix test_monorepos test_mutation_stamp_untouched |
| fault-a2-selected | 1ad28f9 | `time make test SINCE=52ecbd3` | 334 of 341 | 2804.5 s | test_factory_repository test_language_skeletons test_matrix test_monorepos test_mutation_stamp_untouched |
