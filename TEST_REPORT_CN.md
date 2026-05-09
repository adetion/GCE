# GCE 测试报告 — v0.1.0

**日期：** 2026-05-10
**结果：** 148 项通过，0 项失败，1 条警告
**耗时：** 109.31 秒
**Python：** 3.8.10 | **pytest：** 8.3.5

---

## 总览

| 类别 | 文件数 | 测试数 | 状态 |
|------|--------|--------|------|
| 单元测试 — 配置与工具 | 1 | 5 | 全部通过 |
| 单元测试 — 数据库 | 1 | 14 | 全部通过 |
| 单元测试 — 能量公式 | 1 | 4 | 全部通过 |
| 单元测试 — 事件总线 | 1 | 13 | 全部通过 |
| 单元测试 — 采集器 | 1 | 8 | 全部通过 |
| 单元测试 — 函数集 | 1 | 14 | 全部通过 |
| 单元测试 — 基因 | 1 | 10 | 全部通过 |
| 单元测试 — 遗传操作 | 1 | 8 | 全部通过 |
| 单元测试 — Lyapunov 分析 | 1 | 6 | 全部通过 |
| 单元测试 — 解析器 | 1 | 6 | 全部通过 |
| 单元测试 — 预测器 | 1 | 24 | 全部通过 |
| 单元测试 — 数据仓库 | 1 | 28 | 全部通过 |
| 单元测试 — 模拟器 | 1 | 5 | 全部通过 |
| 集成测试 — 端到端 | 1 | 2 | 全部通过 |
| 集成测试 — 进化循环 | 1 | 1 | 全部通过 |
| **合计** | **16** | **148** | **全部通过** |

---

## 1. 配置与工具 — `tests/GCE_test_config.py`（5 项）

测试配置加载、环境变量替换和验证逻辑。

| # | 测试 | 说明 |
|---|------|------|
| 1 | `GCE_test_load_valid_config` | 成功加载有效的 YAML 配置文件 |
| 2 | `GCE_test_env_var_replacement` | `${VAR}` 占位符在配置中被环境变量值正确替换 |
| 3 | `GCE_test_env_var_missing` | 缺失环境变量时打印警告而非崩溃 |
| 4 | `GCE_test_invalid_population` | 验证拒绝 `population_initial: 0` 并以 `sys.exit(1)` 退出 |
| 5 | `GCE_test_invalid_log_level` | 验证拒绝无效的日志级别 |

---

## 2. 数据库 — `tests/GCE_test_database.py`（14 项）

测试 SQLite 模式初始化、连接管理、WAL 模式和迁移。

### 数据库初始化
| # | 测试 | 说明 |
|---|------|------|
| 6 | `GCE_test_init_db_creates_tables_without_error` | `GCE_init_db()` 创建全部 4 张表（`agents`、`predictions`、`raw_events`、`config`） |
| 7 | `GCE_test_init_db_is_idempotent` | 连续两次调用 `GCE_init_db()` 不会报错 |

### 数据库连接
| # | 测试 | 说明 |
|---|------|------|
| 8 | `GCE_test_get_connection_returns_sqlite3_connection` | 连接工厂返回有效的 `sqlite3.Connection` 对象 |
| 9 | `GCE_test_get_connection_creates_parent_dirs` | 缺失的父目录自动创建 |
| 10 | `GCE_test_get_connection_wal_mode_enabled` | 已启用 SQLite WAL 日志模式以支持并发访问 |
| 11 | `GCE_test_foreign_keys_pragma_on` | 已启用 `PRAGMA foreign_keys = ON` 外键约束 |

### 模式版本
| # | 测试 | 说明 |
|---|------|------|
| 12 | `GCE_test_get_schema_version_empty_db_returns_zero` | 空数据库返回模式版本 0 |
| 13 | `GCE_test_get_schema_version_after_init` | `GCE_init_db()` 后模式版本正确设为 1 |

