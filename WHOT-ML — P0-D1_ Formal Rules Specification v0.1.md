# WHOT-ML

## Phase 0 — Formalization

### P0-D1: Formal Rules Specification

**Version:** 0.1\
**Status:** Draft baseline specification\
**Environment name:** WHOT-NG-v1\
**Research program:** WHOT-ML

---

## 1. Purpose

This document defines the rules of the WHOT environment that will serve as the foundation for subsequent machine-learning research.

The objective is **not** to claim that this specification represents one universally authoritative version of WHOT.

WHOT is commonly played using a shared set of core mechanics while allowing players to negotiate or modify particular rules before a game begins. Published descriptions also document meaningful variations in the effects of cards, penalties, turn order, stacking, declarations, and scoring. Therefore, WHOT-ML treats the ruleset itself as an explicit configuration rather than an implicit assumption.

The baseline environment defined here is intended to represent a common Nigerian-style WHOT configuration while remaining extensible enough to support alternative negotiated rulesets.

---

# 2. Design Principles

WHOT-ML follows five principles.

### 2.1 Rules must be explicit

No rule should exist only as an undocumented assumption in the simulator.

Every rule affecting game state, legality, reward, turn order, or information must be represented explicitly.

### 2.2 Rules must be configurable

A different negotiated ruleset should be representable by changing configuration parameters rather than rewriting the environment.

### 2.3 Game mechanics and social conventions are distinct

The environment distinguishes between:

- rules governing what actions are legal,
- rules governing what actions do,
- declarations or announcements expected from players,
- penalties for violating those declarations,
- optional scoring/tournament systems.

### 2.4 Hidden information must remain genuinely hidden

Agents may observe only information available to them during normal play.

The simulator may maintain the complete underlying game state, but an agent must not receive opponents' private hands or other hidden state unless an experiment explicitly grants it.

### 2.5 Experimental variants must be reproducible

Every experiment must record the exact rules configuration under which games were generated.

---

# 3. Baseline Game Definition

WHOT-NG-v1 is defined as a sequential, multiplayer, imperfect-information card game.

### Players

The baseline supports:

**2–6 players.**

The number of players is a configuration parameter.

### Objective

A player wins a round by legally reducing their hand to zero cards.

### Direction

Baseline play proceeds clockwise.

Direction-changing rules are not part of the initial baseline but may be introduced as an optional variant.

### Information

Each player knows:

- their own hand,
- publicly revealed played cards,
- publicly observable actions and effects,
- the current game context.

Players do **not** know:

- opponents' private cards,
- the exact order of the draw pile,
- the complete hidden game state.

---

# 4. Card Set

The baseline uses the Nigerian WHOT deck containing 54 physical cards.

There are five ordinary suits/shapes:

1. Circle / Ball
2. Triangle / Angle
3. Cross
4. Square / Carpet
5. Star

The deck also contains five WHOT cards.

The ordinary cards are distributed according to the standard 54-card WHOT structure:

| Shape            | Numbers                                 |
| ---------------- | --------------------------------------- |
| Circle / Ball    | 1, 2, 3, 4, 5, 7, 8, 10, 11, 12, 13, 14 |
| Triangle / Angle | 1, 2, 3, 4, 5, 7, 8, 10, 11, 12, 13, 14 |
| Cross            | 1, 2, 3, 5, 7, 10, 11, 13, 14           |
| Square / Carpet  | 1, 2, 3, 5, 7, 10, 11, 13, 14           |
| Star             | 1, 2, 3, 4, 5, 7, 8                     |
| WHOT             | 20 × 5                                  |

Total:

**54 cards.**

Each physical card receives a unique internal identifier in the simulator even when two cards share the same shape and number.

Example:

`BALL_1_A`

`BALL_1_B`

would represent two physically distinct copies of the same card if the deck contained them.

---

# 5. Normal Play

At any ordinary turn, the active player may play a card that matches the currently required shape or number.

A card is normally legal when:

[\
shape(card)=required_shape\
]

OR

[\
number(card)=required_number\
]

A WHOT card is also legal under its wild-card rules.

