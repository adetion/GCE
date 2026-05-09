# 博弈混沌引擎 (GCE) v0.1.0

**自主进化的数字生命系统。** 遗传编程与混沌动力学交汇的多智能体平台——以 Lorenz 吸引子为环境基底、拍卖市场为物理规则，通过自然选择驱动机器涌现博弈预测能力。

## 核心理念

GCE 是一个人工生命实验室。100 个智能体诞生时携带着随机的表达式树"大脑"和 36 位特征掩码，决定了它们能感知什么。它们观察混沌环境，做出预测，凭准确度获得能量或走向消亡。高能量智能体通过锦标赛选择 + 交叉 + 变异进行繁殖，低能量智能体则被淘汰。

环境并非随机噪声——它是 **Lorenz 混沌吸引子**与**多主体拍卖市场**的耦合，产生有结构却不可预测的时间序列。为了生存，智能体必须进化出对这种混沌的真正预测模型。

**没有训练数据。没有梯度下降。没有反向传播。** 只有进化。

## 系统架构

```text
                         ┌──────────────────────────┐
                         │      CLI / 用户输入       │
                         └─────────────┬────────────┘
                                       │
                         ┌─────────────▼────────────┐
                         │       GCE_parser          │
                         │   (LLM 或 正则解析)       │
                         └─────────────┬────────────┘
                                       │ GCE_Scenario
                         ┌─────────────▼────────────┐
                         │      GCE_engine           │
                         │   精英前向推演引擎        │
                         │   Lyapunov + 分岔检测      │
                         └─────────────┬────────────┘
                                       │ GCE_SimulationResult
                         ┌─────────────▼────────────┐
                         │     GCE_narrator          │
                         │   四幕战略决策报告         │
                         └──────────────────────────┘

══ 后台持续运行 ═══════════════════════════════════

  环境进程 ──► 队列 ──► Agent₁, Agent₂, ... Agentₙ
  (Lorenz +       │      (Forager → Predictor → DB)
   拍卖市场)      │
                  ▼
            能量管理器 ──► 繁殖器 ──► 清理器
            (奖励/惩罚)    (交叉+变异)  (过期清理)
```

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 离线模式运行（无需 API Key）
python GCE_main.py

# 在线模式（LLM 场景解析与叙事生成）
export GCE_API_KEY="your-deepseek-api-key"
# 在 config.yaml 中设置 llm.enabled: true
python GCE_main.py
```

## 命令行选项

| 选项 | 说明 |
|------|------|
| `--config, -c PATH` | 配置文件路径（默认: `config.yaml`） |
| `--offline, -o` | 强制离线模式（不调用 LLM API） |
| `--reset-db` | 启动时删除并重建数据库 |

**交互式命令：**

| 输入 | 说明 |
|------|------|
| 任意文本 | 描述一个博弈场景（如"三家公司在60天内进行价格战"） |
| `status` | 显示种群规模、能量分布、代际统计 |
| `quit` | 优雅关闭系统 |

## 配置参数

所有参数在 `config.yaml` 中配置，从 `config.yaml.example` 复制并修改。

### LLM 大模型

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `llm.enabled` | `false` | 是否启用 LLM API |
| `llm.api_key` | `${GCE_API_KEY}` | API 密钥（从环境变量读取） |
| `llm.base_url` | `https://api.deepseek.com` | OpenAI 兼容 API 地址 |
| `llm.model` | `deepseek-v4-pro` | 模型名称 |
| `llm.temperature` | `0.7` | 采样温度 |
| `llm.max_tokens` | `2048` | 最大生成长度 |
| `llm.timeout` | `30.0` | 请求超时（秒） |

### Evolution 进化

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `population_initial` | `100` | 初始种群规模 |
| `max_population` | `2000` | 种群硬上限 |
| `initial_energy` | `100.0` | 新生智能体初始能量 |
| `reproduce_threshold` | `200.0` | 繁殖所需最低能量 |
| `reproduction_cost` | `80.0` | 父代繁殖成本（双方分摊） |
| `base_reward` | `10.0` | 完美预测的基础能量奖励 |
| `error_scale` | `2.0` | 误差归一化尺度因子 |
| `tournament_size` | `2` | 锦标赛选择候选数 |
| `crossover_rate` | `0.7` | 子树交换交叉概率 |
| `mutation_rate_base` | `0.2` | 基础变异概率 |
| `mask_flip_rate` | `0.05` | 特征掩码位翻转概率 |
| `max_depth` | `8` | 表达式树最大深度 |
| `min_nodes` | `3` | 表达式树最小节点数 |
| `max_nodes` | `50` | 表达式树最大节点数 |
| `feature_count` | `36` | 特征池维度 |
| `window_size` | `20` | 滑动窗口大小 |
| `energy_tick_seconds` | `1.0` | 能量评估间隔 |
| `breeding_interval_seconds` | `2.0` | 繁殖检查间隔 |

