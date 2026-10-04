# WHOT-ML — P0-D5: Reproducibility & Experimental Protocol v0.1

## Status

**Phase:** Phase 0 — Foundational Formalization\
**Document:** P0-D5 — Reproducibility & Experimental Protocol\
**Version:** 0.1\
**Baseline Environment:** WHOT-NG-v1\
**Purpose:** Define how WHOT-ML experiments must be configured, executed, recorded, evaluated, and reproduced.

---

# 1. Purpose

WHOT-ML is intended to support machine-learning research rather than merely produce a playable WHOT program.

Therefore, a result such as:

> "Agent A won 63% of its games."

is scientifically incomplete.

A reproducible experiment must allow another researcher to determine:

- which WHOT rules were used;
- which simulator version was used;
- which agents participated;
- how they were initialized;
- which random seeds were used;
- how many games were played;
- what information each agent received;
- what training procedure was used;
- what evaluation procedure was used;
- what metrics were measured;
- and whether the reported result survives different random seeds and opponents.

This document establishes that protocol.

---

# 2. Reproducibility Principle

Every reported WHOT-ML result should be reconstructible from:

```text
Simulator Version
+
Ruleset
+
Experiment Configuration
+
Agent Configuration
+
Training Configuration
+
Random Seeds
+
Evaluation Protocol
```

No result should depend on undocumented implementation choices.

---

# 3. Experiment Identity

Every experiment receives a unique identifier.

Example:

```text
WHOT-P2-BASELINE-001
```

The identifier should encode:

```text
paper / research question
experiment family
experiment number
```

Example:

```text
P3-HHP-003
```

could mean:

```text
Paper 3
Hidden-Hand Prediction
Experiment 3
```

---

# 4. Mandatory Experiment Metadata

Every experiment must record:

```text
experiment_id
date
simulator_version
ruleset_version
ruleset_configuration
code_version
training_configuration
evaluation_configuration
agent_versions
random_seeds
hardware
software_environment
```

Where possible, software dependencies should be version-pinned.

---

# 5. Ruleset Specification

A WHOT experiment must never simply state:

> "We played standard WHOT."

Because WHOT contains regional and household rule variations.

Instead, the experiment must provide the exact ruleset.

For example:

```text
players = 4
starting_hand = 6

matching = shape OR number

draw_policy = draw_one_if_no_legal_play

pick_two_defence = pick_two
pick_five_defence = pick_five

pick_two_stacking = enabled
pick_five_stacking = enabled

whot_defends_penalty = false

one_effect = hold_on
eight_effect = suspension
fourteen_effect = general_market

last_card_declaration = enabled
last_card_penalty = draw_one

one_can_finish = false

drawn_card_immediate_play = false

market_exhaustion = reshuffle_discard
```

This configuration becomes part of the experiment record.

---

# 6. WHOT-NG-v1 Baseline

Unless an experiment explicitly studies another ruleset, the baseline is:

```text
Players: 4

Starting hand: 6

Deck: 54 cards

Normal play:
    same shape OR same number

WHOT:
    wild + select next shape

2:
    Pick Two
    defended by 2
    stacking enabled

5:
    Pick Three
    defended by 5
    stacking enabled

8:
    Suspension

1:
    Hold On
    same player receives another turn
    cannot be the winning final card

14:
    General Market
    every opponent draws 1

Draw:
    if no legal card exists, draw 1

Drawn card:
    cannot immediately be played

Last-card declaration:
    enabled

Undeclared attempted victory:
    draw 1

Final special cards:
    permitted except 1

Market:
    draw from top
    reshuffle discard pile when exhausted
    preserve current top card

Rewards:
    winner +1
    losers -1
```

Any deviation must be documented.

---

# 7. Random Seed Protocol

Randomness must be explicitly controlled.

Each experimental run receives a seed.

For example:

```text
seed = 10001
seed = 10002
seed = 10003
...
```

The seed controls stochastic environment behavior such as:

- deck shuffling;
- initial WHOT call when required;
- market reshuffling;
- randomized starting order where applicable.

---

# 8. Seed Independence

