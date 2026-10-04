# WHOT-ML

## Phase 0 — Formalization

### P0-D2: Mathematical Environment Specification

**Version:** 0.1\
**Status:** Draft\
**Environment:** WHOT-NG-v1\
**Research Program:** WHOT-ML

---

# 1. Purpose

This document converts the WHOT-NG-v1 ruleset into a mathematical specification suitable for machine-learning research.

The specification defines:

- the complete hidden game state,
- each player's observable state,
- private and public information,
- legal actions,
- state transitions,
- rewards,
- terminal conditions,
- uncertainty,
- player beliefs,
- game history,
- and the relationship between the simulator and an individual learning agent.

The objective is to provide a sufficiently precise mathematical foundation that different implementations of WHOT-ML produce equivalent environments.

---

# 2. Problem Formulation

WHOT-ML is modeled as a:

> **finite, stochastic, sequential, multi-agent, partially observable decision process with configurable rules.**

For a fixed ruleset (R), the environment can be represented as:

[\
\mathcal{G} =\
(\mathcal{S},\mathcal{A},\mathcal{O},T,\Omega,\mathcal{R},\gamma)\
]

where:

- (\mathcal{S}) = complete state space,
- (\mathcal{A}) = action space,
- (\mathcal{O}) = observation space,
- (T) = state-transition function,
- (\Omega) = observation function,
- (\mathcal{R}) = reward function,
- (\gamma) = discount factor.

Because multiple players act within the environment, these components are player-dependent where appropriate.

---

# 3. Players

Let:

[\
N \in {2,3,4,5,6}\
]

be the number of players.

The player set is:

[\
P={1,2,\ldots,N}\
]

Each player has a unique identifier.

For a given player (i), the remaining players are:

[\
P\_{-i}=P\setminus{i}\
]

Player identity is public unless a future experiment explicitly introduces anonymous players.

---

# 4. Card Representation

Let the complete physical deck be:

[\
D={c_1,c_2,\ldots,c\_{54}}\
]

Each card (c) has attributes:

[\
c=(id,shape,value,effect)\
]

where:

- (id) uniquely identifies the physical card,
- (shape) identifies its suit/shape,
- (value) identifies its number,
- (effect) specifies its special behavior, if any.

For example:

[\
c=(c\_{17},STAR,5,PICK_THREE)\
]

A WHOT card may be represented as:

[\
c=(c\_{51},WHOT,20,WHOT)\
]

The physical-card identity is preserved internally even when cards have identical visible attributes.

---

# 5. Complete Game State

At timestep (t), the complete environment state is:

[\
S_t =\
(H_t,M_t,Q_t,C_t,K_t,E_t,L_t,\tau_t,R)\
]

where:

### (H_t) — Player hands

[\
H_t=(H_1^t,H_2^t,\ldots,H_N^t)\
]

where (H_i^t) is the set of cards currently held by player (i).

---

### (M_t) — Market

(M_t) is the ordered draw pile.

The order matters because drawing is stochastic with respect to the initial shuffle but deterministic once the seed and deck order are fixed.

---

### (Q_t) — Public play/discard pile

[\
Q_t=(q_1,q_2,\ldots,q_k)\
]

where the final element is the currently visible top card:

[\
top(Q_t)=q_k\
]

---

### (C_t) — Current call

(C_t) represents the currently required shape or other matching condition.

For ordinary play:

[\
C_t \in Shapes\
]

For example:

[\
C_t=STAR\
]

After a WHOT card, (C_t) is determined by the shape selected by the player.

---

### (K_t) — Current player

[\
K_t \in P\
]

This identifies whose decision it currently is.

---

### (E_t) — Active effects

(E_t) contains unresolved temporary effects.

Examples include:

```text
PICK_TWO_CHAIN
PICK_THREE_CHAIN
SUSPENSION
EXTRA_TURN
```

---

### (L_t) — Last-card declarations

(L_t) records publicly observable declaration events.

For example:

[\
L_i^t \in {0,1}\
]

where:

[\
L_i^t=1\
]

indicates that player (i) has made the required last-card declaration for their current one-card state.

---

### (\tau_t) — Game timestep

[\
\tau_t=t\
]

This records the progression of the environment.

---

### (R) — Ruleset

(R) contains the complete configuration defining the current game.

Therefore, two games with identical cards and history but different rulesets may represent different environments.

---

# 6. Hidden State vs Public State

This distinction is fundamental.

The complete simulator knows:

[\
S_t\
]

However, player (i) does not.

Player (i) receives only:

[\
O_i^t\
]

the observation available to that player.

The observation function is:

[\
O_i^t=\Omega_i(S_t,H\_{0},A\_{0})\
]

where the observation may depend on:

- the current state,
- previous observations,
- publicly observed history,
- and the player's own private information.

---

# 7. Player Observation

A player's observation consists of:

[\
O_i^t=\
(H_i^t,\
Q_t,\
C_t,\
K_t,\
E_t,\
L_t,\
\mathcal{H}\_t^{public},\
R)\
]

where:

- (H_i^t) = player's private hand,
- (Q_t) = public played cards,
- (C_t) = current call/required shape,
- (K_t) = current player,
- (E_t) = publicly observable effects,
- (L_t) = publicly observable declarations,
- (\mathcal{H}\_t^{public}) = public action history,
- (R) = agreed ruleset.

The player does **not** receive:

[\
H_j^t\
]

for any opponent (j\neq i).

The player also does not directly receive:

[\
M_t\
]

the ordered hidden market.

Thus:

[\
O_i^t \neq S_t\
]

This is the defining partial-observability property of WHOT-ML.

---

# 8. Information Partition

For each player (i), the state can be divided into:

### Private information

[\
I_i^{private}=H_i\
]

### Public information

[\
I^{public}=\
(Q,C,K,E,L,\mathcal{H}^{public},R)\
]

### Hidden information

[\
I_i^{hidden}=\
(H\_{-i},M)\
]

where:

[\
H\_{-i}=\bigcup\_{j\neq i}H_j\
]

Therefore:

[\
S=\
I_i^{private}\
\cup\
I^{public}\
\cup\
I_i^{hidden}\
]

This partition will be particularly important for Paper 3, where the objective is to infer hidden opponent information.

---

# 9. Action Space

Let:

[\
A_i(S_t)\
]

be the legal actions available to player (i) at state (S_t).

The global action space contains several action classes.

---

## 9.1 Play Card

[\
PLAY(c)\
]

where (c\in H_i).

A play is legal only if the card satisfies the current rules.

---

## 9.2 WHOT Shape Selection

When playing WHOT:

[\
PLAY(c,shape)\
]

where:

[\
shape\in Shapes\
]

For example:

[\
PLAY(WHOT_3,STAR)\
]

---

## 9.3 Draw

[\
DRAW\
]

The player draws from the market when required or permitted by the ruleset.

---

## 9.4 Last-Card Declaration

[\
DECLARE_LAST\
]

This is an observable action.

It becomes legal when the player satisfies the configured condition for making a last-card declaration.

---

## 9.5 Other Rule-Dependent Actions

Future configurations may introduce actions such as:

[\
PASS\
]

[\
DEFEND\
]

or other negotiated mechanics.

The environment must not assume that every WHOT configuration has the same action space.

---

# 10. Legal Action Set

The legal action set is:

[\
A_i^{legal}(S_t,R)\
]

This means legal actions depend on both:

1. the current game state,
2. the active ruleset.

For example, if a player holds:

[\
{BALL_4,STAR_7,CROSS_2}\
]

and the current call is:

[\
STAR\
]

then:

[\
PLAY(STAR_7)\
]

is legal.

If the player also holds a WHOT:

[\
PLAY(WHOT)\
]

is also legal.

A card that matches neither the current shape nor number is not legal.

---

# 11. Action Mask

For machine-learning implementations, the environment should expose a legal-action mask.

For an action vector:

[\
A={a_1,a_2,\ldots,a_m}\
]

define:

[\
mask(a_j)=\
\begin{cases}\
1 & a_j\text{ is legal}\\\
0 & a_j\text{ is illegal}\
\end{cases}\
]

Thus an agent may produce arbitrary logits over the action space while the environment prevents illegal actions from being selected.

This is important because WHOT's action space is **state-dependent**.

---

# 12. State Transition

The environment transitions from:

[\
S_t\
]

to:

[\
S\_{t+1}\
]

after an action:

[\
a_t\
]

according to:

[\
S\_{t+1}\sim T(S\_{t+1}|S_t,a_t,R)\
]

The transition is deterministic once all randomness is controlled by the environment's random seed, except where stochastic behavior is deliberately introduced.

Examples of stochastic events include:

- initial shuffle,
- drawing cards,
- reshuffling the market.

---

# 13. Example Transition

Suppose:

```text
Player 2
Hand = [BALL_3, STAR_5, WHOT]
Current shape = STAR
```

Player 2 chooses:

[\
PLAY(STAR_5)\
]

The transition performs:

1. Remove `STAR_5` from Player 2's hand.
2. Add `STAR_5` to the public play pile.
3. Update the current call.
4. Resolve any effect associated with the card.
5. Update the active player.
6. Update the public history.
7. Check the terminal condition.

Thus:

H_2^t\setminus{STAR_5}\
]

and:

Q_t\cup{STAR_5}\
]

---

# 14. Special-Card Transitions

Special cards modify the transition function.

For example, playing a 2 produces:

E_t + PICK_TWO\
]

The next player's legal actions are therefore affected.

Similarly, playing an 8 changes:

[\
K\_{t+1}\
]

according to the configured suspension rule.

A 14 modifies multiple hands:

H_j^t\cup{draw_j}\
]

for every eligible (j\neq i).

A WHOT modifies:

[\
C\_{t+1}=shape\_{selected}\
]

---

# 15. Penalty Chains

For a Pick Two chain:

[\
E_t=PICK2(k)\
]

where (k) is the number of unresolved Pick Two cards.

The accumulated penalty is:

[\
Penalty_2(k)=2k\
]

For Pick Three:

[\
E_t=PICK3(k)\
]

and:

[\
Penalty_3(k)=3k\
]

The transition function therefore depends not merely on the current card but on the unresolved effect history.

---

# 16. Public History

Let:

[\
\mathcal{H}*t=*\
*(a_0,a_1,\ldots,a*{t-1})\
]

be the sequence of actions observed up to time (t).

For player (i), the public portion is:

[\
\mathcal{H}\_t^{public}\
]

This history can contain:

- cards played,
- players who played them,
- cards drawn when observable,
- WHOT shape selections,
- declarations,
- special-card activations,
- turn order.

The history is essential because WHOT is not memoryless from the perspective of a player.

---

# 17. Belief State

Because opponents' hands are hidden, a rational agent may maintain a probability distribution over possible hidden states.

For player (i):

P(S_t|O_i^{0},A_i^{0})\
]

This is the player's **belief state**.

The belief state represents uncertainty about:

- opponent hands,
- remaining market,
- opponent intentions,
- future possible states.

For example, after observing a sequence of plays, the agent may assign:

[\
P(opponent\ has\ STAR_5)=0.73\
]

while assigning:

[\
P(opponent\ has\ BALL_5)=0.12\
]

These probabilities are not directly provided by the environment.

They must be inferred by the agent or by an auxiliary model.

---

# 18. Why Belief States Matter

This is one of the central research opportunities in WHOT.

Two game histories may look different but lead an intelligent agent to similar beliefs.

Conversely, two identical visible states can imply different hidden states depending on the history.

Therefore:

[\
O_t\
]

alone may not contain all information needed for optimal decision-making.

Instead:

[\
Belief_t=f(O\_{0})\
]

may provide a more useful representation.

This establishes the theoretical foundation for later experiments involving:

- recurrent networks,
- transformers,
- Bayesian inference,
- opponent models,
- latent-state models,
- memory architectures.

---

# 19. Reward

For the baseline environment, the primary objective is winning the round.

For player (i):

[\
r_i=\
\begin{cases}\
+1 & \text{if player }i\text{ wins}\\\
-1 & \text{if player }i\text{ loses}\
\end{cases}\
]

Intermediate rewards are initially:

[\
r_t=0\
]

for non-terminal transitions.

This creates a sparse-reward environment.

---

# 20. Optional Dense Rewards

The environment may later support experimental reward shaping.

Possible examples include:

### Hand reduction

[\
r_t =\
\alpha\
(\
|H_i^t|-|H_i^{t+1}|\
)\
]

### Opponent disruption

Reward for increasing opponents' hand sizes.

### Information gain

Reward for reducing uncertainty about hidden states.

However:

> **These rewards must not be used in the primary benchmark without explicit documentation.**

Otherwise we risk measuring whether an agent learned our reward engineering rather than whether it learned WHOT strategy.

---

# 21. Terminal State

A round terminates when a player successfully satisfies:

[\
|H_i|=0\
]

and all configured victory requirements are satisfied.

Define:

[\
Terminal(S_t)=\
\begin{cases}\
1 & \exists i: Winner_i(S_t)\\\
0 & otherwise\
\end{cases}\
]

Once:

[\
Terminal(S_t)=1\
]

no additional player actions occur within that round.

---

# 22. Illegal Actions

If an agent selects:

[\
a_t\notin A_i^{legal}(S_t)\
]

the environment must not silently reinterpret the action.

The environment should instead use one of two explicit modes.

### Training mode

The action is masked before execution.

### Evaluation/debug mode

The environment records an illegal-action event.

Possible evaluation metric:

[\
IllegalActionRate=\
\frac{#illegal\ actions}\
{#total\ action\ attempts}\
]

This helps detect agents that have learned poor representations of game legality.

---

# 23. Randomness and Reproducibility

Every environment instance must have a random seed:

[\
seed\in\mathbb{N}\
]

The seed controls:

- deck shuffling,
- market reshuffling,
- any stochastic opponent behavior,
- other explicitly stochastic processes.

Given:

[\
(seed,R,initial_state)\
]

the simulator should produce reproducible outcomes.

This is mandatory for scientific evaluation.

---

# 24. Environment Configuration

The complete environment is therefore parameterized by:

[\
R=\
(r_1,r_2,\ldots,r_k)\
]

where each (r_j) is a ruleset parameter.

For example:

[\
R=\
(\
N,\
H_0,\
stack_2,\
stack_5,\
last_declaration,\
last_penalty,\
market_rule,\
...\
)\
]

The ruleset becomes part of the experimental metadata.

---

# 25. Agent-Environment Relationship

The simulator occupies the following position:

```text
              COMPLETE WORLD
                   │
                   ▼
            ┌─────────────┐
            │  Simulator  │
            └──────┬──────┘
                   │
          private + public
             observation
                   │
                   ▼
            ┌─────────────┐
            │    Agent    │
            └──────┬──────┘
                   │
                 action
                   │
                   ▼
            ┌─────────────┐
            │  Simulator  │
            └─────────────┘
```

The simulator is effectively the **ground truth**.

The agent operates through an information bottleneck.

That bottleneck is intentional.

---

# 26. Four Different Levels of Knowledge

WHOT-ML distinguishes four concepts.

### Level 1 — True state

Everything the simulator knows.

[\
S_t\
]

### Level 2 — Observable state

Everything the player can currently observe.

[\
O_i^t\
]

### Level 3 — History

Everything the player has observed previously.

[\
O_i^{0}\
]

### Level 4 — Belief

The player's inferred probability distribution over hidden states.

[\
b_i(S_t)\
]

This distinction will become particularly important for the later papers.

---

# 27. Research Mapping

The mathematical environment directly supports the planned research program.

### Paper 1 — WHOT as an ML Environment

Uses:

[\
S,\ O,\ A,\ T,\ R\
]

to establish WHOT as a reproducible benchmark.

---

### Paper 2 — Learning to Play WHOT

Focuses on:

[\
\pi(a|O)\
]

where:

[\
\pi\
]

is the learned policy.

Potential comparison:

```text
Random
Rule-based
Search
RL
Self-play
```

---

### Paper 3 — Hidden-Hand Prediction

Focuses on:

[\
P(H\_{opponent}|O\_{0})\
]

The model attempts to infer hidden opponent cards from observable history.

---

### Paper 4 — Adaptive Opponent Modelling

Focuses on:

[\
P(strategy\_{opponent}|O\_{0})\
]

and potentially:

[\
\pi(a|O,b\_{opponent})\
]

where the policy conditions its decisions on an inferred opponent model.

---

# 28. Important Constraint: No Information Leakage

The environment must never expose hidden information accidentally.

The following are prohibited from a normal agent observation:

```text
opponent_hand
remaining_deck_order
hidden_card_locations
future_draws
simulator_random_seed
```

unless an experiment explicitly studies information leakage.

This should be tested automatically.

---

# 29. Multi-Agent Setting

For (N) players, the game is not simply:

[\
Agent \leftrightarrow Environment\
]

It is:

[\
Agent_1\
\leftrightarrow\
Agent_2\
\leftrightarrow\
\cdots\
\leftrightarrow\
Agent_N\
]

within a shared environment.

Each agent has:

[\
O_i^t\
]

and chooses:

[\
a_i^t\
]

according to its policy:

[\
\pi_i(a_i^t|O_i^{0})\
]

This means that changing one player's strategy can change the distribution of experiences observed by every other player.

This makes WHOT inherently multi-agent.

---

# 30. Self-Play

In self-play experiments:

[\
\pi_1=\pi_2=\cdots=\pi_N\
]

may initially be used.

However, identical policies do not imply identical behavior because:

- players receive different cards,
- players observe different private information,
- random events differ,
- game positions differ.

Self-play can therefore generate experience without requiring human opponents.

---

# 31. Population-Based Opponents

Later experiments may use a population:

[\
\Pi=\
{\pi_1,\pi_2,\ldots,\pi_m}\
]

An agent can then be evaluated against multiple strategies.

This will be particularly important for avoiding the problem:

> "Our agent became extremely good at beating the exact opponent distribution it trained against."

---

# 32. Evaluation Episodes

A single game is one episode:

[\
Episode=\
(S_0,a_0,S_1,a_1,\ldots,S_T)\
]

where (S_T) is terminal.

A training run consists of many episodes:

{Episode_1,\ldots,Episode_M}\
]

Performance should be evaluated across sufficiently many independently seeded episodes.

---

# 33. Primary Evaluation Metrics

The initial benchmark should report:

### Win rate

[\
WinRate_i=\
\frac{wins_i}{games_i}\
]

### Average finishing position

[\
Rank_i=\
\frac{1}{M}\
\sum\_{m=1}^{M}rank_i^{(m)}\
]

### Average game length

[\
GameLength=\
\frac{1}{M}\
\sum\_{m=1}^{M}T_m\
]

### Average hand size over time

Useful for understanding strategic behavior.

### Illegal-action rate

Useful for evaluating implementation correctness and learned legality.

---

# 34. Additional Metrics for Later Research

The environment should eventually support:

### Opponent prediction accuracy

[\
Accuracy=\
\frac{correct\ predictions}{predictions}\
]

### Calibration

Whether:

[\
P(prediction)\
]

corresponds to actual frequencies.

### Belief entropy

-\sum_xP(x)\log P(x)\
]

