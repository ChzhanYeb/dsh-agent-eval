"""Exactly 25 unit tests, grouped by the W2 test plan."""
from __future__ import annotations
import json
import random
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from bench.actions import legal_discards, legal_plays, encode_card_action
from bench.cards import standard_deck
from bench.engine import new_game, play, discard, choose_joker
from bench.oracle import best_play
from bench.jokers import JOKER_CATALOG
from bench.model import Card, Joker, GameState
from bench.rng import encode_state, restore_rng, state_round_trip_ok
from bench.scoring import HandType, classify_hand, score_hand


def C(rank: int, suit: int = 0) -> Card:
    return Card(suit=suit, rank=rank)


class TestHandClassification(unittest.TestCase):
    # 1
    def test_high_card(self):
        self.assertEqual(classify_hand([C(2), C(7, 1), C(11, 2)]), HandType.HIGH_CARD)

    # 2
    def test_pair(self):
        self.assertEqual(classify_hand([C(7, 0), C(7, 1)]), HandType.PAIR)

    # 3
    def test_two_pair(self):
        self.assertEqual(classify_hand([C(7, 0), C(7, 1), C(9, 2), C(9, 3)]), HandType.TWO_PAIR)

    # 4
    def test_three_kind(self):
        self.assertEqual(classify_hand([C(7, 0), C(7, 1), C(7, 2)]), HandType.THREE_KIND)

    # 5
    def test_straight(self):
        self.assertEqual(classify_hand([C(4, 0), C(5, 1), C(6, 2), C(7, 3), C(8, 0)]), HandType.STRAIGHT)

    # 6
    def test_flush(self):
        self.assertEqual(classify_hand([C(2, 1), C(4, 1), C(7, 1), C(9, 1), C(12, 1)]), HandType.FLUSH)

    # 7
    def test_full_house(self):
        self.assertEqual(classify_hand([C(7, 0), C(7, 1), C(7, 2), C(9, 0), C(9, 1)]), HandType.FULL_HOUSE)

    # 8
    def test_four_kind(self):
        self.assertEqual(classify_hand([C(7, 0), C(7, 1), C(7, 2), C(7, 3)]), HandType.FOUR_KIND)

    # 9
    def test_straight_flush(self):
        self.assertEqual(classify_hand([C(4, 1), C(5, 1), C(6, 1), C(7, 1), C(8, 1)]), HandType.STRAIGHT_FLUSH)

    # 10
    def test_wheel_straight(self):
        self.assertEqual(classify_hand([C(1, 0), C(2, 1), C(3, 2), C(4, 3), C(5, 0)]), HandType.STRAIGHT)

    # 11
    def test_straight_flush_precedes_flush(self):
        cards = [C(10, 2), C(11, 2), C(12, 2), C(13, 2), C(1, 2)]
        self.assertEqual(classify_hand(cards), HandType.STRAIGHT_FLUSH)

    # 12
    def test_four_kind_precedes_two_pair_like_boundary(self):
        # Four equal ranks is classified as Four of a Kind even though it contains multiple pairs.
        cards = [C(8, 0), C(8, 1), C(8, 2), C(8, 3), C(4, 0)]
        self.assertEqual(classify_hand(cards), HandType.FOUR_KIND)


class TestScoring(unittest.TestCase):
    # 13
    def test_no_joker_pair_score_is_custom_formula(self):
        result = score_hand([C(7, 1), C(7, 2)])
        self.assertEqual(result.hand_type, HandType.PAIR)
        self.assertEqual(result.chips, 14)
        self.assertEqual(result.final_score, 28)

    # 14
    def test_add_chips_only(self):
        result = score_hand([C(7, 1), C(7, 2)], [Joker("jc", "add_chips", 10)])
        self.assertEqual((result.chips, result.final_score), (24, 48))

    # 15
    def test_add_mult_only(self):
        result = score_hand([C(7, 1), C(7, 2)], [Joker("jm", "add_mult", 4)])
        self.assertEqual(result.final_score, 84)

    # 16
    def test_mul_mult_only(self):
        result = score_hand([C(7, 1), C(7, 2)], [Joker("jx", "mul_mult", 150)])
        self.assertEqual(result.final_score, 42)

    # 17
    def test_mixed_effects_floor_only_at_end(self):
        cards = [C(7, 1), C(7, 2)]
        jokers = [Joker("jc", "add_chips", 1), Joker("jm", "add_mult", 1), Joker("jx", "mul_mult", 150)]
        result = score_hand(cards, jokers)
        self.assertEqual(result.chips, 15)
        self.assertEqual(str(result.mult), "9/2")
        self.assertEqual(result.final_score, 67)  # floor(15 * 4.5)


