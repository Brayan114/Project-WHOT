# WHOT-ML — P0-D4: Simulator Specification v0.1

## Status

**Phase:** Phase 0 — Foundational Formalization\
**Document:** P0-D4 — Simulator Specification\
**Version:** 0.1\
**Baseline Environment:** WHOT-NG-v1\
**Purpose:** Define the exact operational behavior, interfaces, state handling, randomness, logging, validation, and testing requirements for a reproducible WHOT-ML simulator.

---

# 1. Purpose

The WHOT-ML simulator is the controlled experimental environment in which all subsequent WHOT machine-learning research will occur.

Its purpose is not merely to "make a WHOT game."

It must provide a scientifically controlled environment in which:

1. games can be executed correctly;
2. different rulesets can be compared;
3. agents receive only information available to real players;
4. every stochastic event can be reproduced;
5. every action and state transition can be logged;
6. edge cases are handled explicitly;
7. experiments can be repeated across researchers and machines;
8. the simulator itself does not become an uncontrolled source of experimental variation.

The simulator therefore acts as the operational implementation of P0-D1, P0-D2, and P0-D3.

---

# 2. Design Principles

The simulator follows five central principles.

## 2.1 Complete internal knowledge

The simulator maintains the complete game state:

- every physical card;
- every player's complete hand;
- draw pile order;
- discard pile order;
- active penalties;
- current shape/call;
- turn state;
- declarations;
- ruleset;
- random-number-generator state.

Nothing is hidden from the simulator.

## 2.2 Restricted agent observation

An agent must receive only information a real player is permitted to know.

The simulator may internally know that an opponent holds the Circle 7, but the opponent's observation must not contain that fact unless it has become publicly observable.

This separation is fundamental to Papers 1–4.

## 2.3 Deterministic replay

Given the same:

- simulator version;
- ruleset;
- seed;
- initial configuration;
- sequence of agent actions;

the same game must be reproducible.

## 2.4 Ruleset configurability

The simulator must not hard-code WHOT rules into the architecture.

The ruleset is a parameter.

This permits experiments such as:

- different player counts;
- different starting hand sizes;
- alternative draw rules;
- different stacking rules;
- alternative last-card declaration rules;
- alternative scoring systems;
- alternative interpretations of special cards.

WHOT rule variation is itself a potential research variable.

## 2.5 No accidental intelligence

The simulator must perform game mechanics, not strategic reasoning.

It may determine whether an action is legal.

It must not:

- choose a strategically optimal card;
- reveal hidden cards to an agent;
- recommend actions;
- infer opponent strategy;
- perform search on behalf of an agent.

The environment executes rules. The agent supplies decisions.

---

# 3. Environment Lifecycle

Every episode follows the following high-level lifecycle:

```text
CREATE ENVIRONMENT
        ↓
LOAD RULESET
        ↓
INITIALIZE RNG
        ↓
CREATE DECK
        ↓
SHUFFLE
        ↓
DEAL HANDS
        ↓
INITIALIZE DRAW / PLAY PILES
        ↓
SELECT STARTING PLAYER
        ↓
INITIALIZE CURRENT CALL
        ↓
PLAYER TURN
        ↓
GENERATE LEGAL ACTIONS
        ↓
RECEIVE ACTION
        ↓
VALIDATE ACTION
        ↓
EXECUTE ACTION
        ↓
RESOLVE CARD EFFECT
        ↓
RESOLVE DECLARATION
        ↓
CHECK TERMINAL CONDITION
        ↓
ADVANCE TURN
        ↓
REPEAT
        ↓
GAME OVER
```

The simulator must never bypass a state transition merely because an unusual event occurs.

---

# 4. Environment Configuration

Each environment instance is created from a complete ruleset configuration.

At minimum the configuration contains:

```text
player_count
starting_hand_size
turn_direction
starter_policy

draw_policy
draw_play_policy

stacking_enabled
stacking_mode

whot_defends_penalty
whot_shape_selection

last_card_declaration_enabled
last_card_declaration_timing
last_card_violation_penalty

initial_card_policy

market_exhaustion_policy

special_card_mapping

scoring_policy

maximum_turns
random_seed
```

Additional parameters may be added in later versions.

The complete configuration must be serializable.

A published experiment must therefore identify its ruleset using a machine-readable configuration rather than relying solely on prose.

---

# 5. Baseline Ruleset: WHOT-NG-v1

Unless otherwise stated, all initial experiments use the baseline environment:

