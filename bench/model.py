"""Typed domain model for the BalatroBench v1 custom ruleset.

This is a small, deterministic benchmark ruleset, not a claim of complete vanilla-game emulation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

SUIT_NAMES = ("spades", "hearts", "diamonds", "clubs")
SUIT_CODES = ("s", "h", "d", "c")
RANK_NAMES = {1: "A", 11: "J", 12: "Q", 13: "K"}
Phase = Literal["play", "shop", "done"]
JokerKind = Literal["add_chips", "add_mult", "mul_mult"]


@dataclass(frozen=True, slots=True, order=True)
class Card:
    suit: int  # 0 spades, 1 hearts, 2 diamonds, 3 clubs
    rank: int  # 1 (Ace) .. 13 (King)

    def __post_init__(self) -> None:
        if self.suit not in range(4):
            raise ValueError(f"suit must be 0..3, got {self.suit}")
        if self.rank not in range(1, 14):
            raise ValueError(f"rank must be 1..13, got {self.rank}")

    @property
    def card_id(self) -> str:
        """Stable episode-wide identifier; unique for a standard 52-card deck."""
        return f"c{self.rank}{SUIT_CODES[self.suit]}"

    @property
    def label(self) -> str:
        rank = RANK_NAMES.get(self.rank, str(self.rank))
        return f"{rank}{SUIT_CODES[self.suit]}"

    @property
    def chips(self) -> int:
        if self.rank == 1:
            return 11
        if self.rank >= 11:
            return 10
        return self.rank


@dataclass(frozen=True, slots=True)
class Joker:
    jid: str
    kind: JokerKind
    value: int  # chips, additive mult, or x-mult in hundredths (150 == x1.5)
    name: str = ""

    def __post_init__(self) -> None:
        if self.kind not in ("add_chips", "add_mult", "mul_mult"):
            raise ValueError(f"unsupported joker kind: {self.kind}")
        if self.kind == "mul_mult" and self.value <= 0:
            raise ValueError("mul_mult value must be positive hundredths, e.g. 150 for x1.5")
        if self.kind != "mul_mult" and self.value < 0:
            raise ValueError("this v1 subset only supports nonnegative additive effects")


@dataclass
class GameState:
    blind_idx: int
    target: int
    total_score: int
    hand: list[Card]
    deck: list[Card]
    jokers: list[Joker]
    hands_left: int
    discards_left: int
    phase: Phase
    rng_state: str  # JSON encoding of the entire random.Random.getstate(), not just seed
    seed: int
    discard_pile: list[Card] = field(default_factory=list)
    shop_options: list[Joker] = field(default_factory=list)
    outcome: Literal["win", "loss"] | None = None
    steps: int = 0

    def __post_init__(self) -> None:
        if self.blind_idx not in range(3):
            raise ValueError("blind_idx must be 0..2")
        if self.target <= 0:
            raise ValueError("target must be positive")
        if len(self.jokers) > 3:
            raise ValueError("at most 3 jokers are allowed")
        if self.hands_left < 0 or self.discards_left < 0:
            raise ValueError("hands_left and discards_left cannot be negative")


def card_to_dict(card: Card) -> dict[str, int | str]:
    return {"id": card.card_id, "suit": card.suit, "rank": card.rank}


def joker_to_dict(joker: Joker) -> dict[str, int | str]:
    return {"jid": joker.jid, "kind": joker.kind, "value": joker.value, "name": joker.name}


def state_summary(state: GameState) -> dict:
    return {
        "blind_idx": state.blind_idx,
        "target": state.target,
        "total_score": state.total_score,
        "hand": [card_to_dict(c) for c in state.hand],
        "deck_count": len(state.deck),
        "discard_pile_count": len(state.discard_pile),
        "jokers": [joker_to_dict(j) for j in state.jokers],
        "hands_left": state.hands_left,
        "discards_left": state.discards_left,
        "phase": state.phase,
        "seed": state.seed,
        "rng_state": state.rng_state,
        "shop_options": [joker_to_dict(j) for j in state.shop_options],
        "outcome": state.outcome,
        "steps": state.steps,
    }
