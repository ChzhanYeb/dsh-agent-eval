# Data sources and reuse decisions — W2 v2.1

| Source | Intended use | What this implementation uses | License / reuse rule | Status |
|---|---|---|---|---|
| SMODS Calculate Functions | Understand context/area concepts and scoring phases | Architecture reference only; custom effect metadata is documented separately | No source code copied | Reviewed; `before` semantics caveat recorded in `joker-semantics.md` |
| DivvyCr/Balatro-Simulation | Understand pure scoring dispatch structure | Design inspiration only; no code copied | Respect repository's stated license (`LICENCE`); no copied implementation | README reviewed |
| Balatro HQ poker-hands | Verify vanilla base chips/mult and scoring facts | Used to identify the mismatch between vanilla and the custom formula | Facts only; no prose copied | Reference: https://balatrohq.com/poker-hands/ |
| Game Design Lab / Balatro wiki mirror | Cross-check scoring pipeline and phase facts | Reference facts only | No copied prose/code | https://teemo.dev/game-design/balatro/systems/scoring-engine-chips-mult/ |
| EFHIII/balatro-calculator | Third-party single-hand spot-check candidate | No measurements have been run in this environment | Upstream repository lists MIT license; no code copied | 5 checks are pending; see `engine-fidelity.md` |
| evanofslack/balatro-rs | Implementation research only | No code copied | Do not copy code without a verified license | Not used in implementation |
| coder/balatrobot | Potential future action/validation API reference | Not installed or invoked; this project does not script original-game actions | Naming inspiration only | Out of current scope |

## License/process notes

- Effect descriptions and documentation in this repository are written from scratch.
- The eight Joker entries currently in `bench/jokers.py` are synthetic test fixtures. Their values are engineering defaults, **not claims about vanilla Joker values**.
- Before a future release claims score-level fidelity against vanilla Balatro, document the exact game version, exact Joker identities and effects, and all measured input/output pairs. Do not represent pending checks as completed.
