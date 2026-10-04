# WHOT-ML

## Phase 0 — Formalization

### P0-D3: Card & Rule Ontology

**Version:** 0.1\
**Status:** Draft\
**Environment:** WHOT-NG-v1\
**Research Program:** WHOT-ML

---

# 1. Purpose

This document defines the formal ontology of WHOT-ML.

The ontology specifies the entities that constitute the game and the relationships between them.

It defines:

- cards,
- shapes,
- values,
- effects,
- actions,
- conditions,
- declarations,
- penalties,
- turn modifiers,
- rule parameters,
- information events,
- and ruleset variants.

The purpose is to ensure that the simulator and future machine-learning systems operate on a consistent representation of WHOT.

The ontology is designed to support both:

1. the baseline WHOT-NG-v1 environment;
2. alternative negotiated rulesets.

---

# 2. Ontology Philosophy

The ontology separates four concepts that are easy to accidentally mix together:

### Card identity

**What physical card is this?**

### Card properties

**What does this card inherently represent?**

### Card effects

**What happens when this card is successfully played?**

### Rules

**Under what conditions does that effect happen, and how is it resolved?**

For example:

> A 5 is a card.

> "5" is its value.

> "Pick Three" is its effect.

> Whether Pick Three can stack is a ruleset property.

These must remain separate.

---

# 3. Entity Hierarchy

The core ontology is:

```text
WHOT
│
├── Card
│   ├── OrdinaryCard
│   └── WHOTCard
│
├── Shape
│
├── Value
│
├── Effect
│   ├── TurnEffect
│   ├── PenaltyEffect
│   ├── DrawEffect
│   ├── WildEffect
│   └── InformationEffect
│
├── Action
│   ├── PlayAction
│   ├── DrawAction
│   └── DeclarationAction
│
├── Condition
│
├── Declaration
│
├── Penalty
│
├── GameState
│
└── RuleSet
```

---

# 4. Shapes

The baseline ontology contains six shape identifiers:

```text
CIRCLE
TRIANGLE
CROSS
SQUARE
STAR
WHOT
```

`WHOT` is treated separately from the five ordinary shapes for matching purposes.

The ordinary shape set is:

[\
Shapes=\
{CIRCLE,TRIANGLE,CROSS,SQUARE,STAR}\
]

The full symbolic shape domain is:

[\
Shapes^\*=\
Shapes\cup{WHOT}\
]

---

# 5. Card Entity

Every physical card is represented as:

```text
Card {
    id
    shape
    value
    type
    effects
}
```

### Required properties

**id**

Unique physical-card identifier.

**shape**

The card's printed shape or WHOT identity.

**value**

The printed number.

**type**

One of:

```text
ORDINARY
WHOT
```

**effects**

A set/list of effects associated with the card.

---

# 6. Card Identity vs Card Type

Physical identity must remain distinct from logical identity.

For example:

```text
BALL_3_A
BALL_3_B
```

may have equivalent visible properties while remaining distinct physical cards.

Thus:

[\
id(c_1)\neq id(c_2)\
]

while:

[\
properties(c_1)=properties(c_2)\
]

This is important for:

- deck simulation,
- card tracking,
- hidden-information experiments,
- reproducibility,
- and future card-counting research.

---

# 7. Card Classes

## 7.1 Ordinary Card

An ordinary card has:

```text
type = ORDINARY
```

and contains:

- shape,
- number,
- optional special effect.

Examples:

```text
BALL_3
STAR_7
CROSS_10
```

---

## 7.2 WHOT Card

A WHOT card has:

```text
type = WHOT
value = 20
```

Its primary special effect is:

```text
WILD_SHAPE_SELECTION
```

The card itself does not permanently possess one of the five ordinary shapes.

Instead, its play produces a selected shape as part of the resulting state.

---

# 8. Baseline Card Ontology

| Value | Card Class | Baseline Effect      |
| ----: | ---------- | -------------------- |
|     1 | Ordinary   | HOLD_ON              |
|     2 | Ordinary   | PICK_TWO             |
|     3 | Ordinary   | None                 |
|     4 | Ordinary   | None                 |
|     5 | Ordinary   | PICK_THREE           |
|     7 | Ordinary   | None                 |
|     8 | Ordinary   | SUSPENSION           |
|    10 | Ordinary   | None                 |
|    11 | Ordinary   | None                 |
|    12 | Ordinary   | None                 |
|    13 | Ordinary   | None                 |
|    14 | Ordinary   | GENERAL_MARKET       |
|    20 | WHOT       | WILD_SHAPE_SELECTION |

