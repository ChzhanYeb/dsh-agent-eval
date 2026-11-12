# W2 implementation report

Date: 2026-11-12 (execution environment date)

## Verification executed in this environment

| Check | Result | Evidence |
|---|---|---|
| Unit suite | **25/25 passed** | `tests/test_w2_rules.py`; run `python -m unittest discover -s tests -v` |
| Same-seed full episode determinism | **PASS** | Test runs a complete greedy episode twice and compares final `GameState` values |
| RNG state round trip | **PASS** | Full `random.Random.getstate()` serialized and restored |
| O1 vs independent brute-force max | **10/10 match** | `data/o1-bruteforce-10.json`; 218 candidates for each 8-card hand |
| 3-blind transition smoke test | **PASS to terminal state** | `data/demo-summary.json`; seed `20261112`, 13 transitions, reached blind index 2 and terminal loss |
| Episode JSONL logging | **13 records written** | `data/episode.jsonl`; records include before/after state summaries, action IDs, score delta and score trace |
| O2 discard EV | **218 actions, K=50** | `python -m bench ev --seed 20261112 -k 50`; each result contains mean/min/max |
| Manual real-game comparisons | **NOT VERIFIED** | 20 sample rows remain pending in `docs/engine-fidelity.md` |
| Third-party calculator checks | **NOT VERIFIED** | 5 checks remain pending in `docs/engine-fidelity.md` |

## Important limitation

The code is internally tested against the declared simplified custom ruleset. The provided specification is internally inconsistent with its vanilla fidelity claim: vanilla Balatro adds hand-base Chips, uses different level-1 hand multipliers, and its scoring-card selection and Joker-phase semantics are more complex than the custom contract. In addition, the 8 generic Jokers in the spec have no specified names or values, so the executable catalog uses explicitly marked synthetic fixtures. These differences are recorded in `scenarios/RULES_VERSION`, `docs/joker-semantics.md`, and `docs/engine-fidelity.md`.

Consequently, this report does **not** claim score-level fidelity to vanilla Balatro. The 20+5 empirical gate must remain red until the rules are reconciled and the rows are filled with actual observations.