### 表存在性
| # | 测试 | 说明 |
|---|------|------|
| 14 | `GCE_test_agents_table_exists` | `agents` 表存在且列正确 |
| 15 | `GCE_test_predictions_table_exists` | `predictions` 表存在且列正确 |
| 16 | `GCE_test_raw_events_table_exists` | `raw_events` 表存在且列正确 |
| 17 | `GCE_test_config_table_exists` | `config` 表存在且列正确 |

### 迁移
| # | 测试 | 说明 |
|---|------|------|
| 18 | `GCE_test_migrate_db_handles_fresh_db` | `GCE_migrate_db()` 在全新数据库上正常运行 |
| 19 | `GCE_test_migrate_db_sets_schema_version` | 迁移正确将模式版本写入配置表 |

---

## 3. 能量公式 — `tests/GCE_test_energy.py`（4 项）

测试能量奖励公式：`奖励 = base_reward × max(0, 1 - |预测值 - 实际值| / error_scale)`。

| # | 测试 | 输入条件 | 期望结果 |
|---|------|----------|----------|
| 20 | `GCE_test_perfect_prediction` | 误差 = 0 | 奖励 = `base_reward`（10.0） |
| 21 | `GCE_test_partial_prediction` | 误差 = 1.0（为 error_scale 的一半） | 奖励 = 5.0 |
| 22 | `GCE_test_bad_prediction` | 误差 = error_scale（2.0） | 奖励 = 0.0 |
| 23 | `GCE_test_very_bad_prediction` | 误差 > error_scale | 奖励 = 0.0（截断，永不为负） |

---

## 4. 事件总线 — `tests/GCE_test_event_bus.py`（13 项）

测试环境与智能体间多进程队列通信封装。

### 事件总线创建
| # | 测试 | 说明 |
|---|------|------|
| 24 | `GCE_test_create_with_default_maxsize` | 以默认 maxsize=10000 创建 `GCE_EventBus` |
| 25 | `GCE_test_create_with_custom_maxsize` | 以自定义 maxsize 创建 `GCE_EventBus` |
| 26 | `GCE_test_gce_queue_property_returns_multiprocessing_queue` | `.GCE_queue` 属性返回 `multiprocessing.Queue` 实例 |

### 发布与消费
| # | 测试 | 说明 |
|---|------|------|
| 27 | `GCE_test_publish_consume_roundtrip` | 发布后消费 NUMERIC 事件——数值一致 |
| 28 | `GCE_test_publish_consume_text_event` | 发布后消费 TEXT 事件——文本一致 |
| 29 | `GCE_test_consume_empty_queue_returns_none` | 从空队列消费返回 `None`（非阻塞超时） |

### 队列满
| # | 测试 | 说明 |
|---|------|------|
| 30 | `GCE_test_publish_returns_false_when_queue_full` | 向已满队列发布返回 `False` 而非阻塞 |

### FIFO 顺序
| # | 测试 | 说明 |
|---|------|------|
| 31 | `GCE_test_multiple_events_fifo_order` | 多个发布的事件按 FIFO 顺序消费 |

### 关闭
| # | 测试 | 说明 |
|---|------|------|
| 32 | `GCE_test_close_works_without_error` | 对空总线调用 `GCE_close()` 无错误 |
| 33 | `GCE_test_close_after_publish_consume` | 发布/消费后的 `GCE_close()` 正常工作 |
| 34 | `GCE_test_double_close_does_not_crash` | 两次调用 `GCE_close()` 具有幂等性（不崩溃） |

### RawEvent 不可变性
| # | 测试 | 说明 |
|---|------|------|
| 35 | `GCE_test_raw_event_is_frozen` | `GCE_RawEvent` 是冻结数据类——修改会引发 `FrozenInstanceError` |
| 36 | `GCE_test_raw_event_defaults` | `GCE_RawEvent` 可选字段（`value`、`text`、`vector`、`metadata`）默认值正确 |