Values absent from a shape's physical card set are not legal cards.

---

# 9. Effects

An effect is an abstract description of a state-changing operation caused by an action.

Formally:

[\
Effect:\
S_t\times A_t\rightarrow S\_{t+1}\
]

Effects may modify:

- hands,
- turn order,
- active player,
- required shape,
- penalties,
- declarations,
- public information,
- or the game terminal state.

---

# 10. Effect Categories

Effects are categorized as:

### Turn effects

Modify whose turn occurs next.

Examples:

```text
EXTRA_TURN
SKIP_NEXT
```

### Penalty effects

Create or modify obligations.

Examples:

```text
PICK_TWO
PICK_THREE
```

### Draw effects

Cause one or more players to receive cards.

Examples:

```text
DRAW_N
DRAW_ALL_OTHERS
```

### Wild effects

Modify the active matching condition.

Example:

```text
SELECT_SHAPE
```

### Information effects

Change information available to players.

Example:

```text
LAST_CARD_DECLARATION
```

---

# 11. Effect: HOLD_ON

Identifier:

```text
HOLD_ON
```

Type:

```text
TURN_EFFECT
```

Semantics:

The player who successfully plays the card receives another turn.

Formally:

[\
nextPlayer(S\_{t+1})=currentPlayer(S_t)\
]

unless another rule overrides this transition.

---

# 12. Effect: PICK_TWO

Identifier:

```text
PICK_TWO
```

Type:

```text
PENALTY_EFFECT
```

Parameters:

```text
penalty_amount = 2
stackable = configurable
```

When activated:

[\
penalty_2 \leftarrow penalty_2+2\
]

If stacking is enabled:

[\
P_2(k)=2k\
]

where (k) is the number of unresolved Pick Two cards.

---

# 13. Effect: PICK_THREE

Identifier:

```text
PICK_THREE
```

Type:

```text
PENALTY_EFFECT
```

Parameters:

```text
penalty_amount = 3
stackable = configurable
```

When activated:

[\
penalty_3\leftarrow penalty_3+3\
]

If stacking is enabled:

[\
P_3(k)=3k\
]

---

# 14. Effect: SUSPENSION

Identifier:

```text
SUSPENSION
```

Type:

```text
TURN_EFFECT
```

Baseline semantics:

[\
nextPlayer=\
successor(successor(currentPlayer))\
]

for a normal clockwise player ordering.

The exact suspension behavior is configurable for future variants.

---

# 15. Effect: GENERAL_MARKET

Identifier:

```text
GENERAL_MARKET
```

Type:

```text
DRAW_EFFECT
```

Baseline semantics:

For every player:

[\
j\neq i\
]

draw one card.

Thus:

[\
|H_j'|=|H_j|+1\
]

for every eligible opponent (j).

The active player does not draw.

---

# 16. Effect: WILD_SHAPE_SELECTION

Identifier:

```text
WILD_SHAPE_SELECTION
```

Type:

```text
WILD_EFFECT
```

Parameters:

```text
allowed_shapes =
    CIRCLE
    TRIANGLE
    CROSS
    SQUARE
    STAR
```

When activated, the player selects:

[\
s\in Shapes\
]

and:

[\
C\_{t+1}=s\
]

---

# 17. Effect: LAST_CARD_DECLARATION

Identifier:

```text
LAST_CARD_DECLARATION
```

Type:

```text
INFORMATION_EFFECT
```

This effect does not belong inherently to a card.

It is generated by a player action under a ruleset where last-card declaration is enabled.

Its purpose is to publicly reveal:

[\
|H_i|=1\
]

to all players.

---

# 18. Actions

Actions represent deliberate decisions by agents.

The ontology contains:

```text
PLAY
DRAW
DECLARE_LAST
```

with future extensibility.

---

# 19. PLAY Action

Structure:

```text
PLAY {
    card_id
    optional selected_shape
}
```

`selected_shape` is required when:

```text
card.type = WHOT
```

and prohibited otherwise unless a future ruleset explicitly permits it.

---

# 20. DRAW Action

Structure:

```text
DRAW {
    amount
}
```

Normally, `amount` is determined by the active game state rather than freely selected by the agent.

Therefore the agent's conceptual action may simply be:

```text
DRAW
```

while the environment determines:

[\
amount=f(S_t,R)\
]

---

# 21. DECLARE_LAST Action

Structure:

```text
DECLARE_LAST
```

The action is legal only when:

[\
|H_i|=1\
]

under the baseline ruleset.

It produces:

[\
L_i=1\
]

and creates a public information event.

---

# 22. Conditions

A condition specifies whether a rule or action applies.

Formally:

[\
Condition(S_t,A_t,R)\rightarrow{True,False}\
]

Examples include:

```text
MATCHES_SHAPE
MATCHES_NUMBER
IS_WHOT
HAS_ONE_CARD
HAS_LEGAL_MOVE
PENALTY_ACTIVE
DECLARATION_REQUIRED
GAME_TERMINAL
```

---

# 23. Matching Condition

A normal card (c) is playable when:

[\
Match(c,S_t)=\
(shape(c)=C_t)\
\lor\
(value(c)=value(top(Q_t)))\
]

WHOT is separately legal:

[\
type(c)=WHOT\
]

Therefore:

Match(c,S_t)\
\lor\
IsWHOT(c)\
]