class TestJokerOrderAndDispatch(unittest.TestCase):
    # 18
    def test_add_then_xdiffers_from_x_then_add(self):
        cards = [C(7, 1), C(7, 2)]
        add_then_x = score_hand(cards, [Joker("a", "add_mult", 4), Joker("x", "mul_mult", 150)])
        x_then_add = score_hand(cards, [Joker("x", "mul_mult", 150), Joker("a", "add_mult", 4)])
        self.assertNotEqual(add_then_x.final_score, x_then_add.final_score)
        self.assertEqual((add_then_x.final_score, x_then_add.final_score), (126, 98))

    # 19
    def test_three_slot_chain_is_left_to_right(self):
        cards = [C(7, 1), C(7, 2)]
        jokers = [Joker("x1", "mul_mult", 150), Joker("a", "add_mult", 2), Joker("x2", "mul_mult", 200)]
        result = score_hand(cards, jokers)
        self.assertEqual(result.final_score, 140)  # floor(14 * ((2*1.5 + 2)*2))
        self.assertEqual([entry.get("slot") for entry in result.trace if "slot" in entry], [0, 1, 2])

    # 20
    def test_effect_dispatch_area_phase_metadata(self):
        result = score_hand([C(7, 1), C(7, 2)], [
            Joker("c", "add_chips", 1), Joker("m", "add_mult", 1), Joker("x", "mul_mult", 150)
        ])
        trace = [r for r in result.trace if "joker_id" in r]
        self.assertEqual([(r["cardarea"], r["phase"]) for r in trace], [
            ("G.jokers", "before"), ("G.jokers", "before"), ("G.jokers", "individual")
        ])


class TestActionEnumeration(unittest.TestCase):
    # 21
    def test_same_rank_different_suits_are_not_equivalent(self):
        hand = [C(7, 0), C(7, 1), C(3, 2)]
        actions = legal_plays(hand)
        pairs = {tuple(sorted(hand[i].card_id for i in action)) for action in actions if len(action) == 2}
        self.assertIn(tuple(sorted((hand[0].card_id, hand[1].card_id))), pairs)
        self.assertEqual(len(actions), 7)  # 3 singles + 3 pairs + 1 triple

    # 22
    def test_zero_discards_returns_empty(self):
        self.assertEqual(legal_discards([C(2), C(3, 1)], 0), [])

    # 23
    def test_eight_card_hand_has_218_actions_and_stable_ids(self):
        hand = [Card(suit=i % 4, rank=2 + i) for i in range(8)]
        actions = legal_plays(hand)
        self.assertEqual(len(actions), 218)
        encoded = [encode_card_action("play", hand, a).code for a in actions]
        self.assertEqual(len(encoded), len(set(encoded)))
        self.assertTrue(all(code.startswith("play:c") for code in encoded))


class TestReproducibility(unittest.TestCase):
    # 24
    def test_same_seed_entire_episode_is_identical(self):
        def run_once():
            state = new_game(20261112)
            for _ in range(50):
                if state.phase == "done":
                    break
                if state.phase == "shop":
                    state = choose_joker(state, 0, log_path=None)
                else:
                    best = best_play(state)
                    state, _ = play(state, best.card_ids, log_path=None)
            return state
        a, b = run_once(), run_once()
        self.assertEqual(a, b)
        self.assertEqual(a.phase, "done")
        self.assertEqual(a.blind_idx, 2)

    # 25
    def test_rng_state_full_round_trip(self):
        rng = random.Random(43)
        encoded = encode_state(rng)
        restored = restore_rng(encoded)
        self.assertEqual(rng.getstate(), restored.getstate())
        self.assertTrue(state_round_trip_ok(encoded))
        self.assertEqual([rng.random() for _ in range(4)], [restored.random() for _ in range(4)])


if __name__ == "__main__":
    unittest.main()