Experiments must not rely on a single random seed.

A reported result should normally aggregate over multiple independent seeds.

For example:

```text
Seeds:
1001
1002
1003
1004
1005
...
```

The number of seeds should be selected according to computational feasibility and experimental importance.

Small exploratory experiments may use fewer seeds.

Final reported experiments should use substantially more.

---

# 9. Training / Evaluation Separation

Training and evaluation environments must be separated.

An agent must not be evaluated using:

- games it trained on;
- opponents it directly memorized;
- seeds it used to optimize hyperparameters;
- leaked future information.

The evaluation environment should contain fresh games.

---

# 10. Opponent Protocol

WHOT is a multi-agent game.

Therefore, evaluating an agent only against one opponent is insufficient.

At minimum, experiments should consider:

```text
Random Agent
Rule-Based Agent
Search-Based Agent
Self-Play Agent
Previously Trained Agent
Unseen Agent
```

The exact set depends on the research question.

---

# 11. Baseline Agents

WHOT-ML should establish progressively stronger baselines.

## 11.1 Random Agent

Chooses uniformly from legal actions.

Purpose:

```text
minimum competence baseline
```

---

## 11.2 Random-Legal Agent

Chooses uniformly from all currently legal card plays but follows mandatory game mechanics.

This distinguishes:

```text
random decision-making
```

from:

```text
invalid-action behavior
```

---

## 11.3 Rule-Based Agent

Uses simple heuristics.

Possible heuristics include:

- prefer matching-number special cards;
- preserve WHOT cards;
- reduce hand size;
- use Pick cards strategically;
- avoid wasting valuable cards.

The exact heuristic must be documented.

---

## 11.4 Search-Based Agent

A search or Monte-Carlo agent may be introduced once the simulator is validated.

Its computational budget must be reported.

Examples:

```text
simulation count
search depth
time limit
rollout policy
```

---

## 11.5 Learned Agent

Learning agents must report:

- architecture;
- parameter count;
- optimizer;
- learning rate;
- batch size;
- training episodes;
- replay buffer;
- exploration strategy;
- self-play configuration;
- checkpoint selection method.

---

# 12. Self-Play Protocol

When self-play is used, the experiment must specify:

```text
number of agents
population size
opponent sampling
checkpoint frequency
policy update frequency
```

A critical distinction must be made between:

```text
self-play training performance
```

and:

```text
generalization performance
```

An agent winning against copies of itself does not establish that it is generally strong.

---

# 13. Evaluation Opponent Pool

For serious evaluation, the agent should be tested against a fixed opponent pool.

Example:

```text
25% Random
25% Rule-Based
25% Search-Based
25% Learned
```

The exact mixture should be specified before evaluation whenever possible.

This prevents researchers from unconsciously selecting opponents that make their agent look strong.

---

# 14. Unseen-Opponent Evaluation

Paper 4 in particular should evaluate performance against opponents not encountered during training.

This tests:

```text
generalization
```

rather than memorization.

Example:

```text
Training:
    Opponents A, B, C

Evaluation:
    Opponents D, E, F
```

---

# 15. Match Protocol

Individual games can be noisy.

Therefore evaluation should consist of many games.

A match configuration should specify:

```text
number_of_games
seat_assignment
starting_player_policy
seed_set
opponent_set
```

---

# 16. Seat Randomization

In multiplayer WHOT, player position can affect outcomes.

Therefore seat assignment should be randomized or systematically rotated.

For example:

```text
Game 1:
Agent A = Player 1

Game 2:
Agent A = Player 2

Game 3:
Agent A = Player 3

Game 4:
Agent A = Player 4
```

This prevents positional advantages from being mistaken for agent strength.

---

# 17. Starting-Player Control

The first player may have a systematic advantage.

Therefore experiments should either:

1. randomize the starting player; or
2. rotate starting positions evenly.

The method must be stated.

---

# 18. Primary Evaluation Metrics

WHOT-ML should not rely on win rate alone.

Core metrics include:

### Win Rate

```text
wins / games
```

### Average Finishing Position