subject to penalty and other ruleset constraints.

---

# 24. Penalty Condition

A penalty is active when:

[\
E_t\neq\emptyset\
]

and contains an unresolved penalty effect.

For example:

```text
PICK_TWO(4)
```

means the active player is facing a four-card unresolved penalty.

The legal action set must then be generated according to the ruleset.

---

# 25. Declaration Condition

For the baseline:

\begin{cases}\
True & |H_i|=1 \land declaration_enabled\\\
False & otherwise\
\end{cases}\
]

Whether the declaration must occur immediately when the hand reaches one card or only before the final play is a ruleset parameter.

WHOT-NG-v1 uses the declaration before attempting the final winning play.

---

# 26. Penalties

A penalty is a consequence applied after a rule violation or unresolved special-card effect.

A penalty is represented as:

```text
Penalty {
    type
    amount
    trigger
    recipient
}
```

Examples:

```text
DRAW_PENALTY
SKIP_PENALTY
INVALID_WIN
```

---

# 27. Last-Card Penalty

Baseline:

```text
type = DRAW_PENALTY
amount = 1
trigger = UNDECLARED_FINAL_CARD
recipient = violating_player
```

Therefore:

[\
|H_i'|=|H_i|+1\
]

if the player attempts to win without making the required declaration.

The exact penalty is a configurable ruleset property.

---

# 28. Rule

A rule is a conditional transformation of game behavior.

Represent:

```text
Rule {
    id
    condition
    action/effect
    priority
    configuration
}
```

Conceptually:

[\
Rule=\
(condition,\ effect,\ priority,\ parameters)\
]

---

# 29. Example Rule

The last-card rule can be represented as:

```text
Rule {
    id: LAST_CARD_DECLARATION

    condition:
        player.hand_size == 1
        AND last_card_declaration == true

    requirement:
        DECLARE_LAST

    violation:
        DRAW_PENALTY(1)
}
```

This demonstrates why rules should not be encoded directly into card definitions.

The 1-card state creates the requirement.

The player's action satisfies or violates it.

---

# 30. Rule Priority

Some game states may contain multiple applicable rules.

Therefore rules have an explicit priority.

For example:

```text
TERMINAL_RULE
PENALTY_RULE
CARD_EFFECT_RULE
TURN_RULE
NORMAL_MATCH_RULE
```

The exact priority hierarchy will be finalized in P0-D4.

The goal is to prevent ambiguous state transitions.

---

# 31. Rule Dependencies

Rules can depend upon other rules.

Example:

```text
PICK_TWO
   │
   └── depends on:
       PICK_TWO_ENABLED
       PICK_TWO_STACKING
       DEFENSE_RULE
```

Similarly:

```text
LAST_CARD_DECLARATION
   │
   ├── depends on LAST_CARD_ENABLED
   └── violation → LAST_CARD_PENALTY
```

This allows the environment to represent negotiated variants without duplicating entire rule systems.

---

# 32. Rule Configuration

A ruleset is a collection of parameter values.

Example:

```text
RuleSet {
    player_count: 4
    starting_hand_size: 6

    pick_two:
        enabled: true
        stacking: true

    pick_three:
        enabled: true
        stacking: true

    last_card:
        enabled: true
        penalty: DRAW_1

    whot:
        enabled: true
        shape_selection: true
}
```

---

# 33. Rule Variants

A rule variant changes one or more parameters without changing the fundamental game ontology.

For example:

### Variant A

```text
PICK_TWO_STACKING = TRUE
```

### Variant B

```text
PICK_TWO_STACKING = FALSE
```

Both remain WHOT.

The underlying ontology remains unchanged.

---

# 34. Rule Families

WHOT-ML groups configurable rules into families.

### Setup rules

- player count
- starting hand size
- starting player
- direction

### Matching rules

- shape matching
- number matching
- WHOT matching

### Special-card rules

- 1 behavior
- 2 behavior
- 5 behavior
- 8 behavior
- 14 behavior
- 20 behavior

### Penalty rules

- stacking
- penalty size
- defense
- failure consequences

### Declaration rules

- last-card declaration
- semi-last declaration
- final declaration
- declaration penalties

### Market rules

- draw behavior
- exhaustion
- reshuffling

### Victory rules

- final-card requirements
- scoring
- round termination

---

# 35. Public Events

The ontology distinguishes between an action and the information it produces.

For example:

```text
Action:
PLAY(WHOT)

Event:
WHOT_PLAYED

Event:
SHAPE_SELECTED(STAR)
```

Similarly:

```text
Action:
DECLARE_LAST

Event:
PLAYER_2_DECLARED_ONE_CARD
```

Events are public unless explicitly marked private.

---

# 36. Event Ontology

A public event may contain:

```text
Event {
    type
    actor
    timestamp
    parameters
    visibility
}
```

Examples:

```text
CARD_PLAYED
CARD_DRAWN
WHOT_SHAPE_SELECTED
LAST_CARD_DECLARED
PENALTY_ACTIVATED
PENALTY_RESOLVED
TURN_STARTED
TURN_SKIPPED
ROUND_ENDED
```

This event layer will become important for the opponent-modelling paper.

---

# 37. Private Events

Not all events are publicly observable.

For example:

```text
CARD_RECEIVED
```

is private when a player draws a card.

Player (i) can observe:

[\
CardReceived(i,c)\
]

but opponents should not automatically observe:

[\
c\
]

unless another rule reveals it.

This distinction is essential to preventing information leakage.

---

# 38. Card Knowledge States

For any card (c), a player can conceptually have one of several knowledge states:

```text
KNOWN_SELF
KNOWN_PUBLIC
INFERRED
UNKNOWN
```

For example:

If the agent holds a card:

```text
KNOWN_SELF
```

If the card was publicly played:

```text
KNOWN_PUBLIC
```

If the card has not appeared but inference suggests an opponent probably has it:

```text
INFERRED
```

If there is insufficient evidence:

```text
UNKNOWN
```

The simulator itself still knows the actual location.

---

# 39. Card Location Ontology

At any time, each physical card has exactly one location:

[\
Location(c)\in\
{\
HAND_1,\ldots,HAND_N,\
MARKET,\
PLAY_PILE\
}\
]

Therefore:

[\
\sum\_{l}I(Location(c)=l)=1\
]

for every card (c).

This provides an invariant that the simulator can automatically test.

---

# 40. Deck Conservation

The total number of cards must remain:

[\
54\
]

at all times.

Therefore:

54\
]