### Environment 环境

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `seed` | `42` | 随机种子 |
| `simulator.tick_interval` | `0.5` | 模拟 tick 间隔（秒） |
| `simulator.lorenz_dt` | `0.01` | Lorenz 积分步长 |
| `simulator.substeps_per_tick` | `50` | 每 tick 的 RK4 子步数 |
| `simulator.lorenz.sigma` | `10.0` | Lorenz σ 参数 |
| `simulator.lorenz.rho` | `28.0` | Lorenz ρ 参数 |
| `simulator.lorenz.beta` | `2.6666667` | Lorenz β 参数 |
| `simulator.num_market_agents` | `10` | 拍卖市场参与者数量 |
| `online_sources` | `[]` | 在线数据源（`yfinance`、`coingecko`） |

### Database 数据库

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `path` | `gce_data.db` | SQLite 数据库文件路径 |
| `prediction_ttl_days` | `7` | 预测记录保留天数 |
| `cleanup_interval_seconds` | `3600` | 清理检查间隔（秒） |

### Simulation 推演

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `elite_count` | `10` | 用于前向推演的精英智能体数量 |
| `future_steps` | `30` | 默认预测步数 |
| `perturbation_epsilon` | `0.001` | 分岔检测微扰幅度 |
| `divergence_threshold` | `0.5` | 分岔检测发散阈值 |

## 工作原理

### 1. 环境 —— Lorenz 混沌 + 拍卖市场

环境在独立进程中运行，以固定频率产生事件。每个 tick：

1. **Lorenz 吸引子**经 RK4 数值积分（`σ=10, ρ=28, β=8/3`——经典混沌参数区）
2. **市场智能体**（趋势跟踪、均值回归、随机策略）提交买卖报价，Lorenz 的 x 分量作为混沌源注入
3. **清算价格**由拍卖机制计算，Lorenz 的 z 分量作为噪声叠加
4. `GCE_RawEvent`（含价格、成交量、价差、Lorenz 状态）发布到共享队列
5. 约 10% 的 tick 还会产生**文本事件**（合成新闻头条）

### 2. 智能体 —— 表达式树 + 特征掩码

每个智能体是一个独立进程，包含：

- **基因**：表达式树（数学运算符：`+`、`-`、`*`、`/`、`sin`、`cos`、`exp`、`log`、`abs`、`ifgt`），终端节点引用 36 维特征池
- **掩码**：36 位整数，选择智能体能"看到"哪些特征
- **预测器**：对提取的特征向量求值表达式树 → 输出数值预测

**特征池**（36 维）：

| 索引 | 特征 |
|------|------|
| 0–19 | 价格滞后 1–20 期 |
| 20–24 | 成交量滞后 1–5 期 |
| 25–29 | 价差滞后 1–5 期 |
| 30–32 | 价格 5/10/20 期简单移动平均 |
| 33–34 | 价格/成交量 5 期波动率 |
| 35 | 情绪分数（文本大小写启发式） |

### 3. 能量经济

能量公式是唯一的选择压力：

```text
误差   = |预测价格 - 实际价格|
奖励   = base_reward × max(0, 1 - 误差 / error_scale)
```

- 完美预测 → `+base_reward` 能量
- 误差 ≥ error_scale → `0` 奖励
- 能量 ≤ 0 → 智能体死亡（进程终止，状态标记为 "dead"）

### 4. 繁殖 —— 锦标赛选择 + 遗传算子

每 2 秒，繁殖器线程执行：

1. 选取能量 ≥ `reproduce_threshold` 的智能体
2. 通过**锦标赛选择**（规模=2）配对
3. 应用**子树交换交叉**（70% 概率）
4. 应用**变异**——均匀选择以下之一：
   - 终端变异（改变特征索引或微扰常数）
   - 函数变异（更换运算符）
   - 子树替换
   - 收缩/扩张（减少或增加树深度）
   - 掩码位翻转（切换特征可见性）
5. 验证并插入子代，赋予 `initial_energy`
6. 从每个父代扣除 `reproduction_cost / 2`

### 5. 推演与战略分析

当用户描述一个博弈场景（如"两家公司进行 90 天价格战"）：

1. **解析器** 提取参与者、初始价格、时间跨度、目标（离线正则 / 在线 LLM）
2. **引擎** 选取前 K 个精英智能体，进行迭代前向推演——每个智能体独立预测下一值，共识 = 中位数预测
3. **Lyapunov 分析** 估计预测轨迹的混沌程度
4. **微扰分析** 测试敏感性——检测分岔发生的时间点
5. **叙事器** 生成**四幕战略决策报告**：
   - **第一幕** —— 战场全息重构（相空间与体制识别）
   - **第二幕** —— 对手心智镜像（精英策略推断）
   - **第三幕** —— 全博弈树展开（分岔路径分析）
   - **第四幕** —— 战略指令下达（可执行建议）

