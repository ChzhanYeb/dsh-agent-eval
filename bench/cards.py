"""Standard deck construction and card helpers."""
from __future__ import annotations
from itertools import combinations
from .model import Card


def standard_deck() -> list[Card]:
    """Return the canonical 52 physical cards, unique by (suit, rank)."""
    return [Card(suit=suit, rank=rank) for suit in range(4) for rank in range(1, 14)]


def cards_by_ids(cards: list[Card], card_ids: list[str] | tuple[str, ...]) -> list[Card]:
    wanted = set(card_ids)
    by_id = {c.card_id: c for c in cards}
    missing = wanted - by_id.keys()
    if missing:
        raise ValueError(f"unknown card ids: {sorted(missing)}")
    if len(wanted) != len(card_ids):
        raise ValueError("action contains duplicate stable card ids")
    return [by_id[cid] for cid in card_ids]


def combo_ids(cards: tuple[Card, ...] | list[Card]) -> tuple[str, ...]:
    return tuple(sorted(c.card_id for c in cards))
