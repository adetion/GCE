# Gaming Chaos Engine (GCE) v0.1.0

**Autonomous self-evolving digital life meets game-theoretic strategic intelligence.** A multi-agent system where genetic programming converges with chaotic dynamics and domain-aware strategic reasoning — agents evolve predictive intelligence through natural selection atop a Lorenz-attractor environment with auction-market physics, while a parallel simulation pipeline transforms user-described scenarios into professional four-act strategic reports with plain-language tactical conclusions.

## Table of Contents

- [Concept](#concept)
- [Architecture](#architecture)
  - [Background Subsystems (Continuous)](#background-subsystems-continuous)
  - [On-Demand Simulation Pipeline](#on-demand-simulation-pipeline)
- [Quick Start](#quick-start)
- [CLI Commands](#cli-commands)
- [Configuration](#configuration)
- [How It Works](#how-it-works)
  - [1. Environment — Lorenz Chaos + Auction Market](#1-environment--lorenz-chaos--auction-market)
  - [2. Agents — Expression Trees + Feature Masks](#2-agents--expression-trees--feature-masks)
  - [3. Energy Economy](#3-energy-economy)
  - [4. Breeding — Tournament Selection + Genetic Operators](#4-breeding--tournament-selection--genetic-operators)
  - [5. Domain Template System — 7 Application Domains](#5-domain-template-system--7-application-domains)
  - [6. Scene Parsing — LLM + Regex Dual-Mode](#6-scene-parsing--llm--regex-dual-mode)
  - [7. Sentiment Analysis — LLM-Driven Market Psychology](#7-sentiment-analysis--llm-driven-market-psychology)
  - [8. Game-Theoretic Simulation Engine](#8-game-theoretic-simulation-engine)
  - [9. Narrative Generation — Dual-Output Strategic Reports](#9-narrative-generation--dual-output-strategic-reports)
- [The Four Game Models](#the-four-game-models)
- [The Seven Application Domains](#the-seven-application-domains)
- [Plain-Language Conclusion Card](#plain-language-conclusion-card)
- [Multi-Party Weight Ranking](#multi-party-weight-ranking)
- [Project Structure](#project-structure)
- [Running Tests](#running-tests)
- [Docker](#docker)
- [Key Design Principles](#key-design-principles)
- [License](#license)

## Concept

GCE is an artificial life laboratory and strategic intelligence platform operating at two levels:

**Level 1 — Evolutionary Intelligence.** 100 agents are born with random expression-tree "brains" and a 36-bit feature mask that determines what they perceive. They observe a chaotic environment, make predictions, and are rewarded or starved based on accuracy. High-energy agents breed through tournament selection + crossover + mutation. Low-energy agents die. The environment is not random noise — it's a **Lorenz chaotic attractor** coupled with a **multi-agent auction market**, producing structured-yet-unpredictable time series. To survive, agents must evolve genuine predictive models of this chaos.

**Level 2 — Strategic Intelligence.** When a user describes any competitive scenario (price war, budget negotiation, ecological resource allocation, interpersonal conflict, etc.), the system parses the scene, classifies its **application domain**, analyzes sentiment, runs a forward simulation using elite evolved agents as perturbation sources, performs Lyapunov chaos analysis, and generates a **dual-output strategic report**: a professional four-act game-theoretic analysis **plus** a plain-language conclusion card with concrete, actionable steps — no jargon, just "do this."

**No training data. No gradient descent. No backpropagation.** Just evolution.

## Architecture

### Background Subsystems (Continuous)

```
  Environment Process ──► Shared Queue ──► Agent₁, Agent₂, ... Agentₙ
  (Lorenz RK4 +             │              (Forager → Predictor → SQLite)
   Auction Market)          │
                            ▼
                      Energy Manager ──► Breeder ──► Cleanup
                      (reward/punish)    (crossover  (TTL purge)
                                          + mutate)
```

### On-Demand Simulation Pipeline

```
  User Input (natural language scenario)
       │
       ▼
  ┌─────────────────────────────┐
  │   GCE_classify_domain       │  Keyword scoring + LLM disambiguation
  │   7 application domains     │  → DomainTemplate
  └─────────────┬───────────────┘
                │
                ▼
  ┌─────────────────────────────┐
  │   GCE_parser                │  LLM (online) or regex (offline)
  │   + domain prompt injection │  → GCE_Scenario (participants, prices,
  └─────────────┬───────────────┘       game_type, domain_id)
                │
                ▼
  ┌─────────────────────────────┐
  │   GCE_analyze_sentiment     │  LLM-driven market/domain psychology
  │   + domain-specific angle   │  → sentiment_context (scores, themes)
  └─────────────┬───────────────┘
                │
                ▼
  ┌─────────────────────────────┐
  │   GCE_engine                │  Elite forward simulation
  │   Bertrand / Vickrey /       │  Game model selection
  │   Negotiation / Cournot      │  Sentiment bias modulation
  │   Lyapunov + bifurcation     │  → GCE_SimulationResult
  └─────────────┬───────────────┘
                │
                ▼
  ┌─────────────────────────────┐
  │   GCE_narrator              │  LLM (online) or rule-based (offline)
  │   + domain term overrides   │  Four-act professional report
  │   + plain-language card     │  + Act V: 大白话结论卡片
  │   + multi-party ranking     │  → Full dual-output narrative
  └─────────────────────────────┘
```

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run offline (no API key needed — regex parser + rule-based narration)
python GCE_main.py

# Run with LLM-powered scene parsing, sentiment analysis, and narrative generation
export GCE_API_KEY="your-deepseek-api-key"
# Set llm.enabled: true in config.yaml
python GCE_main.py
```

## CLI Commands

**Command-line arguments:**

| Argument | Description |
|----------|-------------|
| `--config, -c PATH` | Path to config file (default: `config.yaml`) |
| `--offline, -o` | Force offline mode (no LLM API calls) |
| `--reset-db` | Delete and recreate the database on startup |

**Interactive prompt:**

| Input | Description |
|-------|-------------|
| Any text | Describe a scenario in natural language (Chinese or English) |
| `status` | Show population size, energy range, generation stats, LLM call count |
| `quit` | Graceful shutdown (terminates all child processes) |

**Example scenarios:**

```
# Enterprise: budget allocation
市场部、研发部和运营部三方在年度预算会议上争夺有限资源。CTO需要在三方之间分配总额3000万的预算。

# Ecology: conservation funding
长江流域中华鲟和白鳍豚的栖息地保护面临资金分配争议。有限保护经费如何在两种濒危物种间分配？

# Personal: career transition
我在职业转型和继续深耕现有领域之间反复犹豫。如何分配学习时间才能最大化长期职业满意度？

# Social: team mediation
团队里技术负责人老张和产品总监小李因为迭代节奏分歧产生了信任裂痕。如何修复协作关系？
```

## Configuration

All parameters are in `config.yaml`. Copy from `config.yaml.example` and edit.

### LLM

| Parameter | Default | Description |
|-----------|---------|-------------|
| `llm.enabled` | `false` | Enable LLM API for all pipeline stages |
| `llm.api_key` | `${GCE_API_KEY}` | API key (from environment variable) |
| `llm.base_url` | `https://api.deepseek.com` | OpenAI-compatible API endpoint |
| `llm.model` | `deepseek-v4-pro` | Model name |
| `llm.temperature` | `0.7` | Sampling temperature for narrative generation |
| `llm.max_tokens` | `2048` | Max generation length |
| `llm.timeout` | `30.0` | Request timeout (seconds) |

### Sentiment

| Parameter | Default | Description |
|-----------|---------|-------------|
| `sentiment.enabled` | `true` | Enable LLM sentiment analysis (requires `llm.enabled`) |
| `sentiment.influence_weight` | `0.3` | How strongly sentiment modulates agent perturbation (0.0–1.0) |

### Evolution

| Parameter | Default | Description |
|-----------|---------|-------------|
| `population_initial` | `100` | Starting population size |
| `max_population` | `2000` | Hard population cap (breeder pauses when reached) |
| `initial_energy` | `100.0` | Energy given to newborn agents |
| `reproduce_threshold` | `200.0` | Minimum energy to be eligible for breeding |
| `reproduction_cost` | `80.0` | Energy deducted from parents (40 each in paired breeding) |
| `base_reward` | `10.0` | Energy reward for perfect prediction (error = 0) |
| `error_scale` | `2.0` | Error normalization factor; error ≥ this → 0 reward |
| `tournament_size` | `2` | Candidates per tournament selection round |
| `crossover_rate` | `0.7` | Probability of subtree-swap crossover per breeding event |
| `mutation_rate_base` | `0.2` | Base mutation probability (applied per offspring) |
| `mask_flip_rate` | `0.05` | Per-bit feature mask flip probability |
| `max_depth` | `8` | Maximum expression tree depth |
| `min_nodes` | `3` | Minimum expression tree nodes (prevents trivial trees) |
| `max_nodes` | `50` | Maximum expression tree nodes (prevents bloat) |
| `feature_count` | `36` | Feature pool dimensionality |
| `window_size` | `20` | Sliding window size for feature extraction |
| `energy_tick_seconds` | `1.0` | Energy evaluation interval |
| `breeding_interval_seconds` | `2.0` | Breeding check interval |

### Environment

| Parameter | Default | Description |
|-----------|---------|-------------|
| `seed` | `42` | Random seed for reproducibility |
| `simulator.tick_interval` | `0.5` | Seconds between environment ticks |
| `simulator.lorenz_dt` | `0.01` | Lorenz integration step size |
| `simulator.substeps_per_tick` | `50` | RK4 substeps per tick |
| `simulator.lorenz.sigma` | `10.0` | Lorenz σ parameter |
| `simulator.lorenz.rho` | `28.0` | Lorenz ρ parameter |
| `simulator.lorenz.beta` | `2.6666667` | Lorenz β parameter (8/3) |
| `simulator.num_market_agents` | `10` | Auction market participants (trend-followers, mean-reverters, random) |
| `online_sources` | `[]` | Online data adapters (`yfinance`, `coingecko`) |

### Database

| Parameter | Default | Description |
|-----------|---------|-------------|
| `path` | `gce_data.db` | SQLite database file path |
| `prediction_ttl_days` | `7` | Retention period for old prediction records |
| `cleanup_interval_seconds` | `3600` | Cleanup check interval (1 hour) |

### Simulation

| Parameter | Default | Description |
|-----------|---------|-------------|
| `elite_count` | `10` | Top-K agents (by energy) used for forward simulation |
| `future_steps` | `30` | Default prediction horizon (time steps) |
| `perturbation_epsilon` | `0.001` | Perturbation magnitude for bifurcation detection |
| `divergence_threshold` | `0.5` | Divergence threshold for identifying bifurcation points |

## How It Works

### 1. Environment — Lorenz Chaos + Auction Market

The environment runs in its own `multiprocessing.Process`, generating events at a fixed tick rate. Each tick:

1. **Lorenz attractor** is integrated via RK4 (`σ=10, ρ=28, β=8/3` — the classic chaotic regime characterized by the butterfly-shaped strange attractor)
2. **Market agents** (trend-followers, mean-reverters, random) submit bids/asks, with the Lorenz x-component injected as an external chaos source influencing agent behavior
3. **Clearing price** is computed from the auction mechanism, with the Lorenz z-component added as structured noise
4. A `GCE_RawEvent` containing price, volume, spread, and full Lorenz state `(x, y, z)` is published to the shared `multiprocessing.Queue`
5. Approximately 10% of ticks also emit a **text event** — a synthetically generated news headline derived from the current market state

The Lorenz attractor was chosen because it produces **structured unpredictability**: deterministic chaos that is neither pure randomness (trivial to average) nor simple periodicity (trivial to memorize). Agents must evolve genuine nonlinear predictive models.

### 2. Agents — Expression Trees + Feature Masks

Each agent is an independent `multiprocessing.Process` with:

- **Gene**: an expression tree encoding a mathematical function. Internal nodes are operators (`+`, `-`, `*`, `/`, `sin`, `cos`, `exp`, `log`, `abs`, `ifgt`). Leaf nodes reference one of 36 feature slots or hold a numeric constant.
- **Mask**: a 36-bit integer acting as a binary selector — each bit determines whether the agent "sees" the corresponding feature. Mask = 0 means the agent is blind; mask = all-1s means full perception.
- **Forager**: maintains a sliding window of the last 20 events. On each new event, extracts the 36 features from the window and passes them through the mask.
- **Predictor**: evaluates the expression tree on the masked feature vector → outputs a single numeric prediction.

**Feature pool** (36 dimensions):

| Indices | Features | Description |
|---------|----------|-------------|
| 0–19 | Price lags 1–20 | Historical prices at 20 lagged time steps |
| 20–24 | Volume lags 1–5 | Historical trading volumes at 5 lagged steps |
| 25–29 | Spread lags 1–5 | Bid-ask spread at 5 lagged steps |
| 30–32 | Price SMA 5, 10, 20 | Simple moving averages of price |
| 33–34 | Price/volume volatility (5-period) | Rolling standard deviation |
| 35 | Sentiment score | Heuristic from text event casing/ keywords |

### 3. Energy Economy

The energy formula is the **sole selection pressure** — there is no separate loss function, no gradient, no backpropagation:

```text
error  = |predicted_price - actual_price|
reward = base_reward × max(0, 1 - error / error_scale)
```

- Perfect prediction (error = 0) → `+base_reward` energy
- Error ≥ error_scale → `0` reward (the prediction was worthless)
- Energy ≤ 0 → agent dies (process killed via `terminate()`, status set to "dead" in SQLite)

Energy is continuously consumed at a small base rate (metabolic cost of existence). Only agents that consistently predict accurately accumulate enough energy to survive and reproduce.

### 4. Breeding — Tournament Selection + Genetic Operators

Every `breeding_interval_seconds` (2s default), the breeder thread:

1. **Eligibility check**: selects all agents with energy ≥ `reproduce_threshold`
2. **Pairing via tournament selection** (size=2): for each parent slot, randomly picks 2 candidates, selects the one with higher energy
3. **Subtree-swap crossover** (70% probability): randomly selects a node in each parent tree, swaps the selected subtrees to produce the child
4. **Mutation** — uniformly picks one operation from:
   - **Terminal mutation**: change feature index or jitter numeric constant by ±20%
   - **Function mutation**: replace operator node with a different operator (same arity)
   - **Subtree replacement**: replace a random subtree with a newly generated random tree
   - **Shrink/expand**: remove a subtree (reduce depth) or insert a new operator node (increase depth)
   - **Mask bit flip**: toggle one randomly selected feature visibility bit
5. **Validation**: checks tree depth and node count constraints; retries up to 3 times on constraint violation
6. **Insertion**: inserts the child into SQLite with `initial_energy` and generation = `max(parent_gen) + 1`
7. **Cost deduction**: deducts `reproduction_cost / 2` from each parent's energy

### 5. Domain Template System — 7 Application Domains

The system is not hardcoded for finance. A **domain template system** (`gce/interface/GCE_domain_templates.py`) maps any user scenario to one of 7 application domains through two-stage classification:

**Stage 1 — Keyword Scoring (offline, always available):**
Each domain template defines 30–50 Chinese keyword triggers. The classifier counts keyword matches in the user input and computes a match score. If one domain's score dominates (>2× the runner-up), it's selected immediately.

**Stage 2 — LLM Disambiguation (online, when ambiguous):**
When keyword scores are too close to distinguish (multiple domains have similar match counts), the LLM is asked to classify the scenario into the most appropriate domain.

**What a DomainTemplate provides:**
- `entity_type_hints`: what kinds of entities to look for (species names, department names, personal goals, etc.)
- `value_semantics`: what numerical values mean in this domain (population counts, budget amounts, satisfaction scores, etc.)
- `game_type_preference`: which game model best fits this domain (Cournot for ecology, Negotiation for personal decisions, etc.)
- `parsing_prompt_additions`: injected into the LLM system prompt during scene parsing
- `sentiment_prompt_additions`: injected into the sentiment analysis query
- `narrative_prompt_additions`: injected into the narrative generation system prompt
- `narrative_term_overrides`: key-value pairs for replacing financial jargon with domain terminology (e.g., "价格" → "种群数量" in ecology)
- `plain_language_additions`: domain-specific metaphors and language for the conclusion card

**Critical design rule**: Templates only describe *what kind of thing to look for* — they never contain hardcoded entity names, numerical values, or domain-specific formulas. They are reference parameters, not data.

### 6. Scene Parsing — LLM + Regex Dual-Mode

The parser (`gce/interface/GCE_parser.py`) extracts structured game-theoretic scenarios from free-form natural language:

**Online mode (LLM):**
- Calls the LLM with a system prompt augmented by the domain template's `parsing_prompt_additions`
- Extracts: participant names, initial positions/prices, game type, time horizon, objective
- Domain-specific entity recognition (e.g., species names in ecology, department names in enterprise)
- Calls sentiment analysis on the parsed scenario text

**Offline mode (regex):**
- Pattern-based participant extraction from Chinese text (names, entities)
- Heuristic game type detection from keywords (price, bid, negotiate, output, compete)
- Numerical value extraction for initial positions
- Limited to ~2 named participants; remaining detected players get fallback names

Both modes produce a `GCE_Scenario` dataclass containing:
```python
participants: List[GCE_Participant]  # name, initial_position, strategy_hint
initial_prices: List[float]          # starting values for each participant
time_steps: int                      # simulation horizon (default 30)
objective: str                       # the parsed objective/context
game_type: str                       # price_war | auction | negotiation | output_competition
domain_id: str                       # matched domain template ID
sentiment_context: Dict[str, Any]    # LLM sentiment analysis result (or empty)
```

### 7. Sentiment Analysis — LLM-Driven Market Psychology

The sentiment module (`gce/environment/GCE_sentiment.py`) provides a structured psychological layer that modulates the simulation:

**`GCE_analyze_sentiment(scenario_text, entity_names, llm_client, domain_id)`**
- Calls the LLM with domain-specific sentiment analysis prompts
- Domain template's `sentiment_prompt_additions` guide the LLM toward domain-relevant sentiment dimensions
- Returns structured JSON:
  - `overall_sentiment`: "positive" | "negative" | "neutral"
  - `sentiment_score`: float in [-1.0, 1.0]
  - `key_themes`: list of narrative themes relevant to the domain
  - `market_mood`: descriptive label (domain-adapted, e.g., "conservation urgency" vs "market fear")
  - `volatility_expectation`: expected sentiment-driven volatility
  - `entity_sentiments`: per-entity sentiment breakdown
- Falls back gracefully to neutral when LLM is unavailable

**`GCE_compute_sentiment_bias(sentiment_context, game_type, player_name) -> float`**
- Computes a per-player perturbation bias modulated by sentiment
- Positive sentiment → aggressive bias (price increases, higher bids)
- Negative sentiment → defensive bias (price cuts, lower bids)
- Clamped to [-0.5, 0.5] and scaled by `sentiment.influence_weight`
- Applied in all four game models during forward simulation

### 8. Game-Theoretic Simulation Engine

The engine (`gce/simulation/GCE_engine.py`) runs iterative forward simulations using elite evolved agents:

1. **Game model selection**: uses the game_type from the parser (or auto-detects from the scenario objective)
2. **Elite agent loading**: selects the top-K agents by energy from SQLite; if no agents exist, falls back to NGRC-style polynomial residual perturbation
3. **Iterative forward simulation**: at each time step `t`:
   - Each elite agent independently predicts the next consensus value
   - The median of elite predictions becomes the next consensus value
   - Sentiment bias is computed per player and combined with the agent perturbation
   - Per-player trajectories are tracked independently
4. **Chaos analysis**:
   - **Lyapunov exponent estimation**: quantifies trajectory chaoticity (positive = chaotic, negative = stable)
   - **Bifurcation detection**: perturbation analysis identifies critical decision points where small changes cause large outcome divergence
   - **Trajectory volatility**: rolling standard deviation of step-to-step changes
   - **Nash convergence**: measures how close the system is to a stable equilibrium
5. **Key event detection**: identifies significant events in each player's trajectory (major concessions, winning bids, aggressive moves)

### 9. Narrative Generation — Dual-Output Strategic Reports

The narrator (`gce/interface/GCE_narrator.py`, ~1300 lines) produces a **dual-output** report for every scenario:

**Online mode (LLM):**
- System prompt includes the domain template's `narrative_prompt_additions` for domain-appropriate language
- The LLM receives all computed data (trajectories, Lyapunov, Nash convergence, player trajectories, sentiment context, key events) and generates both the professional report AND the plain-language card in a single response
- Act V (大白话结论卡片) is specified in the system prompt as a mandatory section

**Offline mode (rule-based):**
- Each of the four acts is built from actual computed data — no static templates
- Domain terminology is applied via string-level `narrative_term_overrides` (longer keys matched first to prevent substring corruption)
- The plain-language card is generated by `_build_plain_language_card()` with domain-specific language packages
- Multi-party (3+) games trigger tiered weight ranking automatically

**Report structure:**

| Act | Title | Content |
|-----|-------|---------|
| I | 战场全息重构 / Battlefield Holographic Reconstruction | Regime identification (chaotic/convergent/stable), Lyapunov analysis, trajectory trends, Nash convergence, equilibrium estimate |
| II | 对手心智镜像 / Opponent Mind Mirror | Per-player behavioral analysis, attack/defense patterns, key pivot points, sentiment-modulated tendencies, overall strategic posture |
| III | 博弈树全展开 / Full Game Tree Expansion | 2–3 branching paths with estimated probabilities, trigger conditions, and outcome descriptions; bifurcation-aware path analysis |
| IV | 策略指令下达 / Strategy Orders Issued | Immediate actions (steps 1–3), medium-term layout (steps 5–15), stop-loss/stop-gain boundaries, monitoring schedules, concrete numbers |
| V | 大白话结论卡片 / Plain-Language Conclusion Card | Zero-jargon actionable summary: one-line strategy with specific ratios, plain-language "why," step-by-step actions with monitoring thresholds, closing metaphor |

## The Four Game Models

The engine supports four classical game-theoretic models, each producing distinct trajectory dynamics:

### 1. Bertrand Price Competition (`price_war`)

n firms compete on price with differentiated products. Each firm sets its price to maximize profit given competitor prices. The model captures:
- Best-response dynamics: each firm undercuts competitors to capture market share
- Demand elasticity scaling with the number of players
- Convergence toward marginal-cost pricing in pure Bertrand, or above-cost equilibrium with product differentiation
- Sentiment bias: positive sentiment → aggressive pricing; negative → defensive undercutting

### 2. Vickrey Auction (`auction`)

Second-price sealed-bid auction. Each bidder submits a private bid; the highest bidder wins but pays the second-highest bid. The model captures:
- Truthful bidding as the dominant strategy in theory, but sentiment and perturbation cause deviations
- Bid shading when bidders have noisy estimates of competitor valuations
- Revenue equivalence dynamics under perturbation
- Sentiment bias: positive sentiment → higher bids (aggressive); negative → cautious bidding

### 3. Alternating-Offer Negotiation (`negotiation`)

Two or more parties alternately propose divisions of a resource, with time discounting. The model captures:
- Rubinstein bargaining dynamics: first-mover advantage, impatience-driven concessions
- Multi-party coalition formation: identifying natural allies and isolating holdouts
- Convergence to Nash bargaining solution under complete information
- Sentiment bias: positive sentiment → firmer stance (less concession); negative → faster concession

### 4. Cournot Output Competition (`output_competition`)

n firms compete on quantity (output) rather than price. Each firm chooses its production quantity given competitor outputs. The model captures:
- Strategic substitutes: if competitor produces more, you produce less
- Market price determined by total output through inverse demand
- Convergence to Cournot-Nash equilibrium quantities
- Sentiment bias: positive sentiment → expand output; negative → contract

### Game Type Detection

The parser auto-detects the appropriate model from keywords in the user's scenario description:

| Keywords (Chinese) | Game Model |
|--------------------|------------|
| 价格, 定价, 降价, 涨价, 价格战 | `price_war` (Bertrand) |
| 拍卖, 竞拍, 出价, 中标, 竞价 | `auction` (Vickrey) |
| 谈判, 协商, 讨价, 让步, 妥协 | `negotiation` |
| 产量, 产能, 输出, 份额, 竞争 | `output_competition` (Cournot) |

Domain templates can override this with `game_type_preference` (e.g., ecology defaults to Cournot).

## The Seven Application Domains

| Domain ID | Display Name | Typical Scenarios | Key Entities | Value Semantics |
|-----------|-------------|-------------------|--------------|-----------------|
| `micro_individual` | 个人存在与内在宇宙 (Micro-Individual) | Career transitions, habit formation, time allocation, health optimization, life planning | Personal roles, goals, life dimensions ("work," "health," "learning") | Time ratios, satisfaction scores, energy levels (0–100) |
| `social_network` | 人际关系的量子纠缠 (Social Network) | Team conflict mediation, family disputes, trust repair, relationship negotiation, community dynamics | People, family members, colleagues, factions ("老张," "小李," "HR") | Relationship closeness, trust index, compromise willingness |
| `creative_entertainment` | 创意与娱乐的无限游戏 (Creative Entertainment) | Virtual idol competition, content strategy, IP rivalry, fan engagement allocation | Content creators, IPs, studios ("星璃," "月见," "工作室") | Attention indices, fan engagement, content resource allocation |
| `enterprise` | 组织与管理的细胞级优化 (Enterprise) | Budget allocation, hiring vs. R&D, sales vs. product, growth strategy, resource negotiation | Departments, executives, teams ("CTO," "VP Sales," "R&D") | Budget amounts, resource allocations, KPI indices |
| `urban_infrastructure` | 城市与基础设施的神经末梢 (Urban Infrastructure) | Metro scheduling, congestion relief, waste management, public space activation, transport planning | Infrastructure nodes, transit lines, urban zones | Load rates (%), service capacity, passenger volume, budget |
| `planetary_ecology` | 生态与地球的免疫系统 (Planetary Ecology) | Endangered species conservation, habitat protection, pollution control, climate intervention, resource competition | Species, ecosystems, habitats, NGOs, nations ("中华鲟," "白鳍豚," "长江") | Population counts, habitat area (km²), pollution levels (ppm), conservation funds |
| `meta_civilization` | 元认知与文明演化 (Meta-Civilization) | AI safety governance, paradigm competition, ethical debates, ideology evolution, academic discourse | Schools of thought, paradigms, ideologies, values ("有效利他主义," "长期主义") | Acceptance indices, citation influence, discourse share, consensus strength |

**Adding new domains**: Call `GCE_register_domain(template)` at runtime with a new `DomainTemplate` instance. The domain is immediately available for classification and all pipeline stages.

## Plain-Language Conclusion Card

Every report includes a **第五章 / Act V** — a plain-language conclusion card (大白话结论卡片) that translates the professional game-theoretic analysis into concrete, jargon-free, immediately actionable guidance:

```
──────────────────────────────────────────────────
  预算分配结论卡
──────────────────────────────────────────────────

**一句话策略**：
下一阶段，把可调配的预算按大概50%给运营部（主力），25%给市场部（维持），
15%给研发部（防守），10%给销售部（兜底）。每个季度根据实际效果微调一次。

**为什么这么分？**
运营部势头正猛（指标上升了21%），每一份预算投给它的回报率最高。
市场部变化不大，保持现有投入就够。
研发部和销售部正在后退，保留最低限度的预算防止崩盘即可。

**接下来具体怎么操作（人话版）**
**立即**：
  - 运营部：把份额拉到总盘约50%，集中火力推上去。
  - 市场部：维持约25%份额，不增不减，静观其变。
  - 研发部：保留约15%兜底，避免彻底崩盘。
  - 销售部：保留约10%兜底。

**盯住两个数字**：
- 如果组织效能指数的单季度变化掉到1.5%以下，就开会重新研究。
- 如果整个轨迹偏离预计方向超过10%，马上暂停所有大动作，先观察。

**最直白的总结**：
现在的局势就像打仗：运营部是冲在最前面的先锋，资源优先倾斜给它。
销售部是最后一道防线，留一点预算别让它垮就行。
中间的几个保持现状观望，等局势明朗了再调。

**各参与方权重排名**：
  1. 运营部 [主力] ↑21% — 建议份额约50%
  2. 市场部 [次主力] ↑7% — 建议份额约25%
  3. 研发部 [防守] ↓2% — 建议份额约15%
  4. 销售部 [兜底] ↓18% — 建议份额约10%
```

The card uses **domain-specific language packages** — each of the 7 domains has its own set of terms:
- Ecology: "保护资金" (conservation funds), "综合生态指数" (composite ecological index), "种群数量" (population count)
- Personal: "精力/时间" (energy/time), "综合满意度指数" (composite satisfaction index)
- Social: "沟通精力/诚意" (communication energy/sincerity), "关系改善指数" (relationship improvement index)
- Enterprise: "预算" (budget), "组织效能指数" (organizational effectiveness index)
- Creative: "创作资源" (creative resources), "综合影响力指数" (composite influence index)
- Urban: "运力/服务资源" (capacity/service resources), "系统负载均衡度" (system load balance)
- Meta-civilization: "论证资源/发表机会" (argument resources/publication opportunities), "学术影响力指数" (academic influence index)

## Multi-Party Weight Ranking

For games with **3 or more players**, the conclusion card automatically switches from binary (attacker vs. defender) to **tiered multi-party ranking**:

**Direction-aware momentum scoring:**
- Players with positive momentum (>5% gain): full score — they deserve investment
- Players with neutral momentum (-5% to +5%): moderate score — maintain current allocation
- Players with negative momentum (< -5%): discounted score — minimize further investment

**Data-driven tier naming:**
- `主力` (Primary): strongest positive momentum, ~50–55% allocation
- `次主力` (Secondary): second-strongest positive momentum, ~25–28% allocation
- `维持` (Maintain): near-neutral, keep current level, ~15–17% allocation
- `防守` (Defensive): declining moderately, preserve minimum, ~10–15% allocation
- `兜底` (Floor): declining severely, absolute minimum to prevent collapse, ~5–10% allocation

Tier names are **not fixed** — they are dynamically assigned based on each player's actual trajectory. A player declining 16% will be labeled "兜底," not "维持," regardless of their rank position.

For 2-player games, the original binary attacker-defender format is preserved unchanged.

## Project Structure

```text
GCE_main.py                   # CLI entry point
config.yaml.example            # Configuration template
narratives.yaml                # Offline narrative template
requirements.txt               # Runtime dependencies
requirements-dev.txt           # Dev dependencies
Dockerfile                     # Container build
README.md                      # This file (English)
README_CN.md                   # Chinese version

gce/
  __init__.py

  core/                        # Genetic programming core (evolution)
    GCE_agent.py               # Agent process main loop — observe → predict → update
    GCE_breeder.py             # Tournament selection + crossover + mutation
    GCE_energy.py              # Reward/cull energy manager thread
    GCE_forager.py             # Sliding window feature extraction (36-dim)
    GCE_functions.py           # Expression tree operator set (10 functions)
    GCE_gene.py                # Gene dataclass + serialization/deserialization
    GCE_genetic_ops.py         # Crossover, mutation, tree generation, validation
    GCE_predictor.py           # Expression tree evaluator on feature vectors

  environment/                 # Environment simulation + sentiment
    GCE_base.py                # Abstract environment base + GCE_EventType enum
    GCE_simulator.py           # Lorenz RK4 integrator + multi-agent auction market
    GCE_event_bus.py           # multiprocessing.Queue wrapper for pub/sub
    GCE_adapters.py            # External data adapters (YFinance, CoinGecko)
    GCE_sentiment.py           # LLM-driven sentiment analysis + bias computation

  interface/                   # CLI / LLM client / parser / narrator / domain system
    GCE_cli.py                 # Main orchestrator — init, launch, interactive loop, shutdown
    GCE_llm_client.py          # DeepSeek/OpenAI-compatible API client with retry + stats
    GCE_parser.py              # Scene parser (LLM online, regex offline, domain injection)
    GCE_narrator.py            # Dual-output narrative generator (~1300 lines)
                               #   - Four-act professional report builder
                               #   - Plain-language conclusion card builder
                               #   - Multi-party weight ranking system
                               #   - 7-domain language package system
                               #   - Domain term override engine
    GCE_domain_templates.py    # Domain template system (~740 lines)
                               #   - 7 domain templates with 30–50 keyword triggers each
                               #   - Two-stage classification (keyword + LLM)
                               #   - Runtime domain registration API
                               #   - Domain-specific prompt injections for all pipeline stages

  simulation/                  # Sandbox simulation + chaos analysis
    GCE_schemas.py             # GCE_Participant, GCE_Scenario, GCE_SimulationResult dataclasses
    GCE_engine.py              # Elite forward simulation engine (~850 lines)
                               #   - All 4 game models (Bertrand, Vickrey, Negotiation, Cournot)
                               #   - Elite agent loading with NGRC fallback
                               #   - Sentiment bias integration
                               #   - Per-player trajectory tracking
    GCE_lyapunov.py            # Lyapunov exponent estimation + perturbation bifurcation analysis

  storage/                     # SQLite persistence layer
    GCE_database.py            # DDL schema + WAL-mode connection management + migrations
    GCE_repository.py          # Full CRUD data access layer (agents, predictions, events, genes)
    GCE_cleanup.py             # Background TTL cleanup thread (expired predictions)

  utils/                       # Utilities
    GCE_config.py              # YAML config loading + ${ENV_VAR} substitution + validation
    GCE_logging.py             # Rotating file logging with configurable levels
    GCE_retry.py               # Exponential backoff retry decorator for SQLite lock contention

tests/                         # Test suite
  GCE_test_config.py           # Config loading, env var substitution, validation
  GCE_test_database.py         # DB init, connection pool, schema migrations
  GCE_test_energy.py           # Energy reward formula correctness
  GCE_test_event_bus.py        # Event bus pub/sub, queue operations
  GCE_test_forager.py          # Sliding window correctness, feature extraction accuracy
  GCE_test_functions.py        # All 10 math operator correctness + edge cases
  GCE_test_gene.py             # Gene serialization/deserialization round-trip
  GCE_test_genetic_ops.py      # Crossover, mutation, tree generation, validation
  GCE_test_lyapunov.py         # Lyapunov exponent accuracy, bifurcation detection
  GCE_test_parser.py           # Offline regex parser (Chinese/English scenarios)
  GCE_test_predictor.py        # Expression tree evaluation correctness
  GCE_test_repository.py       # All CRUD operations (agents, predictions, events)
  GCE_test_simulator.py        # Lorenz RK4 integration accuracy
  integration/
    GCE_test_end_to_end.py     # End-to-end narrative generation pipeline
    GCE_test_evolution_loop.py # Mini evolution loop with sine wave environment
```

## Running Tests

```bash
# All fast tests
pytest tests/ -v

# Including slow integration test (evolution loop)
pytest tests/ -v -m "slow"

# Specific test file
pytest tests/GCE_test_predictor.py -v

# Specific test function
pytest tests/GCE_test_energy.py::test_reward_perfect_prediction -v
```

## Docker

```bash
docker build -t gce .
docker run -it gce
```

The Docker image runs in offline mode by default. To use LLM features, mount a config with `llm.enabled: true` and pass your API key:

```bash
docker run -it -e GCE_API_KEY="your-key" -v ./config.yaml:/app/config.yaml gce
```

## Key Design Principles

1. **Pure Python stdlib + SQLite** — No numpy, no pandas, no Redis, no external computation libraries. The expression tree evaluator, feature extraction engine, Lorenz RK4 integrator, and all game models are hand-written in pure Python.

2. **Multiprocessing architecture** — Each agent is an independent `multiprocessing.Process` with its own memory space. The energy manager, breeder, and cleanup run as `threading.Thread` instances in the main process. All cross-process communication goes through a single `multiprocessing.Queue`.

3. **SQLite WAL mode** — Enables concurrent read/write across all processes and threads without locking conflicts. All write operations use exponential-backoff retry for transient lock contention. No separate database server needed.

4. **Dual-mode LLM** — The entire user-facing pipeline (parsing → sentiment → narration) works fully offline with regex + rule-based engines. Enabling LLM upgrades every stage with domain-aware intelligence. Offline mode is the default — no API key required.

5. **Domain-first design** — All prompt injections, term overrides, and language packages are organized by domain. Adding a new domain requires only a `DomainTemplate` registration — no code changes to the parser, engine, sentiment analyzer, or narrator.

6. **Templates as parameters, not data** — Domain templates describe *what kind of thing to look for* but never contain hardcoded entity names, specific numerical values, or domain formulas. They are reference schemas, not example databases.

7. **Energy as universal fitness** — No separate loss function. No gradient descent. No backpropagation. Energy is the only currency of survival, reproduction, and selection. The energy formula is intentionally simple — `max(0, 1 - |error| / scale)` — so that the complexity emerges from the agents' strategies, not from the fitness landscape.

8. **Data-driven narrative** — Every sentence in the rule-based report is computed from actual simulation data (trajectories, Lyapunov exponents, Nash convergence scores, player trajectories). No static report templates with fill-in-the-blank slots. The LLM receives all computed data and is instructed to cite specific numbers.

9. **Chaos as information** — The Lorenz attractor was chosen specifically because it produces structured unpredictability. It is neither pure noise (trivial to average) nor simple periodicity (trivial to memorize). Agents must evolve genuine nonlinear models, not just pattern-matching heuristics.

10. **Graceful degradation** — Every component has a fallback: no elite agents → NGRC polynomial residuals; no LLM → regex parser + rule-based narrator; no sentiment → neutral bias; no domain match → generic template. The system never fails catastrophically — it degrades gracefully to the best available mode.

## License

Proprietary. Non-commercial use permitted. See license header in source files for full terms. For commercial licensing, contact <i126@126.com>.
