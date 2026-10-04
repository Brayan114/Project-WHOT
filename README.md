# WHOT-ML — Nigerian WHOT Research Simulator

**Version:** 0.1.0 (`WHOT-NG-v1.0` Frozen Baseline)  
**Research Program:** WHOT-ML (Papers 1–4)  
**Specification:** Phase 0 Formalization (P0-D1 to P0-D5 v0.1)

---

## 1. Overview

**WHOT-ML** is a deterministic, partially observable, multi-agent card-game research environment based on standard Nigerian WHOT. Built strictly for scientific machine-learning and reinforcement-learning research, it prioritizes:

1. **Mechanical correctness** — 100% faithful to the formal rules of Nigerian WHOT (P0-D1).
2. **Strict information boundaries** — Genuine hidden information separation: an agent's observation never exposes opponent hands, draw-pile order, future cards, or simulator RNG state (P0-D2).
3. **Deterministic reproducibility** — Given identical seeds, rulesets, and action sequences, simulations produce bitwise identical states and event logs (P0-D4, P0-D5).
4. **Ruleset configurability** — Every gameplay parameter is explicitly defined in `WHOTConfig`, allowing cross-ruleset and rule-variant transfer experiments without rewriting the engine.
5. **Machine-learning readiness** — Standard Gymnasium/PettingZoo-aligned discrete action space (76 frozen actions) with legal action masking.

---

## 2. Baseline Environment: WHOT-NG-v1

The reference baseline environment (`WHOT-NG-v1`) defines the standard Nigerian ruleset:

- **Deck**: 54 physical cards (49 ordinary suit cards across Circle, Triangle, Cross, Square, Star + 5 wild WHOT cards).
- **Players**: 4 players (configurable 2–6).
- **Starting Hand**: 6 cards dealt in clockwise round-robin order.
- **Direction**: Clockwise.
- **Normal Play**: Match current required shape OR match top card value OR play wild WHOT.
- **Draw Restriction**: If a legal playable card exists in hand, `DRAW` is strictly illegal. If no playable card exists, `DRAW` is the only legal normal card action. The drawn card cannot be played immediately.
- **Card 1 (Hold On)**: Grants the current player another turn (`EXTRA_TURN`). Cannot be used as the winning final card (`final_card_one_policy = REJECT_LEGALITY`).
- **Card 2 (Pick Two)**: Penalty of 2 cards. Defended only by another 2. Consecutive 2s stack (+2 each).
- **Card 5 (Pick Three)**: Penalty of 3 cards. Defended only by another 5. Consecutive 5s stack (+3 each).
- **Card 8 (Suspension)**: The next player in turn order is skipped (`SKIP_NEXT`).
- **Card 14 (General Market)**: Every other active player in clockwise order draws exactly 1 card.
- **Card 20 (WHOT)**: Wild card. The playing player chooses one of the five ordinary shapes to become the active required shape. Cannot defend active Pick Two or Pick Three penalties.
- **Last-Card Declaration**: When a player has 1 card in hand, they must declare (`DECLARE_LAST`). If an undeclared final card is played to win, the attempted victory is rejected, a `LAST_CARD_DECLARATION_VIOLATION` event is logged, the player draws 1 penalty card, and the game continues.
- **Market Exhaustion**: When the market is empty, the top card of the play pile is preserved, and all previously played cards underneath are shuffled into a new market.
- **Scoring**: Terminal zero-sum rewards: winner receives `+1.0`, all losers receive `-1.0`.

---

## 3. Architecture & Modular Design

The codebase enforces strict separation of responsibilities:

```text
whot_ml/
├── __init__.py                  # Public exports
├── version.py                   # Simulator and baseline environment version
├── card.py                      # Physical cards, shapes, suits, canonical 54-card deck
├── ruleset.py                   # WHOTConfig and baseline parameters
├── action.py                    # Frozen 76-action space and bidirectional mapping
├── state.py                     # Full ground-truth GameState (all hands, market, RNG)
├── turn_manager.py              # Turn sequencing, clockwise progression, skip/extra turns
├── rng_manager.py               # Deterministic seed-controlled random number generator
├── invariants.py                # Strict card conservation, uniqueness, and state checks
├── rules_engine.py              # Playability checking, legal action generation, action masking
├── effect_resolver.py           # Resolution pipeline for special cards, penalties, market, victory
├── event.py                     # Public and private structured event definitions
├── observation.py               # PlayerObservation and ObservationGenerator (information boundary)
├── serializer.py                # Lossless serialization and restoration of GameState
├── metrics.py                   # Episode metrics and batch statistics aggregation
├── environment.py               # Unified GameEnvironment research API
├── runner.py                    # Headless game and batch evaluation harness
└── agents/
    ├── base.py                  # Abstract Agent class
    ├── random_agent.py          # Uniform RandomLegalAgent
    └── rule_based_agent.py      # Transparent heuristic RuleBasedAgent
```

---

## 4. Frozen 76-Action Space

The action space is permanently mapped to 76 discrete action indices:

| Action Indices | Action Type | Description |
|:---|:---|:---|
| `0` – `48` | `PLAY` | Play an ordinary physical card (49 cards in canonical order: Circle 1..14, Triangle 1..14, Cross 1..14, Square 1..14, Star 1..8) |
| `49` – `73` | `PLAY_WHOT` | Play one of the 5 WHOT cards with a selected shape (5 cards × 5 shapes: Circle, Triangle, Cross, Square, Star) |
| `74` | `DRAW` | Draw from the market (legal only when no playable cards exist or taking penalties) |
| `75` | `DECLARE_LAST` | Declare having 1 card remaining (legal only when hand size is 1 and undeclared) |

---

## 5. Information Boundary Architecture

To support research in imperfect-information games (e.g. Paper 3 hidden-hand inference):

```text
             ┌─────────────────────────┐
             │   Complete World State  │
             │       (GameState)       │
             └────────────┬────────────┘
                          │
            ObservationGenerator.generate()
                          │
                          ▼
             ┌─────────────────────────┐
             │    PlayerObservation    │  <--- STRICT INFORMATION BOTTLENECK
             │ (own hand, public pile, │       - Zero opponent cards
             │  call, public counts)   │       - Zero market ordering
             └────────────┬────────────┘       - Zero RNG state
                          │
                          ▼
                   ┌─────────────┐
                   │    Agent    │
                   └─────────────┘
```

- **Leakage Auditing**: Tested via automated property tests where two states with identical public state and Player 0 hand, but completely swapped opponent hands, produce strictly equal `PlayerObservation` objects (`obs_A == obs_B`).
- **Event Visibility**: Public `CARD_DRAWN` events omit card identities (`card_id = None`), while private `PRIVATE_CARD_RECEIVED` events are delivered exclusively to the drawing player.

---

## 6. Quick Start & Usage Examples

### Running a Game with Baseline Agents

```python
from whot_ml.environment import GameEnvironment
from whot_ml.agents import RandomLegalAgent, RuleBasedAgent

# Create environment and agents
env = GameEnvironment()
agents = {
    0: RuleBasedAgent(name="RuleBased-0", seed=42),
    1: RandomLegalAgent(name="Random-1", seed=43),
    2: RandomLegalAgent(name="Random-2", seed=44),
    3: RandomLegalAgent(name="Random-3", seed=45),
}

# Reset environment
obs_dict = env.reset(seed=1000)

terminated = False
truncated = False

while not (terminated or truncated):
    curr = env.current_player
    obs = env.observe(curr)
    action = agents[curr].act(obs)
    step_result = env.step(action, acting_player=curr)
    
    terminated = step_result.terminated
    truncated = step_result.truncated

print(f"Winner: Player {env.winner} in {env.state.turn_count} turns!")
```

### Running Batch Evaluations

```python
from whot_ml.agents import RandomLegalAgent, RuleBasedAgent
from whot_ml.runner import run_batch_evaluation

agents = {
    0: RuleBasedAgent(name="RuleBased-0", seed=1),
    1: RandomLegalAgent(name="Random-1", seed=2),
    2: RandomLegalAgent(name="Random-2", seed=3),
    3: RandomLegalAgent(name="Random-3", seed=4),
}

# Run 100 independent seeded games
batch = run_batch_evaluation(agents, num_games=100, base_seed=50000)
print(batch.summary())
```

---

## 7. Testing Strategy

The test suite contains 85+ unit, integration, and property tests organized by subsystem:

- `test_deck.py`: 54 cards distribution, uniqueness, and immutability.
- `test_action_space.py`: Frozen 76-action space bijection and boundaries.
- `test_ruleset.py`: Ruleset configuration and serialization round-trip.
- `test_rng.py`: Controlled RNG determinism and checkpointing.
- `test_turn_manager.py`: Clockwise, skip, and extra turn progression.
- `test_game_state.py`: Dealing mechanics and initial card policies.
- `test_invariants.py`: Invariant validation and diagnostic failure reporting.
- `test_rules_engine.py`: Matching rules, draw restrictions, penalty defense, declaration legality.
- `test_effects.py`: Individual special card effects (1, 2, 5, 8, 14, 20).
- `test_market_semantics.py`: Market ordering and discard pile recycling.
- `test_declaration_and_victory.py`: Declaration state-machine and terminal victory.
- `test_combined_interactions.py`: Multi-effect interactions and edge cases.
- `test_victory_pipeline_order.py`: Strict pipeline order regression test.
- `test_information_leakage.py`: 6 critical information-boundary and serialization tests.
- `test_god_agent_boundary.py`: Validation tool boundary test.
- `test_event_visibility.py`: Public vs private event streams.
- `test_environment_api.py`: Lifecycle, turn enforcement, and truncation.
- `test_baseline_agents.py`: RandomLegalAgent and RuleBasedAgent heuristics.
- `test_multi_game_evaluation.py`: Batch evaluation across player counts.
- `test_property_invariants.py`: 50-game per-step invariant validation.
- `test_reproducibility.py`: Deterministic replay and seed schedule consistency.
- `test_information_boundary_stress.py`: Comprehensive attribute and JSON audit.

Execute all tests:
```bash
pytest -v
```

---

## 8. Version Freeze: WHOT-NG-v1.0

With all Phase 0 specifications (P0-D1 to P0-D5) satisfied, the environment core is **frozen at `v0.1.0` (`WHOT-NG-v1.0`)**. Subsequent research (Paper 1 benchmark baselines, Paper 2 RL training, Paper 3 hidden-hand prediction, and Paper 4 opponent modelling) builds on this frozen baseline.
