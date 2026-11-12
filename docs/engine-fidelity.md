# Engine fidelity — manual single-hand score comparisons

**Status: NOT VERIFIED.** No real Balatro session was accessible from this build environment. The 20 manual captures and five third-party calculator checks below are intentionally left pending. The project must not claim `20/20` until each row contains observed game input/output and an independently computed engine score.

## Known blockers to resolve before calling this vanilla-game fidelity

1. The custom formula omits vanilla poker-hand base Chips; vanilla level-1 Pair is 10 Chips × 2 Mult and Flush is 35 Chips × 4 Mult. See `docs/data-sources.md`.
2. The custom hand multipliers (Straight Flush 12, Four of a Kind 10, etc.) differ from vanilla level-1 multipliers (e.g. Straight Flush 8, Four of a Kind 7).
3. This subset counts the rank chips of every played card; vanilla game scoring can exclude unscored cards from a played 5-card selection.
4. Joker fixtures are synthetic, not mapped to named vanilla Jokers.
5. The supplied row `7♥7♦ -> 68` conflicts with the specified subset formula (28) and with vanilla Pair score (48).
6. The custom `before` phase label should not be mistaken for SMODS `context.before` scoring behavior.

Until these are reconciled, engine unit tests validate **the internal custom subset**, not 100% vanilla score fidelity.

## A. Twenty manual game scenarios

Record a stable game version/build and capture the exact cards constituting the played hand and any Joker effects. Do not copy a score from a different run, game version, or Joker condition.

| # | Sampling stratum | Hand (rank+suit) | Actual Jokers / effect state | Played cards | Game score | Engine score | Match | Evidence/version/notes |
|---:|---|---|---|---|---:|---:|---|---|
| 1 | no Joker | PENDING | — | PENDING | — | — | — | PENDING |
| 2 | no Joker | PENDING | — | PENDING | — | — | — | PENDING |
| 3 | no Joker | PENDING | — | PENDING | — | — | — | PENDING |
| 4 | no Joker | PENDING | — | PENDING | — | — | — | PENDING |
| 5 | no Joker | PENDING | — | PENDING | — | — | — | PENDING |
| 6 | no Joker | PENDING | — | PENDING | — | — | — | PENDING |
| 7 | single Joker | PENDING | PENDING | PENDING | — | — | — | PENDING |
| 8 | single Joker | PENDING | PENDING | PENDING | — | — | — | PENDING |
| 9 | single Joker | PENDING | PENDING | PENDING | — | — | — | PENDING |
| 10 | single Joker | PENDING | PENDING | PENDING | — | — | — | PENDING |
| 11 | single Joker | PENDING | PENDING | PENDING | — | — | — | PENDING |
| 12 | single Joker | PENDING | PENDING | PENDING | — | — | — | PENDING |
| 13 | two Jokers | PENDING | PENDING | PENDING | — | — | — | PENDING |
| 14 | two Jokers | PENDING | PENDING | PENDING | — | — | — | PENDING |
| 15 | two Jokers | PENDING | PENDING | PENDING | — | — | — | PENDING |
| 16 | two Jokers | PENDING | PENDING | PENDING | — | — | — | PENDING |
| 17 | two Jokers | PENDING | PENDING | PENDING | — | — | — | PENDING |
| 18 | includes xMult | PENDING | PENDING | PENDING | — | — | — | PENDING |
| 19 | includes xMult | PENDING | PENDING | PENDING | — | — | — | PENDING |
| 20 | includes xMult | PENDING | PENDING | PENDING | — | — | — | PENDING |

The strata intentionally overlap for the three `xMult` rows if applicable; specify the sampling assignment in the notes column.

## B. Five third-party calculator checks

The upstream EFHIII README cautions that a few Jokers may be inaccurate. Note the exact calculator URL/inputs and keep mismatches rather than forcing agreement.

| # | Category | Input / calculator URL | Calculator result | Engine result | Match | Notes |
|---:|---|---|---:|---:|---|---|
| C1 | no Joker | PENDING | — | — | — | PENDING |
| C2 | no Joker | PENDING | — | — | — | PENDING |
| C3 | single +Mult | PENDING | — | — | — | PENDING |
| C4 | single xMult | PENDING | — | — | — | PENDING |
| C5 | mixed / boundary case | PENDING | — | — | — | PENDING |

Calculator link: https://github.com/EFHIII/balatro-calculator

## Required mismatch triage

1. Poker-hand classification and precedence.
2. Ace low/high straight handling.
3. Whether the exact Joker is additive Mult or xMult, and whether its condition actually fired.
4. Rounding/floor timing.
5. Cardarea × phase/context semantics.
6. Joker slot order.
7. Vanilla hand base Chips/Mult and scoring-card selection — this check must not be skipped for v2.1.

## Sign-off template

- Manual samples completed: `__/20`
- Manual score matches: `__/20`
- Calculator checks completed: `__/5`
- Calculator matches: `__/5`
- Game version and build: `PENDING`
- Remaining mismatches and root causes: `PENDING`
- Fidelity status: `NOT_VERIFIED` until evidence is complete and all relevant mismatches are resolved.
