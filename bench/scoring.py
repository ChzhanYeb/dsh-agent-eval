"""Pure hand classification and scoring for the explicitly simplified v1 ruleset.

This formula is intentionally the user's custom subset formula: chips are the sum of the
played cards' rank chips plus add_chips effects; it omits vanilla Balatro hand-base Chips.
That means its output is not directly comparable with vanilla scores until the ruleset is
revised to include real poker-hand base chips and real Joker semantics.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from collections import Counter
from math import floor
from typing import Sequence
from .model import Card, Joker


class HandType(str, Enum):
    STRAIGHT_FLUSH = "straight_flush"
    FOUR_KIND = "four_kind"
    FULL_HOUSE = "full_house"
    FLUSH = "flush"
    STRAIGHT = "straight"
    THREE_KIND = "three_kind"
    TWO_PAIR = "two_pair"
    PAIR = "pair"
    HIGH_CARD = "high_card"


# User-defined simplified multipliers; these are not vanilla Balatro level-1 multipliers.
HAND_MULT: dict[HandType, int] = {
    HandType.STRAIGHT_FLUSH: 12,
    HandType.FOUR_KIND: 10,
    HandType.FULL_HOUSE: 8,
    HandType.FLUSH: 6,
    HandType.STRAIGHT: 5,
    HandType.THREE_KIND: 4,
    HandType.TWO_PAIR: 3,
    HandType.PAIR: 2,
    HandType.HIGH_CARD: 1,
}

PHASE_BY_KIND = {
    "add_chips": ("G.jokers", "before"),
    "add_mult": ("G.jokers", "before"),
    "mul_mult": ("G.jokers", "individual"),
}


def _apply_add_chips(chips: int, mult: Fraction, value: int) -> tuple[int, Fraction]:
    return chips + value, mult


def _apply_add_mult(chips: int, mult: Fraction, value: int) -> tuple[int, Fraction]:
    return chips, mult + value


def _apply_mul_mult(chips: int, mult: Fraction, value: int) -> tuple[int, Fraction]:
    return chips, mult * Fraction(value, 100)


# Dispatcher key includes card area AND phase; adding an effect requires an explicit route.
EFFECT_DISPATCH = {
    ("G.jokers", "before", "add_chips"): _apply_add_chips,
    ("G.jokers", "before", "add_mult"): _apply_add_mult,
    ("G.jokers", "individual", "mul_mult"): _apply_mul_mult,
}


@dataclass(frozen=True, slots=True)
class ScoreResult:
    hand_type: HandType
    chips: int
    mult: Fraction
    final_score: int
    trace: tuple[dict, ...]

    def to_dict(self) -> dict:
        return {
            "hand_type": self.hand_type.value,
            "chips": self.chips,
            "mult": f"{self.mult.numerator}/{self.mult.denominator}",
            "mult_float": float(self.mult),
            "final_score": self.final_score,
            "trace": list(self.trace),
        }


def _is_straight(ranks: set[int]) -> bool:
    if len(ranks) != 5:
        return False
    if ranks == {1, 2, 3, 4, 5}:  # wheel: A-2-3-4-5
        return True
    if ranks == {1, 10, 11, 12, 13}:  # Broadway: 10-J-Q-K-A
        return True
    ordered = sorted(ranks)
    return ordered[-1] - ordered[0] == 4 and all(ordered[i] + 1 == ordered[i + 1] for i in range(4))


def classify_hand(cards: Sequence[Card]) -> HandType:
    """Classify 1..5 selected cards using the documented high-to-low precedence."""
    if not 1 <= len(cards) <= 5:
        raise ValueError("a played hand must contain 1..5 cards")
    rank_counts = Counter(c.rank for c in cards)
    counts = sorted(rank_counts.values(), reverse=True)
    is_flush = len(cards) == 5 and len({c.suit for c in cards}) == 1
    is_straight = len(cards) == 5 and _is_straight(set(rank_counts))

    # The order is deliberate: SF must precede flush; four-kind precedes full-house.
    if is_straight and is_flush:
        return HandType.STRAIGHT_FLUSH
    if counts[0] == 4:
        return HandType.FOUR_KIND
    if len(cards) == 5 and counts == [3, 2]:
        return HandType.FULL_HOUSE
    if is_flush:
        return HandType.FLUSH
    if is_straight:
        return HandType.STRAIGHT
    if counts[0] == 3:
        return HandType.THREE_KIND
    if counts.count(2) >= 2:
        return HandType.TWO_PAIR
    if counts[0] == 2:
        return HandType.PAIR
    return HandType.HIGH_CARD


def score_hand(cards: Sequence[Card], jokers: Sequence[Joker] = ()) -> ScoreResult:
    """Score one hand. Joker effects are applied in stable slot order, using exact fractions.

    The phase/area tuple is preserved in trace metadata. To satisfy the subset's explicit
    slot-order rule, effects are applied in slot order (not globally batched by phase). This
    is a custom deterministic dispatch contract; it is not a substitute for vanilla's full
    SMODS event pipeline.
    """
    if len({c.card_id for c in cards}) != len(cards):
        raise ValueError("played hand contains duplicate card ids")
    hand_type = classify_hand(cards)
    chips = sum(card.chips for card in cards)
    mult = Fraction(HAND_MULT[hand_type], 1)
    trace: list[dict] = [{"cardarea": "G.play", "phase": "individual", "effect": "rank_chips", "delta": chips}]

    for slot, joker in enumerate(jokers):
        area, phase = PHASE_BY_KIND[joker.kind]
        before_chips, before_mult = chips, mult
        dispatcher_key = (area, phase, joker.kind)
        try:
            effect_handler = EFFECT_DISPATCH[dispatcher_key]
        except KeyError as exc:
            raise ValueError(f"no effect dispatcher registered for {dispatcher_key}") from exc
        chips, mult = effect_handler(chips, mult, joker.value)
        trace.append({
            "slot": slot,
            "joker_id": joker.jid,
            "cardarea": area,
            "phase": phase,
            "kind": joker.kind,
            "value": joker.value,
            "chips_before": before_chips,
            "chips_after": chips,
            "mult_before": f"{before_mult.numerator}/{before_mult.denominator}",
            "mult_after": f"{mult.numerator}/{mult.denominator}",
        })

    final_score = floor(Fraction(chips, 1) * mult)
    trace.append({"phase": "final_scoring", "expression": "floor(chips * mult)", "final_score": final_score})
    return ScoreResult(hand_type, chips, mult, final_score, tuple(trace))