```text
Environment: WHOT-NG-v1

Players: 4
Hand size: 6

Direction: clockwise
Starting player: randomized

Normal play:
    match shape OR match number
    OR play WHOT

Draw:
    draw one card

Drawn-card immediate play:
    disabled in baseline

Pick Two:
    active penalty = 2
    stacking = enabled
    defence = another Pick Two

Pick Three:
    active penalty = 3
    stacking = enabled
    defence = another Pick Three

WHOT:
    wild
    player selects one of five ordinary shapes

1:
    Hold On / same player receives another turn

8:
    next player is suspended

14:
    every other player draws one card

Last-card declaration:
    enabled
    player must declare having one card
    undeclared attempted victory = draw one penalty card

Market exhaustion:
    preserve current top card
    reshuffle previous discard pile

Terminal:
    player legally plays final card and satisfies declaration requirements

Scoring:
    winner = +1
    losers = -1
```

Any experiment changing one or more values must identify the resulting ruleset explicitly.

---

# 6. Physical Deck Creation

The simulator creates exactly 54 physical cards.

Each physical card possesses a unique identifier.

For example:

```text
CIRCLE_1
CIRCLE_2
...
STAR_8
WHOT_01
WHOT_02
...
WHOT_20
```

The identifier is not itself meaningful to the agent.

Two physical cards may share the same logical properties.

For example:

```text
WHOT_03
WHOT_04
```

are different physical cards despite being logically identical.

The simulator must preserve physical identity throughout the game.

This allows exact reconstruction of card movement.

---

# 7. Initial Setup

## 7.1 Reset

Calling:

```text
reset(seed)
```

must:

1. clear all previous state;
2. load the configured ruleset;
3. initialize the RNG from the supplied seed;
4. construct the complete deck;
5. verify deck integrity;
6. shuffle the deck;
7. create players;
8. deal starting hands;
9. establish the draw pile;
10. initialize the discard pile;
11. select the starting player;
12. initialize the active call/shape;
13. initialize effect state;
14. initialize declaration state;
15. initialize history and event logs;
16. run invariant validation.

The returned observation must correspond to a valid starting state.

---

# 8. Dealing

Cards are dealt according to the configured starting-hand size.

Baseline:

```text
4 players × 6 cards = 24 cards dealt
```

The remaining cards become the market/draw pile, after accounting for initialization of the play pile.

Cards must be distributed using a defined dealing order.

Baseline:

```text
Player 1
Player 2
Player 3
Player 4
Player 1
Player 2
...
```

The dealing procedure must be deterministic given the RNG seed.

The exact deal sequence must be recorded in the simulator's internal event log, although private card identities must never appear in another player's observation.

---

# 9. Initial Play Card

The simulator requires a card to establish the initial play state.

Baseline policy:

```text
INITIAL_CARD_POLICY = NO_EFFECT_START
```

The first play-pile card is therefore placed normally, but its special effect is not activated during setup.

Examples:

### Initial card = Circle 7

The current call becomes:

```text
CIRCLE
```

### Initial card = Circle 14

The current call becomes:

```text
CIRCLE
```

but General Market does not activate.

### Initial card = WHOT

WHOT cannot establish an ordinary shape by itself.

Therefore the environment selects the initial active shape uniformly from the five ordinary shapes using the environment RNG.

This RNG-based initialization must be logged.

Alternative initial-card policies may be introduced later, including:

```text
RESOLVE_SPECIAL
DISCARD_UNTIL_ORDINARY
DISCARD_UNTIL_NON_WHOT
CUSTOM
```

These are separate experimental rulesets.

---

# 10. Current Call / Active Shape

The simulator maintains:

```text
current_call
```

The current call is normally one of:

```text
CIRCLE
TRIANGLE
CROSS
SQUARE
STAR
```

Ordinary cards update the call to their own shape.

WHOT changes the call to the shape selected by the player.

The numeric value of the most recently played card remains publicly observable through the play pile, but the active call determines the shape-matching condition.

---

# 11. Turn State

The simulator explicitly stores:

```text
current_player
turn_direction
turn_modifier
```

Possible turn modifiers include:

```text
NORMAL
EXTRA_TURN
SKIP_NEXT
```

The effect is resolved before determining the next actor.

## 11.1 Normal

The next player in the configured direction acts.

## 11.2 Hold On

If a player plays a valid 1:

```text
current_player → current_player
```

The same player receives another turn.

The effect does not allow the player to act twice inside the same action unless the ruleset explicitly defines such behavior.

Each turn remains a separate decision point.

