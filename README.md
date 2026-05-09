# Gaming Chaos Engine (GCE) v0.1.0

**Autonomous self-evolving digital life.** A multi-agent system where genetic programming meets chaotic dynamics — agents evolve predictive intelligence through natural selection atop a Lorenz-attractor environment with auction-market physics.

## Concept

GCE is an artificial life laboratory. 100 agents are born with random expression-tree "brains" and a 36-bit feature mask that determines what they perceive. They observe a chaotic environment, make predictions, and are rewarded or starved based on accuracy. High-energy agents breed through tournament selection + crossover + mutation. Low-energy agents die.

The environment is not random noise — it's a **Lorenz chaotic attractor** coupled with a **multi-agent auction market**, producing structured-yet-unpredictable time series. To survive, agents must evolve genuine predictive models of this chaos.

**No training data. No gradient descent. No backpropagation.** Just evolution.

## Architecture

```text
                         ┌──────────────────────────┐
                         │     CLI / User Input      │
                         └─────────────┬────────────┘
                                       │
                         ┌─────────────▼────────────┐
                         │       GCE_parser          │
                         │   (LLM or regex-based)    │
                         └─────────────┬────────────┘
                                       │ GCE_Scenario
                         ┌─────────────▼────────────┐
                         │      GCE_engine           │
                         │  Elite forward simulation │
                         │  Lyapunov + bifurcation   │
                         └─────────────┬────────────┘
                                       │ GCE_SimulationResult
                         ┌─────────────▼────────────┐
                         │     GCE_narrator          │
                         │  Four-act strategic report│
                         └──────────────────────────┘

══ Background Processes (continuous) ═══════════════════════════

  Environment ──► Queue ──► Agent₁, Agent₂, ... Agentₙ
  (Lorenz +         │       (Forager → Predictor → DB)
   Auction)         │
                    ▼
              Energy Manager ──► Breeder ──► Cleanup
              (reward/punish)    (crossover   (TTL purge)
                                  + mutate)
```

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run offline (no API key needed)
python GCE_main.py

# Run with LLM-powered scene parsing and narrative generation
export GCE_API_KEY="your-deepseek-api-key"
# Set llm.enabled: true in config.yaml
python GCE_main.py
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `--config, -c PATH` | Path to config file (default: `config.yaml`) |
| `--offline, -o` | Force offline mode (no LLM API calls) |
| `--reset-db` | Delete and recreate the database on startup |

**Interactive prompt:**

| Input | Description |
|-------|-------------|
| Any text | Describe a scenario (e.g. "3 companies competing on price over 60 days") |
| `status` | Show population size, energy range, generation stats |
| `quit` | Graceful shutdown |

## Configuration

All parameters are in `config.yaml`. Copy from `config.yaml.example` and edit.

### LLM

| Parameter | Default | Description |
|-----------|---------|-------------|
| `llm.enabled` | `false` | Enable LLM API for parsing and narration |
| `llm.api_key` | `${GCE_API_KEY}` | API key (from environment variable) |
| `llm.base_url` | `https://api.deepseek.com` | OpenAI-compatible API endpoint |
| `llm.model` | `deepseek-v4-pro` | Model name |
| `llm.temperature` | `0.7` | Sampling temperature |
| `llm.max_tokens` | `2048` | Max generation length |
| `llm.timeout` | `30.0` | Request timeout (seconds) |

### Evolution

| Parameter | Default | Description |
|-----------|---------|-------------|
| `population_initial` | `100` | Starting population size |
| `max_population` | `2000` | Hard population cap |
| `initial_energy` | `100.0` | Energy given to newborn agents |
| `reproduce_threshold` | `200.0` | Minimum energy to breed |
| `reproduction_cost` | `80.0` | Energy deducted from parents (split) |
| `base_reward` | `10.0` | Energy reward for perfect prediction |
| `error_scale` | `2.0` | Error normalization factor |
| `tournament_size` | `2` | Candidates per tournament selection |
| `crossover_rate` | `0.7` | Probability of subtree-swap crossover |
| `mutation_rate_base` | `0.2` | Base mutation probability |
| `mask_flip_rate` | `0.05` | Per-bit feature mask flip probability |
| `max_depth` | `8` | Max expression tree depth |
| `min_nodes` | `3` | Min expression tree nodes |
| `max_nodes` | `50` | Max expression tree nodes |
| `feature_count` | `36` | Feature pool size |
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
| `simulator.lorenz.beta` | `2.6666667` | Lorenz β parameter |
| `simulator.num_market_agents` | `10` | Auction market participants |
| `online_sources` | `[]` | Online data adapters (`yfinance`, `coingecko`) |

