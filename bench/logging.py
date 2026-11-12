"""Append-only episode JSONL logging."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from .model import GameState, state_summary


def append_episode(path: str | Path, *, state_before: GameState, action: dict[str, Any],
                   score_delta: int, state_after: GameState, score_details: dict | None = None) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "schema_version": 1,
        "state_before": state_summary(state_before),
        "action": action,
        "score_delta": int(score_delta),
        "score_details": score_details,
        "state_after": state_summary(state_after),
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
