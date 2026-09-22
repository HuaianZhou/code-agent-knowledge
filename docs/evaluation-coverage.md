# Evaluation coverage map

Test names refer to `tests/test_knowledge_agent.py` unless stated otherwise.

| Requirement | Executable coverage | Boundary |
|---|---|---|
| A → B ← C, cycles, deduplication | `test_bidirectional_graph_and_cycles`, `test_budgets_and_direction` | Deterministic graph behavior |
| Stable IDs after file/title changes | `test_renaming_and_metadata_only_updates`, `test_explicit_update_preserves_existing_path_and_records_intent` | No title-based identity |
| Combined filters before weight ordering | `test_combined_filters_precede_global_weight_order` | Added; full filtered set |
| Anchor isolation across repos | `test_anchor_lookup_isolates_same_path_across_repositories` | Added; same path/symbol |
| Added/changed/deleted indexed content | `test_incremental_delete_and_rebuild` | Markdown authoritative |
| Fresh vs incremental structure and queries | `test_incremental_and_fresh_index_have_equivalent_graph_and_queries` | Added; metadata, graph, anchors and result IDs |
| Interrupted/concurrent indexing | `test_interrupted_index_rolls_back`, `test_concurrent_index_writers` | Transactional snapshots |
| Proposal hidden until acceptance | `test_proposal_is_invisible_until_acceptance` | Added; default accepted retrieval |
| Team proposal hidden until remote main sync | `test_shared_proposal_push_is_not_accepted_until_remote_main_advances` | Added; external Git acceptance, not a tool feature |
| Local setup/review/accept | Existing setup/acceptance/stale-review tests | Real local Git repos |
| Semantic paraphrase retrieval | `python -m evaluation retrieval` | Requires real model; lexical diagnostic cannot pass |
| Admission, skill overlap, zero writes, uncertainty | `prepare-capture` cases + artifact scorer + independent scorecard | Needs actual isolated coding-agent runs |
| Reuse and relationship construction | `paraphrase`, `shared_constraint` cases | Actual stable IDs/edges plus semantic review |
| Genuine condition change | `changed_conditions` maintenance case | Real v1→v2 fixture diff; independent semantic review |
| No knowledge vs flat vs graph | `prepare-reuse`, `run`, `summarize-reuse` | Controlled retrieval, fresh container per trial |
| Evaluation validity itself | `tests/test_evaluation.py` | Mount plans, provenance, budgets, no false semantic pass, artifact scoring and grader calibration |

Do not count prepared trials, a lexical diagnostic, a mocked adapter or a manually
authored node as a completed real-agent or semantic-search evaluation. See
`docs/validation.md` for the actual execution record.
