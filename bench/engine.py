"""State initialization and transitions for the custom three-blind ruleset."""
from __future__ import annotations
import copy
import random
from pathlib import Path
from typing import Sequence
from .actions import encode_card_action
from .cards import standard_deck, cards_by_ids
from .jokers import JOKER_CATALOG
from .logging import append_episode
from .model import Card, GameState, Joker
from .rng import encode_state, restore_rng
from .scoring import ScoreResult, score_hand

TARGETS = (300, 800, 2000)
HANDS_PER_BLIND = 4
DISCARDS_PER_BLIND = 2
INITIAL_HAND_SIZE = 8


def new_game(seed: int) -> GameState:
    rng = random.Random(seed)
    deck = standard_deck()
    rng.shuffle(deck)
    hand, deck = deck[:INITIAL_HAND_SIZE], deck[INITIAL_HAND_SIZE:]
    return GameState(
        blind_idx=0, target=TARGETS[0], total_score=0, hand=hand, deck=deck,
        jokers=[], hands_left=HANDS_PER_BLIND, discards_left=DISCARDS_PER_BLIND,
        phase="play", rng_state=encode_state(rng), seed=seed, discard_pile=[],
    )


def _draw(state: GameState, count: int) -> list[Card]:
    """Draw in queue order; shuffle the discard pile only when the deck runs out."""
    drawn: list[Card] = []
    while count > 0:
        if not state.deck:
            if not state.discard_pile:
                break
            rng = restore_rng(state.rng_state)
            state.deck = list(state.discard_pile)
            state.discard_pile.clear()
            rng.shuffle(state.deck)
            state.rng_state = encode_state(rng)
        take = min(count, len(state.deck))
        drawn.extend(state.deck[:take])
        del state.deck[:take]
        count -= take
    return drawn


def _create_shop_options(state: GameState, count: int = 3) -> None:
    owned = {j.jid for j in state.jokers}
    available = [j for j in JOKER_CATALOG if j.jid not in owned]
    rng = restore_rng(state.rng_state)
    selected = rng.sample(available, min(count, len(available))) if available else []
    state.shop_options = list(selected)
    state.rng_state = encode_state(rng)


def _after_play(state: GameState) -> None:
    if state.total_score >= state.target:
        if state.blind_idx == 2:
            state.phase = "done"
            state.outcome = "win"
            state.shop_options = []
        else:
            state.phase = "shop"
            _create_shop_options(state, 3)
    elif state.hands_left == 0:
        state.phase = "done"
        state.outcome = "loss"
        state.shop_options = []


def play(state: GameState, card_ids: Sequence[str], log_path: str | Path | None = "data/episode.jsonl") -> tuple[GameState, ScoreResult]:
    if state.phase != "play":
        raise ValueError(f"play requires phase='play', got {state.phase!r}")
    if not 1 <= len(card_ids) <= 5:
        raise ValueError("play action must select 1..5 cards")
    if len(set(card_ids)) != len(card_ids):
        raise ValueError("play action contains duplicate card ids")
    selected = cards_by_ids(state.hand, tuple(card_ids))
    before = state
    after = copy.deepcopy(state)
    hand_index = {card.card_id: i for i, card in enumerate(after.hand)}
    action = encode_card_action("play", after.hand, tuple(hand_index[cid] for cid in card_ids))
    result = score_hand(selected, after.jokers)
    after.total_score += result.final_score
    after.hands_left -= 1
    after.steps += 1
    selected_ids = set(card_ids)
    after.hand = [c for c in after.hand if c.card_id not in selected_ids]
    refill = _draw(after, len(selected))
    after.hand.extend(refill)
    # Played cards enter the discard pile after replenishment, so they cannot be redrawn
    # in the same transition when the draw pile is empty.
    after.discard_pile.extend(selected)
    _after_play(after)
    if log_path is not None:
        append_episode(log_path, state_before=before, action=action.to_dict(),
                       score_delta=result.final_score, state_after=after, score_details=result.to_dict())
    return after, result


def discard(state: GameState, card_ids: Sequence[str], log_path: str | Path | None = "data/episode.jsonl") -> GameState:
    if state.phase != "play":
        raise ValueError(f"discard requires phase='play', got {state.phase!r}")
    if state.discards_left <= 0:
        raise ValueError("no discards remaining")
    if not 1 <= len(card_ids) <= 5:
        raise ValueError("discard action must select 1..5 cards")
    if len(set(card_ids)) != len(card_ids):
        raise ValueError("discard action contains duplicate card ids")
    selected = cards_by_ids(state.hand, tuple(card_ids))
    before = state
    after = copy.deepcopy(state)
    hand_index = {card.card_id: i for i, card in enumerate(after.hand)}
    action = encode_card_action("discard", after.hand, tuple(hand_index[cid] for cid in card_ids))
    selected_ids = set(card_ids)
    after.hand = [c for c in after.hand if c.card_id not in selected_ids]
    after.discards_left -= 1
    after.steps += 1
    refill = _draw(after, len(selected))
    after.hand.extend(refill)
    after.discard_pile.extend(selected)
    if log_path is not None:
        append_episode(log_path, state_before=before, action=action.to_dict(),
                       score_delta=0, state_after=after, score_details=None)
    return after


def choose_joker(state: GameState, idx: int, log_path: str | Path | None = "data/episode.jsonl") -> GameState:
    if state.phase != "shop":
        raise ValueError(f"choose_joker requires phase='shop', got {state.phase!r}")
    if not 0 <= idx < len(state.shop_options):
        raise IndexError("shop option index out of range")
    if len(state.jokers) >= 3:
        raise ValueError("all three Joker slots are occupied")
    before = state
    after = copy.deepcopy(state)
    chosen = after.shop_options[idx]
    if any(j.jid == chosen.jid for j in after.jokers):
        raise ValueError("duplicate Joker ownership is not allowed in v1")
    after.jokers.append(chosen)
    after.blind_idx += 1
    after.target = TARGETS[after.blind_idx]
    after.total_score = 0
    after.hands_left = HANDS_PER_BLIND
    after.discards_left = DISCARDS_PER_BLIND
    after.phase = "play"
    after.shop_options = []
    after.outcome = None
    after.steps += 1
    if log_path is not None:
        append_episode(log_path, state_before=before,
                       action={"kind": "choose_joker", "index": idx, "joker_id": chosen.jid},
                       score_delta=0, state_after=after, score_details=None)
    return after
