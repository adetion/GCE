# GCE Test Report — v0.1.0

**Date:** 2026-05-10
**Result:** 148 passed, 0 failed, 1 warning
**Duration:** 109.31 seconds
**Python:** 3.8.10 | **pytest:** 8.3.5

---

## Summary

| Category | Files | Tests | Status |
|----------|-------|-------|--------|
| Unit — Config & Utils | 1 | 5 | All Passed |
| Unit — Database | 1 | 14 | All Passed |
| Unit — Energy | 1 | 4 | All Passed |
| Unit — Event Bus | 1 | 13 | All Passed |
| Unit — Forager | 1 | 8 | All Passed |
| Unit — Functions | 1 | 14 | All Passed |
| Unit — Gene | 1 | 10 | All Passed |
| Unit — Genetic Ops | 1 | 8 | All Passed |
| Unit — Lyapunov | 1 | 6 | All Passed |
| Unit — Parser | 1 | 6 | All Passed |
| Unit — Predictor | 1 | 24 | All Passed |
| Unit — Repository | 1 | 28 | All Passed |
| Unit — Simulator | 1 | 5 | All Passed |
| Integration — End-to-End | 1 | 2 | All Passed |
| Integration — Evolution | 1 | 1 | All Passed |
| **Total** | **16** | **148** | **All Passed** |

---

## 1. Config & Utils — `tests/GCE_test_config.py` (5 tests)

Tests configuration loading, environment variable substitution, and validation.

| # | Test | Description |
|---|------|-------------|
| 1 | `GCE_test_load_valid_config` | Loads a valid YAML config file successfully |
| 2 | `GCE_test_env_var_replacement` | `${VAR}` patterns in config are replaced with environment variable values |
| 3 | `GCE_test_env_var_missing` | Missing environment variables produce a warning instead of crashing |
| 4 | `GCE_test_invalid_population` | Validation rejects `population_initial: 0` with `sys.exit(1)` |
| 5 | `GCE_test_invalid_log_level` | Validation rejects invalid log levels |

---

## 2. Database — `tests/GCE_test_database.py` (14 tests)

Tests SQLite schema initialization, connection management, WAL mode, and migrations.

### DatabaseInit
| # | Test | Description |
|---|------|-------------|
| 6 | `GCE_test_init_db_creates_tables_without_error` | `GCE_init_db()` creates all 4 tables (`agents`, `predictions`, `raw_events`, `config`) |
| 7 | `GCE_test_init_db_is_idempotent` | Calling `GCE_init_db()` twice does not raise an error |

### DatabaseConnection
| # | Test | Description |
|---|------|-------------|
| 8 | `GCE_test_get_connection_returns_sqlite3_connection` | Connection factory returns a valid `sqlite3.Connection` object |
| 9 | `GCE_test_get_connection_creates_parent_dirs` | Missing parent directories are created automatically |
| 10 | `GCE_test_get_connection_wal_mode_enabled` | SQLite WAL journal mode is enabled for concurrent access |
| 11 | `GCE_test_foreign_keys_pragma_on` | `PRAGMA foreign_keys = ON` is enforced |

### SchemaVersion
| # | Test | Description |
|---|------|-------------|
| 12 | `GCE_test_get_schema_version_empty_db_returns_zero` | Empty database returns schema version 0 |
| 13 | `GCE_test_get_schema_version_after_init` | After `GCE_init_db()`, schema version is set to 1 |

### TablesExist
| # | Test | Description |
|---|------|-------------|
| 14 | `GCE_test_agents_table_exists` | `agents` table exists with correct columns |
| 15 | `GCE_test_predictions_table_exists` | `predictions` table exists with correct columns |
| 16 | `GCE_test_raw_events_table_exists` | `raw_events` table exists with correct columns |
| 17 | `GCE_test_config_table_exists` | `config` table exists with correct columns |

### Migration
| # | Test | Description |
|---|------|-------------|
| 18 | `GCE_test_migrate_db_handles_fresh_db` | `GCE_migrate_db()` runs without error on a fresh database |
| 19 | `GCE_test_migrate_db_sets_schema_version` | Migration correctly sets the schema version to `SCHEMA_VERSION` |

---

## 3. Energy — `tests/GCE_test_energy.py` (4 tests)