If the player has no legal playable card, the player draws from the market/draw pile according to the active ruleset.

The precise consequences of drawing and whether the newly drawn card may immediately be played are configuration parameters and must be fixed before an experiment.

---

# 6. WHOT 20

The WHOT card is a wild card.

When a player plays a WHOT card, the player selects the shape that becomes the required shape for the next play.

Thus:

```text
WHOT
   ↓
player chooses STAR
   ↓
next legal play must match STAR
or use another legal WHOT rule
```

WHOT therefore differs from ordinary cards because its strategic effect includes a player-selected change to the game state.

The internal representation should therefore record both:

- the WHOT card being played,
- the shape selected by the player.

Example:

`PLAY(WHOT_3, STAR)`

---

# 7. Special Cards

The baseline Nigerian configuration assigns the following functions:

| Number | Name           | Baseline Effect                                      |
| -----: | -------------- | ---------------------------------------------------- |
|      1 | Hold On        | The player retains control and receives another turn |
|      2 | Pick Two       | The next player must defend or draw 2                |
|      5 | Pick Three     | The next player must defend or draw 3                |
|      8 | Suspension     | The next player loses/surrenders their turn          |
|     14 | General Market | Every other player draws 1 card                      |
|     20 | WHOT           | Wild card; player selects the next shape             |

These assignments are a baseline configuration rather than immutable WHOT law. Nigerian implementations explicitly describe these cards in broadly similar ways while allowing rule variation.

---

# 8. Card 1 — Hold On

When a player plays a 1:

- the current player retains the next turn,
- the current player may play again,
- the newly played card must obey the ordinary matching rules unless another rule modifies the state.

The exact interpretation of Hold On in multiplayer WHOT varies between rule sets. The baseline adopts the Nigerian-style interpretation in which the player who played the 1 continues playing.

---

# 9. Card 2 — Pick Two

When a player plays a 2:

- the next player becomes subject to a two-card penalty,
- the affected player may defend by playing another 2,
- if they do not defend, they draw the accumulated penalty.

Example:

```text
Player A → 2
Player B → 2
Player C → cannot/will not play 2
Player C → draws 4
```

Thus consecutive 2s increase the unresolved penalty.

The baseline enables stacking.

Formally, if (k) consecutive Pick Two cards have been played:

[\
Penalty = 2k\
]

The penalty is resolved when a player fails to continue the 2-chain.

---

# 10. Card 5 — Pick Three

When a player plays a 5:

- the next player becomes subject to a three-card penalty,
- the affected player may defend with another 5,
- if they do not defend, they draw the accumulated penalty.

Example:

```text
Player A → 5
Player B → 5
Player C → cannot/will not play 5
Player C → draws 6
```

The baseline enables stacking.

For (k) consecutive Pick Three cards:

[\
Penalty = 3k\
]

Published descriptions confirm the use of 5 as Pick Three and the existence of defensive stacking, while noting that variations exist.

---

# 11. Card 8 — Suspension

When a player plays an 8:

- the next player loses their turn,
- play continues with the following player.

The exact behavior of an 8 can vary in multiplayer games; the baseline uses the common interpretation that the immediately following player is suspended.

---

# 12. Card 14 — General Market

When a player plays a 14:

- every other active player draws one card from the market,
- the player who played the 14 does not draw.

Baseline behavior:

```text
Player A → 14

Player B → +1 card
Player C → +1 card
Player D → +1 card
Player A → unchanged
```

The effect is public and observable to all players.

---

# 13. Last-Card Declaration

WHOT-NG-v1 contains an explicit **last-card declaration rule**.

When a player's hand is reduced to exactly one card, the player must announce that they have their last card.

The baseline declaration is represented as:

```text
DECLARE_LAST_CARD
```

The declaration is observable to all players.

A player who attempts to win by playing an undeclared final card is penalized.

### WHOT-NG-v1 penalty

The baseline penalty is:

**Draw 1 card.**

This is intentionally recorded as a **ruleset-specific parameter**, because published WHOT descriptions give different last-card declaration mechanics and penalties. Some describe a penalty of two cards and additionally distinguish between a "last card" warning and a final "check up" declaration.