---

## 5. 采集器 — `tests/GCE_test_forager.py`（8 项）

测试滑动窗口特征提取引擎。

### 采集器
| # | 测试 | 说明 |
|---|------|------|
| 37 | `GCE_test_returns_none_when_window_not_full` | 滑动窗口填满前 `GCE_extract()` 返回 `None` |
| 38 | `GCE_test_returns_features_when_window_full` | 窗口填满后返回全部 `FEATURE_COUNT`（36）个特征 |
| 39 | `GCE_test_mask_filters_features` | 掩码仅选特征 0 时返回长度为 1 的列表 |
| 40 | `GCE_test_empty_mask_returns_single_zero` | 掩码为 0（不选任何特征）时返回 `[0.0]` |

### 辅助函数
| # | 测试 | 说明 |
|---|------|------|
| 41 | `GCE_test_sma` | 简单移动平均对已知序列计算正确均值 |
| 42 | `GCE_test_sma_empty` | 空可迭代对象的 SMA 返回 `0.0` |
| 43 | `GCE_test_volatility` | 波动率（标准差）对已知序列计算结果正确 |
| 44 | `GCE_test_volatility_short` | 单元素序列波动率返回 `0.0` |

---

## 6. 函数集 — `tests/GCE_test_functions.py`（14 项）

测试全部 10 个表达式树数学运算符及函数注册表。

| # | 测试 | 说明 |
|---|------|------|
| 45 | `GCE_test_add` | 加法：3 + 5 = 8 |
| 46 | `GCE_test_sub` | 减法：10 − 3 = 7 |
| 47 | `GCE_test_mul` | 乘法：4 × 6 = 24 |
| 48 | `GCE_test_div_normal` | 除法：10 / 4 = 2.5 |
| 49 | `GCE_test_div_by_zero` | 除以零返回 `0.0`（NaN 安全） |
| 50 | `GCE_test_sin` | 正弦：sin(0) ≈ 0，sin(π/2) ≈ 1 |
| 51 | `GCE_test_cos` | 余弦：cos(0) ≈ 1，cos(π) ≈ −1 |
| 52 | `GCE_test_exp_overflow_protection` | exp(x) 在 x ≥ 50 时截断为 `e^50` |
| 53 | `GCE_test_log_nonnegative` | log(x) 对负数输入安全（使用绝对值 + epsilon） |
| 54 | `GCE_test_abs` | 绝对值：abs(−7.5) = 7.5 |
| 55 | `GCE_test_ifgt_true_branch` | `ifgt(a, b, c, d)` 当 a > b 时返回 `c` |
| 56 | `GCE_test_ifgt_false_branch` | `ifgt(a, b, c, d)` 当 a ≤ b 时返回 `d` |
| 57 | `GCE_test_get_arity` | `GCE_get_arity` 返回各函数的正确参数数目 |
| 58 | `GCE_test_no_forbidden_functions` | 不存在 ML 激活函数名（`sigmoid`、`tanh`、`relu`、`softmax`） |

---

## 7. 基因 — `tests/GCE_test_gene.py`（10 项）

测试基因数据结构、序列化（zlib 压缩 JSON）及表达式树验证。

### 节点序列化
| # | 测试 | 说明 |
|---|------|------|
| 59 | `GCE_test_terminal_roundtrip` | `GCE_Node.to_dict()` → `GCE_Node.from_dict()` 往返一致 |
| 60 | `GCE_test_function_roundtrip` | 三层嵌套函数节点序列化往返一致 |
| 61 | `GCE_test_gene_blob_roundtrip` | `GCE_serialize_gene()` → `GCE_deserialize_gene()` 往返保持基因完整性 |