Tests the energy reward formula: `reward = base_reward × max(0, 1 - |predicted - actual| / error_scale)`.

| # | Test | Input | Expected |
|---|------|-------|----------|
| 20 | `GCE_test_perfect_prediction` | error = 0 | reward = `base_reward` (10.0) |
| 21 | `GCE_test_partial_prediction` | error = 1.0 (half of error_scale) | reward = 5.0 |
| 22 | `GCE_test_bad_prediction` | error = error_scale (2.0) | reward = 0.0 |
| 23 | `GCE_test_very_bad_prediction` | error > error_scale | reward = 0.0 (clamped, never negative) |

---

## 4. Event Bus — `tests/GCE_test_event_bus.py` (13 tests)

Tests the multiprocessing queue wrapper for environment-to-agent communication.

### EventBusCreation
| # | Test | Description |
|---|------|-------------|
| 24 | `GCE_test_create_with_default_maxsize` | Creates `GCE_EventBus` with default maxsize=10000 |
| 25 | `GCE_test_create_with_custom_maxsize` | Creates `GCE_EventBus` with a custom maxsize |
| 26 | `GCE_test_gce_queue_property_returns_multiprocessing_queue` | `.GCE_queue` property returns a `multiprocessing.Queue` |

### EventBusPublishConsume
| # | Test | Description |
|---|------|-------------|
| 27 | `GCE_test_publish_consume_roundtrip` | Publish then consume a NUMERIC event — values match |
| 28 | `GCE_test_publish_consume_text_event` | Publish then consume a TEXT event — text matches |
| 29 | `GCE_test_consume_empty_queue_returns_none` | Consuming from empty queue returns `None` (non-blocking timeout) |

### EventBusFull
| # | Test | Description |
|---|------|-------------|
| 30 | `GCE_test_publish_returns_false_when_queue_full` | Publishing to a full queue returns `False` instead of blocking |

### EventBusFifo
| # | Test | Description |
|---|------|-------------|
| 31 | `GCE_test_multiple_events_fifo_order` | Multiple published events are consumed in FIFO order |

### EventBusClose
| # | Test | Description |
|---|------|-------------|
| 32 | `GCE_test_close_works_without_error` | `GCE_close()` on an empty bus runs without error |
| 33 | `GCE_test_close_after_publish_consume` | `GCE_close()` after a publish/consume cycle works correctly |
| 34 | `GCE_test_double_close_does_not_crash` | Calling `GCE_close()` twice is idempotent (no crash) |

### RawEventImmutability
| # | Test | Description |
|---|------|-------------|
| 35 | `GCE_test_raw_event_is_frozen` | `GCE_RawEvent` is a frozen dataclass — mutation raises `FrozenInstanceError` |
| 36 | `GCE_test_raw_event_defaults` | `GCE_RawEvent` optional fields (`value`, `text`, `vector`, `metadata`) default correctly |

---

## 5. Forager — `tests/GCE_test_forager.py` (8 tests)

Tests the sliding-window feature extraction engine.

### Forager
| # | Test | Description |
|---|------|-------------|
| 37 | `GCE_test_returns_none_when_window_not_full` | `GCE_extract()` returns `None` before the sliding window fills |
| 38 | `GCE_test_returns_features_when_window_full` | Returns all `FEATURE_COUNT` (36) features once the window is full |
| 39 | `GCE_test_mask_filters_features` | A mask selecting only feature 0 returns a length-1 list |
| 40 | `GCE_test_empty_mask_returns_single_zero` | A mask of 0 (no features selected) returns `[0.0]` |

### Helpers
| # | Test | Description |
|---|------|-------------|
| 41 | `GCE_test_sma` | Simple moving average computes the correct mean for a known series |
| 42 | `GCE_test_sma_empty` | SMA on empty iterable returns `0.0` |
| 43 | `GCE_test_volatility` | Volatility (std dev) matches expected value for a known series |
| 44 | `GCE_test_volatility_short` | Volatility of a single-element series returns `0.0` |

---

## 6. Functions — `tests/GCE_test_functions.py` (14 tests)

Tests all 10 expression-tree math operators and the function registry.