## 11.3 Suspension

If a player plays an 8:

```text
current_player → next player
                     ↓
                   skipped
                     ↓
             following player
```

The suspended player does not receive a decision opportunity during the skipped turn.

A skip event must be logged.

---

# 12. Legal Action Generation

At every decision point the simulator generates:

```text
A_i^legal
```

for the current player.

The baseline legal action space contains:

```text
PLAY(card)
PLAY(WHOT, selected_shape)
DRAW
DECLARE_LAST
```

`DECLARE_LAST` is available only when declaration rules permit it.

The simulator must generate an action mask so an agent can distinguish legal from illegal actions.

---

# 13. Normal Legal Play

When no active draw penalty exists, an ordinary card is legal when:

```text
card.shape == current_call
```

OR

```text
card.value == top_card.value
```

OR

```text
card.type == WHOT
```

Therefore a player holding:

```text
Circle 7
Triangle 12
Star 3
WHOT
```

with:

```text
current_call = CIRCLE
top_card = Circle 4
```

may play:

```text
Circle 7
WHOT
```

The simulator must not consider strategic value when determining legality.

---

# 14. WHOT Action

Playing a WHOT card requires an additional parameter:

```text
selected_shape
```

The legal choices are exactly:

```text
CIRCLE
TRIANGLE
CROSS
SQUARE
STAR
```

The simulator must reject:

- invalid shape names;
- WHOT with no selected shape;
- multiple selected shapes;
- selected values;
- selecting another WHOT as the shape.

The selected shape becomes the active call.

---

# 15. Draw Behavior

The baseline rule is:

```text
DRAW = draw exactly one card
```

The player may not choose which card is drawn.

The next card in the market is removed and added to the player's hand.

The draw must be recorded as a private card-received event.

### Baseline turn result

After drawing one card:

```text
turn ends
```

The newly drawn card cannot immediately be played in the baseline ruleset.

This is deliberate.

It creates a clean action boundary:

```text
DRAW
    ↓
receive card
    ↓
turn ends
```

A future ruleset can enable:

```text
MAY_PLAY_DRAWN
MUST_PLAY_DRAWN_IF_LEGAL
DRAW_UNTIL_PLAYABLE
```

without modifying the simulator architecture.

---

# 16. Draw-Pile Exhaustion

When a draw is requested and the market is empty, the simulator invokes the configured market-exhaustion policy.

Baseline:

```text
PRESERVE_TOP_AND_RESHUFFLE_DISCARD
```

The simulator:

1. preserves the current top play-pile card;
2. takes all other discard-pile cards;
3. shuffles them;
4. creates a new market;
5. continues the requested draw.

The top card must never accidentally enter the newly shuffled market.

---

# 17. Completely Exhausted Market

A theoretically possible situation exists where:

```text
market = empty
play_pile contains only top_card
```

and therefore no card is available to recycle.

The simulator must not create cards from nowhere.

Instead it generates:

```text
DRAW_UNAVAILABLE
```

and applies the configured no-card policy.

Baseline:

```text
no card is drawn
turn ends
```

This event must be logged.

This case is unlikely in ordinary games but must be explicitly supported for correctness and adversarial testing.

---

# 18. Pick Two

A Pick Two activates a draw penalty:

```text
penalty_type = PICK_TWO
penalty_count = 2
```

When stacking is enabled, another Pick Two may be played by the next player.

The penalty then accumulates:

```text
2
→ 4
→ 6
→ ...
```

The next player may either:

```text
DEFEND with another Pick Two
```

or:

```text
DRAW the accumulated penalty
```

Under the baseline:

```text
PICK_TWO cannot be defended by ordinary matching cards.
```

The active penalty therefore temporarily overrides normal matching rules.

---

# 19. Pick Three

Pick Three operates analogously.

A Pick Three activates:

```text
penalty_type = PICK_THREE
penalty_count = 3
```

A following Pick Three may stack:

```text
3
→ 6
→ 9
→ ...
```

The player must either:

```text
play another Pick Three
```

or:

```text
draw the accumulated penalty
```

---

# 20. Stacking Modes

The simulator should support at least:

```text
NO_STACKING
SAME_EFFECT
ANY_PICK_CARD
```

### NO_STACKING

The first penalty must be resolved immediately.

### SAME_EFFECT

Pick Two may stack only with Pick Two.

Pick Three may stack only with Pick Three.

This is the WHOT-NG-v1 baseline.

### ANY_PICK_CARD

Any configured pick card may continue the accumulated penalty.