### Database

| Parameter | Default | Description |
|-----------|---------|-------------|
| `path` | `gce_data.db` | SQLite database file path |
| `prediction_ttl_days` | `7` | Retention period for predictions |
| `cleanup_interval_seconds` | `3600` | Cleanup check interval |

### Simulation

| Parameter | Default | Description |
|-----------|---------|-------------|
| `elite_count` | `10` | Top agents used for forward simulation |
| `future_steps` | `30` | Default prediction horizon |
| `perturbation_epsilon` | `0.001` | Perturbation magnitude for bifurcation detection |
| `divergence_threshold` | `0.5` | Divergence threshold for bifurcation detection |

## How It Works

### 1. Environment — Lorenz Chaos + Auction Market

The environment runs in its own process, generating events at a fixed tick rate. Each tick:

1. **Lorenz attractor** is integrated via RK4 (`sigma=10, rho=28, beta=8/3` — the classic chaotic regime)
2. **Market agents** (trend-followers, mean-reverters, random) submit bids/asks, with Lorenz x-component injected as a chaos source
3. **Clearing price** is computed from the auction, with Lorenz z-component added as noise
4. A `GCE_RawEvent` with price, volume, spread, and Lorenz state is published to the shared queue
5. ~10% of ticks also emit a **text event** (synthetic news headline)

### 2. Agents — Expression Trees + Feature Masks

Each agent is an independent process with:

- **Gene**: an expression tree (math operators: `+`, `-`, `*`, `/`, `sin`, `cos`, `exp`, `log`, `abs`, `ifgt`) with terminal nodes referencing a 36-dimension feature pool
- **Mask**: a 36-bit integer selecting which features the agent "sees"
- **Predictor**: evaluates the expression tree on extracted features → outputs a numeric prediction

**Feature pool** (36 dimensions):

| Indices | Features |
|---------|----------|
| 0–19 | Price lags 1–20 |
| 20–24 | Volume lags 1–5 |
| 25–29 | Spread lags 1–5 |
| 30–32 | Price SMA 5, 10, 20 |
| 33–34 | Price/volume volatility (5-period) |
| 35 | Sentiment score (text heuristic) |

### 3. Energy Economy

The energy formula is the sole selection pressure:

```text
error  = |predicted_price - actual_price|
reward = base_reward × max(0, 1 - error / error_scale)
```

- Perfect prediction → `+base_reward` energy
- Error ≥ error_scale → `0` reward
- Energy ≤ 0 → agent dies (process killed, status set to "dead")

### 4. Breeding — Tournament Selection + Genetic Operators

Every 2 seconds, the breeder thread:

1. Selects agents with energy ≥ `reproduce_threshold`
2. Pairs them via **tournament selection** (size=2)
3. Applies **subtree-swap crossover** (70% probability)
4. Applies **mutation** — uniformly picks from:
   - Terminal mutation (change feature index or jitter constant)
   - Function mutation (change operator)
   - Subtree replacement
   - Shrink/expand (remove or add tree depth)
   - Mask bit flip (toggle feature visibility)
5. Validates and inserts the child with `initial_energy`
6. Deducts `reproduction_cost / 2` from each parent

### 5. Simulation & Strategic Analysis

When the user describes a scenario (e.g. "two companies in a price war over 90 days"):

1. **Parser** extracts participants, initial prices, time horizon, objective (regex offline, LLM online)
2. **Engine** selects top-K elite agents, runs iterative forward simulation where each agent predicts the next value and consensus = median prediction
3. **Lyapunov analysis** estimates chaoticity of the predicted trajectory
4. **Perturbation analysis** tests sensitivity — where bifurcations emerge
5. **Narrator** generates a **four-act strategic report**:
   - **Act I** — Battlefield Holographic Reconstruction (regime identification)
   - **Act II** — Opponent Mind Mirror (elite strategy inference)
   - **Act III** — Full Game Tree Expansion (bifurcation path analysis)
   - **Act IV** — Strategy Orders Issued (actionable recommendations)