## 项目结构

```text
GCE_main.py                  # CLI 入口
config.yaml.example           # 配置模板
narratives.yaml               # 离线叙事模板
requirements.txt              # 运行时依赖
requirements-dev.txt          # 开发依赖
Dockerfile                    # 容器构建

gce/
  core/                       # 遗传编程核心
    GCE_agent.py              # 智能体进程主循环
    GCE_breeder.py            # 锦标赛选择 + 繁殖
    GCE_energy.py             # 能量奖励/淘汰管理器
    GCE_forager.py            # 滑动窗口特征提取
    GCE_functions.py          # 表达式树函数集（10个算子）
    GCE_gene.py               # 基因数据结构 + 序列化
    GCE_genetic_ops.py        # 交叉、变异、树生成
    GCE_predictor.py          # 表达式树求值器

  environment/                # 环境模拟
    GCE_base.py               # 抽象基类 + 事件类型
    GCE_simulator.py          # Lorenz RK4 + 拍卖市场
    GCE_event_bus.py          # 多进程队列封装
    GCE_adapters.py           # YFinance / CoinGecko 数据适配器

  interface/                  # CLI / LLM / 解析 / 叙事
    GCE_cli.py                # 主编排器循环
    GCE_llm_client.py         # DeepSeek/OpenAI API 客户端
    GCE_parser.py             # 场景解析器（LLM 或 正则）
    GCE_narrator.py           # 四幕叙事生成器

  simulation/                 # 沙盘推演 + 混沌分析
    GCE_schemas.py            # Scenario/Result 数据结构
    GCE_engine.py             # 精英前向推演引擎
    GCE_lyapunov.py           # Lyapunov 指数 + 微扰分析

  storage/                    # SQLite 持久化
    GCE_database.py           # DDL + 连接管理
    GCE_repository.py         # 完整 CRUD 数据访问层
    GCE_cleanup.py            # 后台 TTL 清理线程

  utils/                      # 工具
    GCE_config.py             # YAML 配置 + 环境变量替换
    GCE_logging.py            # 滚动文件日志
    GCE_retry.py              # 指数退避重试装饰器

tests/                        # 测试套件（148 项测试）
  GCE_test_config.py          # 配置加载与验证
  GCE_test_database.py        # 数据库初始化、连接、模式
  GCE_test_energy.py          # 能量奖励公式
  GCE_test_event_bus.py       # 事件总线发布/订阅
  GCE_test_forager.py         # 滑动窗口 + 特征提取
  GCE_test_functions.py       # 所有数学运算符
  GCE_test_gene.py            # 基因序列化
  GCE_test_genetic_ops.py     # 交叉、变异、剪枝
  GCE_test_lyapunov.py        # Lyapunov + 微扰分析
  GCE_test_parser.py          # 离线正则解析器
  GCE_test_predictor.py       # 表达式树求值
  GCE_test_repository.py      # 全部 CRUD 操作
  GCE_test_simulator.py       # Lorenz RK4 精度
  integration/
    GCE_test_end_to_end.py        # 端到端叙事生成
    GCE_test_evolution_loop.py    # 正弦波迷你进化循环
```

## 运行测试

```bash
# 全部快速测试（147 项）
pytest tests/ -v

# 包含慢速集成测试（进化循环）
pytest tests/ -v -m "slow"

# 指定测试文件
pytest tests/GCE_test_predictor.py -v
```

## Docker

```bash
docker build -t gce .
docker run -it gce
```

Docker 镜像默认以离线模式运行。如需使用 LLM 功能，挂载启用了 `llm.enabled: true` 的配置文件并传入 API Key：

```bash
docker run -it -e GCE_API_KEY="your-key" -v ./config.yaml:/app/config.yaml gce
```

## 核心设计原则

- **纯 Python 标准库 + SQLite** —— 无 numpy、无 pandas、无 Redis。表达式树求值器、特征提取、Lorenz 积分器均为手写实现。
- **多进程架构** —— 每个智能体是独立的 `Process`；能量管理器、繁殖器、清理器以 `Thread` 形式在主进程中运行。进程间通过 `multiprocessing.Queue` 通信。
- **SQLite WAL 模式** —— 支持所有进程和线程的并发读写。所有写操作使用指数退避重试机制处理锁竞争。
- **LLM 双模式** —— 完整支持离线运行（正则解析器 + YAML 模板叙事器）或在线运行（LLM 驱动的解析与叙事生成）。默认为离线模式。
- **能量即通用适应度** —— 没有独立的损失函数、没有反向传播、没有梯度。能量是唯一的生存货币。

## 许可协议

专有软件。允许个人非商业使用。完整许可条款见源代码文件头。商业许可请联系 <i126@126.com>。