Example:

```text
2 → 5 → 2
```

could produce:

```text
2 + 3 + 2 = 7
```

This behavior must never be silently enabled.

---

# 21. WHOT During an Active Penalty

The baseline ruleset treats WHOT as a wild card but does not allow it to cancel an active draw penalty.

Therefore:

```text
active penalty = Pick Two
```

means the player must either:

```text
play a legal defending Pick Two
```

or:

```text
draw two
```

A WHOT is not considered a valid defence.

This is configurable through:

```text
whot_defends_penalty
```

Future experiments may compare:

```text
WHOT_DEFENDS = false
WHOT_DEFENDS = true
```

---

# 22. Resolving a Pick Penalty

When a player chooses DRAW against an active penalty:

1. calculate the total penalty;
2. draw that many cards;
3. clear the active penalty;
4. record all private card receipts;
5. end the player's turn.

If the market becomes empty during this process, the exhaustion policy is invoked as necessary.

Each drawn card is a separate internal card-transfer event.

---

# 23. General Market — Card 14

When a player legally plays a 14:

```text
GENERAL_MARKET
```

every other active player receives one card.

For four players:

```text
Player A plays 14

Player B → +1
Player C → +1
Player D → +1
```

The player who played the 14 does not draw.

The simulator must process recipients in a deterministic player order.

Baseline order:

```text
next player
next player after that
...
```

until every opponent has been processed.

Each received card remains private to its recipient.

The public log may state:

```text
GENERAL_MARKET_RESOLVED
Player B drew 1
Player C drew 1
Player D drew 1
```

but must not reveal the identities of those cards to other agents.

---

# 24. General Market with an Exhausted Market

If the market runs out while resolving General Market, the simulator invokes the normal exhaustion mechanism before the next required draw.

If no card can be produced because the entire recyclable market is exhausted, the affected recipient receives no card and the event is logged as:

```text
DRAW_UNAVAILABLE
```

The remaining recipients are still processed.

The simulator must never fail merely because the 14 effect occurs late in a long game.

---

# 25. Last-Card Declaration

The baseline environment requires a player to alert opponents when they have one card remaining.

The declaration is represented explicitly as:

```text
DECLARE_LAST
```

A declaration is valid when:

```text
hand_size == 1
```

and the declaration rule is enabled.

Once declared:

```text
last_card_declared[player] = true
```

The declaration remains associated with that player until their hand changes or the round terminates.

---

# 26. Undeclared Final-Card Attempt

Suppose a player has one card remaining but has not declared.

They play that card and would otherwise win.

The simulator must not immediately terminate the game.

Instead:

1. the card is processed normally;
2. the victory attempt is detected;
3. the simulator checks declaration state;
4. the player is found to have violated the declaration rule;
5. the configured invalid-win penalty is applied.

Baseline:

```text
INVALID_WIN → draw 1 card
```

Therefore:

```text
hand = 1
play final card
declaration missing
        ↓
draw 1
        ↓
hand ≠ 0
        ↓
game continues
```

The violation must be recorded as a distinct event:

```text
LAST_CARD_DECLARATION_VIOLATION
```

The simulator must not silently convert this into an ordinary draw.

---

# 27. Valid Victory

A player wins only when all terminal requirements are satisfied.

Baseline:

```text
hand_size == 0
AND
last-card declaration requirements satisfied
```

A valid winning action produces:

```text
ROUND_ENDED
GAME_OVER
```

The winner receives:

```text
reward = +1
```

Other players receive:

```text
reward = -1
```

for the baseline zero-sum terminal reward.

---

# 28. Special Card Used as Final Card

Special effects are resolved before final terminal verification.

Therefore a final card may still produce its associated effect before the game is declared over.

For example:

```text
Player A has one card: 14
Player A has correctly declared
Player A plays 14
        ↓
General Market resolves
        ↓
terminal condition checked
        ↓
Player A wins
```

Similarly, a final 1 or 8 may resolve its effect before termination.

No future turn is created after a valid terminal state.

---

# 29. Action Resolution Order

Every submitted action must follow a fixed resolution pipeline.

```text
1. Receive action
2. Validate action
3. Verify actor is current player
4. Verify action legality
5. Execute card movement / draw / declaration
6. Update public state
7. Apply card effect
8. Apply turn modifier
9. Resolve declaration requirements
10. Check terminal state
11. Determine next player
12. Validate invariants
13. Emit observation
14. Return transition result
```

This ordering must remain stable within a simulator version.

---