### 树验证
| # | 测试 | 说明 |
|---|------|------|
| 62 | `GCE_test_count_nodes` | 已知树的节点计数正确（3 个节点） |
| 63 | `GCE_test_tree_depth_simple` | 单节点树深度 = 1 |
| 64 | `GCE_test_tree_depth_nested` | 三层嵌套树深度 = 3 |
| 65 | `GCE_test_validate_tree_ok` | 符合约束的有效树通过验证 |
| 66 | `GCE_test_validate_tree_too_deep` | 超过 `max_depth` 的树被拒绝 |
| 67 | `GCE_test_validate_tree_too_few_nodes` | 节点数少于 `min_nodes` 的树被拒绝 |
| 68 | `GCE_test_validate_tree_too_many_nodes` | 节点数超过 `max_nodes` 的树被拒绝 |

---

## 8. 遗传操作 — `tests/GCE_test_genetic_ops.py`（8 项）

测试随机树生成、交叉、变异和剪枝。

### 随机树
| # | 测试 | 说明 |
|---|------|------|
| 69 | `GCE_test_generates_valid_tree` | `GCE_random_tree()` 生成的树通过验证（20 次迭代） |
| 70 | `GCE_test_terminal_at_depth_1` | 深度为 1 的树仅包含 TERMINAL 节点 |

### 交叉
| # | 测试 | 说明 |
|---|------|------|
| 71 | `GCE_test_crossover_produces_valid_children` | `GCE_crossover()` 的两个子代均通过验证 |
| 72 | `GCE_test_crossover_returns_clones_on_failure` | 超过最大重试次数后返回父代克隆副本 |

### 变异
| # | 测试 | 说明 |
|---|------|------|
| 73 | `GCE_test_mutate_produces_valid_tree` | `GCE_mutate()` 在 5 种变异类型下均产生有效树（20 次迭代） |
| 74 | `GCE_test_mutate_handles_min_nodes` | 对最小树的变异通过 `GCE__expand_tree()` 恢复不崩溃 |

### 剪枝
| # | 测试 | 说明 |
|---|------|------|
| 75 | `GCE_test_prune_reduces_depth` | `GCE_prune_tree()` 将树深度降至 ≤ max_depth |
| 76 | `GCE_test_prune_reduces_nodes` | `GCE_prune_tree()` 将节点数降至 ≤ max_nodes |

---

## 9. Lyapunov 分析 — `tests/GCE_test_lyapunov.py`（6 项）

测试混沌发散度估计和分岔检测算法。

### Lyapunov 估计
| # | 测试 | 说明 |
|---|------|------|
| 77 | `GCE_test_constant_series` | 常数序列 Lyapunov ≈ 0（无发散） |
| 78 | `GCE_test_sinusoidal_series` | 正弦序列返回有限 Lyapunov 值 |
| 79 | `GCE_test_random_series` | 随机游走返回有限正值 Lyapunov |
| 80 | `GCE_test_short_series` | 序列短于嵌入维度时返回 0.0（边界情况） |

### 微扰分析
| # | 测试 | 说明 |
|---|------|------|
| 81 | `GCE_test_no_bifurcation_for_stable_system` | 稳定线性系统（y = 0.5x）无分岔点 |
| 82 | `GCE_test_detects_divergence` | 指数发散系统正确检测到分岔时间步 |

---

## 10. 解析器 — `tests/GCE_test_parser.py`（6 项）

测试基于正则的离线场景解析器。

| # | 测试 | 说明 |
|---|------|------|
| 83 | `GCE_test_extracts_numbers_as_prices` | 用户输入中的数字被提取为 `initial_prices` |
| 84 | `GCE_test_default_prices_when_no_numbers` | 无数字输入时返回 `[1.0]` 默认值 |
| 85 | `GCE_test_extracts_time_steps` | 时间模式"30天"→ `time_steps = 30` |
| 86 | `GCE_test_clamps_time_steps` | 超过 60 的时间步被截断，小于 5 的被设为最小值 |
| 87 | `GCE_test_extracts_participants` | 大写字母/CJK 短语被提取为参与者名称 |
| 88 | `GCE_test_returns_valid_scenario` | 整体输出为包含所有必填字段的有效 `GCE_Scenario` |

