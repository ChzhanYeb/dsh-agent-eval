"""Canonical fixture Joker catalog for the custom subset.

IMPORTANT: These are synthetic deterministic effect fixtures, not named vanilla Jokers.
Replace the value catalog only after mapping each selected real-game Joker to an observed
unconditional effect. Do not use these fixtures to claim vanilla-game score fidelity.
"""
from .model import Joker

# Values are deliberately explicit and versioned. mul_mult values are hundredths.
JOKER_CATALOG: tuple[Joker, ...] = (
    Joker("jc_flat_chips_10", "add_chips", 10, "+10 Chips fixture"),
    Joker("jc_flat_chips_20", "add_chips", 20, "+20 Chips fixture"),
    Joker("jc_flat_chips_30", "add_chips", 30, "+30 Chips fixture"),
    Joker("jm_add_mult_2", "add_mult", 2, "+2 Mult fixture"),
    Joker("jm_add_mult_4", "add_mult", 4, "+4 Mult fixture"),
    Joker("jm_add_mult_6", "add_mult", 6, "+6 Mult fixture"),
    Joker("jx_mul_mult_150", "mul_mult", 150, "x1.5 Mult fixture"),
    Joker("jx_mul_mult_200", "mul_mult", 200, "x2 Mult fixture"),
)

CATALOG_BY_ID = {j.jid: j for j in JOKER_CATALOG}