# 30. Illegal Actions

The simulator supports two modes.

## Training mode

Illegal actions are prevented by the action mask.

The agent should therefore normally never submit one.

## Evaluation/debug mode

The simulator accepts the attempted action as an input but rejects it.

It returns:

```text
illegal_action = true
```

and records:

```text
ILLEGAL_ACTION
```

The game state itself must remain unchanged unless the configured experimental protocol explicitly applies an illegal-action penalty.

Baseline policy:

```text
illegal action → no state change
```

This prevents implementation mistakes from corrupting the environment.

---

# 31. Agent–Simulator Boundary

This boundary is critical.

The simulator possesses:

```text
FULL_STATE
```

The agent possesses:

```text
PLAYER_OBSERVATION
```

A player observation contains only:

```text
own hand
public play pile
current call
current player
active penalties
public declarations
public history
ruleset
legal action mask
```

It must not contain:

```text
opponent hand contents
draw-pile order
hidden card locations
RNG state
future events
debug state
```

---

# 32. Debug State

A special researcher-only interface may expose:

```text
FULL_STATE
```

for:

- testing;
- debugging;
- replay;
- dataset generation;
- simulator verification.

However:

> Full state must never be passed into an agent policy during a hidden-information experiment.

This separation should be enforced architecturally rather than merely by programmer discipline.

---

# 33. Core Environment API

The reference simulator should expose a minimal standard interface.

## 33.1 Reset

```text
reset(seed=None, ruleset=None)
```

Returns the initial observation for each player.

---

## 33.2 Step

```text
step(action)
```

Executes the current player's action.

Returns conceptually:

```text
observation
reward
terminated
truncated
info
```

For multi-agent experiments, the environment must identify the next acting player.

---

## 33.3 Observe

```text
observe(player_id)
```

Returns exactly what that player is permitted to know.

---

## 33.4 Legal Actions

```text
legal_actions(player_id)
```

Returns the complete legal action set.

---

## 33.5 Action Mask

```text
action_mask(player_id)
```

Returns a machine-learning-compatible representation of legal/illegal actions.

---

## 33.6 Full State

```text
get_full_state()
```

Research/debug interface only.

---

## 33.7 Serialize

```text
serialize_state()
```

Produces a complete versioned representation of the current state.

---

## 33.8 Restore

```text
restore_state(serialized_state)
```

Restores the environment to exactly that state.

This enables deterministic replay and debugging.

---

# 34. Transition Record

Every call to `step()` should produce a transition record conceptually equivalent to:

```text
{
    episode_id,
    timestep,
    acting_player,
    observation_before,
    action,
    action_legal,
    event_list,
    observation_after,
    reward,
    terminated,
    truncated
}
```

For hidden-information experiments, private information must be stored separately from public information.

This distinction is necessary for generating supervised datasets without accidentally creating information leakage.

---

# 35. Event System

The simulator should maintain an event stream.

Core public events include:

```text
GAME_STARTED
CARD_PLAYED
WHOT_SHAPE_SELECTED
CARD_DRAWN_PUBLIC_COUNT
PENALTY_ACTIVATED
PENALTY_STACKED
PENALTY_RESOLVED
GENERAL_MARKET_ACTIVATED
TURN_STARTED
TURN_SKIPPED
HOLD_ON_ACTIVATED
LAST_CARD_DECLARED
LAST_CARD_DECLARATION_VIOLATION
ROUND_ENDED
GAME_OVER
```

Private events include:

```text
PRIVATE_CARD_RECEIVED
PRIVATE_CARD_REVEALED
PRIVATE_HAND_CHANGED
```

A public observer receives public events only.

A player's private event stream may include private information relevant to that player.

---

# 36. History

The simulator maintains the public action/event history:

```text
H_t = (e_0, e_1, ..., e_t)
```

This history forms the basis for later research involving:

- opponent modelling;
- hidden-hand prediction;
- strategy inference;
- belief-state construction.

The simulator must preserve event ordering exactly.

---

# 37. Randomness

All stochastic behavior must originate from a controlled RNG.

The master seed controls:

- deck shuffling;
- starter selection;
- initial WHOT shape selection;
- market reshuffling;
- any later stochastic rules.

Randomness must never come from uncontrolled global state.

For example, the simulator should not mix:

```text
seeded_rng
```

with arbitrary system randomness.

---

# 38. Reproducibility Requirement

The following must reproduce the same episode:

```text
same simulator version
same ruleset
same seed
same initial configuration
same sequence of actions
```

