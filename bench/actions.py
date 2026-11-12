"""Legal action generation with stable IDs and hand-index snapshots."""
from __future__ import annotations
from itertools import combinations
from dataclasses import dataclass
from .model import Card


@dataclass(frozen=True, slots=True)
class CardAction:
    kind: str
    card_ids: tuple[str, ...]
    hand_indices_snapshot: tuple[int, ...]

    @property
    def code(self) -> str:
        return f"{self.kind}:" + ",".join(self.card_ids)

    def to_dict(self) -> dict:
        return {
            "kind": self.kind,
            "card_ids": list(self.card_ids),
            "hand_indices_snapshot": list(self.hand_indices_snapshot),
            "code": self.code,
        }


def _legal_card_sets(hand: list[Card]) -> list[tuple[int, ...]]:
    result: list[tuple[int, ...]] = []
    seen: set[tuple[str, ...]] = set()
    for size in range(1, min(5, len(hand)) + 1):
        for idxs in combinations(range(len(hand)), size):
            ids = tuple(sorted(hand[i].card_id for i in idxs))
            # Standard deck IDs are unique, so this never merges distinct standard-deck cards.
            # It only canonicalizes accidental duplicate physical cards in non-v1 test fixtures.
            if ids not in seen:
                seen.add(ids)
                result.append(idxs)
    return result


def legal_plays(hand: list[Card]) -> list[tuple[int, ...]]:
    """All 1..5-card combinations, in deterministic order; max is C(8,1..5)=218."""
    return _legal_card_sets(hand)


def legal_discards(hand: list[Card], discards_left: int) -> list[tuple[int, ...]]:
    """All legal 1..5-card discards, or [] when no discard remains."""
    if discards_left <= 0:
        return []
    return _legal_card_sets(hand)


def encode_card_action(kind: str, hand: list[Card], indices: tuple[int, ...]) -> CardAction:
    if kind not in ("play", "discard"):
        raise ValueError("kind must be 'play' or 'discard'")
    if not indices or len(indices) > 5 or len(set(indices)) != len(indices):
        raise ValueError("action must select 1..5 distinct indices")
    if any(i < 0 or i >= len(hand) for i in indices):
        raise IndexError("hand index out of range")
    # Preserve display/index order in the snapshot; stable IDs make the action replayable.
    return CardAction(kind, tuple(hand[i].card_id for i in indices), tuple(indices))