## Project Structure

```text
GCE_main.py                  # CLI entry point
config.yaml.example           # Configuration template
narratives.yaml               # Offline narrative template
requirements.txt              # Runtime dependencies
requirements-dev.txt          # Dev dependencies
Dockerfile                    # Container build

gce/
  core/                       # Genetic programming core
    GCE_agent.py              # Agent process main loop
    GCE_breeder.py            # Tournament selection + breeding
    GCE_energy.py             # Reward/cull energy manager
    GCE_forager.py            # Sliding window feature extraction
    GCE_functions.py          # Expression tree function set (10 ops)
    GCE_gene.py               # Gene data structure + serialization
    GCE_genetic_ops.py        # Crossover, mutation, tree generation
    GCE_predictor.py          # Expression tree evaluator

  environment/                # Environment simulation
    GCE_base.py               # Abstract base + event types
    GCE_simulator.py          # Lorenz RK4 + auction market
    GCE_event_bus.py          # multiprocessing.Queue wrapper
    GCE_adapters.py           # YFinance / CoinGecko data adapters

  interface/                  # CLI / LLM / parser / narrator
    GCE_cli.py                # Main orchestrator loop
    GCE_llm_client.py         # DeepSeek/OpenAI API client
    GCE_parser.py             # Scene parser (LLM or regex)
    GCE_narrator.py           # Four-act narrative generator

  simulation/                 # Sandbox simulation + chaos analysis
    GCE_schemas.py            # Scenario/Result dataclasses
    GCE_engine.py             # Elite forward simulation engine
    GCE_lyapunov.py           # Lyapunov exponent + perturbation

  storage/                    # SQLite persistence
    GCE_database.py           # Schema DDL + connection management
    GCE_repository.py         # Full CRUD data access layer
    GCE_cleanup.py            # Background TTL cleanup

  utils/                      # Utilities
    GCE_config.py             # YAML config + env var substitution
    GCE_logging.py            # Rotating file logging
    GCE_retry.py              # Exponential backoff retry decorator

tests/                        # Test suite (148 tests)
  GCE_test_config.py          # Config loading & validation
  GCE_test_database.py        # DB init, connection, schema
  GCE_test_energy.py          # Energy reward formula
  GCE_test_event_bus.py       # Event bus pub/sub
  GCE_test_forager.py         # Sliding window + feature extraction
  GCE_test_functions.py       # All math operators
  GCE_test_gene.py            # Gene serialization
  GCE_test_genetic_ops.py     # Crossover, mutation, pruning
  GCE_test_lyapunov.py        # Lyapunov + perturbation analysis
  GCE_test_parser.py          # Offline regex parser
  GCE_test_predictor.py       # Expression tree evaluation
  GCE_test_repository.py      # All CRUD operations
  GCE_test_simulator.py       # Lorenz RK4 accuracy
  integration/
    GCE_test_end_to_end.py        # End-to-end narrative generation
    GCE_test_evolution_loop.py    # Mini evolution with sine wave
```

## Running Tests

```bash
# All fast tests (147 tests)
pytest tests/ -v

# Including slow integration test (evolution loop)
pytest tests/ -v -m "slow"

# Specific test file
pytest tests/GCE_test_predictor.py -v
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

- **Pure Python stdlib + SQLite** — no numpy, no pandas, no Redis. The expression tree evaluator, feature extraction, and Lorenz integrator are all hand-written.
- **Multiprocessing architecture** — each agent is an independent `Process`; the energy manager, breeder, and cleanup run as `Thread`s in the main process. Communication via `multiprocessing.Queue`.
- **SQLite WAL mode** — enables concurrent read/write across all processes and threads. All writes use exponential-backoff retry on lock contention.
- **Dual-mode LLM** — works fully offline (regex parser + YAML template narrator) or online (LLM-powered parsing and narrative generation). Offline is the default.
- **Energy as universal fitness** — no separate loss function, no backpropagation, no gradient. Energy is the only currency of survival.

## License

Proprietary. Non-commercial use permitted. See license header in source files for full terms. For commercial licensing, contact <i126@126.com>.