A replay mismatch constitutes a simulator defect unless the version explicitly declares nondeterministic behavior.

The simulator version must therefore be part of every published experiment.

---

# 39. State Serialization

A complete state representation must contain enough information to continue the game exactly.

At minimum:

```text
ruleset
player count
all player hands
market order
play pile order
current call
current player
turn direction
active penalty
turn modifier
declaration state
timestep
episode identifier
RNG state
simulator version
```

The order of the market is especially important.

Knowing merely which cards remain is insufficient to resume the exact game.

---

# 40. State Invariants

After every action, the simulator should validate core invariants in debug/test mode.

## 40.1 Card conservation

```text
sum(hand sizes)
+ market size
+ play pile size
= 54
```

at every valid state.

## 40.2 Card uniqueness

Every physical card appears in exactly one location.

## 40.3 Hand validity

No player has a negative hand size.

## 40.4 Play validity

The play pile is never empty once the game has initialized.

## 40.5 WHOT validity

If WHOT establishes or changes the active shape, the selected shape must be one of the five ordinary shapes.

## 40.6 Turn validity

Only one player is current at a time.

## 40.7 Terminal validity

No normal gameplay action may occur after terminal state.

## 40.8 Penalty validity

An active penalty must correspond to a supported penalty type and have a positive count.

Failure of any invariant should generate a diagnostic error containing:

```text
episode
timestep
ruleset
action
event
state summary
failed invariant
```

---

# 41. Edge-Case Requirements

The simulator must explicitly test at least the following cases.

### Case A — WHOT as initial card

The environment must establish a valid initial call.

### Case B — 1 as initial card

Its effect must not activate under baseline `NO_EFFECT_START`.

### Case C — 8 as initial card

Its suspension effect must not activate during setup.

### Case D — 14 as initial card

General Market must not activate during setup.

### Case E — Player wins with declared final card

Immediate valid termination.

### Case F — Player attempts undeclared final card

Final card is processed, declaration violation occurs, one penalty card is drawn, game continues.

### Case G — Pick Two stacking

```text
2 → 2 → 2
```

must produce penalty 6 under baseline rules.

### Case H — Pick Three stacking

```text
5 → 5 → 5
```

must produce penalty 9.

### Case I — Wrong defence

A player facing Pick Two attempts to play an ordinary matching card.

Action must be rejected.

### Case J — Market exhaustion

Discard pile is successfully recycled while preserving the top card.

### Case K — Complete exhaustion

No recyclable card exists.

The simulator must handle this without generating nonexistent cards.

### Case L — General Market near exhaustion

The simulator must correctly recycle the market during multi-player drawing.

### Case M — WHOT during penalty

Rejected under baseline rules.

### Case N — Hold On

The same player receives the next turn.

### Case O — Suspension

The next player is skipped.

### Case P — Terminal special card

Effect resolution and terminal resolution occur in the defined order.

### Case Q — Restore and replay

Serializing a state and restoring it must produce identical future behavior.

---

# 42. Testing Strategy

The simulator should contain multiple testing layers.

## 42.1 Unit Tests

Test individual components:

```text
deck construction
card properties
legal action generation
effect resolution
penalty stacking
declaration logic
turn advancement
market reshuffling
serialization
```

## 42.2 Integration Tests

Run complete games using deterministic scripted actions.

Examples:

```text
known seed
known deal
known actions
expected winner
expected event sequence
```

## 42.3 Property-Based Tests

Generate many random valid games and verify invariants.

Especially:

```text
card conservation
card uniqueness
legal action correctness
no invalid state transitions
deterministic replay
```

## 42.4 Hidden-Information Tests

These are especially important for ML.

Construct states in which hidden cards differ while public observations remain identical.

Verify that:

```text
agent observation A == agent observation B
```

even though:

```text
full state A != full state B
```

whenever the difference lies only in information unavailable to the player.

This directly tests against accidental information leakage.

---

# 43. Information-Leakage Audit

Before an environment can be used for hidden-information research, it must undergo an explicit information-leakage audit.

The audit must verify that no agent-visible representation contains hidden information through:

- card identifiers;
- ordering artifacts;
- array positions;
- numerical encodings;
- hashes;
- RNG state;
- memory addresses;
- debugging fields;
- future card information;
- opponent hand sizes when those are not legally observable;
- hidden card metadata.

A particularly dangerous implementation error would be:

```text
opponent hand hidden visually
but encoded numerically in the observation tensor.
```

Therefore observation generation must be tested independently from full-state storage.

