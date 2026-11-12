# Joker semantics ledger — W2 v2.1

## Scope warning

The v2.1 specification defines eight *generic deterministic effects* but does not name eight vanilla Jokers or provide their individual values. To keep the engine runnable without inventing a false mapping to vanilla cards, this implementation uses eight **synthetic fixtures** from `bench/jokers.py`. They are not real-game Joker identities and cannot support a vanilla Joker fidelity claim. Replace this catalog only after the intended effects and numeric values are confirmed from the source game/version.

## Effect cards

| ID | Kind | Value | Area label | Phase label | Target | Slot-order sensitive? | Evidence/status |
|---|---|---:|---|---|---|---|---|
| `jc_flat_chips_10` | add_chips | +10 Chips | `G.jokers` | `before` | chips accumulator | No vs other add-chips effects | Synthetic fixture; not a vanilla Joker |
| `jc_flat_chips_20` | add_chips | +20 Chips | `G.jokers` | `before` | chips accumulator | No vs other add-chips effects | Synthetic fixture; not a vanilla Joker |
| `jc_flat_chips_30` | add_chips | +30 Chips | `G.jokers` | `before` | chips accumulator | No vs other add-chips effects | Synthetic fixture; not a vanilla Joker |
| `jm_add_mult_2` | add_mult | +2 Mult | `G.jokers` | `before` | current Mult | Yes, relative to xMult | Synthetic fixture; not a vanilla Joker |
| `jm_add_mult_4` | add_mult | +4 Mult | `G.jokers` | `before` | current Mult | Yes, relative to xMult | Synthetic fixture; not a vanilla Joker |
| `jm_add_mult_6` | add_mult | +6 Mult | `G.jokers` | `before` | current Mult | Yes, relative to xMult | Synthetic fixture; not a vanilla Joker |
| `jx_mul_mult_150` | mul_mult | x1.5 | `G.jokers` | `individual` | current Mult | Yes, relative to +Mult | Synthetic fixture; not a vanilla Joker |
| `jx_mul_mult_200` | mul_mult | x2.0 | `G.jokers` | `individual` | current Mult | Yes, relative to +Mult | Synthetic fixture; not a vanilla Joker |

## Dispatch contract currently implemented

- Playing-card rank chips are emitted as `G.play × individual` metadata.
- Each Joker is visited in stable left-to-right slot order.
- `add_chips` and `add_mult` use the custom phase label `before`; `mul_mult` uses the custom phase label `individual`.
- The implementation applies effects in **slot order** so `+Mult` and `xMult` order can change the result. The area/phase labels are recorded in the trace; they are not yet an emulation of the full SMODS scheduler.
- Exact arithmetic uses `fractions.Fraction`; only final score is floored.

## Source alignment caveat

SMODS documentation distinguishes contexts such as `before`, `initial_scoring_step`, `main_scoring`, `individual`, and `repetition`. The documentation says chip/mult returns from `context.before` are not added to score, while `initial_scoring_step` and `main_scoring` have specific scoring roles. Therefore, treating `before` as a generic scoring-modifier phase is **not proven equivalent** to vanilla behavior. This implementation labels its contract explicitly rather than claiming a one-to-one mapping.

References:
- https://docs.smods.dev/API%20Documentation/Calculate-Functions/
- https://github.com/DivvyCr/Balatro-Simulation