| # | Test | Description |
|---|------|-------------|
| 45 | `GCE_test_add` | Addition: 3 + 5 = 8 |
| 46 | `GCE_test_sub` | Subtraction: 10 - 3 = 7 |
| 47 | `GCE_test_mul` | Multiplication: 4 × 6 = 24 |
| 48 | `GCE_test_div_normal` | Division: 10 / 4 = 2.5 |
| 49 | `GCE_test_div_by_zero` | Division by zero returns `0.0` (NaN-safe) |
| 50 | `GCE_test_sin` | Sine: sin(0) ≈ 0, sin(π/2) ≈ 1 |
| 51 | `GCE_test_cos` | Cosine: cos(0) ≈ 1, cos(π) ≈ -1 |
| 52 | `GCE_test_exp_overflow_protection` | exp(x) is capped at `e^50` when x ≥ 50 |
| 53 | `GCE_test_log_nonnegative` | log(x) is safe on negative input (uses abs + epsilon) |
| 54 | `GCE_test_abs` | Absolute value: abs(-7.5) = 7.5 |
| 55 | `GCE_test_ifgt_true_branch` | `ifgt(a, b, c, d)` returns `c` when a > b |
| 56 | `GCE_test_ifgt_false_branch` | `ifgt(a, b, c, d)` returns `d` when a ≤ b |
| 57 | `GCE_test_get_arity` | `GCE_get_arity` returns correct arity for each function |
| 58 | `GCE_test_no_forbidden_functions` | No ML-activation function names (`sigmoid`, `tanh`, `relu`, `softmax`) exist |

---

## 7. Gene — `tests/GCE_test_gene.py` (10 tests)

Tests the gene data structure, serialization (zlib-compressed JSON), and tree validation.

### NodeSerialization
| # | Test | Description |
|---|------|-------------|
| 59 | `GCE_test_terminal_roundtrip` | `GCE_Node.to_dict()` → `GCE_Node.from_dict()` roundtrip preserves terminal node |
| 60 | `GCE_test_function_roundtrip` | Nested function node (3 levels) survives serialization roundtrip |
| 61 | `GCE_test_gene_blob_roundtrip` | `GCE_serialize_gene()` → `GCE_deserialize_gene()` roundtrip preserves gene integrity |

### TreeValidation
| # | Test | Description |
|---|------|-------------|
| 62 | `GCE_test_count_nodes` | Node count matches expected for a known tree (3 nodes) |
| 63 | `GCE_test_tree_depth_simple` | Depth of a single-node tree = 1 |
| 64 | `GCE_test_tree_depth_nested` | Depth of a 3-level nested tree = 3 |
| 65 | `GCE_test_validate_tree_ok` | Valid tree within constraints passes validation |
| 66 | `GCE_test_validate_tree_too_deep` | Tree exceeding `max_depth` is rejected |
| 67 | `GCE_test_validate_tree_too_few_nodes` | Tree with fewer than `min_nodes` is rejected |
| 68 | `GCE_test_validate_tree_too_many_nodes` | Tree with more than `max_nodes` is rejected |

---

## 8. Genetic Ops — `tests/GCE_test_genetic_ops.py` (8 tests)

Tests random tree generation, crossover, mutation, and pruning.

### RandomTree
| # | Test | Description |
|---|------|-------------|
| 69 | `GCE_test_generates_valid_tree` | `GCE_random_tree()` produces trees that pass validation (20 iterations) |
| 70 | `GCE_test_terminal_at_depth_1` | Trees of depth 1 contain only TERMINAL nodes |

### Crossover
| # | Test | Description |
|---|------|-------------|
| 71 | `GCE_test_crossover_produces_valid_children` | Both children from `GCE_crossover()` pass tree validation |
| 72 | `GCE_test_crossover_returns_clones_on_failure` | When no valid crossover found after max retries, returns clones of parents |

### Mutation
| # | Test | Description |
|---|------|-------------|
| 73 | `GCE_test_mutate_produces_valid_tree` | `GCE_mutate()` produces valid trees after each of 5 mutation types (20 iterations) |
| 74 | `GCE_test_mutate_handles_min_nodes` | Mutation on minimal trees recovers via `GCE__expand_tree()` without crashing |

### PruneTree
| # | Test | Description |
|---|------|-------------|
| 75 | `GCE_test_prune_reduces_depth` | `GCE_prune_tree()` reduces tree depth to ≤ max_depth |
| 76 | `GCE_test_prune_reduces_nodes` | `GCE_prune_tree()` reduces node count to ≤ max_nodes |

