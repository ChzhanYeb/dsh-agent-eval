"""Local exact and approximate reference policies."""
from __future__ import annotations
from dataclasses import dataclass
from itertools import combinations
import random
from statistics import mean
from typing import Sequence
from .actions import legal_plays, legal_discards
from .engine import play, discard, choose_joker
from .model import Card, GameState
from .scoring import ScoreResult, score_hand


@dataclass(frozen=True, slots=True)
class BestPlay:
    card_ids: tuple[str, ...]
    indices: tuple[int, ...]
    score: int
    result: ScoreResult
    candidates_evaluated: int


def best_play(state: GameState) -> BestPlay:
    """O1: exact argmax over all legal play combinations in the current hand."""
    if state.phase != "play":
        raise ValueError("O1 best_play only applies in phase='play'")
    candidates = legal_plays(state.hand)
    if not candidates:
        raise ValueError("no legal play actions")
    best: BestPlay | None = None
    for indices in candidates:
        cards = [state.hand[i] for i in indices]
        result = score_hand(cards, state.jokers)
        candidate = BestPlay(tuple(c.card_id for c in cards), indices, result.final_score, result, len(candidates))
        if best is None or candidate.score > best.score:
            best = candidate
    assert best is not None
    return best


@dataclass(frozen=True, slots=True)
class DiscardEV:
    card_ids: tuple[str, ...]
    indices: tuple[int, ...]
    mean: float
    min: int
    max: int
    samples: int


def discard_ev(state: GameState, K: int = 50, seed: int | None = None) -> list[DiscardEV]:
    """O2: MC estimate of next-hand O1 score after discarding each legal subset.

    Every candidate uses K independent, repeatable samples without replacement from the
    unseen pool. This estimates an unknown draw rather than reproducing the engine RNG.
    """
    if state.phase != "play":
        raise ValueError("O2 only applies in phase='play'")
    if K < 1:
        raise ValueError("K must be >= 1")
    actions = legal_discards(state.hand, state.discards_left)
    unseen = list(state.deck) + list(state.discard_pile)
    if not actions:
        return []
    if seed is None:
        seed = state.seed ^ (state.blind_idx * 1009) ^ state.steps
    output: list[DiscardEV] = []
    for action_idx, indices in enumerate(actions):
        discarded = {state.hand[i].card_id for i in indices}
        kept = [c for c in state.hand if c.card_id not in discarded]
        candidate_pool = [c for c in unseen if c.card_id not in {x.card_id for x in kept}]
        n_draw = min(len(indices), len(candidate_pool))
        samples: list[int] = []
        for replicate in range(K):
            rng = random.Random(seed + action_idx * 1_000_003 + replicate * 97_409)
            draw = rng.sample(candidate_pool, n_draw) if n_draw else []
            next_hand = kept + draw
            # The local oracle can evaluate hands larger than five, but its plays remain 1..5.
            best_score = max(score_hand([next_hand[i] for i in combo], state.jokers).final_score
                             for combo in _combos_for_hand(next_hand))
            samples.append(best_score)
        output.append(DiscardEV(
            card_ids=tuple(state.hand[i].card_id for i in indices), indices=indices,
            mean=mean(samples), min=min(samples), max=max(samples), samples=K,
        ))
    return output


def _combos_for_hand(hand: Sequence[Card]) -> list[tuple[int, ...]]:
    return [combo for size in range(1, min(5, len(hand)) + 1) for combo in combinations(range(len(hand)), size)]


@dataclass(frozen=True, slots=True)
class EpisodeReference:
    outcome: str | None
    score_by_blind: tuple[int, ...]
    total_scored: int
    steps: int
    precision: str = "approximate_greedy_not_global_optimum"


def greedy_episode(state: GameState, max_steps: int = 100) -> EpisodeReference:
    """O3: simulate O1-greedy play; shops select option 0; no global optimality guarantee."""
    current = state
    scores: list[int] = []
    current_blind = current.blind_idx
    scored_total = 0
    for _ in range(max_steps):
        if current.phase == "done":
            return EpisodeReference(current.outcome, tuple(scores), scored_total, current.steps)
        if current.phase == "shop":
            current = choose_joker(current, 0)
            current_blind = current.blind_idx
            continue
        best = best_play(current)
        before_score = current.total_score
        after, result = play(current, best.card_ids)
        scored_total += result.final_score
        if current.blind_idx == current_blind:
            while len(scores) <= current_blind:
                scores.append(0)
            scores[current_blind] += result.final_score
        current = after
    raise RuntimeError(f"episode exceeded max_steps={max_steps}; probable transition bug")