---

# 44. Observation Contract

The simulator should conceptually maintain two different objects:

```text
WORLD STATE
```

and:

```text
PLAYER OBSERVATION
```

The observation should be generated by a dedicated transformation:

```text
O_i = Observe(S, i)
```

rather than by giving the agent direct access to the internal state and expecting it to ignore forbidden fields.

This makes information boundaries enforceable.

---

# 45. Strategic Neutrality

The environment must remain strategically neutral.

For example, when multiple cards are legal:

```text
Circle 3
Circle 8
WHOT
```

the simulator must not rank them.

It merely returns:

```text
legal = {Circle 3, Circle 8, WHOT}
```

The policy decides.

This ensures measured performance belongs to the agent, not the environment.

---

# 46. Simulator Modes

The reference environment should support at least three modes.

## 46.1 Training Mode

Optimized for repeated interaction.

Features:

- action masks;
- observations;
- rewards;
- fast stepping;
- minimal rendering.

## 46.2 Evaluation Mode

Designed for rigorous experiments.

Features:

- complete event logs;
- deterministic seeds;
- episode metrics;
- replay information;
- illegal-action tracking.

## 46.3 Debug Mode

Designed for development.

Features:

- full state;
- invariant checks;
- verbose event logs;
- state serialization;
- replay;
- assertions.

Debug mode may expose information that must never be available to learning agents.

---

# 47. Episode Limits

The simulator must support:

```text
maximum_turns
```

to prevent pathological episodes from running indefinitely.

If the limit is reached:

```text
truncated = true
```

rather than:

```text
terminated = true
```

unless the ruleset explicitly defines another interpretation.

A truncated episode must be distinguished from a genuine victory.

This distinction is important for reinforcement-learning evaluation.

---

# 48. Rewards

The simulator should maintain a clean separation between:

```text
environment mechanics
```

and:

```text
research reward design
```

Baseline terminal reward:

```text
winner = +1
all losers = -1
```

Intermediate reward:

```text
0
```

Alternative metrics such as:

```text
cards remaining
cards discarded
penalties inflicted
```

must not automatically become reward signals.

Researchers may define dense rewards experimentally, but those rewards belong to the experimental configuration rather than the core game mechanics.

---

# 49. Metrics Generated by the Simulator

At minimum, every episode should report:

```text
winner
finishing positions
episode length
turn count
final hand sizes
win/loss outcome
illegal action count
draw count
Pick Two activations
Pick Three activations
WHOT plays
General Market activations
Hold On activations
Suspensions
last-card declaration violations
market reshuffles
```

These metrics provide basic diagnostic information for Paper 1 and Paper 2.

Later papers may extend them with:

```text
belief accuracy
calibration
opponent-model classification
strategy diversity
adaptation speed
transfer performance
```

---

# 50. Replay

A replay system should reconstruct an episode from:

```text
simulator version
ruleset
seed
action sequence
```

The replay should reproduce:

```text
card movements
public events
private events
turn order
penalties
declarations
terminal state
```

This is necessary when:

- debugging an unusual agent behavior;
- verifying a published result;
- investigating simulator bugs;
- generating training data;
- examining strategic sequences.

---

# 51. Reference Pseudocode

The core game loop should behave approximately as follows:

```text
reset()

while not terminal:

    player = current_player

    observation = observe(player)

    legal_actions = legal_actions(player)

    action = agent(observation, legal_actions)

    validate(action)

    events = execute(action)

    resolve_effects(events)

    resolve_declaration_state()

    if valid_terminal_state():
        terminate()
        break

    advance_turn()

    validate_invariants()

    emit_transition()
```

The exact implementation language and architecture are left open.

The behavior is the contract.

---

# 52. Separation of Responsibilities

The simulator should conceptually separate:

```text
Deck Manager
Rules Engine
State Manager
Action Validator
Turn Manager
Effect Resolver
Observation Generator
Event Logger
RNG Manager
Serializer
Metrics Collector
```

These components may be implemented differently in code, but their responsibilities must remain logically separable.

This prevents changes to one system from silently altering another.

---

# 53. Rules Engine

The rules engine should answer questions such as:

```text
Is this card playable?
What actions are legal?
Does this card activate an effect?
Can this penalty be defended?
Does this action satisfy the victory condition?
Is declaration required?
What happens after this effect?
```

It should not answer:

```text
Which card is strategically best?
What does the opponent probably have?
What should the AI do?
```

Those belong outside the rules engine.

---