WHOT-ML therefore does not treat any single declaration penalty as universal.

---

# 14. Last-Card Rule as an Information Event

The last-card declaration is not merely a penalty mechanic.

It creates an observable information event.

Before declaration:

[\
Opponent\ does\ not\ necessarily\ know\ |H_i|=1\
]

After declaration:

[\
Opponent\ knows\ |H_i|=1\
]

Therefore the declaration changes the information available to every opponent.

This property must remain visible in the environment because it may later become relevant to:

- opponent modelling,
- belief-state inference,
- strategic adaptation,
- deceptive behavior experiments.

---

# 15. Optional Declaration Rules

The following may exist in alternative WHOT configurations but are **not enabled in WHOT-NG-v1**:

### Semi-last declaration

A player with two cards may be required to announce that they have two cards remaining.

### Final winning declaration

A separate declaration may be required when the final card is actually played.

### Special-card verbal declarations

Players may be required to verbally announce actions such as:

- Hold On
- Pick Two
- Pick Three
- Suspension
- General Market

These conventions are documented in some WHOT rulesets but their penalties vary.

These should therefore remain configurable.

---

# 16. Market / Draw Pile

The market is the source of cards drawn by players.

The environment maintains:

- a draw pile,
- a public played/discard pile.

When the draw pile becomes exhausted, the environment must follow the configured **market exhaustion rule**.

The baseline behavior will be:

1. Preserve the current top/call card.
2. Collect previously played cards underneath it.
3. Shuffle those cards.
4. Use the shuffled cards as the new market.

This behavior is documented in WHOT rule descriptions.

The exact implementation must ensure that the currently active top card cannot accidentally disappear from the public game state merely because the market is reshuffled.

---

# 17. Initial Setup

Before each round:

1. Construct the configured deck.
2. Shuffle the deck using a recorded random seed.
3. Deal the configured number of cards to each player.
4. Create the initial market.
5. Reveal the starting call/play card.
6. Determine the first player according to the configuration.
7. Begin play.

### Baseline starting hand

Each player receives:

**6 cards.**

The starting-hand size must remain configurable because different physical and digital implementations may use different setups.

---

# 18. Win Condition

A player wins when they legally play their final card and satisfy all required declaration rules.

Therefore:

[\
|H_i|=0\
]

is necessary but not sufficient when declaration requirements are enabled.

For the baseline:

```text
hand_size = 1
        ↓
DECLARE_LAST_CARD
        ↓
PLAY(final card)
        ↓
WIN
```

If the declaration requirement is violated, the final play does not produce a successful win and the configured penalty is applied.

---

# 19. Negotiated Rule Configuration

A fundamental feature of WHOT-ML is the concept of a **Rule Configuration**.

A game begins with an agreed configuration:

```text
WHOTConfig
```

The configuration defines all variable rules.

Conceptually:

```text
WHOTConfig
├── player_count
├── starting_hand_size
├── direction
├── special_card_mapping
├── pick_two_enabled
├── pick_two_stacking
├── pick_three_enabled
├── pick_three_stacking
├── hold_on_behavior
├── suspension_behavior
├── general_market_behavior
├── whot_behavior
├── semi_last_enabled
├── last_card_enabled
├── last_card_penalty
├── final_declaration_enabled
├── market_exhaustion_rule
└── scoring_rule
```

The exact schema will be formalized in P0-D3.

---

# 20. Default WHOT-NG-v1 Configuration

The baseline experiment should use:

```text
players = 4

starting_hand_size = 6

direction = clockwise

special_card_1 = HOLD_ON
special_card_2 = PICK_TWO
special_card_5 = PICK_THREE
special_card_8 = SUSPENSION
special_card_14 = GENERAL_MARKET
special_card_20 = WHOT

pick_two = enabled
pick_two_stacking = enabled

pick_three = enabled
pick_three_stacking = enabled

last_card_declaration = enabled
last_card_penalty = DRAW_1

semi_last_declaration = disabled

final_winning_declaration = disabled

direction_change = disabled

market_exhaustion = reshuffle_discard

objective = first_to_zero_cards
```