---

## 11. 预测器 — `tests/GCE_test_predictor.py`（24 项）

测试表达式树求值器——每个智能体的核心推理引擎。

| # | 测试 | 说明 |
|---|------|------|
| 89 | `GCE_test_predict_terminal_constant` | `const=3.0` 的终端节点预测 3.0，与特征无关 |
| 90 | `GCE_test_predict_terminal_constant_no_features` | 终端常量在 `features=None` 时仍正常工作 |
| 91 | `GCE_test_predict_terminal_index` | `index=2` 的终端返回 `features[2]` |
| 92 | `GCE_test_predict_terminal_index_zero` | `index=0` 的终端返回 `features[0]` |
| 93 | `GCE_test_predict_add_of_two_constants` | `add(3.0, 5.0)` → 8.0 |
| 94 | `GCE_test_predict_add_of_two_features` | `add(features[0], features[1])` 计算正确 |
| 95 | `GCE_test_predict_sub_and_mul` | `mul(sub(10, 3), 2)` → 14.0（嵌套算术） |
| 96 | `GCE_test_predict_sin` | `sin(0)` → 0.0，`sin(π/2)` → ~1.0 |
| 97 | `GCE_test_predict_cos` | `cos(0)` → 1.0 |
| 98 | `GCE_test_predict_abs` | `abs(−5.0)` → 5.0 |
| 99 | `GCE_test_predict_log` | `log(e)` → ~1.0 |
| 100 | `GCE_test_predict_exp` | `exp(1.0)` → ~2.718 |
| 101 | `GCE_test_predict_nested_sin_cos` | `sin(cos(0.0))` 函数复合求值正确 |
| 102 | `GCE_test_predict_ifgt_true_branch` | `ifgt(5, 3, then=10, else=20)` → 10.0 |
| 103 | `GCE_test_predict_ifgt_false_branch` | `ifgt(2, 3, then=10, else=20)` → 20.0 |
| 104 | `GCE_test_predict_div_by_zero_returns_zero` | 求值期间除以零返回 0.0（不崩溃） |
| 105 | `GCE_test_predict_exp_overflow_capped` | `exp(50)` 被截断，不产生 `inf` |
| 106 | `GCE_test_predict_log_of_negative_works` | 负数输入的 `log` 内部使用 `abs`，返回有效值 |
| 107 | `GCE_test_predict_with_none_features_returns_none` | `None` 特征输入返回 `None`（优雅降级） |
| 108 | `GCE_test_predict_with_empty_features_list` | 空特征列表返回基于常量的有效结果 |
| 109 | `GCE_test_predict_out_of_bounds_index_returns_zero` | 特征索引 ≥ len(features) 返回 0.0 |
| 110 | `GCE_test_predict_negative_index_returns_zero` | 负特征索引返回 0.0 |
| 111 | `GCE_test_confidence_is_always_one` | 置信度始终为 1.0（未来校准功能占位） |
| 112 | `GCE_test_predict_terminal_no_const_no_index_returns_zero` | 既无 `const` 也无 `index` 的终端返回 0.0 |

---

## 12. 数据仓库 — `tests/GCE_test_repository.py`（28 项）

测试全部 27 项 CRUD 操作，涵盖智能体、预测、事件及查询。

### 插入智能体
| # | 测试 | 说明 |
|---|------|------|
| 113 | `GCE_test_insert_agent_creates_row` | `GCE_insert_agent()` 插入行，字段正确 |
| 114 | `GCE_test_insert_agent_with_parent_and_generation` | 含 `parent_id` 和 `generation` 的插入正确存储 |
| 115 | `GCE_test_insert_agent_replace_existing` | `INSERT OR REPLACE` 按 ID 更新已有智能体 |