Important in multiplayer settings.

### Average Hand Size

Measured at selected points or at termination.

### Game Length

Number of turns until termination.

### Illegal Action Rate

Especially important during early agent development.

### Special-Card Usage

Including:

- WHOT usage;
- Pick Two usage;
- Pick Three usage;
- Hold On usage;
- Suspension usage;
- General Market usage.

---

# 19. Statistical Reporting

Results should include uncertainty wherever practical.

For example:

```text
Win rate:
63.4% ± 2.1%
```

The exact uncertainty method should be specified.

For multiple agents, confidence intervals or bootstrap intervals may be used.

The important principle is:

> A tiny difference in average win rate should not automatically be interpreted as a meaningful improvement.

---

# 20. Repeated Experiments

Experiments should be repeated across:

- random seeds;
- opponent configurations;
- player positions;
- possibly rulesets.

A result that appears only under one seed is not considered robust.

---

# 21. Ablation Studies

Novel methods should be evaluated using controlled ablations.

For example, if a proposed agent uses:

```text
Opponent model
+
Memory
+
Belief state
+
Self-play
```

the study should test:

```text
Full model

Without opponent model

Without memory

Without belief state

Without self-play
```

This identifies which component actually contributes to performance.

---

# 22. Paper 1 Experimental Protocol

Paper 1 establishes WHOT as an ML environment.

Its experiments should focus primarily on:

```text
environment validity
state representation
observation representation
action-space structure
hidden-information properties
```

Important measurements include:

```text
state-space characteristics
action-space size
average legal-action count
game length distribution
hand-size distribution
frequency of special cards
frequency of penalties
frequency of market reshuffles
```

The goal is to demonstrate that WHOT forms a meaningful computational environment rather than merely presenting a playable implementation.

---

# 23. Paper 2 Experimental Protocol

Paper 2 studies learning to play WHOT.

The comparison should progressively increase agent sophistication:

```text
Random
    ↓
Rule-Based
    ↓
Search / Monte Carlo
    ↓
RL / Learned Policy
    ↓
Self-Play
```

Questions include:

- How difficult is WHOT for learning agents?
- How quickly can agents learn?
- Does self-play produce stronger policies?
- How does performance change with opponent strength?
- Does performance transfer to unseen opponents?

---

# 24. Paper 3 Experimental Protocol

Paper 3 studies hidden-hand prediction.

The central problem is:

```text
Given observable history H_t,
estimate:

P(opponent_card | H_t)
```

The simulator provides exact hidden ground truth.

Training examples may therefore contain:

```text
Input:
    public history
    current observation
    previous actions

Target:
    opponent's actual hidden hand
```

Evaluation should include:

```text
card-level accuracy
multi-label accuracy
precision
recall
F1
probability calibration
Brier score
belief entropy
```

The model must never receive the true opponent hand as an input feature.

---

# 25. Paper 4 Experimental Protocol

Paper 4 studies adaptive opponent modelling.

The agent observes an opponent's behavior and attempts to infer a latent strategy.

Potential opponent categories might include:

```text
Aggressive
Conservative
Special-card preserving
WHOT preserving
Penalty-focused
Random
Risk-sensitive
```

These labels are experimental constructs, not part of the base WHOT ontology.

Evaluation should ask:

```text
Can the model identify the opponent?

Can it adapt?

Does adaptation improve win rate?

How quickly does adaptation occur?

Does adaptation transfer to previously unseen strategies?
```

---

# 26. Temporal Evaluation for Adaptation

For adaptive agents, performance should be evaluated across time.

For example:

```text
Early game
Middle game
Late game
```

or:

```text
First 5 turns
First 10 turns
First 20 turns
...
```

This allows researchers to measure:

```text
adaptation speed
```

rather than merely final performance.

---

# 27. Hidden-Information Integrity

Every experiment involving hidden information must pass an information-leakage audit.

The audit must verify that:

```text
agent observation
```

contains no direct or indirect representation of:

```text
opponent hand
market order
future draws
RNG state
future actions
future outcomes
```

This is especially important for Papers 3 and 4.