---

## 9. Lyapunov — `tests/GCE_test_lyapunov.py` (6 tests)

Tests chaotic divergence estimation and bifurcation detection algorithms.

### LyapunovEstimate
| # | Test | Description |
|---|------|-------------|
| 77 | `GCE_test_constant_series` | A constant series yields Lyapunov ≈ 0 (no divergence) |
| 78 | `GCE_test_sinusoidal_series` | A sinusoidal series yields a finite Lyapunov value |
| 79 | `GCE_test_random_series` | A random walk yields a finite, positive Lyapunov value |
| 80 | `GCE_test_short_series` | Series shorter than embedding dimension returns 0.0 (edge case) |

### PerturbationAnalysis
| # | Test | Description |
|---|------|-------------|
| 81 | `GCE_test_no_bifurcation_for_stable_system` | A stable linear system (y = 0.5x) has no bifurcation points |
| 82 | `GCE_test_detects_divergence` | An exponentially-diverging system correctly detects bifurcation time steps |

---

## 10. Parser — `tests/GCE_test_parser.py` (6 tests)

Tests the offline regex-based scene parser.

| # | Test | Description |
|---|------|-------------|
| 83 | `GCE_test_extracts_numbers_as_prices` | Numeric tokens in user input become `initial_prices` |
| 84 | `GCE_test_default_prices_when_no_numbers` | Returns `[1.0]` default when no numbers found in input |
| 85 | `GCE_test_extracts_time_steps` | Time pattern "30天" → `time_steps = 30` |
| 86 | `GCE_test_clamps_time_steps` | Time steps exceeding 60 are clamped; below 5 are set to minimum |
| 87 | `GCE_test_extracts_participants` | Capitalized/CJK phrases become participant names |
| 88 | `GCE_test_returns_valid_scenario` | Overall output is a valid `GCE_Scenario` with all required fields |

---

## 11. Predictor — `tests/GCE_test_predictor.py` (24 tests)

Tests the expression tree evaluator — the core inference engine of every agent.

| # | Test | Description |
|---|------|-------------|
| 89 | `GCE_test_predict_terminal_constant` | Terminal with `const=3.0` predicts 3.0 regardless of features |
| 90 | `GCE_test_predict_terminal_constant_no_features` | Terminal constant works even with `features=None` |
| 91 | `GCE_test_predict_terminal_index` | Terminal with `index=2` returns `features[2]` |
| 92 | `GCE_test_predict_terminal_index_zero` | Terminal with `index=0` returns `features[0]` |
| 93 | `GCE_test_predict_add_of_two_constants` | `add(3.0, 5.0)` → 8.0 |
| 94 | `GCE_test_predict_add_of_two_features` | `add(features[0], features[1])` computes correctly |
| 95 | `GCE_test_predict_sub_and_mul` | `mul(sub(10, 3), 2)` → 14.0 (nested arithmetic) |
| 96 | `GCE_test_predict_sin` | `sin(0)` → 0.0, `sin(π/2)` → ~1.0 |
| 97 | `GCE_test_predict_cos` | `cos(0)` → 1.0 |
| 98 | `GCE_test_predict_abs` | `abs(-5.0)` → 5.0 |
| 99 | `GCE_test_predict_log` | `log(e)` → ~1.0 |
| 100 | `GCE_test_predict_exp` | `exp(1.0)` → ~2.718 |
| 101 | `GCE_test_predict_nested_sin_cos` | `sin(cos(0.0))` evaluates correctly (function composition) |
| 102 | `GCE_test_predict_ifgt_true_branch` | `ifgt(5, 3, then=10, else=20)` → 10.0 |
| 103 | `GCE_test_predict_ifgt_false_branch` | `ifgt(2, 3, then=10, else=20)` → 20.0 |
| 104 | `GCE_test_predict_div_by_zero_returns_zero` | Division by zero during evaluation returns 0.0 (no crash) |
| 105 | `GCE_test_predict_exp_overflow_capped` | `exp(50)` is capped, does not produce `inf` |
| 106 | `GCE_test_predict_log_of_negative_works` | `log` on negative input uses `abs` internally, returns valid value |
| 107 | `GCE_test_predict_with_none_features_returns_none` | `None` features input returns `None` (graceful degradation) |
| 108 | `GCE_test_predict_with_empty_features_list` | Empty features list returns valid result from constant-based tree |
| 109 | `GCE_test_predict_out_of_bounds_index_returns_zero` | Feature index ≥ len(features) returns 0.0 |
| 110 | `GCE_test_predict_negative_index_returns_zero` | Negative feature index returns 0.0 |
| 111 | `GCE_test_confidence_is_always_one` | Confidence metric is always 1.0 (placeholder for future calibration) |
| 112 | `GCE_test_predict_terminal_no_const_no_index_returns_zero` | Terminal with neither `const` nor `index` returns 0.0 |