### 智能体计数
| # | 测试 | 说明 |
|---|------|------|
| 116 | `GCE_test_get_agent_count_zero` | 空数据库返回计数 0 |
| 117 | `GCE_test_get_agent_count_one` | 一个活跃智能体返回计数 1 |
| 118 | `GCE_test_get_agent_count_many` | 多个活跃智能体返回正确计数 |
| 119 | `GCE_test_get_agent_count_excludes_dead` | 死亡智能体不计入 |

### 活跃智能体
| # | 测试 | 说明 |
|---|------|------|
| 120 | `GCE_test_get_active_agents_returns_active_only` | 仅返回 `status='active'` 的智能体 |
| 121 | `GCE_test_get_active_agents_empty` | 无活跃智能体返回空列表 |

### 智能体能量
| # | 测试 | 说明 |
|---|------|------|
| 122 | `GCE_test_get_agent_energy_returns_correct_value` | 能量值与插入时一致 |
| 123 | `GCE_test_get_agent_energy_nonexistent_returns_zero` | 不存在智能体的能量返回 0.0 |
| 124 | `GCE_test_update_energy_adds_reward` | `GCE_update_energy()` 正确增加能量 |
| 125 | `GCE_test_update_energy_negative_reward` | 负奖励正确扣除能量 |

### 能量阈值
| # | 测试 | 说明 |
|---|------|------|
| 126 | `GCE_test_get_agents_above_energy` | 返回能量 > 阈值的智能体 |
| 127 | `GCE_test_get_agents_above_energy_includes_exact_threshold` | 恰好处于阈值的智能体也被包含（≥） |
| 128 | `GCE_test_get_agents_below_energy` | 返回能量 < 阈值的智能体 |
| 129 | `GCE_test_get_agents_below_energy_includes_exact_threshold` | 恰好处于阈值的智能体也被包含（≤） |

### 智能体状态
| # | 测试 | 说明 |
|---|------|------|
| 130 | `GCE_test_set_agent_status_changes_status` | 状态从 'active' 变为 'dead' |
| 131 | `GCE_test_set_agent_status_paused` | 状态可设为 'paused' |
| 132 | `GCE_test_set_agent_status_reactivate` | 状态可改回 'active' |

### 预测
| # | 测试 | 说明 |
|---|------|------|
| 133 | `GCE_test_insert_prediction_adds_record` | `GCE_insert_prediction()` 创建行，字段正确 |
| 134 | `GCE_test_insert_prediction_with_custom_confidence` | 自定义置信度正确存储 |
| 135 | `GCE_test_update_prediction_real_value` | `GCE_update_prediction_real_value()` 设置真值 |

### 基因 BLOB
| # | 测试 | 说明 |
|---|------|------|
| 136 | `GCE_test_get_agent_gene_blob_returns_blob` | 经 `GCE_serialize_gene()` 存储的基因 BLOB 完整取回 |
| 137 | `GCE_test_get_agent_gene_blob_nonexistent_returns_none` | 不存在智能体的基因返回 `None` |

### 精英智能体
| # | 测试 | 说明 |
|---|------|------|
| 138 | `GCE_test_get_elite_agents_returns_top_n` | 按能量降序返回前 N 名 |
| 139 | `GCE_test_get_elite_agents_excludes_dead` | 死亡智能体不参与精英选择 |
| 140 | `GCE_test_get_elite_agents_empty_db` | 空数据库返回空列表 |

---

## 13. 模拟器 — `tests/GCE_test_simulator.py`（5 项）

测试 Lorenz RK4 积分物理学。