A model achieving suspiciously high prediction performance should trigger a leakage investigation before the result is interpreted as scientific evidence.

---

# 28. Rule-Variant Experiments

Because WHOT has negotiated rules, rulesets themselves may become an experimental dimension.

For example:

```text
Ruleset A:
Pick 2 stacking enabled

Ruleset B:
Pick 2 stacking disabled
```

or:

```text
Ruleset A:
WHOT cannot defend penalties

Ruleset B:
WHOT can defend penalties
```

The experiment should compare:

```text
game difficulty
strategy
learning speed
agent robustness
```

across rulesets.

This could become a separate research direction later.

---

# 29. Cross-Ruleset Generalization

A particularly interesting experiment is:

```text
Train on Ruleset A
        ↓
Evaluate on Ruleset B
```

This asks whether an agent learns:

```text
WHOT-specific strategy
```

or merely memorizes:

```text
one particular ruleset.
```

Possible future experiment:

```text
Train:
    WHOT-NG-v1

Test:
    WHOT-NG-v1.1
```

where only one mechanic changes.

---

# 30. Human Comparison

Human evaluation may eventually be introduced.

If humans participate, the protocol must record:

```text
ruleset
player experience level
number of games
seat position
opponents
game outcomes
```

Human results should not be directly compared with agents unless the information and rules available to both are equivalent.

---

# 31. Computational Budget

Every experiment should report its computational budget.

For training:

```text
GPU/CPU
training duration
episodes
environment steps
parameter count
memory
```

For search:

```text
search time
nodes explored
simulation count
depth
```

For inference:

```text
average decision time
maximum decision time
hardware
```

This matters because an agent that wins only after receiving vastly more computation may not represent a meaningful algorithmic improvement.

---

# 32. Checkpoint Selection

The evaluation checkpoint must be selected without using the final test set.

Valid approach:

```text
Training
   ↓
Validation
   ↓
Select checkpoint
   ↓
Frozen model
   ↓
Final test
```

The final test results should not influence model selection.

---

# 33. Result Storage

Every completed experiment should generate a machine-readable result record.

Conceptually:

```text
{
    experiment_id,
    simulator_version,
    ruleset,
    agent_versions,
    seed,
    game_count,
    win_rate,
    finishing_position,
    game_length,
    illegal_action_rate,
    special_card_statistics
}
```

For Paper 3:

```text
{
    prediction_accuracy,
    precision,
    recall,
    f1,
    calibration,
    brier_score
}
```

For Paper 4:

```text
{
    opponent_identification_accuracy,
    adaptation_speed,
    pre_adaptation_win_rate,
    post_adaptation_win_rate,
    transfer_performance
}
```

---

# 34. Raw Data Preservation

Researchers should preserve:

```text
raw game trajectories
experiment configurations
model checkpoints
evaluation results
random seeds
logs
```

Summary statistics alone are insufficient for serious reproducibility.

Whenever storage permits, raw trajectories should be retained.

---

# 35. Version Control

The following should be version-controlled:

```text
simulator source
ruleset definitions
experiment configurations
agent implementations
training scripts
evaluation scripts
analysis scripts
```

A paper should identify the exact code revision used to generate its reported results.

---

# 36. Bug Handling

If a simulator bug is discovered after experiments have been run:

1. document the bug;
2. determine which experiments are affected;
3. preserve the original results;
4. fix the simulator;
5. increment the relevant version;
6. rerun affected experiments;
7. compare old and corrected results.

Previous results must never simply be overwritten.

---

# 37. Reproduction Test

Before publication, a selected subset of experiments should be reproduced from the stored configuration.

The reproduction should verify:

```text
same ruleset
same simulator version
same agent version
same seeds
same evaluation protocol
```

and should produce results within the expected stochastic tolerance.

---

# 38. Minimal Reproducibility Package

A published WHOT-ML experiment should ideally provide:

```text
ruleset configuration
experiment configuration
seed list
simulator version
agent version
evaluation code
result files
documentation
```

This should allow another researcher to reproduce the experiment without reconstructing undocumented assumptions from the paper.