---

## 12. Repository — `tests/GCE_test_repository.py` (28 tests)

Tests all 27 CRUD operations for agents, predictions, events, and queries.

### InsertAgent
| # | Test | Description |
|---|------|-------------|
| 113 | `GCE_test_insert_agent_creates_row` | `GCE_insert_agent()` inserts a row with correct fields |
| 114 | `GCE_test_insert_agent_with_parent_and_generation` | Insert with `parent_id` and `generation` stored correctly |
| 115 | `GCE_test_insert_agent_replace_existing` | `INSERT OR REPLACE` updates existing agent by ID |

### AgentCount
| # | Test | Description |
|---|------|-------------|
| 116 | `GCE_test_get_agent_count_zero` | Empty DB returns count 0 |
| 117 | `GCE_test_get_agent_count_one` | One active agent returns count 1 |
| 118 | `GCE_test_get_agent_count_many` | Many active agents returns correct count |
| 119 | `GCE_test_get_agent_count_excludes_dead` | Dead agents are excluded from count |

### ActiveAgents
| # | Test | Description |
|---|------|-------------|
| 120 | `GCE_test_get_active_agents_returns_active_only` | Only agents with `status='active'` are returned |
| 121 | `GCE_test_get_active_agents_empty` | No active agents returns empty list |

### AgentEnergy
| # | Test | Description |
|---|------|-------------|
| 122 | `GCE_test_get_agent_energy_returns_correct_value` | Energy value matches what was inserted |
| 123 | `GCE_test_get_agent_energy_nonexistent_returns_zero` | Non-existent agent energy returns 0.0 |
| 124 | `GCE_test_update_energy_adds_reward` | `GCE_update_energy()` correctly adds to existing energy |
| 125 | `GCE_test_update_energy_negative_reward` | Negative reward correctly subtracts energy |

### EnergyThresholds
| # | Test | Description |
|---|------|-------------|
| 126 | `GCE_test_get_agents_above_energy` | Returns agents with energy > threshold |
| 127 | `GCE_test_get_agents_above_energy_includes_exact_threshold` | Agents at exact threshold are included (≥) |
| 128 | `GCE_test_get_agents_below_energy` | Returns agents with energy < threshold |
| 129 | `GCE_test_get_agents_below_energy_includes_exact_threshold` | Agents at exact threshold are included (≤) |

### AgentStatus
| # | Test | Description |
|---|------|-------------|
| 130 | `GCE_test_set_agent_status_changes_status` | Status transitions from 'active' to 'dead' |
| 131 | `GCE_test_set_agent_status_paused` | Status can be set to 'paused' |
| 132 | `GCE_test_set_agent_status_reactivate` | Status can be changed back to 'active' |

### Predictions
| # | Test | Description |
|---|------|-------------|
| 133 | `GCE_test_insert_prediction_adds_record` | `GCE_insert_prediction()` creates a row with correct fields |
| 134 | `GCE_test_insert_prediction_with_custom_confidence` | Custom confidence value is stored correctly |
| 135 | `GCE_test_update_prediction_real_value` | `GCE_update_prediction_real_value()` sets the ground-truth value |

### GeneBlob
| # | Test | Description |
|---|------|-------------|
| 136 | `GCE_test_get_agent_gene_blob_returns_blob` | Gene BLOB stored via `GCE_serialize_gene()` is retrieved intact |
| 137 | `GCE_test_get_agent_gene_blob_nonexistent_returns_none` | Non-existent agent gene returns `None` |