This invariant must hold except for no circumstance whatsoever: cards are moved, never created or destroyed.

If the simulator violates this:

> **The simulator is broken.**

This should be an automatic assertion during development.

---

# 41. Hand Conservation

Every legal card movement must have a corresponding source and destination.

For example:

[\
DRAW:\
M\rightarrow H_i\
]

[\
PLAY:\
H_i\rightarrow Q\
]

[\
RESHUFFLE:\
Q\rightarrow M\
]

These transformations preserve the total card count.

---

# 42. Turn Ontology

The game maintains:

```text
current_player
next_player
turn_modifier
```

Turn modifiers include:

```text
NORMAL
EXTRA_TURN
SKIP_NEXT
```

Future variants may introduce:

```text
REVERSE
MULTI_TURN
```

but these are not baseline mechanics.

---

# 43. State Machine

At the highest level, the game follows:

```text
SETUP
  ↓
DEAL
  ↓
INITIALIZE
  ↓
PLAYER_TURN
  ↓
ACTION
  ↓
RESOLVE_ACTION
  ↓
RESOLVE_EFFECT
  ↓
CHECK_DECLARATION
  ↓
CHECK_TERMINAL
  ↓
NEXT_TURN
  ↺
```

If a terminal condition occurs:

```text
CHECK_TERMINAL
      ↓
   GAME_OVER
```

---

# 44. Ontological Separation of Strategy

The ontology deliberately does **not** contain concepts such as:

```text
GOOD_MOVE
BAD_MOVE
AGGRESSIVE
DEFENSIVE
SMART
RISKY
BLUFF
```

These are not game mechanics.

They are properties that may emerge from player behavior.

This distinction is important for ML research.

The environment should define:

> what actions are possible.

The agent should discover:

> which actions are strategically useful.

---

# 45. Strategic Concepts as Derived Variables

Later research may define derived quantities such as:

[\
Risk(a,S)\
]

[\
ExpectedWinProbability(a,S)\
]

[\
OpponentThreat(S)\
]

[\
InformationGain(a,S)\
]

These are **not part of the base ontology**.

They belong to agent models or analysis layers.

---

# 46. Ontology Invariants

The simulator must enforce:

### Card conservation

[\
TotalCards=54\
]

### Unique location

Every physical card occupies exactly one location.

### Hand validity

A player cannot play a card not present in their hand.

### Shape validity

A WHOT-selected shape must belong to:

[\
{CIRCLE,TRIANGLE,CROSS,SQUARE,STAR}\
]

### Turn validity

Only the active player may perform a turn action.

### Terminal validity

No normal action may occur after the round has terminated.

### Ruleset validity

Every active configuration must contain valid parameter combinations.

---

# 47. Machine-Readable Representation

The final simulator should be able to serialize ontology objects.

Conceptually:

```text
{
    "card": {
        "id": "WHOT_03",
        "shape": "WHOT",
        "value": 20,
        "type": "WHOT",
        "effects": ["WILD_SHAPE_SELECTION"]
    }
}
```

A ruleset:

```text
{
    "ruleset_id": "WHOT-NG-v1",
    "players": 4,
    "starting_hand_size": 6,
    "pick_two": {
        "enabled": true,
        "stacking": true
    },
    "pick_three": {
        "enabled": true,
        "stacking": true
    },
    "last_card": {
        "enabled": true,
        "penalty": "DRAW_1"
    }
}
```

The exact serialization format will be determined during implementation.

---

# 48. Why the Ontology Matters for ML

A clean ontology allows us to separate:

[\
Game\ Representation\
]

from:

[\
Agent\ Architecture\
]

For example, the same WHOT environment can later be consumed by:

```text
Rule-based agent
        ↓
Search agent
        ↓
Q-learning agent
        ↓
DQN
        ↓
PPO
        ↓
Transformer
        ↓
Belief-state model
        ↓
Opponent-modeling architecture
```

The game does not change merely because the intelligence mechanism changes.

This makes experiments comparable.

---

# 49. Foundation for Paper 3

The ontology provides the variables required for hidden-hand prediction.

For opponent (j):

[\
H_j^t\
]

is hidden.

The model receives:

[\
O_i^{0}\
]

and attempts to estimate:

[\
P(H_j^t|O_i^{0})\
]

The ontology provides the exact definition of what counts as:

- a card,
- an opponent,
- a public event,
- a private event,
- a card location,
- and an observation.

---

# 50. Foundation for Paper 4

Opponent modelling can similarly define a latent opponent strategy:

[\
Z_j\
]

where (Z_j) may represent a learned latent behavioral profile.

The model can attempt:

[\
P(Z_j|O_i^{0})\
]

and condition the policy on that belief:

[\
\pi_i(a_t|O_i^{0},Z_j)\
]

The ontology therefore provides the event stream from which opponent behavior can be learned.

---

# 51. Final Ontology Summary

The WHOT-ML ontology can be summarized as:

```text
CARD
 ├── identity
 ├── shape
 ├── value
 ├── type
 └── effects

EFFECT
 ├── turn
 ├── penalty
 ├── draw
 ├── wild
 └── information

ACTION
 ├── play
 ├── draw
 └── declaration

CONDITION
 ├── matching
 ├── penalty
 ├── declaration
 └── terminal

RULE
 ├── condition
 ├── effect
 ├── priority
 └── parameters

EVENT
 ├── public
 └── private

RULESET
 ├── setup
 ├── matching
 ├── special cards
 ├── penalties
 ├── declarations
 ├── market
 └── victory
```

---

# 52. Phase 0 Status

P0-D3 establishes a formal vocabulary for WHOT-ML.

The project now has:

### P0-D1

**What WHOT-NG-v1 does.**

### P0-D2

**How WHOT-NG-v1 is represented mathematically.**

### P0-D3

**What the entities and rules of WHOT-NG-v1 actually are.**

Remaining:

### P0-D4

**How the simulator must behave.**

### P0-D5

**How experiments must be conducted and reproduced.**

After P0-D5, Phase 0 will be complete and we can begin constructing the actual environment.

---

## Phase 0 Principle

> **The simulator must know everything.**\
> **The agent must know only what a real player could know.**\
> **The researcher must know exactly what both know.**

That principle should govern the entire WHOT-ML research program.
