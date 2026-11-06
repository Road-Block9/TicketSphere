# Graph Report - A Capstone  (2026-11-06)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 516 nodes · 1046 edges · 29 communities (20 shown, 9 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 6 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `bddc3ebc`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4
- Community 5
- Community 6
- Community 7
- Community 8
- Community 9
- Community 10
- Community 11
- Community 12
- Community 13
- Community 14
- Community 15
- Community 16
- Community 17
- Community 18
- Community 19
- Community 20
- Community 21
- Community 22
- Community 23
- Community 24
- Community 25

## God Nodes (most connected - your core abstractions)
1. `init_db()` - 35 edges
2. `read_csv_tickets()` - 33 edges
3. `clean_and_transform_tickets()` - 33 edges
4. `get_ticket_count()` - 29 edges
5. `get_all_analytics_kpis()` - 28 edges
6. `insert_tickets()` - 26 edges
7. `run_csv_pipeline()` - 26 edges
8. `generate_support_insights_report()` - 24 edges
9. `execute_query()` - 19 edges
10. `fetch_tickets_from_api()` - 15 edges

## Surprising Connections (you probably didn't know these)
- `test_generate_fallback_report()` --uses--> `GenAIReportResult`  [INFERRED]
  tests/test_genai.py → src/genai_assistant.py
- `analytics_db()` --calls--> `init_db()`  [EXTRACTED]
  tests/test_analytics.py → src/database.py
- `temp_db()` --calls--> `init_db()`  [EXTRACTED]
  tests/test_csv_variations.py → src/database.py
- `isolated_e2e_env()` --calls--> `init_db()`  [EXTRACTED]
  tests/test_e2e_workflow.py → src/database.py
- `temp_db()` --calls--> `init_db()`  [EXTRACTED]
  tests/test_database.py → src/database.py

## Import Cycles
- None detected.

## Communities (29 total, 9 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.06
Nodes (48): dependencies, lucide-react@^1.66.0, react@^19.3.1, react-dom@^19.3.1, react-markdown@^10.1.0, recharts@^3.10.1, remark-gfm@^4.0.1, devDependencies (+40 more)

### Community 1 - "Community 1"
Cohesion: 0.08
Nodes (22): _build_filter_clause(), format_analytics_summary_text(), get_all_analytics_kpis(), query_category_distribution(), query_management_attention_tickets(), query_resolution_time_metrics(), query_status_distribution(), query_ticket_volume_trends() (+14 more)

### Community 2 - "Community 2"
Cohesion: 0.07
Nodes (12): clean_and_transform_tickets(), DataQualityReport, parse_datetime_series(), test_clean_sample_dataset(), test_duplicate_ticket_removal(), test_false_resolution_date_cleared_for_open_tickets(), test_missing_string_imputation(), test_missing_ticket_id_rejection() (+4 more)

### Community 3 - "Community 3"
Cohesion: 0.07
Nodes (15): read_csv_tickets(), test_column_aliases_and_case_insensitivity(), test_explore_my_data_dataset_no_invalid_comparison_error(), test_how_to_csv_sample_dataset(), test_mixed_timezone_and_date_formats(), test_ingestion_empty_file(), test_ingestion_header_only_file(), test_ingestion_missing_required_columns() (+7 more)

### Community 4 - "Community 4"
Cohesion: 0.06
Nodes (20): args, chrome, [url, out, label], args, chrome, file, frames, [frameX = 0, frameY = 0, frameWidth = 960] (+12 more)

### Community 5 - "Community 5"
Cohesion: 0.10
Nodes (13): build_grounded_prompt(), GenAIReportResult, generate_fallback_report(), generate_support_insights_report(), test_genai_empty_database_fallback(), sample_kpis(), test_build_grounded_prompt(), test_empty_kpis_handling() (+5 more)

### Community 6 - "Community 6"
Cohesion: 0.09
Nodes (7): inspect_dataset(), normalize_column_name(), get_tickets(), health_check(), run_mock_server(), test_column_name_normalization(), test_column_alias_normalization()

### Community 7 - "Community 7"
Cohesion: 0.15
Nodes (7): get_all_tickets(), get_connection(), get_db_path(), init_db(), test_get_all_tickets_retrieval(), test_ingestion_log_recording(), test_init_db_creates_tables()

### Community 8 - "Community 8"
Cohesion: 0.11
Nodes (8): df_to_records(), generate_report(), get_kpis(), health(), ingest_api(), ingest_csv(), list_tickets(), run_flask()