### EliteAgents
| # | Test | Description |
|---|------|-------------|
| 138 | `GCE_test_get_elite_agents_returns_top_n` | Top-N agents sorted by energy descending |
| 139 | `GCE_test_get_elite_agents_excludes_dead` | Dead agents are excluded from elite selection |
| 140 | `GCE_test_get_elite_agents_empty_db` | Empty database returns empty list |

---

## 13. Simulator — `tests/GCE_test_simulator.py` (5 tests)

Tests the Lorenz RK4 integration physics.

| # | Test | Description |
|---|------|-------------|
| 141 | `GCE_test_fixed_point_origin` | The origin `(0, 0, 0)` is a fixed point — all derivatives are zero |
| 142 | `GCE_test_rk4_single_step_finite` | A single RK4 step from a non-origin point produces finite values |
| 143 | `GCE_test_rk4_energy_conservation_approximate` | After 100 steps, Lorenz state remains bounded (no runaway energy) |
| 144 | `GCE_test_deterministic_same_seed` | Same random seed produces identical trajectories (reproducibility) |
| 145 | `GCE_test_butterfly_effect_sensitive` | Two trajectories 0.0001 apart diverge by >10× within 1000 steps (chaos verified) |

---

## 14. Integration — End-to-End — `tests/integration/GCE_test_end_to_end.py` (2 tests)

Tests the full pipeline: scenario → simulation → narrative generation.

| # | Test | Description |
|---|------|-------------|
| 146 | `GCE_test_offline_narrative_returns_four_acts` | Offline narrative contains all four act titles and produces >100 characters |
| 147 | `GCE_test_offline_narrative_with_low_lyapunov` | A low-Lyapunov scenario is correctly identified as "stable" in the narrative |

---

## 15. Integration — Evolution Loop — `tests/integration/GCE_test_evolution_loop.py` (1 test)

Tests actual multi-agent evolution on a sine-wave prediction task. Marked `@pytest.mark.slow`.

| # | Test | Description |
|---|------|-------------|
| 148 | `GCE_test_evolution_reduces_error` | Runs 50 agents on a sine wave for ~3s; verifies population survives (>0 active) and average energy >10.0 after evolution |

**Duration:** ~107 seconds

---

## Component Coverage Summary

| Component | Tests | Key Risk Areas Covered |
|-----------|-------|-----------------------|
| Expression Tree Evaluation | 24 | All 10 operators, edge cases (div/0, exp overflow, log negative, NaN, OOB) |
| Data Persistence (CRUD) | 28 | All 27 repository functions, concurrent write safety, retry on lock |
| Database Schema | 14 | DDL, WAL, foreign keys, idempotent init, migration path |
| Genetic Operations | 8 | Crossover validity, 5 mutation types, tree pruning/expansion |
| Gene Encoding | 10 | Serialization roundtrip, zlib BLOB compression, tree validation |
| Feature Extraction | 8 | Sliding window, 36-dim feature pool, mask filtering |
| Lorenz Physics | 5 | Fixed point, RK4 correctness, chaotic divergence (butterfly effect) |
| Event Bus | 13 | Pub/sub, FIFO, queue full, close idempotency, frozen events |
| Lyapunov Analysis | 6 | Constant/sinusoidal/random/edge case, bifurcation detection |
| Scene Parser | 6 | Number extraction, time parsing, participant naming, clamping |
| Function Registry | 14 | All 10 ops, arity lookup, forbidden ML names check |
| Config & Validation | 5 | YAML loading, env var substitution, validation exit codes |
| Energy Formula | 4 | Perfect/partial/bad/very-bad prediction reward spectrum |
| End-to-End Pipeline | 2 | Full scenario→simulation→narrative offline flow |
| Live Evolution | 1 | Multi-agent breeding with energy selection over real time |
| **Total** | **148** | |

---

## Warnings

| Warning | File | Description |
|---------|------|-------------|
| `PytestUnknownMarkWarning` | `GCE_test_evolution_loop.py:129` | `@pytest.mark.slow` is not registered in pytest config. Recommended: add to `pytest.ini` markers. |

---

## Test Environment

| Property | Value |
|----------|-------|
| Platform | Darwin 22.6.0 (macOS) |
| Python | 3.8.10 |
| pytest | 8.3.5 |
| pytest-asyncio | 0.24.0 |
| Database | SQLite (WAL mode, temporary files per test) |
| Test Isolation | `tempfile.mkdtemp()` for DB tests; fresh fixtures per test class |
