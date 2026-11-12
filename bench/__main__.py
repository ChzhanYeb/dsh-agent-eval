"""CLI: python -m bench {demo,verify,ev} ..."""
from __future__ import annotations
import argparse
from itertools import combinations
import json
from pathlib import Path
import random

from .actions import legal_plays
from .engine import new_game, play, discard, choose_joker
from .oracle import best_play, discard_ev, greedy_episode
from .model import Card
from .scoring import score_hand


def verify_oracle(samples: int = 10, seed: int = 20261112) -> dict:
    rng = random.Random(seed)
    deck = [Card(suit=s, rank=r) for s in range(4) for r in range(1, 14)]
    checks = []
    for i in range(samples):
        hand = rng.sample(deck, 8)
        state = new_game(seed + i)
        state.hand = hand
        state.jokers = []
        result = best_play(state)
        brute_force = max(
            score_hand([hand[j] for j in indices], state.jokers).final_score
            for size in range(1, 6) for indices in combinations(range(len(hand)), size)
        )
        checks.append({"case": i + 1, "oracle": result.score, "brute_force": brute_force,
                       "match": result.score == brute_force, "candidates": result.candidates_evaluated})
    return {"seed": seed, "samples": samples, "passed": all(x["match"] for x in checks), "checks": checks}


def run_demo(seed: int, max_steps: int, log_path: str | None) -> dict:
    state = new_game(seed)
    history = []
    for _ in range(max_steps):
        if state.phase == "done":
            break
        if state.phase == "shop":
            state = choose_joker(state, 0, log_path=log_path)
            history.append({"action": "choose_joker", "picked": state.jokers[-1].jid,
                            "blind_idx": state.blind_idx})
            continue
        best = best_play(state)
        state, result = play(state, best.card_ids, log_path=log_path)
        history.append({"action": "play", "cards": list(best.card_ids), "hand_type": result.hand_type.value,
                        "score_delta": result.final_score, "total_score": state.total_score,
                        "blind_idx": state.blind_idx, "phase": state.phase})
    return {"seed": seed, "phase": state.phase, "outcome": state.outcome, "blind_idx": state.blind_idx,
            "total_score_in_current_blind": state.total_score, "hands_left": state.hands_left,
            "discards_left": state.discards_left, "steps": state.steps, "history": history,
            "log_path": log_path}


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m bench", description="BalatroBench custom ruleset v1")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_demo = sub.add_parser("demo", help="run an O1-greedy sample episode")
    p_demo.add_argument("--seed", type=int, default=20261112)
    p_demo.add_argument("--max-steps", type=int, default=50)
    p_demo.add_argument("--log", default="data/episode.jsonl")
    p_verify = sub.add_parser("verify", help="cross-check O1 against an independent brute-force max")
    p_verify.add_argument("--samples", type=int, default=10)
    p_verify.add_argument("--seed", type=int, default=20261112)
    p_ev = sub.add_parser("ev", help="estimate discard EV for the initial hand")
    p_ev.add_argument("--seed", type=int, default=20261112)
    p_ev.add_argument("-k", type=int, default=50)
    args = parser.parse_args()

    if args.cmd == "demo":
        result = run_demo(args.seed, args.max_steps, args.log)
    elif args.cmd == "verify":
        result = verify_oracle(args.samples, args.seed)
    else:
        state = new_game(args.seed)
        ev = discard_ev(state, K=args.k)
        result = {"seed": args.seed, "K": args.k, "actions": [
            {"cards": list(x.card_ids), "indices": list(x.indices), "mean": x.mean, "min": x.min,
             "max": x.max, "samples": x.samples} for x in ev
        ]}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