### Community 9 - "Community 9"
Cohesion: 0.15
Nodes (9): run_api_pipeline(), run_csv_pipeline(), run_full_pipeline_cycle(), test_run_api_pipeline_error_handling(), test_run_csv_pipeline_duplicate_prevention(), test_run_csv_pipeline_empty_file_handling(), test_run_csv_pipeline_missing_columns(), test_run_csv_pipeline_success() (+1 more)

### Community 10 - "Community 10"
Cohesion: 0.09
Nodes (10): client(), test_flask_ai_report_endpoint(), test_flask_analytics_kpis_endpoint(), test_flask_analytics_kpis_filtered(), test_flask_csv_upload_missing_file(), test_flask_csv_upload_sample_dataset(), test_flask_csv_upload_valid_file(), test_flask_csv_upload_validation_error_details() (+2 more)

### Community 11 - "Community 11"
Cohesion: 0.11
Nodes (7): api_test_client(), test_api_client_timeout_handling(), test_api_client_unauthorized_error(), test_mock_api_get_tickets(), test_mock_api_health_endpoint(), test_mock_api_invalid_api_key(), test_mock_api_status_filtering()

### Community 12 - "Community 12"
Cohesion: 0.17
Nodes (7): insert_tickets(), analytics_db(), test_database_insert_empty_dataframe(), test_database_sql_injection_resilience(), test_genai_api_exception_fallback(), test_genai_missing_key_deterministic_fallback(), test_transformation_all_rejected_rows()

### Community 13 - "Community 13"
Cohesion: 0.12
Nodes (7): test_api_client_http_500_response(), test_api_client_timeout_handling(), test_flask_api_ingest_bad_endpoint(), test_flask_csv_upload_corrupted_data(), test_flask_csv_upload_empty_filename(), test_flask_tickets_filtering_no_matches(), test_transformation_corrupted_timestamps()

### Community 14 - "Community 14"
Cohesion: 0.15
Nodes (5): ApiIngestionResult, fetch_tickets_from_api(), test_api_client_connection_error_handling(), test_api_client_fetch_success(), test_api_client_connection_error()

### Community 15 - "Community 15"
Cohesion: 0.18
Nodes (4): temp_db(), test_database_persistence_and_duplicate_id_safety(), test_flask_api_upload_both_datasets(), test_genai_assistant_grounding_and_fallback_fidelity()

### Community 16 - "Community 16"
Cohesion: 0.20
Nodes (5): get_ticket_count(), test_duplicate_detection_and_idempotent_ingestion(), test_kaggle_missing_created_at_validation_error(), test_duplicate_prevention_on_repeated_import(), test_insert_tickets_success()

### Community 18 - "Community 18"
Cohesion: 0.29
Nodes (3): ingest_api_pipeline(), test_end_to_end_api_ingestion_pipeline(), test_api_pipeline_empty_ticket_list()

### Community 19 - "Community 19"
Cohesion: 0.33
Nodes (5): plugins, rules, react/only-export-components, react/rules-of-hooks, $schema

### Community 20 - "Community 20"
Cohesion: 0.40
Nodes (4): interface, default_prompt, display_name, short_description

## Knowledge Gaps
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `init_db()` connect `Community 7` to `Community 1`, `Community 5`, `Community 8`, `Community 9`, `Community 10`, `Community 11`, `Community 12`, `Community 13`, `Community 14`, `Community 15`, `Community 16`, `Community 17`, `Community 18`, `Community 21`, `Community 22`, `Community 25`?**
  _High betweenness centrality (0.069) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `clean_and_transform_tickets()` (e.g. with `normalize_category()` and `normalize_priority()`) actually correct?**
  _`clean_and_transform_tickets()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.059395801331285206 - nodes in this community are weakly interconnected._
- **Why does `read_csv_tickets()` connect `Community 3` to `Community 2`, `Community 6`, `Community 7`, `Community 8`, `Community 9`, `Community 12`, `Community 13`, `Community 15`, `Community 16`, `Community 24`?**
  _High betweenness centrality (0.054) - this node is a cross-community bridge._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.0815686274509804 - nodes in this community are weakly interconnected._
- **Why does `get_all_analytics_kpis()` connect `Community 1` to `Community 5`, `Community 7`, `Community 8`, `Community 9`, `Community 12`, `Community 13`, `Community 15`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **Should `Community 2` be split into smaller, more focused modules?**
  _Cohesion score 0.07057057057057058 - nodes in this community are weakly interconnected._