# 54. Simulator Correctness Hierarchy

When resolving an action, the simulator should prioritize correctness in this order:

```text
1. State validity
2. Rules legality
3. Card movement
4. Effect resolution
5. Declaration resolution
6. Terminal resolution
7. Turn transition
8. Observation generation
9. Logging / metrics
```

No downstream component should be allowed to repair an invalid upstream state.

---

# 55. Versioning

Simulator behavior must be versioned.

For example:

```text
WHOT-NG-v1
WHOT-NG-v1.1
WHOT-NG-v2
```

A change that can alter gameplay results must produce a new environment version or explicitly documented ruleset version.

Examples:

```text
changing Pick Two stacking
changing draw behavior
changing first-card behavior
changing last-card penalties
```

must not be treated as harmless implementation details.

This is essential for reproducible ML research.

---

# 56. Research Dataset Generation

Once the simulator is validated, it should be able to generate datasets containing:

```text
state
observation
action
outcome
public history
hidden ground truth
```

The intended use differs by paper.

### Paper 1

Environment validation and benchmark trajectories.

### Paper 2

Gameplay trajectories for policy learning and evaluation.

### Paper 3

Pairs such as:

```text
observed history
+
true opponent hand
```

for hidden-hand prediction.

### Paper 4

Sequences such as:

```text
observed history
+
opponent behavior
+
latent strategy label / inferred strategy representation
```

for opponent modelling.

The hidden ground truth must be preserved for researchers while remaining unavailable to the agent during interaction.

---

# 57. Important Dataset Warning

Datasets generated by the simulator must distinguish:

```text
information available at time t
```

from:

```text
information discovered after time t
```

For example, when generating a hidden-hand prediction example at timestep `t`, the target may be:

```text
opponent_hand_t
```

but the input must not accidentally include:

```text
opponent_hand_{t+1}
```

or later events.

Temporal leakage would produce artificially strong models.

---

# 58. Acceptance Criteria for P0-D4

The simulator specification is considered implementable when an implementation can answer all of the following without ambiguity:

### Game setup

- How many cards exist?
- How are they dealt?
- Who starts?
- How is the first play card established?

### Normal turns

- What makes a card legal?
- What happens when no legal card exists?
- What exactly does drawing do?

### Special effects

- How do 1, 2, 5, 8, 14, and 20 behave?
- How are stacked penalties represented?
- Can WHOT defend a penalty?

### Victory

- When must the player declare?
- What happens after a failed declaration?
- When exactly does terminal state occur?

### Randomness

- What events use randomness?
- How are seeds controlled?
- Can the exact game be replayed?

### Hidden information

- What does the simulator know?
- What does each player know?
- What must never enter an observation?

### Correctness

- How is card conservation checked?
- How are illegal actions handled?
- How are exhausted markets handled?

### Research

- Can complete trajectories be logged?
- Can states be serialized?
- Can experiments reproduce the same game?

If any implementation cannot answer one of these questions, the simulator is not yet sufficiently specified for serious experimental use.

---

# 59. Remaining Configurable Questions

WHOT-NG-v1 deliberately establishes a baseline rather than claiming that every Nigerian WHOT player uses identical rules.

Potential future ruleset dimensions include:

```text
draw-until-playable vs draw-one
immediate play after drawing
alternative Pick Two / Pick Three stacking
cross-type penalty stacking
WHOT as penalty defence
different last-card penalties
different declaration timing
special-card first-card resolution
different scoring systems
different starting hand sizes
different player counts
different turn directions
```

These should be treated as explicit experimental variables.

They must never be introduced accidentally through implementation.

---

# 60. Relationship to Phase 0 Documents

The four foundational documents now form a direct chain:

```text
P0-D1
Formal Rules Specification
        ↓
defines what WHOT-NG-v1 means
        ↓
P0-D2
Mathematical Environment Specification
        ↓
defines the game formally as a decision process
        ↓
P0-D3
Card & Rule Ontology
        ↓
defines the entities and relationships
        ↓
P0-D4
Simulator Specification
        ↓
defines how the formal game is executed
```

P0-D5 will then define:

```text
how experiments using this simulator must be run,
recorded,
reported,
and reproduced.
```

---

# 61. Core Principle

The final architectural principle of the simulator is:

> **The simulator knows everything. The player knows only what a real player could know. The rules engine knows exactly what is legal. The researcher can reconstruct exactly what happened.**

That separation is the foundation on which WHOT-ML's hidden-information, self-play, prediction, and opponent-modelling experiments will be built.