Useful for measuring uncertainty about hidden cards.

### Strategy diversity

Measure whether independently trained agents converge on similar or different strategies.

### Transfer performance

Measure performance when:

[\
R\_{train}\neq R\_{test}\
]

or:

[\
Opponent\_{train}\neq Opponent\_{test}\
]

---

# 35. Baseline Mathematical Model

The baseline WHOT environment can therefore be summarized as:

[\
\boxed{\
\mathcal{G}\_R=\
(\mathcal{S}\_R,\
\mathcal{A}\_R,\
\mathcal{O}\_R,\
T_R,\
\Omega_R,\
\mathcal{R}\_R,\
\gamma)\
}\
]

with:

[\
S_t\in\mathcal{S}\_R\
]

[\
O_i^t=\Omega_i(S_t)\
]

[\
a_i^t\in A_i(S_t,R)\
]

[\
S\_{t+1}\sim T_R(S\_{t+1}|S_t,a_t)\
]

and:

[\
r_i^t=\mathcal{R}*i(S_t,a_t,S*{t+1})\
]

The game ends when:

[\
Terminal(S_T)=1\
]

---

# 36. Core Research Insight

The central difficulty of WHOT-ML is not simply choosing the correct card.

The agent must solve:

[\
\boxed{\
Decision\ Making\
+\
Hidden\ Information\
+\
Memory\
+\
Opponent\ Modelling\
+\
Strategic\ Adaptation\
}\
]

The agent observes a partial projection of the true world and must act despite uncertainty.

This makes WHOT substantially more interesting as an ML environment than a simple fully observable card-placement task.

---

# 37. Phase 0 Status

P0-D2 establishes the mathematical interface between WHOT and machine learning.

The environment now has explicit definitions for:

- players,
- cards,
- complete states,
- observations,
- hidden information,
- actions,
- legal-action masks,
- transitions,
- special effects,
- penalty chains,
- public history,
- belief states,
- rewards,
- terminal conditions,
- randomness,
- reproducibility,
- multi-agent interaction,
- and evaluation.

### Remaining Phase 0 work

The next documents are:

**P0-D3 — Card & Rule Ontology**

A machine-readable formal description of every card, effect, rule, dependency, and configurable variant.

**P0-D4 — Simulator Specification**

The actual behavioral contract for the WHOT simulator, including turn resolution, drawing, reshuffling, special-card interactions, and edge cases.

**P0-D5 — Reproducibility & Experimental Protocol**

Seeds, episode generation, train/test separation, benchmark opponents, metrics, statistical reporting, and experiment configuration.

Only after these are complete should implementation begin.