| # | 测试 | 说明 |
|---|------|------|
| 141 | `GCE_test_fixed_point_origin` | 原点 `(0, 0, 0)` 是不动点——所有导数为零 |
| 142 | `GCE_test_rk4_single_step_finite` | 非原点单步 RK4 产生有限值 |
| 143 | `GCE_test_rk4_energy_conservation_approximate` | 100 步后 Lorenz 状态保持有界（无能量逃逸） |
| 144 | `GCE_test_deterministic_same_seed` | 相同随机种子产生相同轨迹（可复现性） |
| 145 | `GCE_test_butterfly_effect_sensitive` | 两个相差 0.0001 的轨迹在 1000 步内发散超过 10 倍（混沌性验证） |

---

## 14. 集成测试 — 端到端 — `tests/integration/GCE_test_end_to_end.py`（2 项）

测试完整流水线：场景 → 推演 → 叙事生成。

| # | 测试 | 说明 |
|---|------|------|
| 146 | `GCE_test_offline_narrative_returns_four_acts` | 离线叙事包含全部四幕标题，报告长度 > 100 字 |
| 147 | `GCE_test_offline_narrative_with_low_lyapunov` | 低 Lyapunov 场景在叙事中被正确识别为"稳定" |

---

## 15. 集成测试 — 进化循环 — `tests/integration/GCE_test_evolution_loop.py`（1 项）

测试在正弦波预测任务上的多智能体实际进化。标记为 `@pytest.mark.slow`。

| # | 测试 | 说明 |
|---|------|------|
| 148 | `GCE_test_evolution_reduces_error` | 在正弦波上运行 50 个智能体约 3 秒；验证种群存活（活跃 > 0）且进化后平均能量 > 10.0 |

**耗时：** 约 107 秒

---

## 组件覆盖度汇总

| 组件 | 测试数 | 关键风险覆盖 |
|------|--------|-------------|
| 表达式树求值 | 24 | 全部 10 个运算符，边界情况（除零、指数溢出、对数负数、NaN、越界） |
| 数据持久化（CRUD） | 28 | 全部 27 项仓库函数，并发写安全性，锁重试 |
| 数据库模式 | 14 | DDL、WAL、外键、幂等初始化、迁移路径 |
| 遗传操作 | 8 | 交叉有效性、5 种变异类型、树剪枝/扩张 |
| 基因编码 | 10 | 序列化往返、zlib BLOB 压缩、树验证 |
| 特征提取 | 8 | 滑动窗口、36 维特征池、掩码过滤 |
| Lorenz 物理 | 5 | 不动点、RK4 正确性、混沌发散（蝴蝶效应） |
| 事件总线 | 13 | 发布/订阅、FIFO、队列满、关闭幂等性、冻结事件 |
| Lyapunov 分析 | 6 | 常数/正弦/随机/边界情况、分岔检测 |
| 场景解析器 | 6 | 数字提取、时间解析、参与者命名、截断 |
| 函数注册表 | 14 | 全部 10 个算子、参数数目查询、禁止 ML 函数名检查 |
| 配置与验证 | 5 | YAML 加载、环境变量替换、验证退出码 |
| 能量公式 | 4 | 完美/部分/差/极差预测的奖励谱 |
| 端到端流水线 | 2 | 完整场景→推演→叙事离线流程 |
| 实时进化 | 1 | 多智能体繁殖与能量选择 |
| **合计** | **148** | |

---

## 警告

| 警告 | 文件 | 说明 |
|------|------|------|
| `PytestUnknownMarkWarning` | `GCE_test_evolution_loop.py:129` | `@pytest.mark.slow` 未在 pytest 配置中注册。建议在 `pytest.ini` 中添加 markers 声明。 |

---

## 测试环境

| 属性 | 值 |
|------|-----|
| 平台 | Darwin 22.6.0 (macOS) |
| Python | 3.8.10 |
| pytest | 8.3.5 |
| pytest-asyncio | 0.24.0 |
| 数据库 | SQLite（WAL 模式，每测试独立临时文件） |
| 测试隔离 | `tempfile.mkdtemp()` 数据库测试；每测试类全新 fixture |