This is the **reference configuration** against which initial experiments should be reported.

---

# 21. Why Variability Is Part of the Research Problem

WHOT's rule variability should not be treated merely as an annoyance.

It creates a potentially useful experimental dimension.

Two agents can be evaluated under:

```text
Ruleset A
stacking = enabled
```

and:

```text
Ruleset B
stacking = disabled
```

allowing researchers to investigate how environmental rules affect:

- strategic difficulty,
- game length,
- branching factor,
- learning stability,
- agent performance,
- opponent modelling,
- transfer,
- strategy diversity.

Therefore, **ruleset variation is an intentional feature of WHOT-ML.**

---

# 22. Terminology

The simulator should standardize the following terminology.

| Human term            | Formal environment term        |
| --------------------- | ------------------------------ |
| Hand                  | Private player card set        |
| Market                | Draw pile                      |
| Call card / top card  | Current public play card       |
| Pick 2                | Draw-two penalty               |
| Pick 3                | Draw-three penalty             |
| Hold On               | Extra-turn effect              |
| Suspension            | Skip-next-player effect        |
| General Market        | Multi-player draw effect       |
| WHOT                  | Wild shape-selection card      |
| Last card             | One-card hand state            |
| Last-card declaration | Observable declaration event   |
| Round                 | Single game ending in a winner |
| Ruleset               | Complete WHOT configuration    |

---

# 23. Open Decisions for P0

The following issues are deliberately **not silently resolved** yet:

### 23.1 Drawing behavior

If a player cannot play:

- Must they draw exactly one?
- Do they continue drawing until they can play?
- Can the newly drawn card be immediately played?
- Does drawing end the turn?

This must be fixed in the simulator specification.

### 23.2 Pick-card resolution

We must explicitly specify:

- whether a player who can defend may choose not to,
- whether Pick Two can interact with Pick Three,
- whether WHOT can interrupt an active penalty,
- what happens to the turn after a penalty is resolved.

### 23.3 WHOT interaction with penalties

Different implementations may disagree on whether WHOT can cancel or otherwise interact with active Pick Two/Pick Three chains.

This must be explicitly configured rather than assumed.

### 23.4 First card

We must specify:

- how the initial call card is selected,
- what happens if the initial card is a special card,
- whether its effect immediately activates.

### 23.5 End-of-round special-card behavior

We must specify whether a player is allowed to win by playing:

- 2,
- 5,
- 8,
- 14,
- WHOT,
- or any other special card,

and whether that card's effect occurs before the game terminates.

### 23.6 Scoring

The first research environment will use direct round victory rather than tournament scoring.

Tournament/elimination scoring will be a separate configuration.

---

# 24. Formal Status

WHOT-NG-v1 is therefore defined as:

> **A configurable, multiplayer, imperfect-information card-game environment based on Nigerian WHOT, with a 54-card baseline deck, six-card starting hands, shape/number matching, special action cards, a wild WHOT card, hidden opponent hands, observable play history, and explicit negotiated-rule configuration.**

The rules in this document define the initial baseline only.

They are **not intended to represent every Nigerian WHOT ruleset**.

---

# 25. Phase 0 Completion Criterion

P0-D1 is considered complete when every gameplay decision affecting simulation has been converted into one of the following:

1. A fixed baseline rule,
2. An explicit configuration parameter,
3. An explicitly documented unresolved decision.

No undocumented gameplay assumption should remain.

The next document, **P0-D2 — Mathematical Environment Specification**, will translate this ruleset into formal game-state, observation, action, transition, reward, and information definitions suitable for machine-learning research.

---

## References

- Pagat, "Whot!" — documented Nigerian WHOT rules, card functions, declaration rules, and rule variations.
- Naija Whot — contemporary Nigerian implementation documenting the 1/2/5/8/14/20 action-card configuration and configurable rules.
- WHOT! — contemporary rules description documenting declarations, market exhaustion, and Nigerian rule variations.