---

# 39. Experimental Naming Convention

Recommended structure:

```text
PAPER-QUESTION-VARIANT-SEED
```

Examples:

```text
P1-ENV-BASELINE-1001
P2-RL-SELFPLAY-1001
P2-RL-SELFPLAY-1002
P3-HHP-BELIEF-1001
P4-OPPONENT-ADAPT-1001
```

---

# 40. Research Notebook

For each major experiment, researchers should record:

```text
Hypothesis
Configuration
Expected result
Actual result
Unexpected behavior
Interpretation
Next experiment
```

This prevents the research process from becoming:

```text
run experiment
look at number
invent explanation afterward
```

Instead, hypotheses should precede measurements whenever possible.

---

# 41. Scientific Interpretation

WHOT-ML results should distinguish between:

### Descriptive findings

What happened?

Example:

> Agents trained with self-play achieved higher average win rates against the rule-based baseline.

### Mechanistic findings

Why did it happen?

Example:

> Improvement appears to result from better management of penalty cards.

### Generalization findings

Does it work elsewhere?

Example:

> The improvement remained after evaluation against previously unseen opponents.

These should not be conflated.

---

# 42. Statistical and Experimental Caution

A higher win rate does not automatically mean a better algorithm.

Possible alternative explanations include:

```text
better starting positions
easier opponents
more training
more computation
favorable ruleset
random seed variation
implementation bugs
information leakage
```

Experiments should therefore be designed to eliminate these explanations where practical.

---

# 43. Phase 0 Completion Criteria

Phase 0 is considered complete when:

### P0-D1

Formal rules are defined.

### P0-D2

The mathematical environment is defined.

### P0-D3

Cards, effects, actions, rules, and states are formally represented.

### P0-D4

The simulator behavior is operationally specified.

### P0-D5

Experiments are reproducible and scientifically controlled.

At this point:

```text
WHOT
 ↓
Formal Game
 ↓
Mathematical Environment
 ↓
Ontology
 ↓
Simulator Contract
 ↓
Experimental Protocol
```

forms a complete research foundation.

---

# 44. Transition to Phase 1

After Phase 0, the project moves into:

# Phase 1 — Simulator Implementation & Validation

The first objective is **not** to train an AI.

The first objective is to prove that the environment itself works.

Phase 1 should therefore proceed approximately as:

```text
Implement deck
        ↓
Implement state
        ↓
Implement rules
        ↓
Implement legal actions
        ↓
Implement effects
        ↓
Implement observations
        ↓
Implement RNG
        ↓
Implement logging
        ↓
Implement serialization
        ↓
Write tests
        ↓
Run invariant/property tests
        ↓
Run complete random games
        ↓
Validate against manually played examples
        ↓
Freeze WHOT-NG-v1
```

Only after this should learning experiments begin.

---

# 45. Final Phase 0 Principle

The purpose of Phase 0 was never simply to make a list of WHOT rules.

It was to establish a chain of scientific accountability:

```text
RULE
  ↓
FORMAL DEFINITION
  ↓
MATHEMATICAL STATE
  ↓
SIMULATOR BEHAVIOR
  ↓
OBSERVATION
  ↓
AGENT DECISION
  ↓
EXPERIMENT
  ↓
MEASUREMENT
  ↓
REPRODUCIBLE RESULT
```

If a result changes, we should be able to trace **where and why**.

If an agent performs surprisingly well, we should be able to determine whether it learned something real or exploited an implementation flaw.

If another researcher wants to reproduce the work, they should not need to ask:

> "Wait, which version of WHOT did you guys actually mean?"

That is the standard WHOT-ML adopts.

---

# 46. Phase 0 Deliverables

The completed foundational specification consists of:

```text
P0-D1 — Formal WHOT-ML Rules Specification

P0-D2 — Mathematical Environment Specification

P0-D3 — Card & Rule Ontology

P0-D4 — Simulator Specification

P0-D5 — Reproducibility & Experimental Protocol
```

Together these constitute:

> **WHOT-ML Phase 0: Foundational Specification v0.1**
